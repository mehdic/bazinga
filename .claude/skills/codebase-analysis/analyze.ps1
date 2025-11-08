#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Codebase Analysis Skill - PowerShell wrapper
.DESCRIPTION
    Analyzes codebase to find similar features, reusable utilities, and patterns.
.PARAMETER TaskDescription
    Description of the task to implement
.EXAMPLE
    ./analyze.ps1 "Implement password reset endpoint"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TaskDescription
)

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
& $PythonCmd "$ScriptDir/analyze.py" $TaskDescription

exit $LASTEXITCODE
