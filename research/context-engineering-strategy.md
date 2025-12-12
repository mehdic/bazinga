# Context Engineering Strategy for BAZINGA

**Date:** 2025-12-12
**Context:** Improving context passing to agents in BAZINGA orchestration
**Decision:** TBD - Pending user approval
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (2025-12-12)

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

**Reviewed by:** OpenAI GPT-5 (2025-12-12)
**Status:** Reviewed - Awaiting user approval for implementation

---

### Critical Issues Identified

| Issue | Recommendation | Status |
|-------|----------------|--------|
| **Orchestrator can't do context assembly** | Create dedicated `context-assembler` skill | Pending |
| **No semantic scoring capability** | Start with SQLite FTS5 before embeddings | Pending |
| **Token budgets undefined** | Define per-agent allocation rules | Pending |
| **SQLite contention in parallel mode** | Enable WAL mode, add indices | Pending |
| **Cross-session memory scope unclear** | Partition by project_id, add TTLs | Pending |
| **Security/PII risks** | Add redaction pipeline, trust levels | Pending |

---

### Consensus Points (Reviewer Agreed With Plan)

1. ✅ Tiered context architecture is sound (aligns with ADK/Manus/ACE)
2. ✅ Incremental implementation phases are correct approach
3. ✅ Visibility for empty context packages is valuable (already done)
4. ✅ Error pattern capture has high value
5. ✅ File system offloading for large outputs is recommended

---

### Incorporated Feedback

#### 1. New Skill Required: `context-assembler`

**Reviewer concern:** "Orchestrator is restricted from reading arbitrary files and must not implement logic; yet the plan assumes it will compile working context."

**Resolution:** Create dedicated `context-assembler` skill:
- **Input:** session_id, group_id, agent_type, token_budget
- **Output:** Compact markdown block with prioritized items + references
- **Responsibilities:** Relevance ranking (FTS5), compression, ordering, redaction
- **Constraint:** Never exceeds token budget

#### 2. Start with FTS5, Not Embeddings

**Reviewer concern:** "The repo has no embeddings or semantic-store skills."

**Resolution:** Use SQLite FTS5 (full-text search) for Phase 1:
- Index context package summaries and error messages
- Rank by keyword relevance (deterministic, low-latency)
- Add semantic embeddings in Phase 2+ only if needed

#### 3. Concrete Schema for Patterns/Strategies

**Reviewer concern:** "Referenced frameworks not validated in-repo."

**Resolution:** Define concrete tables:

```sql
-- Error patterns table
CREATE TABLE error_patterns (
    pattern_hash TEXT PRIMARY KEY,
    signature_json TEXT NOT NULL,
    solution TEXT NOT NULL,
    project_id TEXT NOT NULL,
    lang TEXT,
    confidence REAL DEFAULT 0.5,
    occurrences INTEGER DEFAULT 1,
    last_seen TEXT,
    created_at TEXT,
    ttl_days INTEGER DEFAULT 90
);

-- Strategies table
CREATE TABLE strategies (
    strategy_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    insight TEXT NOT NULL,
    helpfulness INTEGER DEFAULT 0,
    lang TEXT,
    framework TEXT,
    last_seen TEXT
);

-- Context index for FTS5
CREATE VIRTUAL TABLE context_index USING fts5(
    package_id,
    project_id,
    summary,
    content='context_packages'
);
```

#### 4. Per-Agent Token Budget Allocation

**Reviewer concern:** "Token budget claims without allocation rules."

**Resolution:** Define deterministic budgets:

| Agent | Task | Specialization | Context Pkgs | Errors | Total |
|-------|------|----------------|--------------|--------|-------|
| Developer | 50% | 20% | 20% | 10% | 100% |
| QA Expert | 40% | 15% | 30% | 15% | 100% |
| Tech Lead | 30% | 15% | 40% | 15% | 100% |

Enforced by `context-assembler` skill with preflight size checks.

