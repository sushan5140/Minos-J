#!/usr/bin/env python3
"""Render documented SVG figures from recovered Minos-J metrics, without rerunning experiments."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "recovered_results.json"
FIGURES = ROOT / "results" / "figures"


def experiment_5_svg(findings: dict[str, float]) -> str:
    gap = findings["sparse_inverse_probability_marginal_gap_n300"]
    coverage = findings["sparse_inverse_probability_marginal_min_group_coverage_n300"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="330" viewBox="0 0 920 330" role="img" aria-labelledby="title desc">
<title id="title">Experiment 5 P4-F2 failure snapshot at n=300</title>
<desc id="desc">Recovered historical metrics, not a rerun. Coverage gap {gap:.4f} and minimum group coverage {coverage:.4f} for sparse subgroup plus inverse probability plus marginal conditioning.</desc>
<rect width="920" height="330" fill="white"/>
<text x="32" y="42" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#0f172a">Experiment 5 — P4-F2 failure snapshot at n=300</text>
<text x="32" y="68" font-family="Arial,sans-serif" font-size="13" fill="#64748b">Recovered historical metrics · sparse subgroup + inverse-probability + marginal</text>
<text x="32" y="133" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Coverage gap</text>
<rect x="280" y="108" width="560" height="36" rx="6" fill="#e2e8f0"/>
<rect x="280" y="108" width="{gap * 560:.1f}" height="36" rx="6" fill="#334155"/>
<text x="853" y="132" font-family="Arial,sans-serif" font-size="14" fill="#0f172a">{gap:.4f}</text>
<text x="32" y="223" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Minimum group coverage</text>
<rect x="280" y="198" width="560" height="36" rx="6" fill="#e2e8f0"/>
<rect x="280" y="198" width="{coverage * 560:.1f}" height="36" rx="6" fill="#334155"/>
<text x="853" y="222" font-family="Arial,sans-serif" font-size="14" fill="#0f172a">{coverage:.4f}</text>
<line x1="784" y1="94" x2="784" y2="254" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5 5"/>
<text x="748" y="278" font-family="Arial,sans-serif" font-size="12" fill="#64748b">0.90 target coverage reference</text>
<text x="32" y="307" font-family="Arial,sans-serif" font-size="12" fill="#64748b">Historical conclusion: finite-sample-only explanation falsified.</text>
</svg>'''


def experiment_6_svg(findings: dict[str, object]) -> str:
    safe = findings["safest_pair"]
    assert isinstance(safe, dict)
    safe_gap = safe["mean_gap"]
    safe_coverage = safe["minimum_coverage"]
    dangerous_gap = findings["inverse_probability_marginal_mean_gap"]
    dangerous_coverage = findings["inverse_probability_marginal_minimum_coverage"]
    assert all(isinstance(value, (int, float)) for value in (safe_gap, safe_coverage, dangerous_gap, dangerous_coverage))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="500" viewBox="0 0 920 500" role="img" aria-labelledby="title desc">
<title id="title">Experiment 6 safest versus most dangerous tested pair</title>
<desc id="desc">Recovered historical metrics, not a rerun. Safest pair mean gap {safe_gap:.4f} and minimum coverage {safe_coverage:.4f}. Most dangerous inverse-probability plus marginal pair mean gap {dangerous_gap:.4f} and minimum coverage {dangerous_coverage:.4f}.</desc>
<rect width="920" height="500" fill="white"/>
<text x="32" y="42" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#0f172a">Experiment 6 — safest vs most dangerous tested pair</text>
<text x="32" y="68" font-family="Arial,sans-serif" font-size="13" fill="#64748b">Recovered historical metrics · structural-failure study</text>

<text x="32" y="133" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Safest pair mean gap</text>
<rect x="300" y="108" width="520" height="34" rx="6" fill="#e2e8f0"/>
<rect x="300" y="108" width="{safe_gap * 520:.1f}" height="34" rx="6" fill="#334155"/>
<text x="835" y="131" font-family="Arial,sans-serif" font-size="14">{safe_gap:.4f}</text>

<text x="32" y="213" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Safest pair min coverage</text>
<rect x="300" y="188" width="520" height="34" rx="6" fill="#e2e8f0"/>
<rect x="300" y="188" width="{safe_coverage * 520:.1f}" height="34" rx="6" fill="#334155"/>
<text x="835" y="211" font-family="Arial,sans-serif" font-size="14">{safe_coverage:.4f}</text>

<text x="32" y="293" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Dangerous pair mean gap</text>
<rect x="300" y="268" width="520" height="34" rx="6" fill="#e2e8f0"/>
<rect x="300" y="268" width="{dangerous_gap * 520:.1f}" height="34" rx="6" fill="#334155"/>
<text x="835" y="291" font-family="Arial,sans-serif" font-size="14">{dangerous_gap:.4f}</text>

<text x="32" y="373" font-family="Arial,sans-serif" font-size="15" fill="#0f172a">Dangerous pair min coverage</text>
<rect x="300" y="348" width="520" height="34" rx="6" fill="#e2e8f0"/>
<rect x="300" y="348" width="{dangerous_coverage * 520:.1f}" height="34" rx="6" fill="#334155"/>
<text x="835" y="371" font-family="Arial,sans-serif" font-size="14">{dangerous_coverage:.4f}</text>

<text x="32" y="430" font-family="Arial,sans-serif" font-size="12" fill="#64748b">Safest: distance-to-centroid + region-Mondrian · 0 persistent failures.</text>
<text x="32" y="453" font-family="Arial,sans-serif" font-size="12" fill="#64748b">Most dangerous: inverse-probability + marginal conditioning.</text>
<text x="32" y="476" font-family="Arial,sans-serif" font-size="12" fill="#64748b">Historical conclusion: structural failure pattern confirmed.</text>
</svg>'''


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    FIGURES.mkdir(parents=True, exist_ok=True)
    (FIGURES / "experiment_5_p4_f2_snapshot.svg").write_text(
        experiment_5_svg(data["experiment_5"]["findings"]), encoding="utf-8"
    )
    (FIGURES / "experiment_6_pair_comparison.svg").write_text(
        experiment_6_svg(data["experiment_6"]["findings"]), encoding="utf-8"
    )
    print(f"Wrote figures to {FIGURES}")


if __name__ == "__main__":
    main()
