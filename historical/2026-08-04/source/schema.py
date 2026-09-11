"""Contracts and strict validation for the Meno-J Falsification Engine."""

from __future__ import annotations

from typing import Any


ARCHITECTURE_NAME = "Meno-J: A Falsification-Oriented Architecture for AI"
ARCHITECTURE_SHORT_NAME = "Meno-J Falsification Engine"
ARCHITECTURE_PRINCIPLE = (
    "Speculation is input; disciplined filtering, pattern extraction, rival generation, "
    "and falsification are the contribution."
)
EXPERIMENT_NAME = "Meno-J Experiment 1: Auditor Calibration Test"
RESEARCH_QUESTION = (
    "Why does Mondrian conformal prediction show undercoverage for some "
    "physiological stress subjects in WESAD?"
)
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
EXPERIMENT_2_NAME = "Meno-J Experiment 2: Confounder Enrichment Ablation"
EXPERIMENT_3_NAME = "Meno-J Experiment 3: Cross-Question Survivor Synthesis"
EXPERIMENT_4_NAME = "Meno-J Experiment 4: Pattern Falsification Study"
EXPERIMENT_5_NAME = "Meno-J Experiment 5: P4-F2 Synthetic Feature-Geometry Stress Test"
EXPERIMENT_6_NAME = (
    "Meno-J Experiment 6: P4-F1 Score and Conditioning Comparison Across Sample Sizes"
)
EXPERIMENT_7_NAME = "Meno-J Experiment 7: v4 Architecture Upgrade and Ablation"

MECHANISM_BUILDER_FIELDS = {
    "hypothesis_id",
    "mechanism_variables",
    "causal_path",
    "expected_direction",
    "domain_specific_boundary_conditions",
    "measurable_outcomes",
    "mechanism_builder_notes",
}
CONFOUNDER_RIVAL_BUILDER_FIELDS = {
    "hypothesis_id",
    "possible_confounders",
    "control_variables",
    "boring_rival_explanations",
    "rival_prediction",
    "distinguishing_condition",
    "confounder_rival_notes",
}
STATISTICAL_TESTABILITY_BUILDER_FIELDS = {
    "hypothesis_id",
    "effect_size_expectation",
    "effect_size_rationale",
    "minimum_data_needed",
    "testable_prediction",
    "failure_condition",
    "statistical_test_plan",
    "statistical_testability_notes",
}

P4_F2_REQUIRED_CONDITIONS = {
    "well_separated_gaussian_clusters",
    "overlapping_gaussian_clusters",
    "imbalanced_class_geometry",
    "sparse_subgroup_geometry",
    "covariate_shifted_test_geometry",
}

P4_F2_REQUIRED_SCORES = {
    "margin_score",
    "inverse_probability_score",
    "distance_to_class_centroid_score",
}

P4_F2_REQUIRED_CALIBRATION_SIZES = {50, 100, 300}
P4_F2_REQUIRED_SEEDS = {0, 1, 2, 3, 4}

P4_F1_REQUIRED_CONDITIONS = P4_F2_REQUIRED_CONDITIONS
P4_F1_REQUIRED_SCORES = P4_F2_REQUIRED_SCORES
P4_F1_REQUIRED_CONDITIONING = {
    "marginal",
    "mondrian_class",
    "mondrian_region",
}
P4_F1_REQUIRED_CALIBRATION_SIZES = {50, 100, 300, 600}
P4_F1_REQUIRED_SEEDS = P4_F2_REQUIRED_SEEDS

HYPOTHESIS_FIELDS = {
    "hypothesis_id",
    "hypothesis",
    "proposed_mechanism",
    "core_assumption",
    "knowledge_gap_addressed",
    "status",
}

ENRICHMENT_LIST_FIELDS = (
    "possible_confounders",
    "control_variables",
    "rival_explanations",
    "minimum_data_needed",
)

ENRICHMENT_FIELDS = {
    "hypothesis_id",
    "original_hypothesis",
    "original_mechanism",
    *ENRICHMENT_LIST_FIELDS,
    "effect_size_expectation",
    "enriched_mechanism",
    "enrichment_notes",
}

AUDIT_BOOLEAN_FIELDS = (
    "variables_measurable",
    "causal_chain_valid",
    "base_rate_plausible",
    "confounders_identified",
    "effect_size_plausible",
    "data_requirements_clear",
    "mechanism_is_non_generic",
    "prediction_is_testable",
)

CRITICAL_AUDIT_FIELDS = (
    "variables_measurable",
    "causal_chain_valid",
    "confounders_identified",
    "data_requirements_clear",
    "mechanism_is_non_generic",
    "prediction_is_testable",
)

AUDIT_FIELDS = {
    "hypothesis_id",
    "audit_decision",
    *AUDIT_BOOLEAN_FIELDS,
    "failure_points",
    "decision_reason",
    "salvage_note",
}

RIVAL_FIELDS = {
    "hypothesis_id",
    "meno_j_hypothesis",
    "meno_j_prediction",
    "rival_explanation",
    "rival_prediction",
    "distinguishing_test",
    "what_result_supports_meno_j",
    "what_result_supports_rival",
}

FALSIFICATION_FIELDS = {
    "hypothesis_id",
    "strongest_falsification_test",
    "failure_condition",
    "minimum_data_needed",
    "most_likely_false_positive_risk",
    "most_likely_false_negative_risk",
}

CROSS_QUESTION_STRONGEST_FIELDS = {
    "rank",
    "source_question",
    "hypothesis_id",
    "selection_reason",
    "comparative_advantage",
    "residual_weakness",
}

CROSS_QUESTION_PATTERN_FIELDS = {
    "pattern_id",
    "pattern_name",
    "description",
    "supporting_hypotheses",
    "causal_structure",
    "boundary_conditions",
    "shared_confounder_controls",
    "testable_meta_prediction",
}

CROSS_QUESTION_PAIR_FIELDS = {
    "question_pair",
    "shared_structures",
    "distinctive_structures",
    "discriminating_analysis",
}

CROSS_QUESTION_RECOMMENDATION_FIELDS = {
    "experiment_id",
    "title",
    "target_pattern_ids",
    "design",
    "minimum_data_needed",
    "primary_outcome",
    "failure_condition",
}

FALSIFICATION_EFFECT_SIZE_FIELDS = {
    "metric",
    "magnitude",
    "expected_direction",
    "quantitative_target",
    "rationale",
}

PATTERN_FALSIFICATION_EXPERIMENT_FIELDS = {
    "experiment_id",
    "title",
    "design",
    "meno_j_prediction",
    "competing_explanation_prediction",
    "measurable_outcomes",
    "expected_effect_size",
    "required_datasets_or_metadata",
    "implementation_difficulty",
    "difficulty_reason",
    "failure_condition_for_working_theory",
    "supporting_hypothesis_refs",
    "literature_citation_ids",
    "scientific_impact_score",
    "feasibility_score",
    "publication_potential_score",
    "information_gain_score",
    "score_rationale",
}

PATTERN_NOVELTY_FIELDS = {
    "rating",
    "rationale",
    "closest_literature_citation_ids",
    "novel_contribution",
}

PATTERN_FALSIFICATION_STUDY_FIELDS = {
    "pattern_id",
    "pattern_name",
    "working_theory_claim",
    "strongest_competing_explanation",
    "competing_explanation_mechanism",
    "scientifically_plausible_counterexamples",
    "confounders_and_alternative_explanations",
    "evidence_supporting_competing_explanation",
    "evidence_refuting_competing_explanation",
    "distinguishing_experiments",
    "pattern_level_novelty",
}


