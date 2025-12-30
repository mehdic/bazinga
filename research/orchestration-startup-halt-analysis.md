# Orchestration Startup Halt: Root Cause Analysis

**Date:** 2025-12-30
**Context:** BAZINGA orchestration stops immediately after session creation, requiring user to type "continue"
**Decision:** Implement same-turn ordered tool calls with tool-first gating
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (Gemini skipped)

---

## Problem Statement

When running `/bazinga.orchestrate` on the ARTK project, the orchestration stops immediately after session creation:

### Likely Regression Cause

**Commit `8a42ab9` (Dec 29 11:22)** - "Fix orchestrator stopping after developer spawn"

This commit removed text from Axiom 1:

**Before (working):**
```markdown
1. **I am a COORDINATOR** - I spawn agents, I do not implement. I route messages via `Skill(command: "workflow-router")`.
```

**After (broken):**
```markdown
1. **I am a COORDINATOR** - I spawn agents, I do not implement.
```

**Why this caused the regression:**
- The phrase "I route messages via `Skill(command: "workflow-router")`" gave the model general guidance to keep making Skill calls
- Without this, the model lost "momentum" and is more likely to stop after ANY tool call
- The intent was to fix a conflict with inline routing in phase_simple.md
- **Unintended side effect:** Reduced the model's inclination to continue making Skill calls during initialization

**Fix:** Re-add a general "continue making tool calls" instruction to Axiom 1, but phrase it to avoid conflict with inline routing.

```
⏺ Bash(python3 ... create-session ...)
  ⎿  {
       "success": true,
       "session_id": "bazinga_20251230_095724",
       ...
     }
─────────────────────────────────────────────────────────────────────────────────
>   <-- USER PROMPT APPEARS - Orchestration stopped
```

User had to type "continue" to proceed:

```
> continue
⏺ 🚀 Starting orchestration | Session: bazinga_20251230_095724
⏺ /config-seeder   <-- Now continues to next step
```

This is a **workflow hang** that should not occur. The orchestrator should proceed automatically from session creation to config seeding without user intervention.

---

## Root Cause Analysis

### 1. The Exact Failure Point

The orchestration stops at this transition:

| Step | Action | Status |
|------|--------|--------|
| Step 3 | `Skill(command: "bazinga-db")` - create session | ✅ Completes |
| (implicit) | Output: `🚀 Starting orchestration | Session: [id]` | ✅ Outputs |
| Step 3.5 | `Skill(command: "config-seeder")` | ❌ **Never called** |

### 2. Why the Model Stops

The orchestrator template at lines 1027-1034 says:

```markdown
**Display to user (capsule format on success):**
🚀 Starting orchestration | Session: [session_id]

**AFTER successful session creation: IMMEDIATELY continue to step 3.5 (Seed workflow configs). Do NOT stop.**
```

**The Problem:**

1. The model sees "Display to user" → outputs the capsule text
2. The model treats **outputting text to the user** as a "natural stopping point"
3. The "IMMEDIATELY continue... Do NOT stop" is **just documentation** - not a binding constraint
4. The model interprets the capsule output as "completed a unit of work, awaiting user input"

### 3. The Template Gap

The orchestrator template has extensive "INTENT WITHOUT ACTION" warnings, but they're focused on **agent spawning**:

```markdown
**🔴🔴🔴 CRITICAL BUG PATTERN: INTENT WITHOUT ACTION 🔴🔴🔴**

**THE BUG:** Saying "Now let me spawn..." or "I will spawn..." but NOT calling any tool in the same turn.
```

However, there is **NO similar enforcement** for the **initialization sequence**:
- Steps 1-6 are written as "do A, then do B"
- No tool-call gate to enforce continuation
- No self-check layer for initialization

### 4. Why It Sometimes Works

The model may continue if:
- It hasn't used many tokens in the current turn
- Context is fresh and short
- The model doesn't interpret the output as a "checkpoint"

But these are **non-deterministic factors**. The current template structure doesn't guarantee continuation.

---

## Solution Options

### Option A: Parallel Tool Calls (Recommended)

**Approach:** Call session creation and config-seeder in the same model turn using parallel tool calls.

