"""Run Meno-J Experiment 13 on the independent PhysioNet wearable cohort."""

from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import _conformal_quantile


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
DATA_ROOT = PROJECT_DIR / "work" / "e13_data"
STRESS_ROOT = DATA_ROOT / "Wearable_Dataset" / "STRESS"
FEATURE_DIR = PROJECT_DIR / "work" / "experiment_13_checkpoints" / "features"
FOLD_CHECKPOINT = PROJECT_DIR / "work" / "experiment_13_checkpoints" / "fold_results.json"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_13_preregistered_protocol.json"
INTEGRITY_PATH = OUTPUT_DIR / "meno_j_experiment_13_dataset_integrity.json"
INVENTORY_PATH = OUTPUT_DIR / "meno_j_experiment_13_dataset_inventory.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_13_external_replication.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_13_external_replication.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_13_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_13_reproducibility_summary.md"

EXPERIMENT_NAME = "Meno-J Experiment 13: Independent Wearable-Dataset Replication"
WINDOW_SECONDS = 15
EDGE_TRIM_SECONDS = 5.0
PER_CLASS = 16
ONBOARDING_PER_CLASS = 8
ALPHA = 0.10
TARGET = 0.90
REPETITIONS = 3
LABEL_NAMES = {0: "non_stress", 1: "stress"}
ARMS = ("lda_raw", "lda_subject_robust_normalized")
FEATURE_VERSION = "e13_shared_e4_15s_v1"


class Experiment13Error(RuntimeError):
    """Raised when Experiment 13 violates its frozen contract."""


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
        raise Experiment13Error(f"Required valid JSON is unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise Experiment13Error(f"Expected a JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def feature_names() -> list[str]:
    channels = ("EDA", "TEMP", "ACC_X", "ACC_Y", "ACC_Z", "ACC_MAG")
    statistics = ("mean", "std", "min", "max", "median", "q25", "q75", "rms", "madiff")
    return [f"{channel}_{statistic}" for channel in channels for statistic in statistics]


def _statistics(values: np.ndarray) -> list[float]:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)):
        raise Experiment13Error("A feature window contains invalid signal values.")
    return [
        float(values.mean()),
        float(values.std()),
        float(values.min()),
        float(values.max()),
        float(np.median(values)),
        float(np.quantile(values, 0.25)),
        float(np.quantile(values, 0.75)),
        float(np.sqrt(np.mean(values * values))),
        float(np.mean(np.abs(np.diff(values)))) if len(values) > 1 else 0.0,
    ]


def _load_signal(path: Path) -> tuple[datetime, float, np.ndarray]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rate_row = next(reader)
    start = datetime.fromisoformat(header[0].strip())
    rate = float(rate_row[0])
    values = np.loadtxt(path, delimiter=",", skiprows=2, dtype=np.float64, ndmin=2)
    if not np.all(np.isfinite(values)):
        raise Experiment13Error(f"Non-finite raw signal value: {path}")
    return start, rate, values


