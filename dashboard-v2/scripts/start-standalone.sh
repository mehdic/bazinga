#!/bin/bash
# Standalone dashboard server startup script
# This script runs the pre-built standalone Next.js server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")"

# Check if standalone build exists
STANDALONE_DIR="$DASHBOARD_DIR/.next/standalone"
if [ ! -d "$STANDALONE_DIR" ]; then
    echo "Error: Standalone build not found at $STANDALONE_DIR"
    echo "Run 'npm run build' first to create the standalone build"
    exit 1
fi

# Copy static files if not already present (required for standalone)
if [ -d "$DASHBOARD_DIR/.next/static" ] && [ ! -d "$STANDALONE_DIR/.next/static" ]; then
    echo "Copying static files..."
    mkdir -p "$STANDALONE_DIR/.next"
    cp -r "$DASHBOARD_DIR/.next/static" "$STANDALONE_DIR/.next/"
fi

# Copy public folder if exists
if [ -d "$DASHBOARD_DIR/public" ] && [ ! -d "$STANDALONE_DIR/public" ]; then
    echo "Copying public folder..."
    cp -r "$DASHBOARD_DIR/public" "$STANDALONE_DIR/"
fi

# Set default port
PORT="${PORT:-3000}"
HOSTNAME="${HOSTNAME:-localhost}"

# Pass through DATABASE_URL if set
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL
fi

echo "Starting standalone dashboard server on $HOSTNAME:$PORT..."
cd "$STANDALONE_DIR"
exec node server.js
