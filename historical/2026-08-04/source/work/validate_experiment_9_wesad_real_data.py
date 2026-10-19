"""Independently replay and validate Experiment 9 real-data artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_experiment_9_wesad_real_data as experiment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
REPORT_JSON = OUTPUT_DIR / "meno_j_experiment_9_wesad_real_data.json"
REPORT_MD = OUTPUT_DIR / "meno_j_experiment_9_wesad_real_data.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_experiment_9_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_experiment_9_reproducibility_summary.md"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_experiment_9_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_experiment_9_validation.md"


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
    excluded_parts = {".git", "vendor", "__pycache__"}
    for root in (PROJECT_DIR, OUTPUT_DIR, PROJECT_DIR / "work"):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or excluded_parts.intersection(path.parts):
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
    for path in (REPORT_JSON, REPORT_MD, REPRO_JSON, REPRO_MD):
        assert path.is_file(), f"Missing required Experiment 9 output: {path}"

    saved = experiment.validate_report(_read_json(REPORT_JSON))
    saved_markdown = REPORT_MD.read_text(encoding="utf-8")
    assert saved_markdown == experiment.render_markdown(saved), "Saved Markdown does not match saved JSON."

    replayed = experiment.build_report()
    assert replayed == saved, "Independent replay differs from the saved scientific report."
    assert len(replayed["subject_feature_summary"]) == 15
    assert replayed["total_window_count"] == 535
    assert len(replayed["fold_results"]) == 405
    assert len(replayed["aggregate_results"]) == 9
    assert replayed["analysis"]["primary_transfer_decision"] in {
        "SYNTHETIC_SAFEST_PAIR_TRANSFERS",
        "SYNTHETIC_SAFEST_PAIR_DOES_NOT_TRANSFER",
    }

    for row in replayed["subject_feature_summary"]:
        checkpoint = Path(row["checkpoint_path"])
        assert checkpoint.is_file()
        assert _sha256(checkpoint) == row["checkpoint_sha256"]
    assert _sha256(Path(replayed["source_integrity"]["path"])) == replayed["source_integrity"]["sha256"]
    assert _sha256(Path(replayed["preregistered_protocol"]["path"])) == replayed["preregistered_protocol"]["sha256"]

    credential_matches = _credential_scan()
    assert not credential_matches, f"Credential marker found outside .env: {credential_matches}"

    reproducibility = experiment.reproducibility_summary(replayed)
    reproducibility["validation_status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["scientific_report_sha256"] = _sha256(REPORT_JSON)
    reproducibility["markdown_report_sha256"] = _sha256(REPORT_MD)
    reproducibility["validator"] = str(Path(__file__).resolve())
    REPRO_JSON.write_text(
        json.dumps(reproducibility, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    repro_markdown = experiment.render_reproducibility_markdown(reproducibility)
    repro_markdown = repro_markdown.replace(
        "- Independent replay: pending",
        "- Independent exact replay: PASS\n"
        f"- Scientific-report SHA-256: `{reproducibility['scientific_report_sha256']}`\n"
        f"- Markdown-report SHA-256: `{reproducibility['markdown_report_sha256']}`",
    )
    REPRO_MD.write_text(repro_markdown, encoding="utf-8")

    validation = {
        "experiment_name": replayed["experiment_name"],
        "status": "PASS",
        "checks": {
            "required_outputs_exist": True,
            "saved_json_schema_and_invariants_pass": True,
            "markdown_matches_json": True,
            "independent_exact_replay_matches": True,
            "subject_count_is_15": True,
            "window_count_is_535": True,
            "fold_result_count_is_405": True,
            "aggregate_method_count_is_9": True,
            "source_hashes_match": True,
            "feature_checkpoint_hashes_match": True,
            "credential_scan_passes": True,
        },
        "primary_transfer_decision": replayed["analysis"]["primary_transfer_decision"],
        "scientific_report_sha256": _sha256(REPORT_JSON),
        "reproducibility_summary_sha256": _sha256(REPRO_JSON),
    }
    VALIDATION_JSON.write_text(
        json.dumps(validation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    VALIDATION_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 9 — Validation",
                "",
                "**PASS**",
                "",
                "- The saved scientific JSON passed its schema and invariant checks.",
                "- The saved Markdown is an exact rendering of the scientific JSON.",
                "- A deterministic independent replay exactly reproduced the saved report.",
                "- All 15 feature-checkpoint hashes and both prerequisite artifact hashes match.",
                "- The credential scan passed.",
                f"- Primary transfer decision: `{validation['primary_transfer_decision']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 9 WESAD real-data validation: PASS")


if __name__ == "__main__":
    main()
