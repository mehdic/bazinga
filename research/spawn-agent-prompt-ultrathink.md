# Spawn Agent Prompt Implementation: Ultrathink Analysis

**Date:** 2025-12-18
**Context:** Review of the file-reference approach for spawning BAZINGA agents
**Decision:** Evaluate correctness and identify potential issues with current implementation
**Status:** Proposed
**Reviewed by:** Pending (OpenAI GPT-5, Google Gemini 3 Pro Preview)

---

## Problem Statement

The BAZINGA orchestrator spawns specialized agents (Developer, QA Expert, Tech Lead, etc.) via the Task tool. The critical question is:

**How should the orchestrator pass the agent's prompt to the Task tool?**

Two approaches exist:
- **Approach A (Content):** Read prompt file into orchestrator context, pass as prompt content
- **Approach B (File-Reference):** Pass instruction telling agent to read the file itself

## Current Implementation

The fix implemented uses **Approach B (File-Reference)**:

```python
Task(
  subagent_type="general-purpose",
  model=MODEL_CONFIG["{agent_type}"],
  description="{agent_type} working on {group_id}",
  prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first."
)
```

### Locations Updated

| File | Lines | Status |
|------|-------|--------|
| `agents/orchestrator.md` | 223-224, 349, 2088, 2189 | Updated |
| `templates/orchestrator/phase_simple.md` | 90 | Already correct |
| `templates/orchestrator/phase_parallel.md` | 231-234 | Already correct |

### Consistency Check

All spawn locations now consistently use the file-reference pattern:
- Validation block (line 223-224)
- Mandatory prompt-builder section (line 349)
- Phase 2A spawn example (line 2088)
- Phase 2B spawn example (line 2189)
- phase_simple.md template
- phase_parallel.md template

---

## Critical Analysis

### Pros of File-Reference Approach

1. **Token Efficiency** (~99.5% reduction)
   - Developer prompt: ~10,700 tokens
   - File-reference instruction: ~50 tokens
   - 4 parallel developers: 42,800 vs 200 tokens

2. **Context Isolation**
   - Agent reads file in its OWN isolated context
   - Orchestrator context stays minimal for coordination

3. **Scalability**
   - Can spawn many agents without context exhaustion
   - Supports max 4 parallel developers without issue

4. **Consistency**
   - Same pattern for all agent types
   - Templates already used this approach

### Cons / Risks

1. **File Must Exist**
   - If prompt-builder fails but orchestrator proceeds, agent gets empty/missing file
   - Mitigation: JSON verification step (`success: true`) before spawn

2. **Race Condition (Theoretical)**
   - File written by prompt-builder must be flushed before agent reads
   - Mitigation: Python file writing is synchronous; not a practical concern

3. **Agent Compliance Risk**
   - Agent might not follow "FIRST: Read file" instruction
   - Mitigation: Strong language ("Do NOT proceed without reading")

4. **Path Exposure**
   - Agent sees internal file path structure
   - Mitigation: Not a security concern - agent needs file access anyway

5. **Debugging Complexity**
   - If agent fails, need to check prompt file separately
   - Mitigation: Prompt file preserved in bazinga/prompts/{session_id}/

---

## Deep Dive: Does the Task Tool Work This Way?

### Key Question
Does the spawned agent actually have access to read files in the workspace?

### Evidence

1. **Task Tool Documentation** (from system):
   > "Launch a new agent to handle complex, multi-step tasks autonomously"
   > Agents have access to tools including Read, Glob, Grep

2. **general-purpose Agent Type**:
   > Tools: * (all tools)

   This confirms spawned agents CAN use the Read tool.

3. **Previous Integration Tests**:
   - Developers successfully read their prompt files
   - QA Experts read prompt files and executed tests
   - No "file not found" errors in logs

### Verification Needed

**Q1:** Does the agent's Read tool work in the SAME workspace as orchestrator?
- **Hypothesis:** Yes - agents share workspace context
- **Evidence:** Successful integration tests, agents create files orchestrator can see

**Q2:** What if agent ignores the "FIRST: Read" instruction?
- **Hypothesis:** Unlikely but possible with lower-capability models
- **Mitigation:** Use explicit language, consider adding verification step

