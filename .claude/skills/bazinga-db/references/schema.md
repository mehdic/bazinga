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
| `model_config` | Agent model assignments | Dynamic model selection |
| `context_packages` | Inter-agent context | Research, failures, decisions, handoffs |
| `context_package_consumers` | Consumer tracking | Join table for per-agent consumption |
| `workflow_transitions` | Deterministic routing | State machine for agent workflow |
| `agent_markers` | Prompt validation | Required markers per agent type |
| `workflow_special_rules` | Routing rules | Testing mode, escalation, security rules |

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
    initial_branch TEXT DEFAULT 'main',
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
- `initial_branch`: Base branch all work merges back to (captured at session start)
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

Stores all agent interactions and reasoning (replaces `orchestration-log.md`). Extended in schema v8 to support agent reasoning capture.

```sql
CREATE TABLE orchestration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iteration INTEGER,
    agent_type TEXT NOT NULL,
    agent_id TEXT,
    content TEXT NOT NULL,
    -- Reasoning capture columns (v8)
    log_type TEXT DEFAULT 'interaction',  -- 'interaction' or 'reasoning'
    reasoning_phase TEXT,  -- understanding, approach, decisions, risks, blockers, pivot, completion
    confidence_level TEXT,  -- high, medium, low
    references_json TEXT,  -- JSON array of files consulted
    redacted INTEGER DEFAULT 0,  -- 1 if secrets were redacted
    group_id TEXT,  -- Task group for reasoning context
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_logs_session ON orchestration_logs(session_id, timestamp DESC);
CREATE INDEX idx_logs_agent_type ON orchestration_logs(session_id, agent_type);
-- Reasoning-specific indexes (partial indexes for efficiency)
CREATE INDEX idx_logs_reasoning ON orchestration_logs(session_id, log_type, reasoning_phase)
    WHERE log_type = 'reasoning';
CREATE INDEX idx_logs_group_reasoning ON orchestration_logs(session_id, group_id, log_type)
    WHERE log_type = 'reasoning';
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `timestamp`: When the interaction occurred
- `iteration`: Orchestration iteration number
- `agent_type`: Type of agent (accepts any agent type for extensibility: `pm`, `developer`, `qa_expert`, `tech_lead`, `orchestrator`, `investigator`, `requirements_engineer`, `senior_software_engineer`, or any future agent types)
- `agent_id`: Specific agent instance (e.g., `developer_1`)
- `content`: Full agent response text or reasoning content
- `log_type`: Entry type - `interaction` (default) for normal logs, `reasoning` for reasoning capture
- `reasoning_phase`: Phase of reasoning (only for log_type='reasoning'):
  - `understanding`: Initial problem comprehension
  - `approach`: Strategy selection
  - `decisions`: Key choices made
  - `risks`: Identified risks/concerns
  - `blockers`: Issues preventing progress
  - `pivot`: Strategy changes mid-execution
  - `completion`: Final summary/outcome
- `confidence_level`: Agent's confidence in reasoning (`high`, `medium`, `low`)
- `references_json`: JSON array of file paths consulted during reasoning
- `redacted`: 1 if secrets were detected and redacted from content
- `group_id`: Task group ID for associating reasoning with specific work

**Indexes:**
- `idx_logs_session`: Fast session-based queries sorted by time
- `idx_logs_agent_type`: Filter by agent type efficiently
- `idx_logs_reasoning`: Efficient reasoning queries by phase (partial index)
- `idx_logs_group_reasoning`: Efficient reasoning queries by group (partial index)

**Usage Example - Interactions:**
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

**Usage Example - Reasoning Capture:**
```python
# Save agent reasoning (auto-redacts secrets)
result = db.save_reasoning(
    session_id='bazinga_123',
    group_id='group_a',
    agent_type='developer',
    reasoning_phase='understanding',
    content='Analyzing HIN OAuth2 requirements...',
    confidence='high',
    references=['src/auth/oauth.py', 'docs/hin-spec.md']
)

# Get reasoning entries for a group
reasoning = db.get_reasoning(
    session_id='bazinga_123',
    group_id='group_a',
    agent_type='developer',
    phase='understanding'
)

