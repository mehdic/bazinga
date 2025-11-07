#!/bin/bash
#
# Test Coverage Analyzer - Bash Version
#
# Runs test coverage analysis based on project language
#

set -e

echo "🧪 Test Coverage Analysis Starting..."

# Create coordination directory if it doesn't exist
mkdir -p coordination

# Detect project language and test framework
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
    LANG="python"
elif [ -f "package.json" ]; then
    LANG="javascript"
elif [ -f "go.mod" ]; then
    LANG="go"
else
    LANG="unknown"
fi

echo "📋 Detected language: $LANG"

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Run coverage based on language
case $LANG in
    python)
        # Check for pytest and pytest-cov
        if ! command_exists "pytest"; then
            echo "⚙️  Installing pytest..."
            pip install pytest pytest-cov --quiet
        elif ! python -c "import pytest_cov" 2>/dev/null; then
            echo "⚙️  Installing pytest-cov..."
            pip install pytest-cov --quiet
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
        # Check for jest
        if [ ! -f "node_modules/.bin/jest" ]; then
            echo "⚙️  Jest not found. Please install: npm install --save-dev jest"
            echo '{"coverageMap":{}}' > coordination/coverage_report_raw.json
        else
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
    elif [ "$LANG" = "go" ]; then
        COVERAGE=$(jq -r '.coverage // 0' coordination/coverage_report.json 2>/dev/null || echo "0")
        echo "📊 Overall coverage: $COVERAGE%"
    fi
fi
