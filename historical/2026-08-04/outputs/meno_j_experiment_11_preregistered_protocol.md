# Meno-J Experiment 11: Representation-versus-Calibration Falsification

**Protocol status: FROZEN BEFORE EXPERIMENT 11 OUTCOME ANALYSIS**

## Question

When S2 and S4 remain uninformative after personal calibration, is the limiting mechanism calibration order statistics, subject baseline mismatch, a misleading sensor family, or the classifier representation?

## Shared design

Experiment 11 reuses the exact Experiment 10 held-out-subject folds, personal test construction, and hash-validated Experiment 9 features. Fifteen personal test windows remain untouched in every fold. No raw WESAD pickle, API, or external model is used.

## Rival 1: calibration order statistics

Run nested personal calibration counts of 9, 12, 15, 18, 19, and 20 with the fixed LDA representation. At `alpha = 0.1`, the conformal threshold is the maximum observed score through `n = 18`; at `n = 19` it becomes the second-largest score.

Support requires the 18-to-19 transition to reduce mean full-set frequency by at least 0.03, retain mean coverage of at least 0.88, and reduce worst-subject coverage by no more than 0.05.

## Rival 2: subject baseline mismatch

Apply per-subject median centering and robust IQR scaling. Training subjects use only their own training windows. The held-out subject uses only its unlabeled onboarding pool.

General support requires improvements of at least 0.03 in both mean classifier accuracy and mean robustness loss. Targeted S2/S4 support additionally requires at least 0.10 accuracy improvement for both subjects and a 0.10 reduction in their mean full-set frequency while retaining at least 0.80 coverage.

## Rival 3: sensor-family interference

Remove ECG, EMG, EDA, temperature, respiration, or all acceleration features one family at a time. Support requires one removal to improve mean S2/S4 accuracy by at least 0.10, reduce their mean robustness loss by at least 0.03, and reduce overall accuracy by no more than 0.03.

## Rival 4: classifier representation

Compare regularized LDA with two fixed NumPy-only nonlinear alternatives:

- class-specific diagonal QDA with 20% variance shrinkage;
- distance-weighted 15-nearest-neighbor classification with 0.5 pseudocounts.

Support requires an alternative to improve mean S2/S4 accuracy by at least 0.10, reduce their full-set frequency by at least 0.10 while retaining at least 0.80 coverage, and reduce overall accuracy by no more than 0.03.

## Continuity requirement

The Experiment 11 `k = 9` and `k = 12` LDA results must exactly reproduce the corresponding Experiment 10 metrics.

All conclusions remain exploratory for S2/S4, and no literature-novelty claim is permitted from this experiment alone.
