# Seven historical CSC outreach cases — provenance and synthesis

**Status:** These are seven hypotheses that were *locked for outreach* and emailed, not seven experimentally confirmed research results or independently validated 8+/10 novelties. Their exact original email questions are summarized below. For every new run use them as *examples of hypothesis construction*, not a library of reusable/verified gaps.

## 1. Zhenya Huang — student simulation / ability-aware LLM learner modeling (USTC)
- **Original work:** simulate students or learners with LLMs and cognitive/ability modeling to represent different learning behaviors. Original outreach focused on fidelity of LLM-simulated student misconceptions.
- **Mechanism/representation interrogated:** learner proficiency/ability representation and observed overall correctness.
- **Thought experiment:** Student A and Student B score equally; A repeatedly applies the wrong rule, B guesses on unfamiliar material.
- **Our inferred hidden assumption:** matching a learner's apparent proficiency is enough to reproduce *conditional misconception patterns*.
- **Proposed experiment:** pair real and simulated learners at similar measured proficiency; evaluate conditional item-level errors, misconception clusters and downstream instructional selection; test misconception-conditioned surrogate against paper baseline.
- **Origin of hypothesis:** *aggregate-equivalence inversion*: equal average score ≠ equal learning process.
- **Competing-work safeguard:** the original framework includes richer cognitive information than a single score. Explicitly check its cognitive-profile variables before claiming uncovered misconception modeling.
- **Paper bibliographic URL:** NOT sufficiently preserved in historic outreach record; must resolve official title and source afresh before reusing.
- **Original outreach:** huangzhy@ustc.edu.cn — sent 2026-10-12 (historical reference only).

## 2. Enhong Chen — RAPID structured long-form generation (USTC)
- **Original work:** RAPID produces coordinated document sections using an explicit planning/dependency structure.
- **Mechanism interrogated:** ordering sections using a DAG / dependency planning framework.
- **Thought experiment:** section A's definition depends on a decision in B, but B's argument also depends on constraints fixed by A.
- **Our inferred assumption:** a directed acyclic, primarily one-way dependency plan expresses every necessary long-document constraint without reconciliation.
- **Experiment:** introduce genuinely reciprocal cross-section constraints and compare published RAPID with minimal iterative repair; measure logical contradictions and dependency satisfaction while holding context and token budget constant.
- **Origin:** *structure-class mismatch*: model assumes one-way DAG, task may include cycles.
- **Overlap warning:** paper already models dependencies; proving absence of cycle handling and evaluating external work is compulsory.
- **Paper bibliographic URL:** NOT sufficiently preserved in historic outreach record; verify RAPID citation from primary source.
- **Original outreach:** cheneh@ustc.edu.cn.

## 3. Tong Zhang — Self-Ensembling Gaussian Splatting (SE-GS), sparse-view novel-view synthesis (UCAS)
- **Original work:** SE-GS reconstructs/views sparse-observation 3D scenes via Gaussian splatting and self-ensemble/uncertainty-aware components.
- **Mechanism interrogated:** rendered-view agreement and geometry regularization provide quality signals.
- **Thought experiment:** two geometries reproduce a similar small collection of 2D views while differing in a hidden surface.
- **Our hypothesis:** *low rendered disagreement may coexist with incorrect latent geometry*, particularly under sparse observations.
- **Experiment:** controlled paired ambiguous geometry scenes; compare actual geometric error with self-ensemble uncertainty; test independent geometry diagnostic only if mismatch exists.
- **Origin:** *measurement-vs-latent distinction*: plausible observations do not uniquely determine hidden structure.
- **Overlap warning:** existing SE-GS geometry regularization must be understood first; confidence-calibration novelty not assumed.
- **Paper title:** Self-Ensembling Gaussian Splatting for Few-Shot Novel View Synthesis (verify definitive record).
- **Original outreach:** tongzhang@ucas.ac.cn.

## 4. Wei Zhai — EMoTive event-based motion perception (USTC)
- **Original work:** event-camera motion estimation with mechanisms that account for event-information density.
- **Mechanism interrogated:** event density as motion-relevant evidence under variable observation conditions.
- **Thought experiment:** identical object motion generates many events on high-contrast texture, few events on low-contrast texture.
- **Our hypothesis:** *appearance-driven changes to event generation may confound inferred physical motion even at identical motion*.
- **Experiment:** render paired event streams with identical trajectory but changed texture/contrast/lighting; compare motion estimates and density-aware safeguards.
- **Origin:** *proxy-signal confounding*: input signal magnitude ≠ underlying physical variable.
- **Overlap warning:** EMoTive already adapts to event density. Test only the residual not covered by the mechanism.
- **Paper bibliographic URL:** historical email did not preserve canonical primary link; resolve afresh.
- **Original outreach:** wzhai056@ustc.edu.cn.

