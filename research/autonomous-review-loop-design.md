# Autonomous Review Loop: Design Analysis

**Date:** 2025-12-02
**Context:** Adding autonomous review cycle to PR workflow in claude.md
**Decision:** Implement polling-based review loop with intelligent exit conditions
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

Currently, after pushing a PR fix, the workflow returns control to the user. The user must then:
1. Wait for CI pipelines to complete (Copilot, OpenAI, Gemini reviews)
2. Manually ask Claude to check for new reviews
3. Repeat the entire fix cycle if issues are found

This creates friction and delays. The user shouldn't have to babysit the review process.

**Goal:** Automate the "wait for reviews → check for issues → fix → repeat" cycle until all reviews pass or a terminal condition is reached.

## Proposed Solution

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR REVIEW WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│  Steps 1-9: Standard workflow (fetch, fix, commit, push)        │
│                              │                                  │
│                              ▼                                  │
│  Step 10: Enter Review Loop ─────────────────────────┐          │
│                              │                       │          │
│         ┌────────────────────▼──────────────────┐    │          │
│         │         REVIEW LOOP                   │    │          │
│         │                                       │    │          │
│         │  1. Sleep 60 seconds                  │    │          │
│         │  2. Fetch reviews from GitHub         │    │          │
│         │  3. Check: All 3 reviewers responded? │    │          │
│         │     - Copilot (inline review)         │    │          │
│         │     - OpenAI (PR comment)             │    │          │
│         │     - Gemini (PR comment)             │    │          │
│         │  4. Check for workflow failures       │    │          │
│         │  5. Extract issues from reviews       │    │          │
│         │  6. Decide: continue/exit/restart     │    │          │
│         │                                       │    │          │
│         └───────────────────────────────────────┘    │          │
│                              │                       │          │
│              ┌───────────────┼───────────────┐       │          │
│              ▼               ▼               ▼       │          │
│         [SUCCESS]       [TIMEOUT]       [RESTART]    │          │
│         No issues       6 min limit     Issues found │          │
│         Return to       Return to       Go to Step 1 │──────────┘
│         user            user            (full cycle) │
│                                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Exit Conditions (Detailed)

| Condition | Detection | Action |
|-----------|-----------|--------|
| **SUCCESS** | All 3 reviews present AND no critical/actionable items | Exit loop, report "All reviews passed" |
| **PARTIAL SUCCESS** | Some reviews present, no issues in available reviews | Continue waiting up to timeout |
| **WORKFLOW FAILURE** | Review contains "API Error", "Timeout", "503" | Exit loop, inform user to check CI |
| **TIMEOUT** | 10 attempts (10 minutes) with <3 reviews | Exit loop, report which reviews missing |
| **ISSUES FOUND** | Critical or actionable items extracted | Restart full workflow (steps 1-9) |

### Critical Design Decisions

#### 1. Polling Interval: 60 seconds

**Rationale:**
- CI pipelines typically take 1-3 minutes
- Too frequent (10s) → unnecessary API calls, potential rate limiting
- Too infrequent (5m) → poor UX, wasted time
- 60 seconds is a good balance

**Alternative considered:** Webhook-based notification
- Rejected: Adds infrastructure complexity, not feasible in Claude Code environment

#### 2. Max Attempts: 10 (10 minutes total)

**Rationale:**
- Most CI completes within 3-4 minutes
- 10 minutes covers edge cases (cold starts, queued jobs, LLM API retries)
- Gemini 3 Pro can be slow (up to 6 minutes with retries)
- Beyond 10 minutes, likely a real failure requiring user intervention

#### 3. Track Push Timestamp, Not Just Commit

**Problem:** Reviews might exist from previous commits. We only want reviews on OUR push.

**Solution:**
```
push_time = current_timestamp()
# ... later ...
reviews_after_push = filter(reviews, created_at > push_time)
```

#### 4. Restart Full Workflow vs. Incremental Fix

**Decision:** Restart full workflow (steps 1-9)

**Rationale:**
- New reviews might have NEW issues not in previous reviews
- Fresh fetch ensures we don't miss anything
- Consistent behavior, easier to reason about

**Alternative considered:** Only fix new issues, skip re-fetch
- Rejected: Risk of missing issues, complex state management

#### 5. What Counts as "Actionable"?

**Definition:**
- Critical issues (security, bugs, breaking changes) → ALWAYS actionable
- Suggestions with clear code changes → actionable
- Style/formatting suggestions → NOT actionable (skip with note)
- "Consider" suggestions without specific changes → NOT actionable

