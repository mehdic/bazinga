# Orchestrator Optimization: Capsules and Context Packages

**Date:** 2025-12-03
**Context:** Evaluating AI agent's proposal to optimize orchestrator.md size
**Decision:** Extract workflows (~15KB) + consolidate capsules (~4KB) = ~19KB savings
**Status:** Reviewed & Corrected
**Reviewed by:** OpenAI GPT-5 (with corrections based on actual BAZINGA architecture)

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
| `templates/message_templates.md` | 21,134 bytes | 688 |
| `templates/response_parsing.md` | 15,909 bytes | 500+ |
| `templates/prompt_building.md` | 5,185 bytes | 150+ |

### Template Loading Pattern

The orchestrator already loads templates at initialization (lines 673-680):

```markdown
**⚠️ MANDATORY: Read templates that contain runtime instructions**

Read(file_path: "templates/message_templates.md")
Read(file_path: "templates/response_parsing.md")
Read(file_path: "templates/prompt_building.md")
```

And references them throughout:
- Line 59: "You loaded message templates... Use those exact formats"
- Line 99: "Use `templates/response_parsing.md` (loaded at init)"
- Line 1284: "Use the Developer Response Parsing section from `templates/response_parsing.md` (loaded at initialization)"

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
1. Merge-on-approval flow → `templates/merge_workflow.md` (~8KB)
2. Batch processing rules → `templates/batch_processing.md` (~7KB)

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

### Critical Issue Identified (OpenAI) - CORRECTED

**OpenAI's analysis was based on incorrect assumptions about BAZINGA's architecture.**

OpenAI assumed runtime token budget is the constraint. This is wrong.

**Actual constraint:** The tool checks **initial file size of orchestrator.md** before opening. If it exceeds the threshold, it gets blocked. However, once opened, Read() calls for additional templates work gracefully.

**This pattern is already proven in production:**
- orchestrator.md loads `message_templates.md` at init via Read()
- orchestrator.md loads `response_parsing.md` at init via Read()
- orchestrator.md loads `prompt_building.md` at init via Read()

**Therefore:** Extracting content from orchestrator.md to templates DOES reduce the gating file size and DOES help.

### Incorporated Feedback (Re-evaluated)

1. **Capsule consolidation** - NOW VALID
   - Original analysis was correct: ~4-5KB of duplicated capsule formats exist
   - Extracting to `message_templates.md` DOES reduce orchestrator.md initial size
   - **Impact**: ~4-5KB reduction in gating file size

2. **Context package extraction** - STILL NOT RECOMMENDED
   - Only ~2KB (not 5-8KB as claimed)
   - Content is procedural workflow, not reference
   - Breaking workflow steps is riskier than the small savings

3. **Larger workflow extractions** - HIGHEST IMPACT
   - Merge-on-approval flow: ~8KB
   - Batch processing rules: ~7KB
   - These are isolated workflows, safe to extract

4. **Deterministic capsule formatter** (OPTIONAL, from OpenAI)
   - Could replace inline templates with status→field mappings
   - Lower priority than simple extraction
   - Consider if format drift becomes a problem

### Rejected Suggestions (With Reasoning)

1. **"Lazy loading for runtime token reduction"**
   - Based on wrong assumption about constraint
   - The constraint is initial file size, not runtime tokens
   - Templates loaded via Read() work fine once file is opened

2. **"Token measurement infrastructure"**
   - Useful for other purposes, but not the bottleneck here
   - Initial file size is what matters

3. **"Preprocessing build step for prompts"**
   - Overengineered for current needs
   - Keep for future if orchestrator exceeds 150KB

### Corrected Recommendations

Based on corrected understanding of the constraint:

#### Priority 1: Extract Large Isolated Workflows (~15KB savings)
These are self-contained and safe to extract:
1. Merge-on-approval flow → `templates/merge_workflow.md` (~8KB)
2. Batch processing rules → `templates/batch_processing.md` (~7KB)

#### Priority 2: Consolidate Capsule Duplicates (~4KB savings)
1. Keep ONE canonical capsule format definition at top of orchestrator.md
2. Replace step-specific duplicates with status→template references
3. LLM already successfully uses `message_templates.md` via Read()

#### Priority 3: Monitor & Measure
1. Track orchestrator.md size in CI
2. Alert if approaching threshold
3. Have extraction targets ready for next reduction

### Updated Conclusion

The original proposals were partially correct:

1. **Context package proposal**: Still NOT recommended (2KB, procedural content)
2. **Capsule consolidation**: NOW VALID - can save ~4KB
3. **Workflow extraction**: HIGHEST PRIORITY - can save ~15KB

**Total potential savings: ~19KB** (19% reduction from 100KB)

**Key correction:** The constraint is **initial file size**, not runtime tokens. Extracting to templates works because Read() calls succeed after the file is opened.

---

## References

- `agents/orchestrator.md` - Main orchestrator file (100KB, 2662 lines)
- `templates/message_templates.md` - Capsule format canonical source (21KB)
- `templates/response_parsing.md` - Agent response parsing patterns (16KB)
- `templates/prompt_building.md` - Prompt building templates (5KB)
