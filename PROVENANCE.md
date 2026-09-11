# Provenance and recovery boundary

Minos-J has two kinds of material in this public repository.

## 1. Recovered historical evidence

The numerical findings and experiment metadata in `results/recovered_results.json` were recovered from the original Minos-J/Codex research record created on **2026-08-04**.

The original working path was:

```text
C:\Users\DELL\Documents\Codex\2026-08-04\we-are-starting-a-fresh-implementation
```

The recovered record includes experiment counts, conditions, conclusions, headline metrics, replay status, and historical filenames.

These values are presented as **historical results from the original runs**.

## 2. Current reference / reproducibility code

The Python package under `src/minos_j/` and the utilities under `scripts/` were added to the public repository after the historical runs.

They are **not represented as byte-for-byte copies of the original August 4 implementation**.

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

The exact original output files and source tree are not currently present in this public GitHub repository. If the original local working directory is later recovered, those files should be imported into a clearly labeled `historical/` area with their original hashes preserved.
