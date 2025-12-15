#!/bin/bash
# Verify validator workflow integration
# Usage: ./verify_validator_workflow.sh <session_id>

set -euo pipefail
IFS=$'\n\t'

SESSION_ID="${1:-}"

if [ -z "$SESSION_ID" ]; then
    echo "Usage: $0 <session_id>"
    echo ""
    echo "Verifies that the bazinga-validator skill was correctly invoked"
    echo "and that the shutdown protocol's validator gate was checked."
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "        BAZINGA Validator Workflow Verification"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Session: $SESSION_ID"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Check 1: Validator verdict exists
echo "━━━ Check 1: Validator Verdict ━━━"
VERDICT=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "validator_verdict" 1 2>/dev/null || echo "")
if [ -z "$VERDICT" ] || [ "$VERDICT" = "[]" ] || [ "$VERDICT" = "null" ]; then
    echo "❌ FAIL: No validator_verdict event found"
    echo "   → Validator was NOT invoked before shutdown"
    echo "   → This is a critical workflow violation"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    VERDICT_STATUS="missing"
else
    # Extract verdict value
    VERDICT_VALUE=$(echo "$VERDICT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('event_payload',{}).get('verdict','unknown') if isinstance(d,list) and len(d)>0 else 'unknown')" 2>/dev/null || echo "parse_error")

    # FIX #1: Handle unknown/parse_error verdicts explicitly
    if [ "$VERDICT_VALUE" = "unknown" ] || [ "$VERDICT_VALUE" = "parse_error" ]; then
        echo "❌ FAIL: Validator verdict event exists but verdict value is '$VERDICT_VALUE'"
        echo "   → Event payload may be malformed or missing 'verdict' field"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        VERDICT_STATUS="unknown"
    elif [ "$VERDICT_VALUE" = "ACCEPT" ] || [ "$VERDICT_VALUE" = "REJECT" ]; then
        echo "✅ PASS: Validator verdict found"
        echo "   Verdict: $VERDICT_VALUE"
        # Extract additional diagnostics (reason, scope_check) for troubleshooting
        VERDICT_REASON=$(echo "$VERDICT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('event_payload',{}).get('reason','N/A')[:100] if isinstance(d,list) and len(d)>0 else 'N/A')" 2>/dev/null || echo "N/A")
        VERDICT_SCOPE=$(echo "$VERDICT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('event_payload',{}).get('scope_check','N/A') if isinstance(d,list) and len(d)>0 else 'N/A')" 2>/dev/null || echo "N/A")
        echo "   Reason: $VERDICT_REASON"
        echo "   Scope check: $VERDICT_SCOPE"
        PASS_COUNT=$((PASS_COUNT + 1))
        VERDICT_STATUS="$VERDICT_VALUE"
    else
        echo "❌ FAIL: Unexpected verdict value: '$VERDICT_VALUE'"
        echo "   → Expected 'ACCEPT' or 'REJECT'"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        VERDICT_STATUS="invalid"
    fi
fi
echo ""

# Check 2: Validator gate check exists AND passed=true
echo "━━━ Check 2: Validator Gate Check ━━━"
GATE=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "validator_gate_check" 1 2>/dev/null || echo "")
GATE_MISSING="false"
if [ -z "$GATE" ] || [ "$GATE" = "[]" ] || [ "$GATE" = "null" ]; then
    echo "⚠️ WARNING: No validator_gate_check event found"
    echo "   → Shutdown protocol may not have executed Step 0"
    echo "   → Will verify against session status"
    WARN_COUNT=$((WARN_COUNT + 1))
    GATE_MISSING="true"
