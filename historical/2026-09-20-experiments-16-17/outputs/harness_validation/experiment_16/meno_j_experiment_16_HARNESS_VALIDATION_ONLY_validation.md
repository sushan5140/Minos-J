# Meno-J Experiment 16: Matched-Compute Architecture Falsification — Harness Validation

> **HARNESS VALIDATION ONLY - produced by a deterministic fake model. These numbers are NOT scientific results and must not be cited.**

- Status: **PASSED**
- Protocol SHA-256: `f76d6d2a5f6fa4eb0c168a2cdf001af54507618fa8c08ac45cf52cd237eed96a`
- Runner SHA-256: `9ab601b636ee66f2ea100e920a84ec1dedec0ae7bd1b9e89b30802387cf4a7db`
- Historical files hashed: 337

| Check | Result | Detail |
|---|---|---|
| protocol_frozen_and_matches_code | PASS | sha256 f76d6d2a5f6fa4eb0c168a2cdf001af54507618fa8c08ac45cf52cd237eed96a |
| deterministic_replay_identical | PASS |  |
| fake_outputs_labeled | PASS | verdict replaced by HARNESS_VALIDATION_ONLY_NOT_A_SCIENTIFIC_RESULT |
| successful_request_count_matches_server | PASS | 122 vs 122 |
| http_attempts_match_server | PASS | server attempts 123 |
| token_totals_match_server | PASS | prompt 409925/409926, completion 210265/210265, estimated-usage rows 1 (slack 2) |
| usage_missing_path_flagged | PASS |  |
| arm_plus_judge_tokens_equal_ledger | PASS |  |
| retry_path_counted | PASS | one injected HTTP 429, historical 60 s backoff requested (not slept) |
| json_repair_path_counted | PASS |  |
| per_unit_budget_recomputes_from_raw_ledger | PASS |  |
| matched_budget_flags_consistent | PASS |  |
| evaluator_parity_every_unit | PASS |  |
| invalid_baseline_sample_still_charged | PASS |  |
| arm_a_ran_all_v4_stages | PASS |  |
| budget_controller_picks_closest_k | PASS | [] |
| judge_uses_separate_model | PASS |  |
| judge_calls_excluded_from_arm_budgets | PASS |  |
| blinded_judge_plumbing | PASS |  |
| blinding_is_seeded_and_key_kept_out_of_cards | PASS |  |
| raw_and_aggregate_outputs_written | PASS | 9 aggregate rows, 27 budget rows |
| output_names_never_historical | PASS |  |
| real_and_fake_paths_disjoint | PASS |  |
| verdict_rule_matches_preregistration | PASS | [] |
| credential_scan_new_files | PASS |  |
| historical_files_unchanged | PASS | 337 files hashed; changed: [] |
| experiments_8_to_15_present_and_unchanged | PASS | 153 Experiment 8-15 files in this checkout |
