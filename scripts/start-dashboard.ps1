# BAZINGA Dashboard v2 Startup Script (PowerShell)
# ================================================
# This script runs in the background to:
# 1. Check for pre-built standalone server (preferred)
# 2. Fall back to development mode if no standalone build
# 3. Auto-detect database path
#
# Safe to run multiple times - checks if server is already running

$ErrorActionPreference = "Continue"

# Derive paths from script location for robustness
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Detect if script is in bazinga/scripts/ (installed) or scripts/ (development)
$PARENT_DIR = Split-Path -Leaf (Split-Path -Parent $SCRIPT_DIR)
if ($PARENT_DIR -eq "bazinga") {
    # Installed layout: PROJECT_ROOT/bazinga/scripts/start-dashboard.ps1
    # Dashboard at: PROJECT_ROOT/bazinga/dashboard-v2
    $PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
    $BAZINGA_DIR = Join-Path $PROJECT_ROOT "bazinga"
    $DASHBOARD_DIR = Join-Path $BAZINGA_DIR "dashboard-v2"
} else {
    # Development layout: PROJECT_ROOT/scripts/start-dashboard.ps1
    # Dashboard at: PROJECT_ROOT/dashboard-v2 (not inside bazinga/)
    $PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
    $BAZINGA_DIR = Join-Path $PROJECT_ROOT "bazinga"
    $DASHBOARD_DIR = Join-Path $PROJECT_ROOT "dashboard-v2"
}

# PS 5.1 compatible syntax (ternary-style requires PS 7+)
if ($env:DASHBOARD_PORT) { $DASHBOARD_PORT = $env:DASHBOARD_PORT } else { $DASHBOARD_PORT = "3000" }
$USE_STANDALONE = $false

# Determine log/pid file location - use BAZINGA_DIR if writable, else TEMP
function Test-DirectoryWritable {
    param([string]$Path)
    try {
        if (-not (Test-Path $Path)) { return $false }
        $testFile = Join-Path $Path ".write-test-$(Get-Random)"
        [System.IO.File]::WriteAllText($testFile, "test")
        Remove-Item $testFile -Force
        return $true
    } catch {
        return $false
    }
}

if (Test-DirectoryWritable $BAZINGA_DIR) {
    $DASHBOARD_PID_FILE = Join-Path $BAZINGA_DIR "dashboard.pid"
    $DASHBOARD_LOG = Join-Path $BAZINGA_DIR "dashboard.log"
} else {
    # Fallback to TEMP directory if BAZINGA_DIR is not writable
    $DASHBOARD_PID_FILE = Join-Path $env:TEMP "bazinga-dashboard.pid"
    $DASHBOARD_LOG = Join-Path $env:TEMP "bazinga-dashboard.log"
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $DASHBOARD_LOG -Value "$timestamp : $Message"
}

Write-Log "BAZINGA Dashboard v2 Startup (PowerShell)"
Write-Log "Starting dashboard startup process..."
Write-Log "Script dir: $SCRIPT_DIR, Project root: $PROJECT_ROOT"

# Check if dashboard folder exists FIRST (before other checks)
# Dashboard is an experimental feature - gracefully skip if not installed
if (-not (Test-Path $DASHBOARD_DIR)) {
    Write-Log "Dashboard not installed, skipping startup"
    Write-Host "Dashboard not installed, skipping startup" -ForegroundColor Yellow
    Write-Host "  (Dashboard is optional - no impact on BAZINGA functionality)" -ForegroundColor DarkGray
    Write-Host "  To install: bazinga setup-dashboard" -ForegroundColor DarkGray
    # Respect DASHBOARD_STRICT for CI that requires dashboard
    if ($env:DASHBOARD_STRICT -eq '1') { exit 1 } else { exit 0 }
}

