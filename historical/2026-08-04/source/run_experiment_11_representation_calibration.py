"""Execute Experiment 11 representation-versus-calibration falsification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import _conformal_quantile, _fit_regularized_lda, _model_outputs, _score_matrix
import run_experiment_10_calibration_bridge as exp10
from run_experiment_9_wesad_real_data import SUBJECTS, feature_names


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_11_preregistered_protocol.json"
EXP10_REPORT = OUTPUT_DIR / "meno_j_experiment_10_calibration_bridge.json"
EXP10_VALIDATION = OUTPUT_DIR / "meno_j_experiment_10_validation.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_11_representation_calibration.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_11_representation_calibration.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_11_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_11_reproducibility_summary.md"
CHECKPOINT = PROJECT_DIR / "work" / "experiment_11_checkpoints" / "results.json"

EXPERIMENT_NAME = "Meno-J Experiment 11: Representation-versus-Calibration Falsification"
ALPHA = 0.10
TARGET = 0.90
REPETITIONS = 3
LABEL_NAMES = {0: "baseline", 1: "stress", 2: "amusement"}
FRONTIER_ALLOCATIONS = {
    9: {0: 4, 1: 3, 2: 2},
    12: {0: 6, 1: 4, 2: 2},
    15: {0: 8, 1: 4, 2: 3},
    18: {0: 9, 1: 6, 2: 3},
    19: {0: 10, 1: 6, 2: 3},
    20: {0: 11, 1: 6, 2: 3},
}
FRONTIER_METHODS = tuple(f"personal_k{count}" for count in FRONTIER_ALLOCATIONS)
REPRESENTATION_ARMS = (
    "lda_raw_all",
    "lda_subject_robust_normalized",
    "diagonal_qda_raw_all",
    "distance_weighted_knn15_raw_all",
    "lda_without_ECG",
    "lda_without_EMG",
    "lda_without_EDA",
    "lda_without_Temp",
    "lda_without_Resp",
    "lda_without_ACC",
)
SENSOR_ARMS = tuple(arm for arm in REPRESENTATION_ARMS if arm.startswith("lda_without_"))
ALTERNATIVE_MODEL_ARMS = ("diagonal_qda_raw_all", "distance_weighted_knn15_raw_all")


class Experiment11Error(RuntimeError):
    """Raised when Experiment 11 violates its frozen contract."""


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
        raise Experiment11Error(f"Required JSON is unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise Experiment11Error(f"Expected JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_prerequisites() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    protocol = _read_json(PROTOCOL_PATH)
    validation = _read_json(EXP10_VALIDATION)
    exp10_report = _read_json(EXP10_REPORT)
    if protocol.get("protocol_status") != "FROZEN_BEFORE_EXPERIMENT_11_OUTCOME_ANALYSIS":
        raise Experiment11Error("Experiment 11 protocol is not frozen.")
    if validation.get("status") != "PASS":
        raise Experiment11Error("Experiment 10 validation has not passed.")
    _, _, data = exp10._load_prerequisites()
    return protocol, exp10_report, data


def _personal_partitions_extended(
    labels: np.ndarray,
    subject_index: int,
    repetition: int,
) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray]]:
    rng = np.random.default_rng(100_000 + subject_index * 101 + repetition * 7)
    test_parts: list[np.ndarray] = []
    pool_by_label: dict[int, np.ndarray] = {}
    for label in LABEL_NAMES:
        indices = np.flatnonzero(labels == label)
        if len(indices) < exp10.TEST_COUNTS[label] + FRONTIER_ALLOCATIONS[20][label]:
            raise Experiment11Error(f"Insufficient windows for subject class {label}.")
        permuted = rng.permutation(indices)
        test_parts.append(permuted[: exp10.TEST_COUNTS[label]])
        pool_by_label[label] = permuted[exp10.TEST_COUNTS[label] :]
    test = np.sort(np.concatenate(test_parts))
    onboarding = np.sort(np.concatenate(list(pool_by_label.values())))
    personal: dict[int, np.ndarray] = {}
    for count, allocation in FRONTIER_ALLOCATIONS.items():
        selected = np.sort(
            np.concatenate([pool_by_label[label][: allocation[label]] for label in LABEL_NAMES])
        )
        if len(selected) != count or set(selected) & set(test):
            raise Experiment11Error("Personal calibration/test separation failed.")
        personal[count] = selected
    counts = list(FRONTIER_ALLOCATIONS)
    if not all(set(personal[a]).issubset(personal[b]) for a, b in zip(counts, counts[1:])):
        raise Experiment11Error("Extended calibration schedule is not nested.")
    return test, onboarding, personal


def _feature_indices(arm: str) -> np.ndarray:
    names = feature_names()
    if not arm.startswith("lda_without_"):
        return np.arange(len(names), dtype=int)
    family = arm.removeprefix("lda_without_")
    if family == "ACC":
        keep = [not name.startswith("ACC_") for name in names]
    else:
        keep = [not name.startswith(f"{family}_") for name in names]
    indices = np.flatnonzero(keep)
    if len(indices) == 0 or len(indices) == len(names):
        raise Experiment11Error(f"Sensor ablation did not alter features: {arm}")
    return indices


def _robust_stats(features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = np.median(features, axis=0)
    q25, q75 = np.quantile(features, (0.25, 0.75), axis=0)
    scale = (q75 - q25) / 1.349
    fallback = features.std(axis=0)
    scale = np.where(scale >= 1e-8, scale, fallback)
    scale = np.where(scale >= 1e-8, scale, 1.0)
    return center, scale


def _fit_lda(features: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    return {"kind": "lda", "payload": _fit_regularized_lda(features, labels)}


def _fit_diagonal_qda(features: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-8] = 1.0
    standardized = (features - mean) / scale
    class_means = np.vstack([standardized[labels == label].mean(axis=0) for label in LABEL_NAMES])
    class_variances = np.vstack([standardized[labels == label].var(axis=0) for label in LABEL_NAMES])
    class_variances = 0.8 * class_variances + 0.2
    class_variances = np.maximum(class_variances, 0.05)
    priors = np.asarray([(labels == label).mean() for label in LABEL_NAMES])
    return {
        "kind": "diagonal_qda",
        "mean": mean,
        "scale": scale,
        "class_means": class_means,
        "class_variances": class_variances,
        "log_priors": np.log(np.clip(priors, 1e-8, 1.0)),
    }


def _fit_knn15(features: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-8] = 1.0
    return {
        "kind": "knn15",
        "mean": mean,
        "scale": scale,
        "features": (features - mean) / scale,
        "labels": labels.copy(),
    }


def _predict_probabilities(model: dict[str, Any], features: np.ndarray) -> np.ndarray:
    kind = model["kind"]
    if kind == "lda":
        probabilities, _ = _model_outputs(model["payload"], features)
        return probabilities
    standardized = (features - model["mean"]) / model["scale"]
    if kind == "diagonal_qda":
        differences = standardized[:, None, :] - model["class_means"][None, :, :]
        logits = -0.5 * np.sum(
            np.log(model["class_variances"])[None, :, :]
            + differences * differences / model["class_variances"][None, :, :],
            axis=2,
        ) + model["log_priors"][None, :]
    elif kind == "knn15":
        differences = standardized[:, None, :] - model["features"][None, :, :]
        squared = np.sum(differences * differences, axis=2)
        k = min(15, squared.shape[1])
        neighbor_indices = np.argpartition(squared, k - 1, axis=1)[:, :k]
        neighbor_distances = np.take_along_axis(squared, neighbor_indices, axis=1)
        weights = 1.0 / (np.sqrt(neighbor_distances) + 0.10)
        logits = np.full((len(features), 3), 0.5, dtype=float)
        for label in LABEL_NAMES:
            logits[:, label] += np.sum(
                weights * (model["labels"][neighbor_indices] == label), axis=1
            )
        logits = np.log(logits)
    else:
        raise Experiment11Error(f"Unknown model kind: {kind}")
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
    test_scores = 1.0 - test_probabilities
    sets = test_scores <= threshold
    covered = sets[np.arange(len(test_labels)), test_labels]
    sizes = sets.sum(axis=1)
    predicted = np.argmax(test_probabilities, axis=1)
    true_probability = np.clip(
        test_probabilities[np.arange(len(test_labels)), test_labels], 1e-12, 1.0
    )
    coverage = float(covered.mean())
    full = float(np.mean(sizes == 3))
    return {
        "calibration_score_count": int(len(calibration_labels)),
        "conformal_rank": int(np.ceil((len(calibration_labels) + 1) * (1 - ALPHA))),
        "threshold": float(threshold) if np.isfinite(threshold) else None,
        "threshold_status": "FINITE" if np.isfinite(threshold) else "INFINITE",
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


def _raw_fold_arrays(
    data: dict[str, dict[str, np.ndarray]],
    training_subjects: list[str],
    test_subject: str,
    test_indices: np.ndarray,
    calibration_indices: np.ndarray,
    feature_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # Preserve the exact Experiment 10 memory/layout path for the all-feature arm.
    # NumPy advanced indexing creates a differently laid-out copy and can perturb
    # the last few floating-point bits of the LDA solve, which would make the
    # preregistered exact continuity gate fail despite identical mathematics.
    all_features = np.array_equal(feature_indices, np.arange(len(feature_names())))
    if all_features:
        train_x = np.concatenate([data[item]["features"] for item in training_subjects])
    else:
        train_x = np.concatenate(
            [data[item]["features"][:, feature_indices] for item in training_subjects]
        )
    train_y = np.concatenate([data[item]["labels"] for item in training_subjects])
    subject = data[test_subject]
    calibration_x = (
        subject["features"][calibration_indices]
        if all_features
        else subject["features"][calibration_indices][:, feature_indices]
    )
    test_x = (
        subject["features"][test_indices]
        if all_features
        else subject["features"][test_indices][:, feature_indices]
    )
    return (
        train_x,
        train_y,
        calibration_x,
        subject["labels"][calibration_indices],
        test_x,
        subject["labels"][test_indices],
    )


def _normalized_fold_arrays(
    data: dict[str, dict[str, np.ndarray]],
    training_subjects: list[str],
    test_subject: str,
    onboarding_indices: np.ndarray,
    test_indices: np.ndarray,
    calibration_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_parts: list[np.ndarray] = []
    train_labels: list[np.ndarray] = []
    for subject in training_subjects:
        center, scale = _robust_stats(data[subject]["features"])
        train_parts.append((data[subject]["features"] - center) / scale)
        train_labels.append(data[subject]["labels"])
    heldout = data[test_subject]
    center, scale = _robust_stats(heldout["features"][onboarding_indices])
    return (
        np.concatenate(train_parts),
        np.concatenate(train_labels),
        (heldout["features"][calibration_indices] - center) / scale,
        heldout["labels"][calibration_indices],
        (heldout["features"][test_indices] - center) / scale,
        heldout["labels"][test_indices],
    )


def _fit_for_arm(arm: str, train_x: np.ndarray, train_y: np.ndarray) -> dict[str, Any]:
    if arm == "diagonal_qda_raw_all":
        return _fit_diagonal_qda(train_x, train_y)
    if arm == "distance_weighted_knn15_raw_all":
        return _fit_knn15(train_x, train_y)
    return _fit_lda(train_x, train_y)


def _run(data: dict[str, dict[str, np.ndarray]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frontier_rows: list[dict[str, Any]] = []
    representation_rows: list[dict[str, Any]] = []
    all_indices = np.arange(len(feature_names()), dtype=int)
    for test_index, test_subject in enumerate(SUBJECTS):
        for repetition in range(REPETITIONS):
            training_subjects, external_subjects = exp10._fold_subjects(test_index, repetition)
            test_indices, onboarding_indices, personal = _personal_partitions_extended(
                data[test_subject]["labels"], test_index, repetition
            )
            train_x, train_y, _, _, test_x, test_y = _raw_fold_arrays(
                data, training_subjects, test_subject, test_indices, personal[19], all_indices
            )
            frontier_model = _fit_lda(train_x, train_y)
            frontier_test_probabilities = _predict_probabilities(frontier_model, test_x)
            common = {
                "test_subject": test_subject,
                "repetition": repetition,
                "training_subjects": training_subjects,
                "external_calibration_subjects": external_subjects,
                "personal_test_indices": test_indices.tolist(),
                "onboarding_pool_indices": onboarding_indices.tolist(),
            }
            for count, indices in personal.items():
                calibration_x = data[test_subject]["features"][indices]
                calibration_y = data[test_subject]["labels"][indices]
                calibration_probabilities = _predict_probabilities(frontier_model, calibration_x)
                frontier_rows.append(
                    {
                        **common,
                        "method_id": f"personal_k{count}",
                        "personal_calibration_indices": indices.tolist(),
                        **_evaluate(
                            calibration_probabilities,
                            calibration_y,
                            frontier_test_probabilities,
                            test_y,
                        ),
                    }
                )

            for arm in REPRESENTATION_ARMS:
                feature_indices = _feature_indices(arm)
                if arm == "lda_subject_robust_normalized":
                    arrays = _normalized_fold_arrays(
                        data,
                        training_subjects,
                        test_subject,
                        onboarding_indices,
                        test_indices,
                        personal[19],
                    )
                else:
                    arrays = _raw_fold_arrays(
                        data,
                        training_subjects,
                        test_subject,
                        test_indices,
                        personal[19],
                        feature_indices,
                    )
                arm_train_x, arm_train_y, cal_x, cal_y, arm_test_x, arm_test_y = arrays
                model = _fit_for_arm(arm, arm_train_x, arm_train_y)
                representation_rows.append(
                    {
                        **common,
                        "arm_id": arm,
                        "feature_count": int(arm_train_x.shape[1]),
                        "personal_calibration_count": 19,
                        "personal_calibration_indices": personal[19].tolist(),
                        **_evaluate(
                            _predict_probabilities(model, cal_x),
                            cal_y,
                            _predict_probabilities(model, arm_test_x),
                            arm_test_y,
                        ),
                    }
                )
    return frontier_rows, representation_rows


def _fingerprint(exp10_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "experiment_10_report_sha256": _sha256(EXP10_REPORT),
        "experiment_10_validation_sha256": _sha256(EXP10_VALIDATION),
        "feature_checkpoint_hashes": exp10_report["experiment_9_checkpoint_source"][
            "feature_checkpoint_hashes"
        ],
    }


def _load_or_run(
    data: dict[str, dict[str, np.ndarray]],
    exp10_report: dict[str, Any],
    use_checkpoint: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fingerprint = _fingerprint(exp10_report)
    if use_checkpoint and CHECKPOINT.is_file():
        saved = _read_json(CHECKPOINT)
        if saved.get("fingerprint") == fingerprint:
            frontier = saved.get("frontier_rows")
            representation = saved.get("representation_rows")
            if isinstance(frontier, list) and isinstance(representation, list):
                _validate_rows(frontier, representation)
                print("Reused valid Experiment 11 checkpoint.", flush=True)
                return frontier, representation
    frontier, representation = _run(data)
    _validate_rows(frontier, representation)
    _atomic_json(
        CHECKPOINT,
        {
            "fingerprint": fingerprint,
            "frontier_rows": frontier,
            "representation_rows": representation,
        },
    )
    print("Saved valid Experiment 11 checkpoint.", flush=True)
    return frontier, representation


def _validate_rows(frontier: list[dict[str, Any]], representation: list[dict[str, Any]]) -> None:
    expected_frontier = len(SUBJECTS) * REPETITIONS * len(FRONTIER_METHODS)
    expected_representation = len(SUBJECTS) * REPETITIONS * len(REPRESENTATION_ARMS)
    if len(frontier) != expected_frontier or len(representation) != expected_representation:
        raise Experiment11Error("Experiment 11 result grids are incomplete.")
    if len({(row["test_subject"], row["repetition"], row["method_id"]) for row in frontier}) != expected_frontier:
        raise Experiment11Error("Frontier result keys are duplicated or missing.")
    if len({(row["test_subject"], row["repetition"], row["arm_id"]) for row in representation}) != expected_representation:
        raise Experiment11Error("Representation result keys are duplicated or missing.")
    for row in [*frontier, *representation]:
        if row["test_subject"] in row["training_subjects"] or row["test_subject"] in row["external_calibration_subjects"]:
            raise Experiment11Error("Held-out subject leakage detected.")
        if set(row["personal_test_indices"]) & set(row["personal_calibration_indices"]):
            raise Experiment11Error("Personal test/calibration overlap detected.")
        for field in ("coverage", "full_set_frequency", "empty_set_frequency", "base_classifier_accuracy"):
            if not 0.0 <= row[field] <= 1.0:
                raise Experiment11Error(f"Metric outside [0,1]: {field}")
        if row["threshold_status"] != "FINITE":
            raise Experiment11Error("Experiment 11 unexpectedly produced an infinite threshold.")
    for row in frontier:
        count = int(row["method_id"].split("k", 1)[1])
        if row["calibration_score_count"] != count or len(row["personal_calibration_indices"]) != count:
            raise Experiment11Error("Frontier calibration count mismatch.")
        if row["conformal_rank"] != int(np.ceil((count + 1) * (1 - ALPHA))):
            raise Experiment11Error("Conformal rank mismatch.")


def _aggregate(rows: list[dict[str, Any]], id_field: str, ordering: tuple[str, ...]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for method in ordering:
        cells = [row for row in rows if row[id_field] == method]
        subject_values: dict[str, dict[str, float]] = {}
        for subject in SUBJECTS:
            subject_rows = [row for row in cells if row["test_subject"] == subject]
            subject_values[subject] = {
                "coverage": float(np.mean([row["coverage"] for row in subject_rows])),
                "full_set_frequency": float(np.mean([row["full_set_frequency"] for row in subject_rows])),
                "prediction_set_size": float(np.mean([row["average_prediction_set_size"] for row in subject_rows])),
                "accuracy": float(np.mean([row["base_classifier_accuracy"] for row in subject_rows])),
                "log_loss": float(np.mean([row["base_classifier_log_loss"] for row in subject_rows])),
                "robustness_loss": float(np.mean([row["robustness_loss"] for row in subject_rows])),
            }
        aggregates.append(
            {
                id_field: method,
                "fold_count": len(cells),
                "mean_coverage": float(np.mean([row["coverage"] for row in cells])),
                "worst_subject_mean_coverage": float(
                    min(values["coverage"] for values in subject_values.values())
                ),
                "mean_prediction_set_size": float(
                    np.mean([row["average_prediction_set_size"] for row in cells])
                ),
                "mean_full_set_frequency": float(np.mean([row["full_set_frequency"] for row in cells])),
                "mean_accuracy": float(np.mean([row["base_classifier_accuracy"] for row in cells])),
                "mean_log_loss": float(np.mean([row["base_classifier_log_loss"] for row in cells])),
                "mean_robustness_loss": float(np.mean([row["robustness_loss"] for row in cells])),
                "coverage_by_class": {
                    name: float(np.mean([row["coverage_by_class"][name] for row in cells]))
                    for name in LABEL_NAMES.values()
                },
                "subject_metrics": subject_values,
            }
        )
    return aggregates


def _find(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    matches = [row for row in rows if row[key] == value]
    if len(matches) != 1:
        raise Experiment11Error(f"Unable to resolve aggregate {key}={value}.")
    return matches[0]


def _targeted_summary(row: dict[str, Any]) -> dict[str, float]:
    metrics = [row["subject_metrics"][subject] for subject in ("S2", "S4")]
    return {
        "mean_accuracy": float(np.mean([item["accuracy"] for item in metrics])),
        "mean_coverage": float(np.mean([item["coverage"] for item in metrics])),
        "mean_full_set_frequency": float(np.mean([item["full_set_frequency"] for item in metrics])),
        "mean_robustness_loss": float(np.mean([item["robustness_loss"] for item in metrics])),
    }


def _analyze(
    frontier: list[dict[str, Any]],
    representation: list[dict[str, Any]],
) -> dict[str, Any]:
    k18 = _find(frontier, "method_id", "personal_k18")
    k19 = _find(frontier, "method_id", "personal_k19")
    frontier_full_reduction = float(k18["mean_full_set_frequency"] - k19["mean_full_set_frequency"])
    frontier_worst_change = float(
        k19["worst_subject_mean_coverage"] - k18["worst_subject_mean_coverage"]
    )
    frontier_supported = bool(
        frontier_full_reduction >= 0.03
        and k19["mean_coverage"] >= 0.88
        and frontier_worst_change >= -0.05
    )

    baseline = _find(representation, "arm_id", "lda_raw_all")
    baseline_targeted = _targeted_summary(baseline)
    normalized = _find(representation, "arm_id", "lda_subject_robust_normalized")
    normalized_targeted = _targeted_summary(normalized)
    normalization_general = bool(
        normalized["mean_accuracy"] - baseline["mean_accuracy"] >= 0.03
        and baseline["mean_robustness_loss"] - normalized["mean_robustness_loss"] >= 0.03
    )
    normalization_targeted = bool(
        all(
            normalized["subject_metrics"][subject]["accuracy"]
            - baseline["subject_metrics"][subject]["accuracy"] >= 0.10
            for subject in ("S2", "S4")
        )
        and baseline_targeted["mean_full_set_frequency"]
        - normalized_targeted["mean_full_set_frequency"] >= 0.10
        and normalized_targeted["mean_coverage"] >= 0.80
    )

    sensor_results: list[dict[str, Any]] = []
    for arm in SENSOR_ARMS:
        row = _find(representation, "arm_id", arm)
        targeted = _targeted_summary(row)
        supported = bool(
            targeted["mean_accuracy"] - baseline_targeted["mean_accuracy"] >= 0.10
            and baseline_targeted["mean_robustness_loss"] - targeted["mean_robustness_loss"] >= 0.03
            and row["mean_accuracy"] >= baseline["mean_accuracy"] - 0.03
        )
        sensor_results.append(
            {
                "arm_id": arm,
                "supported": supported,
                "overall_accuracy_change": float(row["mean_accuracy"] - baseline["mean_accuracy"]),
                "s2_s4_accuracy_change": float(
                    targeted["mean_accuracy"] - baseline_targeted["mean_accuracy"]
                ),
                "s2_s4_robustness_loss_reduction": float(
                    baseline_targeted["mean_robustness_loss"] - targeted["mean_robustness_loss"]
                ),
                "s2_s4_coverage": targeted["mean_coverage"],
                "s2_s4_full_set_frequency": targeted["mean_full_set_frequency"],
            }
        )

    alternative_results: list[dict[str, Any]] = []
    for arm in ALTERNATIVE_MODEL_ARMS:
        row = _find(representation, "arm_id", arm)
        targeted = _targeted_summary(row)
        supported = bool(
            targeted["mean_accuracy"] - baseline_targeted["mean_accuracy"] >= 0.10
            and baseline_targeted["mean_full_set_frequency"]
            - targeted["mean_full_set_frequency"] >= 0.10
            and targeted["mean_coverage"] >= 0.80
            and row["mean_accuracy"] >= baseline["mean_accuracy"] - 0.03
        )
        alternative_results.append(
            {
                "arm_id": arm,
                "supported": supported,
                "overall_accuracy_change": float(row["mean_accuracy"] - baseline["mean_accuracy"]),
                "s2_s4_accuracy_change": float(
                    targeted["mean_accuracy"] - baseline_targeted["mean_accuracy"]
                ),
                "s2_s4_coverage": targeted["mean_coverage"],
                "s2_s4_full_set_frequency_change": float(
                    targeted["mean_full_set_frequency"]
                    - baseline_targeted["mean_full_set_frequency"]
                ),
                "s2_s4_robustness_loss": targeted["mean_robustness_loss"],
            }
        )

    supported = []
    if frontier_supported:
        supported.append("R1_CALIBRATION_ORDER_STATISTICS")
    if normalization_general or normalization_targeted:
        supported.append("R2_SUBJECT_BASELINE_MISMATCH")
    if any(row["supported"] for row in sensor_results):
        supported.append("R3_SENSOR_FAMILY_INTERFERENCE")
    if any(row["supported"] for row in alternative_results):
        supported.append("R4_CLASSIFIER_REPRESENTATION")
    decision = (
        "SUPPORTED_RIVALS_" + "_AND_".join(item.split("_", 1)[0] for item in supported)
        if supported
        else "TESTED_REPAIRS_DO_NOT_EXPLAIN_S2_S4"
    )
    return {
        "primary_decision": decision,
        "supported_rival_ids": supported,
        "calibration_order_statistic": {
            "supported": frontier_supported,
            "k18_mean_coverage": k18["mean_coverage"],
            "k19_mean_coverage": k19["mean_coverage"],
            "k18_full_set_frequency": k18["mean_full_set_frequency"],
            "k19_full_set_frequency": k19["mean_full_set_frequency"],
            "full_set_frequency_reduction": frontier_full_reduction,
            "worst_subject_coverage_change": frontier_worst_change,
        },
        "subject_baseline_normalization": {
            "general_supported": normalization_general,
            "s2_s4_supported": normalization_targeted,
            "overall_accuracy_change": float(normalized["mean_accuracy"] - baseline["mean_accuracy"]),
            "overall_robustness_loss_reduction": float(
                baseline["mean_robustness_loss"] - normalized["mean_robustness_loss"]
            ),
            "s2_s4_accuracy_change": float(
                normalized_targeted["mean_accuracy"] - baseline_targeted["mean_accuracy"]
            ),
            "s2_s4_full_set_frequency_change": float(
                normalized_targeted["mean_full_set_frequency"]
                - baseline_targeted["mean_full_set_frequency"]
            ),
            "s2_s4_coverage": normalized_targeted["mean_coverage"],
        },
        "sensor_ablation": {
            "supported": any(row["supported"] for row in sensor_results),
            "arms": sensor_results,
        },
        "classifier_representation": {
            "supported": any(row["supported"] for row in alternative_results),
            "arms": alternative_results,
        },
        "baseline_s2_s4": baseline_targeted,
    }


def _continuity_check(frontier_rows: list[dict[str, Any]], exp10_report: dict[str, Any]) -> dict[str, Any]:
    prior = {
        (row["test_subject"], row["repetition"], row["method_id"]): row
        for row in exp10_report["fold_results"]
        if row["method_id"] in ("personal_k9", "personal_k12")
    }
    fields = (
        "coverage",
        "coverage_by_class",
        "average_prediction_set_size",
        "full_set_frequency",
        "empty_set_frequency",
        "threshold",
        "threshold_status",
        "calibration_score_count",
    )
    mismatches: list[str] = []
    checked = 0
    for row in frontier_rows:
        if row["method_id"] not in ("personal_k9", "personal_k12"):
            continue
        key = (row["test_subject"], row["repetition"], row["method_id"])
        previous = prior.get(key)
        if previous is None or any(row[field] != previous[field] for field in fields):
            mismatches.append("/".join(map(str, key)))
        checked += 1
    if checked != 90 or mismatches:
        raise Experiment11Error(f"Experiment 10 continuity check failed: {mismatches[:10]}")
    return {"status": "PASS", "rows_checked": checked, "mismatch_count": 0}


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment11Error("Experiment name mismatch.")
    _validate_rows(report.get("calibration_frontier_rows", []), report.get("representation_rows", []))
    if len(report.get("calibration_frontier_aggregates", [])) != len(FRONTIER_METHODS):
        raise Experiment11Error("Frontier aggregate grid is incomplete.")
    if len(report.get("representation_aggregates", [])) != len(REPRESENTATION_ARMS):
        raise Experiment11Error("Representation aggregate grid is incomplete.")
    if report.get("continuity_with_experiment_10", {}).get("status") != "PASS":
        raise Experiment11Error("Experiment 10 continuity did not pass.")
    validation = report.get("validation", {})
    if validation.get("model_call_used") is not False or validation.get("raw_wesad_pickles_loaded") is not False:
        raise Experiment11Error("Experiment 11 safety contract failed.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, exp10_report, data = _load_prerequisites()
    frontier_rows, representation_rows = _load_or_run(data, exp10_report, use_checkpoint)
    frontier_aggregates = _aggregate(frontier_rows, "method_id", FRONTIER_METHODS)
    representation_aggregates = _aggregate(
        representation_rows, "arm_id", REPRESENTATION_ARMS
    )
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": protocol["research_question"],
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "prerequisites": {
            "experiment_10_report_path": str(EXP10_REPORT.resolve()),
            "experiment_10_report_sha256": _sha256(EXP10_REPORT),
            "experiment_10_validation_path": str(EXP10_VALIDATION.resolve()),
            "experiment_10_validation_sha256": _sha256(EXP10_VALIDATION),
            "feature_checkpoint_hashes": _fingerprint(exp10_report)["feature_checkpoint_hashes"],
        },
        "design_counts": {
            "subjects": len(SUBJECTS),
            "repetitions_per_subject": REPETITIONS,
            "calibration_frontier_rows": len(frontier_rows),
            "representation_rows": len(representation_rows),
            "frontier_methods": list(FRONTIER_METHODS),
            "representation_arms": list(REPRESENTATION_ARMS),
        },
        "calibration_frontier_rows": frontier_rows,
        "calibration_frontier_aggregates": frontier_aggregates,
        "representation_rows": representation_rows,
        "representation_aggregates": representation_aggregates,
        "continuity_with_experiment_10": _continuity_check(frontier_rows, exp10_report),
        "analysis": _analyze(frontier_aggregates, representation_aggregates),
        "limitations": [
            "The k=18 to k=19 transition is only one order-statistic boundary with at most 20 onboarding examples.",
            "S2 and S4 remain post-selected exploratory cases.",
            "Sensor-family ablation diagnoses predictive interference, not physical sensor malfunction.",
            "The nonlinear models use fixed untuned NumPy implementations and are not exhaustive.",
            "One dataset and one recording session per subject limit external validity.",
        ],
        "validation": {
            "protocol_frozen_before_outcome_analysis": True,
            "experiment_10_validation_reused": True,
            "experiment_10_k9_k12_exact_continuity": True,
            "personal_test_calibration_overlap": False,
            "heldout_test_used_for_normalization": False,
            "classifier_hyperparameter_search_used": False,
            "raw_wesad_pickles_loaded": False,
            "raw_dataset_mutated": False,
            "model_call_used": False,
            "api_key_required": False,
            "checkpoint_resume_supported": True,
        },
    }
    return validate_report(report)


def render_markdown(report: dict[str, Any]) -> str:
    analysis = report["analysis"]
    lines = [
        f"# {EXPERIMENT_NAME}",
        "",
        "## Result",
        "",
        f"**{analysis['primary_decision']}**",
        "",
        f"Supported rivals: {analysis['supported_rival_ids'] or 'none'}",
        "",
        "## Calibration frontier",
        "",
        "| Personal k | Rank | Mean coverage | Worst subject | Mean set size | Full sets |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    aggregate_by_method = {
        row["method_id"]: row for row in report["calibration_frontier_aggregates"]
    }
    ranks = {count: int(np.ceil((count + 1) * (1 - ALPHA))) for count in FRONTIER_ALLOCATIONS}
    for count in FRONTIER_ALLOCATIONS:
        row = aggregate_by_method[f"personal_k{count}"]
        lines.append(
            f"| {count} | {ranks[count]} | {row['mean_coverage']:.4f} | "
            f"{row['worst_subject_mean_coverage']:.4f} | {row['mean_prediction_set_size']:.4f} | "
            f"{row['mean_full_set_frequency']:.4f} |"
        )
    order = analysis["calibration_order_statistic"]
    lines.extend(
        [
            "",
            f"Order-statistic rival supported: **{order['supported']}**",
            f"Full-set reduction from k=18 to k=19: {order['full_set_frequency_reduction']:.4f}",
            f"Worst-subject coverage change: {order['worst_subject_coverage_change']:.4f}",
            "",
            "## Representation and sensor interventions at k=19",
            "",
            "| Arm | Accuracy | Coverage | Worst subject | Mean set size | Full sets | Robustness loss |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["representation_aggregates"]:
        lines.append(
            f"| {row['arm_id']} | {row['mean_accuracy']:.4f} | {row['mean_coverage']:.4f} | "
            f"{row['worst_subject_mean_coverage']:.4f} | {row['mean_prediction_set_size']:.4f} | "
            f"{row['mean_full_set_frequency']:.4f} | {row['mean_robustness_loss']:.4f} |"
        )
    norm = analysis["subject_baseline_normalization"]
    lines.extend(
        [
            "",
            "## Rival decisions",
            "",
            f"- Subject normalization, general support: {norm['general_supported']}",
            f"- Subject normalization, S2/S4 support: {norm['s2_s4_supported']}",
            f"- Sensor-family interference supported: {analysis['sensor_ablation']['supported']}",
            f"- Alternative classifier representation supported: {analysis['classifier_representation']['supported']}",
            "",
            "### Sensor ablations",
            "",
            "| Arm | Supported | Overall accuracy Δ | S2/S4 accuracy Δ | S2/S4 robustness reduction |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in analysis["sensor_ablation"]["arms"]:
        lines.append(
            f"| {row['arm_id']} | {row['supported']} | {row['overall_accuracy_change']:.4f} | "
            f"{row['s2_s4_accuracy_change']:.4f} | {row['s2_s4_robustness_loss_reduction']:.4f} |"
        )
    lines.extend(
        [
            "",
            "### Alternative classifiers",
            "",
            "| Arm | Supported | Overall accuracy Δ | S2/S4 accuracy Δ | S2/S4 coverage | S2/S4 full-set Δ |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in analysis["classifier_representation"]["arms"]:
        lines.append(
            f"| {row['arm_id']} | {row['supported']} | {row['overall_accuracy_change']:.4f} | "
            f"{row['s2_s4_accuracy_change']:.4f} | {row['s2_s4_coverage']:.4f} | "
            f"{row['s2_s4_full_set_frequency_change']:.4f} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            f"- Exact Experiment 10 k=9/k=12 rows checked: {report['continuity_with_experiment_10']['rows_checked']}",
            "- Raw WESAD pickle loading: no",
            "- API/model call: no",
            "- Independent exact replay: pending",
            "",
        ]
    )
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic NumPy-only replay from validated feature checkpoints",
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "experiment_10_report_sha256": report["prerequisites"]["experiment_10_report_sha256"],
        "experiment_10_validation_sha256": report["prerequisites"]["experiment_10_validation_sha256"],
        "feature_checkpoint_hashes": report["prerequisites"]["feature_checkpoint_hashes"],
        "frontier_row_count": len(report["calibration_frontier_rows"]),
        "representation_row_count": len(report["representation_rows"]),
        "experiment_10_continuity_rows": report["continuity_with_experiment_10"]["rows_checked"],
        "dependency_installation_used": False,
        "model_call_used": False,
        "api_key_required": False,
        "raw_wesad_pickles_loaded": False,
        "validation_status": "PENDING_INDEPENDENT_EXACT_REPLAY",
    }


def render_reproducibility_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_NAME} — Reproducibility Summary",
            "",
            f"- Execution mode: {summary['execution_mode']}",
            f"- Protocol SHA-256: `{summary['protocol_sha256']}`",
            f"- Experiment 10 report SHA-256: `{summary['experiment_10_report_sha256']}`",
            f"- Experiment 10 validation SHA-256: `{summary['experiment_10_validation_sha256']}`",
            f"- Frontier rows: {summary['frontier_row_count']}",
            f"- Representation rows: {summary['representation_row_count']}",
            f"- Experiment 10 continuity rows: {summary['experiment_10_continuity_rows']}",
            "- Dependency installation: no",
            "- API/model call: no",
            "- Raw WESAD pickle loading: no",
            "- Independent exact replay: pending",
            "",
        ]
    )


def main() -> None:
    report = build_report(use_checkpoint=True)
    summary = reproducibility_summary(report)
    _atomic_json(JSON_OUTPUT, report)
    MARKDOWN_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    _atomic_json(REPRO_JSON, summary)
    REPRO_MD.write_text(render_reproducibility_markdown(summary), encoding="utf-8")
    print(f"Experiment 11 complete: {report['analysis']['primary_decision']}")
    print(
        f"Frontier rows: {len(report['calibration_frontier_rows'])}; "
        f"representation rows: {len(report['representation_rows'])}"
    )


if __name__ == "__main__":
    main()
