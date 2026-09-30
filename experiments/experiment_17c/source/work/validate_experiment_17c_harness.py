"""No-model harness validation for Minos-J Experiment 17-C (Claude replication).

Every check uses a deterministic fake ``claude -p`` runner.  No model is
called and no subscription usage is consumed.  Fake outputs are written only
to a temporary directory and are never scientific results.

Usage:
  python work/validate_experiment_17c_harness.py --capture-baseline   # once, before any 17-C run
  python work/validate_experiment_17c_harness.py                      # harness checks
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import experiment_17_runtime as runtime  # noqa: E402
import experiment_17c_claude_runtime as claude_rt  # noqa: E402
import run_experiment_16_matched_compute as e16  # noqa: E402
import run_experiment_17_matched_compute as e17  # noqa: E402
import run_experiment_17c_claude_replication as e17c  # noqa: E402

BASELINE_JSON = PROJECT_DIR / "work" / "experiment_17c_historical_baseline.json"
OUT_DIR = PROJECT_DIR / "outputs" / "harness_validation" / "experiment_17c"
E17_PROTOCOL_SHA = "76ae7d0ae043fab1e0a34f0f34ed0380473d725cad689260d15b0f44125d5b8b"
SKIP_PARTS = {"__pycache__", ".git", "vendor", "external", "e13_data", ".venv"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_manifest() -> dict[str, str]:
    """Every file not owned by Experiment 17-C, including the original Experiment 17."""
    manifest = {}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        rel = path.relative_to(PROJECT_DIR).as_posix()
        if rel == ".env" or "17c" in rel.lower():
            continue
        manifest[rel] = sha256(path)
    return dict(sorted(manifest.items()))


# ---------------------------------------------------------------------------
# Fake CLI
# ---------------------------------------------------------------------------
class FakeClaudeCLI:
    """Deterministic stand-in for ``claude -p`` built on the E16 fake content model."""

    def __init__(self, script: list[Any] | None = None):
        self.content = e16.FakeOpenRouter()
        self.calls: list[dict[str, Any]] = []
        self.script = list(script or [])

    def __call__(self, argv, stdin_text, env, cwd, timeout):  # noqa: ARG002
        self.calls.append({"argv": argv, "prompt": stdin_text, "env_keys": sorted(env)})
        if self.script:
            action = self.script.pop(0)
            if isinstance(action, BaseException):
                raise action
            if action is not None:
                return action
        model = argv[argv.index("--model") + 1]
        self.content.served += 1
        repair = stdin_text.startswith("<<<ORIGINAL REQUEST>>>")
        prompt = stdin_text.split("<<<ORIGINAL REQUEST>>>\n", 1)[-1].split("\n<<<END ORIGINAL REQUEST>>>", 1)[0]
        text = self.content._respond(prompt, model, repair)
        result = {
            "type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
            "result": text, "structured_output": json.loads(text),
            "usage": {"input_tokens": e16._approx_tokens(stdin_text), "cache_creation_input_tokens": 7,
                      "cache_read_input_tokens": 3, "output_tokens": e16._approx_tokens(text)},
            "modelUsage": {model: {}},
        }
        return 0, json.dumps(result), ""


def cli_error(message: str, status: int | None = None) -> tuple[int, str, str]:
    body = {"type": "result", "subtype": "success", "is_error": True, "result": message,
            "api_error_status": status, "usage": {"input_tokens": 0, "output_tokens": 0}, "modelUsage": {}}
    return 1, json.dumps(body), ""


def make_client(tmp: Path, runner: FakeClaudeCLI, model: str = claude_rt.GENERATOR_MODEL):
    return claude_rt.ClaudeCodeCLIClient(
        model, tmp / "diag", cli_path=Path("fake-claude.exe"), runner=runner, sleeper=lambda s: None
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def run_checks(tmp: Path) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, passed: bool, detail: Any = "") -> None:
        checks[name] = {"passed": bool(passed), "detail": str(detail)[:500]}

    # 1. Protocol
    check("e17_base_protocol_unchanged", e17.protocol_sha256() == E17_PROTOCOL_SHA, e17.protocol_sha256())
    problems = e17c.scientific_invariants_hold()
    check("scientific_fields_identical_to_e17", not problems, problems)
    p = e17c.PROTOCOL
    check("substitutions_recorded",
          [s["experiment_17c_model"] for s in p["model_substitutions"]] == [claude_rt.GENERATOR_MODEL, claude_rt.JUDGE_MODEL]
          and p["models"]["generator"] != p["models"]["blinded_judge"] and len(p["deviations_from_experiment_17"]) >= 5,
          p["models"])
    check("historical_output_guard",
          e17c.HISTORICAL_GUARD.search("meno_j_experiment_17_matched_compute.json") is not None
          and e17c.HISTORICAL_GUARD.search("meno_j_experiment_16_matched_compute.json") is not None
          and all(e17c.HISTORICAL_GUARD.search(path.name) is None
                  for key, path in e17c.REAL_PATHS.items() if key != "checkpoints"),
          "17 and earlier protected; 17c writable")
    check("checkpoints_separate_from_e17",
          e17c.REAL_PATHS["checkpoints"] != e17.REAL_PATHS["checkpoints"]
          and not set(map(str, e17c.REAL_PATHS.values())) & set(map(str, e17.REAL_PATHS.values())),
          e17c.REAL_PATHS["checkpoints"])

    # 2. No paid API dependency
    env = claude_rt.child_env({"ANTHROPIC_API_KEY": "x", "ANTHROPIC_BASE_URL": "y", "CLAUDE_CODE_OAUTH_TOKEN": "z",
                               "CLAUDECODE": "1", "USE_LOCAL_OAUTH": "1", "PATH": "p"})
    check("child_env_strips_api_and_host_auth",
          set(env) == {"PATH", "CLAUDE_CODE_MAX_OUTPUT_TOKENS"} and env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "12000", sorted(env))
    fake = FakeClaudeCLI()
    client = make_client(tmp, fake)
    argv = client._argv("SYS", {"type": "object"})
    check("argv_subscription_mode",
          "--bare" not in argv and argv[argv.index("--tools") + 1] == "" and "--json-schema" in argv
          and argv[argv.index("--model") + 1] == claude_rt.GENERATOR_MODEL and "--no-session-persistence" in argv
          and argv[argv.index("--system-prompt") + 1] == "SYS", argv[1:12])

    # 3. Message serialization
    normal = claude_rt.serialize_messages([{"role": "system", "content": "S"}, {"role": "user", "content": "U"}])
    repair = claude_rt.serialize_messages([{"role": "system", "content": "S"}, {"role": "user", "content": "U"},
                                           {"role": "assistant", "content": "A"}, {"role": "user", "content": "FIX"}])
    check("message_serialization", normal == ("S", "U") and repair[0] == "S" and "U" in repair[1]
          and "A" in repair[1] and repair[1].endswith("FIX"), repair)

    # 4. Envelope and usage accounting through the resume-safe meter
    ledger = tmp / "ledger.jsonl"
    meter = runtime.ResumeSafeMeter(client, ledger)
    prompt = e16.baseline_sample_prompt(e16.QUESTIONS["Q1"], 1)
    with meter.ctx(unit_id="T", arm="B", stage="baseline_sample", role="generator"):
        payload = client.call_llm(prompt)
    meter.uninstall()
    row = runtime.read_jsonl(ledger)[-1]
    expected_prompt = e16._approx_tokens(prompt) + 10
    check("usage_mapping_includes_cache_tokens",
          row["usage_reported"] and row["prompt_tokens"] == expected_prompt
          and row["model_returned"] == claude_rt.GENERATOR_MODEL and len(payload["hypotheses"]) == 10, row)

    # 5. Usage limit halts without an invalid-sample record
    stop_tmp = tmp / "limit"
    runner = FakeClaudeCLI([cli_error("Claude AI usage limit reached|resets 5pm")])
    client = make_client(stop_tmp, runner)
    meter = runtime.ResumeSafeMeter(client, stop_tmp / "ledger.jsonl")
    runtime.install_experiment_17_core_hooks()
    import schema
    halted = False
    try:
        with meter.ctx(unit_id="T"):
            e16.run_arm_b((client, None, None, schema), meter, stop_tmp / "unit", e16.QUESTIONS["Q1"], 20000,
                          {"logical_calls": 7}, 1000)
    except claude_rt.SubscriptionUsageLimitReached:
        halted = True
    meter.uninstall()
    check("usage_limit_halts_without_invalid_sample",
          halted and not (stop_tmp / "unit" / "arm_b_samples" / "sample_01.json").exists(), halted)
    check("usage_limit_is_base_exception", not issubclass(claude_rt.SubscriptionUsageLimitReached, Exception)
          and not issubclass(claude_rt.ClaudeAuthUnavailable, Exception))

    # 6. OAuth refresh contention -> retries then halts as infrastructure
    msg = "Failed to refresh OAuth token: another Claude Code process is refreshing it"
    runner = FakeClaudeCLI([cli_error(msg)] * 5)
    client = make_client(tmp / "oauth", runner)
    try:
        client.call_llm(prompt)
        outcome = "returned"
    except claude_rt.ClaudeAuthUnavailable:
        outcome = "halted"
    check("oauth_refresh_retries_then_halts", outcome == "halted" and len(runner.calls) == 5, (outcome, len(runner.calls)))

    # 7. Transient overload is retried and counted
    runner = FakeClaudeCLI([cli_error("API Error: 529 Overloaded", 529)])
    client = make_client(tmp / "transient", runner)
    client.call_llm(prompt)
    stats = client.get_retry_stats()
    check("transient_error_retried", stats["transient_http_retries"] == 1 and stats["http_attempts"] == 2, stats)

    # 8. Timeout retried and counted
    import subprocess
    runner = FakeClaudeCLI([subprocess.TimeoutExpired("claude", 1)])
    client = make_client(tmp / "timeout", runner)
    client.call_llm(prompt)
    check("timeout_retried", client.get_retry_stats()["timeout_retries"] == 1, client.get_retry_stats())

    # 9. Schema failure uses the inherited one-retry shape policy, then fails the logical call
    bad = (1, json.dumps({"type": "result", "subtype": "error_max_structured_output_retries", "is_error": True,
                          "result": "could not satisfy schema", "usage": {"input_tokens": 5, "output_tokens": 5},
                          "modelUsage": {}}), "")
    runner = FakeClaudeCLI([bad, bad])
    client = make_client(tmp / "schema", runner)
    try:
        client.call_llm(prompt)
        outcome = "returned"
    except ValueError:
        outcome = "ValueError"
    check("schema_failure_single_shape_retry", outcome == "ValueError" and len(runner.calls) == 2, outcome)

    # 10. Invalid assistant JSON triggers exactly one repair request
    garbage = (0, json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "not json",
                              "usage": {"input_tokens": 5, "output_tokens": 5},
                              "modelUsage": {claude_rt.GENERATOR_MODEL: {}}}), "")
    runner = FakeClaudeCLI([garbage])
    client = make_client(tmp / "repair", runner)
    repaired = client.call_llm(prompt)
    check("json_repair_single_request", len(runner.calls) == 2 and runner.calls[1]["prompt"].startswith("<<<ORIGINAL REQUEST>>>")
          and len(repaired["hypotheses"]) == 10, len(runner.calls))

    # 10b. Amendment 1: arm failures are terminal across resumes; pauses are not failures
    e17c._install_protocol_globals()
    calls = {"n": 0}
    original = e16.run_arm_a.__closure__  # wrapper installed
    unit_dir = tmp / "durable" / "U"
    unit_dir.mkdir(parents=True)

    def boom(*a, **k):
        calls["n"] += 1
        raise schema.PipelineValidationError("synthetic Stage 5 failure")

    import pipeline as _pipeline

    class P:  # minimal engine whose pipeline always fails
        run_v4_pipeline = staticmethod(boom)

    class NullMeter:
        def ctx(self, **k):
            import contextlib
            return contextlib.nullcontext()

    engine = (None, P, None, schema)
    outcomes = []
    for _ in range(2):
        try:
            e16.run_arm_a(engine, NullMeter(), unit_dir, "q", "m")
        except Exception as exc:  # noqa: BLE001
            outcomes.append(type(exc).__name__)
    marker_written = (unit_dir / e17c.ARM_A_FAILED_MARKER).exists()

    def pause(*a, **k):
        raise claude_rt.SubscriptionUsageLimitReached("limit")

    class Q:
        run_v4_pipeline = staticmethod(pause)

    pause_dir = tmp / "durable" / "V"
    try:
        e16.run_arm_a((None, Q, None, schema), NullMeter(), pause_dir, "q", "m")
    except claude_rt.SubscriptionUsageLimitReached:
        pass
    check("arm_failure_terminal_across_resume_pause_not_failure",
          calls["n"] == 1 and outcomes == ["PipelineValidationError", "RuntimeError"] and marker_written
          and not (pause_dir / e17c.ARM_A_FAILED_MARKER).exists() and original is not None,
          (calls, outcomes, marker_written))

    # 10c. Arm B: unexpected exception is terminal ARM_B_FAILED (symmetric with Arm A), not a crash loop
    bdir = tmp / "durable" / "B"
    bdir.mkdir(parents=True)
    original_b = e16.run_arm_b._e17c_original
    bcalls = {"n": 0}

    def b_boom(*a, **k):
        bcalls["n"] += 1
        raise KeyError("synthetic arm B crash")

    e16.run_arm_b._e17c_original = b_boom
    try:
        wrapper_b = e16.run_arm_b
        e17c._durable_arm_failures()  # rewrap around b_boom
        r1 = e16.run_arm_b(None, NullMeter(), bdir, "q", 1, {}, 0)
        r2 = e16.run_arm_b(None, NullMeter(), bdir, "q", 1, {}, 0)
    finally:
        e16.run_arm_b._e17c_original = original_b
        e17c._durable_arm_failures()
    check("arm_b_failure_terminal_symmetric",
          bcalls["n"] == 1 and r1["selector_error"].startswith("KeyError") and r2 == r1
          and (bdir / e17c.ARM_B_FAILED_MARKER).exists() and wrapper_b is not None, (bcalls, r1["selector_error"]))

    # 10d. Amendment 2: usage-limit stop with no model output does not consume a judge attempt;
    #      with model output already produced, the frozen E17 consumption rule still applies.
    def judge_case(produce_output: bool) -> dict:
        jdir = tmp / "judge" / ("out" if produce_output else "none")
        jdir.mkdir(parents=True)
        led = jdir / "ledger.jsonl"
        rows = []
        if produce_output:
            rows.append({"event": "request", "arm": "JUDGE", "unit_id": "U", "seq": 1})
        rows.append({"event": "logical_call", "arm": "JUDGE", "unit_id": "U", "ok": False, "seq": 2})
        led.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        runtime.atomic_write_json(jdir / "judge_state.json", {"version": 1, "unit_id": "U", "input_fingerprint": "x",
            "terminal": False, "batches": [{"batch": 0, "status": "PENDING",
                                            "attempts": [{"attempt": 1, "status": "STARTED", "ok": None}]}]})

        class M:
            ledger_path = led
            def event(self, kind, **f):
                runtime.append_jsonl(led, {"event": kind, "seq": 99, **f})

        def stop(*a, **k):
            raise claude_rt.SubscriptionUsageLimitReached("limit")

        saved = e16.judge_unit._e17c_original
        e16.judge_unit._e17c_original = stop
        e17c._durable_arm_failures()
        try:
            e16.judge_unit(None, M(), jdir, "U", "q", {}, "m")
        except claude_rt.SubscriptionUsageLimitReached:
            pass
        finally:
            e16.judge_unit._e17c_original = saved
            e17c._durable_arm_failures()
        return runtime.read_json(jdir / "judge_state.json")

    none_state, out_state = judge_case(False), judge_case(True)
    check("judge_attempt_not_consumed_by_usage_limit_without_output",
          none_state["batches"][0]["attempts"] == [] and none_state["provider_stops"][0]["withdrawn_attempt"] == 1
          and out_state["batches"][0]["attempts"][0]["status"] == "STARTED" and "provider_stops" not in out_state,
          (none_state.get("provider_stops"), out_state["batches"][0]["attempts"]))

    # 10d-2. Retroactive reconciliation at resume (stop in a pre-amendment process); hard kill keeps E17 rule
    rdir = tmp / "reconcile"
    for uid, err in (("R1", "SubscriptionUsageLimitReached"), ("R2", None)):
        (rdir / uid).mkdir(parents=True)
        runtime.atomic_write_json(rdir / uid / "judge_state.json", {"unit_id": uid, "terminal": False, "batches": [
            {"batch": 0, "status": "PENDING", "attempts": [{"attempt": 1, "status": "STARTED", "ok": None}]}]})
    rled = rdir / "ledger.jsonl"
    rled.write_text(json.dumps({"event": "logical_call", "arm": "JUDGE", "unit_id": "R1", "ok": False,
                                "error": "SubscriptionUsageLimitReached", "seq": 5}) + "\n", encoding="utf-8")
    saved_ck = e17c.REAL_PATHS["checkpoints"]
    e17c.REAL_PATHS["checkpoints"] = rdir
    try:
        withdrawn = e17c.reconcile_provider_stopped_judge_attempts(rled)
    finally:
        e17c.REAL_PATHS["checkpoints"] = saved_ck
    r2 = runtime.read_json(rdir / "R2" / "judge_state.json")
    check("judge_reconciliation_at_resume_evidence_only",
          withdrawn == ["R1"] and r2["batches"][0]["attempts"][0]["status"] == "STARTED", withdrawn)

    # 10d-3. Amendment 3: real Pro session-limit message is a quota stop, not a transient error
    msg_limit = "You've hit your session limit · resets 8:20am (Asia/Kolkata)"
    runner = FakeClaudeCLI([cli_error(msg_limit, 429)])
    client = make_client(tmp / "sessionlimit", runner)
    try:
        client.call_llm(prompt)
        sl = "returned"
    except claude_rt.SubscriptionUsageLimitReached:
        sl = "halted"
    check("session_limit_message_halts_immediately",
          sl == "halted" and len(runner.calls) == 1
          and not claude_rt.is_usage_limit("API Error: Claude's response exceeded the 12000 output token maximum", None),
          (sl, len(runner.calls)))

    # 10d-4. Amendment 3: evidence-based reclassification + provider-stop-aware call counts + orphans
    adir = tmp / "a3"
    (adir / "diag").mkdir(parents=True)
    arch = runtime.DiagnosticArchive(adir / "diag")
    for body in ([{"is_error": True, "api_error_status": 429, "result": msg_limit, "usage": {"output_tokens": 0}}] * 2
                 + [{"is_error": True, "api_error_status": None, "result": "exceeded output token maximum",
                     "usage": {"output_tokens": 48000}}]
                 + [{"is_error": True, "api_error_status": 429, "result": msg_limit, "usage": {"output_tokens": 0}}]):
        arch.capture("cli_result", body=json.dumps(body))
    arows = [
        {"seq": 1, "event": "request_failed", "unit_id": "U", "arm": "A", "stage": "stage_5_auditor",
         "error": "RuntimeError", "http_attempts": 2},
        {"seq": 2, "event": "logical_call", "unit_id": "U", "arm": "A", "stage": "stage_5_auditor", "role": "evaluator",
         "ok": False, "error": "RuntimeError"},
        {"seq": 3, "event": "request_failed", "unit_id": "U", "arm": "B", "stage": "baseline_sample",
         "error": "RuntimeError", "http_attempts": 1},
        {"seq": 4, "event": "logical_call", "unit_id": "U", "arm": "B", "stage": "baseline_sample", "role": "generator",
         "ok": False, "error": "RuntimeError"},
    ]
    items = e17c.provider_stop_reclassifications(arows, adir / "diag")
    sim = arows + [{"event": "provider_stop_reclassified", "seq": 10, **items[0]}] if items else arows
    ba = e16.summarize_budget(sim, "U", "A")
    bb = e16.summarize_budget(sim, "U", "B")
    orphans = e17c.orphan_captures(arows, adir / "diag")
    check("amendment3_reclassify_only_zero_output_quota_refusals",
          len(items) == 1 and items[0]["target_seqs"] == [1, 2] and ba["evaluator_calls"] == 0
          and ba["provider_refused_logical_calls"] == 1 and ba["http_attempts"] == 2
          and bb["generator_calls"] == 1 and bb["provider_refused_logical_calls"] == 0 and orphans == [4]
          and e17c.provider_stop_reclassifications(sim, adir / "diag") == [],
          (items, ba["evaluator_calls"], bb["generator_calls"], orphans))

    # 10d-5. find_cli sees the MSIX package-private CLI copy (Task Scheduler context)
    import os as _os
    fake_local = tmp / "localappdata"
    exe = fake_local / "Packages" / "Claude_test" / "LocalCache" / "Roaming" / "Claude" / "claude-code" / "9.9.9" / "claude.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    saved_env = {k: _os.environ.get(k) for k in ("LOCALAPPDATA", "MINOS_J_CLAUDE_CLI")}
    saved_default = claude_rt.DEFAULT_CLI_PATH
    _os.environ["LOCALAPPDATA"] = str(fake_local)
    _os.environ.pop("MINOS_J_CLAUDE_CLI", None)
    claude_rt.DEFAULT_CLI_PATH = tmp / "nonexistent"
    try:
        found = claude_rt.find_cli()
    finally:
        claude_rt.DEFAULT_CLI_PATH = saved_default
        for k, v in saved_env.items():
            if v is None:
                _os.environ.pop(k, None)
            else:
                _os.environ[k] = v
    check("find_cli_msix_package_fallback", found == exe, found)

    # 10e. Single scientific process: a live lock holder blocks a second run (exit 73)
    import os
    saved_lock = e17c.RUN_LOCK
    e17c.RUN_LOCK = tmp / "run.lock"
    e17c.RUN_LOCK.write_text(str(os.getpid()))
    try:
        e17c._acquire_run_lock()
        lock_outcome = "acquired"
    except SystemExit as exc:
        lock_outcome = exc.code
    e17c.RUN_LOCK.write_text("999999")  # dead holder -> reclaimed
    e17c._acquire_run_lock()
    reclaimed = e17c.RUN_LOCK.read_text() == str(os.getpid())
    e17c.RUN_LOCK = saved_lock
    check("runner_single_process_lock", lock_outcome == 73 and reclaimed, (lock_outcome, reclaimed))

    # 10f. Completed results cannot be regenerated by re-running
    saved_report = e17c.REAL_PATHS["report_json"]
    e17c.REAL_PATHS["report_json"] = tmp / "report.json"
    e17c.REAL_PATHS["report_json"].write_text("{}")
    try:
        e17c.run_real(["--run"])
        rerun = "ran"
    except SystemExit as exc:
        rerun = str(exc.code)
    e17c.REAL_PATHS["report_json"] = saved_report
    check("rerun_refused_after_final_report", "already exists" in rerun, rerun)

    # 10g. Supervisor lifecycle: self-removal on completion, disable on crash loop / integrity refusal
    sys.path.insert(0, str(PROJECT_DIR / "work"))
    import experiment_17c_tick as tick
    calls_log: list[tuple] = []
    saved_tick = {k: getattr(tick, k) for k in ("schtasks", "WORK", "LOG", "LOCK", "CHECKPOINTS", "EVENTS", "REPORT",
                                                  "VALIDATION", "STATE", "RUN_LOG", "processes", "run",
                                                  "clear_stale_oauth_lock")}
    twork = tmp / "tick"
    (twork / "ckpt").mkdir(parents=True)
    tick.schtasks = lambda *a: calls_log.append(a) or 0
    tick.WORK, tick.LOG, tick.LOCK = twork, twork / "sup.log", twork / "tick.lock"
    tick.CHECKPOINTS, tick.EVENTS = twork / "ckpt", twork / "ckpt" / "events.jsonl"
    tick.REPORT, tick.VALIDATION, tick.STATE = twork / "report.json", twork / "validation.json", twork / "state.json"
    tick.RUN_LOG = twork / "run.log"
    tick.processes = lambda: []
    tick.clear_stale_oauth_lock = lambda procs: None
    exits = iter([1, 1, 1])
    tick.run = lambda args, log_path: next(exits)
    try:
        for _ in range(3):
            tick.main()
        crash_disabled = calls_log == [("/Change", "/DISABLE")]
        calls_log.clear()
        tick.REPORT.write_text("{}")
        tick.VALIDATION.write_text("{}")
        tick.main()
        removed = calls_log == [("/Delete", "/F")]
        calls_log.clear()
        tick.REPORT.unlink()
        (twork / "ckpt" / "U").mkdir()
        (twork / "ckpt" / "U" / "stage.json").write_text('{"trunc')
        tick.main()
        integrity_disabled = calls_log == [("/Change", "/DISABLE")]
        task_name_only = tick.TASK_NAME == "MinosJ-Experiment17C-Supervisor"
    finally:
        for k, v in saved_tick.items():
            setattr(tick, k, v)
    check("supervisor_lifecycle_remove_on_completion_disable_on_failure",
          crash_disabled and removed and integrity_disabled and task_name_only,
          (crash_disabled, removed, integrity_disabled))

    # 11. End-to-end fake unit through the unchanged E16/E17 scientific core
    import pipeline
    import prompts
    e17c._install_protocol_globals()
    paths = {key: tmp / "e2e" / Path(path).name for key, path in e17c.REAL_PATHS.items()}
    runner = FakeClaudeCLI()
    client = make_client(tmp / "e2e", runner)
    meter = runtime.ResumeSafeMeter(client, paths["checkpoints"] / "request_ledger.jsonl")
    units = []
    try:
        for qid in ("Q1", "Q2"):
            units.append(e16.run_unit((client, pipeline, prompts, schema), meter, paths, qid, 1,
                                      claude_rt.GENERATOR_MODEL, claude_rt.JUDGE_MODEL))
    finally:
        meter.uninstall()
    report = e16.build_report(units, "fake_harness_validation", claude_rt.GENERATOR_MODEL, claude_rt.JUDGE_MODEL, [], "FAKE")
    judge_models = {json.loads(line).get("model_requested") for line in
                    (paths["checkpoints"] / "request_ledger.jsonl").read_text(encoding="utf-8").splitlines()
                    if '"arm": "JUDGE"' in line and '"event": "request"' in line}
    check("end_to_end_fake_units",
          all(u["status"] == "COMPLETE" for u in units) and judge_models == {claude_rt.JUDGE_MODEL}
          and report["verdict"] == e16.FAKE_VERDICT,
          [(u["unit_id"], u["status"], u.get("token_ratio_B_over_A")) for u in units])
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-baseline", action="store_true")
    args = parser.parse_args()
    if args.capture_baseline:
        if e17c.REAL_PATHS["report_json"].exists() or (e17c.REAL_PATHS["checkpoints"] / "request_ledger.jsonl").exists():
            raise SystemExit("Refusing to capture a baseline after Experiment 17-C execution began.")
        manifest = historical_manifest()
        runtime.atomic_write_json(BASELINE_JSON, {
            "purpose": "Pre-execution integrity baseline for Experiment 17-C (covers Experiments 1-17)",
            "e17_protocol_sha256": e17.protocol_sha256(),
            "file_count": len(manifest),
            "manifest": manifest,
        })
        print(f"Captured baseline: {len(manifest)} files")
        return

    before = historical_manifest()
    tmp = Path(tempfile.mkdtemp(prefix="minosj_e17c_harness_"))
    try:
        checks = run_checks(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    after = historical_manifest()
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    checks["historical_files_untouched_by_validation"] = {"passed": not changed, "detail": str(changed[:10])}
    if BASELINE_JSON.exists():
        base = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))["manifest"]
        drift = sorted(k for k in base.keys() | after.keys() if base.get(k) != after.get(k))
        checks["historical_files_match_baseline"] = {"passed": not drift, "detail": str(drift[:10])}
    passed = all(c["passed"] for c in checks.values())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"artifact": "Experiment 17-C harness validation (fake CLI; not a scientific result)",
               "status": "PASSED" if passed else "FAILED",
               "passed": sum(c["passed"] for c in checks.values()), "total": len(checks), "checks": checks}
    runtime.atomic_write_json(OUT_DIR / "meno_j_experiment_17c_harness_validation.json", payload)
    for name, c in checks.items():
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {name}  {c['detail'][:160]}")
    print(f"Harness validation: {payload['status']} ({payload['passed']}/{payload['total']})")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
