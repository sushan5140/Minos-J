# Experiment 17-C — Claude-based replication of Experiment 17

**Status: live run in progress. No results yet.** This file is updated only with verified outputs.

## Why this exists

Experiment 17 was the repaired matched-compute falsification test. Its question: *does the Minos-J multi-stage architecture beat a matched-budget sample-and-select baseline once compute is controlled?* The run was interrupted when OpenRouter's free-tier daily quota ran out, with 0 of 9 units evaluated. Its frozen models are only available through OpenRouter. The operator directed that work continue without OpenRouter and without paid APIs. Experiment 17 therefore stays preserved as an interrupted run (see the [recovery and checkpoint audit](../../historical/2026-09-20-experiments-16-17/RECOVERY_REPORT.md)), and this separately preregistered replication re-runs the full design from scratch.

## What is identical to Experiment 17

These protocol objects are Experiment 17's own. `scientific_invariants_hold()` checks them field by field, and the harness validation asserts they match:

- Research question, questions Q1–Q3, and 3 replicates (9 units).
- Arm A: the historical v4 pipeline (`pipeline.run_v4_pipeline`, unchanged). Arm B: K one-shot samples plus one selector/verifier.
- Matched-compute rule: tolerance `0.85 ≤ T_B/T_A ≤ 1.15`, and evaluator parity.
- Blinding: pooled, shuffled, opaque IDs, seed `sha256('E17|'+unit_id)`. Checklist, two-attempt judge limit, and durable judge state.
- Primary outcome V (judge-validated cards) and D = V_A − V_B. Paired bootstrap 95% CI (10,000 resamples, seed 16), sign test, practical margin 1.0, at least 6 analysable units, and the four preregistered verdicts.
- Prompts, schemas, validators, the one-shape-retry policy, the single JSON-repair request, the resume-safe ledger, and the diagnostic archive (the unchanged `experiment_17_runtime.py` and `run_experiment_16_matched_compute.py`).

## Model substitutions

| Role | Experiment 17 | Experiment 17-C |
|---|---|---|
| Generator (both arms) | `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter) | `claude-sonnet-5` (Claude Code CLI, Claude subscription) |
| Blinded judge | `nex-agi/nex-n2.5-pro:free` (OpenRouter) | `claude-opus-5-5` (Claude Code CLI, Claude subscription) |

All other deviations are listed in the frozen protocol under `deviations_from_experiment_17`:

- Generator and judge now share a vendor family.
- Temperature uses the provider default instead of 0.4.
- Effort is pinned to `medium`; output is capped at 12,000 tokens.
- Structured output is enforced by `--json-schema`.
- Token accounting includes cache tokens and a fixed CLI overhead of about 1k tokens.
- The JSON-repair request is serialized into a single turn.
- Stops for usage limits or OAuth problems pause the run instead of being charged to units.

## How it runs (no paid API)

`experiment_17c_claude_runtime.ClaudeCodeCLIClient` subclasses the Experiment 17 client and replaces only `_request_json`. Each completion is one headless call:

```text
claude -p --model <id> --effort medium --output-format json --tools "" --strict-mcp-config
       --setting-sources "" --disable-slash-commands --no-session-persistence
       --system-prompt <E17 system message> --json-schema <E17 stage schema>
```

- Authentication uses the subscription OAuth login (`authMethod=claude.ai`, checked in preflight).
- `ANTHROPIC_*` and `CLAUDE*` variables are removed from the child environment.
- `--bare` is never used, because it accepts only API keys.

## Files

| Path | Content |
|---|---|
| `source/run_experiment_17c_claude_replication.py` | Runner and frozen-protocol builder (`--write-protocol`, `--preflight`, `--run`) |
| `source/experiment_17c_claude_runtime.py` | Claude Code CLI transport |
| `source/work/validate_experiment_17c_harness.py` | Harness validation that uses a fake CLI (no model calls) |
| `protocol/` | Frozen protocol, SHA-256 `31fadcff3a17d6e81e074b309d23726f394c36cc21d0ce2610148548352ab594` |
| `validation/meno_j_experiment_17c_harness_validation.json` | 19/19 checks passed before the live run |
| `validation/meno_j_experiment_17c_live_smoke_test.json` | Structured-output smoke test for both models. Not a scientific result. |
| `validation/experiment_17c_historical_baseline.json` | Pre-run SHA-256 baseline of the 700 workspace files for Experiments 1–17 |
| `results/` | Filled only after the run completes and passes validation |

These files run from the original workspace root, next to `pipeline.py`, `schema.py`, `prompts.py`, `experiment_17_runtime.py` and `run_experiment_16/17_*.py`. Those are preserved in `historical/`.

## Validation before live trials

- Harness validation passed 19/19. It covered protocol invariants, removal of API-key variables, subscription-mode argv, message serialization, usage and cache-token accounting, usage-limit halting without an invalid-sample record, OAuth-contention halting, transient and timeout retries, the schema-failure shape retry, the single JSON repair, two end-to-end fake units through the unchanged scientific core, and zero changes to historical files.
- The live smoke test returned schema-valid output from `claude-sonnet-5` and `claude-opus-5-5`, and `modelUsage` confirmed the model identities.
