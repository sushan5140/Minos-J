# Korean Historical Research Cases — mechanisms, hypotheses, exact falsification lenses

**WARNING:** These reconstruct prior discussions/outreach, NOT independently replicated findings or all verified novel contributions. Bibliographic details not fully established must be checked from primary publisher sources before reuse.

## 1. Keumjin Lee — AeroCal / aircraft timelines and dense traffic
**Original research theme:** landing/timeline prediction and calibrated uncertainty; exact professor paper/model must be verified.
**Challenge:** individual target flight features may not fully encode interactive congestion and preceding aircraft.
**Counterexample:** two otherwise matched landings with different runway queues and preceding-aircraft constraints.
**Test:** compare conditional coverage, interval width and error while varying interacting traffic at fixed target features; compare traffic-aware model.
**Falsifier:** original method already accounts sufficiently for joint traffic; calibration survives controlled busy conditions.
**Lens:** coupled-system uncertainty; do NOT claim original paper treats flights as independent until proven.

## 2. Young-Bok Joo — KOREATECH project-duration prediction
**Original work:** data-driven software/project duration estimation; canonical article needs verification.
**Challenge:** matching total effort does not imply matching delivery duration if precedence DAG critical paths differ.
**Counterexample:** same tasks/effort in serial versus parallel arrangement.
**Test:** matched total effort/project attributes, vary DAG critical path; measure calendar-time prediction/error with dependency-aware baseline.
**Falsifier:** original method already features sufficient scheduling/dependency representations and remains calibrated.
**Status:** professor responded positively to outreach and concrete 1–2 page proposal was sent; question is not a proven gap.

## 3. Soochahn Lee — Kookmin interactive vessel segmentation
**Original work:** interactive vessel segmentation with correction prompting; verify specific MICCAI paper and actual simulated-click policy.
**Challenge:** idealized oracle/largest-error corrective clicks may not match real clinician actions.
**Counterexample:** clinician clicks a convenient but imperfect location rather than the theoretically optimal error point.
**Test:** same image/click budget/model; compare oracle, human-like and noisy feedback sequence; Dice and correction efficiency.
**Falsifier:** method already models realistic correction sequences and is robust.
**Status:** emailed; open novelty check.

## 4. Hyungi Lee — Kookmin CalibRAG
**Original work:** CalibRAG surrogate LLM/student behavior for estimating assisted-answer quality; verify full NeurIPS paper.
**Challenge:** generation temperature differences may not represent conditional human trust in wrong suggestions.
**Counterexample:** same initial ability, two users who accept/reject confident but incorrect AI advice differently.
**Test:** matched user proficiency and advice correctness/confidence, compare surrogate predictions with observed human reliance.
**Falsifier:** surrogate mechanism already faithfully captures relevant human trust patterns.
**Status:** emailed; potential overlap with existing behavioral modeling.

## 5. Won-Tae Kim — KOREATECH robot digital-twin verification
**Original research theme:** digital-twin-based robotic safety; exact paper needs verification.
**Challenge:** a previously verified environment can become stale after obstacle/layout change.
**Counterexample:** robot safety case remains 'valid' despite newly placed obstacle.
**Test:** timed environmental modifications at fixed robot/verification budget; false-safe decisions and re-verification delay vs selective refresh.
**Falsifier:** existing incremental safety checks recover correct state fast.
**Status:** emailed.

## 6. Kang-Wook Chon — KOREATECH QueCo anomaly detection
**Original work:** reference-driven anomaly detection; exact article and safeguards must be checked.
**Challenge:** repeated contaminated exemplars could make a defect appear normal by consensus.
**Counterexample:** reference pool containing the same previously unseen defect repeatedly.
**Test:** vary reference contamination and defect commonality; assess miss rate vs robust baselines at matched clean training.
**Falsifier:** QueCo already handles contamination without systematic errors.
**Status:** emailed.

## 7. Sungjei Kim — KOREATECH 3D scene graph compression
**Original theme:** compressed spatial scene relations; verify original publication.
**Challenge:** compression may collapse rare directional distinctions.
**Counterexample:** 'A left of B' compressed into generic proximity and fails directional query.
**Test:** fixed relation/graph bit budget; vary rare relation frequency and ask direction-sensitive questions.
**Falsifier:** published representation reliably preserves those semantics.
**Status:** emailed.

## 8. Haeyun Lee — KOREATECH GyroDVD
**Original work:** gyroscope-informed video deblurring; verify specific paper implementation.
**Challenge:** gyro-measured camera motion cannot alone explain independently moving foreground blur.
**Counterexample:** fixed gyro and camera rotation with varied subject motion.
**Test:** evaluate foreground/background separately at fixed gyro; compare motion-aware deblurring baselines.
**Falsifier:** published method already disentangles independent motion at equal quality.
**Status:** emailed.

## 9. Duksu Kim — KOREATECH ECO incremental occupancy octree
**Original theme:** egocentric occupancy mapping with updates; verify source.
**Challenge:** persistent occupied voxels might remain after moved/removed objects.
**Counterexample:** move a chair out of view; map wrongly retains obstacle at old position.
**Test:** fixed sensing coverage, controlled move/remove/reappear sequences; stale voxel duration and map precision.
**Falsifier:** existing eviction/visibility update already solves it.
**Status:** hypothesis shortlisted; specific ECO email NOT confirmed.

## 10. Jinwoo Shin — Ajou Pose6DAug object swapping
**Original work:** geometrically/physically plausible object replacement in manipulation videos; verify exact publication and physical validity criterion.
**Challenge:** matching 6D geometry may not preserve mass, friction, center-of-mass dynamics when robot trajectory is retained.
**Counterexample:** visually same bottle replaced with heavier filled bottle at unchanged gripping force; slipping may occur.
**Test:** same geometry/trajectory, vary mass/friction; physical simulator validity and downstream policy success vs geometry-only.
**Falsifier:** original swapping validates those exact dynamic variables and maintains robustness.
**Status:** shortlisted for outreach, not confirmed mailed.

### Reusable discovery lenses, not reusable proposals
Coupled interactions; oracle vs real human behavior; simulated trust vs actual behavior; stale digital state; misleading consensus; information-loss in compression; sensor cause confusion; geometry vs physical dynamics.

Never automatically resubmit these historical ideas, or treat a professor-response as experimental validation.
