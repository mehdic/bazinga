---
name: bazinga-db
description: Database operations for BAZINGA orchestration system. This skill should be used when agents need to save or retrieve orchestration state, logs, task groups, token usage, or skill outputs. Replaces file-based storage with concurrent-safe SQLite database. Use instead of writing to coordination/*.json files or docs/orchestration-log.md.
---

# BAZINGA-DB: Database Operations for Orchestration

## Overview

This skill provides memory-efficient, concurrent-safe database operations for the BAZINGA orchestration system. It replaces file-based storage (JSON files and markdown logs) with a SQLite database that prevents race conditions, supports efficient queries, and improves dashboard performance.

**Key Benefits:**
- No file locking issues - ACID transactions prevent corruption
- Faster dashboard queries - Indexed lookups instead of full file reads
- Concurrent agent writes - Multiple developers can write simultaneously
- Efficient log pagination - Stream specific ranges instead of reading entire file
- Advanced analytics - SQL queries for token usage, agent performance, etc.

## When to Use This Skill

Use this skill whenever orchestration data needs to be persisted or retrieved:

**Orchestrator Agent:**
- Logging agent interactions after each spawn
- Saving orchestrator state (active agents, iteration, phase)
- Tracking token usage per agent spawn
- Recording decisions (spawn, escalate, complete)

**Project Manager Agent:**
- Saving PM state snapshots
- Creating and updating task groups
- Recording task group assignments

**Developer/QA/Tech Lead Agents:**
- Logging agent interactions
- Updating task group status
- Saving skill outputs (security scan, coverage, lint results)

**Dashboard Server:**
- Loading session state and logs
- Streaming logs with pagination
- Querying token usage summaries
- Getting real-time orchestration status

**DO NOT use this skill for:**
- General file I/O operations
- Code file management
- Configuration that doesn't relate to orchestration state

## Core Capabilities

### 1. Session Management

Create and track orchestration sessions from start to completion.

**Commands:**
```bash
# Create new session
python3 $SCRIPT --db $DB create-session <session_id> <mode> <requirements>

# Update session status
python3 $SCRIPT --db $DB update-session-status <session_id> <status>

# Get session details
python3 $SCRIPT --db $DB get-session <session_id>
```

**Example:**
```bash
# Orchestrator creates session at startup
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db /home/user/bazinga/coordination/bazinga.db \
  create-session \
  "bazinga_20250112_143022" \
  "parallel" \
  "Add user authentication with OAuth2"
```

### 2. Logging Agent Interactions

Record all agent interactions in structured format (replaces orchestration-log.md).

**Commands:**
```bash
# Log interaction
python3 $SCRIPT --db $DB log-interaction \
  <session_id> \
  <agent_type> \
  <content> \
  [iteration] \
  [agent_id]

# Get logs with filtering
python3 $SCRIPT --db $DB get-logs <session_id> [--limit N] [--agent-type TYPE] [--since TIMESTAMP]

# Stream logs as markdown
python3 $SCRIPT --db $DB stream-logs <session_id> [limit] [offset]
```

**Agent Types:** `pm`, `developer`, `qa`, `tech_lead`, `orchestrator`

**Example:**
```bash
# Orchestrator logs PM interaction
python3 $SCRIPT --db $DB log-interaction \
  "$SESSION_ID" \
  "pm" \
  "Analyzed requirements. Created 3 task groups: Authentication, API, Tests" \
  1 \
  "pm_main"

# Dashboard streams recent logs
python3 $SCRIPT --db $DB stream-logs "$SESSION_ID" 50 0
```

**Memory Efficiency:** Agents call this skill command instead of loading the entire orchestration-log.md file. The skill handles database writes efficiently.

### 3. State Management

Save and retrieve state snapshots (replaces pm_state.json, orchestrator_state.json, etc.).

**Commands:**
```bash
# Save state
python3 $SCRIPT --db $DB save-state <session_id> <state_type> <json_data>

# Get latest state
python3 $SCRIPT --db $DB get-state <session_id> <state_type>
```

**State Types:** `pm`, `orchestrator`, `group_status`

**Example:**
```bash
# PM saves state
python3 $SCRIPT --db $DB save-state \
  "$SESSION_ID" \
  "pm" \
  '{"mode":"parallel","iteration":3,"task_groups":[...]}'

# Orchestrator retrieves PM state
PM_STATE=$(python3 $SCRIPT --db $DB get-state "$SESSION_ID" "pm")
```

### 4. Task Group Management

Create and update task groups with status tracking.

**Commands:**
```bash
# Create task group
python3 $SCRIPT --db $DB create-task-group \
  <group_id> <session_id> <name> [status] [assigned_to]

# Update task group
python3 $SCRIPT --db $DB update-task-group \
  <group_id> \
  [--status STATUS] \
  [--assigned_to AGENT_ID] \
  [--revision_count N] \
  [--last_review_status STATUS]

# Get task groups
python3 $SCRIPT --db $DB get-task-groups <session_id> [status]
```

**Statuses:** `pending`, `in_progress`, `completed`, `failed`

**Review Statuses:** `APPROVED`, `CHANGES_REQUESTED`

**Example:**
```bash
# PM creates task groups
python3 $SCRIPT --db $DB create-task-group \
  "group_a" "$SESSION_ID" "Authentication" "pending"

# Orchestrator assigns task group
python3 $SCRIPT --db $DB update-task-group \
  "group_a" --assigned_to "developer_1" --status "in_progress"

# Tech Lead updates after review
python3 $SCRIPT --db $DB update-task-group \
  "group_a" --last_review_status "CHANGES_REQUESTED" --revision_count 1
```

### 5. Token Usage Tracking

Track token consumption per agent for budget management.

**Commands:**
```bash
# Log token usage
python3 $SCRIPT --db $DB log-tokens \
  <session_id> <agent_type> <tokens> [agent_id]

# Get token summary
python3 $SCRIPT --db $DB token-summary <session_id> [agent_type|agent_id]
```

**Example:**
```bash
# Orchestrator logs token usage after developer spawn
python3 $SCRIPT --db $DB log-tokens \
  "$SESSION_ID" "developer" 15000 "developer_1"

# Dashboard queries total usage
python3 $SCRIPT --db $DB token-summary "$SESSION_ID" agent_type
# Output: {"pm":5000,"developer":25000,"qa":8000,"total":38000}
```

### 6. Skill Output Storage

Save skill execution results (replaces security_scan.json, coverage_report.json, etc.).

**Commands:**
```bash
# Save skill output
python3 $SCRIPT --db $DB save-skill-output \
  <session_id> <skill_name> <json_data>

# Get skill output
python3 $SCRIPT --db $DB get-skill-output <session_id> <skill_name>
```

**Example:**
```bash
# Tech Lead saves security scan results
python3 $SCRIPT --db $DB save-skill-output \
  "$SESSION_ID" \
  "security_scan" \
  '{"vulnerabilities":3,"severity":"medium","details":[...]}'

# Dashboard retrieves results
python3 $SCRIPT --db $DB get-skill-output "$SESSION_ID" "security_scan"
```

### 7. Configuration Management

Store system-wide configuration (replaces skills_config.json, testing_config.json, etc.).

**Commands:**
```bash
# Set configuration
python3 $SCRIPT --db $DB set-config <key> <json_value>

# Get configuration
python3 $SCRIPT --db $DB get-config <key>
```

**Example:**
```bash
# Set skills configuration
python3 $SCRIPT --db $DB set-config \
  "skills_config" \
  '{"security_scan":{"status":"mandatory"},"test_coverage":{"status":"optional"}}'
```

### 8. Dashboard Data Retrieval

Get complete dashboard snapshot in a single query.

**Commands:**
```bash
# Get all dashboard data
python3 $SCRIPT --db $DB dashboard-snapshot <session_id>
```

**Returns:**
- Session metadata
- Latest orchestrator state
- Latest PM state
- All task groups with status
- Token usage summary
- Recent logs (last 10)

**Example:**
```bash
# Dashboard loads all data at once
python3 $SCRIPT --db $DB dashboard-snapshot "$SESSION_ID" | jq .
```

## Usage Patterns

### Orchestrator Agent Workflow

When orchestrator spawns an agent:

```bash
# 1. Log the spawn decision
python3 $SCRIPT --db $DB log-interaction \
  "$SESSION_ID" "orchestrator" \
  "Spawning developer for group_a" \
  $ITERATION

# 2. Update orchestrator state
python3 $SCRIPT --db $DB save-state \
  "$SESSION_ID" "orchestrator" \
  '{"active_agents":["developer_1"],"iteration":'"$ITERATION"'}'

# 3. Update task group assignment
python3 $SCRIPT --db $DB update-task-group \
  "group_a" --assigned_to "developer_1" --status "in_progress"

# 4. After agent completes, log tokens
python3 $SCRIPT --db $DB log-tokens \
  "$SESSION_ID" "developer" 15000 "developer_1"
```

### Project Manager Agent Workflow

When PM creates task breakdown:

```bash
# 1. Log PM analysis
python3 $SCRIPT --db $DB log-interaction \
  "$SESSION_ID" "pm" \
  "Created 3 task groups: Auth, API, Tests" \
  1 "pm_main"

# 2. Create task groups
python3 $SCRIPT --db $DB create-task-group \
  "group_a" "$SESSION_ID" "Authentication" "pending"
python3 $SCRIPT --db $DB create-task-group \
  "group_b" "$SESSION_ID" "API Development" "pending"
python3 $SCRIPT --db $DB create-task-group \
  "group_c" "$SESSION_ID" "Testing" "pending"

# 3. Save complete PM state
python3 $SCRIPT --db $DB save-state \
  "$SESSION_ID" "pm" \
  '{"mode":"parallel","iteration":1,"task_groups_created":3}'
```

### Developer Agent Workflow

When developer completes work:

```bash
# 1. Log completion
python3 $SCRIPT --db $DB log-interaction \
  "$SESSION_ID" "developer" \
  "Implemented authentication controller with OAuth2" \
  5 "developer_1"

# 2. Update task group status
python3 $SCRIPT --db $DB update-task-group \
  "group_a" --status "completed"
```

### Tech Lead Agent Workflow

When tech lead reviews code:

```bash
# 1. Log review
python3 $SCRIPT --db $DB log-interaction \
  "$SESSION_ID" "tech_lead" \
  "Review: Code quality good, test coverage below threshold" \
  6

# 2. Run skills and save outputs
# (After running security-scan skill)
python3 $SCRIPT --db $DB save-skill-output \
  "$SESSION_ID" "security_scan" '{"issues":0}'

# (After running test-coverage skill)
python3 $SCRIPT --db $DB save-skill-output \
  "$SESSION_ID" "test_coverage" '{"coverage":75,"threshold":80}'

# 3. Update task group with review result
python3 $SCRIPT --db $DB update-task-group \
  "group_a" \
  --last_review_status "CHANGES_REQUESTED" \
  --revision_count 1
```

## Database Initialization

Before using this skill, initialize the database:

```bash
python3 /home/user/bazinga/.claude/skills/bazinga-db/scripts/init_db.py \
  /home/user/bazinga/coordination/bazinga.db
```

This creates:
- All required tables with indexes
- Foreign key constraints
- WAL mode enabled for concurrency

Run this once per project, or when setting up a new database file.

## Path Variables

For convenience, set these variables:

```bash
BAZINGA_DB_SCRIPT="/home/user/bazinga/.claude/skills/bazinga-db/scripts/bazinga_db.py"
BAZINGA_DB_PATH="/home/user/bazinga/coordination/bazinga.db"
SESSION_ID="bazinga_20250112_143022"

# Then use:
python3 "$BAZINGA_DB_SCRIPT" --db "$BAZINGA_DB_PATH" <command> ...
```

## Migration from Files

To migrate existing file-based data to database:

**Step 1:** Initialize database (see above)

**Step 2:** Dual-write mode - Update agents to write to both files and database

**Step 3:** Verify database contains complete data

**Step 4:** Update dashboard to read from database

**Step 5:** Remove file writes from agents (optional)

This gradual migration ensures no data loss and allows rollback if needed.

## Performance Considerations

**Concurrent Writes:** SQLite WAL mode allows multiple readers and one writer simultaneously. Lock contention is handled automatically with 30-second timeout.

**Query Performance:** All high-frequency queries have supporting indexes:
- Session-based queries: O(log n) lookup via indexes
- Time-ordered queries: Descending timestamp indexes for recent data
- Agent-type filtering: Indexed for fast filtering

**Memory Efficiency:** Agents don't need to load large files into memory. The skill handles database I/O efficiently, keeping agent context windows lean.

**Dashboard Speed:** Indexed queries are ~10-100x faster than reading entire JSON/markdown files, especially for large logs (>1000 entries).

## Error Handling

The skill handles common errors automatically:

**Database Locked:** 30-second timeout with automatic retry
**Foreign Key Violations:** Clear error messages returned
**JSON Parse Errors:** Validated before insertion
**Missing Database:** Clear message to run init_db.py

Check command exit codes:
- `0` = Success
- `1` = Error (see stderr for details)

## Resources

### scripts/

**init_db.py** - Database initialization script. Creates all tables with proper schema, indexes, and constraints. Run once per database file.

**bazinga_db.py** - Main database client. Provides all CRUD operations via simple command interface. Can also be imported as Python module for dashboard integration.

### references/

**schema.md** - Complete database schema documentation with table definitions, column descriptions, and indexes.

**command_examples.md** - Comprehensive command examples for all operations including workflows and integration patterns.

## Advanced Usage

### Custom SQL Queries

For complex analytics not covered by standard commands:

```bash
python3 $SCRIPT --db $DB query \
  "SELECT agent_type, COUNT(*) FROM orchestration_logs WHERE session_id = '$SESSION_ID' GROUP BY agent_type"
```

**Note:** Only SELECT queries are allowed for safety.

### Python API Integration

Dashboard can import the Python class directly:

```python
from bazinga_db import BazingaDB

db = BazingaDB('/home/user/bazinga/coordination/bazinga.db')
logs = db.get_logs(session_id, limit=50, agent_type='developer')
snapshot = db.get_dashboard_snapshot(session_id)
```

This avoids shell command overhead for high-frequency dashboard queries.

## Troubleshooting

**"Database locked" errors:**
- Normal during high concurrency - handled automatically
- If persistent, check for long-running transactions

**"Database not found" errors:**
- Run init_db.py to create database

**JSON parse errors:**
- Validate JSON with `jq` before passing to commands
- Ensure proper shell quoting (single quotes for JSON strings)

**Missing data:**
- Verify correct session_id
- Check agent is actually calling the skill commands
- Query database directly with sqlite3 to debug

## See Also

- Schema documentation: `references/schema.md`
- Command examples: `references/command_examples.md`
- SQLite WAL mode: https://www.sqlite.org/wal.html
