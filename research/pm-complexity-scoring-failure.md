# PM Complexity Scoring Failure: Root Cause Analysis

**Date:** 2025-12-22
**Context:** Task groups created with `complexity=None` despite PM templates requiring complexity scoring
**Decision:** Add --complexity to bazinga-db CLI + enforcement gates
**Status:** ✅ Implemented & Verified (All phases complete + CLI tested)
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

When BAZINGA orchestration runs, task groups are created with `complexity=None` even though:
1. The PM agent template explicitly requires complexity scoring
2. The database schema has a `complexity INTEGER` column
3. Healthcare-sensitive tasks (patient records, medication ordering) were assigned to Developer tier instead of SSE

**Evidence from real session (bazinga_20251215_103357):**
```
NUR-ORDER: initial_tier=Developer, complexity=None, security_sensitive=0
NUR-RECORDS: initial_tier=Developer, complexity=None, security_sensitive=0
NUR-TRACK: initial_tier=Developer, complexity=None, security_sensitive=0
NUR-ADMIN: initial_tier=Developer, complexity=None, security_sensitive=0
```

---

## Root Cause Analysis

### The Complete Data Flow (Current - Broken)

```
PM Agent                    bazinga-db Skill              Database
   │                              │                          │
   │ 1. Reads pm_planning_steps.md │                          │
   │    (Step 3.5.4 template)      │                          │
   │                              │                          │
   │ 2. Outputs natural language:  │                          │
   │    "Complexity: 5"            │                          │
   │    "Initial Tier: Developer"  │                          │
   │                              │                          │
   │ 3. Skill interprets NL ──────►│                          │
   │                              │                          │
   │                              │ 4. Builds CLI command:    │
   │                              │    create-task-group      │
   │                              │    --initial_tier Dev     │
   │                              │    (NO --complexity!)     │
   │                              │                          │
   │                              │ 5. Executes command ─────►│
   │                              │                          │
   │                              │                          │ 6. INSERT with
   │                              │                          │    complexity=NULL
```

### Breaking Points Identified

#### 1. PM Template Says to Output Complexity (pm_planning_steps.md:163-174)
```markdown
### Step 3.5.4: Store via bazinga-db (CANONICAL TEMPLATE)

bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
Complexity: 5              <-- PM is told to output this
Initial Tier: Developer
...
```

#### 2. But CLI Has No --complexity Flag (bazinga_db.py:3371-3437)
```python
elif cmd == 'create-task-group':
    # Parse flags
    specializations = None
    item_count = None
    component_path = None
    initial_tier = None
    # NO complexity variable!

    # Flag parsing handles:
    # --specializations, --item_count, --component_path, --initial_tier
    # NO --complexity handler!
```

#### 3. Function Signature Missing Complexity (bazinga_db.py:1166-1171)
```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None,
                     specializations: Optional[List[str]] = None,
                     item_count: Optional[int] = None,
                     component_path: Optional[str] = None,
                     initial_tier: Optional[str] = None) -> Dict[str, Any]:
    # NO complexity parameter!
```

#### 4. update-task-group Valid Flags Missing Complexity (bazinga_db.py:3451)
```python
valid_flags = {"status", "assigned_to", "revision_count", "last_review_status",
               "auto_create", "name", "specializations", "item_count",
               "security_sensitive", "qa_attempts", "tl_review_attempts",
               "component_path", "initial_tier"}
# NO "complexity" in valid_flags!
```

#### 5. Database Schema HAS the Column (init_db.py:223)
```sql
complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
```

### Secondary Issue: Security Classification

The security keyword list in `pm_task_classification.md` and `model_selection.json` only includes auth/crypto terms:
```
auth, authentication, authorization, security, crypto, encryption,
password, jwt, oauth, saml, sso, bearer, credential
```

