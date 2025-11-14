---
name: bazinga-db
description: Database operations for BAZINGA orchestration system. This skill should be used when agents need to save or retrieve orchestration state, logs, task groups, token usage, or skill outputs. Replaces file-based storage with concurrent-safe SQLite database. Use instead of writing to bazinga/*.json files or docs/orchestration-log.md.
version: 1.0.0
allowed-tools: [Bash, Read]
---

# BAZINGA-DB Skill

You are the bazinga-db skill. When invoked, you handle database operations for the BAZINGA orchestration system, providing concurrent-safe storage for sessions, logs, state, task groups, tokens, and skill outputs.

## When to Invoke This Skill

**Invoke this skill when:**
- Orchestrator needs to log agent interactions or save orchestrator state
- Project Manager needs to save PM state or create/update task groups
- Developer/QA/Tech Lead needs to log completion or update task status
- Any agent needs to save skill outputs (security scan, coverage, lint results)
- Dashboard needs to query orchestration data
- Any agent mentions "save to database", "query database", or "bazinga-db"
- Replacing file writes to `bazinga/*.json` or `docs/orchestration-log.md`

**Do NOT invoke when:**
- Requesting read-only file operations (use Read tool directly)
- No session_id context available
- Working with non-orchestration data

---

## Your Task

When invoked:
1. Parse the request to identify operation and parameters
2. Execute the appropriate database command
3. Return formatted response to calling agent

---

## Environment Setup

**Database paths:**
```bash
DB_SCRIPT="/home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py"
DB_PATH="/home/user/bazinga/bazinga/bazinga.db"
```

**Auto-initialization:**
The database will be automatically initialized on first use (< 2 seconds). The script detects if the database doesn't exist and runs the initialization automatically, creating all tables with proper indexes and WAL mode for concurrency.

No manual initialization needed - just invoke the skill and it handles everything.

---

## Step 1: Parse Request

Extract from the calling agent's request:

**Operation type:**
- "list sessions" / "recent sessions" / "show sessions" → list-sessions
- "create session" / "new session" / "initialize session" → create-session
- "log interaction" / "save log" → log-interaction
- "save PM state" / "save orchestrator state" → save-state
- "get state" / "retrieve state" → get-state
- "create task group" → create-task-group
- "update task group" / "mark complete" → update-task-group
- "get task groups" / "get all task groups" → get-task-groups
- "update session status" → update-session-status
- "log tokens" / "track token usage" → log-tokens
- "save skill output" → save-skill-output
- "dashboard snapshot" / "get dashboard data" → dashboard-snapshot
- "stream logs" / "recent logs" → stream-logs

**Required parameters:**
- session_id (almost always required)
- agent_type (for logs, tokens)
- content (for logs)
- state_type (for state operations: pm, orchestrator, group_status)
- state_data (JSON object)

**Optional parameters:**
- iteration
- agent_id
- group_id
- status (pending, in_progress, completed, failed)
- limit, offset (for queries)

---

## Step 2: Execute Database Command

Use the **Bash** tool to run the appropriate command:

### Session Management

**List recent sessions:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" list-sessions [limit]
```
Returns JSON array of recent sessions (default 10, ordered by created_at DESC).

**Create new session:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" create-session \
  "<session_id>" \
  "<mode>" \
  "<requirements>"
```

**IMPORTANT:** This command will auto-initialize the database if it doesn't exist. No separate initialization needed!

### Common Operations

**Log agent interaction:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" log-interaction \
  "<session_id>" \
  "<agent_type>" \
  "<content>" \
  [iteration] \
  [agent_id]
```

**Save state (PM or orchestrator):**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" save-state \
  "<session_id>" \
  "<state_type>" \
  '<json_data>'
```

**Get latest state:**
```bash
STATE=$(python3 "$DB_SCRIPT" --db "$DB_PATH" get-state \
  "<session_id>" \
  "<state_type>")
```

**Create task group:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" create-task-group \
  "<group_id>" \
  "<session_id>" \
  "<name>" \
  [status] \
  [assigned_to]
```

**Update task group:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" update-task-group \
  "<group_id>" \
  [--status "<status>"] \
  [--assigned_to "<agent_id>"] \
  [--revision_count <N>]
```

**Get task groups:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" get-task-groups \
  "<session_id>" \
  [status]
```
Returns JSON array of task groups for the session. Optional status filter (pending, in_progress, completed, failed).

**Update session status:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" update-session-status \
  "<session_id>" \
  "<status>"
```
Updates session status (active, completed, failed). Auto-sets end_time for completed/failed.

**Dashboard snapshot:**
```bash
SNAPSHOT=$(python3 "$DB_SCRIPT" --db "$DB_PATH" dashboard-snapshot \
  "<session_id>")
```

**Full command reference:** See `scripts/bazinga_db.py --help` for all available operations.

**Note:** All database operations include automatic input validation and write verification. The script will return JSON with verification details including log_id, content_length, and timestamp.

---

## Step 3: Return Response to Calling Agent

**CRITICAL: Return ONLY the raw command output - NO additional formatting or commentary!**

The calling agent (orchestrator, PM, etc.) will parse the data and make decisions automatically. Do NOT add:
- ❌ Explanatory text like "Found 2 sessions"
- ❌ Analysis like "This is the session to resume"
- ❌ Formatted summaries
- ❌ Recommendations or next steps

**For successful operations:**

Simply echo the bash command output directly:
```bash
# The script already outputs JSON or formatted data
# Just return it as-is without additional commentary
[Raw output from bazinga_db.py script]
```

**For failed operations:**

Return ONLY the error output:
```
Error: [exact error message from stderr]
```

**Examples:**

❌ WRONG (too verbose):
```
✓ Recent sessions retrieved

Found 2 active sessions:
- Session 1: bazinga_123 (most recent)
- Session 2: bazinga_456

Recommendation: Resume session bazinga_123
```

✅ CORRECT (minimal):
```json
[
  {
    "session_id": "bazinga_123",
    "start_time": "2025-01-14 10:00:00",
    "status": "active",
    "mode": "simple"
  },
  {
    "session_id": "bazinga_456",
    "start_time": "2025-01-13 15:30:00",
    "status": "active",
    "mode": "parallel"
  }
]
```

**Why minimal output?**
- Orchestrator needs to parse data programmatically
- Verbose text causes orchestrator to pause and wait
- Calling agent will format data for user if needed
- Faster execution (no time spent on formatting)

**For failed operations:**

ALWAYS capture and return the full error output from bash commands:
```
❌ Database operation failed

Command:
python3 /path/to/bazinga_db.py --db /path/to/bazinga.db create-session ...

Error Output:
[Full stderr from the command]

Exit Code: [code]

Possible causes:
- Database file permission denied
- Invalid session_id format
- Missing init_db.py script
- Python dependencies not installed
- Disk space full

The orchestrator MUST see this error to diagnose the issue.
```

**Error detection:**
- Check bash command exit code (non-zero = failure)
- Capture both stdout and stderr
- Include command that failed
- Return detailed error message to calling agent

**For errors:**
Provide actionable guidance:
```
❌ Database not found

I can initialize the database now (takes ~2 seconds).
This creates all tables with proper indexes for concurrency.

Proceed with initialization?
```

---

## Example Invocation

**Scenario 1: Orchestrator Creating New Session**

Input: Orchestrator starting new orchestration, needs to initialize session in database

Request from orchestrator:
```
bazinga-db, please create a new orchestration session:

Session ID: bazinga_20250113_143530
Mode: simple
Requirements: Add user authentication with OAuth2 support
```

Expected output:
```
✓ Database auto-initialized at bazinga/bazinga.db
✓ Session created: bazinga_20250113_143530

Database ready for orchestration. Session is active and ready to receive logs and state.
```

---

**Scenario 2: Orchestrator Logging PM Interaction**

Input: Orchestrator completed PM spawn, needs to log the interaction

Request from orchestrator:
```
bazinga-db, please log this PM interaction:

Session ID: sess_abc123
Agent Type: pm
Content: Task breakdown created: 3 groups (group_a, group_b, group_c). Group A will handle auth, Group B will handle API, Group C will handle UI components.
Iteration: 1
Agent ID: pm_main
```

Expected output:
```
✓ Logged PM interaction for session sess_abc123 (iteration 1)

Database operation successful.
```

---

**Scenario 3: PM Saving State**

Input: PM completed task breakdown, needs to save PM state

Request from PM:
```
bazinga-db, please save the PM state:

Session ID: sess_abc123
State Type: pm
State Data: {
  "iteration": 1,
  "mode": "parallel",
  "task_groups": [
    {"id": "group_a", "name": "Authentication", "status": "pending"},
    {"id": "group_b", "name": "API Backend", "status": "pending"},
    {"id": "group_c", "name": "UI Components", "status": "pending"}
  ],
  "completed_groups": [],
  "in_progress_groups": [],
  "pending_groups": ["group_a", "group_b", "group_c"]
}
```

Expected output:
```
✓ Saved PM state for session sess_abc123

PM state snapshot stored in database.
```

---

**Scenario 4: Dashboard Requesting Data**

Input: Dashboard needs complete session overview

Request:
```
bazinga-db, please provide dashboard snapshot:

Session ID: sess_abc123
```

Expected output:
```
Dashboard Snapshot Retrieved:

Session: sess_abc123 (parallel mode, active)
- Created: 2025-11-12 14:30:00
- Last updated: 2025-11-12 15:45:23

Task Groups: 3 total
- Completed: 2 (group_a, group_b)
- In Progress: 1 (group_c)
- Pending: 0

Token Usage: 45,230 tokens
- PM: 12,450
- Developer: 28,340
- Tech Lead: 4,440

Recent Logs: 15 interactions logged

Full data available in returned JSON object.
```

---

**Scenario 5: Error Scenario (Permission Denied)**

Input: Agent tries to log interaction but database doesn't exist

Expected output:
```
❌ Database not found at: bazinga/bazinga.db

I can initialize the database now. This will:
- Create 8 tables with proper indexes
- Enable WAL mode for concurrency
- Set up foreign key constraints
- Takes ~2 seconds

Initializing database...

✓ Database initialized successfully

Proceeding with original request...
✓ Logged PM interaction for session sess_abc123
```

---

## Error Handling

**Database not found:**
- Auto-initialize using `init_db.py`
- Retry original operation

**Database locked:**
- Rare with WAL mode (30-second timeout handles this)
- If occurs: "Database operation succeeded (handled lock contention)"

**JSON parse error:**
- Validate JSON structure before passing to command
- Return: "Invalid JSON in state data. Please check formatting."

**Foreign key violation:**
- Session doesn't exist
- Auto-create session with default values, retry operation

**Invalid session_id format:**
- Return: "session_id must be provided and non-empty"
- Request clarification from calling agent

---

## Notes

- The script (`bazinga_db.py`) handles all SQL operations and concurrency
- Database uses WAL mode for concurrent reads/writes
- All operations are ACID-compliant
- State data stored as JSON (flexible schema)
- Supports both Python script execution and direct SQL if needed
- For detailed schema: see `references/schema.md` in skill directory
- For command examples: see `references/command_examples.md` in skill directory

---

## Quick Reference

**Most common operations:**

```bash
# Log interaction
python3 "$DB_SCRIPT" --db "$DB_PATH" log-interaction "$SID" "pm" "$CONTENT" 1

# Save PM state
python3 "$DB_SCRIPT" --db "$DB_PATH" save-state "$SID" "pm" '{"iteration":1}'

# Update task group
python3 "$DB_SCRIPT" --db "$DB_PATH" update-task-group "group_a" --status "completed"

# Dashboard snapshot
python3 "$DB_SCRIPT" --db "$DB_PATH" dashboard-snapshot "$SID"
```

**Success criteria:**
1. ✅ Correctly identifies operation type from request
2. ✅ Extracts all required parameters
3. ✅ Executes command without errors
4. ✅ Returns formatted response to calling agent
5. ✅ Handles errors gracefully with actionable messages

**Performance:** <1 second for single operations, <2 seconds for batch operations
