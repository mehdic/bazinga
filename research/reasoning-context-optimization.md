# Reasoning Context Optimization: Preserving Value While Managing Context

**Date:** 2025-12-18
**Context:** BAZINGA orchestration exhausts context during parallel agent spawns due to reasoning heredocs in execution traces
**Decision:** TBD - awaiting multi-LLM review
**Status:** Proposed

---

## Problem Statement

### The Constraint
BAZINGA's reasoning system is a key differentiator - it captures agent decision-making for future reference, enabling developers to understand why decisions were made. **This MUST be preserved.**

### The Symptom
Context exhaustion during parallel developer spawns (4 developers = context overflow).

### Root Cause Analysis

When agents save reasoning:
```bash
cat > /tmp/reasoning_understanding.md << 'REASONING_EOF'
## Understanding - Tech Lead Feedback Iteration
### Task Interpretation
Fix 6 issues identified by Tech Lead...
[... 400+ tokens of content ...]
REASONING_EOF

python3 bazinga_db.py save-reasoning ...
```

**The heredoc content appears in the agent's execution trace**, which is returned to the orchestrator. Even though reasoning is saved to DB, the content briefly exists in the orchestrator's context.

### Token Impact (Current)

| Phase | Avg Tokens | Per Developer | 4 Developers |
|-------|------------|---------------|--------------|
| understanding | 400 | 400 | 1,600 |
| approach | 500 | 500 | 2,000 |
| completion | 800 | 800 | 3,200 |
| **Total** | 1,700 | 1,700 | **6,800** |

Add QA + Tech Lead + PM reasoning → easily 15,000+ tokens just for reasoning.

---

## Proposed Solution: Tiered Reasoning Architecture

### Core Insight

Not all reasoning has equal value. We can **tier the storage mechanism** based on value:

| Tier | Content | Storage | In Trace? | Token Cost |
|------|---------|---------|-----------|------------|
| **Tier 1: Critical** | Structured completion summary | DB (compact JSON) | Yes (~100 tokens) | Low |
| **Tier 2: Valuable** | Detailed reasoning | File artifact | No | Zero |
| **Tier 3: Optional** | Understanding/approach | File only (not DB) | No | Zero |

### Implementation Design

#### Tier 1: Compact Completion (Always in DB)

Replace verbose markdown with structured JSON:

**Before (600-1200 tokens):**
```markdown
## Completion Summary - Tech Lead Feedback Fixes

### What Was Done

#### 1. Created earningsSlice.ts with ALL fixes applied
- **ISSUE 1 FIXED**: Removed all `any` types in error handling (5 locations)
  - Used proper pattern: `error instanceof Error ? error.message : 'An unknown error occurred'`
  - Applied to all 5 async thunks
... [60+ more lines]
```

**After (80-150 tokens):**
```json
{
  "phase": "completion",
  "group_id": "DEL-INIT",
  "summary": "Fixed 6 Tech Lead issues: removed any types, added async thunk tests, memoized selectors",
  "files_modified": ["earningsSlice.ts", "earningsSlice.test.ts"],
  "files_created": [],
  "metrics": {
    "tests_passed": 51,
    "tests_failed": 0,
    "coverage": "94%"
  },
  "key_decisions": [
    "Used instanceof Error pattern for type-safe error handling",
    "Added createSelector for memoized selectors"
  ],
  "concerns": [],
  "details_file": "bazinga/artifacts/{session}/DEL-INIT_completion.md"
}
```

**Savings: 500-1000 tokens per agent**

#### Tier 2: Detailed Reasoning (File Artifact)

Agent writes verbose reasoning to file **before** the compact save:

```bash
# Step 1: Write detailed reasoning to artifact file (NOT in heredoc)
Write(
  file_path: "bazinga/artifacts/{SESSION_ID}/{GROUP_ID}_completion.md",
  content: "[Full verbose reasoning with all details]"
)

# Step 2: Save compact summary to DB (small heredoc)
cat > /tmp/reasoning_compact.json << 'EOF'
{"phase":"completion","summary":"...","details_file":"bazinga/artifacts/..."}
EOF

python3 bazinga_db.py save-reasoning --compact --content-file /tmp/reasoning_compact.json
```

The `Write` tool output is minimal (just confirmation), but the full content is preserved in the artifact file.

#### Tier 3: Optional Expansion (Understanding/Approach)

For understanding and approach phases:
- **Default:** Disabled (not saved at all)
- **On failure:** Automatically captured for debugging
- **On request:** Can be enabled via skills_config.json

```json
// bazinga/skills_config.json
{
  "reasoning": {
    "mode": "compact",  // "full" | "compact" | "disabled"
    "phases": {
      "understanding": "on_failure",  // "always" | "on_failure" | "disabled"
      "approach": "on_failure",
      "completion": "always"
    }
  }
}
```

### File Structure

```
bazinga/artifacts/{session_id}/
├── DEL-INIT_completion.md      # Full verbose completion reasoning
├── DEL-INIT_understanding.md   # Only if failure or explicitly enabled
├── DEL-LIST_completion.md
├── DEL-GPS_completion.md
└── reasoning_index.json        # Quick lookup of all reasoning files
```

### Database Schema Enhancement

```sql
-- Existing reasoning_log table, add columns:
ALTER TABLE reasoning_log ADD COLUMN format TEXT DEFAULT 'markdown';  -- 'markdown' | 'json'
ALTER TABLE reasoning_log ADD COLUMN artifact_path TEXT;  -- Path to detailed file
ALTER TABLE reasoning_log ADD COLUMN token_count INTEGER;  -- For tracking
```

