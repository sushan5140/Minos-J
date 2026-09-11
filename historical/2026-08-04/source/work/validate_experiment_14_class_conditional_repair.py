"""Independently replay and validate Meno-J Experiment 14."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import warnings

import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_14_class_conditional_repair as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_14_class_conditional_repair.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_14_class_conditional_repair.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_14_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_14_reproducibility_summary.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_14_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_14_working_theory_update.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_14_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_14_validation.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"Expected JSON object: {path}"
    return value


def _credential_scan() -> list[str]:
    marker = "sk-" + "or-v1"
    matches: list[str] = []
    excluded = {".git", "vendor", "__pycache__", "external", "e13_data"}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or excluded.intersection(path.parts):
            continue
        if path.name == ".env" or path.suffix.lower() not in {".py", ".json", ".md", ".txt"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if marker in content:
            matches.append(str(path.resolve()))
    return sorted(set(matches))


def main() -> None:
    required = (
        REPORT_JSON,
        REPORT_MD,
        REPRO_JSON,
        REPRO_MD,
        THEORY_JSON,
        THEORY_MD,
        experiment.PROTOCOL_PATH,
        experiment.EXP13_REPORT,
        experiment.EXP13_VALIDATION,
    )
    for path in required:
        assert path.is_file(), f"Missing Experiment 14 artifact: {path}"
        path.read_text(encoding="utf-8")

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    assert REPORT_MD.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    protocol, exp13_report, exp13_validation = experiment._load_prerequisites()
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["prerequisites"]["experiment_13_report_sha256"] == _sha256(
        experiment.EXP13_REPORT
    )
    assert saved["prerequisites"]["experiment_13_validation_sha256"] == _sha256(
        experiment.EXP13_VALIDATION
    )
    assert exp13_validation["status"] == "PASS"
    assert protocol["design"]["expected_fold_rows"] == 396

    for subject, expected_hash in saved["prerequisites"]["feature_checkpoint_hashes"].items():
        path = experiment.exp13.FEATURE_DIR / f"{subject}.npz"
        assert path.is_file() and _sha256(path) == expected_hash

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Fresh deterministic replay differs from saved report."
    assert len(replayed["fold_results"]) == 396

    subjects = set(saved["design"]["subjects"])
    split_map: dict[tuple[str, int], tuple] = {}
    metric_map: dict[tuple[str, int, str], dict] = {}
    for row in saved["fold_results"]:
        test_subject = row["test_subject"]
        training = set(row["training_subjects"])
        calibration = set(row["external_calibration_subjects"])
        assert test_subject not in training and test_subject not in calibration
        assert not training & calibration
        assert training | calibration | {test_subject} == subjects
        assert len(training) == 24 and len(calibration) == 8
        onboarding = set(row["onboarding_indices"])
        test = set(row["test_indices"])
        assert len(onboarding) == 16 and len(test) == 16
        assert not onboarding & test and onboarding | test == set(range(32))
        assert row["onboarding_labels_used"] is False
        split = (
            tuple(row["training_subjects"]),
            tuple(row["external_calibration_subjects"]),
            tuple(row["onboarding_indices"]),
            tuple(row["test_indices"]),
        )
        split_key = (test_subject, row["repetition"])
        if split_key in split_map:
            assert split_map[split_key] == split
        else:
            split_map[split_key] = split
        if row["calibration_mode"] == "marginal":
            assert row["calibration_score_counts"] == {"pooled": 256}
            assert row["conformal_ranks"] == {"pooled": 232}
        else:
            assert row["calibration_score_counts"] == {"non_stress": 128, "stress": 128}
            assert row["conformal_ranks"] == {"non_stress": 117, "stress": 117}
        representation = "normalized" if row["arm_id"].startswith("normalized") else "raw"
        metric_key = (test_subject, row["repetition"], representation)
        metrics = {
            "base_classifier_accuracy": row["base_classifier_accuracy"],
            "base_classifier_log_loss": row["base_classifier_log_loss"],
        }
        if metric_key in metric_map:
            assert metric_map[metric_key] == metrics
        else:
            metric_map[metric_key] = metrics
    assert len(split_map) == 99 and len(metric_map) == 198

    experiment._verify_experiment_13_continuity(saved["fold_results"], exp13_report)
    analysis = saved["analysis"]
    assert analysis["primary_decision"] == "CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED"
    assert analysis["all_preregistered_checks_pass"] is False
    checks = analysis["preregistered_checks"]
    assert checks["mean_coverage_at_least_0_88"] is False
    assert checks["each_class_coverage_at_least_0_88"] is False
    assert all(
        value is True
        for name, value in checks.items()
        if name not in {"mean_coverage_at_least_0_88", "each_class_coverage_at_least_0_88"}
    )
    candidate = analysis["arm_summaries"]["normalized_class_mondrian"]
    assert candidate["mean_coverage"] < 0.88
    assert min(candidate["coverage_by_class"].values()) < 0.88

    theory = _read_json(THEORY_JSON)
    evidence = theory["evidence"]
    assert theory["primary_decision"] == analysis["primary_decision"]
    assert evidence["normalized_class_mondrian_coverage"] == candidate["mean_coverage"]
    assert evidence["normalized_class_mondrian_class_gap"] == candidate[
        "absolute_class_coverage_gap"
    ]
    assert evidence["coverage_change"] == analysis["effect_deltas"][
        "coverage_change_vs_normalized_marginal"
    ]

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    theory["update_status"] = "VALIDATED"
    theory["validation"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    experiment._atomic_json(THEORY_JSON, theory)
    THEORY_MD.write_text(
        THEORY_MD.read_text(encoding="utf-8").replace(
            "Independent exact replay: **pending**.",
            "Independent exact replay: **PASS**.",
        ),
        encoding="utf-8",
    )

    reproducibility = experiment.reproducibility_summary(saved)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(REPORT_JSON)
    reproducibility["markdown_report_sha256"] = _sha256(REPORT_MD)
    reproducibility["runner_sha256"] = _sha256(
        PROJECT_DIR / "run_experiment_14_class_conditional_repair.py"
    )
    reproducibility["validator"] = str(Path(__file__).resolve())
    experiment._atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        experiment.render_reproducibility_markdown(reproducibility).replace(
            "- Independent exact replay: pending",
            "- Independent exact replay: PASS\n"
            f"- Scientific-report SHA-256: `{reproducibility['scientific_report_sha256']}`\n"
            f"- Markdown-report SHA-256: `{reproducibility['markdown_report_sha256']}`\n"
            f"- Runner SHA-256: `{reproducibility['runner_sha256']}`",
        ),
        encoding="utf-8",
    )

    validation = {
        "experiment_name": experiment.EXPERIMENT_NAME,
        "status": "PASS",
        "checks": {
            "required_outputs_exist": True,
            "all_outputs_decode_as_utf8": True,
            "experiment_13_prerequisite_hashes_match": True,
            "all_33_feature_checkpoint_hashes_match": True,
            "independent_exact_replay_matches": True,
            "result_grid_396_complete": True,
            "all_four_arms_share_identical_splits": True,
            "subject_disjoint_training_calibration_test": True,
            "onboarding_test_disjoint_and_complete": True,
            "onboarding_labels_unused": True,
            "marginal_score_counts_and_ranks_match": True,
            "class_mondrian_score_counts_and_ranks_match": True,
            "classifier_metrics_identical_across_calibration_modes": True,
            "experiment_13_marginal_continuity_exact": True,
            "frozen_decision_rules_recomputed": True,
            "working_theory_update_matches_results": True,
            "no_runtime_warnings_on_replay": True,
            "credential_scan_passes": True,
        },
        "primary_decision": analysis["primary_decision"],
        "scientific_report_sha256": _sha256(REPORT_JSON),
        "reproducibility_summary_sha256": _sha256(REPRO_JSON),
        "working_theory_sha256": _sha256(THEORY_JSON),
    }
    experiment._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 14 — Validation",
                "",
                "**PASS**",
                "",
                "- A fresh deterministic replay exactly reproduced all 396 fold rows.",
                "- All four arms used identical subject, onboarding, and test splits.",
                "- Training, external calibration, and held-out subjects were disjoint.",
                "- Marginal and class-Mondrian score counts and conformal ranks were recomputed.",
                "- Class conditioning did not alter classifier probabilities or accuracy.",
                "- Both marginal arms exactly matched their Experiment 13 counterparts.",
                "- All frozen decision checks and the working-theory update match the evidence.",
                "- All outputs decode as UTF-8 and the credential scan passed.",
                f"- Primary decision: `{analysis['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 14 class-conditional repair validation: PASS")


if __name__ == "__main__":
    main()
