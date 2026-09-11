"""Run Meno-J Experiment 14 with frozen class-conditional calibration rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

import run_experiment_13_external_replication as exp13
from pipeline import _conformal_quantile


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
PROTOCOL_PATH = OUTPUT_DIR / "meno_j_experiment_14_preregistered_protocol.json"
EXP13_REPORT = OUTPUT_DIR / "meno_j_experiment_13_external_replication.json"
EXP13_VALIDATION = OUTPUT_DIR / "meno_j_experiment_13_validation.json"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_14_class_conditional_repair.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_14_class_conditional_repair.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_14_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_14_reproducibility_summary.md"
CHECKPOINT = PROJECT_DIR / "work" / "experiment_14_checkpoints" / "fold_results.json"

EXPERIMENT_NAME = "Meno-J Experiment 14: Class-Conditional Calibration Repair"
ARMS = (
    "raw_marginal",
    "normalized_marginal",
    "raw_class_mondrian",
    "normalized_class_mondrian",
)
ALPHA = 0.10
TARGET = 0.90


class Experiment14Error(RuntimeError):
    """Raised when the frozen Experiment 14 contract is violated."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Experiment14Error(f"Expected JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_prerequisites() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol = _read_json(PROTOCOL_PATH)
    report = exp13.validate_report(_read_json(EXP13_REPORT))
    validation = _read_json(EXP13_VALIDATION)
    if protocol.get("protocol_status") != "FROZEN_BEFORE_EXPERIMENT_14_OUTCOME_COMPUTATION":
        raise Experiment14Error("Experiment 14 protocol is not frozen.")
    if validation.get("status") != "PASS":
        raise Experiment14Error("Experiment 13 validation is not PASS.")
    if validation.get("scientific_report_sha256") != _sha256(EXP13_REPORT):
        raise Experiment14Error("Experiment 13 report changed after validation.")
    if report["design"]["subject_count"] != 33 or len(report["fold_results"]) != 198:
        raise Experiment14Error("Experiment 13 design prerequisite changed.")
    return protocol, report, validation


def _load_features(report: dict[str, Any]) -> dict[str, dict[str, np.ndarray]]:
    data: dict[str, dict[str, np.ndarray]] = {}
    for subject in report["design"]["subjects"]:
        path = exp13.FEATURE_DIR / f"{subject}.npz"
        if not path.is_file() or _sha256(path) != report["feature_checkpoints"][subject]:
            raise Experiment14Error(f"Feature checkpoint failed hash validation: {subject}")
        with np.load(path, allow_pickle=False) as saved:
            features = saved["features"].astype(np.float64)
            labels = saved["labels"].astype(np.int32)
        if features.shape != (32, 54) or not np.array_equal(
            np.bincount(labels, minlength=2), np.asarray([16, 16])
        ):
            raise Experiment14Error(f"Feature checkpoint contract changed: {subject}")
        data[subject] = {"features": features, "labels": labels}
    return data


def _metrics(
    probabilities: np.ndarray,
    labels: np.ndarray,
    prediction_sets: np.ndarray,
) -> dict[str, Any]:
    covered = prediction_sets[np.arange(len(labels)), labels]
    sizes = prediction_sets.sum(axis=1)
    predicted = np.argmax(probabilities, axis=1)
    true_probability = np.clip(probabilities[np.arange(len(labels)), labels], 1e-12, 1.0)
    coverage = float(covered.mean())
    full = float(np.mean(sizes == 2))
    return {
        "coverage": coverage,
        "coverage_by_class": {
            exp13.LABEL_NAMES[label]: float(covered[labels == label].mean())
            for label in exp13.LABEL_NAMES
        },
        "average_prediction_set_size": float(sizes.mean()),
        "full_set_frequency": full,
        "empty_set_frequency": float(np.mean(sizes == 0)),
        "base_classifier_accuracy": float(np.mean(predicted == labels)),
        "base_classifier_log_loss": float(-np.log(true_probability).mean()),
        "robustness_loss": float(abs(coverage - TARGET) + 0.25 * full),
    }


