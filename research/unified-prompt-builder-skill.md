# Unified Prompt Builder Skill - Ultrathink Analysis

**Date:** 2025-12-16
**Context:** Can prompt-builder skill internally invoke specialization-loader and context-assembler?
**Decision:** PENDING USER APPROVAL
**Status:** Proposed
**Reviewed by:** PENDING LLM REVIEW

---

## Executive Summary

**User's Request:** Instead of orchestrator calling 3 skills sequentially (specialization-loader → context-assembler → prompt-builder), have orchestrator call ONLY prompt-builder, which internally orchestrates the other skills.

**Finding:** This IS possible according to Claude Code documentation.

**Key Evidence:**
1. [Agent SDK docs](https://code.claude.com/docs/en/skills): "Enable Skills by including 'Skill' in your `allowed_tools` configuration"
2. [Lee Han Chung's deep dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/): "Skills can build on each other... Skills stack together"
3. [Mikhail Shilkov](https://mikhail.io/2025/10/claude-code-skills/): "Skills are composable"

---

## Part 1: Current Flow (What We Planned)

```
Orchestrator
    │
    ├──→ Skill(command: "specialization-loader")
    │         └── Returns: SPEC_BLOCK
    │
    ├──→ Skill(command: "context-assembler")
    │         └── Returns: CONTEXT_BLOCK
    │
    └──→ Skill(command: "prompt-builder")
              └── Receives: SPEC_BLOCK, CONTEXT_BLOCK, agent_type, etc.
              └── Calls: Python script
              └── Returns: COMPLETE_PROMPT
```

**Problems with this approach:**
1. Orchestrator must manage 3 skill invocations per agent spawn
2. Orchestrator must capture and pass outputs between skills
3. More complex orchestrator logic (still some LLM interpretation)
4. 3 tool calls instead of 1

---

## Part 2: Proposed Flow (User's Request)

```
Orchestrator
    │
    └──→ Skill(command: "prompt-builder")
              │
              ├──→ Skill(command: "specialization-loader")
              │         └── Returns: SPEC_BLOCK
              │
              ├──→ Skill(command: "context-assembler")
              │         └── Returns: CONTEXT_BLOCK
              │
              └──→ Bash: python3 prompt_builder.py
                        └── Assembles: SPEC_BLOCK + CONTEXT_BLOCK + AGENT_FILE + TASK
                        └── Returns: COMPLETE_PROMPT
```

**Benefits:**
1. Orchestrator makes ONE skill call per agent spawn
2. All prompt composition logic encapsulated in one skill
3. Simpler orchestrator (truly thin coordination layer)
4. prompt-builder skill owns the entire composition process
5. Easier to test and debug (single entry point)

---

## Part 3: Technical Feasibility Analysis

### 3.1 Can Skills Invoke Other Skills?

**YES** - Based on documentation:

1. **allowed-tools supports Skill:**
   ```yaml
   allowed-tools: [Skill, Bash, Read]
   ```
   This enables the skill to invoke other skills.

2. **Skills run inline:**
   Skills don't spawn sub-agents. They inject instructions into the main conversation.
   When prompt-builder invokes specialization-loader, it's the same Claude instance
   reading different instructions.

3. **Skills are composable:**
   > "Skills stack together. Claude automatically identifies which skills are needed
   > and coordinates their use." — Lee Han Chung

4. **No "same skill twice" restriction applies:**
   The restriction is "Can't invoke same skill twice simultaneously."
   prompt-builder calling specialization-loader is fine (different skills).

### 3.2 How Skill-to-Skill Invocation Works

```
1. Orchestrator: Skill(command: "prompt-builder")

2. System loads prompt-builder SKILL.md
   - Claude reads instructions
   - allowed-tools: [Skill, Bash, Read] becomes active

3. prompt-builder instructions say: "Invoke specialization-loader"

4. Claude (still in prompt-builder context): Skill(command: "specialization-loader")

5. System loads specialization-loader SKILL.md
   - Claude reads THOSE instructions
   - Executes specialization-loader workflow
   - Returns composed identity block

6. Claude returns to prompt-builder context
   - Has the SPEC_BLOCK output
   - Continues with next step

7. prompt-builder instructions say: "Invoke context-assembler"

8. Same process repeats for context-assembler

9. prompt-builder calls Python script with both blocks

10. Returns COMPLETE_PROMPT to orchestrator
```

### 3.3 Potential Issues & Mitigations

| Issue | Risk | Mitigation |
|-------|------|------------|
| Context overflow | Medium | Keep each skill focused, use progressive disclosure |
| Nested skill failure | Low | Error handling in prompt-builder SKILL.md |
| Output capture | Low | Skills return output as text, Claude captures naturally |
| Allowed-tools cascade | None | Each skill has its own allowed-tools; parent doesn't inherit child's |
| Skill recursion | None | We're not calling same skill recursively |

### 3.4 What Changes from Original Plan

| Component | Original Plan | New Plan |
|-----------|---------------|----------|
| Orchestrator calls | 3 skills per spawn | 1 skill per spawn |
| prompt-builder allowed-tools | `[Bash, Read]` | `[Skill, Bash, Read]` |
| prompt-builder SKILL.md | ~100 lines | ~200 lines (includes orchestration) |
| Python script | Same | Same |
| specialization-loader | Called by orchestrator | Called by prompt-builder |
| context-assembler | Called by orchestrator | Called by prompt-builder |

---

## Part 4: Revised prompt-builder Skill Design

### 4.1 Updated SKILL.md Structure

```markdown
---
name: prompt-builder
description: Builds complete agent prompts with specialization and context. Use before spawning any agent.
version: 2.0.0
allowed-tools: [Skill, Bash, Read]
---

# Prompt Builder Skill

You are the prompt-builder skill. You build COMPLETE agent prompts by:
1. Invoking specialization-loader to get tech-specific identity
2. Invoking context-assembler to get relevant context
3. Calling Python script to assemble final prompt with full agent file

## When to Invoke

Before spawning ANY agent (Developer, SSE, QA, Tech Lead, PM, Investigator, RE).
This is the ONLY skill the orchestrator needs to call for prompt building.

## Prerequisites

- specialization-loader skill must exist
- context-assembler skill must exist
- bazinga/scripts/prompt_builder.py must exist
- Database must be seeded with configs

## Your Task

### Step 1: Parse Input Context

Extract from orchestrator's message:
- agent_type (required): developer, qa_expert, tech_lead, etc.
- session_id (required)
- group_id (for non-PM agents)
- task_title
- task_requirements
- branch
- mode (simple/parallel)
- testing_mode (full/minimal/disabled)
- qa_feedback (if retry)
- tl_feedback (if changes requested)
- pm_state (for PM spawns)
- resume_context (for PM resume)

### Step 2: Get Specialization Block

**Invoke the specialization-loader skill:**

```
Skill(command: "specialization-loader")
```

Provide context in your message before invoking:
```
Build specialization for:
- Agent Type: {agent_type}
- Session ID: {session_id}
```

Capture the returned SPEC_BLOCK (composed identity string).

**If specialization-loader returns empty or fails:**
- Continue without spec block (agent file is still included)
- Note the failure in metadata

### Step 3: Get Context Block

**Invoke the context-assembler skill:**

```
Skill(command: "context-assembler")
```

Provide context in your message before invoking:
```
Assemble context for:
- Agent Type: {agent_type}
- Session ID: {session_id}
- Group ID: {group_id}
```

Capture the returned CONTEXT_BLOCK.

**If context-assembler returns empty or fails:**
- Continue without context block
- Note the failure in metadata

### Step 4: Build Complete Prompt

Call the Python script with all components:

```bash
python3 bazinga/scripts/prompt_builder.py \
  --agent-type "{agent_type}" \
  --session-id "{session_id}" \
  --group-id "{group_id}" \
  --task-title "{task_title}" \
  --task-requirements "{task_requirements}" \
  --branch "{branch}" \
  --mode "{mode}" \
  --testing-mode "{testing_mode}" \
  --context-block "{CONTEXT_BLOCK}" \
  --spec-block "{SPEC_BLOCK}" \
  --qa-feedback "{qa_feedback}" \
  --tl-feedback "{tl_feedback}" \
  --pm-state '{pm_state}' \
  --resume-context "{resume_context}"
```

### Step 5: Return Complete Prompt

Return the stdout from the Python script.
This is the COMPLETE prompt ready for Task spawn.

The prompt includes (in order):
1. CONTEXT_BLOCK (if available)
2. SPEC_BLOCK (if available)
3. FULL agent definition file (1000-2500 lines)
4. Task context and requirements

## Output Format

Return ONLY the complete prompt text.
Metadata is logged to stderr by the Python script.

## Error Handling

| Error | Action |
|-------|--------|
| specialization-loader fails | Continue, note in metadata |
| context-assembler fails | Continue, note in metadata |
| Python script fails | STOP, return error to orchestrator |
| Agent file not found | STOP, return error to orchestrator |
| Missing required markers | STOP, return error to orchestrator |

The Python script validates markers and agent file presence.
If it fails, prompt building cannot proceed.
```

### 4.2 Updated Python Script

The Python script remains largely the same, but now:
- SPEC_BLOCK and CONTEXT_BLOCK are passed as arguments
- The skill handles the orchestration of getting those blocks
- Script focuses purely on assembly and validation

### 4.3 Orchestrator Changes

**Before (3 calls):**
```markdown
## Agent Spawn Process

1. Invoke specialization-loader
2. Capture SPEC_BLOCK
3. Invoke context-assembler
4. Capture CONTEXT_BLOCK
5. Invoke prompt-builder with both blocks
6. Get COMPLETE_PROMPT
7. Spawn agent with prompt
```

**After (1 call):**
```markdown
## Agent Spawn Process

1. Provide context for prompt-builder:
   - Agent Type: {agent_type}
   - Session ID: {session_id}
   - Group ID: {group_id}
   - Task details...

2. Invoke prompt-builder:
   Skill(command: "prompt-builder")

3. Receive COMPLETE_PROMPT

4. Spawn agent with prompt:
   Task(prompt: COMPLETE_PROMPT)
```

---

## Part 5: Comparison

### 5.1 Complexity Analysis

| Aspect | 3-Skill Approach | 1-Skill Approach |
|--------|------------------|------------------|
| Orchestrator complexity | Higher | Lower |
| Skill complexity | Lower per skill | Higher for prompt-builder |
| Total skill calls | 3 per spawn | 1 per spawn |
| Orchestrator changes | More routing logic | Minimal routing logic |
| Debugging | 3 points of failure | 1 entry point |
| Testing | Test 3 integrations | Test 1 integration |

### 5.2 Token/Context Usage

| Approach | Context loaded |
|----------|----------------|
| 3-Skill | prompt-builder SKILL.md loaded last |
| 1-Skill | prompt-builder SKILL.md loaded once, then sub-skills |

The 1-skill approach loads slightly more context (prompt-builder stays loaded while sub-skills run), but this is negligible compared to the agent files (1000-2500 lines).

### 5.3 Failure Modes

**3-Skill Approach:**
- Orchestrator must handle failure at each step
- Must decide whether to continue or abort
- Complex error propagation

**1-Skill Approach:**
- prompt-builder handles all failures internally
- Clear error handling rules in one place
- Single error return to orchestrator

---

## Part 6: Critical Analysis

### Pros ✅

1. **Simpler orchestrator** - One call instead of three
2. **Encapsulation** - All prompt building logic in one skill
3. **Cleaner separation** - Orchestrator coordinates, skill builds
4. **Easier testing** - Single integration point
5. **Proven pattern** - Documentation confirms skills can compose
6. **Reduces LLM interpretation** - Less orchestrator decision-making

### Cons ⚠️

1. **Larger SKILL.md** - prompt-builder grows from ~100 to ~200 lines
2. **Nested context** - Sub-skill context overlays prompt-builder context
3. **New pattern** - Haven't tested skill-to-skill invocation in BAZINGA yet
4. **Debugging** - Need to trace through nested skill calls

### Verdict

**RECOMMENDED** - The 1-skill approach is cleaner and aligns with the user's goal of making the orchestrator a thin coordination layer. The complexity moves from orchestrator (LLM-interpreted) to skill (structured instructions), which is the right direction.

---

## Part 7: Implementation Changes

### What Changes from Original Plan

| Task | Original | New |
|------|----------|-----|
| Phase 3.2: Create prompt-builder SKILL.md | 100 lines | 200 lines with sub-skill orchestration |
| Phase 3 Task count | 6 tasks | 6 tasks (same) |
| Phase 4: Orchestrator updates | 8 tasks | 4 tasks (simplified) |
| Phase 4.2-4.6: Agent spawn updates | Complex (3 skills) | Simple (1 skill) |

### New Task List for Phase 3 & 4

**Phase 3: Skills (Updated)**

| # | Task | Description |
|---|------|-------------|
| 3.1 | Create prompt-builder skill directory | `mkdir -p .claude/skills/prompt-builder` |
| 3.2 | Create prompt-builder SKILL.md | **NEW: Includes sub-skill orchestration** |
| 3.3 | Create workflow-router skill directory | Same |
| 3.4 | Create workflow-router SKILL.md | Same |
| 3.5 | Create config-seeder skill directory | Same |
| 3.6 | Create config-seeder SKILL.md | Same |

**Phase 4: Orchestrator Updates (Simplified)**

| # | Task | Description |
|---|------|-------------|
| 4.1 | Add config seeding step | Same - Step 0.3 in initialization |
| 4.2 | Update ALL agent spawns to use prompt-builder | **SIMPLIFIED: One skill call** |
| 4.3 | Add workflow-router calls after responses | Same |
| 4.4 | Remove old prompt composition logic | Same - but less to remove |

---

## Part 8: Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Skill-to-skill invocation fails | Low | High | Test thoroughly before rollout |
| Context overflow with nested skills | Low | Medium | Keep skills focused |
| Sub-skill output not captured | Low | High | Verify output format |
| allowed-tools: [Skill] not working | Very Low | High | Documentation confirms it works |

### Recommendation

1. **Start with a test** - Create minimal prompt-builder that calls specialization-loader
2. **Verify output capture** - Ensure sub-skill output is available to parent skill
3. **Then implement full solution** - Once pattern is proven

---

## Part 9: Decision Points

### For User Approval

1. **Do you approve the 1-skill approach?**
   - prompt-builder internally calls specialization-loader and context-assembler
   - Orchestrator makes only ONE skill call per agent spawn

2. **Do you approve the updated SKILL.md structure?**
   - ~200 lines instead of ~100 lines
   - Includes sub-skill orchestration logic

3. **Do you want a proof-of-concept test first?**
   - Create minimal version
   - Test skill-to-skill invocation
   - Then implement full solution

---

## References

- [Agent SDK Docs](https://code.claude.com/docs/en/skills) - "Enable Skills by including 'Skill' in your allowed_tools"
- [Lee Han Chung's Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) - "Skills can build on each other"
- [Mikhail Shilkov](https://mikhail.io/2025/10/claude-code-skills/) - "Skills are composable"
- [Simon Willison](https://simonwillison.net/2025/Oct/16/claude-skills/) - Skills composability

---

## Appendix: Updated Prompt Builder SKILL.md

See Part 4.1 above for the complete updated SKILL.md content.
