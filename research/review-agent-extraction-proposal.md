# Review Agent Extraction: Architecture Analysis

**Date:** 2025-12-02
**Context:** Extract ~820 lines of PR review workflow from claude.md into a dedicated internal agent
**Decision:** Create internal `pr-review-agent.md` at `.claude/pr-review-agent.md` for manual invocation
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
| **Location** | `.claude/pr-review-agent.md` (NOT `agents/` folder - that's for client deployment) |
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

### 1. Location (Final Decision)

**Chosen:** `.claude/pr-review-agent.md`

- Simple, stays in `.claude/` folder
- Clear naming (`pr-review-agent.md`) distinguishes from commands
- No additional folder needed
- Easily found when user asks to "launch the review agent"

### 2. Agent Structure

The agent file (`.claude/pr-review-agent.md`) is a plain markdown file with no YAML frontmatter (not needed for manual invocation).

**Key sections:**
- Input parameters (PR_URL, MODE)
- Execution modes (fix, analyze, dry-run)
- Loop guardrails (10 min, 7 restarts)
- Full workflow from original claude.md

See `.claude/pr-review-agent.md` for actual implementation.

### 3. Update claude.md (DONE)

Replaced ~820 lines with ~25 lines. See `.claude/claude.md` for actual implementation.

**Location reference:** `.claude/pr-review-agent.md`

### 4. Invocation Pattern

When user says "launch the review agent for [URL]":

```
Claude: Reading review agent...
[Read .claude/pr-review-agent.md]
Claude: Executing review workflow...
[Follows agent instructions inline]
```

**Note:** Slash command `/review-pr` was descoped - direct invocation is sufficient.

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

## Implementation Checklist (COMPLETED)

- [x] Create `.claude/pr-review-agent.md` with full workflow
- [x] Update claude.md with minimal reference (~25 lines)
- [x] Remove old workflow section from claude.md (~820 lines)
- [x] Test invocation
- [x] Commit and push

**Note:** Slash command `/review-pr` was descoped - direct invocation ("launch the review agent for URL") is sufficient and simpler.

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
| 3 | Default mode | ✅ Using fix mode as default (user preference) |
| 4 | Add confirmation gate for pushes | ✅ Adopted |
| 5 | Bot comment markers for idempotency | ✅ Adopted |
| 6 | Specify loop guardrails | ✅ Adopted - max 10 min, max 7 restarts |
| 7 | Token scope validation | ✅ Adopted |
| 8 | Dry-run mode | ✅ Adopted - summary only without posting |

### Deferred/Rejected

| # | Suggestion | Status |
|---|------------|--------|
| 1 | GitHub Actions approach | ❌ Rejected - want inline sub-agent, not CI workflow |
| 2 | Retrieval-based dynamic prompts | ⏸️ Deferred - overkill for now |
| 3 | Run lock per PR | ⏸️ Deferred - manual invocation prevents concurrent runs |
| 4 | Suggested changes API | ⏸️ Deferred - current workflow uses comments, can enhance later |

### Revised Implementation Checklist (COMPLETED)

Based on integrated feedback:

- [x] Create `.claude/pr-review-agent.md`
  - [x] Specify GitHub endpoints explicitly (reviews, review comments, issue comments, threads)
  - [x] Default mode: fix (user preference, not analyze)
  - [x] Bot comment markers for idempotency
  - [x] Loop guardrails: max 10 min, max 7 restarts
  - [x] Dry-run mode option
- [x] Update claude.md with minimal reference (~25 lines)
- [x] Remove old workflow section from claude.md (~820 lines)
- [x] Test invocation
- [x] Commit and push

**Descoped:**
- Slash command `/review-pr` - direct invocation is sufficient
- `.claude/internal/` subfolder - not needed, `.claude/` is fine

## References

- Current claude.md: `.claude/claude.md`
- PR Review section: lines 564-1385
- OpenAI Review: `tmp/ultrathink-reviews/openai-review.md`
