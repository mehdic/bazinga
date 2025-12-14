# BAZINGA-DB Integration Guide: Validated Agent Response Logging

## Overview

The bazinga-db system now includes **automatic validation and verification** for all agent response logging. This ensures that no agent responses are lost due to logging failures.

## What's New

### 1. Automatic Validation (✅ IMPLEMENTED)

Every `log-interaction` operation now:
- ✅ Validates input parameters (session_id, agent_type, content)
- ✅ Verifies the database write succeeded
- ✅ Returns a verification object with log_id, timestamp, and content_length
- ✅ Raises exceptions on failure (non-zero exit code)

### 2. Automated Logger (✅ IMPLEMENTED)

New `auto_logger.py` script provides:
- ✅ Double verification (insert + query back)
- ✅ Statistics tracking (success/failure counts)
- ✅ JSON response format
- ✅ Guaranteed logging or error

## How to Use

### Method 1: Direct Database Call (with validation)

```bash
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db /home/user/bazinga/bazinga/bazinga.db \
  log-interaction \
  "$SESSION_ID" \
  "$AGENT_TYPE" \
  "$AGENT_RESPONSE" \
  $ITERATION \
  "$AGENT_ID"
```

**Returns:**
```json
{
  "success": true,
  "log_id": 42,
  "session_id": "bazinga_20250113_143530",
  "agent_type": "developer",
  "content_length": 2847,
  "timestamp": "2025-01-13 14:35:42",
  "iteration": 5,
  "agent_id": "developer_1"
}
```

### Method 2: Automated Logger (RECOMMENDED)

```bash
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/auto_logger.py \
  /home/user/bazinga/bazinga/bazinga.db \
  "$SESSION_ID" \
  "$AGENT_TYPE" \
  "$AGENT_RESPONSE" \
  $ITERATION \
  "$AGENT_ID"
```

**Returns:**
```json
{
  "status": "success",
  "verified": true,
  "details": {
    "success": true,
    "log_id": 42,
    "session_id": "bazinga_20250113_143530",
    "agent_type": "developer",
    "content_length": 2847,
    "timestamp": "2025-01-13 14:35:42",
    "iteration": 5,
    "agent_id": "developer_1"
  },
  "stats": {
    "logs_saved": 15,
    "logs_failed": 0
  }
}
```

## Integration with Orchestrator

### Current Flow (Manual Invocation)

The orchestrator currently invokes bazinga-db skill manually after each agent:

```
1. Spawn agent (Task tool)
2. Receive agent response
3. Invoke bazinga-db skill to log response
4. Continue workflow
```

**Problem:** If step 3 is forgotten or fails silently, the response is lost.

### Recommended Flow (Automated with Validation)

**Option A: Orchestrator uses auto_logger.py directly**

After each Task tool completion:
```bash
# Capture agent response
AGENT_RESPONSE="$(cat agent_output.txt)"

# Log with automatic validation
RESULT=$(python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/auto_logger.py \
  /home/user/bazinga/bazinga/bazinga.db \
  "$SESSION_ID" \
  "developer" \
  "$AGENT_RESPONSE" \
  5 \
  "developer_1")

# Check result
if [ $? -eq 0 ]; then
  echo "✅ Agent response logged and verified"
else
  echo "❌ CRITICAL: Failed to log agent response"
  exit 1
fi
```

**Option B: Bazinga-DB skill handles validation automatically**

When the orchestrator invokes the bazinga-db skill:
```
Orchestrator: "bazinga-db, please log this developer interaction: ..."
↓
Bazinga-DB skill:
  1. Parses request
  2. Calls auto_logger.py (with validation)
  3. Returns verification to orchestrator
  4. Orchestrator checks verification before proceeding
```

## Validation Rules

### Input Validation
- `session_id`: Must be non-empty string
- `agent_type`: Common values: `pm`, `developer`, `qa_expert`, `tech_lead`, `orchestrator`, `investigator`, `senior_software_engineer`, `requirements_engineer` (extensible - any string accepted)
- `content`: Must be non-empty string (the agent response)
- `iteration`: Optional integer
- `agent_id`: Optional string

### Write Verification
1. Insert returns `log_id`
2. Immediate SELECT query verifies row exists
3. If verification fails, raises `RuntimeError`

### Error Handling
- Invalid input → `ValueError` with clear message
- Database error → `RuntimeError` with details
- Exit code: 0 = success, 1 = failure

## Testing

### Test Validation Works:
```bash
# Valid input (should succeed)
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db /home/user/bazinga/bazinga/bazinga.db \
  log-interaction \
  "test_session" \
  "developer" \
  "Test content" \
  1 \
  "dev_1"

# Invalid agent_type (should fail)
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db /home/user/bazinga/bazinga/bazinga.db \
  log-interaction \
  "test_session" \
  "invalid_type" \
  "Test content" \
  1 \
  "dev_1"
# Expected: Error: Invalid agent_type: invalid_type

# Empty session_id (should fail)
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db /home/user/bazinga/bazinga/bazinga.db \
  log-interaction \
  "" \
  "developer" \
  "Test content" \
  1 \
  "dev_1"
# Expected: Error: session_id cannot be empty
```

### Verify Data Was Saved:
```bash
# Use the CLI to verify data - NEVER use inline SQL
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet stream-logs "test_session" 10
```

## Migration Path

### For Existing Orchestrations

If you want to ensure all past orchestrations are validated:

1. **Check current state:**
   ```bash
   # Use the CLI - NEVER inline SQL
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 5
   ```

2. **No logs found?** → Previous orchestrations didn't save responses properly

3. **Logs found?** → Those logs don't have verification data, but they're valid

### Going Forward

All new orchestrations using the updated bazinga-db will automatically:
- Validate all inputs
- Verify all writes
- Return verification objects
- Track logging statistics

## Benefits

| Feature | Before | After |
|---------|--------|-------|
| **Input validation** | None | ✅ All inputs validated |
| **Write verification** | None | ✅ Read-back verification |
| **Error detection** | Silent failure | ✅ Exception with details |
| **Response format** | Simple message | ✅ JSON with verification |
| **Statistics** | None | ✅ Success/failure tracking |
| **Double-check** | None | ✅ Auto-logger queries back |

## Troubleshooting

### "session_id cannot be empty"
- Ensure SESSION_ID is set before calling log-interaction
- Check that the session was created first

### "agent_type cannot be empty"
- Ensure agent_type is provided and not an empty string
- Common agent types: pm, developer, qa_expert, tech_lead, orchestrator, investigator
- Note: System is extensible - any agent type is accepted (no hardcoded validation)
- Tip: Use snake_case for agent_type (e.g., 'tech_lead', 'qa_expert', 'senior_software_engineer')

### "Failed to verify log insertion"
- Database may be corrupted
- Check database permissions
- Verify WAL mode is enabled

### Exit code 1
- Check stderr for error message
- Validation failed or write failed
- Do not proceed until fixed

## Summary

✅ **Validation**: All inputs validated before insert
✅ **Verification**: All writes verified immediately after insert
✅ **Automation**: auto_logger.py provides guaranteed logging
✅ **Statistics**: Track success/failure rates
✅ **Error handling**: Clear error messages, non-zero exit codes

**Next Steps:**
1. Update orchestrator to use auto_logger.py
2. Add verification checks after each agent spawn
3. Track logging statistics per session
4. Alert on logging failures
