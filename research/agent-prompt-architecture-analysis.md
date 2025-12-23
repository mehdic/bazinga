# Agent Prompt Architecture Analysis

**Date:** 2025-12-15
**Context:** Investigation of why SSE agents spawn subagents instead of implementing
**Decision:** Include full agent files in all spawn prompts
**Status:** Implemented (commit 51a61b3)
**Reviewed by:** Pending ultrathink verification

---

## Problem Statement

SSE agents were spawning subagents instead of implementing. Initial fix added NO DELEGATION rules, but investigation revealed a deeper architectural issue: **agent `.md` files are NOT being sent to most spawned agents**.

## Discovery: Inconsistent Prompt Building

### What I Expected

The agent files (e.g., `senior_software_engineer.md`) contain ~1400 lines of detailed instructions including:
- Role definition
- Workflow steps
- Reasoning documentation requirements
- Routing instructions
- Code quality standards
- Pre-commit validation rules

I expected this content to be sent to the spawned agent as its "base prompt".

### What's Actually Happening

**Two different approaches are used:**

#### Approach A: Full Agent File Included (PM, Scout, Tech Lead validation)

```
# orchestrator.md line 966:
"Read `agents/tech_stack_scout.md` for full agent definition"

# orchestrator.md line 1155:
"Build PM prompt by reading `agents/project_manager.md` and including..."

# phase_simple.md line 829:
"Read `agents/techlead.md` and prepend"
```

These agents receive their FULL agent file content (~1000-1400 lines).

#### Approach B: Small Template Only (Developer, SSE, QA, regular Tech Lead)

```python
# phase_simple.md lines 126-159:
base_prompt = """
You are a {Agent Type} in a Claude Code Multi-Agent Dev Team.

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple
**BRANCH:** {branch}

**TASK:** {task_title}

**REQUIREMENTS:**
{task_requirements}

**MANDATORY WORKFLOW:**
1. Implement the complete solution
2. Write unit tests for new code
3. Run lint check (must pass)
4. Run build check (must pass)
5. Commit to branch: {branch}
6. Report status: READY_FOR_QA or BLOCKED

**OUTPUT FORMAT:**
Use standard response format with STATUS, FILES, TESTS, COVERAGE sections.
"""
```

This is ~25 lines, NOT the full 1400 lines from `developer.md` or `senior_software_engineer.md`.

## Full Prompt Composition

The actual prompt sent to Developer/SSE is:

```
FULL_PROMPT =
    CONTEXT_BLOCK (from context-assembler skill: ~800 tokens of prior reasoning)
    +
    SPEC_BLOCK (from specialization-loader skill: ~900-2400 tokens of tech patterns)
    +
    base_prompt (~25 lines template shown above)
```

**Missing:** The full agent `.md` file content!

## Evidence

### From phase_simple.md (lines 162-170):

```python
**D. Compose Full Prompt** (token-conscious):
```
prompt =
  {CONTEXT_BLOCK}  // Prior reasoning + packages (from context-assembler)
  +
  {SPEC_BLOCK}     // Tech identity (from specialization-loader)
  +
  base_prompt      // Role + task details
```
```

No `Read(agents/developer.md)` anywhere in this composition.

### From prompt_building.md (lines 38-51):

```
### Base Prompt
Always start with agent role and context:
```
You are a {AGENT_TYPE} in a Claude Code Multi-Agent Dev Team.

**GROUP:** {group_id}
**MODE:** {Simple|Parallel}

{code_context - if applicable}

