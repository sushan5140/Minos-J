"""Run Experiment 3 from the validated Experiment 2 v3 survivor artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_client import OPENROUTER_MODEL, call_llm
from pipeline import run_cross_question_analysis_stage
from run_calibration_suite import QUESTIONS
from run_experiment import OUTPUT_DIR
from schema import (
    EXPERIMENT_3_NAME,
    FALSIFICATION_FIELDS,
    RIVAL_FIELDS,
    validate_audits,
    validate_enrichments,
    validate_hypotheses,
    validate_pass_stage,
)


SOURCE_PATHS = {
    label: OUTPUT_DIR / f"meno_j_experiment_2_v3_{label.lower()}.json"
    for label in QUESTIONS
}
CHECKPOINT_DIR = (
    Path(__file__).resolve().parent / "work" / "experiment_3_checkpoints"
)
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_3_cross_question_survivor_analysis.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_3_cross_question_survivor_analysis.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required validated v3 source is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Source contains invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Source must be a JSON object: {path}")
    return payload


def _validate_source(label: str, result: dict[str, Any]) -> dict[str, Any]:
    if result.get("version") != "v3_enriched":
        raise ValueError(f"{label} source is not v3_enriched.")
    if result.get("research_question") != QUESTIONS[label]:
        raise ValueError(f"{label} research question mismatch.")
    hypotheses = validate_hypotheses({"hypotheses": result.get("stage_4_hypotheses")})
    enrichments = validate_enrichments(
        {"enriched_hypotheses": result.get("stage_4_5_confounder_enrichment")},
        hypotheses,
    )
    audits = validate_audits({"audits": result.get("stage_5_audits")}, hypotheses)
    pass_ids = {
        audit["hypothesis_id"] for audit in audits if audit["audit_decision"] == "PASS"
    }
    rivals = validate_pass_stage(
        {"rival_prediction_matrix": result.get("stage_6_rival_prediction_matrix")},
        "rival_prediction_matrix",
        RIVAL_FIELDS,
        pass_ids,
        f"{label} Stage 6",
    )
    falsifications = validate_pass_stage(
        {"falsification_tests": result.get("stage_7_falsification_tests")},
        "falsification_tests",
        FALSIFICATION_FIELDS,
        pass_ids,
        f"{label} Stage 7",
    )
    diagnostics = result.get("diagnostics", {})
    if diagnostics.get("passed_count") != len(pass_ids):
        raise ValueError(f"{label} diagnostics PASS count mismatch.")
    if diagnostics.get("enriched_count") != 10:
        raise ValueError(f"{label} enriched_count must be 10.")
    if not diagnostics.get("failure_points_consistency"):
        raise ValueError(f"{label} failure_points are inconsistent.")
    return {
        "hypotheses": hypotheses,
        "enrichments": enrichments,
        "audits": audits,
        "rivals": rivals,
        "falsifications": falsifications,
        "pass_ids": pass_ids,
        "diagnostics": diagnostics,
    }


def _survivor_records(
    validated_sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for label in QUESTIONS:
        source = validated_sources[label]
        hypotheses = {item["hypothesis_id"]: item for item in source["hypotheses"]}
        enrichments = {item["hypothesis_id"]: item for item in source["enrichments"]}
        audits = {item["hypothesis_id"]: item for item in source["audits"]}
        rivals = {item["hypothesis_id"]: item for item in source["rivals"]}
        falsifications = {
            item["hypothesis_id"]: item for item in source["falsifications"]
        }
        for hypothesis_id in sorted(
            source["pass_ids"],
            key=lambda value: int(value[1:]),
        ):
            hypothesis = hypotheses[hypothesis_id]
            enrichment = enrichments[hypothesis_id]
            audit = audits[hypothesis_id]
            rival = rivals[hypothesis_id]
            falsification = falsifications[hypothesis_id]
            records.append(
                {
                    "source_question": label,
                    "hypothesis_id": hypothesis_id,
                    "research_question": QUESTIONS[label],
                    "hypothesis": hypothesis["hypothesis"],
                    "original_mechanism": hypothesis["proposed_mechanism"],
                    "enriched_mechanism": enrichment["enriched_mechanism"],
                    "possible_confounders": enrichment["possible_confounders"],
                    "control_variables": enrichment["control_variables"],
                    "rival_explanations": enrichment["rival_explanations"],
                    "minimum_data_needed": enrichment["minimum_data_needed"],
                    "effect_size_expectation": enrichment["effect_size_expectation"],
                    "audit_reason": audit["decision_reason"],
                    "meno_j_prediction": rival["meno_j_prediction"],
                    "rival_prediction": rival["rival_prediction"],
                    "distinguishing_test": rival["distinguishing_test"],
                    "strongest_falsification_test": falsification[
                        "strongest_falsification_test"
                    ],
                    "failure_condition": falsification["failure_condition"],
                }
            )
    return records


def _resolve_strongest(
    analysis: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records_by_reference = {
        (record["source_question"], record["hypothesis_id"]): record
        for record in records
    }
    resolved: list[dict[str, Any]] = []
    for selection in analysis["strongest_surviving_hypotheses"]:
        record = records_by_reference[
            (selection["source_question"], selection["hypothesis_id"])
        ]
        resolved.append(
            {
                **selection,
                "hypothesis": record["hypothesis"],
                "enriched_mechanism": record["enriched_mechanism"],
                "meno_j_prediction": record["meno_j_prediction"],
                "strongest_falsification_test": record[
                    "strongest_falsification_test"
                ],
            }
        )
    return resolved


def _build_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['experiment_name']}",
        "",
        "## Model",
        "",
        f"`{result['model']}`",
        "",
        "## Validated source coverage",
        "",
        "| Question | PASS survivors | Stage 6 rows | Stage 7 rows |",
        "|---|---:|---:|---:|",
    ]
    for label, source in result["source_summary"].items():
        lines.append(
            f"| {label} | {source['passed_count']} | {source['stage_6_count']} | "
            f"{source['stage_7_count']} |"
        )

    lines.extend(["", "## Strongest surviving hypotheses", ""])
    for item in result["strongest_survivor_details"]:
        lines.extend(
            [
                f"### {item['rank']}. {item['source_question']}/{item['hypothesis_id']}",
                "",
                f"**Hypothesis:** {item['hypothesis']}",
                "",
                f"**Enriched mechanism:** {item['enriched_mechanism']}",
                "",
                f"**Why selected:** {item['selection_reason']}",
                "",
                f"**Comparative advantage:** {item['comparative_advantage']}",
                "",
                f"**Residual weakness:** {item['residual_weakness']}",
                "",
                f"**Distinguishing prediction:** {item['meno_j_prediction']}",
                "",
                f"**Strongest falsification test:** {item['strongest_falsification_test']}",
                "",
            ]
        )

    lines.extend(["## Recurring structural patterns", ""])
    for pattern in result["combined_analysis"]["recurring_structural_patterns"]:
        supports = ", ".join(
            f"{ref['source_question']}/{ref['hypothesis_id']}"
            for ref in pattern["supporting_hypotheses"]
        )
        lines.extend(
            [
                f"### {pattern['pattern_id']}: {pattern['pattern_name']}",
                "",
                pattern["description"],
                "",
                f"- Supporting hypotheses: {supports}",
                f"- Causal structure: {pattern['causal_structure']}",
                f"- Boundary conditions: {'; '.join(pattern['boundary_conditions'])}",
                f"- Shared confounder controls: {'; '.join(pattern['shared_confounder_controls'])}",
                f"- Testable meta-prediction: {pattern['testable_meta_prediction']}",
                "",
            ]
        )

    lines.extend(["## Cross-question comparisons", ""])
    for comparison in result["combined_analysis"]["cross_question_comparisons"]:
        lines.extend(
            [
                f"### {comparison['question_pair']}",
                "",
                f"- Shared structures: {'; '.join(comparison['shared_structures'])}",
                f"- Distinctive structures: {'; '.join(comparison['distinctive_structures'])}",
                f"- Discriminating analysis: {comparison['discriminating_analysis']}",
                "",
            ]
        )

    lines.extend(["## Next experiment recommendations", ""])
    for recommendation in result["combined_analysis"]["next_experiment_recommendations"]:
        lines.extend(
            [
                f"### {recommendation['experiment_id']}: {recommendation['title']}",
                "",
                f"- Target patterns: {', '.join(recommendation['target_pattern_ids'])}",
                f"- Design: {recommendation['design']}",
                f"- Minimum data: {'; '.join(recommendation['minimum_data_needed'])}",
                f"- Primary outcome: {recommendation['primary_outcome']}",
                f"- Failure condition: {recommendation['failure_condition']}",
                "",
            ]
        )

    lines.extend(["## Validation", ""])
    for key, value in result["validation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    sources = {label: _read_json(path) for label, path in SOURCE_PATHS.items()}
    validated = {
        label: _validate_source(label, sources[label]) for label in QUESTIONS
    }
    survivors = _survivor_records(validated)
    pass_references = {
        (record["source_question"], record["hypothesis_id"])
        for record in survivors
    }
    analysis = run_cross_question_analysis_stage(
        call_llm,
        survivors,
        pass_references,
        checkpoint_dir=CHECKPOINT_DIR,
    )
    selected_per_question = {
        label: sum(
            item["source_question"] == label
            for item in analysis["strongest_surviving_hypotheses"]
        )
        for label in QUESTIONS
    }
    source_summary = {
        label: {
            "research_question": QUESTIONS[label],
            "passed_count": len(validated[label]["pass_ids"]),
            "pass_ids": sorted(
                validated[label]["pass_ids"],
                key=lambda value: int(value[1:]),
            ),
            "stage_6_count": len(validated[label]["rivals"]),
            "stage_7_count": len(validated[label]["falsifications"]),
            "failure_points_consistency": validated[label]["diagnostics"][
                "failure_points_consistency"
            ],
            "rubber_stamp_red_flags": validated[label]["diagnostics"][
                "rubber_stamp_red_flags"
            ],
        }
        for label in QUESTIONS
    }
    result = {
        "experiment_name": EXPERIMENT_3_NAME,
        "version": "v4_cross_question_synthesis",
        "model": OPENROUTER_MODEL,
        "source_outputs": {
            label: str(path.resolve()) for label, path in SOURCE_PATHS.items()
        },
        "source_summary": source_summary,
        "combined_analysis": analysis,
        "strongest_survivor_details": _resolve_strongest(analysis, survivors),
        "validation": {
            "source_runs_valid": True,
            "source_pass_survivor_count": len(survivors),
            "strongest_survivor_count": len(
                analysis["strongest_surviving_hypotheses"]
            ),
            "strongest_per_question": selected_per_question,
            "recurring_pattern_count": len(
                analysis["recurring_structural_patterns"]
            ),
            "pairwise_comparison_count": len(
                analysis["cross_question_comparisons"]
            ),
            "next_experiment_recommendation_count": len(
                analysis["next_experiment_recommendations"]
            ),
            "all_references_are_validated_pass": True,
            "combined_analysis_valid": True,
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(_build_markdown(result), encoding="utf-8")
    print(f"Experiment 3 JSON: {JSON_OUTPUT}", flush=True)
    print(f"Experiment 3 Markdown: {MARKDOWN_OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
