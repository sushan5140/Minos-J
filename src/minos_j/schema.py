from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    WEAKENED = "weakened"
    FALSIFIED = "falsified"
    SURVIVED = "survived"


@dataclass(frozen=True)
class FalsificationTest:
    """A test must state in advance what evidence would count against a claim."""

    test_id: str
    prediction: str
    expected_effect: str
    effect_size_rationale: str
    minimum_data_requirement: str
    failure_condition: str
    statistical_test_plan: str

    def missing_fields(self) -> tuple[str, ...]:
        fields = {
            "prediction": self.prediction,
            "expected_effect": self.expected_effect,
            "effect_size_rationale": self.effect_size_rationale,
            "minimum_data_requirement": self.minimum_data_requirement,
            "failure_condition": self.failure_condition,
            "statistical_test_plan": self.statistical_test_plan,
        }
        return tuple(name for name, value in fields.items() if not value.strip())


@dataclass
class Hypothesis:
    hypothesis_id: str
    statement: str
    distinguishing_predictions: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
    refuting_evidence: list[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    falsification_score: float = 0.0

    def add_refuting_evidence(self, evidence: str, weight: float = 1.0) -> None:
        self.refuting_evidence.append(evidence)
        self.falsification_score += max(0.0, weight)


@dataclass(frozen=True)
class TestResult:
    test_id: str
    hypothesis_id: str
    passed_prediction: bool
    effect_observed: str
    evidence: str
    weight: float = 1.0


@dataclass
class ResearchState:
    question: str
    hypotheses: dict[str, Hypothesis]
    tests: dict[str, FalsificationTest] = field(default_factory=dict)
    results: list[TestResult] = field(default_factory=list)

    @classmethod
    def from_hypotheses(
        cls, question: str, hypotheses: Iterable[Hypothesis]
    ) -> "ResearchState":
        items = list(hypotheses)
        ids = [h.hypothesis_id for h in items]
        if len(ids) != len(set(ids)):
            raise ValueError("hypothesis_id values must be unique")
        return cls(question=question, hypotheses={h.hypothesis_id: h for h in items})
