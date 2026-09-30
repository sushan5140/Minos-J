"""Deterministic synthetic diagnostic cases for Minos-J Experiment 18.

Setting: a conformal predictor with nominal coverage 0.90 under-covers one
subgroup of a wearable stress-detection cohort.  Exactly one of six candidate
mechanisms is planted as the cause.  Every case presents, for EVERY mechanism,
the same three kinds of evidence:

* marker       - a descriptive statistic that is abnormal when the mechanism is present
                 (subgroup value vs reference value);
* intervention - subgroup coverage after the mechanism-specific remedy;
* series       - subgroup coverage along four conditions ordered from most to least
                 affected by the mechanism.

Each mechanism makes two discriminating predictions (shared, verbatim, with every
arm in MECHANISM_VOCABULARY): its intervention restores coverage toward nominal,
and coverage rises along its series.  The planted mechanism satisfies both.

Decoy cases add a persuasive decoy: a different mechanism whose marker is MORE
abnormal than the planted one and which satisfies exactly ONE of its two
predictions, on that one dimension sometimes more strongly than the planted
mechanism.  A reasoner that trusts the most abnormal marker, or a single
prediction, is misled; checking both predictions for every rival is not.
Non-decoy cases add a milder distractor marker (less abnormal than the planted
one) with no supporting predictions.

The answer key is written to a separate file and never enters a prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import random
from pathlib import Path
from typing import Any

from e18_common import TASKS_DIR, atomic_write_json, atomic_write_text, canonical_sha256, dumps, sha256_file, sha256_text

GENERATOR_VERSION = "e18-tasks-1.0.0"
NOMINAL = 0.90
MAIN_SEED = "E18-MAIN-2026-10-01"
PILOT_SEED = "E18-PILOT-2026-10-01"
DEFAULT_DIFFICULTY = 0.5
CASES_PER_MECHANISM_MAIN = 30      # 15 decoy + 15 non-decoy per mechanism -> 180 cases
CASES_PER_MECHANISM_PILOT = 2      # 1 decoy + 1 non-decoy per mechanism -> 12 cases
ORACLE_MARGIN = 0.04

MECHANISMS: list[dict[str, Any]] = [
    {
        "id": "FINITE_SAMPLE",
        "description": "The subgroup has too few calibration examples, so its conformal threshold is a noisy order statistic and realized coverage fell short by chance.",
        "marker": "subgroup calibration examples (count)",
        "intervention": "mean subgroup coverage over 200 random calibration/test re-splits",
        "series": "coverage using 25% / 50% / 75% / 100% of the subgroup's calibration data",
    },
    {
        "id": "COVARIATE_SHIFT",
        "description": "The subgroup's test windows come from a different feature distribution than its calibration windows, breaking exchangeability.",
        "marker": "calibration-vs-test two-sample classifier AUC (0.50 = no shift)",
        "intervention": "coverage after importance-weighted (likelihood-ratio) calibration",
        "series": "coverage by test-window shift-score quartile, highest to lowest shift",
    },
    {
        "id": "LABEL_NOISE",
        "description": "The subgroup's stress labels are unreliable, so true labels often fall outside sets built for the recorded labels.",
        "marker": "inter-annotator label agreement",
        "intervention": "coverage restricted to windows where both annotators agree",
        "series": "coverage by annotator-disagreement quartile, highest to lowest disagreement",
    },
    {
        "id": "TEMPORAL_DRIFT",
        "description": "The subgroup's physiology or device behaviour drifts over time, so later windows no longer resemble the calibration period.",
        "marker": "lag-1 autocorrelation of nonconformity residuals",
        "intervention": "coverage with rolling recalibration on the most recent 20% of windows",
        "series": "coverage by time since calibration, latest to earliest quarter",
    },
    {
        "id": "SCORE_MISMATCH",
        "description": "Pooled (marginal) calibration uses a threshold dominated by other groups whose nonconformity scores are systematically smaller.",
        "marker": "median nonconformity score, subgroup / reference (1.00 = equal)",
        "intervention": "coverage with group-conditional (Mondrian) calibration",
        "series": "coverage by score-distance-from-reference quartile, farthest to nearest",
    },
    {
        "id": "SENSOR_ARTIFACT",
        "description": "Motion or contact artifacts corrupt a share of the subgroup's sensor windows, producing unreliable features.",
        "marker": "artifact-flagged window rate",
        "intervention": "coverage excluding artifact-flagged windows",
        "series": "coverage by window artifact-score quartile, highest to lowest",
    },
]
MECHANISM_IDS = [m["id"] for m in MECHANISMS]
BY_ID = {m["id"]: m for m in MECHANISMS}


def mechanism_vocabulary() -> str:
    """Identical text shown to every arm in every call."""
    lines = [
        "Candidate mechanisms (exactly one is the planted cause of the subgroup's under-coverage).",
        "For each mechanism, if it IS the cause then (1) its intervention should raise subgroup coverage",
        "most of the way back toward the nominal 0.90, and (2) subgroup coverage should rise steadily",
        "along its series (listed from most affected to least affected).",
        "",
    ]
    for m in MECHANISMS:
        lines += [
            f"- {m['id']}: {m['description']}",
            f"    marker: {m['marker']}",
            f"    intervention: {m['intervention']}",
            f"    series: {m['series']}",
        ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- markers
def _marker(mech: str, a: float, rng: random.Random) -> tuple[str, str]:
    """Return (subgroup_value, reference_value) strings for abnormality a in [0, 1]."""
    if mech == "FINITE_SAMPLE":
        ref = rng.randint(180, 260)
        return str(max(6, round(ref * (1 - 0.94 * a)))), str(ref)
    if mech == "COVARIATE_SHIFT":
        ref = 0.50 + rng.uniform(-0.02, 0.02)
        return f"{min(0.99, 0.50 + 0.45 * a + rng.uniform(-0.01, 0.01)):.2f}", f"{ref:.2f}"
    if mech == "LABEL_NOISE":
        ref = rng.uniform(0.92, 0.96)
        return f"{ref - 0.40 * a:.2f}", f"{ref:.2f}"
    if mech == "TEMPORAL_DRIFT":
        ref = rng.uniform(0.02, 0.08)
        return f"{ref + 0.75 * a:.2f}", f"{ref:.2f}"
    if mech == "SCORE_MISMATCH":
        return f"{1.0 + 1.3 * a + rng.uniform(-0.02, 0.02):.2f}", "1.00"
    if mech == "SENSOR_ARTIFACT":
        ref = rng.uniform(0.02, 0.04)
        return f"{ref + 0.45 * a:.2f}", f"{ref:.2f}"
    raise KeyError(mech)


# --------------------------------------------------------------------------- one case
def _clip(x: float) -> float:
    return min(0.995, max(0.30, x))


def generate_case(rng: random.Random, true_id: str, is_decoy: bool, difficulty: float, decoy_id: str | None,
                  decoy_kind: str | None) -> dict[str, Any]:
    noise = 0.006 + 0.024 * difficulty
    c0 = rng.uniform(0.64, 0.76)
    overall = rng.uniform(0.885, 0.905)
    others = [m for m in MECHANISM_IDS if m != true_id]
    distractor_id = None if is_decoy else rng.choice(others)
    a_true = rng.uniform(0.35, 0.60)
    gain_true = (NOMINAL - c0) * rng.uniform(0.80 - 0.35 * difficulty, 1.0)
    slope_true = (0.88 - c0) * rng.uniform(0.75 - 0.35 * difficulty, 1.0)
    decoy_hi = 1.05 + 0.30 * difficulty   # decoy's single satisfied prediction can exceed the truth's
    evidence: dict[str, dict[str, Any]] = {}
    for mech in MECHANISM_IDS:
        gain = rng.gauss(0.008, noise)
        slope = rng.gauss(0.0, noise * 1.5)
        if mech == true_id:
            a, gain, slope = a_true, gain_true, slope_true
        elif is_decoy and mech == decoy_id:
            a = rng.uniform(max(0.72, a_true + 0.15), 0.95)
            if decoy_kind == "gain":
                gain = gain_true * rng.uniform(0.85, decoy_hi)
            else:
                slope = slope_true * rng.uniform(0.85, decoy_hi)
        elif mech == distractor_id:
            a = rng.uniform(0.12, max(0.13, a_true - 0.10))
        else:
            a = rng.uniform(0.0, 0.10)
        sub, ref = _marker(mech, a, rng)
        intervention = _clip(c0 + gain + rng.gauss(0, noise / 2))
        series = [_clip(c0 + slope * i / 3 + rng.gauss(0, noise)) for i in range(4)]
        evidence[mech] = {
            "marker_subgroup": sub,
            "marker_reference": ref,
            "intervention_coverage": round(intervention, 3),
            "series": [round(s, 3) for s in series],
        }
    return {
        "subgroup_coverage": round(c0, 3),
        "overall_coverage": round(overall, 3),
        "evidence": evidence,
        "_key": {"true_mechanism": true_id, "is_decoy": is_decoy, "decoy_mechanism": decoy_id,
                 "decoy_kind": decoy_kind, "distractor_mechanism": distractor_id, "difficulty": difficulty},
    }


# --------------------------------------------------------------------------- reference solvers (no LLM)
def _stats(case: dict[str, Any]) -> dict[str, tuple[float, float]]:
    c0 = case["subgroup_coverage"]
    return {m: (e["intervention_coverage"] - c0, e["series"][3] - e["series"][0]) for m, e in case["evidence"].items()}


def solve_joint(case: dict[str, Any]) -> str:
    """Ideal falsifier: a mechanism must satisfy BOTH predictions; pick the strongest joint support."""
    s = _stats(case)
    return max(s, key=lambda m: min(s[m]))


def solve_gain_only(case: dict[str, Any]) -> str:
    s = _stats(case)
    return max(s, key=lambda m: s[m][0])


def solve_series_only(case: dict[str, Any]) -> str:
    s = _stats(case)
    return max(s, key=lambda m: s[m][1])


def _abnormality(mech: str, sub: str, ref: str) -> float:
    x, r = float(sub), float(ref)
    return {"FINITE_SAMPLE": (r - x) / r, "COVARIATE_SHIFT": (x - 0.5) / 0.45, "LABEL_NOISE": (r - x) / 0.40,
            "TEMPORAL_DRIFT": (x - r) / 0.75, "SCORE_MISMATCH": (x - 1.0) / 1.3, "SENSOR_ARTIFACT": (x - r) / 0.45}[mech]


def solve_marker_only(case: dict[str, Any]) -> str:
    return max(case["evidence"], key=lambda m: _abnormality(m, case["evidence"][m]["marker_subgroup"],
                                                            case["evidence"][m]["marker_reference"]))


def joint_margin(case: dict[str, Any]) -> float:
    s = _stats(case)
    true_id = case["_key"]["true_mechanism"]
    return min(s[true_id]) - max(min(v) for m, v in s.items() if m != true_id)


# --------------------------------------------------------------------------- rendering (public)
def render_packet(case: dict[str, Any], order: list[str]) -> str:
    lines = [
        "Observation: a split-conformal stress classifier with nominal coverage 0.90 under-covers one subject subgroup.",
        f"Overall coverage: {case['overall_coverage']:.3f}.   Subgroup coverage: {case['subgroup_coverage']:.3f}.",
        "",
        "Diagnostics for the under-covered subgroup (series values run from most affected to least affected):",
        "",
        "| Mechanism | Marker: subgroup (reference) | Intervention coverage | Coverage series |",
        "|---|---|---|---|",
    ]
    for mech in order:
        e = case["evidence"][mech]
        series = " -> ".join(f"{v:.3f}" for v in e["series"])
        lines.append(f"| {mech} | {e['marker_subgroup']} ({e['marker_reference']}) | {e['intervention_coverage']:.3f} | {series} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------- task sets
def _rng(*parts: Any) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16], 16))


def build_set(seed: str, per_mechanism: int, prefix: str, difficulty: float) -> tuple[list[dict], dict[str, dict]]:
    plan = []
    for mi, mech in enumerate(MECHANISM_IDS):
        others = [m for m in MECHANISM_IDS if m != mech]
        for j in range(per_mechanism):
            is_decoy = j % 2 == 0
            decoy_id = others[(j // 2 + mi) % len(others)] if is_decoy else None   # balanced rotation
            decoy_kind = ("gain", "series")[(j // 2) % 2] if is_decoy else None
            plan.append((mech, is_decoy, decoy_id, decoy_kind, j))
    _rng(seed, "order").shuffle(plan)
    public, key = [], {}
    for index, (mech, is_decoy, decoy_id, decoy_kind, j) in enumerate(plan, 1):
        case_id = f"{prefix}-{index:03d}"
        attempt = 0
        while True:  # resample until the planted mechanism is uniquely identifiable in principle
            rng = _rng(seed, mech, j, attempt)
            case = generate_case(rng, mech, is_decoy, difficulty, decoy_id, decoy_kind)
            if joint_margin(case) >= ORACLE_MARGIN:
                break
            attempt += 1
        order = list(MECHANISM_IDS)
        _rng(seed, case_id, "display").shuffle(order)
        packet = render_packet(case, order)
        public.append({"case_id": case_id, "packet": packet, "packet_sha256": sha256_text(packet)})
        key[case_id] = {**case["_key"], "resample_attempts": attempt, "joint_margin": round(joint_margin(case), 4),
                        "evidence": case["evidence"], "subgroup_coverage": case["subgroup_coverage"]}
    return public, key


def solver_report(key: dict[str, dict]) -> dict[str, Any]:
    out = {}
    for name, fn in (("joint_falsifier", solve_joint), ("marker_only", solve_marker_only),
                     ("intervention_only", solve_gain_only), ("series_only", solve_series_only)):
        rows = {"all": [], "decoy": [], "non_decoy": []}
        for k in key.values():
            case = {"subgroup_coverage": k["subgroup_coverage"], "evidence": k["evidence"], "_key": k}
            ok = fn(case) == k["true_mechanism"]
            rows["all"].append(ok)
            rows["decoy" if k["is_decoy"] else "non_decoy"].append(ok)
        out[name] = {g: round(sum(v) / len(v), 4) for g, v in rows.items()}
    return out


def write_set(name: str, seed: str, per_mechanism: int, prefix: str, difficulty: float) -> dict[str, Any]:
    public, key = build_set(seed, per_mechanism, prefix, difficulty)
    public_path = TASKS_DIR / f"{name}_cases_public.jsonl"
    key_path = TASKS_DIR / f"{name}_answer_key.json"
    atomic_write_text(public_path, "".join(dumps(row, sort_keys=True) + "\n" for row in public))
    atomic_write_json(key_path, key)
    counts = {}
    for k in key.values():
        counts.setdefault(k["true_mechanism"], {"decoy": 0, "non_decoy": 0})
        counts[k["true_mechanism"]]["decoy" if k["is_decoy"] else "non_decoy"] += 1
    return {
        "set": name, "seed": seed, "difficulty": difficulty, "n_cases": len(public), "counts": counts,
        "public_file": public_path.name, "public_sha256": sha256_file(public_path),
        "answer_key_file": key_path.name, "answer_key_sha256": sha256_file(key_path),
        "case_ids_sha256": canonical_sha256([r["case_id"] for r in public]),
        "packet_hashes_sha256": canonical_sha256({r["case_id"]: r["packet_sha256"] for r in public}),
        "reference_solvers": solver_report(key),
        "max_resample_attempts": max(k["resample_attempts"] for k in key.values()),
    }


def build_all(difficulty: float = DEFAULT_DIFFICULTY) -> dict[str, Any]:
    manifest = {
        "generator_version": GENERATOR_VERSION,
        "generator_sha256": sha256_file(Path(__file__)),
        "vocabulary_sha256": sha256_text(mechanism_vocabulary()),
        "mechanisms": MECHANISM_IDS,
        "oracle_margin": ORACLE_MARGIN,
        "main": write_set("main", MAIN_SEED, CASES_PER_MECHANISM_MAIN, "E18-M", difficulty),
        "pilot": write_set("pilot", PILOT_SEED, CASES_PER_MECHANISM_PILOT, "E18-P", difficulty),
    }
    atomic_write_json(TASKS_DIR / "manifest.json", manifest)
    return manifest


def load_public(name: str) -> list[dict[str, Any]]:
    import json
    return [json.loads(l) for l in (TASKS_DIR / f"{name}_cases_public.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--difficulty", type=float, default=DEFAULT_DIFFICULTY)
    args = parser.parse_args()
    m = build_all(args.difficulty)
    print(dumps({k: m[k] for k in ("generator_sha256", "vocabulary_sha256")}, indent=2))
    for s in ("main", "pilot"):
        print(s, m[s]["n_cases"], m[s]["public_sha256"][:16], dumps(m[s]["reference_solvers"]))
