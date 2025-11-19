# Codebase Analysis Skill - Usage Reference

**Version:** 1.0.0
**Last Updated:** 2025-11-19

---

## Cache Behavior

The skill maintains an intelligent cache to improve performance:

- **Project-wide patterns**: Cached for 1 hour (shared across sessions)
- **Utilities**: Cached per session
- **Similar features**: Always fresh (task-specific)
- **Cache location**: `bazinga/.analysis_cache/{session_id}/`

**Expected cache efficiency:** 33%+ after first run (measured on BAZINGA project)

**Cache invalidation:**
- Project patterns expire after 1 hour
- Utilities cached until session ends
- Changing session ID creates new cache

---

## Error Handling

If analysis fails or times out:

1. Check if partial results are available
2. Return what was found with error indication
3. Suggest manual exploration as fallback

**Example error response:**
```
ANALYSIS PARTIALLY COMPLETE

⚠️ Warning: Full analysis timed out after 20 seconds

## Partial Results
- Found 2 similar features (may be incomplete)
- Utilities discovery incomplete

Suggestion: Manually explore /auth and /utils directories for patterns

Partial results saved to: bazinga/artifacts/{session_id}/skills/codebase-analysis/report.json
```

---

## Performance Expectations

| Project Size | File Count | Analysis Time | Timeout Recommendation |
|--------------|-----------|---------------|------------------------|
| Small | <1K | <5s | 10-15s |
| Medium | 1K-5K | 5-15s | 20-30s |
| Large | 5K-10K | 15-30s | 30-60s |
| Very Large | >10K | 30-60s+ | 60-120s |

**Performance optimizations:**
- Gitignore filtering (skips node_modules, .git, build dirs)
- File limits (max 1000 files for similarity, 100 for utilities)
- Caching (33%+ efficiency on cached data)
- Timeout mechanism (prevents runaway analysis)

---

## Integration with Developer Workflow

Developers will invoke you:

1. **Before implementation** - to understand patterns
2. **When stuck** - to find similar code
3. **For complex tasks** - to get architectural guidance

Your analysis helps developers:
- Write code consistent with the codebase
- Reuse existing utilities
- Follow established patterns
- Reduce revision cycles

---

## Output Format

**Session-Isolated Artifacts:**

Results are saved to session-isolated directories following BAZINGA conventions:

```
bazinga/artifacts/{session_id}/skills/codebase-analysis/report.json
```

This prevents concurrent sessions from overwriting each other's results.

**JSON Structure:**
```json
{
  "task": "task description",
  "session_id": "bazinga_20251119_100000",
  "timestamp": "2025-11-19T10:00:00",
  "cache_hits": 1,
  "cache_misses": 2,
  "cache_efficiency": "33.3%",
  "timed_out": false,
  "partial_results": false,
  "project_patterns": {
    "test_framework": "pytest",
    "build_system": "setuptools/pip",
    "primary_language": "python"
  },
  "utilities": [
    {
      "name": "EmailService",
      "path": "utils/email.py",
      "functions": ["send_email", "validate_email"],
      "purpose": "Email handling and sending"
    }
  ],
  "similar_features": [
    {
      "file": "auth/register.py",
      "similarity": 0.85,
      "matched_keywords": ["email", "validation", "token"],
      "patterns": ["token-based auth", "database transactions"]
    }
  ],
  "suggested_approach": "Follow patterns from auth/register.py | Reuse EmailService from utils/email.py"
}
```

---

## Important Notes

- You are a **read-only skill** - never modify code
- Focus on **actionable insights**, not exhaustive documentation
- Prioritize **relevance over completeness**
- Always save full results to JSON even if returning summary
- Use session-isolated paths for all outputs and caches
- Respect gitignore patterns to avoid scanning irrelevant files
- Timeout protection prevents long-running analysis from blocking developers

---

## Troubleshooting

### Issue: "Found 0 utilities"

**Cause:** Utility directories don't exist or are filtered by gitignore

**Solution:**
```bash
# Verify skill scans .claude/skills/
grep -n ".claude/skills" .claude/skills/codebase-analysis/scripts/analyze_codebase.py
```

### Issue: "Analysis timed out"

**Cause:** Project has >10K files or slow filesystem

**Solution:**
```bash
# Increase timeout
--timeout 60  # For large projects
--timeout 120  # For very large projects
```

### Issue: "Cache efficiency 0%"

**Cause:** --cache-enabled flag not passed or different session ID

**Solution:**
```bash
# Always use --cache-enabled
--cache-enabled
```

---

**For complete troubleshooting guide, see:** `/home/user/bazinga/research/troubleshooting-orchestrator-context-fix.md`
