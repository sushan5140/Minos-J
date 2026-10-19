# Meno-J Experiment 2: Confounder Enrichment Ablation

## Model

`nvidia/nemotron-3-ultra-550b-a55b:free`

## v2 baseline vs v3 enriched

| Question | Version | Generated | PASS | SALVAGEABLE | REJECT | Pass rate | Salvageable rate | Confounder failures | Effect-size failures | Non-generic failures | Data-requirement failures | Stage 6 | Stage 7 | Red flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|---|
| Q1 | v2 baseline | 10 | 0 | 2 | 8 | 0.0% | 20.0% | 10 | 10 | 3 | 5 | No | No | None |
| Q1 | v3 enriched | 10 | 9 | 0 | 1 | 90.0% | 0.0% | 0 | 0 | 1 | 0 | Yes | Yes | None |
| Q2 | v2 baseline | 10 | 0 | 10 | 0 | 0.0% | 100.0% | 10 | 0 | 9 | 0 | No | No | None |
| Q2 | v3 enriched | 10 | 7 | 0 | 3 | 70.0% | 0.0% | 0 | 0 | 3 | 0 | Yes | Yes | None |
| Q3 | v2 baseline | 10 | 0 | 7 | 3 | 0.0% | 70.0% | 10 | 0 | 3 | 0 | No | No | None |
| Q3 | v3 enriched | 10 | 9 | 1 | 0 | 90.0% | 10.0% | 0 | 0 | 1 | 0 | Yes | Yes | None |

## Per-question improvement

### Q1

- `confounders_identified_failures_decreased`: Yes
- `effect_size_plausible_failures_decreased`: Yes
- `pass_count_increased`: Yes
- `stage_6_and_stage_7_ran`: Yes
- `nonpass_reasons_became_more_specific`: No

### Q2

- `confounders_identified_failures_decreased`: Yes
- `effect_size_plausible_failures_decreased`: No
- `pass_count_increased`: Yes
- `stage_6_and_stage_7_ran`: Yes
- `nonpass_reasons_became_more_specific`: No

### Q3

- `confounders_identified_failures_decreased`: Yes
- `effect_size_plausible_failures_decreased`: No
- `pass_count_increased`: Yes
- `stage_6_and_stage_7_ran`: Yes
- `nonpass_reasons_became_more_specific`: Yes

## Overall success criteria

- `confounders_identified_failures_decreased`: Yes
- `effect_size_plausible_failures_decreased`: Yes
- `pass_count_increased`: Yes
- `stage_6_and_stage_7_ran_for_at_least_one_hypothesis`: Yes
- `nonpass_reasons_became_more_specific`: Yes
