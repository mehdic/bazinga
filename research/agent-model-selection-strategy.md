# Agent & Model Selection Strategy: Ultrathink Analysis

**Date:** 2025-12-02
**Context:** User observed PM spawning Haiku developers for research tasks, questioning optimal agent selection
**Decision:** Propose task-type-aware agent routing with difficulty-based model selection
**Status:** Reviewed and Revised
**Reviewed by:** OpenAI GPT-5 (2025-12-02)

---

## Problem Statement

The current BAZINGA system spawns **Developer (Haiku)** agents for **research tasks** like:
- "HIN OAuth2/SAML Provider Research & Setup"
- "Drug Database API Integration Research"
- "Swiss EPD (Electronic Patient Dossier) Research"
- "Speech-to-Text Provider Selection"

**The Issue:** Haiku is optimized for speed and cost on straightforward implementation tasks. Research tasks require:
- Deep reasoning and synthesis
- External information gathering and evaluation
- Comparative analysis and decision-making
- Technical judgment on trade-offs

This is a **task-type mismatch**, not just a complexity mismatch.

---

## Current System Analysis

### Current Model Selection (`model_selection.json`)

| Agent | Model | Rationale |
|-------|-------|-----------|
| Developer | Haiku | Cost-efficient for straightforward implementation |
| Senior Software Engineer | Sonnet | Escalation from developer - handles complex failures |
| QA Expert | Sonnet | Balanced capability for test generation |
| Tech Lead | Opus | Critical architectural decisions and security review |
| Project Manager | Opus | Strategic planning and final quality gate |
| Investigator | Opus | Complex debugging and root cause analysis |

### Current PM Complexity Scoring (from `project_manager.md`)

```
| Factor | Points |
|--------|--------|
| Touches 1-2 files | +1 |
| Touches 3-5 files | +2 |
| Touches 6+ files | +3 |
| Bug fix with clear symptoms | +1 |
| Feature following patterns | +2 |
| New pattern/architecture | +4 |
| Security-sensitive code | +3 |
| External API integration | +2 |
| Database migrations | +2 |
| Concurrent/async code | +2 |

Score 1-6: Developer (Haiku)
Score 7+: Senior Software Engineer (Sonnet)
```

### The Gap

The current system only considers **implementation complexity**, not **task type**. A research task about "OAuth2/SAML Provider Research" might score:
- Touches 0 files (+0) - no implementation yet
- External API integration (+2) - maybe
- **Total: 2 → Developer (Haiku)**

But research requires reasoning capabilities that Haiku lacks!

---

## Solution: Task-Type-Aware Agent Routing

### Proposed Task Classification

**Step 1: Classify Task Type BEFORE Complexity Scoring**

| Task Type | Characteristics | Default Agent |
|-----------|-----------------|---------------|
| **RESEARCH** | Discovery, evaluation, comparison, decision-making | Investigator (Opus) |
| **IMPLEMENTATION** | Writing code, following patterns | Developer/SSE (Haiku/Sonnet) |
| **DEBUGGING** | Finding root cause, hypothesis testing | Investigator (Opus) |
| **TESTING** | Writing/running tests | QA Expert (Sonnet) |
| **REVIEW** | Code quality, architecture assessment | Tech Lead (Opus) |

**Step 2: Task Type Detection Rules**

```
IF task_name contains ANY of ["research", "investigation", "evaluation", "selection", "comparison", "analysis", "discovery"]:
    → task_type = RESEARCH
    → agent = Investigator (Opus)

ELSE IF task_name contains ANY of ["debug", "diagnose", "root cause", "fix unknown", "investigate"]:
    → task_type = DEBUGGING
    → agent = Investigator (Opus)

ELSE IF task_name contains ANY of ["implement", "create", "add", "build", "write", "fix"]:
    → task_type = IMPLEMENTATION
    → Apply complexity scoring for Haiku vs Sonnet

ELSE IF task_name contains ANY of ["test", "validate", "verify"]:
    → task_type = TESTING
    → agent = QA Expert (Sonnet)

ELSE:
    → task_type = IMPLEMENTATION (default)
    → Apply complexity scoring
```

### Enhanced Complexity Scoring (for IMPLEMENTATION tasks only)

Add task-type modifiers:

