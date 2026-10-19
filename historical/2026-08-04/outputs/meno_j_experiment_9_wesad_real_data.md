# Meno-J Experiment 9: WESAD Real-Data Falsification Study

## Result

**SYNTHETIC_SAFEST_PAIR_DOES_NOT_TRANSFER**

- Subjects: 15
- Transition-free 60-second windows: 535
- Class counts: {'baseline': 285, 'stress': 160, 'amusement': 90}
- Subject-disjoint score/conditioning folds: 405

## Primary transfer comparison

| Pair | Mean coverage | Worst-subject coverage | Set size | Full-set frequency |
|---|---:|---:|---:|---:|
| distance_to_class_centroid_score + mondrian_motion_region | 0.8373 | 0.3429 | 2.4364 | 0.7577 |
| inverse_probability_score + marginal | 0.8671 | 0.6000 | 1.7666 | 0.1985 |

- Worst-subject coverage improvement: -0.2571
- Full-set frequency increase: 0.5592
- Paired mean subject coverage difference: -0.0298
- Subject-bootstrap 95% interval: [-0.1060, 0.0565]

## Robustness ranking

| Rank | Score | Conditioning | Mean coverage | Worst subject | Set size | Full sets |
|---:|---|---|---:|---:|---:|---:|
| 1 | inverse_probability_score | marginal | 0.8671 | 0.6000 | 1.7666 | 0.1985 |
| 2 | inverse_probability_score | mondrian_motion_region | 0.8646 | 0.5946 | 1.7666 | 0.2036 |
| 3 | margin_score | mondrian_motion_region | 0.8681 | 0.5676 | 1.8344 | 0.3695 |
| 4 | inverse_probability_score | mondrian_class | 0.8057 | 0.5429 | 1.7232 | 0.1061 |
| 5 | margin_score | marginal | 0.8714 | 0.5225 | 1.8307 | 0.3614 |
| 6 | margin_score | mondrian_class | 0.8079 | 0.5045 | 1.7683 | 0.1547 |
| 7 | distance_to_class_centroid_score | mondrian_class | 0.8250 | 0.3714 | 2.2875 | 0.6265 |
| 8 | distance_to_class_centroid_score | mondrian_motion_region | 0.8373 | 0.3429 | 2.4364 | 0.7577 |
| 9 | distance_to_class_centroid_score | marginal | 0.8188 | 0.3048 | 2.4155 | 0.7604 |

## Structural diagnostics

- Method spread in worst-subject coverage: 0.2952
- Score/conditioning sensitivity observed: True
- Best-pair subject coverage range: 0.4000
- Subject heterogeneity observed: True
- Best-pair mean motion-region coverage gap: 0.1149
- Best-pair mean temporal-tertile coverage gap: 0.0908

## Interpretation guardrail

These are real-data coverage associations under the frozen protocol. They test whether synthetic score/conditioning rankings transfer; they do not by themselves establish a causal physiological mechanism.

## Limitations

- The analysis uses hand-engineered distribution/dynamics features and regularized LDA, not a deep stress detector.
- Only chest signals are used in the primary synchronized analysis; wrist modalities require separate sampling-rate alignment.
- Fifteen subjects limit precision for subject-level tail-risk estimates.
- Motion regions are defined by a calibration-only median split and are not clinical or demographic subgroups.
- Observed coverage associations do not establish a causal physiological mechanism.

## Reproducibility

- Archive SHA-256: `5e15d2606adf16d819ba535c1786d92e94bae5ff5392f7ae01fb63f9938fd71c`
- Restricted pickle loader: yes
- Subject-disjoint splits: yes
- Model/API call: no
- Raw dataset modified: no
