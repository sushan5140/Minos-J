"""Checkpointable filtering and falsification workflows for the Meno-J engine."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from prompts import (
    auditor_prompt,
    confounder_rival_builder_prompt,
    confounder_enrichment_prompt,
    cross_question_survivor_prompt,
    dreamer_prompt,
    falsification_prompt,
    mechanism_builder_prompt,
    pattern_falsification_prompt,
    rival_prompt,
    statistical_testability_builder_prompt,
)
from schema import (
    AUDIT_BOOLEAN_FIELDS,
    DEFAULT_MODEL,
    EXPERIMENT_NAME,
    EXPERIMENT_2_NAME,
    EXPERIMENT_7_NAME,
    FALSIFICATION_FIELDS,
    RESEARCH_QUESTION,
    RIVAL_FIELDS,
    validate_cross_question_analysis,
    validate_audits,
    validate_confounder_rival_builds,
    validate_enrichments,
    validate_hypotheses,
    validate_mechanism_builds,
    validate_pattern_falsification_studies,
    validate_pass_stage,
    validate_statistical_testability_builds,
    validate_v4_report,
)


LLMCaller = Callable[[str], dict]


def _read_checkpoint(directory: Path | None, filename: str) -> dict[str, Any] | None:
    if directory is None:
        return None
    path = directory / filename
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Checkpoint contains invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Checkpoint must contain a JSON object: {path}")
    return payload


def _write_checkpoint(
    directory: Path | None,
    filename: str,
    payload: dict[str, Any],
) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalized_reason(reason: str) -> str:
    return " ".join(reason.lower().split()).strip(" .")


def _generic_reason_red_flag(audits: list[dict[str, Any]]) -> bool:
    generic_phrases = {
        "meets all criteria",
        "fails to meet criteria",
        "the hypothesis is plausible",
        "the hypothesis is not plausible",
        "insufficient detail",
        "more research is needed",
    }
    generic_count = 0
    for audit in audits:
        normalized = _normalized_reason(audit["decision_reason"])
        word_count = len(normalized.split())
        if word_count < 8 or normalized in generic_phrases:
            generic_count += 1
    return bool(audits) and generic_count >= max(2, len(audits) // 2)


def compute_diagnostics(audits: list[dict[str, Any]], generated_count: int) -> dict[str, Any]:
    decisions = Counter(audit["audit_decision"] for audit in audits)
    failed_fields = Counter(
        field
        for audit in audits
        if audit["audit_decision"] in {"REJECT", "SALVAGEABLE"}
        for field in audit["failure_points"]
    )
    mismatch = any(
        {field for field in AUDIT_BOOLEAN_FIELDS if not audit[field]}
        != set(audit["failure_points"])
        for audit in audits
    )
    nonpass_reasons = [
        _normalized_reason(audit["decision_reason"])
        for audit in audits
        if audit["audit_decision"] in {"REJECT", "SALVAGEABLE"}
    ]
    all_checklists_true = all(
        audit[field] for audit in audits for field in AUDIT_BOOLEAN_FIELDS
    ) if audits else False

    red_flags: list[str] = []
    if generated_count == 10 and decisions["PASS"] == 10:
        red_flags.append("10/10 passed")
    if not failed_fields:
        red_flags.append("0 rejection reasons")
    if len(nonpass_reasons) > 1 and len(set(nonpass_reasons)) == 1:
        red_flags.append("all reasons identical")
    if all_checklists_true:
        red_flags.append("all checklist values true")
    if mismatch:
        red_flags.append("failure_points mismatch")
    if decisions["SALVAGEABLE"] == 0 and decisions["REJECT"] == 0:
        red_flags.append("no salvageable or rejected hypotheses")
    if _generic_reason_red_flag(audits):
        red_flags.append("generic boilerplate decision reasons")

    ordered_failed_fields = dict(
        sorted(failed_fields.items(), key=lambda pair: (-pair[1], pair[0]))
    )
    return {
        "generated_count": generated_count,
        "passed_count": decisions["PASS"],
        "rejected_count": decisions["REJECT"],
        "salvageable_count": decisions["SALVAGEABLE"],
        "pass_survival_rate": decisions["PASS"] / generated_count if generated_count else 0.0,
        "salvageable_rate": decisions["SALVAGEABLE"] / generated_count if generated_count else 0.0,
        "rejection_reason_diversity": len(failed_fields),
        "top_failed_checklist_fields": ordered_failed_fields,
        "failure_points_consistency": not mismatch,
        "rubber_stamp_red_flags": red_flags,
    }


def compute_enrichment_diagnostics(
    enrichments: list[dict[str, Any]],
) -> dict[str, Any]:
    count = len(enrichments)
    return {
        "enriched_count": count,
        "avg_confounders_per_hypothesis": (
            sum(len(item["possible_confounders"]) for item in enrichments) / count
            if count
            else 0.0
        ),
        "avg_control_variables_per_hypothesis": (
            sum(len(item["control_variables"]) for item in enrichments) / count
            if count
            else 0.0
        ),
        "avg_rival_explanations_per_hypothesis": (
            sum(len(item["rival_explanations"]) for item in enrichments) / count
            if count
            else 0.0
        ),
        "hypotheses_with_effect_size_expectation": sum(
            bool(item["effect_size_expectation"].strip()) for item in enrichments
        ),
    }


def run_pipeline(
    call_llm: LLMCaller,
    model: str = DEFAULT_MODEL,
    research_question: str = RESEARCH_QUESTION,
) -> dict[str, Any]:
    """Run the legacy v2 intake-to-filter path for calibration compatibility."""
    hypotheses = validate_hypotheses(call_llm(dreamer_prompt(research_question)))
    audits = validate_audits(call_llm(auditor_prompt(research_question, hypotheses)), hypotheses)
    diagnostics = compute_diagnostics(audits, len(hypotheses))

    pass_ids = {
        audit["hypothesis_id"] for audit in audits if audit["audit_decision"] == "PASS"
    }
    pass_hypotheses = [
        hypothesis for hypothesis in hypotheses if hypothesis["hypothesis_id"] in pass_ids
    ]

    if pass_hypotheses:
        rivals = validate_pass_stage(
            call_llm(rival_prompt(research_question, pass_hypotheses)),
            "rival_prediction_matrix",
            RIVAL_FIELDS,
            pass_ids,
            "Stage 6",
        )
        falsification_tests = validate_pass_stage(
            call_llm(falsification_prompt(research_question, pass_hypotheses)),
            "falsification_tests",
            FALSIFICATION_FIELDS,
            pass_ids,
            "Stage 7",
        )
    else:
        rivals = []
        falsification_tests = []

    return {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": research_question,
        "model": model,
        "stage_4_hypotheses": hypotheses,
        "stage_5_audits": audits,
        "diagnostics": diagnostics,
        "stage_6_rival_prediction_matrix": rivals,
        "stage_7_falsification_tests": falsification_tests,
    }


def run_enriched_pipeline(
    call_llm: LLMCaller,
    model: str = DEFAULT_MODEL,
    research_question: str = RESEARCH_QUESTION,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run v3 contract enrichment before the unchanged strict mechanism filter."""
    stage_4_payload = _read_checkpoint(checkpoint_dir, "stage_4.json")
    if stage_4_payload is None:
        stage_4_payload = call_llm(dreamer_prompt(research_question))
    hypotheses = validate_hypotheses(stage_4_payload)
    _write_checkpoint(checkpoint_dir, "stage_4.json", {"hypotheses": hypotheses})

    stage_4_5_payload = _read_checkpoint(checkpoint_dir, "stage_4_5.json")
    if stage_4_5_payload is None:
        stage_4_5_payload = call_llm(
            confounder_enrichment_prompt(research_question, hypotheses)
        )
    enrichments = validate_enrichments(stage_4_5_payload, hypotheses)
    _write_checkpoint(
        checkpoint_dir,
        "stage_4_5.json",
        {"enriched_hypotheses": enrichments},
    )

    stage_5_payload = _read_checkpoint(checkpoint_dir, "stage_5.json")
    if stage_5_payload is None:
        stage_5_payload = call_llm(
            auditor_prompt(
                research_question,
                enrichments,
                input_description="Stage 4.5 enriched hypotheses",
            )
        )
    audits = validate_audits(stage_5_payload, hypotheses)
    _write_checkpoint(checkpoint_dir, "stage_5.json", {"audits": audits})
    diagnostics = compute_diagnostics(audits, len(hypotheses))
    diagnostics.update(compute_enrichment_diagnostics(enrichments))

    pass_ids = {
        audit["hypothesis_id"] for audit in audits if audit["audit_decision"] == "PASS"
    }
    pass_enrichments = [
        enrichment
        for enrichment in enrichments
        if enrichment["hypothesis_id"] in pass_ids
    ]

    if pass_enrichments:
        stage_6_payload = _read_checkpoint(checkpoint_dir, "stage_6.json")
        if stage_6_payload is None:
            stage_6_payload = call_llm(rival_prompt(research_question, pass_enrichments))
        rivals = validate_pass_stage(
            stage_6_payload,
            "rival_prediction_matrix",
            RIVAL_FIELDS,
            pass_ids,
            "Stage 6",
        )
        _write_checkpoint(
            checkpoint_dir,
            "stage_6.json",
            {"rival_prediction_matrix": rivals},
        )
        stage_7_payload = _read_checkpoint(checkpoint_dir, "stage_7.json")
        if stage_7_payload is None:
            stage_7_payload = call_llm(
                falsification_prompt(research_question, pass_enrichments)
            )
        falsification_tests = validate_pass_stage(
            stage_7_payload,
            "falsification_tests",
            FALSIFICATION_FIELDS,
            pass_ids,
            "Stage 7",
        )
        _write_checkpoint(
            checkpoint_dir,
            "stage_7.json",
            {"falsification_tests": falsification_tests},
        )
    else:
        rivals = []
        falsification_tests = []

    return {
        "experiment_name": EXPERIMENT_2_NAME,
        "version": "v3_enriched",
        "research_question": research_question,
        "model": model,
        "stage_4_hypotheses": hypotheses,
        "stage_4_5_confounder_enrichment": enrichments,
        "stage_5_audits": audits,
        "diagnostics": diagnostics,
        "stage_6_rival_prediction_matrix": rivals,
        "stage_7_falsification_tests": falsification_tests,
    }


