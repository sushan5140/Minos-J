# Minos-J research audit — Experiments 1 to 17-C

**Status: FINAL (2026-09-30).** Experiment 17-C is closed and independently validated (15/15); see `experiments/experiment_17c/results/RESULTS.md`. Every claim below is taken from the original experiment records in the research workspace (`outputs/meno_j_*`), mirrored byte-for-byte under `historical/`. Numbers are quoted from those files, not from README summaries.

## How to read this audit

Minos-J has three separate layers of work. Evidence from one layer must not be used as evidence for another.

| Layer | Experiments | Kind of evidence |
|---|---|---|
| **L1 — LLM falsification architecture** | E1, E2, E3, E4, E7 (v4), E16, E17, 17-C | LLM-generated hypotheses, audited by the pipeline itself (E1–E7) or by a blinded LLM judge (E16–17-C) |
| **L2 — Domain science**: subject-level conformal-prediction failure in wearable stress data | E5, E6, E8–E15 | Preregistered numerical experiments on synthetic generators, WESAD, and one independent 33-subject cohort |
| **L3 — Theory of explanation quality** ("J-jump" contract) | Theory studies 1–6 | Conceptual casebooks built from history of science, plus an executable scorer |

The central scientific claim of Minos-J is an L1 claim: that a structured falsification loop makes an AI system's explanations more likely to be correct, not merely more persuasive. **No completed experiment has yet tested that claim under controlled conditions.** The L1 hypotheses motivated the L2 experiments, but L2 successes are not evidence for the L1 claim. The evidence for L2 is the numerical data, not the fact that an LLM proposed the hypothesis.

---

## A. Established findings
*Directly supported by completed, preregistered or fully recorded experiments, within the stated scope.*

| # | Finding | Evidence | Scope limit |
|---|---|---|---|
| A1 | In the synthetic generator, the severity of subgroup undercoverage depends on the pairing of nonconformity score and conditioning strategy. The safest pairing had mean gap 0.0645 and minimum coverage 0.8656; inverse-probability + marginal had mean gap 0.4209 and minimum coverage 0.4838; 15 of 45 grid cells showed persistent failures. | E6 | Synthetic generator only |
| A2 | Region-conditioned coverage can look "safe" only because the prediction sets degenerate into full-label sets (abstention-like). Coverage must be reported together with full-set frequency, finite-threshold probability, effective calibration size and metadata quality. | E8 (`ORACLE_SAFETY_PARTLY_VACUOUS_AND_METADATA_FRAGILE`) | Methodological; synthetic oracle metadata |
| A3 | Limited labeled personal calibration improved cohort-level cold-start coverage without retraining (k=12 vs external: +0.087 mean coverage; paired-subject bootstrap 95% CI [0.024, 0.162]). | E10 | WESAD; improvement partly bought with larger sets (full-set frequency +0.074) |
| A4 | Within WESAD, per-subject robust normalization improved state-classification accuracy (+15.9 pp in E11; +17.5 pp under temporal-block holdout in E12, positive in every temporal tertile), reduced full-label sets, and kept mean coverage near target (0.911–0.924). | E11, E12 | Same dataset, same sessions; not independent-subject evidence |
| A5 | On an independent 33-subject cohort, normalization reduced conformal ambiguity: full-set frequency fell by 0.091, meeting the preregistered ≥ 0.05 threshold. | E13 (`SUPPORTED_IN_THIS_DATASET`) | One external dataset |
| A6 | The Experiment 7 v4 pipeline can produce complete, schema-valid hypothesis contracts with rival predictions and falsification tests: Q1 9 PASS / 1 SALVAGEABLE; Q2 10 PASS. | E7 | Engineering capability only; says nothing about correctness (see B3) |

## B. Tentative findings
*Patterns observed but underpowered, unreplicated or confounded.*