```
| Factor | Points |
|--------|--------|
| [Existing factors...] | ... |
| Requires web research | +5 |
| Requires external API evaluation | +4 |
| Requires vendor comparison | +5 |
| Requires security/compliance assessment | +4 |
| Requires architecture decisions | +4 |
| Novel/unfamiliar domain | +3 |

Score 1-4: Developer (Haiku)
Score 5-6: Developer (Haiku) with Senior oversight
Score 7-9: Senior Software Engineer (Sonnet)
Score 10+: Senior Software Engineer (Sonnet) + Tech Lead review
```

---

## Critical Analysis

### Pros ✅

1. **Right Tool for Right Job**: Research tasks get reasoning-capable models
2. **Cost Optimization**: Simple implementations still use Haiku
3. **Quality Improvement**: Research outputs will be more thorough and accurate
4. **Consistent with Industry Research**: Aligns with DAAO paper's difficulty-aware routing
5. **Leverages Existing Infrastructure**: Uses existing Investigator agent for research
6. **No New Agents Needed**: Repurposes Investigator for research tasks

### Cons ⚠️

1. **Higher Cost for Research**: Opus is 5x more expensive than Haiku
2. **Slower Research Tasks**: Opus has higher latency
3. **PM Complexity**: PM needs additional logic for task classification
4. **False Positives**: "Research" in task name might not always mean research
5. **Investigator Overload**: Current Investigator is optimized for debugging, not research

### Verdict

**Implement with modifications**. The core insight is correct: research tasks need reasoning-capable models. However, we should:
1. Create a dedicated **Research Agent** rather than overloading Investigator
2. Use Sonnet for research (not Opus) as the default - escalate to Opus only for complex research
3. Add explicit task-type classification to PM workflow

---

## Implementation Details

### Option A: Reuse Investigator (Quick Fix)

- Modify Investigator agent to handle both debugging AND research
- Add research-specific prompts and skills
- **Pros**: Fast to implement, no new files
- **Cons**: Dilutes Investigator's focus

### Option B: Create Research Agent (Recommended)

Create new `agents/researcher.md`:

```yaml
---
name: researcher
description: Deep research agent for technology evaluation, API selection, and integration planning
model: sonnet  # Default to Sonnet, escalate to Opus for complex research
---

You are a **RESEARCHER AGENT** - specialized in technology evaluation and decision-making.

## Your Role
- Evaluate technology options and APIs
- Research integration requirements
- Compare vendors/solutions
- Produce actionable recommendations with pros/cons

## Your Tools
- WebSearch / WebFetch for external research
- codebase-analysis for understanding integration points
- pattern-miner for finding similar implementations

## Output Format
- Executive summary (1-2 paragraphs)
- Comparison matrix
- Recommendation with rationale
- Implementation notes for developers
```

### Option C: Hybrid Difficulty-Aware Routing (Advanced)

Implement DAAO-style routing:

1. **Difficulty Estimator**: Score task difficulty 0-1
2. **Task Type Classifier**: Detect research vs implementation
3. **Model Router**: Select model based on both dimensions

```
difficulty < 0.3 AND type == IMPLEMENTATION → Haiku
difficulty 0.3-0.6 AND type == IMPLEMENTATION → Sonnet
difficulty > 0.6 OR type == RESEARCH → Sonnet
type == DEBUGGING AND difficulty > 0.5 → Opus
```

---

## Comparison to Alternatives

### Alternative 1: Always Use Sonnet
- **Pros**: Consistent quality, no routing logic needed
- **Cons**: 3x cost increase, no cost optimization
- **Verdict**: Rejected - wasteful for simple tasks

### Alternative 2: Keep Current System, Just Relabel
- **Pros**: No code changes
- **Cons**: Doesn't solve the problem - Haiku still lacks reasoning
- **Verdict**: Rejected - doesn't address core issue

### Alternative 3: User Manually Specifies Model
- **Pros**: Maximum control
- **Cons**: Burden on user, defeats orchestration purpose
- **Verdict**: Rejected - against automation goals

### Alternative 4: PM Decides Model Per Task (Recommended Hybrid)
- **Pros**: PM already analyzes tasks, can add model selection
- **Cons**: Adds complexity to PM
- **Verdict**: Accepted - best balance of automation and flexibility

---

## Decision Rationale

**Why Task-Type Classification Works:**

1. **Research from Industry**: The DAAO paper shows 11% accuracy improvement with difficulty-aware routing
2. **Anthropic's Own Guidance**: "Route based on task complexity rather than using a single model uniformly"
3. **Cost-Performance Trade-off**: Research tasks are fewer but higher-impact - worth Sonnet/Opus cost
4. **Existing Pattern**: We already do this with Tech Lead (always Opus) and Investigator (always Opus)

