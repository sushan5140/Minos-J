"""Independent reconstruction and integrity validation of an Experiment 18 report.

Deliberately does NOT import e18_analysis: accuracy, paired counts, McNemar p,
bootstrap CI, tokens and the compute ratio are recomputed here from the raw
terminal markers, the answer key and the ledger, then compared with the report.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

from e18_common import E18_DIR, RESULTS_DIR, TASKS_DIR, WORK_DIR, atomic_write_json

ARMS = ("A", "C", "D", "B")
FROZEN_MODEL = "claude-sonnet-5"
KEY_FIELDS = ("true_mechanism", "is_decoy", "decoy_mechanism", "distractor_mechanism")


def _p(b: int, c: int) -> float:
    n = b + c
    if not n:
        return 1.0
    tail = sum(math.factorial(n) // (math.factorial(i) * math.factorial(n - i)) for i in range(min(b, c) + 1))
    return min(1.0, 2 * tail / 2 ** n)


def _boot(pairs: list[tuple[int, int]], seed: int = 18, n: int = 10000) -> list[float]:
    rng = random.Random(seed)
    m = len(pairs)
    vals = []
    for _ in range(n):
        s = [pairs[rng.randrange(m)] for _ in range(m)]
        vals.append(sum(x - y for x, y in s) / m)
    vals.sort()
    return [vals[int(0.025 * n)], vals[int(0.975 * n) - 1]]


def validate(set_name: str = "main", work: Path = WORK_DIR, tasks: Path = TASKS_DIR, report_path: Path | None = None,
             check_protocol: bool = True) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, ok: bool, detail: Any = "") -> None:
        checks[name] = {"passed": bool(ok), "detail": str(detail)[:400]}

    report_path = report_path or RESULTS_DIR / f"{set_name}_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    root = work / set_name
    ledger = [json.loads(l) for l in (root / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    public = [json.loads(l) for l in (tasks / f"{set_name}_cases_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    key = json.loads((tasks / f"{set_name}_answer_key.json").read_text(encoding="utf-8"))
    cases = [c["case_id"] for c in public]

    if check_protocol:
        sys.path.insert(0, str(Path(__file__).parent))
        import e18_protocol
        check("protocol_frozen_and_verified", e18_protocol.verify())

    seqs = [r["seq"] for r in ledger]
    check("ledger_seq_unique_monotonic", seqs == sorted(set(seqs)), f"rows={len(seqs)}")
    starts = {r["attempt_uid"] for r in ledger if r["event"] == "attempt_started"}
    finishes = {r["attempt_uid"] for r in ledger if r["event"] == "attempt_finished"}
    orphans = {r["attempt_uid"] for r in ledger if r["event"] == "orphan_attempt_recorded"}
    check("every_attempt_finished_or_recorded_orphan", starts <= finishes | orphans, f"unaccounted={len(starts - finishes - orphans)}")
    bad_models = [r["seq"] for r in ledger if r["event"] == "attempt_finished" and r.get("classification") == "OK"
                  and r.get("model_returned") != FROZEN_MODEL]
    check("model_identity_frozen", not bad_models, bad_models[:5])
    terminal = [(r["case_id"], r["arm"]) for r in ledger if r["event"] == "trial_terminal"]
    check("no_duplicate_terminal_trials", len(terminal) == len(set(terminal)), f"terminal={len(terminal)}")

    results = {}
    for c in cases:
        for a in ARMS:
            f = root / "trials" / c / a / "trial_result.json"
            results[(c, a)] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    check("all_trials_terminal", all(results.values()), f"missing={sum(v is None for v in results.values())}")
    check("terminal_markers_match_ledger", set(terminal) == {k for k, v in results.items() if v}, "")

    leak = []
    for f in (root / "trials").glob("*/*/call_*.json"):
        text = f.read_text(encoding="utf-8")
        if any(k in text for k in KEY_FIELDS):
            leak.append(f.name)
    check("no_answer_key_fields_in_model_io", not leak, leak[:5])

    def correct(c: str, a: str) -> int:
        t = results[(c, a)]
        return int(bool(t) and t["status"] == "COMPLETE" and t["final"]["mechanism_id"] == key[c]["true_mechanism"])

    if set_name == "main":
        acc = {a: sum(correct(c, a) for c in cases) / len(cases) for a in ARMS}
        check("arm_accuracies_reconstruct", all(abs(acc[a] - report["accuracy"][a]["all"]) < 1e-12 for a in ARMS), acc)
        pairs = [(correct(c, "A"), correct(c, "C")) for c in cases]
        b = sum(x and not y for x, y in pairs)
        cc = sum(y and not x for x, y in pairs)
        pr = report["primary_A_vs_C"]
        check("primary_counts_reconstruct", (b, cc) == (pr["x_only_correct"], pr["y_only_correct"]), (b, cc))
        check("primary_delta_reconstruct", abs((b - cc) / len(cases) - pr["delta"]) < 1e-12)
        check("mcnemar_p_reconstruct", abs(_p(b, cc) - pr["mcnemar_exact_p"]) < 1e-12, _p(b, cc))
        ci = _boot(pairs)
        check("bootstrap_ci_reconstruct", all(abs(x - y) < 1e-12 for x, y in zip(ci, pr["bootstrap_ci95"])), ci)
        tok = {a: sum(int(r.get("measured_total_tokens") or 0) for r in ledger if r["event"] == "attempt_finished" and r.get("arm") == a)
               for a in ARMS}
        ratio = tok["A"] / tok["C"] if tok["C"] else None
        check("tokens_reconstruct", all(tok[a] == report["compute"]["per_arm"][a]["measured_total_tokens"] for a in ARMS), tok)
        check("compute_ratio_reconstruct", ratio is not None and abs(ratio - report["compute"]["R_measured_tokens_A_over_C"]) < 1e-12, ratio)
    status = "PASSED" if all(v["passed"] for v in checks.values()) else "FAILED"
    return {"set": set_name, "status": status, "passed": sum(v["passed"] for v in checks.values()), "total": len(checks), "checks": checks}


if __name__ == "__main__":
    s = sys.argv[1] if len(sys.argv) > 1 else "main"
    out = validate(s)
    atomic_write_json(RESULTS_DIR / f"{s}_independent_validation.json", out)
    for name, v in out["checks"].items():
        print("PASS" if v["passed"] else "FAIL", name, v["detail"][:120])
    print(out["status"], f"{out['passed']}/{out['total']}")
    sys.exit(0 if out["status"] == "PASSED" else 1)
