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
#   GEMINI_API_KEY - Google Gemini API key
#
# Example:
#   ./dev-scripts/llm-reviews.sh research/my-plan.md scripts/foo.sh src/bar.py
#
# Note: This script is for BAZINGA development only, not copied to clients.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

OPENAI_MODEL="gpt-5"
GEMINI_MODEL="gemini-3-pro-preview"
OUTPUT_DIR="$REPO_ROOT/tmp/ultrathink-reviews"
AGENTS_DIR="$REPO_ROOT/agents"

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY environment variable not set"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY environment variable not set"
    exit 1
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

# Create output directory
mkdir -p "$OUTPUT_DIR"

# -----------------------------------------------------------------------------
# Gather Context
# -----------------------------------------------------------------------------

echo "🔍 Gathering context for review..."

# Read the plan
PLAN_CONTENT=$(cat "$PLAN_FILE")

# Gather all agent files
AGENT_CONTEXT=""
for agent_file in "$AGENTS_DIR"/*.md; do
    if [ -f "$agent_file" ]; then
        AGENT_NAME=$(basename "$agent_file")
        echo "  → Including agent: $AGENT_NAME"
        AGENT_CONTEXT+="
=== FILE: agents/$AGENT_NAME ===
$(cat "$agent_file")
"
    fi
done

# Gather additional files
ADDITIONAL_CONTEXT=""
for file in "${ADDITIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  → Including: $file"
        ADDITIONAL_CONTEXT+="
=== FILE: $file ===
$(cat "$file")
"
    else
        echo "  ⚠️ Warning: File not found: $file"
    fi
done

# Build the full context
FULL_CONTEXT="
=== PROJECT: BAZINGA Multi-Agent Orchestration System ===
Repository: https://github.com/mehdic/bazinga

This is a Claude Code multi-agent orchestration system where specialized agents
(PM, Developer, QA, Tech Lead) collaborate on software development tasks.

=== AGENT DEFINITIONS ===
$AGENT_CONTEXT

=== ADDITIONAL CODE/SCRIPTS ===
$ADDITIONAL_CONTEXT
"

# -----------------------------------------------------------------------------
# Build Review Prompt
# -----------------------------------------------------------------------------

REVIEW_PROMPT="You are a senior software architect and system design expert reviewing a technical plan/analysis.

## Your Task

Review the following ULTRATHINK analysis document and provide critical feedback:

1. **Logical Flaws**: Are there any gaps in reasoning or incorrect assumptions?
2. **Missing Considerations**: What important factors were overlooked?
3. **Better Alternatives**: Are there superior approaches not considered?
4. **Implementation Risks**: What could go wrong during implementation?
5. **Improvement Suggestions**: Specific, actionable improvements to the plan

## Project Context

$FULL_CONTEXT

## Document to Review

$PLAN_CONTENT

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
"

# -----------------------------------------------------------------------------
# Call OpenAI API
# -----------------------------------------------------------------------------

echo ""
echo "🤖 Calling OpenAI ($OPENAI_MODEL)..."

OPENAI_PAYLOAD=$(jq -n \
    --arg model "$OPENAI_MODEL" \
    --arg content "$REVIEW_PROMPT" \
    '{
        model: $model,
        messages: [
            {role: "user", content: $content}
        ],
        temperature: 0.7,
        max_tokens: 4096
    }')

OPENAI_RESPONSE=$(curl -s -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$OPENAI_PAYLOAD")

OPENAI_REVIEW=$(echo "$OPENAI_RESPONSE" | jq -r '.choices[0].message.content // "ERROR: Failed to get response"')

if [[ "$OPENAI_REVIEW" == "ERROR:"* ]] || [[ "$OPENAI_REVIEW" == "null" ]]; then
    echo "  ⚠️ OpenAI API error:"
    echo "$OPENAI_RESPONSE" | jq -r '.error.message // "Unknown error"'
    OPENAI_REVIEW="[OpenAI review failed - see logs]"
else
    echo "  ✅ OpenAI review received"
fi

# Save OpenAI response
OPENAI_OUTPUT="$OUTPUT_DIR/openai-review.md"
cat > "$OPENAI_OUTPUT" <<EOF
# OpenAI Review ($OPENAI_MODEL)

**Plan reviewed:** $PLAN_FILE
**Date:** $(date -Iseconds)

---

$OPENAI_REVIEW
EOF
echo "  → Saved to: $OPENAI_OUTPUT"

# -----------------------------------------------------------------------------
# Call Gemini API
# -----------------------------------------------------------------------------

echo ""
echo "🤖 Calling Gemini ($GEMINI_MODEL)..."

GEMINI_PAYLOAD=$(jq -n \
    --arg content "$REVIEW_PROMPT" \
    '{
        contents: [
            {parts: [{text: $content}]}
        ],
        generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 4096
        }
    }')

GEMINI_RESPONSE=$(curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/$GEMINI_MODEL:generateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$GEMINI_PAYLOAD")

GEMINI_REVIEW=$(echo "$GEMINI_RESPONSE" | jq -r '.candidates[0].content.parts[0].text // "ERROR: Failed to get response"')

if [[ "$GEMINI_REVIEW" == "ERROR:"* ]] || [[ "$GEMINI_REVIEW" == "null" ]]; then
    echo "  ⚠️ Gemini API error:"
    echo "$GEMINI_RESPONSE" | jq -r '.error.message // "Unknown error"'
    GEMINI_REVIEW="[Gemini review failed - see logs]"
else
    echo "  ✅ Gemini review received"
fi

# Save Gemini response
GEMINI_OUTPUT="$OUTPUT_DIR/gemini-review.md"
cat > "$GEMINI_OUTPUT" <<EOF
# Gemini Review ($GEMINI_MODEL)

**Plan reviewed:** $PLAN_FILE
**Date:** $(date -Iseconds)

---

$GEMINI_REVIEW
EOF
echo "  → Saved to: $GEMINI_OUTPUT"

# -----------------------------------------------------------------------------
# Generate Combined Summary
# -----------------------------------------------------------------------------

echo ""
echo "📋 Generating combined summary..."

COMBINED_OUTPUT="$OUTPUT_DIR/combined-review.md"
cat > "$COMBINED_OUTPUT" <<EOF
# Multi-LLM Review Summary

**Plan reviewed:** $PLAN_FILE
**Date:** $(date -Iseconds)
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
