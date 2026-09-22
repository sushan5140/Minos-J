"""Minos-J Experiment 17-C: Claude-based replication of Experiment 17.

Experiment 17 was interrupted by OpenRouter's free-tier daily quota after
partial progress on units Q1-r1, Q2-r1 and Q3-r1.  Its frozen models are only
reachable through OpenRouter, so it cannot be completed as preregistered
without that provider.  Experiment 17 records are preserved unchanged.

Experiment 17-C re-runs the complete Experiment 17 design (all nine units,
fresh) with Claude models executed through the Claude Code CLI on the
operator's existing Claude subscription.  The questions, arms, matched-compute
rule, blinded evaluation, outcomes, statistics and falsification criterion are
the Experiment 17 protocol objects themselves; only fields that the model
substitution forces to change are altered, and every alteration is listed in
``model_substitutions`` and ``deviations_from_experiment_17``.

No Experiment 17 checkpoint, card, judgment or ledger row is reused, and
results must never be pooled with Experiment 17 units.

Modes:
  --write-protocol   freeze the 17-C protocol (refuses to overwrite a different one)
  --preflight        local checks + CLI auth check; no model completion
  --run              scientific execution (resumable; re-run the same command)
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import experiment_17_runtime as runtime
import experiment_17c_claude_runtime as claude_rt
import run_experiment_16_matched_compute as e16
import run_experiment_17_matched_compute as e17


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
WORK_DIR = PROJECT_DIR / "work"
EXPERIMENT_NAME = "Minos-J Experiment 17-C: Claude-Based Replication of Experiment 17 (Matched-Compute Architecture Falsification)"
SLUG = "meno_j_experiment_17c_matched_compute"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_experiment_17c_preregistered_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_experiment_17c_preregistered_protocol.md"
REAL_PATHS = {
    "checkpoints": WORK_DIR / "experiment_17c_checkpoints",
    "report_json": OUTPUT_DIR / f"{SLUG}.json",
    "report_md": OUTPUT_DIR / f"{SLUG}.md",
    "raw_units": OUTPUT_DIR / f"{SLUG}_raw_units.jsonl",
    "raw_requests": OUTPUT_DIR / f"{SLUG}_raw_requests.jsonl",
    "judgments": OUTPUT_DIR / f"{SLUG}_judgments.jsonl",
    "aggregate_csv": OUTPUT_DIR / f"{SLUG}_aggregate.csv",
    "budget_csv": OUTPUT_DIR / f"{SLUG}_budget_accounting.csv",
    "repro_json": OUTPUT_DIR / "meno_j_experiment_17c_reproducibility_summary.json",
    "repro_md": OUTPUT_DIR / "meno_j_experiment_17c_reproducibility_summary.md",
}
# Experiments 1-17 (including the interrupted original 17) are historical here.
HISTORICAL_GUARD = re.compile(
    r"meno_j_(experiment_(?:[1-9]|1[0-7])(?:_|$)|theory_study|wesad|literature|complete|falsification)"
)


def _build_protocol() -> dict[str, Any]:
    protocol = copy.deepcopy(e17.PROTOCOL)
    gen, judge = claude_rt.GENERATOR_MODEL, claude_rt.JUDGE_MODEL
    protocol.update({
        "experiment_name": EXPERIMENT_NAME,
        "protocol_status": "FROZEN_BEFORE_ANY_EXPERIMENT_17C_COMPLETION_CALL",
        "frozen_on": "2026-09-23",
        "naming_note": (
            "Experiment 17-C is the Claude-based replication of Experiment 17. Experiment 17 (OpenRouter, "
            "nvidia/nemotron-3-super-120b-a12b:free + nex-agi/nex-n2.5-pro:free) was interrupted by the "
            "OpenRouter free-tier daily quota and is preserved unchanged as an incomplete run."
        ),
        "relation_to_experiment_17": {
            "base_protocol": "outputs/meno_j_experiment_17_preregistered_protocol.json",
            "base_protocol_sha256": e17.protocol_sha256(),
            "reuse_of_experiment_17_state": "none; all nine units run fresh under separate checkpoints",
            "pooling": "Experiment 17-C units are never pooled with Experiment 17 units",
            "experiment_17_state_at_handover": {
                "Q1-r1": "Arm A stages 4-4.3 checkpointed; Stage 5 auditor failed validation twice; no Arm B",
                "Q2-r1": "Arms A and B complete; judge attempt 1 invalid, attempt 2 started but never checkpointed (consumed under the E17 rule, so JUDGE_FAILED on resume)",
                "Q3-r1": "Arm A complete; Arm B samples 1-2 valid, sample 3 recorded invalid by an HTTP 429 before the daily-quota stop",
                "r2_and_r3_units": "not started",
            },
        },
        "models": {
            "generator": gen,
            "blinded_judge": judge,
            "separation_rule": (
                "Generator and judge are different exact model IDs, frozen before execution. Both are Anthropic "
                "Claude models, so the Experiment 17 different-family requirement cannot be met (see deviations)."
            ),
            "transport": "Claude Code CLI headless mode (`claude -p`), authenticated by the operator's Claude subscription (OAuth, authMethod=claude.ai)",
            "structured_output": "`--json-schema` with the identical strict stage-specific schema used by Experiment 17",
            "effort": claude_rt.EFFORT,
            "max_output_tokens": claude_rt.MAX_OUTPUT_TOKENS,
            "paid_api_dependency": "none; API-key and base-URL variables are stripped from the CLI environment",
        },
        "model_substitutions": [
            {
                "role": "generator (both arms)",
                "experiment_17_model": runtime.RECOMMENDED_GENERATOR_MODEL,
                "experiment_17_provider": "OpenRouter free tier",
                "experiment_17c_model": gen,
                "experiment_17c_provider": "Claude Code CLI on Claude subscription",
                "reason": "OpenRouter free-tier quota exhausted mid-run; the operator directed continuation without OpenRouter or paid APIs.",
            },
            {
                "role": "blinded judge",
                "experiment_17_model": runtime.RECOMMENDED_JUDGE_MODEL,
                "experiment_17_provider": "OpenRouter free tier",
                "experiment_17c_model": judge,
                "experiment_17c_provider": "Claude Code CLI on Claude subscription",
                "reason": "Same as generator; a stronger Claude model than the generator is used as judge.",
            },
        ],
        "deviations_from_experiment_17": [
            "Models substituted as listed in model_substitutions; generator and judge share a vendor family (Anthropic), whereas Experiment 17 required different families. Same-family judge bias is a declared threat to validity.",
            "Sampling temperature cannot be set through `claude -p`; provider default is used instead of 0.4. It is identical for both arms.",
            "Output ceiling set with CLAUDE_CODE_MAX_OUTPUT_TOKENS=12000 (Experiment 17: max_tokens=12000). Effort pinned to 'medium' for every call.",
            "Structured output enforced by Claude Code `--json-schema` instead of OpenRouter response_format/provider.require_parameters.",
            "Token currency: prompt_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens; completion_tokens = output_tokens (includes any thinking). Applied identically to both arms and the judge.",
            "Each CLI call carries a fixed overhead of roughly 1k prompt tokens (system prompt plus Claude Code's structured-output tool); it is counted in every request of both arms and the judge. Structured output may use a second internal turn, whose tokens are also counted.",
            "The single JSON-repair request is sent as one user turn quoting the original request and previous response, because `claude -p` accepts one user message.",
            "Transient-retry classes map to CLI failures: timeout, non-JSON CLI exit, HTTP 429 (non-quota)/5xx/529, and OAuth-refresh contention. The four-retry ceiling is unchanged.",
            "A subscription usage-limit stop is treated like Experiment 17's daily-quota stop: the run halts, nothing is charged to an arm as an invalid sample, and the same command resumes later. (Experiment 17's Q3-r1 sample 3 shows the defect this avoids.)",
            "Persistent OAuth-refresh failure halts the run (infrastructure) instead of failing a stage.",
        ],
        "engineering_reliability_contract": {
            **e17.PROTOCOL["engineering_reliability_contract"],
            "structured_output": "Every completion request carries the strict Experiment 17 stage-specific JSON schema via --json-schema.",
            "diagnostics": (
                "Every CLI JSON result (including errors) is retained in a diagnostic archive with exit code and "
                "stderr tail. No credentials are read or stored by the harness. Diagnostics are not scientific outcomes."
            ),
        },
        "estimated_requirements": {
            "experimental_units": 9,
            "logical_calls": "approximately 72-234 including judge calls (same design as Experiment 17)",
            "token_planning_range": "approximately 1.6-2.2M experimental-arm tokens plus 0.3-0.6M judge tokens",
            "cost": "no per-token charge; consumes Claude subscription usage allowance",
            "operational_warning": "Subscription usage windows will likely be exhausted several times; the run is resumable.",
        },
    })
    protocol.pop("estimated_api_requirements", None)
    protocol["held_constant"]["underlying_model"] = f"Exact frozen generator model {gen} for both arms."
    protocol["held_constant"]["model_settings"] = (
        f"claude -p with provider-default temperature, effort {claude_rt.EFFORT}, max output "
        f"{claude_rt.MAX_OUTPUT_TOKENS} tokens, identical system message, identical strict JSON schema per task "
        "type, identical retry policy for both arms"
    )
    protocol["evaluation"]["judge"] = f"blinded LLM judge {judge}; different model from the generator (same vendor family)"
    protocol["falsification_criterion"]["statement"] = protocol["falsification_criterion"]["statement"].replace(
        "Experiment 17 does NOT", "Experiment 17-C does NOT"
    )
    return protocol


PROTOCOL = _build_protocol()

# Fields a replication may change.  Everything else must equal Experiment 17.
ALLOWED_CHANGED_KEYS = {
    "experiment_name", "protocol_status", "frozen_on", "naming_note", "models", "engineering_reliability_contract",
    "estimated_api_requirements", "held_constant", "evaluation", "falsification_criterion",
    "relation_to_experiment_17", "model_substitutions", "deviations_from_experiment_17", "estimated_requirements",
    "changes_from_experiment_16",
}


def scientific_invariants_hold() -> list[str]:
    """Return the scientific protocol fields that differ from Experiment 17 beyond the declared substitutions."""
    problems = [key for key in set(PROTOCOL) | set(e17.PROTOCOL)
                if key not in ALLOWED_CHANGED_KEYS and PROTOCOL.get(key) != e17.PROTOCOL.get(key)]
    base_eval, eval_17c = dict(e17.PROTOCOL["evaluation"]), dict(PROTOCOL["evaluation"])
    base_eval.pop("judge"), eval_17c.pop("judge")
    if base_eval != eval_17c:
        problems.append("evaluation (beyond judge model)")
    base_held, held_17c = dict(e17.PROTOCOL["held_constant"]), dict(PROTOCOL["held_constant"])
    for key in ("underlying_model", "model_settings"):
        base_held.pop(key), held_17c.pop(key)
    if base_held != held_17c:
        problems.append("held_constant (beyond model fields)")
    base_fc, fc_17c = dict(e17.PROTOCOL["falsification_criterion"]), dict(PROTOCOL["falsification_criterion"])
    base_fc.pop("statement"), fc_17c.pop("statement")
    if base_fc != fc_17c:
        problems.append("falsification_criterion (beyond experiment label)")
    return problems


def protocol_sha256() -> str:
    return hashlib.sha256(runtime.strict_json_dumps(PROTOCOL, sort_keys=True).encode("utf-8")).hexdigest()


def protocol_markdown() -> str:
    p = PROTOCOL
    subs = "\n".join(
        f"| {s['role']} | `{s['experiment_17_model']}` ({s['experiment_17_provider']}) | "
        f"`{s['experiment_17c_model']}` ({s['experiment_17c_provider']}) |"
        for s in p["model_substitutions"]
    )
    deviations = "\n".join(f"- {item}" for item in p["deviations_from_experiment_17"])
    handover = "\n".join(f"- {k}: {v}" for k, v in p["relation_to_experiment_17"]["experiment_17_state_at_handover"].items())
    decisions = "\n".join(f"- `{k}`: {v}" for k, v in p["falsification_criterion"]["decisions"].items())
    return f"""# {EXPERIMENT_NAME} — Preregistered Protocol

