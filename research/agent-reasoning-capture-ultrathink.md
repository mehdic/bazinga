# Agent Reasoning Capture Strategy

**Date:** 2025-12-08
**Context:** Need to capture subagent reasoning/thinking for debugging and audit trails
**Decision:** Implement prompt-based reasoning documentation with database storage
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

Claude Code subagents operate with isolated context windows. Their internal "thinking" blocks (extended thinking) are:
1. **Not visible** to the parent orchestrator
2. **Not streamed** in real-time
3. **Not persisted** after agent completion
4. **Not queryable** for debugging

This creates challenges for:
- **Debugging** - When agents fail, we can't see their reasoning
- **Audit trails** - No record of why decisions were made
- **Learning** - Can't improve prompts without understanding failures
- **Transparency** - Users can't understand agent behavior

### Current Situation

| Capability | Available? |
|------------|------------|
| See agent tool calls | ✅ Yes |
| See agent text output | ✅ Yes |
| See agent thinking blocks | ❌ No |
| Query agent reasoning | ❌ No |
| Persist reasoning across sessions | ❌ No |

### Why This Matters for BAZINGA

In BAZINGA orchestration:
- **4 parallel developers** may each make different architectural decisions
- **QA failures** need root cause analysis
- **Tech Lead reviews** benefit from understanding developer reasoning
- **PM decisions** should be traceable for audit
- **Escalation paths** (Developer → SSE) lose context on handoff

---

## Proposed Solution

### Core Approach: Prompt-Injected Reasoning Documentation

Instead of trying to capture internal thinking blocks (not possible), we instruct agents to **explicitly document their reasoning** as structured output saved to the database.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Prompt (Modified)                   │
│                                                              │
│  ## Reasoning Documentation Requirement                      │
│  Before implementing, document your analysis:                │
│  1. Save reasoning to database via bazinga-db skill          │
│  2. Include: understanding, approach, risks, decisions       │
│  3. Update when approach changes significantly               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    bazinga-db Skill                          │
│                                                              │
│  NEW COMMAND: save-reasoning                                 │
│  - session_id, group_id, agent_type, agent_id               │
│  - reasoning_phase: understanding|approach|decisions|risks  │
│  - reasoning_text: structured markdown                       │
│  - timestamp: auto-generated                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│                                                              │
│  NEW TABLE: agent_reasoning                                  │
│  - Indexed by session_id, group_id, agent_type              │
│  - Queryable by orchestrator, PM, Tech Lead                 │
│  - Persists across compactions                               │
│  - Provides audit trail                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### 1. New Database Table: `agent_reasoning`

```sql
CREATE TABLE agent_reasoning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT,  -- NULL for orchestrator/PM global reasoning
    agent_type TEXT NOT NULL,  -- developer, qa_expert, tech_lead, pm, etc.
    agent_id TEXT,  -- specific instance (e.g., developer_1)
    iteration INTEGER DEFAULT 1,
    reasoning_phase TEXT NOT NULL CHECK(reasoning_phase IN (
        'understanding',  -- Initial task comprehension
        'approach',       -- Planned solution strategy
        'decisions',      -- Key architectural/implementation decisions
        'risks',          -- Identified risks and mitigations
        'blockers',       -- What's blocking progress
        'pivot',          -- Why approach changed mid-task
        'completion'      -- Final summary of what was done and why
    )),
    reasoning_text TEXT NOT NULL,
    confidence_level TEXT CHECK(confidence_level IN ('high', 'medium', 'low')),
    references TEXT,  -- JSON array of file paths, context packages consulted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX idx_reasoning_session ON agent_reasoning(session_id, created_at DESC);
CREATE INDEX idx_reasoning_group ON agent_reasoning(session_id, group_id, agent_type);
CREATE INDEX idx_reasoning_phase ON agent_reasoning(reasoning_phase);
```

### 2. New bazinga-db Commands

```bash
# Save reasoning
python3 bazinga_db.py save-reasoning \
  "<session_id>" "<group_id>" "<agent_type>" "<reasoning_phase>" "<reasoning_text>" \
  [--agent_id X] [--iteration N] [--confidence high|medium|low] [--references '["file1","file2"]']

# Get reasoning for a group (for handoffs)
python3 bazinga_db.py get-reasoning \
  "<session_id>" "<group_id>" [--agent_type X] [--phase Y] [--limit N]

# Get reasoning timeline (for debugging)
python3 bazinga_db.py reasoning-timeline \
  "<session_id>" [--group_id X] [--format markdown|json]
```

### 3. Agent Prompt Injection

Add to **all agent prompts** (developer, qa_expert, tech_lead, pm, investigator, sse):

```markdown
## 🧠 Reasoning Documentation Requirement

**CRITICAL**: Document your reasoning to enable debugging and audit trails.

### When to Save Reasoning

| Phase | When | What to Document |
|-------|------|-----------------|
| understanding | Start of task | Your interpretation of requirements, what's unclear |
| approach | After analysis | Your planned solution, why this approach |
| decisions | During impl | Key choices made, alternatives considered |
| risks | If identified | What could go wrong, mitigations |
| blockers | If stuck | What's blocking, what you tried |
| pivot | If changing | Why original approach didn't work |
| completion | End of task | Summary of what was done and key learnings |

### How to Save Reasoning

```bash
# Via bazinga-db skill
Skill(command: "bazinga-db")

