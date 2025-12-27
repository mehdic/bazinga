# PM Agent V2: Critical Analysis

**Date:** 2025-12-27
**Context:** User proposed a new version of the PM agent file with significant additions
**Decision:** Pending user approval
**Status:** Proposed
**Reviewed by:** Pending external LLM reviews

---

## Executive Summary

The proposed PM agent V2 adds three major new sections (~120 additional lines) focused on:
1. Decision-Making Playbook (structured decision framework)
2. Engineering Issue Triage & Unblocking (evidence bundles, MRE requirements)
3. Task Decomposition for Independent Execution (vertical slices, patterns)

This analysis evaluates whether these additions are net positive, identify risks, and recommend a path forward.

---

## Detailed Change Analysis

### Section-by-Section Comparison

| Section | Current V1 | Proposed V2 | Change Type |
|---------|-----------|-------------|-------------|
| Frontmatter | ✓ Same | ✓ Same | No change |
| Your Role | ✓ Same | ✓ Same | No change |
| Golden Rules | ✓ Same | ✓ Same | No change |
| Critical Behaviors | ✓ Same | ✓ Same | No change |
| **Decision-Making Playbook** | ❌ None | ✓ NEW (~50 lines) | **Addition** |
| **Engineering Issue Triage** | ❌ None | ✓ NEW (~40 lines) | **Addition** |
| **Task Decomposition** | ❌ None | ✓ NEW (~35 lines) | **Addition** |
| SCOPE IS IMMUTABLE | Lines 42-49 | **Moved** inside new sections | **Relocation** |
| Workflow Overview | ✓ Same | ✓ Same | No change |
| Mandatory Output Format | ✓ Same | ✓ Same | No change |
| Tool Restrictions | ✓ Same | ✓ Same | No change |
| Database Operations | ✓ Same | ✓ Same | No change |
| SPEC-KIT Integration | ✓ Same | ✓ Same | No change |
| Reference Files | ✓ Same | ✓ Same | No change |
| Quick Reference Table | ✓ Same | ✓ Same | No change |
| Phase 2 Progress | ✓ Same | ✓ Same | No change |
| Handling Failures | ✓ Same | ✓ Same | No change |
| Context Management | ✓ Same | ✓ Same | No change |
| Reasoning Documentation | ✓ Same | ✓ Same | No change |
| Handoff File | ✓ Same | ✓ Same | No change |
| Final Response | ✓ Same | ✓ Same | No change |
| Final Checklist | ✓ Same | ✓ Same | No change |
| Critical Constraints | ✓ Same | ✓ Same | No change |

### Line Count Impact

| Version | Approximate Lines | Token Estimate |
|---------|-------------------|----------------|
| Current V1 | ~440 | ~3,500 |
| Proposed V2 | ~560 | ~4,500 |
| **Delta** | **+120 lines** | **+1,000 tokens** |

---

## New Section Analysis

### 1. Decision-Making Playbook (MANDATORY)

**Content:**
- 5-step decision framework: classify → evidence → method → commit → record
- MCDA (Multi-Criteria Decision Analysis) for tradeoff-heavy choices
- Decision tree thinking for uncertainty/risk choices
- Timebox and commit for reversible choices

**Pros ✅:**
- Provides structured framework preventing ad-hoc decisions
- Forces evidence before decisions (prevents guesswork)
- Introduces decision logging requirement (traceability)
- Covers decision methods PM might not naturally use

**Cons ⚠️:**
- May duplicate pm_routing.md guidance on decisiveness
- MCDA might be overkill for simple mode single-task orchestrations
- "Decision record (REQUIRED)" adds database overhead
- New terminology PM must internalize

**Verdict:** Valuable for complex parallel-mode orchestrations, but may add cognitive load for simple tasks.

### 2. Engineering Issue Triage & Unblocking (MANDATORY)

**Content:**
- Evidence bundle requirements (error, reproduction, expected vs actual)
- Minimal Reproducible Example (MRE) emphasis
- Triage classification taxonomy (7 categories)
- "Where to look first" priority ordering
- Action routing rules

**Pros ✅:**
- Standardizes how blockers are reported (prevents vague "it's broken")
- MRE focus reduces investigation time
- Clear routing rules (known fix → Dev, unknown cause → Investigator)
- Postmortem requirement for recurring issues

**Cons ⚠️:**
- Duplicates some Investigator agent responsibilities
- Classification taxonomy (7 categories) may be overly detailed
- "Where to look first" is guidance for agents, not PM (PM shouldn't be debugging)
- May conflict with PM's tool restrictions (PM shouldn't analyze stack traces)

