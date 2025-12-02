# Review Loop Improvements: Adaptive Timeout and Workflow Recovery

**Date:** 2025-12-02
**Context:** Enhancing autonomous review loop with workflow recovery and adaptive behavior
**Decision:** Implement 10-minute timeout, workflow rerun on 503, and early-start optimization
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

Current review loop has several limitations discovered during testing:

1. **6-minute timeout too short** - Copilot reviews often take longer, causing premature exits
2. **No recovery from 503 errors** - Gemini API failures leave reviews incomplete
3. **Inefficient waiting** - When OpenAI+Gemini are ready with issues, we wait unnecessarily for Copilot

**Goal:** Make the review loop more resilient and efficient while maintaining bounded execution.

## Proposed Changes

### Change 1: Extend Timeout to 10 Minutes

**Rationale:**
- Copilot reviews observed to take 5-8 minutes in some cases
- 10 minutes provides buffer for cold starts and queue delays
- Still bounded - won't run indefinitely

**Implementation:**
```python
max_attempts = 10  # 10 x 60s = 10 minutes
```

### Change 2: Workflow Rerun on 503 Error

**Observed failure pattern:**
```
## Gemini Code Review
_Reviewed commit: a4985ff_
## ⚠️ Gemini API Error (HTTP 503)
```

**Recovery mechanism:**
1. Detect 503/timeout in review comment
2. Find the failed workflow run
3. Trigger rerun via REST API
4. Reset the attempt counter for that reviewer

**Commands to rerun a workflow:**
```bash
GITHUB_TOKEN="${BAZINGA_GITHUB_TOKEN:-$(cat ~/.bazinga-github-token 2>/dev/null)}"

# Step 1: Find failed workflow run by name and head_sha
FAILED_RUN=$(curl -sSf -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/mehdic/bazinga/actions/runs?event=pull_request&head_sha=$HEAD_SHA" | \
  jq -r '.workflow_runs[] | select(.name == "Gemini PR Review") | .id')

# Step 2: Trigger rerun
curl -sSf -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/mehdic/bazinga/actions/runs/$FAILED_RUN/rerun"

# Step 3: Reset attempt counter for this reviewer
gemini_attempts = 0
```

### Change 3: Early-Start Optimization

**Current behavior:** Wait for all 3 reviews before processing
**Problem:** If Copilot is slow but OpenAI+Gemini have actionable issues, we waste time

**New behavior:**
```
IF openai_ready AND gemini_ready:
    IF has_actionable_issues(openai, gemini):
        # Start fixing immediately, reset timer after push
        process_issues()
        push_fixes()
        reset_timer()  # Full 10 minutes for next cycle
    ELSE:
        # No issues in available reviews - wait for Copilot
        continue_waiting()
```

**Rationale:**
- Copilot inline comments are valuable but often duplicative of OpenAI/Gemini
- Starting fixes earlier reduces total cycle time
- Timer reset ensures we still catch Copilot review in next cycle

### Change 4: Wait-for-All on Success

**Scenario:** OpenAI and Gemini both pass with 0 critical issues
**Current behavior:** Could exit early, missing Copilot feedback
**New behavior:** Wait full 10 minutes before declaring success

```
IF openai_ready AND gemini_ready AND NOT has_issues:
    # Wait for Copilot up to timeout
    continue_waiting_until_timeout_or_copilot()
```

## Critical Analysis

### Pros

1. **More resilient** - Recovers from transient API failures
2. **More efficient** - Starts fixes sooner when possible
3. **More thorough** - Waits for all reviews on success path
4. **Still bounded** - 10 minutes max, 3 restart cycles max

### Cons

1. **Longer maximum wait** - 10 min vs 6 min
2. **More complex logic** - Additional state tracking
3. **API calls for rerun** - Extra GitHub API interaction

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Workflow rerun fails | Low | Medium | Log warning, continue without that review |
| Early-start creates thrash | Medium | Medium | Only start if actionable issues exist |
| 10 min still too short | Low | Low | User can manually continue |

### Verdict

**IMPLEMENT** - Benefits outweigh complexity. The early-start optimization is the key improvement.

## Implementation Details

### Updated Loop State

