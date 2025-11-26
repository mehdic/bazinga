# Orchestrator Refactoring: Final Consolidated Plan

**Date:** 2025-11-26
**Context:** Synthesized analysis from original plan + Gemini review + 3 Codex reviews
**Decision:** Modified 4-tier approach with cognitive load safeguards
**Status:** Proposed - awaiting approval

---

## Executive Summary

The original 5-tier plan targets correct problems (duplication, repeated patterns) but **over-estimates the LLM's ability to handle nested pointers**. All reviewers agree that aggressive abstraction trades robustness for brevity.

**Key insight from Gemini:** "LLMs don't execute loops, they simulate them. Every level of indirection increases hallucination risk."

**Revised approach:** Proceed with Tiers 1, 2, and 5, partially implement Tier 3, skip Tier 4.

---

## Reviewer Consensus Summary

| Tier | Original Risk | Gemini | Codex 1 | Codex 2 | Codex 3 | Consensus |
|------|---------------|--------|---------|---------|---------|-----------|
| 1 (Inline dedup) | LOW | **YES** | **YES** | **YES** | **YES** | **PROCEED** |
| 2 (Generic spawn) | MEDIUM | **YES** (with caveats) | **YES** (keep nuances) | **YES** (add deltas) | **YES** (add exceptions) | **PROCEED WITH MODIFICATIONS** |
| 3 (Phase 2B ref) | LOW | **SKIP** (parallel is complex) | LOW (add differences) | LOW (document deviations) | LOW (add delta list) | **PARTIAL - KEEP 2B-SPECIFIC** |
| 4 (Init compact) | MEDIUM | **SKIP** | MEDIUM (map branches) | MEDIUM (tag invariants) | MEDIUM (checklist) | **POSTPONE** |
| 5 (Logging ref) | LOW | **YES** | **YES** | **YES** | **YES** | **PROCEED** |

---

## Critical Risks Identified

### Risk 1: "Pointer Chasing" Cognitive Overload (Gemini)

**Problem:** If Tiers 1, 2, and 3 all use external references, the orchestrator must:
1. Read generic spawn pattern (Tier 2)
2. Resolve "Log" to logging_pattern.md (Tier 5)
3. Resolve "Parse" to response_parsing.md (Tier 1)
4. If in Phase 2B, resolve workflow to Phase 2A (Tier 3)

**Impact:** 4 levels of mental indirection degrades LLM performance. May cause "lazy" execution or hallucinated steps.

**Mitigation:**
- Keep critical micro-summaries inline
- Make routing table explicit (not generic)
- Keep Phase 2B unique logic explicit (not referenced)

### Risk 2: Agent-Specific Nuances Hidden (All Codex)

**Problem:** Generic patterns flatten agent-specific requirements:
- Developer needs skill config + tier selection (PM decides haiku vs sonnet)
- QA needs challenge progression levels
- Tech Lead enforces security/lint/coverage thresholds
- Investigator has hypothesis matrix + diagnostic loops

**Mitigation:** Keep "delta notes" under each agent spawn listing unique requirements.

### Risk 3: Parallel Mode Complexity (Gemini - Critical)

**Problem:** Phase 2B has fundamentally different requirements:
- **Batch processing** with 3-layer verification (LAYER 1, 2, 3)
- **Phase continuation check** (Step 2B.7a)
- **Pre-stop verification gate** (Step 2B.7b)
- **Multiple developers in ONE message** for true parallelism

These don't exist in Phase 2A. Saying "same as 2A" will cause the orchestrator to forget critical parallel-specific behaviors.

**Mitigation:** Only reference 2A for truly identical steps (individual QA/TL spawns). Keep all 2B-specific sections explicit.

### Risk 4: Template Access Reliability (Codex 2)

**Problem:** If orchestrator runtime cannot read external templates (sandbox restrictions, file fetch failure), removing inline quick references makes agent non-self-sufficient.

