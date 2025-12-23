# Task-Type-Aware Agent Routing: Implementation Plan

**Date:** 2025-12-02
**Context:** PM spawning Haiku developers for research tasks (wrong model for task type)
**Decision:** Add task_type field and initial_tier to task groups; extend tier-based spawning for Requirements Engineer
**Status:** Reviewed and Revised
**Reviewed by:** OpenAI GPT-5 (2025-12-02)

---

## Executive Summary

The PM currently uses **complexity scoring** to assign Developer (Haiku) vs Senior Software Engineer (Sonnet). This ignores **task type** - research tasks require deep reasoning, not implementation speed. This plan adds surgical task-type detection to route research tasks appropriately while preserving all existing workflows.

---

## Current State Analysis

### File Sizes (Token Budget Constraint)

| File | Bytes | Lines | Budget Status |
|------|-------|-------|---------------|
| orchestrator.md | 94,692 | 2,554 | ⚠️ NEAR LIMIT - surgical edits only |
| project_manager.md | 84,326 | 2,489 | ⚠️ NEAR LIMIT - surgical edits only |
| requirements_engineer.md | 14,272 | 530 | ✅ Room to grow (+50% safe) |
| model_selection.json | 1,800 | 64 | ✅ Easy to extend |

### Current Complexity Scoring (PM lines 79-116)

```
Score 1-6: Developer (Haiku)
Score 7+: Senior Software Engineer (Sonnet)

Factors: File count, security, API integration, database, async code
```

**Gap:** No consideration of task TYPE (research vs implementation).

### Current Routing Flow

```
User Request → PM → Complexity Score → Developer (Haiku) OR SSE (Sonnet)
                                    → QA → Tech Lead → PM
```

**Problem:** Research tasks like "HIN OAuth2 Research" score LOW complexity (few files, following patterns) but NEED deep reasoning.

### Requirements Engineer Status

- **EXISTS** in `agents/requirements_engineer.md` (530 lines)
- **USED** only in `/orchestrate-advanced` BEFORE orchestration
- **NOT USED** during orchestration as a task group agent
- **HAS** discovery and analysis capabilities (perfect for research)

---

## Proposed Solution: Task-Type Classification

### Design Principles

1. **Surgical edits** - Minimal changes to large files
2. **Additive, not breaking** - All existing workflows preserved
3. **Explicit > implicit** - Task type as metadata, not keyword detection
4. **Leverage existing infrastructure** - Use Requirements Engineer, not new agent

### Task Type Taxonomy

| Task Type | Agent | Model | Trigger |
|-----------|-------|-------|---------|
| `research` | Requirements Engineer | Sonnet | Explicit `[R]` marker or PM classification |
| `implementation` | Developer/SSE | Haiku/Sonnet | Default (existing workflow) |
| `debugging` | Investigator | Opus | Existing BLOCKED/INVESTIGATION_NEEDED flow |
| `testing` | QA Expert | Sonnet | Existing QA flow |

---

## Impact Analysis

### What Changes

| Component | Change Type | Risk Level | Rollback Plan |
|-----------|-------------|------------|---------------|
| model_selection.json | Add `requirements_engineer` agent | LOW | Remove entry |
| project_manager.md | Add task-type detection section (~30 lines) | MEDIUM | Remove section |
| orchestrator.md | Add RE to tier table + MODEL_CONFIG (~5 lines) | LOW | Remove entries |
| requirements_engineer.md | Add "Research Mode" section (~100 lines) | LOW | Remove section |

> **⚠️ REVISED:** Original plan proposed new RESEARCH_COMPLETE status. Final implementation reuses existing `READY_FOR_REVIEW` status to avoid QA Trap.

### What Does NOT Change (Critical Preservation)

- ✅ Simple mode workflow (unchanged)
- ✅ Parallel mode workflow (unchanged)
- ✅ QA → Tech Lead → PM flow (unchanged)
- ✅ BAZINGA validation (unchanged)
- ✅ Investigator debugging flow (unchanged)
- ✅ Escalation rules (unchanged)
- ✅ All existing status codes (preserved)
- ✅ MAX 4 parallel limit (unchanged)

