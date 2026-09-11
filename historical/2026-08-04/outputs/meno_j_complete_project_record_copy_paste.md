MENO-J COMPLETE PROJECT RECORD
From the initial Auditor Calibration Test through the Meno-J Falsification Engine reframing

================================================================================
1. EXECUTIVE SUMMARY
================================================================================

Meno-J began as a staged research pipeline for generating speculative explanations and auditing them. The initial framing was:

Dreamer -> Strict Mechanism Auditor -> Rival Prediction Matrix -> Falsification Agent

The project investigated why conformal prediction, especially Mondrian conformal prediction, can under-cover certain physiological stress subjects, signal segments, and wearable-data subgroups. The initial assumption was that higher-quality speculative hypotheses might lead to useful scientific explanations. The experiments showed something more important:

1. Raw LLM speculation was not reliably audit-ready.
2. Explicit mechanism, confounder, rival, data, effect-size, prediction, and failure-condition contracts greatly improved audit survival.
3. A high PASS rate was not automatically evidence of quality; it could itself trigger rubber-stamping warnings.
4. Cross-question pattern extraction produced more durable scientific structure than isolated hypotheses.
5. Rival explanations and decisive failure conditions converted attractive stories into falsifiable working theories.
6. Deterministic experiments could falsify broad explanations and identify boundary conditions without generating any new hypotheses.
7. The strongest concrete result was that persistent conditional undercoverage in sparse-subgroup geometry was not explained by calibration sample size alone.
8. In the synthetic experiments, inverse-probability scoring with marginal conditioning was the most dangerous combination, while distance-to-class-centroid scoring with region-Mondrian conditioning was the safest tested combination.
9. Increasing calibration size from 50 to 600 did not repair the structural failures. The average coverage gap slightly worsened rather than improving.
10. The project’s real contribution was therefore reframed as disciplined filtering, pattern extraction, rival generation, falsification design, deterministic execution, validation, and working-theory updates.

The new name and framing are:

Meno-J Falsification Engine

and, in full:

Meno-J: A Falsification-Oriented Architecture for AI

The new core statement is:

Speculation is only the input. The contribution is disciplined filtering, pattern extraction, rival generation, falsification, execution, and validated working-theory updates.

Existing experiment outputs, checkpoints, historical stage names, schemas, and results were preserved. The reframing did not rewrite or improve old results retroactively.


================================================================================
2. ORIGINAL SCIENTIFIC PROBLEM
================================================================================

The first research question was:

Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?

Two additional calibration questions were then added:

Q2:
Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?

Q3:
What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?

These questions were chosen to vary specificity while staying within the same scientific domain. Q1 was dataset- and method-specific. Q2 focused on temporal segments and coverage stability. Q3 broadened the focus to subject-level uncertainty mechanisms.


================================================================================
3. SECURITY, REPRODUCIBILITY, AND IMPLEMENTATION RULES
================================================================================

The project followed these security rules throughout:

- The OpenRouter API key was read only from the OPENROUTER_API_KEY environment variable.
- The key was never hardcoded in Python, Markdown, JSON, checkpoint, or output files.
- The key was never intentionally printed.
- OPENROUTER_MODEL was used to select the model through the environment.
- .env was excluded through .gitignore.
- .env.example contained only a placeholder and the intended model name.
- Credential scans were repeatedly run against the project files.
- Credential-pattern scans returned zero matching project files.

The main OpenRouter model used for the model-dependent experiments was:

nvidia/nemotron-3-ultra-550b-a55b:free

A fallback was later requested for the unfinished Q3 portion of Experiment 7:

meta-llama/llama-3.1-8b-instruct:free

That fallback was configured in code but was never actually reached because the final managed sandbox denied outbound socket access before a connection to OpenRouter could be established.

All project file reads and writes used UTF-8 explicitly.

The validation philosophy was “fail loudly.” The pipeline rejected malformed or inconsistent outputs rather than silently correcting scientific content. Important contracts included:

- Exactly 10 Stage 4 hypotheses.
- Exactly one audit per hypothesis.
- Ordered and known hypothesis IDs H1 through H10.
- Exact schema fields, with unexpected or missing fields rejected.
- failure_points exactly equal to the set of checklist fields whose booleans were false.
- Stage 6 and Stage 7 restricted to PASS hypotheses only.
- SALVAGEABLE hypotheses never entered Stage 6 or Stage 7.
- Invalid JSON raised an error and was never checkpointed.
- Valid checkpoints were written only after schema validation.
- Existing valid checkpoints were reused during resume operations.
- Invalid output never overwrote a valid checkpoint.

The unchanged critical PASS checks were:

- variables_measurable
- causal_chain_valid
- confounders_identified
- data_requirements_clear
- mechanism_is_non_generic
- prediction_is_testable

The full audit also recorded:

- base_rate_plausible
- effect_size_plausible

The strict non-generic rule was:

A mechanism is generic if the same explanation would apply to most similar domain problems without modification. A mechanism needed a specific causal path, variable relationship, boundary condition, or domain-specific process. Uncertainty was resolved conservatively by setting mechanism_is_non_generic to false.


================================================================================
4. CORE CODE AND PROJECT STRUCTURE
================================================================================

The main implementation files evolved into the following responsibilities:

schema.py
- Defines exact contracts for hypotheses, audits, enrichment, builders, rivals, falsification tests, cross-question analysis, pattern falsification, and deterministic experiments.
- Enforces exact field sets, IDs, counts, types, PASS rules, and failure-point consistency.
- Now also exposes the architecture identity:
  - Meno-J Falsification Engine
  - Meno-J: A Falsification-Oriented Architecture for AI

prompts.py
- Defines JSON-only prompt adapters.
- Includes the historical Dreamer adapter, strict mechanism filtering, confounder enrichment, Mechanism Builder, Confounder/Rival Builder, Statistical Testability Builder, Rival Prediction Matrix, Falsification Agent, survivor synthesis, and pattern-falsification prompts.
- The Dreamer is now documented as an optional speculative candidate-input adapter rather than the core of the architecture.

llm_client.py
- Reads credentials and model names from environment variables.
- Calls OpenRouter.
- Enforces JSON-object output.
- Implements retry counters, invalid-response handling, invalid-JSON repair, timeout handling, response-shape handling, rate-limit backoff, and credential-safe error logging.
- Was eventually converted from a vendored requests dependency to Python standard-library HTTPS because the managed sandbox denied access to the vendored requests files.

pipeline.py
- Runs the legacy v2, enriched v3, and builder-based v4 paths.
- Computes diagnostics programmatically.
- Enforces PASS-only routing.
- Implements checkpoint reads and writes.
- Contains deterministic Experiment 5 and Experiment 6 simulation, aggregation, ranking, and assessment logic.
- Supports resumable Stage 4.3 batching into H1-H5 and H6-H10 if the complete 10-hypothesis request fails.

Runner files
- run_experiment.py: original Q1 calibration run.
- run_calibration_suite.py: Q2/Q3 and combined Experiment 1 calibration report.
- run_enrichment_ablation.py: v2 versus v3 comparison.
- run_cross_question_analysis.py: Experiment 3 survivor synthesis.
- run_pattern_falsification.py: Experiment 4 pattern falsification and roadmap.
- run_p4_f2_synthetic_geometry.py: Experiment 5 deterministic P4-F2 simulation.
- run_p4_f1_score_conditioning.py: Experiment 6 deterministic P4-F1 comparison.
- run_v4_architecture_ablation.py: checkpointed Experiment 7 v4 builder architecture and ablation.

Validation files under work/
- Validate the original pipeline, enriched pipeline, cross-question analysis, pattern falsification, P4-F2, P4-F1, and v4 architecture ablation.

Checkpoint directories
- Preserve successful model-dependent stages for Experiments 2, 3, 4, and 7.
- Allowed long-running work to resume after invalid JSON, rate limits, malformed envelopes, missing response fields, remote resets, or user interruption.


================================================================================
5. EXPERIMENT 1 — AUDITOR CALIBRATION TEST
================================================================================

Purpose

Experiment 1 tested whether a strict auditor would discriminate among 10 raw speculative hypotheses for each of Q1, Q2, and Q3.

Pipeline

Stage 4: Dreamer generated exactly 10 speculative hypotheses.
Stage 5: Strict Mechanism Auditor audited all 10.
Diagnostics were computed programmatically.
Stage 6 and Stage 7 ran only for PASS hypotheses.

Q1 result

Generated: 10
PASS: 0
SALVAGEABLE: 2
REJECT: 8
Pass survival rate: 0.0%
Salvageable rate: 20.0%

Failed checklist counts:
- confounders_identified: 10
- effect_size_plausible: 10
- data_requirements_clear: 5
- mechanism_is_non_generic: 3
- variables_measurable: 3
- base_rate_plausible: 2
- prediction_is_testable: 2
- causal_chain_valid: 1

Q2 result

Generated: 10
PASS: 0
SALVAGEABLE: 10
REJECT: 0
Pass survival rate: 0.0%
Salvageable rate: 100.0%

Failed checklist counts:
- confounders_identified: 10
- mechanism_is_non_generic: 9

Q3 result

Generated: 10
PASS: 0
SALVAGEABLE: 7
REJECT: 3
Pass survival rate: 0.0%
Salvageable rate: 70.0%

Failed checklist counts:
- confounders_identified: 10
- mechanism_is_non_generic: 3
- causal_chain_valid: 1

Combined interpretation