**REQUIREMENTS:**
{task details from PM}
{user's original requirements}
```
```

Again, no instruction to include the full agent file.

## Comparison Table

| Agent | Full File Included? | Lines Sent | Evidence |
|-------|---------------------|------------|----------|
| Tech Stack Scout | YES | ~500 | orchestrator.md:966 |
| Project Manager | YES | ~1200 | orchestrator.md:1155 |
| Tech Lead (validation) | YES | ~1100 | phase_simple.md:829 |
| Developer | NO | ~25 | phase_simple.md:126-159 |
| Senior Software Engineer | NO | ~25 | Same template |
| QA Expert | NO | ~25 | phase_simple.md:552-566 |
| Tech Lead (regular) | NO | ~25 | phase_simple.md:693-728 |
| Requirements Engineer | NO | ~25 | Same template |
| Investigator | NO | ~25 | phase_simple.md:413-448 |

## Why This Matters

### What Developer/SSE is MISSING without the full agent file:

1. **Escalation awareness** - When to report ESCALATE_SENIOR
2. **Detailed workflow** - The 17-step implementation workflow
3. **Reasoning documentation** - MANDATORY understanding/completion phases
4. **Test-passing integrity** - Rules about not breaking code to pass tests
5. **Tech debt logging** - When and how to log tech debt
6. **Artifact writing** - How to write test failure artifacts
7. **Routing instructions** - The detailed decision tree for QA vs Tech Lead
8. **Code quality standards** - 100+ lines of coding standards
9. **Pre-commit validation gates** - Detailed validation requirements
10. **The NO DELEGATION rule** - Until I added it to base_prompt today

### Why SSE Spawned Subagents

The SSE didn't know it was supposed to implement! It received:
- `subagent_type="general-purpose"` → Full Task tool access
- A vague "You are a Senior Software Engineer" message
- No explicit instruction NOT to delegate

Without the full agent file telling it "YOU ARE AN IMPLEMENTER", it defaulted to using the Task tool because it had access.

## Options

### Option 1: Add Agent Files to Prompts (Recommended)

Modify phase_simple.md and phase_parallel.md to read and include agent files:

```python
# TURN 2: Compose & Spawn
agent_file = Read(f"agents/{agent_type}.md")

base_prompt = f"""
{agent_file}  # Full 1400 lines

**SESSION:** {session_id}
**GROUP:** {group_id}
...
"""
```

**Pros:**
- Agent files become authoritative
- Consistent with PM/Scout/TL-validation pattern
- All instructions reach the agent

**Cons:**
- Token usage increases (~1400 tokens per agent)
- May exceed context limits with specializations

### Option 2: Keep Small Templates, Add Critical Rules

Keep current architecture but ensure all critical rules are in base_prompt:

```python
base_prompt = """
You are a {Agent Type}...

🔴 CRITICAL RULES:
- NO DELEGATION - Do not use Task tool
- MUST document reasoning phases
- MUST validate before committing
...
"""
```

**Pros:**
- Token efficient
- Explicit critical rules

**Cons:**
- Agent files become documentation only
- Easy to forget to add new rules to templates
- Inconsistent with PM/Scout/TL-validation pattern

### Option 3: Create Summary Agent Files

Create compressed "runtime" versions of agent files:
- `agents/developer.runtime.md` (~200 lines, key rules only)
- Full files remain for documentation

**Pros:**
- Balanced token usage
- Clear separation of concerns

**Cons:**
- Two files to maintain per agent
- Risk of drift between full and runtime versions

## Recommendation

**Option 1** - Include full agent files in prompts.

Rationale:
1. Consistency with existing PM/Scout/TL-validation pattern
2. Agent files are already written and maintained
3. Token budget concerns can be managed via specialization-loader limits
4. Makes agent files authoritative, not just documentation

## Implementation (Completed)

**Commit:** `51a61b3` - Include full agent files in all spawn prompts

### Changes Made

**phase_simple.md:**
- Developer/SSE/RE spawn: Added `Read("agents/{agent_type}.md")`
- QA Expert spawn: Added `Read("agents/qa_expert.md")`
- Tech Lead spawn: Added `Read("agents/techlead.md")`
- Investigator spawn: Added `Read("agents/investigator.md")`
- SSE escalation spawn: Added `Read("agents/senior_software_engineer.md")`
- Developer continuation spawn: Added `Read("agents/developer.md")`

**phase_parallel.md:**
- Main Developer/SSE/RE spawn: Added `Read("agents/{agent_type}.md")`
- QA/Tech Lead spawn: Added `Read("agents/{agent_type}.md")`

### New Prompt Structure

```
FULL_PROMPT =
    CONTEXT_BLOCK (from context-assembler: ~800 tokens)
    +
    SPEC_BLOCK (from specialization-loader: ~900-2400 tokens)
    +
    agent_definition (from Read: ~1400 lines)
    +
    task_context (~20 lines of session/task specific info)
```

### Updated Comparison Table

| Agent | Full File Included? | Evidence |
|-------|---------------------|----------|
| Tech Stack Scout | YES | orchestrator.md:966 |
| Project Manager | YES | orchestrator.md:1155 |
| Tech Lead (all cases) | YES | phase_simple.md (updated) |
| Developer | YES | phase_simple.md (updated) |
| Senior Software Engineer | YES | phase_simple.md (updated) |
| QA Expert | YES | phase_simple.md (updated) |
| Requirements Engineer | YES | phase_simple.md (updated) |
| Investigator | YES | phase_simple.md (updated) |

**All agents now receive full definitions.**

## Open Questions

1. What's the token budget constraint for agent prompts?
2. Was the current architecture intentional (for token efficiency) or accidental?
3. Should we reduce specialization token limits to accommodate full agent files?

---

## Appendix: File References

| File | Purpose |
|------|---------|
| `agents/*.md` | Agent definitions (currently NOT sent to most agents) |
| `templates/orchestrator/phase_simple.md` | Simple mode spawn logic |
| `templates/orchestrator/phase_parallel.md` | Parallel mode spawn logic |
| `templates/prompt_building.md` | Prompt building guide |
| `agents/orchestrator.md` | Orchestrator definition |