**Implementation:**
```markdown
**Step 3-3.5: Create session AND seed configs (PARALLEL)**

In a SINGLE message, invoke BOTH skills:
1. Skill(command: "bazinga-db") - create session
2. Skill(command: "config-seeder") - seed configs

ONLY AFTER both complete:
🚀 Starting orchestration | Session: [session_id]
```

**Pros:**
- Eliminates the stopping point between steps
- Uses Claude's native parallel tool calling
- Faster execution (parallel vs sequential)

**Cons:**
- Config-seeder needs session to exist first? (need to verify)
- Changes the semantic structure of the template

### Option B: Add LAYER 0 SELF-CHECK

**Approach:** Add an explicit self-check for initialization that forces continuation.

**Implementation:**
```markdown
**🔴 LAYER 0 SELF-CHECK (INITIALIZATION):**

Before outputting the "🚀 Starting orchestration" capsule, verify:
1. ✅ Session created in database
2. ✅ Config seeder invoked (queued or completed)
3. ✅ Model config loaded
4. ✅ Build baseline checked

**CRITICAL:** The "🚀 Starting orchestration" output MUST NOT appear until ALL initialization steps are complete. This is the GATE.
```

**Pros:**
- Explicit enforcement mechanism
- Consistent with existing self-check patterns
- Clear documentation

**Cons:**
- Relies on model following instructions (same fundamental issue)
- Adds complexity to template

### Option C: Move Status Output to End of Initialization

**Approach:** Don't output "🚀 Starting orchestration..." until after ALL init steps complete.

**Implementation:**
```markdown
**Step 3-7: Complete all initialization (SILENT)**
- Create session
- Seed configs
- Load configs
- Run build baseline
- Load templates

**Step 8: Output initialization complete**
🚀 Initialization complete | Session: [session_id] | Tech stack: [detected] | Ready for PM

**Then IMMEDIATELY proceed to Step 0.5 - Tech Stack Detection.**
```

**Pros:**
- Removes the "checkpoint" that triggers stopping
- User sees one consolidated status message
- Cleaner UX

**Cons:**
- User sees no feedback during init (could take 5-10s)
- Delays error messages if early steps fail

### Option D: Continuation Gate Pattern

**Approach:** Require a tool call to be QUEUED before any text output.

**Implementation:**
```markdown
**CONTINUATION GATE RULE:**

When you are about to output text to the user:
1. FIRST: Queue the NEXT tool call in your response
2. THEN: Output the text
3. The tool call executes after your text output

Example:
[Queue: Skill(command: "config-seeder")]
🚀 Starting orchestration | Session: [session_id]
[Tool executes]
```

**Pros:**
- Enforces continuation by requiring tool calls
- General pattern that can apply everywhere

**Cons:**
- Unusual pattern, may confuse the model
- Adds mental overhead to every output

---

## Critical Analysis

### Pros of Fixing This Issue ✅

1. **Eliminates user intervention requirement** - Orchestration runs end-to-end
2. **Improves reliability** - Works consistently across machines/contexts
3. **Better UX** - User doesn't have to babysit the orchestrator
4. **Reduces confusion** - "Why did it stop?" is a common support question

### Cons/Risks ⚠️

1. **Template complexity** - More rules = more cognitive load on model
2. **Potential regressions** - Changing initialization flow could break other things
3. **Silent failures** - If we batch operations, errors might be harder to diagnose

### Verdict

**Recommended approach:** Same-Turn Ordered Tool Calls + Tool-First Gating (Revised after LLM review)

**Reasoning:**
1. Same-turn, ordered calls prevent stopping between steps (sequential, not parallel)
2. Tool-first gating ensures every user output is followed by a tool call
3. SQLite contention avoided by sequential writes
4. Verification gates catch config seeding failures

---

## Implementation Details

### Change 1: Same-Turn Ordered Tool Calls (Revised)

**Current flow (sequential with stopping point):**
```
Step 3: Skill(bazinga-db) → output to user → STOP
User: continue
Step 3.5: Skill(config-seeder) → ...
```

**New flow (same-turn, ordered, no stopping point):**
```
Step 3:   Skill(bazinga-db) - create session → verify success
Step 3.5: Skill(config-seeder) - seed configs → verify seeding complete
Step 4:   Read(skills_config.json), Read(testing_config.json)
Step 5:   Read(model_selection.json)
Step 6:   Skill(bazinga-db) - save orchestrator state
Step 7:   Read templates (3 files)
↓ ALL ABOVE IN SAME TURN - NO USER OUTPUT BETWEEN STEPS ↓
ONLY NOW: Output capsule "🚀 Starting..." + immediately call next tool (Step 0.5 Scout)
```

