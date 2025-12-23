# Deterministic Orchestration Implementation Review (ULTRATHINK)

**Date:** 2025-12-16
**Context:** Critical review of Phase 4 implementation - updating orchestrator to use deterministic prompt-builder and workflow-router
**Decision:** Review implementation for gaps, broken logic, and non-deterministic paths
**Status:** REVIEWED
**Reviewed by:** OpenAI GPT-5

---

## Executive Summary

**Overall Assessment: 🔴 CRITICAL GAPS FOUND**

The orchestrator.md was updated with new sections for prompt-builder and workflow-router, BUT the phase templates that contain the actual spawn sequences were NOT updated. This creates a disconnect where:

1. Orchestrator says "use prompt-builder"
2. Orchestrator reads phase template
3. Phase template says "use context-assembler + specialization-loader"
4. **Result: OLD SYSTEM STILL IN USE**

---

## Part 1: What Was Implemented Correctly

### ✅ Phase 0-3: Infrastructure (100% Complete)

| Component | Status | Verification |
|-----------|--------|--------------|
| Config JSON files | ✅ | `bazinga/config/transitions.json`, `bazinga/config/agent-markers.json` |
| Database schema v13 | ✅ | `workflow_transitions`, `agent_markers`, `workflow_special_rules` tables |
| `seed_configs.py` | ✅ | Seeds 37 transitions, 7 markers, 5 rules |
| `prompt_builder.py` | ✅ | Generates 1557 lines (dev), 2539 lines (PM) |
| `workflow_router.py` | ✅ | Returns correct routing decisions |
| `prompt-builder` skill | ✅ | Thin wrapper calling script |
| `workflow-router` skill | ✅ | Thin wrapper calling script |
| `config-seeder` skill | ✅ | Calls seed_configs.py |

### ✅ Orchestrator.md New Sections Added

| Section | Line Range | Status |
|---------|------------|--------|
| Step 3.5: Config Seeding | ~1170-1180 | ✅ Added |
| §Prompt Building | ~2025-2115 | ✅ Added |
| §Workflow Routing | ~2182-2237 | ✅ Added |
| §DB Persistence Verification | ~2242-2275 | ✅ Updated |
| PRE-TASK VALIDATION | ~250-275 | ✅ Updated |
| Allowed Tools | ~183-190 | ✅ Updated |

### ✅ "INTENT WITHOUT ACTION" Examples Updated

All examples now reference prompt-builder correctly (lines 158, 173, 1824).

---

## Part 2: CRITICAL GAPS FOUND

### 🔴 GAP 1: Phase Templates NOT Updated (SEVERITY: CRITICAL)

**Location:**
- `templates/orchestrator/phase_simple.md` (1333 lines)
- `templates/orchestrator/phase_parallel.md` (915 lines)

**Problem:** These templates still contain:
- `Skill(command: "context-assembler")` - 13+ occurrences in phase_simple
- `Skill(command: "specialization-loader")` - 15+ occurrences in phase_simple
- TWO-TURN SPAWN SEQUENCE pattern throughout
- Manual `Read(agents/*.md)` instructions
- Manual prompt composition logic

**Evidence from phase_simple.md (lines 46-111):**
```markdown
### SPAWN IMPLEMENTATION AGENT (TWO-TURN SEQUENCE)

**TURN 1: Invoke Both Skills**

**A. Context Assembly:**
...
Then invoke: `Skill(command: "context-assembler")`

**B. Specialization Loading:**
...
Then invoke: `Skill(command: "specialization-loader")`
```

**Impact:** The orchestrator workflow is:
1. Orchestrator reads `§Prompt Building` section → "use prompt-builder"
2. Orchestrator reads `phase_simple.md` template → "use context-assembler + specialization-loader"
3. **Templates override** because they contain actual spawn instructions
4. **Result: Old system still executes**

**Fix Required:** Update both phase templates to use:
```markdown
### SPAWN SEQUENCE (DETERMINISTIC)

1. Output parameters for prompt-builder
2. Invoke: `Skill(command: "prompt-builder")`
3. Capture complete prompt from output
4. Invoke: `Task(...)` with captured prompt
```

