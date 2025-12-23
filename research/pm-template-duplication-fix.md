# PM Template Duplication: Specializations Not Being Assigned

**Date:** 2025-12-11
**Context:** PM agent creates task groups without specializations despite MANDATORY instructions
**Decision:** Pending user approval
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (Gemini skipped)

---

## Problem Statement

The PM agent has TWO different templates for creating task groups via bazinga-db:

### Template 1: Step 3.5.4 (line 1720-1730)
```
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
Complexity: 5
Initial Tier: Developer
--specializations '["templates/specializations/01-languages/typescript.md", ...]'
```

### Template 2: Sub-step 5.3 (line 1922-1932)
```
bazinga-db, please create task group:

Group ID: [group_id like "A", "B", "batch_1", etc.]
Session ID: [session_id]
Name: [human readable task name]
Status: pending
Complexity: [1-10]
Initial Tier: [Developer | Senior Software Engineer]
Item_Count: [number of discrete tasks/items in this group]
```

**Key differences:**
| Field | Step 3.5.4 | Sub-step 5.3 |
|-------|-----------|--------------|
| `--specializations` | ✅ Present | ❌ Missing |
| `Item_Count` | ❌ Missing | ✅ Present |

**Result:** PM uses Sub-step 5.3 template (appears more "official" and is in the database persistence section), creating task groups with `specializations: null`.

---

## Root Cause Analysis

### Why PM Chose the Wrong Template

1. **Step ordering creates precedence illusion**
   - Step 3.5 appears earlier but looks like "planning"
   - Sub-step 5.3 appears in "Step 5: Save PM State to Database" - sounds like the "real" persistence step
   - PM likely thinks: "Step 3 = plan, Step 5 = actually save"

2. **Self-contained template trap**
   - Sub-step 5.3 template looks complete on its own
   - No cross-reference saying "use format from Step 3.5.4"
   - PM has no indication that another template exists with required fields

3. **Duplicate purpose confusion**
   - Both steps claim to "create task groups in database"
   - Step 3.5.4: "Store Specializations via bazinga-db"
   - Sub-step 5.3: "Create Task Groups in Database"
   - PM doesn't know which is authoritative

4. **Missing field awareness**
   - Step 3.5.4 doesn't have `Item_Count`
   - Sub-step 5.3 doesn't have `--specializations`
   - PM needs BOTH fields but each template only has one

---

## Proposed Solutions

### Option A: Merge Templates (Add --specializations to Sub-step 5.3)

**Change:** Add `--specializations` line to Sub-step 5.3 template.

```markdown
#### Sub-step 5.3: Create Task Groups in Database

For each task group, write this request and invoke:

```
bazinga-db, please create task group:

Group ID: [group_id like "A", "B", "batch_1", etc.]
Session ID: [session_id]
Name: [human readable task name]
Status: pending
Complexity: [1-10]
Initial Tier: [Developer | Senior Software Engineer]
Item_Count: [number of discrete tasks/items in this group]
--specializations '["path/to/specialization.md", ...]'  <-- ADD THIS
```
```

**Pros:**
- ✅ Quick fix - minimal changes
- ✅ Sub-step 5.3 becomes complete (has all required fields)
- ✅ Low risk of breaking other logic

**Cons:**
- ⚠️ Two templates still exist - maintenance burden
- ⚠️ If PM uses Step 3.5.4, will miss `Item_Count`
- ⚠️ Doesn't address root cause (template duplication)

**Risk Assessment:** LOW - Adding a field doesn't break anything

---

### Option B: Add Cross-Reference Note

**Change:** Add explicit note in Sub-step 5.3 referencing Step 3.5.4 format.

```markdown
#### Sub-step 5.3: Create Task Groups in Database

**⚠️ CRITICAL:** Use the FULL template from Step 3.5.4 which includes `--specializations`.
Do NOT use the abbreviated template below without specializations.

For each task group, write this request and invoke:
[existing template...]

**🔴 REMINDER:** Include `--specializations` as shown in Step 3.5.4!
```

**Pros:**
- ✅ Minimal change to existing structure
- ✅ Keeps specialization logic in one place (Step 3.5)
- ✅ PM gets explicit reminder

**Cons:**
- ⚠️ Relies on PM following cross-reference
- ⚠️ PM has to jump between sections
- ⚠️ Doesn't actually show the correct template in Sub-step 5.3
- ⚠️ LLMs often skip cross-references when they see a "complete-looking" template

**Risk Assessment:** MEDIUM - Cross-references are often ignored by LLMs

---

### Option C: Consolidate to ONE Canonical Template (RECOMMENDED)

**Change:**
1. Make Step 3.5.4 the ONLY place that creates task groups
2. REMOVE the template from Sub-step 5.3 entirely
3. Sub-step 5.3 becomes just "invoke bazinga-db for each group defined in Step 3.5"

**New Sub-step 5.3:**
```markdown
#### Sub-step 5.3: Persist Task Groups to Database

**Task groups were already defined in Step 3.5.4 with all required fields.**

For each task group you created in Step 3.5, ensure it was persisted to the database.

**Verification:**
- ✅ Each group has `--specializations` (from Step 3.5.4)
- ✅ Each group has `Item_Count` (added to Step 3.5.4)

If any groups were not persisted, invoke now:
```
Skill(command: "bazinga-db")
```

Note: Step 3.5.4 should have already created these groups. This step is for verification only.
```

