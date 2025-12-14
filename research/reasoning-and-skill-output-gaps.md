# Reasoning Storage and Skill Output Persistence Gaps

**Date:** 2025-12-14
**Context:** Integration test revealed gaps in PM reasoning and specialization-loader output persistence
**Decision:** Enforce orchestrator-level requirements, add structured context passing
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

During the integration test for session `bazinga_20251214_115050`, two gaps were identified:

1. **PM 'understanding' phase missing** - Only 7 reasoning entries captured instead of expected 8. PM saved `completion` phase but not `understanding` phase.

2. **Specialization-loader outputs incomplete** - Only 1 of 3 expected skill outputs persisted to database. The skill was invoked for developer, qa_expert, and tech_lead, but only tech_lead's output was saved.

These gaps affect audit trail completeness and post-mortem analysis capabilities.

---

## Root Cause Analysis

### Issue 1: PM 'understanding' Phase Missing

**Current behavior:**
- PM is invoked twice during orchestration:
  1. **Planning phase** - Analyzes requirements, creates task groups, assigns to developers
  2. **Completion phase** - Verifies success criteria, sends BAZINGA

- In planning phase, PM creates task groups but doesn't save reasoning with phase="understanding"
- In completion phase, PM saves reasoning with phase="completion"

**Root cause:**
The PM agent prompt (agents/project_manager.md) defines reasoning phases but the orchestrator's PM spawn prompts don't explicitly require PM to save understanding reasoning at the start.

**Evidence from PM prompt (lines 2457-2469):**
```
| understanding | REQUIRED at task start | User request summary, scope assessment |
| completion | REQUIRED at BAZINGA | Summary of what was accomplished |
```

**Gap:** The orchestrator spawns PM for planning without instructing PM to save "understanding" phase reasoning. PM only saves "completion" phase when doing BAZINGA verification.

### Issue 2: Specialization-Loader Outputs Incomplete

**Current behavior:**
- Orchestrator invokes specialization-loader skill 3 times (developer, qa_expert, tech_lead)
- Only tech_lead invocation persisted to database
- developer and qa_expert invocations either didn't save or failed silently

**Root cause candidates:**

**A. Skill invocation method inconsistency:**
- Specialization-loader is designed to output via Bash heredoc (to keep turn alive)
- If skill doesn't explicitly call `save-skill-output` command, nothing persists
- The skill returns composed block via stdout but may not always save metadata

**B. Session/group context missing:**
- `save-skill-output` requires `session_id` parameter
- If orchestrator doesn't pass session_id to the skill invocation, skill can't save

**C. Timing issue:**
- Earlier invocations (developer, qa_expert) may have failed to save
- Only last invocation (tech_lead) succeeded
- This suggests skill state or context may be lost between invocations

**D. Skill implementation gap:**
- SKILL.md Step 7 shows save-skill-output command
- But implementation may not always execute Step 7
- Success/failure of database save is not verified

---

## Proposed Solutions

### Solution 1: PM Planning Reasoning Capture

**Option A: Split PM invocations with mandatory phases**

Modify orchestrator to require PM to save understanding at start:

```markdown
## PM Planning Spawn Prompt

You are the Project Manager. Session ID: {session_id}

**MANDATORY FIRST ACTION:**
Before any analysis, save your understanding of the request:

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{session_id}" "PLANNING" "project_manager" "understanding" \
  --content-file /tmp/pm_understanding.md --confidence high
```

Include in understanding:
- Raw request summary
- Scope type (file, feature, bug)
- Initial complexity assessment
- Key constraints identified
```

**Pros:**
- Forces PM to capture understanding before planning
- Creates audit trail of initial interpretation
- Matches expected 2 phases per agent pattern

**Cons:**
- Adds overhead to PM spawn
- PM understanding is about whole request, not a specific task group
- group_id="PLANNING" is not a real task group

**Option B: Treat PM differently - 1 phase per invocation**

Accept that PM has different workflow:
- Planning phase → "planning" reasoning (not "understanding")
- Completion phase → "completion" reasoning

Reasoning: PM operates at session level, not task-group level. Other agents (developer, qa, tech_lead) work on specific task groups and have understanding→completion per group. PM plans all groups initially and verifies all groups at end.

**Pros:**
- Matches PM's actual workflow
- Simpler - don't force PM into task-group pattern
- Still captures PM reasoning at both phases

**Cons:**
- Inconsistent with other agents (2 phases each)
- check-mandatory-phases will still fail for PM

**Option C: Create PM-specific phase requirements**

Modify check-mandatory-phases to have agent-specific required phases:

```python
MANDATORY_PHASES = {
    "developer": ["understanding", "completion"],
    "qa_expert": ["understanding", "completion"],
    "tech_lead": ["understanding", "completion"],
    "project_manager": ["planning", "completion"],  # Different phases
}
```

**Pros:**
- Reflects actual PM workflow
- Validation passes correctly
- Clear semantics (PM plans, others understand)

**Cons:**
- Requires bazinga-db schema awareness
- More complex validation logic

**Recommendation:** Option C - PM-specific phases

### Solution 2: Specialization-Loader Output Persistence

**Option A: Make save-skill-output mandatory in skill**

Modify SKILL.md to ALWAYS call save-skill-output before returning:

```markdown
## Step 7: MANDATORY Database Persistence (REQUIRED)

