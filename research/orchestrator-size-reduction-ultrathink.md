# Orchestrator Size Reduction: Ultrathink Analysis

**Date:** 2025-12-22
**Context:** The orchestrator.md (2496 lines, ~25610 tokens) exceeds Claude's 25000 token read limit
**Decision:** Extract content into modular files without losing functionality
**Status:** Proposed
**Reviewed by:** (pending)

---

## Problem Statement

The `agents/orchestrator.md` file has grown too large:
- **2496 lines** / **~25610 tokens**
- Exceeds Claude's 25000 token file read limit
- Built via `build-slash-commands.sh` → `.claude/commands/bazinga.orchestrate.md`
- The orchestrator runs inline (not as spawned agent), so it needs the full context

**Impact:** The orchestrator cannot be read as a single file, breaking the build process and execution.

---

## Current Section Analysis

| Section | Lines | Purpose | Extractable? |
|---------|-------|---------|--------------|
| MANDATORY FIRST ACTION | 422 | PM understanding capture, response parsing | ⚠️ Partially - examples can move |
| SCOPE PRESERVATION (RESUME) | 308 | Resume context handling | ✅ Yes - reference file |
| Initialization (First Run Only) | 218 | Session setup, config loading | ⚠️ Partially - checklist can move |
| YOU ARE A COORDINATOR | 183 | Role enforcement, forbidden actions | ❌ Critical - must stay inline |
| Tech Stack Detection | 130 | Scout spawning, context creation | ⚠️ Partially - examples can move |
| ROLE DRIFT PREVENTION | 129 | Self-check discipline | ❌ Critical - must stay inline |
| PRE-OUTPUT SELF-CHECK | 112 | Validation before output | ⚠️ Merge with role drift |
| §Prompt Building | 101 | Build agent prompts | ✅ Already refs templates/ |
| SCOPE CONTINUITY CHECK | 100 | Scope verification each turn | ⚠️ Can merge/compress |
| Phase 1: Spawn PM | 92 | PM spawn instructions | ⚠️ Examples can move |
| POST-COMPACTION RECOVERY | 82 | Recovery after context loss | ✅ Yes - reference file |
| §Workflow Routing | 59 | State machine transitions | ✅ Already refs templates/ |
| Completion | 48 | Completion handling | ⚠️ Refs shutdown_protocol.md |
| Response Parsing | 46 | Parse agent responses | ✅ Already refs templates/ |

---

## Extraction Strategy

### Tier 1: Already Externalized (Just Remove Inline Duplication)

These sections reference external files but duplicate content inline:

1. **Response Parsing** (46 lines) → `templates/response_parsing.md`
   - Current: Duplicates extraction patterns inline
   - Fix: Keep only the `**Use templates/response_parsing.md**` reference

2. **Prompt Building** (101 lines) → Already uses prompt-builder skill
   - Current: Has inline examples that duplicate skill docs
   - Fix: Keep brief instructions, remove detailed examples

3. **Workflow Routing** (59 lines) → `templates/orchestrator/phase_simple.md`, `phase_parallel.md`
   - Current: References files but has inline duplicates
   - Fix: Just reference the files

4. **Shutdown Protocol** (16 lines) → `templates/shutdown_protocol.md`
   - Current: Brief reference (good)
   - Fix: None needed

**Estimated savings: ~150 lines**

### Tier 2: Extract to New Reference Files

These are large sections that can become separate files read on-demand:

1. **SCOPE PRESERVATION (308 lines)** → `templates/orchestrator/scope_preservation.md`
   - Only needed when resuming a session
   - Orchestrator can read this file ONLY on resume

2. **POST-COMPACTION RECOVERY (82 lines)** → Merge into scope_preservation.md
   - Related to resume scenarios
   - Total: ~390 lines in one reference file

3. **PM Understanding Capture (in MANDATORY FIRST ACTION)** → `templates/orchestrator/pm_spawn.md`
   - The 200+ lines of PM response parsing examples
   - Keep inline: just the spawn instruction and reference

**Estimated savings: ~400 lines**

### Tier 3: Merge and Compress Redundant Sections

These sections have overlapping content:

1. **Merge role enforcement sections:**
   - YOU ARE A COORDINATOR (183 lines)
   - ROLE DRIFT PREVENTION (129 lines)
   - PRE-OUTPUT SELF-CHECK (112 lines)
   - SCOPE CONTINUITY CHECK (100 lines)

   These all say variations of "don't implement, just coordinate"

   **Proposed merge:** Single "ORCHESTRATOR DISCIPLINE" section (~150 lines)
   - Core rules (non-negotiable)
   - Self-check checklist (compact)
   - Remove repetitive examples