def _window_candidates(subject_row: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for interval in subject_row["labeled_intervals"]:
        start = datetime.fromisoformat(interval["start_iso"])
        usable = interval["duration_seconds"] - 2 * EDGE_TRIM_SECONDS
        count = int(np.floor(max(0.0, usable) / WINDOW_SECONDS))
        for index in range(count):
            window_start = start.timestamp() + EDGE_TRIM_SECONDS + index * WINDOW_SECONDS
            candidates.append(
                {
                    "start_timestamp": float(window_start),
                    "start_iso": datetime.fromtimestamp(window_start).isoformat(sep=" "),
                    "label": 1 if interval["label"] == "stress" else 0,
                    "stage": interval["stage"],
                }
            )
    selected: list[dict[str, Any]] = []
    for label in LABEL_NAMES:
        class_candidates = sorted(
            [row for row in candidates if row["label"] == label],
            key=lambda row: row["start_timestamp"],
        )
        if len(class_candidates) < PER_CLASS:
            raise Experiment13Error(
                f"Subject has only {len(class_candidates)} candidates for label {label}."
            )
        positions = np.rint(np.linspace(0, len(class_candidates) - 1, PER_CLASS)).astype(int)
        if len(set(positions.tolist())) != PER_CLASS:
            raise Experiment13Error("Evenly spaced window selection produced duplicate indices.")
        selected.extend(class_candidates[position] for position in positions)
    return sorted(selected, key=lambda row: row["start_timestamp"])


def _extract_subject_features(subject_row: dict[str, Any]) -> dict[str, np.ndarray]:
    subject = subject_row["subject_folder"]
    folder = STRESS_ROOT / subject
    eda_start, eda_rate, eda = _load_signal(folder / "EDA.csv")
    temp_start, temp_rate, temp = _load_signal(folder / "TEMP.csv")
    acc_start, acc_rate, acc = _load_signal(folder / "ACC.csv")
    if not (eda_rate == temp_rate == 4.0 and acc_rate == 32.0):
        raise Experiment13Error(f"Unexpected sampling rate for {subject}.")
    if not (eda_start == temp_start == acc_start):
        raise Experiment13Error(f"Shared sensor start mismatch for {subject}.")
    acc = acc / 64.0
    acc_magnitude = np.sqrt(np.sum(acc * acc, axis=1))
    candidates = _window_candidates(subject_row)
    rows: list[list[float]] = []
    for candidate in candidates:
        offset = candidate["start_timestamp"] - eda_start.timestamp()
        eda_left = int(round(offset * eda_rate))
        acc_left = int(round(offset * acc_rate))
        eda_right = eda_left + int(WINDOW_SECONDS * eda_rate)
        acc_right = acc_left + int(WINDOW_SECONDS * acc_rate)
        if eda_left < 0 or acc_left < 0 or eda_right > len(eda) or acc_right > len(acc):
            raise Experiment13Error(f"Selected window exceeds shared signals for {subject}.")
        channels = (
            eda[eda_left:eda_right, 0],
            temp[eda_left:eda_right, 0],
            acc[acc_left:acc_right, 0],
            acc[acc_left:acc_right, 1],
            acc[acc_left:acc_right, 2],
            acc_magnitude[acc_left:acc_right],
        )
        rows.append([value for channel in channels for value in _statistics(channel)])
    features = np.asarray(rows, dtype=np.float64)
    labels = np.asarray([row["label"] for row in candidates], dtype=np.int32)
    if features.shape != (2 * PER_CLASS, len(feature_names())):
        raise Experiment13Error(f"Feature shape mismatch for {subject}: {features.shape}")
    if {int(label): int(np.sum(labels == label)) for label in LABEL_NAMES} != {0: 16, 1: 16}:
        raise Experiment13Error(f"Balanced label contract failed for {subject}.")
    return {
        "features": features,
        "labels": labels,
        "stages": np.asarray([row["stage"] for row in candidates], dtype="U32"),
        "start_iso": np.asarray([row["start_iso"] for row in candidates], dtype="U32"),
    }


def _feature_fingerprint(subject_row: dict[str, Any], protocol_hash: str) -> dict[str, Any]:
    return {
        "feature_version": FEATURE_VERSION,
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": protocol_hash,
        "inventory_sha256": _sha256(INVENTORY_PATH),
        "source_hashes": {
            "EDA.csv": subject_row["signals"]["EDA"]["sha256"],
            "TEMP.csv": subject_row["signals"]["TEMP"]["sha256"],
            "ACC.csv": subject_row["signals"]["ACC"]["sha256"],
            "tags.csv": subject_row["tag_sha256"],
        },
    }


def _load_or_build_features(
    inventory: dict[str, Any], protocol_hash: str
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, str]]:
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    inventory_by_subject = {
        row["subject_folder"]: row for row in inventory["subject_inventory"]
    }
    data: dict[str, dict[str, np.ndarray]] = {}
    hashes: dict[str, str] = {}
    for subject in inventory["primary_subjects"]:
        subject_row = inventory_by_subject[subject]
        fingerprint = _feature_fingerprint(subject_row, protocol_hash)
        path = FEATURE_DIR / f"{subject}.npz"
        loaded = False
        if path.is_file():
            with np.load(path, allow_pickle=False) as saved:
                saved_fingerprint = json.loads(str(saved["fingerprint_json"].item()))
                if saved_fingerprint == fingerprint:
                    candidate = {
                        "features": saved["features"].astype(np.float64),
                        "labels": saved["labels"].astype(np.int32),
                        "stages": saved["stages"].astype(str),
                        "start_iso": saved["start_iso"].astype(str),
                    }
                    labels_valid = (
                        candidate["labels"].shape == (32,)
                        and np.array_equal(
                            np.bincount(candidate["labels"], minlength=2),
                            np.asarray([16, 16]),
                        )
                    )
                    metadata_valid = (
                        candidate["stages"].shape == (32,)
                        and candidate["start_iso"].shape == (32,)
                        and saved["feature_names"].astype(str).tolist()
                        == feature_names()
                    )
                    if (
                        candidate["features"].shape == (32, 54)
                        and np.isfinite(candidate["features"]).all()
                        and labels_valid
                        and metadata_valid
                    ):
                        data[subject] = candidate
                        loaded = True
        if not loaded:
            extracted = _extract_subject_features(subject_row)
            temporary = path.with_suffix(".npz.tmp")
            with temporary.open("wb") as handle:
                np.savez_compressed(
                    handle,
                    fingerprint_json=json.dumps(fingerprint, sort_keys=True),
                    feature_names=np.asarray(feature_names(), dtype="U32"),
                    **extracted,
                )
            temporary.replace(path)
            data[subject] = extracted
        hashes[subject] = _sha256(path)
    return data, hashes


