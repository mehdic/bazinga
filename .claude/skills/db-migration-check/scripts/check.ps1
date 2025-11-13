#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Database Migration Check Skill - PowerShell wrapper
.DESCRIPTION
    Detects dangerous operations in database migrations before deployment.
.EXAMPLE
    ./check.ps1
#>

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    $PythonCmd = "python3"
} else {
    $PythonCmd = "python"
}

# Run the Python script
& $PythonCmd "$ScriptDir/check.py"

exit $LASTEXITCODE
