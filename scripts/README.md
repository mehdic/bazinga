# Orchestration Scripts

> **Repository:** https://github.com/mehdic/orchestrix

This directory contains utility scripts for Orchestrix (Claude Code Multi-Agent Dev Team) orchestration.

## init-orchestration.sh

**Purpose:** Initialize the coordination environment for Orchestrix orchestration.

**Usage:**
```bash
bash .claude/scripts/init-orchestration.sh
```

**What it does:**
- Creates `orchestrix/` folder structure
- Initializes state files:
  - `pm_state.json` - Project Manager's persistent state
  - `group_status.json` - Per-group progress tracking
  - `orchestrator_state.json` - Orchestrator's state
- Creates message exchange files in `orchestrix/messages/`
- Initializes `docs/orchestration-log.md`
- Generates unique session IDs with timestamps
- Creates `.gitignore` to exclude state files from version control

**Features:**
- **Idempotent** - Safe to run multiple times, won't overwrite existing files
- **Zero-config** - No parameters needed, works out of the box
- **Clear output** - Shows what's being created vs what already exists

**When to run:**
- Automatically called by orchestrator at startup (Step 0)
- Can be run manually to reset orchestration state (delete `orchestrix/` first)
- Run in new projects to set up Claude Code Multi-Agent Dev Team orchestration

**Example output:**
```
🔄 Initializing Claude Code Multi-Agent Dev Team orchestration system...
📅 Session ID: session_20251106_122837
📁 Creating orchestrix/ folder structure...
📝 Creating pm_state.json...
📝 Creating group_status.json...
...
✅ Initialization complete!
```

**Notes:**
- State files contain temporary session data and should NOT be committed to git
- The `.gitignore` file ensures state files are excluded automatically
- Session IDs use format: `orchestrix_YYYYMMDD_HHMMSS` for easy tracking
