"""Independently validate Experiment 6 outputs without credentials or model calls."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_score_conditioning.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_score_conditioning.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_reproducibility_summary.md"


def _credential_scan() -> list[str]:
    marker = "sk-" + "or-v1"
    matches: list[str] = []
    ignored_parts = {".git", "__pycache__", "vendor"}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".env"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if marker in content:
            matches.append(str(path.relative_to(PROJECT_DIR)))
    return matches


def main() -> None:
    for path in (JSON_OUTPUT, MARKDOWN_OUTPUT, REPRO_JSON_OUTPUT, REPRO_MARKDOWN_OUTPUT):
        if not path.exists():
            raise AssertionError(f"Required output does not exist: {path}")
        if not path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"Required UTF-8 output is empty: {path}")
    try:
        report = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
        reproducibility = json.loads(REPRO_JSON_OUTPUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError("Experiment 6 JSON output is invalid.") from exc

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
    required_conditioning = {"marginal", "mondrian_class", "mondrian_region"}
    assert set(report["simulation_conditions"]) == required_conditions
    assert set(report["nonconformity_scores"]) == required_scores
    assert set(report["conditioning_strategies"]) == required_conditioning
    assert set(report["calibration_sizes"]) == {50, 100, 300, 600}
    assert set(report["seeds"]) == {0, 1, 2, 3, 4}
    assert len(report["seed_level_results"]) == 900
    assert len(report["aggregate_results"]) == 180
    assert len(report["trend_results"]) == 45

    for row in report["seed_level_results"]:
        assert 0 <= row["marginal_coverage"] <= 1
        assert all(0 <= value <= 1 for value in row["conditional_coverage_by_class"].values())
        assert all(
            0 <= value <= 1
            for value in row["conditional_coverage_by_region_or_subgroup"].values()
        )
        assert row["coverage_gap"] >= 0
        assert 0 <= row["minimum_group_coverage"] <= 1
        assert row["average_set_size"] > 0
        assert 0 <= row["undercoverage_rate"] <= 1
    assert report["aggregate_results"]
    assert report["persistent_failure_cases"]
    assert all(row["persistent_failure"] for row in report["persistent_failure_cases"])

    answers = report["core_answers"]
    required_answers = {
        "most_robust_score",
        "most_robust_conditioning_strategy",
        "worst_geometry",
        "calibration_size_effect",
        "most_dangerous_score_conditioning_pair",
        "safest_score_conditioning_pair",
    }
    assert set(answers) == required_answers
    assert all(isinstance(answers[field], str) and answers[field].strip() for field in required_answers)
    assert report["p4_followup_assessment"]
    validation = report["validation"]
    assert validation["new_hypotheses_generated"] == 0
    assert validation["upstream_successful_stages_rerun"] is False
    assert validation["model_call_used"] is False
    assert validation["effect_size_targets_present"] is True
    assert validation["failure_conditions_present"] is True
    assert validation["credential_found_in_project_files"] is False
    assert reproducibility["openrouter_key_required"] is False
    assert reproducibility["model_call_used"] is False
    assert reproducibility["deterministic_replay_supported"] is True
    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential pattern found in: {credential_matches}"
    print("P4-F1 score and conditioning output validation passed.")


if __name__ == "__main__":
    main()
