"""Independently replay and validate Meno-J Experiment 12."""

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

import run_experiment_12_temporal_readiness_surface as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_12_temporal_readiness_surface.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_12_temporal_readiness_surface.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_12_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_12_reproducibility_summary.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_12_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_12_working_theory_update.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_12_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_12_validation.md"


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
    excluded = {".git", "vendor", "__pycache__", "external"}
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
    required = (REPORT_JSON, REPORT_MD, REPRO_JSON, REPRO_MD, THEORY_JSON, THEORY_MD)
    for path in required:
        assert path.is_file(), f"Missing Experiment 12 artifact: {path}"
        path.read_text(encoding="utf-8")

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    assert REPORT_MD.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["prerequisites"]["experiment_11_report_sha256"] == _sha256(
        experiment.EXP11_REPORT
    )
    assert saved["prerequisites"]["experiment_11_validation_sha256"] == _sha256(
        experiment.EXP11_VALIDATION
    )

    checkpoint = _read_json(experiment.CHECKPOINT)
    assert checkpoint["fingerprint"] == experiment._fingerprint(
        _read_json(experiment.EXP11_REPORT)
    )
    assert checkpoint["fingerprint"]["runner_sha256"] == _sha256(
        PROJECT_DIR / "run_experiment_12_temporal_readiness_surface.py"
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Independent deterministic replay differs from saved report."
    assert len(replayed["result_rows"]) == 2160
    assert len(replayed["aggregate_results"]) == 16
    assert replayed["design_counts"]["subjects"] == 15
    assert replayed["design_counts"]["temporal_holdouts"] == ["early", "middle", "late"]

    _, _, data = experiment._load_prerequisites()
    for row in replayed["result_rows"]:
        subject = row["test_subject"]
        expected_phase = row["test_phase_code"]
        test = np.asarray(row["test_indices"], dtype=int)
        pool = np.asarray(row["normalization_pool_indices"], dtype=int)
        calibration = np.asarray(row["personal_calibration_indices"], dtype=int)
        assert np.all(data[subject]["phase"][test] == expected_phase)
        assert np.all(data[subject]["phase"][pool] != expected_phase)
        assert np.all(data[subject]["phase"][calibration] != expected_phase)
        assert not set(test) & set(pool)
        assert not set(test) & set(calibration)
        count = row["personal_calibration_count"]
        assert row["conformal_rank"] == int(np.ceil((count + 1) * (1 - experiment.ALPHA)))

    analysis = replayed["analysis"]
    assert analysis["primary_decision"] == "NORMALIZATION_REPLICATED_WITHOUT_SURFACE_INTERACTION"
    assert analysis["subject_normalization"]["supported"] is True
    assert all(
        value >= 0.05
        for value in analysis["subject_normalization"]["phase_accuracy_changes"].values()
    )
    assert analysis["readiness_surface"]["supported"] is False
    assert all(
        boundary["supported"] is False
        for boundary in analysis["order_statistic_boundaries"].values()
    )
    assert analysis["temperature_interference"]["decision"] == "TEMP_INTERFERENCE_NOT_REPLICATED"
    targets = analysis["predeclared_subject_checks"]
    assert targets["S4_replication_supported"] is True
    assert targets["S2_residual_failure_replicated"] is True

    theory = _read_json(THEORY_JSON)
    assert theory["primary_decision"] == analysis["primary_decision"]
    updates = {row["claim"]: row for row in theory["working_theory_updates"]}
    assert len(updates) == 6
    normalization_claim = updates[
        "Subject baseline normalization improves wearable-state representation under temporal-block holdout."
    ]
    assert normalization_claim["evidence"]["accuracy_change"] == analysis[
        "subject_normalization"
    ]["accuracy_change"]
    s4_claim = updates["S4's normalization repair persists across temporal portions of the recording."]
    assert s4_claim["evidence"]["accuracy_change"] == targets["S4_accuracy_change"]
    temperature_claim = updates[
        "Temperature-feature interference is a stable mechanism independent of subject normalization."
    ]
    assert temperature_claim["evidence"]["decision"] == analysis["temperature_interference"][
        "decision"
    ]

    for subject, expected_hash in replayed["prerequisites"]["feature_checkpoint_hashes"].items():
        feature_path = experiment.exp10.FEATURE_DIR / f"{subject}.npz"
        assert feature_path.is_file() and _sha256(feature_path) == expected_hash

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    theory["update_status"] = "VALIDATED"
    theory["validation"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    experiment._atomic_json(THEORY_JSON, theory)
    theory_markdown = THEORY_MD.read_text(encoding="utf-8").replace(
        "Independent exact replay: **pending**.",
        "Independent exact replay: **PASS**.",
    )
    THEORY_MD.write_text(theory_markdown, encoding="utf-8")

    reproducibility = experiment.reproducibility_summary(replayed)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(REPORT_JSON)
    reproducibility["markdown_report_sha256"] = _sha256(REPORT_MD)
    reproducibility["runner_sha256"] = _sha256(
        PROJECT_DIR / "run_experiment_12_temporal_readiness_surface.py"
    )
    reproducibility["validator"] = str(Path(__file__).resolve())
    experiment._atomic_json(REPRO_JSON, reproducibility)
    repro_markdown = experiment.render_reproducibility_markdown(reproducibility).replace(
        "- Independent exact replay: pending",
        "- Independent exact replay: PASS\n"
        f"- Scientific-report SHA-256: `{reproducibility['scientific_report_sha256']}`\n"
        f"- Markdown-report SHA-256: `{reproducibility['markdown_report_sha256']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`",
    )
    REPRO_MD.write_text(repro_markdown, encoding="utf-8")

    validation = {
        "experiment_name": experiment.EXPERIMENT_NAME,
        "status": "PASS",
        "checks": {
            "required_outputs_exist": True,
            "all_outputs_decode_as_utf8": True,
            "saved_schema_and_invariants_pass": True,
            "markdown_matches_json": True,
            "independent_exact_replay_matches": True,
            "result_grid_2160_complete": True,
            "aggregate_grid_16_complete": True,
            "temporal_test_calibration_separation": True,
            "temporal_test_normalization_separation": True,
            "subject_disjoint_training": True,
            "order_statistic_ranks_match": True,
            "all_15_feature_checkpoint_hashes_match": True,
            "decision_rules_recomputed": True,
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
                "# Meno-J Experiment 12 — Validation",
                "",
                "**PASS**",
                "",
                "- The 2,160-row temporal representation/calibration grid is complete.",
                "- A fresh deterministic replay exactly reproduced the scientific report without runtime warnings.",
                "- Every early/middle/late test block is disjoint from calibration and normalization data.",
                "- Subject-disjoint training and all conformal order-statistic ranks passed.",
                "- All 15 feature-checkpoint hashes and Experiment 11 prerequisite hashes match.",
                "- Frozen normalization, boundary, temperature, surface, S4, and S2 rules were recomputed.",
                "- The working-theory update matches the validated results.",
                "- All required outputs decode as UTF-8 and the credential scan passed.",
                f"- Primary decision: `{analysis['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 12 temporal readiness-surface validation: PASS")


if __name__ == "__main__":
    main()
