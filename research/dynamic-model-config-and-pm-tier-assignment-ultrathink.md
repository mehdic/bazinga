# Dynamic Model Config & PM Initial Tier Assignment: Ultrathink Analysis

**Date:** 2025-11-25
**Context:** User suggestions to improve BAZINGA model selection and task routing
**Decision:** BOTH VALID - Implement with specific approaches
**Status:** Proposed

---

## Problem Statement

### Issue 1: Hardcoded Model Assignments
**Current state:** Model assignments are hardcoded in Task invocations:
```markdown
Task(subagent_type="general-purpose", model="haiku", ...)   # Developer
Task(subagent_type="general-purpose", model="sonnet", ...)  # Senior Engineer
```

**Problem:** When Anthropic releases new models (Claude 4, etc.), every hardcoded reference must be manually updated across 14+ Task invocations in the orchestrator.

### Issue 2: Wasteful First Attempts
**Current state:** ALL tasks start with Developer (Haiku), regardless of complexity.

**Problem:** A complexity-8 task will almost certainly fail on Haiku, wasting:
- Tokens on failed attempt
- Time on retry cycle
- User patience

The PM already calculates complexity scores - why not use them?

---

## Solution 1: Dynamic Model Config

### Approach A: Database Storage (RECOMMENDED)

**Why DB over JSON file:**
1. DB already exists (bazinga.db)
2. bazinga-db skill already provides read/write interface
3. Allows runtime updates without file editing
4. Consistent with existing state management pattern

**Implementation:**

**Step 1: Add model_config table to schema**
```sql
CREATE TABLE model_config (
    agent_role TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    rationale TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default values
INSERT INTO model_config VALUES
    ('developer', 'haiku', 'Cost-efficient for L1-2 tasks'),
    ('senior_software_engineer', 'sonnet', 'Complex failures and L3+ tasks'),
    ('qa_expert', 'sonnet', 'Test generation and validation'),
    ('tech_lead', 'opus', 'Architectural decisions - non-negotiable'),
    ('project_manager', 'opus', 'Strategic planning - non-negotiable'),
    ('investigator', 'opus', 'Root cause analysis'),
    ('validator', 'sonnet', 'BAZINGA verification');
```

**Step 2: Orchestrator reads config at initialization**
```markdown
### Step 0.1: Load Model Configuration

**MANDATORY FIRST ACTION after initialization:**

Query model configuration from database:
```
bazinga-db, retrieve model configuration:
Query: SELECT agent_role, model FROM model_config
```
Invoke: `Skill(command: "bazinga-db")`

**Store in context for this session:**
- developer_model: [from query]
- senior_software_engineer_model: [from query]
- qa_expert_model: [from query]
- tech_lead_model: [from query]
- pm_model: [from query]
- investigator_model: [from query]

**Use these values in ALL subsequent Task invocations.**
```

**Step 3: Update Task invocations to use config**
```markdown
# Before (hardcoded):
Task(subagent_type="general-purpose", model="haiku", ...)

# After (from config):
Task(subagent_type="general-purpose", model={developer_model}, ...)
```

### Approach B: JSON File Read (ALTERNATIVE)

**Simpler but less flexible:**
```markdown
### Step 0.1: Load Model Configuration

Read model configuration:
```
Read: bazinga/model_selection.json
```

Extract and store:
- developer_model: agents.developer.model
- senior_software_engineer_model: agents.senior_software_engineer.model
... etc
```

**Pros:** No DB schema changes
**Cons:** File might not exist in fresh installs, less consistent with DB pattern

### Verdict: Use Database Approach

**Rationale:**
1. Single source of truth in DB
2. Runtime updateable via bazinga-db skill
3. Query pattern already established
4. More robust for fresh installs (schema creates defaults)

---

## Solution 2: PM Initial Tier Assignment

### The Logic

PM already calculates complexity (1-10 scale) during planning. Use this to decide initial tier:

| Complexity | Initial Tier | Rationale |
|------------|--------------|-----------|
| 1-4 | Developer (Haiku) | Simple tasks, cost-efficient |
| 5-6 | Developer (Haiku) | Medium tasks, worth trying Haiku first |
| 7-10 | Senior Software Engineer (Sonnet) | Complex tasks, skip Haiku to save time |

### Implementation

**Step 1: Update PM task group output format**

Current:
```markdown
### Task Groups
- Group A: JWT Authentication (Complexity: 7/10)
  - Tasks: T001, T002
```

New:
```markdown
### Task Groups
- Group A: JWT Authentication
  - Complexity: 7/10
  - **Initial Tier:** Senior Software Engineer (Sonnet)
  - Tasks: T001, T002
  - Rationale: Security-sensitive authentication requires senior expertise
```

**Step 2: PM Decision Logic (add to project_manager.md)**

