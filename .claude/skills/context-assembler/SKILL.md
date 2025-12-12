---
name: context-assembler
description: Assembles relevant context for agent spawns with prioritized ranking. Ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.
version: 1.5.3
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
- `agent_type`: Target agent - developer/senior_software_engineer/qa_expert/tech_lead/investigator (REQUIRED)
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
defaults = {'developer': 3, 'senior_software_engineer': 5, 'qa_expert': 5, 'tech_lead': 5, 'investigator': 5}
try:
    c = json.load(sys.stdin).get('context_engineering', {})
    limits = c.get('retrieval_limits', {})
    print(limits.get(agent, defaults.get(agent, 3)))
except:
    print(defaults.get(agent, 3))
" "$AGENT_TYPE" 2>/dev/null || echo 3)
echo "Retrieval limit for $AGENT_TYPE: $LIMIT"
```

Default limits: developer=3, senior_software_engineer=5, qa_expert=5, tech_lead=5, investigator=5

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

# IMPORTANT: Use eval to capture output as shell variables
eval "$(python3 -c "
import sys, json

try:
    import tiktoken
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

# Normalize model name (longest key first to avoid partial matches)
model_key = model.lower()
for key in sorted(MODEL_LIMITS.keys(), key=len, reverse=True):
    if key in model_key:
        model_key = key
        break

limit = MODEL_LIMITS.get(model_key, 200000)
effective_limit = int(limit * (1 - SAFETY_MARGIN))

# Calculate REMAINING budget (not total)
remaining_budget = max(0, effective_limit - current)
usage_pct = (current / effective_limit * 100) if effective_limit > 0 else 0

# Determine zone
if usage_pct >= 95:
    zone = 'Emergency'
elif usage_pct >= 85:
    zone = 'Wrap-up'
elif usage_pct >= 75:
    zone = 'Conservative'
elif usage_pct >= 60:
    zone = 'Soft_Warning'  # Underscore for shell variable safety
else:
    zone = 'Normal'

# IMPORTANT: If current_tokens=0 (unknown), apply conservative context cap
# This prevents runaway context when we don't know actual usage
UNKNOWN_BUDGET_CAP = 2000  # Max tokens for context packages when usage unknown
if current == 0:
    remaining_budget = min(remaining_budget, UNKNOWN_BUDGET_CAP)

# Output as shell variable assignments (will be eval'd)
print(f'ZONE={zone}')
print(f'USAGE_PCT={usage_pct:.1f}')
print(f'EFFECTIVE_LIMIT={effective_limit}')
print(f'REMAINING_BUDGET={remaining_budget}')
print(f'HAS_TIKTOKEN={HAS_TIKTOKEN}')
" "$MODEL" "$CURRENT_TOKENS")"

# Now $ZONE, $USAGE_PCT, $EFFECTIVE_LIMIT, $REMAINING_BUDGET, $HAS_TIKTOKEN are set
echo "Zone: $ZONE, Usage: $USAGE_PCT%, Remaining: $REMAINING_BUDGET tokens"
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
| investigator | 35% | 15% | 35% | 15% |

**Note:** SSE and Investigator handle escalations/complex debugging, so they need more context and error budget.

### Step 3: Query Context Packages (Zone-Conditional)

**CRITICAL: Execute query based on zone from Step 2c**

The query behavior depends entirely on the zone. Use this conditional structure:

```bash
# Zone-conditional query execution
# Variables from previous steps: $ZONE, $SESSION_ID, $GROUP_ID, $AGENT_TYPE, $LIMIT, $REMAINING_BUDGET

# Initialize result variable
QUERY_RESULT=""

if [ "$ZONE" = "Emergency" ]; then
    # Emergency zone: Skip all queries, go directly to Step 5
    echo "ZONE=Emergency: Skipping context query, proceeding to emergency output"
    QUERY_RESULT='{"packages":[],"total_available":0,"zone_skip":true}'

