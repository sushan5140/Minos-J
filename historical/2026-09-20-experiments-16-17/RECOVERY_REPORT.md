# Experiments 16–17 recovery and Experiment 17 checkpoint audit

Audit date: 2026-09-23. Audited by Claude Code on the operator's behalf. No Experiment 16 or 17 file was modified, and no Experiment 16 or 17 model call was made during this audit.

## Source

Same workspace as `historical/2026-08-04`:

```text
C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation
```

Experiments 16 and 17 were added to that workspace between 2026-09-17 and 2026-09-22, after the August recovery.

## Recovered material

| Category | Contents |
|---|---|
| Source | `run_experiment_16_matched_compute.py`, `run_experiment_17_matched_compute.py`, `experiment_17_runtime.py`, `RUN_LATER.md`, the Experiment 16/17 validators, and `work/run_experiment_17_live_compatibility.py` |
| Outputs | every `outputs/meno_j_experiment_16_*` and `outputs/meno_j_experiment_17_*` file |
| Checkpoints | `work/experiment_16_checkpoints/`, `work/experiment_16_harness_validation_checkpoints/`, `work/experiment_17_checkpoints/` (including the request ledger and 64 sanitized diagnostic responses), `work/experiment_17_live_compatibility/` |
| Harness validation | `outputs/harness_validation/experiment_16/` and `outputs/harness_validation/experiment_17/` |
| Manifest | [`MANIFEST.sha256`](MANIFEST.sha256): 362 files, each copied byte-for-byte and hash-checked against its origin |

### Withheld

[`WITHHELD.sha256`](WITHHELD.sha256) lists one file, `work/validate_experiment_17_preparation.py`, by hash only. It contains a synthetic credential-shaped test fixture (`sk-or-v1-synthetic-…`), not a real key. It was held back so that no credential-shaped string is published. The file is still unmodified in the local workspace.

### Excluded

`.env`, which holds the OpenRouter key, and `__pycache__`. A scan for the real key and for `sk-or-`, `sk-ant-` and `Bearer` token patterns found no hits in the published files.

## Experiment 16 (complete, inconclusive)

- Verdict: `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`
- Unit status: 5 `ARM_A_FAILED`, 1 `ARM_B_FAILED`, 3 `JUDGE_FAILED`; 0 analysable units.
- Models: `nvidia/nemotron-3-ultra-550b-a55b:free` (generator), `nvidia/nemotron-3.5-lightning:free` (judge).
- `outputs/meno_j_experiment_16_recovery_audit.md` attributes the failure to engineering, not science. The main causes were prompt-only structured output, truncation at the 12,000-token output limit, audit-rule violations, and an unreliable judge.

## Experiment 17 (interrupted) — last valid checkpoint

The protocol was frozen on 2026-09-20 with SHA-256 `76ae7d0ae043fab1e0a34f0f34ed0380473d725cad689260d15b0f44125d5b8b` (verified unchanged). The generator was `nvidia/nemotron-3-super-120b-a12b:free` and the blinded judge was `nex-agi/nex-n2.5-pro:free`, both on OpenRouter's free tier.

The request ledger has 72 rows (sequences 1–72, unique and monotonic) from two process sessions. Per unit:

| Unit | Arm A | Arm B | Judge | Status under the frozen rules if resumed |
|---|---|---|---|---|
| Q1-r1 | Stages 4, 4.1, 4.2 and 4.3 checkpointed. The Stage 5 auditor was called twice (seq 10–11 and seq 41–43) and failed validation both times, with no `stage_5.json`. | not started | — | Would retry Stage 5 on resume (Arm A has no terminal-failure checkpoint) |
| Q2-r1 | complete (`arm_a_report.json`) | complete: 2 valid samples plus the selector (`arm_b_result.json`) | Attempt 1 failed with `ValueError: OpenRouter assistant content was not a string.` (seq 69–72). Attempt 2 is `STARTED` in `judge_state.json` and has no ledger rows. | **JUDGE_FAILED.** The E17 rule counts an unfinished `STARTED` attempt as consumed, which reaches the two-attempt limit. |
| Q3-r1 | complete | Samples 1–2 valid (11,159 and 23,351 tokens). Sample 3 was checkpointed as **invalid** because of `RuntimeError: OpenRouter HTTP 429` (seq 37). | — | Resume would continue from sample 4 with sample 3 counted as a spent, invalid sample |
| Q1–Q3, r2 and r3 | not started | not started | — | — |

The final stop is recorded in `interrupted_request_recovery.json`. On Q3-r1 Arm B the operator interrupted the process during the daily-quota backoff (seq 39–40, `InterruptedDailyQuotaBackoff`, four HTTP 429 attempts, `openrouter_free_tier_daily`).

### Findings

1. **No unit completed.** Experiment 17 has 0 of 9 units evaluated, so there is nothing to report about the Arm A versus Arm B comparison.
2. **Q2-r1 is already lost under the frozen rules.** Its judge budget ran out on an envelope-shape failure plus an interrupted attempt.
3. **Q3-r1 has a quota-cascade defect.** A provider rate limit (`RuntimeError` after retries) was caught by the historical `except Exception` in `run_arm_b` and saved as an invalid sample. This is the failure mode that `DailyQuotaExhausted` was meant to prevent. It slipped through because the first 429 sequence was not tagged as the daily quota.
4. **Resuming needs the frozen OpenRouter models.** The prepared resume (a Codex heartbeat, now paused) waits for the daily free-tier reset. The operator chose to continue without OpenRouter and without paid APIs, so Experiment 17 cannot be completed as preregistered.

## Continuation

Experiment 17 stays in this directory as an **interrupted, incomplete run**. The research continues as **Experiment 17-C**, a Claude-based replication. It has its own preregistered protocol, re-runs all nine units from scratch, and is never pooled with Experiment 17. See [`experiments/experiment_17c/`](../../experiments/experiment_17c/).
