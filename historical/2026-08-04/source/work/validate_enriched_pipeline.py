"""Deterministic local contract check for Experiment 2; no network calls."""

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from pipeline import run_enriched_pipeline
from schema import AUDIT_BOOLEAN_FIELDS


hypotheses = [
    {
        "hypothesis_id": f"H{i}",
        "hypothesis": f"Experiment 2 hypothesis {i}",
        "proposed_mechanism": f"Original mechanism {i}",
        "core_assumption": f"Assumption {i}",
        "knowledge_gap_addressed": f"Gap {i}",
        "status": "SPECULATIVE",
    }
    for i in range(1, 11)
]

enrichments = [
    {
        "hypothesis_id": item["hypothesis_id"],
        "original_hypothesis": item["hypothesis"],
        "original_mechanism": item["proposed_mechanism"],
        "possible_confounders": ["Specific confounder"],
        "control_variables": ["Measured control"],
        "rival_explanations": ["Boring rival"],
        "minimum_data_needed": ["Required observation"],
        "effect_size_expectation": "medium",
        "enriched_mechanism": f"Controlled enriched mechanism {i}",
        "enrichment_notes": "Added explicit confounder and control logic.",
    }
    for i, item in enumerate(hypotheses, start=1)
]

audits = [
    {
        "hypothesis_id": f"H{i}",
        "audit_decision": "PASS",
        **{field: True for field in AUDIT_BOOLEAN_FIELDS},
        "failure_points": [],
        "decision_reason": f"Enriched mechanism {i} satisfies every strict checklist requirement.",
        "salvage_note": "",
    }
    for i in range(1, 11)
]

rivals = [
    {
        "hypothesis_id": f"H{i}",
        "meno_j_hypothesis": f"Enriched hypothesis {i}",
        "meno_j_prediction": f"Distinct prediction {i}",
        "rival_explanation": f"Boring rival {i}",
        "rival_prediction": f"Rival prediction {i}",
        "distinguishing_test": f"Distinguishing test {i}",
        "what_result_supports_meno_j": f"Meno-J result {i}",
        "what_result_supports_rival": f"Rival result {i}",
    }
    for i in range(1, 11)
]

falsifications = [
    {
        "hypothesis_id": f"H{i}",
        "strongest_falsification_test": f"Falsification test {i}",
        "failure_condition": f"Failure condition {i}",
        "minimum_data_needed": f"Minimum data {i}",
        "most_likely_false_positive_risk": f"False-positive risk {i}",
        "most_likely_false_negative_risk": f"False-negative risk {i}",
    }
    for i in range(1, 11)
]

responses = iter(
    [
        {"hypotheses": hypotheses},
        {"enriched_hypotheses": enrichments},
        {"audits": audits},
        {"rival_prediction_matrix": rivals},
        {"falsification_tests": falsifications},
    ]
)

result = run_enriched_pipeline(
    lambda _prompt: next(responses),
    research_question="Experiment 2 validation question?",
    checkpoint_dir=Path(__file__).resolve().parent / "test_enriched_checkpoint",
)
assert result["version"] == "v3_enriched"
assert len(result["stage_4_5_confounder_enrichment"]) == 10
assert result["diagnostics"]["enriched_count"] == 10
assert result["diagnostics"]["avg_confounders_per_hypothesis"] == 1.0
assert result["diagnostics"]["hypotheses_with_effect_size_expectation"] == 10
assert result["diagnostics"]["passed_count"] == 10
assert len(result["stage_6_rival_prediction_matrix"]) == 10
assert len(result["stage_7_falsification_tests"]) == 10


def unexpected_call(_prompt: str) -> dict:
    raise AssertionError("Validated checkpoint was not reused.")


checkpointed_result = run_enriched_pipeline(
    unexpected_call,
    research_question="Experiment 2 validation question?",
    checkpoint_dir=Path(__file__).resolve().parent / "test_enriched_checkpoint",
)
assert checkpointed_result == result

print("Enriched pipeline contract validation passed.")