**Mitigation:** Keep mission-critical micro-summaries inline for parsing/logging/routing.

### Risk 5: Initialization Edge Cases (All)

**Problem:** Initialization encodes:
- Session resume logic
- Crash recovery
- Config gating
- DB warm-up ordering
- Feature flags

Compressing to decision tree may drop rare-but-critical branches.

**Mitigation:** POSTPONE Tier 4. Only compress if still over limit after other tiers.

---

## Revised Implementation Plan

### Tier 1: Inline Deduplication (PROCEED - LOW RISK)

**Original:** Remove all inline content that exists in templates
**Revised:** Remove most, but keep critical micro-summaries

**What to REMOVE:**
- Response parsing detailed examples (25 lines) → already in response_parsing.md
- Capsule format verbose examples (15 lines) → already in message_templates.md
- Logging step-by-step examples (30 lines) → already in logging_pattern.md
- PM output format inline (15 lines) → already in pm_output_format.md

**What to KEEP (micro-summaries):**
```markdown
**Quick Reference (see response_parsing.md for details):**
- Developer: Extract status (READY_FOR_QA/BLOCKED/PARTIAL), files, tests, coverage
- QA: Extract status (PASS/FAIL), test count, coverage %
- Tech Lead: Extract decision (APPROVED/CHANGES_REQUESTED), issues
- PM: Extract decision (BAZINGA/CONTINUE/INVESTIGATION_NEEDED)
```

**Tokens saved:** ~1,200 (conservative)
**Risk:** LOW

---

### Tier 2: Generic Agent Spawn Pattern (PROCEED WITH MODIFICATIONS - MEDIUM RISK)

**Original:** One generic pattern + minimal routing table
**Revised:** Generic pattern + explicit routing + mandatory delta notes

**Generic Pattern (NEW SECTION):**

```markdown
## Generic Agent Spawn Pattern

**For ANY agent spawn, follow this sequence:**

1. **Output capsule** - Use format from message_templates.md
2. **Build prompt** - Read `agents/{agent}.md` + apply prompt_building.md config
3. **Spawn** - `Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent], description="...", prompt=...)`
4. **Parse response** - Use response_parsing.md (extract status, files, tests, coverage as applicable)
5. **Log to DB** - See §Logging Reference below
6. **Route** - Per explicit routing table below

### Explicit Routing Table (Agent-Specific)

| Agent | Status | Next Action |
|-------|--------|-------------|
| **Developer** | READY_FOR_QA | Spawn QA Expert |
| **Developer** | READY_FOR_REVIEW | Spawn Tech Lead |
| **Developer** | BLOCKED | Spawn Investigator |
| **Developer** | PARTIAL/INCOMPLETE | Respawn Developer with continuation |
| **Developer** | ESCALATE_SENIOR | Spawn Senior Software Engineer |
| **QA Expert** | PASS | Spawn Tech Lead |
| **QA Expert** | FAIL | Respawn Developer with QA feedback |
| **QA Expert** | ESCALATE_SENIOR | Spawn Senior Software Engineer |
| **Tech Lead** | APPROVED | Check pending groups → Spawn PM |
| **Tech Lead** | CHANGES_REQUESTED | Respawn Developer/QA with feedback |
| **Tech Lead** | SPAWN_INVESTIGATOR | Spawn Investigator |
| **PM** | BAZINGA | → Completion Protocol |
| **PM** | CONTINUE | Spawn Developer(s) per PM instructions |
| **PM** | INVESTIGATION_NEEDED | Spawn Investigator |
| **PM** | NEEDS_CLARIFICATION | Surface to user, await response |

### Agent-Specific Delta Notes (MANDATORY)

**Developer:**
- Check PM's Initial Tier decision (Developer vs Senior Software Engineer)
- Model: MODEL_CONFIG["developer"] (haiku) or MODEL_CONFIG["senior_software_engineer"] (sonnet)
- Include: Group ID, branch name, skills config, testing config
- Track revision count for escalation (≥1 revision → escalate to SSE)

**QA Expert:**
- Include developer's files changed and test additions
- Apply 5-level challenge progression per challenge_levels.json
- Model: MODEL_CONFIG["qa_expert"] (sonnet)

**Tech Lead:**
- Include implementation summary + QA results
- Enforce security scan, lint check, coverage thresholds
- Model: MODEL_CONFIG["tech_lead"] (opus)
- Can spawn Investigator for complex issues

**PM:**
- Include complete session context + all group statuses
- Model: MODEL_CONFIG["project_manager"] (opus)
- Only PM can send BAZINGA

**Investigator:**
- Include problem description, evidence, hypothesis matrix
- Model: MODEL_CONFIG["investigator"] (opus)
- Max 5 iterations per investigation loop
```

