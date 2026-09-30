"""Experiment 18 preregistered protocol: builder, renderer and freeze/verify.

``python e18_protocol.py --write-draft``  writes protocol.json + PROTOCOL.md with status DRAFT (no hash file).
``python e18_protocol.py --freeze``       sets status FROZEN and writes PROTOCOL.sha256 (refuses if a
                                          different frozen protocol already exists).
``python e18_protocol.py --verify``       recomputes everything from code/tasks and checks the frozen hash.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import e18_prompts as P
import e18_tasks as T
import e18_transport as X
from e18_common import E18_DIR, SOURCE_DIR, TASKS_DIR, atomic_write_json, atomic_write_text, canonical_sha256, sha256_file, sha256_text

PROTOCOL_JSON = E18_DIR / "protocol.json"
PROTOCOL_MD = E18_DIR / "PROTOCOL.md"
PROTOCOL_SHA = E18_DIR / "PROTOCOL.sha256"
CODE_FILES = ("e18_common.py", "e18_tasks.py", "e18_prompts.py", "e18_transport.py", "e18_runner.py",
              "e18_analysis.py", "e18_protocol.py", "e18_validate_results.py", "e18_validate_harness.py")
N_MAIN = T.CASES_PER_MECHANISM_MAIN * len(T.MECHANISM_IDS)
PRACTICAL_MARGIN = 0.10
COMPUTE_PARITY_LIMIT = 1.20
BOOTSTRAP = {"resamples": 10000, "seed": 18}


def build(status: str = "DRAFT") -> dict[str, Any]:
    manifest = json.loads((TASKS_DIR / "manifest.json").read_text(encoding="utf-8"))
    prompts = {f"{a}{c}": P.INSTRUCTIONS[(a, c)] for (a, c) in P.INSTRUCTIONS}
    return {
        "experiment_name": "Minos-J Experiment 18: Does explicit falsification, rather than compute or rival enumeration, improve mechanism identification?",
        "protocol_status": status,
        "protocol_version": 1,
        "research_question": (
            "With the same model, identical information, the same number of model calls and approximately matched "
            "measured tokens, does an explicit falsification loop (rival mechanisms -> discriminating predictions -> "
            "test against evidence -> eliminate) identify the planted mechanism more reliably than generic "
            "self-critique and revision? Secondary: if it helps, is the gain due to testing discriminating predictions "
            "rather than merely generating rival hypotheses?"
        ),
        "hypotheses": {
            "H1_primary": {"parameter": "delta_AC = P(correct | A) - P(correct | C), paired over cases",
                           "null": "delta_AC = 0 (exact McNemar, two-sided)",
                           "alternative": "delta_AC != 0",
                           "effect_of_interest": f"delta_AC >= +{PRACTICAL_MARGIN:.2f} (10 percentage points)"},
            "H2_mechanistic": {"parameter": "delta_AD = P(correct | A) - P(correct | D)",
                               "claim_tested": "the benefit comes from explicitly testing discriminating predictions, not from enumerating rivals"},
            "H3_decoy_resistance": {"parameter": "delta_AC on decoy cases minus delta_AC on non-decoy cases",
                                    "claim_tested": "falsification specifically resists persuasive but misleading evidence"},
        },
        "primary_endpoint": "exact mechanism-identification accuracy; paired difference Accuracy(A) - Accuracy(C) over all main cases (intention-to-treat: a failed trial counts as incorrect)",
        "secondary_endpoints": [
            "S1 A vs D paired accuracy difference (exact McNemar) [Holm family]",
            "S2 A vs B paired accuracy difference (exact McNemar) [Holm family]",
            "S3 A vs C on decoy cases (exact McNemar) [Holm family]",
            "S4 A vs C on non-decoy cases (exact McNemar) [Holm family]",
            "S5 decoy-vs-non-decoy difference in delta_AC (paired-case bootstrap CI; estimate, not in Holm family)",
            "S6 multi-class Brier score per arm on completed trials (normalized probabilities over six mechanisms)",
            "S7 trial failure rate per arm, split into output failures and infrastructure failures",
            "S8 measured tokens per arm (input, cache-creation, cache-read, output, total) and per-call means",
            "S9 calls completed per arm",
            "S10 wall-clock latency per arm (engineering measure only; no inference)",
            "S11 raw accuracy of every arm, overall and by decoy status and by mechanism (descriptive)",
        ],
        "arms": {
            "A": {"name": "explicit falsification", "calls": 3, "procedure": "rivals + discriminating predictions -> test each prediction against evidence and eliminate -> final answer"},
            "C": {"name": "generic self-critique", "calls": 3, "procedure": "initial diagnosis -> generic critique -> revised final answer; no prediction table or elimination"},
            "D": {"name": "rivals without falsification", "calls": 3, "procedure": "same number of rivals as A, with rationales -> holistic plausibility weighing/ranking without prediction tests -> final answer"},
            "B": {"name": "single pass", "calls": 1, "procedure": "read evidence -> final answer (secondary efficiency/reference baseline)"},
            "primary_comparison": "A vs C",
            "instructions_verbatim": prompts,
            "instructions_sha256": canonical_sha256(prompts),
            "system_message": P.SYSTEM_MESSAGE,
            "common_header": P.COMMON_HEADER,
            "output_line": P.OUTPUT_LINE,
            "n_rivals": P.N_RIVALS,
            "schemas_sha256": canonical_sha256({f"{a}{c}": v for (a, c), v in P.SCHEMAS.items()}),
            "prompt_assembly": "COMMON_HEADER + mechanism vocabulary + evidence packet + this trial's previous-step outputs (verbatim JSON) + step instruction + output line",
            "arm_order": "per case, the four arms run in a seeded random order: sha256('E18|arm-order|' + case_id)",
        },
        "task_set": {
            "generator_version": T.GENERATOR_VERSION,
            "generator_sha256": manifest["generator_sha256"],
            "vocabulary_sha256": manifest["vocabulary_sha256"],
            "mechanisms": T.MECHANISM_IDS,
            "main": {k: manifest["main"][k] for k in ("seed", "difficulty", "n_cases", "counts", "public_sha256",
                                                     "answer_key_sha256", "case_ids_sha256", "packet_hashes_sha256", "reference_solvers")},
            "pilot": {k: manifest["pilot"][k] for k in ("seed", "difficulty", "n_cases", "public_sha256", "answer_key_sha256", "case_ids_sha256")},
            "construction": (
                "Each case plants one mechanism. For every mechanism the packet shows a marker (subgroup vs reference), "
                "coverage after that mechanism's intervention, and a 4-point coverage series. The planted mechanism satisfies "
                "both discriminating predictions (intervention restores coverage; series rises). Decoy cases add a different "
                "mechanism with a more abnormal marker that satisfies exactly one prediction, on that dimension up to "
                f"{1.05 + 0.30 * T.DEFAULT_DIFFICULTY:.2f}x the planted value. Non-decoy cases add a milder distractor marker. "
                f"Cases are resampled until the ideal joint falsifier identifies the planted mechanism with margin >= {T.ORACLE_MARGIN}."
            ),
            "balance": f"{T.CASES_PER_MECHANISM_MAIN} cases per mechanism (half decoy); decoy mechanism and decoy dimension rotate across cases",
            "display_order": "mechanism rows shuffled per case with a seeded RNG (identical for all arms)",
        },
        "sample_size": {
            "n_main_cases": N_MAIN,
            "n_trials": N_MAIN * 4,
            "rationale": (
                "Exact McNemar power for delta_AC = +0.10 (alpha 0.05, two-sided) and probability of ruling out +0.10 "
                "(95% CI upper bound < 0.10) when delta_AC = 0, by discordant-pair rate psi: "
                "n=60 -> power 0.19-0.40, rule-out 0.26-0.52 (psi 0.35-0.15): not informative. "
                "n=120 -> power 0.40-0.79, rule-out 0.46-0.81. n=180 -> power 0.58-0.94, rule-out 0.62-0.93. "
                "n=240 -> power 0.72-0.98, rule-out 0.75-0.98. 180 was chosen as the smallest size giving a majority chance of "
                "a decisive answer across plausible psi while remaining feasible on a Claude Pro subscription (about 1,800 calls)."
            ),
            "assumptions": [
                "discordant-pair rate between A and C of 0.15-0.35 (same model, similar procedures; not yet measured)",
                "cases are exchangeable draws from the frozen generator",
                "secondary comparisons (A vs D, A vs B, decoy subsets) are underpowered relative to the primary and are interpreted as estimates",
            ],
            "fixed": "Sample size cannot change after the freeze for any reason related to observed treatment results.",
        },
        "inclusion_exclusion": {
            "included": "all main cases; every arm-trial counts (intention-to-treat)",
            "excluded": "none. Pilot cases are a separate held-out set and never enter the main analysis.",
            "per_protocol_sensitivity": "primary estimate recomputed on cases where both A and C completed without failure",
        },
        "models": {
            "reasoner": X.GENERATOR_MODEL,
            "judge": "none. Correctness is a deterministic string comparison of the final mechanism_id against the hidden answer key.",
            "identity_recording": "model_returned (modelUsage key) and Claude Code CLI version are recorded on every attempt; any attempt returning a different model is an integrity violation that halts the run",
        },
        "blinding_and_key_isolation": (
            "Answer keys live in separate files that the runner never loads during inference. build_prompt rejects any case object "
            "containing key fields. Prompts are hashed and scanned for key fields in validation. No LLM ever sees the answer key or scores output."
        ),
        "inference_settings": {
            "transport": "claude -p (Claude Code CLI), Claude subscription OAuth (authMethod=claude.ai); no API key, no OpenRouter",
            "flags": "--model claude-sonnet-5 --effort low --output-format json --tools '' --strict-mcp-config --setting-sources '' --disable-slash-commands --no-session-persistence --system-prompt <fixed> --json-schema <per call>",
            "effort": X.EFFORT,
            "max_output_tokens_per_call": X.MAX_OUTPUT_TOKENS,
            "temperature": "not exposed by the Claude Code CLI; provider default, identical for all arms (not claimed to be controlled)",
            "timeout_seconds_per_attempt": X.TIMEOUT_SECONDS,
        },
        "compute_accounting": {
            "measured_tokens": "input + cache_creation_input + cache_read_input + output tokens as reported by the provider for EVERY attempt, including error envelopes and repair calls",
            "reported_separately": ["input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens",
                                    "measured_total_tokens", "fixed CLI overhead estimate", "calls attempted/completed", "wall-clock latency"],
            "fixed_cli_overhead": "estimated once per process session by a non-experimental calibration probe with the same flags and a trivial schema; stored in calibration.jsonl, never in the ledger or dataset",
            "matching": "A and C are matched exactly on number of calls (3), output cap, information and revision opportunities. Tokens are not forced equal; they are measured.",
            "compute_parity_gate": f"R = sum measured tokens(A) / sum measured tokens(C) over all main trials. A positive A>C result supports the causal claim only if R <= {COMPUTE_PARITY_LIMIT:.2f}. A null or negative result for A remains informative whatever R is. R and the output-token-only ratio are always reported.",
        },
        "failure_definitions": {
            "output_failure": "after the single allowed repair, a call's output still fails its schema or semantic validation (or the structured-output/output-cap error recurs); the trial ends FAILED_OUTPUT and scores incorrect",
            "infrastructure_failure": "transient errors persist beyond 4 retries or an unclassified CLI error occurs; the trial ends FAILED_INFRA and scores incorrect (ITT), reported separately",
            "not_a_failure": "subscription usage limit or login problem: the run PAUSES; nothing is recorded against the trial",
        },
        "retry_policy": {
            "transient": "at most 4 retries per call (timeouts, HTTP 429 without a limit message, 5xx, 529, non-JSON CLI exit), exponential backoff",
            "repair": "exactly one repair call per logical call when output is invalid; the repair prompt is the original prompt plus a fixed sentence naming the validation error; identical for every arm",
            "semantic_retries_for_wrong_answers": "none: a valid but wrong answer is never retried",
        },
        "usage_limit_handling": "HTTP 429/limit messages -> QuotaPause (BaseException): current trial is left incomplete with its completed call checkpoints intact, a session_paused ledger event is written, the process exits 75, and the identical command resumes it later",
        "crash_handling": "attempt_started without attempt_finished = orphan attempt; recorded at the next session start as orphan_attempt_recorded; the trial resumes from its last completed call checkpoint; orphan tokens are unknown and reported",
        "checkpoint_semantics": {
            "call_checkpoint": "work/<set>/trials/<case>/<arm>/call_<k>.json written atomically after a call's validated output; reused on resume",
            "terminal_marker": "trial_result.json (COMPLETE | FAILED_OUTPUT | FAILED_INFRA) written atomically; a trial with a terminal marker is never executed again",
            "ledger": "append-only JSONL with fsync; unique monotonic seq; never edited",
            "locks": "work/<set>/run.lock with holder PID; second process exits 73",
            "overwrite_protection": "if results/<set>_report.json exists, --run refuses",
            "corruption": "any unreadable checkpoint or ledger line stops the run for operator review (exit 2); nothing is deleted",
        },
        "stopping_criteria": {
            "planned": "all main cases x all four arms reach terminal markers",
            "no_interim_efficacy_analysis": "no outcome is computed before all trials are terminal",
            "infrastructure_halt": "if >= 5 of the last 40 terminal trials are FAILED_INFRA, the run halts (exit 76) for review and a documented amendment",
            "identity_halt": "any model_returned different from the frozen model halts the run",
        },
        "statistical_analysis": {
            "primary": "delta_AC with 95% paired-case bootstrap percentile CI (10,000 resamples, seed 18); exact two-sided McNemar test on discordant pairs; report b = #(A correct, C wrong), c = #(A wrong, C correct), accuracies of all arms",
            "sensitivity": ["per-protocol estimate (both A and C completed)", "Newcombe hybrid-score CI for paired proportions"],
            "secondary_multiplicity": "Holm correction across S1-S4 at familywise alpha 0.05",
            "brier": "sum_k (p_k - y_k)^2 over six mechanisms, normalized probabilities, completed trials only; mean per arm with bootstrap CI",
            "effect_sizes": "all differences in percentage points with 95% CI; odds ratio b/c for McNemar comparisons",
            "no_p_value_only_interpretation": "decisions use the effect estimate and CI per the decision rules; p-values are reported alongside",
        },
        "decision_rules": {
            "order": "evaluate top to bottom; first matching rule gives the primary verdict",
            "rules": [
                ["INCONCLUSIVE_INCOMPLETE", "fewer than 95% of main cases have terminal A and C trials, or FAILED_INFRA exceeds 10% of A or C trials"],
                ["C_SUPERIOR", "95% CI upper bound of delta_AC < 0"],
                ["NO_PRACTICALLY_MEANINGFUL_ADVANTAGE", "95% CI upper bound of delta_AC < +0.10 (strong evidence against a practically meaningful falsification advantage)"],
                ["FALSIFICATION_ADVANTAGE_SUPPORTED", f"delta_AC >= +0.10 AND CI lower bound > 0 AND McNemar p < 0.05 AND compute gate R <= {COMPUTE_PARITY_LIMIT:.2f}"],
                ["ADVANTAGE_BUT_COMPUTE_UNMATCHED", f"the supported criteria hold except R > {COMPUTE_PARITY_LIMIT:.2f}: cannot support the causal claim"],
                ["POSITIVE_BELOW_MARGIN_OR_UNCERTAIN", "CI lower bound > 0 but delta_AC < +0.10, or CI includes both 0 and +0.10: direction or size unresolved"],
                ["INCONCLUSIVE", "anything else"],
            ],
            "interpretation_rules": [
                "If A and D are materially indistinguishable (S1 CI includes 0 and |delta_AD| < 0.05) while both exceed C, that supports 'considering rivals, not explicit falsification, does the useful work'.",
                "If A shows no particular advantage on decoy cases (S5 estimate <= 0 or its CI includes 0), that weakens the claim that falsification resists persuasive misleading evidence.",
                "A vs B informs efficiency only; it cannot establish the mechanism because B has fewer calls.",
                "No rule may be changed after results are visible.",
            ],
        },
        "success_criteria": "FALSIFICATION_ADVANTAGE_SUPPORTED",
        "falsification_criteria": ["C_SUPERIOR", "NO_PRACTICALLY_MEANINGFUL_ADVANTAGE"],
        "pilot_policy": {
            "set": "12 held-out pilot cases (separate seed, 2 per mechanism, 1 decoy each); never part of the main dataset",
            "purposes": ["infrastructure", "answer schema", "solvability", "floor/ceiling detection", "token accounting", "crash/resume behavior"],
            "forbidden": ["selecting cases", "tuning prompts from arm differences", "changing scoring", "redefining endpoints", "inspecting treatment differences to tune Arm A"],
            "difficulty_rule": "Compute pooled accuracy over ALL pilot trials of ALL arms together (arm identity ignored). If pooled > 0.85, raise difficulty by 0.25 (max 1.0); if pooled < 0.40, lower by 0.25 (min 0.0); otherwise keep 0.5. At most one adjustment. Any change regenerates the untouched main set with the same seed and requires re-freezing (new protocol hash) before main inference.",
            "infrastructure_fixes": "documented in AMENDMENTS.md with re-freeze before the main study if any frozen field changes",
        },
        "deviation_procedure": (
            "Any post-freeze change is recorded in AMENDMENTS.md with timestamp, reason, exact code/config change, affected units, "
            "possible bias for each arm, and validity of prior observations. Scientific fields (questions, arms, prompts, tasks, n, endpoints, "
            "analysis, decision rules) cannot change after main-study inference begins."
        ),
        "code_sha256": {name: sha256_file(SOURCE_DIR / name) for name in CODE_FILES if (SOURCE_DIR / name).exists()},
        "task_manifest_sha256": sha256_file(TASKS_DIR / "manifest.json"),
    }


def protocol_sha256(protocol: dict[str, Any]) -> str:
    return canonical_sha256(protocol)


def render_md(p: dict[str, Any], digest: str | None) -> str:
    rules = "\n".join(f"| `{name}` | {cond} |" for name, cond in p["decision_rules"]["rules"])
    instr = "\n".join(f"- **{k}**: {v}" for k, v in p["arms"]["instructions_verbatim"].items())
    sec = "\n".join(f"- {s}" for s in p["secondary_endpoints"])
    interp = "\n".join(f"- {s}" for s in p["decision_rules"]["interpretation_rules"])
    return f"""# {p['experiment_name']}

