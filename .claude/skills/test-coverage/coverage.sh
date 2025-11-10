#!/bin/bash
#
# Test Coverage Analyzer - Bash Version
#
# Runs test coverage analysis based on project language
#

# Don't exit on error for graceful degradation
set +e

echo "🧪 Test Coverage Analysis Starting..."

# Create coordination directory if it doesn't exist
mkdir -p coordination

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "coordination/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' coordination/skills_config.json 2>/dev/null || echo "lite")
fi

# Detect project language and test framework
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
    LANG="python"
elif [ -f "package.json" ]; then
    LANG="javascript"
elif [ -f "go.mod" ]; then
    LANG="go"
elif [ -f "pom.xml" ] || [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
    LANG="java"
else
    LANG="unknown"
fi

echo "📋 Detected language: $LANG"

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check tool availability and handle graceful degradation
check_tool_or_skip() {
    local tool=$1
    local install_cmd=$2
    local tool_name=$3  # Human readable name

    if ! command_exists "$tool"; then
        if [ "$PROFILE" = "lite" ]; then
            # Lite mode: Skip gracefully with warning
            echo "⚠️  $tool_name not installed - skipping in lite mode"
            echo "   Install with: $install_cmd"
            cat > coordination/coverage_report.json << EOF
{
  "status": "skipped",
  "language": "$LANG",
  "reason": "$tool_name not installed",
  "recommendation": "Install with: $install_cmd",
  "impact": "Test coverage analysis was skipped. Install $tool_name for coverage metrics.",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
            exit 0
        else
            # Advanced mode: Fail if tool not available
            echo "❌ $tool_name required but not installed"
            cat > coordination/coverage_report.json << EOF
{
  "status": "error",
  "language": "$LANG",
  "reason": "$tool_name required but not installed",
  "recommendation": "Install with: $install_cmd",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
            exit 1
        fi
    fi
}

# Run coverage based on language
case $LANG in
    python)
        # Check for pytest with graceful degradation
        check_tool_or_skip "pytest" "pip install pytest pytest-cov" "pytest and pytest-cov (Python test coverage)"

        # Check for pytest-cov module
        if ! python -c "import pytest_cov" 2>/dev/null; then
            if [ "$PROFILE" = "lite" ]; then
                echo "⚠️  pytest-cov not installed - skipping in lite mode"
                echo '{"status":"skipped","reason":"pytest-cov not installed"}' > coordination/coverage_report.json
                exit 0
            fi
        fi

        echo "  Running pytest with coverage..."
        pytest --cov=. --cov-report=json --cov-report=term-missing --quiet 2>/dev/null || {
            echo "⚠️  Tests failed or no tests found"
            echo '{"totals":{"percent_covered":0},"files":{}}' > coordination/coverage_report_raw.json
        }

        # pytest-cov outputs to coverage.json by default
        if [ -f "coverage.json" ]; then
            mv coverage.json coordination/coverage_report_raw.json
        elif [ ! -f "coordination/coverage_report_raw.json" ]; then
            echo '{"totals":{"percent_covered":0},"files":{}}' > coordination/coverage_report_raw.json
        fi
        ;;

    javascript)
        # Check for jest with graceful degradation
        if ! [ -f "node_modules/.bin/jest" ] && ! command_exists "jest"; then
            check_tool_or_skip "jest" "npm install --save-dev jest" "jest (JavaScript test coverage)"
        fi

        echo "  Running jest with coverage..."
        npm test -- --coverage --json --outputFile=coordination/jest-results.json 2>/dev/null || {
            echo "⚠️  Tests failed or no tests found"
            echo '{"coverageMap":{}}' > coordination/coverage_report_raw.json
        }

        # Jest outputs to coverage/coverage-final.json
        if [ -f "coverage/coverage-final.json" ]; then
            cp coverage/coverage-final.json coordination/coverage_report_raw.json
        elif [ ! -f "coordination/coverage_report_raw.json" ]; then
            echo '{"coverageMap":{}}' > coordination/coverage_report_raw.json
        fi
        ;;

    go)
        echo "  Running go test with coverage..."
        go test -coverprofile=coordination/coverage.out ./... 2>/dev/null || {
            echo "⚠️  Tests failed or no tests found"
            echo '{"coverage":0}' > coordination/coverage_report_raw.json
        }

        if [ -f "coordination/coverage.out" ]; then
            # Parse go coverage output
            COVERAGE=$(go tool cover -func=coordination/coverage.out | grep total | awk '{print $3}' | sed 's/%//')
            echo "{\"coverage\":$COVERAGE}" > coordination/coverage_report_raw.json
        elif [ ! -f "coordination/coverage_report_raw.json" ]; then
            echo '{"coverage":0}' > coordination/coverage_report_raw.json
        fi
        ;;

    java)
        # Run JaCoCo via Maven or Gradle
        if [ -f "pom.xml" ]; then
            if command_exists "mvn"; then
                echo "  Running Maven tests with JaCoCo coverage..."
                mvn test jacoco:report 2>/dev/null || {
                    echo "⚠️  Tests failed or no tests found"
                    echo '{"coverage":0}' > coordination/coverage_report_raw.json
                }

                # JaCoCo XML report location (Maven)
                if [ -f "target/site/jacoco/jacoco.xml" ]; then
                    # Parse JaCoCo XML for coverage percentage
                    if command_exists "xmllint"; then
                        LINE_COVERED=$(xmllint --xpath "sum(//counter[@type='LINE']/@covered)" target/site/jacoco/jacoco.xml)
                        LINE_MISSED=$(xmllint --xpath "sum(//counter[@type='LINE']/@missed)" target/site/jacoco/jacoco.xml)
                        TOTAL=$((LINE_COVERED + LINE_MISSED))
                        if [ $TOTAL -gt 0 ]; then
                            COVERAGE=$(echo "scale=2; $LINE_COVERED * 100 / $TOTAL" | bc)
                            echo "{\"coverage\":$COVERAGE,\"source\":\"target/site/jacoco/jacoco.xml\"}" > coordination/coverage_report_raw.json
                        else
                            echo '{"coverage":0}' > coordination/coverage_report_raw.json
                        fi
                    else
                        # Fallback without xmllint
                        echo '{"coverage":"see target/site/jacoco/index.html","source":"target/site/jacoco/jacoco.xml"}' > coordination/coverage_report_raw.json
                    fi
                elif [ ! -f "coordination/coverage_report_raw.json" ]; then
                    echo '{"coverage":0}' > coordination/coverage_report_raw.json
                fi
            else
                echo "❌ Maven not found for Java project"
                echo '{"error":"Maven not found"}' > coordination/coverage_report_raw.json
            fi
        elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
            GRADLE_CMD="gradle"
            [ -f "./gradlew" ] && GRADLE_CMD="./gradlew"

            if command_exists "gradle" || [ -f "./gradlew" ]; then
                echo "  Running Gradle tests with JaCoCo coverage..."
                $GRADLE_CMD test jacocoTestReport 2>/dev/null || {
                    echo "⚠️  Tests failed or no tests found"
                    echo '{"coverage":0}' > coordination/coverage_report_raw.json
                }

                # JaCoCo XML report location (Gradle)
                if [ -f "build/reports/jacoco/test/jacocoTestReport.xml" ]; then
                    # Parse JaCoCo XML for coverage percentage
                    if command_exists "xmllint"; then
                        LINE_COVERED=$(xmllint --xpath "sum(//counter[@type='LINE']/@covered)" build/reports/jacoco/test/jacocoTestReport.xml)
                        LINE_MISSED=$(xmllint --xpath "sum(//counter[@type='LINE']/@missed)" build/reports/jacoco/test/jacocoTestReport.xml)
                        TOTAL=$((LINE_COVERED + LINE_MISSED))
                        if [ $TOTAL -gt 0 ]; then
                            COVERAGE=$(echo "scale=2; $LINE_COVERED * 100 / $TOTAL" | bc)
                            echo "{\"coverage\":$COVERAGE,\"source\":\"build/reports/jacoco/test/jacocoTestReport.xml\"}" > coordination/coverage_report_raw.json
                        else
                            echo '{"coverage":0}' > coordination/coverage_report_raw.json
                        fi
                    else
                        # Fallback without xmllint
                        echo '{"coverage":"see build/reports/jacoco/test/html/index.html","source":"build/reports/jacoco/test/jacocoTestReport.xml"}' > coordination/coverage_report_raw.json
                    fi
                elif [ ! -f "coordination/coverage_report_raw.json" ]; then
                    echo '{"coverage":0}' > coordination/coverage_report_raw.json
                fi
            else
                echo "❌ Gradle not found for Java project"
                echo '{"error":"Gradle not found"}' > coordination/coverage_report_raw.json
            fi
        else
            echo "❌ No Maven or Gradle build file found"
            echo '{"error":"No build file"}' > coordination/coverage_report_raw.json
        fi
        ;;

    *)
        echo "❌ Unknown language. Cannot run coverage analysis."
        echo '{"error":"Unknown language"}' > coordination/coverage_report_raw.json
        ;;
esac

# Add metadata
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create final report with metadata
if command_exists "jq"; then
    jq ". + {\"timestamp\": \"$TIMESTAMP\", \"language\": \"$LANG\"}" \
        coordination/coverage_report_raw.json > coordination/coverage_report.json
else
    # Fallback if jq not available
    cat > coordination/coverage_report.json <<EOF
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "raw_results": $(cat coordination/coverage_report_raw.json)
}
EOF
fi

# Clean up
rm -f coordination/coverage_report_raw.json coordination/jest-results.json 2>/dev/null || true

echo "✅ Coverage analysis complete"
echo "📁 Results saved to: coordination/coverage_report.json"

# Display summary if jq available
if command_exists "jq"; then
    if [ "$LANG" = "python" ]; then
        COVERAGE=$(jq -r '.totals.percent_covered // 0' coordination/coverage_report.json 2>/dev/null || echo "0")
        echo "📊 Overall coverage: $COVERAGE%"
    elif [ "$LANG" = "go" ] || [ "$LANG" = "java" ]; then
        COVERAGE=$(jq -r '.coverage // 0' coordination/coverage_report.json 2>/dev/null || echo "0")
        echo "📊 Overall coverage: $COVERAGE%"
    fi
fi
