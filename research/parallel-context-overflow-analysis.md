# Parallel Context Overflow Analysis

**Date:** 2025-12-22
**Context:** BAZINGA orchestration system experiences context explosion when parallel subagents return results
**Decision:** Pending - multiple mitigation strategies identified
**Status:** Proposed
**Reviewed by:** OpenAI GPT-5, Google Gemini 3 Pro Preview (pending)

---

## Problem Statement

When BAZINGA runs in parallel mode:
1. **Initial state:** Context at ~46% after spawning parallel developers
2. **First return:** When ONE subagent returns → context jumps to 78%
3. **Second return:** When next subagent returns → context fills completely (100%)
4. **Result:** Cannot compact, workflow blocked, session lost

This makes parallel orchestration unusable for complex tasks, defeating the core value proposition of multi-agent development.

## Root Cause Analysis

### How Claude Code Task Tool Returns Work

Based on extensive research of official documentation and community sources:

1. **Subagents have isolated context windows** - Each Task() runs with its own 200k context window
2. **Full results return to parent** - When subagent completes, its final response becomes part of parent's context
3. **No built-in truncation** - There's no configuration to limit returned context size
4. **Parallel results aggregate** - All parallel Task results are placed in a single user message in parent context

The critical issue: **While subagents work in isolated context, their RESULTS return to the orchestrator's context in full.** With verbose agent outputs (reasoning, logs, code, file contents), each return can be 20-40k tokens.

### BAZINGA-Specific Amplifiers

Our agent prompts emphasize comprehensive output:
- `understanding` phase reasoning (mandatory)
- `completion` phase reasoning (mandatory)
- Detailed status capsules
- Full code blocks
- Test results

With 4 parallel developers, if each returns 25k tokens:
- 4 × 25k = 100k tokens added to orchestrator context
- Plus orchestrator's own context (prompts, state, routing logic)
- **Result:** Instant context exhaustion

## Solution Strategies

### Strategy 1: File-Based Result Passing (Recommended)

**Concept:** Subagents write full results to files, return only a compact summary + file reference.

**Implementation:**
```
Agent writes:
- Full reasoning → bazinga/artifacts/{session_id}/reasoning/{agent}_{group}.md
- Full code output → bazinga/artifacts/{session_id}/code/{group}/
- Test results → bazinga/artifacts/{session_id}/tests/{group}.md

Agent returns (to orchestrator context):
- Status code: READY_FOR_QA
- Summary: "Implemented 3 endpoints, 15 tests passing"
- File reference: "Full details in bazinga/artifacts/{session_id}/reasoning/developer_AUTH.md"
```

**Token Impact:**
- Before: 25,000 tokens per agent return
- After: ~500 tokens per agent return
- **Reduction: 98%**

**Pros:**
- Massive context savings
- Full information preserved in files
- Database can index file paths for retrieval
- Next agent in chain reads only what it needs

**Cons:**
- Requires agent prompt changes
- File I/O adds minimal latency
- Need to ensure files are properly cleaned up

### Strategy 2: Structured Output Schema Enforcement

**Concept:** Use JSON schemas to constrain what agents can return.

**Implementation:**
```python
# Define strict return schema
class AgentResult(BaseModel):
    status: Literal["READY_FOR_QA", "BLOCKED", "PASS", "FAIL", ...]
    summary: str = Field(max_length=500)
    key_findings: List[str] = Field(max_items=5)
    files_modified: List[str] = Field(max_items=20)
    artifact_path: str  # Where detailed output was saved
```

**Token Impact:**
- Enforced maximum ~2k tokens per return
- **Reduction: 90%+**

**Pros:**
- Programmatic enforcement
- Consistent output structure
- Easy to parse and route

**Cons:**
- Requires Claude Agent SDK (not available in Claude Code CLI)
- Loses flexibility for edge cases
- May truncate important error context

### Strategy 3: Reasoning to Database Only

**Concept:** Reasoning goes directly to database via bazinga-db skill, not returned in context.

**Implementation:**
```
Agent workflow:
1. Do work
2. Skill(command: "bazinga-db") → save-reasoning {session_id} {agent} {phase} {content}
3. Return ONLY: status code + 1-line summary

Orchestrator reads reasoning from DB only when needed for routing decisions.
```

**Token Impact:**
- Reasoning removed from return context
- **Reduction: 60-80%**

**Pros:**
- Reasoning preserved in database
- Structured storage with timestamps
- Queryable for debugging

**Cons:**
- Still returns code blocks and test output
- Skill invocation adds latency
- May fail if DB skill has issues

### Strategy 4: Deferred Context Loading

**Concept:** Don't load subagent results into orchestrator context. Instead, write to shared state and let next agent in chain read.

**Implementation:**
```
Developer completes → writes to bazinga/state/group_AUTH_dev_complete.json
Orchestrator sees completion event → routes to QA
QA spawns with: "Read state from bazinga/state/group_AUTH_dev_complete.json"
```

**Token Impact:**
- Orchestrator never loads full results
- **Reduction: 95%+**

**Pros:**
- Maximum context preservation
- Natural handoff between agents
- Orchestrator stays lightweight

**Cons:**
- Requires significant workflow redesign
- Agent-to-agent communication becomes file-based
- Orchestrator loses visibility into results (harder to route)

### Strategy 5: Aggressive Summary Mode

