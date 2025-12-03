# Orchestrator Optimization: Capsules and Context Packages

**Date:** 2025-12-03
**Context:** Evaluating AI agent's proposal to optimize orchestrator.md size
**Decision:** Revise approach - focus on runtime tokens, not file size
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

orchestrator.md is 100KB (2,662 lines) and approaching Claude's context window limits. An AI agent proposed two optimizations:

1. Move Context Package Examples to Template (~5-8k savings claimed)
2. Consolidate Duplicate Capsule Formats (~3-5k savings claimed)

This document critically evaluates these proposals.

---

## Current State Analysis

### File Sizes

| File | Size | Lines |
|------|------|-------|
| `agents/orchestrator.md` | 100,366 bytes | 2,662 |
| `bazinga/templates/message_templates.md` | 21,134 bytes | 688 |
| `bazinga/templates/response_parsing.md` | 15,909 bytes | 500+ |
| `bazinga/templates/prompt_building.md` | 5,185 bytes | 150+ |

### Template Loading Pattern

The orchestrator already loads templates at initialization (lines 673-680):

```markdown
**⚠️ MANDATORY: Read templates that contain runtime instructions**

Read(file_path: "bazinga/templates/message_templates.md")
Read(file_path: "bazinga/templates/response_parsing.md")
Read(file_path: "bazinga/templates/prompt_building.md")
```

And references them throughout:
- Line 59: "You loaded message templates... Use those exact formats"
- Line 99: "Use `bazinga/templates/response_parsing.md` (loaded at init)"
- Line 1284: "Use the Developer Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization)"

**This pattern already exists and works.**

---

## Proposal 1: Move Context Package Examples to Template

### Claimed Savings: 5-8KB

### Actual Measurement

Context Package section (lines 1229-1275): **~2KB**

The claim of 5-8KB is inaccurate.

### Content Analysis

The Context Package section contains:

```markdown
**🔴 Context Package Query (MANDATORY before spawn):**

Query available context packages for this agent:
bazinga-db, please get context packages:

Session ID: {session_id}
Group ID: {group_id}
Agent Type: {developer|senior_software_engineer|requirements_engineer}
Limit: 3

**Context Package Routing Rules:**
| Query Result | Action |
|--------------|--------|
| Packages found (N > 0) | Validate file paths, then include Context Packages table in prompt |
| No packages (N = 0) | Proceed without context section |
| Query error | Log warning, proceed without context (non-blocking) |
```

**This is NOT reference documentation** - it's procedural workflow embedded in Step 2A.1 (spawn developer). Moving it would:

1. Break the workflow flow (Step 2A.1 → Step 2A.2)
2. Require LLM to cross-reference during critical spawn operation
3. Risk the step being skipped if template not loaded

### Verdict: ❌ NOT RECOMMENDED

**Reasons:**
- Wrong size estimate (2KB not 5-8KB)
- Content is procedural, not reference
- Already has parallel mode reference ("see Simple Mode §Context Package Routing Rules")
- Moving would fragment critical workflow

---

## Proposal 2: Consolidate Duplicate Capsule Formats

### Claimed Savings: 3-5KB

### Actual Duplications Found

Capsule formats appear at:

| Location | Lines | Content |
|----------|-------|---------|
| message_templates.md | All | CANONICAL source |
| orchestrator.md L61-89 | 28 | Core format + examples |
| orchestrator.md L1293-1315 | 22 | Developer capsule templates |
| orchestrator.md L1449-1466 | 17 | QA capsule templates |
| orchestrator.md L1557-1574 | 17 | Tech Lead capsule templates |
| orchestrator.md L2254-2257 | 4 | Parallel mode reference |

**Total duplicated content: ~4-5KB** (estimate accurate)

### Why Duplications Exist

Each workflow step has inline capsule templates for the LLM to use immediately:

```markdown
### Step 2A.2: Receive Developer Response

IF status = READY_FOR_QA OR READY_FOR_REVIEW:
  → Use "Developer Work Complete" template:
  ```
  🔨 Group {id} [{tier}/{model}] complete | {summary}, {file_count} files modified, {test_count} tests added ({coverage}% coverage) | {status} → {next_phase}
  ```
```