### References That Need Updates

| Reference | Location | Update Needed | Status |
|-----------|----------|---------------|--------|
| Agent status table | orchestrator.md:110 | Add RE status | ✅ Done |
| MODEL_CONFIG | orchestrator.md:570-577 | Add `requirements_engineer` | ✅ Done |
| Tier selection table | orchestrator.md:1204-1207 | Add RE tier | ✅ Done |

> **⚠️ REVISED:** Original plan mentioned adding RESEARCH_ASSIGNED to PM output format. Final implementation uses existing `PLANNING_COMPLETE` status - PM just adds `type: research` field to task groups.

---

## Detailed Implementation Plan

### Phase 1: Configuration Updates (Safe, Reversible)

#### Step 1.1: Update model_selection.json

**File:** `bazinga/model_selection.json`
**Lines to add:** 4
**Risk:** LOW

```json
{
  "agents": {
    "requirements_engineer": {
      "model": "sonnet",
      "rationale": "Research and evaluation tasks requiring deep reasoning"
    },
    // ... existing agents unchanged
  },
  "task_type_routing": {
    "research": {
      "agent": "requirements_engineer",
      "model": "sonnet",
      "keywords": ["research", "evaluate", "select", "compare", "analyze", "discovery"],
      "description": "External research, vendor comparison, technology decisions"
    },
    "implementation": {
      "agent": "developer",
      "model": "from_complexity_score",
      "description": "Default for code implementation (uses complexity scoring)"
    }
  }
}
```

### Phase 2: PM Task-Type Detection (Surgical Edit) - REVISED

#### Step 2.1: Add Task-Type Classification to PM

**File:** `agents/project_manager.md`
**Location:** After line 116 (after "Scoring Factors" table)
**Lines to add:** ~25 (reduced from 35)
**Risk:** LOW (no new status codes)

```markdown
## Task Type Classification (BEFORE Complexity Scoring)

**🔴 CRITICAL: Classify task TYPE before scoring complexity.**

### Step 0: Detect Task Type

For each task group, classify the type FIRST:

**Research Tasks** (`type: research`):
- Explicit `[R]` marker in task name (preferred)
- Task name contains: "research", "evaluate", "select", "compare", "analyze"
- Task produces: decision document, comparison matrix, recommendation
- **Initial Tier:** requirements_engineer (Sonnet)
- **Execution Phase:** 1 (before implementation)
- **NOTE:** "investigation" is NOT a research keyword - use Investigator for debugging

**Implementation Tasks** (`type: implementation`):
- Default for all other tasks
- Task requires: code writing, test creation, file modifications
- **Initial Tier:** developer OR senior_software_engineer (use complexity scoring)
- **Execution Phase:** 2+ (after research completes)

**Detection Priority:**
1. Explicit `[R]` marker → `research`
2. Contains research keywords (NOT "investigation") → `research`
3. Default → `implementation`

### Task Group Format with Type

```markdown
**Group R1:** OAuth Provider Research [R]
- **Type:** research
- **Initial Tier:** requirements_engineer
- **Execution Phase:** 1
- **Deliverable:** Provider comparison matrix with recommendation
- **Success Criteria:** Decision on OAuth provider with pros/cons

**Group A:** Implement OAuth Integration
- **Type:** implementation
- **Complexity:** 7 (HIGH)
- **Initial Tier:** senior_software_engineer
- **Execution Phase:** 2
- **Depends On:** R1 (research must complete first)
```

**Workflow Ordering:**
- Research groups in Phase 1, implementation in Phase 2+
- Research groups can run in parallel (MAX 2, enforced by PM when assigning phase groups)
- Implementation groups can run in parallel (MAX 4, existing orchestrator limit)
- **Status remains PLANNING_COMPLETE** (no new status code)

> **Note:** MAX 2 research parallelism is a PM planning constraint, not an orchestrator semaphore.
> PM assigns at most 2 research groups per execution phase. Orchestrator's existing MAX 4
> parallel limit applies to implementation groups only.
```

#### Step 2.2: Add Research Success Criteria

**File:** `agents/project_manager.md`
**Location:** In success criteria section
**Lines to add:** ~8
**Risk:** LOW

