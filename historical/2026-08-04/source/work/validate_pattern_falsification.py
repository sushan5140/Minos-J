"""Deterministic Experiment 4 contract and checkpoint validation."""

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from pipeline import run_pattern_falsification_stage


pass_references = {
    (question, f"H{index}")
    for question in ("Q1", "Q2", "Q3")
    for index in range(1, 6)
}
patterns_by_id = {
    f"P{index}": {
        "pattern_id": f"P{index}",
        "pattern_name": f"Validated pattern {index}",
        "supporting_hypotheses": [
            {"source_question": "Q1", "hypothesis_id": f"H{index}"},
            {"source_question": "Q2", "hypothesis_id": f"H{index}"},
            {"source_question": "Q3", "hypothesis_id": f"H{index}"},
        ],
    }
    for index in range(1, 6)
}
valid_citation_ids = {f"L{index}" for index in range(1, 9)}


def experiment(pattern_index: int, experiment_index: int) -> dict:
    citation_start = ((pattern_index - 1) * 2 + experiment_index - 1) % 8 + 1
    return {
        "experiment_id": f"P{pattern_index}-F{experiment_index}",
        "title": "Controlled falsification test",
        "design": "A preregistered subject-held-out factorial ablation.",
        "meno_j_prediction": "Coverage changes conditionally under the pattern modifier.",
        "competing_explanation_prediction": "Coverage changes only with the rival nuisance variable.",
        "measurable_outcomes": ["Conditional coverage error", "prediction-set size"],
        "expected_effect_size": {
            "metric": "Absolute conditional coverage-error difference",
            "magnitude": "MEDIUM",
            "expected_direction": "Larger error under the working-theory boundary",
            "quantitative_target": "At least 0.05 absolute coverage difference",
            "rationale": "A smaller difference would be difficult to distinguish from split variability.",
        },
        "required_datasets_or_metadata": ["Wearable signals", "subject IDs", "segment metadata"],
        "implementation_difficulty": "MEDIUM",
        "difficulty_reason": "Requires harmonized metadata but no new sensor platform.",
        "failure_condition_for_working_theory": "The preregistered interaction is null with a narrow interval.",
        "supporting_hypothesis_refs": patterns_by_id[f"P{pattern_index}"][
            "supporting_hypotheses"
        ][:2],
        "literature_citation_ids": [f"L{citation_start}"],
        "scientific_impact_score": 4,
        "feasibility_score": 3,
        "publication_potential_score": 4,
        "information_gain_score": 5,
        "score_rationale": "The design directly distinguishes mechanisms with reusable methodology.",
    }


studies = [
    {
        "pattern_id": f"P{index}",
        "pattern_name": patterns_by_id[f"P{index}"]["pattern_name"],
        "working_theory_claim": "The validated pattern causes conditional coverage failure.",
        "strongest_competing_explanation": "A measured nuisance process creates the same association.",
        "competing_explanation_mechanism": "The nuisance process shifts both sensor quality and residuals.",
        "scientifically_plausible_counterexamples": [
            "Coverage remains stable despite the modifier.",
            "The effect disappears in artifact-free segments.",
        ],
        "confounders_and_alternative_explanations": [
            "Motion intensity",
            "Subject-specific label noise",
        ],
        "evidence_supporting_competing_explanation": [
            "Adjustment for the nuisance removes the pattern effect.",
            "Negative controls reproduce the association.",
        ],
        "evidence_refuting_competing_explanation": [
            "The pattern persists under nuisance matching.",
            "The nuisance has no residual-distribution effect.",
        ],
        "distinguishing_experiments": [experiment(index, 1), experiment(index, 2)],
        "pattern_level_novelty": {
            "rating": "MEDIUM",
            "rationale": "Related conformal tools exist, but this physiological falsification is not established.",
            "closest_literature_citation_ids": [
                f"L{((index - 1) % 8) + 1}",
                f"L{(index % 8) + 1}",
            ],
            "novel_contribution": "Links mechanism-specific physiological controls to conditional coverage.",
        },
    }
    for index in range(1, 6)
]

payload = {"pattern_falsification_studies": studies}
checkpoint_dir = Path(__file__).resolve().parent / "test_pattern_falsification_checkpoint"
validated = run_pattern_falsification_stage(
    lambda _prompt: payload,
    {"patterns": list(patterns_by_id.values())},
    [],
    patterns_by_id,
    pass_references,
    valid_citation_ids,
    checkpoint_dir=checkpoint_dir,
)
assert len(validated) == 5
assert sum(len(study["distinguishing_experiments"]) for study in validated) == 10


def unexpected_call(_prompt: str) -> dict:
    raise AssertionError("Validated Experiment 4 checkpoint was not reused.")


checkpointed = run_pattern_falsification_stage(
    unexpected_call,
    {"patterns": list(patterns_by_id.values())},
    [],
    patterns_by_id,
    pass_references,
    valid_citation_ids,
    checkpoint_dir=checkpoint_dir,
)
assert checkpointed == validated

print("Pattern falsification contract validation passed.")
