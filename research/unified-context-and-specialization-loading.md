# Unified Context and Specialization Loading Analysis

**Date:** 2025-12-14
**Context:** Integration test revealed context-assembler was skipped while specialization-loader was invoked
**Decision:** Unified Pre-Spawn Block with Two-Turn Enforcement
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

During the integration test, the orchestrator:
- ✅ Invoked `specialization-loader` for Developer, QA Expert, and Tech Lead
- ❌ Did NOT invoke `context-assembler` for any agent

This resulted in:
- Agents received **technology-specific identity blocks** (specializations)
- Agents did **NOT receive prior reasoning context** (handoff context)
- The reasoning chain (Developer→QA→TL) was broken

### Root Cause Analysis

The orchestrator templates (`phase_simple.md`, `phase_parallel.md`) specify both skills, but in **separate sections**:

```markdown
## Section 1: Context Assembly (BEFORE building prompt)
Output context for context-assembler:
...
Then invoke: Skill(command: "context-assembler")

## Section 2: Spawn Agent (fused)
Spawn QA (fused): Output [SPEC_CTX_START...]... → Skill(command: "specialization-loader")
```

**Problem:** The two steps are visually and logically separate, making it easy to:
1. Skip the Context Assembly section entirely
2. Jump directly to the Spawn section (which has the Task tool call)

The current workflow has **two decision points** where each skill can be missed independently.

---

## Solution Options

### Option A: Sequential Two-Skill Pattern (Current - Improved Documentation)

**Approach:** Keep both skills separate but add explicit checkpoints and reminders.

**Changes:**
1. Add `🔴 MANDATORY` markers to Context Assembly sections
2. Add self-check: "Before spawning, verify: Did you invoke context-assembler?"
3. Add visual separator between context assembly and spawn

**Template Change (phase_simple.md):**
```markdown
### 🔴 MANDATORY: Context Assembly (BEFORE building prompt)

Output context for context-assembler:
...
Then invoke: `Skill(command: "context-assembler")`

**CHECKPOINT:** Did context-assembler return? If not, do NOT proceed to spawn.

---

### Spawn QA Expert

**Spawn QA (fused):** Output [SPEC_CTX_START...]...
```

**Pros:**
- Minimal change to existing templates
- Each skill remains independently testable
- Flexible ordering if needed

**Cons:**
- Still two separate steps to remember
- Relies on orchestrator following instructions correctly
- Doesn't solve the fundamental "easy to skip" problem

**Risk:** MEDIUM - Documentation can still be ignored

---

### Option B: Unified Pre-Spawn Block Pattern

**Approach:** Create a single "Pre-Spawn" block that explicitly lists BOTH skills as mandatory before ANY agent spawn.

**Changes:**
1. Define a "Pre-Spawn Checklist" that runs before every Task tool call
2. Both skills are invoked in sequence within the same logical block
3. Outputs from both are combined into the agent prompt

**Template Change (phase_simple.md):**
```markdown
### Step 2A.4: QA Expert Spawn

**🔴 PRE-SPAWN CHECKLIST (MANDATORY for every agent spawn):**

**Step A: Context Assembly**
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: qa_expert
- Model: sonnet
- Current Tokens: {estimated_token_usage}
- Iteration: 0
```
Then invoke: `Skill(command: "context-assembler")`
→ Save output as `{CONTEXT_BLOCK}`

**Step B: Specialization Loading**
```
[SPEC_CTX_START group={group_id} agent=qa_expert]
Session ID: {session_id}
...
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Save output as `{SPEC_BLOCK}`

**Step C: Build Prompt**
```
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + {AGENT_DEFINITION} + {TASK_DETAILS}
```

**Step D: Spawn Agent**
```
Task(subagent_type="general-purpose", model=sonnet, prompt={prompt})
```

**SELF-CHECK:** Did Steps A, B, C, D all complete? If ANY step missing, STOP.
```

**Pros:**
- Both skills explicitly listed in ONE block
- Clear sequential dependency (A→B→C→D)
- Self-check validates all steps
- Harder to accidentally skip one skill

**Cons:**
- More verbose templates
- Slightly longer execution time (two skill invocations per spawn)
- May feel repetitive across many spawn sections

**Risk:** LOW - Both skills in same block makes skipping harder

---

### Option C: Fused Skill Pattern (New Skill)

**Approach:** Create a new `pre-spawn-assembler` skill that internally calls BOTH context-assembler and specialization-loader.

**New Skill:** `.claude/skills/pre-spawn-assembler/SKILL.md`