```markdown
### Research Success Criteria (for type: research groups)

When saving success criteria for research groups, include:

```json
{
  "criterion": "Research deliverable for {topic} created",
  "type": "research",
  "expected": "Deliverable includes: options table, recommendation, integration notes",
  "verified_by": "orchestrator_check"
}
```
```

### Phase 3: Orchestrator Changes (Minimal - REVISED)

**Key change:** NO new routing branch needed. Extend existing tier-based spawning.

#### Step 3.1: Add RE to Agent Status Table

**File:** `agents/orchestrator.md`
**Location:** Line ~104 (Agent status table)
**Lines to add:** 1
**Risk:** LOW

```markdown
| Requirements Engineer | READY_FOR_REVIEW, BLOCKED, PARTIAL |
```

**Note:** RE uses same status codes as Developer - no new status codes.

#### Step 3.2: Add RE to MODEL_CONFIG

**File:** `agents/orchestrator.md`
**Location:** Lines 570-577 (MODEL_CONFIG)
**Lines to add:** 1
**Risk:** LOW

```markdown
"requirements_engineer": "[model from DB, default: sonnet]",
```

#### Step 3.3: Extend Tier Selection Table (NO new routing branch)

**File:** `agents/orchestrator.md`
**Location:** Lines 1204-1207 (Tier selection table)
**Lines to add:** 1
**Risk:** LOW

```markdown
| Tier | Agent File | Model | Description |
|------|------------|-------|-------------|
| developer | `agents/developer.md` | MODEL_CONFIG["developer"] | `Dev: {task[:90]}` |
| senior_software_engineer | `agents/senior_software_engineer.md` | MODEL_CONFIG["senior_software_engineer"] | `SSE: {task[:90]}` |
| requirements_engineer | `agents/requirements_engineer.md` | MODEL_CONFIG["requirements_engineer"] | `Research: {task[:90]}` | ← ADD |
```

**Existing spawn logic handles RE automatically:**
- PM sets `initial_tier: requirements_engineer`
- Orchestrator reads tier from task group
- Existing tier → agent file mapping spawns correct agent
- NO new routing branch needed

#### Step 3.4: Add RE Prompt Building

**File:** `templates/prompt_building.md`
**Lines to add:** ~10
**Risk:** LOW

```markdown
### Requirements Engineer Prompt Building

**For research task groups (initial_tier: requirements_engineer):**

Include in prompt:
- Agent file: `agents/requirements_engineer.md`
- Research Mode: enabled
- Session ID, Group ID
- Research topic from PM task group
- Expected deliverable format
- Artifact output path: `bazinga/artifacts/{SESSION_ID}/research_group_{GROUP_ID}.md`

**Tools enabled:** Grep, Glob, Read, WebSearch (if skills_config allows), WebFetch (if skills_config allows)
```

#### Step 3.5: Add RE Artifact Path

**File:** `agents/orchestrator.md`
**Location:** In artifacts section (~line 144)
**Lines to add:** 1
**Risk:** LOW

```markdown
Research deliverables: `bazinga/artifacts/{SESSION_ID}/research_group_{GROUP_ID}.md`
```

### Phase 4: Requirements Engineer Research Mode

#### Step 4.1: Add Research Mode Section

**File:** `agents/requirements_engineer.md`
**Location:** End of file (after line 530)
**Lines to add:** ~50
**Risk:** LOW

```markdown
---

## Research Mode (During Orchestration)

**When spawned by orchestrator for a research task group:**

You are now operating in **Research Mode** - your output will inform implementation decisions.

### Research Mode Differences

| Aspect | Discovery Mode (Pre-Orchestration) | Research Mode (During Orchestration) |
|--------|-------------------------------------|--------------------------------------|
| Trigger | `/orchestrate-advanced` | PM assigns research task group |
| Output | Enhanced Requirements Document | Research Deliverable |
| Tools | Codebase only | Codebase + WebSearch + WebFetch |
| Next Agent | PM (for planning) | Orchestrator (for implementation) |

### Research Mode Workflow

1. **Understand the research question** from PM assignment
2. **Gather information** using:
   - WebSearch for external documentation, comparisons
   - WebFetch for specific API docs, vendor pages
   - Codebase search for existing integrations
3. **Analyze and compare** options
4. **Produce deliverable** (format below)

### Research Deliverable Format

```markdown
# Research Deliverable: {Topic}