def compute_v4_builder_diagnostics(
    mechanism_builds: list[dict[str, Any]],
    confounder_rival_builds: list[dict[str, Any]],
    statistical_builds: list[dict[str, Any]],
) -> dict[str, Any]:
    count = len(mechanism_builds)
    return {
        "mechanism_builder_count": count,
        "confounder_rival_builder_count": len(confounder_rival_builds),
        "statistical_testability_builder_count": len(statistical_builds),
        "avg_mechanism_variables_per_hypothesis": (
            sum(len(item["mechanism_variables"]) for item in mechanism_builds) / count
            if count
            else 0.0
        ),
        "avg_confounders_per_hypothesis": (
            sum(len(item["possible_confounders"]) for item in confounder_rival_builds)
            / len(confounder_rival_builds)
            if confounder_rival_builds
            else 0.0
        ),
        "avg_rivals_per_hypothesis": (
            sum(len(item["boring_rival_explanations"]) for item in confounder_rival_builds)
            / len(confounder_rival_builds)
            if confounder_rival_builds
            else 0.0
        ),
        "hypotheses_with_effect_size_expectation": sum(
            item["effect_size_expectation"] in {"small", "medium", "large", "unknown"}
            for item in statistical_builds
        ),
        "hypotheses_with_failure_condition": sum(
            bool(item["failure_condition"].strip()) for item in statistical_builds
        ),
        "hypotheses_with_testable_prediction": sum(
            bool(item["testable_prediction"].strip()) for item in statistical_builds
        ),
    }


