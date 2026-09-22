"""Meno-J Experiment 17: repaired matched-compute study harness.

Preparation modes make no model-completion calls:

* ``--inspect-models`` reads OpenRouter's public model metadata only.
* ``--write-protocol`` freezes the separate Experiment 17 protocol.
* ``--preflight`` validates local configuration and the saved metadata.

``--run`` exists for a later, explicitly authorized scientific execution.  It
is not invoked by the Experiment 17 preparation workflow.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

import experiment_17_runtime as runtime
import run_experiment_16_matched_compute as e16


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "outputs"
WORK_DIR = PROJECT_DIR / "work"
EXPERIMENT_NAME = "Meno-J Experiment 17: Repaired Matched-Compute Architecture Falsification"
SLUG = "meno_j_experiment_17_matched_compute"
PROTOCOL_JSON = OUTPUT_DIR / "meno_j_experiment_17_preregistered_protocol.json"
PROTOCOL_MD = OUTPUT_DIR / "meno_j_experiment_17_preregistered_protocol.md"
CAPABILITY_JSON = OUTPUT_DIR / "meno_j_experiment_17_model_capability_snapshot.json"
CAPABILITY_MD = OUTPUT_DIR / "meno_j_experiment_17_model_capability_snapshot.md"
REAL_PATHS = {
    "checkpoints": WORK_DIR / "experiment_17_checkpoints",
    "report_json": OUTPUT_DIR / f"{SLUG}.json",
    "report_md": OUTPUT_DIR / f"{SLUG}.md",
    "raw_units": OUTPUT_DIR / f"{SLUG}_raw_units.jsonl",
    "raw_requests": OUTPUT_DIR / f"{SLUG}_raw_requests.jsonl",
    "judgments": OUTPUT_DIR / f"{SLUG}_judgments.jsonl",
    "aggregate_csv": OUTPUT_DIR / f"{SLUG}_aggregate.csv",
    "budget_csv": OUTPUT_DIR / f"{SLUG}_budget_accounting.csv",
    "repro_json": OUTPUT_DIR / "meno_j_experiment_17_reproducibility_summary.json",
    "repro_md": OUTPUT_DIR / "meno_j_experiment_17_reproducibility_summary.md",
}


def _replace_e16(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("Experiment 16", "Experiment 17").replace("E16|", "E17|")
    if isinstance(value, dict):
        return {key: _replace_e16(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_e16(item) for item in value]
    return value


PROTOCOL = _replace_e16(copy.deepcopy(e16.PROTOCOL))
PROTOCOL.update({
    "experiment_name": EXPERIMENT_NAME,
    "protocol_status": "FROZEN_AFTER_EXPERIMENT_16_RECOVERY_AUDIT_BEFORE_ANY_EXPERIMENT_17_COMPLETION_CALL",
    "frozen_on": "2026-09-20",
    "naming_note": (
        "Experiment 17 is a new preregistration following the inconclusive Experiment 16. "
        "Experiment 16's protocol, outputs, checkpoints, and raw responses remain historical and unchanged."
    ),
    "models": {
        "generator": runtime.RECOMMENDED_GENERATOR_MODEL,
        "blinded_judge": runtime.RECOMMENDED_JUDGE_MODEL,
        "separation_rule": "Generator and judge must be different model families and exact IDs are frozen before execution.",
        "capability_requirement": ["response_format", "structured_outputs"],
        "provider_routing": "provider.require_parameters=true; fail rather than route to an endpoint missing requested parameters",
    },
    "engineering_reliability_contract": {
        "transient_network_retries": (
            "At most four retries for timeout, IncompleteRead, remote disconnect/reset, URLError, and HTTP "
            "429/500/502/503/504; failed attempts remain in accounting."
        ),
        "invalid_response_shape": "One retry, recorded in the ledger and diagnostic archive.",
        "invalid_json": "Exactly one schema-constrained repair request; no further semantic repair loop.",
        "structured_output": "Every completion request carries a strict stage-specific JSON schema.",
        "resume": (
            "Ledger sequences continue from the maximum existing value. Judge state is checkpointed after every "
            "attempt, including terminal failure, so resume never creates extra judge opportunities."
        ),
        "serialization": "All Experiment 17 JSON uses UTF-8, allow_nan=false; non-finite statistics are represented as null.",
        "diagnostics": (
            "Response bodies, including partial/invalid bodies, are retained in a credential-free diagnostic archive. "
            "Request headers and credentials are never stored. Diagnostics are not scientific outcomes."
        ),
    },
    "changes_from_experiment_16": [
        "Changed generator and blinded-judge models because the Experiment 16 free endpoints did not advertise structured outputs.",
        "Added strict response_format/json_schema requests and provider capability enforcement.",
        "Added IncompleteRead and remote-disconnect retry coverage.",
        "Made ledger sequences unique across resumed processes.",
        "Made failed judge attempts durable and terminal after the preregistered two-attempt limit.",
        "Made all JSON serialization RFC-compliant and replaced non-finite values with null.",
        "Added sanitized response-body retention for reconstruction of parser and validator failures.",
        "No change to questions, arms, matched-compute tolerance, primary/secondary outcomes, analysis set, or falsification criterion.",
    ],
    "estimated_api_requirements": {
        "experimental_units": 9,
        "generator_endpoint_logical_calls_range": "approximately 63-198 before JSON-repair calls",
        "judge_endpoint_logical_calls_range": "approximately 9-36 including the one allowed invalid-output retry per batch",
        "token_planning_range": "approximately 1.6-2.2M experimental-arm tokens plus 0.3-0.6M judge tokens",
        "advertised_price_at_preregistration": "$0/M input and $0/M output for both recommended :free endpoints",
        "operational_warning": "Free-tier rate limits and availability are not guaranteed; preflight must pass immediately before a real run.",
    },
})
PROTOCOL["held_constant"]["underlying_model"] = (
    f"Exact frozen generator model {runtime.RECOMMENDED_GENERATOR_MODEL} for both arms."
)
PROTOCOL["held_constant"]["model_settings"] = (
    "temperature 0.4, max_tokens 12000, identical strict JSON schema per task type, identical retry policy for both arms"
)
PROTOCOL["evaluation"]["judge"] = (
    f"blinded LLM judge {runtime.RECOMMENDED_JUDGE_MODEL}; separate from generator family"
)
PROTOCOL["evaluation"]["judge_retry"] = (
    "one retry per judge batch on invalid output across the lifetime of the unit, including resumed processes; "
    "otherwise terminal JUDGE_FAILED"
)


def protocol_sha256() -> str:
    return hashlib.sha256(runtime.strict_json_dumps(PROTOCOL, sort_keys=True).encode("utf-8")).hexdigest()


def protocol_markdown() -> str:
    changes = "\n".join(f"- {item}" for item in PROTOCOL["changes_from_experiment_16"])
    requirements = "\n".join(f"- {key}: {value}" for key, value in PROTOCOL["estimated_api_requirements"].items())
    return f"""# {EXPERIMENT_NAME} — Preregistered Protocol

