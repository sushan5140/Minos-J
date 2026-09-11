# Meno-J Experiment 11 — Working-Theory Update

## Decision

**SUPPORTED_RIVALS_R2_AND_R3**

Experiment 11 supports two parts of the rival theory: stable subject baselines distort the population representation, and one sensor family can add subject-specific predictive interference. It does not support a safe single jump at the 18-to-19 conformal order-statistic boundary, nor does it support either tested nonlinear classifier as a repair.

## What changed

### The order-statistic boundary was real but not safely monotonic

Moving from 18 to 19 personal calibration examples changed the 90% conformal threshold from the maximum score to the second-largest score. Full-label sets fell from 0.3081 to 0.1911, but mean coverage fell from 0.9778 to 0.9185 and worst-subject coverage fell by 0.1333. The preregistered safety rule therefore failed.

This is an important falsification: crossing the mathematical threshold boundary makes predictions more informative, but it is not automatically a safe readiness jump for every subject.

### Subject normalization produced the largest cohort-level improvement

Per-subject median/IQR normalization increased mean classifier accuracy from 0.6578 to 0.8163, reduced full-label sets from 0.1911 to 0.0889, and reduced robustness loss by 0.0315 while retaining mean coverage of 0.9111.

The effect was not uniform. S4 accuracy rose from 0.3778 to 0.9111 and its full-label-set frequency fell from 0.5111 to zero. S2 accuracy rose only from 0.5556 to 0.6222, while its full-label-set frequency increased from 0.3111 to 0.6889. The cohort result supports baseline mismatch, but the targeted S2/S4 repair rule did not pass.

### Temperature features showed exploratory predictive interference

Removing temperature features was the only single-sensor-family ablation to meet the preregistered rule. S2/S4 mean accuracy improved by 0.1000, their robustness loss fell by 0.0417, and overall accuracy improved by 0.0178. This is evidence of representation-specific interference, not evidence that temperature is physiologically irrelevant or that the sensor malfunctioned.

### Added classifier complexity did not repair the problem

Fixed diagonal QDA improved S2/S4 accuracy but reduced overall accuracy by 0.0904 and increased their full-set frequency by 0.2222. Distance-weighted 15-neighbor classification reduced overall accuracy by 0.0489 and increased S2/S4 full sets by 0.3778. Neither passed.

## Revised J-jump candidate

The working concept is now a **subject-conditional calibration readiness surface**.

Readiness does not occur at one universal calibration count. It depends jointly on:

1. threshold stability—enough representative calibration examples to avoid an extreme order statistic; and
2. representation adequacy—the model must encode within-subject state changes rather than stable subject identity or interfering sensor variation.

Crossing one boundary can expose the other. More calibration can shrink sets while harming the worst subject; better normalization can transform one subject while leaving another ambiguous.

## Next decisive test

Cross raw and subject-normalized representations with calibration counts on both sides of the order-statistic boundary. Repeat the test across temporal blocks or independent sessions, with subjects declared before analysis. The key question is whether the S4 normalization repair and the S2 residual failure replicate without post-selection.

## Guardrails

- S2 and S4 remain post-selected exploratory cases.
- One order-statistic transition does not establish the full shape of the calibration frontier.
- Sensor ablation diagnoses predictive interference, not physical malfunction.
- Only two fixed nonlinear alternatives were tested.
- WESAD provides one recording session per subject, limiting stability claims.
- No literature novelty claim is made.

Independent exact replay: **PASS**.
