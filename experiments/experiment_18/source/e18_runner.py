"""Experiment 18 runner: executes (case x arm) trials with exact resume semantics.

Exit codes: 0 done | 2 corrupt state (operator review) | 4 completed-study overwrite refused |
            73 another run holds the lock | 75 paused on usage limit / login | 76 infrastructure halt |
            77 model-identity halt | 78 protocol not frozen / mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import e18_prompts as P
import e18_tasks as T
import e18_transport as X
from e18_common import (E18_DIR, PILOT_DIR, RESULTS_DIR, WORK_DIR, CorruptRecord, append_jsonl, atomic_write_json,
                        dumps, read_json_strict, read_jsonl_strict)

EXIT_CORRUPT, EXIT_OVERWRITE, EXIT_BUSY, EXIT_PAUSED, EXIT_INFRA_HALT, EXIT_IDENTITY, EXIT_PROTOCOL = 2, 4, 73, 75, 76, 77, 78
INFRA_WINDOW, INFRA_LIMIT = 40, 5
REPAIR_SENTENCE = "Your previous response was invalid ({reason}). Return corrected JSON that satisfies the schema exactly."


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def arm_order(case_id: str) -> list[str]:
    order = list(P.ARMS)
    random.Random(int(hashlib.sha256(f"E18|arm-order|{case_id}".encode()).hexdigest()[:16], 16)).shuffle(order)
    return order


class Halt(BaseException):
    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = code


class FinalInvalid(Exception):
    pass


class Paths:
    def __init__(self, set_name: str, work: Path = WORK_DIR, results: Path = RESULTS_DIR):
        self.set = set_name
        self.root = work / set_name
        self.trials = self.root / "trials"
        self.ledger = self.root / "ledger.jsonl"
        self.archive = self.root / "attempts"
        self.calibration = self.root / "calibration.jsonl"
        self.lock = self.root / "run.lock"
        self.cli_cwd = work / "cli_cwd"
        self.report = (PILOT_DIR / "pilot_report.json") if set_name == "pilot" and results == RESULTS_DIR else results / f"{set_name}_report.json"

    def trial(self, case_id: str, arm: str) -> Path:
        return self.trials / case_id / arm


def _pid_alive(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    except FileNotFoundError:  # non-Windows fallback
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def acquire_lock(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                holder = int(path.read_text().strip() or 0)
            except ValueError:
                holder = 0
            if holder and holder != os.getpid() and _pid_alive(holder):
                raise Halt(EXIT_BUSY, f"run lock held by pid {holder}")
            path.unlink(missing_ok=True)
    raise Halt(EXIT_BUSY, "could not acquire run lock")


class Ledger:
    def __init__(self, path: Path, session: str):
        self.path = path
        self.session = session
        rows = read_jsonl_strict(path)
        seqs = [r.get("seq") for r in rows]
        if any(type(s) is not int for s in seqs) or len(seqs) != len(set(seqs)) or seqs != sorted(seqs):
            raise CorruptRecord("ledger sequence numbers are not unique and monotonic")
        self.rows = rows
        self.seq = max(seqs, default=0)

    def event(self, kind: str, **fields: Any) -> dict[str, Any]:
        self.seq += 1
        row = {"event": kind, "seq": self.seq, "session": self.session, "at_utc": now(), **fields}
        append_jsonl(self.path, row)
        self.rows.append(row)
        return row


def scan_state(paths: Paths) -> None:
    """Every checkpoint must parse; terminal markers and ledger terminal events must agree."""
    for f in paths.trials.glob("*/*/*.json"):
        read_json_strict(f)


class Runner:
    def __init__(self, set_name: str, client_factory: Callable[..., Any], *, protocol_digest: str, tasks_sha: str,
                 paths: Paths | None = None, frozen_model: str = X.GENERATOR_MODEL, probe: bool = True,
                 cases: list[dict[str, Any]] | None = None):
        self.paths = paths or Paths(set_name)
        self.set = set_name
        self.client_factory = client_factory
        self.protocol_digest = protocol_digest
        self.tasks_sha = tasks_sha
        self.frozen_model = frozen_model
        self.probe = probe
        self.cases = cases if cases is not None else T.load_public(set_name)
        self.recent_terminal: list[str] = []

    # ------------------------------------------------------------------ events from the transport
    def _on_event(self, kind: str, **fields: Any) -> None:
        self.ledger.event(kind, **fields)
        if kind == "attempt_finished" and fields.get("classification") == "OK" and fields.get("model_returned") not in (None, self.frozen_model):
            raise Halt(EXIT_IDENTITY, f"model_returned {fields.get('model_returned')} != frozen {self.frozen_model}")

    # ------------------------------------------------------------------ one logical call with the single repair rule
    def _logical_call(self, arm: str, call: int, prompt: str, previous: list[dict[str, Any]], ctx: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
        schema_name, schema = P.SCHEMAS[(arm, call)]
        attempts: list[str] = []
        reason = None
        for repair in (False, True):
            text = prompt if not repair else f"{prompt}\n\n{REPAIR_SENTENCE.format(reason=reason)}"
            try:
                outcome = self.client.complete(P.SYSTEM_MESSAGE, text, schema_name, schema, {**ctx, "repair": repair})
                attempts += outcome.attempts
                validated = P.validate_output(arm, call, outcome.payload, previous)
                self.ledger.event("logical_call", ok=True, repair_used=repair, **ctx)
                return outcome.payload, validated, attempts
            except (X.InvalidOutput, P.OutputInvalid) as exc:
                reason = str(exc)[:200]
                self.ledger.event("logical_call", ok=False, repair_used=repair, error=type(exc).__name__, reason=reason, **ctx)
        raise FinalInvalid(reason or "invalid output")

    # ------------------------------------------------------------------ one trial
    def _run_trial(self, case: dict[str, Any], arm: str) -> str:
        tdir = self.paths.trial(case["case_id"], arm)
        previous: list[dict[str, Any]] = []
        k = 1
        while (tdir / f"call_{k}.json").exists():
            previous.append(read_json_strict(tdir / f"call_{k}.json")["output"])
            k += 1
        ctx_base = {"set": self.set, "case_id": case["case_id"], "arm": arm}
        status, failure = "COMPLETE", None
        for call in range(k, P.CALLS_PER_ARM[arm] + 1):
            ctx = {**ctx_base, "call": call}
            prompt = P.build_prompt(arm, call, case, previous)
            try:
                raw, validated, attempts = self._logical_call(arm, call, prompt, previous, ctx)
            except FinalInvalid as exc:
                status, failure = "FAILED_OUTPUT", str(exc)
                break
            except X.InfrastructureFailure as exc:
                status, failure = "FAILED_INFRA", str(exc)[:300]
                break
            atomic_write_json(tdir / f"call_{call}.json", {"output": raw, "validated": validated, "attempt_uids": attempts,
                                                            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
            previous.append(raw)
        final = None
        if status == "COMPLETE":
            last = read_json_strict(tdir / f"call_{P.CALLS_PER_ARM[arm]}.json")["validated"]
            final = {"mechanism_id": last["mechanism_id"], "probabilities_normalized": last["probabilities_normalized"]}
        calls_completed = len(previous)
        atomic_write_json(tdir / "trial_result.json", {"case_id": case["case_id"], "arm": arm, "status": status,
                                                       "failure": failure, "calls_completed": calls_completed, "final": final,
                                                       "terminal_at_utc": now()})
        self.ledger.event("trial_terminal", status=status, calls_completed=calls_completed, **ctx_base)
        return status

    # ------------------------------------------------------------------ reconciliation
    def _reconcile_orphans(self) -> None:
        started = {r["attempt_uid"]: r for r in self.ledger.rows if r["event"] == "attempt_started"}
        finished = {r["attempt_uid"] for r in self.ledger.rows if r["event"] == "attempt_finished"}
        recorded = {r["attempt_uid"] for r in self.ledger.rows if r["event"] == "orphan_attempt_recorded"}
        for uid, row in started.items():
            if uid not in finished and uid not in recorded:
                self.ledger.event("orphan_attempt_recorded", attempt_uid=uid, case_id=row.get("case_id"), arm=row.get("arm"),
                                  call=row.get("call"), note="attempt started but never finished (process ended mid-call); tokens unknown")

    def _check_duplicates(self) -> None:
        seen: set[tuple[str, str]] = set()
        for r in self.ledger.rows:
            if r["event"] == "trial_terminal":
                key = (r["case_id"], r["arm"])
                if key in seen:
                    raise CorruptRecord(f"duplicate terminal event for {key}")
                seen.add(key)
                if not (self.paths.trial(*key) / "trial_result.json").exists():
                    raise CorruptRecord(f"terminal event without terminal marker for {key}")

    # ------------------------------------------------------------------ main loop
    def run(self) -> int:
        if self.paths.report.exists():
            print("Final report exists; refusing to re-run or overwrite.", flush=True)
            return EXIT_OVERWRITE
        try:
            acquire_lock(self.paths.lock)
        except Halt as h:
            print(h, flush=True)
            return h.code
        try:
            try:
                scan_state(self.paths)
                self.ledger = Ledger(self.paths.ledger, uuid.uuid4().hex)
                self._check_duplicates()
            except CorruptRecord as exc:
                print(f"CORRUPT STATE: {exc}", flush=True)
                return EXIT_CORRUPT
            self.client, version = self.client_factory(self._on_event, self.paths)
            self.ledger.event("session_start", set=self.set, cli_version=version, protocol_sha256=self.protocol_digest,
                              tasks_sha256=self.tasks_sha, model=self.frozen_model)
            self._reconcile_orphans()
            if self.probe and hasattr(self.client, "calibration_probe"):
                append_jsonl(self.paths.calibration, {"at_utc": now(), "cli_version": version, **self.client.calibration_probe()})
            for case in self.cases:
                for arm in arm_order(case["case_id"]):
                    if (self.paths.trial(case["case_id"], arm) / "trial_result.json").exists():
                        continue
                    status = self._run_trial(case, arm)
                    self.recent_terminal = (self.recent_terminal + [status])[-INFRA_WINDOW:]
                    if self.recent_terminal.count("FAILED_INFRA") >= INFRA_LIMIT:
                        self.ledger.event("run_halted", reason="infrastructure failure threshold")
                        return EXIT_INFRA_HALT
            self.ledger.event("all_trials_terminal", set=self.set)
            return 0
        except (X.QuotaPause, X.AuthPause) as stop:
            self.ledger.event("session_paused", reason=type(stop).__name__, detail=str(stop)[:200])
            print(f"PAUSED ({type(stop).__name__}); re-run the same command to resume.", flush=True)
            return EXIT_PAUSED
        except Halt as h:
            self.ledger.event("run_halted", reason=str(h))
            return h.code
        finally:
            self.paths.lock.unlink(missing_ok=True)


# ---------------------------------------------------------------------- live client factory
def live_client_factory(on_event: Callable[..., None], paths: Paths) -> tuple[Any, str]:
    cli = X.find_cli()
    version = X.cli_version(cli, cwd=paths.cli_cwd if paths.cli_cwd.exists() else None)
    client = X.ClaudeCLI(paths.cli_cwd, paths.archive, on_event, cli=cli, cli_version=version)

    def calibration_probe() -> dict[str, Any]:
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
        code, out, _ = X.default_runner(client.argv(P.SYSTEM_MESSAGE, schema), "Return {\"ok\": true}.", X.child_env(), paths.cli_cwd, 300)
        try:
            usage = X.usage_of(__import__("json").loads(out))
        except Exception:  # noqa: BLE001 - calibration is best-effort and non-experimental
            usage = {}
        return {"purpose": "fixed CLI overhead estimate (non-experimental)", **usage}

    client.calibration_probe = calibration_probe
    return client, version


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=("pilot", "main"), required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--confirm-live", action="store_true", help="required for any live Claude call")
    args = parser.parse_args()
    import e18_protocol
    if not e18_protocol.verify():
        sys.exit(EXIT_PROTOCOL)
    if not (args.run and args.confirm_live):
        sys.exit("Refusing: live runs require --run --confirm-live.")
    import json
    digest = (E18_DIR / "PROTOCOL.sha256").read_text().split()[0]
    manifest = json.loads((T.TASKS_DIR / "manifest.json").read_text(encoding="utf-8"))
    auth = X.auth_status(X.find_cli())
    if auth.get("authMethod") != "claude.ai":
        sys.exit(f"Subscription login required (authMethod=claude.ai); got {auth}")
    code = Runner(args.set, live_client_factory, protocol_digest=digest, tasks_sha=manifest[args.set]["public_sha256"]).run()
    if code == 0:
        import e18_analysis
        e18_analysis.write_report(args.set)
    sys.exit(code)


if __name__ == "__main__":
    main()
