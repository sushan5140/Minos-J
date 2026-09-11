# Meno-J Experiment 9: WESAD Real-Data Falsification Study

Protocol status: **FROZEN BEFORE COVERAGE ANALYSIS**

## Questions

1. Does conformal score and conditioning choice materially alter subject-level WESAD coverage?
2. Does motion-region conditioning improve worst-subject coverage without relying on uninformative full prediction sets?
3. Does the safest synthetic Experiment 6 pair transfer to real WESAD windows?

## Data contract

- Fifteen official WESAD subjects: S2–S11 and S13–S17.
- Chest ACC, ECG, EMG, EDA, temperature, and respiration at 700 Hz.
- Included states: baseline (1), stress (2), and amusement (3).
- Excluded states and transitions: 0, 4, 5, 6, and 7.
- Raw pickle loading is restricted to NumPy reconstruction primitives.

## Window and feature contract

- 60-second non-overlapping windows.
- Every window must lie completely inside one contiguous included-state run.
- Transition windows are excluded.
- Five scalar channels plus three acceleration axes and acceleration magnitude.
- Nine deterministic distribution and dynamics statistics per channel.

## Evaluation contract

- Target coverage: 0.90.
- Held-out test unit: one complete subject.
- Three deterministic repetitions per test subject.
- Each fold: 10 training subjects, 4 calibration subjects, 1 test subject.
- Classifier: NumPy regularized linear discriminant analysis.
- Scores: margin, inverse probability, and distance to class centroid.
- Conditioning: marginal, class-Mondrian, and motion-region Mondrian.
- Motion region is assigned using only the calibration-set median of ACC-magnitude standard deviation.
- Coverage is reported by class, motion region, and within-state temporal tertile.
- Prediction-set size, full-set frequency, and empty-set frequency are co-primary diagnostics.

## Primary transfer test

The synthetic safest pair is distance-to-centroid scoring plus motion-region conditioning. The synthetic danger pair is inverse-probability scoring plus marginal conditioning.

Transfer is supported only if the safest pair improves worst-subject mean coverage by at least 0.05 and increases mean full-set frequency by no more than 0.20. Otherwise the synthetic ranking is falsified for this real-data protocol.

## Safety and reproducibility

- Subject-disjoint splits prevent window leakage between train, calibration, and test.
- The raw dataset remains read-only.
- Feature checkpoints are written after each subject.
- No LLM, OpenRouter call, or API key is used.
