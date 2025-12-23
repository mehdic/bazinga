# Orchestrator Context Accumulation Fix: Feasibility and Implementation Analysis

**Date:** 2025-12-23
**Context:** After CRP implementation, BAZINGA parallel mode still exhausts context after ~4 rounds
**Decision:** Pending - analyzing feasibility of proposed fixes
**Status:** Proposed
**Reviewed by:** OpenAI GPT-5, Google Gemini 3 Pro Preview (pending)

---

## Problem Statement

The Compact Return Protocol (CRP) successfully reduced agent response tokens by 95% (25k → 150-500 tokens per agent). However, orchestration sessions still exhaust context after approximately 4 rounds of parallel execution.

**Evidence from CDC session transcript:**
- Session ran 4 rounds of parallel developers successfully
- Context hit 95% → 0% during Round 4
- All 4 developers completed but orchestrator couldn't process their outputs
- No QA routing occurred for completed work

**Root cause identified:** The orchestrator's own routing logic accumulates context across rounds without cleanup.

---

## Current Architecture Analysis

### What CRP Fixed (Working)

| Component | Before CRP | After CRP | Reduction |
|-----------|------------|-----------|-----------|
| Developer return | ~25,000 tokens | ~150 tokens | 99.4% |
| QA return | ~15,000 tokens | ~150 tokens | 99% |
| Tech Lead return | ~10,000 tokens | ~150 tokens | 98.5% |
| PM return | ~8,000 tokens | ~200 tokens | 97.5% |

**Total per-round agent returns:** ~58k → ~650 tokens (98.9% reduction)

### What CRP Didn't Fix (Problem Areas)

| Component | Tokens/Event | Events/Round | Tokens/Round |
|-----------|--------------|--------------|--------------|
| Task tool metadata per spawn | ~500 | 8 (4 dev + 4 QA/TL) | ~4,000 |
| Orchestrator routing messages | ~300 | 8 | ~2,400 |
| Phase continuation checks (per-group) | ~800 | 4 | ~3,200 |
| DB query/response logging | ~200 | 12 | ~2,400 |
| **Round overhead total** | | | **~12,000** |

**After 4 rounds:** ~48,000 tokens of orchestrator overhead accumulates
**Plus base orchestrator prompt:** ~25,000 tokens
**Plus PM planning context:** ~15,000 tokens
**Total:** ~88,000+ tokens before any context for work remains

---

## Proposed Fixes Analysis

### Fix 1: Phase-Boundary Compaction

**Concept:** After each phase completes (all groups merged), emit a single summary and conceptually "reset" accumulated state.

**Implementation approaches:**

#### Option 1A: Explicit Context Summary Block
```markdown
After all groups in Phase N complete:
1. Generate phase summary: "Phase N: 4 groups completed, all tests passing"
2. Write detailed state to file: bazinga/artifacts/{session}/phase_N_summary.json
3. Clear in-context tracking (orchestrator stops referencing prior routing decisions)
4. Continue with file-reference only: "Phase N complete. See phase_N_summary.json for details."
```

