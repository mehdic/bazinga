#!/bin/bash
#
# Security Scanner - Bash Version
#
# Runs security vulnerability scans based on mode (basic/advanced)
# Mode is controlled via SECURITY_SCAN_MODE environment variable
#

# Don't exit on error for graceful degradation
set +e

# Get mode from environment (default: basic)
MODE="${SECURITY_SCAN_MODE:-basic}"

echo "🔒 Security Scan Starting (Mode: $MODE)..."

# Create coordination directory if it doesn't exist
mkdir -p coordination

# Initialize status tracking
SCAN_STATUS="success"
SCAN_ERROR=""
TOOL_USED="none"

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "coordination/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' coordination/skills_config.json 2>/dev/null || echo "lite")
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
            cat > coordination/security_scan.json << EOF
{
  "status": "skipped",
  "scan_mode": "$MODE",
  "language": "$LANG",
  "reason": "$tool_name not installed",
  "recommendation": "Install with: $install_cmd",
  "impact": "Security scan was skipped. Install $tool_name for vulnerability detection.",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
            exit 0
        else
            # Advanced mode: Try to install, fail if it doesn't work
            echo "⚙️  Installing $tool..."
            if ! eval "$install_cmd" 2>/dev/null; then
                echo "❌ Failed to install $tool_name"
                cat > coordination/security_scan.json << EOF
{
  "status": "error",
  "scan_mode": "$MODE",
  "language": "$LANG",
  "reason": "$tool_name required but not installed",
  "recommendation": "Install with: $install_cmd",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
                exit 1
            fi
        fi
    fi
}

# Legacy function for backward compatibility
install_if_missing() {
    local tool=$1
    local install_cmd=$2
    check_tool_or_skip "$tool" "$install_cmd" "$tool"
}

# Run scan based on mode and language
case $MODE in
    basic)
        echo "⚡ Running BASIC scan (fast, high/medium severity only)..."

        case $LANG in
            python)
                # Check for bandit with graceful degradation
                check_tool_or_skip "bandit" "pip install bandit" "bandit (Python security scanner)"

                TOOL_USED="bandit"
                # Basic: High/medium severity only (-ll flag)
                echo "  Running bandit (high/medium severity)..."
                if ! bandit -r . -f json -o coordination/security_scan_raw.json -ll 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="Bandit scan failed or had errors"
                    echo '{"results":[]}' > coordination/security_scan_raw.json
                fi
                ;;

            javascript)
                TOOL_USED="npm-audit"
                # npm audit is built-in
                echo "  Running npm audit (high severity)..."
                if ! npm audit --audit-level=high --json > coordination/security_scan_raw.json 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="npm audit failed (possibly network issue)"
                    echo '{"vulnerabilities":{}}' > coordination/security_scan_raw.json
                fi
                ;;

            go)
                # Check for gosec with graceful degradation
                check_tool_or_skip "gosec" "go install github.com/securego/gosec/v2/cmd/gosec@latest" "gosec (Go security scanner)"

                export PATH=$PATH:$(go env GOPATH)/bin
                TOOL_USED="gosec"
                echo "  Running gosec (high severity)..."
                if ! gosec -severity high -fmt json -out coordination/security_scan_raw.json ./... 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="gosec scan failed"
                    echo '{"issues":[]}' > coordination/security_scan_raw.json
                fi
                ;;

            ruby)
                # Check for brakeman with graceful degradation
                check_tool_or_skip "brakeman" "gem install brakeman" "brakeman (Ruby security scanner)"

                TOOL_USED="brakeman"
                echo "  Running brakeman (high severity)..."
                if ! brakeman -f json -o coordination/security_scan_raw.json --severity-level 1 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="brakeman scan failed"
                    echo '{"warnings":[]}' > coordination/security_scan_raw.json
                fi
                ;;

            java)
                # Check for SpotBugs (via Maven or Gradle)
                if [ -f "pom.xml" ]; then
                    TOOL_USED="spotbugs-maven"
                    echo "  Running SpotBugs via Maven (high priority)..."
                    if command_exists "mvn"; then
                        if ! mvn compile spotbugs:spotbugs -Dspotbugs.effort=Max -Dspotbugs.threshold=High 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="SpotBugs Maven scan failed"
                        fi
                        # Check if SpotBugs report exists
                        if [ -f "target/spotbugsXml.xml" ]; then
                            # Convert XML to JSON if possible
                            echo '{"tool":"spotbugs","source":"target/spotbugsXml.xml"}' > coordination/security_scan_raw.json
                        else
                            echo '{"issues":[]}' > coordination/security_scan_raw.json
                        fi
                    else
                        SCAN_STATUS="error"
                        SCAN_ERROR="Maven not found for Java project"
                        echo '{"issues":[]}' > coordination/security_scan_raw.json
                    fi
                elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
                    TOOL_USED="spotbugs-gradle"
                    echo "  Running SpotBugs via Gradle (high priority)..."
                    if command_exists "gradle" || command_exists "./gradlew"; then
                        GRADLE_CMD="gradle"
                        [ -f "./gradlew" ] && GRADLE_CMD="./gradlew"

                        if ! $GRADLE_CMD spotbugsMain 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="SpotBugs Gradle scan failed"
                        fi
                        # Check for Gradle SpotBugs report
                        if [ -f "build/reports/spotbugs/main.xml" ]; then
                            echo '{"tool":"spotbugs","source":"build/reports/spotbugs/main.xml"}' > coordination/security_scan_raw.json
                        else
                            echo '{"issues":[]}' > coordination/security_scan_raw.json
                        fi
                    else
                        SCAN_STATUS="error"
                        SCAN_ERROR="Gradle not found for Java project"
                        echo '{"issues":[]}' > coordination/security_scan_raw.json
                    fi
                else
                    SCAN_STATUS="error"
                    SCAN_ERROR="No Maven or Gradle build file found for Java project"
                    echo '{"issues":[]}' > coordination/security_scan_raw.json
                fi
                ;;

            *)
                echo "❌ Unknown language. Cannot run security scan."
                SCAN_STATUS="error"
                SCAN_ERROR="Unknown or unsupported language"
                echo '{"issues":[]}' > coordination/security_scan_raw.json
                ;;
        esac

        echo "✅ Basic security scan complete (5-10s)"
        ;;

    advanced)
        echo "🔍 Running ADVANCED scan (comprehensive, all severities)..."

        case $LANG in
            python)
                TOOL_USED="bandit+semgrep"
                # Check for required tools with graceful degradation
                check_tool_or_skip "bandit" "pip install bandit" "bandit (Python security scanner)"

                # Semgrep is optional even in advanced mode (fallback to bandit only)
                if ! command_exists "semgrep"; then
                    echo "  semgrep not installed, using bandit only"
                    TOOL_USED="bandit"
                fi

                # Run bandit (all severities)
                echo "  Running bandit (all severities)..."
                if ! bandit -r . -f json -o coordination/bandit_full.json 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }Bandit scan failed"
                    echo '{"results":[]}' > coordination/bandit_full.json
                fi

                # Run semgrep if available (comprehensive patterns)
                if command_exists "semgrep"; then
                    echo "  Running semgrep (security patterns)..."
                    if ! semgrep --config=auto --json -o coordination/semgrep.json 2>/dev/null; then
                        SCAN_STATUS="partial"
                        SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }Semgrep scan failed"
                        echo '{"results":[]}' > coordination/semgrep.json
                    fi
                else
                    echo '{"results":[]}' > coordination/semgrep.json
                fi

                # Combine results
                if command_exists "jq"; then
                    jq -s '{"bandit": .[0], "semgrep": .[1]}' coordination/bandit_full.json coordination/semgrep.json > coordination/security_scan_raw.json
                else
                    cat coordination/bandit_full.json > coordination/security_scan_raw.json
                fi
                ;;

            javascript)
                TOOL_USED="npm-audit"
                # Full npm audit
                echo "  Running npm audit (all severabilities)..."
                if ! npm audit --json > coordination/npm_audit.json 2>/dev/null; then
                    SCAN_STATUS="partial"
                    SCAN_ERROR="npm audit failed (possibly network issue)"
                    echo '{"vulnerabilities":{}}' > coordination/npm_audit.json
                fi

                # Try eslint with security plugin if available
                if npm list eslint-plugin-security &> /dev/null; then
                    TOOL_USED="npm-audit+eslint-security"
                    echo "  Running eslint security plugin..."
                    if ! npx eslint . --plugin security --format json > coordination/eslint_security.json 2>/dev/null; then
                        SCAN_STATUS="partial"
                        SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }eslint-security scan failed"
                        echo '[]' > coordination/eslint_security.json
                    fi

                    # Combine if jq available
                    if command_exists "jq"; then
                        jq -s '{"npm_audit": .[0], "eslint": .[1]}' coordination/npm_audit.json coordination/eslint_security.json > coordination/security_scan_raw.json
                    else
                        cat coordination/npm_audit.json > coordination/security_scan_raw.json
                    fi
                else
                    cat coordination/npm_audit.json > coordination/security_scan_raw.json
                fi
                ;;

            go)
                TOOL_USED="gosec"
                # Install gosec if needed
                if ! command_exists "gosec"; then
                    echo "⚙️  Installing gosec..."
                    if ! go install github.com/securego/gosec/v2/cmd/gosec@latest; then
                        SCAN_STATUS="error"
                        SCAN_ERROR="Failed to install gosec"
                        echo '{"issues":[]}' > coordination/security_scan_raw.json
                    else
                        export PATH=$PATH:$(go env GOPATH)/bin
                    fi
                fi

                if [ "$SCAN_STATUS" != "error" ]; then
                    echo "  Running gosec (all severities)..."
                    if ! gosec -fmt json -out coordination/security_scan_raw.json ./... 2>/dev/null; then
                        SCAN_STATUS="partial"
                        SCAN_ERROR="gosec scan failed"
                        echo '{"issues":[]}' > coordination/security_scan_raw.json
                    fi
                fi
                ;;

            ruby)
                TOOL_USED="brakeman"
                # Install brakeman if needed
                if ! install_if_missing "brakeman" "gem install brakeman"; then
                    SCAN_STATUS="error"
                    SCAN_ERROR="Failed to install brakeman"
                    echo '{"warnings":[]}' > coordination/security_scan_raw.json
                else
                    echo "  Running brakeman (all findings)..."
                    if ! brakeman -f json -o coordination/security_scan_raw.json 2>/dev/null; then
                        SCAN_STATUS="partial"
                        SCAN_ERROR="brakeman scan failed"
                        echo '{"warnings":[]}' > coordination/security_scan_raw.json
                    fi
                fi
                ;;

            java)
                TOOL_USED="spotbugs+semgrep+owasp"
                # Advanced mode: SpotBugs + Semgrep + OWASP Dependency Check

                # Run SpotBugs (all priorities)
                if [ -f "pom.xml" ]; then
                    echo "  Running SpotBugs via Maven (all priorities)..."
                    if command_exists "mvn"; then
                        if ! mvn compile spotbugs:spotbugs -Dspotbugs.effort=Max 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="SpotBugs Maven scan failed"
                        fi

                        # Run OWASP Dependency Check
                        echo "  Running OWASP Dependency Check..."
                        if ! mvn org.owasp:dependency-check-maven:check 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }OWASP Dependency Check failed"
                        fi
                    else
                        SCAN_STATUS="error"
                        SCAN_ERROR="Maven not found for Java project"
                    fi
                elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
                    echo "  Running SpotBugs via Gradle (all priorities)..."
                    GRADLE_CMD="gradle"
                    [ -f "./gradlew" ] && GRADLE_CMD="./gradlew"

                    if command_exists "gradle" || [ -f "./gradlew" ]; then
                        if ! $GRADLE_CMD spotbugsMain 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="SpotBugs Gradle scan failed"
                        fi

                        # Run OWASP Dependency Check for Gradle
                        echo "  Running OWASP Dependency Check..."
                        if ! $GRADLE_CMD dependencyCheckAnalyze 2>/dev/null; then
                            SCAN_STATUS="partial"
                            SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }OWASP Dependency Check failed"
                        fi
                    else
                        SCAN_STATUS="error"
                        SCAN_ERROR="Gradle not found for Java project"
                    fi
                fi

                # Run semgrep if available
                if command_exists "semgrep"; then
                    echo "  Running semgrep for Java..."
                    if ! semgrep --config=auto --json -o coordination/semgrep_java.json 2>/dev/null; then
                        SCAN_STATUS="partial"
                        SCAN_ERROR="${SCAN_ERROR:+$SCAN_ERROR; }Semgrep scan failed"
                        echo '{"results":[]}' > coordination/semgrep_java.json
                    fi
                fi

                # Consolidate Java results
                echo '{"tool":"spotbugs+owasp+semgrep","status":"see_build_reports"}' > coordination/security_scan_raw.json
                ;;

            *)
                echo "❌ Unknown language. Cannot run security scan."
                SCAN_STATUS="error"
                SCAN_ERROR="Unknown or unsupported language"
                echo '{"issues":[]}' > coordination/security_scan_raw.json
                ;;
        esac

        echo "✅ Advanced security scan complete (30-60s)"
        ;;

    *)
        echo "❌ Invalid mode: $MODE (use 'basic' or 'advanced')"
        exit 1
        ;;
