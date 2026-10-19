"""Compatibility prompt adapters for the Meno-J Falsification Engine."""

from __future__ import annotations

import json
from typing import Any

from schema import AUDIT_BOOLEAN_FIELDS, CRITICAL_AUDIT_FIELDS


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def dreamer_prompt(research_question: str) -> str:
    """Build speculative candidate input; this adapter is not the engine's core."""
    schema = {
        "hypotheses": [
            {
                "hypothesis_id": "H1",
                "hypothesis": "",
                "proposed_mechanism": "",
                "core_assumption": "",
                "knowledge_gap_addressed": "",
                "status": "SPECULATIVE",
            }
        ]
    }
    return f"""Stage 4 — J-Synthesis / Dreamer

Research question: {research_question}

Generate exactly 10 genuinely diverse speculative hypotheses, ordered and identified H1 through H10.
Cover distinct subject-specific, sensor, physiological, temporal, labeling, stratification, and statistical
possibilities where scientifically defensible. Do not optimize for all hypotheses passing a later audit.
Diversity matters more than safety. Each hypothesis must name a proposed causal mechanism, its core
assumption, and the specific knowledge gap it addresses. Label every status SPECULATIVE.

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def confounder_enrichment_prompt(
    research_question: str,
    hypotheses: list[dict[str, Any]],
) -> str:
    schema = {
        "enriched_hypotheses": [
            {
                "hypothesis_id": "H1",
                "original_hypothesis": "",
                "original_mechanism": "",
                "possible_confounders": [],
                "control_variables": [],
                "rival_explanations": [],
                "minimum_data_needed": [],
                "effect_size_expectation": "small | medium | large | unknown",
                "enriched_mechanism": "",
                "enrichment_notes": "",
            }
        ]
    }
    return f"""Stage 4.5 — Confounder Enrichment Agent

Research question: {research_question}

You are not judging the hypotheses yet. You are strengthening them before audit.

For each hypothesis, add:
1. realistic confounders,
2. control variables,
3. boring rival explanations,
4. minimum data needed to test it,
5. whether the expected effect would likely be exactly small, medium, large, or unknown,
6. a revised enriched mechanism that includes the confounder-control logic.

Do not mark anything PASS, REJECT, or SALVAGEABLE. Do not remove, merge, replace, or reorder hypotheses.
Keep all 10 hypotheses. Copy original_hypothesis and original_mechanism verbatim from the input. Each list
field must contain at least one concrete item.

