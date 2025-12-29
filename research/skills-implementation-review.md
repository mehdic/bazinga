# Skills Configuration Implementation: Ultrathink Review

**Date:** 2025-12-29
**Purpose:** Verify implementation correctness and completeness
**Status:** Under Review
**Reviewed by:** Pending (OpenAI GPT-5)

---

## Changes Made

### Commits
1. `886cfb2` - Add skills configuration enforcement plan with LLM review integration
2. `582a435` - Implement skills configuration enforcement (file-first approach)
3. `e003f86` - Add DB tracking to codebase-analysis, pattern-miner, test-pattern-analysis

### Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `prompt_builder.py` | +110 | Skills block generation |
| `bazinga_db.py` | +102 | check-skill-evidence command |
| `analyze_codebase.py` | +18 | DB tracking |
| `mine.sh` | +13 | DB tracking |
| `analyze_tests.py` | +19 | DB tracking |
| Research docs | +1475 | Planning and documentation |

---

## Implementation Review Checklist

### 1. Prompt Builder (`prompt_builder.py`)

#### Added Constants (lines 96-107)
```python
AGENT_KEY_ALIASES = {"project_manager": "pm"}
TEST_RELATED_SKILLS = {"test-coverage", "test-pattern-analysis"}
AGENTS_KEEP_TEST_SKILLS = {"senior_software_engineer"}
```

**Review Questions:**
- [?] Are all agent aliases covered? (investigator, tech_lead, etc.)
- [?] Are all test-related skills listed?
- [?] Should QA Expert also keep test skills?

#### get_skills_config_from_file() (lines 1471-1486)
```python
def get_skills_config_from_file():
    config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
    if not config_path.exists():
        return None
    # ... read and return
```

**Review Questions:**
- [?] Does PROJECT_ROOT resolve correctly in all modes (dev/installed)?
- [?] Is error handling adequate for malformed JSON?

#### get_skills_for_agent() (lines 1489-1523)
```python
def get_skills_for_agent(agent_type, testing_mode="full"):
    # Apply key aliasing
    agent_key = AGENT_KEY_ALIASES.get(agent_type, agent_type)
    # Filter test skills for non-SSE agents
    if testing_mode in ("disabled", "minimal") and agent_type not in AGENTS_KEEP_TEST_SKILLS:
        mandatory = [s for s in mandatory if s not in TEST_RELATED_SKILLS]
```

**Review Questions:**
- [?] Does filtering work correctly for all agent types?
- [?] What about investigator who has mandatory test-pattern-analysis in some configs?

#### build_skills_block() (lines 1526-1552)
```python
def build_skills_block(agent_type, testing_mode="full"):
    # Compact checklist format (≤10 lines)
    lines = ["## Skills Checklist", ""]
    if skills["mandatory"]:
        lines.append("**MUST invoke before completion:**")
        for skill in skills["mandatory"]:
            lines.append(f'- [ ] `Skill(command: "{skill}")`')
```

**Review Questions:**
- [?] Is the block actually ≤10 lines for agents with many skills?
- [?] Is the format consistent with other prompt sections?

#### Integration in build_prompt() (lines 1844-1850)
```python
# 2.5. Build SKILLS CHECKLIST block (compact, file-first)
if args.agent_type not in ["project_manager", "orchestrator"]:
    testing_mode = getattr(args, 'testing_mode', 'full') or 'full'
    skills_block = build_skills_block(args.agent_type, testing_mode)
    if skills_block:
        components.append(skills_block)
```

**Review Questions:**
- [?] Is insertion point correct (after specialization, before agent definition)?
- [?] Does this affect token budget calculations?
- [?] What happens if testing_mode is None?

---

### 2. Bazinga DB (`bazinga_db.py`)

#### check_skill_evidence() method (lines 1660-1728)
```python
def check_skill_evidence(self, session_id: str, mandatory_skills: List[str],
                        agent_type: Optional[str] = None,
                        since_minutes: int = 30) -> Dict:
    # SQL datetime filtering
    time_modifier = f'-{since_minutes} minutes'
    rows = conn.execute("""
        SELECT DISTINCT skill_name FROM skill_outputs
        WHERE session_id = ?
        AND timestamp >= datetime('now', ?)
    """, (session_id, time_modifier)).fetchall()
```

**Review Questions:**
- [?] Does datetime('now', '-30 minutes') work correctly with SQLite TIMESTAMP format?
- [?] Is agent_type filter applied correctly?
- [?] What if skill_outputs table doesn't exist (old DB)?

