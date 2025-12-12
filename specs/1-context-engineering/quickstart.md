# Quickstart: Context Engineering System

**Feature**: Context Engineering System
**Date**: 2025-12-12

## Overview

The Context Engineering System provides intelligent context assembly for BAZINGA agents. This guide shows how to use the `context-assembler` skill and integrate with the orchestration workflow.

## Basic Usage

### Invoking the Context-Assembler Skill

From the orchestrator, before spawning an agent:

```python
# Invoke context-assembler to get relevant context
Skill(command: "context-assembler")
```

The skill reads the current session/group context from bazinga-db and outputs a structured markdown block.

### Skill Output Format

```markdown
## Context for developer

### Relevant Packages (3/7)

**[HIGH]** research/auth-patterns.md
> Summary: JWT authentication patterns for React Native apps

**[MEDIUM]** research/api-design.md
> Summary: REST API design guidelines for mobile clients

**[MEDIUM]** findings/codebase-analysis.md
> Summary: Existing authentication code in src/auth/

### Error Patterns (1 match)

⚠️ **Known Issue**: "Cannot find module '@/utils'"
> **Solution**: Check tsconfig.json paths configuration - ensure baseUrl is set correctly
> **Confidence**: 0.8 (seen 3 times)

📦 +4 more packages available (invoke context-fetch for details)
```

## Integration Scenarios

### Scenario 1: Developer Agent Spawn

**Given** an active orchestration session with context packages
**When** orchestrator prepares to spawn a Developer agent

```python
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

### Scenario 2: Error Pattern Injection

**Given** a Developer failed with an error, then succeeded on retry
**When** the success is recorded

The system automatically:
1. Captures error signature (error type, message pattern, stack)
2. Redacts any secrets using regex + entropy detection
3. Stores in `error_patterns` table with initial confidence 0.5

**Next time** a similar error occurs:
1. Context-assembler queries `error_patterns` for matches
2. If confidence > 0.7, injects solution hint into context
3. Agent receives: "⚠️ Known Issue: ... Solution: ..."

### Scenario 3: Token Budget Exceeded

**Given** agent is at 70% token usage (Soft Warning zone)
**When** context-assembler is invoked

The system:
1. Detects current token usage via model-aware estimation
2. Applies graduated zone rules (Soft Warning = prefer summaries)
3. Returns summarized context instead of full bodies
4. Shows indicator: "🔶 Token budget: Soft Warning (70%) - using summaries"

### Scenario 4: QA Agent with More Context

**Given** QA Expert needs broader context than Developer
**When** context-assembler is invoked for qa_expert

```json
// skills_config.json
{
  "context_engineering": {
    "retrieval_limits": {
      "developer": 3,
      "qa_expert": 5,
      "tech_lead": 5
    }
  }
}
```

Result: QA receives 5 packages instead of 3, prioritized by relevance.

## Configuration

### skills_config.json

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

## Graduated Token Zones

| Zone | Usage | Behavior |
|------|-------|----------|
| Normal | 0-60% | Full context with all packages |
| Soft Warning | 60-75% | Prefer summarized content |
| Conservative | 75-85% | Minimal context only |
| Wrap-up | 85-95% | Complete current operation only |
| Emergency | 95%+ | Checkpoint and break |

## Error Handling

### Context-Assembler Fails

If the skill errors or times out:
1. System injects minimal context (task + specialization only)
2. Logs warning to session
3. **Never blocks execution** - graceful degradation

### Database Locked

If parallel agents cause lock contention:
1. WAL mode allows concurrent reads
2. Writes retry with exponential backoff (100ms, 200ms, 400ms)
3. After 3 retries, proceed without write (log warning)

### FTS5 Unavailable

If SQLite lacks FTS5 extension:
1. System uses heuristic fallback ranking:
   - Priority weight (critical > high > medium > low)
   - Same-group boost
   - Agent-type relevance
   - Recency
2. Logs info message about fallback mode

## Validation Checklist

Before deployment:

- [ ] `bazinga/bazinga.db` has new tables (run migration)
- [ ] `skills_config.json` has `context_engineering` section
- [ ] WAL mode enabled: `PRAGMA journal_mode=WAL;`
- [ ] Test with FTS5 unavailable (fallback mode)
- [ ] Test token zones at 60%, 75%, 85%, 95%
- [ ] Verify redaction catches test secrets

## Metrics to Monitor

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Assembly latency | <500ms | Log timestamps in skill |
| Context consumption | >50% | `consumption_scope` table |
| Error recurrence | <10% | `error_patterns.occurrences` |
| Prompt sizes | <80% model limit | Token estimation logs |
