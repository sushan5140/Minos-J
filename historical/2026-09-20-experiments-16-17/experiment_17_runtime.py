"""Reliability runtime for Meno-J Experiment 17.

This module is deliberately separate from Experiment 16.  It supplies the
engineering repairs identified by the Experiment 16 recovery audit without
modifying any historical runner, checkpoint, protocol, or output.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import math
import os
import re
import socket
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


PROJECT_DIR = Path(__file__).resolve().parent
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
SYSTEM_MESSAGE = (
    "You are a strict research pipeline component. Return valid JSON only. "
    "No markdown, no commentary."
)
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_NETWORK_RETRIES = 4
DEFAULT_MAX_SHAPE_RETRIES = 1
RECOMMENDED_GENERATOR_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
RECOMMENDED_JUDGE_MODEL = "nex-agi/nex-n2.5-pro:free"

_SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"']+"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s\"']+"),
)


def _redact_text(value: str, api_key: str | None = None) -> str:
    text = value.replace(api_key, "<redacted>") if api_key else value
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "<redacted>", text)
    return text


def strict_json_ready(value: Any) -> Any:
    """Return a JSON-safe value, mapping non-finite floats to JSON null."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings.")
        return {key: strict_json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_json_ready(item) for item in value]
    raise TypeError(f"Unsupported JSON value type: {type(value).__name__}")


def strict_json_dumps(value: Any, *, indent: int | None = None, sort_keys: bool = False) -> str:
    return json.dumps(
        strict_json_ready(value),
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
        sort_keys=sort_keys,
    )


