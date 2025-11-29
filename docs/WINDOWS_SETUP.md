# BAZINGA Dashboard: Windows Setup Guide

This guide covers installing and running the BAZINGA Dashboard on Windows.

## Prerequisites

### Required

- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
  - The LTS version is recommended
  - Verify installation: `node --version`

### Optional (for development mode)

- **npm** - Comes bundled with Node.js
- **Visual Studio Build Tools** - Only needed if npm install fails for native modules
  - **Preferred:** Select "Tools for Native Modules" checkbox during Node.js installation
  - Or download from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/) → "Build Tools for Visual Studio"
  - Legacy: `npm install -g windows-build-tools` (deprecated, may not work on newer systems)

## Installation Methods

### Method 1: Pre-built Package (Recommended)

The `bazinga install` command automatically downloads the Windows pre-built package:

```powershell
# Run in your project directory
bazinga install
```

This downloads `bazinga-dashboard-windows-x64.tar.gz` and extracts it automatically.

### Method 2: Manual Download

1. Download from [GitHub Releases](https://github.com/mehdic/bazinga/releases):
   - Look for `bazinga-dashboard-windows-x64.tar.gz`

2. Extract the archive:
   ```powershell
   # Using built-in tar (Windows 10 1803+)
   tar -xzf bazinga-dashboard-windows-x64.tar.gz

   # Or use 7-Zip or WinRAR (Windows Explorer cannot extract .tar.gz natively)
   ```

3. Move to your project:
   ```powershell
   Move-Item dashboard-v2 .\bazinga\dashboard-v2
   ```

### Method 3: Build from Source

If you need to build from source (e.g., for development):

```powershell
cd bazinga\dashboard-v2
npm install
npm run build
```

**Note:** This requires npm and may need Visual Studio Build Tools for the `better-sqlite3` native module.

## Starting the Dashboard

### Using the Startup Script

```powershell
# From your project root
.\bazinga\scripts\start-dashboard.ps1
```

Or if using the standalone script:

```powershell
.\bazinga\dashboard-v2\scripts\start-standalone.ps1
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_PORT` | 3000 | HTTP port for dashboard |
| `SOCKET_PORT` | 3001 | WebSocket port for real-time updates |
| `DATABASE_URL` | Auto-detected | Path to bazinga.db |

Example:
```powershell
$env:DASHBOARD_PORT = "8080"
.\bazinga\scripts\start-dashboard.ps1
```

## Troubleshooting

### "node not found"

Node.js is not installed or not in PATH.

**Solution:**
1. Install Node.js from [nodejs.org](https://nodejs.org/)
2. Restart PowerShell/Terminal after installation
3. Verify: `node --version`

### "npm install failed" with native module errors

The `better-sqlite3` package needs to compile C++ code.

**Solution (Preferred):**
Re-run the Node.js installer and select "Tools for Native Modules" checkbox.

**Alternative:**
1. Download "Build Tools for Visual Studio" from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/)
2. Install with "Desktop development with C++" workload
3. Restart and retry `npm install`

**Legacy (deprecated):**
```powershell
# May not work on newer Windows/Node.js versions
npm install -g windows-build-tools
```

### Port already in use

Another process is using port 3000.

**Solution:**
```powershell
# Find what's using the port
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess
Get-Process -Id <PID>

# Or use a different port
$env:DASHBOARD_PORT = "3001"
.\bazinga\scripts\start-dashboard.ps1
```

### Dashboard shows no data

The database path may not be detected.

**Solution:**
```powershell
$env:DATABASE_URL = "C:\path\to\your\project\bazinga\bazinga.db"
.\bazinga\scripts\start-dashboard.ps1
```

### Tarball extraction fails

Old Windows versions may not have `tar` built-in.

**Solution:**
- Use 7-Zip: Right-click → 7-Zip → Extract Here
- Use WinRAR
- Install tar via Git for Windows

## Architecture Differences

| Aspect | Linux/macOS | Windows |
|--------|-------------|---------|
| Package format | .tar.gz | .tar.gz |
| Startup script | start-dashboard.sh | start-dashboard.ps1 |
| Shell | bash | PowerShell |
| Path separator | `/` | `\` |
| Native modules | gcc/clang | MSVC |

## Verifying Installation

After starting the dashboard:

1. Open browser to `http://localhost:3000`
2. You should see the BAZINGA Dashboard
3. Check the log file: `bazinga\dashboard.log`

## Getting Help

- **GitHub Issues**: [github.com/mehdic/bazinga/issues](https://github.com/mehdic/bazinga/issues)
- **Documentation**: [docs/](../docs/)

## Version Compatibility

| Windows Version | Support |
|-----------------|---------|
| Windows 11 | ✅ Full |
| Windows 10 (1803+) | ✅ Full |
| Windows 10 (older) | ⚠️ Need 7-Zip for extraction |
| Windows Server 2019+ | ✅ Full |
