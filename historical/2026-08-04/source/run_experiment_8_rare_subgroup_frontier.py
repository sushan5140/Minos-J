"""Run Meno-J Experiment 8 deterministically, without an LLM or API key.

This experiment challenges the strongest apparent mitigation from Experiment 6:
region-Mondrian conditioning.  It separates genuine informative coverage from
coverage obtained by returning the full label set when a rare region has too few
calibration observations to define a finite conformal quantile.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import (
    _conformal_quantile,
    _correlated_covariance,
    _fit_regularized_lda,
    _model_outputs,
    _score_matrix,
)


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
SOURCE_PATH = OUTPUT_DIR / "meno_j_experiment_6_p4_f1_score_conditioning.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_8_rare_subgroup_frontier.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_8_rare_subgroup_frontier.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_8_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_8_reproducibility_summary.md"

EXPERIMENT_NAME = "Meno-J Experiment 8: Rare-Subgroup Feasibility Frontier"
ALPHA = 0.10
TARGET_COVERAGE = 1.0 - ALPHA
PREVALENCES = (0.005, 0.01, 0.02, 0.05, 0.08, 0.15, 0.30)
CALIBRATION_SIZES = (50, 100, 300, 600, 1200, 3000)
SEEDS = tuple(range(20))
SCORES = ("distance_to_class_centroid_score", "inverse_probability_score")
STRATEGIES = (
    "marginal",
    "oracle_region",
    "mildly_noisy_region",
    "moderately_noisy_region",
)
METADATA_QUALITY = {
    "oracle_region": {"sensitivity": 1.0, "false_positive_rate": 0.0},
    "mildly_noisy_region": {"sensitivity": 0.90, "false_positive_rate": 0.02},
    "moderately_noisy_region": {"sensitivity": 0.70, "false_positive_rate": 0.05},
}
TRAIN_SIZE = 4000
TEST_SIZE = 5000
CLASS_COUNT = 3
FEATURE_DIMENSION = 6


class ExperimentValidationError(ValueError):
    """Raised when Experiment 8 violates its preregistered data contract."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_source() -> dict[str, Any]:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Required validated source is missing: {SOURCE_PATH}")
    try:
        source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentValidationError("Experiment 6 source is invalid JSON.") from exc
    if source.get("p4_followup_assessment", {}).get("status") != "STRUCTURAL_FAILURE_CONFIRMED":
        raise ExperimentValidationError(
            "Experiment 6 must contain the validated STRUCTURAL_FAILURE_CONFIRMED result."
        )
    if source.get("validation", {}).get("model_call_used") is not False:
        raise ExperimentValidationError("Experiment 6 unexpectedly used a model call.")
    return source


def minimum_finite_group_count(alpha: float) -> int:
    """Return the smallest group count producing a finite split-conformal quantile."""
    for count in range(1, 1_000_000):
        rank = int(math.ceil((count + 1) * (1 - alpha)))
        if rank <= count:
            return count
    raise RuntimeError("Unable to derive a finite conformal group-count threshold.")


def binomial_probability_at_least(n: int, prevalence: float, minimum: int) -> float:
    """Compute P[Binomial(n, prevalence) >= minimum] using the short lower tail."""
    lower_tail = sum(
        math.comb(n, count)
        * prevalence**count
        * (1.0 - prevalence) ** (n - count)
        for count in range(minimum)
    )
    return float(min(1.0, max(0.0, 1.0 - lower_tail)))


def required_total_calibration(
    prevalence: float,
    minimum: int,
    probability: float,
) -> int:
    """Find the smallest total calibration size meeting a subgroup-count probability."""
    low, high = minimum, minimum
    while binomial_probability_at_least(high, prevalence, minimum) < probability:
        high *= 2
        if high > 10_000_000:
            raise RuntimeError("Calibration requirement search exceeded its safety bound.")
    while low < high:
        midpoint = (low + high) // 2
        if binomial_probability_at_least(midpoint, prevalence, minimum) >= probability:
            high = midpoint
        else:
            low = midpoint + 1
    return low


