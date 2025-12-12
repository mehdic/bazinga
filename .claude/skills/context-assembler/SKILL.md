---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 1.4.0
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
- `agent_type`: Target agent - developer/senior_software_engineer/qa_expert/tech_lead (REQUIRED)
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
import sys, json

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

# Read safety margin from config (default 15%)
try:
    with open('bazinga/skills_config.json') as f:
        cfg = json.load(f).get('context_engineering', {})
        SAFETY_MARGIN = cfg.get('token_safety_margin', 0.15)
except:
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

**Database Retry Logic:**

All database queries should use exponential backoff to handle SQLITE_BUSY and locked errors:

```python
# Retry wrapper for database operations (use in any DB query)
import time
import subprocess
import json

def db_query_with_retry(cmd_args, max_retries=3, backoff_ms=[100, 250, 500]):
    """Execute bazinga-db query with exponential backoff on failures."""
    for attempt in range(max_retries + 1):
        result = subprocess.run(cmd_args, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout) if result.stdout.strip() else []
            except json.JSONDecodeError:
                return result.stdout

        # Check for retryable errors
        if 'SQLITE_BUSY' in result.stderr or 'database is locked' in result.stderr:
            if attempt < max_retries:
                time.sleep(backoff_ms[attempt] / 1000.0)
                continue

        # Non-retryable error or max retries exceeded
        return None
    return None
```

**IMPORTANT: Zone-Aware Behavior**

Before querying, check the zone from Step 2c:

- **Emergency zone (95%+)**: Skip directly to Step 5 with emergency output
- **Wrap-up zone (85-95%)**: Skip context packages, return minimal output
- **Conservative zone (75-85%)**: Query with priority fallback ladder (LIMIT=1)
- **Soft Warning zone (60-75%)**: Normal query, but prefer summaries in output
- **Normal zone (0-60%)**: Full context query

**Standard Query (Normal/Soft Warning zones):**
```bash
# Use shell variables - do NOT interpolate user input directly into commands
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"
AGENT_TYPE="developer"
LIMIT=3  # From Step 2a

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-context-packages \
  "$SESSION_ID" "$GROUP_ID" "$AGENT_TYPE" "$LIMIT"
```

**Conservative Zone Query (Priority Fallback Ladder):**

In Conservative zone, try priorities in order: critical → high → medium until at least one package found:

```bash
# Conservative zone: Priority fallback ladder to prevent starvation
SESSION_ID="bazinga_20250212_143530"
GROUP_ID="group_a"
AGENT_TYPE="developer"

python3 -c "
import subprocess
import json
import sys

session_id = sys.argv[1]
group_id = sys.argv[2]
agent_type = sys.argv[3]

# Priority fallback ladder: critical → high → medium
priorities = ['critical', 'high', 'medium']

for priority in priorities:
    result = subprocess.run([
        'python3', '.claude/skills/bazinga-db/scripts/bazinga_db.py', '--quiet', 'query',
        f\"\"\"SELECT id, file_path, priority, summary FROM context_packages
           WHERE session_id = '{session_id}'
           AND (group_id = '{group_id}' OR group_id IS NULL OR '{group_id}' = '')
           AND priority = '{priority}'
           ORDER BY created_at DESC LIMIT 1\"\"\"
    ], capture_output=True, text=True)

    try:
        packages = json.loads(result.stdout)
        if packages and len(packages) > 0:
            # Found a package at this priority level
            print(json.dumps({'packages': packages, 'total_available': len(packages), 'priority_used': priority}))
            sys.exit(0)
    except:
        continue

# No packages found at any priority - return empty
print(json.dumps({'packages': [], 'total_available': 0, 'priority_used': None}))
" "$SESSION_ID" "$GROUP_ID" "$AGENT_TYPE"
```

This prevents Conservative zone from returning empty when no critical packages exist.

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

### Step 3c: Bottom-Up Token Packing (Budget Enforcement)

After retrieving packages, apply token budget enforcement by packing summaries until budget is met:

```python
# Bottom-up token packing for real budget enforcement
import json

def estimate_tokens(text: str, has_tiktoken: bool = False) -> int:
    """Estimate token count for text."""
    if has_tiktoken:
        try:
            import tiktoken
            enc = tiktoken.get_encoding('cl100k_base')
            return len(enc.encode(text))
        except:
            pass
    # Fallback: ~4 chars per token (conservative)
    return len(text) // 4 + 1

def pack_packages_to_budget(packages: list, zone: str, agent_type: str, effective_limit: int) -> list:
    """Pack packages until context budget is met."""

    # Budget allocation for context packages (from plan.md)
    context_pct = {
        'developer': 0.20,
        'senior_software_engineer': 0.25,
        'qa_expert': 0.30,
        'tech_lead': 0.40
    }

    # Summary truncation limits per zone
    summary_limits = {
        'Normal': 400,
        'Soft Warning': 200,
        'Conservative': 100,
        'Wrap-up': 60,
        'Emergency': 0
    }

    # Calculate context budget in tokens
    pct = context_pct.get(agent_type, 0.20)
    context_budget = int(effective_limit * pct)
    summary_limit = summary_limits.get(zone, 400)

    packed = []
    used_tokens = 0

    for pkg in packages:
        # Truncate summary for this zone
        summary = pkg.get('summary', '')[:summary_limit]
        if len(pkg.get('summary', '')) > summary_limit:
            summary = summary.rsplit(' ', 1)[0] + '...'

        # Estimate tokens for this package (path + priority + summary + formatting)
        pkg_text = f"**[{pkg.get('priority', 'medium').upper()}]** {pkg.get('file_path', '')}\n> {summary}"
        pkg_tokens = estimate_tokens(pkg_text)

        # Check if adding this would exceed budget
        if used_tokens + pkg_tokens > context_budget:
            break  # Stop packing

        # Add package with truncated summary
        packed.append({**pkg, 'summary': summary, 'est_tokens': pkg_tokens})
        used_tokens += pkg_tokens

    return packed
```