class PipelineValidationError(ValueError):
    """Raised when model output violates an experiment contract."""


def _require_exact_fields(item: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise PipelineValidationError(f"{label} must be a JSON object, got {type(item).__name__}.")
    missing = expected - set(item)
    extra = set(item) - expected
    if missing or extra:
        raise PipelineValidationError(
            f"{label} has invalid fields; missing={sorted(missing)}, extra={sorted(extra)}."
        )
    return item


def _require_nonempty_string(value: Any, label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise PipelineValidationError(f"{label} must be {qualifier}.")


def validate_hypotheses(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"hypotheses"}:
        raise PipelineValidationError("Stage 4 must return exactly one top-level key: 'hypotheses'.")
    hypotheses = payload["hypotheses"]
    if not isinstance(hypotheses, list) or len(hypotheses) != 10:
        actual = len(hypotheses) if isinstance(hypotheses, list) else "non-list"
        raise PipelineValidationError(f"Stage 4 must generate exactly 10 hypotheses; got {actual}.")

    expected_ids = [f"H{i}" for i in range(1, 11)]
    actual_ids: list[str] = []
    for index, item in enumerate(hypotheses, start=1):
        hypothesis = _require_exact_fields(item, HYPOTHESIS_FIELDS, f"Stage 4 item {index}")
        for field in HYPOTHESIS_FIELDS - {"status"}:
            _require_nonempty_string(hypothesis[field], f"Stage 4 {hypothesis.get('hypothesis_id', index)}.{field}")
        if hypothesis["status"] != "SPECULATIVE":
            raise PipelineValidationError(
                f"Stage 4 {hypothesis['hypothesis_id']}.status must be 'SPECULATIVE'."
            )
        actual_ids.append(hypothesis["hypothesis_id"])

    if actual_ids != expected_ids:
        raise PipelineValidationError(
            f"Stage 4 hypothesis IDs must be ordered H1 through H10; got {actual_ids}."
        )
    return hypotheses


def validate_enrichments(
    payload: Any,
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"enriched_hypotheses"}:
        raise PipelineValidationError(
            "Stage 4.5 must return exactly one top-level key: 'enriched_hypotheses'."
        )
    enrichments = payload["enriched_hypotheses"]
    if not isinstance(enrichments, list) or len(enrichments) != 10:
        actual = len(enrichments) if isinstance(enrichments, list) else "non-list"
        raise PipelineValidationError(
            f"Stage 4.5 must return exactly 10 enriched hypotheses; got {actual}."
        )

    hypotheses_by_id = {item["hypothesis_id"]: item for item in hypotheses}
    expected_ids = [item["hypothesis_id"] for item in hypotheses]
    actual_ids: list[str] = []
    for index, item in enumerate(enrichments, start=1):
        enrichment = _require_exact_fields(
            item,
            ENRICHMENT_FIELDS,
            f"Stage 4.5 item {index}",
        )
        hypothesis_id = enrichment["hypothesis_id"]
        _require_nonempty_string(hypothesis_id, f"Stage 4.5 item {index}.hypothesis_id")
        if hypothesis_id not in hypotheses_by_id:
            raise PipelineValidationError(
                f"Stage 4.5 contains unknown hypothesis ID: {hypothesis_id}."
            )
        if hypothesis_id in actual_ids:
            raise PipelineValidationError(
                f"Stage 4.5 contains duplicate hypothesis ID: {hypothesis_id}."
            )
        original = hypotheses_by_id[hypothesis_id]
        if enrichment["original_hypothesis"] != original["hypothesis"]:
            raise PipelineValidationError(
                f"Stage 4.5 {hypothesis_id}.original_hypothesis does not match Stage 4."
            )
        if enrichment["original_mechanism"] != original["proposed_mechanism"]:
            raise PipelineValidationError(
                f"Stage 4.5 {hypothesis_id}.original_mechanism does not match Stage 4."
            )
        for field in ENRICHMENT_LIST_FIELDS:
            values = enrichment[field]
            if (
                not isinstance(values, list)
                or not values
                or not all(isinstance(value, str) and value.strip() for value in values)
            ):
                raise PipelineValidationError(
                    f"Stage 4.5 {hypothesis_id}.{field} must be a non-empty string list."
                )
        expectation = enrichment["effect_size_expectation"]
        if not isinstance(expectation, str) or expectation.lower() not in {
            "small",
            "medium",
            "large",
            "unknown",
        }:
            raise PipelineValidationError(
                f"Stage 4.5 {hypothesis_id}.effect_size_expectation must be small, medium, large, or unknown."
            )
        _require_nonempty_string(
            enrichment["enriched_mechanism"],
            f"Stage 4.5 {hypothesis_id}.enriched_mechanism",
        )
        _require_nonempty_string(
            enrichment["enrichment_notes"],
            f"Stage 4.5 {hypothesis_id}.enrichment_notes",
        )
        actual_ids.append(hypothesis_id)

    if actual_ids != expected_ids:
        raise PipelineValidationError(
            f"Stage 4.5 hypothesis IDs must preserve Stage 4 order; got {actual_ids}."
        )
    return enrichments


def validate_audits(payload: Any, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"audits"}:
        raise PipelineValidationError("Stage 5 must return exactly one top-level key: 'audits'.")
    audits = payload["audits"]
    if not isinstance(audits, list):
        raise PipelineValidationError("Stage 5 'audits' must be a list.")
    if len(audits) != len(hypotheses):
        raise PipelineValidationError(
            f"Stage 5 audit count ({len(audits)}) does not equal hypothesis count ({len(hypotheses)})."
        )

    known_ids = {item["hypothesis_id"] for item in hypotheses}
    seen_ids: set[str] = set()
    mismatch_ids: list[str] = []
    for index, item in enumerate(audits, start=1):
        audit = _require_exact_fields(item, AUDIT_FIELDS, f"Stage 5 item {index}")
        hypothesis_id = audit["hypothesis_id"]
        _require_nonempty_string(hypothesis_id, f"Stage 5 item {index}.hypothesis_id")
        if hypothesis_id not in known_ids:
            raise PipelineValidationError(f"Stage 5 contains unknown hypothesis ID: {hypothesis_id}.")
        if hypothesis_id in seen_ids:
            raise PipelineValidationError(f"Stage 5 contains duplicate hypothesis ID: {hypothesis_id}.")
        seen_ids.add(hypothesis_id)

        if audit["audit_decision"] not in {"PASS", "REJECT", "SALVAGEABLE"}:
            raise PipelineValidationError(
                f"Stage 5 {hypothesis_id}.audit_decision must be PASS, REJECT, or SALVAGEABLE."
            )
        for field in AUDIT_BOOLEAN_FIELDS:
            if type(audit[field]) is not bool:
                raise PipelineValidationError(f"Stage 5 {hypothesis_id}.{field} must be boolean.")
        if not isinstance(audit["failure_points"], list) or not all(
            isinstance(field, str) for field in audit["failure_points"]
        ):
            raise PipelineValidationError(f"Stage 5 {hypothesis_id}.failure_points must be a string list.")
        if len(audit["failure_points"]) != len(set(audit["failure_points"])):
            raise PipelineValidationError(f"Stage 5 {hypothesis_id}.failure_points contains duplicates.")
        _require_nonempty_string(audit["decision_reason"], f"Stage 5 {hypothesis_id}.decision_reason")
        _require_nonempty_string(
            audit["salvage_note"],
            f"Stage 5 {hypothesis_id}.salvage_note",
            allow_empty=True,
        )

        false_fields = {field for field in AUDIT_BOOLEAN_FIELDS if not audit[field]}
        if false_fields != set(audit["failure_points"]):
            mismatch_ids.append(hypothesis_id)

        failed_critical = sum(not audit[field] for field in CRITICAL_AUDIT_FIELDS)
        if audit["audit_decision"] == "PASS" and failed_critical:
            raise PipelineValidationError(
                f"Stage 5 {hypothesis_id} cannot PASS because {failed_critical} critical check(s) failed."
            )
        if audit["audit_decision"] == "SALVAGEABLE" and failed_critical not in {1, 2}:
            raise PipelineValidationError(
                f"Stage 5 {hypothesis_id} marked SALVAGEABLE but failed {failed_critical} critical checks; expected 1 or 2."
            )

    if seen_ids != known_ids:
        missing = sorted(known_ids - seen_ids)
        raise PipelineValidationError(f"Stage 5 is missing hypothesis IDs: {missing}.")
    if mismatch_ids:
        raise PipelineValidationError(
            "failure_points mismatch boolean false fields for: " + ", ".join(mismatch_ids)
        )
    return audits


def validate_pass_stage(
    payload: Any,
    top_level_key: str,
    expected_fields: set[str],
    pass_ids: set[str],
    stage_name: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {top_level_key}:
        raise PipelineValidationError(
            f"{stage_name} must return exactly one top-level key: '{top_level_key}'."
        )
    rows = payload[top_level_key]
    if not isinstance(rows, list):
        raise PipelineValidationError(f"{stage_name} '{top_level_key}' must be a list.")
    if len(rows) != len(pass_ids):
        raise PipelineValidationError(
            f"{stage_name} row count ({len(rows)}) does not equal PASS count ({len(pass_ids)})."
        )

    seen_ids: set[str] = set()
    for index, item in enumerate(rows, start=1):
        row = _require_exact_fields(item, expected_fields, f"{stage_name} item {index}")
        hypothesis_id = row["hypothesis_id"]
        if hypothesis_id not in pass_ids:
            raise PipelineValidationError(
                f"{stage_name} received non-PASS or unknown hypothesis ID: {hypothesis_id}."
            )
        if hypothesis_id in seen_ids:
            raise PipelineValidationError(f"{stage_name} contains duplicate hypothesis ID: {hypothesis_id}.")
        seen_ids.add(hypothesis_id)
        for field in expected_fields:
            _require_nonempty_string(row[field], f"{stage_name} {hypothesis_id}.{field}")

    if seen_ids != pass_ids:
        raise PipelineValidationError(
            f"{stage_name} PASS ID mismatch; missing={sorted(pass_ids - seen_ids)}."
        )
    return rows


def _require_nonempty_string_list(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise PipelineValidationError(f"{label} must be a non-empty string list.")
    return value


def _validate_source_reference(
    value: Any,
    pass_references: set[tuple[str, str]],
    label: str,
) -> tuple[str, str]:
    reference = _require_exact_fields(
        value,
        {"source_question", "hypothesis_id"},
        label,
    )
    source_question = reference["source_question"]
    hypothesis_id = reference["hypothesis_id"]
    _require_nonempty_string(source_question, f"{label}.source_question")
    _require_nonempty_string(hypothesis_id, f"{label}.hypothesis_id")
    result = (source_question, hypothesis_id)
    if result not in pass_references:
        raise PipelineValidationError(
            f"{label} references a non-PASS or unknown hypothesis: {source_question}/{hypothesis_id}."
        )
    return result


def validate_cross_question_analysis(
    payload: Any,
    pass_references: set[tuple[str, str]],
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"combined_analysis"}:
        raise PipelineValidationError(
            "Experiment 3 must return exactly one top-level key: 'combined_analysis'."
        )
    analysis = _require_exact_fields(
        payload["combined_analysis"],
        {
            "strongest_surviving_hypotheses",
            "recurring_structural_patterns",
            "cross_question_comparisons",
            "next_experiment_recommendations",
        },
        "Experiment 3 combined_analysis",
    )

    strongest = analysis["strongest_surviving_hypotheses"]
    if not isinstance(strongest, list) or len(strongest) != 9:
        actual = len(strongest) if isinstance(strongest, list) else "non-list"
        raise PipelineValidationError(
            f"Experiment 3 must select exactly 9 strongest survivors; got {actual}."
        )
    selected_references: set[tuple[str, str]] = set()
    selected_questions: list[str] = []
    for index, item in enumerate(strongest, start=1):
        row = _require_exact_fields(
            item,
            CROSS_QUESTION_STRONGEST_FIELDS,
            f"Experiment 3 strongest item {index}",
        )
        if type(row["rank"]) is not int or row["rank"] != index:
            raise PipelineValidationError(
                f"Experiment 3 strongest item {index}.rank must equal {index}."
            )
        reference = (row["source_question"], row["hypothesis_id"])
        if reference not in pass_references:
            raise PipelineValidationError(
                f"Experiment 3 strongest item {index} references non-PASS or unknown {reference}."
            )
        if reference in selected_references:
            raise PipelineValidationError(
                f"Experiment 3 strongest survivors contain duplicate reference {reference}."
            )
        selected_references.add(reference)
        selected_questions.append(row["source_question"])
        for field in CROSS_QUESTION_STRONGEST_FIELDS - {"rank"}:
            _require_nonempty_string(row[field], f"Experiment 3 strongest item {index}.{field}")
    for question in ("Q1", "Q2", "Q3"):
        if selected_questions.count(question) != 3:
            raise PipelineValidationError(
                f"Experiment 3 must select exactly 3 strongest survivors from {question}."
            )

    patterns = analysis["recurring_structural_patterns"]
    if not isinstance(patterns, list) or len(patterns) != 5:
        actual = len(patterns) if isinstance(patterns, list) else "non-list"
        raise PipelineValidationError(
            f"Experiment 3 must identify exactly 5 recurring structural patterns; got {actual}."
        )
    pattern_ids: set[str] = set()
    pattern_support: set[tuple[str, str]] = set()
    for index, item in enumerate(patterns, start=1):
        pattern = _require_exact_fields(
            item,
            CROSS_QUESTION_PATTERN_FIELDS,
            f"Experiment 3 pattern {index}",
        )
        expected_pattern_id = f"P{index}"
        if pattern["pattern_id"] != expected_pattern_id:
            raise PipelineValidationError(
                f"Experiment 3 pattern {index}.pattern_id must be {expected_pattern_id}."
            )
        pattern_ids.add(pattern["pattern_id"])
        for field in (
            "pattern_name",
            "description",
            "causal_structure",
            "testable_meta_prediction",
        ):
            _require_nonempty_string(pattern[field], f"Experiment 3 {expected_pattern_id}.{field}")
        _require_nonempty_string_list(
            pattern["boundary_conditions"],
            f"Experiment 3 {expected_pattern_id}.boundary_conditions",
        )
        _require_nonempty_string_list(
            pattern["shared_confounder_controls"],
            f"Experiment 3 {expected_pattern_id}.shared_confounder_controls",
        )
        references = pattern["supporting_hypotheses"]
        if not isinstance(references, list) or len(references) < 3:
            raise PipelineValidationError(
                f"Experiment 3 {expected_pattern_id} must cite at least 3 supporting hypotheses."
            )
        resolved = {
            _validate_source_reference(
                reference,
                pass_references,
                f"Experiment 3 {expected_pattern_id}.supporting_hypotheses[{ref_index}]",
            )
            for ref_index, reference in enumerate(references, start=1)
        }
        if len(resolved) != len(references):
            raise PipelineValidationError(
                f"Experiment 3 {expected_pattern_id} contains duplicate supporting references."
            )
        if len({question for question, _ in resolved}) < 2:
            raise PipelineValidationError(
                f"Experiment 3 {expected_pattern_id} must recur across at least 2 questions."
            )
        pattern_support.update(resolved)
    if not selected_references.issubset(pattern_support):
        missing = sorted(selected_references - pattern_support)
        raise PipelineValidationError(
            f"Experiment 3 patterns do not cover all strongest survivors: {missing}."
        )

    comparisons = analysis["cross_question_comparisons"]
    expected_pairs = ["Q1-Q2", "Q1-Q3", "Q2-Q3"]
    if not isinstance(comparisons, list) or len(comparisons) != 3:
        raise PipelineValidationError(
            "Experiment 3 must return exactly 3 cross-question comparisons."
        )
    for index, item in enumerate(comparisons):
        comparison = _require_exact_fields(
            item,
            CROSS_QUESTION_PAIR_FIELDS,
            f"Experiment 3 comparison {index + 1}",
        )
        if comparison["question_pair"] != expected_pairs[index]:
            raise PipelineValidationError(
                f"Experiment 3 comparison {index + 1}.question_pair must be {expected_pairs[index]}."
            )
        _require_nonempty_string_list(
            comparison["shared_structures"],
            f"Experiment 3 {expected_pairs[index]}.shared_structures",
        )
        _require_nonempty_string_list(
            comparison["distinctive_structures"],
            f"Experiment 3 {expected_pairs[index]}.distinctive_structures",
        )
        _require_nonempty_string(
            comparison["discriminating_analysis"],
            f"Experiment 3 {expected_pairs[index]}.discriminating_analysis",
        )

    recommendations = analysis["next_experiment_recommendations"]
    if not isinstance(recommendations, list) or len(recommendations) != 3:
        raise PipelineValidationError(
            "Experiment 3 must return exactly 3 next-experiment recommendations."
        )
    for index, item in enumerate(recommendations, start=1):
        recommendation = _require_exact_fields(
            item,
            CROSS_QUESTION_RECOMMENDATION_FIELDS,
            f"Experiment 3 recommendation {index}",
        )
        expected_id = f"E3.{index}"
        if recommendation["experiment_id"] != expected_id:
            raise PipelineValidationError(
                f"Experiment 3 recommendation {index}.experiment_id must be {expected_id}."
            )
        for field in ("title", "design", "primary_outcome", "failure_condition"):
            _require_nonempty_string(
                recommendation[field],
                f"Experiment 3 {expected_id}.{field}",
            )
        targets = _require_nonempty_string_list(
            recommendation["target_pattern_ids"],
            f"Experiment 3 {expected_id}.target_pattern_ids",
        )
        unknown_patterns = set(targets) - pattern_ids
        if unknown_patterns:
            raise PipelineValidationError(
                f"Experiment 3 {expected_id} cites unknown patterns: {sorted(unknown_patterns)}."
            )
        _require_nonempty_string_list(
            recommendation["minimum_data_needed"],
            f"Experiment 3 {expected_id}.minimum_data_needed",
        )
    return analysis


def validate_pattern_falsification_studies(
    payload: Any,
    patterns_by_id: dict[str, dict[str, Any]],
    pass_references: set[tuple[str, str]],
    valid_citation_ids: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"pattern_falsification_studies"}:
        raise PipelineValidationError(
            "Experiment 4 must return exactly one top-level key: 'pattern_falsification_studies'."
        )
    studies = payload["pattern_falsification_studies"]
    if not isinstance(studies, list) or len(studies) != 5:
        actual = len(studies) if isinstance(studies, list) else "non-list"
        raise PipelineValidationError(
            f"Experiment 4 must return exactly 5 pattern studies; got {actual}."
        )

    all_experiment_ids: set[str] = set()
    citations_used: set[str] = set()
    for index, item in enumerate(studies, start=1):
        pattern_id = f"P{index}"
        study = _require_exact_fields(
            item,
            PATTERN_FALSIFICATION_STUDY_FIELDS,
            f"Experiment 4 {pattern_id}",
        )
        if study["pattern_id"] != pattern_id:
            raise PipelineValidationError(
                f"Experiment 4 study {index}.pattern_id must be {pattern_id}."
            )
        source_pattern = patterns_by_id.get(pattern_id)
        if source_pattern is None:
            raise PipelineValidationError(f"Experiment 4 references unknown pattern {pattern_id}.")
        if study["pattern_name"] != source_pattern["pattern_name"]:
            raise PipelineValidationError(
                f"Experiment 4 {pattern_id}.pattern_name must match Experiment 3 exactly."
            )
        for field in (
            "working_theory_claim",
            "strongest_competing_explanation",
            "competing_explanation_mechanism",
        ):
            _require_nonempty_string(study[field], f"Experiment 4 {pattern_id}.{field}")
        for field in (
            "scientifically_plausible_counterexamples",
            "confounders_and_alternative_explanations",
            "evidence_supporting_competing_explanation",
            "evidence_refuting_competing_explanation",
        ):
            values = _require_nonempty_string_list(
                study[field],
                f"Experiment 4 {pattern_id}.{field}",
            )
            if len(values) < 2:
                raise PipelineValidationError(
                    f"Experiment 4 {pattern_id}.{field} must contain at least 2 items."
                )

        source_support = {
            (reference["source_question"], reference["hypothesis_id"])
            for reference in source_pattern["supporting_hypotheses"]
        }
        experiments = study["distinguishing_experiments"]
        if not isinstance(experiments, list) or len(experiments) != 2:
            raise PipelineValidationError(
                f"Experiment 4 {pattern_id} must contain exactly 2 distinguishing experiments."
            )
        for experiment_index, experiment_item in enumerate(experiments, start=1):
            experiment_id = f"{pattern_id}-F{experiment_index}"
            experiment = _require_exact_fields(
                experiment_item,
                PATTERN_FALSIFICATION_EXPERIMENT_FIELDS,
                f"Experiment 4 {experiment_id}",
            )
            if experiment["experiment_id"] != experiment_id:
                raise PipelineValidationError(
                    f"Experiment 4 experiment ID must be {experiment_id}."
                )
            if experiment_id in all_experiment_ids:
                raise PipelineValidationError(
                    f"Experiment 4 contains duplicate experiment ID {experiment_id}."
                )
            all_experiment_ids.add(experiment_id)
            for field in (
                "title",
                "design",
                "meno_j_prediction",
                "competing_explanation_prediction",
                "difficulty_reason",
                "failure_condition_for_working_theory",
                "score_rationale",
            ):
                _require_nonempty_string(
                    experiment[field],
                    f"Experiment 4 {experiment_id}.{field}",
                )
            _require_nonempty_string_list(
                experiment["measurable_outcomes"],
                f"Experiment 4 {experiment_id}.measurable_outcomes",
            )
            _require_nonempty_string_list(
                experiment["required_datasets_or_metadata"],
                f"Experiment 4 {experiment_id}.required_datasets_or_metadata",
            )
            effect = _require_exact_fields(
                experiment["expected_effect_size"],
                FALSIFICATION_EFFECT_SIZE_FIELDS,
                f"Experiment 4 {experiment_id}.expected_effect_size",
            )
            for field in FALSIFICATION_EFFECT_SIZE_FIELDS - {"magnitude"}:
                _require_nonempty_string(
                    effect[field],
                    f"Experiment 4 {experiment_id}.expected_effect_size.{field}",
                )
            if effect["magnitude"] not in {"SMALL", "MEDIUM", "LARGE", "UNKNOWN"}:
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id}.expected_effect_size.magnitude has invalid value."
                )
            difficulty = experiment["implementation_difficulty"]
            if difficulty not in {"LOW", "MEDIUM", "HIGH"}:
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id}.implementation_difficulty has invalid value."
                )
            supporting_refs = experiment["supporting_hypothesis_refs"]
            if not isinstance(supporting_refs, list) or len(supporting_refs) < 2:
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id} must cite at least 2 supporting hypotheses."
                )
            resolved_refs = {
                _validate_source_reference(
                    reference,
                    pass_references,
                    f"Experiment 4 {experiment_id}.supporting_hypothesis_refs[{ref_index}]",
                )
                for ref_index, reference in enumerate(supporting_refs, start=1)
            }
            if len(resolved_refs) != len(supporting_refs):
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id} contains duplicate hypothesis references."
                )
            if not resolved_refs.issubset(source_support):
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id} cites hypotheses outside {pattern_id}'s support set."
                )
            citations = _require_nonempty_string_list(
                experiment["literature_citation_ids"],
                f"Experiment 4 {experiment_id}.literature_citation_ids",
            )
            unknown_citations = set(citations) - valid_citation_ids
            if unknown_citations:
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id} cites unknown literature IDs: {sorted(unknown_citations)}."
                )
            citations_used.update(citations)
            for score_field in (
                "scientific_impact_score",
                "feasibility_score",
                "publication_potential_score",
                "information_gain_score",
            ):
                score = experiment[score_field]
                if type(score) is not int or not 1 <= score <= 5:
                    raise PipelineValidationError(
                        f"Experiment 4 {experiment_id}.{score_field} must be an integer from 1 to 5."
                    )
            feasibility = experiment["feasibility_score"]
            if (
                (difficulty == "LOW" and feasibility < 4)
                or (difficulty == "HIGH" and feasibility > 2)
            ):
                raise PipelineValidationError(
                    f"Experiment 4 {experiment_id} difficulty and feasibility score are inconsistent."
                )

        novelty = _require_exact_fields(
            study["pattern_level_novelty"],
            PATTERN_NOVELTY_FIELDS,
            f"Experiment 4 {pattern_id}.pattern_level_novelty",
        )
        if novelty["rating"] not in {"LOW", "MEDIUM", "HIGH"}:
            raise PipelineValidationError(
                f"Experiment 4 {pattern_id} novelty rating has invalid value."
            )
        for field in ("rationale", "novel_contribution"):
            _require_nonempty_string(
                novelty[field],
                f"Experiment 4 {pattern_id}.pattern_level_novelty.{field}",
            )
        closest = _require_nonempty_string_list(
            novelty["closest_literature_citation_ids"],
            f"Experiment 4 {pattern_id}.pattern_level_novelty.closest_literature_citation_ids",
        )
        if len(closest) < 2:
            raise PipelineValidationError(
                f"Experiment 4 {pattern_id} novelty assessment must cite at least 2 sources."
            )
        unknown_closest = set(closest) - valid_citation_ids
        if unknown_closest:
            raise PipelineValidationError(
                f"Experiment 4 {pattern_id} novelty cites unknown IDs: {sorted(unknown_closest)}."
            )
        citations_used.update(closest)

    if len(all_experiment_ids) != 10:
        raise PipelineValidationError("Experiment 4 must contain exactly 10 unique experiments.")
    if not valid_citation_ids.issubset(citations_used):
        missing = sorted(valid_citation_ids - citations_used)
        raise PipelineValidationError(
            f"Experiment 4 did not use every validated literature source: {missing}."
        )
    return studies


