# Developer Spawn UX Fixes: Ultrathink Analysis

**Date:** 2025-12-01
**Context:** User reported UX regression - task-to-developer mapping became unclear after parallel spawn system was introduced
**Decision:** Implement 4 fixes to improve clarity
**Status:** Implemented

---

## Problem Statement

User observed the following output during orchestration:

```
Running 4 developer agents... (ctrl+o to expand)
 ├─ SSE P0-NURSE-FE: Nurse App Frontend · 36 tool uses · 67.2k tokens
 │  ⎿ Initializing...
 ├─ SSE P0-NURSE-BE: Nurse Backend Services · 35 tool uses · 71.5k tokens
 │  ⎿ Update: backend/services/nurse-service/package.json
 ├─ SSE P0-MSG-BE: Messaging Backend · 34 tool uses · 58.4k tokens
 │  ⎿ Write: backend/services/messaging-service/src/channels/whatsappChannel.ts
 └─ Dev P1-DOCTOR-FE: Doctor Frontend · 30 tool uses · 86.8k tokens
    ⎿ Write: web/src/apps/doctor/__tests__/components/ObservanceStats.test.tsx
```

**Issues identified:**
1. "SSE" and "Dev" labels are cryptic abbreviations - not clear what tier is assigned
2. Task descriptions truncated to 30 chars - not enough context
3. Status updates don't show tier - lost context after spawn
4. Spawn message doesn't explain tier assignments upfront

---

## Proposed Solution

### Fix 1: Expand Task Descriptions to 90+ Characters

**Current (30 chars):**
```markdown
| PM Decision | Description |
|-------------|-------------|
| Developer | `Dev {group}: {task[:30]}` |
| Senior Software Engineer | `SSE {group}: {task[:30]}` |
```

**Proposed (90 chars):**
```markdown
| PM Decision | Description |
|-------------|-------------|
| Developer | `Dev {group}: {task[:90]}` |
| Senior Software Engineer | `SSE {group}: {task[:90]}` |
```

**Rationale:** 90 chars provides meaningful context while staying readable. Example:
- 30 chars: `Dev A: Implement user auth syst`
- 90 chars: `Dev A: Implement user authentication system with JWT tokens and refresh mechanisms for nurse app`

### Fix 2: Clearer Spawn Messages with Tier Assignments

**Current spawn message:**
```
📊 **Context Optimization Point**
About to spawn {parallel_count} developers in parallel.
💡 For optimal performance, consider running `/compact` now.
⏳ Continuing immediately...
```

**Initial proposal (explored but rejected - table with 60 chars):**
```
📋 **Developer Assignments:**
| Group | Tier | Model | Task |
|-------|------|-------|------|
| {group_id} | {tier_name} | {model} | {task[:60]} |
```
*Note: This table format was rejected in favor of the bullet list below for token efficiency and better readability.*

**Implemented spawn message (bullet list with 90 chars):**
```
🔨 **Phase {N} starting** | Spawning {parallel_count} developers in parallel

📋 **Developer Assignments:**
• {group_id}: {tier_name} ({model}) - {task[:90]}
...

💡 For ≥3 developers, consider `/compact` first.
⏳ Continuing immediately...
```

**Example (implemented format):**
```
🔨 **Phase 1 starting** | Spawning 4 developers in parallel

📋 **Developer Assignments:**
• P0-NURSE-FE: Senior Software Engineer (Sonnet) - Nurse App Frontend with auth integration
• P0-NURSE-BE: Senior Software Engineer (Sonnet) - Nurse Backend Services with API endpoints
• P0-MSG-BE: Senior Software Engineer (Sonnet) - Messaging Backend with WhatsApp channel
• P1-DOCTOR-FE: Developer (Haiku) - Doctor Frontend basic components

💡 For ≥3 developers, consider `/compact` first.
⏳ Continuing immediately... (Ctrl+C to pause. Resume via `/bazinga.orchestrate` after `/compact`)
```

**Rationale:** Bullet list is more token-efficient than table format. User sees upfront which tier handles which task.

### Fix 3: Include Tier in Status Updates

