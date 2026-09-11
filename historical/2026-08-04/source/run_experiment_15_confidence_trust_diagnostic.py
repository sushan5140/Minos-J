"""Run the frozen Meno-J Experiment 15 confidence–trust diagnostic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import run_experiment_13_external_replication as exp13
import run_experiment_14_class_conditional_repair as exp14
from pipeline import _conformal_quantile


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_15_preregistered_protocol.json"
LITERATURE_JSON = OUTPUT_DIR / "meno_j_literature_review_after_experiment_14.json"
EXP14_REPORT = OUTPUT_DIR / "meno_j_experiment_14_class_conditional_repair.json"
EXP14_VALIDATION = OUTPUT_DIR / "meno_j_experiment_14_validation.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_15_confidence_trust_diagnostic.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_15_confidence_trust_diagnostic.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_15_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_15_reproducibility_summary.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_15_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_15_working_theory_update.md"
CHECKPOINT = PROJECT_DIR / "work" / "experiment_15_checkpoints" / "diagnostic_rows.json"

EXPERIMENT_NAME = "Meno-J Experiment 15: Confidence–Trust Subject-Shift Diagnostic"
ARMS = ("raw_marginal", "normalized_class_mondrian")
PRIMARY_ARM = "normalized_class_mondrian"
ALPHA = 0.10
KNN_K = 10
DENSITY_TRIM = 0.10
EPSILON = 1e-12


class Experiment15Error(RuntimeError):
    """Raised when the frozen Experiment 15 contract is violated."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Experiment15Error(f"Expected JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_prerequisites() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol = _read_json(PROTOCOL_PATH)
    if protocol.get("protocol_status") != (
        "FROZEN_AFTER_LITERATURE_REVIEW_BEFORE_EXPERIMENT_15_OUTCOME_COMPUTATION"
    ):
        raise Experiment15Error("Experiment 15 protocol is not frozen.")
    literature = _read_json(LITERATURE_JSON)
    if literature.get("next_experiment", {}).get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment15Error("Literature review does not select Experiment 15.")
    report = exp14.validate_report(_read_json(EXP14_REPORT))
    validation = _read_json(EXP14_VALIDATION)
    if validation.get("status") != "PASS":
        raise Experiment15Error("Experiment 14 validation is not PASS.")
    if validation.get("scientific_report_sha256") != _sha256(EXP14_REPORT):
        raise Experiment15Error("Experiment 14 report changed after validation.")
    if report["design"]["subject_count"] != 33 or len(report["fold_results"]) != 396:
        raise Experiment15Error("Experiment 14 design prerequisite changed.")
    return protocol, literature, report, validation


def _load_features(exp14_report: dict[str, Any]) -> dict[str, dict[str, np.ndarray]]:
    expected_hashes = exp14_report["prerequisites"]["feature_checkpoint_hashes"]
    data: dict[str, dict[str, np.ndarray]] = {}
    for subject in exp14_report["design"]["subjects"]:
        path = exp13.FEATURE_DIR / f"{subject}.npz"
        if not path.is_file() or _sha256(path) != expected_hashes[subject]:
            raise Experiment15Error(f"Feature checkpoint failed hash validation: {subject}")
        with np.load(path, allow_pickle=False) as saved:
            features = saved["features"].astype(np.float64)
            labels = saved["labels"].astype(np.int32)
        if features.shape != (32, 54) or not np.array_equal(
            np.bincount(labels, minlength=2), np.asarray([16, 16])
        ):
            raise Experiment15Error(f"Feature checkpoint contract changed: {subject}")
        data[subject] = {"features": features, "labels": labels}
    return data


