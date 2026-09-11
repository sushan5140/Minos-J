# Meno-J Experiment 12: Temporal Readiness-Surface Replication

## Result

**NORMALIZATION_REPLICATED_WITHOUT_SURFACE_INTERACTION**

## Representation × calibration grid

| Arm | k | Accuracy | Coverage | Worst subject | Worst subject-phase | Full sets | Robustness loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| lda_raw_all | 9 | 0.6582 | 0.9020 | 0.8252 | 0.6364 | 0.1982 | 0.1419 |
| lda_raw_all | 18 | 0.6582 | 0.9483 | 0.8535 | 0.7273 | 0.2675 | 0.1453 |
| lda_raw_all | 19 | 0.6582 | 0.8986 | 0.8535 | 0.6364 | 0.1909 | 0.1318 |
| lda_raw_all | 20 | 0.6582 | 0.9051 | 0.8535 | 0.6364 | 0.1927 | 0.1277 |
| lda_raw_without_Temp | 9 | 0.6797 | 0.9047 | 0.8322 | 0.6364 | 0.1895 | 0.1380 |
| lda_raw_without_Temp | 18 | 0.6797 | 0.9493 | 0.8897 | 0.6970 | 0.2702 | 0.1476 |
| lda_raw_without_Temp | 19 | 0.6797 | 0.8946 | 0.8215 | 0.5758 | 0.1711 | 0.1254 |
| lda_raw_without_Temp | 20 | 0.6797 | 0.8998 | 0.8215 | 0.5758 | 0.1742 | 0.1216 |
| lda_subject_robust_normalized_all | 9 | 0.8333 | 0.9359 | 0.8011 | 0.5455 | 0.0885 | 0.1157 |
| lda_subject_robust_normalized_all | 18 | 0.8333 | 0.9526 | 0.8314 | 0.6154 | 0.1322 | 0.1210 |
| lda_subject_robust_normalized_all | 19 | 0.8333 | 0.9038 | 0.8057 | 0.4545 | 0.0668 | 0.1134 |
| lda_subject_robust_normalized_all | 20 | 0.8333 | 0.9051 | 0.8057 | 0.4545 | 0.0668 | 0.1121 |
| lda_subject_robust_normalized_without_Temp | 9 | 0.8039 | 0.9343 | 0.8197 | 0.5758 | 0.1108 | 0.1181 |
| lda_subject_robust_normalized_without_Temp | 18 | 0.8039 | 0.9608 | 0.8772 | 0.6923 | 0.1532 | 0.1228 |
| lda_subject_robust_normalized_without_Temp | 19 | 0.8039 | 0.9053 | 0.8208 | 0.5455 | 0.0786 | 0.0997 |
| lda_subject_robust_normalized_without_Temp | 20 | 0.8039 | 0.9087 | 0.8208 | 0.5455 | 0.0833 | 0.0992 |

## Subject normalization

- Supported: **True**
- Accuracy change: 0.1751
- Full-set-frequency reduction: 0.1237
- Coverage change: 0.0109
- Normalized mean coverage: 0.9244
- Worst-subject coverage change: -0.0360
- Phase accuracy changes: {'early': 0.20000000000000018, 'middle': 0.19545454545454544, 'late': 0.1297979797979797}

## Order-statistic boundary

| Arm | Safe | Coverage Δ | Full-set reduction | Worst subject-phase coverage Δ |
|---|---|---:|---:|---:|
| lda_raw_all | False | -0.0496 | 0.0766 | -0.0909 |
| lda_raw_without_Temp | False | -0.0547 | 0.0991 | -0.1212 |
| lda_subject_robust_normalized_all | False | -0.0488 | 0.0654 | -0.1608 |
| lda_subject_robust_normalized_without_Temp | False | -0.0554 | 0.0747 | -0.1469 |

## Rival distinction

- Temperature decision: **TEMP_INTERFERENCE_NOT_REPLICATED**
- Raw temperature-removal rule passed: False
- Normalized temperature-removal rule passed: False
- Readiness surface supported: **False**
- Boundary coverage interaction magnitude: 0.0008
- Boundary full-set interaction magnitude: 0.0111

## Predeclared subject checks

- S4 normalization replication: **True**
- S4 accuracy change: 0.5245
- S4 full-set reduction: 0.5540
- S2 residual failure replicated: **True**
- S2 accuracy change: 0.0396
- S2 full-set change: -0.0006

## Limitations

- This is internal temporal replication within the same WESAD recording session, not independent-dataset replication.
- S2 and S4 are confirmatory targets declared from Experiment 11 before Experiment 12 outcomes.
- Temporal tertiles are relative positions within each labeled state run, not separate visits or days.
- Accuracy, coverage, prediction-set size, and full-set frequency must be interpreted jointly.
- No literature novelty claim will be made.

## Reproducibility

- Result rows: 2160
- Raw WESAD pickle loading: no
- API/model call: no
- Independent exact replay: pending