You MUST save the skill output to database before returning:

```bash
# Create metadata file
cat > /tmp/spec_output.json << 'EOF'
{
  "group_id": "{group_id}",
  "agent_type": "{agent_type}",
  "model": "{model}",
  "templates_used": [...],
  "token_count": {count},
  "composed_identity": "{summary}"
}
EOF

# Save to database
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-skill-output \
  "{session_id}" "specialization-loader" --content-file /tmp/spec_output.json

# Verify save succeeded
if [ $? -ne 0 ]; then
  echo "WARNING: Failed to save skill output to database"
fi
```

**CRITICAL:** Do NOT skip this step. Skill invocation is incomplete without database persistence.
```

**Pros:**
- Ensures all invocations are persisted
- Explicit verification of save success
- Clear audit trail

**Cons:**
- Adds bash execution overhead
- Requires session_id to be passed to skill

**Option B: Orchestrator saves skill output after invocation**

Instead of skill saving itself, orchestrator captures skill output and saves:

```markdown
## Orchestrator Post-Skill Pattern

After invoking specialization-loader:
1. Extract metadata from skill output
2. Save to database via bazinga-db skill
3. Pass composed block to agent spawn

```bash
# After skill returns, orchestrator saves
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-skill-output \
  "{session_id}" "specialization-loader" '{...metadata...}'
```
```

**Pros:**
- Centralized save logic in orchestrator
- Skill stays simpler
- Orchestrator has session context

**Cons:**
- Orchestrator becomes more complex
- Skill output parsing required
- Two places need coordination

**Option C: Skill returns structured JSON, orchestrator saves**

Skill outputs structured JSON instead of markdown heredoc:

```json
{
  "composed_block": "..markdown..",
  "metadata": {
    "templates_used": [...],
    "token_count": 500
  }
}
```

Orchestrator parses JSON, saves metadata, passes block to agent.

**Pros:**
- Clean separation of concerns
- Structured output easier to parse
- No markdown heredoc complexity

**Cons:**
- Changes skill contract
- JSON in bash output is fragile
- Breaking change to existing skill

**Recommendation:** Option A - Mandatory save in skill

### Solution 3: Pass Session Context to Skills

Current gap: Skills may not have session_id to save outputs.

**Solution:** Orchestrator must always pass session context when invoking skills:

```markdown
## Skill Invocation Pattern

When invoking specialization-loader (or any skill that saves output):

Skill(command: "specialization-loader")