esac

# Add metadata to results
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create final report with metadata and status
if command_exists "jq"; then
    jq ". + {\"scan_mode\": \"$MODE\", \"timestamp\": \"$TIMESTAMP\", \"language\": \"$LANG\", \"status\": \"$SCAN_STATUS\", \"tool\": \"$TOOL_USED\", \"error\": \"$SCAN_ERROR\"}" \
        coordination/security_scan_raw.json > coordination/security_scan.json
else
    # Fallback if jq not available - simple JSON append
    cat > coordination/security_scan.json <<EOF
{
  "scan_mode": "$MODE",
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "status": "$SCAN_STATUS",
  "tool": "$TOOL_USED",
  "error": "$SCAN_ERROR",
  "raw_results": $(cat coordination/security_scan_raw.json)
}
EOF
fi

# Clean up intermediate files
rm -f coordination/bandit_full.json coordination/semgrep.json coordination/npm_audit.json coordination/eslint_security.json coordination/security_scan_raw.json 2>/dev/null || true

# Report status
echo "📊 Scan mode: $MODE | Language: $LANG | Status: $SCAN_STATUS"
if [ "$SCAN_STATUS" != "success" ]; then
    echo "⚠️  WARNING: $SCAN_ERROR"
fi
echo "📁 Results saved to: coordination/security_scan.json"
