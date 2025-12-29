# Skills Configuration Implementation: Ultrathink Analysis

**Date:** 2025-12-28
**Context:** Implementing skills configuration enforcement from approved plan
**Status:** Pre-implementation review
**Purpose:** Ensure correct integration with existing code patterns

---

## Code Pattern Analysis

### 1. Config Seeder Pattern (seed_configs.py)

**Key observations:**
- Uses `BEGIN IMMEDIATE` transaction wrapper in `main()`
- Individual seed functions do NOT call `conn.commit()` - caller handles it
- Returns `True/False` for success tracking
- Uses `DELETE FROM table` before inserting (idempotent)
- Error handling: returns False, doesn't raise

**Pattern to follow:**
```python
def seed_skills_config(conn):
    """Seed skills configuration from JSON."""
    config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
    if not config_path.exists():
        print(f"WARNING: {config_path} not found", file=sys.stderr)
        return True  # Non-fatal - skills config is optional

    # ... read and insert ...
    # Note: commit handled by caller in transaction wrapper
    print(f"Seeded skills configuration")
    return True
```

**Integration point:**
```python
# In main(), after line 268:
if args.all or args.rules:
    success = seed_special_rules(conn) and success
# ADD:
if args.all:
    success = seed_skills_config(conn) and success  # Always seed with --all
```

**No new CLI flag needed** - skills config is seeded as part of `--all`

---

### 2. Prompt Builder Pattern (prompt_builder.py)

**Key observations:**
- Components built in order: context → specialization → agent → task → pm → feedback → handoff
- Uses `conn` from `sqlite3.connect(args.db)` - need to close in finally
- Model comes from `args.model or "sonnet"`
- Testing mode comes from `args.testing_mode`
- Components list - each component is a string or empty string
- Empty strings are filtered out in final join

**Block building pattern:**
```python
def build_skills_block(conn, agent_type, testing_mode="full"):
    """Build compact skills checklist for prompt injection."""
    # 1. Query configuration table for skills_config
    # 2. Apply agent key aliasing (project_manager → pm)
    # 3. Apply testing_mode filtering
    # 4. Return formatted checklist string or ""
```

**Integration point (build_prompt function, after line 1740):**
```python
# 2. Build SPECIALIZATION block (from DB task_groups + template files)
if conn and args.group_id and args.agent_type not in ["project_manager"]:
    spec_block = build_specialization_block(...)
    if spec_block:
        components.append(spec_block)

# ADD: 2.5 Build SKILLS CHECKLIST block (compact, after specialization)
if conn and args.agent_type not in ["project_manager", "orchestrator"]:
    skills_block = build_skills_block(conn, args.agent_type, args.testing_mode)
    if skills_block:
        components.append(skills_block)

# 3. Read AGENT DEFINITION (MANDATORY - this is the core)
```

**Key consideration:** Block inserted AFTER specialization, BEFORE agent definition
- Ensures skills checklist is in context when agent reads its definition
- Compact format (≤10 lines) minimizes token impact

---

### 3. Bazinga DB Pattern (bazinga_db.py)

**Key observations:**
- Methods use `conn = self._get_connection()` and must call `conn.close()`
- Command handlers in `main()` parse flags using while loop pattern
- JSON output via `print(json.dumps(result, indent=2))`
- Error messages via `print(..., file=sys.stderr)` then `sys.exit(1)`

**Method pattern:**
```python
def check_skill_evidence(self, session_id: str, agent_type: str,
                        since_minutes: int = 30, testing_mode: str = "full") -> Dict:
    """Check if mandatory skills have recent evidence in skill_outputs."""
    conn = self._get_connection()

    try:
        # 1. Get skills_config from configuration table
        # 2. Apply agent key aliasing
        # 3. Get mandatory skills (filtered by testing_mode)
        # 4. Query skill_outputs for recent evidence
        # 5. Return {complete, missing, found, recency_window_minutes}
    finally:
        conn.close()
```

**Command handler pattern:**
```python
elif cmd == 'check-skill-evidence':
    # Parse flags: --since, --testing-mode
    since_minutes = 30
    testing_mode = "full"
    positional_args = []
    i = 0
    while i < len(cmd_args):
        if cmd_args[i] == '--since' and i + 1 < len(cmd_args):
            since_minutes = int(cmd_args[i + 1])
            i += 2
        elif cmd_args[i] == '--testing-mode' and i + 1 < len(cmd_args):
            testing_mode = cmd_args[i + 1]
            i += 2
        else:
            positional_args.append(cmd_args[i])
            i += 1

    if len(positional_args) < 2:
        print(json.dumps({...error...}), file=sys.stderr)
        sys.exit(1)

    session_id = positional_args[0]
    agent_type = positional_args[1]
    result = db.check_skill_evidence(session_id, agent_type, since_minutes, testing_mode)
    print(json.dumps(result, indent=2))
```

