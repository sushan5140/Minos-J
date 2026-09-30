# Experiment 18 — sample-size and detectable-effect analysis

**Primary comparison:** A vs C, a paired binary endpoint (correct / incorrect on the same case). **Test:** exact two-sided McNemar at α = 0.05. **Effect we care about:** δ = +10 percentage points.

## Assumptions

- **Discordant-pair rate ψ** = P(A and C disagree on a case) ∈ [0.15, 0.35]. It is unmeasured. Both arms use the same model with similar-length procedures, so moderate agreement is expected. The pilot does not estimate ψ per arm, because it computes no per-arm accuracy.
- Under the alternative, δ = p₁₀ − p₀₁ = 0.10, with p₁₀ + p₀₁ = ψ.
- Cases are exchangeable draws from the frozen generator.
- **Rule-out probability:** the probability that the paired 95% CI upper bound falls below +0.10 when the true δ = 0, using a normal approximation with SE ≈ √(ψ/n).

## Results (exact McNemar power by enumeration)

| n | ψ | Power at δ = +0.10 | CI half-width at δ = 0 | P(rule out +10 pp \| δ = 0) |
|---:|---:|---:|---:|---:|
| 60 | 0.15 / 0.25 / 0.35 | 0.40 / 0.26 / 0.19 | ±0.098 / ±0.127 / ±0.150 | 0.52 / 0.34 / 0.26 |
| 90 | 0.15 / 0.25 / 0.35 | 0.63 / 0.40 / 0.29 | ±0.080 / ±0.103 / ±0.122 | 0.69 / 0.48 / 0.36 |
| 120 | 0.15 / 0.25 / 0.35 | 0.79 / 0.53 / 0.40 | ±0.069 / ±0.089 / ±0.106 | 0.81 / 0.59 / 0.46 |
| **180** | **0.15 / 0.25 / 0.35** | **0.94 / 0.74 / 0.58** | **±0.057 / ±0.073 / ±0.086** | **0.93 / 0.77 / 0.62** |
| 240 | 0.15 / 0.25 / 0.35 | 0.98 / 0.86 / 0.72 | ±0.049 / ±0.063 / ±0.075 | 0.98 / 0.87 / 0.75 |

## Decision

**n = 180**, which replaces the draft's 60.
- **Why 60 was dropped:** most likely it would end inconclusive again. It gives less than a 50% chance of either detecting +10 pp or ruling it out across most plausible ψ.
- **Why 180:** it is the smallest size giving a majority chance of a decisive answer in both directions across the whole ψ range.
- **Cost:** about 1,800 calls, estimated at 9–15 Pro usage windows. That estimate is calibrated on 17-C, where a window allowed roughly 0.9–1.3M tokens.
- **Why not 240:** it is safer statistically, but about 33% more costly, and its gain over 180 is smallest where ψ is low.
- **Balance:** 180 is 6 mechanisms × 30, split 15 decoy / 15 non-decoy per mechanism.

## Secondary comparisons

A vs D, A vs B and the decoy/non-decoy subsets share this n (subsets have n = 90). They carry a Holm correction, so they are **underpowered relative to the primary** and are interpreted as estimates with CIs, not as decisive tests.

The sample size is fixed at the freeze and cannot change in response to any treatment result.
