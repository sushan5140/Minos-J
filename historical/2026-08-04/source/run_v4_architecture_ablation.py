"""Run Experiment 7 v4 and compare validated v2/v3/v4 results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
VENDOR_DIR = PROJECT_DIR / "work" / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from llm_client import OPENROUTER_MODEL, call_llm, get_retry_stats  # noqa: E402
from pipeline import run_v4_pipeline  # noqa: E402
from schema import (  # noqa: E402
    AUDIT_BOOLEAN_FIELDS,
    EXPERIMENT_7_NAME,
    validate_audits,
    validate_hypotheses,
    validate_v4_report,
)


OUTPUT_DIR = PROJECT_DIR / "outputs"
CHECKPOINT_ROOT = PROJECT_DIR / "work" / "experiment_7_checkpoints"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_7_v4_architecture_ablation_report.json"
REPORT_MARKDOWN = OUTPUT_DIR / "meno_j_experiment_7_v4_architecture_ablation_report.md"
REQUIRED_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
FALLBACK_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
FALLBACK_REASON = (
    "Primary model repeatedly returned HTTP 429 / remote connection reset during "
    "Q3 Stage 4.3."
)
QUESTIONS = {
    "Q1": "Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?",
    "Q2": "Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?",
    "Q3": "What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?",
}
V2_PATHS = {
    label: OUTPUT_DIR / f"meno_j_experiment_1_{label.lower()}.json" for label in QUESTIONS
}
V3_PATHS = {
    label: OUTPUT_DIR / f"meno_j_experiment_2_v3_{label.lower()}.json" for label in QUESTIONS
}
V4_STEMS = {
    label: f"meno_j_experiment_7_v4_{label.lower()}" for label in QUESTIONS
}
COMPARE_FIELDS = (
    "confounders_identified",
    "effect_size_plausible",
    "mechanism_is_non_generic",
    "data_requirements_clear",
    "prediction_is_testable",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required validated checkpoint is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON checkpoint: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Checkpoint must contain a JSON object: {path}")
    return payload


def _validate_prior(label: str, result: dict[str, Any], version: str) -> None:
    if result.get("research_question") != QUESTIONS[label]:
        raise ValueError(f"{version} {label} research question mismatch.")
    hypotheses = validate_hypotheses({"hypotheses": result.get("stage_4_hypotheses")})
    validate_audits({"audits": result.get("stage_5_audits")}, hypotheses)
    diagnostics = result.get("diagnostics", {})
    if diagnostics.get("generated_count") != 10:
        raise ValueError(f"{version} {label} generated_count must be 10.")
    if diagnostics.get("failure_points_consistency") is not True:
        raise ValueError(f"{version} {label} has inconsistent failure_points.")
    if version == "v3" and len(result.get("stage_4_5_confounder_enrichment", [])) != 10:
        raise ValueError(f"v3 {label} must contain 10 enrichment rows.")


def _summary_markdown(result: dict[str, Any]) -> str:
    diagnostics = result["diagnostics"]
    lines = [
        f"# {result['experiment_name']} — {result['research_question']}",
        "",
        f"- Version: `{result['version']}`",
        f"- Model: `{result['model']}`",
        f"- Generated: {diagnostics['generated_count']}",
        f"- PASS: {diagnostics['passed_count']}",
        f"- SALVAGEABLE: {diagnostics['salvageable_count']}",
        f"- REJECT: {diagnostics['rejected_count']}",
        f"- Pass survival rate: {diagnostics['pass_survival_rate']:.1%}",
        f"- Stage 6 rows: {len(result['stage_6_rival_prediction_matrix'])}",
        f"- Stage 7 rows: {len(result['stage_7_falsification_tests'])}",
        "",
        "## Builder diagnostics",
        "",
        f"- Mechanism builds: {diagnostics['mechanism_builder_count']}",
        f"- Confounder/rival builds: {diagnostics['confounder_rival_builder_count']}",
        f"- Statistical testability builds: {diagnostics['statistical_testability_builder_count']}",
        f"- Average mechanism variables: {diagnostics['avg_mechanism_variables_per_hypothesis']:.2f}",
        f"- Average confounders: {diagnostics['avg_confounders_per_hypothesis']:.2f}",
        f"- Average rivals: {diagnostics['avg_rivals_per_hypothesis']:.2f}",
        f"- Effect-size expectations: {diagnostics['hypotheses_with_effect_size_expectation']}",
        f"- Failure conditions: {diagnostics['hypotheses_with_failure_condition']}",
        f"- Testable predictions: {diagnostics['hypotheses_with_testable_prediction']}",
        "",
        "## Failed checklist fields",
        "",
    ]
    if "metadata" in result:
        lines[3:3] = [
            f"- Fallback model used: {result['metadata']['fallback_model_used']}",
            f"- Fallback reason: {result['metadata']['fallback_reason']}",
            f"- Stage 4.3 chunked: {result['metadata']['stage_4_3_chunked']}",
        ]
    failed = diagnostics["top_failed_checklist_fields"]
    lines.extend(
        [f"- `{field}`: {failed.get(field, 0)}" for field in COMPARE_FIELDS]
    )
    lines.extend(["", "## Red flags", ""])
    red_flags = diagnostics["rubber_stamp_red_flags"]
    lines.extend(f"- {flag}" for flag in red_flags) if red_flags else lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def _write_v4(label: str, result: dict[str, Any]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / f"{V4_STEMS[label]}.json"
    markdown_path = OUTPUT_DIR / f"{V4_STEMS[label]}_summary.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_summary_markdown(result), encoding="utf-8")
    return json_path, markdown_path


def _run_v4(label: str, v3_result: dict[str, Any]) -> dict[str, Any]:
    output_path = OUTPUT_DIR / f"{V4_STEMS[label]}.json"
    if output_path.exists():
        existing = _read_json(output_path)
        validate_v4_report(existing)
        if existing["research_question"] != QUESTIONS[label]:
            raise ValueError(f"Existing v4 {label} research question mismatch.")
        print(f"Using existing validated v4 {label}: {output_path}", flush=True)
        return existing
    stage_4_payload = (
        {"hypotheses": v3_result["stage_4_hypotheses"]} if label == "Q1" else None
    )
    print(f"Running/resuming v4 {label} from its latest valid checkpoint.", flush=True)
    result = run_v4_pipeline(
        call_llm,
        stage_4_payload=stage_4_payload,
        model=OPENROUTER_MODEL,
        research_question=QUESTIONS[label],
        checkpoint_dir=CHECKPOINT_ROOT / label.lower(),
    )
    if label == "Q3" and OPENROUTER_MODEL == FALLBACK_MODEL:
        checkpoint_dir = CHECKPOINT_ROOT / label.lower()
        result["metadata"] = {
            "fallback_model_used": True,
            "fallback_reason": FALLBACK_REASON,
            "primary_model": REQUIRED_MODEL,
            "stage_4_3_chunked": (
                (checkpoint_dir / "stage_4_3_batch_a.json").exists()
                or (checkpoint_dir / "stage_4_3_batch_b.json").exists()
            ),
            "retry_diagnostics": get_retry_stats(),
        }
        validate_v4_report(result)
    json_path, markdown_path = _write_v4(label, result)
    diagnostics = result["diagnostics"]
    print(
        f"v4 {label}: PASS={diagnostics['passed_count']}, "
        f"SALVAGEABLE={diagnostics['salvageable_count']}, "
        f"REJECT={diagnostics['rejected_count']}",
        flush=True,
    )
    print(f"v4 {label} JSON: {json_path}", flush=True)
    print(f"v4 {label} summary: {markdown_path}", flush=True)
    return result


def _version_metrics(result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = result["diagnostics"]
    failed = diagnostics["top_failed_checklist_fields"]
    return {
        "generated_count": diagnostics["generated_count"],
        "passed_count": diagnostics["passed_count"],
        "salvageable_count": diagnostics["salvageable_count"],
        "rejected_count": diagnostics["rejected_count"],
        "pass_survival_rate": diagnostics["pass_survival_rate"],
        "salvageable_rate": diagnostics["salvageable_rate"],
        "failed_checklist_fields": {
            field: failed.get(field, 0) for field in COMPARE_FIELDS
        },
        "stage_6_ran": bool(result["stage_6_rival_prediction_matrix"]),
        "stage_7_ran": bool(result["stage_7_falsification_tests"]),
        "red_flags": diagnostics["rubber_stamp_red_flags"],
    }


def _improvement(v3: dict[str, Any], v4: dict[str, Any]) -> dict[str, bool]:
    return {
        "pass_count_increased": v4["passed_count"] > v3["passed_count"],
        "confounders_identified_failures_decreased": (
            v4["failed_checklist_fields"]["confounders_identified"]
            < v3["failed_checklist_fields"]["confounders_identified"]
        ),
        "effect_size_plausible_failures_decreased": (
            v4["failed_checklist_fields"]["effect_size_plausible"]
            < v3["failed_checklist_fields"]["effect_size_plausible"]
        ),
        "mechanism_is_non_generic_failures_decreased": (
            v4["failed_checklist_fields"]["mechanism_is_non_generic"]
            < v3["failed_checklist_fields"]["mechanism_is_non_generic"]
        ),
        "data_requirements_clear_failures_decreased": (
            v4["failed_checklist_fields"]["data_requirements_clear"]
            < v3["failed_checklist_fields"]["data_requirements_clear"]
        ),
        "prediction_is_testable_failures_decreased": (
            v4["failed_checklist_fields"]["prediction_is_testable"]
            < v3["failed_checklist_fields"]["prediction_is_testable"]
        ),
        "stage_6_and_stage_7_ran": v4["stage_6_ran"] and v4["stage_7_ran"],
    }


def _build_report(
    v2_results: dict[str, dict[str, Any]],
    v3_results: dict[str, dict[str, Any]],
    v4_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for label in QUESTIONS:
        v2 = _version_metrics(v2_results[label])
        v3 = _version_metrics(v3_results[label])
        v4 = _version_metrics(v4_results[label])
        comparisons[label] = {
            "research_question": QUESTIONS[label],
            "v2_baseline": v2,
            "v3_enriched": v3,
            "v4_mechanism_confounder_testability": v4,
            "v4_vs_v3_improvement": _improvement(v3, v4),
        }
    criteria: dict[str, bool] = {}
    for field in (
        "pass_count_increased",
        "confounders_identified_failures_decreased",
        "effect_size_plausible_failures_decreased",
        "mechanism_is_non_generic_failures_decreased",
        "data_requirements_clear_failures_decreased",
        "prediction_is_testable_failures_decreased",
        "stage_6_and_stage_7_ran",
    ):
        criteria[field if field != "stage_6_and_stage_7_ran" else "stage_6_and_stage_7_ran_for_at_least_one_hypothesis"] = any(
            comparison["v4_vs_v3_improvement"][field]
            for comparison in comparisons.values()
        )
    return {
        "experiment_name": EXPERIMENT_7_NAME,
        "model": OPENROUTER_MODEL,
        "fallback_metadata": v4_results["Q3"].get("metadata", {}),
        "checkpoint_reuse": {
            "v2_outputs_reused": True,
            "v3_outputs_reused": True,
            "q1_valid_stage_4_checkpoint_reused": True,
            "q2_q3_stage_4_generated_and_checkpointed": True,
            "upstream_v2_v3_model_stages_rerun": False,
        },
        "execution_diagnostics": v4_results["Q3"].get("metadata", {}).get(
            "retry_diagnostics", get_retry_stats()
        ),
        "comparisons": comparisons,
        "overall_success_criteria": criteria,
    }


def _report_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['experiment_name']}",
        "",
        f"Model: `{report['model']}`",
        "",
        "| Question | Version | Generated | PASS | SALVAGEABLE | REJECT | Pass rate | Confounder failures | Effect-size failures | Generic failures | Data failures | Testability failures | Stage 6 | Stage 7 | Red flags |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|---|",
    ]
    versions = (
        ("v2_baseline", "v2"),
        ("v3_enriched", "v3"),
        ("v4_mechanism_confounder_testability", "v4"),
    )
    for label, comparison in report["comparisons"].items():
        for key, name in versions:
            row = comparison[key]
            failed = row["failed_checklist_fields"]
            lines.append(
                f"| {label} | {name} | {row['generated_count']} | {row['passed_count']} | "
                f"{row['salvageable_count']} | {row['rejected_count']} | {row['pass_survival_rate']:.1%} | "
                f"{failed['confounders_identified']} | {failed['effect_size_plausible']} | "
                f"{failed['mechanism_is_non_generic']} | {failed['data_requirements_clear']} | "
                f"{failed['prediction_is_testable']} | {'Yes' if row['stage_6_ran'] else 'No'} | "
                f"{'Yes' if row['stage_7_ran'] else 'No'} | "
                f"{', '.join(row['red_flags']) if row['red_flags'] else 'None'} |"
            )
    lines.extend(["", "## Per-question v4 improvement", ""])
    for label, comparison in report["comparisons"].items():
        lines.extend([f"### {label}", ""])
        lines.extend(
            f"- `{field}`: {'Yes' if value else 'No'}"
            for field, value in comparison["v4_vs_v3_improvement"].items()
        )
        lines.append("")
    lines.extend(["## Overall success criteria", ""])
    lines.extend(
        f"- `{field}`: {'Yes' if value else 'No'}"
        for field, value in report["overall_success_criteria"].items()
    )
    lines.extend(["", "## Timeout and retry diagnostics", ""])
    lines.extend(
        f"- `{field}`: {value}"
        for field, value in report["execution_diagnostics"].items()
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the latest schema-valid per-stage checkpoints.",
    )
    parser.add_argument(
        "--question",
        choices=("q1", "q2", "q3"),
        help="Run or resume only the selected v4 question.",
    )
    parser.add_argument(
        "--combine-only",
        action="store_true",
        help="Build the combined report from existing validated v4 outputs only.",
    )
    args = parser.parse_args()
    if OPENROUTER_MODEL not in {REQUIRED_MODEL, FALLBACK_MODEL}:
        raise RuntimeError(
            f"OPENROUTER_MODEL must be {REQUIRED_MODEL} or {FALLBACK_MODEL}."
        )
    if args.question == "q3" and OPENROUTER_MODEL != FALLBACK_MODEL:
        raise RuntimeError(f"Q3 fallback resume requires OPENROUTER_MODEL={FALLBACK_MODEL}.")
    if args.resume:
        print("Resume mode enabled; valid checkpoints will be reused.", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v2_results: dict[str, dict[str, Any]] = {}
    v3_results: dict[str, dict[str, Any]] = {}
    for label in QUESTIONS:
        v2_results[label] = _read_json(V2_PATHS[label])
        v3_results[label] = _read_json(V3_PATHS[label])
        _validate_prior(label, v2_results[label], "v2")
        _validate_prior(label, v3_results[label], "v3")
        print(f"Reusing validated v2/v3 {label} checkpoints.", flush=True)
    if args.combine_only:
        v4_results = {
            label: validate_v4_report(
                _read_json(OUTPUT_DIR / f"{V4_STEMS[label]}.json")
            )
            for label in QUESTIONS
        }
    elif args.question:
        label = args.question.upper()
        _run_v4(label, v3_results[label])
        print(f"Selected v4 {label} run completed.", flush=True)
        return
    else:
        v4_results = {
            label: _run_v4(label, v3_results[label]) for label in QUESTIONS
        }
    report = _build_report(v2_results, v3_results, v4_results)
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    REPORT_MARKDOWN.write_text(_report_markdown(report), encoding="utf-8")
    print(f"Ablation JSON: {REPORT_JSON}", flush=True)
    print(f"Ablation Markdown: {REPORT_MARKDOWN}", flush=True)


if __name__ == "__main__":
    main()
