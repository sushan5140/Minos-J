"""Minimal OpenRouter JSON client."""

from __future__ import annotations

import json
import os
import socket
import time
from typing import Any
from urllib import error, request

from schema import DEFAULT_MODEL


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
REQUEST_TIMEOUT_SECONDS = 300
MAX_NETWORK_RETRIES = 4
_RETRY_STATS = {
    "logical_stage_calls": 0,
    "http_attempts": 0,
    "timeout_retries": 0,
    "network_retries": 0,
    "transient_http_retries": 0,
    "invalid_response_json_retries": 0,
    "invalid_response_shape_retries": 0,
    "invalid_json_repair_attempts": 0,
}


def get_retry_stats() -> dict[str, int]:
    """Return credential-free execution counters for reproducibility reporting."""
    return dict(_RETRY_STATS)


def _safe_http_error_detail(body: bytes) -> str:
    try:
        payload = json.loads(body.decode("utf-8"))
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        detail = error.get("message") or error.get("code") or "no provider detail"
    except Exception:
        detail = "unreadable provider error envelope"
    text = " ".join(str(detail).split())[:400]
    if OPENROUTER_API_KEY:
        text = text.replace(OPENROUTER_API_KEY, "<redacted>")
    return text


def _request_json(
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    request_body = json.dumps(
        {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 12000,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    for attempt in range(MAX_NETWORK_RETRIES + 1):
        retry_delay = 2 ** (attempt + 1)
        _RETRY_STATS["http_attempts"] += 1
        try:
            http_request = request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                },
                method="POST",
            )
            with request.urlopen(
                http_request, timeout=REQUEST_TIMEOUT_SECONDS
            ) as response:
                response_body = response.read()
            return json.loads(response_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            if attempt >= MAX_NETWORK_RETRIES:
                raise
            _RETRY_STATS["invalid_response_json_retries"] += 1
            print(
                f"OpenRouter returned a malformed response envelope; retry "
                f"{attempt + 1}/{MAX_NETWORK_RETRIES}.",
                flush=True,
            )
        except (TimeoutError, socket.timeout):
            if attempt >= MAX_NETWORK_RETRIES:
                raise
            _RETRY_STATS["timeout_retries"] += 1
            print(
                f"OpenRouter timeout; retry {attempt + 1}/{MAX_NETWORK_RETRIES}.",
                flush=True,
            )
        except error.HTTPError as exc:
            status = exc.code
            error_body = exc.read()
            if status not in {429, 500, 502, 503, 504}:
                raise RuntimeError(
                    f"OpenRouter HTTP {status}: {_safe_http_error_detail(error_body)}"
                )
            if attempt >= MAX_NETWORK_RETRIES:
                raise RuntimeError(
                    f"OpenRouter HTTP {status} after {MAX_NETWORK_RETRIES} retries: "
                    f"{_safe_http_error_detail(error_body)}"
                )
            _RETRY_STATS["transient_http_retries"] += 1
            if status == 429:
                retry_after = exc.headers.get("Retry-After", "")
                try:
                    retry_delay = min(
                        240, max(60 * (attempt + 1), int(retry_after))
                    )
                except (TypeError, ValueError):
                    retry_delay = 60 * (attempt + 1)
            print(
                f"OpenRouter transient HTTP {status}; retry "
                f"{attempt + 1}/{MAX_NETWORK_RETRIES}.",
                flush=True,
            )
        except error.URLError as exc:
            is_timeout = isinstance(exc.reason, (TimeoutError, socket.timeout))
            if attempt >= MAX_NETWORK_RETRIES:
                raise
            if is_timeout:
                _RETRY_STATS["timeout_retries"] += 1
                print(
                    f"OpenRouter timeout; retry {attempt + 1}/{MAX_NETWORK_RETRIES}.",
                    flush=True,
                )
            else:
                _RETRY_STATS["network_retries"] += 1
                print(
                    f"OpenRouter network error; retry {attempt + 1}/{MAX_NETWORK_RETRIES}.",
                    flush=True,
                )
            retry_delay = 60
        except (ConnectionError, ConnectionResetError, OSError):
            if attempt >= MAX_NETWORK_RETRIES:
                raise
            _RETRY_STATS["network_retries"] += 1
            retry_delay = 60
            print(
                f"OpenRouter network error; retry {attempt + 1}/{MAX_NETWORK_RETRIES}.",
                flush=True,
            )
        time.sleep(retry_delay)
    raise RuntimeError("OpenRouter request exhausted retry handling.")


def call_llm(prompt: str) -> dict:
    """Call OpenRouter and parse a JSON object, failing loudly on malformed output."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    _RETRY_STATS["logical_stage_calls"] += 1
    system_message = {
        "role": "system",
        "content": (
            "You are a strict research pipeline component. "
            "Return valid JSON only. No markdown, no commentary."
        ),
    }
    messages = [system_message, {"role": "user", "content": prompt}]
    content: Any = None
    for shape_attempt in range(MAX_NETWORK_RETRIES + 1):
        data = _request_json(messages)
        try:
            content = data["choices"][0]["message"]["content"]
            break
        except (KeyError, IndexError, TypeError):
            if shape_attempt >= MAX_NETWORK_RETRIES:
                raise ValueError(
                    "OpenRouter response did not contain assistant message content."
                )
            _RETRY_STATS["invalid_response_shape_retries"] += 1
            print(
                f"OpenRouter returned an invalid response shape; retry "
                f"{shape_attempt + 1}/{MAX_NETWORK_RETRIES}.",
                flush=True,
            )

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        _RETRY_STATS["invalid_json_repair_attempts"] += 1
        print("OpenRouter returned invalid JSON; requesting one JSON repair.", flush=True)
        invalid_content = content if isinstance(content, str) else repr(content)
        repair_messages = [
            system_message,
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": invalid_content},
            {
                "role": "user",
                "content": (
                    "Repair the previous response into valid JSON matching the requested schema exactly. "
                    "Return JSON only; do not explain the repair."
                ),
            },
        ]
        repaired_data = _request_json(repair_messages)
        try:
            repaired_content = repaired_data["choices"][0]["message"]["content"]
            parsed = json.loads(repaired_content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as repair_exc:
            raise ValueError("LLM returned invalid JSON after one repair attempt.") from repair_exc
    if not isinstance(parsed, dict):
        raise ValueError(f"LLM returned JSON {type(parsed).__name__}; expected an object.")
    return parsed
