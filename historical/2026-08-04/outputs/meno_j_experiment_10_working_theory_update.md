# Meno-J Experiment 10 — Working-Theory Update

## Validated outcome

The preregistered cohort-level personal-calibration rule passed. Moving from four external calibration subjects to 12 labeled personal windows increased mean coverage by 0.0874 and worst-subject coverage by 0.2667. The paired subject-bootstrap 95% interval for the mean change was `[0.0237, 0.1615]`, while mean full-set frequency increased by 0.0741.

## What did not survive

### Informative S2/S4 repair

S2 coverage rose from 0.6444 to 1.0000, but its full-set frequency rose by 0.3556. S4 coverage rose from 0.6444 to 0.9333, but its full-set frequency rose by 0.4222. Their base-classifier accuracies were only 0.5556 and 0.3778.

Personal calibration therefore made the uncertainty layer more honest, but did not make the underlying classifier reliably discriminative for these subjects. The preregistered S2/S4 informative-repair rule did not pass.

### Simple calibration compatibility

Selecting the two nearest external calibration subjects by standardized unlabeled feature-centroid distance did not pass the preregistered rule. Nearest-subject calibration reduced robustness loss by only 0.0133 versus the required 0.03, and its mean coverage was 0.8222 versus 0.8859 for the farthest-subject negative control. The distance/loss correlation of 0.356 suggests a weak relationship, but the simple selection rule traded coverage for smaller sets.

## The new working concept

**Calibration readiness is a frontier, not a switch.**

At 90% target coverage:

- 3 and 6 personal examples could not support a finite threshold and returned the full label set every time.
- 9 examples produced finite thresholds, 0.9467 mean coverage, and 0.2281 full-set frequency.
- 12 examples produced 0.9659 mean coverage, but full-set frequency increased to 0.2830.

The first finite threshold is therefore not the same as an informative or stable personalized threshold. Between 9 and 18 examples, the conformal quantile remains an extreme order statistic at `alpha = 0.1`; more examples can increase the observed maximum score and make sets more conservative.

This yields a revised J-jump candidate:

> A subject moves through distinct calibration-readiness stages: no finite threshold, finite but extreme threshold, informative threshold, and stable personalized threshold.

This is a testable working concept, not yet a literature-novelty claim.

## Next falsification target

Extend the onboarding curve through the order-statistic transition beyond 18 personal examples. Test whether prediction sets become more informative without retraining the classifier. In parallel, test representation and sensor-quality interventions for S2/S4 because calibration alone cannot repair their low classifier accuracy.

Independent exact replay: **PASS**.