**Verdict:** Partially valuable. The evidence bundle and routing rules are good. The "where to look first" section feels misplaced (should be in Investigator/Developer prompts).

### 3. Task Decomposition for Independent Execution (MANDATORY)

**Content:**
- Independence rules (independent, testable, mergeable, integratable)
- Default strategy: thin vertical slices
- Slicing patterns (core→enhance, workflow steps, business rules, personas, data scale)
- Dependency-killers (contract-first, stubs/mocks, file ownership)
- Task group definition minimum fields

**Pros ✅:**
- Directly addresses parallel mode challenges
- "Thin vertical slices" is correct architecture guidance
- Dependency-killer techniques are practical
- Enforces contract-first interfaces (prevents blocking)

**Cons ⚠️:**
- Partially duplicates pm_planning_steps.md Step 3.5 (task group creation)
- Partially duplicates pm_task_classification.md (task group format)
- Some guidance is for developers (file ownership), not PM
- May encourage over-engineering of simple tasks

**Verdict:** Good content, but creates duplication with existing template files.

---

## Critical Issues

### Issue 1: Template Duplication Risk

**Problem:** V2 inlines guidance that should live in reference templates.

| V2 Inline Section | Existing Template | Overlap |
|-------------------|-------------------|---------|
| Task Decomposition | pm_planning_steps.md Step 3.5 | 60% |
| Triage Classification | pm_routing.md (routing patterns) | 40% |
| Decision Logging | pm_bazinga_validation.md | 30% |

**Risk:** When templates are updated, the inline V2 content becomes stale. This violates the "single source of truth" principle.

**Recommendation:** If these sections are adopted, they should either:
1. Replace the corresponding template sections (and template files reference the agent file), OR
2. Be moved INTO the template files (keeping agent file as router)

### Issue 2: SCOPE IS IMMUTABLE Buried

**Problem:** In V1, "SCOPE IS IMMUTABLE" is at line 42-49 (highly visible near Golden Rules). In V2, it's buried inside the Decision-Making section (~line 95).

**Risk:** Critical constraint becomes less prominent, increasing chance of scope reduction violations.

**Recommendation:** Keep SCOPE IS IMMUTABLE near top (after Critical Behaviors) OR duplicate it in both places.

### Issue 3: Token Budget Impact

**Problem:** +1,000 tokens in agent file reduces available context for:
- Orchestrator's task prompt
- Specialization blocks
- Codebase context

**Risk:** Longer orchestrations may hit context limits sooner, requiring more context compaction.

**Mitigation:** If sections are valuable, convert verbose paragraphs to bullet points.

### Issue 4: "Where to Look First" Violates Tool Restrictions

**Problem:** The Engineering Issue Triage section includes:
> "Where to look first (order matters):
> 1. Failing test output + most local stack trace
> 2. CI/build logs around the first failure..."

But PM's Tool Restrictions explicitly state:
> "❌ NEVER read code files for implementation"

**Risk:** PM may attempt to analyze logs/stack traces itself, violating role boundaries.

**Recommendation:** Remove "Where to look first" from PM agent (move to Investigator agent instead).

---

## Arguments FOR Adoption

1. **Structured Decision-Making:** PM currently has no explicit decision framework. The playbook provides guardrails preventing analysis paralysis or hasty decisions.

2. **Evidence Bundle Standard:** Forces reporting agents (Dev/QA/TL) to provide actionable info. Reduces back-and-forth "what failed?" cycles.

3. **Vertical Slice Emphasis:** Correct architectural guidance for task decomposition. Current system has seen issues with overlapping task groups.

4. **Autonomous Unblocking:** Triage classification helps PM route blockers without escalating to user. Supports the "fully autonomous" principle.

5. **Decision Audit Trail:** Logging decisions enables post-session analysis of PM behavior for system improvement.

---

## Arguments AGAINST Adoption

1. **Duplication Creates Drift:** Inline content will diverge from template files over time. Single source of truth is better than synchronized duplicates.

2. **Token Overhead:** +1,000 tokens per PM spawn. Over a 10-iteration orchestration = +10,000 tokens of redundant instructions.

3. **Scope Visibility Reduced:** SCOPE IS IMMUTABLE is less prominent. This is the most violated constraint in practice.

