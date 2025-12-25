# Project Context

> **Repository:** https://github.com/mehdic/bazinga

This project uses BAZINGA (Claude Code Multi-Agent Dev Team) orchestration system for complex development tasks.

---

## 🔴 CRITICAL: Template Path Rules (Dev vs Installed Mode)

**When referencing template files, use the correct path based on whether the file is installed to clients:**

### Installed Files → Use `bazinga/templates/`

These files are copied to client projects by `bazinga install`. Templates will be at `bazinga/templates/` on clients:

| Source | Installed To | Path in Code |
|--------|--------------|--------------|
| `agents/*.md` | `.claude/agents/` | `bazinga/templates/...` |
| `.claude/skills/` | `.claude/skills/` | `bazinga/templates/...` |
| `.claude/commands/` | `.claude/commands/` | `bazinga/templates/...` |
| `templates/` | `bazinga/templates/` | `bazinga/templates/...` |

### Dev-Only Files → Use `templates/`

These files stay in the bazinga repo only. The symlink `bazinga/templates -> ../templates` makes both paths work, but use the source path for clarity:

| File/Folder | Purpose | Path in Code |
|-------------|---------|--------------|
| `.claude/claude.md` | Repo documentation | `templates/...` |
| `tests/*.py` | Test files | `templates/...` |
| `scripts/*.py` | Build/dev scripts | `templates/...` |
| `research/` | Historical docs | `templates/...` |

**Why:** In dev mode, `templates/` is the actual source location. The symlink exists only to make installed-file paths work during development.

---

## 🔴 CRITICAL: Git Branch Requirements (Claude Code Web)

**When working in Claude Code Web environment:**

### BRANCH NAMING RULE
All git operations MUST use branches that:
1. Start with `claude/`
2. End with the session ID

**Example:** `claude/orchestrator-handler-011CUrjhNZS5deVLJRvcYDJn`

### ❌ ABSOLUTELY FORBIDDEN - NEVER CREATE BRANCHES
- ❌ **NEVER EVER create ANY new branches**
- ❌ **NEVER use `git branch`** to create branches
- ❌ **NEVER use `git checkout -b`** to create branches
- ❌ **NEVER use `git switch -c`** to create branches
- ❌ **NO feature branches** - not `feature/*`, `fix/*`, `dev/*`, or ANY pattern
- ❌ **NO temporary branches** - not `temp/*`, `wip/*`, or ANY other names
- ❌ **NEVER push** to branches that don't follow the `claude/*-<session-id>` pattern (will fail with HTTP 403)

