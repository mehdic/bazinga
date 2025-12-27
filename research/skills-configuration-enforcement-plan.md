# Skills Configuration Enforcement: Comprehensive Implementation Plan

**Date:** 2025-12-27
**Context:** System skills are defined in `skills_config.json` with levels (mandatory/optional/disabled) but enforcement is incomplete
**Decision:** Implement full skill configuration enforcement across the BAZINGA orchestration system
**Status:** Reviewed - Ready for User Approval
**Reviewed by:** OpenAI GPT-5 (2025-12-27)

---

## Problem Statement

The BAZINGA system has a well-defined skills configuration (`bazinga/skills_config.json`) that assigns skill levels per agent:
- **mandatory** - Must always run
- **optional** - Can be invoked based on task characteristics
- **disabled** - Not available to agent

However, this configuration is **not enforced**:
1. Agents are told to "invoke skills" but there's no guarantee they do
2. `prompt-builder` doesn't inject skill configurations into prompts
3. `config-seeder` doesn't seed skills_config to database
4. No tracking of whether mandatory skills actually ran
5. Optional skills lack context-aware triggering logic

---

## Actors Inventory

### Configuration Files
| File | Purpose | Current State |
|------|---------|---------------|
| `bazinga/skills_config.json` | Skill levels per agent | Defined but not enforced |
| `bazinga/challenge_levels.json` | QA 5-level test progression | Working correctly |
| `bazinga/model_selection.json` | Agent model assignments | Working (seeded to DB) |

### Database Tables
| Table | Purpose | Skills Relevance |
|-------|---------|------------------|
| `configuration` | System config storage | Can store skills_config |
| `skill_outputs` | Skill execution results | Records skill runs |
| `workflow_transitions` | Routing rules | No skill dependency |
| `workflow_special_rules` | Testing mode, escalation | No skill dependency |
| `task_groups` | Task metadata | Could track required skills |

### Skills (18 Total)
| Skill | Who Uses | Config Level |
|-------|----------|--------------|
| `lint-check` | Developer, SSE, Tech Lead | mandatory (dev/sse/tl) |
| `security-scan` | Tech Lead, Investigator | mandatory (tl), optional (inv) |
| `test-coverage` | Tech Lead | mandatory (tl) |
| `codebase-analysis` | Developer, SSE, Investigator | optional (dev), mandatory (sse/inv) |
| `pattern-miner` | Investigator, QA Expert | mandatory (inv), optional (qa) |
| `test-pattern-analysis` | SSE, Investigator | mandatory (sse), optional (inv) |
| `api-contract-validation` | Developer | optional |
| `db-migration-check` | Developer | optional |
| `velocity-tracker` | PM | optional |
| `quality-dashboard` | QA Expert | optional |
| `bazinga-db` | All agents | infrastructure |
| `bazinga-validator` | Orchestrator | infrastructure |
| `workflow-router` | Orchestrator | infrastructure |
| `prompt-builder` | Orchestrator | infrastructure |
| `config-seeder` | Orchestrator | infrastructure |
| `specialization-loader` | Orchestrator | infrastructure |
| `context-assembler` | Orchestrator | infrastructure |
| `skill-creator` | User | meta |

### Agents
| Agent | Mandatory Skills | Optional Skills |
|-------|------------------|-----------------|
| developer | lint-check | codebase-analysis, test-pattern-analysis, api-contract-validation, db-migration-check |
| senior_software_engineer | lint-check, codebase-analysis, test-pattern-analysis | api-contract-validation, db-migration-check, security-scan |
| tech_lead | security-scan, lint-check, test-coverage | codebase-analysis, pattern-miner, test-pattern-analysis |
| qa_expert | (none) | pattern-miner, quality-dashboard |
| investigator | codebase-analysis, pattern-miner | test-pattern-analysis, security-scan |
| project_manager | (none) | velocity-tracker |

### Scripts/Entry Points
| Script | Role | Needs Modification |
|--------|------|-------------------|
| `prompt_builder.py` | Builds agent prompts | YES - inject skills section |
| `seed_configs.py` | Seeds DB at session start | YES - seed skills_config |
| `workflow_router.py` | Routes between agents | NO - skills don't affect routing |
| `bazinga_db.py` | Database operations | YES - add skill tracking |

