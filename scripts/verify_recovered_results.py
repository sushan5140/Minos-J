#!/usr/bin/env python3
"""Validate both the public record and the recovered historical originals."""

from __future__ import annotations

import json
from pathlib import Path

from verify_historical_recovery import main as verify_historical_recovery


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "recovered_results.json"


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))

    e4 = data["experiment_4"]
    assert e4["surviving_explanations"] == 9
    assert e4["competing_patterns"] == 5
    assert e4["distinguishing_experiments"] == 10
    assert e4["effect_size_targets"] == {"present": 10, "total": 10}
    assert e4["explicit_failure_conditions"] == {"present": 10, "total": 10}

    e5 = data["experiment_5"]
    design5 = e5["design"]
    expected_rows5 = (
        design5["geometries"]
        * design5["scores"]
        * len(design5["conditioning_strategies"])
        * len(design5["calibration_sizes"])
        * len(design5["seeds"])
    )
    assert expected_rows5 == design5["seed_rows"] == 450
    assert e5["findings"]["sparse_inverse_probability_marginal_gap_n300"] == 0.7462
    assert e5["conclusion"] == "FALSIFIED"

    e6 = data["experiment_6"]
    design6 = e6["design"]
    expected_rows6 = (
        design6["geometries"]
        * design6["scores"]
        * design6["conditioning_strategies"]
        * len(design6["calibration_sizes"])
        * len(design6["seeds"])
    )
    assert expected_rows6 == design6["seed_rows"] == 900
    assert design6["trajectories"] == 45
    assert e6["findings"]["persistent_failure_trajectories"] == 15
    assert e6["conclusion"] == "STRUCTURAL_FAILURE_CONFIRMED"

    e7 = data["experiment_7_v4"]
    for key in ("q1", "q2"):
        q = e7[key]
        assert q["generated"] == q["pass"] + q["salvageable"] + q["reject"]

    refactor = data["architecture_refactor"]
    assert refactor["historical_outputs_preserved_byte_identical"] == 34
    assert refactor["manifest_hash_match"] is True

    print("Recovered Minos-J result record: OK")
    verify_historical_recovery()


if __name__ == "__main__":
    main()
