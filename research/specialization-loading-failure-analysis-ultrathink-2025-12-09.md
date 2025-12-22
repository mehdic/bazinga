# Specialization Loading: Why It Keeps Failing (4th Attempt Analysis)

**Date:** 2025-12-09
**Context:** Specialization prompts still not being passed to agents despite 3 previous fix attempts
**Status:** ANALYSIS COMPLETE - ROOT CAUSE IDENTIFIED

---

## Problem Statement

After 3 implementation attempts, specialization blocks are STILL not appearing in agent prompts:

**Evidence from latest run:**
```
📝 SSE Prompt | Group: FDB | Model: sonnet
   Config: ... | Specializations: typescript, express | ...
```

But actual spawned prompt:
```
You are a SENIOR SOFTWARE ENGINEER implementing FDB Drug Interactions API Integration.

Session Context
- Session ID: bazinga_20251209_140421
...
```

**Missing:** The `## SPECIALIZATION GUIDANCE` block that should appear BEFORE the agent identity.

---

## Root Cause Analysis

### The Fundamental Misconception

**All 3 previous attempts made the same mistake:** We treated markdown templates as if they were a programming language with imports/includes.

**What we wrote:**
```markdown
**🔴 Spawn with Specializations:**

Read and follow `templates/orchestrator/spawn_with_specializations.md` with:
- session_id: {session_id}
- group_id: {group_id}
...
```

**What the orchestrator (Claude) sees:** "There's a reference to a file called spawn_with_specializations.md"

**What the orchestrator does:** Nothing. It doesn't use the Read tool. It doesn't extract steps. It just acknowledges the reference exists and moves on.

### Why "Read and follow X" Doesn't Work

The orchestrator is a Claude agent processing markdown templates. When it encounters:

```markdown
Read and follow `templates/orchestrator/spawn_with_specializations.md`
```

Claude interprets this as **documentation** (a note about what file exists), not as an **executable instruction** (like `Skill(command: "...")` or `Task(...)`).

**Comparison:**

| Instruction Type | Example | Claude's Interpretation | Result |
|-----------------|---------|------------------------|--------|
| Executable | `Skill(command: "bazinga-db")` | "I need to call this tool" | ✅ Tool called |
| Executable | `Task(subagent_type="general-purpose", ...)` | "I need to spawn this agent" | ✅ Agent spawned |
| Documentation | `Read and follow spawn_with_specializations.md` | "There's a reference to a file" | ❌ Nothing happens |
| Documentation | `Follow §Specialization Loading` | "There's a section about this" | ❌ Nothing happens |

### Evidence of the Pattern

The orchestrator.md file HAS detailed specialization loading steps (lines 1223-1299):
```markdown
## §Specialization Loading
...
**Step 4: Invoke specialization-loader skill**
...
Skill(command: "specialization-loader")
```

But this section is **DOCUMENTATION** within the orchestrator file. The phase templates (where actual spawning happens) just REFERENCE this section without INLINING the executable steps.

### The Execution Gap

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHAT WE BUILT                                 │
└─────────────────────────────────────────────────────────────────┘

orchestrator.md                    phase_simple.md
┌──────────────────┐              ┌──────────────────────────────┐
│ §Specialization  │              │ **Spawn with Specializations:**│
│ Loading          │              │                              │
│                  │   ← NO LINK  │ Read and follow              │
│ Step 1: Check... │              │ spawn_with_specializations.md│
│ Step 2: Query... │              │                              │
│ Step 3: Output...│              │ Task(...)                    │
│ Step 4: Skill()  │              │                              │
│ Step 5: Extract..│              └──────────────────────────────┘
│ Step 6: Prepend..│
└──────────────────┘

spawn_with_specializations.md
┌──────────────────────────────┐
│ (Same detailed steps)        │
│ ...never read by orchestrator│
└──────────────────────────────┘

