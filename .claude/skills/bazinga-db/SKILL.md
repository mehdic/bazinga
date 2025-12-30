---
name: bazinga-db
description: DEPRECATED - Use domain-specific skills instead. Routes to bazinga-db-core, bazinga-db-workflow, bazinga-db-agents, or bazinga-db-context.
version: 2.0.0
allowed-tools: [Bash, Read]
---

# BAZINGA-DB (Deprecated Router)

**This skill is deprecated.** Use domain-specific skills instead:

| Domain | Skill | Use For |
|--------|-------|---------|
| Sessions & State | `bazinga-db-core` | Sessions, state snapshots, dashboard |
| Tasks & Plans | `bazinga-db-workflow` | Task groups, development plans, success criteria |
| Agent Tracking | `bazinga-db-agents` | Logs, reasoning, tokens, skill output, events |
| Context & Learning | `bazinga-db-context` | Context packages, error patterns, strategies |

## Command Routing Table

| Command | Target Skill |
|---------|--------------|
| `create-session`, `get-session`, `list-sessions` | `bazinga-db-core` |
| `update-session-status`, `save-state`, `get-state` | `bazinga-db-core` |
| `dashboard-snapshot`, `query`, `integrity-check` | `bazinga-db-core` |
| `create-task-group`, `update-task-group`, `get-task-groups` | `bazinga-db-workflow` |
| `save-development-plan`, `get-development-plan`, `update-plan-progress` | `bazinga-db-workflow` |
| `save-success-criteria`, `get-success-criteria`, `update-success-criterion` | `bazinga-db-workflow` |
| `log-interaction`, `stream-logs` | `bazinga-db-agents` |
| `save-reasoning`, `get-reasoning`, `reasoning-timeline` | `bazinga-db-agents` |
| `log-tokens`, `token-summary` | `bazinga-db-agents` |
| `save-skill-output`, `get-skill-output`, `check-skill-evidence` | `bazinga-db-agents` |
| `save-event`, `get-events` | `bazinga-db-agents` |
| `save-context-package`, `get-context-packages`, `mark-context-consumed` | `bazinga-db-context` |
| `save-error-pattern`, `get-error-patterns` | `bazinga-db-context` |
| `save-strategy`, `get-strategies` | `bazinga-db-context` |

## Quick Reference

**Script location:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`
**Full CLI help:** `python3 .../bazinga_db.py help`
**Schema docs:** `.claude/skills/bazinga-db/references/schema.md`
**Command examples:** `.claude/skills/bazinga-db/references/command_examples.md`

## If You're Here By Mistake

1. Identify what you're trying to do
2. Invoke the correct domain skill:
   - Session ops? → `Skill(command: "bazinga-db-core")`
   - Task groups? → `Skill(command: "bazinga-db-workflow")`
   - Logging/reasoning? → `Skill(command: "bazinga-db-agents")`
   - Context packages? → `Skill(command: "bazinga-db-context")`

## Migration Notes

The original monolithic bazinga-db skill (v1.x, 887 lines) has been split into 4 domain-focused skills for better maintainability and to stay within file size limits.

**All scripts remain in this directory:**
- `scripts/bazinga_db.py` - Main CLI (unchanged)
- `scripts/init_db.py` - Database initialization
- `scripts/init_session.py` - Session creation helper

**All references remain in this directory:**
- `references/schema.md` - Full database schema
- `references/command_examples.md` - Detailed command examples
