#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Pattern Analysis Skill - PowerShell wrapper
.DESCRIPTION
    Analyzes test suite to find patterns, fixtures, naming conventions, and utilities.
.PARAMETER TestPath
    Path to test directory or file
.PARAMETER TaskDescription
    Optional task description
.EXAMPLE
    ./analyze_tests.ps1 "tests/"
    ./analyze_tests.ps1 "tests/" "Implement password reset"
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TestPath,

    [Parameter(Mandatory=$false, Position=1)]
    [string]$TaskDescription = ""
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
if ($TaskDescription) {
    & $PythonCmd "$ScriptDir/analyze_tests.py" $TestPath $TaskDescription
} else {
    & $PythonCmd "$ScriptDir/analyze_tests.py" $TestPath
}

exit $LASTEXITCODE