def _robust_stats(features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = np.median(features, axis=0)
    q25, q75 = np.quantile(features, (0.25, 0.75), axis=0)
    scale = (q75 - q25) / 1.349
    fallback = features.std(axis=0)
    scale = np.where(scale >= 1e-8, scale, fallback)
    scale = np.where(scale >= 1e-8, scale, 1.0)
    return center, scale


def _fit_binary_lda(features: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-8] = 1.0
    standardized = (features - mean) / scale
    centroids = np.vstack([standardized[labels == label].mean(axis=0) for label in range(2)])
    residuals = standardized - centroids[labels]
    covariance = residuals.T @ residuals / max(1, len(features) - 2)
    covariance += 0.15 * np.eye(features.shape[1])
    priors = np.asarray([(labels == label).mean() for label in range(2)])
    return {
        "mean": mean,
        "scale": scale,
        "centroids": centroids,
        "inverse_covariance": np.linalg.pinv(covariance),
        "log_priors": np.log(np.clip(priors, 1e-8, 1.0)),
    }


def _predict(model: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    standardized = (features - model["mean"]) / model["scale"]
    differences = standardized[:, None, :] - model["centroids"][None, :, :]
    distances = np.einsum(
        "nkd,df,nkf->nk",
        differences,
        model["inverse_covariance"],
        differences,
    )
    logits = -0.5 * distances + model["log_priors"][None, :]
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    return probabilities


def _evaluate(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    calibration_scores = 1.0 - calibration_probabilities[
        np.arange(len(calibration_labels)), calibration_labels
    ]
    threshold = _conformal_quantile(calibration_scores, ALPHA)
    sets = (1.0 - test_probabilities) <= threshold
    covered = sets[np.arange(len(test_labels)), test_labels]
    sizes = sets.sum(axis=1)
    predicted = np.argmax(test_probabilities, axis=1)
    true_probability = np.clip(
        test_probabilities[np.arange(len(test_labels)), test_labels], 1e-12, 1.0
    )
    coverage = float(covered.mean())
    full = float(np.mean(sizes == 2))
    return {
        "calibration_score_count": int(len(calibration_labels)),
        "conformal_rank": int(np.ceil((len(calibration_labels) + 1) * (1 - ALPHA))),
        "threshold": float(threshold),
        "coverage": coverage,
        "coverage_by_class": {
            LABEL_NAMES[label]: float(covered[test_labels == label].mean())
            for label in LABEL_NAMES
        },
        "average_prediction_set_size": float(sizes.mean()),
        "full_set_frequency": full,
        "empty_set_frequency": float(np.mean(sizes == 0)),
        "base_classifier_accuracy": float(np.mean(predicted == test_labels)),
        "base_classifier_log_loss": float(-np.log(true_probability).mean()),
        "robustness_loss": float(abs(coverage - TARGET) + 0.25 * full),
    }


def _fold_subjects(subjects: list[str], test_index: int, repetition: int) -> tuple[list[str], list[str]]:
    test_subject = subjects[test_index]
    remaining = [subject for subject in subjects if subject != test_subject]
    offset = (test_index + 7 * repetition) % len(remaining)
    calibration = [remaining[(offset + index) % len(remaining)] for index in range(8)]
    training = [subject for subject in remaining if subject not in calibration]
    if len(training) != 24 or len(set(calibration)) != 8:
        raise Experiment13Error("Subject fold construction failed.")
    return training, calibration


def _heldout_partition(labels: np.ndarray, subject_index: int, repetition: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(400_000 + 1009 * subject_index + 17 * repetition)
    onboarding: list[np.ndarray] = []
    test: list[np.ndarray] = []
    for label in LABEL_NAMES:
        indices = np.flatnonzero(labels == label)
        if len(indices) != PER_CLASS:
            raise Experiment13Error("Held-out balanced feature checkpoint changed.")
        permuted = rng.permutation(indices)
        onboarding.append(permuted[:ONBOARDING_PER_CLASS])
        test.append(permuted[ONBOARDING_PER_CLASS:])
    onboarding_indices = np.sort(np.concatenate(onboarding))
    test_indices = np.sort(np.concatenate(test))
    if set(onboarding_indices) & set(test_indices) or len(test_indices) != 16:
        raise Experiment13Error("Held-out onboarding/test separation failed.")
    return onboarding_indices, test_indices


def _normalized_subject(features: np.ndarray, reference: np.ndarray | None = None) -> np.ndarray:
    center, scale = _robust_stats(features if reference is None else reference)
    return (features - center) / scale


def _run_folds(
    data: dict[str, dict[str, np.ndarray]], subjects: list[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for test_index, test_subject in enumerate(subjects):
        for repetition in range(REPETITIONS):
            training_subjects, calibration_subjects = _fold_subjects(
                subjects, test_index, repetition
            )
            onboarding_indices, test_indices = _heldout_partition(
                data[test_subject]["labels"], test_index, repetition
            )
            for arm in ARMS:
                normalized = arm == "lda_subject_robust_normalized"
                train_parts = []
                train_labels = []
                for subject in training_subjects:
                    values = data[subject]["features"]
                    train_parts.append(_normalized_subject(values) if normalized else values)
                    train_labels.append(data[subject]["labels"])
                calibration_parts = []
                calibration_labels = []
                for subject in calibration_subjects:
                    values = data[subject]["features"]
                    calibration_parts.append(_normalized_subject(values) if normalized else values)
                    calibration_labels.append(data[subject]["labels"])
                heldout = data[test_subject]["features"]
                if normalized:
                    heldout = _normalized_subject(
                        heldout,
                        reference=heldout[onboarding_indices],
                    )
                train_x = np.concatenate(train_parts)
                train_y = np.concatenate(train_labels)
                calibration_x = np.concatenate(calibration_parts)
                calibration_y = np.concatenate(calibration_labels)
                test_x = heldout[test_indices]
                test_y = data[test_subject]["labels"][test_indices]
                model = _fit_binary_lda(train_x, train_y)
                rows.append(
                    {
                        "test_subject": test_subject,
                        "protocol_version": "V1" if test_subject.startswith("S") else "V2",
                        "repetition": repetition,
                        "arm_id": arm,
                        "training_subjects": training_subjects,
                        "external_calibration_subjects": calibration_subjects,
                        "onboarding_indices": onboarding_indices.tolist(),
                        "test_indices": test_indices.tolist(),
                        "onboarding_label_counts_ignored": {
                            LABEL_NAMES[label]: int(
                                np.sum(data[test_subject]["labels"][onboarding_indices] == label)
                            )
                            for label in LABEL_NAMES
                        },
                        "test_label_counts": {
                            LABEL_NAMES[label]: int(np.sum(test_y == label))
                            for label in LABEL_NAMES
                        },
                        **_evaluate(
                            _predict(model, calibration_x),
                            calibration_y,
                            _predict(model, test_x),
                            test_y,
                        ),
                    }
                )
    return rows


def _validate_rows(rows: list[dict[str, Any]], subjects: list[str]) -> None:
    expected = len(subjects) * REPETITIONS * len(ARMS)
    if len(rows) != expected:
        raise Experiment13Error(f"Expected {expected} fold rows, received {len(rows)}.")
    keys = {(row["test_subject"], row["repetition"], row["arm_id"]) for row in rows}
    if len(keys) != expected:
        raise Experiment13Error("Fold result keys are duplicated or incomplete.")
    for row in rows:
        test_subject = row["test_subject"]
        if test_subject in row["training_subjects"] or test_subject in row[
            "external_calibration_subjects"
        ]:
            raise Experiment13Error("Held-out subject leakage detected.")
        if set(row["training_subjects"]) & set(row["external_calibration_subjects"]):
            raise Experiment13Error("Training/calibration subject overlap detected.")
        if len(row["training_subjects"]) != 24 or len(row["external_calibration_subjects"]) != 8:
            raise Experiment13Error("Fold subject counts changed.")
        if set(row["onboarding_indices"]) & set(row["test_indices"]):
            raise Experiment13Error("Onboarding/test overlap detected.")
        if row["calibration_score_count"] != 256 or len(row["test_indices"]) != 16:
            raise Experiment13Error("Calibration/test row counts changed.")
        if row["conformal_rank"] != 232:
            raise Experiment13Error("Conformal rank changed.")
        if row["onboarding_label_counts_ignored"] != {"non_stress": 8, "stress": 8}:
            raise Experiment13Error("Onboarding balance changed.")
        if row["test_label_counts"] != {"non_stress": 8, "stress": 8}:
            raise Experiment13Error("Test balance changed.")


def _fold_fingerprint(
    feature_hashes: dict[str, str], protocol_hash: str
) -> dict[str, Any]:
    return {
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": protocol_hash,
        "integrity_sha256": _sha256(INTEGRITY_PATH),
        "inventory_sha256": _sha256(INVENTORY_PATH),
        "feature_checkpoint_hashes": feature_hashes,
    }


def _load_or_run_folds(
    data: dict[str, dict[str, np.ndarray]],
    subjects: list[str],
    feature_hashes: dict[str, str],
    protocol_hash: str,
    use_checkpoint: bool,
) -> list[dict[str, Any]]:
    fingerprint = _fold_fingerprint(feature_hashes, protocol_hash)
    if use_checkpoint and FOLD_CHECKPOINT.is_file():
        saved = _read_json(FOLD_CHECKPOINT)
        rows = saved.get("fold_results")
        if saved.get("fingerprint") == fingerprint and isinstance(rows, list):
            _validate_rows(rows, subjects)
            print("Reused valid Experiment 13 fold checkpoint.", flush=True)
            return rows
    rows = _run_folds(data, subjects)
    _validate_rows(rows, subjects)
    _atomic_json(FOLD_CHECKPOINT, {"fingerprint": fingerprint, "fold_results": rows})
    print("Saved valid Experiment 13 fold checkpoint.", flush=True)
    return rows


def _summary(rows: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    subject_metrics = {
        subject: {
            "coverage": float(np.mean([row["coverage"] for row in rows if row["test_subject"] == subject])),
            "accuracy": float(
                np.mean([row["base_classifier_accuracy"] for row in rows if row["test_subject"] == subject])
            ),
            "full_set_frequency": float(
                np.mean([row["full_set_frequency"] for row in rows if row["test_subject"] == subject])
            ),
            "robustness_loss": float(
                np.mean([row["robustness_loss"] for row in rows if row["test_subject"] == subject])
            ),
        }
        for subject in subjects
    }
    return {
        "fold_count": len(rows),
        "mean_coverage": float(np.mean([row["coverage"] for row in rows])),
        "worst_subject_mean_coverage": float(
            min(values["coverage"] for values in subject_metrics.values())
        ),
        "mean_accuracy": float(np.mean([row["base_classifier_accuracy"] for row in rows])),
        "mean_log_loss": float(np.mean([row["base_classifier_log_loss"] for row in rows])),
        "mean_prediction_set_size": float(
            np.mean([row["average_prediction_set_size"] for row in rows])
        ),
        "mean_full_set_frequency": float(np.mean([row["full_set_frequency"] for row in rows])),
        "mean_empty_set_frequency": float(np.mean([row["empty_set_frequency"] for row in rows])),
        "mean_robustness_loss": float(np.mean([row["robustness_loss"] for row in rows])),
        "coverage_by_class": {
            name: float(np.mean([row["coverage_by_class"][name] for row in rows]))
            for name in LABEL_NAMES.values()
        },
        "protocol_version_metrics": {
            version: {
                "coverage": float(
                    np.mean([row["coverage"] for row in rows if row["protocol_version"] == version])
                ),
                "accuracy": float(
                    np.mean(
                        [
                            row["base_classifier_accuracy"]
                            for row in rows
                            if row["protocol_version"] == version
                        ]
                    )
                ),
                "full_set_frequency": float(
                    np.mean(
                        [
                            row["full_set_frequency"]
                            for row in rows
                            if row["protocol_version"] == version
                        ]
                    )
                ),
            }
            for version in ("V1", "V2")
        },
        "subject_metrics": subject_metrics,
    }


def _analyze(rows: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    raw = _summary([row for row in rows if row["arm_id"] == "lda_raw"], subjects)
    normalized = _summary(
        [row for row in rows if row["arm_id"] == "lda_subject_robust_normalized"],
        subjects,
    )
    accuracy_change = float(normalized["mean_accuracy"] - raw["mean_accuracy"])
    full_reduction = float(
        raw["mean_full_set_frequency"] - normalized["mean_full_set_frequency"]
    )
    robustness_reduction = float(
        raw["mean_robustness_loss"] - normalized["mean_robustness_loss"]
    )
    worst_coverage_change = float(
        normalized["worst_subject_mean_coverage"] - raw["worst_subject_mean_coverage"]
    )
    version_changes = {
        version: float(
            normalized["protocol_version_metrics"][version]["accuracy"]
            - raw["protocol_version_metrics"][version]["accuracy"]
        )
        for version in ("V1", "V2")
    }
    subject_accuracy_changes = {
        subject: float(
            normalized["subject_metrics"][subject]["accuracy"]
            - raw["subject_metrics"][subject]["accuracy"]
        )
        for subject in subjects
    }
    nonnegative_fraction = float(
        np.mean([change >= 0 for change in subject_accuracy_changes.values()])
    )
    checks = {
        "accuracy_improvement_at_least_0_08": accuracy_change >= 0.08,
        "full_set_reduction_at_least_0_05": full_reduction >= 0.05,
        "robustness_loss_reduction_at_least_0_02": robustness_reduction >= 0.02,
        "normalized_mean_coverage_at_least_0_88": normalized["mean_coverage"] >= 0.88,
        "worst_subject_coverage_change_at_least_minus_0_10": worst_coverage_change >= -0.10,
        "accuracy_change_positive_in_both_protocol_versions": all(
            change > 0 for change in version_changes.values()
        ),
        "subject_nonnegative_accuracy_fraction_at_least_0_60": nonnegative_fraction >= 0.60,
    }
    supported = all(checks.values())
    if supported:
        decision = "EXTERNAL_NORMALIZATION_REPLICATION_SUPPORTED"
    elif accuracy_change >= 0.08:
        decision = "ACCURACY_ONLY_REPLICATION_UNCERTAINTY_GATE_NOT_SUPPORTED"
    else:
        decision = "EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED"
    differences = np.asarray(list(subject_accuracy_changes.values()), dtype=float)
    rng = np.random.default_rng(13_013)
    bootstrap = np.asarray(
        [rng.choice(differences, size=len(differences), replace=True).mean() for _ in range(5000)]
    )
    return {
        "primary_decision": decision,
        "all_preregistered_checks_pass": supported,
        "preregistered_checks": checks,
        "effect_deltas": {
            "accuracy_change": accuracy_change,
            "full_set_frequency_reduction": full_reduction,
            "robustness_loss_reduction": robustness_reduction,
            "coverage_change": float(normalized["mean_coverage"] - raw["mean_coverage"]),
            "worst_subject_coverage_change": worst_coverage_change,
            "protocol_version_accuracy_changes": version_changes,
            "subject_nonnegative_accuracy_change_fraction": nonnegative_fraction,
            "subject_accuracy_changes": subject_accuracy_changes,
            "paired_subject_accuracy_bootstrap_95_percent_interval": [
                float(np.quantile(bootstrap, 0.025)),
                float(np.quantile(bootstrap, 0.975)),
            ],
        },
        "arm_summaries": {
            "lda_raw": raw,
            "lda_subject_robust_normalized": normalized,
        },
    }


def _load_prerequisites() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol = _read_json(PROTOCOL_PATH)
    integrity = _read_json(INTEGRITY_PATH)
    inventory = _read_json(INVENTORY_PATH)
    if protocol.get("protocol_status") != "FROZEN_AFTER_INVENTORY_BEFORE_FEATURE_OR_OUTCOME_COMPUTATION":
        raise Experiment13Error("Experiment 13 protocol is not frozen.")
    if integrity.get("status") != "PASS" or not integrity.get("extraction_completed"):
        raise Experiment13Error("Dataset integrity/extraction has not passed.")
    if inventory.get("inventory_status") != "PASS_PRE_OUTCOME":
        raise Experiment13Error("Pre-outcome inventory has not passed.")
    if inventory.get("scientific_outcomes_computed") is not False:
        raise Experiment13Error("Inventory outcome-separation contract failed.")
    if protocol["dataset"]["archive_sha256"] != integrity["archive_sha256"]:
        raise Experiment13Error("Protocol/archive hash mismatch.")
    if inventory["primary_subject_count"] != protocol["primary_cohort"]["subject_count"]:
        raise Experiment13Error("Protocol/inventory cohort mismatch.")
    return protocol, integrity, inventory


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment13Error("Experiment name mismatch.")
    subjects = report.get("design", {}).get("subjects", [])
    _validate_rows(report.get("fold_results", []), subjects)
    if len(report.get("feature_checkpoints", {})) != 33:
        raise Experiment13Error("Feature checkpoint grid is incomplete.")
    if report.get("analysis", {}).get("primary_decision") not in {
        "EXTERNAL_NORMALIZATION_REPLICATION_SUPPORTED",
        "ACCURACY_ONLY_REPLICATION_UNCERTAINTY_GATE_NOT_SUPPORTED",
        "EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED",
    }:
        raise Experiment13Error("Unknown primary decision.")
    safety = report.get("validation", {})
    if safety.get("model_call_used") is not False or safety.get("raw_dataset_mutated") is not False:
        raise Experiment13Error("Experiment 13 safety contract failed.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, integrity, inventory = _load_prerequisites()
    protocol_hash = _sha256(PROTOCOL_PATH)
    data, feature_hashes = _load_or_build_features(inventory, protocol_hash)
    subjects = inventory["primary_subjects"]
    rows = _load_or_run_folds(
        data,
        subjects,
        feature_hashes,
        protocol_hash,
        use_checkpoint,
    )
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": protocol["research_question"],
        "dataset": {
            "name": protocol["dataset"]["name"],
            "version": protocol["dataset"]["version"],
            "doi": protocol["dataset"]["doi"],
            "license": protocol["dataset"]["license"],
            "archive_sha256": integrity["archive_sha256"],
            "archive_size_bytes": integrity["archive_size_bytes"],
        },
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": protocol_hash,
            "status": protocol["protocol_status"],
        },
        "prerequisites": {
            "integrity_report_path": str(INTEGRITY_PATH.resolve()),
            "integrity_report_sha256": _sha256(INTEGRITY_PATH),
            "inventory_report_path": str(INVENTORY_PATH.resolve()),
            "inventory_report_sha256": _sha256(INVENTORY_PATH),
        },
        "design": {
            "subjects": subjects,
            "subject_count": len(subjects),
            "protocol_version_counts": {
                "V1": sum(subject.startswith("S") for subject in subjects),
                "V2": sum(subject.startswith("f") for subject in subjects),
            },
            "window_seconds": WINDOW_SECONDS,
            "features_per_window": len(feature_names()),
            "balanced_windows_per_subject": 32,
            "repetitions_per_subject": REPETITIONS,
            "training_subjects_per_fold": 24,
            "calibration_subjects_per_fold": 8,
            "test_windows_per_fold": 16,
            "arms": list(ARMS),
            "expected_fold_rows": 198,
        },
        "feature_checkpoints": feature_hashes,
        "fold_results": rows,
        "analysis": _analyze(rows, subjects),
        "limitations": protocol["guardrails"],
        "validation": {
            "protocol_frozen_before_feature_or_outcome_computation": True,
            "dataset_integrity_passed": True,
            "pre_outcome_inventory_passed": True,
            "subject_disjoint_training_calibration_test": True,
            "heldout_onboarding_test_disjoint": True,
            "onboarding_labels_used_for_model_or_calibration": False,
            "post_outcome_exclusion_or_tuning": False,
            "raw_dataset_mutated": False,
            "dependency_installation_used": False,
            "model_call_used": False,
            "api_key_required": False,
            "checkpoint_resume_supported": True,
        },
    }
    return validate_report(report)


def render_markdown(report: dict[str, Any]) -> str:
    analysis = report["analysis"]
    raw = analysis["arm_summaries"]["lda_raw"]
    normalized = analysis["arm_summaries"]["lda_subject_robust_normalized"]
    delta = analysis["effect_deltas"]
    lines = [
        f"# {EXPERIMENT_NAME}",
        "",
        "## Result",
        "",
        f"**{analysis['primary_decision']}**",
        "",
        "## Independent-cohort comparison",
        "",
        "| Arm | Accuracy | Coverage | Worst subject | Mean set size | Full sets | Robustness loss |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| lda_raw | {raw['mean_accuracy']:.4f} | {raw['mean_coverage']:.4f} | "
        f"{raw['worst_subject_mean_coverage']:.4f} | {raw['mean_prediction_set_size']:.4f} | "
        f"{raw['mean_full_set_frequency']:.4f} | {raw['mean_robustness_loss']:.4f} |",
        f"| lda_subject_robust_normalized | {normalized['mean_accuracy']:.4f} | "
        f"{normalized['mean_coverage']:.4f} | {normalized['worst_subject_mean_coverage']:.4f} | "
        f"{normalized['mean_prediction_set_size']:.4f} | {normalized['mean_full_set_frequency']:.4f} | "
        f"{normalized['mean_robustness_loss']:.4f} |",
        "",
        "## Frozen effect deltas",
        "",
        f"- Accuracy change: {delta['accuracy_change']:.4f}",
        f"- Full-set-frequency reduction: {delta['full_set_frequency_reduction']:.4f}",
        f"- Robustness-loss reduction: {delta['robustness_loss_reduction']:.4f}",
        f"- Coverage change: {delta['coverage_change']:.4f}",
        f"- Worst-subject coverage change: {delta['worst_subject_coverage_change']:.4f}",
        f"- V1/V2 accuracy changes: {delta['protocol_version_accuracy_changes']}",
        f"- Subjects with nonnegative accuracy change: {delta['subject_nonnegative_accuracy_change_fraction']:.4f}",
        f"- Paired-subject accuracy bootstrap 95% interval: {delta['paired_subject_accuracy_bootstrap_95_percent_interval']}",
        "",
        "## Preregistered checks",
        "",
        *[f"- {name}: **{passed}**" for name, passed in analysis["preregistered_checks"].items()],
        "",
        "## Design and integrity",
        "",
        f"- Subjects: {report['design']['subject_count']} ({report['design']['protocol_version_counts']})",
        f"- Fold results: {len(report['fold_results'])}",
        f"- Archive SHA-256: `{report['dataset']['archive_sha256']}`",
        "- ZIP CRC, safe extraction, subject inventory, and source hashes: PASS",
        "- Raw data mutation: no",
        "- API/model call: no",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
        "## Reproducibility",
        "",
        "- Independent exact replay: pending",
        "",
    ]
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic NumPy-only execution on hash-validated external CSV data",
        "archive_sha256": report["dataset"]["archive_sha256"],
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "integrity_report_sha256": report["prerequisites"]["integrity_report_sha256"],
        "inventory_report_sha256": report["prerequisites"]["inventory_report_sha256"],
        "feature_checkpoint_hashes": report["feature_checkpoints"],
        "fold_result_count": len(report["fold_results"]),
        "model_call_used": False,
        "api_key_required": False,
        "dependency_installation_used": False,
        "raw_dataset_mutated": False,
        "validation_status": "PENDING_INDEPENDENT_EXACT_REPLAY",
    }


def render_reproducibility_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_NAME} — Reproducibility Summary",
            "",
            f"- Execution mode: {summary['execution_mode']}",
            f"- Archive SHA-256: `{summary['archive_sha256']}`",
            f"- Protocol SHA-256: `{summary['protocol_sha256']}`",
            f"- Integrity-report SHA-256: `{summary['integrity_report_sha256']}`",
            f"- Inventory-report SHA-256: `{summary['inventory_report_sha256']}`",
            f"- Feature checkpoints: {len(summary['feature_checkpoint_hashes'])}",
            f"- Fold results: {summary['fold_result_count']}",
            "- Dependency installation: no",
            "- API/model call: no",
            "- Raw dataset mutation: no",
            "- Independent exact replay: pending",
            "",
        ]
    )


def main() -> None:
    report = build_report(use_checkpoint=True)
    _atomic_json(JSON_OUTPUT, report)
    MARKDOWN_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    reproducibility = reproducibility_summary(report)
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(render_reproducibility_markdown(reproducibility), encoding="utf-8")
    print(f"Experiment 13 complete: {report['analysis']['primary_decision']}")
    print(f"Fold rows: {len(report['fold_results'])}")


if __name__ == "__main__":
    main()