```markdown
### Initial Tier Assignment

**For each task group, determine starting tier based on complexity:**

| Complexity Score | Initial Tier | Model |
|-----------------|--------------|-------|
| 1-4 (Low) | Developer | {developer_model} |
| 5-6 (Medium) | Developer | {developer_model} |
| 7-10 (High) | Senior Software Engineer | {senior_software_engineer_model} |

**Override rules:**
- Security-sensitive code → Senior Software Engineer (regardless of complexity)
- Architectural decisions → Senior Software Engineer
- Bug fix with clear symptoms → Developer (even if complexity 7+)

**Output format per group:**
```
Group [ID]: [Name]
- Complexity: [X]/10
- Initial Tier: [Developer | Senior Software Engineer]
- Tier Rationale: [Why this tier]
- Tasks: [list]
```
```

**Step 3: Orchestrator reads PM's tier decision**

```markdown
### Step 2A.1: Parse PM Response and Spawn Developers

For each task group in PM's response:
1. Extract: group_id, tasks, complexity, **initial_tier**
2. Spawn appropriate agent:

IF initial_tier = "Senior Software Engineer":
  → Task(subagent_type="general-purpose", model={senior_software_engineer_model},
         description="SSE {group_id}: {task}", prompt=[senior engineer prompt])

IF initial_tier = "Developer":
  → Task(subagent_type="general-purpose", model={developer_model},
         description="Dev {group_id}: {task}", prompt=[developer prompt])
```

### Benefits

1. **Efficiency:** Complex tasks go directly to capable model
2. **Cost-aware:** Simple tasks stay on Haiku
3. **PM autonomy:** PM makes informed decision based on full context
4. **Flexibility:** PM can override based on task nature, not just score

---

## Solution 3: Rename to "Senior Software Engineer"

### Scope of Changes

| File | Changes Required |
|------|------------------|
| `agents/senior_engineer.md` | Rename to `senior_software_engineer.md`, update content |
| `agents/orchestrator.md` | Update all references (~15 occurrences) |
| `agents/developer.md` | Update escalation references (~5 occurrences) |
| `agents/qa_expert.md` | Update escalation routing (~3 occurrences) |
| `agents/project_manager.md` | Update tier references (~2 occurrences) |
| `bazinga/model_selection.json` | Rename key |
| `bazinga/skills_config.json` | Update section name |
| `templates/response_parsing.md` | Update status descriptions |

### Implementation

1. `git mv agents/senior_engineer.md agents/senior_software_engineer.md`
2. Global find/replace: "Senior Engineer" → "Senior Software Engineer"
3. Global find/replace: "senior_engineer" → "senior_software_engineer"
4. Update skill config section names
5. Rebuild slash commands

---

## Critical Analysis

### Pros ✅

**Dynamic Model Config:**
- Future-proof for new model releases
- Single point of configuration
- Runtime adjustable (no code changes)
- Consistent with DB-as-memory pattern

**PM Tier Assignment:**
- Eliminates wasteful first attempts
- Leverages PM's complexity analysis
- More efficient resource allocation
- Smarter cost optimization

**Combined benefit:** System becomes self-tuning based on PM intelligence

### Cons ⚠️

**Dynamic Model Config:**
- Adds initialization step to orchestration
- DB query adds small latency
- Config could be misconfigured (mitigated by defaults)

**PM Tier Assignment:**
- PM could mis-estimate complexity
- Reduces "learning by failure" for Haiku (minor)
- Adds complexity to PM's output format

### Verdict

**IMPLEMENT BOTH.** The benefits significantly outweigh the minimal complexity added. This transforms BAZINGA from a rigid system to an adaptive one.

---

## Implementation Plan

### Phase 1: Rename (Low Risk)
1. Rename agent file
2. Update all references
3. Rebuild slash commands
4. Commit

### Phase 2: PM Tier Assignment (Medium Risk)
1. Update PM with tier decision logic
2. Update orchestrator to read tier decision
3. Test with sample tasks
4. Commit

### Phase 3: Dynamic Model Config (Medium Risk)
1. Add model_config to DB schema (bazinga-db skill)
2. Add orchestrator initialization step
3. Replace hardcoded models with config references
4. Test model swapping
5. Commit

---

## Decision Rationale

**Why implement now:**
1. Both suggestions improve system efficiency
2. Changes are additive (don't break existing flows)
3. Lays foundation for future model upgrades
4. Aligns with "PM decides everything" principle

**Why database over JSON:**
1. Already have bazinga-db infrastructure
2. Runtime updateable
3. Schema enforces valid values
4. Defaults prevent misconfiguration

**Why PM decides tier:**
1. PM already has full context
2. Complexity score is already calculated
3. Eliminates redundant Haiku failures
4. More intelligent resource allocation

---

## References

- `agents/orchestrator.md` - Current Task invocations
- `bazinga/model_selection.json` - Current model documentation
- `skills/bazinga-db/SKILL.md` - DB interface
- Previous ultrathink: `research/review-validation-ultrathink.md`
