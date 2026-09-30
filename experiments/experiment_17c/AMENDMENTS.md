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

## Recovery audit of 2026-09-30 — what happened after the last update

Reconstructed from the request ledger (69 rows; sequences unique and monotonic; readable), 52 diagnostic captures, unit checkpoints, and logs. Nothing was inferred from incomplete files.

- **One process session** ran (PID 22864, `session_start` seq 1, pre-amendment code) from 2026-09-22 22:23 UTC. It never paused, and it wrote no final report.
- **Genuine Stage 5 failure, Q1-r1:** H2 was marked `SALVAGEABLE` with 0 failed critical checks. Replaying the frozen validator on archived response 5 reproduces the error. Terminal `ARM_A_FAILED`.
- **Q2-r1 completed:** both arms and the judge (2 batches, 14 cards, both attempts completed on the first try, no blinding leaks). T_B/T_A = 199,466 / 239,404 = **0.833**, below the 0.85 floor, so it is **budget-unmatched** under the frozen rule.
  - Arm B sample 3 hit the 12,000-token output ceiling. Its error envelope reported 48,000 output tokens (see the separate note below), which the frozen currency ("successful requests only") excludes. It is not reclassified, because this unit's outcome was already known.
- **Genuine Stage 5 failure, Q3-r1:** H4 was marked `SALVAGEABLE` with 0 failed critical checks, reproduced by replaying archived response 26. Terminal `ARM_A_FAILED`, backfilled under amendment 1.
- **From 23:19 UTC, the Pro plan returned HTTP 429** "You've hit your session limit · resets 8:20am (Asia/Kolkata)". The quota-detection pattern did not match this wording, so each refusal was retried 4× as transient and then raised `RuntimeError`. The pre-amendment process recorded in-memory `ARM_A_FAILED` outcomes for **Q1-r2** (at Stage 5, after valid 4–4.3 checkpoints), **Q2-r2**, **Q3-r2** and **Q1-r3** (at Stage 4). All 20 underlying attempts (captures 31–50) are 429 session-limit refusals with 0 output tokens. No marker files were written.
- **Q2-r3:** its first attempt (capture 51) was refused. The next attempt hung, the process ended (captured as a `cli_timeout` at 05:50 UTC, capture 52), and the background shell reported exit code 4. No ledger row was written: this is an **unclean termination**.
- **Q3-r3:** never started.
- **The Task Scheduler supervisor was never installed.** The corrected installer's self-test ran (LastTaskResult 0x0, Python started) but crashed in `find_cli`. The Claude desktop app is an MSIX package, so `%APPDATA%\Claude\claude-code` exists only inside the package view. Processes launched by Task Scheduler see only `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude-code`. Confirmed with an out-of-package probe (`NOT_VISIBLE`). The installer correctly refused to register the supervisor.
- **The Claude Code CLI auto-updated** from 2.1.280 to 2.1.284 between sessions. The model IDs are unchanged, and each session records its CLI version in its `session_start` event.

## Amendment 3 — quota refusals are recognized and never charged as arm calls (2026-09-30)

**Reason.** The quota-detection defect above turned provider refusals into arm "failures" for 4 units. That contradicts frozen protocol deviation 9: "a subscription usage-limit stop … the run halts, nothing is charged to an arm … the same command resumes later". Separately, the inherited budget summarizer counts even a *correctly* classified refused logical call toward generator/evaluator call counts, and therefore toward evaluator parity. That is also a charge to the arm.

**Exact change.**
- `experiment_17c_claude_runtime.is_usage_limit()`: the pattern now also matches `session limit`, `resets <digit>` and `hit your … limit`, and any HTTP 429 whose message mentions a limit is treated as a quota stop. An output-ceiling error (`exceeded the 12000 output token maximum`) is still **not** a quota stop.
- `run_experiment_17c_claude_replication.provider_stop_reclassifications()`: walks the ledger in order and maps each request row to its `http_attempts` diagnostic captures. The mapping is exact: 50 attempts ↔ 50 captures. A `request_failed` `RuntimeError` row is reclassified **only if every** mapped capture is an HTTP 429 limit message with 0 output tokens. Each qualifying row is recorded by appending a `provider_stop_reclassified` ledger event listing the target seqs and capture numbers. No existing ledger row is modified.
- `_provider_stop_aware_budgets()`: logical calls with a provider-stop error, or listed in a reclassification event, are excluded from `logical_calls`, `generator_calls`, `evaluator_calls` and `logical_calls_failed`. They are reported as `provider_refused_logical_calls`. HTTP attempts stay in attempt accounting, and token totals are unaffected, since refusals carry 0 tokens.
- `orphan_captures()`: diagnostic attempts with no ledger row are recorded as an `unclean_termination_recorded` event (Q2-r3: captures 51–52).
- `find_cli()`: also searches the MSIX package-private CLI location, so the Task Scheduler supervisor can find the CLI.

**Affected units.** Q1-r2, Q2-r2, Q3-r2 and Q1-r3 (reclassified; their observations are refusals, not model outputs), and Q2-r3 (unclean termination recorded). On a dry run, the reclassification selected exactly ledger seqs 62–69. **Unaffected:** Q1-r1, Q3-r1 (genuine failures), and Q2-r1 (complete; budgets unchanged, verified by recomputation).

**Bias assessment.** The rule is arm-symmetric: it applies to any arm's refused call. All affected calls happened to be Arm A calls, because Arm A runs first in each unit. No affected unit had produced any Arm B output or judge output, so no treatment comparison was visible for them. Without the amendment, the defect would have forced 4 units into `ARM_A_FAILED`, an outcome caused by a quota message rather than the model.
- **Sensitivity analysis committed now:** the final report will also give the verdict statistics with all amendment-3-affected units excluded.

**Validity of prior observations.** All existing checkpoints remain valid. Q1-r2 resumes at Stage 5 from its intact Stage 4–4.3 checkpoints. Q2-r2, Q3-r2, Q1-r3 and Q2-r3 have no model output and restart from Stage 4. Q3-r3 has not started.

**Validation.** The harness passes 29/29, including a check on the real Pro message and a check that a truncation is not reclassified. Protocol SHA-256 `31fadcff…2ab594` still matches. All Experiment 1–17 files match their pre-run baseline, so the original Experiment 17 is untouched.

## Noted, not amended — unmetered tokens on failed requests

The frozen currency counts provider-reported usage on successful requests only. Claude Code error envelopes can carry usage: Q2-r1's truncated sample reported 48,000 output tokens. These tokens are real compute that the frozen matching rule does not count. The rule is kept as frozen. The final report will list unmetered usage per unit, reconstructed from diagnostics, and a sensitivity token ratio that includes it.
