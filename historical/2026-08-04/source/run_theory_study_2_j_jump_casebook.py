"""Build the first historical calibration case for the Meno-J J-jump contract."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STUDY1_REPORT = OUTPUT_DIR / "meno_j_theory_study_1_explanation_quality.json"
STUDY1_VALIDATION = OUTPUT_DIR / "meno_j_theory_study_1_validation.json"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_2_j_jump_casebook_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_2_j_jump_casebook_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_2_ptolemy_kepler_newton.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_2_ptolemy_kepler_newton.md"
AMENDMENT_JSON = OUTPUT_DIR / "meno_j_theory_study_2_contract_amendment.json"
AMENDMENT_MD = OUTPUT_DIR / "meno_j_theory_study_2_contract_amendment.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_2_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_2_reproducibility_summary.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "H01",
        "authors": "Claudius Ptolemy; George of Trebizond (Latin translator)",
        "year": "second century / fifteenth-century translation",
        "title": "Almagest manuscript and text record",
        "url": "https://ptolemaeus.badw.de/ms/446/616/53r",
        "source_type": "primary_source_archive",
        "access_depth": "official_manuscript_record_and_transcribed_passage",
        "supports": ["Ptolemaic combinations of circular motions were explicit geometrical constructions, not a modern caricature."],
    },
    {
        "source_id": "H02",
        "authors": "Johannes Kepler; Bavarian Academy of Sciences edition project",
        "year": "1609/1619; current critical-edition page",
        "title": "The Planetary Laws",
        "url": "https://kepler.badw.de/en/on-johannes-kepler/the-planetary-laws.html",
        "source_type": "primary_excerpts_in_official_critical_edition",
        "access_depth": "official_primary_excerpts_with_translations",
        "supports": ["The first two laws appear in Astronomia Nova and the third in Harmonice Mundi.", "Kepler tied the ellipse claim to physical principles and observations."],
    },
    {
        "source_id": "H03",
        "authors": "Isaac Newton; Newton Project",
        "year": "1726",
        "title": "Front Matter to the Principia, third edition",
        "url": "https://newtonproject.ox.ac.uk/view/texts/normalized/NATP00084",
        "source_type": "primary_source_critical_archive",
        "access_depth": "official_transcription_and_selected_argument_review",
        "supports": ["Newton explicitly connected terrestrial gravity, celestial effects, comet phenomena, and rules of reasoning."],
    },
    {
        "source_id": "H04",
        "authors": "Isaac Newton; I. Bernard Cohen and Anne Whitman (translators)",
        "year": "1687/1999",
        "title": "The Principia: Mathematical Principles of Natural Philosophy",
        "url": "https://pages.jh.edu/rrynasi1/PrincipleOfRelativity/Literature/Newton/Newton1999ThePrincipia.MathematicalPrinciplesOfNaturalPhilosophy.Cohen%2BEtAl.pdf",
        "source_type": "primary_source_modern_translation",
        "access_depth": "full_text_selected_book_sections_review",
        "supports": ["Book I develops mathematical consequences of forces; Book III applies them to the system of the world."],
    },
    {
        "source_id": "H05",
        "authors": "José Díez, Gonzalo Recio, and Christián C. Carman",
        "year": 2022,
        "title": "Does Explaining Past Success Require (Enough) Retention? The Case of Ptolemaic Astronomy",
        "url": "https://link.springer.com/article/10.1007/s10838-021-09589-9",
        "source_type": "peer_reviewed_history_and_philosophy",
        "access_depth": "full_text_argument_review",
        "supports": ["Ptolemy's Mars model had genuine and risky empirical successes.", "Kepler can explain Ptolemy's success without clearly retaining enough of Ptolemy's theoretical machinery."],
    },
    {
        "source_id": "H06",
        "authors": "George E. Smith",
        "year": 2014,
        "title": "Kepler's Astronomia Nova and the Orbit of Mars",
        "url": "https://dl.tufts.edu/concern/pdfs/sn00b872q",
        "source_type": "university_history_of_science_course_analysis",
        "access_depth": "full_course_argument_notes_review",
        "supports": ["Kepler used a successful vicarious model, pursued physical causes, and treated the eight-arcminute mismatch as evidence against circularity.", "The area rule and ellipse emerged through a longer sequence than the simplified textbook story."],
    },
    {
        "source_id": "H07",
        "authors": "Rhonda Martens",
        "year": 2017,
        "title": "Kepler and Newton",
        "url": "https://academic.oup.com/edited-volume/34749/chapter-abstract/296598868",
        "source_type": "scholarly_handbook_chapter",
        "access_depth": "official_abstract_and_selected_argument_review",
        "supports": ["Kepler's physical astronomy was only partially transmitted to Newton and involved conceptual and computational difficulties."],
    },
    {
        "source_id": "H08",
        "authors": "George E. Smith",
        "year": 2008,
        "title": "Newton's Philosophiae Naturalis Principia Mathematica",
        "url": "https://plato.stanford.edu/entries/newton-principia/",
        "source_type": "expert_scholarly_reference",
        "access_depth": "full_entry_argument_review",
        "supports": ["Newton treated Keplerian phenomena as approximate rather than exact.", "Universal gravity explained ideal Keplerian motion and departures caused by mutual interactions.", "Book III was a sustained evidential argument with major unresolved loose ends."],
    },
    {
        "source_id": "H09",
        "authors": "Curtis Wilson",
        "year": 1987,
        "title": "Kepler's Laws of Planetary Motion, Before and After Newton's Principia",
        "url": "https://www.sciencedirect.com/science/article/pii/0039368187900173",
        "source_type": "peer_reviewed_history_of_science",
        "access_depth": "official_record_and_argument_summary",
        "supports": ["Newton transformed the scientific meaning and problem role of the Keplerian laws rather than merely repeating them."],
    },
    {
        "source_id": "H10",
        "authors": "David Marshall Miller",
        "year": 2008,
        "title": "O Male Factum: Rectilinearity and Kepler's Discovery of the Ellipse",
        "url": "https://journals.sagepub.com/doi/10.1177/002182860803900103",
        "source_type": "peer_reviewed_history_of_astronomy",
        "access_depth": "official_article_argument_review",
        "supports": ["Kepler's route to the ellipse depended on the interplay of geometry, the area relation, and an attempted physical account."],
    },
    {
        "source_id": "H11",
        "authors": "Michael Nauenberg",
        "year": 2001,
        "title": "Kepler's Area Law in the Principia: Filling in Details in Newton's Proof of Proposition 1",
        "url": "https://arxiv.org/abs/math/0112048",
        "source_type": "scholarly_mathematical_analysis",
        "access_depth": "full_preprint_argument_review",
        "supports": ["Newton's Proposition 1 generalized the area law through a central-force framework, although details of the limiting proof have been debated."],
    },
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return value


def protocol() -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 2: Historical J-Jump Calibration Casebook",
        "case": "Ptolemy to Kepler to Newton",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_AFTER_SOURCE_SCOPING_BEFORE_TRANSITION_VERDICTS",
        "scope": "Theory and historical-source analysis only; no numerical dataset, LLM, or OpenRouter call.",
        "question": "Can the Theory Study 1 J-jump contract distinguish model refinement, representational change, false mechanism, and explanatory unification in the Ptolemy-Kepler-Newton sequence?",
        "units_of_analysis": [
            "Ptolemaic baseline",
            "Ptolemy-to-Kepler transition",
            "Kepler orbital representation component",
            "Kepler physical-mechanism component",
            "Kepler-to-Newton transition",
            "Newtonian dynamics component",
        ],
        "predeclared_traps": [
            "Treating Ptolemy as mere arbitrary curve fitting",
            "Treating heliocentrism alone as an immediate accuracy victory",
            "Treating Kepler's successful ellipse and failed magnetic mechanism as one indivisible verdict",
            "Treating Newton as exactly deriving an exactly Keplerian solar system",
            "Demanding literal preservation of superseded theoretical objects",
            "Equating theoretical compression with computational simplicity",
            "Treating unresolved mechanism as automatic failure of a dynamical-law explanation",
        ],
        "success_criteria": {
            "minimum_primary_or_official_source_records": 4,
            "minimum_total_source_records": 10,
            "all_claims_map_to_source_ids": True,
            "both_transitions_receive_component_scoped_verdicts": True,
            "at_least_four_false_jump_or_boundary_controls": True,
            "contract_failure_must_trigger_explicit_amendment": True,
            "no_empirical_or_priority_claim": True,
        },
        "failure_conditions": [
            "The result depends on the myth that Ptolemy only added arbitrary epicycles.",
            "Kepler is labeled wholly correct or wholly wrong without component separation.",
            "Newtonian orbits are described as exactly Keplerian without idealization and perturbation boundaries.",
            "The original contract is declared successful despite a historical counterexample to its retention clause.",
            "A representation change is called a surviving J-jump without rival discrimination or new failure exposure.",
        ],
    }


def _criterion(status: str, reason: str, sources: list[str]) -> dict[str, Any]:
    return {"status": status, "reason": reason, "sources": sources}


def historical_models() -> list[dict[str, Any]]:
    return [
        {
            "model_id": "M1",
            "name": "Ptolemaic planetary astronomy",
            "representation": "Earth-referenced deferent, epicycle, eccentric, and equant constructions for nonuniform apparent planetary motion.",
            "strongest_success": "It organized retrograde motion and planetary longitudes and produced risky consequences such as Mars brightening near opposition.",
            "important_limit": "Its successful geometry did not supply the later Sun-centered dynamical relation, and its distances and physical interpretation remained problematic.",
            "fair_verdict": "MATURE_PREDICTIVE_GEOMETRICAL_MODEL_NOT_ARBITRARY_CURVE_FIT",
            "sources": ["H01", "H05"],
        },
        {
            "model_id": "M2",
            "name": "Keplerian physical astronomy",
            "representation": "Sun-focused ellipses, an area-time relation, and a cross-planet period-distance relation, developed alongside attempted solar physical causes.",
            "strongest_success": "It replaced circle-based kinematics with laws that jointly described orbital shape and nonuniform motion and exposed precise observational discrepancies.",
            "important_limit": "Kepler's proposed magnetic/animating physical machinery was not retained as the cause of orbital motion, and the laws were not yet Newtonian dynamics.",
            "fair_verdict": "SUCCESSFUL_ORBITAL_REPRESENTATION_WITH_FAILED_CAUSAL_SUBMODULE",
            "sources": ["H02", "H06", "H07", "H10"],
        },
        {
            "model_id": "M3",
            "name": "Newtonian celestial dynamics",
            "representation": "Laws of motion and mutual inverse-square gravitation applied to terrestrial bodies, planets, satellites, tides, Earth shape, and comets.",
            "strongest_success": "It recovered Kepler-like motion under ideal conditions while explaining deviations through interactions and extending one framework across previously separate phenomena.",
            "important_limit": "Book III contained approximations, empirical uncertainties, unresolved lunar and planetary details, and no accepted micro-mechanism for gravity.",
            "fair_verdict": "POWERFUL_DYNAMICAL_UNIFICATION_WITH_EXPLICIT_HISTORICAL_LOOSE_ENDS",
            "sources": ["H03", "H04", "H08", "H09", "H11"],
        },
    ]


def transitions() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": "T_PK",
            "from": "Ptolemaic planetary astronomy",
            "to": "Keplerian physical astronomy",
            "claimed_component": "orbital representation and evidential method",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Earth-referenced circle combinations were replaced by Sun-focused ellipses plus an area-time relation.", ["H02", "H06"]),
                "J2_retention": _criterion("FAIL_UNDER_ORIGINAL_WORDING", "Kepler recovered and improved empirical successes, but enough Ptolemaic theoretical structure is not clearly retained; some identical numerical roles belong to different objects.", ["H05"]),
                "J3_new_reach": _criterion("PASS", "The new representation addressed orbital shape, distances, nonuniform speed, and physically meaningful solar organization rather than longitude calculation alone.", ["H02", "H06", "H10"]),
                "J4_compression_control": _criterion("PARTIAL", "Geometrical devices were reduced at the representational level, but computation remained difficult and the attempted magnetic mechanism added unsupported structure.", ["H06", "H07"]),
                "J5_rival_discrimination": _criterion("PASS", "Distance, latitude, and the eight-arcminute octant discrepancy separated the circle-based and elliptical accounts; geoheliocentric and alternative motion rules remained serious rivals.", ["H06"]),
                "J6_falsifiability_growth": _criterion("PASS", "The ellipse and area relation exposed exact quantitative consequences that could fail at many orbital positions.", ["H02", "H06"]),
            },
            "gate_verdicts": {
                "orbital_representation": "PASS_WITH_HISTORICAL_UNCERTAINTY",
                "magnetic_or_animating_mechanism": "REJECT_AS_CAUSAL_EXPLANATION",
            },
            "original_contract_verdict": "INDETERMINATE_BECAUSE_J2_FAILS",
            "amended_contract_verdict": "SURVIVING_COMPONENT_LEVEL_REPRESENTATIONAL_J_JUMP",
            "why_amended_verdict_is_not_whole_theory_approval": "The ellipse/area representation survives; Kepler's causal submodule does not. The transition can be explanatory progress without every accompanying belief being correct.",
        },
        {
            "transition_id": "T_KN",
            "from": "Keplerian physical astronomy",
            "to": "Newtonian celestial dynamics",
            "claimed_component": "dynamical-law framework",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Orbital regularities became consequences and approximations within laws of motion and mutual gravitation centered on the system's center of mass.", ["H04", "H08", "H09"]),
                "J2_retention": _criterion("PASS_AS_LIMITING_AND_SUCCESS_ACCOUNTING", "Kepler-like ellipses and area behavior are recovered under idealized conditions, while gravitational interactions explain why actual motion departs from the ideal.", ["H08", "H11"]),
                "J3_new_reach": _criterion("PASS", "The framework joined terrestrial and celestial gravity and addressed satellites, perturbations, Earth shape, tides, precession, and comet trajectories.", ["H03", "H04", "H08"]),
                "J4_compression_control": _criterion("PASS_WITH_DIMENSION_SPLIT", "A smaller common dynamical principle set replaced separate kinematic rules, although derivations and calculations became substantially harder.", ["H04", "H08"]),
                "J5_rival_discrimination": _criterion("PASS_BUT_HISTORICALLY_INCOMPLETE", "Earth-shape, latitude-gravity, comet, lunar, and perturbation consequences confronted vortex and alternative force accounts, though several tests remained unresolved for decades.", ["H08"]),
                "J6_falsifiability_growth": _criterion("PASS", "The theory risked failure across distinct systems and on deviations, not merely on the observations used to state Kepler's laws.", ["H08"]),
            },
            "gate_verdicts": {
                "dynamical_law_component": "PASS_PROVISIONAL_WITH_LOOSE_ENDS",
                "micro_mechanism_of_gravity": "UNRESOLVED_NOT_REQUIRED_FOR_THIS_COMPONENT_CLAIM",
            },
            "original_contract_verdict": "SURVIVING_J_JUMP_WITH_SCOPE_QUALIFICATION",
            "amended_contract_verdict": "SURVIVING_DYNAMICAL_J_JUMP",
            "why_amended_verdict_is_not_whole_theory_approval": "Newton's dynamical relation and unification survive this case; exact historical calculations, all perturbations, and a micro-mechanism of gravity do not receive blanket approval.",
        },
    ]


def controls() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "FJ1",
            "candidate": "Add another epicycle without changing the representation family",
            "temptation": "Accuracy improves, so call it a conceptual jump.",
            "correct_verdict": "MODEL_REFINEMENT_NOT_J_JUMP",
            "reason": "Potentially good science and improved prediction, but J1 fails unless variables, relations, levels, or contrasts genuinely change.",
        },
        {
            "control_id": "FJ2",
            "candidate": "Exact lookup table for all Tycho observations",
            "temptation": "Perfect retention of observed success.",
            "correct_verdict": "MEMORIZATION_NOT_EXPLANATORY_J_JUMP",
            "reason": "No warranted bridge, no transport to changed cases, no rival discrimination, and no new risky consequence.",
        },
        {
            "control_id": "FJ3",
            "candidate": "Kepler's magnetic or animating mechanism taken by itself",
            "temptation": "It introduced physical causation into mathematical astronomy.",
            "correct_verdict": "NOVEL_CAUSAL_REPRESENTATION_REJECTED_BY_ADEQUACY_AND_WARRANT_GATES",
            "reason": "Novelty and falsifiability do not compensate for a failed causal warrant. Its failure does not erase the orbital representation component.",
        },
        {
            "control_id": "FJ4",
            "candidate": "Copernican circular heliocentrism",
            "temptation": "Either call it the complete revolution or dismiss it because initial positional accuracy did not improve.",
            "correct_verdict": "IMPORTANT_PARTIAL_REPRESENTATIONAL_JUMP_REQUIRING_ITS_OWN_SCOPED_CASE",
            "reason": "It reorganized planetary order and retrograde relations, but retained circular devices and does not receive the later Kepler-Newton achievements retrospectively.",
        },
        {
            "control_id": "FJ5",
            "candidate": "Tychonic geoheliocentrism",
            "temptation": "Dismiss it because heliocentrism later won.",
            "correct_verdict": "SERIOUS_OBSERVATIONALLY_EQUIVALENT_RIVAL_FOR_THE_PERIOD",
            "reason": "Contemporary observational equivalence means the contract must record underdetermination and seek future discriminators rather than rewrite history.",
        },
        {
            "control_id": "FJ6",
            "candidate": "Fit an ellipse with a Fourier or epicycle expansion and call the basis functions retained",
            "temptation": "Mathematical transformability proves theoretical continuity.",
            "correct_verdict": "TRANSFORMABILITY_WITHOUT_EXPLANATORY_RETENTION",
            "reason": "A shared fit or mathematical translation need not preserve what the variables represent or why the model succeeds.",
        },
    ]


def amendments() -> dict[str, Any]:
    return {
        "amendment_name": "Historical Calibration Amendment 1",
        "trigger": "The Ptolemy-to-Kepler transition fails the original literal/special-case reading of J2 even though the orbital representation is a defensible J-jump.",
        "amendments": [
            {
                "amendment_id": "A1_RETENTION_ACCOUNTING",
                "old_rule": "Previously validated consequences are preserved as a special case, or their failure boundary is explicitly demonstrated.",
                "new_rule": "Account for prior success by at least one declared mode: literal component retention; limiting or approximate derivation; empirical-capability recovery; or a non-retentive explanation of why, how well, and where the old account succeeded and failed.",
                "guardrail": "Mathematical transformability or identical fitted values do not count by themselves; represented objects and evidential roles must be mapped.",
                "sources": ["H05"],
            },
            {
                "amendment_id": "A2_COMPONENT_SCOPING",
                "old_rule": "Promote or reject the proposal as one unit.",
                "new_rule": "Declare the component under evaluation—representation, empirical law, mechanism, ontology, or method—and permit different verdicts for coupled components.",
                "guardrail": "A successful component cannot launder an unsupported mechanism, and a failed mechanism cannot erase an independently warranted representation.",
                "sources": ["H02", "H06", "H10"],
            },
            {
                "amendment_id": "A3_COMPRESSION_DIMENSIONS",
                "old_rule": "The jump removes assumptions or detail without losing warranted consequences.",
                "new_rule": "Report conceptual, ontological, parameter, and computational complexity separately. A jump may compress principles while increasing derivational or computational work.",
                "guardrail": "Do not treat shorter prose or fewer named objects as evidence of genuine compression.",
                "sources": ["H07", "H08"],
            },
            {
                "amendment_id": "A4_APPROXIMATION_BOUNDARY",
                "old_rule": "The new representation preserves prior validated consequences.",
                "new_rule": "Specify whether consequences are exact, approximate, idealized, or historically provisional, and state the interactions or conditions that generate deviations.",
                "guardrail": "Never describe the Newtonian many-body solar system as exactly Keplerian.",
                "sources": ["H08"],
            },
            {
                "amendment_id": "A5_UNDERDETERMINATION",
                "old_rule": "List a strongest rival and divergent prediction.",
                "new_rule": "Allow a temporary observational-equivalence verdict. When current evidence cannot discriminate rivals, record the equivalence class and the new observations or concepts needed to separate it.",
                "guardrail": "Later victory cannot be used as evidence that the earlier rival was irrational or already empirically refuted.",
                "sources": ["H07", "H08"],
            },
        ],
        "revised_survival_rule": {
            "candidate_threshold": "J1 representation change passes and the claimed component states J2-J6 obligations.",
            "survival_threshold": "For the claimed component, G0-G3 and G5 pass; J2 passes by an explicit retention-accounting mode; J3, J5, and J6 pass; J4 may be partial only when each complexity dimension and tradeoff is declared.",
            "verdict_scope": "Every verdict names its component, evidence period, approximation status, and unresolved submodules.",
        },
    }


def report(protocol_hash: str, study1_hash: str) -> dict[str, Any]:
    transitions_value = transitions()
    return {
        "study_name": "Meno-J Theory Study 2: Historical J-Jump Calibration Casebook",
        "case": "Ptolemy to Kepler to Newton",
        "method": {
            "protocol_sha256": protocol_hash,
            "theory_study_1_sha256": study1_hash,
            "mode": "primary-source-led historical stress test with explicit false-jump controls",
            "llm_or_api_calls": False,
            "dataset_calls": False,
            "source_count": len(SOURCES),
            "qualification": "The case calibrates an engineering contract; it does not settle all historiographical disputes or prove that future AI systems can originate scientific revolutions.",
        },
        "sources": SOURCES,
        "historical_models": historical_models(),
        "transitions": transitions_value,
        "false_jump_and_boundary_controls": controls(),
        "contract_amendment": amendments(),
        "results": {
            "original_contract_survived_unchanged": False,
            "original_contract_failure": "J2 over-required theoretical retention in the Ptolemy-to-Kepler case and lacked component-scoped verdicts.",
            "ptolemy_to_kepler": "SURVIVING_COMPONENT_LEVEL_REPRESENTATIONAL_J_JUMP",
            "kepler_magnetic_mechanism": "REJECTED_CAUSAL_SUBMODULE",
            "kepler_to_newton": "SURVIVING_DYNAMICAL_J_JUMP",
            "newton_scope": "Provisional dynamical-law success with approximations and historical loose ends; no blanket validation of every calculation or a micro-mechanism of gravity.",
            "controls_correctly_separated": len(controls()),
            "significant_findings": [
                "A genuine J-jump need not retain the superseded theory's objects; it must account for the old success without ad hoc translation.",
                "J-jump verdicts must be component-scoped: Kepler's orbital representation survives while his magnetic mechanism fails.",
                "Conceptual compression and computational simplicity can move in opposite directions.",
                "Newton's gain was not exact repetition of Kepler but an idealized recovery plus an explanation of deviations and wider phenomena.",
                "Observationally equivalent rivals must remain live until a genuine discriminator exists.",
            ],
        },
        "decision": "CASEBOOK_1_SUCCESS_CONTRACT_AMENDED",
        "next_case": {
            "name": "Miasma to germ theory",
            "reason": "It tests whether the amended contract handles multicausal public-health change, partial retention of sanitation success, invisible entities, and rivals without forcing the astronomy pattern onto biology.",
            "stop_condition": "If the same amendment rules require another ad hoc exception rather than generalizing, the J-jump contract must be weakened or rejected before any open-problem AI trial.",
        },
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Theory Study 2 Protocol",
        "",
        f"**Case:** {value['case']}",
        "",
        f"**Question:** {value['question']}",
        "",
        f"Status: `{value['status']}`",
        "",
        "## Predeclared traps",
        "",
    ]
    lines.extend(f"- {item}" for item in value["predeclared_traps"])
    lines.extend(["", "## Failure conditions", ""])
    lines.extend(f"- {item}" for item in value["failure_conditions"])
    lines.append("")
    return "\n".join(lines)


def render_report_md(value: dict[str, Any]) -> str:
    lines = [
        "# Historical J-Jump Casebook 1: Ptolemy → Kepler → Newton",
        "",
        "## Outcome",
        "",
        f"Decision: **{value['decision']}**.",
        "",
        "The historical calibration succeeded, but the original J-jump contract did **not** survive unchanged. Its retention rule was too strict and its verdict unit was too coarse.",
        "",
        "## Simple result",
        "",
        "- Ptolemy was not merely adding random circles; his system was a mature geometrical model with real predictive achievements.",
        "- Kepler made a genuine representational jump with ellipses and the area relation, but his proposed magnetic mechanism did not survive.",
        "- Newton made a deeper dynamical jump: he recovered Kepler-like motion as an ideal case, explained deviations, and connected terrestrial and celestial phenomena.",
        "- Therefore, a J-jump must be judged component by component and must **account for** earlier success, not necessarily preserve the earlier theory's machinery.",
        "",
        "## Fair baseline models",
        "",
        "| Model | Strongest success | Important limit | Verdict |",
        "|---|---|---|---|",
    ]
    for model in value["historical_models"]:
        lines.append(f"| {model['name']} | {model['strongest_success']} | {model['important_limit']} | `{model['fair_verdict']}` |")
    lines.extend(["", "## Transition verdicts", ""])
    for transition in value["transitions"]:
        lines.extend([
            f"### {transition['from']} → {transition['to']}",
            "",
            f"Claimed component: **{transition['claimed_component']}**",
            "",
            "| Criterion | Status | Reason |",
            "|---|---|---|",
        ])
        for criterion, item in transition["criteria"].items():
            lines.append(f"| {criterion} | `{item['status']}` | {item['reason']} |")
        lines.extend([
            "",
            f"Original-contract verdict: `{transition['original_contract_verdict']}`",
            "",
            f"Amended-contract verdict: **{transition['amended_contract_verdict']}**",
            "",
            transition["why_amended_verdict_is_not_whole_theory_approval"],
            "",
        ])
    lines.extend(["## False-jump and boundary controls", ""])
    for item in value["false_jump_and_boundary_controls"]:
        lines.append(f"- **{item['control_id']} — {item['candidate']}:** `{item['correct_verdict']}`. {item['reason']}")
    lines.extend(["", "## Required contract amendments", ""])
    for item in value["contract_amendment"]["amendments"]:
        lines.extend([
            f"### {item['amendment_id']}",
            "",
            f"**Old:** {item['old_rule']}",
            "",
            f"**New:** {item['new_rule']}",
            "",
            f"Guardrail: {item['guardrail']}",
            "",
        ])
    lines.extend([
        "## What this changes for Meno-J",
        "",
        "Meno-J must generate and audit **representation components**, not one monolithic theory paragraph. A candidate may contain a valuable new representation, a weak mechanism, and an unresolved ontology at the same time. The engine must preserve those separate verdicts.",
        "",
        "A J-jump now survives only when it changes the map, accounts for old success, gains new reach, confronts serious rivals, exposes new failure conditions, and declares its component and approximation boundary.",
        "",
        "## Significant findings",
        "",
    ])
    lines.extend(f"- {item}" for item in value["results"]["significant_findings"])
    lines.extend([
        "",
        "## Next case",
        "",
        f"**{value['next_case']['name']}** — {value['next_case']['reason']}",
        "",
        f"Stop condition: {value['next_case']['stop_condition']}",
        "",
        "## Sources",
        "",
    ])
    for source in value["sources"]:
        supports = " ".join(source["supports"])
        lines.append(f"- **{source['source_id']} — [{source['title']}]({source['url']})** ({source['authors']}, {source['year']}). `{source['access_depth']}`. {supports}")
    lines.append("")
    return "\n".join(lines)


def render_amendment_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J J-Jump Contract: Historical Calibration Amendment 1",
        "",
        f"**Trigger:** {value['trigger']}",
        "",
    ]
    for item in value["amendments"]:
        lines.extend([
            f"## {item['amendment_id']}",
            "",
            f"Old rule: {item['old_rule']}",
            "",
            f"New rule: **{item['new_rule']}**",
            "",
            f"Guardrail: {item['guardrail']}",
            "",
        ])
    lines.extend([
        "## Revised survival rule",
        "",
        f"- Candidate threshold: {value['revised_survival_rule']['candidate_threshold']}",
        f"- Survival threshold: {value['revised_survival_rule']['survival_threshold']}",
        f"- Verdict scope: {value['revised_survival_rule']['verdict_scope']}",
        "",
    ])
    return "\n".join(lines)


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    if not STUDY1_REPORT.is_file() or not STUDY1_VALIDATION.is_file():
        raise FileNotFoundError("Validated Theory Study 1 outputs are required.")
    validation = _read_json(STUDY1_VALIDATION)
    if validation.get("status") != "PASS":
        raise ValueError("Theory Study 1 validation must be PASS.")

    frozen = protocol()
    _atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")

    result = report(_sha256(PROTOCOL_JSON), _sha256(STUDY1_REPORT))
    _atomic_json(REPORT_JSON, result)
    REPORT_MD.write_text(render_report_md(result), encoding="utf-8")
    _atomic_json(AMENDMENT_JSON, result["contract_amendment"])
    AMENDMENT_MD.write_text(render_amendment_md(result["contract_amendment"]), encoding="utf-8")

    reproducibility = {
        "study_name": result["study_name"],
        "status": "BUILT_PENDING_INDEPENDENT_VALIDATION",
        "execution_date": date.today().isoformat(),
        "input_hashes": {
            "protocol": _sha256(PROTOCOL_JSON),
            "theory_study_1": _sha256(STUDY1_REPORT),
            "theory_study_1_validation": _sha256(STUDY1_VALIDATION),
        },
        "output_hashes": {
            "report_json": _sha256(REPORT_JSON),
            "report_markdown": _sha256(REPORT_MD),
            "amendment_json": _sha256(AMENDMENT_JSON),
            "amendment_markdown": _sha256(AMENDMENT_MD),
        },
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False},
        "encoding": "UTF-8",
        "source_access_limits_recorded": True,
    }
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 2 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n"
        f"- Theory Study 1 SHA-256: `{reproducibility['input_hashes']['theory_study_1']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n",
        encoding="utf-8",
    )
    print(f"Built {REPORT_JSON.name} and contract amendment")


if __name__ == "__main__":
    main()