**What each spawn section becomes:**

```markdown
### Step 2A.1: Spawn Developer
Follow §Generic Agent Spawn Pattern.
- Agent: Developer (or SSE per PM's Initial Tier decision)
- Group: main
- Mode: Simple
- Context: PM's task assignment + user requirements

**Specific requirements:** See Developer delta notes above.
```

**Tokens saved:** ~4,500 (less aggressive than original ~5,500)
**Risk:** MEDIUM (mitigated by explicit routing + delta notes)

---

### Tier 3: Phase 2B Partial Deduplication (PARTIAL - MEDIUM RISK)

**Original:** Reference "same as 2A" for entire Phase 2B
**Revised:** Reference 2A for identical steps, KEEP explicit instructions for 2B-unique logic

**What to REFERENCE (truly identical):**

```markdown
### Steps 2B.3-2B.6: Route Each Group Through Workflow
Each group follows the same workflow as Phase 2A Steps 2A.3-2A.7:
- 2B.3: Route developer response (same routing logic as 2A.3)
- 2B.4: Spawn QA Expert (same as 2A.4, use group-specific context)
- 2B.5: Route QA response (same as 2A.5)
- 2B.6: Spawn Tech Lead (same as 2A.6, use group-specific context)

**Group-specific adaptations:**
- Replace "main" with group ID (A, B, C, D)
- Use group-specific branch name
- Use group-specific files list
- Track group status independently in database
- Log with agent_id: `{role}_group_{X}`
```

**What to KEEP EXPLICIT (2B-unique, ~250 lines):**

1. **Step 2B.0: Context Optimization Checkpoint** (unique - memory management)
2. **Step 2B.1: Spawn Multiple Developers in Parallel** (unique - true parallelism)
   - Build ALL prompts BEFORE spawning
   - Spawn ALL developers in ONE message block
   - PM's tier decision PER GROUP (some haiku, some sonnet)
3. **Step 2B.2a: Mandatory Batch Processing (LAYER 1)** (unique - root cause fix)
   - Parse ALL responses first
   - Build spawn queue for ALL groups
   - Spawn ALL tasks in ONE message
   - FORBIDDEN patterns (serialization, partial spawning)
4. **Step 2B.7a: Phase Continuation Check** (unique - multi-phase coordination)
   - Check pending groups before spawning PM
   - Handle execution_phases for multi-phase plans
5. **Step 2B.7b: Pre-Stop Verification Gate (LAYER 3)** (unique - safety net)
   - Three-question checklist
   - Auto-fix enforcement
   - PASS criteria before ending message

**Tokens saved:** ~1,500 (conservative - keeping 2B-unique sections)
**Risk:** MEDIUM (mitigated by explicit 2B-specific sections)

**Gemini's concern addressed:** Parallel-specific logic (batch processing, phase continuation, verification gates) remains explicit and is NOT referenced to sequential 2A logic.

---

### Tier 4: Compact Initialization (POSTPONE - MEDIUM RISK)

**Decision:** SKIP for now

