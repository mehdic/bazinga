# Standalone dashboard server startup script (PowerShell)
# This script runs the pre-built standalone Next.js server

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DASHBOARD_DIR = Split-Path -Parent $SCRIPT_DIR

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

# Set default port
$PORT = if ($env:PORT) { $env:PORT } else { "3000" }
$HOSTNAME = if ($env:HOSTNAME) { $env:HOSTNAME } else { "localhost" }

# Pass through DATABASE_URL if set
if ($env:DATABASE_URL) {
    Write-Host "Using DATABASE_URL: $($env:DATABASE_URL)"
}

Write-Host "Starting standalone dashboard server on ${HOSTNAME}:${PORT}..."

# Set environment variables for Node.js
$env:PORT = $PORT
$env:HOSTNAME = $HOSTNAME

# Change to standalone directory and run server
Set-Location $STANDALONE_DIR
node server.js
