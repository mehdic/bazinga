# BAZINGA Database Schema Reference

This document provides complete reference documentation for the BAZINGA database schema.

## Database Configuration

- **Engine**: SQLite 3
- **Journal Mode**: WAL (Write-Ahead Logging) for better concurrency
- **Foreign Keys**: Enabled for referential integrity
- **Location**: `/home/user/bazinga/bazinga/bazinga.db`

## Tables Overview

| Table | Purpose | Key Features |
|-------|---------|-------------|
| `sessions` | Track orchestration sessions | Primary session metadata |
| `orchestration_logs` | Agent interaction logs | Replaces orchestration-log.md |
| `state_snapshots` | State history | Replaces JSON state files |
| `task_groups` | PM task management | Normalized from pm_state.json |
| `token_usage` | Token tracking | Per-agent token consumption |
| `skill_outputs` | Skill results | Replaces skill JSON files |
| `configuration` | System config | Replaces config JSON files |
| `decisions` | Orchestrator decisions | Decision audit trail |

---

## Table Schemas

### sessions

Tracks orchestration sessions from creation to completion.

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    mode TEXT CHECK(mode IN ('simple', 'parallel')),
    original_requirements TEXT,
    status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `session_id`: Unique session identifier (e.g., `bazinga_20250112_143022`)
- `start_time`: Session start timestamp
- `end_time`: Session completion timestamp (NULL if active)
- `mode`: Execution mode (`simple` or `parallel`)
- `original_requirements`: Original user request text
- `status`: Current session status
- `created_at`: Record creation timestamp

**Usage Example:**
```python
# Create new session
db.create_session('bazinga_20250112_143022', 'parallel', 'Add authentication feature')

# Update session status
db.update_session_status('bazinga_20250112_143022', 'completed')
```

---

### orchestration_logs

Stores all agent interactions (replaces `orchestration-log.md`).

```sql
CREATE TABLE orchestration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iteration INTEGER,
    agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')),
    agent_id TEXT,
    content TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_logs_session ON orchestration_logs(session_id, timestamp DESC);
CREATE INDEX idx_logs_agent_type ON orchestration_logs(session_id, agent_type);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When the interaction occurred
- `iteration`: Orchestration iteration number
- `agent_type`: Type of agent (`pm`, `developer`, `qa`, `tech_lead`, `orchestrator`)
- `agent_id`: Specific agent instance (e.g., `developer_1`)
- `content`: Full agent response text

**Indexes:**
- `idx_logs_session`: Fast session-based queries sorted by time
- `idx_logs_agent_type`: Filter by agent type efficiently

**Usage Example:**
```python
# Log agent interaction
db.log_interaction(
    session_id='bazinga_123',
    agent_type='developer',
    content='Implemented authentication...',
    iteration=5,
    agent_id='developer_1'
)

# Query recent logs
logs = db.get_logs('bazinga_123', limit=10, agent_type='developer')
```

---

### state_snapshots

Stores state snapshots over time (replaces `pm_state.json`, `orchestrator_state.json`, etc.).

```sql
CREATE TABLE state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state_type TEXT CHECK(state_type IN ('pm', 'orchestrator', 'group_status')),
    state_data TEXT NOT NULL,  -- JSON format
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_state_session_type ON state_snapshots(session_id, state_type, timestamp DESC);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When the state was saved
- `state_type`: Type of state (`pm`, `orchestrator`, `group_status`)
- `state_data`: Complete state as JSON string

**Usage Example:**
```python
# Save PM state
pm_state = {
    'mode': 'parallel',
    'iteration': 5,
    'task_groups': [...]
}
db.save_state('bazinga_123', 'pm', pm_state)

# Retrieve latest state
current_state = db.get_latest_state('bazinga_123', 'pm')
```

---

### task_groups

Normalized task group tracking (extracted from `pm_state.json`).

```sql
CREATE TABLE task_groups (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status);
```

**Columns:**
- `id`: Unique task group identifier (e.g., `group_a`)
- `session_id`: Foreign key to sessions table
- `name`: Human-readable task group name
- `status`: Current status
- `assigned_to`: Agent ID assigned to this group
- `revision_count`: Number of revision cycles (for escalation)
- `last_review_status`: Tech Lead review result
- `created_at`: When task group was created
- `updated_at`: Last modification timestamp

**Usage Example:**
```python
# Create task group
db.create_task_group('group_a', 'bazinga_123', 'Authentication', status='pending')

# Update task group
db.update_task_group('group_a', status='completed', last_review_status='APPROVED')

# Get incomplete task groups
incomplete = db.get_task_groups('bazinga_123', status='in_progress')
```

---

### token_usage

Tracks token consumption per agent.

