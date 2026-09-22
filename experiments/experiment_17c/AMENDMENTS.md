# Experiment 17-C engineering amendments

The frozen protocol (SHA-256 `31fadcff…2ab594`) is **unchanged**. The amendments below change only execution engineering. Each is recorded with its timing relative to observed data.

## Amendment 1 — arm failures are terminal across resumed processes (2026-09-23, ~22:37 UTC)

**Problem.** The inherited scientific core checkpoints arm *successes* (`arm_a_report.json`, `arm_b_result.json`) but not arm *failures*. When a process resumes after a pause or crash, it re-enters every unit. A failed Arm A (or a failed Arm B selector) is therefore silently given another attempt. A unit's outcome would then depend on whether an interruption happened. This actually occurred in the original Experiment 17: Q1-r1's Stage 5 was attempted in two process sessions (ledger seq 10 and seq 41).

**Trigger.** In the first 17-C session, Q1-r1's Stage 5 auditor returned 10 audits. The frozen `schema.validate_audits` rejected them because H2 was marked `SALVAGEABLE` with 0 failed critical checks, where it expects 1 or 2 (Experiment 16 hit the same failure mode). The process correctly recorded `ARM_A_FAILED` and moved on to Q2-r1. Without this amendment, a later pause would have given Q1-r1 a second chance.

**Change.** `run_experiment_17c_claude_replication._durable_arm_failures()` wraps the core's `run_arm_a` and `run_arm_b`:

- A model or validation failure (`Exception`) is written atomically to `arm_a_failed.json` or `arm_b_failed.json` and replayed on resume.
- Subscription usage-limit and auth stops derive from `BaseException`, so they are never recorded as failures. A pause cannot fail an arm.
- This mirrors Experiment 17's existing rule for judge attempts: resuming never creates extra opportunities.

**Q1-r1 backfill.** Q1-r1 failed under the pre-amendment code, so its marker was backfilled. The frozen validator was replayed on the archived diagnostic response `response_00000005.json`, which reproduced the identical error. The marker's `provenance` field documents this, and `recorded_at_utc` is the backfill time.

**Bias check.** At amendment time, no unit had reached the judge. The only affected unit is Q1-r1, and the amendment keeps it *failed*, which works against Arm A, the arm whose advantage is under test. The amendment cannot favor the hypothesis.

**Validation.** Harness check `arm_failure_terminal_across_resume_pause_not_failure` confirms that a failure is recorded once and replayed without a new model call, and that a pause leaves no marker. The harness now passes 20/20. The process that was already running (PID 22864, started before the amendment) keeps its loaded code until it exits. Its in-session behavior is identical, because the core visits each unit only once per process.

## Interruption safety (operator requirement: interruptions must not corrupt or invalidate completed units)

| State | Write method | Interruption risk |
|---|---|---|
| Arm A report, Arm B samples, selector, results, judge state/result, failure markers | atomic (`os.replace`) | none |
| Arm A per-stage checkpoints (historical `pipeline.py`, frozen) | plain `write_text` | a kill during the few-millisecond write could truncate JSON; the supervisor refuses to resume and flags it instead of letting the unit fail |
| Request ledger | append one line per event | a kill mid-append could truncate the last line; the supervisor refuses to resume and flags it |
| In-flight model call at a hard kill | not recorded (the ledger writes after the call returns) | that call's tokens would be missing from the unit's budget; the supervisor logs `unclean_termination_detected` so the affected unit can be flagged in the report |
| Judge attempt in flight at a stop | `STARTED` in atomic judge state | usage-limit/auth stop with no model output: withdrawn (amendment 2); hard kill or output already produced: consumed (frozen Experiment 17 rule) |

Completed units (those with `arm_a_report.json`/`arm_a_failed.json`, `arm_b_result.json`/`arm_b_failed.json`, and a terminal judge state) are never re-executed or rewritten.

## Amendment 2 — a provider stop with no model output is not a judge attempt (2026-09-23, ~22:50 UTC)

**Problem.** Under the inherited Experiment 17 rule, a judge attempt left `STARTED` counts as consumed. A subscription usage-limit or auth stop during a judge call leaves the attempt `STARTED` even though the provider refused the call and no model output exists. Two badly timed limits could fail a unit's judge phase with zero judgments made. Arm B samples and Arm A stages are already not charged in this situation (declared protocol deviation 9), so the judge was the only asymmetric case.

