"""Validate the official WESAD archive and extracted dataset without modifying them."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zlib
import zipfile


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"
CHECKPOINT_DIR = PROJECT_DIR / "work" / "experiment_9_checkpoints"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_integrity.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_9_wesad_integrity.md"
DEFAULT_ARCHIVE = Path(r"C:\Users\DELL\Downloads\WESAD.zip")
DEFAULT_DATA_DIR = Path(r"C:\Users\DELL\Downloads\WESAD")
EXPECTED_SUBJECTS = {
    "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11",
    "S13", "S14", "S15", "S16", "S17",
}


class WesadIntegrityError(RuntimeError):
    """Raised when the WESAD archive or extraction fails validation."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def crc32_and_sha256(path: Path) -> tuple[str, str]:
    crc = 0
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            crc = zlib.crc32(chunk, crc)
            digest.update(chunk)
    return f"{crc & 0xFFFFFFFF:08x}", digest.hexdigest()


def resolve_extracted_root(data_dir: Path) -> Path:
    candidates = (data_dir, data_dir / "WESAD")
    for candidate in candidates:
        if (candidate / "S2" / "S2.pkl").is_file():
            return candidate.resolve()
    raise WesadIntegrityError(
        f"Unable to locate S2/S2.pkl beneath extracted directory: {data_dir}"
    )


def load_progress(path: Path) -> dict:
    if not path.exists():
        return {"files": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}
    return value if isinstance(value, dict) and isinstance(value.get("files"), dict) else {"files": {}}


