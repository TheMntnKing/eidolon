#!/usr/bin/env bash
# Launch Claude interactively as Eidolon — same identity + tools as the daemon.
# Usage: ./shell.sh [mode]
#   mode: task (default, full tools), conversation, consciousness
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$REPO_DIR/.env" ]]; then
    set -a
    source "$REPO_DIR/.env"
    set +a
fi

MODEL="${EIDOLON_MODEL:-claude-sonnet-4-6}"
MODE="${1:-task}"

# Build system prompt (mirrors claude_runner.py build_system_context)
SYSTEM_PROMPT=""
for file in identity/soul.md identity/constitution.md identity/system.md memory/scratchpad.md; do
    path="$REPO_DIR/$file"
    if [[ -f "$path" ]]; then
        [[ -n "$SYSTEM_PROMPT" ]] && SYSTEM_PROMPT+=$'\n\n---\n\n'
        SYSTEM_PROMPT+="$(cat "$path")"
    fi
done

# Tool sets (mirrors config.py)
CORE="Read,Write,Edit,Glob,Grep,Bash"
TOOLS_CONSCIOUSNESS="${EIDOLON_TOOLS_CONSCIOUSNESS:-$CORE,WebFetch,WebSearch}"
TOOLS_CONVERSATION="${EIDOLON_TOOLS_CONVERSATION:-$CORE,WebFetch,Task,TaskOutput,TaskCreate,TaskUpdate,TaskStop}"

CMD=(claude --system-prompt "$SYSTEM_PROMPT" --model "$MODEL")

case "$MODE" in
    task)
        TOOLS="${EIDOLON_TOOLS_TASK:-}"
        [[ -n "$TOOLS" ]] && CMD+=(--tools "$TOOLS")
        ;;
    conversation)
        CMD+=(--tools "$TOOLS_CONVERSATION")
        ;;
    consciousness)
        CMD+=(--tools "$TOOLS_CONSCIOUSNESS")
        ;;
    *)
        echo "Unknown mode: $MODE (use task, conversation, consciousness)"
        exit 1
        ;;
esac

exec "${CMD[@]}"