---

### 🔴 GAP 2: workflow-router Not Actually Called (SEVERITY: CRITICAL)

**Problem:** The `§Workflow Routing` section documents HOW to use workflow-router, but the actual routing decisions in the phase templates still use hardcoded IF/ELSE logic.

**Evidence from phase_simple.md (lines 251-291):**
```markdown
### Step 2A.3: Route Developer Response

**IF Developer reports READY_FOR_QA:**
- Check testing_config.json for qa_expert_enabled
- IF QA enabled → proceed to Step 2A.4
- IF QA disabled → skip to Step 2A.6

**IF Developer reports BLOCKED:**
- Spawn Investigator...
```

This is hardcoded routing, NOT using workflow-router!

**Expected Pattern:**
```markdown
### Step 2A.3: Route Developer Response

1. Extract status code from Developer response
2. Invoke workflow-router:
   ```
   Current Agent: developer
   Response Status: {extracted_status}
   Session ID: {session_id}
   Group ID: {group_id}
   Testing Mode: {testing_mode}
   ```
   Then invoke: `Skill(command: "workflow-router")`
3. Follow returned action (spawn next_agent with prompt-builder)
```

**Impact:** All the sophisticated routing logic in `workflow_router.py` (escalation rules, testing mode, security overrides) is NOT being used. The templates use their own hardcoded logic.

---

### 🟡 GAP 3: Inconsistent Spawn Instructions (SEVERITY: MEDIUM)

**Problem:** The orchestrator.md has TWO conflicting spawn patterns:

**Pattern A (New - in §Prompt Building section):**
```markdown
1. Output parameters for prompt-builder
2. Invoke: `Skill(command: "prompt-builder")`
3. Capture the full prompt from output
4. Invoke: `Task(...)`
```

**Pattern B (Old - in Phase 2A/2B sections):**
```markdown
Read(file_path: "templates/orchestrator/phase_simple.md")
[Then follow template which uses context-assembler + specialization-loader]
```

The orchestrator says both:
- Line 2132: "Invoke: `Skill(command: "prompt-builder")`"
- Line 2124: "Read(file_path: "templates/orchestrator/phase_simple.md")"

**Impact:** Unclear which pattern takes precedence. If templates are read, they override with old approach.

---

### 🟡 GAP 4: PM Spawn Still Uses Old Pattern (SEVERITY: MEDIUM)

**Location:** `agents/orchestrator.md` lines 1576-1638

**Problem:** The PM spawn section (Step 1.2) still manually builds prompts:

```markdown
Build PM prompt by reading `agents/project_manager.md` and including:
- **Session ID from Step 0** - [current session_id created in Step 0]
- Previous PM state from Step 1.1
- User's requirements from conversation
- Task: Analyze requirements, decide mode, create task groups
```

This should use prompt-builder instead:
```markdown
1. Output parameters for prompt-builder:
   - Agent Type: project_manager
   - Session ID: {session_id}
   - PM State: {pm_state}
   ...
2. Invoke: `Skill(command: "prompt-builder")`
3. Task(...) with built prompt
```

---

### 🟡 GAP 5: Clarification Workflow PM Re-spawn (SEVERITY: MEDIUM)

**Location:** `agents/orchestrator.md` lines 1894-1927

**Problem:** PM re-spawn after clarification still uses inline prompt building:
```markdown
Task(
  subagent_type="general-purpose",
  description="PM planning with clarification",
  prompt=f"""
You are the Project Manager. You previously requested clarification...
"""
)
```

This should use prompt-builder with `--resume-context` parameter.

---

### 🟢 GAP 6: DB Verification Gates Reference prompt-builder (SEVERITY: LOW)

**Location:** Line 2265

**Problem:** Minor - verification gate mentions checking prompt-builder output but doesn't specify exact validation:
```markdown
**If prompt seems short:** Prompt-builder may have failed. Check stderr for errors.
```

Should specify: "Verify `lines=` metadata shows expected count (1200+ for developer, 2000+ for PM)"

---