def save_progress(path: Path, progress: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(progress, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def validate_archive_and_extraction(
    archive: Path,
    data_dir: Path,
    resume: bool,
) -> dict:
    archive = archive.resolve()
    if not archive.is_file():
        raise WesadIntegrityError(f"WESAD archive is missing: {archive}")
    extracted_root = resolve_extracted_root(data_dir)
    archive_sha256 = sha256_file(archive)
    progress_path = CHECKPOINT_DIR / "wesad_extracted_manifest_progress.json"
    progress = load_progress(progress_path) if resume else {"files": {}}
    if progress.get("archive_sha256") not in (None, archive_sha256):
        progress = {"files": {}}
    progress["archive_sha256"] = archive_sha256

    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        unsafe = [
            info.filename
            for info in infos
            if PurePosixPath(info.filename).is_absolute()
            or ".." in PurePosixPath(info.filename).parts
        ]
        if unsafe:
            raise WesadIntegrityError(f"ZIP contains unsafe member paths: {unsafe[:5]}")
        bad_crc_entry = bundle.testzip()
        if bad_crc_entry is not None:
            raise WesadIntegrityError(f"ZIP CRC failure: {bad_crc_entry}")

        file_infos = [info for info in infos if not info.is_dir()]
        manifest: list[dict] = []
        missing: list[str] = []
        size_mismatches: list[dict] = []
        crc_mismatches: list[dict] = []
        archive_prefixes = {
            PurePosixPath(info.filename).parts[0]
            for info in file_infos
            if PurePosixPath(info.filename).parts
        }
        strip_prefix = "WESAD" if archive_prefixes == {"WESAD"} else None

        for index, info in enumerate(file_infos, start=1):
            parts = list(PurePosixPath(info.filename).parts)
            if strip_prefix and parts and parts[0] == strip_prefix:
                parts = parts[1:]
            relative = Path(*parts)
            extracted = extracted_root / relative
            key = relative.as_posix()
            if not extracted.is_file():
                missing.append(key)
                continue
            stat = extracted.stat()
            if stat.st_size != info.file_size:
                size_mismatches.append(
                    {"path": key, "archive_size": info.file_size, "extracted_size": stat.st_size}
                )
                continue
            cached = progress["files"].get(key, {})
            if (
                cached.get("size") == stat.st_size
                and cached.get("mtime_ns") == stat.st_mtime_ns
                and isinstance(cached.get("crc32"), str)
                and isinstance(cached.get("sha256"), str)
            ):
                extracted_crc = cached["crc32"]
                extracted_sha = cached["sha256"]
            else:
                extracted_crc, extracted_sha = crc32_and_sha256(extracted)
                progress["files"][key] = {
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "crc32": extracted_crc,
                    "sha256": extracted_sha,
                }
                save_progress(progress_path, progress)
            archive_crc = f"{info.CRC:08x}"
            if extracted_crc != archive_crc:
                crc_mismatches.append(
                    {"path": key, "archive_crc32": archive_crc, "extracted_crc32": extracted_crc}
                )
            manifest.append(
                {
                    "relative_path": key,
                    "size_bytes": stat.st_size,
                    "archive_crc32": archive_crc,
                    "extracted_crc32": extracted_crc,
                    "sha256": extracted_sha,
                }
            )
            print(f"Validated extracted file {index}/{len(file_infos)}: {key}", flush=True)

    subject_pickles = sorted(
        path.parent.name
        for path in extracted_root.glob("S*/S*.pkl")
        if path.stem == path.parent.name
    )
    actual_subjects = set(subject_pickles)
    missing_subjects = sorted(EXPECTED_SUBJECTS - actual_subjects)
    unknown_subjects = sorted(actual_subjects - EXPECTED_SUBJECTS)
    extracted_files = {
        path.relative_to(extracted_root).as_posix()
        for path in extracted_root.rglob("*")
        if path.is_file()
    }
    archived_files = {row["relative_path"] for row in manifest}
    extra_extracted_files = sorted(extracted_files - archived_files)
    status = "PASS" if not any(
        (missing, size_mismatches, crc_mismatches, missing_subjects, unknown_subjects)
    ) else "FAIL"
    report = {
        "report_name": "Meno-J Experiment 9: WESAD Acquisition and Extraction Integrity",
        "status": status,
        "archive": {
            "path": str(archive),
            "size_bytes": archive.stat().st_size,
            "sha256": archive_sha256,
            "entry_count": len(infos),
            "file_count": len(file_infos),
            "total_uncompressed_bytes": sum(info.file_size for info in infos),
            "unsafe_path_count": 0,
            "bad_crc_entry": None,
        },
        "extraction": {
            "requested_data_dir": str(data_dir.resolve()),
            "resolved_root": str(extracted_root),
            "manifest_file_count": len(manifest),
            "missing_files": missing,
            "size_mismatches": size_mismatches,
            "crc_mismatches": crc_mismatches,
            "extra_extracted_files": extra_extracted_files,
        },
        "subjects": {
            "expected": sorted(EXPECTED_SUBJECTS),
            "found": sorted(actual_subjects),
            "missing": missing_subjects,
            "unknown": unknown_subjects,
            "pickle_count": len(subject_pickles),
        },
        "file_manifest": sorted(manifest, key=lambda row: row["relative_path"]),
        "validation": {
            "archive_sha256_computed": True,
            "zip_crc_test_passed": True,
            "zip_path_traversal_check_passed": True,
            "extracted_sizes_match_archive": not size_mismatches,
            "extracted_crc32_matches_archive": not crc_mismatches,
            "subject_inventory_passed": not missing_subjects and not unknown_subjects,
            "dataset_mutated": False,
            "model_call_used": False,
            "api_key_required": False,
        },
    }
    if status != "PASS":
        raise WesadIntegrityError(
            "WESAD extraction failed integrity validation; report was not written as a PASS artifact."
        )
    return report


def render_markdown(report: dict) -> str:
    archive = report["archive"]
    extraction = report["extraction"]
    subjects = report["subjects"]
    return "\n".join(
        [
            f"# {report['report_name']}",
            "",
            f"Status: **{report['status']}**",
            "",
            "## Archive",
            "",
            f"- Path: `{archive['path']}`",
            f"- Size: {archive['size_bytes']:,} bytes",
            f"- SHA-256: `{archive['sha256']}`",
            f"- ZIP entries: {archive['entry_count']}",
            f"- Files: {archive['file_count']}",
            f"- Total uncompressed bytes: {archive['total_uncompressed_bytes']:,}",
            "- ZIP CRC: PASS",
            "- Unsafe paths: 0",
            "",
            "## Extraction",
            "",
            f"- Resolved root: `{extraction['resolved_root']}`",
            f"- Manifest files: {extraction['manifest_file_count']}",
            f"- Missing files: {len(extraction['missing_files'])}",
            f"- Size mismatches: {len(extraction['size_mismatches'])}",
            f"- CRC mismatches: {len(extraction['crc_mismatches'])}",
            f"- Extra extracted files: {len(extraction['extra_extracted_files'])}",
            "",
            "## Subject inventory",
            "",
            f"- Expected subjects: {len(subjects['expected'])}",
            f"- Found subjects: {len(subjects['found'])}",
            f"- Pickle files: {subjects['pickle_count']}",
            f"- Subject IDs: {', '.join(subjects['found'])}",
            "",
            "## Reproducibility and safety",
            "",
            "- Every extracted file was hashed with SHA-256.",
            "- Every extracted file CRC32 was compared with the official ZIP member CRC.",
            "- The extracted dataset was read-only during validation.",
            "- No model call or API key was used.",
            "- UTF-8 was used for report output.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    report = validate_archive_and_extraction(args.archive, args.data_dir, args.resume)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    print(f"WESAD acquisition integrity: {report['status']}")
    print(f"Archive SHA-256: {report['archive']['sha256']}")


if __name__ == "__main__":
    main()
