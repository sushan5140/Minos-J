# Meno-J Experiment 2: Confounder Enrichment Ablation

## Version

`v3_enriched`

## Research question

What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?

## Model used

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Counts and rates

- Generated: 10
- PASS: 9
- SALVAGEABLE: 1
- REJECT: 0
- Pass survival rate: 90.0%
- Salvageable rate: 10.0%

## Top failed checklist fields

- `mechanism_is_non_generic`: 1

## Red flags

None.

## Confounder enrichment diagnostics

- Enriched hypotheses: 10
- Average confounders per hypothesis: 5.80
- Average control variables per hypothesis: 5.50
- Average rival explanations per hypothesis: 3.00
- Hypotheses with effect-size expectation: 10

## PASS hypotheses

### H1: Subject-specific autonomic baseline variability leads to different signal-to-noise ratios in wearable stress signals.

- Mechanism: Individual differences in resting heart rate variability and skin conductance level alter the dynamic range of stress-induced changes, making the same absolute change represent different signal-to-noise ratios across subjects.
- Audit reason: All critical checks pass. The mechanism specifies a non-generic causal path (baseline autonomic tone modulates dynamic range of stress-induced changes), variables are measurable, confounders identified, data requirements clear, and predictions testable.

### H2: Variability in sensor placement tightness and skin contact introduces subject-specific motion artifact profiles.

- Mechanism: Looser wristbands allow greater relative motion between sensor and skin, amplifying motion artifacts that mimic or mask stress-related physiological changes.
- Audit reason: All critical checks pass. The mechanism names a specific physical process (strap tightness modulates skin-sensor coupling and transfer function from acceleration to artifact), variables are measurable, confounders identified, data requirements clear, and predictions testable.

### H3: Individual differences in sweat gland density and distribution affect skin conductance signal quality and stress detectability.

- Mechanism: Higher eccrine gland density yields larger, faster conductance responses to sympathetic activation, improving classifier confidence; lower density yields noisier, attenuated signals.
- Audit reason: All critical checks pass. The mechanism identifies a domain-specific causal path (eccrine gland density determines transduction gain from sympathetic activity to skin conductance), variables are measurable via proxies, confounders identified, data requirements clear, and predictions testable.

### H4: Circadian phase shifts cause time-of-day dependent model performance that differs across subjects.

- Mechanism: Autonomic regulation follows circadian rhythms; subjects with shifted chronotypes experience stress at different circadian phases, altering baseline physiology and classifier calibration.
- Audit reason: All critical checks pass. The mechanism specifies a non-generic causal path (circadian phase modulates autonomic tone and stress reactivity, and mismatch with training distribution degrades performance), variables are measurable, confounders identified, data requirements clear, and predictions testable.

### H5: Self-reported stress labels contain subject-specific recall bias, creating heterogeneous label noise.

- Mechanism: Individuals differ in meta-cognitive awareness and reporting style; some under-report, others over-report stress, leading to systematic label errors that degrade model certainty differently per subject.
- Audit reason: All critical checks pass. The mechanism names specific traits (alexithymia, neuroticism) and their directional effects on reporting bias, variables are measurable, confounders identified, data requirements clear, and predictions testable via measurement error models.

### H6: Unobserved subpopulations (e.g., anxiety disorders, medication use) create heterogeneous stress response patterns.

- Mechanism: Clinical conditions or pharmacologic agents alter autonomic reactivity, producing distinct physiological signatures that the generic model cannot capture, inflating uncertainty for affected subjects.
- Audit reason: All critical checks pass. The mechanism identifies specific clinical subpopulations (anxiety disorders, beta-blocker users) and their distinct autonomic signatures, variables are measurable via screening, confounders identified, data requirements clear, and predictions testable via hierarchical modeling.

### H8: Sensor firmware version differences introduce systematic bias across devices used by different subjects.

- Mechanism: Firmware updates change filtering, sampling rate, or calibration constants; subjects receiving devices with different firmware experience shifted feature distributions, degrading model performance for those cohorts.
- Audit reason: All critical checks pass. The mechanism specifies a domain-specific causal path (firmware updates alter digital filtering, sampling rate, or calibration coefficients, causing feature distribution shifts), variables are measurable, confounders identified, data requirements clear, and predictions testable via domain adaptation.

### H9: Physical activity intensity interacts with stress detection, and habitual activity patterns differ per subject.

- Mechanism: High-intensity movement generates artifacts that overlap with stress signatures; subjects with more vigorous daily routines produce noisier stress windows, increasing uncertainty.
- Audit reason: All critical checks pass. The mechanism names a specific interaction (physical activity generates motion artifacts and physiological changes overlapping with stress signatures, dependent on intensity, type, and fitness), variables are measurable, confounders identified, data requirements clear, and predictions testable via activity-specific modeling.

### H10: Data missingness not at random (e.g., device removal during high stress) varies by subject, biasing uncertainty estimates.

- Mechanism: Subjects who find the device uncomfortable during stressful episodes remove it, causing systematic loss of high-stress windows; the model then sees a truncated stress distribution, inflating uncertainty for those subjects.
- Audit reason: All critical checks pass. The mechanism specifies a domain-specific MNAR missingness process (device removal during high stress due to comfort tolerance truncates stress distribution), variables are measurable, confounders identified, data requirements clear, and predictions testable via selection models.

## SALVAGEABLE hypotheses

### H7: Statistical model misspecification: assuming homoscedastic errors when residual variance is subject-dependent.

- Mechanism: A single global variance parameter underestimates uncertainty for high-variance subjects and overestimates for low-variance subjects, leading to miscalibrated prediction intervals.
- Audit reason: The mechanism_is_non_generic check fails because the mechanism describes a generic statistical issue (heteroscedasticity due to unmodeled factors) that applies broadly across domains without a domain-specific causal path. Other checks pass. The idea is salvageable by tying subject-specific variance to specific physiological or behavioral traits.
- Failed checks: mechanism_is_non_generic
- Salvage note: Make the mechanism non-generic by specifying domain-specific sources of heteroscedasticity, e.g., individual differences in autonomic reactivity, motion artifact susceptibility, or stressor-type-specific variance, rather than generic unmodeled factors.

## REJECT hypotheses

None.

## Short interpretation

The auditor filtered the candidate set while retaining a smaller group for rival-prediction and falsification analysis. The red flags above indicate whether that selectivity appears meaningfully discriminating.