#### 5. SQLite WAL Mode and Indices

**Reviewer concern:** "Parallel mode + new writes can introduce DB locks."

**Resolution:** Enable WAL mode in bazinga-db:
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

Add indices:
```sql
CREATE INDEX idx_patterns_project ON error_patterns(project_id, lang);
CREATE INDEX idx_strategies_project ON strategies(project_id, framework);
```

#### 6. Security and Privacy Guardrails

**Reviewer concern:** "Reasoning logs and error artifacts can contain secrets/PII."

**Resolution:**
- Redaction at ingestion (scrub before storing)
- Per-project scoping (no cross-project bleed)
- TTLs for long-term memory (default 90 days)
- Trust levels on injected context (human-reviewed vs auto)
- User opt-out via `skills_config.json`

---

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| "Context Ledger artifact per group" | Adds file I/O overhead; bazinga-db already serves this purpose |
| "Hash-based error signatures first" | Will implement semantic later; hash-only misses similar errors |

---

### Revised Implementation Phases

**Phase 1 (Recommended - Quick Wins):**
- [x] Visibility when no context (DONE)
- [x] Token budget increase (DONE)
- [ ] Create `context-assembler` skill
- [ ] SQLite FTS5 for relevance ranking
- [ ] Offload oversized tool outputs to artifacts/
- [ ] Enable WAL mode + indices
- [ ] Define retention policy (TTLs)

**Phase 2 (Medium Term):**
- [ ] Error-pattern capture (signature → solution on retry success)
- [ ] Strategy extraction (QA/TL generates "what worked" bullet at approval)
- [ ] Per-agent token budget enforcement via context-assembler

**Phase 3 (Long Term):**
- [ ] Semantic scoring via embeddings (if FTS5 insufficient)
- [ ] Cross-session memory with scoping
- [ ] Decay/aging for stale patterns
- [ ] Provenance and trust bits on context items

---

### Success Metrics (Added per Review)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Iterations per group | < 3 average | bazinga-db logs |
| Prompt sizes | < 80% of model limit | context-assembler reports |
| Context hits | > 50% of packages consumed | mark-consumed tracking |
| QA failure recurrence | < 10% same error twice | error_patterns table |

---

### Failure Handling (Added per Review)

If `context-assembler` errors or times out:
1. Inject only: task + specialization block + reference list (no full bodies)
2. Log warning to session
3. Never block execution - proceed with minimal context

---

## Gemini Review Integration (2025-12-12)

**Reviewed by:** Gemini (original suggestions) + OpenAI GPT-5 (validation review)
**Status:** Integrated

### Validated Issues from Gemini

| Issue | Verdict | Integration |
|-------|---------|-------------|
| **Retrieval Limit (LIMIT 3)** | ✅ Valid | Make configurable per agent, add overflow indicator |
| **Consumption Logic** | ✅ Valid | Iteration-aware tracking with migration path |
| **Path Validation** | ⚠️ Low Priority | Note in security section |
| **Threshold Logic** | ✅ Valid | Replace hard cutoffs with graduated zones |
| **Token Accuracy** | ✅ Critical | Model-aware tokenizer, safety margins |
| **Secret Redaction** | ✅ Valid | Entropy + patterns, configurable allow-lists |
| **Template Extraction** | ❌ Out of Scope | Orchestrator architecture, not context engineering |

---

### Additional Feedback from OpenAI Validation Review

#### 1. FTS5 Availability and Fallbacks

**Issue:** FTS5 virtual tables require SQLite compiled with FTS5. Many minimal environments lack it.

**Resolution:**
- Add runtime capability detection
- Implement heuristic fallback ranking without FTS5:
  - Compound score: priority weight + recency + same-group boost + agent-type match
- Only enable FTS5 when detected; degrade gracefully otherwise

#### 2. Model-Aware Tokenization

**Issue:** Different models (haiku/sonnet/opus) tokenize differently. Single estimator drifts badly.

