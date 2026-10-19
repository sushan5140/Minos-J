# Meno-J Experiment 13: Independent Wearable-Dataset Replication

## Result

**EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED**

## Independent-cohort comparison

| Arm | Accuracy | Coverage | Worst subject | Mean set size | Full sets | Robustness loss |
|---|---:|---:|---:|---:|---:|---:|
| lda_raw | 0.5751 | 0.8946 | 0.7292 | 1.6856 | 0.6856 | 0.2703 |
| lda_subject_robust_normalized | 0.6187 | 0.8681 | 0.7083 | 1.5947 | 0.5947 | 0.2329 |

## Frozen effect deltas

- Accuracy change: 0.0436
- Full-set-frequency reduction: 0.0909
- Robustness-loss reduction: 0.0374
- Coverage change: -0.0265
- Worst-subject coverage change: -0.0208
- V1/V2 accuracy changes: {'V1': 0.014705882352941124, 'V2': 0.07421875}
- Subjects with nonnegative accuracy change: 0.6364
- Paired-subject accuracy bootstrap 95% interval: [-0.004419191919191892, 0.08903093434343415]

## Preregistered checks

- accuracy_improvement_at_least_0_08: **False**
- full_set_reduction_at_least_0_05: **True**
- robustness_loss_reduction_at_least_0_02: **True**
- normalized_mean_coverage_at_least_0_88: **False**
- worst_subject_coverage_change_at_least_minus_0_10: **True**
- accuracy_change_positive_in_both_protocol_versions: **True**
- subject_nonnegative_accuracy_fraction_at_least_0_60: **True**

## Design and integrity

- Subjects: 33 ({'V1': 17, 'V2': 16})
- Fold results: 198
- Archive SHA-256: `afbff3e8e7230bdc765d0ccfc5c3460964021cdfefa8e351f8ad8f78a1b27c48`
- ZIP CRC, safe extraction, subject inventory, and source hashes: PASS
- Raw data mutation: no
- API/model call: no

## Limitations

- This is an independent cohort and device protocol, but not a multi-day repeated-session stress study.
- Fifteen-second windows differ from the 60-second WESAD windows because the external protocol contains 26-to-37-second social-stress tasks.
- Protocol version is a prespecified cohort-stratification variable.
- No hyperparameter search, feature selection, subject exclusion, or decision-rule change is allowed after outcomes are computed.
- No literature novelty claim is made.

## Reproducibility

- Independent exact replay: pending
