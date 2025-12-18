# Orchestrator Prompt Passing: File Reference vs Content Passing

**Date:** 2025-12-18
**Context:** Context exhaustion during parallel agent spawns traced to contradictory instructions
**Decision:** Standardize on file-reference approach
**Status:** Proposed

---

## Problem Statement

The orchestrator documentation contains **contradictory instructions** for how to pass prompts to spawned agents:

### Approach A: Pass Prompt Content (WRONG)
Text instructions say:
```
4. Read the prompt from prompt_file
5. Use Task() with the prompt content
```

This means:
1. Orchestrator reads the prompt file (~10,700 tokens for developer)
2. Orchestrator passes that content to Task()
3. **10,700 tokens loaded into orchestrator context**

### Approach B: File Reference (CORRECT)
Code examples show:
```python
prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md
        which contains your complete instructions.
        THEN: Execute ALL instructions in that file."
```

This means:
1. Orchestrator passes ~50 token instruction to Task()
2. **Agent** reads the file in its own isolated context
3. **Only ~50 tokens in orchestrator context**

## Root Cause

The orchestrator.md file has:
- Text instructions that say "read the prompt... pass the content" (lines 223-224, 349-350, 2070, 2159)
- Code examples that correctly use file-reference (lines 2103-2107, 2195-2197)
- Phase templates (phase_simple.md, phase_parallel.md) that correctly use file-reference

If the orchestrator (Claude) follows the text instructions instead of the code examples, it causes massive context bloat.

## Token Impact Analysis

| Scenario | Approach A (content) | Approach B (file ref) | Difference |
|----------|---------------------|----------------------|------------|
| 1 Developer spawn | 10,700 | 50 | 10,650 |
| 4 Developer spawns | 42,800 | 200 | 42,600 |
| Full workflow (Dev+QA+TL) | 31,700 | 150 | 31,550 |
| 4 groups full workflow | 126,800 | 600 | 126,200 |

**Approach A can consume 63% of the 200K context window just from prompt passing!**

## Solution

### Changes Required in orchestrator.md

**Location 1: Lines 219-225 (Validation Logic)**
```markdown
# BEFORE (wrong):
IF about to call Task():
  1. Write params JSON file
  2. Invoke Skill(command: "prompt-builder")
  3. Parse JSON response: verify success=true, get prompt_file path
  4. Read the prompt from prompt_file
  5. Use Task() with the prompt content

# AFTER (correct):
IF about to call Task():
  1. Write params JSON file
  2. Invoke Skill(command: "prompt-builder")
  3. Parse JSON response: verify success=true, get prompt_file path
  4. Use Task() with file-reference instruction (DO NOT read the file)
```

**Location 2: Lines 346-350**
```markdown
# BEFORE (wrong):
3. **Parse JSON response**: verify `success: true`, get `prompt_file` path
4. **Read the prompt** from the `prompt_file` path
5. **Spawn agent** with the prompt content in Task()

# AFTER (correct):
3. **Parse JSON response**: verify `success: true`, get `prompt_file` path
4. **Spawn agent** with file-reference instruction:
   Task(prompt="FIRST: Read {prompt_file}... THEN: Execute ALL instructions...")

**🔴 DO NOT read the prompt file into orchestrator context - agent reads it in isolated context**
```

**Location 3: Lines 2067-2071**
```markdown
# BEFORE (wrong):
**Phase 2: Orchestrator Prompt Building (at agent spawn)**
1. Write params JSON file with agent config and output_file path
2. Invoke `Skill(command: "prompt-builder")` - skill reads params file
3. Parse JSON response, verify success, get prompt_file
4. Read prompt from file and spawn agent with prompt content

# AFTER (correct):
**Phase 2: Orchestrator Prompt Building (at agent spawn)**
1. Write params JSON file with agent config and output_file path
2. Invoke `Skill(command: "prompt-builder")` - skill reads params file
3. Parse JSON response, verify success, get prompt_file
4. Spawn agent with file-reference instruction (DO NOT read file into orchestrator context)
```

