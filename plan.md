# Context Availability Tracking Implementation Plan

**Date:** 2025-12-22
**Feature:** Real-time context availability monitoring during BAZINGA orchestration
**Status:** Planning

---

## Problem Statement

During BAZINGA orchestration, there's no visibility into:
1. How much context window has been consumed
2. What percentage of context remains available
3. When context is approaching limits (zone transitions)
4. Cumulative token usage across all agent spawns

**Current State:**
- `token_usage` table exists but only logs AFTER agent spawns
- Context-assembler has 5-zone detection but uses rough estimates
- No real-time tracking during orchestration flow
- Dashboard shows historical data, not live availability

---

## Proposed Solution

Add real-time context availability tracking with:
1. **New database table** for checkpoints
2. **bazinga-db skill commands** for logging/querying
3. **Orchestrator integration** to log before/after agent spawns
4. **Dashboard component** for live visualization

---

## Implementation Tasks

### Task 1: Add `context_availability` Table (Schema v16)

**File:** `.claude/skills/bazinga-db/scripts/init_db.py`

Add new table after existing tables:

```sql
CREATE TABLE IF NOT EXISTS context_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    checkpoint TEXT NOT NULL,          -- e.g., "pre_developer_spawn", "post_qa_complete"
    agent_type TEXT,                   -- agent about to spawn or just completed
    agent_id TEXT,                     -- specific agent instance
    group_id TEXT,                     -- task group context

    -- Token metrics
    estimated_used_tokens INTEGER,     -- cumulative tokens used so far
    estimated_remaining_tokens INTEGER,-- remaining in context window
    usage_percentage REAL,             -- 0.0 to 100.0

    -- Zone information
    zone TEXT,                         -- Normal/Soft_Warning/Conservative/Wrap-up/Emergency
    zone_changed INTEGER DEFAULT 0,    -- 1 if zone changed from previous checkpoint
    previous_zone TEXT,                -- zone before this checkpoint (if changed)

    -- Context window info
    model TEXT,                        -- model being used
    context_window_size INTEGER,       -- total context window for model

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_ca_session ON context_availability(session_id, timestamp DESC);
CREATE INDEX idx_ca_checkpoint ON context_availability(session_id, checkpoint);
CREATE INDEX idx_ca_zone ON context_availability(session_id, zone);
```

**Migration function:** `migrate_v15_to_v16()`
- Create table if not exists
- Add indexes
- Update SCHEMA_VERSION to 16

---

### Task 2: Add bazinga-db Commands

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

#### 2a. `log_context_availability()` method

```python
def log_context_availability(
    self,
    session_id: str,
    checkpoint: str,
    estimated_used: int,
    estimated_remaining: int,
    zone: str,
    model: str,
    context_window_size: int,
    agent_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    group_id: Optional[str] = None,
    previous_zone: Optional[str] = None
) -> int:
    """Log a context availability checkpoint.

    Returns: The ID of the inserted record.
    """
```

#### 2b. `get_context_availability()` method

```python
def get_context_availability(
    self,
    session_id: str,
    limit: int = 10
) -> List[Dict]:
    """Get recent context availability checkpoints for a session.

    Returns list of checkpoints ordered by timestamp DESC.
    """
```

#### 2c. `get_current_context_status()` method

```python
def get_current_context_status(self, session_id: str) -> Dict:
    """Get the most recent context availability status.

    Returns:
        {
            "zone": "Normal",
            "usage_percentage": 45.2,
            "estimated_remaining": 54800,
            "checkpoint": "post_developer_complete",
            "timestamp": "2025-12-22T10:30:00"
        }
    """
```

#### 2d. CLI commands

Add to command parser:
- `log-context-availability <session_id> <checkpoint> <used> <remaining> <zone> <model> <window_size> [--agent-type] [--agent-id] [--group-id] [--previous-zone]`
- `get-context-availability <session_id> [limit]`
- `current-context-status <session_id>`

---

### Task 3: Update bazinga-db Skill SKILL.md

**File:** `.claude/skills/bazinga-db/SKILL.md`

Add documentation for new commands:

```markdown
### Context Availability Tracking

#### Log Context Checkpoint
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
    log-context-availability "{session_id}" "pre_developer_spawn" \
    45000 55000 "Normal" "sonnet" 100000 \
    --agent-type developer --group-id CALC
```