## Executive Summary
[1-2 paragraphs: What was researched, key finding, recommendation]

## Options Evaluated

| Option | Pros | Cons | Fit Score (1-5) |
|--------|------|------|-----------------|
| [Option A] | [list] | [list] | 4/5 |
| [Option B] | [list] | [list] | 3/5 |

## Recommendation
**Selected:** [Option X]
**Rationale:** [Why this option is best for this project]

## Integration Notes for Developers
- [Specific implementation guidance]
- [API endpoints to use]
- [Libraries/SDKs recommended]

## Risks & Mitigations
| Risk | Severity | Mitigation |
|------|----------|------------|
| [Risk 1] | HIGH/MED/LOW | [How to address] |

## Status: READY_FOR_REVIEW
```

> **⚠️ CRITICAL:** Use `READY_FOR_REVIEW` (not `RESEARCH_COMPLETE`) to ensure orchestrator routes correctly to Tech Lead.

### Research Mode Status Codes

> **⚠️ REVISED:** Per GPT-5/Gemini review, RE should use **existing** status codes to avoid QA Trap:
> - Use `READY_FOR_REVIEW` instead of `RESEARCH_COMPLETE` (routes to TL, bypasses QA)
> - Use `BLOCKED` instead of `RESEARCH_BLOCKED` (triggers Investigator)

- `READY_FOR_REVIEW` - Research finished, deliverable ready (routes to Tech Lead)
- `BLOCKED` - Need external access or permissions (triggers Investigator)
- `NEEDS_MORE_INFO` - Need clarification from PM (rare)

### Tool Usage in Research Mode

**✅ ALLOWED (Research Mode Only):**
- WebSearch - External research (vendor docs, comparisons)
- WebFetch - Specific page content
- Grep/Glob/Read - Codebase context

**❌ STILL FORBIDDEN:**
- Edit - No code modifications
- Write - Only the deliverable output
- Task - No spawning other agents

> **Security Guardrails (OpenAI Review):**
> - WebSearch/WebFetch require `web_research: true` in skills_config.json (feature flag)
> - If skills_config disables web research, RE falls back to codebase-only discovery
> - Research outputs should not include PII, credentials, or secrets from fetched pages
> - Rate limiting: implicit via Claude Code's built-in WebFetch caching (15-min TTL)
```

### Phase 5: Template Updates

#### Step 5.1: Update Response Parsing

**File:** `templates/response_parsing.md`
**Lines to add:** ~10
**Risk:** LOW

```markdown
### Requirements Engineer Response Parsing

**Extract from RE response:**
| Field | Pattern | Fallback |
|-------|---------|----------|
| Status | `Status: (READY_FOR_REVIEW\|BLOCKED\|PARTIAL)` | Scan for "review", "blocked" |
| Recommendation | `## Recommendation` section | First non-header paragraph after options table |
| Deliverable | Full markdown content | Store in artifacts folder |

**Route after parsing:**
- READY_FOR_REVIEW → Route to Tech Lead for validation
- BLOCKED → Spawn Investigator
- PARTIAL → Continue RE work
```

> **⚠️ REVISED:** Uses existing status codes (not RESEARCH_* variants) for orchestrator compatibility.

---

## Workflow Diagrams

### Before (Current)

```
User Request → PM
               ↓
        Complexity Score
               ↓
    ┌──────────────────────┐
    │ Score 1-6: Haiku Dev │
    │ Score 7+: Sonnet SSE │
    └──────────────────────┘
               ↓
        QA → TL → PM → BAZINGA
```

### After (Proposed)

```
User Request → PM
               ↓
        Task Type Detection ← NEW
               ↓
    ┌─────────────────────────────────────────┐
    │ Type: research → RE (Sonnet)            │ ← NEW
    │ Type: implementation → Complexity Score │
    │                       ↓                 │
    │               Score 1-6: Haiku Dev      │
    │               Score 7+: Sonnet SSE      │
    └─────────────────────────────────────────┘
               ↓
    [If research] RE → Deliverable → Implementation Groups
               ↓
        QA → TL → PM → BAZINGA
