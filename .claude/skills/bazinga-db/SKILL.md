---
name: bazinga-db
description: Database operations for BAZINGA orchestration system. This skill should be used when agents need to save or retrieve orchestration state, logs, task groups, token usage, or skill outputs. Replaces file-based storage with concurrent-safe SQLite database. Use instead of writing to coordination/*.json files or docs/orchestration-log.md.
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
- Replacing file writes to `coordination/*.json` or `docs/orchestration-log.md`

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
DB_PATH="/home/user/bazinga/coordination/bazinga.db"
```

**Auto-initialization:**
The database will be automatically initialized on first use (< 2 seconds). The script detects if the database doesn't exist and runs the initialization automatically, creating all tables with proper indexes and WAL mode for concurrency.

No manual initialization needed - just invoke the skill and it handles everything.

---

## Step 1: Parse Request

Extract from the calling agent's request:

**Operation type:**
- "log interaction" / "save log" → log-interaction
- "save PM state" / "save orchestrator state" → save-state
- "get state" / "retrieve state" → get-state
- "create task group" → create-task-group
- "update task group" / "mark complete" → update-task-group
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

**Dashboard snapshot:**
```bash
SNAPSHOT=$(python3 "$DB_SCRIPT" --db "$DB_PATH" dashboard-snapshot \
  "<session_id>")
```

**Full command reference:** See `scripts/bazinga_db.py --help` for all available operations.

---

## Step 3: Return Formatted Response

**For write operations:**
Return concise confirmation:
```
✓ Logged PM interaction (iteration 1)
✓ Saved orchestrator state
✓ Updated task group: group_a → completed
```

**For read operations:**
Use the **Read** tool if needed to parse JSON, then format for readability:
```
Current PM State (as of [timestamp]):
- Mode: parallel
- Iteration: 5
- Task Groups: 3 (2 completed, 1 in progress)

[Formatted data]
```

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

**Scenario 1: Orchestrator Logging PM Interaction**

Input: Orchestrator completed PM spawn, needs to log the interaction

Request parameters:
- session_id: "sess_abc123"
- agent_type: "pm"
- content: "Task breakdown created: 3 groups (group_a, group_b, group_c)..."
- iteration: 1

Expected output:
```
✓ Logged PM interaction for session sess_abc123

Database operation successful.
```

---

**Scenario 2: PM Saving State**

Input: PM completed task breakdown, needs to save PM state

Request parameters:
- session_id: "sess_abc123"
- state_type: "pm"
- state_data: `{"iteration": 1, "mode": "parallel", "task_groups": [...]}`

Expected output:
```
✓ Saved PM state for session sess_abc123

PM state snapshot stored in database.
```

---

**Scenario 3: Dashboard Requesting Data**

Input: Dashboard needs complete session overview

Request parameters:
- session_id: "sess_abc123"

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

**Scenario 4: First Invocation (Database Not Initialized)**

Input: Agent tries to log interaction but database doesn't exist

Expected output:
```
❌ Database not found at: coordination/bazinga.db

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
