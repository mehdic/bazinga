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

# Helper functions: log() writes to file only, msg() writes to both stdout and file
log() {
    echo "$(date): $1" >> "$DASHBOARD_LOG"
}
msg() {
    echo "$1"
    echo "$(date): $1" >> "$DASHBOARD_LOG"
}

msg "🖥️  BAZINGA Dashboard v2 Startup"
log "Script dir: $SCRIPT_DIR, Project root: $PROJECT_ROOT"

# Check if Node.js is available (required for standalone mode)
if ! command -v node >/dev/null 2>&1; then
    msg "❌ ERROR: node not found, cannot start dashboard"
    msg "   Please install Node.js and ensure it is in your PATH"
    exit 1
fi

# Check if server is already running
if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
    msg "✅ Dashboard already running (PID: $(cat "$DASHBOARD_PID_FILE"))"
    msg "   URL: http://localhost:$DASHBOARD_PORT"
    exit 0
fi

# Check if port is in use (try lsof, then ss, then netstat)
PORT_IN_USE=0
if command -v lsof >/dev/null 2>&1; then
    lsof -Pi :"$DASHBOARD_PORT" -sTCP:LISTEN -t >/dev/null 2>&1 && PORT_IN_USE=1
elif command -v ss >/dev/null 2>&1; then
    ss -lnt "sport == :$DASHBOARD_PORT" | grep -q LISTEN && PORT_IN_USE=1
elif command -v netstat >/dev/null 2>&1; then
    netstat -ln | grep -q ":$DASHBOARD_PORT " && PORT_IN_USE=1
fi

if [ "$PORT_IN_USE" -eq 1 ]; then
    msg "❌ ERROR: Port $DASHBOARD_PORT already in use by another process"
    msg "   Check what's using the port and stop it first"
    exit 1
fi

# Check if dashboard folder exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    msg "❌ ERROR: Dashboard v2 folder not found at $DASHBOARD_DIR"
    msg "   Run 'bazinga install' in your project root first"
    exit 1
fi

