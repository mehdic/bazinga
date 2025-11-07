# Test Coverage Analyzer - PowerShell Version
#
# Runs test coverage analysis based on project language
#

$ErrorActionPreference = "Continue"

Write-Host "🧪 Test Coverage Analysis Starting..." -ForegroundColor Cyan

# Create coordination directory if it doesn't exist
if (-not (Test-Path "coordination")) {
    New-Item -ItemType Directory -Path "coordination" -Force | Out-Null
}

# Detect project language and test framework
$LANG = "unknown"
if (Test-Path "pyproject.toml") -or (Test-Path "setup.py") -or (Test-Path "requirements.txt") {
    $LANG = "python"
} elseif (Test-Path "package.json") {
    $LANG = "javascript"
} elseif (Test-Path "go.mod") {
    $LANG = "go"
}

Write-Host "📋 Detected language: $LANG" -ForegroundColor Cyan

# Function to check if command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Run coverage based on language
switch ($LANG) {
    "python" {
        # Check for pytest and pytest-cov
        if (-not (Test-CommandExists "pytest")) {
            Write-Host "⚙️  Installing pytest..." -ForegroundColor Yellow
            pip install pytest pytest-cov --quiet
        }

        Write-Host "  Running pytest with coverage..." -ForegroundColor Gray
        pytest --cov=. --cov-report=json --cov-report=term-missing --quiet 2>$null
        if (-not $?) {
            Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
            '{"totals":{"percent_covered":0},"files":{}}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
        }

        # pytest-cov outputs to coverage.json by default
        if (Test-Path "coverage.json") {
            Move-Item "coverage.json" "coordination\coverage_report_raw.json" -Force
        } elseif (-not (Test-Path "coordination\coverage_report_raw.json")) {
            '{"totals":{"percent_covered":0},"files":{}}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
        }
    }

    "javascript" {
        # Check for jest
        if (-not (Test-Path "node_modules\.bin\jest") -and -not (Test-Path "node_modules\.bin\jest.cmd")) {
            Write-Host "⚙️  Jest not found. Please install: npm install --save-dev jest" -ForegroundColor Yellow
            '{"coverageMap":{}}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
        } else {
            Write-Host "  Running jest with coverage..." -ForegroundColor Gray
            npm test -- --coverage --json --outputFile=coordination\jest-results.json 2>$null
            if (-not $?) {
                Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
                '{"coverageMap":{}}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
            }

            # Jest outputs to coverage/coverage-final.json
            if (Test-Path "coverage\coverage-final.json") {
                Copy-Item "coverage\coverage-final.json" "coordination\coverage_report_raw.json"
            } elseif (-not (Test-Path "coordination\coverage_report_raw.json")) {
                '{"coverageMap":{}}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
            }
        }
    }

    "go" {
        Write-Host "  Running go test with coverage..." -ForegroundColor Gray
        go test -coverprofile=coordination\coverage.out .\... 2>$null
        if (-not $?) {
            Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
            '{"coverage":0}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
        }

        if (Test-Path "coordination\coverage.out") {
            # Parse go coverage output
            $coverageOutput = go tool cover -func=coordination\coverage.out | Select-String "total"
            if ($coverageOutput) {
                $COVERAGE = ($coverageOutput -split '\s+')[2] -replace '%',''
                "{`"coverage`":$COVERAGE}" | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
            }
        } elseif (-not (Test-Path "coordination\coverage_report_raw.json")) {
            '{"coverage":0}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
        }
    }

    default {
        Write-Host "❌ Unknown language. Cannot run coverage analysis." -ForegroundColor Red
        '{"error":"Unknown language"}' | Out-File -FilePath "coordination\coverage_report_raw.json" -Encoding UTF8
    }
}

# Add metadata
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read raw results
$rawResults = Get-Content "coordination\coverage_report_raw.json" -Raw

# Create final report with metadata
@"
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "raw_results": $rawResults
}
"@ | Out-File -FilePath "coordination\coverage_report.json" -Encoding UTF8

# Clean up
Remove-Item "coordination\coverage_report_raw.json" -ErrorAction SilentlyContinue
Remove-Item "coordination\jest-results.json" -ErrorAction SilentlyContinue

Write-Host "✅ Coverage analysis complete" -ForegroundColor Green
Write-Host "📁 Results saved to: coordination\coverage_report.json" -ForegroundColor Cyan
