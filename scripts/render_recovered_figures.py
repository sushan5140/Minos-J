#!/usr/bin/env python3
"""Render simple SVG figures from recovered Minos-J headline metrics.

No historical experiment is rerun. Figures are derived only from
results/recovered_results.json.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "recovered_results.json"
FIGURES = ROOT / "results" / "figures"


def bar_svg(title: str, rows: list[tuple[str, float]], maximum: float = 1.0) -> str:
    width, height = 920, 120 + 90 * len(rows)
    left, bar_w = 280, 560
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="32" y="42" font-family="Arial, sans-serif" font-size="24" font-weight="700">{title}</text>',
        '<text x="32" y="70" font-family="Arial, sans-serif" font-size="13" fill="#555">Rendered from recovered historical metrics; not a rerun.</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = 105 + i * 90
        w = max(0.0, min(1.0, value / maximum)) * bar_w
        parts += [
            f'<text x="32" y="{y+25}" font-family="Arial, sans-serif" font-size="15">{label}</text>',
            f'<rect x="{left}" y="{y}" width="{bar_w}" height="32" rx="5" fill="#eceff3"/>',
            f'<rect x="{left}" y="{y}" width="{w:.1f}" height="32" rx="5" fill="#334155"/>',
            f'<text x="{left+bar_w+12}" y="{y+22}" font-family="Arial, sans-serif" font-size="14">{value:.4f}</text>',
        ]
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    FIGURES.mkdir(parents=True, exist_ok=True)

    e5 = data["experiment_5"]["findings"]
    (FIGURES / "experiment_5_p4_f2_snapshot.svg").write_text(
        bar_svg(
            "Experiment 5 — P4-F2 failure snapshot at n=300",
            [
                ("Coverage gap", e5["sparse_inverse_probability_marginal_gap_n300"]),
                ("Minimum group coverage", e5["sparse_inverse_probability_marginal_min_group_coverage_n300"]),
            ],
        ),
        encoding="utf-8",
    )

    e6 = data["experiment_6"]["findings"]
    (FIGURES / "experiment_6_pair_comparison.svg").write_text(
        bar_svg(
            "Experiment 6 — safest vs most dangerous tested pair",
            [
                ("Safest pair mean gap", e6["safest_pair"]["mean_gap"]),
                ("Safest pair min coverage", e6["safest_pair"]["minimum_coverage"]),
                ("Dangerous pair mean gap", e6["inverse_probability_marginal_mean_gap"]),
                ("Dangerous pair min coverage", e6["inverse_probability_marginal_minimum_coverage"]),
            ],
        ),
        encoding="utf-8",
    )

    print(f"Wrote figures to {FIGURES}")


if __name__ == "__main__":
    main()
