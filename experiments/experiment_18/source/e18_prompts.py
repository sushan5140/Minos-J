"""Prompts, output schemas and output validation for Experiment 18.

Every call of every arm is built as:

    SYSTEM_MESSAGE
    user prompt = COMMON_HEADER + vocabulary + evidence packet
                  + [previous outputs of THIS trial, verbatim JSON]
                  + step instruction (the ONLY arm-specific text)
                  + output-format line

so factual information, vocabulary, evidence, answer format and confidence
requirements are identical across arms; only the reasoning procedure differs.
"""

from __future__ import annotations

from typing import Any

from e18_common import dumps
from e18_tasks import MECHANISM_IDS, mechanism_vocabulary

ARMS = ("A", "C", "D", "B")
CALLS_PER_ARM = {"A": 3, "C": 3, "D": 3, "B": 1}
N_RIVALS = 4
SYSTEM_MESSAGE = "You are a careful scientific reasoner. Return only JSON that matches the required schema."

COMMON_HEADER = (
    "Diagnostic task. Exactly one of the candidate mechanisms below was planted as the cause of the "
    "subgroup's under-coverage. Use only the information given here."
)

# --------------------------------------------------------------------------- step instructions (arm-specific)
INSTRUCTIONS: dict[tuple[str, int], str] = {
    ("A", 1): (
        f"Step 1 of 3. Choose the {N_RIVALS} mechanisms you consider the strongest rival explanations. "
        "For each, state two discriminating predictions: observations in these diagnostics that should hold "
        "if that mechanism is the cause and should not hold otherwise."
    ),
    ("A", 2): (
        "Step 2 of 3. Test each rival's predictions against the observed diagnostics, one by one, and record "
        "whether the evidence supports or contradicts each prediction. Eliminate every rival that has a "
        "contradicted prediction."
    ),
    ("A", 3): (
        "Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated "
        "probability for every candidate mechanism."
    ),
    ("C", 1): (
        "Step 1 of 3. Diagnose which candidate mechanism is the planted cause of the subgroup's under-coverage. "
        "Give your diagnosis, a short justification that refers to the diagnostics, and a calibrated "
        "probability for every candidate mechanism."
    ),
    ("C", 2): (
        "Step 2 of 3. Critique your step-1 diagnosis: look for mistakes in your reasoning, diagnostics you "
        "overlooked or misread, and alternative explanations you may have dismissed too quickly."
    ),
    ("C", 3): (
        "Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated "
        "probability for every candidate mechanism."
    ),
    ("D", 1): (
        f"Step 1 of 3. Choose the {N_RIVALS} mechanisms you consider the strongest rival explanations. "
        "For each, give a short rationale, referring to the diagnostics, for why it is a plausible cause of "
        "the subgroup's under-coverage."
    ),
    ("D", 2): (
        "Step 2 of 3. Weigh the rivals against each other by their overall plausibility given the diagnostics "
        "as a whole, and rank them. Give one overall judgement per rival rather than testing predictions one by one."
    ),
    ("D", 3): (
        "Step 3 of 3. Using your previous steps, select the single planted mechanism and give a calibrated "
        "probability for every candidate mechanism."
    ),
    ("B", 1): (
        "Select the single planted mechanism and give a calibrated probability for every candidate mechanism."
    ),
}

# --------------------------------------------------------------------------- schemas
_ID = {"type": "string", "enum": list(MECHANISM_IDS)}
_TEXT = {"type": "string", "minLength": 1}


def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


