# Meno-J Experiment 11: Representation-versus-Calibration Falsification

## Result

**SUPPORTED_RIVALS_R2_AND_R3**

Supported rivals: ['R2_SUBJECT_BASELINE_MISMATCH', 'R3_SENSOR_FAMILY_INTERFERENCE']

## Calibration frontier

| Personal k | Rank | Mean coverage | Worst subject | Mean set size | Full sets |
|---:|---:|---:|---:|---:|---:|
| 9 | 9 | 0.9467 | 0.8444 | 1.8770 | 0.2281 |
| 12 | 12 | 0.9659 | 0.8667 | 1.9585 | 0.2830 |
| 15 | 15 | 0.9704 | 0.8667 | 1.9719 | 0.2859 |
| 18 | 18 | 0.9778 | 0.9333 | 2.0044 | 0.3081 |
| 19 | 18 | 0.9185 | 0.8000 | 1.7452 | 0.1911 |
| 20 | 19 | 0.9244 | 0.8667 | 1.7763 | 0.2089 |

Order-statistic rival supported: **False**
Full-set reduction from k=18 to k=19: 0.1170
Worst-subject coverage change: -0.1333

## Representation and sensor interventions at k=19

| Arm | Accuracy | Coverage | Worst subject | Mean set size | Full sets | Robustness loss |
|---|---:|---:|---:|---:|---:|---:|
| lda_raw_all | 0.6578 | 0.9185 | 0.8000 | 1.7452 | 0.1911 | 0.1211 |
| lda_subject_robust_normalized | 0.8163 | 0.9111 | 0.8222 | 1.3422 | 0.0889 | 0.0896 |
| diagonal_qda_raw_all | 0.5674 | 0.9111 | 0.7778 | 1.8933 | 0.2696 | 0.1437 |
| distance_weighted_knn15_raw_all | 0.6089 | 0.8874 | 0.7111 | 2.1230 | 0.4356 | 0.1852 |
| lda_without_ECG | 0.6741 | 0.9170 | 0.7556 | 1.6385 | 0.1244 | 0.1074 |
| lda_without_EMG | 0.6430 | 0.9230 | 0.8667 | 1.7452 | 0.1659 | 0.1044 |
| lda_without_EDA | 0.6667 | 0.9259 | 0.8222 | 1.8756 | 0.2385 | 0.1270 |
| lda_without_Temp | 0.6756 | 0.9067 | 0.7556 | 1.7037 | 0.1496 | 0.1137 |
| lda_without_Resp | 0.6119 | 0.9244 | 0.8000 | 1.8133 | 0.2119 | 0.1263 |
| lda_without_ACC | 0.6874 | 0.9096 | 0.8000 | 1.7570 | 0.2074 | 0.1267 |

## Rival decisions

- Subject normalization, general support: True
- Subject normalization, S2/S4 support: False
- Sensor-family interference supported: True
- Alternative classifier representation supported: False

### Sensor ablations

| Arm | Supported | Overall accuracy Δ | S2/S4 accuracy Δ | S2/S4 robustness reduction |
|---|---|---:|---:|---:|
| lda_without_ECG | False | 0.0163 | 0.0222 | 0.0250 |
| lda_without_EMG | False | -0.0148 | -0.0111 | 0.0056 |
| lda_without_EDA | False | 0.0089 | 0.0111 | 0.0167 |
| lda_without_Temp | True | 0.0178 | 0.1000 | 0.0417 |
| lda_without_Resp | False | -0.0459 | 0.0111 | 0.0028 |
| lda_without_ACC | False | 0.0296 | 0.0667 | 0.0222 |

### Alternative classifiers

| Arm | Supported | Overall accuracy Δ | S2/S4 accuracy Δ | S2/S4 coverage | S2/S4 full-set Δ |
|---|---|---:|---:|---:|---:|
| diagonal_qda_raw_all | False | -0.0904 | 0.1000 | 0.9889 | 0.2222 |
| distance_weighted_knn15_raw_all | False | -0.0489 | -0.0111 | 0.9333 | 0.3778 |

## Limitations

- The k=18 to k=19 transition is only one order-statistic boundary with at most 20 onboarding examples.
- S2 and S4 remain post-selected exploratory cases.
- Sensor-family ablation diagnoses predictive interference, not physical sensor malfunction.
- The nonlinear models use fixed untuned NumPy implementations and are not exhaustive.
- One dataset and one recording session per subject limit external validity.

## Reproducibility

- Exact Experiment 10 k=9/k=12 rows checked: 90
- Raw WESAD pickle loading: no
- API/model call: no
- Independent exact replay: pending
