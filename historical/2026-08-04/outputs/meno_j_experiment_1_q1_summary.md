# Meno-J Experiment 1: Auditor Calibration Test

## Research question

Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 0
- SALVAGEABLE: 2
- REJECT: 8
- Pass survival rate: 0.0%
- Salvageable rate: 20.0%

## Top failed checklist fields

- `confounders_identified`: 10
- `effect_size_plausible`: 10
- `data_requirements_clear`: 5
- `mechanism_is_non_generic`: 3
- `variables_measurable`: 3
- `base_rate_plausible`: 2
- `prediction_is_testable`: 2
- `causal_chain_valid`: 1

## Red flags

None.

## PASS hypotheses

None.

## SALVAGEABLE hypotheses

### H8: Circadian phase at time of data collection interacts with stress reactivity to produce residual distribution shifts unaccounted for by Mondrian's static taxonomy.

- Mechanism: Subjects tested at different circadian phases exhibit different baseline autonomic tone and stress reactivity; if calibration and test sets have different circadian distributions for a given bin, residual exchangeability fails.
- Audit reason: Circadian phase is measurable from timestamps and plausibly modulates autonomic tone; mechanism is domain-specific and testable. However, confounders (sleep, caffeine, light exposure) are not identified, and the effect size of circadian phase on residual shift is not quantified.
- Failed checks: confounders_identified, effect_size_plausible
- Salvage note: Identify and measure potential confounders (e.g., sleep duration, caffeine intake, light exposure) and quantify the effect size of circadian phase on residual distribution shift via simulation or empirical analysis.

### H9: Non-linear interactions between respiration rate and heart rate variability during stress create subject-specific residual patterns that linear Mondrian taxonomies cannot capture.

- Mechanism: Subjects with strong respiratory sinus arrhythmia modulation during stress produce residuals that depend on the interaction term (RSA × stress phase), but Mondrian bins only condition on marginal feature statistics.
- Audit reason: RSA-stress interaction is physiologically specific and measurable from WESAD's chest sensors; Mondrian's marginal binning is a concrete limitation. However, confounders (voluntary breathing patterns, motion artifacts on respiration) are not identified, and the interaction effect size on residuals is not quantified.
- Failed checks: confounders_identified, effect_size_plausible
- Salvage note: Identify confounders such as voluntary breathing patterns, motion artifacts affecting respiration signal, and quantify the interaction effect size on residuals using hierarchical modeling.

## REJECT hypotheses

### H1: Inter-subject variability in autonomic nervous system reactivity causes non-exchangeability of calibration and test residuals for high-reactivity individuals.

- Mechanism: Subjects with exaggerated sympathetic responses produce residual distributions with heavier tails than the calibration population, violating the exchangeability assumption of Mondrian's stratified conformal prediction.
- Audit reason: Mechanism lacks identification of confounders (e.g., motion artifacts, sensor noise), does not quantify effect size, and does not specify concrete data requirements for measuring autonomic reactivity and residual tail parameters.
- Failed checks: confounders_identified, effect_size_plausible, data_requirements_clear

### H2: Wrist-worn EDA sensor contact quality degrades systematically during high-arousal states due to vasoconstriction and motion artifacts, creating state-dependent measurement bias.

- Mechanism: Peripheral vasoconstriction during stress reduces skin conductance signal amplitude while increasing motion artifact susceptibility, causing the model to systematically underpredict stress probability for affected subjects.
- Audit reason: Key variable (sensor-skin interface impedance) is not measured in WESAD; confounders (skin properties, temperature, sensor placement) not identified; effect size not quantified; data requirements for contact quality metric undefined.
- Failed checks: variables_measurable, confounders_identified, effect_size_plausible, data_requirements_clear

### H3: The Mondrian taxonomy bins (based on coarse subject clusters) fail to capture continuous variation in baseline heart rate variability, causing miscalibration for subjects at cluster boundaries.