def atomic_write_json(path: Path, value: Any) -> None:
    """Atomically write standards-compliant UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(strict_json_dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(strict_json_dumps(value, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class DiagnosticArchive:
    """Credential-free response archive for post-failure reconstruction.

    Request headers and API keys are never accepted by this interface.  Both
    valid and invalid response bodies are retained so a later schema failure
    can be reconstructed even though it occurs outside the HTTP client.
    """

    def __init__(self, directory: Path, api_key: str | None = None):
        self.directory = directory
        self.api_key = api_key
        self.directory.mkdir(parents=True, exist_ok=True)
        existing = []
        for path in self.directory.glob("response_*.json"):
            match = re.fullmatch(r"response_(\d+)\.json", path.name)
            if match:
                existing.append(int(match.group(1)))
        self._counter = max(existing, default=0)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, str):
            return _redact_text(value, self.api_key)
        if isinstance(value, dict):
            return {str(key): self._sanitize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize(item) for item in value]
        return strict_json_ready(value)

    def capture(self, classification: str, *, body: bytes | str | None = None, **metadata: Any) -> Path:
        self._counter += 1
        record: dict[str, Any] = {
            "archive_sequence": self._counter,
            "classification": classification,
            "captured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": self._sanitize(metadata),
        }
        if body is not None:
            raw = body.encode("utf-8") if isinstance(body, str) else body
            record["body_sha256"] = hashlib.sha256(raw).hexdigest()
            record["body_bytes"] = len(raw)
            try:
                record["body_encoding"] = "utf-8"
                record["body"] = self._sanitize(raw.decode("utf-8"))
            except UnicodeDecodeError:
                record["body_encoding"] = "base64"
                record["body"] = base64.b64encode(raw).decode("ascii")
        path = self.directory / f"response_{self._counter:08d}.json"
        atomic_write_json(path, record)
        return path


def _string_schema(*, enum: list[str] | None = None, const: str | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    if enum is not None:
        schema["enum"] = enum
    elif const is not None:
        schema["const"] = const
    else:
        schema["minLength"] = 1
    return schema


def _array_schema(item: dict[str, Any], *, minimum: int = 1, maximum: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "array", "items": item, "minItems": minimum}
    if maximum is not None:
        result["maxItems"] = maximum
    return result


def _object_schema(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _root_array(key: str, item: dict[str, Any], minimum: int, maximum: int) -> dict[str, Any]:
    return _object_schema({key: _array_schema(item, minimum=minimum, maximum=maximum)})


def _prompt_ids(prompt: str) -> list[str]:
    return sorted(set(re.findall(r'"hypothesis_id"\s*:\s*"(H\d+)"', prompt)), key=lambda x: int(x[1:]))


def response_schema_for_prompt(prompt: str) -> tuple[str, dict[str, Any]]:
    """Return the strict OpenRouter JSON schema for one Experiment 17 prompt."""
    import run_experiment_16_matched_compute as e16
    import schema as schema_module

    head = prompt.lstrip().splitlines()[0]
    nonempty_strings = _array_schema(_string_schema(), minimum=1)
    hypothesis = _object_schema({
        "hypothesis_id": _string_schema(),
        "hypothesis": _string_schema(),
        "proposed_mechanism": _string_schema(),
        "core_assumption": _string_schema(),
        "knowledge_gap_addressed": _string_schema(),
        "status": _string_schema(const="SPECULATIVE"),
    })
    mechanism = _object_schema({
        "hypothesis_id": _string_schema(),
        "mechanism_variables": nonempty_strings,
        "causal_path": _string_schema(),
        "expected_direction": _string_schema(),
        "domain_specific_boundary_conditions": nonempty_strings,
        "measurable_outcomes": nonempty_strings,
        "mechanism_builder_notes": _string_schema(),
    })
    confounder = _object_schema({
        "hypothesis_id": _string_schema(),
        "possible_confounders": nonempty_strings,
        "control_variables": nonempty_strings,
        "boring_rival_explanations": nonempty_strings,
        "rival_prediction": _string_schema(),
        "distinguishing_condition": _string_schema(),
        "confounder_rival_notes": _string_schema(),
    })
    statistical = _object_schema({
        "hypothesis_id": _string_schema(),
        "effect_size_expectation": _string_schema(enum=["small", "medium", "large", "unknown"]),
        "effect_size_rationale": _string_schema(),
        "minimum_data_needed": nonempty_strings,
        "testable_prediction": _string_schema(),
        "failure_condition": _string_schema(),
        "statistical_test_plan": _string_schema(),
        "statistical_testability_notes": _string_schema(),
    })
    audit_properties: dict[str, Any] = {
        "hypothesis_id": _string_schema(),
        "audit_decision": _string_schema(enum=["PASS", "REJECT", "SALVAGEABLE"]),
    }
    audit_properties.update({field: {"type": "boolean"} for field in schema_module.AUDIT_BOOLEAN_FIELDS})
    audit_properties.update({
        "failure_points": _array_schema(
            _string_schema(enum=list(schema_module.AUDIT_BOOLEAN_FIELDS)), minimum=0, maximum=len(schema_module.AUDIT_BOOLEAN_FIELDS)
        ),
        "decision_reason": _string_schema(),
        "salvage_note": {"type": "string"},
    })
    audit = _object_schema(audit_properties)
    rival = _object_schema({field: _string_schema() for field in schema_module.RIVAL_FIELDS})
    falsification = _object_schema({field: _string_schema() for field in schema_module.FALSIFICATION_FIELDS})

    if head.startswith("Stage 4 —") or head.startswith("Stage 4 "):
        return "stage_4_hypotheses", _root_array("hypotheses", hypothesis, 10, 10)
    if head.startswith("Stage 4.1"):
        return "stage_4_1_mechanism_builds", _root_array("mechanism_builds", mechanism, 1, 10)
    if head.startswith("Stage 4.2"):
        return "stage_4_2_confounder_rival_builds", _root_array("confounder_rival_builds", confounder, 1, 10)
    if head.startswith("Stage 4.3"):
        return "stage_4_3_statistical_testability", _root_array(
            "statistical_testability_builds", statistical, 1, 10
        )
    if head.startswith("Stage 5"):
        return "stage_5_audits", _root_array("audits", audit, 10, 10)
    if head.startswith("Stage 6"):
        return "stage_6_rival_matrix", _root_array("rival_prediction_matrix", rival, 1, 10)
    if head.startswith("Stage 7"):
        return "stage_7_falsification", _root_array("falsification_tests", falsification, 1, 10)
    if head.startswith("One-shot Hypothesis Contract Generation"):
        card_props: dict[str, Any] = {"hypothesis_id": _string_schema()}
        for field in e16.CARD_FIELDS:
            if field in e16.CARD_LIST_FIELDS:
                card_props[field] = nonempty_strings
            elif field == "effect_size_expectation":
                card_props[field] = _string_schema(enum=sorted(e16.EFFECT_SIZES))
            else:
                card_props[field] = _string_schema()
        return "baseline_sample", _root_array("hypotheses", _object_schema(card_props), 10, 10)
    if head.startswith("Selection and Strict Audit Pass"):
        match = re.search(r"Select exactly (\d+)", prompt)
        expected = int(match.group(1)) if match else 10
        selector_props = dict(audit_properties)
        selector_props.pop("hypothesis_id")
        selector_props = {"candidate_id": _string_schema(), **selector_props}
        return "selector_audits", _root_array("selected_audits", _object_schema(selector_props), expected, expected)
    if head.startswith("Independent Blind Review"):
        card_ids = sorted(
            set(re.findall(r'"card_id"\s*:\s*"(C[0-9a-fA-F]{8})"', prompt)) - {"C00000000"}
        )
        judge_props: dict[str, Any] = {"card_id": _string_schema()}
        judge_props.update({field: {"type": "boolean"} for field in schema_module.AUDIT_BOOLEAN_FIELDS})
        judge_props.update({field: {"type": "boolean"} for field in e16.JUDGE_EXTRA_FIELDS})
        judge_props["judge_reason"] = _string_schema()
        expected = len(card_ids)
        return "blinded_judgments", _root_array("judgments", _object_schema(judge_props), expected, expected)
    raise ValueError(f"No Experiment 17 structured-output schema for prompt head: {head!r}")


class StructuredOpenRouterClient:
    """OpenRouter client with strict schemas, reconstructable diagnostics and retries."""

    def __init__(
        self,
        api_key: str,
        model: str,
        diagnostic_dir: Path,
        *,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_network_retries: int = DEFAULT_MAX_NETWORK_RETRIES,
        urlopen: Callable[..., Any] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ):
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        self.OPENROUTER_API_KEY = api_key
        self.OPENROUTER_MODEL = model
        self.timeout_seconds = timeout_seconds
        self.max_network_retries = max_network_retries
        self.urlopen = urlopen or request.urlopen
        self.sleep = sleeper or time.sleep
        self.archive = DiagnosticArchive(diagnostic_dir, api_key)
        self._stats = {
            "logical_stage_calls": 0,
            "http_attempts": 0,
            "timeout_retries": 0,
            "network_retries": 0,
            "incomplete_read_retries": 0,
            "transient_http_retries": 0,
            "invalid_response_json_retries": 0,
            "invalid_response_shape_retries": 0,
            "invalid_json_repair_attempts": 0,
        }

    def get_retry_stats(self) -> dict[str, int]:
        return dict(self._stats)

    @staticmethod
    def _retry_after(headers: Any, attempt: int) -> int:
        value = headers.get("Retry-After", "") if headers is not None else ""
        try:
            return min(240, max(60 * (attempt + 1), int(value)))
        except (TypeError, ValueError):
            return 60 * (attempt + 1)

    def _request_json(
        self,
        messages: list[dict[str, str]],
        *,
        response_schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        request_body = strict_json_dumps({
            "model": self.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 12000,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": response_schema},
            },
            "provider": {"require_parameters": True},
        }).encode("utf-8")
        for attempt in range(self.max_network_retries + 1):
            delay = min(60, 2 ** (attempt + 1))
            self._stats["http_attempts"] += 1
            try:
                http_request = request.Request(
                    OPENROUTER_CHAT_URL,
                    data=request_body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                    },
                    method="POST",
                )
                response = self.urlopen(http_request, timeout=self.timeout_seconds)
                if hasattr(response, "__enter__"):
                    with response as opened:
                        body = opened.read()
                else:
                    body = response.read()
                self.archive.capture(
                    "response_envelope",
                    body=body,
                    model=self.OPENROUTER_MODEL,
                    schema_name=schema_name,
                    http_attempt=attempt + 1,
                )
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    if attempt >= self.max_network_retries:
                        raise
                    self._stats["invalid_response_json_retries"] += 1
                    self.sleep(delay)
                    continue
                if not isinstance(payload, dict):
                    self.archive.capture(
                        "invalid_response_shape",
                        body=body,
                        model=self.OPENROUTER_MODEL,
                        schema_name=schema_name,
                        http_attempt=attempt + 1,
                        parsed_type=type(payload).__name__,
                    )
                    if attempt >= self.max_network_retries:
                        raise ValueError("OpenRouter response envelope must be a JSON object.")
                    self._stats["invalid_response_shape_retries"] += 1
                    self.sleep(delay)
                    continue
                return payload
            except http.client.IncompleteRead as exc:
                self.archive.capture(
                    "incomplete_read",
                    body=exc.partial,
                    model=self.OPENROUTER_MODEL,
                    schema_name=schema_name,
                    http_attempt=attempt + 1,
                    expected_bytes=exc.expected,
                )
                if attempt >= self.max_network_retries:
                    raise
                self._stats["incomplete_read_retries"] += 1
                self._stats["network_retries"] += 1
                self.sleep(delay)
            except (TimeoutError, socket.timeout):
                if attempt >= self.max_network_retries:
                    raise
                self._stats["timeout_retries"] += 1
                self.sleep(delay)
            except error.HTTPError as exc:
                body = exc.read()
                self.archive.capture(
                    "http_error",
                    body=body,
                    model=self.OPENROUTER_MODEL,
                    schema_name=schema_name,
                    http_attempt=attempt + 1,
                    status=exc.code,
                )
                daily_limit = exc.code == 429 and (
                    b"openrouter_free_tier_daily" in body or b"free-models-per-day" in body
                )
                if daily_limit and attempt >= self.max_network_retries:
                    raise DailyQuotaExhausted(
                        "OpenRouter free-tier daily request limit exhausted; diagnostic body archived."
                    ) from exc
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= self.max_network_retries:
                    raise RuntimeError(f"OpenRouter HTTP {exc.code}; diagnostic body archived.") from exc
                self._stats["transient_http_retries"] += 1
                self.sleep(self._retry_after(exc.headers, attempt) if exc.code == 429 else delay)
            except error.URLError as exc:
                if attempt >= self.max_network_retries:
                    raise
                if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                    self._stats["timeout_retries"] += 1
                else:
                    self._stats["network_retries"] += 1
                self.sleep(delay)
            except (http.client.RemoteDisconnected, ConnectionResetError, ConnectionError, OSError):
                if attempt >= self.max_network_retries:
                    raise
                self._stats["network_retries"] += 1
                self.sleep(delay)
        raise RuntimeError("OpenRouter request exhausted retry handling.")

    def _content_from_envelope(self, payload: dict[str, Any], schema_name: str, attempt: int) -> str:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            self.archive.capture(
                "invalid_response_shape",
                body=str(payload),
                model=self.OPENROUTER_MODEL,
                schema_name=schema_name,
                shape_attempt=attempt,
            )
            raise ValueError("OpenRouter response did not contain assistant message content.") from exc
        if not isinstance(content, str):
            raise ValueError("OpenRouter assistant content was not a string.")
        return content

    def call_llm(self, prompt: str) -> dict[str, Any]:
        self._stats["logical_stage_calls"] += 1
        schema_name, response_schema = response_schema_for_prompt(prompt)
        system_message = {"role": "system", "content": SYSTEM_MESSAGE}
        messages = [system_message, {"role": "user", "content": prompt}]
        content: str | None = None
        for shape_attempt in range(DEFAULT_MAX_SHAPE_RETRIES + 1):
            payload = self._request_json(messages, response_schema=response_schema, schema_name=schema_name)
            try:
                content = self._content_from_envelope(payload, schema_name, shape_attempt + 1)
                break
            except ValueError:
                if shape_attempt >= DEFAULT_MAX_SHAPE_RETRIES:
                    raise
                self._stats["invalid_response_shape_retries"] += 1
        assert content is not None
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            self._stats["invalid_json_repair_attempts"] += 1
            self.archive.capture(
                "invalid_assistant_json",
                body=content,
                model=self.OPENROUTER_MODEL,
                schema_name=schema_name,
            )
            repair_messages = [
                *messages,
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": (
                        "Repair the previous response into valid JSON matching the supplied JSON schema "
                        "exactly. Return JSON only; do not explain the repair."
                    ),
                },
            ]
            repaired = self._request_json(
                repair_messages, response_schema=response_schema, schema_name=f"{schema_name}_repair"
            )
            try:
                repaired_content = self._content_from_envelope(repaired, schema_name, 1)
                parsed = json.loads(repaired_content)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                body = locals().get("repaired_content", str(repaired))
                self.archive.capture(
                    "invalid_json_after_repair",
                    body=body,
                    model=self.OPENROUTER_MODEL,
                    schema_name=schema_name,
                )
                raise ValueError("LLM returned invalid JSON after one repair attempt.") from exc
        if not isinstance(parsed, dict):
            self.archive.capture(
                "invalid_top_level_type",
                body=content,
                model=self.OPENROUTER_MODEL,
                schema_name=schema_name,
                parsed_type=type(parsed).__name__,
            )
            raise ValueError(f"LLM returned JSON {type(parsed).__name__}; expected an object.")
        return parsed


def _retry_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = (
        "http_attempts",
        "timeout_retries",
        "network_retries",
        "incomplete_read_retries",
        "transient_http_retries",
        "invalid_response_json_retries",
        "invalid_response_shape_retries",
    )
    return {key: after.get(key, 0) - before.get(key, 0) for key in keys}


class ResumeSafeMeter:
    """Experiment meter whose sequence continues from the existing ledger."""

    def __init__(self, llm_client: Any, ledger_path: Path):
        self.llm = llm_client
        self.ledger_path = ledger_path
        self.context: dict[str, Any] = {}
        self.session_id = uuid.uuid4().hex
        self._original = llm_client._request_json
        rows = read_jsonl(ledger_path)
        sequences = [row.get("seq") for row in rows]
        if any(type(seq) is not int or seq < 1 for seq in sequences):
            raise ValueError("Existing ledger has invalid sequence identifiers.")
        if len(sequences) != len(set(sequences)):
            raise ValueError("Existing ledger already contains duplicate sequence identifiers.")
        self._seq = max(sequences, default=0)
        llm_client._request_json = self._wrapped

    def uninstall(self) -> None:
        self.llm._request_json = self._original

    @contextmanager
    def ctx(self, **kwargs: Any):
        previous = dict(self.context)
        self.context.update(kwargs)
        try:
            yield
        finally:
            self.context = previous

    def event(self, kind: str, **fields: Any) -> None:
        self._seq += 1
        append_jsonl(
            self.ledger_path,
            {"event": kind, "seq": self._seq, "resume_session_id": self.session_id, **self.context, **fields},
        )

    def _wrapped(self, messages: list[dict[str, str]], *args: Any, **kwargs: Any) -> dict[str, Any]:
        before = self.llm.get_retry_stats()
        prompt_text = "".join(str(message.get("content", "")) for message in messages)
        started = time.perf_counter()
        model = self.llm.OPENROUTER_MODEL
        try:
            data = self._original(messages, *args, **kwargs)
        except BaseException as exc:
            after = self.llm.get_retry_stats()
            self.event(
                "request_failed",
                model_requested=model,
                error=type(exc).__name__,
                **_retry_delta(before, after),
            )
            raise
        after = self.llm.get_retry_stats()
        usage = data.get("usage") if isinstance(data, dict) else None
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            content = ""
        reported = isinstance(usage, dict) and {"prompt_tokens", "completion_tokens"} <= set(usage)
        prompt_tokens = int(usage["prompt_tokens"]) if reported else math.ceil(len(prompt_text) / 4)
        completion_tokens = int(usage["completion_tokens"]) if reported else math.ceil(len(str(content)) / 4)
        cost = usage.get("cost") if isinstance(usage, dict) else None
        self.event(
            "request",
            model_requested=model,
            model_returned=data.get("model") if isinstance(data, dict) else None,
            is_json_repair=len(messages) > 2,
            schema_name=kwargs.get("schema_name"),
            usage_reported=reported,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            prompt_sha256=sha256_text(prompt_text),
            latency_s=round(time.perf_counter() - started, 3),
            **_retry_delta(before, after),
        )
        return data


class DailyQuotaExhausted(BaseException):
    """Stop the orchestrator after the registered retries without consuming later units.

    This deliberately derives directly from BaseException so historical broad
    ``except Exception`` blocks cannot convert a provider-wide daily cap into a
    hypothesis/sample failure and immediately start another doomed request.
    """


def make_caller_e17(llm_client: Any, meter: Any, fixed_stage: str | None = None, fixed_role: str | None = None):
    """Historical caller semantics plus durable accounting for fatal quota stops."""
    import run_experiment_16_matched_compute as e16

    def caller(prompt: str) -> dict[str, Any]:
        stage, role = (fixed_stage, fixed_role) if fixed_stage else e16._stage_from_prompt(prompt)
        with meter.ctx(stage=stage, role=role):
            try:
                result = llm_client.call_llm(prompt)
            except BaseException as exc:
                meter.event("logical_call", ok=False, error=type(exc).__name__)
                raise
            meter.event("logical_call", ok=True)
            return result

    return caller


def summarize_budget_e17(rows: list[dict[str, Any]], unit_id: str, arm: str) -> dict[str, Any]:
    import run_experiment_16_matched_compute as e16

    result = e16._E17_ORIGINAL_SUMMARIZE_BUDGET(rows, unit_id, arm)
    relevant = [
        row for row in rows
        if row.get("unit_id") == unit_id and row.get("arm") == arm and row.get("event") in {"request", "request_failed"}
    ]
    result["incomplete_read_retries"] = sum(row.get("incomplete_read_retries", 0) for row in relevant)
    return result


def blind_cards_e17(unit_id: str, arm_cards: dict[str, list[dict[str, Any]]]):
    import random

    rng = random.Random(int(sha256_text("E17|" + unit_id)[:16], 16))
    pooled = [(arm, item) for arm in sorted(arm_cards) for item in arm_cards[arm]]
    rng.shuffle(pooled)
    used: set[str] = set()
    blinded: list[dict[str, Any]] = []
    key: dict[str, dict[str, str]] = {}
    for arm, item in pooled:
        card_id = "C" + format(rng.getrandbits(32), "08x")
        while card_id in used:
            card_id = "C" + format(rng.getrandbits(32), "08x")
        used.add(card_id)
        blinded.append({"card_id": card_id, **item["card"]})
        key[card_id] = {"arm": arm, "source_ref": item["source_ref"]}
    return blinded, key


def judge_unit_e17(
    engine: tuple[Any, Any, Any, Any],
    meter: Any,
    unit_dir: Path,
    unit_id: str,
    question: str,
    arm_cards: dict[str, list[dict[str, Any]]],
    judge_model: str,
) -> dict[str, Any]:
    """Judge with durable per-attempt state and terminal failure checkpoints."""
    import run_experiment_16_matched_compute as e16

    llm_client, _, _, schema_module = engine
    result_path = unit_dir / "judge_result.json"
    state_path = unit_dir / "judge_state.json"
    done = read_json(result_path)
    if done is not None:
        return done
    blinded, key = blind_cards_e17(unit_id, arm_cards)
    fingerprint = sha256_text(strict_json_dumps({"question": question, "blinded": blinded, "key": key}, sort_keys=True))
    state = read_json(state_path)
    if state is not None:
        if state.get("input_fingerprint") != fingerprint:
            raise RuntimeError("Existing judge state does not match the current blinded inputs.")
        if state.get("terminal"):
            return state["result"]
    else:
        state = {
            "version": 1,
            "unit_id": unit_id,
            "input_fingerprint": fingerprint,
            "terminal": False,
            "batches": [],
        }
        atomic_write_json(state_path, state)

    batch_size = 10
    judgments: list[dict[str, Any]] = []
    leak_hits: list[str] = []
    prompts_meta: list[dict[str, Any]] = []
    status = "OK"
    with meter.ctx(arm="JUDGE"), e16.use_model(llm_client, judge_model):
        for offset in range(0, len(blinded), batch_size):
            index = offset // batch_size
            batch = blinded[offset:offset + batch_size]
            prompt = e16.judge_prompt(question, batch, schema_module)
            cards_text = strict_json_dumps(batch)
            cards_pretty = strict_json_dumps(batch, indent=2)
            if cards_pretty not in prompt:
                raise RuntimeError("Judge prompt construction changed; blinding scan cannot isolate cards.")
            template = prompt.replace(cards_pretty, "<CARDS>")
            template_hits = sorted(set(match.group(0) for match in e16.BLINDING_FORBIDDEN.finditer(template)))
            template_hits += sorted(
                set(token for token in json.dumps([sorted(card) for card in batch]).split('"') if e16.BLINDING_FORBIDDEN.search(token))
            )
            if template_hits:
                raise RuntimeError(f"Blinding violation in judge prompt template/field names: {template_hits}")
            leak_hits += sorted(set(match.group(0) for match in e16.CONTENT_LEAK.finditer(cards_pretty)))
            metadata = {
                "batch": index,
                "card_ids": [card["card_id"] for card in batch],
                "prompt_sha256": sha256_text(prompt),
                "cards_sha256": sha256_text(cards_text),
            }
            prompts_meta.append(metadata)
            while len(state["batches"]) <= index:
                state["batches"].append({"batch": len(state["batches"]), "attempts": [], "status": "PENDING"})
            batch_state = state["batches"][index]
            # A STARTED entry means the prior process stopped after durably
            # consuming an attempt but before it could checkpoint the result.
            # Count it as interrupted; never grant an extra judge opportunity.
            state_changed = False
            for prior_attempt in batch_state["attempts"]:
                if prior_attempt.get("status") == "STARTED":
                    prior_attempt.update({
                        "status": "INTERRUPTED",
                        "ok": False,
                        "error_type": "InterruptedJudgeAttempt",
                        "error": "Process ended before the attempt result was checkpointed.",
                    })
                    state_changed = True
            if state_changed:
                if len(batch_state["attempts"]) >= 2:
                    batch_state["status"] = "FAILED"
                atomic_write_json(state_path, state)
            if batch_state["status"] == "OK":
                judgments.extend(batch_state["judgments"])
                continue
            if batch_state["status"] == "FAILED" or len(batch_state["attempts"]) >= 2:
                status = "JUDGE_FAILED"
                break
            while len(batch_state["attempts"]) < 2:
                attempt_number = len(batch_state["attempts"]) + 1
                attempt_record = {"attempt": attempt_number, "status": "STARTED", "ok": None}
                batch_state["attempts"].append(attempt_record)
                atomic_write_json(state_path, state)
                try:
                    payload = e16.make_caller(llm_client, meter, "blinded_judge", "judge")(prompt)
                    rows = e16.validate_judgments(payload, [card["card_id"] for card in batch], schema_module)
                    attempt_record.update({"status": "COMPLETED", "ok": True})
                    batch_state["status"] = "OK"
                    batch_state["judgments"] = rows
                    atomic_write_json(state_path, state)
                    judgments.extend(rows)
                    break
                except Exception as exc:
                    meter.event("judge_invalid", batch=index, attempt=attempt_number, error=type(exc).__name__)
                    attempt_record.update({
                        "status": "COMPLETED",
                        "ok": False,
                        "error_type": type(exc).__name__,
                        "error": _redact_text(str(exc))[:500],
                    })
                    if len(batch_state["attempts"]) >= 2:
                        batch_state["status"] = "FAILED"
                    atomic_write_json(state_path, state)
            if batch_state["status"] != "OK":
                status = "JUDGE_FAILED"
                break

    result = {
        "status": status,
        "key": key,
        "blinded_cards": blinded,
        "judgments": judgments,
        "batches": prompts_meta,
        "blinding_leak_hits": sorted(set(leak_hits)),
    }
    state["terminal"] = True
    state["result"] = result
    atomic_write_json(state_path, state)
    if status == "OK":
        atomic_write_json(result_path, result)
    return result


def install_experiment_17_core_hooks() -> None:
    """Install in-process E17 hooks into the imported E16 scientific core."""
    import run_experiment_16_matched_compute as e16

    if not hasattr(e16, "_E17_ORIGINAL_SUMMARIZE_BUDGET"):
        e16._E17_ORIGINAL_SUMMARIZE_BUDGET = e16.summarize_budget
    e16._write_json = atomic_write_json
    e16.Meter = ResumeSafeMeter
    e16.make_caller = make_caller_e17
    e16.blind_cards = blind_cards_e17
    e16.judge_unit = judge_unit_e17
    e16.summarize_budget = summarize_budget_e17
    if "incomplete_read_retries" not in e16.BUDGET_FIELDS:
        fields = list(e16.BUDGET_FIELDS)
        fields.insert(fields.index("transient_http_retries"), "incomplete_read_retries")
        e16.BUDGET_FIELDS = tuple(fields)
