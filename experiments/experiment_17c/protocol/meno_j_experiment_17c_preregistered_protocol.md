# Minos-J Experiment 17-C: Claude-Based Replication of Experiment 17 (Matched-Compute Architecture Falsification) — Preregistered Protocol

> Frozen before any Experiment 17-C model-completion call. Experiment 17 and all earlier experiments remain unchanged.

## Relation to Experiment 17

Experiment 17 stopped when the OpenRouter free-tier daily quota ran out. It cannot be completed as preregistered without OpenRouter. Experiment 17-C re-runs the whole Experiment 17 design with Claude models. It reuses no Experiment 17 state and never pools results with it.

- Base protocol SHA-256 (Experiment 17): `76ae7d0ae043fab1e0a34f0f34ed0380473d725cad689260d15b0f44125d5b8b`

Experiment 17 state at handover:

- Q1-r1: Arm A stages 4-4.3 checkpointed; Stage 5 auditor failed validation twice; no Arm B
- Q2-r1: Arms A and B complete; judge attempt 1 invalid, attempt 2 started but never checkpointed (consumed under the E17 rule, so JUDGE_FAILED on resume)
- Q3-r1: Arm A complete; Arm B samples 1-2 valid, sample 3 recorded invalid by an HTTP 429 before the daily-quota stop
- r2_and_r3_units: not started

## Research question

If a multi-stage reasoning pipeline performs better than a simpler baseline, does the architecture itself deserve the credit once inference budget, sampling, retries, and evaluator passes are controlled?

## Model substitutions

| Role | Experiment 17 | Experiment 17-C |
|---|---|---|
| generator (both arms) | `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter free tier) | `claude-sonnet-5` (Claude Code CLI on Claude subscription) |
| blinded judge | `nex-agi/nex-n2.5-pro:free` (OpenRouter free tier) | `claude-opus-5-5` (Claude Code CLI on Claude subscription) |

Transport: Claude Code CLI headless mode (`claude -p`), authenticated by the operator's Claude subscription (OAuth, authMethod=claude.ai). Paid API dependency: none; API-key and base-URL variables are stripped from the CLI environment.

## Deviations from Experiment 17

- Models substituted as listed in model_substitutions; generator and judge share a vendor family (Anthropic), whereas Experiment 17 required different families. Same-family judge bias is a declared threat to validity.
- Sampling temperature cannot be set through `claude -p`; provider default is used instead of 0.4. It is identical for both arms.
- Output ceiling set with CLAUDE_CODE_MAX_OUTPUT_TOKENS=12000 (Experiment 17: max_tokens=12000). Effort pinned to 'medium' for every call.
- Structured output enforced by Claude Code `--json-schema` instead of OpenRouter response_format/provider.require_parameters.
- Token currency: prompt_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens; completion_tokens = output_tokens (includes any thinking). Applied identically to both arms and the judge.
- Each CLI call carries a fixed overhead of roughly 1k prompt tokens (system prompt plus Claude Code's structured-output tool); it is counted in every request of both arms and the judge. Structured output may use a second internal turn, whose tokens are also counted.
- The single JSON-repair request is sent as one user turn quoting the original request and previous response, because `claude -p` accepts one user message.
- Transient-retry classes map to CLI failures: timeout, non-JSON CLI exit, HTTP 429 (non-quota)/5xx/529, and OAuth-refresh contention. The four-retry ceiling is unchanged.
- A subscription usage-limit stop is treated like Experiment 17's daily-quota stop: the run halts, nothing is charged to an arm as an invalid sample, and the same command resumes later. (Experiment 17's Q3-r1 sample 3 shows the defect this avoids.)
- Persistent OAuth-refresh failure halts the run (infrastructure) instead of failing a stage.

## Unchanged from Experiment 17

- Questions Q1-Q3 × 3 replicates = 9 units.
- Arm A: historical Minos-J v4 multi-stage pipeline. Arm B: one-shot sampling plus one strict selector/verifier.
- Budget tolerance: `a unit is budget-matched iff 0.85 <= T_B / T_A <= 1.15 and E_B == E_A`.
- Blinded, pooled, shuffled judging, with the same checklist and the same two-attempt judge limit.
- Primary outcome: V = number of judge-validated cards in an arm's final deliverable (0-10); paired difference D = V_A - V_B per unit
- Analysis set: units where both arms completed, the judge completed, and the budget was matched
- Statistics: mean D; paired bootstrap 95% CI (10000 resamples, seed 16); exact two-sided sign test on non-zero D
- Criterion: If the matched-budget simple baseline performs similarly to or better than Minos-J within reasonable experimental variation, Experiment 17-C does NOT support the claim that the Minos-J architecture itself is responsible for the gain.

- `ARCHITECTURE_ADVANTAGE_SURVIVED`: mean D >= 1.0 AND bootstrap CI lower bound > 0
- `BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED`: bootstrap CI upper bound < 0
- `ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED`: any other outcome (CI includes 0, or mean D below the margin)
- `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`: fewer than 6 analysable units, or more than one third of attempted units unmatched/failed

## Integrity

- Protocol SHA-256 (canonical JSON): `31fadcff3a17d6e81e074b309d23726f394c36cc21d0ce2610148548352ab594`
