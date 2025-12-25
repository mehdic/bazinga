# Absolute Path Resolution for BAZINGA Scripts: Ultrathink Analysis

**Date:** 2025-12-25
**Context:** Scripts fail with "No such file or directory" when CWD differs from project root
**Decision:** Two-layer solution - (1) Skills auto-chdir + resolve paths, (2) Optional `bazinga-skill` runner
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5 (2025-12-25)

---

## Problem Statement

### The Error Pattern

When users invoke BAZINGA skills or scripts from a working directory that differs from the project root, scripts fail:

```bash
# User's CWD: /Users/chaouachimehdi/IdeaProjects/CDC/web/
# BAZINGA installed at: /Users/chaouachimehdi/IdeaProjects/CDC/

Error: Exit code 2
/opt/homebrew/Cellar/python@3.14/3.14.2/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python: can't open file
'/Users/chaouachimehdi/IdeaProjects/CDC/web/.claude/skills/prompt-builder/scripts/prompt_builder.py': [Errno 2] No such file or directory
```

### Root Cause Analysis

1. **All script invocations use relative paths**:
   ```bash
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py
   ```

2. **These paths are relative to CWD**, not to the project root

3. **CWD can differ from project root** when:
   - User navigates to a subdirectory (e.g., `cd src/` before invoking)
   - IDE terminal opens in a subdirectory
   - Monorepo with multiple workspaces
   - Scripts called from git hooks in different contexts

4. **Existing detection exists but isn't used**:
   - `bazinga_paths.py` has robust project root detection
   - But the **skill invocation syntax** in `.md` files uses hardcoded relative paths
   - The Python script has detection, but it's never reached because the path to the script itself fails

### Scope of Impact

**Files using relative script paths:**
| File Type | Count | Example |
|-----------|-------|---------|
| SKILL.md files | 10+ | `.claude/skills/prompt-builder/SKILL.md` |
| Agent templates | 5+ | `templates/tech_lead_speckit.md` |
| Integration tests | 15+ | `tests/integration/simple-calculator-spec.md` |
| Documentation | 10+ | Various `.md` files |

---

## Solution Options

### Option 1: Environment Variable at Install Time

**Concept:** Capture project root during `bazinga install` and persist it as an environment variable.

**Implementation:**

1. **During `bazinga install`:**
   ```python
   # In BazingaSetup.install()
   project_root = Path.cwd().resolve()

   # Write to a dotenv file
   env_file = project_root / ".bazinga" / "env"
   env_file.parent.mkdir(exist_ok=True)
   env_file.write_text(f"BAZINGA_ROOT={project_root}\n")
   ```

2. **Create a source script for shell sessions:**
   ```bash
   # .bazinga/activate.sh
   export BAZINGA_ROOT="/path/to/project"
   ```

3. **Update script invocations to use the variable:**
   ```bash
   # Before
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py

   # After
   python3 "${BAZINGA_ROOT}/.claude/skills/prompt-builder/scripts/prompt_builder.py"
   ```

