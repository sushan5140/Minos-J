"""Inspect one WESAD subject structure using the restricted loader."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from wesad_utils import load_wesad_subject, summarize_structure  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path(r"C:\Users\DELL\Downloads\WESAD\WESAD\S2\S2.pkl"),
    )
    args = parser.parse_args()
    subject = load_wesad_subject(args.path)
    print(json.dumps(summarize_structure(subject), ensure_ascii=False))


if __name__ == "__main__":
    main()
