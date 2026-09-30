"""Deterministic scoring and preregistered statistics for Experiment 18.

The ONLY module that reads answer keys, and only after every trial of a set is
terminal. Correctness = final mechanism_id == planted mechanism (string compare).
The pilot report computes pooled accuracy (all arms together) and infrastructure
measures only; per-arm pilot accuracies are deliberately not computed.
"""

from __future__ import annotations

import json
import math
import random
from math import comb
from pathlib import Path
from typing import Any, Callable

import e18_prompts as P
from e18_common import E18_DIR, PILOT_DIR, RESULTS_DIR, TASKS_DIR, WORK_DIR, atomic_write_json, read_json_strict, read_jsonl_strict

MECHS_N = 6
PRACTICAL_MARGIN = 0.10
COMPUTE_PARITY_LIMIT = 1.20
BOOT_N, BOOT_SEED = 10000, 18
TOKEN_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens", "measured_total_tokens")


# ----------------------------------------------------------------------------- loading
def load(set_name: str, work: Path = WORK_DIR, tasks: Path = TASKS_DIR) -> dict[str, Any]:
    root = work / set_name
    public = [json.loads(l) for l in (tasks / f"{set_name}_cases_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    trials = {}
    for case in public:
        for arm in P.ARMS:
            trials[(case["case_id"], arm)] = read_json_strict(root / "trials" / case["case_id"] / arm / "trial_result.json")
    missing = [k for k, v in trials.items() if v is None]
    if missing:
        raise RuntimeError(f"{len(missing)} trials are not terminal; refusing to score (first: {missing[0]})")
    key = json.loads((tasks / f"{set_name}_answer_key.json").read_text(encoding="utf-8"))
    return {"cases": [c["case_id"] for c in public], "trials": trials, "key": key,
            "ledger": read_jsonl_strict(root / "ledger.jsonl")}


def is_correct(data: dict[str, Any], case: str, arm: str) -> bool:
    t = data["trials"][(case, arm)]
    return t["status"] == "COMPLETE" and t["final"]["mechanism_id"] == data["key"][case]["true_mechanism"]


# ----------------------------------------------------------------------------- statistics
def mcnemar_exact_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def bootstrap_ci(items: list[Any], stat: Callable[[list[Any]], float], seed: int = BOOT_SEED, n_boot: int = BOOT_N) -> list[float]:
    rng = random.Random(seed)
    m = len(items)
    draws = sorted(stat([items[rng.randrange(m)] for _ in range(m)]) for _ in range(n_boot))
    return [draws[int(0.025 * n_boot)], draws[int(0.975 * n_boot) - 1]]


def _wilson(x: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


def newcombe_paired(a: int, b: int, c: int, d: int) -> list[float]:
    """Newcombe (1998) method 10 CI for a difference of paired proportions (p1 = A correct, p2 = C correct)."""
    n = a + b + c + d
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = _wilson(a + b, n)
    l2, u2 = _wilson(a + c, n)
    den = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    phi = (a * d - b * c) / den if den else 0.0
    delta = p1 - p2
    dl = math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    du = math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return [delta - dl, delta + du]


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    order = sorted(pvalues, key=pvalues.get)
    m, running, out = len(order), 0.0, {}
    for i, name in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvalues[name]))
        out[name] = running
    return out


def paired(data: dict[str, Any], arm_x: str, arm_y: str, cases: list[str]) -> dict[str, Any]:
    pairs = [(is_correct(data, c, arm_x), is_correct(data, c, arm_y)) for c in cases]
    if not pairs:
        return {"comparison": f"{arm_x}-{arm_y}", "n_cases": 0, "delta": None, "bootstrap_ci95": None,
                "newcombe_ci95": None, "mcnemar_exact_p": 1.0, "note": "empty subset"}
    a = sum(x and y for x, y in pairs)
    b = sum(x and not y for x, y in pairs)
    c = sum(y and not x for x, y in pairs)
    d = len(pairs) - a - b - c
    delta = (b - c) / len(pairs) if pairs else float("nan")
    return {
        "comparison": f"{arm_x}-{arm_y}", "n_cases": len(pairs),
        "accuracy": {arm_x: (a + b) / len(pairs), arm_y: (a + c) / len(pairs)},
        "both_correct": a, "x_only_correct": b, "y_only_correct": c, "both_wrong": d,
        "discordant": b + c, "delta": delta,
        "bootstrap_ci95": bootstrap_ci(pairs, lambda s: sum(x - y for x, y in s) / len(s)),
        "newcombe_ci95": newcombe_paired(a, b, c, d),
        "mcnemar_exact_p": mcnemar_exact_p(b, c),
        "odds_ratio_b_over_c": (b / c) if c else None,
    }


def brier(data: dict[str, Any], arm: str) -> dict[str, Any]:
    scores = []
    for case in data["cases"]:
        t = data["trials"][(case, arm)]
        if t["status"] != "COMPLETE":
            continue
        truth = data["key"][case]["true_mechanism"]
        scores.append(sum((p - (1.0 if m == truth else 0.0)) ** 2 for m, p in t["final"]["probabilities_normalized"].items()))
    if not scores:
        return {"n": 0, "mean": None, "bootstrap_ci95": None}
    return {"n": len(scores), "mean": sum(scores) / len(scores), "bootstrap_ci95": bootstrap_ci(scores, lambda s: sum(s) / len(s))}


def compute(data: dict[str, Any], set_name: str) -> dict[str, Any]:
    per_arm: dict[str, dict[str, Any]] = {}
    for arm in P.ARMS:
        rows = [r for r in data["ledger"] if r.get("event") == "attempt_finished" and r.get("arm") == arm and r.get("set") == set_name]
        statuses = [data["trials"][(c, arm)]["status"] for c in data["cases"]]
        per_arm[arm] = {
            **{f: sum(int(r.get(f) or 0) for r in rows) for f in TOKEN_FIELDS},
            "attempts": len(rows),
            "logical_calls": sum(1 for r in data["ledger"] if r.get("event") == "logical_call" and r.get("arm") == arm and r.get("set") == set_name),
            "repairs_used": sum(1 for r in data["ledger"] if r.get("event") == "logical_call" and r.get("arm") == arm and r.get("repair_used") and r.get("set") == set_name),
            "calls_completed": sum(data["trials"][(c, arm)]["calls_completed"] for c in data["cases"]),
            "latency_s": round(sum(float(r.get("latency_s") or 0) for r in rows), 3),
            "trials": len(statuses),
            "failed_output": statuses.count("FAILED_OUTPUT"),
            "failed_infra": statuses.count("FAILED_INFRA"),
        }
    return per_arm


def verdict(primary: dict[str, Any], per_arm: dict[str, Any], n_cases: int, terminal_ac: int, ratio: float | None) -> str:
    lo, hi = primary["bootstrap_ci95"]
    infra = max(per_arm["A"]["failed_infra"], per_arm["C"]["failed_infra"]) / max(1, n_cases)
    if terminal_ac < 0.95 * n_cases or infra > 0.10:
        return "INCONCLUSIVE_INCOMPLETE"
    if hi < 0:
        return "C_SUPERIOR"
    if hi < PRACTICAL_MARGIN:
        return "NO_PRACTICALLY_MEANINGFUL_ADVANTAGE"
    supported = primary["delta"] >= PRACTICAL_MARGIN and lo > 0 and primary["mcnemar_exact_p"] < 0.05
    if supported and ratio is not None and ratio <= COMPUTE_PARITY_LIMIT:
        return "FALSIFICATION_ADVANTAGE_SUPPORTED"
    if supported:
        return "ADVANTAGE_BUT_COMPUTE_UNMATCHED"
    if lo > 0 or (lo <= 0 <= hi and hi >= PRACTICAL_MARGIN and lo < PRACTICAL_MARGIN):
        return "POSITIVE_BELOW_MARGIN_OR_UNCERTAIN"
    return "INCONCLUSIVE"


def main_report(data: dict[str, Any]) -> dict[str, Any]:
    cases = data["cases"]
    decoy = [c for c in cases if data["key"][c]["is_decoy"]]
    nondecoy = [c for c in cases if not data["key"][c]["is_decoy"]]
    per_arm = compute(data, "main")
    primary = paired(data, "A", "C", cases)
    ratio = per_arm["A"]["measured_total_tokens"] / per_arm["C"]["measured_total_tokens"] if per_arm["C"]["measured_total_tokens"] else None
    out_ratio = per_arm["A"]["output_tokens"] / per_arm["C"]["output_tokens"] if per_arm["C"]["output_tokens"] else None
    secondary = {"S1_A_vs_D": paired(data, "A", "D", cases), "S2_A_vs_B": paired(data, "A", "B", cases),
                 "S3_A_vs_C_decoy": paired(data, "A", "C", decoy), "S4_A_vs_C_nondecoy": paired(data, "A", "C", nondecoy)}
    adjusted = holm({k: v["mcnemar_exact_p"] for k, v in secondary.items()})
    for k in secondary:
        secondary[k]["holm_adjusted_p"] = adjusted[k]
    strata = [(c, data["key"][c]["is_decoy"]) for c in cases]

    def interaction(sample: list[tuple[str, bool]]) -> float:
        def d(sub):
            return sum(is_correct(data, c, "A") - is_correct(data, c, "C") for c, _ in sub) / len(sub) if sub else 0.0
        return d([s for s in sample if s[1]]) - d([s for s in sample if not s[1]])

    s5 = {"estimate": interaction(strata), "bootstrap_ci95": bootstrap_ci(strata, interaction)}
    per_protocol = [c for c in cases if data["trials"][(c, "A")]["status"] == "COMPLETE" and data["trials"][(c, "C")]["status"] == "COMPLETE"]
    terminal_ac = sum(1 for c in cases if data["trials"][(c, "A")] and data["trials"][(c, "C")])
    def rate(arm: str, subset: list[str]) -> float | None:
        return sum(is_correct(data, c, arm) for c in subset) / len(subset) if subset else None

    accuracy = {arm: {"all": rate(arm, cases), "decoy": rate(arm, decoy), "non_decoy": rate(arm, nondecoy)} for arm in P.ARMS}
    by_mech = {}
    for arm in P.ARMS:
        by_mech[arm] = {}
        for c in cases:
            m = data["key"][c]["true_mechanism"]
            by_mech[arm].setdefault(m, []).append(is_correct(data, c, arm))
        by_mech[arm] = {m: sum(v) / len(v) for m, v in by_mech[arm].items()}
    return {
        "set": "main", "n_cases": len(cases), "primary_A_vs_C": primary,
        "per_protocol_A_vs_C": paired(data, "A", "C", per_protocol) if per_protocol else None,
        "secondary": secondary, "S5_decoy_interaction": s5,
        "brier": {arm: brier(data, arm) for arm in P.ARMS},
        "accuracy": accuracy, "accuracy_by_mechanism": by_mech,
        "compute": {"per_arm": per_arm, "R_measured_tokens_A_over_C": ratio, "R_output_tokens_A_over_C": out_ratio,
                    "parity_limit": COMPUTE_PARITY_LIMIT, "gate_pass": ratio is not None and ratio <= COMPUTE_PARITY_LIMIT},
        "orphan_attempts": sum(1 for r in data["ledger"] if r.get("event") == "orphan_attempt_recorded"),
        "pauses": sum(1 for r in data["ledger"] if r.get("event") == "session_paused"),
        "verdict": verdict(primary, per_arm, len(cases), terminal_ac, ratio),
    }


def pilot_report(data: dict[str, Any]) -> dict[str, Any]:
    pooled = [is_correct(data, c, arm) for c in data["cases"] for arm in P.ARMS]
    acc = sum(pooled) / len(pooled)
    difficulty = data["key"][data["cases"][0]]["difficulty"]
    if acc > 0.85:
        decision, new = "RAISE_DIFFICULTY", min(1.0, difficulty + 0.25)
    elif acc < 0.40:
        decision, new = "LOWER_DIFFICULTY", max(0.0, difficulty - 0.25)
    else:
        decision, new = "KEEP", difficulty
    per_arm = compute(data, "pilot")
    return {"set": "pilot", "pooled_accuracy_all_arms": acc, "n_trials": len(pooled), "difficulty": difficulty,
            "preregistered_difficulty_decision": decision, "main_difficulty_after_rule": new,
            "infrastructure": {arm: {k: v for k, v in per_arm[arm].items()} for arm in P.ARMS},
            "note": "Per-arm pilot accuracy is intentionally not computed (pilot policy: no treatment-difference inspection)."}


def write_report(set_name: str, work: Path = WORK_DIR, tasks: Path = TASKS_DIR, out: Path | None = None) -> dict[str, Any]:
    data = load(set_name, work, tasks)
    report = pilot_report(data) if set_name == "pilot" else main_report(data)
    target = out or ((PILOT_DIR / "pilot_report.json") if set_name == "pilot" else RESULTS_DIR / "main_report.json")
    atomic_write_json(target, report)
    return report
