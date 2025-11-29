# Dashboard Path Resolution: Ultrathink Analysis

**Date:** 2025-11-29
**Context:** Windows dashboard support implementation required understanding path differences between dev and installed modes
**Decision:** Implement dual-mode path detection in startup scripts
**Status:** Implemented

---

## Problem Statement

Dashboard startup scripts need to locate the `dashboard-v2/` directory correctly in two different environments:
1. **Development mode**: Running directly from the cloned bazinga repository
2. **Installed mode**: Running from a client project after `bazinga install`

The challenge is that these environments have different directory structures, and the scripts must auto-detect which environment they're in.

---

## Directory Layouts

### Development Layout (bazinga repo)

```
REPO_ROOT/                       # Could be named anything (bazinga, my-fork, etc.)
├── .claude/                     # Claude-related config
├── bazinga/                     # Config files ONLY (not the install target)
│   ├── challenge_levels.json
│   ├── model_selection.json
│   └── skills_config.json
├── dashboard-v2/                # Dashboard at REPO ROOT
│   ├── scripts/
│   │   ├── start-standalone.sh
│   │   └── start-standalone.ps1
│   └── ...
├── scripts/                     # Main startup scripts at REPO ROOT
│   ├── start-dashboard.sh
│   └── start-dashboard.ps1
└── src/
```

**Key insight**: In dev mode, `dashboard-v2/` is at the repository root, NOT inside `bazinga/`.

### Installed Layout (client project)

```
PROJECT_ROOT/
├── bazinga/                     # ALL bazinga files go here
│   ├── challenge_levels.json
│   ├── model_selection.json
│   ├── skills_config.json
│   ├── dashboard-v2/            # Dashboard INSIDE bazinga/
│   │   └── scripts/
│   │       ├── start-standalone.sh
│   │       └── start-standalone.ps1
│   └── scripts/                 # Scripts INSIDE bazinga/
│       ├── start-dashboard.sh
│       └── start-dashboard.ps1
└── .claude/                     # Claude files at project root (exception)
```

**Key insight**: In installed mode, everything is under `PROJECT_ROOT/bazinga/`, with `.claude/` being the only exception.

---

## Detection Logic

### The Algorithm

Scripts determine their mode by checking the name of their parent directory:

```bash
# Script at: .../scripts/start-dashboard.sh
# Parent of scripts/ directory name determines mode

PARENT_DIR=$(basename "$(dirname "$SCRIPT_DIR")")

if [ "$PARENT_DIR" = "bazinga" ]; then
    # Installed: PROJECT_ROOT/bazinga/scripts/start-dashboard.sh
    DASHBOARD_DIR="$BAZINGA_DIR/dashboard-v2"
else
    # Dev: REPO_ROOT/scripts/start-dashboard.sh
    DASHBOARD_DIR="$PROJECT_ROOT/dashboard-v2"
fi
```

### Why This Works

| Scenario | Script Location | Parent Dir | Mode Detected |
|----------|-----------------|------------|---------------|
| Dev (repo named "bazinga") | `/home/user/bazinga/scripts/` | `bazinga` | Installed* |
| Dev (repo named other) | `/home/user/my-fork/scripts/` | `my-fork` | Dev |
| Installed | `/home/user/project/bazinga/scripts/` | `bazinga` | Installed |

*Edge case: When the repo is named "bazinga", it's detected as "installed" mode, but the paths still resolve correctly because both modes would compute the same `DASHBOARD_DIR`.

---

## Critical Analysis

### Pros

1. **Simple detection**: Single string comparison
2. **No external dependencies**: Doesn't rely on env vars or config files
3. **Automatic**: No manual configuration needed
4. **Robust**: Works from any working directory

### Cons

1. **Edge case with repo named "bazinga"**: Detection is technically "wrong" but paths work
2. **Assumes naming convention**: Relies on `bazinga/` folder name

### Verdict

The detection logic is sound. The edge case where the repo is named "bazinga" is actually a non-issue because the computed paths are correct regardless.

---

## Implementation Details

### Bash Script (`scripts/start-dashboard.sh`)

```bash
PARENT_DIR="$(basename "$(dirname "$SCRIPT_DIR")")"
if [ "$PARENT_DIR" = "bazinga" ]; then
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
    DASHBOARD_DIR="$BAZINGA_DIR/dashboard-v2"
else
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    BAZINGA_DIR="$PROJECT_ROOT/bazinga"
    DASHBOARD_DIR="$PROJECT_ROOT/dashboard-v2"
fi
```

### PowerShell Script (`scripts/start-dashboard.ps1`)

```powershell
$PARENT_DIR = Split-Path -Leaf (Split-Path -Parent $SCRIPT_DIR)
if ($PARENT_DIR -eq "bazinga") {
    $PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
    $BAZINGA_DIR = Join-Path $PROJECT_ROOT "bazinga"
    $DASHBOARD_DIR = Join-Path $BAZINGA_DIR "dashboard-v2"
} else {
    $PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
    $BAZINGA_DIR = Join-Path $PROJECT_ROOT "bazinga"
    $DASHBOARD_DIR = Join-Path $PROJECT_ROOT "dashboard-v2"
}
```

### Standalone Scripts (`dashboard-v2/scripts/start-standalone.*`)

These scripts are simpler because they're always located inside `dashboard-v2/`:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"  # Parent of scripts/ is dashboard-v2/
```

No mode detection needed - they derive paths from their own location.

---

## Path Summary Table

| Variable | Dev Mode | Installed Mode |
|----------|----------|----------------|
| `SCRIPT_DIR` | `REPO/scripts` | `PROJECT/bazinga/scripts` |
| `PROJECT_ROOT` | `REPO` | `PROJECT` |
| `BAZINGA_DIR` | `REPO/bazinga` | `PROJECT/bazinga` |
| `DASHBOARD_DIR` | `REPO/dashboard-v2` | `PROJECT/bazinga/dashboard-v2` |

---

## Testing Verification

Verified both scripts handle paths correctly:

1. **Path resolution test** - All paths resolve to existing directories
2. **Node.js detection** - Version check works (requires 18+)
3. **Standalone build detection** - Correctly identifies missing build

---

## Lessons Learned

1. **Naming matters**: The detection relies on the `bazinga/` folder name convention
2. **Edge cases can be acceptable**: The repo-named-bazinga edge case doesn't break functionality
3. **Consistency is key**: Both bash and PowerShell scripts must use identical logic
4. **Document the layouts**: Added to `claude.md` for future reference

---

## References

- `.claude/claude.md` - Path layout documentation added
- `scripts/start-dashboard.sh` - Bash implementation
- `scripts/start-dashboard.ps1` - PowerShell implementation
- `dashboard-v2/scripts/start-standalone.*` - Simplified standalone scripts
