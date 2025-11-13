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

$TOOL = "none"

# Run linter based on language
switch ($LANG) {
    "python" {
        # Prefer ruff (fast), fallback to pylint
        if (Test-CommandExists "ruff") {
            $TOOL = "ruff"
            Write-Host "  Running ruff..." -ForegroundColor Gray
            ruff check . --output-format=json > bazinga\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } elseif (Test-CommandExists "pylint") {
            $TOOL = "pylint"
            Write-Host "  Running pylint..." -ForegroundColor Gray
            pylint --output-format=json **/*.py > bazinga\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  No Python linter found. Install: pip install ruff" -ForegroundColor Yellow
            '[]' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
        }
    }

    "javascript" {
        # Check for eslint
        if ((Test-Path "node_modules\.bin\eslint") -or (Test-Path "node_modules\.bin\eslint.cmd") -or (Test-CommandExists "eslint")) {
            $TOOL = "eslint"
            Write-Host "  Running eslint..." -ForegroundColor Gray
            npx eslint . --format json > bazinga\lint_results_raw.json 2>$null
            if (-not $?) {
                '[]' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  eslint not found. Install: npm install --save-dev eslint" -ForegroundColor Yellow
            '[]' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
        }
    }

    "go" {
        # Check for golangci-lint
        if (Test-CommandExists "golangci-lint") {
            $TOOL = "golangci-lint"
            Write-Host "  Running golangci-lint..." -ForegroundColor Gray
            golangci-lint run --out-format json > bazinga\lint_results_raw.json 2>$null
            if (-not $?) {
                '{"Issues":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  golangci-lint not found. Install: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest" -ForegroundColor Yellow
            '{"Issues":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
        }
    }

    "ruby" {
        # Check for rubocop
        if (Test-CommandExists "rubocop") {
            $TOOL = "rubocop"
            Write-Host "  Running rubocop..." -ForegroundColor Gray
            rubocop --format json > bazinga\lint_results_raw.json 2>$null
            if (-not $?) {
                '{"files":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "⚠️  rubocop not found. Install: gem install rubocop" -ForegroundColor Yellow
            '{"files":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
        }
    }

    "java" {
        # Check for Maven or Gradle
        if (Test-Path "pom.xml") {
            if (Test-CommandExists "mvn") {
                $TOOL = "checkstyle+pmd-maven"
                Write-Host "  Running Checkstyle via Maven..." -ForegroundColor Gray
                mvn checkstyle:check 2>$null | Out-Null

                Write-Host "  Running PMD via Maven..." -ForegroundColor Gray
                mvn pmd:check 2>$null | Out-Null

                # Consolidate results (Checkstyle XML + PMD XML)
                if ((Test-Path "target\checkstyle-result.xml") -or (Test-Path "target\pmd.xml")) {
                    '{"tool":"checkstyle+pmd","checkstyle":"target/checkstyle-result.xml","pmd":"target/pmd.xml"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
                } else {
                    '{"issues":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
                }
            } else {
                Write-Host "❌ Maven not found for Java project" -ForegroundColor Red
                $TOOL = "none"
                '{"error":"Maven not found"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } elseif ((Test-Path "build.gradle") -or (Test-Path "build.gradle.kts")) {
            $GRADLE_CMD = if (Test-Path ".\gradlew.bat") { ".\gradlew.bat" } elseif (Test-CommandExists "gradle") { "gradle" } else { $null }

            if ($GRADLE_CMD) {
                $TOOL = "checkstyle+pmd-gradle"
                Write-Host "  Running Checkstyle via Gradle..." -ForegroundColor Gray
                & $GRADLE_CMD checkstyleMain 2>$null | Out-Null

                Write-Host "  Running PMD via Gradle..." -ForegroundColor Gray
                & $GRADLE_CMD pmdMain 2>$null | Out-Null

                # Consolidate results (Checkstyle XML + PMD XML)
                if ((Test-Path "build\reports\checkstyle\main.xml") -or (Test-Path "build\reports\pmd\main.xml")) {
                    '{"tool":"checkstyle+pmd","checkstyle":"build/reports/checkstyle/main.xml","pmd":"build/reports/pmd/main.xml"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
                } else {
                    '{"issues":[]}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
                }
            } else {
                Write-Host "❌ Gradle not found for Java project" -ForegroundColor Red
                $TOOL = "none"
                '{"error":"Gradle not found"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "❌ No Maven or Gradle build file found" -ForegroundColor Red
            $TOOL = "none"
            '{"error":"No build file"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
        }
    }

    default {
        Write-Host "❌ Unknown language. Cannot run linting." -ForegroundColor Red
        '{"error":"Unknown language"}' | Out-File -FilePath "bazinga\lint_results_raw.json" -Encoding UTF8
    }
}

# Add metadata
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read raw results
$rawResults = Get-Content "bazinga\lint_results_raw.json" -Raw

# Create final report with metadata
@"
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "tool": "$TOOL",
  "raw_results": $rawResults
}
"@ | Out-File -FilePath "bazinga\lint_results.json" -Encoding UTF8

# Clean up
Remove-Item "bazinga\lint_results_raw.json" -ErrorAction SilentlyContinue

Write-Host "✅ Linting complete" -ForegroundColor Green
Write-Host "📁 Results saved to: bazinga\lint_results.json" -ForegroundColor Cyan
