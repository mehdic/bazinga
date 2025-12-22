# Orchestrator Refactoring Strategy: Under 25K Tokens Without Losing Functionality

**Date:** 2025-11-26
**Context:** orchestrator.md at 26,666 tokens (exceeds 25K limit by 6.7%)
**Decision:** Multi-tier extraction + inline compression strategy
**Status:** Proposed - awaiting implementation

---

## Problem Statement

The orchestrator.md file has grown to **26,666 tokens** (2,695 lines, 94KB), exceeding Claude Code's **25,000 token Read limit**. This prevents the orchestration system from being loaded as a slash command.

**History:**
- Nov 17: File at 3,765 lines (first optimization proposal)
- Nov 20: Reduced to 2,768 lines (23,512 tokens)
- Nov 24: Grew to 2,903 lines (25,282 tokens) - shutdown protocol extracted
- Nov 26 (now): 2,695 lines but **26,666 tokens** (token count increased)

**Root cause:** Content was never truly removed - templates were extracted but verbose inline instructions remain. Token count grows faster than line count due to long lines and code blocks.

---

## Current State Analysis

### File Metrics
| Metric | Value |
|--------|-------|
| Lines | 2,695 |
| Characters | 94,889 |
| Words | 12,811 |
| **Tokens** | **26,666** (6.7% over limit) |
| Target | < 25,000 |
| Reduction needed | **1,666+ tokens** (~6.3%) |

### Section Size Breakdown (by lines)

| Section | Lines | % | Token Est. | Notes |
|---------|-------|---|------------|-------|
| Phase 2A (Simple Mode) | 747 | 27.7% | ~7,400 | Dev→QA→TL→PM flow |
| Phase 2B (Parallel Mode) | 535 | 19.8% | ~5,300 | Batch processing + verification |
| Initialization | 439 | 16.3% | ~4,350 | Session create/resume |
| Phase 1 (PM Planning) | 416 | 15.4% | ~4,100 | PM spawn, clarification |
| Role/Coordinator Section | 98 | 3.6% | ~970 | Role drift prevention |
| Overview/UI Messages | 107 | 4.0% | ~1,060 | Capsule format, agents |
| Database Reference | 68 | 2.5% | ~670 | Logging patterns |
| Error/Completion | 110 | 4.1% | ~1,090 | Error handling, key principles |
| Frontmatter/Other | 175 | 6.5% | ~1,730 | Headers, spacing |
| **Total** | **2,695** | **100%** | **~26,666** | |

### Existing Templates (Already Extracted)

| Template | Lines | Status |
|----------|-------|--------|
| `templates/shutdown_protocol.md` | 564 | In use (Read at runtime) |
| `templates/response_parsing.md` | 549 | Referenced but content duplicated |
| `templates/message_templates.md` | 685 | Referenced but examples inline |
| `templates/prompt_building.md` | 178 | Referenced but logic duplicated |
| `templates/pm_output_format.md` | 264 | Referenced |
| `templates/logging_pattern.md` | 93 | Referenced but expanded inline |
| `templates/completion_report.md` | 108 | Referenced |

**Key insight:** Templates exist but orchestrator still contains verbose inline instructions that duplicate their content.

---

## Critical Analysis: Why Is It Still Too Large?

### Problem 1: Template References + Inline Duplication (HIGH IMPACT)

The orchestrator says "Use template X" but then includes 50-100 lines of inline instructions for the same thing.

**Example - Response Parsing (lines 109-133):**
```markdown
**⚠️ NOTE:** You loaded the complete parsing guide (`templates/response_parsing.md`) during initialization.

**Quick Reference:**
For each agent type, extract:
- **Developer**: Status (READY_FOR_QA/REVIEW/BLOCKED/PARTIAL), files, tests, coverage
- **QA Expert**: Status (PASS/FAIL/PARTIAL/BLOCKED/FLAKY), test results...
[25 more lines of inline instructions]
```

**The problem:** Why have 25 lines of "quick reference" when the template is already loaded?

**Solution:** Trust the template. Remove inline duplication.

**Savings potential:** ~150 lines (~1,500 tokens)

---

### Problem 2: Repetitive Agent Spawn Pattern (HIGH IMPACT)

Every agent spawn follows identical 7-step pattern, repeated 8 times:

1. Output capsule to user
2. Build prompt (read agent file + config)
3. Spawn with Task tool
4. Parse response
5. Construct output capsule
6. Log to database
7. Route to next phase

**Current:** Each spawn is 60-100 lines
**Total:** ~640 lines for 8 spawns

