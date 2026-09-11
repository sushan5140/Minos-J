# Meno-J Literature Review After Experiment 14

## Outcome

The review changes the next move: **do not build a retrospective raw-versus-normalized subject gate yet.** First test whether failures are the specific high-confidence/low-trust errors predicted by conditional-coverage theory.

## Review scope and integrity

- Primary sources screened: 19
- Full texts reviewed: 18
- Abstract/partial only: 1
- LLM/API calls: none
- Sources: primary papers and official publication/dataset pages

## What the papers collectively say

### F1: Exact distribution-free individual conditional coverage is not a scientifically defensible target.

Evidence: L01, L04.

Meno-J action: Use marginal guarantees plus explicitly bounded low-complexity subgroup diagnostics; report that subject coverage is empirical, not guaranteed.

### F2: A data-selected subject gate can manufacture apparent safety unless selection is nested or validity-preserving.

Evidence: L05, L08.

Meno-J action: Do not retrospectively choose raw versus normalized per subject from the same 33 outcomes.

### F3: Covariate weighting is valid only for a narrower shift than the wearable evidence makes plausible.

Evidence: L02, L15, L16.

Meno-J action: Treat weighted conformal as one rival mechanism and measure effective sample size; do not call it the default repair.

### F4: Class-conditional repair and covariate-conditional repair are different problems.

Evidence: L01, L06, L09.

Meno-J action: Experiment 14's class-gap repair does not contradict its subject-safety failure; diagnose classifier-manifold mismatch next.

### F5: The most testable label-free warning signal is confident prediction combined with low geometric trust.

Evidence: L09, L13, L17.

Meno-J action: Run a frozen confidence–trust conditional coverage diagnostic before building any gate or score repair.

### F6: Published stress personalization gains often use labels, a known neutral baseline, or a different normalization operation.

Evidence: L12, L13, L14, L17.

Meno-J action: Do not transfer those claims to Meno-J's unlabeled mixed onboarding design.

### F7: The strongest novelty position is falsification of cross-person uncertainty safety, not conformal prediction on wearables in general.

Evidence: L11, L16, L18.

Meno-J action: Frame the paper around auditable failure diagnosis and rival discrimination across subjects and protocols.

## Paper-by-paper extraction

### L01: [The limits of distribution-free conditional predictive inference](https://par.nsf.gov/servlets/purl/10253824)

- Rina Foygel Barber; Emmanuel J. Candès; Aaditya Ramdas; Ryan J. Tibshirani (2021), Information and Inference
- Review status: full text
- Worth retaining: Exact distribution-free covariate-conditional coverage is nontrivially impossible; useful relaxations must restrict the group class and control its complexity relative to sample size.
- Consequence for Meno-J: Do not claim individual-subject conditional coverage. Any subject reliability rule must be low-dimensional, frozen, and evaluated outside the data used to select it.

### L02: [Conformal Prediction Under Covariate Shift](https://arxiv.org/pdf/1904.06019)

- Ryan J. Tibshirani; Rina Foygel Barber; Emmanuel J. Candès; Aaditya Ramdas (2019), NeurIPS
- Review status: full text
- Worth retaining: Likelihood-ratio weighting restores a target-distribution guarantee only when the conditional label law is unchanged; variable weights reduce effective calibration sample size.
- Consequence for Meno-J: Weighted conformal is a falsifiable rival, not an assumed repair. Report weight concentration and effective sample size, and distinguish covariate shift from posterior or protocol shift.

### L03: [Localized Conformal Prediction: A Generalized Inference Framework for Conformal Prediction](https://arxiv.org/pdf/2106.08460)

- Leying Guan (2023), Biometrika
- Review status: full text
- Worth retaining: Naively replacing a global quantile with a local weighted quantile at the same nominal level can under-cover arbitrarily; localization requires a validity-preserving level adjustment.
- Consequence for Meno-J: Do not implement an ad-hoc nearest-subject calibration rule. First diagnose whether local similarity predicts failure, then use a formally valid localized method if warranted.

### L04: [Conformal Prediction With Conditional Guarantees](https://arxiv.org/pdf/2305.12616)

- Isaac Gibbs; John J. Cherian; Emmanuel J. Candès (2025), Journal of the Royal Statistical Society Series B
- Review status: full text
- Worth retaining: Finite-dimensional, predeclared shift classes can support conditional guarantees; increasingly flexible classes incur explicit statistical and computational costs.
- Consequence for Meno-J: Prefer a tiny prespecified diagnostic space over a free-form subject gate or high-dimensional partition learner.

### L05: [Conformal Prediction with Learned Features](https://proceedings.mlr.press/v235/kiyani24a.html)

- Shayan Kiyani; George J. Pappas; Hamed Hassani (2024), ICML
- Review status: full text
- Worth retaining: Learning uncertainty partitions improves approximate conditional behavior, but the number of groups trades approximation error against fewer calibration samples per group and requires validation or nested splitting.
- Consequence for Meno-J: The 33-subject cohort is too small for unconstrained partition discovery. Treat learned grouping as future work or use fully nested subject-level evaluation.