Then provide context in the follow-up prompt:
- session_id: {current_session_id}
- group_id: {current_group_id}
- agent_type: {target_agent_type}
- model: {target_model}
```

This ensures skill has all context needed to save outputs.

---

## Implementation Plan

### Phase 1: PM-Specific Phases (Low Risk)

1. Update `check-mandatory-phases` command in bazinga-db to accept agent-specific phase requirements
2. Define PM phases as `["planning", "completion"]` instead of `["understanding", "completion"]`
3. Update PM spawn prompts to save "planning" reasoning at start
4. Update verification commands in claude.md

**Files to modify:**
- `.claude/skills/bazinga-db/scripts/bazinga_db.py` - add agent-specific phases
- `agents/project_manager.md` - clarify phase names
- `.claude/claude.md` - update verification expectations

### Phase 2: Mandatory Skill Output Persistence (Medium Risk)

1. Add explicit save-skill-output step to specialization-loader SKILL.md
2. Add verification that save succeeded
3. Update orchestrator spawn prompts to pass session_id to skill
4. Add integration test verification for 3 skill outputs

**Files to modify:**
- `.claude/skills/specialization-loader/SKILL.md` - add mandatory save step
- `agents/orchestrator.md` - pass session context to skills
- `.claude/claude.md` - update verification for 3 entries

### Phase 3: Comprehensive Testing (Low Risk)

1. Re-run integration test
2. Verify 8 reasoning entries (or 7 with PM-specific phases)
3. Verify 3 specialization-loader outputs
4. Update test report template

---

## Critical Analysis

### Pros

1. **Complete audit trail** - All agent reasoning and skill outputs captured
2. **Post-mortem capability** - Can analyze decisions after session ends
3. **Debugging support** - When things go wrong, reasoning explains why
4. **Consistent patterns** - All agents follow similar documentation patterns

### Cons

1. **Increased overhead** - More database writes per session
2. **Complexity** - More places where things can fail
3. **Storage growth** - Reasoning content can be large
4. **Performance** - Bash commands for DB writes add latency

### Risks

1. **Silent failures** - If save-skill-output fails, session continues but data lost
2. **Context loss** - Skills may not have session_id if not passed
3. **Phase confusion** - PM phases differ from other agents

### Verdict

The benefits of complete audit trails outweigh the overhead costs. The implementation is straightforward with clear file modifications. Risk is low because changes are additive (not breaking existing functionality).

---

## Comparison to Alternatives

### Alternative 1: Accept Incomplete Data

Just accept that PM has different phases and skill outputs may not always save.

**Rejected because:** Defeats purpose of reasoning storage. Audit trails should be complete.

### Alternative 2: Post-Process Extraction

Parse agent outputs after session to extract reasoning.

**Rejected because:** Unreliable - agent output format varies. Database storage is more reliable.

### Alternative 3: Mandatory Pre-Flight Checks

Before session starts, verify all skills can save outputs.

**Rejected because:** Over-engineering. Simple fix is to make save-skill-output mandatory in skill.

---

## Decision Rationale

1. **PM-specific phases** - Reflects actual PM workflow better than forcing "understanding" phase
2. **Mandatory skill save** - Skills should be responsible for their own persistence
3. **Session context passing** - Orchestrator owns session, must share with skills

These decisions align with:
- Single responsibility principle (skills save their outputs)
- Explicit over implicit (mandatory save step, not optional)
- Consistency where possible, flexibility where needed (PM phases differ for good reason)

---

## Multi-LLM Review Integration

### Consensus Points (OpenAI)

1. **Orchestrator enforcement is the right layer** - Don't change DB schema or phase taxonomy
2. **Structured context passing needed** - Skill relies on brittle text parsing for session_id
3. **Post-call verification essential** - Silent failures will persist without orchestrator checks
4. **Use "global" for PM scope** - Don't invent synthetic group IDs like "PLANNING"

### Incorporated Feedback

| Original Proposal | Reviewer Feedback | Revised Approach |
|-------------------|-------------------|------------------|
| PM-specific phases in DB | Overreach, breaks validation | Keep phases unchanged, enforce via orchestrator |
| group_id="PLANNING" | Undefined behavior | Use group_id="global" (existing pattern) |
| Skill saves itself | Context passing is brittle | Add JSON context file + orchestrator fallback |
| Hope skill saves work | Silent failures | Add post-call verification gate |

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| Alias mapping (planning→understanding) | Over-engineering; just enforce existing requirement |
| Telemetry events | Out of scope for this fix; adds complexity |

### Revised Implementation Plan

**Phase 1: PM Understanding Enforcement (No Schema Changes)**

1. **Modify orchestrator PM spawn prompt** to include mandatory first action:
   ```markdown
   **MANDATORY FIRST ACTION:**
   Save your understanding of this request before any analysis:

   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
     "{session_id}" "global" "project_manager" "understanding" \
     --content-file /tmp/pm_understanding.md --confidence high
   ```

2. **No changes to bazinga-db** - keep check-mandatory-phases as-is

3. **Update PM verification** to expect group_id="global" for understanding phase

**Phase 2: Structured Context for Specialization-Loader**

1. **Orchestrator writes context file before skill invocation:**
   ```bash
   mkdir -p bazinga/artifacts/{session_id}/skills
   cat > bazinga/artifacts/{session_id}/skills/spec_ctx_{group}_{agent}.json << EOF
   {
     "session_id": "{session_id}",
     "group_id": "{group_id}",
     "agent_type": "{agent_type}",
     "model": "{model}",
     "testing_mode": "full",
     "specialization_paths": [...]
   }
   EOF
   ```

2. **Update SKILL.md** to read context from JSON file (not conversational text)

3. **Skill saves output using context from file** (guaranteed to have session_id)

**Phase 3: Orchestrator Post-Call Verification**

1. **After each specialization-loader call, verify output saved:**
   ```bash
   # Verify skill output was saved
   OUTPUT=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet \
     get-skill-output "{session_id}" "specialization-loader" --agent "{agent_type}")

   if [ -z "$OUTPUT" ]; then
     echo "WARNING: Skill output not saved, orchestrator saving fallback..."
     # Parse skill stdout for metadata and save manually
   fi
   ```

2. **Add integration test assertions:**
   - PM understanding (global) exists
   - 3 specialization-loader outputs exist
   - All mandatory phases documented

### Files to Modify

| File | Change |
|------|--------|
| `agents/orchestrator.md` | Add PM understanding enforcement, add context file creation, add post-call verification |
| `.claude/skills/specialization-loader/SKILL.md` | Read context from JSON file, fail loudly if missing |
| `.claude/claude.md` | Update verification to expect group_id="global" for PM |

### Risk Assessment (Post-Review)

| Risk | Mitigation |
|------|------------|
| JSON file not created | Skill fails loudly (good - visible failure) |
| Orchestrator skips verification | Add to mandatory workflow section |
| DB lock contention | bazinga_db already has retry logic |
| Backward compatibility | No schema changes = no migration needed |

**Confidence Level:** HIGH - Orchestrator enforcement + structured context + verification is robust and low-risk.

---

## References

- `agents/project_manager.md` - PM reasoning documentation requirements
- `.claude/skills/specialization-loader/SKILL.md` - Skill output requirements
- `research/specialization-loader-output-fix.md` - Prior fix for output mechanism
- `.claude/skills/bazinga-db/scripts/bazinga_db.py` - Database CLI commands
- `tmp/ultrathink-reviews/openai-review.md` - OpenAI GPT-5 review feedback
