---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 1.3.0
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
- `model`: Model being used - haiku/sonnet/opus or full model ID (OPTIONAL, for token budgeting)
- `current_tokens`: Current token usage in conversation (OPTIONAL, for zone detection)
- `iteration`: Current iteration number (optional, default 0)

If `session_id` or `agent_type` are missing, check recent conversation context or ask the orchestrator.

### Step 2: Load Configuration and Check FTS5

**Step 2a: Load retrieval limit for this agent type:**

```bash
# Extract retrieval limit for the specific agent type
AGENT_TYPE="developer"  # Replace with actual agent_type

# Pass AGENT_TYPE via command-line argument (not string interpolation)
LIMIT=$(cat bazinga/skills_config.json 2>/dev/null | python3 -c "
import sys, json
agent = sys.argv[1] if len(sys.argv) > 1 else 'developer'
defaults = {'developer': 3, 'senior_software_engineer': 5, 'qa_expert': 5, 'tech_lead': 5}
try:
    c = json.load(sys.stdin).get('context_engineering', {})
    limits = c.get('retrieval_limits', {})
    print(limits.get(agent, defaults.get(agent, 3)))
except:
    print(defaults.get(agent, 3))
" "$AGENT_TYPE" 2>/dev/null || echo 3)
echo "Retrieval limit for $AGENT_TYPE: $LIMIT"
```

Default limits: developer=3, senior_software_engineer=5, qa_expert=5, tech_lead=5

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

**Step 2c: Determine token zone and budget:**

```bash
# Token estimation with tiktoken (with fallback to character estimation)
# Input: MODEL, CURRENT_TOKENS (from Step 1)
MODEL="sonnet"  # or "haiku", "opus", or full model ID
CURRENT_TOKENS=0  # Current usage if known, else 0

python3 -c "
import sys
try:
    import tiktoken
    enc = tiktoken.get_encoding('cl100k_base')
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

# Model context limits (conservative estimates)
MODEL_LIMITS = {
    'haiku': 200000, 'claude-3-5-haiku': 200000,
    'sonnet': 200000, 'claude-sonnet-4-20250514': 200000, 'claude-3-5-sonnet': 200000,
    'opus': 200000, 'claude-opus-4-20250514': 200000
}

# Safety margin from config (default 15%)
SAFETY_MARGIN = 0.15
model = sys.argv[1] if len(sys.argv) > 1 else 'sonnet'
current = int(sys.argv[2]) if len(sys.argv) > 2 else 0

# Normalize model name
model_key = model.lower()
for key in MODEL_LIMITS:
    if key in model_key:
        model_key = key
        break

limit = MODEL_LIMITS.get(model_key, 200000)
effective_limit = int(limit * (1 - SAFETY_MARGIN))
usage_pct = (current / effective_limit * 100) if effective_limit > 0 else 0

# Determine zone
if usage_pct >= 95:
    zone = 'Emergency'
elif usage_pct >= 85:
    zone = 'Wrap-up'
elif usage_pct >= 75:
    zone = 'Conservative'
elif usage_pct >= 60:
    zone = 'Soft Warning'
else:
    zone = 'Normal'

print(f'ZONE={zone}')
print(f'USAGE_PCT={usage_pct:.1f}')
print(f'EFFECTIVE_LIMIT={effective_limit}')
print(f'HAS_TIKTOKEN={HAS_TIKTOKEN}')
" "$MODEL" "$CURRENT_TOKENS"
```

**Token Zone Behaviors:**

| Zone | Usage % | Behavior |
|------|---------|----------|
| Normal | 0-60% | Full context with all packages |
| Soft Warning | 60-75% | Prefer summaries over full content |
| Conservative | 75-85% | Minimal context, critical packages only |
| Wrap-up | 85-95% | Essential info only, no new packages |
| Emergency | 95%+ | Return immediately, suggest checkpoint |

**Token Budget Allocation by Agent Type:**