**Implementation:**
```python
def is_actionable(item):
    if item.category == "Critical":
        return True
    if item.category == "Suggestion":
        # Has specific code change or clear fix
        return item.has_code_suggestion or item.has_clear_fix
    return False
```

## Critical Analysis

### Pros

1. **Reduced user friction** - No need to manually check for reviews
2. **Faster iteration** - Issues fixed immediately when detected
3. **Complete automation** - True "fire and forget" for simple PRs
4. **Clear exit conditions** - User knows exactly why loop ended

### Cons

1. **Context window consumption** - Loop iterations add to context
2. **Potential infinite loop** - If reviews always find issues (mitigated by actionable filter)
3. **API rate limits** - Multiple fetches per cycle (mitigated by 60s interval)
4. **User loses control** - Can't interrupt mid-loop (acceptable tradeoff)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Infinite loop (always new issues) | Medium | High | Only process actionable items, skip style |
| API rate limit | Low | Medium | 60s polling interval |
| Context exhaustion | Medium | High | Exit after 10 minutes regardless |
| Review pipeline failure | Medium | Low | Detect and exit gracefully |

### Verdict

**IMPLEMENT** - Benefits outweigh risks. The mitigations are sufficient.

## Implementation Details

### State Tracking

```python
class ReviewLoopState:
    push_commit: str       # Commit hash we just pushed
    push_time: datetime    # When we pushed (for filtering reviews)
    attempts: int          # Current attempt count
    max_attempts: int = 6  # Exit after this many

    # Review status
    copilot_ready: bool
    openai_ready: bool
    gemini_ready: bool

    # Extracted items
    critical_items: List[Item]
    actionable_items: List[Item]
```

### Review Detection Logic

```bash
# Detect Copilot review (appears as PR review, not comment)
COPILOT=$(jq -r '
  .data.repository.pullRequest.reviews.nodes[]
  | select(.author.login == "copilot-pull-request-reviewer")
  | select(.commit.oid | startswith("'"$PUSH_COMMIT"'"))
' /tmp/pr_data.json)

# Detect OpenAI (appears as PR comment from github-actions)
OPENAI=$(jq -r '
  .data.repository.pullRequest.comments.nodes[]
  | select(.author.login == "github-actions")
  | select(.createdAt > "'"$PUSH_TIME"'")
  | select(.body | contains("OpenAI Code Review"))
' /tmp/pr_data.json)

# Detect Gemini (same pattern)
GEMINI=$(jq -r '
  .data.repository.pullRequest.comments.nodes[]
  | select(.author.login == "github-actions")
  | select(.createdAt > "'"$PUSH_TIME"'")
  | select(.body | contains("Gemini Code Review"))
' /tmp/pr_data.json)
```

### Failure Detection

```bash
# Check for known failure patterns
FAILURES=$(jq -r '
  .data.repository.pullRequest.comments.nodes[]
  | select(.body | test("API Error|Timeout|503|workflow failed"; "i"))
' /tmp/pr_data.json)

if [ -n "$FAILURES" ]; then
    echo "❌ Review workflow failed"
    exit 1
fi
```

### User Output During Loop

```
⏳ Review check 1/6 - Checking for new reviews...
⏳ No reviews yet (1/6)...

⏳ Review check 2/6 - Checking for new reviews...
⏳ 1/3 reviews ready (Copilot), waiting for others...

⏳ Review check 3/6 - Checking for new reviews...
⏳ 2/3 reviews ready (Copilot, OpenAI), waiting for Gemini...

⏳ Review check 4/6 - Checking for new reviews...
📋 Analyzing 3 review(s)...
🔧 Found 2 item(s) to address. Restarting workflow...

[... workflow restarts ...]

⏳ Review check 1/6 - Checking for new reviews...
📋 Analyzing 3 review(s)...
✅ All reviews passed - no critical issues or actionable items!
```

## Comparison to Alternatives

### Alternative 1: Webhook-based notifications

**Pros:** Instant notification, no polling
**Cons:** Requires webhook infrastructure, not feasible in Claude Code
**Verdict:** Rejected - infrastructure complexity

### Alternative 2: User-triggered checks

**Pros:** User maintains control
**Cons:** Friction, delays, current behavior
**Verdict:** Rejected - this is what we're trying to improve

### Alternative 3: Single check after fixed delay

**Pros:** Simple implementation
**Cons:** Might miss reviews, no retry on issues
**Verdict:** Rejected - doesn't handle variability in CI timing