def run_v4_pipeline(
    call_llm: LLMCaller,
    stage_4_payload: dict[str, Any] | None = None,
    model: str = DEFAULT_MODEL,
    research_question: str = RESEARCH_QUESTION,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run v4 contract normalization through strict filtering and falsification."""
    checkpoint_stage_4 = _read_checkpoint(checkpoint_dir, "stage_4.json")
    if checkpoint_stage_4 is not None:
        hypotheses = validate_hypotheses(checkpoint_stage_4)
        if stage_4_payload is not None:
            source_hypotheses = validate_hypotheses(stage_4_payload)
            if hypotheses != source_hypotheses:
                raise ValueError(
                    "v4 Stage 4 checkpoint does not match the supplied Dreamer output."
                )
    elif stage_4_payload is not None:
        hypotheses = validate_hypotheses(stage_4_payload)
    else:
        hypotheses = validate_hypotheses(call_llm(dreamer_prompt(research_question)))
    _write_checkpoint(checkpoint_dir, "stage_4.json", {"hypotheses": hypotheses})

    mechanism_payload = _read_checkpoint(checkpoint_dir, "stage_4_1.json")
    if mechanism_payload is None:
        mechanism_payload = call_llm(mechanism_builder_prompt(research_question, hypotheses))
    mechanism_builds = validate_mechanism_builds(mechanism_payload, hypotheses)
    _write_checkpoint(
        checkpoint_dir, "stage_4_1.json", {"mechanism_builds": mechanism_builds}
    )

    confounder_payload = _read_checkpoint(checkpoint_dir, "stage_4_2.json")
    if confounder_payload is None:
        confounder_payload = call_llm(
            confounder_rival_builder_prompt(
                research_question, hypotheses, mechanism_builds
            )
        )
    confounder_builds = validate_confounder_rival_builds(
        confounder_payload, hypotheses
    )
    _write_checkpoint(
        checkpoint_dir,
        "stage_4_2.json",
        {"confounder_rival_builds": confounder_builds},
    )

    statistical_payload = _read_checkpoint(checkpoint_dir, "stage_4_3.json")
    if statistical_payload is not None:
        statistical_builds = validate_statistical_testability_builds(
            statistical_payload, hypotheses
        )
    else:
        try:
            statistical_payload = call_llm(
                statistical_testability_builder_prompt(
                    research_question,
                    hypotheses,
                    mechanism_builds,
                    confounder_builds,
                )
            )
            statistical_builds = validate_statistical_testability_builds(
                statistical_payload, hypotheses
            )
        except Exception as exc:
            print(
                f"Stage 4.3 full-batch attempt failed safely ({type(exc).__name__}); "
                "resuming with H1-H5 and H6-H10 batches.",
                flush=True,
            )
            mechanism_by_id_for_batch = {
                item["hypothesis_id"]: item for item in mechanism_builds
            }
            confounder_by_id_for_batch = {
                item["hypothesis_id"]: item for item in confounder_builds
            }
            statistical_builds = []
            for batch_name, batch_hypotheses in (
                ("batch_a", hypotheses[:5]),
                ("batch_b", hypotheses[5:]),
            ):
                batch_filename = f"stage_4_3_{batch_name}.json"
                batch_payload = _read_checkpoint(checkpoint_dir, batch_filename)
                if batch_payload is None:
                    batch_ids = {
                        item["hypothesis_id"] for item in batch_hypotheses
                    }
                    batch_payload = call_llm(
                        statistical_testability_builder_prompt(
                            research_question,
                            batch_hypotheses,
                            [
                                mechanism_by_id_for_batch[hypothesis_id]
                                for hypothesis_id in (
                                    item["hypothesis_id"] for item in batch_hypotheses
                                )
                            ],
                            [
                                confounder_by_id_for_batch[hypothesis_id]
                                for hypothesis_id in (
                                    item["hypothesis_id"] for item in batch_hypotheses
                                )
                            ],
                        )
                    )
                    batch_rows = validate_statistical_testability_builds(
                        batch_payload, batch_hypotheses
                    )
                    if {item["hypothesis_id"] for item in batch_rows} != batch_ids:
                        raise ValueError(
                            f"Stage 4.3 {batch_name} returned mismatched IDs."
                        )
                    _write_checkpoint(
                        checkpoint_dir,
                        batch_filename,
                        {"statistical_testability_builds": batch_rows},
                    )
                else:
                    batch_rows = validate_statistical_testability_builds(
                        batch_payload, batch_hypotheses
                    )
                statistical_builds.extend(batch_rows)
            statistical_builds = validate_statistical_testability_builds(
                {"statistical_testability_builds": statistical_builds}, hypotheses
            )
    _write_checkpoint(
        checkpoint_dir,
        "stage_4_3.json",
        {"statistical_testability_builds": statistical_builds},
    )

    mechanism_by_id = {item["hypothesis_id"]: item for item in mechanism_builds}
    confounder_by_id = {item["hypothesis_id"]: item for item in confounder_builds}
    statistical_by_id = {item["hypothesis_id"]: item for item in statistical_builds}
    fully_built = [
        {
            **hypothesis,
            "mechanism_builder": mechanism_by_id[hypothesis["hypothesis_id"]],
            "confounder_rival_builder": confounder_by_id[hypothesis["hypothesis_id"]],
            "statistical_testability_builder": statistical_by_id[
                hypothesis["hypothesis_id"]
            ],
        }
        for hypothesis in hypotheses
    ]

    audit_payload = _read_checkpoint(checkpoint_dir, "stage_5.json")
    if audit_payload is None:
        audit_payload = call_llm(
            auditor_prompt(
                research_question,
                fully_built,
                input_description=(
                    "Fully built v4 hypotheses containing Stage 4, Mechanism Builder, "
                    "Confounder/Rival Builder, and Statistical Testability Builder outputs"
                ),
            )
        )
    audits = validate_audits(audit_payload, hypotheses)
    _write_checkpoint(checkpoint_dir, "stage_5.json", {"audits": audits})
    diagnostics = compute_diagnostics(audits, len(hypotheses))
    diagnostics.update(
        compute_v4_builder_diagnostics(
            mechanism_builds, confounder_builds, statistical_builds
        )
    )

    pass_ids = {
        audit["hypothesis_id"]
        for audit in audits
        if audit["audit_decision"] == "PASS"
    }
    pass_hypotheses = [
        item for item in fully_built if item["hypothesis_id"] in pass_ids
    ]
    if pass_hypotheses:
        rival_payload = _read_checkpoint(checkpoint_dir, "stage_6.json")
        if rival_payload is None:
            rival_payload = call_llm(rival_prompt(research_question, pass_hypotheses))
        rivals = validate_pass_stage(
            rival_payload,
            "rival_prediction_matrix",
            RIVAL_FIELDS,
            pass_ids,
            "Stage 6",
        )
        _write_checkpoint(
            checkpoint_dir, "stage_6.json", {"rival_prediction_matrix": rivals}
        )
        falsification_payload = _read_checkpoint(checkpoint_dir, "stage_7.json")
        if falsification_payload is None:
            falsification_payload = call_llm(
                falsification_prompt(research_question, pass_hypotheses)
            )
        falsification_tests = validate_pass_stage(
            falsification_payload,
            "falsification_tests",
            FALSIFICATION_FIELDS,
            pass_ids,
            "Stage 7",
        )
        _write_checkpoint(
            checkpoint_dir,
            "stage_7.json",
            {"falsification_tests": falsification_tests},
        )
    else:
        rivals = []
        falsification_tests = []

    return validate_v4_report(
        {
            "experiment_name": EXPERIMENT_7_NAME,
            "version": "v4_mechanism_confounder_testability",
            "research_question": research_question,
            "model": model,
            "stage_4_hypotheses": hypotheses,
            "stage_4_1_mechanism_builder": mechanism_builds,
            "stage_4_2_confounder_rival_builder": confounder_builds,
            "stage_4_3_statistical_testability_builder": statistical_builds,
            "stage_5_audits": audits,
            "diagnostics": diagnostics,
            "stage_6_rival_prediction_matrix": rivals,
            "stage_7_falsification_tests": falsification_tests,
        }
    )


def run_cross_question_analysis_stage(
    call_llm: LLMCaller,
    survivors: list[dict[str, Any]],
    pass_references: set[tuple[str, str]],
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Run and validate the Experiment 3 combined survivor synthesis."""
    payload = _read_checkpoint(checkpoint_dir, "combined_analysis.json")
    if payload is None:
        payload = call_llm(cross_question_survivor_prompt(survivors))
    analysis = validate_cross_question_analysis(payload, pass_references)
    _write_checkpoint(
        checkpoint_dir,
        "combined_analysis.json",
        {"combined_analysis": analysis},
    )
    return analysis


def run_pattern_falsification_stage(
    call_llm: LLMCaller,
    working_theory: dict[str, Any],
    literature_sources: list[dict[str, Any]],
    patterns_by_id: dict[str, dict[str, Any]],
    pass_references: set[tuple[str, str]],
    valid_citation_ids: set[str],
    checkpoint_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Run and validate the Experiment 4 pattern falsification stage."""
    payload = _read_checkpoint(checkpoint_dir, "pattern_falsification_studies.json")
    if payload is None:
        payload = call_llm(
            pattern_falsification_prompt(working_theory, literature_sources)
        )
    studies = validate_pattern_falsification_studies(
        payload,
        patterns_by_id,
        pass_references,
        valid_citation_ids,
    )
    _write_checkpoint(
        checkpoint_dir,
        "pattern_falsification_studies.json",
        {"pattern_falsification_studies": studies},
    )
    return studies


P4_F2_CONDITIONS = (
    "well_separated_gaussian_clusters",
    "overlapping_gaussian_clusters",
    "imbalanced_class_geometry",
    "sparse_subgroup_geometry",
    "covariate_shifted_test_geometry",
)
P4_F2_SCORES = (
    "margin_score",
    "inverse_probability_score",
    "distance_to_class_centroid_score",
)
P4_F2_CONDITIONING = ("marginal", "mondrian_class")


def _correlated_covariance(scale: float, correlation: float, dimension: int) -> np.ndarray:
    covariance = np.full((dimension, dimension), correlation * scale, dtype=float)
    np.fill_diagonal(covariance, scale)
    return covariance


def _generate_geometry(
    condition: str,
    sample_count: int,
    rng: np.random.Generator,
    split: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dimension = 6
    if condition == "imbalanced_class_geometry":
        priors = np.array([0.75, 0.20, 0.05])
    else:
        priors = np.array([1 / 3, 1 / 3, 1 / 3])
    labels = rng.choice(3, size=sample_count, p=priors)

    if condition == "well_separated_gaussian_clusters":
        means = np.array(
            [[-3.0, 0, 0, 0, 0, 0], [3.0, 0, 0, 0, 0, 0], [0, 3.0, 0, 0, 0, 0]]
        )
        covariance = _correlated_covariance(0.7, 0.15, dimension)
        features = np.vstack(
            [rng.multivariate_normal(means[label], covariance) for label in labels]
        )
        edge = rng.random(sample_count) < 0.20
        features[edge, 2] += rng.normal(1.0, 0.25, edge.sum())
        subgroups = np.where(edge, "edge_region", "core_region")
    elif condition == "overlapping_gaussian_clusters":
        means = np.array(
            [[-0.8, 0, 0, 0, 0, 0], [0.8, 0, 0, 0, 0, 0], [0, 0.8, 0, 0, 0, 0]]
        )
        covariance = _correlated_covariance(1.5, 0.30, dimension)
        features = np.vstack(
            [rng.multivariate_normal(means[label], covariance) for label in labels]
        )
        component = rng.random(sample_count) < 0.5
        features[:, 2] += np.where(component, 0.9, -0.9)
        subgroups = np.where(component, "overlap_component_a", "overlap_component_b")
    elif condition == "imbalanced_class_geometry":
        means = np.array(
            [[-2.0, 0, 0, 0, 0, 0], [2.0, 0, 0, 0, 0, 0], [0, 2.0, 0, 0, 0, 0]]
        )
        covariance_by_class = [
            _correlated_covariance(0.8, 0.15, dimension),
            _correlated_covariance(1.1, 0.25, dimension),
            _correlated_covariance(1.8, 0.35, dimension),
        ]
        features = np.vstack(
            [
                rng.multivariate_normal(means[label], covariance_by_class[label])
                for label in labels
            ]
        )
        subgroups = np.where(labels == 0, "majority_region", "minority_region")
    elif condition == "sparse_subgroup_geometry":
        means = np.array(
            [[-2.2, 0, 0, 0, 0, 0], [2.2, 0, 0, 0, 0, 0], [0, 2.2, 0, 0, 0, 0]]
        )
        covariance = _correlated_covariance(0.9, 0.20, dimension)
        features = np.vstack(
            [rng.multivariate_normal(means[label], covariance) for label in labels]
        )
        sparse = rng.random(sample_count) < 0.08
        sparse_shift = np.array(
            [[2.0, 2.5, 0, 0, 0, 0], [-2.0, 2.5, 0, 0, 0, 0], [0, -3.0, 0, 0, 0, 0]]
        )
        features[sparse] += sparse_shift[labels[sparse]]
        features[sparse] += rng.normal(0, 0.8, size=(sparse.sum(), dimension))
        subgroups = np.where(sparse, "sparse_subgroup", "common_subgroup")
    elif condition == "covariate_shifted_test_geometry":
        means = np.array(
            [[-2.0, 0, 0, 0, 0, 0], [2.0, 0, 0, 0, 0, 0], [0, 2.0, 0, 0, 0, 0]]
        )
        covariance = _correlated_covariance(0.9, 0.20, dimension)
        features = np.vstack(
            [rng.multivariate_normal(means[label], covariance) for label in labels]
        )
        shifted = rng.random(sample_count) < (0.50 if split == "test" else 0.0)
        shift_vectors = np.array(
            [[1.5, 1.0, 0.5, 0, 0, 0], [-1.5, 1.0, -0.5, 0, 0, 0], [0, -1.8, 0.7, 0, 0, 0]]
        )
        features[shifted] += shift_vectors[labels[shifted]]
        subgroups = np.where(shifted, "shifted_region", "stable_region")
    else:
        raise ValueError(f"Unknown synthetic condition: {condition}")
    return features.astype(float), labels.astype(int), subgroups.astype(str)


def _fit_regularized_lda(
    features: np.ndarray,
    labels: np.ndarray,
) -> dict[str, np.ndarray]:
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-8] = 1.0
    standardized = (features - mean) / scale
    centroids = np.vstack([standardized[labels == label].mean(axis=0) for label in range(3)])
    residuals = standardized - centroids[labels]
    covariance = residuals.T @ residuals / max(1, len(features) - 3)
    covariance += 0.15 * np.eye(features.shape[1])
    inverse_covariance = np.linalg.pinv(covariance)
    priors = np.array([(labels == label).mean() for label in range(3)])
    priors = np.clip(priors, 1e-8, 1.0)
    return {
        "mean": mean,
        "scale": scale,
        "centroids": centroids,
        "inverse_covariance": inverse_covariance,
        "log_priors": np.log(priors),
    }


def _model_outputs(
    model: dict[str, np.ndarray],
    features: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    standardized = (features - model["mean"]) / model["scale"]
    differences = standardized[:, None, :] - model["centroids"][None, :, :]
    mahalanobis_squared = np.einsum(
        "nkd,df,nkf->nk",
        differences,
        model["inverse_covariance"],
        differences,
    )
    logits = -0.5 * mahalanobis_squared + model["log_priors"][None, :]
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    centroid_distances = np.linalg.norm(differences, axis=2)
    return probabilities, centroid_distances


def _score_matrix(
    score_type: str,
    probabilities: np.ndarray,
    centroid_distances: np.ndarray,
) -> np.ndarray:
    if score_type == "inverse_probability_score":
        return 1.0 - probabilities
    if score_type == "margin_score":
        result = np.empty_like(probabilities)
        for label in range(probabilities.shape[1]):
            other = np.max(np.delete(probabilities, label, axis=1), axis=1)
            result[:, label] = other - probabilities[:, label]
        return result
    if score_type == "distance_to_class_centroid_score":
        return centroid_distances
    raise ValueError(f"Unknown score type: {score_type}")


def _conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return float("inf")
    rank = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    if rank > len(scores):
        return float("inf")
    return float(np.partition(scores, rank - 1)[rank - 1])


def _coverage_by_group(
    covered: np.ndarray,
    groups: np.ndarray,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for group in sorted(np.unique(groups).tolist(), key=str):
        mask = groups == group
        result[str(group)] = float(covered[mask].mean())
    return result


def _evaluate_prediction_sets(
    calibration_scores: np.ndarray,
    calibration_labels: np.ndarray,
    test_scores: np.ndarray,
    test_labels: np.ndarray,
    test_subgroups: np.ndarray,
    conditioning_strategy: str,
    alpha: float,
) -> dict[str, Any]:
    true_calibration_scores = calibration_scores[
        np.arange(len(calibration_labels)), calibration_labels
    ]
    if conditioning_strategy == "marginal":
        threshold = _conformal_quantile(true_calibration_scores, alpha)
        thresholds = np.full(3, threshold)
    elif conditioning_strategy == "mondrian_class":
        thresholds = np.array(
            [
                _conformal_quantile(
                    true_calibration_scores[calibration_labels == label],
                    alpha,
                )
                for label in range(3)
            ]
        )
    else:
        raise ValueError(f"Unknown conditioning strategy: {conditioning_strategy}")
    prediction_sets = test_scores <= thresholds[None, :]
    covered = prediction_sets[np.arange(len(test_labels)), test_labels]
    by_class = _coverage_by_group(covered, test_labels)
    by_class = {f"class_{key}": value for key, value in by_class.items()}
    by_subgroup = _coverage_by_group(covered, test_subgroups)
    group_coverages = list(by_class.values()) + list(by_subgroup.values())
    target = 1 - alpha
    return {
        "marginal_coverage": float(covered.mean()),
        "conditional_coverage_by_class": by_class,
        "conditional_coverage_by_subgroup_or_region": by_subgroup,
        "coverage_gap": float(max(abs(value - target) for value in group_coverages)),
        "minimum_group_coverage": float(min(group_coverages)),
        "average_set_size": float(prediction_sets.sum(axis=1).mean()),
        "undercoverage_rate": float(
            sum(value < target for value in group_coverages) / len(group_coverages)
        ),
    }


def run_p4_f2_simulation(
    calibration_sizes: tuple[int, ...] = (50, 100, 300),
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    alpha: float = 0.10,
    train_size: int = 2000,
    test_size: int = 4000,
) -> list[dict[str, Any]]:
    """Run the deterministic seed-level P4-F2 simulation grid."""
    results: list[dict[str, Any]] = []
    max_calibration = max(calibration_sizes)
    for condition_index, condition in enumerate(P4_F2_CONDITIONS):
        for seed in seeds:
            base = condition_index * 10000 + seed * 100
            train = _generate_geometry(
                condition,
                train_size,
                np.random.default_rng(base + 11),
                "train",
            )
            calibration = _generate_geometry(
                condition,
                max_calibration,
                np.random.default_rng(base + 23),
                "calibration",
            )
            test = _generate_geometry(
                condition,
                test_size,
                np.random.default_rng(base + 37),
                "test",
            )
            model = _fit_regularized_lda(train[0], train[1])
            calibration_probabilities, calibration_distances = _model_outputs(
                model,
                calibration[0],
            )
            test_probabilities, test_distances = _model_outputs(model, test[0])
            for score_type in P4_F2_SCORES:
                full_calibration_scores = _score_matrix(
                    score_type,
                    calibration_probabilities,
                    calibration_distances,
                )
                test_scores = _score_matrix(
                    score_type,
                    test_probabilities,
                    test_distances,
                )
                for calibration_size in calibration_sizes:
                    calibration_scores = full_calibration_scores[:calibration_size]
                    calibration_labels = calibration[1][:calibration_size]
                    for conditioning_strategy in P4_F2_CONDITIONING:
                        metrics = _evaluate_prediction_sets(
                            calibration_scores,
                            calibration_labels,
                            test_scores,
                            test[1],
                            test[2],
                            conditioning_strategy,
                            alpha,
                        )
                        results.append(
                            {
                                "condition": condition,
                                "score_type": score_type,
                                "conditioning_strategy": conditioning_strategy,
                                "calibration_size": calibration_size,
                                "seed": seed,
                                **metrics,
                            }
                        )
    return results


def _mean_mapping(rows: list[dict[str, Any]], field: str) -> dict[str, float]:
    keys = sorted({key for row in rows for key in row[field]})
    return {
        key: float(np.mean([row[field][key] for row in rows if key in row[field]]))
        for key in keys
    }


def aggregate_p4_f2_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate seed-level metrics for each design cell."""
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in results:
        key = (
            row["condition"],
            row["score_type"],
            row["conditioning_strategy"],
            row["calibration_size"],
        )
        grouped.setdefault(key, []).append(row)
    aggregates: list[dict[str, Any]] = []
    for key in sorted(grouped, key=lambda value: (P4_F2_CONDITIONS.index(value[0]), P4_F2_SCORES.index(value[1]), P4_F2_CONDITIONING.index(value[2]), value[3])):
        rows = grouped[key]
        numeric_fields = (
            "marginal_coverage",
            "coverage_gap",
            "minimum_group_coverage",
            "average_set_size",
            "undercoverage_rate",
        )
        aggregate: dict[str, Any] = {
            "condition": key[0],
            "score_type": key[1],
            "conditioning_strategy": key[2],
            "calibration_size": key[3],
            "seed_count": len(rows),
        }
        for field in numeric_fields:
            values = np.array([row[field] for row in rows], dtype=float)
            aggregate[f"mean_{field}"] = float(values.mean())
            aggregate[f"std_{field}"] = float(values.std(ddof=0))
        aggregate["mean_conditional_coverage_by_class"] = _mean_mapping(
            rows,
            "conditional_coverage_by_class",
        )
        aggregate["mean_conditional_coverage_by_subgroup_or_region"] = _mean_mapping(
            rows,
            "conditional_coverage_by_subgroup_or_region",
        )
        aggregate["severe_undercoverage_seed_fraction"] = float(
            np.mean([row["minimum_group_coverage"] < 0.85 for row in rows])
        )
        aggregates.append(aggregate)
    return aggregates


def assess_p4_survival(
    results: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply preregistered deterministic P4 survival rules."""
    mean_gap_by_size = {
        size: float(
            np.mean(
                [
                    row["mean_coverage_gap"]
                    for row in aggregates
                    if row["calibration_size"] == size
                ]
            )
        )
        for size in (50, 100, 300)
    }
    gap_reduction = (
        (mean_gap_by_size[50] - mean_gap_by_size[300]) / mean_gap_by_size[50]
        if mean_gap_by_size[50] > 0
        else 0.0
    )

    def sensitivity(size: int, varying: str) -> float:
        group_fields = (
            ("condition", "conditioning_strategy")
            if varying == "score"
            else ("condition", "score_type")
        )
        groups: dict[tuple[str, str], list[float]] = {}
        for row in aggregates:
            if row["calibration_size"] == size:
                group_key = tuple(str(row[field]) for field in group_fields)
                groups.setdefault(group_key, []).append(row["mean_coverage_gap"])
        return float(np.mean([max(values) - min(values) for values in groups.values()]))

    sensitivity_50 = np.mean([sensitivity(50, "score"), sensitivity(50, "conditioning")])
    sensitivity_300 = np.mean(
        [sensitivity(300, "score"), sensitivity(300, "conditioning")]
    )
    sensitivity_reduction = (
        float((sensitivity_50 - sensitivity_300) / sensitivity_50)
        if sensitivity_50 > 0
        else 0.0
    )

    trajectories: list[dict[str, Any]] = []
    for condition in P4_F2_CONDITIONS:
        for score_type in P4_F2_SCORES:
            for strategy in P4_F2_CONDITIONING:
                cells = {
                    row["calibration_size"]: row
                    for row in aggregates
                    if row["condition"] == condition
                    and row["score_type"] == score_type
                    and row["conditioning_strategy"] == strategy
                }
                reduction = cells[50]["mean_coverage_gap"] - cells[300]["mean_coverage_gap"]
                trajectories.append(
                    {
                        "condition": condition,
                        "score_type": score_type,
                        "conditioning_strategy": strategy,
                        "gap_50": cells[50]["mean_coverage_gap"],
                        "gap_300": cells[300]["mean_coverage_gap"],
                        "gap_reduction": reduction,
                        "min_coverage_300": cells[300]["mean_minimum_group_coverage"],
                        "severe_fraction_300": cells[300][
                            "severe_undercoverage_seed_fraction"
                        ],
                    }
                )
    strongest_support = max(trajectories, key=lambda item: item["gap_reduction"])
    strongest_failure = max(trajectories, key=lambda item: item["gap_300"])

    persistent_all_sizes = []
    for trajectory in trajectories:
        matching = [
            row
            for row in results
            if row["condition"] == trajectory["condition"]
            and row["score_type"] == trajectory["score_type"]
            and row["conditioning_strategy"] == trajectory["conditioning_strategy"]
        ]
        severe_by_size = {
            size: sum(
                row["minimum_group_coverage"] < 0.80
                for row in matching
                if row["calibration_size"] == size
            )
            / 5
            for size in (50, 100, 300)
        }
        if all(fraction >= 0.8 for fraction in severe_by_size.values()):
            persistent_all_sizes.append({**trajectory, "severe_by_size": severe_by_size})

    large_n_persistent = [
        item
        for item in trajectories
        if item["gap_300"] >= 0.08
        and item["min_coverage_300"] < 0.85
        and item["severe_fraction_300"] >= 0.8
    ]
    if persistent_all_sizes:
        status = "FALSIFIED"
        rationale = (
            "At least one controlled geometry/score/conditioning cell showed severe group undercoverage "
            "in at least four of five seeds at every calibration size, so finite-sample variance alone "
            "cannot explain the failure."
        )
    elif large_n_persistent:
        status = "WEAKENED"
        rationale = (
            "Coverage gaps persisted at n_calib=300 for at least one score/geometry cell across most "
            "seeds, indicating residual structural sensitivity beyond small-sample instability."
        )
    elif gap_reduction >= 0.20 and sensitivity_reduction >= 0.30:
        status = "SURVIVES"
        rationale = (
            "Mean coverage gaps and score/conditioning sensitivity fell materially as calibration size "
            "increased, with no persistent large-n failure cell; most failures are consistent with "
            "finite-sample instability."
        )
    else:
        status = "INCONCLUSIVE"
        rationale = (
            "The calibration-size trend was not strong enough to establish finite-sample dominance, but "
            "no failure met the preregistered persistent-undercoverage threshold."
        )
    return {
        "status": status,
        "rationale": rationale,
        "strongest_failure_case": (
            f"{strongest_failure['condition']} / {strongest_failure['score_type']} / "
            f"{strongest_failure['conditioning_strategy']}: mean n=300 coverage gap "
            f"{strongest_failure['gap_300']:.4f}, mean minimum group coverage "
            f"{strongest_failure['min_coverage_300']:.4f}."
        ),
        "strongest_support_case": (
            f"{strongest_support['condition']} / {strongest_support['score_type']} / "
            f"{strongest_support['conditioning_strategy']}: mean coverage gap fell from "
            f"{strongest_support['gap_50']:.4f} to {strongest_support['gap_300']:.4f} "
            f"(absolute reduction {strongest_support['gap_reduction']:.4f})."
        ),
        "decision_metrics": {
            "mean_coverage_gap_by_calibration_size": mean_gap_by_size,
            "relative_mean_gap_reduction_50_to_300": float(gap_reduction),
            "combined_score_conditioning_sensitivity_n50": float(sensitivity_50),
            "combined_score_conditioning_sensitivity_n300": float(sensitivity_300),
            "relative_sensitivity_reduction_50_to_300": float(sensitivity_reduction),
            "persistent_failure_cell_count_all_sizes": len(persistent_all_sizes),
            "persistent_large_n_failure_cell_count": len(large_n_persistent),
        },
    }


P4_F1_CONDITIONS = P4_F2_CONDITIONS
P4_F1_SCORES = P4_F2_SCORES
P4_F1_CONDITIONING = ("marginal", "mondrian_class", "mondrian_region")


def _evaluate_p4_f1_prediction_sets(
    calibration_scores: np.ndarray,
    calibration_labels: np.ndarray,
    calibration_regions: np.ndarray,
    test_scores: np.ndarray,
    test_labels: np.ndarray,
    test_regions: np.ndarray,
    conditioning_strategy: str,
    alpha: float,
) -> dict[str, Any]:
    """Evaluate prediction sets, including observable region-Mondrian strata."""
    true_calibration_scores = calibration_scores[
        np.arange(len(calibration_labels)), calibration_labels
    ]
    if conditioning_strategy == "marginal":
        threshold = _conformal_quantile(true_calibration_scores, alpha)
        prediction_sets = test_scores <= threshold
    elif conditioning_strategy == "mondrian_class":
        thresholds = np.array(
            [
                _conformal_quantile(
                    true_calibration_scores[calibration_labels == label],
                    alpha,
                )
                for label in range(3)
            ]
        )
        prediction_sets = test_scores <= thresholds[None, :]
    elif conditioning_strategy == "mondrian_region":
        thresholds_by_region = {
            str(region): _conformal_quantile(
                true_calibration_scores[calibration_regions == region],
                alpha,
            )
            for region in np.unique(calibration_regions)
        }
        row_thresholds = np.array(
            [thresholds_by_region.get(str(region), float("inf")) for region in test_regions]
        )
        prediction_sets = test_scores <= row_thresholds[:, None]
    else:
        raise ValueError(f"Unknown P4-F1 conditioning strategy: {conditioning_strategy}")

    covered = prediction_sets[np.arange(len(test_labels)), test_labels]
    by_class = {
        f"class_{key}": value
        for key, value in _coverage_by_group(covered, test_labels).items()
    }
    by_region = _coverage_by_group(covered, test_regions)
    group_coverages = list(by_class.values()) + list(by_region.values())
    target = 1 - alpha
    return {
        "marginal_coverage": float(covered.mean()),
        "conditional_coverage_by_class": by_class,
        "conditional_coverage_by_region_or_subgroup": by_region,
        "coverage_gap": float(max(abs(value - target) for value in group_coverages)),
        "minimum_group_coverage": float(min(group_coverages)),
        "average_set_size": float(prediction_sets.sum(axis=1).mean()),
        "undercoverage_rate": float(
            sum(value < target for value in group_coverages) / len(group_coverages)
        ),
    }


def run_p4_f1_simulation(
    calibration_sizes: tuple[int, ...] = (50, 100, 300, 600),
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    alpha: float = 0.10,
    train_size: int = 2000,
    test_size: int = 4000,
) -> list[dict[str, Any]]:
    """Run the deterministic 5x3x3x4x5 Experiment 6 grid."""
    results: list[dict[str, Any]] = []
    max_calibration = max(calibration_sizes)
    for condition_index, condition in enumerate(P4_F1_CONDITIONS):
        for seed in seeds:
            base = condition_index * 10000 + seed * 100
            train = _generate_geometry(
                condition, train_size, np.random.default_rng(base + 11), "train"
            )
            calibration = _generate_geometry(
                condition,
                max_calibration,
                np.random.default_rng(base + 23),
                "calibration",
            )
            test = _generate_geometry(
                condition, test_size, np.random.default_rng(base + 37), "test"
            )
            model = _fit_regularized_lda(train[0], train[1])
            calibration_probabilities, calibration_distances = _model_outputs(
                model, calibration[0]
            )
            test_probabilities, test_distances = _model_outputs(model, test[0])
            for score_type in P4_F1_SCORES:
                all_calibration_scores = _score_matrix(
                    score_type, calibration_probabilities, calibration_distances
                )
                test_scores = _score_matrix(
                    score_type, test_probabilities, test_distances
                )
                for calibration_size in calibration_sizes:
                    for conditioning_strategy in P4_F1_CONDITIONING:
                        metrics = _evaluate_p4_f1_prediction_sets(
                            all_calibration_scores[:calibration_size],
                            calibration[1][:calibration_size],
                            calibration[2][:calibration_size],
                            test_scores,
                            test[1],
                            test[2],
                            conditioning_strategy,
                            alpha,
                        )
                        results.append(
                            {
                                "condition": condition,
                                "score_type": score_type,
                                "conditioning_strategy": conditioning_strategy,
                                "calibration_size": calibration_size,
                                "seed": seed,
                                **metrics,
                            }
                        )
    return results


def aggregate_p4_f1_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate Experiment 6 seed-level results by complete design cell."""
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in results:
        key = (
            row["condition"],
            row["score_type"],
            row["conditioning_strategy"],
            row["calibration_size"],
        )
        grouped.setdefault(key, []).append(row)
    ordering = lambda key: (
        P4_F1_CONDITIONS.index(key[0]),
        P4_F1_SCORES.index(key[1]),
        P4_F1_CONDITIONING.index(key[2]),
        key[3],
    )
    aggregates: list[dict[str, Any]] = []
    for key in sorted(grouped, key=ordering):
        rows = grouped[key]
        aggregate: dict[str, Any] = {
            "condition": key[0],
            "score_type": key[1],
            "conditioning_strategy": key[2],
            "calibration_size": key[3],
            "seed_count": len(rows),
        }
        for field in (
            "marginal_coverage",
            "coverage_gap",
            "minimum_group_coverage",
            "average_set_size",
            "undercoverage_rate",
        ):
            values = np.array([row[field] for row in rows], dtype=float)
            aggregate[f"mean_{field}"] = float(values.mean())
            aggregate[f"std_{field}"] = float(values.std(ddof=0))
        aggregate["mean_conditional_coverage_by_class"] = _mean_mapping(
            rows, "conditional_coverage_by_class"
        )
        aggregate["mean_conditional_coverage_by_region_or_subgroup"] = _mean_mapping(
            rows, "conditional_coverage_by_region_or_subgroup"
        )
        aggregates.append(aggregate)
    return aggregates


def analyze_p4_f1_results(
    aggregates: list[dict[str, Any]],
    calibration_sizes: tuple[int, ...] = (50, 100, 300, 600),
) -> dict[str, Any]:
    """Build trends, rankings, core answers, and the deterministic P4 decision."""
    by_cell: dict[tuple[str, str, str], dict[int, dict[str, Any]]] = {}
    for row in aggregates:
        key = (row["condition"], row["score_type"], row["conditioning_strategy"])
        by_cell.setdefault(key, {})[row["calibration_size"]] = row

    trends: list[dict[str, Any]] = []
    for key in sorted(
        by_cell,
        key=lambda value: (
            P4_F1_CONDITIONS.index(value[0]),
            P4_F1_SCORES.index(value[1]),
            P4_F1_CONDITIONING.index(value[2]),
        ),
    ):
        rows = by_cell[key]
        large = rows[600]
        trend = {
            "condition": key[0],
            "score_type": key[1],
            "conditioning_strategy": key[2],
            "coverage_gap_at_50": rows[50]["mean_coverage_gap"],
            "coverage_gap_at_100": rows[100]["mean_coverage_gap"],
            "coverage_gap_at_300": rows[300]["mean_coverage_gap"],
            "coverage_gap_at_600": large["mean_coverage_gap"],
            "gap_reduction_from_50_to_600": (
                rows[50]["mean_coverage_gap"] - large["mean_coverage_gap"]
            ),
            "minimum_group_coverage_at_600": large["mean_minimum_group_coverage"],
            "average_set_size_at_600": large["mean_average_set_size"],
            "persistent_failure": bool(
                large["mean_coverage_gap"] > 0.15
                or large["mean_minimum_group_coverage"] < 0.75
            ),
        }
        trends.append(trend)

    large_rows = [row for row in aggregates if row["calibration_size"] == 600]

    def summarize(entity_type: str, fields: tuple[str, ...]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        for row in large_rows:
            key = tuple(str(row[field]) for field in fields)
            grouped.setdefault(key, []).append(row)
        summaries: list[dict[str, Any]] = []
        for key, rows in grouped.items():
            trend_matches = [
                trend
                for trend in trends
                if all(str(trend[field]) == value for field, value in zip(fields, key))
            ]
            summaries.append(
                {
                    "entity_type": entity_type,
                    "entity": " + ".join(key),
                    "mean_coverage_gap_at_600": float(
                        np.mean([row["mean_coverage_gap"] for row in rows])
                    ),
                    "mean_minimum_group_coverage_at_600": float(
                        np.mean([row["mean_minimum_group_coverage"] for row in rows])
                    ),
                    "mean_average_set_size_at_600": float(
                        np.mean([row["mean_average_set_size"] for row in rows])
                    ),
                    "persistent_failure_count": int(
                        sum(trend["persistent_failure"] for trend in trend_matches)
                    ),
                }
            )
        summaries.sort(
            key=lambda row: (
                row["persistent_failure_count"],
                row["mean_coverage_gap_at_600"],
                -row["mean_minimum_group_coverage_at_600"],
                row["mean_average_set_size_at_600"],
                row["entity"],
            )
        )
        for rank, row in enumerate(summaries, start=1):
            row["rank"] = rank
        return summaries

    score_ranking = summarize("score", ("score_type",))
    conditioning_ranking = summarize(
        "conditioning_strategy", ("conditioning_strategy",)
    )
    pair_ranking = summarize(
        "score_conditioning_pair", ("score_type", "conditioning_strategy")
    )
    geometry_ranking = summarize("geometry", ("condition",))
    ranking = score_ranking + conditioning_ranking + pair_ranking + geometry_ranking
    dangerous_pair = max(
        pair_ranking,
        key=lambda row: (
            row["persistent_failure_count"],
            row["mean_coverage_gap_at_600"],
            -row["mean_minimum_group_coverage_at_600"],
        ),
    )
    worst_geometry = max(
        geometry_ranking,
        key=lambda row: (
            row["persistent_failure_count"],
            row["mean_coverage_gap_at_600"],
            -row["mean_minimum_group_coverage_at_600"],
        ),
    )
    persistent = [trend for trend in trends if trend["persistent_failure"]]
    initial_failures = [
        trend
        for trend in trends
        if trend["coverage_gap_at_50"] > 0.15
        or min(
            row["mean_minimum_group_coverage"]
            for row in aggregates
            if row["condition"] == trend["condition"]
            and row["score_type"] == trend["score_type"]
            and row["conditioning_strategy"] == trend["conditioning_strategy"]
            and row["calibration_size"] == 50
        )
        < 0.75
    ]
    resolved_count = sum(not trend["persistent_failure"] for trend in initial_failures)
    mean_gap_by_size = {
        str(size): float(
            np.mean(
                [row["mean_coverage_gap"] for row in aggregates if row["calibration_size"] == size]
            )
        )
        for size in calibration_sizes
    }
    strongest_failure = max(
        trends,
        key=lambda row: (
            row["coverage_gap_at_600"],
            -row["minimum_group_coverage_at_600"],
        ),
    )
    strongest_size_effect = max(
        trends, key=lambda row: row["gap_reduction_from_50_to_600"]
    )
    if persistent:
        status = "STRUCTURAL_FAILURE_CONFIRMED"
        rationale = (
            f"{len(persistent)} of 45 score-conditioning-geometry cells retained a gap above "
            "0.15 or minimum group coverage below 0.75 at n_calib=600."
        )
    elif mean_gap_by_size["600"] < mean_gap_by_size["50"]:
        status = "PARTIALLY_SIZE_DEPENDENT"
        rationale = (
            "No design cell met the persistent-failure threshold and the mean gap declined with size."
        )
    else:
        status = "INCONCLUSIVE"
        rationale = "Neither persistent structural failure nor a consistent beneficial size trend was detected."

    calibration_effect = (
        f"Increasing n_calib resolved {resolved_count} of {len(initial_failures)} cells that met the "
        f"failure threshold at n=50; {len(persistent)} cells still failed at n=600. Mean gap changed "
        f"from {mean_gap_by_size['50']:.4f} to {mean_gap_by_size['600']:.4f}."
    )
    return {
        "trend_results": trends,
        "robustness_ranking": ranking,
        "persistent_failure_cases": persistent,
        "core_answers": {
            "most_robust_score": score_ranking[0]["entity"],
            "most_robust_conditioning_strategy": conditioning_ranking[0]["entity"],
            "worst_geometry": worst_geometry["entity"],
            "calibration_size_effect": calibration_effect,
            "most_dangerous_score_conditioning_pair": dangerous_pair["entity"],
            "safest_score_conditioning_pair": pair_ranking[0]["entity"],
        },
        "p4_followup_assessment": {
            "status": status,
            "rationale": rationale,
            "strongest_structural_failure_case": (
                f"{strongest_failure['condition']} / {strongest_failure['score_type']} / "
                f"{strongest_failure['conditioning_strategy']}: n=600 mean gap "
                f"{strongest_failure['coverage_gap_at_600']:.4f}, minimum group coverage "
                f"{strongest_failure['minimum_group_coverage_at_600']:.4f}."
            ),
            "strongest_size_effect_case": (
                f"{strongest_size_effect['condition']} / {strongest_size_effect['score_type']} / "
                f"{strongest_size_effect['conditioning_strategy']}: gap fell from "
                f"{strongest_size_effect['coverage_gap_at_50']:.4f} to "
                f"{strongest_size_effect['coverage_gap_at_600']:.4f} "
                f"(reduction {strongest_size_effect['gap_reduction_from_50_to_600']:.4f})."
            ),
        },
        "mean_coverage_gap_by_size": mean_gap_by_size,
        "initial_failure_count": len(initial_failures),
        "resolved_failure_count": resolved_count,
    }