- All three raw-Dreamer runs produced zero PASS hypotheses.
- confounders_identified failed for 10 of 10 hypotheses in every question.
- Raw speculation consistently omitted adequate rival explanations and confounder-control logic.
- Q1 also failed effect_size_plausible for all 10 hypotheses, showing that the raw mechanisms did not establish whether their proposed effects would be detectable in the data.
- Variation in SALVAGEABLE versus REJECT outcomes showed that the auditor was not merely applying one identical response to every question.
- Stage 6 and Stage 7 remained empty, correctly, because no hypotheses passed.

Main lesson

The baseline experiment did not establish that the auditor was necessarily over-strict. It established that raw speculative generation did not reliably produce statistically complete, confounder-aware, domain-specific mechanisms. This became the motivation for explicit pre-audit contracts.


================================================================================
6. EXPERIMENT 2 — CONFOUNDER ENRICHMENT ABLATION (v3)
================================================================================

Purpose

Experiment 2 compared:

v2 baseline:
Dreamer -> Strict Mechanism Auditor

v3 enriched:
Dreamer -> Confounder Enrichment Agent -> Strict Mechanism Auditor

The v3 enrichment added:

- possible confounders
- control variables
- boring rival explanations
- minimum data needed
- effect-size expectation
- an enriched mechanism containing the control logic

The auditor itself was not softened. The PASS rule remained unchanged.

Q1 v3 result

Generated: 10
PASS: 9
SALVAGEABLE: 0
REJECT: 1
Pass survival rate: 90.0%
Only recorded failed field: mechanism_is_non_generic = 1

Q2 v3 result

Generated: 10
PASS: 7
SALVAGEABLE: 0
REJECT: 3
Pass survival rate: 70.0%
Only recorded failed field: mechanism_is_non_generic = 3

Q3 v3 result

Generated: 10
PASS: 9
SALVAGEABLE: 1
REJECT: 0
Pass survival rate: 90.0%
Salvageable rate: 10.0%
Only recorded failed field: mechanism_is_non_generic = 1

Totals across Q1-Q3

Generated: 30
PASS: 25
SALVAGEABLE: 1
REJECT: 4

Comparison with v2

- Confounder failures fell from 10 per question to zero per question.
- Q1 effect-size failures fell from 10 to zero.
- Q1 generic-mechanism failures fell from 3 to 1.
- Q2 generic-mechanism failures fell from 9 to 3.
- Q3 generic-mechanism failures fell from 3 to 1.
- Stage 6 and Stage 7 now ran because PASS hypotheses existed.

Main lesson

Explicit scientific contracts dramatically changed audit outcomes without changing the auditor. The result supported the importance of structured mechanism completion, confounder control, rival construction, data requirements, and effect-size reasoning. It did not prove that the enriched hypotheses were all true. It showed that they were substantially more audit-ready.

Important caution

A higher PASS count is not automatically better. Later Experiment 7 demonstrated that a 10/10 PASS result can trigger rubber-stamp warnings. Enrichment helps, but selectivity diagnostics are still required.


================================================================================
7. EXPERIMENT 3 — CROSS-QUESTION SURVIVOR SYNTHESIS
================================================================================

Purpose

Experiment 3 did not generate additional hypotheses. It used the 25 validated PASS survivors from Experiment 2 and identified:

- the nine strongest surviving hypotheses
- three strongest survivors per question
- five recurring structural patterns
- three pairwise question comparisons
- three recommended next experiments

Validation results

- Source runs valid: true
- Source PASS survivor count: 25
- Strongest survivor count: 9
- Strongest per question: Q1 = 3, Q2 = 3, Q3 = 3
- Recurring pattern count: 5
- Pairwise comparison count: 3
- Next-experiment recommendation count: 3
- All references were validated PASS hypotheses: true
- Combined analysis valid: true

The nine ranked strongest survivors

1. Q2 H1 — Baroreflex gain and arterial stiffness as physiological traits that shift error distributions and violate exchangeability.
   Strength: large effect expectation, specific causal chain, direct trait measurements, explicit confounder controls, and a conditional conformal falsification test.
   Weakness: specialized hemodynamic measurements could limit sample size and wearable-only generalization.

2. Q3 H6 — Clinical subpopulations such as anxiety-disorder subjects or beta-blocker users create distinct autonomic uncertainty regimes.
   Strength: concrete subpopulations, hierarchical modeling, mixture-model test, and clinical screening.
   Weakness: screening instruments may misclassify clinical subgroup membership.

3. Q2 H4 — Disease progression, ventricular remodeling, and neurohormonal changes outpace calibration-window adaptation.
   Strength: links coverage degradation to LVEF and NT-proBNP and specifies an optimized sliding-window test.
   Weakness: requires long, resource-intensive longitudinal data.

4. Q3 H9 — Physical activity intensity interacts with motion artifacts and stress signatures, producing subject-dependent uncertainty.
   Strength: objective METs, activity-specific classifiers, mixed models, and measurable motion context.
   Weakness: high-resolution synchronization and strap-force measurements may be unavailable.

5. Q2 H8 — Rotational motion and sensor shear create artifacts not captured by accelerometer magnitude.
   Strength: defines a motion artifact index and an MAI-conditioned conformal test.
   Weakness: MAI may not capture electromagnetic or vasomotor artifact sources.

6. Q1 H1 — Sympathetic reactivity produces extreme features and inflated nonconformity scores.
   Strength: explicit causal path and a reactivity-stratified Mondrian test.
   Weakness: requires reliable subject-level autonomic baselines and somewhat arbitrary reactivity bins.

7. Q1 H3 — Rapid autonomic transitions violate exchangeability during stress onset, peak, and recovery.
   Strength: temporal residual structure and block-conformal testing.
   Weakness: transition phases can be ambiguous and block methods reduce effective calibration size.

8. Q1 H6 — Softmax-margin nonconformity is misaligned with multimodal feature geometry.
   Strength: direct comparison with distance- and quantile-based scores.
   Weakness: if every score fails, score mismatch cannot be cleanly separated from deeper distribution shift.

9. Q3 H1 — Baseline autonomic tone controls the dynamic range and signal-to-noise ratio of stress responses.
   Strength: mixed-effects design separating within- and between-subject variation.
   Weakness: controlled stress tasks and standardized baselines may not generalize to ecological settings.

The five recurring structural patterns

P1 — Inter-subject physiological heterogeneity violating exchangeability

Stable subject traits such as autonomic reactivity, baroreflex gain, arterial stiffness, baseline HRV/SCL, medication, or clinical subgroup shift the conditional feature or error distribution. A marginal calibration pool mixes these regimes, causing subgroup or subject undercoverage.

Meta-prediction: conditioning directly on the relevant physiological traits should restore coverage across trait strata without per-subject recalibration.

P2 — Temporal non-stationarity and calibration-window mismatch

Rapid autonomic transitions, circadian phase, disease progression, and activity changes shift the data faster than the calibration window adapts.

Meta-prediction: state-aware conditioning should maintain coverage where static or slowly adapting calibration fails.

P3 — Sensor and measurement artifacts inducing distribution shift

Electrode impedance, motion shear, strap tension, firmware differences, missingness, and signal-quality drift distort features in subject- and time-dependent ways.

Meta-prediction: explicit artifact proxies or corrections should restore coverage for affected segments.

P4 — Methodological sensitivity to nonconformity score and conditioning strategy

Coverage depends on whether the score geometry and local conditioning strata match the actual feature and error structure.

Meta-prediction: systematic score-by-conditioning comparisons should expose a combination that restores conditional coverage and reveals the structural mismatch.

P5 — Hidden stratification and label noise from unobserved subpopulations

Clinical, demographic, behavioral, missingness, and labeling subgroups create mixture distributions whose minority regimes are poorly represented by marginal quantiles.

Meta-prediction: latent subgroup inference and subgroup-conditional conformal prediction should restore coverage and align inferred groups with external markers.

Recommended experiments from Experiment 3

E3.1 — Conditional conformal prediction with direct physiological trait measurements, targeting P1.

E3.2 — State-aware conformal prediction across circadian phase, disease progression, and activity intensity, targeting P2.

E3.3 — Systematic comparison of nonconformity scores and conditioning strategies for multimodal stress detection, targeting P4.

Main lesson

The synthesis showed that the durable output was not a single generated hypothesis. The durable output was a small set of recurring causal structures that appeared across independently phrased questions and multiple surviving hypotheses.


================================================================================
8. EXPERIMENT 4 — PATTERN FALSIFICATION STUDY AND RESEARCH ROADMAP
================================================================================

Purpose

Experiment 4 treated the nine survivors and five patterns as a working theory and attempted to disprove each pattern. It generated no new hypotheses. For every pattern it specified:

- the strongest competing explanation
- evidence supporting the competitor
- evidence refuting the competitor
- distinguishing experiments
- measurable outcomes
- expected effect sizes
- required datasets and metadata
- implementation difficulty
- novelty relative to conformal-prediction literature
- scientific impact, feasibility, publication potential, and information gain

Literature validation

Eight primary literature sources were recorded and validated, covering conditional conformal validity, limits of distribution-free conditional coverage, regression conformal prediction, covariate shift, adaptive prediction sets, adaptive conformal inference, time-series conformal prediction, and conformal prediction beyond exchangeability.

Citation validation results:

- All literature citations valid: true
- Unknown citation count: 0
- All hypothesis references valid: true

Strongest competing explanations

P1 competitor
Subject-level signal quality, device fit, skin/device interface, and motion burden may cause heteroscedastic classifier errors. Physiological traits may only proxy for these technical differences.

P2 competitor
The feature-to-label relationship may drift because of habituation, sensitization, or contextual reinterpretation. The problem may be classifier concept drift rather than error-distribution non-stationarity alone.

