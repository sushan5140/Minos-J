"""Session-independent supervisor tick for Experiment 17-C.

Invoked by the Windows Task Scheduler task "MinosJ-Experiment17C-Supervisor"
every 30 minutes (the scheduler never starts a second instance while one tick
is still running).  Each tick:

1. takes an exclusive lock (stale locks from dead processes are reclaimed);
2. exits if an Experiment 17-C ``--run`` process is already alive;
3. exits if the run is complete and independently validated;
4. runs the independent validator if the run is complete but unvalidated;
5. otherwise verifies the ledger parses, then runs the identical frozen
   command ``run_experiment_17c_claude_replication.py --run`` (resumable) and,
   on success, runs the independent validator immediately.

It never edits checkpoints, the ledger, the protocol or any Experiment 1-17
file.  Its own observations go to ``work/experiment_17c_supervisor.log`` and
``work/experiment_17c_checkpoints/supervisor_events.jsonl``.

``--selftest`` proves the scheduler context can run the pipeline: it records
the parent process chain, runs the preflight, and makes one tiny
non-experimental structured-output call (outside the ledger).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
WORK = PROJECT_DIR / "work"
LOG = WORK / "experiment_17c_supervisor.log"
RUN_LOG = WORK / "experiment_17c_run.log"
LOCK = WORK / "experiment_17c_tick.lock"
CHECKPOINTS = WORK / "experiment_17c_checkpoints"
EVENTS = CHECKPOINTS / "supervisor_events.jsonl"
REPORT = PROJECT_DIR / "outputs" / "meno_j_experiment_17c_matched_compute.json"
VALIDATION = PROJECT_DIR / "outputs" / "meno_j_experiment_17c_independent_validation.json"
RUNNER = "run_experiment_17c_claude_replication.py"
PY = sys.executable
OAUTH_LOCK = Path.home() / ".claude" / ".oauth_refresh.lock"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{now()} [pid {os.getpid()}] {message}\n")


def event(kind: str, **fields) -> None:
    CHECKPOINTS.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"event": kind, "at_utc": now(), **fields}, sort_keys=True) + "\n")


def processes() -> list[dict]:
    script = (
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine "
        "| ConvertTo-Json -Compress"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                         timeout=120).stdout
    data = json.loads(out or "[]")
    return data if isinstance(data, list) else [data]


def pid_alive(pid: int) -> bool:
    return any(p.get("ProcessId") == pid for p in processes())


def run_process_alive(procs: list[dict]) -> list[int]:
    return [p["ProcessId"] for p in procs
            if (p.get("Name") or "").lower().startswith("python") and RUNNER in (p.get("CommandLine") or "")
            and "--run" in (p.get("CommandLine") or "")]


def acquire_lock() -> bool:
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            holder = int(LOCK.read_text().strip() or 0)
        except ValueError:
            holder = 0
        if holder and pid_alive(holder):
            return False
        log(f"reclaiming stale tick lock held by dead pid {holder}")
        LOCK.unlink(missing_ok=True)
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return True


def checkpoints_ok() -> bool:
    """Historical pipeline stage checkpoints are written non-atomically; a kill
    mid-write would leave truncated JSON that fails the unit on resume.  Refuse
    to resume instead, so the operator can inspect it (nothing is deleted)."""
    bad = []
    for path in CHECKPOINTS.glob("*/**/*.json"):
        if "diagnostic_responses" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            bad.append(path.relative_to(CHECKPOINTS).as_posix())
    if bad:
        log(f"UNREADABLE CHECKPOINTS {bad}; refusing to resume (needs operator review)")
        event("checkpoint_unreadable", files=bad)
    return not bad


def ledger_ok() -> bool:
    path = CHECKPOINTS / "request_ledger.jsonl"
    if not path.exists():
        return True
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                json.loads(line)
            except json.JSONDecodeError:
                log(f"LEDGER LINE {number} IS NOT VALID JSON; refusing to resume (needs operator review)")
                event("ledger_unreadable", line=number)
                return False
    return True


def note_unclean_termination() -> None:
    """If the last ledger session never paused or finished, the previous process died mid-run."""
    path = CHECKPOINTS / "request_ledger.jsonl"
    if not path.exists():
        return
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    sessions = [r for r in rows if r.get("event") == "session_start"]
    if not sessions:
        return
    last = sessions[-1]
    later = [r for r in rows if r.get("resume_session_id") == last.get("resume_session_id")]
    paused = any(r.get("event") == "session_paused" for r in later)
    tail = RUN_LOG.read_text(encoding="utf-8", errors="replace")[-4000:] if RUN_LOG.exists() else ""
    finished = "Verdict:" in tail
    recorded = EVENTS.exists() and last["resume_session_id"] in EVENTS.read_text(encoding="utf-8")
    if not paused and not finished and not recorded:
        event("unclean_termination_detected", resume_session_id=last["resume_session_id"],
              last_seq=rows[-1].get("seq"),
              note="Previous run process ended without pausing or finishing; a request in flight at that "
                   "moment may have consumed tokens that are absent from the ledger.")
        log(f"unclean termination of session {last['resume_session_id']} recorded")


def clear_stale_oauth_lock(procs: list[dict]) -> None:
    if not OAUTH_LOCK.exists():
        return
    age = time.time() - OAUTH_LOCK.stat().st_mtime
    headless = [p for p in procs if (p.get("Name") or "").lower() == "claude.exe" and " -p " in (p.get("CommandLine") or "")]
    if (age > 1800 or age < -60) and not headless:
        try:
            OAUTH_LOCK.rmdir()
            log(f"removed stale empty OAuth refresh lock (age {int(age)} s)")
            event("stale_oauth_lock_removed", age_seconds=int(age))
        except OSError as exc:
            log(f"could not remove OAuth lock: {exc}")


def run(args: list[str], log_path: Path) -> int:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"=== supervisor tick {now()} :: {' '.join(args)}\n")
        handle.flush()
        code = subprocess.run([PY, "-u", *args], cwd=PROJECT_DIR, stdout=handle, stderr=subprocess.STDOUT).returncode
        handle.write(f"=== exit {code} {now()}\n")
    return code


def validate() -> int:
    code = run(["work/validate_experiment_17c_results.py"], RUN_LOG)
    log(f"independent validator exit {code}")
    event("independent_validation_run", exit_code=code)
    return code


def selftest() -> int:
    procs = {p["ProcessId"]: p for p in processes()}
    chain, pid = [], os.getpid()
    for _ in range(6):
        p = procs.get(pid)
        if not p:
            break
        chain.append({"pid": pid, "name": p.get("Name")})
        pid = p.get("ParentProcessId")
    sys.path.insert(0, str(PROJECT_DIR))
    import experiment_17c_claude_runtime as rt
    cli = rt.find_cli()
    auth = rt.auth_status(cli)
    schema = {"type": "object", "properties": {"answer": {"type": "integer"}}, "required": ["answer"],
              "additionalProperties": False}
    client = rt.ClaudeCodeCLIClient(rt.GENERATOR_MODEL, WORK / "experiment_17c_selftest_diagnostics", cli_path=cli)
    code, out, _ = rt.default_runner(client._argv("Return valid JSON only.", schema),
                                     'Return an object with key "answer" set to 2+2.', rt.child_env(),
                                     rt.ISOLATED_CWD, 300)
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        result = {"unparsed": out[-300:]}
    record = {
        "artifact": "Experiment 17-C supervisor self-test (non-experimental; not in the ledger)",
        "at_utc": now(), "process_chain": chain, "claude_session_env_present": any(k.startswith("CLAUDE") for k in os.environ),
        "cli": str(cli), "auth": auth, "exit_code": code,
        "structured_output": result.get("structured_output"), "is_error": result.get("is_error"),
        "error_text": result.get("result") if result.get("is_error") else None,
    }
    (WORK / "experiment_17c_supervisor_selftest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    log(f"selftest: parent chain {[c['name'] for c in chain]}, output {record['structured_output']}, error {record['error_text']}")
    return 0 if record["structured_output"] == {"answer": 4} else 1


def main() -> int:
    WORK.mkdir(exist_ok=True)
    if "--selftest" in sys.argv:
        return selftest()
    if not acquire_lock():
        log("another tick holds the lock; exiting")
        return 0
    try:
        procs = processes()
        alive = run_process_alive(procs)
        if alive:
            log(f"Experiment 17-C run already active (pid {alive}); nothing to do")
            return 0
        if REPORT.exists():
            if VALIDATION.exists():
                log("run complete and validated; nothing to do")
                return 0
            return validate()
        if not ledger_ok() or not checkpoints_ok():
            return 2
        note_unclean_termination()
        clear_stale_oauth_lock(procs)
        log("starting/resuming Experiment 17-C run")
        code = run([RUNNER, "--run"], RUN_LOG)
        log(f"run exit {code}")
        event("run_process_exit", exit_code=code)
        if code == 0 and REPORT.exists():
            return validate()
        return code
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
