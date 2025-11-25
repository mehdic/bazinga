# PR #122 Review Analysis: Dirty Copy Risk

**Date:** 2025-11-25
**Context:** Final review of wheel packaging changes
**Decision:** Implement explicit allowlist for config file copying
**Status:** Implementing

---

## Review Point 1: Dev Mode "Dirty" Copy Risk

### Verdict: **VALID - HIGH PRIORITY FIX NEEDED**

The reviewer correctly identified a security/correctness issue:

**Current code:**
```python
for config_file in source_bazinga.glob("*.json"):
    # copies ALL .json files
```

**Problem:** In dev mode, `_get_config_source("bazinga")` returns project root's `bazinga/` directory which may contain runtime state files:
- `pm_state.json` - PM orchestration state
- `orchestrator_state.json` - orchestrator state
- `group_status.json` - task group status
- Other developer-created state files

**Risk:** A developer running `bazinga install` in their local environment would copy their runtime state into the target project.

**Fix:** Use explicit allowlist matching `pyproject.toml`'s `force-include`:
```python
ALLOWED_CONFIG_FILES = [
    "model_selection.json",
    "challenge_levels.json",
    "skills_config.json",
]
```

---

## Review Point 2: Path Resolution Fragility

### Verdict: **VALID - LOW PRIORITY**

The `Path(__file__).parents[2]` assumption is documented and guarded by `pyproject.toml` marker check. Current implementation is acceptable.

The suggested improvement (iterate up until marker found) is more robust but adds complexity. Consider for future refactoring.

**Current mitigation already in place:**
```python
project_root = Path(__file__).parents[2]
if (project_root / "pyproject.toml").exists():  # Guard check
    dev_path = project_root / relative_path
```

---

## Review Point 3: Type Hint Imports

### Verdict: **NOT AN ISSUE**

`Optional` is already imported:
```python
from typing import Optional
```

---

## Review Point 4: importlib.resources Suggestion

### Verdict: **VALID BUT DEFERRED**

Using `importlib.resources` is the "Pythonic" way but:
- Adds dependency complexity
- Current `__file__` approach works reliably
- Would require more extensive refactoring

Consider for v2.0 or major refactor.

---

## Action Items

1. **[CRITICAL]** Add explicit allowlist to `copy_bazinga_configs()` to prevent runtime state leakage
2. **[OPTIONAL]** Consider robust project root discovery for future
3. **[DEFERRED]** importlib.resources migration

---

## Implementation

The fix aligns config copying with the `force-include` entries in `pyproject.toml`, creating a single source of truth for which files should be distributed.