P3 competitor
Intrinsic physiological heteroscedasticity may remain even after perfect artifact removal. Artifact correction may reduce one variance source without solving state-dependent noise.

P4 competitor
Apparent score and conditioning sensitivity may be a finite-sample bias-variance effect. Fine strata reduce effective calibration size; covariance-based scores are unstable in high dimensions; rankings might reverse at larger sample sizes.

P5 competitor
The apparent hidden strata may be ordinary classifier misspecification in underrepresented feature regions. Better classifier calibration might solve the problem without latent-variable conformal methods.

Ranked research roadmap

1. P5-F1 — Classifier Calibration vs. Latent Variable Conformal Prediction for Hidden Stratification
   Priority: 4.50
   Difficulty: MEDIUM

2. P4-F2 — Synthetic Feature Geometry Stress Test for Nonconformity Scores
   Priority: 4.40
   Difficulty: LOW

3. P1-F1 — Physiological vs. Signal-Quality Conditioning in Multi-Subject Conformal Stress Detection
   Priority: 4.25
   Difficulty: HIGH

4. P2-F1 — Disentangling Classifier Drift from Error Distribution Shift in Longitudinal Conformal Stress Detection
   Priority: 4.25
   Difficulty: HIGH

5. P4-F1 — Nonconformity Score and Conditioning Strategy Comparison Across Sample Sizes
   Priority: 4.25
   Difficulty: LOW

6. P1-F2 — Counterfactual Simulation of Physiological vs. Technical Heterogeneity
   Priority: 3.90
   Difficulty: MEDIUM

7. P3-F1 — Artifact vs. Intrinsic Heteroscedasticity with MAI and Physiological State
   Priority: 3.90
   Difficulty: MEDIUM

8. P2-F2 — Controlled Induction of Autonomic Transitions vs. Classifier Drift
   Priority: 3.75
   Difficulty: MEDIUM

9. P5-F2 — Missingness Mechanism and Label Noise with Selection-Model Conformal Prediction
   Priority: 3.75
   Difficulty: MEDIUM

10. P3-F2 — Strap Tightness and Electrode Impedance Controlled Perturbation Study
    Priority: 3.40
    Difficulty: LOW

Validation results

- No new hypotheses generated: true
- Working-theory survivor count: 9
- Working-theory pattern count: 5
- Pattern study count: 5
- Distinguishing experiment count: 10
- Roadmap ranked programmatically: true

Main lesson

Experiment 4 changed the unit of progress. Progress no longer meant generating more explanations. Progress meant identifying what observation would eliminate or weaken each recurring explanation and ranking the experiments that would produce the most information.


================================================================================
9. EXPERIMENT 5 — P4-F2 SYNTHETIC FEATURE-GEOMETRY STRESS TEST
================================================================================

Purpose

Experiment 5 executed the second-ranked low-difficulty P4-F2 roadmap item. It tested the competitor:

Apparent score/conditioning sensitivity is a finite-sample bias-variance effect.

No LLM or API key was used. The experiment was deterministic simulation only.

Synthetic setup

Classifier:
- NumPy regularized linear discriminant analysis
- 3 classes
- 6-dimensional features
- 2,000 training samples per condition and seed
- 4,000 test samples per condition and seed

Geometries:
- well-separated Gaussian clusters
- overlapping Gaussian clusters
- imbalanced class geometry
- sparse subgroup geometry
- covariate-shifted test geometry

Nonconformity scores:
- margin score
- inverse-probability score
- distance-to-class-centroid score

Conditioning:
- marginal
- class-Mondrian

Calibration sizes:
- 50
- 100
- 300

Seeds:
- 0, 1, 2, 3, 4

Target coverage:
- 0.90

Finite conformal quantile:
- ceil((n+1) * (1-alpha)) order statistic

Metrics:
- marginal coverage
- class-conditional coverage
- region/subgroup coverage
- maximum coverage gap from target
- minimum group coverage
- average prediction-set size
- fraction of evaluated groups below target coverage

Result volume

- 450 seed-level result rows
- 90 aggregate rows

Final P4-F2 assessment

Status: FALSIFIED

Meaning: the broad finite-sample-only explanation was falsified. This did not mean every aspect of P4 was false. It meant calibration variance alone could not explain the observed score/conditioning sensitivity.

Strongest failure against the finite-sample-only explanation

sparse_subgroup_geometry / inverse_probability_score / marginal

At n = 300:
- mean coverage gap: 0.7462
- mean minimum group coverage: 0.1538

Strongest support for a size effect

overlapping_gaussian_clusters / distance_to_class_centroid_score / class-Mondrian

- mean gap at n = 50: 0.1085
- mean gap at n = 300: 0.0329
- absolute reduction: 0.0755

Overall mean coverage gap by size

- n = 50: 0.2603
- n = 100: 0.2883
- n = 300: 0.2894

The relative mean gap reduction from 50 to 300 was negative: approximately -11.2%. In other words, the average gap worsened rather than shrinking.

Additional decision metrics

- Relative score/conditioning sensitivity reduction: approximately 9.7%
- Persistent severe failure cells across all sizes: 14
- Persistent large-n failure cells: 15

Validation and reproducibility

- New hypotheses generated: 0
- Upstream successful stages rerun: false
- Model call used: false
- Effect-size targets present: true
- Failure conditions present: true
- Credential found in project files: false
- Normal run and clean no-key replay both succeeded.
- All four output SHA-256 hashes were byte-identical across replay.

Implementation constraint and recovery

scikit-learn was not available. Instead of downloading or adding a hidden dependency, the classifier was implemented transparently in NumPy as regularized LDA. This kept the experiment self-contained and reproducible.

Main lesson

Some failures were size-dependent, but the strongest sparse-subgroup failures were structural. Increasing calibration size alone was not a sufficient remedy.


================================================================================
10. EXPERIMENT 6 — P4-F1 SCORE AND CONDITIONING COMPARISON
================================================================================

Purpose

Experiment 6 followed Experiment 5 by asking:

Which nonconformity score and conditioning strategy fails under which geometry, and does increasing calibration size fix it?

No LLM or API key was used.

Design extension

The five geometries and three scores from Experiment 5 were retained.

Conditioning strategies were expanded to:

- marginal
- class-Mondrian
- region/subgroup-Mondrian

Calibration sizes were expanded to:

- 50
- 100
- 300
- 600

Seeds remained 0 through 4.

Result volume

- 900 seed-level result rows
- 180 aggregate rows
- 45 geometry-by-score-by-conditioning trajectories
- 15 persistent failure cases at n = 600

Persistent failure rule

A trajectory was a persistent failure if, at n = 600:

- mean coverage gap remained greater than 0.15, or
- mean minimum group coverage remained below 0.75.

Final assessment

Status: STRUCTURAL_FAILURE_CONFIRMED

15 of 45 geometry/score/conditioning cells still failed at n = 600.

Most robust score

distance_to_class_centroid_score

At n = 600 across its evaluated cells:
- mean coverage gap: approximately 0.1218
- mean minimum group coverage: approximately 0.7911
- mean set size: approximately 2.2311
- persistent failure count: 3

Most robust conditioning strategy

mondrian_region

At n = 600:
- mean coverage gap: approximately 0.0903
- mean minimum group coverage: approximately 0.8370
- mean set size: approximately 1.6753
- persistent failure count: 2

Safest score-conditioning pair

distance_to_class_centroid_score + mondrian_region

At n = 600:
- mean coverage gap: approximately 0.0645
- mean minimum group coverage: approximately 0.8656
- mean set size: approximately 2.2095
- persistent failures: 0

Most dangerous score-conditioning pair

inverse_probability_score + marginal

At n = 600:
- mean coverage gap: approximately 0.4209
- mean minimum group coverage: approximately 0.4838
- mean set size: approximately 1.1766
- persistent failure count: 3

Worst geometry

sparse_subgroup_geometry

Strongest structural failure

sparse_subgroup_geometry / inverse_probability_score / marginal

At n = 600:
- mean coverage gap: 0.7591
- mean minimum group coverage: 0.1409

Strongest beneficial size effect

overlapping_gaussian_clusters / margin_score / class-Mondrian

- gap at n = 50: 0.1128
- gap at n = 600: 0.0286
- reduction: 0.0842

Global size trend

- Mean gap at n = 50: 0.2119
- Mean gap at n = 600: 0.2222
- Initial failure cells at n = 50: 13
- Initial failures repaired by n = 600: 0
- Persistent failures at n = 600: 15

Thus, increasing calibration size did not fix the failure pattern. The average gap slightly increased and two additional cells crossed the failure threshold by n = 600.

Validation and reproducibility

- New hypotheses generated: 0
- Upstream successful stages rerun: false
- Model call used: false
- Effect-size targets present: true
- Failure conditions present: true
- Credential found in project files: false
- 900 seed-level rows validated.
- 180 aggregates validated.
- 45 trajectories validated.
- Normal and no-key replay outputs were byte-identical.

Important limitation

Region-Mondrian conditioning used generator-defined observable regions. An unseen test region received an infinite conservative threshold, which preserves coverage by producing potentially uninformative large prediction sets. Therefore, “most robust” means most robust under the tested coverage-oriented ranking, not universally best in efficiency or real-world deployability.

Other limitations

- Regularized LDA is not a deep wearable classifier.
- Gaussian synthetic geometry cannot reproduce every physiological, temporal, labeling, and sensor-quality effect.
- Five seeds do not characterize extremely rare tails.
- Region labels were known from the generator rather than estimated from noisy real embeddings.

Main lesson

