# Reasoning Consumption and Skill Output Schema Analysis

**Date:** 2025-12-14
**Context:** Integration test revealed reasoning is write-only and skill outputs overwrite
**Decision:** See revised implementation plan below
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

Two related gaps discovered during integration test verification:

### Issue 1: Skill Output Schema Overwrites

**Current behavior:**
- `save-skill-output` stores single JSON blob per (session_id, skill_name)
- Each save overwrites the previous
- Lost 2 of 3 specialization-loader outputs (only last one persisted)

**Desired behavior:**
- Capture every skill invocation
- Support same skill invoked by same agent multiple times (e.g., retry scenarios)

### Issue 2: Reasoning is Write-Only

**Current behavior:**
- Agents save reasoning via `save-reasoning` command ✅
- No agent retrieves reasoning via `get-reasoning` ❌
- Orchestrator doesn't query reasoning before spawning agents ❌
- Each agent starts "fresh" without prior agent's context

**Designed behavior (never implemented):**
- Reasoning passed between agents in workflow handoffs
- Tech Lead reviews Developer's reasoning before code review
- QA Expert sees Developer's decisions for testing context
- SSE receives Developer's reasoning on escalation
- Investigator analyzes full reasoning timeline for root cause

---

## Analysis

### Issue 1: Skill Output Schema

**Root cause:** Table designed for single-output skills, not multi-invocation skills.

**Affected skills:**
- `specialization-loader` - invoked 3+ times per session (once per agent type)
- `codebase-analysis` - may be invoked multiple times by same agent
- `test-coverage` - invoked before/after fixes
- Any skill with retry logic

**Proposed schema change:**

```sql
-- Option A: Add unique key columns
CREATE TABLE skill_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    agent_type TEXT,           -- NEW: Which agent invoked
    group_id TEXT,             -- NEW: Which task group
    iteration INTEGER DEFAULT 1, -- NEW: Invocation count
    output_data TEXT,          -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Query all invocations
SELECT * FROM skill_outputs WHERE session_id = ? AND skill_name = ?;

-- Query specific agent's invocations
SELECT * FROM skill_outputs
WHERE session_id = ? AND skill_name = ? AND agent_type = ?;

-- Query latest per agent
SELECT * FROM skill_outputs
WHERE session_id = ? AND skill_name = ?
GROUP BY agent_type
HAVING MAX(created_at);
```

**Option B: Keep single row, store array**

```sql
-- Each save appends to invocations array
{
  "invocations": [
    {"agent_type": "developer", "group_id": "CALC", "iteration": 1, "data": {...}, "timestamp": "..."},
    {"agent_type": "qa_expert", "group_id": "CALC", "iteration": 1, "data": {...}, "timestamp": "..."},
    {"agent_type": "tech_lead", "group_id": "CALC", "iteration": 1, "data": {...}, "timestamp": "..."}
  ]
}
```

**Recommendation: Option A (multiple rows)**
- Cleaner SQL queries
- No JSON parsing for simple lookups
- Better for concurrent writes (no read-modify-write)
- Standard relational pattern

### Issue 2: Reasoning Consumption

**Current flow (broken):**
```
Developer saves reasoning → DB → (nothing reads it) → QA starts fresh
QA saves reasoning → DB → (nothing reads it) → Tech Lead starts fresh
```

**Intended flow (never implemented):**
```
Developer saves reasoning → DB
                            ↓
Orchestrator queries → get-reasoning(session, CALC, developer)
                            ↓
Orchestrator includes in QA spawn prompt → "Prior agent reasoning: {...}"
                            ↓
QA reads Developer's reasoning → informed testing
```

**Where to implement reasoning retrieval:**

1. **Orchestrator (before each spawn):**
   ```markdown
   ## Before spawning QA Expert

   1. Query prior agent's reasoning:
      ```bash
      python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
        get-reasoning "{session_id}" --group_id "{group_id}" --agent_type "developer"
      ```

   2. Include in QA spawn prompt:
      ```markdown
      ## Prior Agent Reasoning

      The Developer documented the following reasoning:

      ### Understanding
      {developer_understanding}

      ### Completion Summary
      {developer_completion}
      ```
   ```

2. **Agent prompts (retrieval step):**
   ```markdown
   ## Step 1: Retrieve Prior Reasoning (if exists)

   Check if prior agent left reasoning for this task group:
   ```bash
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
     get-reasoning "{session_id}" --group_id "{group_id}"
   ```

   If found, incorporate into your understanding.
   ```

**Decision: Where should retrieval happen?**

