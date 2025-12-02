# Review Agent Extraction: Architecture Analysis

**Date:** 2025-12-02
**Context:** Extract ~820 lines of PR review workflow from claude.md into a dedicated internal agent
**Decision:** Create internal `review-agent.md` for manual invocation
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The `.claude/claude.md` file is 1390 lines, with the "PR Review Workflow" section consuming ~820 lines (59%). This creates issues:

1. **Context bloat** - Every conversation loads full claude.md, even when PR review isn't needed
2. **Maintenance burden** - Navigating massive file for workflow changes
3. **Mixed concerns** - Project context mixed with detailed operational procedures

## Proposed Solution

Extract the PR review workflow into a dedicated **internal agent**: `pr-review-agent.md`

### Key Points

| Aspect | Description |
|--------|-------------|
| **Purpose** | Autonomous PR review: fetch reviews, extract items, fix issues, post responses, review loop |
| **Invocation** | Manual - user asks: "launch the review agent with PR URL" |
| **Location** | Internal location (NOT `agents/` folder - that's for client deployment) |
| **Scope** | Internal dev tooling only - not part of BAZINGA orchestration |

### What This Is NOT

- ❌ NOT part of orchestrator workflow
- ❌ NOT deployed to clients
- ❌ NOT integrated with PM/Dev/QA/TechLead agents
- ❌ NOT auto-detected or auto-invoked

### What This IS

- ✅ Internal dev tooling for PR reviews
- ✅ Manually invoked via Task tool when user requests
- ✅ Self-contained autonomous workflow
- ✅ Reduces claude.md by ~820 lines

## Critical Analysis

### Pros

1. **59% reduction in claude.md** - From 1390 to ~570 lines
2. **On-demand loading** - Only loaded when explicitly requested
3. **Clean separation** - Project context vs operational workflow
4. **Easier maintenance** - Single dedicated file for review workflow
5. **Self-contained** - All review logic in one place

### Cons

1. **Manual invocation** - User must remember to request it
2. **Context handoff** - Need to pass PR URL to agent
3. **One more file** - Additional file to maintain

### Verdict

**Recommended.** The 59% context reduction is significant. The workflow is self-contained and doesn't need to be loaded in every conversation.

## Implementation Details

### 1. Location Options

**Option A: `.claude/internal/review-agent.md`**
- Pro: Clear separation from deployed agents
- Con: New folder to create

**Option B: `dev-agents/review-agent.md`**
- Pro: Parallel to `dev-scripts/` pattern
- Con: New top-level folder

**Option C: `.claude/review-agent.md`**
- Pro: Simple, stays in .claude
- Con: Might be confused with commands

**Recommendation:** Option A (`.claude/internal/`) - clearest separation

### 2. Agent Structure (Enhanced)

```markdown
---
name: pr-review-agent
description: Internal PR review agent. Fetches reviews, creates extraction table, implements fixes, posts responses, runs autonomous review loop.
model: sonnet
---

# PR Review Agent

You are a PR review agent. Given a PR URL, you will:
1. Validate token scope (repo access required)
2. Fetch all reviews via GitHub GraphQL:
   - reviews (PR review summaries)
   - reviewThreads (inline code comments)
   - comments (PR issue comments)
3. Create master extraction table (before any fixes)
4. Implement fixes (with confirmation before push)
5. Post response to PR (use bot markers for idempotency)
6. Run autonomous review loop (max 10 min, max 7 restarts)
7. Return summary

## Execution Modes
- **default**: Analyze + suggest changes only (no auto-push)
- **fix**: Implement fixes with confirmation before each push
- **dry-run**: Generate summary without posting to GitHub

## Loop Guardrails
- Max runtime: 10 minutes
- Max restarts: 7 cycles
- Exponential backoff for API errors

## Input
- PR_URL: The GitHub PR URL to review
- MODE (optional): default | fix | dry-run

## Workflow
[Full workflow content from claude.md lines 564-1385]
```

### 3. Update claude.md

Replace ~820 lines with ~25 lines:

```markdown
## PR Review Workflow

**To review a PR, use one of these methods:**

### Option 1: Direct request
"Launch the review agent for https://github.com/owner/repo/pull/123"

### Option 2: Slash command
/review-pr https://github.com/owner/repo/pull/123

### Modes
- **default**: Analyze + suggest (no auto-push)
- **fix**: Implement fixes (with confirmation)
- **dry-run**: Summary only, no GitHub posts

### What it does
1. Fetches all reviews (OpenAI, Gemini, Copilot, inline threads)
2. Creates extraction table
3. Implements fixes (if in fix mode)
4. Posts responses to PR
5. Runs autonomous review loop (max 10 min)

**Location:** `.claude/internal/pr-review-agent.md`
```

### 4. Invocation Pattern

When user says "launch the review agent for [URL]":

```
Claude: Reading review agent...
[Read .claude/internal/review-agent.md]
Claude: Spawning review agent...
[Task tool with agent content as prompt, PR_URL passed in]
```

## Comparison to Alternatives

| Alternative | Verdict |
|-------------|---------|
| Keep in claude.md | ❌ Rejected - 59% bloat |
| Put in `agents/` folder | ❌ Rejected - that's for client deployment |
| Create as Skill | ❌ Rejected - skills are brief helpers, not 10-min autonomous loops |
| Create as slash command | ⚠️ Possible but adds complexity |
| **Internal agent file** | ✅ Chosen - clean separation, on-demand loading |

## Risk Analysis

| Risk | Mitigation |
|------|------------|
| User forgets to invoke | Document in claude.md, simple phrase to remember |
| PR URL not passed correctly | Agent prompts for URL if not provided |
| Agent fails mid-loop | Built-in timeout and restart caps |

## Implementation Checklist

- [ ] Create `.claude/internal/` folder
- [ ] Create `.claude/internal/review-agent.md` with full workflow
- [ ] Update claude.md with minimal reference (~20 lines)
- [ ] Remove old workflow section from claude.md (~820 lines)
- [ ] Test invocation
- [ ] Commit and push

## Additional: Internal Slash Command

Add `/review-pr` command for convenience (also internal-only, not deployed to clients):

`.claude/commands/review-pr.md`:
```markdown
---
description: Launch PR review agent (internal - not deployed to clients)
---

Parse the PR URL from arguments and spawn the review agent.
```

**Note:** This command file should NOT be in the list of files copied to clients during `bazinga install`.

## Multi-LLM Review Integration

### Key Feedback from OpenAI

1. **Clarify data sources** - Be explicit about which GitHub endpoints: reviews, review comments, issue comments, review threads
2. **Execution modes** - Default: analyze + suggested changes only. Opt-in: open fix branch/PR or push to branch
3. **Permissions/safety** - Detect forks, protected branches, validate token scopes upfront
4. **Idempotency** - Use bot markers, update existing comments vs posting duplicates
5. **Loop guardrails** - Specify max steps, max tokens, max runtime
6. **Concurrency** - Add run lock per PR to avoid conflicts
7. **Naming** - Rename to `pr-review-agent.md` for clarity
8. **Packaging isolation** - Add explicit mechanism to exclude from client installs

### Incorporated Feedback

| # | Feedback | Action |
|---|----------|--------|
| 1 | Rename to `pr-review-agent.md` | ✅ Adopted |
| 2 | Clarify GitHub endpoints | ✅ Adopted - specify exactly which APIs |
| 3 | Default to analyze+suggest mode | ✅ Adopted - safer default |
| 4 | Add confirmation gate for pushes | ✅ Adopted |
| 5 | Bot comment markers for idempotency | ✅ Adopted |
| 6 | Specify loop guardrails | ✅ Adopted - max 10 min, max 7 restarts |
| 7 | Token scope validation | ✅ Adopted |
| 8 | Dry-run mode | ✅ Adopted - summary only without posting |

### Deferred/Rejected

| # | Suggestion | Status |
|---|------------|--------|
| 1 | GitHub Action approach | ❌ Rejected - want inline sub-agent, not CI workflow |
| 2 | Retrieval-based dynamic prompts | ⏸️ Deferred - overkill for now |
| 3 | Run lock per PR | ⏸️ Deferred - manual invocation prevents concurrent runs |
| 4 | Suggested changes API | ⏸️ Deferred - current workflow uses comments, can enhance later |

### Revised Implementation Checklist

Based on integrated feedback:

- [ ] Create `.claude/internal/` folder
- [ ] Create `.claude/internal/pr-review-agent.md` (renamed for clarity)
  - [ ] Specify GitHub endpoints explicitly (reviews, review comments, issue comments, threads)
  - [ ] Default mode: analyze + suggest (no auto-push)
  - [ ] Confirmation gate before any push
  - [ ] Bot comment markers for idempotency
  - [ ] Loop guardrails: max 10 min, max 7 restarts
  - [ ] Token scope validation upfront
  - [ ] Dry-run mode option
- [ ] Create internal `/review-pr` command (NOT deployed to clients)
- [ ] Update claude.md with minimal reference (~20 lines)
- [ ] Remove old workflow section from claude.md (~820 lines)
- [ ] Ensure packaging excludes `.claude/internal/` from client installs
- [ ] Test invocation
- [ ] Commit and push

## Open Questions

1. **Folder location** - `.claude/internal/` seems best (OpenAI didn't object to this)

## References

- Current claude.md: `.claude/claude.md`
- PR Review section: lines 564-1385
- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
