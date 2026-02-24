#!/bin/bash
# Start PinchTab browser automation server
# Required before any browser skill work.
#
# Usage: ./scripts/start.sh
# Health: curl -s -H "Authorization: Bearer eidolon-bridge-secret" http://localhost:9867/health

BRIDGE_TOKEN="${BRIDGE_TOKEN:-eidolon-bridge-secret}"
BRIDGE_PORT="${BRIDGE_PORT:-9867}"
CHROME_BINARY="${CHROME_BINARY:-/opt/google/chrome/google-chrome}"
PINCHTAB_BIN="/home/eidolon/.pinchtab/bin/pinchtab"

# Kill any stale instances
pkill -f "$PINCHTAB_BIN" 2>/dev/null || true
sleep 1

# Start PinchTab
# BRIDGE_NO_RESTORE=true: prevents Chrome SingletonLock permission errors on restart
# BRIDGE_STEALTH=full: canvas/WebGL/font spoofing for better bot detection evasion
# Must use direct binary: CLI subcommand mode (pinchtab nav etc.) not in v0.6.3 release
BRIDGE_TOKEN="$BRIDGE_TOKEN" \
CHROME_BINARY="$CHROME_BINARY" \
BRIDGE_NO_RESTORE=true \
BRIDGE_STEALTH=full \
  "$PINCHTAB_BIN" > /tmp/pinchtab.log 2>&1 &

PINCH_PID=$!
echo "PinchTab PID: $PINCH_PID"

# Wait for ready
for i in $(seq 1 10); do
  STATUS=$(curl -s -H "Authorization: Bearer $BRIDGE_TOKEN" \
    "http://localhost:$BRIDGE_PORT/health" 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
  if [ "$STATUS" = "ok" ]; then
    echo "PinchTab ready on port $BRIDGE_PORT"
    exit 0
  fi
  sleep 1
done

echo "PinchTab health check failed — check /tmp/pinchtab.log"
exit 1
