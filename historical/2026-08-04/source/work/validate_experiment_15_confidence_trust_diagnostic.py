"""Independently replay and validate Meno-J Experiment 15 and its literature ledger."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import warnings


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_15_confidence_trust_diagnostic as experiment  # noqa: E402
import run_literature_review_after_experiment_14 as literature_builder  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_15_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_15_validation.md"


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
        experiment.JSON_OUTPUT,
        experiment.MARKDOWN_OUTPUT,
        experiment.REPRO_JSON,
        experiment.REPRO_MD,
        experiment.THEORY_JSON,
        experiment.THEORY_MD,
        experiment.PROTOCOL_PATH,
        experiment.LITERATURE_JSON,
        literature_builder.MARKDOWN_OUTPUT,
        experiment.EXP14_REPORT,
        experiment.EXP14_VALIDATION,
    )
    for path in required:
        assert path.is_file(), f"Missing Experiment 15 artifact: {path}"
        path.read_text(encoding="utf-8")

    literature = _read_json(experiment.LITERATURE_JSON)
    assert literature == literature_builder._report()
    assert literature_builder.MARKDOWN_OUTPUT.read_text(encoding="utf-8") == (
        literature_builder.render_markdown(literature)
    )
    sources = literature["sources"]
    assert len(sources) == 19
    assert len({source["source_id"] for source in sources}) == 19
    assert len({source["url"] for source in sources}) == 19
    assert sum(source["full_text_reviewed"] for source in sources) == 18
    assert sum(not source["full_text_reviewed"] for source in sources) == 1
    source_ids = {source["source_id"] for source in sources}
    for source in sources:
        assert source["url"].startswith("https://")
        assert source["title"] and source["authors"] and source["evidence"]
        assert source["meno_j_implication"]
    for finding in literature["cross_paper_findings"]:
        assert set(finding["supported_by"]) <= source_ids
        assert len(finding["supported_by"]) >= 2

    saved = experiment.validate_report(_read_json(experiment.JSON_OUTPUT))
    assert experiment.MARKDOWN_OUTPUT.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    protocol, _, exp14_report, exp14_validation = experiment._load_prerequisites()
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["literature_review"]["sha256"] == _sha256(experiment.LITERATURE_JSON)
    assert saved["prerequisites"]["experiment_14_report_sha256"] == _sha256(
        experiment.EXP14_REPORT
    )
    assert saved["prerequisites"]["experiment_14_validation_sha256"] == _sha256(
        experiment.EXP14_VALIDATION
    )
    assert exp14_validation["status"] == "PASS"
    assert protocol["design"]["expected_fold_rows"] == 198
    assert protocol["design"]["expected_observation_rows"] == 3168

    for subject, expected_hash in saved["prerequisites"]["feature_checkpoint_hashes"].items():
        path = experiment.exp13.FEATURE_DIR / f"{subject}.npz"
        assert path.is_file() and _sha256(path) == expected_hash

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Fresh deterministic replay differs from saved Experiment 15 report."
    assert len(replayed["fold_results"]) == 198
    assert len(replayed["observation_results"]) == 3168
    experiment._verify_experiment_14_continuity(replayed["fold_results"], exp14_report)

    subjects = set(saved["design"]["subjects"])
    fold_map = {
        (row["test_subject"], row["repetition"], row["arm_id"]): row
        for row in saved["fold_results"]
    }
    assert len(fold_map) == 198
    observations_by_fold: dict[tuple[str, int, str], list[dict]] = {}
    for row in saved["observation_results"]:
        key = (row["test_subject"], row["repetition"], row["arm_id"])
        observations_by_fold.setdefault(key, []).append(row)
        fold = fold_map[key]
        assert row["confidence_threshold"] == fold["confidence_threshold"]
        assert row["trust_threshold"] == fold["trust_threshold"]
        assert row["high_confidence"] == (row["confidence"] >= row["confidence_threshold"])
        assert row["low_trust"] == (row["trust_score"] <= row["trust_threshold"])
        assert row["test_index"] in fold["test_indices"]
    assert set(observations_by_fold) == set(fold_map)
    for key, rows in observations_by_fold.items():
        assert len(rows) == 16
        fold = fold_map[key]
        assert {row["test_index"] for row in rows} == set(fold["test_indices"])
        assert sum(row["covered"] for row in rows) / 16 == fold["coverage"]
        reconstructed = {
            name: sum(row["risk_quadrant"] == name for row in rows)
            for name in fold["quadrant_counts"]
        }
        assert reconstructed == fold["quadrant_counts"]
        training = set(fold["training_subjects"])
        calibration = set(fold["external_calibration_subjects"])
        assert len(training) == 24 and len(calibration) == 8
        assert fold["test_subject"] not in training | calibration
        assert training | calibration | {fold["test_subject"]} == subjects
        assert not training & calibration
        assert not set(fold["onboarding_indices"]) & set(fold["test_indices"])
        assert fold["onboarding_labels_used"] is False

    analysis = saved["analysis"]
    assert analysis["primary_decision"] == "CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_NOT_SUPPORTED"
    assert analysis["all_preregistered_checks_pass"] is False
    checks = analysis["preregistered_checks"]
    failed_checks = [name for name, passed in checks.items() if not passed]
    assert failed_checks == [
        "primary_high_risk_miscoverage_minus_high_confidence_high_trust_at_least_0_10"
    ]
    primary = analysis["arm_analyses"][experiment.PRIMARY_ARM]
    risk = primary["quadrant_summaries"]["high_confidence_low_trust"]
    high_trust = primary["quadrant_summaries"]["high_confidence_high_trust"]
    assert risk["coverage"] < 0.85
    assert primary["high_risk_miscoverage_minus_all_other"] >= 0.10
    assert primary["high_risk_miscoverage_minus_high_confidence_high_trust"] < 0.10
    assert abs(risk["coverage"] - high_trust["coverage"]) < 0.05

    theory = _read_json(experiment.THEORY_JSON)
    expected_theory = experiment._theory_update(saved)
    assert theory["primary_decision"] == analysis["primary_decision"]
    assert theory["evidence"] == expected_theory["evidence"]
    assert theory["working_theory"] == expected_theory["working_theory"]
    assert theory["next_action"] == expected_theory["next_action"]

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    theory["update_status"] = "VALIDATED"
    theory["validation"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    experiment._atomic_json(experiment.THEORY_JSON, theory)
    experiment.THEORY_MD.write_text(
        experiment.render_theory_markdown(theory).replace(
            "Independent exact replay: **pending**.",
            "Independent exact replay: **PASS**.",
        ),
        encoding="utf-8",
    )

    reproducibility = experiment.reproducibility_summary(saved)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(experiment.JSON_OUTPUT)
    reproducibility["markdown_report_sha256"] = _sha256(experiment.MARKDOWN_OUTPUT)
    reproducibility["runner_sha256"] = _sha256(
        PROJECT_DIR / "run_experiment_15_confidence_trust_diagnostic.py"
    )
    reproducibility["validator"] = str(Path(__file__).resolve())
    experiment._atomic_json(experiment.REPRO_JSON, reproducibility)
    experiment.REPRO_MD.write_text(
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
            "literature_ledger_has_19_unique_primary_sources": True,
            "literature_full_text_and_partial_statuses_explicit": True,
            "literature_finding_citations_resolve_to_ledger": True,
            "experiment_14_prerequisite_hashes_match": True,
            "all_33_feature_checkpoint_hashes_match": True,
            "independent_exact_replay_matches": True,
            "fold_grid_198_complete": True,
            "observation_grid_3168_complete": True,
            "subject_disjoint_training_calibration_test": True,
            "onboarding_test_disjoint_and_complete": True,
            "onboarding_labels_unused": True,
            "risk_flags_and_quadrants_recomputed": True,
            "fold_aggregates_recomputed_from_observations": True,
            "experiment_14_outcome_continuity_exact": True,
            "frozen_decision_rule_recomputed": True,
            "negative_primary_decision_preserved": True,
            "no_runtime_warnings_on_replay": True,
            "credential_scan_passes": True,
        },
        "primary_decision": analysis["primary_decision"],
        "scientific_report_sha256": _sha256(experiment.JSON_OUTPUT),
        "literature_review_sha256": _sha256(experiment.LITERATURE_JSON),
        "reproducibility_summary_sha256": _sha256(experiment.REPRO_JSON),
        "working_theory_sha256": _sha256(experiment.THEORY_JSON),
    }
    experiment._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 15 — Validation",
                "",
                "**PASS**",
                "",
                "- The 19-source literature ledger is internally complete; 18 sources are marked full-text and one publisher source is explicitly partial-only.",
                "- A fresh deterministic replay exactly reproduced all 198 folds and 3,168 heldout observations.",
                "- Training, external calibration, and heldout subjects remained disjoint.",
                "- Risk thresholds, flags, quadrants, and fold aggregates were recomputed.",
                "- The two retained conformal arms exactly match Experiment 14 outcomes.",
                "- The frozen negative decision was preserved: low trust added no material separation among high-confidence windows.",
                "- All outputs decode as UTF-8 and the credential scan passed.",
                f"- Primary decision: `{analysis['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 15 confidence–trust diagnostic validation: PASS")


if __name__ == "__main__":
    main()