| # | Observation | Evidence | Why it is only tentative |
|---|---|---|---|
| B1 | Adding confounder, rival and statistical "enrichment" stages raised the pipeline's own PASS rate: Q1 went from 0/10 (E1/v2) to 9/10 (E2/v3). | E1, E2 | The same model family generated and audited the outputs; there was no independent judge, no compute control, and one run per question. Consistent both with "better hypotheses" and with "outputs tailored to the checklist". |
| B2 | S4's normalization repair persisted across early, middle and late recording segments. | E12 | Internal same-session replication only |
| B3 | E7 Q2 passed 10/10, which the pipeline flagged itself as an auditor-calibration red flag. | E7 | A red flag about auditor leniency, not a quality result |
| B4 | The direction of the normalization effect held in both protocol versions of the external cohort (V1 +1.5 pp, V2 +7.4 pp), but the size differed. | E13 (`DIRECTIONALLY_SUPPORTED_BUT_HETEROGENEOUS`) | Two strata; not preregistered as confirmatory |
| B5 | Removing temperature features helped the difficult subjects in raw WESAD (S2/S4 accuracy +10 pp). | E11 (exploratory) | Did **not** replicate in E12 (see C8) |
| B6 | In all 3 complete 17-C units, Arm A had more judge-validated cards than Arm B (D = +3, +2, +4). | 17-C | Only 1 unit (Q2-r3, D = +4) is analysable under the preregistered rule. In the other two, Arm B received **less** compute (T_B/T_A = 0.833 and 0.735). The endpoint is an unvalidated LLM checklist, and n is far below the preregistered minimum of 6. This is a direction to test, not a finding. |

## C. Negative findings
*Hypotheses that failed their preregistered test, or mechanisms that did not deliver the expected improvement.*

| # | Failed hypothesis | Evidence |
|---|---|---|
| C1 | "Subgroup undercoverage is only a finite-sample artifact." **Falsified**: at n = 300, gap 0.7462, minimum group coverage 0.1538, 14 persistent-failure cells. | E5 |
| C2 | "The safest synthetic score/conditioning pairing transfers to real WESAD." **Not supported**: worst-subject coverage 0.343 vs 0.600 for the "dangerous" pairing; full-set frequency +0.559; paired bootstrap CI [−0.106, 0.056]. | E9 |
| C3 | "A finite conformal threshold means useful calibration readiness." **Falsified**: at k = 3 and 6, 100% of sets were full-label. | E10 |
| C4 | "Unlabeled centroid distance selects compatible external calibration subjects." **Not supported**: loss improvement 0.013 vs the required 0.03. | E10 |
| C5 | "Twelve personal windows repair S2 and S4." **Not supported**: coverage rose by becoming uninformative. | E10 |
| C6 | "Crossing the α = 0.10 order-statistic boundary (18 → 19 examples) is a safe readiness jump." **Not supported** in E11 (worst-subject coverage −0.133); **falsified for all 4 representations** in E12. | E11, E12 |
| C7 | "Diagonal QDA or k-NN repairs the difficult subjects." **Not supported** (accuracy −9.0 pp and −4.9 pp). | E11 |
| C8 | "Temperature-feature interference is a stable mechanism." **Not replicated.** | E12 |
| C9 | "One normalization repairs both difficult subjects." **Not supported**: S2 remained a distinct residual failure (E12 S2 coverage 0.811). | E11, E12 |
| C10 | "Normalization produces a large, externally replicable accuracy repair." **Not supported**: +4.4 pp, CI [−0.4, 8.9] pp, below the preregistered +8 pp; normalized coverage 0.868 < 0.88. **Refuted**: "representation improvement is sufficient evidence of a safe uncertainty repair" and "the effect is uniform across subjects". | E13 |
| C11 | "Class-Mondrian calibration repairs normalized external coverage and preserves subject safety." **Not supported**; "balancing class coverage improves informativeness" **refuted**. | E14 |
| C12 | "A confidence–trust proxy explains residual subject undercoverage." **Not supported**: high-risk vs high-confidence/high-trust miscoverage gap = 0.010. | E15 |
| C13 | **The shared audit decision contract (v4 Stage 5 auditor, reused by the Arm B selector) is not reliably satisfiable by the models tested.** "SALVAGEABLE" is legal only with 1–2 failed *critical* checks, but the auditor repeatedly marks SALVAGEABLE when only non-critical checks fail. The frozen validator then fails the whole arm. Counts: 4 of 5 Arm A failures in E16 (Nemotron-3-Ultra); Q1-r1 in E17 (Nemotron-3-Super); **6 of 9 units in 17-C** (Claude Sonnet 5): 5 at Arm A's Stage 5 and 1 at Arm B's selector. In 17-C's archived Stage 5 audits, 11 of 40 rows (27.5%) violate the rule, so a 10-row audit usually contains at least one violation. | E16, E17, 17-C | A negative finding about **the audit contract shared by both arms**, not about the falsification idea itself. It hits Arm A first only because Arm A audits before Arm B runs. Under the frozen endpoint these are arm failures, not low-quality answers. |

