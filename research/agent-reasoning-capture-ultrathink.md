# Agent Reasoning Capture Strategy

**Date:** 2025-12-08
**Context:** Need to capture subagent reasoning/thinking for debugging and audit trails
**Decision:** Implement prompt-based reasoning documentation with database storage
**Status:** Reviewed - Ready for Implementation
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

Claude Code subagents operate with isolated context windows. Their internal "thinking" blocks (extended thinking) are:
1. **Not visible** to the parent orchestrator
2. **Not streamed** in real-time
3. **Not persisted** after agent completion
4. **Not queryable** for debugging

This creates challenges for:
- **Debugging** - When agents fail, we can't see their reasoning
- **Audit trails** - No record of why decisions were made
- **Learning** - Can't improve prompts without understanding failures
- **Transparency** - Users can't understand agent behavior

### Current Situation

| Capability | Available? |
|------------|------------|
| See agent tool calls | ✅ Yes |
| See agent text output | ✅ Yes |
| See agent thinking blocks | ❌ No |
| Query agent reasoning | ❌ No |
| Persist reasoning across sessions | ❌ No |

### Why This Matters for BAZINGA

In BAZINGA orchestration:
- **4 parallel developers** may each make different architectural decisions
- **QA failures** need root cause analysis
- **Tech Lead reviews** benefit from understanding developer reasoning
- **PM decisions** should be traceable for audit
- **Escalation paths** (Developer → SSE) lose context on handoff

---

## Approved Solution

### Core Approach: Prompt-Injected Reasoning Documentation

Agents **explicitly document their reasoning** as structured output saved to the database via CLI commands. This is **MANDATORY** for all agents.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Prompt (Modified)                   │
│                                                              │
│  ## Reasoning Documentation Requirement (MANDATORY)          │
│  Before implementing, document your analysis:                │
│  1. Save reasoning to database via bazinga-db CLI            │
│  2. Include: understanding, approach, risks, decisions       │
│  3. Update when approach changes significantly               │
│  4. All 7 phases available, minimum 2 required               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    bazinga-db Skill                          │
│                                                              │
│  EXTENDED: orchestration_logs table                          │
│  - NEW log_type: 'reasoning'                                 │
│  - NEW reasoning_phase column                                │
│  - Secret scanning/redaction before storage                  │
│  - Retry with exponential backoff                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│                                                              │
│  EXTENDED: orchestration_logs table                          │
│  - Full reasoning text stored (DB is source of truth)        │
│  - Indexed by session_id, group_id, agent_type, phase        │
│  - Queryable by orchestrator, PM, Tech Lead                  │
│  - Persists across compactions                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. Extended Database Schema: `orchestration_logs`

Extend the existing `orchestration_logs` table instead of creating a new table:

```sql
-- Add new columns to existing orchestration_logs table
ALTER TABLE orchestration_logs ADD COLUMN log_type TEXT DEFAULT 'interaction'
    CHECK(log_type IN ('interaction', 'reasoning'));

ALTER TABLE orchestration_logs ADD COLUMN reasoning_phase TEXT
    CHECK(reasoning_phase IS NULL OR reasoning_phase IN (
        'understanding',  -- Initial task comprehension
        'approach',       -- Planned solution strategy
        'decisions',      -- Key architectural/implementation decisions
        'risks',          -- Identified risks and mitigations
        'blockers',       -- What's blocking progress
        'pivot',          -- Why approach changed mid-task
        'completion'      -- Final summary of what was done and why
    ));

ALTER TABLE orchestration_logs ADD COLUMN confidence_level TEXT
    CHECK(confidence_level IS NULL OR confidence_level IN ('high', 'medium', 'low'));

ALTER TABLE orchestration_logs ADD COLUMN references_json TEXT;  -- JSON array of file paths consulted

ALTER TABLE orchestration_logs ADD COLUMN redacted INTEGER DEFAULT 0;  -- 1 if secrets were redacted

-- Add index for reasoning queries
CREATE INDEX idx_logs_reasoning ON orchestration_logs(session_id, log_type, reasoning_phase)
    WHERE log_type = 'reasoning';
```

