# CSC Professor Discovery — auditable research protocol

**Scope:** University of Science and Technology of China (USTC) and University of Chinese Academy of Sciences (UCAS). **Audience:** future hourly research runs for Syeda Subhana's CSC outreach. **Status:** methodology reference, not a collection of proven discoveries.

## Required reading order on EVERY run
1. Read this README in full.
2. Read [PROTOCOL.md](PROTOCOL.md) in full. Treat its gates as binding.
3. Read [SEVEN_CASES.md](SEVEN_CASES.md) in full; these are historical examples, **not seven established novel breakthroughs**.
4. Read [LEDGER.md](LEDGER.md) for already-audited names/papers and exclusions.
5. Fetch the professor's current official faculty page AND the actual new paper's full text, supplementary, references, and code when available. Do not claim a source was inspected unless it was.
6. Before a positive report, explicitly cite original paper section/equation/table and prior-art sources. Never manufacture verification.

If any file is unavailable, state the missing provenance and do not substitute guessed memory. Never silently overwrite the ledger or call an untested hypothesis a result.

## Per-run contract
- Screen **exactly two distinct professors**, preferably one at USTC and one at UCAS. Professor identity, current affiliation and official email must be verified, not inferred from a shared surname.
- Discover hypothesis candidates internally, then independently falsify them with existing-paper methodology, ablations, limitations, supplementary material, code, and competitive prior art.
- Report **only >=80/100 candidates** that pass all compulsory gates. If none, state **0 qualified hypotheses** and report the two professors screened without describing rejected hypothesis pitches.
- Keep *screened* distinct from *qualified*; two professors per run does **not** mean two successes.
- Keep controlled test feasible for modest software-only resources; no unapproved paid APIs.
- Never automatically email professors, generate commitments on anyone's behalf, or rewrite an existing locked proposal.

## Core mindset
Find the *hidden assumption in the research representation* and construct the smallest fair case in which it would cease to hold. The correct idea is not necessarily “add dependencies”; it may challenge observability, confidence, equivalence, sensor reliability, temporal linkage, measurement bias, or information retention.

## Important limitations
This repository cannot by itself guarantee persistent deduplication: scheduled runs must be able to **read it live**, and cannot update the ledger without write authorization. When a run cannot access the repo or a reliable prior-run ledger, explicitly say deduplication is incomplete. Use unique university + professor + paper DOI/arXiv identifiers.

## Research ethics
Quotes and bibliographic claims need traceable sources. Label every hypothetical example *thought experiment* unless tested; no invented performance, failures, citations, experiments, or contacts.

Maintainer: research playbook stored in Minos-J as a separate directory; this folder does not modify Minos-J experiments.
