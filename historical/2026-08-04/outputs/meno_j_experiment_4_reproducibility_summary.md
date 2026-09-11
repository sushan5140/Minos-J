# Meno-J Experiment 4: Reproducibility Summary

- Model: `nvidia/nemotron-3-ultra-550b-a55b:free`
- Temperature: 0.4
- Source file: `C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation\outputs\meno_j_experiment_3_cross_question_survivor_analysis.json`
- Source SHA-256: `42c37a0cdb7a00a1982df06ce34f1ac59b390b6e2c8ed82e120712a211e083dc`
- Literature sources: 8
- Pattern studies: 5
- Distinguishing experiments: 10
- Checkpoint: `C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation\work\experiment_4_checkpoints\pattern_falsification_studies.json`
- Checkpoint SHA-256: `2939917cd9f0e065a0855b4b4b8945434f1c99e5e3ec13ecf1d4856cc21e2b27`
- Ranking formula: `0.35*scientific_impact + 0.25*feasibility + 0.25*publication_potential + 0.15*information_gain`

## Validation

- `working_theory_valid`: True
- `no_new_hypotheses_generated`: True
- `all_pattern_ids_valid`: True
- `all_hypothesis_references_are_existing_pass`: True
- `all_citations_resolved`: True
- `all_effect_sizes_specified`: True
- `all_failure_conditions_specified`: True
- `roadmap_ranked_programmatically`: True

## Run command

`$env:OPENROUTER_API_KEY="<redacted>"; $env:OPENROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b:free"; python -u run_pattern_falsification.py`
