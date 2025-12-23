# PM Agent File Size Reduction: Analysis and Strategies

**Date:** 2025-12-17
**Context:** PM agent file (agents/project_manager.md) is ~91k chars, ~25k tokens - exceeds Claude's 25k file read limit
**Decision:** Reduce PM agent file size while preserving all essential functionality
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

The PM agent file cannot be loaded by spawned agents because it exceeds Claude's 25,000 token file read limit:

```
Current: ~91,132 characters, 2,518 lines, ~25,183 tokens
Limit:   25,000 tokens
Overage: ~183 tokens (0.7% over)
```

Even with no extras (no specialization, no project context, no feedback), the PM agent file alone exceeds the limit. This is a fundamental blocker for the BAZINGA orchestration system.

## Current File Analysis

### Section-by-Section Token Estimates

| Section | Lines | Est. Tokens | Purpose |
|---------|-------|-------------|---------|
| **Core Identity** (1-119) | 119 | ~1,700 | Role, critical behaviors, workflow overview |
| **Task Classification** (120-234) | 114 | ~1,800 | Research vs implementation, security flags |
| **Complexity Scoring** (235-291) | 56 | ~800 | Developer tier assignment |
| **Autonomy Protocol** (293-497) | 204 | ~3,200 | Clarification rules, assumptions |
| **Tool Restrictions** (498-603) | 105 | ~1,600 | Allowed/forbidden tools |
| **Routing Instructions** (605-901) | 296 | ~4,500 | Status codes, examples |
| **BAZINGA Validation** (903-1097) | 194 | ~3,000 | Pre-BAZINGA checks, paths A/B/C |
| **Metrics & Advanced** (1098-1163) | 65 | ~1,000 | Quality gates, velocity |
| **Spec-Kit Reference** (1164-1176) | 12 | ~150 | Template reference (GOOD PATTERN) |
| **Phase 1: Planning** (1179-2056) | 877 | ~10,500 | Full planning workflow |
| **Failure Handling** (2059-2151) | 92 | ~1,400 | Tech Lead changes, retries |
| **Phase 2: Progress** (2155-2294) | 139 | ~2,100 | Resume, tracking |
| **Guidelines/Checks** (2296-2518) | 222 | ~2,400 | Decisions, errors, checklists |
| **TOTAL** | 2518 | **~24,150** | |

*Note: Actual Claude tokenization showed 25,183 tokens - this analysis is approximate.*

### Redundancy Analysis

**Pattern 1: Repeated "WRONG vs CORRECT" Examples**
Many sections have lengthy examples showing wrong and correct approaches. These are valuable but verbose:
- Routing instructions: 4 separate WRONG/CORRECT blocks (~300 tokens each)
- Autonomy protocol: 3 WRONG/CORRECT blocks
- BAZINGA validation: Multiple path examples

**Estimated bloat from redundant examples: ~2,500-3,000 tokens**

**Pattern 2: Same Rule Stated Multiple Times**
Several critical rules appear 2-4 times with slightly different wording:
- "Never ask user questions" - appears ~8 times
- "You coordinate, don't implement" - appears ~6 times
- "Only PM sends BAZINGA" - appears ~5 times

**Estimated bloat from repetition: ~800-1,200 tokens**

**Pattern 3: Embedded JSON/Markdown Templates**
Long code blocks that could be externalized:
- PM state JSON template (~200 tokens)
- Task group creation template (~150 tokens)
- BAZINGA response template (~180 tokens)
- Reasoning save template (~120 tokens)

**Estimated tokens that could be externalized: ~650 tokens**

**Pattern 4: Over-Specified Edge Cases**
Some sections handle edge cases that may never occur:
- Orphaned plan detection (lines 1202-1217) - complex logic for rare scenario
- Path B "strict requirements" (lines 1047-1096) - very detailed for rare case

**Estimated tokens in rare edge cases: ~400-600 tokens**

---

## Reduction Strategies

### Strategy 1: Reference File Pattern (PROVEN SAFE)

**The Spec-Kit section already uses this pattern successfully:**
```markdown
## SPEC-KIT INTEGRATION MODE

**When orchestrator signals SPEC-KIT INTEGRATION MODE, read:** `templates/pm_speckit.md`

This template contains the full Spec-Kit integration workflow...
```

**Apply to other verbose sections:**

| Section | Move To | Est. Savings |
|---------|---------|--------------|
| Task Classification details | `templates/pm_task_classification.md` | ~1,200 tokens |
| Complexity Scoring table | `templates/pm_complexity_scoring.md` | ~500 tokens |
| Autonomy Protocol details | `templates/pm_autonomy.md` | ~2,000 tokens |
| BAZINGA Validation paths | `templates/pm_bazinga_validation.md` | ~2,000 tokens |
| Phase 1 detailed steps | `templates/pm_planning_steps.md` | ~4,000 tokens |

