# Meno-J Experiment 2: Confounder Enrichment Ablation

## Version

`v3_enriched`

## Research question

Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 9
- SALVAGEABLE: 0
- REJECT: 1
- Pass survival rate: 90.0%
- Salvageable rate: 0.0%

## Top failed checklist fields

- `mechanism_is_non_generic`: 1

## Red flags

None.

## Confounder enrichment diagnostics

- Enriched hypotheses: 10
- Average confounders per hypothesis: 3.00
- Average control variables per hypothesis: 3.00
- Average rival explanations per hypothesis: 2.00
- Hypotheses with effect-size expectation: 10

## PASS hypotheses

### H1: Inter‑subject variability in autonomic reactivity causes the nonconformity scores to be systematically miscalibrated for high‑reactivity individuals.

- Mechanism: Subjects with exaggerated sympathetic responses produce extreme physiological feature values that lie outside the training distribution, inflating the nonconformity measure and shrinking prediction sets.
- Audit reason: All critical checks pass: variables measurable (HRV, EDA, reactivity), causal chain valid (sympathetic reactivity -> extreme features -> nonconformity inflation), confounders identified (fitness, medication, circadian), data requirements clear (baseline measures, stratified scores, subject-independent splits), mechanism is non-generic (specific to autonomic reactivity and Mondrian nonconformity), prediction testable (coverage vs reactivity quantiles). Base rate and effect size plausible.

### H2: Sensor‑specific drift in the wrist‑worn EDA channel during prolonged recordings leads to biased nonconformity estimates for later trials.

- Mechanism: Gradual electrode impedance increase reduces EDA amplitude, shifting the feature distribution relative to the calibration set and causing undercoverage for sessions recorded late in the protocol.
- Audit reason: All critical checks pass: variables measurable (electrode impedance proxy, SNR, environmental logs), causal chain valid (impedance increase -> reduced EDA amplitude -> distribution shift -> undercoverage), confounders identified (temperature, hydration, movement), data requirements clear (time-resolved quality metrics, trial-order nonconformity, environmental logs), mechanism is non-generic (specific to wrist-worn EDA electrode impedance), prediction testable (coverage vs trial order). Base rate and effect size plausible.

### H3: Non‑stationary heart‑rate variability (HRV) dynamics across the stress‑recovery cycle violate the exchangeability assumption within Mondrian strata.

- Mechanism: Rapid autonomic transitions create temporal dependence in residuals; the conformal algorithm treats each window as independent, underestimating prediction interval width for transitional periods.
- Audit reason: All critical checks pass: variables measurable (window-level HRV, autocorrelation, stratum counts), causal chain valid (rapid autonomic transitions -> temporal dependence -> exchangeability violation -> undercoverage), confounders identified (breathing, posture, substance use), data requirements clear (temporal HRV features, residual autocorrelation, stratum sizes), mechanism is non-generic (specific to HRV dynamics in stress-recovery cycle), prediction testable (coverage in transitional periods). Base rate and effect size plausible.

### H4: Mislabeling of self‑reported stress levels for a subset of participants introduces systematic label noise into the Mondrian categories.

- Mechanism: Subjects who under‑report stress are placed in a low‑stress stratum while their physiological signals resemble high stress, causing the nonconformity distribution to be too narrow for that stratum.
- Audit reason: All critical checks pass: variables measurable (personality scores, self-report consistency, cortisol), causal chain valid (under-reporting -> stratum mismatch -> narrow nonconformity distribution), confounders identified (social desirability, scale interpretation, fatigue), data requirements clear (reliability metrics, consistency-split nonconformity, external labels), mechanism is non-generic (specific to Mondrian strata and self-report bias), prediction testable (coverage by report consistency). Base rate and effect size plausible.

### H5: Insufficient representation of certain demographic sub‑groups (e.g., age > 50) in the calibration set leads to stratum‑specific undercoverage.

- Mechanism: Mondrian taxonomy does not include age as a stratification variable; older subjects exhibit different baseline HRV and EDA ranges, making the shared nonconformity quantile too optimistic for them.
- Audit reason: All critical checks pass: variables measurable (age, comorbidities, medication, baseline HRV/EDA), causal chain valid (taxonomy lacks age -> shared quantile too optimistic for older subjects), confounders identified (comorbidities, polypharmacy, fitness), data requirements clear (demographic metadata, coverage by age deciles, calibration sizes), mechanism is non-generic (specific to Mondrian taxonomy and physiological baselines), prediction testable (coverage vs age). Base rate and effect size plausible.

