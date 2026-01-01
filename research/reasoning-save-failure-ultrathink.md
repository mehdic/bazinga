# Reasoning Save Failure: Root Cause Analysis

**Date:** 2026-01-01
**Context:** Integration test revealed Developer/Tech Lead agents not saving reasoning despite having instructions
**Decision:** Implement Option E (Enhanced Hybrid) with scoped substitution + pre-filled block injection
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)

---

## Problem Statement

During BAZINGA integration testing, we observed:
- **QA Expert**: Saved 2 reasoning entries (understanding + completion) ✅
- **Developer (SSE)**: Saved 0 reasoning entries ❌
- **Tech Lead**: Saved 0 reasoning entries ❌
- **PM**: Saved 2 reasoning entries ✅

The reasoning documentation is present in all agent prompts and uses the correct skill invocation (`Skill(command: "bazinga-db-agents")`). Yet 50% of agents failed to execute the save-reasoning call.

---

## Root Cause Analysis

### Finding 1: Unsubstituted Placeholders in Agent Files

**The Critical Bug:**

Agent definition files (`tech_lead.md`, `developer.md`, etc.) contain reasoning documentation with placeholders:

```markdown
Request: save-reasoning "{SESSION_ID}" "{GROUP_ID}" "tech_lead" "understanding" \
  --content-file /tmp/reasoning_understanding.md \
  --confidence high
```

The prompt-builder (`prompt_builder.py`) reads these files verbatim via `read_agent_file()` and appends them to the prompt **WITHOUT substituting placeholders**.

Meanwhile, the Task Context section (built by `build_task_context()`) DOES contain actual values:
```markdown
**SESSION:** bazinga_20260101_134959
**GROUP:** CALC
```

**Evidence from generated prompts:**
- Line 2009 (reasoning section): `save-reasoning "{SESSION_ID}" "{GROUP_ID}"` - NOT substituted
- Line 2085-2086 (task context): `**SESSION:** bazinga_20260101_134959` - SUBSTITUTED

**Impact:** The agent sees literal `{SESSION_ID}` text, not the actual value. It must mentally substitute from the Task Context section - an error-prone cognitive leap that some agents fail to make.

### Finding 2: Prompt Length and Attention Degradation

| Agent | Prompt Lines | Reasoning Section Location | Saved Reasoning? |
|-------|--------------|---------------------------|------------------|
| PM | 514 | Lines 354-372 (68% position) | ✅ Yes |
| QA Expert | 1770 | Lines 1655-1730 (93% position) | ✅ Yes |
| SSE | 1773 | Lines 583-684 (33% position) | ❌ No |
| Tech Lead | 2098 | Lines 1957-2033 (93% position) | ❌ No |

**Observations:**
- Position in prompt doesn't directly correlate with success (QA at 93% succeeded, TL at 93% failed)
- Absolute length may matter: TL's prompt is longest (2098 lines)
- SSE's reasoning section is early (33%) yet still failed

**Hypothesis:** The unsubstituted placeholders create cognitive friction. Some agents process them correctly, others don't - possibly model-dependent (haiku/sonnet/opus) or task-complexity-dependent.

### Finding 3: No Placeholder Substitution Mechanism

Searched `prompt_builder.py` for substitution patterns:
```bash
grep -E "\.format\(|\.replace\(|{session_id}|{group_id}" prompt_builder.py
# Result: No matches found
```

The prompt-builder was never designed to substitute placeholders in agent file content. This is a design gap.

---

## Why QA Expert Succeeded

Comparing QA Expert vs Tech Lead behavior:

1. **QA Expert Prompt Structure:**
   - Reasoning section at lines 1655-1730
   - Has explicit "After reading each package" workflow markers
   - Clear step numbering (Step 0, Step 1, Step 2...)

2. **Tech Lead Prompt Structure:**
   - Reasoning section at lines 1957-2033
   - Buried after extensive review content
   - Less procedural structure around reasoning calls

The QA Expert's more procedural structure may have reinforced the reasoning call execution. But the key differentiator is likely random variance in how each agent spawn interpreted the placeholder vs actual value relationship.

---

## Solution Options

### Option A: Placeholder Substitution in Prompt-Builder (Recommended)

