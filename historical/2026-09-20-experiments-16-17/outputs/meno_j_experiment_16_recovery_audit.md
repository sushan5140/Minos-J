# Minos-J Experiment 16 Recovery Audit

## Status and scope

This is a diagnostic report, not a scientific result.

- The original Experiment 16 protocol, checkpoints, request ledger, reports, and historical Experiments 1–15 were not modified.
- No OpenRouter completion was called for this audit.
- No diagnostic observation below is interpreted as evidence for or against the Minos-J architecture.
- Audit date: 2026-09-20.

The audit examined:

- `outputs/meno_j_experiment_16_matched_compute.json`
- `outputs/meno_j_experiment_16_matched_compute_raw_requests.jsonl`
- `outputs/meno_j_experiment_16_matched_compute_raw_units.jsonl`
- `work/experiment_16_checkpoints/`
- `run_experiment_16_matched_compute.py`
- `llm_client.py`, `pipeline.py`, `prompts.py`, and `schema.py`
- the current OpenRouter model catalog and structured-output documentation

## Executive diagnosis

Experiment 16 did not fail because its scientific comparison favored one arm. It failed before a valid comparison could be measured.

The dominant causes were:

1. **Prompt-only structured output.** The exact free generator and judge endpoints do not currently advertise `response_format` or `structured_outputs`. The harness also sent neither parameter. Exact JSON structure was therefore requested only in prose.
2. **Output truncation.** Several critical responses reached the harness's exact `max_tokens=12000` ceiling. Those responses frequently required JSON repair and sometimes remained invalid or incomplete.
3. **Semantic rule violations after successful parsing.** Four Arm A audits returned `SALVAGEABLE` while all critical booleans were true. The JSON parser worked; the model contradicted an explicit decision rule, and the validator correctly rejected it.
4. **Judge unreliability.** The judge repeatedly produced truncated JSON, invalid repaired JSON, schema-invalid parsed JSON, or response envelopes with no assistant content.
5. **One genuine transport failure.** Q3-r3 ended with `http.client.IncompleteRead(605 bytes read)`. The client did not classify this exception as retryable.
6. **Insufficient failure observability.** Invalid model content and invalid response envelopes were not archived. Exact field-level defects therefore cannot be recovered for several failures.
7. **Resume and reporting defects.** Ledger sequence numbers restarted at 1 on resume, failed judge state was not checkpointed, and an empty analysis set was serialized with non-standard JSON `NaN` values.

The parsers and strict validators were not the primary cause of the failed scientific run. They mostly did their job by refusing malformed or contradictory data. The important parser-adjacent problem was that the harness discarded the evidence needed to diagnose invalid payloads precisely.

## Critical evidence limitation: invalid raw responses were not preserved

The user requested inspection of the raw responses. The valid response metadata is available, but the invalid response bodies are not.

`Meter._wrapped` records token usage, hashes, timing, model identity, and retry counters. It does not store `message.content`, the full OpenRouter envelope, response IDs, finish reasons, provider identifiers, or native finish reasons. Invalid Stage 5 and selector payloads are rejected before checkpointing. `judge_unit` writes `judge_result.json` only when the entire judge stage succeeds.

Consequently:

- the exact contradictory audit objects are not recoverable;
- the actual incorrect Arm B audit count is not recoverable;
- the exact judge schema rule violated in `PipelineValidationError` cases is not recoverable;
- the contents of the five Q2-r3 no-content response envelopes are not recoverable;
- the invalid or truncated text passed to JSON repair is not recoverable.

The audit can still identify the failure layer exactly from control flow and exception type. It cannot honestly reconstruct content that was never retained.

## Failure classification summary