RESULT: Orchestrator sees "Read and follow X", ignores it, just does Task(...)
```

---

## The Solution

### Principle: Inline Executable Instructions

The orchestrator needs to LITERALLY SEE the skill invocation in the template it's processing. Not a reference to another file, but the actual `Skill(command: "...")` call.

### Implementation

Replace the "Read and follow" pattern with **inlined executable steps**:

**BEFORE (broken):**
```markdown
**🔴 Spawn with Specializations:**

Read and follow `templates/orchestrator/spawn_with_specializations.md` with:
- session_id: {session_id}
- ...
```

**AFTER (working):**
```markdown
**🔴 Spawn with Specializations:**

**Step A: Load Specializations (if enabled)**

IF specializations.enabled in skills_config.json AND agent_type in enabled_agents:

  1. Output this context (REQUIRED - skill reads from conversation):
     ```
     Session ID: {session_id}
     Group ID: {group_id}
     Agent Type: {agent_type}
     Model: {model}
     Specialization Paths: {task_group.specializations from PM}
     ```

  2. Immediately invoke: Skill(command: "specialization-loader")

  3. Extract block between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]

  4. Prepend extracted block to base_prompt

**Step B: Spawn Agent**

Task(subagent_type="general-purpose", model={model}, description=desc, prompt=[specialization_block + base_prompt])
```

### Why This Works

1. **Literal Skill call:** The orchestrator sees `Skill(command: "specialization-loader")` as an executable instruction
2. **Context output:** The "Output this context" step produces text the skill reads
3. **No file references:** Everything needed is INLINE in the template

---

## Files to Modify

| File | Change |
|------|--------|
| `templates/orchestrator/phase_simple.md` | Replace 8 "Read and follow" blocks with inlined steps |
| `templates/orchestrator/phase_parallel.md` | Replace parallel spawn section with inlined steps |
| `templates/merge_workflow.md` | Replace 3 spawn points with inlined steps |

**DELETE (no longer needed):**
| File | Reason |
|------|--------|
| `templates/orchestrator/spawn_with_specializations.md` | Redundant - steps are now inlined |

---

## Lessons Learned

1. **Markdown templates are not code.** You can't "import" or "include" other files.
2. **Claude interprets literally.** If you want Claude to call a skill, write `Skill(command: "...")` literally.
3. **References are documentation.** "Read file X" or "Follow section Y" are notes, not instructions.
4. **Test with evidence.** Check the actual spawned prompt, not just the template code.

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review (2025-12-09)

**Key Feedback Incorporated:**

1. ✅ **Strict scoping markers** - Added `[SPEC_CTX_START group={group_id} agent={agent_type}]` and `[SPEC_CTX_END]` markers
2. ✅ **Sequential per-agent execution** - Isolation rule enforced: context→skill→spawn per agent before next
3. ✅ **Literal Skill invocation** - Every spawn point now has explicit `Skill(command: "specialization-loader")`
4. ⏳ **Keep spawn_with_specializations.md** - Retained as reference (not deleted) per reviewer suggestion

**Rejected Suggestions:**

| Suggestion | Reason |
|------------|--------|
| Parameterized skill invocation | Would require skill rewrite; current context-reading approach works once inlined |
| Pre-composition caching | Adds complexity; inline approach simpler to debug |

## Implementation Checklist

- [x] Inline specialization loading steps in phase_simple.md (8 spawn points)
- [x] Inline specialization loading steps in phase_parallel.md (parallel spawn)
- [x] Inline specialization loading steps in merge_workflow.md (3 spawn points)
- [ ] ~~Delete spawn_with_specializations.md~~ (kept as reference per OpenAI review)
- [ ] Test: Verify agent prompts contain `## SPECIALIZATION GUIDANCE` block

---

## Success Criteria

After this fix, spawned agent prompts should look like:

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override...

For this session, your identity is enhanced:

**You are a TypeScript Backend Developer specialized in Express/Node.js healthcare APIs.**

...

---

You are a SENIOR SOFTWARE ENGINEER implementing FDB Drug Interactions API Integration.
...
```

The `## SPECIALIZATION GUIDANCE` block MUST appear at the TOP of the prompt.
