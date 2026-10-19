# Meno-J Experiment 12 — Preregistered Protocol

Status: **FROZEN BEFORE OUTCOME ANALYSIS**  
Date: 2026-08-09

## Question

Do the Experiment 11 representation and calibration-boundary effects persist under temporal-block holdout, and is temperature-feature interference independent of subject baseline normalization?

## Design

- Reuse all 15 validated Experiment 9 feature checkpoints and Experiment 10 subject rotations.
- Hold out every early, middle, or late within-state temporal-tertile window in turn.
- Use only the other two tertiles for personal calibration and held-out-subject normalization.
- Run three deterministic nested calibration draws at k = 9, 18, 19, and 20.
- Cross those counts with raw/all-feature, raw/no-temperature, normalized/all-feature, and normalized/no-temperature LDA.
- Produce exactly 2,160 result rows.
- Never use a temporal test window for calibration or normalization.

## Frozen decisions

Subject normalization receives general support only if it improves accuracy by at least 0.10 and reduces full-label sets by at least 0.05, retains at least 0.88 mean coverage, does not reduce worst-subject coverage by more than 0.10, and improves accuracy by at least 0.05 in every temporal holdout.

For each representation, the k=18 to k=19 boundary is safe only if full-label sets decrease by at least 0.03 overall and in every temporal holdout, k=19 mean coverage remains at least 0.88, and worst subject-phase coverage falls by no more than 0.05.

Temperature interference is independent of baseline normalization only if the frozen S2/S4 removal rule passes both before and after normalization. It is baseline-mediated if the raw rule passes, the normalized rule fails, and the removal benefit shrinks by at least 0.05 after normalization.

The readiness-surface theory receives support only if normalization passes and the calibration-boundary behavior differs materially between raw and normalized representations.

S4 and S2 are declared confirmatory targets before these outcomes. This remains same-session temporal replication, not independent-dataset validation and not a literature-novelty claim.