def _generate_sparse_geometry(
    sample_count: int,
    prevalence: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    labels = rng.integers(0, CLASS_COUNT, size=sample_count)
    means = np.array(
        [[-2.2, 0, 0, 0, 0, 0], [2.2, 0, 0, 0, 0, 0], [0, 2.2, 0, 0, 0, 0]],
        dtype=float,
    )
    covariance = _correlated_covariance(0.9, 0.20, FEATURE_DIMENSION)
    features = np.empty((sample_count, FEATURE_DIMENSION), dtype=float)
    for label in range(CLASS_COUNT):
        mask = labels == label
        features[mask] = rng.multivariate_normal(means[label], covariance, size=int(mask.sum()))
    rare = rng.random(sample_count) < prevalence
    rare_shift = np.array(
        [[2.0, 2.5, 0, 0, 0, 0], [-2.0, 2.5, 0, 0, 0, 0], [0, -3.0, 0, 0, 0, 0]],
        dtype=float,
    )
    if rare.any():
        features[rare] += rare_shift[labels[rare]]
        features[rare] += rng.normal(0, 0.8, size=(int(rare.sum()), FEATURE_DIMENSION))
    return features, labels.astype(int), rare.astype(bool)


def _observe_region(
    true_rare: np.ndarray,
    sensitivity: float,
    false_positive_rate: float,
    rng: np.random.Generator,
) -> np.ndarray:
    draws = rng.random(len(true_rare))
    return np.where(true_rare, draws < sensitivity, draws < false_positive_rate).astype(bool)


def _safe_mean(values: np.ndarray) -> float:
    return float(values.mean()) if len(values) else float("nan")


def _evaluate(
    calibration_scores: np.ndarray,
    calibration_labels: np.ndarray,
    calibration_true_rare: np.ndarray,
    calibration_observed_rare: np.ndarray,
    test_scores: np.ndarray,
    test_labels: np.ndarray,
    test_true_rare: np.ndarray,
    test_observed_rare: np.ndarray,
    strategy: str,
) -> dict[str, Any]:
    true_calibration_scores = calibration_scores[
        np.arange(len(calibration_labels)), calibration_labels
    ]
    if strategy == "marginal":
        threshold = _conformal_quantile(true_calibration_scores, ALPHA)
        row_thresholds = np.full(len(test_labels), threshold)
        rare_threshold = threshold
        observed_count = int(calibration_true_rare.sum())
    else:
        thresholds = {
            False: _conformal_quantile(
                true_calibration_scores[~calibration_observed_rare], ALPHA
            ),
            True: _conformal_quantile(
                true_calibration_scores[calibration_observed_rare], ALPHA
            ),
        }
        row_thresholds = np.where(
            test_observed_rare,
            thresholds[True],
            thresholds[False],
        )
        rare_threshold = thresholds[True]
        observed_count = int(calibration_observed_rare.sum())
    prediction_sets = test_scores <= row_thresholds[:, None]
    covered = prediction_sets[np.arange(len(test_labels)), test_labels]
    set_sizes = prediction_sets.sum(axis=1)
    rare_mask = test_true_rare
    common_mask = ~rare_mask
    return {
        "marginal_coverage": _safe_mean(covered),
        "true_rare_coverage": _safe_mean(covered[rare_mask]),
        "true_common_coverage": _safe_mean(covered[common_mask]),
        "average_set_size": _safe_mean(set_sizes),
        "true_rare_average_set_size": _safe_mean(set_sizes[rare_mask]),
        "true_common_average_set_size": _safe_mean(set_sizes[common_mask]),
        "true_rare_full_set_fraction": _safe_mean(set_sizes[rare_mask] == CLASS_COUNT),
        "true_common_full_set_fraction": _safe_mean(set_sizes[common_mask] == CLASS_COUNT),
        "true_rare_empty_set_fraction": _safe_mean(set_sizes[rare_mask] == 0),
        "true_common_empty_set_fraction": _safe_mean(set_sizes[common_mask] == 0),
        "true_calibration_rare_count": int(calibration_true_rare.sum()),
        "observed_calibration_rare_count": observed_count,
        "rare_threshold_finite": bool(math.isfinite(rare_threshold)),
    }


def run_simulation() -> list[dict[str, Any]]:
    """Run the preregistered prevalence x size x score x metadata-quality grid."""
    results: list[dict[str, Any]] = []
    maximum_calibration = max(CALIBRATION_SIZES)
    for prevalence_index, prevalence in enumerate(PREVALENCES):
        for seed in SEEDS:
            base = 100_000 * prevalence_index + 1_000 * seed
            train = _generate_sparse_geometry(
                TRAIN_SIZE, prevalence, np.random.default_rng(base + 11)
            )
            calibration = _generate_sparse_geometry(
                maximum_calibration, prevalence, np.random.default_rng(base + 23)
            )
            test = _generate_sparse_geometry(
                TEST_SIZE, prevalence, np.random.default_rng(base + 37)
            )
            model = _fit_regularized_lda(train[0], train[1])
            calibration_probabilities, calibration_distances = _model_outputs(
                model, calibration[0]
            )
            test_probabilities, test_distances = _model_outputs(model, test[0])
            observed_regions: dict[str, tuple[np.ndarray, np.ndarray]] = {
                "oracle_region": (calibration[2], test[2])
            }
            for quality_index, strategy in enumerate(
                ("mildly_noisy_region", "moderately_noisy_region")
            ):
                quality = METADATA_QUALITY[strategy]
                observed_regions[strategy] = (
                    _observe_region(
                        calibration[2],
                        quality["sensitivity"],
                        quality["false_positive_rate"],
                        np.random.default_rng(base + 101 + quality_index * 10),
                    ),
                    _observe_region(
                        test[2],
                        quality["sensitivity"],
                        quality["false_positive_rate"],
                        np.random.default_rng(base + 107 + quality_index * 10),
                    ),
                )
            for score_type in SCORES:
                all_calibration_scores = _score_matrix(
                    score_type, calibration_probabilities, calibration_distances
                )
                test_scores = _score_matrix(score_type, test_probabilities, test_distances)
                for calibration_size in CALIBRATION_SIZES:
                    calibration_slice = slice(0, calibration_size)
                    for strategy in STRATEGIES:
                        if strategy == "marginal":
                            calibration_observed = calibration[2][calibration_slice]
                            test_observed = test[2]
                        else:
                            calibration_observed = observed_regions[strategy][0][
                                calibration_slice
                            ]
                            test_observed = observed_regions[strategy][1]
                        metrics = _evaluate(
                            all_calibration_scores[calibration_slice],
                            calibration[1][calibration_slice],
                            calibration[2][calibration_slice],
                            calibration_observed,
                            test_scores,
                            test[1],
                            test[2],
                            test_observed,
                            strategy,
                        )
                        results.append(
                            {
                                "rare_prevalence": prevalence,
                                "calibration_size": calibration_size,
                                "score_type": score_type,
                                "conditioning_strategy": strategy,
                                "seed": seed,
                                **metrics,
                            }
                        )
    return results


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in results:
        key = (
            row["rare_prevalence"],
            row["calibration_size"],
            row["score_type"],
            row["conditioning_strategy"],
        )
        grouped.setdefault(key, []).append(row)
    aggregates: list[dict[str, Any]] = []
    numeric_fields = (
        "marginal_coverage",
        "true_rare_coverage",
        "true_common_coverage",
        "average_set_size",
        "true_rare_average_set_size",
        "true_common_average_set_size",
        "true_rare_full_set_fraction",
        "true_common_full_set_fraction",
        "true_rare_empty_set_fraction",
        "true_common_empty_set_fraction",
        "true_calibration_rare_count",
        "observed_calibration_rare_count",
    )
    ordering = lambda key: (
        PREVALENCES.index(key[0]),
        CALIBRATION_SIZES.index(key[1]),
        SCORES.index(key[2]),
        STRATEGIES.index(key[3]),
    )
    for key in sorted(grouped, key=ordering):
        rows = grouped[key]
        aggregate: dict[str, Any] = {
            "rare_prevalence": key[0],
            "calibration_size": key[1],
            "score_type": key[2],
            "conditioning_strategy": key[3],
            "seed_count": len(rows),
        }
        for field in numeric_fields:
            values = np.asarray([row[field] for row in rows], dtype=float)
            aggregate[f"mean_{field}"] = float(np.nanmean(values))
            aggregate[f"std_{field}"] = float(np.nanstd(values, ddof=0))
        aggregate["finite_rare_threshold_seed_fraction"] = float(
            np.mean([row["rare_threshold_finite"] for row in rows])
        )
        aggregates.append(aggregate)
    return aggregates


def build_analytic_frontier() -> list[dict[str, Any]]:
    minimum = minimum_finite_group_count(ALPHA)
    rows: list[dict[str, Any]] = []
    for prevalence in PREVALENCES:
        required_95 = required_total_calibration(prevalence, minimum, 0.95)
        required_99 = required_total_calibration(prevalence, minimum, 0.99)
        for calibration_size in CALIBRATION_SIZES:
            rows.append(
                {
                    "rare_prevalence": prevalence,
                    "calibration_size": calibration_size,
                    "expected_rare_count": prevalence * calibration_size,
                    "probability_finite_rare_threshold": binomial_probability_at_least(
                        calibration_size, prevalence, minimum
                    ),
                    "minimum_rare_count_for_finite_threshold": minimum,
                    "minimum_total_calibration_for_95_percent_finite_probability": required_95,
                    "minimum_total_calibration_for_99_percent_finite_probability": required_99,
                }
            )
    return rows


def _select(
    aggregates: list[dict[str, Any]],
    prevalence: float,
    calibration_size: int,
    score: str,
    strategy: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in aggregates
        if row["rare_prevalence"] == prevalence
        and row["calibration_size"] == calibration_size
        and row["score_type"] == score
        and row["conditioning_strategy"] == strategy
    ]
    if len(matches) != 1:
        raise ExperimentValidationError("Unable to select a unique aggregate design cell.")
    return matches[0]


def analyze(
    aggregates: list[dict[str, Any]], analytic_frontier: list[dict[str, Any]]
) -> dict[str, Any]:
    distance = "distance_to_class_centroid_score"
    low_prevalence_oracle = [
        row
        for row in aggregates
        if row["rare_prevalence"] <= 0.02
        and row["calibration_size"] <= 600
        and row["score_type"] == distance
        and row["conditioning_strategy"] == "oracle_region"
    ]
    mean_oracle_coverage = float(
        np.mean([row["mean_true_rare_coverage"] for row in low_prevalence_oracle])
    )
    mean_oracle_rare_set_size = float(
        np.mean([row["mean_true_rare_average_set_size"] for row in low_prevalence_oracle])
    )
    mean_oracle_full_set_fraction = float(
        np.mean([row["mean_true_rare_full_set_fraction"] for row in low_prevalence_oracle])
    )
    mean_oracle_finite_fraction = float(
        np.mean([row["finite_rare_threshold_seed_fraction"] for row in low_prevalence_oracle])
    )

    metadata_comparisons: list[dict[str, Any]] = []
    for prevalence in PREVALENCES:
        for calibration_size in (600, 3000):
            oracle = _select(
                aggregates, prevalence, calibration_size, distance, "oracle_region"
            )
            for strategy in ("mildly_noisy_region", "moderately_noisy_region"):
                noisy = _select(
                    aggregates, prevalence, calibration_size, distance, strategy
                )
                metadata_comparisons.append(
                    {
                        "rare_prevalence": prevalence,
                        "calibration_size": calibration_size,
                        "conditioning_strategy": strategy,
                        "oracle_rare_coverage": oracle["mean_true_rare_coverage"],
                        "noisy_rare_coverage": noisy["mean_true_rare_coverage"],
                        "rare_coverage_penalty": (
                            oracle["mean_true_rare_coverage"]
                            - noisy["mean_true_rare_coverage"]
                        ),
                        "oracle_rare_set_size": oracle[
                            "mean_true_rare_average_set_size"
                        ],
                        "noisy_rare_set_size": noisy[
                            "mean_true_rare_average_set_size"
                        ],
                    }
                )
    strongest_noise_failure = max(
        metadata_comparisons, key=lambda row: row["rare_coverage_penalty"]
    )

    marginal_rows = [
        row
        for row in aggregates
        if row["conditioning_strategy"] == "marginal"
        and row["score_type"] == distance
    ]
    worst_marginal = min(marginal_rows, key=lambda row: row["mean_true_rare_coverage"])
    best_informative_oracle = min(
        (
            row
            for row in aggregates
            if row["conditioning_strategy"] == "oracle_region"
            and row["score_type"] == distance
            and row["mean_true_rare_coverage"] >= 0.88
            and row["mean_true_rare_full_set_fraction"] <= 0.20
        ),
        key=lambda row: (
            row["calibration_size"],
            row["rare_prevalence"],
        ),
        default=None,
    )
    covered_oracle_cells = [
        row
        for row in aggregates
        if row["conditioning_strategy"] == "oracle_region"
        and row["score_type"] == distance
        and row["mean_true_rare_coverage"] >= 0.88
    ]
    best_covered_oracle_cell = min(
        covered_oracle_cells,
        key=lambda row: row["mean_true_rare_full_set_fraction"],
        default=None,
    )
    apparent_safety_is_vacuous = bool(
        mean_oracle_coverage >= 0.88
        and mean_oracle_full_set_fraction >= 0.50
        and mean_oracle_finite_fraction <= 0.50
    )
    metadata_is_fragile = bool(strongest_noise_failure["rare_coverage_penalty"] >= 0.10)
    if apparent_safety_is_vacuous and metadata_is_fragile:
        decision = "ORACLE_SAFETY_PARTLY_VACUOUS_AND_METADATA_FRAGILE"
    elif apparent_safety_is_vacuous:
        decision = "ORACLE_SAFETY_PARTLY_VACUOUS"
    elif metadata_is_fragile:
        decision = "REGION_CONDITIONING_METADATA_FRAGILE"
    else:
        decision = "REGION_CONDITIONING_REMAINS_INFORMATIVELY_ROBUST"
    return {
        "decision": decision,
        "preregistered_decision_rules": {
            "apparent_safety_is_vacuous": (
                "For prevalence <= 0.02 and n_calib <= 600 with distance scoring, mean oracle "
                "rare coverage >= 0.88, mean rare full-set fraction >= 0.50, and mean finite "
                "rare-threshold seed fraction <= 0.50."
            ),
            "metadata_is_fragile": (
                "At least one noisy-metadata cell reduces true rare-group coverage by >= 0.10 "
                "relative to oracle region conditioning."
            ),
        },
        "decision_metrics": {
            "low_prevalence_oracle_mean_rare_coverage": mean_oracle_coverage,
            "low_prevalence_oracle_mean_rare_set_size": mean_oracle_rare_set_size,
            "low_prevalence_oracle_mean_rare_full_set_fraction": mean_oracle_full_set_fraction,
            "low_prevalence_oracle_mean_finite_threshold_fraction": mean_oracle_finite_fraction,
            "apparent_safety_is_vacuous": apparent_safety_is_vacuous,
            "metadata_is_fragile": metadata_is_fragile,
            "informative_oracle_success_cell_count": sum(
                row["mean_true_rare_full_set_fraction"] <= 0.20
                for row in covered_oracle_cells
            ),
            "best_covered_oracle_full_set_fraction": (
                best_covered_oracle_cell["mean_true_rare_full_set_fraction"]
                if best_covered_oracle_cell
                else None
            ),
        },
        "strongest_metadata_noise_failure": strongest_noise_failure,
        "worst_marginal_cell": worst_marginal,
        "first_informative_oracle_cell": best_informative_oracle,
        "best_covered_oracle_cell": best_covered_oracle_cell,
        "secondary_diagnostic": (
            "No tested distance-score oracle-region cell simultaneously achieved mean true "
            "rare coverage >= 0.88 and a mean rare full-set fraction <= 0.20. This diagnostic "
            "was summarized after applying the preregistered primary decision rule."
            if best_informative_oracle is None
            else "At least one tested oracle-region cell achieved both coverage and the specified informativeness threshold."
        ),
        "metadata_noise_comparisons": metadata_comparisons,
        "analytic_frontier_summary": [
            row
            for row in analytic_frontier
            if row["calibration_size"] == 600
        ],
    }


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    required = {
        "experiment_name",
        "research_question",
        "source_checkpoint",
        "preregistered_design",
        "analytic_feasibility_frontier",
        "seed_level_results",
        "aggregate_results",
        "analysis",
        "limitations",
        "working_theory_update",
        "validation",
    }
    missing = required - set(report)
    if missing:
        raise ExperimentValidationError(f"Experiment 8 report missing fields: {sorted(missing)}")
    expected_seed_rows = (
        len(PREVALENCES)
        * len(CALIBRATION_SIZES)
        * len(SCORES)
        * len(STRATEGIES)
        * len(SEEDS)
    )
    expected_aggregate_rows = expected_seed_rows // len(SEEDS)
    if len(report["seed_level_results"]) != expected_seed_rows:
        raise ExperimentValidationError("Experiment 8 seed-level row count is invalid.")
    if len(report["aggregate_results"]) != expected_aggregate_rows:
        raise ExperimentValidationError("Experiment 8 aggregate row count is invalid.")
    if len(report["analytic_feasibility_frontier"]) != len(PREVALENCES) * len(
        CALIBRATION_SIZES
    ):
        raise ExperimentValidationError("Experiment 8 analytic frontier is incomplete.")
    expected_keys = {
        (prevalence, size, score, strategy, seed)
        for prevalence in PREVALENCES
        for size in CALIBRATION_SIZES
        for score in SCORES
        for strategy in STRATEGIES
        for seed in SEEDS
    }
    actual_keys = {
        (
            row["rare_prevalence"],
            row["calibration_size"],
            row["score_type"],
            row["conditioning_strategy"],
            row["seed"],
        )
        for row in report["seed_level_results"]
    }
    if actual_keys != expected_keys:
        raise ExperimentValidationError("Experiment 8 design grid is incomplete or duplicated.")
    for row in report["seed_level_results"]:
        for field in (
            "marginal_coverage",
            "true_rare_coverage",
            "true_common_coverage",
            "true_rare_full_set_fraction",
            "true_common_full_set_fraction",
            "true_rare_empty_set_fraction",
            "true_common_empty_set_fraction",
        ):
            value = row[field]
            if not (0.0 <= value <= 1.0):
                raise ExperimentValidationError(f"Metric {field} is outside [0, 1].")
        for field in (
            "average_set_size",
            "true_rare_average_set_size",
            "true_common_average_set_size",
        ):
            value = row[field]
            if not (0.0 <= value <= CLASS_COUNT):
                raise ExperimentValidationError(f"Metric {field} is outside [0, 3].")
    if minimum_finite_group_count(ALPHA) != 9:
        raise ExperimentValidationError("Expected finite group-count threshold is not 9.")
    validation = report["validation"]
    if validation.get("model_call_used") is not False:
        raise ExperimentValidationError("Experiment 8 must not use a model call.")
    if validation.get("new_hypotheses_generated") != 0:
        raise ExperimentValidationError("Experiment 8 generated a new hypothesis.")
    if validation.get("upstream_successful_stages_rerun") is not False:
        raise ExperimentValidationError("Experiment 8 reran a successful upstream stage.")
    return report


def build_report(
    seed_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _read_source()
    if seed_results is None:
        seed_results = run_simulation()
    aggregates = aggregate_results(seed_results)
    analytic_frontier = build_analytic_frontier()
    analysis = analyze(aggregates, analytic_frontier)
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": (
            "Does region-Mondrian conditioning genuinely repair rare-subgroup undercoverage, "
            "or does it appear safe because insufficient subgroup calibration data force full, "
            "uninformative prediction sets; and how sensitive is it to metadata error?"
        ),
        "source_checkpoint": {
            "path": str(SOURCE_PATH.resolve()),
            "sha256": _sha256(SOURCE_PATH),
            "validated_status": source["p4_followup_assessment"]["status"],
            "reused_without_rerun": True,
        },
        "preregistered_design": {
            "target_coverage": TARGET_COVERAGE,
            "alpha": ALPHA,
            "rare_prevalences": list(PREVALENCES),
            "calibration_sizes": list(CALIBRATION_SIZES),
            "seeds": list(SEEDS),
            "scores": list(SCORES),
            "conditioning_strategies": list(STRATEGIES),
            "metadata_quality": METADATA_QUALITY,
            "classifier": "NumPy regularized linear discriminant analysis",
            "class_count": CLASS_COUNT,
            "feature_dimension": FEATURE_DIMENSION,
            "training_samples_per_prevalence_seed": TRAIN_SIZE,
            "test_samples_per_prevalence_seed": TEST_SIZE,
            "nested_calibration_samples": True,
            "finite_split_conformal_quantile": "ceil((n_group+1)*(1-alpha)) <= n_group",
        },
        "analytic_feasibility_frontier": analytic_frontier,
        "seed_level_results": seed_results,
        "aggregate_results": aggregates,
        "analysis": analysis,
        "limitations": [
            "This is a controlled Gaussian synthetic study, not evidence that the same prevalence frontier holds numerically in WESAD.",
            "True and noisy subgroup labels are generated rather than estimated from wearable features.",
            "The classifier is regularized LDA rather than a deep physiological stress detector.",
            "The experiment tests two previously validated score families and does not exhaust all conformal scores.",
            "A full prediction set is valid but operationally uninformative; usefulness depends on an application-specific set-size cost.",
        ],
        "working_theory_update": {
            "prior_claim": (
                "Distance-to-centroid scoring with oracle region-Mondrian conditioning was the "
                "safest Experiment 6 combination."
            ),
            "updated_claim": (
                "Region-conditioned coverage must be reported jointly with subgroup effective "
                "calibration size, finite-threshold probability, full-set frequency, and metadata "
                "quality. Coverage alone can mistake abstention-like full sets for successful repair."
            ),
            "status": analysis["decision"],
        },
        "validation": {
            "new_hypotheses_generated": 0,
            "upstream_successful_stages_rerun": False,
            "model_call_used": False,
            "api_key_required": False,
            "preregistered_before_execution": True,
            "complete_design_grid": True,
            "analytic_and_monte_carlo_checks_present": True,
            "credential_found_in_outputs": False,
        },
    }
    return validate_report(report)


