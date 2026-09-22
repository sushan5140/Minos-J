# Meno-J Experiment 17 Preparation Report

> Engineering preparation only. No real model-completion calls were made and no scientific conclusions were generated.

## 1. Engineering repairs completed

- Added retry handling for `http.client.IncompleteRead`, remote disconnect/reset, timeout, `URLError`, and transient HTTP 429/5xx failures.
- Ledger sequence numbers resume from the maximum existing sequence and refuse a ledger that already contains duplicate or invalid identifiers.
- Judge attempts are checkpointed as `STARTED` before the request and as `COMPLETED` afterward. Interrupted attempts remain consumed. A terminal judge failure is checkpointed, so resume cannot grant extra attempts.
- All Experiment 17 JSON is written as UTF-8 with `allow_nan=false`; non-finite statistics become JSON `null`.
- Every response envelope, partial body, and invalid assistant body is retained in a separate diagnostic archive. Credentials and request headers are not retained.
- Every model request carries a strict, stage-specific JSON schema and `provider.require_parameters=true`.
- Experiment 16 code, protocol, checkpoints, raw responses, and results were not modified.

## 2. Synthetic validation

- Result: **14/14 passed**.
- Covered contradictory `SALVAGEABLE` decisions, incomplete output, wrong audit counts, invalid JSON, successful single repair, failed repair, `IncompleteRead`, response-body retention/redaction, ledger resume, token accounting, repeated judge attempts, interrupted in-flight judge attempts, strict JSON, protocol invariants, schema dispatch, capability metadata, credentials, and Experiment 16 integrity.
- The deterministic responses are engineering fixtures only, not research findings.

## 3. Recommended generator

`nvidia/nemotron-3-super-120b-a12b:free`

The public model record and its Nvidia endpoint both advertised `response_format` and `structured_outputs`, a 262,144-token context, a 235,929-token maximum completion, endpoint status `0`, and zero advertised input/output price at inspection time.

## 4. Recommended blinded judge

`nex-agi/nex-n2.5-pro:free`

The public model record and its Nex AGI endpoint both advertised `response_format` and `structured_outputs`, a 262,144-token context, a 235,929-token maximum completion, endpoint status `0`, and zero advertised input/output price at inspection time. It is a separate model family from the generator.

## 5. Verified capability metadata

- Metadata source: `https://openrouter.ai/api/v1/models` plus each selected model's public endpoint record.
- Required at both model and endpoint levels: `response_format`, `structured_outputs`.
- Future preflight refreshes the public metadata and fails if either selected endpoint loses the required parameters, 12,000-token output capacity, zero advertised price, or status `0`.
- Metadata inspection used public GET requests only; it did not submit prompts or consume model tokens.

## 6. Estimated API requirements

- Units: 9 (Q1-Q3 × 3 replicates).
- Generator endpoint: approximately 63-198 logical calls before any one-time JSON-repair calls.
- Blinded judge: approximately 9-36 logical calls including the single allowed invalid-output retry per batch.
- Planning range: approximately 1.6-2.2 million experimental-arm tokens plus 0.3-0.6 million judge tokens.
- Advertised cost at preregistration: zero for both selected free endpoints; rate limits and continued free availability are not guaranteed.

## 7. Protocol and validation locations

- `outputs/meno_j_experiment_17_preregistered_protocol.json`
- `outputs/meno_j_experiment_17_preregistered_protocol.md`
- `outputs/meno_j_experiment_17_model_capability_snapshot.json`
- `outputs/meno_j_experiment_17_model_capability_snapshot.md`
- `outputs/harness_validation/experiment_17/meno_j_experiment_17_preparation_validation.json`
- `outputs/harness_validation/experiment_17/meno_j_experiment_17_preparation_validation.md`
- `outputs/harness_validation/experiment_17/meno_j_experiment_17_preparation_reproducibility.json`
- `outputs/harness_validation/experiment_17/meno_j_experiment_17_preparation_reproducibility.md`

## 8. Remaining blockers before real execution

1. The local environment is not yet configured for the frozen Experiment 17 pair: `OPENROUTER_MODEL` is unset and `MINOS_J_JUDGE_MODEL` still names the Experiment 16 judge. The current preflight therefore fails intentionally.
2. A minimal live structured-output smoke test has not been run because this preparation task explicitly stops before real model calls. It should test one tiny schema against each frozen model before starting scientific units and must not be interpreted as a scientific result.
3. Free-tier availability and rate limits can change. The public metadata preflight must pass immediately before execution. If either exact model becomes unsuitable, a protocol amendment or newly preregistered study is required before seeing results; models must never be switched mid-study.

## Scientific-protocol status

The central question, Q1-Q3 task set, Arm A and Arm B definitions, matching tolerance, failed-call accounting, blinded evaluation criteria, primary and secondary outcomes, analysis set, confidence-interval method, minimum analysable units, and falsification decisions are unchanged from Experiment 16. The reliability and model-compatibility changes are explicitly preregistered as Experiment 17 rather than silently altering Experiment 16.
