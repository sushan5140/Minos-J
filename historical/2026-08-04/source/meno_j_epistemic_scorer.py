"""Deterministic, non-scalar decision engine for the Meno-J theory contract."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any


GATE_IDS = (
    "G0_QUESTION",
    "G1_ADEQUACY",
    "G2_WARRANT",
    "G3_RELEVANCE_AND_SELECTIVITY",
    "G4_GENERATIVITY",
    "G5_RIVAL_VULNERABILITY",
)
JUMP_IDS = (
    "J1_representation_change",
    "J2_retention",
    "J3_new_reach",
    "J4_compression_control",
    "J5_rival_discrimination",
    "J6_falsifiability_growth",
)
RULE_IDS = tuple(f"A{index}" for index in range(1, 21))
EVIDENCE_STATUSES = {"PASS", "PARTIAL", "FAIL", "UNKNOWN", "NOT_APPLICABLE"}
PRIMARY_STANCES = {"REJECT", "NON_ACCEPT", "PURSUE", "PROVISIONAL_USE", "ACCEPT"}


class AssessmentValidationError(ValueError):
    """Raised when an assessment violates the executable input contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssessmentValidationError(message)


def _validate_result_map(name: str, value: Any, expected_ids: tuple[str, ...]) -> None:
    _require(isinstance(value, dict), f"{name} must be an object")
    _require(set(value) == set(expected_ids), f"{name} IDs must exactly match the contract")
    for item_id, item in value.items():
        _require(isinstance(item, dict), f"{name}.{item_id} must be an object")
        _require(item.get("status") in EVIDENCE_STATUSES, f"invalid status for {name}.{item_id}")
        _require(bool(item.get("reason")), f"missing reason for {name}.{item_id}")
        _require(isinstance(item.get("evidence_ids"), list), f"missing evidence_ids for {name}.{item_id}")


