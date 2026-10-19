# Meno-J Experiment 1: Auditor Calibration Test

## Research question

Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 0
- SALVAGEABLE: 10
- REJECT: 0
- Pass survival rate: 0.0%
- Salvageable rate: 100.0%

## Top failed checklist fields

- `confounders_identified`: 10
- `mechanism_is_non_generic`: 9

## Red flags

None.

## PASS hypotheses

None.

## SALVAGEABLE hypotheses

### H1: Inter-subject physiological heterogeneity violates the exchangeability assumption required for conformal prediction coverage guarantees.

- Mechanism: Individual differences in autonomic regulation, anatomy, and baseline physiology cause the conditional distribution of prediction errors to vary systematically across subjects, making calibration scores from one subject non-representative for another.
- Audit reason: Two critical checks fail: confounders are not identified and the mechanism (inter-subject heterogeneity violating exchangeability) is generic across many domains. However, the idea is concretely repairable by specifying physiological confounders and a more detailed causal path linking autonomic regulation to prediction error variance.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Add confounders such as age, sex, comorbidities, and medication. Specify how autonomic regulation (e.g., HRV metrics) modulates prediction error variance for the specific predictor used, making the mechanism specific to physiological signal conformal prediction.

### H2: Sensor-specific noise characteristics and placement variability induce heteroscedastic prediction errors that break conformal prediction's assumption of homogeneous noise structure.

- Mechanism: Different sensor modalities (e.g., ECG vs. PPG), electrode placements, and contact impedances produce segment-specific noise distributions with varying variance and bias, causing calibration quantiles to misestimate true coverage.
- Audit reason: Two critical checks fail: no confounders identified and the mechanism (sensor heterogeneity causing heteroscedastic errors) is generic to any multi-sensor domain. Repairable by identifying sensor-specific confounders and modeling noise characteristics unique to physiological sensors.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders like motion artifacts, skin impedance, and electrode type. Develop sensor-specific noise models (e.g., PPG motion artifact vs. ECG baseline wander) that link placement variability to prediction error distribution shifts in a physiologically grounded way.

### H3: Abrupt physiological state transitions (e.g., sleep-stage changes, stress responses) create within-segment distribution shifts that invalidate calibration performed on preceding stable states.

- Mechanism: Rapid autonomic shifts alter signal morphology and noise characteristics faster than the calibration window can adapt, causing prediction error distributions to diverge from those used to compute conformal quantiles.
- Audit reason: Two critical checks fail: confounders not identified and the mechanism (abrupt state transitions causing distribution shift) is generic to non-stationary time series. Repairable by specifying physiological confounders and detailing how autonomic shifts alter specific signal features used by the predictor.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Add confounders such as circadian phase, medication, and sleep disorders. Specify how autonomic shifts (e.g., changes in HRV spectral power) affect the predictor's input features and error distribution, making the mechanism specific to physiological state transitions.

### H4: Long-range temporal autocorrelation in physiological signals violates the i.i.d. assumption underlying standard conformal prediction, causing coverage to degrade with prediction horizon.

- Mechanism: Physiological signals exhibit fractal-like correlations (e.g., 1/f noise in heart rate variability) that create dependence between calibration and test errors, making the effective sample size smaller than assumed and quantiles anti-conservative.
- Audit reason: Two critical checks fail: no confounders identified and the mechanism (long-range autocorrelation reducing effective sample size) is a generic statistical issue. Repairable by identifying physiological confounders and quantifying the relationship between long-memory parameters and conformal quantile inflation.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders like non-stationary trends and external interventions. Derive or simulate the relationship between Hurst exponent (or 1/f noise parameters) and the effective sample size for conformal prediction intervals, linking it to physiological signal properties.

### H5: Inter-rater variability in ground-truth labeling differs systematically across physiological signal segments, causing the calibration labels themselves to be noisy in a segment-dependent way.

- Mechanism: Expert annotation agreement for events like arrhythmias or apneas varies with signal quality, event morphology, and physiological context, making the 'true' coverage target a moving target across segments.
- Audit reason: Two critical checks fail: confounders not identified and the mechanism (inter-rater label noise varying by segment) is generic to any domain with noisy labels. Repairable by specifying physiological factors that modulate annotation agreement and their impact on coverage targets.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders such as annotator experience, signal quality indices, and event morphology complexity. Model how physiological context (e.g., low-amplitude ECG, overlapping artifacts) specifically reduces inter-rater agreement for certain event types, making the label noise mechanism domain-specific.

