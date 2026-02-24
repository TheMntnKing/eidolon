#!/usr/bin/env python3
"""Claude CLI execution with streaming, session continuity, and compaction."""

from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    CONSCIOUSNESS_TOOLS,
    CONVERSATION_TOOLS,
    CONTEXT_ROTATION_PCT,
    MODEL,
    REPO_DIR,
    SEND_HARD_TIMEOUT,
    SEND_IDLE_TIMEOUT,
    TASK_TOOLS,
)
from .state import load_sessions, read_run_logs, run_kind, save_sessions, should_resume


# ── Stream-JSON + tool activity ────────────────────────────────

def _short_path(path: str) -> str:
    parts = Path(path).parts
    return "/".join(parts[-2:]) if len(parts) > 2 else path



def _truncate(text: str, n: int = 60) -> str:
    return text[:n] + "…" if len(text) > n else text



def extract_tool_activity(event: dict) -> str | None:
    """Extract human-readable tool activity from a stream event."""
    if event.get("type") != "assistant":
        return None

    content = event.get("message", {}).get("content", [])
    for item in content:
        if item.get("type") != "tool_use":
            continue

        name = item.get("name", "")
        inp = item.get("input", {})

        if name == "Read":
            return f"📖 {_short_path(inp.get('file_path', '...'))}"
        if name == "Glob":
            return f"🔍 {inp.get('pattern', '...')}"
        if name == "Grep":
            return f"🔍 grep '{_truncate(inp.get('pattern', '...'), 40)}'"
        if name == "Edit":
            return f"✏️ {_short_path(inp.get('file_path', '...'))}"
        if name == "Write":
            return f"📝 {_short_path(inp.get('file_path', '...'))}"
        if name == "Bash":
            desc = inp.get("description", "")
            label = desc if desc else _truncate(inp.get("command", "..."), 50)
            return f"⚡ {label}"
        if name == "WebSearch":
            return f"🌐 {_truncate(inp.get('query', '...'), 50)}"
        if name == "WebFetch":
            return f"🌐 {_truncate(inp.get('url', '...'), 50)}"
        if name == "Skill":
            return f"🛠 /{inp.get('skill', '...')} {inp.get('args', '')}".strip()
        if name == "Task":
            agent = inp.get("subagent_type", "")
            desc = inp.get("description", "...")
            return f"🤖 {agent}: {desc}" if agent else f"🤖 {desc}"
        return f"🔧 {name}"

    return None


# ── Process management ─────────────────────────────────────────

def _signal_proc(proc: subprocess.Popen, sig: int) -> None:
    if proc.poll() is not None:
        return

    pid = getattr(proc, "pid", None)
    if pid and hasattr(os, "killpg"):
        with suppress(ProcessLookupError):
            os.killpg(pid, sig)
        return

    if sig == signal.SIGTERM:
        with suppress(Exception):
            proc.terminate()
    else:
        with suppress(Exception):
            proc.kill()



