# QA Specialization Gap Analysis

**Date:** 2025-12-13
**Context:** Integration test revealed QA Expert received 0 templates despite QA-compatible templates existing
**Decision:** TBD
**Status:** Proposed
**Reviewed by:** TBD

---

## Problem Statement

During the BAZINGA integration test, the QA Expert agent was spawned with **0 specialization templates loaded**, despite:
1. QA-compatible templates existing (`qa-strategies.md`, `testing-patterns.md`)
2. The specialization-loader skill being invoked
3. The task group having a Python specialization assigned

The specialization-loader output showed:
```
Metadata:
- Group: CALC
- Templates: 0 loaded (Python template not compatible with qa_expert)
- Tokens: ~350/1800
- Identity: Python QA Specialist (pytest)
```

---

## Root Cause Analysis

### Issue 1: Template Compatibility Mismatch

**Python template frontmatter:**
```yaml
compatible_with: [developer, senior_software_engineer]
```

**QA Expert is NOT in this list**, so the template was correctly filtered out by the specialization-loader.

### Issue 2: Missing QA Template Assignment

The task group only had ONE specialization assigned:
```json
"specializations": ["templates/specializations/01-languages/python.md"]
```

QA-compatible templates exist but were never assigned:
- `08-testing/qa-strategies.md` → `compatible_with: [qa_expert, tech_lead]`
- `08-testing/testing-patterns.md` → `compatible_with: [developer, senior_software_engineer, qa_expert]`

### Issue 3: Single Specialization Array Design

Current design: **One `specializations` array per task group**, shared by all agents.

Problem: Different agents need different templates:
- Developer needs: `python.md`
- QA Expert needs: `qa-strategies.md`, `testing-patterns.md`
- Tech Lead needs: `code-review.md`, `security-auditing.md`

The current design forces all agents to use the same template list, which breaks when templates have agent-specific `compatible_with` filters.

---

## Secondary Finding: Context Engineering Data Not Persisted

The database is missing critical context engineering data:

| Table | Expected | Actual |
|-------|----------|--------|
| `skill_outputs` | specialization-loader output | Empty |
| `context_packages` | Inter-agent context sharing | Empty |
| `reasoning_log` | Agent reasoning documentation | Empty |
| `success_criteria` | PM's 11 criteria | Empty |

### Why This Matters

1. **No audit trail** - Can't trace why decisions were made
2. **No inter-agent context** - Agents don't benefit from prior agent's findings
3. **No reasoning preservation** - Lost on context compaction
4. **BAZINGA validation incomplete** - Success criteria not queryable

### Root Causes

1. **Spawned agents didn't invoke bazinga-db skill** for reasoning/context packages
2. **PM saved success criteria** but to internal state, not to DB table
3. **Specialization-loader composed block** but didn't log to `skill_outputs`
4. **Orchestrator didn't verify** DB persistence after agent completions

---

## Proposed Solutions

### Solution A: Per-Agent Specialization Arrays

Change task group schema from:
```json
{
  "specializations": ["python.md"]
}
```

To:
```json
{
  "specializations": {
    "developer": ["python.md", "testing-patterns.md"],
    "qa_expert": ["qa-strategies.md", "testing-patterns.md"],
    "tech_lead": ["code-review.md", "python.md"]
  }
}
```

**Pros:**
- Clean separation of agent-specific templates
- No reliance on `compatible_with` filtering
- PM explicitly decides what each role needs

**Cons:**
- More complex task group schema
- PM must understand template catalog
- Increased cognitive load on PM

### Solution B: Auto-Augment Based on Role

Keep single array but have specialization-loader **auto-add role-specific templates**:

```python
def augment_specializations(base_list, agent_type):
    role_defaults = {
        "qa_expert": ["08-testing/qa-strategies.md", "08-testing/testing-patterns.md"],
        "tech_lead": ["11-domains/code-review.md", "10-security/security-auditing.md"],
        "developer": [],  # Uses base list as-is
    }
    return base_list + role_defaults.get(agent_type, [])
```

**Pros:**
- Backwards compatible
- PM doesn't need to know QA templates
- Automatic role enhancement

