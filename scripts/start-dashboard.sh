#!/usr/bin/env bash

#
# BAZINGA Dashboard v2 Startup Script
# ====================================
# This script runs in the background to:
# 1. Check/install dashboard dependencies (npm install if needed)
# 2. Start the Next.js dashboard server
#
# Safe to run multiple times - checks if server is already running
#

set -e

DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
DASHBOARD_PID_FILE="/tmp/bazinga-dashboard.pid"
DASHBOARD_LOG="/tmp/bazinga-dashboard.log"
DASHBOARD_DIR="dashboard-v2"

echo "🖥️  BAZINGA Dashboard v2 Startup" >> "$DASHBOARD_LOG"
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
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "$(date): Dashboard v2 folder not found" >> "$DASHBOARD_LOG"
    exit 1
fi

# Check if npm is available
if ! command -v npm >/dev/null 2>&1; then
    echo "$(date): ERROR - npm not found, cannot start dashboard" >> "$DASHBOARD_LOG"
    exit 1
fi

# Check and install dependencies if needed
if [ ! -d "$DASHBOARD_DIR/node_modules" ]; then
    echo "$(date): Installing dashboard dependencies (npm install)..." >> "$DASHBOARD_LOG"

    cd "$DASHBOARD_DIR"
    npm install >> "$DASHBOARD_LOG" 2>&1

    if [ $? -eq 0 ]; then
        echo "$(date): Dependencies installed successfully" >> "$DASHBOARD_LOG"
    else
        echo "$(date): ERROR - npm install failed" >> "$DASHBOARD_LOG"
        exit 1
    fi
    cd ..
else
    echo "$(date): Dependencies already installed (node_modules exists)" >> "$DASHBOARD_LOG"
fi

# Start dashboard server (development mode)
echo "$(date): Starting Next.js dashboard server on port $DASHBOARD_PORT..." >> "$DASHBOARD_LOG"

cd "$DASHBOARD_DIR"

# Use npm run dev for development, or npm start for production
# Development mode provides hot reloading
npm run dev >> "$DASHBOARD_LOG" 2>&1 &
DASHBOARD_PID=$!
cd ..

# Save PID
echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if kill -0 $DASHBOARD_PID 2>/dev/null; then
    echo "$(date): Dashboard server started successfully (PID: $DASHBOARD_PID)" >> "$DASHBOARD_LOG"
    echo "$(date): Dashboard available at http://localhost:$DASHBOARD_PORT" >> "$DASHBOARD_LOG"
else
    echo "$(date): ERROR - Failed to start dashboard server" >> "$DASHBOARD_LOG"
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