**Why Sonnet for Research (Not Opus):**

1. **Cost**: Sonnet is $3/$15 per million tokens vs Opus at $15/$75 - 5x cheaper
2. **Speed**: Sonnet has lower latency for interactive research
3. **Capability**: Sonnet 4.5 handles research well - Opus only needed for deepest analysis
4. **Escalation Path**: Can escalate to Opus if Sonnet research is insufficient

---

## Proposed Changes

### 1. Update `model_selection.json`

```json
{
  "agents": {
    "developer": {
      "model": "haiku",
      "rationale": "Cost-efficient for straightforward IMPLEMENTATION tasks only",
      "task_types": ["implementation_simple"]
    },
    "senior_software_engineer": {
      "model": "sonnet",
      "rationale": "Complex implementation and escalated failures",
      "task_types": ["implementation_complex", "implementation_escalated"]
    },
    "researcher": {
      "model": "sonnet",
      "rationale": "Technology evaluation, API research, vendor comparison",
      "task_types": ["research", "evaluation", "selection"]
    },
    "investigator": {
      "model": "opus",
      "rationale": "Complex debugging and root cause analysis only",
      "task_types": ["debugging_complex", "root_cause_analysis"]
    }
  },
  "task_type_routing": {
    "research_keywords": ["research", "evaluation", "selection", "comparison", "analysis", "discovery", "find best"],
    "debugging_keywords": ["debug", "diagnose", "root cause", "fix unknown"],
    "implementation_keywords": ["implement", "create", "add", "build", "write", "fix known"]
  }
}
```

### 2. Update PM Task Classification Logic

In `project_manager.md`, add before complexity scoring:

```markdown
### Step 0: Classify Task Type

Before scoring complexity, classify each task:

**Research Tasks** (→ Researcher Agent, Sonnet):
- Contains: "research", "evaluate", "select", "compare", "analyze"
- Requires: external information, vendor comparison, technology decisions
- Examples: "OAuth provider selection", "Database comparison", "API evaluation"

**Debugging Tasks** (→ Investigator Agent, Opus):
- Contains: "debug", "diagnose", "root cause", "investigate failure"
- Requires: hypothesis testing, code analysis, systematic elimination
- Examples: "Find memory leak", "Diagnose timeout", "Root cause analysis"

**Implementation Tasks** (→ Developer, use complexity scoring):
- Contains: "implement", "create", "add", "build", "write", "fix"
- Requires: code writing, test creation, pattern following
- Examples: "Add login endpoint", "Create user model", "Fix null check"

**Assign agent based on task type BEFORE complexity scoring.**
```

### 3. Create `agents/researcher.md` (New Agent)

See Option B above for full specification.

---

## Implementation Checklist

- [ ] Create `agents/researcher.md` with research-focused prompts
- [ ] Update `model_selection.json` with task type mapping
- [ ] Update `project_manager.md` with task classification step
- [ ] Update orchestrator to spawn Researcher agent for research tasks
- [ ] Add research-related skills to skills registry
- [ ] Update dashboard to show Researcher as a valid agent type
- [ ] Add tests for task type classification
- [ ] Update documentation

---

## Expected Outcomes

| Metric | Before | After (Projected) |
|--------|--------|-------------------|
| Research task quality | Low (Haiku reasoning) | High (Sonnet reasoning) |
| Implementation cost | $X | $X (unchanged for simple tasks) |
| Research cost | $X (Haiku) | $3X (Sonnet) - acceptable |
| Task routing accuracy | ~60% (complexity only) | ~85% (type + complexity) |
| PM overhead | Low | Medium (adds classification step) |

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 on 2025-12-02
**Gemini:** Skipped (API blocked in Claude Code Web)

### Critical Insights (GPT-5)

The GPT-5 review identified several fundamental flaws in the original proposal:

1. **Investigator Misuse**: Using Investigator for research conflicts with its debugging-focused contract (5-iteration limit, hypothesis testing, mandatory DB logging semantics)

2. **Requirements Engineer Overlap**: BAZINGA already has a `requirements_engineer.md` agent designed for discovery, clarification, and structuring requirements - creating a Researcher duplicates this role

3. **Orchestration Gaps**: The original proposal didn't update response parsing, status codes, or message templates for the new agent

4. **Naive Classification**: Keyword-based task detection is fragile; should use explicit `task_type` metadata

### Incorporated Feedback (Revised Approach)

**MAJOR REVISION: Extend Requirements Engineer, Don't Create New Agent**