**Current status capsules:**
```
🔨 Group {id} complete | {summary}, {files}, {tests} ({coverage}%) | {status} → {next}
🔨 Group {id} implementing | {what's done} | {current_status}
```

**Proposed status capsules:**
```
🔨 {id} [{tier}/{model}] complete | {summary}, {files}, {tests} ({coverage}%) | {status} → {next}
🔨 {id} [{tier}/{model}] implementing | {what's done} | {current_status}
```

**Example:**
```
🔨 P0-NURSE-FE [SSE/Sonnet] complete | JWT auth + refresh, 5 files, 12 tests (92%) | READY_FOR_QA → QA
🔨 P1-DOCTOR-FE [Dev/Haiku] implementing | Basic components done | Tests running
```

**Rationale:** Tier context persists through the workflow - user knows which agent tier is being QA'd or reviewed.

### Fix 4: Add Missing subagent_type to Parallel Spawns

**Current (BUG - missing subagent_type):**
```
Task(model: models["A"], description: "Dev A: {task}", prompt: [Group A prompt])
Task(model: models["B"], description: "SSE B: {task}", prompt: [Group B prompt])
```

**Proposed (FIXED):**
```
Task(subagent_type="general-purpose", model=models["A"], description="Dev A: {task}", prompt=[Group A prompt])
Task(subagent_type="general-purpose", model=models["B"], description="SSE B: {task}", prompt=[Group B prompt])
```

**Rationale:** Without `subagent_type="general-purpose"`, agents may spawn with 0 tool uses (observed behavior documented in `research/parallel-spawn-subagent-type-bug-ultrathink.md`).

---

## Critical Analysis

### Pros

1. **Immediate clarity** - Users instantly understand tier assignments
2. **Full context** - 90 chars provides meaningful task descriptions
3. **Persistence** - Tier info flows through status updates
4. **Bug fix included** - Prevents 0 tool use failures
5. **No breaking changes** - Additive improvements only

### Cons

1. **Slightly more verbose** - Spawn message grows from 3 lines to 8+ lines
2. **Longer descriptions** - 90 chars vs 30 chars takes more horizontal space
3. **More template changes** - Multiple places need updating

### Trade-off Assessment

| Aspect | Before | After | Trade-off |
|--------|--------|-------|-----------|
| Description length | 30 chars | 90 chars | +More context, +horizontal space |
| Spawn message | 3 lines | 8+ lines | +Clarity, +verbosity |
| Status capsules | No tier | Tier+Model | +Context, +2 extra tokens |
| subagent_type | Missing | Present | +Bug fix, no downside |

**Verdict:** All trade-offs favor the proposed changes. Verbosity increase is justified by clarity gains.

---

## Implementation Details

### Files to Modify

1. **`.claude/commands/bazinga.orchestrate.md`** (primary)
   - Lines 1202-1203: Simple mode description table (30→90 chars)
   - Lines 2094-2095: Parallel mode description table (30→90 chars)
   - Lines 2068-2074: Context optimization checkpoint message
   - Lines 2099-2104: Spawn template (add subagent_type)
   - Lines 1228, 1234, 2119-2121: Status capsule templates

2. **`.claude/agents/orchestrator.md`** (source of truth)
   - Same sections as above (orchestrate.md is generated from this)

### Change Locations

**Fix 1: Description length (4 locations)**
```
Line 1202: Dev: {task[:40]} → Dev: {task[:90]}
Line 1203: SSE: {task[:40]} → SSE: {task[:90]}
Line 2094: Dev {group}: {task[:30]} → Dev {group}: {task[:90]}
Line 2095: SSE {group}: {task[:30]} → SSE {group}: {task[:90]}
```

**Fix 2: Spawn message (replace lines 2068-2074)**
```
Old: "About to spawn {parallel_count} developers in parallel."
New: Full table with Group, Tier, Model, Task columns
```

**Fix 3: Status capsules (5+ locations)**
```
Line 1228: 🔨 Group {id} complete → 🔨 {id} [{tier}/{model}] complete
Line 1234: 🔨 Group {id} implementing → 🔨 {id} [{tier}/{model}] implementing
Line 2119: Same pattern
Line 2120: Same pattern
Line 2121: Same pattern (blocked)
```