> Frozen before any Experiment 17 model-completion call. This is a new protocol; Experiment 16 remains unchanged.

## Central research question

{PROTOCOL['research_question']}

## Arms and matched-compute rule

- Arm A: historical Minos-J v4 multi-stage pipeline.
- Arm B: one-shot sampling plus one strict selector/verifier.
- Generator: `{runtime.RECOMMENDED_GENERATOR_MODEL}` for both arms.
- Blinded judge: `{runtime.RECOMMENDED_JUDGE_MODEL}`.
- Budget tolerance: `{PROTOCOL['matched_compute_rule']['tolerance']}`.
- Failed calls are included in attempt accounting; judge calls remain outside arm budgets.

## Changes from Experiment 16

{changes}

## Outcomes and falsification criterion

- Primary outcome: {PROTOCOL['metrics']['primary']}
- Analysis set: {PROTOCOL['falsification_criterion']['analysis_set']}
- Statistics: {PROTOCOL['falsification_criterion']['statistics']}
- Criterion: {PROTOCOL['falsification_criterion']['statement']}

## Engineering reliability contract

{chr(10).join(f'- {key}: {value}' for key, value in PROTOCOL['engineering_reliability_contract'].items())}

## Estimated API requirements

{requirements}

## Integrity

- Protocol SHA-256: `{protocol_sha256()}`
- Capability snapshot: `{CAPABILITY_JSON.name}`
"""


def write_protocol() -> None:
    if PROTOCOL_JSON.exists():
        existing = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
        if existing != PROTOCOL:
            raise SystemExit("Refusing to overwrite a different frozen Experiment 17 protocol.")
    else:
        runtime.atomic_write_json(PROTOCOL_JSON, PROTOCOL)
    PROTOCOL_MD.parent.mkdir(parents=True, exist_ok=True)
    PROTOCOL_MD.write_text(protocol_markdown(), encoding="utf-8")
    print(f"Experiment 17 protocol frozen: {PROTOCOL_JSON}")


def require_protocol() -> None:
    if not PROTOCOL_JSON.exists():
        raise SystemExit("Experiment 17 protocol is not frozen; run --write-protocol first.")
    if json.loads(PROTOCOL_JSON.read_text(encoding="utf-8")) != PROTOCOL:
        raise SystemExit("Experiment 17 protocol on disk differs from the runner; refusing to continue.")


def _fetch_json(url: str) -> dict[str, Any]:
    with request.urlopen(url, timeout=60) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Metadata endpoint returned {type(value).__name__}; expected object.")
    return value


def _model_summary(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": model["id"],
        "name": model.get("name"),
        "context_length": model.get("context_length"),
        "architecture": model.get("architecture"),
        "pricing": model.get("pricing"),
        "top_provider": model.get("top_provider"),
        "supported_parameters": model.get("supported_parameters", []),
        "expiration_date": model.get("expiration_date"),
    }


def inspect_models() -> dict[str, Any]:
    models = _fetch_json(runtime.OPENROUTER_MODELS_URL).get("data", [])
    by_id = {model.get("id"): model for model in models if isinstance(model, dict)}
    selected = {}
    for role, model_id in (
        ("generator", runtime.RECOMMENDED_GENERATOR_MODEL),
        ("blinded_judge", runtime.RECOMMENDED_JUDGE_MODEL),
    ):
        model = by_id.get(model_id)
        if model is None:
            raise RuntimeError(f"Recommended {role} model is absent from OpenRouter metadata: {model_id}")
        endpoint_url = f"{runtime.OPENROUTER_MODELS_URL}/{model_id}/endpoints"
        endpoints = _fetch_json(endpoint_url).get("data", {}).get("endpoints", [])
        selected[role] = {
            "model": _model_summary(model),
            "endpoint_url": endpoint_url,
            "endpoints": [
                {
                    "provider_name": endpoint.get("provider_name"),
                    "status": endpoint.get("status"),
                    "context_length": endpoint.get("context_length"),
                    "max_completion_tokens": endpoint.get("max_completion_tokens"),
                    "pricing": endpoint.get("pricing"),
                    "supported_parameters": endpoint.get("supported_parameters", []),
                    "uptime_last_30m": endpoint.get("uptime_last_30m"),
                    "uptime_last_1d": endpoint.get("uptime_last_1d"),
                }
                for endpoint in endpoints
            ],
        }
    required = {"response_format", "structured_outputs"}
    eligible_free = []
    for model in models:
        parameters = set(model.get("supported_parameters") or [])
        pricing = model.get("pricing") or {}
        top = model.get("top_provider") or {}
        if (
            required <= parameters
            and str(pricing.get("prompt")) == "0"
            and str(pricing.get("completion")) == "0"
            and int(top.get("max_completion_tokens") or 0) >= 12000
        ):
            eligible_free.append(_model_summary(model))
    snapshot = {
        "artifact": "Experiment 17 model capability metadata snapshot",
        "scientific_results": False,
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": runtime.OPENROUTER_MODELS_URL,
        "selection_criteria": {
            "required_supported_parameters": sorted(required),
            "minimum_max_completion_tokens": 12000,
            "generator_and_judge_must_differ": True,
            "prefer_advertised_zero_price": True,
        },
        "recommended": selected,
        "eligible_free_models": sorted(eligible_free, key=lambda item: item["id"]),
        "eligible_free_model_count": len(eligible_free),
    }
    for role, record in selected.items():
        model_params = set(record["model"]["supported_parameters"])
        qualifying_endpoints = [
            endpoint for endpoint in record["endpoints"]
            if required <= set(endpoint["supported_parameters"])
            and int(endpoint.get("max_completion_tokens") or 0) >= 12000
            and str((endpoint.get("pricing") or {}).get("prompt")) == "0"
            and str((endpoint.get("pricing") or {}).get("completion")) == "0"
            and endpoint.get("status") == 0
        ]
        if not required <= model_params or not qualifying_endpoints:
            raise RuntimeError(f"Recommended {role} does not advertise required structured-output capabilities.")
    runtime.atomic_write_json(CAPABILITY_JSON, snapshot)
    lines = [
        "# Experiment 17 Model Capability Snapshot",
        "",
        f"- Retrieved (UTC): {snapshot['fetched_at_utc']}",
        f"- Source: {snapshot['source']}",
        "- This is capability metadata only; no completion request was made.",
        "",
    ]
    for role, record in selected.items():
        model = record["model"]
        endpoint = record["endpoints"][0]
        lines += [
            f"## {role.replace('_', ' ').title()}",
            "",
            f"- Model: `{model['id']}`",
            f"- Model-level `response_format`: {'response_format' in model['supported_parameters']}",
            f"- Model-level `structured_outputs`: {'structured_outputs' in model['supported_parameters']}",
            f"- Endpoint provider: {endpoint['provider_name']}",
            f"- Endpoint-level `response_format`: {'response_format' in endpoint['supported_parameters']}",
            f"- Endpoint-level `structured_outputs`: {'structured_outputs' in endpoint['supported_parameters']}",
            f"- Context / max completion: {endpoint['context_length']} / {endpoint['max_completion_tokens']}",
            f"- Advertised prompt/completion price: {endpoint['pricing'].get('prompt')} / {endpoint['pricing'].get('completion')}",
            "",
        ]
    CAPABILITY_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Capability snapshot written: {CAPABILITY_JSON}")
    return snapshot


def load_dotenv_without_overwrite(path: Path) -> list[str]:
    return e16.load_dotenv(path)


def preflight(*, refresh_metadata: bool = True) -> None:
    require_protocol()
    if refresh_metadata:
        # Public metadata only. This does not submit a prompt or spend model
        # tokens, and it prevents stale capability claims at execution time.
        inspect_models()
    if not CAPABILITY_JSON.exists():
        raise SystemExit("Capability snapshot missing; run --inspect-models first.")
    snapshot = json.loads(CAPABILITY_JSON.read_text(encoding="utf-8"))
    problems = []
    required = {"response_format", "structured_outputs"}
    for role in ("generator", "blinded_judge"):
        record = snapshot.get("recommended", {}).get(role, {})
        model_params = set(record.get("model", {}).get("supported_parameters", []))
        qualifying_endpoints = [
            item for item in record.get("endpoints", [])
            if required <= set(item.get("supported_parameters", []))
            and int(item.get("max_completion_tokens") or 0) >= 12000
            and str((item.get("pricing") or {}).get("prompt")) == "0"
            and str((item.get("pricing") or {}).get("completion")) == "0"
            and item.get("status") == 0
        ]
        if not required <= model_params or not qualifying_endpoints:
            problems.append(f"{role} capability snapshot no longer satisfies the structured-output contract")
    loaded = load_dotenv_without_overwrite(PROJECT_DIR / ".env")
    generator = os.environ.get("OPENROUTER_MODEL", "")
    judge = os.environ.get("MINOS_J_JUDGE_MODEL", "")
    if not os.environ.get("OPENROUTER_API_KEY"):
        problems.append("OPENROUTER_API_KEY missing")
    if generator != runtime.RECOMMENDED_GENERATOR_MODEL:
        problems.append(f"OPENROUTER_MODEL must equal frozen Experiment 17 generator {runtime.RECOMMENDED_GENERATOR_MODEL}")
    if judge != runtime.RECOMMENDED_JUDGE_MODEL:
        problems.append(f"MINOS_J_JUDGE_MODEL must equal frozen Experiment 17 judge {runtime.RECOMMENDED_JUDGE_MODEL}")
    if generator and generator == judge:
        problems.append("generator and judge model must differ")
    print(f".env variables loaded: {', '.join(sorted(loaded)) or 'none'}")
    print(f"Generator model: {generator or '(unset)'}")
    print(f"Judge model: {judge or '(unset)'}")
    print("PREFLIGHT OK" if not problems else "PREFLIGHT FAILED: " + "; ".join(problems))
    if problems:
        raise SystemExit(1)


def _install_protocol_globals() -> None:
    runtime.install_experiment_17_core_hooks()
    e16.EXPERIMENT_16_NAME = EXPERIMENT_NAME
    e16.PROTOCOL = PROTOCOL
    e16.PROTOCOL_JSON = PROTOCOL_JSON
    e16.PROTOCOL_MD = PROTOCOL_MD


def _write_outputs(report: dict[str, Any], units: list[dict[str, Any]], ledger_path: Path) -> None:
    # The historical writer is reused only after normalization.  Its path guard
    # is narrowed to Experiments 1-16 so Experiment 17 cannot touch them.
    original_guard = e16.HISTORICAL_OUTPUT_PATTERN
    e16.HISTORICAL_OUTPUT_PATTERN = re.compile(
        r"meno_j_(experiment_(?:[1-9]|1[0-6])(?:_|$)|theory_study|wesad|literature|complete|falsification)"
    )
    try:
        e16.write_outputs(
            REAL_PATHS,
            runtime.strict_json_ready(report),
            runtime.strict_json_ready(units),
            ledger_path,
        )
    finally:
        e16.HISTORICAL_OUTPUT_PATTERN = original_guard
    repro = json.loads(REAL_PATHS["repro_json"].read_text(encoding="utf-8"))
    repro.update({
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_sha256": hashlib.sha256((PROJECT_DIR / "experiment_17_runtime.py").read_bytes()).hexdigest(),
        "capability_snapshot_sha256": hashlib.sha256(CAPABILITY_JSON.read_bytes()).hexdigest(),
        "historical_experiment_16_modified": False,
    })
    runtime.atomic_write_json(REAL_PATHS["repro_json"], repro)


def run_real(argv: list[str]) -> dict[str, Any]:
    """Execute the frozen E17 design. Not called during preparation."""
    preflight()
    _install_protocol_globals()
    import pipeline
    import prompts
    import schema

    api_key = os.environ["OPENROUTER_API_KEY"]
    generator = os.environ["OPENROUTER_MODEL"]
    judge = os.environ["MINOS_J_JUDGE_MODEL"]
    client = runtime.StructuredOpenRouterClient(
        api_key,
        generator,
        REAL_PATHS["checkpoints"] / "diagnostic_responses",
    )
    engine = (client, pipeline, prompts, schema)
    ledger_path = REAL_PATHS["checkpoints"] / "request_ledger.jsonl"
    meter = runtime.ResumeSafeMeter(client, ledger_path)
    units = []
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        for replicate in range(1, PROTOCOL["task_set"]["replicates_per_question"] + 1):
            for question_id in e16.QUESTIONS:
                print(f"[E17] unit {question_id}-r{replicate}", flush=True)
                units.append(e16.run_unit(engine, meter, REAL_PATHS, question_id, replicate, generator, judge))
    finally:
        meter.uninstall()
    command = "python " + " ".join([Path(__file__).name, *argv])
    report = e16.build_report(units, "real", generator, judge, [command], started)
    report.update({
        "experiment_name": EXPERIMENT_NAME,
        "provenance": (
            "Generated by the separately preregistered Experiment 17 repaired harness. "
            "Experiment 16 and Experiments 1-15 were not overwritten."
        ),
        "engineering_repairs": PROTOCOL["engineering_reliability_contract"],
        "protocol_deviation": None,
    })
    _write_outputs(report, units, ledger_path)
    return report


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=EXPERIMENT_NAME)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--inspect-models", action="store_true", help="metadata only; no model completion")
    group.add_argument("--write-protocol", action="store_true")
    group.add_argument("--preflight", action="store_true", help="local checks only; no model completion")
    group.add_argument("--run", action="store_true", help="future real run; not part of preparation")
    args = parser.parse_args(argv)
    if args.inspect_models:
        inspect_models()
    elif args.write_protocol:
        write_protocol()
    elif args.preflight:
        preflight()
    else:
        require_protocol()
        run_real(argv)


if __name__ == "__main__":
    main()