# Get full reasoning timeline
timeline = db.reasoning_timeline(
    session_id='bazinga_123',
    group_id='group_a',
    format='markdown'
)
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
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN (
        'pending', 'in_progress', 'completed', 'failed',
        'approved_pending_merge', 'merging'
    )) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
    feature_branch TEXT,
    merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
    complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
    initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
    context_references TEXT,  -- JSON array of context package IDs relevant to this group
    specializations TEXT,  -- JSON array of specialization file paths (e.g., ["bazinga/templates/specializations/01-languages/typescript.md"])
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, session_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)

-- Indexes
CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status);
```

**Columns:**
- `id`: Unique task group identifier (e.g., `group_a`)
- `session_id`: Foreign key to sessions table
- `name`: Human-readable task group name
- `status`: Current status (`pending`, `in_progress`, `completed`, `failed`, `approved_pending_merge`, `merging`)
- `assigned_to`: Agent ID assigned to this group
- `revision_count`: Number of revision cycles (for escalation)
- `last_review_status`: Tech Lead review result (APPROVED or CHANGES_REQUESTED)
- `feature_branch`: Developer's feature branch for this group (e.g., `feature/group-A-jwt-auth`)
- `merge_status`: Tracks merge state (`pending`, `in_progress`, `merged`, `conflict`, `test_failure`, NULL)
- `complexity`: Task complexity score (1-10), set by PM
- `initial_tier`: Initial implementation tier (`Developer` or `Senior Software Engineer`), set by PM
- `context_references`: JSON array of context package IDs relevant to this group (e.g., `[1, 3, 5]`)
- `specializations`: JSON array of specialization file paths assigned by PM (e.g., `["bazinga/templates/specializations/01-languages/typescript.md", "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md"]`)
- `created_at`: When task group was created
- `updated_at`: Last modification timestamp

**Status Flow (Merge-on-Approval):**
```
pending → in_progress → approved_pending_merge → merging → completed
                                             ↘ in_progress (conflict, back to dev)
```

**Merge Status Flow:**
```
NULL (not yet approved)
  ↓
pending (TL approved, waiting for merge)
  ↓
in_progress (Developer performing merge)
  ↓
merged (success)
OR conflict (git merge conflicts → dev fixes conflicts)
OR test_failure (tests failed after merge → dev fixes tests)
```

**Usage Example:**
```python
# Create task group with full PM fields
db.create_task_group(
    'group_a', 'bazinga_123', 'Authentication',
    status='pending',
    complexity=7,  # 1-3=Low (Dev), 4-6=Medium (SSE), 7-10=High (SSE)
    initial_tier='Senior Software Engineer',
    item_count=5,
    component_path='backend/auth/',
    specializations=['bazinga/templates/specializations/01-languages/typescript.md']
)

# Update task group with complexity (requires session_id for composite key)
db.update_task_group(
    'group_a', 'bazinga_123',
    status='completed',
    complexity=5,
    last_review_status='APPROVED',
    specializations=['bazinga/templates/specializations/03-frameworks-backend/express.md']
)

# Get task groups (includes specializations, complexity, initial_tier)
groups = db.get_task_groups('bazinga_123', status='in_progress')
# Returns: [{'id': 'group_a', 'complexity': 7, 'initial_tier': 'Senior Software Engineer', ...}]
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

### model_config

Stores agent model assignments for dynamic model selection.

```sql
CREATE TABLE model_config (
    agent_role TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    rationale TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Default data (keep in sync with bazinga/model_selection.json)
INSERT INTO model_config (agent_role, model, rationale) VALUES
    ('developer', 'sonnet', 'Balanced capability for implementation tasks'),
    ('senior_software_engineer', 'opus', 'Complex failures requiring deep reasoning'),
    ('qa_expert', 'sonnet', 'Test generation and validation'),
    ('tech_lead', 'opus', 'Architectural decisions - non-negotiable'),
    ('project_manager', 'opus', 'Strategic planning - non-negotiable'),
    ('investigator', 'opus', 'Root cause analysis'),
    ('validator', 'sonnet', 'BAZINGA verification');
```

**Columns:**
- `agent_role`: Agent role identifier (primary key)
- `model`: Model name (e.g., `haiku`, `sonnet`, `opus`)
- `rationale`: Explanation for model choice
- `updated_at`: Last update timestamp

**Usage Example:**
```python
# Get all model assignments
models = db.get_model_config()
# Returns: {'developer': 'sonnet', 'senior_software_engineer': 'opus', ...}

# Get model for specific agent (before update)
model = db.get_agent_model('developer')
# Returns: 'sonnet'

# Update model for an agent
db.set_model_config('developer', 'opus', 'Upgrading for complex project')

# Get model after update
model = db.get_agent_model('developer')
# Returns: 'opus'
```

