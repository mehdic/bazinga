#!/bin/bash
# Build Baseline Script for BAZINGA Orchestration
# Purpose: Detect project language and run build to establish baseline
# Usage: bash bazinga/scripts/build-baseline.sh <SESSION_ID>
# Output: bazinga/artifacts/<SESSION_ID>/build_baseline.log
#
# SECURITY: By default, uses safe checks that don't execute arbitrary scripts.
# Set ALLOW_BASELINE_BUILD=1 to enable full build (runs npm install, bundle install, etc.)

set -e

SESSION_ID="${1:-unknown}"
OUTPUT_DIR="bazinga/artifacts/${SESSION_ID}"
LOG_FILE="${OUTPUT_DIR}/build_baseline.log"
STATUS_FILE="${OUTPUT_DIR}/build_baseline_status.txt"
ALLOW_BUILD="${ALLOW_BASELINE_BUILD:-0}"

mkdir -p "$OUTPUT_DIR"

detect_and_build() {
    echo "Build Baseline - $(date -Iseconds)" > "$LOG_FILE"
    echo "Session: $SESSION_ID" >> "$LOG_FILE"
    echo "Safe mode: $([ "$ALLOW_BUILD" = "1" ] && echo "OFF (full build)" || echo "ON (no scripts)")" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Detect project type and run appropriate build
    if [ -f "package.json" ]; then
        echo "Detected: Node.js/TypeScript" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # Full build (may run arbitrary scripts)
            if npm run build >> "$LOG_FILE" 2>&1 || (npm ci && npm run build) >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            # Safe check: type-check only using LOCAL tsc (no network fetch)
            # Use ./node_modules/.bin/tsc to avoid npx fetching from network
            if [ -x "./node_modules/.bin/tsc" ]; then
                if ./node_modules/.bin/tsc --noEmit >> "$LOG_FILE" 2>&1; then
                    echo "success" > "$STATUS_FILE"
                    exit 0
                else
                    echo "error" > "$STATUS_FILE"
                    exit 1
                fi
            elif [ -f "tsconfig.json" ]; then
                # TypeScript config exists but tsc not installed locally
                echo "skipped (no local tsc, run npm install first)" > "$STATUS_FILE"
                echo "Note: tsc not found locally. Run npm install to enable type checking." >> "$LOG_FILE"
                exit 0
            else
                # No TypeScript, just validate package.json exists
                echo "success (no tsc)" > "$STATUS_FILE"
                exit 0
            fi
        fi
    elif [ -f "go.mod" ]; then
        echo "Detected: Go" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # go build can execute arbitrary code via go:generate, cgo, plugins
            if go build ./... >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            echo "skipped (safe mode - go build disabled)" > "$STATUS_FILE"
            echo "Note: go build disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable." >> "$LOG_FILE"
            exit 0
        fi
    elif [ -f "pom.xml" ]; then
        echo "Detected: Java (Maven)" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # mvn compile can execute arbitrary plugins
            if mvn compile -q >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            echo "skipped (safe mode - mvn compile disabled)" > "$STATUS_FILE"
            echo "Note: mvn compile disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable." >> "$LOG_FILE"
            exit 0
        fi
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        echo "Detected: Java (Gradle)" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # gradle can execute arbitrary build scripts
            if ./gradlew compileJava -q >> "$LOG_FILE" 2>&1 || gradle compileJava -q >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            echo "skipped (safe mode - gradle compile disabled)" > "$STATUS_FILE"
            echo "Note: gradle compile disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable." >> "$LOG_FILE"
            exit 0
        fi
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        echo "Detected: Python" >> "$LOG_FILE"
        # Safe: compileall with exclusions for venv directories
        if python -m compileall -q -x '(^|/)(venv|\.venv|env|site-packages|__pycache__)/' . >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "Gemfile" ]; then
        echo "Detected: Ruby" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # Full install (may run arbitrary gem extensions)
            if bundle check >> "$LOG_FILE" 2>&1 || bundle install --quiet >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            # Safe check: only verify lockfile, no install
            if bundle check >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "warning (bundle check failed, run with ALLOW_BASELINE_BUILD=1)" > "$STATUS_FILE"
                exit 0
            fi
        fi
    elif [ -f "Cargo.toml" ]; then
        echo "Detected: Rust" >> "$LOG_FILE"
        if [ "$ALLOW_BUILD" = "1" ]; then
            # cargo check can execute build scripts and proc macros
            if cargo check >> "$LOG_FILE" 2>&1; then
                echo "success" > "$STATUS_FILE"
                exit 0
            else
                echo "error" > "$STATUS_FILE"
                exit 1
            fi
        else
            echo "skipped (safe mode - cargo check disabled)" > "$STATUS_FILE"
            echo "Note: cargo check disabled in safe mode. Set ALLOW_BASELINE_BUILD=1 to enable." >> "$LOG_FILE"
            exit 0
        fi
    else
        echo "No recognized build system detected" >> "$LOG_FILE"
        echo "skipped" > "$STATUS_FILE"
        exit 0
    fi
}

detect_and_build
