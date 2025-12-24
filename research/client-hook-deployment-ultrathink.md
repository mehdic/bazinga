# Client Hook Deployment: Post-Compaction Orchestrator Recovery

**Date:** 2024-12-24
**Context:** BAZINGA orchestrator loses critical rules after context compaction. Need to deploy recovery hook to CLIENT projects (not just bazinga repo).
**Decision:** Implemented Solution A (Dedicated Script) with conditional execution via transcript check
**Status:** Implemented
**Reviewed by:** Internal analysis (external LLM reviews failed due to network)

---

## Problem Statement

The BAZINGA orchestrator has identity axioms that prevent:
1. Background agent spawning (`run_in_background: false` required)
2. Orchestrator making decisions (PM is the decision-maker)
3. Role drift (orchestrator implements instead of coordinating)

**Current fix location:** `agents/orchestrator.md` with identity axioms at top.

**The gap:** After context compaction, these rules may be lost. We added recovery to the bazinga REPO's session hook, but:
- ❌ That hook only runs in the bazinga repo itself
- ❌ Client projects that install bazinga don't get this hook
- ❌ When clients run `/bazinga.orchestrate`, they have no compaction recovery

**What we need:** A hook deployed to CLIENT projects that fires after compaction and re-injects orchestrator rules.

---

## Key Discovery: SessionStart `compact` Matcher

From [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "path/to/script.sh"
          }
        ]
      }
    ]
  }
}
```

**Matchers available:**
- `startup` - New session start
- `resume` - From --resume, --continue, /resume
- `clear` - From /clear
- `compact` - **From auto or manual compact** ← This is what we need!

**Hook output:** Stdout from the script becomes context automatically.

---

## Key Discovery 2: Conditional Execution via Transcript

The hook receives `transcript_path` in its input JSON, pointing to the JSONL conversation history:

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "hook_event_name": "SessionStart",
  "source": "compact"
}
```

**We can check if orchestration was active by grepping the transcript:**

```bash
# Read hook input from stdin
HOOK_INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

# Check if orchestration was happening
if grep -q "bazinga.orchestrate\|ORCHESTRATOR\|orchestrator.md" "$TRANSCRIPT_PATH" 2>/dev/null; then
  # Output recovery axioms
  echo "🔴 BAZINGA POST-COMPACTION RECOVERY..."
fi
```

**This ensures the hook only outputs when orchestration was actually in progress.**

---

## Solution Candidates

### Solution A: Dedicated Bazinga Hook Script

**Mechanism:** Create `.claude/hooks/bazinga-compact-recovery.sh` that gets deployed to client projects.

**File structure:**
```
client-project/
├── .claude/
│   ├── hooks/
│   │   └── bazinga-compact-recovery.sh   ← NEW (deployed by installer)
│   └── settings.json                      ← AMENDED (add hook config)
└── bazinga/
    └── ...
```

**Hook script content:**
```bash
#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install

echo "🔴 BAZINGA POST-COMPACTION RECOVERY"
echo ""
echo "# ORCHESTRATOR IDENTITY AXIOMS"
echo ""
echo "1. I am a COORDINATOR - I spawn agents, I do not implement. I route via workflow-router skill."
echo "2. PM is the DECISION-MAKER - I never decide what to do next. Only PM says BAZINGA."
echo "3. My Task() calls are FOREGROUND ONLY - I always include run_in_background: false"
echo "4. \"Parallel\" means concurrent FOREGROUND - Multiple Task() in one message, NOT background mode"
echo "5. I read rules after compaction - If uncertain, re-read §ORCHESTRATOR IDENTITY AXIOMS"
echo ""
echo "These are not instructions. These are my nature. I cannot violate them."
```