#### Get Current Status
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
    current-context-status "{session_id}"
```
```

---

### Task 4: Define Context Window Sizes

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py` (or new constants file)

```python
MODEL_CONTEXT_WINDOWS = {
    "haiku": 200000,    # Claude 3.5 Haiku
    "sonnet": 200000,   # Claude 3.5/4 Sonnet
    "opus": 200000,     # Claude 4 Opus
}

ZONE_THRESHOLDS = {
    "Normal": (0, 60),
    "Soft_Warning": (60, 75),
    "Conservative": (75, 85),
    "Wrap-up": (85, 95),
    "Emergency": (95, 100),
}

def determine_zone(usage_percentage: float) -> str:
    """Determine the context zone based on usage percentage."""
    for zone, (low, high) in ZONE_THRESHOLDS.items():
        if low <= usage_percentage < high:
            return zone
    return "Emergency"  # >= 95%
```

---

### Task 5: Update Schema Reference

**File:** `.claude/skills/bazinga-db/references/schema.md`

Add documentation for the new table with:
- Column descriptions
- Usage examples
- Zone definitions
- Query patterns

---

### Task 6: Dashboard Integration (Optional - Phase 2)

**Files:**
- `dashboard-v2/src/lib/db/schema.ts` - Add Drizzle schema
- `dashboard-v2/src/types/index.ts` - Add TypeScript interfaces
- `dashboard-v2/src/lib/trpc/routers/sessions.ts` - Add queries
- New component: `dashboard-v2/src/components/context-gauge.tsx`

**Gauge Component Features:**
- Circular progress indicator showing % used
- Color-coded by zone (green→yellow→orange→red)
- Tooltip with exact numbers
- Zone label

---

## Orchestrator Integration Points

The orchestrator should log context availability at these checkpoints:

| Checkpoint | When | Purpose |
|------------|------|---------|
| `session_start` | After session creation | Baseline (0% used) |
| `pre_{agent}_spawn` | Before spawning any agent | Track pre-spawn state |
| `post_{agent}_complete` | After agent returns | Track consumption |
| `zone_transition` | When zone changes | Alert visibility |
| `session_complete` | At BAZINGA | Final state |

**Example orchestrator integration:**
```python
# Before spawning developer
db.log_context_availability(
    session_id=session_id,
    checkpoint="pre_developer_spawn",
    estimated_used=calculate_cumulative_tokens(session_id),
    estimated_remaining=context_window - estimated_used,
    zone=determine_zone(usage_pct),
    model="haiku",
    context_window_size=200000,
    agent_type="developer",
    group_id="CALC"
)
```

---

## Token Estimation Strategy

### Cumulative Calculation

```python
def calculate_cumulative_tokens(session_id: str) -> int:
    """Calculate total tokens used in session so far."""
    # Sum from token_usage table
    result = db.get_token_summary(session_id, by='agent_type')
    return sum(r['total'] for r in result)
```

### Per-Spawn Estimation

Use the existing `15000 tokens per spawn` estimate from context-assembler, or:
- Haiku responses: ~3000-5000 tokens
- Sonnet responses: ~5000-8000 tokens
- Opus responses: ~8000-15000 tokens

---

## Success Criteria

1. **Database:** `context_availability` table created with proper indexes
2. **CLI:** Three new commands working (`log-context-availability`, `get-context-availability`, `current-context-status`)
3. **Zones:** Correct zone calculation based on thresholds
4. **Visibility:** Can query current context status at any point during orchestration

---

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/bazinga-db/scripts/init_db.py` | Add table, migration v15→v16 |
| `.claude/skills/bazinga-db/scripts/bazinga_db.py` | Add methods and CLI commands |
| `.claude/skills/bazinga-db/SKILL.md` | Document new commands |
| `.claude/skills/bazinga-db/references/schema.md` | Document new table |

---

## Out of Scope (Future Work)

- Dashboard real-time visualization (Phase 2)
- Automatic context summarization when hitting Wrap-up zone
- Proactive agent context trimming
- Historical analytics across sessions

---

## Questions for Confirmation

1. **Zone thresholds** - Use existing context-assembler thresholds (60/75/85/95) or different?
2. **Context window size** - Use 200K for all Claude models or differentiate?
3. **Dashboard** - Include in this phase or defer to Phase 2?
4. **Orchestrator integration** - Should this plan include the orchestrator changes, or just the infrastructure?