## D. Inconclusive findings
*Experiments that cannot support either conclusion.*

| # | Question | Evidence | Why inconclusive |
|---|---|---|---|
| D1 | Does the v4 architecture beat a matched-compute sample-and-select baseline? | E16: `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`, 0 of 9 units analysable (5 Arm A, 1 Arm B and 3 judge failures) | Engineering failure: prompt-only structured output, truncation, judge unreliability, C13 |
| D2 | Same question, repaired harness | E17: 0 of 9 units evaluated, **interrupted** by the OpenRouter free-tier quota | Never ran to completion |
| D3 | Same question, Claude models | **17-C: `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`**, independently validated (15/15). 1 of 9 units analysable (D = +4). The effect size is not estimable, and every committed sensitivity analysis agrees. | Audit-contract failures (C13, 6 units) plus Arm B budget undershoot (2 units) |
| D4 | Pipeline output quality in E1–E3 | E1–E3 | No external judge, no controls, single runs |
| D5 | Does the executable J-jump scorer agree with experts on unseen cases? | Theory study 6 passed 5/5 **author-constructed** calibration cases and its adversarial guards | Its own preregistered next step (a prospective blind benchmark against expert judgments) has not been run |

## E. Engineering findings
*Important for validity, but **not** evidence for or against the scientific hypothesis.*

| # | Finding | Evidence |
|---|---|---|
| E1 | Prompt-only JSON instructions on free endpoints produced truncated, invalid and contradictory outputs. Strict per-stage JSON schemas removed format failures but not **semantic** rule violations (C13). | E16 audit, E17 preparation, 17-C |
| E2 | Output ceilings cause silent data loss: 12,000-token truncation happened in E16, and in 17-C Q2-r1 Arm B sample 3 (the error envelope reported 48,000 output tokens). | E16, 17-C |
| E3 | **Unmetered compute.** Failed requests can consume and report tokens that a "successful requests only" budget currency ignores. That biases matched-compute comparisons toward whichever arm fails more expensively. | 17-C Q2-r1 |
| E4 | **Quota errors cascade into fake scientific failures** unless they are classified exactly. Hit in E17 (Q3-r1 invalid sample from an HTTP 429) and in 17-C (Pro "session limit" wording not recognized, 4 spurious Arm A failures; corrected by amendment 3 on evidence). | E17, 17-C |
| E5 | **Resume can create extra attempts.** If failures are not persisted, a restarted process silently retries them (E17 Q1-r1 Stage 5 ran twice). 17-C amendments 1–2 make failures terminal and make provider refusals free. | E17, 17-C |
| E6 | A blinded LLM judge is itself a failure point: 3 of 9 E16 units were `JUDGE_FAILED`, and E17 Q2-r1's judge attempts were exhausted. Judge validity (agreement with experts) has never been measured. | E16, E17 |
| E7 | Scheduling pitfalls on this machine: MSIX file virtualization hides the Claude CLI from Task Scheduler; the Task Scheduler Operational log is disabled; the CLI auto-updates between sessions (2.1.280 → 2.1.284). | 17-C recovery |
| E8 | Byte-level provenance works: every historical file has a SHA-256 manifest, and no historical output was modified across 17 experiments. | historical manifests, 17-C baseline checks |
| E9 | **The matched-compute controller undershoots.** The frozen Arm B sampling controller stopped at T_B/T_A = 0.833 and 0.735 on 2 of 3 complete 17-C units. Its selector-cost projection does not track Claude CLI accounting (structured output adds a second internal turn; the selector call alone reached 188,595 tokens in Q3-r2). Compute matching by a projection-based controller needs calibration or hard budget stops. | 17-C |

