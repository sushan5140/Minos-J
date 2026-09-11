from __future__ import annotations

from .schema import (
    FalsificationTest,
    Hypothesis,
    HypothesisStatus,
    ResearchState,
    TestResult,
)


def validate_testability(test: FalsificationTest) -> None:
    """Reject rhetorical tests that do not define how they can fail."""
    missing = test.missing_fields()
    if missing:
        raise ValueError(
            "Falsification test is incomplete; missing: " + ", ".join(missing)
        )


def register_test(state: ResearchState, test: FalsificationTest) -> None:
    validate_testability(test)
    if test.test_id in state.tests:
        raise ValueError(f"duplicate test_id: {test.test_id}")
    state.tests[test.test_id] = test


def apply_test_result(
    state: ResearchState,
    result: TestResult,
    *,
    falsification_threshold: float = 2.0,
) -> Hypothesis:
    """Apply a preregistered test outcome to a competing hypothesis.

    A failed prediction adds refuting evidence. Repeated or sufficiently
    strong failures can falsify the hypothesis. A passing result does not
    automatically "prove" the hypothesis; it remains a survivor.
    """
    if result.test_id not in state.tests:
        raise KeyError(f"unknown test_id: {result.test_id}")
    if result.hypothesis_id not in state.hypotheses:
        raise KeyError(f"unknown hypothesis_id: {result.hypothesis_id}")

    hypothesis = state.hypotheses[result.hypothesis_id]
    state.results.append(result)

    if result.passed_prediction:
        if hypothesis.status is HypothesisStatus.ACTIVE:
            hypothesis.status = HypothesisStatus.SURVIVED
        hypothesis.supporting_evidence.append(result.evidence)
        return hypothesis

    hypothesis.add_refuting_evidence(result.evidence, result.weight)
    hypothesis.status = (
        HypothesisStatus.FALSIFIED
        if hypothesis.falsification_score >= falsification_threshold
        else HypothesisStatus.WEAKENED
    )
    return hypothesis


def rank_survivors(state: ResearchState) -> list[Hypothesis]:
    """Return non-falsified hypotheses with the least refuting weight first."""
    survivors = [
        h for h in state.hypotheses.values()
        if h.status is not HypothesisStatus.FALSIFIED
    ]
    return sorted(
        survivors,
        key=lambda h: (h.falsification_score, -len(h.supporting_evidence), h.hypothesis_id),
    )