| Original Proposal | Revised Approach |
|-------------------|------------------|
| Create new Researcher agent | Extend Requirements Engineer with "Research Mode" |
| Repurpose Investigator for research | Keep Investigator strictly for debugging |
| Keyword-based task detection | Explicit `task_type` metadata in PM planning |
| No artifact persistence | Research artifacts → `bazinga/artifacts/{SESSION_ID}/research_{GROUP_ID}.md` |
| No success criteria | PM sets research success criteria before spawning |
| Unbounded research | Timebox to 1-2 iterations with token/time caps |

**Implementation Changes:**

1. **Add `task_type` to PM Task Groups**
   ```json
   "task_groups": {
     "RESEARCH-1": {
       "type": "research",  // NEW: research | implementation | debugging | testing
       "description": "OAuth provider evaluation",
       "agent": "requirements_engineer",
       "model": "sonnet"
     }
   }
   ```

2. **Extend Requirements Engineer with Research Mode**
   - Add optional WebFetch/WebSearch skills (feature-flagged)
   - Output format: executive summary, comparison matrix, recommendation, integration notes
   - Store artifacts to `bazinga/artifacts/`
   - ~~New statuses: `RESEARCH_COMPLETE`, `RESEARCH_BLOCKED`~~ → **REVISED:** Uses existing `READY_FOR_REVIEW`/`BLOCKED` statuses

3. **Research Workflow**
   ```
   PM (task_type=research) → Requirements Engineer (Sonnet)
                           → Tech Lead (validates decision)
                           → PM (plans implementation groups)
   ```

4. **Cost Guardrails**
   - Timebox research to 1-2 iterations
   - Require interim report if exceeded
   - PM can request "Phase 2 research" only if Tech Lead deems necessary

5. **Model Selection Refinement**
   - Requirements Engineer (research mode): Sonnet
   - Escalate to Opus only for high-risk research (security/legal/architecture)
   - Investigator: Stays on Opus, strictly for debugging

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| "Add [R] marker to Spec-Kit tasks.md" | Spec-Kit is external tool; we shouldn't mandate format changes. Use PM metadata instead. |
| "Research competing for MAX 4 parallel limit" | Research is a planning phase, not implementation. Should be sequential before dev spawning. |

### Revised Model Selection Matrix

| Task Type | Agent | Model | Rationale |
|-----------|-------|-------|-----------|
| Research/Evaluation | Requirements Engineer | Sonnet | Deep reasoning for vendor comparison |
| Research (high-risk) | Requirements Engineer | Opus | Security/compliance decisions |
| Simple Implementation | Developer | Haiku | Cost-efficient for straightforward tasks |
| Complex Implementation | Senior Software Engineer | Sonnet | Handles complex failures |
| Debugging/Root Cause | Investigator | Opus | Iterative hypothesis testing |
| Testing | QA Expert | Sonnet | Test generation and validation |
| Code Review | Tech Lead | Opus | Architectural decisions |
| Coordination | PM | Opus | Strategic planning |

### Updated Implementation Checklist

- [x] Add `task_type` field to PM task group schema ✅ Done
- [x] Update `project_manager.md` with task type classification step ✅ Done
- [x] Extend `requirements_engineer.md` with Research Mode section ✅ Done
- [ ] Add research-related skills to skills_config.json (feature-flagged)
- [x] ~~Add new statuses~~ → Uses existing READY_FOR_REVIEW/BLOCKED ✅ Done
- [ ] Update orchestrator message templates for research deliverables
- [ ] Define research artifact path and DB logging schema
- [ ] Add cost/iteration guardrails to PM research planning
- [ ] Update dashboard to show research task type
- [ ] Add tests for task type classification

### Confidence Level

**Medium-High**: The revised approach leverages existing infrastructure (Requirements Engineer, explicit metadata), adds proper guardrails, and avoids creating new agents or repurposing debugging tools. Main risk is the additional complexity in PM planning logic.

---

## References

- [Difficulty-Aware Agent Orchestration (DAAO)](https://arxiv.org/abs/2406.05726) - Academic research on task-difficulty routing
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - Official best practices
- [Strategic LLM Routing](https://mhaske-padmajeet.medium.com/strategic-llm-routing-business-rules-for-optimal-ai-model-selection-79a37b477dc8) - Business rules for model selection
- [Claude Model Comparison](https://medium.com/@ayaanhaider.dev/sonnet-4-5-vs-haiku-4-5-vs-opus-4-1-which-claude-model-actually-works-best-in-real-projects-7183c0dc2249) - Practical model selection guide