**Cons:**
- Magic behavior (implicit template addition)
- May add templates that aren't relevant
- Harder to understand what's loaded

### Solution C: Hybrid - Role Defaults + PM Override

PM specifies base templates. System auto-augments with role defaults unless PM explicitly sets `"disable_role_defaults": true`.

```json
{
  "specializations": ["python.md"],
  "disable_role_defaults": false  // Default
}
```

Loader behavior:
1. Start with PM's base list
2. Filter by `compatible_with` for current agent
3. Auto-add role defaults for agent type
4. Deduplicate

**Pros:**
- Best of both worlds
- PM can override if needed
- Maintains backwards compatibility

**Cons:**
- Slightly more complex logic
- Need to document role defaults

---

## Solution D: Fix DB Persistence (Separate Concern)

For the context engineering data gap, implement:

1. **Orchestrator verification gate**: After each agent spawn, verify expected DB writes occurred
2. **Mandatory reasoning hooks**: Agent definitions enforce `understanding` and `completion` phases
3. **Success criteria DB sync**: PM explicitly calls `save-success-criteria` command
4. **Skill output logging**: specialization-loader uses `save-skill-output` after composing

---

## Recommended Approach

**Primary:** Solution C (Hybrid - Role Defaults + PM Override)
- Maintains backwards compatibility
- QA Expert automatically gets testing templates
- PM can still customize if needed

**Secondary:** Solution D (Fix DB Persistence)
- Separate PR/implementation
- Critical for audit trail and debugging

---

## Implementation Details

### Phase 1: Add Role Defaults to Specialization-Loader

Update `.claude/skills/specialization-loader/SKILL.md`:

```markdown
### Step 3.6: Auto-Augment Role Defaults

After filtering by compatibility, add role-specific defaults:

| Agent Type | Auto-Added Templates |
|------------|---------------------|
| qa_expert | 08-testing/qa-strategies.md, 08-testing/testing-patterns.md |
| tech_lead | 11-domains/code-review.md |
| investigator | (none - investigates specific issues) |
| developer | (none - uses PM-assigned templates) |
| senior_software_engineer | (none - uses PM-assigned templates) |
| requirements_engineer | 11-domains/research-analysis.md |

Skip if template already in filtered list (no duplicates).
```

### Phase 2: Update Task Group Schema (DB)

Add optional `role_specializations` column:
```sql
ALTER TABLE task_groups ADD COLUMN role_specializations TEXT;
-- JSON: {"qa_expert": ["..."], "tech_lead": ["..."]}
```

### Phase 3: Fix DB Persistence

1. Add verification step in orchestrator after agent spawns
2. Update agent definitions with mandatory bazinga-db calls
3. Add PM success criteria persistence to DB

---

## Comparison to Alternatives

| Approach | Complexity | Backwards Compatible | Explicit Control | Auto-Enhancement |
|----------|------------|---------------------|-----------------|------------------|
| A: Per-Agent Arrays | High | No | Full | None |
| B: Auto-Augment | Low | Yes | None | Full |
| **C: Hybrid** | Medium | Yes | Partial | Partial |

**Why Solution C wins:**
- Doesn't break existing sessions
- QA Expert automatically benefits
- PM can still customize for edge cases
- Tech Stack Scout output feeds into augmentation (future enhancement)

---

## Decision Rationale

The current system has a **design gap**: templates are filtered by `compatible_with` but nothing ensures each agent type actually receives templates.

The hybrid approach fixes this by:
1. Respecting PM's base template selection
2. Auto-adding role-appropriate testing/review templates
3. Still allowing explicit PM override

This is the minimal change that solves the immediate problem while preserving system simplicity.

---

## Lessons Learned

1. **Agent compatibility filtering without fallbacks** leads to empty template sets
2. **Single specialization array** doesn't scale to multi-agent workflows
3. **DB persistence is not verified** - agents can skip mandatory steps
4. **Integration tests caught this** - validates the testing approach

---

## References

- Specialization-loader skill: `.claude/skills/specialization-loader/SKILL.md`
- Python template: `templates/specializations/01-languages/python.md`
- QA templates: `templates/specializations/08-testing/*.md`
- Task group schema: `.claude/skills/bazinga-db/references/schema.md`
