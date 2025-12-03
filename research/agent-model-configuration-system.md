# Agent Model Configuration System: Correction Analysis

**Date:** 2025-12-03
**Context:** Correcting incorrect implementation of agent model selection
**Decision:** Update both model_selection.json AND frontmatter for requirements_engineer
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

In the previous session, `model: opus` was added to the frontmatter of `agents/requirements_engineer.md`. This partially follows the existing pattern (other agents have model in frontmatter), but the JSON config was NOT updated, creating a mismatch.

## Multi-LLM Review Integration

### Key Insights from OpenAI GPT-5 Review

1. **JSON is the single source of truth** - The orchestrator reads from `bazinga/model_selection.json` at session start and caches model assignments (no DB layer for model config)
2. **Frontmatter is used across all agents** - It serves as documentation hints matching the JSON values
3. **Consistency matters** - Frontmatter and JSON should match to avoid confusion

### Agent Files with `model:` in Frontmatter (Current State)

| Agent | Frontmatter | JSON | Match? |
|-------|-------------|------|--------|
| developer | haiku | haiku | ✅ |
| senior_software_engineer | sonnet | sonnet | ✅ |
| qa_expert | (none) | sonnet | - |
| tech_lead | opus | opus | ✅ |
| project_manager | opus | opus | ✅ |
| orchestrator | sonnet | sonnet | ✅ |
| requirements_engineer | opus | sonnet | ❌ MISMATCH |
| investigator | (none) | opus | - |
| validator | (none) | sonnet | - |

### Incorporated Feedback

1. **Keep frontmatter consistent with JSON** - Frontmatter serves as documentation
2. **Update JSON as authoritative source** - This is what orchestrator actually reads
3. **Consider cost implications** - Opus is more expensive than Sonnet

### Rejected Suggestions (With Reasoning)

1. **DB migration step** - Not needed for new sessions; DB starts empty and loads from JSON
2. **Conditional RE model selection** - Over-engineering for current needs; user explicitly wants RE on Opus
3. **Remove all frontmatter model fields** - Existing pattern is useful for documentation

## Correct Architecture

### Model Configuration: Single Source of Truth

```
bazinga/model_selection.json = AUTHORITATIVE SOURCE
Agent frontmatter model: field = Documentation only (NOT read by orchestrator)
```

**Decision:** No DB layer for model config. The JSON file is the single source of truth. This keeps the system simple and avoids sync complexity.

### How Orchestrator Uses Model Config

1. At session start, orchestrator reads `bazinga/model_selection.json`
2. Caches model assignments in `MODEL_CONFIG` for the session
3. Uses `MODEL_CONFIG` values in all Task invocations

### Task Invocation Pattern

```python
Task(
  subagent_type="general-purpose",
  model=MODEL_CONFIG["requirements_engineer"],  # From JSON file
  description="Research: {task}",
  prompt=[agent_prompt]
)
```

## Correct Implementation

### Step 1: Update model_selection.json (Authoritative Source)
Change requirements_engineer model from "sonnet" to "opus":
```json
"requirements_engineer": {
  "model": "opus",
  "rationale": "Complex requirements analysis, codebase discovery, and risk assessment requiring deep reasoning"
}
```

### Step 2: Keep frontmatter consistent
The `model: opus` in requirements_engineer.md frontmatter should STAY - it documents the intended model and matches the JSON value after update.

## Configuration Files Overview

The project uses three main configuration files in `bazinga/`:

### 1. `model_selection.json`
**Purpose:** Controls which AI model each agent uses

**Structure:**
- `agents`: Model assignment for each agent
- `escalation_rules`: When to escalate to stronger models
- `task_type_routing`: Route certain task types to specific agents

**Key Rules:**
- Tech Lead and PM: Always Opus (non-negotiable)
- Developer: Starts on Haiku (cost efficiency)
- Escalation after failures triggers model upgrade

**Precedence:** JSON only (orchestrator caches at session start)

### 2. `skills_config.json`
**Purpose:** Controls which skills each agent can/must use

**Modes:**
- `mandatory`: Skill always runs (automatic)
- `optional`: Framework-driven, agent can invoke if needed
- `disabled`: Skill not available

**Per-Agent Configuration:** Each agent has different skill requirements

### 3. `challenge_levels.json`
**Purpose:** QA Expert test challenge progression

**5 Levels:**
1. Boundary Probing (edge cases)
2. Mutation Analysis (test completeness)
3. Behavioral Contracts (pre/post conditions)
4. Security Adversary (security testing)
5. Production Chaos (failure scenarios)

**Escalation:** Levels 3-5 failures escalate to Senior Software Engineer

## Final Implementation Plan

1. ✅ Create this research document
2. ✅ Run LLM reviews
3. ✅ Integrate feedback (documented above)
4. ✅ Update model_selection.json: requirements_engineer → opus
5. ✅ Keep frontmatter `model: opus` (matches JSON after update)
6. ✅ Add config documentation to claude.md
7. ✅ Commit and push

## References

- `bazinga/model_selection.json` - Model configuration (authoritative)
- `bazinga/skills_config.json` - Skills configuration
- `bazinga/challenge_levels.json` - QA challenge levels
- `agents/orchestrator.md` - How orchestrator spawns agents (lines 564-598)
