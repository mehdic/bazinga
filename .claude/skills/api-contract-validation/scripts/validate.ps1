#!/usr/bin/env pwsh
<#
.SYNOPSIS
    API Contract Validation Skill - PowerShell wrapper
.DESCRIPTION
    Detects breaking changes in OpenAPI/Swagger specifications.
.EXAMPLE
    ./validate.ps1
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
& $PythonCmd "$ScriptDir/validate.py"

exit $LASTEXITCODE