Missing domain-specific terms that should trigger SSE:
- Healthcare: `patient`, `medical`, `clinical`, `PHI`, `HIPAA`, `medication`, `drug`
- Financial: `payment`, `PCI`, `banking`, `financial`, `credit card`
- Privacy: `PII`, `GDPR`, `CCPA`, `privacy`

---

## Solution

### Part 1: Add --complexity to bazinga-db CLI

**Files to modify:**
1. `.claude/skills/bazinga-db/scripts/bazinga_db.py`
   - Add `complexity` parameter to `create_task_group()` function
   - Add `--complexity` flag parsing in CLI `create-task-group` command
   - Add `complexity` to `valid_flags` in `update-task-group` command
   - Add validation: must be integer 1-10

2. `.claude/skills/bazinga-db/SKILL.md`
   - Document `--complexity` parameter for create-task-group
   - Document `--complexity` in update-task-group

### Part 2: Update PM Templates (if needed)

Verify PM templates use correct CLI syntax:
- `templates/pm_planning_steps.md` - check Step 3.5.4 format

### Part 3: Add Domain-Specific Security Keywords (Separate PR)

Add to `bazinga/model_selection.json` and `templates/pm_task_classification.md`:
- Healthcare markers
- Financial markers
- Privacy markers

---

## Implementation Details

### bazinga_db.py Changes

**1. Update create_task_group function signature:**
```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None,
                     specializations: Optional[List[str]] = None,
                     item_count: Optional[int] = None,
                     component_path: Optional[str] = None,
                     initial_tier: Optional[str] = None,
                     complexity: Optional[int] = None) -> Dict[str, Any]:  # ADD
```

**2. Add complexity validation in function:**
```python
if complexity is not None:
    if not isinstance(complexity, int) or not 1 <= complexity <= 10:
        return {"success": False, "error": "complexity must be integer 1-10"}
```

**3. Update SQL INSERT to include complexity:**
```python
# In the INSERT statement, add complexity column
# In the ON CONFLICT UPDATE, add complexity update
```

**4. Add --complexity flag parsing in CLI:**
```python
complexity = None
# In the flag parsing loop:
elif arg_normalized == '--complexity' and i + 1 < len(cmd_args):
    try:
        complexity = int(cmd_args[i + 1])
        if not 1 <= complexity <= 10:
            print(json.dumps({"success": False, "error": "--complexity must be 1-10"}, indent=2), file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print(json.dumps({"success": False, "error": "--complexity must be an integer"}, indent=2), file=sys.stderr)
        sys.exit(1)
    i += 2
```

**5. Add to valid_flags for update-task-group:**
```python
valid_flags = {"status", "assigned_to", "revision_count", "last_review_status",
               "auto_create", "name", "specializations", "item_count",
               "security_sensitive", "qa_attempts", "tl_review_attempts",
               "component_path", "initial_tier", "complexity"}  # ADD
```

---

## Comparison to Alternatives

### Alternative 1: Natural Language Parsing
**Approach:** Have bazinga-db skill's LLM extract complexity from natural language
**Pros:** No code changes to CLI
**Cons:** Unreliable, adds latency, LLM might miss it
**Verdict:** Rejected - explicit parameters are more reliable

### Alternative 2: Derive Complexity from initial_tier
**Approach:** If initial_tier=SSE, assume complexity >= 4
**Pros:** No schema change needed
**Cons:** Loses granularity (4 vs 7 vs 10), backwards reasoning
**Verdict:** Rejected - complexity determines tier, not vice versa

### Alternative 3: Store in PM State JSON Only
**Approach:** Don't use task_groups.complexity, keep in pm_state JSON
**Pros:** No bazinga_db.py changes
**Cons:** Not queryable, inconsistent with schema, dashboard can't use it
**Verdict:** Rejected - defeats purpose of having the column

---

## Decision Rationale

**Chosen approach:** Add `--complexity` parameter to bazinga-db CLI