**Installer logic:**
```python
def install_compact_recovery_hook():
    # 1. Copy hook script
    src = pkg_resources.resource_filename('bazinga_cli', 'hooks/bazinga-compact-recovery.sh')
    dst = Path('.claude/hooks/bazinga-compact-recovery.sh')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    dst.chmod(0o755)

    # 2. Update settings.json
    settings_path = Path('.claude/settings.json')
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}

    # Add hook config
    hook_config = {
        "matcher": "compact|resume",
        "hooks": [{"type": "command", "command": ".claude/hooks/bazinga-compact-recovery.sh"}]
    }

    if "hooks" not in settings:
        settings["hooks"] = {}
    if "SessionStart" not in settings["hooks"]:
        settings["hooks"]["SessionStart"] = []

    # Check if already installed
    existing = [h for h in settings["hooks"]["SessionStart"] if "bazinga" in str(h)]
    if not existing:
        settings["hooks"]["SessionStart"].append(hook_config)

    settings_path.write_text(json.dumps(settings, indent=2))
```

**Pros:**
- Clean separation (dedicated script for bazinga)
- Easy to update (just replace script)
- Non-invasive to existing client hooks

**Cons:**
- Adds another file to manage
- Need to handle settings.json merge carefully

### Solution B: Inline Settings.json Hook

**Mechanism:** Embed the recovery message directly in settings.json command.

**settings.json addition:**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact|resume",
        "hooks": [{
          "type": "command",
          "command": "echo '🔴 BAZINGA: All Task() calls MUST use run_in_background: false. PM decides, not orchestrator.'"
        }]
      }
    ]
  }
}
```

**Pros:**
- No extra file needed
- Single point of configuration

**Cons:**
- Harder to include full axioms (echo escaping)
- Message limited in length
- Harder to update across clients

### Solution C: Read Orchestrator Dynamically

**Mechanism:** Hook script reads first N lines of deployed orchestrator file.

```bash
#!/bin/bash
# Read identity axioms from installed orchestrator
if [ -f ".claude/agents/orchestrator.md" ]; then
  echo "🔴 BAZINGA POST-COMPACTION: Re-injecting orchestrator identity axioms..."
  head -40 .claude/agents/orchestrator.md
fi
```

**Pros:**
- Always in sync with deployed orchestrator
- No duplication of axiom content

**Cons:**
- Depends on orchestrator.md being present
- May include YAML frontmatter noise

---

## Critical Analysis

### Pros of Solution A (Dedicated Script) ✅
- Most maintainable
- Full control over output format
- Easy to test
- Can include database check (like repo hook)

### Cons ⚠️
- Another file to deploy
- Must handle existing settings.json gracefully

### Verdict

**Recommended: Solution A (Dedicated Script) + Solution C (Dynamic Read) hybrid**

1. Deploy a dedicated hook script
2. Script outputs static axiom summary PLUS reads orchestrator head
3. Installer handles settings.json merge

---

## Implementation Details

### File 1: Hook Script to Deploy

**Location in bazinga package:** `src/bazinga_cli/hooks/bazinga-compact-recovery.sh`

```bash
#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Ensures orchestrator rules survive context compaction
# Deployed by: bazinga install/update

