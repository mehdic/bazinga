#!/bin/bash
#
# Code Linter - Bash Version
#
# Runs code quality linters based on project language
#

set -e

echo "📋 Code Linting Starting..."

# Create coordination directory if it doesn't exist
mkdir -p coordination

# Detect project language
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
    LANG="python"
elif [ -f "package.json" ]; then
    LANG="javascript"
elif [ -f "go.mod" ]; then
    LANG="go"
elif [ -f "Gemfile" ] || [ -f "*.gemspec" ]; then
    LANG="ruby"
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

# Run linter based on language
case $LANG in
    python)
        # Prefer ruff (fast), fallback to pylint
        if command_exists "ruff"; then
            TOOL="ruff"
            echo "  Running ruff..."
            ruff check . --output-format=json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
        elif command_exists "pylint"; then
            TOOL="pylint"
            echo "  Running pylint..."
            pylint --output-format=json **/*.py > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
        else
            echo "⚠️  No Python linter found. Install: pip install ruff"
            TOOL="none"
            echo '[]' > coordination/lint_results_raw.json
        fi
        ;;

    javascript)
        # Check for eslint
        if [ -f "node_modules/.bin/eslint" ] || command_exists "eslint"; then
            TOOL="eslint"
            echo "  Running eslint..."
            npx eslint . --format json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
        else
            echo "⚠️  eslint not found. Install: npm install --save-dev eslint"
            TOOL="none"
            echo '[]' > coordination/lint_results_raw.json
        fi
        ;;

    go)
        # Check for golangci-lint
        if command_exists "golangci-lint"; then
            TOOL="golangci-lint"
            echo "  Running golangci-lint..."
            golangci-lint run --out-format json > coordination/lint_results_raw.json 2>/dev/null || echo '{"Issues":[]}' > coordination/lint_results_raw.json
        else
            echo "⚠️  golangci-lint not found. Install: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
            TOOL="none"
            echo '{"Issues":[]}' > coordination/lint_results_raw.json
        fi
        ;;

    ruby)
        # Check for rubocop
        if command_exists "rubocop"; then
            TOOL="rubocop"
            echo "  Running rubocop..."
            rubocop --format json > coordination/lint_results_raw.json 2>/dev/null || echo '{"files":[]}' > coordination/lint_results_raw.json
        else
            echo "⚠️  rubocop not found. Install: gem install rubocop"
            TOOL="none"
            echo '{"files":[]}' > coordination/lint_results_raw.json
        fi
        ;;

    java)
        # Check for Maven or Gradle
        if [ -f "pom.xml" ]; then
            if command_exists "mvn"; then
                TOOL="checkstyle+pmd-maven"
                echo "  Running Checkstyle via Maven..."
                mvn checkstyle:check 2>/dev/null || true

                echo "  Running PMD via Maven..."
                mvn pmd:check 2>/dev/null || true

                # Consolidate results (Checkstyle XML + PMD XML)
                if [ -f "target/checkstyle-result.xml" ] || [ -f "target/pmd.xml" ]; then
                    echo '{"tool":"checkstyle+pmd","checkstyle":"target/checkstyle-result.xml","pmd":"target/pmd.xml"}' > coordination/lint_results_raw.json
                else
                    echo '{"issues":[]}' > coordination/lint_results_raw.json
                fi
            else
                echo "❌ Maven not found for Java project"
                TOOL="none"
                echo '{"error":"Maven not found"}' > coordination/lint_results_raw.json
            fi
        elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
            GRADLE_CMD="gradle"
            [ -f "./gradlew" ] && GRADLE_CMD="./gradlew"

            if command_exists "gradle" || [ -f "./gradlew" ]; then
                TOOL="checkstyle+pmd-gradle"
                echo "  Running Checkstyle via Gradle..."
                $GRADLE_CMD checkstyleMain 2>/dev/null || true

                echo "  Running PMD via Gradle..."
                $GRADLE_CMD pmdMain 2>/dev/null || true

                # Consolidate results (Checkstyle XML + PMD XML)
                if [ -f "build/reports/checkstyle/main.xml" ] || [ -f "build/reports/pmd/main.xml" ]; then
                    echo '{"tool":"checkstyle+pmd","checkstyle":"build/reports/checkstyle/main.xml","pmd":"build/reports/pmd/main.xml"}' > coordination/lint_results_raw.json
                else
                    echo '{"issues":[]}' > coordination/lint_results_raw.json
                fi
            else
                echo "❌ Gradle not found for Java project"
                TOOL="none"
                echo '{"error":"Gradle not found"}' > coordination/lint_results_raw.json
            fi
        else
            echo "❌ No Maven or Gradle build file found"
            TOOL="none"
            echo '{"error":"No build file"}' > coordination/lint_results_raw.json
        fi
        ;;

    *)
        echo "❌ Unknown language. Cannot run linting."
        TOOL="none"
        echo '{"error":"Unknown language"}' > coordination/lint_results_raw.json
        ;;
esac

# Add metadata
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create final report with metadata
if command_exists "jq"; then
    jq ". + {\"timestamp\": \"$TIMESTAMP\", \"language\": \"$LANG\", \"tool\": \"$TOOL\"}" \
        coordination/lint_results_raw.json > coordination/lint_results.json
else
    # Fallback if jq not available
    cat > coordination/lint_results.json <<EOF
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "tool": "$TOOL",
  "raw_results": $(cat coordination/lint_results_raw.json)
}
EOF
fi

# Clean up
rm -f coordination/lint_results_raw.json 2>/dev/null || true

echo "✅ Linting complete"
echo "📁 Results saved to: coordination/lint_results.json"

# Display summary if jq available
if command_exists "jq" && [ "$TOOL" != "none" ]; then
    if [ "$LANG" = "python" ] && [ "$TOOL" = "ruff" ]; then
        ISSUE_COUNT=$(jq '. | length' coordination/lint_results.json 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    elif [ "$LANG" = "go" ]; then
        ISSUE_COUNT=$(jq '.Issues | length // 0' coordination/lint_results.json 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    fi
fi
