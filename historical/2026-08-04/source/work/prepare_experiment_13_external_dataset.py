"""Integrity-check and safely extract the official Experiment 13 dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import zipfile


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_DIR = PROJECT_DIR / "work" / "external" / "wearable_device_dataset"
CANONICAL_ARCHIVE = TARGET_DIR / "wearable-device-dataset-1.0.1.zip"
# Keep the extraction root deliberately short. The official ZIP has a long
# common outer directory, and retaining it under the already-long workspace
# path exceeds the legacy Windows MAX_PATH limit.
EXTRACTED_DIR = PROJECT_DIR / "work" / "e13_data"
INTEGRITY_JSON = OUTPUT_DIR / "meno_j_experiment_13_dataset_integrity.json"
INTEGRITY_MD = OUTPUT_DIR / "meno_j_experiment_13_dataset_integrity.md"
DOWNLOADS_DIR = Path.home() / "Downloads"
MIN_ARCHIVE_BYTES = 60_000_000
MAX_ARCHIVE_BYTES = 100_000_000
EXPECTED_SUFFIXES = (
    "README.txt",
    "LICENSE.txt",
    "data_constraints.txt",
    "Data_Dictionary.csv",
    "Stress_Level_v1.csv",
    "Stress_Level_v2.csv",
)
SENSORS = ("ACC.csv", "EDA.csv", "TEMP.csv", "tags.csv")


class DatasetIntegrityError(RuntimeError):
    """Raised when the external archive is absent, incomplete, or unsafe."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _find_archive(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise DatasetIntegrityError(f"Archive does not exist: {path}")
        return path
    candidates = [
        path
        for path in DOWNLOADS_DIR.glob("*.zip")
        if "wearable" in path.name.lower() and "dataset" in path.name.lower()
    ]
    if CANONICAL_ARCHIVE.is_file():
        candidates.append(CANONICAL_ARCHIVE)
    if len(candidates) != 1:
        names = [str(path) for path in candidates]
        raise DatasetIntegrityError(
            "Expected exactly one completed wearable-dataset ZIP in Downloads "
            f"or the canonical target; found {names}. Partial .crdownload files are rejected."
        )
    return candidates[0].resolve()


def _validate_member_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", normalized):
        raise DatasetIntegrityError(f"Unsafe archive member path: {name}")


def _inventory(archive: Path) -> dict:
    size = archive.stat().st_size
    if not MIN_ARCHIVE_BYTES <= size <= MAX_ARCHIVE_BYTES:
        raise DatasetIntegrityError(
            f"Archive size {size} bytes is outside the expected completed range."
        )
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            for member in members:
                _validate_member_name(member.filename)
            bad_member = bundle.testzip()
            if bad_member is not None:
                raise DatasetIntegrityError(f"ZIP CRC failure: {bad_member}")
    except (zipfile.BadZipFile, OSError) as exc:
        raise DatasetIntegrityError(f"Archive is not a valid complete ZIP: {archive}") from exc
    names = [member.filename.replace("\\", "/") for member in members]
    missing = [suffix for suffix in EXPECTED_SUFFIXES if not any(name.endswith(suffix) for name in names)]
    if missing:
        raise DatasetIntegrityError(f"Expected metadata files are missing: {missing}")
    stress_subjects: dict[str, set[str]] = {}
    for name in names:
        match = re.search(r"(?:^|/)Wearable_Dataset/STRESS/([^/]+)/([^/]+)$", name)
        if match:
            stress_subjects.setdefault(match.group(1), set()).add(match.group(2))
    complete_sensor_folders = sorted(
        subject for subject, files in stress_subjects.items() if set(SENSORS).issubset(files)
    )
    if len(stress_subjects) < 36 or len(complete_sensor_folders) < 33:
        raise DatasetIntegrityError(
            "Stress-session inventory is smaller than the official release contract: "
            f"{len(stress_subjects)} folders, {len(complete_sensor_folders)} complete sensor folders."
        )
    return {
        "archive_path": str(archive),
        "archive_size_bytes": size,
        "archive_sha256": _sha256(archive),
        "member_count": len(members),
        "uncompressed_size_bytes": int(sum(member.file_size for member in members)),
        "zip_crc_test": "PASS",
        "unsafe_member_count": 0,
        "stress_subject_folder_count": len(stress_subjects),
        "stress_complete_sensor_folder_count": len(complete_sensor_folders),
        "stress_subject_folders": sorted(stress_subjects),
        "complete_sensor_folders": complete_sensor_folders,
    }


