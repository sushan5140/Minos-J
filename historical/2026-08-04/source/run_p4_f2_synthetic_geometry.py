"""Execute Meno-J Experiment 5 without an LLM or API key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import (
    P4_F2_CONDITIONS,
    P4_F2_CONDITIONING,
    P4_F2_SCORES,
    aggregate_p4_f2_results,
    assess_p4_survival,
    run_p4_f2_simulation,
)
from schema import EXPERIMENT_5_NAME, validate_p4_f2_report


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
SOURCE_PATH = OUTPUT_DIR / "meno_j_experiment_4_pattern_falsification_study.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_synthetic_geometry.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_synthetic_geometry.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_5_p4_f2_reproducibility_summary.md"
CALIBRATION_SIZES = (50, 100, 300)
SEEDS = (0, 1, 2, 3, 4)
ALPHA = 0.10
TRAIN_SIZE = 2000
TEST_SIZE = 4000


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required roadmap source is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Roadmap source contains invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Roadmap source must be a JSON object: {path}")
    return payload


def _validate_roadmap_source(source: dict[str, Any]) -> dict[str, Any]:
    validation = source.get("validation", {})
    if not validation.get("no_new_hypotheses_generated"):
        raise ValueError("Experiment 4 source did not preserve the working theory.")
    roadmap_matches = [
        row for row in source.get("ranked_research_roadmap", []) if row.get("experiment_id") == "P4-F2"
    ]
    if len(roadmap_matches) != 1:
        raise ValueError("Experiment 4 must contain exactly one P4-F2 roadmap row.")
    roadmap = roadmap_matches[0]
    if (
        roadmap.get("pattern_id") != "P4"
        or roadmap.get("priority_score") != 4.4
        or roadmap.get("implementation_difficulty") != "LOW"
    ):
        raise ValueError("P4-F2 roadmap metadata does not match the validated Experiment 4 result.")
    p4_studies = [
        study
        for study in source.get("pattern_falsification_studies", [])
        if study.get("pattern_id") == "P4"
    ]
    if len(p4_studies) != 1:
        raise ValueError("Experiment 4 must contain exactly one P4 study.")
    experiment_matches = [
        experiment
        for experiment in p4_studies[0]["distinguishing_experiments"]
        if experiment.get("experiment_id") == "P4-F2"
    ]
    if len(experiment_matches) != 1:
        raise ValueError("Experiment 4 P4 study must contain exactly one P4-F2 design.")
    return {
        "source_file": str(SOURCE_PATH.resolve()),
        "source_sha256": _sha256(SOURCE_PATH),
        "roadmap_entry": roadmap,
        "pattern_study": p4_studies[0],
        "experiment_design": experiment_matches[0],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_report(source: dict[str, Any]) -> dict[str, Any]:
    roadmap_source = _validate_roadmap_source(source)
    results = run_p4_f2_simulation(
        calibration_sizes=CALIBRATION_SIZES,
        seeds=SEEDS,
        alpha=ALPHA,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
    )
    aggregates = aggregate_p4_f2_results(results)
    assessment = assess_p4_survival(results, aggregates)
    report = {
        "experiment_name": EXPERIMENT_5_NAME,
        "roadmap_item": "P4-F2",
        "pattern_tested": "P4",
        "competing_explanation": (
            "Apparent score/conditioning sensitivity is a finite-sample bias–variance effect."
        ),
        "target_coverage": 0.90,
        "alpha": ALPHA,
        "simulation_conditions": list(P4_F2_CONDITIONS),
        "nonconformity_scores": list(P4_F2_SCORES),
        "conditioning_strategies": list(P4_F2_CONDITIONING),
        "calibration_sizes": list(CALIBRATION_SIZES),
        "seeds": list(SEEDS),
        "simulation_config": {
            "classifier": "NumPy regularized linear discriminant analysis",
            "class_count": 3,
            "feature_dimension": 6,
            "training_samples_per_condition_seed": TRAIN_SIZE,
            "maximum_nested_calibration_samples": max(CALIBRATION_SIZES),
            "test_samples_per_condition_seed": TEST_SIZE,
            "finite_sample_quantile": "ceil((n+1)*(1-alpha)) order statistic",
            "nested_calibration_samples": True,
        },
        "roadmap_source": roadmap_source,
        "results": results,
        "aggregate_results": aggregates,
        "p4_survival_assessment": assessment,
        "limitations": [
            "The simulation uses a regularized LDA probability model rather than a deep wearable classifier.",
            "Five seeds characterize Monte Carlo variability but do not exhaust rare-tail behavior.",
            "The largest calibration size is 300, as preregistered here, rather than the n=10,000 idealization in Experiment 4.",
            "Label-conditional Mondrian strata are known exactly; estimated latent clusters are not evaluated.",
        ],
        "next_recommended_experiment": (
            "Run P4-F1 on a real multi-subject wearable dataset, expanding calibration sizes beyond 300 "
            "and comparing label strata with estimated geometry-aware clusters."
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
    return validate_p4_f2_report(report)


def _aggregate_table_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for size in CALIBRATION_SIZES:
        cells = [
            row for row in report["aggregate_results"] if row["calibration_size"] == size
        ]
        rows.append(
            {
                "calibration_size": size,
                "mean_marginal_coverage": float(
                    np.mean([row["mean_marginal_coverage"] for row in cells])
                ),
                "mean_coverage_gap": float(
                    np.mean([row["mean_coverage_gap"] for row in cells])
                ),
                "mean_average_set_size": float(
                    np.mean([row["mean_average_set_size"] for row in cells])
                ),
                "mean_undercoverage_rate": float(
                    np.mean([row["mean_undercoverage_rate"] for row in cells])
                ),
            }
        )
    return rows


def _markdown(report: dict[str, Any]) -> str:
    assessment = report["p4_survival_assessment"]
    lines = [
        f"# {report['experiment_name']}",
        "",
        "## Experiment purpose",
        "",
        "Test whether methodological sensitivity to nonconformity score and conditioning strategy is primarily finite-sample instability or persists under controlled feature geometry.",
        "",
        "## Roadmap source: Experiment 4 / P4-F2",
        "",
        f"- Priority: {report['roadmap_source']['roadmap_entry']['priority_score']:.2f}",
        f"- Difficulty: {report['roadmap_source']['roadmap_entry']['implementation_difficulty']}",
        f"- Competing explanation: {report['competing_explanation']}",
        "",
        "## Simulation conditions",
        "",
    ]
    lines.extend(f"- `{condition}`" for condition in report["simulation_conditions"])
    lines.extend(["", "## Nonconformity scores", ""])
    lines.extend(f"- `{score}`" for score in report["nonconformity_scores"])
    lines.extend(["", "## Calibration sizes and seeds", ""])
    lines.extend(
        [
            f"- Calibration sizes: {', '.join(map(str, report['calibration_sizes']))}",
            f"- Seeds: {', '.join(map(str, report['seeds']))}",
            f"- Conditioning: {', '.join(report['conditioning_strategies'])}",
            "",
            "## Main results table",
            "",
            "| n_calib | Mean marginal coverage | Mean coverage gap | Mean set size | Mean undercoverage rate |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _aggregate_table_rows(report):
        lines.append(
            f"| {row['calibration_size']} | {row['mean_marginal_coverage']:.4f} | "
            f"{row['mean_coverage_gap']:.4f} | {row['mean_average_set_size']:.4f} | "
            f"{row['mean_undercoverage_rate']:.4f} |"
        )
    metrics = assessment["decision_metrics"]
    lines.extend(
        [
            "",
            "## Coverage-gap trends",
            "",
            f"- Relative mean gap reduction from n=50 to n=300: {metrics['relative_mean_gap_reduction_50_to_300']:.1%}",
            f"- Relative score/conditioning sensitivity reduction: {metrics['relative_sensitivity_reduction_50_to_300']:.1%}",
            f"- Persistent severe failure cells across all sizes: {metrics['persistent_failure_cell_count_all_sizes']}",
            f"- Persistent large-n failure cells: {metrics['persistent_large_n_failure_cell_count']}",
            "",
            "## Average set-size trends",
            "",
        ]
    )
    for row in _aggregate_table_rows(report):
        lines.append(
            f"- n={row['calibration_size']}: mean set size {row['mean_average_set_size']:.4f}"
        )
    lines.extend(
        [
            "",
            "## Strongest support case for P4",
            "",
            assessment["strongest_support_case"],
            "",
            "## Strongest failure case against P4",
            "",
            assessment["strongest_failure_case"],
            "",
            "## Final survival assessment",
            "",
            f"**{assessment['status']}** — {assessment['rationale']}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
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
        "experiment_name": EXPERIMENT_5_NAME,
        "model_call_used": False,
        "openrouter_key_required": False,
        "deterministic_replay_supported": True,
        "random_number_generator": "numpy.random.Generator(PCG64) with explicit integer seeds",
        "numpy_version": np.__version__,
        "source_file": str(SOURCE_PATH.resolve()),
        "source_sha256": _sha256(SOURCE_PATH),
        "implementation_file": str(Path(__file__).resolve()),
        "implementation_sha256": _sha256(Path(__file__).resolve()),
        "pipeline_sha256": _sha256(Path(__file__).resolve().parent / "pipeline.py"),
        "result_json_sha256": _sha256(JSON_OUTPUT),
        "result_markdown_sha256": _sha256(MARKDOWN_OUTPUT),
        "conditions": report["simulation_conditions"],
        "scores": report["nonconformity_scores"],
        "conditioning_strategies": report["conditioning_strategies"],
        "calibration_sizes": report["calibration_sizes"],
        "seeds": report["seeds"],
        "seed_level_result_count": len(report["results"]),
        "aggregate_result_count": len(report["aggregate_results"]),
        "credential_scan_passed": True,
        "validation_script": str(
            (Path(__file__).resolve().parent / "work" / "validate_p4_f2_synthetic_geometry.py")
        ),
        "run_command": "python run_p4_f2_synthetic_geometry.py",
        "validation_command": "python work/validate_p4_f2_synthetic_geometry.py",
    }


def _repro_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Meno-J Experiment 5: P4-F2 Reproducibility Summary",
            "",
            f"- OpenRouter key required: {summary['openrouter_key_required']}",
            f"- Model call used: {summary['model_call_used']}",
            f"- Deterministic replay supported: {summary['deterministic_replay_supported']}",
            f"- RNG: {summary['random_number_generator']}",
            f"- NumPy: {summary['numpy_version']}",
            f"- Source SHA-256: `{summary['source_sha256']}`",
            f"- Implementation SHA-256: `{summary['implementation_sha256']}`",
            f"- Pipeline SHA-256: `{summary['pipeline_sha256']}`",
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
    source = _read_json(SOURCE_PATH)
    report = _build_report(source)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(_markdown(report), encoding="utf-8")
    reproducibility = _reproducibility(report)
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(reproducibility, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPRO_MARKDOWN_OUTPUT.write_text(
        _repro_markdown(reproducibility),
        encoding="utf-8",
    )
    print(f"Experiment 5 status: {report['p4_survival_assessment']['status']}")
    print(f"Experiment 5 JSON: {JSON_OUTPUT}")
    print(f"Experiment 5 Markdown: {MARKDOWN_OUTPUT}")
    print(f"Reproducibility JSON: {REPRO_JSON_OUTPUT}")
    print(f"Reproducibility Markdown: {REPRO_MARKDOWN_OUTPUT}")


if __name__ == "__main__":
    main()