def _standardize(model: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    return (features - model["mean"]) / model["scale"]


def _retained_class_manifolds(
    model: dict[str, np.ndarray], train_x: np.ndarray, train_y: np.ndarray
) -> dict[int, np.ndarray]:
    standardized = _standardize(model, train_x)
    retained: dict[int, np.ndarray] = {}
    for label in exp13.LABEL_NAMES:
        points = standardized[train_y == label]
        if len(points) <= KNN_K:
            raise Experiment15Error("Insufficient training points for frozen trust-score k.")
        squared_norm = np.sum(points * points, axis=1)
        squared = squared_norm[:, None] + squared_norm[None, :] - 2.0 * (points @ points.T)
        distances = np.sqrt(np.maximum(squared, 0.0))
        np.fill_diagonal(distances, np.inf)
        radii = np.partition(distances, KNN_K - 1, axis=1)[:, KNN_K - 1]
        cutoff = float(np.quantile(radii, 1.0 - DENSITY_TRIM))
        kept = points[radii <= cutoff]
        if len(kept) < 100:
            raise Experiment15Error("Density filtering retained too few class-manifold points.")
        retained[label] = kept
    return retained


def _nearest_distances(queries: np.ndarray, points: np.ndarray) -> np.ndarray:
    query_norm = np.sum(queries * queries, axis=1)
    point_norm = np.sum(points * points, axis=1)
    squared = query_norm[:, None] + point_norm[None, :] - 2.0 * (queries @ points.T)
    return np.sqrt(np.maximum(np.min(squared, axis=1), 0.0))


def _trust_scores(
    model: dict[str, np.ndarray], manifolds: dict[int, np.ndarray], features: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    probabilities = exp13._predict(model, features)
    predicted = np.argmax(probabilities, axis=1).astype(np.int32)
    queries = _standardize(model, features)
    distances = {
        label: _nearest_distances(queries, manifolds[label]) for label in exp13.LABEL_NAMES
    }
    predicted_distance = np.where(predicted == 0, distances[0], distances[1])
    rival_distance = np.where(predicted == 0, distances[1], distances[0])
    trust = rival_distance / np.maximum(predicted_distance, EPSILON)
    confidence = np.max(probabilities, axis=1)
    if not np.all(np.isfinite(trust)) or not np.all(np.isfinite(confidence)):
        raise Experiment15Error("Non-finite confidence or trust score.")
    return probabilities, confidence, trust


def _prediction_sets(
    arm: str,
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    if arm == "raw_marginal":
        scores = 1.0 - calibration_probabilities[
            np.arange(len(calibration_labels)), calibration_labels
        ]
        threshold = float(_conformal_quantile(scores, ALPHA))
        return (1.0 - test_probabilities) <= threshold, {"pooled": threshold}
    if arm != "normalized_class_mondrian":
        raise Experiment15Error(f"Unknown arm: {arm}")
    prediction_sets = np.zeros_like(test_probabilities, dtype=bool)
    thresholds: dict[str, float] = {}
    for label, name in exp13.LABEL_NAMES.items():
        mask = calibration_labels == label
        scores = 1.0 - calibration_probabilities[mask, label]
        threshold = float(_conformal_quantile(scores, ALPHA))
        prediction_sets[:, label] = (1.0 - test_probabilities[:, label]) <= threshold
        thresholds[name] = threshold
    return prediction_sets, thresholds


def _quadrant(high_confidence: bool, low_trust: bool) -> str:
    if high_confidence and low_trust:
        return "high_confidence_low_trust"
    if high_confidence:
        return "high_confidence_high_trust"
    if low_trust:
        return "low_confidence_low_trust"
    return "low_confidence_high_trust"


def _run_diagnostic(
    data: dict[str, dict[str, np.ndarray]], subjects: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fold_rows: list[dict[str, Any]] = []
    observation_rows: list[dict[str, Any]] = []
    for test_index, test_subject in enumerate(subjects):
        for repetition in range(exp13.REPETITIONS):
            training_subjects, calibration_subjects = exp13._fold_subjects(
                subjects, test_index, repetition
            )
            onboarding_indices, test_indices = exp13._heldout_partition(
                data[test_subject]["labels"], test_index, repetition
            )
            for arm in ARMS:
                normalized = arm == "normalized_class_mondrian"
                train_x = np.concatenate(
                    [
                        exp13._normalized_subject(data[subject]["features"])
                        if normalized
                        else data[subject]["features"]
                        for subject in training_subjects
                    ]
                )
                train_y = np.concatenate(
                    [data[subject]["labels"] for subject in training_subjects]
                )
                calibration_x = np.concatenate(
                    [
                        exp13._normalized_subject(data[subject]["features"])
                        if normalized
                        else data[subject]["features"]
                        for subject in calibration_subjects
                    ]
                )
                calibration_y = np.concatenate(
                    [data[subject]["labels"] for subject in calibration_subjects]
                )
                heldout = data[test_subject]["features"]
                if normalized:
                    heldout = exp13._normalized_subject(
                        heldout, reference=heldout[onboarding_indices]
                    )
                test_x = heldout[test_indices]
                test_y = data[test_subject]["labels"][test_indices]
                model = exp13._fit_binary_lda(train_x, train_y)
                manifolds = _retained_class_manifolds(model, train_x, train_y)
                calibration_probabilities, calibration_confidence, calibration_trust = (
                    _trust_scores(model, manifolds, calibration_x)
                )
                test_probabilities, test_confidence, test_trust = _trust_scores(
                    model, manifolds, test_x
                )
                confidence_threshold = float(np.median(calibration_confidence))
                trust_threshold = float(np.median(calibration_trust))
                prediction_sets, conformal_thresholds = _prediction_sets(
                    arm,
                    calibration_probabilities,
                    calibration_y,
                    test_probabilities,
                )
                covered = prediction_sets[np.arange(len(test_y)), test_y]
                sizes = prediction_sets.sum(axis=1)
                predicted = np.argmax(test_probabilities, axis=1)
                quadrants: list[str] = []
                for local_index in range(len(test_y)):
                    high_confidence = bool(test_confidence[local_index] >= confidence_threshold)
                    low_trust = bool(test_trust[local_index] <= trust_threshold)
                    quadrant = _quadrant(high_confidence, low_trust)
                    quadrants.append(quadrant)
                    observation_rows.append(
                        {
                            "test_subject": test_subject,
                            "protocol_version": "V1" if test_subject.startswith("S") else "V2",
                            "repetition": repetition,
                            "arm_id": arm,
                            "test_index": int(test_indices[local_index]),
                            "confidence": float(test_confidence[local_index]),
                            "trust_score": float(test_trust[local_index]),
                            "confidence_threshold": confidence_threshold,
                            "trust_threshold": trust_threshold,
                            "high_confidence": high_confidence,
                            "low_trust": low_trust,
                            "risk_quadrant": quadrant,
                            "covered": bool(covered[local_index]),
                            "prediction_set_size": int(sizes[local_index]),
                            "predicted_label": exp13.LABEL_NAMES[int(predicted[local_index])],
                            "true_label": exp13.LABEL_NAMES[int(test_y[local_index])],
                        }
                    )
                fold_rows.append(
                    {
                        "test_subject": test_subject,
                        "protocol_version": "V1" if test_subject.startswith("S") else "V2",
                        "repetition": repetition,
                        "arm_id": arm,
                        "training_subjects": training_subjects,
                        "external_calibration_subjects": calibration_subjects,
                        "onboarding_indices": onboarding_indices.tolist(),
                        "test_indices": test_indices.tolist(),
                        "onboarding_labels_used": False,
                        "confidence_threshold": confidence_threshold,
                        "trust_threshold": trust_threshold,
                        "retained_manifold_counts": {
                            exp13.LABEL_NAMES[label]: int(len(manifolds[label]))
                            for label in exp13.LABEL_NAMES
                        },
                        "conformal_thresholds": conformal_thresholds,
                        "coverage": float(np.mean(covered)),
                        "average_prediction_set_size": float(np.mean(sizes)),
                        "full_set_frequency": float(np.mean(sizes == 2)),
                        "empty_set_frequency": float(np.mean(sizes == 0)),
                        "base_classifier_accuracy": float(np.mean(predicted == test_y)),
                        "quadrant_counts": {
                            name: int(quadrants.count(name))
                            for name in (
                                "high_confidence_low_trust",
                                "high_confidence_high_trust",
                                "low_confidence_low_trust",
                                "low_confidence_high_trust",
                            )
                        },
                    }
                )
    return fold_rows, observation_rows


def _validate_rows(
    fold_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
    subjects: list[str],
) -> None:
    if len(fold_rows) != 198 or len(observation_rows) != 3168:
        raise Experiment15Error("Experiment 15 result grid is incomplete.")
    fold_keys = {
        (row["test_subject"], row["repetition"], row["arm_id"]) for row in fold_rows
    }
    if len(fold_keys) != 198:
        raise Experiment15Error("Experiment 15 fold keys are duplicated or incomplete.")
    observation_keys = {
        (row["test_subject"], row["repetition"], row["arm_id"], row["test_index"])
        for row in observation_rows
    }
    if len(observation_keys) != 3168:
        raise Experiment15Error("Experiment 15 observation keys are duplicated or incomplete.")
    subject_set = set(subjects)
    for row in fold_rows:
        if row["arm_id"] not in ARMS:
            raise Experiment15Error("Unknown arm in fold results.")
        training = set(row["training_subjects"])
        calibration = set(row["external_calibration_subjects"])
        test_subject = row["test_subject"]
        if test_subject in training or test_subject in calibration or training & calibration:
            raise Experiment15Error("Subject leakage detected.")
        if training | calibration | {test_subject} != subject_set:
            raise Experiment15Error("Subject fold partition is incomplete.")
        if set(row["onboarding_indices"]) & set(row["test_indices"]):
            raise Experiment15Error("Onboarding/test leakage detected.")
        if row["onboarding_labels_used"] is not False:
            raise Experiment15Error("Onboarding labels were used.")
        if sum(row["quadrant_counts"].values()) != 16:
            raise Experiment15Error("Fold quadrant counts do not sum to 16.")
    valid_quadrants = {
        "high_confidence_low_trust",
        "high_confidence_high_trust",
        "low_confidence_low_trust",
        "low_confidence_high_trust",
    }
    for row in observation_rows:
        if row["risk_quadrant"] not in valid_quadrants:
            raise Experiment15Error("Unknown risk quadrant.")
        if row["high_confidence"] != (row["confidence"] >= row["confidence_threshold"]):
            raise Experiment15Error("High-confidence flag mismatch.")
        if row["low_trust"] != (row["trust_score"] <= row["trust_threshold"]):
            raise Experiment15Error("Low-trust flag mismatch.")


def _fingerprint(exp14_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "literature_review_sha256": _sha256(LITERATURE_JSON),
        "experiment_14_report_sha256": _sha256(EXP14_REPORT),
        "experiment_14_validation_sha256": _sha256(EXP14_VALIDATION),
        "feature_checkpoint_hashes": exp14_report["prerequisites"][
            "feature_checkpoint_hashes"
        ],
    }


def _load_or_run(
    data: dict[str, dict[str, np.ndarray]],
    subjects: list[str],
    exp14_report: dict[str, Any],
    use_checkpoint: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fingerprint = _fingerprint(exp14_report)
    if use_checkpoint and CHECKPOINT.is_file():
        saved = _read_json(CHECKPOINT)
        folds = saved.get("fold_results")
        observations = saved.get("observation_results")
        if (
            saved.get("fingerprint") == fingerprint
            and isinstance(folds, list)
            and isinstance(observations, list)
        ):
            _validate_rows(folds, observations, subjects)
            print("Reused valid Experiment 15 checkpoint.", flush=True)
            return folds, observations
    folds, observations = _run_diagnostic(data, subjects)
    _validate_rows(folds, observations, subjects)
    _atomic_json(
        CHECKPOINT,
        {
            "fingerprint": fingerprint,
            "fold_results": folds,
            "observation_results": observations,
        },
    )
    print("Saved valid Experiment 15 checkpoint.", flush=True)
    return folds, observations


def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"count": 0, "coverage": None, "miscoverage": None, "mean_confidence": None, "mean_trust": None}
    coverage = float(np.mean([row["covered"] for row in rows]))
    return {
        "count": len(rows),
        "coverage": coverage,
        "miscoverage": float(1.0 - coverage),
        "mean_confidence": float(np.mean([row["confidence"] for row in rows])),
        "mean_trust": float(np.mean([row["trust_score"] for row in rows])),
    }


def _risk_gap(rows: list[dict[str, Any]], comparator: str) -> float:
    risk = [row for row in rows if row["risk_quadrant"] == "high_confidence_low_trust"]
    if comparator == "all_other":
        other = [row for row in rows if row["risk_quadrant"] != "high_confidence_low_trust"]
    else:
        other = [row for row in rows if row["risk_quadrant"] == comparator]
    if not risk or not other:
        raise Experiment15Error("A required risk comparison group is empty.")
    return float(
        (1.0 - np.mean([row["covered"] for row in risk]))
        - (1.0 - np.mean([row["covered"] for row in other]))
    )


def _arm_analysis(rows: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    quadrants = {
        name: _group_summary([row for row in rows if row["risk_quadrant"] == name])
        for name in (
            "high_confidence_low_trust",
            "high_confidence_high_trust",
            "low_confidence_low_trust",
            "low_confidence_high_trust",
        )
    }
    covered = [row for row in rows if row["covered"]]
    miscovered = [row for row in rows if not row["covered"]]
    return {
        "observation_count": len(rows),
        "overall_coverage": float(np.mean([row["covered"] for row in rows])),
        "quadrant_summaries": quadrants,
        "high_risk_miscoverage_minus_all_other": _risk_gap(rows, "all_other"),
        "high_risk_miscoverage_minus_high_confidence_high_trust": _risk_gap(
            rows, "high_confidence_high_trust"
        ),
        "protocol_version_gaps_vs_all_other": {
            version: _risk_gap(
                [row for row in rows if row["protocol_version"] == version], "all_other"
            )
            for version in ("V1", "V2")
        },
        "repetition_gaps_vs_all_other": {
            str(repetition): _risk_gap(
                [row for row in rows if row["repetition"] == repetition], "all_other"
            )
            for repetition in range(exp13.REPETITIONS)
        },
        "covered_vs_miscovered_diagnostics": {
            "covered": _group_summary(covered),
            "miscovered": _group_summary(miscovered),
        },
        "subject_summaries": {
            subject: {
                "observation_count": len(subject_rows := [row for row in rows if row["test_subject"] == subject]),
                "coverage": float(np.mean([row["covered"] for row in subject_rows])),
                "high_risk_fraction": float(
                    np.mean(
                        [row["risk_quadrant"] == "high_confidence_low_trust" for row in subject_rows]
                    )
                ),
            }
            for subject in subjects
        },
    }


def _analyze(observations: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    arms = {
        arm: _arm_analysis([row for row in observations if row["arm_id"] == arm], subjects)
        for arm in ARMS
    }
    primary = arms[PRIMARY_ARM]
    high_risk = primary["quadrant_summaries"]["high_confidence_low_trust"]
    checks = {
        "primary_high_risk_observation_count_at_least_100": high_risk["count"] >= 100,
        "primary_high_risk_miscoverage_minus_all_other_at_least_0_10": primary[
            "high_risk_miscoverage_minus_all_other"
        ]
        >= 0.10,
        "primary_high_risk_miscoverage_minus_high_confidence_high_trust_at_least_0_10": primary[
            "high_risk_miscoverage_minus_high_confidence_high_trust"
        ]
        >= 0.10,
        "primary_high_risk_coverage_below_0_85": high_risk["coverage"] < 0.85,
        "gap_vs_all_other_positive_in_both_protocol_versions": all(
            value > 0 for value in primary["protocol_version_gaps_vs_all_other"].values()
        ),
        "gap_vs_all_other_positive_in_all_three_repetitions": all(
            value > 0 for value in primary["repetition_gaps_vs_all_other"].values()
        ),
    }
    decision = (
        "CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_SUPPORTED"
        if all(checks.values())
        else "CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_NOT_SUPPORTED"
    )
    return {
        "primary_decision": decision,
        "all_preregistered_checks_pass": all(checks.values()),
        "preregistered_checks": checks,
        "arm_analyses": arms,
    }


def _verify_experiment_14_continuity(
    fold_rows: list[dict[str, Any]], exp14_report: dict[str, Any]
) -> None:
    current = {
        (row["test_subject"], row["repetition"], row["arm_id"]): row for row in fold_rows
    }
    previous = {
        (row["test_subject"], row["repetition"], row["arm_id"]): row
        for row in exp14_report["fold_results"]
        if row["arm_id"] in ARMS
    }
    for key, old in previous.items():
        new = current[key]
        for metric in (
            "coverage",
            "average_prediction_set_size",
            "full_set_frequency",
            "empty_set_frequency",
            "base_classifier_accuracy",
        ):
            if new[metric] != old[metric]:
                raise Experiment15Error(f"Experiment 14 continuity failed: {key} {metric}")


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment15Error("Experiment name mismatch.")
    _validate_rows(
        report.get("fold_results", []),
        report.get("observation_results", []),
        report.get("design", {}).get("subjects", []),
    )
    if report.get("analysis", {}).get("primary_decision") not in {
        "CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_SUPPORTED",
        "CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_NOT_SUPPORTED",
    }:
        raise Experiment15Error("Unknown primary decision.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, literature, exp14_report, exp14_validation = _load_prerequisites()
    data = _load_features(exp14_report)
    subjects = exp14_report["design"]["subjects"]
    folds, observations = _load_or_run(
        data, subjects, exp14_report, use_checkpoint=use_checkpoint
    )
    _verify_experiment_14_continuity(folds, exp14_report)
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": protocol["research_question"],
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "literature_review": {
            "path": str(LITERATURE_JSON.resolve()),
            "sha256": _sha256(LITERATURE_JSON),
            "full_text_reviewed_count": literature["method"]["full_text_reviewed_count"],
        },
        "prerequisites": {
            "experiment_14_report_sha256": _sha256(EXP14_REPORT),
            "experiment_14_validation_sha256": _sha256(EXP14_VALIDATION),
            "experiment_14_validation_status": exp14_validation["status"],
            "feature_checkpoint_hashes": exp14_report["prerequisites"][
                "feature_checkpoint_hashes"
            ],
        },
        "design": {
            "subjects": subjects,
            "subject_count": len(subjects),
            "repetitions_per_subject": exp13.REPETITIONS,
            "arms": list(ARMS),
            "primary_arm": PRIMARY_ARM,
            "expected_fold_rows": 198,
            "expected_observation_rows": 3168,
            "trust_score_knn_k": KNN_K,
            "density_trim_fraction": DENSITY_TRIM,
        },
        "fold_results": folds,
        "observation_results": observations,
        "analysis": _analyze(observations, subjects),
        "guardrails": protocol["guardrails"],
        "validation": {
            "protocol_frozen_before_outcome_computation": True,
            "experiment_14_continuity_exact": True,
            "subject_disjoint_folds": True,
            "onboarding_test_disjoint": True,
            "onboarding_labels_used": False,
            "risk_thresholds_use_calibration_labels": False,
            "test_labels_used_for_diagnostic_construction": False,
            "diagnostic_only_not_a_repair": True,
            "model_call_used": False,
            "api_key_required": False,
            "raw_dataset_mutated": False,
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
        "This experiment is a diagnostic, not a repair or deployment gate.",
        "",
        "## Frozen primary checks",
        "",
        *[f"- {name}: **{passed}**" for name, passed in analysis["preregistered_checks"].items()],
        "",
        "## Arm results",
        "",
        "| Arm | Overall coverage | High-conf/low-trust n | High-conf/low-trust coverage | Miscoverage gap vs rest | Gap vs high-conf/high-trust |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        value = analysis["arm_analyses"][arm]
        risk = value["quadrant_summaries"]["high_confidence_low_trust"]
        lines.append(
            f"| {arm} | {value['overall_coverage']:.4f} | {risk['count']} | "
            f"{risk['coverage']:.4f} | {value['high_risk_miscoverage_minus_all_other']:.4f} | "
            f"{value['high_risk_miscoverage_minus_high_confidence_high_trust']:.4f} |"
        )
    primary = analysis["arm_analyses"][PRIMARY_ARM]
    lines.extend(
        [
            "",
            "## Primary-arm stability",
            "",
            f"- Protocol-version gaps versus all other quadrants: {primary['protocol_version_gaps_vs_all_other']}",
            f"- Repetition gaps versus all other quadrants: {primary['repetition_gaps_vs_all_other']}",
            f"- Covered versus miscovered diagnostics: {primary['covered_vs_miscovered_diagnostics']}",
            "",
            "## Interpretation boundary",
            "",
            "- A positive result supports a specific classifier-manifold mismatch proxy; it does not prove causality or individual coverage.",
            "- A negative result blocks a confidence–trust gate and redirects the falsification engine to protocol/stressor posterior shift or temporal dependence.",
            "- No thresholds were tuned on heldout outcomes.",
            "",
            "## Integrity",
            "",
            f"- Fold rows: {len(report['fold_results'])}",
            f"- Observation rows: {len(report['observation_results'])}",
            "- Exact Experiment 14 outcome continuity: PASS",
            "- API/model call: no",
            "- Independent exact replay: pending",
            "",
        ]
    )
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic NumPy replay from validated Experiment 13 feature checkpoints and Experiment 14 folds",
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "literature_review_sha256": report["literature_review"]["sha256"],
        "experiment_14_report_sha256": report["prerequisites"]["experiment_14_report_sha256"],
        "experiment_14_validation_sha256": report["prerequisites"]["experiment_14_validation_sha256"],
        "feature_checkpoint_hashes": report["prerequisites"]["feature_checkpoint_hashes"],
        "fold_result_count": len(report["fold_results"]),
        "observation_result_count": len(report["observation_results"]),
        "model_call_used": False,
        "api_key_required": False,
        "raw_dataset_mutated": False,
        "validation_status": "PENDING_INDEPENDENT_EXACT_REPLAY",
    }


def render_reproducibility_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {EXPERIMENT_NAME} — Reproducibility Summary",
            "",
            f"- Execution mode: {summary['execution_mode']}",
            f"- Protocol SHA-256: `{summary['protocol_sha256']}`",
            f"- Literature-review SHA-256: `{summary['literature_review_sha256']}`",
            f"- Experiment 14 report SHA-256: `{summary['experiment_14_report_sha256']}`",
            f"- Experiment 14 validation SHA-256: `{summary['experiment_14_validation_sha256']}`",
            f"- Feature checkpoints: {len(summary['feature_checkpoint_hashes'])}",
            f"- Fold results: {summary['fold_result_count']}",
            f"- Observation results: {summary['observation_result_count']}",
            "- API/model call: no",
            "- Raw-data mutation: no",
            "- Independent exact replay: pending",
            "",
        ]
    )


def _theory_update(report: dict[str, Any]) -> dict[str, Any]:
    analysis = report["analysis"]
    primary = analysis["arm_analyses"][PRIMARY_ARM]
    risk = primary["quadrant_summaries"]["high_confidence_low_trust"]
    supported = analysis["all_preregistered_checks_pass"]
    return {
        "experiment_name": EXPERIMENT_NAME,
        "update_status": "PENDING_INDEPENDENT_VALIDATION",
        "primary_decision": analysis["primary_decision"],
        "evidence": {
            "primary_overall_coverage": primary["overall_coverage"],
            "high_risk_count": risk["count"],
            "high_risk_coverage": risk["coverage"],
            "miscoverage_gap_vs_all_other": primary[
                "high_risk_miscoverage_minus_all_other"
            ],
            "miscoverage_gap_vs_high_confidence_high_trust": primary[
                "high_risk_miscoverage_minus_high_confidence_high_trust"
            ],
        },
        "working_theory": (
            "Residual undercoverage after normalization and class conditioning is concentrated in confidently predicted windows that are geometrically closer to the rival training-class manifold."
            if supported
            else "The frozen confidence–trust proxy does not explain the residual subject-level undercoverage strongly or stably enough."
        ),
        "next_action": (
            "Preregister a separately validated score-rectification or safe-abstention experiment using confidence and trust; do not tune on Experiment 15 outcomes."
            if supported
            else "Do not build a confidence–trust gate. Test protocol/stressor posterior shift and temporal dependence as the next rivals."
        ),
        "claim_boundary": "This is an empirical mechanism diagnostic, not a causal proof or individual conditional-coverage guarantee.",
        "validation": "PENDING_INDEPENDENT_EXACT_REPLAY",
    }


def render_theory_markdown(theory: dict[str, Any]) -> str:
    evidence = theory["evidence"]
    return "\n".join(
        [
            "# Meno-J Experiment 15 — Working-Theory Update",
            "",
            f"**{theory['primary_decision']}**",
            "",
            theory["working_theory"],
            "",
            f"- Primary overall coverage: {evidence['primary_overall_coverage']:.4f}",
            f"- High-confidence/low-trust count: {evidence['high_risk_count']}",
            f"- High-confidence/low-trust coverage: {evidence['high_risk_coverage']:.4f}",
            f"- Miscoverage gap versus all other quadrants: {evidence['miscoverage_gap_vs_all_other']:.4f}",
            f"- Miscoverage gap versus high-confidence/high-trust: {evidence['miscoverage_gap_vs_high_confidence_high_trust']:.4f}",
            "",
            f"Next action: {theory['next_action']}",
            "",
            f"Boundary: {theory['claim_boundary']}",
            "",
            "Independent exact replay: **pending**.",
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
    theory = _theory_update(report)
    _atomic_json(THEORY_JSON, theory)
    THEORY_MD.write_text(render_theory_markdown(theory), encoding="utf-8")
    print(f"Experiment 15 complete: {report['analysis']['primary_decision']}", flush=True)
    print(f"Fold rows: {len(report['fold_results'])}", flush=True)
    print(f"Observation rows: {len(report['observation_results'])}", flush=True)


if __name__ == "__main__":
    main()
