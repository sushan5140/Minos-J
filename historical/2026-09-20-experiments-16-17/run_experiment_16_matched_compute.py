"""Meno-J / Minos-J Experiment 16: Matched-Compute Architecture Falsification.

Question: if the multi-stage v4 pipeline beats a simpler baseline, does the
architecture deserve the credit once inference budget, sampling, retries and
evaluator passes are matched?

Provenance
----------
* This file was written on 2026-09-17. It is NOT part of the historical
  2026-08-04 .. 2026-08-17 record and it never rewrites Experiments 1-15.
* Arm A calls the historical ``pipeline.run_v4_pipeline`` unchanged.
* All model traffic goes through the historical ``llm_client`` unchanged; this
  runner only wraps ``llm_client._request_json`` to meter calls and tokens.

Modes
-----
  --write-protocol            freeze the preregistered protocol (before any run)
  --run                       real run (needs OPENROUTER_API_KEY, judge model)
  --fake-harness-validation   deterministic fake model; HARNESS VALIDATION ONLY
"""

from __future__ import annotations

import argparse
import csv
import email.message
import hashlib
import io
import json
import math
import os
import random
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

EXPERIMENT_16_NAME = "Meno-J Experiment 16: Matched-Compute Architecture Falsification"
EXPERIMENT_16_SLUG = "meno_j_experiment_16_matched_compute"
OUTPUT_DIR = PROJECT_DIR / "outputs"
WORK_DIR = PROJECT_DIR / "work"

PROTOCOL_JSON = OUTPUT_DIR / "meno_j_experiment_16_preregistered_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_experiment_16_preregistered_protocol.md"

REAL_PATHS = {
    "checkpoints": WORK_DIR / "experiment_16_checkpoints",
    "report_json": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}.json",
    "report_md": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}.md",
    "raw_units": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}_raw_units.jsonl",
    "raw_requests": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}_raw_requests.jsonl",
    "judgments": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}_judgments.jsonl",
    "aggregate_csv": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}_aggregate.csv",
    "budget_csv": OUTPUT_DIR / f"{EXPERIMENT_16_SLUG}_budget_accounting.csv",
    "repro_json": OUTPUT_DIR / "meno_j_experiment_16_reproducibility_summary.json",
    "repro_md": OUTPUT_DIR / "meno_j_experiment_16_reproducibility_summary.md",
}
HARNESS_DIR = OUTPUT_DIR / "harness_validation" / "experiment_16"
HARNESS_PREFIX = "meno_j_experiment_16_HARNESS_VALIDATION_ONLY_fake_model"
FAKE_PATHS = {
    "checkpoints": WORK_DIR / "experiment_16_harness_validation_checkpoints",
    "report_json": HARNESS_DIR / f"{HARNESS_PREFIX}.json",
    "report_md": HARNESS_DIR / f"{HARNESS_PREFIX}.md",
    "raw_units": HARNESS_DIR / f"{HARNESS_PREFIX}_raw_units.jsonl",
    "raw_requests": HARNESS_DIR / f"{HARNESS_PREFIX}_raw_requests.jsonl",
    "judgments": HARNESS_DIR / f"{HARNESS_PREFIX}_judgments.jsonl",
    "aggregate_csv": HARNESS_DIR / f"{HARNESS_PREFIX}_aggregate.csv",
    "budget_csv": HARNESS_DIR / f"{HARNESS_PREFIX}_budget_accounting.csv",
    "repro_json": HARNESS_DIR / f"{HARNESS_PREFIX}_reproducibility_summary.json",
    "repro_md": HARNESS_DIR / f"{HARNESS_PREFIX}_reproducibility_summary.md",
}
FAKE_BANNER = (
    "HARNESS VALIDATION ONLY - produced by a deterministic fake model. "
    "These numbers are NOT scientific results and must not be cited."
)
FAKE_VERDICT = "HARNESS_VALIDATION_ONLY_NOT_A_SCIENTIFIC_RESULT"
FAKE_GENERATOR_MODEL = "fake/deterministic-generator-v1"
FAKE_JUDGE_MODEL = "fake/deterministic-judge-v1"

# Historical file names that Experiment 16 must never write to.
HISTORICAL_OUTPUT_PATTERN = re.compile(r"meno_j_(experiment_(?!16_)\d+|theory_study|wesad|literature|complete|falsification)")

QUESTIONS = {
    "Q1": "Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?",
    "Q2": "Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?",
    "Q3": "What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?",
}

CARD_LIST_FIELDS = ("mechanism_variables", "possible_confounders", "control_variables", "minimum_data_needed")
CARD_TEXT_FIELDS = (
    "hypothesis", "proposed_mechanism", "causal_path", "rival_explanation", "rival_prediction",
    "distinguishing_test", "effect_size_rationale", "testable_prediction", "failure_condition",
    "statistical_test_plan", "falsification_test",
)
CARD_FIELDS = (
    "hypothesis", "proposed_mechanism", "causal_path", "mechanism_variables", "possible_confounders",
    "control_variables", "rival_explanation", "rival_prediction", "distinguishing_test",
    "effect_size_expectation", "effect_size_rationale", "minimum_data_needed", "testable_prediction",
    "failure_condition", "statistical_test_plan", "falsification_test",
)
EFFECT_SIZES = {"small", "medium", "large", "unknown"}
JUDGE_EXTRA_FIELDS = ("rival_prediction_diverges", "failure_condition_operational")
CONTENT_LEAK = re.compile(r"meno|minos", re.IGNORECASE)
BLINDING_FORBIDDEN = re.compile(
    r"meno|minos|arm[_ ]?[ab]\b|baseline|\bv4\b|architecture|selector|candidate_id|\bS\d+-H\d+\b",
    re.IGNORECASE,
)

# --------------------------------------------------------------------------
# Preregistered protocol (frozen to disk before any run; hash-checked at run)
# --------------------------------------------------------------------------
PROTOCOL: dict[str, Any] = {
    "experiment_name": EXPERIMENT_16_NAME,
    "protocol_status": "FROZEN_BEFORE_ANY_EXPERIMENT_16_MODEL_CALL",
    "frozen_on": "2026-09-17",
    "naming_note": (
        "Requested as 'Experiment 8'. Numbered 16 because the historical record already contains "
        "Experiment 8 (rare-subgroup frontier) through Experiment 15. No historical file is touched."
    ),
    "research_question": (
        "If a multi-stage reasoning pipeline performs better than a simpler baseline, does the architecture "
        "itself deserve the credit once inference budget, sampling, retries, and evaluator passes are controlled?"
    ),
    "task_set": {
        "questions": QUESTIONS,
        "source": "Identical Q1-Q3 used by Experiments 1, 2 and 7 (run_v4_architecture_ablation.QUESTIONS).",
        "replicates_per_question": 3,
        "unit_of_analysis": "(question, replicate) pair; both arms run fresh on every unit",
    },
    "arms": {
        "A_minos_j_v4": {
            "implementation": "historical pipeline.run_v4_pipeline, unchanged, fresh Stage 4 (no reuse of historical checkpoints)",
            "stages": ["4 Dreamer", "4.1 Mechanism Builder", "4.2 Confounder/Rival Builder",
                       "4.3 Statistical Testability Builder (auto-splits into 2 batches on failure)",
                       "5 Strict Auditor (evaluator)", "6 Rival Matrix (PASS only)", "7 Falsification (PASS only)"],
            "final_deliverable": "hypotheses the Stage 5 auditor marked PASS, with their builds, rival row and falsification test",
        },
        "B_matched_budget_sample_and_select": {
            "implementation": "K independent one-shot calls, each producing 10 complete hypothesis cards with every field Arm A ends up with, then ONE selector/verifier call applying the same strict audit checklist and decision rules to the pooled candidates",
            "final_deliverable": "up to 10 distinct selected cards that the selector marked PASS",
            "not_handicapped_because": [
                "same model, temperature, max_tokens, system message, client and retry policy",
                "asked for the same final fields and the same quality requirements as Arm A's builders",
                "receives the same total token budget as Arm A on the same unit (K chosen by the budget controller)",
                "receives the same number of evaluator/verifier calls (1)",
                "gets to choose among 10*K sampled candidates, versus 10 for Arm A",
            ],
        },
    },
    "held_constant": {
        "underlying_model": "OPENROUTER_MODEL (single value for both arms; recorded per request, including provider-returned model id)",
        "model_settings": "historical llm_client: temperature 0.4, max_tokens 12000, same system message, same JSON-repair and retry policy",
        "retrieval_evidence": "none in either arm (the v4 pipeline has no retrieval stage); both arms receive only the research question",
        "task_inputs": "identical research question text",
    },
    "matched_compute_rule": {
        "budget_currency": "total tokens = provider-reported prompt_tokens + completion_tokens over every successful HTTP request of the arm, including JSON-repair requests; chars/4 estimate only if the provider omits usage (flagged)",
        "order": "Arm A runs first on a unit; its realized total T_A becomes Arm B's budget for that unit",
        "evaluator_parity": "Arm B makes exactly as many evaluator/verifier calls as Arm A made (1 per unit)",
        "controller": "Arm B keeps adding one-shot samples while the projected total (samples spent + estimated selector cost) after one more sample is closer to T_A than the projected total without it; at least 1 sample; hard cap K <= 2 * L_A",
        "selector_cost_estimate": "selector prompt template chars/4 + sum of sample completion tokens + Arm A's realized Stage 5 completion tokens",
        "tolerance": "a unit is budget-matched iff 0.85 <= T_B / T_A <= 1.15 and E_B == E_A",
        "reported_not_matched": ["logical calls", "HTTP attempts", "timeout/network/429 retries", "JSON repair requests", "sampled candidates", "cost (if provider returns it)", "wall-clock latency"],
        "failed_requests": "HTTP attempts that failed carry no token usage; they are counted as attempts in both arms",
        "judge_calls": "excluded from both arms' budgets (measurement, not inference) and reported separately",
    },
    "evaluation": {
        "judge": "blinded LLM judge using MINOS_J_JUDGE_MODEL, which must differ from the generator model",
        "normalization": "every final deliverable is converted to the identical 16-field card schema; arm-specific field names and IDs are removed",
        "blinding": "cards from both arms of a unit are pooled, given random opaque IDs, shuffled with a seed derived from the unit ID, and judged in mixed batches of 10; the card->arm key never enters a prompt; prompts are scanned for arm-revealing strings",
        "judge_checklist": [
            "variables_measurable", "causal_chain_valid", "base_rate_plausible", "confounders_identified",
            "effect_size_plausible", "data_requirements_clear", "mechanism_is_non_generic", "prediction_is_testable",
            "rival_prediction_diverges", "failure_condition_operational",
        ],
        "judge_validated_card": "all six historical CRITICAL_AUDIT_FIELDS true AND rival_prediction_diverges AND failure_condition_operational",
        "judge_retry": "one retry per judge batch on invalid output; otherwise the unit is marked JUDGE_FAILED",
    },
    "metrics": {
        "primary": "V = number of judge-validated cards in an arm's final deliverable (0-10); paired difference D = V_A - V_B per unit",
        "secondary": [
            "precision = V / reported survivors",
            "mean judge checklist fraction over reported cards",
            "within-arm near-duplicate rate (word-set Jaccard >= 0.6 on hypothesis text)",
            "mean card length in characters (verbosity confound)",
            "arm failure rate (pipeline or validation failure)",
            "per-question paired differences",
        ],
    },
    "falsification_criterion": {
        "statement": "If the matched-budget simple baseline performs similarly to or better than Minos-J within reasonable experimental variation, Experiment 16 does NOT support the claim that the Minos-J architecture itself is responsible for the gain.",
        "analysis_set": "units where both arms completed, the judge completed, and the budget was matched",
        "statistics": "mean D; paired bootstrap 95% CI (10000 resamples, seed 16); exact two-sided sign test on non-zero D",
        "practical_margin_delta": 1.0,
        "minimum_analysable_units": 6,
        "decisions": {
            "ARCHITECTURE_ADVANTAGE_SURVIVED": "mean D >= 1.0 AND bootstrap CI lower bound > 0",
            "BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED": "bootstrap CI upper bound < 0",
            "ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED": "any other outcome (CI includes 0, or mean D below the margin)",
            "INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS": "fewer than 6 analysable units, or more than one third of attempted units unmatched/failed",
        },
        "negative_results": "reported with the same prominence as positive results",
    },
    "seeds": {"bootstrap_seed": 16, "blinding_seed_derivation": "sha256('E16|' + unit_id)"},
}


