# Meno-J Experiment 15 — Validation

**PASS**

- The 19-source literature ledger is internally complete; 18 sources are marked full-text and one publisher source is explicitly partial-only.
- A fresh deterministic replay exactly reproduced all 198 folds and 3,168 heldout observations.
- Training, external calibration, and heldout subjects remained disjoint.
- Risk thresholds, flags, quadrants, and fold aggregates were recomputed.
- The two retained conformal arms exactly match Experiment 14 outcomes.
- The frozen negative decision was preserved: low trust added no material separation among high-confidence windows.
- All outputs decode as UTF-8 and the credential scan passed.
- Primary decision: `CONFIDENCE_TRUST_SUBJECT_SHIFT_SIGNAL_NOT_SUPPORTED`
