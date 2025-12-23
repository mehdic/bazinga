# Agent Prompt Composition Bug: Analysis and Fix Plan

**Date:** 2025-12-15
**Context:** Orchestrator spawns agents with custom abbreviated prompts instead of full agent definitions
**Decision:** Fix prompt composition logic in orchestrator and related templates
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

The BAZINGA orchestrator is spawning agents (PM, Developer, QA, Tech Lead, etc.) with custom abbreviated prompts instead of including the full agent definition files. This causes agents to miss critical instructions, workflow rules, and behavioral constraints.

### Evidence

**PM Spawn (Resume Scenario):**
- Orchestrator runs `Read(.claude/agents/project_manager.md)` → 2508 lines loaded
- Spawned PM prompt contains ~100 lines of custom content
- **Missing:** 2500+ lines of PM instructions (scope preservation, BAZINGA rules, complexity scoring, etc.)

**Developer Spawn:**
- Orchestrator runs `Read(.claude/agents/developer.md)` → 1364 lines loaded
- Spawned Developer prompt contains ~120 lines (SPEC_BLOCK + custom task context)
- **Missing:** 1364 lines of Developer instructions (NO DELEGATION rules, status codes, tool restrictions, etc.)

### Impact

Without the full agent definitions, agents:
1. **Miss workflow rules** - Don't know the complete dev→QA→TL chain
2. **Miss status codes** - May not report READY_FOR_QA, BLOCKED correctly
3. **Miss constraints** - NO DELEGATION rules, tool restrictions not enforced
4. **Miss domain logic** - PM's complexity scoring, QA's 5-level challenge system, etc.

---

## Root Cause Analysis

### The Bug Pattern

```
1. Read(agents/{type}.md) → 1000+ lines loaded (stored internally)
2. Build custom prompt with task context → ~100 lines
3. Task(prompt: SPEC_BLOCK + custom_prompt) → Agent file NOT included
```

**Should be:**
```
1. Read(agents/{type}.md) → 1000+ lines loaded
2. Build task context → ~20 lines
3. base_prompt = agent_definition + task_context
4. full_prompt = CONTEXT_BLOCK + SPEC_BLOCK + base_prompt
5. Task(prompt: full_prompt) → All ~1400+ lines included
```

### Why This Happens

#### Cause 1: Ambiguous Resume Path Instructions

**Step 5 (Resume) in bazinga.orchestrate.md says:**
```markdown
**NOW jump to Phase 1** and spawn the PM agent with:
- The resume context (what was done, what's next)
- User's current request
- PM state loaded from database
```

**Missing:** Explicit instruction to include full `agents/project_manager.md` content.

Compare to **Step 1.2 (New Session)**:
```markdown
Build PM prompt by reading `agents/project_manager.md` and including:
...
prompt: [Full PM prompt from agents/project_manager.md with session_id context...]
```

The "jump to Phase 1" instruction is ambiguous - orchestrator interprets it as "include resume context items" rather than "follow Phase 1's full prompt building process."

#### Cause 2: Misleading Template Example

**prompt_building.md** provides this "Base Prompt" example:
```markdown
### Base Prompt
Always start with agent role and context:
```
You are a {AGENT_TYPE} in a Claude Code Multi-Agent Dev Team.

**GROUP:** {group_id}
**MODE:** {Simple|Parallel}
...
```

This example suggests creating a custom "You are a..." prompt rather than using the agent file content. The orchestrator sees this example and constructs similar custom prompts.

#### Cause 3: "SILENT PROCESSING" Misinterpretation

**phase_parallel.md lines 342-354:**
```markdown
**🔴🔴🔴 SILENT PROCESSING - DO NOT PRINT BLOCKS 🔴🔴🔴**

