# Project Context

> **Repository:** https://github.com/mehdic/bazinga

This project uses BAZINGA (Claude Code Multi-Agent Dev Team) orchestration system for complex development tasks.

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

- `.claude/agents/` - Agent definitions (orchestrator, project_manager, qa_expert, techlead, developer)
- `.claude/commands/` - Slash commands (orchestrate)
- `docs/` - Architecture documentation
- `bazinga/` - State files for orchestration (created during runs)

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

### 1. `model_selection.json` - Agent Model Assignment

**Purpose:** Controls which AI model (haiku/sonnet/opus) each agent uses

**Current assignments:**
| Agent | Model | Rationale |
|-------|-------|-----------|
| developer | haiku | Cost-efficient for straightforward implementation |
| senior_software_engineer | sonnet | Escalation - handles complex failures |
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

## 🔴 CRITICAL: Config File Sync Requirement

**When adding new bazinga config files (JSON), you MUST update TWO places:**

### Files That Must Stay In Sync

1. **`pyproject.toml`** - `[tool.hatch.build.targets.wheel.force-include]` section
2. **`src/bazinga_cli/__init__.py`** - `BazingaSetup.ALLOWED_CONFIG_FILES` list

### Why This Matters

- `force-include` controls what gets packaged in the wheel
- `ALLOWED_CONFIG_FILES` controls what gets copied during `bazinga install`
- If they're out of sync: files get packaged but never installed, or vice versa

### Checklist When Adding New Config Files

```bash
# 1. Add file to bazinga/ directory
# 2. Add to pyproject.toml force-include:
"bazinga/new_config.json" = "bazinga_cli/bazinga/new_config.json"

# 3. Add to ALLOWED_CONFIG_FILES in __init__.py:
ALLOWED_CONFIG_FILES = [
    "model_selection.json",
    "challenge_levels.json",
    "skills_config.json",
    "new_config.json",  # <-- ADD HERE
]

# 4. Run the sync test to verify:
python -m pytest tests/test_config_sync.py -v
```

### Automated Verification

The `tests/test_config_sync.py` test will fail if these lists are out of sync.

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

**When the user includes the keyword "ultrathink" in their request, you MUST:**

1. **Perform deep critical analysis** of the problem/solution
2. **Get external LLM reviews** (OpenAI + Gemini) on your analysis
3. **Integrate feedback** from external reviewers
4. **Save the refined document** to research folder

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

**When implementing features or fixes based on research documents, add a comment referencing the doc:**

```python
# See: research/token-budget-strategy.md for rationale
def calculate_budget(complexity: str) -> int:
    ...
```

```typescript
// Architecture decision: research/parallel-execution-design.md
class TaskOrchestrator {
    ...
```

**When to add:**
- Complex logic that isn't self-explanatory
- Architectural decisions with non-obvious trade-offs
- Bug fixes where root cause analysis is documented
- Any code that future readers might question "why?"

**Format:** `# See: research/{document}.md` or `// Ref: research/{document}.md`

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

✅ Project context loaded successfully!

📚 Research documents available in 'research/' folder
   Use these for historical context and past decisions
