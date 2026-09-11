"""Legacy Experiment 1 calibration entry point for the Meno-J engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_client import OPENROUTER_MODEL, call_llm
from pipeline import run_pipeline


OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_1_q1.json"
SUMMARY_OUTPUT = OUTPUT_DIR / "meno_j_experiment_1_q1_summary.md"


def _format_hypothesis_section(
    title: str,
    decision: str,
    hypotheses: list[dict[str, Any]],
    audits_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [f"## {title}", ""]
    selected = [
        hypothesis
        for hypothesis in hypotheses
        if audits_by_id[hypothesis["hypothesis_id"]]["audit_decision"] == decision
    ]
    if not selected:
        lines.extend(["None.", ""])
        return lines
    for hypothesis in selected:
        audit = audits_by_id[hypothesis["hypothesis_id"]]
        lines.extend(
            [
                f"### {hypothesis['hypothesis_id']}: {hypothesis['hypothesis']}",
                "",
                f"- Mechanism: {hypothesis['proposed_mechanism']}",
                f"- Audit reason: {audit['decision_reason']}",
            ]
        )
        if audit["failure_points"]:
            lines.append(f"- Failed checks: {', '.join(audit['failure_points'])}")
        if decision == "SALVAGEABLE" and audit["salvage_note"].strip():
            lines.append(f"- Salvage note: {audit['salvage_note']}")
        lines.append("")
    return lines


def build_summary(result: dict[str, Any]) -> str:
    diagnostics = result["diagnostics"]
    hypotheses = result["stage_4_hypotheses"]
    audits_by_id = {
        audit["hypothesis_id"]: audit for audit in result["stage_5_audits"]
    }
    failed = diagnostics["top_failed_checklist_fields"]
    red_flags = diagnostics["rubber_stamp_red_flags"]

    lines = [
        f"# {result['experiment_name']}",
        "",
        "## Research question",
        "",
        result["research_question"],
        "",
        "## Model used",
        "",
        f"`{result['model']}`",
        "",
        "## Counts and rates",
        "",
        f"- Generated: {diagnostics['generated_count']}",
        f"- PASS: {diagnostics['passed_count']}",
        f"- SALVAGEABLE: {diagnostics['salvageable_count']}",
        f"- REJECT: {diagnostics['rejected_count']}",
        f"- Pass survival rate: {diagnostics['pass_survival_rate']:.1%}",
        f"- Salvageable rate: {diagnostics['salvageable_rate']:.1%}",
        "",
        "## Top failed checklist fields",
        "",
    ]
    if "version" in result:
        lines[2:2] = ["## Version", "", f"`{result['version']}`", ""]
    if failed:
        lines.extend(f"- `{field}`: {count}" for field, count in failed.items())
    else:
        lines.append("None.")
    lines.extend(["", "## Red flags", ""])
    if red_flags:
        lines.extend(f"- {flag}" for flag in red_flags)
    else:
        lines.append("None.")
    lines.append("")

    if "enriched_count" in diagnostics:
        lines.extend(
            [
                "## Confounder enrichment diagnostics",
                "",
                f"- Enriched hypotheses: {diagnostics['enriched_count']}",
                f"- Average confounders per hypothesis: {diagnostics['avg_confounders_per_hypothesis']:.2f}",
                f"- Average control variables per hypothesis: {diagnostics['avg_control_variables_per_hypothesis']:.2f}",
                f"- Average rival explanations per hypothesis: {diagnostics['avg_rival_explanations_per_hypothesis']:.2f}",
                f"- Hypotheses with effect-size expectation: {diagnostics['hypotheses_with_effect_size_expectation']}",
                "",
            ]
        )

    lines.extend(_format_hypothesis_section("PASS hypotheses", "PASS", hypotheses, audits_by_id))
    lines.extend(
        _format_hypothesis_section(
            "SALVAGEABLE hypotheses", "SALVAGEABLE", hypotheses, audits_by_id
        )
    )
    lines.extend(_format_hypothesis_section("REJECT hypotheses", "REJECT", hypotheses, audits_by_id))

    if diagnostics["passed_count"] == diagnostics["generated_count"]:
        interpretation = (
            "The auditor did not filter any Dreamer output, so this run shows a likely calibration or "
            "rubber-stamping problem."
        )
    elif diagnostics["passed_count"] == 0:
        interpretation = (
            "The auditor filtered every speculative hypothesis. The failure patterns should be reviewed "
            "to distinguish appropriate strictness from over-rejection."
        )
    else:
        interpretation = (
            "The auditor filtered the candidate set while retaining a smaller group for rival-prediction "
            "and falsification analysis. The red flags above indicate whether that selectivity appears "
            "meaningfully discriminating."
        )
    lines.extend(["## Short interpretation", "", interpretation, ""])
    return "\n".join(lines)


def write_result_files(result: dict[str, Any], output_stem: str) -> tuple[Path, Path]:
    """Write one validated experiment result and summary as explicit UTF-8."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_output = OUTPUT_DIR / f"{output_stem}.json"
    summary_output = OUTPUT_DIR / f"{output_stem}_summary.md"
    json_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_output.write_text(build_summary(result), encoding="utf-8")
    return json_output, summary_output


def main() -> None:
    result = run_pipeline(call_llm, model=OPENROUTER_MODEL)
    json_output, summary_output = write_result_files(result, "meno_j_experiment_1_q1")

    diagnostics = result["diagnostics"]
    print(f"Experiment completed with model: {result['model']}")
    print(
        "Counts: "
        f"generated={diagnostics['generated_count']}, "
        f"pass={diagnostics['passed_count']}, "
        f"salvageable={diagnostics['salvageable_count']}, "
        f"reject={diagnostics['rejected_count']}"
    )
    print(f"Pass survival rate: {diagnostics['pass_survival_rate']:.1%}")
    print(f"JSON output: {json_output}")
    print(f"Summary output: {summary_output}")


if __name__ == "__main__":
    main()
