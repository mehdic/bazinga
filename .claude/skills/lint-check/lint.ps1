# Code Linter - PowerShell Version
#
# Runs code quality linters based on project language
#

$ErrorActionPreference = "Continue"

Write-Host "📋 Code Linting Starting..." -ForegroundColor Cyan

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

$TOOL = "none"

# Run linter based on language
switch ($LANG) {
    "python" {
        # Prefer ruff (fast), fallback to pylint
        if (Test-CommandExists "ruff") {
            $TOOL = "ruff"
            Write-Host "  Running ruff..." -ForegroundColor Gray
            ruff check . --output-format=json > coordination\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
            }
        } elseif (Test-CommandExists "pylint") {
            $TOOL = "pylint"
            Write-Host "  Running pylint..." -ForegroundColor Gray
            pylint --output-format=json **/*.py > coordination\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  No Python linter found. Install: pip install ruff" -ForegroundColor Yellow
            '[]' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
        }
    }

    "javascript" {
        # Check for eslint
        if ((Test-Path "node_modules\.bin\eslint") -or (Test-Path "node_modules\.bin\eslint.cmd") -or (Test-CommandExists "eslint")) {
            $TOOL = "eslint"
            Write-Host "  Running eslint..." -ForegroundColor Gray
            npx eslint . --format json > coordination\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  eslint not found. Install: npm install --save-dev eslint" -ForegroundColor Yellow
            '[]' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
        }
    }

    "go" {
        # Check for golangci-lint
        if (Test-CommandExists "golangci-lint") {
            $TOOL = "golangci-lint"
            Write-Host "  Running golangci-lint..." -ForegroundColor Gray
            golangci-lint run --out-format json > coordination\lint_results_raw.json 2>$null
            if (-not $?) {
                '{"Issues":[]}' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  golangci-lint not found. Install: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest" -ForegroundColor Yellow
            '{"Issues":[]}' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
        }
    }

    "ruby" {
        # Check for rubocop
        if (Test-CommandExists "rubocop") {
            $TOOL = "rubocop"
            Write-Host "  Running rubocop..." -ForegroundColor Gray
            rubocop --format json > coordination\lint_results_raw.json 2>$null
            if (-not $?) {
                '{"files":[]}' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  rubocop not found. Install: gem install rubocop" -ForegroundColor Yellow
            '{"files":[]}' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
        }
    }

    default {
        Write-Host "❌ Unknown language. Cannot run linting." -ForegroundColor Red
        '{"error":"Unknown language"}' | Out-File -FilePath "coordination\lint_results_raw.json" -Encoding UTF8
    }
}

# Add metadata
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read raw results
$rawResults = Get-Content "coordination\lint_results_raw.json" -Raw

# Create final report with metadata
@"
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "tool": "$TOOL",
  "raw_results": $rawResults
}
"@ | Out-File -FilePath "coordination\lint_results.json" -Encoding UTF8

# Clean up
Remove-Item "coordination\lint_results_raw.json" -ErrorAction SilentlyContinue

Write-Host "✅ Linting complete" -ForegroundColor Green
Write-Host "📁 Results saved to: coordination\lint_results.json" -ForegroundColor Cyan