| Option | Pros | Cons |
|--------|------|------|
| Orchestrator retrieves & passes | Centralized, guaranteed delivery | Orchestrator prompt grows, more complexity |
| Agent retrieves on startup | Agent has full control | Agent may skip, inconsistent |
| Both | Maximum reliability | Redundant, token waste |

**Recommendation: Orchestrator retrieves & passes**
- Single point of enforcement
- Agents don't need to learn retrieval patterns
- Orchestrator already queries DB for task groups
- Natural extension of existing workflow

---

## Implementation Plan

### Phase 1: Fix Skill Output Schema

**Step 1.1: Update bazinga_db.py**

Modify `save-skill-output` to INSERT (not upsert):
```python
def save_skill_output(session_id, skill_name, output_data, agent_type=None, group_id=None, iteration=1):
    # INSERT new row (never overwrite)
    cursor.execute("""
        INSERT INTO skill_outputs (session_id, skill_name, agent_type, group_id, iteration, output_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, skill_name, agent_type, group_id, iteration, json.dumps(output_data)))
```

**Step 1.2: Update get-skill-output**

Return array of all matching invocations:
```python
def get_skill_output(session_id, skill_name, agent_type=None, group_id=None):
    query = "SELECT * FROM skill_outputs WHERE session_id = ? AND skill_name = ?"
    params = [session_id, skill_name]

    if agent_type:
        query += " AND agent_type = ?"
        params.append(agent_type)
    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)

    return cursor.fetchall()  # Array, not single object
```

**Step 1.3: Schema migration**

Add columns to existing table (backward compatible):
```sql
ALTER TABLE skill_outputs ADD COLUMN agent_type TEXT;
ALTER TABLE skill_outputs ADD COLUMN group_id TEXT;
ALTER TABLE skill_outputs ADD COLUMN iteration INTEGER DEFAULT 1;
```

### Phase 2: Wire Reasoning Consumption

**Step 2.1: Add reasoning retrieval to orchestrator**

In `agents/orchestrator.md`, before each agent spawn:

```markdown
### Step X.Y: Retrieve Prior Reasoning for {Agent}

Before spawning {Agent}, query reasoning from prior agents in this task group:

```bash
# Get all reasoning for this task group
PRIOR_REASONING=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
  get-reasoning "{session_id}" --group_id "{group_id}" --format markdown)
```

If reasoning exists, include in spawn prompt:

```markdown
## Context from Prior Agents

{PRIOR_REASONING}

Use this context to inform your work. Key points:
- Developer's understanding of requirements
- Decisions made and rationale
- Any risks or blockers identified
```
```

**Step 2.2: Define reasoning handoff matrix**

| Spawning | Prior Agents to Query | What to Include |
|----------|----------------------|-----------------|
| QA Expert | Developer | understanding, completion, decisions |
| Tech Lead | Developer, QA Expert | all phases from both |
| SSE (escalation) | Developer | all phases (critical for context) |
| PM (completion) | All agents | completion summaries only |

**Step 2.3: Update agent prompts**

Add "Prior Reasoning" section to agent prompt templates:

```markdown
## Prior Agent Reasoning (Read-Only Context)

The following reasoning was documented by prior agents on this task:

{prior_reasoning_markdown}

Use this context to:
- Understand what was attempted
- Avoid repeating same mistakes
- Build on decisions already made
- Understand constraints identified
```

### Phase 3: Verification

**Step 3.1: Update integration test verification**

```bash
# Verify reasoning was retrieved AND passed
# Check orchestration logs for "Prior Reasoning" keyword
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
  stream-logs "{session_id}" --search "Prior Reasoning"

# Should find entries like:
# "QA Expert spawn included prior reasoning from Developer"
# "Tech Lead spawn included prior reasoning from Developer, QA Expert"
```

**Step 3.2: Add traceability**

Log when reasoning is retrieved and passed:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-event \
  "{session_id}" "reasoning_handoff" '{
    "from_agent": "developer",
    "to_agent": "qa_expert",
    "phases_passed": ["understanding", "completion"],
    "content_length": 1234
  }'