### Alternative 4: Exponential backoff polling

**Pros:** Adapts to response time
**Cons:** More complex, less predictable
**Verdict:** Rejected - fixed interval is simpler and sufficient

## Edge Cases

### Edge Case 1: Review appears but is empty/malformed

**Detection:** Review body doesn't match expected format
**Action:** Treat as "not ready", continue waiting

### Edge Case 2: Same issue reported by multiple reviewers

**Detection:** Duplicate detection during extraction
**Action:** Deduplicate, count as single item

### Edge Case 3: Context window exhausted mid-loop

**Detection:** Claude Code will signal context limit
**Action:** Exit loop, inform user to continue manually

### Edge Case 4: Network failure during fetch

**Detection:** curl returns error
**Action:** Log warning, count as failed attempt, continue loop

### Edge Case 5: PR closed/merged during loop

**Detection:** PR state changed in response
**Action:** Exit loop, report PR state change

## Decision Rationale

The polling-based approach with 60-second intervals and 10 attempts provides:

1. **Simplicity** - Easy to understand and debug
2. **Reliability** - No external dependencies
3. **Flexibility** - Exit conditions handle all scenarios
4. **User experience** - Progress updates keep user informed

The key insight is that this is a **bounded automation** - it will always terminate, either successfully or with a clear explanation of why it stopped.

## Open Questions

1. **Should we allow user interrupt?** Currently no mechanism to break out of loop.
   - Recommendation: No - loop is max 10 minutes, acceptable to wait

2. **Should we process partial reviews?** If only 2/3 reviews arrive, should we process them?
   - Recommendation: Yes, after timeout - some feedback is better than none

3. **Should we track across sessions?** If user starts new session, should we remember loop state?
   - Recommendation: No - each session is independent, simpler model

## Multi-LLM Review Integration

### Consensus Points (OpenAI)

1. **Author matching is brittle** - Hard-coded `github-actions` misses `github-actions[bot]`
2. **Head SHA anchoring needed** - Time-based filtering alone is insufficient
3. **Global restart cap required** - Prevent infinite loops across cycles
4. **Dedup strategy needed** - Multiple reviewers may flag same issue
5. **Pagination limits dangerous** - `last: 20` may miss reviews on large PRs

### Incorporated Feedback

| Suggestion | Action |
|------------|--------|
| Accept both `github-actions` and `github-actions[bot]` | ✅ Incorporated - Use `contains("github-actions")` |
| Add head SHA anchoring | ✅ Incorporated - Track PR `headRefOid` at loop start |
| Add global restart cap (3 cycles max) | ✅ Incorporated - Exit after 3 full workflow restarts |
| Implement dedup with file:line key | ✅ Incorporated - Normalize items before counting |
| Push first, then comment | ⏭️ Rejected - User requirement is comment-before-push for LLM context |
| Use Checks API instead of comment parsing | ⏭️ Deferred - Comment parsing works, Checks API is enhancement |
| Exponential backoff | ⏭️ Deferred - Fixed 60s is simpler and sufficient for now |
| Persist state in bazinga-db | ⏭️ Deferred - Session-scoped state is acceptable |

### Rejected Suggestions (With Reasoning)

1. **Push first, then comment**
   - User explicitly requested comment-before-push
   - Rationale: LLM reviewers see our responses in their context window
   - We reference the local commit hash which exists after `git commit` but before `git push`

2. **Checks API for workflow status**
   - Valid improvement but adds complexity
   - Comment parsing is working reliably
   - Can be added later as enhancement

### Updated Design (Post-Review)

**Key changes to claude.md implementation:**

1. **Author matching:**
   ```bash
   # Accept both variants
   select(.author.login | test("github-actions"))
   ```

2. **Head SHA tracking:**
   ```bash
   # Get PR head SHA at loop start
   HEAD_SHA=$(jq -r '.data.repository.pullRequest.headRefOid' /tmp/pr_data.json)
   # If HEAD changes mid-loop, restart
   ```

3. **Global restart cap:**
   ```
   max_restarts = 3
   IF restart_count >= max_restarts:
     EXIT with "Max restarts reached"
   ```

4. **Dedup strategy:**
   ```python
   def dedup_key(item):
       return f"{item.file}:{item.line}:{hash(item.message[:50])}"
   ```

## Lessons Learned

(To be filled after implementation)

## References

- claude.md PR workflow section
- GitHub GraphQL API documentation
- Existing LLM review workflow in `.github/workflows/`
- OpenAI review: `tmp/ultrathink-reviews/openai-review.md`
