# Meno-J Experiment 13 — Preregistered External-Replication Protocol

Status: **FROZEN AFTER INVENTORY AND BEFORE FEATURE OR OUTCOME COMPUTATION**  
Date: 2026-08-09

## Question

Does per-subject robust normalization improve subject-disjoint wearable stress classification and conformal informativeness in an independently collected Empatica E4 cohort?

## Frozen cohort and labels

The primary cohort contains 33 subjects. S02, f07, f14_a, and f14_b are excluded for author-documented duplication, invalid covered sensors, or a split recording. No exclusion may change after outcome computation.

Protocol baseline and two rest stages are labeled non-stress. Stroop when present, TMCT, real opinion, opposite opinion, and subtraction stages are labeled stress. Self-reported stress remains separate metadata rather than replacing protocol labels.

## Frozen windows and features

Each labeled interval loses five seconds at both edges. Non-overlapping 15-second windows are then generated. Within each class, 16 chronologically ordered, evenly spaced windows are retained per subject. The validated pre-outcome inventory guarantees this count; longer windows do not.

The representation contains 54 features: nine fixed summary statistics from EDA, temperature, ACC X/Y/Z, and ACC magnitude. Acceleration is converted from Empatica units to g. Raw CSV files are never modified.

## Frozen subject-disjoint evaluation

Every subject is held out under three deterministic repetitions. Twenty-four subjects train fixed regularized LDA, eight different subjects calibrate inverse-probability conformal scores, and one subject is tested.

The held-out subject's 32 balanced windows are split into eight onboarding and eight test windows per class. Onboarding labels are ignored and onboarding data are used only to estimate the held-out subject's normalization center and scale. Test windows are evaluation-only.

The two arms are identical except for representation:

- pooled raw features;
- per-subject median centering and IQR scaling.

## Frozen replication decision

External normalization replication passes only if all conditions hold:

- mean accuracy improves by at least 0.08;
- full two-label-set frequency falls by at least 0.05;
- robustness loss falls by at least 0.02;
- normalized mean coverage remains at least 0.88;
- worst-subject coverage falls by no more than 0.10;
- accuracy improves in both protocol versions;
- at least 60% of subjects have nonnegative accuracy change.

This is an independent cohort and wearable protocol, but not a multi-day repeated-session study. No tuning, feature selection, post-outcome exclusions, decision-rule changes, API calls, or novelty claims are permitted.
