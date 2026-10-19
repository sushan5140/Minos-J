"""Build Meno-J Theory Study 5: continental drift to plate tectonics."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STUDY4_REPORT = OUTPUT_DIR / "meno_j_theory_study_4_caloric_kinetic_casebook.json"
STUDY4_EXTENSION = OUTPUT_DIR / "meno_j_theory_study_4_contract_extension.json"
STUDY4_VALIDATION = OUTPUT_DIR / "meno_j_theory_study_4_validation.json"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_5_continental_drift_plate_tectonics_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_5_continental_drift_plate_tectonics_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_5_continental_drift_plate_tectonics_casebook.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_5_continental_drift_plate_tectonics_casebook.md"
EXTENSION_JSON = OUTPUT_DIR / "meno_j_theory_study_5_contract_extension.json"
EXTENSION_MD = OUTPUT_DIR / "meno_j_theory_study_5_contract_extension.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_5_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_5_reproducibility_summary.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "D01", "authors": "Alfred Wegener; English translation by Roland von Huene", "year": "1912; translation 2002",
        "title": "The Origin of Continents", "url": "https://planet-terre.ens-lyon.fr/article/Wegener-genese-continents-oceans.xml",
        "source_type": "primary_source_translation", "access_depth": "translated_1912_paper_and_context_reviewed",
        "supports": ["Wegener explicitly proposed horizontal continental displacement as a unifying alternative to fixed-continent accounts."],
    },
    {
        "source_id": "D02", "authors": "Alfred Wegener; translated by J. G. A. Skerl", "year": "1922 third edition; English 1924",
        "title": "The Origin of Continents and Oceans", "url": "https://en.wikisource.org/wiki/The_Origin_of_Continents_and_Oceans",
        "source_type": "primary_source_book_translation", "access_depth": "complete_public_domain_english_translation_reviewed",
        "supports": ["Wegener combined geometrical, geological, paleontological, paleoclimatic, and geodetic considerations, while proposing physically problematic motion through oceanic substrate."],
    },
    {
        "source_id": "D03", "authors": "Harold Jeffreys", "year": 1924,
        "title": "The Earth: Its Origin, History and Physical Constitution", "url": "https://books.google.com/books/about/The_Earth.html?id=j71NAAAAMAAJ",
        "source_type": "primary_source_book", "access_depth": "bibliographic_record_and_relevant_geophysical_arguments_reviewed",
        "supports": ["Contemporary geophysical criticism challenged the adequacy of proposed tidal and rotational driving forces and the mechanical behavior required by drift."],
    },
    {
        "source_id": "D04", "authors": "American Association of Petroleum Geologists; W. A. J. M. van Waterschoot van der Gracht, editor", "year": 1928,
        "title": "Theory of Continental Drift: A Symposium", "url": "https://doi.org/10.1306/SV2329",
        "source_type": "primary_source_symposium", "access_depth": "official_volume_metadata_and_selected_arguments_reviewed",
        "supports": ["The early controversy contained qualified support, factual disputes, and methodological disagreement—not one uniformly mocking rejection."],
    },
    {
        "source_id": "D05", "authors": "Arthur Holmes", "year": "1929; published 1931",
        "title": "Radioactivity and Earth Movements", "url": "https://planet-terre.ens-lyon.fr/article/Arthur-Holmes-convection.xml",
        "source_type": "primary_source_excerpts", "access_depth": "substantial_primary_excerpts_and_publication_context_reviewed",
        "supports": ["Holmes proposed heat-driven mantle circulation as a possible mechanism connecting internal energy, spreading, and continental movement."],
    },
    {
        "source_id": "D06", "authors": "S. K. Runcorn", "year": 1956,
        "title": "Applications of the Remanent Magnetization of Rocks", "url": "https://www.earthdoc.org/content/journals/gpr/4/3",
        "source_type": "primary_source_journal", "access_depth": "official_abstract_and_bibliographic_record_reviewed",
        "supports": ["Paleomagnetism offered an independent physical method for comparing past continental positions and apparent polar-wander paths."],
    },
    {
        "source_id": "D07", "authors": "S. K. Runcorn", "year": 1961,
        "title": "Climatic Change through Geological Time in the Light of Palaeomagnetic Evidence", "url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.49708737303",
        "source_type": "primary_source_journal", "access_depth": "official_abstract_and_detailed_argument_reviewed",
        "supports": ["Systematically different continental paleomagnetic paths and paleoclimate indicators supported relative continental motion rather than one shared polar path."],
    },
    {
        "source_id": "D08", "authors": "Harry H. Hess", "year": 1962,
        "title": "History of Ocean Basins", "url": "https://eos-courses.readthedocs.io/en/latest/_downloads/53c5de2f78442b9d6494bcbee70d202e/Hess1962.pdf",
        "source_type": "primary_source_book_chapter", "access_depth": "complete_paper_reviewed",
        "supports": ["Hess proposed ocean-floor renewal at ridges and return into the mantle, replacing continents-plowing-through-fixed-seafloor with moving oceanic substrate."],
    },
    {
        "source_id": "D09", "authors": "Frederick J. Vine and Drummond H. Matthews", "year": 1963,
        "title": "Magnetic Anomalies over Oceanic Ridges", "url": "https://www.nature.com/articles/199947a0.pdf",
        "source_type": "primary_source_journal", "access_depth": "complete_primary_paper_reviewed",
        "supports": ["The magnetic-stripe hypothesis joined geomagnetic reversals to symmetric seafloor accretion and generated quantitative spreading-rate expectations."],
    },
    {
        "source_id": "D10", "authors": "Edward Bullard, J. E. Everett, and A. Gilbert Smith", "year": 1965,
        "title": "The Fit of the Continents around the Atlantic", "url": "https://royalsocietypublishing.org/doi/pdf/10.1098/rsta.1965.0020",
        "source_type": "primary_source_journal", "access_depth": "complete_primary_paper_and_official_abstract_reviewed",
        "supports": ["Least-squares fitting at continental margins quantified Atlantic reconstruction and stated its residual errors rather than relying on coastline resemblance."],
    },
    {
        "source_id": "D11", "authors": "J. Tuzo Wilson", "year": 1965,
        "title": "A New Class of Faults and Their Bearing on Continental Drift", "url": "https://www.nature.com/articles/207343a0",
        "source_type": "primary_source_journal", "access_depth": "official_article_and_argument_reviewed",
        "supports": ["Transform faults supplied a new boundary type whose geometry and earthquake behavior followed from relative plate motion."],
    },
    {
        "source_id": "D12", "authors": "Jack Oliver and Bryan Isacks", "year": 1967,
        "title": "Deep Earthquake Zones, Anomalous Structures in the Upper Mantle, and the Lithosphere", "url": "https://agupubs.onlinelibrary.wiley.com/doi/10.1029/JZ072i016p04259",
        "source_type": "primary_source_journal", "access_depth": "official_full_article_record_and_detailed_abstract_reviewed",
        "supports": ["Deep seismic zones beneath island arcs supported a strong descending lithospheric slab and crustal recycling."],
    },
    {
        "source_id": "D13", "authors": "Dan P. McKenzie and Robert L. Parker", "year": 1967,
        "title": "The North Pacific: An Example of Tectonics on a Sphere", "url": "https://www.nature.com/articles/2161276a0",
        "source_type": "primary_source_journal", "access_depth": "official_article_and_abstract_reviewed",
        "supports": ["Rigid aseismic regions moving as plates on a sphere predicted boundary slip directions using finite rotations."],
    },
    {
        "source_id": "D14", "authors": "W. Jason Morgan", "year": 1968,
        "title": "Rises, Trenches, Great Faults, and Crustal Blocks", "url": "https://www.mantleplumes.org/WebDocuments/Morgan1968.pdf",
        "source_type": "primary_source_journal", "access_depth": "complete_primary_paper_reviewed",
        "supports": ["Morgan generalized rigid crustal blocks including oceanic regions and connected rises, trenches, faults, and spherical motions."],
    },
    {
        "source_id": "D15", "authors": "Naomi Oreskes", "year": 1999,
        "title": "The Rejection of Continental Drift: Theory and Method in American Earth Science", "url": "https://academic.oup.com/book/40879",
        "source_type": "scholarly_history_of_science", "access_depth": "official_book_summary_and_selected_argument_reviewed",
        "supports": ["American rejection cannot be reduced to absence of mechanism; disciplinary standards about direct and indirect evidence also shaped appraisal."],
    },
    {
        "source_id": "D16", "authors": "Dunja Šešelja and Erik Weber", "year": 2012,
        "title": "Rationality and Irrationality in the History of Continental Drift", "url": "https://www.sciencedirect.com/science/article/pii/S0039368111001099",
        "source_type": "peer_reviewed_philosophy_of_science", "access_depth": "official_abstract_and_full_argument_preview_reviewed",
        "supports": ["A theory can be insufficiently warranted for acceptance yet epistemically worthy of continued pursuit; early drift should not have been abandoned as unworthy."],
    },
    {
        "source_id": "D17", "authors": "Henry R. Frankel", "year": 2012,
        "title": "The Continental Drift Controversy", "url": "https://www.cambridge.org/core/books/continental-drift-controversy/63BC36D3F78D604E3E204234342ED804",
        "source_type": "scholarly_history_of_science", "access_depth": "official_four_volume_scope_and_relevant_summaries_reviewed",
        "supports": ["The transition developed through distinct paleomagnetic, ocean-floor-spreading, and plate-kinematic research programs rather than a single vindication event."],
    },
    {
        "source_id": "D18", "authors": "U.S. Geological Survey", "year": "1996; updated online",
        "title": "Developing the Theory of Plate Tectonics", "url": "https://pubs.usgs.gov/gip/dynamic/developing.html",
        "source_type": "official_scientific_synthesis", "access_depth": "complete_official_exposition_reviewed",
        "supports": ["Ocean-floor topography, magnetic reversals and stripes, seafloor spreading, rock ages, and earthquake-volcano localization formed a converging evidential system."],
    },
    {
        "source_id": "D19", "authors": "Ronald E. Doel", "year": 2024,
        "title": "Cold War and Earth Sciences", "url": "https://link.springer.com/rwe/10.1007/978-3-030-92679-3_25-1",
        "source_type": "scholarly_history_of_science", "access_depth": "complete_open_access_chapter_reviewed",
        "supports": ["Military patronage, new instruments, global surveys, and classification helped create both new ocean-floor knowledge and consequential domains of ignorance."],
    },
    {
        "source_id": "D20", "authors": "Dan McKenzie", "year": 2015,
        "title": "A Harbinger of Plate Tectonics: Commentary on Bullard, Everett and Smith (1965)", "url": "https://doi.org/10.1098/rsta.2014.0227",
        "source_type": "peer_reviewed_historical_commentary", "access_depth": "full_open_access_commentary_reviewed",
        "supports": ["The quantitative Atlantic fit was a kinematic bridge between continental drift and plate tectonics, explicitly distinct from a complete driving mechanism."],
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
        "study_name": "Meno-J Theory Study 5: Historical J-Jump Casebook 4",
        "case": "Continental drift, ocean-floor spreading, and plate tectonics",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_AFTER_SOURCE_SCOPING_BEFORE_FINAL_VERDICTS",
        "scope": "Historical-conceptual study only; no OpenRouter, LLM, numerical dataset, or geodynamic simulation.",
        "question": "Can Meno-J distinguish a pursuit-worthy precursor with a correct broad pattern from an acceptance-ready successor with redefined objects, mechanisms, independent predictions, and new observational infrastructure?",
        "predeclared_traps": [
            "Calling Wegener fully correct because continents move",
            "Treating plate tectonics as continental drift plus a mechanism",
            "Saying rejection occurred only because Wegener lacked a mechanism",
            "Calling all early rejection irrational or all early acceptance rational",
            "Using 1960s evidence to score Wegener's original warrant",
            "Treating continents and lithospheric plates as the same objects",
            "Calling Hess's speculative geopoetry direct proof",
            "Treating one magnetic-stripe paper as the entire revolution",
            "Ignoring failed mechanisms and inaccurate motion claims in precursor credit",
            "Treating instruments and survey infrastructure as neutral background",
            "Conflating worthiness of pursuit with warrant for acceptance",
        ],
        "success_criteria": {
            "source_records": 20, "minimum_primary_source_records": 14,
            "lineage_nodes": 8, "transition_edges": 6, "false_jump_controls": 11,
            "all_fifteen_prior_contract_rules_tested": True,
            "contemporaneous_and_retrospective_verdicts_separated": True,
        },
        "failure_conditions": [
            "The report tells a lone-genius vindication story.",
            "Wegener receives plate-tectonic credit for evidence or objects absent from his theory.",
            "Mechanism is treated as the only source of early disagreement despite contrary historiography.",
            "The report cannot state why pursuit could be rational while acceptance remained premature.",
            "Ocean-floor instrumentation and data infrastructure are omitted from causal history.",
            "Plate-boundary predictions are treated only as accommodations after the fact.",
        ],
    }


def nodes() -> list[dict[str, Any]]:
    return [
        {"node_id": "N1", "name": "Fixed-continent predecessor mosaic", "component": "land bridges, contraction, vertical movements, and regional geology", "surviving_value": "It addressed real stratigraphic, fossil, mountain-building, and isostatic observations through established field practices.", "failed_or_limited_claim": "Separate auxiliary explanations struggled to unify cross-ocean matches, paleoclimates, and later global geophysical patterns.", "verdict": "EMPIRICAL_PRACTICE_RETAINED_FRAGMENTED_GLOBAL_ARCHITECTURE_REPLACED", "sources": ["D02", "D15"]},
        {"node_id": "N2", "name": "Wegener's continental-displacement synthesis", "component": "mobile continents and reconstructed past geography", "surviving_value": "It unified continental-margin fit, matching geology and fossils, and paleoclimatic distributions under relative continental motion.", "failed_or_limited_claim": "Continents were modeled as moving through oceanic substrate under inadequate forces, with rates and reconstructions of uneven quality.", "verdict": "PURSUIT_WORTHY_PATTERN_AND_HISTORY_PRECURSOR_NOT_ACCEPTANCE_READY", "sources": ["D01", "D02", "D03", "D16"]},
        {"node_id": "N3", "name": "Interwar appraisal and criticism", "component": "mechanical, evidential, and disciplinary stress testing", "surviving_value": "Critics exposed force-scale, material, fit, and evidential problems that a mature mobility theory had to answer.", "failed_or_limited_claim": "Treating the whole research program as unworthy of pursuit overreached the available counterevidence and ignored its unifying promise.", "verdict": "ACCEPTANCE_SKEPTICISM_PARTLY_WARRANTED_PURSUIT_REJECTION_NOT_WARRANTED", "sources": ["D03", "D04", "D15", "D16"]},
        {"node_id": "N4", "name": "Holmes's mantle-circulation mechanism program", "component": "internal heat, convection, upwelling, and horizontal transport", "surviving_value": "It made internal circulation a physically motivated research path and anticipated links among spreading, sinking, and crustal movement.", "failed_or_limited_claim": "It lacked the postwar ocean-floor observations, quantitative plate boundaries, and decisive independent tests required for a complete theory.", "verdict": "PROMISING_MECHANISM_PROGRAM_NOT_COMPLETE_J_JUMP", "sources": ["D05", "D17"]},
        {"node_id": "N5", "name": "Postwar observability infrastructure", "component": "sonar bathymetry, marine magnetometry, global seismology, dating, and surveys", "surviving_value": "Previously hidden ocean-floor structure became measurable, comparable, and globally mappable.", "failed_or_limited_claim": "Data and instruments did not logically generate one theory; patronage and classification also shaped what was collected and shared.", "verdict": "EPISTEMIC_INFRASTRUCTURE_EXPANDED_TEST_SURFACE_NOT_THEORY_BY_ITSELF", "sources": ["D18", "D19"]},
        {"node_id": "N6", "name": "Hess's seafloor-spreading architecture", "component": "creation, lateral transport, and recycling of oceanic lithosphere", "surviving_value": "It redefined the moving substrate and connected ridges, ocean-basin youth, trenches, and mantle circulation.", "failed_or_limited_claim": "Initially speculative elements and mechanism details required independent empirical discrimination.", "verdict": "REPRESENTATIONAL_AND_MECHANISTIC_J_JUMP_CANDIDATE_PENDING_TESTS", "sources": ["D08", "D18"]},
        {"node_id": "N7", "name": "Independent marine and seismic discriminators", "component": "magnetic symmetry, age patterns, transform geometry, and descending seismic zones", "surviving_value": "Several new observation types tested different consequences of spreading, boundary motion, and recycling.", "failed_or_limited_claim": "No single discriminator supplied the entire global kinematic architecture or resolved all driving-force questions.", "verdict": "CONVERGENT_DISCRIMINATION_NETWORK", "sources": ["D09", "D10", "D11", "D12", "D18", "D20"]},
        {"node_id": "N8", "name": "Rigid-plate tectonic synthesis", "component": "lithospheric plates, spherical rotations, and boundary interactions", "surviving_value": "It unified continental and oceanic motion, spreading ridges, subduction zones, transforms, earthquake vectors, and reconstruction rates.", "failed_or_limited_claim": "Plate interiors are approximations and the balance among slab pull, ridge forces, mantle flow, initiation, and deep-time regimes remains research-active.", "verdict": "SURVIVING_ACCEPTANCE_READY_J_JUMP_WITH_DECLARED_APPROXIMATIONS", "sources": ["D11", "D12", "D13", "D14", "D18"]},
    ]


def transitions() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": "T1_WEGENER_SYNTHESIS", "from_nodes": ["N1"], "to_node": "N2", "claimed_component": "mobile-continent reconstruction",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Continents became historically mobile bodies rather than permanent geographic fixtures.", ["D01", "D02"]),
                "J2_retention_accounting": _criterion("PASS_PARTIAL", "Regional geology, fossils, and climate indicators were retained and reassembled, but some reconstructions and force claims failed.", ["D02"]),
                "J3_new_reach": _criterion("PASS", "One reconstruction linked observations across geology, paleontology, climatology, and geography.", ["D02"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "Global unification reduced auxiliary land bridges while creating difficult mechanical commitments.", ["D02", "D03"]),
                "J5_rival_discrimination": _criterion("PARTIAL", "Consilience favored mobility, but fits, land bridges, polar motion, and deformation histories remained disputed with limited ocean data.", ["D03", "D04"]),
                "J6_falsifiability_growth": _criterion("PASS_BUT_WEAKLY_INSTRUMENTED", "Reconstructions risked mismatch in geology, fossils, climates, and geodesy, though decisive ocean-floor tests were unavailable.", ["D02"]),
            }, "verdict": "GENUINE_PATTERN_REPRESENTATION_JUMP_PURSUIT_WORTHY_NOT_FULLY_ACCEPTANCE_READY", "unresolved": "Moving object, force, ocean-floor response, and directly measurable rates were inadequate or unclear.",
        },
        {
            "transition_id": "T2_CRITICAL_STRESS_TEST", "from_nodes": ["N2"], "to_node": "N3", "claimed_component": "contemporaneous acceptance and pursuit appraisal",
            "criteria": {
                "J1_representation_change": _criterion("NOT_APPLICABLE", "Criticism tested the proposal rather than supplying a successor representation.", ["D03", "D04"]),
                "J2_retention_accounting": _criterion("PASS_AS_AUDIT", "It preserved anomalous observations while challenging whether drift explained them physically.", ["D04"]),
                "J3_new_reach": _criterion("PARTIAL", "Mechanical estimates and field standards exposed new requirements but did not unify the phenomena.", ["D03", "D15"]),
                "J4_complexity_dimensions": _criterion("NOT_APPLICABLE", "The episode concerns evaluation thresholds rather than compression.", ["D15", "D16"]),
                "J5_rival_discrimination": _criterion("PASS_FOR_ACCEPTANCE_PARTIAL_FOR_PURSUIT", "Objections weakened full acceptance, but did not show the mobile research program lacked future promise.", ["D15", "D16"]),
                "J6_falsifiability_growth": _criterion("PASS", "Critics sharpened force, fit, material, and evidential tests that successors had to meet.", ["D03", "D04"]),
            }, "verdict": "VALUABLE_AUDIT_NOT_J_JUMP_ACCEPTANCE_AND_PURSUIT_MUST_SPLIT", "unresolved": "Different scientific communities weighted direct versus synthetic evidence differently.",
        },
        {
            "transition_id": "T3_HOLMES_MECHANISM", "from_nodes": ["N2", "N3"], "to_node": "N4", "claimed_component": "mantle-circulation research program",
            "criteria": {
                "J1_representation_change": _criterion("PASS_CANDIDATE", "Internal heat-driven circulation replaced surface tidal and rotational forcing as a possible transport system.", ["D05"]),
                "J2_retention_accounting": _criterion("PASS_PARTIAL", "Continental mobility was retained while its proposed driving forces were replaced.", ["D05"]),
                "J3_new_reach": _criterion("PASS_CONCEPTUAL", "Upwelling, lateral flow, and sinking offered a common architecture for extension and compression.", ["D05"]),
                "J4_complexity_dimensions": _criterion("PARTIAL", "The picture unified processes but lacked constrained rheology and global boundary calculation.", ["D05"]),
                "J5_rival_discrimination": _criterion("FAIL_AT_TIME", "Available observations did not uniquely select the circulation geometry over rivals.", ["D17"]),
                "J6_falsifiability_growth": _criterion("PARTIAL", "It suggested spatial associations but lacked a mature quantitative prediction program.", ["D05"]),
            }, "verdict": "MECHANISM_PROGRAM_WORTHY_OF_PURSUIT_NOT_ACCEPTANCE_READY", "unresolved": "Direct ocean-floor and deep-Earth tests were not yet available.",
        },
        {
            "transition_id": "T4_SEAFLOOR_REDEFINITION", "from_nodes": ["N2", "N4", "N5"], "to_node": "N6", "claimed_component": "mobile and renewable oceanic substrate",
            "criteria": {
                "J1_representation_change": _criterion("PASS_MAJOR", "The moving unit changed from continents crossing fixed seafloor to a coupled surface where new ocean floor forms and old floor returns.", ["D08"]),
                "J2_retention_accounting": _criterion("PASS", "Relative continental separation survived, while the plowing mechanism and permanent ocean floor were rejected.", ["D02", "D08"]),
                "J3_new_reach": _criterion("PASS", "Ridges, trenches, ocean-floor youth, sediment patterns, and continental separation entered one cyclic architecture.", ["D08", "D18"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "A conveyor-like system unified ocean basins but introduced mantle and recycling commitments.", ["D08"]),
                "J5_rival_discrimination": _criterion("PARTIAL_PENDING_TESTS", "It generated distinctive consequences but was initially presented as geopoetry requiring independent checks.", ["D08", "D17"]),
                "J6_falsifiability_growth": _criterion("PASS", "It risked failure on symmetry, ages, sediments, ridge flux, trenches, and global closure.", ["D08", "D18"]),
            }, "verdict": "OBJECT_REDEFINITION_AND_MECHANISM_J_JUMP_CANDIDATE", "unresolved": "The predicted records needed independent observational confirmation.",
        },
        {
            "transition_id": "T5_CONVERGENT_DISCRIMINATION", "from_nodes": ["N5", "N6"], "to_node": "N7", "claimed_component": "independent prediction and evidence network",
            "criteria": {
                "J1_representation_change": _criterion("PASS_EMPIRICAL_ENCODING", "Oceanic crust became a time-ordered magnetic record and boundaries became kinematically typed structures.", ["D09", "D11"]),
                "J2_retention_accounting": _criterion("PASS", "Margin fit and paleomagnetic mobility were retained while being tied to spreading, transforms, and sinking slabs.", ["D06", "D09", "D10", "D12"]),
                "J3_new_reach": _criterion("PASS", "The framework predicted stripe symmetry and rates, correct transform sense, deep slab geometry, and quantitative reconstructions.", ["D09", "D10", "D11", "D12"]),
                "J4_complexity_dimensions": _criterion("PASS", "Several independent datasets became mutually constraining parts of one boundary system.", ["D18"]),
                "J5_rival_discrimination": _criterion("PASS_STRONG", "Symmetric reversals, transform geometry, and dipping seismic zones were much harder for fixed or expanding alternatives to reproduce jointly.", ["D09", "D11", "D12"]),
                "J6_falsifiability_growth": _criterion("PASS_STRONG", "Each independent data family supplied its own failure surface and cross-checks on rates and directions.", ["D09", "D10", "D11", "D12"]),
            }, "verdict": "SURVIVING_CONVERGENT_EVIDENTIAL_J_JUMP", "unresolved": "A global rigid-plate kinematics still had to close motions consistently on a sphere.",
        },
        {
            "transition_id": "T6_RIGID_PLATE_SYNTHESIS", "from_nodes": ["N6", "N7"], "to_node": "N8", "claimed_component": "global spherical plate kinematics",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Continents and oceanic lithosphere became parts of rigid plates separated by spreading, transform, and subduction boundaries.", ["D13", "D14"]),
                "J2_retention_accounting": _criterion("PASS_EXPLICIT", "Wegener's relative continental histories, Holmes-Hess mobility, and boundary evidence were recovered within a new moving object.", ["D02", "D08", "D13", "D14"]),
                "J3_new_reach": _criterion("PASS", "Euler rotations connected slip vectors, spreading rates, transforms, trenches, and reconstructions quantitatively.", ["D13", "D14"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_APPROXIMATION", "A small set of plate rotations compressed global surface motion while idealizing intraplate deformation.", ["D13", "D14"]),
                "J5_rival_discrimination": _criterion("PASS", "Closed spherical motions and boundary-consistent vectors distinguished the synthesis from loose continental mobility.", ["D13", "D14"]),
                "J6_falsifiability_growth": _criterion("PASS", "Predicted velocities, fault senses, boundary locations, earthquake vectors, and reconstruction closure could independently fail.", ["D13", "D14"]),
            }, "verdict": "SURVIVING_ACCEPTANCE_READY_GLOBAL_J_JUMP", "unresolved": "Driving-force partition, diffuse boundaries, plate initiation, and early-Earth applicability remain domain-specific research questions.",
        },
    ]


def controls() -> list[dict[str, str]]:
    return [
        {"control_id": "G1", "false_claim": "Wegener merely noticed that coastlines fit.", "verdict": "REJECT_EVIDENCE_ERASURE", "reason": "His case integrated geological, fossil, climatic, geographical, and attempted geodetic evidence."},
        {"control_id": "G2", "false_claim": "Plate tectonics proved Wegener's complete theory correct.", "verdict": "REJECT_RETROSPECTIVE_SCOPE_INFLATION", "reason": "Plate theory changed the moving object, rejected plowing and weak forces, and added ocean-floor creation, recycling, and boundaries."},
        {"control_id": "G3", "false_claim": "Early critics were simply irrational conservatives.", "verdict": "REJECT_HEROIC_MARTYR_MYTH", "reason": "Mechanical and evidential objections were serious even though abandoning pursuit was not warranted."},
        {"control_id": "G4", "false_claim": "Lack of mechanism alone explains American rejection.", "verdict": "REJECT_MONOCAUSAL_HISTORIOGRAPHY", "reason": "Disciplinary evidential standards and methodological preferences also shaped rejection."},
        {"control_id": "G5", "false_claim": "A theory worthy of pursuit should already be accepted as true.", "verdict": "REJECT_STANCE_COLLAPSE", "reason": "Promising unification can justify research before evidence justifies belief or operational adoption."},
        {"control_id": "G6", "false_claim": "Holmes had already completed plate tectonics in 1929.", "verdict": "REJECT_FORERUNNER_COMPLETION", "reason": "He proposed a fruitful mechanism family without the later oceanic object, boundaries, kinematics, or discriminators."},
        {"control_id": "G7", "false_claim": "Hess directly proved seafloor spreading.", "verdict": "REJECT_SPECULATION_AS_PROOF", "reason": "His architecture created risky predictions whose warrant came from later independent evidence."},
        {"control_id": "G8", "false_claim": "Vine and Matthews alone discovered plate tectonics.", "verdict": "REJECT_SINGLE_PAPER_REVOLUTION", "reason": "Magnetic stripes were one powerful link within paleomagnetic, bathymetric, seismic, fault, and kinematic programs."},
        {"control_id": "G9", "false_claim": "Continents are tectonic plates.", "verdict": "REJECT_OBJECT_EQUIVOCATION", "reason": "Plates can contain both oceanic and continental lithosphere, and some continents span or interact with multiple plates."},
        {"control_id": "G10", "false_claim": "New instruments automatically produced the correct theory.", "verdict": "REJECT_DATA_DETERMINISM", "reason": "Theory guided interpretation, while patronage, sampling, secrecy, and disciplinary choices shaped the observable record."},
        {"control_id": "G11", "false_claim": "Acceptance in the 1960s settled every mechanism and domain question.", "verdict": "REJECT_FINAL_THEORY_MYTH", "reason": "Plate kinematics is strongly established while driving forces, diffuse deformation, initiation, and deep-time regimes remain active research areas."},
    ]


def prior_rule_tests() -> list[dict[str, str]]:
    values = [
        ("A1_RETENTION_ACCOUNTING", "Wegener's mobility and reconstructions survive selectively; his forces and moving-object model do not."),
        ("A2_COMPONENT_SCOPING", "Pattern, reconstruction, mechanism, ocean-floor renewal, boundary types, and kinematics require separate verdicts."),
        ("A3_COMPRESSION_DIMENSIONS", "Global plate rotations compress surface motion while adding observational and computational machinery."),
        ("A4_APPROXIMATION_BOUNDARY", "Rigid plates and sharp boundaries are strong approximations, not universal literal descriptions."),
        ("A5_UNDERDETERMINATION", "Early cross-ocean matches supported mobility without uniquely determining plate tectonics."),
        ("A6_DISTRIBUTED_LINEAGE_GRAPH", "The successor arose across drift, paleomagnetism, oceanography, seismology, and spherical kinematics."),
        ("A7_INTERVENTION_MECHANISM_DECOUPLING", "Generalized: accurate reconstruction can precede a valid transport mechanism."),
        ("A8_EVIDENCE_TRIANGULATION_LADDER", "Independent magnetic, age, seismic, geometric, and fault evidence supplied convergent warrant."),
        ("A9_RELATIONAL_CAUSAL_SCOPE", "Relative motion, driving force, material transport, and boundary response are different claims."),
        ("A10_DISCOVERY_UPTAKE_OUTCOME_SEPARATION", "Early proposal, research pursuit, disciplinary rejection, and later acceptance followed distinct timelines."),
        ("A11_FORMAL_ONTOLOGY_DECOUPLING", "Continental reconstructions can survive while the ontology of continents plowing through sima fails."),
        ("A12_CONSTRAINT_MECHANISM_LAYERING", "Kinematics, boundary constraints, and mantle-driving mechanisms occupy different explanatory layers."),
        ("A13_BRIDGE_LAW_REQUIREMENT", "Plate rotations and boundary vectors bridge global objects to measurable local motions."),
        ("A14_TRANSITION_ROLE_TAXONOMY", "Wegener was a synthesis precursor; Holmes a mechanism program; Hess an architecture; later work supplied discriminators and kinematics."),
        ("A15_LAYERED_SUCCESSOR_TEST", "Plate kinematics, geodynamics, seismology, and geological reconstruction coexist as constrained layers."),
    ]
    return [{"rule_id": key, "status": "PASS_AND_ESSENTIAL", "finding": finding} for key, finding in values]


def extension() -> dict[str, Any]:
    return {
        "extension_name": "Historical Calibration Extension 4",
        "trigger": "The case requires scoring a precursor using only contemporaneous evidence, separating pursuit from acceptance, recognizing redefinition of the theoretical object, and treating observability infrastructure as part of the test architecture.",
        "prior_rule_status": prior_rule_tests(),
        "extensions": [
            {"extension_id": "A16_HINDSIGHT_FIREWALL", "new_rule": "Partition evidence by availability date and issue a contemporaneous verdict before adding retrospective evidence. Never credit a precursor with later instruments, observations, concepts, or successful descendants.", "guardrail": "Later vindication can update lineage credit but cannot rewrite the warrant originally available.", "sources": ["D02", "D15", "D16", "D17"]},
            {"extension_id": "A17_EPISTEMIC_STANCE_LADDER", "new_rule": "Score rejection, non-acceptance, pursuit, provisional use, and acceptance separately. A hypothesis may rationally merit pursuit while rationally failing the acceptance threshold.", "guardrail": "Promising is not true; premature non-acceptance is not the same as suppressing further investigation.", "sources": ["D04", "D16"]},
            {"extension_id": "A18_OBJECT_REDEFINITION_TEST", "new_rule": "Record whether the successor preserves the predecessor's objects or replaces them. If the moving, causal, or measured object changes, treat the relation as transformation rather than simple confirmation.", "guardrail": "Shared surface vocabulary such as drift does not establish identity between continents and lithospheric plates.", "sources": ["D02", "D08", "D13", "D14"]},
            {"extension_id": "A19_INDEPENDENT_PREDICTION_LEDGER", "new_rule": "For each evidential success, record whether it was used to construct, tune, or independently test the proposal, and whether it discriminates against named rivals jointly or only in isolation.", "guardrail": "Do not count multiple transformations of one dataset as independent convergence or call post-hoc fit a novel prediction.", "sources": ["D09", "D10", "D11", "D12", "D18"]},
            {"extension_id": "A20_OBSERVABILITY_FRONTIER", "new_rule": "Record which claims were untestable under the available measurement infrastructure and which new instruments, surveys, access, funding, or data-sharing changes expanded the falsification surface.", "guardrail": "Do not treat infrastructure as automatic truth production; document sampling, classification, and institutional selection effects.", "sources": ["D18", "D19"]},
        ],
        "revised_j_jump_object": "A hindsight-controlled lineage subgraph with separate pursuit and acceptance verdicts, explicit object identity or redefinition, independently classified predictions, dated observability limits, and a successor architecture that survives cross-domain closure tests.",
    }


def report(protocol_hash: str, study4_hash: str, extension_hash: str) -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 5: Historical J-Jump Casebook 4",
        "case": "Continental drift, ocean-floor spreading, and plate tectonics",
        "method": {
            "protocol_sha256": protocol_hash, "study_4_report_sha256": study4_hash, "study_4_extension_sha256": extension_hash,
            "mode": "primary-source-led hindsight-controlled historical falsification study",
            "llm_or_api_calls": False, "dataset_or_simulation_calls": False, "source_count": len(SOURCES),
        },
        "sources": SOURCES, "lineage_nodes": nodes(), "transition_edges": transitions(), "false_jump_controls": controls(),
        "prior_contract_rule_tests": prior_rule_tests(), "contract_extension": extension(),
        "results": {
            "wegener_contemporaneous_pursuit_verdict": "WORTHY_OF_PURSUIT",
            "wegener_contemporaneous_acceptance_verdict": "NOT_YET_ACCEPTANCE_READY",
            "plate_tectonics_relation_to_wegener": "SELECTIVE_RETENTION_PLUS_OBJECT_REDEFINITION_NOT_SIMPLE_VINDICATION",
            "prior_contract_generalized": True, "prior_contract_sufficient_unchanged": False,
            "full_transition_verdict": "SURVIVING_HINDSIGHT_CONTROLLED_DISTRIBUTED_J_JUMP",
            "significant_findings": [
                "Wegener's program deserved continued pursuit even though full acceptance was premature; Meno-J must separate those epistemic decisions.",
                "Plate tectonics did not merely add a mechanism to continental drift: it redefined the moving object from continents to lithospheric plates containing continental and oceanic material.",
                "The strongest warrant came from independent cross-domain closure—magnetic symmetry, ages, transform geometry, deep seismic zones, and spherical motion—not from retrospective resemblance alone.",
                "Rejection was historically multi-causal: mechanical objections mattered, but disciplinary standards concerning direct and synthetic evidence also shaped appraisal.",
                "New instruments and surveys expanded what could be falsified; observability infrastructure is therefore part of scientific reasoning, not invisible background.",
                "For AI J-jumps, the target is a pursuit-worthy new representation that states what future observation would make it acceptance-ready, not a confident claim of present truth.",
            ],
        },
        "decision": "CASEBOOK_4_SUCCESS_PURSUIT_ACCEPTANCE_SPLIT_AND_OBJECT_REDEFINITION_ADDED",
        "next_case": {
            "name": "Ulcers: stress and acid to Helicobacter pylori and interaction models",
            "reason": "This tests whether Meno-J can distinguish pathogen discovery, intervention success, causal contribution, host variability, and later multifactorial correction without repeating the germ-theory case mechanically.",
            "stop_condition": "If the present twenty-rule contract only restates case-specific history without changing decisions, stop adding cases and formalize a minimal executable scoring protocol.",
        },
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = ["# Meno-J Theory Study 5 Protocol", "", f"**Case:** {value['case']}", "", f"**Question:** {value['question']}", "", f"Status: `{value['status']}`", "", "## Predeclared traps", ""]
    lines.extend(f"- {item}" for item in value["predeclared_traps"])
    lines.extend(["", "## Failure conditions", ""])
    lines.extend(f"- {item}" for item in value["failure_conditions"])
    lines.append("")
    return "\n".join(lines)


def render_report_md(value: dict[str, Any]) -> str:
    lines = [
        "# Historical J-Jump Casebook 4: Continental Drift → Plate Tectonics", "", "## Outcome", "",
        f"Decision: **{value['decision']}**.", "",
        "Wegener was neither simply vindicated nor simply wrong. His synthesis was **worthy of pursuit but not yet ready for acceptance**. Plate tectonics later changed the moving object and supplied a distributed mechanism-and-test architecture.", "",
        "```text",
        "Wegener: cross-domain continental mobility ──→ pursuit-worthy precursor",
        "            ├→ criticism: force + evidence requirements",
        "            └→ Holmes: mantle-circulation program",
        "postwar sonar + magnetometry + seismology ─→ Hess: renewable ocean floor",
        "Hess + magnetic stripes + transforms + slabs ─→ rigid plates on a sphere",
        "```", "", "## Node verdicts", "", "| Node | Surviving component | Failed or limited component | Verdict |", "|---|---|---|---|",
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
    lines.extend(["", "All fifteen prior rules generalized, but they were not sufficient unchanged.", "", "## New contract extensions", ""])
    for item in value["contract_extension"]["extensions"]:
        lines.extend([f"### {item['extension_id']}", "", f"**Rule:** {item['new_rule']}", "", f"Guardrail: {item['guardrail']}", ""])
    lines.extend(["## What this changes for Meno-J", "", "Meno-J should be able to recommend that a strange hypothesis deserves targeted investigation without claiming it is already true. It must specify the missing observation, instrument, mechanism, or independent prediction that would move the hypothesis from pursuit to acceptance.", "", f"**Revised J-jump object:** {value['contract_extension']['revised_j_jump_object']}", "", "## Significant findings", ""])
    lines.extend(f"- {item}" for item in value["results"]["significant_findings"])
    lines.extend(["", "## Next case", "", f"**{value['next_case']['name']}** — {value['next_case']['reason']}", "", f"Stop condition: {value['next_case']['stop_condition']}", "", "## Sources", ""])
    for source in value["sources"]:
        lines.append(f"- **{source['source_id']} — [{source['title']}]({source['url']})** ({source['authors']}, {source['year']}). `{source['access_depth']}`. {' '.join(source['supports'])}")
    lines.append("")
    return "\n".join(lines)


def render_extension_md(value: dict[str, Any]) -> str:
    lines = ["# Meno-J J-Jump Contract: Historical Calibration Extension 4", "", f"**Trigger:** {value['trigger']}", "", "## Prior rules", ""]
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
    for path in (STUDY4_REPORT, STUDY4_EXTENSION, STUDY4_VALIDATION):
        if not path.is_file():
            raise FileNotFoundError(f"Missing validated Study 4 prerequisite: {path}")
    if _read_json(STUDY4_VALIDATION).get("status") != "PASS":
        raise ValueError("Theory Study 4 validation must be PASS.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = protocol()
    _atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")
    result = report(_sha256(PROTOCOL_JSON), _sha256(STUDY4_REPORT), _sha256(STUDY4_EXTENSION))
    _atomic_json(REPORT_JSON, result)
    REPORT_MD.write_text(render_report_md(result), encoding="utf-8")
    _atomic_json(EXTENSION_JSON, result["contract_extension"])
    EXTENSION_MD.write_text(render_extension_md(result["contract_extension"]), encoding="utf-8")
    reproducibility = {
        "study_name": result["study_name"], "status": "BUILT_PENDING_INDEPENDENT_VALIDATION", "execution_date": date.today().isoformat(),
        "input_hashes": {"protocol": _sha256(PROTOCOL_JSON), "study_4_report": _sha256(STUDY4_REPORT), "study_4_extension": _sha256(STUDY4_EXTENSION), "study_4_validation": _sha256(STUDY4_VALIDATION)},
        "output_hashes": {"report_json": _sha256(REPORT_JSON), "report_markdown": _sha256(REPORT_MD), "extension_json": _sha256(EXTENSION_JSON), "extension_markdown": _sha256(EXTENSION_MD)},
        "runner": str(Path(__file__).resolve()), "runner_sha256": _sha256(Path(__file__).resolve()),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False, "simulation": False}, "encoding": "UTF-8", "source_access_limits_recorded": True,
    }
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 5 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n- OpenRouter/LLM calls: **none**\n- Dataset/simulation calls: **none**\n- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n- Study 4 report SHA-256: `{reproducibility['input_hashes']['study_4_report']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n- Runner SHA-256: `{reproducibility['runner_sha256']}`\n",
        encoding="utf-8",
    )
    print(f"Built {REPORT_JSON.name} and contract extension")


if __name__ == "__main__":
    main()