| Agent | Task | Specialization | Context Pkgs | Errors |
|-------|------|----------------|--------------|--------|
| developer | 50% | 20% | 20% | 10% |
| senior_software_engineer | 40% | 20% | 25% | 15% |
| qa_expert | 40% | 15% | 30% | 15% |
| tech_lead | 30% | 15% | 40% | 15% |

**Note:** SSE handles escalations from failed developer attempts, so it needs more context and error budget.

### Step 3: Query Context Packages

**IMPORTANT: Zone-Aware Behavior**

Before querying, check the zone from Step 2c:

- **Emergency zone (95%+)**: Skip directly to Step 5 with emergency output
- **Wrap-up zone (85-95%)**: Skip context packages, return minimal output
- **Conservative zone (75-85%)**: Query only critical priority packages (LIMIT=1)
- **Soft Warning zone (60-75%)**: Normal query, but prefer summaries in output
- **Normal zone (0-60%)**: Full context query

**With group_id:**
```bash
# Use shell variables - do NOT interpolate user input directly into commands
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"
AGENT_TYPE="developer"
LIMIT=3  # Reduce to 1 in Conservative zone

# In Conservative zone, filter for critical packages only
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

**First, fetch raw context packages with consumer data:**

```bash
# Fetch packages with LEFT JOIN to get consumer info for agent_relevance calculation
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"  # or empty string for session-wide
AGENT_TYPE="developer"

# Note: SESSION_ID is system-generated (not user input), but use shell variables for clarity
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet query \
  "SELECT cp.id, cp.file_path, cp.priority, cp.summary, cp.group_id, cp.created_at,
          GROUP_CONCAT(cpc.agent_type) as consumers
   FROM context_packages cp
   LEFT JOIN context_package_consumers cpc ON cp.id = cpc.package_id
   WHERE cp.session_id = '$SESSION_ID'
   GROUP BY cp.id"
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
- agent_relevance = 1 if AGENT_TYPE appears in package.consumers (from JOIN), else 0
- recency_factor = 1 / (days_since_created + 1)
```

Sort packages by score DESC, then by `created_at DESC` (tie-breaker), take top N.
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
- `zone` = current token zone from Step 2c
- `usage_pct` = token usage percentage from Step 2c

**Zone-Specific Output:**

**Emergency Zone (95%+):**
```markdown
## Context for {agent_type}

🚨 **Token budget: Emergency ({usage_pct}%) - Checkpoint recommended**

Context assembly skipped due to token budget constraints.
Suggest: Complete current operation and start new session.
```

**Wrap-up Zone (85-95%):**
```markdown
## Context for {agent_type}

🔶 **Token budget: Wrap-up ({usage_pct}%) - Completing current operation**

### Essential Info Only

Minimal context mode active. Focus on completing current task.
```

**Conservative Zone (75-85%):**
```markdown
## Context for {agent_type}

🔶 **Token budget: Conservative ({usage_pct}%)**

### Critical Packages Only ({count}/{available})

**[CRITICAL]** {file_path}
> {summary}
```

**Soft Warning Zone (60-75%):**
```markdown
## Context for {agent_type}

🔶 **Token budget: Soft Warning ({usage_pct}%) - Using summaries**

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}  ← Summaries only, no full content
```

**Normal Zone (0-60%):**
```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}

**[{PRIORITY}]** {file_path}
> {summary}

### Error Patterns ({pattern_count} matches)

⚠️ **Known Issue**: "{error_signature}"
> **Solution**: {solution}
> **Confidence**: {confidence} (seen {occurrences} times)

📦 +{overflow_count} more packages available (re-invoke with higher limit to expand)
```

**Priority Indicators:**
- `[CRITICAL]` - Priority: critical
- `[HIGH]` - Priority: high
- `[MEDIUM]` - Priority: medium
- `[LOW]` - Priority: low

**Zone Indicators:**
- Normal zone: No indicator (full context)
- Soft Warning/Conservative/Wrap-up: `🔶` (orange diamond)
- Emergency: `🚨` (emergency symbol)

**Only show overflow indicator if overflow_count > 0 AND zone is Normal or Soft Warning.**

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
      "senior_software_engineer": 5,
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