---

## Implementation Plan

### Phase 1: Database Foundation (Low Risk)

#### 1.1 Add Skills Configuration Seeding

**File:** `.claude/skills/config-seeder/scripts/seed_configs.py`

**Changes:**
```python
def seed_skills_config(conn):
    """Seed skills configuration from JSON."""
    config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
    if not config_path.exists():
        print(f"WARNING: {config_path} not found, skipping skills config", file=sys.stderr)
        return True  # Non-fatal

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()

    # Store in configuration table (already exists)
    cursor.execute("""
        INSERT OR REPLACE INTO configuration (key, value, updated_at)
        VALUES ('skills_config', ?, CURRENT_TIMESTAMP)
    """, (json.dumps(data),))

    conn.commit()
    print(f"Seeded skills configuration")
    return True
```

**Update `--all` flag to include skills:**
```python
if args.all:
    seed_transitions(conn)
    seed_markers(conn)
    seed_special_rules(conn)
    seed_skills_config(conn)  # NEW
```

#### 1.2 Add Skill Invocation Tracking

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**New Command:** `track-skill-invocation`

```python
def track_skill_invocation(session_id, group_id, agent_type, skill_name, invoked_by):
    """Record that a skill was invoked."""
    cursor.execute("""
        INSERT INTO skill_invocations
        (session_id, group_id, agent_type, skill_name, invoked_by, timestamp)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (session_id, group_id, agent_type, skill_name, invoked_by))
```

**New Command:** `check-mandatory-skills`

```python
def check_mandatory_skills(session_id, group_id, agent_type):
    """Verify all mandatory skills for agent were invoked."""
    # Get skills_config from configuration table
    cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
    row = cursor.fetchone()
    if not row:
        return {"complete": True, "missing": [], "error": "No skills config"}

    config = json.loads(row[0])
    agent_config = config.get(agent_type, {})

    mandatory = [skill for skill, level in agent_config.items() if level == "mandatory"]

    # Check which were invoked
    cursor.execute("""
        SELECT DISTINCT skill_name FROM skill_invocations
        WHERE session_id = ? AND group_id = ? AND agent_type = ?
    """, (session_id, group_id, agent_type))

    invoked = {row[0] for row in cursor.fetchall()}
    missing = [s for s in mandatory if s not in invoked]

    return {"complete": len(missing) == 0, "missing": missing, "invoked": list(invoked)}
```

#### 1.3 Database Schema Addition

**File:** `.claude/skills/bazinga-db/scripts/init_db.py`

**New Table:**
```sql
CREATE TABLE IF NOT EXISTS skill_invocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT,
    agent_type TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    invoked_by TEXT,  -- 'agent' or 'orchestrator'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_si_session ON skill_invocations(session_id, agent_type);
CREATE INDEX idx_si_group ON skill_invocations(session_id, group_id);
```

---

### Phase 2: Prompt Builder Skills Injection (Medium Risk)

#### 2.1 Add Skills Configuration Reader

**File:** `.claude/skills/prompt-builder/scripts/prompt_builder.py`

**New Function:**
```python
def get_skills_config_for_agent(conn, agent_type):
    """Get skills configuration for an agent from database."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
        row = cursor.fetchone()
        if not row:
            return {"mandatory": [], "optional": [], "disabled": []}

        config = json.loads(row[0])
        agent_config = config.get(agent_type, {})

        result = {"mandatory": [], "optional": [], "disabled": []}
        for skill, level in agent_config.items():
            if level in result:
                result[level].append(skill)

        return result
    except sqlite3.OperationalError:
        return {"mandatory": [], "optional": [], "disabled": []}
```

#### 2.2 Build Skills Configuration Block