**Description:** Add placeholder substitution to `prompt_builder.py` after reading agent file.

**Implementation:**
```python
def read_agent_file(agent_type):
    content = path.read_text(encoding="utf-8")
    return content  # Currently returns raw

# Change to:
def read_agent_file(agent_type, session_id=None, group_id=None):
    content = path.read_text(encoding="utf-8")
    if session_id:
        content = content.replace("{SESSION_ID}", session_id)
    if group_id:
        content = content.replace("{GROUP_ID}", group_id)
    return content
```

**Pros:**
- Simple fix with minimal risk
- Fixes the issue at source
- All agents get correctly substituted values
- No changes to agent files needed

**Cons:**
- Need to identify all placeholders to substitute
- Could accidentally substitute unintended patterns

### Option B: Remove Placeholders from Agent Files

**Description:** Change agent files to reference values from Task Context instead.

**Current:**
```markdown
Request: save-reasoning "{SESSION_ID}" "{GROUP_ID}" "tech_lead" "understanding"
```

**Proposed:**
```markdown
Request: save-reasoning "$(session_id from Task Assignment)" "$(group_id from Task Assignment)" "tech_lead" "understanding"

OR

# Use the SESSION and GROUP values from your Current Task Assignment section above
cat > /tmp/reasoning_understanding.md << 'EOF'
...
EOF
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py save-reasoning \
  [SESSION_ID from Task Assignment] [GROUP_ID from Task Assignment] \
  "tech_lead" "understanding" --content-file /tmp/reasoning_understanding.md
```

**Pros:**
- Makes intent clearer
- Self-documenting

**Cons:**
- Requires updating all agent files (7+ files)
- More verbose and potentially confusing
- Agents must still make the mental link

### Option C: Inject Explicit Variable Block

**Description:** Add a "Variables for This Session" block immediately after the agent definition that agents can copy-paste.

**Implementation:**
In `build_task_context()`, prepend a variables block:
```markdown
---

## Session Variables (Copy These Values)

```
SESSION_ID="bazinga_20260101_134959"
GROUP_ID="CALC"
```

When the agent documentation says `{SESSION_ID}`, use the value above.
```

**Pros:**
- Explicit and unambiguous
- Easy to implement
- Agents can literally copy values

**Cons:**
- Adds prompt length
- Still requires agent to make the connection
- Doesn't fix root cause

### Option D: Hybrid Approach (Option A + Verification)

**Description:** Implement placeholder substitution AND add a verification step.

1. Substitute placeholders in prompt-builder (Option A)
2. Add a post-processing validation step that warns if any `{...}` patterns remain
3. Add a reminder at the end of reasoning section: "The session_id and group_id above have been pre-filled for this session"

**Pros:**
- Belt-and-suspenders approach
- Catches any missed placeholders
- Reinforces to agent that values are ready to use

**Cons:**
- More complex implementation
- Slightly more verbose

---

## Recommended Solution: Option D (Hybrid)

### Strategic Plan

#### Phase 1: Immediate Fix (1 change)

1. **Modify `prompt_builder.py`** to substitute placeholders in agent file content:

```python
# In read_agent_file() or after agent_definition = read_agent_file():
PLACEHOLDER_SUBSTITUTIONS = {
    "{SESSION_ID}": args.session_id,
    "{GROUP_ID}": args.group_id or "global",
    "{BRANCH}": args.branch,
}
for placeholder, value in PLACEHOLDER_SUBSTITUTIONS.items():
    agent_definition = agent_definition.replace(placeholder, value)
```

#### Phase 2: Validation Guard (1 change)

2. **Add placeholder validation** before writing prompt:

```python
# After composing full_prompt
import re
remaining_placeholders = re.findall(r'\{[A-Z_]+\}', full_prompt)
if remaining_placeholders:
    print(f"WARNING: Unsubstituted placeholders found: {set(remaining_placeholders)}", file=sys.stderr)
```

#### Phase 3: Agent File Enhancement (Optional)

3. **Add reinforcement to agent reasoning sections:**

Update the reasoning documentation header in each agent file:
```markdown
## 🧠 Reasoning Documentation (MANDATORY)

**Note:** The session_id and group_id in examples below are pre-filled for your current task.
You can use them directly without modification.
```

