# Meno-J Experiment 8: Rare-Subgroup Feasibility Frontier

## Research question

Does region-Mondrian conditioning genuinely repair rare-subgroup undercoverage, or does it appear safe because insufficient subgroup calibration data force full, uninformative prediction sets; and how sensitive is it to metadata error?

## Result

**ORACLE_SAFETY_PARTLY_VACUOUS_AND_METADATA_FRAGILE**

For rare prevalence at or below 2% and calibration size at or below 600, using the previously safest distance score with oracle region conditioning:

- Mean true rare-group coverage: 0.9920
- Mean rare-group prediction-set size: 2.9809 of 3
- Mean rare-group full-set fraction: 0.9901
- Mean fraction of seeds with a finite rare threshold: 0.1042
- Oracle cells meeting both rare coverage >= 0.88 and rare full-set fraction <= 0.20: 0

This separates formal coverage from informative coverage: a full label set covers the truth but does not discriminate among classes.

Secondary diagnostic: No tested distance-score oracle-region cell simultaneously achieved mean true rare coverage >= 0.88 and a mean rare full-set fraction <= 0.20. This diagnostic was summarized after applying the preregistered primary decision rule.

## Exact feasibility boundary

At alpha=0.10, a subgroup needs at least **9 calibration observations** before the finite-sample quantile can be finite.

| Rare prevalence | P(finite threshold) at n=600 | Total n for 95% probability | Total n for 99% probability |
|---:|---:|---:|---:|
| 0.500% | 0.0037 | 2884 | 3476 |
| 1.000% | 0.1517 | 1441 | 1736 |
| 2.000% | 0.8476 | 719 | 866 |
| 5.000% | 1.0000 | 286 | 344 |
| 8.000% | 1.0000 | 178 | 213 |
| 15.000% | 1.0000 | 93 | 112 |
| 30.000% | 1.0000 | 45 | 53 |

## Metadata-noise stress test

The strongest observed metadata-noise penalty occurred at prevalence 0.500%, n=600, using `moderately_noisy_region`:

- Oracle rare coverage: 1.0000
- Noisy-metadata rare coverage: 0.3537
- Coverage penalty: 0.6463
- Oracle rare set size: 3.0000
- Noisy-metadata rare set size: 1.4360

## Marginal baseline

The worst distance-score marginal cell occurred at prevalence 0.500%, n=600: true rare coverage 0.2782, mean rare set size 1.2085.

## Working-theory update

Region-conditioned coverage must be reported jointly with subgroup effective calibration size, finite-threshold probability, full-set frequency, and metadata quality. Coverage alone can mistake abstention-like full sets for successful repair.

The practical evaluation unit is therefore not coverage alone. It is the joint tuple:

```text
(coverage, subgroup effective n, finite-threshold probability, set size, full-set fraction, metadata quality)
```

## Interpretation

Oracle region conditioning remains mathematically valid, but its apparent robustness can be partly vacuous for rare groups. When the calibration group is too small, the conservative infinite threshold returns every label. When subgroup metadata is noisy, common samples can contaminate the rare threshold and rare samples can be routed to the common threshold, recreating undercoverage. This is a boundary condition on the Experiment 6 mitigation, not a contradiction of conformal validity under its assumptions.

## Reproducibility

- No model call was used.
- No API key was required.
- Experiment 6 was reused by SHA-256 checkpoint and was not rerun.
- Seed-level rows: 6720
- Aggregate cells: 336
- UTF-8 was used explicitly for report output.

## Limitations

- This is a controlled Gaussian synthetic study, not evidence that the same prevalence frontier holds numerically in WESAD.
- True and noisy subgroup labels are generated rather than estimated from wearable features.
- The classifier is regularized LDA rather than a deep physiological stress detector.
- The experiment tests two previously validated score families and does not exhaust all conformal scores.
- A full prediction set is valid but operationally uninformative; usefulness depends on an application-specific set-size cost.
