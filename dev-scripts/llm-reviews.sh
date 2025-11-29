#!/bin/bash
#
# Multi-LLM Review Script for ULTRATHINK Plans
#
# Sends analysis/plan documents to OpenAI and Gemini for review,
# then returns their feedback for integration.
#
# Usage: ./dev-scripts/llm-reviews.sh <plan_file> [additional_files...]
#
# Environment variables required:
#   OPENAI_API_KEY - OpenAI API key
#   GEMINI_API_KEY - Google Gemini API key (optional if ENABLE_GEMINI=false)
#
# Optional environment variables:
#   ENABLE_GEMINI  - Set to "false" to skip Gemini review (default: true)
#                    Use in Claude Code Web where Gemini API is blocked.
#
# Example:
#   ./dev-scripts/llm-reviews.sh research/my-plan.md scripts/foo.sh src/bar.py
#
# Note: This script is for BAZINGA development only, not copied to clients.

# Don't use set -e to allow explicit error handling for API calls

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Model names (matching GitHub Actions workflow configuration)
# OpenAI: gpt-5 is reasoning model (temperature fixed at 1, needs high max_completion_tokens)
# Gemini: gemini-3-pro-preview (latest preview model)
OPENAI_MODEL="gpt-5"
GEMINI_MODEL="gemini-3-pro-preview"
OUTPUT_DIR="$REPO_ROOT/tmp/ultrathink-reviews"

# Enable/disable Gemini (default: true)
# Set ENABLE_GEMINI=false in Claude Code Web where Gemini API is blocked
ENABLE_GEMINI="${ENABLE_GEMINI:-true}"
AGENTS_DIR="$REPO_ROOT/agents"
MAX_FILE_SIZE_KB=100  # Warn if files exceed this size

# Temp files for large prompts (cleaned up on exit)
PROMPT_TEMP_FILE=""
CONTEXT_TEMP_FILE=""
cleanup() {
    [ -n "$PROMPT_TEMP_FILE" ] && [ -f "$PROMPT_TEMP_FILE" ] && rm -f "$PROMPT_TEMP_FILE"
    [ -n "$CONTEXT_TEMP_FILE" ] && [ -f "$CONTEXT_TEMP_FILE" ] && rm -f "$CONTEXT_TEMP_FILE"
}
trap cleanup EXIT

