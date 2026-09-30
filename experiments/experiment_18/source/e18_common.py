"""Shared I/O helpers for Minos-J Experiment 18 (atomic, strict, append-only)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import uuid
from pathlib import Path
from typing import Any

E18_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = E18_DIR / "source"
TASKS_DIR = E18_DIR / "tasks"
WORK_DIR = E18_DIR / "work"          # live checkpoints / ledger (committed at M6)
RESULTS_DIR = E18_DIR / "results"
PILOT_DIR = E18_DIR / "pilot"
VALIDATION_DIR = E18_DIR / "validation"


def strict_ready(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): strict_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_ready(v) for v in value]
    raise TypeError(f"Unsupported JSON type {type(value).__name__}")


def dumps(value: Any, *, indent: int | None = None, sort_keys: bool = False) -> str:
    return json.dumps(strict_ready(value), ensure_ascii=False, allow_nan=False, indent=indent, sort_keys=sort_keys)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


class CorruptRecord(Exception):
    """A checkpoint or ledger line could not be parsed; resume must stop for review."""


def read_json_strict(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CorruptRecord(f"Unreadable checkpoint {path}: {exc}") from exc


def read_jsonl_strict(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise CorruptRecord(f"{path} line {number} is not valid JSON") from exc
    return rows


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(dumps(value, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