**Feasibility:** HIGH
- No code changes to Claude Code/Task tool required
- Pure prompt engineering in orchestrator.md
- Risk: LLM may not "forget" prior context (it's still in window)

#### Option 1B: Trigger Auto-Compact at Phase Boundary
```markdown
After Phase N complete:
1. Output: "Phase N complete. Running /compact before Phase N+1..."
2. Invoke compact (if possible via tool)
3. Resume with minimal state from database
```

**Feasibility:** LOW
- `/compact` is a user command, not programmatically invokable
- Would require user intervention at each phase boundary
- Defeats autonomous orchestration goal

#### Option 1C: Chunked Session Architecture
```markdown
Each phase runs as a separate orchestration "sub-session":
1. Phase 1 → runs to completion → writes state to DB → exits
2. User runs `/bazinga.orchestrate` again → detects Phase 2 needed → continues
```

**Feasibility:** MEDIUM
- Already partially implemented (session resume logic exists)
- Would require user intervention between phases
- Could be automated with hooks or background process

**Recommendation:** Option 1A with aggressive file-offloading

---

### Fix 2: Batch Phase Checks (Per-Phase, Not Per-Group)

**Current behavior (phase_parallel.md:497-504):**
```
After EACH group's MERGE_SUCCESS:
1. Update group status=completed (DB call)
2. Query ALL groups (DB call)
3. Load PM state for execution_phases (DB call)
4. Count: completed/in_progress/pending
5. Decision logic
```

**Problem:** 4 groups × 3 DB queries × ~300 tokens/query = 3,600 tokens per phase just for phase checking

**Proposed change:**
```
After EACH group's MERGE_SUCCESS:
1. Update group status=completed (DB call) - ~100 tokens
2. Increment local counter (no DB call)
3. IF local_counter == expected_phase_groups THEN run full phase check
   ELSE output "Group X merged (Y/Z in phase)" - minimal capsule
```

**Implementation:**

```markdown
### Step 2B.7b: Phase Continuation Check (OPTIMIZED)

**Track locally:** Maintain `phase_completion_tracker = {phase_id: {completed: N, total: M}}`

**On MERGE_SUCCESS:**
1. Update DB: `update-task-group {group} status=completed` (1 call)
2. Increment local: `phase_completion_tracker[current_phase].completed += 1`
3. Output capsule: `✅ {group} merged | Phase {N}: {completed}/{total}`

**IF completed == total for current phase:**
4. THEN run full phase transition check (query DB for next phase)
5. ELSE skip DB queries, continue waiting for other groups
```

**Feasibility:** HIGH
- Pure prompt engineering change
- Reduces DB calls from 3N to N+1 per phase (where N = groups in phase)
- ~67% reduction in phase-checking tokens

**Risk:** Orchestrator state may drift if interrupted mid-phase. Mitigation: Full DB reconciliation on resume.

---

### Fix 3: Aggregate Routing Messages

**Current behavior:**
```
Received Developer A response: READY_FOR_QA
→ Routing Developer A to QA Expert...

Received Developer B response: READY_FOR_QA
→ Routing Developer B to QA Expert...

Received Developer C response: PARTIAL
→ Developer C needs continuation...

Received Developer D response: READY_FOR_QA
→ Routing Developer D to QA Expert...
```

**Each routing message:** ~300 tokens × 4 = 1,200 tokens

**Proposed change:**
```
Received 4 developer responses:
| Group | Status | Next |
|-------|--------|------|
| A | READY_FOR_QA | → QA |
| B | READY_FOR_QA | → QA |
| C | PARTIAL | → Dev retry |
| D | READY_FOR_QA | → QA |

Spawning 3 QA + 1 Dev continuation in parallel.
```

**Single aggregated message:** ~400 tokens (67% reduction)

**Implementation in phase_parallel.md:**

```markdown
### Step 2B.2: Receive All Developer Responses (BATCH FORMAT)

**MANDATORY: Aggregate all responses before ANY routing:**

1. Collect all responses into table format:
   ```
   | Group | Status | Files | Tests | Summary |
   |-------|--------|-------|-------|---------|
   | {id} | {status} | {count} | {pass}/{total} | {summary[0]} |
   ```

2. Output SINGLE aggregated capsule:
   ```
   🔨 **{N} Developers Complete**
   {table}

   **Routing:** {X} → QA, {Y} → Dev retry, {Z} → TL
   ```

3. Spawn ALL next agents in ONE Task block
```

**Feasibility:** HIGH
- Prompt engineering only
- Already partially implemented in batch_processing.md template
- Need to enforce tabular output format

---

### Fix 4: Orchestrator CRP (Meta-Level File Offloading)

**Concept:** Apply the same CRP pattern to orchestrator's own state. Instead of keeping routing decisions in context, write them to files.

**Current orchestrator context accumulates:**
- All capsule outputs (displayed to user but also in context)
- All routing decisions and reasoning
- All DB query results
- All phase transition logic

**Proposed structure:**
```
bazinga/artifacts/{session_id}/orchestrator/
├── round_1_routing.json    # All routing decisions for round 1
├── round_2_routing.json    # All routing decisions for round 2
├── phase_transitions.json  # Phase boundary decisions
└── current_state.json      # Minimal current state for decision-making
```

**Orchestrator prompt modification:**
```markdown
## Context Management (MANDATORY)

After processing each round of agent responses:
1. Write routing decisions to: bazinga/artifacts/{session_id}/orchestrator/round_{N}_routing.json
2. Keep in context ONLY:
   - Current phase number
   - Groups currently in_progress (IDs only)
   - Next action to take
3. Reference files for historical context: "See round_1_routing.json for Phase 1 decisions"
```

**Feasibility:** MEDIUM
- Requires orchestrator to actively manage its own context
- Risk: LLM may not reliably "forget" what it wrote
- May need explicit instructions to not reference prior rounds

**Alternative: Structured State Object**
```markdown
## Orchestrator State (Keep Minimal)

Maintain ONLY this state object in context:
```json
{
  "session_id": "bazinga_xxx",
  "current_phase": 2,
  "groups_in_progress": ["PAT-CART", "PAT-HIST"],
  "groups_completed_this_phase": 2,
  "total_groups_this_phase": 4,
  "next_action": "wait_for_agent_completion"
}
```

Do NOT keep:
- Historical routing decisions
- Previous agent responses
- Completed group details (query from DB if needed)
```

**Feasibility:** MEDIUM-HIGH
- Enforces minimal state through explicit structure
- May require multiple prompt iterations to get compliance

---

## Comparative Analysis

| Fix | Token Savings | Feasibility | Risk | Implementation Effort |
|-----|---------------|-------------|------|----------------------|
| 1A: Phase Summary Files | ~5k/phase | HIGH | Low | 1-2 days |
| 2: Batch Phase Checks | ~2.4k/phase | HIGH | Low | 0.5 days |
| 3: Aggregate Routing | ~0.8k/round | HIGH | Low | 0.5 days |
| 4: Orchestrator CRP | ~8k/round | MEDIUM | Medium | 2-3 days |

**Combined savings estimate:**
- Fix 1A: 5k × 4 phases = 20k tokens saved
- Fix 2: 2.4k × 4 phases = 9.6k tokens saved
- Fix 3: 0.8k × 8 rounds = 6.4k tokens saved
- Fix 4: 8k × 4 rounds = 32k tokens saved

**Total potential savings: ~68k tokens** (enough for 2-3 additional rounds)

---

## Implementation Recommendation

### Phase 1: Quick Wins (1-2 days)
1. **Fix 2: Batch Phase Checks** - Modify `phase_parallel.md` Step 2B.7b
2. **Fix 3: Aggregate Routing** - Modify `phase_parallel.md` Step 2B.2

### Phase 2: Medium Effort (2-3 days)
3. **Fix 1A: Phase Summary Files** - Add phase-boundary summary logic to orchestrator

### Phase 3: Advanced (3-5 days)
4. **Fix 4: Orchestrator CRP** - Implement meta-level context offloading

### Implementation Order Rationale
- Fixes 2 & 3 are pure prompt changes with no architectural risk
- Fix 1A builds on existing CRP patterns
- Fix 4 is most complex but provides largest savings

---

## Risk Analysis

### Risk 1: LLM Non-Compliance
**Description:** Claude may not reliably follow instructions to minimize context
**Mitigation:**
- Add explicit "DO NOT" rules
- Add verification checkpoints ("Your context should contain < 1k tokens of routing history")
- Use structured output formats (JSON/tables) that are naturally compact

### Risk 2: State Loss on Interruption
**Description:** If orchestrator is interrupted mid-phase, local tracking may be lost
**Mitigation:**
- Always reconcile with database on resume
- Write checkpoints to files at key decision points
- Already handled by existing session resume logic

### Risk 3: Reduced Debugging Visibility
**Description:** With more state in files, harder to debug orchestration issues
**Mitigation:**
- Keep detailed logs in files (not context)
- Dashboard can read artifact files
- Add explicit "debug mode" that keeps verbose context

### Risk 4: Breaking Existing Workflows
**Description:** Changes to orchestrator may break edge cases
**Mitigation:**
- Incremental implementation (one fix at a time)
- Test with simple calculator integration test
- Maintain backward compatibility for simple mode

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Rounds before context exhaustion | ~4 | 8+ | Count rounds in parallel session |
| Context usage at Phase 4 end | 95%+ | <60% | Check context indicator |
| Token overhead per round | ~12k | <4k | Estimate from prompt length |
| Session completion rate | ~40% | 90%+ | Track BAZINGA success |

---

## Alternative Approaches Considered

### Alternative 1: Reduce Parallel Concurrency
**Concept:** Instead of 4 parallel developers, use 2
**Rejected:** Defeats parallelism value proposition, just delays the problem

### Alternative 2: Session Chunking with User Intervention
**Concept:** Require user to run `/compact` between phases
**Rejected:** Breaks autonomous orchestration, poor UX

### Alternative 3: Wait for Claude Code SDK Improvements
**Concept:** Hope for better context management in future versions
**Rejected:** No timeline, problem needs solving now

### Alternative 4: Streaming/Incremental Processing
**Concept:** Process agent returns as they arrive, don't batch
**Rejected:** Already doing this; the issue is accumulation over time, not batch size

---

## Implementation Details

### File: bazinga/templates/orchestrator/phase_parallel.md

#### Change 1: Optimized Phase Check (Fix 2)

**Before (lines 497-504):**
```markdown
**Actions:** 1) Update group status=completed, 2) Query ALL groups, 3) Load PM state for execution_phases, 4) Count: completed_count, in_progress_count, pending_count
```

**After:**
```markdown
**Actions:**
1) Update group status=completed via bazinga-db
2) Increment local phase tracker: `current_phase_completed += 1`
3) Output minimal capsule: `✅ {group} merged | Phase {N}: {current_phase_completed}/{current_phase_total}`
4) IF current_phase_completed == current_phase_total:
   - THEN query DB for next phase groups
   - ELSE skip DB query, continue waiting
```

#### Change 2: Aggregated Response Format (Fix 3)

**Before (lines 279-290):**
```markdown
**For EACH developer response:**
**Step 1: Parse response and output capsule to user**
[Individual capsules per developer]
```

**After:**
```markdown
**Batch all developer responses:**

**Step 1: Collect all responses into aggregated table**
```
| Group | Status | Files | Tests | Coverage | Next |
|-------|--------|-------|-------|----------|------|
```

**Step 2: Output SINGLE aggregated capsule**
```
🔨 **{N} Developers Complete** | {summary_stats}
{aggregated_table}
Routing: {X} QA, {Y} retry, {Z} TL
```

**Step 3: Spawn ALL next agents in ONE Task block**
```

### File: agents/orchestrator.md

#### Change 3: Phase Summary Offloading (Fix 1A)

**Add new section after Step 2B.7b:**
```markdown
### Step 2B.7c: Phase Summary Offloading (Context Management)

**After all groups in current phase reach MERGE_SUCCESS:**

1. Write phase summary to file:
   ```
   Write to bazinga/artifacts/{session_id}/orchestrator/phase_{N}_summary.json:
   {
     "phase": N,
     "groups_completed": ["A", "B", "C", "D"],
     "total_tests": 150,
     "total_coverage": "87%",
     "duration_minutes": 45,
     "routing_decisions": [prior decisions array]
   }
   ```

2. Clear routing history from context (conceptual):
   ```
   From this point, DO NOT reference Phase {N} routing decisions.
   If historical context needed, read from phase_{N}_summary.json
   ```

3. Continue to next phase with minimal state only
```

---

## Conclusion

The proposed fixes are feasible and address the root cause of context accumulation. The recommended implementation order prioritizes quick wins (Fixes 2 & 3) that can be deployed immediately, followed by more substantial changes (Fixes 1A & 4) that provide larger savings.

**Key insight:** The CRP fixed the symptom (large agent returns) but not the underlying issue (orchestrator's own context growth). These fixes complete the optimization by applying similar principles to the orchestrator itself.

**Expected outcome:** With all fixes implemented, parallel orchestration should sustain 8+ rounds (double current capacity), enabling completion of complex multi-phase projects without context exhaustion.

---

## References

- `research/parallel-context-overflow-analysis.md` - Original CRP analysis
- `bazinga/templates/orchestrator/phase_parallel.md` - Current parallel mode implementation
- `agents/orchestrator.md` - Main orchestrator logic
- CDC session transcript - Evidence of 4-round limitation

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-23)

### Critical Issues Identified

| Issue | Original Plan | OpenAI Feedback | Resolution |
|-------|---------------|-----------------|------------|
| **Write tool gap** | Fix 1A/4 use Write to create files | Orchestrator can't use Write tool | Use bazinga-db skill for state/context packages instead |
| **Local counters not persisted** | Fix 2 uses ephemeral local counter | Will drift on resume/retry | Persist in bazinga-db orchestrator state |
| **Routing logic in context** | Aggregation adds decision logic | Use workflow-router skill | Defer routing decisions to skill, not in-context |
| **No token telemetry** | Rough estimates only | Missing feedback loop | Query token_usage table, add threshold gates |

### Incorporated Feedback

#### 1. DB-First State Management (Adopted)

**Original:** Local phase counters in orchestrator context
**Changed to:** Persist all tracking via bazinga-db:

```json
{
  "current_phase": N,
  "phase_group_totals": {"PHASE_N": 4},
  "phase_group_completed": {"PHASE_N": 2},
  "templates_loaded": ["phase_parallel", "message_templates"],
  "last_processed_group_ids": ["A", "B"]
}
```

**Rationale:** Enables deterministic resume, prevents drift, eliminates ephemeral state issues.

#### 2. Skill-First Artifact Writing (Adopted)

**Original:** Orchestrator writes files directly (Fix 1A, Fix 4)
**Changed to:** Two options:
- **Option A (Preferred):** Use `bazinga-db save-context-package` to store phase summaries as context packages
- **Option B:** Create minimal `artifact-writer` skill for orchestrator use

**Rationale:** Respects orchestrator tool constraints while achieving same goal.

#### 3. Workflow-Router Integration (Adopted)

**Original:** Inline routing logic in orchestrator
**Changed to:** Call `workflow-router` skill for each response, batch spawn queue:

```
1. Parse all responses
2. For each: Skill(command: "workflow-router") → get next_agent
3. Build spawn queue from router outputs
4. Spawn all in ONE Task block
5. Output single aggregated capsule
```

**Rationale:** Reduces in-prompt decision tokens, deterministic routing, existing skill underutilized.

#### 4. Template Caching (Adopted)

**Original:** Not addressed
**Changed to:** Track loaded templates in orchestrator state:

```markdown
### Template Loading Protocol

BEFORE Read(file_path: "bazinga/templates/X.md"):
1. Check orchestrator state: templates_loaded array
2. IF "X" in templates_loaded → SKIP Read, use cached reference
3. ELSE → Read template, add "X" to templates_loaded in state
```

**Rationale:** Prevents repeated 5k+ token template injections across turns.

#### 5. Token Telemetry Gates (Adopted)

**Original:** Not addressed
**Changed to:** Add threshold-based compaction triggers:

```markdown
### Context Threshold Protocol

Every turn, check context usage:
- 70% threshold → Switch to ultra-compact capsules (counts only)
- 80% threshold → Force phase summary offload to DB
- 90% threshold → Emergency mode: skip non-essential logs, DB reconciliation only
```

**Rationale:** Proactive intervention before context exhaustion.

### Rejected Suggestions (With Reasoning)

#### 1. Spec-kit Orchestrator Parity (Deferred)
**Suggestion:** Mirror changes to orchestrator_speckit.md
**Decision:** Defer to separate PR
**Reasoning:** Different use case (spec-kit is sequential), changes not directly applicable, would double scope

#### 2. Transaction-like DB Sequences (Deferred)
**Suggestion:** Use transaction guards for idempotency
**Decision:** Out of scope for this fix
**Reasoning:** bazinga-db skill doesn't support transactions; idempotency can be achieved via status checks before updates

### Revised Implementation Plan

| Phase | Fix | Original Approach | Revised Approach |
|-------|-----|-------------------|------------------|
| 1 | Batch Phase Checks | Local counters | **DB-persisted state via bazinga-db** |
| 1 | Aggregate Routing | Inline logic | **workflow-router skill + single capsule** |
| 2 | Phase Summaries | Write to files | **bazinga-db context packages** |
| 2 | Template Caching | Not included | **State flag tracking** |
| 3 | Token Gates | Not included | **Threshold-based compaction triggers** |

### Updated Token Savings Estimate

| Fix | Original Estimate | Revised Estimate | Notes |
|-----|-------------------|------------------|-------|
| Batch Phase Checks (DB) | 2.4k/phase | 3k/phase | Includes template caching benefit |
| Aggregate Routing (Router) | 0.8k/round | 2k/round | Router eliminates inline decision logic |
| Phase Summaries (Context Pkg) | 5k/phase | 5k/phase | Same savings, different mechanism |
| Token Gates | N/A | 5k+ (emergency) | Prevents overflow, enables recovery |

**Revised total savings:** ~70-80k tokens across 4 phases (improved from original ~68k)

### Revised Risk Matrix

| Risk | Original Severity | Revised Severity | Mitigation Applied |
|------|-------------------|------------------|-------------------|
| Write tool policy violation | HIGH | LOW | Using bazinga-db skill instead |
| State drift on resume | HIGH | LOW | DB-persisted state |
| Aggregation deadlock | MEDIUM | LOW | Process "all arrived now" policy explicit |
| Escalation path omissions | MEDIUM | LOW | workflow-router handles all status codes |
| Template bloat | MEDIUM | LOW | Caching flag protocol added |

### Implementation Confidence

**Original:** Medium
**Revised:** Medium-High

The LLM review identified real gaps (Write tool, state persistence, router underuse) that would have caused implementation failures. With these addressed, the approach is architecturally sound and aligned with existing BAZINGA patterns.