**Location 4: Lines 2097-2108**
```markdown
# BEFORE (ambiguous - text says "content" but example shows file-ref):
**Step 4: Spawn agent with prompt content**
```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["{agent_type}"],
  description: "{agent_type} working on {group_id}",
  prompt: "FIRST: Read bazinga/prompts/..."
)
```

# AFTER (clear):
**Step 4: Spawn agent with file-reference instruction**

**🔴 CRITICAL: DO NOT read the prompt file. Pass only the file-reference instruction.**

```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["{agent_type}"],
  description: "{agent_type} working on {group_id}",
  prompt: "FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first."
)
```
```

**Location 5: Lines 2155-2160**
```markdown
# BEFORE (wrong):
1. **Write params file** with agent config
2. **Run prompt-builder** with `--params-file` (outputs JSON to stdout)
3. **Parse JSON response**, verify `success: true`, get `prompt_file` path
4. **Read prompt** from `prompt_file`, spawn agent with prompt content

# AFTER (correct):
1. **Write params file** with agent config
2. **Run prompt-builder** with `--params-file` (outputs JSON to stdout)
3. **Parse JSON response**, verify `success: true`, get `prompt_file` path
4. **Spawn agent** with file-reference instruction (DO NOT read file)
```

### Add Explicit Warning Section

Add new section after line 2160:

```markdown
### 🔴 CRITICAL: File Reference vs Content Passing

**NEVER read the prompt file into orchestrator context.**

| Approach | Tokens | Correct? |
|----------|--------|----------|
| Read file, pass content | ~10,700/agent | ❌ WRONG |
| Pass file-reference instruction | ~50/agent | ✅ CORRECT |

**Why this matters:**
- Developer prompt: ~10,700 tokens
- 4 parallel developers: ~42,800 tokens
- This alone consumes 21% of 200K context!

**The spawned agent reads the file in its OWN isolated context.**
**Orchestrator context stays minimal.**

**WRONG (causes context exhaustion):**
```python
# DON'T DO THIS:
prompt_content = Read(prompt_file)  # 10,700 tokens loaded!
Task(prompt=prompt_content)         # Passed to Task, stays in context
```

**CORRECT (context efficient):**
```python
# DO THIS:
Task(prompt="FIRST: Read {prompt_file}...")  # Only 50 tokens!
# Agent reads file in its own isolated context
```
```

## Phase Templates Verification

The phase templates already use the correct approach:

**phase_simple.md (line 90-91):** ✅ Correct
```
prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md..."
```

**phase_parallel.md (lines 231-235):** ✅ Correct
```
prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_A.md..."
```

No changes needed in phase templates.

## Implementation Checklist

- [ ] Edit orchestrator.md lines 219-225 (validation logic)
- [ ] Edit orchestrator.md lines 346-350 (spawning instructions)
- [ ] Edit orchestrator.md lines 2067-2071 (phase 2 description)
- [ ] Edit orchestrator.md lines 2097-2108 (step 4 description)
- [ ] Edit orchestrator.md lines 2155-2160 (spawn sequence)
- [ ] Add explicit warning section after line 2160
- [ ] Verify phase_simple.md (no changes needed)
- [ ] Verify phase_parallel.md (no changes needed)
- [ ] Rebuild slash command via pre-commit hook
- [ ] Test with integration test

## Expected Outcome

After fix:
- Orchestrator context stays minimal (~200 tokens for 4 spawns vs ~42,800)
- No more context exhaustion during parallel spawns
- Agents still receive full prompts (they read from file)
- Same functionality, 99% less context usage for prompt passing

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Agents fail to read file | Clear error message in instruction |
| File path wrong | prompt-builder validates path exists |
| Breaking change | No - behavior same for agents, just context-efficient |

## References

- Original context exhaustion incident: Session bazinga_20251215_103357
- orchestrator.md contradictory sections identified
- phase_simple.md and phase_parallel.md already correct
