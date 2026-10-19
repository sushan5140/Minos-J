# Meno-J Experiment 2: Confounder Enrichment Ablation

## Version

`v3_enriched`

## Research question

Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 7
- SALVAGEABLE: 0
- REJECT: 3
- Pass survival rate: 70.0%
- Salvageable rate: 0.0%

## Top failed checklist fields

- `mechanism_is_non_generic`: 3

## Red flags

None.

## Confounder enrichment diagnostics

- Enriched hypotheses: 10
- Average confounders per hypothesis: 6.60
- Average control variables per hypothesis: 5.00
- Average rival explanations per hypothesis: 4.00
- Hypotheses with effect-size expectation: 10

## PASS hypotheses

### H1: Inter-subject variability in cardiovascular dynamics violates the exchangeability assumption required for conformal prediction coverage guarantees.

- Mechanism: Individual differences in autonomic regulation, vascular compliance, and baroreflex sensitivity cause the conditional distribution of prediction errors to shift systematically across subjects, making calibration on one subject invalid for another.
- Audit reason: All critical checks pass. The mechanism specifies domain-specific cardiovascular traits (baroreflex gain, arterial stiffness) that cause systematic shifts in error distributions across subjects, with measurable variables, valid causal chain, identified confounders, clear data requirements, and a testable prediction.

### H3: Circadian modulation of autonomic tone creates periodic non-stationarity in heart rate variability that conformal prediction fails to capture with static calibration sets.

- Mechanism: Sympathetic-parasympathetic balance oscillates with a ~24-hour period, altering the conditional variance of RR intervals and causing prediction error distributions to widen during sympathetic dominance (day) and narrow during parasympathetic dominance (night).
- Audit reason: All critical checks pass. The mechanism is domain-specific to circadian modulation of autonomic tone and HRV, with a clear causal path from circadian phase to error distribution shifts, measurable variables, identified confounders, clear data requirements, and a testable prediction.

### H4: Progressive pathophysiological remodeling in chronic disease alters the signal-generating process faster than the conformal calibration window can track.

- Mechanism: In conditions like heart failure, ventricular remodeling and neurohormonal activation change the morphology and variability of ECG and PPG signals on timescales of weeks, causing the conformal predictor's error distribution to shift beyond the adaptation capacity of sliding-window calibration.
- Audit reason: All critical checks pass. The mechanism is specific to heart failure pathophysiology (ventricular remodeling, neurohormonal activation) and its effect on ECG/PPG morphology, with measurable variables, valid causal chain, identified confounders, clear data requirements, and a testable prediction.

### H6: Unobserved subpopulations defined by medication response or genetic polymorphisms create hidden stratification that breaks marginal coverage guarantees.

- Mechanism: Beta-blocker responders vs. non-responders exhibit fundamentally different heart rate dynamics; if the calibration set mixes these groups but test segments come predominantly from one, the conformal predictor's marginal coverage fails for the underrepresented group.
- Audit reason: All critical checks pass. The mechanism is domain-specific to pharmacogenomics of beta-blocker response (ADRB1 polymorphism) and heart rate dynamics. Effect size plausibility is unknown (non-critical), but the mechanism names a specific genetic variant and physiological outcome.
- Failed checks: effect_size_plausible

### H7: Long-range temporal dependence in physiological signals violates the exchangeability assumption even after conditioning on recent history.

- Mechanism: Fractal-like correlations in heart rate variability (e.g., 1/f scaling) mean that prediction errors remain dependent across arbitrarily long lags, so finite-history conditioning does not achieve approximate exchangeability required for conformal coverage.
- Audit reason: All critical checks pass. The mechanism is specific to fractal-like long-range correlations in HRV (1/f scaling) and their impact on effective sample size for conformal quantile estimation. Effect size plausibility is unknown (non-critical) but the causal chain is well-defined.
- Failed checks: effect_size_plausible

### H8: Segment-dependent motion artifact prevalence creates heteroscedastic noise that conformal prediction cannot calibrate for without artifact labels.

- Mechanism: Physical activity levels vary across recording segments (sleep vs. exercise), causing non-Gaussian, signal-dependent noise in wearable PPG/accelerometer data that widens prediction intervals unpredictably when artifact contamination is high.
- Audit reason: All critical checks pass. The mechanism is domain-specific to wearable PPG motion artifacts (rotational motion, sensor shear, signal-dependent noise) with measurable variables, valid causal chain, identified confounders, clear data requirements, and a testable prediction.

### H9: Sleep-stage-dependent cardiorespiratory coupling alters the predictability of cardiovascular signals in ways not captured by standard conformal conditioning.

- Mechanism: During REM sleep, autonomic instability and irregular breathing increase heart rate variability unpredictability, while deep NREM sleep shows high predictability; if calibration data underrepresents REM, coverage fails specifically in REM segments.
- Audit reason: All critical checks pass. The mechanism is specific to sleep-stage-dependent cardiorespiratory coupling and its effect on HRV predictability, with measurable variables, valid causal chain, identified confounders, clear data requirements, and a testable prediction.

## SALVAGEABLE hypotheses

None.

## REJECT hypotheses

### H2: Gradual sensor calibration drift across recording sessions introduces non-stationary measurement bias that conformal prediction cannot adapt to without recalibration.

- Mechanism: Temperature-dependent sensor gain changes and electrode polarization cause the mapping from true physiological state to observed signal to shift slowly over time, altering the error distribution in a way that violates the i.i.d. assumption.
- Audit reason: The mechanism describes generic sensor drift (temperature-dependent gain, electrode polarization, gel drying) that applies broadly to many sensing domains, not a domain-specific causal path unique to physiological signals. Therefore it fails the non-generic mechanism criterion.
- Failed checks: mechanism_is_non_generic

### H5: Inconsistent expert annotation of physiological events across segments introduces label noise that violates the conformal prediction assumption of reliable ground truth.

- Mechanism: Inter-rater variability in identifying arrhythmia onset, sleep stage transitions, or artifact epochs creates segment-dependent label error rates, causing the conformal predictor to calibrate against a moving target of imperfect labels.
- Audit reason: The mechanism describes generic label noise from expert annotation variability, which is a common issue in many supervised learning domains and does not specify a domain-specific causal path unique to physiological signals.
- Failed checks: mechanism_is_non_generic

### H10: Time-varying electrode-skin impedance modulates signal-to-noise ratio in ECG/PPG, causing segment-dependent calibration failure.

- Mechanism: Sweat accumulation, skin desquamation, and electrode gel drying change contact impedance over hours, attenuating signal amplitude and increasing baseline wander in a segment-specific manner that shifts the prediction error distribution.
- Audit reason: The mechanism describes generic electrode-skin impedance drift due to sweat and desquamation, which is a common issue in biopotential recordings (ECG, EEG, EMG) and does not specify a domain-specific causal path unique to the physiological signal of interest.
- Failed checks: mechanism_is_non_generic

## Short interpretation

The auditor filtered the candidate set while retaining a smaller group for rival-prediction and falsification analysis. The red flags above indicate whether that selectivity appears meaningfully discriminating.
