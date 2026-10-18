# Korean Professor Hypothesis Discovery — Exact Compulsory Rules (v1)

## A. Research provenance
A1 Verify full professor name, current Korean university and department, official faculty page and verified contact.
A2 Prove paper-to-professor identity; avoid common-name ambiguity and misattribution.
A3 Record canonical paper title, authors, venue/year, DOI/arXiv, publisher, code and dataset links, when verified.
A4 READ full method, figures, equations, ablations, limitations, related work, supplementary and available code. Abstract-only review fails.
A5 Trace inputs -> representation -> preprocessing -> prediction/decision -> evaluation and existing defenses.
A6 Independently verify GKS eligibility by university/track/year and any evidence of undergraduate mentorship; do not infer availability.

## B. Hypothesis construction
B1 Phrase: 'Change X while holding Y constant; mechanism Z may fail on measurable Q because assumption A may not hold.'
B2 Examine genuine missing information/observability, dependency structure, sensor reliability, proxy confounding, stale world state, simulation fidelity, uncertainty calibration, non-identifiability.
B3 Invent a precise *labeled hypothetical* controlled counterexample: two observations equivalent to the model, but different in the world.
B4 Isolate mechanism: don't attribute source/sampling problems to compression, acquisition errors to fusion, or downstream policy errors to inference.
B5 Don't force the Professor Lee dependency idea into every paper; transfer the research mindset, not the feature.
B6 Demand matched data, memory, compute, training and sampling budgets; no 'bigger model wins' shortcut.
B7 State exact original baseline, competing state-of-art baseline, minimal intervention/ablation, metrics, statistical uncertainty, and outcome that FALSIFIES the claim.
B8 Prefer software-only public-data experiments, reproducible on modest compute; state unavailable assets honestly.

## C. Adversarial overlap gates — HARD REJECT on failure
C1 Full-text keyword/synonym search for problem and author-discussed limitations.
C2 Read paper's real method, ablations, supplementary experiments, adversarial tests and limitations.
C3 Check code and safeguards that solve the proposed issue under a different name.
C4 Search at least three *mechanism-specific* competing literature queries; read actual methods, not headlines.
C5 Explicitly separate author-admitted limitation, empirically demonstrated failure and our untested hypothesis.
C6 If same remedy exists in original or directly applicable prior work without defensible distinct contribution, REJECT.
C7 If critical original sources inaccessible, mark unverified and DON'T award >=8/10.
C8 Avoid contacted/audited papers and near-duplicates; consult LEDGER.md and past available runs; disclose incomplete deduplication.

## D. Scoring
D1 Architecture/mechanism specificity: 0–25.
D2 Evidence-checked novelty/non-overlap: 0–25.
D3 Falsifiability/experiment discrimination: 0–20.
D4 Plausible scientific contribution: 0–15.
D5 Feasibility/reproducibility: 0–15.
D6 Qualify only if total >=80/100 AND D1 >=20 AND D2 >=20 AND every hard gate passes.
D7 Hypothesis score is NOT empirical confirmation, publication acceptance or guaranteed novelty.
D8 Zero qualifying discoveries is a valid output; never inflate or pad.

## E. Workflow
E1 Screen individual verified professors, not just university lists; deduplicate university + faculty + publication + mechanism.
E2 For each success cite official profile, actual paper sections, existing safeguards, assumption, counterexample, paired experiment, baselines, falsifier, prior art, score breakdown and compute/data constraints.
E3 Distinguish screened / eligible hypothesis / sent outreach / professor response / experimentally validated.
E4 Respect faculty: no unsupported allegations that their research is flawed.
E5 LEDGER updates only with explicit authorization, using source-linked versioned edits.
E6 Never send mail, run experiments, edit repositories or create automation without explicit authorization.
E7 Re-evaluate historic emailed hypotheses whenever fuller methodological evidence undercuts them.

### Failure patterns
- Abstract-only apparent novelty that disappears on reading methodology.
- Confounding sampling, sensor acquisition, model fusion or downstream reasoning.
- Generic accuracy improvements masquerading as new scientific questions.
- Assuming each aircraft is predicted independently without examining original dependencies.
- Treating previously sent outreach emails as validated research discoveries.
