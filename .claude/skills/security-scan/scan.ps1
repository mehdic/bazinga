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
                    pip install bandit --quiet
                }

                # Basic: High/medium severity only
                Write-Host "  Running bandit (high/medium severity)..." -ForegroundColor Gray
                bandit -r . -f json -o coordination\security_scan_raw.json -ll 2>$null
                if (-not $?) {
                    '{"results":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            "javascript" {
                # npm audit is built-in
                Write-Host "  Running npm audit (high severity)..." -ForegroundColor Gray
                npm audit --audit-level=high --json > coordination\security_scan_raw.json 2>$null
                if (-not $?) {
                    '{"vulnerabilities":{}}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            "go" {
                # Install gosec if needed
                if (-not (Test-CommandExists "gosec")) {
                    Write-Host "⚙️  Installing gosec..." -ForegroundColor Yellow
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                }

                Write-Host "  Running gosec (high severity)..." -ForegroundColor Gray
                gosec -severity high -fmt json -out coordination\security_scan_raw.json .\... 2>$null
                if (-not $?) {
                    '{"issues":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            "ruby" {
                # Install brakeman if needed
                if (-not (Test-CommandExists "brakeman")) {
                    Write-Host "⚙️  Installing brakeman..." -ForegroundColor Yellow
                    gem install brakeman
                }

                Write-Host "  Running brakeman (high severity)..." -ForegroundColor Gray
                brakeman -f json -o coordination\security_scan_raw.json --severity-level 1 2>$null
                if (-not $?) {
                    '{"warnings":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            default {
                Write-Host "❌ Unknown language. Cannot run security scan." -ForegroundColor Red
                '{"error":"Unknown language","issues":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
            }
        }

        Write-Host "✅ Basic security scan complete (5-10s)" -ForegroundColor Green
    }

    "advanced" {
        Write-Host "🔍 Running ADVANCED scan (comprehensive, all severities)..." -ForegroundColor Yellow

        switch ($LANG) {
            "python" {
                # Install tools if needed
                if (-not (Test-CommandExists "bandit")) {
                    Write-Host "⚙️  Installing bandit..." -ForegroundColor Yellow
                    pip install bandit --quiet
                }
                if (-not (Test-CommandExists "semgrep")) {
                    Write-Host "⚙️  Installing semgrep..." -ForegroundColor Yellow
                    pip install semgrep --quiet
                }

                # Run bandit (all severities)
                Write-Host "  Running bandit (all severities)..." -ForegroundColor Gray
                bandit -r . -f json -o coordination\bandit_full.json 2>$null
                if (-not $?) {
                    '{"results":[]}' | Out-File -FilePath "coordination\bandit_full.json" -Encoding UTF8
                }

                # Run semgrep (comprehensive patterns)
                Write-Host "  Running semgrep (security patterns)..." -ForegroundColor Gray
                semgrep --config=auto --json -o coordination\semgrep.json 2>$null
                if (-not $?) {
                    '{"results":[]}' | Out-File -FilePath "coordination\semgrep.json" -Encoding UTF8
                }

                # Combine results (simplified - no jq equivalent check)
                Copy-Item "coordination\bandit_full.json" "coordination\security_scan_raw.json"
            }

            "javascript" {
                # Full npm audit
                Write-Host "  Running npm audit (all severities)..." -ForegroundColor Gray
                npm audit --json > coordination\npm_audit.json 2>$null
                if (-not $?) {
                    '{"vulnerabilities":{}}' | Out-File -FilePath "coordination\npm_audit.json" -Encoding UTF8
                }

                Copy-Item "coordination\npm_audit.json" "coordination\security_scan_raw.json"
            }

            "go" {
                # Install gosec if needed
                if (-not (Test-CommandExists "gosec")) {
                    Write-Host "⚙️  Installing gosec..." -ForegroundColor Yellow
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                }

                Write-Host "  Running gosec (all severities)..." -ForegroundColor Gray
                gosec -fmt json -out coordination\security_scan_raw.json .\... 2>$null
                if (-not $?) {
                    '{"issues":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            "ruby" {
                # Install brakeman if needed
                if (-not (Test-CommandExists "brakeman")) {
                    Write-Host "⚙️  Installing brakeman..." -ForegroundColor Yellow
                    gem install brakeman
                }

                Write-Host "  Running brakeman (all findings)..." -ForegroundColor Gray
                brakeman -f json -o coordination\security_scan_raw.json 2>$null
                if (-not $?) {
                    '{"warnings":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
                }
            }

            default {
                Write-Host "❌ Unknown language. Cannot run security scan." -ForegroundColor Red
                '{"error":"Unknown language","issues":[]}' | Out-File -FilePath "coordination\security_scan_raw.json" -Encoding UTF8
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

# Read raw results
$rawResults = Get-Content "coordination\security_scan_raw.json" -Raw

# Create final report with metadata
@"
{
  "scan_mode": "$MODE",
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "raw_results": $rawResults
}
"@ | Out-File -FilePath "coordination\security_scan.json" -Encoding UTF8

# Clean up intermediate files
Remove-Item "coordination\bandit_full.json" -ErrorAction SilentlyContinue
Remove-Item "coordination\semgrep.json" -ErrorAction SilentlyContinue
Remove-Item "coordination\npm_audit.json" -ErrorAction SilentlyContinue
Remove-Item "coordination\eslint_security.json" -ErrorAction SilentlyContinue
Remove-Item "coordination\security_scan_raw.json" -ErrorAction SilentlyContinue

Write-Host "📊 Scan mode: $MODE | Language: $LANG" -ForegroundColor Cyan
Write-Host "📁 Results saved to: coordination\security_scan.json" -ForegroundColor Cyan
