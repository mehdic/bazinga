# Tier and Model Decision Flow

**Date:** 2025-11-25
**Context:** How PM and Orchestrator collaborate on agent assignment
**Status:** Implemented

---

## Overview

BAZINGA uses a two-layer decision system:
- **PM decides the Tier** (Developer vs Senior Software Engineer)
- **Orchestrator decides the Model** (haiku, sonnet, opus)

This separation allows PM to make context-aware decisions while keeping model configuration centralized and runtime-updateable.

---

## PM: Tier Assignment

### Complexity Scoring

PM assigns a complexity score (1-10) to each task group:

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

### Tier Mapping

| Complexity | Initial Tier |
|------------|--------------|
| 1-3 | Developer |
| 4-10 | Senior Software Engineer |

### Override Rules

Regardless of complexity score:
- Security-sensitive code → **Senior Software Engineer**
- Architectural decisions → **Senior Software Engineer**
- Bug fix with clear symptoms → **Developer** (even if 7+)
- External system integration → **Senior Software Engineer**
- Performance-critical paths → **Senior Software Engineer**

### PM Output Format

```markdown
**Group AUTH: JWT Implementation**
- Complexity: 8/10
- Initial Tier: Senior Software Engineer
- Tier Rationale: Security-sensitive authentication code
- Tasks: T001, T002, T003
```

---

## Orchestrator: Model Assignment

### Model Configuration

Orchestrator loads model assignments from database at initialization:

```sql
SELECT agent_role, model FROM model_config
```

Default configuration:
| Agent Role | Model | Rationale |
|------------|-------|-----------|
| developer | haiku | Cost-efficient for L1-2 tasks |
| senior_software_engineer | sonnet | Complex failures and L3+ tasks |
| qa_expert | sonnet | Test generation and validation |
| tech_lead | opus | Architectural decisions |
| project_manager | opus | Strategic planning |
| investigator | opus | Root cause analysis |
| validator | sonnet | BAZINGA verification |

### Translation Flow

```
PM Output:
  Initial Tier: Senior Software Engineer

Orchestrator:
  1. Reads "Senior Software Engineer"
  2. Maps to agent_role: "senior_software_engineer"
  3. Looks up MODEL_CONFIG["senior_software_engineer"] → "sonnet"
  4. Spawns: Task(model="sonnet", ...)
```

### Code Reference

```python
# Orchestrator spawn logic (agents/orchestrator.md:1226-1258)
IF Initial Tier = "Developer":
    model = MODEL_CONFIG["developer"]
    agent_file = "agents/developer.md"

IF Initial Tier = "Senior Software Engineer":
    model = MODEL_CONFIG["senior_software_engineer"]
    agent_file = "agents/senior_software_engineer.md"

Task(subagent_type="general-purpose", model=model, ...)
```

---

## Why This Separation?

| Concern | Owner | Reasoning |
|---------|-------|-----------|
| Task complexity | PM | Has full context about requirements |
| Agent capability | PM | Knows what tier can handle what |
| Model performance | Config/DB | Can be tuned without code changes |
| Cost optimization | Config/DB | Runtime adjustable |
| Future models | Config/DB | Add Claude 4 without PM changes |

### Benefits

1. **PM stays domain-focused** - Thinks in terms of "this needs a senior engineer" not "this needs sonnet"
2. **Models are centrally managed** - One place to update when new models release
3. **Runtime flexibility** - Upgrade all developers to sonnet for a complex project without code changes
4. **Clear responsibility** - PM = what, Orchestrator = how

---

## Escalation Triggers

Beyond initial assignment, escalation can occur:

| Trigger | From | To |
|---------|------|-----|
| `revision_count >= 1` | Developer | Senior Software Engineer |
| `challenge_level_3_fail` | Developer | Senior Software Engineer |
| `ESCALATE_SENIOR` status | Developer | Senior Software Engineer |
| `revision_count >= 2` (after SSE) | Senior Software Engineer | Tech Lead |

---

## Configuration Files

- `bazinga/model_selection.json` - Fallback JSON config
- `model_config` table in `bazinga.db` - Primary source (DB)
- `bazinga/challenge_levels.json` - QA challenge escalation rules

---

## References

- `agents/project_manager.md` - PM tier assignment rules (lines 78-124, 2036-2077)
- `agents/orchestrator.md` - Model config loading (lines 554-596) and spawn logic (lines 1226-1258)
- `.claude/skills/bazinga-db/references/schema.md` - model_config table schema
