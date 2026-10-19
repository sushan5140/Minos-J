# Meno-J Minimal Executable Epistemic Scoring Results

Decision: **EXECUTABLE_PROTOCOL_SUCCESS_ALL_FIVE_STANCES_AND_ADVERSARIAL_GUARDS_PASS**

The engine emits no overall quality score. It asks four independent questions—reject, pursue, permit bounded provisional use, and accept—then assigns a primary stance without allowing strength in one dimension to conceal a failed critical gate.

## Calibration decisions

| Case | Expected | Observed | Match | Independent discriminating groups |
|---|---:|---:|---:|---:|
| C1 — Decorative renaming of an existing account | `REJECT` | `REJECT` | True | 0 |
| C2 — Coherent but non-generative decorative mechanism | `NON_ACCEPT` | `NON_ACCEPT` | True | 0 |
| C3 — Wegener continental mobility assessed at 1924 | `PURSUE` | `PURSUE` | True | 1 |
| C4 — Bounded high-accuracy lookup predictor | `PROVISIONAL_USE` | `PROVISIONAL_USE` | True | 1 |
| C5 — Rigid plate tectonic synthesis assessed at 1968 | `ACCEPT` | `ACCEPT` | True | 4 |

## Why the two middle decisions matter

- **PURSUE** means an idea earns further testing without being called true.
- **PROVISIONAL_USE** means bounded practical utility can be authorized with monitoring and rollback without laundering that utility into explanatory acceptance.
- **NON_ACCEPT** means insufficient support, not a declaration that the proposal is false.

## Mutation tests

| Test | Result | Observed |
|---|---:|---|
| M1 — Post-cutoff evidence cannot be marked contemporaneously available. | `PASS` | AssessmentValidationError |
| M2 — Unknown evidence references fail. | `PASS` | AssessmentValidationError |
| M3 — Duplicate evidence IDs fail. | `PASS` | AssessmentValidationError |
| M4 — Missing contract fields fail. | `PASS` | AssessmentValidationError |
| M5 — Duplicated evidence streams cannot simulate independent convergence. | `PASS` | PURSUE |
| M6 — Unresolved object identity blocks acceptance. | `PASS` | PURSUE |
| M7 — Predictive usefulness does not imply explanatory acceptance. | `PASS` | PROVISIONAL_USE |
| M8 — Mere relabeling is rejected as a J-jump. | `PASS` | REJECT |

## Twenty-rule execution

All valid cases executed A1–A20. The rules remain audit operations, not points in a weighted score.

- **A1_RETENTION_ACCOUNTING** — Account for prior success by at least one declared mode: literal component retention; limiting or approximate derivation; empirical-capability recovery; or a non-retentive explanation of why, how well, and where the old account succeeded and failed.
- **A2_COMPONENT_SCOPING** — Declare the component under evaluation—representation, empirical law, mechanism, ontology, or method—and permit different verdicts for coupled components.
- **A3_COMPRESSION_DIMENSIONS** — Report conceptual, ontological, parameter, and computational complexity separately. A jump may compress principles while increasing derivational or computational work.
- **A4_APPROXIMATION_BOUNDARY** — Specify whether consequences are exact, approximate, idealized, or historically provisional, and state the interactions or conditions that generate deviations.
- **A5_UNDERDETERMINATION** — Allow a temporary observational-equivalence verdict. When current evidence cannot discriminate rivals, record the equivalence class and the new observations or concepts needed to separate it.
- **A6_DISTRIBUTED_LINEAGE_GRAPH** — Represent a proposed J-jump as a lineage graph when route, intervention, ontology, method, and mechanism arise in different agents or periods. Credit only the component and evidence actually supplied by each node.
- **A7_INTERVENTION_MECHANISM_DECOUPLING** — Record separately: intervention effectiveness, transmission route, causal agent, production mechanism, and full etiology. Success at one level raises but does not automatically satisfy another level's warrant.
- **A8_EVIDENCE_TRIANGULATION_LADDER** — For causal J-jumps, map which independent evidence modes support the claim: comparative pattern, intervention, localization, visualization, isolation/characterization, reproduction, re-identification, dose/host response, and alternative elimination.
- **A9_RELATIONAL_CAUSAL_SCOPE** — State whether the causal claim concerns a necessary agent, sufficient agent, contributing cause, route, virulence factor, susceptible host, or environment. Do not use a generic cause label across these roles.
- **A10_DISCOVERY_UPTAKE_OUTCOME_SEPARATION** — Track conceptual discovery, evidential warrant, community uptake, implementation, and health outcome as separate timelines.
- **A11_FORMAL_ONTOLOGY_DECOUPLING** — Audit equations, operational quantities, invariants, and ontology separately; test whether the formal success transports to a rival representation after reinterpretation.
- **A12_CONSTRAINT_MECHANISM_LAYERING** — Allow a well-supported macroscopic constraint and a microscopic mechanism to coexist as different explanatory layers; score each for its own predictions and assumptions.
- **A13_BRIDGE_LAW_REQUIREMENT** — A cross-level J-jump must state mappings between macro variables and micro or ensemble quantities, together with limits, coarse-graining, and independence assumptions.
- **A14_TRANSITION_ROLE_TAXONOMY** — Label a contribution as anomaly, measurement standard, conversion law, constraint, synthesis, or microfoundation before testing whether it is a J-jump.
- **A15_LAYERED_SUCCESSOR_TEST** — Do not force one successor theory when mature science uses compatible layers. Require the proposed architecture to say what each layer explains, predicts, leaves open, and can falsify.
- **A16_HINDSIGHT_FIREWALL** — Partition evidence by availability date and issue a contemporaneous verdict before adding retrospective evidence. Never credit a precursor with later instruments, observations, concepts, or successful descendants.
- **A17_EPISTEMIC_STANCE_LADDER** — Score rejection, non-acceptance, pursuit, provisional use, and acceptance separately. A hypothesis may rationally merit pursuit while rationally failing the acceptance threshold.
- **A18_OBJECT_REDEFINITION_TEST** — Record whether the successor preserves the predecessor's objects or replaces them. If the moving, causal, or measured object changes, treat the relation as transformation rather than simple confirmation.
- **A19_INDEPENDENT_PREDICTION_LEDGER** — For each evidential success, record whether it was used to construct, tune, or independently test the proposal, and whether it discriminates against named rivals jointly or only in isolation.
- **A20_OBSERVABILITY_FRONTIER** — Record which claims were untestable under the available measurement infrastructure and which new instruments, surveys, access, funding, or data-sharing changes expanded the falsification surface.

## Significant findings

- The twenty-rule contract is executable without collapsing epistemic judgment into one compensatory score.
- The engine distinguishes rejection from non-acceptance: an unsupported but coherent idea is not automatically declared false.
- Wegener at the 1924 cutoff is classified PURSUE rather than ACCEPT; later marine evidence cannot leak backward through the hindsight firewall.
- A bounded high-accuracy lookup predictor can receive PROVISIONAL_USE while its explanatory J-jump claim remains unaccepted.
- The 1968 plate architecture reaches ACCEPT only through multiple independent discriminating evidence groups and an explicit object redefinition.
- Duplicated evidence, unresolved object identity, and post-cutoff evidence each prevent a false acceptance upgrade.

## Next stage

**Prospective blind theory benchmark:** Give the frozen scorer unseen theory proposals with evidence packets and compare its decisions with blinded expert judgments and later outcomes.

Constraint: Do not tune thresholds on the evaluation set and do not let hypothesis-generation quality define the score.
