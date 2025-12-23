# Orchestrator Token Optimization: Ultrathink Analysis

**Date:** 2025-12-04
**Context:** Orchestrator file is 2390 lines / 90KB - largest agent file by far
**Problem:** Orchestrator bypasses token limits during long sessions
**Status:** Approved for Implementation
**Reviewed by:** OpenAI GPT-5 (2025-12-04)

## User Decision (2025-12-04)

| Question | Decision |
|----------|----------|
| Use `templates/orchestrator/` | ✅ YES |
| Add CI gates | ❌ NO |
| Compress prose | ❌ NO - Extract only |

**Implementation approach:** Extract Phase 2A/2B to templates without compression. Adjust core orchestrator to read templates at runtime.

## Implementation Complete (2025-12-04)

**Files created:**
- `templates/orchestrator/phase_simple.md` (604 lines) - Phase 2A workflow
- `templates/orchestrator/phase_parallel.md` (349 lines) - Phase 2B workflow

**Files modified:**
- `agents/orchestrator.md` - Reduced from 2390 → 1496 lines (37% reduction)
- `scripts/build-slash-commands.sh` - Updated line count validation (2000 → 1400)
- `.claude/commands/bazinga.orchestrate.md` - Regenerated (1495 lines)

**Results:**
| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Core orchestrator | 2390 lines | 1496 lines | 894 lines (37%) |
| Active context (simple) | 2390 lines | 1496 + 604 = 2100 lines | 12% |
| Active context (parallel) | 2390 lines | 1496 + 349 = 1845 lines | 23% |

**Note:** Core is always loaded. Templates are loaded on-demand when entering each phase.

---

## Problem Statement

The orchestrator agent file (`agents/orchestrator.md`) has grown to 2390 lines (~90KB / ~22,500 tokens estimated). This causes:

1. **Context overflow** - Long sessions cause critical instructions to fall out of context window
2. **Token budget violations** - Exceeds reasonable agent prompt sizes
3. **Role drift** - When instructions are lost, orchestrator starts implementing instead of coordinating
4. **Slow initialization** - Large file takes longer to process

### Size Comparison

| Agent | Lines | Relative Size |
|-------|-------|---------------|
| orchestrator.md | 2390 | **100%** (baseline) |
| project_manager.md | 2215 | 93% |
| senior_software_engineer.md | 1468 | 61% |
| qa_expert.md | 1455 | 61% |
| techlead.md | 1413 | 59% |
| developer.md | 1238 | 52% |
| investigator.md | 1062 | 44% |
| requirements_engineer.md | 734 | 31% |

---

## Current Structure Analysis

### Major Sections (by line count estimate)

| Section | Lines | Purpose | Critical? |
|---------|-------|---------|-----------|
| Role Enforcement & Drift Prevention | ~200 | Prevent orchestrator from implementing | YES |
| Initialization (Step 0) | ~400 | Session setup, resume logic | YES |
| Tech Stack Detection (Step 0.5) | ~80 | Scout spawn and processing | NO (runs once) |
| Phase 1: PM Spawn | ~300 | Spawn PM, receive decision | YES |
| Phase 2A: Simple Mode | ~500 | Single developer workflow | Conditional |
| Phase 2B: Parallel Mode | ~300 | Multi-developer workflow | Conditional |
| Specialization Loading | ~100 | Template composition | NO (delegated to skill) |
| Logging Reference | ~50 | Database logging format | Reference only |
| Error Handling | ~80 | Stuck detection, recovery | YES |
| Completion/Shutdown | ~100 | BAZINGA validation, cleanup | YES |

### Identified Redundancies

1. **Duplicate routing logic** - Same routing decision tree appears in 2A and 2B
2. **Inline examples** - Full prompt examples could be templates
3. **Verbose explanations** - Some sections have 3+ ways to say the same thing
4. **Historical comments** - "(NEW - CRITICAL)", "(LAYER 1 - ROOT CAUSE FIX)"

---

## Proposed Solutions

### Option 1: Modular Decomposition (Recommended)

**Concept:** Split orchestrator into core + loadable modules

```
agents/
  orchestrator.md           # Core (~800 lines) - Always loaded
  orchestrator-modules/
    phase-2a-simple.md      # Simple mode workflow
    phase-2b-parallel.md    # Parallel mode workflow
    routing-logic.md        # Shared routing decisions
    logging-reference.md    # Database formats
```

**How it works:**
1. Core orchestrator always loaded (role enforcement, initialization, PM spawn)
2. Phase 2A/2B loaded conditionally based on PM's mode decision
3. Routing logic shared module (loaded once, used by both phases)

**Pros:**
- Reduces base token usage by ~60%
- Conditional loading means only relevant sections in context
- Modules can evolve independently

**Cons:**
- Adds complexity (file reading during execution)
- Risk of module becoming out of sync
- May confuse the model about what's "loaded"

**Estimated savings:** 1400+ lines from core

---

### Option 2: External State Machine

**Concept:** Move workflow logic to a state machine definition

```yaml
# orchestrator-workflow.yaml
states:
  INIT:
    entry: "Initialize session"
    transitions:
      - on: NEW_SESSION -> TECH_STACK_SCOUT
      - on: RESUME -> LOAD_STATE

  PM_SPAWN:
    entry: "Spawn PM with context"
    transitions:
      - on: SIMPLE_MODE -> PHASE_2A
      - on: PARALLEL_MODE -> PHASE_2B
      - on: NEEDS_CLARIFICATION -> CLARIFY
```

**How it works:**
1. Orchestrator reads state machine definition
2. Current state determines which section to execute
3. Transitions are explicit and verifiable

**Pros:**
- Workflow becomes data, not prose
- Easier to visualize and debug
- Formal verification possible

