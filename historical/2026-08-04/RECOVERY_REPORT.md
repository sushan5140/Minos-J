# Minos-J historical recovery report

## Scope

This recovery preserves the local Minos-J workspace rooted at:

```text
C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation
```

The directory name records where the project started. The workspace continued to evolve after August 4; later experiments and theory studies retain their own original files and timestamps. Their presence here is not a claim that every file existed on August 4.

The adjacent August 4 workspaces inspected were `as`, `build-a-single-file-html-css`, `realtime-voice-chat`, and `redesign-my-homepage-dashboard-based-on`. No additional Minos-J implementation was found in them.

## Recovered material

| Category | Files | Recovery treatment |
|---|---:|---|
| Source and support files | 59 | 56 Python files plus the original `README.md`, `.env.example`, and `.gitignore`; copied byte-for-byte |
| Experiment outputs | 178 | 88 JSON, 89 Markdown, and 1 text file; copied byte-for-byte |
| Checkpoints | 48 | JSON checkpoints with original relative paths; copied byte-for-byte |
| Run/hash logs | 2 | Original Experiment 5 and 6 first-run hash records; copied byte-for-byte |
| Original figures | 0 | None found |
| Manifest entries | 287 | Every recovered source, output, checkpoint, and log file |

The SHA-256 inventory is [`MANIFEST.sha256`](MANIFEST.sha256). The recovery script compared every copied file with its local origin at recovery time; all 287 matched and no original was altered. `.gitattributes` disables Git text normalization below this historical directory so repository checkout does not rewrite the evidence.

## What was intentionally excluded

- 48 `.npz` feature files derived from WESAD participants.
- Raw or prepared participant datasets under `work/e13_data` and `work/external`.
- Vendored dependencies, interpreter caches, and `__pycache__` directories.

Those exclusions avoid redistributing participant-derived biometric data and third-party datasets, and avoid presenting caches or vendored packages as project source. They are not needed to verify the recovered Experiment 4–7 record. No API key, credential, `.env` file, private key, or token was copied.

Files requiring sanitization: **0**. Because no credential-bearing candidate was found, every included historical file remains byte-identical to its source.

## Integrity findings

The historical project record reports that an architecture refactor preserved 34 pre-existing Experiment 1–7 output files byte-for-byte and records this composite manifest SHA-256:

```text
839E74C7C9B7DE98150F3064BB60EDFF223E322B3828EE92E10134E7A4AAB02E
```

Exactly those 34 output paths are present in this recovery and each is individually protected by the new manifest. Two original first-run hash logs independently verify eight Experiment 5 and 6 files. However, the original 34-line manifest and the exact algorithm used to serialize and hash it were not found. Therefore the historical composite hash is preserved as reported but cannot be independently reproduced from an original manifest. This is corroborated historical evidence, not a newly re-created proof of the old composite hash.

## Experiment 4–7 verification

The repository verifier checks the public record against the original JSON artifacts, including:

- Experiment 4: 9 survivors, 5 patterns, 10 distinguishing experiments, 8 literature sources, effect-size and failure-condition completeness, and no upstream rerun.
- Experiment 5: the 5 × 3 × 2 × 3 × 5 design (450 rows and 90 aggregates), all published headline metrics, 14 persistent failures, 15 severe `n=300` cells, and the `FALSIFIED` conclusion.
- Experiment 6: the 5 × 3 × 3 × 4 × 5 design (900 rows, 180 aggregates, and 45 trends), all published headline metrics, 15 persistent trajectories, and the `STRUCTURAL_FAILURE_CONFIRMED` conclusion.
- Experiment 7: Q1 has 9 PASS and 1 SALVAGEABLE; Q2 has 10 PASS and four recorded rubber-stamp red flags; Stage 6 and Stage 7 contain only PASS hypotheses.

The verifier also caught and corrected one public metadata simplification: Experiment 5's exact historical strategy identifiers are `marginal` and `mondrian_class`.

## Experiment 7 Q3 state

Q3 was not completed. Valid checkpoints exist only for:

```text
Stage 4
Stage 4.1
Stage 4.2
```

There is no valid Stage 4.3 checkpoint, Q3 v4 report, or combined v2/v3/v4 report. The recovered narrative run record reports 11 total retries, including 8 HTTP 429 retries. It also records that the proposed fallback model was not actually contacted because outbound networking was blocked before the call. This recovery does not invent the missing result.

## Dependencies and execution boundary

The recovered Python code uses the standard library plus NumPy. LLM-backed runners require `OPENROUTER_API_KEY` at runtime; no credential is stored here. WESAD-dependent experiments additionally require a separately and legitimately obtained WESAD dataset. The original model stages and numerical experiments were not rerun during recovery.

Safe verification commands are:

```bash
python scripts/verify_recovered_results.py
pytest -q
```

These validate stored evidence and current reference contracts. They do not call OpenRouter or rerun the historical studies.

Recovery verification completed successfully with:

- all 56 recovered Python files parsed without writing bytecode;
- both current reference pipeline tests passed through a direct local runner (the bundled Python did not contain `pytest`; GitHub Actions installs it explicitly);
- four original deterministic validators passed from an isolated temporary copy: base pipeline, enriched pipeline, cross-question analysis, and pattern falsification;
- the figure renderer reproduced the committed SVG files exactly;
- the public/result verifier passed against the historical artifacts; and
- the credential scan passed with zero likely live credentials or private keys.

The isolated copy was necessary because three original validators intentionally write test checkpoints beside themselves. Running them inside `historical/` would have changed the evidence tree. API-backed runners were not executed. Dataset-backed scripts remain syntactically valid but require separately supplied data and were not treated as reproducible from this public-safe archive alone.

## Known missing evidence

- The original 34-output manifest and its serialization procedure.
- A standalone machine-readable retry log for Experiment 7; retry counts survive in the narrative project record.
- Experiment 7 Q3 Stage 4.3 onward and the combined v2/v3/v4 report.
- Original historical chart files; none were found.

No numerical conclusion was invented to fill these gaps.
