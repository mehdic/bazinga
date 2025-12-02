# Review Agent Extraction: Architecture Analysis

**Date:** 2025-12-02
**Context:** The PR review workflow in claude.md is ~820 lines (59% of the file). Proposal to extract into a dedicated internal component.
**Decision:** Extract to `bazinga/templates/review_workflow.md` (internal template, not deployed to clients)
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (Gemini skipped)

---

## Problem Statement

The `.claude/claude.md` file has grown to 1390 lines, with the "PR Review Workflow" section consuming ~820 lines (59%). This creates several issues:

1. **Cognitive load** - claude.md is supposed to be project context, not a detailed procedural manual
2. **Context consumption** - Every conversation loads the full claude.md, even when PR review isn't needed
3. **Maintenance burden** - Changes to review workflow require navigating a massive file
4. **Single responsibility violation** - claude.md mixes project context with operational procedures

## Proposed Solution (Revised After Review)

Extract the PR review workflow into `bazinga/templates/review_workflow.md` (template-based approach).

**Key insight from OpenAI review:** The Orchestrator is allowed to read templates but NOT arbitrary agent files. Using templates avoids expanding the agent catalog and stays within existing tool constraints.

### Key Characteristics

| Aspect | Current State | Proposed State |
|--------|--------------|----------------|
| **Location** | `.claude/claude.md` (lines 564-1385) | `bazinga/templates/review_workflow.md` |
| **Deployment** | Loaded in every conversation | Only loaded when PR review triggered |
| **Client visibility** | Part of installed files | Internal-only (dev-only) |
| **Invocation** | Implicit (always present) | Explicit via `/review-pr` command OR auto-detection |
| **Size** | ~820 lines in claude.md | ~900 lines standalone (with enhancements) |
| **claude.md residue** | ~820 lines | ~40 lines (reference + detection) |

### Template Structure

```markdown
# PR Review Workflow Template

This template is loaded when a PR review is requested.
It runs as a general-purpose sub-agent with the Task tool.

## Context Variables
- PR_URL: The full PR URL
- PR_NUMBER: Extracted PR number
- OWNER: Repository owner
- REPO: Repository name
- SESSION_ID: Current session ID (for branch validation)

## Workflow
...
```

### Invocation Patterns

**Option A: Slash Command (Explicit)**
```
User: /review-pr https://github.com/mehdic/bazinga/pull/157
```

**Option B: Auto-Detection (Implicit)**
```
User: Can you review this PR? https://github.com/mehdic/bazinga/pull/157
Claude: Detected PR link. Loading review workflow...
```

Both trigger the same workflow via Task tool:
```
Task(subagent_type="general-purpose",
     prompt="<content of bazinga/templates/review_workflow.md>",
     model="sonnet")
```

## Critical Analysis

### Pros

1. **Reduced context consumption** - claude.md drops from 1390 to ~570 lines (-59%)
2. **On-demand loading** - Review workflow only loaded when PR link detected
3. **Cleaner separation** - Project context vs operational procedures clearly delineated
4. **Easier maintenance** - Single file to modify for review workflow changes
5. **Consistent with existing patterns** - Other agents (PM, Developer, QA) already follow this pattern
6. **Autonomy preserved** - Agent can run the full autonomous loop independently
7. **Internal-only scope** - Clear distinction: not for client deployment

### Cons

1. **Detection complexity** - Need reliable PR link detection in claude.md
2. **Context handoff** - Agent needs full context (repo, token, session ID) passed explicitly
3. **Loss of inline visibility** - Review workflow no longer visible in main context
4. **Additional file to maintain** - One more agent file in the repo
5. **Spawning overhead** - Task tool invocation has latency vs inline execution

### Verdict

**Strongly recommended.** The pros significantly outweigh the cons. The 59% reduction in claude.md size is substantial, and the review workflow is self-contained enough to work as an independent agent.

## Implementation Details (Revised)

### 1. Create `bazinga/templates/review_workflow.md`

Contents:
- All content from claude.md lines 564-1385
- Enhanced with:
  - Dynamic owner/repo extraction from URL
  - Branch validation before push
  - Status codes for progress tracking
  - Lint-check integration
  - Exponential backoff for API errors
  - GraphQL pagination