**Resolution:**
- Context-assembler must be model-aware
- Per-model token calculators (tiktoken for Claude-compatible)
- Store `estimation_error` for monitoring drift
- Apply per-model budget caps

#### 3. Iteration-Aware Consumption Migration

**Issue:** Changing consumption tracking requires schema changes and backward compatibility.

**Resolution:**
- Introduce new `consumption_scope` table keyed by (session_id, group_id, agent_type, iteration)
- Keep old field for one release (write-through)
- Query prefers new scope when present
- Explicit migration scripts in bazinga-db

#### 4. On-Demand Context Expansion

**Issue:** Plan only pushes pre-selected context. No "expand on demand" pattern.

**Resolution:**
- Inject only titles/summaries with package IDs initially
- Provide "context-fetch" skill for agents to request full bodies
- Reduces initial prompt size, gives agents control

#### 5. Redaction Configurability

**Issue:** Entropy-based detection can over-redact legitimate code/data.

**Resolution:**
- Pair entropy with contextual rules (file type, prefix heuristics)
- Maintain allow-list (UUIDs, hashes in fixtures)
- Per-project and per-agent configuration
- Log sampling to tune thresholds

---

### Revised Token Management (Graduated Zones)

Replace hard cutoffs with graduated zones:

| Token Usage | Zone | Behavior |
|-------------|------|----------|
| 0-60% | **Normal** | Full context, all packages |
| 60-75% | **Soft Warning** | Prefer summarized context |
| 75-85% | **Conservative** | Minimal context, no new large operations |
| 85-95% | **Wrap-up** | Complete current operation only |
| 95%+ | **Emergency** | Checkpoint and break |

**Key principle:** Check token budget BEFORE starting operation, not during. Add "in-progress operation" flag to prevent mid-task interruption.

---

### Context-Assembler MVP Specification (Updated)

Based on combined reviews, MVP should be:

**Inputs:**
- session_id, group_id, agent_type, model

**Ranking (No FTS5 in MVP):**
1. Priority level (critical > high > medium > low)
2. Same-group match boost
3. Agent-type relevance (research→Developer, failures→QA)
4. Recency (newer preferred)

**Output:**
- Top N summaries (configurable per agent: Developer=3, QA=5, TechLead=5)
- Overflow indicator: "📦 +{X} more packages available"
- Package IDs for on-demand expansion

**Token Budgeting:**
- Model-aware tokenizer
- 15% safety margin (increased from 10%)
- Truncate least-relevant first when over budget

**Fallbacks:**
- FTS5 unavailable → Use heuristic ranking
- Timeout → Return empty with warning
- Error → Inject minimal context (task + spec only)

---

### Updated Phase 1 Checklist

**Phase 1 (Quick Wins) - Revised:**
- [x] Visibility when no context (DONE)
- [x] Token budget increase (DONE)
- [ ] Create `context-assembler` skill (MVP, no FTS5)
- [ ] Model-aware tokenization with safety margins
- [ ] Configurable retrieval limits per agent type
- [ ] Iteration-aware consumption with migration
- [ ] Graduated token zones (replace hard cutoffs)
- [ ] Enable WAL mode + centralized DB access with retries
- [ ] Configurable secret redaction with allow-lists

**Deferred to Phase 2:**
- [ ] FTS5 relevance ranking (when available)
- [ ] On-demand context expansion ("context-fetch" skill)
- [ ] Error-pattern capture
- [ ] Cross-session memory

---

### Feature Flags (Added per Review)

Gate new features in `skills_config.json`:

```json
{
  "context_engineering": {
    "enable_context_assembler": true,
    "enable_fts5": false,
    "retrieval_limits": {
      "developer": 3,
      "qa_expert": 5,
      "tech_lead": 5
    },
    "redaction_mode": "pattern_only",
    "token_safety_margin": 0.15
  }
}
```

Start with conservative settings, expand after stabilization.