def validate_p4_f2_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise PipelineValidationError("Experiment 5 report must be a JSON object.")
    required_top_level = {
        "experiment_name",
        "roadmap_item",
        "pattern_tested",
        "competing_explanation",
        "target_coverage",
        "alpha",
        "simulation_conditions",
        "nonconformity_scores",
        "conditioning_strategies",
        "calibration_sizes",
        "seeds",
        "simulation_config",
        "roadmap_source",
        "results",
        "aggregate_results",
        "p4_survival_assessment",
        "limitations",
        "next_recommended_experiment",
        "validation",
    }
    missing = required_top_level - set(report)
    extra = set(report) - required_top_level
    if missing or extra:
        raise PipelineValidationError(
            f"Experiment 5 report fields invalid; missing={sorted(missing)}, extra={sorted(extra)}."
        )
    if report["experiment_name"] != EXPERIMENT_5_NAME:
        raise PipelineValidationError("Experiment 5 name mismatch.")
    if report["roadmap_item"] != "P4-F2" or report["pattern_tested"] != "P4":
        raise PipelineValidationError("Experiment 5 must execute roadmap item P4-F2 for P4.")
    if report["target_coverage"] != 0.9 or report["alpha"] != 0.1:
        raise PipelineValidationError("Experiment 5 target coverage and alpha must be 0.90 and 0.10.")
    if set(report["simulation_conditions"]) != P4_F2_REQUIRED_CONDITIONS:
        raise PipelineValidationError("Experiment 5 simulation conditions are incomplete.")
    if set(report["nonconformity_scores"]) != P4_F2_REQUIRED_SCORES:
        raise PipelineValidationError("Experiment 5 nonconformity scores are incomplete.")
    if set(report["conditioning_strategies"]) != {"marginal", "mondrian_class"}:
        raise PipelineValidationError("Experiment 5 conditioning strategies are incomplete.")
    if set(report["calibration_sizes"]) != P4_F2_REQUIRED_CALIBRATION_SIZES:
        raise PipelineValidationError("Experiment 5 calibration sizes are incomplete.")
    if set(report["seeds"]) != P4_F2_REQUIRED_SEEDS:
        raise PipelineValidationError("Experiment 5 seeds are incomplete.")

    results = report["results"]
    expected_count = (
        len(P4_F2_REQUIRED_CONDITIONS)
        * len(P4_F2_REQUIRED_SCORES)
        * 2
        * len(P4_F2_REQUIRED_CALIBRATION_SIZES)
        * len(P4_F2_REQUIRED_SEEDS)
    )
    if not isinstance(results, list) or len(results) != expected_count:
        actual = len(results) if isinstance(results, list) else "non-list"
        raise PipelineValidationError(
            f"Experiment 5 must contain {expected_count} seed-level results; got {actual}."
        )
    seen_keys: set[tuple[Any, ...]] = set()
    for index, row in enumerate(results, start=1):
        required_result_fields = {
            "condition",
            "score_type",
            "conditioning_strategy",
            "calibration_size",
            "seed",
            "marginal_coverage",
            "conditional_coverage_by_class",
            "conditional_coverage_by_subgroup_or_region",
            "coverage_gap",
            "minimum_group_coverage",
            "average_set_size",
            "undercoverage_rate",
        }
        _require_exact_fields(row, required_result_fields, f"Experiment 5 result {index}")
        key = (
            row["condition"],
            row["score_type"],
            row["conditioning_strategy"],
            row["calibration_size"],
            row["seed"],
        )
        if key in seen_keys:
            raise PipelineValidationError(f"Experiment 5 contains duplicate result key {key}.")
        seen_keys.add(key)
        if row["condition"] not in P4_F2_REQUIRED_CONDITIONS:
            raise PipelineValidationError(f"Experiment 5 result {index} has unknown condition.")
        if row["score_type"] not in P4_F2_REQUIRED_SCORES:
            raise PipelineValidationError(f"Experiment 5 result {index} has unknown score.")
        if row["conditioning_strategy"] not in {"marginal", "mondrian_class"}:
            raise PipelineValidationError(f"Experiment 5 result {index} has unknown conditioning.")
        if row["calibration_size"] not in P4_F2_REQUIRED_CALIBRATION_SIZES:
            raise PipelineValidationError(f"Experiment 5 result {index} has invalid calibration size.")
        if row["seed"] not in P4_F2_REQUIRED_SEEDS:
            raise PipelineValidationError(f"Experiment 5 result {index} has invalid seed.")
        for field in (
            "marginal_coverage",
            "minimum_group_coverage",
            "undercoverage_rate",
        ):
            value = row[field]
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise PipelineValidationError(
                    f"Experiment 5 result {index}.{field} must be between 0 and 1."
                )
        if not isinstance(row["coverage_gap"], (int, float)) or row["coverage_gap"] < 0:
            raise PipelineValidationError(
                f"Experiment 5 result {index}.coverage_gap must be non-negative."
            )
        if not isinstance(row["average_set_size"], (int, float)) or row[
            "average_set_size"
        ] <= 0:
            raise PipelineValidationError(
                f"Experiment 5 result {index}.average_set_size must be positive."
            )
        for field in (
            "conditional_coverage_by_class",
            "conditional_coverage_by_subgroup_or_region",
        ):
            values = row[field]
            if not isinstance(values, dict) or not values:
                raise PipelineValidationError(
                    f"Experiment 5 result {index}.{field} must be a non-empty object."
                )
            if not all(
                isinstance(name, str)
                and isinstance(value, (int, float))
                and 0 <= value <= 1
                for name, value in values.items()
            ):
                raise PipelineValidationError(
                    f"Experiment 5 result {index}.{field} contains invalid coverage values."
                )

    aggregates = report["aggregate_results"]
    expected_aggregate_count = expected_count // len(P4_F2_REQUIRED_SEEDS)
    if not isinstance(aggregates, list) or len(aggregates) != expected_aggregate_count:
        raise PipelineValidationError(
            f"Experiment 5 must contain {expected_aggregate_count} aggregate rows."
        )
    assessment = report["p4_survival_assessment"]
    required_assessment = {
        "status",
        "rationale",
        "strongest_failure_case",
        "strongest_support_case",
        "decision_metrics",
    }
    _require_exact_fields(assessment, required_assessment, "Experiment 5 assessment")
    if assessment["status"] not in {"SURVIVES", "WEAKENED", "FALSIFIED", "INCONCLUSIVE"}:
        raise PipelineValidationError("Experiment 5 survival status is invalid.")
    for field in ("rationale", "strongest_failure_case", "strongest_support_case"):
        _require_nonempty_string(assessment[field], f"Experiment 5 assessment.{field}")
    if not isinstance(assessment["decision_metrics"], dict) or not assessment[
        "decision_metrics"
    ]:
        raise PipelineValidationError("Experiment 5 decision metrics are missing.")

    validation = report["validation"]
    required_validation = {
        "new_hypotheses_generated",
        "upstream_successful_stages_rerun",
        "model_call_used",
        "effect_size_targets_present",
        "failure_conditions_present",
        "credential_found_in_project_files",
    }
    _require_exact_fields(validation, required_validation, "Experiment 5 validation")
    if validation["new_hypotheses_generated"] != 0:
        raise PipelineValidationError("Experiment 5 must generate zero new hypotheses.")
    for field in (
        "upstream_successful_stages_rerun",
        "model_call_used",
        "credential_found_in_project_files",
    ):
        if validation[field] is not False:
            raise PipelineValidationError(f"Experiment 5 validation.{field} must be false.")
    for field in ("effect_size_targets_present", "failure_conditions_present"):
        if validation[field] is not True:
            raise PipelineValidationError(f"Experiment 5 validation.{field} must be true.")
    _require_nonempty_string_list(report["limitations"], "Experiment 5 limitations")
    _require_nonempty_string(
        report["next_recommended_experiment"],
        "Experiment 5 next_recommended_experiment",
    )
    return report


