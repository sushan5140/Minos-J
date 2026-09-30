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


ARM_A_FAILED_MARKER = "arm_a_failed.json"
ARM_B_FAILED_MARKER = "arm_b_failed.json"


def _durable_arm_failures() -> None:
    """Make arm failures terminal across resumed processes (amendment 1, 2026-09-23).

    The inherited core checkpoints arm successes but not arm failures, so a
    resumed process would silently grant a failed arm another attempt, making a
    unit's outcome depend on whether an interruption happened (this occurred in
    Experiment 17 for Q1-r1 Stage 5).  Mirroring Experiment 17's rule for judge
    attempts, a model/validation failure (``Exception``) is persisted and replayed
    on resume.  Usage-limit/auth stops are ``BaseException`` and are never
    persisted, so pausing cannot fail an arm.
    """
    # Idempotent: E17 hooks may have been re-installed (replacing judge_unit), so
    # unwrap to the current underlying functions before wrapping again.
    original_a = getattr(e16.run_arm_a, "_e17c_original", e16.run_arm_a)
    original_b = getattr(e16.run_arm_b, "_e17c_original", e16.run_arm_b)

    def run_arm_a(engine, meter, unit_dir: Path, question: str, model: str):
        marker = unit_dir / ARM_A_FAILED_MARKER
        stored = runtime.read_json(marker)
        if stored is not None:
            raise RuntimeError(f"{stored['error']} [terminal; recorded {stored['recorded_at_utc']}]")
        try:
            return original_a(engine, meter, unit_dir, question, model)
        except Exception as exc:
            runtime.atomic_write_json(marker, {
                "status": "ARM_A_FAILED", "error": f"{type(exc).__name__}: {str(exc)[:300]}",
                "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            raise

    def run_arm_b(engine, meter, unit_dir: Path, *args, **kwargs):
        stored = runtime.read_json(unit_dir / ARM_B_FAILED_MARKER)
        if stored is not None:
            return stored["result"]
        try:
            result = original_b(engine, meter, unit_dir, *args, **kwargs)
        except Exception as exc:  # symmetric with Arm A: unexpected failures are terminal, not crash loops
            result = {"samples": [], "k_samples": 0, "k_cap": 0, "pool_size": 0, "selected": [], "audits": [],
                      "selector_error": f"{type(exc).__name__}: {str(exc)[:200]}", "cards": []}
        if result.get("selector_error"):
            runtime.atomic_write_json(unit_dir / ARM_B_FAILED_MARKER, {
                "status": "ARM_B_FAILED", "result": result,
                "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
        return result

    original_judge = getattr(e16.judge_unit, "_e17c_original", e16.judge_unit)

    def judge_unit(engine, meter, unit_dir: Path, unit_id: str, *args, **kwargs):
        """Amendment 2: a provider stop that produced no model output is not a judge attempt."""
        try:
            return original_judge(engine, meter, unit_dir, unit_id, *args, **kwargs)
        except (claude_rt.SubscriptionUsageLimitReached, claude_rt.ClaudeAuthUnavailable) as stop:
            rows = runtime.read_jsonl(meter.ledger_path)
            judge_calls = [i for i, r in enumerate(rows)
                           if r.get("event") == "logical_call" and r.get("arm") == "JUDGE" and r.get("unit_id") == unit_id]
            start = judge_calls[-2] + 1 if len(judge_calls) >= 2 else 0
            end = judge_calls[-1] if judge_calls else len(rows)
            produced = any(r.get("event") == "request" and r.get("arm") == "JUDGE" and r.get("unit_id") == unit_id
                           for r in rows[start:end])
            state_path = unit_dir / "judge_state.json"
            state = runtime.read_json(state_path)
            if state is not None and not produced:
                for batch in state.get("batches", []):
                    attempts = batch.get("attempts", [])
                    if attempts and attempts[-1].get("status") == "STARTED":
                        withdrawn = attempts.pop()
                        state.setdefault("provider_stops", []).append({
                            "batch": batch.get("batch"), "withdrawn_attempt": withdrawn.get("attempt"),
                            "reason": type(stop).__name__, "model_output_produced": False,
                            "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        })
                        runtime.atomic_write_json(state_path, state)
                        meter.event("judge_attempt_not_sent", batch=batch.get("batch"), reason=type(stop).__name__)
                        break
            raise

    run_arm_a._e17c_original = original_a
    run_arm_b._e17c_original = original_b
    judge_unit._e17c_original = original_judge
    e16.run_arm_a, e16.run_arm_b, e16.judge_unit = run_arm_a, run_arm_b, judge_unit


PROVIDER_STOP_ERRORS = {"SubscriptionUsageLimitReached", "ClaudeAuthUnavailable"}


def provider_stop_reclassifications(ledger_rows: list[dict[str, Any]], diagnostic_dir: Path) -> list[dict[str, Any]]:
    """Amendment 3: find request_failed rows that were subscription quota refusals misclassified as RuntimeError.

    Each HTTP/CLI attempt produces exactly one ``cli_result``/``cli_timeout`` capture, in order,
    so walking request/request_failed rows by ``http_attempts`` maps every row to its raw
    captures.  A row qualifies only if EVERY mapped capture is HTTP 429, mentions a limit, and
    reports zero output tokens (no model output).  Already-reclassified rows are skipped.
    """
    import experiment_17c_claude_runtime as rt17c
    captures = []
    for path in sorted(diagnostic_dir.glob("response_*.json")):
        record = runtime.read_json(path)
        if record.get("classification") in ("cli_result", "cli_timeout"):
            captures.append(record)
    done = {seq for r in ledger_rows if r.get("event") == "provider_stop_reclassified" for seq in r.get("target_seqs", [])}
    found, cursor = [], 0
    for index, row in enumerate(ledger_rows):
        if row.get("event") not in ("request", "request_failed"):
            continue
        segment = captures[cursor:cursor + int(row.get("http_attempts", 0))]
        cursor += int(row.get("http_attempts", 0))
        if row["event"] != "request_failed" or row.get("error") != "RuntimeError" or row["seq"] in done:
            continue
        evidence = []
        for capture in segment:
            try:
                body = json.loads(capture.get("body", ""))
            except (TypeError, json.JSONDecodeError):
                body = None
            if not (isinstance(body, dict) and body.get("is_error") and body.get("api_error_status") == 429
                    and rt17c.is_usage_limit(str(body.get("result", "")), 429)
                    and int((body.get("usage") or {}).get("output_tokens") or 0) == 0):
                evidence = []
                break
            evidence.append(capture["archive_sequence"])
        if not evidence or len(evidence) != int(row.get("http_attempts", 0)):
            continue
        following = next((r for r in ledger_rows[index + 1:] if r.get("event") == "logical_call"
                          and r.get("unit_id") == row.get("unit_id") and r.get("stage") == row.get("stage")), None)
        found.append({"target_seqs": [row["seq"]] + ([following["seq"]] if following else []),
                      "unit_id": row.get("unit_id"), "arm": row.get("arm"), "stage": row.get("stage"),
                      "diagnostic_archive_sequences": evidence, "model_output_produced": False})
    return found


def orphan_captures(ledger_rows: list[dict[str, Any]], diagnostic_dir: Path) -> list[int]:
    """Attempt captures not covered by ledger request rows and not already recorded."""
    attempts = [r for r in sorted(diagnostic_dir.glob("response_*.json"))
                if runtime.read_json(r).get("classification") in ("cli_result", "cli_timeout")]
    covered = sum(int(r.get("http_attempts", 0)) for r in ledger_rows if r.get("event") in ("request", "request_failed"))
    recorded = {s for r in ledger_rows if r.get("event") == "unclean_termination_recorded"
                for s in r.get("diagnostic_archive_sequences", [])}
    seqs = [runtime.read_json(p)["archive_sequence"] for p in attempts[covered:]]
    return [s for s in seqs if s not in recorded]


def _is_provider_stop(row: dict[str, Any], reclassified: set[int]) -> bool:
    return row.get("error") in PROVIDER_STOP_ERRORS or row.get("seq") in reclassified


def _provider_stop_aware_budgets() -> None:
    """Amendment 3: provider-refused calls (zero model output) are not arm calls.

    Frozen deviation 9 states a usage-limit stop charges nothing to an arm.  The inherited
    summariser nevertheless counted the refused *logical call* toward generator/evaluator
    call counts (and hence evaluator parity).  Refused logical calls are now excluded from
    call counts; their HTTP attempts remain in attempt accounting, and tokens are unaffected
    (refusals carry none).
    """
    base = getattr(e16.summarize_budget, "_e17c_original", e16.summarize_budget)

    def summarize_budget(rows, unit_id, arm):
        reclassified = {s for r in rows if r.get("event") == "provider_stop_reclassified" for s in r.get("target_seqs", [])}
        kept = [r for r in rows if not (r.get("event") == "logical_call" and _is_provider_stop(r, reclassified))]
        result = base(kept, unit_id, arm)
        result["provider_refused_logical_calls"] = sum(
            1 for r in rows if r.get("event") == "logical_call" and r.get("unit_id") == unit_id
            and r.get("arm") == arm and _is_provider_stop(r, reclassified))
        return result

    summarize_budget._e17c_original = base
    e16.summarize_budget = summarize_budget


def reconcile_provider_stopped_judge_attempts(ledger_path: Path) -> list[str]:
    """Apply amendment 2 retroactively from ledger evidence (e.g. a stop in a pre-amendment process).

    A STARTED judge attempt is withdrawn only if the unit's last judge logical call
    ended with a usage-limit/auth stop and no successful judge request lies between
    it and the previous judge logical call.  Without that evidence (e.g. a hard kill)
    the Experiment 17 rule (STARTED counts as consumed) is kept.
    """
    stops = {"SubscriptionUsageLimitReached", "ClaudeAuthUnavailable"}
    rows = runtime.read_jsonl(ledger_path)
    withdrawn = []
    for state_path in sorted(REAL_PATHS["checkpoints"].glob("*/judge_state.json")):
        state = runtime.read_json(state_path)
        unit_id = state.get("unit_id")
        if state.get("terminal"):
            continue
        calls = [i for i, r in enumerate(rows) if r.get("event") == "logical_call" and r.get("arm") == "JUDGE"
                 and r.get("unit_id") == unit_id]
        if not calls or rows[calls[-1]].get("error") not in stops:
            continue
        start = calls[-2] + 1 if len(calls) >= 2 else 0
        if any(r.get("event") == "request" and r.get("arm") == "JUDGE" and r.get("unit_id") == unit_id
               for r in rows[start:calls[-1]]):
            continue
        for batch in state.get("batches", []):
            attempts = batch.get("attempts", [])
            if attempts and attempts[-1].get("status") == "STARTED":
                item = attempts.pop()
                state.setdefault("provider_stops", []).append({
                    "batch": batch.get("batch"), "withdrawn_attempt": item.get("attempt"),
                    "reason": rows[calls[-1]]["error"], "model_output_produced": False,
                    "reconciled_from_ledger_seq": rows[calls[-1]].get("seq"),
                    "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
                runtime.atomic_write_json(state_path, state)
                withdrawn.append(unit_id)
                break
    return withdrawn


def _install_protocol_globals() -> None:
    runtime.install_experiment_17_core_hooks()
    _durable_arm_failures()
    _provider_stop_aware_budgets()
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


RUN_LOCK = WORK_DIR / "experiment_17c_run.lock"


def _pid_alive(pid: int) -> bool:
    import subprocess
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def _acquire_run_lock() -> None:
    """Exactly one Experiment 17-C scientific process at a time (any launcher)."""
    import os
    for _ in range(2):
        try:
            fd = os.open(RUN_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                holder = int(RUN_LOCK.read_text().strip() or 0)
            except ValueError:
                holder = 0
            if holder and _pid_alive(holder):
                print(f"Another Experiment 17-C run holds the lock (pid {holder}); refusing to start.", flush=True)
                raise SystemExit(73)
            RUN_LOCK.unlink(missing_ok=True)
    raise SystemExit("Could not acquire the Experiment 17-C run lock.")


def run_real(argv: list[str]) -> dict[str, Any]:
    if REAL_PATHS["report_json"].exists():
        raise SystemExit("Experiment 17-C final report already exists; refusing to re-run or overwrite results.")
    _acquire_run_lock()
    try:
        return _run_real(argv)
    finally:
        RUN_LOCK.unlink(missing_ok=True)


def _run_real(argv: list[str]) -> dict[str, Any]:
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
    for unit_id in reconcile_provider_stopped_judge_attempts(ledger_path):
        meter.event("judge_attempt_not_sent", unit_id=unit_id, reason="reconciled at resume from ledger evidence")
    for item in provider_stop_reclassifications(runtime.read_jsonl(ledger_path), REAL_PATHS["checkpoints"] / "diagnostic_responses"):
        meter.event("provider_stop_reclassified", reason="amendment 3: HTTP 429 session-limit refusal misclassified as RuntimeError", **item)
    orphans = orphan_captures(runtime.read_jsonl(ledger_path), REAL_PATHS["checkpoints"] / "diagnostic_responses")
    if orphans:
        meter.event("unclean_termination_recorded", diagnostic_archive_sequences=orphans,
                    note="CLI attempts captured without a ledger row: the previous process ended mid-call. "
                         "Any tokens those attempts consumed are absent from arm budgets.")

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