**New Function:**
```python
def build_skills_block(conn, agent_type):
    """Build the skills configuration block for prompt injection."""
    skills = get_skills_config_for_agent(conn, agent_type)

    if not skills["mandatory"] and not skills["optional"]:
        return ""

    block = """## SKILLS CONFIGURATION (From bazinga/skills_config.json)

**Your assigned skills for this session:**

"""

    if skills["mandatory"]:
        block += """### MANDATORY Skills (MUST invoke before completing task)

| Skill | When to Invoke | Invocation |
|-------|----------------|------------|
"""
        skill_docs = {
            "lint-check": ("Before any commit", '`Skill(command: "lint-check")`'),
            "security-scan": ("During code review", '`Skill(command: "security-scan")`'),
            "test-coverage": ("When reviewing tests", '`Skill(command: "test-coverage")`'),
            "codebase-analysis": ("For complex tasks", '`Skill(command: "codebase-analysis")`'),
            "pattern-miner": ("For historical patterns", '`Skill(command: "pattern-miner")`'),
            "test-pattern-analysis": ("When writing tests", '`Skill(command: "test-pattern-analysis")`'),
        }
        for skill in skills["mandatory"]:
            when, how = skill_docs.get(skill, ("As needed", f'`Skill(command: "{skill}")`'))
            block += f"| {skill} | {when} | {how} |\n"

        block += """
**CRITICAL:** Orchestrator will verify these skills were invoked before accepting your completion.

"""

    if skills["optional"]:
        block += """### OPTIONAL Skills (Invoke based on task characteristics)

"""
        for skill in skills["optional"]:
            block += f"- `{skill}` - Use when relevant to your task\n"

    return block
```

#### 2.3 Integrate into build_prompt()

**Modification to `build_prompt()` function:**

```python
def build_prompt(args):
    # ... existing code ...

    components = []

    # 1. Build CONTEXT block (existing)
    # 2. Build SPECIALIZATION block (existing)

    # 3. Build SKILLS CONFIGURATION block (NEW)
    if conn and args.agent_type not in ["project_manager", "orchestrator"]:
        skills_block = build_skills_block(conn, args.agent_type)
        if skills_block:
            components.append(skills_block)

    # 4. Read AGENT DEFINITION (existing, was #3)
    # ... rest of function ...
```

---

### Phase 3: Orchestrator Verification (Medium Risk)

#### 3.1 Post-Agent Skill Verification

**File:** `agents/orchestrator.md`

**Add verification step after agent completion:**

```markdown
### 🔴 MANDATORY: Skill Invocation Verification

**AFTER receiving agent response, BEFORE routing:**

1. Check mandatory skills were invoked:
   ```
   bazinga-db check-mandatory-skills {session_id} {group_id} {agent_type}
   ```

2. IF missing skills:
   - Log warning but DO NOT block (skills are agent's responsibility)
   - Include in next spawn prompt: "Note: Previous agent did not invoke: [skills]"

3. IF all mandatory skills invoked:
   - Proceed with normal routing
```

**Rationale:** We log but don't block because:
- Agent may have valid reason to skip (e.g., no code changes = no lint needed)
- Blocking creates deadlocks
- Visibility is the primary goal

#### 3.2 Workflow Router Integration (Optional)

**File:** `.claude/skills/workflow-router/scripts/workflow_router.py`

**Add skill check to routing result:**

```python
def route(current_agent, status, session_id, group_id, testing_mode):
    # ... existing routing logic ...

    # Add skill check information to result
    skill_check = check_mandatory_skills(session_id, group_id, current_agent)

    result["skill_check"] = {
        "complete": skill_check["complete"],
        "missing": skill_check["missing"]
    }

    return result
```

---

### Phase 4: Optional Skills Context-Awareness (Low Priority)

#### 4.1 Task Characteristic Detection

**Concept:** Analyze task description to suggest optional skills.

```python
def suggest_optional_skills(task_description, agent_type, skills_config):
    """Suggest optional skills based on task characteristics."""
    suggestions = []

    # API changes → api-contract-validation
    if any(kw in task_description.lower() for kw in ['api', 'endpoint', 'route', 'rest']):
        if 'api-contract-validation' in skills_config.get('optional', []):
            suggestions.append(('api-contract-validation', 'Task involves API changes'))

    # Database/migration → db-migration-check
    if any(kw in task_description.lower() for kw in ['migration', 'schema', 'database', 'model']):
        if 'db-migration-check' in skills_config.get('optional', []):
            suggestions.append(('db-migration-check', 'Task involves database changes'))

    # Security keywords → security-scan
    if any(kw in task_description.lower() for kw in ['auth', 'security', 'password', 'token', 'encrypt']):
        if 'security-scan' in skills_config.get('optional', []):
            suggestions.append(('security-scan', 'Task involves security-sensitive code'))

    return suggestions
```

