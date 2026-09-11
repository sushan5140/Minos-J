# Meno-J Experiment 12 — Working-Theory Update

## Decision

**NORMALIZATION_REPLICATED_WITHOUT_SURFACE_INTERACTION**

The strongest Experiment 11 finding survived temporal-block holdout: subject baseline normalization materially improves the representation. The proposed interaction between representation and the conformal order-statistic boundary did not survive, and the temperature-ablation mechanism did not replicate.

## What replicated

Per-subject robust normalization increased accuracy by 0.1751, reduced full-label-set frequency by 0.1237, and slightly increased mean coverage to 0.9244. Accuracy improved in every held-out temporal tertile: 0.2000 early, 0.1955 middle, and 0.1298 late. Worst-subject mean coverage decreased by only 0.0360, inside the frozen safety bound.

S4's repair also replicated across time. Its accuracy increased by 0.5245, full-label sets fell by 0.5540, and normalized coverage was 0.9112. Accuracy improved in every temporal holdout, including 0.8462 in early windows and 0.3636 in both middle and late windows.

S2 did not follow S4. Its accuracy improved by only 0.0396 and normalized coverage remained 0.8110. S2 is therefore a residual mechanism problem, not evidence that normalization failed generally.

## What was falsified or weakened

The k=18-to-k=19 transition was unsafe under all four representations. Raw/all-feature coverage fell by 0.0496 and worst subject-phase coverage fell by 0.0909. Normalized/all-feature coverage fell by 0.0488 and worst subject-phase coverage fell by 0.1608. Full-label sets became less common, but the improvement in informativeness did not protect the tail.

The preregistered readiness-surface interaction was not supported. Raw and normalized representations agreed that the boundary was unsafe. Their boundary coverage changes differed by only 0.0008 and their full-set reductions by only 0.0111.

Temperature-feature interference did not replicate. Removing temperature missed the raw S2/S4 accuracy threshold, worsened their robustness loss, and reduced S2/S4 accuracy after normalization. The Experiment 11 temperature result should remain exploratory and should not be part of the core theory.

## Revised J-jump candidate

The narrower working concept is a **two-gate subject readiness model**:

1. a representation gate: remove stable subject baseline distortion so physiological states become discriminable;
2. a calibration gate: obtain an informative conformal threshold without sacrificing subject-phase coverage.

The two constraints both matter, but Experiment 12 did not show their proposed interaction. Passing the representation gate did not make the order-statistic boundary safe, and no universal calibration count created readiness.

## Next decisive test

The normalization gate now needs independent-session or independent-dataset testing. Separately, S2-like residual failures should be challenged with predeclared class-conditional geometry, label-transition, and signal-quality rivals. This is the cleanest way to distinguish a general baseline correction from subject-specific state ambiguity.

## Guardrails

- This is same-session temporal replication, not external validation.
- Temporal tertiles are not separate visits or days.
- S4 is now a predeclared confirmatory target, but still comes from WESAD.
- Temperature interference is removed from the core theory.
- No literature novelty claim is made.

Independent exact replay: **PASS**.
