"""Build the literature review that freezes the next Meno-J experiment direction."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_literature_review_after_experiment_14.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_literature_review_after_experiment_14.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "L01",
        "title": "The limits of distribution-free conditional predictive inference",
        "authors": "Rina Foygel Barber; Emmanuel J. Candès; Aaditya Ramdas; Ryan J. Tibshirani",
        "year": 2021,
        "venue": "Information and Inference",
        "url": "https://par.nsf.gov/servlets/purl/10253824",
        "full_text_reviewed": True,
        "evidence": "Exact distribution-free covariate-conditional coverage is nontrivially impossible; useful relaxations must restrict the group class and control its complexity relative to sample size.",
        "meno_j_implication": "Do not claim individual-subject conditional coverage. Any subject reliability rule must be low-dimensional, frozen, and evaluated outside the data used to select it.",
    },
    {
        "source_id": "L02",
        "title": "Conformal Prediction Under Covariate Shift",
        "authors": "Ryan J. Tibshirani; Rina Foygel Barber; Emmanuel J. Candès; Aaditya Ramdas",
        "year": 2019,
        "venue": "NeurIPS",
        "url": "https://arxiv.org/pdf/1904.06019",
        "full_text_reviewed": True,
        "evidence": "Likelihood-ratio weighting restores a target-distribution guarantee only when the conditional label law is unchanged; variable weights reduce effective calibration sample size.",
        "meno_j_implication": "Weighted conformal is a falsifiable rival, not an assumed repair. Report weight concentration and effective sample size, and distinguish covariate shift from posterior or protocol shift.",
    },
    {
        "source_id": "L03",
        "title": "Localized Conformal Prediction: A Generalized Inference Framework for Conformal Prediction",
        "authors": "Leying Guan",
        "year": 2023,
        "venue": "Biometrika",
        "url": "https://arxiv.org/pdf/2106.08460",
        "full_text_reviewed": True,
        "evidence": "Naively replacing a global quantile with a local weighted quantile at the same nominal level can under-cover arbitrarily; localization requires a validity-preserving level adjustment.",
        "meno_j_implication": "Do not implement an ad-hoc nearest-subject calibration rule. First diagnose whether local similarity predicts failure, then use a formally valid localized method if warranted.",
    },
    {
        "source_id": "L04",
        "title": "Conformal Prediction With Conditional Guarantees",
        "authors": "Isaac Gibbs; John J. Cherian; Emmanuel J. Candès",
        "year": 2025,
        "venue": "Journal of the Royal Statistical Society Series B",
        "url": "https://arxiv.org/pdf/2305.12616",
        "full_text_reviewed": True,
        "evidence": "Finite-dimensional, predeclared shift classes can support conditional guarantees; increasingly flexible classes incur explicit statistical and computational costs.",
        "meno_j_implication": "Prefer a tiny prespecified diagnostic space over a free-form subject gate or high-dimensional partition learner.",
    },
    {
        "source_id": "L05",
        "title": "Conformal Prediction with Learned Features",
        "authors": "Shayan Kiyani; George J. Pappas; Hamed Hassani",
        "year": 2024,
        "venue": "ICML",
        "url": "https://proceedings.mlr.press/v235/kiyani24a.html",
        "full_text_reviewed": True,
        "evidence": "Learning uncertainty partitions improves approximate conditional behavior, but the number of groups trades approximation error against fewer calibration samples per group and requires validation or nested splitting.",
        "meno_j_implication": "The 33-subject cohort is too small for unconstrained partition discovery. Treat learned grouping as future work or use fully nested subject-level evaluation.",
    },
    {
        "source_id": "L06",
        "title": "Classification with Valid and Adaptive Coverage",
        "authors": "Yaniv Romano; Matteo Sesia; Emmanuel Candès",
        "year": 2020,
        "venue": "NeurIPS",
        "url": "https://papers.nips.cc/paper_files/paper/2020/file/244edd7e85dc81602b7615cd705545f5-Paper.pdf",
        "full_text_reviewed": True,
        "evidence": "Adaptive classification scores can improve set adaptivity, but their conditional behavior depends on the quality of estimated class probabilities.",
        "meno_j_implication": "After class-Mondrian failed to restore subject safety, investigate probability-model mismatch rather than adding more class-threshold variants.",
    },
    {
        "source_id": "L07",
        "title": "Uncertainty Sets for Image Classifiers using Conformal Prediction",
        "authors": "Anastasios N. Angelopoulos; Stephen Bates; Michael Jordan; Jitendra Malik",
        "year": 2021,
        "venue": "ICLR",
        "url": "https://people.eecs.berkeley.edu/~angelopoulos/publications/downloads/conformal-classification.pdf",
        "full_text_reviewed": True,
        "evidence": "RAPS regularization principally controls many small, unlikely classes in large-label problems.",
        "meno_j_implication": "RAPS is low priority for a binary stress task; score quality and subject shift are more plausible bottlenecks.",
    },
    {
        "source_id": "L08",
        "title": "Conformal Classification with Equalized Coverage for Adaptively Selected Groups",
        "authors": "Yanfei Zhou; Matteo Sesia",
        "year": 2024,
        "venue": "arXiv preprint",
        "url": "https://arxiv.org/pdf/2405.15106",
        "full_text_reviewed": True,
        "evidence": "Selecting the worst-covered attribute using the same calibration data creates selection bias; the paper uses a permutation-invariant leave-one-out construction to preserve validity without an extra split.",
        "meno_j_implication": "A retrospectively selected raw-versus-normalized subject gate would be invalid evidence. Selection must be nested or use a validity-preserving adaptive construction.",
    },
    {
        "source_id": "L09",
        "title": "Conformal Prediction Sets with Improved Conditional Coverage using Trust Scores",
        "authors": "Jivat Neet Kaur; Michael I. Jordan; Ahmed Alaa",
        "year": 2025,
        "venue": "arXiv preprint",
        "url": "https://arxiv.org/pdf/2501.10139",
        "full_text_reviewed": True,
        "evidence": "Miscoverage concentrates when classifiers are confidently wrong; confidence plus a nonparametric trust score provides a low-dimensional proxy for disagreement with the Bayes classifier.",
        "meno_j_implication": "This is the strongest next diagnostic: test whether normalized class-Mondrian failures concentrate in high-confidence, low-trust physiological windows.",
    },
    {
        "source_id": "L10",
        "title": "Rectifying Conformity Scores for Better Conditional Coverage",
        "authors": "Vincent Plassier; Alexander Fishkov; Victor Dheur; Mohsen Guizani; Souhaib Ben Taieb; Maxim Panov; Eric Moulines",
        "year": 2025,
        "venue": "ICML",
        "url": "https://arxiv.org/abs/2502.16336",
        "full_text_reviewed": True,
        "evidence": "Rectified scores preserve exact marginal validity while approximate conditional validity depends explicitly on conditional-quantile estimation error; the method needs extra data splitting or out-of-sample scores.",
        "meno_j_implication": "Score rectification is a plausible later repair only after the low-dimensional failure signal is verified and an independent split is reserved for quantile estimation.",
    },
    {
        "source_id": "L11",
        "title": "WESAD: A Multimodal Dataset for Wearable Stress and Affect Detection",
        "authors": "Philip Schmidt; Attila Reiss; Robert Duerichen; Claus Marberger; Kristof Van Laerhoven",
        "year": 2018,
        "venue": "ICMI",
        "url": "https://ubi29.informatik.uni-siegen.de/usi/data_wesad.html",
        "full_text_reviewed": True,
        "evidence": "WESAD contains 15 subjects, wrist and chest signals, and baseline, stress, amusement, and meditation conditions; its benchmark reports average classification performance rather than subject-conditional conformal safety.",
        "meno_j_implication": "Meno-J's contribution is not another average-accuracy WESAD benchmark; it is the falsification of uncertainty guarantees across people and protocols.",
    },
    {
        "source_id": "L12",
        "title": "An Improved Subject-Independent Stress Detection Model Applied to Consumer-grade Wearable Devices",
        "authors": "Anh Ninh; Tu Machu; Cathal Gurrin",
        "year": 2022,
        "venue": "MMM",
        "url": "https://doras.dcu.ie/27656/1/MMM22_Tu_MACHU_new_version%20%281%29.pdf",
        "full_text_reviewed": True,
        "evidence": "The study normalizes each 60-second signal segment before feature extraction and reports subject-independent stress accuracy, but its normalization target differs from subject onboarding median/IQR scaling.",
        "meno_j_implication": "Do not cite generic stress normalization as validation of Experiment 13's onboarding transform; the operations remove different information and answer different questions.",
    },
    {
        "source_id": "L13",
        "title": "Effect of Person-specific Biometrics in Improving Generic Stress Predictive Models",
        "authors": "Kizito Nkurikiyeyezu; Toshiya Yokokubo; Guillaume Lopez",
        "year": 2020,
        "venue": "Sensors and Materials",
        "url": "https://sensors.myu-group.co.jp/sm_pdf/SM2131.pdf",
        "full_text_reviewed": True,
        "evidence": "Large gains came from adding labeled person-specific samples and retraining; normalization alone remained below supervised person-specific adaptation.",
        "meno_j_implication": "This does not validate label-free onboarding. It predicts that unlabeled normalization may be insufficient when the label mechanism itself differs by person.",
    },
    {
        "source_id": "L14",
        "title": "Personalized Stress Detection from Physiological Measurements",
        "authors": "Fang-Yu Sun; Chao-Wen Hsu; Chih-Kai Chuang; Santosh Kumar",
        "year": 2010,
        "venue": "International Conference on Quality of Life Technology",
        "url": "https://www.memphis.edu/cs/santosh-kumar/papers/qol_paper4.pdf",
        "full_text_reviewed": True,
        "evidence": "Deviation from a labeled neutral baseline improved personalized stress precision, and temporal aggregation improved performance further.",
        "meno_j_implication": "A known neutral baseline is informative but unavailable in our label-free mixed onboarding protocol; temporal and baseline mechanisms should remain separate hypotheses.",
    },
    {
        "source_id": "L15",
        "title": "Stressor Type Matters! Exploring Factors Influencing Cross-Dataset Generalizability of Machine Learning Stress Detection Models Using Heart Rate Variability",
        "authors": "Preetham Prajod; Dario M. Sommer; Alexander L. Francis; Thomas Plötz",
        "year": 2024,
        "venue": "arXiv preprint",
        "url": "https://arxiv.org/abs/2405.09563",
        "full_text_reviewed": True,
        "evidence": "Across four stress datasets, stressor type was the strongest observed driver of cross-dataset generalization differences in the studied HRV setting.",
        "meno_j_implication": "The PhysioNet protocol versions and short social/cognitive tasks can induce posterior shift; covariate weighting alone may therefore fail even with accurate density ratios.",
    },
    {
        "source_id": "L16",
        "title": "Cross Dataset Analysis for Generalizability of HRV-Based Stress Detection Models",
        "authors": "Oumaima Benchekroun; Alexandre M. M. Sousa; Hugo Gamboa",
        "year": 2023,
        "venue": "Sensors",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9960690/",
        "full_text_reviewed": True,
        "evidence": "Strong within-dataset models degraded sharply across datasets, with protocol, sensor, laboratory, and real-life differences implicated in transfer failure.",
        "meno_j_implication": "Experiment 13's modest accuracy gain but unsafe coverage is consistent with cross-protocol uncertainty shift, not merely a poor global threshold.",
    },
    {
        "source_id": "L17",
        "title": "An Adaptive System for Wearable Devices to Detect Stress Using Physiological Signals",
        "authors": "Gelei Xu; Ruiyang Qin; Zhi Zheng; Yiyu Shi",
        "year": 2024,
        "venue": "arXiv position paper",
        "url": "https://arxiv.org/pdf/2407.15252",
        "full_text_reviewed": True,
        "evidence": "The proposed wearable personalization path uses unlabeled adaptation followed by a small labeled fine-tuning stage, explicitly recognizing new-user domain shift.",
        "meno_j_implication": "A purely unlabeled gate should be evaluated as a limited safety diagnostic, not represented as equivalent to full personalized stress adaptation.",
    },
    {
        "source_id": "L18",
        "title": "Cover your cough: detection of respiratory events with confidence using a smartwatch",
        "authors": "Khuong An Nguyen; Zhiyuan Luo",
        "year": 2018,
        "venue": "COPA / PMLR",
        "url": "https://proceedings.mlr.press/v91/nguyen18a.html",
        "full_text_reviewed": True,
        "evidence": "Conformal prediction has been used with smartwatch sensing, but for cough and sneeze event confidence rather than cross-subject physiological stress coverage.",
        "meno_j_implication": "Wearable conformal prediction is not new by itself; the defensible novelty is subject- and protocol-level falsification in stress detection.",
    },
    {
        "source_id": "L19",
        "title": "Hierarchical adaptive conformal inference for reliable uncertainty quantification in edge-deployable medical wearables",
        "authors": "Oussama El Allam; Mohamed Hamlich",
        "year": 2026,
        "venue": "Measurement",
        "url": "https://www.sciencedirect.com/science/article/pii/S0263224126014740",
        "full_text_reviewed": False,
        "evidence": "Abstract and accessible methods summary propose multi-timescale online adaptation for physiological drift and few-shot labeled personalization in ECG.",
        "meno_j_implication": "Online adaptation is relevant future work, but the inaccessible full text was not used to set Experiment 15's decision thresholds or claims.",
        "review_limitation": "Publisher full text was not accessible in the current environment; this record is screened, not counted as a top-to-bottom full-text review.",
    },
]


def _report() -> dict[str, Any]:
    return {
        "report_name": "Meno-J Literature Review After Experiment 14",
        "review_date": date.today().isoformat(),
        "scope": "Conditional conformal coverage, distribution shift, adaptive grouping, wearable physiological uncertainty, and subject-independent stress detection.",
        "method": {
            "source_policy": "Primary papers and official publication or dataset pages only.",
            "full_text_rule": "A source is marked full_text_reviewed only when the complete article or proceedings text was accessible and inspected from introduction through conclusions/appendices relevant to the claim.",
            "screened_count": len(SOURCES),
            "full_text_reviewed_count": sum(bool(item["full_text_reviewed"]) for item in SOURCES),
            "abstract_or_partial_only_count": sum(not item["full_text_reviewed"] for item in SOURCES),
            "no_llm_or_api_call": True,
        },
        "sources": SOURCES,
        "cross_paper_findings": [
            {
                "finding_id": "F1",
                "finding": "Exact distribution-free individual conditional coverage is not a scientifically defensible target.",
                "supported_by": ["L01", "L04"],
                "action": "Use marginal guarantees plus explicitly bounded low-complexity subgroup diagnostics; report that subject coverage is empirical, not guaranteed.",
            },
            {
                "finding_id": "F2",
                "finding": "A data-selected subject gate can manufacture apparent safety unless selection is nested or validity-preserving.",
                "supported_by": ["L05", "L08"],
                "action": "Do not retrospectively choose raw versus normalized per subject from the same 33 outcomes.",
            },
            {
                "finding_id": "F3",
                "finding": "Covariate weighting is valid only for a narrower shift than the wearable evidence makes plausible.",
                "supported_by": ["L02", "L15", "L16"],
                "action": "Treat weighted conformal as one rival mechanism and measure effective sample size; do not call it the default repair.",
            },
            {
                "finding_id": "F4",
                "finding": "Class-conditional repair and covariate-conditional repair are different problems.",
                "supported_by": ["L01", "L06", "L09"],
                "action": "Experiment 14's class-gap repair does not contradict its subject-safety failure; diagnose classifier-manifold mismatch next.",
            },
            {
                "finding_id": "F5",
                "finding": "The most testable label-free warning signal is confident prediction combined with low geometric trust.",
                "supported_by": ["L09", "L13", "L17"],
                "action": "Run a frozen confidence–trust conditional coverage diagnostic before building any gate or score repair.",
            },
            {
                "finding_id": "F6",
                "finding": "Published stress personalization gains often use labels, a known neutral baseline, or a different normalization operation.",
                "supported_by": ["L12", "L13", "L14", "L17"],
                "action": "Do not transfer those claims to Meno-J's unlabeled mixed onboarding design.",
            },
            {
                "finding_id": "F7",
                "finding": "The strongest novelty position is falsification of cross-person uncertainty safety, not conformal prediction on wearables in general.",
                "supported_by": ["L11", "L16", "L18"],
                "action": "Frame the paper around auditable failure diagnosis and rival discrimination across subjects and protocols.",
            },
        ],
        "next_experiment": {
            "experiment_name": "Meno-J Experiment 15: Confidence–Trust Subject-Shift Diagnostic",
            "status": "SELECTED_AND_PREREGISTERED_AFTER_LITERATURE_REVIEW",
            "research_question": "After class conditioning, does undercoverage concentrate in physiological windows where the classifier is highly confident but geometrically unsupported by its predicted-class training manifold?",
            "why_this_before_a_repair": "It directly tests the probability-model mismatch mechanism without retrospectively optimizing a gate, preserves all prior outputs, and can fail cleanly.",
            "deferred_repairs": [
                "raw-versus-normalized subject gate",
                "localized conformal calibration",
                "covariate-weighted conformal calibration",
                "rectified conformity scores",
                "online adaptive conformal inference",
            ],
        },
        "claim_boundaries": [
            "This review is a targeted primary-paper review, not a formal systematic review or meta-analysis.",
            "One 2026 publisher article was abstract-screened only and is explicitly excluded from the full-text count.",
            "No literature source validates individual-subject coverage for the current Meno-J protocol.",
            "No novelty claim is based only on absence from keyword search.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Literature Review After Experiment 14",
        "",
        "## Outcome",
        "",
        "The review changes the next move: **do not build a retrospective raw-versus-normalized subject gate yet.** First test whether failures are the specific high-confidence/low-trust errors predicted by conditional-coverage theory.",
        "",
        "## Review scope and integrity",
        "",
        f"- Primary sources screened: {report['method']['screened_count']}",
        f"- Full texts reviewed: {report['method']['full_text_reviewed_count']}",
        f"- Abstract/partial only: {report['method']['abstract_or_partial_only_count']}",
        "- LLM/API calls: none",
        "- Sources: primary papers and official publication/dataset pages",
        "",
        "## What the papers collectively say",
        "",
    ]
    for finding in report["cross_paper_findings"]:
        lines.extend(
            [
                f"### {finding['finding_id']}: {finding['finding']}",
                "",
                f"Evidence: {', '.join(finding['supported_by'])}.",
                "",
                f"Meno-J action: {finding['action']}",
                "",
            ]
        )
    lines.extend(["## Paper-by-paper extraction", ""])
    for source in report["sources"]:
        status = "full text" if source["full_text_reviewed"] else "abstract/partial only"
        lines.extend(
            [
                f"### {source['source_id']}: [{source['title']}]({source['url']})",
                "",
                f"- {source['authors']} ({source['year']}), {source['venue']}",
                f"- Review status: {status}",
                f"- Worth retaining: {source['evidence']}",
                f"- Consequence for Meno-J: {source['meno_j_implication']}",
            ]
        )
        if source.get("review_limitation"):
            lines.append(f"- Limitation: {source['review_limitation']}")
        lines.append("")
    next_experiment = report["next_experiment"]
    lines.extend(
        [
            "## Frozen next step",
            "",
            f"**{next_experiment['experiment_name']}**",
            "",
            next_experiment["research_question"],
            "",
            f"Why now: {next_experiment['why_this_before_a_repair']}",
            "",
            "Deferred until this mechanism survives:",
            "",
            *[f"- {item}" for item in next_experiment["deferred_repairs"]],
            "",
            "## Boundaries",
            "",
            *[f"- {item}" for item in report["claim_boundaries"]],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = _report()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    print(
        f"Literature review complete: {report['method']['full_text_reviewed_count']} full texts",
        flush=True,
    )


if __name__ == "__main__":
    main()
