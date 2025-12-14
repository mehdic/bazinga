# BAZINGA Validator Workflow Test Specification

**Purpose:** Verify that the bazinga-validator skill is correctly integrated into the orchestration workflow and that completion cannot proceed without validator approval.

---

## Test Objective

Verify the following critical workflow behaviors:

1. **Validator is invoked** when PM sends BAZINGA
2. **ACCEPT verdict** proceeds to shutdown protocol
3. **REJECT verdict** returns to PM with failure details
4. **Validator gate** in shutdown protocol blocks completion without validator verdict
5. **Validator verdict** is logged to database as `validator_verdict` event

---

## Prerequisites

- Clean database (no prior sessions)
- No existing files in `tmp/validator-test/`

---

## Test Scenario: Complete Workflow with Validator

### Setup

```bash
# Clean up
rm -rf tmp/validator-test bazinga/bazinga.db bazinga/project_context.json
```

### Task Description

```
Implement a simple greeting function in Python:

1. Create a file `greeter.py` with a function `greet(name)` that returns "Hello, {name}!"
2. Create a test file `test_greeter.py` with at least 3 test cases
3. All tests must pass

Success Criteria:
- greeter.py exists with greet() function
- test_greeter.py exists with 3+ tests
- All tests pass (pytest exit code 0)
```

### Expected Orchestration Flow

```
1. Session created
2. PM analyzes requirements → creates task group
3. Developer implements greeter.py and test_greeter.py
4. QA verifies tests pass
5. Tech Lead approves
6. PM sends BAZINGA
7. 🔴 CRITICAL: Orchestrator invokes bazinga-validator
8. Validator runs tests independently
9. Validator returns ACCEPT or REJECT
10. IF ACCEPT: Shutdown protocol executes
11. IF REJECT: PM respawned with failure details
```

---

## Verification Commands

### After PM Sends BAZINGA

**Check 1: Validator was invoked**
```bash
# The validator should have logged its verdict
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events \
  "[session_id]" "validator_verdict" 1
```

**Expected output:**
```json
{
  "event_type": "validator_verdict",
  "event_payload": {
    "verdict": "ACCEPT",
    "reason": "...",
    "scope_check": "pass"
  }
}
```

**If empty:** Validator was NOT invoked - this is a test FAILURE.

---

### Check 2: Validator Gate in Shutdown Protocol

**Verify the shutdown protocol checked for validator verdict:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events \
  "[session_id]" "validator_gate_check" 1
```

**Expected output:**
```json
{
  "event_type": "validator_gate_check",
  "event_payload": {
    "passed": true,
    "verdict": "ACCEPT",
    "timestamp": "..."
  }
}
```

**If empty:** Shutdown protocol did NOT check validator gate - runtime guard failed.

---

### Check 3: Session Completed Successfully

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1
```

**Expected:**
- `status: "completed"` (not "active")
- `end_time` is set

---

## Test Scenario: Validator REJECT Path

### Setup

Create a scenario where validator will REJECT:

```
Task: Create a function that passes specific tests

Success Criteria:
- All 5 tests pass
- Coverage > 90%
```

But the implementation only passes 3/5 tests.

### Expected Flow

```
1. Developer implements incomplete solution
2. QA may pass (if not catching all edge cases)
3. Tech Lead may approve (code looks good)
4. PM sends BAZINGA (incorrectly claiming completion)
5. Orchestrator invokes bazinga-validator
6. Validator runs tests independently
7. Validator finds 2 failing tests
8. Validator returns REJECT
9. PM is respawned with rejection details
10. Development continues until criteria actually met
```

### Verification After REJECT

```bash
# Check validator verdict shows REJECT
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events \
  "[session_id]" "validator_verdict" 1

# Expected: verdict = "REJECT"

# Check PM was respawned after rejection
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-orchestration-logs \
  "[session_id]" 5

# Should show PM spawn AFTER validator rejection
```

---

## Pass/Fail Criteria

### PASS Conditions

| Check | Requirement |
|-------|-------------|
| Validator invoked | `validator_verdict` event exists after PM BAZINGA |
| Validator gate checked | `validator_gate_check` event exists |
| Correct verdict handling | ACCEPT → shutdown, REJECT → PM respawn |
| Session completion | `status = "completed"` only after ACCEPT |

### FAIL Conditions

| Symptom | Root Cause |
|---------|------------|
| No `validator_verdict` event | Validator skill not invoked |
| No `validator_gate_check` event | Shutdown protocol skipped Step 0 |
| Session completed with REJECT | Runtime guard bypassed |
| PM not respawned after REJECT | Orchestrator ignored rejection |

---

## Automated Verification Script

Save as `tests/integration/verify_validator_workflow.sh`:

```bash
#!/bin/bash
# Verify validator workflow integration
# Usage: ./verify_validator_workflow.sh <session_id>

SESSION_ID=$1

if [ -z "$SESSION_ID" ]; then
    echo "Usage: $0 <session_id>"
    exit 1
fi

echo "=== Validator Workflow Verification ==="
echo "Session: $SESSION_ID"
echo ""

# Check 1: Validator verdict exists
echo "Check 1: Validator verdict..."
VERDICT=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "validator_verdict" 1 2>/dev/null)
if [ -z "$VERDICT" ] || [ "$VERDICT" = "[]" ]; then
    echo "❌ FAIL: No validator_verdict event found"
    echo "   Validator was NOT invoked"
    exit 1
else
    echo "✅ PASS: Validator verdict found"
    echo "   $VERDICT"
fi

echo ""

# Check 2: Validator gate check exists
echo "Check 2: Validator gate check..."
GATE=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events "$SESSION_ID" "validator_gate_check" 1 2>/dev/null)
if [ -z "$GATE" ] || [ "$GATE" = "[]" ]; then
    echo "⚠️ WARNING: No validator_gate_check event found"
    echo "   Shutdown protocol may not have executed Step 0"
else
    echo "✅ PASS: Validator gate check found"
    echo "   $GATE"
fi

echo ""

# Check 3: Session status
echo "Check 3: Session status..."
STATUS=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1 2>/dev/null | grep -o '"status": "[^"]*"' | head -1)
echo "   $STATUS"

# Check if verdict was ACCEPT and session is completed
if echo "$VERDICT" | grep -q '"verdict": "ACCEPT"'; then
    if echo "$STATUS" | grep -q '"status": "completed"'; then
        echo "✅ PASS: ACCEPT verdict led to completed session"
    else
        echo "❌ FAIL: ACCEPT verdict but session not completed"
        exit 1
    fi
elif echo "$VERDICT" | grep -q '"verdict": "REJECT"'; then
    if echo "$STATUS" | grep -q '"status": "active"'; then
        echo "✅ PASS: REJECT verdict kept session active"
    else
        echo "⚠️ WARNING: REJECT verdict but session is completed"
        echo "   This may indicate a bypass of the validator gate"
    fi
fi

echo ""
echo "=== Verification Complete ==="
```

---

## Integration with CI

Add to test suite:

```yaml
# .github/workflows/integration-tests.yml
- name: Validator Workflow Test
  run: |
    # Run orchestration with simple task
    # Extract session ID
    # Run verification script
    ./tests/integration/verify_validator_workflow.sh $SESSION_ID
```

---

## Notes

1. **This test is critical** - it verifies the last line of defense against premature completion
2. **Manual testing** - Run a full orchestration and use verification commands
3. **Automated testing** - Use the verification script in CI pipeline
4. **Failure indicates** - Either validator skill not invoked or runtime guard bypassed