### 🔴 GAP 7: Skill Scripts in Wrong Location (SEVERITY: CRITICAL)

**Problem:** The Python scripts for the new skills were placed in `bazinga/scripts/` instead of under the skill directories, violating the skill implementation guide pattern.

**Current (WRONG) structure:**
```
bazinga/
└── scripts/
    ├── seed_configs.py
    ├── prompt_builder.py
    └── workflow_router.py
```

**Expected (CORRECT) structure (per bazinga-db pattern):**
```
.claude/skills/
├── prompt-builder/
│   ├── SKILL.md
│   └── scripts/
│       └── prompt_builder.py
├── workflow-router/
│   ├── SKILL.md
│   └── scripts/
│       └── workflow_router.py
└── config-seeder/
    ├── SKILL.md
    └── scripts/
        └── seed_configs.py
```

**Evidence (correct pattern from bazinga-db):**
```
.claude/skills/bazinga-db/
├── SKILL.md
├── references/
│   └── schema.md
└── scripts/
    ├── bazinga_db.py
    └── init_db.py
```

**Impact:**
- Violates skill implementation guide
- Skills may not find scripts in production (path mismatch)
- Inconsistent with existing skill patterns
- May break `bazinga install` for client projects

**Fix Required:**
1. Move `bazinga/scripts/seed_configs.py` → `.claude/skills/config-seeder/scripts/seed_configs.py`
2. Move `bazinga/scripts/prompt_builder.py` → `.claude/skills/prompt-builder/scripts/prompt_builder.py`
3. Move `bazinga/scripts/workflow_router.py` → `.claude/skills/workflow-router/scripts/workflow_router.py`
4. Update SKILL.md files to reference correct paths
5. Update any orchestrator references to these scripts

---

## Part 3: Non-Deterministic Paths Still Present

### Path 1: Testing Mode Override

**Location:** Phase templates hardcode testing mode logic instead of using workflow-router.

**phase_simple.md lines 287-290:**
```markdown
- IF QA enabled → IMMEDIATELY continue to Step 2A.4
- IF QA disabled → IMMEDIATELY skip to Step 2A.6
```

**Problem:** This duplicates logic that should be in workflow-router's `testing_mode_disabled` and `testing_mode_minimal` special rules.

### Path 2: Escalation Logic

**phase_simple.md lines 574-576:**
```markdown
**IF revision count >= 1 (Developer failed once):**
- Escalate to SSE...
```

**Problem:** Hardcoded escalation threshold. Should use workflow-router's `escalation_after_failures` rule (threshold: 2).

### Path 3: Security Override

**phase_simple.md lines 743-746:**
```markdown
**🔴 SECURITY OVERRIDE:** If PM marked task as `security_sensitive: true`:
- ALWAYS spawn Senior Software Engineer for fixes
```

**Problem:** Should use workflow-router's `security_sensitive` rule.

---

## Part 4: What Works vs What's Broken