---

## Implementation Details

### File 1: seed_configs.py

**Location:** `.claude/skills/config-seeder/scripts/seed_configs.py`

**Changes:**

1. Add `seed_skills_config()` function (after line 187):

```python
def seed_skills_config(conn):
    """Seed skills configuration from JSON to configuration table.

    Note: This uses the configuration table which stores key-value pairs.
    The skills_config key stores the entire JSON as a string value.

    Unlike transitions/markers which have dedicated tables, skills_config
    uses the generic configuration table for flexibility.
    """
    # Skills config is in bazinga/ not bazinga/config/
    config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
    if not config_path.exists():
        print(f"WARNING: {config_path} not found, skipping skills config", file=sys.stderr)
        return True  # Non-fatal - system works without it

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()

    # Use INSERT OR REPLACE for idempotency
    cursor.execute("""
        INSERT OR REPLACE INTO configuration (key, value, updated_at)
        VALUES ('skills_config', ?, CURRENT_TIMESTAMP)
    """, (json.dumps(data),))

    # Note: commit handled by caller in transaction wrapper
    print("Seeded skills configuration")
    return True
```

2. Modify main() to call it (after line 268, inside transaction):

```python
        if args.all or args.rules:
            success = seed_special_rules(conn) and success
        # ADD THIS:
        if args.all:
            success = seed_skills_config(conn) and success
```

---

### File 2: prompt_builder.py

**Location:** `.claude/skills/prompt-builder/scripts/prompt_builder.py`

**Changes:**

1. Add constants (after line 134, after MIN_AGENT_LINES):

```python
# Agent type to skills config key mapping
# Skills config uses short keys (pm) but agent_type uses full names (project_manager)
AGENT_KEY_ALIASES = {
    "project_manager": "pm",
}

# Test-related skills to filter when testing is disabled/minimal
TEST_RELATED_SKILLS = {"test-coverage", "test-pattern-analysis"}
```

2. Add `get_skills_config()` function (after build_context_block, around line 1390):

```python
def get_skills_config(conn, agent_type, testing_mode="full"):
    """Get skills configuration for an agent from database.

    Args:
        conn: SQLite connection
        agent_type: Agent type (e.g., "developer", "project_manager")
        testing_mode: Testing mode ("full", "minimal", "disabled")

    Returns:
        Dict with keys: mandatory (list), optional (list), disabled (list)
    """
    empty_result = {"mandatory": [], "optional": [], "disabled": []}

    if not conn:
        return empty_result

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configuration WHERE key = 'skills_config'")
        row = cursor.fetchone()
        if not row:
            return empty_result

        config = json.loads(row[0])

        # Apply key aliasing (project_manager -> pm)
        agent_key = AGENT_KEY_ALIASES.get(agent_type, agent_type)
        agent_config = config.get(agent_key, {})

        # Categorize skills by level
        result = {"mandatory": [], "optional": [], "disabled": []}
        for skill, level in agent_config.items():
            if level in result:
                result[level].append(skill)

        # Filter test-related skills when testing is disabled/minimal
        if testing_mode in ("disabled", "minimal"):
            result["mandatory"] = [s for s in result["mandatory"]
                                   if s not in TEST_RELATED_SKILLS]

        return result

    except (sqlite3.OperationalError, json.JSONDecodeError) as e:
        print(f"WARNING: Failed to get skills config: {e}", file=sys.stderr)
        return empty_result
```

3. Add `build_skills_block()` function (after get_skills_config):

```python
def build_skills_block(conn, agent_type, testing_mode="full"):
    """Build compact skills checklist for prompt injection.

    Returns a compact checklist (≤10 lines) to minimize token impact.
    Inserted after specialization block, before agent definition.
    """
    skills = get_skills_config(conn, agent_type, testing_mode)

    # Skip if no skills configured for this agent
    if not skills["mandatory"] and not skills["optional"]:
        return ""

    # Compact checklist format
    lines = ["## Skills Checklist", ""]

    if skills["mandatory"]:
        lines.append("**MUST invoke before completion:**")
        for skill in skills["mandatory"]:
            lines.append(f'- [ ] `Skill(command: "{skill}")`')
        lines.append("")

    if skills["optional"]:
        lines.append("**Consider if relevant:** " + ", ".join(
            f'`{s}`' for s in skills["optional"]
        ))

    return "\n".join(lines)
```

4. Integrate into `build_prompt()` (after line 1740, after specialization block):

