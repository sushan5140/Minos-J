# Experiment 18 — prompt parity audit

**Status: completed before freeze (2026-10-01). Checked by harness test `06_prompt_parity` (PASS).**

Purpose: Arm A must not receive more factual information, more persuasive framing, more reasoning opportunities or a different answer format than the control arms. The prompts may differ **only** in the reasoning procedure being tested.

## How every prompt is assembled (identical for all arms)

```
system:  "You are a careful scientific reasoner. Return only JSON that matches the required schema."
user:    COMMON_HEADER
         mechanism vocabulary (six mechanisms: description, marker, intervention, series; identical text)
         evidence packet (identical per case; mechanism row order seeded per case, identical across arms)
         [this trial's own previous-step outputs, verbatim JSON]          <- calls 2-3 only
         STEP INSTRUCTION                                                  <- the only arm-specific text
         "Return JSON only, matching the provided schema exactly."
```

The harness removes the step instruction from each of the 10 (arm, call) prompts for a case and confirms the remainders are **byte-identical** across all arms.

## Checklist

| Dimension | A (falsification) | C (self-critique) | D (rivals, no falsification) | B (single pass) | Parity |
|---|---|---|---|---|---|
| Evidence exposure | full packet, every call | same | same | same, one call | ✔ identical bytes |
| Mechanism vocabulary | all six, every call | same | same | same | ✔ identical bytes |
| Each mechanism's two discriminating predictions (in the vocabulary) | shown | shown | shown | shown | ✔ information parity: every arm knows what each mechanism predicts; only A is **instructed to test** the predictions |
| Answer format (final call) | `FINAL_SCHEMA`: mechanism_id + probabilities over all six + justification | same schema | same schema | same schema | ✔ same object (harness asserts) |
| Confidence requirement | calibrated probability for every mechanism | same | same | same | ✔ |
| Number of model calls | 3 | 3 | 3 | 1 | A = C = D. B is a secondary efficiency reference only. |
| Revision opportunities | call 3 sees calls 1–2 | call 3 sees calls 1–2 (call 1 already commits a diagnosis, call 2 critiques it) | call 3 sees calls 1–2 | none | ✔ equal for A/C/D |
| Output-token cap | 8,000 per call | same | same | same | ✔ same CLI setting |
| Effort, model, flags | `claude-sonnet-5`, effort low | same | same | same | ✔ |
| Retries / repair | ≤4 transient retries; exactly 1 repair per logical call, fixed sentence | same | same | same | ✔ same code path |
| Rival count | 4 (step 1) | — | 4 (step 1) | — | ✔ A = D |
| Step-3 instruction | identical text | identical text | identical text | — | ✔ byte-identical |

## Instruction length (characters)

| Call | A | C | D | max/min |
|---|---:|---:|---:|---:|
| 1 | 244 | 237 | 213 | 1.146 |
| 2 | 219 | 185 | 208 | 1.184 |
| 3 | 140 | 140 | 140 | 1.000 |

The shared prompt body is about 3,500 characters, so instruction differences are under 1.5% of the prompt. The preregistered parity limit is max/min ≤ 1.20 per call index. Before this audit, C's step-1 instruction was 33% shorter than A's. It was lengthened with neutral wording that adds no information ("of the subgroup's under-coverage", "that refers to the diagnostics").

## Wording review (persuasiveness and domain information)

- **No instruction contains domain facts, hints about decoys, or statements about which evidence is reliable.** The only domain content anywhere is the shared vocabulary and packet.
- **A's distinctive words** are procedural: "discriminating predictions", "test … one by one", "supports or contradicts", "eliminate".
- **C's distinctive words** are procedural: "critique", "mistakes in your reasoning", "overlooked or misread", "alternative explanations". C is explicitly invited to reconsider alternatives, so it is a strong generic-revision control, not a strawman.
- **D's distinctive words** are procedural: "rationale", "overall plausibility", "one overall judgement per rival rather than testing predictions one by one". The last clause is needed to keep D from turning into A, and it is the only negative instruction in any arm.
- **No arm is told the task contains decoys.**

## Known, accepted asymmetries (inherent to the arm definitions)

1. **C commits to a diagnosis at step 1; A and D do not.** This is the definition of generic self-critique (diagnose → critique → revise).
2. **A's step-2 output format** (a prediction-by-prediction verdict table) is the treatment itself.
3. **Previous-step outputs differ in content and length across arms**, because they are each arm's own reasoning. Their token cost is measured and reported; the compute-parity gate (R ≤ 1.20) bounds how much extra processing A may receive before a positive result is disqualified.

## Answer-key isolation

The runner, prompt builder and transport never open an answer-key file; the harness checks the source files statically. `build_prompt` raises if a case object contains any key field. Public case objects contain only `case_id`, `packet` and `packet_sha256`. Scoring happens only in `e18_analysis.py`, only after every trial is terminal (harness test 19).
