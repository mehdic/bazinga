---
name: bazinga-db
description: Database operations for BAZINGA orchestration system. This skill should be used when agents need to save or retrieve orchestration state, logs, task groups, token usage, or skill outputs. Replaces file-based storage with concurrent-safe SQLite database. Use instead of writing to coordination/*.json files or docs/orchestration-log.md.
allowed-tools: [Bash, Read]
---

# BAZINGA-DB Skill

## Purpose

This skill provides concurrent-safe database operations for BAZINGA orchestration. Execute database commands efficiently using the Python client, handling all data persistence for sessions, logs, state, task groups, tokens, and skill outputs.

**Key Capabilities:**
- Session management (create, update, query)
- Agent interaction logging (replaces orchestration-log.md)
- State snapshots (replaces JSON state files)
- Task group tracking (normalized from PM state)
- Token usage tracking
- Skill output storage
- Configuration management
- Dashboard data aggregation

## Automatic Invocation

This skill is **automatically invoked** when:
- Orchestrator needs to log agent interactions or save state
- Project Manager needs to save PM state or create/update task groups
- Developer/QA/Tech Lead needs to log completion or update task status
- Any agent needs to save skill outputs (security scan, coverage, lint)
- Dashboard needs to query orchestration data
- Any agent mentions "save to database" or "query database" or "bazinga-db"

## Environment Setup

**Database Paths:**
```bash
DB_SCRIPT="/home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py"
DB_PATH="/home/user/bazinga/coordination/bazinga.db"
```

**Initialization Check:**
Before first use, verify database exists. If not, initialize it:
```bash
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/init_db.py "$DB_PATH"
```

## Request Parsing

When invoked, parse the request to identify:
1. **Operation type** (log, save, get, update, query)
2. **Data type** (session, log, state, task_group, tokens, skill_output, config)
3. **Required parameters** (session_id, agent_type, content, etc.)
4. **Optional parameters** (iteration, agent_id, filters, limits)

### Common Request Patterns

**Pattern Recognition:**
- "log this interaction" → `log-interaction`
- "save PM state" / "save orchestrator state" → `save-state`
- "get latest PM state" / "retrieve state" → `get-state`
- "create task group" → `create-task-group`
- "update task group" → `update-task-group`
- "log token usage" / "track tokens" → `log-tokens`
- "save security scan results" / "save skill output" → `save-skill-output`
- "get dashboard data" / "dashboard snapshot" → `dashboard-snapshot`
- "stream logs" / "get recent logs" → `stream-logs`

## Operations

### 1. Session Management

#### Create Session
**When:** Orchestrator starts new session
**Parameters:** session_id, mode (simple/parallel), requirements (user request)
**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" create-session \
  "<session_id>" \
  "<mode>" \
  "<requirements>"
```
**Return:** Confirmation message

#### Update Session Status
**When:** Session completes or fails
**Parameters:** session_id, status (active/completed/failed)
**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" update-session-status \
  "<session_id>" \
  "<status>"
```
**Return:** Confirmation message

### 2. Logging Agent Interactions

#### Log Interaction
**When:** Any agent completes a spawn (PM, developer, QA, tech lead, orchestrator)
**Parameters:**
- session_id (required)
- agent_type (required): pm, developer, qa, tech_lead, orchestrator
- content (required): full agent response text
- iteration (optional): orchestration iteration number
- agent_id (optional): specific agent instance (e.g., "developer_1")

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" log-interaction \
  "<session_id>" \
  "<agent_type>" \
  "<content>" \
  [iteration] \
  [agent_id]
```

**Content Handling:**
- Escape single quotes in content: replace `'` with `'\''`
- Preserve newlines and formatting
- Use heredoc for large content if needed

**Return:** "✓ Logged {agent_type} interaction"

#### Stream Logs
**When:** Dashboard needs to display logs, or agent needs to review recent activity
**Parameters:**
- session_id (required)
- limit (optional, default 50): number of logs to retrieve
- offset (optional, default 0): skip first N logs

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" stream-logs \
  "<session_id>" \
  [limit] \
  [offset]
```
**Return:** Markdown-formatted logs with timestamps and agent types

### 3. State Management

#### Save State
**When:** PM or orchestrator needs to save current state
**Parameters:**
- session_id (required)
- state_type (required): pm, orchestrator, group_status
- state_data (required): JSON object with complete state

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" save-state \
  "<session_id>" \
  "<state_type>" \
  '<json_data>'
```

**JSON Handling:**
- Use single quotes around JSON to prevent shell interpolation
- Escape internal single quotes if present
- Validate JSON structure before passing

**Return:** "✓ Saved {state_type} state"

#### Get Latest State
**When:** Agent needs to retrieve current state
**Parameters:**
- session_id (required)
- state_type (required): pm, orchestrator, group_status

**Command:**
```bash
STATE=$(python3 "$DB_SCRIPT" --db "$DB_PATH" get-state \
  "<session_id>" \
  "<state_type>")
```
**Return:** JSON object with state data (or null if not found)

**Parse return value** and present to calling agent in readable format.

### 4. Task Group Management

#### Create Task Group
**When:** PM creates task breakdown
**Parameters:**
- group_id (required): unique identifier (e.g., "group_a")
- session_id (required)
- name (required): human-readable task name
- status (optional, default "pending"): pending, in_progress, completed, failed
- assigned_to (optional): agent ID

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" create-task-group \
  "<group_id>" \
  "<session_id>" \
  "<name>" \
  [status] \
  [assigned_to]
```
**Return:** "✓ Task group created: {group_id}"

#### Update Task Group
**When:** Orchestrator assigns work, or agent completes work, or tech lead reviews
**Parameters:**
- group_id (required)
- status (optional): pending, in_progress, completed, failed
- assigned_to (optional): agent ID
- revision_count (optional): increment for escalation
- last_review_status (optional): APPROVED, CHANGES_REQUESTED

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" update-task-group \
  "<group_id>" \
  [--status "<status>"] \
  [--assigned_to "<agent_id>"] \
  [--revision_count <N>] \
  [--last_review_status "<status>"]
```
**Return:** "✓ Task group updated: {group_id}"

### 5. Token Usage Tracking

#### Log Token Usage
**When:** Orchestrator records token consumption after agent spawn
**Parameters:**
- session_id (required)
- agent_type (required): pm, developer, qa, tech_lead
- tokens (required): estimated token count
- agent_id (optional): specific agent instance

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" log-tokens \
  "<session_id>" \
  "<agent_type>" \
  <tokens> \
  [agent_id]
```
**Return:** Success (silent)

#### Get Token Summary
**When:** Dashboard or orchestrator needs token usage overview
**Parameters:**
- session_id (required)
- by (optional, default "agent_type"): agent_type or agent_id

**Command:**
```bash
SUMMARY=$(python3 "$DB_SCRIPT" --db "$DB_PATH" token-summary \
  "<session_id>" \
  [by])
```
**Return:** JSON object with token breakdown and total

### 6. Skill Output Storage

#### Save Skill Output
**When:** Tech lead runs skills (security-scan, test-coverage, lint-check)
**Parameters:**
- session_id (required)
- skill_name (required): security_scan, test_coverage, lint_check, etc.
- output_data (required): JSON object with skill results

**Command:**
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" save-skill-output \
  "<session_id>" \
  "<skill_name>" \
  '<json_data>'
```
**Return:** "✓ Saved {skill_name} output"

#### Get Skill Output
**When:** Agent needs to retrieve previous skill results
**Parameters:**
- session_id (required)
- skill_name (required)

**Command:**
```bash
OUTPUT=$(python3 "$DB_SCRIPT" --db "$DB_PATH" get-skill-output \
  "<session_id>" \
  "<skill_name>")
```
**Return:** JSON object with skill output (or null if not found)

### 7. Dashboard Data

#### Get Dashboard Snapshot
**When:** Dashboard needs complete overview of session
**Parameters:**
- session_id (required)

**Command:**
```bash
SNAPSHOT=$(python3 "$DB_SCRIPT" --db "$DB_PATH" dashboard-snapshot \
  "<session_id>")
```
**Return:** JSON object containing:
- session metadata
- latest orchestrator state
- latest PM state
- all task groups
- token usage summary
- recent logs (last 10)

**Optimization:** This is a single query that aggregates all dashboard data efficiently.

## Execution Workflow

### Step 1: Parse Request
Extract operation type and parameters from the calling agent's request.

### Step 2: Validate Parameters
- Check required parameters are present
- Validate parameter formats (session_id pattern, agent_type enum, etc.)
- If missing parameters, ask calling agent for clarification

### Step 3: Build Command
Construct the appropriate `bazinga_db.py` command with parameters.

### Step 4: Execute via Bash Tool
Run the command using the Bash tool with proper error handling.

### Step 5: Parse Result
- If exit code 0: Extract output and present to calling agent
- If exit code 1: Read stderr, identify error, report to calling agent

### Step 6: Return Response
Provide structured response to calling agent:
- Success confirmation for write operations
- Data payload for read operations
- Error message with suggested fix if failed

## Error Handling

### Common Errors

**"Database not found"**
- **Cause:** Database not initialized
- **Fix:** Run `init_db.py` script
- **Auto-fix:** Execute initialization automatically if database missing

**"Database locked"**
- **Cause:** Concurrent write contention (rare with WAL mode)
- **Fix:** Retry automatically (30-second timeout handles this)
- **Response:** "Database operation succeeded (handled lock contention)"

**"JSON parse error"**
- **Cause:** Invalid JSON in state_data or skill_output
- **Fix:** Validate JSON before passing to command
- **Prevention:** Use proper shell quoting (single quotes around JSON)

**"Foreign key violation"**
- **Cause:** Referencing non-existent session_id
- **Fix:** Create session first before logging/saving data
- **Auto-fix:** If session_id doesn't exist, create it with default values

### Error Response Format

When returning errors to calling agent:
```
❌ Operation failed: {error_message}

Suggested fix: {fix_description}

Would you like me to attempt the fix automatically?
```

## Performance Optimization

### Batch Operations
When multiple operations are requested together, execute them in a single bash command chain:
```bash
python3 "$DB_SCRIPT" --db "$DB_PATH" log-interaction ... && \
python3 "$DB_SCRIPT" --db "$DB_PATH" save-state ... && \
python3 "$DB_SCRIPT" --db "$DB_PATH" update-task-group ...
```

### Caching
For repeated reads within same invocation, cache results in memory:
- Latest PM state
- Latest orchestrator state
- Task group list

### Smart Defaults
If optional parameters not provided, use smart defaults:
- iteration: derive from orchestrator state if available
- mode: "parallel" if not specified
- status: "pending" for new task groups

## Response Formatting

### For Write Operations
Keep responses concise:
```
✓ Logged PM interaction (iteration 1)
✓ Saved orchestrator state
✓ Updated task group: group_a → completed
```

### For Read Operations
Format data for readability:
```
Current PM State (as of [timestamp]):
- Mode: parallel
- Iteration: 5
- Task Groups: 3 (2 completed, 1 in progress)

Recent Logs (last 10):
[Formatted log entries with timestamps]
```

### For Errors
Be actionable:
```
❌ Could not save state: Database not initialized

I can initialize the database now. This takes 2 seconds and creates:
- 8 tables with proper indexes
- WAL mode for concurrency
- Foreign key constraints

Proceed with initialization?
```

## Integration Points

### With Orchestrator
- Log all agent spawns and completions
- Save orchestrator state after each iteration
- Track token usage per spawn
- Update task group assignments

### With Project Manager
- Save PM state after task breakdown
- Create task groups for each work unit
- Track iteration count

### With Developers/QA/Tech Lead
- Log agent completion messages
- Update task group status
- Save skill outputs

### With Dashboard
- Provide complete snapshots for UI
- Stream paginated logs
- Return token summaries

## Reference Documentation

For detailed schema and examples, load reference files as needed:
- `references/schema.md` - Complete database schema with table definitions
- `references/command_examples.md` - Comprehensive command examples

**When to load references:**
- Agent asks about schema details
- Agent needs complex query examples
- Agent asks about table relationships or indexes

Use Read tool to load reference files only when needed to keep context efficient.

## Quick Reference

**Most Common Operations:**

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

## Success Criteria

A successful invocation:
1. ✅ Correctly identifies operation type from request
2. ✅ Extracts all required parameters
3. ✅ Executes command without errors
4. ✅ Returns formatted response to calling agent
5. ✅ Handles errors gracefully with actionable messages

**Speed Target:** <1 second for single operations, <2 seconds for batch operations