| Unit | Failure | JSON parsing | Schema/decision validation | Truncation evidence | Primary owner |
|---|---|---|---|---|---|
| Q2-r1 | Stage 5 H6 `SALVAGEABLE` with 0 failed critical checks | Passed | Correctly failed | None; 6,882 completion tokens | Model instruction following |
| Q3-r1 | Stage 5 H5 `SALVAGEABLE` with 0 failed critical checks | Passed | Correctly failed | None; 7,615 completion tokens | Model instruction following |
| Q1-r2 | Stage 5 H1 `SALVAGEABLE` with 0 failed critical checks | Initial JSON failed; repair parsed | Correctly failed | Initial response hit 12,000 tokens | Model plus truncation |
| Q3-r2 | Stage 5 H6 `SALVAGEABLE` with 0 failed critical checks | Passed | Correctly failed | None; 7,983 completion tokens | Model instruction following |
| Q3-r3 | Arm A Stage 4.2 `IncompleteRead(605 bytes read)` | No complete envelope | Not reached | Incomplete transfer | Provider/network plus retry gap |
| Q1-r3 | Arm B selector returned a list whose length was not 10 | Initial JSON failed; repair parsed | Correctly failed | Initial response hit 12,000 tokens | Model plus truncation |
| Q1-r1 | Blind judge batch 1 failed; failures included invalid repaired JSON and later schema-invalid parsed JSON | Mixed | Mixed | Multiple responses hit 12,000 tokens | Judge model; resume defect added attempts |
| Q2-r2 | Blind judge batch 0 failed schema validation twice after JSON repair | Repair parsed both times | Failed, exact rule unavailable | Both initial responses hit 12,000 tokens | Judge model plus truncation |
| Q2-r3 | First judge attempt remained invalid after repair; second returned five envelopes without assistant content | Failed | Not reached | Initial response hit 12,000 tokens | Judge model/provider response shape |

## 1. Four contradictory `SALVAGEABLE` decisions

Affected units:

- Q2-r1, H6
- Q3-r1, H5
- Q1-r2, H1
- Q3-r2, H6

### What happened

The Stage 5 prompt states that `SALVAGEABLE` is permitted only when one or two critical checks fail. `schema.validate_audits` independently recomputes the number of false critical fields. In each affected unit the model selected `SALVAGEABLE` while the critical booleans implied zero failures.

The error was raised only after the payload had passed all earlier checks needed to reach that branch: top-level object, audit list, expected count, exact row fields, known ID, legal decision name, JSON booleans, failure-point list type, and a non-empty decision reason.

Therefore these were **not parser implementation failures**. They were semantic contradictions in model output. The validator correctly enforced the preregistered rule.

### Per-unit evidence

- **Q2-r1:** one normal model response, 6,882 completion tokens, no JSON repair, followed by `PipelineValidationError` for H6.
- **Q3-r1:** one normal model response, 7,615 completion tokens, no JSON repair, followed by the same contradiction for H5.
- **Q1-r2:** the first response used exactly 12,000 completion tokens and was invalid JSON. One repair response used 2,557 tokens and parsed successfully, but the repaired object still made the contradictory decision for H1.
- **Q3-r2:** one normal model response, 7,983 completion tokens, no JSON repair, followed by the contradiction for H6.

### Root cause assignment

- Model instruction following: **yes**.
- Invalid JSON: **only the initial Q1-r2 response; repaired before the semantic failure**.
- Schema validation failure: **yes, correctly detected**.
- Contradictory decision rule: **yes; this is the final cause in all four units**.
- Parser error: **no evidence**.
- Provider/network error: **no evidence**.
- Token truncation: **Q1-r2 initial response only**.

## 2. Incomplete Arm A network response

Affected unit: Q3-r3, Stage 4.2 Confounder/Rival Builder.

### What happened

The request ended with `IncompleteRead(605 bytes read)`. The ledger contains a `request_failed` event, one HTTP attempt, no returned model, no usage, and no retry.

This is a transport-level incomplete body, not a hypothesis-schema failure and not evidence about model reasoning quality.

### Why it was not retried

`llm_client._request_json` retries `TimeoutError`, `socket.timeout`, transient HTTP status codes, `URLError`, `ConnectionError`, `ConnectionResetError`, and `OSError`. `http.client.IncompleteRead` was not caught by those clauses in this execution, so it escaped immediately.

### Root cause assignment

- Provider/network: **primary cause**.
- Harness retry coverage: **secondary cause**.
- Model instruction following: **not assessable; no complete response**.
- JSON/parser/schema: **not reached**.

## 3. Incorrect Arm B audit count

Affected unit: Q1-r3, Arm B selector/auditor.

### What happened

The selector prompt required exactly 10 distinct selected audits. The initial response reached exactly 12,000 completion tokens and was invalid JSON. The JSON-repair response used 3,707 completion tokens and parsed as an object. `validate_selector` then rejected it because `selected_audits` was not a list of length 10.

The actual returned length is unavailable because the invalid selector payload was not archived.

### Root cause assignment

- Incomplete output/token truncation: **strong evidence for the initial response**.
- Invalid JSON: **yes, initial response**.
- Model instruction following: **yes, repaired response still violated exact cardinality**.
- Schema validator: **correct behavior**.
- Parser implementation: **no evidence of error**.

