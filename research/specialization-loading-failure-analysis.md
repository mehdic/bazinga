# Specialization Loading Failure Analysis: Why Templates Are Read But Skill Not Invoked

**Date:** 2025-12-11
**Context:** User reports specializations not loading even after template Read succeeds
**Decision:** Two-turn spawn sequence (Skill in Turn 1, Task in Turn 2)
**Status:** Implemented
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The orchestrator:
1. ✅ Reads the phase template (`phase_simple.md` or `phase_parallel.md`)
2. ✅ Template contains MANDATORY SPAWN SEQUENCE with specialization loading
3. ❌ Skill `specialization-loader` is NEVER invoked
4. ❌ Agent spawns with generic prompt, missing technology-specific guidance

**Evidence from user trace:**
```
Orchestrator: Read agents/senior_software_engineer.md
Orchestrator: Read src/target_file.ts
Orchestrator: [Spawns SSE directly with Task()]
// NO Skill(command: "specialization-loader") call
// NO [SPEC_CTX_START] block output
// NO specialization block in prompt
```

---

## Root Cause Hypothesis Matrix

### Hypothesis 1: Efficiency Optimization (HIGH CONFIDENCE)

**Evidence from research:**
> "Claude 4.5 models tend toward efficiency and may skip verbal summaries after tool calls, jumping directly to the next action."
> — [Claude 4 Best Practices](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)

**Mechanism:**
- Claude sees the template with 4 spawn steps
- Identifies end goal: spawn agent with prompt
- Optimizes by skipping "intermediate" steps
- Views skill invocation as optional enhancement, not blocking requirement

**Why this explains the bug:**
- Template is READ (checked)
- MANDATORY markers are SEEN
- But Claude's efficiency heuristic says "I can achieve spawn without this step"
- Jumps directly to Task() call

### Hypothesis 2: Documentation vs Action Confusion (HIGH CONFIDENCE)

**The template format problem:**
```markdown
**2c. IMMEDIATELY invoke the skill** (no other output between context and this):
```
Skill(command: "specialization-loader")
```
```

This is **documentation-style** formatting. Claude may interpret this as:
- "This is what the skill invocation looks like" (informational)
- Rather than: "I must execute this right now" (imperative)