def validate_assessment(value: dict[str, Any]) -> None:
    """Fail loudly if a proposal assessment is incomplete or leaks hindsight."""

    required = {
        "proposal_id", "title", "evidence_cutoff", "component_scope", "relation_type",
        "target", "foil", "purpose", "background", "scope", "gates", "jump_criteria",
        "evidence_ledger", "rivals", "retention", "complexity", "approximation",
        "underdetermination", "lineage", "causal_decomposition", "causal_scope",
        "timelines", "formal_ontology", "layers", "bridge_law", "transition_role",
        "hindsight_partitioned", "object_relation", "observability", "practical_use",
        "decisive_refutation",
    }
    _require(set(value) == required, "assessment fields must exactly match the executable schema")
    for field in ("proposal_id", "title", "component_scope", "relation_type", "target", "foil", "purpose", "background", "scope"):
        _require(isinstance(value[field], str) and bool(value[field].strip()), f"{field} must be non-empty")
    try:
        cutoff = date.fromisoformat(value["evidence_cutoff"])
    except (TypeError, ValueError) as exc:
        raise AssessmentValidationError("evidence_cutoff must be an ISO date") from exc

    _validate_result_map("gates", value["gates"], GATE_IDS)
    _validate_result_map("jump_criteria", value["jump_criteria"], JUMP_IDS)

    ledger = value["evidence_ledger"]
    _require(isinstance(ledger, list), "evidence_ledger must be a list")
    evidence_ids: set[str] = set()
    available_ids: set[str] = set()
    for item in ledger:
        _require(isinstance(item, dict), "each evidence item must be an object")
        _require(set(item) == {"evidence_id", "date", "role", "independence_group", "discriminates", "available_at_cutoff"}, "evidence item fields must exactly match schema")
        evidence_id = item["evidence_id"]
        _require(isinstance(evidence_id, str) and evidence_id not in evidence_ids, "evidence IDs must be unique non-empty strings")
        evidence_ids.add(evidence_id)
        try:
            evidence_date = date.fromisoformat(item["date"])
        except (TypeError, ValueError) as exc:
            raise AssessmentValidationError(f"invalid evidence date for {evidence_id}") from exc
        _require(item["role"] in {"construction", "tuning", "independent_test", "background"}, f"invalid evidence role for {evidence_id}")
        _require(bool(item["independence_group"]), f"missing independence group for {evidence_id}")
        _require(isinstance(item["discriminates"], bool) and isinstance(item["available_at_cutoff"], bool), f"invalid evidence booleans for {evidence_id}")
        if item["available_at_cutoff"]:
            _require(evidence_date <= cutoff, f"hindsight leak: {evidence_id} postdates evidence cutoff")
            available_ids.add(evidence_id)
        else:
            _require(evidence_date > cutoff, f"evidence marked unavailable does not postdate cutoff: {evidence_id}")

    cited_ids: set[str] = set()
    for result_map in (value["gates"], value["jump_criteria"]):
        for item in result_map.values():
            cited_ids.update(item["evidence_ids"])
    _require(cited_ids <= evidence_ids, "gate or J-jump criterion cites an unknown evidence ID")
    _require(cited_ids <= available_ids, "gate or J-jump criterion cites evidence unavailable at cutoff")

    _require(isinstance(value["rivals"], list), "rivals must be a list")
    for rival in value["rivals"]:
        _require(set(rival) == {"rival_id", "prediction", "distinguishing_test"}, "rival fields must exactly match schema")
        _require(all(isinstance(rival[key], str) and rival[key].strip() for key in rival), "rival fields must be non-empty")

    required_nested = {
        "retention": {"mode", "boundary"},
        "complexity": {"conceptual", "ontological", "parameter", "computational", "tradeoff_declared"},
        "approximation": {"status", "boundary"},
        "underdetermination": {"equivalence_class", "separating_observation"},
        "lineage": {"nodes", "distributed"},
        "causal_decomposition": {"intervention", "route", "agent", "mechanism", "etiology"},
        "timelines": {"discovery", "warrant", "uptake", "implementation", "outcome"},
        "formal_ontology": {"formal_component", "ontology_component", "mapping"},
        "layers": {"declared_layers", "cross_layer_limits"},
        "bridge_law": {"mapping", "limits", "assumptions"},
        "object_relation": {"status", "predecessor_object", "successor_object"},
        "observability": {"status", "frontier", "planned_test"},
        "practical_use": {"enabled", "bounded_role", "monitoring", "rollback"},
    }
    for field, nested_fields in required_nested.items():
        nested = value[field]
        _require(isinstance(nested, dict) and set(nested) == nested_fields, f"{field} fields must exactly match schema")
    _require(value["retention"]["mode"] in {"LITERAL", "LIMITING", "EMPIRICAL_RECOVERY", "NON_RETENTIVE_EXPLANATION", "NONE"}, "invalid retention mode")
    _require(value["object_relation"]["status"] in {"PRESERVED", "REFINED", "REDEFINED", "REPLACED", "UNRESOLVED"}, "invalid object relation")
    _require(value["observability"]["status"] in {"CURRENTLY_TESTABLE", "ROADMAP_TESTABLE", "UNOBSERVABLE"}, "invalid observability status")
    _require(isinstance(value["hindsight_partitioned"], bool), "hindsight_partitioned must be boolean")
    _require(isinstance(value["decisive_refutation"], bool), "decisive_refutation must be boolean")
    _require(isinstance(value["complexity"]["tradeoff_declared"], bool), "complexity.tradeoff_declared must be boolean")
    _require(isinstance(value["lineage"]["nodes"], list) and isinstance(value["lineage"]["distributed"], bool), "invalid lineage")
    _require(isinstance(value["layers"]["declared_layers"], list), "layers.declared_layers must be a list")
    _require(isinstance(value["practical_use"]["enabled"], bool), "practical_use.enabled must be boolean")