### Implementation Checklist

- [ ] Modify `prompt_builder.py:read_agent_file()` to accept session_id, group_id parameters
- [ ] Apply substitutions after reading agent file content
- [ ] Add validation regex check for remaining placeholders
- [ ] Add warning output for any unsubstituted patterns
- [ ] Test with integration test to verify reasoning is saved
- [ ] Update agent files with reinforcement note (optional)

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Over-substitution | Low | Medium | Only substitute uppercase patterns in `{}` |
| Breaking existing patterns | Low | High | Regex validation catches issues |
| Agent still ignores reasoning | Low | Medium | Reinforcement note helps |

---

## Success Criteria

After implementing this fix:

1. **All generated prompts** should have `{SESSION_ID}` and `{GROUP_ID}` replaced with actual values
2. **Validation** should log warning if any placeholders remain
3. **Integration test** should show 8 reasoning entries (2 per agent × 4 agents)
4. **No regression** in existing prompt-builder functionality

---

## Related Files

| File | Change Needed |
|------|---------------|
| `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Add substitution logic |
| `agents/developer.md` | Optional: Add reinforcement note |
| `agents/tech_lead.md` | Optional: Add reinforcement note |
| `agents/qa_expert.md` | Optional: Add reinforcement note |
| `agents/senior_software_engineer.md` | Optional: Add reinforcement note |

---

## Multi-LLM Review Integration

### Consensus Points (OpenAI Agreed)

1. **Scoped substitution is safer** - Global `.replace()` risks modifying unrelated JSON/code examples
2. **Pre-filled mandatory block needed** - PM/QA succeed because they have procedural "MANDATORY" sections; Dev/TL lack this
3. **Orchestrator-level verification needed** - No current guard to detect missing reasoning entries
4. **CI pre-flight test needed** - Should catch unsubstituted placeholders before production

### Incorporated Feedback

| Suggestion | Incorporated? | Implementation |
|------------|---------------|----------------|
| Scoped substitution (only save-reasoning lines) | ✅ Yes | Regex-targeted replacement only in lines containing `save-reasoning` |
| Inject mandatory pre-filled reasoning block | ✅ Yes | New Phase 0: Inject at prompt start before agent definition |
| Add bazinga-db-agents to Skills Checklist | ✅ Yes | Update `build_skills_block()` to include as MANDATORY |
| Orchestrator guardrail | ✅ Yes | Query DB after agent response to verify reasoning saved |
| CI pre-flight test | ✅ Yes | Add test that generates prompts and validates no placeholders remain |
| Narrow placeholder validation | ✅ Yes | Only flag `{SESSION_ID}|{GROUP_ID}|{BRANCH}` in save-reasoning lines |

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejected | Reason |
|------------|----------|--------|
| "Remove contaminating content from agents/tech_lead.md" | ❌ False alarm | No RCA content exists in tech_lead.md - reviewer confused files in context bundle |
| "Move non-instructional content to docs/" | N/A | No such content exists; agent files are purely instructions |

---

## Revised Solution: Option E (Enhanced Hybrid)

Incorporating OpenAI feedback, the solution is upgraded:

### Phase 0: Inject Mandatory Pre-Filled Reasoning Block (NEW)

**Before** the agent definition, inject a compact block with concrete values:

```markdown
---

## 🔴 MANDATORY REASONING SAVES (Pre-filled for this session)

**Save understanding at START of your task:**
```bash
cat > /tmp/reasoning_understanding.md << 'EOF'
## Understanding
[Document your interpretation of the task]
EOF
```

Then invoke:
```
Skill(command: "bazinga-db-agents")

Request: save-reasoning "{actual_session_id}" "{actual_group_id}" "{agent_type}" "understanding" \
  --content-file /tmp/reasoning_understanding.md --confidence high
```

**Save completion at END before returning status:**
```bash
cat > /tmp/reasoning_completion.md << 'EOF'
## Completion
[Document what you accomplished and key decisions]
EOF
```

Then invoke:
```
Skill(command: "bazinga-db-agents")

Request: save-reasoning "{actual_session_id}" "{actual_group_id}" "{agent_type}" "completion" \
  --content-file /tmp/reasoning_completion.md --confidence high
```

