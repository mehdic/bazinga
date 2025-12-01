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

**Step 4: Integrate Feedback**
- Read the combined review from `tmp/ultrathink-reviews/combined-review.md`
- Identify consensus points (both OpenAI and Gemini agree)
- Evaluate conflicting opinions objectively
- Update your plan with valid improvements
- Add a "## Multi-LLM Review Integration" section documenting what was incorporated

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

---

## 🔍 PR Review Workflow

**When the user pastes a GitHub PR link for review:**

### 🔴 CRITICAL: All Feedback Sources Are Equal

**Treat ALL feedback as reviews, regardless of source:**
- Automated review comments (Copilot, CodeRabbit, etc.)
- User suggestions in chat
- User-provided code snippets or improvements
- Comments on the PR itself

**DO NOT prioritize automated reviews over user suggestions.** If the user provides a better solution than your implementation, implement it immediately - don't wait to be asked twice.

### 🔴 CRITICAL: Fetch ALL Feedback Sources Completely

**You MUST fetch and read the FULL body of ALL three sources:**

| Source | GraphQL Field | What It Contains |
|--------|--------------|------------------|
| `reviewThreads` | Inline code comments | Line-specific suggestions |
| `reviews` | Review summary bodies | **Often contains detailed analysis from bots** |
| `comments` | PR comments | **Bot analysis, "Updates Since Last Review"** |

**❌ NEVER truncate comment bodies** - Bot reviewers (Copilot, GitHub Actions) post multi-paragraph analyses with issues buried 20+ lines deep.

**When fetching, display FULL content:**
```bash
# ❌ WRONG - truncates to first line, misses issues
jq '.body | split("\n")[0]'

# ✅ CORRECT - show full body for analysis
jq '.body'
```

**Search for keywords in ALL bodies:** "fix", "issue", "regression", "missing", "should", "consider"

### 📋 Expected LLM Review Format (OpenAI & Gemini)

Both OpenAI and Gemini reviews are configured to use this structured format (makes extraction easier):

```markdown
## OpenAI Code Review  (or "## Gemini Code Review")

_Reviewed commit: {sha}_

### Summary

| Category | Count |
|----------|-------|
| 🔴 Critical | N |
| 🟡 Suggestions | N |
| ✅ Good Practices | N |

### 🔴 Critical Issues (MUST FIX)

1. **[file:line]** Issue title
   - Problem: What's wrong (1 sentence)
   - Fix: How to fix it (1 sentence)

### 🟡 Suggestions (SHOULD CONSIDER)

1. **[file:line]** Suggestion title
   - Current: What the code does now
   - Better: What would be better

### ✅ Good Practices Observed

- [Brief acknowledgment of good patterns]

### Updates Since Last Review (if applicable)

| Previous Issue | Status |
|----------------|--------|
| Issue X | ✅ Fixed in this commit |
| Issue Y | ⏭️ Acknowledged as deferred |
```

**Extraction tips:**
- Look for `### 🔴 Critical` section first - these are MUST FIX
- Count items in Summary table to verify you extracted all
- Each issue has `**[file:line]**` format for easy location
- If review doesn't follow format, extract manually from prose

### Automatic Behavior

1. **Fetch ALL THREE sources** - reviewThreads, reviews, AND comments (full bodies)
2. **Read complete content** - Never truncate, bot analysis is often multi-paragraph
3. **Process user suggestions** - Treat chat messages with code/suggestions as reviews
4. **Ultrathink** - Apply deep critical analysis to each feedback point
5. **Triage** feedback into categories:
   - **Critical/Breaking** - Must fix (security issues, bugs, breaking changes)
   - **Valid improvements** - Better solutions than current implementation
   - **Minor/Style** - Low-impact changes

### 🔴 MANDATORY: Extraction-First Workflow (BEFORE Implementation)

**⚠️ ROOT CAUSE OF MISSED ITEMS:** Jumping straight to implementation without systematic extraction causes items to be lost. Long reviews (200+ lines) have issues buried in the middle that get skipped.

**THE FIX: Create extraction table BEFORE touching any code.**