# Check if Node.js is available (required for dashboard)
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Log "Node.js not found, cannot start dashboard"
    Write-Host "Node.js not found, cannot start dashboard" -ForegroundColor Yellow
    Write-Host "  (Dashboard is optional - no impact on BAZINGA functionality)" -ForegroundColor DarkGray
    Write-Host "  To enable: install Node.js and run 'bazinga setup-dashboard'" -ForegroundColor DarkGray
    # Respect DASHBOARD_STRICT for CI that requires dashboard
    if ($env:DASHBOARD_STRICT -eq '1') { exit 1 } else { exit 0 }
}

# Check Node.js version (requires 18+)
# Use regex guard to avoid [int] exception on nonstandard version strings
$nodeVersion = (node --version) -replace '^v', ''
if ($nodeVersion -match '^\d+') {
    $majorVersion = [int]$Matches[0]
} else {
    $majorVersion = $null
}
if (-not $majorVersion -or $majorVersion -lt 18) {
    Write-Log "Node.js 18+ required (found v$nodeVersion), skipping dashboard"
    Write-Host "Node.js 18+ required for dashboard (found v$nodeVersion)" -ForegroundColor Yellow
    Write-Host "  (Dashboard is optional - no impact on BAZINGA functionality)" -ForegroundColor DarkGray
    Write-Host "  To enable: upgrade Node.js to 18+ and run 'bazinga setup-dashboard'" -ForegroundColor DarkGray
    # Respect DASHBOARD_STRICT for CI that requires dashboard
    if ($env:DASHBOARD_STRICT -eq '1') { exit 1 } else { exit 0 }
}
Write-Log "Node.js version: v$nodeVersion"

# Check if server is already running
if (Test-Path $DASHBOARD_PID_FILE) {
    $existingPid = Get-Content $DASHBOARD_PID_FILE -ErrorAction SilentlyContinue
    if ($existingPid) {
        $process = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Log "Dashboard server already running (PID: $existingPid)"
            Write-Host "Dashboard server already running (PID: $existingPid)" -ForegroundColor Green
            exit 0
        }
    }
}

# Check if port is in use
function Test-PortInUse {
    param([int]$Port)
    try {
        if (Get-Command "Get-NetTCPConnection" -ErrorAction SilentlyContinue) {
            $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
            return $null -ne $conn
        }
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $false
    }
    catch {
        return $true
    }
}

if (Test-PortInUse -Port $DASHBOARD_PORT) {
    Write-Log "Port $DASHBOARD_PORT already in use by another process"
    Write-Host "Port $DASHBOARD_PORT already in use by another process" -ForegroundColor Yellow
    exit 1
}

# Check for pre-built standalone server (preferred mode)
$STANDALONE_SERVER = Join-Path $DASHBOARD_DIR ".next\standalone\server.js"
if (Test-Path $STANDALONE_SERVER) {
    Write-Log "Found pre-built standalone server"
    $USE_STANDALONE = $true

    # Ensure static files are copied to standalone
    $STATIC_SRC = Join-Path $DASHBOARD_DIR ".next\static"
    $STATIC_DEST = Join-Path $DASHBOARD_DIR ".next\standalone\.next\static"
    if ((Test-Path $STATIC_SRC) -and (-not (Test-Path $STATIC_DEST))) {
        Write-Log "Copying static files to standalone..."
        $parentDir = Split-Path -Parent $STATIC_DEST
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        Copy-Item -Path $STATIC_SRC -Destination $STATIC_DEST -Recurse -Force
    }

    # Copy public folder if exists
    $PUBLIC_SRC = Join-Path $DASHBOARD_DIR "public"
    $PUBLIC_DEST = Join-Path $DASHBOARD_DIR ".next\standalone\public"
    if ((Test-Path $PUBLIC_SRC) -and (-not (Test-Path $PUBLIC_DEST))) {
        Write-Log "Copying public folder to standalone..."
        Copy-Item -Path $PUBLIC_SRC -Destination $PUBLIC_DEST -Recurse -Force
    }
} else {
    Write-Log "No standalone build found, using development mode"

    # Check if npm is available (only needed for dev mode)
    if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
        Write-Log "npm not found, cannot start dashboard in dev mode"
        Write-Host "npm not found, cannot start dashboard in dev mode" -ForegroundColor Yellow
        Write-Host "  (Dashboard is optional - no impact on BAZINGA functionality)" -ForegroundColor DarkGray
        Write-Host "  To enable: install Node.js with npm, or download a pre-built dashboard package" -ForegroundColor DarkGray
        # Respect DASHBOARD_STRICT for CI that requires dashboard
        if ($env:DASHBOARD_STRICT -eq '1') { exit 1 } else { exit 0 }
    }

    # Check and install dependencies if needed (only for dev mode)
    $NODE_MODULES = Join-Path $DASHBOARD_DIR "node_modules"
    if (-not (Test-Path $NODE_MODULES)) {
        Write-Log "Installing dashboard dependencies (npm install)..."
        Write-Host "Installing dashboard dependencies..." -ForegroundColor Yellow

        Push-Location $DASHBOARD_DIR
        try {
            npm install 2>&1 | Out-File -Append $DASHBOARD_LOG
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Dependencies installed successfully"
                Write-Host "Dependencies installed successfully" -ForegroundColor Green
            } else {
                Write-Log "ERROR - npm install failed"
                Write-Host "ERROR - npm install failed" -ForegroundColor Red
                exit 1
            }
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Log "Dependencies already installed (node_modules exists)"
    }
}

