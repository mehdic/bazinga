#!/bin/bash
set -euo pipefail

# Hook that reminds Claude to document planning/brainstorming sessions
# Triggers when user's message contains planning/brainstorming keywords

# Get the user's message from STDIN
USER_MESSAGE=$(cat)

# Keywords that indicate planning/brainstorming/decision-making sessions
PLANNING_KEYWORDS=(
  "ultrathink"
  "brainstorm"
  "analyze.*strateg"
  "suggest.*plan"
  "should we"
  "what.*approach"
  "design.*decision"
  "architect"
  "options.*implement"
  "recommend.*way"
  "best.*strategy"
  "alternatives"
  "trade-off"
  "pros.*cons"
  "evaluate.*approach"
)

# Check if message contains any planning keywords (case-insensitive)
MATCHED=false
for keyword in "${PLANNING_KEYWORDS[@]}"; do
  if echo "$USER_MESSAGE" | grep -qiE "$keyword"; then
    MATCHED=true
    break
  fi
done

# If planning/brainstorming detected, remind to document
if [ "$MATCHED" = true ]; then
  echo ""
  echo "📝 **DOCUMENTATION REMINDER**: This appears to be a planning/brainstorming session."
  echo ""
  echo "After completing this discussion, consider documenting it in \`research/\` folder:"
  echo "- Create file: \`research/[topic]-[decision/design/analysis].md\`"
  echo "- Include: Context, options considered, decision made, rationale"
  echo "- Use for: Future reference, avoiding repeated discussions, knowledge transfer"
  echo ""
fi

# Always pass through the original message
echo "$USER_MESSAGE"
