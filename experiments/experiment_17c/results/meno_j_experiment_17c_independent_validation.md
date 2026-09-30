# Minos-J Experiment 17-C: Claude-Based Replication of Experiment 17 (Matched-Compute Architecture Falsification) — Independent Validation

- Status: **PASSED**
- Protocol SHA-256: `31fadcff3a17d6e81e074b309d23726f394c36cc21d0ce2610148548352ab594`
- Scientific verdict: `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`

| Check | Result | Detail |
|---|---|---|
| all_scientific_outputs_exist | PASS |  |
| protocol_frozen_and_hash_verified | PASS | canonical SHA-256 31fadcff3a17d6e81e074b309d23726f394c36cc21d0ce2610148548352ab594 |
| model_assignments_exact | PASS | generator=claude-sonnet-5; judge=claude-opus-5-5 |
| nine_unique_preregistered_units | PASS | report=['Q1-r1', 'Q2-r1', 'Q3-r1', 'Q1-r2', 'Q2-r2', 'Q3-r2', 'Q1-r3', 'Q2-r3', 'Q3-r3']; raw=['Q1-r1', 'Q2-r1', 'Q3-r1', 'Q1-r2', 'Q2-r2', 'Q3-r2', 'Q1-r3', 'Q2-r3', 'Q3-r3'] |
| ledger_sequences_unique_and_monotonic | PASS | rows=225; max=225 |
| ledger_uses_only_frozen_models | PASS | bad sequences=[] |
| per_unit_budgets_recompute_from_ledger | PASS |  |
| token_and_attempt_accounting_reconciles | PASS | tokens=2826926/2826926; attempts=113/113 |
| matched_compute_flags_and_count | PASS | analysable=1; mismatches=[] |
| judge_outputs_schema_and_counts | PASS | judgment_rows=48; judge_failed_units=0; issues=[] |
| paired_differences_recompute | PASS |  |
| bootstrap_ci_and_preregistered_verdict_recompute | PASS | verdict=INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS; stats mismatches=[] |
| historical_experiments_unchanged | PASS | files=700; changed=[] |
| credential_safety_scan | PASS | files=229; hits=[] |
| resume_and_judge_attempt_integrity | PASS | judge_state_files=3; invalid=[] |