**Why extend existing table:**
- Simpler schema, fewer migrations
- Reuses existing indexes and connections
- Single source for all agent activity
- Easier dashboard integration

### 2. Secret Scanning/Redaction

Before storing reasoning, scan and redact sensitive content:

```python
import re

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', 'API_KEY_REDACTED'),
    (r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']+)["\']?', 'SECRET_REDACTED'),
    (r'(?i)(token|bearer)\s*[=:]\s*["\']?([a-zA-Z0-9_.-]{20,})["\']?', 'TOKEN_REDACTED'),
    (r'sk-[a-zA-Z0-9]{20,}', 'OPENAI_KEY_REDACTED'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN_REDACTED'),
    (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', 'PRIVATE_KEY_REDACTED'),
]

def scan_and_redact(text: str) -> tuple[str, bool]:
    """Scan text for secrets and redact them.

    Returns:
        (redacted_text, was_redacted)
    """
    redacted = False
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        if re.search(pattern, result):
            result = re.sub(pattern, replacement, result)
            redacted = True
    return result, redacted
```

### 3. Retry with Exponential Backoff

Add to BazingaDB class for all write operations:

```python
def save_reasoning(self, session_id: str, group_id: str, agent_type: str,
                   reasoning_phase: str, reasoning_text: str,
                   agent_id: str = None, iteration: int = 1,
                   confidence: str = None, references: list = None,
                   _retry_count: int = 0) -> Dict[str, Any]:
    """Save agent reasoning with secret scanning and retry logic."""

    # Prevent infinite recursion
    if _retry_count > 3:
        return {"success": False, "error": "Max retries exceeded"}

    # Scan and redact secrets
    redacted_text, was_redacted = scan_and_redact(reasoning_text)

    try:
        conn = self._get_connection()
        cursor = conn.execute("""
            INSERT INTO orchestration_logs
            (session_id, agent_type, agent_id, iteration, content,
             log_type, reasoning_phase, confidence_level, references_json, redacted)
            VALUES (?, ?, ?, ?, ?, 'reasoning', ?, ?, ?, ?)
        """, (session_id, agent_type, agent_id, iteration, redacted_text,
              reasoning_phase, confidence,
              json.dumps(references) if references else None,
              1 if was_redacted else 0))
        conn.commit()
        # ... verification and return

    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower() and _retry_count < 3:
            wait_time = 2 ** _retry_count  # 1s, 2s, 4s
            time.sleep(wait_time)
            return self.save_reasoning(
                session_id, group_id, agent_type, reasoning_phase, reasoning_text,
                agent_id, iteration, confidence, references,
                _retry_count=_retry_count + 1
            )
        raise
```

### 4. New bazinga-db CLI Commands

```bash
# Save reasoning (with automatic secret scanning)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "<session_id>" "<group_id>" "<agent_type>" "<reasoning_phase>" "<reasoning_text>" \
  [--agent_id X] [--iteration N] [--confidence high|medium|low] [--references '["file1","file2"]']

# Get reasoning for a group (for handoffs)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-reasoning \
  "<session_id>" "<group_id>" [--agent_type X] [--phase Y] [--limit N]

# Get reasoning timeline (for debugging)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet reasoning-timeline \
  "<session_id>" [--group_id X] [--format markdown|json]
```

### 5. Agent Prompt Injection (MANDATORY for ALL agents)

Add to **ALL agent prompts** (developer, senior_software_engineer, qa_expert, techlead, project_manager, investigator, requirements_engineer):

