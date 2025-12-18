# Bazinga-DB Path Resolution: Robust Cross-Context Detection

**Date:** 2025-12-18
**Context:** Orchestration running from client projects fails with "can't open file" errors when bazinga_db.py path is wrong
**Decision:** Python Runner Script (Option E) - short-term; Python Packaging - long-term
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

When BAZINGA orchestration runs in a client project (e.g., `/Users/chaouachimehdi/IdeaProjects/CDC/mobile/delivery-app/`), the bazinga-db skill fails because:

1. The SKILL.md instructs agents to run: `python3 .claude/skills/bazinga-db/scripts/bazinga_db.py`
2. This **relative path** assumes CWD is the project root
3. During orchestration, the CWD may be different (e.g., a subdirectory, or the wrong project entirely)
4. The script can't be found, causing silent failures in agent logging

**Actual error observed:**
```
/opt/homebrew/Cellar/python@3.14/3.14.2/.../Python: can't open file
'/Users/chaouachimehdi/IdeaProjects/CDC/mobile/delivery-app/.claude/skills/bazinga-db/scripts/bazinga_db.py':
[Errno 2] No such file or directory
```

The script **exists** at the correct location, but the path **resolution** fails because it's being invoked from the wrong context.

---

## Current Architecture

### Path Detection Chain (bazinga_paths.py)

```
Priority 1: --db flag (explicit override)
Priority 2: --project-root flag
Priority 3: BAZINGA_ROOT environment variable
Priority 4: .bazinga/paths.env file
Priority 5: Script location (walk up from __file__)
Priority 6: Current working directory (walk up from CWD)
```

### The Problem

The **script invocation path** in SKILL.md is:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command>
```

This fails when:
- CWD ≠ project root
- Agent is in a subdirectory
- Orchestration context has different CWD

### Current Detection Logic

`bazinga_paths.py` has robust detection **once the script runs**, but the issue is **the script can't be found to run in the first place**.

---

## Solution Design

### Option A: Absolute Path via Script Discovery (Recommended)

**Concept:** Before invoking `bazinga_db.py`, dynamically discover its absolute path using a shell-based search.

**Implementation:**

```bash
# In SKILL.md, replace:
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command>

