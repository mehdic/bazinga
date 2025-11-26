# BAZINGA Dashboard Startup Script (PowerShell)
# =================================
# This script runs in the background to:
# 1. Check/install dashboard dependencies (if needed)
# 2. Start the dashboard server
#
# Safe to run multiple times - checks if server is already running

$ErrorActionPreference = "Continue"

$DASHBOARD_PORT = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "53124" }
$DASHBOARD_PID_FILE = Join-Path $env:TEMP "bazinga-dashboard.pid"
$DASHBOARD_LOG = Join-Path $env:TEMP "bazinga-dashboard.log"
$DEPS_MARKER = "dashboard\.deps-installed"

# Cross-platform Python detection
function Get-PythonCommand {
    # Try python3 first (Unix/macOS, some Windows)
    if (Get-Command "python3" -ErrorAction SilentlyContinue) {
        return "python3"
    }
    # Try python (Windows default)
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        # Verify it's Python 3
        $version = & python --version 2>&1
        if ($version -match "Python 3") {
            return "python"
        }
    }
    # Try py launcher (Windows Python launcher)
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        return "py -3"
    }
    return $null
}

# Cross-platform pip detection
function Get-PipCommand {
    if (Get-Command "pip3" -ErrorAction SilentlyContinue) {
        return "pip3"
    }
    if (Get-Command "pip" -ErrorAction SilentlyContinue) {
        return "pip"
    }
    # Use python -m pip as fallback
    $python = Get-PythonCommand
    if ($python) {
        return "$python -m pip"
    }
    return $null
}

$PYTHON_CMD = Get-PythonCommand
$PIP_CMD = Get-PipCommand

if (-not $PYTHON_CMD) {
    Write-Host "ERROR: Python 3 not found. Install Python 3 and ensure it's in PATH." -ForegroundColor Red
    exit 1
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $DASHBOARD_LOG -Value "$timestamp : $Message"
}

Write-Log "🖥️  BAZINGA Dashboard Startup"
Write-Log "Starting dashboard startup process..."

# Check if server is already running
if (Test-Path $DASHBOARD_PID_FILE) {
    $pid = Get-Content $DASHBOARD_PID_FILE
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Log "Dashboard server already running (PID: $pid)"
        Write-Host "Dashboard server already running (PID: $pid)" -ForegroundColor Green
        exit 0
    }
}

# Check if port is in use (cross-platform)
function Test-PortInUse {
    param([int]$Port)
    try {
        # Try Windows-specific cmdlet first
        if (Get-Command "Get-NetTCPConnection" -ErrorAction SilentlyContinue) {
            $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
            return $null -ne $conn
        }
        # Fallback: try to bind to the port
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

# Check if dashboard folder exists
if (-not (Test-Path "dashboard")) {
    Write-Log "Dashboard folder not found"
    Write-Host "Dashboard folder not found" -ForegroundColor Red
    exit 1
}

# Check and install dependencies if needed
if (-not (Test-Path $DEPS_MARKER)) {
    Write-Log "Installing dashboard dependencies..."
    Write-Host "Installing dashboard dependencies..." -ForegroundColor Yellow

    # Check if Python dependencies are installed
    $depsInstalled = $true
    try {
        & $PYTHON_CMD -c "import flask, flask_sock, watchdog, anthropic" 2>$null
        if ($LASTEXITCODE -ne 0) { $depsInstalled = $false }
    }
    catch {
        $depsInstalled = $false
    }

    if (-not $depsInstalled) {
        Write-Log "Installing Python packages..."
        Write-Host "Installing Python packages..." -ForegroundColor Yellow

        # Install dependencies
        try {
            Invoke-Expression "$PIP_CMD install flask flask-sock watchdog anthropic" 2>&1 | Out-Null

            # Create marker file
            New-Item -ItemType File -Path $DEPS_MARKER -Force | Out-Null
            Write-Log "Dependencies installed successfully"
            Write-Host "Dependencies installed successfully" -ForegroundColor Green
        }
        catch {
            Write-Log "ERROR - Could not install dependencies"
            Write-Host "ERROR - Could not install dependencies" -ForegroundColor Red
            exit 1
        }
    }
    else {
        # Dependencies are installed, create marker
        New-Item -ItemType File -Path $DEPS_MARKER -Force | Out-Null
        Write-Log "Dependencies already available"
    }
}
else {
    Write-Log "Dependencies already installed (marker exists)"
}

# Start dashboard server
Write-Log "Starting dashboard server on port $DASHBOARD_PORT..."
Write-Host "Starting dashboard server on port $DASHBOARD_PORT..." -ForegroundColor Cyan

Push-Location dashboard
try {
    $process = Start-Process -FilePath $PYTHON_CMD -ArgumentList "server.py" `
        -RedirectStandardOutput $DASHBOARD_LOG -RedirectStandardError $DASHBOARD_LOG `
        -PassThru -WindowStyle Hidden

    # Save PID
    $process.Id | Out-File -FilePath $DASHBOARD_PID_FILE -Encoding ASCII

    # Wait a moment for server to start
    Start-Sleep -Seconds 2

    # Check if server started successfully
    $serverProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if ($serverProcess) {
        Write-Log "Dashboard server started successfully (PID: $($process.Id))"
        Write-Log "Dashboard available at http://localhost:$DASHBOARD_PORT"
        Write-Host "✅ Dashboard server started successfully (PID: $($process.Id))" -ForegroundColor Green
        Write-Host "🌐 Dashboard available at http://localhost:$DASHBOARD_PORT" -ForegroundColor Cyan
    }
    else {
        Write-Log "ERROR - Failed to start dashboard server"
        Write-Host "ERROR - Failed to start dashboard server" -ForegroundColor Red
        Remove-Item $DASHBOARD_PID_FILE -ErrorAction SilentlyContinue
        exit 1
    }
}
finally {
    Pop-Location
}