**Total potential savings: ~9,700 tokens (39%)**

**Risk Assessment:**
- LOW: PM can read these files when needed
- MITIGATION: Keep critical rules in main file, move only detailed procedures
- PRECEDENT: Spec-Kit pattern already works

### Strategy 2: Consolidate Redundant Examples

**Before (3 separate examples for same concept):**
```markdown
**WRONG:**
```
Would you like me to continue?
```

**CORRECT:**
```
## PM Status: CONTINUE
Assigning developer to fix issues.
```

---

**WRONG:**
```
Do you want me to proceed with fixing?
```

**CORRECT:**
```
## PM Status: REASSIGNING_FOR_FIXES
Orchestrator should spawn developer...
```
```

**After (single consolidated example):**
```markdown
**Examples of autonomous decision-making:**
- Never ask: "Would you like me to continue?" / "Should I proceed?"
- Always: Output status code + next action without asking permission

Example:
❌ "Do you want me to continue?"
✅ `## PM Status: CONTINUE` + Next Action
```

**Estimated savings: ~2,000 tokens (8%)**

**Risk Assessment:**
- LOW: Condensed examples preserve the lesson
- MITIGATION: Keep one clear example per concept

### Strategy 3: Deduplicate Repeated Rules

**Consolidate repeated rules into a single "Golden Rules" section:**

```markdown
## Golden Rules (Always Apply)

1. **Never ask user questions** - You are fully autonomous
2. **Never implement code** - You coordinate, developers implement
3. **Only PM sends BAZINGA** - Tech Lead approves groups, you approve project
4. **Continue until 100% complete** - No partial completion
5. **Use bazinga-db for state** - Never inline SQL
```

Then remove scattered repetitions throughout the file.

**Estimated savings: ~800 tokens (3%)**

**Risk Assessment:**
- LOW: Rules are still present and emphasized
- MITIGATION: Reference "See Golden Rules" at key decision points

### Strategy 4: Compress JSON Templates

**Before:**
```markdown
State Data: {
  "session_id": "[session_id]",
  "initial_branch": "[from session data queried in Sub-step 5.1]",
  "mode": "simple" or "parallel",
  "mode_reasoning": "Explanation of why you chose this mode",
  "original_requirements": "Full user requirements",
  "success_criteria": [
    {"criterion": "Coverage >70%", "status": "pending", "actual": null, "evidence": null},
    {"criterion": "All tests passing", "status": "pending", "actual": null, "evidence": null}
  ],
  ...
}
```

**After:**
```markdown
State Data: See `templates/pm_state_schema.json` for full schema.
Required fields: session_id, mode, mode_reasoning, success_criteria[], task_groups[]
```

**Estimated savings: ~500 tokens (2%)**

### Strategy 5: Simplify Rare Edge Cases

**Move to appendix or remove:**
- Orphaned plan detection (complex but rare)
- Path B external blockers (very rare, most use Path C)
- 5-minute clarification timeout (rarely triggered)

**Keep simplified reference:**
```markdown
**Edge Cases:** See `templates/pm_edge_cases.md` for: orphaned plans, external blockers, clarification timeouts
```

**Estimated savings: ~400 tokens (2%)**

---

## Recommended Approach: Tiered Implementation

### Tier 1: Immediate (Low Risk, High Impact)
Apply Strategy 1 to move detailed procedures to reference files.

**Files to create:**
1. `templates/pm_task_classification.md` - Task type detection, security flags
2. `templates/pm_complexity_scoring.md` - Scoring factors table
3. `templates/pm_planning_steps.md` - Detailed Phase 1 steps (3.5, 5.1-5.3)
4. `templates/pm_bazinga_validation.md` - Paths A/B/C details

**Keep in main file:**
- Core identity and role
- Critical behaviors (skeptical, honest, non-lenient)
- Workflow overview (the big picture)
- Status codes and when to use them
- State management basics
- Golden rules
- When to read reference files

**Expected result: ~15,000 tokens (40% reduction)**

### Tier 2: Refinement (Medium Risk, Medium Impact)
Apply Strategies 2-4 to consolidate examples and deduplicate.

**Expected additional savings: ~3,000 tokens**

**Result after Tier 2: ~12,000 tokens (52% reduction)**

### Tier 3: Aggressive (Higher Risk)
Apply Strategy 5 to simplify rare edge cases.

**Expected additional savings: ~400 tokens**

**Final target: ~11,600 tokens (54% reduction)**

---

## Implementation Plan

### Phase 1: Create Reference Files (Safe)

1. Create `templates/pm_task_classification.md`
   - Move lines 120-234 (task type classification details)
   - Keep summary in main file

2. Create `templates/pm_complexity_scoring.md`
   - Move lines 235-291 (scoring factors table)
   - Keep quick reference in main file

3. Create `templates/pm_planning_steps.md`
   - Move lines 1281-1798 (detailed Step 3.5, Step 5)
   - Keep step overview in main file

4. Create `templates/pm_bazinga_validation.md`
   - Move lines 903-1096 (Paths A/B/C details)
   - Keep validation summary in main file

### Phase 2: Update Main File

Replace moved content with references:
```markdown
### Task Classification
**Read:** `templates/pm_task_classification.md` for full classification rules.

