# Compact Return Protocol (CRP) - Complete Design Document

**Date:** 2025-12-22
**Context:** BAZINGA orchestration system experiences context explosion when parallel subagents return results
**Decision:** Implement ultra-minimal file-based handoff pattern
**Status:** Approved by user, ready for implementation
**Reviewed by:** OpenAI GPT-5

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Solution Strategies Evaluated](#solution-strategies-evaluated)
4. [Recommended Solution: Ultra-Minimal Handoff](#recommended-solution-ultra-minimal-handoff)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Agent Output Format Mapping](#agent-output-format-mapping)
7. [Handoff File Structure](#handoff-file-structure)
8. [Implementation Plan](#implementation-plan)
9. [Token Budget Analysis](#token-budget-analysis)
10. [External LLM Review Integration](#external-llm-review-integration)

---

## Problem Statement

When BAZINGA runs in parallel mode:
1. **Initial state:** Context at ~46% after spawning parallel developers
2. **First return:** When ONE subagent returns → context jumps to 78%
3. **Second return:** When next subagent returns → context fills completely (100%)
4. **Result:** Cannot compact, workflow blocked, session lost

This makes parallel orchestration unusable for complex tasks, defeating the core value proposition of multi-agent development.

---

## Root Cause Analysis

### How Claude Code Task Tool Returns Work

Based on extensive research of official documentation and community sources:

1. **Subagents have isolated context windows** - Each Task() runs with its own 200k context window
2. **Full results return to parent** - When subagent completes, its final response becomes part of parent's context
3. **No built-in truncation** - There's no configuration to limit returned context size
4. **Parallel results aggregate** - All parallel Task results are placed in a single user message in parent context

**Critical insight:** While subagents work in isolated context, their RESULTS return to the orchestrator's context in full. With verbose agent outputs (reasoning, logs, code, file contents), each return can be 20-40k tokens.

### Key Clarification: What Returns vs What Stays Isolated

**What gets returned to orchestrator context:**
- Only the agent's **FINAL RESPONSE TEXT** - not the tool calls

**What stays in agent's isolated context (never returned):**
- All intermediate tool calls (Read, Write, Bash, Grep, etc.)
- File contents the agent read
- Outputs from commands it ran

So the pattern works if agents:
1. Write verbose content to files DURING execution (in isolated context)
2. Make the FINAL RESPONSE compact (just status + summary + file references)

The file writing itself doesn't bloat parent context. What bloats it is whatever text the agent outputs as its final response.

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

---

## Solution Strategies Evaluated

### Strategy 1: File-Based Result Passing

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

**Token Impact:** ~2k tokens per return, **90%+ reduction**

**Verdict:** Requires Claude Agent SDK (not available in Claude Code CLI). Rejected.

### Strategy 3: Reasoning to Database Only

**Concept:** Reasoning goes directly to database via bazinga-db skill, not returned in context.

**Token Impact:** 60-80% reduction

**Verdict:** Partially implemented already. Agents save to DB but ALSO include in response.

### Strategy 4: Deferred Context Loading

**Concept:** Don't load subagent results into orchestrator context. Write to shared state.

**Token Impact:** 95%+ reduction

**Verdict:** Good but requires significant workflow redesign.

### Strategy 5: Aggressive Summary Mode

**Concept:** Agents return only structured status, everything else is optional.

**Token Impact:** 95%+ reduction

**Verdict:** Simple prompt modification, works with current architecture.

---

## Recommended Solution: Ultra-Minimal Handoff

### User's Key Insight

The orchestrator doesn't NEED most of the returned data. It only needs:
- **status** - for routing (READY_FOR_QA → spawn QA)
- That's it!

The "files_modified" and "test counts" are only needed by the NEXT agent, not the orchestrator.

### Ultra-Minimal Flow (With User Visibility)

```
Developer completes:
1. Writes everything to artifact file: bazinga/artifacts/{session}/{group}/handoff_dev.json
2. Returns to orchestrator:
   {
     "status": "READY_FOR_QA",
     "summary": [
       "Implemented JWT authentication with token generation and validation",
       "Created 3 files: jwt_handler.py, auth_middleware.py, test_jwt.py",
       "All 15 tests passing with 92% coverage"
     ]
   }
   ← ~100-150 tokens

Orchestrator receives:
1. Parses status → READY_FOR_QA
2. Prints summary to user (visibility!)
3. Routes to QA Expert
4. Prompt-builder tells QA: "Read your context from bazinga/artifacts/.../handoff_dev.json"

QA Expert:
1. Reads handoff_dev.json in its OWN isolated context
2. Has all the info it needs (files, test counts, details, etc.)
```

### Why 3-Line Summary?

The user needs visibility into what agents accomplished. The 3-line summary:
- Line 1: What was done (the main accomplishment)
- Line 2: What changed (files, components affected)
- Line 3: Result (tests, quality metrics, status)

This gives the user meaningful progress updates without bloating context.

### Token Impact Comparison

| Scenario | Per Agent Return | 4 Parallel Devs | Full Cycle (4 groups × 3 agents) |
|----------|-----------------|-----------------|----------------------------------|
| **Current** | ~25,000 | ~100,000 | ~300,000 (OVERFLOW) |
| **CRP (JSON)** | ~400 | ~1,600 | ~4,800 |
| **Ultra-Minimal + Summary** | ~150 | ~600 | ~1,800 |

**Still 99% reduction, but user sees progress!**

---

## Data Flow Architecture

### Complete Data Preservation Map

#### What's ALREADY Saved (No changes needed):

| Data | Where It's Saved | How | When |
|------|-----------------|-----|------|
| **Reasoning** | `bazinga-db` | `Skill(bazinga-db) → save-reasoning` | During agent execution |
| **Code** | Repository files | `Edit()` / `Write()` tools | During agent execution |

#### What's NEW (Must add to agent prompts):

| Data | Where to Save | How | When |
|------|--------------|-----|------|
| **Handoff data** | `bazinga/artifacts/{session}/{group}/handoff_{agent}.json` | `Write()` tool | Before final response |
| **Test Results (detailed)** | `bazinga/artifacts/{session}/tests/{group}.md` | `Write()` tool | Before final response |
| **Review Feedback (detailed)** | `bazinga/artifacts/{session}/reviews/{group}.md` | `Write()` tool | Before final response |

#### What Returns to Orchestrator (Minimal + Summary):

```json
{
  "status": "READY_FOR_QA",
  "summary": [
    "Implemented JWT authentication with token generation and validation",
    "Created 3 files: jwt_handler.py, auth_middleware.py, test_jwt.py",
    "All 15 tests passing with 92% coverage"
  ]
}
```

**~100-150 tokens. Orchestrator prints summary to user for visibility.**

### Complete Handoff Chain

| From | Writes To | Returns to Orchestrator | Next Agent Reads |
|------|-----------|------------------------|------------------|
| Developer | `handoff_dev.json` | `{"status": "READY_FOR_QA"}` | QA reads `handoff_dev.json` |
| QA Expert | `handoff_qa.json` | `{"status": "PASS"}` | Tech Lead reads `handoff_qa.json` |
| Tech Lead | `handoff_tl.json` | `{"status": "APPROVED"}` | PM reads `handoff_tl.json` |
| PM | DB state | `{"status": "BAZINGA"}` | N/A (end) |

### Who Reads What, When

| Data | Stored In | Read By | When | How |
|------|-----------|---------|------|-----|
| **Reasoning** | bazinga-db | Next agent | At spawn | prompt-builder queries DB, includes in prompt |
| **Code** | Repo files | QA, TL | During their work | Direct file reads in isolated context |
| **Handoff data** | Artifact file | Next agent | First action | Reads file in isolated context |
| **Status** | Orchestrator context | Orchestrator | Immediately | For routing decision only |

---

## Agent Output Format Mapping

### Current Verbose Formats (The Problem)

#### Developer (lines 926-964, 1268-1364 in developer.md):

```markdown
## Implementation Complete

**Summary:** [One sentence describing what was done]

**Files Modified:**
- path/to/file1.py (created/modified)
- path/to/file2.py (created/modified)

**Key Changes:**
- [Main change 1]
- [Main change 2]
- [Main change 3]

**Code Snippet** (most important change):
```python
[5-10 lines of key code]        ← BLOAT!
```

**Tests:**
- Total: X
- Passing: Y
- Failing: Z

**Test coverage:**                ← BLOAT!
- Token generation with valid user
- Token validation with valid token
- [... more test descriptions]

**Concerns/Questions:**
- [Any concerns for tech lead review]

**Status:** READY_FOR_QA
**Next Step:** Orchestrator, please forward to QA Expert
```

**Estimated tokens: 5,000-10,000 per response**

#### QA Expert (lines 1232-1400+ in qa_expert.md):

```markdown
## QA Expert: Test Results - [PASS / FAIL / BLOCKED / FLAKY]

[One-line summary]

### Test Summary

**Integration Tests**: X/Y passed (duration)
[details or "Not available"]

**Contract Tests**: X/Y passed (duration)
[details or "Not available"]

**E2E Tests**: X/Y passed (duration)
[details or "Not available"]

**Total Tests**: X/Y passed
**Total Duration**: XmYs

### Quality Assessment

✅ Integration: [assessment]
✅ Contracts: [assessment]
✅ E2E Flows: [assessment]

### Handoff to Tech Lead

All automated tests passing. Ready for code quality review.

Files tested: [list]
Branch: [name]

**Status:** PASS
**Next Step:** Orchestrator, please forward to Tech Lead
```

**Estimated tokens: 3,000-8,000 per response**

#### Tech Lead (lines 948-1050+ in tech_lead.md):

```markdown
## Review: APPROVED

**What Was Done Well:**
- [Specific accomplishment 1]
- [Specific accomplishment 2]

**Code Quality:** [Brief assessment]

**Test Coverage:** [Assessment of tests]

**Optional Suggestions for Future:**
- [Nice-to-have improvement 1]

**Ready for Production:** YES ✅

**Status:** APPROVED
**Next Step:** Orchestrator, please forward to PM
```

Or with changes requested (even more verbose with code examples).

**Estimated tokens: 3,000-6,000 per response**

### New Ultra-Minimal Formats (With User Visibility)

#### All Agents - Final Response:

```json
{
  "status": "STATUS_CODE",
  "summary": [
    "Line 1: What was accomplished (main action)",
    "Line 2: What changed (files, components)",
    "Line 3: Result (metrics, quality, next step)"
  ]
}
```

**Estimated tokens: ~100-150**

**Summary Guidelines by Agent:**

| Agent | Line 1 (What) | Line 2 (Changed) | Line 3 (Result) |
|-------|---------------|------------------|-----------------|
| Developer | "Implemented X feature" | "Created/modified N files: list" | "N tests passing, N% coverage" |
| QA Expert | "Tested X implementation" | "Ran integration/contract/E2E tests" | "N/N tests passed, quality: good" |
| Tech Lead | "Reviewed X implementation" | "Checked security, architecture, tests" | "Approved/Changes requested: reason" |
| PM | "Analyzed/tracked X" | "N groups complete, M remaining" | "Proceeding with phase N / BAZINGA" |
| Investigator | "Investigated X issue" | "Analyzed N files, found root cause" | "Solution: brief description" |

#### All Agents - Handoff File (written before final response):

```json
{
  "from_agent": "developer",
  "to_agent": "qa_expert",
  "timestamp": "2025-12-22T10:30:00Z",
  "session_id": "bazinga_20251222_103000",
  "group_id": "AUTH",

  "status": "READY_FOR_QA",
  "summary": "Implemented JWT auth with 3 endpoints, 15 tests passing",

  "files_modified": [
    "src/auth/jwt_handler.py",
    "src/middleware/auth.py",
    "tests/test_jwt_auth.py"
  ],

  "tests": {
    "total": 15,
    "passing": 15,
    "failing": 0,
    "coverage": "92%"
  },

  "branch": "feature/group-AUTH-jwt-auth",

  "concerns": [
    "Should we add refresh token rotation?"
  ],

  "artifacts": {
    "reasoning": "bazinga/artifacts/.../reasoning/developer_AUTH.md",
    "test_output": "bazinga/artifacts/.../tests/AUTH_dev.md"
  }
}
```

**This file is read by the NEXT agent in its isolated context, not by orchestrator.**

---

## Handoff File Structure

### Directory Layout

```
bazinga/artifacts/{session_id}/
├── handoffs/                     # Agent-to-agent handoff files
│   ├── {group}_dev.json          # Developer → QA handoff
│   ├── {group}_qa.json           # QA → Tech Lead handoff
│   └── {group}_tl.json           # Tech Lead → PM handoff
├── reasoning/                    # Detailed reasoning (also in DB)
│   ├── developer_{group}_understanding.md
│   ├── developer_{group}_completion.md
│   ├── qa_expert_{group}_understanding.md
│   └── ...
├── tests/                        # Detailed test output
│   ├── {group}_dev_results.md    # Developer's test output
│   └── {group}_qa_results.md     # QA's detailed test report
├── reviews/                      # Tech Lead review details
│   └── {group}_tech_lead.md      # TL's detailed feedback
└── investigations/               # Investigator analysis
    └── {group}_root_cause.md     # Root cause analysis
```

### Handoff File Schema by Agent

#### Developer Handoff (`handoff_dev.json`):

```json
{
  "from_agent": "developer",
  "status": "READY_FOR_QA | READY_FOR_REVIEW | BLOCKED | ESCALATE_SENIOR",
  "summary": "string (max 100 words)",
  "files_modified": ["path1", "path2"],
  "files_created": ["path1", "path2"],
  "tests": {
    "total": 15,
    "passing": 15,
    "failing": 0,
    "coverage": "92%"
  },
  "branch": "feature/group-X-description",
  "concerns": ["question1", "question2"],
  "tech_debt_logged": true | false,
  "artifacts": {
    "reasoning": "path/to/reasoning.md",
    "test_output": "path/to/tests.md"
  }
}
```

#### QA Expert Handoff (`handoff_qa.json`):

```json
{
  "from_agent": "qa_expert",
  "status": "PASS | FAIL | BLOCKED | FLAKY",
  "summary": "string",
  "tests_run": {
    "integration": {"passed": 15, "failed": 0, "duration": "30s"},
    "contract": {"passed": 6, "failed": 0, "duration": "12s"},
    "e2e": {"passed": 4, "failed": 0, "duration": "1m45s"}
  },
  "total_tests": {"passed": 25, "failed": 0},
  "challenge_level_reached": 3,
  "quality_assessment": "string",
  "failures": [],
  "artifacts": {
    "reasoning": "path/to/reasoning.md",
    "test_report": "path/to/qa_report.md"
  }
}
```

#### Tech Lead Handoff (`handoff_tl.json`):

```json
{
  "from_agent": "tech_lead",
  "status": "APPROVED | CHANGES_REQUESTED | ESCALATE_TO_OPUS | SPAWN_INVESTIGATOR",
  "summary": "string",
  "decision": "APPROVED | CHANGES_REQUESTED",
  "code_quality_score": 9,
  "security_issues": 0,
  "lint_issues": 2,
  "coverage_acceptable": true,
  "what_was_done_well": ["item1", "item2"],
  "required_changes": [],
  "suggestions": ["optional improvement 1"],
  "artifacts": {
    "reasoning": "path/to/reasoning.md",
    "review_details": "path/to/review.md"
  }
}
```

---

## Orchestrator Summary Display

When the orchestrator receives an agent response, it prints the summary to the user using the existing capsule format:

### Format

```
🔨 Group {id} [{agent}] | {summary[0]} | {summary[1]} | {summary[2]} → {next_step}
```

### Examples

**Developer completes:**
```
🔨 Group AUTH [Developer] | Implemented JWT authentication | Created 3 files: jwt_handler.py, auth_middleware.py, test_jwt.py | 15 tests passing, 92% coverage → QA Expert
```

**QA passes:**
```
✅ Group AUTH [QA] | Tested JWT implementation | Ran 25 integration/contract/E2E tests | 25/25 passed, quality excellent → Tech Lead
```

**Tech Lead approves:**
```
👔 Group AUTH [TL] | Reviewed JWT implementation | Checked security, architecture, coverage | Approved, ready for merge → PM
```

### Implementation in Orchestrator

The orchestrator's response parsing section should:

1. Parse the JSON response
2. Extract status and summary array
3. Format as capsule using message_templates.md
4. Print to user
5. Route based on status

```python
# Pseudo-code for orchestrator
response = parse_json(agent_response)
status = response["status"]
summary = response["summary"]

# Print to user
print(f"🔨 Group {group_id} [{agent}] | {summary[0]} | {summary[1]} | {summary[2]} → {next_agent}")

# Route based on status
route_to_next_agent(status)
```

---

## Implementation Plan

### Files to Modify

#### Phase 1: Agent Definitions (7 files)

| File | Changes Required |
|------|------------------|
| `agents/developer.md` | Add "Write Handoff" section, minimize final response |
| `agents/senior_software_engineer.md` | Same as developer |
| `agents/qa_expert.md` | Add "Write Handoff" section, minimize final response |
| `agents/tech_lead.md` | Add "Write Handoff" section, minimize final response |
| `agents/project_manager.md` | Minimize final response (uses DB for state) |
| `agents/investigator.md` | Add "Write Handoff" section, minimize final response |
| `agents/requirements_engineer.md` | Add "Write Handoff" section, minimize final response |

#### Phase 2: Prompt Builder (1 file)

| File | Changes Required |
|------|------------------|
| `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Inject handoff path for next agent to read |

Key change in `build_task_context()`:
```python
if previous_agent:
    handoff_path = f"bazinga/artifacts/{session_id}/{group_id}/handoffs/handoff_{previous_agent}.json"
    context += f"""
## Prior Agent Handoff (MANDATORY READ)

**FIRST:** Read the handoff from the previous agent:
```
Read: {handoff_path}
```

This contains all context you need from the previous agent.
Do NOT proceed without reading this file first.
"""
```

#### Phase 3: Response Parsing (1 file)

| File | Changes Required |
|------|------------------|
| `templates/response_parsing.md` | Simplify to status-only JSON parsing |

New parsing logic:
```markdown
## Response Parsing (All Agents)

Agent responses are now minimal JSON:

```json
{"status": "STATUS_CODE"}
```

Parse the status field and route accordingly:
- READY_FOR_QA → Spawn QA Expert
- PASS → Spawn Tech Lead
- APPROVED → Route to PM
- etc.

All detailed information is in handoff files, not in the response.
```

#### Phase 4: Source Files (2 files)

| File | Changes Required |
|------|------------------|
| `agents/_sources/developer.base.md` | Update with CRP sections |
| `agents/_sources/senior.delta.md` | Update with CRP sections |

### Agent Prompt Template Addition

Add this section to ALL agent files:

```markdown
## Handoff Protocol (MANDATORY)

### Before Your Final Response

**You MUST write a handoff file before returning your status.**

1. **Create handoff file:**
```
Write(
  file_path="bazinga/artifacts/{SESSION_ID}/{GROUP_ID}/handoffs/handoff_{YOUR_AGENT}.json",
  content=<handoff JSON per schema>
)
```

2. **Include all context the next agent needs:**
   - Files you modified/created
   - Test results
   - Any concerns or questions
   - Paths to detailed artifacts

### Your Final Response

**Your final response MUST be ONLY:**

```json
{"status": "YOUR_STATUS_CODE"}
```

**NO other text. NO explanations. NO code blocks.**

The next agent will read your handoff file. The orchestrator only needs your status for routing.
```

### Ensuring Next Agent Reads Handoff

**Method: Prompt-Builder Injection (Recommended)**

Update `prompt_builder.py` to automatically tell agents to read prior handoffs:

```python
def build_task_context(args, db_path):
    context = ""

    # Determine previous agent in chain
    agent_chain = {
        "qa_expert": "developer",  # or senior_software_engineer
        "tech_lead": "qa_expert",  # or developer if no tests
        "project_manager": "tech_lead"
    }

    previous_agent = agent_chain.get(args.agent_type)

    if previous_agent:
        handoff_path = f"bazinga/artifacts/{args.session_id}/{args.group_id}/handoffs/handoff_{previous_agent}.json"
        context += f"""
## Prior Agent Handoff (MANDATORY FIRST ACTION)

**Before doing ANYTHING else, read the handoff from {previous_agent}:**

```
Read: {handoff_path}
```

This file contains:
- What the previous agent accomplished
- Files that were modified
- Test results
- Any concerns to address
- Branch information

**DO NOT proceed without reading this file.**

---

"""

    # Rest of task context building...
    return context
```

---

## Token Budget Analysis

### Current State (Parallel Mode with 4 Developers):

| Phase | Tokens Used | Cumulative |
|-------|-------------|------------|
| Orchestrator prompt | ~25k | 25k |
| PM spawn + return | ~15k | 40k |
| 4x Developer spawn prompts | ~10k | 50k |
| Developer 1 return | ~25k | 75k |
| Developer 2 return | ~25k | 100k |
| **CONTEXT FULL** | — | — |

### With Ultra-Minimal Handoff:

| Phase | Tokens Used | Cumulative |
|-------|-------------|------------|
| Orchestrator prompt | ~25k | 25k |
| PM spawn + return | ~1k (status only) | 26k |
| 4x Developer spawn prompts | ~10k | 36k |
| Developer 1 return (JSON) | ~0.05k | 36.05k |
| Developer 2 return (JSON) | ~0.05k | 36.1k |
| Developer 3 return (JSON) | ~0.05k | 36.15k |
| Developer 4 return (JSON) | ~0.05k | 36.2k |
| 4x QA spawn + return | ~0.2k | 36.4k |
| 4x TL spawn + return | ~0.2k | 36.6k |
| PM final + BAZINGA | ~0.1k | 36.7k |
| **Remaining budget** | | **~163k** |

**Improvement: 163k tokens remaining vs 0 (overflow)**

---

## External LLM Review Integration

### OpenAI GPT-5 Review Summary

**Critical Issues Identified:**

1. **Incomplete integration plan with existing Bazinga routing/parsers**
   - Current orchestrator and templates rely on markdown headers and specific status markers
   - **Resolution:** Complete migration to new JSON format (per user decision)

2. **File path collision and race conditions**
   - Parallel agents writing artifacts must use deterministic, unique paths
   - **Resolution:** Path schema `{session}/{group}/handoffs/handoff_{agent}.json`

3. **No adaptive parallelism or headroom control**
   - **Resolution:** User rejected adaptive parallelism - not implementing

4. **Response-size guardrail suggestion**
   - **Resolution:** User correctly identified this won't work (too late once received)

### Specific Improvements Incorporated:

1. **Centralized path utilities** - Standardized naming: `{session}/{group}/handoffs/handoff_{agent}.json`

2. **Prompt-builder injection** - Automatically inject handoff paths for next agent

3. **Backward compatibility** - User chose complete migration, no dual-mode

### Rejected Suggestions (With Reasoning):

1. **Dual-mode parsing** - User wants complete migration to new format
2. **Adaptive parallelism** - User rejected (complexity not worth it)
3. **Response-size guardrail with retry** - Correctly rejected (by the time response arrives, tokens are consumed)

---

## User Decisions Log

| Decision Point | User Choice | Rationale |
|---------------|-------------|-----------|
| File-based output for all agents | ✅ YES | Map all decision trees first |
| Dual-mode parsing | ❌ NO | Complete migration to new format |
| Adaptive parallelism | ❌ NO | Added complexity not needed |
| Response-size guardrail | ❌ NO | Too late once response received |
| Ultra-minimal orchestrator | ✅ YES | Orchestrator only needs status |
| Include 3-line summary in return | ✅ YES | User needs visibility of agent work |
| Prompt-builder injects handoff path | ✅ YES (Option A) | Automatic, reliable, centralized |
| Orchestrator prints summary to user | ✅ YES | User visibility without context bloat |

---

## References

- [Subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Context Management with Subagents](https://www.richsnapp.com/article/2025/10-05-context-management-with-subagents-in-claude-code)
- [Efficient Claude Code: Context Parallelism](https://www.agalanov.com/notes/efficient-claude-code-context-parallelism-sub-agents/)
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Context Windows - Claude Docs](https://docs.claude.com/en/docs/build-with-claude/context-windows)
- [Output token limit issues - GitHub #10738](https://github.com/anthropics/claude-code/issues/10738)

---

## Next Steps (Implementation Order)

### Phase 1: Agent Files (7 files)

Update each agent with:
1. "Write Handoff File" section (before final response)
2. "Final Response Format" section (JSON with status + 3-line summary)
3. "Read Prior Handoff" section (for agents that receive from prior agent)

Order of implementation:
1. `agents/developer.md` - Most complex, sets the pattern
2. `agents/senior_software_engineer.md` - Similar to developer
3. `agents/qa_expert.md` - Receives from developer
4. `agents/tech_lead.md` - Receives from QA
5. `agents/project_manager.md` - Receives from TL, sends BAZINGA
6. `agents/investigator.md` - Special case for debugging
7. `agents/requirements_engineer.md` - Research agent

### Phase 2: Prompt Builder

Update `.claude/skills/prompt-builder/scripts/prompt_builder.py`:
1. Add `get_previous_agent()` function to determine agent chain
2. Update `build_task_context()` to inject handoff path
3. Add handoff path to spawned agent's prompt

### Phase 3: Response Parsing

Update `templates/response_parsing.md`:
1. Change all agent sections to parse JSON format
2. Extract status and summary array
3. Document capsule construction from summary

### Phase 4: Orchestrator

Update `agents/orchestrator.md` (and rebuild slash command):
1. Update response parsing instructions to use JSON
2. Add summary display using capsule format
3. Update routing to use status from JSON

### Phase 5: Testing

1. Run integration test with simple-calculator-spec
2. Verify parallel mode works without context overflow
3. Verify user sees summaries in terminal
4. Verify handoff files are created and read correctly

### Phase 6: Cleanup

1. Add artifact cleanup to session end
2. Document handoff file retention policy