#### Command handler (lines 3505-3533)
```python
elif cmd == 'check-skill-evidence':
    # Parse comma-separated skill names
    mandatory_skills = [s.strip() for s in positional_args[1].split(',') if s.strip()]
    result = db.check_skill_evidence(session_id, mandatory_skills, agent_type, since_minutes)
```

**Review Questions:**
- [?] Is comma-separated parsing robust for edge cases?
- [?] What if positional_args[1] is empty string?

---

### 3. Skill DB Tracking

#### codebase-analysis/analyze_codebase.py (lines 387-403)
```python
try:
    import subprocess
    db_script = Path(__file__).parent.parent.parent / "bazinga-db" / "scripts" / "bazinga_db.py"
    db_path = Path("bazinga/bazinga.db")
    if db_script.exists() and db_path.exists():
        subprocess.run([...], capture_output=True, timeout=5)
except Exception:
    pass  # DB save is non-fatal
```

**Review Questions:**
- [?] Does path resolution work when script is invoked from different CWD?
- [?] Is relative path "bazinga/bazinga.db" reliable?
- [?] 5 second timeout - is this adequate?

#### pattern-miner/mine.sh (lines 97-108)
```bash
DB_PATH="bazinga/bazinga.db"
DB_SCRIPT=".claude/skills/bazinga-db/scripts/bazinga_db.py"
if [ -f "$DB_PATH" ] && [ -f "$DB_SCRIPT" ]; then
    python3 "$DB_SCRIPT" --db "$DB_PATH" --quiet save-skill-output \
        "$SESSION_ID" "pattern-miner" "{...}" 2>/dev/null || echo "⚠️  Database save failed"
fi
```

**Review Questions:**
- [?] Is SESSION_ID always available (line 34)?
- [?] Are paths relative to CWD - what if invoked from different directory?

#### test-pattern-analysis/analyze_tests.py (lines 395-412)
```python
try:
    import subprocess
    db_script = Path(__file__).parent.parent.parent / "bazinga-db" / "scripts" / "bazinga_db.py"
    db_path = Path("bazinga/bazinga.db")
    if db_script.exists() and db_path.exists():
        subprocess.run([
            sys.executable, str(db_script),
            "--db", str(db_path), "--quiet",
            "save-skill-output", SESSION_ID, "test-pattern-analysis", json.dumps({...})
        ], capture_output=True, timeout=5)
except Exception:
    pass
```

**Review Questions:**
- [?] SESSION_ID is a module-level variable - is it always set?
- [?] Same path concerns as above

---

## Potential Issues Found

### Issue 1: Relative Path Resolution

All three skill scripts use relative paths:
- `Path("bazinga/bazinga.db")`
- `".claude/skills/bazinga-db/scripts/bazinga_db.py"`

These assume the script is invoked from project root. If invoked from a different directory:
- `db_path.exists()` returns False
- DB save silently fails

**Impact:** Low (save is non-fatal, skill still works)
**Fix:** Use absolute paths via PROJECT_ROOT detection

### Issue 2: Testing Mode for SSE Only

Current filter:
```python
if testing_mode in ("disabled", "minimal") and agent_type not in AGENTS_KEEP_TEST_SKILLS:
    mandatory = [s for s in mandatory if s not in TEST_RELATED_SKILLS]
```

But `AGENTS_KEEP_TEST_SKILLS = {"senior_software_engineer"}` only.

**Investigator** has `test-pattern-analysis: optional` in skills_config.json - this is fine.
But if config changes to mandatory, it would be filtered incorrectly.

**Impact:** Low (current config is correct)
**Fix:** Make AGENTS_KEEP_TEST_SKILLS configurable or derive from skills_config.json

### Issue 3: Token Budget Trimming

The skills block is added as a component but:
- `enforce_global_budget()` doesn't know about it
- `enforce_file_read_budget()` doesn't handle it

If budget is exceeded, skills block may be:
- Kept (unknown section kept by default)
- Or dropped without notice

**Impact:** Medium (could cause prompt bloat or lost guidance)
**Fix:** Add skills block to budget enforcement logic with low priority

### Issue 4: Datetime Comparison in SQLite

```python
time_modifier = f'-{since_minutes} minutes'
# ...
AND timestamp >= datetime('now', ?)
```

This works IF:
- `timestamp` column stores ISO format "YYYY-MM-DD HH:MM:SS"
- `datetime('now', '-30 minutes')` returns same format