**Example - Developer Spawn (Phase 2A.1):**
```markdown
### Step 2A.1: Spawn Single Developer

**User output (capsule format):**
[Format template - 3 lines]

### 🔴 MANDATORY DEVELOPER/SSE PROMPT BUILDING (PM Tier Decision)

**Step 1: Check PM's Initial Tier decision...**
[20 lines of tier logic]

**Step 2: Build prompt based on tier:**
[15 lines of if/then]

**Step 3: Add config...**
[reference to prompt_building.md]

**Step 4: Include...**
[5 lines]

**Step 5: Validate...**
[3 lines]

**Step 6: Spawn:**
[code block]
```

**The problem:** Same pattern documented 8 times with minor variations.

**Solution:** Generic spawn pattern + agent-specific parameters table.

**Savings potential:** ~400 lines (~4,000 tokens)

---

### Problem 3: Verbose Database Logging (MEDIUM IMPACT)

Every step includes 14-16 lines of logging instructions, appearing ~10 times:

```markdown
**Step 4: Log developer interaction:**
```
bazinga-db, please log this developer interaction:

Session ID: [session_id]
Agent Type: developer
Content: [dev_response]
Iteration: [iteration]
Agent ID: developer_main
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**IMPORTANT:** You MUST invoke bazinga-db skill here...
```

**Total:** ~140-160 lines (~1,400-1,600 tokens)

**Solution:** Single logging reference section + "Log: {agent_type}" one-liner.

**Savings potential:** ~120 lines (~1,200 tokens)

---

### Problem 4: Phase 2B Duplicates Phase 2A (HIGH IMPACT)

Phase 2B (parallel mode) is 535 lines and shares ~80% of logic with Phase 2A.

**What's actually different:**
- Spawn multiple developers in ONE message (parallelism)
- Batch response processing (Layer 1-3 verification)
- Phase continuation check (Step 2B.7a)

**What's duplicated:**
- QA spawn pattern (identical to 2A.4)
- Tech Lead spawn pattern (identical to 2A.6)
- Investigation loop (identical to 2A.6b)
- PM spawn pattern (identical to 2A.8)
- Routing logic

**Solution:** Reference "Same as Phase 2A.X but [difference]" for identical steps.

**Savings potential:** ~250 lines (~2,500 tokens)

---

### Problem 5: Initialization Over-Documentation (MEDIUM IMPACT)

Lines 269-708 (439 lines) document initialization in extreme detail:

- Session check with full example outputs
- Resume workflow with 5 explicit steps
- Path A vs Path B with complete code blocks
- Template loading with verification steps
- Build baseline check with language detection

**The problem:** Most of this is procedural - the AI will follow the logic without needing every edge case documented.

**Solution:** Compact initialization to decision tree + key requirements only.

**Savings potential:** ~150 lines (~1,500 tokens)

---

## Proposed Refactoring Strategy

### Tier 1: Eliminate Inline Duplication (LOW RISK, HIGH IMPACT)

**Target:** Remove content already in templates

| Remove From Orchestrator | Template Source | Lines Saved |
|--------------------------|-----------------|-------------|
| Response parsing quick reference (109-133) | response_parsing.md | 25 |
| Capsule format examples (80-100) | message_templates.md | 20 |
| Logging inline examples | logging_pattern.md | 40 |
| PM output format inline | pm_output_format.md | 20 |
| Prompt building inline steps | prompt_building.md | 30 |

**Total Tier 1 savings:** ~135 lines (~1,350 tokens)

---

### Tier 2: Generic Agent Spawn Pattern (MEDIUM RISK, VERY HIGH IMPACT)

**Create new inline section:**

```markdown
## Generic Agent Spawn Pattern

**For ANY agent spawn:**
1. Output capsule: Use template from message_templates.md
2. Build prompt: Read `agents/{agent}.md` + use prompt_building.md
3. Spawn: `Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent], description="...", prompt=...)`
4. Parse response: Use response_parsing.md
5. Log: `bazinga-db log {agent} interaction` (see Logging Reference)
6. Route: Per routing table below

### Routing Table
| Status | Next Action |
|--------|-------------|
| READY_FOR_QA | Spawn QA Expert |
| READY_FOR_REVIEW | Spawn Tech Lead |
| PASS | Spawn Tech Lead |
| APPROVED | Phase check → PM |
| BLOCKED | Spawn Investigator |
| CONTINUE | Respawn Developer |
| BAZINGA | Completion |