# Then execute:
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "{AGENT_TYPE}" "approach" \
  "## Approach

### Chosen Strategy
Implementing JWT auth using PyJWT library with HS256.

### Why This Approach
1. Project already uses Flask - PyJWT integrates cleanly
2. HS256 is sufficient for internal API (no third-party verification needed)
3. Follows existing patterns in auth_utils.py

### Alternatives Considered
- RS256: Overkill for internal API, requires key management
- Session-based: Doesn't align with stateless API design
- OAuth2: Too complex for MVP, consider for v2

### Dependencies
- PyJWT >= 2.0.0
- cryptography (for future RS256 support)" \
  --confidence high \
  --references '["src/utils/auth.py", "requirements.txt"]'
```

### Minimum Reasoning Requirements

**At minimum, every agent MUST save:**
1. `understanding` phase at task start
2. `completion` phase at task end

**Additional phases are STRONGLY ENCOURAGED when:**
- Making non-obvious decisions
- Encountering unexpected behavior
- Changing approach mid-task
- Identifying risks

### Why This Matters

Your reasoning is:
- **Queryable** by PM/Tech Lead for reviews
- **Passed** to next agent in workflow (handoffs)
- **Preserved** across context compactions
- **Available** for debugging failures
- **Used** by Investigator for root cause analysis
```

### 4. Integration Points

#### A. Orchestrator Spawn Enhancement

When spawning agents, orchestrator can query previous reasoning:

```python
# Get reasoning from previous agents for context
previous_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    limit=5
)

# Include in agent spawn prompt
spawn_prompt += f"""
## Previous Agent Reasoning (for context)
{format_reasoning(previous_reasoning)}
"""
```

#### B. Tech Lead Review Enhancement

Tech Lead can review developer reasoning before code review:

```python
# Tech Lead queries developer reasoning
dev_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    agent_type='developer'
)

# Inform code review with reasoning context
review_prompt += f"""
## Developer's Documented Reasoning
{format_reasoning(dev_reasoning)}

Consider: Does the implementation match the stated reasoning?
Are the decisions justified?
"""
```

#### C. Investigator Deep-Dive

Investigator gets full reasoning timeline:

```python
# Get complete reasoning timeline for debugging
timeline = db.reasoning_timeline(
    session_id=SESSION_ID,
    group_id=GROUP_ID,
    format='markdown'
)

investigation_prompt += f"""
## Complete Reasoning Timeline
{timeline}

Analyze: Where did reasoning diverge from implementation?
What assumptions proved incorrect?
"""
```

#### D. PM Audit Trail

PM can query reasoning for BAZINGA validation:

```python
# Get all completion reasoning for final review
completion_reasoning = db.get_reasoning(
    session_id=SESSION_ID,
    phase='completion'
)

# Verify against success criteria
for criteria in success_criteria:
    matching_reasoning = find_related_reasoning(criteria, completion_reasoning)
    # Validate implementation matches reasoning
```

---

## Implementation Plan

### Phase 1: Database Schema (30 min)
1. Add `agent_reasoning` table to `init_db.py`
2. Add schema version migration
3. Update `references/schema.md`

### Phase 2: bazinga-db Commands (1 hour)
1. Add `save_reasoning()` method to BazingaDB class
2. Add `get_reasoning()` method with filters
3. Add `reasoning_timeline()` method
4. Add CLI commands to main()
5. Update SKILL.md with new commands

### Phase 3: Agent Prompt Updates (2 hours)
1. Update `agents/developer.md` with reasoning section
2. Update `agents/senior_software_engineer.md`
3. Update `agents/qa_expert.md`
4. Update `agents/techlead.md`
5. Update `agents/project_manager.md`
6. Update `agents/investigator.md`
7. Update `agents/requirements_engineer.md`

### Phase 4: Integration (1 hour)
1. Update orchestrator to query reasoning for spawns
2. Update Tech Lead to review reasoning
3. Update Investigator to use reasoning timeline

### Phase 5: Testing (1 hour)
1. Test save/get reasoning commands
2. Test reasoning in agent workflow
3. Verify persistence across compactions

---

## Critical Analysis

### Pros ✅

1. **No System Changes Required**
   - Uses existing bazinga-db infrastructure
   - No hooks, no special Claude Code features needed
   - Works today with current architecture

2. **Structured & Queryable**
   - SQLite with indexes = fast queries
   - Filterable by phase, agent, group
   - Supports timeline reconstruction

3. **Persists Across Compactions**
   - Database survives context compaction
   - Reasoning available for entire session lifetime
   - Can query historical reasoning

4. **Enables New Capabilities**
   - Tech Lead can review reasoning before code
   - Investigator has full context for debugging
   - PM has audit trail for decisions
   - Better handoffs between agents