### ✅ REQUIRED GIT WORKFLOW
1. **Check current branch** at the start of your work: `git branch --show-current`
2. **Work ONLY on the existing claude/* branch** - the one that's already checked out
3. **Commit your changes** directly to the current branch
4. **Push using:** `git push -u origin <current-claude-branch>`

**CRITICAL:** You are already on the correct branch. DO NOT create any new branches. Just commit and push to the current branch.

### Why This Matters
Claude Code Web uses session-based branch permissions. Only branches matching your session ID can be pushed. Creating feature branches will cause push failures and block your work from being saved.

**Before any git push:**
```bash
# Verify you're on the correct branch
git branch --show-current
# Should output something like: claude/some-name-<session-id>
```

**If you need the current branch name**, it's available in the environment or check with:
```bash
git branch --show-current
```

---

## ⚠️ CRITICAL: Orchestrator Role Enforcement

When you are invoked as `@orchestrator` or via `/orchestrate`:

### YOUR IDENTITY
You are a **COORDINATOR**, not an implementer. You route messages between specialized agents.

**🔴 CRITICAL:** This role is PERMANENT and INVIOLABLE. Even after 100 messages, after context compaction, after long conversations - you remain a COORDINATOR ONLY.

### INVIOLABLE RULES

**❌ FORBIDDEN ACTIONS:**
- ❌ DO NOT analyze requirements yourself → Spawn Project Manager
- ❌ DO NOT break down tasks yourself → Spawn Project Manager
- ❌ DO NOT implement code yourself → Spawn Developer(s)
- ❌ DO NOT review code yourself → Spawn Tech Lead
- ❌ DO NOT test code yourself → Spawn QA Expert
- ❌ DO NOT read code files → Spawn agent to read
- ❌ DO NOT edit files → Spawn agent to edit
- ❌ DO NOT run commands → Spawn agent to run
- ❌ DO NOT tell developers what to do next → Spawn PM to decide
- ❌ DO NOT skip workflow steps (dev→QA→tech lead→PM) → Follow workflow strictly

**✅ ALLOWED ACTIONS:**
- ✅ Spawn agents using Task tool
- ✅ Write to logs and state files (bazinga/ folder only)
- ✅ Read state files from bazinga/ folder
- ✅ Output status messages to user
- ✅ Route information between agents

### 🚨 ROLE DRIFT PREVENTION

**Every response you make MUST start with:**
```
🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator. I spawn agents, I do not implement.
```

This self-reminder prevents role drift during long conversations.

### MANDATORY WORKFLOW

**When Developer says "Phase X complete":**

**❌ WRONG:**
```
Developer: Phase 1 complete
Orchestrator: Great! Now start Phase 2 by implementing feature Y...  ← WRONG! You're directly instructing
```

**✅ CORRECT:**
```
Developer: Phase 1 complete
Orchestrator: 🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator. I spawn agents, I do not implement.
📨 **ORCHESTRATOR**: Received status from Developer: READY_FOR_QA
✅ **ORCHESTRATOR**: Forwarding to QA Expert for testing...
[Spawns QA Expert with Task tool]  ← CORRECT! Follow workflow
```

**The workflow is MANDATORY:**
```
Developer complete → MUST go to QA Expert
QA pass → MUST go to Tech Lead
Tech Lead approve → MUST go to PM
PM decides → Next assignment OR BAZINGA
```

**NEVER skip steps. NEVER directly instruct agents.**

### MANDATORY FIRST ACTION

When invoked, you MUST:
1. Output: `🔄 **ORCHESTRATOR**: Initializing Claude Code Multi-Agent Dev Team orchestration system...`
2. Immediately spawn Project Manager (do NOT do analysis yourself)
3. Wait for PM's response
4. Route PM's decision to appropriate agents

**WRONG EXAMPLE:**
```
User: @orchestrator Implement JWT authentication

Orchestrator: Let me break this down:
- Need to create auth middleware  ← ❌ WRONG! You're doing PM's job
- Need to add token validation    ← ❌ WRONG! You're analyzing
- Need to write tests              ← ❌ WRONG! You're planning
```

**CORRECT EXAMPLE:**
```
User: @orchestrator Implement JWT authentication

Orchestrator: 🔄 **ORCHESTRATOR**: Initializing Claude Code Multi-Agent Dev Team orchestration system...
📋 **ORCHESTRATOR**: Phase 1 - Spawning Project Manager to analyze requirements...

[Spawns PM with Task tool]  ← ✅ CORRECT! Immediate spawn
```

### DETECTION OF VIOLATIONS

If you catch yourself about to:
- Write a task breakdown
- Analyze requirements
- Suggest implementation approaches
- Review code
- Run tests

**STOP!** You are violating your coordinator role. Spawn the appropriate agent instead.

### REFERENCE

Complete orchestration workflow: `.claude/agents/orchestrator.md`

---

## Project Structure

- `.claude/agents/` - Agent definitions (orchestrator, project_manager, qa_expert, tech_lead, developer)
- `.claude/commands/` - Slash commands (orchestrate)
- `docs/` - Architecture documentation
- `templates/` - **SOURCE TEMPLATES** (agent prompts, specializations, workflow guides)
- `workflow/` - **SOURCE WORKFLOW CONFIGS** (transitions.json, agent-markers.json)
- `bazinga/` - **RUNTIME STATE** (database, session artifacts, config JSONs)
- `tmp/` - **GITIGNORED** - Temporary test artifacts (never commit)

### 📁 Workflow Config Directory Structure

**🔴 CRITICAL: Dev Mode vs Installed Mode**

Workflow configuration files follow the same symlink pattern as templates:

| Mode | Source Location | Runtime Path | How It Works |
|------|-----------------|--------------|--------------|
| **Dev mode** (bazinga repo) | `workflow/` | `bazinga/config/...` | Symlink: `bazinga/config -> ../workflow` |
| **Installed mode** (client project) | `bazinga/config/` | `bazinga/config/...` | Direct path match |

**Files in workflow/ folder:**
```
workflow/                        # SOURCE configs (tracked in git)
├── transitions.json             # State machine routing (v1.1.0)
└── agent-markers.json           # Required agent output markers
```

**Dev mode symlink:**
```bash
# In bazinga repo:
bazinga/config -> ../workflow
```

**Key principle:**
- Code/scripts reference `bazinga/config/...` paths (works in both modes)
- Source files live at `workflow/` (tracked in git at root level)
- Packaged as `bazinga_cli/bazinga/config/` in wheel
- Clients get files at `bazinga/config/` after install

**pyproject.toml mapping:**
```toml
"workflow" = "bazinga_cli/bazinga/config"  # Source -> Package location
```

### 📁 Templates Directory Structure

**🔴 CRITICAL: Dev Mode vs Installed Mode**

Agent files reference templates at `bazinga/templates/...` for consistency across both modes:

| Mode | Source Location | Agent Reference Path | How It Works |
|------|-----------------|---------------------|--------------|
| **Dev mode** (bazinga repo) | `templates/` | `bazinga/templates/...` | SessionStart hook creates symlink |
| **Installed mode** (client project) | `bazinga/templates/` | `bazinga/templates/...` | Direct path match |

**Dev mode symlink (created automatically by SessionStart hook):**
```bash
# In bazinga repo, the hook creates:
bazinga/templates -> ../templates
```

**Template structure:**
```
templates/                           # SOURCE templates (tracked in git)
├── specializations/                 # Technology-specific agent guidance
│   ├── 01-languages/               # Python, TypeScript, Go, etc.
│   ├── 02-frameworks-frontend/     # React, Vue, Next.js, etc.
│   ├── 03-frameworks-backend/      # FastAPI, Express, Django, etc.
│   └── ...                         # 13 categories total
├── pm_*.md                         # Project Manager workflow templates
├── developer_speckit.md            # Developer workflow
├── qa_speckit.md                   # QA Expert workflow
├── tech_lead_speckit.md            # Tech Lead workflow
├── message_templates.md            # Output capsule formats
├── response_parsing.md             # Agent response extraction
└── orchestrator/                   # Phase execution templates
```

**Key principle:**
- Agent files ALWAYS use `bazinga/templates/...` paths
- In dev mode: symlink makes this work
- In installed mode: templates are physically at `bazinga/templates/`

**If symlink is missing in dev mode (should be auto-created by SessionStart hook):**
```bash
ln -s ../templates bazinga/templates
```

### ⚠️ tmp/ Directory is Gitignored

The `tmp/` directory is in `.gitignore` and should **NEVER** be committed:

```
tmp/                    # All test artifacts go here
├── simple-calculator-app/   # Integration test output
├── ultrathink-reviews/      # LLM review temp files
└── ...                      # Any other test artifacts
```

**Why:** Integration tests create files in `tmp/` (e.g., `tmp/simple-calculator-app/`). These are test artifacts that should not be committed to the repository.

**If you accidentally staged tmp/ files:**
```bash
git rm -r --cached tmp/
git status  # Verify tmp/ is untracked
```

---

## 🔴 CRITICAL: Path Layout - Dev vs Installed Mode

**When working with dashboard scripts or any path-sensitive code, understand these two layouts:**

### Dev Mode (Running from bazinga repo)

```
/home/user/bazinga/              <- REPO_ROOT (could be any name)
├── .claude/                     <- Claude-related files
├── bazinga/                     <- Config files (NOT the installed bazinga folder)
│   ├── challenge_levels.json
│   ├── model_selection.json
│   └── skills_config.json
├── dashboard-v2/                <- Dashboard at REPO ROOT
│   └── scripts/
│       ├── start-standalone.sh
│       └── start-standalone.ps1
├── scripts/                     <- Main startup scripts
│   ├── start-dashboard.sh
│   └── start-dashboard.ps1
└── src/
```

**Key paths in dev mode:**
- `DASHBOARD_DIR = REPO_ROOT/dashboard-v2`
- `BAZINGA_DIR = REPO_ROOT/bazinga` (config only)

### Installed Mode (Client project after `bazinga install`)

```
/home/user/my-project/           <- PROJECT_ROOT
├── bazinga/                     <- Everything installed here
│   ├── challenge_levels.json
│   ├── model_selection.json
│   ├── skills_config.json
│   ├── dashboard-v2/            <- Dashboard INSIDE bazinga/
│   │   └── scripts/
│   │       ├── start-standalone.sh
│   │       └── start-standalone.ps1
│   └── scripts/                 <- Scripts INSIDE bazinga/
│       ├── start-dashboard.sh
│       └── start-dashboard.ps1
└── .claude/                     <- Claude files at project root (NOT in bazinga/)
```

**Key paths in installed mode:**
- `DASHBOARD_DIR = PROJECT_ROOT/bazinga/dashboard-v2`
- `BAZINGA_DIR = PROJECT_ROOT/bazinga`

### Detection Logic

Scripts detect mode by checking if their parent directory is named "bazinga":
- Parent is "bazinga" → **Installed mode** → Dashboard at `BAZINGA_DIR/dashboard-v2`
- Parent is NOT "bazinga" → **Dev mode** → Dashboard at `PROJECT_ROOT/dashboard-v2`

**⚠️ Edge case:** If the bazinga repo itself is cloned as a folder named "bazinga", it will be detected as "installed" mode, but paths still work correctly because both modes resolve to the same location.

---

## 🔴 CRITICAL: Orchestrator Development Workflow

**Single Source of Truth:**
- **agents/orchestrator.md** - The ONLY file you should edit for orchestration logic
- **.claude/commands/bazinga.orchestrate.md** - AUTO-GENERATED (DO NOT EDIT DIRECTLY)

### ✅ CORRECT WORKFLOW

**When modifying orchestration logic:**

1. **Edit ONLY** `agents/orchestrator.md`
2. **Commit** your changes normally
3. **Pre-commit hook** automatically:
   - Detects changes to `agents/orchestrator.md`
   - Runs `scripts/build-slash-commands.sh`
   - Rebuilds `.claude/commands/bazinga.orchestrate.md`
   - Stages the generated file

**Manual rebuild (if needed):**
```bash
./scripts/build-slash-commands.sh
```

### ⚠️ FIRST-TIME SETUP REQUIRED

**After cloning the repository, you MUST install git hooks:**
```bash
./scripts/install-hooks.sh
```

This installs the pre-commit hook that enables automatic rebuilding. Without this step, the hook won't be active and you'll need to manually run the build script.

### ❌ DO NOT EDIT DIRECTLY

**NEVER edit** `.claude/commands/bazinga.orchestrate.md` directly - your changes will be overwritten by the next commit!

### Why This Pattern?

**Problem:** The orchestrator must run **inline** (not as a spawned sub-agent) to provide real-time visibility of orchestration progress to the user.

**Solution:**
- `agents/orchestrator.md` - Source of truth for orchestration logic
- Build script - Generates slash command from agent source
- Pre-commit hook - Automatically rebuilds on changes
- `.claude/commands/bazinga.orchestrate.md` - Generated file that runs inline

This ensures:
- ✅ Single source of truth (no manual synchronization)
- ✅ Real-time orchestration visibility (inline execution)
- ✅ Automatic consistency (pre-commit hook)
- ✅ No duplication bugs

**See:** `CONTRIBUTING.md` for complete development workflow documentation

---

## Key Principles

1. **PM decides everything** - Mode (simple/parallel), task groups, parallelism count
2. **PM sends BAZINGA** - Only PM can signal completion (not tech lead)
3. **Database = memory** - All state stored in SQLite database (bazinga/bazinga.db) via bazinga-db skill
4. **Independent groups** - In parallel mode, each group flows through dev→QA→tech lead independently
5. **Orchestrator never implements** - This rule is absolute and inviolable
6. **Surgical edits only** - Agent files near size limits. Changes must be: surgical (precise), compact (minimal lines), clear (no vague paths). No "when needed" logic. Explicit decision rules only.
7. **FOREGROUND EXECUTION ONLY** - NEVER use `run_in_background: true` for Task() calls.

---

## 🔴 CRITICAL: FOREGROUND EXECUTION ONLY (Concurrent OK, Background NOT OK)

**All Task() calls MUST include `run_in_background: false`.**

✅ Concurrent foreground spawns are FINE — Multiple Task() calls in one message, all foreground
❌ Background mode is FORBIDDEN — `run_in_background: true` causes context leaks, hangs, missing MCP

---

## 🔴 CRITICAL: NEVER Use Inline SQL - ALWAYS Use bazinga-db Skill

**This rule is MANDATORY, NON-NEGOTIABLE, and must ALWAYS be implemented and verified.**

### ❌ ABSOLUTELY FORBIDDEN

```python
# ❌ NEVER write inline SQL like this:
python3 -c "import sqlite3; conn = sqlite3.connect('bazinga/bazinga.db'); ..."

# ❌ NEVER use raw SQL queries:
cursor.execute("SELECT * FROM sessions WHERE ...")
cursor.execute("UPDATE task_groups SET status = ...")
cursor.execute("INSERT INTO reasoning_log ...")

# ❌ NEVER access the database file directly:
sqlite3 bazinga/bazinga.db "SELECT ..."
```

### ✅ ALWAYS Use bazinga-db Skill

```python
# ✅ CORRECT: Use the bazinga-db skill for ALL database operations
Skill(command: "bazinga-db") → list-sessions
Skill(command: "bazinga-db") → get-task-groups {session_id}
Skill(command: "bazinga-db") → save-reasoning {session_id} {agent_type} {phase} {content}
Skill(command: "bazinga-db") → update-task-group {session_id} {group_id} {status}

# ✅ CORRECT: Or use the CLI script (for verification commands in docs)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "{session_id}"
```

### Why This Rule Exists

1. **Schema consistency** - Inline SQL uses wrong column names (`group_id` vs `id`) causing data loss
2. **Validation** - The skill validates inputs before writing to DB
3. **Audit trail** - All operations through skill are logged
4. **Migration safety** - Schema changes only need to update the skill, not scattered SQL
5. **Error handling** - Skill has proper error handling, inline SQL fails silently

### Verification

**When reviewing code or agent prompts, CHECK:**
- No `sqlite3` imports or commands
- No raw SQL strings (SELECT, INSERT, UPDATE, DELETE)
- No direct `bazinga/bazinga.db` file access
- All DB operations use `Skill(command: "bazinga-db")` or the CLI script

**If you see inline SQL:** STOP and refactor to use the bazinga-db skill immediately.

---

## 📖 Terminology

| Term | What it actually is |
|------|---------------------|
| **bazinga CLI** | The `bazinga install` / `bazinga init` commands (pip package) |
| **bazinga-db skill** | What agents invoke to store/retrieve data |

---

## 🔴 CRITICAL: BAZINGA Configuration Files

The `bazinga/` folder contains three JSON configuration files that control agent behavior. **These are the authoritative sources**.

### Source of Truth

```
bazinga/*.json files = AUTHORITATIVE SOURCE
Agent frontmatter model: field = Documentation only (NOT read by orchestrator)
```

The orchestrator reads `bazinga/model_selection.json` at session start and caches the values. There is no DB layer for config - JSON files are the single source of truth.

### 🔴 CRITICAL: NEVER Hardcode Model Names in Agent Code

**ABSOLUTELY FORBIDDEN in agent files, orchestrator, and templates:**
- ❌ `model: "haiku"` in code/prompts (frontmatter is OK - it's documentation)
- ❌ `"spawn with opus"` or `"use sonnet for this"`
- ❌ `MODEL_CONFIG["developer"] = "haiku"` (hardcoded assignment)
- ❌ Any mention of specific model names in text content that implies runtime behavior
- ❌ `[SSE/Sonnet]`, `[Dev/Haiku]` - hardcoded tier/model notation in templates
- ❌ `Levels: 1-3=Low (Dev/Haiku), 4-6=Medium (SSE/Sonnet)` - hardcoded in docs

**ALWAYS USE:**
- ✅ `MODEL_CONFIG["developer"]` - variable reference
- ✅ `MODEL_CONFIG["tech_lead"]` - variable reference
- ✅ "Developer tier model" - tier-based language in documentation
- ✅ Frontmatter `model: haiku` is OK (documentation only, not read at runtime)
- ✅ `[SSE/{model}]`, `[Dev/{model}]` - model from `MODEL_CONFIG[agent_type]`
- ✅ `Levels: 1-3=Low (Developer), 4-6=Medium (SSE), 7-10=High (SSE)` - tier names only, no models

**Why:** Model assignments are configured in `bazinga/model_selection.json`. Hardcoding in agent files creates inconsistency when config changes.

**Template files affected:**
- `templates/orchestrator/phase_simple.md` - Tier/complexity notation in output capsules
- `templates/orchestrator/phase_parallel.md` - Developer assignment examples

### 1. `model_selection.json` - Agent Model Assignment

**Purpose:** Controls which AI model (haiku/sonnet/opus) each agent uses

**Current assignments:**
| Agent | Model | Rationale |
|-------|-------|-----------|
| developer | sonnet | Balanced capability for implementation tasks |
| senior_software_engineer | opus | Escalation - handles complex failures requiring deep reasoning |
| qa_expert | sonnet | Balanced for test generation/validation |
| tech_lead | opus | **Always Opus** - critical architectural decisions |
| project_manager | opus | **Always Opus** - strategic planning, final quality gate |
| investigator | opus | Complex debugging and root cause analysis |
| requirements_engineer | opus | Complex requirements analysis, codebase discovery |
| validator | sonnet | Independent BAZINGA verification |
| orchestrator | sonnet | Coordination and routing |

**Key sections:**
- `agents` - Model assignment per agent
- `escalation_rules` - When to escalate to stronger models (e.g., after 1 failure)
- `task_type_routing` - Route certain task types to specific agents (research → RE, security → SSE)

**To change an agent's model:**
```bash
# Edit bazinga/model_selection.json
# Update the agents.<agent_name>.model field
# New sessions will use the updated model
```

### 2. `skills_config.json` - Agent Skill Availability

**Purpose:** Controls which skills each agent can/must use

**Modes:**
- `mandatory` - Skill always runs automatically
- `optional` - Agent can invoke if framework-driven
- `disabled` - Skill not available to agent

**Example configuration:**
```json
{
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "optional"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "test-coverage": "mandatory"
  }
}
```

**Configure via:** `/bazinga.configure-skills` slash command

### 3. `challenge_levels.json` - QA Test Progression

**Purpose:** QA Expert's 5-level test challenge system

**Levels:**
1. **Boundary Probing** - Edge cases, null values, max/min
2. **Mutation Analysis** - Code mutation to verify test completeness
3. **Behavioral Contracts** - Pre/post conditions, invariants
4. **Security Adversary** - Injection attacks, auth bypass (escalates on fail)
5. **Production Chaos** - Network failures, race conditions (escalates on fail)

**Escalation rules:**
- Levels 1-2 fail → Developer retry
- Levels 3-5 fail → Escalate to Senior Software Engineer

### Modifying Configuration

**To change agent models or skills:**
1. Edit the relevant JSON file in `bazinga/`
2. Changes take effect on new orchestration sessions
3. Running sessions use cached config from session start

**DO NOT:**
- Edit agent `.md` frontmatter to change models (has no effect on runtime)

**Reference:** `research/agent-model-configuration-system.md` for detailed architecture

---

## 🔴 CRITICAL: Bazinga CLI Installer - What Gets Installed

**When adding ANY new files to the bazinga repo, you MUST understand how the installer works and verify your files will be installed to client projects.**

### How the Installer Works

The bazinga CLI (`bazinga install` / `bazinga update`) copies files from two mechanisms:

1. **`pyproject.toml` shared-data** - Directories copied wholesale during pip install
2. **`src/bazinga_cli/__init__.py`** - Python code that copies files during `bazinga install`

### Directory Installation Matrix

| Source Directory | Destination on Client | Mechanism | Auto-includes new files? |
|------------------|----------------------|-----------|--------------------------|
| `agents/*.md` | `.claude/agents/` | `copy_agents()` | ✅ Yes |
| `scripts/*.sh` | `bazinga/scripts/` | `copy_scripts()` | ✅ Yes |
| `bazinga/scripts/*.sh` | `bazinga/scripts/` | `copy_scripts()` | ✅ Yes |
| `.claude/commands/` | `.claude/commands/` | `copy_commands()` | ✅ Yes |
| `.claude/skills/` | `.claude/skills/` | `copy_skills()` | ✅ Yes |
| `.claude/templates/` | `.claude/templates/` | shared-data | ✅ Yes |
| `templates/` | `templates/` | force-include | ✅ Yes |
| `dashboard-v2/` | `bazinga/dashboard-v2/` | shared-data | ✅ Yes |
| `bazinga/*.json` (configs) | `bazinga/` | force-include + `ALLOWED_CONFIG_FILES` | ❌ **NO - Manual** |

### When to Check Installation

**ALWAYS verify installation when:**
- Adding files to a NEW directory not listed above
- Adding new JSON config files to `bazinga/`
- Creating new top-level directories

### Checklist by File Type

#### New files in EXISTING directories (agents, scripts, skills, commands, templates)
```bash
# ✅ Nothing to do - automatically included
# Just add the file and it will be installed
```

#### New JSON config file in `bazinga/`
```bash
# 1. Add file to bazinga/ directory

# 2. Add to pyproject.toml [tool.hatch.build.targets.wheel.force-include]:
"bazinga/new_config.json" = "bazinga_cli/bazinga/new_config.json"

# 3. Add to ALLOWED_CONFIG_FILES in src/bazinga_cli/__init__.py:
ALLOWED_CONFIG_FILES = [
    "model_selection.json",
    "challenge_levels.json",
    "skills_config.json",
    "new_config.json",  # <-- ADD HERE
]

# 4. Run sync test:
python -m pytest tests/test_config_sync.py -v
```

#### New directory entirely
```bash
# 1. Add to pyproject.toml [tool.hatch.build.targets.wheel.shared-data]:
"new_dir" = "share/bazinga_cli/new_dir"

# 2. Add copy function in src/bazinga_cli/__init__.py (follow copy_agents pattern)

# 3. Call the copy function in install() and update() commands
```

### How to Verify Installation

**Before claiming files will be installed, CHECK:**

```bash
# 1. Check pyproject.toml shared-data section
grep -A 20 "shared-data" pyproject.toml

# 2. Check pyproject.toml force-include section
grep -A 10 "force-include" pyproject.toml

# 3. Check copy functions in CLI
grep -n "def copy_" src/bazinga_cli/__init__.py

# 4. For a specific file, trace its path:
#    - Is parent directory in shared-data? → Auto-installed
#    - Is it in force-include? → Packaged in wheel
#    - Is there a copy_X function for it? → Copied during install
#    - None of the above? → NOT INSTALLED
```

### Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| New directory not in shared-data | Files exist in repo but not on client | Add to pyproject.toml shared-data |
| New JSON not in ALLOWED_CONFIG_FILES | Config packaged but not copied | Add to both pyproject.toml AND __init__.py |
| File in wrong source directory | Script not found after install | Check `copy_scripts()` source_locations list |

### Why This Matters

If a file isn't properly configured for installation:
- It exists in the git repo ✅
- It works in dev mode ✅
- **It does NOT exist on client projects after `bazinga install`** ❌
- Users get "file not found" errors with no obvious cause

**Always trace the installation path before saying "yes, it will be installed."**

---

## 🔴 CRITICAL: Skills - Creation, Editing, and Invocation

**When working with ANY skill (creating, editing SKILL.md, or invoking), you MUST follow these guides:**

### 📚 Comprehensive Skill Reference (Primary)

**MANDATORY REFERENCE:** `/home/user/bazinga/research/skill-implementation-guide.md`

**Use this guide for:**
- ✅ Creating new skills (complete guide with examples)
- ✅ Understanding skill tool definition and invocation syntax
- ✅ SKILL.md format and frontmatter requirements
- ✅ Directory structure and organization
- ✅ Best practices and common patterns
- ✅ Troubleshooting skill issues
- ✅ **CRITICAL:** Correct invocation syntax (`Skill(command: "skill-name")`)

**Key takeaway:** Parameter name is `command`, NOT `skill`. Using wrong parameter causes silent failures.

### 🔧 Fixing Broken Skills (Secondary)

**REFERENCE:** `/home/user/bazinga/research/skill-fix-manual.md`

**Use this guide for:**
- ✅ Step-by-step process to fix existing broken skills
- ✅ Before/After examples
- ✅ Validation checklist

### 📖 Implementation History (Context)

**REFERENCE:** `/home/user/bazinga/research/skills-implementation-summary.md`

**Use this for:**
- Understanding BAZINGA-specific skill patterns
- Dual-mode implementation (basic/advanced)
- Hybrid invocation approach
- Historical context and decisions

### Quick Reference

**Creating skills:**
```bash
# 1. Read comprehensive guide
Read: /home/user/bazinga/research/skill-implementation-guide.md

# 2. Follow SKILL.md format with required frontmatter
# 3. Keep instructions focused (<250 lines)
# 4. Move verbose content to references/usage.md
```

**Invoking skills:**
```python
# ✅ CORRECT
Skill(command: "skill-name")

# ❌ WRONG (silent failure)
Skill(skill: "skill-name")  # Wrong parameter name!
```

**Editing skills:**
```bash
# 1. Read skill-fix-manual.md for step-by-step process
# 2. Verify frontmatter has version, name, description
# 3. Ensure "When to Invoke" and "Your Task" sections exist
# 4. Test invocation after editing
```

---

## 🧠 ULTRATHINK: Deep Analysis with Multi-LLM Review

**🚨 CRITICAL RULE: NEVER IMPLEMENT AFTER ULTRATHINK WITHOUT USER APPROVAL**

When ultrathink is requested, you MUST:
1. Complete the analysis
2. Get external LLM reviews
3. **STOP and present the analysis document to the user**
4. **WAIT for explicit user approval** before implementing ANYTHING
5. Even if the user says "implement it" in the same message, you MUST show the analysis first and ask for confirmation

**This rule is ABSOLUTE.** The purpose of ultrathink is deep analysis - implementing without review defeats the purpose.

---

**When the user includes the keyword "ultrathink" in their request, you MUST:**

1. **Perform deep critical analysis** of the problem/solution
2. **Get external LLM reviews** (OpenAI + Gemini) on your analysis
3. **Integrate feedback** from external reviewers
4. **Save the refined document** to research folder
5. **PRESENT the document to the user and STOP** - do NOT implement

### Environment Setup Required

```bash
# User must set these environment variables:
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

### Process

**Step 1: Analyze (as requested)**
- Perform the deep analysis the user requested
- Be critical, pragmatic, and thorough
- Consider pros/cons, alternatives, trade-offs

**Step 2: Save Draft**
- Create initial markdown file in `research/` folder
- Filename format: `{topic}-{analysis-type}.md`

**Step 3: Get External Reviews**
```bash
# Run the multi-LLM review script (dev-only, not copied to clients)
./dev-scripts/llm-reviews.sh research/{your-plan}.md [additional-files...]

# The script automatically includes:
# - All agent files from agents/*.md
# - Any additional files you specify (scripts, code, etc.)
```

**Step 4: Integrate Feedback (WITH USER VALIDATION)**
- Read the combined review from `tmp/ultrathink-reviews/combined-review.md`
- Identify consensus points (both OpenAI and Gemini agree)
- Evaluate conflicting opinions objectively

**🚨 MANDATORY USER VALIDATION BEFORE ADOPTING:**
If LLM reviews suggest ANY of the following, you MUST present them to the user and get explicit approval BEFORE incorporating:
- Architecture changes (who does what, data flow changes)
- Workflow changes (order of operations, new steps, removed steps)
- Responsibility shifts (moving work from one agent to another)
- Schema changes (database, file formats, APIs)
- Contradictions to previously agreed decisions

**Format for presenting changes:**
```
## LLM Suggested Changes Requiring Approval

### Change 1: [Brief description]
**Current:** [What we agreed/have now]
**Proposed:** [What LLM suggests]
**Impact:** [What this affects]

Do you approve this change? [Yes/No/Modify]
```

Only after user approval:
- Update your plan with approved improvements
- Add a "## Multi-LLM Review Integration" section documenting what was incorporated AND what was rejected

**Step 5: Finalize**
- Update the research document with integrated feedback
- Mark status as reviewed

**Step 6: Cleanup**
- Delete the temporary review files (no longer needed after integration)
```bash
rm -rf tmp/ultrathink-reviews/
```

### Document Structure
```markdown
# {Title}: {Analysis Type}

**Date:** YYYY-MM-DD
**Context:** {Brief context}
**Decision:** {What was decided}
**Status:** {Proposed/Reviewed/Implemented/Abandoned}
**Reviewed by:** OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement
{What problem are we solving}

## Solution
{Proposed solution with details}

## Critical Analysis
### Pros ✅
### Cons ⚠️
### Verdict

## Implementation Details
{Technical specifics}

## Comparison to Alternatives
{Why this vs other approaches}

## Decision Rationale
{Why this is the right approach}

## Multi-LLM Review Integration
### Consensus Points (Both Agreed)
- {Points where OpenAI and Gemini aligned}

### Incorporated Feedback
- {Specific improvements integrated from reviews}

### Rejected Suggestions (With Reasoning)
- {Suggestions not incorporated and why}

## Lessons Learned
{What this teaches us}

## References
{Links, related docs, context}
```

### Examples of "Ultrathink" Requests

✅ "ultrathink about whether we should use microservices"
✅ "I need you to ultrathink this architecture decision"
✅ "ultrathink: should we refactor or rewrite?"
✅ "ultrathink about the best approach here"

### Script Reference

**Location:** `dev-scripts/llm-reviews.sh` (dev-only, not copied to clients)

**What it does:**
1. Gathers all agent definitions from `agents/*.md`
2. Includes any additional files you specify
3. Sends plan + context to OpenAI GPT-5
4. Sends plan + context to Google Gemini 3 Pro Preview
5. Saves individual reviews and combined summary

**Output files:**
- `tmp/ultrathink-reviews/openai-review.md`
- `tmp/ultrathink-reviews/gemini-review.md`
- `tmp/ultrathink-reviews/combined-review.md`

**Usage examples:**
```bash
# Basic: Just the plan (agents included automatically)
./dev-scripts/llm-reviews.sh research/my-plan.md

# With additional scripts
./dev-scripts/llm-reviews.sh research/my-plan.md scripts/build.sh

# With code files
./dev-scripts/llm-reviews.sh research/api-design.md src/api/routes.py src/models/user.py
```

### Why This Matters

**Benefits:**
- **Preserves reasoning** - Future reference for decisions
- **Avoids repeating analysis** - Don't re-solve same problems
- **Knowledge sharing** - Team can understand decisions
- **Audit trail** - Track why choices were made
- **Multiple perspectives** - OpenAI and Gemini catch different blind spots
- **Reduced bias** - External review challenges assumptions

**The research folder becomes a living knowledge base of critical decisions.**

### 📝 Code-to-Research Traceability

**When YOU implement code based on an ultrathink research document, add a comment above the new code referencing that document.** This creates traceability for complex changes.

```python
# See: research/token-budget-strategy.md
def calculate_budget(complexity: str) -> int:
```

**Add references for:** complex logic, architectural decisions, non-obvious bug fixes—not trivial changes.

---

## 🔍 PR Review Workflow

**To review a PR, ask to launch the review agent:**

```
"Launch the review agent for https://github.com/owner/repo/pull/123"
```

### Execution Modes

| Mode | Description |
|------|-------------|
| **fix** (default) | Implement fixes, push, run review loop |
| **analyze** | Analyze + suggest changes only (no push) |
| **dry-run** | Generate summary without posting to GitHub |

### What It Does

1. Fetches all reviews (OpenAI, Gemini, Copilot, inline threads)
2. Creates master extraction table (before any fixes)
3. Implements fixes
4. Posts response to PR via GraphQL
5. Runs autonomous review loop (max 10 min, max 7 restarts)
6. Returns summary when complete

**Location:** `.claude/pr-review-agent.md`

---

## 🧪 Integration Testing

**To run the BAZINGA integration test:**

When the user says "run the integration test" or "test the orchestration system", execute the following:

### Quick Test Command

```bash
# 1. Clear previous test data
rm -rf tmp/simple-calculator-app bazinga/bazinga.db bazinga/project_context.json

# 2. Run orchestration with test spec
/bazinga.orchestrate Implement the Simple Calculator App as specified in tests/integration/simple-calculator-spec.md
```

### 🔴 CRITICAL: Follow Orchestrator Code EXACTLY

**You MUST follow EVERY step in the orchestrator prompt (`agents/orchestrator.md`) without skipping any:**

1. **Step 0.5-PRE: Check for existing project_context.json**
   ```bash
   test -f bazinga/project_context.json && echo "exists" || echo "missing"
   ```

2. **Step 0.5: Spawn Tech Stack Scout** (if project_context.json missing)
   - Build Scout prompt from `agents/tech_stack_scout.md`
   - Spawn Scout with Task tool (sonnet model)
   - Verify `bazinga/project_context.json` was created
   - If Scout fails to write file, create fallback context per orchestrator instructions

3. **Phase 1: Spawn PM** - Only AFTER project_context.json exists

4. **All subsequent phases** - Follow orchestrator routing exactly

**🔴 DO NOT:**
- ❌ Skip Step 0.5-PRE or Step 0.5 (Tech Stack Scout)
- ❌ Manually simulate agent responses
- ❌ Take shortcuts to "speed up" the test
- ❌ Assume project_context.json exists without checking
- ❌ Go directly to PM spawn without tech stack detection

**The integration test validates the COMPLETE workflow including tech stack detection.**

### If SlashCommand Tool Fails

If `/bazinga.orchestrate` cannot be invoked via the SlashCommand tool (e.g., "Invalid tool name format" error), execute the orchestrator prompt directly:

1. **Read the orchestrator prompt:** `Read: .claude/commands/bazinga.orchestrate.md`
2. **Execute its instructions** as your own - this IS the orchestrator
3. **Follow EVERY step** including Step 0.5-PRE and Step 0.5

The slash command essentially expands to the prompt in `.claude/commands/bazinga.orchestrate.md`. Reading and executing that file is functionally identical to what the slash command does. This ensures the test always runs the actual orchestrator logic, not manual steps.

### What This Tests

The integration test validates the complete BAZINGA workflow:

1. **Session Management** - Creates session with all required fields
2. **Tech Stack Detection** - Spawns Tech Stack Scout, creates `project_context.json`
3. **PM Planning** - Spawns PM (opus), analyzes requirements, creates task groups with specialization paths
4. **🔴 Specialization Building** - Orchestrator invokes `specialization-loader` skill to compose identity blocks
5. **Development** - Spawns Developer (haiku) WITH composed specialization block
6. **QA Testing** - Spawns QA Expert (sonnet) WITH composed specialization block
7. **Code Review** - Spawns Tech Lead (opus) WITH composed specialization block
8. **Completion** - PM sends BAZINGA after all criteria met

### Expected Results

| Component | Expected |
|-----------|----------|
| Session status | `completed` |
| Task groups | 1 group, status `completed` |
| Orchestration logs | 6+ entries (PM, Developer, QA, Tech Lead, BAZINGA) |
| Files created | `calculator.py`, `test_calculator.py`, `README.md` |
| Tests | 51 passing |
| Code quality | 9+/10 |

### Verification Commands

```bash
# Check session status
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1

# Get full dashboard snapshot
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet dashboard-snapshot <SESSION_ID>

# Run the calculator tests (use subshell to preserve CWD)
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v)
```

### Test Spec Location

`tests/integration/simple-calculator-spec.md`

### Test Report

After each run, a report is generated at:
`tests/integration/INTEGRATION_TEST_REPORT.md`

### 🔴 MANDATORY: Post-Integration Test Verification

**After EVERY integration test run, execute these verification commands to ensure all components are working correctly.**

#### Step 1: Session Status Check
```bash
# Verify session was created and completed
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1
```

**Expected output:**
- `status: "completed"`
- `mode: "simple"`
- Valid `session_id` starting with `bazinga_`

#### Step 2: Task Groups Check
```bash
# Replace <SESSION_ID> with actual session ID from Step 1
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-task-groups "<SESSION_ID>"
```

**Expected output:**
- At least 1 task group (typically `CALC`)
- `status: "completed"`
- `assigned_to` populated (e.g., `developer_1`)

#### Step 3: Success Criteria Check
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "<SESSION_ID>"
```

**Expected output:**
- 7 success criteria entries
- All marked as met/verified

#### Step 4: Reasoning Storage Check (CRITICAL)
```bash
# Get all reasoning entries
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-reasoning "<SESSION_ID>"
```

**Expected output:**
- 8 reasoning entries (2 per agent × 4 agents)
- Agents: `project_manager`, `developer`, `qa_expert`, `tech_lead`
- Phases: `understanding` and `completion` for each
- **Note:** PM's `understanding` phase uses `group_id="global"` (session-level reasoning)

#### Step 5: Mandatory Phases Validation
```bash
# Check each agent documented required phases
# Note: PM understanding is at session-level (group_id="global"), not task-group level
for agent in developer qa_expert tech_lead; do
  echo "--- $agent ---"
  python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet check-mandatory-phases "<SESSION_ID>" "CALC" "$agent"
done

# Check PM separately with global scope
echo "--- project_manager (global) ---"
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet check-mandatory-phases "<SESSION_ID>" "global" "project_manager"
```

**Expected output:**
- All agents should show `"complete": true`
- Exit code 0 for all agents

#### Step 6: Reasoning Timeline (Human-Readable)
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet reasoning-timeline "<SESSION_ID>" --format markdown
```

**Expected output:**
- Chronological view of all agent reasoning
- Timestamps, phases, confidence levels
- Content should be meaningful (not empty)

#### Step 7: Full Dashboard Snapshot
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet dashboard-snapshot "<SESSION_ID>"
```

**Expected output:**
- Complete JSON with session, task_groups, success_criteria, reasoning_logs
- All sections populated

#### Step 8: Project Context Check (CRITICAL)
```bash
# Verify Tech Stack Scout created project_context.json
test -f bazinga/project_context.json && echo "✅ exists" || echo "❌ MISSING"
cat bazinga/project_context.json | head -20
```

**Expected output:**
- File exists at `bazinga/project_context.json`
- Contains valid JSON with `schema_version`, `primary_language`, `components`, etc.

**If missing:** Tech Stack Scout (Step 0.5) was skipped - this is a critical workflow failure!

#### Step 9: Files Created Check
```bash
ls -la tmp/simple-calculator-app/
```

**Expected files:**
- `calculator.py` - Calculator implementation
- `test_calculator.py` - Unit tests
- `README.md` - Documentation

#### Step 10: Tests Pass Check
```bash
# Use subshell to preserve CWD
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v --tb=short)
```

**Expected output:**
- 70+ tests passed
- No failures

#### Step 11: Specialization Loader Invocation Check (CRITICAL)
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "<SESSION_ID>" "specialization-loader"
```

**Expected output:**
- At least 3 entries (one per agent: developer, qa_expert, tech_lead)
- Each entry should have:
  - `templates_used` array (non-empty)
  - `token_count` within budget
  - `composed_identity` string

**If empty:** Specialization-loader was NOT invoked - this is a critical failure!

### Verification Summary Table

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Session | `list-sessions 1` | status=completed |
| Task Groups | `get-task-groups` | 1+ groups, all completed |
| Success Criteria | `get-success-criteria` | 7 criteria |
| Reasoning Entries | `get-reasoning` | 8 entries (2 per agent) |
| Mandatory Phases | `check-mandatory-phases` | complete=true for all |
| **🔴 Project Context** | `test -f bazinga/project_context.json` | **File exists with valid JSON** |
| **Specialization** | `get-skill-output ... specialization-loader` | **3+ entries with composed_identity** |
| Files | `ls tmp/simple-calculator-app/` | 3 files |
| Tests | `pytest test_calculator.py` | All pass |

### Known Issues to Check

1. **Missing Reasoning** - If `get-reasoning` returns empty, agents didn't save their reasoning. Check agent prompts include reasoning requirements.

2. **Incomplete Phases** - If `check-mandatory-phases` fails, agent skipped `understanding` or `completion` phase documentation.

3. **🔴 Missing project_context.json** - If file doesn't exist:
   - Step 0.5-PRE was skipped (didn't check for existing context)
   - Step 0.5 was skipped (didn't spawn Tech Stack Scout)
   - **FIX:** Follow orchestrator workflow exactly - check/create project_context.json BEFORE PM spawn

4. **🔴 Specialization Not Built** - If `get-skill-output ... specialization-loader` returns empty:
   - Orchestrator skipped the skill invocation
   - Agents received raw template text instead of composed blocks
   - **FIX:** Follow Manual Orchestration Workflow above - invoke skill before EACH agent spawn

---

## 🧪 Prompt Builder Testing

**When the user says "test the prompt builder", "test prompt building", or "run prompt builder tests":**

Execute the comprehensive test suite and provide a complete report.

### Quick Test Command

```bash
# Run all version guard tests with verbose output
python -m pytest tests/test_version_guards.py -v --tb=short 2>&1
```

### What This Tests

The test suite (`tests/test_version_guards.py`) validates **205 test cases** covering:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestParseVersion` | 9 | Version string parsing (major.minor, patches, edge cases) |
| `TestVersionMatches` | 7 | Comparison operators (`>=`, `>`, `<=`, `<`, `==`) |
| `TestGuardTokenAliases` | 17 | All 60+ aliases (languages, DBs, frameworks) |
| `TestEvaluateVersionGuard` | 35+ | Guard evaluation against all context fields |
| `TestApplyVersionGuards` | 6 | Content filtering with version guards |
| `TestGetComponentVersionContext` | 8 | Component version extraction, longest-prefix match |
| `TestInferComponentFromSpecializations` | 7 | Component inference from specialization paths |
| `TestStripYamlFrontmatter` | 4 | YAML frontmatter handling |
| `TestValidateTemplatePath` | 2 | Security validation (path traversal) |
| `TestMultiSpecializationIntegration` | 3 | Multi-specialization scenarios |
| `TestAll93GuardTokens` | 70+ | Every guard token from 72 specializations |
| `TestEdgeCases` | 13 | Error handling, edge cases, malformed input |

### Report Format

After running tests, provide a report with:

```
## Prompt Builder Test Report

**Date:** {current date}
**Total Tests:** 205
**Passed:** {count}
**Failed:** {count}
**Duration:** {time}

### Summary
{Pass/Fail status with any notable issues}

### Failed Tests (if any)
| Test | Error |
|------|-------|
| {test_name} | {error message} |

### Coverage Areas Validated
- ✅ Version parsing (None, empty, invalid, numeric)
- ✅ Version comparison (all operators)
- ✅ Guard token aliases (60+ aliases)
- ✅ All 93 version guard tokens from 72 specializations
- ✅ Multi-specialization support (unified context)
- ✅ Monorepo component version extraction
- ✅ Edge cases and error handling
```

### Additional Commands

```bash
# Run specific test class
python -m pytest tests/test_version_guards.py::TestAll93GuardTokens -v

# Run with coverage
python -m pytest tests/test_version_guards.py --cov=.claude/skills/prompt-builder/scripts --cov-report=term-missing

# Run just edge case tests
python -m pytest tests/test_version_guards.py::TestEdgeCases -v
```

### Expected Results

| Metric | Expected |
|--------|----------|
| Total tests | 205 |
| Pass rate | 100% |
| Duration | < 2 seconds |

### If Tests Fail

1. **Check the error message** - Most failures indicate a regression in prompt_builder.py
2. **Identify the failing function** - Test class names map to functions (e.g., `TestParseVersion` → `parse_version()`)
3. **Review recent changes** to `.claude/skills/prompt-builder/scripts/prompt_builder.py`
4. **Fix the issue** and re-run tests until all pass

### Files Involved

| File | Purpose |
|------|---------|
| `tests/test_version_guards.py` | 205 unit tests |
| `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Code under test |
| `templates/specializations/**/*.md` | 72 templates with version guards |

---

## 🔴 CRITICAL: Dashboard-Schema Synchronization

**When modifying the database schema (bazinga-db skill), the dashboard MUST be updated to match.**

### Why This Matters

The dashboard (`dashboard-v2/`) has its own schema definition in Drizzle ORM that must stay in sync with the authoritative schema in `.claude/skills/bazinga-db/scripts/init_db.py`. If they diverge:
- Dashboard queries fail silently or return incomplete data
- New features (reasoning, success criteria, etc.) won't appear in UI
- Composite primary keys may cause data collisions

### Checklist for Schema Changes

When you modify the database schema:

- [ ] **1. Update Drizzle schema** in `dashboard-v2/src/lib/db/schema.ts`
  - Add new columns to existing tables
  - Add new tables with proper relations
  - Match column names EXACTLY (snake_case in DB → camelCase in Drizzle)
  - Ensure primary keys match (especially composite PKs like `task_groups`)

- [ ] **2. Update TypeScript types** in `dashboard-v2/src/types/index.ts`
  - Add interfaces for new tables
  - Update existing interfaces with new fields
  - Add summary/helper types as needed

- [ ] **3. Add TRPC queries** in `dashboard-v2/src/lib/trpc/routers/sessions.ts`
  - Create queries for new tables
  - Add pagination (limit/offset) to list queries
  - Wrap new queries in try/catch for graceful degradation

- [ ] **4. Update capability detection** in `dashboard-v2/src/lib/db/capabilities.ts`
  - Add probes for new tables/columns
  - Expose capabilities via TRPC

- [ ] **5. Update UI components** to display new data
  - Create viewer components for new data types
  - Add tabs to session detail page (gated by capabilities)
  - Handle missing data gracefully

- [ ] **6. Test both scenarios**
  - Old database (missing new tables/columns)
  - Fresh database (all structures present)

### Quick Reference

| DB Schema File | Dashboard Schema File |
|----------------|----------------------|
| `.claude/skills/bazinga-db/scripts/init_db.py` | `dashboard-v2/src/lib/db/schema.ts` |
| `.claude/skills/bazinga-db/references/schema.md` | `dashboard-v2/src/types/index.ts` |

### Schema Version Tracking

The DB schema version is defined in `init_db.py`:
```python
SCHEMA_VERSION = 12  # Current version
```

The dashboard should reference this version in comments for traceability.

---

## 🔴 MANDATORY: Specialization Loader Invocation

**Before spawning Developer, QA Expert, or Tech Lead, the orchestrator MUST invoke the specialization-loader skill.**

### ❌ WRONG (What was done in failed tests)
```python
# Just reading the raw template file
Read: templates/specializations/01-languages/python.md
# Then spawning Developer...
```

### ✅ CORRECT
```python
# Invoke the specialization-loader skill
Skill(command: "specialization-loader")

