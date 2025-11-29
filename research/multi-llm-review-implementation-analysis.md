# Multi-LLM Review Implementation: Analysis

**Date:** 2025-11-29
**Context:** Adding external LLM review capability to ULTRATHINK workflow
**Decision:** Implement GPT-5 + Gemini 3 Pro review integration
**Status:** Proposed
**Reviewed by:** Pending (OpenAI GPT-5, Google Gemini 3 Pro)

---

## Problem Statement

When making critical architectural decisions or creating implementation plans, a single perspective (even from a capable AI) can have blind spots. We need a mechanism to get diverse feedback on analysis documents before finalizing them.

## Solution

Integrate OpenAI and Google Gemini APIs to review ULTRATHINK analysis documents:

1. **Keyword trigger** - User says "ultrathink" in their request
2. **Draft creation** - Initial analysis saved to `research/` folder
3. **External review** - Script calls GPT-5 and Gemini 3 Pro with:
   - The analysis document
   - All agent definitions (project context)
   - Optional additional code files
4. **Feedback integration** - Claude reviews both opinions, integrates valid points
5. **Finalization** - Updated document with "Multi-LLM Review Integration" section
6. **Cleanup** - Remove temporary review files

## Critical Analysis

### Pros ✅
- **Multiple perspectives** - Different models catch different issues
- **Reduced bias** - External review challenges assumptions
- **Documented reasoning** - Integration section shows what was considered
- **Automated workflow** - Single script handles both API calls
- **Security** - API key in header, not URL; keys not logged

### Cons ⚠️
- **Latency** - Two sequential API calls add ~10-30 seconds
- **Cost** - Each ultrathink incurs API costs for both providers
- **Context limits** - Large codebases may exceed token limits
- **Dependency** - Requires both API keys to be configured
- **No repo browsing** - External LLMs can't access full codebase

### Verdict

The benefits of diverse feedback outweigh the costs for critical decisions. The implementation is sound with appropriate safeguards (validation, error handling, security).

## Implementation Details

### Script: `dev-scripts/llm-reviews.sh`

**Key features:**
- Cross-platform date function (GNU/BSD compatible)
- Model name validation (URL safety)
- File size warnings (>100KB)
- Temp file for large prompts (avoids cmdline limits)
- HTTP status code checking
- API key in header (X-Goog-Api-Key), not URL
- Cleanup trap for temp files

### Integration in claude.md

The workflow is documented as a MUST instruction triggered by the keyword "ultrathink".

## Comparison to Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Our approach (GPT-5 + Gemini)** | Two diverse perspectives, automated | Cost, latency |
| Single external LLM | Simpler, cheaper | Single perspective |
| No external review | Fast, free | Blind spots |
| Human review | Best quality | Slow, not always available |

## Decision Rationale

1. **Two models > one** - Different training data = different insights
2. **GPT-5 + Gemini** - Leading models from different providers
3. **Keyword trigger** - User controls when to incur cost/latency
4. **dev-scripts/ location** - Not copied to clients (dev-only tool)

## Lessons Learned

1. Always use canonical header names (X-Goog-Api-Key not x-goog-api-key)
2. jq's `//` operator makes null checks redundant
3. Model names need URL validation
4. Cross-platform compatibility requires explicit date formatting

## References

- OpenAI API docs: https://platform.openai.com/docs
- Gemini API docs: https://ai.google.dev/gemini-api/docs
- PR #147: Implementation and review feedback
