#!/usr/bin/env bash

#
# BAZINGA Dashboard Startup Script
# =================================
# This script runs in the background to:
# 1. Check/install dashboard dependencies (if needed)
# 2. Start the dashboard server
#
# Safe to run multiple times - checks if server is already running
#

set -e

DASHBOARD_PORT="${DASHBOARD_PORT:-53124}"
DASHBOARD_PID_FILE="/tmp/bazinga-dashboard.pid"
DASHBOARD_LOG="/tmp/bazinga-dashboard.log"
DEPS_MARKER="dashboard/.deps-installed"

echo "🖥️  BAZINGA Dashboard Startup" >> "$DASHBOARD_LOG"
echo "$(date): Starting dashboard startup process..." >> "$DASHBOARD_LOG"

# Check if server is already running
if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
    echo "$(date): Dashboard server already running (PID: $(cat $DASHBOARD_PID_FILE))" >> "$DASHBOARD_LOG"
    exit 0
fi

# Check if port is in use by another process
if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "$(date): Port $DASHBOARD_PORT already in use by another process" >> "$DASHBOARD_LOG"
    exit 1
fi

# Check if dashboard folder exists
if [ ! -d "dashboard" ]; then
    echo "$(date): Dashboard folder not found" >> "$DASHBOARD_LOG"
    exit 1
fi

# Check and install dependencies if needed
if [ ! -f "$DEPS_MARKER" ]; then
    echo "$(date): Installing dashboard dependencies..." >> "$DASHBOARD_LOG"

    # Check if Python dependencies are installed
    if ! python3 -c "import flask, flask_sock, watchdog" 2>/dev/null; then
        echo "$(date): Installing Python packages..." >> "$DASHBOARD_LOG"

        # Install dependencies
        if command -v pip3 >/dev/null 2>&1; then
            pip3 install -q flask flask-sock watchdog anthropic 2>> "$DASHBOARD_LOG"

            # Create marker file
            touch "$DEPS_MARKER"
            echo "$(date): Dependencies installed successfully" >> "$DASHBOARD_LOG"
        else
            echo "$(date): ERROR - pip3 not found, cannot install dependencies" >> "$DASHBOARD_LOG"
            exit 1
        fi
    else
        # Dependencies are installed, create marker
        touch "$DEPS_MARKER"
        echo "$(date): Dependencies already available" >> "$DASHBOARD_LOG"
    fi
else
    echo "$(date): Dependencies already installed (marker exists)" >> "$DASHBOARD_LOG"
fi

# Start dashboard server
echo "$(date): Starting dashboard server on port $DASHBOARD_PORT..." >> "$DASHBOARD_LOG"

cd dashboard
python3 server.py >> "$DASHBOARD_LOG" 2>&1 &
DASHBOARD_PID=$!
cd ..

# Save PID
echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

# Wait a moment for server to start
sleep 2

# Check if server started successfully
if kill -0 $DASHBOARD_PID 2>/dev/null; then
    echo "$(date): Dashboard server started successfully (PID: $DASHBOARD_PID)" >> "$DASHBOARD_LOG"
    echo "$(date): Dashboard available at http://localhost:$DASHBOARD_PORT" >> "$DASHBOARD_LOG"
else
    echo "$(date): ERROR - Failed to start dashboard server" >> "$DASHBOARD_LOG"
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
