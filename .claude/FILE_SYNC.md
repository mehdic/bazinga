# File Synchronization Requirements

This document lists files that must be kept identical to maintain system consistency.

## Critical Sync Requirements

### Orchestrator Agent/Command Files

**Files:**
- `agents/orchestrator.md`
- `.claude/commands/bazinga.orchestrate.md`

**Requirement:** These files MUST be kept identical at all times.

**Reason:**
- The orchestrator can be invoked either as an agent or via the `/bazinga.orchestrate` slash command
- Both invocation methods must have identical behavior and instructions
- Any updates to orchestrator logic, database operations, or workflow must be reflected in both files

**How to maintain sync:**
```bash
# When updating orchestrator, copy to both locations:
cp agents/orchestrator.md .claude/commands/bazinga.orchestrate.md
# OR
cp .claude/commands/bazinga.orchestrate.md agents/orchestrator.md

# Verify they're identical:
diff -q agents/orchestrator.md .claude/commands/bazinga.orchestrate.md
```

**Important Changes:**
- Database persistence requirements (lines 68-114)
- State save instructions (lines 1679-1724)
- PM state verification (lines 685-738)
- Completion state saves (lines 1991-2046)

## Future Sync Requirements

Add any additional file sync requirements here as they are identified.
