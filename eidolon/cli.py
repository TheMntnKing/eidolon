#!/usr/bin/env python3
"""CLI entrypoints for Eidolon daemon and one-shot commands."""

from __future__ import annotations

import sys

from .daemon import run_daemon
from .logging_utils import ensure_unbuffered_stdout
from .state import get_next_due_task, mark_task_status
from .telegram_api import tg_send
from .workflows import run_consciousness, run_task



def main(argv: list[str] | None = None) -> int:
    ensure_unbuffered_stdout()

    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        run_daemon()
        return 0

    subcmd = args[0]
    if subcmd == "talk":
        message = " ".join(args[1:]) if len(args) > 1 else ""
        if not message:
            print("Usage: python main.py talk 'message'")
            return 1
        tg_send(message)
        return 0

    if subcmd == "consciousness":
        success = run_consciousness()
        return 0 if success else 1

    if subcmd == "runtask":
        task = get_next_due_task()
        if not task:
            print("No pending tasks in memory/tasks.json")
            return 0
        print(f"Running task: {task.get('title', 'unnamed')}")
        try:
            success = run_task(task)
        except Exception as exc:
            print(f"Task failed: {exc}")
            mark_task_status(task.get("id", ""), "failed")
            return 1
        return 0 if success else 1

    print(f"Unknown command: {subcmd}")
    print("Usage: python main.py [consciousness|runtask|talk 'msg']")
    return 1