# Check for pre-built standalone server (preferred mode)
STANDALONE_SERVER="$DASHBOARD_DIR/.next/standalone/server.js"
if [ -f "$STANDALONE_SERVER" ]; then
    msg "📦 Found pre-built standalone server"
    USE_STANDALONE="true"

    STANDALONE_NEXT="$DASHBOARD_DIR/.next/standalone/.next"
    SOURCE_NEXT="$DASHBOARD_DIR/.next"

    # Check if BUILD_ID exists (required for Next.js to recognize a production build)
    if [ ! -f "$SOURCE_NEXT/BUILD_ID" ]; then
        msg "❌ ERROR: No BUILD_ID found - standalone build is incomplete"
        msg "   Run 'npm run build' in dashboard-v2 to create a proper build"
        exit 1
    fi

    # Check if we need to sync (destination missing OR build ID mismatch)
    SHOULD_SYNC="false"
    if [ ! -f "$STANDALONE_NEXT/BUILD_ID" ]; then
        SHOULD_SYNC="true"
    elif ! cmp -s "$SOURCE_NEXT/BUILD_ID" "$STANDALONE_NEXT/BUILD_ID"; then
        # Build IDs differ - new build detected
        SHOULD_SYNC="true"
    fi

    if [ "$SHOULD_SYNC" = "true" ]; then
        msg "🔄 Syncing build artifacts to standalone..."

        # Clean destination to avoid mixing versions
        rm -rf "$STANDALONE_NEXT"
        mkdir -p "$STANDALONE_NEXT"

        # Copy BUILD_ID and all manifest files
        cp "$SOURCE_NEXT/BUILD_ID" "$STANDALONE_NEXT/"
        for file in "$SOURCE_NEXT"/*.json; do
            [ -f "$file" ] && cp "$file" "$STANDALONE_NEXT/"
        done
        [ -f "$SOURCE_NEXT/prerender-manifest.js" ] && cp "$SOURCE_NEXT/prerender-manifest.js" "$STANDALONE_NEXT/"

        # Copy directories
        [ -d "$SOURCE_NEXT/static" ] && cp -r "$SOURCE_NEXT/static" "$STANDALONE_NEXT/"
        [ -d "$SOURCE_NEXT/server" ] && cp -r "$SOURCE_NEXT/server" "$STANDALONE_NEXT/"

        log "Build artifacts synced successfully"
    else
        log "Standalone artifacts are up to date"
    fi

    # Copy public folder if exists (separate from .next)
    if [ -d "$DASHBOARD_DIR/public" ] && [ ! -d "$DASHBOARD_DIR/.next/standalone/public" ]; then
        log "Copying public folder to standalone..."
        cp -r "$DASHBOARD_DIR/public" "$DASHBOARD_DIR/.next/standalone/"
    fi
else
    msg "🔧 No standalone build found, using development mode"

    # Check if npm is available (only needed for dev mode)
    if ! command -v npm >/dev/null 2>&1; then
        msg "❌ ERROR: npm not found, cannot start dashboard in dev mode"
        msg "   Consider using a pre-built standalone dashboard package"
        exit 1
    fi

    # Check and install dependencies if needed (only for dev mode)
    if [ ! -d "$DASHBOARD_DIR/node_modules" ]; then
        msg "📥 Installing dashboard dependencies (npm install)..."

        cd "$DASHBOARD_DIR"
        npm install >> "$DASHBOARD_LOG" 2>&1

        if [ $? -eq 0 ]; then
            msg "   ✅ Dependencies installed successfully"
        else
            msg "❌ ERROR: npm install failed"
            msg "   Check $DASHBOARD_LOG for details"
            exit 1
        fi
        cd - > /dev/null
    else
        log "Dependencies already installed (node_modules exists)"
    fi
fi

# Auto-detect DATABASE_URL if not set
if [ -z "$DATABASE_URL" ]; then
    # Look for database in project root bazinga folder
    DB_PATH="$PROJECT_ROOT/bazinga/bazinga.db"
    if [ -f "$DB_PATH" ]; then
        export DATABASE_URL="$DB_PATH"
        # Redact credentials only if DATABASE_URL is a connection string (not a file path)
        if [[ "$DATABASE_URL" =~ :// ]]; then
            redacted=$(printf "%s" "$DATABASE_URL" | sed -E 's#(://[^:]+):[^@]+@#\1:***@#')
        else
            redacted="$DATABASE_URL"
        fi
        log "Auto-detected DATABASE_URL=$redacted"
    else
        msg "⚠️  WARNING: No database found at $DB_PATH"
        msg "   Dashboard will start but won't show data until orchestration runs"
    fi
else
    # Redact credentials only if DATABASE_URL is a connection string (not a file path)
    if [[ "$DATABASE_URL" =~ :// ]]; then
        redacted=$(printf "%s" "$DATABASE_URL" | sed -E 's#(://[^:]+):[^@]+@#\1:***@#')
    else
        redacted="$DATABASE_URL"
    fi
    log "Using provided DATABASE_URL=$redacted"
fi

# Start dashboard server
msg "🚀 Starting dashboard server..."

if [ "$USE_STANDALONE" = "true" ]; then
    log "Starting standalone Next.js server..."

    cd "$DASHBOARD_DIR/.next/standalone"
    PORT="$DASHBOARD_PORT" HOSTNAME="localhost" node server.js >> "$DASHBOARD_LOG" 2>&1 &
    DASHBOARD_PID=$!
    cd - > /dev/null

    # Start Socket.io server if compiled version exists (for real-time updates)
    SOCKET_SERVER="$DASHBOARD_DIR/socket-server.js"
    if [ -f "$SOCKET_SERVER" ]; then
        log "Starting Socket.io server for real-time updates..."
        SOCKET_PORT="${SOCKET_PORT:-3001}"
        DATABASE_URL="$DATABASE_URL" SOCKET_PORT="$SOCKET_PORT" node "$SOCKET_SERVER" >> "$DASHBOARD_LOG" 2>&1 &
        SOCKET_PID=$!
        echo "$SOCKET_PID" > "$BAZINGA_DIR/socket.pid"
        log "Socket.io server started (PID: $SOCKET_PID) on port $SOCKET_PORT"
    else
        log "Note: Real-time updates limited (socket-server.js not found)"
    fi
else
    log "Starting Next.js dashboard + Socket.io server (dev mode)..."

    cd "$DASHBOARD_DIR"

    # Export PORT for dev mode
    export PORT="$DASHBOARD_PORT"

    # Check if dev:all script exists in package.json
    if grep -q '"dev:all"' package.json 2>/dev/null; then
        npm run dev:all >> "$DASHBOARD_LOG" 2>&1 &
        DASHBOARD_PID=$!
    else
        log "dev:all not found, starting dev only..."
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
if kill -0 "$DASHBOARD_PID" 2>/dev/null; then
    if [ "$USE_STANDALONE" = "true" ]; then
        log "Dashboard server started successfully in STANDALONE mode (PID: $DASHBOARD_PID)"
    else
        log "Dashboard server started successfully in DEV mode (PID: $DASHBOARD_PID)"
    fi
    msg ""
    msg "✅ Dashboard started successfully!"
    msg "   URL: http://localhost:$DASHBOARD_PORT"
    msg "   PID: $DASHBOARD_PID"
    msg "   Log: $DASHBOARD_LOG"
    msg ""
else
    msg ""
    msg "❌ ERROR: Failed to start dashboard server"
    msg "   Check $DASHBOARD_LOG for details"
    msg ""
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