The score/conditioning choice mattered structurally. Sparse minority geometry remained a severe failure regime even at larger calibration size. Conservative local conditioning and geometry-aware scores were safer than marginal inverse-probability scoring, but real-data validation remained necessary.


================================================================================
11. EXPERIMENT 7 — v4 ARCHITECTURE UPGRADE AND ABLATION
================================================================================

Purpose

Experiment 7 compared:

v2:
Dreamer -> Strict Mechanism Auditor

v3:
Dreamer -> Confounder Enrichment -> Strict Mechanism Auditor

v4:
Dreamer -> Mechanism Builder -> Confounder/Rival Builder -> Statistical Testability Builder -> Strict Mechanism Auditor -> PASS-only Rival Prediction Matrix -> PASS-only Falsification Agent

Builder contracts

Mechanism Builder added:
- mechanism variables
- causal path
- expected direction
- domain-specific boundary conditions
- measurable outcomes

Confounder/Rival Builder added:
- possible confounders
- control variables
- boring rival explanations
- rival prediction
- distinguishing condition

Statistical Testability Builder added:
- effect-size expectation
- effect-size rationale
- minimum data needed
- testable prediction
- failure condition
- statistical test plan

Checkpointing and resume behavior

Every valid stage was checkpointed independently:

- stage_4
- stage_4_1
- stage_4_2
- stage_4_3
- stage_5
- stage_6
- stage_7

Invalid JSON or schema-invalid output was never checkpointed. Resume operations began from the latest valid checkpoint.

Q1 v4 result

Model: nvidia/nemotron-3-ultra-550b-a55b:free

Generated: 10
PASS: 9
SALVAGEABLE: 1
REJECT: 0
Pass survival rate: 90.0%

Failed fields:
- prediction_is_testable: 1
- variables_measurable: 1

Builder diagnostics:
- Mechanism Builder rows: 10
- Confounder/Rival Builder rows: 10
- Statistical Testability Builder rows: 10
- Average mechanism variables per hypothesis: 5.2
- Average confounders per hypothesis: 3.0
- Average rivals per hypothesis: 2.0
- Hypotheses with effect-size expectation: 10
- Hypotheses with failure condition: 10
- Hypotheses with testable prediction: 10

Stage 6 rows: 9
Stage 7 rows: 9
Rubber-stamp red flags: none

Q2 v4 result

Model: nvidia/nemotron-3-ultra-550b-a55b:free

Generated: 10
PASS: 10
SALVAGEABLE: 0
REJECT: 0
Pass survival rate: 100.0%

Builder diagnostics:
- Mechanism Builder rows: 10
- Confounder/Rival Builder rows: 10
- Statistical Testability Builder rows: 10
- Average mechanism variables per hypothesis: 5.1
- Average confounders per hypothesis: 3.0
- Average rivals per hypothesis: 3.0
- Hypotheses with effect-size expectation: 10
- Hypotheses with failure condition: 10
- Hypotheses with testable prediction: 10

Stage 6 rows: 10
Stage 7 rows: 10

Q2 rubber-stamp red flags:
- 10/10 passed
- 0 rejection reasons
- all checklist values true
- no salvageable or rejected hypotheses

Interpretation of Q2

Q2 showed why PASS rate alone could not be the architecture’s success metric. The builders made every hypothesis appear complete enough to pass, but the diagnostic layer correctly warned that the result might be indiscriminate. This directly supported the later reframing away from generation/building as the main contribution.

Q3 v4 current state

Q3 was not completed.

Valid checkpoints exist for:
- Stage 4
- Stage 4.1
- Stage 4.2

Missing stages:
- Stage 4.3
- Stage 5
- Stage 6
- Stage 7

Missing outputs:
- Experiment 7 v4 Q3 JSON
- Experiment 7 v4 Q3 summary
- Combined v2/v3/v4 ablation JSON
- Combined v2/v3/v4 ablation Markdown

The final Experiment 7 validator correctly fails because Q3 and the combined report are absent. Existing Q1 and Q2 outputs individually pass the full v4 schema validator.

Experiment 7 failures and recoveries

The primary free model repeatedly experienced:

- HTTP 429 rate limits
- malformed HTTP JSON envelopes
- syntactically valid envelopes without a choices field
- remote TLS/connection resets
- very long provider response times

The pipeline recovered valid Q1 and Q2 work by checkpointing every completed stage. It did not rerun Q1 or Q2 after their final outputs were validated.

Observed automatic retries during the primary-model recovery sequence:

- Total automatic retries observed: 11
- Invalid-response-shape retries: 3
- HTTP 429 retries: 8
- Timeout retries: 0
- Model-content JSON repair attempts: 0

Two earlier provider failures occurred before their exact retry cases were added:

- one malformed response envelope
- one response missing assistant choices

Those failures were recovered by resuming from the latest valid checkpoint.

Fallback strategy implemented

The code was extended to support:

- Q3-only execution
- combine-only execution
- fallback model metadata
- 300-second request timeout
- four retries
- HTTP 429 waits of 60, 120, 180, and 240 seconds
- 60-second retry after remote connection reset
- invalid-response-shape retry
- invalid-JSON repair prompt
- Stage 4.3 full-batch attempt
- Stage 4.3 fallback batches H1-H5 and H6-H10
- validation of merged IDs before checkpointing

Requested fallback model:

meta-llama/llama-3.1-8b-instruct:free

The fallback model was not actually used. The final managed execution environment rejected the network escalation request and then denied outbound sockets with Windows error 10013. The failure occurred before OpenRouter was contacted. Consequently:

- The fallback architecture exists in code.
- No fallback response was received.
- No fallback-model checkpoint was written.
- Stage 4.3 was not chunked in an executed run.
- Q3 remains resumable from Stage 4.2 when network access is available.


================================================================================
12. ARCHITECTURE REFRAMING
================================================================================

Old framing

Dreamer -> Builder stages -> Auditor -> Falsification

Problem with the old framing

- It over-emphasized the Dreamer.
- It made perceived project quality depend too heavily on LLM-generated hypothesis quality.
- It risked treating fluent or detailed generation as scientific contribution.
- Experiment 1 showed raw speculation could fail every audit.
- Experiment 7 Q2 showed detailed builders could also produce suspiciously universal PASS results.
- The most decisive scientific findings came from cross-hypothesis structure, rival explanations, failure conditions, and deterministic execution rather than from generating more hypotheses.

New framing

Speculation is only the input.

The real contribution is disciplined filtering, pattern extraction, rival generation, falsification, execution, and working-theory updates.

New architecture

Candidate intake
-> contract normalization
-> strict mechanism filtering
-> failure diagnostics
-> cross-candidate pattern extraction
-> rival generation
-> falsification design
-> deterministic execution and validation
-> working-theory update

Candidate intake is source-agnostic. Candidates can come from:

- human experts
- LLMs
- literature
- prior experiments
- automated search
- curated hypothesis banks

Historical Dreamer remains supported as one optional intake adapter. It does not receive epistemic privilege.

Historical terminology mapping

Dreamer
-> optional speculative candidate-intake adapter

Builder stages
-> contract normalization

Strict Mechanism Auditor
-> strict mechanism filter

Survivor synthesis
-> cross-candidate pattern extraction

Rival Prediction Matrix
-> rival generation and discriminating predictions

Falsification Agent
-> falsification design

Experiment pipeline
-> checkpointed evidence workflow

The new canonical architecture document is:

outputs/meno_j_falsification_engine_architecture.md

The project README now introduces the Meno-J Falsification Engine and links to the canonical architecture document.

Preservation verification

Before reframing, the output directory contained 34 existing files. After adding the architecture document, a hash manifest was recomputed over the original 34 files. The manifest SHA-256 matched exactly:

839E74C7C9B7DE98150F3064BB60EDFF223E322B3828EE92E10134E7A4AAB02E

Therefore all 34 pre-existing outputs remained byte-for-byte unchanged. Existing checkpoints were not deleted or rewritten. No model call was made during reframing.


================================================================================
13. MAJOR SCIENTIFIC FINDINGS ACROSS THE PROJECT
================================================================================

Finding 1 — Raw hypothesis generation was not enough

All 30 raw v2 hypotheses across three questions failed to PASS. The universal confounder-control failure showed that raw speculative mechanisms were incomplete in a systematic way.

Finding 2 — Explicit contracts improved audit readiness

Confounder enrichment raised total PASS count from 0 of 30 to 25 of 30 without loosening the auditor. Mechanism quality depended strongly on explicit confounders, controls, rivals, data, and effect-size expectations.

Finding 3 — More PASS is not always better

Experiment 7 Q2 produced 10/10 PASS and triggered four rubber-stamp red flags. Selectivity and failure diversity must be monitored. A system that always passes richly formatted hypotheses can still be poorly calibrated.

Finding 4 — Recurring structures were more durable than isolated hypotheses

The 25 v3 survivors compressed into nine strongest examples and five recurring patterns. These patterns created a tractable working theory spanning physiological heterogeneity, time, sensors, methods, and hidden strata.

Finding 5 — Rival generation changed the scientific value of the output

Each pattern was paired with a strong competing explanation. This prevented the preferred explanation from becoming a one-sided story and made it possible to design decisive comparisons.

Finding 6 — Falsification was a positive result

Experiment 5 falsified the broad claim that P4 sensitivity was only a finite-sample bias-variance effect. Eliminating this explanation was a successful scientific output.

Finding 7 — Sparse subgroup geometry was the most dangerous tested regime

The worst failures repeatedly appeared in sparse_subgroup_geometry. Minority geometry can remain severely under-covered even when marginal coverage appears acceptable.

