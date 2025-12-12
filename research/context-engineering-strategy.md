# Context Engineering Strategy for BAZINGA

**Date:** 2025-12-12
**Context:** Improving context passing to agents in BAZINGA orchestration
**Decision:** TBD - Pending user approval
**Status:** Proposed
**Reviewed by:** Pending external LLM review

---

## Problem Statement

BAZINGA currently passes minimal context to agents:
1. **Specialization blocks** (HOW to code) - Working ✅
2. **Context packages** (research/investigation findings) - Present but underutilized
3. **Agent reasoning** (WHY decisions were made) - Present but underutilized

**Issues identified:**
- No visibility when context packages are empty (fixed in this PR)
- No automatic collection of useful context during agent execution
- No semantic prioritization of context based on relevance
- No cross-session memory for recurring patterns
- Context can grow unbounded without compression strategy

---

## Research: Three Paradigms for Agent Context

### 1. Google ADK: Tiered Memory Architecture

**Source:** [Google ADK Documentation](https://google.github.io/adk-docs/sessions/)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    WORKING CONTEXT                      │
│   (Compiled view for THIS invocation)                   │
│   - System instructions, agent identity                 │
│   - Selected history (not all)                          │
│   - Tool outputs, memory results                        │
│   - Artifact references                                 │
└────────────────────────┬────────────────────────────────┘
                         │ Compiled from
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌─────────┐        ┌──────────┐        ┌────────────┐
│ SESSION │        │  STATE   │        │   MEMORY   │
│ (Events)│        │(Key-Val) │        │(Long-term) │
│ Durable │        │ Mutable  │        │ Cross-sess │
│ Log     │        │ Working  │        │ Searchable │
└─────────┘        └──────────┘        └────────────┘
```

**Key concepts:**
- **Sessions**: Durable event log (all interactions)
- **State**: Short-term working memory (current task)
- **Memory**: Long-term searchable knowledge (user preferences, learned patterns)
- **Artifacts**: Binary/large content stored separately

**Scoping via prefixes:**
- `app:` - Application-wide (shared across all sessions)
- `user:` - User-specific (persists across sessions for one user)
- `temp:` - Invocation-specific (temporary)
- Unprefixed - Session-specific only

**BAZINGA relevance:**
- We have Sessions (bazinga.db logs)
- We have State (task_groups, pm_state)
- We lack: Cross-session Memory, proper scoping

---

### 2. Manus: Context Offloading & Compression

**Source:** [Manus Context Engineering Blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

**Core strategies:**

| Strategy | Description | BAZINGA Applicability |
|----------|-------------|----------------------|
| **KV-Cache Optimization** | Keep prompt prefixes stable for caching | Medium - agent prompts vary |
| **File System as Memory** | Offload large content to files, keep references | **HIGH** - we have artifacts/ |
| **Attention Manipulation** | Write todo.md to keep goals in recent context | **HIGH** - we have todo lists |
| **Error Preservation** | Keep failures in context to prevent repetition | **HIGH** - we log errors |
| **Controlled Randomness** | Vary phrasing to prevent mimicry | Low - not a current issue |

**Compression strategy:**
```
IF context > 128k tokens:
    1. Summarize oldest 20 turns (JSON structure)
    2. Keep last 3 turns RAW (preserve rhythm)
    3. Offload tool results to filesystem
```

**BAZINGA relevance:**
- We don't compress context - agents just truncate
- We could offload large tool results to `bazinga/artifacts/`
- We could implement "keep recent turns raw" strategy

---

### 3. ACE: Evolving Context via Delta Updates

**Source:** [ACE Paper (arXiv:2510.04618)](https://arxiv.org/abs/2510.04618)

**Three-role architecture:**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  GENERATOR  │───▶│  REFLECTOR  │───▶│   CURATOR   │
│ (Execute)   │    │ (Critique)  │    │ (Synthesize)│
│             │    │             │    │             │
│ Run task,   │    │ Extract     │    │ Merge delta │
│ produce     │    │ lessons,    │    │ into context│
│ traces      │    │ refine      │    │ (non-LLM)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Delta updates (not full rewrites):**
```json
{
  "id": "strategy_001",
  "helpfulness_count": 5,
  "content": "When tests fail with import errors, check tsconfig paths first",
  "source": "Developer iteration 3, group AUTH"
}
```

**Grow-and-refine mechanism:**
1. **Growth**: Append new bullets with fresh IDs
2. **In-place update**: Increment helpfulness counters
3. **Refinement**: Deduplicate via semantic similarity when approaching capacity

**Performance gains:**
- -82% adaptation latency
- -75% rollouts needed
- +10.6% on agent tasks

**BAZINGA relevance:**
- We could implement delta context items
- QA Expert could be a Reflector (extracts lessons from failures)
- Curator could be automated (merge patterns across sessions)

---

## Current BAZINGA Context Flow

```
┌──────────────┐
│ Orchestrator │
└──────┬───────┘
       │ Queries bazinga-db for:
       │ 1. context_packages (research files)
       │ 2. reasoning_entries (prior decisions)
       ▼
┌──────────────────────────────────────────────────┐
│               BASE_PROMPT                        │
│  ┌─────────────────────────────────────────────┐ │
│  │ Context Packages (if any)                   │ │  ← Research from RE/Investigator
│  │ - Research files, findings                  │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ Agent Reasoning (if any)                    │ │  ← Why decisions were made
│  │ - Prior agent thought processes             │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ Task Requirements                           │ │  ← What to do
│  │ - From PM's task breakdown                  │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
       │
       │ + Specialization block (from skill)
       ▼
┌──────────────┐
│    Agent     │
└──────────────┘
```

**What's missing:**
1. No automatic context collection during execution
2. No compression for long-running tasks
3. No cross-session learning
4. No semantic relevance scoring
5. No error pattern memory

---

## Proposed Enhancement: Tiered Context System

### Tier 1: Immediate Context (Per-Invocation)
**Scope:** Single agent spawn
**Content:**
- Task requirements
- Specialization block
- Recent tool outputs (last 3)
- Relevant errors from this task

**Implementation:** Already exists, needs compression strategy

### Tier 2: Session Context (Per-Session)
**Scope:** All agents in current orchestration
**Content:**
- Context packages (research, investigation)
- Agent reasoning entries
- Shared learnings (patterns discovered this session)
- Error patterns encountered

**Implementation:** Exists via bazinga-db, needs better collection

### Tier 3: Project Context (Cross-Session)
**Scope:** Persists across orchestration sessions
**Content:**
- Common error fixes (e.g., "tsconfig paths issue → fix X")
- Code patterns for this project
- User preferences (testing style, naming conventions)
- Successful strategies (what worked before)

**Implementation:** NEW - requires cross-session memory store

---

## Proposed Collection Mechanisms

### A. Automatic Error Pattern Capture

**Trigger:** Agent reports failure, then succeeds on retry

**Capture:**
```json
{
  "pattern_id": "err_001",
  "error_signature": "Cannot find module '@/...'",
  "solution": "Check tsconfig.json paths configuration",
  "confidence": 0.8,
  "occurrences": 3,
  "last_seen": "2025-12-12T10:00:00Z"
}
```

**Usage:** When new agent sees similar error, inject solution hint

### B. Successful Strategy Extraction (ACE-inspired)

**Trigger:** Task completes successfully

**Process:**
1. QA Expert validates success
2. Reflector phase extracts: "What made this work?"
3. Curator merges into project context

**Example delta:**
```json
{
  "strategy_id": "strat_001",
  "context": "React Native offline sync",
  "insight": "Use @react-native-community/netinfo event listeners, not polling",
  "helpfulness": 5
}
```

### C. Research Context Prioritization

**Problem:** Research files vary in relevance to specific tasks

**Solution:** Semantic scoring
1. Embed task description
2. Embed each context package summary
3. Score by cosine similarity
4. Include top 3, mention existence of others

---

## Implementation Phases

### Phase 1: Visibility & Compression (Quick Wins)
- [x] Add "none found" messages for empty context
- [ ] Implement context compression for agents exceeding 50k tokens
- [ ] Keep last 3 tool outputs raw, summarize older ones
- [ ] Offload large tool results to artifacts/

### Phase 2: Better Collection (Medium Term)
- [ ] Auto-capture error patterns when retry succeeds
- [ ] Extract strategies from successful completions
- [ ] Semantic relevance scoring for context packages
- [ ] Priority-based context inclusion

### Phase 3: Cross-Session Memory (Long Term)
- [ ] Project-level pattern store (SQLite table)
- [ ] Cross-session error pattern memory
- [ ] User preference learning
- [ ] Deduplication via semantic similarity

---

## Decision Matrix: What to Implement

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Context visibility (empty messages) | Low | Medium | **P0** (Done) |
| Token budget increase | Low | Medium | **P0** (Done) |
| Large output offloading | Medium | High | P1 |
| Error pattern capture | Medium | High | P1 |
| Semantic relevance scoring | High | Medium | P2 |
| Strategy extraction | High | High | P2 |
| Cross-session memory | High | High | P3 |

---

## Critical Analysis

### Pros of Proposed Approach ✅
1. **Incremental**: Can implement in phases without breaking existing flow
2. **Aligned with research**: Draws from proven patterns (ADK, Manus, ACE)
3. **Addresses real issues**: Empty context visibility, unbounded growth
4. **Low risk**: Phase 1 changes are minimal

### Cons / Risks ⚠️
1. **Complexity**: Adding tiers adds cognitive load for debugging
2. **Storage**: Cross-session memory requires new tables/indices
3. **Relevance scoring**: May need embedding model, adds latency
4. **Over-engineering risk**: Current system works, may not need all features

### Verdict

Start with Phase 1 (visibility, compression) - low effort, immediate benefit.
Evaluate need for Phase 2 based on observed pain points.
Phase 3 only if agents repeatedly solve same problems across sessions.

---

## References

- [Google ADK Sessions & Memory](https://google.github.io/adk-docs/sessions/)
- [Google ADK Context](https://google.github.io/adk-docs/context/)
- [Google Cloud: Agent State & Memory with ADK](https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk)
- [Manus Context Engineering Blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [ACE Paper: Agentic Context Engineering](https://arxiv.org/abs/2510.04618)
- [MarkTechPost: Context Engineering Lessons from Manus](https://www.marktechpost.com/2025/07/22/context-engineering-for-ai-agents-key-lessons-from-manus/)

---

## Multi-LLM Review Integration

*Pending external review*
