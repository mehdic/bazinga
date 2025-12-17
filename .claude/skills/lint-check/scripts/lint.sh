#!/bin/bash
#
# Code Linter - Bash Version
#
# Runs code quality linters based on project language
#

# Don't exit on error for graceful degradation
set +e

echo "📋 Code Linting Starting..."

# Get current session ID from database
get_current_session_id() {
    local db_path="bazinga/bazinga.db"
    if [ ! -f "$db_path" ]; then
        echo "bazinga_default"
        return
    fi

    local session_id=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$db_path')
    cursor = conn.execute('SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1')
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print('bazinga_default')
    conn.close()
except:
    print('bazinga_default')
" 2>/dev/null || echo "bazinga_default")

    echo "$session_id"
}

SESSION_ID=$(get_current_session_id)
OUTPUT_DIR="bazinga/artifacts/$SESSION_ID/skills"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/lint_results.json"

echo "📁 Output directory: $OUTPUT_DIR"

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "bazinga/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' bazinga/skills_config.json 2>/dev/null || echo "lite")
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
            cat > $OUTPUT_FILE << EOF
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
            cat > $OUTPUT_FILE << EOF
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
                    run_with_timeout ruff check $PYTHON_FILES --output-format=json > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
                else
                    echo '[]' > bazinga/lint_results_raw.json
                fi
            else
                run_with_timeout ruff check . --output-format=json > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
            fi
        elif command_exists "pylint"; then
            TOOL="pylint"
            echo "  Running pylint..."
            if [ -n "$CHANGED_FILES" ]; then
                PYTHON_FILES=$(echo "$CHANGED_FILES" | grep '\.py$' || echo "")
                if [ -n "$PYTHON_FILES" ]; then
                    run_with_timeout pylint --output-format=json $PYTHON_FILES > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
                else
                    echo '[]' > bazinga/lint_results_raw.json
                fi
            else
                run_with_timeout pylint --output-format=json **/*.py > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
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
                run_with_timeout npx eslint $JS_FILES --format json > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
            else
                echo '[]' > bazinga/lint_results_raw.json
            fi
        else
            run_with_timeout npx eslint . --format json > bazinga/lint_results_raw.json 2>/dev/null || echo '[]' > bazinga/lint_results_raw.json
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
                run_with_timeout golangci-lint run --new --out-format json > bazinga/lint_results_raw.json 2>/dev/null || echo '{"Issues":[]}' > bazinga/lint_results_raw.json
            else
                echo '{"Issues":[]}' > bazinga/lint_results_raw.json
            fi
        else
            run_with_timeout golangci-lint run --out-format json --timeout ${LINT_TIMEOUT}s > bazinga/lint_results_raw.json 2>/dev/null || echo '{"Issues":[]}' > bazinga/lint_results_raw.json
        fi
        ;;

    ruby)
        # Check for rubocop with graceful degradation
        check_tool_or_skip "rubocop" "gem install rubocop" "rubocop (Ruby linter)"

        TOOL="rubocop"
        echo "  Running rubocop..."
        rubocop --format json > bazinga/lint_results_raw.json 2>/dev/null || echo '{"files":[]}' > bazinga/lint_results_raw.json
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
                    echo '{"tool":"checkstyle+pmd","checkstyle":"target/checkstyle-result.xml","pmd":"target/pmd.xml"}' > bazinga/lint_results_raw.json
                else
                    echo '{"issues":[]}' > bazinga/lint_results_raw.json
                fi
            else
                echo "❌ Maven not found for Java project"
                TOOL="none"
                echo '{"error":"Maven not found"}' > bazinga/lint_results_raw.json
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
                    echo '{"tool":"checkstyle+pmd","checkstyle":"build/reports/checkstyle/main.xml","pmd":"build/reports/pmd/main.xml"}' > bazinga/lint_results_raw.json
                else
                    echo '{"issues":[]}' > bazinga/lint_results_raw.json
                fi
            else
                echo "❌ Gradle not found for Java project"
                TOOL="none"
                echo '{"error":"Gradle not found"}' > bazinga/lint_results_raw.json
            fi
        else
            echo "❌ No Maven or Gradle build file found"
            TOOL="none"
            echo '{"error":"No build file"}' > bazinga/lint_results_raw.json
        fi
        ;;

    *)
        echo "❌ Unknown language. Cannot run linting."
        TOOL="none"
        echo '{"error":"Unknown language"}' > bazinga/lint_results_raw.json
        ;;
esac

# Add metadata
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create final report with metadata
if command_exists "jq"; then
    # Wrap results in object to handle both array and object inputs
    jq "{\"results\": ., \"timestamp\": \"$TIMESTAMP\", \"language\": \"$LANG\", \"tool\": \"$TOOL\"}" \
        bazinga/lint_results_raw.json > $OUTPUT_FILE
else
    # Fallback if jq not available
    cat > $OUTPUT_FILE <<EOF
{
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "tool": "$TOOL",
  "raw_results": $(cat bazinga/lint_results_raw.json)
}
EOF
fi

# Clean up
rm -f bazinga/lint_results_raw.json 2>/dev/null || true

echo "✅ Linting complete"
echo "📁 Results saved to: $OUTPUT_FILE"

# Save to database
echo "💾 Saving to database..."
DB_PATH="bazinga/bazinga.db"
DB_SCRIPT=".claude/skills/bazinga-db/scripts/bazinga_db.py"
SKILL_OUTPUT=$(cat "$OUTPUT_FILE")

python3 "$DB_SCRIPT" --db "$DB_PATH" --quiet save-skill-output \
    "$SESSION_ID" \
    "lint-check" \
    "$SKILL_OUTPUT" 2>/dev/null || echo "⚠️  Database save failed (non-fatal)"

# Display summary if jq available
# Note: Results are wrapped in {"results": ...} by the jq command above
if command_exists "jq" && [ "$TOOL" != "none" ]; then
    if [ "$LANG" = "python" ] && [ "$TOOL" = "ruff" ]; then
        # Ruff results are in .results array after wrapping
        ISSUE_COUNT=$(jq '.results | length // 0' $OUTPUT_FILE 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    elif [ "$LANG" = "go" ]; then
        # golangci-lint results are in .results.Issues after wrapping
        ISSUE_COUNT=$(jq '.results.Issues | length // 0' $OUTPUT_FILE 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    elif [ "$LANG" = "javascript" ] || [ "$LANG" = "typescript" ]; then
        # ESLint results are in .results array after wrapping
        ISSUE_COUNT=$(jq '[.results[].messages | length] | add // 0' $OUTPUT_FILE 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    elif [ "$LANG" = "ruby" ]; then
        # RuboCop results are in .results.offenses after wrapping
        ISSUE_COUNT=$(jq '.results.files | map(.offenses | length) | add // 0' $OUTPUT_FILE 2>/dev/null || echo "0")
        echo "📊 Issues found: $ISSUE_COUNT"
    fi
fi
