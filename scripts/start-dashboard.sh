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
    # Dashboard at: PROJECT_ROOT/bazinga/dashboard-v2
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
    DASHBOARD_DIR="$BAZINGA_DIR/dashboard-v2"
else
    # Development layout: PROJECT_ROOT/scripts/start-dashboard.sh
    # Dashboard at: PROJECT_ROOT/dashboard-v2 (not inside bazinga/)
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
    DASHBOARD_DIR="$PROJECT_ROOT/dashboard-v2"
fi

DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
DASHBOARD_PID_FILE="$BAZINGA_DIR/dashboard.pid"
DASHBOARD_LOG="$BAZINGA_DIR/dashboard.log"
USE_STANDALONE="false"

# Helper functions: log() writes to file only, msg() writes to both stdout and file
log() {
    echo "$(date): $1" >> "$DASHBOARD_LOG"
}
msg() {
    echo "$1"
    echo "$(date): $1" >> "$DASHBOARD_LOG"
}

# Safe rm -rf with path validation
safe_rm_rf() {
    local path="$1"
    # Validate path is non-empty and within expected directory
    if [ -z "$path" ] || [ "$path" = "/" ] || [ "$path" = "$HOME" ]; then
        log "ERROR: Refusing to remove unsafe path: $path"
        return 1
    fi
    # Ensure path is within DASHBOARD_DIR
    case "$path" in
        "$DASHBOARD_DIR"/*) rm -rf "$path" ;;
        *) log "ERROR: Path outside dashboard directory: $path"; return 1 ;;
    esac
}

# Redact credentials from database URLs (file paths pass through unchanged)
# Handles scheme URLs (postgres://user:pass@host) - file paths are passed through as-is
redact_db_url() {
    local url="$1"
    if [[ "$url" =~ :// ]]; then
        printf "%s" "$url" | sed -E 's#(://[^:]+):[^@]+@#\1:***@#'
    else
        printf "%s" "$url"
    fi
}

# Wait for server to be ready with health check
wait_for_server() {
    local pid="$1"
    local port="$2"
    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        # Check if process is still running
        if ! kill -0 "$pid" 2>/dev/null; then
            return 1  # Process died
        fi

        # Check if port is listening
        if command -v lsof >/dev/null 2>&1; then
            if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
                return 0  # Server ready
            fi
        elif command -v ss >/dev/null 2>&1; then
            if ss -lnt "sport == :$port" | grep -q LISTEN; then
                return 0
            fi
        else
            # Fallback: without network tools, check process stability
            # Don't return early - wait through all attempts to catch delayed crashes
            sleep 1
            if ! kill -0 "$pid" 2>/dev/null; then
                return 1  # Process died
            fi
            # Only return success on the last attempt if process survived
            if [ $attempt -eq $max_attempts ]; then
                return 0
            fi
        fi

        sleep 1
        attempt=$((attempt + 1))
    done

    # Final check - process alive means likely success
    kill -0 "$pid" 2>/dev/null
}

msg "🖥️  BAZINGA Dashboard v2 Startup"
log "Script dir: $SCRIPT_DIR, Project root: $PROJECT_ROOT"

# Support strict mode for CI that requires dashboard
STRICT="${DASHBOARD_STRICT:-0}"

# Check if dashboard folder exists FIRST (before other checks)
# Dashboard is an experimental feature - gracefully skip if not installed
if [ ! -d "$DASHBOARD_DIR" ]; then
    msg "⏭️  Dashboard not installed, skipping startup"
    msg "   (Dashboard is optional - no impact on BAZINGA functionality)"
    msg "   To install: bazinga setup-dashboard"
    [ "$STRICT" = "1" ] && exit 1 || exit 0
fi

# Check if Node.js is available (required for dashboard)
if ! command -v node >/dev/null 2>&1; then
    msg "⚠️  Node.js not found, cannot start dashboard"
    msg "   (Dashboard is optional - no impact on BAZINGA functionality)"
    msg "   To enable: install Node.js and run 'bazinga setup-dashboard'"
    [ "$STRICT" = "1" ] && exit 1 || exit 0
fi

# Check Node.js version (requires 18+)
NODE_VERSION=$(node --version 2>/dev/null | sed 's/^v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
if [ -n "$NODE_MAJOR" ] && [ "$NODE_MAJOR" -lt 18 ] 2>/dev/null; then
    msg "⚠️  Node.js 18+ required for dashboard (found v$NODE_VERSION)"
    msg "   (Dashboard is optional - no impact on BAZINGA functionality)"
    msg "   To enable: upgrade Node.js to 18+ and run 'bazinga setup-dashboard'"
    [ "$STRICT" = "1" ] && exit 1 || exit 0
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

# Check for pre-built standalone server (preferred mode)
STANDALONE_SERVER="$DASHBOARD_DIR/.next/standalone/server.js"
if [ -f "$STANDALONE_SERVER" ]; then
    msg "📦 Found pre-built standalone server"
    USE_STANDALONE="true"

    STANDALONE_NEXT="$DASHBOARD_DIR/.next/standalone/.next"
    SOURCE_NEXT="$DASHBOARD_DIR/.next"

    # Check if standalone is already complete (pre-packaged release)
    if [ -f "$STANDALONE_NEXT/BUILD_ID" ]; then
        log "Standalone build is pre-packaged and ready"

        # Check if source exists and differs (new local build)
        if [ -f "$SOURCE_NEXT/BUILD_ID" ] && ! cmp -s "$SOURCE_NEXT/BUILD_ID" "$STANDALONE_NEXT/BUILD_ID"; then
            msg "🔄 New build detected, syncing artifacts..."

            # Clean destination to avoid mixing versions (with validation)
            safe_rm_rf "$STANDALONE_NEXT" || { msg "❌ ERROR: Failed to clean standalone directory"; exit 1; }
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

            # Sync public folder (must update along with build artifacts)
            if [ -d "$DASHBOARD_DIR/public" ]; then
                safe_rm_rf "$DASHBOARD_DIR/.next/standalone/public" || true
                cp -r "$DASHBOARD_DIR/public" "$DASHBOARD_DIR/.next/standalone/"
            fi

            log "Build artifacts synced successfully"
        fi
    elif [ -f "$SOURCE_NEXT/BUILD_ID" ]; then
        # Source exists but standalone not ready - sync needed
        msg "🔄 Syncing build artifacts to standalone..."

        # Clean destination to avoid mixing versions (with validation)
        safe_rm_rf "$STANDALONE_NEXT" || { msg "❌ ERROR: Failed to clean standalone directory"; exit 1; }
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

        # Sync public folder (must update along with build artifacts)
        if [ -d "$DASHBOARD_DIR/public" ]; then
            safe_rm_rf "$DASHBOARD_DIR/.next/standalone/public" || true
            cp -r "$DASHBOARD_DIR/public" "$DASHBOARD_DIR/.next/standalone/"
        fi

        log "Build artifacts synced successfully"
    else
        # Neither source nor standalone has BUILD_ID - standalone is incomplete
        # Fall back to dev mode instead of failing
        msg "⚠️  Standalone build incomplete (missing BUILD_ID), falling back to dev mode..."
        msg "   Tip: run 'bazinga update --force' to fetch a complete standalone build"
        USE_STANDALONE="false"
    fi
fi

# Dev mode fallback or primary dev mode (when no standalone exists)
if [ "$USE_STANDALONE" != "true" ]; then
    # Only show this message if we didn't already show the fallback message
    if [ ! -f "$STANDALONE_SERVER" ]; then
        msg "🔧 No standalone build found, using development mode"
    fi

    # Check if npm is available (only needed for dev mode)
    if ! command -v npm >/dev/null 2>&1; then
        msg "⚠️  npm not found, cannot start dashboard in dev mode"
        msg "   (Dashboard is optional - no impact on BAZINGA functionality)"
        msg "   To enable: install npm, or download a pre-built dashboard package"
        [ "$STRICT" = "1" ] && exit 1 || exit 0
    fi

    # Check and install dependencies if needed (only for dev mode)
    if [ ! -d "$DASHBOARD_DIR/node_modules" ]; then
        msg "📥 Installing dashboard dependencies (npm install)..."

        cd "$DASHBOARD_DIR"
        # Use || pattern to handle failure with set -e
        if npm install >> "$DASHBOARD_LOG" 2>&1; then
            msg "   ✅ Dependencies installed successfully"
        else
            msg "❌ ERROR: npm install failed"
            msg "   Last few lines from log:"
            tail -5 "$DASHBOARD_LOG" 2>/dev/null | while read -r line; do msg "   $line"; done
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
        log "Auto-detected DATABASE_URL=$(redact_db_url "$DATABASE_URL")"
    else
        msg "⚠️  WARNING: No database found at $DB_PATH"
        msg "   Dashboard will start but won't show data until orchestration runs"
    fi
else
    log "Using provided DATABASE_URL=$(redact_db_url "$DATABASE_URL")"
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
        # Prepend NODE_PATH so socket server can find better-sqlite3 native module
        # Use prepend (not overwrite) to preserve existing NODE_PATH dependencies
        SOCKET_NODE_PATH="$DASHBOARD_DIR/node_modules"
        NODE_PATH="${SOCKET_NODE_PATH}${NODE_PATH:+:$NODE_PATH}" DATABASE_URL="$DATABASE_URL" SOCKET_PORT="$SOCKET_PORT" node "$SOCKET_SERVER" >> "$DASHBOARD_LOG" 2>&1 &
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

# Wait for server to be ready (health check with timeout)
msg "   Waiting for server to be ready..."
if wait_for_server "$DASHBOARD_PID" "$DASHBOARD_PORT"; then
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
    msg "   Last few lines from log:"
    tail -5 "$DASHBOARD_LOG" 2>/dev/null | while read -r line; do msg "   $line"; done
    msg ""
    rm -f "$DASHBOARD_PID_FILE"
    exit 1
fi