```python
class ReviewLoopState:
    push_commit: str
    push_time: datetime
    head_sha: str
    attempts: int
    max_attempts: int = 10  # Changed from 6
    restart_count: int
    max_restarts: int = 3

    # Per-reviewer tracking (new)
    openai_ready: bool
    gemini_ready: bool
    copilot_ready: bool
    openai_has_503: bool  # Track failures
    gemini_has_503: bool

    # Workflow rerun tracking (new)
    gemini_rerun_triggered: bool = False
    openai_rerun_triggered: bool = False
```

### Updated Loop Procedure

```
LOOP_START:
  IF restart_count >= max_restarts:
    EXIT with "Max restarts reached"

  attempts = 0
  openai_ready = gemini_ready = copilot_ready = False
  gemini_rerun_triggered = openai_rerun_triggered = False

  WHILE attempts < max_attempts:
    sleep 60 seconds
    attempts += 1

    output: "⏳ Review check {attempts}/10 - Checking for new reviews..."

    fetch_reviews()

    # Check for 503 errors and trigger reruns
    IF gemini_has_503 AND NOT gemini_rerun_triggered:
      output: "🔄 Gemini API failed (503). Triggering workflow rerun..."
      rerun_workflow("Gemini PR Review")
      gemini_rerun_triggered = True
      gemini_ready = False  # Wait for new review

    IF openai_has_503 AND NOT openai_rerun_triggered:
      output: "🔄 OpenAI API failed. Triggering workflow rerun..."
      rerun_workflow("OpenAI PR Review")
      openai_rerun_triggered = True
      openai_ready = False

    # Check review status
    update_review_status()  # Sets openai_ready, gemini_ready, copilot_ready

    reviews_ready = count([openai_ready, gemini_ready, copilot_ready])
    output: "⏳ {reviews_ready}/3 reviews ready"

    # EARLY-START OPTIMIZATION
    IF openai_ready AND gemini_ready:
      items = extract_items(openai, gemini)

      IF has_actionable_issues(items):
        output: "🔧 OpenAI+Gemini have {len(items)} issues. Starting fixes (not waiting for Copilot)..."
        process_and_fix(items)
        push_fixes()
        restart_count += 1
        GOTO LOOP_START  # Reset timer for next cycle

      ELSE IF copilot_ready:
        # All 3 ready, no issues
        output: "✅ All reviews passed!"
        EXIT LOOP

      ELSE:
        # OpenAI+Gemini passed, waiting for Copilot
        output: "⏳ OpenAI+Gemini passed. Waiting for Copilot ({attempts}/10)..."
        CONTINUE

    # Not enough reviews yet
    CONTINUE

  # Timeout reached
  output: "⏱️ Timeout (10 minutes). Processing available reviews..."
  process_available_reviews()
  EXIT LOOP
```

### Workflow Rerun Function

```bash
rerun_workflow() {
  WORKFLOW_NAME=$1
  GITHUB_TOKEN="${BAZINGA_GITHUB_TOKEN:-$(cat ~/.bazinga-github-token 2>/dev/null)}"

  # Find the workflow run
  RUN_ID=$(curl -sSf -H "Authorization: Bearer $GITHUB_TOKEN" \
    "https://api.github.com/repos/mehdic/bazinga/actions/runs?event=pull_request&head_sha=$HEAD_SHA" | \
    jq -r ".workflow_runs[] | select(.name == \"$WORKFLOW_NAME\") | .id")

  if [ -n "$RUN_ID" ]; then
    # Trigger rerun
    RESPONSE=$(curl -sSf -X POST \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      "https://api.github.com/repos/mehdic/bazinga/actions/runs/$RUN_ID/rerun" 2>&1)

    if [ $? -eq 0 ]; then
      echo "✅ Workflow rerun triggered: $WORKFLOW_NAME (Run ID: $RUN_ID)"
      return 0
    else
      echo "⚠️ Failed to rerun workflow: $RESPONSE"
      return 1
    fi
  else
    echo "⚠️ Could not find workflow run for: $WORKFLOW_NAME"
    return 1
  fi
}
```

## Decision Matrix

| Scenario | OpenAI | Gemini | Copilot | Action |
|----------|--------|--------|---------|--------|
| All pass | ✅ 0 issues | ✅ 0 issues | ✅ 0 issues | EXIT success |
| OpenAI+Gemini pass, Copilot missing | ✅ 0 issues | ✅ 0 issues | ⏳ waiting | WAIT until timeout |
| OpenAI+Gemini have issues | 🔧 issues | 🔧 issues | any | START FIXING (early) |
| Gemini 503 | any | ❌ 503 | any | RERUN workflow |
| Timeout, partial reviews | ✅/🔧 | ✅/🔧 | ⏳ missing | PROCESS available |

