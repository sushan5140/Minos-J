"""Run Experiment 2 v3 and compare it with the existing v2 calibration runs."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from llm_client import OPENROUTER_MODEL, call_llm
from pipeline import run_enriched_pipeline, run_pipeline
from run_calibration_suite import QUESTIONS
from run_experiment import OUTPUT_DIR, write_result_files
from schema import EXPERIMENT_2_NAME


V2_STEMS = {label: f"meno_j_experiment_1_{label.lower()}" for label in QUESTIONS}
V3_STEMS = {label: f"meno_j_experiment_2_v3_{label.lower()}" for label in QUESTIONS}
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_2_enrichment_ablation_report.json"
REPORT_MARKDOWN = OUTPUT_DIR / "meno_j_experiment_2_enrichment_ablation_report.md"
CHECKPOINT_ROOT = Path(__file__).resolve().parent / "work" / "experiment_2_checkpoints"

COMPARE_FIELDS = (
    "confounders_identified",
    "effect_size_plausible",
    "mechanism_is_non_generic",
    "data_requirements_clear",
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON output: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def _validate_run(label: str, result: dict[str, Any], *, enriched: bool) -> None:
    if result.get("research_question") != QUESTIONS[label]:
        raise ValueError(f"{label} research question mismatch.")
    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, dict) or diagnostics.get("generated_count") != 10:
        raise ValueError(f"{label} must contain diagnostics for exactly 10 hypotheses.")
    if len(result.get("stage_4_hypotheses", [])) != 10:
        raise ValueError(f"{label} does not contain exactly 10 Stage 4 hypotheses.")
    if len(result.get("stage_5_audits", [])) != 10:
        raise ValueError(f"{label} does not contain exactly 10 Stage 5 audits.")
    if not diagnostics.get("failure_points_consistency"):
        raise ValueError(f"{label} has inconsistent failure_points.")
    if enriched:
        if result.get("version") != "v3_enriched":
            raise ValueError(f"{label} is not marked v3_enriched.")
        if len(result.get("stage_4_5_confounder_enrichment", [])) != 10:
            raise ValueError(f"{label} does not contain exactly 10 enrichments.")
        if diagnostics.get("enriched_count") != 10:
            raise ValueError(f"{label} enriched_count must be 10.")


def _run_v2_if_missing(label: str) -> dict[str, Any]:
    path = OUTPUT_DIR / f"{V2_STEMS[label]}.json"
    if path.exists():
        result = _read_json(path)
        _validate_run(label, result, enriched=False)
        print(f"Using existing v2 {label}: {path}", flush=True)
        return result
    print(f"v2 {label} is missing; running the baseline.", flush=True)
    result = run_pipeline(
        call_llm,
        model=OPENROUTER_MODEL,
        research_question=QUESTIONS[label],
    )
    _validate_run(label, result, enriched=False)
    write_result_files(result, V2_STEMS[label])
    return result


def _run_v3(label: str) -> dict[str, Any]:
    existing_path = OUTPUT_DIR / f"{V3_STEMS[label]}.json"
    if existing_path.exists():
        result = _read_json(existing_path)
        _validate_run(label, result, enriched=True)
        print(f"Using existing v3 {label}: {existing_path}", flush=True)
        return result
    print(f"Running v3 {label}.", flush=True)
    result = run_enriched_pipeline(
        call_llm,
        model=OPENROUTER_MODEL,
        research_question=QUESTIONS[label],
        checkpoint_dir=CHECKPOINT_ROOT / label.lower(),
    )
    _validate_run(label, result, enriched=True)
    json_path, summary_path = write_result_files(result, V3_STEMS[label])
    diagnostics = result["diagnostics"]
    print(
        f"v3 {label} completed: generated={diagnostics['generated_count']}, "
        f"pass={diagnostics['passed_count']}, "
        f"salvageable={diagnostics['salvageable_count']}, "
        f"reject={diagnostics['rejected_count']}",
        flush=True,
    )
    print(f"v3 {label} JSON: {json_path}", flush=True)
    print(f"v3 {label} summary: {summary_path}", flush=True)
    return result


def _average_nonpass_reason_words(result: dict[str, Any]) -> float:
    counts = [
        len(audit["decision_reason"].split())
        for audit in result["stage_5_audits"]
        if audit["audit_decision"] in {"SALVAGEABLE", "REJECT"}
    ]
    return mean(counts) if counts else 0.0


def _version_metrics(result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = result["diagnostics"]
    failed = diagnostics["top_failed_checklist_fields"]
    metrics = {
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
        "avg_nonpass_decision_reason_words": _average_nonpass_reason_words(result),
    }
    for field in (
        "enriched_count",
        "avg_confounders_per_hypothesis",
        "avg_control_variables_per_hypothesis",
        "avg_rival_explanations_per_hypothesis",
        "hypotheses_with_effect_size_expectation",
    ):
        if field in diagnostics:
            metrics[field] = diagnostics[field]
    return metrics


def build_report(
    v2_results: dict[str, dict[str, Any]],
    v3_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for label in QUESTIONS:
        v2 = _version_metrics(v2_results[label])
        v3 = _version_metrics(v3_results[label])
        comparisons[label] = {
            "research_question": QUESTIONS[label],
            "v2_baseline": v2,
            "v3_enriched": v3,
            "improvement": {
                "confounders_identified_failures_decreased": (
                    v3["failed_checklist_fields"]["confounders_identified"]
                    < v2["failed_checklist_fields"]["confounders_identified"]
                ),
                "effect_size_plausible_failures_decreased": (
                    v3["failed_checklist_fields"]["effect_size_plausible"]
                    < v2["failed_checklist_fields"]["effect_size_plausible"]
                ),
                "pass_count_increased": v3["passed_count"] > v2["passed_count"],
                "stage_6_and_stage_7_ran": v3["stage_6_ran"] and v3["stage_7_ran"],
                "nonpass_reasons_became_more_specific": (
                    v3["avg_nonpass_decision_reason_words"]
                    > v2["avg_nonpass_decision_reason_words"]
                ),
            },
        }

    total_v2_confounders = sum(
        item["v2_baseline"]["failed_checklist_fields"]["confounders_identified"]
        for item in comparisons.values()
    )
    total_v3_confounders = sum(
        item["v3_enriched"]["failed_checklist_fields"]["confounders_identified"]
        for item in comparisons.values()
    )
    total_v2_effect_size = sum(
        item["v2_baseline"]["failed_checklist_fields"]["effect_size_plausible"]
        for item in comparisons.values()
    )
    total_v3_effect_size = sum(
        item["v3_enriched"]["failed_checklist_fields"]["effect_size_plausible"]
        for item in comparisons.values()
    )
    return {
        "experiment_name": EXPERIMENT_2_NAME,
        "model": OPENROUTER_MODEL,
        "comparisons": comparisons,
        "overall_success_criteria": {
            "confounders_identified_failures_decreased": (
                total_v3_confounders < total_v2_confounders
            ),
            "effect_size_plausible_failures_decreased": (
                total_v3_effect_size < total_v2_effect_size
            ),
            "pass_count_increased": (
                sum(item["v3_enriched"]["passed_count"] for item in comparisons.values())
                > sum(item["v2_baseline"]["passed_count"] for item in comparisons.values())
            ),
            "stage_6_and_stage_7_ran_for_at_least_one_hypothesis": any(
                item["v3_enriched"]["stage_6_ran"]
                and item["v3_enriched"]["stage_7_ran"]
                for item in comparisons.values()
            ),
            "nonpass_reasons_became_more_specific": (
                mean(
                    item["v3_enriched"]["avg_nonpass_decision_reason_words"]
                    for item in comparisons.values()
                )
                > mean(
                    item["v2_baseline"]["avg_nonpass_decision_reason_words"]
                    for item in comparisons.values()
                )
            ),
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Experiment 2: Confounder Enrichment Ablation",
        "",
        "## Model",
        "",
        f"`{report['model']}`",
        "",
        "## v2 baseline vs v3 enriched",
        "",
        "| Question | Version | Generated | PASS | SALVAGEABLE | REJECT | Pass rate | Salvageable rate | Confounder failures | Effect-size failures | Non-generic failures | Data-requirement failures | Stage 6 | Stage 7 | Red flags |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|---|",
    ]
    for label, comparison in report["comparisons"].items():
        for version_key, version_name in (
            ("v2_baseline", "v2 baseline"),
            ("v3_enriched", "v3 enriched"),
        ):
            item = comparison[version_key]
            failed = item["failed_checklist_fields"]
            lines.append(
                f"| {label} | {version_name} | {item['generated_count']} | "
                f"{item['passed_count']} | {item['salvageable_count']} | "
                f"{item['rejected_count']} | {item['pass_survival_rate']:.1%} | "
                f"{item['salvageable_rate']:.1%} | {failed['confounders_identified']} | "
                f"{failed['effect_size_plausible']} | {failed['mechanism_is_non_generic']} | "
                f"{failed['data_requirements_clear']} | "
                f"{'Yes' if item['stage_6_ran'] else 'No'} | "
                f"{'Yes' if item['stage_7_ran'] else 'No'} | "
                f"{', '.join(item['red_flags']) if item['red_flags'] else 'None'} |"
            )

    lines.extend(["", "## Per-question improvement", ""])
    for label, comparison in report["comparisons"].items():
        lines.append(f"### {label}")
        lines.append("")
        for criterion, succeeded in comparison["improvement"].items():
            lines.append(f"- `{criterion}`: {'Yes' if succeeded else 'No'}")
        lines.append("")

    lines.extend(["## Overall success criteria", ""])
    for criterion, succeeded in report["overall_success_criteria"].items():
        lines.append(f"- `{criterion}`: {'Yes' if succeeded else 'No'}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v2_results = {label: _run_v2_if_missing(label) for label in QUESTIONS}
    v3_results = {label: _run_v3(label) for label in QUESTIONS}
    report = build_report(v2_results, v3_results)
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT_MARKDOWN.write_text(build_markdown(report), encoding="utf-8")
    print(f"Ablation JSON report: {REPORT_JSON}", flush=True)
    print(f"Ablation Markdown report: {REPORT_MARKDOWN}", flush=True)


if __name__ == "__main__":
    main()