**And update Step 3.5.4 to include Item_Count:**
```
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
Complexity: 5
Initial Tier: Developer
Item_Count: [number of discrete tasks/items]  <-- ADD THIS
--specializations '["templates/specializations/01-languages/typescript.md", ...]'
```

**Pros:**
- ✅ Single source of truth - ONE template only
- ✅ Eliminates template confusion forever
- ✅ All required fields in one place
- ✅ Clear workflow: Step 3.5 = define AND persist, Step 5.3 = verify
- ✅ LLM can't pick "wrong" template

**Cons:**
- ⚠️ Larger change to PM agent
- ⚠️ Need to verify Step 3.5 is always executed before Step 5.3
- ⚠️ If PM skips Step 3.5, no fallback in Step 5.3

**Risk Assessment:** LOW-MEDIUM - Cleaner architecture but more extensive change

---

## Impact Analysis

### What Could Break?

| Change | Option A | Option B | Option C |
|--------|----------|----------|----------|
| PM workflow order | No impact | No impact | Minor - Step 5.3 becomes verification |
| bazinga-db skill | No impact | No impact | No impact |
| Orchestrator | No impact | No impact | No impact |
| Resume scenarios | No impact | No impact | No impact |
| Dashboard | No impact | No impact | No impact |

### Compatibility Matrix

| Scenario | Option A | Option B | Option C |
|----------|----------|----------|----------|
| PM creates new session | ✅ Works | ⚠️ May skip | ✅ Works |
| PM resumes session | ✅ Works | ⚠️ May skip | ✅ Works |
| PM uses Step 3.5.4 only | ❌ Missing Item_Count | ❌ Missing Item_Count | ✅ Complete |
| PM uses Sub-step 5.3 only | ✅ Has specializations | ❌ Missing specializations | ✅ Redirects to 3.5.4 |
| PM uses both steps | ⚠️ Duplicate creation | ⚠️ Confusion | ✅ Clear: 3.5=create, 5.3=verify |

---

## Recommendation

**Option C (Consolidate to ONE template)** is recommended because:

1. **Addresses root cause** - Eliminates template duplication entirely
2. **Prevents future bugs** - Can't pick wrong template if only one exists
3. **Clearer mental model** - Step 3.5 = create, Step 5.3 = verify
4. **Complete template** - Single template has ALL required fields

**Implementation steps:**
1. Add `Item_Count` to Step 3.5.4 template
2. Rewrite Sub-step 5.3 as verification-only (no template)
3. Rebuild slash command
4. Test on client project

---

## Comparison to Alternatives

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Implementation effort | Low | Low | Medium |
| Root cause fix | No | No | **Yes** |
| Future maintenance | Higher | Higher | **Lower** |
| PM confusion risk | Medium | High | **Low** |
| Regression risk | Low | Medium | Low |
| **Overall score** | 6/10 | 4/10 | **9/10** |

---

## Decision Rationale

Pending user approval.

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

**Key Insight:** Option C alone is **insufficient**. Without hard gates at orchestrator and skill/DB layers, LLM drift will continue to produce incomplete task groups.

### Critical Issues Identified
1. **No systemic enforcement** - PM guidance relies on template discipline; bazinga-db accepts incomplete groups
2. **Two competing templates** - LLMs choose the "persistence" section (Sub-step 5.3), reinforcing the problem
3. **Missing backfill strategy** - No migration path for existing sessions with incomplete groups

### Suggested Enhancements (Beyond Option C)

| Enhancement | Description | Recommendation |
|-------------|-------------|----------------|
| **bazinga-db validation** | Reject create-task-group without required fields | ⚠️ Consider for future |
| **Orchestrator hard gate** | Enforce field-completeness before developer spawn | ⚠️ Consider for future |
| **Resume backfill** | Update PM Step 0.9 to also backfill item_count | ✅ Include in fix |
| **DRY templates** | Single canonical snippet referenced everywhere | ✅ Included in Option C |

### What We're Incorporating

1. **Option C as base** - Consolidate to one canonical template
2. **Update Step 0.9 backfill** - Add item_count backfill alongside specializations
3. **Strengthen validation gate language** - Already done in previous fix

### What We're Deferring (Future Enhancement)

1. **bazinga-db validation** - Would require Python changes, risk breaking existing sessions
2. **Orchestrator hard gate** - Good idea but increases complexity
3. **Spec-Kit-aware derivation** - Only needed for spec-kit mode

### Rationale for Deferral

The immediate fix should be minimal and low-risk. Option C + Step 0.9 backfill addresses the root cause without requiring:
- Python code changes to bazinga-db
- Database schema changes
- Orchestrator workflow changes

If the problem persists after this fix, we can add the harder gates.

---

## Revised Recommendation

**Option C+ (Consolidate + Strengthen Backfill)**

1. Add `Item_Count` to Step 3.5.4 template (single source)
2. Rewrite Sub-step 5.3 as verification-only (no template)
3. Update Step 0.9 to backfill BOTH specializations AND item_count
4. Rebuild slash command

**Risk:** LOW - Only documentation changes, no Python/DB changes

---

## References

- `agents/project_manager.md` - PM agent definition
- Step 3.5.4 (lines 1716-1732) - Template WITH specializations
- Sub-step 5.3 (lines 1916-1945) - Template WITHOUT specializations