**Fix 4: subagent_type (lines 2100-2104)**
```
Old: Task(model: models["A"], description: ...)
New: Task(subagent_type="general-purpose", model=models["A"], description=...)
```

---

## Comparison to Alternatives

### Alternative 1: Keep 30 chars, add tooltip
- **Rejected:** No tooltip system exists in CLI output

### Alternative 2: Full task name (unlimited)
- **Rejected:** Would create very long lines, hard to scan

### Alternative 3: 60 chars (middle ground)
- **Considered:** Still too short for complex task names
- **User requested 90+:** Following user's explicit requirement

### Alternative 4: Add separate "Tier Legend" section
- **Rejected:** Extra cognitive load, information should be inline

---

## Decision Rationale

1. **User explicitly requested 90+ chars** - following their requirement
2. **All 4 fixes are additive** - no breaking changes
3. **Bug fix (subagent_type) is mandatory** - prevents real failures
4. **Clarity > brevity** for orchestration UX - user needs to understand agent assignments

---

## Lessons Learned

1. **Abbreviations need context** - "SSE" alone is unclear without model info
2. **Description truncation affects UX** - too aggressive truncation loses meaning
3. **Spawn messages are the primary visibility point** - worth investing in clarity
4. **Status persistence matters** - tier context shouldn't disappear after spawn

---

## Test Plan

1. **Manual test:** Run orchestration with 4 parallel developers
2. **Verify:** Spawn message shows tier assignment table
3. **Verify:** Descriptions show ~90 chars of task context
4. **Verify:** Status updates include `[tier/model]` suffix
5. **Verify:** No "0 tool uses" failures (subagent_type fix)

---

## Multi-LLM Review Integration

### Consensus Points (OpenAI Agreed)

1. **subagent_type fix is mandatory** - Must apply uniformly to all Task() calls
2. **Parser compatibility is critical** - Changing capsule format could break downstream tools
3. **Token/verbosity budget matters** - Long sessions can truncate; keep capsules compact

### Incorporated Feedback

| Suggestion | Action | Rationale |
|------------|--------|-----------|
| Keep "Group {id}" prefix for parser safety | **Adopted** | Preserves backward compatibility with response_parsing.md |
| Add tier hint as suffix, not prefix | **Adopted** | `🔨 Group {id} [SSE/Sonnet]` instead of `🔨 {id} [SSE/Sonnet]` |
| Use artifact for detailed table | **Partially adopted** | Use capsule with inline tier breakdown instead of full table (token savings) |
| Update shared templates | **Adopted** | Will update message_templates.md alongside orchestrator.md |
| Apply subagent_type fix uniformly | **Adopted** | All Task() calls must include it |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Use artifact link for spawn assignments | Adds complexity; inline tier list in capsule is sufficient and token-efficient |
| Configurable truncation setting | Over-engineering for this use case; user explicitly requested 90 chars |
| Update orchestrator_speckit.md | Out of scope for this fix; speckit has different workflow |
| Track current_tier in DB | Correct but out of scope; current fix focuses on initial display clarity |

### Revised Implementation Plan

**Token-conscious approach (user requirement):**

1. **Fix 1 (90 chars):** Simple string replacement `[:30]` → `[:90]` (minimal change)
2. **Fix 2 (spawn message):** Replace inline table with compact tier list:
   ```
   🔨 Phase {N} | Spawning {k} developers:
   • {group}: {tier} ({model}) - {task[:90]}
   ```
3. **Fix 3 (status capsules):** Add `[{tier}/{model}]` AFTER "Group {id}":
   ```
   🔨 Group {id} [SSE/Sonnet] complete | ...
   ```
4. **Fix 4 (subagent_type):** Add parameter to all parallel spawn templates

**Token budget:** Changes add ~50-100 tokens to orchestrator.md. Acceptable.

---

## References

- `research/parallel-spawn-subagent-type-bug-ultrathink.md` - Bug analysis
- `.claude/commands/bazinga.orchestrate.md` - Target file
- User's bug report showing unclear "SSE" vs "Dev" labels
- OpenAI review feedback (tmp/ultrathink-reviews/openai-review.md)