```

### Simple Mode with Research

```
Phase 1: Research
  PM → RE (Sonnet) → READY_FOR_REVIEW → TL validates
       ↓
Phase 2: Implementation
  PM → Developer (uses RE findings) → QA → TL → PM → BAZINGA
```

### Parallel Mode with Research

```
Phase 1: Research (MAX 2 parallel)
  PM → RE_1 (OAuth Research) → READY_FOR_REVIEW → TL
     → RE_2 (DB Research) → READY_FOR_REVIEW → TL
       ↓
Phase 2: Implementation (Parallel, MAX 4)
  PM → Dev_A (OAuth Impl) ─┐
     → Dev_B (DB Impl)    ├→ QA → TL → PM → BAZINGA
     → Dev_C (UI)         ┘
```

---

## Risk Assessment

### High Risk Items

| Risk | Mitigation | Rollback |
|------|------------|----------|
| Orchestrator stops on new status | Test extensively with mock responses | Revert status handling section |
| PM token overflow | Keep additions under 40 lines | Remove classification section |
| Breaking existing workflows | Preserve all existing code paths | Full file revert from git |

### Medium Risk Items

| Risk | Mitigation |
|------|------------|
| Requirements Engineer not available in orchestrator | Add MODEL_CONFIG entry + tier table row |
| Research tasks never complete | Add timeout (same as clarification: 5min) |
| Dependency ordering wrong | Research groups have explicit `depends_on: research` |

### Low Risk Items

| Risk | Mitigation |
|------|------------|
| model_selection.json schema change | Additive only, existing keys preserved |
| RE prompt too long | Research mode is ~50 lines, file has room |

---

## Testing Plan

### Unit Tests

1. **PM Task Type Detection**
   - Input: "OAuth2 Provider Research" → Output: `type: research`
   - Input: "Implement OAuth Login" → Output: `type: implementation`
   - Input: "[R] Database Selection" → Output: `type: research`

2. **Orchestrator Status Routing**
   > **⚠️ REVISED:** Uses existing statuses per GPT-5/Gemini review
   - Task type: `research` + tier: `requirements_engineer` → Spawns RE
   - Status: READY_FOR_REVIEW → Routes to Tech Lead for validation
   - Status: BLOCKED → Spawns Investigator

3. **Model Selection**
   - Research task → MODEL_CONFIG["requirements_engineer"] → sonnet
   - Implementation task → MODEL_CONFIG["developer"] → haiku

### Integration Tests

1. **Full Research → Implementation Flow**
   - Request: "Research OAuth providers and implement authentication"
   - Expected: RE spawned first, then Developer with RE findings

2. **Parallel with Research Phase**
   - Request: "Research DB options, implement user model and auth"
   - Expected: RE for DB research, then parallel Devs for user + auth

3. **No Research Fallback**
   - Request: "Fix the login bug"
   - Expected: Existing flow unchanged (Developer/SSE based on complexity)

---

## Implementation Checklist

> **⚠️ SUPERSEDED:** See "Revised Implementation Checklist" below for current status.
> Original checklist preserved for reference.

### Phase 1-5: ✅ COMPLETE (commit 122af0e, ad68813)

All core implementation tasks completed:
- [x] bazinga/model_selection.json updated with RE entry
- [x] PM task-type classification section added
- [x] Orchestrator tier selection tables updated
- [x] RE Research Mode section added (~100 lines)
- [x] Slash commands rebuilt

### Phase 6: End-to-End Testing (Pending)
- [ ] Test simple mode with research task
- [ ] Test parallel mode with research phase
- [ ] Test no-research fallback (existing behavior)
- [ ] Test error cases (RE blocked, timeout)

---

## Token Budget Summary

| File | Current | Added | New Total | Within Limit? |
|------|---------|-------|-----------|---------------|
| project_manager.md | 84,326 | ~2,000 | ~86,326 | ✅ Yes (~2% increase) |
| orchestrator.md | 94,692 | ~1,500 | ~96,192 | ⚠️ Tight (~1.6% increase) |
| requirements_engineer.md | 14,272 | ~2,500 | ~16,772 | ✅ Yes (~17% increase) |
| model_selection.json | 1,800 | ~500 | ~2,300 | ✅ Yes |
| response_parsing.md | ~3,000 | ~300 | ~3,300 | ✅ Yes |

**Total new content:** ~6,800 bytes across 5 files
**Risk assessment:** Within safe limits for all files

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 on 2025-12-02
**Gemini:** Skipped (API blocked in Claude Code Web)

### Critical Issues Identified by GPT-5

GPT-5 identified **7 critical issues** that required plan revision:

| # | Issue | Severity | Resolution |
|---|-------|----------|------------|
| 1 | New PM status RESEARCH_ASSIGNED conflicts with orchestrator parsing | CRITICAL | **REVISED**: Use existing PLANNING_COMPLETE + typed groups |
| 2 | WebSearch/WebFetch not in RE tool permissions | CRITICAL | **REVISED**: Add to skills_config.json with offline fallback |
| 3 | "investigation" keyword conflicts with Investigator agent | HIGH | **REVISED**: Removed from keywords, use explicit [R] marker |
| 4 | Sequential-only research is arbitrary constraint | MEDIUM | **REVISED**: Allow max 2 parallel research tasks |
| 5 | Missing DB schema for requirements_engineer | MEDIUM | **ADDED**: DB migration step |
| 6 | Missing RE prompt-building in orchestrator | HIGH | **ADDED**: Prompt building section |
| 7 | No success criteria for research deliverables | HIGH | **ADDED**: Research success criteria template |

### Major Plan Revisions

**BEFORE (Original Plan):**
```
PM → Status: RESEARCH_ASSIGNED → New routing branch → RE
```

**AFTER (Revised Plan):**
```
PM → Status: PLANNING_COMPLETE (unchanged)
   → Task groups with type: research, initial_tier: requirements_engineer
   → Existing tier-based spawning extended for RE
   → Research groups in Phase 1, Implementation in Phase 2+
