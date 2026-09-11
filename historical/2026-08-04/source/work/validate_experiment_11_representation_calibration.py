"""Independently replay and validate Meno-J Experiment 11 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_11_representation_calibration as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_11_representation_calibration.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_11_representation_calibration.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_11_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_11_reproducibility_summary.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_11_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_11_working_theory_update.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_11_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_11_validation.md"


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


def _find(rows: list[dict], field: str, value: str) -> dict:
    matches = [row for row in rows if row[field] == value]
    assert len(matches) == 1, f"Expected one {field}={value} row."
    return matches[0]


def main() -> None:
    required = (REPORT_JSON, REPORT_MD, REPRO_JSON, REPRO_MD, THEORY_JSON, THEORY_MD)
    for path in required:
        assert path.is_file(), f"Missing Experiment 11 artifact: {path}"
        path.read_text(encoding="utf-8")

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    assert REPORT_MD.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["prerequisites"]["experiment_10_report_sha256"] == _sha256(
        experiment.EXP10_REPORT
    )
    assert saved["prerequisites"]["experiment_10_validation_sha256"] == _sha256(
        experiment.EXP10_VALIDATION
    )

    checkpoint = _read_json(experiment.CHECKPOINT)
    assert checkpoint["fingerprint"] == experiment._fingerprint(_read_json(experiment.EXP10_REPORT))
    assert checkpoint["fingerprint"]["runner_sha256"] == _sha256(
        PROJECT_DIR / "run_experiment_11_representation_calibration.py"
    )

    replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Independent deterministic replay differs from saved report."
    assert len(replayed["calibration_frontier_rows"]) == 270
    assert len(replayed["representation_rows"]) == 450
    assert len(replayed["calibration_frontier_aggregates"]) == 6
    assert len(replayed["representation_aggregates"]) == 10
    assert replayed["continuity_with_experiment_10"] == {
        "status": "PASS",
        "rows_checked": 90,
        "mismatch_count": 0,
    }

    k18_rows = [
        row for row in replayed["calibration_frontier_rows"]
        if row["method_id"] == "personal_k18"
    ]
    k19_rows = [
        row for row in replayed["calibration_frontier_rows"]
        if row["method_id"] == "personal_k19"
    ]
    assert len(k18_rows) == len(k19_rows) == 45
    assert all(row["conformal_rank"] == 18 for row in k18_rows)
    assert all(row["conformal_rank"] == 18 for row in k19_rows)
    assert replayed["analysis"]["primary_decision"] == "SUPPORTED_RIVALS_R2_AND_R3"
    assert replayed["analysis"]["calibration_order_statistic"]["supported"] is False
    assert replayed["analysis"]["subject_baseline_normalization"]["general_supported"] is True
    assert replayed["analysis"]["subject_baseline_normalization"]["s2_s4_supported"] is False
    assert replayed["analysis"]["sensor_ablation"]["supported"] is True
    assert replayed["analysis"]["classifier_representation"]["supported"] is False

    theory = _read_json(THEORY_JSON)
    assert theory["primary_decision"] == replayed["analysis"]["primary_decision"]
    updates = {row["claim"]: row for row in theory["working_theory_updates"]}
    assert len(updates) == 5
    order = updates[
        "Crossing the alpha=0.10 order-statistic boundary from 18 to 19 personal examples is by itself a safe calibration-readiness jump."
    ]
    assert order["evidence"]["worst_subject_coverage_change"] == replayed["analysis"][
        "calibration_order_statistic"
    ]["worst_subject_coverage_change"]
    baseline = _find(replayed["representation_aggregates"], "arm_id", "lda_raw_all")
    normalized = _find(
        replayed["representation_aggregates"], "arm_id", "lda_subject_robust_normalized"
    )
    baseline_claim = updates[
        "Subject baseline mismatch is a material source of poor wearable-state representation."
    ]
    assert baseline_claim["evidence"]["raw_full_set_frequency"] == baseline[
        "mean_full_set_frequency"
    ]
    assert baseline_claim["evidence"]["normalized_full_set_frequency"] == normalized[
        "mean_full_set_frequency"
    ]

    for subject, expected_hash in replayed["prerequisites"]["feature_checkpoint_hashes"].items():
        feature_path = experiment.exp10.FEATURE_DIR / f"{subject}.npz"
        assert feature_path.is_file() and _sha256(feature_path) == expected_hash

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    theory["update_status"] = "VALIDATED"
    theory["validation"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    experiment._atomic_json(THEORY_JSON, theory)
    theory_markdown = THEORY_MD.read_text(encoding="utf-8")
    theory_markdown = theory_markdown.replace(
        "Independent exact replay: **pending**.",
        "Independent exact replay: **PASS**.",
    )
    THEORY_MD.write_text(theory_markdown, encoding="utf-8")

    reproducibility = experiment.reproducibility_summary(replayed)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(REPORT_JSON)
    reproducibility["markdown_report_sha256"] = _sha256(REPORT_MD)
    reproducibility["runner_sha256"] = _sha256(
        PROJECT_DIR / "run_experiment_11_representation_calibration.py"
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
            "frontier_grid_270_complete": True,
            "representation_grid_450_complete": True,
            "experiment_10_k9_k12_exact_continuity_90_rows": True,
            "order_statistic_boundary_matches_protocol": True,
            "heldout_subject_and_test_window_leakage_absent": True,
            "all_15_feature_checkpoint_hashes_match": True,
            "working_theory_update_matches_results": True,
            "credential_scan_passes": True,
        },
        "primary_decision": replayed["analysis"]["primary_decision"],
        "scientific_report_sha256": _sha256(REPORT_JSON),
        "reproducibility_summary_sha256": _sha256(REPRO_JSON),
        "working_theory_sha256": _sha256(THEORY_JSON),
    }
    experiment._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 11 — Validation",
                "",
                "**PASS**",
                "",
                "- The 270-row calibration frontier and 450-row representation grid are complete.",
                "- A fresh deterministic replay exactly reproduced the saved scientific report.",
                "- All 90 Experiment 10 k=9/k=12 continuity rows match exactly.",
                "- Subject-disjoint folds and personal test/calibration separation passed.",
                "- The preregistered order-statistic, representation, sensor, and model rules were enforced.",
                "- All 15 validated feature-checkpoint hashes match.",
                "- The working-theory update matches the scientific results.",
                "- All required outputs decode as UTF-8 and the credential scan passed.",
                f"- Primary decision: `{validation['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 11 representation/calibration validation: PASS")


if __name__ == "__main__":
    main()