**Evidence from research:**
> "If you say 'can you suggest some changes,' Claude will sometimes provide suggestions rather than implementing them."
> — [Why Is Claude Not Following Instructions?](https://beginswithai.com/why-is-claude-not-following-instructions/)

### Hypothesis 3: Long Context Instruction Decay (MEDIUM CONFIDENCE)

**Mechanism:**
- Orchestrator definition is ~1600 lines
- Phase template adds ~900 lines
- Earlier instructions (specialization loading) compete with later instructions (spawn)
- Claude prioritizes recent/proximate instructions

**Evidence from research:**
> "When you give Claude a massive, multi-step task... It loses focus - the longer the generation, the more likely the AI is to drift from the original instructions."
> — [Mastering Prompt Engineering for Claude](https://www.walturn.com/insights/mastering-prompt-engineering-for-claude)

### Hypothesis 4: Human Message vs System Prompt Priority (MEDIUM CONFIDENCE)

**Mechanism:**
- Phase templates are loaded via Read tool (appears as system/context)
- User's original request is in human message
- Claude prioritizes human message goal ("implement X") over system instructions

**Evidence from research:**
> "Claude follows instructions in the human messages (the actual user prompts) better than those in the system message. Use the system message mainly for high-level scene setting."
> — [Prompt Engineering with Anthropic Claude](https://medium.com/promptlayer/prompt-engineering-with-anthropic-claude-5399da57461d)

### Hypothesis 5: Missing Verification Loop (HIGH CONFIDENCE)

**The template lacks:**
1. Verification that skill was actually called (not just documented)
2. User-visible output confirming specializations loaded
3. Blocking mechanism preventing spawn without prior skill result

**Current flow:**
```
Template says: "Invoke skill"
Claude thinks: "I understand"
Claude does: [Nothing, proceeds to spawn]
```

**Required flow:**
```
Template says: "Invoke skill"
Claude outputs: [SPEC_CTX_START]...
Claude calls: Skill(command: "specialization-loader")
System returns: [SPECIALIZATION_BLOCK_START]...
Only then: Claude proceeds to spawn
```

### Hypothesis 6: No Forcing Function (HIGH CONFIDENCE)

**Problem:** The spawn step doesn't require proof of specialization loading.

**Current Step 4:**
```markdown
**Spawn the agent:**
Task(subagent_type="general-purpose", model=MODEL_CONFIG[...], prompt=full_prompt)
```

**Missing:** Validation that `full_prompt` contains specialization block.

Claude can construct `full_prompt = base_prompt` (skipping Step 2) and still satisfy Step 4.

---

## Analysis: Why Current Fixes Failed

### Fix Attempt 1: Added MANDATORY markers
- ❌ Claude's efficiency heuristic overrides MANDATORY text
- Text markers don't create execution barriers

### Fix Attempt 2: Restructured spawn sequence
- ❌ Reordering doesn't prevent skipping
- Claude can still optimize "unnecessary" steps

### Fix Attempt 3: Removed Quick Reference
- ✅ Partial improvement - removed easy shortcut
- ❌ But Claude can still skip steps in the full template

### Fix Attempt 4: Added verification checkpoint
- ❌ Checkpoint is self-checked (honor system)
- Claude can "verify" by thinking "yes I did it" without actually doing it

---

## Solution Framework

Based on research, effective solutions must create **forcing functions** - mechanisms that make skipping impossible.

### Solution Category A: Tool-Level Enforcement

**A1: Skill Invocation Before Spawn Detection**
- Modify spawn execution to check conversation history for skill invocation
- Block spawn if no `Skill(command: "specialization-loader")` found in recent turns
- **Pro:** Guaranteed enforcement
- **Con:** Requires code changes to spawn mechanism

**A2: Required Tool Sequence**
- Make `specialization-loader` a prerequisite tool for `Task`
- System-level enforcement, not prompt-level
- **Pro:** Cannot be bypassed
- **Con:** Significant infrastructure change

### Solution Category B: Prompt Engineering Forcing Functions

**B1: Output-Required Pattern**
Make specialization output VISIBLE and REQUIRED:
```markdown
**STEP 2: YOU MUST OUTPUT THIS EXACT BLOCK NOW:**
```
I am now invoking specialization-loader:
[SPEC_CTX_START group={group_id} agent={agent_type}]
Session ID: {session_id}
...
[SPEC_CTX_END]
```
Then call: Skill(command: "specialization-loader")

**🔴 IF YOU DO NOT SEE "[SPEC_CTX_START" IN YOUR OUTPUT ABOVE, YOU SKIPPED THIS STEP. GO BACK.**
```

**Rationale:** Forces Claude to produce visible output before the skill call. If output is missing, user can see the skip.

**B2: Chain-of-Thought Verification**
Add explicit thinking verification:
```markdown
**Before Step 4, you MUST complete this checklist IN YOUR OUTPUT:**
```
✓ Step 2 Verification:
- Did I output [SPEC_CTX_START] block? [YES/NO]
- Did I call Skill(command: "specialization-loader")? [YES/NO]
- Did I receive [SPECIALIZATION_BLOCK_START] in response? [YES/NO]
- Is specialization_block set to the response? [YES/NO]

IF ANY ANSWER IS "NO": STOP. Go back and complete Step 2.
```
```

**Rationale:** Forces explicit reasoning trace that's auditable.

**B3: Blocking Gate Pattern**
```markdown
**Step 2 GATE (BLOCKING):**

This step produces output. If you proceed to Step 3 without producing this output, you have failed.

Required output format:
```
📜 SPECIALIZATION LOADING IN PROGRESS
[SPEC_CTX_START group={X} agent={Y}]
...
[SPEC_CTX_END]
```

[CALL SKILL NOW - NO FURTHER TEXT UNTIL SKILL RETURNS]
Skill(command: "specialization-loader")
```

**Rationale:** Creates visible gate that's obvious when missing.

**B4: User-Visible Confirmation**
```markdown
**After Step 2, output this confirmation to user:**
```
✅ Specializations loaded | Templates: {N} | Tokens: {X}/{Y} | Identity: {summary}
```

**IF you cannot output this line, specializations were NOT loaded. STOP and debug.**
```

**Rationale:** Makes success/failure visible to user who can interrupt if missing.

### Solution Category C: Structural Changes

**C1: Separate Skill Invocation Turn**
Split spawn into two turns:
1. Turn 1: Load specializations (skill call)
2. Turn 2: Spawn agent (Task call)

Forces the skill result to be in context before spawn can occur.

**C2: Pre-Spawn Checkpoint**
Add a human-in-the-loop checkpoint:
```markdown
**Before spawning, output to user:**
```
🚀 Ready to spawn {agent_type}
- Specializations: {status}
- Model: {model}
- Task: {summary}

[Proceeding in 3 seconds... Type STOP to halt]
```
```

**Rationale:** User can see if specializations loaded and intervene.

**C3: Required Specialization Block Reference**
Make the Task call require specialization proof:
```markdown
**Step 4: Spawn (REQUIRES SPECIALIZATION PROOF):**

In your Task call, you MUST include this parameter:
```
Task(
  subagent_type="general-purpose",
  model=MODEL_CONFIG[...],
  description="...",
  prompt=full_prompt  // MUST contain [SPECIALIZATION_BLOCK_START]
)
```

**Validation:** If full_prompt does NOT contain "[SPECIALIZATION_BLOCK_START]",
specializations are missing. Either:
1. Re-run Step 2
2. OR set specializations_status = "disabled" and document why
```

---

## Recommended Solution: Multi-Layer Defense

Based on analysis, no single solution is sufficient. Implement layered approach:

### Layer 1: Visible Output Requirement (B1)
Force orchestrator to output the context block visibly. Missing output = obvious skip.

### Layer 2: Chain-of-Thought Checklist (B2)
Require explicit YES/NO verification before spawn. Creates audit trail.

### Layer 3: User-Visible Confirmation (B4)
Output specialization status to user. User can intervene on failure.

### Layer 4: Blocking Gate (B3)
Make Step 2 produce required output format. No output = gate not passed.

---

## Implementation Plan

### Phase 1: Rewrite Step 2 in Templates
Transform from documentation to action-forcing format:

**Before (documentation style):**
```markdown
**2c. IMMEDIATELY invoke the skill** (no other output between context and this):
```
Skill(command: "specialization-loader")
```
```

**After (action-forcing style):**
```markdown
**2c. OUTPUT AND INVOKE NOW:**

YOU MUST NOW PRODUCE THIS EXACT OUTPUT (copy/adapt):
```text
📜 SPECIALIZATION LOADING
[SPEC_CTX_START group=main agent=developer]
Session ID: {session_id}
Group ID: main
Agent Type: developer
Model: haiku
Specialization Paths: ["templates/specializations/..."]
[SPEC_CTX_END]
```

IMMEDIATELY AFTER THE ABOVE OUTPUT, CALL:
Skill(command: "specialization-loader")

DO NOT WRITE ANY OTHER TEXT. THE NEXT THING IN YOUR MESSAGE MUST BE THE SKILL CALL.

---

**2d. WAIT AND VERIFY:**

After skill returns, verify you received:
- `[SPECIALIZATION_BLOCK_START]`
- `[SPECIALIZATION_BLOCK_END]`

IF NOT PRESENT: Output `⚠️ Specialization loading failed` and set status accordingly.
```

### Phase 2: Add Pre-Spawn Checkpoint
```markdown
### SPAWN STEP 3.5: PRE-SPAWN VERIFICATION (MANDATORY OUTPUT)

Before proceeding to Step 4, you MUST output this checklist:

```text
✅ PRE-SPAWN CHECKLIST
- Base prompt built: [YES]
- Specialization context output: [YES/NO - if NO, explain]
- Skill invoked: [YES/NO - if NO, explain]
- Specialization block received: [YES/NO - if NO, explain]
- full_prompt contains specializations: [YES/NO]

Status: {READY TO SPAWN / BLOCKED - explain}
```

IF STATUS IS NOT "READY TO SPAWN": Do not proceed. Fix the issue first.
```

### Phase 3: User Confirmation Output
```markdown
### SPAWN STEP 4: EXECUTE (WITH USER VISIBILITY)

**Output to user before Task call:**
```text
🚀 Spawning {agent_type} | Group: {group_id} | Model: {model}
📋 Specializations: {loaded/failed/disabled} | Templates: {N}
📝 Task: {task_summary_50_chars}
```

THEN call Task().
```

---

## Verification Strategy

After implementing, verify with test scenarios:

### Test 1: Normal Flow
- Invoke orchestrator with simple task
- Verify: `[SPEC_CTX_START]` appears in output
- Verify: Skill invocation in tool calls
- Verify: Spawned prompt contains specialization block

### Test 2: Stress Test (Long Conversation)
- Run orchestrator through 10+ turns
- Check if specializations still load on turn 15
- Watch for context decay

### Test 3: Disabled Specializations
- Set `skills_config.json` specializations.enabled = false
- Verify: Orchestrator outputs "Specializations: disabled"
- Verify: No skill invocation attempt
- Verify: Spawn proceeds with base prompt

### Test 4: Skill Failure
- Mock skill to return error
- Verify: Graceful degradation output visible
- Verify: Spawn proceeds with base prompt + status="error"

---

## Alternative Approaches Considered

### Rejected: Hook-Based Enforcement
- Add pre-spawn hook to verify specialization loading
- **Rejected because:** Adds complexity, hooks can fail silently

### Rejected: Database Verification
- Store specialization loading status in DB
- Check DB before spawn
- **Rejected because:** Adds latency, DB calls can fail

### Rejected: Hardcoded Model Rules
- Make specialization loading model-behavior, not prompt-behavior
- **Rejected because:** Requires Anthropic changes, not controllable

---

## Risk Assessment

### Risk 1: Over-Engineering
- Adding too many checkpoints slows orchestration
- **Mitigation:** Checkpoints are output-only (no extra tool calls)

### Risk 2: Prompt Bloat
- Adding verification text increases token count
- **Mitigation:** Use concise markers, leverage XML tags

### Risk 3: False Confidence
- Checklist could be "checked" without actual verification
- **Mitigation:** Require visible output that can be audited

---

## Success Metrics

1. **Primary:** Specialization block present in 100% of spawned agent prompts (when enabled)
2. **Secondary:** User can see specialization status before spawn
3. **Tertiary:** Graceful degradation visible when skill fails

---

## Lessons Learned

1. **MANDATORY text is not a forcing function.** Claude can acknowledge requirements while skipping them.
2. **Documentation-style prompts invite interpretation.** Action-forcing prompts require specific output.
3. **Efficiency is the enemy of thoroughness.** Claude 4.5 will skip "unnecessary" steps.
4. **Verification must be visible.** Self-checks without output can be bypassed mentally.
5. **Layer defenses.** No single mechanism is sufficient for multi-step workflows.

---

## References

- [Claude 4 Best Practices](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Why Is Claude Not Following Instructions?](https://beginswithai.com/why-is-claude-not-following-instructions/)
- [Mastering Prompt Engineering for Claude](https://www.walturn.com/insights/mastering-prompt-engineering-for-claude)
- [Prompt Engineering with Anthropic Claude](https://medium.com/promptlayer/prompt-engineering-with-anthropic-claude-5399da57461d)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Building Effective Agents - Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [Extended Thinking Tips](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/extended-thinking-tips)

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-11)

### Critical Feedback Summary

**The external review identified a fundamental flaw in my proposed solutions:**

> "The plan relies heavily on 'MANDATORY' text, visible gates, and checklists inside prompts. This does not create a hard constraint and is exactly what's failing today (Claude skips steps). You need a programmatic guard, not just instructional prose."

This is the key insight: **Prompt-based enforcement is brittle. We need procedural/DB enforcement.**

### Incorporated Feedback

#### 1. DB-Backed Pre-Spawn Enforcement (ACCEPTED ✅)
**Before:** Rely on prompt text to ensure skill invocation
**After:** Query bazinga-db for recent specialization-loader output before Task() spawn

```
Before Task():
  1. Query: bazinga-db get-skill-output session_id={} skill="specialization-loader" group_id={} agent_type={}
  2. IF missing/stale AND specializations.enabled:
     - Output SPEC_CTX block (internally, not to user)
     - Skill(command: "specialization-loader")
     - Validate block received
     - Save to DB
  3. IF still failing: set specializations_status="error", proceed with base prompt
  4. THEN: Task() spawn
```

**Why accepted:** Creates verifiable state before spawn. If DB has no record, spawn is blocked.

#### 2. Single-Message Atomic Sequence (ACCEPTED ✅)
**Before:** Split specialization loading and spawn across turns
**After:** Keep both in same message, sequenced

**Why accepted:** Avoids "intent without action" bug. Same message = same execution context.

#### 3. Remove User-Interaction Gates (ACCEPTED ✅)
**Before:** "Proceeding in 3 seconds... Type STOP to halt"
**After:** Silent execution with single capsule: `🔧 Specializations: loaded (3 templates)`

**Why accepted:** Contradicts orchestrator autonomy rules. User gates violate BAZINGA principles.

#### 4. Minimal User Output (ACCEPTED ✅)
**Before:** Verbose checklists, visible SPEC_CTX blocks, confirmation prompts
**After:** Single capsule line + DB logging for audit trail

**Why accepted:** Capsule format is the BAZINGA standard. Verbose output = UI pollution.

#### 5. Once-Per-Group Materialization (ACCEPTED ✅)
**Before:** Run specialization-loader on every spawn
**After:** Run once per (session, group_id, agent_type), cache in DB, reuse

**Why accepted:** Reduces token load, eliminates mid-spawn fragility.

### Rejected Suggestions (With Reasoning)

#### 1. Parameterized Skill Variant (REJECTED ❌)
**Suggestion:** Extend skill to accept JSON args instead of parsing chat text
**Reason for rejection:** Skills currently can't receive parameters in BAZINGA architecture. Would require significant infrastructure change. The SPEC_CTX marker approach is the current pattern.

#### 2. Fallback Inference When PM Omitted Specializations (DEFERRED 🔄)
**Suggestion:** Auto-derive specializations from project_context.components
**Reason for deferral:** Good idea but scope creep. Focus on fixing the core loading issue first. Can add inference logic later.

#### 3. Compact "V2" Variant for Subsequent Spawns (DEFERRED 🔄)
**Suggestion:** Shorter specialization block for respawns
**Reason for deferral:** Optimization, not fix. Address after core issue resolved.

---

## IMPLEMENTED Solution: Two-Turn Spawn Sequence

**Note:** The initial "fused atomic action" approach (Skill() and Task() in same message) was **impossible** because Task() needs the specialization block from Skill()'s response, which only arrives in the next turn.

### Why Two-Turn Sequence

1. **Physical constraint** - Task() needs output from Skill(), which arrives in next turn
2. **Cannot be same message** - Skill() response isn't available until message completes
3. **Clear separation** - Turn 1: gather data, Turn 2: use data
4. **Self-check per turn** - Each turn has its own verification

### Implemented Spawn Sequence (Phase Templates)

```markdown
## SPAWN DEVELOPER (ATOMIC SEQUENCE)

**To spawn a developer, you MUST produce this EXACT output sequence.**

### TWO-TURN SPAWN SEQUENCE

**IMPORTANT:** Skill() and Task() CANNOT be in the same message because Task() needs
the specialization_block from Skill()'s response.

**Turn 1 (this message):**
1. Output the [SPEC_CTX_START]...[SPEC_CTX_END] block
2. Call Skill(command: "specialization-loader")
3. END this message (wait for skill response)

**Turn 2 (after skill response):**
1. Read the skill's response
2. Extract content between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]
3. Call Task() with the extracted block prepended to base_prompt

**SELF-CHECK (Turn 1):** Does this message contain [SPEC_CTX_START? Does it contain Skill()?
**SELF-CHECK (Turn 2):** Did I extract the specialization block? Does this message contain Task()?
```

### Key Change from Original Approach

| Aspect | Fused Action (Original) | Two-Turn Sequence (Implemented) |
|--------|------------------------|--------------------------------|
| Message count | 1 message | 2 messages |
| Tool dependency | Impossible (Task needs Skill output) | Resolved (Task in Turn 2 has Skill output) |
| Self-check | One check | Per-turn checks |
| Skip path | Template in same message | Skill must complete before Task possible |

### Additional Fixes in This Commit

1. **Over-broad CONTINUE fallback** - Restricted to explicit status codes only
2. **Incomplete Task() invocations** - Added missing `subagent_type` and `description` parameters
3. **Verification checkpoints** - Updated to reflect two-turn pattern

### Success Criteria (Implemented)

1. **Primary:** Skill() in Turn 1, Task() in Turn 2 (physical separation)
2. **Secondary:** Per-turn self-checks catch missing actions
3. **Tertiary:** Single capsule line confirms status (loaded/failed/disabled)
4. **Explicit status codes** - No guessing from generic phrases

---

## Implementation Complete

**Commits:**
1. `7ce0f46` - fix: rewrite spawn sequences as fused atomic actions (initial, flawed)
2. (this commit) - fix: correct impossible tool dependency with 2-turn sequence

**Files Modified:**
- `templates/orchestrator/phase_simple.md` - Two-turn spawn sequence
- `templates/orchestrator/phase_parallel.md` - Two-turn spawn sequence per group
- `agents/orchestrator.md` - Updated verification checkpoints, fixed CONTINUE fallback

---

## Status

**Status:** Implemented (Two-Turn Spawn Sequence)

**Confidence:** Medium-High - Physical separation (Skill in Turn 1, Task in Turn 2) means Task() literally cannot execute without Skill() completing first. The data dependency is structural, not prompt-based.
