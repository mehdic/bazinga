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

# Derive paths from script location for robustness
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
BAZINGA_DIR="$PROJECT_ROOT/bazinga"
DASHBOARD_PID_FILE="$BAZINGA_DIR/dashboard.pid"
DASHBOARD_LOG="$BAZINGA_DIR/dashboard.log"
DASHBOARD_DIR="$BAZINGA_DIR/dashboard-v2"
USE_STANDALONE="false"

echo "🖥️  BAZINGA Dashboard v2 Startup" >> "$DASHBOARD_LOG"
echo "$(date): Starting dashboard startup process..." >> "$DASHBOARD_LOG"
echo "$(date): Script dir: $SCRIPT_DIR, Project root: $PROJECT_ROOT" >> "$DASHBOARD_LOG"

# Check if Node.js is available (required for standalone mode)
if ! command -v node >/dev/null 2>&1; then
    echo "$(date): ERROR - node not found, cannot start dashboard" >> "$DASHBOARD_LOG"
    echo "$(date): Please install Node.js and ensure it's in your PATH" >> "$DASHBOARD_LOG"
    exit 1
fi

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
        cd - > /dev/null
    else
        echo "$(date): Dependencies already installed (node_modules exists)" >> "$DASHBOARD_LOG"
    fi
fi

# Auto-detect DATABASE_URL if not set
if [ -z "$DATABASE_URL" ]; then
    # Look for database in project root bazinga folder
    DB_PATH="$PROJECT_ROOT/bazinga/bazinga.db"
    if [ -f "$DB_PATH" ]; then
        export DATABASE_URL="$DB_PATH"
        echo "$(date): Auto-detected DATABASE_URL=$DATABASE_URL" >> "$DASHBOARD_LOG"
    else
        echo "$(date): WARNING - Could not find database at $DB_PATH" >> "$DASHBOARD_LOG"
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

    # Start Socket.io server if compiled version exists (for real-time updates)
    SOCKET_SERVER="$DASHBOARD_DIR/socket-server.js"
    if [ -f "$SOCKET_SERVER" ]; then
        echo "$(date): Starting Socket.io server for real-time updates..." >> "$DASHBOARD_LOG"
        SOCKET_PORT="${SOCKET_PORT:-3001}"
        DATABASE_URL="$DATABASE_URL" SOCKET_PORT="$SOCKET_PORT" node "$SOCKET_SERVER" >> "$DASHBOARD_LOG" 2>&1 &
        SOCKET_PID=$!
        echo $SOCKET_PID > "$BAZINGA_DIR/socket.pid"
        echo "$(date): Socket.io server started (PID: $SOCKET_PID) on port $SOCKET_PORT" >> "$DASHBOARD_LOG"
    else
        echo "$(date): Note: Real-time updates limited (socket-server.js not found)" >> "$DASHBOARD_LOG"
    fi
else
    echo "$(date): Starting Next.js dashboard + Socket.io server (dev mode)..." >> "$DASHBOARD_LOG"

    cd "$DASHBOARD_DIR"

    # Export PORT for dev mode
    export PORT="$DASHBOARD_PORT"

    # Check if dev:all script exists in package.json
    if grep -q '"dev:all"' package.json 2>/dev/null; then
        npm run dev:all >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    else
        echo "$(date): dev:all not found, starting dev only..." >> "$DASHBOARD_LOG"
        npm run dev >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    fi
    cd - > /dev/null
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