4. **Role Boundary Blur:** "Where to look first" implies PM should analyze errors. This contradicts tool restrictions and Investigator responsibilities.

5. **Cognitive Load:** PM must now internalize 3 new mandatory sections. May slow down response time without proportional quality gain.

6. **Untested Content:** These sections haven't been validated in production orchestrations. Could introduce unexpected behaviors.

---

## Comparison Matrix

| Criterion | Weight | V1 (Current) | V2 (Proposed) | Notes |
|-----------|--------|--------------|---------------|-------|
| Single Source of Truth | 25% | 9 | 6 | V2 duplicates template content |
| Token Efficiency | 20% | 9 | 7 | V2 +1,000 tokens |
| Decision Quality | 20% | 6 | 8 | V2 has structured framework |
| Scope Visibility | 15% | 9 | 6 | V2 buries SCOPE IS IMMUTABLE |
| Unblocking Speed | 10% | 6 | 8 | V2 has triage framework |
| Role Clarity | 10% | 8 | 6 | V2 has role boundary issues |
| **Weighted Score** | 100% | **7.9** | **6.8** | V1 wins marginally |

---

## Recommendation

### Option A: Selective Adoption (RECOMMENDED)

**Adopt the following from V2:**
1. Decision-Making Playbook (condensed to ~25 lines, bullet-point format)
2. Evidence Bundle requirement from Triage section (5 lines)
3. Task group independence rules from Decomposition section (10 lines)

**Reject the following:**
1. "Where to look first" (move to Investigator agent)
2. Full triage classification taxonomy (overkill)
3. Detailed slicing patterns (move to pm_planning_steps.md)

