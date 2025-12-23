# Specialization Loading: Generic N-to-M Mapping Solution

**Date:** 2025-12-11
**Context:** Orchestrator hangs after specialization skill returns because it doesn't know how to map N skill outputs to M Task() calls
**Decision:** Pending analysis
**Status:** Proposed

---

## Problem Statement

The orchestrator loads specializations before spawning agents. The current implementation has a fundamental flaw: it assumes a 1:1 or 1:N mapping between skill calls and Task() calls, but the reality is more complex.

### Scenarios That Must Work

| Scenario | Skill Calls | Task Calls | Example |
|----------|-------------|------------|---------|
| **All same** | 1 | 4 | All groups need TypeScript/React |
| **All different** | 4 | 4 | Each group needs different stack |
| **Partial overlap** | 2 | 4 | Groups A,B=TypeScript, C,D=Python |
| **Complex overlap** | 3 | 4 | A=TS/React, B=TS/Vue, C,D=Python |
| **No specializations** | 0 | 4 | Specializations disabled |

### Current Bug

When the orchestrator calls Skill() once for shared specializations:
1. Skill outputs the block
2. Orchestrator receives output
3. **Orchestrator doesn't know what to do** - stops/hangs
4. Never calls the 4 Task() spawns

### Root Cause

The orchestrator templates describe a "TWO-TURN SPAWN SEQUENCE" but:
1. Don't handle the N:M mapping problem
2. Don't provide a clear algorithm for "after receiving skill output(s), spawn all agents"
3. Rely on implicit understanding rather than explicit state machine

---

## Solution: Explicit Specialization State Machine

### Core Insight

The orchestrator needs to track **which groups need which specializations** and **which specializations have been loaded**, then spawn all agents once all required specializations are ready.

### Data Structures

```
spec_requirements = {
  "A": ["typescript.md", "react.md"],
  "B": ["typescript.md", "react.md"],  # Same as A
  "C": ["python.md", "fastapi.md"],
  "D": ["python.md", "fastapi.md"],    # Same as C
}

spec_cache = {
  "typescript.md,react.md": null,      # Not loaded yet
  "python.md,fastapi.md": null,        # Not loaded yet
}

base_prompts = {
  "A": "...",  # Built from PM's task description
  "B": "...",
  "C": "...",
  "D": "...",
}
```

### Algorithm

```
PHASE 1: ANALYZE REQUIREMENTS
1. For each group, get specialization paths from DB
2. Deduplicate: group paths into unique "spec_keys"
3. Count: N = number of unique spec_keys

PHASE 2: LOAD SPECIALIZATIONS (Turn 1)
FOR each unique spec_key:
  1. Output [SPEC_CTX_START] block with paths
  2. Call Skill(command: "specialization-loader")
END this turn (wait for skill responses)

PHASE 3: CACHE AND SPAWN (Turn 2)
1. Parse each skill response
2. Extract block, store in spec_cache[spec_key]
3. For EACH group:
   a. Look up group's spec_key
   b. Get cached block from spec_cache
   c. Build FULL_PROMPT = cached_block + base_prompts[group]
   d. Call Task() for this group
4. Output only brief capsule before Tasks
```

### Key Properties

1. **Deduplication**: Same specialization paths → single skill call
2. **Caching**: Each unique spec_key is loaded once, reused for all groups needing it
3. **Deterministic**: Clear algorithm, no ambiguity about "what to do next"
4. **Generic**: Works for 1:1, 1:N, N:M mappings

---

## Implementation Options

### Option A: Inline Algorithm in Templates

Embed the full algorithm in phase_parallel.md and phase_simple.md.

**Pros:**
- Self-contained in existing files
- No new files needed

**Cons:**
- Templates already long (~700 lines)
- Duplicated logic between simple/parallel modes
- Hard to maintain

### Option B: Dedicated Specialization Workflow Template

Create `templates/orchestrator/specialization_workflow.md` that both phase templates reference.

**Pros:**
- Single source of truth
- Cleaner separation
- Easier to maintain

**Cons:**
- Another file to load
- Indirection

### Option C: State Machine in Orchestrator (Programmatic)

Track state explicitly with clear transitions:

```
States:
  INIT → ANALYZING → LOADING_SPECS → SPECS_READY → SPAWNING → DONE

Transitions:
  INIT → ANALYZING: Start specialization workflow
  ANALYZING → LOADING_SPECS: Found N unique spec_keys
  LOADING_SPECS → SPECS_READY: All skill responses received
  SPECS_READY → SPAWNING: Begin Task() calls
  SPAWNING → DONE: All Tasks called
```

**Pros:**
- Most explicit and robust
- Clear debugging (log current state)
- Handles edge cases naturally

**Cons:**
- More verbose in templates
- Might be overkill

### Option D: Simplified Inline with Clear Checkpoints

Keep it in templates but use explicit checkpoints:

