# Exact, non-generic audit rules (v1)

## Stage A — identity and original work (all compulsory)
**A1.** Find the *current official* USTC/UCAS faculty page. Verify name, institute, track, and a working official contact. Do not conflate the UCAS university with a CAS institute affiliation; establish the exact relationship.
**A2.** Record the actual paper title, authors, venue/year, paper URL/DOI, code URL if any, and paper sections inspected.
**A3.** Reconstruct the actual inference or training pipeline in 4–8 precise steps, including input, latent representation, selection/filtering/compression, output, and claimed safeguards.
**A4.** Cite exact passages/tables/equations that establish each purported assumption. If an assumption is merely inferred, label it an inference.
**A5.** Do not choose a professor merely because a topic sounds interesting. The challenge must refer to a concrete mechanism implemented in their own study.

## Stage B — produce a *discriminating* hypothesis
**B1.** State a single falsifiable proposition: *When X is changed while Y is held constant, component Z will produce measurable error Q because of assumption A.*
**B2.** Distinguish correlation from mechanism: don't blame compression when upstream frame sampling could have removed the content first.
**B3.** Use an equivalence pair: inputs that look equivalent under the model's representation but differ in an outcome that matters (e.g., same aggregate student score/different misconception, same geometry/different mass).
**B4.** Control nuisance variables: texture-only at fixed motion; false-radar-only at fixed camera; same visual rendering with varied hidden geometry; same total effort with varied dependency graph.
**B5.** Name baseline(s) that reproduce the original code/paper settings, one minimum-change ablation, one strong external baseline, and a null/failure test.
**B6.** Keep memory, sampled frames, training budget, or compute fixed whenever the proposed change might otherwise buy accuracy with more resources.
**B7.** Identify what observation would *refute*, not merely support, the proposed hypothesis.

## Stage C — adversarial overlap check (FAIL means do not lock)
**C1.** Search inside the paper for the same problem under alternative names. Authors' awareness and their partial mitigations must be reported, not erased.
**C2.** Inspect *method*, **ablations**, supplementary, evaluation datasets, failure cases and limitations before evaluating novelty. Paper abstract alone never suffices.
**C3.** Search at least 3 precise prior-art formulations and competing systems, not just the proposed coined term. Search “sensor corruption reliability gate”, not just “our novel radar gate.”
**C4.** Existing countermeasure ≠ full solution; identify *exact residual case* with evidence. If evidence insufficient, abstain rather than score 8+.
**C5.** Separate (i) the author's explicit admitted limitation, (ii) an experimentally demonstrated failure, and (iii) our untested conjecture.
**C6.** A proposed improvement already implemented in the same paper or prominent directly applicable prior work is a hard reject unless a genuinely distinct novelty claim is defensible.
**C7.** Track whether claimed weakness is from upstream collection/sampling, core model mechanism, or downstream reasoning. Don't conflate stages.
**C8.** Never upgrade an idea merely because it is intuitively striking, resembles Professor Lee's dependent aircraft timelines, or would be easy to explain in an email.

## Stage D — scientific plan and score
**D1.** Specify dataset/source, contamination/leakage prevention, matching/matched-pair design, intervention, metrics, error bar/confidence intervals, reproducibility, and modest-cost environment.
**D2.** Compare original model vs matched-budget modified model; if code or data absent, mark feasibility uncertainty, no guessed benchmark.
**D3.** Rate in 5 dimensions: architecture specificity 0–25; independently checked non-overlap/novelty 0–25; falsifiable test 0–20; likely contribution 0–15; feasibility 0–15.
**D4.** Qualification requires total **>=80/100**, specificity **>=20/25**, novelty **>=20/25**, and NO hard-reject gate failure. A numerical total cannot override a failed gate.
**D5.** “Score” measures *audited promise*, not evidence that the failure already occurs, or an accepted scientific contribution.
**D6.** If no candidate passes, result is exactly “0 qualified”; never output a rejected hypothesis as a “promising 8/10” concept.

## Stage E — report and reuse
**E1.** Each successful candidate: professor and official page; paper and exact source; Professor Did (mechanism); Hidden Assumption; Our Question; controlled toy example; discrimination test; baseline; existing overlap; novelty gap; explicit falsification outcome; score breakdown; next experimental step.
**E2.** Explicitly list the two professors screened even when 0 qualifies, but don't repeat discarded pitches or padded analysis.
**E3.** Read LEDGER.md before discovery; avoid all known outreach targets and duplicate papers. When uncertain, check old task reports. Do not assume an inaccessible ledger is synchronized.
**E4.** Do not write into GitHub, send mail, start experiments or schedule additional actions without separate explicit authorization.
**E5.** A professor being contactable does not establish CSC funding, availability, or willingness to supervise. Confirm separately.
**E6.** For Chinese faculty with common names, verify the *specific person-paper affiliation* before proposing outreach.
**E7.** Source links must be checked at run time, not invented. If a claim cannot be verified, remove it.

## Anti-patterns learned from MuKV
- “Rare short event may be forgotten” was already adjacent to MuKV's discussed unseen future questions, fine-grained compression, counting weakness and temporal frequency preservation. Generic framing dropped after full-paper audit.
- Apparent forgotten event may actually have been missed by sampling, not compression.
- “Add relationships between frames” is not new if the method already has temporal/segment-level context.
- A vivid example is NOT evidence of a published method's failure.