def _terminate_proc(proc: subprocess.Popen) -> None:
    _signal_proc(proc, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass

    _signal_proc(proc, signal.SIGKILL)
    with suppress(Exception):
        proc.wait(timeout=1)



def _read_stream(stream, out_queue: queue.Queue) -> None:
    """Read lines from a stream into a queue. Runs in a thread."""
    try:
        for line in iter(stream.readline, ""):
            out_queue.put(line)
    finally:
        out_queue.put(None)


# ── Health invariants (LLM-first state surface) ────────────────

def build_health_status() -> str:
    """Generate dynamic health invariants for the system prompt."""
    lines = ["# Health (auto-generated)"]
    now = datetime.now(timezone.utc)
    lines.append(f"- Time: {now.strftime('%Y-%m-%d %H:%M UTC')}")

    run_logs = read_run_logs()
    task_logs = [entry for entry in run_logs if run_kind(entry) == "task"]
    today = now.strftime("%Y-%m-%d")

    if task_logs:
        last = task_logs[-1]
        status = "OK" if last.get("ok") else "FAILED"
        ctx = last.get("ctx_pct", "?")
        ts = last.get("ts", "")
        ts_short = ts[11:16] + " UTC" if len(ts) > 16 else ts
        lines.append(f"- Last task: {status} ({ctx}% ctx) at {ts_short}")

    task_ok = task_fail = 0
    for entry in task_logs:
        if not entry.get("ts", "").startswith(today):
            continue
        if entry.get("ok"):
            task_ok += 1
        else:
            task_fail += 1
    lines.append(f"- Tasks today: {task_ok} ok, {task_fail} failed")

    soul_path = REPO_DIR / "identity" / "soul.md"
    if soul_path.exists():
        mtime = datetime.fromtimestamp(soul_path.stat().st_mtime, tz=timezone.utc)
        age_hours = (now - mtime).total_seconds() / 3600
        if age_hours > 8:
            lines.append(f"- STALE IDENTITY: soul.md last modified {age_hours:.0f}h ago")
        else:
            lines.append(f"- soul.md modified: {age_hours:.1f}h ago")

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True,
            text=True,
            cwd=str(REPO_DIR),
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            commit_time = datetime.fromisoformat(result.stdout.strip())
            commit_age_h = (now - commit_time).total_seconds() / 3600
            if commit_age_h > 6:
                lines.append(f"- NO RECENT OUTPUT: last commit {commit_age_h:.0f}h ago")
            else:
                lines.append(f"- Last commit: {commit_age_h:.1f}h ago")
    except Exception:
        pass

    return "\n".join(lines)



def build_system_context() -> str:
    """Build system prompt from identity + constitution + operations + state."""
    parts = []
    for rel in (
        "identity/soul.md",
        "identity/constitution.md",
        "identity/system.md",
        "memory/scratchpad.md",
    ):
        path = REPO_DIR / rel
        if path.exists():
            parts.append(path.read_text().strip())

    parts.append(build_health_status())
    return "\n\n---\n\n".join(parts)


def _tools_for_mode(mode: str) -> tuple[str, ...]:
    if mode == "consciousness":
        return CONSCIOUSNESS_TOOLS
    if mode == "conversation":
        return CONVERSATION_TOOLS
    if mode == "task":
        return TASK_TOOLS
    return ()


def _append_mode_tools(cmd: list[str], mode: str) -> None:
    """Append strict tool pruning (`--tools`) for the current mode."""
    tools = _tools_for_mode(mode)
    if tools:
        cmd += ["--tools", ",".join(tools)]


COMPACTION_PROMPT = """\
Context rotation imminent — this session is ending. Before it closes, persist what matters.

1. Scan this conversation. What happened that isn't already in memory/scratchpad.md?
   Decisions made, new priorities, follow-ups, insights. Update scratchpad.md surgically —
   only modify sections touched in this conversation. Do NOT remove sections not discussed.
2. If identity shifted meaningfully this session, update identity/soul.md.
3. Git commit any changes.

Be surgical. Don't rewrite what's already there.
Output: one line confirming what you saved, or "nothing new to persist."
"""



def _run_compaction(session_id: str, mode: str) -> None:
    """Resume session, persist state to disk, then let it rotate."""
    print(f"[compaction] {mode} ctx at limit — persisting before rotation")

    cmd = [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--model",
        MODEL,
        "--resume",
        session_id,
        "-p",
        COMPACTION_PROMPT,
    ]
    _append_mode_tools(cmd, mode)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(REPO_DIR),
            start_new_session=True,
        )

        stream_q: queue.Queue = queue.Queue()
        threading.Thread(
            target=_read_stream,
            args=(proc.stdout, stream_q),
            daemon=True,
        ).start()

        started = time.monotonic()
        result = ""

        while True:
            if time.monotonic() - started >= 300:
                _terminate_proc(proc)
                print("[compaction] timed out")
                return

            try:
                line = stream_q.get(timeout=1.0)
            except queue.Empty:
                continue

            if line is None:
                break

            stripped = line.strip()
            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "result":
                result = event.get("result", "")

        proc.wait(timeout=10)
        print(f"[compaction] done — {result[:120]}")
    except Exception as exc:
        print(f"[compaction] error: {exc}")



