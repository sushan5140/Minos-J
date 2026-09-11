from minos_j.pipeline import apply_test_result, register_test, validate_testability
from minos_j.schema import (
    FalsificationTest,
    Hypothesis,
    HypothesisStatus,
    ResearchState,
    TestResult as FalsificationResult,
)


def valid_test() -> FalsificationTest:
    return FalsificationTest(
        test_id="T1",
        prediction="Coverage gap should shrink below 0.10 as n increases.",
        expected_effect="Gap < 0.10",
        effect_size_rationale="A finite-sample explanation predicts material convergence.",
        minimum_data_requirement="At least the preregistered largest calibration size.",
        failure_condition="Gap remains >= 0.10 at the largest calibration size.",
        statistical_test_plan="Compare preregistered aggregate gap across calibration sizes.",
    )


def test_incomplete_test_is_rejected():
    test = valid_test()
    broken = FalsificationTest(
        **{**test.__dict__, "failure_condition": ""}
    )
    try:
        validate_testability(broken)
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete falsification test should fail validation")


def test_failed_predictions_can_falsify_hypothesis():
    state = ResearchState.from_hypotheses(
        "Is the failure finite-sample only?",
        [Hypothesis("H1", "The effect disappears with more calibration data.")],
    )
    register_test(state, valid_test())

    apply_test_result(
        state,
        FalsificationResult("T1", "H1", False, "gap=0.25", "Failure persisted.", weight=1.0),
    )
    assert state.hypotheses["H1"].status is HypothesisStatus.WEAKENED

    apply_test_result(
        state,
        FalsificationResult("T1", "H1", False, "gap=0.20", "Failure replicated.", weight=1.0),
    )
    assert state.hypotheses["H1"].status is HypothesisStatus.FALSIFIED
