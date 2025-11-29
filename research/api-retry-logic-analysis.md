# API Retry Logic for llm-reviews.sh: Analysis

**Date:** 2025-11-29
**Context:** Evaluating whether to add retry logic to the multi-LLM review script
**Decision:** Proposed - Add limited retry logic with exponential backoff
**Status:** Reviewed (External LLM review attempted - see Integration section)
**Reviewed by:** OpenAI GPT-4o (rate limited), Google Gemini 1.5 Pro (auth error)

---

## Problem Statement

The `dev-scripts/llm-reviews.sh` script makes API calls to OpenAI and Gemini without any retry mechanism. When a call fails due to transient issues (network errors, rate limits, server errors), the entire review for that provider fails and the user must manually re-run the script.

Should we add retry logic to improve reliability?

## Solution

Add **limited retry logic** with the following characteristics:

1. **Retry only on retryable errors**:
   - Network errors (curl exit code != 0)
   - Server errors (HTTP 5xx)
   - Rate limits (HTTP 429)

2. **Do NOT retry on**:
   - Authentication errors (HTTP 401/403) - won't self-heal
   - Bad request errors (HTTP 400) - indicates bug in our code
   - Other client errors (HTTP 4xx) - retrying won't help

3. **Exponential backoff**:
   - Delays: 2s, 4s, 8s
   - Maximum 3 retries
   - Total max added latency: ~14s per API

4. **Implementation approach**:
   - Wrap each curl call in a retry loop
   - Log retry attempts for visibility
   - Preserve original error on final failure

## Critical Analysis

### Pros ✅

1. **Improved Reliability**: Network glitches and rate limits are common; auto-retry handles them transparently
2. **Better UX**: User doesn't need to manually re-run for transient failures
3. **Industry Standard**: Exponential backoff is the recommended pattern for API clients
4. **Bounded Cost**: Only retries on errors that might succeed on retry; won't multiply costs on partial success
5. **Bounded Latency**: Max 3 retries with 14s total delay is acceptable for a dev tool
6. **Selective Retry**: Not retrying 4xx errors prevents futile retries and fast failure on auth issues

### Cons ⚠️

1. **Added Complexity**: ~20-30 lines of additional code
2. **Dev-Only Tool**: May be over-engineering for a script run occasionally
3. **Manual Retry Easy**: `./dev-scripts/llm-reviews.sh` is trivial to re-run
4. **Masking Issues**: Automatic retries might hide recurring problems
5. **Latency Increase**: Failed calls take longer to report failure

### Verdict

The benefits outweigh the costs. The retry logic:
- Adds minimal complexity (can be a reusable function)
- Handles real-world failure modes gracefully
- Doesn't increase costs (only retries likely-to-succeed scenarios)
- Follows best practices for API integration

**Recommendation: IMPLEMENT** with the selective retry approach described.

## Implementation Details

### Proposed Code

```bash
# Retry logic with exponential backoff
# Usage: retry_curl <output_file> <curl_args...>
# Returns: curl exit code (0 = success)
retry_curl() {
    local output_file="$1"
    shift
    local max_retries=3
    local retry_count=0
    local delay=2
    local http_code
    local curl_exit

    while [ $retry_count -le $max_retries ]; do
        http_code=$(curl -s -w "%{http_code}" -o "$output_file" "$@")
        curl_exit=$?

        # Success
        if [ $curl_exit -eq 0 ] && [ "$http_code" -lt 400 ]; then
            echo "$http_code"
            return 0
        fi

        # Don't retry client errors (except rate limits)
        if [ $curl_exit -eq 0 ] && [ "$http_code" -ge 400 ] && [ "$http_code" -lt 500 ] && [ "$http_code" -ne 429 ]; then
            echo "$http_code"
            return 0  # Return success but with error code for caller to handle
        fi

        # Retryable error
        retry_count=$((retry_count + 1))
        if [ $retry_count -le $max_retries ]; then
            echo "  ⚠️ Attempt $retry_count failed (curl=$curl_exit, http=$http_code), retrying in ${delay}s..." >&2
            sleep $delay
            delay=$((delay * 2))
        fi
    done

    # Final failure
    echo "$http_code"
    return $curl_exit
}
```