Finding 8 — Marginal inverse-probability scoring was the most dangerous tested pair

At n = 600, inverse_probability_score + marginal had a mean gap around 0.4209 and mean minimum group coverage around 0.4838 across geometries. Its strongest sparse-subgroup case had gap 0.7591 and minimum coverage 0.1409.

Finding 9 — Geometry-aware scoring and local conditioning were safer

distance_to_class_centroid_score + mondrian_region had no persistent failures under the tested ranking and achieved mean gap around 0.0645 at n = 600. This result is conditional on known synthetic regions and a conservative unseen-region rule.

Finding 10 — More calibration data did not solve structural mismatch

No cell that met the failure rule at n = 50 was repaired by n = 600. Mean gap changed from 0.2119 to 0.2222. The result directly contradicted the idea that calibration size alone would wash out the problem.

Finding 11 — Coverage and usefulness must be evaluated together

Conservative conditioning can restore coverage by increasing set size. A method should not be called universally superior based only on coverage; prediction-set efficiency and the treatment of unseen strata also matter.

Finding 12 — The best project-level result was an evidence workflow

The project’s strongest reusable contribution became the architecture that converts uncertain candidates into auditable contracts, survivor patterns, rivals, failure conditions, experiments, and validated theory updates.


================================================================================
14. ENGINEERING AND OPERATIONAL CONSTRAINTS
================================================================================

OpenRouter free-model reliability

The free primary model was slow and intermittently unavailable. The project encountered long-running responses, repeated HTTP 429 errors, malformed envelopes, missing choices, and remote connection resets.

Network permission changes

Earlier runs could use approved escalated network execution. Later, the permission profile disabled sandbox escalation. The final environment denied outbound sockets entirely. This prevented completion of Experiment 7 Q3 even after fallback-model support was implemented.

Vendored HTTP dependency access

The project contained a vendored requests installation, but the managed sandbox later denied read access to those files. The client was converted to Python standard-library urllib HTTPS to remove that local dependency. The standard-library client compiled, but network policy still blocked outbound sockets.

Model output format

The project required JSON-only model output. Provider responses could still be malformed or structurally incomplete. The client was extended to distinguish:

- malformed provider JSON envelope
- missing assistant choices/content
- invalid model-content JSON
- HTTP rate limits
- network errors
- timeouts

Only validated JSON was checkpointed.

Library availability

scikit-learn was unavailable for deterministic simulations. The solution was a transparent NumPy regularized LDA implementation rather than downloading a new dependency.

Windows execution environment

The project used PowerShell and a bundled Python runtime. Some commands required Windows-specific environment-variable syntax, permissions, and path handling. A few read-only PowerShell probes had quoting or formatting errors; these did not alter project data.

No local Git metadata

At one stage, no local .git metadata was available in the project directory, so changed-file reporting relied on direct file inventories and hashes rather than Git status.

Long-running model stages

Some requests remained open beyond the nominal timeout because transport activity prevented the underlying read timeout from firing as a strict wall-clock limit. Checkpoint inspection was used to determine whether the process had silently advanced.

Synthetic-to-real gap

Experiments 5 and 6 were controlled simulations. Their structural findings are strong within the designed geometries but are not a substitute for validation on real multi-subject wearable datasets with subject, activity, sensor-quality, clinical, and temporal metadata.

Conditional coverage limits

Exact distribution-free object-conditional coverage is generally impossible without assumptions. The project therefore evaluated meaningful group, class, region, and state conditions rather than claiming universal conditional validity.


================================================================================
15. RECOVERED ISSUES AND WHY CHECKPOINTING MATTERED
================================================================================

Recovered issue: raw mechanisms lacked confounders
Solution: added a separate enrichment contract while leaving the auditor strict.

Recovered issue: effect-size plausibility was absent
Solution: required explicit small/medium/large/unknown expectation, rationale, minimum data, prediction, and failure condition.

Recovered issue: malformed LLM JSON
Solution: fail loudly, request one JSON repair, and never checkpoint invalid content.

Recovered issue: provider envelope was malformed
Solution: added malformed-envelope retries.

Recovered issue: provider response omitted choices
Solution: added invalid-response-shape retries.

Recovered issue: HTTP 429
Solution: added bounded retries and increasing 60/120/180/240-second backoff.

Recovered issue: remote reset
Solution: added 60-second network retry.

Recovered issue: full Stage 4.3 could be too large
Solution: added independent H1-H5 and H6-H10 batch checkpoints and exact merged-ID validation.

Recovered issue: process interruption
Solution: resume from the latest validated stage instead of restarting the question.

Recovered issue: external HTTP dependency became unreadable
Solution: replaced it with standard-library HTTPS.

Recovered issue: deterministic simulations lacked scikit-learn
Solution: implemented regularized LDA with NumPy.

Recovered issue: concern that reframing might alter evidence
Solution: verified a stable manifest hash over all 34 pre-existing outputs before and after reframing.


================================================================================
16. VALIDATION AND REPRODUCIBILITY RECORD
================================================================================

Experiment 1
- Exactly 10 hypotheses per question.
- Audit count matched hypothesis count.
- IDs validated.
- failure_points consistency validated.
- Stage 6/7 PASS-only routing validated.

Experiment 2
- Existing v2 results reused.
- v3 checkpoints preserved.
- Enrichment count exactly 10 per question.
- Auditor remained unchanged.

Experiment 3
- All 25 source survivors referenced validated PASS hypotheses.
- Nine strongest survivors selected, three per question.
- Five patterns, three pairwise comparisons, and three recommendations validated.

Experiment 4
- Five pattern studies and ten distinguishing experiments validated.
- All literature citation IDs valid.
- Unknown citation count zero.
- Roadmap ranked programmatically.

Experiment 5
- 450 seed rows and 90 aggregates validated.
- Normal and no-key replays produced identical hashes.

Experiment 6
- 900 seed rows, 180 aggregates, and 45 trends validated.
- Normal and no-key replays produced identical hashes.

Experiment 7
- Q1 and Q2 complete v4 artifacts validate independently.
- Q1 and Q2 each have valid Stage 4 through Stage 7 checkpoints.
- Q3 has valid Stage 4 through Stage 4.2 checkpoints.
- Full Experiment 7 validator fails, correctly, because Q3 and combined outputs are missing.

Architecture reframing
- No model calls.
- No experiment reruns.
- Python compilation passed.
- Existing output manifest unchanged.
- Credential scan returned zero matching files.


================================================================================
17. CURRENT PROJECT STATE
================================================================================

Complete and validated

- Experiment 1 Q1, Q2, Q3, and combined calibration report
- Experiment 2 v3 Q1, Q2, Q3, and enrichment ablation report
- Experiment 3 cross-question survivor analysis
- Experiment 4 pattern falsification study and reproducibility summary
- Experiment 5 P4-F2 synthetic geometry study and reproducibility summary
- Experiment 6 P4-F1 score/conditioning study and reproducibility summary
- Experiment 7 v4 Q1
- Experiment 7 v4 Q2
- Meno-J Falsification Engine architecture reframing

Incomplete

- Experiment 7 v4 Q3 Stage 4.3 through Stage 7
- Experiment 7 combined v2/v3/v4 report

Exact Q3 resume point

Reuse:
- work/experiment_7_checkpoints/q3/stage_4.json
- work/experiment_7_checkpoints/q3/stage_4_1.json
- work/experiment_7_checkpoints/q3/stage_4_2.json

Start at:
- Stage 4.3 Statistical Testability Builder

Do not rerun:
- Q1
- Q2
- Q3 Stage 4
- Q3 Stage 4.1
- Q3 Stage 4.2


================================================================================
18. RECOMMENDED NEXT WORK
================================================================================

Immediate operational task

Complete Experiment 7 Q3 in an environment that permits outbound HTTPS. Use the fallback model only through OPENROUTER_API_KEY and OPENROUTER_MODEL environment variables. Resume at Stage 4.3. If the full Stage 4.3 request fails, use the implemented H1-H5 and H6-H10 batch path. Then run Stage 5, PASS-only Stage 6, PASS-only Stage 7, combine-only report generation, and the final validator.

Highest-ranked scientific roadmap task

P5-F1: compare ordinary classifier calibration with latent-variable conformal prediction for hidden stratification. This was the highest-ranked Experiment 4 roadmap item by combined scientific impact, feasibility, publication potential, and information gain.

Real-data validation of P4

Apply the safest and most dangerous score-conditioning pairs from Experiment 6 to a real multi-subject wearable dataset. Required metadata should include:

- subject ID
- stress label and label provenance
- activity and posture
- accelerometer-derived motion measures
- signal-quality and missingness indicators
- device/firmware information
- medication and clinical screening where permitted
- time, session, transition phase, and circadian context
- enough calibration observations per class and subgroup

Compare:

- inverse-probability + marginal
- distance-to-centroid + region/subgroup-Mondrian
- margin + class-Mondrian

Report both coverage and prediction-set efficiency.

Architecture research

Future studies should vary the candidate source while keeping the filtering and falsification engine fixed. For example:

- human-only candidate set
- literature-derived candidate set
- LLM-generated candidate set
- mixed human/LLM set

The evaluation should ask whether downstream survivor quality and falsification value remain stable when the intake source changes. This would directly test the new claim that Meno-J is source-agnostic and does not depend on Dreamer quality.


================================================================================
19. FINAL CONCLUSION
================================================================================

The project began by asking whether an LLM could generate mechanisms that survive a strict scientific audit. The baseline answer was largely no: all 30 raw hypotheses failed to PASS, mainly because confounders and statistical detectability were missing.