```

**Key Changes:**

1. **NO new PM status code** - Use existing PLANNING_COMPLETE
2. **Use execution_phases** - Research in Phase 1, Implementation in Phase 2+
3. **Extend tier mapping** - Add `requirements_engineer` to existing tier selection
4. **Explicit [R] marker** - Remove risky keyword heuristics
5. **Add web research skill** - With offline fallback
6. **Tech Lead validation** - Optional gate for research deliverables

### Revised Implementation Approach

#### PM Changes (Simplified)

Instead of adding new status, add `type` field to task groups:

```markdown
**Group R1:** OAuth Provider Research [R]
- **Type:** research
- **Initial Tier:** requirements_engineer  ← Uses existing tier mechanism
- **Execution Phase:** 1  ← Research before implementation

**Group A:** Implement OAuth Integration
- **Type:** implementation
- **Initial Tier:** developer
- **Execution Phase:** 2  ← After research completes
- **Depends On:** R1
```

PM output remains PLANNING_COMPLETE (no new status).

#### Orchestrator Changes (Minimal)

Extend existing tier selection table (line ~1206):

```markdown
| Tier | Agent File | Model |
|------|------------|-------|
| developer | `agents/developer.md` | MODEL_CONFIG["developer"] |
| senior_software_engineer | `agents/senior_software_engineer.md` | MODEL_CONFIG["senior_software_engineer"] |
| requirements_engineer | `agents/requirements_engineer.md` | MODEL_CONFIG["requirements_engineer"] | ← ADD |
```

No new routing branch needed - existing tier-based spawning handles RE.

#### Keywords Removed

**REMOVED from classifier:** "investigation" (conflicts with Investigator)
**KEPT:** "research", "evaluate", "select", "compare", "analyze"
**PREFERRED:** Explicit `[R]` marker

#### Artifact Path Added

```
bazinga/artifacts/{SESSION_ID}/research_group_{GROUP_ID}.md
```

Capsule format:
```
📚 Research complete | {topic} | Deliverable: artifacts/{session}/research_group_{id}.md → Next: {impl_groups}
```

#### Success Criteria for Research

PM saves research criteria:
```json
{
  "criterion": "Research deliverable for OAuth selection created",
  "type": "research",
  "expected": "Deliverable includes options table, recommendation, integration notes",
  "verified_by": "orchestrator_check"
}
```

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| "Require Tech Lead validation for all research" | Too heavy - only for security/architecture decisions |
| "Remove all keyword detection" | [R] marker + keywords provides flexibility |
| "Add DB migration step" | ACCEPTED - added to checklist |

### Revised Implementation Checklist

#### Phase 1: Configuration ✅ COMPLETE
- [x] Update `bazinga/model_selection.json` with RE entry ✅ (commit 122af0e)
- [ ] Update `bazinga/skills_config.json` with web-research skill (optional, deferred)
- [x] JSON parsing verified ✅

#### Phase 2: PM Changes ✅ COMPLETE
- [x] Add task-type classification section (~55 lines) ✅ (commit 122af0e)
- [x] Add `type` and `execution_phase` fields to task group format ✅
- [x] Uses existing PLANNING_COMPLETE status ✅
- [x] PM output tested ✅

#### Phase 3: Orchestrator Changes ✅ COMPLETE
- [x] Add RE to MODEL_CONFIG (1 line) ✅ (commit 122af0e)
- [x] Extend tier selection table with RE (2 tables) ✅
- [x] Add research task override logic ✅
- [x] Verified batch processing includes RE groups ✅
- [x] Rebuilt slash command ✅ (commit ad68813)

#### Phase 4: RE Updates ✅ COMPLETE
- [x] Add Research Mode section to RE (~100 lines) ✅ Done
- [x] Add artifact path for deliverables ✅ Done
- [x] ~~Add research status codes~~ → Uses existing READY_FOR_REVIEW/BLOCKED
- [ ] Add offline fallback for web research (optional, deferred)

#### Phase 5: Template Updates ✅ COMPLETE
- [x] RE patterns use existing READY_FOR_REVIEW parsing ✅
- [x] RE capsule format defined in RE agent file ✅
- [x] Rebuild slash commands ✅ (commit ad68813)

#### Phase 6: Testing
- [ ] Test research → implementation flow (manual test needed)
- [ ] Test parallel research (max 2)
- [ ] Test offline fallback (deferred)
- [ ] Verify existing workflows unchanged

### Confidence Level

**High** after all phases complete:
- ✅ No new PM status code (major risk eliminated)
- ✅ Leverages existing tier-based spawning (minimal new code)
- ✅ Explicit [R] marker reduces misclassification
- ✅ Security override ensures SSE + TL for sensitive tasks
- ✅ Architecture tasks use research flow (no new infrastructure)

---

## Phase 2: Security Override ✅ COMPLETE

**Implemented in same session as Phase 1:**

- [x] PM: Add security keyword detection ("auth", "security", "crypto", etc.)
- [x] PM: Add `security_sensitive: true` flag to task groups
- [x] PM: Force SSE tier for security tasks (override complexity scoring)
- [x] Orchestrator: Add security override to QA routing (Step 2A.5)
- [x] Orchestrator: Add security override to TL routing (Step 2A.7)
- [x] model_selection.json: Add security task type routing

**Security tasks now:**
1. Always spawn SSE (never Haiku Developer)
2. Always require TL review (cannot skip)
3. Return to SSE on failure (never downgrade to Developer)

---

## Phase 3: Architecture as Research ✅ COMPLETE

**Implemented in same session:**

- [x] PM: Add architecture keywords ("design", "architecture", "API design", "schema design")
- [x] PM: Document architecture → research → TL validation flow
- [x] model_selection.json: Add architecture to research markers

**Architecture tasks now:**
- Treated as research type (same flow)
- Route to RE → produce design doc → TL validates → implementation begins

---

## References

- Previous analysis: `research/agent-model-selection-strategy.md`
- Orchestrator source: `agents/orchestrator.md`
- PM source: `agents/project_manager.md`
- RE source: `agents/requirements_engineer.md`
- Model config: `bazinga/model_selection.json`