elif [ "$ZONE" = "Wrap-up" ]; then
    # Wrap-up zone: Skip context packages, minimal output only
    echo "ZONE=Wrap-up: Skipping context packages"
    QUERY_RESULT='{"packages":[],"total_available":0,"zone_skip":true}'

elif [ "$ZONE" = "Conservative" ]; then
    # Conservative zone: Priority fallback with LIMIT items across buckets
    echo "ZONE=Conservative: Using priority fallback ladder"
    QUERY_RESULT=$(python3 -c "
import sqlite3
import json
import sys
import time

session_id = sys.argv[1]
group_id = sys.argv[2]
limit = int(sys.argv[3])

def db_query_with_retry(db_path, sql, params, max_retries=3, backoff_ms=[100, 250, 500]):
    '''Execute parameterized query with retry on SQLITE_BUSY.'''
    for attempt in range(max_retries + 1):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries:
                time.sleep(backoff_ms[attempt] / 1000.0)
                continue
            return []
    return []

db_path = 'bazinga/bazinga.db'

# Priority fallback: fill up to LIMIT across critical → high → medium
priorities = ['critical', 'high', 'medium']
collected = []
total_available = 0

for priority in priorities:
    if len(collected) >= limit:
        break
    remaining = limit - len(collected)

    # Count total available at this priority (parameterized - NO SQL injection)
    count_sql = '''SELECT COUNT(*) as cnt FROM context_packages
                   WHERE session_id = ?
                   AND (group_id = ? OR group_id IS NULL OR ? = '')
                   AND priority = ?'''
    count_result = db_query_with_retry(db_path, count_sql, (session_id, group_id, group_id, priority))
    if count_result:
        total_available += count_result[0].get('cnt', 0)

    # Fetch packages at this priority (parameterized - NO SQL injection)
    fetch_sql = '''SELECT id, file_path, priority, summary FROM context_packages
                   WHERE session_id = ?
                   AND (group_id = ? OR group_id IS NULL OR ? = '')
                   AND priority = ?
                   ORDER BY created_at DESC LIMIT ?'''
    packages = db_query_with_retry(db_path, fetch_sql, (session_id, group_id, group_id, priority, remaining))
    collected.extend(packages)

print(json.dumps({'packages': collected, 'total_available': total_available}))
" "$SESSION_ID" "$GROUP_ID" "$LIMIT")

else
    # Normal or Soft_Warning zone: Standard query
    echo "ZONE=$ZONE: Standard query with LIMIT=$LIMIT"
    QUERY_RESULT=$(python3 -c "
import subprocess
import json
import sys
import time

session_id = sys.argv[1]
group_id = sys.argv[2]
agent_type = sys.argv[3]
limit = int(sys.argv[4])

def db_query_with_retry(cmd_args, max_retries=3, backoff_ms=[100, 250, 500]):
    for attempt in range(max_retries + 1):
        result = subprocess.run(cmd_args, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout) if result.stdout.strip() else []
            except json.JSONDecodeError:
                return []
        if 'SQLITE_BUSY' in result.stderr or 'database is locked' in result.stderr:
            if attempt < max_retries:
                time.sleep(backoff_ms[attempt] / 1000.0)
                continue
        return []
    return []

# Use bazinga-db get-context-packages (parameterized, safe)
result = db_query_with_retry([
    'python3', '.claude/skills/bazinga-db/scripts/bazinga_db.py', '--quiet',
    'get-context-packages', session_id, group_id, agent_type, str(limit)
])

# If result is dict with 'packages' key, use it; otherwise wrap
if isinstance(result, dict):
    print(json.dumps(result))
elif isinstance(result, list):
    print(json.dumps({'packages': result, 'total_available': len(result)}))
else:
    print(json.dumps({'packages': [], 'total_available': 0}))
" "$SESSION_ID" "$GROUP_ID" "$AGENT_TYPE" "$LIMIT")
fi

# Parse result for next steps (log count only - summaries may contain secrets before redaction)
echo "Query returned: $(echo "$QUERY_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"packages\",[]))} packages, total_available={d.get(\"total_available\",0)}')" 2>/dev/null || echo 'parse error')"
```

**If query fails or returns empty, proceed to Step 3b (Heuristic Fallback).**

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

### Step 3c: Token Packing with Redaction

After Step 3 or 3b retrieves packages, apply redaction, truncation, and token packing in the correct order:

```bash
# Token packing with proper order: redact → truncate → estimate → pack
# Input: $QUERY_RESULT (JSON from Step 3), $ZONE, $AGENT_TYPE, $REMAINING_BUDGET

PACKED_RESULT=$(python3 -c "
import json
import sys
import re

# Inputs from command line
query_result = json.loads(sys.argv[1])
zone = sys.argv[2]
agent_type = sys.argv[3]
remaining_budget = int(sys.argv[4])

packages = query_result.get('packages', [])
total_available = query_result.get('total_available', len(packages))

# --- Redaction Patterns (apply FIRST) ---
REDACTION_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|access[_-]?token|auth[_-]?token|bearer)[\"\\s:=]+[\"\\']?([a-zA-Z0-9_\\-]{20,})[\"\\']?', r'\\1=[REDACTED]'),
    (r'(?i)(aws[_-]?(access|secret)[_-]?key[_-]?id?)[\"\\s:=]+[\"\\']?([A-Z0-9]{16,})[\"\\']?', r'\\1=[REDACTED]'),
    (r'(?i)(password|passwd|secret|private[_-]?key)[\"\\s:=]+[\"\\']?([^\\s\"\\'\n]{8,})[\"\\']?', r'\\1=[REDACTED]'),
    (r'(?i)(mongodb|postgres|mysql|redis|amqp)://[^\\s]+@', r'\\1://[REDACTED]@'),
    (r'eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*', '[JWT_REDACTED]'),
]

def redact_text(text):
    for pattern, replacement in REDACTION_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

# --- Truncation limits per zone ---
SUMMARY_LIMITS = {
    'Normal': 400,
    'Soft_Warning': 200,
    'Conservative': 100,
    'Wrap-up': 60,
    'Emergency': 0
}

def truncate_summary(summary, zone):
    max_len = SUMMARY_LIMITS.get(zone, 400)
    if len(summary) <= max_len:
        return summary
    truncated = summary[:max_len].rsplit(' ', 1)[0]
    return truncated + '...'

# --- Token estimation ---
def estimate_tokens(text):
    # ~4 chars per token (conservative fallback)
    return len(text) // 4 + 1

# --- Budget allocation ---
CONTEXT_PCT = {
    'developer': 0.20,
    'senior_software_engineer': 0.25,
    'qa_expert': 0.30,
    'tech_lead': 0.40,
    'investigator': 0.35
}

pct = CONTEXT_PCT.get(agent_type, 0.20)
context_budget = int(remaining_budget * pct)  # Use REMAINING, not total

# --- Process packages: redact → truncate → estimate → pack ---
packed = []
used_tokens = 0
package_ids = []

for pkg in packages:
    raw_summary = pkg.get('summary', '')

    # 1. REDACT first
    redacted_summary = redact_text(raw_summary)

    # 2. TRUNCATE second
    truncated_summary = truncate_summary(redacted_summary, zone)

    # 3. ESTIMATE tokens
    pkg_text = f\"**[{pkg.get('priority', 'medium').upper()}]** {pkg.get('file_path', '')}\\n> {truncated_summary}\"
    pkg_tokens = estimate_tokens(pkg_text)

    # 4. PACK if within budget
    if used_tokens + pkg_tokens > context_budget:
        break

    packed.append({
        'id': pkg.get('id'),
        'file_path': pkg.get('file_path'),
        'priority': pkg.get('priority'),
        'summary': truncated_summary,
        'est_tokens': pkg_tokens
    })
    package_ids.append(pkg.get('id'))
    used_tokens += pkg_tokens

print(json.dumps({
    'packages': packed,
    'total_available': total_available,
    'used_tokens': used_tokens,
    'budget': context_budget,
    'package_ids': package_ids
}))
" "$QUERY_RESULT" "$ZONE" "$AGENT_TYPE" "$REMAINING_BUDGET")

# Extract package IDs for Step 5b consumption tracking (cast to strings to avoid TypeError)
PACKAGE_IDS=($(echo "$PACKED_RESULT" | python3 -c "import sys,json; ids=json.load(sys.stdin).get('package_ids',[]); print(' '.join(str(x) for x in ids))"))

echo "Packed: $(echo "$PACKED_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"packages\",[]))} pkgs, {d.get(\"used_tokens\",0)}/{d.get(\"budget\",0)} tokens')")"
echo "Package IDs to mark consumed: ${PACKAGE_IDS[*]}"
```

**Key improvements:**
- Uses `REMAINING_BUDGET` (not total limit)
- Applies redaction BEFORE truncation
- Populates `PACKAGE_IDS` array for Step 5b
- Includes `investigator` in budget allocation

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
        'Soft_Warning': 200,  # Underscore to match $ZONE variable
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

**IMPORTANT: Only run if zone is Normal or Soft_Warning (skip for Wrap-up/Emergency)**

After formatting output, mark delivered packages as consumed to prevent repeated delivery:

```bash
# Only mark consumption if packages were actually delivered
if { [ "$ZONE" = "Normal" ] || [ "$ZONE" = "Soft_Warning" ]; } && [ ${#PACKAGE_IDS[@]} -gt 0 ]; then
    # Mark consumed packages using bazinga-db with retry
    # Note: Uses context_package_consumers table (unified table)
    python3 -c "
import subprocess
import sys
import time
import sqlite3

session_id = sys.argv[1]
agent_type = sys.argv[2]
iteration = int(sys.argv[3])
package_ids = sys.argv[4:]  # Remaining args are package IDs

def db_execute_with_retry(db_path, sql, params, max_retries=3, backoff_ms=[100, 250, 500]):
    '''Execute SQL with retry on SQLITE_BUSY.'''
    for attempt in range(max_retries + 1):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries:
                time.sleep(backoff_ms[attempt] / 1000.0)
                continue
            return False
    return False

# Insert consumption records using parameterized queries (no SQL injection)
db_path = 'bazinga/bazinga.db'
sql = '''INSERT OR IGNORE INTO context_package_consumers
         (package_id, agent_type, session_id, iteration, consumed_at)
         VALUES (?, ?, ?, ?, datetime('now'))'''

marked = 0
for pkg_id in package_ids:
    if db_execute_with_retry(db_path, sql, (pkg_id, agent_type, session_id, iteration)):
        marked += 1

print(f'Marked {marked}/{len(package_ids)} packages as consumed')
" "$SESSION_ID" "$AGENT_TYPE" "$ITERATION" "${PACKAGE_IDS[@]}"
else
    echo "Skipping consumption tracking (zone=$ZONE or no packages)"
fi
```

**Key improvements:**
- Uses **parameterized queries** (no SQL injection via f-strings)
- Uses **context_package_consumers** table (unified, not consumption_scope)
- Includes **retry logic** for SQLITE_BUSY
- **Skips** in Wrap-up/Emergency zones (nothing delivered)
- Uses **sqlite3 directly** for parameterized safety

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
      "tech_lead": 5,
      "investigator": 5
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
| `context_package_consumers` | Per-agent consumption tracking (unified table with session_id, iteration) |
| `error_patterns` | Captured error signatures with solutions |
| `sessions` | Session metadata including project_id |

**Note:** The `context_package_consumers` table has columns: `package_id`, `agent_type`, `session_id`, `iteration`, `consumed_at`. Step 5b uses this for tracking delivery and preventing duplicate context.

---

## References

See `references/usage.md` for detailed usage documentation and integration examples.
