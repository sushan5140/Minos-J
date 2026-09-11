"""Execute Meno-J Experiment 9 on integrity-validated WESAD data."""

from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import (
    _conformal_quantile,
    _fit_regularized_lda,
    _model_outputs,
    _score_matrix,
)
from wesad_utils import load_wesad_subject


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
CHECKPOINT_DIR = PROJECT_DIR / "work" / "experiment_9_checkpoints"
FEATURE_DIR = CHECKPOINT_DIR / "features"
INTEGRITY_PATH = OUTPUT_DIR / "meno_j_experiment_9_wesad_integrity.json"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_9_preregistered_protocol.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_real_data.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_real_data.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_reproducibility_summary.md"

EXPERIMENT_NAME = "Meno-J Experiment 9: WESAD Real-Data Falsification Study"
SUBJECTS = (
    "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11",
    "S13", "S14", "S15", "S16", "S17",
)
LABEL_NAMES = {1: "baseline", 2: "stress", 3: "amusement"}
SAMPLE_RATE = 700
WINDOW_SECONDS = 60
WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_SECONDS
ALPHA = 0.10
TARGET = 1.0 - ALPHA
REPETITIONS = 3
SCORES = (
    "margin_score",
    "inverse_probability_score",
    "distance_to_class_centroid_score",
)
STRATEGIES = ("marginal", "mondrian_class", "mondrian_motion_region")
SCALAR_CHANNELS = ("ECG", "EMG", "EDA", "Temp", "Resp")
STATISTICS = (
    "mean", "std", "q05", "median", "q95", "q90_range", "rms", "slope_per_second", "mean_abs_diff"
)
FEATURE_VERSION = "wesad_chest_60s_v1"
WINDOW_TIME_CENTERED = np.arange(WINDOW_SAMPLES, dtype=np.float64)
WINDOW_TIME_CENTERED -= WINDOW_TIME_CENTERED.mean()
WINDOW_TIME_DENOMINATOR = float(np.dot(WINDOW_TIME_CENTERED, WINDOW_TIME_CENTERED))