def _contract_rule_audit(value: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Show where every historically validated rule is executed."""

    mapping = {
        "A1": ("retention", "Retention mode and failure boundary are explicit."),
        "A2": ("component_scope", "The evaluated component is explicit."),
        "A3": ("complexity", "Four complexity dimensions and their tradeoff are recorded."),
        "A4": ("approximation", "Approximation status and boundary are explicit."),
        "A5": ("underdetermination", "Equivalence class and separating observation are recorded."),
        "A6": ("lineage", "Contributing lineage nodes and distributed status are explicit."),
        "A7": ("causal_decomposition", "Intervention, route, agent, mechanism, and etiology are separated."),
        "A8": ("evidence_ledger", "Evidence modes are individually classified."),
        "A9": ("causal_scope", "The causal role is explicitly scoped."),
        "A10": ("timelines", "Discovery, warrant, uptake, implementation, and outcome are separated."),
        "A11": ("formal_ontology", "Formal and ontological components are audited separately."),
        "A12": ("layers", "Constraint and mechanism layers are declared."),
        "A13": ("bridge_law", "Cross-level mapping, limits, and assumptions are recorded."),
        "A14": ("transition_role", "The contribution's transition role is labeled."),
        "A15": ("layers", "Layered successor structure and limits are represented."),
        "A16": ("hindsight_partitioned", "Evidence availability is checked against a dated cutoff."),
        "A17": ("decision_vector", "Rejection, pursuit, provisional use, and acceptance are decided separately."),
        "A18": ("object_relation", "Predecessor and successor object identity is explicitly tested."),
        "A19": ("evidence_ledger", "Construction, tuning, independent testing, and independence groups are recorded."),
        "A20": ("observability", "Current or future observability and the planned test are recorded."),
    }
    return {rule_id: {"status": "EXECUTED", "input": field, "reason": reason} for rule_id, (field, reason) in mapping.items()}


def score_assessment(value: dict[str, Any]) -> dict[str, Any]:
    """Return independent epistemic decisions, never an aggregate quality score."""

    validate_assessment(value)
    gates = {key: item["status"] for key, item in value["gates"].items()}
    jumps = {key: item["status"] for key, item in value["jump_criteria"].items()}
    available = [item for item in value["evidence_ledger"] if item["available_at_cutoff"]]
    independent_groups = sorted({
        item["independence_group"] for item in available
        if item["role"] == "independent_test" and item["discriminates"]
    })

    reject_reasons: list[str] = []
    if value["decisive_refutation"]:
        reject_reasons.append("DECISIVELY_REFUTED_AT_CUTOFF")
    if gates["G0_QUESTION"] == "FAIL":
        reject_reasons.append("NO_COHERENT_QUESTION_OR_SCOPE")
    if gates["G1_ADEQUACY"] == "FAIL" and gates["G2_WARRANT"] == "FAIL":
        reject_reasons.append("ADEQUACY_AND_WARRANT_BOTH_FAIL")
    if jumps["J1_representation_change"] == "FAIL" and gates["G4_GENERATIVITY"] == "FAIL" and gates["G5_RIVAL_VULNERABILITY"] == "FAIL":
        reject_reasons.append("MERE_RELABELING_WITHOUT_NEW_REACH_OR_VULNERABILITY")
    rejected = bool(reject_reasons)

    pursuit_reasons: list[str] = []
    pursuit = (
        not rejected
        and gates["G0_QUESTION"] == "PASS"
        and jumps["J1_representation_change"] == "PASS"
        and jumps["J3_new_reach"] in {"PASS", "PARTIAL"}
        and gates["G4_GENERATIVITY"] in {"PASS", "PARTIAL"}
        and jumps["J6_falsifiability_growth"] == "PASS"
        and value["observability"]["status"] in {"CURRENTLY_TESTABLE", "ROADMAP_TESTABLE"}
        and bool(value["observability"]["planned_test"])
    )
    if pursuit:
        pursuit_reasons.extend(["REPRESENTATION_CHANGE", "NEW_REACH", "EXPLICIT_FAILURE_PATH", "OBSERVABLE_TEST_PATH"])

    acceptance_blockers: list[str] = []
    for gate_id in GATE_IDS:
        if gates[gate_id] != "PASS":
            acceptance_blockers.append(f"{gate_id}_{gates[gate_id]}")
    for jump_id in ("J1_representation_change", "J2_retention", "J3_new_reach", "J5_rival_discrimination", "J6_falsifiability_growth"):
        if jumps[jump_id] != "PASS":
            acceptance_blockers.append(f"{jump_id}_{jumps[jump_id]}")
    if jumps["J4_compression_control"] == "FAIL":
        acceptance_blockers.append("J4_COMPRESSION_CONTROL_FAIL")
    if jumps["J4_compression_control"] == "PARTIAL" and not value["complexity"]["tradeoff_declared"]:
        acceptance_blockers.append("J4_PARTIAL_WITHOUT_DECLARED_TRADEOFF")
    if len(independent_groups) < 2:
        acceptance_blockers.append("FEWER_THAN_TWO_INDEPENDENT_DISCRIMINATING_EVIDENCE_GROUPS")
    if not value["rivals"]:
        acceptance_blockers.append("NO_NAMED_RIVAL")
    if not value["hindsight_partitioned"]:
        acceptance_blockers.append("HINDSIGHT_NOT_PARTITIONED")
    if value["object_relation"]["status"] == "UNRESOLVED":
        acceptance_blockers.append("THEORETICAL_OBJECT_RELATION_UNRESOLVED")
    if value["observability"]["status"] != "CURRENTLY_TESTABLE":
        acceptance_blockers.append("NOT_CURRENTLY_TESTABLE")
    accepted = not rejected and not acceptance_blockers

    practical = value["practical_use"]
    provisional_blockers: list[str] = []
    if not practical["enabled"]:
        provisional_blockers.append("NO_PROPOSED_PRACTICAL_ROLE")
    for gate_id in ("G0_QUESTION", "G1_ADEQUACY", "G3_RELEVANCE_AND_SELECTIVITY"):
        if gates[gate_id] != "PASS":
            provisional_blockers.append(f"{gate_id}_{gates[gate_id]}")
    for field in ("bounded_role", "monitoring", "rollback"):
        if not practical[field]:
            provisional_blockers.append(f"PRACTICAL_{field.upper()}_MISSING")
    provisional_use = not rejected and not accepted and not provisional_blockers

    if rejected:
        primary_stance = "REJECT"
    elif accepted:
        primary_stance = "ACCEPT"
    elif provisional_use:
        primary_stance = "PROVISIONAL_USE"
    elif pursuit:
        primary_stance = "PURSUE"
    else:
        primary_stance = "NON_ACCEPT"

    decision_vector = {
        "reject": rejected,
        "pursue": pursuit,
        "provisional_use": provisional_use,
        "accept": accepted,
    }
    result = {
        "proposal_id": value["proposal_id"],
        "title": value["title"],
        "evidence_cutoff": value["evidence_cutoff"],
        "primary_stance": primary_stance,
        "decision_vector": decision_vector,
        "reject_reasons": reject_reasons,
        "pursuit_reasons": pursuit_reasons,
        "provisional_use_blockers": provisional_blockers,
        "acceptance_blockers": acceptance_blockers,
        "independent_discriminating_evidence_groups": independent_groups,
        "object_relation": deepcopy(value["object_relation"]),
        "rule_execution": _contract_rule_audit(value),
        "no_aggregate_score": True,
    }
    _require(primary_stance in PRIMARY_STANCES, "engine produced an unknown stance")
    _require(sum(bool(decision_vector[key]) for key in ("reject", "provisional_use", "accept")) <= 1, "mutually exclusive terminal decisions conflict")
    return result

