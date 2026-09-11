"""Validate and exactly replay Meno-J Theory Study 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_theory_study_1_explanation_quality as study  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_theory_study_1_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_theory_study_1_validation.md"


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
        study.PROTOCOL_JSON,
        study.PROTOCOL_MD,
        study.REPORT_JSON,
        study.REPORT_MD,
        study.REPRO_JSON,
        study.REPRO_MD,
    ]
    for path in required:
        assert path.is_file(), f"Missing output: {path}"
        path.read_text(encoding="utf-8")

    protocol = read_json(study.PROTOCOL_JSON)
    report = read_json(study.REPORT_JSON)
    reproducibility = read_json(study.REPRO_JSON)

    assert protocol == study.protocol(), "Protocol is not an exact deterministic build."
    assert study.PROTOCOL_MD.read_text(encoding="utf-8") == study.render_protocol_md(protocol)
    expected = study.report(sha256(study.PROTOCOL_JSON))
    assert report == expected, "Scientific report is not an exact deterministic build."
    assert study.REPORT_MD.read_text(encoding="utf-8") == study.render_report_md(report)

    assert len(report["sources"]) == 13
    assert len(report["theory_matrix"]) == 8
    assert len(report["stress_tests"]) == 10
    assert all(case["status"].startswith("HANDLED") for case in report["stress_tests"])
    source_ids = {source["source_id"] for source in report["sources"]}
    assert len(source_ids) == 13
    assert len({source["url"] for source in report["sources"]}) == 13
    assert sum(source["access_depth"] == "full_text_argument_review" for source in report["sources"]) >= 8
    for source in report["sources"]:
        assert source["url"].startswith("https://")
        assert source["contribution"] and source["pressure_point"]
    for theory in report["theory_matrix"]:
        assert set(theory["sources"]) <= source_ids
    for finding in report["result"]["central_findings"]:
        assert set(finding["sources"]) <= source_ids

    assert report["failed_initial_candidate"]["decision"] == "REJECT_AS_UNIVERSAL_THEORY"
    assert report["decision"] == "THEORY_STAGE_1_SUCCESS_WITH_NARROWED_CLAIM"
    assert report["result"]["architecture_status"] == "DEFENSIBLE_CONSTRAINED_PLURALIST_SYNTHESIS"
    assert "empirical validation" in report["result"]["not_claimed"]
    assert "philosophical priority or novelty" in report["result"]["not_claimed"]
    assert len(report["contract"]["ordered_gates"]) == 6
    assert len(report["contract"]["relation_type_routes"]) == 6
    assert len(report["j_jump"]["criteria"]) == 6
    assert "J1" in report["j_jump"]["decision_rule"]
    assert "J2-J6" in report["j_jump"]["decision_rule"]
    assert report["method"]["llm_or_api_calls"] is False
    assert report["method"]["dataset_calls"] is False
    assert not credential_scan(), "Credential marker found outside .env."

    reproducibility["status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["validation"] = {
        "validator": str(Path(__file__).resolve()),
        "validator_sha256": sha256(Path(__file__).resolve()),
        "report_json_sha256": sha256(study.REPORT_JSON),
        "report_markdown_sha256": sha256(study.REPORT_MD),
    }
    study._atomic_json(study.REPRO_JSON, reproducibility)
    study.REPRO_MD.write_text(
        "# Meno-J Theory Study 1 Reproducibility\n\n"
        "- Status: **PASS_INDEPENDENT_EXACT_REPLAY**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['inputs']['protocol_sha256']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['outputs']['report_json_sha256']}`\n"
        f"- Report Markdown SHA-256: `{reproducibility['outputs']['report_markdown_sha256']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n"
        f"- Validator SHA-256: `{reproducibility['validation']['validator_sha256']}`\n",
        encoding="utf-8",
    )

    validation = {
        "study_name": report["study_name"],
        "status": "PASS",
        "checks": {
            "required_outputs_exist": True,
            "all_outputs_decode_as_utf8": True,
            "protocol_exact_replay": True,
            "report_exact_replay": True,
            "markdown_exact_render": True,
            "eight_theory_families": True,
            "ten_adversarial_cases": True,
            "all_adversarial_cases_handled": True,
            "source_references_resolve": True,
            "access_depths_disclosed": True,
            "universal_counterfactual_candidate_rejected": True,
            "non_empirical_scope_disclosed": True,
            "j_jump_contract_complete": True,
            "no_llm_or_dataset_calls": True,
            "credential_scan": True,
        },
        "red_flags": [],
        "blockers": [],
    }
    study._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "# Meno-J Theory Study 1 Validation\n\n"
        "Status: **PASS**\n\n"
        "The protocol and scientific report reproduced exactly. All eight theory families, ten adversarial cases, source references, scope disclosures, six contract gates, six relation routes, and six J-jump criteria passed validation. No credentials, model calls, or dataset calls were used.\n",
        encoding="utf-8",
    )
    print("Meno-J Theory Study 1 validation: PASS")


if __name__ == "__main__":
    main()