Adding explicit scientific contracts produced many audit-ready survivors, but high survival created a new risk: a builder-heavy system could make every claim look complete. The project therefore moved beyond hypothesis-level success. It extracted recurring patterns, constructed strong rivals, defined failure conditions, and executed deterministic studies against the most tractable pattern.

Those studies produced the clearest scientific result in the project: the worst conditional undercoverage was structural, concentrated in sparse subgroups, and not repaired by simply increasing calibration size. Inverse-probability scoring with marginal conditioning was consistently dangerous. Geometry-aware distance scoring with region-aware conditioning was safer in the synthetic setting, with important efficiency and realism caveats.

The final architectural insight was that Meno-J should not be presented primarily as a hypothesis generator. Generation is replaceable. The durable contribution is the disciplined evidence workflow around uncertain claims:

filter them,
record why they fail,
extract recurring structures,
construct credible rivals,
define decisive tests,
execute reproducibly,
and update or eliminate the working theory.

That is the Meno-J Falsification Engine.


================================================================================
20. COPY-PASTE SHORT FORM
================================================================================

Meno-J is a falsification-oriented architecture for AI-assisted scientific reasoning. It accepts speculative candidates from any source, normalizes them into explicit scientific contracts, filters them with strict mechanism checks, extracts recurring patterns from survivors, generates rival explanations, designs decisive falsification tests, executes checkpointed experiments, and updates the working theory. The original raw-Dreamer baseline produced zero PASS hypotheses across 30 candidates, primarily because every question lacked adequate confounder control. Enrichment raised survival to 25 of 30 without loosening the auditor, showing that explicit confounder, rival, data, and effect-size contracts matter. Cross-question synthesis compressed the survivors into nine strong hypotheses and five recurring patterns: physiological heterogeneity, temporal non-stationarity, sensor artifacts, score/conditioning sensitivity, and hidden stratification. Pattern falsification generated ten ranked experiments and eight validated primary literature sources. Deterministic P4 experiments then falsified the broad finite-sample-only explanation and confirmed structural sparse-subgroup failure. At n=600, the strongest sparse-subgroup inverse-probability/marginal case had a 0.7591 coverage gap and 0.1409 minimum group coverage. Increasing calibration size did not repair the failures. The safest tested pair was distance-to-centroid scoring with region-Mondrian conditioning; the most dangerous was inverse-probability scoring with marginal conditioning. Experiment 7 showed that builder stages can improve completeness but can also produce 10/10 PASS and rubber-stamp warnings. Q1 and Q2 completed; Q3 remains checkpointed through Stage 4.2 because the primary model was repeatedly rate-limited and the final sandbox blocked outbound sockets before the fallback model could run. The project was therefore reframed as the Meno-J Falsification Engine: speculation is input, while disciplined filtering, pattern extraction, rival generation, falsification, reproducible execution, and working-theory updates are the contribution.

================================================================================
21. EXPERIMENT 8 ADDENDUM: RARE-SUBGROUP FEASIBILITY FRONTIER
================================================================================

Experiment 8 challenged the apparent safety of distance-to-centroid scoring with oracle region-Mondrian conditioning. It varied rare-subgroup prevalence from 0.5% to 30%, total calibration size from 50 to 3,000, two score families, four conditioning/metadata strategies, and 20 deterministic seeds. It produced 6,720 seed-level rows, 336 aggregate cells, and 42 exact binomial feasibility rows without using an LLM, an API key, or rerunning Experiment 6.

The primary decision was ORACLE_SAFETY_PARTLY_VACUOUS_AND_METADATA_FRAGILE. For prevalence at or below 2% and calibration size at or below 600, oracle region conditioning produced mean true rare-group coverage of 0.9920, but the mean rare-group prediction-set size was 2.9809 of three labels and the full three-label set was returned 99.01% of the time. Only 10.42% of the relevant design seeds had a finite rare-region threshold. Coverage was therefore achieved largely through conservative, nearly non-discriminating output.

The finite-sample boundary is exact. At alpha=0.10, a region needs at least nine calibration observations before the split-conformal quantile can be finite. With total calibration size 600, the probability of meeting that minimum is approximately 0.0037 at 0.5% prevalence, 0.1517 at 1% prevalence, and 0.8476 at 2% prevalence. A 0.5%-prevalence subgroup needs total calibration size 2,884 for a 95% probability of a finite threshold and 3,476 for 99%. A 1%-prevalence subgroup needs 1,441 and 1,736 respectively. A 2%-prevalence subgroup needs 719 and 866 respectively.

Metadata quality was a major boundary condition. The strongest tested penalty occurred at 0.5% prevalence and calibration size 600 under moderately noisy region metadata: true rare-group coverage fell from 1.0000 with oracle metadata to 0.3537, a 0.6463 absolute penalty. The oracle returned a mean rare-group set size of 3.0000, while noisy routing returned 1.4360 and substantially undercovered the true rare group.

A secondary diagnostic found no tested distance-score oracle-region cell that simultaneously achieved mean true rare-group coverage of at least 0.88 and a mean rare-group full-set fraction at or below 0.20. This was recorded after applying the preregistered primary decision rule and was not retroactively added to that rule.

The working theory is now narrower: region conditioning can repair formal subgroup coverage only when the subgroup is identifiable, adequately represented in calibration data, and capable of supporting informative thresholds. Coverage must be reported jointly with effective subgroup calibration size, the probability of a finite threshold, prediction-set size, full-set frequency, empty-set frequency, and metadata quality. Coverage alone can mistake abstention-like full sets for successful uncertainty calibration.

Experiment 8 passed an independent validator that rebuilt the complete deterministic report, reproduced the scientific JSON and Markdown byte-for-byte, recomputed the analytic frontier, verified the Experiment 6 checkpoint hash, decoded all outputs as UTF-8, and passed the credential scan.

================================================================================
22. EXPERIMENT 9 ADDENDUM: WESAD REAL-DATA FALSIFICATION
================================================================================

The official WESAD archive supplied by the user resolved the earlier partial-download blocker. The 2,249,444,501-byte ZIP had SHA-256 5e15d2606adf16d819ba535c1786d92e94bae5ff5392f7ae01fb63f9938fd71c. All 92 entries and 76 files passed the ZIP CRC test, no unsafe paths were present, and all 17,578,304,666 uncompressed bytes were accounted for. The extracted tree contained the expected 15 subjects: S2 through S11 and S13 through S17. Every extracted file matched the archive by size and CRC32 and received a SHA-256 manifest entry.

Before examining coverage, Experiment 9 froze a deterministic protocol. It used 60-second non-overlapping chest-signal windows wholly contained within contiguous baseline, stress, or amusement runs; transition and other labels were excluded. Nine statistics were extracted from nine signal channels for 81 features. Regularized LDA was trained with subject-disjoint splits: ten training subjects, four calibration subjects, and one held-out test subject. Every subject served as the test subject under three deterministic calibration rotations. Three nonconformity scores crossed three conditioning strategies, giving 405 fold results over 535 windows. The raw dataset was not modified, pickle loading was restricted to the minimal NumPy objects required by WESAD, and no LLM, API, or credential was used.

The preregistered primary transfer test was falsified. The synthetic safest pair, distance-to-class-centroid scoring with motion-region Mondrian conditioning, had mean coverage 0.8373, worst-subject coverage 0.3429, average set size 2.4364, and full-set frequency 0.7577. The synthetic dangerous comparator, inverse-probability scoring with marginal conditioning, had mean coverage 0.8671, worst-subject coverage 0.6000, average set size 1.7666, and full-set frequency 0.1985. Thus the purported safe pair reduced worst-subject coverage by 0.2571 and increased full-set frequency by 0.5592. Its paired mean subject-coverage difference was -0.0298 with a subject-bootstrap 95% interval from -0.1060 to 0.0565.

The ranking reversal is scientifically important. It does not prove that inverse-probability/marginal conformal prediction is universally safe; it shows that the synthetic ranking was not portable to this real-data protocol. The result strengthens the falsification-engine framing: simulation-derived rankings are candidates for transfer testing, not conclusions. Real-data evaluation must report tail coverage and prediction-set informativeness together.

Subject heterogeneity remained pronounced. S4 and S2 had mean coverage below 0.59 across all nine methods and fell below 0.80 for every method. S10 and S7 fell below 0.80 for six of nine methods. The best-ranked real-data method was inverse-probability scoring with marginal conditioning; its worst-subject coverage was still only 0.6000, far below the nominal 0.90 target. No tested method solved subject-level undercoverage.

Experiment 9 passed an independent exact replay. The validator reproduced the complete scientific report, confirmed all 15 feature-checkpoint hashes, verified the integrity-report and preregistered-protocol hashes, checked the 535-window and 405-fold contracts, matched the Markdown to the JSON, and passed the credential scan.

================================================================================
23. EXPERIMENT 10 ADDENDUM: CALIBRATION ONBOARDING AND COMPATIBILITY
================================================================================

Experiment 10 connected the cold-start failure studied by Meno-J with the personalized regime developed in the BioConformal project. The protocol was frozen before examining Experiment 10 outcomes. It reused the 15 hash-validated Experiment 9 feature checkpoints, loaded no raw WESAD pickles, made no API or model calls, and did not retrain the classifier with personal data.

Every WESAD subject was held out under three deterministic rotations. Regularized LDA was trained on ten external subjects, four external subjects formed the calibration pool, and fifteen label-stratified windows from the held-out subject formed a test set completely disjoint from personal onboarding windows. The experiment compared all four external calibration subjects, the nearest two and farthest two subjects under an unlabeled standardized-centroid distance, and nested personal calibration sets of 3, 6, 9, and 12 labeled windows. This produced 315 method-fold results and 180 single-external-subject compatibility probes.

