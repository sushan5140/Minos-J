# Minos-J

**An ignorance-first falsification framework for LLM-assisted scientific reasoning.**

Minos-J explores a simple question:

> **Can an AI reasoning system be designed to search for ways its own explanations could fail, rather than merely generating increasingly persuasive answers?**

The project turns uncertain observations into **competing hypotheses, explicit predictions, falsification tests, and revised working theories**. The aim is not to make an LLM sound more confident; it is to make the reasoning process more inspectable and easier to disprove.

---

## Research direction

Many agentic reasoning systems improve an answer through additional sampling, self-critique, or evaluator loops. That creates an important methodological problem:

**Did the architecture actually improve reasoning, or did we simply spend more inference compute and produce a more convincing explanation?**

Minos-J is being developed around that distinction.

Current themes include:

- LLM reasoning and evaluator reliability
- rival-hypothesis generation
- controlled falsification
- matched-compute evaluation
- robustness under subgroup / distribution shift
- evidence grounding and provenance
- explicit failure conditions
- reproducible experiment pipelines

---

## Core loop

```text
Observation / unresolved question
        ↓
Evidence retrieval
        ↓
Independent reasoning
        ↓
Strict filtering
        ↓
Pattern extraction
        ↓
Competing hypotheses
        ↓
Critique + falsification
        ↓
Executable / statistical tests
        ↓
Surviving explanations
        ↓
Revised working theory
```

The important design choice is that hypotheses are expected to **lose** when evidence contradicts them.

A failed hypothesis is therefore a useful result, not an experiment to hide.

---

## Current experimental record

### Experiment 4 — pattern separation and test design

The pipeline reduced:

**9 surviving explanations → 5 competing patterns → 10 distinguishing experiments**

The study was grounded in **8 validated primary sources**.

Each proposed experiment included:

- an explicit prediction
- expected effect size
- minimum evidence / data requirement
- a failure condition
- a statistical or executable test plan

This stage was designed to turn free-form explanation into claims that could actually be challenged.

### Experiment 5 — P4-F2

**Result: finite-sample-only explanation falsified.**

At `n = 300`, the sparse-subgroup + inverse-probability + marginal configuration still showed:

- **coverage gap:** 0.7462
- **minimum group coverage:** 0.1538
- **persistent-failure cells:** 14

The failure persisted despite increased sample size, contradicting the explanation that the observed behavior was only a small-sample artifact.

### Experiment 6 — P4-F1

**Result: structural failure pattern confirmed.**

Safest tested pairing:

- mean gap: **0.0645**
- minimum coverage: **0.8656**
- persistent failures: **0**

Most dangerous tested pairing:

- inverse-probability + marginal
- mean gap: **0.4209**
- minimum coverage: **0.4838**

This supported the interpretation that the failure depended on the structure of the estimator / conditioning setup rather than only random finite-sample variation.

### Experiment 7 v4

- **Q1:** 9 PASS / 1 SALVAGEABLE
- **Q2:** 10 PASS
- **Q3:** valid checkpoints preserved through the completed stages; later execution was stopped by sandbox outbound-network restrictions before the required external API call

The intended next stage for Q3 produces exactly 10 statistical-testability objects containing:

- expected effect size
- effect-size rationale
- minimum-data requirement
- testable prediction
- failure condition
- statistical-test plan

---

## Reproducibility work

During the architecture refactor:

- **34 historical outputs were preserved byte-for-byte**
- manifest/hash verification was used to detect accidental changes
- compilation checks were run
- credential scanning was performed
- historical experiments were not silently regenerated during refactoring

The purpose of these checks is to keep architectural changes separate from changes to experimental evidence.

---

## What Minos-J is trying to test

Minos-J is not based on the assumption that more critique automatically means better reasoning.

The project is specifically interested in separating:

1. **architecture-level gains**
2. **extra inference / sampling**
3. **evaluator bias**
4. **retrieval or evidence leakage**
5. **distribution-specific behavior**
6. **explanations that merely sound more rigorous**

That makes matched-compute controls, adversarial cases, domain shift, and explicit falsification central to the evaluation plan.

---

## Current status

**Research prototype / active investigation.**

The public repository is being assembled from the existing experiment and architecture record. Research artifacts and implementation components will be added incrementally while preserving provenance between historical results and later refactors.

See:

- [Experiment record](docs/EXPERIMENTS.md)
- [Architecture notes](docs/ARCHITECTURE.md)

---

## Research interests connected to this project

- trustworthy AI
- LLM reasoning evaluation
- agentic AI
- falsification and scientific reasoning
- formal / executable verification
- robustness and distribution shift
- uncertainty and calibration

---

## Author

**Susan**  
Prospective AI / Computer Science undergraduate

This is an independent research project in development. Results in this repository should be read as experimental findings from the specified setups, not as universal claims about all LLM or agent systems.