# With discovery pattern:
BAZINGA_DB_SCRIPT=$(python3 -c "
from pathlib import Path
import os

# Priority 1: BAZINGA_ROOT env var
if os.environ.get('BAZINGA_ROOT'):
    p = Path(os.environ['BAZINGA_ROOT']) / '.claude/skills/bazinga-db/scripts/bazinga_db.py'
    if p.exists(): print(p); exit(0)

# Priority 2: Walk up from CWD
current = Path.cwd()
for _ in range(10):
    candidate = current / '.claude/skills/bazinga-db/scripts/bazinga_db.py'
    if candidate.exists():
        print(candidate); exit(0)
    if current.parent == current: break
    current = current.parent

# Priority 3: Check common locations
for loc in [Path.home() / 'bazinga', Path('/usr/local/share/bazinga')]:
    p = loc / '.claude/skills/bazinga-db/scripts/bazinga_db.py'
    if p.exists(): print(p); exit(0)

print('ERROR: bazinga_db.py not found', file=__import__('sys').stderr)
exit(1)
")
python3 "$BAZINGA_DB_SCRIPT" --quiet <command>
```

**Pros:**
- Works regardless of CWD
- Leverages existing Python for cross-platform compatibility
- No new dependencies

**Cons:**
- Adds overhead (extra Python invocation)
- Complex shell quoting

### Option B: Environment Variable Injection (Simpler)

**Concept:** The orchestrator sets `BAZINGA_DB` environment variable at session start, containing the absolute path to the script.

**Implementation:**

1. **Orchestrator** (at session start):
   ```bash
   # Detect and set once
   export BAZINGA_DB="$(dirname $(realpath .claude/skills/bazinga-db/scripts/bazinga_db.py))/bazinga_db.py"
   ```

2. **SKILL.md** uses:
   ```bash
   python3 "${BAZINGA_DB:-$(pwd)/.claude/skills/bazinga-db/scripts/bazinga_db.py}" --quiet <command>
   ```

**Pros:**
- Simple, minimal changes
- No per-invocation overhead
- Fallback to relative path if env not set

**Cons:**
- Requires orchestrator to set env var
- Env vars may not propagate to all sub-shells

### Option C: Wrapper Script with Self-Discovery

**Concept:** Create a `bazinga-db` wrapper script that handles path discovery internally.

**Implementation:**

1. Create `scripts/bazinga-db` (no .py extension, executable):
   ```bash
   #!/usr/bin/env bash
   # Self-discovering wrapper for bazinga_db.py

   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   exec python3 "$SCRIPT_DIR/bazinga_db.py" "$@"
   ```

2. Install wrapper to a PATH location during `bazinga install`

3. SKILL.md uses:
   ```bash
   bazinga-db --quiet <command>
   ```

**Pros:**
- Cleanest invocation syntax
- Always works via PATH lookup
- Self-contained

**Cons:**
- Requires PATH modification or symlink installation
- More installation complexity
- May conflict with other tools

### Option D: Python Module Invocation (Long-term)

**Concept:** Install bazinga-db as a proper Python module, invoke via `python -m`

**Implementation:**

1. Structure:
   ```
   bazinga_db/
   ├── __init__.py
   ├── __main__.py  # Entry point
   └── db.py        # Actual implementation
   ```

2. Install via pip (already done for bazinga CLI)

3. SKILL.md uses:
   ```bash
   python3 -m bazinga_db --quiet <command>
   ```

**Pros:**
- Proper Python packaging
- Works from any directory
- Clean module semantics

**Cons:**
- Major refactoring
- Changes deployment model
- May not work if module not installed
- **Current directory names use hyphens (bazinga-db) which are invalid Python module names**

### Option E: Python Runner Script (NEW - RECOMMENDED)

**Concept:** Create a cross-platform Python wrapper script at a stable path that discovers and invokes `bazinga_db.py` using `pathlib` only.

**Implementation:**

1. Create `scripts/bazinga_db_runner.py`:
   ```python
   #!/usr/bin/env python3
   """
   Cross-platform runner for bazinga_db.py.
   Discovers the script location by walking up from __file__ or CWD.
   Works regardless of current working directory.
   """
   import sys
   import os
   from pathlib import Path

   def find_bazinga_db_script() -> Path:
       """Find bazinga_db.py by walking up directory tree."""
       # Priority 1: Walk up from this script's location
       current = Path(__file__).resolve().parent
       for _ in range(15):
           candidate = current / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
           if candidate.exists():
               return candidate
           # Also check if we're already in .claude structure
           if current.name == 'scripts' and (current.parent.parent.parent / '.claude').exists():
               return current.parent.parent / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
           if current.parent == current:
               break
           current = current.parent

       # Priority 2: Walk up from CWD
       current = Path.cwd().resolve()
       for _ in range(15):
           candidate = current / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
           if candidate.exists():
               return candidate
           if current.parent == current:
               break
           current = current.parent

       # Priority 3: Check BAZINGA_ROOT env var
       env_root = os.environ.get('BAZINGA_ROOT')
       if env_root:
           candidate = Path(env_root) / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
           if candidate.exists():
               return candidate

       return None

   def main():
       script_path = find_bazinga_db_script()
       if script_path is None:
           print("ERROR: Could not find bazinga_db.py", file=sys.stderr)
           print("Searched from:", file=sys.stderr)
           print(f"  - Script location: {Path(__file__).resolve().parent}", file=sys.stderr)
           print(f"  - CWD: {Path.cwd()}", file=sys.stderr)
           print(f"  - BAZINGA_ROOT: {os.environ.get('BAZINGA_ROOT', 'not set')}", file=sys.stderr)
           print("\nEnsure you're in a BAZINGA project with .claude/skills/bazinga-db/", file=sys.stderr)
           sys.exit(1)

       # Execute bazinga_db.py with all arguments
       os.execv(sys.executable, [sys.executable, str(script_path)] + sys.argv[1:])

   if __name__ == '__main__':
       main()
   ```

2. All agents invoke via:
   ```bash
   python3 scripts/bazinga_db_runner.py --quiet <command>
   ```

3. For Windows, provide `scripts/bazinga-db.ps1`:
   ```powershell
   $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
   python3 "$ScriptDir/bazinga_db_runner.py" @args
   ```

**Pros:**
- Cross-platform (pure Python, no shell dependencies)
- Works from any directory
- Self-contained discovery logic
- No installation required
- Actionable error messages when script not found
- Single source of truth for path resolution

**Cons:**
- Extra script to maintain
- Slightly more complex invocation path

---

## Critical Analysis

### Pros ✅

| Option | Key Advantage |
|--------|---------------|
| A (Discovery) | Works now, no installation changes |
| B (Env Var) | ~~Minimal code change~~ **REJECTED** |
| C (Wrapper) | Cleaner UX long-term |
| D (Module) | Most "correct" Python solution |
| **E (Runner)** | **Cross-platform, no deps, works from any CWD** |

### Cons ⚠️

| Option | Key Disadvantage |
|--------|------------------|
| A (Discovery) | Extra Python overhead per invocation |
| B (Env Var) | **FATAL: Env vars don't persist across Bash tool calls** |
| C (Wrapper) | Installation complexity |
| D (Module) | Major refactoring required, hyphen in dir name |
| **E (Runner)** | Extra script to maintain |

### Verdict

**Recommended: Option E (Python Runner Script) - short-term**
**Long-term: Option D (Python Module) after directory restructuring**

**Rationale:**
1. ~~Option B~~ **REJECTED** - Each Bash tool execution is a fresh process; env vars set in one call don't persist to the next
2. Option E is pure Python, cross-platform (works on Windows), and requires no installation changes
3. Option E provides actionable error messages when the script can't be found
4. Long-term, proper Python packaging (Option D) eliminates path issues entirely but requires renaming `bazinga-db` to `bazinga_db` (valid module name)

---

## Proposed Implementation (REVISED per OpenAI Review)

### Phase 1: Create Python Runner Script

Create `scripts/bazinga_db_runner.py` with cross-platform discovery:

```python
#!/usr/bin/env python3
"""
Cross-platform runner for bazinga_db.py.
Discovers the script location by walking up from __file__ or CWD.
Works regardless of current working directory.
"""
import sys
import os
from pathlib import Path

def find_bazinga_db_script() -> Path:
    """Find bazinga_db.py by walking up directory tree."""
    # Priority 1: Walk up from this script's location
    current = Path(__file__).resolve().parent
    for _ in range(15):
        candidate = current / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    # Priority 2: Walk up from CWD
    current = Path.cwd().resolve()
    for _ in range(15):
        candidate = current / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    # Priority 3: Check BAZINGA_ROOT env var (optimization, not required)
    env_root = os.environ.get('BAZINGA_ROOT')
    if env_root:
        candidate = Path(env_root) / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
        if candidate.exists():
            return candidate

    return None

def main():
    script_path = find_bazinga_db_script()
    if script_path is None:
        print("ERROR: Could not find bazinga_db.py", file=sys.stderr)
        print("Searched from:", file=sys.stderr)
        print(f"  - Script location: {Path(__file__).resolve().parent}", file=sys.stderr)
        print(f"  - CWD: {Path.cwd()}", file=sys.stderr)
        print(f"  - BAZINGA_ROOT: {os.environ.get('BAZINGA_ROOT', 'not set')}", file=sys.stderr)
        print("\nEnsure you're in a BAZINGA project with .claude/skills/bazinga-db/", file=sys.stderr)
        sys.exit(1)

    # Execute bazinga_db.py with all arguments
    os.execv(sys.executable, [sys.executable, str(script_path)] + sys.argv[1:])

if __name__ == '__main__':
    main()
```

### Phase 2: Update All Agent Documentation

Replace ALL occurrences of:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command>
```

With:
```bash
python3 scripts/bazinga_db_runner.py --quiet <command>
```

Files to update:
- `.claude/skills/bazinga-db/SKILL.md`
- `agents/developer.md`
- `agents/qa_expert.md`
- `agents/techlead.md`
- `agents/senior_software_engineer.md`
- `agents/project_manager.md`
- Any other files referencing the direct path

### Phase 3: Add Windows Support

Create `scripts/bazinga-db.ps1`:
```powershell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python3 "$ScriptDir/bazinga_db_runner.py" @args
```

### Phase 4: Add bazinga_paths Helper

Add to `bazinga_paths.py`:
```python
def get_skill_script_path(skill_name: str, script_name: str = None,
                          project_root: Optional[Path] = None) -> Path:
    """Get absolute path to a skill's script.

    Args:
        skill_name: Name of skill (e.g., "bazinga-db")
        script_name: Script filename (defaults to skill_name.replace('-','_') + '.py')
        project_root: Pre-computed project root

    Returns:
        Absolute path to the script
    """
    root = project_root or get_project_root()
    if script_name is None:
        script_name = skill_name.replace('-', '_') + '.py'
    return root / '.claude' / 'skills' / skill_name / 'scripts' / script_name
```

### Phase 5: Add CI Tests

Create `tests/test_path_resolution.py`:
```python
def test_runner_from_project_root():
    """Runner works from project root."""

def test_runner_from_nested_dir():
    """Runner works from nested subdirectory."""

def test_runner_with_wrong_cwd():
    """Runner provides actionable error when not in project."""

def test_runner_cross_platform():
    """Runner works on Windows/macOS/Linux."""
```

---

## Comparison to Alternatives

| Approach | Complexity | Reliability | Overhead | Backwards Compatible | Cross-Platform |
|----------|------------|-------------|----------|---------------------|----------------|
| Current (relative) | Low | **Low** | None | Yes | Yes |
| Env var only (B) | Low | **Low** ❌ | None | Yes | Yes |
| Discovery inline (A) | Medium | High | ~50ms | Yes | **No** (bash) |
| **Python Runner (E)** | Medium | **Very High** | ~10ms | Yes | **Yes** |
| Python module (D) | High | Very High | None | No | Yes |

**Legend:**
- ❌ Env var approach fails because each Bash tool call is a fresh process

---

## Decision Rationale (REVISED)

The Python Runner Script (Option E) is chosen because:

1. **Cross-platform** - Pure Python, works on Windows/macOS/Linux (no bash dependencies)
2. **No installation changes** - Just add one file and update references
3. **High reliability** - Works regardless of CWD by walking up from script location
4. **Actionable errors** - Clear error messages show where it searched
5. **Future-proof** - Sets foundation for proper module packaging later

**Why NOT Option B (Env Var)?**
- Each Bash tool execution is a fresh process
- Env vars set in one Bash call don't persist to the next
- This is a fundamental limitation of the Claude Code process model

---

## Implementation Checklist (REVISED)

- [ ] Create `scripts/bazinga_db_runner.py` with cross-platform discovery
- [ ] Create `scripts/bazinga-db.ps1` for Windows PowerShell support
- [ ] Add `get_skill_script_path()` to `bazinga_paths.py`
- [ ] Update SKILL.md to use `python3 scripts/bazinga_db_runner.py`
- [ ] Update all agent docs (developer.md, qa_expert.md, techlead.md, etc.)
- [ ] Add `scripts/bazinga_db_runner.py` to installer (pyproject.toml)
- [ ] Create `tests/test_path_resolution.py` with cross-platform tests
- [ ] Test from project root
- [ ] Test from nested subdirectory
- [ ] Test with wrong CWD (different project)
- [ ] Test on Windows (if available)

---

## Risk Assessment (REVISED)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Runner adds overhead | Low | Low | ~10ms overhead, negligible |
| Partial adoption (docs not updated) | Medium | High | Grep for old path, update all |
| Windows edge cases | Low | Medium | Test on Windows CI |
| Runner script not included in install | Medium | High | Add to pyproject.toml shared-data |
| `os.execv` doesn't work on Windows | Low | Medium | Use `subprocess.run` fallback |

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-18)