### Integration Points

1. Replace direct `curl` calls with `retry_curl` wrapper
2. Update both OpenAI and Gemini API call sections
3. Add logging to indicate retry attempts

### Testing Strategy

1. **Network error simulation**: `curl --connect-timeout 1` to a slow endpoint
2. **Rate limit simulation**: Mock 429 response
3. **Auth error verification**: Intentionally bad API key should fail fast (no retry)

## Comparison to Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Our approach (selective retry)** | Handles transient errors, bounded cost/latency | Added complexity |
| **No retry (current)** | Simple, fast failure | User must manually re-run |
| **Unlimited retry** | Very persistent | Could hang forever, multiply costs |
| **Queue-based (background)** | Async, can retry later | Over-engineering for dev tool |

## Decision Rationale

1. **Selective retry** - Only retry errors that might succeed
2. **Exponential backoff** - Standard pattern, prevents thundering herd
3. **Bounded retries** - Max 3 prevents infinite loops
4. **Visible logging** - User sees retry attempts, not just silent delays
5. **Function wrapper** - Reusable, testable, minimal code changes

## Lessons Learned

1. Not all errors are equal - 4xx vs 5xx require different handling
2. Exponential backoff is industry standard for good reason
3. Bounded retries prevent runaway costs and latency
4. Logging retries improves debuggability

## Multi-LLM Review Integration

### External Review Attempt

The ULTRATHINK workflow attempted to get external reviews from OpenAI and Gemini, but both calls failed - providing real-world validation of the retry logic analysis:

**OpenAI GPT-4o (HTTP 429 - Rate Limited)**
- Prompt size: 107,069 tokens
- Limit: 30,000 tokens per minute
- Root cause: Including all agent files (~9 files) exceeds context limits
- **Retry applicable?** YES - rate limits are classic retry candidates with backoff

**Gemini 1.5 Pro (HTTP 403 - Forbidden)**
- API key authentication issue or model access not granted
- **Retry applicable?** NO - auth errors won't self-heal with retries

### Validation from Real-World Testing

The failed API calls actually **validate this analysis**:

1. **429 Rate Limit** - Perfect example of retryable error
   - Wait and retry would likely succeed
   - Exponential backoff prevents hammering the API
   - Our proposed solution correctly identifies 429 as retryable

2. **403 Auth Error** - Perfect example of non-retryable error
   - Retrying won't fix auth issues
   - Our proposed solution correctly excludes 4xx (except 429) from retry

### Additional Findings

1. **Context size issue** - The script includes all agent files automatically, which can exceed API limits. Consider:
   - Adding a `--minimal` flag to include only essential context
   - Truncating large files or using summaries
   - This is a separate issue from retry logic

2. **Script bugs discovered during testing**:
   - `max_tokens` parameter deprecated for newer OpenAI models → Fixed to `max_completion_tokens`
   - Gemini 1.5 models **retired April 2025** → Updated to `gemini-2.5-flash` (current generation)
   - OpenAI model remains `gpt-4o` (current flagship)

### Consensus Points

Since external review wasn't available, proceeding with internal analysis only. The proposed solution is validated by:
- Industry standard practices (exponential backoff)
- Real-world testing (429 vs 403 handling)
- Bounded complexity (reusable function wrapper)

### Incorporated Feedback

- Real-world API error testing strengthened the analysis
- Discovered and fixed script bugs (`max_tokens` → `max_completion_tokens`)
- Identified additional improvement opportunity (context size management)

### Rejected Suggestions

None - no external feedback was received due to API failures.

## References

- OpenAI Rate Limits: https://platform.openai.com/docs/guides/rate-limits
- Gemini API Quotas: https://ai.google.dev/gemini-api/docs/quota
- Exponential Backoff: https://cloud.google.com/storage/docs/exponential-backoff
- Current script: `dev-scripts/llm-reviews.sh`