```markdown
**CHECKPOINT 1: Spec Analysis Complete**
- unique_specs = [list of unique spec_key strings]
- groups_per_spec = {spec_key: [group_ids]}
- Proceed to Turn 1

**CHECKPOINT 2: All Specs Loaded**
- spec_cache = {spec_key: block_content}
- All entries populated? → Proceed to spawning
- Missing entries? → ERROR

**CHECKPOINT 3: All Tasks Spawned**
- Count Task() calls made
- Expected: len(groups)
- Actual: [verify]
```

**Pros:**
- Explicit without being overly complex
- Self-verifying
- Easy to debug

**Cons:**
- Still embedded in long template files

---

## Recommendation

**Option D: Simplified Inline with Clear Checkpoints**

This balances clarity with pragmatism:
1. Doesn't require new files
2. Has explicit verification points
3. The "checkpoint" pattern is easy to follow
4. Can be added to existing templates without major restructuring

---

## Detailed Implementation

### Step 1: Update phase_parallel.md Turn 1

```markdown
### PART B: Load Specializations (GENERIC N:M ALGORITHM)

**CHECKPOINT 1: Analyze Specialization Requirements**

1. For each group (A, B, C, D), retrieve specializations from task_group
2. Create spec_key for each group: `spec_key = sorted(specializations).join(",")`
3. Group by spec_key:
   ```
   spec_groups = {}
   for group in groups:
     key = make_spec_key(group.specializations)
     spec_groups[key] = spec_groups.get(key, []) + [group.id]
   ```
4. unique_specs = list(spec_groups.keys())
5. N = len(unique_specs)

**Output checkpoint:**
```
🔧 Spec Analysis: {N} unique specialization sets for {M} groups
   {spec_key_1}: Groups {A, B}
   {spec_key_2}: Groups {C, D}
```

**TURN 1: Load All Unique Specializations**

FOR i, spec_key in enumerate(unique_specs):
  1. Pick representative group (first in spec_groups[spec_key])
  2. Output context block:
     ```
     [SPEC_CTX_START spec_key={i}]
     Session ID: {session_id}
     Group ID: {representative_group}
     Agent Type: {agent_type}
     Model: {model}
     Specialization Paths: {paths as JSON}
     [SPEC_CTX_END]
     ```
  3. Call Skill(command: "specialization-loader")

END Turn 1 (wait for {N} skill responses)
```

### Step 2: Update phase_parallel.md Turn 2

```markdown
**TURN 2: Cache Blocks and Spawn All Agents**

**🔴🔴🔴 SILENT PROCESSING 🔴🔴🔴**

**CHECKPOINT 2: Cache All Spec Blocks**

FOR each skill response:
  1. Extract spec_key from response metadata (Group field)
  2. Extract block between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]
  3. Store: spec_cache[spec_key] = block

Verify: len(spec_cache) == N (all loaded)

**CHECKPOINT 3: Spawn All Agents**

FOR each group in groups:
  1. Get group's spec_key
  2. Get block from spec_cache[spec_key]
  3. Build: FULL_PROMPT = block + "\n\n---\n\n" + base_prompts[group]
  4. Call Task() for group

**Output only:**
```
🔧 Specializations: ✓ | {N} unique sets cached

Task(...)  # Group A
Task(...)  # Group B
Task(...)  # Group C
Task(...)  # Group D
```

**Verify:** Count of Task() calls == len(groups)
```

---

## Edge Cases

| Case | Handling |
|------|----------|
| Group has empty specializations | Skip spec loading for that group, use base_prompt only |
| Skill call fails | Use base_prompt for affected groups, log warning |
| All groups have empty specializations | Skip entire spec workflow, spawn directly |
| Duplicate spec_key detection fails | Fall back to calling skill per group (safe but inefficient) |

---

## Critical Analysis

### Pros ✅

1. **Generic**: Handles any N:M mapping naturally
2. **Efficient**: Deduplicates identical specialization requests
3. **Explicit**: Clear checkpoints prevent "what do I do now?" confusion
4. **Debuggable**: Each checkpoint can be logged
5. **Backwards compatible**: Still works for 1:1 and 1:N cases

### Cons ⚠️

1. **Complexity**: More logic than current simple approach
2. **Template bloat**: Adds ~50-100 lines to phase_parallel.md
3. **Spec key matching**: Relies on consistent path ordering
4. **Multiple skill responses**: Need to track which response matches which spec_key

### Verdict

The complexity is justified because:
1. Current approach is broken for real-world cases
2. The "hang" bug wastes user time
3. Checkpoints make debugging easy
4. Extra lines are documentation, not code

---

## Migration Path

1. Update phase_parallel.md with new algorithm
2. Update phase_simple.md (simpler: always 1 group, so N=1 or N=0)
3. Update skill to include spec_key in metadata output
4. Test with: all-same, all-different, partial-overlap scenarios

---

## Open Questions

1. Should spec_key be computed by orchestrator or skill?
2. How to handle version-specific specializations (Java 8 vs Java 17)?
3. Should we cache specs across groups AND across sessions?

---

## References

- Current bug: Orchestrator hangs after skill output
- Related: phase_parallel.md TWO-TURN SPAWN SEQUENCE
- Related: specialization-loader/SKILL.md
