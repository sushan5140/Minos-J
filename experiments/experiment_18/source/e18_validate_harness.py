"""Non-live validation harness for Experiment 18 (fake Claude CLI; zero quota).

Runs the real transport, runner, analysis and independent validator against a
fake ``claude -p`` whose "reasoning" is a known deterministic rule per arm:
A = joint falsifier, C = marker-only, D = intervention-only, B = series-only.
Expected accuracies therefore equal the non-LLM reference-solver accuracies.
Fake outputs are never scientific results.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import e18_analysis as AN  # noqa: E402
import e18_common as CM  # noqa: E402
import e18_prompts as P  # noqa: E402
import e18_protocol as PR  # noqa: E402
import e18_runner as R  # noqa: E402
import e18_tasks as T  # noqa: E402
import e18_transport as X  # noqa: E402
import e18_validate_results as V  # noqa: E402

ROW = re.compile(r"^\| (\w+) \| ([\d.]+) \(([\d.]+)\) \| ([\d.]+) \| ([\d. >-]+) \|$", re.M)
RULES = {"A": T.solve_joint, "C": T.solve_marker_only, "D": T.solve_gain_only, "B": T.solve_series_only}


def parse_packet(prompt: str) -> dict[str, Any]:
    c0 = float(re.search(r"Subgroup coverage: (\d+\.\d+)", prompt).group(1))
    ev = {m: {"marker_subgroup": s, "marker_reference": r, "intervention_coverage": float(i),
              "series": [float(v) for v in ser.split("->")]} for m, s, r, i, ser in ROW.findall(prompt)}
    return {"subgroup_coverage": c0, "evidence": ev}


def identify(prompt: str) -> tuple[str, int]:
    """Step-3 instructions are identical across A/C/D by design (parity), so use the trial's own step-2 output."""
    if P.INSTRUCTIONS[("A", 3)] in prompt:
        step2 = prompt.split("[step 2] ", 1)[1].split("\n", 1)[0]
        return ("A" if '"tests"' in step2 else "C" if '"critique_points"' in step2 else "D"), 3
    for (arm, call), text in P.INSTRUCTIONS.items():
        if call != 3 and text in prompt:
            return arm, call
    raise AssertionError("unknown instruction")


class FakeCLI:
    """Callable with the transport runner signature. Fault injection via self.script (by attempt index)."""

    def __init__(self, script: dict[int, Any] | None = None, model: str = "claude-sonnet-5"):
        self.script = dict(script or {})
        self.n = 0
        self.model = model
        self.calls: list[tuple[str, int]] = []

    def __call__(self, argv, stdin_text, env, cwd, timeout):  # noqa: ARG002
        if argv[1:] == ["--version"]:
            return 0, "9.9.9 (fake)", ""
        self.n += 1
        action = self.script.get(self.n)
        if isinstance(action, BaseException):
            raise action
        if callable(action):
            return action(stdin_text)
        if isinstance(action, tuple):
            return action
        arm, call = identify(stdin_text)
        self.calls.append((arm, call))
        case = parse_packet(stdin_text)
        answer = RULES[arm](case)
        others = [m for m in T.MECHANISM_IDS if m != answer]
        name = P.SCHEMAS[(arm, call)][0]
        rivals = [answer] + others[:3]
        if name == "final_answer":
            out = {"mechanism_id": answer, "probabilities": {m: (0.75 if m == answer else 0.05) for m in T.MECHANISM_IDS},
                   "justification": "fake"}
        elif name == "rivals_with_predictions":
            out = {"rivals": [{"mechanism_id": m, "discriminating_predictions": ["intervention restores", "series rises"]} for m in rivals]}
        elif name == "falsification_tests":
            out = {"tests": [{"mechanism_id": m, "prediction": "p", "observed_evidence": "e",
                              "verdict": "SUPPORTED" if m == answer else "CONTRADICTED"} for m in rivals],
                   "eliminated": rivals[1:], "surviving": [answer]}
        elif name == "rivals_with_rationale":
            out = {"rivals": [{"mechanism_id": m, "rationale": "r"} for m in rivals]}
        elif name == "plausibility_ranking":
            out = {"assessments": [{"mechanism_id": m, "overall_plausibility": "HIGH" if m == answer else "LOW", "judgement": "j"} for m in rivals],
                   "ranking": rivals}
        else:
            out = {"critique_points": ["c"], "overlooked_or_misread_evidence": [], "alternative_explanations": []}
        usage = {"input_tokens": 10, "cache_creation_input_tokens": len(stdin_text) // 4, "cache_read_input_tokens": 100,
                 "output_tokens": 50 + 10 * call}
        return 0, json.dumps({"type": "result", "subtype": "success", "is_error": False, "structured_output": out,
                              "usage": usage, "modelUsage": {self.model: {}}, "num_turns": 2}), ""