## Comparison to Current Design

| Aspect | Current | Proposed |
|--------|---------|----------|
| Timeout | 6 minutes | 10 minutes |
| 503 handling | Exit, inform user | Auto-rerun workflow |
| Early start | No | Yes, if OpenAI+Gemini have issues |
| Wait on success | Exit when 2/3 pass | Wait for all 3 |

## Open Questions

1. **Should we rerun more than once?** Current: No, only one rerun attempt per reviewer
   - Recommendation: Single rerun is sufficient; if it fails again, likely systemic issue

2. **What if Copilot has issues but OpenAI+Gemini passed?**
   - Recommendation: Process Copilot issues in next cycle (timer was reset)

3. **Should early-start threshold be configurable?**
   - Recommendation: No, keep it simple - any actionable issue triggers early start

## Multi-LLM Review Integration

### Consensus Points (OpenAI)

1. **Use workflow run status, not comment parsing** - More reliable than parsing for "503" strings
2. **Quorum+grace policy** - Don't wait full timeout if 2/3 pass; use shorter grace period
3. **Per-run rerun cap** - Only attempt one rerun per workflow to prevent loops
4. **Head SHA sync after push** - Must update tracking after pushing fixes
5. **Robust workflow selection** - Use workflow file path, not name matching

### Incorporated Feedback

| Suggestion | Action |
|------------|--------|
| Use workflow run conclusion instead of comment parsing | ✅ Incorporated - Check `conclusion: failure` on workflow run |
| Add quorum+grace (2 of 3 with short wait) | ✅ Incorporated - 3-minute grace after 2/3 pass |
| Per-run rerun cap of 1 | ✅ Incorporated - `rerun_triggered` flags prevent double-rerun |
| Head SHA sync after push | ✅ Incorporated - Clear provider flags, update head_sha |
| Use workflow file path for selection | ✅ Incorporated - Filter by `.path` not `.name` |
| Use Checks API instead of comments | ⏭️ Deferred - Comment parsing works; Checks API is enhancement |
| Exponential backoff with jitter | ⏭️ Deferred - Fixed 60s interval is simpler and sufficient |
| Persist loop state to disk | ⏭️ Deferred - Session-scoped state is acceptable |
| Provider presence detection | ⏭️ Deferred - Hardcoded 3 providers for now |
| Central aggregator check-run | ⏭️ Deferred - Nice-to-have for future |

### Rejected Suggestions (With Reasoning)

1. **Event-driven model over polling**
   - Requires webhook infrastructure not available in Claude Code environment
   - Polling is simple and bounded

2. **Max 30-45 minute total runtime**
   - 10 minutes x 3 restarts = 30 min is already implicit
   - Adding explicit cap adds complexity without benefit

3. **Rate-limit handling with ETag headers**
   - GitHub rate limits are high enough for our use case (5000/hour)
   - Adding rate-limit logic is premature optimization

### Updated Design (Post-Review)

**Key improvements from review:**

1. **Quorum+grace policy:**
   ```
   IF openai_ready AND gemini_ready AND NOT has_issues:
     # Wait 3-minute grace period for Copilot (not full 10 min)
     grace_attempts = 0
     WHILE grace_attempts < 3:  # 3 minutes
       IF copilot_ready:
         EXIT success
       sleep 60
       grace_attempts += 1
     # Grace expired - proceed with 2/3 pass
     EXIT success (with note: "Copilot review not received")
   ```

2. **Workflow failure detection via API:**
   ```bash
   # Check if workflow failed (not just comment parsing)
   FAILED=$(curl -sSf -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/mehdic/bazinga/actions/runs?head_sha=$HEAD_SHA" | \
     jq -r ".workflow_runs[] | select(.path == \".github/workflows/gemini-pr-review.yml\") | select(.conclusion == \"failure\") | .id")
   ```

3. **Head SHA sync after push:**
   ```
   push_fixes()
   head_sha = get_new_head_sha()  # Must update!
   openai_ready = gemini_ready = copilot_ready = False  # Clear flags
   restart_count += 1
   GOTO LOOP_START
   ```

## References

- Previous design: `research/autonomous-review-loop-design.md`
- GitHub Actions API: workflow reruns
- Observed 503 failures in PR #156
- OpenAI review: `tmp/ultrathink-reviews/openai-review.md`
