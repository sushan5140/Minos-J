# Experiment 18 — Does explicit falsification itself improve mechanism identification?

**Status: DESIGN (not frozen). No live experimental call has been made. The pilot has not run.**

## Question

With the same model, identical information, the same number of calls and approximately matched measured tokens, does an explicit falsification loop identify the planted mechanism more reliably than generic self-critique and revision? And if it does, is the gain due to **testing discriminating predictions** rather than merely **generating rival hypotheses**?

This is question F1+F2 from the [research audit](../RESEARCH_AUDIT_THROUGH_17C.md). Experiments 16, 17 and 17-C could not answer it. They produced no analysable units, and they scored plausibility with an LLM judge rather than correctness against ground truth.

## Design at a glance

| | |
|---|---|
| Tasks | 180 synthetic conformal-undercoverage cases: 6 mechanisms × 30, half containing a persuasive decoy. The generator is deterministic and seeded; the answer key is hidden from every model. |
| Arms | **A** explicit falsification (3 calls) · **C** generic self-critique (3) · **D** rivals without falsification (3) · **B** single pass (1) |
| Model | `claude-sonnet-5` via Claude Code CLI on the Claude Pro subscription, effort low, 8,000-token output cap |
| Scoring | Deterministic string match of the final `mechanism_id` against the planted mechanism. No LLM judge. |
| Primary | Accuracy(A) − Accuracy(C), paired; exact McNemar; paired bootstrap 95% CI; practical margin +10 pp |
| Compute | Calls, output cap, information and revision opportunities are matched exactly for A/C/D. Tokens are measured per attempt. A positive result requires R = tokens(A)/tokens(C) ≤ 1.20. |
| Falsified if | 95% CI upper bound for A−C is below +10 pp (below 0 for the stronger negative result) |

## Files

| Path | Content |
|---|---|
| `PROTOCOL.md`, `protocol.json` | Draft protocol, 29 fields. Frozen only after approval: freezing writes `PROTOCOL.sha256`. |
| `PROMPT_PARITY_AUDIT.md` | Evidence-exposure, vocabulary, format, opportunity, cap and confidence parity |
| `AMENDMENTS.md` | Post-freeze changes (none yet) |
| `source/e18_tasks.py` | Mechanism definitions, seeded case generator, packet renderer, non-LLM reference solvers |
| `source/e18_prompts.py` | Exact prompts, JSON schemas, output validation |
| `source/e18_transport.py` | Claude Code CLI transport with per-attempt accounting; quota/auth → pause |
| `source/e18_runner.py` | Trials, checkpoints, ledger, lock, resume, orphan detection, halts |
| `source/e18_analysis.py` | Deterministic scorer and preregistered statistics (the only module that reads answer keys) |
| `source/e18_validate_results.py` | Independent reconstruction of the final statistics (does not import the analysis module) |
| `source/e18_validate_harness.py` | Fake-CLI validation harness: 23 checks, zero quota |
| `source/e18_protocol.py` | Protocol builder, renderer, freeze and verify |
| `tasks/` | `main_cases_public.jsonl` (180), `pilot_cases_public.jsonl` (12), the answer keys, and `manifest.json` with seeds and hashes |
| `validation/harness_validation.json` | Latest harness result |
| `pilot/`, `results/` | Empty until the pilot and main runs |
| `work/` | Live checkpoints and ledger (git-ignored until the raw-results milestone) |

## Reproduce the non-live parts

```bash
cd experiments/experiment_18/source
python e18_tasks.py              # regenerates tasks; hashes must match tasks/manifest.json
python e18_validate_harness.py   # 23 fake-CLI checks, no Claude calls
python e18_protocol.py --write-draft
```