def run_claude(
    prompt: str,
    mode: str = "task",
    on_activity=None,
    hard_timeout: int | None = None,
    idle_timeout: int | None = None,
    max_tool_calls: int | None = None,
    allow_resume: bool = True,
    keep_session: bool = True,
) -> tuple[str, bool, int]:
    """Run Claude CLI with streaming and session management.

    Returns (response_text, success, context_pct).
    on_activity: callback receiving tool activity strings.
    hard_timeout/idle_timeout: override defaults (seconds).
    max_tool_calls: terminate after this many tool invocations.
    allow_resume: if False, always start a fresh Claude session.
    keep_session: if False, do not persist session_id/context for reuse.
    """
    _hard_timeout = hard_timeout or SEND_HARD_TIMEOUT
    _idle_timeout = idle_timeout or SEND_IDLE_TIMEOUT

    sessions = load_sessions()
    session = sessions[mode]
    resuming = allow_resume and should_resume(session)
    now = datetime.now(timezone.utc)

    system_context = build_system_context()

    cmd = [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--model",
        MODEL,
        "--system-prompt",
        system_context,
    ]

    _append_mode_tools(cmd, mode)

    if resuming:
        cmd += ["--resume", session["session_id"]]

    cmd += ["-p", prompt]

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(REPO_DIR),
            start_new_session=True,
        )

        if proc.stdout is None or proc.stderr is None:
            _terminate_proc(proc)
            return "Subprocess pipes unavailable.", False, 0

        stream_q: queue.Queue = queue.Queue()
        stderr_lines: deque[str] = deque(maxlen=10)

        stdout_t = threading.Thread(
            target=_read_stream,
            args=(proc.stdout, stream_q),
            daemon=True,
        )
        stderr_t = threading.Thread(
            target=lambda: [
                stderr_lines.append(line.strip())
                for line in iter(proc.stderr.readline, "")
                if line.strip()
            ],
            daemon=True,
        )
        stdout_t.start()
        stderr_t.start()

        result_text = ""
        session_id = None
        context_pct = 0
        last_assistant_usage = None
        started_at = time.monotonic()
        last_output_at = started_at
        timed_out = None
        tool_call_count = 0

        while True:
            now_mono = time.monotonic()
            hard_left = _hard_timeout - (now_mono - started_at)
            idle_left = _idle_timeout - (now_mono - last_output_at)

            if hard_left <= 0:
                timed_out = f"{_hard_timeout}s total"
                break
            if idle_left <= 0:
                timed_out = f"{_idle_timeout}s idle"
                break

            try:
                line = stream_q.get(timeout=min(1.0, hard_left, idle_left))
            except queue.Empty:
                continue

            if line is None:
                break

            last_output_at = time.monotonic()
            stripped = line.strip()
            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            etype = event.get("type")

            if etype == "assistant":
                usage = event.get("message", {}).get("usage")
                if usage:
                    last_assistant_usage = usage

                activity = extract_tool_activity(event)
                if activity:
                    tool_call_count += 1
                    if on_activity:
                        on_activity(activity)
                    if max_tool_calls and tool_call_count >= max_tool_calls:
                        timed_out = f"tool call limit ({max_tool_calls})"
                        break

            if etype == "result":
                result_text = event.get("result", "")
                session_id = event.get("session_id")

                usage = last_assistant_usage or event.get("usage", {})
                total_tokens = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                )

                model_usage = event.get("modelUsage", {})
                ctx_window = next(iter(model_usage.values()), {}).get(
                    "contextWindow", 200_000
                )
                if ctx_window:
                    context_pct = round(total_tokens / ctx_window * 100)

        if timed_out:
            _terminate_proc(proc)
            stderr_text = "\n".join(stderr_lines) if stderr_lines else ""
            suffix = f" stderr: {stderr_text}" if stderr_text else ""
            return f"Timed out ({timed_out}).{suffix}", False, 0

        proc.wait(timeout=10)

        if not result_text and proc.returncode != 0:
            stderr_text = "\n".join(stderr_lines) if stderr_lines else ""
            return f"CLI error (exit {proc.returncode}). {stderr_text}", False, 0

        if keep_session and session_id:
            session["session_id"] = session_id
        elif not keep_session:
            session["session_id"] = None
        session["last_interaction"] = now.isoformat()
        session["context_pct"] = context_pct if keep_session else 0

        if keep_session and context_pct >= CONTEXT_ROTATION_PCT:
            if session_id:
                _run_compaction(session_id, mode)
            session["session_id"] = None
            session["context_pct"] = 0

        sessions[mode] = session
        save_sessions(sessions)

        return result_text, True, context_pct

    except Exception as exc:
        return f"Error: {exc}", False, 0
    finally:
        if proc is not None and proc.poll() is None:
            _terminate_proc(proc)