- Status: **{p['protocol_status']}**
- Protocol SHA-256: `{digest or 'not frozen'}`

## Research question
{p['research_question']}

## Hypotheses
- H1 (primary): {p['hypotheses']['H1_primary']['parameter']}; null {p['hypotheses']['H1_primary']['null']}; effect of interest {p['hypotheses']['H1_primary']['effect_of_interest']}.
- H2 (mechanism): {p['hypotheses']['H2_mechanistic']['claim_tested']}.
- H3 (decoys): {p['hypotheses']['H3_decoy_resistance']['claim_tested']}.

## Endpoints
- Primary: {p['primary_endpoint']}
{sec}

## Arms and exact instructions
{instr}

Prompt assembly: {p['arms']['prompt_assembly']}. Arm order: {p['arms']['arm_order']}.

## Tasks
{p['task_set']['construction']}
- Main: {p['task_set']['main']['n_cases']} cases, seed `{p['task_set']['main']['seed']}`, difficulty {p['task_set']['main']['difficulty']}, public file SHA-256 `{p['task_set']['main']['public_sha256']}`.
- Pilot: {p['task_set']['pilot']['n_cases']} held-out cases, seed `{p['task_set']['pilot']['seed']}`.
- Reference (non-LLM) solvers on the main set: `{json.dumps(p['task_set']['main']['reference_solvers'])}`