#### Step 1: Fetch ALL Reviews
```bash
# Fetch from ALL three sources (OpenAI, Gemini, Copilot, inline comments)
# Use GraphQL to get full bodies - NEVER truncate
```

#### Step 2: Create Master Extraction Table (BEFORE ANY IMPLEMENTATION)
```markdown
## PR #XXX - Master Extraction Table

**Sources:** OpenAI (X items), Gemini (Y items), Copilot (Z items)
**Total: N items to address**

| # | Source | Category | Suggestion | Status |
|---|--------|----------|------------|--------|
| 1 | OpenAI | Critical | Shape-accurate no-ops | ❌ Pending |
| 2 | OpenAI | Type Safety | Use import type | ❌ Pending |
| 3 | Gemini | Style | Extract shared loader | ❌ Pending |
| 4 | Copilot | Bug | Fix null check | ❌ Pending |
| ... | ... | ... | ... | ... |

**Announce:** "Found N items: X from OpenAI, Y from Gemini, Z from Copilot"
```

#### Step 3: ONLY THEN Implement
- Work through the table row by row
- Update status as you go: `❌ Pending` → `🔄 In Progress` → `✅ Fixed` or `⏭️ Skipped`
- NEVER skip a row without explicit justification

**🔴 CRITICAL: Never Dismiss Entire Reviews**

If you find ONE false positive in a review, DO NOT dismiss the entire review:
- ❌ WRONG: "The LLM is wrong about X, so I'll ignore this review"
- ✅ CORRECT: Mark that item as `⏭️ False Positive`, but STILL extract and address ALL other items

**Common failure mode:** Getting distracted proving one claim wrong, then never returning
to address the valid issues in the same review. ALWAYS complete the full extraction table.

#### Step 4: Final Verification
```markdown
## Final Count Verification
- Items extracted: N
- Items addressed: N
- ✅ All items accounted for

| Status | Count |
|--------|-------|
| ✅ Fixed | X |
| ⏭️ Skipped | Y |
| ❌ Missed | 0 |  ← MUST be zero
```

**🔴 IF "Missed" > 0: STOP and fix before proceeding.**

#### Step 5: Post Response to PR (MANDATORY)
**After committing fixes, you MUST post a response comment to the PR.**

Use headers that match the LLM reviewer:
- `## Response to OpenAI Code Review`
- `## Response to Gemini Code Review`

```markdown
## Response to OpenAI Code Review

| # | Suggestion | Action |
|---|------------|--------|
| 1 | Fix X | ✅ Fixed in {commit} |
| 2 | Add Y | ⏭️ Skipped - by design: [reason] |

## Response to Gemini Code Review

| # | Suggestion | Action |
|---|------------|--------|
| 1 | Issue Z | ✅ Fixed in {commit} |
```

**Why this matters:**
- LLMs see your responses in their next review (via timestamp filtering)
- Prevents re-raising of already-addressed items
- Creates audit trail for future developers

#### Why This Works
1. **Forces enumeration** - Can't skip what's in the table
2. **Visual accountability** - Pending items are visible
3. **Count verification** - Math doesn't lie
4. **Prevents "I'll get to it later"** - Everything tracked upfront

### Implementation Rules

