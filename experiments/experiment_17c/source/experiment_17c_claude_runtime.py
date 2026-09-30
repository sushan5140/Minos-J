"""Claude Code CLI transport for Minos-J Experiment 17-C.

Experiment 17-C is the Claude-based replication of the interrupted Experiment
17.  The only component replaced here is the model transport: instead of an
OpenRouter HTTP request, each completion is one headless ``claude -p`` call
authenticated through the operator's existing Claude subscription (OAuth).

Everything above the transport -- strict per-stage JSON schemas, the one-retry
shape policy, the single JSON-repair request, the resume-safe ledger, the
diagnostic archive, the durable judge state and the historical v4 pipeline --
is inherited unchanged from ``experiment_17_runtime`` and
``run_experiment_16_matched_compute``.

No paid API dependency is introduced: API-key and base-URL variables are
removed from the child environment, ``--bare`` (which only accepts API keys)
is never used, and the preflight refuses to run unless the CLI reports
``authMethod == "claude.ai"``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

import experiment_17_runtime as runtime


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CLI_PATH = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude-code"
GENERATOR_MODEL = "claude-sonnet-5"
JUDGE_MODEL = "claude-opus-5-5"
EFFORT = "medium"
MAX_OUTPUT_TOKENS = 12000
CLI_TIMEOUT_SECONDS = 900
ISOLATED_CWD = PROJECT_DIR / "work" / "experiment_17c_cli_cwd"

# Variables that would redirect the child away from the subscription login
# (API keys, gateways) or tie it to the desktop host session.
_STRIPPED_ENV_PREFIXES = ("CLAUDE", "ANTHROPIC_")
_STRIPPED_ENV_NAMES = {"USE_LOCAL_OAUTH", "USE_STAGING_OAUTH"}

_USAGE_LIMIT = re.compile(
    r"usage limit|session limit|limit reached|limit will reset|resets? (at|in)|resets \d|weekly limit|5-hour limit|"
    r"hit your \w+ limit|out of (extra )?usage|upgrade to (max|pro)|credit balance",
    re.IGNORECASE,
)
# Amendment 3: Claude Pro returned HTTP 429 "You've hit your session limit · resets 8:20am",
# which the original pattern missed.  Any 429 that mentions a limit is a quota stop.
_LIMIT_WORD = re.compile(r"\blimit\b", re.IGNORECASE)


def is_usage_limit(message: str, status: Any = None) -> bool:
    return bool(_USAGE_LIMIT.search(message)) or (status == 429 and bool(_LIMIT_WORD.search(message)))
_TRANSIENT = re.compile(
    r"overloaded|529|500|502|503|504|internal server error|timed? ?out|ECONNRESET|socket|network|"
    r"fetch failed|refresh(ing)? OAuth token|another Claude Code process|temporarily",
    re.IGNORECASE,
)
_OAUTH_REFRESH = re.compile(r"refresh(ing)? OAuth token|another Claude Code process", re.IGNORECASE)
_AUTH_FATAL = re.compile(r"invalid api key|not logged in|please run /login|authentication_error|401", re.IGNORECASE)


class SubscriptionUsageLimitReached(BaseException):
    """Claude subscription usage window exhausted.

    Derives from BaseException for the same reason as
    ``experiment_17_runtime.DailyQuotaExhausted``: historical broad
    ``except Exception`` blocks must not turn a provider-wide limit into an
    invalid sample or a failed stage.  The run stops, state is preserved, and
    the identical command resumes after the window resets.
    """


class ClaudeAuthUnavailable(BaseException):
    """The subscription login cannot be used; stop without consuming units."""


def find_cli(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"Claude Code CLI not found at {path}")
        return path
    env_path = os.environ.get("MINOS_J_CLAUDE_CLI")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    # The Claude desktop app is an MSIX package: processes inside it see
    # %APPDATA%\Claude, processes outside it (e.g. Task Scheduler) only see the
    # package-private LocalCache copy.  Search both.
    roots = [DEFAULT_CLI_PATH]
    packages = Path(os.environ.get("LOCALAPPDATA", "")) / "Packages"
    roots += [p / "LocalCache" / "Roaming" / "Claude" / "claude-code" for p in packages.glob("Claude_*")]
    candidates = sorted(
        (exe for root in roots for exe in root.glob("*/claude.exe")),
        key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"[.]", p.parent.name)],
    )
    if not candidates:
        raise FileNotFoundError("Claude Code CLI not found; set MINOS_J_CLAUDE_CLI.")
    return candidates[-1]


def child_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in (base if base is not None else os.environ).items()
        if not key.startswith(_STRIPPED_ENV_PREFIXES) and key not in _STRIPPED_ENV_NAMES
    }
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(MAX_OUTPUT_TOKENS)
    return env


def serialize_messages(messages: list[dict[str, str]]) -> tuple[str, str]:
    """Map chat messages onto (system prompt, single user prompt) for ``claude -p``.

    Normal stage calls are exactly [system, user] and pass through verbatim.
    The single JSON-repair request is [system, user, assistant, user]; ``-p``
    accepts one user turn, so the prior exchange is quoted inside it.
    """
    system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
    rest = messages[1:] if system else messages
    if len(rest) == 1 and rest[0]["role"] == "user":
        return system, rest[0]["content"]
    parts = []
    for message in rest[:-1]:
        label = "ORIGINAL REQUEST" if message["role"] == "user" else "YOUR PREVIOUS RESPONSE"
        parts.append(f"<<<{label}>>>\n{message['content']}\n<<<END {label}>>>")
    parts.append(rest[-1]["content"])
    return system, "\n\n".join(parts)


def default_runner(argv: list[str], stdin_text: str, env: dict[str, str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    completed = subprocess.run(
        argv,
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        env=env,
        cwd=str(cwd),
        timeout=timeout,
    )
    return (
        completed.returncode,
        completed.stdout.decode("utf-8", errors="replace"),
        completed.stderr.decode("utf-8", errors="replace"),
    )


def auth_status(cli: Path, runner: Callable[..., tuple[int, str, str]] | None = None) -> dict[str, Any]:
    ISOLATED_CWD.mkdir(parents=True, exist_ok=True)
    code, out, err = (runner or default_runner)([str(cli), "auth", "status"], "", child_env(), ISOLATED_CWD, 60)
    try:
        status = json.loads(out)
    except json.JSONDecodeError:
        return {"parse_error": True, "exit_code": code, "stderr": err[-500:]}
    # Keep only non-identifying fields.
    return {k: status.get(k) for k in ("loggedIn", "authMethod", "apiProvider", "subscriptionType")}


def cli_version(cli: Path, runner: Callable[..., tuple[int, str, str]] | None = None) -> str:
    ISOLATED_CWD.mkdir(parents=True, exist_ok=True)
    _, out, _ = (runner or default_runner)([str(cli), "--version"], "", child_env(), ISOLATED_CWD, 60)
    return out.strip()


class ClaudeCodeCLIClient(runtime.StructuredOpenRouterClient):
    """Drop-in replacement for the E17 client whose transport is ``claude -p``.

    ``OPENROUTER_MODEL`` keeps its historical attribute name because the
    inherited meter, ``use_model`` context manager and judge code address the
    active model through it; here it holds a Claude model ID.
    """

    def __init__(
        self,
        model: str,
        diagnostic_dir: Path,
        *,
        cli_path: Path | None = None,
        effort: str = EFFORT,
        timeout_seconds: int = CLI_TIMEOUT_SECONDS,
        max_network_retries: int = runtime.DEFAULT_MAX_NETWORK_RETRIES,
        runner: Callable[..., tuple[int, str, str]] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ):
        # The parent requires a non-empty key; the subscription transport has none.
        super().__init__(
            "claude-subscription-oauth",
            model,
            diagnostic_dir,
            timeout_seconds=timeout_seconds,
            max_network_retries=max_network_retries,
            sleeper=sleeper,
        )
        self.OPENROUTER_API_KEY = None
        self.archive.api_key = None
        self.cli_path = cli_path or find_cli()
        self.effort = effort
        self.runner = runner or default_runner
        ISOLATED_CWD.mkdir(parents=True, exist_ok=True)

    def _argv(self, system: str, response_schema: dict[str, Any]) -> list[str]:
        return [
            str(self.cli_path),
            "-p",
            "--model", self.OPENROUTER_MODEL,
            "--effort", self.effort,
            "--output-format", "json",
            "--tools", "",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--system-prompt", system,
            "--json-schema", runtime.strict_json_dumps(response_schema),
        ]

    @staticmethod
    def _envelope(result: dict[str, Any], requested_model: str) -> dict[str, Any]:
        usage = result.get("usage") or {}
        structured = result.get("structured_output")
        if structured is not None:
            content: Any = runtime.strict_json_dumps(structured)
        else:
            content = result.get("result") if isinstance(result.get("result"), str) else None
        prompt_tokens = sum(
            int(usage.get(key) or 0)
            for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        )
        completion_tokens = int(usage.get("output_tokens") or 0)
        models = sorted((result.get("modelUsage") or {}).keys())
        returned = next((m for m in models if m.startswith(requested_model)), models[0] if models else None)
        envelope: dict[str, Any] = {
            "model": returned,
            "choices": [{"message": {"role": "assistant", "content": content}}],
        }
        if "input_tokens" in usage and "output_tokens" in usage:
            envelope["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        return envelope

    def _request_json(
        self,
        messages: list[dict[str, str]],
        *,
        response_schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        system, prompt = serialize_messages(messages)
        argv = self._argv(system, response_schema)
        env = child_env()
        for attempt in range(self.max_network_retries + 1):
            delay = min(60, 2 ** (attempt + 1))
            self._stats["http_attempts"] += 1
            try:
                code, out, err = self.runner(argv, prompt, env, ISOLATED_CWD, self.timeout_seconds)
            except subprocess.TimeoutExpired:
                self.archive.capture("cli_timeout", model=self.OPENROUTER_MODEL, schema_name=schema_name,
                                     cli_attempt=attempt + 1)
                if attempt >= self.max_network_retries:
                    raise TimeoutError("Claude Code CLI call timed out after retries.")
                self._stats["timeout_retries"] += 1
                self.sleep(delay)
                continue
            self.archive.capture(
                "cli_result",
                body=out,
                model=self.OPENROUTER_MODEL,
                schema_name=schema_name,
                cli_attempt=attempt + 1,
                exit_code=code,
                stderr_tail=err[-2000:],
            )
            try:
                result = json.loads(out)
            except json.JSONDecodeError:
                result = None
            if not isinstance(result, dict):
                text = f"{out[-1000:]}\n{err[-1000:]}"
                if _USAGE_LIMIT.search(text):
                    raise SubscriptionUsageLimitReached("Claude subscription usage limit reached; state preserved.")
                if attempt >= self.max_network_retries:
                    raise RuntimeError(f"Claude Code CLI exited {code} without a JSON result; diagnostic archived.")
                self._stats["invalid_response_json_retries"] += 1
                self.sleep(delay)
                continue
            if result.get("is_error"):
                message = str(result.get("result") or "")
                status = result.get("api_error_status")
                if is_usage_limit(message, status):
                    raise SubscriptionUsageLimitReached(
                        "Claude subscription usage limit reached; diagnostic archived; state preserved."
                    )
                if _AUTH_FATAL.search(message) and not _TRANSIENT.search(message):
                    raise ClaudeAuthUnavailable("Claude subscription login unavailable; diagnostic archived.")
                if _OAUTH_REFRESH.search(message):
                    # Infrastructure, not model behaviour: never charge it to a unit.
                    if attempt >= self.max_network_retries:
                        raise ClaudeAuthUnavailable("Claude OAuth refresh kept failing; state preserved.")
                    self._stats["network_retries"] += 1
                    self.sleep(60 * (attempt + 1))
                    continue
                structured_failure = "structured" in str(result.get("subtype", "")) or "schema" in message.lower()
                if structured_failure:
                    # Model could not satisfy the schema: hand back an empty
                    # content so the inherited shape-retry policy applies.
                    return self._envelope({**result, "structured_output": None, "result": None}, self.OPENROUTER_MODEL)
                transient = status in {429, 500, 502, 503, 504, 529} or bool(_TRANSIENT.search(message))
                if not transient or attempt >= self.max_network_retries:
                    raise RuntimeError(f"Claude Code CLI error (status {status}); diagnostic archived.")
                self._stats["transient_http_retries"] += 1
                self.sleep(delay if status != 429 else 60 * (attempt + 1))
                continue
            return self._envelope(result, self.OPENROUTER_MODEL)
        raise RuntimeError("Claude Code CLI request exhausted retry handling.")

    def _content_from_envelope(self, payload: dict[str, Any], schema_name: str, attempt: int) -> str:
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(content, str):
            self.archive.capture(
                "invalid_response_shape",
                body=runtime.strict_json_dumps(payload),
                model=self.OPENROUTER_MODEL,
                schema_name=schema_name,
                shape_attempt=attempt,
            )
            raise ValueError("Claude Code CLI returned no assistant content.")
        return content
