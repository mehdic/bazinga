# Parallel Spawn subagent_type Bug: Ultrathink Analysis

**Date:** 2025-11-28
**Context:** User observed "senior_software_engineer" agents with 0 tool uses, then "developer" with sonnet fallback
**Decision:** This is a BUG that needs fixing
**Status:** Identified - Not Yet Fixed

---

## Problem Statement

User observed the following behavior during orchestration:

```
📋 ORCHESTRATOR: Spawning Phase 2 developers (2 Senior Software Engineers in parallel)...

  🔄 Phase 2 Developer Spawn:
  1. P2-MEDICAL (Senior/Sonnet) - Medical Records Access
  2. P2-COMMS (Senior/Sonnet) - Multi-Channel Communication

⏺ 2 senior_software_engineer agents finished (ctrl+o to expand)
   ├─ SSE P2-MEDICAL records · 0 tool uses  ← PROBLEM: No work done!
   │  ⎿ Done
   └─ SSE P2-COMMS messaging · 0 tool uses  ← PROBLEM: No work done!
      ⎿ Done

⏺ 🔄 ORCHESTRATOR: Agent type correction - using developer with sonnet model for complex tasks.

  Running 2 developer agents… (ctrl+o to expand)
   ├─ Dev P2-MEDICAL records · 26 tool uses · 49.9k tokens  ← Fallback worked
   │  ⎿ Write: backend/services/medical-records-service/src/models/MedicalRecord.ts
   └─ Dev P2-COMMS messaging · 19 tool uses · 53.4k tokens  ← Fallback worked
      ⎿ Write: backend/services/messaging-service/src/integrations/whatsapp.ts
```

**The questions:**
1. Why did "senior_software_engineer" agents do 0 tool uses?
2. Why did it fallback to "developer" with sonnet?
3. Is this expected behavior or a bug?

---

## Root Cause Analysis

### Finding 1: Valid subagent_type Values

The Task tool ONLY accepts these `subagent_type` values:
- `general-purpose` ← The only one for dev work
- `statusline-setup`
- `Explore`
- `Plan`
- `claude-code-guide`

**`senior_software_engineer` and `developer` are NOT valid subagent_type values.**

### Finding 2: Inconsistent Documentation

**Simple Mode (Section: "Step 2A.1: Spawn Developer") - CORRECT:**

    **Spawn:** Task(subagent_type="general-purpose", model=MODEL_CONFIG[tier], description=desc, prompt=[prompt])

✅ Explicitly includes `subagent_type="general-purpose"`

**Parallel Mode (Section: "Step 2B.1: Spawn Multiple Developers") - MISSING subagent_type:**

    Task(model: models["A"], description: "Dev A: {task}", prompt: [Group A prompt])
    Task(model: models["B"], description: "SSE B: {task}", prompt: [Group B prompt])

❌ **Missing `subagent_type` parameter entirely!**

### Finding 3: What Happened at Runtime

1. **Orchestrator read the parallel spawn template** which doesn't specify `subagent_type`
2. **Without explicit subagent_type**, the orchestrator may have:
   - Tried to infer type from description ("SSE" → senior_software_engineer)
   - Used tier name as subagent_type directly
3. **Since `senior_software_engineer` is invalid**, Claude Code created empty/non-functional agents
4. **Result: 0 tool uses** - agents completed immediately doing nothing
5. **Fallback kicked in**: "Agent type correction - using developer with sonnet model"
6. **Second spawn worked** because it used a valid approach (even if description said "developer")

### Finding 4: The "Agent type correction" Message

This message suggests there IS a fallback mechanism somewhere that:
1. Detects when an invalid subagent_type was used
2. Corrects to use a working configuration
3. Re-spawns with sonnet model

This fallback is a **symptom**, not the fix. The bug is that the orchestrator tried an invalid approach first.

---

## Evidence from Codebase

### Correct Patterns (with subagent_type):

| Section | Pattern | Status |
|---------|---------|--------|
| Step 2A.1 (Simple Mode Spawn) | `Task(subagent_type="general-purpose", model=...)` | ✅ Correct |
| Step 2A.3 (ESCALATE_SENIOR routing) | `Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], ...)` | ✅ Correct |
| Step 2A.3 (INCOMPLETE routing) | `Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], ...)` | ✅ Correct |
| Step 2A.3 (revision escalation) | `Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], ...)` | ✅ Correct |

