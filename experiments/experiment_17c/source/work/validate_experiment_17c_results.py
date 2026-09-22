"""Independent integrity and result validation for Minos-J Experiment 17-C.

Adapted from ``validate_experiment_17_results.py``: same checks, pointed at the
Experiment 17-C paths, protocol and Claude models.  The pre-run baseline is
captured by ``validate_experiment_17c_harness.py --capture-baseline`` and covers
every file of Experiments 1-17, including the interrupted original Experiment 17.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import experiment_17_runtime as runtime  # noqa: E402
import run_experiment_16_matched_compute as e16  # noqa: E402
import experiment_17c_claude_runtime as claude_rt  # noqa: E402
import run_experiment_17c_claude_replication as e17  # noqa: E402
from work.validate_experiment_17c_harness import historical_manifest as historical_manifest_17c  # noqa: E402
import schema  # noqa: E402


BASELINE_JSON = PROJECT_DIR / "work" / "experiment_17c_historical_baseline.json"
OUT_JSON = PROJECT_DIR / "outputs" / "meno_j_experiment_17c_independent_validation.json"
OUT_MD = PROJECT_DIR / "outputs" / "meno_j_experiment_17c_independent_validation.md"
SKIP_PARTS = {"__pycache__", ".git", "vendor", "external", "e13_data", ".venv"}
SECRET_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9_-]{32,}|sk-ant-[A-Za-z0-9_-]{20,}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_load(path: Path) -> Any:
    def reject(value: str) -> None:
        raise ValueError(f"Non-standard JSON constant {value!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def strict_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"Non-standard JSON constant {value!r}")
            )))
        except Exception as exc:
            raise ValueError(f"Invalid JSONL in {path} line {line_number}: {exc}") from exc
    return rows


def historical_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        rel = path.relative_to(PROJECT_DIR).as_posix()
        low = rel.lower()
        if rel == ".env" or "experiment_17" in low:
            continue
        manifest[rel] = sha256(path)
    return dict(sorted(manifest.items()))


def capture_baseline() -> None:
    scientific = [
        e17.REAL_PATHS["report_json"],
        e17.REAL_PATHS["raw_units"],
        e17.REAL_PATHS["raw_requests"],
        e17.REAL_PATHS["judgments"],
    ]
    existing = [str(path.relative_to(PROJECT_DIR)) for path in scientific if path.exists()]
    if existing:
        raise SystemExit(f"Refusing to capture a pre-run baseline after scientific outputs exist: {existing}")
    manifest = historical_manifest()
    payload = {
        "purpose": "Pre-execution historical integrity baseline for Experiment 17",
        "protocol_sha256": e17.protocol_sha256(),
        "generator_model": claude_rt.GENERATOR_MODEL,
        "judge_model": claude_rt.JUDGE_MODEL,
        "file_count": len(manifest),
        "manifest": manifest,
    }
    runtime.atomic_write_json(BASELINE_JSON, payload)
    print(f"Captured Experiment 17 historical baseline: {len(manifest)} files")
    print(f"Protocol SHA-256: {e17.protocol_sha256()}")


def close(left: Any, right: Any, tolerance: float = 1e-12) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)
    return left == right


def load_env_key() -> str:
    path = PROJECT_DIR / ".env"
    if not path.exists():
        return ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "OPENROUTER_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-baseline", action="store_true")
    args = parser.parse_args()
    if args.capture_baseline:
        raise SystemExit("Use work/validate_experiment_17c_harness.py --capture-baseline.")

    e17._install_protocol_globals()
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    required = [path for key, path in e17.REAL_PATHS.items() if key != "checkpoints"]
    missing = [str(path.relative_to(PROJECT_DIR)) for path in required if not path.exists() or not path.stat().st_size]
    check("all_scientific_outputs_exist", not missing, ", ".join(missing))
    if missing:
        write_validation(checks, None)
        raise SystemExit(1)

    report = strict_load(e17.REAL_PATHS["report_json"])
    units = report.get("units", [])
    raw_units = strict_jsonl(e17.REAL_PATHS["raw_units"])
    ledger = strict_jsonl(e17.REAL_PATHS["raw_requests"])
    judgments = strict_jsonl(e17.REAL_PATHS["judgments"])

    frozen = strict_load(e17.PROTOCOL_JSON)
    md_text = e17.PROTOCOL_MD.read_text(encoding="utf-8")
    declared = re.search(r"Protocol SHA-256[^`]*`([0-9a-f]{64})`", md_text)
    check(
        "protocol_frozen_and_hash_verified",
        frozen == e17.PROTOCOL and declared is not None and declared.group(1) == e17.protocol_sha256()
        and report.get("protocol_sha256") == e17.protocol_sha256(),
        f"canonical SHA-256 {e17.protocol_sha256()}",
    )
    check(
        "model_assignments_exact",
        report.get("generator_model") == claude_rt.GENERATOR_MODEL
        and report.get("judge_model") == claude_rt.JUDGE_MODEL
        and all(u.get("generator_model") == claude_rt.GENERATOR_MODEL for u in units)
        and all(u.get("judge_model") == claude_rt.JUDGE_MODEL for u in units),
        f"generator={report.get('generator_model')}; judge={report.get('judge_model')}",
    )

    expected_ids = {f"Q{question}-r{replicate}" for replicate in range(1, 4) for question in range(1, 4)}
    unit_ids = [u.get("unit_id") for u in units]
    raw_ids = [u.get("unit_id") for u in raw_units]
    check(
        "nine_unique_preregistered_units",
        len(units) == 9 and len(set(unit_ids)) == 9 and set(unit_ids) == expected_ids
        and raw_ids == unit_ids,
        f"report={unit_ids}; raw={raw_ids}",
    )

    sequences = [row.get("seq") for row in ledger]
    seq_ok = bool(sequences) and all(type(value) is int and value > 0 for value in sequences)
    seq_ok = seq_ok and len(sequences) == len(set(sequences)) and sequences == sorted(sequences)
    check("ledger_sequences_unique_and_monotonic", seq_ok, f"rows={len(sequences)}; max={max(sequences, default=0)}")

    request_rows = [row for row in ledger if row.get("event") == "request"]
    failed_rows = [row for row in ledger if row.get("event") == "request_failed"]
    model_bad = [
        row.get("seq") for row in request_rows + failed_rows
        if row.get("model_requested") != (
            claude_rt.JUDGE_MODEL if row.get("arm") == "JUDGE" else claude_rt.GENERATOR_MODEL
        )
    ]
    check("ledger_uses_only_frozen_models", not model_bad, f"bad sequences={model_bad[:10]}")

    budget_mismatches: list[str] = []
    for unit in units:
        for arm, key in (("A", "budget_A"), ("B", "budget_B"), ("JUDGE", "judge_budget")):
            if key not in unit:
                if unit.get("status") == "COMPLETE":
                    budget_mismatches.append(f"{unit['unit_id']}/{key}:missing")
                continue
            recomputed = e16.summarize_budget(ledger, unit["unit_id"], arm)
            for field in e16.BUDGET_FIELDS:
                if not close(recomputed.get(field), unit[key].get(field)):
                    budget_mismatches.append(f"{unit['unit_id']}/{arm}/{field}")
    check("per_unit_budgets_recompute_from_ledger", not budget_mismatches, ", ".join(budget_mismatches[:12]))

    total_from_ledger = sum(row.get("total_tokens", 0) for row in request_rows)
    total_from_report = sum(report["budget_totals"][arm]["total_tokens"] for arm in ("A", "B", "JUDGE"))
    attempts_from_ledger = sum(
        row.get("http_attempts", 0) for row in ledger if row.get("event") in {"request", "request_failed"}
    )
    attempts_from_report = sum(report["budget_totals"][arm]["http_attempts"] for arm in ("A", "B", "JUDGE"))
    check(
        "token_and_attempt_accounting_reconciles",
        total_from_ledger == total_from_report and attempts_from_ledger == attempts_from_report,
        f"tokens={total_from_ledger}/{total_from_report}; attempts={attempts_from_ledger}/{attempts_from_report}",
    )

    match_bad: list[str] = []
    complete = [unit for unit in units if unit.get("status") == "COMPLETE"]
    for unit in complete:
        total_a = unit["budget_A"]["total_tokens"]
        total_b = unit["budget_B"]["total_tokens"]
        ratio = total_b / total_a if total_a else math.inf
        parity = unit["budget_A"]["evaluator_calls"] == unit["budget_B"]["evaluator_calls"] == 1
        expected = 0.85 <= ratio <= 1.15 and parity
        if not close(ratio, unit.get("token_ratio_B_over_A")) or expected != unit.get("budget_matched"):
            match_bad.append(unit["unit_id"])
    analysable = [unit for unit in complete if unit.get("budget_matched")]
    check(
        "matched_compute_flags_and_count",
        not match_bad and report.get("budget_matched_units") == len(analysable),
        f"analysable={len(analysable)}; mismatches={match_bad}",
    )

    judge_bad: list[str] = []
    for unit in complete:
        rows = [row for row in judgments if row.get("unit_id") == unit["unit_id"]]
        ids = [row.get("card_id") for row in rows]
        batch_ids = [card_id for batch in unit.get("judge_batches", []) for card_id in batch.get("card_ids", [])]
        if len(ids) != len(set(ids)) or sorted(ids) != sorted(batch_ids):
            judge_bad.append(f"{unit['unit_id']}:coverage")
        for arm in ("A", "B"):
            arm_rows = [row for row in rows if row.get("arm") == arm]
            if len(arm_rows) != unit[f"metrics_{arm}"]["reported_survivors"]:
                judge_bad.append(f"{unit['unit_id']}:{arm}:survivors")
            try:
                recount = sum(e16.judge_validated(row["judgment"], schema) for row in arm_rows)
            except Exception:
                recount = -1
            if recount != unit[f"metrics_{arm}"]["judge_validated"]:
                judge_bad.append(f"{unit['unit_id']}:{arm}:validated")
        for batch in unit.get("judge_batches", []):
            batch_rows = [row for row in rows if row.get("card_id") in batch.get("card_ids", [])]
            payload = {"judgments": [row["judgment"] for row in batch_rows]}
            try:
                e16.validate_judgments(payload, batch.get("card_ids", []), schema)
            except Exception as exc:
                judge_bad.append(f"{unit['unit_id']}:schema:{type(exc).__name__}")
    failed_judge_rows = [unit for unit in units if unit.get("status") == "JUDGE_FAILED"]
    check(
        "judge_outputs_schema_and_counts",
        not judge_bad,
        f"judgment_rows={len(judgments)}; judge_failed_units={len(failed_judge_rows)}; issues={judge_bad[:12]}",
    )

    differences = [float(unit["difference_A_minus_B"]) for unit in analysable]
    recomputed_stats = e16.decide_verdict(differences, len(units))
    stats_bad = [
        key for key, value in recomputed_stats.items()
        if key not in report.get("statistics", {}) or (
            isinstance(value, list)
            and (len(value) != len(report["statistics"][key]) or any(
                not close(a, b) for a, b in zip(value, report["statistics"][key])
            ))
        ) or (not isinstance(value, list) and not close(value, report["statistics"].get(key)))
    ]
    pair_bad = [
        unit["unit_id"] for unit in complete
        if unit.get("difference_A_minus_B")
        != unit.get("metrics_A", {}).get("judge_validated", 0) - unit.get("metrics_B", {}).get("judge_validated", 0)
    ]
    check("paired_differences_recompute", not pair_bad, ", ".join(pair_bad))
    check(
        "bootstrap_ci_and_preregistered_verdict_recompute",
        not stats_bad and report.get("verdict") == recomputed_stats["verdict"],
        f"verdict={recomputed_stats['verdict']}; stats mismatches={stats_bad}",
    )

    baseline = strict_load(BASELINE_JSON) if BASELINE_JSON.exists() else None
    current_manifest = historical_manifest_17c()
    changed = [] if baseline else ["missing baseline"]
    if baseline:
        before = baseline.get("manifest", {})
        changed = sorted(path for path in before.keys() | current_manifest.keys() if before.get(path) != current_manifest.get(path))
    check(
        "historical_experiments_unchanged",
        baseline is not None and not changed,
        f"files={len(current_manifest)}; changed={changed[:12]}",
    )

    key = load_env_key()
    credential_hits: list[str] = []
    scan_paths = [
        path for path in PROJECT_DIR.rglob("*")
        if path.is_file() and not SKIP_PARTS.intersection(path.parts)
        and path.name != ".env" and "17c" in path.relative_to(PROJECT_DIR).as_posix().lower()
        and path.suffix.lower() in {".py", ".json", ".jsonl", ".md", ".csv"}
    ]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if (key and key in text) or SECRET_PATTERN.search(text):
            credential_hits.append(path.relative_to(PROJECT_DIR).as_posix())
    check("credential_safety_scan", not credential_hits, f"files={len(scan_paths)}; hits={credential_hits}")

    judge_states = list(e17.REAL_PATHS["checkpoints"].glob("*/judge_state.json")) if e17.REAL_PATHS["checkpoints"].exists() else []
    state_bad: list[str] = []
    for path in judge_states:
        state = strict_load(path)
        batches = state.get("batches", [])
        for batch in (batches.values() if isinstance(batches, dict) else batches):
            attempts = batch.get("attempts", [])
            if len(attempts) > 2 or any(item.get("status") == "STARTED" for item in attempts):
                state_bad.append(str(path.relative_to(PROJECT_DIR)))
    check(
        "resume_and_judge_attempt_integrity",
        not state_bad,
        f"judge_state_files={len(judge_states)}; invalid={state_bad}",
    )

    write_validation(checks, report)
    if not all(item["passed"] for item in checks.values()):
        raise SystemExit(1)


def write_validation(checks: dict[str, dict[str, Any]], report: dict[str, Any] | None) -> None:
    passed = all(item["passed"] for item in checks.values())
    payload = {
        "experiment_name": e17.EXPERIMENT_NAME,
        "scope": "Independent post-execution validation of real Experiment 17-C outputs",
        "status": "PASSED" if passed else "FAILED",
        "protocol_sha256": e17.protocol_sha256(),
        "scientific_verdict": report.get("verdict") if report else None,
        "checks": checks,
    }
    runtime.atomic_write_json(OUT_JSON, payload)
    lines = [
        f"# {e17.EXPERIMENT_NAME} — Independent Validation",
        "",
        f"- Status: **{payload['status']}**",
        f"- Protocol SHA-256: `{payload['protocol_sha256']}`",
        f"- Scientific verdict: `{payload['scientific_verdict'] or 'not available'}`",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, value in checks.items():
        detail = str(value["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {name} | {'PASS' if value['passed'] else 'FAIL'} | {detail} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, value in checks.items():
        print(f"{'PASS' if value['passed'] else 'FAIL'}  {name}  {value['detail']}")
    print(f"Independent Experiment 17-C validation: {payload['status']}")


if __name__ == "__main__":
    main()
