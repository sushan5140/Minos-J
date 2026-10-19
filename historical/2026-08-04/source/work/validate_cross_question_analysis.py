"""Deterministic Experiment 3 contract and checkpoint validation."""

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from pipeline import run_cross_question_analysis_stage


pass_references = {
    (question, f"H{index}")
    for question in ("Q1", "Q2", "Q3")
    for index in range(1, 10)
}

selected = [
    {
        "rank": rank,
        "source_question": question,
        "hypothesis_id": hypothesis_id,
        "selection_reason": "Specific causal mechanism with a validated discriminating test.",
        "comparative_advantage": "More directly measurable than alternative survivors.",
        "residual_weakness": "External validity remains bounded by the source dataset.",
    }
    for rank, (question, hypothesis_id) in enumerate(
        [
            ("Q1", "H1"),
            ("Q2", "H1"),
            ("Q3", "H1"),
            ("Q1", "H2"),
            ("Q2", "H2"),
            ("Q3", "H2"),
            ("Q1", "H3"),
            ("Q2", "H3"),
            ("Q3", "H3"),
        ],
        start=1,
    )
]

support_sets = [
    [("Q1", "H1"), ("Q2", "H1"), ("Q3", "H1")],
    [("Q1", "H2"), ("Q2", "H2"), ("Q3", "H2")],
    [("Q1", "H3"), ("Q2", "H3"), ("Q3", "H3")],
    [("Q1", "H1"), ("Q2", "H2"), ("Q3", "H3")],
    [("Q1", "H3"), ("Q2", "H1"), ("Q3", "H2")],
]

patterns = [
    {
        "pattern_id": f"P{index}",
        "pattern_name": f"Recurring structure {index}",
        "description": "A concrete structure recurring across physiological uncertainty questions.",
        "supporting_hypotheses": [
            {"source_question": question, "hypothesis_id": hypothesis_id}
            for question, hypothesis_id in supports
        ],
        "causal_structure": "A measured modifier shifts residual distributions under a boundary condition.",
        "boundary_conditions": ["Specified sensor and subject regime"],
        "shared_confounder_controls": ["Subject baseline and motion control"],
        "testable_meta_prediction": "Coverage changes only when the measured modifier crosses its boundary.",
    }
    for index, supports in enumerate(support_sets, start=1)
]

comparisons = [
    {
        "question_pair": pair,
        "shared_structures": ["Conditional residual shift"],
        "distinctive_structures": ["Question-specific measurement boundary"],
        "discriminating_analysis": "Fit the same hierarchical interaction and compare its conditional effect.",
    }
    for pair in ("Q1-Q2", "Q1-Q3", "Q2-Q3")
]

recommendations = [
    {
        "experiment_id": f"E3.{index}",
        "title": f"Validated follow-up {index}",
        "target_pattern_ids": [f"P{index}", "P5"],
        "design": "A preregistered hierarchical ablation with subject-held-out evaluation.",
        "minimum_data_needed": ["Signals", "subject IDs", "segment timestamps"],
        "primary_outcome": "Conditional coverage error with uncertainty interval.",
        "failure_condition": "No conditional coverage change under the preregistered modifier.",
    }
    for index in range(1, 4)
]

payload = {
    "combined_analysis": {
        "strongest_surviving_hypotheses": selected,
        "recurring_structural_patterns": patterns,
        "cross_question_comparisons": comparisons,
        "next_experiment_recommendations": recommendations,
    }
}

checkpoint_dir = Path(__file__).resolve().parent / "test_cross_question_checkpoint"
analysis = run_cross_question_analysis_stage(
    lambda _prompt: payload,
    [],
    pass_references,
    checkpoint_dir=checkpoint_dir,
)
assert len(analysis["strongest_surviving_hypotheses"]) == 9
assert len(analysis["recurring_structural_patterns"]) == 5


def unexpected_call(_prompt: str) -> dict:
    raise AssertionError("Validated Experiment 3 checkpoint was not reused.")


checkpointed = run_cross_question_analysis_stage(
    unexpected_call,
    [],
    pass_references,
    checkpoint_dir=checkpoint_dir,
)
assert checkpointed == analysis

print("Cross-question analysis contract validation passed.")