**Invocation:**
```
Pre-spawn assembly for agent:
- Session: {session_id}
- Group: {group_id}
- Agent: qa_expert
- Model: sonnet
...
Then invoke: Skill(command: "pre-spawn-assembler")
```

**Skill Implementation:**
1. Call context-assembler logic internally
2. Call specialization-loader logic internally
3. Combine outputs into unified markdown block
4. Return single block for prompt inclusion

**Pros:**
- Single skill invocation (can't forget half)
- Unified output format
- Atomic operation - either both happen or neither
- Cleaner orchestrator templates

**Cons:**
- New skill to create and maintain
- Coupling between two previously independent skills
- More complex skill logic
- May be harder to debug issues in either component

**Risk:** MEDIUM - New complexity, but eliminates the "forgot one" problem

---

### Option D: Prompt Building Template Pattern

**Approach:** Create a `prompt_building_sequence.md` template that orchestrator MUST follow for every spawn.

**New Template:** `templates/orchestrator/prompt_building_sequence.md`

**Content:**
```markdown
# Agent Prompt Building Sequence

**This sequence MUST be followed for EVERY agent spawn.**

## Phase 1: Context Assembly
1. Invoke `Skill(command: "context-assembler")` with agent details
2. Capture output as `CONTEXT_BLOCK`
3. If empty or error, log warning but continue

## Phase 2: Specialization Loading
1. Output `[SPEC_CTX_START...]...[SPEC_CTX_END]` block
2. Invoke `Skill(command: "specialization-loader")`
3. Capture output as `SPEC_BLOCK`

## Phase 3: Prompt Composition
1. Read agent definition: `agents/{agent_type}.md`
2. Compose prompt:
   ```
   {CONTEXT_BLOCK}

   {SPEC_BLOCK}

   {AGENT_DEFINITION}

   ## Your Task
   {TASK_DETAILS}
   ```

## Phase 4: Spawn
1. Call `Task(subagent_type="general-purpose", model={model}, prompt={composed_prompt})`

## Validation
- [ ] Context assembly invoked
- [ ] Specialization loaded
- [ ] Agent definition included
- [ ] Task details included
```

**Template Change (phase_simple.md):**
```markdown
### Step 2A.4: QA Expert Spawn

**Follow prompt building sequence:** `templates/orchestrator/prompt_building_sequence.md`

Agent: qa_expert
Model: sonnet
Session: {session_id}
Group: {group_id}
Task Details: {qa_task_details}
```

**Pros:**
- Single source of truth for prompt building
- All spawn sections reference same sequence
- Changes to sequence automatically apply everywhere
- Clear checklist format

**Cons:**
- Requires orchestrator to "follow" a referenced template
- Indirect instruction (read file → follow steps)
- May be confusing if orchestrator doesn't read the template

**Risk:** MEDIUM - Depends on orchestrator following references correctly

---

## Recommendation

**Recommended: Option B (Unified Pre-Spawn Block Pattern)**

**Rationale:**

1. **Explicit is better than implicit** - Both skills listed in same block, visible together
2. **Self-check validates** - STOP instruction if any step missing
3. **Minimal new code** - Just template reorganization, no new skills
4. **Proven pattern** - Similar to the existing "fused spawn" pattern but expanded
5. **Debugging clarity** - Each step is labeled (A, B, C, D) for easy tracking

**Why not other options:**

- **Option A:** Documentation alone won't fix the problem - I had documentation and still skipped it
- **Option C:** New skill adds complexity and coupling - overkill for this problem
- **Option D:** Indirect reference to another file is fragile - orchestrator may not read it

---

## Implementation Plan

### Step 1: Update phase_simple.md

For EACH agent spawn section (Developer, QA, TL, SSE, Investigator):

**Before (current):**
```markdown
### Context Assembly (BEFORE building prompt)
[context-assembler instructions]

### Spawn QA (fused)
[specialization-loader + Task]
```

**After (unified):**
```markdown
### Step 2A.4: QA Expert Spawn

**🔴 PRE-SPAWN CHECKLIST (MANDATORY):**

**A. Context Assembly:**
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: qa_expert
...
Then invoke: `Skill(command: "context-assembler")`
→ Output saved as `{CONTEXT_BLOCK}`

**B. Specialization Loading:**
[SPEC_CTX_START group={group_id} agent=qa_expert]
...
[SPEC_CTX_END]
Then invoke: `Skill(command: "specialization-loader")`
→ Output saved as `{SPEC_BLOCK}`

**C. Compose Prompt:**
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt

**D. Spawn:**
Task(subagent_type="general-purpose", model=sonnet, prompt={prompt})

**✅ SELF-CHECK:** Steps A, B, C, D all complete?
```

### Step 2: Update phase_parallel.md

Same pattern for parallel mode spawns.

### Step 3: Update orchestrator.md

Add to the "Skills Invoked" section:

```markdown
**BOTH skills MUST be invoked before EVERY agent spawn:**
1. `context-assembler` - Builds prior reasoning + context packages
2. `specialization-loader` - Builds technology-specific identity

**Neither skill is optional. Both must complete before Task() is called.**
```

### Step 4: Rebuild slash command

```bash
./scripts/build-slash-commands.sh
```

---

## Prompt Composition Order

The final agent prompt should include blocks in this order:

```markdown
## Context for {agent_type}
{CONTEXT_BLOCK from context-assembler}

## SPECIALIZATION GUIDANCE (Advisory)
{SPEC_BLOCK from specialization-loader}

## Agent Definition
{Content from agents/{agent_type}.md}

## Your Task
{Task-specific details}
```

**Rationale for order:**
1. **Context first** - Prior reasoning sets the stage for what happened before
2. **Specialization second** - Technology-specific patterns to follow
3. **Agent definition third** - Role and workflow rules
4. **Task last** - Specific requirements for this spawn

---

## Verification Checklist

After implementation:

- [ ] phase_simple.md updated with unified pre-spawn blocks
- [ ] phase_parallel.md updated with unified pre-spawn blocks
- [ ] orchestrator.md updated with dual-skill requirement
- [ ] Slash command rebuilt
- [ ] Integration test re-run shows BOTH skills invoked
- [ ] QA Expert receives Developer reasoning
- [ ] Tech Lead receives Developer + QA reasoning

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Orchestrator still skips steps | Medium | High | Self-check instructions + validation |
| Template becomes too verbose | Low | Low | Accept minor verbosity for clarity |
| Two skill invocations slow spawn | Low | Low | Skills are fast (<500ms each) |
| Context-assembler fails silently | Low | Medium | Log warning, continue with specialization only |

---

## Alternative Considered: Automatic Skill Chaining

**Idea:** Have specialization-loader automatically invoke context-assembler first.

**Rejected because:**
1. Violates single-responsibility principle
2. Makes testing harder (can't test skills independently)
3. Hidden behavior is harder to debug
4. Context-assembler may legitimately be skipped in some scenarios

---

## Multi-LLM Review Integration

### Critical Issues Identified by OpenAI

1. **Duplicate context injection risk** - Templates have BOTH context-assembler AND manual DB queries
2. **Prompt bloat and token overrun** - Full agent definitions + both blocks exceeds limits
3. **Two-turn sequencing not explicit** - specialization-loader requires 2 turns; plan didn't spell this out
4. **No runtime guard** - Nothing prevents skipping context-assembler
5. **QA/testing mode gating missing** - Pre-spawn should respect testing_mode

### Incorporated Feedback

**1. Remove duplicate context injection (ACCEPTED)**
- When context-assembler is enabled, DELETE manual "bazinga-db get context packages" queries
- Keep manual queries ONLY as fallback when `enable_context_assembler=false`
- This eliminates confusion and double consumption tracking

**2. Two-turn enforcement (ACCEPTED)**
- Turn 1: Invoke context-assembler → Invoke specialization-loader
- Turn 2: Compose prompt with BOTH outputs → Call Task()
- Add explicit self-check: "If SPEC_BLOCK missing, do NOT call Task()"

**3. Token budget caps per role (ACCEPTED)**
- Combined preface (spec + context) caps:
  - Developer/Haiku: ≤ 900 tokens
  - QA/TL/SSE/Sonnet: ≤ 1,200 tokens
  - Opus agents: ≤ 1,800 tokens
- Ratio: Spec block (60%), Context (40%)
- When over cap: drop low-priority context items first

**4. Assembler verification gate (ACCEPTED)**
- After context-assembler, verify it returned metadata (zone, package_count)
- If empty AND assembler enabled: fallback to DB query, log fallback used
- Log to skill_outputs for audit trail

**5. Minimal agent definition (ACCEPTED)**
- Replace full `{AGENT_DEFINITION}` with compact identity line
- Example: "You are the QA Expert. Focus: comprehensive testing, challenge levels."
- Full agent definitions are reference docs, not inlined in prompts

**6. QA/testing mode gating (ACCEPTED)**
- Wrap QA pre-spawn block with `testing_mode==full` guard
- In minimal/disabled modes: skip QA-specific augmentation

**7. Runtime guard (ACCEPTED)**
- Before Task(): Assert "Did context-assembler AND specialization-loader complete?"
- If not: Re-run missing skill(s), then proceed
- Prevents silent skips

### Rejected Suggestions (With Reasoning)

**1. Make specialization optional for Investigator (REJECTED)**
- Reasoning: Investigator benefits from stack-specific debugging patterns
- The existing compatibility filtering already handles this
- Keep specialization universal; templates filter to relevant content

**2. Caching assembler results in parallel mode (DEFERRED)**
- Reasoning: Adds complexity; current implementation is fast enough (<200ms)
- Can revisit if performance becomes an issue
- DB retry/backoff already handles lock contention

### Revised Implementation Plan

**Phase 1: Template Updates**

Update `phase_simple.md` and `phase_parallel.md` with:

```markdown
### Step X: {Agent} Spawn (TWO-TURN SEQUENCE)

**🔴 TURN 1: Skill Invocations**

**A. Context Assembly** (IF enable_context_assembler=true):
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: {agent_type}
- Model: {model}
- Current Tokens: {estimated_token_usage}
- Iteration: {iteration_count}
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`
→ Verify: Did it return zone/packages? If empty, use DB fallback.

**B. Specialization Loading**:
```
[SPEC_CTX_START group={group_id} agent={agent_type}]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: {agent_type}
Model: {model}
Specialization Paths: {paths_from_pm}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked (or explicitly disabled)?
- [ ] Specialization-loader invoked?
- [ ] Both returned valid blocks?

END TURN 1 (wait for skill responses)

---

**🔴 TURN 2: Compose & Spawn**

**C. Compose Prompt** (token-conscious):
```
prompt =
  {CONTEXT_BLOCK}  // Prior reasoning + packages (~400 tokens max)
  +
  {SPEC_BLOCK}     // Tech identity (~600 tokens max)
  +
  "You are the {role}. Your workflow: [critical bullets only]"
  +
  {TASK_DETAILS}
```

**D. Spawn Agent**:
```
Task(subagent_type="general-purpose", model={model}, prompt={prompt})
```

**✅ TURN 2 SELF-CHECK:**
- [ ] CONTEXT_BLOCK present (or fallback used)?
- [ ] SPEC_BLOCK present?
- [ ] Task() called?
```

**Phase 2: Remove Duplicate Context Queries**

Delete from templates (when context-assembler enabled):
- "bazinga-db get context packages" sections in agent base prompts
- "Previous Agent Reasoning" manual queries
- "mark-context-consumed" instructions (assembler handles this)

Keep ONLY as explicit fallback when `enable_context_assembler=false`.

**Phase 3: Add Runtime Guard to Orchestrator**

Add to `agents/orchestrator.md`:

```markdown
### 🔴 PRE-TASK VALIDATION (MANDATORY)

Before ANY `Task()` call, verify:

1. **Specialization-loader invoked?** Check for `[SPECIALIZATION_BLOCK_START]` in this turn
2. **Context-assembler invoked?** Check for `## Context for {agent}` in this turn
   - OR: `enable_context_assembler=false` in skills_config.json

**If either missing:** STOP. Re-invoke the missing skill(s). Do NOT call Task().

This prevents the "intent without action" bug where skills are mentioned but not actually invoked.
```

---

## Updated Prompt Composition Order

```markdown
## Context for {agent_type}
{From context-assembler: prior reasoning + packages, ~400 tokens}

## SPECIALIZATION GUIDANCE (Advisory)
{From specialization-loader: tech identity + patterns, ~600 tokens}

## Your Role
You are the {role}. Your workflow:
- [Critical bullet 1]
- [Critical bullet 2]
- [Critical bullet 3]

## Your Task
{Task-specific details}
```

**Total preface target:** ~1000 tokens (leaves room for task details and responses)

---

## References

- `.claude/skills/context-assembler/SKILL.md` - Context assembly logic
- `.claude/skills/specialization-loader/SKILL.md` - Specialization building logic
- `templates/orchestrator/phase_simple.md` - Simple mode workflow
- `templates/orchestrator/phase_parallel.md` - Parallel mode workflow
- `research/reasoning-auto-enable-analysis.md` - Reasoning handoff implementation
- `tmp/ultrathink-reviews/combined-review.md` - OpenAI review feedback
