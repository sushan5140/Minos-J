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
| Judge attempt in flight at any stop | `STARTED` → `INTERRUPTED` (Experiment 17 rule) | consumes one of the two judge attempts for that batch (frozen rule, kept) |

Completed units (those with `arm_a_report.json`/`arm_a_failed.json`, `arm_b_result.json`/`arm_b_failed.json`, and a terminal judge state) are never re-executed or rewritten.