## F. Remaining scientific uncertainties

| # | Uncertainty | Why the existing experiments do not answer it |
|---|---|---|
| F1 | **Does the falsification structure itself make the system reach correct explanations more often than equal-compute reasoning without falsification?** | D1–D3 never produced an analysable comparison, and their endpoint was an LLM judge's checklist, which rewards explanations that *sound* rigorous (a confound the README names explicitly). |
| F2 | If there is an advantage, which part carries it: generating rivals, or checking predictions against evidence? | Never ablated |
| F3 | Is the LLM-judge endpoint valid? | Never compared with expert judgment or ground truth (E6 above) |
| F4 | Can the audit decision contract be made reliable without weakening its strictness? | C13 shows it fails in both arms and across model families; no repair has been tested |
| F5 | **Domain:** which subjects benefit from normalization, and why does S2 remain a residual failure? | E13's preregistered next target: predict benefit from unlabeled diagnostics without post-outcome subgroup selection |
| F6 | **Domain:** do protocol/stressor posterior shift and temporal dependence explain the residual undercoverage? | E15's stated next rival; untested |
| F7 | **Theory:** does the J-jump scorer predict expert or historical judgments on unseen cases? | Theory study 6's own next stage |

---

## The most important unresolved causal question

**Candidates compared:**
- **F1 (architecture vs compute)** is the claim Minos-J exists to test. It has failed to produce evidence three times, for engineering reasons, and its endpoint was never valid for it.
- **F3 (judge validity)** is a prerequisite for F1 *only if* F1 keeps using an LLM judge. A ground-truth endpoint removes the dependency.
- **F4 (auditor contract)** matters for the v4 implementation, but it is an implementation question. Fixing it would not show that falsification helps.
- **F5 and F6** are real domain questions, but answering them would not test Minos-J's central claim.
- **F7** tests the theory layer, and it needs expert annotators the project doesn't currently have.

**Selected: F1, sharpened to include F2.**
- **Question:** when the same model has the same number of calls and a comparable token budget, does an explicit rival-hypothesis falsification loop identify the true mechanism behind an observation more often than (a) generic self-critique and revision, and (b) generating rivals without falsifying them?
- **Why it matters:** if the answer is no, Minos-J's value would lie in formatting and documentation, not in reasoning. The README's own list of confounds (extra inference, evaluator bias, explanations that merely sound rigorous) is exactly what F1 has to rule out.
- **What earlier experiments failed to establish:** E1–E7 had no controls. E16–17-C had controls but produced no analysable units, and they scored plausibility with an LLM judge rather than correctness against ground truth.
- **What would distinguish the explanations:**
  - *Structure* predicts that the falsification loop beats equal-call self-critique, most of all on cases containing a persuasive decoy.
  - *Compute* predicts that equal-call arms perform about the same.
  - *Rival enumeration* predicts that rivals-without-falsification perform about as well as the full loop.
- **What counts against Minos-J:** the falsification loop failing to beat equal-call self-critique by a preregistered practical margin, especially on decoy cases.
