# Meno-J Experiment 6: P4-F1 Score and Conditioning Comparison Across Sample Sizes

## Experiment purpose

Isolate which score and conditioning strategy fails under each geometry and whether larger calibration samples repair the failure.

## Roadmap source: Experiment 4 / P4-F1

- Priority: 4.25
- Difficulty: LOW

## Connection to Experiment 5 / P4-F2

Experiment 5 / P4-F2 falsified the broad finite-sample-only explanation.

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

## Conditioning strategies

- `marginal`
- `mondrian_class`
- `mondrian_region`

## Calibration sizes and seeds

- Calibration sizes: 50, 100, 300, 600
- Seeds: 0, 1, 2, 3, 4

## Main aggregate table

| n_calib | Coverage | Coverage gap | Minimum group coverage | Set size | Undercoverage rate |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.8886 | 0.2119 | 0.7288 | 1.7402 | 0.4133 |
| 100 | 0.8752 | 0.2343 | 0.6968 | 1.6464 | 0.4622 |
| 300 | 0.8741 | 0.2212 | 0.6948 | 1.6068 | 0.5031 |
| 600 | 0.8732 | 0.2222 | 0.6915 | 1.5982 | 0.5093 |

## Robustness ranking

| Type | Rank | Entity | Persistent failures | Gap at n=600 | Min group coverage | Set size |
|---|---:|---|---:|---:|---:|---:|
| score | 1 | `distance_to_class_centroid_score` | 3 | 0.1218 | 0.7911 | 2.2311 |
| score | 2 | `margin_score` | 6 | 0.2698 | 0.6454 | 1.2910 |
| score | 3 | `inverse_probability_score` | 6 | 0.2751 | 0.6382 | 1.2725 |
| conditioning_strategy | 1 | `mondrian_region` | 2 | 0.0903 | 0.8370 | 1.6753 |
| conditioning_strategy | 2 | `mondrian_class` | 5 | 0.2397 | 0.6701 | 1.6000 |
| conditioning_strategy | 3 | `marginal` | 8 | 0.3368 | 0.5676 | 1.5193 |
| score_conditioning_pair | 1 | `distance_to_class_centroid_score + mondrian_region` | 0 | 0.0645 | 0.8656 | 2.2095 |
| score_conditioning_pair | 2 | `margin_score + mondrian_region` | 1 | 0.1015 | 0.8256 | 1.4145 |
| score_conditioning_pair | 3 | `inverse_probability_score + mondrian_region` | 1 | 0.1048 | 0.8198 | 1.4019 |
| score_conditioning_pair | 4 | `distance_to_class_centroid_score + mondrian_class` | 1 | 0.1256 | 0.7798 | 2.2924 |
| score_conditioning_pair | 5 | `distance_to_class_centroid_score + marginal` | 2 | 0.1754 | 0.7278 | 2.1915 |
| score_conditioning_pair | 6 | `margin_score + mondrian_class` | 2 | 0.2939 | 0.6196 | 1.2685 |
| score_conditioning_pair | 7 | `inverse_probability_score + mondrian_class` | 2 | 0.2996 | 0.6109 | 1.2390 |
| score_conditioning_pair | 8 | `margin_score + marginal` | 3 | 0.4141 | 0.4910 | 1.1900 |
| score_conditioning_pair | 9 | `inverse_probability_score + marginal` | 3 | 0.4209 | 0.4838 | 1.1765 |
| geometry | 1 | `overlapping_gaussian_clusters` | 0 | 0.0317 | 0.8761 | 2.2694 |
| geometry | 2 | `well_separated_gaussian_clusters` | 0 | 0.0456 | 0.8683 | 1.1937 |
| geometry | 3 | `covariate_shifted_test_geometry` | 4 | 0.3341 | 0.5993 | 1.6425 |
| geometry | 4 | `imbalanced_class_geometry` | 5 | 0.2584 | 0.6533 | 1.3981 |
| geometry | 5 | `sparse_subgroup_geometry` | 6 | 0.4414 | 0.4607 | 1.4873 |

## Persistent failure cases