Process skill outputs SILENTLY:
...
**🔴 FORBIDDEN - DO NOT OUTPUT:**
- ❌ The context blocks
- ❌ The specialization blocks
- ❌ The full prompts
```

This instruction about NOT OUTPUTTING to the user may be misinterpreted as NOT INCLUDING in the prompt.

#### Cause 4: Cognitive Load / Context Compaction

With ~26,000 tokens in bazinga.orchestrate.md, the orchestrator may:
- Read the agent file early
- Lose track of its content during complex orchestration
- Default to building custom prompts from memory

---

## Proposed Solution

### Fix 1: Explicit Agent File Inclusion in Resume Path

**Current (Step 5):**
```markdown
**NOW jump to Phase 1** and spawn the PM agent with:
- The resume context (what was done, what's next)
- User's current request
- PM state loaded from database
- **🔴 CRITICAL: Original_Scope from Step 3.5**
```

**Fixed:**
```markdown
**NOW jump to Phase 1** and spawn the PM agent with:
- **🔴 FULL content of `agents/project_manager.md`** (MANDATORY - same as new session)
- The resume context (what was done, what's next)
- User's current request
- PM state loaded from database
- **🔴 CRITICAL: Original_Scope from Step 3.5**

**Prompt structure:**
```
FULL_PROMPT =
  [Optional: CONTEXT_BLOCK from context-assembler]
  + [Optional: SPEC_BLOCK from specialization-loader]
  + [MANDATORY: Full agents/project_manager.md content (~2500 lines)]
  + [Resume context section (~50 lines)]
```
```

### Fix 2: Rename and Clarify prompt_building.md

**Current confusing section:**
```markdown
### Base Prompt
Always start with agent role and context:
```
You are a {AGENT_TYPE}...
```

**Fixed:**
```markdown
### Task Context Section (APPENDED to agent file, NOT a replacement)

The task context is a SHORT section (~20 lines) appended to the full agent definition:
```markdown
---

## Current Task Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** {Simple|Parallel}
**BRANCH:** {branch}

**TASK:** {task_title}

**REQUIREMENTS:**
{task_requirements}

**COMMIT TO:** {branch}
**REPORT STATUS:** READY_FOR_QA or BLOCKED when complete
```

**🔴 CRITICAL: This is APPENDED to the full agent file, NOT used standalone.**

The complete prompt structure is:
```
FULL_PROMPT =
  CONTEXT_BLOCK (from context-assembler, ~200 tokens)
  + SPEC_BLOCK (from specialization-loader, ~800 tokens)
  + AGENT_DEFINITION (from agents/{type}.md, ~1400 lines)
  + TASK_CONTEXT (this section, ~20 lines)
```
```

### Fix 3: Add Enforcement Check Before Task() Call

Add to all phase templates (phase_simple.md, phase_parallel.md) before the Task() call:

```markdown
### 🔴 PRE-SPAWN VALIDATION (MANDATORY)

**Before calling Task(), verify prompt length:**

```python
MINIMUM_PROMPT_LENGTHS = {
    "project_manager": 2000,  # ~2500 lines
    "developer": 1200,        # ~1364 lines
    "senior_software_engineer": 1500,  # ~1700 lines
    "qa_expert": 1100,        # ~1200 lines
    "tech_lead": 900,         # ~1000 lines
    "investigator": 600,      # ~700 lines
    "requirements_engineer": 800  # ~900 lines
}

IF len(prompt.split('\n')) < MINIMUM_PROMPT_LENGTHS[agent_type]:
    ❌ PROMPT TOO SHORT | Expected {min} lines, got {actual} | Agent file NOT included - FIX REQUIRED
    → Re-read agents/{type}.md and include full content
```

**This catches the bug at spawn time.**
```

### Fix 4: Add Explicit Composition Formula

Add to bazinga.orchestrate.md overview section:

```markdown
## 🔴 AGENT PROMPT COMPOSITION FORMULA (MANDATORY)

**Every agent spawn MUST use this formula:**

```
FULL_PROMPT =
  CONTEXT_BLOCK        // From context-assembler (optional, ~200 tokens)
  + SPEC_BLOCK         // From specialization-loader (optional, ~800 tokens)
  + AGENT_DEFINITION   // 🔴 MANDATORY: Full Read(agents/{type}.md) content
  + TASK_CONTEXT       // Short task details (~20 lines)
```

**Expected sizes:**
| Component | Typical Size | Source |
|-----------|-------------|--------|
| CONTEXT_BLOCK | 0-200 tokens | context-assembler skill |
| SPEC_BLOCK | 0-900 tokens | specialization-loader skill |
| AGENT_DEFINITION | 1000-2500 lines | agents/{type}.md file |
| TASK_CONTEXT | 15-50 lines | Session/group/task details |

**🔴 AGENT_DEFINITION is NOT optional. If missing, agent lacks critical instructions.**
```

### Fix 5: Simplify Orchestrator (Optional - Larger Refactor)

Consider extracting prompt building into a dedicated skill:

```markdown
## prompt-builder Skill

**Purpose:** Centralize agent prompt composition to prevent custom prompt construction.

**Invocation:**
```
Skill(command: "prompt-builder")

Input context:
- agent_type: {developer|qa_expert|tech_lead|...}
- session_id: {session_id}
- group_id: {group_id}
- task_title: {title}
- task_requirements: {requirements}
- context_block: {optional}
- spec_block: {optional}
```

**Output:**
```
[PROMPT_START]
{Correctly composed full prompt with agent definition}
[PROMPT_END]
```

**Benefit:** Orchestrator can't construct custom prompts - must use skill.
```

---

## Implementation Priority

| Fix | Priority | Effort | Impact |
|-----|----------|--------|--------|
| Fix 1: Resume path | **P0 - Critical** | Low | Fixes immediate bug |
| Fix 3: Length validation | **P0 - Critical** | Low | Catches bug at runtime |
| Fix 4: Composition formula | **P1 - High** | Low | Prevents future drift |
| Fix 2: Rename template | **P2 - Medium** | Low | Clarifies intent |
| Fix 5: prompt-builder skill | **P3 - Nice to have** | Medium | Structural prevention |

---

## Risks and Mitigations

### Risk 1: Prompt Length Concerns
**Concern:** Including full agent file makes prompts very long (~1500+ lines).
**Mitigation:**
- This is by design - agent files contain critical instructions
- Context-assembler already handles token budgeting
- Split into CONTEXT_BLOCK + SPEC_BLOCK + agent_file + task_context is the intended structure

### Risk 2: Orchestrator Context Usage
**Concern:** Orchestrator processing 2500-line agent files increases its context usage.
**Mitigation:**
- Orchestrator reads file once, includes content in Task() prompt
- Task() spawns separate agent with that context
- Orchestrator's context is not bloated by agent file content in responses

### Risk 3: Backward Compatibility
**Concern:** Existing sessions may have been created with abbreviated prompts.
**Mitigation:**
- Fix is forward-looking - new spawns use correct prompts
- Resume logic already re-reads agent files
- No migration needed for existing sessions

---

## Verification Plan

### Test 1: PM Spawn (New Session)
```bash
/bazinga.orchestrate Implement a simple calculator

# Verify PM prompt includes:
# - Full agents/project_manager.md content (~2500 lines)
# - Session context (~20 lines)
# - Scope preservation section
```

### Test 2: PM Spawn (Resume)
```bash
# Create session, interrupt, resume
/bazinga.orchestrate continue

# Verify PM prompt includes:
# - Full agents/project_manager.md content (~2500 lines)
# - Resume context
# - PM state from database
```

### Test 3: Developer Spawn
```bash
# After PM planning completes

# Verify Developer prompt includes:
# - SPEC_BLOCK from specialization-loader
# - Full agents/developer.md content (~1364 lines)
# - Task context (~20 lines)
```

### Test 4: Length Validation
```bash
# Intentionally try to spawn with short prompt
# Verify error: "PROMPT TOO SHORT | Expected X lines, got Y"
```

---

## Decision Rationale

**Why include full agent files?**

1. **Agent files are the source of truth** - They contain workflow rules, status codes, constraints that agents MUST follow
2. **Custom prompts drift** - Without the full file, each spawn constructs slightly different instructions
3. **Templates specify this** - phase_simple.md and phase_parallel.md explicitly show `agent_definition = Read(agent_file_path)` followed by composition
4. **Consistency** - All agents get the same base instructions, only task context varies

**Why not summarize agent files?**

1. **Loss of critical details** - Summarization loses nuanced rules (e.g., specific escalation patterns)
2. **Maintenance burden** - Would need to update summaries when agent files change
3. **No benefit** - Agent context is separate from orchestrator context, so length isn't a concern

---

## Files to Modify

| File | Changes |
|------|---------|
| `.claude/commands/bazinga.orchestrate.md` | Fix 1: Resume path, Fix 4: Composition formula |
| `templates/orchestrator/phase_simple.md` | Fix 3: Length validation |
| `templates/orchestrator/phase_parallel.md` | Fix 3: Length validation |
| `templates/prompt_building.md` | Fix 2: Clarify template |
| `agents/orchestrator.md` | Add composition formula reference |

---

## Lessons Learned

1. **"Read" doesn't mean "include"** - Instructions to "read" a file may not be interpreted as "include its content"
2. **Examples become templates** - The prompt_building.md example was copied as a template rather than understood as documentation
3. **Resume paths need explicit rules** - "Jump to Phase X" is ambiguous without specifying what to bring along
4. **Length validation catches composition bugs** - A simple line count check would have caught this immediately

---

## References

- `templates/orchestrator/phase_simple.md` lines 126-165 (correct pattern)
- `templates/orchestrator/phase_parallel.md` lines 270-320 (correct pattern)
- `.claude/commands/bazinga.orchestrate.md` Step 5 (buggy resume path)
- `templates/prompt_building.md` (misleading example)
