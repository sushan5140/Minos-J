"""Validate Meno-J Experiment 5 outputs without using an API key."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_synthetic_geometry.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_synthetic_geometry.md"


def main() -> None:
    if not JSON_OUTPUT.exists():
        raise AssertionError(f"JSON output does not exist: {JSON_OUTPUT}")
    if not MARKDOWN_OUTPUT.exists():
        raise AssertionError(f"Markdown output does not exist: {MARKDOWN_OUTPUT}")
    try:
        report = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("JSON output is invalid.") from exc

    required_conditions = {
        "well_separated_gaussian_clusters",
        "overlapping_gaussian_clusters",
        "imbalanced_class_geometry",
        "sparse_subgroup_geometry",
        "covariate_shifted_test_geometry",
    }
    required_scores = {
        "margin_score",
        "inverse_probability_score",
        "distance_to_class_centroid_score",
    }
    assert set(report["simulation_conditions"]) == required_conditions
    assert set(report["nonconformity_scores"]) == required_scores
    assert set(report["calibration_sizes"]) == {50, 100, 300}
    assert set(report["seeds"]) == {0, 1, 2, 3, 4}
    assert report["results"]
    for row in report["results"]:
        assert 0 <= row["marginal_coverage"] <= 1
        assert all(0 <= value <= 1 for value in row["conditional_coverage_by_class"].values())
        assert all(
            0 <= value <= 1
            for value in row["conditional_coverage_by_subgroup_or_region"].values()
        )
        assert row["average_set_size"] > 0
        assert row["coverage_gap"] >= 0
    assert report["p4_survival_assessment"]
    assert report["validation"]
    assert report["validation"]["new_hypotheses_generated"] == 0
    assert report["validation"]["upstream_successful_stages_rerun"] is False
    assert report["validation"]["model_call_used"] is False
    assert len(report["results"]) == 450
    assert len(report["aggregate_results"]) == 90
    assert MARKDOWN_OUTPUT.read_text(encoding="utf-8").strip()
    print("P4-F2 synthetic geometry output validation passed.")


if __name__ == "__main__":
    main()