# Cross-platform date function (works on GNU and BSD/macOS)
iso_date() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Validate model name contains only safe URL characters
validate_model_name() {
    local model="$1"
    if [[ ! "$model" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        echo "❌ ERROR: Invalid model name '$model' - contains unsafe characters"
        exit 1
    fi
}

# Retry logic with exponential backoff
# Usage: retry_curl <output_file> <curl_args...>
# Returns: curl exit code (0 = success), prints HTTP code to stdout
retry_curl() {
    local output_file="$1"
    shift
    local max_retries=3
    local retry_count=0
    local delay=2
    local http_code
    local curl_exit

    while [ $retry_count -le $max_retries ]; do
        http_code=$(curl -s -w "%{http_code}" -o "$output_file" "$@")
        curl_exit=$?

        # Success
        if [ $curl_exit -eq 0 ] && [ "$http_code" -lt 400 ]; then
            echo "$http_code"
            return 0
        fi

        # Don't retry client errors (except rate limits)
        if [ $curl_exit -eq 0 ] && [ "$http_code" -ge 400 ] && [ "$http_code" -lt 500 ] && [ "$http_code" -ne 429 ]; then
            echo "$http_code"
            return 0  # Return success but with error code for caller to handle
        fi

        # Retryable error (network, 5xx, or 429)
        retry_count=$((retry_count + 1))
        if [ $retry_count -le $max_retries ]; then
            echo "  ⚠️ Attempt $retry_count failed (curl=$curl_exit, http=$http_code), retrying in ${delay}s..." >&2
            sleep $delay
            delay=$((delay * 2))
        fi
    done

    # Final failure
    echo "$http_code"
    return $curl_exit
}

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY environment variable not set"
    exit 1
fi

# Gemini API key only required if Gemini is enabled
if [ "$ENABLE_GEMINI" = "true" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY environment variable not set (or set ENABLE_GEMINI=false to skip)"
    exit 1
fi

# Validate model names for URL safety
validate_model_name "$OPENAI_MODEL"
if [ "$ENABLE_GEMINI" = "true" ]; then
    validate_model_name "$GEMINI_MODEL"
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <plan_file> [additional_files...]"
    echo ""
    echo "Example:"
    echo "  $0 research/my-plan.md dev-scripts/foo.sh"
    exit 1
fi

PLAN_FILE="$1"
shift
ADDITIONAL_FILES=("$@")

if [ ! -f "$PLAN_FILE" ]; then
    echo "❌ ERROR: Plan file not found: $PLAN_FILE"
    exit 1
fi

# Check file size and warn if too large
check_file_size() {
    local file="$1"
    local size_kb
    if [ -f "$file" ]; then
        size_kb=$(du -k "$file" | cut -f1)
        if [ "$size_kb" -gt "$MAX_FILE_SIZE_KB" ]; then
            echo "  ⚠️ Warning: $file is ${size_kb}KB (>${MAX_FILE_SIZE_KB}KB) - may exceed API limits"
        fi
    fi
}

# Create output directory
mkdir -p "$OUTPUT_DIR"

# -----------------------------------------------------------------------------
# Gather Context (using temp file to avoid shell memory issues)
# -----------------------------------------------------------------------------

echo "🔍 Gathering context for review..."

# Check plan file size
check_file_size "$PLAN_FILE"

# Create temp file for context (will be cleaned up on exit)
CONTEXT_TEMP_FILE=$(mktemp)

# Write project header
cat > "$CONTEXT_TEMP_FILE" <<'EOF'
=== PROJECT: BAZINGA Multi-Agent Orchestration System ===
Repository: https://github.com/mehdic/bazinga

This is a Claude Code multi-agent orchestration system where specialized agents
(PM, Developer, QA, Tech Lead) collaborate on software development tasks.

=== AGENT DEFINITIONS ===
EOF

# Gather all agent files (append directly to temp file)
shopt -s nullglob
agent_files=("$AGENTS_DIR"/*.md)
shopt -u nullglob

if [ ${#agent_files[@]} -eq 0 ]; then
    echo "  ⚠️ Warning: No agent files found in $AGENTS_DIR"
else
    for agent_file in "${agent_files[@]}"; do
        AGENT_NAME=$(basename "$agent_file")
        echo "  → Including agent: $AGENT_NAME"
        check_file_size "$agent_file"
        echo "" >> "$CONTEXT_TEMP_FILE"
        echo "=== FILE: agents/$AGENT_NAME ===" >> "$CONTEXT_TEMP_FILE"
        cat "$agent_file" >> "$CONTEXT_TEMP_FILE"
    done
fi

# Gather additional files
echo "" >> "$CONTEXT_TEMP_FILE"
echo "=== ADDITIONAL CODE/SCRIPTS ===" >> "$CONTEXT_TEMP_FILE"

for file in "${ADDITIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  → Including: $file"
        check_file_size "$file"
        echo "" >> "$CONTEXT_TEMP_FILE"
        echo "=== FILE: $file ===" >> "$CONTEXT_TEMP_FILE"
        cat "$file" >> "$CONTEXT_TEMP_FILE"
    else
        echo "  ⚠️ Warning: File not found: $file"
    fi
done

# -----------------------------------------------------------------------------
# Build Review Prompt (using temp file for large content)
# -----------------------------------------------------------------------------

PROMPT_TEMP_FILE=$(mktemp)

# Write prompt header
cat > "$PROMPT_TEMP_FILE" <<'EOF'
You are a senior software architect and system design expert reviewing a technical plan/analysis.

## Your Task

Review the following ULTRATHINK analysis document and provide critical feedback:

1. **Logical Flaws**: Are there any gaps in reasoning or incorrect assumptions?
2. **Missing Considerations**: What important factors were overlooked?
3. **Better Alternatives**: Are there superior approaches not considered?
4. **Implementation Risks**: What could go wrong during implementation?
5. **Improvement Suggestions**: Specific, actionable improvements to the plan

## Project Context

EOF

# Append context from temp file
cat "$CONTEXT_TEMP_FILE" >> "$PROMPT_TEMP_FILE"

# Append document to review
echo "" >> "$PROMPT_TEMP_FILE"
echo "## Document to Review" >> "$PROMPT_TEMP_FILE"
echo "" >> "$PROMPT_TEMP_FILE"
cat "$PLAN_FILE" >> "$PROMPT_TEMP_FILE"

# Append output format instructions
cat >> "$PROMPT_TEMP_FILE" <<'EOF'

## Output Format

Provide your review in the following structured format:

### Critical Issues (Must Fix)
- [List any critical flaws that must be addressed]

### Missing Considerations
- [List overlooked factors]

### Alternative Approaches
- [Suggest better alternatives if any]

### Implementation Risks
- [List potential risks]

### Specific Improvements
1. [Actionable improvement 1]
2. [Actionable improvement 2]
...

### Overall Assessment
[Brief summary: Is this plan sound? What's the confidence level?]
EOF

# -----------------------------------------------------------------------------
# Call OpenAI API
# -----------------------------------------------------------------------------

echo ""
echo "🤖 Calling OpenAI ($OPENAI_MODEL)..."

# Build payload using temp file to handle large prompts
OPENAI_PAYLOAD_FILE=$(mktemp)
# GPT-5 is a reasoning model - temperature is fixed at 1 (not configurable)
# Needs high max_completion_tokens because reasoning tokens count against the limit
jq -n \
    --arg model "$OPENAI_MODEL" \
    --rawfile content "$PROMPT_TEMP_FILE" \
    '{
        model: $model,
        messages: [
            {role: "user", content: $content}
        ],
        max_completion_tokens: 49152
    }' > "$OPENAI_PAYLOAD_FILE"

# Call API with retry logic (use @file to avoid cmdline size limits)
OPENAI_HTTP_CODE=$(retry_curl "$OUTPUT_DIR/openai-raw.json" \
    -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    --data @"$OPENAI_PAYLOAD_FILE")
CURL_EXIT_CODE=$?
rm -f "$OPENAI_PAYLOAD_FILE"

if [ $CURL_EXIT_CODE -ne 0 ]; then
    echo "  ⚠️ OpenAI API failed after retries (curl exit code $CURL_EXIT_CODE)"
    OPENAI_REVIEW="[OpenAI review failed - network error after retries]"
elif [ "$OPENAI_HTTP_CODE" -ge 400 ]; then
    echo "  ⚠️ OpenAI API HTTP error (status $OPENAI_HTTP_CODE):"
    jq -r '.error.message // "Unknown error"' "$OUTPUT_DIR/openai-raw.json" 2>/dev/null || cat "$OUTPUT_DIR/openai-raw.json"
    OPENAI_REVIEW="[OpenAI review failed - HTTP $OPENAI_HTTP_CODE]"
else
    OPENAI_REVIEW=$(jq -r '.choices[0].message.content // "ERROR: Failed to parse response"' "$OUTPUT_DIR/openai-raw.json")
    if [[ "$OPENAI_REVIEW" == "ERROR:"* ]]; then
        echo "  ⚠️ OpenAI API response parsing error"
        OPENAI_REVIEW="[OpenAI review failed - invalid response]"
    else
        echo "  ✅ OpenAI review received"
    fi
fi
rm -f "$OUTPUT_DIR/openai-raw.json"

# Save OpenAI response
OPENAI_OUTPUT="$OUTPUT_DIR/openai-review.md"
cat > "$OPENAI_OUTPUT" <<EOF
# OpenAI Review ($OPENAI_MODEL)

**Plan reviewed:** $PLAN_FILE
**Date:** $(iso_date)

---

$OPENAI_REVIEW
EOF
echo "  → Saved to: $OPENAI_OUTPUT"

# -----------------------------------------------------------------------------
# Call Gemini API (using X-API-Key header for security)
# -----------------------------------------------------------------------------

if [ "$ENABLE_GEMINI" = "true" ]; then
    echo ""
    echo "🤖 Calling Gemini ($GEMINI_MODEL)..."

    # Build payload using temp file to handle large prompts
    GEMINI_PAYLOAD_FILE=$(mktemp)
    jq -n \
        --rawfile content "$PROMPT_TEMP_FILE" \
        '{
            contents: [
                {parts: [{text: $content}]}
            ],
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 4096
            }
        }' > "$GEMINI_PAYLOAD_FILE"

    # Call API with retry logic (X-API-Key header for security)
    GEMINI_HTTP_CODE=$(retry_curl "$OUTPUT_DIR/gemini-raw.json" \
        -X POST "https://generativelanguage.googleapis.com/v1beta/models/$GEMINI_MODEL:generateContent" \
        -H "Content-Type: application/json" \
        -H "x-goog-api-key: $GEMINI_API_KEY" \
        --data @"$GEMINI_PAYLOAD_FILE")
    CURL_EXIT_CODE=$?
    rm -f "$GEMINI_PAYLOAD_FILE"

    if [ $CURL_EXIT_CODE -ne 0 ]; then
        echo "  ⚠️ Gemini API failed after retries (curl exit code $CURL_EXIT_CODE)"
        GEMINI_REVIEW="[Gemini review failed - network error after retries]"
    elif [ "$GEMINI_HTTP_CODE" -ge 400 ]; then
        echo "  ⚠️ Gemini API HTTP error (status $GEMINI_HTTP_CODE):"
        jq -r '.error.message // "Unknown error"' "$OUTPUT_DIR/gemini-raw.json" 2>/dev/null || cat "$OUTPUT_DIR/gemini-raw.json"
        GEMINI_REVIEW="[Gemini review failed - HTTP $GEMINI_HTTP_CODE]"
    else
        GEMINI_REVIEW=$(jq -r '.candidates[0].content.parts[0].text // "ERROR: Failed to parse response"' "$OUTPUT_DIR/gemini-raw.json")
        if [[ "$GEMINI_REVIEW" == "ERROR:"* ]]; then
            echo "  ⚠️ Gemini API response parsing error"
            GEMINI_REVIEW="[Gemini review failed - invalid response]"
        else
            echo "  ✅ Gemini review received"
        fi
    fi
    rm -f "$OUTPUT_DIR/gemini-raw.json"

    # Save Gemini response
    GEMINI_OUTPUT="$OUTPUT_DIR/gemini-review.md"
    cat > "$GEMINI_OUTPUT" <<EOF
# Gemini Review ($GEMINI_MODEL)

**Plan reviewed:** $PLAN_FILE
**Date:** $(iso_date)

---

$GEMINI_REVIEW
EOF
    echo "  → Saved to: $GEMINI_OUTPUT"
else
    echo ""
    echo "⏭️  Skipping Gemini review (ENABLE_GEMINI=false)"
    GEMINI_REVIEW="[Gemini review skipped - ENABLE_GEMINI=false]"
    GEMINI_OUTPUT="$OUTPUT_DIR/gemini-review.md"
    cat > "$GEMINI_OUTPUT" <<EOF
# Gemini Review (Skipped)

**Plan reviewed:** $PLAN_FILE
**Date:** $(iso_date)

---

Gemini review was skipped because ENABLE_GEMINI=false.
This is expected in Claude Code Web where Gemini API is blocked.
EOF
    echo "  → Saved to: $GEMINI_OUTPUT"
fi

# -----------------------------------------------------------------------------
# Generate Combined Summary
# -----------------------------------------------------------------------------

echo ""
echo "📋 Generating combined summary..."

COMBINED_OUTPUT="$OUTPUT_DIR/combined-review.md"
cat > "$COMBINED_OUTPUT" <<EOF
# Multi-LLM Review Summary

**Plan reviewed:** $PLAN_FILE
**Date:** $(iso_date)
**Reviewers:** OpenAI $OPENAI_MODEL, Google $GEMINI_MODEL

---

## OpenAI Review

$OPENAI_REVIEW

---

## Gemini Review

$GEMINI_REVIEW

---

## Integration Notes

The Claude agent should now:
1. Read both reviews above
2. Identify consensus points (both agree)
3. Evaluate conflicting opinions
4. Integrate valid feedback into the plan
5. Document what was incorporated and why
EOF

echo "  → Combined review saved to: $COMBINED_OUTPUT"

# -----------------------------------------------------------------------------
# Output for Claude
# -----------------------------------------------------------------------------

echo ""
echo "=========================================="
echo "✅ Multi-LLM Review Complete"
echo "=========================================="
echo ""
echo "Review files:"
echo "  - $OPENAI_OUTPUT"
echo "  - $GEMINI_OUTPUT"
echo "  - $COMBINED_OUTPUT"
echo ""
echo "Next step: Read $COMBINED_OUTPUT and integrate feedback into your plan."
echo ""

# Output the combined review to stdout for Claude to capture
echo "--- BEGIN COMBINED REVIEW ---"
cat "$COMBINED_OUTPUT"
echo "--- END COMBINED REVIEW ---"
