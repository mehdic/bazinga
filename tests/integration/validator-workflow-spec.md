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
# Query sessions and filter by specific session_id
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 100 | \
  python3 -c "
import sys, json
sessions = json.load(sys.stdin)
target = '[session_id]'  # Replace with actual session ID
for s in sessions:
    if s.get('session_id') == target:
        print(json.dumps(s, indent=2))
        break
else:
    print('Session not found')
"
```

**Expected:**
- `status: "completed"` (not "active")
- `end_time` is set
- `session_id` matches the target session

**IMPORTANT:** Do NOT use `list-sessions 1` - it returns the most recent session which may not be your target session in multi-session environments.

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

**Location:** `tests/integration/verify_validator_workflow.sh`

**Usage:**
```bash
./tests/integration/verify_validator_workflow.sh <session_id>
```

**What it checks:**
1. **Validator verdict** - Event exists with valid ACCEPT/REJECT value (not unknown)
2. **Validator gate check** - Event exists AND `passed=true` (not just exists)
3. **Session status** - Queries by specific session_id (not just first session)
4. **PM BAZINGA message** - Logged for validator access

**Key features:**
- Filters sessions by SESSION_ID (not `list-sessions 1`)
- Validates verdict is ACCEPT or REJECT (fails on unknown/parse_error)
- Checks gate `passed` field is true (not just event existence)
- Returns proper exit codes for CI integration

**See the actual script for implementation details.**

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
