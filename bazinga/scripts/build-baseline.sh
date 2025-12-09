#!/bin/bash
# Build Baseline Script for BAZINGA Orchestration
# Purpose: Detect project language and run build to establish baseline
# Usage: bash bazinga/scripts/build-baseline.sh <SESSION_ID>
# Output: bazinga/artifacts/<SESSION_ID>/build_baseline.log

set -e

SESSION_ID="${1:-unknown}"
OUTPUT_DIR="bazinga/artifacts/${SESSION_ID}"
LOG_FILE="${OUTPUT_DIR}/build_baseline.log"
STATUS_FILE="${OUTPUT_DIR}/build_baseline_status.txt"

mkdir -p "$OUTPUT_DIR"

detect_and_build() {
    echo "Build Baseline - $(date -Iseconds)" > "$LOG_FILE"
    echo "Session: $SESSION_ID" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Detect project type and run appropriate build
    if [ -f "package.json" ]; then
        echo "Detected: Node.js/TypeScript" >> "$LOG_FILE"
        if npm run build >> "$LOG_FILE" 2>&1 || (npm install && npm run build) >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "go.mod" ]; then
        echo "Detected: Go" >> "$LOG_FILE"
        if go build ./... >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "pom.xml" ]; then
        echo "Detected: Java (Maven)" >> "$LOG_FILE"
        if mvn compile -q >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        echo "Detected: Java (Gradle)" >> "$LOG_FILE"
        if ./gradlew compileJava -q >> "$LOG_FILE" 2>&1 || gradle compileJava -q >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        echo "Detected: Python" >> "$LOG_FILE"
        if python -m compileall . >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "Gemfile" ]; then
        echo "Detected: Ruby" >> "$LOG_FILE"
        if bundle check >> "$LOG_FILE" 2>&1 || bundle install >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    elif [ -f "Cargo.toml" ]; then
        echo "Detected: Rust" >> "$LOG_FILE"
        if cargo check >> "$LOG_FILE" 2>&1; then
            echo "success" > "$STATUS_FILE"
            exit 0
        else
            echo "error" > "$STATUS_FILE"
            exit 1
        fi
    else
        echo "No recognized build system detected" >> "$LOG_FILE"
        echo "skipped" > "$STATUS_FILE"
        exit 0
    fi
}

detect_and_build