**Concept:** Agents return only structured status, everything else is optional.

**Implementation:**
Add to agent prompts:
```markdown
## Return Format (STRICT)

Your final response MUST be ONLY:

```json
{
  "status": "READY_FOR_QA",
  "summary": "max 100 words",
  "files_changed": ["file1.py", "file2.py"],
  "tests_added": 5,
  "tests_passing": 5,
  "artifact_path": "bazinga/artifacts/..."
}
```

NO additional text. NO code blocks. NO explanations.
Full details saved to artifact_path.
```

**Token Impact:**
- ~200-500 tokens per return
- **Reduction: 95%+**

**Pros:**
- Simple prompt modification
- Works with current architecture
- Deterministic parsing

**Cons:**
- Agents may not comply perfectly
- Loses some routing context
- User visibility reduced (must read files)

## Recommended Hybrid Approach

Combine strategies for maximum effectiveness:

### Tier 1: File-Based Full Output (Strategy 1)
- All verbose content goes to files
- Reasoning, code, tests, logs → artifacts folder

### Tier 2: Structured Return (Strategy 5)
- Agents return ONLY JSON status block
- ~300 tokens per agent

### Tier 3: Database Logging (Strategy 3)
- Key reasoning phases saved to DB
- Enables dashboard visualization
- Preserves audit trail

### Implementation Changes Required

1. **Agent Prompt Modifications**
   - Add "## Output Requirements" section enforcing file-first, summary-return pattern
   - Update all 6 agent files (developer, SSE, QA, TL, PM, Investigator)

2. **Prompt Builder Update**
   - Include artifact_path in task context
   - Ensure agents know where to write

3. **Orchestrator Update**
   - Parse JSON status instead of extracting from prose
   - Route based on status code only
   - Read files only when needed for next agent context

4. **File Structure**
   ```
   bazinga/artifacts/{session_id}/
   ├── reasoning/
   │   ├── developer_AUTH_understanding.md
   │   ├── developer_AUTH_completion.md
   │   └── ...
   ├── code/
   │   └── {group_id}/
   ├── tests/
   │   └── {group_id}_results.md
   └── reviews/
       └── tech_lead_{group_id}.md
   ```

## Token Budget Analysis

**Current State (Parallel Mode with 4 Developers):**
| Phase | Tokens Used | Cumulative |
|-------|-------------|------------|
| Orchestrator prompt | ~25k | 25k |
| PM spawn + return | ~15k | 40k |
| 4x Developer spawn prompts | ~10k | 50k |
| Developer 1 return | ~25k | 75k |
| Developer 2 return | ~25k | 100k |
| **CONTEXT FULL** | — | — |

**Proposed State (File-Based Returns):**
| Phase | Tokens Used | Cumulative |
|-------|-------------|------------|
| Orchestrator prompt | ~25k | 25k |
| PM spawn + return | ~5k (summary only) | 30k |
| 4x Developer spawn prompts | ~10k | 40k |
| Developer 1 return (JSON) | ~0.5k | 40.5k |
| Developer 2 return (JSON) | ~0.5k | 41k |
| Developer 3 return (JSON) | ~0.5k | 41.5k |
| Developer 4 return (JSON) | ~0.5k | 42k |
| 4x QA returns | ~2k | 44k |
| 4x TL returns | ~2k | 46k |
| PM final + BAZINGA | ~2k | 48k |
| **Remaining budget** | | ~150k |

**Improvement: 60% context remaining vs 0%**

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Agents don't comply with output format | Add validation in orchestrator, retry with stricter prompt |
| File I/O failures | Use atomic writes, verify file exists before routing |
| Next agent can't find files | Include explicit paths in task context |
| Loss of real-time visibility | Dashboard reads from files + DB, not context |
| Complex error scenarios | Investigator reads all artifacts to diagnose |

## Alternative Considered: Don't Use Parallel Mode

**Rejected** because:
- Sequential mode takes 4x longer
- User explicitly requires parallel execution
- Defeats value proposition of multi-agent system

## Alternative Considered: Ignore Reasoning

**Rejected** because:
- Reasoning is core value of BAZINGA
- Enables debugging and learning
- Required for quality assurance

## Implementation Priority

1. **Phase 1 (Critical):** Update agent prompts for file-based output
2. **Phase 2 (High):** Update prompt-builder to include artifact paths
3. **Phase 3 (Medium):** Update orchestrator response parsing for JSON status
4. **Phase 4 (Low):** Add file cleanup and artifact management

## Decision Rationale

The file-based approach is recommended because:
1. **Maximum context savings** (~95% reduction per agent return)
2. **Preserves all information** (nothing lost, just relocated)
3. **Compatible with existing architecture** (minimal refactoring)
4. **Enables future features** (artifact browsing, diff viewing)
5. **Proven pattern** (documented in Claude Code best practices)

## Next Steps

1. Get external LLM reviews (OpenAI + Gemini)
2. Integrate feedback
3. Present to user for approval
4. Implement in priority order

## References

- [Subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Context Management with Subagents](https://www.richsnapp.com/article/2025/10-05-context-management-with-subagents-in-claude-code)
- [Efficient Claude Code: Context Parallelism](https://www.agalanov.com/notes/efficient-claude-code-context-parallelism-sub-agents/)
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Context Windows - Claude Docs](https://docs.claude.com/en/docs/build-with-claude/context-windows)
