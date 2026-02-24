#!/bin/bash
# Stop the headless PinchTab instance (port 9867).

PINCHTAB_BIN="/home/eidolon/.pinchtab/bin/pinchtab"

if pkill -f "$PINCHTAB_BIN" 2>/dev/null; then
    echo "Stopped headless PinchTab"
else
    echo "No headless PinchTab running"
fi
