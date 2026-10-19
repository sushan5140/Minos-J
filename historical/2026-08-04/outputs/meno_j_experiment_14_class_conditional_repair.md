# Meno-J Experiment 14: Class-Conditional Calibration Repair

## Result

**CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED**

## Arm comparison

| Arm | Coverage | Non-stress | Stress | Class gap | Worst subject | Full sets | Empty sets |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw_marginal | 0.8946 | 0.9028 | 0.8864 | 0.0164 | 0.7292 | 0.6856 | 0.0000 |
| normalized_marginal | 0.8681 | 0.8194 | 0.9167 | 0.0972 | 0.7083 | 0.5947 | 0.0000 |
| raw_class_mondrian | 0.8826 | 0.8788 | 0.8864 | 0.0076 | 0.6458 | 0.6503 | 0.0000 |
| normalized_class_mondrian | 0.8769 | 0.8826 | 0.8712 | 0.0114 | 0.6875 | 0.6187 | 0.0000 |

## Frozen primary checks

- mean_coverage_at_least_0_88: **False**
- each_class_coverage_at_least_0_88: **False**
- class_coverage_gap_at_most_0_05: **True**
- worst_subject_coverage_change_vs_normalized_marginal_at_least_minus_0_05: **True**
- full_set_frequency_reduction_vs_raw_marginal_at_least_0_05: **True**
- coverage_change_vs_normalized_marginal_nonnegative_in_both_protocol_versions: **True**
- subject_nonnegative_coverage_change_fraction_vs_normalized_marginal_at_least_0_60: **True**
- empty_set_frequency_at_most_0_01: **True**

## Primary candidate deltas

- Coverage change versus normalized/marginal: 0.0088
- Class coverage changes: {'non_stress': 0.06313131313131315, 'stress': -0.045454545454545414}
- Worst-subject coverage change: -0.0208
- Full-set reduction versus raw/marginal: 0.0669
- Protocol-version coverage changes: {'V1': 0.015931372549019662, 'V2': 0.0013020833333333703}
- Subject nonnegative coverage-change fraction: 0.7576
- Paired-subject bootstrap 95% interval: [-0.0037878787878787845, 0.021464646464646478]

## Integrity

- Fold rows: 396
- Exact Experiment 13 marginal-arm continuity: PASS
- Only the conformal conditioning rule changed
- API/model call: no
- Raw-data mutation: no
- Independent exact replay: pending