#### 4.2 Inject Suggestions into Prompt

```python
def build_skill_suggestions_block(task_description, agent_type, conn):
    skills_config = get_skills_config_for_agent(conn, agent_type)
    suggestions = suggest_optional_skills(task_description, agent_type, skills_config)

    if not suggestions:
        return ""

    block = """### Suggested Skills for This Task

Based on your task description, consider invoking:

"""
    for skill, reason in suggestions:
        block += f"- **{skill}**: {reason}\n"

    return block
```

---

## Edge Cases

### Edge Case 1: Skills Config Not Seeded
**Scenario:** Session starts but config-seeder fails or skips skills.
**Handling:**
- `get_skills_config_for_agent()` returns empty config
- No skills block injected into prompt
- Agent falls back to static instructions in markdown file
- System continues to work (graceful degradation)

### Edge Case 2: Agent Invokes Skill That's Disabled
**Scenario:** Developer tries to invoke `security-scan` but it's disabled for them.
**Handling:**
- Skill invocation still works (skills are standalone)
- Tracking records the invocation
- No enforcement prevents disabled skill usage
- **Future:** Could add enforcement in skill wrapper

### Edge Case 3: Mandatory Skill Fails
**Scenario:** `lint-check` is mandatory but returns errors.
**Handling:**
- Skill failure is the agent's problem to fix
- Tracking still records invocation (skill ran, just had findings)
- Agent must address findings before reporting ready

### Edge Case 4: Resume Session After Context Compaction
**Scenario:** Long session, context compacted, skills config "forgotten."
**Handling:**
- Skills config is in database, not context
- `prompt-builder` re-queries on each spawn
- Configuration persists across compactions

### Edge Case 5: Parallel Developers with Different Skill Requirements
**Scenario:** Group A needs API skills, Group B needs DB skills.
**Handling:**
- Current design is agent-level, not group-level
- All developers get same mandatory skills
- Optional suggestions are task-based (per group)
- **Future:** Could add group-level skill config to task_groups table

### Edge Case 6: Skill Output Not Saved to Database
**Scenario:** Agent invokes skill but skill fails to save output.
**Handling:**
- `track-skill-invocation` is separate from skill output saving
- Invocation tracking happens at invoke time
- Output saving happens in skill script
- Both should succeed but are independent

### Edge Case 7: Testing Mode Affects Skill Requirements
**Scenario:** `testing_mode: disabled` - should test-coverage still be mandatory?
**Handling:**
- Current: skills_config is static, doesn't vary by testing mode
- **Enhancement:** Add testing_mode filter in `build_skills_block()`:
  ```python
  if testing_mode == "disabled":
      skills["mandatory"] = [s for s in skills["mandatory"]
                            if s not in ["test-coverage", "test-pattern-analysis"]]
  ```

### Edge Case 8: New Skill Added Mid-Session
**Scenario:** User adds new skill to skills_config.json during active session.
**Handling:**
- Config is seeded at session start
- Changes don't affect running sessions
- New sessions will pick up changes
- No hot-reload mechanism (by design)

---

## Verification Plan

### Unit Tests