def protocol_sha256() -> str:
    return hashlib.sha256(json.dumps(PROTOCOL, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _protocol_markdown() -> str:
    p = PROTOCOL
    m = p["matched_compute_rule"]
    f = p["falsification_criterion"]
    lines = [
        f"# {p['experiment_name']} — Preregistered Protocol", "",
        f"- Status: `{p['protocol_status']}`",
        f"- Frozen on: {p['frozen_on']}",
        f"- Protocol SHA-256 (canonical JSON): `{protocol_sha256()}`",
        f"- Naming: {p['naming_note']}", "",
        "## Research question", "", p["research_question"], "",
        "## Task set", "",
    ]
    lines += [f"- {k}: {v}" for k, v in QUESTIONS.items()]
    lines += [f"- Replicates per question: {p['task_set']['replicates_per_question']}", "",
              "## Arms", "",
              f"- A (Minos-J v4): {p['arms']['A_minos_j_v4']['implementation']}",
              f"- B (matched-budget sample-and-select): {p['arms']['B_matched_budget_sample_and_select']['implementation']}", "",
              "## Held constant", ""]
    lines += [f"- {k}: {v}" for k, v in p["held_constant"].items()]
    lines += ["", "## Matched-compute rule", ""]
    lines += [f"- {k}: {v}" for k, v in m.items() if not isinstance(v, list)]
    lines += [f"- reported but not matched: {', '.join(m['reported_not_matched'])}", "",
              "## Evaluation", ""]
    lines += [f"- {k}: {v if not isinstance(v, list) else ', '.join(v)}" for k, v in p["evaluation"].items()]
    lines += ["", "## Falsification criterion (fixed before any result)", "", f"- {f['statement']}",
              f"- Analysis set: {f['analysis_set']}", f"- Statistics: {f['statistics']}",
              f"- Practical margin: {f['practical_margin_delta']} judge-validated hypothesis", ""]
    lines += [f"- `{k}`: {v}" for k, v in f["decisions"].items()]
    lines.append("")
    return "\n".join(lines)


def write_protocol(force: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(PROTOCOL, ensure_ascii=False, indent=2) + "\n"
    if PROTOCOL_JSON.exists() and not force:
        existing = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
        if existing != PROTOCOL:
            raise SystemExit("Refusing to overwrite a different frozen protocol.")
        print(f"Protocol already frozen and identical: {PROTOCOL_JSON}")
        return
    PROTOCOL_JSON.write_text(payload, encoding="utf-8")
    PROTOCOL_MD.write_text(_protocol_markdown(), encoding="utf-8")
    print(f"Protocol frozen: {PROTOCOL_JSON} (sha256 {protocol_sha256()})")


def _require_frozen_protocol() -> None:
    if not PROTOCOL_JSON.exists():
        raise SystemExit("Protocol not frozen. Run with --write-protocol first.")
    if json.loads(PROTOCOL_JSON.read_text(encoding="utf-8")) != PROTOCOL:
        raise SystemExit("Frozen protocol on disk differs from the protocol in code; refusing to run.")


# --------------------------------------------------------------------------
# Environment and engine import
# --------------------------------------------------------------------------
def load_dotenv(path: Path) -> list[str]:
    """Minimal .env loader (no dependency). Never prints values."""
    loaded: list[str] = []
    if not path.exists():
        return loaded
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def import_engine():
    import llm_client  # noqa: WPS433  (historical, unchanged)
    import pipeline  # noqa: WPS433
    import prompts  # noqa: WPS433
    import schema  # noqa: WPS433
    return llm_client, pipeline, prompts, schema


def _approx_tokens(text: str) -> int:
    return int(math.ceil(len(text) / 4)) if text else 0


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# Metering (wraps historical llm_client._request_json without editing it)
# --------------------------------------------------------------------------
class Meter:
    def __init__(self, llm_client, ledger_path: Path):
        self.llm = llm_client
        self.ledger_path = ledger_path
        self.context: dict[str, Any] = {}
        self._original = llm_client._request_json
        self._seq = 0
        llm_client._request_json = self._wrapped

    def uninstall(self) -> None:
        self.llm._request_json = self._original

    @contextmanager
    def ctx(self, **kwargs):
        previous = dict(self.context)
        self.context.update(kwargs)
        try:
            yield
        finally:
            self.context = previous

    def _write(self, row: dict[str, Any]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def event(self, kind: str, **fields) -> None:
        self._seq += 1
        self._write({"event": kind, "seq": self._seq, **self.context, **fields})

    def _wrapped(self, messages):
        before = self.llm.get_retry_stats()
        prompt_text = "".join(str(m.get("content", "")) for m in messages)
        started = time.perf_counter()
        model = self.llm.OPENROUTER_MODEL
        try:
            data = self._original(messages)
        except Exception as exc:
            after = self.llm.get_retry_stats()
            self.event("request_failed", model_requested=model, error=type(exc).__name__,
                       **_retry_delta(before, after))
            raise
        after = self.llm.get_retry_stats()
        usage = data.get("usage") if isinstance(data, dict) else None
        content = ""
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            pass
        reported = isinstance(usage, dict) and "prompt_tokens" in usage and "completion_tokens" in usage
        prompt_tokens = int(usage["prompt_tokens"]) if reported else _approx_tokens(prompt_text)
        completion_tokens = int(usage["completion_tokens"]) if reported else _approx_tokens(str(content))
        cost = usage.get("cost") if isinstance(usage, dict) else None
        self.event(
            "request",
            model_requested=model,
            model_returned=data.get("model") if isinstance(data, dict) else None,
            is_json_repair=len(messages) > 2,
            usage_reported=reported,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            prompt_sha256=_sha256_text(prompt_text),
            latency_s=round(time.perf_counter() - started, 3),
            **_retry_delta(before, after),
        )
        return data


def _retry_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = ("http_attempts", "timeout_retries", "network_retries", "transient_http_retries",
            "invalid_response_json_retries", "invalid_response_shape_retries")
    return {k: after.get(k, 0) - before.get(k, 0) for k in keys}


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_budget(rows: list[dict[str, Any]], unit_id: str, arm: str) -> dict[str, Any]:
    reqs = [r for r in rows if r.get("unit_id") == unit_id and r.get("arm") == arm and r["event"] == "request"]
    fails = [r for r in rows if r.get("unit_id") == unit_id and r.get("arm") == arm and r["event"] == "request_failed"]
    logical = [r for r in rows if r.get("unit_id") == unit_id and r.get("arm") == arm and r["event"] == "logical_call"]
    both = reqs + fails
    costs = [r["cost"] for r in reqs if isinstance(r.get("cost"), (int, float))]
    return {
        "logical_calls": len(logical),
        "logical_calls_failed": sum(1 for r in logical if not r.get("ok")),
        "generator_calls": sum(1 for r in logical if r.get("role") == "generator"),
        "evaluator_calls": sum(1 for r in logical if r.get("role") == "evaluator"),
        "successful_requests": len(reqs),
        "failed_requests": len(fails),
        "json_repair_requests": sum(1 for r in reqs if r["is_json_repair"]),
        "http_attempts": sum(r.get("http_attempts", 0) for r in both),
        "timeout_retries": sum(r.get("timeout_retries", 0) for r in both),
        "network_retries": sum(r.get("network_retries", 0) for r in both),
        "transient_http_retries": sum(r.get("transient_http_retries", 0) for r in both),
        "malformed_envelope_retries": sum(r.get("invalid_response_json_retries", 0) + r.get("invalid_response_shape_retries", 0) for r in both),
        "prompt_tokens": sum(r["prompt_tokens"] for r in reqs),
        "completion_tokens": sum(r["completion_tokens"] for r in reqs),
        "total_tokens": sum(r["total_tokens"] for r in reqs),
        "requests_with_estimated_usage": sum(1 for r in reqs if not r["usage_reported"]),
        "cost_usd": round(sum(costs), 6) if costs else None,
        "cost_complete": bool(reqs) and len(costs) == len(reqs),
        "models_returned": sorted({str(r.get("model_returned")) for r in reqs}),
        "latency_s": round(sum(r.get("latency_s", 0.0) for r in reqs), 3),
    }


# --------------------------------------------------------------------------
# Arm B prompts and validation (new; Arm A uses historical prompts)
# --------------------------------------------------------------------------
def _card_schema_example() -> dict[str, Any]:
    card: dict[str, Any] = {"hypothesis_id": "H1"}
    for field in CARD_FIELDS:
        card[field] = [] if field in CARD_LIST_FIELDS else ""
    card["effect_size_expectation"] = "small | medium | large | unknown"
    return card


def baseline_sample_prompt(research_question: str, sample_index: int) -> str:
    schema = {"hypotheses": [_card_schema_example()]}
    return f"""One-shot Hypothesis Contract Generation (independent sample {sample_index})

Research question: {research_question}

Generate exactly 10 genuinely diverse hypotheses, ordered and identified H1 through H10. Cover distinct
subject-specific, sensor, physiological, temporal, labeling, stratification, and statistical possibilities
where scientifically defensible. Diversity matters more than safety.

For every hypothesis, directly write its complete, testable research contract:
- proposed_mechanism and causal_path: a specific directed causal path with named measurable variables
  (mechanism_variables), not an explanation that would apply unchanged to most problems in this domain;
- possible_confounders and control_variables: realistic confounders and explicit control logic;
- rival_explanation and rival_prediction: one boring, plausible rival whose prediction DIFFERS from the
  proposed mechanism's prediction; distinguishing_test: an observable result that separates them;
- effect_size_expectation: exactly one of small, medium, large, unknown (if unknown, say in
  effect_size_rationale exactly what data would estimate it); effect_size_rationale;
- minimum_data_needed: a non-empty list of concrete data requirements;
- testable_prediction: directional; failure_condition: an operational result that would count against the
  hypothesis; statistical_test_plan: a concrete test; falsification_test: the strongest test capable of
  proving the mechanism wrong, not merely finding an association.
Every list must contain at least one concrete non-empty string; every other field must be a non-empty string.

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{json.dumps(schema, ensure_ascii=False, indent=2)}
Do not add fields or prose outside the JSON."""


def validate_baseline_sample(payload: Any, schema_module) -> list[dict[str, Any]]:
    err = schema_module.PipelineValidationError
    if not isinstance(payload, dict) or set(payload) != {"hypotheses"}:
        raise err("Baseline sample must return exactly one top-level key: 'hypotheses'.")
    items = payload["hypotheses"]
    if not isinstance(items, list) or len(items) != 10:
        raise err(f"Baseline sample must contain exactly 10 hypotheses; got {len(items) if isinstance(items, list) else 'non-list'}.")
    expected = {"hypothesis_id", *CARD_FIELDS}
    ids = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or set(item) != expected:
            got = set(item) if isinstance(item, dict) else set()
            raise err(f"Baseline card {index} fields invalid; missing={sorted(expected - got)}, extra={sorted(got - expected)}.")
        for field in CARD_LIST_FIELDS:
            v = item[field]
            if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
                raise err(f"Baseline card {index}.{field} must be a non-empty string list.")
        for field in CARD_TEXT_FIELDS:
            if not isinstance(item[field], str) or not item[field].strip():
                raise err(f"Baseline card {index}.{field} must be a non-empty string.")
        es = item["effect_size_expectation"]
        if not isinstance(es, str) or es.lower() not in EFFECT_SIZES:
            raise err(f"Baseline card {index}.effect_size_expectation invalid.")
        item["effect_size_expectation"] = es.lower()
        ids.append(item["hypothesis_id"])
    if ids != [f"H{i}" for i in range(1, 11)]:
        raise err(f"Baseline hypothesis IDs must be H1..H10 in order; got {ids}.")
    return items


def selector_prompt(research_question: str, pool: list[dict[str, Any]], select_n: int, schema_module) -> str:
    audit_example = {"candidate_id": "S1-H1", "audit_decision": "PASS | REJECT | SALVAGEABLE"}
    for field in schema_module.AUDIT_BOOLEAN_FIELDS:
        audit_example[field] = True
    audit_example.update({"failure_points": [], "decision_reason": "", "salvage_note": ""})
    output_schema = {"selected_audits": [audit_example]}
    return f"""Selection and Strict Audit Pass

Research question: {research_question}

You receive {len(pool)} candidate hypothesis contracts from independent samples. Select exactly {select_n}
distinct candidates that together form the strongest, most diverse final set (do not select near-duplicates),
then audit each selected candidate independently and skeptically. Do not numerically score them. Do not
rubber-stamp.

Strict non-generic mechanism rule:
- A mechanism is generic if the same explanation would apply to most similar problems in this domain
  without modification.
- If it does not name a specific causal path, variable relationship, boundary condition, or domain-specific
  process, set mechanism_is_non_generic to false.
- If unsure, set it to false.

PASS is allowed only when every critical check is true: {json.dumps(list(schema_module.CRITICAL_AUDIT_FIELDS))}.
If one or two critical checks fail but the idea is concretely repairable, mark SALVAGEABLE and explain the
repair in salvage_note. If the mechanism is vague, untestable, statistically weak, or domain-generic, mark
REJECT. For PASS and REJECT, salvage_note may be an empty string.

failure_points must contain every and only checklist field whose boolean is false. The complete checklist is:
{json.dumps(list(schema_module.AUDIT_BOOLEAN_FIELDS))}

Every audit must include a candidate-specific, non-empty decision_reason.

Candidates:
{json.dumps(pool, ensure_ascii=False, indent=2)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per audit, one audit per
selected candidate, using candidate_id values exactly as given:
{json.dumps(output_schema, ensure_ascii=False, indent=2)}
Do not add fields or prose outside the JSON."""


def validate_selector(payload: Any, pool_ids: list[str], select_n: int, schema_module) -> list[dict[str, Any]]:
    err = schema_module.PipelineValidationError
    if not isinstance(payload, dict) or set(payload) != {"selected_audits"}:
        raise err("Selector must return exactly one top-level key: 'selected_audits'.")
    rows = payload["selected_audits"]
    if not isinstance(rows, list) or len(rows) != select_n:
        raise err(f"Selector must return exactly {select_n} audits.")
    ids = []
    converted = []
    for row in rows:
        if not isinstance(row, dict) or "candidate_id" not in row:
            raise err("Selector audit missing candidate_id.")
        cid = row["candidate_id"]
        if cid not in pool_ids:
            raise err(f"Selector returned unknown candidate_id {cid}.")
        ids.append(cid)
        audit = {k: v for k, v in row.items() if k != "candidate_id"}
        audit["hypothesis_id"] = cid
        converted.append(audit)
    if len(set(ids)) != len(ids):
        raise err("Selector returned duplicate candidate_id values.")
    # Reuse the historical audit validator and decision rules verbatim.
    schema_module.validate_audits({"audits": converted}, [{"hypothesis_id": cid} for cid in ids])
    return converted


# --------------------------------------------------------------------------
# Budget controller for Arm B
# --------------------------------------------------------------------------
def choose_next_sample(target: float, spent_gen: float, sample_costs: list[float],
                       sample_completions: list[float], selector_template_tokens: float,
                       evaluator_completion_estimate: float, k_cap: int) -> bool:
    """Return True if Arm B should draw one more sample."""
    k = len(sample_costs)
    if k == 0:
        return True
    if k >= k_cap:
        return False
    mean_cost = sum(sample_costs) / k
    mean_completion = sum(sample_completions) / k
    sel_now = selector_template_tokens + sum(sample_completions) + evaluator_completion_estimate
    sel_next = sel_now + mean_completion
    proj_now = spent_gen + sel_now
    proj_next = spent_gen + mean_cost + sel_next
    return abs(proj_next - target) < abs(proj_now - target)


# --------------------------------------------------------------------------
# Card normalization, blinding, judging
# --------------------------------------------------------------------------
def cards_from_arm_a(report: dict[str, Any]) -> list[dict[str, Any]]:
    pass_ids = [a["hypothesis_id"] for a in report["stage_5_audits"] if a["audit_decision"] == "PASS"]
    by = lambda key: {row["hypothesis_id"]: row for row in report[key]}  # noqa: E731
    hyp, mech = by("stage_4_hypotheses"), by("stage_4_1_mechanism_builder")
    conf, stat = by("stage_4_2_confounder_rival_builder"), by("stage_4_3_statistical_testability_builder")
    rival, fals = by("stage_6_rival_prediction_matrix"), by("stage_7_falsification_tests")
    cards = []
    for hid in sorted(pass_ids, key=lambda x: int(x[1:])):
        h, m, c, s, r, f = hyp[hid], mech[hid], conf[hid], stat[hid], rival[hid], fals[hid]
        cards.append({
            "source_ref": hid,
            "card": {
                "hypothesis": h["hypothesis"],
                "proposed_mechanism": h["proposed_mechanism"],
                "causal_path": m["causal_path"],
                "mechanism_variables": m["mechanism_variables"],
                "possible_confounders": c["possible_confounders"],
                "control_variables": c["control_variables"],
                "rival_explanation": r["rival_explanation"],
                "rival_prediction": r["rival_prediction"],
                "distinguishing_test": r["distinguishing_test"],
                "effect_size_expectation": s["effect_size_expectation"],
                "effect_size_rationale": s["effect_size_rationale"],
                "minimum_data_needed": s["minimum_data_needed"],
                "testable_prediction": s["testable_prediction"],
                "failure_condition": f["failure_condition"],
                "statistical_test_plan": s["statistical_test_plan"],
                "falsification_test": f["strongest_falsification_test"],
            },
        })
    return cards


def cards_from_arm_b(pool: dict[str, dict[str, Any]], audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"source_ref": a["hypothesis_id"], "card": {k: pool[a["hypothesis_id"]][k] for k in CARD_FIELDS}}
        for a in audits if a["audit_decision"] == "PASS"
    ]


def blind_cards(unit_id: str, arm_cards: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    rng = random.Random(int(_sha256_text("E16|" + unit_id)[:16], 16))
    pooled = [(arm, item) for arm in sorted(arm_cards) for item in arm_cards[arm]]
    rng.shuffle(pooled)
    used: set[str] = set()
    blinded, key = [], {}
    for arm, item in pooled:
        cid = "C" + format(rng.getrandbits(32), "08x")
        while cid in used:
            cid = "C" + format(rng.getrandbits(32), "08x")
        used.add(cid)
        blinded.append({"card_id": cid, **item["card"]})
        key[cid] = {"arm": arm, "source_ref": item["source_ref"]}
    return blinded, key


def judge_prompt(research_question: str, cards: list[dict[str, Any]], schema_module) -> str:
    fields = list(schema_module.AUDIT_BOOLEAN_FIELDS) + list(JUDGE_EXTRA_FIELDS)
    example = {"card_id": "C00000000", **{f: True for f in fields}, "judge_reason": ""}
    return f"""Independent Blind Review of Research Hypothesis Cards

Research question: {research_question}

Each card below is a proposed hypothesis with its test plan. Cards come from an undisclosed mixture of
sources and are presented in random order. Judge every card on its own merits, skeptically, without
comparing lengths or styles. Do not rubber-stamp.

For each card set each check to true only if clearly satisfied:
- variables_measurable: the named variables can actually be measured with plausible data.
- causal_chain_valid: the causal path is coherent and directed.
- base_rate_plausible: the proposed effect is plausible given what is known in this domain.
- confounders_identified: realistic confounders and control logic are specified.
- effect_size_plausible: the stated effect size and its rationale are reasonable.
- data_requirements_clear: minimum data needs are concrete.
- mechanism_is_non_generic: the mechanism names a specific causal path, variable relationship, boundary
  condition, or domain-specific process; if the same explanation would fit most similar problems, or if
  unsure, set false.
- prediction_is_testable: the prediction is directional and testable.
- rival_prediction_diverges: the rival's prediction genuinely differs and the distinguishing test separates them.
- failure_condition_operational: the failure condition is a concrete observable result that would count
  against the hypothesis.

Cards:
{json.dumps(cards, ensure_ascii=False, indent=2)}

Return valid JSON only: one judgment per card, card_id copied exactly, with exactly these fields:
{json.dumps({"judgments": [example]}, ensure_ascii=False, indent=2)}
judge_reason must be a short non-empty card-specific reason. Do not add fields or prose outside the JSON."""


def validate_judgments(payload: Any, card_ids: list[str], schema_module) -> list[dict[str, Any]]:
    err = schema_module.PipelineValidationError
    fields = list(schema_module.AUDIT_BOOLEAN_FIELDS) + list(JUDGE_EXTRA_FIELDS)
    if not isinstance(payload, dict) or set(payload) != {"judgments"}:
        raise err("Judge must return exactly one top-level key: 'judgments'.")
    rows = payload["judgments"]
    if not isinstance(rows, list) or len(rows) != len(card_ids):
        raise err("Judge returned the wrong number of judgments.")
    expected = {"card_id", "judge_reason", *fields}
    seen = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected:
            raise err("Judge row has invalid fields.")
        if any(type(row[f]) is not bool for f in fields):
            raise err("Judge booleans must be JSON booleans.")
        if not isinstance(row["judge_reason"], str) or not row["judge_reason"].strip():
            raise err("Judge reason must be non-empty.")
        seen.append(row["card_id"])
    if sorted(seen) != sorted(card_ids):
        raise err("Judge card_id set mismatch.")
    return rows


def judge_validated(row: dict[str, Any], schema_module) -> bool:
    return all(row[f] for f in schema_module.CRITICAL_AUDIT_FIELDS) and all(row[f] for f in JUDGE_EXTRA_FIELDS)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def near_duplicate_rate(texts: list[str], threshold: float = 0.6) -> float:
    if len(texts) < 2:
        return 0.0
    dup = 0
    sets = [_words(t) for t in texts]
    for i in range(len(sets)):
        for j in range(i):
            union = sets[i] | sets[j]
            if union and len(sets[i] & sets[j]) / len(union) >= threshold:
                dup += 1
                break
    return dup / len(texts)


# --------------------------------------------------------------------------
# Statistics and verdict
# --------------------------------------------------------------------------
def paired_bootstrap_ci(diffs: list[float], resamples: int = 10000, seed: int = 16) -> tuple[float, float]:
    if not diffs:
        return (math.nan, math.nan)
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return (means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1])


def sign_test_p(diffs: list[float]) -> float:
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def decide_verdict(diffs: list[float], attempted_units: int) -> dict[str, Any]:
    crit = PROTOCOL["falsification_criterion"]
    n = len(diffs)
    mean = sum(diffs) / n if n else math.nan
    lo, hi = paired_bootstrap_ci(diffs, seed=PROTOCOL["seeds"]["bootstrap_seed"])
    result = {"analysable_units": n, "attempted_units": attempted_units, "mean_difference_A_minus_B": mean,
              "bootstrap_ci95": [lo, hi], "sign_test_p_two_sided": sign_test_p(diffs),
              "units_A_better": sum(d > 0 for d in diffs), "units_B_better": sum(d < 0 for d in diffs),
              "units_tied": sum(d == 0 for d in diffs)}
    if n < crit["minimum_analysable_units"] or (attempted_units and (attempted_units - n) > attempted_units / 3):
        verdict = "INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS"
    elif mean >= crit["practical_margin_delta"] and lo > 0:
        verdict = "ARCHITECTURE_ADVANTAGE_SURVIVED"
    elif hi < 0:
        verdict = "BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED"
    else:
        verdict = "ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED"
    result["verdict"] = verdict
    result["architecture_survived_falsification_test"] = verdict == "ARCHITECTURE_ADVANTAGE_SURVIVED"
    return result


# --------------------------------------------------------------------------
# Unit execution
# --------------------------------------------------------------------------
def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stage_from_prompt(prompt: str) -> tuple[str, str]:
    head = prompt.lstrip().splitlines()[0]
    table = [
        ("Stage 4.1", "stage_4_1_mechanism_builder", "generator"),
        ("Stage 4.2", "stage_4_2_confounder_rival_builder", "generator"),
        ("Stage 4.3", "stage_4_3_statistical_testability_builder", "generator"),
        ("Stage 4 ", "stage_4_dreamer", "generator"),
        ("Stage 5", "stage_5_auditor", "evaluator"),
        ("Stage 6", "stage_6_rival_matrix", "generator"),
        ("Stage 7", "stage_7_falsification", "generator"),
    ]
    for prefix, stage, role in table:
        if head.startswith(prefix):
            return stage, role
    return "unknown", "generator"


def make_caller(llm_client, meter: Meter, fixed_stage: str | None = None, fixed_role: str | None = None) -> Callable[[str], dict]:
    def caller(prompt: str) -> dict:
        stage, role = (fixed_stage, fixed_role) if fixed_stage else _stage_from_prompt(prompt)
        with meter.ctx(stage=stage, role=role):
            try:
                result = llm_client.call_llm(prompt)
            except Exception as exc:
                meter.event("logical_call", ok=False, error=type(exc).__name__)
                raise
            meter.event("logical_call", ok=True)
            return result
    return caller


@contextmanager
def use_model(llm_client, model: str):
    previous = llm_client.OPENROUTER_MODEL
    llm_client.OPENROUTER_MODEL = model
    try:
        yield
    finally:
        llm_client.OPENROUTER_MODEL = previous


def run_arm_a(engine, meter, unit_dir: Path, question: str, model: str) -> dict[str, Any]:
    llm_client, pipeline, _, _ = engine
    done = _read_json(unit_dir / "arm_a_report.json")
    if done is not None:
        return done
    with meter.ctx(arm="A"):
        report = pipeline.run_v4_pipeline(
            make_caller(llm_client, meter), model=model, research_question=question,
            checkpoint_dir=unit_dir / "arm_a_stages",
        )
    _write_json(unit_dir / "arm_a_report.json", report)
    return report


def run_arm_b(engine, meter, unit_dir: Path, question: str, target_tokens: int,
              a_budget: dict[str, Any], a_stage5_completion: int) -> dict[str, Any]:
    llm_client, _, _, schema_module = engine
    done = _read_json(unit_dir / "arm_b_result.json")
    if done is not None:
        return done
    k_cap = max(2, 2 * a_budget["logical_calls"])
    template_tokens = _approx_tokens(selector_prompt(question, [], 10, schema_module))
    samples_dir = unit_dir / "arm_b_samples"
    sample_costs: list[float] = []
    sample_completions: list[float] = []
    pool: dict[str, dict[str, Any]] = {}
    sample_log = []
    k = 0
    with meter.ctx(arm="B"):
        while choose_next_sample(target_tokens, sum(sample_costs), sample_costs, sample_completions,
                                 template_tokens, a_stage5_completion, k_cap):
            k += 1
            ckpt = samples_dir / f"sample_{k:02d}.json"
            record = _read_json(ckpt)
            if record is None:
                rows_before = len(read_ledger(meter.ledger_path))
                valid, error_name, cards = True, None, []
                try:
                    payload = make_caller(llm_client, meter, "baseline_sample", "generator")(baseline_sample_prompt(question, k))
                    cards = validate_baseline_sample(payload, schema_module)
                except Exception as exc:  # spent budget still counts
                    valid, error_name = False, f"{type(exc).__name__}: {str(exc)[:200]}"
                new_rows = [r for r in read_ledger(meter.ledger_path)[rows_before:] if r["event"] == "request"]
                record = {"sample_index": k, "valid": valid, "error": error_name, "cards": cards,
                          "total_tokens": sum(r["total_tokens"] for r in new_rows),
                          "completion_tokens": sum(r["completion_tokens"] for r in new_rows)}
                _write_json(ckpt, record)
            sample_costs.append(record["total_tokens"])
            sample_completions.append(record["completion_tokens"] if record["valid"] else 0)
            sample_log.append({k2: record[k2] for k2 in ("sample_index", "valid", "error", "total_tokens", "completion_tokens")})
            if record["valid"]:
                for card in record["cards"]:
                    pool[f"S{k}-{card['hypothesis_id']}"] = {k2: card[k2] for k2 in CARD_FIELDS}
        pool_list = [{"candidate_id": cid, **card} for cid, card in pool.items()]
        select_n = min(10, len(pool_list))
        audits: list[dict[str, Any]] = []
        selector_error = None
        if select_n:
            sel_ckpt = unit_dir / "arm_b_selector.json"
            audits = _read_json(sel_ckpt)
            if audits is None:
                try:
                    payload = make_caller(llm_client, meter, "selector_audit", "evaluator")(
                        selector_prompt(question, pool_list, select_n, schema_module))
                    audits = validate_selector(payload, list(pool), select_n, schema_module)
                    _write_json(sel_ckpt, audits)
                except Exception as exc:
                    selector_error = f"{type(exc).__name__}: {str(exc)[:200]}"
                    audits = []
    result = {"samples": sample_log, "k_samples": k, "k_cap": k_cap, "pool_size": len(pool),
              "selected": [a["hypothesis_id"] for a in audits], "audits": audits,
              "selector_error": selector_error,
              "cards": cards_from_arm_b(pool, audits)}
    if selector_error is None:
        _write_json(unit_dir / "arm_b_result.json", result)
    return result


def judge_unit(engine, meter, unit_dir: Path, unit_id: str, question: str,
               arm_cards: dict[str, list[dict[str, Any]]], judge_model: str) -> dict[str, Any]:
    llm_client, _, _, schema_module = engine
    done = _read_json(unit_dir / "judge_result.json")
    if done is not None:
        return done
    blinded, key = blind_cards(unit_id, arm_cards)
    batch_size = 10
    judgments: list[dict[str, Any]] = []
    leak_hits: list[str] = []
    prompts_meta = []
    status = "OK"
    with meter.ctx(arm="JUDGE"), use_model(llm_client, judge_model):
        for b in range(0, len(blinded), batch_size):
            batch = blinded[b:b + batch_size]
            prompt = judge_prompt(question, batch, schema_module)
            cards_text = json.dumps(batch, ensure_ascii=False)
            template = prompt.replace(cards_text_pretty := json.dumps(batch, ensure_ascii=False, indent=2), "<CARDS>")
            if cards_text_pretty not in prompt:
                raise RuntimeError("judge prompt construction changed; blinding scan cannot isolate cards")
            template_hits = sorted(set(m.group(0) for m in BLINDING_FORBIDDEN.finditer(template)))
            template_hits += sorted(set(k for k in json.dumps([sorted(c) for c in batch]).split('"') if BLINDING_FORBIDDEN.search(k)))
            if template_hits:
                raise RuntimeError(f"Blinding violation in judge prompt template/field names: {template_hits}")
            leak_hits += sorted(set(m.group(0) for m in CONTENT_LEAK.finditer(cards_text_pretty)))
            prompts_meta.append({"batch": b // batch_size, "card_ids": [c["card_id"] for c in batch],
                                 "prompt_sha256": _sha256_text(prompt), "cards_sha256": _sha256_text(cards_text)})
            rows = None
            for attempt in range(2):
                try:
                    payload = make_caller(llm_client, meter, "blinded_judge", "judge")(prompt)
                    rows = validate_judgments(payload, [c["card_id"] for c in batch], schema_module)
                    break
                except Exception as exc:
                    meter.event("judge_invalid", batch=b // batch_size, attempt=attempt, error=type(exc).__name__)
            if rows is None:
                status = "JUDGE_FAILED"
                break
            judgments += rows
    out = {"status": status, "key": key, "blinded_cards": blinded, "judgments": judgments,
           "batches": prompts_meta, "blinding_leak_hits": sorted(set(leak_hits))}
    if status == "OK":
        _write_json(unit_dir / "judge_result.json", out)
    return out


def arm_metrics(arm: str, cards: list[dict[str, Any]], judge: dict[str, Any], schema_module) -> dict[str, Any]:
    by_id = {j["card_id"]: j for j in judge["judgments"]}
    ids = [cid for cid, k in judge["key"].items() if k["arm"] == arm]
    fields = list(schema_module.AUDIT_BOOLEAN_FIELDS) + list(JUDGE_EXTRA_FIELDS)
    validated = sum(judge_validated(by_id[c], schema_module) for c in ids if c in by_id)
    fractions = [sum(by_id[c][f] for f in fields) / len(fields) for c in ids if c in by_id]
    texts = [c["card"]["hypothesis"] for c in cards]
    return {
        "reported_survivors": len(cards),
        "judge_validated": validated,
        "precision": validated / len(cards) if cards else None,
        "mean_checklist_fraction": sum(fractions) / len(fractions) if fractions else None,
        "near_duplicate_rate": near_duplicate_rate(texts),
        "mean_card_chars": (sum(len(json.dumps(c["card"], ensure_ascii=False)) for c in cards) / len(cards)) if cards else None,
    }


def run_unit(engine, meter, paths, qid: str, replicate: int, model: str, judge_model: str) -> dict[str, Any]:
    _, _, _, schema_module = engine
    unit_id = f"{qid}-r{replicate}"
    unit_dir = paths["checkpoints"] / unit_id
    question = QUESTIONS[qid]
    row: dict[str, Any] = {"unit_id": unit_id, "question_id": qid, "replicate": replicate,
                           "generator_model": model, "judge_model": judge_model, "anomalies": []}
    with meter.ctx(unit_id=unit_id):
        try:
            report_a = run_arm_a(engine, meter, unit_dir, question, model)
        except Exception as exc:
            row.update(status="ARM_A_FAILED", error=f"{type(exc).__name__}: {str(exc)[:300]}")
            row["budget_A"] = summarize_budget(read_ledger(meter.ledger_path), unit_id, "A")
            return row
        ledger = read_ledger(meter.ledger_path)
        budget_a = summarize_budget(ledger, unit_id, "A")
        stage5 = [r for r in ledger if r.get("unit_id") == unit_id and r.get("arm") == "A"
                  and r["event"] == "request" and r.get("stage") == "stage_5_auditor"]
        a_stage5_completion = sum(r["completion_tokens"] for r in stage5)
        result_b = run_arm_b(engine, meter, unit_dir, question, budget_a["total_tokens"], budget_a, a_stage5_completion)
        ledger = read_ledger(meter.ledger_path)
        budget_b = summarize_budget(ledger, unit_id, "B")
        row.update(budget_A=budget_a, budget_B=budget_b,
                   arm_a_pass_ids=[a["hypothesis_id"] for a in report_a["stage_5_audits"] if a["audit_decision"] == "PASS"],
                   arm_a_stage_4_3_chunked=(unit_dir / "arm_a_stages" / "stage_4_3_batch_a.json").exists(),
                   arm_b_samples=result_b["samples"], arm_b_k=result_b["k_samples"], arm_b_k_cap=result_b["k_cap"],
                   arm_b_pool_size=result_b["pool_size"], arm_b_selected=result_b["selected"])
        row["candidates_sampled_A"] = len(report_a["stage_4_hypotheses"])
        row["candidates_sampled_B"] = result_b["pool_size"]
        ratio = budget_b["total_tokens"] / budget_a["total_tokens"] if budget_a["total_tokens"] else math.nan
        tol = (0.85, 1.15)
        row["token_ratio_B_over_A"] = ratio
        row["evaluator_parity"] = budget_a["evaluator_calls"] == budget_b["evaluator_calls"]
        row["budget_matched"] = bool(tol[0] <= ratio <= tol[1] and row["evaluator_parity"])
        invalid_samples = [s for s in result_b["samples"] if not s["valid"]]
        if invalid_samples:
            row["anomalies"].append(f"{len(invalid_samples)} Arm B sample(s) failed validation (tokens still charged)")
        if budget_a["requests_with_estimated_usage"] or budget_b["requests_with_estimated_usage"]:
            row["anomalies"].append("provider omitted usage on some requests; chars/4 estimate used")
        if not row["budget_matched"]:
            row["anomalies"].append(f"budget not matched (ratio {ratio:.3f}, evaluator parity {row['evaluator_parity']})")
        if result_b["selector_error"]:
            row.update(status="ARM_B_FAILED", error=result_b["selector_error"])
            return row
        arm_cards = {"A": cards_from_arm_a(report_a), "B": result_b["cards"]}
        judge = judge_unit(engine, meter, unit_dir, unit_id, question, arm_cards, judge_model)
        row["judge_budget"] = summarize_budget(read_ledger(meter.ledger_path), unit_id, "JUDGE")
        row["judge_batches"] = judge["batches"]
        row["blinding_leak_hits"] = judge["blinding_leak_hits"]
        if judge["blinding_leak_hits"]:
            row["anomalies"].append(f"card text mentions the architecture name (possible unblinding): {judge['blinding_leak_hits']}")
        if judge["status"] != "OK":
            row.update(status="JUDGE_FAILED")
            return row
        row["metrics_A"] = arm_metrics("A", arm_cards["A"], judge, schema_module)
        row["metrics_B"] = arm_metrics("B", arm_cards["B"], judge, schema_module)
        row["difference_A_minus_B"] = row["metrics_A"]["judge_validated"] - row["metrics_B"]["judge_validated"]
        row["status"] = "COMPLETE"
        row["_judge"] = judge
        row["_cards"] = arm_cards
    return row


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
BUDGET_FIELDS = ("logical_calls", "generator_calls", "evaluator_calls", "successful_requests", "failed_requests",
                 "json_repair_requests", "http_attempts", "timeout_retries", "network_retries",
                 "transient_http_retries", "malformed_envelope_retries", "prompt_tokens", "completion_tokens",
                 "total_tokens", "requests_with_estimated_usage", "cost_usd")


def _mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def build_report(units: list[dict[str, Any]], mode: str, model: str, judge_model: str,
                 commands: list[str], started: str) -> dict[str, Any]:
    complete = [u for u in units if u["status"] == "COMPLETE"]
    analysable = [u for u in complete if u["budget_matched"]]
    diffs = [float(u["difference_A_minus_B"]) for u in analysable]
    stats = decide_verdict(diffs, len(units))
    per_question = {}
    for qid in QUESTIONS:
        d = [float(u["difference_A_minus_B"]) for u in analysable if u["question_id"] == qid]
        per_question[qid] = {"units": len(d), "mean_difference_A_minus_B": _mean(d)}
    sensitivity = [float(u["difference_A_minus_B"]) for u in complete]
    def agg(arm: str, key: str, rows):
        return _mean([u[f"metrics_{arm}"][key] for u in rows])
    aggregate = {arm: {k: agg(arm, k, analysable) for k in
                       ("reported_survivors", "judge_validated", "precision", "mean_checklist_fraction",
                        "near_duplicate_rate", "mean_card_chars")} for arm in ("A", "B")}
    budget_totals = {}
    for arm in ("A", "B", "JUDGE"):
        key = "judge_budget" if arm == "JUDGE" else f"budget_{arm}"
        rows = [u[key] for u in units if key in u]
        budget_totals[arm] = {f: (sum((r[f] or 0) for r in rows) if rows else 0) for f in BUDGET_FIELDS}
    report = {
        "experiment_name": EXPERIMENT_16_NAME,
        "mode": mode,
        "generated_at_utc": started,
        "provenance": ("Generated by run_experiment_16_matched_compute.py (written 2026-09-17). Not part of the "
                       "historical Experiment 1-15 record; no historical output was read-modified or regenerated."),
        "protocol_sha256": protocol_sha256(),
        "generator_model": model,
        "judge_model": judge_model,
        "commands": commands,
        "matched_compute_rule": PROTOCOL["matched_compute_rule"],
        "falsification_criterion": PROTOCOL["falsification_criterion"],
        "unit_status_counts": {s: sum(u["status"] == s for u in units) for s in sorted({u["status"] for u in units})},
        "budget_matched_units": sum(1 for u in complete if u["budget_matched"]),
        "aggregate_metrics_analysis_set": aggregate,
        "budget_totals": budget_totals,
        "per_question": per_question,
        "statistics": stats,
        "sensitivity_including_unmatched_complete_units": {
            "units": len(sensitivity), "mean_difference_A_minus_B": _mean(sensitivity),
            "bootstrap_ci95": list(paired_bootstrap_ci(sensitivity)) if sensitivity else None,
        },
        "anomalies": [{"unit_id": u["unit_id"], "status": u["status"], "error": u.get("error"), "notes": u["anomalies"]}
                      for u in units if u["anomalies"] or u["status"] != "COMPLETE"],
        "units": [{k: v for k, v in u.items() if not k.startswith("_")} for u in units],
    }
    if mode == "fake_harness_validation":
        report["banner"] = FAKE_BANNER
        report["verdict_logic_exercised"] = stats["verdict"]
        report["statistics"] = {**stats, "verdict": FAKE_VERDICT, "architecture_survived_falsification_test": None}
    report["verdict"] = report["statistics"]["verdict"]
    return report


def _fmt(v, nd=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{v:.{nd}f}" if isinstance(v, float) else str(v)


def report_markdown(report: dict[str, Any]) -> str:
    fake = report["mode"] == "fake_harness_validation"
    s = report["statistics"]
    L = []
    title = f"# {report['experiment_name']}" + (" — HARNESS VALIDATION ONLY (fake model)" if fake else "")
    L += [title, ""]
    if fake:
        L += [f"> **{FAKE_BANNER}**", ""]
    L += ["## Setup", "",
          f"- Mode: `{report['mode']}`", f"- Generator model (both arms): `{report['generator_model']}`",
          f"- Judge model: `{report['judge_model']}`", f"- Protocol SHA-256: `{report['protocol_sha256']}`",
          f"- Generated (UTC): {report['generated_at_utc']}", f"- Provenance: {report['provenance']}",
          f"- Protocol deviation: {report.get('protocol_deviation') or 'none'}", "",
          "## Commands", ""] + [f"- `{c}`" for c in report["commands"]] + ["",
          "## Matched-compute rule", ""]
    L += [f"- {k}: {v}" for k, v in report["matched_compute_rule"].items() if not isinstance(v, list)]
    L += ["", "## Unit status", ""] + [f"- {k}: {v}" for k, v in report["unit_status_counts"].items()]
    L += [f"- Budget-matched complete units: {report['budget_matched_units']}", "",
          "## Compute-budget accounting (totals)", "",
          "| Field | Arm A | Arm B | Judge (excluded) |", "|---|---:|---:|---:|"]
    for f in BUDGET_FIELDS:
        L.append(f"| {f} | {_fmt(report['budget_totals']['A'][f])} | {_fmt(report['budget_totals']['B'][f])} | {_fmt(report['budget_totals']['JUDGE'][f])} |")
    L += ["", "## Per-unit budget and outcome", "",
          "| Unit | Status | A calls | B calls | A tokens | B tokens | B/A | Eval A/B | K | Matched | V_A | V_B | D |",
          "|---|---|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|"]
    for u in report["units"]:
        ba, bb = u.get("budget_A", {}), u.get("budget_B", {})
        ma, mb = u.get("metrics_A", {}), u.get("metrics_B", {})
        L.append(f"| {u['unit_id']} | {u['status']} | {ba.get('logical_calls', 'n/a')} | {bb.get('logical_calls', 'n/a')} | "
                 f"{ba.get('total_tokens', 'n/a')} | {bb.get('total_tokens', 'n/a')} | {_fmt(u.get('token_ratio_B_over_A'))} | "
                 f"{ba.get('evaluator_calls', '?')}/{bb.get('evaluator_calls', '?')} | {u.get('arm_b_k', 'n/a')} | "
                 f"{u.get('budget_matched', 'n/a')} | {ma.get('judge_validated', 'n/a')} | {mb.get('judge_validated', 'n/a')} | "
                 f"{u.get('difference_A_minus_B', 'n/a')} |")
    L += ["", "## Aggregate metrics (analysis set)", "", "| Metric | Arm A (Minos-J v4) | Arm B (matched baseline) |", "|---|---:|---:|"]
    for k in report["aggregate_metrics_analysis_set"]["A"]:
        L.append(f"| {k} | {_fmt(report['aggregate_metrics_analysis_set']['A'][k])} | {_fmt(report['aggregate_metrics_analysis_set']['B'][k])} |")
    L += ["", "## Minos-J vs baseline", "",
          f"- Analysable units: {s['analysable_units']} of {s['attempted_units']}",
          f"- Mean D (A - B, judge-validated hypotheses): {_fmt(s['mean_difference_A_minus_B'])}",
          f"- Bootstrap 95% CI: [{_fmt(s['bootstrap_ci95'][0])}, {_fmt(s['bootstrap_ci95'][1])}]",
          f"- Sign test p (two-sided): {_fmt(s['sign_test_p_two_sided'])}",
          f"- Units A better / B better / tied: {s['units_A_better']} / {s['units_B_better']} / {s['units_tied']}", ""]
    L += [f"- {q}: units {v['units']}, mean D {_fmt(v['mean_difference_A_minus_B'])}" for q, v in report["per_question"].items()]
    L += ["", "## Falsification test", "", f"- Criterion: {report['falsification_criterion']['statement']}",
          f"- **Verdict: `{report['verdict']}`**"]
    if fake:
        L += [f"- Verdict logic was exercised (internal value `{report['verdict_logic_exercised']}`) but is meaningless with a fake model."]
    L += ["", "## Anomalies and failure cases", ""]
    L += [f"- {a['unit_id']} ({a['status']}): {a['error'] or ''} {'; '.join(a['notes'])}" for a in report["anomalies"]] or ["- None."]
    L += ["", "## What this experiment does NOT show", "",
          "- It covers three conformal-prediction/WESAD questions only; it says nothing about other domains.",
          "- The judge is an LLM; judge-validated means 'passes a blinded checklist', not 'scientifically true'.",
          "- Arm B is one fair baseline (sample-and-select); other budget-matched baselines (e.g. iterative self-refine) are untested.",
          "- Token matching is approximate (tolerance 0.85-1.15) and depends on provider-reported usage.",
          "- A null result does not show the stages are useless; it shows the gain is not separable from compute at this sample size.",
          ""]
    return "\n".join(L)


def write_outputs(paths, report: dict[str, Any], units: list[dict[str, Any]], ledger_path: Path) -> None:
    for key in ("report_json", "report_md", "raw_units", "judgments", "aggregate_csv", "budget_csv", "repro_json", "repro_md"):
        if HISTORICAL_OUTPUT_PATTERN.search(paths[key].name):
            raise RuntimeError(f"Refusing to write a historical-looking path: {paths[key]}")
    _write_json(paths["report_json"], report)
    paths["report_md"].write_text(report_markdown(report), encoding="utf-8")
    with paths["raw_units"].open("w", encoding="utf-8") as h:
        for u in units:
            h.write(json.dumps({k: v for k, v in u.items() if k != "_judge"}, ensure_ascii=False, sort_keys=True) + "\n")
    with paths["judgments"].open("w", encoding="utf-8") as h:
        for u in units:
            j = u.get("_judge")
            if not j:
                continue
            by = {r["card_id"]: r for r in j["judgments"]}
            for card in j["blinded_cards"]:
                cid = card["card_id"]
                h.write(json.dumps({"unit_id": u["unit_id"], "card_id": cid, **j["key"][cid],
                                    "judgment": by.get(cid), "card": card}, ensure_ascii=False, sort_keys=True) + "\n")
    paths["raw_requests"].write_text(ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else "", encoding="utf-8")
    with paths["aggregate_csv"].open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        cols = ["reported_survivors", "judge_validated", "precision", "mean_checklist_fraction", "near_duplicate_rate", "mean_card_chars"]
        w.writerow(["unit_id", "question_id", "replicate", "status", "budget_matched", "token_ratio_B_over_A"]
                   + [f"A_{c}" for c in cols] + [f"B_{c}" for c in cols] + ["difference_A_minus_B"])
        for u in units:
            ma, mb = u.get("metrics_A", {}), u.get("metrics_B", {})
            w.writerow([u["unit_id"], u["question_id"], u["replicate"], u["status"], u.get("budget_matched"),
                        u.get("token_ratio_B_over_A")] + [ma.get(c) for c in cols] + [mb.get(c) for c in cols]
                       + [u.get("difference_A_minus_B")])
    with paths["budget_csv"].open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["unit_id", "arm"] + list(BUDGET_FIELDS) + ["candidates_sampled"])
        for u in units:
            for arm, key in (("A", "budget_A"), ("B", "budget_B"), ("JUDGE", "judge_budget")):
                if key in u:
                    cand = u.get(f"candidates_sampled_{arm}", "")
                    w.writerow([u["unit_id"], arm] + [u[key][f] for f in BUDGET_FIELDS] + [cand])
    repro = {
        "experiment_name": EXPERIMENT_16_NAME,
        "mode": report["mode"],
        "protocol_sha256": report["protocol_sha256"],
        "runner_sha256": _sha256_file(Path(__file__)),
        "engine_sha256": {n: _sha256_file(PROJECT_DIR / n) for n in ("llm_client.py", "pipeline.py", "prompts.py", "schema.py")},
        "generator_model": report["generator_model"],
        "judge_model": report["judge_model"],
        "report_json_sha256": _sha256_file(paths["report_json"]),
        "raw_units_sha256": _sha256_file(paths["raw_units"]),
        "raw_requests_sha256": _sha256_file(paths["raw_requests"]),
        "commands": report["commands"],
        "historical_outputs_modified": False,
        "note": FAKE_BANNER if report["mode"] == "fake_harness_validation" else "Real-model run.",
    }
    _write_json(paths["repro_json"], repro)
    paths["repro_md"].write_text("\n".join([f"# {EXPERIMENT_16_NAME} — Reproducibility Summary", ""]
                                          + ([f"> **{FAKE_BANNER}**", ""] if report["mode"] == "fake_harness_validation" else [])
                                          + [f"- {k}: `{v}`" for k, v in repro.items()]) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Deterministic fake transport (harness validation only)
# --------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpenRouter:
    """Deterministic stand-in for https://openrouter.ai used only by --fake-harness-validation.

    Fault injection (by global request counter): an HTTP 429 on attempt 3, invalid JSON content on
    served response 6 (exercises the historical JSON-repair path), one wrong-count baseline sample,
    and one response without usage (exercises the estimate path).
    """

    def __init__(self):
        self.attempts = 0
        self.served = 0
        self.issued_prompt_tokens = 0
        self.issued_completion_tokens = 0
        self.log: list[dict[str, Any]] = []
        self.bad_baseline_done = False
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)

    @staticmethod
    def _h(*parts: Any) -> int:
        return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)

    def urlopen(self, req, timeout=None):  # noqa: ARG002
        from urllib import error as urlerror
        self.attempts += 1
        body = json.loads(req.data.decode("utf-8"))
        if self.attempts == 3:
            hdrs = email.message.Message()
            hdrs["Retry-After"] = "0"
            raise urlerror.HTTPError(req.full_url, 429, "Too Many Requests", hdrs, io.BytesIO(b'{"error":{"message":"rate limited"}}'))
        self.served += 1
        messages = body["messages"]
        prompt = messages[1]["content"]
        repair = len(messages) > 2
        content = self._respond(prompt, body["model"], repair)
        if self.served == 6 and not repair:
            content = "Sure! Here is the JSON: " + content  # invalid JSON -> repair request
        prompt_tokens = sum(_approx_tokens(m["content"]) for m in messages)
        completion_tokens = _approx_tokens(content)
        envelope: dict[str, Any] = {"id": f"fake-{self.served}", "model": body["model"],
                                    "choices": [{"message": {"role": "assistant", "content": content}}]}
        if self.served != 9:
            envelope["usage"] = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                                 "total_tokens": prompt_tokens + completion_tokens,
                                 "cost": round((prompt_tokens + completion_tokens) * 1e-7, 8)}
        self.issued_prompt_tokens += prompt_tokens
        self.issued_completion_tokens += completion_tokens
        self.log.append({"served": self.served, "model": body["model"], "repair": repair,
                         "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                         "usage_included": "usage" in envelope, "head": prompt.splitlines()[0][:60]})
        return FakeResponse(json.dumps(envelope).encode("utf-8"))

    # -- content builders ------------------------------------------------
    def _ids(self, text: str, pattern: str) -> list[str]:
        seen: list[str] = []
        for m in re.finditer(pattern, text):
            if m.group(1) not in seen:
                seen.append(m.group(1))
        return seen

    def _section(self, prompt: str, marker: str) -> str:
        idx = prompt.find(marker)
        return prompt[idx:] if idx >= 0 else prompt

    def _audit(self, key: str, salt: str, id_field: str, ident: str, fields, critical) -> dict[str, Any]:
        r = self._h(salt, key, ident) % 10
        failing: list[str] = []
        if r >= 8:
            failing = list(critical)[:3]
            decision = "REJECT"
        elif r >= 6:
            failing = [list(critical)[r % len(critical)]]
            decision = "SALVAGEABLE"
        else:
            decision = "PASS"
        row = {id_field: ident, "audit_decision": decision}
        row.update({f: f not in failing for f in fields})
        row.update({"failure_points": [f for f in fields if f in failing],
                    "decision_reason": f"Fake audit reason for {ident}.",
                    "salvage_note": "Fake repair." if decision == "SALVAGEABLE" else ""})
        return row

    def _respond(self, prompt: str, model: str, repair: bool) -> str:
        import schema as S
        head = prompt.lstrip().splitlines()[0]
        nonce = self.served
        text = lambda tag, i: f"Fake {tag} {i} (n{self._h(nonce, tag, i) % 997}) with a specific variable relation."  # noqa: E731
        if head.startswith("Stage 4 —"):
            return json.dumps({"hypotheses": [{"hypothesis_id": f"H{i}", "hypothesis": text("hypothesis", i),
                                               "proposed_mechanism": text("mechanism", i), "core_assumption": text("assumption", i),
                                               "knowledge_gap_addressed": text("gap", i), "status": "SPECULATIVE"} for i in range(1, 11)]})
        if head.startswith(("Stage 4.1", "Stage 4.2", "Stage 4.3")):
            ids = self._ids(self._section(prompt, "Stage 4 hypotheses:"), r'"hypothesis_id": "(H\d+)"')
            if head.startswith("Stage 4.1"):
                return json.dumps({"mechanism_builds": [{"hypothesis_id": h, "mechanism_variables": [text("var", h)],
                                   "causal_path": text("path", h), "expected_direction": "increase",
                                   "domain_specific_boundary_conditions": [text("boundary", h)],
                                   "measurable_outcomes": [text("outcome", h)], "mechanism_builder_notes": "fake"} for h in ids]})
            if head.startswith("Stage 4.2"):
                return json.dumps({"confounder_rival_builds": [{"hypothesis_id": h, "possible_confounders": [text("confounder", h)],
                                   "control_variables": [text("control", h)], "boring_rival_explanations": [text("rival", h)],
                                   "rival_prediction": text("rival prediction", h), "distinguishing_condition": text("distinguish", h),
                                   "confounder_rival_notes": "fake"} for h in ids]})
            return json.dumps({"statistical_testability_builds": [{"hypothesis_id": h, "effect_size_expectation": "Medium",
                               "effect_size_rationale": text("rationale", h), "minimum_data_needed": [text("data", h)],
                               "testable_prediction": text("prediction", h), "failure_condition": text("failure", h),
                               "statistical_test_plan": text("plan", h), "statistical_testability_notes": "fake"} for h in ids]})
        if head.startswith("Stage 5"):
            ids = self._ids(self._section(prompt, "to audit:"), r'"hypothesis_id": "(H\d+)"')
            return json.dumps({"audits": [self._audit(prompt[:400], "A5", "hypothesis_id", h, S.AUDIT_BOOLEAN_FIELDS, S.CRITICAL_AUDIT_FIELDS) for h in ids]})
        if head.startswith(("Stage 6", "Stage 7")):
            ids = self._ids(self._section(prompt, "PASS hypotheses:"), r'"hypothesis_id": "(H\d+)"')
            if head.startswith("Stage 6"):
                return json.dumps({"rival_prediction_matrix": [{"hypothesis_id": h, "meno_j_hypothesis": text("h", h),
                                   "meno_j_prediction": text("p", h), "rival_explanation": text("rival", h),
                                   "rival_prediction": text("rp", h), "distinguishing_test": text("dt", h),
                                   "what_result_supports_meno_j": text("s", h), "what_result_supports_rival": text("sr", h)} for h in ids]})
            return json.dumps({"falsification_tests": [{"hypothesis_id": h, "strongest_falsification_test": text("ft", h),
                               "failure_condition": text("fc", h), "minimum_data_needed": text("md", h),
                               "most_likely_false_positive_risk": text("fp", h), "most_likely_false_negative_risk": text("fn", h)} for h in ids]})
        if head.startswith("One-shot Hypothesis Contract Generation"):
            count = 10
            if not self.bad_baseline_done and "(independent sample 2)" in head:
                self.bad_baseline_done = True
                count = 9  # deliberate validation failure
            cards = []
            for i in range(1, count + 1):
                card = {"hypothesis_id": f"H{i}"}
                for f in CARD_FIELDS:
                    card[f] = [text(f, i)] if f in CARD_LIST_FIELDS else text(f, i)
                card["effect_size_expectation"] = "small"
                cards.append(card)
            return json.dumps({"hypotheses": cards})
        if head.startswith("Selection and Strict Audit Pass"):
            ids = self._ids(prompt, r'"candidate_id": "(S\d+-H\d+)"')
            m = re.search(r"Select exactly (\d+)", prompt)
            n = int(m.group(1)) if m else 10
            chosen = sorted(ids, key=lambda c: self._h("sel", prompt[:200], c))[:n]
            return json.dumps({"selected_audits": [self._audit(prompt[:400], "SEL", "candidate_id", c, S.AUDIT_BOOLEAN_FIELDS, S.CRITICAL_AUDIT_FIELDS) for c in chosen]})
        if head.startswith("Independent Blind Review"):
            cards_part = prompt.split("\nCards:\n", 1)[1].split("\nReturn valid JSON only", 1)[0]
            ids = self._ids(cards_part, r'"card_id": "(C[0-9a-f]{8})"')
            fields = list(S.AUDIT_BOOLEAN_FIELDS) + list(JUDGE_EXTRA_FIELDS)
            rows = []
            for c in ids:
                r = self._h("J", c)
                row = {"card_id": c}
                row.update({f: ((r >> k) & 7) != 0 for k, f in enumerate(fields)})
                row["judge_reason"] = f"Fake judge reason for {c}."
                rows.append(row)
            return json.dumps({"judgments": rows})
        raise AssertionError(f"FakeOpenRouter received an unknown prompt: {head!r}")


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------
def run_experiment(mode: str, replicates: int, question_ids: list[str], argv: list[str]) -> dict[str, Any]:
    deviation = (replicates != PROTOCOL["task_set"]["replicates_per_question"] or question_ids != list(QUESTIONS))
    fake = mode == "fake_harness_validation"
    paths = FAKE_PATHS if fake else REAL_PATHS
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if not fake else "FAKE-RUN-TIMESTAMP-OMITTED"
    fake_server = None
    if fake:
        os.environ["OPENROUTER_API_KEY"] = "fake-key-for-harness-validation"
        os.environ["OPENROUTER_MODEL"] = FAKE_GENERATOR_MODEL
        judge_model = FAKE_JUDGE_MODEL
    else:
        load_dotenv(PROJECT_DIR / ".env")
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise SystemExit("OPENROUTER_API_KEY is not set (put it in .env). See RUN_LATER.md.")
        judge_model = os.environ.get("MINOS_J_JUDGE_MODEL", "")
        if not judge_model:
            raise SystemExit("MINOS_J_JUDGE_MODEL is not set. See RUN_LATER.md.")
    engine = import_engine()
    llm_client = engine[0]
    model = llm_client.OPENROUTER_MODEL
    if fake:
        # llm_client read the key at import; make sure the fake values are active.
        llm_client.OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
        llm_client.OPENROUTER_MODEL = model = FAKE_GENERATOR_MODEL
        fake_server = FakeOpenRouter()
        saved_patches = (llm_client.request.urlopen, llm_client.time.sleep)
        llm_client.request.urlopen = fake_server.urlopen
        llm_client.time.sleep = fake_server.sleep
        import shutil
        for p in (paths["checkpoints"],):
            if p.exists():
                shutil.rmtree(p)
    if judge_model == model:
        raise SystemExit("Judge model must differ from the generator model.")
    ledger_path = paths["checkpoints"] / "request_ledger.jsonl"
    meter = Meter(llm_client, ledger_path)
    units = []
    try:
        for replicate in range(1, replicates + 1):
            for qid in question_ids:
                print(f"[E16{' FAKE' if fake else ''}] unit {qid}-r{replicate}", flush=True)
                units.append(run_unit(engine, meter, paths, qid, replicate, model, judge_model))
                print(f"    status={units[-1]['status']} matched={units[-1].get('budget_matched')} "
                      f"D={units[-1].get('difference_A_minus_B')}", flush=True)
    finally:
        meter.uninstall()
        if fake:
            llm_client.request.urlopen, llm_client.time.sleep = saved_patches
    command = "python " + " ".join([Path(__file__).name] + argv)
    report = build_report(units, mode, model, judge_model, [command], started)
    report["protocol_deviation"] = (
        f"replicates={replicates}, questions={question_ids} differ from the preregistered design" if deviation else None)
    if fake:
        report["fake_transport"] = {
            "http_attempts": fake_server.attempts, "served": fake_server.served,
            "issued_prompt_tokens": fake_server.issued_prompt_tokens,
            "issued_completion_tokens": fake_server.issued_completion_tokens,
            "responses_without_usage": sum(1 for r in fake_server.log if not r["usage_included"]),
            "sleeps_requested": fake_server.sleeps,
            "served_by_model": {m: sum(1 for r in fake_server.log if r["model"] == m) for m in sorted({r["model"] for r in fake_server.log})},
        }
    write_outputs(paths, report, units, ledger_path)
    print(f"Verdict: {report['verdict']}")
    print(f"Report: {paths['report_md']}")
    return report


def preflight() -> None:
    """Configuration check for a real run. Spends no tokens and never prints secrets."""
    from urllib import request as urlrequest
    loaded = load_dotenv(PROJECT_DIR / ".env")
    problems = []
    print(f".env found: {(PROJECT_DIR / '.env').exists()} (variables loaded: {', '.join(sorted(loaded)) or 'none'})")
    if not os.environ.get("OPENROUTER_API_KEY"):
        problems.append("OPENROUTER_API_KEY missing")
    model = os.environ.get("OPENROUTER_MODEL", "")
    judge = os.environ.get("MINOS_J_JUDGE_MODEL", "")
    print(f"Generator model: {model or '(unset -> historical default in schema.DEFAULT_MODEL)'}")
    print(f"Judge model: {judge or '(unset)'}")
    if not judge:
        problems.append("MINOS_J_JUDGE_MODEL missing")
    engine = import_engine()
    if judge and judge == engine[0].OPENROUTER_MODEL:
        problems.append("judge model equals generator model")
    try:
        with urlrequest.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as resp:
            ids = {m["id"] for m in json.loads(resp.read().decode("utf-8")).get("data", [])}
        for label, mid in (("generator", engine[0].OPENROUTER_MODEL), ("judge", judge)):
            if mid and mid not in ids:
                problems.append(f"{label} model '{mid}' not in OpenRouter's public model list")
        print(f"OpenRouter reachable: yes ({len(ids)} models listed)")
    except Exception as exc:  # network policy, DNS, etc.
        problems.append(f"OpenRouter not reachable: {type(exc).__name__}")
    for name in ("llm_client.py", "pipeline.py", "prompts.py", "schema.py"):
        print(f"{name} sha256 {_sha256_file(PROJECT_DIR / name)}")
    print("PREFLIGHT OK" if not problems else "PREFLIGHT FAILED: " + "; ".join(problems))
    if problems:
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=EXPERIMENT_16_NAME)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-protocol", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--fake-harness-validation", action="store_true")
    group.add_argument("--preflight", action="store_true", help="check config and reachability; no tokens spent")
    parser.add_argument("--replicates", type=int, default=PROTOCOL["task_set"]["replicates_per_question"])
    parser.add_argument("--questions", default="Q1,Q2,Q3")
    args = parser.parse_args(argv)
    qids = [q.strip() for q in args.questions.split(",") if q.strip()]
    unknown = set(qids) - set(QUESTIONS)
    if unknown:
        raise SystemExit(f"Unknown question ids: {sorted(unknown)}")
    if args.write_protocol:
        write_protocol()
        return
    _require_frozen_protocol()
    if args.preflight:
        preflight()
        return
    if args.run:
        if args.replicates != PROTOCOL["task_set"]["replicates_per_question"] or qids != list(QUESTIONS):
            print("WARNING: replicates/questions differ from the preregistered design; the report will record a protocol deviation.")
        run_experiment("real", args.replicates, qids, argv)
    else:
        run_experiment("fake_harness_validation", args.replicates, qids, argv)


if __name__ == "__main__":
    main()
