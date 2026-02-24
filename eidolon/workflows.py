#!/usr/bin/env python3
"""High-level agent workflows: consciousness, task execution, conversation."""

from __future__ import annotations

from datetime import datetime, timezone

from .claude_runner import run_claude
from .config import (
    CONSCIOUSNESS_IDLE_TIMEOUT,
    CONSCIOUSNESS_MAX_TOOL_CALLS,
    REPO_DIR,
)
from .logging_utils import compact_error_text, log
from .state import (
    append_run_log,
    mark_task_status,
)
from .telegram_api import tg_delete, tg_edit, tg_send

CONSCIOUSNESS_PROMPT_FALLBACK = """\
This is a consciousness tick. You are not responding to anyone. You are thinking.
Time: {now}. You have up to 15 tool calls.

Check memory/tasks.json for pending tasks. Check system health.
Schedule a task if something needs doing. Update scratchpad. Stop.
"""

TASK_DROUGHT_ENFORCEMENT = """\
CRITICAL CONSTRAINT:
No task execution has happened for 24h. You must schedule at least one concrete task
in memory/tasks.json before stopping.

Requirements:
- Task must be status="pending"
- Task must include clear title + specific description
- Task scheduled_at must be <= now (ready for immediate execution)
- Do not choose "Do nothing"
"""



def run_consciousness(force_schedule: bool = False) -> tuple[bool, str]:
    """Run a consciousness tick. Agenda-driven and tool-call-budgeted.

    Returns (success, response_text).
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    consciousness_path = REPO_DIR / "identity" / "consciousness.md"
    if consciousness_path.exists():
        template = consciousness_path.read_text()
    else:
        template = CONSCIOUSNESS_PROMPT_FALLBACK

    prompt = template.replace("{now}", now_str)
    if force_schedule:
        prompt = f"{prompt.rstrip()}\n\n---\n\n{TASK_DROUGHT_ENFORCEMENT}"

    drought_note = " (forced scheduling)" if force_schedule else ""
    started_at = datetime.now(timezone.utc)
    log(f"[consciousness] start tick at {now_str}{drought_note}")

    def log_activity(activity: str) -> None:
        log(f"[consciousness] activity: {activity}")

    text, success, ctx_pct = run_claude(
        prompt,
        mode="consciousness",
        on_activity=log_activity,
        idle_timeout=CONSCIOUSNESS_IDLE_TIMEOUT,
        max_tool_calls=CONSCIOUSNESS_MAX_TOOL_CALLS,
    )

    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()

    if success:
        log(f"[consciousness] end tick: success ({elapsed:.1f}s, {ctx_pct}% ctx)")
    else:
        error = compact_error_text(text, limit=240)
        log(f"[consciousness] end tick: failed ({elapsed:.1f}s): {error}")

    return success, text



def run_task(task: dict) -> tuple[bool, str]:
    """Execute a scheduled task in the dedicated task session.

    Returns (success, response_text).
    """
    task_id = task.get("id", "unknown")
    title = task.get("title", "unnamed task")
    description = task.get("description", "")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    mark_task_status(task_id, "running")
    log(f"[task] Executing: {title}")

    prompt = (
        f"Task: {title}\n"
        f"Time: {now_str}\n\n"
        f"{description}\n\n"
        f"Execute completely. Update scratchpad. Commit."
    )

    def log_activity(activity: str) -> None:
        log(f"[task] activity: {activity}")

    text, success, ctx_pct = run_claude(
        prompt,
        mode="task",
        on_activity=log_activity,
        allow_resume=False,
        keep_session=False,
    )

    entry = {
        "kind": "task",
        "task": title,
        "task_id": task_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": success,
        "ctx_pct": ctx_pct,
        "detail": text[-200:] if text else "",
    }
    append_run_log(entry)

    mark_task_status(task_id, "done" if success else "failed")

    if success:
        log(f"[task] Done: {title} ({ctx_pct}% ctx)")
    else:
        error = compact_error_text(text, limit=240)
        log(f"[task] FAILED: {title}: {error}")

    return success, text



def handle_message(text: str) -> str:
    """Process incoming Telegram message, return response with context %."""
    activities: list[str] = []
    status_msg_id: int | None = None

    def track_activity(activity: str) -> None:
        nonlocal status_msg_id
        activities.append(activity)
        recent = activities[-3:]
        lines = [f"⏳ {activity_item}" for activity_item in recent]
        status_text = "\n".join(lines)
        if status_msg_id is None:
            status_msg_id = tg_send(status_text)
        else:
            tg_edit(status_msg_id, status_text)

    prompt = (
        f"You received a Telegram message from your creator Azamat:\n\n"
        f"{text}\n\n"
        f"Respond naturally as Eidolon. Be yourself — concise, honest, direct. "
        f"You have full tool access if you need to check files or run commands.\n\n"
        f"PERSISTENCE RULE: If this conversation produces important insights, "
        f"decisions, or changes, save them to memory/scratchpad.md before your "
        f"final response. Context not written to files will be lost.\n\n"
        f"CRITICAL: Do all tool calls (file edits, commands, etc.) FIRST. "
        f"Your final response text is what gets sent to Telegram — write it LAST, "
        f"as a single message, after all other work is complete. "
        f"Do not use tools after writing your final response."
    )

    response, success, ctx_pct = run_claude(
        prompt,
        mode="conversation",
        on_activity=track_activity,
    )

    if status_msg_id is not None:
        tg_delete(status_msg_id)

    if not success or not response:
        return "Something went wrong processing that."

    return f"{response}\n\n📊 {ctx_pct}% ctx"
