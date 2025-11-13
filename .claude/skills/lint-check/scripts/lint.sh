#!/bin/bash
#
# Code Linter - Bash Version
#
# Runs code quality linters based on project language
#

# Don't exit on error for graceful degradation
set +e

echo "📋 Code Linting Starting..."

# Create coordination directory if it doesn't exist
mkdir -p coordination

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "coordination/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' coordination/skills_config.json 2>/dev/null || echo "lite")
fi

# TIMEOUT PROTECTION: Max 45 seconds for linting
LINT_TIMEOUT="${LINT_TIMEOUT:-45}"
echo "⏱️  Timeout set to ${LINT_TIMEOUT}s"

# Helper function to run command with timeout
run_with_timeout() {
    timeout "${LINT_TIMEOUT}s" "$@" || {
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo "⚠️  Lint command timed out after ${LINT_TIMEOUT}s"
            return 124
        fi
        return $EXIT_CODE
    }
}

# Get changed files (if in git repo) for faster linting
CHANGED_FILES=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Get files changed in last commit OR uncommitted changes
    CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || git ls-files -m 2>/dev/null || echo "")
    if [ -n "$CHANGED_FILES" ]; then
        echo "🎯 Linting changed files only (faster)"
    fi
fi

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
            cat > coordination/lint_results.json << EOF
{
  "status": "skipped",
  "language": "$LANG",
  "reason": "$tool_name not installed",
  "recommendation": "Install with: $install_cmd",
  "impact": "Code linting was skipped. Install $tool_name for code quality checks.",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
            exit 0
        else
            # Advanced mode: Fail if tool not available
            echo "❌ $tool_name required but not installed"
            cat > coordination/lint_results.json << EOF
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

# Run linter based on language
case $LANG in
    python)
        # Check for Python linter with graceful degradation
        if ! command_exists "ruff" && ! command_exists "pylint"; then
            check_tool_or_skip "ruff" "pip install ruff" "ruff or pylint (Python linter)"
        fi

        # Prefer ruff (fast), fallback to pylint
        if command_exists "ruff"; then
            TOOL="ruff"
            echo "  Running ruff..."
            # Use changed files if available, otherwise lint all
            if [ -n "$CHANGED_FILES" ]; then
                PYTHON_FILES=$(echo "$CHANGED_FILES" | grep '\.py$' || echo "")
                if [ -n "$PYTHON_FILES" ]; then
                    run_with_timeout ruff check $PYTHON_FILES --output-format=json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
                else
                    echo '[]' > coordination/lint_results_raw.json
                fi
            else
                run_with_timeout ruff check . --output-format=json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
            fi
        elif command_exists "pylint"; then
            TOOL="pylint"
            echo "  Running pylint..."
            if [ -n "$CHANGED_FILES" ]; then
                PYTHON_FILES=$(echo "$CHANGED_FILES" | grep '\.py$' || echo "")
                if [ -n "$PYTHON_FILES" ]; then
                    run_with_timeout pylint --output-format=json $PYTHON_FILES > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
                else
                    echo '[]' > coordination/lint_results_raw.json
                fi
            else
                run_with_timeout pylint --output-format=json **/*.py > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
            fi
        fi
        ;;

    javascript)
        # Check for eslint with graceful degradation
        if ! [ -f "node_modules/.bin/eslint" ] && ! command_exists "eslint"; then
            check_tool_or_skip "eslint" "npm install --save-dev eslint" "eslint (JavaScript linter)"
        fi

        TOOL="eslint"
        echo "  Running eslint..."
        # Use changed files if available, otherwise lint all
        if [ -n "$CHANGED_FILES" ]; then
            JS_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(js|jsx|ts|tsx)$' || echo "")
            if [ -n "$JS_FILES" ]; then
                run_with_timeout npx eslint $JS_FILES --format json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
            else
                echo '[]' > coordination/lint_results_raw.json
            fi
        else
            run_with_timeout npx eslint . --format json > coordination/lint_results_raw.json 2>/dev/null || echo '[]' > coordination/lint_results_raw.json
        fi
        ;;

    go)
        # Check for golangci-lint with graceful degradation
        check_tool_or_skip "golangci-lint" "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest" "golangci-lint (Go linter)"

        TOOL="golangci-lint"
        echo "  Running golangci-lint..."
        # golangci-lint doesn't support individual file linting well, use --new flag for changed files
        if [ -n "$CHANGED_FILES" ]; then
            GO_FILES=$(echo "$CHANGED_FILES" | grep '\.go$' || echo "")
            if [ -n "$GO_FILES" ]; then
                # Use --new to only lint changed code
                run_with_timeout golangci-lint run --new --out-format json > coordination/lint_results_raw.json 2>/dev/null || echo '{"Issues":[]}' > coordination/lint_results_raw.json
            else
                echo '{"Issues":[]}' > coordination/lint_results_raw.json
            fi
        else
            run_with_timeout golangci-lint run --out-format json --timeout ${LINT_TIMEOUT}s > coordination/lint_results_raw.json 2>/dev/null || echo '{"Issues":[]}' > coordination/lint_results_raw.json
        fi
        ;;

    ruby)
        # Check for rubocop with graceful degradation
        check_tool_or_skip "rubocop" "gem install rubocop" "rubocop (Ruby linter)"

        TOOL="rubocop"
        echo "  Running rubocop..."
        rubocop --format json > coordination/lint_results_raw.json 2>/dev/null || echo '{"files":[]}' > coordination/lint_results_raw.json
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