### Token Budget Enforcement

Add to agent prompts:
```markdown
## Reasoning Budget

Your completion reasoning MUST fit within **150 tokens** when saved to DB.
Use the structured JSON format below. For detailed explanations, write to the artifact file.

**Compact format (required):**
- summary: 1-2 sentences (max 50 tokens)
- files_modified/created: array of filenames only
- metrics: numbers only
- key_decisions: max 3 items, 1 sentence each
- concerns: max 2 items

**If you need more space:** Write details to artifact file first, then summarize.
```

---

## Alternative Solutions Considered

### Alternative A: Post-Completion Extraction
**Approach:** Agent saves nothing inline. After completion, parse Claude Code transcripts to extract reasoning.
**Pros:** Zero context cost
**Cons:** Relies on transcript format (fragile), loses explicit reasoning structure, complex implementation
**Verdict:** Rejected - too fragile and loses intentional reasoning

### Alternative B: Background Reasoning Pipeline
**Approach:** Agent returns status only. Background process monitors queue and extracts reasoning.
**Pros:** Complete decoupling
**Cons:** Complex architecture, race conditions, delayed availability
**Verdict:** Rejected - over-engineered for the problem

### Alternative C: Aggressive Token Limits Only
**Approach:** Keep current format but enforce 100-token limit
**Pros:** Simple change
**Cons:** Loses valuable detail, hard to enforce prose limits
**Verdict:** Partially incorporated - limits are part of solution

### Alternative D: Reasoning as Return Value (Not Heredoc)
**Approach:** Agent returns reasoning in final message, orchestrator saves to DB
**Pros:** No heredoc in trace
**Cons:** Reasoning briefly in orchestrator context anyway, complex parsing
**Verdict:** Rejected - doesn't solve the core problem

### Alternative E: Base64 Encoding
**Approach:** Encode reasoning as base64 to reduce trace size
**Pros:** Smaller trace
**Cons:** Still in trace, adds encode/decode complexity, not human-readable in logs
**Verdict:** Rejected - complexity without sufficient benefit

---

## Implementation Plan

### Phase 1: Reasoning Configuration (1 task)
1. Add reasoning config to `bazinga/skills_config.json`
2. Update bazinga-db skill to read config
3. Add `--compact` flag to save-reasoning command

### Phase 2: Agent Prompt Updates (1 task per agent)
1. Update developer.md with new reasoning protocol
2. Update qa_expert.md
3. Update tech_lead.md
4. Update project_manager.md
5. Update senior_software_engineer.md

### Phase 3: Artifact Writing (1 task)
1. Add artifact writing step before compact save
2. Create reasoning_index.json generator
3. Update inspect-reasoning.sh to show both DB and files

### Phase 4: Dashboard Updates (1 task)
1. Add reasoning detail viewer (fetches from artifact files)
2. Add compact vs full toggle
3. Show token counts

---

## Expected Outcomes

### Token Savings

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| 1 Developer | 1,700 | 150 | 91% |
| 4 Developers (parallel) | 6,800 | 600 | 91% |
| Full cycle (Dev→QA→TL→PM) | 5,100 | 450 | 91% |
| 10 task groups | 51,000 | 4,500 | 91% |

### Value Preserved

| Feature | Before | After |
|---------|--------|-------|
| Completion reasoning | ✅ Verbose in DB | ✅ Compact in DB + Verbose in file |
| Understanding reasoning | ✅ Always | ⚠️ On failure only (configurable) |
| Queryable summaries | ❌ Markdown parsing needed | ✅ Structured JSON |
| Token tracking | ❌ Unknown | ✅ Explicit counts |
| Audit trail | ✅ Full | ✅ Full (DB + files) |

---

## Critical Analysis

### Pros ✅
1. **91% token reduction** - Solves context exhaustion
2. **Preserves all reasoning** - Just in different tiers
3. **Better queryability** - JSON vs markdown
4. **Configurable** - Teams can choose full/compact/disabled
5. **Backward compatible** - Old reasoning still readable
6. **Adds value** - Token tracking, structured data

### Cons ⚠️
1. **Two storage locations** - DB + files (complexity)
2. **Agent prompt changes** - All 5+ agents need updates
3. **Dashboard changes** - Need file fetching
4. **Migration** - Existing sessions use old format

### Risks
1. **Agents ignore compact format** - Mitigation: Validation in bazinga-db skill
2. **File artifacts lost** - Mitigation: Include in git, backup strategy
3. **Format drift** - Mitigation: JSON schema validation

### Verdict

**RECOMMENDED** - This solution achieves 91% token savings while preserving 100% of reasoning value. The tiered approach is pragmatic: critical info in DB (fast, queryable), details in files (complete, archival). The complexity cost (dual storage) is justified by the benefits.

---

## Open Questions for Review

1. Should understanding/approach phases be completely removed or just moved to "on failure" mode?
2. Is 150 tokens sufficient for compact completion? Or should it be 200?
3. Should artifact files be committed to git or gitignored?
4. Should we add a "reasoning budget exceeded" warning to agents?

---

## References

- Original context exhaustion incident: Session bazinga_20251215_103357
- inspect-reasoning.sh analysis showing 14 entries, 1200+ tokens each
- Claude Code Task tool documentation on execution traces