# The skill will:
# 1. Read project_context.json
# 2. Load appropriate templates
# 3. Compose identity block with token budgeting
# 4. Apply version guards
# 5. Return composed block via Bash heredoc

# THEN spawn Developer with the composed block
```

### Why This Matters

The `specialization-loader` skill:
- Composes technology-specific identity (e.g., "You are a Python 3.11 Developer")
- Applies version guards (Python 3.11 patterns, not 2.7)
- Respects per-model token budgets (haiku=900, sonnet=1800, opus=2400)
- Auto-augments QA/Tech Lead with role-specific templates
- Logs to database for audit trail

Without it:
- Agents get raw template text instead of composed guidance
- No version-specific filtering
- No token budget enforcement
- No identity composition

---

## 🧪 Mini Dashboard Testing

The Mini Dashboard has a comprehensive test suite located in `mini-dashboard/tests/`.

### Running Tests

```bash
# Navigate to mini-dashboard directory
cd mini-dashboard

# Run all tests (API + Frontend if Playwright available)
./run_tests.sh

# Run API tests only (no browser needed)
./run_tests.sh api
# Or directly:
python -m pytest tests/test_api.py -v --tb=short -c /dev/null

# Run Frontend tests only (requires Playwright)
./run_tests.sh frontend
# Or directly:
python -m pytest tests/test_frontend.py -v --tb=short -c /dev/null
```

### Test Dependencies

```bash
# Install test dependencies
pip install flask pytest pytest-playwright

# Install Playwright browser (for frontend tests)
playwright install chromium
```

### Test Structure

| File | Description | Count |
|------|-------------|-------|
| `tests/test_api.py` | API endpoint tests | 42 tests |
| `tests/test_frontend.py` | Playwright UI tests | 25 tests |
| `tests/seed_test_db.py` | Test database seeder | - |
| `tests/conftest.py` | Pytest configuration | - |

### GitHub Actions

Tests run automatically on push/PR via `.github/workflows/mini-dashboard-tests.yml`:
- API tests always run
- Frontend tests run with Playwright in headless mode

---

✅ Project context loaded successfully!

📚 Research documents available in 'research/' folder
   Use these for historical context and past decisions