⚠️ **These values are pre-filled. Invoke the skill directly.**

---
```

This block is ~20 lines and uses actual values (not placeholders).

### Phase 1: Scoped Placeholder Substitution (REFINED)

Instead of global `.replace()`, use targeted regex:

```python
import re

def substitute_reasoning_placeholders(content, session_id, group_id):
    """Substitute placeholders ONLY in save-reasoning command lines."""
    def replacer(match):
        line = match.group(0)
        line = line.replace("{SESSION_ID}", session_id)
        line = line.replace("{GROUP_ID}", group_id or "global")
        return line

    # Match lines containing save-reasoning commands
    pattern = r'.*save-reasoning.*\{SESSION_ID\}.*\{GROUP_ID\}.*'
    return re.sub(pattern, replacer, content)
```

### Phase 2: Narrow Placeholder Validation (REFINED)

Only validate the specific placeholders in save-reasoning context:

```python
# After composing prompt
def validate_reasoning_placeholders(content):
    """Check for unsubstituted placeholders in save-reasoning lines only."""
    pattern = r'save-reasoning.*(\{SESSION_ID\}|\{GROUP_ID\})'
    matches = re.findall(pattern, content)
    if matches:
        print(f"ERROR: Unsubstituted placeholders in save-reasoning: {matches}", file=sys.stderr)
        return False
    return True
```

### Phase 3: Update Skills Checklist (NEW)

Add `bazinga-db-agents` as MANDATORY skill in `build_skills_block()`:

```python
MANDATORY_SKILLS = {
    "developer": ["bazinga-db-agents"],
    "senior_software_engineer": ["bazinga-db-agents"],
    "qa_expert": ["bazinga-db-agents"],
    "tech_lead": ["bazinga-db-agents"],
    "project_manager": ["bazinga-db-agents"],
}
```

### Phase 4: Orchestrator Guardrail (NEW)

After each agent response, verify reasoning was saved:

```python
# In orchestrator, after agent returns
Skill(command: "bazinga-db-agents")
Request: check-mandatory-phases "{session_id}" "{group_id}" "{agent_type}"

# If missing phases detected, log warning and optionally spawn micro-remediation
```

### Phase 5: CI Pre-Flight Test (NEW)

Add test to `tests/test_prompt_builder.py`:

```python
def test_no_unsubstituted_placeholders():
    """Ensure generated prompts have all placeholders substituted."""
    for agent_type in ["developer", "qa_expert", "tech_lead"]:
        prompt = generate_prompt(agent_type, "test_session", "TEST_GROUP")
        assert "{SESSION_ID}" not in prompt
        assert "{GROUP_ID}" not in prompt
```

---

## Updated Implementation Checklist

- [ ] **Phase 0:** Add `build_mandatory_reasoning_block()` function to prompt_builder.py
- [ ] **Phase 0:** Inject block before agent definition in prompt composition
- [ ] **Phase 1:** Add `substitute_reasoning_placeholders()` function
- [ ] **Phase 1:** Apply scoped substitution after reading agent file
- [ ] **Phase 2:** Add `validate_reasoning_placeholders()` function
- [ ] **Phase 2:** Fail build if unsubstituted placeholders remain in save-reasoning lines
- [ ] **Phase 3:** Update `build_skills_block()` to include bazinga-db-agents as MANDATORY
- [ ] **Phase 4:** Add orchestrator guardrail to verify reasoning after agent response
- [ ] **Phase 5:** Add CI test for placeholder validation
- [ ] **Verify:** Run integration test and confirm 8 reasoning entries (2 per agent × 4 agents)

---

## Lessons Learned

1. **Template variables need explicit handling** - Assuming agents will infer values from context is unreliable
2. **Prompt composition should be holistic** - The prompt-builder must handle ALL dynamic content, not just appended sections
3. **Validation catches bugs early** - A simple regex check would have caught this before production
4. **Test reasoning independently** - Integration tests should verify reasoning storage as a specific success criterion
5. **Pre-filled blocks increase compliance** - Agents follow concrete examples better than templates with placeholders
6. **Scoped operations are safer** - Global replacements risk unintended side effects
