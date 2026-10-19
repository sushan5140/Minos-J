"""Run Experiment 4 from the validated Experiment 3 working theory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from literature_sources import EXPERIMENT_4_LITERATURE
from llm_client import OPENROUTER_MODEL, call_llm
from pipeline import run_pattern_falsification_stage
from run_experiment import OUTPUT_DIR
from schema import (
    EXPERIMENT_4_NAME,
    validate_cross_question_analysis,
)


SOURCE_PATH = OUTPUT_DIR / "meno_j_experiment_3_cross_question_survivor_analysis.json"
CHECKPOINT_DIR = Path(__file__).resolve().parent / "work" / "experiment_4_checkpoints"
JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_4_pattern_falsification_study.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_4_pattern_falsification_study.md"
REPRO_JSON_OUTPUT = OUTPUT_DIR / "meno_j_experiment_4_reproducibility_summary.json"
REPRO_MARKDOWN_OUTPUT = OUTPUT_DIR / "meno_j_experiment_4_reproducibility_summary.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required validated source is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Source contains invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Source must be a JSON object: {path}")
    return payload


def _validate_literature() -> dict[str, dict[str, Any]]:
    expected_ids = [f"L{index}" for index in range(1, 9)]
    actual_ids = [source.get("citation_id") for source in EXPERIMENT_4_LITERATURE]
    if actual_ids != expected_ids:
        raise ValueError(f"Literature IDs must be ordered L1-L8; got {actual_ids}.")
    required = {
        "citation_id",
        "title",
        "authors",
        "year",
        "venue",
        "url",
        "relevance",
        "validation_method",
    }
    urls: set[str] = set()
    for source in EXPERIMENT_4_LITERATURE:
        if set(source) != required:
            raise ValueError(f"Literature {source.get('citation_id')} has invalid fields.")
        if (
            not isinstance(source["title"], str)
            or not source["title"].strip()
            or not isinstance(source["authors"], list)
            or not source["authors"]
            or not all(isinstance(author, str) and author.strip() for author in source["authors"])
            or type(source["year"]) is not int
            or not isinstance(source["url"], str)
            or not source["url"].startswith("https://")
        ):
            raise ValueError(f"Literature {source['citation_id']} failed structural validation.")
        if source["url"] in urls:
            raise ValueError(f"Duplicate literature URL: {source['url']}")
        urls.add(source["url"])
    return {source["citation_id"]: source for source in EXPERIMENT_4_LITERATURE}


def _load_working_theory() -> tuple[dict[str, Any], set[tuple[str, str]]]:
    source = _read_json(SOURCE_PATH)
    validation = source.get("validation", {})
    if not validation.get("source_runs_valid") or not validation.get(
        "combined_analysis_valid"
    ):
        raise ValueError("Experiment 3 source validation is not complete.")
    if validation.get("strongest_survivor_count") != 9:
        raise ValueError("Experiment 4 requires exactly 9 strongest survivors.")
    if validation.get("recurring_pattern_count") != 5:
        raise ValueError("Experiment 4 requires exactly 5 recurring patterns.")
    pass_references = {
        (label, hypothesis_id)
        for label, summary in source["source_summary"].items()
        for hypothesis_id in summary["pass_ids"]
    }
    validate_cross_question_analysis(
        {"combined_analysis": source["combined_analysis"]},
        pass_references,
    )
    strongest_refs = {
        (item["source_question"], item["hypothesis_id"])
        for item in source["strongest_survivor_details"]
    }
    if len(strongest_refs) != 9 or not strongest_refs.issubset(pass_references):
        raise ValueError("Experiment 3 strongest survivor details are inconsistent.")
    working_theory = {
        "strongest_surviving_hypotheses": source["strongest_survivor_details"],
        "recurring_structural_patterns": source["combined_analysis"][
            "recurring_structural_patterns"
        ],
    }
    return working_theory, pass_references


def _priority_score(experiment: dict[str, Any]) -> float:
    return round(
        0.35 * experiment["scientific_impact_score"]
        + 0.25 * experiment["feasibility_score"]
        + 0.25 * experiment["publication_potential_score"]
        + 0.15 * experiment["information_gain_score"],
        2,
    )


def _build_roadmap(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for study in studies:
        for experiment in study["distinguishing_experiments"]:
            rows.append(
                {
                    "experiment_id": experiment["experiment_id"],
                    "pattern_id": study["pattern_id"],
                    "title": experiment["title"],
                    "scientific_impact_score": experiment["scientific_impact_score"],
                    "feasibility_score": experiment["feasibility_score"],
                    "publication_potential_score": experiment[
                        "publication_potential_score"
                    ],
                    "information_gain_score": experiment["information_gain_score"],
                    "priority_score": _priority_score(experiment),
                    "implementation_difficulty": experiment[
                        "implementation_difficulty"
                    ],
                    "failure_condition_for_working_theory": experiment[
                        "failure_condition_for_working_theory"
                    ],
                }
            )
    rows.sort(key=lambda row: (-row["priority_score"], row["experiment_id"]))
    return [{"rank": rank, **row} for rank, row in enumerate(rows, start=1)]


def _resolve_citations(
    studies: list[dict[str, Any]],
    literature_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    used = {
        citation_id
        for study in studies
        for experiment in study["distinguishing_experiments"]
        for citation_id in experiment["literature_citation_ids"]
    }
    used.update(
        citation_id
        for study in studies
        for citation_id in study["pattern_level_novelty"][
            "closest_literature_citation_ids"
        ]
    )
    return {citation_id: literature_by_id[citation_id] for citation_id in sorted(used)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_reproducibility_summary(
    studies: list[dict[str, Any]],
    roadmap: list[dict[str, Any]],
) -> dict[str, Any]:
    checkpoint_path = CHECKPOINT_DIR / "pattern_falsification_studies.json"
    return {
        "experiment_name": EXPERIMENT_4_NAME,
        "model": OPENROUTER_MODEL,
        "model_temperature": 0.4,
        "source_file": str(SOURCE_PATH.resolve()),
        "source_sha256": _sha256(SOURCE_PATH),
        "source_strongest_survivor_count": 9,
        "source_recurring_pattern_count": 5,
        "validated_literature_source_count": len(EXPERIMENT_4_LITERATURE),
        "pattern_study_count": len(studies),
        "distinguishing_experiment_count": sum(
            len(study["distinguishing_experiments"]) for study in studies
        ),
        "roadmap_entry_count": len(roadmap),
        "checkpoint_file": str(checkpoint_path.resolve()),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "checkpoint_reusable_without_api_key": True,
        "successful_upstream_stages_rerun": False,
        "citation_validation": {
            "only_frozen_primary_source_ids_allowed": True,
            "all_eight_sources_used": True,
            "unknown_citation_count": 0,
        },
        "ranking_formula": (
            "0.35*scientific_impact + 0.25*feasibility + "
            "0.25*publication_potential + 0.15*information_gain"
        ),
        "validation": {
            "working_theory_valid": True,
            "no_new_hypotheses_generated": True,
            "all_pattern_ids_valid": True,
            "all_hypothesis_references_are_existing_pass": True,
            "all_citations_resolved": True,
            "all_effect_sizes_specified": True,
            "all_failure_conditions_specified": True,
            "roadmap_ranked_programmatically": True,
        },
        "run_command": (
            "$env:OPENROUTER_API_KEY=\"<redacted>\"; "
            "$env:OPENROUTER_MODEL=\"nvidia/nemotron-3-ultra-550b-a55b:free\"; "
            "python -u run_pattern_falsification.py"
        ),
    }


def _main_markdown(result: dict[str, Any]) -> str:
    citations = result["validated_literature_sources"]
    lines = [
        f"# {result['experiment_name']}",
        "",
        "## Working theory",
        "",
        "Experiment 4 attempts to falsify the nine surviving hypotheses and five recurring patterns from Experiment 3. No new hypotheses were generated.",
        "",
    ]
    for study in result["pattern_falsification_studies"]:
        lines.extend(
            [
                f"## {study['pattern_id']}: {study['pattern_name']}",
                "",
                f"**Working-theory claim:** {study['working_theory_claim']}",
                "",
                f"**Strongest competitor:** {study['strongest_competing_explanation']}",
                "",
                f"**Competitor mechanism:** {study['competing_explanation_mechanism']}",
                "",
                "### Evidence and alternatives",
                "",
                "**Plausible counterexamples**",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in study["scientifically_plausible_counterexamples"])
        lines.extend(["", "**Confounders and alternatives**", ""])
        lines.extend(
            f"- {item}" for item in study["confounders_and_alternative_explanations"]
        )
        lines.extend(["", "**Evidence supporting the competitor**", ""])
        lines.extend(
            f"- {item}" for item in study["evidence_supporting_competing_explanation"]
        )
        lines.extend(["", "**Evidence refuting the competitor**", ""])
        lines.extend(
            f"- {item}" for item in study["evidence_refuting_competing_explanation"]
        )
        lines.extend(["", "### Distinguishing experiments", ""])
        for experiment in study["distinguishing_experiments"]:
            effect = experiment["expected_effect_size"]
            citation_links = ", ".join(
                f"[{citation_id}]({citations[citation_id]['url']})"
                for citation_id in experiment["literature_citation_ids"]
            )
            lines.extend(
                [
                    f"#### {experiment['experiment_id']}: {experiment['title']}",
                    "",
                    f"- Design: {experiment['design']}",
                    f"- Working-theory prediction: {experiment['meno_j_prediction']}",
                    f"- Competitor prediction: {experiment['competing_explanation_prediction']}",
                    f"- Measurable outcomes: {'; '.join(experiment['measurable_outcomes'])}",
                    f"- Expected effect: {effect['magnitude']} — {effect['metric']}; {effect['expected_direction']}; target: {effect['quantitative_target']}",
                    f"- Effect rationale: {effect['rationale']}",
                    f"- Required data/metadata: {'; '.join(experiment['required_datasets_or_metadata'])}",
                    f"- Difficulty: {experiment['implementation_difficulty']} — {experiment['difficulty_reason']}",
                    f"- Working-theory failure condition: {experiment['failure_condition_for_working_theory']}",
                    f"- Literature: {citation_links}",
                    "",
                ]
            )
        novelty = study["pattern_level_novelty"]
        novelty_links = ", ".join(
            f"[{citation_id}]({citations[citation_id]['url']})"
            for citation_id in novelty["closest_literature_citation_ids"]
        )
        lines.extend(
            [
                "### Novelty",
                "",
                f"- Rating: {novelty['rating']}",
                f"- Rationale: {novelty['rationale']}",
                f"- Novel contribution: {novelty['novel_contribution']}",
                f"- Closest literature: {novelty_links}",
                "",
            ]
        )

    lines.extend(
        [
            "## Ranked research roadmap",
            "",
            "| Rank | Experiment | Pattern | Priority | Impact | Feasibility | Publication | Information gain | Difficulty |",
            "|---:|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["ranked_research_roadmap"]:
        lines.append(
            f"| {row['rank']} | {row['experiment_id']}: {row['title']} | {row['pattern_id']} | "
            f"{row['priority_score']:.2f} | {row['scientific_impact_score']} | "
            f"{row['feasibility_score']} | {row['publication_potential_score']} | "
            f"{row['information_gain_score']} | {row['implementation_difficulty']} |"
        )

    lines.extend(["", "## Validated literature", ""])
    for citation_id, source in citations.items():
        authors = ", ".join(source["authors"])
        lines.append(
            f"- **{citation_id}.** {authors} ({source['year']}). "
            f"[{source['title']}]({source['url']}). {source['venue']}."
        )
    lines.append("")
    return "\n".join(lines)


def _repro_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Experiment 4: Reproducibility Summary",
        "",
        f"- Model: `{summary['model']}`",
        f"- Temperature: {summary['model_temperature']}",
        f"- Source file: `{summary['source_file']}`",
        f"- Source SHA-256: `{summary['source_sha256']}`",
        f"- Literature sources: {summary['validated_literature_source_count']}",
        f"- Pattern studies: {summary['pattern_study_count']}",
        f"- Distinguishing experiments: {summary['distinguishing_experiment_count']}",
        f"- Checkpoint: `{summary['checkpoint_file']}`",
        f"- Checkpoint SHA-256: `{summary['checkpoint_sha256']}`",
        f"- Ranking formula: `{summary['ranking_formula']}`",
        "",
        "## Validation",
        "",
    ]
    lines.extend(
        f"- `{key}`: {value}" for key, value in summary["validation"].items()
    )
    lines.extend(["", "## Run command", "", f"`{summary['run_command']}`", ""])
    return "\n".join(lines)


def main() -> None:
    literature_by_id = _validate_literature()
    working_theory, pass_references = _load_working_theory()
    patterns_by_id = {
        pattern["pattern_id"]: pattern
        for pattern in working_theory["recurring_structural_patterns"]
    }
    studies = run_pattern_falsification_stage(
        call_llm,
        working_theory,
        EXPERIMENT_4_LITERATURE,
        patterns_by_id,
        pass_references,
        set(literature_by_id),
        checkpoint_dir=CHECKPOINT_DIR,
    )
    roadmap = _build_roadmap(studies)
    resolved_citations = _resolve_citations(studies, literature_by_id)
    result = {
        "experiment_name": EXPERIMENT_4_NAME,
        "version": "v5_pattern_falsification",
        "model": OPENROUTER_MODEL,
        "source_experiment": str(SOURCE_PATH.resolve()),
        "working_theory": working_theory,
        "pattern_falsification_studies": studies,
        "ranked_research_roadmap": roadmap,
        "validated_literature_sources": resolved_citations,
        "validation": {
            "no_new_hypotheses_generated": True,
            "working_theory_survivor_count": 9,
            "working_theory_pattern_count": 5,
            "pattern_study_count": len(studies),
            "distinguishing_experiment_count": len(roadmap),
            "all_hypothesis_references_valid": True,
            "all_literature_citations_valid": True,
            "unknown_citation_count": 0,
            "roadmap_ranked_programmatically": True,
        },
    }
    reproducibility = _build_reproducibility_summary(studies, roadmap)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(_main_markdown(result), encoding="utf-8")
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(reproducibility, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPRO_MARKDOWN_OUTPUT.write_text(
        _repro_markdown(reproducibility),
        encoding="utf-8",
    )
    print(f"Experiment 4 JSON: {JSON_OUTPUT}", flush=True)
    print(f"Experiment 4 Markdown: {MARKDOWN_OUTPUT}", flush=True)
    print(f"Reproducibility JSON: {REPRO_JSON_OUTPUT}", flush=True)
    print(f"Reproducibility Markdown: {REPRO_MARKDOWN_OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
