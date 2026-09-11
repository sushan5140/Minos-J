"""Build Meno-J Theory Study 4: caloric, thermodynamics, and kinetic theory."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STUDY3_REPORT = OUTPUT_DIR / "meno_j_theory_study_3_miasma_germ_casebook.json"
STUDY3_EXTENSION = OUTPUT_DIR / "meno_j_theory_study_3_contract_extension.json"
STUDY3_VALIDATION = OUTPUT_DIR / "meno_j_theory_study_3_validation.json"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_4_caloric_kinetic_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_4_caloric_kinetic_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_4_caloric_kinetic_casebook.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_4_caloric_kinetic_casebook.md"
EXTENSION_JSON = OUTPUT_DIR / "meno_j_theory_study_4_contract_extension.json"
EXTENSION_MD = OUTPUT_DIR / "meno_j_theory_study_4_contract_extension.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_4_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_4_reproducibility_summary.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "C01",
        "authors": "Antoine-Laurent Lavoisier; translated by Robert Kerr",
        "year": 1790,
        "title": "Elements of Chemistry, in a New Systematic Order",
        "url": "https://books.google.com/books?id=LfKAZy5nqx8C",
        "source_type": "primary_source_book",
        "access_depth": "complete_public_domain_scan_and_caloric_sections_reviewed",
        "supports": ["Lavoisier treated caloric as an imponderable principle while also organizing quantitative calorimetry and heat-capacity phenomena."],
    },
    {
        "source_id": "C02",
        "authors": "Benjamin Thompson, Count Rumford; Royal Society",
        "year": 1798,
        "title": "An Inquiry Concerning the Source of the Heat Which Is Excited by Friction",
        "url": "https://library.si.edu/digital-library/book/philosophicaltr88roya",
        "source_type": "primary_source_journal_archive",
        "access_depth": "complete_public_domain_journal_volume_and_paper_reviewed",
        "supports": ["Sustained cannon-boring friction produced apparently inexhaustible heat, challenging a simply conserved material stock of caloric."],
    },
    {
        "source_id": "C03",
        "authors": "Joseph Fourier",
        "year": 1822,
        "title": "Théorie analytique de la chaleur",
        "url": "https://fr.wikisource.org/wiki/Th%C3%A9orie_analytique_de_la_chaleur",
        "source_type": "primary_source_book_transcription",
        "access_depth": "complete_public_domain_scan_and_transcription_reviewed",
        "supports": ["Fourier developed a powerful mathematical theory of heat propagation without requiring a decisive microscopic ontology."],
    },
    {
        "source_id": "C04",
        "authors": "Sadi Carnot",
        "year": 1824,
        "title": "Réflexions sur la puissance motrice du feu",
        "url": "https://www.e-rara.ch/zut/doi/10.3931/e-rara-9118",
        "source_type": "primary_source_book_archive",
        "access_depth": "complete_public_domain_scan_and_ocr_reviewed",
        "supports": ["Carnot used conserved-caloric reasoning to isolate reversibility, temperature difference, and an upper constraint on heat-engine performance."],
    },
    {
        "source_id": "C05",
        "authors": "Émile Clapeyron",
        "year": "1834; English translation 1837",
        "title": "Memoir on the Motive Power of Heat",
        "url": "https://en.wikisource.org/wiki/Scientific_Memoirs/1/Memoir_on_the_Motive_Power_of_Heat",
        "source_type": "primary_source_translation",
        "access_depth": "complete_public_domain_english_translation_reviewed",
        "supports": ["Clapeyron mathematized Carnot's cycle and made its relations usable by later thermodynamic theorists."],
    },
    {
        "source_id": "C06",
        "authors": "Julius Robert Mayer; translated by G. C. Foster",
        "year": "1842; English translation 1862",
        "title": "Remarks on the Forces of Inorganic Nature",
        "url": "https://web.lemoyne.edu/giunta/mayer.html",
        "source_type": "primary_source_translation",
        "access_depth": "complete_documented_english_translation_reviewed",
        "supports": ["Mayer argued that natural forces transform rather than disappear and estimated a mechanical equivalent of heat."],
    },
    {
        "source_id": "C07",
        "authors": "James Prescott Joule; Royal Society",
        "year": 1850,
        "title": "On the Mechanical Equivalent of Heat",
        "url": "https://commons.wikimedia.org/wiki/File:On_the_Mechanical_Equivalent_of_Heat_(IA_jstor-108427).pdf",
        "source_type": "primary_source_journal_archive",
        "access_depth": "complete_public_domain_paper_reviewed",
        "supports": ["Joule compared work inputs and temperature changes across controlled friction experiments to quantify a stable mechanical equivalent."],
    },
    {
        "source_id": "C08",
        "authors": "Rudolf Clausius",
        "year": 1850,
        "title": "On the Moving Force of Heat and the Laws Deducible Therefrom",
        "url": "https://onlinelibrary.wiley.com/doi/10.1002/andp.18501550403",
        "source_type": "primary_source_journal",
        "access_depth": "official_bibliographic_record_and_complete_public_domain_text_comparison",
        "supports": ["Clausius reconciled heat-work equivalence with the surviving Carnot constraint, creating a modern macroscopic thermodynamic synthesis."],
    },
    {
        "source_id": "C09",
        "authors": "William Thomson",
        "year": 1851,
        "title": "On the Dynamical Theory of Heat",
        "url": "https://zapatopi.net/kelvin/papers/on_the_dynamical_theory_of_heat.html",
        "source_type": "primary_source_transcription",
        "access_depth": "complete_transcription_cross_checked_against_publication_metadata",
        "supports": ["Thomson explicitly combined Joule's equivalent with Carnot and Clausius constraints after earlier caloric-based hesitation."],
    },
    {
        "source_id": "C10",
        "authors": "Rudolf Clausius",
        "year": 1857,
        "title": "On the Nature of the Motion Which We Call Heat",
        "url": "https://webserver.lemoyne.edu/giunta/CLAUSIUS57.html",
        "source_type": "primary_source_translation",
        "access_depth": "complete_documented_translation_reviewed",
        "supports": ["Clausius deliberately separated general thermodynamic conclusions from a particular molecular-motion model before developing the latter."],
    },
    {
        "source_id": "C11",
        "authors": "James Clerk Maxwell",
        "year": 1860,
        "title": "Illustrations of the Dynamical Theory of Gases",
        "url": "https://www.tandfonline.com/doi/abs/10.1080/14786446008642902",
        "source_type": "primary_source_journal",
        "access_depth": "official_record_and_complete_public_domain_scan_reviewed",
        "supports": ["Maxwell introduced a distribution of molecular velocities, making probability part of physical explanation rather than assigning one representative speed."],
    },
    {
        "source_id": "C12",
        "authors": "Ludwig Boltzmann",
        "year": "1872; English translation",
        "title": "Further Studies on the Thermal Equilibrium of Gas Molecules",
        "url": "https://gilles.montambaux.com/files/histoire-physique/Boltzmann-1872-anglais.pdf",
        "source_type": "primary_source_translation",
        "access_depth": "complete_english_translation_reviewed",
        "supports": ["Boltzmann connected molecular collision statistics with approach to equilibrium, while exposing assumptions later central to reversibility debates."],
    },
    {
        "source_id": "C13",
        "authors": "John Young",
        "year": 2015,
        "title": "Heat, Work and Subtle Fluids: A Commentary on Joule (1850)",
        "url": "https://doi.org/10.1098/rsta.2014.0348",
        "source_type": "peer_reviewed_historical_commentary",
        "access_depth": "full_open_access_article_reviewed",
        "supports": ["Joule's result emerged from a sustained experimental program and difficult reception, not one visually decisive paddle-wheel demonstration."],
    },
    {
        "source_id": "C14",
        "authors": "Wayne M. Saslow",
        "year": 2020,
        "title": "A History of Thermodynamics: The Missing Manual",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7516509/",
        "source_type": "peer_reviewed_history_and_technical_review",
        "access_depth": "full_open_access_article_reviewed",
        "supports": ["The transition joined distinct heat-conservation and energy-conservation lineages; Rumford's results admitted caloric-compatible replies, while Clausius supplied the key synthesis."],
    },
    {
        "source_id": "C15",
        "authors": "Stathis Psillos",
        "year": 1994,
        "title": "A Philosophical Study of the Transition from the Caloric Theory of Heat to Thermodynamics",
        "url": "https://www.sciencedirect.com/science/article/pii/0039368194900264",
        "source_type": "peer_reviewed_philosophy_of_science",
        "access_depth": "official_abstract_and_detailed_argument_review",
        "supports": ["Important calorimetric, adiabatic, and Carnot results were separable from caloric's material ontology and recoverable in thermodynamics."],
    },
    {
        "source_id": "C16",
        "authors": "Penha Maria Cardoso Dias",
        "year": 1996,
        "title": "William Thomson and the Heritage of Caloric",
        "url": "https://www.tandfonline.com/doi/abs/10.1080/00033799600200361",
        "source_type": "peer_reviewed_history_of_physics",
        "access_depth": "official_abstract_and_argument_summary_reviewed",
        "supports": ["Thomson's transition required reconciliation of Joule's transformation principle with Carnot's constraint rather than simple replacement."],
    },
    {
        "source_id": "C17",
        "authors": "Malcolm S. Longair",
        "year": 2003,
        "title": "Kinetic Theory and the Origin of Statistical Mechanics",
        "url": "https://www.cambridge.org/core/books/abs/theoretical-concepts-in-physics/kinetic-theory-and-the-origin-of-statistical-mechanics/51A51FEA108C0E96BDE4EA1C3B46FF5C",
        "source_type": "scholarly_history_of_physics",
        "access_depth": "official_chapter_summary_and_argument_review",
        "supports": ["Thermodynamic laws were formulated independently of a specific microscopic model; Clausius, Maxwell, and Boltzmann then built a distinct kinetic-statistical explanatory layer."],
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


def _criterion(status: str, reason: str, sources: list[str]) -> dict[str, Any]:
    return {"status": status, "reason": reason, "sources": sources}


def protocol() -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 4: Historical J-Jump Casebook 3",
        "case": "Caloric ontology, energy conservation, thermodynamics, and kinetic-statistical theory",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_AFTER_SOURCE_SCOPING_BEFORE_FINAL_LINEAGE_VERDICTS",
        "scope": "Historical-conceptual analysis only; no LLM, OpenRouter call, dataset, or numerical simulation.",
        "question": "Does the extended J-jump contract preserve caloric theory's real successes while distinguishing anomaly, conversion law, phenomenological synthesis, and microscopic-statistical explanation?",
        "predeclared_traps": [
            "Claiming Rumford's cannon experiment immediately killed caloric theory",
            "Treating caloric theory as wholly unsuccessful because its substance ontology failed",
            "Calling Carnot's valid engine constraint evidence that conserved caloric existed",
            "Treating Joule's mechanical equivalent as a complete molecular theory of heat",
            "Conflating thermodynamics with kinetic theory",
            "Back-projecting Maxwell-Boltzmann probability into Carnot or Joule",
            "Treating one experiment as the discovery of energy conservation",
            "Ignoring the different meanings carried by heat, work, force, and energy across authors",
            "Assuming macroscopic thermodynamic validity depends on one microscopic ontology",
            "Presenting the transition as one theory replacing one rival at one date",
        ],
        "success_criteria": {
            "source_records": 17,
            "minimum_primary_source_records": 12,
            "lineage_nodes": 7,
            "transition_edges": 6,
            "false_jump_controls": 10,
            "all_prior_contract_rules_explicitly_tested": True,
            "new_extension_triggered_only_by_unhandled_structure": True,
        },
        "failure_conditions": [
            "The report says caloric simply became kinetic theory.",
            "Surviving mathematics is credited to caloric's material ontology without a portability test.",
            "An anomaly is treated as a replacement theory.",
            "Macroscopic thermodynamics and microscopic statistical mechanics are collapsed into one explanatory level.",
            "Later evidence is transferred backward to earlier authors.",
            "Study 3's distributed-lineage and evidential-level rules are silently weakened.",
        ],
    }


def nodes() -> list[dict[str, Any]]:
    return [
        {
            "node_id": "N1",
            "name": "Lavoisierian caloric and quantitative calorimetry",
            "component": "material-fluid ontology plus measurable heat quantities",
            "surviving_value": "Heat capacity, latent-heat accounting, equilibration, and quantitative comparison became tractable research objects.",
            "failed_or_limited_claim": "Heat is not a separately conserved imponderable material whose amount merely moves between bodies.",
            "verdict": "ONTOLOGY_REJECTED_MEASUREMENT_AND_ACCOUNTING_PARTLY_RETAINED",
            "sources": ["C01", "C15"],
        },
        {
            "node_id": "N2",
            "name": "Fourier's phenomenological heat-flow theory",
            "component": "macroscopic propagation law and mathematical representation",
            "surviving_value": "The heat equation describes conduction at its intended scale without deciding whether heat is substance or motion.",
            "failed_or_limited_claim": "It does not by itself identify heat's ontology or explain irreversible conduction microscopically.",
            "verdict": "FORMAL_MACROSCOPIC_SUCCESS_ONTOLOGICALLY_PORTABLE",
            "sources": ["C03", "C14", "C15"],
        },
        {
            "node_id": "N3",
            "name": "Rumford's frictional-heat anomaly",
            "component": "repeatable production-like behavior under mechanical work",
            "surviving_value": "Apparently inexhaustible frictional heating strongly pressured finite-stock caloric explanations and motivated motion accounts.",
            "failed_or_limited_claim": "The experiment did not quantify a universal conversion constant or uniquely eliminate every flexible caloric model.",
            "verdict": "STRONG_ANOMALY_NOT_SELF_SUFFICIENT_J_JUMP",
            "sources": ["C02", "C14"],
        },
        {
            "node_id": "N4",
            "name": "Carnot-Clapeyron reversible-engine framework",
            "component": "engine-cycle constraint and temperature-level dependence",
            "surviving_value": "Reversibility and the limit on motive power survived reinterpretation in the second law.",
            "failed_or_limited_claim": "The waterwheel-like transport of conserved caloric is not the mechanism by which engines produce work.",
            "verdict": "FALSE_ONTOLOGY_WITH_SURVIVING_CONSTRAINT_STRUCTURE",
            "sources": ["C04", "C05", "C15"],
        },
        {
            "node_id": "N5",
            "name": "Mayer-Joule transformation and equivalence program",
            "component": "quantitative interchangeability of work and heat",
            "surviving_value": "Multiple transformations could be represented by a conserved energy quantity and a measurable heat-work equivalence.",
            "failed_or_limited_claim": "Equivalence and conservation did not alone explain directionality, entropy, molecular motion, or every experimental discrepancy.",
            "verdict": "SURVIVING_CONVERSION_LAW_J_JUMP_INCOMPLETE_THERMAL_THEORY",
            "sources": ["C06", "C07", "C13", "C14"],
        },
        {
            "node_id": "N6",
            "name": "Clausius-Thomson macroscopic thermodynamic synthesis",
            "component": "joint first- and second-law constraint architecture",
            "surviving_value": "Energy conservation and Carnot-style directionality were reconciled without requiring a final microscopic story.",
            "failed_or_limited_claim": "Macroscopic laws alone do not explain molecular mechanisms or derive irreversibility from reversible microdynamics.",
            "verdict": "SURVIVING_MACROSCOPIC_SYNTHESIS_J_JUMP",
            "sources": ["C08", "C09", "C14", "C16"],
        },
        {
            "node_id": "N7",
            "name": "Clausius-Maxwell-Boltzmann kinetic-statistical layer",
            "component": "molecular motion, velocity distributions, collisions, and equilibrium statistics",
            "surviving_value": "Macroscopic pressure, temperature, transport, and equilibrium could be connected to ensembles of molecular motions and probability.",
            "failed_or_limited_claim": "Specific models and independence assumptions are domain-limited, and the emergence of irreversible behavior remains assumption-sensitive.",
            "verdict": "SURVIVING_MICROSCOPIC_STATISTICAL_J_JUMP_WITH_FOUNDATIONAL_LIMITS",
            "sources": ["C10", "C11", "C12", "C17"],
        },
    ]


def transitions() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": "T1_CALORIC_TO_FORMAL_HEAT_FLOW",
            "from_nodes": ["N1"], "to_node": "N2", "claimed_component": "ontology-light macroscopic heat propagation",
            "criteria": {
                "J1_representation_change": _criterion("PARTIAL", "The representation shifted toward fields, gradients, and boundary conditions while retaining heat-quantity language.", ["C03"]),
                "J2_retention_accounting": _criterion("PASS", "Calorimetric quantities were retained as measurable variables without making material caloric essential to the differential law.", ["C03", "C15"]),
                "J3_new_reach": _criterion("PASS", "The framework solved spatial and temporal conduction problems beyond verbal fluid analogy.", ["C03"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "Ontological commitment decreased while mathematical complexity increased.", ["C03"]),
                "J5_rival_discrimination": _criterion("FAIL_FOR_ONTOLOGY", "The same macroscopic law could coexist with caloric or motion interpretations.", ["C15"]),
                "J6_falsifiability_growth": _criterion("PASS_AT_MACRO_LEVEL", "Boundary-value predictions could fail even though the microscopic ontology remained open.", ["C03"]),
            },
            "verdict": "FORMAL_ADVANCE_NOT_COMPLETE_ONTOLOGICAL_J_JUMP",
            "unresolved": "The formalism deliberately underdetermined what heat is.",
        },
        {
            "transition_id": "T2_RUMFORD_ANOMALY",
            "from_nodes": ["N1"], "to_node": "N3", "claimed_component": "frictional-heat anomaly",
            "criteria": {
                "J1_representation_change": _criterion("PARTIAL", "Rumford favored motion over a material stock, but did not supply a mature replacement architecture.", ["C02"]),
                "J2_retention_accounting": _criterion("PARTIAL", "The anomaly retained measured heating but did not recover the full successes of calorimetry or engine theory.", ["C02", "C14"]),
                "J3_new_reach": _criterion("PASS_LOCAL", "It connected continued mechanical friction with continued heating.", ["C02"]),
                "J4_complexity_dimensions": _criterion("INDETERMINATE", "A motion metaphor was simpler but insufficiently specified for broad calculation.", ["C02"]),
                "J5_rival_discrimination": _criterion("PARTIAL", "It strongly pressured finite caloric reservoirs but caloric defenders could posit abundant or released caloric.", ["C14"]),
                "J6_falsifiability_growth": _criterion("PARTIAL", "It supplied a repeatable anomaly but not a universal quantitative conversion prediction.", ["C02", "C14"]),
            },
            "verdict": "ANOMALY_AND_RESEARCH_REDIRECTION_NOT_J_JUMP_ALONE",
            "unresolved": "A discriminating quantitative bridge between work and heat was still missing.",
        },
        {
            "transition_id": "T3_CARNOT_CONSTRAINT",
            "from_nodes": ["N1", "N2"], "to_node": "N4", "claimed_component": "reversible heat-engine constraint",
            "criteria": {
                "J1_representation_change": _criterion("PASS_AT_PROCESS_LEVEL", "Heat engines became cyclic transformations constrained by temperatures rather than collections of machine parts.", ["C04", "C05"]),
                "J2_retention_accounting": _criterion("PASS_WITH_REINTERPRETATION", "The cycle and efficiency constraint survived while conserved-caloric transport was discarded.", ["C08", "C15"]),
                "J3_new_reach": _criterion("PASS", "It derived a general upper-bound structure across working substances and engine designs.", ["C04", "C05"]),
                "J4_complexity_dimensions": _criterion("PASS", "Ideal reversibility compressed many engine details into a general constraint.", ["C04"]),
                "J5_rival_discrimination": _criterion("FAIL_FOR_CALORIC_ONTOLOGY", "Success of the engine theorem did not distinguish a material caloric from later energy-based reinterpretation.", ["C15"]),
                "J6_falsifiability_growth": _criterion("PASS_FOR_ENGINE_THEORY", "Claims about reversible cycles and temperature levels exposed engine-performance limits to test.", ["C04", "C05"]),
            },
            "verdict": "CONSTRAINT_LEVEL_J_JUMP_EMBEDDED_IN_FALSE_ONTOLOGY",
            "unresolved": "Why work can be produced while heat is not conserved remained contradictory under the original ontology.",
        },
        {
            "transition_id": "T4_ENERGY_TRANSFORMATION",
            "from_nodes": ["N1", "N3"], "to_node": "N5", "claimed_component": "work-heat conversion and conserved energy",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Heat changed from conserved substance to one transfer/conversion mode within a more general conserved quantity.", ["C06", "C07"]),
                "J2_retention_accounting": _criterion("PASS", "Calorimetric measurements remained usable while conservation moved from heat alone to total energy.", ["C07", "C15"]),
                "J3_new_reach": _criterion("PASS", "Mechanical, electrical, chemical, and thermal processes became quantitatively comparable.", ["C06", "C07", "C13"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "One invariant unified phenomena but demanded careful system boundaries and measurement corrections.", ["C07", "C13"]),
                "J5_rival_discrimination": _criterion("PASS_CUMULATIVE", "Stable equivalence across distinct work-to-heat routes discriminated transformation from a finite heat stock better than Rumford alone.", ["C07", "C13"]),
                "J6_falsifiability_growth": _criterion("PASS", "Different conversion routes had to yield a consistent equivalent after declared losses and uncertainties.", ["C07"]),
            },
            "verdict": "SURVIVING_ENERGY_CONVERSION_J_JUMP",
            "unresolved": "The law did not yet contain the directional restriction captured by Carnot.",
        },
        {
            "transition_id": "T5_THERMODYNAMIC_SYNTHESIS",
            "from_nodes": ["N4", "N5"], "to_node": "N6", "claimed_component": "joint conservation and directionality architecture",
            "criteria": {
                "J1_representation_change": _criterion("PASS_SYNTHETIC", "Two apparently conflicting lineages became distinct laws: energy is conserved while thermal transformations are directionally constrained.", ["C08", "C09"]),
                "J2_retention_accounting": _criterion("PASS_EXPLICIT", "Carnot's reversible constraint and Joule's equivalence were both retained after their incompatible interpretations were removed.", ["C08", "C09", "C16"]),
                "J3_new_reach": _criterion("PASS", "The synthesis addressed engines, state changes, specific heats, and irreversible direction under one macroscopic framework.", ["C08", "C09", "C14"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "Two compact constraints replaced material-fluid pictures but introduced abstract state and path distinctions.", ["C08", "C14"]),
                "J5_rival_discrimination": _criterion("PASS", "It explained how heat can convert to work without preserving caloric and why complete cyclic conversion remains restricted.", ["C08", "C09"]),
                "J6_falsifiability_growth": _criterion("PASS", "A process could violate energy accounting, directionality, or both, yielding sharper independent failure modes.", ["C08", "C09"]),
            },
            "verdict": "SURVIVING_SYNTHETIC_MACROSCOPIC_J_JUMP",
            "unresolved": "The framework was intentionally compatible with more than one microscopic realization.",
        },
        {
            "transition_id": "T6_KINETIC_STATISTICAL_BRIDGE",
            "from_nodes": ["N5", "N6"], "to_node": "N7", "claimed_component": "molecular-statistical microfoundation",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Macroscopic heat variables were connected to ensembles of molecules, distributions, and collision statistics.", ["C10", "C11", "C12"]),
                "J2_retention_accounting": _criterion("PASS_LAYERED", "Thermodynamic laws remained autonomous constraints while gaining candidate microscopic realizations.", ["C10", "C17"]),
                "J3_new_reach": _criterion("PASS", "The layer explained gas pressure, temperature, velocity distributions, transport, and equilibrium tendencies.", ["C10", "C11", "C12"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "Molecular unity increased explanatory depth but required probabilistic assumptions and large-number approximations.", ["C11", "C12", "C17"]),
                "J5_rival_discrimination": _criterion("PASS_DOMAIN_BOUND", "Distribution and transport predictions could discriminate micro-models in gases, though thermodynamics itself did not select one universal micro-ontology.", ["C11", "C17"]),
                "J6_falsifiability_growth": _criterion("PASS", "Velocity distributions, mean free paths, transport coefficients, and equilibrium behavior supplied new failure surfaces.", ["C10", "C11", "C12"]),
            },
            "verdict": "SURVIVING_LAYERED_MICROFOUNDATIONAL_J_JUMP",
            "unresolved": "Irreversibility, molecular chaos, and domain transfer remain foundational and approximation-sensitive questions.",
        },
    ]


def controls() -> list[dict[str, str]]:
    return [
        {"control_id": "F1", "false_claim": "Rumford's cannon boring disproved caloric theory immediately.", "verdict": "REJECT_SINGLE_EXPERIMENT_REVOLUTION", "reason": "It was a powerful anomaly, but flexible caloric interpretations survived and no complete quantitative successor followed from the experiment."},
        {"control_id": "F2", "false_claim": "Caloric theory made no true predictions.", "verdict": "REJECT_WHOLESALE_FAILURE", "reason": "Calorimetry, heat-flow mathematics, and Carnot-style constraints contained portable empirical and formal successes."},
        {"control_id": "F3", "false_claim": "Carnot's successful engine theory confirms a material caloric fluid.", "verdict": "REJECT_SUCCESS_TO_ONTOLOGY_TRANSFER", "reason": "The constraint survives after its material-fluid interpretation is removed."},
        {"control_id": "F4", "false_claim": "Joule alone discovered the complete modern theory of heat.", "verdict": "REJECT_SINGLE_HERO_AND_SCOPE_INFLATION", "reason": "Joule established quantitative equivalence; directionality and microscopic explanation came from other linked programs."},
        {"control_id": "F5", "false_claim": "Mechanical equivalence automatically entails the second law.", "verdict": "REJECT_CONSERVATION_DIRECTIONALITY_COLLAPSE", "reason": "Energy accounting does not by itself state which transformations occur spontaneously or cyclically."},
        {"control_id": "F6", "false_claim": "Thermodynamics is kinetic theory expressed macroscopically.", "verdict": "REJECT_LEVEL_COLLAPSE", "reason": "Macroscopic thermodynamic constraints can be formulated and tested without selecting one microscopic model."},
        {"control_id": "F7", "false_claim": "Clausius's 1850 thermodynamics already contained Maxwell-Boltzmann statistics.", "verdict": "REJECT_BACK_PROJECTION", "reason": "Clausius intentionally separated general principles from the later particular molecular-motion account."},
        {"control_id": "F8", "false_claim": "Formal continuity proves approximate truth of the old ontology.", "verdict": "REJECT_EQUATION_ONTOLOGY_EQUIVOCATION", "reason": "An equation may be portable across rival ontologies because its empirical variables and symmetry constraints are more stable than its interpretation."},
        {"control_id": "F9", "false_claim": "A molecular model that recovers equilibrium has explained irreversibility completely.", "verdict": "REJECT_HIDDEN_ASSUMPTION_ERASURE", "reason": "Collision independence, coarse-graining, initial conditions, and reversibility objections must remain visible."},
        {"control_id": "F10", "false_claim": "The transition had one winning theory and one losing theory.", "verdict": "REJECT_BINARY_REPLACEMENT", "reason": "The mature result is layered: phenomenological thermodynamics and kinetic-statistical explanation coexist while doing different work."},
    ]


def prior_rule_tests() -> list[dict[str, str]]:
    return [
        {"rule_id": "A1_RETENTION_ACCOUNTING", "status": "PASS_AND_ESSENTIAL", "finding": "Heat quantities and engine constraints survived even though caloric substance did not."},
        {"rule_id": "A2_COMPONENT_SCOPING", "status": "PASS_AND_ESSENTIAL", "finding": "Ontology, propagation law, conversion constant, directionality, and microfoundation require separate verdicts."},
        {"rule_id": "A3_COMPRESSION_DIMENSIONS", "status": "PASS", "finding": "Energy unified more phenomena while statistical mechanics increased mathematical and assumption complexity."},
        {"rule_id": "A4_APPROXIMATION_BOUNDARY", "status": "PASS", "finding": "Ideal gases, reversible cycles, continua, and molecular chaos have different declared domains."},
        {"rule_id": "A5_UNDERDETERMINATION", "status": "PASS_AND_ESSENTIAL", "finding": "Fourier and macroscopic thermodynamics underdetermine microscopic ontology."},
        {"rule_id": "A6_DISTRIBUTED_LINEAGE_GRAPH", "status": "PASS_AND_ESSENTIAL", "finding": "Carnot, Mayer, Joule, Clausius, Thomson, Maxwell, and Boltzmann contribute different linked components."},
        {"rule_id": "A7_INTERVENTION_MECHANISM_DECOUPLING", "status": "PASS_GENERALIZED_AS_OPERATION_MECHANISM_DECOUPLING", "finding": "Engine performance and work-heat conversions can be established before their microscopic mechanism."},
        {"rule_id": "A8_EVIDENCE_TRIANGULATION_LADDER", "status": "PASS", "finding": "Anomaly, equivalence measurements, cycle constraints, gas laws, and distribution predictions supply different evidential modes."},
        {"rule_id": "A9_RELATIONAL_CAUSAL_SCOPE", "status": "PASS_GENERALIZED_AS_EXPLANATORY_LEVEL_SCOPE", "finding": "A heat-flow law, conservation law, directional law, and micro-mechanism are not interchangeable causal claims."},
        {"rule_id": "A10_DISCOVERY_UPTAKE_OUTCOME_SEPARATION", "status": "PASS_AND_ESSENTIAL", "finding": "Rumford's anomaly and Joule's early results did not produce immediate community replacement."},
    ]


def extension() -> dict[str, Any]:
    return {
        "extension_name": "Historical Calibration Extension 3",
        "trigger": "A theory can have false ontology yet portable mathematics, while the successor can consist of autonomous macroscopic constraints plus a later microscopic bridge.",
        "prior_rule_status": prior_rule_tests(),
        "extensions": [
            {
                "extension_id": "A11_FORMAL_ONTOLOGY_DECOUPLING",
                "new_rule": "Audit equations, operational quantities, invariants, and ontology separately; test whether the formal success transports to a rival representation after reinterpretation.",
                "guardrail": "Formal retention is not evidence that the discarded entities approximately existed.",
                "sources": ["C03", "C04", "C15"],
            },
            {
                "extension_id": "A12_CONSTRAINT_MECHANISM_LAYERING",
                "new_rule": "Allow a well-supported macroscopic constraint and a microscopic mechanism to coexist as different explanatory layers; score each for its own predictions and assumptions.",
                "guardrail": "Do not reject a reliable constraint for lacking micro-ontology, or promote a micro-story merely because it can narrate the constraint.",
                "sources": ["C08", "C09", "C10", "C17"],
            },
            {
                "extension_id": "A13_BRIDGE_LAW_REQUIREMENT",
                "new_rule": "A cross-level J-jump must state mappings between macro variables and micro or ensemble quantities, together with limits, coarse-graining, and independence assumptions.",
                "guardrail": "Similarity of vocabulary such as heat, motion, or disorder is not a derivation.",
                "sources": ["C10", "C11", "C12", "C17"],
            },
            {
                "extension_id": "A14_TRANSITION_ROLE_TAXONOMY",
                "new_rule": "Label a contribution as anomaly, measurement standard, conversion law, constraint, synthesis, or microfoundation before testing whether it is a J-jump.",
                "guardrail": "An anomaly or instrument result cannot receive the credit of a complete replacement architecture.",
                "sources": ["C02", "C07", "C08", "C13", "C14"],
            },
            {
                "extension_id": "A15_LAYERED_SUCCESSOR_TEST",
                "new_rule": "Do not force one successor theory when mature science uses compatible layers. Require the proposed architecture to say what each layer explains, predicts, leaves open, and can falsify.",
                "guardrail": "Explanatory pluralism is not permission for contradiction: bridge relations and shared observables must remain mutually consistent.",
                "sources": ["C08", "C10", "C17"],
            },
        ],
        "revised_j_jump_object": "A component-scoped lineage subgraph that preserves transportable empirical and formal structure, replaces failed ontology explicitly, distinguishes anomalies from successor architecture, and connects autonomous explanatory levels through testable bridge laws.",
    }


def report(protocol_hash: str, study3_hash: str, extension_hash: str) -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 4: Historical J-Jump Casebook 3",
        "case": "Caloric ontology, energy conservation, thermodynamics, and kinetic-statistical theory",
        "method": {
            "protocol_sha256": protocol_hash,
            "study_3_report_sha256": study3_hash,
            "study_3_extension_sha256": extension_hash,
            "mode": "primary-source-led layered historical falsification study",
            "llm_or_api_calls": False,
            "dataset_or_simulation_calls": False,
            "source_count": len(SOURCES),
        },
        "sources": SOURCES,
        "lineage_nodes": nodes(),
        "transition_edges": transitions(),
        "false_jump_controls": controls(),
        "prior_contract_rule_tests": prior_rule_tests(),
        "contract_extension": extension(),
        "results": {
            "original_case_label_valid": False,
            "corrected_case_label": "Caloric ontology → energy transformation + macroscopic thermodynamics + kinetic-statistical microfoundation",
            "prior_contract_generalized": True,
            "prior_contract_sufficient_unchanged": False,
            "full_transition_verdict": "SURVIVING_LAYERED_DISTRIBUTED_J_JUMP_WITH_FORMAL_PORTABILITY",
            "significant_findings": [
                "Caloric theory did not simply become kinetic theory; energy conservation, thermodynamics, and statistical mechanics are distinct successor layers.",
                "A false ontology can support portable equations and constraints, so preserved prediction must not be confused with preserved entities.",
                "Rumford supplied a strong anomaly, not a complete revolution; cumulative quantitative equivalence and later synthesis did the discriminating work.",
                "Carnot was wrong about conserved caloric yet right about a deep engine constraint that Clausius and Thomson reinterpreted.",
                "Clausius explicitly separated general thermodynamic laws from a particular molecular model, showing that mechanism completeness is not required at every explanatory layer.",
                "For AI, a defensible J-jump is often invariant extraction plus ontological replacement plus a new bridge between levels—not unconstrained novelty.",
            ],
        },
        "decision": "CASEBOOK_3_SUCCESS_ORIGINAL_BINARY_FRAMING_REJECTED_CONTRACT_EXTENDED",
        "next_case": {
            "name": "Continental drift to plate tectonics",
            "reason": "This tests whether Meno-J can distinguish a partly correct large-scale pattern claim from the later mechanism, independent predictions, and multi-domain synthesis that made it scientifically compelling.",
            "stop_condition": "If the extended contract cannot distinguish precursor correctness from mechanistic adequacy without hindsight, pause case expansion and formalize the detector as an explicit scoring model.",
        },
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Theory Study 4 Protocol", "", f"**Case:** {value['case']}", "",
        f"**Question:** {value['question']}", "", f"Status: `{value['status']}`", "",
        "## Predeclared traps", "",
    ]
    lines.extend(f"- {item}" for item in value["predeclared_traps"])
    lines.extend(["", "## Failure conditions", ""])
    lines.extend(f"- {item}" for item in value["failure_conditions"])
    lines.append("")
    return "\n".join(lines)


def render_report_md(value: dict[str, Any]) -> str:
    lines = [
        "# Historical J-Jump Casebook 3: Caloric → Thermodynamics → Kinetic Theory", "",
        "## Outcome", "", f"Decision: **{value['decision']}**.", "",
        "The original binary case label failed. The historical successor is a **layered distributed J-jump**:", "",
        "```text",
        "caloric measurements ──→ Fourier: macroscopic heat flow",
        "        │               └→ Carnot/Clapeyron: reversible constraint ─┐",
        "        └→ Rumford anomaly → Mayer/Joule: energy conversion ────────┼→ Clausius/Thomson: thermodynamics",
        "                                                                  └→ Clausius/Maxwell/Boltzmann: kinetic statistics",
        "```", "", "Thermodynamics and kinetic theory remain distinct but compatible explanatory layers.", "",
        "## Node verdicts", "", "| Node | Surviving component | Failed or limited component | Verdict |", "|---|---|---|---|",
    ]
    for item in value["lineage_nodes"]:
        lines.append(f"| {item['name']} | {item['surviving_value']} | {item['failed_or_limited_claim']} | `{item['verdict']}` |")
    lines.extend(["", "## Transition tests", ""])
    for edge in value["transition_edges"]:
        lines.extend([f"### {edge['transition_id']} — {edge['claimed_component']}", "", "| Criterion | Status | Reason |", "|---|---|---|"])
        for name, result in edge["criteria"].items():
            lines.append(f"| {name} | `{result['status']}` | {result['reason']} |")
        lines.extend(["", f"Verdict: **{edge['verdict']}**", "", f"Unresolved: {edge['unresolved']}", ""])
    lines.extend(["## False-jump controls", ""])
    for item in value["false_jump_controls"]:
        lines.append(f"- **{item['control_id']}: {item['false_claim']}** `{item['verdict']}` — {item['reason']}")
    lines.extend(["", "## Prior contract stress result", ""])
    for item in value["prior_contract_rule_tests"]:
        lines.append(f"- **{item['rule_id']}: `{item['status']}`** — {item['finding']}")
    lines.extend(["", "All ten prior rules generalized, but they were not sufficient unchanged.", "", "## New contract extensions", ""])
    for item in value["contract_extension"]["extensions"]:
        lines.extend([f"### {item['extension_id']}", "", f"**Rule:** {item['new_rule']}", "", f"Guardrail: {item['guardrail']}", ""])
    lines.extend([
        "## What this changes for Meno-J", "",
        "Meno-J should not ask an AI merely for an unconventional theory. It should ask the AI to identify which constraints survive across rivals, isolate which ontology fails, propose explicit cross-level bridges, and expose every bridge assumption to a new failure test.", "",
        f"**Revised J-jump object:** {value['contract_extension']['revised_j_jump_object']}", "",
        "## Significant findings", "",
    ])
    lines.extend(f"- {item}" for item in value["results"]["significant_findings"])
    lines.extend(["", "## Next case", "", f"**{value['next_case']['name']}** — {value['next_case']['reason']}", "", f"Stop condition: {value['next_case']['stop_condition']}", "", "## Sources", ""])
    for source in value["sources"]:
        lines.append(f"- **{source['source_id']} — [{source['title']}]({source['url']})** ({source['authors']}, {source['year']}). `{source['access_depth']}`. {' '.join(source['supports'])}")
    lines.append("")
    return "\n".join(lines)


def render_extension_md(value: dict[str, Any]) -> str:
    lines = ["# Meno-J J-Jump Contract: Historical Calibration Extension 3", "", f"**Trigger:** {value['trigger']}", "", "## Prior rules", ""]
    for item in value["prior_rule_status"]:
        lines.append(f"- **{item['rule_id']}: `{item['status']}`** — {item['finding']}")
    lines.append("")
    for item in value["extensions"]:
        lines.extend([f"## {item['extension_id']}", "", f"New rule: **{item['new_rule']}**", "", f"Guardrail: {item['guardrail']}", ""])
    lines.extend(["## Revised J-jump object", "", value["revised_j_jump_object"], ""])
    return "\n".join(lines)


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    for path in (STUDY3_REPORT, STUDY3_EXTENSION, STUDY3_VALIDATION):
        if not path.is_file():
            raise FileNotFoundError(f"Missing validated Study 3 prerequisite: {path}")
    if _read_json(STUDY3_VALIDATION).get("status") != "PASS":
        raise ValueError("Theory Study 3 validation must be PASS.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = protocol()
    _atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")
    result = report(_sha256(PROTOCOL_JSON), _sha256(STUDY3_REPORT), _sha256(STUDY3_EXTENSION))
    _atomic_json(REPORT_JSON, result)
    REPORT_MD.write_text(render_report_md(result), encoding="utf-8")
    _atomic_json(EXTENSION_JSON, result["contract_extension"])
    EXTENSION_MD.write_text(render_extension_md(result["contract_extension"]), encoding="utf-8")

    reproducibility = {
        "study_name": result["study_name"],
        "status": "BUILT_PENDING_INDEPENDENT_VALIDATION",
        "execution_date": date.today().isoformat(),
        "input_hashes": {
            "protocol": _sha256(PROTOCOL_JSON),
            "study_3_report": _sha256(STUDY3_REPORT),
            "study_3_extension": _sha256(STUDY3_EXTENSION),
            "study_3_validation": _sha256(STUDY3_VALIDATION),
        },
        "output_hashes": {
            "report_json": _sha256(REPORT_JSON), "report_markdown": _sha256(REPORT_MD),
            "extension_json": _sha256(EXTENSION_JSON), "extension_markdown": _sha256(EXTENSION_MD),
        },
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False, "simulation": False},
        "encoding": "UTF-8",
        "source_access_limits_recorded": True,
    }
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 4 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset/simulation calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n"
        f"- Study 3 report SHA-256: `{reproducibility['input_hashes']['study_3_report']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n",
        encoding="utf-8",
    )
    print(f"Built {REPORT_JSON.name} and contract extension")


if __name__ == "__main__":
    main()
