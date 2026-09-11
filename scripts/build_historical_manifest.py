#!/usr/bin/env python3
"""Build the public-safe historical artifact manifest.

Only recovered source, output, JSON-checkpoint, and hash-log trees are included.
The recovery report and manifest itself are intentionally excluded.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "historical" / "2026-08-04"
MANIFEST = HISTORICAL / "MANIFEST.sha256"
INCLUDED_DIRS = ("source", "outputs", "checkpoints", "logs")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_lines() -> list[str]:
    files = sorted(
        (path for name in INCLUDED_DIRS for path in (HISTORICAL / name).rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(HISTORICAL).as_posix(),
    )
    return [f"{sha256(path)}  {path.relative_to(HISTORICAL).as_posix()}" for path in files]


def main() -> None:
    lines = manifest_lines()
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Historical public-safe manifest: {len(lines)} files")


if __name__ == "__main__":
    main()