> Frozen before any Experiment 17-C model-completion call. Experiment 17 and all earlier experiments remain unchanged.

## Relation to Experiment 17

Experiment 17 stopped when the OpenRouter free-tier daily quota ran out. It cannot be completed as preregistered without OpenRouter. Experiment 17-C re-runs the whole Experiment 17 design with Claude models. It reuses no Experiment 17 state and never pools results with it.

- Base protocol SHA-256 (Experiment 17): `{p['relation_to_experiment_17']['base_protocol_sha256']}`

Experiment 17 state at handover:

{handover}

## Research question

{p['research_question']}

## Model substitutions

| Role | Experiment 17 | Experiment 17-C |
|---|---|---|
{subs}

Transport: {p['models']['transport']}. Paid API dependency: {p['models']['paid_api_dependency']}.

## Deviations from Experiment 17

{deviations}

## Unchanged from Experiment 17

- Questions Q1-Q3 × 3 replicates = 9 units.
- Arm A: historical Minos-J v4 multi-stage pipeline. Arm B: one-shot sampling plus one strict selector/verifier.
- Budget tolerance: `{p['matched_compute_rule']['tolerance']}`.
- Blinded, pooled, shuffled judging, with the same checklist and the same two-attempt judge limit.
- Primary outcome: {p['metrics']['primary']}
- Analysis set: {p['falsification_criterion']['analysis_set']}
- Statistics: {p['falsification_criterion']['statistics']}
- Criterion: {p['falsification_criterion']['statement']}

