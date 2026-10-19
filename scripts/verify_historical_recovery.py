#!/usr/bin/env python3
"""Verify recovered originals, headline metrics, v4 state, and provenance."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "historical" / "2026-08-04"
OUTPUTS = HISTORICAL / "outputs"
CHECKPOINTS = HISTORICAL / "checkpoints"
LOGS = HISTORICAL / "logs"
MANIFEST = HISTORICAL / "MANIFEST.sha256"
PUBLIC_RESULTS = ROOT / "results" / "recovered_results.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    # utf-8-sig accepts both ordinary UTF-8 and the BOM emitted by the two
    # historical PowerShell hash records without modifying their bytes.
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    assert isinstance(value, dict), f"Expected JSON object: {path}"
    return value


def verify_manifest() -> int:
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(set(lines)) == 287
    listed_paths: set[str] = set()
    for line in lines:
        expected, relative = line.split("  ", 1)
        listed_paths.add(relative)
        path = HISTORICAL / Path(relative)
        assert path.is_file(), f"Missing manifest path: {relative}"
        assert sha256(path) == expected, f"Hash mismatch: {relative}"
    expected_paths = {
        path.relative_to(HISTORICAL).as_posix()
        for name in ("source", "outputs", "checkpoints", "logs")
        for path in (HISTORICAL / name).rglob("*")
        if path.is_file()
    }
    assert listed_paths == expected_paths, "Manifest does not exactly cover the recovered evidence trees"
    return len(lines)


def verify_python_syntax() -> int:
    files = sorted((HISTORICAL / "source").rglob("*.py"))
    assert len(files) == 56
    for path in files:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return len(files)


def verify_first_run_hashes() -> int:
    verified = 0
    for name in ("p4_f1_first_run_hashes.json", "p4_f2_first_run_hashes.json"):
        records = read_json(LOGS / name)
        assert len(records) == 4
        for original_path, expected in records.items():
            relative = Path(original_path.replace("\\", "/"))
            assert relative.parts[0] == "outputs"
            recovered = HISTORICAL / relative
            assert sha256(recovered).upper() == expected.upper()
            verified += 1
    return verified


def lookup_aggregate(rows: list[dict[str, Any]], condition: str, score: str, conditioning: str, n: int) -> dict[str, Any]:
    matches = [
        row for row in rows
        if row["condition"] == condition
        and row["score_type"] == score
        and row["conditioning_strategy"] == conditioning
        and row["calibration_size"] == n
    ]
    assert len(matches) == 1
    return matches[0]


def verify_experiment_4(public: dict[str, Any]) -> None:
    original = read_json(OUTPUTS / "meno_j_experiment_4_pattern_falsification_study.json")
    replay = read_json(OUTPUTS / "meno_j_experiment_4_reproducibility_summary.json")
    record = public["experiment_4"]
    studies = original["pattern_falsification_studies"]
    experiments = [item for study in studies for item in study["distinguishing_experiments"]]
    sources = original["validated_literature_sources"]
    validation = original["validation"]
    assert record["runner"] == "run_pattern_falsification.py"
    assert record["surviving_explanations"] == validation["working_theory_survivor_count"] == 9
    assert record["competing_patterns"] == len(studies) == validation["working_theory_pattern_count"] == 5
    assert record["distinguishing_experiments"] == len(experiments) == 10
    assert record["validated_primary_sources"] == len(sources) == 8
    assert record["unknown_or_invalid_citations"] == validation["unknown_citation_count"] == 0
    assert record["effect_size_targets"] == {"present": sum(bool(item["expected_effect_size"]) for item in experiments), "total": len(experiments)}
    assert record["explicit_failure_conditions"] == {"present": sum(bool(item["failure_condition_for_working_theory"]) for item in experiments), "total": len(experiments)}
    assert record["upstream_reruns"] is replay["successful_upstream_stages_rerun"] is False
    assert record["no_key_replay_succeeded"] is replay["checkpoint_reusable_without_api_key"] is True


def verify_experiment_5(public: dict[str, Any]) -> None:
    original = read_json(OUTPUTS / "meno_j_experiment_5_p4_f2_synthetic_geometry.json")
    replay = read_json(OUTPUTS / "meno_j_experiment_5_p4_f2_reproducibility_summary.json")
    record = public["experiment_5"]
    assert record["label"] == "P4-F2"
    assert record["runner"] == "run_p4_f2_synthetic_geometry.py"
    design = record["design"]
    assert design["geometries"] == len(original["simulation_conditions"]) == 5
    assert design["scores"] == len(original["nonconformity_scores"]) == 3
    assert design["conditioning_strategies"] == replay["conditioning_strategies"] == ["marginal", "mondrian_class"]
    assert design["calibration_sizes"] == original["calibration_sizes"] == [50, 100, 300]
    assert design["seeds"] == original["seeds"] == [0, 1, 2, 3, 4]
    assert design["seed_rows"] == len(original["results"]) == replay["seed_level_result_count"] == 450
    assert design["aggregates"] == len(original["aggregate_results"]) == replay["aggregate_result_count"] == 90

    findings = record["findings"]
    metrics = original["p4_survival_assessment"]["decision_metrics"]
    mean_gaps = metrics["mean_coverage_gap_by_calibration_size"]
    assert findings["overall_mean_gap_n50"] == round(mean_gaps["50"], 4) == 0.2603
    assert findings["overall_mean_gap_n300"] == round(mean_gaps["300"], 4) == 0.2894
    assert findings["sensitivity_decline_percent"] == round(metrics["relative_sensitivity_reduction_50_to_300"] * 100, 1) == 9.7
    assert findings["persistent_failure_cells"] == metrics["persistent_failure_cell_count_all_sizes"] == 14
    assert findings["severe_cells_at_n300"] == metrics["persistent_large_n_failure_cell_count"] == 15
    overlap50 = lookup_aggregate(original["aggregate_results"], "overlapping_gaussian_clusters", "distance_to_class_centroid_score", "mondrian_class", 50)
    overlap300 = lookup_aggregate(original["aggregate_results"], "overlapping_gaussian_clusters", "distance_to_class_centroid_score", "mondrian_class", 300)
    sparse300 = lookup_aggregate(original["aggregate_results"], "sparse_subgroup_geometry", "inverse_probability_score", "marginal", 300)
    assert findings["overlap_centroid_mondrian_gap_n50"] == round(overlap50["mean_coverage_gap"], 4) == 0.1085
    assert findings["overlap_centroid_mondrian_gap_n300"] == round(overlap300["mean_coverage_gap"], 4) == 0.0329
    assert findings["sparse_inverse_probability_marginal_gap_n300"] == round(sparse300["mean_coverage_gap"], 4) == 0.7462
    assert findings["sparse_inverse_probability_marginal_min_group_coverage_n300"] == round(sparse300["mean_minimum_group_coverage"], 4) == 0.1538
    assert record["conclusion"] == original["p4_survival_assessment"]["status"] == "FALSIFIED"
    assert record["deterministic_no_key_replay"] is replay["deterministic_replay_supported"] is True
    assert replay["openrouter_key_required"] is replay["model_call_used"] is False
    assert record["replay_outputs_with_identical_sha256"] == 4


def verify_experiment_6(public: dict[str, Any]) -> None:
    original = read_json(OUTPUTS / "meno_j_experiment_6_p4_f1_score_conditioning.json")
    replay = read_json(OUTPUTS / "meno_j_experiment_6_p4_f1_reproducibility_summary.json")
    record = public["experiment_6"]
    assert record["label"] == "P4-F1"
    assert record["runner"] == "run_p4_f1_score_conditioning.py"
    design = record["design"]
    assert design["geometries"] == len(original["simulation_conditions"]) == 5
    assert design["scores"] == len(original["nonconformity_scores"]) == 3
    assert design["conditioning_strategies"] == len(original["conditioning_strategies"]) == 3
    assert design["calibration_sizes"] == original["calibration_sizes"] == [50, 100, 300, 600]
    assert design["seeds"] == original["seeds"] == [0, 1, 2, 3, 4]
    assert design["seed_rows"] == len(original["seed_level_results"]) == replay["seed_level_result_count"] == 900
    assert design["aggregates"] == len(original["aggregate_results"]) == replay["aggregate_result_count"] == 180
    assert design["trajectories"] == len(original["trend_results"]) == 45

    findings = record["findings"]
    aggregates = original["aggregate_results"]
    at50 = [row["mean_coverage_gap"] for row in aggregates if row["calibration_size"] == 50]
    at600 = [row["mean_coverage_gap"] for row in aggregates if row["calibration_size"] == 600]
    assert findings["overall_mean_gap_n50"] == round(sum(at50) / len(at50), 4) == 0.2119
    assert findings["overall_mean_gap_n600"] == round(sum(at600) / len(at600), 4) == 0.2222
    ranking = {item["entity"]: item for item in original["robustness_ranking"]}
    centroid = ranking["distance_to_class_centroid_score"]
    region = ranking["mondrian_region"]
    dangerous = ranking["inverse_probability_score + marginal"]
    safe = ranking["distance_to_class_centroid_score + mondrian_region"]
    assert findings["distance_to_centroid_mean_gap"] == round(centroid["mean_coverage_gap_at_600"], 4) == 0.1218
    assert findings["region_mondrian_mean_gap"] == round(region["mean_coverage_gap_at_600"], 4) == 0.0903
    assert findings["region_mondrian_mean_minimum_coverage"] == round(region["mean_minimum_group_coverage_at_600"], 4) == 0.837
    assert findings["inverse_probability_marginal_mean_gap"] == round(dangerous["mean_coverage_gap_at_600"], 4) == 0.4209
    assert findings["inverse_probability_marginal_minimum_coverage"] == round(dangerous["mean_minimum_group_coverage_at_600"], 4) == 0.4838
    assert findings["safest_pair"] == {
        "score": "distance-to-centroid", "conditioning": "region-Mondrian",
        "mean_gap": round(safe["mean_coverage_gap_at_600"], 4),
        "minimum_coverage": round(safe["mean_minimum_group_coverage_at_600"], 4),
        "persistent_failures": safe["persistent_failure_count"],
    }
    sparse = next(
        row for row in original["trend_results"]
        if row["condition"] == "sparse_subgroup_geometry"
        and row["score_type"] == "inverse_probability_score"
        and row["conditioning_strategy"] == "marginal"
    )
    assert findings["sparse_inverse_probability_marginal_n600"] == {
        "gap": round(sparse["coverage_gap_at_600"], 4),
        "minimum_coverage": round(sparse["minimum_group_coverage_at_600"], 4),
    }
    assert findings["persistent_failure_trajectories"] == len(original["persistent_failure_cases"]) == 15
    assert findings["total_trajectories"] == len(original["trend_results"]) == 45
    assert record["conclusion"] == original["p4_followup_assessment"]["status"] == "STRUCTURAL_FAILURE_CONFIRMED"


def verify_experiment_7(public: dict[str, Any]) -> None:
    record = public["experiment_7_v4"]
    for key, filename in (("q1", "meno_j_experiment_7_v4_q1.json"), ("q2", "meno_j_experiment_7_v4_q2.json")):
        original = read_json(OUTPUTS / filename)
        diagnostics = original["diagnostics"]
        assert record[key]["generated"] == diagnostics["generated_count"] == 10
        assert record[key]["pass"] == diagnostics["passed_count"]
        assert record[key]["salvageable"] == diagnostics["salvageable_count"]
        assert record[key]["reject"] == diagnostics["rejected_count"]
        assert record[key]["valid_stages"] == "4-7"
        assert len(original["stage_6_rival_prediction_matrix"]) == diagnostics["passed_count"]
        assert len(original["stage_7_falsification_tests"]) == diagnostics["passed_count"]
        if key == "q2":
            assert diagnostics["rubber_stamp_red_flags"] == [
                "10/10 passed",
                "0 rejection reasons",
                "all checklist values true",
                "no salvageable or rejected hypotheses",
            ]
    q3_files = sorted(path.name for path in (CHECKPOINTS / "experiment_7_checkpoints" / "q3").glob("*.json"))
    assert q3_files == ["stage_4.json", "stage_4_1.json", "stage_4_2.json"]
    assert record["q3"]["valid_through_stage"] == "4.2"
    assert record["q3"]["blocked_at"] == "4.3"
    assert not (OUTPUTS / "meno_j_experiment_7_v4_q3.json").exists()
    assert not (OUTPUTS / "meno_j_experiment_7_v4_architecture_ablation_report.json").exists()
    assert record["retries_total"] == 11
    assert record["http_429_retries"] == 8
    for key in ("q1", "q2"):
        v3 = read_json(OUTPUTS / f"meno_j_experiment_2_v3_{key}.json")["diagnostics"]["top_failed_checklist_fields"]
        v4 = read_json(OUTPUTS / f"meno_j_experiment_7_v4_{key}.json")["diagnostics"]["top_failed_checklist_fields"]
        assert v3.get("confounders_identified", 0) == v4.get("confounders_identified", 0) == 0
        assert v3.get("effect_size_plausible", 0) == v4.get("effect_size_plausible", 0) == 0
    assert record["comparison_to_v3"] == {
        "mechanism_generic_failures_q1": "1 -> 0",
        "mechanism_generic_failures_q2": "3 -> 0",
        "confounder_effect_size_failures": "0 -> 0",
    }
    project_record = (OUTPUTS / "meno_j_complete_project_record_copy_paste.md").read_text(encoding="utf-8")
    assert "Total automatic retries observed: 11" in project_record
    assert "HTTP 429 retries: 8" in project_record
    assert "The fallback model was not actually used." in project_record


def main() -> None:
    public = read_json(PUBLIC_RESULTS)
    assert public["provenance"]["original_source_bytes_present"] is True
    assert public["provenance"]["historical_recovery_path"] == "historical/2026-08-04"
    manifest_count = verify_manifest()
    syntax_count = verify_python_syntax()
    first_run_hash_count = verify_first_run_hashes()
    original_34 = sorted(OUTPUTS.glob("meno_j_experiment_[1-7]_*.json")) + sorted(OUTPUTS.glob("meno_j_experiment_[1-7]_*.md"))
    assert len(original_34) == 34
    verify_experiment_4(public)
    verify_experiment_5(public)
    verify_experiment_6(public)
    verify_experiment_7(public)
    print(f"Historical manifest: OK ({manifest_count} files)")
    print(f"Historical Python syntax: OK ({syntax_count} files)")
    print(f"Recorded first-run hashes: OK ({first_run_hash_count} files)")
    print("Historical 34-output set: present and individually hashed")
    print("Public Experiment 4-7 metrics: verified against original artifacts")
    print("Experiment 7 Q3: correctly remains incomplete through Stage 4.2")
    print("Historical experiments were NOT rerun by this verifier.")


if __name__ == "__main__":
    main()