```

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Schema migration breaks existing data | LOW | ALTER TABLE is additive, no data loss |
| Token budget exceeded by prior reasoning | MEDIUM | Truncate to last 500 chars per phase |
| Orchestrator prompt too large | MEDIUM | Only include completion phase by default |
| Agents ignore prior reasoning | LOW | Make it "Prior Context" not optional |
| Performance (extra DB queries) | LOW | Single query per spawn, cached |

---

## Comparison to Alternatives

### Alternative 1: Context Packages for Reasoning

Use existing context_packages table instead of reasoning_log.

**Rejected because:**
- Context packages are for artifacts (files, summaries)
- Reasoning is meta-information about decision process
- Different consumption patterns (packages are optional, reasoning should flow automatically)

### Alternative 2: File-Based Reasoning

Write reasoning to `bazinga/artifacts/{session}/reasoning/*.md`

**Rejected because:**
- DB provides better querying (by agent, by phase)
- Files require more orchestrator logic to manage
- DB already exists and works for reasoning storage

### Alternative 3: No Reasoning Handoff

Keep reasoning write-only, just for audit trail.

**Rejected because:**
- Defeats purpose of capturing reasoning
- Agents repeat work without prior context
- Escalations (Dev→SSE) lose critical information
- Tech Lead can't understand Developer's decisions

---

## Critical Analysis

### Pros ✅

1. **Complete audit trail** - All skill invocations captured, not just last one
2. **Informed agents** - QA knows what Developer intended, not just what code exists
3. **Better escalations** - SSE receives full context from failed Developer
4. **Reduced re-work** - Agents build on prior reasoning, not starting fresh
5. **Debugging value** - Can trace decision flow through session

### Cons ⚠️

1. **Increased complexity** - Orchestrator has more steps
2. **Token usage** - Prior reasoning consumes prompt space
3. **Migration needed** - Schema change for skill_outputs
4. **More DB queries** - One extra query per spawn

### Verdict

The benefits significantly outweigh the costs. The reasoning system was designed for agent-to-agent communication but only the "write" side was implemented. Completing the "read" side is essential for the system to work as intended.

Without reasoning handoff:
- ❌ Each agent starts fresh
- ❌ Decisions not propagated
- ❌ Escalations lose context
- ❌ Audit trail exists but unused

With reasoning handoff:
- ✅ Continuous context flow
- ✅ Decisions inform subsequent work
- ✅ Escalations retain full history
- ✅ Audit trail actively used

---

## Decision Rationale

1. **Skill outputs should never overwrite** - Multiple invocations = multiple rows
2. **Reasoning should flow downstream** - Orchestrator retrieves and includes in spawn
3. **Keep it simple** - Orchestrator handles retrieval, not agents
4. **Truncate if needed** - Token budget > completeness for reasoning handoff

---

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/bazinga-db/scripts/bazinga_db.py` | Add agent_type/group_id/iteration to save-skill-output, return array from get-skill-output |
| `agents/orchestrator.md` | Add reasoning retrieval before each agent spawn |
| `.claude/commands/bazinga.orchestrate.md` | Regenerate from orchestrator.md |
| `.claude/claude.md` | Update verification to check reasoning handoff |

---

## Multi-LLM Review Integration

### Critical Issues Identified by OpenAI

| Issue | Severity | Resolution |
|-------|----------|------------|
| Orchestrator uses direct python/bash (violates tool policy) | CRITICAL | Use `Skill(command: "bazinga-db")` instead |
| get-skill-output breaking change (array vs object) | HIGH | Add new `get-latest-skill-output` command, keep existing |
| Iteration handling (caller-provided = race conditions) | MEDIUM | Compute server-side atomically |
| Token budget risk (reasoning bloats prompts) | MEDIUM | Cap at 1200-1600 tokens, prioritize completion phase |
| No migration/versioning strategy | MEDIUM | Add PRAGMA user_version + migrate-schema command |
| Missing indexes for performance | LOW | Add composite indexes |

### Key Architecture Decision: Context-Assembler for Reasoning

**Original proposal:** Orchestrator retrieves reasoning via bazinga-db, injects into spawn prompts

**OpenAI suggestion:** Use context-assembler skill instead

**Decision:** **Accept OpenAI suggestion** ✅

**Rationale:**
1. Context-assembler already handles token budgeting
2. Centralizes summarization logic (not scattered in orchestrator)
3. Consistent with existing context package flow
4. Orchestrator stays simple (just invokes skill)

### Revised Implementation Plan

#### Phase 1: Fix Skill Output Schema (No Breaking Changes)

**1.1 Add new columns (backward compatible):**
```sql
ALTER TABLE skill_outputs ADD COLUMN agent_type TEXT;
ALTER TABLE skill_outputs ADD COLUMN group_id TEXT;
ALTER TABLE skill_outputs ADD COLUMN iteration INTEGER DEFAULT 1;

CREATE INDEX idx_skill_outputs_lookup
ON skill_outputs(session_id, skill_name, agent_type, created_at);
```

**1.2 Add new commands (keep existing):**
- `save-skill-output` - Modified to compute iteration server-side
- `get-latest-skill-output` - Returns single object (for existing verification)
- `get-skill-output-all` - Returns array of all invocations

**1.3 Update save-skill-output:**
```python
# Compute iteration atomically
cursor.execute("""
    SELECT COALESCE(MAX(iteration), 0) + 1
    FROM skill_outputs
    WHERE session_id = ? AND skill_name = ?
      AND (agent_type IS ? OR (? IS NULL AND agent_type IS NULL))
      AND (group_id IS ? OR (? IS NULL AND group_id IS NULL))
""", (session_id, skill_name, agent_type, agent_type, group_id, group_id))
next_iteration = cursor.fetchone()[0]

# Insert new row
cursor.execute("""
    INSERT INTO skill_outputs (session_id, skill_name, agent_type, group_id, iteration, output_data)
    VALUES (?, ?, ?, ?, ?, ?)
""", (session_id, skill_name, agent_type, group_id, next_iteration, json.dumps(output_data)))
```

#### Phase 2: Wire Reasoning via Context-Assembler

**2.1 Add reasoning retrieval to context-assembler SKILL.md:**
```markdown
### Step 3.5: Include Prior Reasoning (Optional)

If orchestrator context includes `include_reasoning: true`:

1. Query prior agent reasoning:
   ```bash
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
     get-reasoning "{session_id}" --group_id "{group_id}" --limit 3
   ```

2. Summarize to fit token budget:
   - Max 1200 tokens for reasoning digest
   - Priority: completion > decisions > understanding
   - Truncate each phase to 400 chars if needed

3. Include in output block:
   ```markdown
   ## Prior Agent Reasoning

   ### Developer (completion)
   {truncated_completion_summary}

   ### Developer (decisions)
   {truncated_decisions_if_room}
   ```
```

**2.2 Orchestrator invokes context-assembler with flag:**

In orchestrator.md, before spawning QA/TL:
```markdown
**Step X: Gather Context for {Agent}**

Skill(command: "context-assembler")

With context:
- Session ID: {session_id}
- Group ID: {group_id}
- Agent Type: {target_agent}
- Include Reasoning: true  ← NEW FLAG
```

**2.3 Token budget enforcement:**
| Component | Max Tokens |
|-----------|------------|
| Specialization block | 900-2400 (per model) |
| Reasoning digest | 1200 |
| Context packages | Remaining budget |

#### Phase 3: Migration Strategy

**3.1 Add schema versioning:**
```python
def get_schema_version():
    cursor.execute("PRAGMA user_version")
    return cursor.fetchone()[0]

def migrate_schema():
    version = get_schema_version()

    if version < 1:
        # V1: Add skill_outputs columns
        cursor.execute("ALTER TABLE skill_outputs ADD COLUMN agent_type TEXT")
        cursor.execute("ALTER TABLE skill_outputs ADD COLUMN group_id TEXT")
        cursor.execute("ALTER TABLE skill_outputs ADD COLUMN iteration INTEGER DEFAULT 1")
        cursor.execute("PRAGMA user_version = 1")
```

**3.2 Auto-migrate on first access:**
```python
def ensure_db_ready():
    if get_schema_version() < CURRENT_VERSION:
        migrate_schema()
```

### Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/bazinga-db/scripts/bazinga_db.py` | Add columns, new commands, server-side iteration |
| `.claude/skills/context-assembler/SKILL.md` | Add reasoning retrieval step |
| `agents/orchestrator.md` | Add `include_reasoning: true` to context-assembler calls |

### Rejected Suggestions

| Suggestion | Rejection Reason |
|------------|------------------|
| Store reasoning as context packages | Different table, different consumption pattern |
| Add group_id foreign key | Requires table rebuild, complexity not justified |
| Dedupe mechanism for reasoning | Over-engineering; token budget handles redundancy |

### Risk Assessment (Post-Review)

| Risk | Mitigation |
|------|------------|
| Breaking existing verification | `get-latest-skill-output` preserves single-object shape |
| Token budget exceeded | Context-assembler enforces caps |
| Migration fails mid-session | Auto-migrate on first access, additive changes only |
| Performance regression | Composite indexes added |

**Confidence Level:** MEDIUM-HIGH - After incorporating OpenAI feedback, approach is robust.

---

## References

- Integration test session `bazinga_20251214_124946`
- `research/reasoning-and-skill-output-gaps.md` - Prior analysis
- `research/inter-agent-communication-design.md` - Original design intent
- `specs/1-context-engineering/spec.md` - Context engineering spec
- `tmp/ultrathink-reviews/openai-review.md` - External LLM review
