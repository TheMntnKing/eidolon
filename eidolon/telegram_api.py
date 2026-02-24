#!/usr/bin/env python3
"""Telegram API helpers and markdown->HTML conversion."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from .config import MAX_TELEGRAM_MSG, TELEGRAM_API, TELEGRAM_CHAT_ID, TELEGRAM_POLL_TIMEOUT


# ── Markdown → Telegram HTML ──────────────────────────────────

_HTML_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;"})



def _escape_html(text: str) -> str:
    return text.translate(_HTML_ESCAPE)



def _convert_text(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text



def _convert_inline(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    converted = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            converted.append(f"<code>{_escape_html(part[1:-1])}</code>")
        else:
            converted.append(_convert_text(part))
    return "".join(converted)



def md_to_tg_html(text: str) -> str:
    """Convert markdown to Telegram-compatible HTML."""
    parts = re.split(r"(```[\s\S]*?```)", text)
    result = []
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            inner = part[3:-3]
            if inner and inner[0] != "\n":
                inner = inner.split("\n", 1)[1] if "\n" in inner else ""
            result.append(f"<pre>{_escape_html(inner.strip())}</pre>")
        else:
            result.append(_convert_inline(part))
    return "".join(result)


# ── Telegram API ───────────────────────────────────────────────

def tg_request(method: str, params: dict | None = None, timeout: int = 35) -> dict:
    if not TELEGRAM_API:
        return {}

    url = f"{TELEGRAM_API}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}



def tg_send(text: str, parse_mode: str = "") -> int | None:
    """Send message. Returns message_id on success, None on failure."""
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if parse_mode:
        params["parse_mode"] = parse_mode
    result = tg_request("sendMessage", params, timeout=10)
    if result.get("ok"):
        return result.get("result", {}).get("message_id")
    return None



def tg_edit(message_id: int, text: str, parse_mode: str = "") -> bool:
    """Edit an existing message in place."""
    params = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "text": text}
    if parse_mode:
        params["parse_mode"] = parse_mode
    result = tg_request("editMessageText", params, timeout=10)
    return result.get("ok", False)



def tg_delete(message_id: int) -> bool:
    """Delete a message."""
    result = tg_request(
        "deleteMessage",
        {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id},
        timeout=10,
    )
    return result.get("ok", False)



def tg_send_html(text: str) -> int | None:
    """Send as HTML, fall back to plain text if parsing fails."""
    msg_id = tg_send(text, parse_mode="HTML")
    if msg_id is None:
        return tg_send(text)
    return msg_id



def tg_send_chunked(text: str) -> None:
    """Convert markdown->HTML and send in chunks."""
    html = md_to_tg_html(text)
    for i in range(0, len(html), MAX_TELEGRAM_MSG):
        chunk = html[i : i + MAX_TELEGRAM_MSG]
        tg_send_html(chunk)



def tg_get_updates(offset: int = 0) -> list:
    result = tg_request(
        "getUpdates",
        {
            "offset": offset,
            "timeout": TELEGRAM_POLL_TIMEOUT,
            "allowed_updates": json.dumps(["message"]),
        },
        timeout=TELEGRAM_POLL_TIMEOUT + 5,
    )
    return result.get("result", [])