```python
# test_skills_config.py

def test_seed_skills_config():
    """Verify skills config is seeded to database."""
    conn = init_test_db()
    seed_skills_config(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
    row = cursor.fetchone()

    assert row is not None
    config = json.loads(row[0])
    assert "developer" in config
    assert config["developer"]["lint-check"] == "mandatory"

def test_get_skills_config_for_agent():
    """Verify skills config retrieval per agent."""
    conn = init_test_db()
    seed_skills_config(conn)

    dev_skills = get_skills_config_for_agent(conn, "developer")
    assert "lint-check" in dev_skills["mandatory"]
    assert "codebase-analysis" in dev_skills["optional"]

def test_track_skill_invocation():
    """Verify skill invocation tracking."""
    conn = init_test_db()
    track_skill_invocation("sess_1", "GROUP_A", "developer", "lint-check", "agent")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skill_invocations WHERE session_id = 'sess_1'")
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_check_mandatory_skills_complete():
    """Verify mandatory skills check when all invoked."""
    conn = init_test_db()
    seed_skills_config(conn)
    track_skill_invocation("sess_1", "GROUP_A", "developer", "lint-check", "agent")

    result = check_mandatory_skills("sess_1", "GROUP_A", "developer")
    assert result["complete"] == True
    assert result["missing"] == []

def test_check_mandatory_skills_missing():
    """Verify mandatory skills check when some missing."""
    conn = init_test_db()
    seed_skills_config(conn)
    # Don't invoke lint-check

    result = check_mandatory_skills("sess_1", "GROUP_A", "developer")
    assert result["complete"] == False
    assert "lint-check" in result["missing"]

def test_build_skills_block():
    """Verify skills block generation."""
    conn = init_test_db()
    seed_skills_config(conn)

    block = build_skills_block(conn, "developer")
    assert "MANDATORY Skills" in block
    assert "lint-check" in block
    assert "OPTIONAL Skills" in block
    assert "codebase-analysis" in block
```

### Integration Tests

```bash
# Test full flow: session init → agent spawn → skill check

# 1. Create session with config seeding
python3 .claude/skills/bazinga-db/scripts/init_session.py --session-id "test_skills_001"

# 2. Verify skills config was seeded
python3 -c "
import sqlite3, json
conn = sqlite3.connect('bazinga/bazinga.db')
cursor = conn.cursor()
cursor.execute(\"SELECT value FROM configuration WHERE key = 'skills_config'\")
row = cursor.fetchone()
assert row is not None, 'Skills config not seeded'
print('Skills config seeded:', json.loads(row[0]).keys())
"

# 3. Build developer prompt and verify skills block
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
    --agent-type developer \
    --session-id "test_skills_001" \
    --group-id "TEST" \
    --branch "main" \
    --mode "simple" \
    --testing-mode "full" \
    | grep -A 20 "SKILLS CONFIGURATION"

# 4. Simulate skill invocation tracking
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
    track-skill-invocation "test_skills_001" "TEST" "developer" "lint-check" "agent"

# 5. Verify mandatory skills check
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
    check-mandatory-skills "test_skills_001" "TEST" "developer"
```

---

## Implementation Order

| Phase | Component | Files Modified | Risk | Dependencies |
|-------|-----------|---------------|------|--------------|
| 1.1 | Seed skills_config | config-seeder/scripts/seed_configs.py | Low | None |
| 1.2 | Track skill invocations | bazinga-db/scripts/bazinga_db.py | Low | 1.3 (schema) |
| 1.3 | Add skill_invocations table | bazinga-db/scripts/init_db.py | Low | None |
| 2.1 | Skills config reader | prompt-builder/scripts/prompt_builder.py | Medium | 1.1 |
| 2.2 | Build skills block | prompt-builder/scripts/prompt_builder.py | Medium | 2.1 |
| 2.3 | Integrate into build_prompt | prompt-builder/scripts/prompt_builder.py | Medium | 2.2 |
| 3.1 | Post-agent verification | agents/orchestrator.md | Medium | 1.2 |
| 3.2 | Workflow router integration | workflow-router/scripts/workflow_router.py | Low | 1.2 |
| 4.1 | Task characteristic detection | prompt-builder/scripts/prompt_builder.py | Low | 2.2 |
| 4.2 | Inject suggestions | prompt-builder/scripts/prompt_builder.py | Low | 4.1 |

---

## Rollback Plan

If issues arise after deployment:

1. **Phase 1 (DB):** Drop `skill_invocations` table, remove skills_config from configuration table
2. **Phase 2 (Prompt):** Revert prompt_builder.py changes (skills block becomes empty string)
3. **Phase 3 (Orchestrator):** Remove verification step from orchestrator.md
4. **Phase 4 (Suggestions):** Remove suggestion functions