**Estimated savings: ~370 lines**

### Tier 4: Remove Verbose Examples

Many sections have extensive examples that could be shortened:

1. **Tech Stack Detection (130 lines)**
   - Has 3 full JSON examples (~60 lines)
   - Keep 1 minimal example, reference tech_stack_scout.md for full examples

2. **Initialization (218 lines)**
   - Has verbose startup checklists
   - Compress to essential steps

3. **MANDATORY FIRST ACTION (422 lines)**
   - Has extensive PM response parsing examples
   - These duplicate templates/response_parsing.md

**Estimated savings: ~200 lines**

---

## Proposed New Structure

```
agents/orchestrator.md (~1200 lines target)
├── Header/Frontmatter (30 lines)
├── User Requirements (5 lines)
├── Overview (30 lines)
├── ORCHESTRATOR DISCIPLINE (150 lines) - merged from 4 sections
├── PROMPT-BUILDER MANDATE (40 lines)
├── Initialization (100 lines) - compressed
├── Tech Stack Detection (60 lines) - compressed
├── Phase 1: PM Spawn (50 lines) - refs templates/orchestrator/pm_spawn.md
├── Phase 2A/2B: Execution (80 lines) - refs phase_simple.md/phase_parallel.md
├── Workflow Routing (30 lines) - just refs
├── Completion (30 lines) - refs shutdown_protocol.md
├── Error Handling (30 lines)
├── Key Principles (15 lines)

templates/orchestrator/
├── phase_simple.md (existing)
├── phase_parallel.md (existing)
├── scope_preservation.md (NEW - 400 lines)
├── pm_spawn.md (NEW - 250 lines)
└── initialization_checklist.md (NEW - 100 lines)
```

---

## Risk Analysis

### ✅ Low Risk Extractions
- Response parsing → already externalized
- Workflow routing → already externalized
- Shutdown protocol → already externalized

### ⚠️ Medium Risk Extractions
- Scope preservation → read on-demand adds latency
- PM spawn details → must ensure orchestrator reads before spawning

### ❌ High Risk (DO NOT Extract)
- Role enforcement rules → must be always visible
- Self-check discipline → must be always visible
- Core workflow state machine → must be always visible

---

## Implementation Plan

### Phase 1: Remove Inline Duplicates (~150 lines saved)
1. Remove inline response parsing patterns (keep just the reference)
2. Remove inline prompt building examples (keep just the skill reference)
3. Remove inline workflow routing details (keep just file references)

### Phase 2: Create New Reference Files (~400 lines saved)
1. Create `templates/orchestrator/scope_preservation.md` (390 lines)
2. Create `templates/orchestrator/pm_spawn.md` (250 lines)
3. Update orchestrator to `Read()` these files when needed

### Phase 3: Merge Redundant Sections (~370 lines saved)
1. Merge 4 role enforcement sections into 1 compact section
2. Remove repetitive examples
3. Keep only unique rules/checks

### Phase 4: Compress Verbose Examples (~200 lines saved)
1. Reduce JSON examples in Tech Stack Detection
2. Compress initialization checklist
3. Remove PM response parsing examples (already in templates/)

---

## Success Criteria

1. `agents/orchestrator.md` < 1500 lines (~18000 tokens)
2. All functionality preserved (verified by integration test)
3. No behavioral changes to orchestration workflow
4. Clean extraction with clear references

---

## Questions for Review

1. Should scope_preservation be read on every turn (safe but slow) or only on resume detection (fast but risky)?

2. The role enforcement sections are repetitive but serve as "constant reminders". Is there value in keeping some repetition for emphasis?

3. Should we create a "orchestrator kernel" concept - essential rules that MUST stay inline vs "reference material" that can be external?

---

## Appendix: Token Budget Estimate

Current: ~25,610 tokens

Proposed reductions:
- Tier 1 (remove duplicates): -1,800 tokens
- Tier 2 (extract to files): -4,800 tokens
- Tier 3 (merge redundant): -4,400 tokens
- Tier 4 (compress examples): -2,400 tokens

**Target: ~12,200 tokens (~1200 lines)**

This gives 50% headroom for future additions.
