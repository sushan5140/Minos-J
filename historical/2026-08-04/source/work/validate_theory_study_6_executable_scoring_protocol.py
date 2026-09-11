"""Independently replay and validate Meno-J Theory Study 6."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_theory_study_6_executable_scoring_protocol as study  # noqa: E402
from meno_j_epistemic_scorer import RULE_IDS, score_assessment  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_theory_study_6_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_theory_study_6_validation.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"Expected JSON object: {path}"
    return value


def credential_scan() -> list[str]:
    marker = "sk-" + "or-v1"
    matches: list[str] = []
    excluded = {".git", "vendor", "__pycache__", "external", "e13_data"}
    for path in PROJECT_DIR.rglob("*"):
        if not path.is_file() or excluded.intersection(path.parts):
            continue
        if path.name == ".env" or path.suffix.lower() not in {".py", ".json", ".md", ".txt"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if marker in content:
            matches.append(str(path.resolve()))
    return sorted(set(matches))


def main() -> None:
    required = [
        study.STUDY2, study.STUDY3, study.STUDY4, study.STUDY5, study.STUDY5_VALIDATION,
        study.PROTOCOL_JSON, study.PROTOCOL_MD, study.REPORT_JSON, study.REPORT_MD,
        study.REPRO_JSON, study.REPRO_MD,
    ]
    for path in required:
        assert path.is_file(), f"Missing required artifact: {path}"
        path.read_text(encoding="utf-8")
    assert read_json(study.STUDY5_VALIDATION)["status"] == "PASS"

    protocol = read_json(study.PROTOCOL_JSON)
    report = read_json(study.REPORT_JSON)
    reproducibility = read_json(study.REPRO_JSON)
    assert protocol == study.protocol()
    assert study.PROTOCOL_MD.read_text(encoding="utf-8") == study.render_protocol_md(protocol)
    expected_report = study.build_report(sha256(study.PROTOCOL_JSON))
    assert report == expected_report, "Theory Study 6 report differs from exact replay."
    assert study.REPORT_MD.read_text(encoding="utf-8") == study.render_report_md(report)

    contract = report["normalized_twenty_rule_contract"]
    assert len(contract) == 20
    assert tuple(item["rule_id"] for item in contract) == RULE_IDS
    assert len({item["full_rule_id"] for item in contract}) == 20
    assert all(item["rule"] and item["guardrail"] and item["source_artifact"] for item in contract)

    inputs = report["input_assessments"]
    decisions = report["decisions"]
    assert len(inputs) == len(decisions) == 5
    replayed = [score_assessment(item) for item in inputs]
    assert replayed == decisions
    by_id = {item["proposal_id"]: item for item in decisions}
    assert set(by_id) == {"C1", "C2", "C3", "C4", "C5"}
    assert {item["primary_stance"] for item in decisions} == {"REJECT", "NON_ACCEPT", "PURSUE", "PROVISIONAL_USE", "ACCEPT"}
    assert by_id["C1"]["primary_stance"] == "REJECT"
    assert by_id["C2"]["primary_stance"] == "NON_ACCEPT"
    assert by_id["C3"]["primary_stance"] == "PURSUE"
    assert by_id["C4"]["primary_stance"] == "PROVISIONAL_USE"
    assert by_id["C5"]["primary_stance"] == "ACCEPT"
    assert by_id["C3"]["decision_vector"]["accept"] is False
    assert by_id["C4"]["decision_vector"]["accept"] is False
    assert len(by_id["C5"]["independent_discriminating_evidence_groups"]) == 4
    assert all(set(item["rule_execution"]) == set(RULE_IDS) for item in decisions)
    assert all(item["no_aggregate_score"] is True for item in decisions)
    assert all("aggregate_score" not in item for item in decisions)

    mutations = report["mutation_tests"]
    assert len(mutations) == 8
    assert all(item["status"] == "PASS" for item in mutations)
    assert {item["test_id"] for item in mutations} == {f"M{index}" for index in range(1, 9)}
    diagnostics = report["diagnostics"]
    assert diagnostics["all_five_stances_reached"] is True
    assert diagnostics["all_expected_decisions_matched"] is True
    assert diagnostics["all_mutation_tests_passed"] is True
    assert diagnostics["all_twenty_rules_executed"] is True
    assert diagnostics["aggregate_score_emitted"] is False
    assert diagnostics["red_flags"] == []
    assert report["decision"] == "EXECUTABLE_PROTOCOL_SUCCESS_ALL_FIVE_STANCES_AND_ADVERSARIAL_GUARDS_PASS"
    assert report["method"]["llm_or_api_calls"] is False
    assert report["method"]["dataset_or_simulation_calls"] is False
    assert not credential_scan(), "Credential marker found outside .env."

    reproducibility["status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["validation"] = {
        "validator": str(Path(__file__).resolve()),
        "validator_sha256": sha256(Path(__file__).resolve()),
        "report_json_sha256": sha256(study.REPORT_JSON),
        "scorer_sha256": sha256(PROJECT_DIR / "meno_j_epistemic_scorer.py"),
    }
    study.atomic_json(study.REPRO_JSON, reproducibility)
    study.REPRO_MD.write_text(
        "# Meno-J Theory Study 6 Reproducibility\n\n"
        "- Status: **PASS_INDEPENDENT_EXACT_REPLAY**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset/simulation calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes'][study.PROTOCOL_JSON.name]}`\n"
        f"- Report SHA-256: `{reproducibility['output_hashes'][study.REPORT_JSON.name]}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n"
        f"- Scorer SHA-256: `{reproducibility['scorer_sha256']}`\n"
        f"- Validator SHA-256: `{reproducibility['validation']['validator_sha256']}`\n",
        encoding="utf-8",
    )

    checks = {
        "study_5_validated_prerequisite": True,
        "required_outputs_exist": True,
        "all_outputs_decode_as_utf8": True,
        "protocol_exact_replay": True,
        "report_exact_replay": True,
        "markdown_exact_render": True,
        "twenty_rules_normalized_in_order": True,
        "five_assessments_validate": True,
        "five_decisions_exact_replay": True,
        "all_five_stances_reached": True,
        "all_predeclared_decisions_match": True,
        "all_twenty_rules_execute_per_case": True,
        "eight_mutation_tests_pass": True,
        "hindsight_leak_fails_loudly": True,
        "duplicate_evidence_not_independent": True,
        "object_redefinition_gate_operational": True,
        "provisional_use_not_acceptance": True,
        "no_aggregate_score": True,
        "no_llm_dataset_or_simulation": True,
        "credential_scan": True,
    }
    validation = {
        "study_name": report["study_name"], "status": "PASS", "checks": checks,
        "check_count": len(checks), "red_flags": [], "blockers": [],
    }
    study.atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "# Meno-J Theory Study 6 Validation\n\n"
        "Status: **PASS**\n\n"
        "The executable twenty-rule contract reproduced exactly. All five epistemic stances were reached once, all five predeclared decisions matched, all twenty rules executed for every valid case, and all eight adversarial mutation tests passed. Hindsight leakage, duplicate evidence, unresolved object identity, and usefulness-to-truth laundering were blocked. No aggregate score, credentials, model calls, datasets, or simulations were used.\n",
        encoding="utf-8",
    )
    print("Meno-J Theory Study 6 executable scoring validation: PASS")


if __name__ == "__main__":
    main()