def validate_p4_f1_report(report: Any) -> dict[str, Any]:
    """Validate the complete deterministic Experiment 6 artifact."""
    if not isinstance(report, dict):
        raise PipelineValidationError("Experiment 6 report must be a JSON object.")
    required_top_level = {
        "experiment_name",
        "roadmap_item",
        "pattern_tested",
        "prior_result",
        "target_coverage",
        "simulation_conditions",
        "nonconformity_scores",
        "conditioning_strategies",
        "calibration_sizes",
        "seeds",
        "simulation_config",
        "roadmap_source",
        "experiment_5_source",
        "seed_level_results",
        "aggregate_results",
        "trend_results",
        "robustness_ranking",
        "persistent_failure_cases",
        "core_answers",
        "p4_followup_assessment",
        "limitations",
        "next_recommended_experiment",
        "validation",
    }
    _require_exact_fields(report, required_top_level, "Experiment 6 report")
    if report["experiment_name"] != EXPERIMENT_6_NAME:
        raise PipelineValidationError("Experiment 6 name mismatch.")
    if report["roadmap_item"] != "P4-F1" or report["pattern_tested"] != "P4":
        raise PipelineValidationError("Experiment 6 must execute roadmap item P4-F1 for P4.")
    if report["target_coverage"] != 0.9:
        raise PipelineValidationError("Experiment 6 target coverage must be 0.90.")
    if set(report["simulation_conditions"]) != P4_F1_REQUIRED_CONDITIONS:
        raise PipelineValidationError("Experiment 6 geometries are incomplete.")
    if set(report["nonconformity_scores"]) != P4_F1_REQUIRED_SCORES:
        raise PipelineValidationError("Experiment 6 scores are incomplete.")
    if set(report["conditioning_strategies"]) != P4_F1_REQUIRED_CONDITIONING:
        raise PipelineValidationError("Experiment 6 conditioning strategies are incomplete.")
    if set(report["calibration_sizes"]) != P4_F1_REQUIRED_CALIBRATION_SIZES:
        raise PipelineValidationError("Experiment 6 calibration sizes are incomplete.")
    if set(report["seeds"]) != P4_F1_REQUIRED_SEEDS:
        raise PipelineValidationError("Experiment 6 seeds are incomplete.")

    results = report["seed_level_results"]
    expected_count = (
        len(P4_F1_REQUIRED_CONDITIONS)
        * len(P4_F1_REQUIRED_SCORES)
        * len(P4_F1_REQUIRED_CONDITIONING)
        * len(P4_F1_REQUIRED_CALIBRATION_SIZES)
        * len(P4_F1_REQUIRED_SEEDS)
    )
    if not isinstance(results, list) or len(results) != expected_count:
        actual = len(results) if isinstance(results, list) else "non-list"
        raise PipelineValidationError(
            f"Experiment 6 must contain {expected_count} seed-level rows; got {actual}."
        )
    result_fields = {
        "condition",
        "score_type",
        "conditioning_strategy",
        "calibration_size",
        "seed",
        "marginal_coverage",
        "conditional_coverage_by_class",
        "conditional_coverage_by_region_or_subgroup",
        "coverage_gap",
        "minimum_group_coverage",
        "average_set_size",
        "undercoverage_rate",
    }
    seen: set[tuple[Any, ...]] = set()
    for index, row in enumerate(results, start=1):
        _require_exact_fields(row, result_fields, f"Experiment 6 result {index}")
        key = tuple(
            row[field]
            for field in (
                "condition",
                "score_type",
                "conditioning_strategy",
                "calibration_size",
                "seed",
            )
        )
        if key in seen:
            raise PipelineValidationError(f"Experiment 6 duplicate result key: {key}.")
        seen.add(key)
        if row["condition"] not in P4_F1_REQUIRED_CONDITIONS:
            raise PipelineValidationError(f"Experiment 6 result {index} has unknown geometry.")
        if row["score_type"] not in P4_F1_REQUIRED_SCORES:
            raise PipelineValidationError(f"Experiment 6 result {index} has unknown score.")
        if row["conditioning_strategy"] not in P4_F1_REQUIRED_CONDITIONING:
            raise PipelineValidationError(f"Experiment 6 result {index} has unknown conditioning.")
        if row["calibration_size"] not in P4_F1_REQUIRED_CALIBRATION_SIZES:
            raise PipelineValidationError(f"Experiment 6 result {index} has invalid n_calib.")
        if row["seed"] not in P4_F1_REQUIRED_SEEDS:
            raise PipelineValidationError(f"Experiment 6 result {index} has invalid seed.")
        for field in ("marginal_coverage", "minimum_group_coverage", "undercoverage_rate"):
            value = row[field]
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise PipelineValidationError(
                    f"Experiment 6 result {index}.{field} must be between 0 and 1."
                )
        if not isinstance(row["coverage_gap"], (int, float)) or row["coverage_gap"] < 0:
            raise PipelineValidationError(
                f"Experiment 6 result {index}.coverage_gap must be non-negative."
            )
        if not isinstance(row["average_set_size"], (int, float)) or row["average_set_size"] <= 0:
            raise PipelineValidationError(
                f"Experiment 6 result {index}.average_set_size must be positive."
            )
        for field in (
            "conditional_coverage_by_class",
            "conditional_coverage_by_region_or_subgroup",
        ):
            mapping = row[field]
            if not isinstance(mapping, dict) or not mapping:
                raise PipelineValidationError(
                    f"Experiment 6 result {index}.{field} must be non-empty."
                )
            if not all(
                isinstance(name, str)
                and isinstance(value, (int, float))
                and 0 <= value <= 1
                for name, value in mapping.items()
            ):
                raise PipelineValidationError(
                    f"Experiment 6 result {index}.{field} contains invalid coverage."
                )

    aggregates = report["aggregate_results"]
    expected_aggregates = expected_count // len(P4_F1_REQUIRED_SEEDS)
    if not isinstance(aggregates, list) or len(aggregates) != expected_aggregates:
        raise PipelineValidationError(
            f"Experiment 6 must contain {expected_aggregates} aggregate rows."
        )
    if not isinstance(report["trend_results"], list) or len(report["trend_results"]) != 45:
        raise PipelineValidationError("Experiment 6 must contain 45 design-cell trends.")
    failures = report["persistent_failure_cases"]
    if not isinstance(failures, list) or not failures:
        raise PipelineValidationError("Experiment 6 persistent failure cases are missing.")
    if not all(row.get("persistent_failure") is True for row in failures):
        raise PipelineValidationError("Experiment 6 failure list contains a non-failure.")
    ranking = report["robustness_ranking"]
    if not isinstance(ranking, list) or not ranking:
        raise PipelineValidationError("Experiment 6 robustness ranking is missing.")

    answers = report["core_answers"]
    answer_fields = {
        "most_robust_score",
        "most_robust_conditioning_strategy",
        "worst_geometry",
        "calibration_size_effect",
        "most_dangerous_score_conditioning_pair",
        "safest_score_conditioning_pair",
    }
    _require_exact_fields(answers, answer_fields, "Experiment 6 core answers")
    for field in answer_fields:
        _require_nonempty_string(answers[field], f"Experiment 6 core_answers.{field}")

    assessment = report["p4_followup_assessment"]
    assessment_fields = {
        "status",
        "rationale",
        "strongest_structural_failure_case",
        "strongest_size_effect_case",
    }
    _require_exact_fields(assessment, assessment_fields, "Experiment 6 assessment")
    if assessment["status"] not in {
        "STRUCTURAL_FAILURE_CONFIRMED",
        "PARTIALLY_SIZE_DEPENDENT",
        "INCONCLUSIVE",
    }:
        raise PipelineValidationError("Experiment 6 follow-up status is invalid.")
    for field in assessment_fields - {"status"}:
        _require_nonempty_string(assessment[field], f"Experiment 6 assessment.{field}")

    validation = report["validation"]
    validation_fields = {
        "new_hypotheses_generated",
        "upstream_successful_stages_rerun",
        "model_call_used",
        "effect_size_targets_present",
        "failure_conditions_present",
        "credential_found_in_project_files",
    }
    _require_exact_fields(validation, validation_fields, "Experiment 6 validation")
    if validation["new_hypotheses_generated"] != 0:
        raise PipelineValidationError("Experiment 6 must generate zero hypotheses.")
    for field in (
        "upstream_successful_stages_rerun",
        "model_call_used",
        "credential_found_in_project_files",
    ):
        if validation[field] is not False:
            raise PipelineValidationError(f"Experiment 6 validation.{field} must be false.")
    for field in ("effect_size_targets_present", "failure_conditions_present"):
        if validation[field] is not True:
            raise PipelineValidationError(f"Experiment 6 validation.{field} must be true.")
    _require_nonempty_string_list(report["limitations"], "Experiment 6 limitations")
    _require_nonempty_string(
        report["next_recommended_experiment"],
        "Experiment 6 next recommended experiment",
    )
    return report


