#!/bin/bash
# fetch.sh — Convert any URL to clean Markdown via markdown.new (Cloudflare-powered)
# Usage: ./fetch.sh <url> [max_lines]
# Example: ./fetch.sh https://github.com/trending 100

set -euo pipefail

URL="${1:-}"
MAX_LINES="${2:-}"

if [ -z "$URL" ]; then
    echo "Usage: $0 <url> [max_lines]"
    echo "Example: $0 https://example.com 100"
    exit 1
fi

# Prepend markdown.new/ to the target URL
FETCH_URL="https://markdown.new/${URL}"

if [ -n "$MAX_LINES" ]; then
    curl -sL --max-time 30 "$FETCH_URL" | head -n "$MAX_LINES"
else
    curl -sL --max-time 30 "$FETCH_URL"
fi