```python
        # 2. Build SPECIALIZATION block (from DB task_groups + template files)
        if conn and args.group_id and args.agent_type not in ["project_manager"]:
            spec_block = build_specialization_block(
                conn, args.session_id, args.group_id, args.agent_type, model
            )
            if spec_block:
                components.append(spec_block)

        # 2.5 Build SKILLS CHECKLIST block (compact, minimizes token impact)
        if conn and args.agent_type not in ["project_manager", "orchestrator"]:
            skills_block = build_skills_block(conn, args.agent_type, args.testing_mode)
            if skills_block:
                components.append(skills_block)

        # 3. Read AGENT DEFINITION (MANDATORY - this is the core)
```

---

### File 3: bazinga_db.py

**Location:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Changes:**

1. Add `check_skill_evidence()` method (after `get_skill_output_all`, around line 1660):

```python
    def check_skill_evidence(self, session_id: str, agent_type: str,
                            since_minutes: int = 30, testing_mode: str = "full") -> Dict:
        """Check if mandatory skills have recent evidence in skill_outputs.

        Uses the existing skill_outputs table as evidence of skill invocation.
        This avoids needing a new table or modifying individual skills.

        Args:
            session_id: Session to check
            agent_type: Agent type (e.g., "developer")
            since_minutes: Look for evidence within this time window
            testing_mode: Testing mode for filtering test-related skills

        Returns:
            Dict with: complete (bool), missing (list), found (list),
                      mandatory (list), recency_window_minutes (int)
        """
        conn = self._get_connection()

        try:
            # 1. Get skills_config from configuration table
            row = conn.execute(
                "SELECT value FROM configuration WHERE key = 'skills_config'"
            ).fetchone()

            if not row:
                return {
                    "complete": True,
                    "missing": [],
                    "found": [],
                    "mandatory": [],
                    "note": "No skills config found in database",
                    "recency_window_minutes": since_minutes
                }

            config = json.loads(row['value'])

            # 2. Apply agent key aliasing
            agent_key_aliases = {"project_manager": "pm"}
            agent_key = agent_key_aliases.get(agent_type, agent_type)
            agent_config = config.get(agent_key, {})

            # 3. Get mandatory skills (filtered by testing_mode)
            test_skills = {"test-coverage", "test-pattern-analysis"}
            mandatory = []
            for skill, level in agent_config.items():
                if level == "mandatory":
                    # Skip test skills if testing disabled/minimal
                    if testing_mode in ("disabled", "minimal") and skill in test_skills:
                        continue
                    mandatory.append(skill)

            if not mandatory:
                return {
                    "complete": True,
                    "missing": [],
                    "found": [],
                    "mandatory": [],
                    "recency_window_minutes": since_minutes
                }

            # 4. Query skill_outputs for recent evidence
            from datetime import datetime, timedelta
            since_time = datetime.now() - timedelta(minutes=since_minutes)

            rows = conn.execute("""
                SELECT DISTINCT skill_name FROM skill_outputs
                WHERE session_id = ?
                AND timestamp >= ?
            """, (session_id, since_time.isoformat())).fetchall()

            recent_outputs = {row['skill_name'] for row in rows}

            # 5. Calculate missing
            found = [s for s in mandatory if s in recent_outputs]
            missing = [s for s in mandatory if s not in recent_outputs]

            return {
                "complete": len(missing) == 0,
                "missing": missing,
                "found": found,
                "mandatory": mandatory,
                "recency_window_minutes": since_minutes
            }

        finally:
            conn.close()
```

2. Add command handler in `main()` (after `get-skill-output-all` handler, around line 3434):

```python
        elif cmd == 'check-skill-evidence':
            # Parse flags: --since, --testing-mode
            since_minutes = 30
            testing_mode = "full"
            positional_args = []
            i = 0
            while i < len(cmd_args):
                if cmd_args[i] == '--since' and i + 1 < len(cmd_args):
                    since_minutes = int(cmd_args[i + 1])
                    i += 2
                elif cmd_args[i] == '--testing-mode' and i + 1 < len(cmd_args):
                    testing_mode = cmd_args[i + 1]
                    i += 2
                else:
                    positional_args.append(cmd_args[i])
                    i += 1

            if len(positional_args) < 2:
                print(json.dumps({
                    "success": False,
                    "error": "check-skill-evidence requires <session_id> <agent_type> [--since N] [--testing-mode MODE]"
                }, indent=2), file=sys.stderr)
                sys.exit(1)

            session_id = positional_args[0]
            agent_type = positional_args[1]
            result = db.check_skill_evidence(session_id, agent_type, since_minutes, testing_mode)
            print(json.dumps(result, indent=2))
```

3. Add help text (in `print_help()` function):

```
check-skill-evidence <session_id> <agent_type> [--since N] [--testing-mode MODE]
    Check if mandatory skills have recent evidence in skill_outputs
    --since: Minutes to look back (default: 30)
    --testing-mode: full/minimal/disabled (default: full)
```