Each phase is independently reversible. Database changes are additive (new table, not schema modifications to existing tables).

---

## Success Metrics

| Metric | Before | After | How to Measure |
|--------|--------|-------|----------------|
| Skills config seeded | 0% sessions | 100% sessions | Query configuration table |
| Skill invocations tracked | 0 | All mandatory | Query skill_invocations table |
| Mandatory skills visibility | Static in MD | Dynamic per-agent | Check prompt content |
| Missing skill detection | None | Per-agent report | check-mandatory-skills command |

---

## Open Questions

1. **Enforcement Level:** Should missing mandatory skills block agent completion, or just log?
   - **Recommendation:** Log only (visibility without blocking)

2. **Group-Level Skills:** Should different task groups have different skill requirements?
   - **Recommendation:** Not in v1, agent-level is sufficient

3. **Skill Dependencies:** Should some skills require others first (e.g., lint before security)?
   - **Recommendation:** Not in v1, too complex for initial implementation

4. **Testing Mode Integration:** Should testing_mode filter out test-related skills?
   - **Recommendation:** Yes, add filter in build_skills_block()

---

## Multi-LLM Review Integration

**Review completed:** 2025-12-27 by OpenAI GPT-5

### Critical Issues Identified (MUST FIX)

| Issue | Problem | Solution |
|-------|---------|----------|
| **Transaction Boundary Violation** | `seed_skills_config()` calls `conn.commit()` while outer function already manages transaction | Remove `conn.commit()` from function, rely on outer transaction |
| **No Migration Path** | Adding tables won't affect existing DBs | Add migration script with `CREATE TABLE IF NOT EXISTS` |
| **Skill Tracking Not Instrumented** | Plan assumes agents track invocations but skills don't auto-record | Use `skill_outputs` table as evidence (already populated by skills) |
| **PM Key Mismatch** | Config uses "pm" but agent_type is "project_manager" | Add key alias mapping in `get_skills_config_for_agent()` |
| **Prompt Budget Risk** | Skills block could cause trimming of valuable sections | Make skills block compact (checklist, not table) |

### Incorporated Feedback

1. **Use `skill_outputs` as evidence instead of new table**
   - Skills already save to `skill_outputs` table
   - Query this with recency window instead of adding `skill_invocations`
   - Reduces schema churn and eliminates instrumentation requirement

2. **Transaction cleanup**
   - Remove `conn.commit()` from `seed_skills_config()`
   - Rely on outer transaction in `seed_configs.py`

3. **Compact skills checklist**
   - Replace verbose table with short checklist (≤10 lines)
   - Lower trimming priority than specializations

4. **Agent key aliasing**
   - Map "project_manager" → "pm" when querying config
   - Add alias dict: `{"project_manager": "pm"}`

5. **Testing mode filtering**
   - Skip `test-coverage`, `test-pattern-analysis` when testing_mode is disabled/minimal
   - Pass testing_mode to `build_skills_block()`

6. **Recency-based evidence check**
   - Query `skill_outputs` with timestamp filter
   - Check "invoked within this iteration" not "ever invoked"

### Rejected Suggestions (With Reasoning)

1. **Blocking enforcement for any gates**
   - OpenAI suggested blocking Developer→QA if lint-check missing
   - **Rejected:** Creates deadlocks, agents may have valid skip reasons
   - **Alternative:** Warn-only with visibility in next spawn prompt

2. **Skill wrapper instrumentation**
   - OpenAI suggested modifying all skills to auto-track
   - **Rejected:** Too much churn, `skill_outputs` already provides evidence
   - **Alternative:** Evidence-by-output approach

---

## Revised Implementation Plan (Post-Review)

### Phase 1: Database Foundation (REVISED)

#### 1.1 Seed Skills Configuration (NO conn.commit())

```python
def seed_skills_config(conn):
    """Seed skills configuration from JSON.

    NOTE: Do NOT call conn.commit() - caller manages transaction.
    """
    config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
    if not config_path.exists():
        print(f"WARNING: {config_path} not found", file=sys.stderr)
        return True  # Non-fatal

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO configuration (key, value, updated_at)
        VALUES ('skills_config', ?, CURRENT_TIMESTAMP)
    """, (json.dumps(data),))

    # NO conn.commit() here - outer transaction handles it
    print(f"Seeded skills configuration")
    return True
```

