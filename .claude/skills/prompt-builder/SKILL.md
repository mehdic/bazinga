---
name: prompt-builder
description: Build complete agent prompts deterministically via Python script. Use BEFORE spawning any BAZINGA agent (Developer, QA, Tech Lead, PM, etc.).
version: 2.0.0
author: BAZINGA Team
tags: [orchestration, prompts, agents]
allowed-tools: [Bash, Read, Write]
---

# Prompt Builder Skill

You are the prompt-builder skill. Your role is to build complete agent prompts by calling `prompt_builder.py`, which handles everything deterministically.

## Overview

This skill builds complete agent prompts by calling a Python script that:
- Reads specializations from database (task_groups.specializations)
- Reads context from database (context_packages, error_patterns, reasoning)
- Reads full agent definition files from filesystem
- Applies token budgets per model
- Validates required markers are present
- Saves prompt to file and returns JSON result

## Prerequisites

- Database must be initialized (`bazinga/bazinga.db` exists)
- Config must be seeded (run `config-seeder` skill first at session start)
- Agent files must exist in `agents/` directory

## When to Invoke This Skill

- **RIGHT BEFORE** spawning any BAZINGA agent
- When orchestrator needs a complete prompt for Developer, QA Expert, Tech Lead, PM, Investigator, or Requirements Engineer
- Called ON-DEMAND to get the latest context from database

## Your Task

When invoked, you must:

### Step 1: Read Parameters File

The orchestrator writes a params JSON file before invoking this skill. Look for it at:

```
bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json
```

Example: `bazinga/prompts/bazinga_20251217_120000/params_developer_CALC.json`

**Params file format:**
```json
{
  "agent_type": "developer",
  "session_id": "bazinga_20251217_120000",
  "group_id": "CALC",
  "task_title": "Implement calculator",
  "task_requirements": "Create add/subtract functions",
  "branch": "main",
  "mode": "simple",
  "testing_mode": "full",
  "model": "haiku",
  "output_file": "bazinga/prompts/bazinga_20251217_120000/developer_CALC.md"
}
```

**Additional fields for retries:**
```json
{
  "qa_feedback": "Tests failed: test_add expected 4, got 5",
  "tl_feedback": "Error handling needs improvement"
}
```

**Additional fields for CRP (Compact Return Protocol):**
```json
{
  "prior_handoff_file": "bazinga/artifacts/bazinga_20251217_120000/CALC/handoff_developer.json"
}
```

**Additional fields for PM spawns:**
```json
{
  "pm_state": "{...json...}",
  "resume_context": "Resuming after developer completion"
}
```

### Step 2: Call the Python Script

Run the prompt builder with the params file:

```bash
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py --params-file "bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json"
```

The script will:
1. Read all parameters from the JSON file
2. Build the complete prompt
3. Save prompt to `output_file` path
4. Output JSON result to stdout

### Step 3: Return JSON Result to Orchestrator

The script outputs JSON to stdout:

**Success response:**
```json
{
  "success": true,
  "prompt_file": "bazinga/prompts/bazinga_20251217_120000/developer_CALC.md",
  "tokens_estimate": 10728,
  "lines": 1406,
  "markers_ok": true,
  "missing_markers": [],
  "error": null
}
```

**Error response:**
```json
{
  "success": false,
  "prompt_file": null,
  "tokens_estimate": 0,
  "lines": 0,
  "markers_ok": false,
  "missing_markers": ["READY_FOR_QA"],
  "error": "Prompt validation failed - missing required markers"
}
```

**Return this JSON to the orchestrator** so it can:
1. Verify `success` is `true`
2. Read prompt from `prompt_file` for the Task spawn
3. Check `markers_ok` is `true`

### Step 4: IMMEDIATELY Spawn Agent (CRITICAL - SAME TURN)

**🔴 DO NOT STOP after receiving JSON. IMMEDIATELY call Task() to spawn the agent.**

After verifying `success: true`, spawn the agent in the SAME assistant turn:

```
Task(
  subagent_type: "general-purpose",
  model: "{haiku|sonnet|opus}",
  description: "{agent_type} working on {group_id}",
  prompt: "FIRST: Read {prompt_file} which contains your complete instructions.
THEN: Execute ALL instructions in that file.
Do NOT proceed without reading the file first."
)
```

**🚫 ANTI-PATTERN:**
```
❌ WRONG: "Prompt built successfully. JSON result: {...}" [STOPS - turn ends]
   → Agent never spawns. Workflow hangs until user says "continue".

✅ CORRECT: "Prompt built successfully." [IMMEDIATELY calls Task() with prompt_file]
   → Agent spawns automatically. Workflow continues.
```

**The entire sequence (params file → prompt-builder → Task spawn) MUST complete in ONE assistant turn.**

## Params File Reference

| Field | Required | Example | Description |
|-------|----------|---------|-------------|
| `agent_type` | Yes | `developer` | developer, qa_expert, tech_lead, project_manager, etc. |
| `session_id` | Yes | `bazinga_20251217_120000` | Current session ID |
| `group_id` | Non-PM | `CALC` | Task group ID |
| `task_title` | No | `Implement calculator` | Brief title |
| `task_requirements` | No | `Create functions...` | Detailed requirements |
| `branch` | Yes | `main` | Git branch name |
| `mode` | Yes | `simple` | simple or parallel |
| `testing_mode` | Yes | `full` | full, minimal, or disabled |
| `model` | No | `haiku` | haiku, sonnet, or opus (default: sonnet) |
| `output_file` | No | `bazinga/prompts/.../dev.md` | Where to save prompt |
| `qa_feedback` | No | `Tests failed...` | For developer retry after QA fail |
| `tl_feedback` | No | `Needs refactoring` | For developer retry after TL review |
| `pm_state` | No | `{...json...}` | PM state for resume spawns |
| `resume_context` | No | `Resuming after...` | Context for PM resume |
| `prior_handoff_file` | No | `bazinga/artifacts/.../handoff_developer.json` | CRP: Prior agent's handoff file (see behavior below) |

**`prior_handoff_file` Behavior:**
- If path is valid and file exists: Handoff section added with instruction to read file
- If path is invalid (traversal attempt, wrong pattern): Warning logged, section omitted
- If path is valid but file doesn't exist: Warning logged, section omitted (agent proceeds without prior context)
- Path validation: Must start with `bazinga/artifacts/`, match `handoff_*.json` pattern, no path traversal (`../`)

## What the Script Does Internally

1. Reads parameters from JSON file
2. Queries database for `task_groups.specializations` → reads template files
3. Queries database for `context_packages`, `error_patterns`, `agent_reasoning`
4. Reads full agent definition file (`agents/*.md`) - 800-2500 lines
5. Applies token budgets per model (haiku=900, sonnet=1800, opus=2400)
6. Validates required markers are present (e.g., "READY_FOR_QA", "NO DELEGATION")
7. Saves prompt to `output_file`
8. Returns JSON result to stdout

## Error Handling

| Error | JSON Response | Action |
|-------|---------------|--------|
| Params file not found | `success: false`, `error: "Params file not found"` | Check file path |
| Invalid JSON in params | `success: false`, `error: "Invalid JSON..."` | Fix params file |
| Missing markers | `success: false`, `markers_ok: false` | Agent file corrupted |
| Agent file not found | `success: false`, `error: "Agent file not found"` | Invalid agent_type |
| Database not found | Warning, continues | Proceeds without DB data |

If the result has `success: false`, do NOT proceed with agent spawn. Report the error to orchestrator.

## Legacy CLI Mode (Backward Compatibility)

The script still supports direct CLI invocation for manual testing:

```bash
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
  --agent-type developer \
  --session-id "bazinga_123" \
  --branch "main" \
  --mode "simple" \
  --testing-mode "full"
```

Add `--json-output` to get JSON response in CLI mode.