**Pros:**
- ✅ Standard Unix convention (like virtualenv's `activate`)
- ✅ Works across all shell types (bash, zsh, fish)
- ✅ Easy to understand and debug
- ✅ No runtime overhead

**Cons:**
- ⚠️ Requires manual sourcing: `source .bazinga/activate.sh`
- ⚠️ Users may forget to source before running commands
- ⚠️ Doesn't work automatically with Claude Code's Bash tool
- ⚠️ IDE terminal integration varies

---

### Option 2: Wrapper Scripts with Self-Resolution

**Concept:** Create thin wrapper scripts that resolve the project root dynamically before calling Python.

**Implementation:**

1. **Create wrapper script:**
   ```bash
   #!/usr/bin/env bash
   # .claude/skills/prompt-builder/run.sh

   # Find project root by walking up from script location
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

   # Verify we found the right root
   if [[ ! -d "$PROJECT_ROOT/.claude" ]] || [[ ! -d "$PROJECT_ROOT/bazinga" ]]; then
       echo "ERROR: Cannot find BAZINGA project root from script location" >&2
       exit 1
   fi

   # Run Python script with absolute path
   cd "$PROJECT_ROOT"
   python3 "$SCRIPT_DIR/scripts/prompt_builder.py" "$@"
   ```

2. **Update skill invocations:**
   ```bash
   # Before
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py

   # After
   .claude/skills/prompt-builder/run.sh
   ```

3. **Problem:** The wrapper script itself uses a relative path!

**Pros:**
- ✅ Self-contained, no manual setup
- ✅ Uses `${BASH_SOURCE[0]}` which is always the script's path

**Cons:**
- ❌ **Doesn't solve the problem** - the wrapper path is still relative
- ⚠️ Extra file per skill (maintenance burden)
- ⚠️ Adds shell overhead

---

### Option 3: Python Package Entry Points (CLI Commands)

**Concept:** Install Python scripts as executable commands via pip entry points.

**Implementation:**

1. **Add entry points to pyproject.toml:**
   ```toml
   [project.scripts]
   bazinga-prompt-builder = "bazinga_cli.skills.prompt_builder:main"
   bazinga-db = "bazinga_cli.skills.bazinga_db:main"
   bazinga-config-seeder = "bazinga_cli.skills.config_seeder:main"
   ```

2. **Scripts become globally available:**
   ```bash
   # Before (relative path)
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py

   # After (global command)
   bazinga-prompt-builder --params-file ...
   ```

3. **Each script knows its project root:**
   ```python
   # The script uses bazinga_paths.py internally
   from bazinga_paths import get_project_root
   root = get_project_root()  # Uses CWD detection or BAZINGA_ROOT env var
   ```

**Pros:**
- ✅ Clean, professional approach
- ✅ Works from any directory
- ✅ No path manipulation in skill files
- ✅ Scripts can be versioned with the package

**Cons:**
- ⚠️ Requires package reinstall to update scripts
- ⚠️ Development mode more complex (editable install)
- ⚠️ All skills need to be bundled into the package
- ⚠️ Namespace pollution (many `bazinga-*` commands)

---

### Option 4: Persistent Config File with Auto-Detection (RECOMMENDED)

**Concept:** Write project root to a config file during install, then have Python scripts auto-detect and use it.

**Implementation:**

1. **During `bazinga install`, write config:**
   ```python
   # In BazingaSetup.install()
   config_dir = target_dir / ".bazinga"
   config_dir.mkdir(exist_ok=True)

   config = {
       "version": "1.0",
       "project_root": str(target_dir.resolve()),
       "installed_at": datetime.now().isoformat()
   }

   (config_dir / "config.json").write_text(json.dumps(config, indent=2))
   ```

2. **Update `bazinga_paths.py` to read from config:**
   ```python
   def _detect_from_config_file() -> Optional[Path]:
       """Check for .bazinga/config.json in CWD or ancestors."""
       current = Path.cwd().resolve()
       while current != current.parent:
           config_file = current / ".bazinga" / "config.json"
           if config_file.exists():
               data = json.loads(config_file.read_text())
               root = Path(data.get("project_root", ""))
               if root.exists() and _is_bazinga_project_root(root)[0]:
                   return root
           current = current.parent
       return None
   ```

3. **Key insight: Python scripts already use `bazinga_paths.py`**
   - The scripts themselves work correctly once started
   - The problem is getting Python to find the script file

4. **Create a universal launcher:**
   ```python
   # bazinga_launcher.py (placed in a known location, or as entry point)

   import sys
   from pathlib import Path

   def find_project_root():
       """Find project root from .bazinga/config.json"""
       current = Path.cwd().resolve()
       while current != current.parent:
           config = current / ".bazinga" / "config.json"
           if config.exists():
               import json
               return Path(json.loads(config.read_text())["project_root"])
           current = current.parent
       raise RuntimeError("Not in a BAZINGA project")

   def run_skill_script(skill_name: str, script_name: str = "main.py"):
       root = find_project_root()
       script = root / ".claude" / "skills" / skill_name / "scripts" / script_name
       if not script.exists():
           raise RuntimeError(f"Script not found: {script}")

       # Execute the script
       import runpy
       sys.argv[0] = str(script)
       runpy.run_path(str(script), run_name="__main__")

   # Entry points:
   # bazinga-run prompt-builder prompt_builder.py -- --params-file ...
   ```

**Pros:**
- ✅ Works from any subdirectory
- ✅ Config file is human-readable and debuggable
- ✅ No manual sourcing required
- ✅ Single entry point (`bazinga-run`) for all skills
- ✅ Survives directory changes, IDE restarts, etc.

**Cons:**
- ⚠️ Adds a config file to the project
- ⚠️ Config can become stale if project moved
- ⚠️ Requires updating all skill invocations in docs

---

### Option 5: Dynamic Path Resolution via Python Shim (SIMPLEST)

**Concept:** Create a single Python shim script that's installed as a CLI command and resolves paths dynamically.

**Implementation:**

1. **Add single entry point to pyproject.toml:**
   ```toml
   [project.scripts]
   bz = "bazinga_cli.runner:main"
   ```

2. **Create the runner module:**
   ```python
   # src/bazinga_cli/runner.py
   """
   Universal BAZINGA script runner.

   Usage:
       bz prompt-builder --params-file ...
       bz db list-sessions 10
       bz config-seeder seed-all
   """

   import sys
   import json
   import importlib.util
   from pathlib import Path

   # Map short names to script paths
   SKILL_SCRIPTS = {
       "prompt-builder": ".claude/skills/prompt-builder/scripts/prompt_builder.py",
       "db": ".claude/skills/bazinga-db/scripts/bazinga_db.py",
       "config-seeder": ".claude/skills/config-seeder/scripts/seed_configs.py",
       "specialization-loader": ".claude/skills/specialization-loader/scripts/load_specializations.py",
   }

   def find_project_root() -> Path:
       """Walk up from CWD to find .bazinga/config.json or .claude + bazinga dirs."""
       current = Path.cwd().resolve()

       while current != current.parent:
           # Check for config file first (fastest)
           config = current / ".bazinga" / "config.json"
           if config.exists():
               data = json.loads(config.read_text())
               if "project_root" in data:
                   return Path(data["project_root"])

           # Check for directory markers
           if (current / ".claude").is_dir() and (current / "bazinga").is_dir():
               return current

           current = current.parent

       raise RuntimeError(
           "Not in a BAZINGA project. Ensure you're in a directory with "
           ".claude/ and bazinga/ folders, or run `bazinga init` first."
       )

   def main():
       if len(sys.argv) < 2:
           print("Usage: bz <skill> [args...]")
           print("Skills:", ", ".join(SKILL_SCRIPTS.keys()))
           sys.exit(1)

       skill = sys.argv[1]
       if skill not in SKILL_SCRIPTS:
           print(f"Unknown skill: {skill}")
           print("Available:", ", ".join(SKILL_SCRIPTS.keys()))
           sys.exit(1)

       root = find_project_root()
       script_path = root / SKILL_SCRIPTS[skill]

       if not script_path.exists():
           print(f"Script not found: {script_path}")
           sys.exit(1)

       # Run the script with remaining args
       sys.argv = [str(script_path)] + sys.argv[2:]

       # Load and execute the script
       spec = importlib.util.spec_from_file_location("__main__", script_path)
       module = importlib.util.module_from_spec(spec)
       sys.modules["__main__"] = module
       spec.loader.exec_module(module)
   ```

3. **Update skill invocations:**
   ```bash
   # Before
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py --params-file ...

   # After
   bz prompt-builder --params-file ...
   ```

4. **During install, write config:**
   ```python
   # In BazingaSetup.install()
   config = {"project_root": str(target_dir.resolve()), "version": "1.0"}
   (target_dir / ".bazinga" / "config.json").write_text(json.dumps(config))
   ```

**Pros:**
- ✅ Single command (`bz`) for all skills
- ✅ Short and memorable
- ✅ Works from any directory
- ✅ Auto-installs with package
- ✅ Minimal maintenance (skill map is small)
- ✅ Backward compatible (old paths still work if CWD is correct)

**Cons:**
- ⚠️ Requires updating all documentation and skill files
- ⚠️ Adds dependency on package being installed
- ⚠️ Skill map needs updating when new skills added

---

## Recommended Solution: Hybrid Approach (Options 4 + 5)

### Why Hybrid?

1. **Option 5 (`bz` command)** solves the immediate invocation problem
2. **Option 4 (config file)** provides persistent project root for other use cases

### Implementation Plan

#### Phase 1: Config File Infrastructure

1. **Create `.bazinga/config.json` during install:**
   ```json
   {
     "version": "1.0",
     "project_root": "/absolute/path/to/project",
     "installed_at": "2025-12-25T12:00:00",
     "bazinga_version": "1.1.0"
   }
   ```

2. **Update `bazinga_paths.py`** to read from config as highest priority (after env var)

3. **Add config migration** for existing installs via `bazinga update`

#### Phase 2: Universal Runner (`bz` command)

1. **Create `src/bazinga_cli/runner.py`** with skill mapping

2. **Add entry point** to pyproject.toml:
   ```toml
   [project.scripts]
   bazinga = "bazinga_cli:main"
   bz = "bazinga_cli.runner:main"
   ```

3. **Update SKILL.md files** to use `bz` command:
   ```bash
   # Old
   python3 .claude/skills/prompt-builder/scripts/prompt_builder.py

   # New
   bz prompt-builder
   ```

#### Phase 3: Documentation Updates

1. Update all SKILL.md files
2. Update agent templates
3. Update integration tests
4. Update claude.md

### Rollout Strategy

| Phase | Files | Migration Path |
|-------|-------|----------------|
| 1 | `bazinga install` | New installs get config.json |
| 1 | `bazinga update` | Existing installs get config.json |
| 2 | Entry points | Package reinstall adds `bz` command |
| 3 | Documentation | Search/replace in .md files |

### Backward Compatibility

1. **Relative paths still work** if CWD is project root
2. **`bz` command is additive**, doesn't break existing usage
3. **`bazinga_paths.py`** gains new detection method, falls back to old methods

---

## Critical Analysis

### Pros ✅

1. **Complete solution**: Addresses root cause, not symptoms
2. **Zero manual setup**: No sourcing scripts, no environment management
3. **IDE agnostic**: Works with any terminal, IDE, or CI system
4. **Debuggable**: Config file is human-readable JSON
5. **Extensible**: Easy to add new skills to the runner
6. **Short command**: `bz prompt-builder` is concise

### Cons ⚠️

1. **Breaking change for existing users**: Need to update invocations
2. **Package dependency**: Requires `pip install bazinga`
3. **Config staleness**: If project moved, config points to wrong location
4. **Learning curve**: Users need to know about `bz` command

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Config staleness | Add `--refresh` flag to `bz` to update config |
| Breaking change | Keep relative paths working, deprecate gradually |
| Package not installed | Error message guides user to install |
| Unknown skills | Error lists available skills |

---

## Verdict

**Recommendation: Implement Hybrid Approach (Options 4 + 5)**

The `bz` command with config.json backup provides:
- Immediate fix for the path resolution problem
- Zero manual setup for users
- Clean, short invocation syntax
- Robust fallback chain (config → env var → directory markers → CWD)

---

## Implementation Details

### File Changes Required

| File | Change |
|------|--------|
| `pyproject.toml` | Add `bz` entry point |
| `src/bazinga_cli/__init__.py` | Write config.json in install |
| `src/bazinga_cli/runner.py` | New file - universal runner |
| `.claude/skills/_shared/bazinga_paths.py` | Add config.json detection |
| All SKILL.md files | Update invocation commands |
| Agent templates | Update script paths |
| Integration tests | Update script paths |

### New Files

1. **`src/bazinga_cli/runner.py`** - Universal skill runner
2. **`.bazinga/config.json`** - Created during install

### Test Cases

1. **Happy path**: `bz prompt-builder` from project root
2. **Subdirectory**: `cd src && bz prompt-builder`
3. **Different project**: Should fail with clear error
4. **Missing skill**: Should list available skills
5. **Config migration**: `bazinga update` creates config.json
6. **Moved project**: Warning + suggestion to run `bazinga init`

---

## Comparison to Alternatives

| Approach | Works from subdirs | No manual setup | Short syntax | Complexity |
|----------|-------------------|-----------------|--------------|------------|
| Current (relative) | ❌ | ✅ | ⚠️ Long | Low |
| Env var only | ✅ | ❌ Source required | ⚠️ Long | Low |
| Entry points per skill | ✅ | ✅ | ✅ | High |
| **Hybrid (bz + config)** | ✅ | ✅ | ✅ | Medium |

---

## Decision Rationale

1. **User friction is high**: Path errors waste significant debugging time
2. **Claude Code context**: The Bash tool cannot source scripts, so env vars don't help
3. **IDE integration**: Users work from various subdirectories naturally
4. **Package already installed**: Users have `pip install bazinga`, adding `bz` is free
5. **One command to learn**: `bz <skill>` is simpler than multiple entry points

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-25)
**Gemini:** Skipped (ENABLE_GEMINI=false)

