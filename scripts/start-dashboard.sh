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

# Detect if script is in bazinga/scripts/ (installed) or scripts/ (development)
PARENT_DIR="$(basename "$(dirname "$SCRIPT_DIR")")"
if [ "$PARENT_DIR" = "bazinga" ]; then
    # Installed layout: PROJECT_ROOT/bazinga/scripts/start-dashboard.sh
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
else
    # Development layout: PROJECT_ROOT/scripts/start-dashboard.sh
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
fi

DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
DASHBOARD_PID_FILE="$BAZINGA_DIR/dashboard.pid"
DASHBOARD_LOG="$BAZINGA_DIR/dashboard.log"
DASHBOARD_DIR="$BAZINGA_DIR/dashboard-v2"
USE_STANDALONE="false"

# Terminal output function - shows on screen AND logs to file
log() {
    echo "$1"
    echo "$(date): $1" >> "$DASHBOARD_LOG"
}

log "🖥️  BAZINGA Dashboard v2 Startup"
log "Project root: $PROJECT_ROOT"
log "Dashboard dir: $DASHBOARD_DIR"

# Check if Node.js is available (required for standalone mode)
if ! command -v node >/dev/null 2>&1; then
    log "❌ ERROR: node not found. Please install Node.js."
    exit 1
fi

# Check if server is already running
if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
    log "✅ Dashboard already running (PID: $(cat $DASHBOARD_PID_FILE))"
    log "   URL: http://localhost:$DASHBOARD_PORT"
    exit 0
fi

# Check if port is in use by another process
if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    log "❌ ERROR: Port $DASHBOARD_PORT already in use by another process"
    exit 1
fi

# Check if dashboard folder exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    log "❌ ERROR: Dashboard folder not found at $DASHBOARD_DIR"
    log "   Run 'bazinga dashboard --install' first"
    exit 1
fi

# Check for pre-built standalone server (preferred mode)
STANDALONE_SERVER="$DASHBOARD_DIR/.next/standalone/server.js"
if [ -f "$STANDALONE_SERVER" ]; then
    log "📦 Using pre-built standalone server"
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
    log "🔧 No standalone build, using development mode"

    # Check if npm is available (only needed for dev mode)
    if ! command -v npm >/dev/null 2>&1; then
        log "❌ ERROR: npm not found, cannot start in dev mode"
        exit 1
    fi

    # Check and install dependencies if needed (only for dev mode)
    if [ ! -d "$DASHBOARD_DIR/node_modules" ]; then
        log "📥 Installing dependencies (npm install)..."

        cd "$DASHBOARD_DIR"
        npm install >> "$DASHBOARD_LOG" 2>&1

        if [ $? -eq 0 ]; then
            log "✅ Dependencies installed"
        else
            log "❌ ERROR: npm install failed. Check $DASHBOARD_LOG"
            exit 1
        fi
        cd - > /dev/null
    fi
fi

# Auto-detect DATABASE_URL if not set
if [ -z "$DATABASE_URL" ]; then
    DB_PATH="$PROJECT_ROOT/bazinga/bazinga.db"
    if [ -f "$DB_PATH" ]; then
        export DATABASE_URL="$DB_PATH"
        echo "$(date): Database found at $DB_PATH" >> "$DASHBOARD_LOG"
    else
        log "⚠️  Warning: Database not found at $DB_PATH"
    fi
fi

# Start dashboard server
log "🚀 Starting dashboard server..."

if [ "$USE_STANDALONE" = "true" ]; then
    cd "$DASHBOARD_DIR/.next/standalone"
    PORT="$DASHBOARD_PORT" HOSTNAME="localhost" node server.js >> "$DASHBOARD_LOG" 2>&1 &
    DASHBOARD_PID=$!
    cd - > /dev/null

    # Start Socket.io server if compiled version exists
    SOCKET_SERVER="$DASHBOARD_DIR/socket-server.js"
    if [ -f "$SOCKET_SERVER" ]; then
        SOCKET_PORT="${SOCKET_PORT:-3001}"
        DATABASE_URL="$DATABASE_URL" SOCKET_PORT="$SOCKET_PORT" node "$SOCKET_SERVER" >> "$DASHBOARD_LOG" 2>&1 &
        SOCKET_PID=$!
        echo $SOCKET_PID > "$BAZINGA_DIR/socket.pid"
    fi
else
    cd "$DASHBOARD_DIR"
    export PORT="$DASHBOARD_PORT"

    if grep -q '"dev:all"' package.json 2>/dev/null; then
        npm run dev:all >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    else
        npm run dev >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    fi
    cd - > /dev/null
fi

# Save PID
echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

# Wait for server to start
sleep 3

# Check if server started successfully
if kill -0 $DASHBOARD_PID 2>/dev/null; then
    log "✅ Dashboard started successfully!"
    log "   URL: http://localhost:$DASHBOARD_PORT"
    log "   PID: $DASHBOARD_PID"
    log "   Log: $DASHBOARD_LOG"
else
    log "❌ ERROR: Dashboard failed to start"
    log "   Check log: $DASHBOARD_LOG"
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