SQLite's CURRENT_TIMESTAMP uses "YYYY-MM-DD HH:MM:SS" format.
datetime() function also returns this format.

**Impact:** None (formats match)
**Verified:** SQLite documentation confirms this works

### Issue 5: Missing Skills in skills_config.json

The implementation reads from `bazinga/skills_config.json`. Let me verify all skills are configured:

```json
"developer": {"lint-check": "mandatory", ...}
"senior_software_engineer": {"lint-check": "mandatory", "codebase-analysis": "mandatory", ...}
"tech_lead": {"security-scan": "mandatory", "lint-check": "mandatory", "test-coverage": "mandatory", ...}
"qa_expert": {"pattern-miner": "optional", "quality-dashboard": "optional"}
"pm": {"velocity-tracker": "optional"}
"investigator": {"codebase-analysis": "mandatory", "pattern-miner": "mandatory", ...}
```

**Missing from skills_config.json:**
- `requirements_engineer` - No skills configured
- `orchestrator` - No skills configured (correctly excluded in code)

**Impact:** Low (RE has no mandatory skills, orchestrator excluded)

---

## Test Scenarios to Verify

### Scenario 1: Developer Prompt Generation
```bash
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
    --agent-type developer --session-id test --branch main \
    --mode simple --testing-mode full --allow-no-db 2>/dev/null | grep -A10 "Skills Checklist"
```
**Expected:** Skills block with lint-check mandatory

### Scenario 2: Testing Mode Filtering
```bash
# With testing=disabled, developer should still have lint-check but no test-coverage
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.claude/skills/prompt-builder/scripts')))
from prompt_builder import get_skills_for_agent

# Developer with disabled testing
dev = get_skills_for_agent('developer', 'disabled')
print('Developer (disabled):', dev)

# SSE with disabled testing - should KEEP test-pattern-analysis
sse = get_skills_for_agent('senior_software_engineer', 'disabled')
print('SSE (disabled):', sse)

# Tech Lead with disabled testing - should lose test-coverage
tl = get_skills_for_agent('tech_lead', 'disabled')
print('Tech Lead (disabled):', tl)
"
```

### Scenario 3: Evidence Check with Recency
```bash
# Create test DB and add skill output
rm -f /tmp/test_evidence.db
python3 .claude/skills/bazinga-db/scripts/init_db.py /tmp/test_evidence.db 2>&1 | tail -3

# Create session
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db /tmp/test_evidence.db \
    create-session test_ev simple "Test" 2>&1 | head -2

# Add recent skill output
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db /tmp/test_evidence.db \
    save-skill-output test_ev lint-check '{"passed": true}' --agent developer

# Check evidence
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db /tmp/test_evidence.db \
    check-skill-evidence test_ev "lint-check,security-scan" --agent developer

# Cleanup
rm -f /tmp/test_evidence.db
```

---

## Recommendations

### High Priority
1. **Add skills block to budget trimming** - Modify enforce_global_budget() to handle skills block as low-priority section

### Medium Priority
2. **Use absolute paths in skill DB saves** - Convert relative paths to absolute using PROJECT_ROOT pattern

### Low Priority
3. **Add requirements_engineer to skills_config.json** - Even if empty, for consistency
4. **Make AGENTS_KEEP_TEST_SKILLS configurable** - Read from skills_config.json metadata

---

## Verification Commands Run

```bash
# 1. Skills config read correctly
python3 -c "..." # ✅ Passed

# 2. Agent key aliasing works
python3 -c "..." # ✅ Passed (PM uses 'pm' key)

# 3. SSE keeps test skills
python3 -c "..." # ✅ Passed

# 4. check-skill-evidence command works
python3 ... check-skill-evidence ... # ✅ Passed

# 5. All mandatory skills save to DB
grep -rq "save-skill-output" .claude/skills/{skill}/ # ✅ All 6 pass
```

---

## Summary

| Area | Status | Issues Found |
|------|--------|--------------|
| Prompt Builder | ✅ Working | Token budget integration missing |
| Bazinga DB | ✅ Working | None |
| Skill DB Tracking | ✅ Working | Relative path assumptions |
| Testing Mode Filter | ✅ Working | Edge case for investigator |

**Overall Assessment:** Implementation is functional but has minor gaps in budget enforcement and path resolution. These are non-critical as all failures are graceful (silent or non-fatal).

---

## Multi-LLM Review Integration

*Pending external review*
