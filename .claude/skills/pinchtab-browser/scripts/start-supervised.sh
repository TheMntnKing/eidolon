#!/bin/bash
# Start PinchTab in supervised mode (port 9868).
# Connects to Azamat's desktop Chrome via SSH reverse tunnel on localhost:9222.
# Runs alongside the headless instance (port 9867) without interfering.
#
# Azamat's steps (on his machine):
#   1. google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-remote-debug
#   2. ssh -o ServerAliveInterval=30 -J azamat@<JUMP_HOST> -R 9222:localhost:9222 eidolon@<VM_IP>
#      ^^^ ServerAliveInterval=30 keeps the tunnel alive — without it the CDP connection drops after ~2min idle
# Then tell Eidolon to run this script.
#
# Usage:    ./scripts/start-supervised.sh
# Interact: BRIDGE_PORT=9868 ./scripts/browse.sh nav https://example.com
# Stop:     ./scripts/stop-supervised.sh

BRIDGE_TOKEN="${BRIDGE_TOKEN:-eidolon-bridge-secret}"
BRIDGE_PORT="${BRIDGE_PORT:-9868}"
PINCHTAB_BIN="/home/eidolon/.pinchtab/bin/pinchtab"
PID_FILE="/tmp/pinchtab-supervised.pid"
KEEPALIVE_PID_FILE="/tmp/pinchtab-supervised-keepalive.pid"

# Check tunnel is up and Chrome is responding
echo "Checking tunnel to Azamat's Chrome on localhost:9222..."
CDP_RESPONSE=$(curl -s --max-time 5 "http://localhost:9222/json/version" 2>/dev/null)

if [ -z "$CDP_RESPONSE" ]; then
    echo "ERROR: Cannot reach localhost:9222 — tunnel not up or Chrome not running with debug port"
    echo ""
    echo "Azamat needs to:"
    echo "  1. Start Chrome: google-chrome --remote-debugging-port=9222 --user-data-dir=\$HOME/.chrome-remote-debug"
    echo "  2. SSH tunnel:   ssh -o ServerAliveInterval=30 -J azamat@<JUMP_HOST> -R 9222:localhost:9222 eidolon@<VM_IP>"
    exit 1
fi

CDP_URL=$(echo "$CDP_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['webSocketDebuggerUrl'])" 2>/dev/null)

if [ -z "$CDP_URL" ]; then
    echo "ERROR: Chrome responded but no webSocketDebuggerUrl found"
    echo "Chrome response: $CDP_RESPONSE"
    exit 1
fi

echo "Chrome found. CDP URL: $CDP_URL"

# Kill any existing supervised instance and keepalive
if [ -f "$KEEPALIVE_PID_FILE" ]; then
    KPID=$(cat "$KEEPALIVE_PID_FILE")
    kill "$KPID" 2>/dev/null
    rm -f "$KEEPALIVE_PID_FILE"
fi
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null && echo "Stopped previous supervised instance (PID $OLD_PID)"
    rm -f "$PID_FILE"
    sleep 1
fi

# Start PinchTab in supervised mode (no headless Chrome launch — uses CDP_URL)
BRIDGE_TOKEN="$BRIDGE_TOKEN" \
BRIDGE_PORT="$BRIDGE_PORT" \
CDP_URL="$CDP_URL" \
  "$PINCHTAB_BIN" > /tmp/pinchtab-supervised.log 2>&1 &

PINCH_PID=$!
echo "$PINCH_PID" > "$PID_FILE"
echo "Supervised PinchTab PID: $PINCH_PID"

# Wait for ready (health check through tunnel can take 3-5s on first call)
for i in $(seq 1 15); do
    STATUS=$(curl -s --max-time 8 -H "Authorization: Bearer $BRIDGE_TOKEN" \
        "http://localhost:$BRIDGE_PORT/health" 2>/dev/null \
        | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
    if [ "$STATUS" = "ok" ]; then
        # Start CDP keepalive — pings health every 30s to prevent idle tunnel timeout
        (
            while kill -0 "$PINCH_PID" 2>/dev/null; do
                sleep 30
                curl -s --max-time 5 -H "Authorization: Bearer $BRIDGE_TOKEN" \
                    "http://localhost:$BRIDGE_PORT/health" > /dev/null 2>&1
            done
        ) &
        KEEPALIVE_PID=$!
        echo "$KEEPALIVE_PID" > "$KEEPALIVE_PID_FILE"

        echo "Supervised PinchTab ready on port $BRIDGE_PORT"
        echo "CDP keepalive running (PID $KEEPALIVE_PID, every 30s)"
        echo ""
        echo "Use: BRIDGE_PORT=9868 ./scripts/browse.sh <command>"
        exit 0
    fi
    sleep 1
done

echo "Supervised PinchTab health check failed — check /tmp/pinchtab-supervised.log:"
cat /tmp/pinchtab-supervised.log
exit 1
