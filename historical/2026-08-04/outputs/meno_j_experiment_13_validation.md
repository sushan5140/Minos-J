# Meno-J Experiment 13 — Validation

**PASS**

- The independent dataset archive passed size, SHA-256, member-count, and full CRC checks.
- All 33 subject feature checkpoints passed hash, shape, label-balance, and feature-name checks.
- A fresh deterministic replay exactly reproduced all 198 fold rows without runtime warnings.
- Training, external calibration, and test subjects are disjoint in every fold.
- Onboarding and test windows are disjoint, balanced, and complete; onboarding labels are not used.
- Both arms use identical splits and every conformal rank independently recomputes to 232.
- Frozen decision rules and the working-theory update match the scientific report.
- All required outputs decode as UTF-8 and the credential scan passed.
- Primary decision: `EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED`
