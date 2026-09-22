# Experiment 16 (matched compute) — how to run it later

Experiment 16 is the matched-compute comparison you asked for as "Experiment 8". It has its own number because Experiment 8 (rare-subgroup frontier) through Experiment 15 already exist in this folder.

Current state: the harness has only been tested with a deterministic fake model. Files under `outputs/harness_validation/experiment_16/` are harness checks, not results.

## 1. Required environment variables

Put these in a file named `.env` in this folder. `.env` is already in `.gitignore`.

```text
OPENROUTER_API_KEY=<your OpenRouter key>
OPENROUTER_MODEL=<generator model id, used by BOTH arms>
MINOS_J_JUDGE_MODEL=<judge model id, must be DIFFERENT from OPENROUTER_MODEL>
```

- `OPENROUTER_API_KEY` is required. The runner never prints it.
- `OPENROUTER_MODEL` is optional. If you leave it out, the runner uses the historical default `nvidia/nemotron-3-ultra-550b-a55b:free` from `schema.py`, which keeps continuity with Experiments 1, 2 and 7.
- `MINOS_J_JUDGE_MODEL` is required. The runner refuses to start if it matches the generator model.

## 2. Provider and model configuration

- **Provider:** OpenRouter, through the unchanged historical `llm_client.py`:
  - temperature 0.4
  - max_tokens 12000
  - the same system message
  - the same retry and JSON-repair policy
- **Generator:** one model id for both arms, taken from `OPENROUTER_MODEL`.
  - Free-tier models hit repeated HTTP 429 errors in Experiment 7.
  - A paid model id makes a 9-unit run much more likely to finish.
- **Judge:** use a model from a different family than the generator.
  - Any id listed at https://openrouter.ai/models will work.
  - Check that the id is still listed before you run.
- **Retrieval:** none. The v4 pipeline has no retrieval stage, so both arms get only the research question.
- **Size of the run:** 3 questions × 3 replicates = 9 units.
  - Arm A makes about 7–9 calls per unit.
  - Arm B makes about the same number of tokens' worth of calls.
  - The judge makes about 2 calls per unit.
  - Expect roughly 150–200 model calls in total.
  - Token use depends on the model, likely somewhere around 1–2 million tokens in total. Check your OpenRouter spend limit first.

## 3. Exact commands (Windows, from this folder)

```powershell
cd C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation

# optional: re-check the harness with the fake model (no key, no tokens)
py work\validate_experiment_16_matched_compute.py

# no-token config and connectivity check
py run_experiment_16_matched_compute.py --preflight

# the real run (resumable: re-run the same command after any interruption)
py run_experiment_16_matched_compute.py --run
```

- If `py` is not available on your machine, use `python` instead.
- **Do not run `--write-protocol` again.** The protocol is already frozen, and `--run` refuses to start if the protocol on disk differs from the one in the code.
- **Resuming:** checkpoints are saved per unit, per arm and per stage under `work\experiment_16_checkpoints\`. Re-running the same command continues from where it stopped.
- **Starting over:** delete that folder.

## 4. Expected output files (real run)

All of these are in `outputs\`:

| File | Content |
|---|---|
| `meno_j_experiment_16_preregistered_protocol.json` / `.md` | Frozen before any call (already present) |
| `meno_j_experiment_16_matched_compute.json` | Full report: rule, per-unit budgets, metrics, statistics, verdict, anomalies |
| `meno_j_experiment_16_matched_compute.md` | Readable version of the same report |
| `meno_j_experiment_16_matched_compute_raw_units.jsonl` | One row per unit, including both arms' final cards |
| `meno_j_experiment_16_matched_compute_raw_requests.jsonl` | Every model request: arm, stage, role, tokens, retries, cost |
| `meno_j_experiment_16_matched_compute_judgments.jsonl` | Every blinded card with its judge verdict and the unblinding key |
| `meno_j_experiment_16_matched_compute_aggregate.csv` | Per-unit metrics for both arms |
| `meno_j_experiment_16_matched_compute_budget_accounting.csv` | Per-unit, per-arm compute (A, B and the excluded judge) |
| `meno_j_experiment_16_reproducibility_summary.json` / `.md` | Hashes of the protocol, code and outputs |

## 5. How to confirm the run completed correctly

1. The console ends with `Verdict: <one of the four preregistered verdicts>`:
   - `ARCHITECTURE_ADVANTAGE_SURVIVED`
   - `ARCHITECTURE_ADVANTAGE_NOT_SUPPORTED`
   - `BASELINE_SUPERIOR_ARCHITECTURE_NOT_SUPPORTED`
   - `INCONCLUSIVE_INSUFFICIENT_MATCHED_UNITS`

   It must not say `HARNESS_VALIDATION_ONLY...`.
2. In `meno_j_experiment_16_matched_compute.md`, check the units:
   - "Unit status" shows 9 units.
   - Ideally all 9 units are `COMPLETE`.
   - "Budget-matched complete units" is at least 6. Otherwise the verdict is automatically `INCONCLUSIVE...`.
3. Check the budget table:
   - The "Eval A/B" column reads `1/1` on every unit.
   - "B/A" is between 0.85 and 1.15 on matched units.
4. Check the report fields:
   - `protocol_deviation` is `none`.
   - `generator_model` and `judge_model` are different.
5. The "Anomalies and failure cases" section lists every failed unit, invalid sample, missing-usage request and possible unblinding. Read it before interpreting the verdict.
6. Run `py work\validate_experiment_16_matched_compute.py` again. It should still print `Harness validation: PASSED`. This re-checks the harness and hashes every historical file before and after its own run. It does not replace your own check that the Experiment 8–15 files still have their original dates and sizes.
7. Send the `outputs\meno_j_experiment_16_*` files back for analysis.
