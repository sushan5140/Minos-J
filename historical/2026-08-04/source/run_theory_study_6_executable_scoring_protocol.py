"""Build and exercise the executable twenty-rule Meno-J scoring protocol."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from meno_j_epistemic_scorer import (
    AssessmentValidationError,
    GATE_IDS,
    JUMP_IDS,
    RULE_IDS,
    score_assessment,
)


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
STUDY2 = OUTPUT_DIR / "meno_j_theory_study_2_contract_amendment.json"
STUDY3 = OUTPUT_DIR / "meno_j_theory_study_3_contract_extension.json"
STUDY4 = OUTPUT_DIR / "meno_j_theory_study_4_contract_extension.json"
STUDY5 = OUTPUT_DIR / "meno_j_theory_study_5_contract_extension.json"
STUDY5_VALIDATION = OUTPUT_DIR / "meno_j_theory_study_5_validation.json"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_6_executable_scoring_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_6_executable_scoring_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_6_executable_scoring_results.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_6_executable_scoring_results.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_6_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_6_reproducibility_summary.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _short_id(identifier: str) -> str:
    return identifier.split("_", 1)[0]


def normalized_contract() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source_groups = [
        (STUDY2, read_json(STUDY2)["amendments"], "amendment_id"),
        (STUDY3, read_json(STUDY3)["extensions"], "extension_id"),
        (STUDY4, read_json(STUDY4)["extensions"], "extension_id"),
        (STUDY5, read_json(STUDY5)["extensions"], "extension_id"),
    ]
    for artifact, items, id_field in source_groups:
        for item in items:
            records.append({
                "rule_id": _short_id(item[id_field]),
                "full_rule_id": item[id_field],
                "rule": item["new_rule"],
                "guardrail": item["guardrail"],
                "source_artifact": artifact.name,
            })
    if tuple(item["rule_id"] for item in records) != RULE_IDS:
        raise ValueError("Historical contract does not normalize to A1-A20 in order.")
    return records


def protocol() -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 6: Minimal Executable Epistemic Scoring Protocol",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_BEFORE_CALIBRATION_EXECUTION",
        "scope": "Deterministic theory-contract execution only; no LLM, OpenRouter, numerical dataset, or simulation.",
        "objective": "Test whether the twenty-rule historical contract can produce distinct, auditable reject, non-accept, pursue, provisional-use, and accept decisions without a compensatory scalar score.",
        "decision_semantics": {
            "REJECT": "The proposal is refuted, incoherent, or only relabels the problem without new reach or vulnerability.",
            "NON_ACCEPT": "The proposal is not accepted and presently lacks enough generativity or testability to justify prioritized pursuit; it is not claimed false.",
            "PURSUE": "The proposal changes the representation, reaches beyond the old account, and exposes a feasible failure path, but evidence is not yet sufficient for acceptance.",
            "PROVISIONAL_USE": "A bounded practical use is warranted with monitoring and rollback even though the explanatory or J-jump claim is not accepted.",
            "ACCEPT": "All explanation gates pass, the core J-jump obligations pass, rivals are named, and at least two independent evidence groups discriminate at the dated cutoff.",
        },
        "non_scalar_rule": "No aggregate score is computed. A preference or strength in one dimension cannot compensate for a failed critical gate.",
        "predeclared_calibration_cases": {
            "C1": "REJECT", "C2": "NON_ACCEPT", "C3": "PURSUE", "C4": "PROVISIONAL_USE", "C5": "ACCEPT",
        },
        "predeclared_mutation_tests": [
            "Post-cutoff evidence cited as contemporaneous must fail validation.",
            "Unknown evidence IDs must fail validation.",
            "Duplicate evidence IDs must fail validation.",
            "Missing required assessment fields must fail validation.",
            "Duplicating one evidence stream must not satisfy independent convergence.",
            "An unresolved predecessor/successor object relation must block acceptance.",
            "Bounded predictive usefulness must not imply explanatory acceptance.",
            "Mere relabeling must be rejected as a J-jump.",
        ],
        "success_conditions": {
            "all_five_stances_reachable": True,
            "all_predeclared_cases_match": True,
            "all_mutation_tests_pass": True,
            "all_twenty_rules_executed_per_valid_case": True,
            "hindsight_leaks_fail_loudly": True,
            "duplicate_evidence_not_counted_as_independent": True,
            "no_aggregate_score": True,
        },
    }


def _result(status: str, reason: str, evidence_ids: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "reason": reason, "evidence_ids": evidence_ids or []}


def _evidence(evidence_id: str, when: str, role: str, group: str, discriminates: bool, available: bool = True) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id, "date": when, "role": role,
        "independence_group": group, "discriminates": discriminates,
        "available_at_cutoff": available,
    }


def _base(proposal_id: str, title: str, cutoff: str) -> dict[str, Any]:
    gates = {gate: _result("UNKNOWN", "Not established in this fixture.") for gate in GATE_IDS}
    jumps = {criterion: _result("UNKNOWN", "Not established in this fixture.") for criterion in JUMP_IDS}
    return {
        "proposal_id": proposal_id,
        "title": title,
        "evidence_cutoff": cutoff,
        "component_scope": "representation",
        "relation_type": "mixed historical and explanatory",
        "target": "Explain the specified target phenomenon.",
        "foil": "The strongest named predecessor or rival.",
        "purpose": "Determine the warranted epistemic stance at the evidence cutoff.",
        "background": "Only evidence available at the cutoff is admissible.",
        "scope": "The declared component and historical period only.",
        "gates": gates,
        "jump_criteria": jumps,
        "evidence_ledger": [],
        "rivals": [],
        "retention": {"mode": "NONE", "boundary": "No retention claim established."},
        "complexity": {"conceptual": "declared", "ontological": "declared", "parameter": "declared", "computational": "declared", "tradeoff_declared": True},
        "approximation": {"status": "declared", "boundary": "Fixture-specific boundary declared."},
        "underdetermination": {"equivalence_class": "Declared rivals remain possible.", "separating_observation": "A fixture-specific discriminating observation is stated when available."},
        "lineage": {"nodes": ["proposal"], "distributed": False},
        "causal_decomposition": {"intervention": "not claimed", "route": "not claimed", "agent": "not claimed", "mechanism": "not claimed", "etiology": "not claimed"},
        "causal_scope": "No generic causal claim is imported beyond the declared component.",
        "timelines": {"discovery": cutoff, "warrant": cutoff, "uptake": "separate", "implementation": "separate", "outcome": "separate"},
        "formal_ontology": {"formal_component": "declared", "ontology_component": "declared", "mapping": "separately audited"},
        "layers": {"declared_layers": ["representation"], "cross_layer_limits": "No cross-layer inference without a bridge."},
        "bridge_law": {"mapping": "not applicable to this single-layer fixture", "limits": "declared", "assumptions": "declared"},
        "transition_role": "representation candidate",
        "hindsight_partitioned": True,
        "object_relation": {"status": "UNRESOLVED", "predecessor_object": "declared predecessor object", "successor_object": "declared proposal object"},
        "observability": {"status": "UNOBSERVABLE", "frontier": "No current discriminator.", "planned_test": ""},
        "practical_use": {"enabled": False, "bounded_role": "", "monitoring": "", "rollback": ""},
        "decisive_refutation": False,
    }


def calibration_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    relabel = _base("C1", "Decorative renaming of an existing account", "2020-01-01")
    relabel["evidence_ledger"] = [_evidence("C1E1", "2019-01-01", "construction", "same-description", False)]
    relabel["gates"].update({
        "G0_QUESTION": _result("PASS", "The target is stated.", ["C1E1"]),
        "G1_ADEQUACY": _result("PARTIAL", "The old observations are repeated.", ["C1E1"]),
        "G2_WARRANT": _result("FAIL", "No new relation is warranted.", ["C1E1"]),
        "G3_RELEVANCE_AND_SELECTIVITY": _result("PARTIAL", "The language tracks the target but adds no selection.", ["C1E1"]),
        "G4_GENERATIVITY": _result("FAIL", "No new consequence follows.", ["C1E1"]),
        "G5_RIVAL_VULNERABILITY": _result("FAIL", "No rival or new failure condition is supplied.", ["C1E1"]),
    })
    relabel["jump_criteria"].update({
        "J1_representation_change": _result("FAIL", "Only vocabulary changes.", ["C1E1"]),
        "J2_retention": _result("PASS", "The old description is copied.", ["C1E1"]),
        "J3_new_reach": _result("FAIL", "No anomaly or contrast is newly resolved.", ["C1E1"]),
        "J4_compression_control": _result("FAIL", "Renaming is not compression.", ["C1E1"]),
        "J5_rival_discrimination": _result("FAIL", "Predictions are unchanged.", ["C1E1"]),
        "J6_falsifiability_growth": _result("FAIL", "No new failure surface exists.", ["C1E1"]),
    })
    relabel["object_relation"]["status"] = "PRESERVED"
    cases.append(relabel)

    decorative = _base("C2", "Coherent but non-generative decorative mechanism", "2020-01-01")
    decorative["component_scope"] = "mechanism"
    decorative["evidence_ledger"] = [_evidence("C2E1", "2019-06-01", "construction", "anecdotal-pattern", False)]
    decorative["gates"].update({
        "G0_QUESTION": _result("PASS", "The target and scope are coherent.", ["C2E1"]),
        "G1_ADEQUACY": _result("PARTIAL", "The motivating observation is limited.", ["C2E1"]),
        "G2_WARRANT": _result("UNKNOWN", "The mechanism has not been independently probed.", ["C2E1"]),
        "G3_RELEVANCE_AND_SELECTIVITY": _result("PARTIAL", "Important alternatives remain uncontrolled.", ["C2E1"]),
        "G4_GENERATIVITY": _result("FAIL", "It yields no consequence beyond the motivating case.", ["C2E1"]),
        "G5_RIVAL_VULNERABILITY": _result("FAIL", "No distinguishing test is available.", ["C2E1"]),
    })
    decorative["jump_criteria"].update({
        "J1_representation_change": _result("PARTIAL", "A mechanism is named but the operative map is unchanged.", ["C2E1"]),
        "J2_retention": _result("UNKNOWN", "Prior success recovery is unspecified.", ["C2E1"]),
        "J3_new_reach": _result("FAIL", "No new contrast is answered.", ["C2E1"]),
        "J4_compression_control": _result("FAIL", "The account adds entities without controlled gain.", ["C2E1"]),
        "J5_rival_discrimination": _result("FAIL", "No discriminating consequence exists.", ["C2E1"]),
        "J6_falsifiability_growth": _result("FAIL", "No feasible failure test exists.", ["C2E1"]),
    })
    cases.append(decorative)

    wegener = _base("C3", "Wegener continental mobility assessed at 1924", "1924-12-31")
    wegener["evidence_ledger"] = [
        _evidence("C3E1", "1912-01-06", "construction", "geometric-fit", False),
        _evidence("C3E2", "1922-01-01", "construction", "cross-domain-correspondence", False),
        _evidence("C3E3", "1924-01-01", "independent_test", "geodetic-attempt", True),
        _evidence("C3E4", "1963-09-07", "independent_test", "marine-magnetism", True, False),
    ]
    wegener["rivals"] = [{"rival_id": "C3R1", "prediction": "Fixed continents plus vertical crustal change should reproduce the same correspondences without lateral displacement.", "distinguishing_test": "Measure relative continental motion or ocean-floor renewal independently."}]
    wegener["retention"] = {"mode": "EMPIRICAL_RECOVERY", "boundary": "Retains cross-ocean correspondences, not the proposed driving force or continents-plowing-through-substrate object."}
    wegener["gates"].update({
        "G0_QUESTION": _result("PASS", "Continental distribution and cross-domain correspondences are explicit.", ["C3E1", "C3E2"]),
        "G1_ADEQUACY": _result("PARTIAL", "Several correspondences are substantive, but some reconstructions and measurements remain uncertain.", ["C3E1", "C3E2"]),
        "G2_WARRANT": _result("PARTIAL", "Mobility has indirect support, while the proposed forces remain physically inadequate.", ["C3E2", "C3E3"]),
        "G3_RELEVANCE_AND_SELECTIVITY": _result("PASS", "Multiple relevant geological and paleoclimatic patterns are selected.", ["C3E1", "C3E2"]),
        "G4_GENERATIVITY": _result("PASS", "The representation organizes additional cross-continental tests.", ["C3E2"]),
        "G5_RIVAL_VULNERABILITY": _result("PASS", "A fixed-continent rival and future motion/renewal tests are explicit.", ["C3E3"]),
    })
    wegener["jump_criteria"].update({
        "J1_representation_change": _result("PASS", "Continents become horizontally mobile historical objects.", ["C3E1", "C3E2"]),
        "J2_retention": _result("PARTIAL", "Pattern successes are retained, but prior geophysical constraints are not yet recovered.", ["C3E2"]),
        "J3_new_reach": _result("PASS", "Separated geological and climatic patterns receive a common historical account.", ["C3E2"]),
        "J4_compression_control": _result("PARTIAL", "Conceptual unification comes with unresolved physical complexity.", ["C3E2"]),
        "J5_rival_discrimination": _result("PARTIAL", "Discriminators are proposed but not decisive at the cutoff.", ["C3E3"]),
        "J6_falsifiability_growth": _result("PASS", "Relative-motion and ocean-floor observations can fail the proposal.", ["C3E3"]),
    })
    wegener["lineage"] = {"nodes": ["Wegener synthesis", "geophysical critics"], "distributed": True}
    wegener["formal_ontology"] = {"formal_component": "continental reconstruction", "ontology_component": "continents moving through oceanic substrate", "mapping": "reconstruction can survive while substrate ontology fails"}
    wegener["layers"] = {"declared_layers": ["geometric reconstruction", "historical synthesis", "proposed force"], "cross_layer_limits": "Pattern agreement does not warrant the force."}
    wegener["bridge_law"] = {"mapping": "relative displacement to mapped geological correspondences", "limits": "no ocean-floor kinematic bridge at cutoff", "assumptions": "continental rigidity and correct feature matching"}
    wegener["transition_role"] = "synthesis precursor"
    wegener["object_relation"] = {"status": "REDEFINED", "predecessor_object": "fixed continents and ocean basins", "successor_object": "mobile continents; later redefined again as lithospheric plates"}
    wegener["observability"] = {"status": "ROADMAP_TESTABLE", "frontier": "Reliable ocean-floor mapping and global geophysics are not yet available.", "planned_test": "Independent relative-motion, ocean-age, magnetic, and seismic observations."}
    cases.append(wegener)

    lookup = _base("C4", "Bounded high-accuracy lookup predictor", "2020-01-01")
    lookup["component_scope"] = "practical prediction method"
    lookup["evidence_ledger"] = [
        _evidence("C4E1", "2019-01-01", "tuning", "development-set", False),
        _evidence("C4E2", "2019-10-01", "independent_test", "held-out-site", True),
    ]
    lookup["rivals"] = [{"rival_id": "C4R1", "prediction": "A simple baseline may perform equally well outside the lookup support.", "distinguishing_test": "Prospective monitored comparison on the bounded deployment population."}]
    lookup["retention"] = {"mode": "EMPIRICAL_RECOVERY", "boundary": "Recovers held-out predictive performance only inside the declared support."}
    lookup["gates"].update({
        "G0_QUESTION": _result("PASS", "The prediction task, population, and use are explicit.", ["C4E1"]),
        "G1_ADEQUACY": _result("PASS", "Held-out performance supports bounded predictive adequacy.", ["C4E2"]),
        "G2_WARRANT": _result("PARTIAL", "Predictive association is warranted; an explanatory relation is not.", ["C4E2"]),
        "G3_RELEVANCE_AND_SELECTIVITY": _result("PASS", "The inputs are relevant to the bounded prediction task.", ["C4E2"]),
        "G4_GENERATIVITY": _result("PASS", "It generates testable future predictions in scope.", ["C4E2"]),
        "G5_RIVAL_VULNERABILITY": _result("PASS", "Prospective baseline comparison and drift monitoring can expose failure.", ["C4E2"]),
    })
    lookup["jump_criteria"].update({
        "J1_representation_change": _result("PARTIAL", "The lookup changes prediction machinery but supplies no explanatory representation.", ["C4E1"]),
        "J2_retention": _result("PASS", "Held-out predictive capability is recovered in scope.", ["C4E2"]),
        "J3_new_reach": _result("PASS", "It predicts cases not present in the lookup construction set.", ["C4E2"]),
        "J4_compression_control": _result("FAIL", "The table may expand rather than compress.", ["C4E1"]),
        "J5_rival_discrimination": _result("PARTIAL", "One held-out comparison exists, not explanatory discrimination.", ["C4E2"]),
        "J6_falsifiability_growth": _result("PASS", "Prospective error and drift thresholds are concrete failure conditions.", ["C4E2"]),
    })
    lookup["object_relation"] = {"status": "PRESERVED", "predecessor_object": "prediction target", "successor_object": "same prediction target"}
    lookup["observability"] = {"status": "CURRENTLY_TESTABLE", "frontier": "Only the bounded deployment population is observed.", "planned_test": "Prospective monitored error and subgroup calibration."}
    lookup["practical_use"] = {"enabled": True, "bounded_role": "Low-stakes decision support inside the validated population.", "monitoring": "Continuously monitor error, coverage, and subgroup drift.", "rollback": "Revert to the established baseline when thresholds fail."}
    cases.append(lookup)

    plates = _base("C5", "Rigid plate tectonic synthesis assessed at 1968", "1968-12-31")
    plates["component_scope"] = "layered kinematic and causal architecture"
    plates["evidence_ledger"] = [
        _evidence("C5E1", "1963-09-07", "independent_test", "marine-magnetism", True),
        _evidence("C5E2", "1965-07-24", "independent_test", "transform-geometry", True),
        _evidence("C5E3", "1967-08-15", "independent_test", "deep-seismic-zones", True),
        _evidence("C5E4", "1967-12-30", "independent_test", "spherical-kinematics", True),
        _evidence("C5E5", "1962-01-01", "construction", "seafloor-spreading", False),
    ]
    plates["rivals"] = [{"rival_id": "C5R1", "prediction": "Fixed continents, Earth expansion, or vertical tectonics should not jointly predict symmetric stripes, transform slip, descending seismic zones, and spherical boundary velocities.", "distinguishing_test": "Test the joint geometry, polarity sequence, ages, earthquake depths, and relative-motion vectors."}]
    plates["retention"] = {"mode": "NON_RETENTIVE_EXPLANATION", "boundary": "Retains continental mobility and reconstruction successes while replacing continents-plowing-through-oceanic-substrate with plates containing both materials."}
    for gate_id in GATE_IDS:
        plates["gates"][gate_id] = _result("PASS", f"{gate_id} is supported by convergent dated evidence.", ["C5E1", "C5E2", "C5E3", "C5E4"])
    for jump_id in JUMP_IDS:
        status = "PARTIAL" if jump_id == "J4_compression_control" else "PASS"
        plates["jump_criteria"][jump_id] = _result(status, f"{jump_id} is satisfied by the layered plate architecture; complexity tradeoffs remain explicit.", ["C5E1", "C5E2", "C5E3", "C5E4", "C5E5"])
    plates["lineage"] = {"nodes": ["continental mobility", "mantle circulation", "seafloor spreading", "magnetic reversal tests", "transform faults", "subduction seismology", "spherical plate kinematics"], "distributed": True}
    plates["causal_decomposition"] = {"intervention": "not directly available", "route": "plate-boundary transport", "agent": "lithospheric plates", "mechanism": "spreading, subduction, and relative rigid motion", "etiology": "mantle-driving details remain layered and partly open"}
    plates["causal_scope"] = "Relative plate motion and boundary response are accepted separately from a complete universal driving-force account."
    plates["formal_ontology"] = {"formal_component": "finite rotations and relative boundary vectors", "ontology_component": "rigid lithospheric plates", "mapping": "local motion measurements map to spherical plate rotations"}
    plates["layers"] = {"declared_layers": ["reconstruction", "kinematics", "boundary mechanics", "mantle dynamics"], "cross_layer_limits": "Kinematic success does not by itself close every mantle-driving mechanism."}
    plates["bridge_law"] = {"mapping": "Euler rotations map plate-scale motion to local boundary velocities", "limits": "diffuse boundaries and deformation violate ideal rigidity", "assumptions": "piecewise rigid plates on a sphere"}
    plates["transition_role"] = "distributed synthesis and kinematic architecture"
    plates["object_relation"] = {"status": "REDEFINED", "predecessor_object": "continents moving through fixed oceanic crust", "successor_object": "lithospheric plates containing continental and oceanic material"}
    plates["observability"] = {"status": "CURRENTLY_TESTABLE", "frontier": "Global oceanic and seismic observations are available, though unevenly sampled.", "planned_test": "Continue joint prediction of age, polarity, boundary motion, and earthquake structure."}
    cases.append(plates)
    return cases


def mutation_tests(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["proposal_id"]: item for item in cases}
    results: list[dict[str, Any]] = []

    def expect_validation_failure(test_id: str, description: str, mutated: dict[str, Any]) -> None:
        try:
            score_assessment(mutated)
        except AssessmentValidationError as exc:
            results.append({"test_id": test_id, "description": description, "status": "PASS", "observed": type(exc).__name__})
        else:
            results.append({"test_id": test_id, "description": description, "status": "FAIL", "observed": "validation unexpectedly succeeded"})

    leak = deepcopy(by_id["C3"])
    leak["evidence_ledger"][-1]["available_at_cutoff"] = True
    expect_validation_failure("M1", "Post-cutoff evidence cannot be marked contemporaneously available.", leak)

    unknown = deepcopy(by_id["C3"])
    unknown["gates"]["G1_ADEQUACY"]["evidence_ids"].append("UNKNOWN")
    expect_validation_failure("M2", "Unknown evidence references fail.", unknown)

    duplicate = deepcopy(by_id["C5"])
    duplicate["evidence_ledger"][1]["evidence_id"] = duplicate["evidence_ledger"][0]["evidence_id"]
    expect_validation_failure("M3", "Duplicate evidence IDs fail.", duplicate)

    missing = deepcopy(by_id["C5"])
    del missing["object_relation"]
    expect_validation_failure("M4", "Missing contract fields fail.", missing)

    copied_streams = deepcopy(by_id["C5"])
    for item in copied_streams["evidence_ledger"]:
        item["independence_group"] = "one-reprocessed-stream"
    copied_result = score_assessment(copied_streams)
    results.append({"test_id": "M5", "description": "Duplicated evidence streams cannot simulate independent convergence.", "status": "PASS" if copied_result["primary_stance"] != "ACCEPT" and "FEWER_THAN_TWO_INDEPENDENT_DISCRIMINATING_EVIDENCE_GROUPS" in copied_result["acceptance_blockers"] else "FAIL", "observed": copied_result["primary_stance"]})

    unresolved = deepcopy(by_id["C5"])
    unresolved["object_relation"]["status"] = "UNRESOLVED"
    unresolved_result = score_assessment(unresolved)
    results.append({"test_id": "M6", "description": "Unresolved object identity blocks acceptance.", "status": "PASS" if unresolved_result["primary_stance"] != "ACCEPT" and "THEORETICAL_OBJECT_RELATION_UNRESOLVED" in unresolved_result["acceptance_blockers"] else "FAIL", "observed": unresolved_result["primary_stance"]})

    lookup_result = score_assessment(by_id["C4"])
    results.append({"test_id": "M7", "description": "Predictive usefulness does not imply explanatory acceptance.", "status": "PASS" if lookup_result["primary_stance"] == "PROVISIONAL_USE" and not lookup_result["decision_vector"]["accept"] else "FAIL", "observed": lookup_result["primary_stance"]})

    relabel_result = score_assessment(by_id["C1"])
    results.append({"test_id": "M8", "description": "Mere relabeling is rejected as a J-jump.", "status": "PASS" if relabel_result["primary_stance"] == "REJECT" else "FAIL", "observed": relabel_result["primary_stance"]})
    return results


def build_report(protocol_hash: str) -> dict[str, Any]:
    cases = calibration_cases()
    decisions = [score_assessment(case) for case in cases]
    mutations = mutation_tests(cases)
    expected = protocol()["predeclared_calibration_cases"]
    comparison = [
        {"proposal_id": item["proposal_id"], "expected": expected[item["proposal_id"]], "observed": item["primary_stance"], "match": expected[item["proposal_id"]] == item["primary_stance"]}
        for item in decisions
    ]
    stance_counts = {stance: sum(item["primary_stance"] == stance for item in decisions) for stance in ("REJECT", "NON_ACCEPT", "PURSUE", "PROVISIONAL_USE", "ACCEPT")}
    return {
        "study_name": protocol()["study_name"],
        "method": {"protocol_sha256": protocol_hash, "mode": "deterministic non-scalar exact replay", "llm_or_api_calls": False, "dataset_or_simulation_calls": False},
        "normalized_twenty_rule_contract": normalized_contract(),
        "input_assessments": cases,
        "decisions": decisions,
        "calibration_comparison": comparison,
        "mutation_tests": mutations,
        "diagnostics": {
            "case_count": len(cases), "stance_counts": stance_counts,
            "all_five_stances_reached": set(stance_counts.values()) == {1},
            "all_expected_decisions_matched": all(item["match"] for item in comparison),
            "all_mutation_tests_passed": all(item["status"] == "PASS" for item in mutations),
            "all_twenty_rules_executed": all(set(item["rule_execution"]) == set(RULE_IDS) for item in decisions),
            "aggregate_score_emitted": False,
            "red_flags": [],
        },
        "significant_findings": [
            "The twenty-rule contract is executable without collapsing epistemic judgment into one compensatory score.",
            "The engine distinguishes rejection from non-acceptance: an unsupported but coherent idea is not automatically declared false.",
            "Wegener at the 1924 cutoff is classified PURSUE rather than ACCEPT; later marine evidence cannot leak backward through the hindsight firewall.",
            "A bounded high-accuracy lookup predictor can receive PROVISIONAL_USE while its explanatory J-jump claim remains unaccepted.",
            "The 1968 plate architecture reaches ACCEPT only through multiple independent discriminating evidence groups and an explicit object redefinition.",
            "Duplicated evidence, unresolved object identity, and post-cutoff evidence each prevent a false acceptance upgrade.",
        ],
        "decision": "EXECUTABLE_PROTOCOL_SUCCESS_ALL_FIVE_STANCES_AND_ADVERSARIAL_GUARDS_PASS",
        "next_stage": {
            "name": "Prospective blind theory benchmark",
            "purpose": "Give the frozen scorer unseen theory proposals with evidence packets and compare its decisions with blinded expert judgments and later outcomes.",
            "constraint": "Do not tune thresholds on the evaluation set and do not let hypothesis-generation quality define the score.",
        },
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = ["# Meno-J Theory Study 6 Protocol", "", f"**Objective:** {value['objective']}", "", f"**Status:** `{value['status']}`", "", "## Decision meanings", ""]
    lines.extend(f"- **{key}:** {text}" for key, text in value["decision_semantics"].items())
    lines.extend(["", "## Non-scalar rule", "", value["non_scalar_rule"], "", "## Predeclared calibration", ""])
    lines.extend(f"- {key}: `{stance}`" for key, stance in value["predeclared_calibration_cases"].items())
    lines.extend(["", "## Mutation tests", ""])
    lines.extend(f"- {item}" for item in value["predeclared_mutation_tests"])
    lines.append("")
    return "\n".join(lines)


def render_report_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Minimal Executable Epistemic Scoring Results", "", f"Decision: **{value['decision']}**", "",
        "The engine emits no overall quality score. It asks four independent questions—reject, pursue, permit bounded provisional use, and accept—then assigns a primary stance without allowing strength in one dimension to conceal a failed critical gate.", "",
        "## Calibration decisions", "", "| Case | Expected | Observed | Match | Independent discriminating groups |", "|---|---:|---:|---:|---:|",
    ]
    by_id = {item["proposal_id"]: item for item in value["decisions"]}
    for item in value["calibration_comparison"]:
        decision = by_id[item["proposal_id"]]
        lines.append(f"| {item['proposal_id']} — {decision['title']} | `{item['expected']}` | `{item['observed']}` | {item['match']} | {len(decision['independent_discriminating_evidence_groups'])} |")
    lines.extend(["", "## Why the two middle decisions matter", "", "- **PURSUE** means an idea earns further testing without being called true.", "- **PROVISIONAL_USE** means bounded practical utility can be authorized with monitoring and rollback without laundering that utility into explanatory acceptance.", "- **NON_ACCEPT** means insufficient support, not a declaration that the proposal is false.", "", "## Mutation tests", "", "| Test | Result | Observed |", "|---|---:|---|"])
    for item in value["mutation_tests"]:
        lines.append(f"| {item['test_id']} — {item['description']} | `{item['status']}` | {item['observed']} |")
    lines.extend(["", "## Twenty-rule execution", "", "All valid cases executed A1–A20. The rules remain audit operations, not points in a weighted score.", ""])
    for item in value["normalized_twenty_rule_contract"]:
        lines.append(f"- **{item['full_rule_id']}** — {item['rule']}")
    lines.extend(["", "## Significant findings", ""])
    lines.extend(f"- {item}" for item in value["significant_findings"])
    lines.extend(["", "## Next stage", "", f"**{value['next_stage']['name']}:** {value['next_stage']['purpose']}", "", f"Constraint: {value['next_stage']['constraint']}", ""])
    return "\n".join(lines)


def main() -> None:
    prerequisites = (STUDY2, STUDY3, STUDY4, STUDY5, STUDY5_VALIDATION)
    for path in prerequisites:
        if not path.is_file():
            raise FileNotFoundError(f"Missing validated contract prerequisite: {path}")
        path.read_text(encoding="utf-8")
    if read_json(STUDY5_VALIDATION).get("status") != "PASS":
        raise ValueError("Theory Study 5 validation must be PASS.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = protocol()
    atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")
    report = build_report(sha256(PROTOCOL_JSON))
    if not report["diagnostics"]["all_expected_decisions_matched"] or not report["diagnostics"]["all_mutation_tests_passed"]:
        raise RuntimeError("Executable scoring calibration failed; invalid report was not checkpointed.")
    atomic_json(REPORT_JSON, report)
    REPORT_MD.write_text(render_report_md(report), encoding="utf-8")
    reproducibility = {
        "study_name": report["study_name"], "status": "BUILT_PENDING_INDEPENDENT_VALIDATION", "execution_date": date.today().isoformat(),
        "input_hashes": {path.name: sha256(path) for path in prerequisites} | {PROTOCOL_JSON.name: sha256(PROTOCOL_JSON)},
        "output_hashes": {REPORT_JSON.name: sha256(REPORT_JSON), REPORT_MD.name: sha256(REPORT_MD)},
        "runner": str(Path(__file__).resolve()), "runner_sha256": sha256(Path(__file__).resolve()),
        "scorer": str((PROJECT_DIR / "meno_j_epistemic_scorer.py").resolve()), "scorer_sha256": sha256(PROJECT_DIR / "meno_j_epistemic_scorer.py"),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False, "simulation": False}, "encoding": "UTF-8",
    }
    atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 6 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n- OpenRouter/LLM calls: **none**\n- Dataset/simulation calls: **none**\n- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes'][PROTOCOL_JSON.name]}`\n- Report SHA-256: `{reproducibility['output_hashes'][REPORT_JSON.name]}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n- Scorer SHA-256: `{reproducibility['scorer_sha256']}`\n",
        encoding="utf-8",
    )
    print("Built Meno-J Theory Study 6 executable scoring protocol and results")


if __name__ == "__main__":
    main()
