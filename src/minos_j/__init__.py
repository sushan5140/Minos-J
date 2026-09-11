"""Minos-J reference research contracts.

This package was added to the public repository after the historical
experiments. It is not claimed as a byte-identical copy of the original
August 4 implementation.
"""

from .schema import FalsificationTest, Hypothesis, ResearchState, TestResult
from .pipeline import apply_test_result, rank_survivors, validate_testability

__all__ = [
    "FalsificationTest",
    "Hypothesis",
    "ResearchState",
    "TestResult",
    "apply_test_result",
    "rank_survivors",
    "validate_testability",
]