---

## Alternative Approaches Considered

### Alternative 1: Hybrid (Summary + File)

```python
prompt="""
## Quick Summary
Task: {task_title}
Group: {group_id}
Key Files: {key_files}

## Full Instructions
Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md for complete details.
"""
```

**Pros:** Agent has context even if Read fails
**Cons:** Adds tokens back (~500-1000), partial info might cause confusion

### Alternative 2: Embedded Prompt (Current Approach A)

```python
prompt_content = Read(prompt_file)  # Load ~10,700 tokens
Task(prompt=prompt_content)
```

**Pros:** Guaranteed agent has full instructions
**Cons:** Context exhaustion (original problem)

### Alternative 3: Two-Stage Spawn

```python
# Stage 1: Minimal spawn
Task(prompt="Read file and confirm ready")
# Stage 2: Full task after confirmation
Task(prompt="Execute task...")
```

**Pros:** Verification that agent can read file
**Cons:** Doubles spawn overhead, adds complexity

---

## Verdict

**The file-reference approach (Approach B) is correct.**

| Criterion | Assessment |
|-----------|------------|
| Token efficiency | Excellent (~99.5% reduction) |
| Context isolation | Excellent |
| Implementation consistency | Good (all locations updated) |
| Agent compliance risk | Low (strong language, proven in tests) |
| Debugging experience | Acceptable (prompt files preserved) |

### Remaining Concerns

1. **No explicit verification that agent read the file**
   - Current: Trust-based ("Do NOT proceed without reading")
   - Could add: Agent must echo first line of file before proceeding

2. **Error handling if prompt-builder fails**
   - Current: JSON check for `success: true`
   - Could add: File existence check before spawn

3. **Model-specific behavior**
   - Haiku might be less reliable at following "read file first"
   - Opus/Sonnet likely more compliant
   - Testing needed across model tiers

---

## Recommendations

### Immediate (Already Implemented)

1. Use file-reference for all spawns
2. Strong language: "FIRST: Read... Do NOT proceed without"
3. JSON verification before spawn

### Consider Adding

1. **File existence check** before Task() call:
   ```python
   # After prompt-builder succeeds
   test -f {prompt_file} && echo "exists" || echo "MISSING"
   ```

2. **First-line echo requirement** in agent prompt:
   ```
   FIRST: Read {prompt_file}
   THEN: Echo the first heading from that file to confirm you read it
   FINALLY: Execute ALL instructions
   ```

3. **Integration test** specifically for file-reference compliance:
   - Spawn agent with file-reference
   - Verify agent's first action is Read tool on that file
   - Verify agent produces expected output

---

## Implementation Checklist

### Completed

- [x] Updated orchestrator.md line 223-224 (validation block)
- [x] Updated orchestrator.md line 349 (spawn instruction)
- [x] Updated orchestrator.md line 2088 (Phase 2A example)
- [x] Updated orchestrator.md line 2189 (Phase 2B example)
- [x] Added warning section (lines 2145-2154)
- [x] Verified phase_simple.md (already correct)
- [x] Verified phase_parallel.md (already correct)
- [x] Rebuilt slash command
- [x] Committed and pushed

### Not Yet Done

- [ ] Add file existence check before spawn (optional)
- [ ] Add first-line echo requirement (optional)
- [ ] Create integration test for file-reference compliance
- [ ] Test across all model tiers (haiku, sonnet, opus)

---

## Questions for External Review

1. **Is the file-reference approach fundamentally sound?**
   - Does passing "Read this file" instead of file content work reliably?

2. **Are there edge cases we're missing?**
   - Network failures, file system issues, concurrent access?

3. **Should we add verification that agent read the file?**
   - Is trust-based approach sufficient, or should we verify?

4. **Model-tier concerns?**
   - Are there known issues with haiku following multi-step instructions?

5. **Alternative approaches?**
   - Did we miss a better solution?

---

## References

- Previous analysis: `research/orchestrator-prompt-passing-fix.md`
- Task tool documentation: System prompt
- Integration test spec: `tests/integration/simple-calculator-spec.md`
- Orchestrator source: `agents/orchestrator.md`
