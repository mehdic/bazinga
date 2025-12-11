# PM Token Reduction Analysis

**Date:** 2025-12-11
**Context:** `agents/project_manager.md` exceeds 25000 token limit (currently ~25422 tokens)
**Decision:** TBD
**Status:** Proposed

---

## Problem Statement

The `project_manager.md` file is 25422 tokens, exceeding the 25000 token Read limit. This causes the session start hook to fail when loading project context.

**Constraint:** Must reduce by ~422+ tokens WITHOUT removing functionality or creating dependencies on external files that need additional reads.

---

## Current File Analysis

| Metric | Value |
|--------|-------|
| Lines | 2593 |
| Characters | 91856 |
| Tokens (estimated) | ~25422 |
| Target | <25000 tokens |
| Reduction needed | ~2% (422+ tokens) |

---

## Approaches Considered

### ❌ Approach 1: Move Content to Reference Files
**What:** Extract verbose examples to `pm_examples.md`, reference with "See: file"
**Pros:** Significant token reduction in main file
**Cons:**
- Agent must read additional file when needing examples
- Adds latency and token cost at runtime
- Creates fragile dependency
- **User rejected this approach**

### ❌ Approach 2: Aggressive Inline Compression
**What:** Compress examples to single lines, remove formatting
**Pros:** Keeps everything in one file
**Cons:**
- May reduce clarity for the agent
- Risk of losing important nuance
- Already tried partially, still needs more analysis

### ✅ Approach 3: Identify True Redundancy
**What:** Find content that is genuinely duplicated or explained multiple times
**Pros:**
- Removes actual waste, not just reformatting
- No loss of unique information
- No external dependencies
**Cons:**
- Requires careful analysis to avoid removing unique content

### ✅ Approach 4: Remove Obsolete/Unused Sections
**What:** Identify sections that are no longer used or superseded by other mechanisms
**Pros:**
- Clean removal of dead weight
- No impact on functionality
**Cons:**
- Requires domain knowledge to identify what's obsolete

### ✅ Approach 5: Consolidate Similar Sections
**What:** Merge sections that cover the same topic in different places
**Pros:**
- Reduces repetition while keeping information
- Improves document coherence
**Cons:**
- Requires careful merging

---

## Detailed Analysis Plan

### Step 1: Token Count by Section
Break down the file by major sections to identify heaviest areas.

### Step 2: Identify Redundancy
- Find concepts explained multiple times
- Find examples that make the same point
- Find formatting that adds tokens without value

### Step 3: Check for Obsolete Content
- Cross-reference with current orchestrator behavior
- Check if any sections are legacy/unused

### Step 4: Propose Surgical Cuts
- Specific line ranges
- Exact before/after
- Verify no functionality loss

---

## Section-by-Section Token Analysis

### Identified Redundancies

| Location | Issue | Lines Saved | Risk |
|----------|-------|-------------|------|
| **Path B check duplication** | Lines 1046-1058 AND 1098-1130 explain same Path B requirements twice | ~30 lines | LOW - consolidate into one |
| **Investigation examples** | Lines 750-807 have 3 full examples (build, deploy, perf) | ~40 lines | LOW - one full example + brief mentions |
| **Reasoning bash templates** | Lines 2505-2593 show same heredoc pattern 3 times | ~60 lines | LOW - one example + "same pattern for X, Y" |

### Potential Total Savings: ~130 lines (~5% reduction, ~1300 tokens)

---

## Specific Proposals

### Proposal 1: Consolidate Path B Explanations

**Current (redundant):**
- Lines 1046-1058: "Path B Blocker Check" with questions
- Lines 1098-1130: "Path B Strict Requirements" with numbered list + bash

**Proposed:** Keep lines 1098-1130 (more complete), remove lines 1046-1058 (redundant questions)

**Savings:** ~15 lines

---

### Proposal 2: Compress Investigation Examples

**Current (lines 750-807):**
```
Example 1 - Build Failure: [17 lines of markdown]
Example 2 - Deployment Blocker: [17 lines of markdown]
Example 3 - Performance Regression: [17 lines of markdown]
```

**Proposed:**
```
**Example - Build Failure:**
[Keep full example - 17 lines]

**Other scenarios:** Deployment blockers (pods failing health checks), performance regressions (unexplained slowdowns) follow same pattern: describe issue → analyze → set INVESTIGATION_NEEDED → include problem/context/hypothesis for Investigator.
```

**Savings:** ~35 lines

---

### Proposal 3: Compress Reasoning Documentation Bash Templates

**Current (lines 2505-2593):**
- Full heredoc example for "understanding" phase (~25 lines)
- Full heredoc example for "approach" phase (~25 lines)
- Full heredoc example for "completion" phase (~25 lines)

**Proposed:**
```
**Template pattern (use for all phases):**
```bash
cat > /tmp/reasoning_{phase}.md << 'REASONING_EOF'
## {Phase Title}
[Relevant sections based on phase type]
REASONING_EOF

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "project_manager" "{phase}" \
  --content-file /tmp/reasoning_{phase}.md \
  --confidence high
```

**Phase-specific sections:**
- `understanding`: User Request Summary, Scope Assessment, Key Requirements, Success Criteria
- `approach`: Mode, Why This Mode, Task Groups, Developer Allocation
- `completion`: What Was Delivered, Success Criteria Met, Key Decisions, Lessons Learned
```

**Savings:** ~50 lines

---

## Risk Assessment

| Proposal | Risk Level | Why |
|----------|------------|-----|
| Path B consolidation | LOW | Removing true duplication, keeping complete version |
| Investigation examples | LOW | Keeping one full example, pattern is clear |
| Reasoning templates | MEDIUM | PM needs to understand pattern, but one example should suffice |

---

## Implementation Order

1. **Safest first:** Path B consolidation (clear duplication)
2. **Second:** Investigation examples (pattern-based, low risk)
3. **Third:** Reasoning templates (slightly higher risk, verify PM still understands)

---

## Risk Assessment

**High Risk Actions (avoid):**
- Removing any unique decision logic
- Breaking the PM's ability to understand its role
- Creating external file dependencies

**Low Risk Actions (prefer):**
- Removing duplicate explanations of same concept
- Shortening examples while preserving the point
- Removing excessive markdown formatting (extra blank lines, etc.)

---

## Questions to Answer

1. Are there sections that explain the same thing twice?
2. Are there examples that could be shortened without losing meaning?
3. Are there obsolete sections from older versions of the system?
4. Are there formatting inefficiencies (excessive whitespace, verbose markdown)?

---

## Next Steps

1. Run section-by-section token analysis
2. Identify specific redundancies with line numbers
3. Propose exact edits with before/after
4. Get user approval before any changes
5. Make surgical, tested changes

---

## References

- Original file: `agents/project_manager.md` (2593 lines, ~25422 tokens)
- Token limit: 25000
- Reduction needed: ~2% minimum