### L06: [Classification with Valid and Adaptive Coverage](https://papers.nips.cc/paper_files/paper/2020/file/244edd7e85dc81602b7615cd705545f5-Paper.pdf)

- Yaniv Romano; Matteo Sesia; Emmanuel Candès (2020), NeurIPS
- Review status: full text
- Worth retaining: Adaptive classification scores can improve set adaptivity, but their conditional behavior depends on the quality of estimated class probabilities.
- Consequence for Meno-J: After class-Mondrian failed to restore subject safety, investigate probability-model mismatch rather than adding more class-threshold variants.

### L07: [Uncertainty Sets for Image Classifiers using Conformal Prediction](https://people.eecs.berkeley.edu/~angelopoulos/publications/downloads/conformal-classification.pdf)

- Anastasios N. Angelopoulos; Stephen Bates; Michael Jordan; Jitendra Malik (2021), ICLR
- Review status: full text
- Worth retaining: RAPS regularization principally controls many small, unlikely classes in large-label problems.
- Consequence for Meno-J: RAPS is low priority for a binary stress task; score quality and subject shift are more plausible bottlenecks.

### L08: [Conformal Classification with Equalized Coverage for Adaptively Selected Groups](https://arxiv.org/pdf/2405.15106)

- Yanfei Zhou; Matteo Sesia (2024), arXiv preprint
- Review status: full text
- Worth retaining: Selecting the worst-covered attribute using the same calibration data creates selection bias; the paper uses a permutation-invariant leave-one-out construction to preserve validity without an extra split.
- Consequence for Meno-J: A retrospectively selected raw-versus-normalized subject gate would be invalid evidence. Selection must be nested or use a validity-preserving adaptive construction.

### L09: [Conformal Prediction Sets with Improved Conditional Coverage using Trust Scores](https://arxiv.org/pdf/2501.10139)

- Jivat Neet Kaur; Michael I. Jordan; Ahmed Alaa (2025), arXiv preprint
- Review status: full text
- Worth retaining: Miscoverage concentrates when classifiers are confidently wrong; confidence plus a nonparametric trust score provides a low-dimensional proxy for disagreement with the Bayes classifier.
- Consequence for Meno-J: This is the strongest next diagnostic: test whether normalized class-Mondrian failures concentrate in high-confidence, low-trust physiological windows.

### L10: [Rectifying Conformity Scores for Better Conditional Coverage](https://arxiv.org/abs/2502.16336)

- Vincent Plassier; Alexander Fishkov; Victor Dheur; Mohsen Guizani; Souhaib Ben Taieb; Maxim Panov; Eric Moulines (2025), ICML
- Review status: full text
- Worth retaining: Rectified scores preserve exact marginal validity while approximate conditional validity depends explicitly on conditional-quantile estimation error; the method needs extra data splitting or out-of-sample scores.
- Consequence for Meno-J: Score rectification is a plausible later repair only after the low-dimensional failure signal is verified and an independent split is reserved for quantile estimation.

### L11: [WESAD: A Multimodal Dataset for Wearable Stress and Affect Detection](https://ubi29.informatik.uni-siegen.de/usi/data_wesad.html)

- Philip Schmidt; Attila Reiss; Robert Duerichen; Claus Marberger; Kristof Van Laerhoven (2018), ICMI
- Review status: full text
- Worth retaining: WESAD contains 15 subjects, wrist and chest signals, and baseline, stress, amusement, and meditation conditions; its benchmark reports average classification performance rather than subject-conditional conformal safety.
- Consequence for Meno-J: Meno-J's contribution is not another average-accuracy WESAD benchmark; it is the falsification of uncertainty guarantees across people and protocols.

### L12: [An Improved Subject-Independent Stress Detection Model Applied to Consumer-grade Wearable Devices](https://doras.dcu.ie/27656/1/MMM22_Tu_MACHU_new_version%20%281%29.pdf)

- Anh Ninh; Tu Machu; Cathal Gurrin (2022), MMM
- Review status: full text
- Worth retaining: The study normalizes each 60-second signal segment before feature extraction and reports subject-independent stress accuracy, but its normalization target differs from subject onboarding median/IQR scaling.
- Consequence for Meno-J: Do not cite generic stress normalization as validation of Experiment 13's onboarding transform; the operations remove different information and answer different questions.

### L13: [Effect of Person-specific Biometrics in Improving Generic Stress Predictive Models](https://sensors.myu-group.co.jp/sm_pdf/SM2131.pdf)

