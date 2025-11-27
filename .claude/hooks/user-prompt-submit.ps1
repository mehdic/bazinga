#!/usr/bin/env pwsh
# User Prompt Submit Hook (PowerShell)
# Hook that reminds Claude to document planning/brainstorming sessions
# Triggers when user's message contains planning/brainstorming keywords

$ErrorActionPreference = "SilentlyContinue"

# Get the user's message from STDIN (Trim removes trailing newline from Out-String)
$USER_MESSAGE = ($input | Out-String).Trim()

# Keywords that indicate planning/brainstorming/decision-making sessions
$PLANNING_KEYWORDS = @(
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
$MATCHED = $false
foreach ($keyword in $PLANNING_KEYWORDS) {
    if ($USER_MESSAGE -imatch $keyword) {
        $MATCHED = $true
        break
    }
}

# If planning/brainstorming detected, remind to document
if ($MATCHED) {
    Write-Host ""
    Write-Host "📝 **DOCUMENTATION REMINDER**: This appears to be a planning/brainstorming session."
    Write-Host ""
    Write-Host "After completing this discussion, consider documenting it in ``research/`` folder:"
    Write-Host "- Create file: ``research/[topic]-[decision/design/analysis].md``"
    Write-Host "- Include: Context, options considered, decision made, rationale"
    Write-Host "- Use for: Future reference, avoiding repeated discussions, knowledge transfer"
    Write-Host ""
}

# Always pass through the original message
Write-Output $USER_MESSAGE