| Category | Action |
|----------|--------|
| **Critical/Breaking** | Implement immediately |
| **Valid improvements** | Implement immediately (don't wait to be asked) |
| **Minor/Style** | Track in table, implement if quick, otherwise mark `⏭️ Skipped - Minor` |

### 🔴 MANDATORY: Validation Checklist

**Before saying "done" or moving on, you MUST:**

1. **Extract ALL suggestions** - Create a numbered list of EVERY suggestion from:
   - PR review comments (automated)
   - User messages in chat
   - Code snippets user provided

2. **Explicitly address each one** - For each item, state:
   - `✅ Implemented in commit {hash}` - if fixed
   - `⏭️ Skipped: {reason}` - if intentionally skipped (must justify)
   - `❌ Missed` - if you forgot (then go fix it!)

3. **Count check** - Verify: `Items extracted == Items addressed`

**Example validation:**
```
## Validation Checklist
User provided 3 suggestions:
1. Smart BUILD_ID sync → ✅ Implemented in commit abc123
2. Robust port check → ✅ Implemented in commit abc123
3. Public folder sync → ✅ Implemented in commit def456

Count: 3 extracted, 3 addressed ✓
```

**If count doesn't match, STOP and fix before proceeding.**

### 🔴 MANDATORY: Final Summary Table

**When finishing PR review, you MUST present a complete table of ALL suggestions:**

```markdown
## PR #XXX - Complete Suggestions Table

| # | File:Line | Suggestion | Action |
|---|-----------|------------|--------|
| 1 | file.sh:42 | Quote variable $FOO | ✅ Fixed in commit abc123 |
| 2 | file.sh:55 | Add error handling | ✅ Fixed in commit abc123 |
| 3 | file.sh:78 | Use different approach | ⏭️ Skipped - current approach is correct |
| ... | ... | ... | ... |

**Count: X extracted, X addressed ✓**
```

**This table MUST include:**
- Every single suggestion from PR review threads
- File path and line number
- Brief description of suggestion
- Action taken (✅ Fixed / ⏭️ Skipped with reason)

**Present this table to the user before declaring the PR review complete.**

### 🔴 CRITICAL: Always Re-check Before Declaring Complete

Before telling the user "no new reviews":
1. **Re-fetch ALL review sources** - threads, reviews, AND issue comments
2. **Compare timestamps** - any comments after your last response?
3. **If new comments exist** - evaluate them before declaring complete

**Why this matters:** Automated reviewers (OpenAI, Gemini) may post comments minutes after you check. A 2-minute gap can mean missing important feedback.

**Example failure mode:**
```
09:08:42 - You check for reviews, see none
09:10:41 - OpenAI posts a review
09:11:00 - You tell user "no new reviews" ← WRONG!
```

### Verification

Before implementing any "fix":
- **Check if already addressed** - Reviewers may miss existing safeguards
- **Verify the claim** - Read the actual code, not just the review comment
- **Assess risk/reward** - Some "improvements" add complexity without value

### Output Format

```
## PR #XXX Review Analysis

### Critical/Breaking Issues: [NONE | list]
- Issue 1: [description] → [action taken]

### Implemented (Minor Improvements)
- [list of quick wins implemented]

### Valid but NOT Critical (Deferred)
| Feedback | Why Deferred |
|----------|--------------|
| [feedback] | [reasoning] |
```

### Documentation

Always create `research/prXXX-review-analysis.md` with full ultrathink analysis.

---

## 🤖 GitHub PR Automation

**When reviewing PRs and resolving comments, use the GitHub API directly.**

### GitHub Token Setup

**Token sources (in order of preference):**
1. Environment variable: `BAZINGA_GITHUB_TOKEN` (Claude Code Web)
2. File: `~/.bazinga-github-token` (local development)

**Load token in scripts:**
```bash
GITHUB_TOKEN="${BAZINGA_GITHUB_TOKEN:-$(cat ~/.bazinga-github-token 2>/dev/null)}"
```

**Token requirements:**
- Classic PAT with `repo` scope (required for GraphQL thread resolution)
- Fine-grained PATs do NOT support `resolveReviewThread` mutation

**Load token in scripts:**
```bash
GITHUB_TOKEN=$(cat ~/.bazinga-github-token)
```

### Workflow: Responding to PR Review Comments

**Step 1: Fetch review threads (GraphQL)**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d '{"query": "query { repository(owner: \"mehdic\", name: \"bazinga\") { pullRequest(number: PR_NUMBER) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 10) { nodes { id databaseId body author { login } } } } } } } }"}'
```

**Step 2: Resolve threads (GraphQL mutation)**
```bash
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d '{"query": "mutation { resolveReviewThread(input: {threadId: \"THREAD_ID\"}) { thread { id isResolved } } }"}'
```

**Batch resolve multiple threads:**
```bash
GITHUB_TOKEN="${BAZINGA_GITHUB_TOKEN:-$(cat ~/.bazinga-github-token 2>/dev/null)}"

for thread_id in PRRT_xxx PRRT_yyy PRRT_zzz; do
  curl -s -X POST \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.github.com/graphql" \
    -d "{\"query\": \"mutation { resolveReviewThread(input: {threadId: \\\"$thread_id\\\"}) { thread { id isResolved } } }\"}"
done
```

**Note:** REST API doesn't work in Claude Code Web - use GraphQL only.

### Response Templates

| Situation | Response Prefix |
|-----------|-----------------|
| Fixed in commit | `✅ **Fixed in commit {hash}**` |
| Valid but deferred | `📝 **Valid observation - Deferred**` |
| Not a bug / By design | `📝 **Intentional** / **Not a bug**` |
| Acknowledged low priority | `📝 **Acknowledged - Low risk**` |

### Process When User Shares PR Link

1. **Fetch** all review threads via GraphQL (includes `isResolved` status)
2. **Analyze** each unresolved comment (triage: critical vs deferred)
3. **Fix** critical issues in code
4. **Commit & push** fixes
5. **🔴 Post response to PR via GraphQL** (BEFORE any merge - see "Post via GraphQL" section below)
6. **Resolve** inline threads if applicable
7. **Report** summary to user

**🔴 CRITICAL: Always post PR response via GraphQL BEFORE merging.** This ensures:
- LLM reviewers see your response in subsequent reviews
- Audit trail exists for all addressed/skipped items
- No feedback is silently ignored

### 🔴 MANDATORY: Respond to ALL Feedback (Fixed AND Skipped)

**CRITICAL: You MUST respond to EVERY piece of feedback, whether implemented or skipped.**

This serves two purposes:
1. **Audit trail** - Reviewers see what was done and why
2. **LLM context** - Responses are included in subsequent LLM reviews via `llm-reviews.sh`

### For Inline Code Comments (with resolve buttons)

**Step 1: Reply to the thread explaining your action**
```bash
GITHUB_TOKEN="${BAZINGA_GITHUB_TOKEN:-$(cat ~/.bazinga-github-token 2>/dev/null)}"

# Reply to a review thread (use the comment's node_id)
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d '{"query": "mutation { addPullRequestReviewComment(input: {pullRequestReviewId: \"PRR_xxx\", inReplyTo: \"PRRC_xxx\", body: \"✅ Fixed in commit abc123\"}) { comment { id } } }"}'
```

**Step 2: Resolve the thread (only if FIXED)**
```bash
# Only resolve if you actually fixed it
curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d '{"query": "mutation { resolveReviewThread(input: {threadId: \"PRRT_xxx\"}) { thread { id isResolved } } }"}'
```

**For SKIPPED items: Reply but do NOT resolve**
```
⏭️ **Skipped - By Design**

This is intentional behavior because [explanation].
The graceful degradation allows the dashboard to start even when [reason].
```

### For PR Comments (LLM Reviews)

**🔴 CRITICAL: Use specific headers for each LLM reviewer:**

Responses to LLM reviews MUST use these exact headers so the workflows can filter them:
- `## Response to OpenAI Code Review` - for OpenAI feedback
- `## Response to Gemini Code Review` - for Gemini feedback

This enables timestamp-windowed filtering: each LLM only sees responses to ITS OWN reviews.

**Post via GraphQL (required in Claude Code Web):**

**Step 0: Validate prerequisites**
```bash
# Set PR number (replace with actual number)
PR_NUMBER=155

# Validate token exists
if [ -z "${BAZINGA_GITHUB_TOKEN:-}" ]; then
  echo "ERROR: BAZINGA_GITHUB_TOKEN is not set" >&2
  exit 1
fi
```

**Step 1: Get PR node ID (with error handling)**
```bash
RESPONSE=$(curl -sSf -X POST \
  -H "Authorization: Bearer $BAZINGA_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d "{\"query\": \"query { repository(owner: \\\"mehdic\\\", name: \\\"bazinga\\\") { pullRequest(number: $PR_NUMBER) { id } } }\"}")

PR_NODE_ID=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.id')

# Validate PR node ID was retrieved
if [ -z "$PR_NODE_ID" ] || [ "$PR_NODE_ID" = "null" ]; then
  echo "ERROR: Could not resolve PR node ID. Response: $RESPONSE" >&2
  exit 1
fi
echo "PR Node ID: $PR_NODE_ID"
```

**Step 2: Write JSON to temp file and patch with jq (cross-platform)**
```bash
# Use mktemp for secure temp file creation
TMPFILE=$(mktemp)
cat > "$TMPFILE" << 'ENDJSON'
{
  "query": "mutation($body: String!, $id: ID!) { addComment(input: {subjectId: $id, body: $body}) { commentEdge { node { url } } } }",
  "variables": {
    "id": "PLACEHOLDER_ID",
    "body": "## Response to OpenAI Code Review\n\n| # | Suggestion | Action |\n|---|------------|--------|\n| 1 | Fix X | ✅ Fixed in abc123 |\n| 2 | Add Y | ⏭️ Skipped - by design: [explanation] |\n\n## Response to Gemini Code Review\n\n| # | Suggestion | Action |\n|---|------------|--------|\n| 1 | Issue Z | ✅ Fixed in def456 |"
  }
}
ENDJSON

# Use jq to replace placeholder (cross-platform, unlike sed -i)
jq --arg id "$PR_NODE_ID" '.variables.id = $id' "$TMPFILE" > "${TMPFILE}.patched"
mv "${TMPFILE}.patched" "$TMPFILE"
```

**Step 3: Post the comment (with error detection)**
```bash
RESPONSE=$(curl -sSf -X POST \
  -H "Authorization: Bearer $BAZINGA_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/graphql" \
  -d @"$TMPFILE")

# Cleanup temp file
rm -f "$TMPFILE"

# Check for GraphQL errors
if echo "$RESPONSE" | jq -e '.errors' > /dev/null 2>&1; then
  echo "ERROR: GraphQL mutation failed: $RESPONSE" >&2
  exit 1
fi

echo "$RESPONSE" | jq -r '.data.addComment.commentEdge.node.url'
```

**Note:** Use `\n` for newlines in the JSON body. The jq patching method is cross-platform (works on Linux and macOS).

### Response Templates

| Action | Response Format |
|--------|-----------------|
| **Fixed** | `✅ **Fixed in commit {hash}** - [brief description of fix]` |
| **Skipped (by design)** | `⏭️ **Skipped - By Design** - [detailed explanation why this is intentional]` |
| **Skipped (low risk)** | `⏭️ **Skipped - Low Risk** - [explanation of why impact is minimal]` |
| **Skipped (deferred)** | `📝 **Deferred** - Valid suggestion, will address in future PR` |

### 🔴 CRITICAL: Skipped Items MUST Have Detailed Explanations

**❌ WRONG (too brief):**
```
⏭️ Skipped - intentional
```

**✅ CORRECT (detailed):**
```
⏭️ **Skipped - By Design**

Silent failure is intentional here. The dashboard should gracefully degrade
when the database module fails to load (e.g., architecture mismatch).
Throwing an error would prevent the dashboard from starting entirely,
which is worse than running with limited functionality.

The warning message in console provides debugging info for developers.
```

### Why Respond to Everything?

1. **LLM Review Context** - The `llm-reviews.sh` script includes previous responses, so OpenAI/Gemini see your reasoning
2. **Prevents Re-raising** - Reviewers won't flag the same issue again if they see it was considered
3. **Knowledge Base** - Future developers understand why decisions were made
4. **Accountability** - Shows thorough review, not just cherry-picking easy fixes

### Summary: Actions for Each Feedback Type

| Feedback Type | Reply Required? | Resolve Thread? |
|--------------|-----------------|-----------------|
| Fixed inline comment | ✅ Yes (explain fix) | ✅ Yes |
| Skipped inline comment | ✅ Yes (explain why) | ❌ No (leave open) |
| PR comment (any) | ✅ Yes (response table) | N/A |
| Bot analysis | ✅ Yes (response table) | N/A |

---

✅ Project context loaded successfully!

📚 Research documents available in 'research/' folder
   Use these for historical context and past decisions
