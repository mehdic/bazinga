---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 1.0.0
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

When invoked, execute these steps in order:

### Step 1: Determine Context Parameters

Extract from the calling request or infer from conversation:
- `session_id`: Current orchestration session (REQUIRED)
- `group_id`: Task group being processed (optional, defaults to session-wide)
- `agent_type`: Target agent - developer/qa_expert/tech_lead (REQUIRED)
- `iteration`: Current iteration number (optional, default 0)

If parameters are missing, check recent conversation context or ask the orchestrator.

### Step 2: Load Configuration

Read retrieval limits from `bazinga/skills_config.json`:

```bash
cat bazinga/skills_config.json 2>/dev/null | python3 -c "import sys,json; c=json.load(sys.stdin).get('context_engineering',{}); print(json.dumps(c))" 2>/dev/null || echo '{"retrieval_limits":{"developer":3,"qa_expert":5,"tech_lead":5}}'
```

Extract:
- `retrieval_limits.{agent_type}` - Max packages for this agent (default: 3)
- `enable_fts5` - Whether to use FTS5 (default: false)

### Step 3: Query Context Packages

Use bazinga-db skill to get relevant packages:

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "<session_id>" "<group_id>" "<agent_type>" <limit>
```

If this fails or returns empty, proceed to Step 3b (Heuristic Fallback).

### Step 3b: Heuristic Fallback (FTS5 Unavailable or Query Failed)

If the database query fails or FTS5 is unavailable, use heuristic ranking on raw results:

**Priority Weights:**
| Priority | Weight |
|----------|--------|
| critical | 4 |
| high | 3 |
| medium | 2 |
| low | 1 |

**Scoring Formula:**
```
score = (priority_weight * 4) + (same_group_boost * 2) + (agent_relevance * 1.5) + recency_factor

Where:
- same_group_boost = 1 if package.group_id == request.group_id, else 0
- agent_relevance = 1 if agent_type in package.consumers, else 0
- recency_factor = 1 / (days_since_created + 1)
```

Sort packages by score DESC, take top N based on retrieval_limit.

### Step 4: Query Error Patterns (Optional)

If error patterns might be relevant (e.g., agent previously failed), query them via bazinga-db:

```bash
# Get the project_id from session metadata (or use 'default')
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query "SELECT COALESCE(json_extract(metadata, '$.project_id'), 'default') as project_id FROM sessions WHERE session_id = '<session_id>'"

# Then query error patterns for that project with confidence > 0.7
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query "SELECT pattern_hash, signature_json, solution, confidence, occurrences FROM error_patterns WHERE project_id = '<project_id>' AND confidence > 0.7 ORDER BY confidence DESC, occurrences DESC LIMIT 3"
```

If no session or project_id found, use 'default' as the project identifier.

Only include patterns with confidence > 0.7 in the output.

### Step 5: Format Output

Format the assembled context as markdown:

```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}

**[{PRIORITY}]** {file_path}
> {summary}

{...more packages...}

### Error Patterns ({count} matches)

{If error patterns exist and confidence > 0.7:}
:warning: **Known Issue**: "{message_pattern}"
> **Solution**: {solution}
> **Confidence**: {confidence} (seen {occurrences} times)

{If overflow exists:}
:package: +{overflow_count} more packages available (re-invoke with higher limit to expand)
```

**Priority Indicators:**
- `[CRITICAL]` - Priority: critical
- `[HIGH]` - Priority: high
- `[MEDIUM]` - Priority: medium
- `[LOW]` - Priority: low

### Step 6: Handle Edge Cases

**Empty Packages:**
If no context packages are found, output:
```markdown
## Context for {agent_type}

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

**Graceful Degradation:**
If ANY step fails (database unavailable, query error, etc.):
1. Log a warning (but do NOT block)
2. Return minimal context:
```markdown
## Context for {agent_type}

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

3. The orchestrator should NEVER block on context-assembler failure

---

## Configuration Reference

From `bazinga/skills_config.json`:

```json
{
  "context_engineering": {
    "enable_context_assembler": true,
    "enable_fts5": false,
    "retrieval_limits": {
      "developer": 3,
      "qa_expert": 5,
      "tech_lead": 5
    },
    "redaction_mode": "pattern_only",
    "token_safety_margin": 0.15
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_context_assembler` | true | Enable/disable the skill |
| `enable_fts5` | false | Use FTS5 for relevance (requires SQLite FTS5) |
| `retrieval_limits.*` | 3 | Max packages per agent type |
| `redaction_mode` | pattern_only | Secret redaction mode |
| `token_safety_margin` | 0.15 | Safety margin for token budgets |

---

## Example Invocations

### Example 1: Developer Context Assembly

**Request:**
```
Assemble context for developer spawn:
- Session: bazinga_20250212_143530
- Group: group_a
- Agent: developer
```

**Output:**
```markdown
## Context for developer

### Relevant Packages (3/7)

**[HIGH]** research/auth-patterns.md
> JWT authentication patterns for React Native apps

**[MEDIUM]** research/api-design.md
> REST API design guidelines for mobile clients

**[MEDIUM]** findings/codebase-analysis.md
> Existing authentication code in src/auth/

### Error Patterns (1 match)

:warning: **Known Issue**: "Cannot find module '@/utils'"
> **Solution**: Check tsconfig.json paths configuration - ensure baseUrl is set correctly
> **Confidence**: 0.8 (seen 3 times)

:package: +4 more packages available (re-invoke with higher limit to expand)
```

### Example 2: Empty Context

**Request:**
```
Assemble context for QA spawn:
- Session: bazinga_new_session
- Group: group_a
- Agent: qa_expert
```

**Output:**
```markdown
## Context for qa_expert

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

### Example 3: Error/Fallback

**Request:**
```
Assemble context for tech_lead spawn:
- Session: bazinga_broken_db
- Agent: tech_lead
```

**Output (if database unavailable):**
```markdown
## Context for tech_lead

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

---

## FTS5 Detection

To check if FTS5 is available in the current SQLite installation:

```bash
sqlite3 :memory: "SELECT sqlite_compileoption_used('ENABLE_FTS5')" 2>/dev/null
```

Returns `1` if FTS5 is available, `0` or error if not.

If FTS5 is unavailable, the skill automatically falls back to heuristic ranking (Step 3b).

---

## Integration with Orchestrator

The orchestrator invokes this skill before spawning agents:

```python
# 1. Invoke context-assembler
Skill(command: "context-assembler")

# 2. Capture output and include in agent prompt
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

## References

See `references/usage.md` for detailed usage documentation and integration examples.
