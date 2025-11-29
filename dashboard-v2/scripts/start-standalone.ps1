# Standalone dashboard server startup script (PowerShell)
# This script runs the pre-built standalone Next.js server

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DASHBOARD_DIR = Split-Path -Parent $SCRIPT_DIR

# Check Node.js version (requires 18+)
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Node.js not found. Install Node.js 18+ and ensure it's in PATH." -ForegroundColor Red
    exit 1
}
$nodeVersion = (node --version) -replace '^v', ''
$majorVersion = [int]($nodeVersion -split '\.')[0]
if ($majorVersion -lt 18) {
    Write-Host "Error: Node.js 18+ required (found v$nodeVersion)" -ForegroundColor Red
    exit 1
}

# Check if standalone build exists
$STANDALONE_DIR = Join-Path $DASHBOARD_DIR ".next\standalone"
if (-not (Test-Path $STANDALONE_DIR)) {
    Write-Host "Error: Standalone build not found at $STANDALONE_DIR" -ForegroundColor Red
    Write-Host "Run 'npm run build' first to create the standalone build" -ForegroundColor Yellow
    exit 1
}

# Copy static files if not already present (required for standalone)
$STATIC_SRC = Join-Path $DASHBOARD_DIR ".next\static"
$STATIC_DEST = Join-Path $STANDALONE_DIR ".next\static"
if ((Test-Path $STATIC_SRC) -and (-not (Test-Path $STATIC_DEST))) {
    Write-Host "Copying static files..."
    $parentDir = Split-Path -Parent $STATIC_DEST
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    Copy-Item -Path $STATIC_SRC -Destination $STATIC_DEST -Recurse -Force
}

# Copy public folder if exists
$PUBLIC_SRC = Join-Path $DASHBOARD_DIR "public"
$PUBLIC_DEST = Join-Path $STANDALONE_DIR "public"
if ((Test-Path $PUBLIC_SRC) -and (-not (Test-Path $PUBLIC_DEST))) {
    Write-Host "Copying public folder..."
    Copy-Item -Path $PUBLIC_SRC -Destination $PUBLIC_DEST -Recurse -Force
}

# Set default port (DASHBOARD_PORT takes precedence over PORT for consistency)
# PS 5.1 compatible syntax (ternary-style requires PS 7+)
if ($env:DASHBOARD_PORT) { $PORT = $env:DASHBOARD_PORT }
elseif ($env:PORT) { $PORT = $env:PORT }
else { $PORT = "3000" }

if ($env:HOSTNAME) { $HOSTNAME = $env:HOSTNAME } else { $HOSTNAME = "localhost" }

# Pass through DATABASE_URL if set (mask path in logs for security)
if ($env:DATABASE_URL) {
    Write-Host "Using DATABASE_URL: [configured]"
}

# Start Socket.io server if exists (background process for real-time updates)
$SOCKET_SERVER = Join-Path $DASHBOARD_DIR "socket-server.js"
if (Test-Path $SOCKET_SERVER) {
    Write-Host "Starting Socket.io server for real-time updates..."
    if ($env:SOCKET_PORT) { $SOCKET_PORT = $env:SOCKET_PORT } else { $SOCKET_PORT = "3001" }
    $env:SOCKET_PORT = $SOCKET_PORT

    # Log to separate file for debugging (in standalone dir)
    $SOCKET_LOG = Join-Path $STANDALONE_DIR "socket.log"

    # Start as a hidden background process so it doesn't block the main server
    Start-Process -FilePath "node" -ArgumentList $SOCKET_SERVER `
        -RedirectStandardOutput $SOCKET_LOG -RedirectStandardError $SOCKET_LOG `
        -WindowStyle Hidden
    Write-Host "Socket.io server started on port $SOCKET_PORT (Log: $SOCKET_LOG)"
}

Write-Host "Starting standalone dashboard server on ${HOSTNAME}:${PORT}..."

# Set environment variables for Node.js
$env:PORT = $PORT
$env:HOSTNAME = $HOSTNAME

# Change to standalone directory and run server
Set-Location $STANDALONE_DIR
node server.js
