---
name: config-seeder
description: Seed JSON configuration files into database. Use ONCE at BAZINGA session initialization, BEFORE spawning PM.
version: 1.0.0
author: BAZINGA Team
tags: [orchestration, config, initialization]
allowed-tools: [Bash]
---

# Config Seeder Skill

You are the config-seeder skill. Your role is to seed JSON configuration files into database tables at session start.

## Overview

This skill seeds workflow configuration from JSON files into database tables:
- `bazinga/config/transitions.json` → `workflow_transitions` table
- `bazinga/config/agent-markers.json` → `agent_markers` table
- `_special_rules` from transitions.json → `workflow_special_rules` table

## Prerequisites

- Database must be initialized (`bazinga/bazinga.db` exists)
- Config files must exist:
  - `bazinga/config/transitions.json`
  - `bazinga/config/agent-markers.json`

## When to Invoke This Skill

- **ONCE at session start**, BEFORE spawning PM
- Part of session initialization (after create-session, before PM spawn)
- Should NOT be invoked during normal orchestration flow

## Your Task

When invoked, you must:

### Step 1: Call the Seed Script

```bash
python3 .claude/skills/config-seeder/scripts/seed_configs.py --all
```

### Step 2: Verify Success

Expected output on success:
```
Seeded 45 transitions
Seeded 7 agent marker sets
Seeded 5 special rules
✅ Config seeding complete
```

### Step 3: Report Result

If successful:
- Report: "Configuration seeded successfully"
- Orchestration can proceed

If failed:
- Report the error message
- Orchestration CANNOT proceed without routing config

## What Gets Seeded

### Transitions (45+ entries)

State machine rules for routing:
- `developer` + `READY_FOR_QA` → `qa_expert`
- `developer` + `READY_FOR_REVIEW` → `tech_lead`
- `qa_expert` + `PASS` → `tech_lead`
- `tech_lead` + `APPROVED` → merge → check phase
- etc.

### Agent Markers (7 entries)

Required markers per agent type:
- `developer`: "NO DELEGATION", "READY_FOR_QA", "BLOCKED", etc.
- `qa_expert`: "PASS", "FAIL", "Challenge Level", etc.
- `tech_lead`: "APPROVED", "CHANGES_REQUESTED", etc.
- etc.

### Special Rules (5 entries)

Workflow modification rules:
- `testing_mode_disabled`: Skip QA entirely
- `testing_mode_minimal`: Skip QA Expert
- `escalation_after_failures`: Escalate to SSE after 2 failures
- `security_sensitive`: Force SSE + mandatory TL review
- `research_tasks`: Route to RE with limited parallelism

## Output Format

Return success/failure message. No structured output needed.

## Error Handling

| Error | Meaning |
|-------|---------|
| Config file not found | JSON files missing - check bazinga/config/ |
| Database not found | Run init_db.py first |
| Insert failed | Database schema mismatch - run migration |

If seeding fails, orchestration CANNOT proceed. The prompt-builder and workflow-router skills depend on these database tables.