else
    # FIX #3: Check if passed=true, not just if event exists
    GATE_PASSED=$(echo "$GATE" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d[0].get('event_payload',{}).get('passed',False) if isinstance(d,list) and len(d)>0 else False; print('true' if p is True or p == 'true' else 'false')" 2>/dev/null || echo "false")

    if [ "$GATE_PASSED" = "true" ]; then
        echo "✅ PASS: Validator gate check logged with passed=true"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "❌ FAIL: Validator gate check exists but passed=$GATE_PASSED"
        echo "   → Gate check was logged but did not pass"
        echo "   → This indicates a validation failure that was not handled"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi
echo ""

# Check 3: Session status (query specific session by ID)
echo "━━━ Check 3: Session Status ━━━"

# Use get-session for direct lookup (no pagination issues)
SESSION_INFO=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-session "$SESSION_ID" 2>/dev/null || echo "null")
SESSION_STATUS=$(echo "$SESSION_INFO" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data is None or data == 'null':
        print('not_found')
    elif isinstance(data, dict):
        print(data.get('status', 'unknown'))
    else:
        print('parse_error')
except:
    print('parse_error')
" 2>/dev/null || echo "parse_error")

if [ "$SESSION_STATUS" = "not_found" ]; then
    echo "❌ FAIL: Session '$SESSION_ID' not found in database"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif [ "$SESSION_STATUS" = "parse_error" ]; then
    echo "❌ FAIL: Could not parse session data from database"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo "   Session status: $SESSION_STATUS"
fi

# Validate verdict vs session status consistency
if [ "$VERDICT_STATUS" = "ACCEPT" ]; then
    if [ "$SESSION_STATUS" = "completed" ]; then
        echo "✅ PASS: ACCEPT verdict → session completed (correct)"
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [ "$SESSION_STATUS" = "not_found" ] || [ "$SESSION_STATUS" = "parse_error" ]; then
        # Already counted as fail above, don't double-count
        :
    else
        echo "⚠️ WARNING: ACCEPT verdict but session is '$SESSION_STATUS'"
        echo "   → Shutdown may not have completed"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
elif [ "$VERDICT_STATUS" = "REJECT" ]; then
    if [ "$SESSION_STATUS" = "active" ]; then
        echo "✅ PASS: REJECT verdict → session still active (correct)"
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [ "$SESSION_STATUS" = "completed" ]; then
        echo "❌ FAIL: REJECT verdict but session is 'completed'"
        echo "   → Runtime guard was BYPASSED"
        echo "   → This is a critical security issue"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    elif [ "$SESSION_STATUS" = "not_found" ] || [ "$SESSION_STATUS" = "parse_error" ]; then
        # Already counted as fail above, don't double-count
        :
    else
        echo "⚠️ WARNING: REJECT verdict, session status is '$SESSION_STATUS'"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
elif [ "$VERDICT_STATUS" = "missing" ]; then
    if [ "$SESSION_STATUS" = "completed" ]; then
        echo "❌ FAIL: No validator verdict but session is 'completed'"
        echo "   → Validator was SKIPPED entirely"
        echo "   → This is a critical workflow violation"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    elif [ "$SESSION_STATUS" = "not_found" ] || [ "$SESSION_STATUS" = "parse_error" ]; then
        # Already counted as fail above, don't double-count
        :
    else
        echo "   Session not completed (validator may still be pending)"
    fi
# FIX #1 continued: Handle unknown/invalid verdict status
elif [ "$VERDICT_STATUS" = "unknown" ] || [ "$VERDICT_STATUS" = "invalid" ]; then
    echo "   → Cannot validate session status consistency (verdict was invalid)"
    # Already counted as fail in Check 1, don't double-count
fi

# Additional check: Missing gate + completed session = FAIL
if [ "$GATE_MISSING" = "true" ] && [ "$SESSION_STATUS" = "completed" ]; then
    echo ""
    echo "❌ FAIL: Session completed but validator_gate_check was missing"
    echo "   → The shutdown protocol's Step 0 gate was bypassed"
    echo "   → This indicates a critical security issue"
    # Convert the warning to a failure
    WARN_COUNT=$((WARN_COUNT - 1))
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Check 4: PM BAZINGA message logged (for validator access)
echo "━━━ Check 4: PM BAZINGA Message Logged ━━━"
PM_BAZINGA=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "pm_bazinga" 1 2>/dev/null || echo "")
if [ -z "$PM_BAZINGA" ] || [ "$PM_BAZINGA" = "[]" ] || [ "$PM_BAZINGA" = "null" ]; then
    echo "⚠️ WARNING: No pm_bazinga event found"
    echo "   → Orchestrator may not have logged PM's BAZINGA message"
    echo "   → Validator may not have had access to completion claims"
    WARN_COUNT=$((WARN_COUNT + 1))
else
    echo "✅ PASS: PM BAZINGA message logged"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "                      SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  ✅ Passed:   $PASS_COUNT"
echo "  ⚠️ Warnings: $WARN_COUNT"
echo "  ❌ Failed:   $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo "❌ OVERALL: FAIL"
    echo ""
    echo "The validator workflow has critical issues that need fixing."
    echo "Review the orchestrator prompt and shutdown protocol."
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo "⚠️ OVERALL: PASS WITH WARNINGS"
    echo ""
    echo "The validator workflow is working but has minor issues."
    exit 0
else
    echo "✅ OVERALL: PASS"
    echo ""
    echo "The validator workflow is functioning correctly."
    exit 0
fi
