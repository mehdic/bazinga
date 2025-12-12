---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 0.1.0
allowed-tools: [Bash, Read]
---

# Context-Assembler Skill

You are the context-assembler skill. When invoked, you assemble relevant context packages for agent spawns, prioritizing by relevance and respecting token budgets.

## When to Invoke This Skill

**Invoke this skill when:**
- Orchestrator prepares to spawn an agent and needs relevant context
- Any agent mentions "assemble context", "get context packages", or "context-assembler"
- Preparing developer/QA/tech lead spawns with session context
- Need to check for relevant error patterns before agent spawn

**Do NOT invoke when:**
- No active orchestration session exists
- Manually reading specific files (use Read tool directly)
- Working outside BAZINGA orchestration

---

## Your Task

When invoked:
1. Query bazinga-db for relevant context packages
2. Rank packages using heuristic relevance scoring
3. Apply token budget constraints
4. Format output with prioritized packages and overflow indicator
5. Include relevant error patterns if any match

---

## Status: Phase 1 Placeholder

This skill will be fully implemented in Phase 3 (User Story 1). Current capabilities:
- Directory structure established
- Configuration added to skills_config.json
- Reference documentation available

**Implementation pending:**
- [ ] Heuristic relevance ranking (T011)
- [ ] Package retrieval via bazinga-db (T012)
- [ ] Output formatting (T013)
- [ ] Empty packages handling (T014)
- [ ] FTS5 fallback (T015)
- [ ] Graceful degradation (T016)

---

## Inputs

```
session_id: str      # Current orchestration session
group_id: str        # Task group being processed
agent_type: str      # developer/qa_expert/tech_lead
model: str           # haiku/sonnet/opus (for token budgeting)
```

## Output Format

```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})
{ranked package summaries with priority indicators}

### Error Patterns ({count} matches)
{relevant error hints if any}

📦 +{overflow_count} more packages available (use context-fetch skill to expand)
```

---

## References

See `references/usage.md` for detailed usage documentation and integration examples.