- Kizito Nkurikiyeyezu; Toshiya Yokokubo; Guillaume Lopez (2020), Sensors and Materials
- Review status: full text
- Worth retaining: Large gains came from adding labeled person-specific samples and retraining; normalization alone remained below supervised person-specific adaptation.
- Consequence for Meno-J: This does not validate label-free onboarding. It predicts that unlabeled normalization may be insufficient when the label mechanism itself differs by person.

### L14: [Personalized Stress Detection from Physiological Measurements](https://www.memphis.edu/cs/santosh-kumar/papers/qol_paper4.pdf)

- Fang-Yu Sun; Chao-Wen Hsu; Chih-Kai Chuang; Santosh Kumar (2010), International Conference on Quality of Life Technology
- Review status: full text
- Worth retaining: Deviation from a labeled neutral baseline improved personalized stress precision, and temporal aggregation improved performance further.
- Consequence for Meno-J: A known neutral baseline is informative but unavailable in our label-free mixed onboarding protocol; temporal and baseline mechanisms should remain separate hypotheses.

### L15: [Stressor Type Matters! Exploring Factors Influencing Cross-Dataset Generalizability of Machine Learning Stress Detection Models Using Heart Rate Variability](https://arxiv.org/abs/2405.09563)

- Preetham Prajod; Dario M. Sommer; Alexander L. Francis; Thomas Plötz (2024), arXiv preprint
- Review status: full text
- Worth retaining: Across four stress datasets, stressor type was the strongest observed driver of cross-dataset generalization differences in the studied HRV setting.
- Consequence for Meno-J: The PhysioNet protocol versions and short social/cognitive tasks can induce posterior shift; covariate weighting alone may therefore fail even with accurate density ratios.

### L16: [Cross Dataset Analysis for Generalizability of HRV-Based Stress Detection Models](https://pmc.ncbi.nlm.nih.gov/articles/PMC9960690/)

- Oumaima Benchekroun; Alexandre M. M. Sousa; Hugo Gamboa (2023), Sensors
- Review status: full text
- Worth retaining: Strong within-dataset models degraded sharply across datasets, with protocol, sensor, laboratory, and real-life differences implicated in transfer failure.
- Consequence for Meno-J: Experiment 13's modest accuracy gain but unsafe coverage is consistent with cross-protocol uncertainty shift, not merely a poor global threshold.

### L17: [An Adaptive System for Wearable Devices to Detect Stress Using Physiological Signals](https://arxiv.org/pdf/2407.15252)

- Gelei Xu; Ruiyang Qin; Zhi Zheng; Yiyu Shi (2024), arXiv position paper
- Review status: full text
- Worth retaining: The proposed wearable personalization path uses unlabeled adaptation followed by a small labeled fine-tuning stage, explicitly recognizing new-user domain shift.
- Consequence for Meno-J: A purely unlabeled gate should be evaluated as a limited safety diagnostic, not represented as equivalent to full personalized stress adaptation.

### L18: [Cover your cough: detection of respiratory events with confidence using a smartwatch](https://proceedings.mlr.press/v91/nguyen18a.html)

- Khuong An Nguyen; Zhiyuan Luo (2018), COPA / PMLR
- Review status: full text
- Worth retaining: Conformal prediction has been used with smartwatch sensing, but for cough and sneeze event confidence rather than cross-subject physiological stress coverage.
- Consequence for Meno-J: Wearable conformal prediction is not new by itself; the defensible novelty is subject- and protocol-level falsification in stress detection.

### L19: [Hierarchical adaptive conformal inference for reliable uncertainty quantification in edge-deployable medical wearables](https://www.sciencedirect.com/science/article/pii/S0263224126014740)

- Oussama El Allam; Mohamed Hamlich (2026), Measurement
- Review status: abstract/partial only
- Worth retaining: Abstract and accessible methods summary propose multi-timescale online adaptation for physiological drift and few-shot labeled personalization in ECG.
- Consequence for Meno-J: Online adaptation is relevant future work, but the inaccessible full text was not used to set Experiment 15's decision thresholds or claims.
- Limitation: Publisher full text was not accessible in the current environment; this record is screened, not counted as a top-to-bottom full-text review.

## Frozen next step

**Meno-J Experiment 15: Confidence–Trust Subject-Shift Diagnostic**

After class conditioning, does undercoverage concentrate in physiological windows where the classifier is highly confident but geometrically unsupported by its predicted-class training manifold?

Why now: It directly tests the probability-model mismatch mechanism without retrospectively optimizing a gate, preserves all prior outputs, and can fail cleanly.

Deferred until this mechanism survives:

- raw-versus-normalized subject gate
- localized conformal calibration
- covariate-weighted conformal calibration
- rectified conformity scores
- online adaptive conformal inference

## Boundaries

- This review is a targeted primary-paper review, not a formal systematic review or meta-analysis.
- One 2026 publisher article was abstract-screened only and is explicitly excluded from the full-text count.
- No literature source validates individual-subject coverage for the current Meno-J protocol.
- No novelty claim is based only on absence from keyword search.