### H6: Systematic exclusion of low-signal-quality segments from calibration sets creates a selection bias where conformal prediction intervals are only valid for high-quality segments.

- Mechanism: Quality-based filtering during dataset construction removes segments with motion artifacts, electrode pops, or saturation from calibration, but these segments appear at test time, causing coverage to collapse precisely when signals are most degraded.
- Audit reason: Two critical checks fail: no confounders identified and the mechanism (quality-based selection bias) is a generic data curation issue. Repairable by identifying confounders that affect both quality filtering and error distribution, and quantifying the coverage gap as a function of signal quality.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders like artifact type, patient population, and recording environment. Quantify the relationship between signal quality indices (e.g., SQI) and prediction error distribution shifts, and test coverage conditional on quality strata.

### H7: Circadian rhythms induce time-of-day-dependent shifts in physiological signal distributions that are not captured by calibration sets collected at limited times.

- Mechanism: Core body temperature, hormone levels, and autonomic tone follow circadian patterns that alter baseline signal characteristics and variability, causing prediction error distributions to shift predictably but unaccounted for across the 24-hour cycle.
- Audit reason: Two critical checks fail: confounders not identified and the mechanism (circadian rhythms causing diurnal distribution shifts) is generic within physiological monitoring. Repairable by specifying confounders and linking specific circadian mediators to signal features that affect prediction errors.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Add confounders such as sleep-wake cycle, shift work, and lighting conditions. Specify how cortisol, melatonin, and autonomic tone modulate specific signal features (e.g., QT interval, HRV) that the predictor relies on, creating a domain-specific causal chain.

### H8: Gradual sensor drift and calibration decay create covariate shift that conformal prediction cannot adapt to without explicit recalibration triggers.

- Mechanism: Electrode gel drying, sensor oxidation, and mechanical displacement cause slow, monotonic changes in signal amplitude and noise floor, shifting the error distribution away from the calibration quantiles over hours to days.
- Audit reason: Two critical checks fail: no confounders identified and the mechanism (sensor drift causing covariate shift) is generic to any long-term sensor deployment. Repairable by identifying environmental and usage confounders and modeling the time-course of sensor degradation on signal amplitude and error variance.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders like temperature, humidity, sensor age, and patient activity. Model the kinetics of electrode gel drying and impedance change, linking them to signal amplitude attenuation and prediction error variance increase over hours to days.

### H9: Pharmacokinetic and pharmacodynamic effects of medications create time-varying physiological signal distributions that violate conformal prediction's stationarity assumptions.

- Mechanism: Drug absorption, distribution, metabolism, and excretion cycles (e.g., beta-blockers, vasopressors) induce structured, non-stationary changes in heart rate variability, blood pressure waveforms, and ECG morphology that alter prediction error distributions in a dose- and time-dependent manner.
- Audit reason: One critical check fails: confounders not identified. The mechanism (pharmacokinetic/pharmacodynamic effects) is non-generic, naming specific drug classes and physiological pathways. Repairable by adding confounders that affect drug response and linking PK/PD models to prediction error distributions.
- Failed checks: confounders_identified
- Salvage note: Identify confounders such as disease severity, drug interactions, renal/hepatic function, and genetic polymorphisms. Incorporate PK/PD models that link drug concentration time-courses to changes in HRV, blood pressure waveforms, and ECG morphology, and test coverage across dosing intervals.

### H10: Rare but clinically critical physiological patterns (e.g., pre-ictal states, pre-arrest rhythms) are underrepresented in calibration sets, causing conformal prediction to produce overconfident intervals for these high-stakes segments.

- Mechanism: Calibration sets typically reflect common physiological states; the prediction model's error distribution on rare pathological precursors differs systematically (often larger errors), but conformal quantiles computed from common states fail to capture this tail behavior.
- Audit reason: Two critical checks fail: no confounders identified and the mechanism (rare-event underrepresentation causing tail coverage failure) is generic to any imbalanced classification problem. Repairable by specifying pathophysiological mechanisms that make rare events have distinct error distributions and identifying confounders affecting event rarity.
- Failed checks: confounders_identified, mechanism_is_non_generic
- Salvage note: Identify confounders like comorbidities, medication, and demographic factors. Specify how pathophysiological mechanisms (e.g., pre-ictal synchronization, pre-arrest electrical instability) alter signal complexity and prediction error distributions, making the tail behavior specific to physiological rare events.

## REJECT hypotheses

None.

## Short interpretation

The auditor filtered every speculative hypothesis. The failure patterns should be reviewed to distinguish appropriate strictness from over-rejection.