Stage 4 hypotheses:
{_json(hypotheses)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def mechanism_builder_prompt(
    research_question: str,
    hypotheses: list[dict[str, Any]],
) -> str:
    schema = {
        "mechanism_builds": [
            {
                "hypothesis_id": "H1",
                "mechanism_variables": [],
                "causal_path": "",
                "expected_direction": "",
                "domain_specific_boundary_conditions": [],
                "measurable_outcomes": [],
                "mechanism_builder_notes": "",
            }
        ]
    }
    return f"""Stage 4.1 — Mechanism Builder

Research question: {research_question}

For every Stage 4 hypothesis, construct the strongest concrete and scientifically testable version of its
mechanism while preserving the original idea. Name specific measurable variables, a directed causal path,
the expected direction, domain-specific boundary conditions, and measurable outcomes.

Do not judge PASS, REJECT, or SALVAGEABLE. Do not remove, merge, replace, or reorder hypotheses. Every list
must contain at least one concrete non-empty item. Keep all 10 IDs in H1 through H10 order.

Stage 4 hypotheses:
{_json(hypotheses)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def confounder_rival_builder_prompt(
    research_question: str,
    hypotheses: list[dict[str, Any]],
    mechanism_builds: list[dict[str, Any]],
) -> str:
    schema = {
        "confounder_rival_builds": [
            {
                "hypothesis_id": "H1",
                "possible_confounders": [],
                "control_variables": [],
                "boring_rival_explanations": [],
                "rival_prediction": "",
                "distinguishing_condition": "",
                "confounder_rival_notes": "",
            }
        ]
    }
    return f"""Stage 4.2 — Confounder/Rival Builder

Research question: {research_question}

Add realistic rival explanations and explicit confounder-control logic to every hypothesis/mechanism pair.
The rival prediction must differ from the proposed mechanism's prediction, and the distinguishing condition
must state an observable result capable of separating them.

Do not judge PASS, REJECT, or SALVAGEABLE. Do not remove, merge, replace, or reorder hypotheses. Every list
must contain at least one concrete non-empty item. Keep all 10 IDs in H1 through H10 order.

Stage 4 hypotheses:
{_json(hypotheses)}

Stage 4.1 mechanism builds:
{_json(mechanism_builds)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def statistical_testability_builder_prompt(
    research_question: str,
    hypotheses: list[dict[str, Any]],
    mechanism_builds: list[dict[str, Any]],
    confounder_rival_builds: list[dict[str, Any]],
) -> str:
    schema = {
        "statistical_testability_builds": [
            {
                "hypothesis_id": "H1",
                "effect_size_expectation": "small | medium | large | unknown",
                "effect_size_rationale": "",
                "minimum_data_needed": [],
                "testable_prediction": "",
                "failure_condition": "",
                "statistical_test_plan": "",
                "statistical_testability_notes": "",
            }
        ]
    }
    return f"""Stage 4.3 — Statistical Testability Builder

Research question: {research_question}

Make every fully developed hypothesis statistically testable. Set effect_size_expectation to exactly one of
small, medium, large, or unknown. If unknown, explain exactly what data are needed to estimate it. Provide a
directional testable prediction, an operational failure condition, minimum data requirements, and a concrete
statistical test plan.

Do not judge PASS, REJECT, or SALVAGEABLE. Do not remove, merge, replace, or reorder hypotheses. Keep all 10
IDs in H1 through H10 order. minimum_data_needed must be a non-empty list of concrete strings.

Stage 4 hypotheses:
{_json(hypotheses)}

Stage 4.1 mechanism builds:
{_json(mechanism_builds)}

Stage 4.2 confounder/rival builds:
{_json(confounder_rival_builds)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per item:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def auditor_prompt(
    research_question: str,
    hypotheses: list[dict[str, Any]],
    input_description: str = "Stage 4 hypotheses",
) -> str:
    """Build the strict mechanism-filter prompt used by the legacy Auditor stage."""
    output_schema = {
        "audits": [
            {
                "hypothesis_id": "H1",
                "audit_decision": "PASS | REJECT | SALVAGEABLE",
                "variables_measurable": True,
                "causal_chain_valid": True,
                "base_rate_plausible": True,
                "confounders_identified": True,
                "effect_size_plausible": True,
                "data_requirements_clear": True,
                "mechanism_is_non_generic": True,
                "prediction_is_testable": True,
                "failure_points": [],
                "decision_reason": "",
                "salvage_note": "",
            }
        ]
    }
    return f"""Stage 5 — Strict Mechanism Auditor

Research question: {research_question}

Audit all 10 hypotheses independently and skeptically. Do not numerically score them. Do not rubber-stamp.

Strict non-generic mechanism rule:
- A mechanism is generic if the same explanation would apply to most similar problems in this domain
  without modification.
- If it does not name a specific causal path, variable relationship, boundary condition, or domain-specific
  process, set mechanism_is_non_generic to false.
- If unsure, set it to false.

PASS is allowed only when every critical check is true: {_json(list(CRITICAL_AUDIT_FIELDS))}.
If one or two critical checks fail but the idea is concretely repairable, mark SALVAGEABLE and explain the
repair in salvage_note. If the mechanism is vague, untestable, statistically weak, or domain-generic, mark
REJECT. For PASS and REJECT, salvage_note may be an empty string.

failure_points must contain every and only checklist field whose boolean is false. The complete checklist is:
{_json(list(AUDIT_BOOLEAN_FIELDS))}

Every audit must include a hypothesis-specific, non-empty decision_reason that explains the checklist
judgment. Never return an empty decision_reason. For SALVAGEABLE, salvage_note must state the concrete
repair; for PASS or REJECT, salvage_note may be an empty string.

{input_description} to audit:
{_json(hypotheses)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per audit:
{_json(output_schema)}
Return one audit for every input hypothesis, preserving IDs. Do not add fields or prose outside the JSON."""


def rival_prompt(
    research_question: str,
    pass_hypotheses: list[dict[str, Any]],
) -> str:
    schema = {
        "rival_prediction_matrix": [
            {
                "hypothesis_id": "H1",
                "meno_j_hypothesis": "",
                "meno_j_prediction": "",
                "rival_explanation": "",
                "rival_prediction": "",
                "distinguishing_test": "",
                "what_result_supports_meno_j": "",
                "what_result_supports_rival": "",
            }
        ]
    }
    return f"""Stage 6 — Rival Prediction Matrix

Research question: {research_question}

Create exactly one row for each supplied PASS hypothesis and no other hypothesis. For each, generate one
boring, plausible rival explanation. Reject generic predictions both mechanisms would make: predictions must
diverge, and the distinguishing test must identify results that discriminate the two mechanisms.

PASS hypotheses:
{_json(pass_hypotheses)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per row:
{_json(schema)}
Preserve hypothesis IDs. The hypothesis text output field must be named meno_j_hypothesis; never use
original_hypothesis or any other substitute field name. Every field shown must be a non-empty JSON string.
Do not add fields or prose outside the JSON."""


def falsification_prompt(
    research_question: str,
    pass_hypotheses: list[dict[str, Any]],
) -> str:
    schema = {
        "falsification_tests": [
            {
                "hypothesis_id": "H1",
                "strongest_falsification_test": "",
                "failure_condition": "",
                "minimum_data_needed": "",
                "most_likely_false_positive_risk": "",
                "most_likely_false_negative_risk": "",
            }
        ]
    }
    return f"""Stage 7 — Falsification Agent

Research question: {research_question}

Create exactly one rigorous falsification test for each supplied PASS hypothesis and no other hypothesis.
State an operational failure condition, the minimum data needed, and the most likely false-positive and
false-negative risks. Prefer tests capable of proving the proposed mechanism wrong, not merely finding an
association.

PASS hypotheses:
{_json(pass_hypotheses)}

Return valid JSON only, with exactly this top-level shape and exactly these fields per row:
{_json(schema)}
Preserve hypothesis IDs. Every field shown, including minimum_data_needed, must be a non-empty JSON string,
not a list or object. Do not add fields or prose outside the JSON."""


def cross_question_survivor_prompt(survivors: list[dict[str, Any]]) -> str:
    schema = {
        "combined_analysis": {
            "strongest_surviving_hypotheses": [
                {
                    "rank": 1,
                    "source_question": "Q1",
                    "hypothesis_id": "H1",
                    "selection_reason": "",
                    "comparative_advantage": "",
                    "residual_weakness": "",
                }
            ],
            "recurring_structural_patterns": [
                {
                    "pattern_id": "P1",
                    "pattern_name": "",
                    "description": "",
                    "supporting_hypotheses": [
                        {"source_question": "Q1", "hypothesis_id": "H1"}
                    ],
                    "causal_structure": "",
                    "boundary_conditions": [],
                    "shared_confounder_controls": [],
                    "testable_meta_prediction": "",
                }
            ],
            "cross_question_comparisons": [
                {
                    "question_pair": "Q1-Q2",
                    "shared_structures": [],
                    "distinctive_structures": [],
                    "discriminating_analysis": "",
                }
            ],
            "next_experiment_recommendations": [
                {
                    "experiment_id": "E3.1",
                    "title": "",
                    "target_pattern_ids": [],
                    "design": "",
                    "minimum_data_needed": [],
                    "primary_outcome": "",
                    "failure_condition": "",
                }
            ],
        }
    }
    return f"""Experiment 3 — Cross-Question Survivor Synthesis

Analyze only the validated PASS survivors supplied below. Do not alter their source question or hypothesis ID.

Tasks and exact contracts:
1. Rank exactly 9 strongest survivors globally, with ranks 1 through 9 and exactly 3 selections from each
   of Q1, Q2, and Q3. Prefer specific causal structure, discriminating prediction, falsifiability, explicit
   confounder control, and feasible data requirements. Do not rank by prose length.
2. Identify exactly 5 recurring structural patterns, identified P1 through P5. Each pattern must cite at
   least 3 unique validated PASS hypotheses spanning at least 2 questions. Across the five patterns, every
   one of the 9 strongest selections must be cited at least once.
3. Return exactly 3 pairwise comparisons in this order: Q1-Q2, Q1-Q3, Q2-Q3. Each must state shared and
   distinctive structures plus a concrete discriminating analysis.
4. Return exactly 3 next-experiment recommendations, identified E3.1 through E3.3, targeting only P1-P5.
   Each design must have explicit minimum data, primary outcome, and failure condition.

All explanatory strings must be non-empty. All list fields must be non-empty. Supporting references must
contain exactly source_question and hypothesis_id. Do not cite SALVAGEABLE, REJECT, or unknown hypotheses.

Validated PASS survivor records:
{_json(survivors)}

Return valid JSON only with exactly this structure and field names:
{_json(schema)}
Do not add fields or prose outside the JSON."""


def pattern_falsification_prompt(
    working_theory: dict[str, Any],
    literature_sources: list[dict[str, Any]],
) -> str:
    experiment_schema = {
        "experiment_id": "P1-F1",
        "title": "",
        "design": "",
        "meno_j_prediction": "",
        "competing_explanation_prediction": "",
        "measurable_outcomes": [],
        "expected_effect_size": {
            "metric": "",
            "magnitude": "SMALL | MEDIUM | LARGE | UNKNOWN",
            "expected_direction": "",
            "quantitative_target": "",
            "rationale": "",
        },
        "required_datasets_or_metadata": [],
        "implementation_difficulty": "LOW | MEDIUM | HIGH",
        "difficulty_reason": "",
        "failure_condition_for_working_theory": "",
        "supporting_hypothesis_refs": [
            {"source_question": "Q1", "hypothesis_id": "H1"}
        ],
        "literature_citation_ids": ["L1"],
        "scientific_impact_score": 1,
        "feasibility_score": 1,
        "publication_potential_score": 1,
        "information_gain_score": 1,
        "score_rationale": "",
    }
    schema = {
        "pattern_falsification_studies": [
            {
                "pattern_id": "P1",
                "pattern_name": "",
                "working_theory_claim": "",
                "strongest_competing_explanation": "",
                "competing_explanation_mechanism": "",
                "scientifically_plausible_counterexamples": [],
                "confounders_and_alternative_explanations": [],
                "evidence_supporting_competing_explanation": [],
                "evidence_refuting_competing_explanation": [],
                "distinguishing_experiments": [experiment_schema],
                "pattern_level_novelty": {
                    "rating": "LOW | MEDIUM | HIGH",
                    "rationale": "",
                    "closest_literature_citation_ids": ["L1", "L2"],
                    "novel_contribution": "",
                },
            }
        ]
    }
    return f"""Experiment 4 — Pattern Falsification Study

Treat the nine survivors and five recurring patterns below as the complete working theory. Do not generate,
add, revise, or replace hypotheses. Your goal is adversarial: design scientifically plausible attempts to
disprove each existing pattern using counterexamples, confounders, and alternative explanations.

For each pattern P1 through P5, preserving its exact pattern_name:
- state the strongest competing explanation and its causal mechanism;
- give at least 2 plausible counterexamples, at least 2 confounders/alternatives, at least 2 observations
  supporting the competitor, and at least 2 observations refuting it;
- design exactly 2 distinguishing experiments, identified P1-F1/P1-F2 through P5-F1/P5-F2;
- make the working-theory and competitor predictions diverge;
- define measurable outcomes, a scientifically plausible expected effect-size target, data/metadata needs,
  implementation difficulty, and a precommitted condition that would falsify the working theory;
- cite at least 2 of the pattern's existing validated supporting hypotheses per experiment;
- cite only literature IDs in the validated source list and use every literature source somewhere;
- assess novelty against at least 2 closest sources per pattern.

Scores are integers 1–5. HIGH implementation difficulty requires feasibility <=2; LOW difficulty requires
feasibility >=4. Do not inflate scores. Effect magnitude must be exactly SMALL, MEDIUM, LARGE, or UNKNOWN.
Novelty and difficulty ratings must be exactly LOW, MEDIUM, or HIGH. A quantitative_target may be a
preregistered range or minimally important difference stated as a non-empty string; do not fabricate a
published effect estimate. Citation objects and URLs must not be generated—use citation IDs only.

Complete working theory:
{_json(working_theory)}

Validated primary literature:
{_json(literature_sources)}

Return valid JSON only with exactly this top-level shape and exactly these fields:
{_json(schema)}
Return exactly 5 studies in P1-P5 order and exactly 2 experiments per study. Do not add prose outside JSON."""
