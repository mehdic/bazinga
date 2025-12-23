# BAZINGA-DB Command Examples

This document provides practical examples of using the bazinga-db skill commands.

## Command Format

All commands follow this pattern:
```bash
python3 /path/to/bazinga_db.py --db /path/to/bazinga.db <command> [arguments...]
```

For brevity, examples below use (relative paths for portability):
```bash
$DB_SCRIPT = .claude/skills/bazinga-db/scripts/bazinga_db.py
$DB_PATH = bazinga/bazinga.db
```

---

## Session Management

### Create New Session
```bash
python3 $DB_SCRIPT --db $DB_PATH create-session \
  "bazinga_20250112_143022" \
  "parallel" \
  "Add user authentication feature with OAuth2"
```

### Update Session Status
```bash
# Mark session as completed
python3 $DB_SCRIPT --db $DB_PATH update-session-status \
  "bazinga_20250112_143022" \
  "completed"

# Mark as failed
python3 $DB_SCRIPT --db $DB_PATH update-session-status \
  "bazinga_20250112_143022" \
  "failed"
```

### Get Session Details
```bash
python3 $DB_SCRIPT --db $DB_PATH get-session \
  "bazinga_20250112_143022"
```

---

## Logging Agent Interactions

### Log PM Interaction
```bash
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "bazinga_123" \
  "pm" \
  "Analyzed requirements and created 3 task groups..." \
  1 \
  "pm_main"
```

### Log Developer Interaction
```bash
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "bazinga_123" \
  "developer" \
  "Implemented authentication controller..." \
  5 \
  "developer_1"
```

### Log Orchestrator Decision
```bash
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "bazinga_123" \
  "orchestrator" \
  "Spawning 2 developers in parallel for Groups A and B" \
  3
```

---

## State Management

### Save PM State
```bash
python3 $DB_SCRIPT --db $DB_PATH save-state \
  "bazinga_123" \
  "pm" \
  '{"mode":"parallel","iteration":3,"task_groups":[{"id":"group_a","status":"completed"}]}'
```

### Save Orchestrator State
```bash
python3 $DB_SCRIPT --db $DB_PATH save-state \
  "bazinga_123" \
  "orchestrator" \
  '{"phase":"development","active_agents":["developer_1","developer_2"],"iteration":10}'
```

### Retrieve Latest State
```bash
# Get PM state
python3 $DB_SCRIPT --db $DB_PATH get-state \
  "bazinga_123" \
  "pm"

# Get orchestrator state
python3 $DB_SCRIPT --db $DB_PATH get-state \
  "bazinga_123" \
  "orchestrator"
```

---

## Task Group Management

### Create Task Group
```bash
# Basic creation
python3 $DB_SCRIPT --db $DB_PATH create-task-group \
  "group_a" \
  "bazinga_123" \
  "Authentication Implementation" \
  "pending"

# Full creation with all PM fields
python3 $DB_SCRIPT --db $DB_PATH create-task-group \
  "group_a" \
  "bazinga_123" \
  "Authentication Implementation" \
  "pending" \
  --complexity 7 \
  --initial_tier "Senior Software Engineer" \
  --item_count 5 \
  --component-path "backend/auth/" \
  --specializations '["bazinga/templates/specializations/01-languages/python.md"]'
```

### Update Task Group Status
```bash
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" \
  "bazinga_123" \
  --status "completed" \
  --last_review_status "APPROVED"

# Update complexity score
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" \
  "bazinga_123" \
  --complexity 5
```

### Increment Revision Count
```bash
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" \
  "bazinga_123" \
  --revision_count 2
```

### Assign Task Group
```bash
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" \
  "bazinga_123" \
  --assigned_to "developer_1"
```

---

## Reading Logs

### Stream Recent Logs (Markdown Format)
```bash
# Get last 50 logs
python3 $DB_SCRIPT --db $DB_PATH stream-logs \
  "bazinga_123"

# With pagination
python3 $DB_SCRIPT --db $DB_PATH stream-logs \
  "bazinga_123" \
  50 \
  100  # offset
```

### Get Logs (JSON Format)
```bash
# Recent logs
python3 $DB_SCRIPT --db $DB_PATH get-logs \
  "bazinga_123" \
  --limit 10

# Filter by agent type
python3 $DB_SCRIPT --db $DB_PATH get-logs \
  "bazinga_123" \
  --agent-type developer \
  --limit 20

# Time-range query
python3 $DB_SCRIPT --db $DB_PATH get-logs \
  "bazinga_123" \
  --since "2025-01-12 14:00:00" \
  --limit 100
```

---

## Token Usage Tracking

### Log Token Usage
```bash
python3 $DB_SCRIPT --db $DB_PATH log-tokens \
  "bazinga_123" \
  "developer" \
  15000 \
  "developer_1"
```

### Get Token Summary
```bash
# By agent type
python3 $DB_SCRIPT --db $DB_PATH token-summary \
  "bazinga_123" \
  agent_type

# By agent ID
python3 $DB_SCRIPT --db $DB_PATH token-summary \
  "bazinga_123" \
  agent_id
```

Example output:
```json
{
  "pm": 5000,
  "developer": 25000,
  "qa": 8000,
  "tech_lead": 7000,
  "total": 45000
}
```