The repair call also increased Arm B tokens enough to produce an unmatched B/A ratio of 1.640. That mismatch is a consequence of charging the repair call as preregistered, not an accounting error.

## 4. Three failed blinded-judge evaluations

### Q1-r1

Q1-r1 had 18 cards, split into batches of 10 and 8. Batch 0 succeeded. Batch 1 failed.

The request ledger contains evidence from the original interrupted execution and the resumed execution:

- Original execution, batch 1: two attempts ended as `ValueError`, meaning JSON remained invalid after the repair path.
- Resumed execution, batch 1: two more attempts parsed but ended as `PipelineValidationError`.
- Six of the twelve Q1-r1 judge HTTP responses reached exactly 12,000 completion tokens.
- Six judge JSON-repair requests were made across the original and resumed judge stage.

The exact schema violation in the later attempts cannot be recovered because `judge_invalid` logged only the exception class, not the exception message or rejected payload.

#### Resume protocol issue

`judge_unit` checkpoints only successful judge results. A failed judge result is returned but not written to `judge_result.json`. When the Experiment 16 process was resumed, Q1-r1's judge stage ran again from batch 0 and provided another two attempts for failing batch 1.

This did not rescue Q1-r1, but it created more judge opportunities than the intended one retry per batch. It is a harness resume defect and should be fixed before any future preregistered run.

### Q2-r2

Q2-r2 failed on judge batch 0:

- attempt 1: initial output hit 12,000 tokens; the 9,730-token repair parsed; validation failed;
- attempt 2: initial output hit 12,000 tokens; the 4,391-token repair parsed; validation failed.

Both final exceptions were `PipelineValidationError`. The exact violated rule—wrong count, fields, boolean types, empty reason, or card-ID mismatch—is unavailable because the error message and rejected payload were not logged.

### Q2-r3

Q2-r3 failed in two different ways:

- attempt 1: initial output hit 12,000 tokens; the 2,661-token repair was still invalid JSON, producing `ValueError`;
- attempt 2: OpenRouter returned five JSON envelopes without usable `choices[0].message.content`. Each ledger row has `model_returned=null`, `completion_tokens=0`, and estimated rather than provider-reported usage. After four internal shape retries, `call_llm` raised `ValueError`.

The content of those envelopes was not retained, so the audit cannot determine whether they contained provider error objects, incomplete generation status, or another non-chat response shape.

### Judge-wide pattern

Across the three failed judge units:

- 23 response-envelope rows were recorded;
- 9 responses hit exactly 12,000 completion tokens;
- 9 JSON-repair requests were made;
- 5 envelopes had no returned model and no assistant content;
- zero complete judgment files were produced.

The judge prompt is explicit and the validator is straightforward. The practical failure is that the selected judge endpoint did not reliably emit the required exact-cardinality JSON under the observed full-size prompts.

## 5. OpenRouter structured-output capability audit

The current OpenRouter catalog distinguishes the paid and free variants of both NVIDIA models.

As of the audit date:

- `nvidia/nemotron-3-ultra-550b-a55b` advertises `response_format` and `structured_outputs`;
- `nvidia/nemotron-3-ultra-550b-a55b:free` does **not** advertise either parameter;
- `nvidia/nemotron-3.5-lightning` advertises `response_format` and `structured_outputs`;
- `nvidia/nemotron-3.5-lightning:free` does **not** advertise either parameter.

The free endpoints do advertise large context windows and up to 65,536 completion tokens. The failures were therefore not caused by an advertised context-window limit. The experiment itself imposed `max_tokens=12000`, and many failing outputs reached that exact cap.

