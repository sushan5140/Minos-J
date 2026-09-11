"""Independently replay and validate Meno-J Experiment 13."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import warnings
import zipfile

import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_13_external_replication as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_13_external_replication.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_13_external_replication.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_13_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_13_reproducibility_summary.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_13_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_13_working_theory_update.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_13_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_13_validation.md"


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
        experiment.INTEGRITY_PATH,
        experiment.INVENTORY_PATH,
    )
    for path in required:
        assert path.is_file(), f"Missing Experiment 13 artifact: {path}"
        path.read_text(encoding="utf-8")

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    assert REPORT_MD.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    protocol, integrity, inventory = experiment._load_prerequisites()
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["prerequisites"]["integrity_report_sha256"] == _sha256(
        experiment.INTEGRITY_PATH
    )
    assert saved["prerequisites"]["inventory_report_sha256"] == _sha256(
        experiment.INVENTORY_PATH
    )

    archive = Path(integrity["canonical_archive_path"])
    assert archive.is_file()
    assert archive.stat().st_size == integrity["archive_size_bytes"]
    assert _sha256(archive) == integrity["archive_sha256"]
    with zipfile.ZipFile(archive) as zipped:
        assert len(zipped.infolist()) == integrity["member_count"]
        assert zipped.testzip() is None

    assert saved["design"]["subjects"] == inventory["primary_subjects"]
    assert saved["design"]["subject_count"] == 33
    assert saved["design"]["expected_fold_rows"] == 198
    assert len(saved["fold_results"]) == 198
    assert len(saved["feature_checkpoints"]) == 33

    for subject, expected_hash in saved["feature_checkpoints"].items():
        path = experiment.FEATURE_DIR / f"{subject}.npz"
        assert path.is_file() and _sha256(path) == expected_hash
        with np.load(path, allow_pickle=False) as checkpoint:
            assert checkpoint["features"].shape == (32, 54)
            assert checkpoint["labels"].shape == (32,)
            assert np.array_equal(
                np.bincount(checkpoint["labels"].astype(int), minlength=2),
                np.asarray([16, 16]),
            )
            assert checkpoint["feature_names"].astype(str).tolist() == experiment.feature_names()

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Fresh deterministic fold replay differs from the saved report."

    subjects = set(saved["design"]["subjects"])
    split_keys: dict[tuple[str, int], tuple] = {}
    for row in saved["fold_results"]:
        test_subject = row["test_subject"]
        training = set(row["training_subjects"])
        calibration = set(row["external_calibration_subjects"])
        assert test_subject not in training
        assert test_subject not in calibration
        assert not training & calibration
        assert training | calibration | {test_subject} == subjects
        assert len(training) == 24 and len(calibration) == 8
        onboarding = set(row["onboarding_indices"])
        test = set(row["test_indices"])
        assert len(onboarding) == 16 and len(test) == 16
        assert not onboarding & test
        assert onboarding | test == set(range(32))
        assert row["onboarding_label_counts_ignored"] == {"non_stress": 8, "stress": 8}
        assert row["test_label_counts"] == {"non_stress": 8, "stress": 8}
        assert row["calibration_score_count"] == 256
        assert row["conformal_rank"] == int(np.ceil(257 * (1 - experiment.ALPHA))) == 232
        key = (test_subject, row["repetition"])
        split = (
            tuple(row["training_subjects"]),
            tuple(row["external_calibration_subjects"]),
            tuple(row["onboarding_indices"]),
            tuple(row["test_indices"]),
        )
        if key in split_keys:
            assert split_keys[key] == split
        else:
            split_keys[key] = split
    assert len(split_keys) == 99

    analysis = saved["analysis"]
    assert analysis["primary_decision"] == "EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED"
    assert analysis["all_preregistered_checks_pass"] is False
    checks = analysis["preregistered_checks"]
    assert checks["accuracy_improvement_at_least_0_08"] is False
    assert checks["normalized_mean_coverage_at_least_0_88"] is False
    assert all(value is True for name, value in checks.items() if name not in {
        "accuracy_improvement_at_least_0_08",
        "normalized_mean_coverage_at_least_0_88",
    })

    theory = _read_json(THEORY_JSON)
    assert theory["primary_decision"] == analysis["primary_decision"]
    evidence = theory["evidence"]
    deltas = analysis["effect_deltas"]
    assert evidence["accuracy_change"] == deltas["accuracy_change"]
    assert evidence["full_set_frequency_reduction"] == deltas["full_set_frequency_reduction"]
    assert evidence["robustness_loss_reduction"] == deltas["robustness_loss_reduction"]
    assert evidence["coverage_change"] == deltas["coverage_change"]
    assert evidence["normalized_mean_coverage"] == analysis["arm_summaries"][
        "lda_subject_robust_normalized"
    ]["mean_coverage"]

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
    reproducibility["runner_sha256"] = _sha256(PROJECT_DIR / "run_experiment_13_external_replication.py")
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
            "archive_size_sha256_and_crc_pass": True,
            "protocol_integrity_inventory_hashes_match": True,
            "all_33_feature_checkpoint_hashes_match": True,
            "feature_shapes_labels_and_names_pass": True,
            "independent_exact_fold_replay_matches": True,
            "result_grid_198_complete": True,
            "subject_disjoint_training_calibration_test": True,
            "onboarding_test_disjoint_and_complete": True,
            "paired_arms_use_identical_splits": True,
            "conformal_score_counts_and_ranks_match": True,
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
                "# Meno-J Experiment 13 — Validation",
                "",
                "**PASS**",
                "",
                "- The independent dataset archive passed size, SHA-256, member-count, and full CRC checks.",
                "- All 33 subject feature checkpoints passed hash, shape, label-balance, and feature-name checks.",
                "- A fresh deterministic replay exactly reproduced all 198 fold rows without runtime warnings.",
                "- Training, external calibration, and test subjects are disjoint in every fold.",
                "- Onboarding and test windows are disjoint, balanced, and complete; onboarding labels are not used.",
                "- Both arms use identical splits and every conformal rank independently recomputes to 232.",
                "- Frozen decision rules and the working-theory update match the scientific report.",
                "- All required outputs decode as UTF-8 and the credential scan passed.",
                f"- Primary decision: `{analysis['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 13 external replication validation: PASS")


if __name__ == "__main__":
    main()
