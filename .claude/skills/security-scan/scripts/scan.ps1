# Security Scanner - PowerShell Version
#
# Runs security vulnerability scans based on mode (basic/advanced)
# Mode is controlled via SECURITY_SCAN_MODE environment variable
#

$ErrorActionPreference = "Continue"

# Get mode from environment (default: basic)
$MODE = if ($env:SECURITY_SCAN_MODE) { $env:SECURITY_SCAN_MODE } else { "basic" }

Write-Host "🔒 Security Scan Starting (Mode: $MODE)..." -ForegroundColor Cyan

# Create coordination directory if it doesn't exist
if (-not (Test-Path "coordination")) {
    New-Item -ItemType Directory -Path "coordination" -Force | Out-Null
}

# Initialize status tracking
$SCAN_STATUS = "success"
$SCAN_ERROR = ""
$TOOL_USED = "none"

# Detect project language
$LANG = "unknown"
if (Test-Path "pyproject.toml") -or (Test-Path "setup.py") -or (Test-Path "requirements.txt") {
    $LANG = "python"
} elseif (Test-Path "package.json") {
    $LANG = "javascript"
} elseif (Test-Path "go.mod") {
    $LANG = "go"
} elseif (Test-Path "Gemfile") -or (Get-ChildItem -Filter "*.gemspec" -ErrorAction SilentlyContinue) {
    $LANG = "ruby"
} elseif (Test-Path "pom.xml") -or (Test-Path "build.gradle") -or (Test-Path "build.gradle.kts") {
    $LANG = "java"
}

