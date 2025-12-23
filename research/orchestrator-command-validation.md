# Orchestrator Command Validation: Preventing Parameter Mistakes

**Date:** 2025-12-17
**Context:** During integration testing, orchestrator improvised command parameters instead of following documented templates, causing errors
**Decision:** Create spawn-agent skill with JSON contract
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The orchestrator executed scripts with incorrect parameters:
- Used `--task-description` (doesn't exist) instead of `--task-title` + `--task-requirements`
- Used 2 args for `create-session` instead of 3

**Root cause:** Free-form shell command construction instead of structured skill invocation.

## Multi-LLM Review Integration

### Critical Feedback from OpenAI (Incorporated)

1. **Misalignment with design**: The orchestrator should use `Skill(command: "prompt-builder")` not direct python scripts. My original proposal (shell templates) conflicts with orchestrator's own rules.

2. **Template duplication causes drift**: Embedding command templates in multiple places guarantees future inconsistency.

3. **CLI args are fragile**: Shell escaping, arg length limits, and quoting issues will continue causing problems.

### Rejected Suggestions

1. **JSON Schema + version handshake**: Over-engineering for current needs. Skills already have Python argparse validation.

2. **Staged rollout with feature flags**: Unnecessary complexity - we control all code.

## Revised Solution: spawn-agent Skill

Create a `spawn-agent` skill that:
1. Accepts structured parameters (agent_type, session_id, task_title, etc.)
2. Internally calls prompt-builder with correct syntax
3. Returns JSON result with prompt_file path
4. Validates required fields per agent type

### Interface

```
Skill(command: "spawn-agent")

Input (via skill prompt):
  agent_type: developer
  session_id: bazinga_20251217_120000
  group_id: CALC
  task_title: Implement calculator
  task_requirements: Create add/subtract functions
  branch: main
  mode: simple
  testing_mode: full

Output (JSON):
{
  "success": true,
  "prompt_file": "bazinga/prompts/bazinga_20251217_120000/developer_CALC.md",
  "model": "haiku",
  "markers_valid": true
}
```

### Why This Solves the Problem

| Issue | How spawn-agent fixes it |
|-------|-------------------------|
| Wrong parameter names | Skill validates; no CLI arg construction |
| Missing required args | Skill enforces per agent_type |
| Shell escaping issues | No shell commands; structured input |
| Template drift | Single source: the skill itself |
| Orchestrator improvising | Skill interface is the contract |

## Implementation Plan

### Phase 1: Create spawn-agent Skill
- New skill at `.claude/skills/spawn-agent/`
- SKILL.md with structured input format
- Script calls prompt_builder.py internally with validated args
- Returns JSON with prompt_file path

### Phase 2: Update Orchestrator Templates
- Replace shell commands with `Skill(command: "spawn-agent")`
- Remove embedded command syntax from templates
- Parse JSON response for prompt_file

### Phase 3: Add "Did You Mean?" to prompt_builder.py
- Catch unknown args and suggest corrections
- Helps when testing manually outside of skill

## Critical Analysis

### Pros ✅
- Eliminates free-form command construction
- Single source of truth (the skill)
- Structured interface prevents typos
- JSON output is machine-parseable

### Cons ⚠️
- Another skill to maintain
- Migration effort to update templates
- Skill invocation syntax must be learned

### Verdict

This is the correct architectural solution. It aligns with the principle that the orchestrator should use skills, not construct shell commands. The initial proposal (strict mode + templates) was a band-aid; this solves the root cause.

## Files to Create/Modify

**New:**
- `.claude/skills/spawn-agent/SKILL.md`
- `.claude/skills/spawn-agent/scripts/spawn_agent.py`

**Modify:**
- `templates/orchestrator/phase_simple.md` - Use skill instead of shell
- `templates/orchestrator/phase_parallel.md` - Use skill instead of shell
- `.claude/skills/prompt-builder/scripts/prompt_builder.py` - Add "did you mean?" for unknown args

## Decision Rationale

OpenAI's review correctly identified that my original proposal conflicts with the orchestrator's design principles. The orchestrator should not be constructing shell commands - it should invoke skills with structured parameters. The spawn-agent skill encapsulates the complexity and provides a stable, validated interface.

## References

- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
- Current templates: `templates/orchestrator/phase_simple.md`
- prompt-builder skill: `.claude/skills/prompt-builder/`