#### 1.2 Evidence-Based Skill Check (Use skill_outputs)

**New Command:** `check-skill-evidence`

```python
def check_skill_evidence(session_id, group_id, agent_type, since_minutes=30):
    """Check if mandatory skills have recent evidence in skill_outputs.

    Uses existing skill_outputs table - no new schema needed.
    """
    # Get skills_config
    cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
    row = cursor.fetchone()
    if not row:
        return {"complete": True, "missing": [], "note": "No skills config"}

    config = json.loads(row[0])

    # Handle agent key aliasing
    agent_key = {"project_manager": "pm"}.get(agent_type, agent_type)
    agent_config = config.get(agent_key, {})

    mandatory = [skill for skill, level in agent_config.items() if level == "mandatory"]

    if not mandatory:
        return {"complete": True, "missing": [], "mandatory": []}

    # Check skill_outputs for recent evidence
    since_time = datetime.now() - timedelta(minutes=since_minutes)

    cursor.execute("""
        SELECT DISTINCT skill_name FROM skill_outputs
        WHERE session_id = ?
        AND timestamp >= ?
    """, (session_id, since_time.isoformat()))

    recent_outputs = {row[0] for row in cursor.fetchall()}
    missing = [s for s in mandatory if s not in recent_outputs]

    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "found": list(recent_outputs & set(mandatory)),
        "recency_window_minutes": since_minutes
    }
```

#### 1.3 NO New Table Needed

**REMOVED:** `skill_invocations` table
**Reason:** `skill_outputs` already provides evidence of skill execution

### Phase 2: Compact Skills Checklist (REVISED)

#### 2.1 Agent Key Aliasing

```python
# Agent type to config key mapping
AGENT_KEY_ALIASES = {
    "project_manager": "pm",
    # Add others if needed
}

def get_skills_config_for_agent(conn, agent_type, testing_mode="full"):
    """Get skills configuration with key aliasing and testing mode filter."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
        row = cursor.fetchone()
        if not row:
            return {"mandatory": [], "optional": [], "disabled": []}

        config = json.loads(row[0])

        # Apply key aliasing
        agent_key = AGENT_KEY_ALIASES.get(agent_type, agent_type)
        agent_config = config.get(agent_key, {})

        result = {"mandatory": [], "optional": [], "disabled": []}
        for skill, level in agent_config.items():
            if level in result:
                result[level].append(skill)

        # Testing mode filtering
        if testing_mode in ("disabled", "minimal"):
            test_skills = {"test-coverage", "test-pattern-analysis"}
            result["mandatory"] = [s for s in result["mandatory"] if s not in test_skills]

        return result
    except sqlite3.OperationalError:
        return {"mandatory": [], "optional": [], "disabled": []}
```

#### 2.2 Compact Checklist Block (≤10 lines)

```python
def build_skills_block(conn, agent_type, testing_mode="full"):
    """Build compact skills checklist for prompt injection."""
    skills = get_skills_config_for_agent(conn, agent_type, testing_mode)

    if not skills["mandatory"] and not skills["optional"]:
        return ""

    # Compact checklist format (≤10 lines)
    lines = ["## Skills Checklist", ""]

    if skills["mandatory"]:
        lines.append("**MUST invoke before completion:**")
        for skill in skills["mandatory"]:
            lines.append(f"- [ ] `Skill(command: \"{skill}\")`")
        lines.append("")

    if skills["optional"]:
        lines.append("**Consider if relevant:** " + ", ".join(skills["optional"]))

    return "\n".join(lines)
```

---

## References

- `bazinga/skills_config.json` - Skills configuration source
- `bazinga/challenge_levels.json` - QA levels (working correctly)
- `.claude/skills/config-seeder/SKILL.md` - Current seeding docs
- `.claude/skills/bazinga-db/references/schema.md` - Database schema
- `.claude/skills/prompt-builder/scripts/prompt_builder.py` - Prompt building logic
- `agents/orchestrator.md` - Orchestrator workflow
