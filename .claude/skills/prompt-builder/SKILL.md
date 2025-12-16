---
name: prompt-builder
description: Build complete agent prompts deterministically via Python script. Use BEFORE spawning any BAZINGA agent (Developer, QA, Tech Lead, PM, etc.).
version: 1.0.0
author: BAZINGA Team
tags: [orchestration, prompts, agents]
allowed-tools: [Bash]
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
- Returns the complete prompt to stdout

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

### Step 1: Extract Parameters from Orchestrator Context

Parse the following from the orchestrator's context or message:
- `agent_type` (required): developer, qa_expert, tech_lead, project_manager, investigator, requirements_engineer, senior_software_engineer
- `session_id` (required): Current session ID
- `group_id` (required for non-PM): Task group ID (e.g., "AUTH", "API")
- `task_title`: Brief title of the task
- `task_requirements`: Detailed requirements
- `branch`: Git branch name
- `mode`: simple or parallel
- `testing_mode`: full, minimal, or disabled
- `model`: haiku, sonnet, or opus (for token budgeting)

**For retries, also extract:**
- `qa_feedback`: QA failure details (if retrying after QA fail)
- `tl_feedback`: Tech Lead feedback (if retrying after changes requested)

**For PM spawns, also extract:**
- `pm_state`: PM state JSON from database
- `resume_context`: Context for PM resume spawns

### Step 2: Call the Python Script

Run the prompt builder script with extracted parameters:

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
  --model "{model}"
```

**For retries, add:**
```bash
  --qa-feedback "{qa_feedback}" \
  --tl-feedback "{tl_feedback}"
```

**For PM spawns, add:**
```bash
  --pm-state '{pm_state_json}' \
  --resume-context "{resume_context}"
```

### Step 3: Return the Complete Prompt

- The script outputs the COMPLETE prompt to stdout
- The script outputs metadata to stderr (lines, tokens, validation status)
- Return the stdout content to the orchestrator

## What the Script Does Internally

1. Queries database for `task_groups.specializations` → reads template files
2. Queries database for `context_packages`, `error_patterns`, `agent_reasoning`
3. Reads full agent definition file (`agents/*.md`) - 800-2500 lines
4. Applies token budgets per model (haiku=900, sonnet=1800, opus=2400)
5. Validates required markers are present (e.g., "READY_FOR_QA", "NO DELEGATION")
6. Returns composed prompt with: context + specialization + agent file + task

## Output Format

The skill returns the complete prompt text ready for use in a Task spawn.

## Error Handling

| Error | Exit Code | Meaning |
|-------|-----------|---------|
| Missing markers | 1 | Agent file corrupted/incomplete - STOP |
| Agent file not found | 1 | Invalid agent_type or missing file - STOP |
| Unknown agent type | 1 | Check agent_type parameter |
| Database not found | Warning | Proceeds without DB data (specializations/context empty) |

If the script fails, do NOT proceed with agent spawn. Report the error to orchestrator.
