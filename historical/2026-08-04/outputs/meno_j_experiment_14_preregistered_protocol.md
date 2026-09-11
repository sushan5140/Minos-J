# Meno-J Experiment 14 — Frozen Protocol

Status: **FROZEN BEFORE EXPERIMENT 14 OUTCOME COMPUTATION**

## Question

Can class-Mondrian calibration preserve normalization's reduction in ambiguity while repairing its non-stress undercoverage on the independent wearable cohort?

## Fixed design

Experiment 14 reuses the validated Experiment 13 cohort, feature checkpoints, subject-disjoint folds, held-out onboarding windows, test windows, classifier, score, and alpha without alteration. The only experimental change is whether conformal thresholds are pooled or estimated separately for each true calibration class.

The four arms are raw/marginal, normalized/marginal, raw/class-Mondrian, and normalized/class-Mondrian. There are 33 subjects, three repetitions, and four arms, producing exactly 396 fold rows. Marginal calibration uses 256 scores and rank 232. Each class-Mondrian threshold uses 128 scores and rank 117.

## Primary candidate and frozen PASS rule

The primary candidate is normalized/class-Mondrian. It passes only if all conditions hold:

- mean coverage is at least 0.88;
- both stress and non-stress coverage are at least 0.88;
- the absolute class-coverage gap is at most 0.05;
- worst-subject coverage changes by no less than -0.05 versus normalized/marginal;
- full-set frequency is at least 0.05 lower than raw/marginal;
- coverage change versus normalized/marginal is nonnegative in both protocol versions;
- at least 60% of subjects have nonnegative coverage change versus normalized/marginal;
- empty-set frequency is at most 0.01.

Passing only aggregate or class-level checks is not enough to claim subject-level repair. No threshold, subgroup, representation, or decision rule may be tuned after viewing the outcomes.
