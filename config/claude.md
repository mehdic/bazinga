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

- `.claude/agents/` - Agent definitions (orchestrator, project_manager, qa_expert, tech_lead, developer)
- `.claude/commands/` - Slash commands (orchestrate)
- `docs/` - Architecture documentation
- `bazinga/` - State files for orchestration (created during runs)

---

## 🔴 CRITICAL: Orchestrator File Synchronization

**These files MUST be kept IDENTICAL:**

1. **agents/orchestrator.md** - The agent definition (Task tool invocation)
2. **.claude/commands/bazinga.orchestrate.md** - The slash command version

### ✅ REQUIRED SYNC PROCEDURE

After making ANY changes to either file, copy to the other:

```bash
# When updating orchestrator, copy to both locations:
cp agents/orchestrator.md .claude/commands/bazinga.orchestrate.md

# OR if you edited the command file:
cp .claude/commands/bazinga.orchestrate.md agents/orchestrator.md
```

### Verify Synchronization

```bash
# Verify files are identical (should output: "Files are identical")
diff -q agents/orchestrator.md .claude/commands/bazinga.orchestrate.md && echo "✓ Files are identical"
```

### Why Both Files Must Be Identical

- **Same orchestration logic** - Both use identical workflow and state management
- **Same database operations** - Both invoke bazinga-db skill identically at same points
- **Same agent coordination** - Both spawn PM, developers, QA, tech lead identically
- **Same state persistence** - Both have mandatory database persistence checkpoints
- **NO differences** - Files are now completely identical (no header variations)

**Recent critical updates (ensure both files have these):**
- Mandatory database operations section (lines 68-114)
- PM state verification with fallback (Step 1.4, lines 685-738)
- Enhanced orchestrator state saves (lines 1679-1724)
- Final state checkpoint (lines 1991-2046)

**⚠️ IMPORTANT:** Edit one, sync to the other. Always verify they're identical after changes.

---

## Key Principles

1. **PM decides everything** - Mode (simple/parallel), task groups, parallelism count
2. **PM sends BAZINGA** - Only PM can signal completion (not tech lead)
3. **Database = memory** - All state stored in SQLite database (bazinga/bazinga.db) via bazinga-db skill
4. **Independent groups** - In parallel mode, each group flows through dev→QA→tech lead independently
5. **Orchestrator never implements** - This rule is absolute and inviolable

---

## 🔴 CRITICAL: Skill File Editing Guidelines

**When creating or editing ANY skill SKILL.md file, you MUST follow this guide:**

📋 **MANDATORY REFERENCE:** `/home/user/bazinga/research/skill-fix-manual.md`

### Key Requirements

1. **Skills are Claude instances** - SKILL.md contains instructions FOR the skill instance, not documentation ABOUT it
2. **Proper framing** - Start with "You are the [skill-name] skill..."
3. **Call scripts** - Skills should call existing scripts, not implement logic inline
4. **Required sections:**
   - YAML frontmatter with `version: 1.0.0`
   - "When to Invoke This Skill" section
   - "Your Task" section (3 steps: execute script → read report → return summary)
   - "Example Invocation" scenarios with concrete input/output

### Before Editing Any SKILL.md

```bash
# ALWAYS read the manual first
Read: /home/user/bazinga/research/skill-fix-manual.md
```

This manual provides:
- ✅ Correct skill pattern (150-250 lines focused on instructions)
- ❌ Wrong pattern to avoid (300-500+ lines of documentation)
- ✅ Step-by-step fix process
- ✅ Before/After examples
- ✅ Validation checklist

**❌ DO NOT:**
- Write documentation-style content
- Show raw bash commands for humans to copy
- Include detailed implementation logic
- Create skills without version numbers
- Skip "When to Invoke" section

**✅ DO:**
- Write actionable instructions for the skill instance
- Call existing scripts in `.claude/skills/skill-name/`
- Include example invocation scenarios
- Keep it under 250 lines
- Use minimal allowed-tools (usually `[Bash, Read]`)

---