### 2. Create `/review-pr` Slash Command

`.claude/commands/review-pr.md`:
```markdown
---
description: Review a GitHub PR with autonomous review loop
---

Parse the PR URL from user input and spawn review workflow:
1. Extract owner, repo, number from URL
2. Read `bazinga/templates/review_workflow.md`
3. Spawn Task with template as prompt + context variables
```

### 3. Add Feature Flag

`bazinga/skills_config.json`:
```json
{
  "review_workflow": {
    "enabled": true,
    "auto_detect": true,
    "lint_before_push": true,
    "max_loop_minutes": 10,
    "max_restarts": 7
  }
}
```

### 4. Update claude.md with Minimal Reference

Replace ~820 lines with ~40 lines:

```markdown
## PR Review Workflow

**When the user shares a GitHub PR link for review:**

### Option 1: Explicit Command
\`\`\`
/review-pr https://github.com/{owner}/{repo}/pull/{number}
\`\`\`

### Option 2: Auto-Detection
When a PR URL is detected in user message, automatically load the review workflow.

### What It Does
1. Fetches all reviews (OpenAI, Gemini, Copilot, inline threads)
2. Creates extraction table (all items before any fixes)
3. Implements fixes with lint-check before push
4. Posts response to PR via GraphQL
5. Runs autonomous review loop (configurable timeout)
6. Returns summary when complete

### Status Codes
- REVIEW_STARTED - Workflow initiated
- ITEMS_EXTRACTED(N) - N items found across all reviewers
- FIXES_PUSHED(M) - M fixes committed and pushed
- LOOP_WAIT(n/10) - Waiting for new reviews (attempt n of 10)
- COMPLETE(SUCCESS|TIMEOUT|ERROR) - Workflow finished

**Reference:** `bazinga/templates/review_workflow.md`
**Config:** `bazinga/skills_config.json` → `review_workflow`
```

### 5. Internal-Only Enforcement

Since templates aren't copied to clients (only agents are):
- `bazinga/templates/` folder is naturally internal-only
- No exclusion mechanism needed
- Document in template header that it's internal

## Comparison to Alternatives

### Alternative 1: Keep in claude.md (Status Quo)

**Pros:** No migration effort, always available
**Cons:** 59% bloat, loaded in every conversation, maintenance nightmare
**Verdict:** ❌ Rejected - current state is unsustainable

### Alternative 2: Move to `agents/review-agent.md`

**Pros:** Consistent with other agents, clear separation
**Cons:** Orchestrator cannot read arbitrary agent files (tool constraint)
**Verdict:** ❌ Rejected - violates tool access policy (per OpenAI review)

### Alternative 3: Move to `research/` as reference doc

**Pros:** Removes from claude.md
**Cons:** Not executable, would need to read + process at runtime
**Verdict:** ❌ Rejected - loses the agent execution pattern

### Alternative 4: Create as a Skill

**Pros:** Could use Skill tool for invocation
**Cons:** Skills are meant for brief helpers, not autonomous 10-minute loops
**Verdict:** ❌ Rejected - doesn't fit skill pattern

### Alternative 5: Move to `bazinga/templates/review_workflow.md` ← CHOSEN

**Pros:**
- Orchestrator CAN read templates (within tool policy)
- Templates are internal-only (not copied to clients)
- Can be loaded on-demand via Task tool
- Supports both slash command and auto-detection
**Cons:**
- New pattern (first workflow template)
**Verdict:** ✅ **Adopted** - Best fit for constraints and requirements

## Decision Rationale

The template-based extraction is the right approach because:

1. **Respects tool constraints** - Orchestrator can read templates (unlike agent files)
2. **Clear trigger** - PR links are unambiguous detection targets
3. **Self-contained workflow** - All logic is encapsulated, minimal external dependencies
4. **Significant impact** - 59% reduction in base context size
5. **No behavior change** - Same workflow, just different loading mechanism
6. **Internal-only by design** - Templates folder not copied to clients
7. **Flexible invocation** - Supports both `/review-pr` command and auto-detection

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PR link not detected | Low | Medium | Clear regex pattern + fallback to `/review-pr` command |
| Context not passed correctly | Medium | High | Document required context explicitly in template |
| Workflow fails mid-loop | Medium | Medium | Built-in timeout (10 min) and restart caps (7) |
| GitHub API rate limits | Medium | Medium | Exponential backoff, respect secondary limits |
| Branch validation fails | Low | High | Check branch before any push, abort with clear error |
| Lint-check blocks push | Medium | Low | Report lint errors, let user decide to fix or skip |
| Large PR pagination | Low | Medium | Use GraphQL cursors for reviews/comments/threads |
| Token/permission issues | Medium | High | Validate token scope upfront, clear error messages |

## Implementation Checklist (Original - Superseded)

See "Revised Implementation Checklist" in Multi-LLM Review Integration section below.

## Multi-LLM Review Integration

### Consensus Points (OpenAI)

OpenAI provided comprehensive feedback. Key issues identified:

1. **Template vs Agent** - Orchestrator can read templates but not agent files
2. **Hardcoded repo** - GraphQL examples hardcode `mehdic/bazinga`
3. **No quality gates** - Direct push without lint/test checks
4. **Branch enforcement missing** - Must validate `claude/*-session-id` before push
5. **No status contract** - Orchestrator can't parse progress
6. **Missing artifacts/logging** - No bazinga-db integration

### Incorporated Feedback

| # | Feedback | Action |
|---|----------|--------|
| 1 | Use templates, not agents folder | ✅ **Adopted** - Changed to `bazinga/templates/review_workflow.md` |
| 2 | Add explicit slash command | ✅ **Adopted** - Will add `/review-pr` command |
| 3 | Define status contract | ✅ **Adopted** - Added status codes for capsule output |
| 4 | Enforce branch policy before push | ✅ **Adopted** - Add validation step |
| 5 | Parse owner/repo from URL (not hardcode) | ✅ **Adopted** - Dynamic extraction |
| 6 | Add quality gates (lint-check) | ✅ **Adopted** - Run lint before push |
| 7 | Save artifacts to bazinga-db | ✅ **Adopted** - Log extraction table and summary |
| 8 | Add feature flag in skills_config | ✅ **Adopted** - `review_workflow.enabled` |
| 9 | Handle pagination for large PRs | ✅ **Adopted** - GraphQL cursors |
| 10 | Rate limit handling | ✅ **Adopted** - Exponential backoff |

### Rejected Suggestions (With Reasoning)

| # | Suggestion | Reason for Rejection |
|---|------------|---------------------|
| 1 | SSE fix executor mode (use Dev→QA→TL pipeline) | **Too heavyweight** - PR fixes are typically small; full BAZINGA pipeline is overkill. Keep direct-push mode as default. |
| 2 | Non-jq fallback (Python-based) | **Deferred** - jq is available in all current environments. Add Python fallback later if needed. |

### Revised Implementation Checklist

Based on integrated feedback:

- [ ] Create `bazinga/templates/review_workflow.md`
  - [ ] Dynamic owner/repo extraction from PR URL
  - [ ] Branch validation before push
  - [ ] Status codes: REVIEW_STARTED, ITEMS_EXTRACTED, FIXES_PUSHED, LOOP_WAIT, COMPLETE
  - [ ] Lint-check before push
  - [ ] Exponential backoff for API errors
  - [ ] GraphQL pagination for large PRs
- [ ] Create `/review-pr` slash command (`.claude/commands/review-pr.md`)
- [ ] Add feature flag to `bazinga/skills_config.json`
- [ ] Update claude.md with minimal reference (~40 lines)
- [ ] Remove old workflow section from claude.md (~820 lines)
- [ ] Log to bazinga-db (extraction table, final summary)
- [ ] Test with real PR
- [ ] Commit and push

## Lessons Learned

(To be filled after implementation)

## References

- Current claude.md: `.claude/claude.md`
- Agent patterns: `agents/*.md`
- Template patterns: `bazinga/templates/*.md`
- Task tool documentation: Claude Code internal docs
- GitHub GraphQL API: https://docs.github.com/en/graphql
- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