| Component | Works in Isolation? | Works in Orchestrator Flow? |
|-----------|---------------------|----------------------------|
| seed_configs.py | ✅ Yes | ✅ Yes (Step 3.5 added) |
| prompt_builder.py | ✅ Yes | ❌ No (templates don't call it) |
| workflow_router.py | ✅ Yes | ❌ No (templates don't call it) |
| prompt-builder skill | ✅ Yes | ❌ No (not invoked by templates) |
| workflow-router skill | ✅ Yes | ❌ No (not invoked by templates) |
| config-seeder skill | ✅ Yes | ✅ Yes |

**Bottom Line:** The infrastructure is complete and tested, but the **integration with orchestrator workflow is incomplete** because the phase templates were not updated.

---

## Part 5: Recommended Fixes

### Fix 1: Update Phase Templates (CRITICAL)

**Files:** `templates/orchestrator/phase_simple.md`, `phase_parallel.md`

**Action:** Replace ALL occurrences of:
- TWO-TURN SPAWN SEQUENCE → Single prompt-builder call
- `Skill(command: "context-assembler")` → Remove (prompt-builder handles)
- `Skill(command: "specialization-loader")` → Remove (prompt-builder handles)
- Manual `Read(agents/*.md)` → Remove (prompt-builder handles)
- Hardcoded routing logic → workflow-router calls

**Estimated effort:** ~2 hours (significant rewrite of both templates)

### Fix 2: Update PM Spawn Section (MEDIUM)

**File:** `agents/orchestrator.md` lines 1576-1638

**Action:** Replace manual prompt building with prompt-builder call.

### Fix 3: Update Clarification Re-spawn (MEDIUM)

**File:** `agents/orchestrator.md` lines 1894-1927

**Action:** Use prompt-builder with `--resume-context`.

### Fix 4: Add workflow-router to All Routing Steps (CRITICAL)

**Files:** Phase templates

**Action:** Replace hardcoded IF/ELSE routing with:
```markdown
1. Extract status from agent response
2. Invoke: `Skill(command: "workflow-router")`
3. Execute returned action
```

---

## Part 6: Risk Assessment

### If Left Unfixed

| Risk | Impact | Likelihood |
|------|--------|------------|
| Agents get abbreviated prompts | HIGH - Original bug not fixed | CERTAIN |
| Context not accumulated | HIGH - QA/TL miss Dev reasoning | CERTAIN |
| Escalation rules not applied | MEDIUM - Manual fallback exists | LIKELY |
| Testing mode not respected | MEDIUM - Manual fallback exists | LIKELY |
| Security overrides missed | HIGH - Security tasks mishandled | POSSIBLE |

### After Fixes Applied

| Improvement | Impact |
|-------------|--------|
| All prompts are full agent files | Original bug fixed |
| Context accumulates correctly | QA/TL get Dev reasoning |
| Routing is deterministic | Same input → same output |
| Single source of truth | Changes in JSON/DB apply immediately |

---

## Part 7: Verification Checklist

After applying fixes, verify:

- [ ] `grep -r "context-assembler" templates/orchestrator/` returns 0 results
- [ ] `grep -r "specialization-loader" templates/orchestrator/` returns 0 results
- [ ] `grep -r "TWO-TURN" templates/orchestrator/` returns 0 results
- [ ] `grep -c "prompt-builder" templates/orchestrator/phase_simple.md` ≥ 8
- [ ] `grep -c "workflow-router" templates/orchestrator/phase_simple.md` ≥ 4
- [ ] Integration test passes with prompt metadata showing 1200+ lines for developer

---

## Part 8: Conclusion

**Summary:**
- Phases 0-3 (infrastructure): ✅ 100% complete
- Phase 4 (orchestrator update): 🔴 ~30% complete
- Phase 5 (testing): ⏸️ Blocked by Phase 4 gaps

**Critical Issue:** The phase templates (`phase_simple.md`, `phase_parallel.md`) were NOT updated to use the new deterministic system. They still contain the old TWO-TURN SPAWN SEQUENCE with context-assembler and specialization-loader.

**Required Action:** Update phase templates before declaring implementation complete.

---

## Part 9: Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

OpenAI confirmed all critical gaps identified in this analysis and added additional considerations:

### Consensus Points (Incorporated)

| Finding | OpenAI Assessment | Action |
|---------|-------------------|--------|
| Phase templates use old pattern | ✅ Confirmed critical | Fix 1 |
| workflow-router not called | ✅ Confirmed critical | Fix 4 |
| PM spawns manual | ✅ Confirmed | Fix 2, Fix 3 |
| Skill scripts wrong location | ✅ Confirmed (user feedback) | Fix 5 (new) |

### Additional Points from OpenAI (Adopted)

| Point | Description | Incorporated? |
|-------|-------------|---------------|
| Preservation of enforcement gates | Post-spawn token tracking, reasoning-phase checks must be preserved when removing template logic | ✅ Added to Fix 1 notes |
| Fallback/error handling | Define fallback if prompt-builder or workflow-router fails | ✅ Added as Fix 6 |
| Observability | Log workflow-router inputs/outputs to DB for audit | ✅ Added as Fix 7 |
| CI guards | Block merges if templates contain old patterns | ✅ Added to verification checklist |
| Feature flag rollout | Add skills_config flag for controlled cutover | Deferred (complexity) |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Centralize spawns in helper flow | Over-engineering for current phase; address after core fixes |
| Performance token budgets | Already handled in prompt_builder.py |

---

## Part 10: Updated Fix List (Post-Review)

### Fix 1: Update Phase Templates (CRITICAL) ✅ Confirmed
- Files: `templates/orchestrator/phase_simple.md`, `phase_parallel.md`
- Replace TWO-TURN with prompt-builder
- **ADDITIONAL:** Preserve post-spawn token tracking logic

### Fix 2: Update PM Spawn Section (MEDIUM) ✅ Confirmed
- File: `agents/orchestrator.md`
- Use prompt-builder for initial PM spawn

### Fix 3: Update Clarification Re-spawn (MEDIUM) ✅ Confirmed
- File: `agents/orchestrator.md`
- Use prompt-builder with `--resume-context`

### Fix 4: Add workflow-router to All Routing Steps (CRITICAL) ✅ Confirmed
- Files: Phase templates
- Replace IF/ELSE with workflow-router calls

### Fix 5: Move Scripts to Skill Directories (CRITICAL) ✅ NEW
- Move `bazinga/scripts/*.py` → `.claude/skills/*/scripts/`
- Update SKILL.md references
- **ALSO:** Update `src/bazinga_cli/__init__.py` to copy scripts from new paths during `bazinga install`

### Fix 6: Add Fallback/Error Handling (MEDIUM) ✅ NEW from OpenAI
- If prompt-builder fails: fall back to minimal prompt, log warning
- If workflow-router fails: route to Tech Lead, log to DB

### Fix 7: Add Observability Logging (LOW) ✅ NEW from OpenAI
- Log workflow-router inputs/outputs to DB
- Include: agent_type, status, returned action, model

---

## Part 11: Updated Verification Checklist (Post-Review)

After applying fixes, verify:

- [ ] `grep -r "context-assembler" templates/orchestrator/` returns 0 results
- [ ] `grep -r "specialization-loader" templates/orchestrator/` returns 0 results
- [ ] `grep -r "TWO-TURN" templates/orchestrator/` returns 0 results
- [ ] `grep -c "prompt-builder" templates/orchestrator/phase_simple.md` ≥ 8
- [ ] `grep -c "workflow-router" templates/orchestrator/phase_simple.md` ≥ 4
- [ ] Scripts under `.claude/skills/*/scripts/` (not `bazinga/scripts/`)
- [ ] Integration test passes with prompt metadata showing 1200+ lines for developer
- [ ] Post-spawn token tracking preserved in templates
- [ ] Error fallback paths defined for prompt-builder and workflow-router

---

## Part 12: Conclusion (Updated)

**Summary:**
- Phases 0-3 (infrastructure): ✅ 100% complete BUT scripts in wrong location
- Phase 4 (orchestrator update): 🔴 ~30% complete
- Phase 5 (testing): ⏸️ Blocked by Phase 4 gaps

**Critical Issues (7 total):**
1. 🔴 Phase templates NOT updated (GAP 1)
2. 🔴 workflow-router NOT called (GAP 2)
3. 🟡 Inconsistent spawn instructions (GAP 3)
4. 🟡 PM spawn uses old pattern (GAP 4)
5. 🟡 Clarification re-spawn uses old pattern (GAP 5)
6. 🟢 DB verification incomplete (GAP 6)
7. 🔴 Scripts in wrong location (GAP 7) ← NEW

**Required Actions Before Implementation Complete:**
1. Move scripts to correct skill directories
2. Update phase templates to use prompt-builder and workflow-router
3. Update PM spawn sections
4. Add error fallbacks
5. Run integration test to verify

---

## References

- Research plan: `research/deterministic-orchestration-final-plan.md`
- Orchestrator: `agents/orchestrator.md`
- Phase simple: `templates/orchestrator/phase_simple.md`
- Phase parallel: `templates/orchestrator/phase_parallel.md`
- Skill implementation guide: `research/skill-implementation-guide.md`
- OpenAI review: `tmp/ultrathink-reviews/openai-review.md`