**Additionally:**
- Keep SCOPE IS IMMUTABLE at line 42 (don't relocate)
- Add pointers to templates for detailed procedures

**Net effect:** +40 lines instead of +120 lines. Captures core value without duplication.

### Option B: Full Adoption with Refactor

**Adopt all V2 sections BUT:**
1. Move detailed content to template files
2. Agent file contains only "must read X for Y" pointers
3. Remove "Where to look first" section entirely
4. Keep SCOPE IS IMMUTABLE near top

**Risk:** Requires updating 3 template files + agent file. Larger change scope.

### Option C: Reject V2

**Keep current V1 as-is.**

**Rationale:** Current system is working. V2 additions are incremental improvements with non-trivial risks. Wait for specific failures that would be addressed by V2 content.

---

## Implementation Checklist (if adopting)

- [ ] Condense Decision-Making Playbook to bullet points
- [ ] Move "Where to look first" to Investigator agent
- [ ] Keep SCOPE IS IMMUTABLE at prominent position (after Critical Behaviors)
- [ ] Update pm_planning_steps.md with Task Decomposition patterns (if not duplicating)
- [ ] Run integration test to validate no regressions
- [ ] Measure token usage before/after

---

## References

- Current PM agent: `agents/project_manager.md`
- PM planning steps: `templates/pm_planning_steps.md`
- PM routing: `templates/pm_routing.md`
- PM task classification: `templates/pm_task_classification.md`

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (Gemini skipped - disabled)

### Consensus Points (OpenAI + Claude Analysis Aligned)

1. **Single Source of Truth Violation is Critical** - Both analyses identify template duplication as the primary risk. OpenAI explicitly calls this "knowingly duplicates guidance...will drift and become inconsistent."

2. **SCOPE IS IMMUTABLE Must Stay Prominent** - OpenAI: "top-3 cause of PM failures; burying it increases risk of scope narrowing." Matches Claude analysis.

3. **Role Boundary Bleed ("Where to look first")** - OpenAI: "encourages PM to perform analysis outside allowed tools." Matches Claude analysis on Tool Restrictions conflict.

4. **Token Budget Impact Needs Mitigation** - OpenAI adds: "prompt-builder enforces marker/tokens budgets; longer PM prompts reduce room for specializations."

5. **Selective Adoption is Correct Direction** - OpenAI: "The current 'Selective Adoption' recommendation is directionally right."

### Key New Insights from OpenAI Review

**Missing Considerations Identified:**
| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Prompt-builder marker validation | Longer file may break parsing | Add CI prompt-lint check |
| Conditional prompt construction | Overhead for simple mode | Inject V2 blocks only for parallel/high-complexity |
| Decision logging schema | Ad-hoc logs can't be consumed | Use existing `save-reasoning phase="decisions"` |
| Workflow-router implications | Evidence bundles not enforced | Router should validate, not just PM |
| SPECKIT alignment | Potential conflicts | Verify pm_speckit.md compatibility |
| Rollout strategy | No rollback path | Feature-flag V2, A/B test, canary week |

**Critical Implementation Risks Added:**
1. **Routing regressions** - Denser PM output may bury `## PM Status: [CODE]` header
2. **Token overflows** - Prompt-builder may truncate specializations silently
3. **DB schema mismatch** - Decision logs unusable by dashboard without schema alignment
4. **Performance degradation** - Increased cost/latency without conditional gates

### Incorporated Feedback

1. **Keep SCOPE IS IMMUTABLE Near Top AND Add Reminder in Decision Section** (OpenAI suggestion) - Don't relocate exclusively; duplicate as reminder.

2. **Conditional Prompt Injection** (OpenAI: "inject decision bullets only for parallel mode or complexity ≥ 4") - This is a better approach than static inclusion.

3. **Use Existing Logging Primitives** (OpenAI: "save-reasoning phase 'decisions'") - Don't invent new ad-hoc logging; use bazinga-db properly.

4. **Move Heavy Content to Templates** (OpenAI: "Keep PM agent as concise router with pointers") - Aligns with Claude analysis.

5. **Workflow-Router Enhancement** (OpenAI: "require evidence_bundle object when PM sets INVESTIGATION_NEEDED") - Enforcement at router level reduces PM cognitive load.

6. **Add Verification Gates** (OpenAI recommendation):
   - CI prompt-lint for status header presence
   - Prompt-builder budget check
   - Build fails if over budget

### Rejected Suggestions (With Reasoning)

None. All OpenAI suggestions are valid and complementary to the analysis.

---

## Updated Recommendation

Based on integrated feedback, the recommendation is refined:

### Path Forward: Selective Adoption + Operational Hardening

**Step 1: Minimal Agent File Changes (~40 lines)**
```markdown
## Decision-Making Discipline (COMPACT)
- Classify: reversible vs hard-to-reverse, local vs cross-cutting
- Evidence: Demand clear problem + 2-4 options + risks before deciding
- Method: Tradeoffs → weight criteria; Uncertainty → decision tree; Low-risk → timebox
- Commit: Decision + rationale + rollback plan
- Log: via bazinga-db save-reasoning phase="decisions"

📚 Full playbook: `bazinga/templates/pm_planning_steps.md` (Step 0-6)

## Task Group Independence (COMPACT)
- Independent: minimal shared files with other groups
- Testable: clear acceptance criteria
- Mergeable: incremental deliverables (no big bang)
- Contract-first: define API/schema early to unblock parallel work

📚 Decomposition patterns: `bazinga/templates/pm_planning_steps.md` (Step 3.5)

## Evidence Bundle (When Routing to Investigator)
Reporting agent MUST provide: exact error, repro steps, expected vs actual, what was tried.

📚 Full triage: `bazinga/templates/pm_routing.md` (Investigation section)
```

**Step 2: Move Heavy Content to Templates**
- Add detailed "Decision-Making Playbook" to `pm_planning_steps.md`
- Add detailed "Task Slicing Patterns" to `pm_planning_steps.md`
- Add "Evidence Bundle Standard" to `pm_routing.md` under Investigation section

**Step 3: Do NOT Include in PM Agent**
- "Where to look first" - Move to Investigator agent (`agents/investigator.md`)
- Full triage classification taxonomy - Move to template
- Detailed slicing patterns - Move to template

**Step 4: Keep SCOPE IS IMMUTABLE at Line 42** (after Critical Behaviors)

**Step 5: Operational Hardening (NEW from OpenAI)**
- [ ] Add prompt-lint CI check for `## PM Status: [CODE]` presence
- [ ] Prompt-builder token budget validation (fail if over)
- [ ] Feature-flag for V2 blocks in prompt-builder
- [ ] Track metrics: token usage, iteration count, failure rates
- [ ] One-week canary before full rollout

---

## Final Verdict

| Aspect | Decision |
|--------|----------|
| **Can we replace as-is?** | **NO** - Risks outweigh benefits |
| **Should we adopt elements?** | **YES** - Selective adoption is valuable |
| **What to adopt?** | Compact decision discipline, independence rules, evidence bundle |
| **What to reject?** | "Where to look first", full taxonomies, detailed patterns inline |
| **Required hardening?** | Prompt-lint, token budgets, feature flags, canary rollout |

---

## Cleanup

```bash
rm -rf tmp/ultrathink-reviews/
```