def _evaluate_marginal(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    scores = 1.0 - calibration_probabilities[
        np.arange(len(calibration_labels)), calibration_labels
    ]
    threshold = _conformal_quantile(scores, ALPHA)
    prediction_sets = (1.0 - test_probabilities) <= threshold
    return {
        "calibration_mode": "marginal",
        "calibration_score_counts": {"pooled": int(len(scores))},
        "conformal_ranks": {
            "pooled": int(np.ceil((len(scores) + 1) * (1 - ALPHA)))
        },
        "thresholds": {"pooled": float(threshold)},
        **_metrics(test_probabilities, test_labels, prediction_sets),
    }


def _evaluate_class_mondrian(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    thresholds: dict[str, float] = {}
    counts: dict[str, int] = {}
    ranks: dict[str, int] = {}
    prediction_sets = np.zeros_like(test_probabilities, dtype=bool)
    for label, name in exp13.LABEL_NAMES.items():
        mask = calibration_labels == label
        scores = 1.0 - calibration_probabilities[mask, label]
        counts[name] = int(len(scores))
        ranks[name] = int(np.ceil((len(scores) + 1) * (1 - ALPHA)))
        threshold = _conformal_quantile(scores, ALPHA)
        thresholds[name] = float(threshold)
        prediction_sets[:, label] = (1.0 - test_probabilities[:, label]) <= threshold
    return {
        "calibration_mode": "class_mondrian",
        "calibration_score_counts": counts,
        "conformal_ranks": ranks,
        "thresholds": thresholds,
        **_metrics(test_probabilities, test_labels, prediction_sets),
    }


def _run_folds(
    data: dict[str, dict[str, np.ndarray]], subjects: list[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for test_index, test_subject in enumerate(subjects):
        for repetition in range(exp13.REPETITIONS):
            training_subjects, calibration_subjects = exp13._fold_subjects(
                subjects, test_index, repetition
            )
            onboarding_indices, test_indices = exp13._heldout_partition(
                data[test_subject]["labels"], test_index, repetition
            )
            for normalized in (False, True):
                train_x = np.concatenate(
                    [
                        exp13._normalized_subject(data[subject]["features"])
                        if normalized
                        else data[subject]["features"]
                        for subject in training_subjects
                    ]
                )
                train_y = np.concatenate([data[subject]["labels"] for subject in training_subjects])
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
                calibration_probabilities = exp13._predict(model, calibration_x)
                test_probabilities = exp13._predict(model, test_x)
                common = {
                    "test_subject": test_subject,
                    "protocol_version": "V1" if test_subject.startswith("S") else "V2",
                    "repetition": repetition,
                    "training_subjects": training_subjects,
                    "external_calibration_subjects": calibration_subjects,
                    "onboarding_indices": onboarding_indices.tolist(),
                    "test_indices": test_indices.tolist(),
                    "onboarding_labels_used": False,
                    "test_label_counts": {
                        exp13.LABEL_NAMES[label]: int(np.sum(test_y == label))
                        for label in exp13.LABEL_NAMES
                    },
                }
                representation = "normalized" if normalized else "raw"
                rows.append(
                    {
                        **common,
                        "arm_id": f"{representation}_marginal",
                        **_evaluate_marginal(
                            calibration_probabilities,
                            calibration_y,
                            test_probabilities,
                            test_y,
                        ),
                    }
                )
                rows.append(
                    {
                        **common,
                        "arm_id": f"{representation}_class_mondrian",
                        **_evaluate_class_mondrian(
                            calibration_probabilities,
                            calibration_y,
                            test_probabilities,
                            test_y,
                        ),
                    }
                )
    return rows


def _validate_rows(rows: list[dict[str, Any]], subjects: list[str]) -> None:
    expected = len(subjects) * exp13.REPETITIONS * len(ARMS)
    if len(rows) != expected:
        raise Experiment14Error(f"Expected {expected} rows, received {len(rows)}.")
    keys = {(row["test_subject"], row["repetition"], row["arm_id"]) for row in rows}
    if len(keys) != expected:
        raise Experiment14Error("Fold grid is duplicated or incomplete.")
    for row in rows:
        if row["arm_id"] not in ARMS:
            raise Experiment14Error("Unknown arm.")
        subject = row["test_subject"]
        training = set(row["training_subjects"])
        calibration = set(row["external_calibration_subjects"])
        if subject in training or subject in calibration or training & calibration:
            raise Experiment14Error("Subject leakage detected.")
        if set(row["onboarding_indices"]) & set(row["test_indices"]):
            raise Experiment14Error("Onboarding/test leakage detected.")
        if row["onboarding_labels_used"] is not False:
            raise Experiment14Error("Onboarding labels were used.")
        if row["test_label_counts"] != {"non_stress": 8, "stress": 8}:
            raise Experiment14Error("Test balance changed.")
        if row["calibration_mode"] == "marginal":
            if row["calibration_score_counts"] != {"pooled": 256} or row[
                "conformal_ranks"
            ] != {"pooled": 232}:
                raise Experiment14Error("Marginal calibration contract failed.")
        else:
            expected_counts = {"non_stress": 128, "stress": 128}
            expected_ranks = {"non_stress": 117, "stress": 117}
            if row["calibration_score_counts"] != expected_counts or row[
                "conformal_ranks"
            ] != expected_ranks:
                raise Experiment14Error("Class-Mondrian calibration contract failed.")


def _fingerprint(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "protocol_sha256": _sha256(PROTOCOL_PATH),
        "experiment_13_report_sha256": _sha256(EXP13_REPORT),
        "experiment_13_validation_sha256": _sha256(EXP13_VALIDATION),
        "feature_checkpoint_hashes": report["feature_checkpoints"],
    }


def _load_or_run_folds(
    data: dict[str, dict[str, np.ndarray]],
    subjects: list[str],
    report: dict[str, Any],
    use_checkpoint: bool,
) -> list[dict[str, Any]]:
    fingerprint = _fingerprint(report)
    if use_checkpoint and CHECKPOINT.is_file():
        saved = _read_json(CHECKPOINT)
        rows = saved.get("fold_results")
        if saved.get("fingerprint") == fingerprint and isinstance(rows, list):
            _validate_rows(rows, subjects)
            print("Reused valid Experiment 14 fold checkpoint.", flush=True)
            return rows
    rows = _run_folds(data, subjects)
    _validate_rows(rows, subjects)
    _atomic_json(CHECKPOINT, {"fingerprint": fingerprint, "fold_results": rows})
    print("Saved valid Experiment 14 fold checkpoint.", flush=True)
    return rows


def _summary(rows: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    subject_metrics = {
        subject: {
            "coverage": float(np.mean([row["coverage"] for row in rows if row["test_subject"] == subject])),
            "full_set_frequency": float(
                np.mean([row["full_set_frequency"] for row in rows if row["test_subject"] == subject])
            ),
        }
        for subject in subjects
    }
    class_coverage = {
        name: float(np.mean([row["coverage_by_class"][name] for row in rows]))
        for name in exp13.LABEL_NAMES.values()
    }
    return {
        "fold_count": len(rows),
        "mean_coverage": float(np.mean([row["coverage"] for row in rows])),
        "coverage_by_class": class_coverage,
        "absolute_class_coverage_gap": float(abs(class_coverage["non_stress"] - class_coverage["stress"])),
        "worst_subject_mean_coverage": float(min(value["coverage"] for value in subject_metrics.values())),
        "mean_accuracy": float(np.mean([row["base_classifier_accuracy"] for row in rows])),
        "mean_prediction_set_size": float(np.mean([row["average_prediction_set_size"] for row in rows])),
        "mean_full_set_frequency": float(np.mean([row["full_set_frequency"] for row in rows])),
        "mean_empty_set_frequency": float(np.mean([row["empty_set_frequency"] for row in rows])),
        "mean_robustness_loss": float(np.mean([row["robustness_loss"] for row in rows])),
        "protocol_version_metrics": {
            version: {
                "coverage": float(np.mean([row["coverage"] for row in rows if row["protocol_version"] == version])),
                "full_set_frequency": float(
                    np.mean([row["full_set_frequency"] for row in rows if row["protocol_version"] == version])
                ),
            }
            for version in ("V1", "V2")
        },
        "subject_metrics": subject_metrics,
    }


def _analyze(rows: list[dict[str, Any]], subjects: list[str]) -> dict[str, Any]:
    summaries = {
        arm: _summary([row for row in rows if row["arm_id"] == arm], subjects)
        for arm in ARMS
    }
    candidate = summaries["normalized_class_mondrian"]
    normalized_marginal = summaries["normalized_marginal"]
    raw_marginal = summaries["raw_marginal"]
    subject_changes = {
        subject: float(
            candidate["subject_metrics"][subject]["coverage"]
            - normalized_marginal["subject_metrics"][subject]["coverage"]
        )
        for subject in subjects
    }
    version_changes = {
        version: float(
            candidate["protocol_version_metrics"][version]["coverage"]
            - normalized_marginal["protocol_version_metrics"][version]["coverage"]
        )
        for version in ("V1", "V2")
    }
    deltas = {
        "coverage_change_vs_normalized_marginal": float(
            candidate["mean_coverage"] - normalized_marginal["mean_coverage"]
        ),
        "class_coverage_changes_vs_normalized_marginal": {
            name: float(
                candidate["coverage_by_class"][name]
                - normalized_marginal["coverage_by_class"][name]
            )
            for name in exp13.LABEL_NAMES.values()
        },
        "worst_subject_coverage_change_vs_normalized_marginal": float(
            candidate["worst_subject_mean_coverage"]
            - normalized_marginal["worst_subject_mean_coverage"]
        ),
        "full_set_frequency_reduction_vs_raw_marginal": float(
            raw_marginal["mean_full_set_frequency"] - candidate["mean_full_set_frequency"]
        ),
        "full_set_frequency_change_vs_normalized_marginal": float(
            candidate["mean_full_set_frequency"] - normalized_marginal["mean_full_set_frequency"]
        ),
        "protocol_version_coverage_changes_vs_normalized_marginal": version_changes,
        "subject_nonnegative_coverage_change_fraction_vs_normalized_marginal": float(
            np.mean([change >= 0 for change in subject_changes.values()])
        ),
        "subject_coverage_changes_vs_normalized_marginal": subject_changes,
    }
    rng = np.random.default_rng(14_014)
    values = np.asarray(list(subject_changes.values()))
    bootstrap = np.asarray(
        [rng.choice(values, size=len(values), replace=True).mean() for _ in range(5000)]
    )
    deltas["paired_subject_coverage_bootstrap_95_percent_interval"] = [
        float(np.quantile(bootstrap, 0.025)),
        float(np.quantile(bootstrap, 0.975)),
    ]
    checks = {
        "mean_coverage_at_least_0_88": candidate["mean_coverage"] >= 0.88,
        "each_class_coverage_at_least_0_88": min(candidate["coverage_by_class"].values()) >= 0.88,
        "class_coverage_gap_at_most_0_05": candidate["absolute_class_coverage_gap"] <= 0.05,
        "worst_subject_coverage_change_vs_normalized_marginal_at_least_minus_0_05": deltas[
            "worst_subject_coverage_change_vs_normalized_marginal"
        ] >= -0.05,
        "full_set_frequency_reduction_vs_raw_marginal_at_least_0_05": deltas[
            "full_set_frequency_reduction_vs_raw_marginal"
        ] >= 0.05,
        "coverage_change_vs_normalized_marginal_nonnegative_in_both_protocol_versions": all(
            change >= 0 for change in version_changes.values()
        ),
        "subject_nonnegative_coverage_change_fraction_vs_normalized_marginal_at_least_0_60": deltas[
            "subject_nonnegative_coverage_change_fraction_vs_normalized_marginal"
        ] >= 0.60,
        "empty_set_frequency_at_most_0_01": candidate["mean_empty_set_frequency"] <= 0.01,
    }
    if all(checks.values()):
        decision = "CLASS_CONDITIONAL_REPAIR_SUPPORTED"
    elif checks["mean_coverage_at_least_0_88"] and checks["each_class_coverage_at_least_0_88"]:
        decision = "AGGREGATE_CLASS_REPAIR_ONLY_SUBJECT_SAFETY_NOT_SUPPORTED"
    else:
        decision = "CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED"
    return {
        "primary_decision": decision,
        "all_preregistered_checks_pass": all(checks.values()),
        "preregistered_checks": checks,
        "effect_deltas": deltas,
        "arm_summaries": summaries,
    }


def _verify_experiment_13_continuity(rows: list[dict[str, Any]], report: dict[str, Any]) -> None:
    map14 = {
        (row["test_subject"], row["repetition"], row["arm_id"]): row
        for row in rows
    }
    mapping = {
        "lda_raw": "raw_marginal",
        "lda_subject_robust_normalized": "normalized_marginal",
    }
    metrics = (
        "coverage",
        "coverage_by_class",
        "average_prediction_set_size",
        "full_set_frequency",
        "empty_set_frequency",
        "base_classifier_accuracy",
        "base_classifier_log_loss",
        "robustness_loss",
    )
    for old in report["fold_results"]:
        current = map14[(old["test_subject"], old["repetition"], mapping[old["arm_id"]])]
        for metric in metrics:
            if current[metric] != old[metric]:
                raise Experiment14Error(f"Experiment 13 continuity failed: {metric}")


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("experiment_name") != EXPERIMENT_NAME:
        raise Experiment14Error("Experiment name mismatch.")
    _validate_rows(report.get("fold_results", []), report.get("design", {}).get("subjects", []))
    if report.get("analysis", {}).get("primary_decision") not in {
        "CLASS_CONDITIONAL_REPAIR_SUPPORTED",
        "AGGREGATE_CLASS_REPAIR_ONLY_SUBJECT_SAFETY_NOT_SUPPORTED",
        "CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED",
    }:
        raise Experiment14Error("Unknown primary decision.")
    return report


def build_report(use_checkpoint: bool = True) -> dict[str, Any]:
    protocol, exp13_report, exp13_validation = _load_prerequisites()
    data = _load_features(exp13_report)
    subjects = exp13_report["design"]["subjects"]
    rows = _load_or_run_folds(data, subjects, exp13_report, use_checkpoint)
    _verify_experiment_13_continuity(rows, exp13_report)
    report = {
        "experiment_name": EXPERIMENT_NAME,
        "research_question": protocol["research_question"],
        "preregistered_protocol": {
            "path": str(PROTOCOL_PATH.resolve()),
            "sha256": _sha256(PROTOCOL_PATH),
            "status": protocol["protocol_status"],
        },
        "prerequisites": {
            "experiment_13_report_sha256": _sha256(EXP13_REPORT),
            "experiment_13_validation_sha256": _sha256(EXP13_VALIDATION),
            "experiment_13_validation_status": exp13_validation["status"],
            "feature_checkpoint_hashes": exp13_report["feature_checkpoints"],
        },
        "design": {
            "subjects": subjects,
            "subject_count": len(subjects),
            "repetitions_per_subject": exp13.REPETITIONS,
            "arms": list(ARMS),
            "expected_fold_rows": 396,
            "only_calibration_rule_changed": True,
        },
        "fold_results": rows,
        "analysis": _analyze(rows, subjects),
        "guardrails": protocol["guardrails"],
        "validation": {
            "protocol_frozen": True,
            "experiment_13_continuity_exact": True,
            "subject_disjoint_folds": True,
            "onboarding_test_disjoint": True,
            "onboarding_labels_used": False,
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
        "## Arm comparison",
        "",
        "| Arm | Coverage | Non-stress | Stress | Class gap | Worst subject | Full sets | Empty sets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        value = analysis["arm_summaries"][arm]
        lines.append(
            f"| {arm} | {value['mean_coverage']:.4f} | "
            f"{value['coverage_by_class']['non_stress']:.4f} | "
            f"{value['coverage_by_class']['stress']:.4f} | "
            f"{value['absolute_class_coverage_gap']:.4f} | "
            f"{value['worst_subject_mean_coverage']:.4f} | "
            f"{value['mean_full_set_frequency']:.4f} | "
            f"{value['mean_empty_set_frequency']:.4f} |"
        )
    delta = analysis["effect_deltas"]
    lines.extend(
        [
            "",
            "## Frozen primary checks",
            "",
            *[f"- {name}: **{passed}**" for name, passed in analysis["preregistered_checks"].items()],
            "",
            "## Primary candidate deltas",
            "",
            f"- Coverage change versus normalized/marginal: {delta['coverage_change_vs_normalized_marginal']:.4f}",
            f"- Class coverage changes: {delta['class_coverage_changes_vs_normalized_marginal']}",
            f"- Worst-subject coverage change: {delta['worst_subject_coverage_change_vs_normalized_marginal']:.4f}",
            f"- Full-set reduction versus raw/marginal: {delta['full_set_frequency_reduction_vs_raw_marginal']:.4f}",
            f"- Protocol-version coverage changes: {delta['protocol_version_coverage_changes_vs_normalized_marginal']}",
            f"- Subject nonnegative coverage-change fraction: {delta['subject_nonnegative_coverage_change_fraction_vs_normalized_marginal']:.4f}",
            f"- Paired-subject bootstrap 95% interval: {delta['paired_subject_coverage_bootstrap_95_percent_interval']}",
            "",
            "## Integrity",
            "",
            f"- Fold rows: {len(report['fold_results'])}",
            "- Exact Experiment 13 marginal-arm continuity: PASS",
            "- Only the conformal conditioning rule changed",
            "- API/model call: no",
            "- Raw-data mutation: no",
            "- Independent exact replay: pending",
            "",
        ]
    )
    return "\n".join(lines)


def reproducibility_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_name": EXPERIMENT_NAME,
        "execution_mode": "deterministic NumPy replay from validated Experiment 13 feature checkpoints",
        "protocol_sha256": report["preregistered_protocol"]["sha256"],
        "experiment_13_report_sha256": report["prerequisites"]["experiment_13_report_sha256"],
        "experiment_13_validation_sha256": report["prerequisites"]["experiment_13_validation_sha256"],
        "feature_checkpoint_hashes": report["prerequisites"]["feature_checkpoint_hashes"],
        "fold_result_count": len(report["fold_results"]),
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
            f"- Experiment 13 report SHA-256: `{summary['experiment_13_report_sha256']}`",
            f"- Experiment 13 validation SHA-256: `{summary['experiment_13_validation_sha256']}`",
            f"- Feature checkpoints: {len(summary['feature_checkpoint_hashes'])}",
            f"- Fold results: {summary['fold_result_count']}",
            "- API/model call: no",
            "- Raw-data mutation: no",
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
    print(f"Experiment 14 complete: {report['analysis']['primary_decision']}", flush=True)
    print(f"Fold rows: {len(report['fold_results'])}", flush=True)


if __name__ == "__main__":
    main()