{decisions}

## Integrity

- Protocol SHA-256 (canonical JSON): `{protocol_sha256()}`
"""


def write_protocol() -> None:
    problems = scientific_invariants_hold()
    if problems:
        raise SystemExit(f"Refusing to freeze: scientific fields differ from Experiment 17: {problems}")
    if PROTOCOL_JSON.exists():
        if json.loads(PROTOCOL_JSON.read_text(encoding="utf-8")) != PROTOCOL:
            raise SystemExit("Refusing to overwrite a different frozen Experiment 17-C protocol.")
    else:
        runtime.atomic_write_json(PROTOCOL_JSON, PROTOCOL)
    PROTOCOL_MD.write_text(protocol_markdown(), encoding="utf-8")
    print(f"Experiment 17-C protocol frozen: {PROTOCOL_JSON} (sha256 {protocol_sha256()})")


def require_protocol() -> None:
    if not PROTOCOL_JSON.exists():
        raise SystemExit("Experiment 17-C protocol is not frozen; run --write-protocol first.")
    if json.loads(PROTOCOL_JSON.read_text(encoding="utf-8")) != PROTOCOL:
        raise SystemExit("Experiment 17-C protocol on disk differs from the runner; refusing to continue.")
    if e17.protocol_sha256() != PROTOCOL["relation_to_experiment_17"]["base_protocol_sha256"]:
        raise SystemExit("Experiment 17 base protocol changed; refusing to continue.")


def preflight() -> dict[str, Any]:
    require_protocol()
    problems = scientific_invariants_hold()
    cli = claude_rt.find_cli()
    version = claude_rt.cli_version(cli)
    auth = claude_rt.auth_status(cli)
    if auth.get("authMethod") != "claude.ai" or not auth.get("loggedIn"):
        problems.append(f"CLI must be logged in with a Claude subscription (authMethod=claude.ai); got {auth}")
    if claude_rt.GENERATOR_MODEL == claude_rt.JUDGE_MODEL:
        problems.append("generator and judge model must differ")
    print(f"Claude Code CLI: {cli} ({version})")
    print(f"Auth: {auth}")
    print(f"Generator model: {claude_rt.GENERATOR_MODEL}")
    print(f"Judge model: {claude_rt.JUDGE_MODEL}")
    print("PREFLIGHT OK" if not problems else "PREFLIGHT FAILED: " + "; ".join(problems))
    if problems:
        raise SystemExit(1)
    return {"cli": str(cli), "cli_version": version, "auth": auth}


def _install_protocol_globals() -> None:
    runtime.install_experiment_17_core_hooks()
    e16.EXPERIMENT_16_NAME = EXPERIMENT_NAME
    e16.PROTOCOL = PROTOCOL


def _write_outputs(report: dict[str, Any], units: list[dict[str, Any]], ledger_path: Path, env_info: dict[str, Any]) -> None:
    original_guard = e16.HISTORICAL_OUTPUT_PATTERN
    e16.HISTORICAL_OUTPUT_PATTERN = HISTORICAL_GUARD
    try:
        e16.write_outputs(REAL_PATHS, runtime.strict_json_ready(report), runtime.strict_json_ready(units), ledger_path)
    finally:
        e16.HISTORICAL_OUTPUT_PATTERN = original_guard
    repro = json.loads(REAL_PATHS["repro_json"].read_text(encoding="utf-8"))
    repro.update({
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "claude_runtime_sha256": hashlib.sha256((PROJECT_DIR / "experiment_17c_claude_runtime.py").read_bytes()).hexdigest(),
        "e17_runtime_sha256": hashlib.sha256((PROJECT_DIR / "experiment_17_runtime.py").read_bytes()).hexdigest(),
        "e17_protocol_sha256": e17.protocol_sha256(),
        "claude_code_cli_version": env_info.get("cli_version"),
        "historical_experiment_17_modified": False,
    })
    runtime.atomic_write_json(REAL_PATHS["repro_json"], repro)


def run_real(argv: list[str]) -> dict[str, Any]:
    env_info = preflight()
    _install_protocol_globals()
    import pipeline
    import prompts
    import schema

    generator, judge = claude_rt.GENERATOR_MODEL, claude_rt.JUDGE_MODEL
    client = claude_rt.ClaudeCodeCLIClient(
        generator, REAL_PATHS["checkpoints"] / "diagnostic_responses", cli_path=Path(env_info["cli"])
    )
    engine = (client, pipeline, prompts, schema)
    ledger_path = REAL_PATHS["checkpoints"] / "request_ledger.jsonl"
    meter = runtime.ResumeSafeMeter(client, ledger_path)
    meter.event("session_start", cli_version=env_info["cli_version"], protocol_sha256=protocol_sha256())
    units = []
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        for replicate in range(1, PROTOCOL["task_set"]["replicates_per_question"] + 1):
            for question_id in e16.QUESTIONS:
                print(f"[E17-C] unit {question_id}-r{replicate}", flush=True)
                units.append(e16.run_unit(engine, meter, REAL_PATHS, question_id, replicate, generator, judge))
    except (claude_rt.SubscriptionUsageLimitReached, claude_rt.ClaudeAuthUnavailable) as stop:
        meter.event("session_paused", reason=type(stop).__name__)
        print(f"[E17-C] PAUSED: {stop} Re-run the same command to resume.", flush=True)
        raise SystemExit(75)
    finally:
        meter.uninstall()
    command = "python " + " ".join([Path(__file__).name, *argv])
    report = e16.build_report(units, "real", generator, judge, [command], started)
    report.update({
        "experiment_name": EXPERIMENT_NAME,
        "protocol_sha256": protocol_sha256(),
        "provenance": (
            "Generated by the separately preregistered Experiment 17-C Claude replication harness. "
            "Experiment 17 and Experiments 1-16 were not overwritten or pooled."
        ),
        "model_substitutions": PROTOCOL["model_substitutions"],
        "deviations_from_experiment_17": PROTOCOL["deviations_from_experiment_17"],
        "claude_code_cli_version": env_info["cli_version"],
        "protocol_deviation": None,
    })
    _write_outputs(report, units, ledger_path, env_info)
    print(f"Verdict: {report['verdict']}", flush=True)
    return report


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=EXPERIMENT_NAME)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-protocol", action="store_true")
    group.add_argument("--preflight", action="store_true", help="local checks and CLI auth status; no model completion")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.write_protocol:
        write_protocol()
    elif args.preflight:
        preflight()
    else:
        require_protocol()
        run_real(argv)


if __name__ == "__main__":
    main()