**Why This Table:**
- Allows runtime model updates without code changes
- Future-proof for new model releases (Claude 4, etc.)
- Single source of truth for model assignments
- Orchestrator queries this at initialization

---

### context_packages

Stores context packages for inter-agent communication (research, failures, decisions, handoffs).

```sql
CREATE TABLE context_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT,  -- NULL for global/session-wide packages
    package_type TEXT NOT NULL CHECK(package_type IN ('research', 'failures', 'decisions', 'handoff', 'investigation')),
    file_path TEXT NOT NULL,
    producer_agent TEXT NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    summary TEXT NOT NULL,  -- Brief description for routing (max 200 chars)
    size_bytes INTEGER,  -- File size for budget decisions
    version INTEGER DEFAULT 1,
    supersedes_id INTEGER,  -- Previous version if updated
    scope TEXT DEFAULT 'group' CHECK(scope IN ('group', 'global')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (supersedes_id) REFERENCES context_packages(id)
)

-- Indexes
CREATE INDEX idx_cp_session ON context_packages(session_id);
CREATE INDEX idx_cp_group ON context_packages(group_id);
CREATE INDEX idx_cp_type ON context_packages(package_type);
CREATE INDEX idx_cp_priority ON context_packages(priority);
CREATE INDEX idx_cp_scope ON context_packages(scope);
```

**Columns:**
- `id`: Auto-increment primary key
- `session_id`: Foreign key to sessions table
- `group_id`: Task group ID (NULL for global packages)
- `package_type`: Type of context (`research`, `failures`, `decisions`, `handoff`, `investigation`)
- `file_path`: Path to the context package markdown file
- `producer_agent`: Agent that created the package
- `priority`: Routing priority (`low`, `medium`, `high`, `critical`)
- `summary`: Brief description for spawn prompts (max 200 chars)
- `size_bytes`: File size for token budget decisions
- `version`: Package version (incremented on updates)
- `supersedes_id`: Reference to previous version if updated
- `scope`: Whether package is group-specific or session-wide
- `created_at`: When package was created

**Usage Example:**
```python
# Create context package
db.save_context_package(
    session_id='bazinga_123',
    group_id='group_a',
    package_type='research',
    file_path='bazinga/artifacts/bazinga_123/context/research-group_a-hin.md',
    producer_agent='requirements_engineer',
    consumers=['developer', 'senior_software_engineer'],
    priority='high',
    summary='HIN OAuth2 endpoints, scopes, security requirements'
)

# Get packages for agent spawn
packages = db.get_context_packages(
    session_id='bazinga_123',
    group_id='group_a',
    agent_type='developer',
    limit=3
)
```

---

### context_package_consumers

Join table for tracking per-agent consumption of context packages.

```sql
CREATE TABLE context_package_consumers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    agent_type TEXT NOT NULL,
    consumed_at TIMESTAMP,  -- NULL = not yet consumed
    iteration INTEGER DEFAULT 1,  -- Which iteration of the agent consumed it
    FOREIGN KEY (package_id) REFERENCES context_packages(id) ON DELETE CASCADE,
    UNIQUE(package_id, agent_type, iteration)
)

-- Indexes
CREATE INDEX idx_cpc_package ON context_package_consumers(package_id);
CREATE INDEX idx_cpc_agent ON context_package_consumers(agent_type);
CREATE INDEX idx_cpc_pending ON context_package_consumers(consumed_at) WHERE consumed_at IS NULL;
```

**Columns:**
- `id`: Auto-increment primary key
- `package_id`: Foreign key to context_packages table
- `agent_type`: Type of agent that can consume (`developer`, `qa_expert`, etc.)
- `consumed_at`: When the package was consumed (NULL if pending)
- `iteration`: Which iteration of the agent consumed it (allows re-consumption)

**Usage Example:**
```python
# Mark package as consumed
db.mark_context_consumed(
    package_id=1,
    agent_type='developer',
    iteration=2
)

# Get pending packages for agent
pending = db.get_pending_context(
    session_id='bazinga_123',
    agent_type='developer',
    group_id='group_a'
)
```

**Why Join Table (Not JSON Array):**
- Proper indexing for efficient lookups
- Per-consumer tracking (multiple agents can consume same package)
- Supports iteration-based re-consumption
- Clean queries without string pattern matching

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

---