```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_type TEXT NOT NULL,
    agent_id TEXT,
    tokens_estimated INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_tokens_session ON token_usage(session_id, agent_type);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When tokens were consumed
- `agent_type`: Type of agent
- `agent_id`: Specific agent instance
- `tokens_estimated`: Estimated token count

**Usage Example:**
```python
# Log token usage
db.log_tokens('bazinga_123', 'developer', 15000, agent_id='developer_1')

# Get token summary
summary = db.get_token_summary('bazinga_123', by='agent_type')
# Returns: {'pm': 5000, 'developer': 25000, 'qa': 8000, 'total': 38000}
```

---

### skill_outputs

Stores skill execution outputs (replaces individual JSON files).

```sql
CREATE TABLE skill_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    skill_name TEXT NOT NULL,
    output_data TEXT NOT NULL,  -- JSON format
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_skill_session ON skill_outputs(session_id, skill_name, timestamp DESC);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When skill output was saved
- `skill_name`: Name of skill (e.g., `security_scan`, `test_coverage`)
- `output_data`: Complete output as JSON string

**Usage Example:**
```python
# Save skill output
security_results = {'vulnerabilities': [...], 'severity': 'high'}
db.save_skill_output('bazinga_123', 'security_scan', security_results)

# Retrieve latest skill output
results = db.get_skill_output('bazinga_123', 'security_scan')
```

---

### configuration

System-wide configuration storage (replaces `skills_config.json`, `testing_config.json`, etc.).

```sql
CREATE TABLE configuration (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,  -- JSON format
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `key`: Configuration key (e.g., `skills_config`, `testing_mode`)
- `value`: Configuration value as JSON string
- `updated_at`: Last update timestamp

**Usage Example:**
```python
# Set configuration
db.set_config('testing_mode', {'framework': 'full', 'coverage_threshold': 80})

# Get configuration
config = db.get_config('testing_mode')
```

---

### decisions

Audit trail of orchestrator decisions.

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iteration INTEGER,
    decision_type TEXT NOT NULL,
    decision_data TEXT NOT NULL,  -- JSON format
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_decisions_session ON decisions(session_id, timestamp DESC);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When decision was made
- `iteration`: Orchestration iteration number
- `decision_type`: Type of decision (e.g., `spawn_agent`, `escalate_model`)
- `decision_data`: Decision details as JSON string

---

## Query Examples

### Get Dashboard Overview
```python
snapshot = db.get_dashboard_snapshot('bazinga_123')
# Returns complete dashboard state in one query
```

### Filter Logs by Time Range
```python
logs = db.get_logs(
    session_id='bazinga_123',
    since='2025-01-12 14:00:00',
    limit=100
)
```

### Get Incomplete Tasks
```python
tasks = db.get_task_groups('bazinga_123', status='in_progress')
```

### Token Usage Analysis
```python
by_type = db.get_token_summary('bazinga_123', by='agent_type')
by_agent = db.get_token_summary('bazinga_123', by='agent_id')
```

### Custom Analytics Query
```python
results = db.query("""
    SELECT agent_type, COUNT(*) as interaction_count,
           AVG(LENGTH(content)) as avg_response_length
    FROM orchestration_logs
    WHERE session_id = ?
    GROUP BY agent_type
""", ('bazinga_123',))
```

---

## Migration from Files

| Old File | New Table | Migration Path |
|----------|-----------|----------------|
| `orchestration-log.md` | `orchestration_logs` | Parse markdown, insert rows |
| `pm_state.json` | `state_snapshots` + `task_groups` | JSON to normalized tables |
| `orchestrator_state.json` | `state_snapshots` | JSON to single row |
| `group_status.json` | `task_groups` | JSON to table rows |
| `security_scan.json` | `skill_outputs` | JSON to single row |
| `sessions_history.json` | `sessions` | JSON array to table rows |

---

## Performance Considerations

### WAL Mode Benefits
- **Concurrent Reads**: Multiple readers don't block each other
- **Non-blocking Reads**: Reads don't block writes (and vice versa)
- **Better Performance**: ~2-5x faster than default journal mode

### Index Usage
All high-frequency queries have supporting indexes:
- Session-based queries: `idx_logs_session`, `idx_state_session_type`, `idx_taskgroups_session`
- Time-ordered queries: Timestamps in descending order for recent data
- Filtering queries: Agent type, skill name indexes

### Connection Management
- Connection timeout: 30 seconds (handles lock contention)
- Foreign keys enabled: Ensures referential integrity
- Row factory: `sqlite3.Row` for dict-like access

---

## Backup and Maintenance

### Backup Database
```bash
sqlite3 bazinga.db ".backup bazinga_backup.db"
```

### Vacuum (Reclaim Space)
```bash
sqlite3 bazinga.db "VACUUM"
```

### Check Integrity
```bash
sqlite3 bazinga.db "PRAGMA integrity_check"
```
