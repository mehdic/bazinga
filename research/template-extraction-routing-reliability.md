# Template Extraction Routing Reliability Analysis

**Date:** 2025-12-03
**Context:** Evaluation of whether extracting merge workflow and batch processing routing logic to external templates maintains routing reliability
**Decision:** Implement Hybrid Pattern - add inline routing tables as safety net
**Status:** Reviewed → Implementing
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

We extracted ~7.4KB of content from `agents/orchestrator.md` to external templates:
- `templates/merge_workflow.md` (~5KB) - Contains merge task routing logic
- `templates/batch_processing.md` (~3.5KB) - Contains batch processing rules

**Core question:** Will the orchestrator reliably follow routing instructions that are read from external files mid-workflow, as opposed to instructions inline in the system prompt?

---

## Implementation Analysis

### What Was Extracted

**merge_workflow.md contains:**
- Variable sources (session_id, initial_branch, feature_branch, group_id)
- Merge task prompt template
- Spawn configuration
- **Status routing rules** (MERGE_SUCCESS, MERGE_CONFLICT, MERGE_TEST_FAILURE)
- Escalation rules for repeated failures

**batch_processing.md contains:**
- Three-step batch process (parse all → build queue → spawn all)
- Forbidden patterns
- Enforcement checklist

### How It's Referenced

The orchestrator now has MANDATORY references:

```markdown
### 🔴 MANDATORY: Load Merge Workflow Template

**⚠️ YOU MUST READ AND FOLLOW the merge workflow template. This is NOT optional.**

Read(file_path: "templates/merge_workflow.md")

**After reading the template, you MUST:**
1. Build the merge prompt using the template's prompt structure
2. Spawn Developer with the merge task
3. Handle the response according to the template's status routing rules
4. Apply escalation rules for repeated failures

**DO NOT proceed without reading and applying `templates/merge_workflow.md`.**
```

---

## Critical Analysis

### Risk Factors

**1. Context Window Position Effect**

Research indicates LLMs apply more attention to the beginning and end of prompts. File content read mid-conversation appears in the middle of context, potentially receiving less attention.

