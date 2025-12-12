# Context-Assembler Usage Guide

**Version**: 1.5.2
**Status**: Production Ready (Phase 4.5 - Conservative Default Budget)

## Overview

The context-assembler skill provides intelligent context assembly for BAZINGA agents. It retrieves, ranks, and delivers relevant context packages while respecting token budgets and learning from error patterns.

## Dependencies

### tiktoken (Token Estimation)

The context-assembler uses `tiktoken` for accurate, model-aware token estimation with a 15% safety margin.

**Installation:**
```bash
pip install tiktoken
```

**Model-to-Encoding Mapping:**

| Model ID | Encoding | Chars/Token (approx) |
|----------|----------|----------------------|
| claude-opus-4-20250514 | cl100k_base | ~4 |
| claude-sonnet-4-20250514 | cl100k_base | ~4 |
| claude-3-5-sonnet | cl100k_base | ~4 |
| claude-3-5-haiku | cl100k_base | ~4 |
| haiku | cl100k_base | ~4 |
| sonnet | cl100k_base | ~4 |
| opus | cl100k_base | ~4 |

**Note:** Claude models use similar tokenization to GPT-4. The `cl100k_base` encoding provides approximate planning estimates; verify against actual usage where possible.

**Safety Margin:**
All token estimates include a 15% safety margin (configurable via `token_safety_margin` in skills_config.json):
```
effective_budget = model_limit * (1 - safety_margin)
```

**Fallback Behavior:**
If tiktoken is unavailable:
1. Uses character-based estimation (~4 chars per token)
2. Logs warning about reduced accuracy
3. Continues with heuristic token counting

## Invocation

From the orchestrator, before spawning an agent:

```python
# Invoke context-assembler to get relevant context
Skill(command: "context-assembler")
```

The skill reads the current session/group context from bazinga-db and outputs a structured markdown block.

## Output Format Examples

### Example 1: Developer Context with Error Pattern

```markdown
## Context for developer

### Relevant Packages (3/7)

**[HIGH]** research/auth-patterns.md
> JWT authentication patterns for React Native apps

**[MEDIUM]** research/api-design.md
> REST API design guidelines for mobile clients

**[MEDIUM]** findings/codebase-analysis.md
> Existing authentication code in src/auth/

### Error Patterns (1 match)

:warning: **Known Issue**: "Cannot find module '@/utils'"
> **Solution**: Check tsconfig.json paths configuration - ensure baseUrl is set correctly
> **Confidence**: 0.8 (seen 3 times)

:package: +4 more packages available (re-invoke with higher limit for details)
```

### Example 2: Empty Context (New Session)

```markdown
## Context for qa_expert

### Relevant Packages (0/0)

No context packages found for this session/group. The agent will proceed with task and specialization context only.
```

### Example 3: Fallback Mode (Database Error)

```markdown
## Context for tech_lead

:warning: Context assembly encountered an error. Proceeding with minimal context.

**Fallback Mode**: Task and specialization context only. Context packages unavailable.
```

## Heuristic Relevance Ranking

Packages are ranked using weighted scoring when FTS5 is unavailable:

| Factor | Weight | Description |
|--------|--------|-------------|
| Priority | 4 | critical=4, high=3, medium=2, low=1 |
| Same-group | 2 | Boost if package group_id matches request |
| Agent-type | 1.5 | Boost if package tagged for agent type |
| Recency | 1 | Prefer recently created packages |

**Scoring formula:**
```
score = (priority_weight * 4) + (same_group * 2) + (agent_match * 1.5) + (recency_factor)

Where:
- same_group = 1 if package.group_id == request.group_id, else 0
- agent_match = 1 if agent_type in package.consumers, else 0
- recency_factor = 1 / (days_since_created + 1)
```

## Token Budget Allocation

Different agent types receive different context budgets:

| Agent | Task | Specialization | Context Pkgs | Errors | Total |
|-------|------|----------------|--------------|--------|-------|
| Developer | 50% | 20% | 20% | 10% | 100% |
| Senior Software Engineer | 40% | 20% | 25% | 15% | 100% |
| QA Expert | 40% | 15% | 30% | 15% | 100% |
| Tech Lead | 30% | 15% | 40% | 15% | 100% |
| Investigator | 35% | 15% | 35% | 15% | 100% |

**Note:** SSE and Investigator handle escalations/complex debugging, so they receive more context and error budget than developers.

## Graduated Token Zones

| Zone | Usage | Behavior |
|------|-------|----------|
| Normal | 0-60% | Full context with all packages |
| Soft Warning | 60-75% | Prefer summarized content |
| Conservative | 75-85% | Minimal context only |
| Wrap-up | 85-95% | Complete current operation only |
| Emergency | 95%+ | Checkpoint and break |

**Zone indicator in output:**
```
Token budget: Soft Warning (70%) - using summaries
```

## Retrieval Limits

Configurable per agent type in `bazinga/skills_config.json`:

```json
{
  "context_engineering": {
    "retrieval_limits": {
      "developer": 3,
      "senior_software_engineer": 5,
      "qa_expert": 5,
      "tech_lead": 5,
      "investigator": 5
    }
  }
}
```

**Note:** SSE gets more packages (5) than developer (3) since it handles escalations requiring broader context.

## Error Pattern Learning

### Capture Flow
1. Agent fails with error X
2. Agent succeeds on retry
3. System extracts error signature
4. Redacts secrets (regex + entropy detection)
5. Stores pattern with confidence 0.5