- `imbalanced_class_geometry / margin_score / marginal`: gap=0.6117, min coverage=0.2883, set size=0.9201.
- `imbalanced_class_geometry / margin_score / mondrian_region`: gap=0.2519, min coverage=0.6481, set size=0.9809.
- `imbalanced_class_geometry / inverse_probability_score / marginal`: gap=0.6102, min coverage=0.2898, set size=0.9220.
- `imbalanced_class_geometry / inverse_probability_score / mondrian_region`: gap=0.2522, min coverage=0.6478, set size=0.9788.
- `imbalanced_class_geometry / distance_to_class_centroid_score / marginal`: gap=0.2983, min coverage=0.6017, set size=1.9486.
- `sparse_subgroup_geometry / margin_score / marginal`: gap=0.7550, min coverage=0.1450, set size=1.0720.
- `sparse_subgroup_geometry / margin_score / mondrian_class`: gap=0.7294, min coverage=0.1706, set size=1.0975.
- `sparse_subgroup_geometry / inverse_probability_score / marginal`: gap=0.7591, min coverage=0.1409, set size=1.0752.
- `sparse_subgroup_geometry / inverse_probability_score / mondrian_class`: gap=0.7432, min coverage=0.1568, set size=1.1027.
- `sparse_subgroup_geometry / distance_to_class_centroid_score / marginal`: gap=0.4087, min coverage=0.4913, set size=2.3630.
- `sparse_subgroup_geometry / distance_to_class_centroid_score / mondrian_class`: gap=0.3949, min coverage=0.5051, set size=2.3628.
- `covariate_shifted_test_geometry / margin_score / marginal`: gap=0.6227, min coverage=0.2773, set size=0.9289.
- `covariate_shifted_test_geometry / margin_score / mondrian_class`: gap=0.6162, min coverage=0.2838, set size=0.9495.
- `covariate_shifted_test_geometry / inverse_probability_score / marginal`: gap=0.6370, min coverage=0.2630, set size=0.9051.
- `covariate_shifted_test_geometry / inverse_probability_score / mondrian_class`: gap=0.6295, min coverage=0.2705, set size=0.9333.

## Coverage-gap trends

- n=50: mean gap 0.2119
- n=100: mean gap 0.2343
- n=300: mean gap 0.2212
- n=600: mean gap 0.2222

## Average set-size trends

- n=50: mean set size 1.7402
- n=100: mean set size 1.6464
- n=300: mean set size 1.6068
- n=600: mean set size 1.5982

## Most robust score

distance_to_class_centroid_score

## Most robust conditioning strategy

mondrian_region

## Most dangerous score-conditioning pair

inverse_probability_score + marginal

## Safest score-conditioning pair

distance_to_class_centroid_score + mondrian_region

## Calibration-size effect

Increasing n_calib resolved 0 of 13 cells that met the failure threshold at n=50; 15 cells still failed at n=600. Mean gap changed from 0.2119 to 0.2222.

## Final P4 follow-up assessment

**STRUCTURAL_FAILURE_CONFIRMED** — 15 of 45 score-conditioning-geometry cells retained a gap above 0.15 or minimum group coverage below 0.75 at n_calib=600.

- Strongest structural failure: sparse_subgroup_geometry / inverse_probability_score / marginal: n=600 mean gap 0.7591, minimum group coverage 0.1409.
- Strongest size effect: overlapping_gaussian_clusters / margin_score / mondrian_class: gap fell from 0.1128 to 0.0286 (reduction 0.0842).

## Limitations

- The classifier is regularized LDA rather than a deep wearable stress detector.
- Region labels are generator-defined and observable, not estimated from noisy embeddings.
- An unseen test region receives an infinite threshold, guaranteeing conservative but potentially uninformative sets.
- Five seeds quantify common Monte Carlo variation but not extremely rare tails.
- Synthetic Gaussian geometry does not reproduce all temporal and sensor-quality effects in wearable data.

## Next recommended experiment

Apply the safest and most dangerous score-conditioning pairs to a real multi-subject wearable benchmark with subject, activity, sensor-quality, and time-segment metadata.
