# Ewha Reasoning Arena — E1 evidence audit (2026-10-11)

## Scope and branch isolation
Portal branch: `feature/ewha-reasoning-arena-e1`, based on `claude/experiment-17c-claude-replication`, **not** the older `main`. This is an independent Minos-J implementation. AeroCal is not a dependency or data source.

## Evidence classification
| Record | Status | Supported interpretation | Source |
|---|---|---|---|
| Experiments 4–7 | RECONSTRUCTED_SUMMARY_WITH_RECOVERED_ORIGINALS | Historical results cross-checked to recovered original JSON; not new runs | `historical/2026-08-04/RECOVERY_REPORT.md`, `docs/EXPERIMENTS.md` |
| Experiment 5 | HISTORICAL_SYNTHETIC_EXPERIMENT | Finite-sample-only hypothesis failed in tested simulated geometry; do not describe as participant or real-world model result | `results/recovered_results.json`, original historical output |
| Experiment 6 | HISTORICAL_SYNTHETIC_EXPERIMENT | Structural differences in coverage failures under tested combinations; not evidence of generally superior LLM reasoning | same |
| Experiment 7 Q3 | BLOCKED | Through stage 4.2 only, network blocked before stage 4.3 | `historical/2026-08-04/RECOVERY_REPORT.md` |
| Experiment 16 | INCONCLUSIVE | 0/9 analysable matched units | `docs/EXPERIMENTS.md` |
| Experiment 17 | INTERRUPTED | 0/9 evaluated; must not pool with 17-C | `historical/2026-09-20-experiments-16-17/RECOVERY_REPORT.md` |
| Experiment 17-C | INCONCLUSIVE | 1/9 analysable (minimum 6); six shared audit-rule failures; two other complete units budget-unmatched | `experiments/experiment_17c/results/RESULTS.md` |

## Study arms (17-C; *not* general to all experiments)
- A: v4 multi-stage pipeline.
- B: budget-matched sampling + one selector.
- Blinded judge: separate evaluation.
- The nominal budget tolerance is ±15%; only one of nine units met the full primary-analysis criterion.
- Requested model name and executed-model identity require separate provenance fields; 17-C reports ledger identity checks, but the portal should preserve this distinction for any other run.
- Never display the three complete 17-C units as three budget-matched comparisons.

## Provenance limitations
Original August source, outputs and checkpoints **are present on the recovered branch**, unlike `main`. 287 recovered SHA-256 manifest entries are described in the August recovery report. The original historical composite manifest procedure was **not** recovered and cannot be independently reproduced. Recovered results and a regenerated graphic are not new measurements.

## Replay data readiness
The checked README, result summaries, experiment reports and recovery notes document stage checkpoints and unit statuses, but do **not** establish that each event has a timestamped, log-backed, individually linkable reasoning trace meeting a playback schema. Until a trace adapter verifies exact event paths, show summary evidence and an explicit `TRACE_UNAVAILABLE` state. **Do not infer intermediate reasoning from stage names, summary text or diagrams.**

## E1 contract decision
- No implicit default for event timestamps, latency, cost, model execution identity, usage, or unit correctness.
- Every displayed measurement has a source path, evidence kind and verification status.
- `historical_synthetic_experiment` is distinct from `synthetic_ui_demo`: Experiment 5 and 6 were real historical tests **on synthetic geometry**, not fabricated UI data.
- `scientific_verdict = inconclusive` cannot be overridden by favorable subset metrics.
- Data loading remains read-only, and portal routes must never call original experimental runners.

## Next gates
E2: prepare a deterministic, read-only stage-event adapter against checkpoint files; validate every event's source path before animating. Render explicit unavailable states, then add timeline/lane controls. E3: verify matched-unit accounting from the persisted ledger. E4: gated professor feedback (no public writes). E5: responsive, reduced-motion and integrity tests prior to publication. Professor identity and sharing permissions remain unconfirmed.
