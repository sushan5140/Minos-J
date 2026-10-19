"""Independently replay and validate Experiment 10 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_10_calibration_bridge as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_10_calibration_bridge.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_10_calibration_bridge.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_10_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_10_reproducibility_summary.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_10_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_10_validation.md"
THEORY_JSON = OUTPUT_DIR / "meno_j_experiment_10_working_theory_update.json"
THEORY_MD = OUTPUT_DIR / "meno_j_experiment_10_working_theory_update.md"


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
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if marker in text:
            matches.append(str(path.resolve()))
    return sorted(set(matches))


def main() -> None:
    for path in (REPORT_JSON, REPORT_MD, REPRO_JSON, REPRO_MD, THEORY_JSON, THEORY_MD):
        assert path.is_file(), f"Missing Experiment 10 artifact: {path}"

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    assert REPORT_MD.read_text(encoding="utf-8") == experiment.render_markdown(saved)
    assert saved["preregistered_protocol"]["sha256"] == _sha256(experiment.PROTOCOL_PATH)
    assert saved["experiment_9_checkpoint_source"]["sha256"] == _sha256(experiment.EXP9_REPORT)
    assert saved["experiment_9_checkpoint_source"]["validation_sha256"] == _sha256(
        experiment.EXP9_VALIDATION
    )

    replayed = experiment.build_report(use_checkpoint=False)
    assert replayed == saved, "Independent deterministic replay differs from saved report."
    assert len(replayed["fold_results"]) == 315
    assert len(replayed["compatibility_rows"]) == 180
    assert len(replayed["aggregate_results"]) == 7
    assert len(replayed["subject_diagnostics"]) == 15

    boundary = replayed["analysis"]["finite_sample_boundary"]
    for method in ("personal_k3", "personal_k6"):
        assert boundary[method]["finite_threshold_fraction"] == 0.0
        assert boundary[method]["mean_full_set_frequency"] == 1.0
    for method in ("personal_k9", "personal_k12"):
        assert boundary[method]["finite_threshold_fraction"] == 1.0

    theory = _read_json(THEORY_JSON)
    assert theory["primary_decision"] == replayed["analysis"]["primary_decision"]
    assert theory["validation"] == "PASS_INDEPENDENT_EXACT_REPLAY"
    theory_updates = {row["claim"]: row for row in theory["working_theory_updates"]}
    assert len(theory_updates) == 4
    s2_s4 = replayed["analysis"]["s2_s4_personal_repair"]["subjects"]
    repair_claim = theory_updates[
        "Twelve personal calibration windows provide an informative repair for S2 and S4."
    ]
    assert repair_claim["status"] == "NOT_SUPPORTED"
    assert repair_claim["evidence"]["S2"]["coverage_change"] == s2_s4["S2"]["coverage_change"]
    assert repair_claim["evidence"]["S4"]["coverage_change"] == s2_s4["S4"]["coverage_change"]

    for subject, expected_hash in replayed["experiment_9_checkpoint_source"][
        "feature_checkpoint_hashes"
    ].items():
        path = experiment.FEATURE_DIR / f"{subject}.npz"
        assert path.is_file() and _sha256(path) == expected_hash

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    reproducibility = experiment.reproducibility_summary(replayed)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(REPORT_JSON)
    reproducibility["markdown_report_sha256"] = _sha256(REPORT_MD)
    reproducibility["validator"] = str(Path(__file__).resolve())
    experiment._atomic_json(REPRO_JSON, reproducibility)
    repro_markdown = experiment.render_reproducibility_markdown(reproducibility).replace(
        "- Independent exact replay: pending",
        "- Independent exact replay: PASS\n"
        f"- Scientific-report SHA-256: `{reproducibility['scientific_report_sha256']}`\n"
        f"- Markdown-report SHA-256: `{reproducibility['markdown_report_sha256']}`",
    )
    REPRO_MD.write_text(repro_markdown, encoding="utf-8")

    validation = {
        "experiment_name": experiment.EXPERIMENT_NAME,
        "status": "PASS",
        "checks": {
            "required_outputs_exist": True,
            "saved_schema_and_invariants_pass": True,
            "markdown_matches_json": True,
            "independent_exact_replay_matches": True,
            "fold_grid_315_complete": True,
            "compatibility_grid_180_complete": True,
            "personal_test_calibration_disjoint": True,
            "finite_sample_boundary_matches_protocol": True,
            "experiment_9_source_hashes_match": True,
            "all_15_feature_checkpoint_hashes_match": True,
            "working_theory_update_matches_results": True,
            "credential_scan_passes": True,
        },
        "primary_decision": replayed["analysis"]["primary_decision"],
        "scientific_report_sha256": _sha256(REPORT_JSON),
        "reproducibility_summary_sha256": _sha256(REPRO_JSON),
    }
    experiment._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 10 — Validation",
                "",
                "**PASS**",
                "",
                "- The 315-fold method grid and 180-row compatibility grid are complete.",
                "- Personal test and calibration windows are disjoint.",
                "- The preregistered finite-sample boundary was enforced.",
                "- A fresh deterministic replay exactly reproduced the saved scientific report.",
                "- Experiment 9 prerequisites and all 15 feature-checkpoint hashes match.",
                "- The working-theory update matches the validated results.",
                "- The credential scan passed.",
                f"- Primary decision: `{validation['primary_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 10 calibration bridge validation: PASS")


if __name__ == "__main__":
    main()
