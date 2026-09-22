# Meno-J Experiment 16: Matched-Compute Architecture Falsification — Preregistered Protocol

- Status: `FROZEN_BEFORE_ANY_EXPERIMENT_16_MODEL_CALL`
- Frozen on: 2026-09-17
- Protocol SHA-256 (canonical JSON): `f76d6d2a5f6fa4eb0c168a2cdf001af54507618fa8c08ac45cf52cd237eed96a`
- Naming: Requested as 'Experiment 8'. Numbered 16 because the historical record already contains Experiment 8 (rare-subgroup frontier) through Experiment 15. No historical file is touched.

## Research question

If a multi-stage reasoning pipeline performs better than a simpler baseline, does the architecture itself deserve the credit once inference budget, sampling, retries, and evaluator passes are controlled?

## Task set

- Q1: Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?
- Q2: Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?
- Q3: What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?
- Replicates per question: 3

## Arms

- A (Minos-J v4): historical pipeline.run_v4_pipeline, unchanged, fresh Stage 4 (no reuse of historical checkpoints)
- B (matched-budget sample-and-select): K independent one-shot calls, each producing 10 complete hypothesis cards with every field Arm A ends up with, then ONE selector/verifier call applying the same strict audit checklist and decision rules to the pooled candidates

## Held constant

- underlying_model: OPENROUTER_MODEL (single value for both arms; recorded per request, including provider-returned model id)
- model_settings: historical llm_client: temperature 0.4, max_tokens 12000, same system message, same JSON-repair and retry policy
- retrieval_evidence: none in either arm (the v4 pipeline has no retrieval stage); both arms receive only the research question
- task_inputs: identical research question text

## Matched-compute rule

- budget_currency: total tokens = provider-reported prompt_tokens + completion_tokens over every successful HTTP request of the arm, including JSON-repair requests; chars/4 estimate only if the provider omits usage (flagged)
- order: Arm A runs first on a unit; its realized total T_A becomes Arm B's budget for that unit
- evaluator_parity: Arm B makes exactly as many evaluator/verifier calls as Arm A made (1 per unit)
- controller: Arm B keeps adding one-shot samples while the projected total (samples spent + estimated selector cost) after one more sample is closer to T_A than the projected total without it; at least 1 sample; hard cap K <= 2 * L_A
- selector_cost_estimate: selector prompt template chars/4 + sum of sample completion tokens + Arm A's realized Stage 5 completion tokens
- tolerance: a unit is budget-matched iff 0.85 <= T_B / T_A <= 1.15 and E_B == E_A
- failed_requests: HTTP attempts that failed carry no token usage; they are counted as attempts in both arms
- judge_calls: excluded from both arms' budgets (measurement, not inference) and reported separately
- reported but not matched: logical calls, HTTP attempts, timeout/network/429 retries, JSON repair requests, sampled candidates, cost (if provider returns it), wall-clock latency

## Evaluation

- judge: blinded LLM judge using MINOS_J_JUDGE_MODEL, which must differ from the generator model
- normalization: every final deliverable is converted to the identical 16-field card schema; arm-specific field names and IDs are removed
- blinding: cards from both arms of a unit are pooled, given random opaque IDs, shuffled with a seed derived from the unit ID, and judged in mixed batches of 10; the card->arm key never enters a prompt; prompts are scanned for arm-revealing strings
- judge_checklist: variables_measurable, causal_chain_valid, base_rate_plausible, confounders_identified, effect_size_plausible, data_requirements_clear, mechanism_is_non_generic, prediction_is_testable, rival_prediction_diverges, failure_condition_operational
- judge_validated_card: all six historical CRITICAL_AUDIT_FIELDS true AND rival_prediction_diverges AND failure_condition_operational
- judge_retry: one retry per judge batch on invalid output; otherwise the unit is marked JUDGE_FAILED

## Falsification criterion (fixed before any result)

- If the matched-budget simple baseline performs similarly to or better than Minos-J within reasonable experimental variation, Experiment 16 does NOT support the claim that the Minos-J architecture itself is responsible for the gain.
- Analysis set: units where both arms completed, the judge completed, and the budget was matched
- Statistics: mean D; paired bootstrap 95% CI (10000 resamples, seed 16); exact two-sided sign test on non-zero D
- Practical margin: 1.0 judge-validated hypothesis

- `ARCHITECTURE_ADVANTAGE_SURVIVED`: mean D >= 1.0 AND bootstrap CI lower bound > 0
- `BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED`: bootstrap CI upper bound < 0
- `ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED`: any other outcome (CI includes 0, or mean D below the margin)
- `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`: fewer than 6 analysable units, or more than one third of attempted units unmatched/failed
