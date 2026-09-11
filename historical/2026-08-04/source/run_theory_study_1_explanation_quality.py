"""Build Meno-J Theory Study 1 without model or dataset calls.

The study asks what makes an explanation genuinely good and converts the
literature synthesis into an auditable contract for a Meno-J J-jump.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_theory_study_1_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_theory_study_1_protocol.md"
REPORT_JSON = OUTPUT_DIR / "meno_j_theory_study_1_explanation_quality.json"
REPORT_MD = OUTPUT_DIR / "meno_j_theory_study_1_explanation_quality.md"
REPRO_JSON = OUTPUT_DIR / "meno_j_theory_study_1_reproducibility_summary.json"
REPRO_MD = OUTPUT_DIR / "meno_j_theory_study_1_reproducibility_summary.md"


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "S01",
        "authors": "Carl G. Hempel and Paul Oppenheim",
        "year": 1948,
        "title": "Studies in the Logic of Explanation",
        "url": "https://home.csulb.edu/~cwallis/382/readings/690/recieved/hempel.studies.logic.explanation.1948.pdf",
        "access_depth": "full_text_argument_review",
        "contribution": "Makes explanation auditable through derivation from laws and initial conditions, with truth and law-likeness requirements.",
        "pressure_point": "Formal derivability does not by itself secure direction, relevance, or immunity from spurious regularities.",
    },
    {
        "source_id": "S02",
        "authors": "Philip Kitcher",
        "year": 1989,
        "title": "Explanatory Unification and the Causal Structure of the World",
        "url": "https://conservancy.umn.edu/bitstream/handle/11299/185687/13_13Kitcher.pdf",
        "access_depth": "full_text_argument_review",
        "contribution": "Explains why a small number of argument patterns that derive many facts can increase understanding.",
        "pressure_point": "Unification can impose a false unity on heterogeneous mechanisms and can reward a compact but wrong system.",
    },
    {
        "source_id": "S03",
        "authors": "Wesley C. Salmon",
        "year": 1998,
        "title": "Scientific Explanation: Causation and Unification",
        "url": "https://critica.filosoficas.unam.mx/index.php/critica/article/view/773",
        "access_depth": "official_article_and_argument_review",
        "contribution": "Treats causal-mechanical and unification accounts as potentially complementary rather than forced alternatives.",
        "pressure_point": "Causal detail alone does not select the factors relevant to the contrast actually being asked about.",
    },
    {
        "source_id": "S04",
        "authors": "Peter Machamer, Lindley Darden, and Carl F. Craver",
        "year": 2000,
        "title": "Thinking About Mechanisms",
        "url": "https://philosophy.wustl.edu/files/philosophy/imce/thinking_about_mechanisms.pdf",
        "access_depth": "full_text_argument_review",
        "contribution": "Characterizes mechanisms through organized entities and activities producing regular changes from start to finish.",
        "pressure_point": "Mechanistic completeness may add enormous detail without identifying the difference-maker for a particular question.",
    },
    {
        "source_id": "S05",
        "authors": "James Woodward",
        "year": 2003,
        "title": "Making Things Happen: A Theory of Causal Explanation",
        "url": "https://academic.oup.com/book/4324",
        "access_depth": "official_book_summary_and_selected_argument_review",
        "contribution": "Connects causal explanation to invariant relations that answer what-if-things-had-been-different questions under interventions.",
        "pressure_point": "Interventionism is strongest for causal explanation and should not be silently extended to mathematical, constitutive, or grounding explanation.",
    },
    {
        "source_id": "S06",
        "authors": "Bas C. van Fraassen",
        "year": 1980,
        "title": "The Scientific Image",
        "url": "https://academic.oup.com/book/7116",
        "access_depth": "official_book_summary_and_selected_argument_review",
        "contribution": "Shows that why-questions are contrastive and context-sensitive: why P rather than which alternative matters.",
        "pressure_point": "Context may select a relevant valid answer, but cannot turn a false dependency or unsupported story into a good explanation.",
    },
    {
        "source_id": "S07",
        "authors": "Marc Lange",
        "year": 2013,
        "title": "What Makes a Scientific Explanation Distinctively Mathematical?",
        "url": "https://www.journals.uchicago.edu/doi/abs/10.1093/bjps/axs012",
        "access_depth": "official_abstract_and_selected_argument_review",
        "contribution": "Establishes that some scientific explanations work through mathematical constraints rather than causal histories.",
        "pressure_point": "A causal-only architecture will misclassify genuine constraint explanations.",
    },
    {
        "source_id": "S08",
        "authors": "Alexander Reutlinger",
        "year": 2016,
        "title": "Is There a Monist Theory of Causal and Noncausal Explanations?",
        "url": "https://www.cambridge.org/core/journals/philosophy-of-science/article/is-there-a-monist-theory-of-causal-and-noncausal-explanations-the-counterfactual-theory-of-scientific-explanation/FBB564457C645E9F294F87C65CE8561A",
        "access_depth": "full_text_argument_review",
        "contribution": "Develops a unified counterfactual account intended to cover causal and noncausal explanation.",
        "pressure_point": "The account faces overgeneration, directionality, necessary-truth, grounding, and overdetermination cases.",
    },
    {
        "source_id": "S09",
        "authors": "Daniel A. Wilkenfeld",
        "year": 2019,
        "title": "Understanding as Compression",
        "url": "https://doi.org/10.1007/s11098-018-1152-1",
        "access_depth": "full_text_argument_review",
        "contribution": "Models understanding as a minimal representational kernel plus processes that regenerate useful information.",
        "pressure_point": "Compression concerns an epistemic achievement and does not by itself guarantee truth, direction, or explanatory relevance.",
    },
    {
        "source_id": "S10",
        "authors": "Stefan Roski",
        "year": 2021,
        "title": "Metaphysical Explanations and the Counterfactual Theory of Explanation",
        "url": "https://link.springer.com/article/10.1007/s11098-020-01518-8",
        "access_depth": "full_text_argument_review",
        "contribution": "Tests a counterfactual monism against grounding, redundancy, overdetermination, and relevance cases.",
        "pressure_point": "Weak dependency conditions trivialize; strong conditions exclude paradigmatic grounding explanations.",
    },
    {
        "source_id": "S11",
        "authors": "Victor Gijsbers",
        "year": 2016,
        "title": "Explanatory Pluralism and the (Dis)unity of Science",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4786542/",
        "access_depth": "full_text_argument_review",
        "contribution": "Shows that explanations may resist integration when they imply incompatible counterfactual consequences.",
        "pressure_point": "Pluralism needs a rule for genuine complementarity versus incompatible claims; otherwise it becomes anything-goes.",
    },
    {
        "source_id": "S12",
        "authors": "Eric Muszynski and Christophe Malaterre",
        "year": 2021,
        "title": "A Roadmap to Explanatory Pluralism",
        "url": "https://link.springer.com/article/10.1007/s11229-020-02856-0",
        "access_depth": "official_abstract_and_selected_argument_review",
        "contribution": "Separates type, fragmentation, and insular forms of explanatory pluralism.",
        "pressure_point": "Saying that there are many explanation types is a map of the problem, not yet a quality-control procedure.",
    },
    {
        "source_id": "S13",
        "authors": "J. De Rizzo and B. Schnieder",
        "year": 2026,
        "title": "Mathematical Explanation: A Defence and a Challenge",
        "url": "https://academic.oup.com/philmat/advance-article/doi/10.1093/philmat/nkag008/8729470",
        "access_depth": "full_text_argument_review",
        "contribution": "Defends mathematical explanation while arguing that ordinary counterfactual dependence is neither sufficient nor necessary for explanation.",
        "pressure_point": "A universal counterfactual-compression definition fails mutual-dependence, overdetermination, constitution, and necessary-truth cases.",
    },
]


THEORY_MATRIX = [
    {
        "theory_id": "T1",
        "name": "Deductive-nomological",
        "best_insight": "Good explanations must expose an inferential bridge and cannot be mere assertions.",
        "decisive_limit": "Entailment plus true premises can preserve the wrong direction or irrelevant information.",
        "disposition": "RETAIN_AS_VALIDITY_GATE_NOT_COMPLETE_THEORY",
        "sources": ["S01"],
    },
    {
        "theory_id": "T2",
        "name": "Unification",
        "best_insight": "Explanatory breadth and reusable patterns matter; isolated restatement is weak.",
        "decisive_limit": "A compact conspiracy or an imposed universal pattern can unify while tracking no warranted relation.",
        "disposition": "RETAIN_AS_BREADTH_PREFERENCE_AFTER_VALIDITY",
        "sources": ["S02", "S03"],
    },
    {
        "theory_id": "T3",
        "name": "Causal-mechanistic",
        "best_insight": "Organized entities, activities, and causal direction distinguish productive stories from correlations.",
        "decisive_limit": "Not every explanation is causal, and exhaustive mechanism can obscure the relevant difference-maker.",
        "disposition": "RETAIN_AS_TYPE_SPECIFIC_WARRANT",
        "sources": ["S03", "S04"],
    },
    {
        "theory_id": "T4",
        "name": "Interventionist and counterfactual",
        "best_insight": "A deep causal explanation supports stable what-if answers and identifies manipulable difference-makers.",
        "decisive_limit": "Ordinary counterfactual dependence is neither universally necessary nor sufficient, especially under overdetermination and noncausal explanation.",
        "disposition": "RETAIN_FOR_CAUSAL_GENERATIVITY_NOT_AS_UNIVERSAL_ESSENCE",
        "sources": ["S05", "S08", "S10", "S13"],
    },
    {
        "theory_id": "T5",
        "name": "Pragmatic and contrastive",
        "best_insight": "The same fact can answer one why-question and fail another because the foil and purpose differ.",
        "decisive_limit": "Audience satisfaction cannot license falsehood or unsupported dependence.",
        "disposition": "RETAIN_AS_QUESTION_SPECIFICATION_GATE",
        "sources": ["S06"],
    },
    {
        "theory_id": "T6",
        "name": "Mathematical and constraint-based",
        "best_insight": "Necessity, impossibility, constitution, and grounding can explain without a causal process.",
        "decisive_limit": "A proof that establishes a result need not reveal why it holds; type-specific direction and relevance still matter.",
        "disposition": "RETAIN_AS_NONCAUSAL_WARRANT_FAMILY",
        "sources": ["S07", "S10", "S13"],
    },
    {
        "theory_id": "T7",
        "name": "Understanding as compression",
        "best_insight": "Useful understanding removes detail while retaining the ability to regenerate needed information.",
        "decisive_limit": "Compression can be achieved by an inaccurate, conspiratorial, or directionless representation.",
        "disposition": "RETAIN_AS_SELECTIVITY_AND_USABILITY_PREFERENCE",
        "sources": ["S09"],
    },
    {
        "theory_id": "T8",
        "name": "Explanatory pluralism",
        "best_insight": "Different questions legitimately require different explanatory relation types and levels.",
        "decisive_limit": "Incompatible consequences within the same target, contrast, and scope cannot all be accepted as complementary.",
        "disposition": "RETAIN_AS_CONSTRAINED_QUESTION_INDEXED_PLURALISM",
        "sources": ["S03", "S11", "S12"],
    },
]


STRESS_TESTS = [
    {
        "case_id": "C1",
        "name": "Flagpole and shadow reversal",
        "challenge": "A derivation can calculate pole height from shadow length although the shadow does not explain the pole.",
        "rules_out": ["derivation_is_sufficient", "prediction_is_sufficient"],
        "contract_response": "Require a type-specific direction warrant; for causal claims, interventions on pole height change the shadow, not conversely.",
        "status": "HANDLED",
    },
    {
        "case_id": "C2",
        "name": "Barometer and storm",
        "challenge": "A barometer predicts a storm through a shared cause but does not cause or mechanically explain it.",
        "rules_out": ["correlation_is_explanation", "accuracy_is_sufficient"],
        "contract_response": "Require rivals and a causal/mechanistic warrant that distinguishes indicator, common cause, and producer.",
        "status": "HANDLED",
    },
    {
        "case_id": "C3",
        "name": "Causal overdetermination",
        "challenge": "Bob's shot can explain a death even when Boba's shot would have caused death anyway, so simple but-for dependence fails.",
        "rules_out": ["ordinary_counterfactual_dependence_is_necessary"],
        "contract_response": "Allow causal-production and contribution warrants; record redundancy and test component-removal or timing consequences rather than only but-for dependence.",
        "status": "HANDLED_WITH_TYPE_SPECIFIC_WARRANT",
    },
    {
        "case_id": "C4",
        "name": "Scarlet and red constitution",
        "challenge": "Being scarlet can explain being red even though a nearby non-scarlet state may still be red.",
        "rules_out": ["ordinary_counterfactual_dependence_is_necessary", "causation_is_necessary"],
        "contract_response": "Route constitutive claims through asymmetric inclusion or grounding rather than an intervention test.",
        "status": "HANDLED_WITH_NONCAUSAL_WARRANT",
    },
    {
        "case_id": "C5",
        "name": "Königsberg bridges",
        "challenge": "The impossibility of an Eulerian walk is explained by graph structure, not by a causal history.",
        "rules_out": ["causation_is_necessary"],
        "contract_response": "Route mathematical claims through constraint, invariance, or impossibility derivations and test whether the cited structure is indispensable.",
        "status": "HANDLED_WITH_NONCAUSAL_WARRANT",
    },
    {
        "case_id": "C6",
        "name": "Perfect lookup table",
        "challenge": "A table can predict every observed case while supplying no transferable relation or answer to a changed case.",
        "rules_out": ["prediction_is_sufficient", "fit_is_sufficient"],
        "contract_response": "Require generativity beyond stored instances and a warranted bridge from selected factors to the target.",
        "status": "HANDLED",
    },
    {
        "case_id": "C7",
        "name": "Elegant conspiracy",
        "challenge": "A single hidden-agent story can compress and unify many facts while remaining insulated from failure.",
        "rules_out": ["compression_is_sufficient", "unification_is_sufficient"],
        "contract_response": "Validity, rival discrimination, and explicit failure conditions are mandatory gates that elegance cannot compensate for.",
        "status": "HANDLED",
    },
    {
        "case_id": "C8",
        "name": "Mechanistic overload",
        "challenge": "A complete molecular history may be true but worse than a dose difference for explaining why this patient, rather than a matched patient, responded.",
        "rules_out": ["more_detail_is_always_better", "mechanism_completeness_is_sufficient"],
        "contract_response": "Index relevance to the foil and require an irrelevance justification for omitted and included detail.",
        "status": "HANDLED",
    },
    {
        "case_id": "C9",
        "name": "Foil shift",
        "challenge": "Why the plant died rather than lived, rather than the neighboring plant, and rather than yesterday are different questions.",
        "rules_out": ["explanation_quality_is_intrinsic_to_text"],
        "contract_response": "Require target, contrast, background, purpose, and scope before evaluating an answer.",
        "status": "HANDLED",
    },
    {
        "case_id": "C10",
        "name": "Incompatible plural explanations",
        "challenge": "Two accounts may be useful at different levels yet imply incompatible consequences for the same intervention and scope.",
        "rules_out": ["pluralism_means_all_accounts_can_coexist"],
        "contract_response": "Treat accounts as complementary only when question or relation type differs; same-scope divergent consequences trigger a rival test.",
        "status": "HANDLED_AS_ADJUDICATION_RULE",
    },
]


def protocol() -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 1: What Makes an Explanation Genuinely Good?",
        "protocol_date": date.today().isoformat(),
        "status": "FROZEN_AFTER_INITIAL_SCOPING_BEFORE_FINAL_ADJUDICATION",
        "scope": "Theory-only study; no WESAD data, numerical experiment, LLM, or OpenRouter call.",
        "research_question": "What properties distinguish a genuinely good explanation from a merely accurate, detailed, simple, persuasive, or predictive account?",
        "candidate_families": [
            "deductive-nomological",
            "unification",
            "causal-mechanistic",
            "interventionist/counterfactual",
            "pragmatic/contrastive",
            "mathematical/constraint",
            "understanding-as-compression",
            "explanatory pluralism",
        ],
        "success_criteria": {
            "major_theory_families_compared": 8,
            "minimum_adversarial_cases": 10,
            "must_separate_truth_relevance_generativity_and_preferences": True,
            "must_handle_causal_and_noncausal_cases": True,
            "must_not_reduce_quality_to_one_scalar": True,
            "must_state_scope_and_unresolved_limits": True,
            "must_produce_operational_meno_j_contract": True,
            "must_define_auditable_j_jump": True,
        },
        "failure_conditions": [
            "The synthesis treats prediction, compression, mechanism, counterfactual dependence, or audience satisfaction as sufficient by itself.",
            "The synthesis calls every rival complementary even when same-scope consequences conflict.",
            "The contract cannot say what evidence warrants different explanation types.",
            "The J-jump definition rewards novelty without retention, reach, or falsifiability.",
            "The report claims empirical validation or established novelty from a theory-only comparison.",
        ],
        "evidence_policy": "Primary papers and official publication pages; access depth is recorded per source and claims are limited accordingly.",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report(protocol_sha256: str) -> dict[str, Any]:
    return {
        "study_name": "Meno-J Theory Study 1: What Makes an Explanation Genuinely Good?",
        "research_question": protocol()["research_question"],
        "method": {
            "mode": "adversarial conceptual synthesis",
            "protocol_sha256": protocol_sha256,
            "llm_or_api_calls": False,
            "dataset_calls": False,
            "source_count": len(SOURCES),
            "full_text_argument_review_count": sum(
                source["access_depth"] == "full_text_argument_review" for source in SOURCES
            ),
            "qualification": "This is a defensible architecture synthesis, not an empirical proof or a priority claim of philosophical novelty.",
        },
        "sources": SOURCES,
        "theory_matrix": THEORY_MATRIX,
        "stress_tests": STRESS_TESTS,
        "failed_initial_candidate": {
            "name": "Counterfactual Compression Theory",
            "claim": "A good explanation is a lossy compression that preserves counterfactual dependency structure.",
            "decision": "REJECT_AS_UNIVERSAL_THEORY",
            "why": [
                "Compression is not sufficient: false or unfalsifiable stories can compress and unify.",
                "Ordinary counterfactual dependence is not sufficient: mutual or self-dependence can be nonexplanatory.",
                "Ordinary counterfactual dependence is not necessary: overdetermined causal, constitutive, grounding, and some mathematical cases survive without it.",
                "Understanding and explanation are related but not identical; a useful representation can be inaccurate.",
            ],
            "sources": ["S09", "S10", "S13"],
            "scientific_value": "The rejected candidate exposed the need for relation-type routing rather than a seductive monist slogan.",
        },
        "result": {
            "name": "Meno-J Explanation Contract",
            "short_definition": "A good explanation is a question-indexed, selectively simplified account whose premises are adequately warranted, whose bridge to the target is licensed by the relevant relation type, and whose scope, rivals, consequences, omissions, and failure conditions are explicit.",
            "architecture_status": "DEFENSIBLE_CONSTRAINED_PLURALIST_SYNTHESIS",
            "not_claimed": [
                "a universal metaphysical essence of explanation",
                "empirical validation",
                "philosophical priority or novelty",
                "that counterfactual dependence is always necessary or sufficient",
            ],
            "central_findings": [
                {
                    "finding_id": "F1",
                    "finding": "Explanation quality is relational, not an intrinsic property of a paragraph.",
                    "consequence": "Target, foil, background, audience/purpose, relation type, and scope must be declared before audit.",
                    "sources": ["S06"],
                },
                {
                    "finding_id": "F2",
                    "finding": "Quality is a gated partial order, not a compensatory scalar score.",
                    "consequence": "Elegance, simplicity, breadth, or detail cannot compensate for false premises, an unwarranted bridge, or no vulnerability to rivals.",
                    "sources": ["S01", "S02", "S04", "S09"],
                },
                {
                    "finding_id": "F3",
                    "finding": "Explanatory warrants are plural but disciplined.",
                    "consequence": "Causal, mechanistic, statistical, mathematical, constitutive, and intentional accounts require different evidence; they are not interchangeable.",
                    "sources": ["S03", "S04", "S05", "S07", "S11", "S13"],
                },
                {
                    "finding_id": "F4",
                    "finding": "Counterfactual reach is a powerful depth test where meaningful, not a universal definition.",
                    "consequence": "Use interventions for causal claims, but allow production, grounding, constitution, constraint, or derivational consequences where ordinary but-for dependence fails.",
                    "sources": ["S05", "S08", "S10", "S13"],
                },
                {
                    "finding_id": "F5",
                    "finding": "Good explanation uses controlled omission.",
                    "consequence": "Details are retained only when they affect the stated contrast, warrant, consequences, scope, or rival discrimination; omitted details need an irrelevance reason.",
                    "sources": ["S02", "S04", "S09"],
                },
                {
                    "finding_id": "F6",
                    "finding": "Pluralism is question-indexed, not anything-goes.",
                    "consequence": "Different accounts may coexist for different contrasts or relation types; conflicting same-scope consequences must be tested as rivals.",
                    "sources": ["S11", "S12"],
                },
            ],
        },
        "contract": {
            "required_fields": [
                "target P",
                "contrast or foil Q",
                "purpose and intended user",
                "background conditions",
                "scope and boundary",
                "relation type",
                "selected difference-makers or constraints",
                "type-specific warrant",
                "bridge from explanans to target",
                "type-appropriate consequence profile",
                "omitted details and irrelevance justification",
                "strongest rivals",
                "divergent predictions or consequences",
                "failure conditions",
            ],
            "relation_type_routes": {
                "causal": "intervention/invariance, temporal direction, common-cause controls, production evidence, and redundancy handling",
                "mechanistic": "entities, activities, organization, start/finish conditions, perturbation or decomposition evidence",
                "statistical": "stable probabilistic relation, calibration, rival confounding controls, domain and sampling boundary; correlation alone is insufficient",
                "mathematical_constraint": "valid derivation, indispensability of the cited structure, direction or asymmetry, and impossibility/invariance consequences",
                "constitutive_or_grounding": "asymmetric composition, realization, entailment, or dependence warrant; do not force an intervention semantics",
                "intentional_or_reason_based": "agent's reasons, sensitivity to alternatives, background norms/information, and rival causal-only accounts",
            },
            "ordered_gates": [
                {
                    "gate": "G0_QUESTION",
                    "pass_condition": "Target, foil, purpose, background, and scope are explicit.",
                },
                {
                    "gate": "G1_ADEQUACY",
                    "pass_condition": "Premises and observations are sufficiently true/evidenced for the claim; derivations are internally valid.",
                },
                {
                    "gate": "G2_WARRANT",
                    "pass_condition": "The cited relation has the evidence and direction required by its declared type.",
                },
                {
                    "gate": "G3_RELEVANCE_AND_SELECTIVITY",
                    "pass_condition": "Included factors answer the stated contrast; important omissions and irrelevant additions are controlled.",
                },
                {
                    "gate": "G4_GENERATIVITY",
                    "pass_condition": "The account supports new type-appropriate consequences beyond restating the target.",
                },
                {
                    "gate": "G5_RIVAL_VULNERABILITY",
                    "pass_condition": "At least one strong rival, a discriminating consequence, and a failure condition are explicit.",
                },
            ],
            "post_gate_preferences": [
                "simplicity",
                "breadth/unification",
                "precision",
                "cognitive usability",
                "mechanistic detail",
                "elegance",
            ],
            "preference_rule": "Preferences rank only explanations that pass the relevant gates; they cannot rescue a failed gate.",
        },
        "j_jump": {
            "definition": "A J-jump is an auditable change in representation that reorganizes variables, relations, levels, or admissible contrasts and earns acceptance by retaining warranted successes, gaining new discriminating reach, and exposing itself to new failure conditions.",
            "criteria": {
                "J1_representation_change": "The proposal changes the map, not merely the wording or number of details.",
                "J2_retention": "Previously validated consequences are preserved as a special case, or their failure boundary is explicitly demonstrated.",
                "J3_new_reach": "The new representation resolves at least one prior anomaly, rival, or previously unanswerable contrast.",
                "J4_compression_control": "The jump removes assumptions or detail without losing the warranted consequences it claims to retain.",
                "J5_rival_discrimination": "It produces consequences that separate it from the strongest old and alternative representations.",
                "J6_falsifiability_growth": "It creates at least one new concrete way to fail.",
            },
            "decision_rule": "Call a proposal a J-jump candidate only if J1 is true and J2-J6 are explicit. Promote it to a surviving J-jump only after the relevant explanation-contract gates pass.",
            "rejected_shortcuts": [
                "novel wording",
                "more hypotheses",
                "greater confidence",
                "a prettier unified story",
                "an unexplained accuracy gain",
                "a model-generated idea with no retained-success map",
            ],
            "meno_j_architecture_change": "Candidate generation supplies representation mutations. The Falsification Engine evaluates preservation, warranted reach, and added vulnerability; it does not equate generation with thinking.",
        },
        "limitations": [
            "The type routes are an engineering contract, not a settled metaphysics of every possible explanation.",
            "Type classification can itself be contested, especially for mixed causal-constitutive or mathematical-empirical explanations.",
            "Intentional and normative explanation need deeper treatment before the contract is used outside scientific/technical domains.",
            "The source set is purposive rather than a systematic review, and several books/articles were available only through official summaries or selected argument access.",
            "A human or AI benchmark is still needed to test whether the contract improves explanatory judgment and J-jump discovery in practice.",
        ],
        "next_theory_stage": {
            "name": "Adversarial J-Jump Casebook",
            "purpose": "Apply the frozen contract to historical and synthetic representation changes without numerical datasets.",
            "cases": [
                "Ptolemaic epicycles to Keplerian ellipses",
                "Keplerian regularities to Newtonian dynamics",
                "caloric fluid to kinetic theory",
                "miasma to germ theory",
                "classical inheritance to Mendelian mechanism",
                "lookup-table prediction to causal model",
            ],
            "success_condition": "The contract must distinguish genuine representational jumps from mere relabeling, added detail, curve fitting, and retrospective storytelling while recording disputed cases rather than forcing unanimity.",
        },
        "decision": "THEORY_STAGE_1_SUCCESS_WITH_NARROWED_CLAIM",
    }


def render_protocol_md(value: dict[str, Any]) -> str:
    lines = [
        "# Meno-J Theory Study 1 Protocol",
        "",
        f"**Question:** {value['research_question']}",
        "",
        f"**Status:** `{value['status']}`",
        "",
        f"**Scope:** {value['scope']}",
        "",
        "## Success criteria",
        "",
    ]
    for key, item in value["success_criteria"].items():
        lines.append(f"- `{key}`: {item}")
    lines.extend(["", "## Failure conditions", ""])
    lines.extend(f"- {item}" for item in value["failure_conditions"])
    lines.extend(["", "## Evidence policy", "", value["evidence_policy"], ""])
    return "\n".join(lines)


def render_report_md(value: dict[str, Any]) -> str:
    result = value["result"]
    lines = [
        "# What Makes an Explanation Genuinely Good?",
        "",
        "## Outcome",
        "",
        f"**{result['name']}:** {result['short_definition']}",
        "",
        f"Decision: **{value['decision']}**.",
        "",
        "This is a constrained architecture synthesis, not a universal metaphysical theory, empirical proof, or claim of philosophical priority.",
        "",
        "## The significant correction",
        "",
        f"The initial candidate—**{value['failed_initial_candidate']['name']}**—was **rejected as a universal theory**. Compression and counterfactual reach remain useful, but neither is a universal test of explanation. Causal overdetermination, constitution, grounding, and mathematical explanation defeat the necessity claim; self-dependence and directionless cases defeat sufficiency.",
        "",
        "## Central findings",
        "",
    ]
    for item in result["central_findings"]:
        lines.append(f"- **{item['finding_id']}: {item['finding']}** {item['consequence']}")
    lines.extend([
        "",
        "## The gated architecture",
        "",
        "Quality is not one compensatory score. An account must pass the relevant gates in order:",
        "",
    ])
    for gate in value["contract"]["ordered_gates"]:
        lines.append(f"1. **{gate['gate']}** — {gate['pass_condition']}")
    lines.extend([
        "",
        "Simplicity, breadth, precision, usability, detail, and elegance rank only the accounts that pass. They cannot repair a failed validity, warrant, relevance, generativity, or rival-vulnerability gate.",
        "",
        "## Explanation Contract",
        "",
    ])
    for item in value["contract"]["required_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Relation-type routes", ""])
    for key, item in value["contract"]["relation_type_routes"].items():
        lines.append(f"- **{key.replace('_', ' ')}:** {item}")
    lines.extend(["", "## Adversarial cases", ""])
    lines.append("| Case | What it defeats | Contract response | Status |")
    lines.append("|---|---|---|---|")
    for item in value["stress_tests"]:
        defeats = ", ".join(code.replace("_", " ") for code in item["rules_out"])
        lines.append(f"| {item['case_id']} — {item['name']} | {defeats} | {item['contract_response']} | {item['status']} |")
    lines.extend([
        "",
        "## The J-jump result",
        "",
        value["j_jump"]["definition"],
        "",
    ])
    for key, item in value["j_jump"]["criteria"].items():
        lines.append(f"- **{key}:** {item}")
    lines.extend([
        "",
        f"**Decision rule:** {value['j_jump']['decision_rule']}",
        "",
        "In simple words: AI does not earn a J-jump by producing a surprising sentence. It earns one by changing the map of the problem, keeping what the old map got right, explaining something the old map could not, beating serious alternatives, and giving us new ways to prove it wrong.",
        "",
        "## Theory comparison",
        "",
        "| Family | Best retained insight | Decisive limit | Disposition |",
        "|---|---|---|---|",
    ])
    for item in value["theory_matrix"]:
        lines.append(f"| {item['name']} | {item['best_insight']} | {item['decisive_limit']} | `{item['disposition']}` |")
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in value["limitations"])
    lines.extend([
        "",
        "## Next theory stage",
        "",
        f"**{value['next_theory_stage']['name']}:** {value['next_theory_stage']['purpose']}",
        "",
    ])
    lines.extend(f"- {item}" for item in value["next_theory_stage"]["cases"])
    lines.extend(["", "## Sources", ""])
    for source in value["sources"]:
        lines.append(f"- **{source['source_id']} — [{source['title']}]({source['url']})** ({source['authors']}, {source['year']}). Access: `{source['access_depth']}`. {source['contribution']} Limit: {source['pressure_point']}")
    lines.append("")
    return "\n".join(lines)


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = protocol()
    _atomic_json(PROTOCOL_JSON, frozen)
    PROTOCOL_MD.write_text(render_protocol_md(frozen), encoding="utf-8")

    synthesis = report(_sha256(PROTOCOL_JSON))
    _atomic_json(REPORT_JSON, synthesis)
    REPORT_MD.write_text(render_report_md(synthesis), encoding="utf-8")

    reproducibility = {
        "study_name": synthesis["study_name"],
        "status": "BUILT_PENDING_INDEPENDENT_VALIDATION",
        "execution_date": date.today().isoformat(),
        "inputs": {
            "protocol": str(PROTOCOL_JSON.resolve()),
            "protocol_sha256": _sha256(PROTOCOL_JSON),
            "source_ledger_embedded_in_report": True,
        },
        "outputs": {
            "report_json": str(REPORT_JSON.resolve()),
            "report_json_sha256": _sha256(REPORT_JSON),
            "report_markdown": str(REPORT_MD.resolve()),
            "report_markdown_sha256": _sha256(REPORT_MD),
        },
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "external_calls": {"openrouter": False, "llm": False, "dataset": False},
        "encoding": "UTF-8",
        "deterministic_rebuild_expected": True,
        "limitations": synthesis["limitations"],
    }
    _atomic_json(REPRO_JSON, reproducibility)
    REPRO_MD.write_text(
        "# Meno-J Theory Study 1 Reproducibility\n\n"
        f"- Status: **{reproducibility['status']}**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['inputs']['protocol_sha256']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['outputs']['report_json_sha256']}`\n"
        f"- Report Markdown SHA-256: `{reproducibility['outputs']['report_markdown_sha256']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n",
        encoding="utf-8",
    )
    print(f"Built {REPORT_JSON.name} and {REPORT_MD.name}")


if __name__ == "__main__":
    main()
