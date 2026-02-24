#!/usr/bin/env python3
"""Minimal logging helper: line-buffered stdout + timestamped log lines."""

from __future__ import annotations

import sys
from datetime import datetime, timezone



def ensure_unbuffered_stdout() -> None:
    """Force line-buffered stdout/stderr so journald sees logs immediately."""
    for stream in (sys.stdout, sys.stderr):
        if not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(line_buffering=True, write_through=True)
        except Exception:
            pass



def log(message: str) -> None:
    """Print one timestamped log line with flush enabled."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts} UTC] {message}", flush=True)



def compact_error_text(text: str, limit: int = 240) -> str:
    """Normalize and truncate error text for safe concise logs."""
    if not text:
        return ""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "…"
