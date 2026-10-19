# Meno-J Experiment 13 — Working Theory Update

## Decision

**EXTERNAL_NORMALIZATION_REPLICATION_NOT_SUPPORTED**

The earlier normalization effect did not meet the frozen external-replication standard. The independent cohort showed a smaller accuracy gain (+0.0436), and its paired-subject 95% bootstrap interval included zero. Normalization did reduce full prediction sets by 0.0909 and robustness loss by 0.0374, but normalized coverage was 0.8681—below the preregistered 0.88 safety floor.

## Updated working theory

Subject-relative normalization is a context-sensitive representation intervention, not a generally established repair. It can make predictions sharper, yet sharper predictions are not automatically safer predictions. The two gates must remain separate:

1. **Representation gate:** does the intervention materially improve discrimination across subjects and settings?
2. **Calibration-safety gate:** does it preserve coverage, including for the weakest subjects?

Experiment 13 passed neither complete gate. It produced a modest, heterogeneous representation signal and a useful ambiguity reduction, but it missed both the frozen accuracy threshold and the mean-coverage floor.

## Claim changes

- **Large externally replicable accuracy repair:** not supported.
- **Reduced conformal ambiguity in this external dataset:** supported.
- **Representation improvement implies safe uncertainty repair:** refuted.
- **Same directional effect across protocol versions:** directionally supported, but heterogeneous (+0.0147 V1; +0.0742 V2).
- **Uniform subject benefit:** refuted; 63.64% were nonnegative, with changes from -0.2917 to +0.2292.

## Relation to the J-jump

The J-jump should not mean accepting an imaginative transformation because one metric improves. It should mean generating a constrained leap, extracting measurable consequences, and retaining it only when independent effect-size, heterogeneity, and safety tests survive. This result is scientifically useful because the Meno-J Falsification Engine rejected an attractive partial success.

## Next falsification target

Freeze a new analysis before inspecting associations, then test whether baseline reliability, protocol version, sensor quality, or distribution shift predicts which subjects benefit from normalization. Do not define favorable subgroups after seeing their outcomes.

Independent exact replay: **PASS**.