# Auto-detect DATABASE_URL if not set
if (-not $env:DATABASE_URL) {
    $DB_PATH = Join-Path (Join-Path $PROJECT_ROOT "bazinga") "bazinga.db"
    if (Test-Path $DB_PATH) {
        $env:DATABASE_URL = $DB_PATH
        Write-Log "Auto-detected DATABASE_URL=[local bazinga.db]"
    } else {
        Write-Log "WARNING - Could not find database at expected location"
        Write-Log "Set DATABASE_URL environment variable if dashboard fails to load data"
    }
} else {
    Write-Log "Using provided DATABASE_URL=[configured]"
}

# Start dashboard server
$process = $null  # Initialize to avoid undefined variable errors
if ($USE_STANDALONE) {
    Write-Log "Starting standalone Next.js server..."
    Write-Host "Starting standalone Next.js server on port $DASHBOARD_PORT..." -ForegroundColor Cyan

    $STANDALONE_DIR = Join-Path $DASHBOARD_DIR ".next\standalone"

    # Start Next.js standalone server
    $env:PORT = $DASHBOARD_PORT
    $env:HOSTNAME = "localhost"

    $process = Start-Process -FilePath "node" -ArgumentList "server.js" `
        -WorkingDirectory $STANDALONE_DIR `
        -RedirectStandardOutput $DASHBOARD_LOG -RedirectStandardError $DASHBOARD_LOG `
        -PassThru -WindowStyle Hidden

    # Save PID
    $process.Id | Out-File -FilePath $DASHBOARD_PID_FILE -Encoding ASCII

    # Start Socket.io server if compiled version exists (for real-time updates)
    $SOCKET_SERVER = Join-Path $DASHBOARD_DIR "socket-server.js"
    if (Test-Path $SOCKET_SERVER) {
        Write-Log "Starting Socket.io server for real-time updates..."
        if ($env:SOCKET_PORT) { $SOCKET_PORT = $env:SOCKET_PORT } else { $SOCKET_PORT = "3001" }
        $env:SOCKET_PORT = $SOCKET_PORT

        # Prepend NODE_PATH so socket server can find better-sqlite3 native module
        # Use prepend (not overwrite) to preserve existing NODE_PATH dependencies
        $SOCKET_NODE_PATH = Join-Path $DASHBOARD_DIR "node_modules"
        if ($env:NODE_PATH) {
            $env:NODE_PATH = "$SOCKET_NODE_PATH;$env:NODE_PATH"
        } else {
            $env:NODE_PATH = $SOCKET_NODE_PATH
        }

        # Use separate log file to avoid file locking conflicts on Windows
        $LOG_DIR = Split-Path -Parent $DASHBOARD_LOG
        $SOCKET_LOG = Join-Path $LOG_DIR "socket.log"

        $socketProcess = Start-Process -FilePath "node" -ArgumentList $SOCKET_SERVER `
            -RedirectStandardOutput $SOCKET_LOG -RedirectStandardError $SOCKET_LOG `
            -PassThru -WindowStyle Hidden

        # Use same directory as DASHBOARD_PID_FILE (respects TEMP fallback)
        $PID_DIR = Split-Path -Parent $DASHBOARD_PID_FILE
        $SOCKET_PID_FILE = Join-Path $PID_DIR "socket.pid"
        $socketProcess.Id | Out-File -FilePath $SOCKET_PID_FILE -Encoding ASCII
        Write-Log "Socket.io server started (PID: $($socketProcess.Id)) on port $SOCKET_PORT (Log: $SOCKET_LOG)"
    } else {
        Write-Log "Note: Real-time updates limited (socket-server.js not found)"
    }
} else {
    Write-Log "Starting Next.js dashboard + Socket.io server (dev mode)..."
    Write-Host "Starting Next.js dashboard in dev mode on port $DASHBOARD_PORT..." -ForegroundColor Cyan

    Push-Location $DASHBOARD_DIR
    try {
        $env:PORT = $DASHBOARD_PORT

        # Check if dev:all script exists in package.json
        try {
            $packageJson = Get-Content "package.json" -Raw -ErrorAction Stop
        } catch {
            Write-Log "ERROR - Unable to read package.json in $DASHBOARD_DIR"
            Write-Host "ERROR - Unable to read package.json" -ForegroundColor Red
            Pop-Location
            exit 1
        }

        $hasDevAll = $packageJson -match '"dev:all"'
        $script:DEV_ALL_STARTED = $false
        if ($hasDevAll) {
            $process = Start-Process -FilePath "npm" -ArgumentList "run", "dev:all" `
                -RedirectStandardOutput $DASHBOARD_LOG -RedirectStandardError $DASHBOARD_LOG `
                -PassThru -WindowStyle Hidden
            $script:DEV_ALL_STARTED = $true
        } else {
            Write-Log "dev:all not found, starting dev only (no Socket.io server)..."
            $process = Start-Process -FilePath "npm" -ArgumentList "run", "dev" `
                -RedirectStandardOutput $DASHBOARD_LOG -RedirectStandardError $DASHBOARD_LOG `
                -PassThru -WindowStyle Hidden
        }

        # Save PID
        $process.Id | Out-File -FilePath $DASHBOARD_PID_FILE -Encoding ASCII
    }
    finally {
        Pop-Location
    }
}

# Wait a moment for server to start
Start-Sleep -Seconds 3

# Check if server started successfully
$serverProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
if ($serverProcess) {
    if ($USE_STANDALONE) {
        Write-Log "Dashboard server started successfully in STANDALONE mode (PID: $($process.Id))"
        Write-Host "Dashboard server started successfully in STANDALONE mode (PID: $($process.Id))" -ForegroundColor Green
    } else {
        Write-Log "Dashboard server started successfully in DEV mode (PID: $($process.Id))"
        Write-Host "Dashboard server started successfully in DEV mode (PID: $($process.Id))" -ForegroundColor Green
        if ($script:DEV_ALL_STARTED) {
            if ($env:SOCKET_PORT) { $SOCKET_PORT = $env:SOCKET_PORT } else { $SOCKET_PORT = "3001" }
            Write-Log "Socket.io server on port $SOCKET_PORT (real-time updates)"
            Write-Host "Socket.io server on port $SOCKET_PORT (real-time updates)" -ForegroundColor Cyan
        }
    }
    Write-Log "Dashboard available at http://localhost:$DASHBOARD_PORT"
    Write-Host "Dashboard available at http://localhost:$DASHBOARD_PORT" -ForegroundColor Cyan
} else {
    Write-Log "ERROR - Failed to start dashboard server"
    Write-Host "ERROR - Failed to start dashboard server" -ForegroundColor Red
    Remove-Item $DASHBOARD_PID_FILE -ErrorAction SilentlyContinue
    exit 1
}
