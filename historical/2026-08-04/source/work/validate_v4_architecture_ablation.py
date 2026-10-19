"""Validate all Experiment 7 v4 and ablation artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from schema import AUDIT_BOOLEAN_FIELDS, validate_v4_report  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
LABELS = ("q1", "q2", "q3")
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_7_v4_architecture_ablation_report.json"
REPORT_MARKDOWN = OUTPUT_DIR / "meno_j_experiment_7_v4_architecture_ablation_report.md"
COMPARE_FIELDS = {
    "confounders_identified",
    "effect_size_plausible",
    "mechanism_is_non_generic",
    "data_requirements_clear",
    "prediction_is_testable",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"Required output is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON output: {path}") from exc
    if not isinstance(payload, dict):
        raise AssertionError(f"Output is not a JSON object: {path}")
    return payload


def _credential_scan() -> list[str]:
    marker = "sk-" + "or-v1"
    matches: list[str] = []
    ignored_parts = {".git", "__pycache__", "vendor"}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".env"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if marker in text:
            matches.append(str(path.relative_to(PROJECT_DIR)))
    return matches


def main() -> None:
    v4_results: dict[str, dict[str, Any]] = {}
    for label in LABELS:
        json_path = OUTPUT_DIR / f"meno_j_experiment_7_v4_{label}.json"
        markdown_path = OUTPUT_DIR / f"meno_j_experiment_7_v4_{label}_summary.md"
        result = _read_json(json_path)
        validate_v4_report(result)
        if not markdown_path.exists() or not markdown_path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"Missing or empty v4 summary: {markdown_path}")
        hypotheses = result["stage_4_hypotheses"]
        known_ids = {item["hypothesis_id"] for item in hypotheses}
        assert len(hypotheses) == 10
        for field in (
            "stage_4_1_mechanism_builder",
            "stage_4_2_confounder_rival_builder",
            "stage_4_3_statistical_testability_builder",
            "stage_5_audits",
        ):
            assert len(result[field]) == 10
            assert {item["hypothesis_id"] for item in result[field]} == known_ids
        for audit in result["stage_5_audits"]:
            false_fields = {
                field for field in AUDIT_BOOLEAN_FIELDS if not audit[field]
            }
            assert false_fields == set(audit["failure_points"])
        pass_ids = {
            audit["hypothesis_id"]
            for audit in result["stage_5_audits"]
            if audit["audit_decision"] == "PASS"
        }
        assert {
            row["hypothesis_id"] for row in result["stage_6_rival_prediction_matrix"]
        } == pass_ids
        assert {
            row["hypothesis_id"] for row in result["stage_7_falsification_tests"]
        } == pass_ids
        v4_results[label.upper()] = result

    q3_metadata = v4_results["Q3"].get("metadata", {})
    assert q3_metadata.get("fallback_model_used") is True
    assert q3_metadata.get("fallback_reason") == (
        "Primary model repeatedly returned HTTP 429 / remote connection reset during "
        "Q3 Stage 4.3."
    )

    report = _read_json(REPORT_JSON)
    if not REPORT_MARKDOWN.exists() or not REPORT_MARKDOWN.read_text(encoding="utf-8").strip():
        raise AssertionError("Combined ablation Markdown is missing or empty.")
    assert set(report["comparisons"]) == {"Q1", "Q2", "Q3"}
    assert report["fallback_metadata"] == q3_metadata
    retry_diagnostics = report["execution_diagnostics"]
    assert set(retry_diagnostics) == {
        "logical_stage_calls",
        "http_attempts",
        "timeout_retries",
        "network_retries",
        "transient_http_retries",
        "invalid_response_json_retries",
        "invalid_response_shape_retries",
        "invalid_json_repair_attempts",
    }
    assert all(isinstance(value, int) and value >= 0 for value in retry_diagnostics.values())
    for label, comparison in report["comparisons"].items():
        assert comparison["research_question"] == v4_results[label]["research_question"]
        for version in (
            "v2_baseline",
            "v3_enriched",
            "v4_mechanism_confounder_testability",
        ):
            metrics = comparison[version]
            assert metrics["generated_count"] == 10
            assert set(metrics["failed_checklist_fields"]) == COMPARE_FIELDS
        assert comparison["v4_vs_v3_improvement"]
    assert report["overall_success_criteria"]
    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential pattern found in: {credential_matches}"
    print("Experiment 7 v4 architecture ablation validation passed.")


if __name__ == "__main__":
    main()