```markdown
## 🧠 Reasoning Documentation Requirement (MANDATORY)

**CRITICAL**: You MUST document your reasoning. This is NOT optional.

### Required Reasoning Phases

| Phase | When | What to Document |
|-------|------|-----------------|
| understanding | **REQUIRED** at task start | Your interpretation of requirements, what's unclear |
| approach | After analysis | Your planned solution, why this approach |
| decisions | During implementation | Key choices made, alternatives considered |
| risks | If identified | What could go wrong, mitigations |
| blockers | If stuck | What's blocking, what you tried |
| pivot | If changing approach | Why original approach didn't work |
| completion | **REQUIRED** at task end | Summary of what was done and key learnings |

**Minimum requirement:** `understanding` at start + `completion` at end

### How to Save Reasoning

```bash
# Save via bazinga-db CLI (secrets automatically redacted)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "{AGENT_TYPE}" "approach" \
  "## Approach

### Chosen Strategy
Implementing JWT auth using PyJWT library with HS256.

### Why This Approach
1. Project already uses Flask - PyJWT integrates cleanly
2. HS256 is sufficient for internal API (no third-party verification needed)
3. Follows existing patterns in auth_utils.py

### Alternatives Considered
- RS256: Overkill for internal API, requires key management
- Session-based: Doesn't align with stateless API design
- OAuth2: Too complex for MVP, consider for v2

### Dependencies
- PyJWT >= 2.0.0
- cryptography (for future RS256 support)" \
  --confidence high \
  --references '["src/utils/auth.py", "requirements.txt"]'
```

### Why This Matters

Your reasoning is:
- **Queryable** by PM/Tech Lead for reviews
- **Passed** to next agent in workflow (handoffs)
- **Preserved** across context compactions
- **Available** for debugging failures
- **Used** by Investigator for root cause analysis
- **Secrets automatically redacted** before storage
```

### 6. Integration Points

#### A. Orchestrator Spawn Enhancement

When spawning agents, orchestrator queries previous reasoning:

```python
# Get reasoning from previous agents for context
previous_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    limit=5
)

# Include in agent spawn prompt
spawn_prompt += f"""
## Previous Agent Reasoning (for context)
{format_reasoning(previous_reasoning)}
"""
```

#### B. Tech Lead Review Enhancement

Tech Lead reviews developer reasoning before code review:

```python
# Tech Lead queries developer reasoning
dev_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    agent_type='developer'
)

# Inform code review with reasoning context
review_prompt += f"""
## Developer's Documented Reasoning
{format_reasoning(dev_reasoning)}

Consider: Does the implementation match the stated reasoning?
Are the decisions justified?
"""
```

#### C. Investigator Deep-Dive

Investigator gets full reasoning timeline:

```python
# Get complete reasoning timeline for debugging
timeline = db.reasoning_timeline(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    format='markdown'
)

investigation_prompt += f"""
## Complete Reasoning Timeline
{timeline}

Analyze: Where did reasoning diverge from implementation?
What assumptions proved incorrect?
"""
```

#### D. PM Audit Trail

PM queries reasoning for BAZINGA validation:

```python
# Get all completion reasoning for final review
completion_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    phase='completion'
)

# Verify against success criteria
for criteria in success_criteria:
    matching_reasoning = find_related_reasoning(criteria, completion_reasoning)
    # Validate implementation matches reasoning
```

---

## Implementation Plan

### Phase 1: Database Schema (30 min)
1. Add migration to extend `orchestration_logs` table
2. Add new columns: `log_type`, `reasoning_phase`, `confidence_level`, `references_json`, `redacted`
3. Add index for reasoning queries
4. Update schema version

### Phase 2: bazinga-db Commands (1.5 hours)
1. Add `scan_and_redact()` function for secret scanning
2. Add `save_reasoning()` method with retry/backoff
3. Add `get_reasoning()` method with filters
4. Add `reasoning_timeline()` method
5. Add CLI commands to main()
6. Update SKILL.md with new commands

### Phase 3: Agent Prompt Updates (2 hours)
1. Update `agents/developer.md` with mandatory reasoning section
2. Update `agents/senior_software_engineer.md`
3. Update `agents/qa_expert.md`
4. Update `agents/techlead.md`
5. Update `agents/project_manager.md`
6. Update `agents/investigator.md`
7. Update `agents/requirements_engineer.md`