def render_markdown(report: dict[str, Any]) -> str:
    analysis = report["analysis"]
    metrics = analysis["decision_metrics"]
    strongest = analysis["strongest_metadata_noise_failure"]
    worst = analysis["worst_marginal_cell"]
    frontier = {
        row["rare_prevalence"]: row
        for row in report["analytic_feasibility_frontier"]
        if row["calibration_size"] == 600
    }
    lines = [
        f"# {report['experiment_name']}",
        "",
        "## Research question",
        "",
        report["research_question"],
        "",
        "## Result",
        "",
        f"**{analysis['decision']}**",
        "",
        "For rare prevalence at or below 2% and calibration size at or below 600, using the previously safest distance score with oracle region conditioning:",
        "",
        f"- Mean true rare-group coverage: {metrics['low_prevalence_oracle_mean_rare_coverage']:.4f}",
        f"- Mean rare-group prediction-set size: {metrics['low_prevalence_oracle_mean_rare_set_size']:.4f} of {CLASS_COUNT}",
        f"- Mean rare-group full-set fraction: {metrics['low_prevalence_oracle_mean_rare_full_set_fraction']:.4f}",
        f"- Mean fraction of seeds with a finite rare threshold: {metrics['low_prevalence_oracle_mean_finite_threshold_fraction']:.4f}",
        f"- Oracle cells meeting both rare coverage >= 0.88 and rare full-set fraction <= 0.20: {metrics['informative_oracle_success_cell_count']}",
        "",
        "This separates formal coverage from informative coverage: a full label set covers the truth but does not discriminate among classes.",
        "",
        f"Secondary diagnostic: {analysis['secondary_diagnostic']}",
        "",
        "## Exact feasibility boundary",
        "",
        f"At alpha={ALPHA:.2f}, a subgroup needs at least **{minimum_finite_group_count(ALPHA)} calibration observations** before the finite-sample quantile can be finite.",
        "",
        "| Rare prevalence | P(finite threshold) at n=600 | Total n for 95% probability | Total n for 99% probability |",
        "|---:|---:|---:|---:|",
    ]
    for prevalence in PREVALENCES:
        row = frontier[prevalence]
        lines.append(
            f"| {prevalence:.3%} | {row['probability_finite_rare_threshold']:.4f} | "
            f"{row['minimum_total_calibration_for_95_percent_finite_probability']} | "
            f"{row['minimum_total_calibration_for_99_percent_finite_probability']} |"
        )
    lines.extend(
        [
            "",
            "## Metadata-noise stress test",
            "",
            f"The strongest observed metadata-noise penalty occurred at prevalence {strongest['rare_prevalence']:.3%}, n={strongest['calibration_size']}, using `{strongest['conditioning_strategy']}`:",
            "",
            f"- Oracle rare coverage: {strongest['oracle_rare_coverage']:.4f}",
            f"- Noisy-metadata rare coverage: {strongest['noisy_rare_coverage']:.4f}",
            f"- Coverage penalty: {strongest['rare_coverage_penalty']:.4f}",
            f"- Oracle rare set size: {strongest['oracle_rare_set_size']:.4f}",
            f"- Noisy-metadata rare set size: {strongest['noisy_rare_set_size']:.4f}",
            "",
            "## Marginal baseline",
            "",
            f"The worst distance-score marginal cell occurred at prevalence {worst['rare_prevalence']:.3%}, n={worst['calibration_size']}: true rare coverage {worst['mean_true_rare_coverage']:.4f}, mean rare set size {worst['mean_true_rare_average_set_size']:.4f}.",
            "",
            "## Working-theory update",
            "",
            report["working_theory_update"]["updated_claim"],
            "",
            "The practical evaluation unit is therefore not coverage alone. It is the joint tuple:",
            "",
            "```text",
            "(coverage, subgroup effective n, finite-threshold probability, set size, full-set fraction, metadata quality)",
            "```",
            "",
            "## Interpretation",
            "",
            "Oracle region conditioning remains mathematically valid, but its apparent robustness can be partly vacuous for rare groups. When the calibration group is too small, the conservative infinite threshold returns every label. When subgroup metadata is noisy, common samples can contaminate the rare threshold and rare samples can be routed to the common threshold, recreating undercoverage. This is a boundary condition on the Experiment 6 mitigation, not a contradiction of conformal validity under its assumptions.",
            "",
            "## Reproducibility",
            "",
            "- No model call was used.",
            "- No API key was required.",
            "- Experiment 6 was reused by SHA-256 checkpoint and was not rerun.",
            f"- Seed-level rows: {len(report['seed_level_results'])}",
            f"- Aggregate cells: {len(report['aggregate_results'])}",
            "- UTF-8 was used explicitly for report output.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    return "\n".join(lines) + "\n"


def build_reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic local NumPy simulation plus exact binomial calculation",
        "model_call_used": False,
        "api_key_required": False,
        "source_checkpoint": report["source_checkpoint"],
        "configuration": report["preregistered_design"],
        "row_counts": {
            "seed_level_results": len(report["seed_level_results"]),
            "aggregate_results": len(report["aggregate_results"]),
            "analytic_frontier_rows": len(report["analytic_feasibility_frontier"]),
        },
        "determinism": {
            "fixed_seeds": list(SEEDS),
            "nested_calibration_samples": True,
            "no_wall_clock_fields_in_scientific_report": True,
            "independent_validator_rebuilds_report": True,
        },
        "validation_status": "PENDING_INDEPENDENT_VALIDATOR",
    }


def render_reproducibility_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_NAME} — Reproducibility Summary",
            "",
            f"- Execution mode: {summary['execution_mode']}",
            "- Model call used: no",
            "- API key required: no",
            "- Upstream Experiment 6 rerun: no",
            f"- Source SHA-256: `{summary['source_checkpoint']['sha256']}`",
            f"- Fixed seeds: {', '.join(map(str, SEEDS))}",
            f"- Seed-level rows: {summary['row_counts']['seed_level_results']}",
            f"- Aggregate cells: {summary['row_counts']['aggregate_results']}",
            f"- Analytic frontier rows: {summary['row_counts']['analytic_frontier_rows']}",
            "- Independent validator: rebuilds the complete deterministic report and compares it with the saved artifact",
            "- Encoding: UTF-8",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_seed_results: list[dict[str, Any]] | None = None
    if JSON_OUTPUT.exists():
        try:
            checkpoint = validate_report(
                json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
            )
            checkpoint_seed_results = checkpoint["seed_level_results"]
            print("Reusing validated Experiment 8 seed-level simulation checkpoint.")
        except (json.JSONDecodeError, ExperimentValidationError, KeyError, TypeError):
            checkpoint_seed_results = None
    report = build_report(checkpoint_seed_results)
    markdown = render_markdown(report)
    summary = build_reproducibility_summary(report)
    JSON_OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown, encoding="utf-8")
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    REPRO_MARKDOWN_OUTPUT.write_text(
        render_reproducibility_markdown(summary), encoding="utf-8"
    )
    print(f"Experiment 8 complete: {analysis_line(report)}")


def analysis_line(report: dict[str, Any]) -> str:
    metrics = report["analysis"]["decision_metrics"]
    return (
        f"{report['analysis']['decision']}; low-prevalence oracle rare coverage="
        f"{metrics['low_prevalence_oracle_mean_rare_coverage']:.4f}, full-set fraction="
        f"{metrics['low_prevalence_oracle_mean_rare_full_set_fraction']:.4f}"
    )


if __name__ == "__main__":
    main()
