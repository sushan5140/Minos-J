# Results artifacts

This directory contains **recovered historical metrics** from the original August 4 Minos-J runs plus figures rendered from those recovered values.

It does **not** contain regenerated raw experiment output.

## Files

- `recovered_results.json` — machine-readable recovered experiment record
- `experiment_5_p4_f2_summary.csv` — selected Experiment 5 headline metrics
- `experiment_6_p4_f1_summary.csv` — selected Experiment 6 headline metrics
- `figures/experiment_5_p4_f2_snapshot.svg` — visual summary of the strongest P4-F2 failure case
- `figures/experiment_6_pair_comparison.svg` — safest vs most dangerous Experiment 6 pairing

To verify the recovered metadata:

```bash
python scripts/verify_recovered_results.py
```

To regenerate the SVG figures from `recovered_results.json`:

```bash
python scripts/render_recovered_figures.py
```

See [PROVENANCE.md](../PROVENANCE.md) for the historical/source boundary.
