# Minos-J Architecture Notes

## Design principle

Minos-J follows an **ignorance-first** approach.

Instead of starting from one answer and refining it until it appears convincing, the system starts by treating the explanation space as unresolved.

The design goal is to make disagreement, uncertainty, and falsification explicit.

---

## High-level pipeline

```text
1. Observation / unresolved question
2. Evidence retrieval
3. Independent reasoning
4. Strict filtering
5. Pattern extraction
6. Rival-hypothesis construction
7. Critique
8. Falsification design
9. Executable / statistical tests
10. Survivor analysis
11. Working-theory revision
```

---

## Why rival hypotheses matter

A single explanation plus self-critique can still remain trapped inside one framing.

Minos-J therefore attempts to construct competing explanations that make meaningfully different predictions.

A useful rival hypothesis must disagree in a way that can be tested.

---

## Why explicit failure conditions matter

A reasoning system can always generate more text explaining why its previous answer was "mostly right."

To prevent that, hypotheses are expected to specify conditions under which they should be considered weakened or falsified.

Examples include:

- effect-size thresholds
- subgroup performance bounds
- coverage failures
- robustness under changed distributions
- executable test failures
- contradictions with independently retrieved evidence

---

## Evaluation problem

A multi-stage reasoning system receives more inference compute than a one-shot baseline.

Therefore a core open question is:

> Does the architecture improve reasoning, or does performance improve simply because the system receives more samples, tokens, or evaluator passes?

Minos-J's evaluation plan therefore emphasizes:

- matched-compute baselines
- ablations
- evaluator reliability checks
- adversarial / OOD cases
- retrieval controls
- repeated-seed stability
- behavior-level rather than prose-level comparison

---

## Reproducibility boundary

Historical experiment outputs and later architecture refactors are treated as separate layers.

The project has used:

- byte-level output preservation
- manifest/hash verification
- compile checks
- credential scanning

This is intended to reduce the risk of unintentionally changing previous evidence while restructuring the system.

The original implementation and canonical architecture artifact are available at:

- [`historical/2026-08-04/source`](../historical/2026-08-04/source)
- [`meno_j_falsification_engine_architecture.md`](../historical/2026-08-04/outputs/meno_j_falsification_engine_architecture.md)

The package under `src/minos_j/` is a smaller later reference implementation, not a replacement for the historical tree.

---

## Current research questions

- How should evaluator reliability be measured in multi-stage LLM reasoning?
- How can genuine falsification be distinguished from persuasive self-critique?
- What controls best separate architecture gains from extra inference compute?
- Can rival generation improve robustness under domain shift?
- When should falsification stages use statistical tests, executable checks, or formal constraints?
- How should failed hypotheses be represented and carried forward without being silently rewritten?