The preregistered cohort-level personal-repair rule passed. At k=12, mean coverage improved from 0.8785 under all four external calibration subjects to 0.9659 under personal calibration. Worst-subject coverage improved from 0.6000 to 0.8667. Mean full-set frequency rose by only 0.0741 at the cohort level. The paired subject mean coverage change was 0.0874 with a subject-bootstrap 95% interval from 0.0237 to 0.1615.

The targeted S2/S4 informative-repair rule did not pass. S2 coverage rose from 0.6444 to 1.0000, but full-set frequency increased by 0.3556 and its base-classifier accuracy was only 0.5556. S4 coverage rose from 0.6444 to 0.9333, but full-set frequency increased by 0.4222 and classifier accuracy was only 0.3778. Personal thresholds made uncertainty more honest, but much of the apparent repair was achieved by expressing greater ambiguity rather than by making the classifier discriminate the states correctly.

The simple calibration-compatibility proposal also did not pass. Nearest-two calibration reduced the preregistered robustness loss by only 0.0133 relative to the farthest-two negative control, below the required 0.03. Its mean coverage was 0.8222 versus 0.8859 for the farthest pair, although its sets were smaller. A single-subject distance/loss correlation of 0.356 suggests a weak signal, but standardized feature-centroid distance is not sufficient as a selection rule.

The most important conceptual result was a distinction between finite and useful calibration. With three or six personal examples, no finite 90%-coverage split-conformal threshold exists, so the honest output was the full three-label set every time. At nine examples, all thresholds became finite and mean coverage was 0.9467, but full-set frequency remained 0.2281. At twelve examples, coverage increased to 0.9659 while full-set frequency also increased to 0.2830. The first finite threshold is therefore not the same as an informative or stable threshold. At alpha=0.1, the conformal quantile remains an extreme order statistic through this range.

The revised J-jump candidate is a calibration-readiness frontier. A subject moves through distinct stages: no finite personal threshold, finite but extreme threshold, informative threshold, and stable personalized threshold. This is a new testable working concept, not a literature-novelty claim. Its next falsification should extend the onboarding curve beyond the extreme-order-statistic range and separately test representation or sensor-quality interventions for S2 and S4.

Experiment 10 passed independent exact replay. The validator rebuilt all folds without using the Experiment 10 result checkpoint, reproduced the saved report exactly, verified the Experiment 9 prerequisite artifacts and all feature hashes, enforced the personal test/calibration separation and finite-sample boundary, matched the working-theory update to the results, and passed the credential scan.

================================================================================
24. EXPERIMENT 11 ADDENDUM: REPRESENTATION-VERSUS-CALIBRATION FALSIFICATION
================================================================================

Experiment 11 tested four rival explanations for the residual S2/S4 ambiguity from Experiment 10 without loading raw WESAD pickles, calling a model, installing dependencies, or tuning hyperparameters. Its protocol was frozen before outcome analysis. It reused all 15 validated Experiment 9 feature checkpoints and the exact Experiment 10 subject folds and personal test construction. Six nested calibration counts produced 270 frontier rows, and ten fixed representation arms at k=19 produced 450 rows.

The calibration order-statistic transition was real but not safely monotonic. At alpha=0.10, k=18 uses the largest calibration score and k=19 uses the second largest. Moving from k=18 to k=19 reduced mean full-label-set frequency from 0.3081 to 0.1911, but mean coverage fell from 0.9778 to 0.9185 and worst-subject mean coverage fell by 0.1333. The preregistered order-statistic support rule therefore failed. This falsifies the idea that crossing that mathematical boundary is by itself a safe J-jump in calibration readiness.

Subject baseline mismatch received strong cohort-level support. Per-subject median/IQR normalization raised mean classifier accuracy from 0.6578 to 0.8163, reduced mean full-label-set frequency from 0.1911 to 0.0889, and reduced mean robustness loss from 0.1211 to 0.0896 while preserving mean coverage of 0.9111. The effect was sharply subject-dependent: S4 accuracy rose from 0.3778 to 0.9111 and its full-set frequency fell from 0.5111 to zero, whereas S2 accuracy rose only from 0.5556 to 0.6222 and its full-set frequency increased from 0.3111 to 0.6889. Thus the general normalization rule passed but the targeted S2/S4 rule did not.

Sensor-family interference also received exploratory support. Removing temperature features was the only preregistered single-family ablation to pass: S2/S4 mean accuracy improved by 0.1000, their mean robustness loss fell by 0.0417, and overall accuracy improved by 0.0178. This diagnoses predictive interference in the current feature/model combination; it does not establish temperature sensor failure or physiological irrelevance.

Added classifier complexity was not a repair. Fixed diagonal QDA reduced cohort accuracy by 0.0904 and increased S2/S4 full-set frequency by 0.2222. Distance-weighted 15-neighbor classification reduced cohort accuracy by 0.0489 and increased S2/S4 full-set frequency by 0.3778. Neither met the frozen rule.

The revised J-jump candidate is a subject-conditional calibration readiness surface. Useful prediction requires at least two coupled conditions: a stable calibration threshold supported by enough representative examples, and a representation that separates within-subject state from stable subject identity and interfering sensor variation. Crossing the count boundary can make sets smaller while exposing undercoverage; improving representation can transform one subject while leaving another ambiguous. The next decisive test should cross raw versus subject-normalized representations with calibration counts on both sides of the order-statistic boundary and require replication across temporal blocks or independent sessions with subjects declared before analysis.

Experiment 11 passed independent exact replay. The validator rebuilt all 720 result rows, reproduced the scientific report exactly, verified the 90 Experiment 10 continuity rows and all 15 feature-checkpoint hashes, enforced leakage and protocol invariants, matched the working-theory update, decoded all required artifacts as UTF-8, and passed the credential scan.

================================================================================
25. EXPERIMENT 12 ADDENDUM: TEMPORAL READINESS-SURFACE REPLICATION
================================================================================

Experiment 12 challenged the Experiment 11 theory using temporal-block holdout rather than another random window split. Its protocol was frozen before outcome analysis. For each of the 15 WESAD subjects, every early, middle, and late within-state temporal tertile was held out in turn. Personal calibration and held-out-subject normalization used only the other two tertiles. Three deterministic nested draws at k=9, 18, 19, and 20 were crossed with raw/all-feature LDA, raw/no-temperature LDA, normalized/all-feature LDA, and normalized/no-temperature LDA. This produced 2,160 result rows without raw-pickle loading, API calls, dependency installation, or hyperparameter tuning.

Subject baseline normalization replicated strongly. Across the entire temporal grid, accuracy increased by 0.1751, full-label-set frequency fell by 0.1237, mean coverage increased slightly to 0.9244, and worst-subject mean coverage fell by only 0.0360. Accuracy improved by 0.2000 in early holdouts, 0.1955 in middle holdouts, and 0.1298 in late holdouts. The effect therefore cannot be explained only by the random test-window allocation used in Experiment 11.

S4's repair passed its predeclared internal replication rule. Accuracy increased by 0.5245, full-label sets fell by 0.5540, and normalized coverage was 0.9112. Accuracy gains were positive in all temporal blocks: 0.8462 early and 0.3636 in both middle and late windows. S2 remained a separate residual failure: its accuracy improved by only 0.0396, its full-set frequency was essentially unchanged, and normalized coverage was 0.8110. The evidence therefore supports a baseline-mismatch mechanism for S4 and the cohort generally, but not as a complete explanation for every difficult subject.

The order-statistic boundary again failed as a universal readiness jump. Every tested representation returned fewer full-label sets at k=19 than k=18, but none passed the worst-subject-phase safety rule. Raw/all-feature coverage fell by 0.0496 and worst subject-phase coverage fell by 0.0909. Normalized/all-feature coverage fell by 0.0488 and worst subject-phase coverage fell by 0.1608. Smaller prediction sets at the boundary exposed undercoverage rather than guaranteeing useful safe prediction.

The proposed representation-by-calibration readiness-surface interaction was not supported. Raw and normalized representations both classified the boundary as unsafe. Their k=18-to-k=19 coverage changes differed by only 0.0008, and their full-set reductions differed by only 0.0111. The correct response is to narrow the theory: representation quality and calibration safety are both important, but this experiment did not show that they interact.

Temperature-feature interference also did not replicate. Raw temperature removal improved S2/S4 accuracy by 0.0944, just below the frozen threshold, but worsened their robustness loss. After normalization, temperature removal reduced S2/S4 accuracy by 0.0303. The Experiment 11 temperature result is therefore removed from the core working theory and retained only as a split-sensitive exploratory observation.

The revised J-jump candidate is a two-gate subject readiness model. The representation gate asks whether stable subject baseline distortion has been removed sufficiently for physiological states to become discriminable. The calibration gate asks whether the conformal threshold is informative without sacrificing subject-phase coverage. Neither gate occurs at one universal sample count, and passing the representation gate does not imply passing the calibration gate. The next decisive test is independent-session or independent-dataset replication of normalization, followed by predeclared diagnosis of S2-like residual failures.

Experiment 12 passed independent exact replay. The validator regenerated all 2,160 rows without runtime warnings, reproduced the report exactly, checked every temporal test/calibration/normalization separation, recomputed all frozen decisions, verified all 15 feature-checkpoint hashes, matched the theory update, decoded all artifacts as UTF-8, and passed the credential scan.

================================================================================
26. EXPERIMENT 13 PREPARATION: INDEPENDENT DATASET REPLICATION
================================================================================

