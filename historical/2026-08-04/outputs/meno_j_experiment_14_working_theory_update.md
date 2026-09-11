# Meno-J Experiment 14 — Working Theory Update

## Decision

**CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED**

Class conditioning diagnosed a real part of the problem but did not produce a complete repair.

Normalized marginal calibration had a large class-coverage gap of 0.0972. Class-Mondrian calibration reduced that gap to 0.0114 and raised overall coverage from 0.8681 to 0.8769. However, the frozen rule required overall and both class coverages to reach 0.88. Stress coverage remained 0.8712, worst-subject coverage fell to 0.6875, and the subject-level bootstrap interval for the coverage change included zero.

## Updated theory

The pooled threshold contributed to class imbalance, but it was not the entire external safety failure. Class conditioning mostly exchanged coverage between the two classes: non-stress improved by 0.0631 while stress fell by 0.0455. It also increased full-set frequency by 0.0240 relative to normalized marginal calibration.

The remaining failure is therefore more consistent with subject-level distribution shift or reliability differences than with class pooling alone.

## Relation to the J-jump

This is a useful Meno-J outcome. The system detected a concrete contradiction, proposed the smallest plausible intervention, and discovered that the mechanism was real but insufficient. A J-jump must survive the full contract; explaining one structural pattern does not justify promoting an incomplete repair.

## Next falsification target

Freeze a subject-level reliability-gate study using only unlabeled onboarding diagnostics. Test whether train-to-subject shift, within-subject dispersion, sensor stability, and protocol version can safely select raw versus normalized representation without seeing test labels.

Independent exact replay: **PASS**.
