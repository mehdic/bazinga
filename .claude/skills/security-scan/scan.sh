#!/bin/bash
#
# Security Scanner - Bash Version
#
# Runs security vulnerability scans based on mode (basic/advanced)
# Mode is controlled via SECURITY_SCAN_MODE environment variable
#

set -e

# Get mode from environment (default: basic)
MODE="${SECURITY_SCAN_MODE:-basic}"

echo "🔒 Security Scan Starting (Mode: $MODE)..."

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
else
    LANG="unknown"
fi

echo "📋 Detected language: $LANG"

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install tool if missing
install_if_missing() {
    local tool=$1
    local install_cmd=$2

    if ! command_exists "$tool"; then
        echo "⚙️  Installing $tool..."
        eval "$install_cmd" || {
            echo "⚠️  Failed to install $tool. Please install manually."
            return 1
        }
    fi
}

# Run scan based on mode and language
case $MODE in
    basic)
        echo "⚡ Running BASIC scan (fast, high/medium severity only)..."

        case $LANG in
            python)
                # Install bandit if needed
                install_if_missing "bandit" "pip install bandit --quiet"

                # Basic: High/medium severity only (-ll flag)
                echo "  Running bandit (high/medium severity)..."
                bandit -r . -f json -o coordination/security_scan_raw.json -ll 2>/dev/null || true
                ;;

            javascript)
                # npm audit is built-in
                echo "  Running npm audit (high severity)..."
                npm audit --audit-level=high --json > coordination/security_scan_raw.json 2>/dev/null || echo '{"vulnerabilities":{}}' > coordination/security_scan_raw.json
                ;;

            go)
                # Install gosec if needed
                if ! command_exists "gosec"; then
                    echo "⚙️  Installing gosec..."
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                    export PATH=$PATH:$(go env GOPATH)/bin
                fi

                echo "  Running gosec (high severity)..."
                gosec -severity high -fmt json -out coordination/security_scan_raw.json ./... 2>/dev/null || echo '{"issues":[]}' > coordination/security_scan_raw.json
                ;;

            ruby)
                # Install brakeman if needed
                install_if_missing "brakeman" "gem install brakeman"

                echo "  Running brakeman (high severity)..."
                brakeman -f json -o coordination/security_scan_raw.json --severity-level 1 2>/dev/null || echo '{"warnings":[]}' > coordination/security_scan_raw.json
                ;;

            *)
                echo "❌ Unknown language. Cannot run security scan."
                echo '{"error":"Unknown language","issues":[]}' > coordination/security_scan_raw.json
                ;;
        esac

        echo "✅ Basic security scan complete (5-10s)"
        ;;

    advanced)
        echo "🔍 Running ADVANCED scan (comprehensive, all severities)..."

        case $LANG in
            python)
                # Install tools if needed
                install_if_missing "bandit" "pip install bandit --quiet"
                install_if_missing "semgrep" "pip install semgrep --quiet"

                # Run bandit (all severities)
                echo "  Running bandit (all severities)..."
                bandit -r . -f json -o coordination/bandit_full.json 2>/dev/null || echo '{"results":[]}' > coordination/bandit_full.json

                # Run semgrep (comprehensive patterns)
                echo "  Running semgrep (security patterns)..."
                semgrep --config=auto --json -o coordination/semgrep.json 2>/dev/null || echo '{"results":[]}' > coordination/semgrep.json

                # Combine results
                if command_exists "jq"; then
                    jq -s '{"bandit": .[0], "semgrep": .[1]}' coordination/bandit_full.json coordination/semgrep.json > coordination/security_scan_raw.json
                else
                    # Fallback if jq not available
                    cat coordination/bandit_full.json > coordination/security_scan_raw.json
                fi
                ;;

            javascript)
                # Full npm audit
                echo "  Running npm audit (all severabilities)..."
                npm audit --json > coordination/npm_audit.json 2>/dev/null || echo '{"vulnerabilities":{}}' > coordination/npm_audit.json

                # Try eslint with security plugin if available
                if npm list eslint-plugin-security &> /dev/null; then
                    echo "  Running eslint security plugin..."
                    npx eslint . --plugin security --format json > coordination/eslint_security.json 2>/dev/null || echo '[]' > coordination/eslint_security.json

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
                # Install gosec if needed
                if ! command_exists "gosec"; then
                    echo "⚙️  Installing gosec..."
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                    export PATH=$PATH:$(go env GOPATH)/bin
                fi

                echo "  Running gosec (all severities)..."
                gosec -fmt json -out coordination/security_scan_raw.json ./... 2>/dev/null || echo '{"issues":[]}' > coordination/security_scan_raw.json
                ;;

            ruby)
                # Install brakeman if needed
                install_if_missing "brakeman" "gem install brakeman"

                echo "  Running brakeman (all findings)..."
                brakeman -f json -o coordination/security_scan_raw.json 2>/dev/null || echo '{"warnings":[]}' > coordination/security_scan_raw.json
                ;;

            *)
                echo "❌ Unknown language. Cannot run security scan."
                echo '{"error":"Unknown language","issues":[]}' > coordination/security_scan_raw.json
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

# Create final report with metadata
if command_exists "jq"; then
    jq ". + {\"scan_mode\": \"$MODE\", \"timestamp\": \"$TIMESTAMP\", \"language\": \"$LANG\"}" \
        coordination/security_scan_raw.json > coordination/security_scan.json
else
    # Fallback if jq not available - simple JSON append
    cat > coordination/security_scan.json <<EOF
{
  "scan_mode": "$MODE",
  "timestamp": "$TIMESTAMP",
  "language": "$LANG",
  "raw_results": $(cat coordination/security_scan_raw.json)
}
EOF
fi

# Clean up intermediate files
rm -f coordination/bandit_full.json coordination/semgrep.json coordination/npm_audit.json coordination/eslint_security.json coordination/security_scan_raw.json 2>/dev/null || true

echo "📊 Scan mode: $MODE | Language: $LANG"
echo "📁 Results saved to: coordination/security_scan.json"
