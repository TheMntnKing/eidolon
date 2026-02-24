#!/usr/bin/env python3
"""State persistence helpers for sessions, tasks, logs, and offsets."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    CONTEXT_ROTATION_PCT,
    LOG_FILE,
    SESSION_FILE,
    SESSION_MODES,
    STALE_SESSION_HOURS,
    TASKS_FILE,
    TG_OFFSET_FILE,
)


# ── Session state ──────────────────────────────────────────────

def _default_session() -> dict:
    return {
        "session_id": None,
        "last_interaction": None,
        "context_pct": 0,
    }



def load_sessions() -> dict:
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            data = {}
    else:
        data = {}

    # Strip unknown keys (e.g. stale "heartbeat" from old format).
    for key in list(data.keys()):
        if key not in SESSION_MODES:
            del data[key]

    for mode in SESSION_MODES:
        data.setdefault(mode, _default_session())

    return data



def save_sessions(data: dict) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=SESSION_FILE.parent, suffix=".tmp", delete=False
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.rename(SESSION_FILE)



def is_stale(session: dict) -> bool:
    last = session.get("last_interaction")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        age_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
        return age_hours > STALE_SESSION_HOURS
    except (ValueError, TypeError):
        return True



def should_resume(session: dict) -> bool:
    return (
        session.get("session_id") is not None
        and not is_stale(session)
        and (session.get("context_pct", 0) < CONTEXT_ROTATION_PCT)
    )


# ── Task queue ─────────────────────────────────────────────────

def load_tasks() -> list:
    if TASKS_FILE.exists():
        try:
            data = json.loads(TASKS_FILE.read_text())
            return data.get("tasks", [])
        except (json.JSONDecodeError, IOError):
            return []
    return []



def save_tasks(tasks: list) -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=TASKS_FILE.parent, suffix=".tmp", delete=False
    ) as tmp:
        json.dump({"tasks": tasks}, tmp, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.rename(TASKS_FILE)



def get_next_due_task() -> dict | None:
    """Return highest-priority pending task whose scheduled_at has passed."""
    tasks = load_tasks()
    now = datetime.now(timezone.utc)
    pending: list[tuple[datetime, dict]] = []

    for task in tasks:
        if task.get("status") != "pending":
            continue
        try:
            scheduled = datetime.fromisoformat(task.get("scheduled_at", "2099-01-01"))
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            if scheduled <= now:
                pending.append((scheduled, task))
        except (ValueError, TypeError):
            continue

    if not pending:
        return None

    # Priority first, then oldest due time.
    _, next_task = min(pending, key=lambda item: (item[1].get("priority", 99), item[0]))
    return next_task



def mark_task_status(task_id: str, status: str) -> None:
    tasks = load_tasks()
    now_str = datetime.now(timezone.utc).isoformat()

    for task in tasks:
        if task.get("id") != task_id:
            continue

        task["status"] = status
        task["updated_at"] = now_str

        # Auto-reschedule recurring tasks on completion.
        if status == "done" and task.get("type") == "recurring":
            interval_h = task.get("interval_hours", 24)
            new_scheduled = datetime.now(timezone.utc).timestamp() + interval_h * 3600
            import uuid as _uuid

            tasks.append(
                {
                    "id": str(_uuid.uuid4())[:8],
                    "title": task.get("title", ""),
                    "description": task.get("description", ""),
                    "priority": task.get("priority", 2),
                    "scheduled_at": datetime.fromtimestamp(
                        new_scheduled, tz=timezone.utc
                    ).isoformat(),
                    "type": "recurring",
                    "interval_hours": interval_h,
                    "status": "pending",
                    "created_by": "recurrence",
                    "created_at": now_str,
                }
            )

    save_tasks(tasks)


# ── Telegram offset ────────────────────────────────────────────

def load_tg_offset() -> int:
    try:
        if TG_OFFSET_FILE.exists():
            return int(TG_OFFSET_FILE.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0



def save_tg_offset(offset: int) -> None:
    try:
        TG_OFFSET_FILE.write_text(str(offset))
    except IOError:
        pass


# ── Runtime log ────────────────────────────────────────────────

def append_run_log(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as fh:
        fh.write(json.dumps(entry) + "\n")



def read_run_logs() -> list[dict]:
    if not LOG_FILE.exists():
        return []

    entries: list[dict] = []
    for line in LOG_FILE.read_text().strip().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries



def run_kind(entry: dict) -> str:
    kind = entry.get("kind")
    if kind == "task":
        return kind

    # Backward compatibility for older logs without explicit kind.
    if "task" in entry or "task_id" in entry:
        return "task"
    return "unknown"
