#!/usr/bin/env python3
"""Runtime configuration and repository paths for Eidolon."""

from __future__ import annotations

import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_DIR / "memory" / "heartbeat.log"
SCRATCHPAD = REPO_DIR / "memory" / "scratchpad.md"
SESSION_FILE = REPO_DIR / "memory" / "session.json"
TG_OFFSET_FILE = REPO_DIR / "memory" / "tg_offset.txt"
TASKS_FILE = REPO_DIR / "memory" / "tasks.json"



def _load_env() -> None:
    env_file = REPO_DIR / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
                val = val[1:-1]
            os.environ.setdefault(key, val)


_load_env()

TELEGRAM_TOKEN = os.environ.get("EIDOLON_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("EIDOLON_TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else ""

MODEL = os.environ.get("EIDOLON_MODEL", "claude-sonnet-4-6") or "claude-sonnet-4-6"


def _parse_tools(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Parse comma-separated tool names from env var, deduped and ordered."""
    raw = os.environ.get(name)
    if raw is None:
        return default

    parts: list[str] = []
    for item in raw.split(","):
        tool = item.strip()
        if not tool or tool in parts:
            continue
        parts.append(tool)

    return tuple(parts) if parts else default

# Autonomous mode flags — set to "1" or "true" in .env to enable
CONSCIOUSNESS_ENABLED = os.environ.get("EIDOLON_CONSCIOUSNESS_ENABLED", "").lower() in ("1", "true")
AUTO_TASKS_ENABLED = os.environ.get("EIDOLON_AUTO_TASKS_ENABLED", "").lower() in ("1", "true")

CONSCIOUSNESS_INTERVAL = 30 * 60
CONSCIOUSNESS_IDLE_TIMEOUT = 300
CONSCIOUSNESS_MAX_TOOL_CALLS = 25
TASK_DROUGHT_INTERVAL = 24 * 3600
TELEGRAM_POLL_TIMEOUT = 30
CONTEXT_ROTATION_PCT = 50
STALE_SESSION_HOURS = 24
SEND_HARD_TIMEOUT = 1800
SEND_IDLE_TIMEOUT = 1800
MAX_TELEGRAM_MSG = 4096

CORE_LOOP_TOOLS = ("Read", "Write", "Edit", "Glob", "Grep", "Bash")
WEB_TOOLS = ("WebFetch", "WebSearch")
TASK_MANAGEMENT_TOOLS = (
    "Task",
    "TaskOutput",
    "TaskCreate",
    "TaskUpdate",
    "TaskStop",
)

CONSCIOUSNESS_DEFAULT_TOOLS = CORE_LOOP_TOOLS + WEB_TOOLS
CONVERSATION_DEFAULT_TOOLS = CORE_LOOP_TOOLS + ("WebFetch",) + TASK_MANAGEMENT_TOOLS

CONSCIOUSNESS_TOOLS = _parse_tools(
    "EIDOLON_TOOLS_CONSCIOUSNESS",
    CONSCIOUSNESS_DEFAULT_TOOLS,
)
CONVERSATION_TOOLS = _parse_tools(
    "EIDOLON_TOOLS_CONVERSATION",
    CONVERSATION_DEFAULT_TOOLS,
)
# Empty means "do not pass --tools", i.e. keep full Claude toolset for task mode.
TASK_TOOLS = _parse_tools("EIDOLON_TOOLS_TASK", ())

SESSION_MODES = ("conversation", "consciousness", "task")
