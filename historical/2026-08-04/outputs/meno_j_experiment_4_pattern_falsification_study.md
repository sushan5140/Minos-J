# Meno-J Experiment 4: Pattern Falsification Study

## Working theory

Experiment 4 attempts to falsify the nine surviving hypotheses and five recurring patterns from Experiment 3. No new hypotheses were generated.

## P1: Inter-subject physiological heterogeneity violating exchangeability

**Working-theory claim:** Stable between-subject differences in autonomic or cardiovascular traits (reactivity, baroreflex gain, baseline HRV/SCL, clinical subpopulations) cause the conditional error distribution to shift systematically, breaking the exchangeability assumption required for marginal conformal coverage.

**Strongest competitor:** Systematic differences in wearable sensor data quality (signal-to-noise ratio, motion artifact burden, electrode-skin interface) across subjects create heteroscedastic noise that violates exchangeability; physiological traits merely proxy for these technical factors.

**Competitor mechanism:** Subject-specific factors such as skin tone, hair density, device fit, and habitual movement patterns cause variation in PPG/ECG signal quality. This leads to different error distributions for the stress classifier. Physiological traits (e.g., baseline HRV) correlate with these technical factors (e.g., higher HRV subjects may be more fit, move differently), creating a spurious association between physiology and coverage failure.

### Evidence and alternatives

**Plausible counterexamples**

- Two subjects with nearly identical baroreflex gain and baseline HRV but different skin tones (Fitzpatrick scale) show markedly different conformal coverage when using the same device.
- A single subject's coverage improves from 80% to 95% after repositioning the wearable to improve contact, without any change in physiological traits.

**Confounders and alternatives**

- Device firmware version differences across subjects alter signal processing pipelines and artifact rejection.
- Ambient light conditions during free-living wear introduce PPG baseline wander that correlates with subject lifestyle (indoor vs outdoor occupation).

**Evidence supporting the competitor**

- Published studies demonstrate PPG signal quality indices (SQI) vary significantly with skin tone and motion, and that SQI-stratified models restore calibration (e.g., Temko et al., 2019).
- Analyses of WESAD and similar datasets show that adding accelerometer-derived motion artifact indices as conditioning variables reduces coverage disparities across subjects without including physiological traits.

**Evidence refuting the competitor**

- Pharmacological intervention studies (beta-blocker administration) show coverage changes that track baroreflex gain modulation independent of signal quality metrics.
- Simulation studies where physiological heterogeneity is synthetically introduced into clean signals (no artifact variation) reproduce coverage drops matching empirical magnitudes.

### Distinguishing experiments

#### P1-F1: Physiological vs. Signal-Quality Conditioning in Multi-Subject Conformal Stress Detection