def _copy_canonical(source: Path, expected_sha256: str) -> Path:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if CANONICAL_ARCHIVE.is_file():
        if _sha256(CANONICAL_ARCHIVE) != expected_sha256:
            raise DatasetIntegrityError(
                "A different canonical archive already exists; refusing to overwrite it."
            )
        return CANONICAL_ARCHIVE
    temporary = CANONICAL_ARCHIVE.with_suffix(".zip.tmp")
    if temporary.exists():
        raise DatasetIntegrityError(
            f"A previous temporary copy exists and was preserved: {temporary}"
        )
    shutil.copyfile(source, temporary)
    if _sha256(temporary) != expected_sha256:
        raise DatasetIntegrityError("Copied archive hash does not match its source.")
    temporary.replace(CANONICAL_ARCHIVE)
    return CANONICAL_ARCHIVE


def _safe_extract(archive: Path) -> str:
    if EXTRACTED_DIR.exists():
        raise DatasetIntegrityError(
            f"Extraction target already exists; refusing to overwrite: {EXTRACTED_DIR}"
        )
    staging = EXTRACTED_DIR.with_name(EXTRACTED_DIR.name + ".staging")
    if staging.exists():
        raise DatasetIntegrityError(
            f"A previous staging directory was preserved: {staging}"
        )
    staging.mkdir(parents=True)
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = [
                PurePosixPath(member.filename.replace("\\", "/"))
                for member in bundle.infolist()
                if member.filename
            ]
            roots = {path.parts[0] for path in names if path.parts}
            if len(roots) != 1:
                raise DatasetIntegrityError(
                    f"Expected one common archive root, found: {sorted(roots)}"
                )
            common_root = next(iter(roots))
            for member in bundle.infolist():
                _validate_member_name(member.filename)
                source_path = PurePosixPath(member.filename.replace("\\", "/"))
                relative_parts = source_path.parts[1:]
                if not relative_parts:
                    continue
                destination = staging.joinpath(*relative_parts).resolve()
                if staging.resolve() not in destination.parents and destination != staging.resolve():
                    raise DatasetIntegrityError(f"Extraction escaped staging: {member.filename}")
                unix_mode = (member.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise DatasetIntegrityError(f"Symbolic links are not allowed: {member.filename}")
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
        staging.replace(EXTRACTED_DIR)
        return common_root
    except Exception:
        # Preserve staging for diagnosis; never replace it with a partial final tree.
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", help="Path to the completed official ZIP")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    source = _find_archive(args.archive)
    inventory = _inventory(source)
    canonical = _copy_canonical(source, inventory["archive_sha256"])
    stripped_prefix = None
    if not args.validate_only and not EXTRACTED_DIR.exists():
        stripped_prefix = _safe_extract(canonical)
    inventory.update(
        {
            "experiment_name": "Meno-J Experiment 13: Independent Wearable-Dataset Replication",
            "status": "PASS",
            "source_url": "https://physionet.org/content/wearable-device-dataset/get-zip/1.0.1/",
            "doi": "10.13026/he0v-tf17",
            "license": "Open Data Commons Attribution License v1.0",
            "canonical_archive_path": str(CANONICAL_ARCHIVE.resolve()),
            "extracted_path": str(EXTRACTED_DIR.resolve()) if EXTRACTED_DIR.exists() else None,
            "extraction_completed": EXTRACTED_DIR.exists(),
            "stripped_common_archive_prefix": stripped_prefix,
            "failed_long_path_staging_preserved": str(
                (TARGET_DIR / "extracted.staging").resolve()
            ) if (TARGET_DIR / "extracted.staging").exists() else None,
            "raw_dataset_mutated": False,
        }
    )
    _atomic_json(INTEGRITY_JSON, inventory)
    INTEGRITY_MD.write_text(
        "\n".join(
            [
                "# Meno-J Experiment 13 — Dataset Integrity",
                "",
                "**PASS**",
                "",
                f"- Archive: `{inventory['canonical_archive_path']}`",
                f"- Size: {inventory['archive_size_bytes']:,} bytes",
                f"- SHA-256: `{inventory['archive_sha256']}`",
                f"- ZIP members: {inventory['member_count']}",
                f"- Uncompressed bytes: {inventory['uncompressed_size_bytes']:,}",
                f"- Stress subject folders: {inventory['stress_subject_folder_count']}",
                f"- Complete stress sensor folders: {inventory['stress_complete_sensor_folder_count']}",
                f"- Extraction complete: {inventory['extraction_completed']}",
                "- ZIP CRC and safe-path checks: PASS",
                "- License: Open Data Commons Attribution License v1.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Experiment 13 external dataset integrity: PASS")


if __name__ == "__main__":
    main()