Quick reference:
- `[R]` marker or research keywords → research type → spawn RE
- Default → implementation type → use complexity scoring
```

### Phase 3: Test

1. Build PM prompt with prompt_builder.py
2. Verify token count < 24,000 (with safety margin)
3. Run integration test
4. Verify PM can read reference files when needed

---

## Critical Constraints

**MUST KEEP in main file:**
- Identity ("You are the PROJECT MANAGER")
- Critical behaviors (skeptical, honest, scope immutable)
- Status codes (PLANNING_COMPLETE, CONTINUE, BAZINGA, etc.)
- When to read reference files
- Routing instructions for orchestrator
- Final checklist before returning

**CAN MOVE to reference files:**
- Detailed procedures with step-by-step instructions
- Long examples (WRONG vs CORRECT patterns)
- JSON/Markdown templates
- Edge case handling
- Scoring tables and formulas

**MUST NOT CHANGE:**
- Behavior semantics (PM should behave identically)
- Critical decision logic
- State management commands
- BAZINGA validation requirements

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PM fails to read reference file | HIGH | Include fallback summary in main file |
| Reference file not found | HIGH | Check file existence in prompt_builder.py |
| Split logic causes confusion | MEDIUM | Clear "When to read" triggers in main file |
| Maintenance burden increases | LOW | Use pre-commit hook to validate consistency |
| Token budget exceeded anyway | LOW | Multiple reference files allow selective loading |

---

## Success Criteria

1. PM agent file < 16,000 tokens (leaving 9k for task requirements)
2. Integration test passes
3. PM behavior unchanged (no regression)
4. Reference files are discoverable and readable
5. No circular dependencies between files

---

## Alternative Approaches Considered

### A: Rewrite PM Agent from Scratch
- PRO: Could be more concise
- CON: High risk of losing critical behaviors, long revalidation
- VERDICT: Rejected - too risky

### B: Use Include Directives
- PRO: Single file perception, automatic assembly
- CON: Requires tooling changes, not currently supported
- VERDICT: Rejected - infrastructure change needed

### C: Reduce PM Responsibilities
- PRO: Simpler PM = smaller file
- CON: Changes system architecture, reduces PM capabilities
- VERDICT: Rejected - degrades functionality

### D: Reference File Pattern (Selected)
- PRO: Proven pattern (Spec-Kit already uses it), low risk
- CON: PM must read additional files when needed
- VERDICT: Selected - best balance of safety and effectiveness

---

## Next Steps

1. Get external LLM reviews on this plan
2. User approval
3. Implement Tier 1 (reference files)
4. Test with integration test
5. If successful, consider Tier 2 refinements

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-17)

### Consensus Points (Validated)

1. **Direction is sound** - Externalizing verbose procedures and keeping a marker-rich kernel is the right approach
2. **Reference file pattern proven** - Spec-Kit already uses this successfully
3. **40-55% reduction achievable** - With proper implementation, target is realistic

### Incorporated Feedback

#### 1. Spawn Profile Strategy (NEW - from LLM review)

**Critical insight:** PM is spawned multiple times for different purposes:
- Initial planning (needs task classification, complexity scoring, full planning steps)
- Progress tracking (needs status handling, routing, minimal context)
- BAZINGA validation (needs validation checklist, completion report format)

**Action:** Enhance prompt_builder.py to support spawn profiles:
```python
PM_PROFILES = {
    'planning': ['pm_task_classification.md', 'pm_complexity_scoring.md', 'pm_planning_steps.md'],
    'progress': ['pm_routing.md', 'pm_status_codes.md'],
    'bazinga': ['pm_bazinga_validation.md', 'pm_completion_format.md']
}
```

This allows including only sections needed for each spawn type, maximizing token efficiency.

#### 2. Minimal PM Kernel Definition (NEW - from LLM review)

The main `agents/project_manager.md` file MUST retain:
- Identity ("You are the PROJECT MANAGER...")
- Golden Rules (critical behaviors, autonomy)
- Status codes dictionary (PLANNING_COMPLETE, CONTINUE, BAZINGA, etc.)
- Mandatory output formats (orchestrator parsing depends on these)
- Required markers (orchestrator routing depends on these)
- bazinga-db mandates (state persistence rules)
- Reference file triggers ("When X, read template Y")

Everything else CAN be moved to templates.

#### 3. Template Size Constraints (ENHANCED - from LLM review)

Split templates by topic, each <3-4k tokens:
- `pm_task_classification.md` (~1,200 tokens)
- `pm_complexity_scoring.md` (~500 tokens)
- `pm_autonomy.md` (~2,000 tokens)
- `pm_planning_steps.md` (~4,000 tokens) - largest, consider further split
- `pm_bazinga_validation.md` (~2,000 tokens)
- `pm_routing.md` (~1,500 tokens)

**Rationale:** Smaller templates = faster reads + lower failure risk if one fails

#### 4. Prompt-Builder Integration (NEW - from LLM review)

Extend `.claude/skills/prompt-builder/scripts/prompt_builder.py` to:

1. **Validate template existence** before building prompts:
```python
def validate_template_paths(templates: list[str]) -> list[str]:
    """Check templates exist, return list of valid paths."""
    valid = []
    for t in templates:
        if os.path.exists(t):
            valid.append(t)
        else:
            log_warning(f"Template not found: {t}")
    return valid
