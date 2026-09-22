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
