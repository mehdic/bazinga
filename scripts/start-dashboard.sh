#!/usr/bin/env bash

#
# BAZINGA Dashboard v2 Startup Script
# ====================================
# This script runs in the background to:
# 1. Check for pre-built standalone server (preferred)
# 2. Fall back to development mode if no standalone build
# 3. Auto-detect database path
#
# Safe to run multiple times - checks if server is already running
#

set -e

DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
DASHBOARD_PID_FILE="/tmp/bazinga-dashboard.pid"
DASHBOARD_LOG="/tmp/bazinga-dashboard.log"
DASHBOARD_DIR="bazinga/dashboard-v2"
USE_STANDALONE="false"

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

# Check for pre-built standalone server (preferred mode)
STANDALONE_SERVER="$DASHBOARD_DIR/.next/standalone/server.js"
if [ -f "$STANDALONE_SERVER" ]; then
    echo "$(date): Found pre-built standalone server" >> "$DASHBOARD_LOG"
    USE_STANDALONE="true"

    # Ensure static files are copied to standalone
    if [ -d "$DASHBOARD_DIR/.next/static" ] && [ ! -d "$DASHBOARD_DIR/.next/standalone/.next/static" ]; then
        echo "$(date): Copying static files to standalone..." >> "$DASHBOARD_LOG"
        mkdir -p "$DASHBOARD_DIR/.next/standalone/.next"
        cp -r "$DASHBOARD_DIR/.next/static" "$DASHBOARD_DIR/.next/standalone/.next/"
    fi

    # Copy public folder if exists
    if [ -d "$DASHBOARD_DIR/public" ] && [ ! -d "$DASHBOARD_DIR/.next/standalone/public" ]; then
        echo "$(date): Copying public folder to standalone..." >> "$DASHBOARD_LOG"
        cp -r "$DASHBOARD_DIR/public" "$DASHBOARD_DIR/.next/standalone/"
    fi
else
    echo "$(date): No standalone build found, using development mode" >> "$DASHBOARD_LOG"

    # Check if npm is available (only needed for dev mode)
    if ! command -v npm >/dev/null 2>&1; then
        echo "$(date): ERROR - npm not found, cannot start dashboard in dev mode" >> "$DASHBOARD_LOG"
        echo "$(date): Consider using a pre-built standalone dashboard package" >> "$DASHBOARD_LOG"
        exit 1
    fi

    # Check and install dependencies if needed (only for dev mode)
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
fi

# Auto-detect DATABASE_URL if not set
if [ -z "$DATABASE_URL" ]; then
    # Look for database in common locations (relative to script execution dir)
    if [ -f "bazinga/bazinga.db" ]; then
        export DATABASE_URL="$(pwd)/bazinga/bazinga.db"
        echo "$(date): Auto-detected DATABASE_URL=$DATABASE_URL" >> "$DASHBOARD_LOG"
    elif [ -f "../bazinga/bazinga.db" ]; then
        export DATABASE_URL="$(cd .. && pwd)/bazinga/bazinga.db"
        echo "$(date): Auto-detected DATABASE_URL=$DATABASE_URL (parent dir)" >> "$DASHBOARD_LOG"
    else
        echo "$(date): WARNING - Could not auto-detect database path" >> "$DASHBOARD_LOG"
        echo "$(date): Set DATABASE_URL environment variable if dashboard fails to load data" >> "$DASHBOARD_LOG"
    fi
else
    echo "$(date): Using provided DATABASE_URL=$DATABASE_URL" >> "$DASHBOARD_LOG"
fi

# Start dashboard server
if [ "$USE_STANDALONE" = "true" ]; then
    echo "$(date): Starting standalone Next.js server..." >> "$DASHBOARD_LOG"

    cd "$DASHBOARD_DIR/.next/standalone"
    PORT="$DASHBOARD_PORT" HOSTNAME="localhost" node server.js >> "$DASHBOARD_LOG" 2>&1 &
    DASHBOARD_PID=$!
    cd - > /dev/null

    # Note: Socket.io server needs to be started separately in standalone mode
    # For now, standalone mode only supports the main dashboard
    echo "$(date): Note: Real-time updates may be limited in standalone mode" >> "$DASHBOARD_LOG"
else
    echo "$(date): Starting Next.js dashboard + Socket.io server (dev mode)..." >> "$DASHBOARD_LOG"

    cd "$DASHBOARD_DIR"

    # Check if dev:all script exists in package.json
    if grep -q '"dev:all"' package.json 2>/dev/null; then
        npm run dev:all >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    else
        echo "$(date): dev:all not found, starting dev only..." >> "$DASHBOARD_LOG"
        npm run dev >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    fi
    cd ..
fi

# Save PID
echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if kill -0 $DASHBOARD_PID 2>/dev/null; then
    if [ "$USE_STANDALONE" = "true" ]; then
        echo "$(date): Dashboard server started successfully in STANDALONE mode (PID: $DASHBOARD_PID)" >> "$DASHBOARD_LOG"
        echo "$(date): Dashboard available at http://localhost:$DASHBOARD_PORT" >> "$DASHBOARD_LOG"
    else
        echo "$(date): Dashboard server started successfully in DEV mode (PID: $DASHBOARD_PID)" >> "$DASHBOARD_LOG"
        echo "$(date): Dashboard available at http://localhost:$DASHBOARD_PORT" >> "$DASHBOARD_LOG"
        echo "$(date): Socket.io server on port 3001 (real-time updates)" >> "$DASHBOARD_LOG"
    fi
else
    echo "$(date): ERROR - Failed to start dashboard server" >> "$DASHBOARD_LOG"
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
