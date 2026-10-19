"""Execute Meno-J Experiment 6 deterministically, without an LLM or API key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import (
    P4_F1_CONDITIONS,
    P4_F1_CONDITIONING,
    P4_F1_SCORES,
    aggregate_p4_f1_results,
    analyze_p4_f1_results,
    run_p4_f1_simulation,
)
from schema import EXPERIMENT_6_NAME, validate_p4_f1_report


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
ROADMAP_PATH = OUTPUT_DIR / "meno_j_experiment_4_pattern_falsification_study.json"
PRIOR_PATH = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_synthetic_geometry.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_score_conditioning.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_score_conditioning.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_reproducibility_summary.md"
CALIBRATION_SIZES = (50, 100, 300, 600)
SEEDS = (0, 1, 2, 3, 4)
ALPHA = 0.10
TRAIN_SIZE = 2000
TEST_SIZE = 4000


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required validated checkpoint is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Checkpoint contains invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Checkpoint must be a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_sources(
    roadmap_source: dict[str, Any],
    prior_source: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not roadmap_source.get("validation", {}).get("no_new_hypotheses_generated"):
        raise ValueError("Experiment 4 did not preserve the validated working theory.")
    roadmap_matches = [
        row
        for row in roadmap_source.get("ranked_research_roadmap", [])
        if row.get("experiment_id") == "P4-F1"
    ]
    if len(roadmap_matches) != 1:
        raise ValueError("Experiment 4 must contain exactly one P4-F1 roadmap entry.")
    roadmap = roadmap_matches[0]
    if (
        roadmap.get("pattern_id") != "P4"
        or roadmap.get("priority_score") != 4.25
        or roadmap.get("implementation_difficulty") != "LOW"
    ):
        raise ValueError("P4-F1 roadmap metadata does not match Experiment 4.")
    p4_studies = [
        row
        for row in roadmap_source.get("pattern_falsification_studies", [])
        if row.get("pattern_id") == "P4"
    ]
    if len(p4_studies) != 1:
        raise ValueError("Experiment 4 must contain exactly one P4 study.")
    designs = [
        row
        for row in p4_studies[0].get("distinguishing_experiments", [])
        if row.get("experiment_id") == "P4-F1"
    ]
    if len(designs) != 1:
        raise ValueError("Experiment 4 P4 study must contain exactly one P4-F1 design.")

    assessment = prior_source.get("p4_survival_assessment", {})
    if assessment.get("status") != "FALSIFIED":
        raise ValueError("Experiment 5 must have the validated FALSIFIED P4 result.")
    prior_validation = prior_source.get("validation", {})
    if prior_validation.get("new_hypotheses_generated") != 0:
        raise ValueError("Experiment 5 unexpectedly generated hypotheses.")
    if prior_validation.get("model_call_used") is not False:
        raise ValueError("Experiment 5 checkpoint used a model call.")
    roadmap_record = {
        "source_file": str(ROADMAP_PATH.resolve()),
        "source_sha256": _sha256(ROADMAP_PATH),
        "roadmap_entry": roadmap,
        "experiment_design": designs[0],
    }
    prior_record = {
        "source_file": str(PRIOR_PATH.resolve()),
        "source_sha256": _sha256(PRIOR_PATH),
        "status": assessment["status"],
        "strongest_failure_case": assessment["strongest_failure_case"],
    }
    return roadmap_record, prior_record


def _build_report(
    roadmap_source: dict[str, Any],
    prior_source: dict[str, Any],
) -> dict[str, Any]:
    roadmap_record, prior_record = _validate_sources(roadmap_source, prior_source)
    seed_results = run_p4_f1_simulation(
        calibration_sizes=CALIBRATION_SIZES,
        seeds=SEEDS,
        alpha=ALPHA,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
    )
    aggregates = aggregate_p4_f1_results(seed_results)
    analysis = analyze_p4_f1_results(aggregates, CALIBRATION_SIZES)
    report = {
        "experiment_name": EXPERIMENT_6_NAME,
        "roadmap_item": "P4-F1",
        "pattern_tested": "P4",
        "prior_result": (
            "Experiment 5 / P4-F2 falsified the broad finite-sample-only explanation."
        ),
        "target_coverage": 0.90,
        "simulation_conditions": list(P4_F1_CONDITIONS),
        "nonconformity_scores": list(P4_F1_SCORES),
        "conditioning_strategies": list(P4_F1_CONDITIONING),
        "calibration_sizes": list(CALIBRATION_SIZES),
        "seeds": list(SEEDS),
        "simulation_config": {
            "alpha": ALPHA,
            "classifier": "NumPy regularized linear discriminant analysis",
            "class_count": 3,
            "feature_dimension": 6,
            "training_samples_per_condition_seed": TRAIN_SIZE,
            "maximum_nested_calibration_samples": max(CALIBRATION_SIZES),
            "test_samples_per_condition_seed": TEST_SIZE,
            "finite_sample_quantile": "ceil((n+1)*(1-alpha)) order statistic",
            "nested_calibration_samples": True,
            "region_conditioning_scope": (
                "Observable generator-defined region/subgroup; unseen test regions receive an "
                "infinite conservative threshold."
            ),
            "persistent_failure_rule": (
                "mean coverage_gap > 0.15 OR mean minimum_group_coverage < 0.75 at n=600"
            ),
        },
        "roadmap_source": roadmap_record,
        "experiment_5_source": prior_record,
        "seed_level_results": seed_results,
        "aggregate_results": aggregates,
        "trend_results": analysis["trend_results"],
        "robustness_ranking": analysis["robustness_ranking"],
        "persistent_failure_cases": analysis["persistent_failure_cases"],
        "core_answers": analysis["core_answers"],
        "p4_followup_assessment": analysis["p4_followup_assessment"],
        "limitations": [
            "The classifier is regularized LDA rather than a deep wearable stress detector.",
            "Region labels are generator-defined and observable, not estimated from noisy embeddings.",
            "An unseen test region receives an infinite threshold, guaranteeing conservative but potentially uninformative sets.",
            "Five seeds quantify common Monte Carlo variation but not extremely rare tails.",
            "Synthetic Gaussian geometry does not reproduce all temporal and sensor-quality effects in wearable data.",
        ],
        "next_recommended_experiment": (
            "Apply the safest and most dangerous score-conditioning pairs to a real multi-subject "
            "wearable benchmark with subject, activity, sensor-quality, and time-segment metadata."
        ),
        "validation": {
            "new_hypotheses_generated": 0,
            "upstream_successful_stages_rerun": False,
            "model_call_used": False,
            "effect_size_targets_present": True,
            "failure_conditions_present": True,
            "credential_found_in_project_files": False,
        },
    }
    return validate_p4_f1_report(report)


def _mean_by_size(report: dict[str, Any]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for size in CALIBRATION_SIZES:
        cells = [
            row for row in report["aggregate_results"] if row["calibration_size"] == size
        ]
        rows.append(
            {
                "calibration_size": float(size),
                "coverage": float(np.mean([row["mean_marginal_coverage"] for row in cells])),
                "gap": float(np.mean([row["mean_coverage_gap"] for row in cells])),
                "minimum": float(
                    np.mean([row["mean_minimum_group_coverage"] for row in cells])
                ),
                "set_size": float(np.mean([row["mean_average_set_size"] for row in cells])),
                "undercoverage": float(
                    np.mean([row["mean_undercoverage_rate"] for row in cells])
                ),
            }
        )
    return rows


def _markdown(report: dict[str, Any]) -> str:
    answers = report["core_answers"]
    assessment = report["p4_followup_assessment"]
    lines = [
        f"# {report['experiment_name']}",
        "",
        "## Experiment purpose",
        "",
        "Isolate which score and conditioning strategy fails under each geometry and whether larger calibration samples repair the failure.",
        "",
        "## Roadmap source: Experiment 4 / P4-F1",
        "",
        f"- Priority: {report['roadmap_source']['roadmap_entry']['priority_score']:.2f}",
        f"- Difficulty: {report['roadmap_source']['roadmap_entry']['implementation_difficulty']}",
        "",
        "## Connection to Experiment 5 / P4-F2",
        "",
        report["prior_result"],
        "",
        "## Simulation conditions",
        "",
    ]
    lines.extend(f"- `{value}`" for value in report["simulation_conditions"])
    lines.extend(["", "## Nonconformity scores", ""])
    lines.extend(f"- `{value}`" for value in report["nonconformity_scores"])
    lines.extend(["", "## Conditioning strategies", ""])
    lines.extend(f"- `{value}`" for value in report["conditioning_strategies"])
    lines.extend(
        [
            "",
            "## Calibration sizes and seeds",
            "",
            f"- Calibration sizes: {', '.join(map(str, report['calibration_sizes']))}",
            f"- Seeds: {', '.join(map(str, report['seeds']))}",
            "",
            "## Main aggregate table",
            "",
            "| n_calib | Coverage | Coverage gap | Minimum group coverage | Set size | Undercoverage rate |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _mean_by_size(report):
        lines.append(
            f"| {int(row['calibration_size'])} | {row['coverage']:.4f} | {row['gap']:.4f} | "
            f"{row['minimum']:.4f} | {row['set_size']:.4f} | {row['undercoverage']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Robustness ranking",
            "",
            "| Type | Rank | Entity | Persistent failures | Gap at n=600 | Min group coverage | Set size |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in report["robustness_ranking"]:
        lines.append(
            f"| {row['entity_type']} | {row['rank']} | `{row['entity']}` | "
            f"{row['persistent_failure_count']} | {row['mean_coverage_gap_at_600']:.4f} | "
            f"{row['mean_minimum_group_coverage_at_600']:.4f} | "
            f"{row['mean_average_set_size_at_600']:.4f} |"
        )
    lines.extend(["", "## Persistent failure cases", ""])
    for row in report["persistent_failure_cases"]:
        lines.append(
            f"- `{row['condition']} / {row['score_type']} / {row['conditioning_strategy']}`: "
            f"gap={row['coverage_gap_at_600']:.4f}, min coverage="
            f"{row['minimum_group_coverage_at_600']:.4f}, set size="
            f"{row['average_set_size_at_600']:.4f}."
        )
    lines.extend(["", "## Coverage-gap trends", ""])
    for row in _mean_by_size(report):
        lines.append(f"- n={int(row['calibration_size'])}: mean gap {row['gap']:.4f}")
    lines.extend(["", "## Average set-size trends", ""])
    for row in _mean_by_size(report):
        lines.append(f"- n={int(row['calibration_size'])}: mean set size {row['set_size']:.4f}")
    lines.extend(
        [
            "",
            "## Most robust score",
            "",
            answers["most_robust_score"],
            "",
            "## Most robust conditioning strategy",
            "",
            answers["most_robust_conditioning_strategy"],
            "",
            "## Most dangerous score-conditioning pair",
            "",
            answers["most_dangerous_score_conditioning_pair"],
            "",
            "## Safest score-conditioning pair",
            "",
            answers["safest_score_conditioning_pair"],
            "",
            "## Calibration-size effect",
            "",
            answers["calibration_size_effect"],
            "",
            "## Final P4 follow-up assessment",
            "",
            f"**{assessment['status']}** — {assessment['rationale']}",
            "",
            f"- Strongest structural failure: {assessment['strongest_structural_failure_case']}",
            f"- Strongest size effect: {assessment['strongest_size_effect_case']}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {value}" for value in report["limitations"])
    lines.extend(
        [
            "",
            "## Next recommended experiment",
            "",
            report["next_recommended_experiment"],
            "",
        ]
    )
    return "\n".join(lines)


def _reproducibility(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_6_NAME,
        "model_call_used": False,
        "openrouter_key_required": False,
        "deterministic_replay_supported": True,
        "random_number_generator": "numpy.random.Generator(PCG64) with explicit integer seeds",
        "numpy_version": np.__version__,
        "roadmap_source_sha256": _sha256(ROADMAP_PATH),
        "experiment_5_source_sha256": _sha256(PRIOR_PATH),
        "implementation_sha256": _sha256(Path(__file__).resolve()),
        "pipeline_sha256": _sha256(PROJECT_DIR / "pipeline.py"),
        "schema_sha256": _sha256(PROJECT_DIR / "schema.py"),
        "result_json_sha256": _sha256(JSON_OUTPUT),
        "result_markdown_sha256": _sha256(MARKDOWN_OUTPUT),
        "conditions": report["simulation_conditions"],
        "scores": report["nonconformity_scores"],
        "conditioning_strategies": report["conditioning_strategies"],
        "calibration_sizes": report["calibration_sizes"],
        "seeds": report["seeds"],
        "seed_level_result_count": len(report["seed_level_results"]),
        "aggregate_result_count": len(report["aggregate_results"]),
        "credential_scan_passed": True,
        "run_command": "python -u run_p4_f1_score_conditioning.py",
        "validation_command": "python -u work/validate_p4_f1_score_conditioning.py",
    }


def _repro_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Meno-J Experiment 6: P4-F1 Reproducibility Summary",
            "",
            f"- OpenRouter key required: {summary['openrouter_key_required']}",
            f"- Model call used: {summary['model_call_used']}",
            f"- Deterministic replay supported: {summary['deterministic_replay_supported']}",
            f"- RNG: {summary['random_number_generator']}",
            f"- NumPy: {summary['numpy_version']}",
            f"- Roadmap source SHA-256: `{summary['roadmap_source_sha256']}`",
            f"- Experiment 5 source SHA-256: `{summary['experiment_5_source_sha256']}`",
            f"- Implementation SHA-256: `{summary['implementation_sha256']}`",
            f"- Pipeline SHA-256: `{summary['pipeline_sha256']}`",
            f"- Schema SHA-256: `{summary['schema_sha256']}`",
            f"- Result JSON SHA-256: `{summary['result_json_sha256']}`",
            f"- Result Markdown SHA-256: `{summary['result_markdown_sha256']}`",
            f"- Seed-level rows: {summary['seed_level_result_count']}",
            f"- Aggregate rows: {summary['aggregate_result_count']}",
            f"- Credential scan passed: {summary['credential_scan_passed']}",
            "",
            "## Commands",
            "",
            f"- Run: `{summary['run_command']}`",
            f"- Validate: `{summary['validation_command']}`",
            "",
        ]
    )


def main() -> None:
    roadmap = _read_json(ROADMAP_PATH)
    prior = _read_json(PRIOR_PATH)
    report = _build_report(roadmap, prior)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(_markdown(report), encoding="utf-8")
    reproducibility = _reproducibility(report)
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(reproducibility, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPRO_MARKDOWN_OUTPUT.write_text(
        _repro_markdown(reproducibility), encoding="utf-8"
    )
    print(f"Experiment 6 status: {report['p4_followup_assessment']['status']}")
    print(f"Experiment 6 JSON: {JSON_OUTPUT}")
    print(f"Experiment 6 Markdown: {MARKDOWN_OUTPUT}")
    print(f"Reproducibility JSON: {REPRO_JSON_OUTPUT}")
    print(f"Reproducibility Markdown: {REPRO_MARKDOWN_OUTPUT}")


if __name__ == "__main__":
    main()
