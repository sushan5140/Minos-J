# Meno-J Experiment 1: Combined Calibration Report

## Model

`nvidia/nemotron-3-ultra-550b-a55b:free`

## Run comparison

| Run | Generated | PASS | SALVAGEABLE | REJECT | Pass rate | Salvageable rate | Reason diversity | Failure points consistent | Stage 6 ran | Stage 7 ran |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|
| Q1 | 10 | 0 | 2 | 8 | 0.0% | 20.0% | 8 | Yes | No | No |
| Q2 | 10 | 0 | 10 | 0 | 0.0% | 100.0% | 2 | Yes | No | No |
| Q3 | 10 | 0 | 7 | 3 | 0.0% | 70.0% | 3 | Yes | No | No |

## Questions

### Q1

Why does Mondrian conformal prediction show undercoverage for some physiological stress subjects in WESAD?

### Q2

Why might conformal prediction fail to maintain stable coverage across different physiological signal segments?

### Q3

What mechanisms could explain subject-level variation in wearable stress-detection uncertainty?

## Top failed checklist fields

### Q1

- `confounders_identified`: 10
- `effect_size_plausible`: 10
- `data_requirements_clear`: 5
- `mechanism_is_non_generic`: 3
- `variables_measurable`: 3
- `base_rate_plausible`: 2
- `prediction_is_testable`: 2
- `causal_chain_valid`: 1

### Q2

- `confounders_identified`: 10
- `mechanism_is_non_generic`: 9

### Q3

- `confounders_identified`: 10
- `mechanism_is_non_generic`: 3
- `causal_chain_valid`: 1

## Repeated failed checklist fields across all questions

- `confounders_identified`: Q1=10, Q2=10, Q3=10
- `mechanism_is_non_generic`: Q1=3, Q2=9, Q3=3

## Rubber-stamp red flags

- Q1: None
- Q2: None
- Q3: None

## Interpretation

- All three runs have 0 PASS: the Auditor may be over-strict, or the Dreamer is not producing statistically complete mechanisms.
- All three runs have confounders_identified failing 10/10: the Dreamer consistently fails to include rival explanations or confounder control.
- Stages 6 and 7 remain empty, as expected when no hypotheses PASS.