FINAL_SCHEMA = _obj({
    "mechanism_id": _ID,
    "probabilities": _obj({m: {"type": "number", "minimum": 0, "maximum": 1} for m in MECHANISM_IDS}),
    "justification": _TEXT,
})
SCHEMAS: dict[tuple[str, int], tuple[str, dict[str, Any]]] = {
    ("A", 1): ("rivals_with_predictions", _obj({"rivals": {"type": "array", "minItems": N_RIVALS, "maxItems": N_RIVALS,
        "items": _obj({"mechanism_id": _ID, "discriminating_predictions": {"type": "array", "minItems": 2, "maxItems": 2, "items": _TEXT}})}})),
    ("A", 2): ("falsification_tests", _obj({
        "tests": {"type": "array", "minItems": N_RIVALS, "items": _obj({"mechanism_id": _ID, "prediction": _TEXT,
                  "observed_evidence": _TEXT, "verdict": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED"]}})},
        "eliminated": {"type": "array", "items": _ID}, "surviving": {"type": "array", "items": _ID}})),
    ("A", 3): ("final_answer", FINAL_SCHEMA),
    ("C", 1): ("final_answer", FINAL_SCHEMA),
    ("C", 2): ("critique", _obj({"critique_points": {"type": "array", "minItems": 1, "items": _TEXT},
        "overlooked_or_misread_evidence": {"type": "array", "items": _TEXT},
        "alternative_explanations": {"type": "array", "items": _TEXT}})),
    ("C", 3): ("final_answer", FINAL_SCHEMA),
    ("D", 1): ("rivals_with_rationale", _obj({"rivals": {"type": "array", "minItems": N_RIVALS, "maxItems": N_RIVALS,
        "items": _obj({"mechanism_id": _ID, "rationale": _TEXT})}})),
    ("D", 2): ("plausibility_ranking", _obj({
        "assessments": {"type": "array", "minItems": N_RIVALS, "maxItems": N_RIVALS,
                        "items": _obj({"mechanism_id": _ID, "overall_plausibility": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                                       "judgement": _TEXT})},
        "ranking": {"type": "array", "minItems": N_RIVALS, "maxItems": N_RIVALS, "items": _ID}})),
    ("D", 3): ("final_answer", FINAL_SCHEMA),
    ("B", 1): ("final_answer", FINAL_SCHEMA),
}
OUTPUT_LINE = "Return JSON only, matching the provided schema exactly."


def build_prompt(arm: str, call: int, public_case: dict[str, Any], previous: list[dict[str, Any]]) -> str:
    """public_case must contain only case_id/packet/packet_sha256 (never answer-key fields)."""
    forbidden = {"true_mechanism", "is_decoy", "decoy_mechanism", "decoy_kind", "distractor_mechanism", "_key", "evidence"}
    if forbidden & set(public_case):
        raise ValueError("Answer-key fields must never reach prompt construction.")
    parts = [COMMON_HEADER, "", mechanism_vocabulary(), "", public_case["packet"], ""]
    if previous:
        parts.append("Your outputs from the previous steps of this task:")
        for index, output in enumerate(previous, 1):
            parts.append(f"[step {index}] {dumps(output, sort_keys=True)}")
        parts.append("")
    parts += [INSTRUCTIONS[(arm, call)], OUTPUT_LINE]
    return "\n".join(parts)


# --------------------------------------------------------------------------- semantic validation
class OutputInvalid(Exception):
    pass


def _check_final(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("mechanism_id") not in MECHANISM_IDS:
        raise OutputInvalid("mechanism_id not in vocabulary")
    probs = payload.get("probabilities")
    if not isinstance(probs, dict) or set(probs) != set(MECHANISM_IDS):
        raise OutputInvalid("probabilities must cover exactly the six mechanisms")
    values = [probs[m] for m in MECHANISM_IDS]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or v > 1 for v in values):
        raise OutputInvalid("probabilities must be numbers in [0, 1]")
    total = sum(values)
    if not 0.97 <= total <= 1.03:
        raise OutputInvalid(f"probabilities sum to {total:.3f}, outside [0.97, 1.03]")
    normalized = {m: probs[m] / total for m in MECHANISM_IDS}
    return {**payload, "probabilities_normalized": normalized}


def _check_rivals(payload: dict[str, Any], key: str) -> dict[str, Any]:
    rivals = payload.get("rivals")
    ids = [r.get("mechanism_id") for r in rivals] if isinstance(rivals, list) else []
    if len(ids) != N_RIVALS or len(set(ids)) != N_RIVALS or not set(ids) <= set(MECHANISM_IDS):
        raise OutputInvalid(f"need exactly {N_RIVALS} distinct rival mechanisms")
    if key == "predictions" and any(len(r.get("discriminating_predictions", [])) != 2 for r in rivals):
        raise OutputInvalid("each rival needs exactly two discriminating predictions")
    return payload


def validate_output(arm: str, call: int, payload: Any, previous: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise OutputInvalid("output must be a JSON object")
    name = SCHEMAS[(arm, call)][0]
    if name == "final_answer":
        return _check_final(payload)
    if name == "rivals_with_predictions":
        return _check_rivals(payload, "predictions")
    if name == "rivals_with_rationale":
        return _check_rivals(payload, "rationale")
    rival_ids = {r["mechanism_id"] for r in previous[0]["rivals"]} if previous and "rivals" in previous[0] else set()
    if name == "falsification_tests":
        tested = {t.get("mechanism_id") for t in payload.get("tests", [])}
        if rival_ids and not rival_ids <= tested:
            raise OutputInvalid("every rival must be tested")
        if not set(payload.get("eliminated", [])) | set(payload.get("surviving", [])) <= set(MECHANISM_IDS):
            raise OutputInvalid("eliminated/surviving must use vocabulary ids")
        return payload
    if name == "plausibility_ranking":
        if rival_ids and {a.get("mechanism_id") for a in payload.get("assessments", [])} != rival_ids:
            raise OutputInvalid("assess exactly the step-1 rivals")
        if rival_ids and set(payload.get("ranking", [])) != rival_ids:
            raise OutputInvalid("rank exactly the step-1 rivals")
        return payload
    if name == "critique":
        return payload
    raise OutputInvalid(f"unknown output type {name}")