> "Put instructions at the beginning or end of a prompt. For longer prompts, models may apply optimizations to prevent attention from scaling quadratically, which places more emphasis at the beginning and end." — [Palantir Best Practices](https://www.palantir.com/docs/foundry/aip/best-practices-prompt-engineering)

**2. Tool Results vs System Prompt**

Tool results (like file reads) are structurally different from system prompt content. The LLM may treat them as "data" rather than "instructions to execute."

**3. Competing with Original Instructions**

The orchestrator.md contains many explicit routing instructions. When the model reads additional routing logic from a template, there's potential for:
- Confusion about which instructions take precedence
- Missing template instructions while following inline instructions
- Partial execution of template instructions

**4. No Verification Mechanism**

Unlike the initialization templates (message_templates.md, response_parsing.md, prompt_building.md) which have a verification checkpoint:
```
Verify all 3 templates loaded. If ANY Read fails → Output `❌ Template load failed | [filename]` and STOP.
```

The mid-workflow template loads have no such verification that the instructions were APPLIED, only that the file was read.

### Positive Factors

**1. Claude's Strong Instruction Following**

Anthropic documentation notes:
> "At Anthropic, they occasionally run CLAUDE.md files through the prompt improver and often tune instructions (e.g., adding emphasis with 'IMPORTANT' or 'YOU MUST') to improve adherence."

We use strong language: "YOU MUST READ AND FOLLOW", "This is NOT optional", "DO NOT proceed without reading and applying"

**2. Existing Template Pattern Works**

The orchestrator already loads templates at initialization that contain operational logic (response_parsing.md has status values, parsing rules). These work correctly.

**3. 200K Context Window Reliability**

> "All Claude models can recall information very well across their 200K context window (they passed the 'Needle in a Haystack' test with 95% accuracy)."

Claude can find and use information from anywhere in context.

**4. Simpler Subtask = Better Focus**

> "Each link in the chain gets Claude's full attention! Breaking tasks into separate prompts improves reliability."

The merge step is a discrete subtask that receives focused attention.

---

## Comparison with Existing Patterns

### Pattern 1: Initialization Templates (WORKS)
- Loaded at start before any workflow
- Part of "Step 0" initialization
- Has verification checkpoint
- Templates contain reference material (parsing rules, formats)

### Pattern 2: Investigation Loop (HYBRID)
```markdown
📋 Full investigation loop procedure: templates/investigation_loop.md (v1.0)
```
- References external template BUT...
- Exit codes are DUPLICATED in orchestrator:
```
| Status | Condition | Next Action |
|--------|-----------|-------------|
| ROOT_CAUSE_FOUND | ... | → Step 2A.6c |
| BLOCKED | ... | → Escalate to PM |
```

**Key insight:** The investigation loop pattern has routing logic in BOTH places (template reference + inline exit codes).

### Pattern 3: Merge Workflow (NEW - QUESTION)
- All routing logic moved to template
- Only reference + "you must follow" instructions in orchestrator
- No inline backup of routing rules

---

## Risk Assessment

### Scenarios Where Routing Could Fail

**Scenario 1: Status Not Recognized**
- Developer returns `MERGE_TEST_FAILURE`
- Orchestrator reads template but doesn't properly match the status
- Falls through without proper routing

**Mitigation:** Add inline status enum back to orchestrator

**Scenario 2: Escalation Rules Forgotten**
- Merge fails 2+ times
- Template has escalation rules but orchestrator doesn't apply them
- Gets stuck in infinite retry loop

**Mitigation:** Add inline escalation summary

**Scenario 3: Conflict Resolution Steps Skipped**
- Template has detailed conflict resolution workflow
- Orchestrator only spawns Developer without full context
- Incomplete fix, more failures

**Mitigation:** Ensure spawn template includes complete context

---

## Recommendations

### Option A: Hybrid Pattern (Recommended)

Keep routing logic in BOTH places:
1. **Template:** Full detailed instructions, context, examples
2. **Orchestrator:** Inline summary of status values and routing destinations

```markdown
### Step 2A.7a: Spawn Developer for Merge

🔴 MANDATORY: Load and follow `templates/merge_workflow.md`

**Status Routing (from template):**
| Status | Action |
|--------|--------|
| MERGE_SUCCESS | → Step 2A.8 (PM final check) |
| MERGE_CONFLICT | → Developer fix conflicts, retry QA→TL→merge |
| MERGE_TEST_FAILURE | → Developer fix tests, retry QA→TL→merge |

**Escalation:** 2nd fail → SSE, 3rd fail → TL, 4th+ → PM
```

**Pros:**
- Template has full details for Claude to follow
- Inline routing prevents missed statuses
- Matches investigation_loop pattern

**Cons:**
- Some duplication (but minimal - just status table)

### Option B: Trust Template Only (Current)

Keep as implemented, trust the MANDATORY language.

**Pros:**
- Maximum size reduction
- No duplication

**Cons:**
- Higher risk of routing failures
- No inline backup if template instructions not followed

### Option C: Load Template at Initialization

Move merge_workflow.md to initialization phase (Step 0).

**Pros:**
- Loaded early with other templates
- Part of verified initialization

**Cons:**
- Increases initial context size
- Template may be stale by merge time (long orchestrations)

---

## Questions for External Review

1. Do LLMs reliably execute instructions from files read mid-conversation?
2. Is the "MANDATORY + YOU MUST" language sufficient for instruction adherence?
3. Should routing logic be duplicated (template + inline) for reliability?
4. Are there better patterns for ensuring template instructions are followed?

---

## Evidence Needed

1. Test the current implementation with actual merge scenarios
2. Check if MERGE_CONFLICT routing works correctly
3. Verify escalation rules are applied on repeated failures

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Critical Issues Identified

1. **No verification that template instructions were applied** - Read() gives data but no guard that routing map was built
2. **No `merge_retry_count` field** for escalation tracking - risks infinite retry loops
3. **Single point of failure** if template read fails mid-run
4. **Unknown/novel statuses not handled** - no default/failsafe route
5. **Context eviction risk** - template content could fall out of window in long sessions

### Incorporated Feedback

**1. Hybrid Pattern (IMPLEMENTING)**
- Keep detailed templates for full instructions
- Add inline routing tables to orchestrator as safety net
- Matches investigation_loop pattern already in codebase

**2. Add Unknown Status Fallback**
- If status doesn't match known values → route to Tech Lead with "UNKNOWN_STATUS"
- Prevents stalls from unrecognized statuses

**3. Template Read Failure Handling**
- If Read() fails mid-workflow → use inline routing table
- Output warning capsule and continue

### Rejected Suggestions (With Reasoning)

**1. Persist routing map to DB**
- Overkill for current scope
- Inline routing tables provide same safety with less complexity
- May revisit if routing drift observed in practice

**2. Template checksums/versioning**
- Adds complexity for marginal benefit
- Templates are version-controlled in git
- Inline tables prevent drift regardless

**3. Bounded batch spawning limits**
- Not relevant to routing reliability question
- Existing orchestrator handles batching appropriately

### Implementation Plan

1. Add inline routing tables for merge workflow (Step 2A.7a and 2B.7a)
2. Add inline enforcement summary for batch processing (Step 2B.2a)
3. Add unknown status fallback handling
4. Keep template references for full details
5. Rebuild slash command and commit

---

## References

- [Claude Prompt Chaining Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/chain-prompts)
- [Palantir Prompt Engineering Best Practices](https://www.palantir.com/docs/foundry/aip/best-practices-prompt-engineering)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [26 Principles for Prompt Engineering](https://codingscape.com/blog/26-principles-for-prompt-engineering-to-increase-llm-accuracy)