**Key difference:** Tool calls are SEQUENTIAL within the same turn, not parallel. This avoids SQLite write contention while ensuring continuation.

### Change 2: Tool-First Gating Rule

**Add to orchestrator.md initialization section:**

```markdown
**🔴 TOOL-FIRST GATING RULE (INITIALIZATION):**

During initialization (Steps 1-7), the following MUST be enforced:
1. NEVER output text to user between tool calls
2. ALL tool calls complete before ANY user-facing output
3. First user output MUST be accompanied by the NEXT tool call in the same turn

**Pattern:**
[Tool calls 1-N complete silently] → [Output capsule] + [Next tool call] (same turn)

**Example:**
✅ CORRECT: Skill(bazinga-db), Skill(config-seeder), Read(configs)... → "🚀 Starting..." + Skill(Scout) (same turn)
❌ WRONG:   Skill(bazinga-db) → "🚀 Starting..." → [STOP] → User types continue → Skill(config-seeder)
```

### Change 3: Config Seeding Verification Gate

**After config-seeder invocation, verify success:**

```markdown
**Step 3.5a: Verify Config Seeding (MANDATORY)**

After Skill(config-seeder) completes:
1. Query: Skill(bazinga-db) → check-configs (verify N transitions, M markers exist)
2. IF verification fails:
   - Retry config-seeder ONCE
   - IF still fails: Output "❌ Config seeding failed | Cannot proceed" and STOP
3. IF verification passes: Continue to Step 4 (silent, no output)
```

### Change 4: Init Self-Check (Updated)

Add to orchestrator.md after Step 7:

```markdown
**🔴 LAYER 0 SELF-CHECK (INITIALIZATION GATE):**

Before ANY output to user, verify ALL are complete:
1. ✅ Session created (bazinga-db returned success)
2. ✅ Configs seeded (config-seeder succeeded AND verified)
3. ✅ Configs loaded (Read tools completed)
4. ✅ Model config parsed (MODEL_CONFIG populated)
5. ✅ State saved to database (bazinga-db save-state succeeded)
6. ✅ Templates loaded (3 templates verified)

**Only after all 6 checks pass:** Output init capsule AND call next tool (Step 0.5) in same turn
```

### Change 5: Make Config-Seeder Idempotent (New)

**Modify config-seeder skill to be safe for re-runs:**

```markdown
**Config Seeder Idempotency:**

Before seeding:
1. Check if configs already seeded (query DB for seeded_version)
2. IF seeded_version matches current version: Return immediately (O(1))
3. IF not seeded OR version mismatch: Seed configs, update seeded_version

This enables:
- Fast re-runs on resume (no redundant writes)
- Safe partial initialization recovery
```

---

## Comparison to Alternatives

### Alternative 1: Keep Current Template, Add More "Do NOT stop" Instructions

**Why not:** This is the same approach that's already failing. Text-based instructions don't reliably enforce continuation.

### Alternative 2: Use a Monitor/Watchdog

**Why not:** Adds complexity without addressing root cause. Would require external process to detect stalls and inject "continue" commands.

### Alternative 3: Split Orchestrator into Phases

**Why not:** Over-engineering. The issue is localized to the init sequence, not a fundamental architecture problem.

---

## Decision Rationale

The recommended fix (same-turn ordered calls + tool-first gating) addresses the root cause:

1. **Same-turn ordered calls** - Model executes all init steps sequentially in one turn, no stopping points
2. **Tool-first gating** - Every user output is followed by a tool call, preventing the "checkpoint" stop
3. **Verification gates** - Config seeding success is verified deterministically
4. **Idempotent config-seeder** - Safe for re-runs on resume or partial initialization

This approach is:
- **Structural** - Changes the flow, not just documentation
- **Sequential** - Avoids SQLite write contention from parallel writers
- **Deterministic** - Verification gates catch failures, no silent continuation on partial state
- **Robust** - Init_state tracking enables recovery from partial initialization

---

## Lessons Learned

