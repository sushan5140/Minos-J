#!/usr/bin/env python3
"""Fail if repository files contain likely live credentials or private keys.

Only finding categories and file paths are reported; matched values are never
printed. Placeholder examples such as ``your_openrouter_key_here`` are allowed.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cfg", ".csv", ".ini", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"
}
EXCLUDED_DIRS = {".git", ".test-deps", ".venv", "venv", "__pycache__", ".pytest_cache"}
PATTERNS = {
    "OpenRouter API key": re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    "OpenAI API key": re.compile(r"sk-(?!or-v1-)[A-Za-z0-9_-]{20,}"),
    "Anthropic API key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh(?:p|o|u|s|r)_[A-Za-z0-9]{20,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "Supabase access token": re.compile(r"sbp_[A-Za-z0-9]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "JWT": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Assigned credential": re.compile(
        r'''(?ix)(?:password|passwd|cookie|session_token|access_token|api_key)\s*[:=]\s*["']
        (?!your_|example|placeholder|redacted|<redacted>|paste_your_key_here)[^"'\s]{12,}["']'''
    ),
}


def candidate_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and not EXCLUDED_DIRS.intersection(path.parts)
        and (path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore", ".gitattributes"})
    )


def main() -> None:
    findings: dict[str, set[str]] = {category: set() for category in PATTERNS}
    scanned = 0
    for path in candidate_files():
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        scanned += 1
        relative = path.relative_to(ROOT).as_posix()
        for category, pattern in PATTERNS.items():
            if pattern.search(text):
                findings[category].add(relative)

    active = {category: paths for category, paths in findings.items() if paths}
    print(f"Credential scan: {scanned} text files")
    if active:
        for category, paths in active.items():
            print(f"{category}: {len(paths)} file(s): {', '.join(sorted(paths))}")
        raise SystemExit("Credential scan failed")
    print("Credential scan: PASS (0 likely live credentials or private keys)")


if __name__ == "__main__":
    main()
