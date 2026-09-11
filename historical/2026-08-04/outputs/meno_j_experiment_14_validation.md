# Meno-J Experiment 14 — Validation

**PASS**

- A fresh deterministic replay exactly reproduced all 396 fold rows.
- All four arms used identical subject, onboarding, and test splits.
- Training, external calibration, and held-out subjects were disjoint.
- Marginal and class-Mondrian score counts and conformal ranks were recomputed.
- Class conditioning did not alter classifier probabilities or accuracy.
- Both marginal arms exactly matched their Experiment 13 counterparts.
- All frozen decision checks and the working-theory update match the evidence.
- All outputs decode as UTF-8 and the credential scan passed.
- Primary decision: `CLASS_CONDITIONAL_REPAIR_NOT_SUPPORTED`
