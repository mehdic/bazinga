# Deterministic Orchestration Implementation: Ultrathink Critical Review

**Date:** 2025-12-16
**Context:** Review of the deterministic prompt-builder, workflow-router, and config-seeder implementation
**Decision:** Multiple critical bugs identified requiring fixes
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA orchestrator was spawning agents with abbreviated prompts (~100 lines) instead of full agent definitions (~1400-2500 lines). The solution was to create a deterministic prompt-building system using Python scripts that:
1. Read agent files directly from filesystem
2. Query database for context and specializations
3. Apply token budgets per model
4. Validate required markers

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                                       │
│                                                                           │
│  1. Session Init:                                                         │
│     └── Skill("config-seeder") ──▶ Seeds transitions.json, markers.json  │
│                                     into workflow_* tables                │
│                                                                           │
│  2. Agent Spawn:                                                          │
│     └── Skill("prompt-builder") ──▶ Returns COMPLETE prompt (stdout)     │
│         │                                                                 │
│         └── Task(prompt={COMPLETE_PROMPT})                               │
│                                                                           │
│  3. After Response:                                                       │
│     └── Skill("workflow-router") ──▶ Returns JSON routing decision       │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
                 JSON Config Files                    Database
                 ─────────────────                    ────────
                       │                                  │
                       ▼                                  │
