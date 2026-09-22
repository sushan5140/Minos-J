# Meno-J Experiment 17: Repaired Matched-Compute Architecture Falsification — Preregistered Protocol

> Frozen before any Experiment 17 model-completion call. This is a new protocol; Experiment 16 remains unchanged.

## Central research question

If a multi-stage reasoning pipeline performs better than a simpler baseline, does the architecture itself deserve the credit once inference budget, sampling, retries, and evaluator passes are controlled?

## Arms and matched-compute rule

- Arm A: historical Minos-J v4 multi-stage pipeline.
- Arm B: one-shot sampling plus one strict selector/verifier.
- Generator: `nvidia/nemotron-3-super-120b-a12b:free` for both arms.
- Blinded judge: `nex-agi/nex-n2.5-pro:free`.
- Budget tolerance: `a unit is budget-matched iff 0.85 <= T_B / T_A <= 1.15 and E_B == E_A`.
- Failed calls are included in attempt accounting; judge calls remain outside arm budgets.

## Changes from Experiment 16

- Changed generator and blinded-judge models because the Experiment 16 free endpoints did not advertise structured outputs.
- Added strict response_format/json_schema requests and provider capability enforcement.
- Added IncompleteRead and remote-disconnect retry coverage.
- Made ledger sequences unique across resumed processes.
- Made failed judge attempts durable and terminal after the preregistered two-attempt limit.
- Made all JSON serialization RFC-compliant and replaced non-finite values with null.
- Added sanitized response-body retention for reconstruction of parser and validator failures.
- No change to questions, arms, matched-compute tolerance, primary/secondary outcomes, analysis set, or falsification criterion.

## Outcomes and falsification criterion

- Primary outcome: V = number of judge-validated cards in an arm's final deliverable (0-10); paired difference D = V_A - V_B per unit
- Analysis set: units where both arms completed, the judge completed, and the budget was matched
- Statistics: mean D; paired bootstrap 95% CI (10000 resamples, seed 16); exact two-sided sign test on non-zero D
- Criterion: If the matched-budget simple baseline performs similarly to or better than Minos-J within reasonable experimental variation, Experiment 17 does NOT support the claim that the Minos-J architecture itself is responsible for the gain.

## Engineering reliability contract

- transient_network_retries: At most four retries for timeout, IncompleteRead, remote disconnect/reset, URLError, and HTTP 429/500/502/503/504; failed attempts remain in accounting.
- invalid_response_shape: One retry, recorded in the ledger and diagnostic archive.
- invalid_json: Exactly one schema-constrained repair request; no further semantic repair loop.
- structured_output: Every completion request carries a strict stage-specific JSON schema.
- resume: Ledger sequences continue from the maximum existing value. Judge state is checkpointed after every attempt, including terminal failure, so resume never creates extra judge opportunities.
- serialization: All Experiment 17 JSON uses UTF-8, allow_nan=false; non-finite statistics are represented as null.
- diagnostics: Response bodies, including partial/invalid bodies, are retained in a credential-free diagnostic archive. Request headers and credentials are never stored. Diagnostics are not scientific outcomes.

## Estimated API requirements

- experimental_units: 9
- generator_endpoint_logical_calls_range: approximately 63-198 before JSON-repair calls
- judge_endpoint_logical_calls_range: approximately 9-36 including the one allowed invalid-output retry per batch
- token_planning_range: approximately 1.6-2.2M experimental-arm tokens plus 0.3-0.6M judge tokens
- advertised_price_at_preregistration: $0/M input and $0/M output for both recommended :free endpoints
- operational_warning: Free-tier rate limits and availability are not guaranteed; preflight must pass immediately before a real run.

## Integrity

- Protocol SHA-256: `76ae7d0ae043fab1e0a34f0f34ed0380473d725cad689260d15b0f44125d5b8b`
- Capability snapshot: `meno_j_experiment_17_model_capability_snapshot.json`