- Mechanism: Subjects with borderline HRV profiles get assigned to taxonomy bins whose calibration sets have systematically different residual quantiles, producing undercoverage when their true residual distribution falls between bin centroids.
- Audit reason: Discretization of continuous variables causing boundary miscalibration is a generic statistical issue, not specific to HRV or WESAD; confounders (other physiological features, sensor noise) not identified; effect size of bin granularity on coverage not quantified.
- Failed checks: confounders_identified, effect_size_plausible, mechanism_is_non_generic

### H4: Temporal non-stationarity within stress trials — specifically, habituation of physiological responses across repeated stressors — creates time-varying residual distributions that violate conformal prediction's i.i.d. assumption.

- Mechanism: Subjects showing strong habituation produce residuals that drift systematically across a session; calibration residuals (early trials) differ distributionally from test residuals (later trials), causing undercoverage for high-habituation subjects.
- Audit reason: WESAD does not contain repeated stress trials, so habituation cannot be measured; the causal chain assumes a data structure that does not exist; base rate of habituation unmeasurable; data requirements (repeated stressors) not met; prediction not testable on this dataset.
- Failed checks: variables_measurable, causal_chain_valid, base_rate_plausible, confounders_identified, effect_size_plausible, data_requirements_clear, prediction_is_testable

### H5: Self-report stress labels in WESAD contain systematic subject-specific biases (e.g., response styles, interoceptive awareness differences) that decouple labels from physiological ground truth for certain individuals.

- Mechanism: Subjects with low interoceptive awareness or extreme response styles produce labels that poorly reflect their actual physiological state, causing the model to learn a miscalibrated mapping for these subjects specifically.
- Audit reason: Interoceptive awareness, alexithymia, and response styles are not measured in WESAD; base rate of label bias unknown; confounders not identified; effect size not quantified; data requirements cannot be satisfied; prediction not testable without additional psychological measures.
- Failed checks: variables_measurable, base_rate_plausible, confounders_identified, effect_size_plausible, data_requirements_clear, prediction_is_testable

### H6: Chest-worn ECG and respiration sensors capture different physiological constructs than wrist-worn PPG/EDA during stress, and Mondrian's feature aggregation weights them suboptimally for subjects with divergent signal quality across modalities.

- Mechanism: For subjects with poor wrist-signal quality but good chest-signal quality (or vice versa), the fixed feature weighting causes the model to rely on noisier modalities, inflating residuals for that subgroup.
- Audit reason: Confounders (e.g., motion affecting both modalities differently) not identified; effect size of cross-modality quality divergence on residuals not quantified; data requirements for signal quality metrics per modality not specified.
- Failed checks: confounders_identified, effect_size_plausible, data_requirements_clear

### H7: The conformal prediction calibration set size per Mondrian bin is insufficient for subjects with rare physiological profiles, causing high variance in quantile estimates and sporadic undercoverage.

- Mechanism: Subjects in low-density regions of the physiological feature space (e.g., extreme HRV + high EDA reactivity) have few calibration neighbors, making their bin's empirical quantile estimates unstable and occasionally anti-conservative.
- Audit reason: Small calibration bin size causing quantile variance is a generic statistical problem, not specific to physiological feature spaces; confounders (model complexity, feature relevance) not identified; effect size of bin sparsity on coverage not quantified for WESAD.
- Failed checks: confounders_identified, effect_size_plausible, mechanism_is_non_generic

### H10: The split conformal prediction procedure uses a fixed calibration-test split that, by chance, assigns subjects with similar physiological profiles to different splits, breaking exchangeability for those profiles.

- Mechanism: Random splitting can place all instances of a rare physiological subtype into either calibration or test set; when they appear only in test, their residuals follow an unseen distribution causing undercoverage.
- Audit reason: Random split failing to represent rare subtypes is a generic issue in conformal prediction, not specific to WESAD or physiological subtypes; confounders (other sources of non-exchangeability) not identified; effect size of split randomness on coverage not quantified.
- Failed checks: confounders_identified, effect_size_plausible, mechanism_is_non_generic

## Short interpretation

The auditor filtered every speculative hypothesis. The failure patterns should be reviewed to distinguish appropriate strictness from over-rejection.
