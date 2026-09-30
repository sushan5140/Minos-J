# Experiment 17-C — final validated result

**Verdict (preregistered): `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`.** This is not evidence for or against the Minos-J architecture.

- **Run:** 2026-09-22 22:23 UTC to 2026-09-30 17:07 UTC. 10 process sessions, including 8 usage-limit pauses. Claude Code CLI 2.1.280 for session 1, 2.1.284 afterwards.
- **Models:** `claude-sonnet-5` generated for both arms; `claude-opus-5-5` was the blinded judge. The model identity returned on every request matched these (validator check `ledger_uses_only_frozen_models`).
- **Protocol:** SHA-256 `31fadcff3a17d6e81e074b309d23726f394c36cc21d0ce2610148548352ab594`, unchanged. Amendments 1–3 are in [`../AMENDMENTS.md`](../AMENDMENTS.md).
- **Independent validation:** **PASSED, 15/15 checks**, run from a clean invocation with no bytecode cache. See [`meno_j_experiment_17c_independent_validation.md`](meno_j_experiment_17c_independent_validation.md).

## Units

| Unit | Status | T_B/T_A | Matched | V_A / reported | V_B / reported | D = V_A − V_B |
|---|---|---:|---|---|---|---:|
| Q1-r1 | ARM_A_FAILED¹ | — | — | — | — | — |
| Q2-r1 | COMPLETE | 0.833 | no | 4 / 8 | 1 / 6 | +3 |
| Q3-r1 | ARM_A_FAILED¹ | — | — | — | — | — |
| Q1-r2 | ARM_A_FAILED¹ | — | — | — | — | — |
| Q2-r2 | COMPLETE | 0.735 | no | 6 / 8 | 4 / 9 | +2 |
| Q3-r2 | ARM_B_FAILED¹ | 1.309 | no | — | — | — |
| Q1-r3 | ARM_A_FAILED¹ | — | — | — | — | — |
| **Q2-r3** | **COMPLETE** | **0.912** | **yes** | 6 / 10 | 2 / 7 | **+4** |
| Q3-r3 | ARM_A_FAILED¹ | — | — | — | — | — |

¹ **All six failures have the same cause.** Each audit (Arm A's Stage 5, or Arm B's selector, which reuses the same frozen validator) marked a hypothesis `SALVAGEABLE` while failing 0 critical checks. The frozen rule allows `SALVAGEABLE` only with 1–2 critical failures, so the whole arm fails. These are genuine model outputs; in every case, replaying the validator on the archived response reproduces the error.

## Preregistered statistics (analysis set: complete, judged, budget-matched units)

- Analysable units: **1 of 9**. The preregistered minimum is 6, and at most one-third of units may be unmatched or failed.
- Mean D = 4.0. The "bootstrap CI" of [4.0, 4.0] is degenerate with n = 1. Sign test p = 1.0 (1 unit favours A, 0 favour B).
- `architecture_survived_falsification_test`: **false**. The effect size and uncertainty are **not estimable**.

## Sensitivity analyses (committed in advance in the amendments; none changes the verdict)

| Analysis | Analysable units | Result |
|---|---:|---|
| Frozen rule (primary) | 1 | inconclusive |
| All complete units, matched or not (report field) | 3 | mean D = +3.0, bootstrap [2.0, 4.0] |
| Excluding amendment-3-affected units (Q1-r2, Q2-r2, Q3-r2, Q1-r3, Q2-r3) | 0 | inconclusive |
| Counting unmetered failed-request tokens (Q2-r1 Arm B: 58,760), which makes Q2-r1 ratio 1.079, i.e. matched | 2 (D = +3, +4) | inconclusive |

**How to read these.** Arm A had more judge-validated cards in every complete unit (3 of 3). That pattern is not evidence for the architecture:
- only one unit is analysable under the preregistered rule;
- two of the three complete units gave Arm B **less** compute than Arm A (ratios 0.735 and 0.833);
- the endpoint is an LLM judge's checklist, whose validity has not been established.

## Compute (tokens as reported by the provider, successful requests only)

| | Total | Prompt / context | Completion | Attempts | Failed requests |
|---|---:|---:|---:|---:|---:|
| Arm A | 1,817,915 | 1,328,171 | 489,744 | 81 | 12 |
| Arm B | 899,809 | 448,326 | 451,483 | 26 | 1 |
| Judge | 109,202 | 87,868 | 21,334 | 6 | 0 |

Arm A's failed requests were almost all quota refusals, which carry 0 tokens. The ledger also holds 2 orphan captures from Q2-r3's unclean termination; both were refused or timed out, and they are recorded in the ledger.

## Integrity

- **No completed unit was re-run or overwritten.** All of Q1-r1's, Q2-r1's and Q3-r1's requests are in a single session. The two units that span sessions, Q1-r2 and Q2-r3, resumed only at stages that had never produced output.
- **Ledger:** 225 rows, sequences unique and monotonic. Tokens (2,826,926) and attempts (113) reconcile with the report.
- **History untouched:** all 700 Experiment 1–17 files, including the interrupted original Experiment 17, match their pre-run SHA-256 baseline.
- **Credential scan:** clean.

## What 17-C establishes

1. **The shared audit contract of the v4 design is not reliably satisfiable by Claude Sonnet 5.** It failed 6 of 9 units: 5 at Arm A's Stage 5 and 1 at Arm B's selector. The same failure mode appeared with Nemotron in Experiments 16 and 17, so the contract, not a particular model, is the main obstacle to measuring the architecture.
2. **The frozen Arm B budget controller undershoots** under Claude CLI accounting (ratios 0.735 and 0.833 on two of three complete units). That makes compute matching unreliable as designed.
3. **The architecture question remains open.** See [`../../RESEARCH_AUDIT_THROUGH_17C.md`](../../RESEARCH_AUDIT_THROUGH_17C.md).
