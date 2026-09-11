# Meno-J Experiment 10: Calibration Onboarding and Compatibility Bridge

## Result

**PERSONAL_CALIBRATION_REPAIR_SUPPORTED**

This experiment bridges cold-start external calibration and limited personal calibration while keeping the classifier fixed.

## Calibration onboarding curve

| Method | Mean coverage | Worst subject | Mean set size | Full sets | Finite thresholds |
|---|---:|---:|---:|---:|---:|
| external_all4 | 0.8785 | 0.6000 | 1.7956 | 0.2089 | 1.0000 |
| external_nearest2 | 0.8222 | 0.4889 | 1.5467 | 0.1141 | 1.0000 |
| external_farthest2 | 0.8859 | 0.6222 | 1.8578 | 0.2622 | 1.0000 |
| personal_k3 | 1.0000 | 1.0000 | 3.0000 | 1.0000 | 0.0000 |
| personal_k6 | 1.0000 | 1.0000 | 3.0000 | 1.0000 | 0.0000 |
| personal_k9 | 0.9467 | 0.8444 | 1.8770 | 0.2281 | 1.0000 |
| personal_k12 | 0.9659 | 0.8667 | 1.9585 | 0.2830 | 1.0000 |

## Preregistered personal-repair decision

- Supported: True
- Mean coverage change, k=12 versus external all4: 0.0874
- Worst-subject coverage change: 0.2667
- Mean full-set-frequency change: 0.0741

## S2 and S4

| Subject | External coverage | Personal k=12 coverage | Change | External full sets | Personal full sets | Repair | Persistent |
|---|---:|---:|---:|---:|---:|---|---|
| S2 | 0.6444 | 1.0000 | 0.3556 | 0.0000 | 0.3556 | False | True |
| S4 | 0.6444 | 0.9333 | 0.2889 | 0.0889 | 0.5111 | False | True |

## Calibration compatibility

- Supported: False
- Nearest-two robustness loss: 0.1789
- Farthest-two robustness loss: 0.1922
- Robustness-loss improvement: 0.0133
- Single-subject distance/loss correlation: 0.3560

## Finite-sample boundary

- personal_k3: finite thresholds 0.0%; full sets 100.0%
- personal_k6: finite thresholds 0.0%; full sets 100.0%
- personal_k9: finite thresholds 100.0%; full sets 22.8%
- personal_k12: finite thresholds 100.0%; full sets 28.3%

## Subject diagnostics

| Subject | Accuracy | Log loss | Feature shift | External coverage | Personal k=12 | Change |
|---|---:|---:|---:|---:|---:|---:|
| S2 | 0.5556 | 4.5684 | 1.6453 | 0.6444 | 1.0000 | 0.3556 |
| S3 | 0.7111 | 1.4593 | 1.3231 | 0.8444 | 0.8667 | 0.0222 |
| S4 | 0.3778 | 2.3009 | 1.1797 | 0.6444 | 0.9333 | 0.2889 |
| S5 | 0.7333 | 0.4653 | 0.4561 | 1.0000 | 0.9778 | -0.0222 |
| S6 | 0.7778 | 0.4071 | 0.8468 | 0.9778 | 1.0000 | 0.0222 |
| S7 | 0.6889 | 0.9727 | 1.0747 | 0.8444 | 1.0000 | 0.1556 |
| S8 | 0.7778 | 0.5818 | 0.4762 | 0.9333 | 0.9778 | 0.0444 |
| S9 | 0.5778 | 0.9888 | 0.3906 | 0.8889 | 1.0000 | 0.1111 |
| S10 | 0.3778 | 2.4828 | 0.6665 | 0.6000 | 0.9778 | 0.3778 |
| S11 | 0.6000 | 0.7978 | 0.5378 | 1.0000 | 1.0000 | 0.0000 |
| S13 | 0.8444 | 0.4127 | 0.6710 | 0.9556 | 1.0000 | 0.0444 |
| S14 | 0.6667 | 0.8259 | 0.6420 | 0.9333 | 0.9333 | 0.0000 |
| S15 | 0.6667 | 0.7453 | 0.5770 | 1.0000 | 0.9333 | -0.0667 |
| S16 | 0.7778 | 0.6732 | 0.7763 | 0.9778 | 0.9556 | -0.0222 |
| S17 | 0.7333 | 0.7453 | 1.0933 | 0.9333 | 0.9333 | 0.0000 |

## Limitations

- S2 and S4 are exploratory cases selected after Experiment 9, not an independent confirmation cohort.
- Only 15 personal test windows are available per fold under the non-overlapping window contract.
- Personal calibration changes the conformal threshold but does not retrain the classifier.
- Centroid distance is a simple compatibility proxy and does not establish a physiological mechanism.
- All data come from one 15-subject benchmark and require external replication.

## Reproducibility

- Reused hash-validated Experiment 9 features: yes
- Raw WESAD pickle loading: no
- Model/API call: no
- Test labels used for compatibility selection: no
- Independent exact replay: pending