### Agent-Specific Parameters
| Agent | Config | Tier | Description Pattern |
|-------|--------|------|---------------------|
| Developer | developer section | PM decision | Dev {group}: {task[:30]} |
| QA Expert | qa_expert section | sonnet | QA {group}: tests |
| Tech Lead | tech_lead section | opus | TechLead {group}: review |
| PM | pm section | opus | PM: {phase} |
```

**Then replace each spawn section with:**

```markdown
### Step 2A.1: Spawn Developer
Follow §Generic Agent Spawn Pattern. Agent=Developer, Group=main, Mode=Simple.
**Specific:** Check PM's Initial Tier decision (Developer vs SSE).
```

**Savings:** Replace 8 × 80 lines = 640 lines with:
- Generic pattern: 50 lines
- 8 × 5 line agent-specific sections: 40 lines
- **Net savings:** ~550 lines (~5,500 tokens)

---

### Tier 3: Phase 2B Deduplication (LOW RISK, HIGH IMPACT)

**Replace duplicated steps with references:**

```markdown
## Phase 2B: Parallel Mode Execution

### Step 2B.0: Context Optimization Checkpoint
[Keep - unique to parallel]

### Step 2B.1: Spawn Multiple Developers in Parallel
[Keep - core parallel logic, but use Generic Spawn Pattern]

### Step 2B.2: Receive All Developer Responses
Same parsing as Step 2A.2, but for multiple responses.

### Step 2B.2a: Mandatory Batch Processing (LAYER 1)
[Keep - unique batch processing]

### Step 2B.3-2B.6: Route Each Group
Same workflow as Phase 2A Steps 2A.3-2A.7, executed per group.

### Step 2B.7a: Phase Continuation Check
[Keep - unique to parallel]

### Step 2B.7b: Pre-Stop Verification Gate (LAYER 3)
[Keep - unique verification]

### Step 2B.8-2B.9: PM Assessment
Same as Step 2A.8-2A.9.
```

**Savings:** ~250 lines (~2,500 tokens)

---

### Tier 4: Compact Initialization (MEDIUM RISK, MEDIUM IMPACT)

**Current:** 439 lines of detailed initialization
**Target:** 200 lines (decision tree + key actions)

**Compact format:**
```markdown
## Initialization

### Step 0: Check Session State
1. Query bazinga-db for recent sessions
2. If DB fails → check fallback file `bazinga/pm_state_temp.json`
3. Decision:
   - No sessions OR last session completed → **Path B (New Session)**
   - Active session + user says "resume" → **Path A (Resume)**
   - Active session + new task → **Path B (New Session)**

### Path A: Resume Session
1. Extract SESSION_ID from DB response
2. Create artifacts dirs: `mkdir -p bazinga/artifacts/${SESSION_ID}/skills`
3. Load PM state: `bazinga-db get PM state for session [id]`
4. Check success criteria: `bazinga-db get-success-criteria [id]`
5. Spawn PM to continue

### Path B: Create New Session
1. Generate: `SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"`
2. Create dirs: `mkdir -p bazinga/artifacts/${SESSION_ID}/skills`
3. Create session in DB (mode=simple initially)
4. Load configs: skills_config.json, testing_config.json
5. Load model config from DB (or fallback to model_selection.json)
6. Save orchestrator state to DB
7. Run build baseline (silent unless errors)
8. Load templates: message_templates.md, response_parsing.md, prompt_building.md
9. Proceed to Phase 1
```

**Savings:** ~200 lines (~2,000 tokens)

---

### Tier 5: Compact Logging Reference (LOW RISK, MEDIUM IMPACT)

**Create single reference section:**

```markdown
## Logging Reference

**Pattern for ALL agent interactions:**
```
bazinga-db, log {agent_type} interaction:
Session ID: {session_id}, Agent Type: {agent_type},
Content: {response}, Iteration: {N}, Agent ID: {id}
```
Then: `Skill(command: "bazinga-db")`

**Agent IDs:** pm_main, developer_{group}, qa_{group}, techlead_{group}, investigator_{group}