**Why:**
1. Database schema already expects this column
2. PM templates already tell PM to output complexity
3. Only missing piece is the CLI bridge
4. Explicit parameter is more reliable than NL parsing
5. Enables dashboard to show/filter by complexity
6. Enables orchestrator to make tier decisions based on stored complexity

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PM doesn't use new flag | Medium | Low | Update template example, clear docs |
| Backwards compatibility | Low | Low | complexity is optional, defaults to NULL |
| Migration needed | None | None | Column already exists, just unused |

---

## Success Criteria

After implementation:
- [ ] `create-task-group --complexity 5` stores 5 in database
- [ ] `update-task-group --complexity 7` updates complexity to 7
- [ ] PM planning produces task groups with non-NULL complexity
- [ ] Dashboard can display complexity scores
- [ ] High-complexity tasks (7+) route to SSE tier

---

## Lessons Learned

1. **Schema-first isn't enough:** Having a database column doesn't mean it gets populated
2. **Trace the full data flow:** PM → Skill → CLI → DB - any break loses data
3. **Template sync matters:** PM templates must match CLI capabilities
4. **Test with real data:** The nurse project exposed this gap that unit tests missed

---

## Multi-LLM Review Integration

### Critical Issues Identified by OpenAI GPT-5

#### 1. initial_tier Casing Mismatch (CONFIRMED)
**Issue:** pm_task_classification.md uses lowercase (`developer`, `senior_software_engineer`) but bazinga_db.py validates title-case (`Developer`, `Senior Software Engineer`).

**Resolution:** Fix documentation to use title-case. Code is correct.

#### 2. SQL Changes Missing from Original Plan (INCORPORATED)
**Issue:** Original plan didn't specify exact SQL changes for INSERT/UPDATE.

**Resolution:** Added detailed SQL implementation below.

#### 3. Backfill Logic Missing (INCORPORATED)
**Issue:** Step 0.9 (resume backfill) doesn't handle complexity.

**Resolution:** Add complexity to backfill logic - if missing and initial_tier=SSE, set complexity=4 minimum.

#### 4. Validator/Router Enforcement (INCORPORATED)
**Issue:** Relying only on PM to set complexity is brittle.

**Resolution:** Add validation gate in orchestrator - block PLANNING_COMPLETE if any task group has null complexity.

### Incorporated Feedback

1. **Explicit SQL Changes:** Added complete INSERT/UPDATE statements with complexity
2. **Validation Gate:** Add complexity presence check before proceeding with dev spawn
3. **Backfill Step 0.9:** Include complexity derivation for resumed sessions
4. **Test Cases:** Added unit test requirements for CLI parsing

### Rejected Suggestions (With Reasoning)

1. **Centralized deterministic classification skill:** Overkill for this fix. PM is already opus-tier and should calculate complexity correctly once CLI accepts it.

2. **Router-side fallback policy:** Creates hidden magic. Better to fail fast if PM doesn't provide complexity.

3. **Security keywords JSON config:** Separate concern - will address in follow-up PR. This PR focuses on complexity propagation.

---

## Revised Implementation Plan (Post-Review)

### Phase 1: bazinga_db.py Changes

**1. Function signature update:**
```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None,
                     specializations: Optional[List[str]] = None,
                     item_count: Optional[int] = None,
                     component_path: Optional[str] = None,
                     initial_tier: Optional[str] = None,
                     complexity: Optional[int] = None) -> Dict[str, Any]:
```

**2. Validation:**
```python
if complexity is not None:
    if not isinstance(complexity, int) or not 1 <= complexity <= 10:
        return {"success": False, "error": "complexity must be integer 1-10"}
```

**3. SQL INSERT (add to columns and values):**
```sql
INSERT INTO task_groups (id, session_id, name, status, assigned_to,
                        specializations, item_count, component_path,
                        initial_tier, complexity)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**4. SQL ON CONFLICT UPDATE (add complexity):**
```sql
ON CONFLICT(id, session_id) DO UPDATE SET
  name = COALESCE(excluded.name, task_groups.name),
  status = COALESCE(excluded.status, task_groups.status),
  ...
  complexity = COALESCE(excluded.complexity, task_groups.complexity)
