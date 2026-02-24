#!/usr/bin/env python3
"""Main daemon loop orchestrating tasks, consciousness ticks, and Telegram."""

from __future__ import annotations

import time
import traceback
from datetime import datetime

from .config import (
    AUTO_TASKS_ENABLED,
    CONSCIOUSNESS_ENABLED,
    CONSCIOUSNESS_INTERVAL,
    TASK_DROUGHT_INTERVAL,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from .state import (
    get_next_due_task,
    load_sessions,
    load_tg_offset,
    mark_task_status,
    save_tg_offset,
)
from .logging_utils import log
from .telegram_api import tg_get_updates, tg_send, tg_send_chunked
from .workflows import handle_message, run_consciousness, run_task



def _load_timer(sessions: dict, key: str) -> float:
    """Load a timer from session.json, returning epoch timestamp or 0."""
    last = sessions.get(key, {}).get("last_interaction")
    if last:
        try:
            return datetime.fromisoformat(last).timestamp()
        except (ValueError, TypeError):
            pass
    return 0



def run_daemon() -> None:
    mode_parts = []
    if AUTO_TASKS_ENABLED:
        mode_parts.append("auto-tasks")
    if CONSCIOUSNESS_ENABLED:
        mode_parts.append(f"consciousness every {CONSCIOUSNESS_INTERVAL}s")
    if TELEGRAM_TOKEN:
        mode_parts.append("telegram")
    mode_desc = " + ".join(mode_parts) if mode_parts else "idle (nothing enabled)"

    log(f"[daemon] Starting. Mode: {mode_desc}")

    if not TELEGRAM_TOKEN:
        log("[daemon] WARNING: No Telegram token")

    sessions = load_sessions()
    last_task_run = _load_timer(sessions, "task")
    last_consciousness = _load_timer(sessions, "consciousness")
    tg_offset = load_tg_offset()

    while True:
        now = time.time()

        # --- Auto task execution (only when enabled) ---
        if AUTO_TASKS_ENABLED:
            task = get_next_due_task()
            if task:
                try:
                    run_task(task)  # returns (success, text); result ignored in auto mode
                except Exception as exc:
                    log(f"[daemon] Task error: {exc}")
                    traceback.print_exc()
                    mark_task_status(task.get("id", ""), "failed")
                last_task_run = time.time()

        # --- Consciousness ticks (only when enabled) ---
        if CONSCIOUSNESS_ENABLED and now - last_consciousness >= CONSCIOUSNESS_INTERVAL:
            drought = (now - last_task_run) >= TASK_DROUGHT_INTERVAL if last_task_run else True
            try:
                run_consciousness(force_schedule=drought)  # returns (success, text); result ignored in auto mode
            except Exception as exc:
                log(f"[daemon] Consciousness error: {exc}")
                traceback.print_exc()
            last_consciousness = time.time()

        # --- Telegram polling (always, if token exists) ---
        if TELEGRAM_TOKEN:
            try:
                updates = tg_get_updates(offset=tg_offset)
                for update in updates:
                    tg_offset = update["update_id"] + 1
                    save_tg_offset(tg_offset)

                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    text = message.get("text", "")

                    if chat_id != TELEGRAM_CHAT_ID or not text:
                        continue

                    log(f"[telegram] From Azamat: {text[:100]}")
                    try:
                        if text.strip().startswith("/tick"):
                            tg_send("Running consciousness tick...")
                            success, output = run_consciousness()
                            status = "Tick done." if success else "Tick failed."
                            if output:
                                tg_send_chunked(f"{status}\n\n{output}")
                            else:
                                tg_send(status)
                        elif text.strip().startswith("/task"):
                            task = get_next_due_task()
                            if task:
                                tg_send(f"Running task: {task.get('title', 'unnamed')}")
                                success, output = run_task(task)
                                status = "Task done." if success else "Task failed."
                                if output:
                                    tg_send_chunked(f"{status}\n\n{output}")
                                else:
                                    tg_send(status)
                            else:
                                tg_send("No pending tasks.")
                        else:
                            response = handle_message(text)
                            tg_send_chunked(response)
                    except Exception as exc:
                        log(f"[telegram] Error: {exc}")
                        traceback.print_exc()
                        tg_send("Something broke while thinking about that.")

            except Exception as exc:
                log(f"[telegram] Poll error: {exc}")
                time.sleep(5)
        else:
            time.sleep(60)
