# Meno-J Theory Study 6 Protocol

**Objective:** Test whether the twenty-rule historical contract can produce distinct, auditable reject, non-accept, pursue, provisional-use, and accept decisions without a compensatory scalar score.

**Status:** `FROZEN_BEFORE_CALIBRATION_EXECUTION`

## Decision meanings

- **REJECT:** The proposal is refuted, incoherent, or only relabels the problem without new reach or vulnerability.
- **NON_ACCEPT:** The proposal is not accepted and presently lacks enough generativity or testability to justify prioritized pursuit; it is not claimed false.
- **PURSUE:** The proposal changes the representation, reaches beyond the old account, and exposes a feasible failure path, but evidence is not yet sufficient for acceptance.
- **PROVISIONAL_USE:** A bounded practical use is warranted with monitoring and rollback even though the explanatory or J-jump claim is not accepted.
- **ACCEPT:** All explanation gates pass, the core J-jump obligations pass, rivals are named, and at least two independent evidence groups discriminate at the dated cutoff.

## Non-scalar rule

No aggregate score is computed. A preference or strength in one dimension cannot compensate for a failed critical gate.

## Predeclared calibration

- C1: `REJECT`
- C2: `NON_ACCEPT`
- C3: `PURSUE`
- C4: `PROVISIONAL_USE`
- C5: `ACCEPT`

## Mutation tests

- Post-cutoff evidence cited as contemporaneous must fail validation.
- Unknown evidence IDs must fail validation.
- Duplicate evidence IDs must fail validation.
- Missing required assessment fields must fail validation.
- Duplicating one evidence stream must not satisfy independent convergence.
- An unresolved predecessor/successor object relation must block acceptance.
- Bounded predictive usefulness must not imply explanatory acceptance.
- Mere relabeling must be rejected as a J-jump.