The LLM can apply this immediately without searching loaded templates.

### Trade-off Analysis

| Keep Inline | Extract to Template |
|-------------|---------------------|
| ✅ Immediate access | ❌ Requires lookup in loaded context |
| ✅ No latency | ❌ May increase token usage searching |
| ✅ Clear step→format mapping | ❌ Mapping becomes fragmented |
| ❌ 4-5KB duplication | ✅ 4-5KB savings |
| ❌ Risk of drift | ✅ Single source of truth |

### Critical Question: Does the LLM Actually Use Loaded Templates?

Testing required to determine if the LLM:
1. Reliably references loaded templates when told "use template X"
2. Or needs inline examples to follow formats correctly

**Observation:** The current pattern mixes both - it says "Use template (loaded at init)" AND provides inline examples. This suggests uncertainty about template reference reliability.

### Hybrid Approach (Recommended if optimizing)

Instead of full extraction:

1. **Keep ONE canonical format at the top** (already exists at lines 61-89)
2. **Replace step-specific duplicates with status→action mappings:**

```markdown
### Step 2A.2: Receive Developer Response

**Status → Action mapping:**
| Status | Template | Next |
|--------|----------|------|
| READY_FOR_QA | Developer Complete (§UI) | QA spawn |
| READY_FOR_REVIEW | Developer Complete (§UI) | Tech Lead |
| PARTIAL | Work in Progress (§UI) | Continue |
| BLOCKED | Blocker (§UI) | Investigate |

Apply template from §UI Status Messages, then continue to Step 2A.3.
```

**Savings:** ~3KB (keeps mappings, removes format strings)
**Risk:** Medium (requires LLM to look up §UI section)

### Verdict: ⚠️ PARTIALLY VALID

**Valid:**
- Duplications exist (~4-5KB)
- Template reference pattern already established

**Concerns:**
- May degrade LLM performance on format consistency
- Requires testing to verify LLM reliably uses §references
- May not be worth the complexity for 4KB savings

---

## Alternative Optimizations (Higher Impact)

If the goal is reducing orchestrator.md size, better targets exist:

| Section | Lines | Est. Size | Extractable? |
|---------|-------|-----------|--------------|
| Merge-On-Approval Flow | 1780-1950 | 8KB | Yes - separate workflow doc |
| Batch Processing Rules | 2263-2420 | 7KB | Yes - could be template |
| Parallel Mode Duplicate Logic | 2150-2450 | 12KB | Partial - overlaps with simple |
| Investigation Loop | 1600-1700 | 5KB | Already extracted to template |

**Higher-impact extractions:**
1. Merge-on-approval flow → `bazinga/templates/merge_workflow.md` (~8KB)
2. Batch processing rules → `bazinga/templates/batch_processing.md` (~7KB)

---

## Recommendations

### Immediate (Low Risk)

1. **Do nothing** - Current structure works. 4KB savings not worth fragmentation risk.

### If Optimization Required

1. **Extract merge-on-approval flow** - 8KB savings, isolated workflow
2. **Extract batch processing rules** - 7KB savings, pure procedural
3. **Test capsule extraction** - Run A/B test on format consistency before committing

### NOT Recommended

1. **Context package extraction** - Wrong size estimate, procedural content
2. **Full capsule consolidation** - High risk of format inconsistency

---

## Testing Plan (If Proceeding)

1. Create branch with capsule consolidation
2. Run 10 orchestration sessions
3. Measure:
   - Format consistency (capsules match template)
   - Error rate (malformed output)
   - Token usage (searching vs inline)
4. Compare to baseline

---

## Conclusion

The AI agent's proposals have merit in identifying duplication, but:

1. **Context package proposal**: Inaccurate sizing, wrong content type
2. **Capsule consolidation**: Valid but risky, requires testing

**The better path is extracting larger, isolated workflows** (merge flow, batch processing) rather than fragmenting core status capsules that the LLM uses constantly.

---

## Multi-LLM Review Integration

### Critical Issue Identified (OpenAI)

**The original analysis conflated file size with runtime token usage.**