### Phase 4: Integration (1 hour)
1. Update orchestrator to query reasoning for spawns
2. Update Tech Lead to review reasoning
3. Update Investigator to use reasoning timeline

### Phase 5: Testing (1 hour)
1. Test save/get reasoning commands
2. Test secret redaction
3. Test retry/backoff under load
4. Test reasoning in agent workflow
5. Verify persistence across compactions

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI vs Natural Language | **CLI commands** | Consistent with existing bazinga-db usage, explicit and reliable |
| New table vs Extend existing | **Extend orchestration_logs** | Simpler schema, reuses indexes, single activity source |
| Scope | **All agents, all 7 phases** | Comprehensive audit trail, mandatory minimum of 2 phases |
| Auto-extract vs Manual | **Manual agent documentation** | Agents do all reasoning documentation explicitly |
| Storage location | **Full text in DB** | Database is source of truth, queryable, no file I/O |
| Secret handling | **Scan and redact** | Prevent accidental secret leakage |
| Configurability | **Mandatory (not optional)** | Reasoning capture is always required |
| Concurrency | **Retry with exponential backoff** | Handle parallel agent writes gracefully |

---

## Success Metrics

1. **Adoption Rate**
   - Target: 100% of agent spawns include at least `understanding` + `completion` phases
   - Measure: `SELECT COUNT(*) FROM orchestration_logs WHERE log_type='reasoning' AND reasoning_phase IN ('understanding', 'completion')`

2. **Debugging Utility**
   - Target: 50% reduction in Investigator iteration count
   - Measure: Compare iteration counts before/after reasoning availability

3. **Review Efficiency**
   - Target: 20% faster Tech Lead reviews (less back-and-forth)
   - Measure: Time from READY_FOR_REVIEW to APPROVED

4. **Handoff Quality**
   - Target: 30% fewer "context lost" escalations
   - Measure: Escalation reasons citing missing context

5. **Secret Safety**
   - Target: 0 secrets stored in reasoning text
   - Measure: `SELECT COUNT(*) FROM orchestration_logs WHERE redacted=1`

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

**Critical feedback received and addressed:**

1. ✅ **Concurrency/locking** - Added retry with exponential backoff
2. ✅ **Secret scanning** - Added redaction before storage
3. ❌ **Natural language protocol** - Rejected: CLI is more explicit and reliable
4. ✅ **Schema fragmentation** - Accepted: Extend existing table instead of new one
5. ❌ **Start minimal** - Rejected: All agents, all phases from start
6. ❌ **Auto-extract from reports** - Rejected: Agents manually document
7. ❌ **Files + DB summary** - Rejected: DB is source of truth
8. ❌ **Configurable** - Rejected: Mandatory, not optional

### Incorporated Feedback
- Extended `orchestration_logs` table instead of new `agent_reasoning` table
- Added secret scanning with regex patterns for common secrets
- Added retry with exponential backoff (1s, 2s, 4s) for DB writes
- Added `redacted` column to track when secrets were removed

### Rejected Suggestions (With Reasoning)
| Suggestion | Why Rejected |
|------------|--------------|
| Natural language protocol | CLI is explicit, consistent with existing skill usage |
| Start with 2 phases, 2 agents | Comprehensive from start enables full audit trail |
| Auto-extract from reports | Agents should explicitly articulate reasoning, not auto-parse |
| Store long-form in files | DB is single source of truth, files add complexity |
| Make configurable | Reasoning is always valuable, no reason to disable |

---

## References

- [Claude Code Background Agent Feature](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [SubagentStop Hook Documentation](https://code.claude.com/docs/en/hooks)
- [Context Package System](research/context-package-system.md)
- [bazinga-db Schema Reference](/.claude/skills/bazinga-db/references/schema.md)
- [OpenAI GPT-5 Review](tmp/ultrathink-reviews/openai-review.md)
