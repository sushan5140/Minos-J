"""Local deterministic contract check; does not call a network service."""

from copy import deepcopy
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from pipeline import run_pipeline
from schema import AUDIT_BOOLEAN_FIELDS, PipelineValidationError


hypotheses = [
    {
        "hypothesis_id": f"H{i}",
        "hypothesis": f"Test hypothesis {i}",
        "proposed_mechanism": f"Specific mechanism {i}",
        "core_assumption": f"Assumption {i}",
        "knowledge_gap_addressed": f"Gap {i}",
        "status": "SPECULATIVE",
    }
    for i in range(1, 11)
]

audits = []
for i in range(1, 11):
    audit = {
        "hypothesis_id": f"H{i}",
        "audit_decision": "PASS" if i == 1 else ("SALVAGEABLE" if i == 2 else "REJECT"),
        **{field: True for field in AUDIT_BOOLEAN_FIELDS},
        "failure_points": [],
        "decision_reason": f"Specific evidence-based audit reason for hypothesis {i} with adequate detail.",
        "salvage_note": "Repair the single failed check." if i == 2 else "",
    }
    if i == 2:
        audit["confounders_identified"] = False
        audit["failure_points"] = ["confounders_identified"]
    elif i > 2:
        for field in ("causal_chain_valid", "mechanism_is_non_generic", "prediction_is_testable"):
            audit[field] = False
        audit["failure_points"] = [
            "causal_chain_valid",
            "mechanism_is_non_generic",
            "prediction_is_testable",
        ]
    audits.append(audit)

rival = {
    "hypothesis_id": "H1",
    "meno_j_hypothesis": "Specific Meno-J mechanism",
    "meno_j_prediction": "Specific prediction",
    "rival_explanation": "Boring rival explanation",
    "rival_prediction": "Divergent rival prediction",
    "distinguishing_test": "Discriminating test",
    "what_result_supports_meno_j": "Result A",
    "what_result_supports_rival": "Result B",
}

falsification = {
    "hypothesis_id": "H1",
    "strongest_falsification_test": "Strong test",
    "failure_condition": "Predefined failure",
    "minimum_data_needed": "Minimum dataset",
    "most_likely_false_positive_risk": "False-positive risk",
    "most_likely_false_negative_risk": "False-negative risk",
}

responses = iter(
    [
        {"hypotheses": hypotheses},
        {"audits": audits},
        {"rival_prediction_matrix": [rival]},
        {"falsification_tests": [falsification]},
    ]
)
result = run_pipeline(
    lambda _prompt: next(responses),
    research_question="Custom calibration question?",
)
assert result["research_question"] == "Custom calibration question?"
assert result["diagnostics"]["generated_count"] == 10
assert result["diagnostics"]["passed_count"] == 1
assert result["diagnostics"]["salvageable_count"] == 1
assert result["diagnostics"]["rejected_count"] == 8
assert len(result["stage_6_rival_prediction_matrix"]) == 1
assert len(result["stage_7_falsification_tests"]) == 1

bad_audits = deepcopy(audits)
bad_audits[1]["failure_points"] = []
bad_responses = iter([{"hypotheses": hypotheses}, {"audits": bad_audits}])
try:
    run_pipeline(lambda _prompt: next(bad_responses))
except PipelineValidationError as exc:
    assert "failure_points mismatch" in str(exc)
else:
    raise AssertionError("failure_points mismatch did not fail loudly")

print("Pipeline contract validation passed.")