- Design: Recruit 60 subjects spanning diverse skin tones, fitness levels, and autonomic phenotypes. Collect synchronized PPG, ECG, accelerometer, and reference clinical measures (baroreflex gain via sequence method, PWV, resting HRV, SCL) during standardized stress tasks (TSST, cold pressor) and free-living periods. Train a stress classifier and construct three conditional conformal predictors: (A) conditioning on physiological traits (baroreflex gain, PWV, baseline HRV/SCL, reactivity quantiles), (B) conditioning on signal quality indices (PPG SQI, ECG SNR, motion artifact index from accelerometry), (C) conditioning on both. Evaluate per-subject coverage and prediction interval width on held-out data using subject-wise cross-validation.
- Working-theory prediction: Predictor (A) achieves nominal 95% coverage (±1%) across all subjects; adding signal quality indices (C) does not significantly improve coverage over (A). Predictor (B) fails to achieve nominal coverage for subjects with extreme physiological traits but good signal quality.
- Competitor prediction: Predictor (B) achieves nominal coverage across all subjects; adding physiological traits (C) does not significantly improve coverage over (B). Predictor (A) fails for subjects with poor signal quality regardless of physiological traits.
- Measurable outcomes: Per-subject coverage probability (target 95%); Mean prediction interval width; Coverage stratified by physiological trait quantiles and signal quality quantiles
- Expected effect: LARGE — Difference in coverage deviation from nominal (95%) between conditioning strategies; Physiological conditioning reduces coverage deviation by >10 percentage points compared to signal-quality conditioning if working theory holds; opposite if competitor holds.; target: ≥10% absolute difference in mean absolute coverage error between best and worst conditioning strategy
- Effect rationale: Prior work (H1, H6) shows large effect sizes for physiological heterogeneity; signal quality effects are typically medium in controlled lab settings but may be larger in free-living.
- Required data/metadata: Multi-subject wearable dataset with synchronized PPG, ECG, accelerometer; Clinical measures: baroreflex gain (sequence method), carotid-femoral PWV, resting HRV, SCL; Signal quality indices: PPG SQI, ECG SNR, motion artifact index; Subject metadata: age, sex, BMI, medication, skin tone (Fitzpatrick), fitness (VO2max proxy)
- Difficulty: HIGH — Requires invasive/specialized hemodynamic measurements (baroreflex gain, PWV) on 60 subjects, synchronized multi-modal wearable acquisition, and standardized stress protocols; resource-intensive and limits sample size.
- Working-theory failure condition: If predictor (B) achieves nominal coverage (±1%) in all subjects while predictor (A) does not, the working theory that physiological traits are the primary drivers of exchangeability violation is falsified.
- Literature: [L1](https://proceedings.mlr.press/v25/vovk12.html), [L3](https://arxiv.org/abs/1903.04684)

#### P1-F2: Counterfactual Simulation of Physiological vs. Technical Heterogeneity

- Design: Using a validated generative model of PPG/ECG signals (e.g., based on physiological simulators like PhysioNet's Cardiovascular Simulator), create synthetic datasets where (1) only physiological parameters vary across subjects (baroreflex gain, vascular compliance, autonomic reactivity) while signal quality is held constant, and (2) only signal quality parameters vary (SQI, motion artifact magnitude, electrode impedance) while physiology is held constant. Apply the same stress classifier and conformal prediction pipeline. Measure coverage degradation in each scenario. Additionally, create a mixed scenario where both vary with realistic correlations estimated from real data.
- Working-theory prediction: Scenario (1) reproduces the empirically observed coverage drops and their correlation with physiological traits; scenario (2) produces minimal coverage degradation unless artifact magnitude is extreme.
- Competitor prediction: Scenario (2) reproduces the coverage drops and their correlation with physiological traits (via induced correlations); scenario (1) produces minimal coverage degradation.
- Measurable outcomes: Coverage probability per simulated subject; Correlation between coverage error and simulated physiological traits vs. signal quality parameters; Calibration curves for marginal and conditional predictors
- Expected effect: LARGE — Coverage deviation from nominal attributable to each factor in isolation; Physiological heterogeneity alone causes >15% coverage drop in high-reactivity subjects; signal quality heterogeneity alone causes <5% drop unless artifacts are severe.; target: ≥15% absolute coverage difference between high and low physiological reactivity groups in scenario (1); ≤5% in scenario (2) for matched artifact levels.
- Effect rationale: H1 and H6 report large effect sizes for physiological heterogeneity; simulation isolates causality.
- Required data/metadata: Validated physiological signal simulator with adjustable autonomic and hemodynamic parameters; Artifact simulation module (motion, baseline wander, noise); Stress classifier trained on real data (fixed across simulations); Conformal prediction implementation (marginal, Mondrian, conditional)
- Difficulty: MEDIUM — Requires development/validation of a comprehensive physiological simulator with artifact models; computationally intensive but no human subjects.
- Working-theory failure condition: If scenario (2) produces coverage drops matching empirical magnitudes and patterns while scenario (1) does not, the working theory is falsified.
- Literature: [L2](https://arxiv.org/abs/1604.04173), [L7](https://arxiv.org/abs/2010.09107)

### Novelty

- Rating: HIGH
- Rationale: While conditional conformal prediction (L1) and covariate shift adaptation (L4) are established, the explicit adversarial comparison between physiological vs. technical drivers of exchangeability violation in wearable stress detection, with direct hemodynamic measurements and counterfactual simulation, is novel. Closest works (L1, L3) address conditional validity limits but not this specific physiological-technical confound.
- Novel contribution: First study to directly pit physiological heterogeneity against sensor data quality as the primary cause of conformal coverage failure in wearable stress detection, using both empirical multi-subject hemodynamic measurements and counterfactual simulation.
- Closest literature: [L1](https://proceedings.mlr.press/v25/vovk12.html), [L3](https://arxiv.org/abs/1903.04684)

## P2: Temporal non-stationarity and calibration window mismatch

**Working-theory claim:** Physiological signals exhibit non-stationarity at multiple timescales (rapid autonomic transitions, circadian rhythms, disease progression, activity-state changes) that violate the approximate stationarity assumption within the conformal calibration window, causing coverage to degrade when the calibration window does not track the current state.

**Strongest competitor:** Coverage degradation is primarily due to concept drift in the stress classifier itself (e.g., changing relationship between features and stress labels over time) rather than non-stationarity of the error distribution per se. The classifier's decision boundary shifts because the mapping from physiology to stress evolves (e.g., due to learning, sensitization, or contextual reinterpretation), and conformal prediction merely reflects this classifier drift.

**Competitor mechanism:** The stress classifier is trained on an initial distribution of physiological responses to stress. Over time, subjects' psychological appraisal of stressors changes (habituation, sensitization), altering the feature-label relationship. The conformal predictor's nonconformity scores (based on classifier outputs) then become miscalibrated because the classifier's softmax margins no longer reflect true uncertainty, not because the error distribution shifts independently. This is a form of label shift or concept drift that conformal prediction cannot correct without retraining.

### Evidence and alternatives

**Plausible counterexamples**

- In a longitudinal heart failure study, coverage drops coincide with documented changes in patients' self-reported stress appraisal (e.g., increased anxiety about symptoms) but not with echocardiographic remodeling markers.
- During a multi-day ambulatory study, coverage degrades on days when subjects report high cognitive load (e.g., work deadlines) but autonomic markers (HRV, EDA) remain stable.

**Confounders and alternatives**

- Gradual sensor degradation (e.g., LED aging, battery voltage drop) alters feature distributions over weeks.
- Seasonal changes in ambient temperature and daylight affect both physiology and behavior, creating spurious temporal trends.

**Evidence supporting the competitor**

- Machine learning literature shows concept drift in physiological classifiers over months (e.g., EEG-based emotion recognition).
- Psychological studies demonstrate that stress appraisal modifies physiological reactivity independently of autonomic state (e.g., challenge vs. threat appraisal).

**Evidence refuting the competitor**

- Experiments where the classifier is frozen but conformal calibration is updated with a sliding window show coverage recovery, indicating the error distribution shifts independently of classifier drift.
- Simulations where only the error distribution shifts (by adding noise to features) while the classifier remains optimal still cause coverage drops that conformal adaptation corrects.

### Distinguishing experiments

#### P2-F1: Disentangling Classifier Drift from Error Distribution Shift in Longitudinal Conformal Stress Detection

- Design: Recruit 30 heart failure patients for 6-month longitudinal monitoring with weekly wearable recordings (PPG, ECG, accelerometer), monthly echocardiography/NT-proBNP, and weekly ecological momentary assessment (EMA) of stress appraisal. Train a stress classifier at baseline and freeze its weights. Implement three conformal predictors: (A) static marginal conformal (calibration set = first week), (B) sliding-window conformal (window = 4 weeks, updated weekly), (C) sliding-window conformal with classifier retraining (same window). Track coverage over time. Additionally, compute classifier performance metrics (AUC, calibration error) on labeled stress events (from EMA) to quantify classifier drift.
- Working-theory prediction: Predictor (B) maintains nominal coverage (±1%) throughout despite ventricular remodeling; predictor (A) degrades. Classifier performance (AUC) remains stable, indicating error distribution shift is primary driver.
- Competitor prediction: Predictor (B) fails to maintain coverage because classifier drift corrupts nonconformity scores; predictor (C) (with retraining) restores coverage. Classifier AUC declines significantly over time, correlating with coverage loss.
- Measurable outcomes: Weekly coverage probability (target 95%) for each predictor; Classifier AUC and calibration error on weekly EMA-labeled stress events; Correlation between coverage deviation and clinical markers (LVEF, NT-proBNP) vs. EMA stress appraisal scores
- Expected effect: LARGE — Coverage deviation from nominal for static vs. sliding-window predictors; Static predictor coverage drops >15% by month 6; sliding-window without retraining maintains within ±1% if working theory holds. If competitor holds, sliding-window without retraining also drops >10%.; target: ≥10% absolute difference in coverage between static and sliding-window (no retrain) at 6 months; classifier AUC change <0.02 if working theory holds.
- Effect rationale: H4 and H9 report large effect sizes for non-stationarity; classifier drift in physiological signals is typically slower.
- Required data/metadata: Longitudinal wearable data (weekly) for 6 months; Serial clinical assessments: echocardiography, NT-proBNP; Weekly EMA stress appraisal labels; Medication and acute event logs
- Difficulty: HIGH — 6-month longitudinal study with weekly visits, clinical assessments, and EMA compliance is resource-intensive; heart failure patient recruitment and retention challenging.
- Working-theory failure condition: If sliding-window conformal without classifier retraining fails to maintain nominal coverage (deviation >2%) while the retraining version succeeds, and classifier AUC declines significantly, the working theory that error distribution shift alone drives coverage loss is falsified.
- Literature: [L6](https://arxiv.org/abs/2106.00170), [L8](https://arxiv.org/abs/2202.13415)

#### P2-F2: Controlled Laboratory Induction of Autonomic Transitions vs. Classifier Drift

- Design: In a within-subject crossover design (N=40), induce rapid autonomic transitions (cold pressor, mental arithmetic, recovery) across multiple sessions separated by weeks. In each session, collect high-resolution PPG, ECG, EDA, and respiration. Use a pre-trained stress classifier (frozen). Implement block-conformal predictors with blocks defined by transition phase (baseline, onset, peak, recovery) and compare to sliding-window and static predictors. Additionally, simulate classifier drift by gradually shifting the classifier's decision boundary (via temperature scaling) and measure coverage impact. Test whether block-conformal (which conditions on transition phase) restores coverage without classifier updating.
- Working-theory prediction: Block-conformal predictor achieves nominal coverage in each transition phase; sliding-window fails during transitions. Simulated classifier drift causes coverage drops that block-conformal cannot correct, requiring classifier retraining.
- Competitor prediction: Block-conformal fails because classifier drift occurs within phases; only retraining restores coverage. Simulated drift mimics real coverage patterns better than transition-phase conditioning.
- Measurable outcomes: Per-block coverage probability for block-conformal, sliding-window, static predictors; Coverage under simulated classifier drift (varying drift magnitude); Nonconformity score distributions per block and over sessions
- Expected effect: LARGE — Coverage deviation in transition blocks vs. stationary blocks; Transition blocks show >20% coverage drop for static predictor; block-conformal reduces to <2%. Classifier drift of 0.1 logit shift causes >10% coverage drop.; target: ≥15% absolute coverage improvement of block-conformal over static in transition blocks; classifier drift effect size ≥10% coverage drop per 0.1 logit shift.
- Effect rationale: H3 and H9 identify large effects for rapid transitions; classifier drift effects are estimated from ML literature.
- Required data/metadata: High-resolution multi-modal physiological data during standardized stress tasks; Pre-trained stress classifier (fixed); Block-conformal and sliding-window conformal implementations; Session metadata: time of day, session order, subject ID
- Difficulty: MEDIUM — Requires multiple lab sessions per subject with controlled stressors; feasible with standard psychophysiology lab equipment.
- Working-theory failure condition: If block-conformal fails to achieve nominal coverage in transition blocks while a predictor that updates the classifier (even with same block structure) succeeds, the working theory that non-stationarity is primarily in the error distribution (not classifier) is falsified.
- Literature: [L5](https://arxiv.org/abs/2006.02544), [L7](https://arxiv.org/abs/2010.09107)

### Novelty

- Rating: MEDIUM
- Rationale: Adaptive conformal inference under distribution shift (L6) and conformal prediction for time series (L7) are established. The novelty lies in the explicit adversarial comparison between error distribution shift and classifier concept drift in a longitudinal clinical wearable context, with simultaneous clinical and psychological monitoring. Closest works (L6, L8) address distribution drift but not the classifier drift confound.
- Novel contribution: First study to disentangle error distribution non-stationarity from classifier concept drift as causes of conformal coverage degradation in longitudinal wearable stress detection, using frozen vs. retrained classifiers and block-conformal conditioning on autonomic transition phases.
- Closest literature: [L6](https://arxiv.org/abs/2106.00170), [L8](https://arxiv.org/abs/2202.13415)

## P3: Sensor and measurement artifacts inducing distribution shift

**Working-theory claim:** Wearable sensor imperfections (electrode impedance drift, motion artifacts from rotational shear, strap tightness variation, firmware changes, informative missingness) create systematic, subject- or time-dependent shifts in the observed feature distribution that are not captured by the conformal predictor's conditioning variables, leading to miscalibration.

**Strongest competitor:** The observed coverage failures are not due to sensor artifacts per se, but to the conformal predictor's inability to handle the inherent heteroscedasticity of physiological signals even in artifact-free conditions. Physiological variability (e.g., beat-to-beat HRV, vasomotion) naturally produces non-Gaussian, signal-dependent noise that violates the homoscedasticity assumptions implicit in many nonconformity scores. Artifact correction merely reduces one source of heteroscedasticity but the fundamental issue remains.

**Competitor mechanism:** Physiological signals exhibit intrinsic heteroscedasticity: the variance of features like HRV, PTT, or EDA amplitude depends on the mean level (e.g., higher HR during stress increases absolute variability). Standard nonconformity scores (e.g., softmax margin, absolute residual) assume constant variance, leading to miscalibration when variance changes with physiological state. Sensor artifacts add another layer of heteroscedasticity, but even after perfect artifact removal, the residual physiological heteroscedasticity would still cause coverage failures if not modeled.

### Evidence and alternatives

**Plausible counterexamples**

- In a controlled lab setting with research-grade sensors (minimal artifacts), conformal coverage still drops during high-stress periods when physiological variability increases.
- Simulations using clean physiological signals (no artifacts) but with realistic state-dependent variance produce coverage drops matching empirical magnitudes.

**Confounders and alternatives**

- Changes in skin hydration and temperature across sessions alter electrode impedance and PPG baseline, mimicking artifact-induced shifts.
- Firmware updates that change filtering or sampling rates create step-changes in feature distributions unrelated to artifacts.

**Evidence supporting the competitor**

- Statistical literature on heteroscedasticity in physiological time series (e.g., HRV variance scales with mean HR).
- Conformal prediction studies showing that conformalized quantile regression (which models conditional variance) outperforms marginal conformal even on clean data.

**Evidence refuting the competitor**

- Experiments where motion artifact index (MAI) conditioning restores coverage during vigorous exercise to nominal levels, while physiological state conditioning alone does not.
- Studies showing that artifact-contaminated segments have coverage drops an order of magnitude larger than clean segments with matched physiological state.

### Distinguishing experiments

#### P3-F1: Artifact vs. Intrinsic Heteroscedasticity: Conditional Conformal Prediction with MAI and Physiological State

- Design: Collect synchronized PPG, 3D accelerometer, ECG, and reference BP (cuff) in 30 subjects across activities: sleep, rest, treadmill (graded), free-living. Compute motion artifact index (MAI) from accelerometer magnitude and orientation variability. Define physiological state bins (e.g., HR, HRV, SCL quantiles). Train a stress classifier and build conditional conformal predictors: (A) conditioning on MAI bins only, (B) conditioning on physiological state bins only, (C) conditioning on both, (D) conformalized quantile regression (CQR) with MAI and state as features. Evaluate coverage per activity bin and per MAI/state bin.
- Working-theory prediction: Predictor (A) achieves nominal coverage in all activity bins including vigorous exercise; (B) fails in high-MAI bins. CQR (D) performs similarly to (A).
- Competitor prediction: Predictor (B) achieves nominal coverage across physiological states; (A) fails in high-variance states even with low MAI. CQR (D) outperforms both by modeling conditional variance.
- Measurable outcomes: Coverage probability per MAI bin and per physiological state bin; Prediction interval width vs. MAI and state; CQR interval calibration (conditional coverage)
- Expected effect: LARGE — Coverage deviation from nominal in high-MAI vs. high-variance states; High-MAI bins show >20% coverage drop for (B); high-variance states show <5% drop for (A) if working theory holds. Opposite if competitor holds.; target: ≥15% absolute coverage difference between (A) and (B) in high-MAI bins; ≤5% difference in high-variance low-MAI bins.
- Effect rationale: H8 and H2 report large effects for motion artifacts; intrinsic heteroscedasticity effects are typically smaller in controlled settings.
- Required data/metadata: Multi-activity wearable dataset with synchronized PPG, ECG, accelerometer; Reference BP for validation; MAI computation pipeline; Physiological state binning definitions
- Difficulty: MEDIUM — Requires treadmill protocol and free-living collection with reference BP; feasible with standard lab equipment.
- Working-theory failure condition: If predictor (B) achieves nominal coverage in high-MAI bins while (A) does not, or if CQR significantly outperforms (A) in high-MAI bins, the working theory that artifacts are the primary driver is falsified.
- Literature: [L4](https://arxiv.org/abs/1904.06019), [L5](https://arxiv.org/abs/2006.02544)

#### P3-F2: Strap Tightness and Electrode Impedance as Artifact Proxies: A Controlled Perturbation Study

- Design: In a within-subject design (N=25), systematically vary strap tightness (loose, optimal, tight) and electrode gel condition (fresh, dried, none) during standardized stress tasks. Measure electrode impedance (via built-in impedance check) and PPG signal quality. Collect PPG, ECG, accelerometer. Apply the same stress classifier and conformal predictors: (A) marginal, (B) conditioning on impedance/SQI, (C) conditioning on strap tightness category, (D) conditioning on MAI. Test whether explicit artifact proxies restore coverage. Additionally, simulate firmware changes by applying different filter settings to the same raw data and assess coverage shift.
- Working-theory prediction: Predictors (B), (C), (D) achieve nominal coverage across all tightness/gel conditions; marginal (A) fails in loose/dry conditions. Firmware simulation shows coverage shifts that are corrected by conditioning on filter version.
- Competitor prediction: Conditioning on artifact proxies does not fully restore coverage because intrinsic heteroscedasticity remains; CQR with physiological state features outperforms artifact-conditioned predictors.
- Measurable outcomes: Coverage per tightness/gel condition for each predictor; Electrode impedance and SQI vs. coverage error; Coverage shift magnitude under simulated firmware changes
- Expected effect: LARGE — Coverage improvement from artifact conditioning vs. marginal; Artifact conditioning improves coverage by >15% in loose/dry conditions; firmware simulation causes >10% coverage shift corrected by version conditioning.; target: ≥15% absolute coverage improvement for (B)/(C)/(D) over (A) in worst artifact condition; ≤5% residual coverage error after artifact conditioning.
- Effect rationale: H2, H8, H10 identify large effects for impedance, strap tightness, firmware.
- Required data/metadata: Controlled perturbation dataset with varied strap tightness and electrode conditions; Electrode impedance measurements; Firmware/filter version metadata; Standardized stress task protocol
- Difficulty: LOW — Simple within-subject lab study with controlled perturbations; no specialized clinical measures needed.
- Working-theory failure condition: If artifact-conditioned predictors fail to achieve nominal coverage in high-artifact conditions while CQR with physiological state succeeds, the working theory is falsified.
- Literature: [L2](https://arxiv.org/abs/1604.04173), [L3](https://arxiv.org/abs/1903.04684)

### Novelty

- Rating: MEDIUM
- Rationale: Weighted conformal for covariate shift (L4) and adaptive prediction sets (L5) are relevant. The novelty is the explicit comparison of artifact proxies (MAI, impedance, strap tightness) vs. intrinsic physiological heteroscedasticity in a controlled perturbation design with firmware simulation. Closest works (L4, L5) address covariate shift and adaptive sets but not sensor-specific artifact conditioning.
- Novel contribution: First study to systematically perturb wearable sensor coupling (strap tightness, electrode condition) and firmware to quantify their causal impact on conformal coverage, and to compare artifact-conditioned conformal prediction against conformalized quantile regression for handling heteroscedasticity.
- Closest literature: [L4](https://arxiv.org/abs/1904.06019), [L5](https://arxiv.org/abs/2006.02544)

## P4: Methodological sensitivity to nonconformity score and conditioning strategy

**Working-theory claim:** The choice of nonconformity function (softmax margin vs. Mahalanobis distance vs. quantile regression) and the conditioning strategy (Mondrian taxonomy strata, block-conformal bins, MAI conditioning, mixture-model clusters) critically determine whether conformal prediction achieves valid coverage under distribution shift, non-stationarity, or heterogeneity.

**Strongest competitor:** The observed sensitivity is not due to fundamental mismatches between nonconformity scores and feature geometry, but to finite-sample effects and the curse of dimensionality in conditioning. When conditioning strata become too fine (e.g., many Mondrian taxa, high-dimensional MAI bins), the effective calibration sample size per stratum drops, causing high variance in quantile estimates and apparent coverage failures. The 'best' score/strategy simply balances bias-variance tradeoff for a given sample size, not a fundamental geometric alignment.

**Competitor mechanism:** Nonconformity scores like Mahalanobis distance require estimating a covariance matrix, which is unstable in high dimensions with limited data. Softmax margin is low-dimensional but ignores correlations. In small calibration sets, the variance of the Mahalanobis quantile estimate dominates, making margin scores appear better. As sample size grows, Mahalanobis should eventually win if geometry matters. Similarly, fine conditioning (e.g., many MAI bins) reduces bias but increases variance. The observed 'sensitivity' is a sample-size artifact, not a structural mismatch.

### Evidence and alternatives

**Plausible counterexamples**

- In a large-scale dataset (N>10,000 calibration samples), Mahalanobis distance outperforms softmax margin consistently across all strata, and fine conditioning (e.g., 50 MAI bins) outperforms coarse conditioning.
- Simulation studies show that with infinite data, the coverage of all nonconformity scores converges to nominal if the conditioning captures the true heterogeneity axes; differences vanish asymptotically.

**Confounders and alternatives**

- Classifier architecture and training procedure affect the geometry of softmax outputs, confounding nonconformity score comparisons.
- Feature standardization and missing modality handling interact with nonconformity scores (e.g., Mahalanobis requires careful imputation).

**Evidence supporting the competitor**

- Statistical learning theory: nonparametric quantile estimation rates depend on effective sample size per conditioning cell.
- Empirical studies in conformal prediction showing that Mondrian taxonomy with too many strata hurts coverage due to insufficient calibration points per stratum.

**Evidence refuting the competitor**

- Experiments where even with large calibration sets, margin scores fail for multimodal feature distributions while Mahalanobis succeeds, indicating geometric mismatch.
- Studies showing that certain conditioning strategies (e.g., mixture-model clusters) achieve nominal coverage with fewer samples than fixed bins, suggesting structural alignment matters beyond sample size.

### Distinguishing experiments

#### P4-F1: Nonconformity Score and Conditioning Strategy Comparison Across Sample Sizes

- Design: Using a large multi-subject wearable stress dataset (e.g., WESAD, N>1000 subjects), subsample calibration sets of varying sizes (n=50, 100, 500, 1000, 5000). For each size, evaluate a grid of nonconformity scores (softmax margin, Mahalanobis distance, conformalized quantile regression) and conditioning strategies (marginal, Mondrian with reactivity strata, block-conformal with transition phases, MAI bins, mixture-model clusters). Measure coverage and interval width on a fixed large test set. Plot coverage vs. calibration size for each combination. Test whether performance ranking changes with sample size (indicating variance-dominated) or remains stable (indicating bias-dominated).
- Working-theory prediction: Mahalanobis and mixture-model conditioning achieve nominal coverage at smaller sample sizes (n=500) and maintain advantage at all sizes; margin scores and fixed bins require larger n to reach nominal coverage. The ranking is stable, indicating structural alignment.
- Competitor prediction: At small n, margin scores and coarse conditioning win due to lower variance; at large n, Mahalanobis and fine conditioning win. The crossover point identifies the variance-bias tradeoff, not fundamental geometry.
- Measurable outcomes: Coverage probability vs. calibration set size for each score/strategy; Prediction interval width vs. size; Variance of coverage estimates across bootstrap resamples
- Expected effect: MEDIUM — Calibration sample size needed to achieve 95% coverage (±1%); Working theory: Mahalanobis/mixture-model need ~500 samples; margin/fixed bins need ~5000. Competitor: crossover at ~2000 samples.; target: ≥2x difference in required sample size between best and worst strategy at nominal coverage; stability of ranking across sizes.
- Effect rationale: H6, H7, H8 suggest medium effect sizes for score/strategy choice; sample size effects are well-known in conformal literature.
- Required data/metadata: Large multi-subject wearable stress dataset with multimodal features (ECG, EDA, respiration, accelerometer); Pre-trained stress classifier; Implementations of all nonconformity scores and conditioning strategies; Computational resources for extensive subsampling experiments
- Difficulty: LOW — Computational experiment on existing data; no new data collection needed.
- Working-theory failure condition: If the performance ranking of nonconformity scores/conditioning strategies reverses as calibration size increases (i.e., margin scores win at small n, Mahalanobis wins at large n), the working theory that structural mismatch is primary is falsified.
- Literature: [L1](https://proceedings.mlr.press/v25/vovk12.html), [L5](https://arxiv.org/abs/2006.02544)

#### P4-F2: Synthetic Feature Geometry Stress Test for Nonconformity Scores

- Design: Generate synthetic multimodal feature distributions with known geometry: (1) Gaussian with correlated modalities, (2) mixture of Gaussians (multimodal), (3) heavy-tailed (t-distribution), (4) nonlinear manifold. Embed a known stress label with varying signal-to-noise. Train a classifier on each. Apply conformal prediction with different nonconformity scores (margin, Mahalanobis, CQR) and conditioning strategies (true latent class, estimated clusters, marginal). Since ground truth geometry is known, we can isolate the effect of geometric mismatch from sample size by using large calibration sets (n=10,000). Measure coverage conditional on true latent class.
- Working-theory prediction: Mahalanobis and CQR achieve nominal conditional coverage for all geometries when conditioned on true latent class; margin scores fail for multimodal and heavy-tailed geometries even with large n. Estimated clusters perform nearly as well as true labels if clustering captures geometry.
- Competitor prediction: All scores achieve nominal coverage with large n if conditioned on true latent class; differences only appear at small n. Margin scores are not fundamentally misaligned.
- Measurable outcomes: Conditional coverage per true latent class for each score; Coverage gap between true-label conditioning and estimated-cluster conditioning; Interval width efficiency
- Expected effect: LARGE — Conditional coverage deviation from nominal for margin vs. Mahalanobis in multimodal geometry; Margin scores show >15% conditional coverage drop in minority modes; Mahalanobis/CQR show <2%.; target: ≥10% absolute conditional coverage difference between margin and Mahalanobis in multimodal/heavy-tailed settings with n=10,000.
- Effect rationale: H6 and H8 posit large geometric mismatch effects; synthetic control isolates geometry.
- Required data/metadata: Synthetic data generator with controllable geometry; Classifier training pipeline; Conformal prediction implementations; Clustering algorithms for estimated conditioning
- Difficulty: LOW — Purely computational; no human data needed.
- Working-theory failure condition: If margin scores achieve nominal conditional coverage in all synthetic geometries with large n when conditioned on true latent class, the working theory that margin scores are fundamentally misaligned with multimodal feature geometry is falsified.
- Literature: [L3](https://arxiv.org/abs/1903.04684), [L8](https://arxiv.org/abs/2202.13415)

### Novelty

- Rating: MEDIUM
- Rationale: Conditional conformal prediction (L1) and adaptive prediction sets (L5) are established. The novelty is the systematic empirical and synthetic comparison of nonconformity scores and conditioning strategies across sample sizes and known geometries, explicitly testing the bias-variance tradeoff vs. structural mismatch. Closest works (L1, L5) provide theoretical foundations but not this comprehensive empirical/synthetic benchmark.
- Novel contribution: First large-scale empirical and synthetic benchmark of nonconformity scores and conditioning strategies for wearable stress detection, disentangling finite-sample variance effects from fundamental geometric mismatch.
- Closest literature: [L1](https://proceedings.mlr.press/v25/vovk12.html), [L5](https://arxiv.org/abs/2006.02544)

## P5: Hidden stratification and label noise from unobserved subpopulations

**Working-theory claim:** Unobserved subpopulations (mislabeling due to self-report bias, demographic underrepresentation, clinical subgroups, recall bias, MNAR missingness) create latent strata with distinct error distributions or label noise patterns. Marginal conformal prediction mixes these strata, causing coverage failures for the underrepresented or mislabeled groups.

**Strongest competitor:** The coverage failures attributed to hidden stratification are actually due to model misspecification in the stress classifier: the classifier fails to capture relevant feature interactions for certain subgroups, leading to systematic prediction errors that conformal prediction correctly reflects as wider intervals. The 'hidden strata' are not distinct subpopulations with different label noise, but regions of feature space where the classifier is poorly calibrated due to insufficient representation in training data. Conformal prediction is working as intended by widening intervals where classifier uncertainty is high.

**Competitor mechanism:** The stress classifier (e.g., a neural network) learns a decision boundary that is accurate on average but has high error in regions of feature space corresponding to underrepresented groups (e.g., older adults, high alexithymia). These regions have fewer training samples, so the classifier's predicted probabilities are miscalibrated (overconfident). Conformal prediction uses these miscalibrated scores, producing nonconformity scores that are too small for these groups, leading to undercoverage. This is a classifier calibration issue, not a hidden stratification issue per se. Improving classifier calibration (e.g., via temperature scaling, focal loss) would resolve coverage failures without needing latent variable models.

### Evidence and alternatives

**Plausible counterexamples**

- After applying temperature scaling to the classifier on a validation set, conformal coverage becomes nominal across all demographic subgroups without any latent variable modeling.
- In a dataset with balanced representation across subgroups, coverage failures disappear even without explicit stratification, suggesting the issue was training data imbalance, not hidden subpopulations.

**Confounders and alternatives**

- Differential missingness (MNAR) due to device discomfort in certain subgroups creates selection bias that mimics label noise.
- Personality traits (alexithymia, neuroticism) affect both self-report accuracy and physiological reactivity, confounding subgroup identification.

**Evidence supporting the competitor**

- ML literature shows that classifier calibration techniques (temperature scaling, isotonic regression) improve conformal coverage in underrepresented groups.
- Studies demonstrating that conformal prediction coverage correlates with classifier calibration error (e.g., ECE) across subgroups.

**Evidence refuting the competitor**

- Experiments where classifier calibration is near-perfect (ECE<0.01) but conformal coverage still fails for clinically defined subgroups (e.g., beta-blocker users), indicating distinct error distributions.
- Latent variable conformal predictors that infer subgroups achieve nominal coverage in each inferred cluster, and clusters align with external clinical markers, confirming hidden stratification.

### Distinguishing experiments

#### P5-F1: Classifier Calibration vs. Latent Variable Conformal Prediction for Hidden Stratification

- Design: Using a wearable stress dataset with rich metadata (demographics, clinical screening GAD-7/PHQ-9, medication, personality questionnaires), train a stress classifier. Measure classifier calibration error (ECE) overall and per subgroup. Apply three conformal predictors: (A) marginal conformal on raw classifier scores, (B) marginal conformal on temperature-scaled classifier scores, (C) latent variable conformal predictor using a finite mixture model on physiological response features (HRV/EDA reactivity) with clinical covariates as fixed effects (as in H6). Evaluate per-subgroup coverage (defined by clinical screening, medication, demographics).
- Working-theory prediction: Predictor (C) achieves nominal coverage in all subgroups; (A) and (B) fail in subgroups with high clinical screening scores or beta-blocker use. Classifier calibration (B) improves overall coverage but not subgroup-specific coverage.
- Competitor prediction: Predictor (B) achieves nominal coverage in all subgroups; (C) provides no additional benefit. Subgroup coverage failures in (A) are fully explained by classifier miscalibration (high ECE in those subgroups).
- Measurable outcomes: Per-subgroup coverage probability for each predictor; Classifier ECE per subgroup; Mixture model cluster alignment with clinical variables (ARI, chi-square)
- Expected effect: LARGE — Coverage deviation from nominal in high-risk subgroups (e.g., GAD-7≥10, beta-blocker users); Working theory: (A) and (B) show >15% undercoverage in high-risk subgroups; (C) achieves ±1%. Competitor: (B) achieves ±1% in all subgroups.; target: ≥10% absolute coverage difference between (B) and (C) in high-risk subgroups; mixture model clusters significantly associated with clinical variables (p<0.01).
- Effect rationale: H6 and H10 report large effects for hidden stratification; classifier calibration effects are typically medium.
- Required data/metadata: Wearable stress dataset with clinical screening (GAD-7, PHQ-9), medication logs, demographics, personality questionnaires; Physiological response features (HRV/EDA reactivity); Stress classifier training pipeline; Temperature scaling and mixture model implementations
- Difficulty: MEDIUM — Requires dataset with rich clinical metadata; feasible with existing cohorts like WESAD extensions or new collection.
- Working-theory failure condition: If temperature-scaled conformal predictor (B) achieves nominal coverage in all clinically defined subgroups, the working theory that hidden stratification requires latent variable modeling is falsified.
- Literature: [L4](https://arxiv.org/abs/1904.06019), [L6](https://arxiv.org/abs/2106.00170)

#### P5-F2: Missingness Mechanism and Label Noise: Selection Model Conformal Prediction

- Design: In a longitudinal wearable study (N=200), intentionally introduce controlled missingness mechanisms: (1) MCAR (random), (2) MAR (missingness depends on observed activity level), (3) MNAR (missingness depends on unobserved stress level, simulated via a proxy). Collect self-reported stress labels with known recall bias (e.g., end-of-day recall vs. momentary EMA). Apply conformal predictors: (A) marginal ignoring missingness, (B) weighted conformal with inverse probability weighting (IPW) using a model for missingness, (C) selection model conformal that jointly models missingness and label noise via a latent variable. Evaluate coverage in subgroups defined by missingness propensity and recall bias severity.
- Working-theory prediction: Predictor (C) achieves nominal coverage under MNAR missingness and recall bias; (A) and (B) fail. The latent variable model recovers the true stress distribution.
- Competitor prediction: Predictor (B) (IPW) achieves nominal coverage under MAR and MNAR if the missingness model is correct; (C) is unnecessary. Recall bias is a form of label noise that conformal prediction handles via wider intervals if classifier is calibrated.
- Measurable outcomes: Coverage per missingness mechanism and recall bias condition; Bias in estimated stress prevalence; Calibration of latent variable model posterior
- Expected effect: MEDIUM — Coverage deviation under MNAR missingness; Working theory: (A) and (B) show 10-15% undercoverage under MNAR; (C) within ±2%. Competitor: (B) within ±2% if missingness model correct.; target: ≥8% absolute coverage difference between (B) and (C) under MNAR; (C) coverage within ±2% of nominal.
- Effect rationale: H5 and H10 suggest medium effects for MNAR missingness and recall bias; IPW often works for MAR but struggles with MNAR.
- Required data/metadata: Longitudinal wearable data with simulated missingness mechanisms; Momentary EMA and end-of-day recall stress labels; Missingness propensity models; Selection model conformal implementation
- Difficulty: MEDIUM — Requires longitudinal data collection with EMA; simulation of missingness mechanisms is computational.
- Working-theory failure condition: If IPW conformal (B) achieves nominal coverage under MNAR missingness and recall bias, the working theory that selection models are needed for MNAR is falsified.
- Literature: [L2](https://arxiv.org/abs/1604.04173), [L7](https://arxiv.org/abs/2010.09107)

### Novelty

- Rating: HIGH
- Rationale: Weighted conformal for covariate shift (L4) and adaptive conformal (L6) exist. The novelty is the explicit comparison of classifier calibration vs. latent variable conformal prediction for hidden stratification in wearable stress detection, and the use of selection models for MNAR missingness and recall bias in self-reported labels. Closest works (L4, L6) address covariate shift and adaptation but not label noise and MNAR missingness in conformal stress detection.
- Novel contribution: First study to pit classifier calibration against latent variable conformal prediction for hidden stratification in wearable stress detection, and to develop selection model conformal prediction for MNAR missingness and recall bias in self-reported stress labels.
- Closest literature: [L4](https://arxiv.org/abs/1904.06019), [L6](https://arxiv.org/abs/2106.00170)

## Ranked research roadmap

| Rank | Experiment | Pattern | Priority | Impact | Feasibility | Publication | Information gain | Difficulty |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | P5-F1: Classifier Calibration vs. Latent Variable Conformal Prediction for Hidden Stratification | P5 | 4.50 | 5 | 3 | 5 | 5 | MEDIUM |
| 2 | P4-F2: Synthetic Feature Geometry Stress Test for Nonconformity Scores | P4 | 4.40 | 4 | 5 | 4 | 5 | LOW |
| 3 | P1-F1: Physiological vs. Signal-Quality Conditioning in Multi-Subject Conformal Stress Detection | P1 | 4.25 | 5 | 2 | 5 | 5 | HIGH |
| 4 | P2-F1: Disentangling Classifier Drift from Error Distribution Shift in Longitudinal Conformal Stress Detection | P2 | 4.25 | 5 | 2 | 5 | 5 | HIGH |
| 5 | P4-F1: Nonconformity Score and Conditioning Strategy Comparison Across Sample Sizes | P4 | 4.25 | 4 | 5 | 4 | 4 | LOW |
| 6 | P1-F2: Counterfactual Simulation of Physiological vs. Technical Heterogeneity | P1 | 3.90 | 4 | 3 | 4 | 5 | MEDIUM |
| 7 | P3-F1: Artifact vs. Intrinsic Heteroscedasticity: Conditional Conformal Prediction with MAI and Physiological State | P3 | 3.90 | 4 | 3 | 4 | 5 | MEDIUM |
| 8 | P2-F2: Controlled Laboratory Induction of Autonomic Transitions vs. Classifier Drift | P2 | 3.75 | 4 | 3 | 4 | 4 | MEDIUM |
| 9 | P5-F2: Missingness Mechanism and Label Noise: Selection Model Conformal Prediction | P5 | 3.75 | 4 | 3 | 4 | 4 | MEDIUM |
| 10 | P3-F2: Strap Tightness and Electrode Impedance as Artifact Proxies: A Controlled Perturbation Study | P3 | 3.40 | 3 | 4 | 3 | 4 | LOW |

## Validated literature

- **L1.** Vladimir Vovk (2012). [Conditional Validity of Inductive Conformal Predictors](https://proceedings.mlr.press/v25/vovk12.html). Proceedings of Machine Learning Research 25 (ACML).
- **L2.** Jing Lei, Max G'Sell, Alessandro Rinaldo, Ryan J. Tibshirani, Larry Wasserman (2018). [Distribution-Free Predictive Inference For Regression](https://arxiv.org/abs/1604.04173). Journal of the American Statistical Association.
- **L3.** Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas, Ryan J. Tibshirani (2019). [The limits of distribution-free conditional predictive inference](https://arxiv.org/abs/1903.04684). arXiv preprint arXiv:1903.04684.
- **L4.** Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas (2019). [Conformal Prediction Under Covariate Shift](https://arxiv.org/abs/1904.06019). Advances in Neural Information Processing Systems 32.
- **L5.** Yaniv Romano, Matteo Sesia, Emmanuel J. Candès (2020). [Classification with Valid and Adaptive Coverage](https://arxiv.org/abs/2006.02544). Advances in Neural Information Processing Systems 33.
- **L6.** Isaac Gibbs, Emmanuel J. Candès (2021). [Adaptive Conformal Inference Under Distribution Shift](https://arxiv.org/abs/2106.00170). Advances in Neural Information Processing Systems 34.
- **L7.** Chen Xu, Yao Xie (2021). [Conformal prediction for time series](https://arxiv.org/abs/2010.09107). International Conference on Machine Learning (conference version).
- **L8.** Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas, Ryan J. Tibshirani (2023). [Conformal prediction beyond exchangeability](https://arxiv.org/abs/2202.13415). Annals of Statistics.
