# Meno-J Experiment 5: P4-F2 Synthetic Feature-Geometry Stress Test

## Experiment purpose

Test whether methodological sensitivity to nonconformity score and conditioning strategy is primarily finite-sample instability or persists under controlled feature geometry.

## Roadmap source: Experiment 4 / P4-F2

- Priority: 4.40
- Difficulty: LOW
- Competing explanation: Apparent score/conditioning sensitivity is a finite-sample bias–variance effect.

## Simulation conditions

- `well_separated_gaussian_clusters`
- `overlapping_gaussian_clusters`
- `imbalanced_class_geometry`
- `sparse_subgroup_geometry`
- `covariate_shifted_test_geometry`

## Nonconformity scores

- `margin_score`
- `inverse_probability_score`
- `distance_to_class_centroid_score`

## Calibration sizes and seeds

- Calibration sizes: 50, 100, 300
- Seeds: 0, 1, 2, 3, 4
- Conditioning: marginal, mondrian_class

## Main results table

| n_calib | Mean marginal coverage | Mean coverage gap | Mean set size | Mean undercoverage rate |
|---:|---:|---:|---:|---:|
| 50 | 0.8783 | 0.2603 | 1.7563 | 0.4453 |
| 100 | 0.8626 | 0.2883 | 1.6350 | 0.5147 |
| 300 | 0.8597 | 0.2894 | 1.5684 | 0.5453 |

## Coverage-gap trends

- Relative mean gap reduction from n=50 to n=300: -11.2%
- Relative score/conditioning sensitivity reduction: 9.7%
- Persistent severe failure cells across all sizes: 14
- Persistent large-n failure cells: 15

## Average set-size trends

- n=50: mean set size 1.7563
- n=100: mean set size 1.6350
- n=300: mean set size 1.5684

## Strongest support case for P4

overlapping_gaussian_clusters / distance_to_class_centroid_score / mondrian_class: mean coverage gap fell from 0.1085 to 0.0329 (absolute reduction 0.0755).

## Strongest failure case against P4

sparse_subgroup_geometry / inverse_probability_score / marginal: mean n=300 coverage gap 0.7462, mean minimum group coverage 0.1538.

## Final survival assessment

**FALSIFIED** — At least one controlled geometry/score/conditioning cell showed severe group undercoverage in at least four of five seeds at every calibration size, so finite-sample variance alone cannot explain the failure.

## Limitations

- The simulation uses a regularized LDA probability model rather than a deep wearable classifier.
- Five seeds characterize Monte Carlo variability but do not exhaust rare-tail behavior.
- The largest calibration size is 300, as preregistered here, rather than the n=10,000 idealization in Experiment 4.
- Label-conditional Mondrian strata are known exactly; estimated latent clusters are not evaluated.

## Next recommended experiment

Run P4-F1 on a real multi-subject wearable dataset, expanding calibration sizes beyond 300 and comparing label strata with estimated geometry-aware clusters.
