#!/bin/bash
# Stop the supervised PinchTab instance (port 9868) and its keepalive loop.

PID_FILE="/tmp/pinchtab-supervised.pid"
KEEPALIVE_PID_FILE="/tmp/pinchtab-supervised-keepalive.pid"

# Stop keepalive loop
if [ -f "$KEEPALIVE_PID_FILE" ]; then
    KPID=$(cat "$KEEPALIVE_PID_FILE")
    if kill "$KPID" 2>/dev/null; then
        echo "Stopped keepalive (PID $KPID)"
    fi
    rm -f "$KEEPALIVE_PID_FILE"
fi

# Stop PinchTab
if [ ! -f "$PID_FILE" ]; then
    echo "No supervised instance running (no PID file)"
    exit 0
fi

PID=$(cat "$PID_FILE")
if kill "$PID" 2>/dev/null; then
    echo "Stopped supervised PinchTab (PID $PID)"
    rm -f "$PID_FILE"
else
    echo "Process $PID not found — already stopped"
    rm -f "$PID_FILE"
fi
