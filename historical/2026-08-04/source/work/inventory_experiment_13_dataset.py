"""Build a pre-outcome inventory for Experiment 13 without fitting models."""

from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_DIR / "work" / "e13_data"
STRESS_ROOT = DATA_ROOT / "Wearable_Dataset" / "STRESS"
INTEGRITY_JSON = PROJECT_DIR / "outputs" / "meno_j_experiment_13_dataset_integrity.json"
INVENTORY_JSON = PROJECT_DIR / "outputs" / "meno_j_experiment_13_dataset_inventory.json"
INVENTORY_MD = PROJECT_DIR / "outputs" / "meno_j_experiment_13_dataset_inventory.md"
EXCLUSIONS = {
    "S02": "duplicated stress signals documented by the dataset authors",
    "f07": "covered PPG and temperature sensors documented by the dataset authors",
    "f14_a": "split f14 stress recording; primary complete-file cohort excludes both parts",
    "f14_b": "split f14 stress recording; primary complete-file cohort excludes both parts",
}
SENSORS = {"EDA.csv": 4.0, "TEMP.csv": 4.0, "ACC.csv": 32.0}
CANDIDATE_WINDOWS_SECONDS = (10, 15, 30, 60)
EDGE_TRIM_SECONDS = 5.0


class InventoryError(RuntimeError):
    """Raised when the extracted dataset violates its inventory contract."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InventoryError(f"Expected JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.strip())


def _signal_metadata(path: Path, expected_rate: float) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rates = next(reader)
        row_count = sum(1 for _ in reader)
    starts = [_parse_timestamp(value) for value in header]
    numeric_rates = [float(value) for value in rates]
    if len(set(starts)) != 1 or any(rate != expected_rate for rate in numeric_rates):
        raise InventoryError(f"Signal header/rate mismatch: {path}")
    if path.name == "ACC.csv" and (len(header) != 3 or len(numeric_rates) != 3):
        raise InventoryError(f"ACC dimensionality mismatch: {path}")
    if path.name != "ACC.csv" and (len(header) != 1 or len(numeric_rates) != 1):
        raise InventoryError(f"Scalar signal dimensionality mismatch: {path}")
    return {
        "start": starts[0],
        "sampling_rate_hz": expected_rate,
        "sample_count": row_count,
        "duration_seconds": float(row_count / expected_rate),
        "sha256": _sha256(path),
    }


def _read_tags(path: Path) -> list[datetime]:
    tags: list[datetime] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            if row and row[0].strip():
                tags.append(_parse_timestamp(row[0]))
    if tags != sorted(tags) or len(set(tags)) != len(tags):
        raise InventoryError(f"Tags are not strictly ordered: {path}")
    return tags


def _intervals(
    subject: str,
    signal_start: datetime,
    tags: list[datetime],
) -> list[dict[str, Any]]:
    if subject.startswith("S"):
        # The release notebook says "12 tags", but every extracted V1
        # stress file contains 13. Its plotting code uses the first 12
        # protocol markers and leaves the final recording-end marker unused.
        if len(tags) != 13:
            raise InventoryError(f"V1 subject {subject} does not have 13 released tags.")
        definitions = [
            ("baseline", "non_stress", 0, 1),
            ("stroop", "stress", 2, 3),
            ("first_rest", "non_stress", 3, 4),
            ("tmct", "stress", 4, 5),
            ("second_rest", "non_stress", 5, 6),
            ("real_opinion", "stress", 6, 7),
            ("opposite_opinion", "stress", 8, 9),
            ("subtract", "stress", 10, 11),
        ]
        pairs = [(name, label, tags[left], tags[right]) for name, label, left, right in definitions]
    else:
        if len(tags) != 9:
            raise InventoryError(f"V2 subject {subject} does not have 9 tags.")
        pairs = [
            ("baseline", "non_stress", signal_start, tags[0]),
            ("tmct", "stress", tags[1], tags[2]),
            ("first_rest", "non_stress", tags[2], tags[3]),
            ("real_opinion", "stress", tags[3], tags[4]),
            ("opposite_opinion", "stress", tags[5], tags[6]),
            ("second_rest", "non_stress", tags[6], tags[7]),
            ("subtract", "stress", tags[7], tags[8]),
        ]
    intervals = []
    for name, label, start, end in pairs:
        duration = (end - start).total_seconds()
        if duration <= 0:
            raise InventoryError(f"Non-positive {subject}/{name} interval.")
        intervals.append(
            {
                "stage": name,
                "label": label,
                "start_iso": start.isoformat(sep=" "),
                "end_iso": end.isoformat(sep=" "),
                "duration_seconds": duration,
            }
        )
    return intervals


def _window_counts(intervals: list[dict[str, Any]], window_seconds: int) -> dict[str, int]:
    counts = {"stress": 0, "non_stress": 0}
    for interval in intervals:
        usable = max(0.0, interval["duration_seconds"] - 2 * EDGE_TRIM_SECONDS)
        counts[interval["label"]] += math.floor(usable / window_seconds)
    return counts


def build_inventory() -> dict[str, Any]:
    integrity = _read_json(INTEGRITY_JSON)
    if integrity.get("status") != "PASS" or not integrity.get("extraction_completed"):
        raise InventoryError("Experiment 13 integrity/extraction gate has not passed.")
    if _sha256(Path(integrity["canonical_archive_path"])) != integrity["archive_sha256"]:
        raise InventoryError("Canonical archive hash changed after integrity validation.")
    folders = sorted(path.name for path in STRESS_ROOT.iterdir() if path.is_dir())
    if set(folders) != set(integrity["stress_subject_folders"]):
        raise InventoryError("Extracted stress folder inventory differs from the ZIP inventory.")

    subjects: list[dict[str, Any]] = []
    for subject in folders:
        folder = STRESS_ROOT / subject
        sensor_metadata = {
            name.removesuffix(".csv"): _signal_metadata(folder / name, rate)
            for name, rate in SENSORS.items()
        }
        starts = {metadata["start"] for metadata in sensor_metadata.values()}
        if len(starts) != 1:
            raise InventoryError(f"Shared sensor start times differ for {subject}.")
        signal_start = next(iter(starts))
        common_end_seconds = min(
            metadata["duration_seconds"] for metadata in sensor_metadata.values()
        )
        tags = _read_tags(folder / "tags.csv")
        split_f14 = subject in {"f14_a", "f14_b"}
        intervals = [] if split_f14 else _intervals(subject, signal_start, tags)
        if tags and max((tag - signal_start).total_seconds() for tag in tags) > common_end_seconds + 1.0:
            raise InventoryError(f"Tags exceed common signal duration for {subject}.")
        candidate_counts = {
            str(seconds): _window_counts(intervals, seconds)
            for seconds in CANDIDATE_WINDOWS_SECONDS
        }
        subjects.append(
            {
                "subject_folder": subject,
                "canonical_subject_id": "f14" if subject.startswith("f14_") else subject,
                "protocol_version": "V1" if subject.startswith("S") else "V2",
                "primary_included": subject not in EXCLUSIONS,
                "exclusion_reason": EXCLUSIONS.get(subject, ""),
                "tag_count": len(tags),
                "tag_sha256": _sha256(folder / "tags.csv"),
                "common_signal_start": signal_start.isoformat(sep=" "),
                "common_signal_duration_seconds": common_end_seconds,
                "signals": {
                    name: {
                        key: value.isoformat(sep=" ") if isinstance(value, datetime) else value
                        for key, value in metadata.items()
                    }
                    for name, metadata in sensor_metadata.items()
                },
                "labeled_intervals": intervals,
                "candidate_window_counts_after_5s_edge_trim": candidate_counts,
            }
        )

    included = [row for row in subjects if row["primary_included"]]
    cohort_counts = {
        str(seconds): {
            label: {
                "total": int(
                    sum(
                        row["candidate_window_counts_after_5s_edge_trim"][str(seconds)][label]
                        for row in included
                    )
                ),
                "minimum_per_subject": int(
                    min(
                        row["candidate_window_counts_after_5s_edge_trim"][str(seconds)][label]
                        for row in included
                    )
                ),
                "maximum_per_subject": int(
                    max(
                        row["candidate_window_counts_after_5s_edge_trim"][str(seconds)][label]
                        for row in included
                    )
                ),
            }
            for label in ("non_stress", "stress")
        }
        for seconds in CANDIDATE_WINDOWS_SECONDS
    }
    return {
        "experiment_name": "Meno-J Experiment 13: Independent Wearable-Dataset Replication",
        "inventory_status": "PASS_PRE_OUTCOME",
        "integrity_report_path": str(INTEGRITY_JSON.resolve()),
        "integrity_report_sha256": _sha256(INTEGRITY_JSON),
        "archive_sha256": integrity["archive_sha256"],
        "stress_folder_count": len(subjects),
        "primary_subject_count": len(included),
        "primary_subjects": [row["subject_folder"] for row in included],
        "excluded_folders": EXCLUSIONS,
        "shared_signals": list(SENSORS),
        "edge_trim_seconds": EDGE_TRIM_SECONDS,
        "candidate_window_counts": cohort_counts,
        "subject_inventory": subjects,
        "scientific_outcomes_computed": False,
        "model_fitted": False,
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Experiment 13 — Pre-outcome Dataset Inventory",
        "",
        "**PASS**",
        "",
        f"- Stress folders: {inventory['stress_folder_count']}",
        f"- Primary complete-case subjects: {inventory['primary_subject_count']}",
        f"- Archive SHA-256: `{inventory['archive_sha256']}`",
        "- Shared primary sensors: EDA, temperature, and three-axis acceleration",
        "- Scientific outcomes computed: no",
        "- Model fitted: no",
        "",
        "## Candidate window feasibility after five-second interval-edge trimming",
        "",
        "| Window | Label | Total | Minimum/subject | Maximum/subject |",
        "|---:|---|---:|---:|---:|",
    ]
    for seconds, labels in inventory["candidate_window_counts"].items():
        for label, values in labels.items():
            lines.append(
                f"| {seconds}s | {label} | {values['total']} | "
                f"{values['minimum_per_subject']} | {values['maximum_per_subject']} |"
            )
    lines.extend(
        [
            "",
            "## Declared primary exclusions",
            "",
            *[f"- {subject}: {reason}" for subject, reason in inventory["excluded_folders"].items()],
            "",
            "This inventory validates data availability and segmentation feasibility only. It contains no classifier, conformal, coverage, or effect-size outcome.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    inventory = build_inventory()
    _atomic_json(INVENTORY_JSON, inventory)
    INVENTORY_MD.write_text(render_markdown(inventory), encoding="utf-8")
    print(
        f"Experiment 13 pre-outcome inventory: PASS ({inventory['primary_subject_count']} subjects)"
    )


if __name__ == "__main__":
    main()