def _validate_v4_builder(
    payload: Any,
    top_level_key: str,
    expected_fields: set[str],
    list_fields: set[str],
    hypotheses: list[dict[str, Any]],
    stage_name: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {top_level_key}:
        raise PipelineValidationError(
            f"{stage_name} must return exactly one top-level key: '{top_level_key}'."
        )
    rows = payload[top_level_key]
    expected_count = len(hypotheses)
    if not isinstance(rows, list) or len(rows) != expected_count:
        actual = len(rows) if isinstance(rows, list) else "non-list"
        raise PipelineValidationError(
            f"{stage_name} must return exactly {expected_count} rows; got {actual}."
        )
    expected_ids = [item["hypothesis_id"] for item in hypotheses]
    actual_ids: list[str] = []
    for index, item in enumerate(rows, start=1):
        row = _require_exact_fields(item, expected_fields, f"{stage_name} item {index}")
        hypothesis_id = row["hypothesis_id"]
        _require_nonempty_string(hypothesis_id, f"{stage_name} item {index}.hypothesis_id")
        if hypothesis_id not in expected_ids:
            raise PipelineValidationError(
                f"{stage_name} contains unknown hypothesis ID: {hypothesis_id}."
            )
        if hypothesis_id in actual_ids:
            raise PipelineValidationError(
                f"{stage_name} contains duplicate hypothesis ID: {hypothesis_id}."
            )
        for field in list_fields:
            _require_nonempty_string_list(row[field], f"{stage_name} {hypothesis_id}.{field}")
        for field in expected_fields - list_fields - {"hypothesis_id", "effect_size_expectation"}:
            _require_nonempty_string(row[field], f"{stage_name} {hypothesis_id}.{field}")
        if "effect_size_expectation" in expected_fields:
            expectation = row["effect_size_expectation"]
            if not isinstance(expectation, str) or expectation.lower() not in {
                "small",
                "medium",
                "large",
                "unknown",
            }:
                raise PipelineValidationError(
                    f"{stage_name} {hypothesis_id}.effect_size_expectation is invalid."
                )
            row["effect_size_expectation"] = expectation.lower()
        actual_ids.append(hypothesis_id)
    if actual_ids != expected_ids:
        raise PipelineValidationError(
            f"{stage_name} hypothesis IDs must preserve Stage 4 order; got {actual_ids}."
        )
    return rows


def validate_mechanism_builds(
    payload: Any,
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _validate_v4_builder(
        payload,
        "mechanism_builds",
        MECHANISM_BUILDER_FIELDS,
        {"mechanism_variables", "domain_specific_boundary_conditions", "measurable_outcomes"},
        hypotheses,
        "Stage 4.1",
    )


def validate_confounder_rival_builds(
    payload: Any,
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _validate_v4_builder(
        payload,
        "confounder_rival_builds",
        CONFOUNDER_RIVAL_BUILDER_FIELDS,
        {"possible_confounders", "control_variables", "boring_rival_explanations"},
        hypotheses,
        "Stage 4.2",
    )


def validate_statistical_testability_builds(
    payload: Any,
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return _validate_v4_builder(
        payload,
        "statistical_testability_builds",
        STATISTICAL_TESTABILITY_BUILDER_FIELDS,
        {"minimum_data_needed"},
        hypotheses,
        "Stage 4.3",
    )


def validate_v4_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise PipelineValidationError("Experiment 7 v4 output must be a JSON object.")
    required_fields = {
        "experiment_name",
        "version",
        "research_question",
        "model",
        "stage_4_hypotheses",
        "stage_4_1_mechanism_builder",
        "stage_4_2_confounder_rival_builder",
        "stage_4_3_statistical_testability_builder",
        "stage_5_audits",
        "diagnostics",
        "stage_6_rival_prediction_matrix",
        "stage_7_falsification_tests",
    }
    optional_fields = {"metadata"}
    missing = required_fields - set(report)
    extra = set(report) - required_fields - optional_fields
    if missing or extra:
        raise PipelineValidationError(
            f"Experiment 7 v4 output fields invalid; missing={sorted(missing)}, "
            f"extra={sorted(extra)}."
        )
    if report["experiment_name"] != EXPERIMENT_7_NAME:
        raise PipelineValidationError("Experiment 7 name mismatch.")
    if report["version"] != "v4_mechanism_confounder_testability":
        raise PipelineValidationError("Experiment 7 version mismatch.")
    if "metadata" in report:
        metadata = _require_exact_fields(
            report["metadata"],
            {
                "fallback_model_used",
                "fallback_reason",
                "primary_model",
                "stage_4_3_chunked",
                "retry_diagnostics",
            },
            "Experiment 7 metadata",
        )
        if type(metadata["fallback_model_used"]) is not bool:
            raise PipelineValidationError(
                "Experiment 7 metadata.fallback_model_used must be boolean."
            )
        if type(metadata["stage_4_3_chunked"]) is not bool:
            raise PipelineValidationError(
                "Experiment 7 metadata.stage_4_3_chunked must be boolean."
            )
        _require_nonempty_string(
            metadata["fallback_reason"], "Experiment 7 metadata.fallback_reason"
        )
        _require_nonempty_string(
            metadata["primary_model"], "Experiment 7 metadata.primary_model"
        )
        if not isinstance(metadata["retry_diagnostics"], dict):
            raise PipelineValidationError(
                "Experiment 7 metadata.retry_diagnostics must be an object."
            )
    _require_nonempty_string(report["research_question"], "Experiment 7 research question")
    _require_nonempty_string(report["model"], "Experiment 7 model")
    hypotheses = validate_hypotheses({"hypotheses": report["stage_4_hypotheses"]})
    validate_mechanism_builds(
        {"mechanism_builds": report["stage_4_1_mechanism_builder"]}, hypotheses
    )
    validate_confounder_rival_builds(
        {"confounder_rival_builds": report["stage_4_2_confounder_rival_builder"]},
        hypotheses,
    )
    validate_statistical_testability_builds(
        {
            "statistical_testability_builds": report[
                "stage_4_3_statistical_testability_builder"
            ]
        },
        hypotheses,
    )
    audits = validate_audits({"audits": report["stage_5_audits"]}, hypotheses)
    pass_ids = {
        audit["hypothesis_id"]
        for audit in audits
        if audit["audit_decision"] == "PASS"
    }
    validate_pass_stage(
        {"rival_prediction_matrix": report["stage_6_rival_prediction_matrix"]},
        "rival_prediction_matrix",
        RIVAL_FIELDS,
        pass_ids,
        "Stage 6",
    )
    validate_pass_stage(
        {"falsification_tests": report["stage_7_falsification_tests"]},
        "falsification_tests",
        FALSIFICATION_FIELDS,
        pass_ids,
        "Stage 7",
    )
    diagnostics = report["diagnostics"]
    required_diagnostics = {
        "generated_count",
        "passed_count",
        "rejected_count",
        "salvageable_count",
        "pass_survival_rate",
        "salvageable_rate",
        "rejection_reason_diversity",
        "top_failed_checklist_fields",
        "failure_points_consistency",
        "rubber_stamp_red_flags",
        "mechanism_builder_count",
        "confounder_rival_builder_count",
        "statistical_testability_builder_count",
        "avg_mechanism_variables_per_hypothesis",
        "avg_confounders_per_hypothesis",
        "avg_rivals_per_hypothesis",
        "hypotheses_with_effect_size_expectation",
        "hypotheses_with_failure_condition",
        "hypotheses_with_testable_prediction",
    }
    _require_exact_fields(diagnostics, required_diagnostics, "Experiment 7 diagnostics")
    for field in (
        "generated_count",
        "mechanism_builder_count",
        "confounder_rival_builder_count",
        "statistical_testability_builder_count",
        "hypotheses_with_effect_size_expectation",
        "hypotheses_with_failure_condition",
        "hypotheses_with_testable_prediction",
    ):
        if diagnostics[field] != 10:
            raise PipelineValidationError(f"Experiment 7 diagnostics.{field} must equal 10.")
    if diagnostics["failure_points_consistency"] is not True:
        raise PipelineValidationError("Experiment 7 failure_points must be consistent.")
    return report
