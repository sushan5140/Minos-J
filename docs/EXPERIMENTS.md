# Minos-J Experiment Record

This document summarizes the currently recovered and verified experiment record for the Minos-J research project.

The purpose of this file is to keep headline results separate from the project landing page and to make it clear which conclusions came from which experimental stage.

---

## Experiment 4 — competing-pattern construction

### Objective

Convert surviving explanations into a smaller set of genuinely competing patterns and design experiments that distinguish between them.

### Output

- 9 surviving explanations
- 5 competing patterns
- 10 distinguishing experiments
- 8 validated primary sources

### Methodological requirement

Every proposed experiment had to contain:

- a testable prediction
- an expected effect size
- rationale for that expected effect
- minimum evidence / sample requirement
- an explicit failure condition
- a statistical or executable test plan

The purpose was to prevent "critique" from remaining rhetorical. A hypothesis had to specify what observation would count against it.

---

## Experiment 5 — P4-F2

### Hypothesis under test

The observed subgroup failure was primarily a finite-sample effect and should substantially disappear as sample size increased.

### Result

**Falsified.**

At `n = 300`, the sparse-subgroup + inverse-probability + marginal configuration still produced:

| Metric | Result |
|---|---:|
| Coverage gap | 0.7462 |
| Minimum group coverage | 0.1538 |
| Persistent-failure cells | 14 |

### Interpretation

The failure remained too large to support a finite-sample-only explanation.

This does not prove a single alternative explanation by itself; it removes one explanation from the surviving set and motivates structural tests.

---

## Experiment 6 — P4-F1

### Objective

Test whether the failure depends on the estimator / conditioning structure rather than only sample scarcity.

### Safest tested pairing

| Metric | Result |
|---|---:|
| Mean gap | 0.0645 |
| Minimum coverage | 0.8656 |
| Persistent failures | 0 |

### Most dangerous tested pairing

**Inverse-probability + marginal**

| Metric | Result |
|---|---:|
| Mean gap | 0.4209 |
| Minimum coverage | 0.4838 |

Across the tested grid, 15 of 45 cells exhibited persistent failures.

### Interpretation

**Structural failure pattern confirmed.**

Different estimator / conditioning pairings changed failure severity substantially, supporting a structural rather than purely finite-sample interpretation.

---

## Experiment 7 v4

### Q1

- 9 PASS
- 1 SALVAGEABLE

### Q2

- 10 PASS

### Q3

Execution preserved valid completed checkpoints, but a later stage was blocked by sandbox outbound-network restrictions before the required external API request could be made.

No fabricated completion result is reported for the blocked stage.

### Intended testability-object schema

The next stage was designed to produce exactly 10 testability objects, each containing:

1. effect-size expectation
2. effect-size rationale
3. minimum-data requirement
4. testable prediction
5. failure condition
6. statistical-test plan

---

## Reproducibility / refactor verification

During architecture refactoring:

- 34 historical outputs remained byte-identical
- manifest and hash checks were used
- compilation checks passed
- credential scanning was performed
- historical experiment outputs were not silently regenerated

This separation matters because a refactor should not be allowed to rewrite the evidence it is later evaluated against.

---

## How to read these results

These experiments are evidence about the **specific tested setups**.

They should not be read as:

- a universal proof that all self-critique systems fail
- a universal proof that Minos-J improves all reasoning
- a claim that extra reasoning stages automatically create trustworthy AI

The project is intentionally structured so that explanations can be rejected and architectural claims remain conditional on controlled evaluation.
