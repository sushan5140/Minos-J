"""Run Meno-J Experiment 1 for Q2/Q3 and compare the three calibration runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_client import OPENROUTER_MODEL, call_llm
from pipeline import run_pipeline
from run_experiment import OUTPUT_DIR, write_result_files
from schema import DEFAULT_MODEL, RESEARCH_QUESTION


QUESTIONS = {
    "Q1": RESEARCH_QUESTION,
    "Q2": "Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?",
    "Q3": "What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?",
}

OUTPUT_STEMS = {
    "Q1": "meno_j_experiment_1_q1",
    "Q2": "meno_j_experiment_1_q2",
    "Q3": "meno_j_experiment_1_q3",
}

COMBINED_JSON = OUTPUT_DIR / "meno_j_experiment_1_combined_calibration_report.json"
COMBINED_MARKDOWN = OUTPUT_DIR / "meno_j_experiment_1_combined_calibration_report.md"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Existing result is invalid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Existing result must be a JSON object: {path}")
    return data


def _validate_loaded_run(label: str, result: dict[str, Any]) -> None:
    if result.get("research_question") != QUESTIONS[label]:
        raise ValueError(f"{label} output research question does not match the configured question.")
    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError(f"{label} output has no valid diagnostics object.")
    required = {
        "generated_count",
        "passed_count",
        "salvageable_count",
        "rejected_count",
        "pass_survival_rate",
        "salvageable_rate",
        "top_failed_checklist_fields",
        "rejection_reason_diversity",
        "failure_points_consistency",
        "rubber_stamp_red_flags",
    }
    missing = required - set(diagnostics)
    if missing:
        raise ValueError(f"{label} diagnostics missing fields: {sorted(missing)}")
    if diagnostics["generated_count"] != 10:
        raise ValueError(f"{label} generated_count must be 10.")
    decision_total = (
        diagnostics["passed_count"]
        + diagnostics["salvageable_count"]
        + diagnostics["rejected_count"]
    )
    if decision_total != diagnostics["generated_count"]:
        raise ValueError(f"{label} decision counts do not sum to generated_count.")
    if not diagnostics["failure_points_consistency"]:
        raise ValueError(f"{label} failure_points are inconsistent.")


def _run_one(label: str) -> dict[str, Any]:
    result = run_pipeline(
        call_llm,
        model=OPENROUTER_MODEL,
        research_question=QUESTIONS[label],
    )
    _validate_loaded_run(label, result)
    json_path, summary_path = write_result_files(result, OUTPUT_STEMS[label])
    diagnostics = result["diagnostics"]
    print(
        f"{label} completed: generated={diagnostics['generated_count']}, "
        f"pass={diagnostics['passed_count']}, "
        f"salvageable={diagnostics['salvageable_count']}, "
        f"reject={diagnostics['rejected_count']}"
    )
    print(f"{label} JSON output: {json_path}")
    print(f"{label} summary output: {summary_path}")
    return result


def _run_comparison(label: str, result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = result["diagnostics"]
    return {
        "research_question": result["research_question"],
        "model": result["model"],
        "generated_count": diagnostics["generated_count"],
        "passed_count": diagnostics["passed_count"],
        "salvageable_count": diagnostics["salvageable_count"],
        "rejected_count": diagnostics["rejected_count"],
        "pass_survival_rate": diagnostics["pass_survival_rate"],
        "salvageable_rate": diagnostics["salvageable_rate"],
        "top_failed_checklist_fields": diagnostics["top_failed_checklist_fields"],
        "rejection_reason_diversity": diagnostics["rejection_reason_diversity"],
        "failure_points_consistency": diagnostics["failure_points_consistency"],
        "rubber_stamp_red_flags": diagnostics["rubber_stamp_red_flags"],
        "stage_6_ran": bool(result["stage_6_rival_prediction_matrix"]),
        "stage_7_ran": bool(result["stage_7_falsification_tests"]),
    }


def _interpretation(runs: dict[str, dict[str, Any]]) -> list[str]:
    statements: list[str] = []
    if all(run["passed_count"] == 0 for run in runs.values()):
        statements.append(
            "All three runs have 0 PASS: the Auditor may be over-strict, or the Dreamer is not producing "
            "statistically complete mechanisms."
        )
    if all(
        run["top_failed_checklist_fields"].get("confounders_identified") == 10
        for run in runs.values()
    ):
        statements.append(
            "All three runs have confounders_identified failing 10/10: the Dreamer consistently fails "
            "to include rival explanations or confounder control."
        )
    if all(
        run["top_failed_checklist_fields"].get("effect_size_plausible") == 10
        for run in runs.values()
    ):
        statements.append(
            "All three runs have effect_size_plausible failing 10/10: the Dreamer consistently fails to "
            "justify whether mechanisms would be detectable in the dataset."
        )
    if len({run["pass_survival_rate"] for run in runs.values()}) > 1:
        statements.append(
            "Pass rates vary across Q1–Q3: the Auditor may be calibrated and sensitive to hypothesis quality."
        )
    if all(not run["stage_6_ran"] and not run["stage_7_ran"] for run in runs.values()):
        statements.append(
            "Stages 6 and 7 remain empty, as expected when no hypotheses PASS."
        )
    if not statements:
        statements.append(
            "The prescribed calibration conditions were not uniformly met; inspect the per-question "
            "diagnostics before changing the Auditor."
        )
    return statements


def build_combined_report(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    runs = {label: _run_comparison(label, results[label]) for label in QUESTIONS}
    common_failed_fields = set.intersection(
        *(set(run["top_failed_checklist_fields"]) for run in runs.values())
    )
    repeated = {
        field: {
            label: runs[label]["top_failed_checklist_fields"][field]
            for label in QUESTIONS
        }
        for field in sorted(common_failed_fields)
    }
    return {
        "experiment_name": "Meno-J Experiment 1: Auditor Calibration Test",
        "model": OPENROUTER_MODEL or DEFAULT_MODEL,
        "runs": runs,
        "repeated_failed_checklist_fields": repeated,
        "interpretation": _interpretation(runs),
    }


def build_combined_markdown(report: dict[str, Any]) -> str:
    runs = report["runs"]
    lines = [
        "# Meno-J Experiment 1: Combined Calibration Report",
        "",
        "## Model",
        "",
        f"`{report['model']}`",
        "",
        "## Run comparison",
        "",
        "| Run | Generated | PASS | SALVAGEABLE | REJECT | Pass rate | Salvageable rate | Reason diversity | Failure points consistent | Stage 6 ran | Stage 7 ran |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for label, run in runs.items():
        lines.append(
            f"| {label} | {run['generated_count']} | {run['passed_count']} | "
            f"{run['salvageable_count']} | {run['rejected_count']} | "
            f"{run['pass_survival_rate']:.1%} | {run['salvageable_rate']:.1%} | "
            f"{run['rejection_reason_diversity']} | "
            f"{'Yes' if run['failure_points_consistency'] else 'No'} | "
            f"{'Yes' if run['stage_6_ran'] else 'No'} | "
            f"{'Yes' if run['stage_7_ran'] else 'No'} |"
        )

    lines.extend(["", "## Questions", ""])
    for label, run in runs.items():
        lines.extend([f"### {label}", "", run["research_question"], ""])

    lines.extend(["## Top failed checklist fields", ""])
    for label, run in runs.items():
        lines.extend([f"### {label}", ""])
        failed = run["top_failed_checklist_fields"]
        if failed:
            lines.extend(f"- `{field}`: {count}" for field, count in failed.items())
        else:
            lines.append("None.")
        lines.append("")

    lines.extend(["## Repeated failed checklist fields across all questions", ""])
    repeated = report["repeated_failed_checklist_fields"]
    if repeated:
        for field, counts in repeated.items():
            formatted_counts = ", ".join(f"{label}={count}" for label, count in counts.items())
            lines.append(f"- `{field}`: {formatted_counts}")
    else:
        lines.append("None.")

    lines.extend(["", "## Rubber-stamp red flags", ""])
    for label, run in runs.items():
        flags = run["rubber_stamp_red_flags"]
        lines.append(f"- {label}: {', '.join(flags) if flags else 'None'}")

    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {statement}" for statement in report["interpretation"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    q1_path = OUTPUT_DIR / f"{OUTPUT_STEMS['Q1']}.json"
    if q1_path.exists():
        print(f"Using existing Q1 output: {q1_path}")
        q1 = _read_json(q1_path)
        _validate_loaded_run("Q1", q1)
    else:
        print("Q1 output is missing; running Q1 before Q2 and Q3.")
        q1 = _run_one("Q1")

    results = {
        "Q1": q1,
        "Q2": _run_one("Q2"),
        "Q3": _run_one("Q3"),
    }
    combined = build_combined_report(results)
    COMBINED_JSON.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    COMBINED_MARKDOWN.write_text(build_combined_markdown(combined), encoding="utf-8")
    print(f"Combined JSON output: {COMBINED_JSON}")
    print(f"Combined Markdown output: {COMBINED_MARKDOWN}")


if __name__ == "__main__":
    main()
