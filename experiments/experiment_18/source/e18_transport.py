"""Claude Code CLI transport for Experiment 18 (subscription OAuth; no paid API).

Accounting design (new for E18; the E17-C budget controller is NOT used):
* every CLI attempt gets an ``attempt_uid``;
* ``on_event("attempt_started", ...)`` is emitted BEFORE the subprocess starts and
  ``on_event("attempt_finished", ...)`` after it returns, carrying the provider-reported
  usage split into input / cache-creation / cache-read / output tokens, latency, exit
  code, model returned and CLI version;
* usage reported inside ERROR envelopes is recorded too ("measured tokens" = everything
  the provider reports, successful or not);
* an ``attempt_started`` without a matching ``attempt_finished`` is an orphan (process
  killed mid-call) and is detected exactly by the runner.

Failure classes:
  QuotaPause / AuthPause   -> BaseException: the run pauses; nothing is charged to a trial.
  InvalidOutput            -> the model answered but the answer is unusable (schema/structured-output
                              failure, output cap, non-JSON content); handled by the runner's single
                              repair rule, identical for every arm.
  InfrastructureFailure    -> transient errors persisted past the retry limit, or an unclassified CLI error.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from e18_common import atomic_write_json, dumps

GENERATOR_MODEL = "claude-sonnet-5"
EFFORT = "low"
MAX_OUTPUT_TOKENS = 8000
TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 4

_QUOTA = re.compile(r"usage limit|session limit|weekly limit|limit reached|limit will reset|resets? (at|in)|resets \d|"
                    r"hit your \w+ limit|out of (extra )?usage|credit balance", re.I)
_OAUTH = re.compile(r"refresh(ing)? OAuth token|another Claude Code process", re.I)
_AUTH = re.compile(r"not logged in|please run /login|invalid api key|authentication_error", re.I)
_TRANSIENT = re.compile(r"overloaded|internal server error|timed? ?out|ECONNRESET|socket hang up|network|fetch failed|temporarily", re.I)
_OUTPUT_CAP = re.compile(r"exceeded the \d+ output token maximum", re.I)
_STRIP_PREFIXES = ("CLAUDE", "ANTHROPIC_")
_STRIP_NAMES = {"USE_LOCAL_OAUTH", "USE_STAGING_OAUTH"}


class QuotaPause(BaseException):
    """Subscription usage window exhausted. Not an experimental outcome."""


class AuthPause(BaseException):
    """Subscription login unusable. Not an experimental outcome."""


class InvalidOutput(Exception):
    pass


class InfrastructureFailure(Exception):
    pass


def is_quota_message(message: str, status: Any = None) -> bool:
    return bool(_QUOTA.search(message)) or (status == 429 and re.search(r"\blimit\b", message, re.I) is not None)


def find_cli() -> Path:
    explicit = os.environ.get("MINOS_J_CLAUDE_CLI")
    if explicit and Path(explicit).exists():
        return Path(explicit)
    roots = [Path(os.environ.get("APPDATA", "")) / "Claude" / "claude-code"]
    roots += [p / "LocalCache" / "Roaming" / "Claude" / "claude-code"
              for p in (Path(os.environ.get("LOCALAPPDATA", "")) / "Packages").glob("Claude_*")]
    found = sorted((exe for r in roots for exe in r.glob("*/claude.exe")),
                   key=lambda p: [int(x) if x.isdigit() else x for x in p.parent.name.split(".")])
    if not found:
        raise FileNotFoundError("Claude Code CLI not found; set MINOS_J_CLAUDE_CLI.")
    return found[-1]


def child_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in (base if base is not None else os.environ).items()
           if not k.startswith(_STRIP_PREFIXES) and k not in _STRIP_NAMES}
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(MAX_OUTPUT_TOKENS)
    return env


def default_runner(argv: list[str], stdin_text: str, env: dict[str, str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    done = subprocess.run(argv, input=stdin_text.encode("utf-8"), capture_output=True, env=env, cwd=str(cwd), timeout=timeout)
    return done.returncode, done.stdout.decode("utf-8", "replace"), done.stderr.decode("utf-8", "replace")


def usage_of(result: dict[str, Any] | None) -> dict[str, int]:
    u = (result or {}).get("usage") or {}
    out = {
        "input_tokens": int(u.get("input_tokens") or 0),
        "cache_creation_input_tokens": int(u.get("cache_creation_input_tokens") or 0),
        "cache_read_input_tokens": int(u.get("cache_read_input_tokens") or 0),
        "output_tokens": int(u.get("output_tokens") or 0),
    }
    out["measured_total_tokens"] = sum(out.values())
    return out


@dataclass
class CallOutcome:
    payload: dict[str, Any]
    attempts: list[str] = field(default_factory=list)
    model_returned: str | None = None


class ClaudeCLI:
    def __init__(self, cwd: Path, archive_dir: Path, on_event: Callable[..., None], *, cli: Path | None = None,
                 runner: Callable[..., tuple[int, str, str]] | None = None, sleeper: Callable[[float], None] | None = None,
                 cli_version: str = "unknown", model: str = GENERATOR_MODEL):
        self.cli = cli or find_cli()
        self.cwd = cwd
        self.archive_dir = archive_dir
        self.on_event = on_event
        self.runner = runner or default_runner
        self.sleep = sleeper or time.sleep
        self.cli_version = cli_version
        self.model = model
        cwd.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

    def argv(self, system: str, schema: dict[str, Any]) -> list[str]:
        return [str(self.cli), "-p", "--model", self.model, "--effort", EFFORT, "--output-format", "json",
                "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--disable-slash-commands",
                "--no-session-persistence", "--system-prompt", system, "--json-schema", dumps(schema)]

    def complete(self, system: str, prompt: str, schema_name: str, schema: dict[str, Any], context: dict[str, Any]) -> CallOutcome:
        argv, env = self.argv(system, schema), child_env()
        attempts: list[str] = []
        for attempt in range(MAX_TRANSIENT_RETRIES + 1):
            uid = uuid.uuid4().hex
            attempts.append(uid)
            self.on_event("attempt_started", attempt_uid=uid, attempt_index=attempt + 1, schema_name=schema_name,
                          prompt_sha256=__import__("hashlib").sha256(prompt.encode()).hexdigest(), **context)
            started = time.perf_counter()
            try:
                code, out, err = self.runner(argv, prompt, env, self.cwd, TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                code, out, err = -1, "", "TIMEOUT"
            latency = round(time.perf_counter() - started, 3)
            try:
                result = json.loads(out)
                if not isinstance(result, dict):
                    result = None
            except json.JSONDecodeError:
                result = None
            message = str((result or {}).get("result") or "") if result else f"{out[-500:]} {err[-500:]}"
            status = (result or {}).get("api_error_status")
            usage = usage_of(result)
            models = sorted(((result or {}).get("modelUsage") or {}).keys())
            model_returned = next((m for m in models if m.startswith(self.model)), models[0] if models else None)
            if result is not None and not result.get("is_error") and result.get("structured_output") is not None:
                klass = "OK"
            elif result is None and "TIMEOUT" in err:
                klass = "TRANSIENT"
            elif is_quota_message(message, status):
                klass = "QUOTA"
            elif _OAUTH.search(message):
                klass = "OAUTH_CONTENTION"
            elif _AUTH.search(message):
                klass = "AUTH"
            elif _OUTPUT_CAP.search(message) or "structured" in str((result or {}).get("subtype", "")):
                klass = "INVALID_OUTPUT"
            elif result is not None and not result.get("is_error"):
                klass = "INVALID_OUTPUT"          # answered, but no structured output
            elif result is None or status in (429, 500, 502, 503, 504, 529) or _TRANSIENT.search(message):
                klass = "TRANSIENT"
            else:
                klass = "CLI_ERROR"
            atomic_write_json(self.archive_dir / f"{uid}.json", {
                "attempt_uid": uid, "classification": klass, "exit_code": code, "latency_s": latency,
                "stdout": out, "stderr_tail": err[-2000:], **context})
            self.on_event("attempt_finished", attempt_uid=uid, classification=klass, exit_code=code, latency_s=latency,
                          model_returned=model_returned, cli_version=self.cli_version, num_turns=(result or {}).get("num_turns"),
                          **usage, **context)
            if klass == "OK":
                return CallOutcome(result["structured_output"], attempts, model_returned)
            if klass == "QUOTA":
                raise QuotaPause(message[:200])
            if klass == "AUTH":
                raise AuthPause(message[:200])
            if klass == "INVALID_OUTPUT":
                raise InvalidOutput(message[:300] or "no structured output")
            if klass == "OAUTH_CONTENTION":
                if attempt >= MAX_TRANSIENT_RETRIES:
                    raise AuthPause("OAuth refresh contention persisted")
                self.sleep(60 * (attempt + 1))
                continue
            if klass == "CLI_ERROR" or attempt >= MAX_TRANSIENT_RETRIES:
                raise InfrastructureFailure(f"{klass}: {message[:200]}")
            self.sleep(min(60, 2 ** (attempt + 1)) if status != 429 else 60 * (attempt + 1))
        raise InfrastructureFailure("retry handling exhausted")


def cli_version(cli: Path, runner: Callable[..., tuple[int, str, str]] | None = None, cwd: Path | None = None) -> str:
    code, out, _ = (runner or default_runner)([str(cli), "--version"], "", child_env(), cwd or Path.cwd(), 60)
    return out.strip()


def auth_status(cli: Path, runner: Callable[..., tuple[int, str, str]] | None = None, cwd: Path | None = None) -> dict[str, Any]:
    code, out, _ = (runner or default_runner)([str(cli), "auth", "status"], "", child_env(), cwd or Path.cwd(), 60)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"parse_error": True}
    return {k: data.get(k) for k in ("loggedIn", "authMethod", "apiProvider", "subscriptionType")}
