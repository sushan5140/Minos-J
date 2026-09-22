"""Independent harness validation for Meno-J Experiment 16 (fake model only).

Runs the Experiment 16 runner twice in fresh processes with the deterministic fake
model and checks call/token accounting, matched-budget logic, blinded-judge
plumbing, output generation, determinism, verdict logic, and that no historical
file changed. Nothing here is a scientific result.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_16_matched_compute as e16  # noqa: E402
import schema  # noqa: E402

OUT_JSON = e16.HARNESS_DIR / "meno_j_experiment_16_HARNESS_VALIDATION_ONLY_validation.json"
OUT_MD = e16.HARNESS_DIR / "meno_j_experiment_16_HARNESS_VALIDATION_ONLY_validation.md"

E16_OWNED = (
    "run_experiment_16_matched_compute.py",
    "work/validate_experiment_16_matched_compute.py",
    "RUN_LATER.md",
    "outputs/meno_j_experiment_16_",
    "outputs/harness_validation/experiment_16/",
    "work/experiment_16_",
)
SKIP_PARTS = {"__pycache__", ".git", "vendor", "external", "e13_data", ".venv"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def historical_manifest() -> dict[str, str]:
    manifest = {}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        rel = path.relative_to(PROJECT_DIR).as_posix()
        if rel == ".env" or rel.startswith(E16_OWNED):
            continue
        manifest[rel] = sha256(path)
    return manifest


def run_fake() -> None:
    subprocess.run([sys.executable, str(PROJECT_DIR / "run_experiment_16_matched_compute.py"),
                    "--fake-harness-validation"], cwd=PROJECT_DIR, check=True,
                   stdout=subprocess.DEVNULL)


def strip_volatile(value):
    if isinstance(value, dict):
        return {k: strip_volatile(v) for k, v in value.items() if k not in {"latency_s"}}
    if isinstance(value, list):
        return [strip_volatile(v) for v in value]
    return value


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> None:
    checks: dict[str, dict] = {}

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks[name] = {"passed": bool(ok), "detail": detail}

    before = historical_manifest()

    # 1. protocol
    frozen = load(e16.PROTOCOL_JSON)
    check("protocol_frozen_and_matches_code", frozen == e16.PROTOCOL,
          f"sha256 {e16.protocol_sha256()}")

    # 2. two independent fake runs
    run_fake()
    first = strip_volatile(load(e16.FAKE_PATHS["report_json"]))
    run_fake()
    report = load(e16.FAKE_PATHS["report_json"])
    check("deterministic_replay_identical", strip_volatile(report) == first)

    P = e16.FAKE_PATHS
    units = report["units"]
    ledger = jsonl(P["raw_requests"])
    ft = report["fake_transport"]

    # 3. labeling
    check("fake_outputs_labeled",
          report["mode"] == "fake_harness_validation" and report["verdict"] == e16.FAKE_VERDICT
          and report["banner"] == e16.FAKE_BANNER
          and all(e16.FAKE_BANNER in P[k].read_text(encoding="utf-8") for k in ("report_md", "repro_md"))
          and report["statistics"]["architecture_survived_falsification_test"] is None,
          "verdict replaced by HARNESS_VALIDATION_ONLY_NOT_A_SCIENTIFIC_RESULT")

    # 4. token / call accounting against the fake server's own ledger
    reqs = [r for r in ledger if r["event"] == "request"]
    reported = [r for r in reqs if r["usage_reported"]]
    estimated = [r for r in reqs if not r["usage_reported"]]
    check("successful_request_count_matches_server", len(reqs) == ft["served"], f"{len(reqs)} vs {ft['served']}")
    check("http_attempts_match_server",
          sum(r["http_attempts"] for r in ledger if r["event"] in {"request", "request_failed"}) == ft["http_attempts"],
          f"server attempts {ft['http_attempts']}")
    ledger_prompt = sum(r["prompt_tokens"] for r in reqs)
    ledger_completion = sum(r["completion_tokens"] for r in reqs)
    slack = 2 * len(estimated)
    check("token_totals_match_server",
          abs(ledger_prompt - ft["issued_prompt_tokens"]) <= slack
          and abs(ledger_completion - ft["issued_completion_tokens"]) <= slack,
          f"prompt {ledger_prompt}/{ft['issued_prompt_tokens']}, completion {ledger_completion}/{ft['issued_completion_tokens']}, "
          f"estimated-usage rows {len(estimated)} (slack {slack})")
    check("usage_missing_path_flagged", len(estimated) == ft["responses_without_usage"] == 1)
    budget_a = report["budget_totals"]["A"]
    budget_b = report["budget_totals"]["B"]
    budget_j = report["budget_totals"]["JUDGE"]
    check("arm_plus_judge_tokens_equal_ledger",
          budget_a["total_tokens"] + budget_b["total_tokens"] + budget_j["total_tokens"] == ledger_prompt + ledger_completion)
    check("retry_path_counted", budget_a["transient_http_retries"] + budget_b["transient_http_retries"] == 1
          and ft["sleeps_requested"] == [60], "one injected HTTP 429, historical 60 s backoff requested (not slept)")
    check("json_repair_path_counted",
          budget_a["json_repair_requests"] + budget_b["json_repair_requests"] == 1
          and budget_a["successful_requests"] == budget_a["logical_calls"] + budget_a["json_repair_requests"])

    # per-unit recomputation from raw ledger
    mismatches = []
    for u in units:
        for arm, key in (("A", "budget_A"), ("B", "budget_B"), ("JUDGE", "judge_budget")):
            recomputed = e16.summarize_budget(ledger, u["unit_id"], arm)
            for f in e16.BUDGET_FIELDS:
                if recomputed[f] != u[key][f]:
                    mismatches.append(f"{u['unit_id']}/{arm}/{f}")
    check("per_unit_budget_recomputes_from_raw_ledger", not mismatches, ", ".join(mismatches[:10]))

    # 5. matched budget
    bad = []
    for u in units:
        ratio = u["budget_B"]["total_tokens"] / u["budget_A"]["total_tokens"]
        expected_match = 0.85 <= ratio <= 1.15 and u["budget_A"]["evaluator_calls"] == u["budget_B"]["evaluator_calls"] == 1
        if abs(ratio - u["token_ratio_B_over_A"]) > 1e-12 or expected_match != u["budget_matched"]:
            bad.append(u["unit_id"])
        if u["budget_B"]["generator_calls"] != u["arm_b_k"] or u["arm_b_k"] > u["arm_b_k_cap"]:
            bad.append(u["unit_id"] + ":K")
        if u["budget_A"]["logical_calls"] < 7:
            bad.append(u["unit_id"] + ":A-stages")
    check("matched_budget_flags_consistent", not bad, ", ".join(bad))
    check("evaluator_parity_every_unit", all(u["evaluator_parity"] for u in units))
    invalid = [s for u in units for s in u["arm_b_samples"] if not s["valid"]]
    check("invalid_baseline_sample_still_charged",
          len(invalid) == 1 and invalid[0]["total_tokens"] > 0
          and any("failed validation" in n for u in units for n in u["anomalies"]))
    check("arm_a_ran_all_v4_stages",
          all({r["stage"] for r in reqs if r.get("unit_id") == u["unit_id"] and r.get("arm") == "A"}
              >= {"stage_4_dreamer", "stage_4_1_mechanism_builder", "stage_4_2_confounder_rival_builder",
                  "stage_4_3_statistical_testability_builder", "stage_5_auditor", "stage_6_rival_matrix",
                  "stage_7_falsification"} for u in units))

    # controller brute-force test
    def brute(target, cost, comp, tmpl, ev, cap):
        best_k, best = None, None
        for k in range(1, cap + 1):
            total = k * cost + tmpl + k * comp + ev
            if best is None or abs(total - target) < best:
                best_k, best = k, abs(total - target)
        return best_k
    ctrl_bad = []
    for target, cost, comp, tmpl, ev, cap in [(30000, 4000, 3500, 600, 900, 14), (10000, 2000, 1500, 500, 300, 14),
                                              (5000, 6000, 5000, 500, 300, 14), (90000, 4000, 3500, 600, 900, 6)]:
        costs, comps = [], []
        while e16.choose_next_sample(target, sum(costs), costs, comps, tmpl, ev, cap):
            costs.append(cost)
            comps.append(comp)
        if len(costs) != brute(target, cost, comp, tmpl, ev, cap):
            ctrl_bad.append((target, len(costs), brute(target, cost, comp, tmpl, ev, cap)))
    check("budget_controller_picks_closest_k", not ctrl_bad, str(ctrl_bad))

    # 6. blinded judge plumbing
    judgments = jsonl(P["judgments"])
    judge_reqs = [r for r in reqs if r.get("arm") == "JUDGE"]
    check("judge_uses_separate_model",
          report["judge_model"] != report["generator_model"]
          and all(r["model_requested"] == report["judge_model"] for r in judge_reqs)
          and all(r["model_requested"] == report["generator_model"] for r in reqs if r.get("arm") in {"A", "B"}))
    check("judge_calls_excluded_from_arm_budgets",
          all(r.get("role") == "judge" for r in judge_reqs) and budget_j["total_tokens"] > 0
          and not any(r.get("stage") == "blinded_judge" and r.get("arm") != "JUDGE" for r in reqs))
    blind_bad = []
    for u in units:
        rows = [j for j in judgments if j["unit_id"] == u["unit_id"]]
        ids = [j["card_id"] for j in rows]
        if len(ids) != len(set(ids)) or any(j["judgment"] is None for j in rows):
            blind_bad.append(u["unit_id"] + ":coverage")
        for arm in ("A", "B"):
            if sum(j["arm"] == arm for j in rows) != u[f"metrics_{arm}"]["reported_survivors"]:
                blind_bad.append(u["unit_id"] + f":count{arm}")
            recount = sum(e16.judge_validated(j["judgment"], schema) for j in rows if j["arm"] == arm)
            if recount != u[f"metrics_{arm}"]["judge_validated"]:
                blind_bad.append(u["unit_id"] + f":V{arm}")
        batch_ids = [c for b in u["judge_batches"] for c in b["card_ids"]]
        if sorted(batch_ids) != sorted(ids):
            blind_bad.append(u["unit_id"] + ":batches")
        for j in rows:
            card = j["card"]
            if set(card) != {"card_id", *e16.CARD_FIELDS}:
                blind_bad.append(u["unit_id"] + ":fields")
            if j["source_ref"] in json.dumps(card) and j["source_ref"].startswith("S"):
                blind_bad.append(u["unit_id"] + ":srcref")
        # rebuild each judge prompt and scan the template
        order = ("card_id", *e16.CARD_FIELDS)  # judgments.jsonl is written with sort_keys
        cards_by_id = {j["card_id"]: {k: j["card"][k] for k in order} for j in rows}
        for b in u["judge_batches"]:
            batch = [cards_by_id[c] for c in b["card_ids"]]
            prompt = e16.judge_prompt(e16.QUESTIONS[u["question_id"]], batch, schema)
            if e16._sha256_text(prompt) != b["prompt_sha256"]:
                blind_bad.append(u["unit_id"] + ":prompt-hash")
            template = prompt.replace(json.dumps(batch, ensure_ascii=False, indent=2), "<CARDS>")
            if e16.BLINDING_FORBIDDEN.search(template):
                blind_bad.append(u["unit_id"] + ":template-leak")
        mixed = any(len({cards_arm for cards_arm in (next(j["arm"] for j in rows if j["card_id"] == c) for c in b["card_ids"])}) == 2
                    for b in u["judge_batches"])
        if u["metrics_A"]["reported_survivors"] and u["metrics_B"]["reported_survivors"] and not mixed:
            blind_bad.append(u["unit_id"] + ":not-mixed")
    check("blinded_judge_plumbing", not blind_bad, ", ".join(blind_bad[:12]))
    shuffled_a, key_a = e16.blind_cards("X-r1", {"A": [{"source_ref": "H1", "card": {"hypothesis": "a"}}],
                                                  "B": [{"source_ref": "S1-H1", "card": {"hypothesis": "b"}}]})
    shuffled_b, key_b = e16.blind_cards("X-r1", {"A": [{"source_ref": "H1", "card": {"hypothesis": "a"}}],
                                                  "B": [{"source_ref": "S1-H1", "card": {"hypothesis": "b"}}]})
    check("blinding_is_seeded_and_key_kept_out_of_cards",
          shuffled_a == shuffled_b and key_a == key_b and all("arm" not in c and "source_ref" not in c for c in shuffled_a))

    # 7. outputs
    exist = all(P[k].exists() and P[k].stat().st_size > 0 for k in P if k != "checkpoints")
    with P["aggregate_csv"].open(encoding="utf-8") as f:
        agg_rows = list(csv.DictReader(f))
    with P["budget_csv"].open(encoding="utf-8") as f:
        bud_rows = list(csv.DictReader(f))
    check("raw_and_aggregate_outputs_written",
          exist and len(agg_rows) == len(units) == 9 and len(bud_rows) == 3 * len(units)
          and len(jsonl(P["raw_units"])) == len(units),
          f"{len(agg_rows)} aggregate rows, {len(bud_rows)} budget rows")
    check("output_names_never_historical",
          not any(e16.HISTORICAL_OUTPUT_PATTERN.search(P[k].name) for k in P if k != "checkpoints")
          and not e16.HISTORICAL_OUTPUT_PATTERN.search(e16.REAL_PATHS["report_json"].name)
          and all(not e16.HISTORICAL_OUTPUT_PATTERN.search(e16.REAL_PATHS[k].name) for k in e16.REAL_PATHS if k != "checkpoints"))
    check("real_and_fake_paths_disjoint",
          not ({str(v) for v in e16.REAL_PATHS.values()} & {str(v) for v in e16.FAKE_PATHS.values()}))

    # 8. verdict logic
    cases = [([2.0] * 9, 9, "ARCHITECTURE_ADVANTAGE_SURVIVED"),
             ([0, 1, -1, 0, 1, -1, 0, 0, 1], 9, "ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED"),
             ([0.5, 0.6, 0.4, 0.5, 0.7, 0.5, 0.6, 0.4, 0.5], 9, "ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED"),
             ([-2.0] * 9, 9, "BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED"),
             ([3.0] * 3, 3, "INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS"),
             ([3.0] * 6, 10, "INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS")]
    verdict_bad = [(d, want, e16.decide_verdict(d, n)["verdict"]) for d, n, want in cases
                   if e16.decide_verdict(d, n)["verdict"] != want]
    check("verdict_rule_matches_preregistration", not verdict_bad, str(verdict_bad))

    # 9. credentials and historical integrity
    marker = "sk-" + "or-v1"
    new_files = [PROJECT_DIR / "run_experiment_16_matched_compute.py", Path(__file__)] + \
        [p for p in e16.HARNESS_DIR.glob("*") if p.is_file()] + [e16.PROTOCOL_JSON, e16.PROTOCOL_MD]
    if (PROJECT_DIR / "RUN_LATER.md").exists():
        new_files.append(PROJECT_DIR / "RUN_LATER.md")
    check("credential_scan_new_files", not any(marker in p.read_text(encoding="utf-8") for p in new_files if p.suffix in {".py", ".json", ".md", ".jsonl", ".csv"}))
    after = historical_manifest()
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    check("historical_files_unchanged", not changed, f"{len(before)} files hashed; changed: {changed[:10]}")
    hist8_15 = sorted(k for k in after if any(f"experiment_{n}_" in k for n in range(8, 16)))
    check("experiments_8_to_15_present_and_unchanged", all(before.get(k) == after.get(k) for k in hist8_15),
          f"{len(hist8_15)} Experiment 8-15 files in this checkout")

    passed = all(c["passed"] for c in checks.values())
    out = {"experiment_name": e16.EXPERIMENT_16_NAME, "scope": "HARNESS VALIDATION ONLY (fake model); no scientific result",
           "status": "PASSED" if passed else "FAILED", "protocol_sha256": e16.protocol_sha256(),
           "runner_sha256": sha256(PROJECT_DIR / "run_experiment_16_matched_compute.py"),
           "fake_report_sha256": sha256(P["report_json"]), "historical_manifest": after, "checks": checks}
    e16.HARNESS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# {e16.EXPERIMENT_16_NAME} — Harness Validation", "", f"> **{e16.FAKE_BANNER}**", "",
             f"- Status: **{out['status']}**", f"- Protocol SHA-256: `{out['protocol_sha256']}`",
             f"- Runner SHA-256: `{out['runner_sha256']}`", f"- Historical files hashed: {len(after)}", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {k} | {'PASS' if v['passed'] else 'FAIL'} | {v['detail']} |" for k, v in checks.items()]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in checks.items():
        print(f"{'PASS' if v['passed'] else 'FAIL'}  {k}  {v['detail']}")
    print(f"Harness validation: {out['status']}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