---

## Edge Cases & Error Handling

### Edge Case 1: skills_config.json doesn't exist
- **seed_skills_config:** Returns True (non-fatal), prints warning
- **get_skills_config:** Returns empty dict
- **check_skill_evidence:** Returns complete=True with note

### Edge Case 2: configuration table doesn't have skills_config key
- **get_skills_config:** Returns empty dict, no error
- **check_skill_evidence:** Returns complete=True with note

### Edge Case 3: Agent type not in skills_config (e.g., "orchestrator")
- **get_skills_config:** Returns empty dict for that agent
- **build_skills_block:** Returns empty string (no block added)
- **check_skill_evidence:** Returns complete=True (no mandatory skills)

### Edge Case 4: Database locked (concurrent access)
- All functions use existing connection patterns with timeout
- seed_configs.py already uses `timeout=5.0` and `BEGIN IMMEDIATE`

### Edge Case 5: Invalid JSON in configuration table
- **get_skills_config:** Catches JSONDecodeError, returns empty dict
- **check_skill_evidence:** Same handling

### Edge Case 6: Empty mandatory list after filtering
- Returns complete=True (nothing to check)

---

## Testing Plan

### Unit Tests

```python
# test_skills_config.py

def test_seed_skills_config_success():
    """Verify skills config seeds to configuration table."""
    # Create test DB with configuration table
    # Call seed_skills_config
    # Verify key exists with correct JSON

def test_seed_skills_config_missing_file():
    """Verify graceful handling when file missing."""
    # Point to non-existent file
    # Should return True (non-fatal)

def test_get_skills_config_agent_aliasing():
    """Verify project_manager maps to pm key."""
    # Seed config with pm key
    # Query with project_manager agent_type
    # Should return pm's config

def test_get_skills_config_testing_mode_filter():
    """Verify test skills filtered when testing disabled."""
    # Seed config with test-coverage as mandatory
    # Query with testing_mode="disabled"
    # Should not include test-coverage

def test_build_skills_block_compact():
    """Verify block is ≤10 lines."""
    # Seed config with skills
    # Build block
    # Count lines, verify ≤10

def test_check_skill_evidence_complete():
    """Verify detection when all skills have evidence."""
    # Seed config
    # Add skill_outputs for all mandatory
    # Should return complete=True

def test_check_skill_evidence_missing():
    """Verify detection when some skills missing."""
    # Seed config with 2 mandatory
    # Add skill_output for only 1
    # Should return complete=False, missing=[other]

def test_check_skill_evidence_recency():
    """Verify recency window filtering."""
    # Add old skill_output (> 30 min ago)
    # Should not count as evidence
```

### Integration Test

```bash
# Test full flow
rm -f bazinga/bazinga.db

# Initialize DB and seed configs
python3 .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db
python3 .claude/skills/config-seeder/scripts/seed_configs.py --all

# Verify skills_config was seeded
python3 -c "
import sqlite3, json
conn = sqlite3.connect('bazinga/bazinga.db')
row = conn.execute(\"SELECT value FROM configuration WHERE key = 'skills_config'\").fetchone()
assert row, 'skills_config not found'
config = json.loads(row[0])
assert 'developer' in config, 'developer key missing'
print('✓ skills_config seeded correctly')
"

# Test prompt builder includes skills block
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
    --agent-type developer \
    --session-id "test_001" \
    --branch "main" \
    --mode "simple" \
    --testing-mode "full" \
    --allow-no-db 2>/dev/null | grep -A5 "Skills Checklist"

# Test check-skill-evidence command
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py \
    check-skill-evidence "test_001" "developer"
```

---

## Rollback Plan

If issues arise:

1. **seed_configs.py:** Remove `seed_skills_config()` call from main()
2. **prompt_builder.py:** Remove `build_skills_block()` call from build_prompt()
3. **bazinga_db.py:** Remove `check-skill-evidence` command handler

Each change is isolated and independently reversible. No schema changes needed.

---

## Success Criteria

| Criteria | How to Verify |
|----------|---------------|
| skills_config seeded by --all | Query configuration table |
| Prompt includes skills checklist | Check prompt output for "Skills Checklist" |
| Evidence check works | Run check-skill-evidence command |
| No token budget impact | Compare prompt sizes before/after |
| No breaking changes | Run existing tests |

---

## References

- `research/skills-configuration-enforcement-plan.md` - Approved plan with LLM review
- `.claude/skills/config-seeder/scripts/seed_configs.py` - Seeding pattern
- `.claude/skills/prompt-builder/scripts/prompt_builder.py` - Prompt building pattern
- `.claude/skills/bazinga-db/scripts/bazinga_db.py` - DB command pattern