The live model metadata is available from the [OpenRouter models API](https://openrouter.ai/api/v1/models). OpenRouter's documentation says strict schema enforcement requires a compatible model, `response_format.type=json_schema`, a strict schema, and—when routing—`require_parameters: true`; support should be checked in the model's `supported_parameters` list. See [OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

Experiment 16 sent only:

- model ID;
- messages;
- temperature 0.4;
- `max_tokens=12000`.

It did not send `response_format`, a JSON Schema, or `provider.require_parameters=true`. The system message and prompts requested JSON in natural language, but no provider-level structural constraint was active.

### Suitability conclusion

OpenRouter availability did not imply suitability for this experiment's strict structured-output contracts.

- **Current free judge:** should not be reused for another scientific run. It failed every unit that reached judging and its endpoint does not advertise structured outputs.
- **Current free generator:** it completed many stages, but its unsupported structured-output path produced four semantic audit contradictions, a selector cardinality error, and multiple truncated JSON responses. It is not reliable enough for this exact harness without a successful pre-registered qualification test.
- A paid variant of the same model family or a different model that advertises structured outputs may be more suitable, but either changes the exact model configuration and must not be substituted into the existing preregistration.

## 6. Duplicate ledger sequence identifiers

The raw ledger contains 214 rows but sequence values range only from 1 to 169. Sequence IDs 1–45 each appear twice, yielding 45 duplicate identifiers.

### Exact root cause

`Meter.__init__` always sets `self._seq = 0`. It does not read the maximum sequence already present in `request_ledger.jsonl`. On resume, new events were appended to the existing file beginning again at sequence 1.

The duplicated sequence numbers represent distinct events, not duplicated billing/accounting rows. Unit/arm/stage grouping still recomputes the published budgets exactly. However, `seq` is not a globally unique event identifier and cannot safely be used alone for ordering or joins.

### Safe fix

Before installing the meter, initialize the next sequence from the maximum existing sequence, or use a compound identifier such as `{run_session_id, sequence}`. This is logging/resume infrastructure and does not alter the scientific protocol.

Do not renumber the historical ledger; preserve it and document the collision.

## 7. Non-standard `NaN` values

The main JSON contains bare `NaN` at:

- `statistics.mean_difference_A_minus_B`;
- both elements of `statistics.bootstrap_ci95`.

### Exact root cause

`decide_verdict` returns `math.nan` when there are no analyzable differences. `_write_json` uses Python's default `json.dumps`, whose `allow_nan=True` behavior writes `NaN` even though RFC-compliant JSON does not allow it.

The Markdown correctly renders these values as `n/a`; strict JSON consumers may reject the JSON report.

### Safe fix

For an empty analysis set, serialize unestimable quantities as `null`, and write JSON with `allow_nan=False` so future non-finite values fail loudly. This is a reporting-format correction and does not alter the outcome measure, criterion, or result.

Do not rewrite the original Experiment 16 report. Produce a separately versioned corrected export if one is needed.

## 8. Additional harness findings

### Invalid output evidence is discarded

The harness should preserve rejected content in a separate diagnostic quarantine with:

- unit, stage, arm, and attempt;
- response ID and provider/model identifiers;
- finish reason and native finish reason;
- response-envelope shape;
- rejected assistant content;
- validation exception type and message;
- SHA-256 hashes.

Credentials and authorization headers must never be stored. Diagnostic payloads should be separate from scientific outputs and clearly labeled non-results.

### Invalid-shape retries are underreported

Q2-r3 visibly made five no-content judge requests, but each request row reports `invalid_response_shape_retries=0`. The counter increment occurs in `call_llm` after one wrapped `_request_json` returns and before the next wrapped call starts, so the meter's before/after delta does not attribute it to either request.

This did not affect arm token matching because judge calls are excluded, but it makes the reliability report inaccurate. Retry events should be logged explicitly at the point of retry or summarized at logical-call scope.

### Failure checkpointing is incomplete

Terminal failed judge stages are not checkpointed. Resume therefore retries them. A terminal failure checkpoint should record status and exhausted attempt count so resume does not create extra recovery opportunities.

## 9. Responsibility matrix

| Component | Finding |
|---|---|
| Model | Primary source of contradictory decisions, wrong cardinality, invalid JSON, and excessive output length |
| Prompt | Rules were explicit, but large embedded cards and exact 10-row schemas created demanding long-output tasks; prose alone could not enforce structure |
| JSON parser | Correctly rejected malformed JSON; no evidence it misparsed valid JSON |
| Schema validator | Correctly enforced exact count, field, boolean, ID, and decision-consistency contracts |
| Provider/network | Responsible for Q3-r3 `IncompleteRead` and implicated in Q2-r3 no-content envelopes |
| Harness | Did not request constrained outputs, discarded invalid response content, missed `IncompleteRead` retry, reset ledger sequence on resume, retried failed judge stages after resume, undercounted shape retries, and serialized `NaN` |
| Scientific protocol | Not itself evaluated because no valid matched-and-judged analysis set was produced |

## 10. Fixes that do not change the scientific protocol

These are implementation, observability, or serialization repairs. They do not loosen acceptance rules or alter outcome definitions:

1. Preserve invalid responses in a credential-free diagnostic quarantine.
2. Log full validation exception messages, not only exception class names.
3. Record response ID, routed provider, finish reason, native finish reason, and response shape.
4. Make ledger event IDs resume-safe.
5. Persist terminal failed-stage checkpoints so resume does not grant new attempts.
6. Count invalid-shape retries correctly.
7. Treat `IncompleteRead` as a retryable network/incomplete-body condition under the already declared network retry policy.
8. Serialize unestimable statistics as `null` and enable `allow_nan=False`.
9. Add deterministic unit tests for every parser and validator failure contract.

Although these repairs do not change the scientific question or decision rule, the repaired harness must receive a new code hash and complete validation before another run.

## 11. Changes requiring a newly preregistered study

The following change inference or evaluation behavior and must not be applied to the completed Experiment 16 protocol:

1. Changing either exact model ID, including removing `:free` to use a paid endpoint.
2. Adding `response_format=json_schema`, constrained decoding, response-healing plugins, or `provider.require_parameters=true`.
3. Changing temperature, maximum completion tokens, or reasoning configuration.
4. Changing prompts, schemas, decision rules, or validator strictness.
5. Reducing judge batch size or changing how cards are divided across judge calls.
6. Adding more judge attempts, repairs, fallbacks, or model switching.
7. Allowing `SALVAGEABLE` outputs to pass or weakening exact-count rules.
8. Changing task questions, matched-compute tolerance, primary outcome, or falsification criterion.

The safest path is to label a future run as a new preregistered Experiment 16b or Experiment 17 rather than silently revising Experiment 16.

## 12. Recommended minimal smoke tests before another real run

These tests are engineering qualification only and must not be interpreted as scientific evidence.

### A. Zero-generation metadata gate

For each candidate model and exact endpoint:

1. query the live OpenRouter model record;
2. require both `response_format` and `structured_outputs` in `supported_parameters`;
3. verify required context and completion limits;
4. use `provider.require_parameters=true` so routing cannot silently select an incompatible provider.

Fail the smoke test before spending tokens if any requirement is absent.

### B. Deterministic parser/validator fixtures

Run local fixtures for:

- exact valid payload;
- truncated JSON;
- JSON repaired but wrong count;
- extra or missing fields;
- string values instead of JSON booleans;
- duplicate and unknown IDs;
- `SALVAGEABLE` with 0, 1, 2, and 3 failed critical checks;
- `failure_points` mismatch;
- no-content response envelope;
- `IncompleteRead` and connection reset;
- empty analysis-set serialization.

### C. Structured-output canary

With synthetic, non-scientific cards:

1. request one judgment using a strict JSON Schema;
2. repeat with 5 and 10 cards;
3. verify exact cardinality, IDs, booleans, and reasons;
4. record finish reasons and confirm no response reaches the completion cap;
5. repeat enough times to expose stochastic contract failures before approving a model.

A reasonable minimum gate for a strict scientific harness is 20/20 valid outputs at the largest planned batch size, with zero repairs and zero truncations. The threshold itself should be frozen before comparing candidate models.

### D. Full-size synthetic prompt test

Use dummy cards with the same approximate prompt and output sizes as Experiment 16. This detects failures that a one-row JSON canary will miss. No real Q1–Q3 hypotheses should be used or interpreted.

### E. Resume and fault-injection test

Simulate interruption after every stage and verify:

- no completed call is repeated;
- exhausted failures remain terminal;
- sequence/event IDs remain unique;
- partial invalid data never overwrites a valid checkpoint;
- `IncompleteRead`, timeout, reset, 429, malformed envelope, and invalid content are all logged and handled according to the frozen policy.

### F. Strict artifact test

Parse every `.json` file with a standards-compliant parser that rejects `NaN` and Infinity. Recompute hashes and verify that diagnostic files are excluded from scientific analysis inputs.

## 13. Recommendation

Do not rerun Experiment 16 with the same free model pair and prompt-only JSON enforcement.

First repair the harness-only defects and qualify one or more structured-output-capable endpoint configurations with synthetic smoke tests. At minimum, replace the judge configuration for the next preregistered study. Strongly consider replacing or moving the generator to an endpoint that also advertises structured outputs.

After qualification, freeze:

- exact generator and judge IDs;
- exact provider-routing requirements;
- JSON Schemas and request parameters;
- batch sizes and retry policy;
- complete code and prompt hashes;
- smoke-test acceptance threshold.

Then preregister a new study. The completed Experiment 16 should remain preserved as an inconclusive execution and as evidence that model availability is not equivalent to measurement reliability.