```

2. **Include template versions** in prompt metadata for debugging

3. **Fallback handling** - if template missing, include minimal inline summary

#### 5. CI Token Gates (NEW - from LLM review)

Add automated checks in CI:
```yaml
# .github/workflows/validate-prompts.yml
- name: Token budget validation
  run: |
    python scripts/validate_prompt_tokens.py agents/project_manager.md --max 16000
    python scripts/validate_required_markers.py agents/project_manager.md
```

**Benefits:** Catch size regressions before merge, ensure markers preserved

#### 6. Shared Templates for De-duplication (NEW - from LLM review)

Create shared templates used by multiple agents (PM, TL, SSE):
- `templates/shared/golden_rules.md` - autonomy, no-asking, continue until done
- `templates/shared/status_dictionary.md` - status codes all agents use
- `templates/shared/output_formats.md` - markdown formatting, structured responses

**Benefits:** Single source of truth, reduces drift, smaller per-agent files

### Rejected Suggestions (With Reasoning)

#### 1. "Profile-based assembly with different kernels"
**Rejected because:** Too complex for current orchestrator. Would require spawner to know PM lifecycle stage. Current design: single PM file + selective template reads is simpler.

**Compromise:** Document which templates PM should read at each phase, but don't require orchestrator changes.

#### 2. "Multi-agent refactor for SSE/TL simultaneously"
**Rejected because:** Scope creep. PM is the immediate blocker. SSE/TL can be addressed after PM is fixed.

**Deferred to:** Future work after PM reduction validated.

#### 3. "Context-pack injection"
**Rejected because:** Requires infrastructure changes to prompt-builder. Current Read-based approach works with existing tools.

### Updated Implementation Plan

**Phase 1: Create Reference Files (Immediate)**
1. Create PM kernel definition (identity + golden rules + markers + status codes)
2. Create template files as specified
3. Update main PM file with reference triggers

**Phase 2: Prompt-Builder Enhancement**
1. Add template validation
2. Add token counting with actual tokenizer
3. Add fallback handling for missing templates

**Phase 3: Testing & CI**
1. Add token budget tests
2. Add marker validation tests
3. Run integration test

**Phase 4: Documentation**
1. Update agent development guide
2. Document template structure
3. Plan SSE/TL refactor (future)

### Revised Success Criteria

1. PM kernel file < 12,000 tokens (leaves 13k for templates + task requirements)
2. Each template file < 4,000 tokens
3. Integration test passes
4. All required markers present in kernel
5. CI gates pass

### Confidence Level

**Before LLM review:** Medium
**After incorporating feedback:** High

The LLM review validated the core approach and added important safeguards (profiles, validation, CI gates) that strengthen the implementation.

---

## References

- Current PM agent file: `agents/project_manager.md`
- Spec-Kit template pattern: `templates/pm_speckit.md`
- Token budget implementation: `research/automated-token-budget-implementation.md`
- Prompt builder: `.claude/skills/prompt-builder/scripts/prompt_builder.py`
- LLM review: `tmp/ultrathink-reviews/combined-review.md`
