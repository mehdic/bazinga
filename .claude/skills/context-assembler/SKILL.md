---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 1.1.0
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
- `group_id`: Task group being processed (OPTIONAL - use empty string "" if not provided)
- `agent_type`: Target agent - developer/qa_expert/tech_lead (REQUIRED)
- `iteration`: Current iteration number (optional, default 0)

If `session_id` or `agent_type` are missing, check recent conversation context or ask the orchestrator.

### Step 2: Load Configuration and Check FTS5

**Step 2a: Load retrieval limit for this agent type:**

```bash
# Extract retrieval limit for the specific agent type (defaults to 3 if not configured)
AGENT_TYPE="developer"  # Replace with actual agent_type
LIMIT=$(cat bazinga/skills_config.json 2>/dev/null | python3 -c "
import sys, json
try:
    c = json.load(sys.stdin).get('context_engineering', {})
    limits = c.get('retrieval_limits', {})
    print(limits.get('$AGENT_TYPE', 3))
except:
    print(3)
" 2>/dev/null || echo 3)
echo "Retrieval limit for $AGENT_TYPE: $LIMIT"
```

Default limits: developer=3, qa_expert=5, tech_lead=5

**Step 2b: Check FTS5 availability:**

```bash
# Test FTS5 support by attempting to create a virtual table
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE VIRTUAL TABLE test USING fts5(x)')
    print('FTS5_AVAILABLE=true')
except:
    print('FTS5_AVAILABLE=false')
" 2>/dev/null || echo "FTS5_AVAILABLE=false"
```

If FTS5 is unavailable, Step 3 may return less optimal ranking; Step 3b provides heuristic fallback.

### Step 3: Query Context Packages

**With group_id:**
```bash
# Use shell variables - do NOT interpolate user input directly into commands
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"
AGENT_TYPE="developer"
LIMIT=3

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "$SESSION_ID" "$GROUP_ID" "$AGENT_TYPE" "$LIMIT"
```

**Without group_id (session-wide):**
```bash
# Pass empty string for group_id to get session-wide packages
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "$SESSION_ID" "" "$AGENT_TYPE" "$LIMIT"
```

**Parse the JSON response:**
- `packages`: Array of context packages with `id`, `file_path`, `priority`, `summary`
- `total_available`: Total packages matching criteria (for overflow calculation)
- If `total_available` > `LIMIT`, there are more packages available

If this command fails or returns empty `packages`, proceed to Step 3b.

### Step 3b: Heuristic Fallback (Query Failed or FTS5 Unavailable)

**First, fetch raw context packages from database:**

```bash
# Fetch all packages for this session (with optional group filter)
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"  # or empty string for session-wide

# Query raw packages - use parameterized approach via bazinga-db
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query \
  "SELECT id, file_path, priority, summary, group_id, created_at FROM context_packages WHERE session_id = '$SESSION_ID'"
```

**Then apply heuristic ranking:**

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
- agent_relevance = 1 if agent_type appears in package consumers, else 0
- recency_factor = 1 / (days_since_created + 1)
```

Sort packages by score DESC, take top N based on retrieval_limit.
Calculate: `overflow_count = max(0, total_packages - limit)`

### Step 4: Query Error Patterns (Optional)

If the agent previously failed or error patterns might be relevant:

**Step 4a: Get project_id from session:**
```bash
SESSION_ID="bazinga_20250212_143530"

# Retrieve project_id (defaults to 'default' if not set)
PROJECT_ID=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query \
  "SELECT COALESCE(json_extract(metadata, '\$.project_id'), 'default') as pid FROM sessions WHERE session_id = '$SESSION_ID'" \
  2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin); print(r[0]['pid'] if r else 'default')" 2>/dev/null || echo "default")
```

**Step 4b: Query matching error patterns:**
```bash
# Filter by project_id and optionally session_id for more specific matches
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query \
  "SELECT signature_json, solution, confidence, occurrences FROM error_patterns WHERE project_id = '$PROJECT_ID' AND confidence > 0.7 ORDER BY confidence DESC, occurrences DESC LIMIT 3"
```

Only include patterns with confidence > 0.7 in the output.

### Step 5: Format Output

**Compute display values:**
- `count` = number of packages returned (up to limit)
- `available` = total_available from Step 3 response (or total from Step 3b query)
- `overflow_count` = max(0, available - count)

**Format as markdown:**

```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}

**[{PRIORITY}]** {file_path}
> {summary}

### Error Patterns ({pattern_count} matches)

:warning: **Known Issue**: "{error_signature}"
> **Solution**: {solution}
> **Confidence**: {confidence} (seen {occurrences} times)

:package: +{overflow_count} more packages available (re-invoke with higher limit to expand)
```

**Priority Indicators:**
- `[CRITICAL]` - Priority: critical
- `[HIGH]` - Priority: high
- `[MEDIUM]` - Priority: medium
- `[LOW]` - Priority: low

**Only show overflow indicator if overflow_count > 0.**

### Step 6: Handle Edge Cases

**Empty Packages:**
If no context packages are found (count=0, available=0):
```markdown
## Context for {agent_type}

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

**Graceful Degradation:**
If ANY step fails (database unavailable, query error, etc.):
1. Log a warning (but do NOT block execution)
2. Return minimal context:
```markdown
## Context for {agent_type}

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

3. **CRITICAL**: The orchestrator should NEVER block on context-assembler failure

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

### Example 2: Session-Wide Context (No Group)

**Request:**
```
Assemble context for tech_lead spawn:
- Session: bazinga_20250212_143530
- Group: (none - session-wide)
- Agent: tech_lead
```

**Commands used:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "bazinga_20250212_143530" "" "tech_lead" 5
```

### Example 3: Empty Context

**Output:**
```markdown
## Context for qa_expert

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

### Example 4: Error/Fallback

**Output (if database unavailable):**
```markdown
## Context for tech_lead

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

---

## Security Notes

**Parameter Handling:**
- Always assign user-provided values to shell variables first
- Use quoted variable expansion (`"$VAR"`) in commands
- The bazinga-db CLI uses positional arguments (safer than string interpolation)
- Avoid constructing SQL strings with raw user input

**Example of safe vs unsafe:**
```bash
# SAFE: Use shell variables with quotes
SESSION_ID="user_provided_session"
python3 ... --quiet get-context-packages "$SESSION_ID" "$GROUP_ID" "$AGENT_TYPE" "$LIMIT"

# UNSAFE: Direct string interpolation (avoid this)
python3 ... --quiet query "SELECT * FROM t WHERE id = 'user_input'"
```

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
| `sessions` | Session metadata including project_id |

---

## References

See `references/usage.md` for detailed usage documentation and integration examples.
