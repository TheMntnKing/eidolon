#!/usr/bin/env python3
"""Send messages to creator via Telegram Bot API."""

import json
import os
import sys
import urllib.parse
import urllib.request


def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to creator. Returns True on success."""
    token = os.environ.get("EIDOLON_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("EIDOLON_TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("[telegram] Not configured — need EIDOLON_TELEGRAM_BOT_TOKEN and EIDOLON_TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if not result.get("ok"):
                print(f"[telegram] API error: {result}")
                return False
            return True
    except Exception as e:
        print(f"[telegram] Send failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/telegram.py 'message'")
        sys.exit(1)
    msg = " ".join(sys.argv[1:])
    success = send_message(msg)
    sys.exit(0 if success else 1)
