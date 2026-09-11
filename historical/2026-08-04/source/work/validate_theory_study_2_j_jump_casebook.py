"""Independently validate and replay Meno-J historical J-jump Casebook 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import run_theory_study_2_j_jump_casebook as study  # noqa: E402


OUTPUT_DIR = PROJECT_DIR / "outputs"
VALIDATION_JSON = OUTPUT_DIR / "meno_j_theory_study_2_validation.json"
VALIDATION_MD = OUTPUT_DIR / "meno_j_theory_study_2_validation.md"


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
        study.STUDY1_REPORT,
        study.STUDY1_VALIDATION,
        study.PROTOCOL_JSON,
        study.PROTOCOL_MD,
        study.REPORT_JSON,
        study.REPORT_MD,
        study.AMENDMENT_JSON,
        study.AMENDMENT_MD,
        study.REPRO_JSON,
        study.REPRO_MD,
    ]
    for path in required:
        assert path.is_file(), f"Missing required artifact: {path}"
        path.read_text(encoding="utf-8")

    study1_validation = read_json(study.STUDY1_VALIDATION)
    assert study1_validation["status"] == "PASS"
    protocol = read_json(study.PROTOCOL_JSON)
    report = read_json(study.REPORT_JSON)
    amendment = read_json(study.AMENDMENT_JSON)
    reproducibility = read_json(study.REPRO_JSON)

    assert protocol == study.protocol()
    assert study.PROTOCOL_MD.read_text(encoding="utf-8") == study.render_protocol_md(protocol)
    expected = study.report(sha256(study.PROTOCOL_JSON), sha256(study.STUDY1_REPORT))
    assert report == expected, "Historical casebook differs from deterministic replay."
    assert study.REPORT_MD.read_text(encoding="utf-8") == study.render_report_md(report)
    assert amendment == report["contract_amendment"] == study.amendments()
    assert study.AMENDMENT_MD.read_text(encoding="utf-8") == study.render_amendment_md(amendment)

    source_ids = {source["source_id"] for source in report["sources"]}
    assert len(source_ids) == 11
    assert len({source["url"] for source in report["sources"]}) == 11
    assert sum("primary" in source["source_type"] for source in report["sources"]) >= 4
    for source in report["sources"]:
        assert source["url"].startswith("https://")
        assert source["supports"] and source["access_depth"]
    for model in report["historical_models"]:
        assert set(model["sources"]) <= source_ids
    for transition in report["transitions"]:
        assert len(transition["criteria"]) == 6
        for criterion in transition["criteria"].values():
            assert set(criterion["sources"]) <= source_ids
    for item in amendment["amendments"]:
        assert set(item["sources"]) <= source_ids

    assert len(report["historical_models"]) == 3
    assert len(report["transitions"]) == 2
    assert len(report["false_jump_and_boundary_controls"]) == 6
    assert len(amendment["amendments"]) == 5
    assert report["results"]["original_contract_survived_unchanged"] is False
    assert report["results"]["ptolemy_to_kepler"] == "SURVIVING_COMPONENT_LEVEL_REPRESENTATIONAL_J_JUMP"
    assert report["results"]["kepler_magnetic_mechanism"] == "REJECTED_CAUSAL_SUBMODULE"
    assert report["results"]["kepler_to_newton"] == "SURVIVING_DYNAMICAL_J_JUMP"
    assert report["decision"] == "CASEBOOK_1_SUCCESS_CONTRACT_AMENDED"
    assert report["method"]["llm_or_api_calls"] is False
    assert report["method"]["dataset_calls"] is False
    assert "component" in amendment["revised_survival_rule"]["verdict_scope"].lower()
    assert not credential_scan(), "Credential marker found outside .env."

    reproducibility["status"] = "PASS_INDEPENDENT_EXACT_REPLAY"
    reproducibility["validation"] = {
        "validator": str(Path(__file__).resolve()),
        "validator_sha256": sha256(Path(__file__).resolve()),
        "report_json_sha256": sha256(study.REPORT_JSON),
        "amendment_json_sha256": sha256(study.AMENDMENT_JSON),
    }
    study._atomic_json(study.REPRO_JSON, reproducibility)
    study.REPRO_MD.write_text(
        "# Meno-J Theory Study 2 Reproducibility\n\n"
        "- Status: **PASS_INDEPENDENT_EXACT_REPLAY**\n"
        "- OpenRouter/LLM calls: **none**\n"
        "- Dataset calls: **none**\n"
        "- Encoding: **UTF-8**\n"
        f"- Protocol SHA-256: `{reproducibility['input_hashes']['protocol']}`\n"
        f"- Theory Study 1 SHA-256: `{reproducibility['input_hashes']['theory_study_1']}`\n"
        f"- Report JSON SHA-256: `{reproducibility['output_hashes']['report_json']}`\n"
        f"- Runner SHA-256: `{reproducibility['runner_sha256']}`\n"
        f"- Validator SHA-256: `{reproducibility['validation']['validator_sha256']}`\n",
        encoding="utf-8",
    )

    validation = {
        "study_name": report["study_name"],
        "status": "PASS",
        "checks": {
            "theory_study_1_validated_prerequisite": True,
            "required_outputs_exist": True,
            "all_outputs_decode_as_utf8": True,
            "protocol_exact_replay": True,
            "report_exact_replay": True,
            "markdown_exact_render": True,
            "citation_ids_resolve": True,
            "access_limits_disclosed": True,
            "primary_source_floor_met": True,
            "component_scoped_transition_verdicts": True,
            "six_false_jump_and_boundary_controls": True,
            "original_contract_failure_disclosed": True,
            "five_contract_amendments_complete": True,
            "no_llm_or_dataset_calls": True,
            "credential_scan": True,
        },
        "red_flags": [],
        "blockers": [],
    }
    study._atomic_json(VALIDATION_JSON, validation)
    VALIDATION_MD.write_text(
        "# Meno-J Theory Study 2 Validation\n\n"
        "Status: **PASS**\n\n"
        "The historical casebook and contract amendment reproduced exactly. All citation IDs resolve, access limits are explicit, both transitions have six-criterion component-scoped verdicts, six controls were adjudicated, and the original retention-rule failure was preserved rather than hidden. No credentials, model calls, or datasets were used.\n",
        encoding="utf-8",
    )
    print("Meno-J Theory Study 2 historical casebook validation: PASS")


if __name__ == "__main__":
    main()