Moving content to templates does NOT reduce runtime tokens if those templates are still loaded at initialization. The orchestrator reads 3 templates at init:
- `message_templates.md` (21KB)
- `response_parsing.md` (16KB)
- `prompt_building.md` (5KB)

**Total loaded at init: ~42KB + orchestrator.md (100KB) = 142KB per orchestration turn**

Extracting 4-5KB of capsule formats into `message_templates.md` saves 0 runtime tokens because `message_templates.md` is already loaded.

### Incorporated Feedback

1. **Lazy loading strategy** (VALID)
   - Currently: All templates loaded at init
   - Recommended: Load only `message_templates.md` at init (critical, small)
   - Defer loading: `investigation_loop.md`, `merge_workflow.md`, `batch_processing.md` until needed
   - **Impact**: Could reduce typical turn tokens by 15-20% for simple orchestrations

2. **Deterministic capsule formatter** (VALID, HIGH IMPACT)
   - Instead of carrying large text templates, create a small skill/function:
   - Input: `{emoji, action, observation, decision, next}`
   - Output: Correctly formatted capsule string
   - Replace all inline capsule templates with status→field mappings
   - **Impact**: Eliminates format drift, reduces tokens significantly

3. **Token measurement infrastructure** (VALID, PREREQUISITE)
   - Add script to measure token counts for:
     - orchestrator.md alone
     - orchestrator.md + loaded templates
     - Per-path budgets (simple, parallel, investigation, merge)
   - Set target budget and fail CI if exceeded
   - **Impact**: Enables data-driven optimization

4. **A/B testing requirement** (VALID)
   - Before any extraction, run controlled tests:
     - A: Current (inline templates)
     - B: Consolidated with references
   - Track: malformed capsules, parsing errors, token usage
   - **Impact**: Prevents regressions

### Rejected Suggestions (With Reasoning)

1. **"Preprocessing build step for prompts"**
   - Too complex for current team size
   - Introduces build system dependency
   - May complicate debugging
   - **Keep for future consideration** when orchestrator exceeds 150KB

2. **"Broader dedup across agent files"**
   - Spec-kit blocks are intentionally per-agent for independence
   - Cross-agent dedup would create coupling
   - **Not recommended** - agents should remain self-contained

3. **"Hash checks and version headers on templates"**
   - Adds complexity without clear failure modes today
   - Current system recovers gracefully from missing templates
   - **Not recommended** for now

### Revised Recommendations

Based on OpenAI review, the priority order changes:

#### Priority 1: Measure First (1-2 hours)
Create token measurement script to establish baseline:
```bash
# Measure tokens using Claude tokenizer
./scripts/measure-orchestrator-tokens.sh
```

#### Priority 2: Implement Lazy Loading (if needed)
Only if Priority 1 shows token budget exceeded:
1. Keep `message_templates.md` at init (always needed)
2. Load `investigation_loop.md` only when SPAWN_INVESTIGATOR
3. Load `merge_workflow.md` only in merge phase
4. Load `batch_processing.md` only in parallel mode

#### Priority 3: Capsule Formatter Skill (if needed)
Only if A/B testing confirms benefit:
1. Create `capsule-format` skill
2. Input: structured data (emoji, action, observation, decision, next)
3. Output: formatted capsule string
4. Replace inline templates with status→field mappings

### Updated Conclusion

The original proposals (context package extraction, capsule consolidation) address the **wrong problem**:
- They optimize file size, not runtime tokens
- Templates are already loaded at init
- No savings until loading strategy changes

**The correct approach:**
1. Measure actual runtime token usage
2. Implement lazy loading for rarely-used templates
3. Consider capsule formatter skill for deterministic formatting
4. Only then consider content extraction

**Key insight from OpenAI:** "Simply moving text into templates without changing loading strategy won't reduce tokens."

---

## References

- `agents/orchestrator.md` - Main orchestrator file
- `bazinga/templates/message_templates.md` - Capsule format canonical source
- `bazinga/templates/response_parsing.md` - Agent response parsing patterns
- `/home/user/bazinga/tmp/ultrathink-reviews/openai-review.md` - Full OpenAI review