1. **Text instructions are not constraints** - "Do NOT stop" doesn't prevent stopping
2. **User-facing output triggers checkpoints** - Model interprets output as "await feedback"
3. **Parallel tool calls enforce atomicity** - Bundling operations prevents interruption
4. **Self-checks are documentation, not enforcement** - They help but don't guarantee
5. **Test on fresh contexts** - Init flows may work on "warm" contexts but fail on fresh ones

---

## Implementation Checklist

- [ ] Add TOOL-FIRST GATING RULE to initialization section of orchestrator.md
- [ ] Restructure Steps 3-7 to execute in same turn without user output between them
- [ ] Add Step 3.5a: Config seeding verification gate (check N transitions exist)
- [ ] Add LAYER 0 SELF-CHECK after Step 7 (verify all 6 conditions)
- [ ] Ensure first user output is accompanied by next tool call (Step 0.5 Scout) in same turn
- [ ] Make config-seeder idempotent (check seeded_version before writing)
- [ ] Test on fresh context (new conversation, new project)
- [ ] Document changes in CHANGELOG.md
- [ ] (Long-term) Consider init-orchestration macro skill for atomic initialization

---

## Multi-LLM Review Integration

### Critical Issues Identified by OpenAI

1. **"Parallel tool calls" is a misnomer** - Many tool runners execute sequentially within a single turn. The fix is "same-turn, ordered calls," not truly parallel execution.

2. **SQLite contention risk** - Both bazinga-db and config-seeder write to the same SQLite database. Concurrent writes can cause locks/races. Sequential, ordered execution is safer.

3. **"Queue tool call after text" is not reliable** - Tool calls must be invoked within the same assistant turn; there's no guarantee a queued call executes after free-form text.

4. **Missing verification gate** - No deterministic check that config seeding completed successfully.

5. **Delayed error surfacing** - Moving status to end hides early failures, contradicting "surface errors on failure" principle.

### Incorporated Feedback

1. **Changed approach from "parallel" to "same-turn, ordered"**
   - Call tools sequentially in the same turn without text output between them
   - Ensures config-seeder runs immediately after session creation
   - Avoids SQLite write contention

2. **Added tool-first gating rule**
   - Never emit user-facing text without an immediately following tool call in the same turn
   - Extends "INTENT WITHOUT ACTION" pattern to initialization sequence

3. **Added config seeding verification gate**
   - After config-seeder, query DB to verify transitions and markers exist
   - Fail fast with error capsule if seeding incomplete

4. **Added init_state tracking in DB** (new requirement)
   - Track flags: session_created, config_seeded, configs_loaded, state_saved, templates_loaded
   - Enables resume path to detect and complete partial initialization

5. **Make config-seeder idempotent**
   - Check if configs already seeded before running
   - Add "seeded_version" stamp for fast O(1) re-runs

6. **Long-term: init-orchestration macro skill**
   - Single skill that atomically executes steps 3-7
   - Removes all LLM sequencing risk
   - Returns structured result, orchestrator prints capsule

### Rejected Suggestions (With Reasoning)

1. **"Add a minimal integration test"** - Deferred to separate PR; not needed for the immediate fix.

2. **"Emit progress capsules with following tool calls"** - Adds complexity. Prefer single consolidated output after all init steps.

### Revised Implementation Approach

**Before (original proposal - REJECTED):**
```
"Parallel" tool calls: [Skill(bazinga-db), Skill(config-seeder)] simultaneously
```

**After (revised approach - APPROVED):**
```
Same-turn, ordered calls:
1. Skill(bazinga-db) - create session → verify success
2. Skill(config-seeder) - seed configs → verify success
3. Read(configs) - load configs
4. Skill(bazinga-db) - save state
5. ONLY THEN: Output capsule + next tool call in same turn
```

**Key principle:** Each user-facing capsule must be followed by a concrete Skill/Task call in the same assistant turn.

---

## References

- `agents/orchestrator.md` - Lines 960-1060 (Path B: CREATE NEW SESSION)
- `agents/orchestrator.md` - Lines 216-228 (INTENT WITHOUT ACTION pattern)
- `.claude/commands/bazinga.orchestrate.md` - Generated slash command (reflects orchestrator.md)
- User log from ARTK project showing the exact failure
- OpenAI GPT-5 review (2025-12-30) - Critical issues and alternative approaches
