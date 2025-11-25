# Wheel Packaging for Bazinga Config Files: Analysis and Implementation

**Date:** 2025-11-25
**Context:** PR #122 review feedback on `ignore-vcs = true` security concerns
**Decision:** Use `force-include` for explicit file inclusion instead of VCS bypass
**Status:** Implemented

---

## Problem Statement

The `bazinga/` directory contains two types of files:
1. **Config files** (needed for distribution): `model_selection.json`, `challenge_levels.json`, `skills_config.json`, `templates/`
2. **Runtime artifacts** (must NOT be distributed): `bazinga.db*`, `artifacts/`, `pm_state.json`, etc.

The `.gitignore` pattern `bazinga/` ignores the entire directory, with negation patterns to un-ignore specific config files. This works for git tracking but creates a wheel packaging challenge.

### Initial Approach (Problematic)
```toml
[tool.hatch.build.targets.wheel]
ignore-vcs = true

[tool.hatch.build.targets.wheel.shared-data]
"bazinga" = "share/bazinga_cli/bazinga"
```

### Security Concerns Raised
1. **Runtime artifact leakage**: If developers build wheels locally after running BAZINGA, database files, session artifacts, and state files would be bundled
2. **Broad VCS bypass**: `ignore-vcs = true` is a sledgehammer that affects ALL files, not just the ones we need
3. **Unpredictable builds**: Wheel contents would vary based on local development state

---

## Solution Analysis

### Option 1: ignore-vcs + exclude patterns
```toml
ignore-vcs = true
exclude = ["bazinga/artifacts", "bazinga/*.db*", ...]
```

**Result:** Failed - `exclude` patterns in `[tool.hatch.build.targets.wheel]` don't apply to `shared-data` entries. Hatchling processes exclusions separately from shared-data mapping.

### Option 2: Explicit file paths in shared-data
```toml
"bazinga/model_selection.json" = "share/bazinga_cli/bazinga/model_selection.json"
"bazinga/templates" = "share/bazinga_cli/bazinga/templates"
```

**Result:** Failed - Hatchling's VCS exclusion applies at directory level. Since `bazinga/` matches gitignore, even explicit paths within it are excluded before negation patterns are processed.

### Option 3: force-include as package data (Chosen)
```toml
[tool.hatch.build.targets.wheel.force-include]
"bazinga/model_selection.json" = "bazinga_cli/bazinga/model_selection.json"
"bazinga/challenge_levels.json" = "bazinga_cli/bazinga/challenge_levels.json"
"bazinga/skills_config.json" = "bazinga_cli/bazinga/skills_config.json"
"bazinga/templates" = "bazinga_cli/bazinga/templates"
```

**Result:** Success - Files are explicitly included as package data, bypassing both VCS exclusion and shared-data complexity.

---

## Critical Analysis

### Pros
- **Explicit inclusion**: Only specified files are included, nothing else
- **No VCS bypass**: Don't need `ignore-vcs = true`, maintaining gitignore protection
- **Self-documenting**: Config clearly lists exactly what's distributed
- **Immune to local state**: Runtime artifacts can never leak into wheel
- **Simpler mental model**: Package data location is predictable

### Cons
- **Requires CLI update**: CLI must check package directory, not just shared-data location
- **Different path structure**: Files at `bazinga_cli/bazinga/` vs `share/bazinga_cli/bazinga/`
- **Manual maintenance**: Adding new config files requires updating pyproject.toml

### Verdict
The `force-include` approach is the correct solution. The security benefits far outweigh the maintenance overhead. The CLI changes are minimal (fallback checks) and make the code more robust.

---

## Implementation Details

### pyproject.toml Changes
```toml
[tool.hatch.build.targets.wheel.force-include]
# Force-include bazinga config files as package data
# These are gitignored (for runtime state) but needed for distribution
"bazinga/model_selection.json" = "bazinga_cli/bazinga/model_selection.json"
"bazinga/challenge_levels.json" = "bazinga_cli/bazinga/challenge_levels.json"
"bazinga/skills_config.json" = "bazinga_cli/bazinga/skills_config.json"
"bazinga/templates" = "bazinga_cli/bazinga/templates"
```

### CLI Changes (src/bazinga_cli/__init__.py)
Updated `copy_templates()` and `copy_bazinga_configs()` to check package directory as fallback:

```python
source_bazinga = self.source_dir / "bazinga"
if not source_bazinga.exists():
    # Fallback: Check package directory (for pip/uvx installs with force-include)
    package_dir = Path(__file__).parent / "bazinga"
    if package_dir.exists():
        source_bazinga = package_dir
```

---

## Comparison to Alternatives

| Approach | Security | Maintenance | Complexity |
|----------|----------|-------------|------------|
| ignore-vcs + shared-data | Bad (leaks artifacts) | Low | Low |
| ignore-vcs + exclude | Bad (doesn't work) | Medium | High |
| Explicit shared-data paths | Good | High | Medium |
| **force-include (chosen)** | **Excellent** | **Medium** | **Low** |

---

## Decision Rationale

1. **Security is non-negotiable**: Runtime artifacts must never ship in wheels
2. **Explicit > implicit**: Listing files explicitly prevents surprises
3. **hatchling limitations**: VCS exclusion doesn't support per-path negation for shared-data
4. **CLI flexibility**: Small changes to support multiple source locations is good design
5. **Future-proof**: Adding new config files is straightforward (add to force-include)

---

## Lessons Learned

1. **gitignore negation patterns** don't work as expected with hatchling's shared-data
2. **`exclude` patterns** in wheel config only affect package contents, not shared-data
3. **force-include** is the correct tool for including VCS-ignored files explicitly
4. **Package data vs shared-data**: Package data is simpler for files that need to be bundled

---

## References

- PR #122: https://github.com/mehdic/bazinga/pull/122
- Hatchling force-include docs: https://hatch.pypa.io/latest/config/build/#force-include
- Original issue: bazinga configs not included in pip/uvx installs
