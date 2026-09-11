# Provenance and recovery boundary

Minos-J has two kinds of material in this public repository.

## 1. Recovered historical implementation and evidence

The original implementation, outputs, checkpoints, and selected run logs are preserved byte-for-byte under `historical/2026-08-04/`. The numerical findings and experiment metadata in `results/recovered_results.json` are verified against those originals.

The original working path was:

```text
C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation
```

The directory date identifies the workspace lineage. The workspace continued evolving later in August, so files retain their own experiment identity and timestamps rather than being falsely represented as all created on August 4.

These values are presented as **historical results from the original runs**.

## 2. Current reference / reproducibility code

The Python package under `src/minos_j/` and the utilities under `scripts/` were added to the public repository after the historical runs.

They remain a later, compact reference implementation. They are separate from the now-recovered original source under `historical/2026-08-04/source/`.

Their purpose is to:

- expose the research contracts clearly
- validate the recovered result record
- render figures from recovered metrics
- provide a small inspectable implementation of the hypothesis → falsification → revision logic

This distinction is intentional. Reconstructed code should never be passed off as historical source.

## Historical integrity

The original architecture refactor reported that:

- **34 pre-existing outputs remained byte-for-byte unchanged**
- the output manifest/hash comparison matched
- existing checkpoints were preserved
- compilation checks passed
- credential scanning passed
- no historical experiments were silently rerun during that refactor

All 34 reported output paths are present and individually hashed in `historical/2026-08-04/MANIFEST.sha256`. The original composite manifest was not found, so its recorded SHA-256 is preserved as a historical statement rather than claimed as independently reproduced. See the [recovery report](historical/2026-08-04/RECOVERY_REPORT.md) for file counts, exclusions, missing evidence, and verification limits.
