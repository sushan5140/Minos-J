"""Execute Meno-J Experiment 12 from validated WESAD feature checkpoints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import run_experiment_10_calibration_bridge as exp10
import run_experiment_11_representation_calibration as exp11
from run_experiment_9_wesad_real_data import SUBJECTS, feature_names


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_12_preregistered_protocol.json"
EXP11_REPORT = OUTPUT_DIR / "meno_j_experiment_11_representation_calibration.json"
EXP11_VALIDATION = OUTPUT_DIR / "meno_j_experiment_11_validation.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_12_temporal_readiness_surface.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_12_temporal_readiness_surface.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_12_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_12_reproducibility_summary.md"
CHECKPOINT = PROJECT_DIR / "work" / "experiment_12_checkpoints" / "result_rows.json"

EXPERIMENT_NAME = "Meno-J Experiment 12: Temporal Readiness-Surface Replication"
ALPHA = 0.10
TARGET = 0.90
REPETITIONS = 3
PHASE_NAMES = {0: "early", 1: "middle", 2: "late"}
LABEL_NAMES = exp10.LABEL_NAMES
ALLOCATIONS = {
    9: {0: 4, 1: 3, 2: 2},
    18: {0: 9, 1: 6, 2: 3},
    19: {0: 10, 1: 6, 2: 3},
    20: {0: 11, 1: 6, 2: 3},
}
ARMS = (
    "lda_raw_all",
    "lda_raw_without_Temp",
    "lda_subject_robust_normalized_all",
    "lda_subject_robust_normalized_without_Temp",
)


class Experiment12Error(RuntimeError):
    """Raised when Experiment 12 violates its frozen contract."""


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
        raise Experiment12Error(f"Required valid JSON is unavailable: {path}") from exc
    if not isinstance(value, dict):
        raise Experiment12Error(f"Expected a JSON object: {path}")
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
    validation = _read_json(EXP11_VALIDATION)
    exp11_report = _read_json(EXP11_REPORT)
    if protocol.get("protocol_status") != "FROZEN_BEFORE_EXPERIMENT_12_OUTCOME_ANALYSIS":
        raise Experiment12Error("Experiment 12 protocol is not frozen.")
    if validation.get("status") != "PASS":
        raise Experiment12Error("Experiment 11 independent validation has not passed.")
    _, _, data = exp10._load_prerequisites()
    expected_hashes = exp11_report["prerequisites"]["feature_checkpoint_hashes"]
    for subject in SUBJECTS:
        checkpoint = exp10.FEATURE_DIR / f"{subject}.npz"
        if _sha256(checkpoint) != expected_hashes[subject]:
            raise Experiment12Error(f"Feature checkpoint changed for {subject}.")
    return protocol, exp11_report, data


def _feature_indices(arm: str) -> np.ndarray:
    names = feature_names()
    if arm.endswith("_all"):
        return np.arange(len(names), dtype=int)
    if arm.endswith("_without_Temp"):
        indices = np.asarray(
            [index for index, name in enumerate(names) if not name.startswith("Temp_")],
            dtype=int,
        )
        if len(indices) == len(names):
            raise Experiment12Error("Temperature ablation did not remove features.")
        return indices
    raise Experiment12Error(f"Unknown arm: {arm}")


def _phase_partitions(
    labels: np.ndarray,
    phases: np.ndarray,
    subject_index: int,
    test_phase: int,
    repetition: int,
) -> tuple[np.ndarray, np.ndarray, dict[int, np.ndarray]]:
    test = np.flatnonzero(phases == test_phase)
    pool = np.flatnonzero(phases != test_phase)
    rng = np.random.default_rng(
        200_000 + subject_index * 1009 + test_phase * 101 + repetition * 11
    )
    pool_by_label: dict[int, np.ndarray] = {}
    for label in LABEL_NAMES:
        candidates = pool[labels[pool] == label]
        if len(candidates) < ALLOCATIONS[20][label]:
            raise Experiment12Error(
                f"Insufficient phase-disjoint calibration windows for label {label}."
            )
        pool_by_label[label] = rng.permutation(candidates)
    personal: dict[int, np.ndarray] = {}
    for count, allocation in ALLOCATIONS.items():
        selected = np.sort(
            np.concatenate(
                [pool_by_label[label][: allocation[label]] for label in LABEL_NAMES]
            )
        )
        if len(selected) != count or set(selected) & set(test):
            raise Experiment12Error("Temporal test/calibration separation failed.")
        personal[count] = selected
    counts = list(ALLOCATIONS)
    if not all(set(personal[a]).issubset(personal[b]) for a, b in zip(counts, counts[1:])):
        raise Experiment12Error("Temporal calibration schedule is not nested.")
    return np.sort(test), np.sort(pool), personal


def _arm_arrays(
    data: dict[str, dict[str, np.ndarray]],
    training_subjects: list[str],
    test_subject: str,
    pool_indices: np.ndarray,
    feature_indices: np.ndarray,
    normalized: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_parts: list[np.ndarray] = []
    train_labels: list[np.ndarray] = []
    for subject in training_subjects:
        values = data[subject]["features"][:, feature_indices]
        if normalized:
            center, scale = exp11._robust_stats(values)
            values = (values - center) / scale
        train_parts.append(values)
        train_labels.append(data[subject]["labels"])
    heldout = data[test_subject]["features"][:, feature_indices]
    if normalized:
        center, scale = exp11._robust_stats(heldout[pool_indices])
        heldout = (heldout - center) / scale
    return np.concatenate(train_parts), np.concatenate(train_labels), heldout


def _run(data: dict[str, dict[str, np.ndarray]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subject_index, test_subject in enumerate(SUBJECTS):
        heldout = data[test_subject]
        for test_phase in PHASE_NAMES:
            training_subjects, external_subjects = exp10._fold_subjects(subject_index, test_phase)
            # The pool/test split does not depend on repetition; the nested labeled
            # calibration draw does. Construct repetition zero here for the pool.
            test_indices, pool_indices, _ = _phase_partitions(
                heldout["labels"], heldout["phase"], subject_index, test_phase, 0
            )
            arm_cache: dict[str, dict[str, Any]] = {}
            for arm in ARMS:
                normalized = "normalized" in arm
                indices = _feature_indices(arm)
                train_x, train_y, transformed_heldout = _arm_arrays(
                    data,
                    training_subjects,
                    test_subject,
                    pool_indices,
                    indices,
                    normalized,
                )
                model = exp11._fit_lda(train_x, train_y)
                arm_cache[arm] = {
                    "model": model,
                    "heldout": transformed_heldout,
                    "test_probabilities": exp11._predict_probabilities(
                        model, transformed_heldout[test_indices]
                    ),
                    "test_labels": heldout["labels"][test_indices],
                    "feature_count": int(len(indices)),
                }

            for repetition in range(REPETITIONS):
                repeated_test, repeated_pool, personal = _phase_partitions(
                    heldout["labels"],
                    heldout["phase"],
                    subject_index,
                    test_phase,
                    repetition,
                )
                if not np.array_equal(test_indices, repeated_test) or not np.array_equal(
                    pool_indices, repeated_pool
                ):
                    raise Experiment12Error("Temporal partition changed across calibration draws.")
                for arm in ARMS:
                    cached = arm_cache[arm]
                    for count, calibration_indices in personal.items():
                        calibration_probabilities = exp11._predict_probabilities(
                            cached["model"], cached["heldout"][calibration_indices]
                        )
                        rows.append(
                            {
                                "test_subject": test_subject,
                                "test_phase": PHASE_NAMES[test_phase],
                                "test_phase_code": test_phase,
                                "repetition": repetition,
                                "training_subjects": training_subjects,
                                "unused_external_subjects": external_subjects,
                                "arm_id": arm,
                                "normalized": "normalized" in arm,
                                "temperature_features_included": "without_Temp" not in arm,
                                "feature_count": cached["feature_count"],
                                "personal_calibration_count": count,
                                "test_indices": test_indices.tolist(),
                                "normalization_pool_indices": pool_indices.tolist(),
                                "personal_calibration_indices": calibration_indices.tolist(),
                                "test_class_counts": {
                                    LABEL_NAMES[label]: int(
                                        np.sum(cached["test_labels"] == label)
                                    )
                                    for label in LABEL_NAMES
                                },
                                **exp11._evaluate(
                                    calibration_probabilities,
                                    heldout["labels"][calibration_indices],
                                    cached["test_probabilities"],
                                    cached["test_labels"],
                                ),
                            }
                        )
    return rows


def _fingerprint(exp11_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "experiment_11_report_sha256": _sha256(EXP11_REPORT),
        "experiment_11_validation_sha256": _sha256(EXP11_VALIDATION),
        "feature_checkpoint_hashes": exp11_report["prerequisites"]["feature_checkpoint_hashes"],
    }


def _validate_rows(rows: list[dict[str, Any]]) -> None:
    expected = len(SUBJECTS) * len(PHASE_NAMES) * REPETITIONS * len(ARMS) * len(ALLOCATIONS)
    if len(rows) != expected:
        raise Experiment12Error(f"Expected {expected} rows, received {len(rows)}.")
    keys = {
        (
            row["test_subject"],
            row["test_phase"],
            row["repetition"],
            row["arm_id"],
            row["personal_calibration_count"],
        )
        for row in rows
    }
    if len(keys) != expected:
        raise Experiment12Error("Experiment 12 result keys are duplicated or missing.")
    for row in rows:
        if row["test_subject"] in row["training_subjects"] or row["test_subject"] in row[
            "unused_external_subjects"
        ]:
            raise Experiment12Error("Held-out subject leakage detected.")
        test = set(row["test_indices"])
        calibration = set(row["personal_calibration_indices"])
        pool = set(row["normalization_pool_indices"])
        if test & calibration or test & pool or not calibration.issubset(pool):
            raise Experiment12Error("Temporal test/calibration/normalization leakage detected.")
        count = row["personal_calibration_count"]
        if len(calibration) != count or row["calibration_score_count"] != count:
            raise Experiment12Error("Calibration count mismatch.")
        expected_rank = int(np.ceil((count + 1) * (1 - ALPHA)))
        if row["conformal_rank"] != expected_rank or row["threshold_status"] != "FINITE":
            raise Experiment12Error("Conformal order-statistic contract failed.")
    for subject in SUBJECTS:
        for phase in PHASE_NAMES.values():
            for repetition in range(REPETITIONS):
                for arm in ARMS:
                    cells = [
                        row for row in rows
                        if row["test_subject"] == subject
                        and row["test_phase"] == phase
                        and row["repetition"] == repetition
                        and row["arm_id"] == arm
                    ]
                    cells.sort(key=lambda row: row["personal_calibration_count"])
                    if len(cells) != len(ALLOCATIONS) or not all(
                        set(left["personal_calibration_indices"]).issubset(
                            right["personal_calibration_indices"]
                        )
                        for left, right in zip(cells, cells[1:])
                    ):
                        raise Experiment12Error("Nested calibration validation failed.")


def _load_or_run(
    data: dict[str, dict[str, np.ndarray]],
    exp11_report: dict[str, Any],
    use_checkpoint: bool,
) -> list[dict[str, Any]]:
    fingerprint = _fingerprint(exp11_report)
    if use_checkpoint and CHECKPOINT.is_file():
        saved = _read_json(CHECKPOINT)
        rows = saved.get("result_rows")
        if saved.get("fingerprint") == fingerprint and isinstance(rows, list):
            _validate_rows(rows)
            print("Reused valid Experiment 12 checkpoint.", flush=True)
            return rows
    rows = _run(data)
    _validate_rows(rows)
    _atomic_json(CHECKPOINT, {"fingerprint": fingerprint, "result_rows": rows})
    print("Saved valid Experiment 12 checkpoint.", flush=True)
    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise Experiment12Error("Cannot summarize an empty result selection.")
    metrics = {
        "mean_coverage": float(np.mean([row["coverage"] for row in rows])),
        "mean_prediction_set_size": float(
            np.mean([row["average_prediction_set_size"] for row in rows])
        ),
        "mean_full_set_frequency": float(np.mean([row["full_set_frequency"] for row in rows])),
        "mean_accuracy": float(np.mean([row["base_classifier_accuracy"] for row in rows])),
        "mean_log_loss": float(np.mean([row["base_classifier_log_loss"] for row in rows])),
        "mean_robustness_loss": float(np.mean([row["robustness_loss"] for row in rows])),
    }
    subject_coverage = {
        subject: float(
            np.mean([row["coverage"] for row in rows if row["test_subject"] == subject])
        )
        for subject in SUBJECTS
        if any(row["test_subject"] == subject for row in rows)
    }
    subject_phase_coverage = {
        f"{subject}/{phase}": float(
            np.mean(
                [
                    row["coverage"]
                    for row in rows
                    if row["test_subject"] == subject and row["test_phase"] == phase
                ]
            )
        )
        for subject in SUBJECTS
        for phase in PHASE_NAMES.values()
        if any(
            row["test_subject"] == subject and row["test_phase"] == phase for row in rows
        )
    }
    metrics["worst_subject_mean_coverage"] = float(min(subject_coverage.values()))
    metrics["worst_subject_phase_mean_coverage"] = float(min(subject_phase_coverage.values()))
    metrics["subject_metrics"] = {
        subject: {
            "coverage": subject_coverage[subject],
            "accuracy": float(
                np.mean(
                    [row["base_classifier_accuracy"] for row in rows if row["test_subject"] == subject]
                )
            ),
            "full_set_frequency": float(
                np.mean(
                    [row["full_set_frequency"] for row in rows if row["test_subject"] == subject]
                )
            ),
            "robustness_loss": float(
                np.mean(
                    [row["robustness_loss"] for row in rows if row["test_subject"] == subject]
                )
            ),
        }
        for subject in subject_coverage
    }
    metrics["phase_metrics"] = {
        phase: {
            "coverage": float(np.mean([row["coverage"] for row in rows if row["test_phase"] == phase])),
            "accuracy": float(
                np.mean([row["base_classifier_accuracy"] for row in rows if row["test_phase"] == phase])
            ),
            "full_set_frequency": float(
                np.mean([row["full_set_frequency"] for row in rows if row["test_phase"] == phase])
            ),
            "robustness_loss": float(
                np.mean([row["robustness_loss"] for row in rows if row["test_phase"] == phase])
            ),
        }
        for phase in PHASE_NAMES.values()
    }
    return metrics


def _aggregates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "arm_id": arm,
            "personal_calibration_count": count,
            "row_count": len(cells := [
                row for row in rows
                if row["arm_id"] == arm and row["personal_calibration_count"] == count
            ]),
            **_summary(cells),
        }
        for arm in ARMS
        for count in ALLOCATIONS
    ]


def _find(aggregates: list[dict[str, Any]], arm: str, count: int) -> dict[str, Any]:
    matches = [
        row for row in aggregates
        if row["arm_id"] == arm and row["personal_calibration_count"] == count
    ]
    if len(matches) != 1:
        raise Experiment12Error(f"Unable to resolve {arm}/k{count} aggregate.")
    return matches[0]


def _delta(after: dict[str, Any], before: dict[str, Any], field: str) -> float:
    return float(after[field] - before[field])


def _targeted(rows: list[dict[str, Any]], arm: str, count: int) -> dict[str, Any]:
    selected = [
        row for row in rows
        if row["arm_id"] == arm
        and row["personal_calibration_count"] == count
        and row["test_subject"] in ("S2", "S4")
    ]
    return _summary(selected)


def _analyze(rows: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> dict[str, Any]:
    raw_rows = [row for row in rows if row["arm_id"] == "lda_raw_all"]
    normalized_rows = [
        row for row in rows if row["arm_id"] == "lda_subject_robust_normalized_all"
    ]
    raw = _summary(raw_rows)
    normalized = _summary(normalized_rows)
    phase_accuracy_changes = {
        phase: float(
            normalized["phase_metrics"][phase]["accuracy"]
            - raw["phase_metrics"][phase]["accuracy"]
        )
        for phase in PHASE_NAMES.values()
    }
    normalization_supported = bool(
        _delta(normalized, raw, "mean_accuracy") >= 0.10
        and raw["mean_full_set_frequency"] - normalized["mean_full_set_frequency"] >= 0.05
        and normalized["mean_coverage"] >= 0.88
        and _delta(normalized, raw, "worst_subject_mean_coverage") >= -0.10
        and all(change >= 0.05 for change in phase_accuracy_changes.values())
    )

    boundaries: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        k18 = _find(aggregates, arm, 18)
        k19 = _find(aggregates, arm, 19)
        phase_full_reductions = {
            phase: float(
                k18["phase_metrics"][phase]["full_set_frequency"]
                - k19["phase_metrics"][phase]["full_set_frequency"]
            )
            for phase in PHASE_NAMES.values()
        }
        full_reduction = float(
            k18["mean_full_set_frequency"] - k19["mean_full_set_frequency"]
        )
        coverage_change = _delta(k19, k18, "mean_coverage")
        worst_change = _delta(k19, k18, "worst_subject_phase_mean_coverage")
        boundaries[arm] = {
            "supported": bool(
                full_reduction >= 0.03
                and k19["mean_coverage"] >= 0.88
                and worst_change >= -0.05
                and all(value > 0 for value in phase_full_reductions.values())
            ),
            "k18_mean_coverage": k18["mean_coverage"],
            "k19_mean_coverage": k19["mean_coverage"],
            "coverage_change": coverage_change,
            "full_set_frequency_reduction": full_reduction,
            "worst_subject_phase_coverage_change": worst_change,
            "phase_full_set_frequency_reductions": phase_full_reductions,
        }

    temperature_results: dict[str, dict[str, Any]] = {}
    for label, with_temp, without_temp in (
        ("raw", "lda_raw_all", "lda_raw_without_Temp"),
        (
            "normalized",
            "lda_subject_robust_normalized_all",
            "lda_subject_robust_normalized_without_Temp",
        ),
    ):
        overall_before = _find(aggregates, with_temp, 19)
        overall_after = _find(aggregates, without_temp, 19)
        target_before = _targeted(rows, with_temp, 19)
        target_after = _targeted(rows, without_temp, 19)
        accuracy_change = _delta(target_after, target_before, "mean_accuracy")
        robustness_reduction = float(
            target_before["mean_robustness_loss"] - target_after["mean_robustness_loss"]
        )
        overall_accuracy_change = _delta(overall_after, overall_before, "mean_accuracy")
        temperature_results[label] = {
            "supported": bool(
                accuracy_change >= 0.10
                and robustness_reduction >= 0.03
                and overall_accuracy_change >= -0.03
            ),
            "S2_S4_accuracy_change": accuracy_change,
            "S2_S4_robustness_loss_reduction": robustness_reduction,
            "S2_S4_coverage_after_removal": target_after["mean_coverage"],
            "S2_S4_full_set_frequency_change": _delta(
                target_after, target_before, "mean_full_set_frequency"
            ),
            "overall_accuracy_change": overall_accuracy_change,
        }
    raw_temp = temperature_results["raw"]
    normalized_temp = temperature_results["normalized"]
    if raw_temp["supported"] and normalized_temp["supported"]:
        temperature_decision = "INDEPENDENT_INTERFERENCE_SUPPORTED"
    elif (
        raw_temp["supported"]
        and not normalized_temp["supported"]
        and raw_temp["S2_S4_accuracy_change"]
        - normalized_temp["S2_S4_accuracy_change"] >= 0.05
    ):
        temperature_decision = "BASELINE_MEDIATED_INTERFERENCE_SUPPORTED"
    else:
        temperature_decision = "TEMP_INTERFERENCE_NOT_REPLICATED"

    raw_boundary = boundaries["lda_raw_all"]
    normalized_boundary = boundaries["lda_subject_robust_normalized_all"]
    boundary_decisions_differ = raw_boundary["supported"] != normalized_boundary["supported"]
    boundary_coverage_interaction = abs(
        raw_boundary["coverage_change"] - normalized_boundary["coverage_change"]
    )
    boundary_full_set_interaction = abs(
        raw_boundary["full_set_frequency_reduction"]
        - normalized_boundary["full_set_frequency_reduction"]
    )
    surface_supported = bool(
        normalization_supported
        and (
            boundary_decisions_differ
            or boundary_coverage_interaction >= 0.05
            or boundary_full_set_interaction >= 0.05
        )
    )

    s4_raw = raw["subject_metrics"]["S4"]
    s4_normalized = normalized["subject_metrics"]["S4"]
    s4_phase_accuracy_changes = {
        phase: float(
            np.mean(
                [
                    row["base_classifier_accuracy"]
                    for row in normalized_rows
                    if row["test_subject"] == "S4" and row["test_phase"] == phase
                ]
            )
            - np.mean(
                [
                    row["base_classifier_accuracy"]
                    for row in raw_rows
                    if row["test_subject"] == "S4" and row["test_phase"] == phase
                ]
            )
        )
        for phase in PHASE_NAMES.values()
    }
    s4_replicated = bool(
        s4_normalized["accuracy"] - s4_raw["accuracy"] >= 0.30
        and s4_raw["full_set_frequency"] - s4_normalized["full_set_frequency"] >= 0.20
        and s4_normalized["coverage"] >= 0.80
        and all(value > 0 for value in s4_phase_accuracy_changes.values())
    )
    s2_raw = raw["subject_metrics"]["S2"]
    s2_normalized = normalized["subject_metrics"]["S2"]
    s2_accuracy_change = float(s2_normalized["accuracy"] - s2_raw["accuracy"])
    s2_full_set_change = float(
        s2_normalized["full_set_frequency"] - s2_raw["full_set_frequency"]
    )
    s2_residual_failure = bool(s2_accuracy_change < 0.10 or s2_full_set_change >= 0.10)

    if surface_supported:
        primary = "READINESS_SURFACE_SUPPORTED"
    elif normalization_supported:
        primary = "NORMALIZATION_REPLICATED_WITHOUT_SURFACE_INTERACTION"
    else:
        primary = "EXPERIMENT_11_NORMALIZATION_EFFECT_NOT_REPLICATED"
    return {
        "primary_decision": primary,
        "subject_normalization": {
            "supported": normalization_supported,
            "accuracy_change": _delta(normalized, raw, "mean_accuracy"),
            "full_set_frequency_reduction": float(
                raw["mean_full_set_frequency"] - normalized["mean_full_set_frequency"]
            ),
            "coverage_change": _delta(normalized, raw, "mean_coverage"),
            "normalized_mean_coverage": normalized["mean_coverage"],
            "worst_subject_coverage_change": _delta(
                normalized, raw, "worst_subject_mean_coverage"
            ),
            "phase_accuracy_changes": phase_accuracy_changes,
        },
        "order_statistic_boundaries": boundaries,
        "temperature_interference": {
            "decision": temperature_decision,
            "raw": raw_temp,
            "normalized": normalized_temp,
        },
        "readiness_surface": {
            "supported": surface_supported,
            "boundary_decisions_differ": boundary_decisions_differ,
            "coverage_change_interaction_magnitude": boundary_coverage_interaction,
            "full_set_reduction_interaction_magnitude": boundary_full_set_interaction,
        },
        "predeclared_subject_checks": {
            "S4_replication_supported": s4_replicated,
            "S4_accuracy_change": float(s4_normalized["accuracy"] - s4_raw["accuracy"]),
            "S4_full_set_frequency_reduction": float(
                s4_raw["full_set_frequency"] - s4_normalized["full_set_frequency"]
            ),
            "S4_normalized_coverage": s4_normalized["coverage"],
            "S4_phase_accuracy_changes": s4_phase_accuracy_changes,
            "S2_residual_failure_replicated": s2_residual_failure,
            "S2_accuracy_change": s2_accuracy_change,
            "S2_full_set_frequency_change": s2_full_set_change,
            "S2_normalized_coverage": s2_normalized["coverage"],
        },
    }


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment12Error("Experiment name mismatch.")
    _validate_rows(report.get("result_rows", []))
    aggregates = report.get("aggregate_results", [])
    if len(aggregates) != len(ARMS) * len(ALLOCATIONS):
        raise Experiment12Error("Aggregate grid is incomplete.")
    if report.get("analysis", {}).get("primary_decision") not in {
        "READINESS_SURFACE_SUPPORTED",
        "NORMALIZATION_REPLICATED_WITHOUT_SURFACE_INTERACTION",
        "EXPERIMENT_11_NORMALIZATION_EFFECT_NOT_REPLICATED",
    }:
        raise Experiment12Error("Unknown primary decision.")
    safety = report.get("validation", {})
    if safety.get("model_call_used") is not False or safety.get("raw_wesad_pickles_loaded") is not False:
        raise Experiment12Error("Experiment 12 safety contract failed.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, exp11_report, data = _load_prerequisites()
    rows = _load_or_run(data, exp11_report, use_checkpoint)
    aggregates = _aggregates(rows)
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": protocol["research_question"],
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "prerequisites": {
            "experiment_11_report_path": str(EXP11_REPORT.resolve()),
            "experiment_11_report_sha256": _sha256(EXP11_REPORT),
            "experiment_11_validation_path": str(EXP11_VALIDATION.resolve()),
            "experiment_11_validation_sha256": _sha256(EXP11_VALIDATION),
            "feature_checkpoint_hashes": exp11_report["prerequisites"]["feature_checkpoint_hashes"],
        },
        "design_counts": {
            "subjects": len(SUBJECTS),
            "temporal_holdouts": list(PHASE_NAMES.values()),
            "calibration_draws_per_subject_phase": REPETITIONS,
            "arms": list(ARMS),
            "personal_calibration_counts": list(ALLOCATIONS),
            "result_rows": len(rows),
            "aggregate_rows": len(aggregates),
        },
        "result_rows": rows,
        "aggregate_results": aggregates,
        "analysis": _analyze(rows, aggregates),
        "limitations": protocol["guardrails"],
        "validation": {
            "protocol_frozen_before_outcome_analysis": True,
            "experiment_11_validation_reused": True,
            "temporal_test_calibration_overlap": False,
            "temporal_test_normalization_overlap": False,
            "heldout_subject_training_leakage": False,
            "raw_wesad_pickles_loaded": False,
            "raw_dataset_mutated": False,
            "dependency_installation_used": False,
            "classifier_hyperparameter_search_used": False,
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
        "## Representation × calibration grid",
        "",
        "| Arm | k | Accuracy | Coverage | Worst subject | Worst subject-phase | Full sets | Robustness loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["aggregate_results"]:
        lines.append(
            f"| {row['arm_id']} | {row['personal_calibration_count']} | "
            f"{row['mean_accuracy']:.4f} | {row['mean_coverage']:.4f} | "
            f"{row['worst_subject_mean_coverage']:.4f} | "
            f"{row['worst_subject_phase_mean_coverage']:.4f} | "
            f"{row['mean_full_set_frequency']:.4f} | {row['mean_robustness_loss']:.4f} |"
        )
    normalization = analysis["subject_normalization"]
    lines.extend(
        [
            "",
            "## Subject normalization",
            "",
            f"- Supported: **{normalization['supported']}**",
            f"- Accuracy change: {normalization['accuracy_change']:.4f}",
            f"- Full-set-frequency reduction: {normalization['full_set_frequency_reduction']:.4f}",
            f"- Coverage change: {normalization['coverage_change']:.4f}",
            f"- Normalized mean coverage: {normalization['normalized_mean_coverage']:.4f}",
            f"- Worst-subject coverage change: {normalization['worst_subject_coverage_change']:.4f}",
            f"- Phase accuracy changes: {normalization['phase_accuracy_changes']}",
            "",
            "## Order-statistic boundary",
            "",
            "| Arm | Safe | Coverage Δ | Full-set reduction | Worst subject-phase coverage Δ |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for arm, row in analysis["order_statistic_boundaries"].items():
        lines.append(
            f"| {arm} | {row['supported']} | {row['coverage_change']:.4f} | "
            f"{row['full_set_frequency_reduction']:.4f} | "
            f"{row['worst_subject_phase_coverage_change']:.4f} |"
        )
    temperature = analysis["temperature_interference"]
    surface = analysis["readiness_surface"]
    targets = analysis["predeclared_subject_checks"]
    lines.extend(
        [
            "",
            "## Rival distinction",
            "",
            f"- Temperature decision: **{temperature['decision']}**",
            f"- Raw temperature-removal rule passed: {temperature['raw']['supported']}",
            f"- Normalized temperature-removal rule passed: {temperature['normalized']['supported']}",
            f"- Readiness surface supported: **{surface['supported']}**",
            f"- Boundary coverage interaction magnitude: {surface['coverage_change_interaction_magnitude']:.4f}",
            f"- Boundary full-set interaction magnitude: {surface['full_set_reduction_interaction_magnitude']:.4f}",
            "",
            "## Predeclared subject checks",
            "",
            f"- S4 normalization replication: **{targets['S4_replication_supported']}**",
            f"- S4 accuracy change: {targets['S4_accuracy_change']:.4f}",
            f"- S4 full-set reduction: {targets['S4_full_set_frequency_reduction']:.4f}",
            f"- S2 residual failure replicated: **{targets['S2_residual_failure_replicated']}**",
            f"- S2 accuracy change: {targets['S2_accuracy_change']:.4f}",
            f"- S2 full-set change: {targets['S2_full_set_frequency_change']:.4f}",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
            "## Reproducibility",
            "",
            f"- Result rows: {len(report['result_rows'])}",
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
        "experiment_11_report_sha256": report["prerequisites"]["experiment_11_report_sha256"],
        "experiment_11_validation_sha256": report["prerequisites"]["experiment_11_validation_sha256"],
        "feature_checkpoint_hashes": report["prerequisites"]["feature_checkpoint_hashes"],
        "result_row_count": len(report["result_rows"]),
        "aggregate_row_count": len(report["aggregate_results"]),
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
            f"- Experiment 11 report SHA-256: `{summary['experiment_11_report_sha256']}`",
            f"- Experiment 11 validation SHA-256: `{summary['experiment_11_validation_sha256']}`",
            f"- Result rows: {summary['result_row_count']}",
            f"- Aggregate rows: {summary['aggregate_row_count']}",
            "- Dependency installation: no",
            "- API/model call: no",
            "- Raw WESAD pickle loading: no",
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
    print(f"Experiment 12 complete: {report['analysis']['primary_decision']}", flush=True)
    print(f"Result rows: {len(report['result_rows'])}", flush=True)


if __name__ == "__main__":
    main()
