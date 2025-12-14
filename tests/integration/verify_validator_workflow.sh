#!/bin/bash
# Verify validator workflow integration
# Usage: ./verify_validator_workflow.sh <session_id>

set -e

SESSION_ID=$1

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
    echo "✅ PASS: Validator verdict found"
    # Extract verdict value
    VERDICT_VALUE=$(echo "$VERDICT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('event_payload',{}).get('verdict','unknown') if isinstance(d,list) and len(d)>0 else 'unknown')" 2>/dev/null || echo "unknown")
    echo "   Verdict: $VERDICT_VALUE"
    PASS_COUNT=$((PASS_COUNT + 1))
    VERDICT_STATUS="$VERDICT_VALUE"
fi
echo ""

# Check 2: Validator gate check exists
echo "━━━ Check 2: Validator Gate Check ━━━"
GATE=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "validator_gate_check" 1 2>/dev/null || echo "")
if [ -z "$GATE" ] || [ "$GATE" = "[]" ] || [ "$GATE" = "null" ]; then
    echo "⚠️ WARNING: No validator_gate_check event found"
    echo "   → Shutdown protocol may not have executed Step 0"
    echo "   → If session is completed, the gate may have been bypassed"
    WARN_COUNT=$((WARN_COUNT + 1))
else
    echo "✅ PASS: Validator gate check logged"
    GATE_PASSED=$(echo "$GATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('event_payload',{}).get('passed',False) if isinstance(d,list) and len(d)>0 else False)" 2>/dev/null || echo "false")
    echo "   Gate passed: $GATE_PASSED"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# Check 3: Session status
echo "━━━ Check 3: Session Status ━━━"
SESSION_INFO=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1 2>/dev/null || echo "[]")
SESSION_STATUS=$(echo "$SESSION_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('status','unknown') if isinstance(d,list) and len(d)>0 else 'unknown')" 2>/dev/null || echo "unknown")
echo "   Session status: $SESSION_STATUS"

# Validate verdict vs session status
if [ "$VERDICT_STATUS" = "ACCEPT" ]; then
    if [ "$SESSION_STATUS" = "completed" ]; then
        echo "✅ PASS: ACCEPT verdict → session completed (correct)"
        PASS_COUNT=$((PASS_COUNT + 1))
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
    else
        echo "   Session not completed (validator may still be pending)"
    fi
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
