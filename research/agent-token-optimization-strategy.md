# Agent Token Optimization Strategy

**Date:** 2025-12-02
**Context:** Agent file sizes have grown beyond token limits, particularly project_manager.md and orchestrator.md
**Decision:** Extract only Spec-Kit section to `templates/pm_speckit.md` - PM reads on-demand
**Status:** Reviewed & Approved

---

## Problem Statement

The BAZINGA multi-agent orchestration system uses markdown files to define agent behaviors. These files are loaded into LLM context when agents are spawned. Two files have exceeded or approached the ~25,000 token limit:

| Agent File | Bytes | Est. Tokens | Status |
|------------|-------|-------------|--------|
| orchestrator.md | 98KB | ~24,500 | ⚠️ Near limit |
| project_manager.md | 90KB | ~22,500 | 🔴 Exceeded limit |
| senior_software_engineer.md | 55KB | ~13,900 | ✅ OK |
| developer.md | 49KB | ~12,250 | ✅ OK |
| techlead.md | 39KB | ~9,700 | ✅ OK |
| qa_expert.md | 36KB | ~9,000 | ✅ OK |
| investigator.md | 26KB | ~6,400 | ✅ OK |
| requirements_engineer.md | 20KB | ~5,000 | ✅ OK |
| orchestrator_speckit.md | 12KB | ~3,000 | ✅ OK |

**Impact:**
- Token overflow causes truncation of agent instructions
- Critical instructions at end of file may be lost
- Agent behavior becomes unpredictable

---

## Solution: Modular Reference Architecture

### 🔴 CRITICAL: Zero Content Loss Policy

**ALL content MUST be preserved.** This is NOT a deletion exercise - it's a reorganization:
- Every line of the original files must exist somewhere
- Extracted content goes to reference files
- Reference pointers added to main files
- Validation: `wc -l` before and after must account for all lines

### Core Principle

Split agent files into:
1. **Core instructions** (in main agent file) - Essential behavior, decision logic, tool restrictions
2. **Reference materials** (in separate files) - Examples, templates, detailed formats

### Proposed Directory Structure

```
agents/
├── project_manager.md          # Core PM instructions (~15K tokens target)
├── orchestrator.md             # Core orchestrator instructions (~18K tokens target)
├── references/
│   ├── pm_examples.md          # PM example scenarios, output formats
│   ├── pm_speckit.md           # Spec-Kit integration details
│   ├── pm_bazinga_validation.md # Detailed BAZINGA validation examples
│   ├── orchestrator_examples.md # Orchestrator routing examples
│   └── shared_formats.md       # Shared output formats across agents
└── [other agents unchanged]
```

### Reference Loading Strategy

Agents can load references when needed using Read tool:
```markdown
**For detailed examples, see:** `agents/references/pm_examples.md`
```

This is preferable to always including everything because:
- Core instructions always fit in context
- Examples loaded on-demand when agent encounters unfamiliar scenario
- Reduces base context overhead

---

## Critical Analysis

### Pros ✅

1. **Guaranteed context fit** - Core instructions never truncated
2. **Maintainability** - Easier to update examples separately
3. **Flexibility** - Can add more examples without bloating core
4. **Debugging** - Clear separation of "what" vs "how"

### Cons ⚠️

1. **Extra tool calls** - Agent may need to Read reference files
2. **Latency** - Additional file reads add time
3. **Complexity** - More files to maintain
4. **Risk of drift** - References may become outdated

### Verdict

The pros outweigh cons. Token overflow is a hard blocker; extra tool calls are acceptable overhead.

---

## Implementation Details

### Phase 1: Identify Extraction Candidates in project_manager.md

Based on file analysis (2604 lines, ~22,500 tokens):

| Section | Lines | Est. Tokens | Action |
|---------|-------|-------------|--------|
| Frontmatter + Role | 1-78 | ~500 | KEEP |
| Critical/Skeptical section | 13-35 | ~300 | KEEP |
| Workflow overview | 39-78 | ~400 | KEEP |
| Task Type Classification | 79-160 | ~800 | KEEP (important logic) |
| Security Classification | 162-194 | ~400 | KEEP |
| Complexity Scoring | 194-240 | ~400 | KEEP |
| Tool Restrictions | 457-555 | ~600 | KEEP |
| **Routing Examples** | 563-765 | ~1,500 | **EXTRACT** (verbose examples) |
| **BAZINGA Validation Detail** | 802-1085 | ~2,000 | **EXTRACT** (detailed paths) |
| **Spec-Kit Integration** | 1152-1660 | ~3,500 | **EXTRACT** (entire section) |
| Phase 1 Planning | 1662-1920 | ~1,800 | TRIM (reduce examples) |
| Phase 2 Progress | 2336-2435 | ~700 | KEEP |
| Error Handling | 2514-2542 | ~200 | KEEP |
| Final Checklist | 2565-2605 | ~300 | KEEP |

**Estimated savings:** ~7,000 tokens (from ~22,500 to ~15,500)

### Phase 2: Identify Extraction Candidates in orchestrator.md

Need to analyze separately, but likely candidates:
- Detailed routing examples
- Error handling verbose examples
- Agent spawn templates

### Phase 3: Create Reference Files

**agents/references/pm_examples.md** (~3,500 tokens):
- Routing instruction examples (lines 563-765)
- Investigation examples
- Status update formats

**agents/references/pm_bazinga_validation.md** (~2,000 tokens):
- Path A/B/C detailed examples
- Pre-BAZINGA verification steps
- Self-adversarial check examples

**agents/references/pm_speckit.md** (~3,500 tokens):
- Full Spec-Kit integration mode
- Task parsing examples
- Dual tracking requirements

