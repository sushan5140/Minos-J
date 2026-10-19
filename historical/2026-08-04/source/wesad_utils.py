"""Safe, deterministic utilities for the WESAD real-data experiment."""

from __future__ import annotations

import builtins
import codecs
import pickle
from pathlib import Path
from typing import Any

import numpy as np


class RestrictedWesadUnpickler(pickle.Unpickler):
    """Load the official NumPy-based WESAD pickle without arbitrary globals."""

    _ALLOWED: dict[tuple[str, str], Any] = {
        ("numpy.core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
        ("numpy._core.multiarray", "_reconstruct"): np.core.multiarray._reconstruct,
        ("numpy.core.multiarray", "scalar"): np.core.multiarray.scalar,
        ("numpy._core.multiarray", "scalar"): np.core.multiarray.scalar,
        ("numpy", "ndarray"): np.ndarray,
        ("numpy", "dtype"): np.dtype,
        ("_codecs", "encode"): codecs.encode,
        ("builtins", "set"): builtins.set,
        ("builtins", "slice"): builtins.slice,
        ("__builtin__", "set"): builtins.set,
        ("__builtin__", "slice"): builtins.slice,
    }

    def find_class(self, module: str, name: str) -> Any:
        value = self._ALLOWED.get((module, name))
        if value is None:
            raise pickle.UnpicklingError(
                f"Disallowed global in WESAD pickle: {module}.{name}"
            )
        return value


def load_wesad_subject(path: Path) -> dict[str, Any]:
    """Load one verified official WESAD subject pickle with a restricted loader."""
    with path.open("rb") as handle:
        value = RestrictedWesadUnpickler(
            handle,
            fix_imports=True,
            encoding="latin1",
        ).load()
    if not isinstance(value, dict):
        raise ValueError(f"WESAD subject pickle is not a dictionary: {path}")
    return value


def summarize_structure(value: Any) -> Any:
    """Return JSON-safe shape/type metadata without serializing signal values."""
    if isinstance(value, dict):
        return {str(key): summarize_structure(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        result: dict[str, Any] = {
            "type": "ndarray",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
        }
        if value.size and value.ndim == 1 and value.size < 100_000_000:
            unique, counts = np.unique(value, return_counts=True)
            if len(unique) <= 20:
                result["value_counts"] = {
                    str(int(key) if np.issubdtype(unique.dtype, np.integer) else float(key)): int(count)
                    for key, count in zip(unique, counts)
                }
        return result
    return {"type": type(value).__name__, "value": str(value)[:200]}