**Cons:**
- Requires state machine interpreter logic
- Less natural for LLM to follow
- Migration effort significant

**Estimated savings:** 800+ lines (workflow prose → YAML)

---

### Option 3: Progressive Disclosure

**Concept:** Start with minimal instructions, expand on demand

```markdown
## Core Instructions (Always Loaded)
[~300 lines of critical rules]

## Extended Instructions
When you need detailed guidance on:
- Simple mode: Read `docs/phase-2a-guide.md`
- Parallel mode: Read `docs/phase-2b-guide.md`
- Error recovery: Read `docs/error-handling.md`
```

**How it works:**
1. Orchestrator starts with minimal core (role enforcement, basic workflow)
2. Reads extended docs only when entering that phase
3. Uses caching - once read, doesn't need to re-read

**Pros:**
- Natural fit for LLM context management
- No structural changes to execution
- Can be adopted incrementally

**Cons:**
- May re-read docs if context compacted
- Depends on model's ability to reference external docs
- Debugging harder (instructions spread across files)

**Estimated savings:** 1600+ lines from initial prompt

---

### Option 4: Compression Without Loss

**Concept:** Aggressive editing to remove redundancy while keeping all functionality

**Specific targets:**
1. **Remove "(NEW - CRITICAL)" annotations** - 50+ occurrences
2. **Consolidate routing logic** - Single decision tree, referenced twice
3. **Convert verbose explanations to bullets** - ~300 lines saved
4. **Remove inline examples** - Move to templates
5. **Deduplicate mode-specific logic** - 2A and 2B share ~40% content

**Example transformation:**
```markdown
# BEFORE (15 lines)
### Step 2A.3: Route Developer Response

After receiving the developer's response, you need to analyze what they reported
and determine the next step in the workflow. The developer will report their
status using one of several status codes. Based on this status code, you will
route to the appropriate next agent.

**Status codes and routing:**
- READY_FOR_QA: Developer created integration tests, route to QA Expert
- READY_FOR_REVIEW: Developer created only unit tests, route to Tech Lead
...

# AFTER (5 lines)
### Step 2A.3: Route Developer Response

| Status | Route To | Condition |
|--------|----------|-----------|
| READY_FOR_QA | QA Expert | Integration tests created |
| READY_FOR_REVIEW | Tech Lead | Unit tests only |
```

**Pros:**
- No architectural changes
- Preserves all functionality
- Lowest risk approach

**Cons:**
- Limited savings (~30% reduction)
- Requires careful editing
- May lose helpful context for humans

**Estimated savings:** 600-800 lines

---

### Option 5: Hybrid Approach (Recommended Best)

**Concept:** Combine Options 1 + 4

**Phase 1: Immediate compression (Option 4)**
- Remove redundant annotations
- Convert prose to tables
- Deduplicate routing logic
- Target: Reduce to ~1800 lines

**Phase 2: Modular decomposition (Option 1)**
- Extract Phase 2A/2B to modules
- Create shared routing module
- Keep core at ~800 lines
- Total with modules: ~1800 lines, but only ~800 in base context

**Implementation order:**
1. Week 1: Compression pass (immediate relief)
2. Week 2: Module extraction (structural improvement)
3. Week 3: Testing and validation

---

## Critical Analysis

### Pros of Hybrid Approach ✅

1. **Immediate improvement** - Compression provides quick wins
2. **Sustainable structure** - Modules prevent future bloat
3. **Backward compatible** - No workflow changes
4. **Testable** - Each phase can be validated independently
5. **Addresses root cause** - Both size AND structure problems

### Cons ⚠️

1. **Two-phase effort** - More work than single approach
2. **Module complexity** - Need to ensure modules stay in sync
3. **Testing burden** - Must test both compressed and modular versions
4. **Documentation debt** - Need to update CONTRIBUTING.md

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Compression removes critical instructions | Medium | High | Peer review each change |
| Modules become out of sync | Medium | Medium | Build script validates |
| Model can't follow modular structure | Low | High | Test with real sessions |
| Regression in workflow | Medium | High | Integration tests |

---

## Verdict

**Recommended: Option 5 (Hybrid Approach)**

The orchestrator's size problem has two root causes:
1. **Accumulated verbosity** - Solved by compression
2. **Monolithic structure** - Solved by modularization

Addressing only one leaves the other to grow back. The hybrid approach provides:
- Immediate relief (compression)
- Long-term sustainability (modules)
- Manageable risk (phased rollout)

**Estimated final state:**
- Core orchestrator: ~800 lines (always loaded)
- Phase modules: ~500 lines each (conditionally loaded)
- Total: ~1800 lines (vs current 2390)
- Context savings: ~60% during execution (only relevant module loaded)

---

## Implementation Considerations

### What MUST stay in core:
- Role enforcement ("You are a COORDINATOR")
- Role drift prevention
- Initialization and resume logic
- PM spawn and decision routing
- Error handling fundamentals
- Shutdown protocol

### What CAN be modular:
- Phase 2A simple mode details
- Phase 2B parallel mode details
- Detailed logging formats
- Specialization loading steps
- Context package definitions

### What should be REMOVED:
- "(NEW - CRITICAL)" annotations (40+ occurrences)
- Duplicate explanations
- Overly verbose examples
- Historical comments

---

## Questions for Review

1. Is the modular approach feasible for an LLM orchestrator?
2. Will compression lose important nuance?
3. Should we prioritize one phase over another?
4. How do we test that no functionality is lost?
5. Is there a simpler solution we're missing?

---

## References

- `agents/orchestrator.md` - Current orchestrator (2390 lines)
- `.claude/commands/bazinga.orchestrate.md` - Generated slash command
- `scripts/build-slash-commands.sh` - Build script
- `research/orchestrator-context-violation-analysis.md` - Previous analysis
