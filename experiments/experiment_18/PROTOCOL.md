# Minos-J Experiment 18: Does explicit falsification, rather than compute or rival enumeration, improve mechanism identification?

- Status: **DRAFT**
- Protocol SHA-256: `not frozen`

## Research question
With the same model, identical information, the same number of model calls and approximately matched measured tokens, does an explicit falsification loop (rival mechanisms -> discriminating predictions -> test against evidence -> eliminate) identify the planted mechanism more reliably than generic self-critique and revision? Secondary: if it helps, is the gain due to testing discriminating predictions rather than merely generating rival hypotheses?

## Hypotheses
- H1 (primary): delta_AC = P(correct | A) - P(correct | C), paired over cases; null delta_AC = 0 (exact McNemar, two-sided); effect of interest delta_AC >= +0.10 (10 percentage points).
- H2 (mechanism): the benefit comes from explicitly testing discriminating predictions, not from enumerating rivals.
- H3 (decoys): falsification specifically resists persuasive but misleading evidence.

## Endpoints
- Primary: exact mechanism-identification accuracy; paired difference Accuracy(A) - Accuracy(C) over all main cases (intention-to-treat: a failed trial counts as incorrect)
- S1 A vs D paired accuracy difference (exact McNemar) [Holm family]
- S2 A vs B paired accuracy difference (exact McNemar) [Holm family]
- S3 A vs C on decoy cases (exact McNemar) [Holm family]
- S4 A vs C on non-decoy cases (exact McNemar) [Holm family]
- S5 decoy-vs-non-decoy difference in delta_AC (paired-case bootstrap CI; estimate, not in Holm family)
- S6 multi-class Brier score per arm on completed trials (normalized probabilities over six mechanisms)
- S7 trial failure rate per arm, split into output failures and infrastructure failures
- S8 measured tokens per arm (input, cache-creation, cache-read, output, total) and per-call means
- S9 calls completed per arm
- S10 wall-clock latency per arm (engineering measure only; no inference)
- S11 raw accuracy of every arm, overall and by decoy status and by mechanism (descriptive)

## Arms and exact instructions
- **A1**: Step 1 of 3. Choose the 4 mechanisms you consider the strongest rival explanations. For each, state two discriminating predictions: observations in these diagnostics that should hold if that mechanism is the cause and should not hold otherwise.
- **A2**: Step 2 of 3. Test each rival's predictions against the observed diagnostics, one by one, and record whether the evidence supports or contradicts each prediction. Eliminate every rival that has a contradicted prediction.
- **A3**: Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated probability for every candidate mechanism.
- **C1**: Step 1 of 3. Diagnose which candidate mechanism is the planted cause of the subgroup's under-coverage. Give your diagnosis, a short justification that refers to the diagnostics, and a calibrated probability for every candidate mechanism.
- **C2**: Step 2 of 3. Critique your step-1 diagnosis: look for mistakes in your reasoning, diagnostics you overlooked or misread, and alternative explanations you may have dismissed too quickly.
- **C3**: Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated probability for every candidate mechanism.
- **D1**: Step 1 of 3. Choose the 4 mechanisms you consider the strongest rival explanations. For each, give a short rationale, referring to the diagnostics, for why it is a plausible cause of the subgroup's under-coverage.
- **D2**: Step 2 of 3. Weigh the rivals against each other by their overall plausibility given the diagnostics as a whole, and rank them. Give one overall judgement per rival rather than testing predictions one by one.
- **D3**: Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated probability for every candidate mechanism.
- **B1**: Select the single planted mechanism and give a calibrated probability for every candidate mechanism.

Prompt assembly: COMMON_HEADER + mechanism vocabulary + evidence packet + this trial's previous-step outputs (verbatim JSON) + step instruction + output line. Arm order: per case, the four arms run in a seeded random order: sha256('E18|arm-order|' + case_id).