**Rationale (from all reviewers):**
- Initialization encodes edge cases (resume, recovery, migration)
- Compressing to decision tree may drop critical branches
- Safety is worth the token cost
- Other tiers provide sufficient savings

**When to revisit:** Only if still over limit after implementing Tiers 1, 2, 3, 5.

**If needed later:**
- Map ALL initialization branches first
- Tag each with triggering condition
- Keep invariant checklist (required configs, DB connectivity, resume-token handling)
- Keep "safe path" for unexpected states

---

### Tier 5: Compact Logging Reference (PROCEED - LOW RISK)

**Implementation:**

```markdown
## Logging Reference

**Standard pattern for ALL agent interactions:**
```
bazinga-db, log {agent_type} interaction:
Session ID: {session_id}
Agent Type: {agent_type}
Content: {response}
Iteration: {N}
Agent ID: {id}
```
Then invoke: `Skill(command: "bazinga-db")`

**Agent ID formats:**
- PM: pm_main, pm_final, pm_parallel_final
- Developer: developer_main, developer_group_{X}
- QA: qa_main, qa_group_{X}
- Tech Lead: techlead_main, techlead_group_{X}
- Investigator: investigator_{group}_{N}

**Error handling:**
- Initialization fails → STOP workflow
- Workflow logging fails → WARN and continue (degraded mode)

**Per-phase required fields:**
| Phase | Additional Fields |
|-------|-------------------|
| Parallel mode | group_id, parallel_count |
| Investigation | hypothesis_id, iteration |
| Completion | final_status, criteria_met |
```

**Replace throughout:** 14-line logging blocks → "Log to DB (see §Logging Reference)"

**Tokens saved:** ~1,000
**Risk:** LOW

---

## Consolidated Savings

| Tier | Strategy | Original Est. | Revised Est. | Risk |
|------|----------|---------------|--------------|------|
| 1 | Inline dedup + micro-summaries | 1,350 | **1,200** | LOW |
| 2 | Generic spawn + explicit routing + deltas | 5,500 | **4,500** | MEDIUM |
| 3 | Partial 2B dedup (keep unique sections) | 2,500 | **1,500** | MEDIUM |
| 4 | Compact initialization | 2,000 | **0** (postponed) | N/A |
| 5 | Compact logging reference | 1,000 | **1,000** | LOW |
| **Total** | | **12,350** | **8,200** | |

**Result:**
- Current: 26,666 tokens
- After refactoring: **18,466 tokens**
- Buffer: 6,534 tokens (26.1% under limit)
- Room for future growth: ~6,500 tokens

---

## Implementation Order

**Recommended sequence (safest):**

### Phase 1: Tier 1 + Tier 5 (Immediate - Low Risk)
1. Remove inline duplication, keep micro-summaries
2. Create §Logging Reference section
3. Replace logging blocks with references
4. **Test:** Verify orchestrator loads and parses correctly
5. **Checkpoint:** Measure token count

**Expected after Phase 1:** ~24,466 tokens (2.1% under limit)

### Phase 2: Tier 2 (Carefully - Medium Risk)
1. Create §Generic Agent Spawn Pattern section
2. Create §Explicit Routing Table
3. Create §Agent-Specific Delta Notes
4. Replace each spawn section with 5-line reference + deltas
5. **Test:** Run orchestration through ALL agent types
6. **Test:** Verify routing handles all status codes
7. **Checkpoint:** Measure token count

**Expected after Phase 2:** ~19,966 tokens (20.1% under limit)

### Phase 3: Tier 3 (Carefully - Medium Risk)
1. Keep 2B-unique sections explicit (2B.0, 2B.1, 2B.2a, 2B.7a, 2B.7b)
2. Reference 2A for identical group-level workflows (2B.3-2B.6)
3. Add "Group-specific adaptations" section
4. **Test:** Run parallel mode orchestration
5. **Test:** Verify batch processing and verification gates work
6. **Checkpoint:** Measure token count

