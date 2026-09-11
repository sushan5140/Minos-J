"""Run Meno-J Experiment 10 on validated Experiment 9 WESAD checkpoints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pipeline import _conformal_quantile, _fit_regularized_lda, _model_outputs, _score_matrix
from run_experiment_9_wesad_real_data import FEATURE_VERSION, SUBJECTS, feature_names


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
FEATURE_DIR = PROJECT_DIR / "work" / "experiment_9_checkpoints" / "features"
CHECKPOINT_DIR = PROJECT_DIR / "work" / "experiment_10_checkpoints"
FOLD_CHECKPOINT = CHECKPOINT_DIR / "fold_results.json"
EXP9_REPORT = OUTPUT_DIR / "meno_j_experiment_9_wesad_real_data.json"
EXP9_VALIDATION = OUTPUT_DIR / "meno_j_experiment_9_validation.json"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_10_preregistered_protocol.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_10_calibration_bridge.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_10_calibration_bridge.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_10_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_10_reproducibility_summary.md"

EXPERIMENT_NAME = "Meno-J Experiment 10: Calibration Onboarding and Compatibility Bridge"
ALPHA = 0.10
TARGET = 0.90
REPETITIONS = 3
LABEL_NAMES = {0: "baseline", 1: "stress", 2: "amusement"}
TEST_COUNTS = {0: 8, 1: 4, 2: 3}
PERSONAL_ALLOCATIONS = {
    3: {0: 1, 1: 1, 2: 1},
    6: {0: 3, 1: 2, 2: 1},
    9: {0: 4, 1: 3, 2: 2},
    12: {0: 6, 1: 4, 2: 2},
}
METHODS = (
    "external_all4",
    "external_nearest2",
    "external_farthest2",
    "personal_k3",
    "personal_k6",
    "personal_k9",
    "personal_k12",
)


class Experiment10Error(RuntimeError):
    """Raised when Experiment 10 violates its frozen contract."""


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
        raise Experiment10Error(f"Required valid JSON is unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise Experiment10Error(f"Expected a JSON object: {path}")
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
    exp9 = _read_json(EXP9_REPORT)
    validation = _read_json(EXP9_VALIDATION)
    if protocol.get("protocol_status") != "FROZEN_BEFORE_EXPERIMENT_10_OUTCOME_ANALYSIS":
        raise Experiment10Error("Experiment 10 protocol is not frozen.")
    if validation.get("status") != "PASS":
        raise Experiment10Error("Experiment 9 independent validation has not passed.")
    if exp9.get("validation", {}).get("integrity_gate_passed") is not True:
        raise Experiment10Error("Experiment 9 integrity gate has not passed.")
    summaries = {row["subject_id"]: row for row in exp9["subject_feature_summary"]}
    if set(summaries) != set(SUBJECTS):
        raise Experiment10Error("Experiment 9 subject inventory changed.")

    expected_names = feature_names()
    data: dict[str, dict[str, np.ndarray]] = {}
    for subject in SUBJECTS:
        row = summaries[subject]
        checkpoint = Path(row["checkpoint_path"])
        if checkpoint.parent.resolve() != FEATURE_DIR.resolve():
            raise Experiment10Error(f"Unexpected feature checkpoint location for {subject}.")
        if not checkpoint.is_file() or _sha256(checkpoint) != row["checkpoint_sha256"]:
            raise Experiment10Error(f"Feature checkpoint hash mismatch for {subject}.")
        with np.load(checkpoint, allow_pickle=False) as saved:
            if str(saved["feature_version"].item()) != FEATURE_VERSION:
                raise Experiment10Error(f"Feature version mismatch for {subject}.")
            if saved["feature_names"].tolist() != expected_names:
                raise Experiment10Error(f"Feature-name mismatch for {subject}.")
            if str(saved["source_sha256"].item()) != row["source_pickle_sha256"]:
                raise Experiment10Error(f"Source hash mismatch in checkpoint for {subject}.")
            data[subject] = {
                "features": saved["features"].astype(np.float64),
                "labels": saved["labels"].astype(np.int32) - 1,
                "start_seconds": saved["start_seconds"].astype(np.float64),
                "phase": saved["phase"].astype(np.int8),
            }
        if not set(np.unique(data[subject]["labels"]).tolist()).issubset(LABEL_NAMES):
            raise Experiment10Error(f"Unexpected label for {subject}.")
    return protocol, exp9, data


def _fold_subjects(test_index: int, repetition: int) -> tuple[list[str], list[str]]:
    test_subject = SUBJECTS[test_index]
    remaining = [subject for subject in SUBJECTS if subject != test_subject]
    offset = (test_index + repetition * 4) % len(remaining)
    calibration = [remaining[(offset + index) % len(remaining)] for index in range(4)]
    training = [subject for subject in remaining if subject not in calibration]
    if len(training) != 10 or len(set(calibration)) != 4:
        raise Experiment10Error("Invalid subject-disjoint fold construction.")
    return training, calibration


def _personal_partitions(
    labels: np.ndarray,
    subject_index: int,
    repetition: int,
) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray]]:
    rng = np.random.default_rng(100_000 + subject_index * 101 + repetition * 7)
    test_parts: list[np.ndarray] = []
    pool_by_label: dict[int, np.ndarray] = {}
    for label in LABEL_NAMES:
        indices = np.flatnonzero(labels == label)
        if len(indices) < TEST_COUNTS[label] + PERSONAL_ALLOCATIONS[12][label]:
            raise Experiment10Error(
                f"Subject lacks windows required by frozen allocation for class {label}."
            )
        permuted = rng.permutation(indices)
        test_parts.append(permuted[: TEST_COUNTS[label]])
        pool_by_label[label] = permuted[TEST_COUNTS[label] :]
    test = np.sort(np.concatenate(test_parts))
    onboarding = np.sort(np.concatenate(list(pool_by_label.values())))
    personal: dict[int, np.ndarray] = {}
    for count, allocation in PERSONAL_ALLOCATIONS.items():
        selected = np.concatenate(
            [pool_by_label[label][: allocation[label]] for label in LABEL_NAMES]
        )
        personal[count] = np.sort(selected)
        if len(selected) != count or set(selected) & set(test):
            raise Experiment10Error("Personal calibration/test partition contract failed.")
    if not all(set(personal[left]).issubset(personal[right]) for left, right in ((3, 6), (6, 9), (9, 12))):
        raise Experiment10Error("Personal calibration schedule is not nested.")
    return test, onboarding, personal


def _compatibility_distance(model: dict[str, np.ndarray], left: np.ndarray, right: np.ndarray) -> float:
    left_standardized = (left - model["mean"]) / model["scale"]
    right_standardized = (right - model["mean"]) / model["scale"]
    return float(
        np.linalg.norm(left_standardized.mean(axis=0) - right_standardized.mean(axis=0))
        / np.sqrt(left.shape[1])
    )


def _evaluate(
    true_calibration_scores: np.ndarray,
    test_scores: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    threshold = _conformal_quantile(true_calibration_scores, ALPHA)
    sets = test_scores <= threshold
    covered = sets[np.arange(len(test_labels)), test_labels]
    set_sizes = sets.sum(axis=1)
    coverage_by_class = {
        LABEL_NAMES[label]: float(covered[test_labels == label].mean())
        for label in LABEL_NAMES
    }
    return {
        "calibration_score_count": int(len(true_calibration_scores)),
        "threshold": float(threshold) if np.isfinite(threshold) else None,
        "threshold_status": "FINITE" if np.isfinite(threshold) else "INFINITE",
        "coverage": float(covered.mean()),
        "coverage_by_class": coverage_by_class,
        "average_prediction_set_size": float(set_sizes.mean()),
        "full_set_frequency": float(np.mean(set_sizes == 3)),
        "empty_set_frequency": float(np.mean(set_sizes == 0)),
        "robustness_loss": float(abs(float(covered.mean()) - TARGET) + 0.25 * np.mean(set_sizes == 3)),
    }


def _true_scores(model: dict[str, np.ndarray], features: np.ndarray, labels: np.ndarray) -> np.ndarray:
    probabilities, distances = _model_outputs(model, features)
    scores = _score_matrix("inverse_probability_score", probabilities, distances)
    return scores[np.arange(len(labels)), labels]


def _run_all_folds(data: dict[str, dict[str, np.ndarray]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    compatibility_rows: list[dict[str, Any]] = []
    for test_index, test_subject in enumerate(SUBJECTS):
        subject = data[test_subject]
        for repetition in range(REPETITIONS):
            training_subjects, external_subjects = _fold_subjects(test_index, repetition)
            test_indices, onboarding_indices, personal_indices = _personal_partitions(
                subject["labels"], test_index, repetition
            )
            train_x = np.concatenate([data[item]["features"] for item in training_subjects])
            train_y = np.concatenate([data[item]["labels"] for item in training_subjects])
            model = _fit_regularized_lda(train_x, train_y)

            test_x = subject["features"][test_indices]
            test_y = subject["labels"][test_indices]
            test_probabilities, test_distances = _model_outputs(model, test_x)
            test_scores = _score_matrix(
                "inverse_probability_score", test_probabilities, test_distances
            )
            predicted = np.argmax(test_probabilities, axis=1)
            accuracy = float(np.mean(predicted == test_y))
            true_probability = np.clip(
                test_probabilities[np.arange(len(test_y)), test_y], 1e-12, 1.0
            )
            log_loss = float(-np.log(true_probability).mean())
            onboarding_x = subject["features"][onboarding_indices]
            shift_distance = _compatibility_distance(model, onboarding_x, train_x)

            external_scores: dict[str, np.ndarray] = {}
            distances_by_subject: dict[str, float] = {}
            for external in external_subjects:
                external_scores[external] = _true_scores(
                    model, data[external]["features"], data[external]["labels"]
                )
                distances_by_subject[external] = _compatibility_distance(
                    model, onboarding_x, data[external]["features"]
                )
            ordered = sorted(external_subjects, key=lambda item: (distances_by_subject[item], item))
            nearest = ordered[:2]
            farthest = ordered[-2:]

            common = {
                "test_subject": test_subject,
                "repetition": repetition,
                "training_subjects": training_subjects,
                "external_calibration_subjects": external_subjects,
                "nearest_external_subjects": nearest,
                "farthest_external_subjects": farthest,
                "personal_test_indices": test_indices.tolist(),
                "onboarding_pool_indices": onboarding_indices.tolist(),
                "personal_test_window_count": int(len(test_indices)),
                "onboarding_pool_window_count": int(len(onboarding_indices)),
                "base_classifier_accuracy": accuracy,
                "base_classifier_log_loss": log_loss,
                "feature_shift_distance": shift_distance,
                "compatibility_distance_by_external_subject": distances_by_subject,
            }
            external_methods = {
                "external_all4": external_subjects,
                "external_nearest2": nearest,
                "external_farthest2": farthest,
            }
            for method, selected in external_methods.items():
                scores = np.concatenate([external_scores[item] for item in selected])
                results.append(
                    {
                        **common,
                        "method_id": method,
                        "calibration_source": "external_subjects",
                        "selected_calibration_subjects": selected,
                        "personal_labeled_window_count": 0,
                        "personal_calibration_indices": [],
                        **_evaluate(scores, test_scores, test_y),
                    }
                )
            for count, indices in personal_indices.items():
                scores = _true_scores(
                    model, subject["features"][indices], subject["labels"][indices]
                )
                results.append(
                    {
                        **common,
                        "method_id": f"personal_k{count}",
                        "calibration_source": "held_out_subject_labeled_onboarding",
                        "selected_calibration_subjects": [test_subject],
                        "personal_labeled_window_count": count,
                        "personal_calibration_indices": indices.tolist(),
                        **_evaluate(scores, test_scores, test_y),
                    }
                )
            for external in external_subjects:
                metrics = _evaluate(external_scores[external], test_scores, test_y)
                compatibility_rows.append(
                    {
                        "test_subject": test_subject,
                        "repetition": repetition,
                        "external_calibration_subject": external,
                        "compatibility_distance": distances_by_subject[external],
                        **metrics,
                    }
                )
    return results, compatibility_rows


def _checkpoint_fingerprint(exp9: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "experiment_9_report_sha256": _sha256(EXP9_REPORT),
        "feature_checkpoint_hashes": {
            row["subject_id"]: row["checkpoint_sha256"]
            for row in exp9["subject_feature_summary"]
        },
    }


def _load_or_run_folds(
    data: dict[str, dict[str, np.ndarray]],
    exp9: dict[str, Any],
    use_checkpoint: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    fingerprint = _checkpoint_fingerprint(exp9)
    if use_checkpoint and FOLD_CHECKPOINT.is_file():
        saved = _read_json(FOLD_CHECKPOINT)
        if saved.get("fingerprint") == fingerprint:
            results = saved.get("fold_results")
            compatibility = saved.get("compatibility_rows")
            if isinstance(results, list) and isinstance(compatibility, list):
                _validate_fold_rows(results, compatibility)
                print("Reused valid Experiment 10 fold checkpoint.", flush=True)
                return results, compatibility, True
    results, compatibility = _run_all_folds(data)
    _validate_fold_rows(results, compatibility)
    _atomic_json(
        FOLD_CHECKPOINT,
        {
            "fingerprint": fingerprint,
            "fold_results": results,
            "compatibility_rows": compatibility,
        },
    )
    print("Saved valid Experiment 10 fold checkpoint.", flush=True)
    return results, compatibility, False


def _validate_fold_rows(results: list[dict[str, Any]], compatibility: list[dict[str, Any]]) -> None:
    expected = len(SUBJECTS) * REPETITIONS * len(METHODS)
    if len(results) != expected:
        raise Experiment10Error(f"Expected {expected} fold rows, found {len(results)}.")
    keys = {(row["test_subject"], row["repetition"], row["method_id"]) for row in results}
    if len(keys) != expected:
        raise Experiment10Error("Experiment 10 fold keys are duplicated or missing.")
    if len(compatibility) != len(SUBJECTS) * REPETITIONS * 4:
        raise Experiment10Error("Compatibility row grid is incomplete.")
    for row in results:
        if row["test_subject"] in row["training_subjects"] or row["test_subject"] in row["external_calibration_subjects"]:
            raise Experiment10Error("Held-out subject leaked into external train/calibration partitions.")
        if set(row["training_subjects"]) & set(row["external_calibration_subjects"]):
            raise Experiment10Error("External train/calibration subject overlap detected.")
        if set(row["personal_test_indices"]) & set(row["personal_calibration_indices"]):
            raise Experiment10Error("Personal test/calibration window overlap detected.")
        if row["personal_test_window_count"] != 15:
            raise Experiment10Error("Personal test window count differs from frozen protocol.")
        if row["method_id"].startswith("personal_k"):
            count = int(row["method_id"].split("k", 1)[1])
            if row["personal_labeled_window_count"] != count or row["calibration_score_count"] != count:
                raise Experiment10Error("Personal calibration count mismatch.")
            expected_status = "INFINITE" if count < 9 else "FINITE"
            if row["threshold_status"] != expected_status:
                raise Experiment10Error("Personal finite-threshold boundary violated.")
        for field in ("coverage", "full_set_frequency", "empty_set_frequency", "base_classifier_accuracy"):
            if not 0.0 <= row[field] <= 1.0:
                raise Experiment10Error(f"Fold metric outside [0,1]: {field}")
        if not 0.0 <= row["average_prediction_set_size"] <= 3.0:
            raise Experiment10Error("Prediction-set size outside [0,3].")


def _aggregate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: list[dict[str, Any]] = []
    for method in METHODS:
        rows = [row for row in results if row["method_id"] == method]
        subject_coverage = {
            subject: float(np.mean([row["coverage"] for row in rows if row["test_subject"] == subject]))
            for subject in SUBJECTS
        }
        subject_full = {
            subject: float(np.mean([row["full_set_frequency"] for row in rows if row["test_subject"] == subject]))
            for subject in SUBJECTS
        }
        subject_size = {
            subject: float(np.mean([row["average_prediction_set_size"] for row in rows if row["test_subject"] == subject]))
            for subject in SUBJECTS
        }
        class_coverage = {
            name: float(np.mean([row["coverage_by_class"][name] for row in rows]))
            for name in LABEL_NAMES.values()
        }
        aggregates.append(
            {
                "method_id": method,
                "fold_count": len(rows),
                "mean_coverage": float(np.mean([row["coverage"] for row in rows])),
                "worst_subject_mean_coverage": float(min(subject_coverage.values())),
                "mean_prediction_set_size": float(np.mean([row["average_prediction_set_size"] for row in rows])),
                "mean_full_set_frequency": float(np.mean([row["full_set_frequency"] for row in rows])),
                "mean_empty_set_frequency": float(np.mean([row["empty_set_frequency"] for row in rows])),
                "finite_threshold_fraction": float(np.mean([row["threshold_status"] == "FINITE" for row in rows])),
                "mean_robustness_loss": float(np.mean([row["robustness_loss"] for row in rows])),
                "coverage_by_class": class_coverage,
                "subject_mean_coverage": subject_coverage,
                "subject_mean_full_set_frequency": subject_full,
                "subject_mean_prediction_set_size": subject_size,
            }
        )
    return aggregates


def _find(aggregates: list[dict[str, Any]], method: str) -> dict[str, Any]:
    matches = [row for row in aggregates if row["method_id"] == method]
    if len(matches) != 1:
        raise Experiment10Error(f"Unable to find aggregate method: {method}")
    return matches[0]


def _bootstrap_difference(left: dict[str, float], right: dict[str, float], seed: int) -> dict[str, Any]:
    differences = np.asarray([left[subject] - right[subject] for subject in SUBJECTS])
    rng = np.random.default_rng(seed)
    boot = np.asarray(
        [rng.choice(differences, size=len(differences), replace=True).mean() for _ in range(5000)]
    )
    return {
        "paired_subject_mean_difference": float(differences.mean()),
        "bootstrap_95_percent_lower": float(np.quantile(boot, 0.025)),
        "bootstrap_95_percent_upper": float(np.quantile(boot, 0.975)),
        "bootstrap_iterations": 5000,
        "bootstrap_seed": seed,
    }


def _subject_diagnostics(results: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all4 = _find(aggregates, "external_all4")
    personal = _find(aggregates, "personal_k12")
    rows: list[dict[str, Any]] = []
    for subject in SUBJECTS:
        base_rows = [
            row for row in results
            if row["test_subject"] == subject and row["method_id"] == "external_all4"
        ]
        rows.append(
            {
                "subject_id": subject,
                "base_classifier_accuracy": float(np.mean([row["base_classifier_accuracy"] for row in base_rows])),
                "base_classifier_log_loss": float(np.mean([row["base_classifier_log_loss"] for row in base_rows])),
                "feature_shift_distance": float(np.mean([row["feature_shift_distance"] for row in base_rows])),
                "external_all4_coverage": all4["subject_mean_coverage"][subject],
                "personal_k12_coverage": personal["subject_mean_coverage"][subject],
                "personal_k12_coverage_change": float(
                    personal["subject_mean_coverage"][subject] - all4["subject_mean_coverage"][subject]
                ),
                "external_all4_full_set_frequency": all4["subject_mean_full_set_frequency"][subject],
                "personal_k12_full_set_frequency": personal["subject_mean_full_set_frequency"][subject],
            }
        )
    return rows


def _analyze(
    results: list[dict[str, Any]],
    compatibility_rows: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
) -> dict[str, Any]:
    all4 = _find(aggregates, "external_all4")
    nearest = _find(aggregates, "external_nearest2")
    farthest = _find(aggregates, "external_farthest2")
    personal = _find(aggregates, "personal_k12")
    general_delta = float(personal["mean_coverage"] - all4["mean_coverage"])
    worst_delta = float(personal["worst_subject_mean_coverage"] - all4["worst_subject_mean_coverage"])
    full_delta = float(personal["mean_full_set_frequency"] - all4["mean_full_set_frequency"])
    general_repair = bool(general_delta >= 0.05 and worst_delta >= 0.10 and full_delta <= 0.20)

    targeted: dict[str, Any] = {}
    targeted_passes: list[bool] = []
    persistent: list[str] = []
    for subject in ("S2", "S4"):
        coverage_delta = float(
            personal["subject_mean_coverage"][subject] - all4["subject_mean_coverage"][subject]
        )
        subject_full_delta = float(
            personal["subject_mean_full_set_frequency"][subject]
            - all4["subject_mean_full_set_frequency"][subject]
        )
        passes = bool(
            coverage_delta >= 0.10
            and personal["subject_mean_coverage"][subject] >= 0.80
            and subject_full_delta <= 0.20
        )
        targeted_passes.append(passes)
        remains = bool(
            personal["subject_mean_coverage"][subject] < 0.80 or subject_full_delta > 0.20
        )
        if remains:
            persistent.append(subject)
        targeted[subject] = {
            "external_all4_coverage": all4["subject_mean_coverage"][subject],
            "personal_k12_coverage": personal["subject_mean_coverage"][subject],
            "coverage_change": coverage_delta,
            "external_all4_full_set_frequency": all4["subject_mean_full_set_frequency"][subject],
            "personal_k12_full_set_frequency": personal["subject_mean_full_set_frequency"][subject],
            "full_set_frequency_change": subject_full_delta,
            "repair_rule_met": passes,
            "persistent_difficulty_rule_met": remains,
        }
    s2_s4_repair = bool(all(targeted_passes))

    compatibility_loss_improvement = float(
        farthest["mean_robustness_loss"] - nearest["mean_robustness_loss"]
    )
    compatibility_supported = bool(compatibility_loss_improvement >= 0.03)
    distances = np.asarray([row["compatibility_distance"] for row in compatibility_rows])
    losses = np.asarray([row["robustness_loss"] for row in compatibility_rows])
    distance_loss_correlation = float(np.corrcoef(distances, losses)[0, 1])

    if general_repair and compatibility_supported:
        decision = "PERSONAL_AND_COMPATIBILITY_REPAIR_SUPPORTED"
    elif general_repair:
        decision = "PERSONAL_CALIBRATION_REPAIR_SUPPORTED"
    elif compatibility_supported:
        decision = "COMPATIBILITY_SELECTION_SUPPORTED_PERSONAL_REPAIR_NOT_SUPPORTED"
    elif persistent:
        decision = "CALIBRATION_ALONE_DOES_NOT_REPAIR_DIFFICULT_SUBJECTS"
    else:
        decision = "INCONCLUSIVE_ONBOARDING_BRIDGE"
    return {
        "primary_decision": decision,
        "general_personal_repair": {
            "supported": general_repair,
            "mean_coverage_change_k12_vs_external_all4": general_delta,
            "worst_subject_coverage_change": worst_delta,
            "mean_full_set_frequency_change": full_delta,
            "paired_subject_bootstrap": _bootstrap_difference(
                personal["subject_mean_coverage"], all4["subject_mean_coverage"], 101010
            ),
        },
        "s2_s4_personal_repair": {
            "supported": s2_s4_repair,
            "subjects": targeted,
            "persistent_difficulty_subjects": persistent,
        },
        "compatibility_selection": {
            "supported": compatibility_supported,
            "nearest2_mean_robustness_loss": nearest["mean_robustness_loss"],
            "farthest2_mean_robustness_loss": farthest["mean_robustness_loss"],
            "robustness_loss_improvement": compatibility_loss_improvement,
            "single_external_subject_distance_loss_correlation": distance_loss_correlation,
            "nearest2_minus_farthest2_coverage_bootstrap": _bootstrap_difference(
                nearest["subject_mean_coverage"], farthest["subject_mean_coverage"], 101011
            ),
        },
        "finite_sample_boundary": {
            method: {
                "finite_threshold_fraction": _find(aggregates, method)["finite_threshold_fraction"],
                "mean_full_set_frequency": _find(aggregates, method)["mean_full_set_frequency"],
            }
            for method in ("personal_k3", "personal_k6", "personal_k9", "personal_k12")
        },
    }


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment10Error("Experiment name mismatch.")
    _validate_fold_rows(report.get("fold_results", []), report.get("compatibility_rows", []))
    aggregates = report.get("aggregate_results", [])
    if len(aggregates) != len(METHODS) or {row["method_id"] for row in aggregates} != set(METHODS):
        raise Experiment10Error("Aggregate method grid is incomplete.")
    if len(report.get("subject_diagnostics", [])) != len(SUBJECTS):
        raise Experiment10Error("Subject diagnostics are incomplete.")
    if report.get("validation", {}).get("experiment_9_validation_reused") is not True:
        raise Experiment10Error("Experiment 9 validation was not reused.")
    if report.get("validation", {}).get("model_call_used") is not False:
        raise Experiment10Error("Experiment 10 unexpectedly used a model call.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, exp9, data = _load_prerequisites()
    results, compatibility, _checkpoint_reused = _load_or_run_folds(
        data, exp9, use_checkpoint=use_checkpoint
    )
    aggregates = _aggregate(results)
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": (
            "Can limited personal calibration or unlabeled subject-calibration compatibility "
            "bridge the cold-start coverage failures observed in WESAD, especially for S2 and S4?"
        ),
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "experiment_9_checkpoint_source": {
            "path": str(EXP9_REPORT.resolve()),
            "sha256": _sha256(EXP9_REPORT),
            "validation_path": str(EXP9_VALIDATION.resolve()),
            "validation_sha256": _sha256(EXP9_VALIDATION),
            "feature_version": FEATURE_VERSION,
            "feature_checkpoint_hashes": _checkpoint_fingerprint(exp9)["feature_checkpoint_hashes"],
        },
        "fold_contract": {
            "subject_count": len(SUBJECTS),
            "repetitions_per_subject": REPETITIONS,
            "methods": list(METHODS),
            "test_windows_per_fold": 15,
            "target_coverage": TARGET,
            "score": "inverse_probability_score",
        },
        "fold_results": results,
        "compatibility_rows": compatibility,
        "aggregate_results": aggregates,
        "subject_diagnostics": _subject_diagnostics(results, aggregates),
        "analysis": _analyze(results, compatibility, aggregates),
        "limitations": [
            "S2 and S4 are exploratory cases selected after Experiment 9, not an independent confirmation cohort.",
            "Only 15 personal test windows are available per fold under the non-overlapping window contract.",
            "Personal calibration changes the conformal threshold but does not retrain the classifier.",
            "Centroid distance is a simple compatibility proxy and does not establish a physiological mechanism.",
            "All data come from one 15-subject benchmark and require external replication.",
        ],
        "validation": {
            "protocol_frozen_before_outcome_analysis": True,
            "experiment_9_validation_reused": True,
            "feature_checkpoint_hashes_verified": True,
            "raw_wesad_pickles_loaded": False,
            "raw_dataset_mutated": False,
            "personal_test_calibration_overlap": False,
            "test_labels_used_for_compatibility_selection": False,
            "classifier_personalized": False,
            "model_call_used": False,
            "api_key_required": False,
            "fold_checkpoint_reuse_supported": True,
        },
    }
    return validate_report(report)


def render_markdown(report: dict[str, Any]) -> str:
    analysis = report["analysis"]
    aggregates = {row["method_id"]: row for row in report["aggregate_results"]}
    lines = [
        f"# {EXPERIMENT_NAME}",
        "",
        "## Result",
        "",
        f"**{analysis['primary_decision']}**",
        "",
        "This experiment bridges cold-start external calibration and limited personal calibration while keeping the classifier fixed.",
        "",
        "## Calibration onboarding curve",
        "",
        "| Method | Mean coverage | Worst subject | Mean set size | Full sets | Finite thresholds |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        row = aggregates[method]
        lines.append(
            f"| {method} | {row['mean_coverage']:.4f} | {row['worst_subject_mean_coverage']:.4f} | "
            f"{row['mean_prediction_set_size']:.4f} | {row['mean_full_set_frequency']:.4f} | "
            f"{row['finite_threshold_fraction']:.4f} |"
        )
    general = analysis["general_personal_repair"]
    lines.extend(
        [
            "",
            "## Preregistered personal-repair decision",
            "",
            f"- Supported: {general['supported']}",
            f"- Mean coverage change, k=12 versus external all4: {general['mean_coverage_change_k12_vs_external_all4']:.4f}",
            f"- Worst-subject coverage change: {general['worst_subject_coverage_change']:.4f}",
            f"- Mean full-set-frequency change: {general['mean_full_set_frequency_change']:.4f}",
            "",
            "## S2 and S4",
            "",
            "| Subject | External coverage | Personal k=12 coverage | Change | External full sets | Personal full sets | Repair | Persistent |",
            "|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for subject, row in analysis["s2_s4_personal_repair"]["subjects"].items():
        lines.append(
            f"| {subject} | {row['external_all4_coverage']:.4f} | {row['personal_k12_coverage']:.4f} | "
            f"{row['coverage_change']:.4f} | {row['external_all4_full_set_frequency']:.4f} | "
            f"{row['personal_k12_full_set_frequency']:.4f} | {row['repair_rule_met']} | "
            f"{row['persistent_difficulty_rule_met']} |"
        )
    compatibility = analysis["compatibility_selection"]
    lines.extend(
        [
            "",
            "## Calibration compatibility",
            "",
            f"- Supported: {compatibility['supported']}",
            f"- Nearest-two robustness loss: {compatibility['nearest2_mean_robustness_loss']:.4f}",
            f"- Farthest-two robustness loss: {compatibility['farthest2_mean_robustness_loss']:.4f}",
            f"- Robustness-loss improvement: {compatibility['robustness_loss_improvement']:.4f}",
            f"- Single-subject distance/loss correlation: {compatibility['single_external_subject_distance_loss_correlation']:.4f}",
            "",
            "## Finite-sample boundary",
            "",
        ]
    )
    for method, row in analysis["finite_sample_boundary"].items():
        lines.append(
            f"- {method}: finite thresholds {row['finite_threshold_fraction']:.1%}; full sets {row['mean_full_set_frequency']:.1%}"
        )
    lines.extend(
        [
            "",
            "## Subject diagnostics",
            "",
            "| Subject | Accuracy | Log loss | Feature shift | External coverage | Personal k=12 | Change |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["subject_diagnostics"]:
        lines.append(
            f"| {row['subject_id']} | {row['base_classifier_accuracy']:.4f} | "
            f"{row['base_classifier_log_loss']:.4f} | {row['feature_shift_distance']:.4f} | "
            f"{row['external_all4_coverage']:.4f} | {row['personal_k12_coverage']:.4f} | "
            f"{row['personal_k12_coverage_change']:.4f} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "- Reused hash-validated Experiment 9 features: yes",
            "- Raw WESAD pickle loading: no",
            "- Model/API call: no",
            "- Test labels used for compatibility selection: no",
            "- Independent exact replay: pending",
            "",
        ]
    )
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic local replay from hash-validated Experiment 9 feature checkpoints",
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "experiment_9_report_sha256": report["experiment_9_checkpoint_source"]["sha256"],
        "experiment_9_validation_sha256": report["experiment_9_checkpoint_source"]["validation_sha256"],
        "feature_checkpoint_hashes": report["experiment_9_checkpoint_source"]["feature_checkpoint_hashes"],
        "subject_count": len(SUBJECTS),
        "fold_result_count": len(report["fold_results"]),
        "compatibility_row_count": len(report["compatibility_rows"]),
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
            f"- Experiment 9 report SHA-256: `{summary['experiment_9_report_sha256']}`",
            f"- Experiment 9 validation SHA-256: `{summary['experiment_9_validation_sha256']}`",
            f"- Subjects: {summary['subject_count']}",
            f"- Fold results: {summary['fold_result_count']}",
            f"- Compatibility rows: {summary['compatibility_row_count']}",
            "- Model/API call: no",
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
    print(f"Experiment 10 complete: {report['analysis']['primary_decision']}")
    print(
        f"Fold results: {len(report['fold_results'])}; compatibility rows: "
        f"{len(report['compatibility_rows'])}"
    )


if __name__ == "__main__":
    main()
