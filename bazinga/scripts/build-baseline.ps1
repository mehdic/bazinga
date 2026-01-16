<#
.SYNOPSIS
Build Baseline Script for BAZINGA Orchestration (Windows PowerShell)

.DESCRIPTION
Detects project language and runs build to establish baseline.
Output:
  - bazinga/artifacts/<SESSION_ID>/build_baseline.log (human-readable log)
  - bazinga/artifacts/<SESSION_ID>/build_baseline_status.txt (simple status)
  - bazinga/artifacts/<SESSION_ID>/build_baseline.json (structured, machine-readable)

SECURITY: By default, uses safe checks that don't execute arbitrary scripts.
Set $env:ALLOW_BASELINE_BUILD=1 to enable full build.

EXIT CODES: Script exits 1 on build/syntax errors, 0 on success/skip.
The orchestrator treats non-zero exits as informational warnings (logs + proceeds).

.PARAMETER SessionId
The BAZINGA session ID for artifact storage

.EXAMPLE
.\build-baseline.ps1 "bazinga_20260116_120626"
#>

param(
    [Parameter(Position=0)]
    [string]$SessionId = "unknown"
)

$ErrorActionPreference = "Stop"

$OutputDir = "bazinga/artifacts/$SessionId"
$LogFile = "$OutputDir/build_baseline.log"
$StatusFile = "$OutputDir/build_baseline_status.txt"
$JsonFile = "$OutputDir/build_baseline.json"
$AllowBuild = $env:ALLOW_BASELINE_BUILD -eq "1"
$SafeMode = -not $AllowBuild

# Ensure output directory exists
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

function Write-BaselineJson {
    param(
        [string]$Status,
        [string]$Language,
        [string]$CheckName,
        [string]$CheckResult,
        [string]$Message
    )

    $json = @{
        session_id = $SessionId
        timestamp = (Get-Date -Format "o")
        status = $Status
        language = $Language
        safe_mode = $SafeMode
        checks = @(
            @{
                name = $CheckName
                result = $CheckResult
                message = $Message
            }
        )
    } | ConvertTo-Json -Depth 3

    $json | Out-File -FilePath $JsonFile -Encoding UTF8
}