### Critical Issues Identified

| Issue | Impact | Resolution |
|-------|--------|------------|
| **Params file path resolution** | High - Even with `bz` working, `--params-file bazinga/prompts/...` is relative and won't be found | All skill scripts must resolve relative args against project root |
| **Git ignore for .bazinga/** | Medium - Machine-specific paths would be committed | Add `.bazinga/config.json` to `.gitignore` |
| **Entry-point availability** | High - `bz` command may not be on PATH | Provide fallback documentation; skills self-resolve |
| **Security validation** | Medium - Tampered config.json could redirect execution | Validate resolved root contains `.claude/` and `bazinga/` |
| **Windows path handling** | Low - Entry points work, but PowerShell may need docs | Document execution policy handling |

### Incorporated Feedback

**1. Two-Layer Solution (CRITICAL CHANGE)**

OpenAI correctly identified that the `bz` command alone is insufficient. The real fix requires TWO layers:

**Layer 1: Skill Scripts Auto-Resolve (Primary Fix)**
```python
# At top of every skill script (prompt_builder.py, bazinga_db.py, etc.)
import os
from pathlib import Path

# Add _shared to path for bazinga_paths import
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from bazinga_paths import get_project_root

# Resolve project root and chdir
ROOT = get_project_root()
os.chdir(ROOT)

# Resolve all relative path arguments against ROOT
def resolve_path(p: str) -> str:
    path = Path(p)
    if not path.is_absolute():
        return str(ROOT / path)
    return p
```

**Layer 2: `bazinga-skill` Runner (Convenience)**
- Provides cleaner invocation syntax
- NOT required for functionality (Layer 1 handles CWD)
- Useful for discovery (`bazinga-skill --list`)

**2. Config File with Validation**

```python
def _detect_from_config_file() -> Optional[Path]:
    """Read .bazinga/config.json with security validation."""
    current = Path.cwd().resolve()
    while current != current.parent:
        config_file = current / ".bazinga" / "config.json"
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text())
                root = Path(data.get("project_root", "")).resolve()

                # SECURITY: Validate the root
                if not root.exists():
                    continue
                if ".." in str(root):  # Path traversal check
                    continue
                if not (root / ".claude").is_dir():
                    continue
                if not (root / "bazinga").is_dir():
                    continue

                return root
            except (json.JSONDecodeError, KeyError):
                continue
        current = current.parent
    return None
```

**3. Git Ignore Updates**

```gitignore
# Machine-local BAZINGA config
.bazinga/config.json
.bazinga/paths.env
```

**4. Backward-Compatible Rollout**

| Phase | Change | Effect |
|-------|--------|--------|
| 1 | Update skill scripts to auto-chdir | Fixes CWD problem immediately |
| 2 | Add `bazinga-skill` entry point | Provides cleaner UX |
| 3 | Update SKILL.md files | Documents new syntax |
| 4 | Write config.json in install | Speeds up root detection |

**5. Runner Uses subprocess (Not runpy)**

```python
# Use subprocess to preserve exact behavior
import subprocess
result = subprocess.call(
    [sys.executable, str(script)] + sys.argv[2:],
    cwd=str(root)
)
sys.exit(result)
```

This preserves:
- Exit codes
- stdout/stderr streams
- `if __name__ == "__main__"` semantics
- Relative imports behavior

**6. Canonical Naming**

- **Primary command:** `bazinga-skill` (unambiguous)
- **Alias:** `bz` (short, optional)
- Avoids collision with other tools

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| "Orchestrator-level CWD enforcement only" | Doesn't help when users run skills manually; Layer 1 is more robust |
| "`python -m bazinga_cli.skills.*`" | Requires packaging all skills into the CLI; breaks modularity |
| "Defense-in-depth: Refuse if root outside git repo" | Too restrictive; users may work in non-git directories |

### Revised Implementation Plan

#### Phase 1: Make Skills Self-Resolving (Immediate Fix)

**Files to modify:**
- `.claude/skills/prompt-builder/scripts/prompt_builder.py`
- `.claude/skills/bazinga-db/scripts/bazinga_db.py`
- `.claude/skills/config-seeder/scripts/seed_configs.py`
- `.claude/skills/specialization-loader/scripts/load_specializations.py`

**Change pattern:**
```python
# Add at top of main() or __main__ block
import os
import sys
from pathlib import Path

# Import bazinga_paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from bazinga_paths import get_project_root

# Chdir to project root
ROOT = get_project_root()
os.chdir(ROOT)

# Later, resolve any relative file arguments
if args.params_file and not Path(args.params_file).is_absolute():
    args.params_file = str(ROOT / args.params_file)
```

#### Phase 2: Add Config File Support

**Files to modify:**
- `.claude/skills/_shared/bazinga_paths.py` - Add `_detect_from_config_file()`
- `src/bazinga_cli/__init__.py` - Write config during install
- `.gitignore` - Add `.bazinga/config.json`

#### Phase 3: Add `bazinga-skill` Runner (Optional Enhancement)

**Files to create:**
- `src/bazinga_cli/skill_runner.py`

**Files to modify:**
- `pyproject.toml` - Add entry points

#### Phase 4: Update Documentation

**Files to update:**
- All SKILL.md files
- Agent templates with script paths
- Integration tests

### Test Cases Required

| Test | Description |
|------|-------------|
| `test_skill_from_root` | Run skill from project root - should work |
| `test_skill_from_subdir` | Run skill from `src/` subdirectory - should work |
| `test_relative_params_file` | Params file as relative path - should resolve |
| `test_config_json_detection` | Config file speeds up detection |
| `test_invalid_config_json` | Malformed/invalid config falls back gracefully |
| `test_moved_project` | Moved project with stale config still works via markers |
| `test_security_path_traversal` | Config with `../` in path is rejected |

---

## Lessons Learned

1. **Relative paths in documentation are fragile** - Always consider CWD variations
2. **Python's `__file__` is powerful** - But only works after the script is found
3. **Config files provide persistence** - Better than requiring env var sourcing
4. **Short CLI commands improve DX** - `bz db` beats `python3 .claude/skills/...`

---

## References

- Existing: `.claude/skills/_shared/bazinga_paths.py`
- Existing: `research/centralized-path-management.md`
- Problem: `/Users/chaouachimehdi/IdeaProjects/CDC/web/` CWD mismatch
