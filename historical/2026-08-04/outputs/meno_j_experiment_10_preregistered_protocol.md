# Meno-J Experiment 10: Calibration Onboarding and Compatibility Bridge

**Protocol status: FROZEN BEFORE EXPERIMENT 10 OUTCOME ANALYSIS**

## Purpose

Experiment 10 bridges the two deployment regimes exposed by BioConformal and Meno-J Experiment 9: personalized calibration after a subject has supplied data, and cold-start evaluation on a completely unseen subject.

It asks whether the difficult WESAD subjects recover as labeled personal calibration windows accumulate, and whether unlabeled physiological similarity can identify better external calibration subjects before a personal threshold is supportable.

## Fixed design

- Reuse the 15 hash-validated Experiment 9 feature checkpoints; do not reload or mutate raw WESAD data.
- Use the Experiment 9 60-second, non-overlapping, transition-free chest-signal feature contract.
- Hold out one subject, train regularized LDA on 10 other subjects, and retain four other subjects as the external calibration pool.
- Repeat three deterministic subject allocations for every held-out subject.
- Use inverse-probability nonconformity and target 90% coverage.
- Reserve 15 label-stratified personal test windows per subject and repetition: eight baseline, four stress, and three amusement.
- Keep the personal test set completely separate from compatibility estimation and calibration.
- Add nested personal labeled calibration sets of 3, 6, 9, and 12 windows.
- Do not retrain or fine-tune the classifier with personal windows.

## Honest finite-sample rule

At `alpha = 0.1`, fewer than nine personal calibration scores cannot yield a finite split-conformal threshold. Personal-only calibration at `k = 3` or `k = 6` must therefore return the full three-label set and cannot count as an informative repair.

## Compatibility comparison

The held-out subject is represented using only unlabeled onboarding-pool features standardized by training-subject statistics. External calibration subjects are ranked by centroid distance.

Compare:

- all four external calibration subjects;
- the two nearest external calibration subjects;
- the two farthest external calibration subjects as a negative control.

No held-out test label may influence compatibility selection.

## Preregistered decisions

- General personal repair requires `k = 12` to improve mean subject coverage by at least 0.05 and worst-subject coverage by at least 0.10 over external calibration, without increasing mean full-set frequency by more than 0.20.
- S2/S4 repair requires both subjects to gain at least 0.10 coverage, reach at least 0.80, and avoid a full-set-frequency increase above 0.20.
- Compatibility support requires nearest-subject calibration to reduce mean robustness loss by at least 0.03 versus farthest-subject calibration. Robustness loss is `abs(coverage - 0.90) + 0.25 × full-set frequency`.
- S2 or S4 remains persistently difficult if its finite-threshold `k = 12` coverage remains below 0.80 or apparent repair requires a full-set-frequency increase above 0.20.

## Guardrails

S2 and S4 are exploratory cases selected after Experiment 9. This experiment isolates calibration-threshold adaptation, not classifier personalization, and compatibility associations are not causal explanations. No novelty claim will be made without a separate literature review.
