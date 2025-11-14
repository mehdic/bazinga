# BAZINGA Orchestration System - Claude Code Documentation

This file contains important information for Claude Code when working on this project.

---

## File Synchronization Requirements

### Critical: Orchestrator Agent/Command Sync

**These files MUST be kept identical:**
- `agents/orchestrator.md`
- `.claude/commands/bazinga.orchestrate.md`

**Why:** The orchestrator can be invoked either as an agent or via the `/bazinga.orchestrate` slash command. Both invocation methods must have identical behavior and instructions.

**How to maintain sync:**
```bash
# When updating orchestrator, copy to both locations:
cp agents/orchestrator.md .claude/commands/bazinga.orchestrate.md

# Verify they're identical:
diff -q agents/orchestrator.md .claude/commands/bazinga.orchestrate.md
```

**Recent critical updates:**
- Database persistence requirements (mandatory operations)
- PM state verification with fallback mechanism
- Orchestrator state save instructions
- Task group creation and verification

---

## Project Structure

### Key Directories
- `agents/` - Agent prompt definitions (PM, Developer, QA, Tech Lead, Orchestrator)
- `.claude/commands/` - Slash command definitions
- `.claude/skills/` - Skill definitions (security-scan, test-coverage, lint-check, etc.)
- `bazinga/` - Session artifacts, database, configuration
- `dashboard/` - Web dashboard for monitoring orchestration

### Database
- Location: `bazinga/bazinga.db` (SQLite)
- Schema: See `.claude/skills/bazinga-db/references/schema.md`
- State types: `pm`, `orchestrator`, task groups
- All state must be persisted to database for dashboard and resumption

---

## Important Notes for Development

### State Persistence is Mandatory
Both PM and Orchestrator agents MUST invoke the `bazinga-db` skill to persist state at specific checkpoints. This is not optional - the dashboard, session resumption, and progress tracking all depend on this.

### Testing Configuration
- Testing mode configured in `bazinga/testing_config.json`
- QA Expert can be enabled/disabled
- See `/bazinga.configure-testing` command

### Skills Configuration
- Skills configured in `bazinga/skills_config.json`
- Skills can be marked as mandatory or disabled
- See `/bazinga.configure-skills` command

---

## Development Workflow

When making changes to orchestration logic:
1. Update the appropriate agent file in `agents/`
2. If updating orchestrator, sync both orchestrator files
3. Test with `/bazinga.orchestrate` command
4. Verify database persistence is working
5. Check dashboard displays state correctly