Write-Host "📋 Detected language: $LANG" -ForegroundColor Cyan

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Run scan based on mode and language
switch ($MODE) {
    "basic" {
        Write-Host "⚡ Running BASIC scan (fast, high/medium severity only)..." -ForegroundColor Yellow

        switch ($LANG) {
            "python" {
                # Install bandit if needed
                if (-not (Test-CommandExists "bandit")) {
                    Write-Host "⚙️  Installing bandit..." -ForegroundColor Yellow
                    pip install bandit --quiet 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install bandit"
                        '{"results":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                }

                $TOOL_USED = "bandit"
                Write-Host "  Running bandit (high/medium severity)..." -ForegroundColor Gray
                bandit -r . -f json -o bazinga\security_scan_raw.json -ll 2>$null
                if (-not $?) {
                    $SCAN_STATUS = "partial"
                    $SCAN_ERROR = "Bandit scan failed or had errors"
                    '{"results":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            "javascript" {
                $TOOL_USED = "npm-audit"
                Write-Host "  Running npm audit (high severity)..." -ForegroundColor Gray
                npm audit --audit-level=high --json > bazinga\security_scan_raw.json 2>$null
                if (-not $?) {
                    $SCAN_STATUS = "partial"
                    $SCAN_ERROR = "npm audit failed (possibly network issue)"
                    '{"vulnerabilities":{}}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            "go" {
                # Install gosec if needed
                if (-not (Test-CommandExists "gosec")) {
                    Write-Host "⚙️  Installing gosec..." -ForegroundColor Yellow
                    go install github.com/securego/gosec/v2/cmd/gosec@latest 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install gosec"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                    $env:PATH = "$env:PATH;$(go env GOPATH)\bin"
                }

                if ($SCAN_STATUS -ne "error") {
                    $TOOL_USED = "gosec"
                    Write-Host "  Running gosec (high severity)..." -ForegroundColor Gray
                    gosec -severity high -fmt json -out bazinga\security_scan_raw.json .\... 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = "gosec scan failed"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                    }
                }
            }

            "ruby" {
                # Install brakeman if needed
                if (-not (Test-CommandExists "brakeman")) {
                    Write-Host "⚙️  Installing brakeman..." -ForegroundColor Yellow
                    gem install brakeman 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install brakeman"
                        '{"warnings":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                }

                $TOOL_USED = "brakeman"
                Write-Host "  Running brakeman (high severity)..." -ForegroundColor Gray
                brakeman -f json -o bazinga\security_scan_raw.json --severity-level 1 2>$null
                if (-not $?) {
                    $SCAN_STATUS = "partial"
                    $SCAN_ERROR = "brakeman scan failed"
                    '{"warnings":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            "java" {
                # Check for SpotBugs (via Maven or Gradle)
                if (Test-Path "pom.xml") {
                    $TOOL_USED = "spotbugs-maven"
                    Write-Host "  Running SpotBugs via Maven (high priority)..." -ForegroundColor Gray
                    if (Test-CommandExists "mvn") {
                        mvn compile spotbugs:spotbugs -Dspotbugs.effort=Max -Dspotbugs.threshold=High 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = "SpotBugs Maven scan failed"
                        }

                        # Check if SpotBugs report exists
                        if (Test-Path "target\spotbugsXml.xml") {
                            '{"tool":"spotbugs","source":"target/spotbugsXml.xml"}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        } else {
                            '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        }
                    } else {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Maven not found for Java project"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                    }
                } elseif ((Test-Path "build.gradle") -or (Test-Path "build.gradle.kts")) {
                    $TOOL_USED = "spotbugs-gradle"
                    Write-Host "  Running SpotBugs via Gradle (high priority)..." -ForegroundColor Gray
                    $GRADLE_CMD = if (Test-Path ".\gradlew.bat") { ".\gradlew.bat" } elseif (Test-CommandExists "gradle") { "gradle" } else { $null }

                    if ($GRADLE_CMD) {
                        & $GRADLE_CMD spotbugsMain 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = "SpotBugs Gradle scan failed"
                        }

                        # Check for Gradle SpotBugs report
                        if (Test-Path "build\reports\spotbugs\main.xml") {
                            '{"tool":"spotbugs","source":"build/reports/spotbugs/main.xml"}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        } else {
                            '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        }
                    } else {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Gradle not found for Java project"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                    }
                } else {
                    $SCAN_STATUS = "error"
                    $SCAN_ERROR = "No Maven or Gradle build file found for Java project"
                    '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            default {
                Write-Host "❌ Unknown language. Cannot run security scan." -ForegroundColor Red
                $SCAN_STATUS = "error"
                $SCAN_ERROR = "Unknown or unsupported language"
                '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
            }
        }

        Write-Host "✅ Basic security scan complete (5-10s)" -ForegroundColor Green
    }

    "advanced" {
        Write-Host "🔍 Running ADVANCED scan (comprehensive, all severities)..." -ForegroundColor Yellow

        switch ($LANG) {
            "python" {
                $TOOL_USED = "bandit+semgrep"

                # Install bandit if needed
                if (-not (Test-CommandExists "bandit")) {
                    Write-Host "⚙️  Installing bandit..." -ForegroundColor Yellow
                    pip install bandit --quiet 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install bandit"
                        '{"results":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                }

                # Install semgrep if needed
                if (-not (Test-CommandExists "semgrep")) {
                    Write-Host "⚙️  Installing semgrep..." -ForegroundColor Yellow
                    pip install semgrep --quiet 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = "Failed to install semgrep, running bandit only"
                        $TOOL_USED = "bandit"
                    }
                }

                if ($SCAN_STATUS -ne "error") {
                    # Run bandit (all severities)
                    Write-Host "  Running bandit (all severities)..." -ForegroundColor Gray
                    bandit -r . -f json -o bazinga\bandit_full.json 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; Bandit scan failed" } else { "Bandit scan failed" }
                        '{"results":[]}' | Out-File -FilePath "bazinga\bandit_full.json" -Encoding UTF8
                    }

                    # Run semgrep if available
                    if (Test-CommandExists "semgrep") {
                        Write-Host "  Running semgrep (security patterns)..." -ForegroundColor Gray
                        semgrep --config=auto --json -o bazinga\semgrep.json 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; Semgrep scan failed" } else { "Semgrep scan failed" }
                            '{"results":[]}' | Out-File -FilePath "bazinga\semgrep.json" -Encoding UTF8
                        }
                    } else {
                        '{"results":[]}' | Out-File -FilePath "bazinga\semgrep.json" -Encoding UTF8
                    }

                    # Combine results (PowerShell JSON merge)
                    $banditData = Get-Content "bazinga\bandit_full.json" -Raw | ConvertFrom-Json
                    $semgrepData = Get-Content "bazinga\semgrep.json" -Raw | ConvertFrom-Json
                    @{
                        bandit = $banditData
                        semgrep = $semgrepData
                    } | ConvertTo-Json -Depth 10 | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            "javascript" {
                $TOOL_USED = "npm-audit"

                # Full npm audit
                Write-Host "  Running npm audit (all severabilities)..." -ForegroundColor Gray
                npm audit --json > bazinga\npm_audit.json 2>$null
                if (-not $?) {
                    $SCAN_STATUS = "partial"
                    $SCAN_ERROR = "npm audit failed (possibly network issue)"
                    '{"vulnerabilities":{}}' | Out-File -FilePath "bazinga\npm_audit.json" -Encoding UTF8
                }

                # Try eslint with security plugin if available
                $hasEslintSecurity = npm list eslint-plugin-security 2>$null
                if ($?) {
                    $TOOL_USED = "npm-audit+eslint-security"
                    Write-Host "  Running eslint security plugin..." -ForegroundColor Gray
                    npx eslint . --plugin security --format json > bazinga\eslint_security.json 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; eslint-security scan failed" } else { "eslint-security scan failed" }
                        '[]' | Out-File -FilePath "bazinga\eslint_security.json" -Encoding UTF8
                    }

                    # Combine results
                    $npmData = Get-Content "bazinga\npm_audit.json" -Raw | ConvertFrom-Json
                    $eslintData = Get-Content "bazinga\eslint_security.json" -Raw | ConvertFrom-Json
                    @{
                        npm_audit = $npmData
                        eslint = $eslintData
                    } | ConvertTo-Json -Depth 10 | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                } else {
                    Copy-Item "bazinga\npm_audit.json" "bazinga\security_scan_raw.json"
                }
            }

            "go" {
                $TOOL_USED = "gosec"

                # Install gosec if needed
                if (-not (Test-CommandExists "gosec")) {
                    Write-Host "⚙️  Installing gosec..." -ForegroundColor Yellow
                    go install github.com/securego/gosec/v2/cmd/gosec@latest 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install gosec"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                    $env:PATH = "$env:PATH;$(go env GOPATH)\bin"
                }

                if ($SCAN_STATUS -ne "error") {
                    Write-Host "  Running gosec (all severities)..." -ForegroundColor Gray
                    gosec -fmt json -out bazinga\security_scan_raw.json .\... 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = "gosec scan failed"
                        '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                    }
                }
            }

            "ruby" {
                $TOOL_USED = "brakeman"

                # Install brakeman if needed
                if (-not (Test-CommandExists "brakeman")) {
                    Write-Host "⚙️  Installing brakeman..." -ForegroundColor Yellow
                    gem install brakeman 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Failed to install brakeman"
                        '{"warnings":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                        break
                    }
                }

                Write-Host "  Running brakeman (all findings)..." -ForegroundColor Gray
                brakeman -f json -o bazinga\security_scan_raw.json 2>$null
                if (-not $?) {
                    $SCAN_STATUS = "partial"
                    $SCAN_ERROR = "brakeman scan failed"
                    '{"warnings":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
                }
            }

            "java" {
                $TOOL_USED = "spotbugs+semgrep+owasp"

                # Run SpotBugs (all priorities)
                if (Test-Path "pom.xml") {
                    Write-Host "  Running SpotBugs via Maven (all priorities)..." -ForegroundColor Gray
                    if (Test-CommandExists "mvn") {
                        mvn compile spotbugs:spotbugs -Dspotbugs.effort=Max 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = "SpotBugs Maven scan failed"
                        }

                        # Run OWASP Dependency Check
                        Write-Host "  Running OWASP Dependency Check..." -ForegroundColor Gray
                        mvn org.owasp:dependency-check-maven:check 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; OWASP Dependency Check failed" } else { "OWASP Dependency Check failed" }
                        }
                    } else {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Maven not found for Java project"
                    }
                } elseif ((Test-Path "build.gradle") -or (Test-Path "build.gradle.kts")) {
                    Write-Host "  Running SpotBugs via Gradle (all priorities)..." -ForegroundColor Gray
                    $GRADLE_CMD = if (Test-Path ".\gradlew.bat") { ".\gradlew.bat" } elseif (Test-CommandExists "gradle") { "gradle" } else { $null }

                    if ($GRADLE_CMD) {
                        & $GRADLE_CMD spotbugsMain 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = "SpotBugs Gradle scan failed"
                        }

                        # Run OWASP Dependency Check for Gradle
                        Write-Host "  Running OWASP Dependency Check..." -ForegroundColor Gray
                        & $GRADLE_CMD dependencyCheckAnalyze 2>$null
                        if (-not $?) {
                            $SCAN_STATUS = "partial"
                            $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; OWASP Dependency Check failed" } else { "OWASP Dependency Check failed" }
                        }
                    } else {
                        $SCAN_STATUS = "error"
                        $SCAN_ERROR = "Gradle not found for Java project"
                    }
                }

                # Run semgrep if available
                if (Test-CommandExists "semgrep") {
                    Write-Host "  Running semgrep for Java..." -ForegroundColor Gray
                    semgrep --config=auto --json -o bazinga\semgrep_java.json 2>$null
                    if (-not $?) {
                        $SCAN_STATUS = "partial"
                        $SCAN_ERROR = if ($SCAN_ERROR) { "$SCAN_ERROR; Semgrep scan failed" } else { "Semgrep scan failed" }
                        '{"results":[]}' | Out-File -FilePath "bazinga\semgrep_java.json" -Encoding UTF8
                    }
                }

                # Consolidate Java results
                '{"tool":"spotbugs+owasp+semgrep","status":"see_build_reports"}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
            }

            default {
                Write-Host "❌ Unknown language. Cannot run security scan." -ForegroundColor Red
                $SCAN_STATUS = "error"
                $SCAN_ERROR = "Unknown or unsupported language"
                '{"issues":[]}' | Out-File -FilePath "bazinga\security_scan_raw.json" -Encoding UTF8
            }
        }

        Write-Host "✅ Advanced security scan complete (30-60s)" -ForegroundColor Green
    }

    default {
        Write-Host "❌ Invalid mode: $MODE (use 'basic' or 'advanced')" -ForegroundColor Red
        exit 1
    }
}

# Add metadata to results
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read raw results and add metadata
$rawData = Get-Content "bazinga\security_scan_raw.json" -Raw | ConvertFrom-Json

# Create final report with metadata and status
$finalReport = @{
    scan_mode = $MODE
    timestamp = $TIMESTAMP
    language = $LANG
    status = $SCAN_STATUS
    tool = $TOOL_USED
    error = $SCAN_ERROR
}

# Merge with raw results
$rawData.PSObject.Properties | ForEach-Object {
    $finalReport[$_.Name] = $_.Value
}

$finalReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "bazinga\security_scan.json" -Encoding UTF8

# Clean up intermediate files
Remove-Item "bazinga\bandit_full.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\semgrep.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\npm_audit.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\eslint_security.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\security_scan_raw.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\semgrep_java.json" -ErrorAction SilentlyContinue

# Report status
Write-Host "📊 Scan mode: $MODE | Language: $LANG | Status: $SCAN_STATUS" -ForegroundColor Cyan
if ($SCAN_STATUS -ne "success") {
    Write-Host "⚠️  WARNING: $SCAN_ERROR" -ForegroundColor Yellow
}
Write-Host "📁 Results saved to: bazinga\security_scan.json" -ForegroundColor Cyan