**Usage:**
```python
# After Step 3 query
packages = query_result.get('packages', [])
effective_limit = EFFECTIVE_LIMIT  # From Step 2c

# Apply token packing
packed_packages = pack_packages_to_budget(packages, zone, agent_type, effective_limit)
```

This ensures context stays within the allocated budget percentage for each agent type.

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

**Micro-Summary Truncation:**

Apply zone-specific summary length limits for actual degradation:

| Zone | Max Summary Chars | Rationale |
|------|-------------------|-----------|
| Normal | 400 | Full detail |
| Soft Warning | 200 | Reduced detail |
| Conservative | 100 | Key points only |
| Wrap-up | 60 | Minimal hints |

```python
def truncate_summary(summary: str, zone: str) -> str:
    """Truncate summary based on zone-specific limits."""
    limits = {
        'Normal': 400,
        'Soft Warning': 200,
        'Conservative': 100,
        'Wrap-up': 60,
        'Emergency': 0  # No summaries in emergency
    }
    max_len = limits.get(zone, 400)
    if len(summary) <= max_len:
        return summary
    # Truncate at word boundary with ellipsis
    truncated = summary[:max_len].rsplit(' ', 1)[0]
    return truncated + '...'
```

Apply `truncate_summary()` to each package summary before rendering output.

**Summary Redaction (Security):**

Apply the same redaction patterns used for error_patterns to summaries before output:

```python
import re

# Redaction patterns for secrets (same as error_patterns redaction)
REDACTION_PATTERNS = [
    # API keys and tokens
    (r'(?i)(api[_-]?key|apikey|access[_-]?token|auth[_-]?token|bearer)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', r'\1=[REDACTED]'),
    # AWS credentials
    (r'(?i)(aws[_-]?(access|secret)[_-]?key[_-]?id?)["\s:=]+["\']?([A-Z0-9]{16,})["\']?', r'\1=[REDACTED]'),
    # Passwords and secrets
    (r'(?i)(password|passwd|secret|private[_-]?key)["\s:=]+["\']?([^\s"\']{8,})["\']?', r'\1=[REDACTED]'),
    # Connection strings
    (r'(?i)(mongodb|postgres|mysql|redis|amqp)://[^\s]+@', r'\1://[REDACTED]@'),
    # JWT tokens
    (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', '[JWT_REDACTED]'),
]

def redact_summary(summary: str) -> str:
    """Redact potential secrets from summary."""
    redacted = summary
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)

    # Entropy-based detection for high-entropy strings (potential secrets)
    def has_high_entropy(s):
        if len(s) < 20:
            return False
        char_set = set(s)
        # High entropy = many unique chars relative to length
        return len(char_set) / len(s) > 0.6 and any(c.isdigit() for c in s) and any(c.isupper() for c in s)

    # Find and redact high-entropy strings
    words = redacted.split()
    for i, word in enumerate(words):
        if has_high_entropy(word):
            words[i] = '[REDACTED]'
    return ' '.join(words)
```

Apply `redact_summary()` before `truncate_summary()` in the processing pipeline.

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

### Priority Packages ({count}/{available}) - {priority_used} level

**[{PRIORITY}]** {file_path}
> {summary}
```

Note: `priority_used` comes from the fallback ladder response (critical/high/medium).

**Soft Warning Zone (60-75%):**
```markdown
## Context for {agent_type}

🔶 **Token budget: Soft Warning ({usage_pct}%) - Reduced summaries (200 char)**

### Relevant Packages ({count}/{available})

**[{PRIORITY}]** {file_path}
> {summary}  ← Truncated to 200 chars
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

### Step 5b: Mark Packages as Consumed

After formatting output, mark delivered packages as consumed to prevent repeated delivery:

```bash
# Mark consumed packages via bazinga-db
# Call this for each package that was included in the output
SESSION_ID="bazinga_20250212_143530"
AGENT_TYPE="developer"
ITERATION=0  # Current iteration number

# For each package_id in packed_packages:
python3 -c "
import subprocess
import json
import sys

session_id = sys.argv[1]
agent_type = sys.argv[2]
iteration = int(sys.argv[3])
package_ids = sys.argv[4:]  # Remaining args are package IDs

for pkg_id in package_ids:
    # Insert consumption record (use db_query_with_retry if available)
    subprocess.run([
        'python3', '.claude/skills/bazinga-db/scripts/bazinga_db.py', '--quiet', 'execute',
        f\"\"\"INSERT OR IGNORE INTO consumption_scope (package_id, session_id, agent_type, iteration, consumed_at)
           VALUES ('{pkg_id}', '{session_id}', '{agent_type}', {iteration}, datetime('now'))\"\"\"
    ], capture_output=True)

print(f'Marked {len(package_ids)} packages as consumed')
" "$SESSION_ID" "$AGENT_TYPE" "$ITERATION" "${PACKAGE_IDS[@]}"
```

**Why mark consumption?**
- Prevents repeated delivery of same packages across iterations
- Enables iteration-aware freshness scoring
- Reduces token waste from redundant context

**Note:** Use `INSERT OR IGNORE` to handle duplicate consumption (same package, same agent, same iteration).

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