## Sample size
{p['sample_size']['rationale']}

## Compute control
{p['compute_accounting']['compute_parity_gate']}

## Decision rules (evaluated in order)
| Verdict | Condition |
|---|---|
{rules}

Interpretation rules:
{interp}

## Pilot policy
{p['pilot_policy']['difficulty_rule']}

The full field list is in `protocol.json`.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--write-draft", action="store_true")
    g.add_argument("--freeze", action="store_true")
    g.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write_draft:
        if PROTOCOL_SHA.exists():
            sys.exit("A frozen protocol exists; drafts can no longer be written.")
        p = build("DRAFT")
        atomic_write_json(PROTOCOL_JSON, p)
        atomic_write_text(PROTOCOL_MD, render_md(p, None))
        print("draft written; canonical SHA-256 (not frozen):", protocol_sha256(p))
    elif args.freeze:
        p = build("FROZEN")
        digest = protocol_sha256(p)
        if PROTOCOL_SHA.exists() and PROTOCOL_SHA.read_text().split()[0] != digest:
            sys.exit("A different protocol is already frozen; record an amendment and re-freeze deliberately.")
        atomic_write_json(PROTOCOL_JSON, p)
        atomic_write_text(PROTOCOL_MD, render_md(p, digest))
        atomic_write_text(PROTOCOL_SHA, f"{digest}  protocol.json (canonical JSON, sorted keys)\n")
        print("FROZEN", digest)
    else:
        ok = verify()
        print("PROTOCOL VERIFIED" if ok else "PROTOCOL MISMATCH")
        sys.exit(0 if ok else 1)


def verify() -> bool:
    if not PROTOCOL_SHA.exists():
        return False
    frozen = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
    return (frozen == build("FROZEN") and protocol_sha256(frozen) == PROTOCOL_SHA.read_text().split()[0])


if __name__ == "__main__":
    main()