**Change.**
- `_durable_arm_failures()` also wraps `judge_unit`. On `SubscriptionUsageLimitReached` or `ClaudeAuthUnavailable`, it checks the ledger for any successful judge `request` row between the previous judge logical call and the failing one. If there is none, the `STARTED` attempt is withdrawn, kept under `provider_stops` in `judge_state.json`, and logged as a `judge_attempt_not_sent` ledger event.
- If model output *was* produced (for example, the limit hit on the JSON-repair request), the attempt stays consumed. That is the frozen Experiment 17 rule.
- `reconcile_provider_stopped_judge_attempts()` applies the same evidence rule at every resume. This covers stops that happened in a process started before this amendment (PID 22864).
- A hard kill leaves no ledger evidence, so it keeps the Experiment 17 rule.

**Bias check.** The judge scores both arms' cards in the same pooled, blinded batches, so this is arm-neutral. At amendment time, no unit had reached the judge.

## Execution safeguards added in the same audit (no scientific effect)

- **Arm B symmetry:** an unexpected Arm B exception is saved as a terminal `ARM_B_FAILED`, the same as Arm A, instead of crashing the process and being retried on every resume.
- **Single process:** the runner takes `work/experiment_17c_run.lock` (holder PID; reclaimed only when that PID is dead). A second run exits with code 73. The supervisor also refuses to start while any `--run` process is alive, and Task Scheduler's `IgnoreNew` policy stops ticks from overlapping.
- **No overwrite:** `--run` refuses to start once the final report exists, so completed results can't be regenerated. Output names for Experiments ≤ 17 are blocked by `HISTORICAL_GUARD`, and 17-C checkpoints live in their own folder.
- **Supervisor lifecycle:**
  - The tick deletes its own task once the run is complete and the independent validator has run.
  - It disables the task after 3 consecutive run failures, or when a ledger or checkpoint integrity check refuses to resume.
  - A usage-limit pause (exit 75) is not a failure. At most one run process starts per 30-minute tick, and it stops at the first refused call, so a limit window costs at most one zero-token failed call per tick.
  - Task Scheduler deletes the task automatically at its 21-day end boundary (`DeleteExpiredTaskAfter=PT0S`).

Harness validation now passes 26/26. The frozen protocol is unchanged, and preflight confirms the on-disk protocol still matches.

## Installer fix — self-test wait logic (2026-09-23)

The first manual install failed with "Self-test produced no fresh result". Investigation:

- **Not auth or Python.** The identical action (`conhost --headless python work\experiment_17c_tick.py --selftest`), run outside Task Scheduler, passed in 6.3 s: `authMethod=claude.ai`, output `{"answer": 4}`. `conhost --headless` was also confirmed to wait for its child.
- **Not the future `StartBoundary` either.** The installer already called `Start-ScheduledTask`; StartBoundary only controls automatic triggering.
- **Root cause: the wait loop.** It slept 3 s and then waited only *while* the state was `Running`, without ever confirming the task had launched. If the task was still `Queued`/`Ready` at that moment, the loop ended at once. `Stop-ScheduledTask` then killed any Python that had started, and the task was deleted, erasing `LastTaskResult`. The self-test takes about 6 s and logged only at its end, so no trace was left.
- **Why the exact path can't be confirmed.** The Task Scheduler Operational log is disabled on this machine, and the installer deleted the task record. The log was not enabled, because that is a system setting.

**Fix (installer and self-test diagnostics only; no experimental file, protocol or running process touched):**

- The self-test task has no trigger; it runs on demand only.
- It is started explicitly. The installer then polls until Task Scheduler reports `LastRunTime` after registration *and* a state other than `Running`/`Queued`, with a 6-minute timeout.
- `LastRunTime`, `LastTaskResult` and a state timeline are captured before the task is deleted, in a `finally` block.
- The tick logs `selftest started` as its first action and writes any traceback to `work/experiment_17c_selftest_error.txt`.
- Every attempt writes `work/experiment_17c_install_diagnostics/install_<timestamp>.json`, classified as one of: `SCHEDULING_FAILURE`, `LAUNCHER_FAILURE`, `TIMEOUT`, `SELFTEST_CRASH`, `NO_RESULT`, `CLAUDE_CLI_OR_AUTH_FAILURE`, `WRONG_OUTPUT`, `PASS`.
- Earlier results are moved aside, never deleted.
- The recurring supervisor is registered only on `PASS`.