### Injection Flow
1. Context-assembler queries error_patterns table
2. Matches current context against stored signatures
3. If confidence > 0.7, injects solution hint
4. Agent receives: ":warning: Known Issue: ... Solution: ..."

### Confidence Adjustment
- Each successful match: +0.1 (max 1.0)
- Each false positive: -0.2 (min 0.1)
- Below 0.3: Don't inject, observe only

## Configuration

Full configuration in `bazinga/skills_config.json`:

```json
{
  "context_engineering": {
    "enable_context_assembler": true,
    "enable_fts5": false,
    "retrieval_limits": {
      "developer": 3,
      "senior_software_engineer": 5,
      "qa_expert": 5,
      "tech_lead": 5,
      "investigator": 5
    },
    "redaction_mode": "pattern_only",
    "token_safety_margin": 0.15
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_context_assembler` | true | Enable/disable the skill |
| `enable_fts5` | false | Use FTS5 for relevance (requires SQLite FTS5) |
| `retrieval_limits.*` | 3 | Max packages per agent type |
| `redaction_mode` | pattern_only | `pattern_only`, `entropy`, or `both` |
| `token_safety_margin` | 0.15 | Safety margin for token budgets |

### Redaction Modes

| Mode | Description | Performance |
|------|-------------|-------------|
| `pattern_only` | Regex patterns for common secrets | Fast |
| `entropy` | High-entropy string detection | Slower |
| `both` | Regex + entropy (recommended for security) | Slowest |

## Error Handling

### Context-Assembler Fails
1. System injects minimal context (task + specialization only)
2. Logs warning to session
3. **Never blocks execution** - graceful degradation

### Database Locked
1. WAL mode allows concurrent reads
2. Writes retry with exponential backoff (100ms, 200ms, 400ms)
3. After 3 retries, proceed without write (log warning)

### FTS5 Unavailable
1. System uses heuristic fallback ranking:
   - Priority weight (critical > high > medium > low)
   - Same-group boost
   - Agent-type relevance
   - Recency
2. Logs info message about fallback mode

## Integration Example

```python
# In orchestrator, before spawning Developer agent:

# 1. Invoke context-assembler
Skill(command: "context-assembler")

# 2. Capture the output block
# 3. Include in Developer agent prompt
Task(
    prompt=f"""
    {context_assembler_output}

    ## Your Task
    Implement the authentication middleware...
    """,
    subagent_type="developer"
)
```

## Database Tables

The skill uses these tables (created in Phase 2):

| Table | Purpose |
|-------|---------|
| `context_packages` | Research files, findings, artifacts with priority/summary |
| `context_package_consumers` | Per-agent consumption tracking |
| `error_patterns` | Captured error signatures with solutions |
| `strategies` | Successful approaches from completions |
| `consumption_scope` | Per-iteration package consumption tracking |

## Metrics to Monitor

| Metric | Target | Measurement |
|--------|--------|-------------|
| Assembly latency | <500ms | Skill execution time |
| Context consumption | >50% | `consumption_scope` tracking |
| Error recurrence | <10% | `error_patterns.occurrences` |
| Prompt sizes | <80% | Token estimation logs |

## Priority Values

Packages can have one of four priority levels:

- **critical** - Must always be included (errors, blockers)
- **high** - Include if budget allows (research findings)
- **medium** - Default for most packages
- **low** - Include only if ample budget

## Related Documentation

- **Specification**: `specs/1-context-engineering/spec.md`
- **Data Model**: `specs/1-context-engineering/data-model.md`
- **Technical Plan**: `specs/1-context-engineering/plan.md`
- **Quickstart**: `specs/1-context-engineering/quickstart.md`

## Version History

- v1.3.0 (2025-12-12): Phase 4 - Graduated Token Management
  - Added tiktoken dependency for model-aware token estimation
  - Implemented 5 graduated token zones (Normal, Soft Warning, Conservative, Wrap-up, Emergency)
  - Added zone indicator to output (`🔶` for warnings, `🚨` for emergency)
  - Implemented summary-preference logic for Soft Warning zone
  - Implemented truncation behavior for Conservative/Wrap-up zones
  - Added token budget allocation per agent type (Developer: 50/20/20/10, QA: 40/15/30/15, Tech Lead: 30/15/40/15)
  - 15% safety margin applied to all token estimates
  - Fallback to character-based estimation when tiktoken unavailable
- v1.2.0 (2025-12-12): Bug fixes and improvements
  - Fixed agent_relevance calculation by adding LEFT JOIN to context_package_consumers
  - Fixed AGENT_TYPE variable passing to Python via sys.argv (not string interpolation)
  - Added per-agent default limits in Python fallback
  - Added deterministic tie-breaker (created_at DESC) for equal scores
  - Added note about system-generated session_ids in SQL queries
- v1.1.0 (2025-12-12): Critical fixes
  - Fixed query syntax for bazinga-db commands
  - Added Security Notes section
  - Clarified group_id handling (use empty string for session-wide)
- v1.0.0 (2025-12-12): Initial production release (Phase 3 complete)
  - Full heuristic relevance ranking
  - Package retrieval via bazinga-db
  - Output formatting with priority indicators
  - Empty packages handling
  - FTS5 availability check with fallback
  - Graceful degradation on failures
- v0.1.0 (2025-12-12): Phase 1 placeholder with directory structure
