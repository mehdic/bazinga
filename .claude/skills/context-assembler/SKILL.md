---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Use when preparing developer/QA/tech lead spawns with session context or checking for error patterns before agent spawn.
version: 1.0.0
allowed-tools: [Bash, Read]
---

# Context-Assembler Skill

You are the context-assembler skill. When invoked, assemble relevant context packages for agent spawns, prioritizing by relevance and respecting token budgets.

## When to Invoke This Skill

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

### Step 1: Determine Context Parameters

Extract from the calling request:
- `session_id`: Current orchestration session (REQUIRED)
- `group_id`: Task group being processed (optional)
- `agent_type`: Target agent - developer/qa_expert/tech_lead (REQUIRED)

### Step 2: Load Configuration

Read retrieval limits from `bazinga/skills_config.json`:

```bash
cat bazinga/skills_config.json 2>/dev/null | python3 -c "import sys,json; c=json.load(sys.stdin).get('context_engineering',{}); print(json.dumps(c))" 2>/dev/null || echo '{"retrieval_limits":{"developer":3,"qa_expert":5,"tech_lead":5}}'
```

Defaults: developer=3, qa_expert=5, tech_lead=5 packages.

### Step 3: Query Context Packages

Use bazinga-db skill to get relevant packages:

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "<session_id>" "<group_id>" "<agent_type>" <limit>
```

If this fails, use heuristic ranking (Step 3b).

### Step 3b: Heuristic Fallback

Apply heuristic scoring when database query fails or FTS5 unavailable:

```
score = (priority_weight * 4) + (same_group_boost * 2) + (agent_relevance * 1.5) + recency_factor
```

**Priority weights:** critical=4, high=3, medium=2, low=1

Sort by score DESC, take top N based on retrieval_limit.

### Step 4: Query Error Patterns (Optional)

For agents that previously failed, query error_patterns table:

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query <<'SQL'
SELECT signature_json, solution, confidence, occurrences
FROM error_patterns WHERE confidence > 0.7
ORDER BY confidence DESC LIMIT 3
SQL
```

### Step 5: Format Output

```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}

### Error Patterns ({count} matches)

:warning: **Known Issue**: "{message_pattern}"
> **Solution**: {solution}
> **Confidence**: {confidence} (seen {occurrences} times)

:package: +{overflow_count} more packages available (re-invoke with higher limit)
```

**Priority indicators:** `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`

### Step 6: Handle Edge Cases

**Empty packages:**
```markdown
## Context for {agent_type}

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

**Graceful degradation (on any failure):**
```markdown
## Context for {agent_type}

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

Never block execution on context-assembler failure.

---

## FTS5 Detection

Check if FTS5 is available:

```bash
sqlite3 :memory: "SELECT sqlite_compileoption_used('ENABLE_FTS5')" 2>/dev/null
```

Returns `1` if available, falls back to heuristic ranking if not.

---

## Integration with Orchestrator

```python
# 1. Invoke context-assembler
Skill(command: "context-assembler")

# 2. Include output in agent prompt
Task(
    prompt=f"""
    {context_assembler_output}

    ## Your Task
    {task_description}
    """,
    subagent_type="developer"
)
```

---

## Database Tables Used

| Table | Purpose |
|-------|---------|
| `context_packages` | Research files, findings, artifacts with priority/summary |
| `context_package_consumers` | Per-agent consumption tracking |
| `error_patterns` | Captured error signatures with solutions |

---

**For detailed documentation, examples, and configuration:** See `references/usage.md`