### Incorrect Patterns (missing subagent_type):

| Section | Pattern | Status |
|---------|---------|--------|
| Step 2B.1 (Parallel Mode Spawn) | `Task(model: ..., description: ..., prompt: ...)` | ❌ **BUG** |

---

## Verdict

### Is this a bug? **YES**

**Bug Type:** Documentation/Instruction Error in Parallel Mode

**Severity:** Medium-High
- Causes wasted tokens (agents do nothing)
- Causes confusion (unclear what happened)
- Causes delay (fallback mechanism adds latency)
- But: fallback eventually works, so not a blocker

**Root Cause:** The parallel mode spawn instructions (Section: "Step 2B.1: Spawn Multiple Developers in Parallel") are missing the required `subagent_type="general-purpose"` parameter.

### Why Simple Mode Works but Parallel Mode Fails

- **Simple Mode** has explicit `Task(subagent_type="general-purpose", model=..., ...)` ✅
- **Parallel Mode** has only `Task(model: ..., ...)` without subagent_type ❌

The orchestrator faithfully follows the instructions it's given. When instructions are incomplete (missing subagent_type), unexpected behavior occurs.

---

## Recommended Fix

### Change Required in `agents/orchestrator.md`

**Current (Section: "Step 2B.1: Spawn Multiple Developers in Parallel"):**

    **Spawn ALL in ONE message (MAX 4 groups):**
    Task(model: models["A"], description: "Dev A: {task}", prompt: [Group A prompt])
    Task(model: models["B"], description: "SSE B: {task}", prompt: [Group B prompt])
    ... # MAX 4 Task() calls

**Fixed (consistent `=` syntax for all parameters):**

    **Spawn ALL in ONE message (MAX 4 groups):**
    Task(subagent_type="general-purpose", model=models["A"], description="Dev A: {task}", prompt=[Group A prompt])
    Task(subagent_type="general-purpose", model=models["B"], description="SSE B: {task}", prompt=[Group B prompt])
    ... # MAX 4 Task() calls

### Additional Consistency Check

Search for ALL Task() calls in orchestrator.md and ensure they ALL have `subagent_type="general-purpose"`.

---

## Why This Design (general-purpose for all devs)?

The architecture uses:
- **subagent_type** = `general-purpose` → Determines the agent's capabilities/tools
- **model** = `haiku`/`sonnet`/`opus` → Determines the intelligence level
- **prompt** = developer.md or senior_software_engineer.md content → Determines the behavior/expertise

This separation allows:
1. Same toolset for all developers (general-purpose gives them full tools)
2. Different intelligence (haiku for simple, sonnet for complex)
3. Different instructions (senior has additional mandatory skills, stricter requirements)

**`senior_software_engineer` is an AGENT DEFINITION (prompt content), not a subagent_type.**

---

## Expected Behavior After Fix

```
📋 ORCHESTRATOR: Spawning Phase 2 developers (2 Senior Software Engineers in parallel)...

  Running 2 general-purpose agents with sonnet model... (ctrl+o to expand)
   ├─ SSE P2-MEDICAL records · ~25 tool uses · ~50k tokens
   │  ⎿ Write: backend/services/medical-records-service/src/models/MedicalRecord.ts
   └─ SSE P2-COMMS messaging · ~20 tool uses · ~50k tokens
      ⎿ Write: backend/services/messaging-service/src/integrations/whatsapp.ts
```

No "0 tool uses", no "Agent type correction" fallback, no wasted spawns.

---

## Lessons Learned

1. **subagent_type is NOT the agent name** - It's the capability set
2. **Developer/Senior distinction is in the prompt**, not the subagent_type
3. **All Task() calls must explicitly include subagent_type** - Don't rely on inference
4. **Documentation consistency matters** - One correct pattern + one incorrect pattern = bugs

---

## References

- `agents/orchestrator.md` - Section "Step 2B.1: Spawn Multiple Developers in Parallel" (bug location)
- `agents/orchestrator.md` - Section "Step 2A.1: Spawn Developer" (correct pattern)
- Task tool documentation in Claude Code system prompt (defines valid subagent_type values)
- User's bug report showing the symptom (0 tool uses, fallback message)
