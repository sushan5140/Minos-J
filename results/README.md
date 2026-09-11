# Results artifacts

This directory contains a compact **verified index of historical metrics** plus figures rendered from those values.

It does **not** contain regenerated raw experiment output. Byte-preserved original outputs are under [`historical/2026-08-04/outputs`](../historical/2026-08-04/outputs).

## Files

- `recovered_results.json` — machine-readable recovered experiment record
- `experiment_5_p4_f2_summary.csv` — selected Experiment 5 headline metrics
- `experiment_6_p4_f1_summary.csv` — selected Experiment 6 headline metrics
- `figures/experiment_5_p4_f2_snapshot.svg` — later visual rendering of the strongest P4-F2 failure case
- `figures/experiment_6_pair_comparison.svg` — later visual rendering of the safest vs most dangerous Experiment 6 pairing

To verify the recovered metadata:

```bash
python scripts/verify_recovered_results.py
```

To regenerate the SVG figures from `recovered_results.json`:

```bash
python scripts/render_recovered_figures.py
```

See [PROVENANCE.md](../PROVENANCE.md) for the historical/source boundary.