function Write-Log {
    param([string]$Message)
    $Message | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Initialize-Log {
    $timestamp = Get-Date -Format "o"
    $modeText = if ($AllowBuild) { "OFF (full build)" } else { "ON (no scripts)" }

    @"
Build Baseline - $timestamp
Session: $SessionId
Safe mode: $modeText
---
"@ | Out-File -FilePath $LogFile -Encoding UTF8
}

function Detect-And-Build {
    Initialize-Log

    # Node.js/TypeScript
    if (Test-Path "package.json") {
        Write-Log "Detected: Node.js/TypeScript"

        if ($AllowBuild) {
            try {
                npm run build 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "success" "nodejs" "npm_build" "pass" "Build completed successfully"
                exit 0
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "nodejs" "npm_build" "fail" "Build failed - check build_baseline.log for details"
                exit 1
            }
        } else {
            $tscPath = "./node_modules/.bin/tsc.cmd"
            if (Test-Path $tscPath) {
                try {
                    & $tscPath --noEmit 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                    if ($LASTEXITCODE -eq 0) {
                        "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                        Write-BaselineJson "success" "typescript" "tsc_typecheck" "pass" "TypeScript type check passed"
                        exit 0
                    } else {
                        "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                        Write-BaselineJson "error" "typescript" "tsc_typecheck" "fail" "TypeScript type errors detected - check build_baseline.log"
                        exit 1
                    }
                } catch {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "typescript" "tsc_typecheck" "fail" "TypeScript type check failed"
                    exit 1
                }
            } elseif (Test-Path "tsconfig.json") {
                Write-Log "Note: tsc not found locally. Run npm install to enable type checking."
                "skipped (no local tsc, run npm install first)" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "skipped" "typescript" "tsc_typecheck" "skipped" "tsc not found locally - run npm install first"
                exit 0
            } else {
                "success (no tsc)" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "success" "nodejs" "package_json" "pass" "package.json exists, no TypeScript"
                exit 0
            }
        }
    }
    # Go
    elseif (Test-Path "go.mod") {
        Write-Log "Detected: Go"

        if ($AllowBuild) {
            try {
                go build ./... 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "go" "go_build" "pass" "Go build completed successfully"
                    exit 0
                } else {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "go" "go_build" "fail" "Go build failed - check build_baseline.log for details"
                    exit 1
                }
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "go" "go_build" "fail" "Go build failed"
                exit 1
            }
        } else {
            Write-Log "Note: go build disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable."
            "skipped (safe mode - go build disabled)" | Out-File -FilePath $StatusFile -Encoding UTF8
            Write-BaselineJson "skipped" "go" "go_build" "skipped" "go build disabled in safe mode"
            exit 0
        }
    }
    # Java (Maven)
    elseif (Test-Path "pom.xml") {
        Write-Log "Detected: Java (Maven)"

        if ($AllowBuild) {
            try {
                mvn compile -q 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "java" "mvn_compile" "pass" "Maven compile completed successfully"
                    exit 0
                } else {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "java" "mvn_compile" "fail" "Maven compile failed - check build_baseline.log"
                    exit 1
                }
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "java" "mvn_compile" "fail" "Maven compile failed"
                exit 1
            }
        } else {
            Write-Log "Note: mvn compile disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable."
            "skipped (safe mode - mvn compile disabled)" | Out-File -FilePath $StatusFile -Encoding UTF8
            Write-BaselineJson "skipped" "java" "mvn_compile" "skipped" "mvn compile disabled in safe mode"
            exit 0
        }
    }
    # Java (Gradle)
    elseif ((Test-Path "build.gradle") -or (Test-Path "build.gradle.kts")) {
        Write-Log "Detected: Java (Gradle)"

        if ($AllowBuild) {
            try {
                $gradlew = if (Test-Path "./gradlew.bat") { "./gradlew.bat" } else { "gradle" }
                & $gradlew compileJava -q 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "java" "gradle_compile" "pass" "Gradle compile completed successfully"
                    exit 0
                } else {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "java" "gradle_compile" "fail" "Gradle compile failed - check build_baseline.log"
                    exit 1
                }
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "java" "gradle_compile" "fail" "Gradle compile failed"
                exit 1
            }
        } else {
            Write-Log "Note: gradle compile disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable."
            "skipped (safe mode - gradle compile disabled)" | Out-File -FilePath $StatusFile -Encoding UTF8
            Write-BaselineJson "skipped" "java" "gradle_compile" "skipped" "gradle compile disabled in safe mode"
            exit 0
        }
    }
    # Python
    elseif ((Test-Path "requirements.txt") -or (Test-Path "pyproject.toml") -or (Test-Path "setup.py")) {
        Write-Log "Detected: Python"

        try {
            # Python compileall is safe - just syntax check
            python -m compileall -q . 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
            if ($LASTEXITCODE -eq 0) {
                "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "success" "python" "compileall" "pass" "Python syntax check passed"
                exit 0
            } else {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "python" "compileall" "fail" "Python syntax errors detected - check build_baseline.log"
                exit 1
            }
        } catch {
            "error" | Out-File -FilePath $StatusFile -Encoding UTF8
            Write-BaselineJson "error" "python" "compileall" "fail" "Python syntax check failed"
            exit 1
        }
    }
    # Ruby
    elseif (Test-Path "Gemfile") {
        Write-Log "Detected: Ruby"

        if ($AllowBuild) {
            try {
                bundle check 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -ne 0) {
                    bundle install --quiet 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                }
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "ruby" "bundle_install" "pass" "Bundle install completed successfully"
                    exit 0
                } else {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "ruby" "bundle_install" "fail" "Bundle install failed - check build_baseline.log"
                    exit 1
                }
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "ruby" "bundle_install" "fail" "Bundle install failed"
                exit 1
            }
        } else {
            try {
                bundle check 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "ruby" "bundle_check" "pass" "Bundle check passed"
                    exit 0
                } else {
                    "warning (bundle check failed, run with ALLOW_BASELINE_BUILD=1)" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "warning" "ruby" "bundle_check" "warning" "Bundle check failed - dependencies may need install"
                    exit 0
                }
            } catch {
                "warning (bundle check failed)" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "warning" "ruby" "bundle_check" "warning" "Bundle check failed"
                exit 0
            }
        }
    }
    # Rust
    elseif (Test-Path "Cargo.toml") {
        Write-Log "Detected: Rust"

        if ($AllowBuild) {
            try {
                cargo check 2>&1 | Out-File -FilePath $LogFile -Append -Encoding UTF8
                if ($LASTEXITCODE -eq 0) {
                    "success" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "success" "rust" "cargo_check" "pass" "Cargo check completed successfully"
                    exit 0
                } else {
                    "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                    Write-BaselineJson "error" "rust" "cargo_check" "fail" "Cargo check failed - check build_baseline.log"
                    exit 1
                }
            } catch {
                "error" | Out-File -FilePath $StatusFile -Encoding UTF8
                Write-BaselineJson "error" "rust" "cargo_check" "fail" "Cargo check failed"
                exit 1
            }
        } else {
            Write-Log "Note: cargo check disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable."
            "skipped (safe mode - cargo check disabled)" | Out-File -FilePath $StatusFile -Encoding UTF8
            Write-BaselineJson "skipped" "rust" "cargo_check" "skipped" "cargo check disabled in safe mode"
            exit 0
        }
    }
    # No recognized build system
    else {
        Write-Log "No recognized build system detected"
        "skipped" | Out-File -FilePath $StatusFile -Encoding UTF8
        Write-BaselineJson "skipped" "unknown" "none" "skipped" "No recognized build system detected"
        exit 0
    }
}

# Run the detection and build
Detect-And-Build