### H6: The choice of nonconformity score (e.g., softmax margin) is poorly aligned with the multimodal feature geometry for stress classification.

- Mechanism: Margin‑based scores ignore correlation structure between ECG, EDA, and respiration features, producing overly confident scores for out‑of‑distribution multimodal patterns.
- Audit reason: All critical checks pass: variables measurable (standardized features, modality presence, alternative scores), causal chain valid (margin scores ignore cross-modality correlation -> overconfident for OOD patterns), confounders identified (scaling, missing modalities, classifier bias), data requirements clear (multiple nonconformity functions, coverage per stratum, correlation matrices), mechanism is non-generic (specific to multimodal stress feature geometry), prediction testable (coverage comparison across scores). Base rate and effect size plausible.

### H7: Batch effects from different recording days cause distribution shift that is not captured by the Mondrian condition labels.

- Mechanism: Day‑specific ambient temperature and humidity alter skin conductance baseline, shifting the EDA feature distribution; the conformal predictor treats all days as exchangeable within a condition.
- Audit reason: All critical checks pass: variables measurable (day ID, ambient logs, experimenter ID, sleep diary), causal chain valid (day-specific temperature/humidity -> skin conductance shift -> distribution shift), confounders identified (experimenter variability, equipment changes, sleep), data requirements clear (day-level metadata, nonconformity by day, day-respecting splits), mechanism is non-generic (specific to EDA skin conductance and Mondrian condition labels), prediction testable (coverage by day). Base rate and effect size plausible.

### H9: Physiological habituation across repeated stress trials reduces signal discriminability, but the Mondrian taxonomy treats each trial as identically distributed.

- Mechanism: Repeated exposure attenuates EDA peaks and HRV reactivity, moving later‑trial feature vectors toward the non‑stress distribution while the nonconformity calibration remains based on early‑trial statistics.
- Audit reason: All critical checks pass: variables measurable (trial index, inter-trial interval, fatigue ratings, time-of-day), causal chain valid (repeated exposure attenuates EDA/HRV -> feature shift -> nonconformity based on early trials), confounders identified (fatigue, anticipation, time-of-day), data requirements clear (trial-wise trajectories, nonconformity per trial, habituation curves), mechanism is non-generic (specific to physiological habituation in stress trials), prediction testable (coverage vs trial order). Base rate and effect size plausible.

### H10: Correlated missingness in the respiration belt (e.g., motion artifacts) creates informative missingness that the conformal predictor ignores.

- Mechanism: When respiration data are missing during high‑movement stress periods, the imputed or omitted features shift the joint distribution; the nonconformity score computed on available modalities underestimates uncertainty.
- Audit reason: All critical checks pass: variables measurable (accelerometer movement, missingness indicators, imputation method), causal chain valid (missing respiration during high-movement stress -> informative missingness -> underestimated uncertainty), confounders identified (movement-stress correlation, imputation bias, multi-modality dropout), data requirements clear (missingness logs, movement intensity, coverage comparisons), mechanism is non-generic (specific to respiration belt missingness correlated with stress), prediction testable (coverage: complete-case vs imputed vs missingness-aware). Base rate and effect size plausible.

## SALVAGEABLE hypotheses

None.

## REJECT hypotheses

### H8: Finite‑sample estimation error of the conditional quantile in small strata leads to systematic undercoverage for rare stress levels.

- Mechanism: Mondrian splits the calibration data into many condition‑subject strata; strata with few samples yield noisy quantile estimates that are biased low.
- Audit reason: Mechanism is domain-generic: finite-sample quantile estimation bias is a general statistical issue not specific to WESAD or physiological stress. Thus mechanism_is_non_generic fails. Other checks pass. Therefore REJECT.
- Failed checks: mechanism_is_non_generic

## Short interpretation

The auditor filtered the candidate set while retaining a smaller group for rival-prediction and falsification analysis. The red flags above indicate whether that selectivity appears meaningfully discriminating.
