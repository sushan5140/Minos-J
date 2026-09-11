"""Validate the saved WESAD acquisition-integrity artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_integrity.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_integrity.md"
EXPECTED_SUBJECTS = {
    "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11",
    "S13", "S14", "S15", "S16", "S17",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    assert JSON_OUTPUT.is_file(), f"Missing output: {JSON_OUTPUT}"
    assert MARKDOWN_OUTPUT.is_file(), f"Missing output: {MARKDOWN_OUTPUT}"
    report = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    archive = Path(report["archive"]["path"])
    root = Path(report["extraction"]["resolved_root"])
    assert archive.is_file()
    assert root.is_dir()
    assert archive.stat().st_size == report["archive"]["size_bytes"]
    assert _sha256(archive) == report["archive"]["sha256"]
    assert report["archive"]["bad_crc_entry"] is None
    assert report["archive"]["unsafe_path_count"] == 0
    assert report["extraction"]["manifest_file_count"] == report["archive"]["file_count"]
    assert not report["extraction"]["missing_files"]
    assert not report["extraction"]["size_mismatches"]
    assert not report["extraction"]["crc_mismatches"]
    assert set(report["subjects"]["found"]) == EXPECTED_SUBJECTS
    assert report["subjects"]["pickle_count"] == 15
    for row in report["file_manifest"]:
        path = root / Path(row["relative_path"])
        assert path.is_file()
        assert path.stat().st_size == row["size_bytes"]
        assert row["archive_crc32"] == row["extracted_crc32"]
        assert len(row["sha256"]) == 64
    validation = report["validation"]
    for field in (
        "archive_sha256_computed",
        "zip_crc_test_passed",
        "zip_path_traversal_check_passed",
        "extracted_sizes_match_archive",
        "extracted_crc32_matches_archive",
        "subject_inventory_passed",
    ):
        assert validation[field] is True
    assert validation["dataset_mutated"] is False
    assert validation["model_call_used"] is False
    assert validation["api_key_required"] is False
    marker = "sk-" + "or-v1"
    assert marker not in JSON_OUTPUT.read_text(encoding="utf-8")
    assert marker not in MARKDOWN_OUTPUT.read_text(encoding="utf-8")
    print("Experiment 9 WESAD integrity validation: PASS")


if __name__ == "__main__":
    main()