def err(message: str, status: Any = None, usage: dict | None = None) -> tuple[int, str, str]:
    return 1, json.dumps({"type": "result", "is_error": True, "result": message, "api_error_status": status,
                          "usage": usage or {"input_tokens": 0, "output_tokens": 0}, "modelUsage": {}}), ""


def factory(fake: FakeCLI):
    def make(on_event, paths):
        return X.ClaudeCLI(paths.cli_cwd, paths.archive, on_event, cli=Path("fake-claude.exe"), runner=fake,
                           sleeper=lambda s: None, cli_version="9.9.9 (fake)"), "9.9.9 (fake)"
    return make


def setup_tasks(tmp: Path, per_mech: int = 2) -> tuple[Path, list[dict], dict]:
    tasks = tmp / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    public, key = T.build_set(T.MAIN_SEED, per_mech, "E18-M", T.DEFAULT_DIFFICULTY)
    (tasks / "main_cases_public.jsonl").write_text("".join(CM.dumps(r) + "\n" for r in public), encoding="utf-8")
    (tasks / "main_answer_key.json").write_text(CM.dumps(key), encoding="utf-8")
    return tasks, public, key


def runner(tmp: Path, public: list[dict], fake: FakeCLI, name: str = "main") -> R.Runner:
    paths = R.Paths(name, work=tmp / "work", results=tmp / "results")
    return R.Runner(name, factory(fake), protocol_digest="test", tasks_sha="test", paths=paths, cases=public, probe=False)