**Expected after Phase 3:** ~18,466 tokens (26.1% under limit)

---

## Validation Checklist

After EACH phase, verify:

### Functional Tests
- [ ] Simple mode: Developer → QA → Tech Lead → PM → BAZINGA
- [ ] Parallel mode: Multiple developers → batch processing → phase continuation
- [ ] Blocked path: Developer BLOCKED → Investigator → resolution
- [ ] Escalation path: Developer fail → SSE → Tech Lead guidance
- [ ] Resume: Session resume loads correct state
- [ ] Investigation: Tech Lead spawns Investigator, validation loop works

### Cognitive Load Tests (Gemini's concern)
- [ ] Pick a random status (e.g., QA FAIL) and trace the path without ambiguity
- [ ] Verify routing table has NO generic "PASS" entries (all agent-specific)
- [ ] Confirm 2B-specific logic is NOT referenced to 2A

### Safety Tests
- [ ] All templates referenced are loadable
- [ ] Micro-summaries cover mission-critical rules
- [ ] Logging captures required fields per phase
- [ ] Error handling preserved (init fails → stop, logging fails → warn)

---

## Comparison to Original Plan

| Aspect | Original Plan | Revised Plan |
|--------|---------------|--------------|
| Tokens saved | 9,350 | 8,200 |
| Final size | 17,316 | 18,466 |
| Buffer | 30.7% | 26.1% |
| Tier 3 approach | Full reference to 2A | Keep 2B-unique explicit |
| Tier 4 | Optional | Postponed |
| Routing table | Generic | Agent-specific explicit |
| Agent nuances | Implicit | Explicit delta notes |
| Micro-summaries | None | Kept for critical rules |

**Trade-off:** Slightly less aggressive savings in exchange for significantly reduced cognitive load risk and better robustness.

---

## Risk Mitigation Summary

| Risk | Mitigation |
|------|------------|
| Pointer chasing | Keep micro-summaries inline; max 2 levels of indirection |
| Agent nuances hidden | Mandatory delta notes per agent |
| Parallel mode confusion | Keep 2B-specific sections explicit |
| Template access failure | Micro-summaries for mission-critical rules |
| Initialization fragility | Postpone Tier 4; preserve edge case handling |
| Routing ambiguity | Agent-specific status codes (not generic PASS) |

---

## Final Recommendation

**Implement Tiers 1, 2, 3 (partial), and 5 in sequence.**

**Expected outcome:**
- Final size: ~18,466 tokens (26.1% under limit)
- Buffer: ~6,500 tokens for future growth
- Risk level: LOW-MEDIUM (significantly reduced from original)
- Functionality: 100% preserved
- Cognitive load: Manageable (max 2 levels of indirection)

**Key differences from original:**
1. **Explicit routing table** - Not generic, agent-specific status codes
2. **Delta notes mandatory** - Agent-specific requirements preserved
3. **2B-specific logic explicit** - Parallel mode complexity not hidden
4. **Micro-summaries kept** - Mission-critical rules accessible inline
5. **Tier 4 postponed** - Safety over brevity for initialization

---

## Appendix: Reviewer Insights Worth Preserving

### Gemini's Key Insight
> "The more you force [an LLM] to 'unzip' compressed instructions (look up a reference -> fill a template -> execute), the higher the chance of instruction drift or hallucination."

### Codex 1's Key Insight
> "If the model misinterprets a branch in the compact tree, it might wipe context or fail to load previous state."

### Codex 2's Key Insight
> "Keep a short 'micro-summary' inline for mission-critical rules so outages in template access don't stall execution."

### Codex 3's Key Insight
> "Add explicit anchor links (e.g., 'see response_parsing.md, section X') to avoid ambiguity."

---

**Document Status:** Final Consolidated Plan
**Next Step:** User approval, then implement Phase 1 (Tiers 1 + 5)
