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

# Run coverage based on language
switch ($LANG) {
    "python" {
        # Check for pytest and pytest-cov
        if (-not (Test-CommandExists "pytest")) {
            Write-Host "⚙️  Installing pytest..." -ForegroundColor Yellow
            pip install pytest pytest-cov --quiet 2>$null
        }

        Write-Host "  Running pytest with coverage..." -ForegroundColor Gray
        pytest --cov=. --cov-report=json --cov-report=term-missing --quiet 2>$null
        if (-not $?) {
            Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
            '{"totals":{"percent_covered":0},"files":{}}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        }

        # pytest-cov outputs to coverage.json by default
        if (Test-Path "coverage.json") {
            Move-Item "coverage.json" "bazinga\coverage_report_raw.json" -Force
        } elseif (-not (Test-Path "bazinga\coverage_report_raw.json")) {
            '{"totals":{"percent_covered":0},"files":{}}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        }
    }

    "javascript" {
        # Check for jest
        if (-not (Test-Path "node_modules\.bin\jest") -and -not (Test-Path "node_modules\.bin\jest.cmd")) {
            Write-Host "⚙️  Jest not found. Please install: npm install --save-dev jest" -ForegroundColor Yellow
            '{"coverageMap":{}}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        } else {
            Write-Host "  Running jest with coverage..." -ForegroundColor Gray
            npm test -- --coverage --json --outputFile=bazinga\jest-results.json 2>$null
            if (-not $?) {
                Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
                '{"coverageMap":{}}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            }

            # Jest outputs to coverage/coverage-final.json
            if (Test-Path "coverage\coverage-final.json") {
                Copy-Item "coverage\coverage-final.json" "bazinga\coverage_report_raw.json"
            } elseif (-not (Test-Path "bazinga\coverage_report_raw.json")) {
                '{"coverageMap":{}}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            }
        }
    }

    "go" {
        Write-Host "  Running go test with coverage..." -ForegroundColor Gray
        go test -coverprofile=bazinga\coverage.out .\... 2>$null
        if (-not $?) {
            Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
            '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        }

        if (Test-Path "bazinga\coverage.out") {
            # Parse go coverage output
            $coverageOutput = go tool cover -func=bazinga\coverage.out | Select-String "total"
            if ($coverageOutput) {
                $COVERAGE = ($coverageOutput -replace '.*\s(\d+\.\d+)%.*','$1')
                "{`"coverage`":$COVERAGE}" | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            } else {
                '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            }
        } elseif (-not (Test-Path "bazinga\coverage_report_raw.json")) {
            '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        }
    }

    "java" {
        # Run JaCoCo via Maven or Gradle
        if (Test-Path "pom.xml") {
            if (Test-CommandExists "mvn") {
                Write-Host "  Running Maven tests with JaCoCo coverage..." -ForegroundColor Gray
                mvn test jacoco:report 2>$null
                if (-not $?) {
                    Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
                    '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                }

                # JaCoCo XML report location (Maven)
                if (Test-Path "target\site\jacoco\jacoco.xml") {
                    # Parse JaCoCo XML for coverage percentage
                    [xml]$jacocoXml = Get-Content "target\site\jacoco\jacoco.xml"
                    $lineCovered = ($jacocoXml.report.counter | Where-Object { $_.type -eq 'LINE' } | Measure-Object -Property covered -Sum).Sum
                    $lineMissed = ($jacocoXml.report.counter | Where-Object { $_.type -eq 'LINE' } | Measure-Object -Property missed -Sum).Sum
                    $total = $lineCovered + $lineMissed
                    if ($total -gt 0) {
                        $coverage = [math]::Round(($lineCovered / $total) * 100, 2)
                        "{`"coverage`":$coverage,`"source`":`"target/site/jacoco/jacoco.xml`"}" | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                    } else {
                        '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                    }
                } elseif (-not (Test-Path "bazinga\coverage_report_raw.json")) {
                    '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                }
            } else {
                Write-Host "❌ Maven not found for Java project" -ForegroundColor Red
                '{"error":"Maven not found"}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            }
        } elseif ((Test-Path "build.gradle") -or (Test-Path "build.gradle.kts")) {
            $GRADLE_CMD = if (Test-Path ".\gradlew.bat") { ".\gradlew.bat" } elseif (Test-CommandExists "gradle") { "gradle" } else { $null }

            if ($GRADLE_CMD) {
                Write-Host "  Running Gradle tests with JaCoCo coverage..." -ForegroundColor Gray
                & $GRADLE_CMD test jacocoTestReport 2>$null
                if (-not $?) {
                    Write-Host "⚠️  Tests failed or no tests found" -ForegroundColor Yellow
                    '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                }

                # JaCoCo XML report location (Gradle)
                if (Test-Path "build\reports\jacoco\test\jacocoTestReport.xml") {
                    # Parse JaCoCo XML for coverage percentage
                    [xml]$jacocoXml = Get-Content "build\reports\jacoco\test\jacocoTestReport.xml"
                    $lineCovered = ($jacocoXml.report.counter | Where-Object { $_.type -eq 'LINE' } | Measure-Object -Property covered -Sum).Sum
                    $lineMissed = ($jacocoXml.report.counter | Where-Object { $_.type -eq 'LINE' } | Measure-Object -Property missed -Sum).Sum
                    $total = $lineCovered + $lineMissed
                    if ($total -gt 0) {
                        $coverage = [math]::Round(($lineCovered / $total) * 100, 2)
                        "{`"coverage`":$coverage,`"source`":`"build/reports/jacoco/test/jacocoTestReport.xml`"}" | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                    } else {
                        '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                    }
                } elseif (-not (Test-Path "bazinga\coverage_report_raw.json")) {
                    '{"coverage":0}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
                }
            } else {
                Write-Host "❌ Gradle not found for Java project" -ForegroundColor Red
                '{"error":"Gradle not found"}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
            }
        } else {
            Write-Host "❌ No Maven or Gradle build file found" -ForegroundColor Red
            '{"error":"No build file"}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
        }
    }

    default {
        Write-Host "❌ Unknown language. Cannot run coverage analysis." -ForegroundColor Red
        '{"error":"Unknown language"}' | Out-File -FilePath "bazinga\coverage_report_raw.json" -Encoding UTF8
    }
}

# Add metadata
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Read raw results and add metadata
$rawData = Get-Content "bazinga\coverage_report_raw.json" -Raw | ConvertFrom-Json

# Create final report with metadata
$finalReport = @{
    timestamp = $TIMESTAMP
    language = $LANG
}

# Merge with raw results
$rawData.PSObject.Properties | ForEach-Object {
    $finalReport[$_.Name] = $_.Value
}

$finalReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "bazinga\coverage_report.json" -Encoding UTF8

# Clean up
Remove-Item "bazinga\coverage_report_raw.json" -ErrorAction SilentlyContinue
Remove-Item "bazinga\jest-results.json" -ErrorAction SilentlyContinue

Write-Host "✅ Coverage analysis complete" -ForegroundColor Green
Write-Host "📁 Results saved to: bazinga\coverage_report.json" -ForegroundColor Cyan

# Display summary
$reportData = Get-Content "bazinga\coverage_report.json" -Raw | ConvertFrom-Json
if ($LANG -eq "python" -and $reportData.totals) {
    $coverage = $reportData.totals.percent_covered
    Write-Host "📊 Overall coverage: $coverage%" -ForegroundColor Cyan
} elseif (($LANG -eq "go" -or $LANG -eq "java") -and $reportData.coverage) {
    $coverage = $reportData.coverage
    Write-Host "📊 Overall coverage: $coverage%" -ForegroundColor Cyan
}