┌─────────────────────────────────────────────────────────────────────────┐
│                     config-seeder (run once)                             │
│                                                                           │
│  bazinga/config/transitions.json ──▶ workflow_transitions table          │
│  bazinga/config/agent-markers.json ──▶ agent_markers table               │
│  transitions.json._special_rules ──▶ workflow_special_rules table        │
└─────────────────────────────────────────────────────────────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     prompt-builder (per spawn)                           │
│                                                                           │
│  Reads from DB:                    Reads from filesystem:                │
│  - context_packages                - agents/*.md (agent definition)      │
│  - error_patterns                  - specialization templates            │
│  - orchestration_logs (reasoning)                                        │
│  - task_groups.specializations                                           │
│  - agent_markers (validation)                                            │
│                                                                           │
│  Output: Complete prompt to stdout                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     workflow-router (after response)                     │
│                                                                           │
│  Input:  current_agent, status, session_id, group_id, testing_mode       │
│                                                                           │
│  Queries: workflow_transitions, workflow_special_rules, task_groups      │
│                                                                           │
│  Output: JSON { next_agent, action, model, ... }                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Critical Analysis

### Component 1: prompt_builder.py

#### Strengths ✅

1. **Path Validation**: `validate_template_path()` prevents path traversal attacks
2. **Graceful DB Degradation**: All DB queries wrapped in try/except, returns empty on failure
3. **Token Budgeting**: Per-model limits (haiku=900, sonnet=1800, opus=2400)
4. **Marker Validation**: Ensures required markers present before spawn
5. **Agent File Validation**: Checks minimum line counts to detect truncation

#### Potential Issues ⚠️

1. **AGENT_FILE_MAP Path Inconsistency**
   ```python
   AGENT_FILE_MAP = {
       "developer": "agents/developer.md",
       "tech_lead": "agents/techlead.md",  # Note: "techlead" not "tech_lead"
   }
   ```
   - The filename is `techlead.md` but agent type is `tech_lead` (with underscore)
   - This is intentional but could confuse maintainers

2. **Database Connection Not Closed on Error Path**
   ```python
   def build_prompt(args):
       conn = sqlite3.connect(args.db)
       # ... if marker validation fails, sys.exit(1) is called
       # conn.close() only happens at line 573, but sys.exit at 114
   ```
   - **FIX NEEDED**: Marker validation calls `sys.exit(1)` before `conn.close()`

3. **Specialization Budget Applied to Wrong Budget Type**
   ```python
   if total_tokens + tokens <= budget["soft"]:  # Uses SOFT budget
       templates_content.append(content)
   ```
   - Specialization uses soft budget, but what about context block?
   - Context also uses soft budget (line 351)
   - Both compete for the same soft budget without coordination

4. **Token Estimation Too Simple**
   ```python
   def estimate_tokens(text):
       return len(text) // 4  # Characters / 4
   ```
   - This is a rough estimate. Claude tokenization varies.
   - Could under/overestimate by 20-30%

5. **Prior Reasoning Query Has Missing Agent Types**
   ```python
   relevant_agents = {
       'qa_expert': ['developer', 'senior_software_engineer'],
       # ... 'project_manager' not in list
   }
   ```
   - PM isn't queried for prior reasoning, but that's by design (line 528)
   - However, `requirements_engineer` also not in the list

6. **Model Parameter Default vs Passed Value**
   ```python
   parser.add_argument("--model", default="sonnet",  # Default
   # ...
   model = args.model or "sonnet"  # Also has fallback
   ```
   - Double fallback is redundant but harmless

### Component 2: workflow_router.py

#### Strengths ✅

1. **Config Loading from JSON**: `load_model_config()` reads from model_selection.json
2. **Fallback to Defaults**: If JSON missing, uses DEFAULT_MODEL_CONFIG
3. **Escalation Logic**: Checks revision count against threshold
4. **Security Override**: Forces SSE for security-sensitive tasks

#### Potential Issues ⚠️

1. **Model Config Loaded at Module Init**
   ```python
   MODEL_CONFIG = load_model_config()  # Line 60
   ```
   - If model_selection.json changes during orchestration, won't pick up changes
   - This is probably fine (config shouldn't change mid-session)

2. **get_revision_count Uses Wrong Column?**
   ```python
   cursor.execute("""
       SELECT revision_count FROM task_groups
       WHERE session_id = ? AND id = ?
   """, (session_id, group_id))
   ```
   - Let me verify `task_groups` has `revision_count` column...
   - **POTENTIAL BUG**: Need to verify schema has this column

3. **Security Check Only Looks at Task Name**
   ```python
   def check_security_sensitive(conn, session_id, group_id):
       name = row[0].lower()
       return "security" in name or "auth" in name
   ```
   - Only checks `name`, not PM's `security_sensitive` flag from task_group
   - **INCONSISTENCY**: PM sets flag, but router ignores it

4. **Batch Spawn Logic Incomplete**
   ```python
   if action == "spawn_batch":
       pending = get_pending_groups(conn, args.session_id)
       max_parallel = transition.get("max_parallel", 4)
       groups_to_spawn = pending[:max_parallel]
   ```
   - Returns group IDs but doesn't return their details
   - Orchestrator needs to query DB again for task details

### Component 3: seed_configs.py

#### Strengths ✅

1. **Transaction Wrapping**: `BEGIN TRANSACTION` / `ROLLBACK` / `COMMIT`
2. **Atomic Seeding**: All-or-nothing - if any fails, rolls back
3. **Clear Output**: Prints counts for each table seeded

#### Potential Issues ⚠️

1. **No Version Check**
   ```python
   cursor.execute("DELETE FROM workflow_transitions")  # Deletes ALL
   ```
   - Always deletes and re-inserts, even if config unchanged
   - Could add version check to skip re-seeding

2. **Special Rules Parsing**
   ```python
   rules = data.get("_special_rules", {})
   ```
   - Stores entire config as JSON in `config` column
   - But `workflow_router.py` expects specific fields like `threshold`
   - **COUPLING**: Schema expected by router must match JSON structure

### Component 4: Phase Templates (phase_simple.md)

#### Potential Issues ⚠️

1. **Skill Invocation Pattern**
   ```markdown
   Then invoke: `Skill(command: "prompt-builder")`
   → Capture stdout as `{COMPLETE_PROMPT}`
   ```
   - The orchestrator must capture stdout from the skill
   - **QUESTION**: How does the LLM capture stdout? The skill SKILL.md says:
     ```
     The script outputs the COMPLETE prompt to stdout
     ```
   - But LLMs can't directly capture stdout - they see tool output

2. **Missing Error Handling for Skill Failures**
   ```markdown
   **IF script returns exit code 1:**
   → Read stderr for error message
   ```
   - Good that it handles exit code 1
   - But what if the skill itself fails to invoke?

3. **Model Config Not Passed Correctly**
   ```markdown
   - model: {MODEL_CONFIG[agent_type]}
   ```
   - This assumes `MODEL_CONFIG` is available in template context
   - But `MODEL_CONFIG` is defined in Python scripts, not available to orchestrator
   - **INCONSISTENCY**: Template references variable that doesn't exist in orchestrator context

---

## Database Schema Analysis

### Tables Used by Deterministic System

| Table | Created By | Seeded By | Used By |
|-------|------------|-----------|---------|
| workflow_transitions | init_db.py (v13) | seed_configs.py | workflow_router.py |
| agent_markers | init_db.py (v13) | seed_configs.py | prompt_builder.py |
| workflow_special_rules | init_db.py (v13) | seed_configs.py | workflow_router.py |
| task_groups | init_db.py | PM via bazinga-db | prompt_builder.py, workflow_router.py |
| context_packages | init_db.py | Agents | prompt_builder.py |
| error_patterns | init_db.py | Agents | prompt_builder.py |
| orchestration_logs | init_db.py | Agents | prompt_builder.py |

### Schema Verification Needed

1. **task_groups.revision_count** - Does this column exist?
2. **task_groups.specializations** - Is this a JSON column?

---

## Security Analysis

### Addressed ✅

1. **Path Traversal**: `validate_template_path()` rejects `..` and absolute paths
2. **SQL Injection**: All queries use parameterized statements
3. **Transaction Safety**: Atomic seeding with rollback

### Remaining Concerns ⚠️

1. **Shell Command Injection**
   The SKILL.md files show commands like:
   ```bash
   --task-title "{task_title}"
   ```
   - If `task_title` contains shell metacharacters, could be problematic
   - **RECOMMENDATION**: Orchestrator should escape or use safer invocation

2. **No Input Validation on Args**
   ```python
   parser.add_argument("--task-title", default="")
   # No sanitization before use
   ```
   - Task title goes directly into prompt
   - Not a security issue but could allow prompt injection

---

## Testing Gaps

### Not Tested

1. **prompt_builder.py with missing DB** - Proceeds without DB, but untested
2. **workflow_router.py escalation logic** - Complex conditions untested
3. **config_seeder.py rollback on partial failure** - Transaction logic untested
4. **Phase template integration** - Does orchestrator correctly invoke skills?

### Recommended Tests

1. Unit tests for each Python script
2. Integration test: full orchestration flow with skills
3. Edge case: DB missing at prompt build time
4. Edge case: Agent file truncated (below MIN_AGENT_LINES)

---

## Inconsistencies Found

### 1. MODEL_CONFIG Reference Mismatch

**In templates:**
```markdown
model: {MODEL_CONFIG[agent_type]}
```

**In Python:**
```python
MODEL_CONFIG = load_model_config()  # Defined in workflow_router.py
```

**Problem:** Templates reference `MODEL_CONFIG` as if it's a template variable, but it's only defined in Python scripts. The orchestrator (an LLM) doesn't have access to Python variables.

**Impact:** Orchestrator might spawn agents with wrong models.

### 2. Security Sensitive Flag Ignored

**PM sets:**
```json
{
  "security_sensitive": true,  // Task group flag
}
```

**Router checks:**
```python
name = row[0].lower()
return "security" in name or "auth" in name  # Only checks NAME
```

**Problem:** PM can mark a task as security_sensitive, but router only checks task name.

**Impact:** Security tasks might not get SSE escalation if name doesn't contain "security" or "auth".

### 3. Token Budget Not Coordinated

**Specialization block:**
```python
if total_tokens + tokens <= budget["soft"]:
```

**Context block:**
```python
context_budget = int(budget["soft"] * allocation)
```

**Problem:** Both use parts of the same soft budget, but calculated independently. Total could exceed budget.

**Impact:** Prompts might exceed model context limits.

### 4. revision_count Column - VERIFIED ✅

**Router queries:**
```python
SELECT revision_count FROM task_groups WHERE ...
```

**Schema verified:** `task_groups` DOES have `revision_count INTEGER DEFAULT 0` (init_db.py:1266)

### 5. security_sensitive Flag - CONFIRMED BUG ❌

**PM Documentation says:**
```markdown
**Security Tasks** (`security_sensitive: true`):
  → security_sensitive: true
```

**Schema reality:**
- `task_groups` table has NO `security_sensitive` column
- `bazinga_db.py` update-task-group valid_flags: `{"status", "assigned_to", "revision_count", "last_review_status", "auto_create", "name", "specializations", "item_count"}`
- NO way to store or update `security_sensitive`

**Router implementation:**
```python
def check_security_sensitive(conn, session_id, group_id):
    name = row[0].lower()
    return "security" in name or "auth" in name  # Only checks NAME
```

**IMPACT:** PM's `security_sensitive: true` flag is completely ignored. Security tasks only get SSE escalation if their NAME happens to contain "security" or "auth" strings. This is a documentation-implementation mismatch.

---

## Recommendations

### Critical Fixes

1. **Fix conn.close() before sys.exit()** in prompt_builder.py marker validation
2. ~~**Verify revision_count column** exists in task_groups~~ ✅ VERIFIED - exists
3. **Add security_sensitive column** to task_groups schema OR update documentation
   - Option A: Add column + update bazinga_db.py + update workflow_router.py
   - Option B: Remove `security_sensitive: true` from PM documentation, rely on name-based detection
4. **Coordinate token budgets** between specialization and context blocks

### Medium Priority

5. **Add shell escaping** for task_title and other user inputs in SKILL.md commands
6. **Add version check** to seed_configs.py to avoid unnecessary re-seeding
7. **Document MODEL_CONFIG availability** - how does orchestrator get model values?

### Low Priority

8. **Improve token estimation** - consider using tiktoken or similar
9. **Add requirements_engineer** to prior reasoning query
10. **Add unit tests** for all Python scripts

---

## Questions for External Review

1. Is the overall architecture sound for deterministic prompt building?
2. Are there additional security concerns with the path validation approach?
3. Should token budgets be coordinated centrally rather than independently?
4. Is the escalation logic in workflow_router.py correct and complete?
5. How should MODEL_CONFIG values be made available to the orchestrator?

---

## Files for Review

- `.claude/skills/prompt-builder/scripts/prompt_builder.py` (639 lines)
- `.claude/skills/workflow-router/scripts/workflow_router.py` (270 lines)
- `.claude/skills/config-seeder/scripts/seed_configs.py` (191 lines)
- `templates/orchestrator/phase_simple.md` (partial)
- `bazinga/config/transitions.json` (246 lines)
- `bazinga/config/agent-markers.json` (92 lines)

---

## Appendix: Code Snippets

### A1: Path Validation (Security Fix)

```python
def validate_template_path(template_path):
    """Validate that template path is safe (no path traversal)."""
    ALLOWED_BASE = Path("templates/specializations").resolve()

    if Path(template_path).is_absolute():
        return None
    if ".." in str(template_path):
        return None

    resolved = Path(template_path).resolve()
    try:
        resolved.relative_to(ALLOWED_BASE)
        return resolved
    except ValueError:
        return None
```

### A2: Transaction Wrapping (Atomicity Fix)

```python
try:
    conn.execute("BEGIN TRANSACTION")
    # ... all seeding operations ...
    if success:
        conn.commit()
    else:
        conn.rollback()
except Exception as e:
    conn.rollback()
finally:
    conn.close()
```

### A3: Model Config Loading (Dynamic Config)

```python
def load_model_config():
    """Load model config from JSON file, fallback to defaults."""
    try:
        if Path(MODEL_CONFIG_PATH).exists():
            with open(MODEL_CONFIG_PATH) as f:
                data = json.load(f)
            config = {}
            for agent_name, agent_data in data.get("agents", {}).items():
                if isinstance(agent_data, dict) and "model" in agent_data:
                    config[agent_name] = agent_data["model"]
            if config:
                return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"WARNING: Failed to load model config: {e}", file=sys.stderr)
    return DEFAULT_MODEL_CONFIG
```

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

The external review confirmed and expanded on our analysis. Key findings:

### Confirmed Issues (Both Reviews Agree)

1. **security_sensitive flag non-functional** - Schema missing, router ignores PM flag
2. **DB connection resource leak** - sys.exit(1) before conn.close()
3. **Token budget not coordinated** - No global cap across all prompt sections
4. **Model config reference inconsistency** - Templates reference variable not available to orchestrator

### NEW Issues Identified by OpenAI

5. **QA FAIL escalation uses wrong counter**
   - `transitions.json` sets `escalation_check: true` for QA FAIL
   - But `workflow_router` escalates based on `revision_count`
   - PM only increments `revision_count` on TL CHANGES_REQUESTED
   - **Impact:** QA failure loops won't trigger SSE escalation as intended
   - **Fix:** Add `qa_attempts` column and track separately

6. **Script path mismatches in documentation**
   - Docs reference: `bazinga/scripts/prompt_builder.py`
   - Actual location: `.claude/skills/prompt-builder/scripts/prompt_builder.py`
   - **Impact:** Operator confusion, mis-invocation

7. **Missing merge workflow implementation**
   - Router returns `action: "spawn_merge"` but no reference implementation
   - How does developer perform merge? How are conflicts handled?

8. **Concurrency and SQLite locking**
   - config-seeder deletes/re-inserts transitions wholesale
   - If run mid-session, can race other operations
   - **Fix:** Lock seeding to init only; add retry/backoff

9. **Prompt injection risk**
   - Context packages, summaries, feedback injected verbatim
   - Could contain adversarial content
   - **Fix:** Add basic sanitization/quotas

### Incorporated Feedback

| Suggestion | Status | Rationale |
|------------|--------|-----------|
| Add `security_sensitive` column | **ACCEPT** | Critical for PM's security task routing |
| Add `qa_attempts` counter | **ACCEPT** | Essential for correct QA escalation |
| Add `tl_review_attempts` counter | **ACCEPT** | Separates TL review loops from revision_count |
| Global prompt budget cap | **ACCEPT** | Prevents context overflow |
| Use real tokenizer (tiktoken) | **DEFER** | Good idea but adds dependency; keep heuristic with safety margin |
| Script path wrappers | **DEFER** | Low priority; can update docs instead |
| Shell argument safety | **ACCEPT** | Security concern for skill invocation |

### Rejected Suggestions (With Reasoning)

| Suggestion | Status | Rationale |
|------------|--------|-----------|
| Persist seed_version to skip reseeding | **REJECT** | Over-engineering; seeding is fast and runs once per session |

---

## Updated Priority List

### P0 - Critical (Must Fix Before Production)

1. **Add security_sensitive column to task_groups**
   - Schema migration (v14)
   - Update bazinga_db.py valid_flags
   - Update workflow_router.py to check column

2. **Add qa_attempts column to task_groups**
   - Schema migration (v14)
   - Update QA FAIL handling to increment
   - Update workflow_router escalation logic

3. **Fix DB resource leak in prompt_builder.py**
   - Use try/finally or context manager
   - Ensure conn.close() always executes

4. **Add global prompt budget enforcement**
   - Calculate total after assembly
   - Trim lowest-priority sections if over budget
   - Log what was trimmed

### P1 - Important

5. **Update documentation paths**
   - Fix references to script locations

6. **Add shell argument escaping**
   - Skill invocations should pass params safely

7. **Add tl_review_attempts column**
   - Separate from revision_count for clarity

### P2 - Nice to Have

8. **Improve token estimation**
   - Consider tiktoken with fallback

9. **Document merge workflow**
   - Reference implementation for spawn_merge action