**Error handling:** Init fails → STOP. Workflow logging fails → warn, continue.
```

**Then throughout document:** Replace 14-line logging blocks with "Log to DB (see §Logging Reference)"

**Savings:** ~100 lines (~1,000 tokens)

---

## Implementation Summary

| Tier | Strategy | Lines Saved | Tokens Saved | Risk |
|------|----------|-------------|--------------|------|
| 1 | Eliminate inline duplication | 135 | ~1,350 | LOW |
| 2 | Generic agent spawn pattern | 550 | ~5,500 | MEDIUM |
| 3 | Phase 2B deduplication | 250 | ~2,500 | LOW |
| 4 | Compact initialization | 200 | ~2,000 | MEDIUM |
| 5 | Compact logging reference | 100 | ~1,000 | LOW |
| **Total** | | **1,235** | **~12,350** | |

**Result:**
- Current: 2,695 lines (~26,666 tokens)
- After refactoring: ~1,460 lines (~14,316 tokens)
- **Reduction: 46% (12,350 tokens saved)**
- **Buffer: 10,684 tokens (42.7% under limit)**

---

## Alternative: Minimum Viable Reduction

If aggressive refactoring is too risky, here's the minimum to get under 25K:

| Tier | Strategy | Tokens Saved |
|------|----------|--------------|
| 1 | Eliminate inline duplication | ~1,350 |
| 3 | Phase 2B "same as 2A" references | ~800 |
| **Total** | | **~2,150** |

**Result:** 26,666 - 2,150 = **24,516 tokens** (just under limit)

**Risk:** Very low - only removes truly redundant content
**Downside:** No buffer for future growth

---

## Recommended Approach: Tiers 1-3

**Balance of impact vs risk:**

| Tier | Tokens | Risk | Recommendation |
|------|--------|------|----------------|
| 1 | 1,350 | LOW | **YES** - pure deduplication |
| 2 | 5,500 | MEDIUM | **YES** - significant savings, testable |
| 3 | 2,500 | LOW | **YES** - obvious deduplication |
| 4 | 2,000 | MEDIUM | **OPTIONAL** - if more buffer needed |
| 5 | 1,000 | LOW | **OPTIONAL** - if more buffer needed |

**Tiers 1-3 total:** 9,350 tokens saved
**Result:** 26,666 - 9,350 = **17,316 tokens** (30.7% under limit)

---

## Implementation Plan

### Phase 1: Tier 1 (Eliminate Inline Duplication)
1. Remove response parsing quick reference (25 lines)
2. Remove capsule format inline examples (20 lines)
3. Remove logging inline expansions (40 lines)
4. Keep references to templates, remove duplicated content
5. **Test:** Verify orchestrator still runs

### Phase 2: Tier 2 (Generic Spawn Pattern)
1. Create "Generic Agent Spawn Pattern" section
2. Create routing table
3. Create agent-specific parameters table
4. Replace each spawn section with 5-line reference
5. **Test:** Run orchestration through all agent types

### Phase 3: Tier 3 (Phase 2B Deduplication)
1. Replace duplicated QA/TL/PM spawns with "Same as 2A.X"
2. Keep unique parallel-mode sections intact
3. **Test:** Run parallel mode orchestration

### Phase 4: Validation
1. Run full orchestration (simple mode)
2. Run full orchestration (parallel mode)
3. Verify all workflows complete
4. Check no functionality lost

---

## Risk Mitigation

1. **Backup:** Git commit current state before changes
2. **Incremental:** Apply one tier at a time, test between
3. **Rollback:** Each tier is reversible
4. **Template integrity:** Don't modify existing templates
5. **Reference check:** Ensure all references resolve

---

## Trade-offs Analysis

### What We Preserve
- All functionality (no features removed)
- All templates (unchanged)
- All workflow logic
- All role enforcement
- All verification gates

### What We Lose
- Inline redundancy (good - DRY principle)
- Step-by-step verbosity (acceptable - patterns are clear)
- Copy-paste completeness (acceptable - references are explicit)

### What We Gain
- 30-46% smaller file
- 10K+ token buffer for future growth
- Cleaner separation of concerns
- Easier maintenance
- Single source of truth per concept

---

## Verdict

**Recommended:** Implement Tiers 1-3 (9,350 tokens saved)

**Rationale:**
1. Gets safely under limit with 30% buffer
2. Low-to-medium risk (mostly deduplication)
3. Improves maintainability (DRY principle)
4. Leaves Tiers 4-5 as future options if needed
5. No functionality loss

**Expected outcome:**
- Final size: ~17,316 tokens (30.7% under limit)
- Lines: ~1,650 (39% reduction)
- Room for future additions: ~7,684 tokens

---

## References

- Previous analysis: `research/orchestrator-size-optimization-ultrathink-2025-11-24.md`
- First analysis: `research/orchestrator_size_reduction_strategy.md`
- Bloat analysis: `research/orchestrator-bloat-analysis.md`
- Existing templates: `templates/`

---

**Document Status:** Proposed
**Next Step:** User approval, then implement Tier 1 as proof of concept
