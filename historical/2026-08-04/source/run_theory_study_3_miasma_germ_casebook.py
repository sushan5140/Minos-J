"""Build historical J-jump Casebook 2: miasma, transmission, and germ theories."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STUDY2_REPORT = OUTPUT_DIR / "meno_j_theory_study_2_ptolemy_kepler_newton.json"
STUDY2_AMENDMENT = OUTPUT_DIR / "meno_j_theory_study_2_contract_amendment.json"
STUDY2_VALIDATION = OUTPUT_DIR / "meno_j_theory_study_2_validation.json"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_3_miasma_germ_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_3_miasma_germ_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_3_miasma_germ_casebook.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_3_miasma_germ_casebook.md"
AMENDMENT_JSON = OUTPUT_DIR / "meno_j_theory_study_3_contract_extension.json"
AMENDMENT_MD = OUTPUT_DIR / "meno_j_theory_study_3_contract_extension.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_3_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_3_reproducibility_summary.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "B01",
        "authors": "John Snow",
        "year": 1855,
        "title": "On the Mode of Communication of Cholera, second edition",
        "url": "https://www.gutenberg.org/ebooks/72894",
        "source_type": "primary_source",
        "access_depth": "complete_public_domain_text_available_and_argument_reviewed",
        "supports": ["Snow argued for a disease-specific waterborne route using outbreak comparisons, exceptions, and water-supply evidence rather than a cultured organism."],
    },
    {
        "source_id": "B02",
        "authors": "John Snow; Wellcome Collection",
        "year": 1855,
        "title": "On the Mode of Communication of Cholera",
        "url": "https://wellcomecollection.org/works/uqa27qrt",
        "source_type": "primary_source_archive",
        "access_depth": "official_complete_scan_record",
        "supports": ["The enlarged edition included household deaths and water-supply evidence, not only the famous map."],
    },
    {
        "source_id": "B03",
        "authors": "Ignaz Philipp Semmelweis",
        "year": 1861,
        "title": "Die Aetiologie, der Begriff und die Prophylaxis des Kindbettfiebers",
        "url": "https://books.google.com/books/about/Die_Aetiologie_der_Begriff_und_die_Proph.html?id=MlpO45_11l4C",
        "source_type": "primary_source",
        "access_depth": "complete_original_german_scan_and_selected_argument_review",
        "supports": ["Semmelweis presented mortality tables, cadaveric and other decaying material, chlorine washing, and competing etiological claims."],
    },
    {
        "source_id": "B04",
        "authors": "Louis Pasteur",
        "year": 1861,
        "title": "On the Organized Corpuscles Existing in the Atmosphere",
        "url": "https://fr.wikisource.org/wiki/Sur_les_corpuscules_organis%C3%A9s_qui_existent_dans_l%E2%80%99atmosph%C3%A8re",
        "source_type": "primary_source_transcription",
        "access_depth": "complete_french_transcription_and_scan_review",
        "supports": ["Pasteur framed spontaneous generation as an experimental question and argued that apparent generation resulted from unnoticed contamination or experimental error."],
    },
    {
        "source_id": "B05",
        "authors": "Louis Pasteur; Smithsonian Libraries and Archives",
        "year": 1857,
        "title": "Memoir on Lactic Fermentation",
        "url": "https://www.si.edu/object/siris_sil_138569",
        "source_type": "primary_source_archive",
        "access_depth": "official_archival_record_and_selected_primary_text_review",
        "supports": ["Pasteur connected a specific fermentation process with living microorganisms, contributing a laboratory ontology broader than a single epidemic route."],
    },
    {
        "source_id": "B06",
        "authors": "Robert Koch",
        "year": 1876,
        "title": "The Etiology of Anthrax Based on the Developmental History of Bacillus anthracis",
        "url": "https://zenodo.org/records/7425627",
        "source_type": "primary_source_archive",
        "access_depth": "complete_original_german_paper_available_and_argument_reviewed",
        "supports": ["Koch linked a particular organism and life cycle to anthrax using microscopy, cultivation, and transmission experiments."],
    },
    {
        "source_id": "B07",
        "authors": "Robert Koch; Robert Koch Institute",
        "year": 1882,
        "title": "The Etiology of Tuberculosis",
        "url": "https://edoc.rki.de/handle/176904/5163?locale-attribute=en",
        "source_type": "primary_source_official_archive",
        "access_depth": "complete_original_paper_from_official_institute_archive",
        "supports": ["Koch used staining, repeated detection, culture, and inoculation to argue for a specific infectious cause of tuberculosis."],
    },
    {
        "source_id": "B08",
        "authors": "Robert Koch; German History Intersections",
        "year": "1882/1932 translation",
        "title": "The Aetiology of Tuberculosis, English excerpts",
        "url": "https://germanhistory-intersections.org/en/knowledge-and-education/ghis%3Adocument-25",
        "source_type": "primary_source_translation",
        "access_depth": "documented_english_translation_excerpts",
        "supports": ["Koch treated tuberculosis as a specific infectious disease and connected etiology with possible prevention."],
    },
    {
        "source_id": "B09",
        "authors": "Margaret Pelling",
        "year": 2022,
        "title": "Mythological Endings: John Snow and the History of American Epidemiology",
        "url": "https://www.brepolsonline.net/doi/full/10.1484/J.CNT.5.130194",
        "source_type": "peer_reviewed_history",
        "access_depth": "full_text_argument_review",
        "supports": ["The claim that pump-handle removal ended the Broad Street epidemic is a durable heroic myth rather than the evidential core of Snow's work."],
    },
    {
        "source_id": "B10",
        "authors": "Raphael Scholl",
        "year": 2013,
        "title": "Causal Inference, Mechanisms, and the Semmelweis Case",
        "url": "https://philsci-archive.pitt.edu/9556/1/scholl-shps-2013.pdf",
        "source_type": "peer_reviewed_philosophy_and_history",
        "access_depth": "full_preprint_argument_review",
        "supports": ["Semmelweis combined comparative causal reasoning, quantitative tables, intervention evidence, and animal experiments; later retellings often omit crucial tables and experiments."],
    },
    {
        "source_id": "B11",
        "authors": "Dana Tulodziecki",
        "year": 2013,
        "title": "Shattering the Myth of Semmelweis",
        "url": "https://www.cambridge.org/core/journals/philosophy-of-science/article/abs/shattering-the-myth-of-semmelweis/87CDEDEB824A21443156437677CE5A83",
        "source_type": "peer_reviewed_philosophy_of_science",
        "access_depth": "official_abstract_and_reference_review",
        "supports": ["The standard portrayal of Semmelweis as an unambiguously excellent reasoner is contested and should not be treated as settled history."],
    },
    {
        "source_id": "B12",
        "authors": "Michael Worboys",
        "year": 2007,
        "title": "Was There a Bacteriological Revolution in Late Nineteenth-Century Medicine?",
        "url": "https://research.manchester.ac.uk/en/publications/was-there-a-bacteriological-revolution-in-late-nineteenth-century/",
        "source_type": "peer_reviewed_history_of_medicine",
        "access_depth": "official_abstract_and_detailed_argument_record",
        "supports": ["Bacteriological change was uneven across diseases and practices; a single rapid British revolution remains historically unproven."],
    },
    {
        "source_id": "B13",
        "authors": "Pierre-Olivier Méthot and Samuel Alizon",
        "year": 2014,
        "title": "What Is a Pathogen? Toward a Process View of Host-Parasite Interactions",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4601502/",
        "source_type": "peer_reviewed_philosophy_and_biology",
        "access_depth": "full_text_argument_review",
        "supports": ["Pathogenicity depends on host-microbe interactions; pure-culture rules face carriers, unculturable agents, variable hosts, and artificial inoculation limits."],
    },
    {
        "source_id": "B14",
        "authors": "Christoph Gradmann",
        "year": 2014,
        "title": "A Spirit of Scientific Rigour: Koch's Postulates in Twentieth-Century Medicine",
        "url": "https://www.sciencedirect.com/science/article/pii/S1286457914001270",
        "source_type": "peer_reviewed_history_of_medicine",
        "access_depth": "official_abstract_and_argument_summary",
        "supports": ["The textbook three-step postulate story simplifies Koch's changing practice, and later medicine repeatedly adapted causal criteria to agents and carrier states."],
    },
    {
        "source_id": "B15",
        "authors": "Samantha Vanderslott; Maile T. Phillips; Virginia E. Pitzer; Claas Kirchhelle",
        "year": 2019,
        "title": "Water and Filth: Reevaluating the First Era of Sanitary Typhoid Intervention",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6792102/",
        "source_type": "peer_reviewed_history_of_public_health",
        "access_depth": "full_text_argument_review",
        "supports": ["Miasmatic and sanitary reformers promoted environmental and sewer interventions whose practical effects cannot be evaluated solely by whether their causal theory was correct."],
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
        "study_name": "Meno-J Theory Study 3: Historical J-Jump Casebook 2",
        "case": "Miasma, sanitation, transmission, and germ theories",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_AFTER_SOURCE_SCOPING_BEFORE_FINAL_NETWORK_VERDICTS",
        "scope": "Historical and conceptual analysis only; no medical recommendation, patient data, numerical experiment, LLM, or OpenRouter call.",
        "question": "Does the amended J-jump contract distinguish practical sanitation success, transmission-route discovery, intervention evidence, microbial ontology, and disease-specific causal proof without inventing a single-hero germ-theory revolution?",
        "predeclared_nodes": [
            "miasmatic and sanitary environmental frameworks",
            "Snow's cholera transmission-route account",
            "Semmelweis's hand-disinfection intervention and cadaveric-material account",
            "Pasteur's fermentation and anti-spontaneous-generation laboratory program",
            "Koch's disease-specific experimental etiology",
            "later host-pathogen-environment process corrections",
        ],
        "predeclared_traps": [
            "Saying Snow identified or cultured the cholera germ",
            "Saying pump-handle removal ended the already-waning epidemic",
            "Inferring Semmelweis's entire etiology from successful hand disinfection",
            "Treating miasma or contagionism as one uniform predecessor theory",
            "Treating Pasteur or Koch as the single inventor of germ theory",
            "Treating Koch's postulates as Koch's fixed universal rule for every pathogen",
            "Treating sanitation success as evidence that foul air was the causal agent",
            "Replacing miasmatic monocausality with microbial monocausality and ignoring host and environment",
        ],
        "success_criteria": {
            "minimum_source_records": 14,
            "minimum_primary_source_records": 8,
            "minimum_transition_nodes": 4,
            "minimum_false_jump_controls": 7,
            "all_claims_map_to_source_ids": True,
            "study_2_amendments_receive_explicit_stress_verdicts": True,
            "new_contract_failure_triggers_extension": True,
            "medical_scope_warning_present": True,
        },
        "failure_conditions": [
            "The report tells a linear miasma-to-germ victory story.",
            "An effective intervention is treated as sufficient proof of the proposed mechanism.",
            "Snow, Semmelweis, Pasteur, or Koch is credited with the whole transition.",
            "The report ignores conflicting scholarly assessments of Semmelweis.",
            "The report treats infection as a one-pathogen/one-outcome relation in every host.",
            "The first historical amendment is silently changed rather than tested.",
        ],
    }


def _criterion(status: str, reason: str, sources: list[str]) -> dict[str, Any]:
    return {"status": status, "reason": reason, "sources": sources}


def nodes() -> list[dict[str, Any]]:
    return [
        {
            "node_id": "N1",
            "name": "Miasmatic and sanitary frameworks",
            "component": "environmental localization and public-health intervention",
            "surviving_value": "They focused attention on filth, crowding, drainage, water, waste, ventilation, and municipal responsibility; several resulting interventions reduced real exposure routes.",
            "failed_or_limited_claim": "A generic disease-causing foul-air emanation did not identify disease-specific agents or reliably distinguish air, water, contact, vector, and host pathways.",
            "verdict": "PRACTICAL_AND_ENVIRONMENTAL_COMPONENTS_PARTLY_RETAINED_CAUSAL_AGENT_REJECTED",
            "sources": ["B12", "B15"],
        },
        {
            "node_id": "N2",
            "name": "Snow's cholera transmission account",
            "component": "disease-specific route and comparative epidemiology",
            "surviving_value": "It used household exceptions, spatial patterns, and differing water supplies to support ingestion of contaminated water as cholera's route.",
            "failed_or_limited_claim": "It did not isolate the causal organism, and pump-handle removal was not the decisive experiment that ended the outbreak.",
            "verdict": "SURVIVING_ROUTE_LEVEL_J_JUMP_NOT_A_GERM_IDENTIFICATION",
            "sources": ["B01", "B02", "B09"],
        },
        {
            "node_id": "N3",
            "name": "Semmelweis's puerperal-fever program",
            "component": "contact pathway, intervention, and partial material mechanism",
            "surviving_value": "Comparative mortality, chlorine hand disinfection, and mechanistic experiments supported transmission of harmful material by attendants and a lifesaving control practice.",
            "failed_or_limited_claim": "Intervention success did not validate every etiological or monocausal statement, and historians disagree about the quality and completeness of his reasoning.",
            "verdict": "SURVIVING_INTERVENTION_AND_CONTACT_COMPONENT_CONTESTED_FULL_ETIOLOGY",
            "sources": ["B03", "B10", "B11"],
        },
        {
            "node_id": "N4",
            "name": "Pasteur's microbial laboratory program",
            "component": "microbial ontology, contamination controls, and experimental laboratory method",
            "surviving_value": "Fermentation and anti-spontaneous-generation work made living microorganisms and controlled contamination experimentally productive explanatory entities.",
            "failed_or_limited_claim": "These results did not by themselves establish that one particular microorganism caused each particular human disease.",
            "verdict": "SURVIVING_ONTOLOGICAL_AND_METHOD_JUMP_NOT_COMPLETE_DISEASE_ETIOLOGY",
            "sources": ["B04", "B05"],
        },
        {
            "node_id": "N5",
            "name": "Koch's disease-specific experimental etiology",
            "component": "agent-disease linkage through visualization, culture, transmission, and pathology",
            "surviving_value": "Anthrax and tuberculosis studies joined a specific organism to a specific disease using converging laboratory evidence.",
            "failed_or_limited_claim": "Pure-culture criteria do not universally fit viruses, unculturable agents, asymptomatic carriers, polymicrobial disease, or variable host responses.",
            "verdict": "SURVIVING_DISEASE_SPECIFIC_CAUSAL_METHOD_WITH_DECLARED_DOMAIN_LIMITS",
            "sources": ["B06", "B07", "B08", "B13", "B14"],
        },
        {
            "node_id": "N6",
            "name": "Host-pathogen-environment process view",
            "component": "relational pathogenicity and multilevel disease causation",
            "surviving_value": "It preserves microbes as causal participants while explaining carriers, variable susceptibility, virulence, dose, immunity, co-infection, and environmental exposure.",
            "failed_or_limited_claim": "A generic process slogan is not enough; each claimed causal contribution still needs disease-specific evidence.",
            "verdict": "CORRECTIVE_EXTENSION_OF_GERM_CAUSATION_NOT_RETURN_TO_MIASMA",
            "sources": ["B13", "B14"],
        },
    ]


def transitions() -> list[dict[str, Any]]:
    return [
        {
            "transition_id": "T1_ROUTE",
            "from_nodes": ["N1"],
            "to_node": "N2",
            "claimed_component": "cholera transmission route",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "A generic atmospheric/environmental cause was replaced for cholera by a specific ingestion and water-supply pathway.", ["B01"]),
                "J2_retention_accounting": _criterion("PASS_NONRETENTIVE_SUCCESS_ACCOUNTING", "Environmental clustering and clean-water benefits were retained as phenomena and re-explained through contaminated water, without retaining foul air as the agent.", ["B01", "B15"]),
                "J3_new_reach": _criterion("PASS", "The route explained household exceptions, occupational exposure, and contrasting water-company mortality that generic miasma could not isolate.", ["B01", "B02"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "The causal route was more specific and conceptually narrower, while exposure tracing and population comparisons increased evidential work.", ["B01"]),
                "J5_rival_discrimination": _criterion("PASS", "Water-source comparisons and exceptions separated waterborne transmission from local bad-air proximity better than the map alone.", ["B01", "B09"]),
                "J6_falsifiability_growth": _criterion("PASS", "The account risked failure wherever water source and cholera incidence diverged under comparable conditions.", ["B01"]),
            },
            "verdict": "SURVIVING_ROUTE_LEVEL_J_JUMP",
            "unresolved": "The causal agent remained unspecified; route evidence was not yet germ isolation.",
        },
        {
            "transition_id": "T2_INTERVENTION",
            "from_nodes": ["N1"],
            "to_node": "N3",
            "claimed_component": "puerperal-fever contact pathway and chlorine-hand-disinfection intervention",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "The account localized a transferable harmful material on attendants and instruments rather than a shared ward atmosphere alone.", ["B03", "B10"]),
                "J2_retention_accounting": _criterion("PASS_EMPIRICAL_CAPABILITY_RECOVERY", "Cleaning remained practically valuable, but success was reassigned from odor removal to material-transfer interruption.", ["B03"]),
                "J3_new_reach": _criterion("PASS", "It connected ward differences, autopsy exposure, individual cases, and prevention through one manipulable pathway.", ["B03", "B10"]),
                "J4_complexity_dimensions": _criterion("PARTIAL", "The intervention rule was simple; the full etiology, disease identity, and alternative causes were not.", ["B10", "B11"]),
                "J5_rival_discrimination": _criterion("PASS_FOR_INTERVENTION_PARTIAL_FOR_FULL_ETIOLOGY", "Mortality changes under disinfection and comparative tables supported a contact contribution, but did not eliminate every rival cause or establish a modern germ ontology.", ["B10", "B11"]),
                "J6_falsifiability_growth": _criterion("PASS", "The account predicted mortality changes with material transfer and disinfection and could fail across clinics, periods, and non-cadaveric cases.", ["B03", "B10"]),
            },
            "verdict": "SURVIVING_INTERVENTION_AND_CONTACT_J_JUMP_FULL_ETIOLOGY_NOT_PROMOTED",
            "unresolved": "The exact agent, multiplicity of causes, and generality beyond the studied setting remained contested.",
        },
        {
            "transition_id": "T3_ONTOLOGY_METHOD",
            "from_nodes": ["N1", "N2", "N3"],
            "to_node": "N4",
            "claimed_component": "microbial ontology and controlled laboratory method",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "Living microorganisms and contamination pathways became manipulable experimental entities rather than unspecified poisons or emanations.", ["B04", "B05"]),
                "J2_retention_accounting": _criterion("PASS_DISTRIBUTED", "Contagion, contamination, fermentation, and sanitation successes received a common microbial interpretation without preserving all predecessor etiologies.", ["B04", "B05"]),
                "J3_new_reach": _criterion("PASS", "Controlled exposure, sterilization, and organism-specific fermentation generated new questions and laboratory interventions.", ["B04", "B05"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "A common living-agent ontology compressed several phenomena while demanding new laboratory controls and techniques.", ["B04"]),
                "J5_rival_discrimination": _criterion("PASS_FOR_SPONTANEOUS_GENERATION_PARTIAL_FOR_DISEASE", "Contamination-controlled vessels discriminated spontaneous generation claims, but did not alone distinguish microbes causing particular diseases.", ["B04"]),
                "J6_falsifiability_growth": _criterion("PASS", "The program exposed claims to controlled-air, contamination, sterilization, and organism-process tests.", ["B04", "B05"]),
            },
            "verdict": "SURVIVING_ONTOLOGICAL_AND_METHOD_J_JUMP",
            "unresolved": "Human disease-specific etiology required further evidence.",
        },
        {
            "transition_id": "T4_SPECIFIC_ETIOLOGY",
            "from_nodes": ["N2", "N3", "N4"],
            "to_node": "N5",
            "claimed_component": "specific microbe-specific disease causal linkage",
            "criteria": {
                "J1_representation_change": _criterion("PASS", "The broad possibility of living agents became a disease-specific agent, life cycle, pathology, and transmission claim.", ["B06", "B07"]),
                "J2_retention_accounting": _criterion("PASS_CONVERGENT", "Earlier route and intervention successes were connected to agent behavior while failed generic etiologies were discarded.", ["B06", "B07", "B08"]),
                "J3_new_reach": _criterion("PASS", "The method enabled disease-specific detection, cultivation, experimental reproduction, prevention questions, and differentiation among infections.", ["B06", "B07"]),
                "J4_complexity_dimensions": _criterion("PASS_WITH_TRADEOFF", "Specific etiologies reduced causal ambiguity but increased experimental, technical, and disease-by-disease work.", ["B06", "B07"]),
                "J5_rival_discrimination": _criterion("PASS", "Repeated detection, isolation/culture, inoculation, pathology, and re-identification supplied converging discriminators beyond association alone.", ["B06", "B07"]),
                "J6_falsifiability_growth": _criterion("PASS", "A candidate agent could fail presence, isolation, transmission, pathology, or re-identification tests.", ["B06", "B07"]),
            },
            "verdict": "SURVIVING_DISTRIBUTED_DISEASE_SPECIFIC_CAUSAL_J_JUMP",
            "unresolved": "The method's domain did not include every pathogen, carrier state, host response, or polymicrobial process.",
        },
    ]


def controls() -> list[dict[str, str]]:
    return [
        {"control_id": "C1", "false_claim": "Snow ended the Broad Street epidemic by removing the pump handle.", "verdict": "REJECT_HEROIC_INTERVENTION_MYTH", "reason": "The outbreak was already waning; Snow's stronger contribution was the wider comparative route evidence."},
        {"control_id": "C2", "false_claim": "Snow discovered the cholera germ.", "verdict": "REJECT_LEVEL_CONFUSION", "reason": "He argued for a mode of communication without isolating or identifying the organism."},
        {"control_id": "C3", "false_claim": "Hand disinfection worked, therefore Semmelweis's complete etiology was correct.", "verdict": "REJECT_INTERVENTION_TO_MECHANISM_LEAP", "reason": "An action effect supports a pathway contribution but underdetermines the complete mechanism and cause set."},
        {"control_id": "C4", "false_claim": "Sanitation sometimes worked, therefore miasma was approximately the pathogen.", "verdict": "REJECT_ACTION_CAUSE_EQUIVOCATION", "reason": "An intervention can block a real water/contact/vector route for reasons different from the theory that motivated it."},
        {"control_id": "C5", "false_claim": "Pasteur single-handedly discovered germ theory of human disease.", "verdict": "REJECT_SINGLE_HERO_AND_SCOPE_INFLATION", "reason": "His ontology and experimental controls were crucial nodes, not the entire route-, clinical-, and disease-specific evidential network."},
        {"control_id": "C6", "false_claim": "Finding a microorganism in diseased tissue proves it caused the disease.", "verdict": "REJECT_ASSOCIATION_AS_CAUSATION", "reason": "Specific etiology needs converging evidence about presence, isolation or characterization, transmission/production, pathology, and alternatives."},
        {"control_id": "C7", "false_claim": "Koch's postulates are a universal timeless checklist that every genuine pathogen must satisfy.", "verdict": "REJECT_DOMAIN_FREE_POSTULATE_MYTH", "reason": "Carriers, viruses, unculturable agents, host variation, ethics, and polymicrobial disease require type-specific adaptations."},
        {"control_id": "C8", "false_claim": "One germ produces one inevitable disease outcome independently of host and environment.", "verdict": "REJECT_MICROBIAL_MONOCAUSALITY", "reason": "Pathogenicity is often a process involving organism, virulence, dose, host susceptibility/immunity, and environment."},
    ]


def amendment_tests() -> list[dict[str, str]]:
    return [
        {"amendment_id": "A1_RETENTION_ACCOUNTING", "status": "PASS_AND_ESSENTIAL", "finding": "Sanitation success can be recovered and re-explained without retaining foul air as the agent."},
        {"amendment_id": "A2_COMPONENT_SCOPING", "status": "PASS_AND_ESSENTIAL", "finding": "Snow's route, Semmelweis's intervention, Pasteur's ontology, and Koch's agent-disease method need separate verdicts."},
        {"amendment_id": "A3_COMPRESSION_DIMENSIONS", "status": "PASS", "finding": "Microbial specificity reduced causal ambiguity while increasing laboratory and disease-by-disease complexity."},
        {"amendment_id": "A4_APPROXIMATION_BOUNDARY", "status": "PASS_BUT_REQUIRES_DOMAIN_EXTENSION", "finding": "Koch-style evidence is powerful within a domain but not universal across carriers, viruses, host variation, or polymicrobial disease."},
        {"amendment_id": "A5_UNDERDETERMINATION", "status": "PASS_AND_ESSENTIAL", "finding": "Effective route/intervention evidence often preceded and underdetermined the agent and complete mechanism."},
    ]


def extensions() -> dict[str, Any]:
    return {
        "extension_name": "Historical Calibration Extension 2",
        "trigger": "The case is a distributed network of complementary component jumps; no single arrow or successful intervention carries the whole explanatory transition.",
        "prior_amendment_status": amendment_tests(),
        "extensions": [
            {
                "extension_id": "A6_DISTRIBUTED_LINEAGE_GRAPH",
                "new_rule": "Represent a proposed J-jump as a lineage graph when route, intervention, ontology, method, and mechanism arise in different agents or periods. Credit only the component and evidence actually supplied by each node.",
                "guardrail": "Do not collapse a distributed discovery into a single-hero narrative or transfer later evidence backward to an earlier node.",
                "sources": ["B01", "B03", "B04", "B06", "B12"],
            },
            {
                "extension_id": "A7_INTERVENTION_MECHANISM_DECOUPLING",
                "new_rule": "Record separately: intervention effectiveness, transmission route, causal agent, production mechanism, and full etiology. Success at one level raises but does not automatically satisfy another level's warrant.",
                "guardrail": "An effective action is not by itself proof of the action's proposed mechanism or of a complete cause set.",
                "sources": ["B01", "B03", "B09", "B10", "B11"],
            },
            {
                "extension_id": "A8_EVIDENCE_TRIANGULATION_LADDER",
                "new_rule": "For causal J-jumps, map which independent evidence modes support the claim: comparative pattern, intervention, localization, visualization, isolation/characterization, reproduction, re-identification, dose/host response, and alternative elimination.",
                "guardrail": "No fixed rung is universal, but an association-only or rhetoric-only candidate cannot be promoted.",
                "sources": ["B06", "B07", "B10", "B13", "B14"],
            },
            {
                "extension_id": "A9_RELATIONAL_CAUSAL_SCOPE",
                "new_rule": "State whether the causal claim concerns a necessary agent, sufficient agent, contributing cause, route, virulence factor, susceptible host, or environment. Do not use a generic cause label across these roles.",
                "guardrail": "A microbe's presence and a disease outcome must not be modeled as one inevitable one-to-one relation.",
                "sources": ["B13", "B14"],
            },
            {
                "extension_id": "A10_DISCOVERY_UPTAKE_OUTCOME_SEPARATION",
                "new_rule": "Track conceptual discovery, evidential warrant, community uptake, implementation, and health outcome as separate timelines.",
                "guardrail": "Later acceptance or beneficial policy cannot be back-projected as evidence available to the original proposal, and rejection alone does not prove a proposal was ahead of its time.",
                "sources": ["B09", "B11", "B12"],
            },
        ],
        "revised_j_jump_object": "A component-scoped node or linked subgraph with declared lineage, evidence available at the time, retention accounting, causal level, approximation/domain boundary, rivals, and new failure conditions.",
    }


def report(protocol_hash: str, study2_hash: str, amendment_hash: str) -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 3: Historical J-Jump Casebook 2",
        "case": "Miasma, sanitation, transmission, and germ theories",
        "method": {
            "protocol_sha256": protocol_hash,
            "study_2_report_sha256": study2_hash,
            "study_2_amendment_sha256": amendment_hash,
            "mode": "primary-source-led distributed historical stress test",
            "llm_or_api_calls": False,
            "dataset_calls": False,
            "medical_advice": False,
            "source_count": len(SOURCES),
            "qualification": "This is a historical-philosophical calibration, not medical guidance or proof that one timeless germ theory replaced one timeless miasma theory.",
        },
        "sources": SOURCES,
        "lineage_nodes": nodes(),
        "transition_edges": transitions(),
        "false_jump_controls": controls(),
        "study_2_amendment_tests": amendment_tests(),
        "contract_extension": extensions(),
        "results": {
            "study_2_amendments_generalized": True,
            "study_2_contract_sufficient_unchanged": False,
            "why_not_sufficient": "It handled retention, components, complexity, approximation, and underdetermination, but still modeled a jump too much like one proposal-to-proposal arrow and did not explicitly decouple intervention, route, agent, mechanism, uptake, and outcome.",
            "route_level_j_jump": "Snow's cholera communication account",
            "intervention_level_j_jump": "Semmelweis's contact and chlorine-disinfection component",
            "ontology_method_j_jump": "Pasteur's microbial and contamination-control program",
            "disease_specific_causal_j_jump": "Koch's convergent agent-disease program",
            "full_transition_verdict": "SURVIVING_DISTRIBUTED_J_JUMP_NETWORK_WITH_DOMAIN_LIMITS",
            "significant_findings": [
                "The miasma-to-germ transition is a network of component jumps, not one Einstein-style moment or one hero's theory.",
                "An effective intervention can precede correct ontology and mechanism; action success and explanatory success must be audited separately.",
                "Wrong theories can motivate beneficial actions when the action intersects the real causal route for a different reason.",
                "Specific microbial causation was a major gain, but microbial presence is not an inevitable disease outcome independently of host and environment.",
                "A credible AI J-jump may be a new synthesis across partially successful nodes rather than a wholly new sentence generated from nothing.",
            ],
        },
        "decision": "CASEBOOK_2_SUCCESS_CONTRACT_EXTENDED",
        "next_case": {
            "name": "Caloric fluid to kinetic theory of heat",
            "reason": "This tests whether the distributed and intervention-decoupled contract works when an empirically successful conserved-substance model is replaced by a statistical-mechanical representation with different ontology and scale.",
            "stop_condition": "If the contract requires domain-specific exceptions that cannot be expressed through the existing lineage, component, retention, causal-level, and evidence rules, pause historical expansion and reassess whether a general J-jump detector is possible.",
        },
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Theory Study 3 Protocol",
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
        "# Historical J-Jump Casebook 2: Miasma → Germ Theories",
        "",
        "## Outcome",
        "",
        f"Decision: **{value['decision']}**.",
        "",
        "This case did not reveal one clean arrow from a bad theory to a good theory. It revealed a **distributed J-jump network**.",
        "",
        "## The actual network",
        "",
        "```text",
        "Environmental sanitation ─┬─→ Snow: cholera transmission route",
        "                           ├─→ Semmelweis: contact intervention",
        "Contagion/fermentation ────┴─→ Pasteur: microbial ontology + controls",
        "Snow + Semmelweis + Pasteur ─→ Koch: disease-specific causal method",
        "Kochian specificity ─────────→ host–pathogen–environment process view",
        "```",
        "",
        "## Node verdicts",
        "",
        "| Node | Surviving component | Failed or limited component | Verdict |",
        "|---|---|---|---|",
    ]
    for item in value["lineage_nodes"]:
        lines.append(f"| {item['name']} | {item['surviving_value']} | {item['failed_or_limited_claim']} | `{item['verdict']}` |")
    lines.extend(["", "## Transition tests", ""])
    for edge in value["transition_edges"]:
        lines.extend([
            f"### {edge['transition_id']} — {edge['claimed_component']}",
            "",
            "| Criterion | Status | Reason |",
            "|---|---|---|",
        ])
        for criterion, result in edge["criteria"].items():
            lines.append(f"| {criterion} | `{result['status']}` | {result['reason']} |")
        lines.extend(["", f"Verdict: **{edge['verdict']}**", "", f"Unresolved: {edge['unresolved']}", ""])
    lines.extend(["## False-jump controls", ""])
    for item in value["false_jump_controls"]:
        lines.append(f"- **{item['control_id']}: {item['false_claim']}** `{item['verdict']}` — {item['reason']}")
    lines.extend(["", "## Did the first historical amendment generalize?", ""])
    for item in value["study_2_amendment_tests"]:
        lines.append(f"- **{item['amendment_id']}: `{item['status']}`** — {item['finding']}")
    lines.extend(["", "All five rules generalized, but they were not sufficient unchanged.", "", "## New contract extensions", ""])
    for item in value["contract_extension"]["extensions"]:
        lines.extend([
            f"### {item['extension_id']}",
            "",
            f"**Rule:** {item['new_rule']}",
            "",
            f"Guardrail: {item['guardrail']}",
            "",
        ])
    lines.extend([
        "## What this changes for AI and Meno-J",
        "",
        "A scientific J-jump should no longer be imagined only as one extraordinary mind producing one complete theory. The historical unit can be a linked subgraph: one node discovers a route, another finds a working intervention, another supplies an ontology, and another establishes a disease-specific mechanism.",
        "",
        "For AI, this means multi-vision thinking should generate **different representation components and causal levels**, then search for a new synthesis that preserves each component's actual success without inheriting its unsupported story.",
        "",
        f"**Revised J-jump object:** {value['contract_extension']['revised_j_jump_object']}",
        "",
        "## Significant findings",
        "",
    ])
    lines.extend(f"- {item}" for item in value["results"]["significant_findings"])
    lines.extend([
        "",
        "## Scope warning",
        "",
        "This report is historical and philosophical. It is not medical advice and does not use the historical cases to recommend present-day disease treatment or public-health action.",
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
        lines.append(f"- **{source['source_id']} — [{source['title']}]({source['url']})** ({source['authors']}, {source['year']}). `{source['access_depth']}`. {' '.join(source['supports'])}")
    lines.append("")
    return "\n".join(lines)


def render_extension_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J J-Jump Contract: Historical Calibration Extension 2",
        "",
        f"**Trigger:** {value['trigger']}",
        "",
        "## Prior amendment stress result",
        "",
    ]
    for item in value["prior_amendment_status"]:
        lines.append(f"- **{item['amendment_id']}: `{item['status']}`** — {item['finding']}")
    lines.append("")
    for item in value["extensions"]:
        lines.extend([
            f"## {item['extension_id']}",
            "",
            f"New rule: **{item['new_rule']}**",
            "",
            f"Guardrail: {item['guardrail']}",
            "",
        ])
    lines.extend(["## Revised J-jump object", "", value["revised_j_jump_object"], ""])
    return "\n".join(lines)


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    for path in (STUDY2_REPORT, STUDY2_AMENDMENT, STUDY2_VALIDATION):
        if not path.is_file():
            raise FileNotFoundError(f"Missing validated Study 2 prerequisite: {path}")
    if _read_json(STUDY2_VALIDATION).get("status") != "PASS":
        raise ValueError("Theory Study 2 validation must be PASS.")

    frozen = protocol()
    _atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")
    result = report(_sha256(PROTOCOL_JSON), _sha256(STUDY2_REPORT), _sha256(STUDY2_AMENDMENT))
    _atomic_json(REPORT_JSON, result)
    REPORT_MD.write_text(render_report_md(result), encoding="utf-8")
    _atomic_json(AMENDMENT_JSON, result["contract_extension"])
    AMENDMENT_MD.write_text(render_extension_md(result["contract_extension"]), encoding="utf-8")

    reproducibility = {
        "study_name": result["study_name"],
        "status": "BUILT_PENDING_INDEPENDENT_VALIDATION",
        "execution_date": date.today().isoformat(),
        "input_hashes": {
            "protocol": _sha256(PROTOCOL_JSON),
            "study_2_report": _sha256(STUDY2_REPORT),
            "study_2_amendment": _sha256(STUDY2_AMENDMENT),
            "study_2_validation": _sha256(STUDY2_VALIDATION),
        },
        "output_hashes": {
            "report_json": _sha256(REPORT_JSON),
            "report_markdown": _sha256(REPORT_MD),
            "extension_json": _sha256(AMENDMENT_JSON),
            "extension_markdown": _sha256(AMENDMENT_MD),
        },
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False},
        "encoding": "UTF-8",
        "source_access_limits_recorded": True,
    }
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 3 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset or patient-data calls: **none**\n"
        "- Medical advice: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n"
        f"- Study 2 report SHA-256: `{reproducibility['input_hashes']['study_2_report']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n",
        encoding="utf-8",
    )
    print(f"Built {REPORT_JSON.name} and contract extension")


if __name__ == "__main__":
    main()