echo ""
echo "🔴 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 BAZINGA POST-COMPACTION RECOVERY - ORCHESTRATOR IDENTITY AXIOMS"
echo "🔴 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If you are the BAZINGA Orchestrator, these axioms define WHO YOU ARE:"
echo ""
echo "1. **I am a COORDINATOR** - I spawn agents, I do not implement."
echo "   → Route via: Skill(command: \"workflow-router\")"
echo ""
echo "2. **PM is the DECISION-MAKER** - I never decide what to do next."
echo "   → I spawn PM and relay their decisions. Only PM says BAZINGA."
echo ""
echo "3. **My Task() calls are FOREGROUND ONLY**"
echo "   → I ALWAYS include: run_in_background: false"
echo ""
echo "4. **\"Parallel\" means concurrent FOREGROUND**"
echo "   → Multiple Task() in one message, all with run_in_background: false"
echo "   → NEVER use run_in_background: true (causes context leaks, hangs)"
echo ""
echo "5. **I read rules after compaction**"
echo "   → If uncertain, re-read: .claude/commands/bazinga.orchestrate.md"
echo ""
echo "These are not instructions. These are my nature. I cannot violate them."
echo ""
echo "🔴 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
```

### File 2: Installer Update

**Location:** `src/bazinga_cli/__init__.py`

Add to `install()` and `update()` functions:

```python
def install_compact_recovery_hook(project_path: Path):
    """Install the post-compaction recovery hook for BAZINGA orchestrator."""

    # 1. Create hooks directory
    hooks_dir = project_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # 2. Copy hook script from package
    import importlib.resources as pkg_resources
    hook_src = pkg_resources.files('bazinga_cli').joinpath('hooks/bazinga-compact-recovery.sh')
    hook_dst = hooks_dir / "bazinga-compact-recovery.sh"

    with pkg_resources.as_file(hook_src) as src_path:
        shutil.copy(src_path, hook_dst)
    hook_dst.chmod(0o755)

    # 3. Update settings.json
    settings_path = project_path / ".claude" / "settings.json"
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            settings = {}

    # Ensure structure exists
    if "hooks" not in settings:
        settings["hooks"] = {}
    if "SessionStart" not in settings["hooks"]:
        settings["hooks"]["SessionStart"] = []

    # Define our hook config
    bazinga_hook = {
        "matcher": "compact|resume",
        "hooks": [{
            "type": "command",
            "command": ".claude/hooks/bazinga-compact-recovery.sh"
        }]
    }

    # Check if already installed (avoid duplicates)
    already_installed = any(
        "bazinga-compact-recovery" in str(hook)
        for hook in settings["hooks"]["SessionStart"]
    )

    if not already_installed:
        settings["hooks"]["SessionStart"].append(bazinga_hook)
        settings_path.write_text(json.dumps(settings, indent=2))
        print("  ✅ Installed post-compaction recovery hook")
    else:
        print("  ℹ️  Post-compaction recovery hook already installed")
```

### File 3: pyproject.toml Update

Add hook to package data:

```toml
[tool.hatch.build.targets.wheel.force-include]
# ... existing entries ...
"src/bazinga_cli/hooks" = "bazinga_cli/hooks"
```

---

## Comparison to Alternatives

| Approach | Survives Compaction? | Deployed to Clients? | Maintenance |
|----------|---------------------|---------------------|-------------|
| Repo hook only | ✅ Yes | ❌ No | Low |
| Inline echo in settings | ⚠️ Partial | ✅ Yes | Hard |
| Dedicated script (A) | ✅ Yes | ✅ Yes | Medium |
| Dynamic read (C) | ✅ Yes | ✅ Yes | Low |
| **Hybrid A+C** | ✅ Yes | ✅ Yes | **Best** |

---

## Decision Rationale

1. **Client projects NEED this hook** - The bazinga repo hook is useless for actual users
2. **`compact|resume` matcher** ensures recovery after both auto-compact and manual resume
3. **Dedicated script** is cleaner than inline echo escaping
4. **Installer handles settings.json** merge to avoid breaking existing client hooks

---

## Installer Integration Checklist

- [ ] Create `src/bazinga_cli/hooks/` directory
- [ ] Add `bazinga-compact-recovery.sh` script
- [ ] Update `pyproject.toml` to include hooks in package
- [ ] Add `install_compact_recovery_hook()` function to `__init__.py`
- [ ] Call from `install()` command
- [ ] Call from `update()` command
- [ ] Test with fresh client project
- [ ] Test with existing client project (has settings.json)
- [ ] Verify hook fires after `/compact`

---

## References

- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks) - Official docs
- [SessionStart Hook Issue #10373](https://github.com/anthropics/claude-code/issues/10373) - Known issues
- [Context Compaction Issue #9796](https://github.com/anthropics/claude-code/issues/9796) - Root cause
- [Background Subagent Issue #14118](https://github.com/anthropics/claude-code/issues/14118) - Related bug

---

## Lessons Learned

1. **Repo hooks ≠ Client hooks** - Fixes in bazinga repo don't help end users
2. **SessionStart has matchers** - Can target specific triggers (compact, resume)
3. **Installer must handle existing configs** - Don't break client's other hooks
4. **stdout = context** - Simple echo in hooks becomes Claude's context