def run_checks(tmp: Path) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, ok: bool, detail: Any = "") -> None:
        checks[name] = {"passed": bool(ok), "detail": str(detail)[:300]}

    # 1 deterministic generation
    a1, k1 = T.build_set(T.MAIN_SEED, 30, "E18-M", 0.5)
    a2, k2 = T.build_set(T.MAIN_SEED, 30, "E18-M", 0.5)
    a3, _ = T.build_set("OTHER-SEED", 30, "E18-M", 0.5)
    manifest = json.loads((CM.TASKS_DIR / "manifest.json").read_text(encoding="utf-8"))
    check("01_deterministic_task_generation", a1 == a2 and k1 == k2 and a1 != a3
          and CM.canonical_sha256({r["case_id"]: r["packet_sha256"] for r in a1}) == manifest["main"]["packet_hashes_sha256"],
          "same seed identical; other seed differs; matches on-disk manifest")

    # 2 answer-key isolation
    case = a1[0]
    leaked = False
    try:
        P.build_prompt("A", 1, {**case, "true_mechanism": "X"}, [])
    except ValueError:
        leaked = True
    src_ok = all("answer_key" not in (CM.SOURCE_DIR / f).read_text(encoding="utf-8")
                 for f in ("e18_runner.py", "e18_prompts.py", "e18_transport.py"))
    public_fields = set().union(*(set(r) for r in a1))
    check("02_answer_key_isolation", leaked and src_ok and public_fields == {"case_id", "packet", "packet_sha256"},
          public_fields)

    # 3 schema parsing / semantic validation
    good = {"mechanism_id": "LABEL_NOISE", "probabilities": {m: 1 / 6 for m in T.MECHANISM_IDS}, "justification": "x"}
    bad_sum = {**good, "probabilities": {m: 0.1 for m in T.MECHANISM_IDS}}
    bad_id = {**good, "mechanism_id": "UNKNOWN"}
    bad_rivals = {"rivals": [{"mechanism_id": "LABEL_NOISE", "discriminating_predictions": ["a", "b"]}] * 4}
    rejected = 0
    for payload, arm, call in ((bad_sum, "B", 1), (bad_id, "B", 1), (bad_rivals, "A", 1)):
        try:
            P.validate_output(arm, call, payload, [])
        except P.OutputInvalid:
            rejected += 1
    norm = P.validate_output("B", 1, good, [])["probabilities_normalized"]
    check("03_schema_and_semantic_validation", rejected == 3 and abs(sum(norm.values()) - 1) < 1e-12, rejected)

    # 5 prompt construction + 6 prompt parity
    prompts = {(arm, call): P.build_prompt(arm, call, case, []) for (arm, call) in P.INSTRUCTIONS}
    body_ok = all(p.startswith(P.COMMON_HEADER) and T.mechanism_vocabulary() in p and case["packet"] in p
                  and p.endswith(P.OUTPUT_LINE) for p in prompts.values())
    prev_prompt = P.build_prompt("A", 2, case, [{"rivals": []}])
    check("05_prompt_construction", body_ok and "[step 1]" in prev_prompt, len(prompts))
    shared = {k: v.replace(P.INSTRUCTIONS[k], "") for k, v in prompts.items()}
    ratios = [max(len(P.INSTRUCTIONS[(a, c)]) for a in "ACD") / min(len(P.INSTRUCTIONS[(a, c)]) for a in "ACD") for c in (1, 2, 3)]
    finals = {P.SCHEMAS[(a, P.CALLS_PER_ARM[a])][1] == P.FINAL_SCHEMA for a in P.ARMS}
    check("06_prompt_parity", len(set(shared.values())) == 1 and max(ratios) <= 1.20 and finals == {True}
          and P.INSTRUCTIONS[("A", 3)] == P.INSTRUCTIONS[("C", 3)] == P.INSTRUCTIONS[("D", 3)], [round(r, 3) for r in ratios])

    # full fake run on 12 cases (2 per mechanism)
    tasks, public, key = setup_tasks(tmp / "full")
    fake = FakeCLI()
    code = runner(tmp / "full", public, fake).run()
    data = AN.load("main", tmp / "full" / "work", tasks)
    rep = AN.main_report(data)
    CM.atomic_write_json(tmp / "full" / "results" / "main_report.json", rep)
    sol = T.solver_report(key)
    expected = {"A": sol["joint_falsifier"]["all"], "C": sol["marker_only"]["all"], "D": sol["intervention_only"]["all"],
                "B": sol["series_only"]["all"]}
    check("04_scorer_correctness", code == 0 and all(abs(rep["accuracy"][a]["all"] - expected[a]) < 5e-5 for a in P.ARMS),  # solver report rounds to 4 dp
          ({a: rep["accuracy"][a]["all"] for a in P.ARMS}, expected))

    # 7 token accounting (incl. usage inside an error envelope)
    ledger = CM.read_jsonl_strict(tmp / "full" / "work" / "main" / "ledger.jsonl")
    tot = {a: sum(r["measured_total_tokens"] for r in ledger if r["event"] == "attempt_finished" and r["arm"] == a) for a in P.ARMS}
    split_ok = all(r["measured_total_tokens"] == r["input_tokens"] + r["cache_creation_input_tokens"] + r["cache_read_input_tokens"] + r["output_tokens"]
                   for r in ledger if r["event"] == "attempt_finished")
    tasks2, public2, _ = setup_tasks(tmp / "cap", per_mech=1)
    capfake = FakeCLI({1: err("API Error: Claude's response exceeded the 8000 output token maximum.", None,
                              {"input_tokens": 5, "output_tokens": 8000})})
    runner(tmp / "cap", public2[:1], capfake).run()
    cap_rows = [r for r in CM.read_jsonl_strict(tmp / "cap" / "work" / "main" / "ledger.jsonl") if r["event"] == "attempt_finished"]
    check("07_token_accounting", split_ok and all(tot[a] == rep["compute"]["per_arm"][a]["measured_total_tokens"] for a in P.ARMS)
          and cap_rows[0]["classification"] == "INVALID_OUTPUT" and cap_rows[0]["output_tokens"] == 8000
          and rep["compute"]["per_arm"]["A"]["calls_completed"] == 3 * len(public), tot)

    # 8 compute gate
    prim = {"bootstrap_ci95": [0.05, 0.25], "delta": 0.15, "mcnemar_exact_p": 0.01}
    pa = {"A": {"failed_infra": 0}, "C": {"failed_infra": 0}}
    check("08_compute_gate", AN.verdict(prim, pa, 180, 180, 1.10) == "FALSIFICATION_ADVANTAGE_SUPPORTED"
          and AN.verdict(prim, pa, 180, 180, 1.30) == "ADVANTAGE_BUT_COMPUTE_UNMATCHED"
          and AN.verdict({**prim, "bootstrap_ci95": [-0.08, 0.07], "delta": 0.0}, pa, 180, 180, 1.30) == "NO_PRACTICALLY_MEANINGFUL_ADVANTAGE"
          and AN.verdict({**prim, "bootstrap_ci95": [-0.2, -0.01], "delta": -0.1}, pa, 180, 180, 1.0) == "C_SUPERIOR"
          and AN.verdict(prim, pa, 180, 150, 1.0) == "INCONCLUSIVE_INCOMPLETE")

    # 9 quota pause (real Pro wording) + 15/16 resume, orphan detection, no rerun
    tasks3, public3, key3 = setup_tasks(tmp / "pause", per_mech=2)
    msg = "You've hit your session limit · resets 8:20am (Asia/Kolkata)"
    pfake = FakeCLI({5: err(msg, 429)})
    r1 = runner(tmp / "pause", public3, pfake)
    c1 = r1.run()
    trials_dir = tmp / "pause" / "work" / "main" / "trials"
    partial_terminal = len(list(trials_dir.glob("*/*/trial_result.json")))
    led1 = CM.read_jsonl_strict(tmp / "pause" / "work" / "main" / "ledger.jsonl")
    check("09_quota_pause_not_failure", c1 == R.EXIT_PAUSED and any(r["event"] == "session_paused" for r in led1)
          and not any(r["event"] == "trial_terminal" and r.get("status", "").startswith("FAILED") for r in led1), (c1, partial_terminal))

    class HardKill(BaseException):
        pass

    kfake = FakeCLI({3: HardKill()})
    try:
        runner(tmp / "pause", public3, kfake).run()
    except HardKill:
        pass
    (tmp / "pause" / "work" / "main" / "run.lock").unlink(missing_ok=True)
    rfake = FakeCLI()
    c3 = runner(tmp / "pause", public3, rfake).run()
    led = CM.read_jsonl_strict(tmp / "pause" / "work" / "main" / "ledger.jsonl")
    orphan = [r for r in led if r["event"] == "orphan_attempt_recorded"]
    per_trial_calls: dict[tuple, int] = {}
    for r in led:
        if r["event"] == "logical_call" and r["ok"]:
            per_trial_calls[(r["case_id"], r["arm"], r["call"])] = per_trial_calls.get((r["case_id"], r["arm"], r["call"]), 0) + 1
    data3 = AN.load("main", tmp / "pause" / "work", tasks3)
    rep3 = AN.main_report(data3)
    sol3 = T.solver_report(key3)
    check("15_resume_after_interruption", c3 == 0 and len(orphan) == 1
          and abs(rep3["accuracy"]["A"]["all"] - sol3["joint_falsifier"]["all"]) < 5e-5, (c3, len(orphan)))
    check("16_no_rerun_of_completed_calls_or_trials", max(per_trial_calls.values()) == 1
          and len([r for r in led if r["event"] == "trial_terminal"]) == len(public3) * 4, max(per_trial_calls.values()))

    # 10 corrupted checkpoint detection (nothing deleted)
    first = next(trials_dir.glob("*/A/call_1.json"))
    original = first.read_text(encoding="utf-8")
    first.write_text(original[: len(original) // 2], encoding="utf-8")
    report_file = tmp / "pause" / "results" / "main_report.json"
    report_file.unlink(missing_ok=True)
    c4 = runner(tmp / "pause", public3, FakeCLI()).run()
    check("10_corrupted_checkpoint_detection", c4 == R.EXIT_CORRUPT and first.exists(), c4)
    first.write_text(original, encoding="utf-8")

    # 11 atomic writes: a failed replace leaves the previous file intact and no temp debris
    target = tmp / "atomic" / "x.json"
    CM.atomic_write_json(target, {"v": 1})
    real_replace = os.replace
    try:
        os.replace = lambda *a, **k: (_ for _ in ()).throw(OSError("simulated crash"))
        try:
            CM.atomic_write_json(target, {"v": 2})
        except OSError:
            pass
    finally:
        os.replace = real_replace
    check("11_atomic_writes", json.loads(target.read_text())["v"] == 1, "previous content intact after simulated crash")

    # 12 terminal failure persistence + repair parity
    tasks4, public4, _ = setup_tasks(tmp / "fail", per_mech=1)
    order = R.arm_order(public4[0]["case_id"])
    bad = lambda _prompt: (0, json.dumps({"type": "result", "is_error": False, "structured_output":  # noqa: E731
                           {"mechanism_id": "LABEL_NOISE", "probabilities": {m: 0.5 for m in T.MECHANISM_IDS}, "justification": "x"}
                           if order[0] == "B" or True else {}, "usage": {"input_tokens": 1, "output_tokens": 1},
                           "modelUsage": {"claude-sonnet-5": {}}}), "")
    ffake = FakeCLI({1: bad, 2: bad})
    runner(tmp / "fail", public4[:1], ffake).run()
    first_trial = tmp / "fail" / "work" / "main" / "trials" / public4[0]["case_id"] / order[0] / "trial_result.json"
    status = CM.read_json(first_trial)["status"]
    n_before = ffake.n
    (tmp / "fail" / "results" / "main_report.json").unlink(missing_ok=True)
    runner(tmp / "fail", public4[:1], ffake).run()
    check("12_terminal_failure_persistence", status == "FAILED_OUTPUT" and ffake.n == n_before, (status, ffake.n - n_before))

    # 13 duplicate prevention
    dup = tmp / "dup" / "work" / "main"
    dup.mkdir(parents=True)
    row = {"event": "trial_terminal", "case_id": public4[0]["case_id"], "arm": "A", "status": "COMPLETE"}
    (dup / "ledger.jsonl").write_text(CM.dumps({**row, "seq": 1}) + "\n" + CM.dumps({**row, "seq": 2}) + "\n", encoding="utf-8")
    check("13_duplicate_terminal_prevention", runner(tmp / "dup", public4[:1], FakeCLI()).run() == R.EXIT_CORRUPT)

    # 14 runner lock
    lockdir = tmp / "lock" / "work" / "main"
    lockdir.mkdir(parents=True)
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        (lockdir / "run.lock").write_text(str(holder.pid))
        busy = runner(tmp / "lock", public4[:1], FakeCLI()).run()
    finally:
        holder.kill()
        holder.wait()
    (lockdir / "run.lock").write_text("999999")
    reclaimed = runner(tmp / "lock", public4[:1], FakeCLI()).run()
    check("14_single_process_lock", busy == R.EXIT_BUSY and reclaimed == 0, (busy, reclaimed))

    # overwrite protection
    (tmp / "lock" / "results").mkdir(parents=True, exist_ok=True)
    (tmp / "lock" / "results" / "main_report.json").write_text("{}")
    check("14b_completed_study_overwrite_protection", runner(tmp / "lock", public4[:1], FakeCLI()).run() == R.EXIT_OVERWRITE)

    # infrastructure halt and model-identity halt
    tasks5, public5, _ = setup_tasks(tmp / "infra", per_mech=2)
    ifake = FakeCLI({i: err("unclassified failure xyz") for i in range(1, 200)})
    check("14c_infrastructure_halt", runner(tmp / "infra", public5, ifake).run() == R.EXIT_INFRA_HALT)
    check("14d_model_identity_halt", runner(tmp / "ident", public4[:1], FakeCLI(model="claude-other")).run() == R.EXIT_IDENTITY)

    # 17 protocol hash verification
    p1, p2 = PR.build("FROZEN"), PR.build("FROZEN")
    saved = P.INSTRUCTIONS[("A", 1)]
    P.INSTRUCTIONS[("A", 1)] = saved + " "
    p3 = PR.build("FROZEN")
    P.INSTRUCTIONS[("A", 1)] = saved
    check("17_protocol_hash_verification", PR.protocol_sha256(p1) == PR.protocol_sha256(p2) != PR.protocol_sha256(p3)
          and (PR.PROTOCOL_SHA.exists() or PR.verify() is False), "hash stable; prompt edit changes hash; unfrozen protocol does not verify")

    # 18 independent reconstruction of final statistics (and tamper detection)
    v_ok = V.validate("main", tmp / "full" / "work", tasks, tmp / "full" / "results" / "main_report.json", check_protocol=False)
    tampered = dict(rep)
    tampered["primary_A_vs_C"] = {**rep["primary_A_vs_C"], "delta": rep["primary_A_vs_C"]["delta"] + 0.01}
    CM.atomic_write_json(tmp / "full" / "results" / "tampered.json", tampered)
    v_bad = V.validate("main", tmp / "full" / "work", tasks, tmp / "full" / "results" / "tampered.json", check_protocol=False)
    check("18_independent_reconstruction", v_ok["status"] == "PASSED" and v_bad["status"] == "FAILED", (v_ok["passed"], v_ok["total"]))

    # scorer blindness: key is never loaded before all trials are terminal
    try:
        AN.load("main", tmp / "cap" / "work", tasks2)
        blind = False
    except RuntimeError:
        blind = True
    check("19_scorer_refuses_incomplete_sets", blind)
    return checks


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="e18_harness_"))
    before = {p: p.stat().st_mtime_ns for p in CM.TASKS_DIR.glob("*")}
    try:
        checks = run_checks(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    after = {p: p.stat().st_mtime_ns for p in CM.TASKS_DIR.glob("*")}
    checks["20_frozen_task_files_untouched"] = {"passed": before == after, "detail": ""}
    passed = all(c["passed"] for c in checks.values())
    out = {"artifact": "Experiment 18 harness validation (fake CLI, zero quota; not a scientific result)",
           "status": "PASSED" if passed else "FAILED", "passed": sum(c["passed"] for c in checks.values()),
           "total": len(checks), "checks": checks}
    CM.atomic_write_json(CM.VALIDATION_DIR / "harness_validation.json", out)
    for name, c in sorted(checks.items()):
        print("PASS" if c["passed"] else "FAIL", name, c["detail"][:140])
    print(out["status"], f"{out['passed']}/{out['total']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