## Deterministic Orchestration Tables (v13)

These tables support the deterministic prompt building and workflow routing system.

### workflow_transitions

Stores state machine transitions for deterministic workflow routing. Seeded from `workflow/transitions.json` at session start.

```sql
CREATE TABLE workflow_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_agent TEXT NOT NULL,
    response_status TEXT NOT NULL,
    next_agent TEXT,
    action TEXT NOT NULL,
    include_context TEXT,  -- JSON array of context types to include
    escalation_check INTEGER DEFAULT 0,  -- 1 to check revision count for escalation
    model_override TEXT,  -- Override model for next agent
    fallback_agent TEXT,  -- Fallback if primary agent unavailable
    bypass_qa INTEGER DEFAULT 0,  -- 1 to skip QA (e.g., RE tasks)
    max_parallel INTEGER,  -- Max parallel spawns for batch actions
    then_action TEXT,  -- Action after primary (e.g., 'check_phase')
    UNIQUE(current_agent, response_status)
)

-- Indexes
CREATE INDEX idx_wt_agent ON workflow_transitions(current_agent);
```

**Columns:**
- `current_agent`: Agent that produced the response (developer, qa_expert, tech_lead, etc.)
- `response_status`: Status code from agent (READY_FOR_QA, PASS, APPROVED, etc.)
- `next_agent`: Agent to spawn next (NULL for end states)
- `action`: Action type (`spawn`, `respawn`, `spawn_batch`, `validate_then_end`, `pause_for_user`, `end_session`)
- `include_context`: JSON array of context types to pass (e.g., `["dev_output", "test_results"]`)
- `escalation_check`: If 1, check revision_count against escalation threshold
- `model_override`: Override model (e.g., `opus` for escalation)
- `fallback_agent`: Alternative agent if primary unavailable
- `bypass_qa`: If 1, skip QA Expert (for RE tasks)
- `max_parallel`: Maximum parallel spawns for `spawn_batch`
- `then_action`: Secondary action (e.g., `check_phase` after merge)

**Usage Example:**
```python
# Get next transition (called by workflow_router.py)
transition = db.get_transition('developer', 'READY_FOR_QA')
# Returns: {'next_agent': 'qa_expert', 'action': 'spawn', ...}
```

---

### agent_markers

Stores required markers that MUST be present in agent prompts. Seeded from `workflow/agent-markers.json` at session start.

```sql
CREATE TABLE agent_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL UNIQUE,
    required_markers TEXT NOT NULL,  -- JSON array of required strings
    workflow_markers TEXT  -- JSON array of workflow-related strings
)
```

**Columns:**
- `agent_type`: Type of agent (developer, qa_expert, tech_lead, etc.)
- `required_markers`: JSON array of strings that MUST appear in prompt
- `workflow_markers`: JSON array of workflow-related strings (informational)

**Usage Example:**
```python
# Get markers for validation (called by prompt_builder.py)
markers = db.get_markers('developer')
# Returns: {'required': ['NO DELEGATION', 'READY_FOR_QA', ...], 'workflow': [...]}

# Validate prompt contains all markers
missing = [m for m in markers['required'] if m not in prompt]
if missing:
    raise ValueError(f"Prompt missing markers: {missing}")
```

---

### workflow_special_rules

Stores special routing rules (testing mode, escalation, security). Seeded from `transitions.json` `_special_rules` at session start.

```sql
CREATE TABLE workflow_special_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    description TEXT,
    config TEXT NOT NULL  -- JSON object with rule configuration
)
```

**Columns:**
- `rule_name`: Unique rule identifier (e.g., `testing_mode_disabled`, `escalation_after_failures`)
- `description`: Human-readable description
- `config`: JSON object with rule-specific configuration

**Usage Example:**
```python
# Get escalation rule (called by workflow_router.py)
rule = db.get_special_rule('escalation_after_failures')
# Returns: {'threshold': 2, 'escalation_agent': 'senior_software_engineer'}

# Check if escalation needed
if revision_count >= rule['threshold']:
    next_agent = rule['escalation_agent']
```

**Available Rules:**
- `testing_mode_disabled`: Skip QA entirely when testing is disabled
- `testing_mode_minimal`: Skip QA Expert when testing is minimal
- `escalation_after_failures`: Escalate to SSE after N failures
- `security_sensitive`: Force SSE + mandatory TL review for security tasks
- `research_tasks`: Route to RE with limited parallelism
