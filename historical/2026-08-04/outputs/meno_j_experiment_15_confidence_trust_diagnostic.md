# Meno-J Experiment 15: Confidence–Trust Subject-Shift Diagnostic

## Result

**CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_NOT_SUPPORTED**

This experiment is a diagnostic, not a repair or deployment gate.

## Frozen primary checks

- primary_high_risk_observation_count_at_least_100: **True**
- primary_high_risk_miscoverage_minus_all_other_at_least_0_10: **True**
- primary_high_risk_miscoverage_minus_high_confidence_high_trust_at_least_0_10: **False**
- primary_high_risk_coverage_below_0_85: **True**
- gap_vs_all_other_positive_in_both_protocol_versions: **True**
- gap_vs_all_other_positive_in_all_three_repetitions: **True**

## Arm results

| Arm | Overall coverage | High-conf/low-trust n | High-conf/low-trust coverage | Miscoverage gap vs rest | Gap vs high-conf/high-trust |
|---|---:|---:|---:|---:|---:|
| raw_marginal | 0.8946 | 388 | 0.7938 | 0.1334 | -0.0015 |
| normalized_class_mondrian | 0.8769 | 433 | 0.7852 | 0.1262 | 0.0100 |

## Primary-arm stability

- Protocol-version gaps versus all other quadrants: {'V1': 0.06923348086639769, 'V2': 0.1785466785466786}
- Repetition gaps versus all other quadrants: {'0': 0.14236111111111116, '1': 0.11086226203807392, '2': 0.12653312673847694}
- Covered versus miscovered diagnostics: {'covered': {'count': 1389, 'coverage': 1.0, 'miscoverage': 0.0, 'mean_confidence': 0.6195208187823862, 'mean_trust': 1.0594907511751834}, 'miscovered': {'count': 195, 'coverage': 0.0, 'miscoverage': 1.0, 'mean_confidence': 0.7255101751112035, 'mean_trust': 1.04612752264255}}

## Interpretation boundary

- A positive result supports a specific classifier-manifold mismatch proxy; it does not prove causality or individual coverage.
- A negative result blocks a confidence–trust gate and redirects the falsification engine to protocol/stressor posterior shift or temporal dependence.
- No thresholds were tuned on heldout outcomes.

## Integrity

- Fold rows: 198
- Observation rows: 3168
- Exact Experiment 14 outcome continuity: PASS
- API/model call: no
- Independent exact replay: pending
