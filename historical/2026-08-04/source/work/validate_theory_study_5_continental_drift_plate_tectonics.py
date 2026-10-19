"""Independently replay and validate Meno-J Theory Study 5."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_theory_study_5_continental_drift_plate_tectonics as study  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_theory_study_5_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_theory_study_5_validation.md"


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
        study.STUDY4_REPORT, study.STUDY4_EXTENSION, study.STUDY4_VALIDATION,
        study.PROTOCOL_JSON, study.PROTOCOL_MD, study.REPORT_JSON, study.REPORT_MD,
        study.EXTENSION_JSON, study.EXTENSION_MD, study.REPRO_JSON, study.REPRO_MD,
    ]
    for path in required:
        assert path.is_file(), f"Missing required artifact: {path}"
        path.read_text(encoding="utf-8")

    assert read_json(study.STUDY4_VALIDATION)["status"] == "PASS"
    protocol = read_json(study.PROTOCOL_JSON)
    report = read_json(study.REPORT_JSON)
    extension = read_json(study.EXTENSION_JSON)
    reproducibility = read_json(study.REPRO_JSON)

    assert protocol == study.protocol()
    assert study.PROTOCOL_MD.read_text(encoding="utf-8") == study.render_protocol_md(protocol)
    expected = study.report(
        sha256(study.PROTOCOL_JSON),
        sha256(study.STUDY4_REPORT),
        sha256(study.STUDY4_EXTENSION),
    )
    assert report == expected, "Theory Study 5 differs from deterministic replay."
    assert study.REPORT_MD.read_text(encoding="utf-8") == study.render_report_md(report)
    assert extension == report["contract_extension"] == study.extension()
    assert study.EXTENSION_MD.read_text(encoding="utf-8") == study.render_extension_md(extension)

    sources = report["sources"]
    source_ids = {source["source_id"] for source in sources}
    assert len(sources) == len(source_ids) == 20
    assert len({source["url"] for source in sources}) == 20
    assert sum("primary" in source["source_type"] for source in sources) >= 14
    for source in sources:
        assert source["url"].startswith("https://")
        assert source["supports"] and source["access_depth"]
    for node in report["lineage_nodes"]:
        assert set(node["sources"]) <= source_ids
    for edge in report["transition_edges"]:
        assert len(edge["criteria"]) == 6
        for criterion in edge["criteria"].values():
            assert set(criterion["sources"]) <= source_ids
    for item in extension["extensions"]:
        assert set(item["sources"]) <= source_ids

    assert len(report["lineage_nodes"]) == 8
    assert len(report["transition_edges"]) == 6
    assert len(report["false_jump_controls"]) == 11
    assert len(report["prior_contract_rule_tests"]) == 15
    assert all(item["status"].startswith("PASS") for item in report["prior_contract_rule_tests"])
    assert len(extension["extensions"]) == 5
    assert {item["extension_id"] for item in extension["extensions"]} == {
        "A16_HINDSIGHT_FIREWALL",
        "A17_EPISTEMIC_STANCE_LADDER",
        "A18_OBJECT_REDEFINITION_TEST",
        "A19_INDEPENDENT_PREDICTION_LEDGER",
        "A20_OBSERVABILITY_FRONTIER",
    }

    results = report["results"]
    assert results["wegener_contemporaneous_pursuit_verdict"] == "WORTHY_OF_PURSUIT"
    assert results["wegener_contemporaneous_acceptance_verdict"] == "NOT_YET_ACCEPTANCE_READY"
    assert results["plate_tectonics_relation_to_wegener"] == "SELECTIVE_RETENTION_PLUS_OBJECT_REDEFINITION_NOT_SIMPLE_VINDICATION"
    assert results["prior_contract_generalized"] is True
    assert results["prior_contract_sufficient_unchanged"] is False
    assert results["full_transition_verdict"] == "SURVIVING_HINDSIGHT_CONTROLLED_DISTRIBUTED_J_JUMP"
    assert report["decision"] == "CASEBOOK_4_SUCCESS_PURSUIT_ACCEPTANCE_SPLIT_AND_OBJECT_REDEFINITION_ADDED"
    assert report["method"]["llm_or_api_calls"] is False
    assert report["method"]["dataset_or_simulation_calls"] is False
    markdown = study.REPORT_MD.read_text(encoding="utf-8")
    assert "worthy of pursuit but not yet ready for acceptance" in markdown
    assert "redefined the moving object" in markdown
    assert not credential_scan(), "Credential marker found outside .env."

    reproducibility["status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["validation"] = {
        "validator": str(Path(__file__).resolve()),
        "validator_sha256": sha256(Path(__file__).resolve()),
        "report_json_sha256": sha256(study.REPORT_JSON),
        "extension_json_sha256": sha256(study.EXTENSION_JSON),
    }
    study._atomic_json(study.REPRO_JSON, reproducibility)
    study.REPRO_MD.write_text(
        "# Meno-J Theory Study 5 Reproducibility\n\n"
        "- Status: **PASS_INDEPENDENT_EXACT_REPLAY**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset/simulation calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n"
        f"- Study 4 report SHA-256: `{reproducibility['input_hashes']['study_4_report']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n"
        f"- Validator SHA-256: `{reproducibility['validation']['validator_sha256']}`\n",
        encoding="utf-8",
    )

    validation = {
        "study_name": report["study_name"],
        "status": "PASS",
        "checks": {
            "study_4_validated_prerequisite": True,
            "required_outputs_exist": True,
            "all_outputs_decode_as_utf8": True,
            "protocol_exact_replay": True,
            "report_exact_replay": True,
            "markdown_exact_render": True,
            "twenty_unique_source_records": True,
            "fourteen_primary_source_floor_met": True,
            "citation_ids_resolve": True,
            "eight_lineage_nodes": True,
            "six_six_criterion_transition_edges": True,
            "eleven_false_jump_controls": True,
            "fifteen_prior_contract_rules_tested": True,
            "five_contract_extensions_complete": True,
            "pursuit_acceptance_split_explicit": True,
            "object_redefinition_explicit": True,
            "no_llm_dataset_or_simulation": True,
            "credential_scan": True,
        },
        "red_flags": [],
        "blockers": [],
    }
    study._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "# Meno-J Theory Study 5 Validation\n\n"
        "Status: **PASS**\n\n"
        "The hindsight-controlled continental-drift/plate-tectonics casebook reproduced exactly. Twenty unique source records, eight lineage nodes, six six-criterion transitions, eleven false-jump controls, fifteen prior-rule tests, and five new extensions passed. The pursuit/acceptance split and object redefinition are explicit; citation IDs and access limits resolve; no credentials, model calls, datasets, or simulations were used.\n",
        encoding="utf-8",
    )
    print("Meno-J Theory Study 5 continental-drift/plate-tectonics validation: PASS")


if __name__ == "__main__":
    main()
