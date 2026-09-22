"""Minimal live compatibility probe for the frozen Experiment 17 models.

This is not an experimental unit and produces no scientific outcome.  It makes
one small structured-output call to the generator and, only if that passes,
one small blinded-judge call.  Results and diagnostics are isolated from the
Experiment 17 scientific checkpoints and budgets.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import experiment_17_runtime as runtime
import prompts
import run_experiment_16_matched_compute as e16
import run_experiment_17_matched_compute as e17
import schema


WORK_DIR = PROJECT_DIR / "work" / "experiment_17_live_compatibility"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "harness_validation" / "experiment_17"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_17_live_compatibility.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_17_live_compatibility.md"
BANNER = "LIVE COMPATIBILITY TEST ONLY — not a scientific Experiment 17 result."


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_cases() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    hypotheses = []
    false_fields = {
        "H1": [],
        "H2": ["confounders_identified"],
        "H3": ["mechanism_is_non_generic", "prediction_is_testable"],
        "H4": ["variables_measurable", "causal_chain_valid", "data_requirements_clear"],
        "H5": [],
        "H6": ["causal_chain_valid"],
        "H7": ["confounders_identified", "data_requirements_clear"],
        "H8": ["variables_measurable", "mechanism_is_non_generic", "prediction_is_testable"],
        "H9": [],
        "H10": ["causal_chain_valid", "confounders_identified", "data_requirements_clear"],
    }
    expected = {}
    for index in range(1, 11):
        hypothesis_id = f"H{index}"
        hypotheses.append({
            "hypothesis_id": hypothesis_id,
            "hypothesis": f"Synthetic compatibility case {index}",
            "proposed_mechanism": "Synthetic directed path X -> M -> Y.",
            "core_assumption": "The listed checklist profile is authoritative for this compatibility probe.",
            "knowledge_gap_addressed": "Structured decision-rule compatibility only.",
            "status": "SPECULATIVE",
        })
        failed = false_fields[hypothesis_id]
        critical_failures = sum(field in schema.CRITICAL_AUDIT_FIELDS for field in failed)
        decision = "PASS" if critical_failures == 0 else "SALVAGEABLE" if critical_failures <= 2 else "REJECT"
        expected[hypothesis_id] = {
            "false_fields": failed,
            "audit_decision": decision,
        }
    return hypotheses, expected


def generator_probe_prompt() -> tuple[str, dict[str, dict[str, Any]]]:
    hypotheses, expected = probe_cases()
    prompt = prompts.auditor_prompt(
        "Synthetic contract-compatibility probe; not a research question.",
        hypotheses,
        input_description="Synthetic checklist cases",
    )
    matrix = [
        {
            "hypothesis_id": hypothesis_id,
            "false_checklist_fields": values["false_fields"],
            "required_decision": values["audit_decision"],
        }
        for hypothesis_id, values in expected.items()
    ]
    prompt += (
        "\n\nLIVE COMPATIBILITY OVERRIDE:\n"
        "This is a deterministic contract test, not scientific evaluation. Do not reassess the synthetic "
        "hypotheses. For each ID, set exactly the listed checklist fields false and every other checklist "
        "field true. Set failure_points to every and only the false fields. Copy required_decision exactly. "
        "Use a non-empty decision_reason for every row and a non-empty concrete salvage_note for every "
        "SALVAGEABLE row. Preserve H1-H10 order.\n"
        f"Contract matrix:\n{json.dumps(matrix, ensure_ascii=False, indent=2)}\n"
        "Return only the JSON object required by the Stage 5 schema above."
    )
    return prompt, expected


def validate_generator_probe(payload: dict[str, Any], expected: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    hypotheses, _ = probe_cases()
    audits = schema.validate_audits(payload, hypotheses)
    for audit in audits:
        hypothesis_id = audit["hypothesis_id"]
        requirement = expected[hypothesis_id]
        actual_false = {field for field in schema.AUDIT_BOOLEAN_FIELDS if not audit[field]}
        if actual_false != set(requirement["false_fields"]):
            raise schema.PipelineValidationError(
                f"Generator decision probe {hypothesis_id} false fields {sorted(actual_false)} "
                f"did not match required {sorted(requirement['false_fields'])}."
            )
        if audit["audit_decision"] != requirement["audit_decision"]:
            raise schema.PipelineValidationError(
                f"Generator decision probe {hypothesis_id} returned {audit['audit_decision']}; "
                f"required {requirement['audit_decision']}."
            )
        if audit["audit_decision"] == "SALVAGEABLE" and not audit["salvage_note"].strip():
            raise schema.PipelineValidationError(
                f"Generator decision probe {hypothesis_id} omitted its required salvage note."
            )
    return audits


def judge_card() -> dict[str, Any]:
    return {
        "card_id": "C17a0b1c2",
        "hypothesis": "Increasing synthetic exposure X causes measurable outcome Y through mediator M.",
        "proposed_mechanism": "X increases M, and M increases Y under boundary condition B.",
        "causal_path": "X -> M -> Y",
        "mechanism_variables": ["X", "M", "Y"],
        "possible_confounders": ["C"],
        "control_variables": ["C"],
        "rival_explanation": "C independently changes both X and Y.",
        "rival_prediction": "The X-Y association vanishes after conditioning on C.",
        "distinguishing_test": "Estimate the controlled direct and mediated effects with C adjustment.",
        "effect_size_expectation": "medium",
        "effect_size_rationale": "The synthetic probe stipulates a detectable standardized effect near 0.5.",
        "minimum_data_needed": ["X, M, Y, C measured in at least 100 independent cases"],
        "testable_prediction": "Y rises as X rises, with a positive indirect effect through M.",
        "failure_condition": "No positive indirect effect through M within a prespecified confidence interval.",
        "statistical_test_plan": "Fit a preregistered mediation model with C adjustment.",
        "falsification_test": "Intervene on X while holding C fixed and test whether M and Y fail to increase.",
    }


def scan_for_credentials(paths: list[Path], api_key: str) -> None:
    credential_pattern = re.compile(r"sk-or-v1-[A-Za-z0-9_-]{40,}")
    hits = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if api_key in text or credential_pattern.search(text):
            hits.append(str(path))
    if hits:
        raise RuntimeError(f"Credential material appeared in compatibility artifacts: {hits}")


def current_artifact_paths() -> list[Path]:
    paths = []
    if WORK_DIR.exists():
        paths.extend(path for path in WORK_DIR.rglob("*") if path.is_file())
    for path in (REPORT_JSON, REPORT_MD):
        if path.exists():
            paths.append(path)
    return paths


def report_markdown(report: dict[str, Any]) -> str:
    generator = report["generator"]
    judge = report["judge"]
    token_usage = report["token_usage"]
    return "\n".join([
        "# Meno-J Experiment 17 — Live Compatibility Test",
        "",
        f"> **{BANNER}**",
        "",
        f"- Overall status: **{report['overall_status']}**",
        f"- Generator: `{generator['model']}` — {generator['status']}",
        f"- Judge: `{judge['model']}` — {judge['status']}",
        f"- Logical calls: {report['logical_calls']}",
        f"- HTTP attempts: {report['http_attempts']}",
        f"- Prompt tokens: {token_usage['prompt_tokens']}",
        f"- Completion tokens: {token_usage['completion_tokens']}",
        f"- Total tokens: {token_usage['total_tokens']}",
        f"- Provider usage reported for every successful response: {report['usage_reported_for_all_successes']}",
        f"- Rate-limit retries: {report['rate_limit_retries']}",
        f"- Response bodies captured safely: {report['response_bodies_captured_safely']}",
        f"- Credential scan passed: {report['credential_scan_passed']}",
        f"- Frozen protocol unchanged: {report['protocol_unchanged']}",
        f"- Ready for full execution: {report['ready_for_full_execution']}",
        "",
        "## Generator contract probe",
        "",
        f"- Valid Stage 5 JSON: {generator.get('valid_stage_json')}",
        f"- Decision rules followed exactly: {generator.get('decision_rules_followed')}",
        f"- Decision counts: {generator.get('decision_counts')}",
        f"- Error: {generator.get('error') or 'none'}",
        "",
        "## Blinded-judge probe",
        "",
        f"- Schema-conforming judgment: {judge.get('schema_conforming')}",
        f"- Returned card IDs: {judge.get('card_ids')}",
        f"- Error: {judge.get('error') or 'none'}",
        "",
        "## Diagnostics",
        "",
        f"- Ledger: `{report['paths']['ledger']}`",
        f"- Response archive: `{report['paths']['diagnostic_archive']}`",
        "",
    ])


def main() -> None:
    e17.require_protocol()
    protocol_hash_before = sha256_file(e17.PROTOCOL_JSON)
    e17.preflight(refresh_metadata=True)
    api_key = os.environ["OPENROUTER_API_KEY"]
    generator_model = os.environ["OPENROUTER_MODEL"]
    judge_model = os.environ["MINOS_J_JUDGE_MODEL"]
    diagnostics_dir = WORK_DIR / "diagnostic_responses"
    ledger_path = WORK_DIR / "request_ledger.jsonl"
    archive_before = len(list(diagnostics_dir.glob("response_*.json"))) if diagnostics_dir.exists() else 0
    ledger_before = len(runtime.read_jsonl(ledger_path))
    client = runtime.StructuredOpenRouterClient(api_key, generator_model, diagnostics_dir)
    meter = runtime.ResumeSafeMeter(client, ledger_path)
    generator_result = {
        "model": generator_model,
        "status": "NOT_RUN",
        "valid_stage_json": False,
        "decision_rules_followed": False,
        "decision_counts": {},
        "error": None,
    }
    judge_result = {
        "model": judge_model,
        "status": "NOT_RUN",
        "schema_conforming": False,
        "card_ids": [],
        "error": None,
    }
    failure: Exception | None = None
    try:
        generator_prompt, expected = generator_probe_prompt()
        try:
            payload = e16.make_caller(client, meter, "compatibility_stage_5", "evaluator")(generator_prompt)
            audits = validate_generator_probe(payload, expected)
            generator_result.update({
                "status": "PASS",
                "valid_stage_json": True,
                "decision_rules_followed": True,
                "decision_counts": dict(Counter(row["audit_decision"] for row in audits)),
            })
        except Exception as exc:
            generator_result.update({"status": "FAIL", "error": f"{type(exc).__name__}: {str(exc)[:1000]}"})
            failure = exc

        if failure is None:
            try:
                card = judge_card()
                prompt = e16.judge_prompt("Synthetic compatibility probe; not a research question.", [card], schema)
                with e16.use_model(client, judge_model):
                    payload = e16.make_caller(client, meter, "compatibility_blinded_judge", "judge")(prompt)
                judgments = e16.validate_judgments(payload, [card["card_id"]], schema)
                judge_result.update({
                    "status": "PASS",
                    "schema_conforming": True,
                    "card_ids": [row["card_id"] for row in judgments],
                })
            except Exception as exc:
                judge_result.update({"status": "FAIL", "error": f"{type(exc).__name__}: {str(exc)[:1000]}"})
                failure = exc
    finally:
        meter.uninstall()

    new_rows = runtime.read_jsonl(ledger_path)[ledger_before:]
    request_rows = [row for row in new_rows if row.get("event") == "request"]
    failed_rows = [row for row in new_rows if row.get("event") == "request_failed"]
    logical_rows = [row for row in new_rows if row.get("event") == "logical_call"]
    new_archives = sorted(diagnostics_dir.glob("response_*.json"))[archive_before:]
    successful_http_attempts = sum(row.get("http_attempts", 0) for row in request_rows)
    failed_http_attempts = sum(row.get("http_attempts", 0) for row in failed_rows)
    total_http_attempts = successful_http_attempts + failed_http_attempts
    token_usage = {
        "prompt_tokens": sum(row.get("prompt_tokens", 0) for row in request_rows),
        "completion_tokens": sum(row.get("completion_tokens", 0) for row in request_rows),
        "total_tokens": sum(row.get("total_tokens", 0) for row in request_rows),
    }
    usage_reported = bool(request_rows) and all(row.get("usage_reported") for row in request_rows)
    response_envelopes = []
    for path in new_archives:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("classification") == "response_envelope":
            response_envelopes.append(record)
    bodies_captured = len(response_envelopes) >= len(request_rows)
    protocol_hash_after = sha256_file(e17.PROTOCOL_JSON)
    rate_limit_retries = sum(row.get("transient_http_retries", 0) for row in request_rows + failed_rows)
    report = {
        "artifact": "Meno-J Experiment 17 live compatibility test",
        "banner": BANNER,
        "scientific_results": False,
        "overall_status": "PASS" if failure is None else "FAIL",
        "generator": generator_result,
        "judge": judge_result,
        "logical_calls": len(logical_rows),
        "successful_requests": len(request_rows),
        "failed_requests": len(failed_rows),
        "http_attempts": total_http_attempts,
        "token_usage": token_usage,
        "usage_reported_for_all_successes": usage_reported,
        "rate_limit_retries": rate_limit_retries,
        "retry_counters": {
            key: sum(row.get(key, 0) for row in request_rows + failed_rows)
            for key in (
                "timeout_retries",
                "network_retries",
                "incomplete_read_retries",
                "transient_http_retries",
                "invalid_response_json_retries",
                "invalid_response_shape_retries",
            )
        },
        "response_bodies_captured_safely": bodies_captured,
        "credential_scan_passed": False,
        "protocol_sha256_before": protocol_hash_before,
        "protocol_sha256_after": protocol_hash_after,
        "protocol_unchanged": protocol_hash_before == protocol_hash_after,
        "ready_for_full_execution": bool(
            failure is None and usage_reported and bodies_captured and protocol_hash_before == protocol_hash_after
        ),
        "paths": {
            "ledger": str(ledger_path.relative_to(PROJECT_DIR)),
            "diagnostic_archive": str(diagnostics_dir.relative_to(PROJECT_DIR)),
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    runtime.atomic_write_json(REPORT_JSON, report)
    REPORT_MD.write_text(report_markdown(report), encoding="utf-8")
    scan_for_credentials(current_artifact_paths(), api_key)
    report["credential_scan_passed"] = True
    report["ready_for_full_execution"] = bool(report["ready_for_full_execution"] and report["credential_scan_passed"])
    runtime.atomic_write_json(REPORT_JSON, report)
    REPORT_MD.write_text(report_markdown(report), encoding="utf-8")
    scan_for_credentials(current_artifact_paths(), api_key)
    print(f"Generator compatibility: {generator_result['status']}")
    print(f"Judge compatibility: {judge_result['status']}")
    print(f"Logical calls: {len(logical_rows)}; HTTP attempts: {total_http_attempts}")
    print(f"Tokens: prompt={token_usage['prompt_tokens']} completion={token_usage['completion_tokens']} total={token_usage['total_tokens']}")
    print(f"Rate-limit retries: {rate_limit_retries}")
    print(f"Ready for full execution: {report['ready_for_full_execution']}")
    print(f"Report: {REPORT_MD}")
    if failure is not None or not report["ready_for_full_execution"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
