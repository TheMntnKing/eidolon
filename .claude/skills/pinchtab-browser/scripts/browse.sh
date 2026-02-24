#!/bin/bash
# Browser automation CLI wrapper using PinchTab HTTP API.
# Implements the core agent loop: navigate → snapshot → act → snapshot
#
# Usage:
#   ./browse.sh nav https://example.com
#   ./browse.sh snap                      # compact interactive snapshot
#   ./browse.sh snap full                 # full accessibility tree
#   ./browse.sh snap diff                 # changes since last snapshot
#   ./browse.sh click e0                  # click ref
#   ./browse.sh type e2 "hello world"     # type into ref
#   ./browse.sh fill e2 "search term"     # fill field (clears first)
#   ./browse.sh press Enter               # press key
#   ./browse.sh hover e3                  # hover over ref
#   ./browse.sh scroll e4                 # scroll to ref
#   ./browse.sh focus e5                  # focus ref
#   ./browse.sh select e6 "option"        # select dropdown option
#   ./browse.sh text                      # get page text
#   ./browse.sh ss                        # screenshot (saves to /tmp/screenshot.jpg)
#   ./browse.sh eval "document.title"     # run JS
#   ./browse.sh tabs                      # list tabs
#   ./browse.sh health                    # check server
#
# Env vars:
#   BRIDGE_PORT=9868     use supervised mode (default: 9867 headless)
#   BROWSE_TIMEOUT=60    curl timeout in seconds (default: 30)

TOKEN="${BRIDGE_TOKEN:-eidolon-bridge-secret}"
HOST="http://localhost:${BRIDGE_PORT:-9867}"
H="Authorization: Bearer $TOKEN"
T="--max-time ${BROWSE_TIMEOUT:-30}"

case "$1" in
  nav|navigate)
    curl -s $T -X POST "$HOST/navigate" -H "$H" -H "Content-Type: application/json" \
      -d "{\"url\": \"$2\"}" | python3 -m json.tool
    ;;
  snap|snapshot)
    if [ "$2" = "full" ]; then
      curl -s $T -H "$H" "$HOST/snapshot" | python3 -m json.tool
    elif [ "$2" = "diff" ]; then
      curl -s $T -H "$H" "$HOST/snapshot?diff=true&format=compact"
    else
      curl -s $T -H "$H" "$HOST/snapshot?filter=interactive&format=compact"
    fi
    ;;
  click)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"click\", \"ref\": \"$2\"}" | python3 -m json.tool
    ;;
  type)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"type\", \"ref\": \"$2\", \"value\": \"$3\"}" | python3 -m json.tool
    ;;
  fill)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"fill\", \"ref\": \"$2\", \"value\": \"$3\"}" | python3 -m json.tool
    ;;
  press)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"press\", \"value\": \"$2\"}" | python3 -m json.tool
    ;;
  hover)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"hover\", \"ref\": \"$2\"}" | python3 -m json.tool
    ;;
  scroll)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"scroll\", \"ref\": \"$2\"}" | python3 -m json.tool
    ;;
  focus)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"focus\", \"ref\": \"$2\"}" | python3 -m json.tool
    ;;
  select)
    curl -s $T -X POST "$HOST/action" -H "$H" -H "Content-Type: application/json" \
      -d "{\"kind\": \"select\", \"ref\": \"$2\", \"value\": \"$3\"}" | python3 -m json.tool
    ;;
  text)
    curl -s $T -H "$H" "$HOST/text" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('text',''))"
    ;;
  ss|screenshot)
    OUT="${2:-/tmp/screenshot.jpg}"
    curl -s $T -H "$H" "$HOST/screenshot" -o "$OUT" && echo "Screenshot saved to $OUT"
    ;;
  eval|evaluate)
    curl -s $T -X POST "$HOST/evaluate" -H "$H" -H "Content-Type: application/json" \
      -d "{\"expression\": \"$2\"}" | python3 -m json.tool
    ;;
  tabs)
    curl -s $T -H "$H" "$HOST/tabs" | python3 -m json.tool
    ;;
  health)
    curl -s $T -H "$H" "$HOST/health" | python3 -m json.tool
    ;;
  *)
    echo "Usage: $0 {nav|snap|click|type|fill|press|hover|scroll|focus|select|text|ss|eval|tabs|health} [args...]"
    exit 1
    ;;
esac