### Critical Issues Identified

1. **Option B (Env Var) is FATAL** - Each Bash tool execution is a fresh process; env vars don't persist
2. **Path discovery in SKILL.md won't fix callers** - Agents invoke via `Skill(command: "bazinga-db")`, not Python directly
3. **Windows/PowerShell not addressed** - Bash utilities (realpath, dirname) don't work on Windows
4. **Hyphen in module name** - `bazinga-db` is invalid Python module name, breaks `python -m`
5. **Duplication risk** - Many docs embed the relative path; changing one leaves others broken

### Incorporated Feedback ✅

| Suggestion | Incorporated As |
|------------|-----------------|
| Add Python entry shim (wrapper) | **Phase 1**: `scripts/bazinga_db_runner.py` |
| Use pathlib only (cross-platform) | Runner uses pure Python, no shell dependencies |
| Provide actionable error messages | Runner prints search locations on failure |
| Add Windows support | **Phase 3**: `scripts/bazinga-db.ps1` |
| Remove env var as recommended | Moved Option B to REJECTED status |
| Single source of truth for paths | All docs will reference runner script |
| Add CI tests for path resolution | **Phase 5**: `tests/test_path_resolution.py` |
| Add `get_skill_script_path()` helper | **Phase 4**: Added to `bazinga_paths.py` |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Rename dirs to valid module names now | Too disruptive; breaks existing installations. Deferred to v2. |
| Package as console_scripts entry point | Requires major packaging changes. Long-term goal, not short-term fix. |
| Ship shell+bat launcher duo | Adds complexity; Python runner is simpler and cross-platform. |

### Risk Mitigations Added

1. **Partial adoption risk**: Implementation checklist includes grep for old path across all files
2. **Windows `os.execv`**: Add `subprocess.run` fallback in runner for Windows compatibility
3. **Installer inclusion**: Explicitly add runner to pyproject.toml shared-data

---

## References

- Error observed: `/Users/chaouachimehdi/IdeaProjects/CDC/mobile/delivery-app/.claude/skills/bazinga-db/scripts/bazinga_db.py`
- Current path detection: `.claude/skills/_shared/bazinga_paths.py`
- SKILL.md invocation: `.claude/skills/bazinga-db/SKILL.md`
- Project root detection rules: `.claude/claude.md` (Path Layout section)