class Experiment9Error(RuntimeError):
    """Raised when Experiment 9 violates its frozen contract."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise Experiment9Error(f"Required validated JSON is unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise Experiment9Error(f"Required JSON is not an object: {path}")
    return value


def _verify_sources() -> tuple[dict[str, Any], dict[str, Any], Path, dict[str, str]]:
    integrity = _read_json(INTEGRITY_PATH)
    protocol = _read_json(PROTOCOL_PATH)
    if integrity.get("status") != "PASS":
        raise Experiment9Error("WESAD integrity report has not passed.")
    if protocol.get("protocol_status") != "FROZEN_BEFORE_COVERAGE_ANALYSIS":
        raise Experiment9Error("Experiment 9 protocol is not frozen.")
    if set(integrity.get("subjects", {}).get("found", [])) != set(SUBJECTS):
        raise Experiment9Error("WESAD subject inventory differs from the frozen protocol.")
    root = Path(integrity["extraction"]["resolved_root"])
    manifest_hashes = {
        row["relative_path"]: row["sha256"]
        for row in integrity["file_manifest"]
    }
    return integrity, protocol, root, manifest_hashes


def _statistics(values: np.ndarray) -> list[float]:
    x = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.isfinite(x).all():
        raise Experiment9Error("Non-finite raw signal value encountered.")
    q05, median, q95 = np.quantile(x, (0.05, 0.50, 0.95))
    mean = float(x.mean())
    slope = (
        float(np.dot(WINDOW_TIME_CENTERED, x - mean) / WINDOW_TIME_DENOMINATOR * SAMPLE_RATE)
        if len(x) == WINDOW_SAMPLES and WINDOW_TIME_DENOMINATOR > 0
        else 0.0
    )
    return [
        mean,
        float(x.std(ddof=0)),
        float(q05),
        float(median),
        float(q95),
        float(q95 - q05),
        float(np.sqrt(np.mean(x * x))),
        slope,
        float(np.mean(np.abs(np.diff(x)))) if len(x) > 1 else 0.0,
    ]


def feature_names() -> list[str]:
    channels = [*SCALAR_CHANNELS, "ACC_X", "ACC_Y", "ACC_Z", "ACC_MAG"]
    return [f"{channel}_{statistic}" for channel in channels for statistic in STATISTICS]


def _continuous_runs(labels: np.ndarray) -> list[tuple[int, int, int]]:
    changes = np.flatnonzero(labels[1:] != labels[:-1]) + 1
    boundaries = np.concatenate(([0], changes, [len(labels)]))
    return [
        (int(boundaries[index]), int(boundaries[index + 1]), int(labels[boundaries[index]]))
        for index in range(len(boundaries) - 1)
    ]


def _extract_subject_features(subject_id: str, path: Path) -> dict[str, np.ndarray]:
    payload = load_wesad_subject(path)
    if str(payload.get("subject")) != subject_id:
        raise Experiment9Error(f"Subject identity mismatch in {path}")
    labels = np.asarray(payload.get("label"), dtype=np.int32)
    chest = payload.get("signal", {}).get("chest", {})
    required = {*SCALAR_CHANNELS, "ACC"}
    if not isinstance(chest, dict) or not required.issubset(chest):
        raise Experiment9Error(f"Required chest signals missing for {subject_id}")
    if any(len(np.asarray(chest[name])) != len(labels) for name in required):
        raise Experiment9Error(f"Chest signal/label length mismatch for {subject_id}")

    rows: list[list[float]] = []
    window_labels: list[int] = []
    starts: list[float] = []
    phases: list[int] = []
    for run_start, run_end, label in _continuous_runs(labels):
        if label not in LABEL_NAMES:
            continue
        window_count = (run_end - run_start) // WINDOW_SAMPLES
        for window_index in range(window_count):
            start = run_start + window_index * WINDOW_SAMPLES
            end = start + WINDOW_SAMPLES
            values: list[float] = []
            for channel in SCALAR_CHANNELS:
                values.extend(_statistics(np.asarray(chest[channel])[start:end]))
            acceleration = np.asarray(chest["ACC"])[start:end]
            for axis in range(3):
                values.extend(_statistics(acceleration[:, axis]))
            values.extend(_statistics(np.linalg.norm(acceleration, axis=1)))
            rows.append(values)
            window_labels.append(label)
            starts.append(start / SAMPLE_RATE)
            phases.append(min(2, int(3 * window_index / max(1, window_count))))
    features = np.asarray(rows, dtype=np.float64)
    expected_width = len(feature_names())
    if features.ndim != 2 or features.shape[1] != expected_width:
        raise Experiment9Error(f"Feature width mismatch for {subject_id}: {features.shape}")
    if not np.isfinite(features).all():
        raise Experiment9Error(f"Non-finite feature generated for {subject_id}")
    return {
        "features": features,
        "labels": np.asarray(window_labels, dtype=np.int32),
        "start_seconds": np.asarray(starts, dtype=np.float64),
        "phase": np.asarray(phases, dtype=np.int8),
    }


def _load_or_extract_features(
    root: Path,
    manifest_hashes: dict[str, str],
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    all_subjects: dict[str, dict[str, np.ndarray]] = {}
    summaries: list[dict[str, Any]] = []
    names = np.asarray(feature_names(), dtype="U64")
    for subject_id in SUBJECTS:
        relative = f"{subject_id}/{subject_id}.pkl"
        source_hash = manifest_hashes.get(relative)
        if source_hash is None:
            raise Experiment9Error(f"Integrity manifest lacks {relative}")
        checkpoint = FEATURE_DIR / f"{subject_id}.npz"
        data: dict[str, np.ndarray] | None = None
        if checkpoint.exists():
            with np.load(checkpoint, allow_pickle=False) as saved:
                if (
                    str(saved["feature_version"].item()) == FEATURE_VERSION
                    and str(saved["source_sha256"].item()) == source_hash
                    and saved["feature_names"].tolist() == names.tolist()
                ):
                    data = {
                        "features": saved["features"],
                        "labels": saved["labels"],
                        "start_seconds": saved["start_seconds"],
                        "phase": saved["phase"],
                    }
                    print(f"Reused feature checkpoint: {subject_id}", flush=True)
        if data is None:
            print(f"Extracting verified WESAD features: {subject_id}", flush=True)
            data = _extract_subject_features(subject_id, root / relative)
            temporary = checkpoint.with_suffix(".tmp")
            with temporary.open("wb") as handle:
                np.savez_compressed(
                    handle,
                    **data,
                    feature_names=names,
                    feature_version=np.asarray(FEATURE_VERSION),
                    source_sha256=np.asarray(source_hash),
                )
            temporary.replace(checkpoint)
            gc.collect()
        if not set(np.unique(data["labels"]).tolist()).issubset(LABEL_NAMES):
            raise Experiment9Error(f"Unexpected checkpoint label for {subject_id}")
        all_subjects[subject_id] = data
        unique, counts = np.unique(data["labels"], return_counts=True)
        summaries.append(
            {
                "subject_id": subject_id,
                "window_count": int(len(data["labels"])),
                "class_counts": {
                    LABEL_NAMES[int(label)]: int(count)
                    for label, count in zip(unique, counts)
                },
                "checkpoint_path": str(checkpoint.resolve()),
                "checkpoint_sha256": _sha256(checkpoint),
                "source_pickle_sha256": source_hash,
            }
        )
    return all_subjects, summaries


def _coverage_mapping(covered: np.ndarray, groups: np.ndarray) -> tuple[dict[str, float], dict[str, int]]:
    coverage: dict[str, float] = {}
    counts: dict[str, int] = {}
    for group in sorted(np.unique(groups).tolist(), key=str):
        mask = groups == group
        coverage[str(group)] = float(covered[mask].mean())
        counts[str(group)] = int(mask.sum())
    return coverage, counts


def _evaluate_sets(
    calibration_scores: np.ndarray,
    calibration_labels: np.ndarray,
    calibration_motion: np.ndarray,
    test_scores: np.ndarray,
    test_labels: np.ndarray,
    test_motion: np.ndarray,
    test_phase: np.ndarray,
    strategy: str,
) -> dict[str, Any]:
    true_scores = calibration_scores[np.arange(len(calibration_labels)), calibration_labels]
    finite_thresholds: list[bool] = []
    if strategy == "marginal":
        threshold = _conformal_quantile(true_scores, ALPHA)
        prediction_sets = test_scores <= threshold
        finite_thresholds = [bool(np.isfinite(threshold))]
    elif strategy == "mondrian_class":
        thresholds = np.asarray(
            [_conformal_quantile(true_scores[calibration_labels == label], ALPHA) for label in range(3)]
        )
        prediction_sets = test_scores <= thresholds[None, :]
        finite_thresholds = np.isfinite(thresholds).tolist()
    elif strategy == "mondrian_motion_region":
        thresholds = {
            int(region): _conformal_quantile(true_scores[calibration_motion == region], ALPHA)
            for region in (0, 1)
        }
        row_thresholds = np.asarray([thresholds[int(region)] for region in test_motion])
        prediction_sets = test_scores <= row_thresholds[:, None]
        finite_thresholds = [bool(np.isfinite(thresholds[region])) for region in (0, 1)]
    else:
        raise Experiment9Error(f"Unknown conditioning strategy: {strategy}")
    covered = prediction_sets[np.arange(len(test_labels)), test_labels]
    set_sizes = prediction_sets.sum(axis=1)
    class_names = np.asarray([LABEL_NAMES[int(label + 1)] for label in test_labels])
    motion_names = np.where(test_motion == 1, "high_motion", "low_motion")
    phase_names = np.asarray([("early", "middle", "late")[int(value)] for value in test_phase])
    by_class, class_counts = _coverage_mapping(covered, class_names)
    by_motion, motion_counts = _coverage_mapping(covered, motion_names)
    by_phase, phase_counts = _coverage_mapping(covered, phase_names)
    group_values = [*by_class.values(), *by_motion.values(), *by_phase.values()]
    return {
        "coverage": float(covered.mean()),
        "coverage_by_class": by_class,
        "class_counts": class_counts,
        "coverage_by_motion_region": by_motion,
        "motion_region_counts": motion_counts,
        "coverage_by_temporal_tertile": by_phase,
        "temporal_tertile_counts": phase_counts,
        "minimum_reported_group_coverage": float(min(group_values)),
        "maximum_reported_group_gap": float(max(abs(value - TARGET) for value in group_values)),
        "average_set_size": float(set_sizes.mean()),
        "full_set_frequency": float(np.mean(set_sizes == 3)),
        "empty_set_frequency": float(np.mean(set_sizes == 0)),
        "finite_threshold_fraction": float(np.mean(finite_thresholds)),
    }


def run_folds(subject_data: dict[str, dict[str, np.ndarray]]) -> list[dict[str, Any]]:
    motion_feature_index = feature_names().index("ACC_MAG_std")
    rows: list[dict[str, Any]] = []
    for test_index, test_subject in enumerate(SUBJECTS):
        remaining = [subject for subject in SUBJECTS if subject != test_subject]
        for repetition in range(REPETITIONS):
            offset = (test_index + repetition * 4) % len(remaining)
            calibration_subjects = [remaining[(offset + index) % len(remaining)] for index in range(4)]
            training_subjects = [subject for subject in remaining if subject not in calibration_subjects]
            if len(training_subjects) != 10 or len(set(calibration_subjects)) != 4:
                raise Experiment9Error("Invalid subject-disjoint fold construction.")
            train_x = np.concatenate([subject_data[s]["features"] for s in training_subjects])
            train_y = np.concatenate([subject_data[s]["labels"] for s in training_subjects]) - 1
            calibration_x = np.concatenate([subject_data[s]["features"] for s in calibration_subjects])
            calibration_y = np.concatenate([subject_data[s]["labels"] for s in calibration_subjects]) - 1
            test_x = subject_data[test_subject]["features"]
            test_y = subject_data[test_subject]["labels"] - 1
            motion_threshold = float(np.median(calibration_x[:, motion_feature_index]))
            calibration_motion = (calibration_x[:, motion_feature_index] >= motion_threshold).astype(int)
            test_motion = (test_x[:, motion_feature_index] >= motion_threshold).astype(int)
            model = _fit_regularized_lda(train_x, train_y)
            calibration_probabilities, calibration_distances = _model_outputs(model, calibration_x)
            test_probabilities, test_distances = _model_outputs(model, test_x)
            for score_type in SCORES:
                calibration_scores = _score_matrix(
                    score_type, calibration_probabilities, calibration_distances
                )
                test_scores = _score_matrix(score_type, test_probabilities, test_distances)
                for strategy in STRATEGIES:
                    metrics = _evaluate_sets(
                        calibration_scores,
                        calibration_y,
                        calibration_motion,
                        test_scores,
                        test_y,
                        test_motion,
                        subject_data[test_subject]["phase"],
                        strategy,
                    )
                    rows.append(
                        {
                            "test_subject": test_subject,
                            "repetition": repetition,
                            "training_subjects": training_subjects,
                            "calibration_subjects": calibration_subjects,
                            "test_window_count": int(len(test_y)),
                            "calibration_window_count": int(len(calibration_y)),
                            "motion_threshold": motion_threshold,
                            "score_type": score_type,
                            "conditioning_strategy": strategy,
                            **metrics,
                        }
                    )
    return rows


def aggregate_folds(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for score in SCORES:
        for strategy in STRATEGIES:
            cells = [
                row for row in rows
                if row["score_type"] == score and row["conditioning_strategy"] == strategy
            ]
            subject_coverage = {
                subject: float(np.mean([row["coverage"] for row in cells if row["test_subject"] == subject]))
                for subject in SUBJECTS
            }
            numeric = (
                "coverage", "minimum_reported_group_coverage", "maximum_reported_group_gap",
                "average_set_size", "full_set_frequency", "empty_set_frequency", "finite_threshold_fraction",
            )
            aggregate: dict[str, Any] = {
                "score_type": score,
                "conditioning_strategy": strategy,
                "fold_count": len(cells),
                "subject_mean_coverage": subject_coverage,
                "worst_subject_mean_coverage": float(min(subject_coverage.values())),
                "best_subject_mean_coverage": float(max(subject_coverage.values())),
                "subject_coverage_range": float(max(subject_coverage.values()) - min(subject_coverage.values())),
            }
            for field in numeric:
                values = np.asarray([row[field] for row in cells], dtype=float)
                aggregate[f"mean_{field}"] = float(values.mean())
                aggregate[f"std_{field}"] = float(values.std(ddof=0))
            aggregate["severe_undercoverage_fold_fraction"] = float(
                np.mean([row["coverage"] < 0.75 for row in cells])
            )
            aggregates.append(aggregate)
    for row in aggregates:
        row["robustness_score"] = float(
            abs(row["mean_coverage"] - TARGET)
            + max(0.0, TARGET - row["worst_subject_mean_coverage"])
            + 0.25 * row["mean_full_set_frequency"]
            + 0.10 * row["mean_empty_set_frequency"]
        )
    return aggregates


def _find_aggregate(aggregates: list[dict[str, Any]], score: str, strategy: str) -> dict[str, Any]:
    matches = [
        row for row in aggregates
        if row["score_type"] == score and row["conditioning_strategy"] == strategy
    ]
    if len(matches) != 1:
        raise Experiment9Error("Unable to identify unique aggregate comparison cell.")
    return matches[0]


def _paired_bootstrap_ci(
    safe: dict[str, float], danger: dict[str, float], seed: int = 90210
) -> dict[str, float]:
    differences = np.asarray([safe[s] - danger[s] for s in SUBJECTS], dtype=float)
    rng = np.random.default_rng(seed)
    bootstrap = np.asarray(
        [rng.choice(differences, size=len(differences), replace=True).mean() for _ in range(5000)]
    )
    return {
        "paired_subject_mean_difference": float(differences.mean()),
        "bootstrap_95_percent_lower": float(np.quantile(bootstrap, 0.025)),
        "bootstrap_95_percent_upper": float(np.quantile(bootstrap, 0.975)),
        "bootstrap_iterations": 5000,
        "bootstrap_seed": seed,
    }


def analyze(rows: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(aggregates, key=lambda row: row["robustness_score"])
    safest = _find_aggregate(
        aggregates, "distance_to_class_centroid_score", "mondrian_motion_region"
    )
    danger = _find_aggregate(aggregates, "inverse_probability_score", "marginal")
    worst_subject_improvement = (
        safest["worst_subject_mean_coverage"] - danger["worst_subject_mean_coverage"]
    )
    full_set_increase = safest["mean_full_set_frequency"] - danger["mean_full_set_frequency"]
    transfer_supported = bool(worst_subject_improvement >= 0.05 and full_set_increase <= 0.20)

    best = ranked[0]
    best_cells = [
        row for row in rows
        if row["score_type"] == best["score_type"]
        and row["conditioning_strategy"] == best["conditioning_strategy"]
    ]
    motion_gaps = [
        abs(row["coverage_by_motion_region"].get("high_motion", np.nan) - row["coverage_by_motion_region"].get("low_motion", np.nan))
        for row in best_cells
    ]
    phase_gaps = [
        max(row["coverage_by_temporal_tertile"].values())
        - min(row["coverage_by_temporal_tertile"].values())
        for row in best_cells
    ]
    method_worst_coverage_spread = float(
        max(row["worst_subject_mean_coverage"] for row in aggregates)
        - min(row["worst_subject_mean_coverage"] for row in aggregates)
    )
    return {
        "primary_transfer_decision": (
            "SYNTHETIC_SAFEST_PAIR_TRANSFERS" if transfer_supported
            else "SYNTHETIC_SAFEST_PAIR_DOES_NOT_TRANSFER"
        ),
        "primary_transfer_metrics": {
            "safe_pair": {
                "score_type": safest["score_type"],
                "conditioning_strategy": safest["conditioning_strategy"],
                "worst_subject_mean_coverage": safest["worst_subject_mean_coverage"],
                "mean_coverage": safest["mean_coverage"],
                "mean_full_set_frequency": safest["mean_full_set_frequency"],
                "mean_average_set_size": safest["mean_average_set_size"],
            },
            "danger_pair": {
                "score_type": danger["score_type"],
                "conditioning_strategy": danger["conditioning_strategy"],
                "worst_subject_mean_coverage": danger["worst_subject_mean_coverage"],
                "mean_coverage": danger["mean_coverage"],
                "mean_full_set_frequency": danger["mean_full_set_frequency"],
                "mean_average_set_size": danger["mean_average_set_size"],
            },
            "worst_subject_coverage_improvement": float(worst_subject_improvement),
            "full_set_frequency_increase": float(full_set_increase),
            "support_threshold_met": transfer_supported,
            "paired_subject_bootstrap": _paired_bootstrap_ci(
                safest["subject_mean_coverage"], danger["subject_mean_coverage"]
            ),
        },
        "robustness_ranking": [
            {
                "rank": index,
                "score_type": row["score_type"],
                "conditioning_strategy": row["conditioning_strategy"],
                "robustness_score": row["robustness_score"],
                "mean_coverage": row["mean_coverage"],
                "worst_subject_mean_coverage": row["worst_subject_mean_coverage"],
                "mean_set_size": row["mean_average_set_size"],
                "mean_full_set_frequency": row["mean_full_set_frequency"],
            }
            for index, row in enumerate(ranked, start=1)
        ],
        "structural_diagnostics": {
            "method_worst_subject_coverage_spread": method_worst_coverage_spread,
            "score_conditioning_sensitivity_observed": method_worst_coverage_spread >= 0.05,
            "best_pair_subject_coverage_range": best["subject_coverage_range"],
            "subject_heterogeneity_observed": best["subject_coverage_range"] >= 0.10,
            "best_pair_mean_motion_region_coverage_gap": float(np.nanmean(motion_gaps)),
            "motion_region_difference_observed": float(np.nanmean(motion_gaps)) >= 0.10,
            "best_pair_mean_temporal_tertile_coverage_gap": float(np.mean(phase_gaps)),
            "temporal_difference_observed": float(np.mean(phase_gaps)) >= 0.10,
        },
    }


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment9Error("Experiment 9 name mismatch.")
    if len(report.get("subject_feature_summary", [])) != 15:
        raise Experiment9Error("Experiment 9 must contain 15 subject feature summaries.")
    expected_folds = len(SUBJECTS) * REPETITIONS * len(SCORES) * len(STRATEGIES)
    if len(report.get("fold_results", [])) != expected_folds:
        raise Experiment9Error("Experiment 9 fold grid is incomplete.")
    if len(report.get("aggregate_results", [])) != len(SCORES) * len(STRATEGIES):
        raise Experiment9Error("Experiment 9 aggregate grid is incomplete.")
    keys = {
        (row["test_subject"], row["repetition"], row["score_type"], row["conditioning_strategy"])
        for row in report["fold_results"]
    }
    if len(keys) != expected_folds:
        raise Experiment9Error("Experiment 9 fold keys are duplicated or missing.")
    for row in report["fold_results"]:
        if set(row["training_subjects"]) & set(row["calibration_subjects"]):
            raise Experiment9Error("Train/calibration subject leakage detected.")
        if row["test_subject"] in row["training_subjects"] or row["test_subject"] in row["calibration_subjects"]:
            raise Experiment9Error("Test-subject leakage detected.")
        if len(row["training_subjects"]) != 10 or len(row["calibration_subjects"]) != 4:
            raise Experiment9Error("Fold subject count mismatch.")
        for field in (
            "coverage", "minimum_reported_group_coverage", "full_set_frequency",
            "empty_set_frequency", "finite_threshold_fraction",
        ):
            if not 0.0 <= row[field] <= 1.0:
                raise Experiment9Error(f"Fold metric outside [0,1]: {field}")
        if not 0.0 <= row["average_set_size"] <= 3.0:
            raise Experiment9Error("Prediction-set size outside [0,3].")
    validation = report.get("validation", {})
    if validation.get("integrity_gate_passed") is not True:
        raise Experiment9Error("Integrity gate was not passed.")
    if validation.get("model_call_used") is not False or validation.get("api_key_required") is not False:
        raise Experiment9Error("Experiment 9 unexpectedly used an LLM or API key.")
    return report


def build_report() -> dict[str, Any]:
    integrity, protocol, root, manifest_hashes = _verify_sources()
    subject_data, feature_summary = _load_or_extract_features(root, manifest_hashes)
    fold_results = run_folds(subject_data)
    aggregates = aggregate_folds(fold_results)
    analysis = analyze(fold_results, aggregates)
    total_class_counts = {
        name: int(sum(row["class_counts"].get(name, 0) for row in feature_summary))
        for name in LABEL_NAMES.values()
    }
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": (
            "Do score and conditioning choices explain subject-level variation in conformal "
            "coverage on real WESAD physiological stress windows, and does the synthetic safest "
            "pair transfer without becoming uninformative?"
        ),
        "source_integrity": {
            "path": str(INTEGRITY_PATH.resolve()),
            "sha256": _sha256(INTEGRITY_PATH),
            "archive_sha256": integrity["archive"]["sha256"],
            "status": integrity["status"],
        },
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "feature_contract": {
            "version": FEATURE_VERSION,
            "window_seconds": WINDOW_SECONDS,
            "sampling_rate_hz": SAMPLE_RATE,
            "feature_count": len(feature_names()),
            "feature_names": feature_names(),
            "included_labels": {str(key): value for key, value in LABEL_NAMES.items()},
            "transition_windows_excluded": True,
        },
        "subject_feature_summary": feature_summary,
        "total_window_count": int(sum(row["window_count"] for row in feature_summary)),
        "total_class_counts": total_class_counts,
        "fold_contract": {
            "test_subject_count": len(SUBJECTS),
            "repetitions_per_subject": REPETITIONS,
            "training_subjects_per_fold": 10,
            "calibration_subjects_per_fold": 4,
            "test_subjects_per_fold": 1,
            "target_coverage": TARGET,
            "scores": list(SCORES),
            "conditioning_strategies": list(STRATEGIES),
        },
        "fold_results": fold_results,
        "aggregate_results": aggregates,
        "analysis": analysis,
        "limitations": [
            "The analysis uses hand-engineered distribution/dynamics features and regularized LDA, not a deep stress detector.",
            "Only chest signals are used in the primary synchronized analysis; wrist modalities require separate sampling-rate alignment.",
            "Fifteen subjects limit precision for subject-level tail-risk estimates.",
            "Motion regions are defined by a calibration-only median split and are not clinical or demographic subgroups.",
            "Observed coverage associations do not establish a causal physiological mechanism.",
        ],
        "validation": {
            "integrity_gate_passed": True,
            "protocol_frozen_before_coverage_analysis": True,
            "restricted_pickle_loader_used": True,
            "subject_disjoint_splits": True,
            "raw_dataset_mutated": False,
            "upstream_successful_stages_rerun": False,
            "model_call_used": False,
            "api_key_required": False,
        },
    }
    return validate_report(report)


def render_markdown(report: dict[str, Any]) -> str:
    analysis = report["analysis"]
    transfer = analysis["primary_transfer_metrics"]
    structural = analysis["structural_diagnostics"]
    lines = [
        f"# {report['experiment_name']}",
        "",
        "## Result",
        "",
        f"**{analysis['primary_transfer_decision']}**",
        "",
        f"- Subjects: {len(report['subject_feature_summary'])}",
        f"- Transition-free 60-second windows: {report['total_window_count']}",
        f"- Class counts: {report['total_class_counts']}",
        f"- Subject-disjoint score/conditioning folds: {len(report['fold_results'])}",
        "",
        "## Primary transfer comparison",
        "",
        "| Pair | Mean coverage | Worst-subject coverage | Set size | Full-set frequency |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("safe_pair", "danger_pair"):
        row = transfer[name]
        lines.append(
            f"| {row['score_type']} + {row['conditioning_strategy']} | {row['mean_coverage']:.4f} | "
            f"{row['worst_subject_mean_coverage']:.4f} | {row['mean_average_set_size']:.4f} | "
            f"{row['mean_full_set_frequency']:.4f} |"
        )
    bootstrap = transfer["paired_subject_bootstrap"]
    lines.extend(
        [
            "",
            f"- Worst-subject coverage improvement: {transfer['worst_subject_coverage_improvement']:.4f}",
            f"- Full-set frequency increase: {transfer['full_set_frequency_increase']:.4f}",
            f"- Paired mean subject coverage difference: {bootstrap['paired_subject_mean_difference']:.4f}",
            f"- Subject-bootstrap 95% interval: [{bootstrap['bootstrap_95_percent_lower']:.4f}, {bootstrap['bootstrap_95_percent_upper']:.4f}]",
            "",
            "## Robustness ranking",
            "",
            "| Rank | Score | Conditioning | Mean coverage | Worst subject | Set size | Full sets |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in analysis["robustness_ranking"]:
        lines.append(
            f"| {row['rank']} | {row['score_type']} | {row['conditioning_strategy']} | "
            f"{row['mean_coverage']:.4f} | {row['worst_subject_mean_coverage']:.4f} | "
            f"{row['mean_set_size']:.4f} | {row['mean_full_set_frequency']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Structural diagnostics",
            "",
            f"- Method spread in worst-subject coverage: {structural['method_worst_subject_coverage_spread']:.4f}",
            f"- Score/conditioning sensitivity observed: {structural['score_conditioning_sensitivity_observed']}",
            f"- Best-pair subject coverage range: {structural['best_pair_subject_coverage_range']:.4f}",
            f"- Subject heterogeneity observed: {structural['subject_heterogeneity_observed']}",
            f"- Best-pair mean motion-region coverage gap: {structural['best_pair_mean_motion_region_coverage_gap']:.4f}",
            f"- Best-pair mean temporal-tertile coverage gap: {structural['best_pair_mean_temporal_tertile_coverage_gap']:.4f}",
            "",
            "## Interpretation guardrail",
            "",
            "These are real-data coverage associations under the frozen protocol. They test whether synthetic score/conditioning rankings transfer; they do not by themselves establish a causal physiological mechanism.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            f"- Archive SHA-256: `{report['source_integrity']['archive_sha256']}`",
            "- Restricted pickle loader: yes",
            "- Subject-disjoint splits: yes",
            "- Model/API call: no",
            "- Raw dataset modified: no",
            "",
        ]
    )
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic local WESAD feature extraction and conformal evaluation",
        "source_integrity_sha256": report["source_integrity"]["sha256"],
        "archive_sha256": report["source_integrity"]["archive_sha256"],
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "feature_version": FEATURE_VERSION,
        "subject_checkpoint_hashes": {
            row["subject_id"]: row["checkpoint_sha256"]
            for row in report["subject_feature_summary"]
        },
        "subject_count": len(report["subject_feature_summary"]),
        "window_count": report["total_window_count"],
        "fold_result_count": len(report["fold_results"]),
        "model_call_used": False,
        "api_key_required": False,
        "validation_status": "PENDING_INDEPENDENT_REPLAY",
    }


def render_reproducibility_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_NAME} — Reproducibility Summary",
            "",
            f"- Execution mode: {summary['execution_mode']}",
            f"- Archive SHA-256: `{summary['archive_sha256']}`",
            f"- Integrity-report SHA-256: `{summary['source_integrity_sha256']}`",
            f"- Protocol SHA-256: `{summary['protocol_sha256']}`",
            f"- Feature version: `{summary['feature_version']}`",
            f"- Subjects: {summary['subject_count']}",
            f"- Windows: {summary['window_count']}",
            f"- Fold results: {summary['fold_result_count']}",
            "- Model call used: no",
            "- API key required: no",
            "- Independent replay: pending",
            "",
        ]
    )


def main() -> None:
    report = build_report()
    summary = reproducibility_summary(report)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    REPRO_MARKDOWN_OUTPUT.write_text(
        render_reproducibility_markdown(summary), encoding="utf-8"
    )
    print(f"Experiment 9 complete: {report['analysis']['primary_transfer_decision']}")
    print(f"Windows: {report['total_window_count']}; fold results: {len(report['fold_results'])}")


if __name__ == "__main__":
    main()