### Phase 4: Update Core Files

Add reference pointers where content was extracted:
```markdown
### Routing Instructions

**For detailed routing examples, see:** `agents/references/pm_examples.md`

[Keep only the essential routing logic here]
```

---

## Comparison to Alternatives

### Alternative 1: Aggressive Trimming (No Reference Files)

- **Approach:** Simply delete verbose examples, keep only essential
- **Pro:** Simpler, no new files
- **Con:** Loses valuable context that helps agent behavior
- **Verdict:** Rejected - examples improve agent accuracy

### Alternative 2: Dynamic Loading via Skill

- **Approach:** Create a skill that loads agent references
- **Pro:** Cleaner abstraction
- **Con:** Over-engineered, adds dependency
- **Verdict:** Rejected - Read tool is sufficient

### Alternative 3: Split into Sub-Agents

- **Approach:** Create PM-Planning, PM-Tracking, PM-Validation sub-agents
- **Pro:** Each agent smaller and focused
- **Con:** Increases orchestration complexity, more agent spawns
- **Verdict:** Rejected - current architecture works well

---

## Decision Rationale

The **Modular Reference Architecture** (proposed solution) is best because:

1. **Minimal disruption** - Core agent logic unchanged
2. **Proven pattern** - Similar to how documentation is structured
3. **Reversible** - Can inline references back if needed
4. **Scalable** - Can extract more as agents grow

---

## Implementation Plan

### Step 1: Create Reference Directory
```bash
mkdir -p agents/references
```

### Step 2: Extract PM Examples
- Copy lines 563-765 (routing examples) to `pm_examples.md`
- Copy lines 802-1085 (BAZINGA validation) to `pm_bazinga_validation.md`
- Copy lines 1152-1660 (Spec-Kit) to `pm_speckit.md`

### Step 3: Update project_manager.md
- Replace extracted sections with reference pointers
- Add brief summaries where needed
- Verify token count is under 18,000

### Step 4: Test Agent Behavior
- Run orchestration with modified PM
- Verify PM can still access examples when needed
- Check for any behavioral regressions

### Step 5: Apply Same Pattern to orchestrator.md (if needed)
- Analyze and extract similar patterns
- Target ~20,000 tokens

---

## Token Budget Targets

| File | Current | Target | Reduction |
|------|---------|--------|-----------|
| project_manager.md | ~22,500 | ~15,000 | 33% |
| orchestrator.md | ~24,500 | ~18,000 | 27% |

**Buffer:** 5,000-7,000 tokens for future growth

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agent misses important example | MEDIUM | Include brief inline summary, point to reference |
| Reference files become outdated | LOW | Review references when updating core file |
| Extra latency from file reads | LOW | Agent caches after first read in session |
| Breaking existing orchestrations | MEDIUM | Test thoroughly before deploying |

---

## Success Criteria

1. ✅ project_manager.md under 18,000 tokens
2. ✅ orchestrator.md under 20,000 tokens
3. ✅ All existing orchestration tests pass
4. ✅ Agent behavior unchanged in normal scenarios
5. ✅ Reference files are complete and accurate

---

## Lessons Learned

*(To be filled after implementation)*

---

## References

- Agent files: `agents/*.md`
- Current token analysis: Manual calculation (bytes/4)
- Token limit source: Claude context window constraints

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-02)

### Consensus Points

1. **Keep enforcement logic in core** - BAZINGA validation, self-adversarial checks, success criteria gates must never be extracted
2. **Use allowed paths** - PM can only Read from `bazinga/...` paths, so references must go to `templates/`
3. **Token measurement** - bytes/4 is approximate; real tokenization may differ

### Incorporated Feedback

1. ✅ **Changed reference location** from `agents/references/` to `templates/` (allowed Read path)
2. ✅ **Kept BAZINGA validation in core** - only extracting Spec-Kit section (optional mode)
3. ✅ **Minimal extraction** - only ~3,890 tokens extracted (Spec-Kit only), not the full 7,000 proposed

### Rejected Suggestions

1. ❌ **Build-time compilation** - Over-engineered for current needs; simple extraction sufficient
2. ❌ **Conditional prompt assembly** - Would require orchestrator changes; on-demand Read is simpler
3. ❌ **Token budget CI enforcement** - Good idea for future, not blocking current fix

---

## Final Decision

### What We're Doing

**Extract ONLY the Spec-Kit Integration section** (lines 1152-1660, ~3,890 tokens) from `project_manager.md`:

| Before | After |
|--------|-------|
| project_manager.md: ~22,446 tokens | project_manager.md: ~18,556 tokens |
| (no separate file) | templates/pm_speckit.md: ~3,890 tokens |

### Why This Approach

1. **Minimal change** - Only extract one well-bounded section
2. **Zero content loss** - All content preserved in template file
3. **On-demand loading** - PM reads template only when Spec-Kit mode is active
4. **Follows existing pattern** - Uses `templates/` like other templates
5. **Enforcement logic stays** - BAZINGA validation remains in core PM

### Implementation

1. Create `templates/pm_speckit.md` with extracted content
2. Replace section in `project_manager.md` with reference pointer:
   ```markdown
   ## 🆕 SPEC-KIT INTEGRATION MODE

   **When orchestrator signals Spec-Kit mode, read:** `templates/pm_speckit.md`

   This template contains the full Spec-Kit integration workflow including:
   - Reading spec-kit artifacts (spec.md, tasks.md, plan.md)
   - Parsing tasks.md format with [P] and [US] markers
   - Creating BAZINGA groups from spec-kit tasks
   - Dual progress tracking (tasks.md + pm_state.json)
   ```
3. Validate token count is under 20,000

