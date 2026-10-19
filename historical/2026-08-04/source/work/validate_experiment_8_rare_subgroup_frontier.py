"""Independently validate and deterministically replay Meno-J Experiment 8."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from run_experiment_8_rare_subgroup_frontier import (  # noqa: E402
    JSON_OUTPUT,
    MARKDOWN_OUTPUT,
    REPRO_JSON_OUTPUT,
    REPRO_MARKDOWN_OUTPUT,
    SOURCE_PATH,
    build_report,
    build_reproducibility_summary,
    render_markdown,
    render_reproducibility_markdown,
    validate_report,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON: {path}") from exc
    assert isinstance(value, dict), f"Expected a JSON object: {path}"
    return value


def _credential_scan() -> list[str]:
    findings: list[str] = []
    credential_prefix = "sk-" + "or-v1-"
    candidates = [
        *PROJECT_DIR.glob("*.py"),
        *PROJECT_DIR.glob("*.md"),
        *PROJECT_DIR.glob("*.txt"),
        *PROJECT_DIR.joinpath("work").glob("*.py"),
        *PROJECT_DIR.joinpath("outputs").glob("*.json"),
        *PROJECT_DIR.joinpath("outputs").glob("*.md"),
        *PROJECT_DIR.joinpath("outputs").glob("*.txt"),
    ]
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="strict")
        if credential_prefix in text:
            findings.append(str(path.resolve()))
    return sorted(set(findings))


def main() -> None:
    required = (JSON_OUTPUT, MARKDOWN_OUTPUT, REPRO_JSON_OUTPUT, REPRO_MARKDOWN_OUTPUT)
    for path in required:
        assert path.exists(), f"Missing required Experiment 8 output: {path}"
        path.read_text(encoding="utf-8", errors="strict")

    saved_report = validate_report(_read_json(JSON_OUTPUT))
    assert saved_report["source_checkpoint"]["sha256"] == _sha256(SOURCE_PATH)

    replay_report = build_report()
    assert saved_report == replay_report, "Deterministic replay differs from saved JSON report."
    expected_json = json.dumps(replay_report, indent=2, ensure_ascii=False) + "\n"
    assert JSON_OUTPUT.read_text(encoding="utf-8") == expected_json
    assert MARKDOWN_OUTPUT.read_text(encoding="utf-8") == render_markdown(replay_report)

    credential_findings = _credential_scan()
    assert not credential_findings, "Credential-like OpenRouter tokens were found in project text files."

    summary = build_reproducibility_summary(replay_report)
    summary["validation_status"] = "PASSED_INDEPENDENT_DETERMINISTIC_REPLAY"
    summary["validation_results"] = {
        "all_required_outputs_exist": True,
        "utf8_decode_passed": True,
        "source_checkpoint_hash_matches": True,
        "complete_design_grid": True,
        "analytic_frontier_recomputed": True,
        "saved_report_equals_replay": True,
        "saved_markdown_equals_replay": True,
        "credential_scan_passed": True,
        "scientific_json_sha256": _sha256(JSON_OUTPUT),
        "scientific_markdown_sha256": _sha256(MARKDOWN_OUTPUT),
    }
    REPRO_JSON_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    reproducibility_markdown = render_reproducibility_markdown(summary) + "\n".join(
        [
            "## Independent validation",
            "",
            "- Status: PASSED",
            "- Complete deterministic replay: identical",
            "- Analytic frontier: recomputed",
            "- Source checkpoint hash: matched",
            "- UTF-8 decoding: passed",
            "- Credential scan: passed",
            f"- Scientific JSON SHA-256: `{summary['validation_results']['scientific_json_sha256']}`",
            f"- Scientific Markdown SHA-256: `{summary['validation_results']['scientific_markdown_sha256']}`",
            "",
        ]
    )
    REPRO_MARKDOWN_OUTPUT.write_text(reproducibility_markdown, encoding="utf-8")
    print("Experiment 8 validation: PASS")
    print("Deterministic replay: byte-identical scientific JSON and Markdown")
    print("Credential scan: PASS")


if __name__ == "__main__":
    main()
