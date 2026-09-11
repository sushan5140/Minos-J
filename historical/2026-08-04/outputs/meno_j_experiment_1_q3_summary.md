# Meno-J Experiment 1: Auditor Calibration Test

## Research question

What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 0
- SALVAGEABLE: 7
- REJECT: 3
- Pass survival rate: 0.0%
- Salvageable rate: 70.0%

## Top failed checklist fields

- `confounders_identified`: 10
- `mechanism_is_non_generic`: 3
- `causal_chain_valid`: 1

## Red flags

None.

## PASS hypotheses

None.

## SALVAGEABLE hypotheses

### H2: Variability in sensor placement on the wrist introduces subject-specific measurement bias that propagates to uncertainty estimates.

- Mechanism: Differences in radial artery depth and subcutaneous tissue thickness alter photoplethysmography (PPG) amplitude, causing heterogeneous signal quality across users.
- Audit reason: One critical check failed (confounders not identified), but mechanism is specific and testable; salvageable by identifying confounders such as skin tone, motion, device fit.
- Failed checks: confounders_identified
- Salvage note: Add confounders: skin pigmentation, motion artifacts, device tightness, and ambient light; incorporate into model to isolate placement effect.

### H3: Physiological stress response heterogeneity (e.g., cortisol vs. sympathetic activation) leads to divergent wearable signal patterns across individuals.

- Mechanism: Some subjects mount a primarily hypothalamic-pituitary-adrenal (HPA) response with minimal cardiac changes, while others show strong sympathetic surges, producing mismatched feature distributions for a single stress model.
- Audit reason: Confounders not identified; otherwise mechanism is specific and testable.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: stressor type, context, baseline fitness, time of day, and incorporate phenotype classification.

### H5: Self-report labeling noise varies by subject due to differences in emotional awareness and reporting latency.

- Mechanism: Subjects with low interoceptive accuracy provide delayed or inaccurate stress timestamps, corrupting ground truth and inflating model uncertainty for those individuals.
- Audit reason: Confounders not identified; mechanism is specific to self-report labeling noise in stress detection.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: stressor intensity, context, recall bias, and mood; incorporate interoceptive accuracy as covariate.

### H6: Circadian phase at the time of measurement stratifies uncertainty because autonomic baseline shifts across the day.

- Mechanism: Morning cortisol peaks and evening parasympathetic dominance alter HRV baselines, causing the same stressor to produce different feature deviations depending on time-of-day.
- Audit reason: Confounders not identified; mechanism is specific to circadian modulation of stress detection.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: chronotype, sleep quality, shift work, and individual circadian phase markers.

### H8: Skin optical properties (melanin, thickness, hydration) modulate PPG signal quality, creating systematic per-subject uncertainty differences.

- Mechanism: Higher melanin concentration attenuates green-light PPG, reducing signal-to-noise ratio and increasing classifier variance for darker-skinned individuals.
- Audit reason: Confounders not identified; mechanism is specific to skin optical properties affecting PPG-based stress detection.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: sensor contact pressure, ambient light, motion, skin hydration, and incorporate dermatological metrics.

### H9: Concurrent physical activity confounds stress detection differently across subjects based on habitual activity patterns.

- Mechanism: Subjects who frequently engage in high-intensity exercise develop distinct motion artifact signatures that overlap with stress-induced autonomic changes, inflating uncertainty during active periods.
- Audit reason: Confounders not identified; mechanism is specific to activity-stress confounding in wearable stress detection.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: fitness level, exercise type, sensor location, and develop subject-specific activity models.

### H10: Genetic polymorphisms in autonomic regulation genes (e.g., ADRB1, COMT) cause inter-individual differences in wearable stress signal dynamics.

- Mechanism: Variants affecting beta-adrenergic receptor sensitivity or catecholamine metabolism alter heart-rate response magnitude to stressors, leading to heterogeneous feature distributions and variable model confidence.
- Audit reason: Confounders not identified; mechanism is specific to genetic polymorphisms affecting autonomic stress reactivity.
- Failed checks: confounders_identified
- Salvage note: Identify confounders: population stratification, age, sex, fitness, medication, and incorporate principal components of genetic ancestry.

## REJECT hypotheses

### H1: Individual differences in baseline autonomic tone cause systematic variation in wearable stress-detection uncertainty.

- Mechanism: Subjects with higher resting parasympathetic activity exhibit lower heart-rate variability (HRV) signal-to-noise ratios, leading to noisier stress classifiers.
- Audit reason: Causal chain is questionable (higher parasympathetic activity does not necessarily lower HRV SNR), confounders not identified, and mechanism is generic (baseline physiology affecting model uncertainty applies broadly).
- Failed checks: causal_chain_valid, confounders_identified, mechanism_is_non_generic

### H4: Temporal drift in sensor calibration (e.g., LED intensity decay) creates increasing uncertainty for long-term users.

- Mechanism: Gradual degradation of optical components reduces PPG signal fidelity, inflating model prediction variance over weeks to months.
- Audit reason: Mechanism is domain-generic (sensor drift affects all optical wearables similarly) and confounders not identified; not salvageable as a specific mechanism for stress detection uncertainty.
- Failed checks: confounders_identified, mechanism_is_non_generic

### H7: Statistical model misspecification due to non-stationary noise processes yields subject-dependent uncertainty inflation.

- Mechanism: Assuming i.i.d. Gaussian residuals ignores subject-specific autocorrelation in sensor noise (e.g., motion artifacts), leading to underestimation of predictive variance for high-mobility users.
- Audit reason: Mechanism is domain-generic (model misspecification due to non-stationary noise applies broadly) and confounders not identified.
- Failed checks: confounders_identified, mechanism_is_non_generic

## Short interpretation

The auditor filtered every speculative hypothesis. The failure patterns should be reviewed to distinguish appropriate strictness from over-rejection.
