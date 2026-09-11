#!/usr/bin/env python3
"""Check local links in the hand-authored repository documentation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md",
    ROOT / "PROVENANCE.md",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "EXPERIMENTS.md",
    ROOT / "docs" / "HISTORICAL_FILE_MAP.md",
    ROOT / "results" / "README.md",
    ROOT / "historical" / "2026-08-04" / "RECOVERY_REPORT.md",
    ROOT / "historical" / "2026-08-04" / "figures" / "README.md",
]
LINK = re.compile(r"!?\[[^]]*]\(([^)]+)\)")


def main() -> None:
    failures: list[str] = []
    checked = 0
    for document in DOCUMENTS:
        assert document.is_file(), f"Missing documentation file: {document.relative_to(ROOT)}"
        for raw_target in LINK.findall(document.read_text(encoding="utf-8")):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            checked += 1
            resolved = (document.parent / unquote(target)).resolve()
            if not resolved.exists():
                failures.append(f"{document.relative_to(ROOT).as_posix()} -> {target}")
    if failures:
        raise SystemExit("Broken documentation links:\n" + "\n".join(failures))
    print(f"Documentation links: PASS ({checked} local links)")


if __name__ == "__main__":
    main()