## 5. Xiaohui Cai — PI-HMR in-bed human reconstruction from pressure signals (USTC)
- **Original work:** recover body pose in bed from pressure observations, with temporal/motion context.
- **Mechanism interrogated:** observability of 3D body arrangement from distributed pressure patterns.
- **Thought experiment:** two physically different poses/contact conditions produce very similar pressure distributions.
- **Our hypothesis:** *a unique/high-confidence pose prediction may be underdetermined by the observed pressure, even with some temporal evidence*.
- **Experiment:** physically plausible matched-pressure cases, isolate the extent to which temporal histories disambiguate, evaluate calibrated multi-hypothesis estimates.
- **Origin:** *inverse problem non-identifiability*: same measured output can arise from multiple hidden causes.
- **Overlap warning:** paper explicitly discusses depth ambiguity and temporal context. Show the residual.
- **Paper bibliographic URL:** not fully preserved; resolve from primary work.
- **Original outreach:** caixiaohui@ustc.edu.cn.

## 6. Libo Zhang — TRACT / Attention to Trajectory, ICCV 2025 (CAS-affiliated researcher; confirm precise UCAS supervision)
- **Original work:** Attention to Trajectory: Trajectory-Aware Open-Vocabulary Tracking uses trajectory-level information for persistent tracking.
- **Mechanism interrogated:** historical trajectory coherence as identity evidence under occlusion.
- **Thought experiment:** visually similar people cross and disappear behind a pillar; two smooth trajectory continuations are plausible, and the wrong assignment can become self-reinforcing.
- **Our hypothesis:** *a coherent stored trajectory can be confidently associated with the wrong object during ambiguous crossings*.
- **Experiment:** identity-controlled crossings, isolate occlusion duration and visual similarity; measure ID switches, error propagation, and reliability-gated history baseline.
- **Origin:** *correlated-history failure*: consistency of a hypothesis ≠ correctness of its identity.
- **Overlap warning:** identity consistency is already a target of the paper and existing trackers; benchmark against safeguards.
- **Paper bibliographic URL:** verify ICCV record directly before future claims.
- **Original outreach:** libo@iscas.ac.cn.
- **Affiliation caution:** ISCAS address is NOT automatically evidence of appointment at UCAS. Verify status and supervision before counting as UCAS.

## 7. Yanyong Zhang — RaCFormer radar-camera fusion (USTC)
- **Original work:** radar-camera fusion using radar-guided depth and temporal fusion for perception.
- **Mechanism interrogated:** using radar information to improve visual depth/perception.
- **Thought experiment:** camera image remains reliable while multipath/interference creates *plausible but false* radar returns. “Radar present” does not mean “radar correct.”
- **Our hypothesis:** *plausible corrupted radar may degrade an otherwise reliable camera prediction through fusion*.
- **Experiment:** hold camera fixed, inject controlled false-but-plausible radar returns, compare camera-only, original fusion, and calibrated reliability-gating baselines.
- **Origin:** *available vs trustworthy evidence*: signal availability ≠ evidential reliability.
- **Overlap warning:** RaCFormer already includes temporal/radar-camera fusion safeguards; audit exact robustness tests and relevant corruption-aware fusion prior art.
- **Paper bibliographic URL:** must resolve canonical primary source; original outreach preserved name and mechanism only.
- **Original outreach:** yanyongz@ustc.edu.cn.

## Seven distinct hypothesis-generation lenses
1. Aggregate score hides conditional behavior (Huang).
2. Representation excludes reciprocal structural constraints (Chen).
3. Observed 2D consistency hides latent 3D error (Tong Zhang).
4. Measurement proxy confounds true physical variable (Wei Zhai).
5. Inverse mapping is non-identifiable (Xiaohui Cai).
6. Internally consistent history can be wrongly associated (Libo Zhang).
7. Available sensor may be untrustworthy (Yanyong Zhang).

**Do not** turn these into generic repeated templates or reuse the same professor. First understand the next paper's actual implementation and own failure analyses.