## Tasks
Each case plants one mechanism. For every mechanism the packet shows a marker (subgroup vs reference), coverage after that mechanism's intervention, and a 4-point coverage series. The planted mechanism satisfies both discriminating predictions (intervention restores coverage; series rises). Decoy cases add a different mechanism with a more abnormal marker that satisfies exactly one prediction, on that dimension up to 1.20x the planted value. Non-decoy cases add a milder distractor marker. Cases are resampled until the ideal joint falsifier identifies the planted mechanism with margin >= 0.04.
- Main: 180 cases, seed `E18-MAIN-2026-10-01`, difficulty 0.5, public file SHA-256 `0ac69d961e42c99944e1f1ea4dba02960cdd4603e3cb43e1936d5df4ad92f1b4`.
- Pilot: 12 held-out cases, seed `E18-PILOT-2026-10-01`.
- Reference (non-LLM) solvers on the main set: `{"joint_falsifier": {"all": 1.0, "decoy": 1.0, "non_decoy": 1.0}, "marker_only": {"all": 0.5, "decoy": 0.0, "non_decoy": 1.0}, "intervention_only": {"all": 0.8444, "decoy": 0.6889, "non_decoy": 1.0}, "series_only": {"all": 0.8833, "decoy": 0.7667, "non_decoy": 1.0}}`

## Sample size
Exact McNemar power for delta_AC = +0.10 (alpha 0.05, two-sided) and probability of ruling out +0.10 (95% CI upper bound < 0.10) when delta_AC = 0, by discordant-pair rate psi: n=60 -> power 0.19-0.40, rule-out 0.26-0.52 (psi 0.35-0.15): not informative. n=120 -> power 0.40-0.79, rule-out 0.46-0.81. n=180 -> power 0.58-0.94, rule-out 0.62-0.93. n=240 -> power 0.72-0.98, rule-out 0.75-0.98. 180 was chosen as the smallest size giving a majority chance of a decisive answer across plausible psi while remaining feasible on a Claude Pro subscription (about 1,800 calls).

## Compute control
R = sum measured tokens(A) / sum measured tokens(C) over all main trials. A positive A>C result supports the causal claim only if R <= 1.20. A null or negative result for A remains informative whatever R is. R and the output-token-only ratio are always reported.

## Decision rules (evaluated in order)
| Verdict | Condition |
|---|---|
| `INCONCLUSIVE_INCOMPLETE` | fewer than 95% of main cases have terminal A and C trials, or FAILED_INFRA exceeds 10% of A or C trials |
| `C_SUPERIOR` | 95% CI upper bound of delta_AC < 0 |
| `NO_PRACTICALLY_MEANINGFUL_ADVANTAGE` | 95% CI upper bound of delta_AC < +0.10 (strong evidence against a practically meaningful falsification advantage) |
| `FALSIFICATION_ADVANTAGE_SUPPORTED` | delta_AC >= +0.10 AND CI lower bound > 0 AND McNemar p < 0.05 AND compute gate R <= 1.20 |
| `ADVANTAGE_BUT_COMPUTE_UNMATCHED` | the supported criteria hold except R > 1.20: cannot support the causal claim |
| `POSITIVE_BELOW_MARGIN_OR_UNCERTAIN` | CI lower bound > 0 but delta_AC < +0.10, or CI includes both 0 and +0.10: direction or size unresolved |
| `INCONCLUSIVE` | anything else |

Interpretation rules:
- If A and D are materially indistinguishable (S1 CI includes 0 and |delta_AD| < 0.05) while both exceed C, that supports 'considering rivals, not explicit falsification, does the useful work'.
- If A shows no particular advantage on decoy cases (S5 estimate <= 0 or its CI includes 0), that weakens the claim that falsification resists persuasive misleading evidence.
- A vs B informs efficiency only; it cannot establish the mechanism because B has fewer calls.
- No rule may be changed after results are visible.

## Pilot policy
Compute pooled accuracy over ALL pilot trials of ALL arms together (arm identity ignored). If pooled > 0.85, raise difficulty by 0.25 (max 1.0); if pooled < 0.40, lower by 0.25 (min 0.0); otherwise keep 0.5. At most one adjustment. Any change regenerates the untouched main set with the same seed and requires re-freezing (new protocol hash) before main inference.

The full field list is in `protocol.json`.
