# Historical file map

The original Minos-J files have now been imported byte-for-byte under [`historical/2026-08-04`](../historical/2026-08-04). Every included source, output, checkpoint, and log is covered by the [SHA-256 manifest](../historical/2026-08-04/MANIFEST.sha256).

## Core modules reported in the historical implementation

- `literature_sources.py`
- `schema.py`
- `prompts.py`
- `pipeline.py`

These and the historical runners are available in [`historical/2026-08-04/source`](../historical/2026-08-04/source).

## Experiment 4

Runner:

- `run_pattern_falsification.py`

Outputs:

- `outputs/meno_j_experiment_4_pattern_falsification_study.json`
- `outputs/meno_j_experiment_4_pattern_falsification_study.md`
- `outputs/meno_j_experiment_4_reproducibility_summary.json`
- `outputs/meno_j_experiment_4_reproducibility_summary.md`

Recovered status:

- 9 surviving explanations
- 5 competing patterns
- 10 distinguishing experiments
- 8 validated primary sources
- 0 unknown citations / invalid references
- 10/10 experiments included effect-size targets
- 10/10 included explicit failure conditions
- no upstream/model-stage reruns
- no-key replay succeeded

## Experiment 5 — P4-F2

Runner:

- `run_p4_f2_synthetic_geometry.py`

Outputs:

- `outputs/meno_j_experiment_5_p4_f2_synthetic_geometry.json`
- `outputs/meno_j_experiment_5_p4_f2_synthetic_geometry.md`
- corresponding reproducibility summaries

Recovered design:

- 5 geometries
- 3 scores
- exact strategy identifiers: `marginal` and `mondrian_class`
- calibration sizes: 50, 100, 300
- seeds: 0–4
- 450 seed rows
- 90 aggregates

Recovered conclusion:

**P4-F2 falsified.**

## Experiment 6 — P4-F1

Runner:

- `run_p4_f1_score_conditioning.py`

Outputs:

- `outputs/meno_j_experiment_6_p4_f1_score_conditioning.json`
- `outputs/meno_j_experiment_6_p4_f1_score_conditioning.md`
- corresponding reproducibility summaries

Recovered design:

- 5 geometries
- 3 scores
- 3 conditioning strategies
- calibration sizes: 50, 100, 300, 600
- seeds: 0–4
- 900 seed rows
- 180 aggregates
- 45 trajectories

Recovered conclusion:

**Structural failure confirmed.**

## Experiment 7 v4

Recovered state:

- Q1: 10 generated / 9 PASS / 1 SALVAGEABLE / 0 REJECT
- Q2: 10 generated / 10 PASS / 0 SALVAGEABLE / 0 REJECT
- Q1/Q2 Stage 4–7 checkpoints valid
- Q3 valid through Stage 4.2
- Q3 blocked at Stage 4.3 by outbound-socket/network restriction before the required external API call
- 11 retries in the run record, including 8 HTTP 429 responses
- no fabricated Q3 completion was reported

## Architecture refactor

A canonical architecture document was historically created at:

- `outputs/meno_j_falsification_engine_architecture.md`

The refactor reframed the system around:

- strict filtering
- pattern extraction
- rival generation
- falsification
- execution
- theory updates

The older Dreamer component was made optional / replaceable rather than treated as the core scientific contribution.

## Recovery boundary

The historical tree contains 59 source/support files, 178 outputs, 48 checkpoints, and 2 run/hash logs. Participant-derived WESAD features, external datasets, vendor directories, and caches were intentionally excluded. No original figures were found. See the [full recovery report](../historical/2026-08-04/RECOVERY_REPORT.md).