---

## Skill Outputs

### Save Skill Output
```bash
python3 $DB_SCRIPT --db $DB_PATH save-skill-output \
  "bazinga_123" \
  "security_scan" \
  '{"vulnerabilities":5,"severity":"medium","details":[...]}'
```

### Retrieve Skill Output
```bash
python3 $DB_SCRIPT --db $DB_PATH get-skill-output \
  "bazinga_123" \
  "security_scan"
```

---

## Configuration

**REMOVED:** Configuration table no longer exists (2025-11-21).
See `research/empty-tables-analysis.md` for details.

Use file-based configuration instead:
- Skills config: `bazinga/skills_config.json`
- Testing config: `bazinga/testing_config.json`

---

## Dashboard Data

### Get Complete Dashboard Snapshot
```bash
python3 $DB_SCRIPT --db $DB_PATH dashboard-snapshot \
  "bazinga_123"
```

Returns:
```json
{
  "session": {...},
  "orchestrator_state": {...},
  "pm_state": {...},
  "task_groups": [...],
  "token_summary": {...},
  "recent_logs": [...]
}
```

---

## Advanced Queries

### Custom SQL Query
```bash
# Agent interaction counts
python3 $DB_SCRIPT --db $DB_PATH query \
  "SELECT agent_type, COUNT(*) as count FROM orchestration_logs WHERE session_id = 'bazinga_123' GROUP BY agent_type"

# Average response length
python3 $DB_SCRIPT --db $DB_PATH query \
  "SELECT agent_type, AVG(LENGTH(content)) as avg_length FROM orchestration_logs WHERE session_id = 'bazinga_123' GROUP BY agent_type"
```

---

## Common Workflows

### Orchestrator Spawn Workflow
```bash
# 1. Log orchestrator decision
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "$SESSION_ID" "orchestrator" "Spawning developer for group_a" $ITERATION

# 2. Update orchestrator state
python3 $DB_SCRIPT --db $DB_PATH save-state \
  "$SESSION_ID" "orchestrator" \
  "{\"active_agents\":[\"developer_1\"],\"iteration\":$ITERATION}"

# 3. Update task group
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" "$SESSION_ID" --status "in_progress" --assigned_to "developer_1"
```

### Developer Completion Workflow
```bash
# 1. Log developer completion
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "$SESSION_ID" "developer" "Implementation completed" $ITERATION "developer_1"

# 2. Log token usage
python3 $DB_SCRIPT --db $DB_PATH log-tokens \
  "$SESSION_ID" "developer" 15000 "developer_1"

# 3. Update task group
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" "$SESSION_ID" --status "completed"
```

### Tech Lead Review Workflow
```bash
# 1. Log tech lead review
python3 $DB_SCRIPT --db $DB_PATH log-interaction \
  "$SESSION_ID" "tech_lead" "Code review: Changes requested" $ITERATION

# 2. Update task group with review result
python3 $DB_SCRIPT --db $DB_PATH update-task-group \
  "group_a" \
  "$SESSION_ID" \
  --last_review_status "CHANGES_REQUESTED" \
  --revision_count 1

# 3. Save skill outputs (if skills ran)
python3 $DB_SCRIPT --db $DB_PATH save-skill-output \
  "$SESSION_ID" "test_coverage" '{"coverage":75,"threshold":80}'
```

---

## Error Handling

### Check Database Exists
```bash
if [ ! -f "$DB_PATH" ]; then
  echo "Database not initialized. Run init_db.py first."
  python3 /path/to/init_db.py "$DB_PATH"
fi
```

### Retry on Lock
```bash
# The client has 30-second timeout built-in
# No manual retry needed - SQLite handles lock contention automatically
```

### Validate JSON Before Saving
```bash
# Use jq to validate JSON
echo '{"test":"data"}' | jq . && \
  python3 $DB_SCRIPT --db $DB_PATH save-state "session" "pm" '{"test":"data"}'
```

---

## Integration with Bash Tool

When using from Claude Code's Bash tool:

```bash
# Set up variables (relative paths for portability)
DB_SCRIPT=".claude/skills/bazinga-db/scripts/bazinga_db.py"
DB_PATH="bazinga/bazinga.db"
SESSION_ID="bazinga_20250112_143022"

# Example: Log interaction and update state in one command chain
python3 "$DB_SCRIPT" --db "$DB_PATH" log-interaction \
  "$SESSION_ID" "pm" "Created task breakdown" 1 && \
python3 "$DB_SCRIPT" --db "$DB_PATH" save-state \
  "$SESSION_ID" "pm" '{"iteration":1,"mode":"parallel"}'
```

---

## Python API Usage (For Dashboard)

The `BazingaDB` class can be imported directly:

```python
from bazinga_db import BazingaDB

db = BazingaDB('/home/user/bazinga/bazinga/bazinga.db')

# Query logs
logs = db.get_logs('bazinga_123', limit=10, agent_type='developer')

# Get dashboard data
snapshot = db.get_dashboard_snapshot('bazinga_123')

# Stream logs in markdown
markdown = db.stream_logs('bazinga_123', limit=50)
```