5. **Minimal Token Overhead**
   - Reasoning is saved once, not repeated
   - Query only relevant reasoning for spawns
   - Much cheaper than repeating context

### Cons ⚠️

1. **Relies on Agent Compliance**
   - Agents must follow prompt instructions
   - Can't force reasoning documentation
   - Quality varies by agent attention

2. **Token Cost for Writing**
   - Each reasoning save uses tokens
   - Verbose reasoning = more cost
   - Need balance between detail and efficiency

3. **Not Real-Time**
   - Reasoning saved at discrete points
   - Can't see "thinking in progress"
   - Post-hoc, not streaming

4. **Potential for Noise**
   - Low-quality reasoning clutters database
   - Need clear guidelines on what's useful
   - May need cleanup mechanisms

5. **Doesn't Capture Implicit Reasoning**
   - Only what agents explicitly document
   - Internal thinking blocks still hidden
   - May miss unconscious assumptions

### Verdict

**RECOMMENDED** - This approach provides 80% of the value with 20% of the complexity. The key insight is that **explicit reasoning documentation is more useful than captured thinking blocks** because:

1. It's structured and queryable
2. It forces agents to articulate decisions
3. It's designed for human consumption
4. It persists and survives compactions

The main risk is agent compliance, but this can be mitigated with:
- Clear prompt instructions
- PM validation of reasoning completeness
- Tech Lead review of reasoning quality

---

## Comparison to Alternatives

### Alternative 1: SubagentStop Hook + Transcript Parsing

**Approach:** Parse JSONL transcript when agent stops

**Pros:**
- Captures all tool calls
- No agent prompt changes needed

**Cons:**
- Thinking blocks stripped from transcript
- Complex parsing required
- Only captures after completion
- No structured phases

**Verdict:** Inferior - transcript doesn't include thinking, and parsing is fragile.

### Alternative 2: State File Decoupling

**Approach:** SubagentStop saves to file, UserPromptSubmit injects

**Pros:**
- Works with current hooks

**Cons:**
- Complex hook setup
- File-based (not queryable)
- Timing issues
- Doesn't capture reasoning structure

**Verdict:** Inferior - too complex, not queryable, not structured.

### Alternative 3: Git-Based Persistence

**Approach:** PostToolUse commits reasoning files

**Pros:**
- Version controlled
- Diff-able

**Cons:**
- Pollutes git history
- Not queryable
- Overhead per save
- Merge conflicts possible

**Verdict:** Inferior - wrong tool for the job.

### Alternative 4: External Observability System

**Approach:** Real-time hook monitoring (like disler/claude-code-hooks-multi-agent-observability)

**Pros:**
- Real-time visibility
- Dashboard UI

**Cons:**
- Doesn't capture thinking
- Complex setup
- External dependency
- Still no structured reasoning

**Verdict:** Complementary - good for monitoring, but doesn't solve reasoning capture.

### Winner: Prompt-Injected Database Storage

Our proposed approach combines:
- Simplicity of prompt-based instructions
- Structure of database storage
- Queryability of SQL
- Integration with existing bazinga-db skill

---

## Open Questions

1. **Reasoning Length Limits?**
   - Should we cap reasoning_text at N characters?
   - Pro: Prevents token bloat
   - Con: May truncate important context
   - **Recommendation:** Soft limit of 2000 chars, warn if exceeded

2. **Automatic vs Manual Phases?**
   - Should some phases be auto-triggered?
   - E.g., auto-save "completion" when agent reports READY_FOR_QA
   - **Recommendation:** Start manual, add automation if adoption is low

3. **Reasoning Review in Tech Lead?**
   - Should Tech Lead explicitly review reasoning quality?
   - Could add "Reasoning Quality" to review criteria
   - **Recommendation:** Yes, add as optional review dimension

4. **Retention Policy?**
   - Keep reasoning forever? Archive after session complete?
   - **Recommendation:** Keep for 30 days, then archive to cold storage

5. **Privacy/Security?**
   - Reasoning may contain sensitive implementation details
   - **Recommendation:** Same access controls as code

---

## Success Metrics

1. **Adoption Rate**
   - Target: 80% of agent spawns include at least `understanding` + `completion` phases
   - Measure: `SELECT COUNT(DISTINCT agent_id) FROM agent_reasoning / total spawns`

2. **Debugging Utility**
   - Target: 50% reduction in Investigator iteration count
   - Measure: Compare iteration counts before/after reasoning availability

3. **Review Efficiency**
   - Target: 20% faster Tech Lead reviews (less back-and-forth)
   - Measure: Time from READY_FOR_REVIEW to APPROVED

4. **Handoff Quality**
   - Target: 30% fewer "context lost" escalations
   - Measure: Escalation reasons citing missing context

---

## References

- [Claude Code Background Agent Feature](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [SubagentStop Hook Documentation](https://code.claude.com/docs/en/hooks)
- [Context Package System](research/context-package-system.md)
- [bazinga-db Schema Reference](/.claude/skills/bazinga-db/references/schema.md)

---

## Multi-LLM Review Integration

*Pending review from OpenAI GPT-5 and Google Gemini 3 Pro Preview*
