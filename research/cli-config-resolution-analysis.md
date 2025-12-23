# CLI Config File Resolution: Root Cause Analysis

**Date:** 2025-11-26
**Context:** User reported "No templates found" and "No config files found" when running `bazinga update` from a different PC
**Decision:** Force-include is working correctly; issue is stale CLI version
**Status:** Resolved

---

## Problem Statement

After implementing `force-include` in pyproject.toml to bundle `bazinga/*.json` configs and `templates/` into the wheel, users on other machines still see:
```
7. Updating templates
  ⚠️  No templates found

7.1. Updating config files
  ⚠️  No config files found
```

## Root Cause Analysis

### What Was Checked

1. **Source files exist**: `/home/user/bazinga/templates/` and `*.json` files are present
2. **Wheel contents are correct**: Built wheel contains:
   - `bazinga_cli/templates/*.md` (7 template files)
   - `bazinga_cli/bazinga/*.json` (3 config files)
3. **Path resolution logic is correct**: `_get_config_source()` checks:
   - Package directory first (`Path(__file__).parent / relative_path`)
   - Shared-data directory (`self.source_dir / relative_path`)
   - Project root for dev mode

### The Actual Issue

**Users installed an OLD version of the CLI** that was built BEFORE the `force-include` changes were added to pyproject.toml.

The old wheel structure:
```
bazinga_cli/
├── __init__.py
├── security.py
└── telemetry.py
# NO bazinga/ subdirectory!
```

The new wheel structure (after force-include):
```
bazinga_cli/
├── __init__.py
├── security.py
├── telemetry.py
└── bazinga/
    ├── challenge_levels.json
    ├── model_selection.json
    ├── skills_config.json
    └── templates/
        ├── completion_report.md
        ├── logging_pattern.md
        └── ... (7 files)
```

### Why Path Resolution Failed

In the OLD installed package:
1. `Path(__file__).parent / "bazinga/templates"` → `site-packages/bazinga_cli/bazinga/templates` → **DOES NOT EXIST**
2. `self.source_dir / "bazinga/templates"` → `share/bazinga_cli/bazinga/templates` → **DOES NOT EXIST** (shared-data never had this)
3. Dev mode fallback → Not applicable (not in project directory)

Result: All three path resolution attempts fail → "No templates found"

## Solution

### Immediate Fix
Users need to **update their CLI** to get the new wheel with force-included files:
```bash
# For uv tool installs
uv tool upgrade bazinga-cli

# For pip installs
pip install --upgrade bazinga-cli

# For fresh install
uv tool install bazinga-cli --force-reinstall
```

### Code Improvement
Added diagnostic hints when files aren't found:
```python
console.print("[yellow]⚠️  No templates found in source[/yellow]")
console.print("[dim]   Checked: package dir, shared-data, project root[/dim]")
console.print("[dim]   Hint: Update CLI with 'uv tool upgrade bazinga-cli' or reinstall[/dim]")
```

This helps users understand:
1. What paths were checked
2. That they likely need to update the CLI

## Architecture Overview

### Three Installation Modes

| Mode | `Path(__file__).parent` | `self.source_dir` | Primary Config Source |
|------|------------------------|-------------------|----------------------|
| **Editable/Dev** | `src/bazinga_cli` | Project root | Project root (`bazinga/`) |
| **Pip/UV wheel** | `site-packages/bazinga_cli` | `share/bazinga_cli` | Package dir (`bazinga_cli/bazinga/`) |
| **Legacy** | `site-packages/bazinga_cli` | `share/bazinga_cli` | Shared-data (if exists) |

### Path Resolution Priority

```python
def _get_config_source(self, relative_path: str) -> Optional[Path]:
    # 1. Package directory (force-included in wheels) ← NEW, highest priority
    # 2. Shared data directory (legacy/system installs)
    # 3. Project root (development/editable mode fallback)
```

The priority ensures:
- **Version-matched configs**: Package dir is checked first to avoid stale shared-data
- **Backward compatibility**: Shared-data still works for legacy installs
- **Dev mode support**: Project root works for editable installs

## Lessons Learned

1. **Version drift is silent**: When users install from different sources/times, they may have different wheel contents. Adding diagnostic output helps identify this.

2. **Force-include timing matters**: The wheel must be rebuilt AFTER adding force-include to pyproject.toml. Old wheels don't have the files.

3. **Shared-data isn't versioned**: Files in `share/bazinga_cli/` persist across updates and can become stale. That's why package dir (force-include) takes priority.

4. **Test on fresh installs**: Always test CLI updates on a fresh environment (not just editable mode) to catch packaging issues.

## Verification Commands

```bash
# Check wheel contents
unzip -l dist/bazinga_cli-*.whl | grep bazinga

# Check installed package
ls -la $(python -c "import bazinga_cli; print(bazinga_cli.__file__)")/..

# Test path resolution
python -c "
from bazinga_cli import BazingaSetup
setup = BazingaSetup()
print('templates:', setup._get_config_source('bazinga/templates'))
print('configs:', setup._get_config_source('bazinga'))
"
```

## References

- PR #122: Original wheel packaging fix
- `pyproject.toml`: force-include configuration
- `src/bazinga_cli/__init__.py`: `_get_config_source()` method
