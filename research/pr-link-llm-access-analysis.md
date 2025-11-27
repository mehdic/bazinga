# PR Link Access: Can LLMs Review PRs via URL?

**Date:** 2025-11-27
**Context:** Testing whether OpenAI/Gemini APIs can access GitHub PR links
**Decision:** Continue using diff-in-prompt approach (correct)
**Status:** Validated

---

## Question

> Do the PR review pipelines (Gemini and OpenAI) send the PR link with instructions to review the history? Would that work?

## Answer

**No, we do NOT send PR links to the LLMs.** And it would NOT work if we did.

## Current Implementation

Both pipelines (`.github/workflows/openai-pr-review.yml` and `.github/workflows/gemini-pr-review.yml`) work as follows:

1. **Checkout repository** in GitHub Actions runner
2. **Compute git diff** locally: `git diff origin/$base_ref...HEAD`
3. **Fetch previous reviews** from PR comments (their own previous feedback)
4. **Build prompt** that includes the actual diff content
5. **Send prompt** with content to LLM API
6. **Post review** as PR comment

## Why PR Links Would NOT Work

### Technical Limitation

API-based LLMs (OpenAI, Gemini, Claude, etc.) **cannot browse the web** when called via API:

| Capability | ChatGPT Web UI | API Calls |
|------------|---------------|-----------|
| Web browsing | ✅ Yes (with plugins/browsing) | ❌ No |
| URL access | ✅ Can fetch pages | ❌ Cannot fetch |
| Real-time data | ✅ With tools | ❌ Only prompt content |

When you call `POST /v1/chat/completions`, the model can only process:
- The system prompt you send
- The user messages you send
- That's it.

### What Would Happen

If we sent:
```
Please review this PR: https://github.com/mehdic/bazinga/pull/129
```

The model would either:
1. **Honestly admit**: "I cannot access URLs or browse the web"
2. **Hallucinate**: Fabricate a fake review based on the URL pattern

Neither is useful for actual code review.

## Verification Test

Created `tests/test_pr_link_access.py` that:
1. Sends a PR link to OpenAI/Gemini APIs
2. Asks the model to review the code
3. Verifies the model admits it cannot access the URL

### Running the Test

```bash
# Locally (with API keys)
OPENAI_API_KEY=xxx GEMINI_API_KEY=xxx python tests/test_pr_link_access.py

# Via GitHub Actions (uses repository secrets)
gh workflow run test-pr-link-access.yml
```

### Expected Output

```
TEST: Can OpenAI access a GitHub PR link?
PR URL: https://github.com/mehdic/bazinga/pull/129

OpenAI Response:
I cannot access external URLs or browse the web. I can only
analyze content that is directly provided to me in our conversation.
To review this PR, please paste the diff or relevant code changes.

✅ CONFIRMED: OpenAI API cannot access PR links directly
```

## Correct Architecture

The current implementation is correct:

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Actions                         │
│                                                         │
│  1. git diff origin/main...HEAD > diff.patch           │
│  2. Build prompt with actual diff content               │
│  3. Call LLM API with prompt                            │
│  4. Post response as PR comment                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
          │                           ▲
          │ POST /v1/chat/completions │
          │ {                         │
          │   messages: [             │
          │     { content: "Review:   │
          │       ```diff             │
          │       +new code           │
          │       -old code           │
          │       ```"                │
          │     }                     │ Response with
          │   ]                       │ code review
          │ }                         │
          ▼                           │
┌─────────────────────────────────────────────────────────┐
│                    LLM API                              │
│                                                         │
│  - Processes only content in prompt                     │
│  - Cannot access URLs                                   │
│  - Cannot browse the web                                │
│  - Reviews the diff you send it                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Alternatives Considered

### Option 1: Send PR link (rejected)
- ❌ LLMs cannot access URLs via API
- ❌ Would result in hallucinated or refused reviews

### Option 2: Use MCP/Tools (possible but complex)
- Some LLMs support tool calling that could fetch URLs
- Would require custom tool implementation
- Adds complexity with minimal benefit
- GitHub Actions can fetch content more reliably

### Option 3: Current approach - diff in prompt (chosen) ✅
- ✅ Reliable - content is guaranteed available
- ✅ Fast - no additional network calls from model
- ✅ Simple - standard API usage
- ✅ Secure - no need to give model web access

## What About PR History?

The current implementation includes **previous review comments** in the prompt:

```yaml
- name: Fetch previous OpenAI reviews from PR
  run: |
    gh api "repos/${{ github.repository }}/issues/$PR_NUMBER/comments" \
      --jq '[.[] | select(.body | contains("## OpenAI Code Review"))] | last | .body' \
      > previous_openai_review.txt
```

This gives the model context about:
- Issues it previously raised
- Whether those issues were fixed
- Avoiding duplicate feedback

But it's still **content fetched by GitHub Actions**, not the model accessing URLs.

## Conclusion

The current pipeline architecture is correct:
1. GitHub Actions fetches all needed content (diff, previous reviews)
2. Content is sent directly in the prompt
3. LLM processes only what it receives
4. No URL access needed or possible

Sending PR links would not work due to fundamental API limitations.

## References

- `.github/workflows/openai-pr-review.yml`
- `.github/workflows/gemini-pr-review.yml`
- `tests/test_pr_link_access.py`
- OpenAI API docs: https://platform.openai.com/docs/api-reference
- Gemini API docs: https://ai.google.dev/gemini-api/docs
