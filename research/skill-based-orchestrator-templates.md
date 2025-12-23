# Skill-Based Orchestrator Templates: Replace Direct Python Calls

**Date:** 2025-12-17
**Context:** Orchestrator templates call `python3 prompt_builder.py` directly instead of using `Skill(command: "prompt-builder")`
**Decision:** Update skill to return JSON, use file-based parameter handoff
**Status:** Implemented
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

**Current state (WRONG):**
```markdown
# In phase_simple.md
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
  --agent-type {agent_type} \
  --session-id "{session_id}" \
  ...
```

**Should be:**
```markdown
# In phase_simple.md
→ Skill(command: "prompt-builder")
```

## Multi-LLM Review Integration

### Critical Feedback from OpenAI (Incorporated)

1. **Skill I/O mismatch**: Current skill writes metadata to stderr, returns prompt to stdout. Orchestrator can't reliably verify prompt file path. **Fix:** Return JSON with structured output.

2. **Parameter delivery ambiguity**: YAML in freeform text is unreliable. **Fix:** Write params to JSON file, skill reads that file.

3. **Directory creation gap**: Script must ensure `bazinga/prompts/{session_id}/` exists. **Fix:** Add mkdir -p in script.

4. **Incomplete coverage**: Must update ALL locations (phase_simple, phase_parallel, orchestrator.md, etc.). **Fix:** Comprehensive migration plan.

5. **Missing retry feedback**: qa_feedback/tl_feedback must be passed. **Fix:** Include in JSON params file.

### Incorporated Improvements

1. **JSON output schema** for skill:
   ```json
   {
     "success": true,
     "prompt_file": "bazinga/prompts/{session}/{agent}_{group}.md",
     "tokens_estimate": 10728,
     "lines": 1406,
     "markers_ok": true,
     "missing_markers": [],
     "error": null
   }
   ```

2. **File-based parameter handoff**: Orchestrator writes params JSON, skill reads it.

3. **Explicit mkdir behavior**: Script ensures directory exists.

### Rejected Suggestions

1. **Skill args support**: Tool doesn't support passing JSON args directly to `Skill(command: ...)`.

2. **Result file for post-compaction recovery**: Over-engineering for current needs.

## Revised Solution

### Architecture

```
Orchestrator                    Skill                         Script
-----------                    -----                         ------
1. Write params JSON    →
2. Skill(prompt-builder)→      3. Read params JSON     →
                               4. Call script          →     5. Build prompt
                               ←     6. Return JSON    ←     7. Write to file
←      8. Return JSON
9. Verify success
10. Task() with file path
```

### Change 1: Update prompt_builder.py

Add JSON output mode (already partially implemented with `--output-file`):

```python
# After writing prompt to file, output JSON to stdout:
result = {
    "success": True,
    "prompt_file": output_path,
    "tokens_estimate": token_count,
    "lines": line_count,
    "markers_ok": markers_valid,
    "missing_markers": missing,
    "error": None
}
print(json.dumps(result))
```

Ensure directory creation:
```python
os.makedirs(os.path.dirname(output_path), exist_ok=True)
```

### Change 2: Update SKILL.md

**Input:** Read params from `bazinga/prompts/{session_id}/params_{agent}_{group}.json`

**Output:** JSON result (not raw prompt text)

```markdown
## Your Task

### Step 1: Read Parameters File

Look for params file at: `bazinga/prompts/{session_id}/params_{agent}_{group}.json`

This file is written by the orchestrator before invoking this skill.

### Step 2: Call Script

```bash
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
  --params-file "bazinga/prompts/{session_id}/params_{agent}_{group}.json"
```

### Step 3: Return JSON Result

The script outputs JSON to stdout. Return this JSON to the orchestrator.
```

### Change 3: Update Orchestrator Templates

**Before:**
```markdown
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
  --agent-type developer \
  --session-id "{session_id}" \
  ...
```

**After:**
```markdown
**Step 1: Write params file**
Write to `bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json`:
```json
{
  "agent_type": "{agent_type}",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "{task_title}",
  "task_requirements": "{task_requirements}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[agent_type]}"
}
```

**Step 2: Invoke skill**
→ `Skill(command: "prompt-builder")`

**Step 3: Verify result**
Skill returns JSON. Check:
- `success` is true
- `prompt_file` is non-empty
- `markers_ok` is true

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP
```

## Files to Modify

| File | Change |
|------|--------|
| `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Add `--params-file` mode, JSON output, mkdir |
| `.claude/skills/prompt-builder/SKILL.md` | Update to read params file, return JSON |
| `templates/orchestrator/phase_simple.md` | Replace 8 python calls with skill pattern |
| `templates/orchestrator/phase_parallel.md` | Replace 5 python calls with skill pattern |

## Implementation Plan

### Phase 1: Update Script
1. Add `--params-file` argument to prompt_builder.py
2. Add JSON output mode (stdout)
3. Add mkdir for output directory
4. Test with existing CLI args (backward compat)

### Phase 2: Update SKILL.md
1. Document params file format
2. Document JSON output schema
3. Add error handling section

### Phase 3: Update Templates
1. Update phase_simple.md (8 locations)
2. Update phase_parallel.md (5 locations)
3. Test each spawn pattern

### Phase 4: Integration Test
1. Run Simple Calculator App test
2. Verify all agents spawn correctly
3. Verify retry flows work (qa_feedback, tl_feedback)

## Critical Analysis

### Pros ✅
- Eliminates shell quoting/escaping issues
- Structured JSON output is machine-parseable
- File-based params handles long content safely
- Single source of truth (skill owns script invocation)

### Cons ⚠️
- Extra file I/O (params file)
- More complex skill logic
- Migration touches many files

### Verdict

This is the correct architectural approach. The file-based parameter handoff solves the quoting/escaping issues that caused the original bug. The JSON output contract provides reliable verification.

## References

- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
- Current templates: `templates/orchestrator/phase_simple.md`
- Skill: `.claude/skills/prompt-builder/SKILL.md`
- Script: `.claude/skills/prompt-builder/scripts/prompt_builder.py`