After Experiment 12, the project reached the limit of what the single-session WESAD cohort could establish. The next falsification requires an independently collected wearable dataset. A source review selected PhysioNet's Wearable Device Dataset from Induced Stress and Structured Exercise Sessions, version 1.0.1, DOI 10.13026/he0v-tf17. PhysioNet reports 36 healthy volunteers in the stress cohort, a 69.7 MB compressed archive, 247.4 MB uncompressed size, open access, and the Open Data Commons Attribution License v1.0.

The dataset uses an Empatica E4 and contains EDA, skin temperature, three-axis accelerometry, BVP, heart rate, IBI, event tags, demographics, and self-reported stress levels. It is a strong external test because it was collected independently of WESAD, has a larger stress cohort, uses a different wearable placement and protocol, and shares EDA, temperature, and acceleration modalities with the Meno-J representation. The planned primary feature space uses only shared EDA, temperature, ACC X/Y/Z, and ACC magnitude summary statistics so sensor names are not mistaken for device equivalence.

The primary label contract will distinguish protocol baseline/rest from cognitive and social stress tasks. Self-reported stress remains a separate secondary outcome. Known primary complete-case exclusions are declared before acquisition outcomes: S02 has duplicated stress signals, f07 had covered PPG and temperature sensors, and f14's stress session is split across files. f14 may enter only a separately validated sensitivity analysis if tag timing supports an unambiguous merge.

The exact scientific protocol is intentionally not yet frozen. First the complete archive must pass size, central-directory, CRC, safe-path, metadata-file, subject-folder, and required-sensor inventory checks. Then a subject/session/tag inventory will be built without calculating scientific outcomes. Only after that inventory will the exact interval mapping, window counts, folds, exclusions, and effect-size rules be frozen.

Direct command-line access to PhysioNet was blocked by the execution environment's outbound socket policy. The in-app browser reached 27,181,002 bytes before its transfer stalled. The partial browser file was preserved in Downloads and was not copied, extracted, or used. A second attempt and the managed download path also stalled at negligible size. No dataset-dependent claim was made.

A UTF-8 Python acquisition gate was prepared and compiled. It searches only for a completed wearable-dataset ZIP, rejects .crdownload files, requires a plausible completed size, tests every ZIP CRC, rejects unsafe paths, verifies official metadata and at least 33 complete stress sensor folders, copies through a hash-checked temporary file, and refuses to overwrite any existing canonical archive or extracted tree. Its dry run failed loudly as designed because no completed ZIP was present.

The official download is https://physionet.org/content/wearable-device-dataset/get-zip/1.0.1/. Once that single archive is placed in Downloads, Experiment 13 can resume from integrity validation without rerunning Experiments 9 through 12.

================================================================================
27. EXPERIMENT 13 RESULT: INDEPENDENT WEARABLE-DATASET REPLICATION
================================================================================

The user completed the official PhysioNet download and extraction. The 73,121,143-byte ZIP had SHA-256 afbff3e8e7230bdc765d0ccfc5c3460964021cdfefa8e351f8ad8f78a1b27c48. All 709 archive members passed the full CRC test, no unsafe paths were present, and 259,375,714 uncompressed bytes were accounted for. The first safe extraction attempt encountered Windows path-length limits because the official archive contains a long common root. That failed staging tree was preserved, the valid archive was not overwritten, and a second safe extractor used a short canonical root while stripping only the single verified common prefix. The resulting extraction contained 37 stress folders and all 37 had the required sensor folders.

A pre-outcome inventory identified 33 primary complete-case subjects. S02, f07, f14_a, and f14_b were excluded under declared data-quality or split-session rules. The inventory also resolved a documentation discrepancy: the V1 recordings contain 13 tags, while the supplied notebook operationalizes the first 12 protocol markers and leaves the final recording-end marker. No outcomes were computed during inventory.

The protocol was then frozen before feature or outcome computation. It used 15-second non-overlapping windows with five seconds trimmed from each stage boundary. Baseline and two rest stages formed the non-stress class; Stroop, TMCT, real-opinion, opposite-opinion, and subtraction tasks formed the stress class where available. Exactly 16 evenly spaced windows per class were selected chronologically for every subject. Each window contained 54 summary features from EDA, temperature, ACC X/Y/Z, and ACC magnitude. No BVP-specific feature was used, keeping the transfer representation limited to shared modalities.

Every subject was held out under three deterministic repetitions. Twenty-four subjects trained a fixed regularized binary LDA, eight different subjects supplied external conformal calibration scores, and the held-out subject contributed sixteen unlabeled onboarding windows used only for normalization statistics plus sixteen disjoint balanced test windows. The study compared raw features with per-subject median/IQR normalization. This produced 198 fold rows. The primary replication required all seven frozen checks to pass, including an accuracy gain of at least 0.08, full-set reduction of at least 0.05, robustness-loss reduction of at least 0.02, normalized mean coverage of at least 0.88, worst-subject safety, positive gains in both protocol versions, and nonnegative change for at least 60% of subjects.

The primary decision was EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED. Raw accuracy was 0.5751 and normalized accuracy was 0.6187, a gain of 0.0436—positive, but below the frozen 0.08 requirement. The paired-subject bootstrap 95% interval was -0.0044 to 0.0890 and included zero. Full-set frequency improved from 0.6856 to 0.5947, a reduction of 0.0909, and robustness loss improved by 0.0374. However, mean coverage fell from 0.8946 to 0.8681, below the frozen 0.88 safety floor. Worst-subject coverage moved from 0.7292 to 0.7083. Accuracy improved in both protocol versions, but heterogeneously: +0.0147 in V1 and +0.0742 in V2. Only 63.64% of subjects had nonnegative accuracy change, with changes ranging from -0.2917 to +0.2292.

This is an informative falsification, not a null result. Normalization made prediction sets less ambiguous and modestly improved discrimination, but the large WESAD repair did not generalize at the preregistered magnitude and the calibrated uncertainty became less safe on average. The working theory is therefore narrowed again: subject-relative normalization is a context-sensitive representation intervention, not a universal repair. Representation and calibration must remain separate gates. A method cannot be promoted as a J-jump because accuracy or efficiency improves while coverage falls below its safety contract.

Experiment 13 passed independent exact replay. The validator rechecked archive size, SHA-256, member count, and every ZIP CRC; verified all 33 feature-checkpoint hashes, shapes, names, and class balances; regenerated all 198 folds without using the fold-result checkpoint; enforced subject-disjoint training, external calibration, onboarding, and testing; recomputed the conformal rank of 232; verified paired-arm split identity and all frozen decision rules; matched the working-theory update to the evidence; decoded all outputs as UTF-8; and passed the credential scan. No LLM, API key, dependency installation, or raw-data mutation was used.

================================================================================
28. EXPERIMENT 14 RESULT: CLASS-CONDITIONAL CALIBRATION REPAIR
================================================================================

Experiment 14 tested the smallest plausible explanation for Experiment 13's normalized coverage failure: a single pooled conformal threshold might redistribute coverage asymmetrically between stress and non-stress. The protocol was frozen before Experiment 14 outcomes. It reused the exact 33 subjects, 54-feature checkpoints, three deterministic repetitions, subject-disjoint training and calibration folds, held-out onboarding windows, test windows, regularized LDA, inverse-probability score, and alpha of 0.10. Only the conformal conditioning rule changed.

Four arms crossed raw versus per-subject normalized representation with marginal versus class-Mondrian calibration. Marginal calibration used 256 external scores and conformal rank 232. Class-Mondrian calibration used 128 scores per class and rank 117 for each class. Thirty-three subjects, three repetitions, and four arms produced 396 fold rows.

The primary candidate was normalized class-Mondrian calibration. It had to achieve mean and per-class coverage of at least 0.88, a class gap no larger than 0.05, no material worst-subject deterioration, at least a 0.05 full-set reduction versus raw marginal calibration, nonnegative coverage change in both protocol versions and at least 60% of subjects, and no more than 1% empty sets. Every condition was required.

The primary decision was CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED. Class conditioning exposed a real partial mechanism: the normalized class-coverage gap fell from 0.0972 under marginal calibration to 0.0114. Non-stress coverage increased by 0.0631, but stress coverage fell by 0.0455. Overall normalized coverage rose only from 0.8681 to 0.8769, still below 0.88, and stress coverage remained only 0.8712. Worst-subject coverage fell from 0.7083 to 0.6875. The paired-subject coverage change was positive for 75.76% of subjects, but its bootstrap 95% interval ranged from -0.0038 to 0.0215 and included zero. Full-set frequency increased by 0.0240 versus normalized marginal calibration, although it remained 0.0669 below the raw marginal baseline.

The scientific interpretation is narrower than a repair claim. The pooled threshold contributed to class imbalance, but class pooling was not the entire safety failure. Class-Mondrian calibration mostly exchanged coverage between non-stress and stress and did not solve the weak-subject tail. The leading unresolved explanation is now subject-level reliability or distribution shift. The next falsification target should use only unlabeled onboarding diagnostics to predict whether raw or normalized representation is safer for a held-out subject, with the gate trained only on other subjects and evaluated without test-label access.

Experiment 14 passed independent exact replay. The validator regenerated all 396 rows, verified identical splits across all four arms, enforced subject and onboarding/test separation, recomputed marginal and class-specific score counts and ranks, confirmed unchanged classifier metrics across calibration modes, exactly matched both Experiment 13 marginal arms, recomputed every frozen decision rule, verified all 33 feature-checkpoint hashes, decoded all outputs as UTF-8, and passed the credential scan. No LLM, API key, or raw-data mutation was used.