```

**5. CLI flag parsing (create-task-group):**
```python
complexity = None
# In flag loop:
elif arg_normalized == '--complexity' and i + 1 < len(cmd_args):
    try:
        complexity = int(cmd_args[i + 1])
        if not 1 <= complexity <= 10:
            print(json.dumps({"success": False, "error": "--complexity must be 1-10"}), file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print(json.dumps({"success": False, "error": "--complexity must be integer"}), file=sys.stderr)
        sys.exit(1)
    i += 2
```

**6. update-task-group valid_flags:**
```python
valid_flags = {..., "complexity"}  # Add to existing set
```

### Phase 2: PM Template Updates

**pm_planning_steps.md Step 3.5.4 - Update canonical template:**
```markdown
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
--complexity 5
--initial_tier "Developer"
--item_count 3
--component_path 'frontend/'
--specializations '["templates/specializations/01-languages/typescript.md"]'
```

**pm_task_classification.md - Fix initial_tier casing:**
- Change `developer` → `Developer`
- Change `senior_software_engineer` → `Senior Software Engineer`

### Phase 3: Validation Gate

**pm_planning_steps.md - Add validation gate after Step 3.5.4:**
```markdown
### VALIDATION GATE (After Step 3.5.4)

IMMEDIATE SELF-CHECK after creating each task group:
1. Does it include Item_Count? ✓
2. Does it include --component-path? ✓
3. Does it include --specializations with non-empty array? ✓
4. Does it include --complexity (1-10)? ✓  <-- NEW

IF any missing → IMMEDIATELY invoke bazinga-db update-task-group
DO NOT proceed to Step 5 until ALL fields present.
```

### Phase 4: Backfill Logic

**pm_planning_steps.md Step 0.9 - Add complexity backfill:**
```markdown
2. **Check each group for missing fields:**
   ```
   FOR each task_group:
     needs_specializations = task_group.specializations is null OR empty
     needs_item_count = task_group.item_count is null OR 0
     needs_complexity = task_group.complexity is null  <-- NEW
   ```

3. **Backfill complexity if missing:**
   - If initial_tier = "Senior Software Engineer" → set complexity = 4 (minimum SSE)
   - If initial_tier = "Developer" → set complexity = 2 (default low)
   - Log: "Backfilled complexity={N} based on initial_tier"
```

### Phase 5: Documentation

**SKILL.md - Update command docs:**
```markdown
python3 .../bazinga_db.py --quiet create-task-group \
  "<group_id>" "<session_id>" "<name>" [status] [assigned_to] \
  [--specializations '<json_array>'] [--item_count N] [--initial_tier "<tier>"] \
  [--component_path "<path>"] [--complexity N]

Parameters:
- `complexity`: Task complexity score (1-10). 1-3=Low (Developer), 4-6=Medium (SSE), 7-10=High (SSE)
```

---

## Test Cases Required

1. **CLI parsing:**
   - `create-task-group A sess "Name" --complexity 5` → stores 5
   - `create-task-group A sess "Name" --complexity 0` → error (out of range)
   - `create-task-group A sess "Name" --complexity 11` → error (out of range)
   - `create-task-group A sess "Name" --complexity abc` → error (not integer)

2. **Update:**
   - `update-task-group A sess --complexity 7` → updates to 7

3. **Integration:**
   - PM planning creates group with complexity=5 → DB stores 5
   - Dashboard shows complexity column

---

## References

- PM Agent: `agents/project_manager.md`
- PM Planning Steps: `templates/pm_planning_steps.md`
- PM Task Classification: `templates/pm_task_classification.md`
- bazinga-db CLI: `.claude/skills/bazinga-db/scripts/bazinga_db.py`
- Database Schema: `.claude/skills/bazinga-db/scripts/init_db.py`
- Session with issue: `bazinga_20251215_103357` (nurse management project)
- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
