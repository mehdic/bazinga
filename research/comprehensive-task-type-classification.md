# Comprehensive Task Type Classification for Agent Routing

**Date:** 2025-12-02
**Context:** Expanding task-type routing beyond research/implementation to all task categories
**Decision:** Define complete task taxonomy with optimal agent routing for each type
**Status:** Reviewed and Revised
**Reviewed by:** OpenAI GPT-5 (2025-12-02)

---

## Executive Summary

The current BAZINGA implementation plan addresses **research vs implementation** task routing. This document expands the taxonomy to cover **ALL task types** that occur in software development, mapping each to the optimal agent based on required capabilities.

**Key Finding:** Most task types already have implicit routing through existing mechanisms (QA flow, Investigator for blockers, Tech Lead for review). The gap is primarily in **pre-execution classification** that the PM performs.

---

## Research Sources

### Academic Literature

1. [Classification of Task Types in Software Development Projects](https://www.mdpi.com/2079-9292/11/22/3827) - MDPI Electronics 2022
   - Task, bug, subtask as primary types
   - Stateful tasks comprise 90%+ of projects but only 40% of effort

2. [A Taxonomy for Software Testing Projects](https://ieeexplore.ieee.org/document/7170545/) - IEEE 2015
   - Planning, analysis, design, implementation, execution phases

3. [SEI Taxonomy of Testing](https://www.sei.cmu.edu/blog/a-taxonomy-of-testing-what-based-and-when-based-testing-types/) - CMU SEI
   - 200+ testing types organized by 5Ws and 2Hs

### Industry Best Practices

4. [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - Anthropic Research
   - Simple, composable patterns over complex frameworks
   - Routing as first-class workflow pattern

5. [Multi-LLM Routing Strategies](https://aws.amazon.com/blogs/machine-learning/multi-llm-routing-strategies-for-generative-ai-applications-on-aws/) - AWS ML Blog
   - Complexity-based routing (low/moderate/high)
   - Specialized classifier for task classification

6. [AI Agent Routing Best Practices](https://www.patronus.ai/ai-agent-development/ai-agent-routing) - Patronus AI
   - Task routing as separation of concerns
   - Specialized agents for distinct categories

7. [LLM-Based Multi-Agent Systems for Software Engineering](https://dl.acm.org/doi/10.1145/3712003) - ACM TOSEM 2025
   - Analyst → Coder → Tester pattern
   - Debugger with block-level tracking

---

## Complete Task Type Taxonomy

### Category 1: Research & Discovery

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **External Research** | Vendor/API/library evaluation | Requirements Engineer | Sonnet | `[R]`, "research", "evaluate", "select" |
| **Architecture Discovery** | Understanding existing system design | Requirements Engineer | Sonnet | "discover", "analyze architecture" |
| **Competitive Analysis** | Comparing approaches/tools | Requirements Engineer | Sonnet | "compare", "alternatives", "options" |

**Current Status:** ❌ Not implemented - addressed in task-type-routing-implementation-plan.md

**Key Capabilities Needed:**
- WebSearch, WebFetch for external info
- Deep reasoning for comparison/evaluation
- Structured deliverable output

---

### Category 2: Implementation

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **New Feature** | Building new functionality | Developer/SSE | Haiku/Sonnet | Default for code tasks |
| **Enhancement** | Extending existing features | Developer/SSE | Haiku/Sonnet | "extend", "add to", "improve" |
| **Integration** | Connecting systems/APIs | SSE | Sonnet | "integrate", "connect", API work |

**Current Status:** ✅ Implemented via complexity scoring (PM lines 79-116)

**Existing Mechanism:**
- Score 1-6 → Developer (Haiku)
- Score 7+ → SSE (Sonnet)
- Factors: file count, security, API, database, async

---

### Category 3: Debugging & Investigation

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Bug Fix (Simple)** | Clear symptoms, known location | Developer | Haiku | "fix bug", clear stack trace |
| **Bug Fix (Complex)** | Unclear cause, multiple systems | Investigator | Opus | Multi-file, no clear cause |
| **Root Cause Analysis** | Finding underlying issues | Investigator | Opus | "investigate", "why is", "root cause" |
| **Performance Debugging** | Identifying bottlenecks | Investigator | Opus | "slow", "memory leak", profiling |

**Current Status:** ⚠️ Partially implemented

**Existing Mechanism:**
- BLOCKED status → Investigator spawned
- INVESTIGATION_NEEDED → Investigator spawned

**Gap:** Simple bug fixes go to Developer regardless of diagnostic complexity. No pre-classification for "needs investigation" vs "straightforward fix".

---

### Category 4: Refactoring

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Code Smell Fix** | Extract method, rename, simplify | Developer | Haiku | "refactor", "clean up", "extract" |
| **Pattern Migration** | Moving to new architecture patterns | SSE | Sonnet | "migrate to", "adopt pattern" |
| **Large-Scale Restructure** | Major codebase reorganization | Tech Lead + SSE | Opus/Sonnet | Multiple modules, breaking changes |

**Current Status:** ⚠️ Treated as implementation

**Gap:** Refactoring requires understanding "why" (existing patterns) before "how" (new structure). Currently scored by file count, not reasoning depth.

---

### Category 5: Architecture & Design

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Component Design** | Designing new modules/services | Tech Lead | Opus | "design", "architect", new system |
| **API Design** | Endpoint structure, contracts | Tech Lead | Opus | "API design", "contract", "interface" |
| **System Integration Design** | How systems communicate | Tech Lead | Opus | "integration architecture" |

**Current Status:** ⚠️ No explicit pre-routing

**Existing Mechanism:**
- Tech Lead reviews ALL code (post-implementation)
- Tech Lead activated for ARCHITECTURAL_CONCERN

**Gap:** Architecture tasks should START with Tech Lead guidance, not just end with review.

---

### Category 6: Security

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Security Fix** | Patching vulnerabilities | SSE + Tech Lead | Sonnet/Opus | "vulnerability", "CVE", "security fix" |
| **Security Audit** | Reviewing for vulnerabilities | Tech Lead | Opus | "audit", "security review" |
| **Auth Implementation** | Authentication/authorization | SSE + Tech Lead | Sonnet/Opus | "auth", "OAuth", "permissions" |

**Current Status:** ⚠️ Partially implemented

**Existing Mechanism:**
- Security tasks get +2 complexity score
- Tech Lead reviews security-sensitive code
- security-scan skill available

**Gap:** Auth implementations should always start at SSE tier (not Developer) regardless of file count.

---

### Category 7: Database & Data

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Schema Migration** | Adding/modifying tables | SSE | Sonnet | "migration", "schema change" |
| **Query Optimization** | Improving DB performance | Investigator | Opus | "slow query", "N+1", "optimize DB" |
| **Data Transformation** | ETL, data processing | Developer/SSE | Haiku/Sonnet | "transform", "process data" |

**Current Status:** ⚠️ Partially implemented

**Existing Mechanism:**
- Database tasks get +2 complexity score

**Gap:** Schema migrations have high risk of data loss - should always include Tech Lead validation before execution.

---

### Category 8: Testing & Quality

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Unit Test Creation** | Writing unit tests | Developer | Haiku | "add tests", "unit test" |
| **Integration Test Creation** | E2E test scenarios | QA Expert | Sonnet | "integration test", "E2E" |
| **Test Coverage Improvement** | Filling coverage gaps | QA Expert | Sonnet | "improve coverage", "test gap" |

**Current Status:** ✅ Implemented via QA flow

**Existing Mechanism:**
- QA Expert handles all test-related tasks during QA phase
- test-coverage skill tracks coverage

---

### Category 9: Documentation

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **Code Documentation** | Inline docs, docstrings | Developer | Haiku | "document", "add comments" |
| **API Documentation** | OpenAPI, reference docs | Developer | Haiku | "API docs", "document endpoints" |
| **Architecture Docs** | System design docs | Tech Lead | Opus | "architecture doc", "design doc" |

**Current Status:** ⚠️ No explicit routing

**Gap:** Documentation is currently treated as low-complexity implementation. API docs could benefit from RE research mode to ensure accuracy.

---

### Category 10: DevOps & Infrastructure

| Task Type | Description | Primary Agent | Model | Triggers |
|-----------|-------------|---------------|-------|----------|
| **CI/CD Setup** | Pipeline configuration | SSE | Sonnet | "CI", "pipeline", "GitHub Actions" |
| **Infrastructure as Code** | Terraform, CloudFormation | SSE + Tech Lead | Sonnet/Opus | "infrastructure", "IaC", "terraform" |
| **Container Configuration** | Docker, K8s | Developer/SSE | Haiku/Sonnet | "docker", "container", "kubernetes" |

**Current Status:** ❌ Not explicitly handled

**Gap:** Infrastructure changes can have production impact - should require Tech Lead validation.

---

## Agent-Task Mapping Summary

### By Primary Agent

| Agent | Task Types | Model | Current Routing |
|-------|------------|-------|-----------------|
| **Developer** | Implementation (simple), Bug fix (simple), Refactor (simple), Docs (code), Unit tests | Haiku | Complexity 1-6 |
| **Senior Software Engineer** | Implementation (complex), Integration, Pattern migration, Security fixes, Schema migration, CI/CD | Sonnet | Complexity 7+ or escalation |
| **Requirements Engineer** | External research, Architecture discovery, Competitive analysis | Sonnet | NEW - not implemented |
| **Investigator** | Root cause analysis, Performance debugging, Complex bugs | Opus | BLOCKED status |
| **Tech Lead** | Architecture design, API design, Security audit, Large restructure, Infra validation | Opus | Always reviews, ARCHITECTURAL_CONCERN |
| **QA Expert** | Integration tests, Coverage improvement, Test scenarios | Sonnet | QA phase |
| **Project Manager** | Planning, Coordination, BAZINGA | Opus | Always involved |

### Capability Matrix

| Capability | Dev | SSE | RE | Investigator | TL | QA |
|------------|-----|-----|-----|--------------|-----|-----|
| Code writing | ✅ | ✅ | ❌ | ⚠️ | ⚠️ | ❌ |
| Deep reasoning | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| External research | ❌ | ❌ | ✅ | ✅ | ⚠️ | ❌ |
| Architectural decisions | ❌ | ⚠️ | ⚠️ | ⚠️ | ✅ | ❌ |
| Security expertise | ⚠️ | ✅ | ❌ | ⚠️ | ✅ | ⚠️ |
| Test creation | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Debugging | ⚠️ | ✅ | ❌ | ✅ | ⚠️ | ⚠️ |

Legend: ✅ Primary capability | ⚠️ Secondary/limited | ❌ Not applicable

---

## Gap Analysis

### What's Already Working

1. **Implementation routing** - Complexity scoring works well
2. **QA flow** - Test tasks handled properly
3. **Tech Lead review** - Always reviews, catches issues
4. **Investigator escalation** - BLOCKED → Investigator works

### What Needs Improvement

| Gap | Impact | Priority | Solution |
|-----|--------|----------|----------|
| **Research tasks to Haiku** | Wrong model for reasoning-heavy tasks | HIGH | Task-type classification (existing plan) |
| **Architecture tasks not pre-routed** | TL feedback comes late | MEDIUM | Add `architecture` task type |
| **Security tasks can go to Developer** | Risk if simple file count | MEDIUM | Override for security keywords |
| **Refactoring treated as implementation** | May need design thinking first | LOW | Add `refactor` task type |
| **Infrastructure has no TL gate** | Production risk | MEDIUM | Add `infrastructure` task type with TL validation |
| **Bug classification is binary** | Simple vs complex not distinguished | LOW | Add investigation detection |

---

## Proposed Task Type Expansion

### Phase 1: Core Types (Already Planned)

```python
TASK_TYPES = {
    "research": {
        "agent": "requirements_engineer",
        "model": "sonnet",
        "markers": ["[R]", "research", "evaluate", "select", "compare"],
        "phase": 1
    },
    "implementation": {
        "agent": "developer",  # or SSE based on complexity
        "model": "from_complexity_score",
        "markers": [],  # default
        "phase": 2
    }
}
```

### Phase 2: Safety-Critical Types (Recommended)

```python
TASK_TYPES_PHASE2 = {
    "security": {
        "agent": "senior_software_engineer",
        "model": "sonnet",
        "markers": ["security", "auth", "vulnerability", "CVE", "OAuth", "SAML"],
        "requires_tl_validation": True,
        "override_complexity": True  # Always SSE, never Developer
    },
    "architecture": {
        "agent": "tech_lead",  # TL provides guidance BEFORE implementation
        "model": "opus",
        "markers": ["[A]", "architect", "design system", "API design"],
        "output": "design_document",
        "followed_by": "implementation"
    },
    "infrastructure": {
        "agent": "senior_software_engineer",
        "model": "sonnet",
        "markers": ["terraform", "infrastructure", "CI/CD", "kubernetes", "docker"],
        "requires_tl_validation": True
    }
}
```

### Phase 3: Optimization Types (Future)

```python
TASK_TYPES_PHASE3 = {
    "investigation": {
        "agent": "investigator",
        "model": "opus",
        "markers": ["investigate", "root cause", "why is", "performance issue"],
        "note": "Only for pre-classified investigation, not post-BLOCKED"
    },
    "refactor": {
        "agent": "senior_software_engineer",
        "model": "sonnet",
        "markers": ["refactor", "restructure", "migrate pattern"],
        "requires_tl_guidance": True  # TL reviews plan before execution
    },
    "migration": {
        "agent": "senior_software_engineer",
        "model": "sonnet",
        "markers": ["migrate", "schema change", "database migration"],
        "requires_tl_validation": True,
        "requires_backup_verification": True
    }
}
```

---

## Implementation Impact on Existing Files

### Database Schema Change

Current CHECK constraint:
```sql
initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer'
```

Required expansion:
```sql
initial_tier TEXT CHECK(initial_tier IN (
    'developer',
    'senior_software_engineer',
    'requirements_engineer',
    'tech_lead',
    'investigator'
)) DEFAULT 'developer'
```

**Migration required:** Yes - ALTER TABLE with new CHECK constraint

### model_selection.json Changes

Add all agent entries (some may already exist):
```json
{
  "agents": {
    "developer": { "model": "haiku" },
    "senior_software_engineer": { "model": "sonnet" },
    "requirements_engineer": { "model": "sonnet" },
    "tech_lead": { "model": "opus" },
    "investigator": { "model": "opus" },
    "qa_expert": { "model": "sonnet" },
    "project_manager": { "model": "opus" },
    "validator": { "model": "sonnet" }
  },
  "task_type_routing": {
    "research": { "initial_tier": "requirements_engineer", "phase": 1 },
    "security": { "initial_tier": "senior_software_engineer", "requires_tl": true },
    "architecture": { "initial_tier": "tech_lead", "phase": 0 },
    "infrastructure": { "initial_tier": "senior_software_engineer", "requires_tl": true },
    "investigation": { "initial_tier": "investigator" },
    "implementation": { "initial_tier": "from_complexity" }
  }
}
```

### PM Changes (project_manager.md)

Add task-type detection section (~40 lines):

```markdown
## Task Type Classification (Before Complexity)

**Step 0: Classify task type before scoring complexity**

| Type | Markers | Initial Tier | Override |
|------|---------|--------------|----------|
| research | [R], research, evaluate, select, compare | requirements_engineer | Yes |
| security | security, auth, OAuth, vulnerability | senior_software_engineer | Yes |
| architecture | [A], architect, design system | tech_lead | Yes |
| infrastructure | terraform, CI/CD, kubernetes | senior_software_engineer | No |
| investigation | investigate, root cause, why is | investigator | Yes |
| implementation | (default) | from_complexity | No |

**Override = Yes:** Skip complexity scoring, always use this tier
**Override = No:** Apply complexity scoring after classification
```

### Orchestrator Changes (orchestrator.md)

Extend tier selection table (~3 lines added):
```markdown
| Tier | Agent File | Model |
|------|------------|-------|
| developer | agents/developer.md | haiku |
| senior_software_engineer | agents/senior_software_engineer.md | sonnet |
| requirements_engineer | agents/requirements_engineer.md | sonnet |
| tech_lead | agents/techlead.md | opus |
| investigator | agents/investigator.md | opus |
```

---

## Workflow Impact Analysis

### Simple Mode

**Before:**
```
PM → Developer/SSE (complexity) → QA → TL → PM
```

**After:**
```
PM → Type Classification
    → research: RE → PM (with findings)
    → architecture: TL (design doc) → Developer/SSE → QA → TL → PM
    → security: SSE → QA → TL (mandatory security check) → PM
    → implementation: Developer/SSE (complexity) → QA → TL → PM
```

### Parallel Mode

**Before:**
```
PM → [Dev A, Dev B, Dev C] parallel → QA per group → TL per group → PM
```

**After:**
```
PM → Phase 1: [RE, RE] parallel (max 2) → Findings
   → Phase 2: [Dev A, SSE B, Dev C] parallel (max 4) → QA → TL → PM
```

### Existing Workflows Preserved

- ✅ QA → Tech Lead → PM flow unchanged
- ✅ BAZINGA validation unchanged
- ✅ Investigator for BLOCKED unchanged
- ✅ Escalation rules unchanged
- ✅ MAX 4 parallel limit unchanged

---

## Risk Assessment

### High Risk

| Risk | Mitigation |
|------|------------|
| Token budget overflow (orchestrator near limit) | Keep PM changes surgical, move details to separate doc |
| Wrong task type classification | Prefer explicit markers [R], [A] over keyword detection |
| Breaking existing workflows | All new types are additive, defaults to implementation |

### Medium Risk

| Risk | Mitigation |
|------|------------|
| Tech Lead overwhelmed by architecture tasks | Architecture type should be rare (major design only) |
| Database migration failure | Test with empty DB first, add rollback script |
| PM output parsing breaks | Add backward compatibility for old format |

### Low Risk

| Risk | Mitigation |
|------|------------|
| Requirements Engineer prompt too long | Research mode is ~50 lines, RE has room |
| New agents not found | Add to MODEL_CONFIG and tier table |

---

## Recommended Implementation Order

### Phase 1 (Immediate - Already Planned)

1. **Research type** - Addresses the original problem
2. **Database migration** - Enable new tier values
3. **PM classification section** - Core routing logic

### Phase 2 (High Value - Security)

4. **Security type** - Safety-critical, always SSE + TL
5. **Infrastructure type** - Production safety

### Phase 3 (Medium Value - Design)

6. **Architecture type** - Better design outcomes
7. **Investigation type** - Earlier problem detection

### Phase 4 (Lower Priority - Optimization)

8. **Refactor type** - Nice to have
9. **Migration type** - Nice to have

---

## Questions for Discussion

1. **Should architecture tasks skip QA?** Design docs don't have tests. TL could review directly.

2. **Should security always require TL, or only for auth-related?** Current plan says always.

3. **How to handle mixed-type tasks?** E.g., "Research OAuth options and implement the chosen one"
   - Option A: PM splits into separate groups
   - Option B: Research phase feeds implementation phase (current plan)

4. **Should infrastructure tasks spawn different workflow?** E.g., require plan approval before execution.

5. **Is investigation type redundant with BLOCKED?** BLOCKED is reactive (after failure), investigation type is proactive (before implementation).

---

## Summary

| Category | Status | Priority | Agent Routing |
|----------|--------|----------|---------------|
| Research | Planned | HIGH | → RE (Sonnet) |
| Implementation | Done | - | → Dev/SSE (complexity) |
| Debugging (simple) | Done | - | → Dev (escalate if BLOCKED) |
| Debugging (complex) | Done | - | → Investigator (BLOCKED trigger) |
| Refactoring | Implicit | LOW | → SSE (high complexity) |
| Architecture | Missing | MEDIUM | → TL (design first) |
| Security | Partial | HIGH | → SSE + TL (always) |
| Testing | Done | - | → QA (QA phase) |
| Documentation | Implicit | LOW | → Dev (low complexity) |
| Infrastructure | Missing | MEDIUM | → SSE + TL (validation) |

**Key Takeaway:** The existing BAZINGA system handles most task types through complexity scoring and existing workflows. The main gaps are:
1. **Research tasks** (wrong agent - high priority)
2. **Security tasks** (need mandatory TL validation - high priority)
3. **Architecture tasks** (TL guidance before implementation - medium priority)
4. **Infrastructure tasks** (need TL validation - medium priority)

---

## References

- Current implementation plan: `research/task-type-routing-implementation-plan.md`
- Agent model selection strategy: `research/agent-model-selection-strategy.md`
- BAZINGA orchestrator: `agents/orchestrator.md`
- PM source: `agents/project_manager.md`

---

## Database and Workflow Impact Analysis

### Current Database Schema

**Schema Version:** 5 (requires v6 for task type routing)

**Affected Table:** `task_groups`

```sql
-- Current schema (init_db.py lines 293-312)
CREATE TABLE task_groups (
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN (
        'pending', 'in_progress', 'completed', 'failed',
        'approved_pending_merge', 'merging'
    )) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
    feature_branch TEXT,
    merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
    complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
    initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',  -- ⚠️ NEEDS MIGRATION
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, session_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
```

### Required Schema Migration (v5 → v6)

**Problem:** `initial_tier` CHECK constraint only allows `Developer` and `Senior Software Engineer`

**Solution:** Add new allowed values for task type routing

```sql
-- Migration to Schema v6
-- File: .claude/skills/bazinga-db/scripts/init_db.py

-- New CHECK constraint (replace line 307):
initial_tier TEXT CHECK(initial_tier IN (
    'developer',                    -- Standard implementation (Haiku)
    'senior_software_engineer',     -- Complex implementation (Sonnet)
    'requirements_engineer',        -- Research tasks (Sonnet) ← NEW
    'tech_lead',                    -- Architecture tasks (Opus) ← NEW
    'investigator'                  -- Investigation tasks (Opus) ← NEW
)) DEFAULT 'developer'

-- Also add new column for task type:
task_type TEXT CHECK(task_type IN (
    'research',
    'implementation',
    'security',
    'architecture',
    'infrastructure',
    'investigation'
)) DEFAULT 'implementation'

-- And execution phase for ordering:
execution_phase INTEGER DEFAULT 2  -- 0=pre-planning, 1=research, 2+=implementation
```

### Migration Script

**Location:** `.claude/skills/bazinga-db/scripts/init_db.py`
**Pattern:** Follow existing v4→v5 migration (lines 127-221)

```python
# Handle v5→v6 migration (task-type routing)
if current_version == 5:
    print("🔄 Migrating schema from v5 to v6...")

    # 1. Add task_type column to task_groups
    try:
        cursor.execute("ALTER TABLE task_groups ADD COLUMN task_type TEXT DEFAULT 'implementation'")
        print("   ✓ Added task_groups.task_type")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⊘ task_groups.task_type already exists")
        else:
            raise

    # 2. Add execution_phase column
    try:
        cursor.execute("ALTER TABLE task_groups ADD COLUMN execution_phase INTEGER DEFAULT 2")
        print("   ✓ Added task_groups.execution_phase")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ⊘ task_groups.execution_phase already exists")
        else:
            raise

    # 3. Recreate table with expanded initial_tier CHECK constraint
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='task_groups'")
    schema = cursor.fetchone()[0]

    if 'requirements_engineer' not in schema:
        print("   Recreating task_groups with expanded initial_tier enum...")

        cursor.execute("""
            CREATE TABLE task_groups_new (
                id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT CHECK(status IN (
                    'pending', 'in_progress', 'completed', 'failed',
                    'approved_pending_merge', 'merging'
                )) DEFAULT 'pending',
                assigned_to TEXT,
                revision_count INTEGER DEFAULT 0,
                last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
                feature_branch TEXT,
                merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
                complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
                initial_tier TEXT CHECK(initial_tier IN (
                    'developer', 'senior_software_engineer',
                    'requirements_engineer', 'tech_lead', 'investigator'
                )) DEFAULT 'developer',
                task_type TEXT CHECK(task_type IN (
                    'research', 'implementation', 'security',
                    'architecture', 'infrastructure', 'investigation'
                )) DEFAULT 'implementation',
                execution_phase INTEGER DEFAULT 2,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, session_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Copy existing data (map old tier names to new lowercase)
        cursor.execute("""
            INSERT INTO task_groups_new
            SELECT
                id, session_id, name, status, assigned_to, revision_count,
                last_review_status, feature_branch, merge_status, complexity,
                CASE initial_tier
                    WHEN 'Developer' THEN 'developer'
                    WHEN 'Senior Software Engineer' THEN 'senior_software_engineer'
                    ELSE 'developer'
                END,
                'implementation',  -- default task_type for existing data
                2,                 -- default execution_phase
                created_at, updated_at
            FROM task_groups
        """)

        cursor.execute("DROP TABLE task_groups")
        cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")
        cursor.execute("CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status)")
        cursor.execute("CREATE INDEX idx_taskgroups_type ON task_groups(session_id, task_type)")

        print("   ✓ Recreated task_groups with expanded initial_tier enum")

    print("✓ Migration to v6 complete (task-type routing)")
```

### Schema Documentation Update

**File:** `.claude/skills/bazinga-db/references/schema.md`

Add to `task_groups` section:
```markdown
#### New Columns (v6)

| Column | Type | Description |
|--------|------|-------------|
| `task_type` | TEXT | Type of task (research, implementation, security, etc.) |
| `execution_phase` | INTEGER | Execution order (0=pre-planning, 1=research, 2+=implementation) |

#### Initial Tier Values (v6)

| Value | Agent | Model | Use Case |
|-------|-------|-------|----------|
| `developer` | Developer | Haiku | Standard implementation (complexity 1-6) |
| `senior_software_engineer` | SSE | Sonnet | Complex implementation (complexity 7+) |
| `requirements_engineer` | RE | Sonnet | Research and evaluation tasks |
| `tech_lead` | Tech Lead | Opus | Architecture and design tasks |
| `investigator` | Investigator | Opus | Root cause analysis, complex debugging |
```

### Workflow Impact by Task Type

#### Research Tasks (`task_type: research`)

```
Before (Current - Broken):
  PM → Developer (Haiku) → QA → TL → PM

After (Fixed):
  PM → Requirements Engineer (Sonnet) → Orchestrator (checks deliverable) → Implementation
```

**Database Changes:**
- `initial_tier`: 'requirements_engineer'
- `task_type`: 'research'
- `execution_phase`: 1

**Workflow Impact:**
- Research groups execute in Phase 1 (before implementation)
- No QA phase for research (produces document, not code)
- Tech Lead may optionally review critical research decisions
- Deliverable stored in `bazinga/artifacts/{session}/research_{group_id}.md`

#### Security Tasks (`task_type: security`)

```
Before (Current - Risky):
  PM → Developer OR SSE (based on file count) → QA → TL → PM

After (Safer):
  PM → SSE (always Sonnet) → QA → TL (mandatory security review) → PM
```

**Database Changes:**
- `initial_tier`: 'senior_software_engineer' (always)
- `task_type`: 'security'
- `execution_phase`: 2

**Workflow Impact:**
- Always starts at SSE tier regardless of complexity score
- Tech Lead security review is mandatory (not optional)
- security-scan skill invoked during QA phase

#### Architecture Tasks (`task_type: architecture`)

```
Before (Current - Late Feedback):
  PM → Developer/SSE → QA → TL (catches design issues late) → PM

After (Early Design):
  PM → Tech Lead (design doc) → Developer/SSE (implementation) → QA → TL → PM
```

**Database Changes:**
- `initial_tier`: 'tech_lead'
- `task_type`: 'architecture'
- `execution_phase`: 0 (before research)

**Workflow Impact:**
- Tech Lead produces design document first
- Implementation groups depend on architecture group
- Two TL touchpoints: initial design + final review

#### Investigation Tasks (`task_type: investigation`)

```
Before (Current - Reactive):
  PM → Developer → BLOCKED → Investigator → Developer continues

After (Proactive):
  PM → Investigator (pre-assigned) → Findings → Developer uses findings
```

**Database Changes:**
- `initial_tier`: 'investigator'
- `task_type`: 'investigation'
- `execution_phase`: 1 (with research)

**Workflow Impact:**
- Investigation starts proactively (not waiting for BLOCKED)
- Findings inform implementation approach
- Can run parallel with research tasks

### Other Workflows - NO IMPACT

The following workflows remain **completely unchanged**:

| Workflow | Status | Reason |
|----------|--------|--------|
| QA → Tech Lead → PM flow | ✅ Unchanged | Task type doesn't affect review flow |
| BAZINGA validation | ✅ Unchanged | PM still signals completion |
| Escalation (Dev → SSE) | ✅ Unchanged | Complexity-based escalation preserved |
| Investigator for BLOCKED | ✅ Unchanged | BLOCKED trigger still works |
| MAX 4 parallel limit | ✅ Unchanged | Applies to all task types |
| Feature branch per group | ✅ Unchanged | Branch strategy unchanged |
| Merge-on-approval | ✅ Unchanged | Merge flow unchanged |

### Dashboard Impact

**File:** `dashboard-v2/server.py`

Dashboard displays task groups with their status. New columns need UI support:

```python
# Current task group display (line ~614)
# May need to show task_type and execution_phase

# Suggested addition:
def format_task_group(group):
    type_emoji = {
        'research': '🔍',
        'implementation': '🔨',
        'security': '🔒',
        'architecture': '📐',
        'infrastructure': '🏗️',
        'investigation': '🔬'
    }
    return f"{type_emoji.get(group['task_type'], '📋')} {group['name']}"
```

**Impact Level:** LOW - Dashboard enhancement, not breaking change

### Rollback Strategy

If migration causes issues:

1. **Quick rollback** (no data loss):
   ```sql
   -- Revert initial_tier values to old format
   UPDATE task_groups SET initial_tier = 'Developer' WHERE initial_tier IN ('developer', 'requirements_engineer', 'investigator');
   UPDATE task_groups SET initial_tier = 'Senior Software Engineer' WHERE initial_tier = 'senior_software_engineer';
   UPDATE task_groups SET initial_tier = 'Senior Software Engineer' WHERE initial_tier = 'tech_lead';
   ```

2. **Full rollback** (restore backup):
   ```bash
   # Backup is created automatically before migration
   cp bazinga/bazinga.db.backup.v5 bazinga/bazinga.db
   ```

3. **Schema version reset**:
   ```sql
   UPDATE schema_version SET version = 5 WHERE version = 6;
   ```

### Testing the Migration

```bash
# 1. Create test database
python3 .claude/skills/bazinga-db/scripts/init_db.py /tmp/test_bazinga.db

# 2. Verify schema
sqlite3 /tmp/test_bazinga.db ".schema task_groups"

# 3. Test constraint allows new values
sqlite3 /tmp/test_bazinga.db "INSERT INTO task_groups (id, session_id, name, initial_tier, task_type) VALUES ('test', 'sess_001', 'Test Research', 'requirements_engineer', 'research');"

# 4. Verify insert
sqlite3 /tmp/test_bazinga.db "SELECT * FROM task_groups WHERE id='test';"

# 5. Cleanup
rm /tmp/test_bazinga.db
```

### Summary: Database Changes Required

| Change | File | Lines | Risk |
|--------|------|-------|------|
| Add `task_type` column | init_db.py | ~5 | LOW |
| Add `execution_phase` column | init_db.py | ~5 | LOW |
| Expand `initial_tier` CHECK constraint | init_db.py | ~20 | MEDIUM |
| Add migration v5→v6 handler | init_db.py | ~60 | MEDIUM |
| Update schema.md documentation | schema.md | ~30 | LOW |
| Update SCHEMA_VERSION constant | init_db.py | 1 | LOW |

**Total: ~120 lines of database changes**

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 on 2025-12-02
**Gemini:** Skipped (ENABLE_GEMINI=false)

### Critical Issues Identified by GPT-5

GPT-5 identified **6 critical issues** that require plan revision:

| # | Issue | Severity | Resolution |
|---|-------|----------|------------|
| 1 | **Tech Lead/Investigator as initial tier breaks orchestrator** - Orchestrator expects TL to review code, not produce deliverables. Investigator only supported in investigation loop. | CRITICAL | **REVISED**: Remove TL/Investigator as initial tiers. Use architecture-as-research + TL validation instead |
| 2 | **Requirements Engineer tool mismatch** - RE explicitly forbids Skills and web access, but research mode depends on WebSearch/WebFetch | CRITICAL | **REVISED**: Phase 1 uses codebase-only discovery. Web research optional in Phase 2 with explicit RE update |
| 3 | **Risky DB schema changes** - Changing initial_tier casing ('Developer' → 'developer') breaks backward compatibility | HIGH | **REVISED**: NO DB schema changes in Phase 1. Store task_type in PM state only |
| 4 | **Unaligned phase management** - Two sources of truth: task_groups.execution_phase vs PM.state.execution_phases | HIGH | **REVISED**: Use PM.state.execution_phases exclusively. No new DB column |
| 5 | **New statuses not wired** - RESEARCH_COMPLETE not in orchestrator's routing tables | HIGH | **REVISED**: Reuse existing READY_FOR_REVIEW status with deliverable path |
| 6 | **Token budget risk** - orchestrator.md and project_manager.md near limits | MEDIUM | **REVISED**: Minimal changes to large files. ~10 lines each max |

### Major Plan Revision: Minimal Viable Routing

**BEFORE (Original Plan - Over-scoped):**
```
- 6 task types (research, security, architecture, infrastructure, investigation, implementation)
- 5 initial_tier values in DB (developer, sse, re, tl, investigator)
- New DB columns (task_type, execution_phase)
- New status codes (RESEARCH_COMPLETE, RESEARCH_BLOCKED)
- ~120 lines of DB changes
- ~100+ lines of orchestrator changes
```

**AFTER (Revised Plan - Minimal Risk):**
```
Phase 1 (Immediate):
- 1 task type: "research" only
- NO DB changes
- Store task_type in PM.state.task_groups[i] only
- Reuse existing status: READY_FOR_REVIEW with deliverable link
- ~25 lines PM changes, ~10 lines orchestrator changes

Phase 2 (After Phase 1 success):
- Add "security" as PM state flag (security_sensitive: true)
- Force SSE tier + mandatory TL review
- NO DB changes

Phase 3 (Future, if needed):
- Architecture as research type + TL validation
- Consider DB metadata column if persistence needed
```

### Revised Task Type Routing

#### Phase 1: Research Only (NO DB CHANGES)

**PM State Extension (NOT Database):**
```json
{
  "task_groups": [
    {
      "id": "R1",
      "name": "OAuth Provider Research [R]",
      "type": "research",  // NEW field in PM state only
      "initial_tier": "developer",  // Keep as 'developer' in DB
      "deliverable": "bazinga/artifacts/{session}/research_R1.md"
    },
    {
      "id": "A",
      "name": "Implement OAuth",
      "type": "implementation",  // Default
      "initial_tier": "developer",
      "depends_on": ["R1"]
    }
  ],
  "execution_phases": [
    {"phase": 1, "groups": ["R1"], "type": "research"},
    {"phase": 2, "groups": ["A"], "type": "implementation"}
  ]
}
```

**Orchestrator Routing (Minimal Change):**
```python
# When spawning, check PM.state.task_groups[i].type
if task_type == "research":
    # Override DB tier to spawn RE instead
    agent = "requirements_engineer"
    model = MODEL_CONFIG["requirements_engineer"]  # sonnet
else:
    # Use existing tier-based spawning
    agent = tier_to_agent[initial_tier]
    model = MODEL_CONFIG[agent]
```

**Status Flow (Reuse Existing):**
```
RE → READY_FOR_REVIEW (with deliverable link)
   → TL → APPROVED/CHANGES_REQUESTED
   → PM proceeds to implementation phase
```

#### Phase 2: Security Override (NO DB CHANGES)

**PM State Flag:**
```json
{
  "task_groups": [
    {
      "id": "AUTH",
      "name": "Implement OAuth Login",
      "security_sensitive": true,  // NEW flag in PM state
      "initial_tier": "senior_software_engineer"  // PM always assigns SSE for security
    }
  ]
}
```

**Orchestrator Check:**
```python
# After TL review, check security flag
if task_group.get("security_sensitive"):
    # Ensure TL approved before PM marks complete
    require_tl_approval = True
```

#### Phase 3: Architecture as Research (Future)

**Treat architecture tasks as research type:**
```json
{
  "task_groups": [
    {
      "id": "ARCH1",
      "name": "API Design [R]",  // Mark as research
      "type": "research",
      "initial_tier": "developer",  // Override to spawn RE
      "deliverable": "bazinga/artifacts/{session}/design_ARCH1.md"
    }
  ]
}
```

**Then route RE output to TL for validation, then spawn implementation groups.**

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| "Add metadata JSON column to DB" | Adds complexity; PM state is sufficient for Phase 1 |
| "Use generic 'research' agent" | RE already exists and has discovery capabilities |
| "Skip TL validation for research" | Research decisions need review; TL is appropriate validator |
| "Add all 6 task types immediately" | Too much risk; incremental rollout is safer |

### Incorporated Feedback

1. **No DB schema changes in Phase 1** ✅
   - Store task_type in PM.state only
   - Keep initial_tier values unchanged in DB

2. **Reuse existing statuses** ✅
   - READY_FOR_REVIEW for research deliverables
   - APPROVED/CHANGES_REQUESTED from TL

3. **Keep TL/Investigator in existing roles** ✅
   - TL reviews, doesn't produce
   - Investigator for BLOCKED only

4. **Architecture as research + TL validation** ✅
   - Not a separate task type
   - Research deliverable → TL review → implementation

5. **Security as PM state flag** ✅
   - security_sensitive: true
   - Forces SSE + mandatory TL review

6. **Single source of phase truth** ✅
   - PM.state.execution_phases only
   - No task_groups.execution_phase column

7. **Offline fallback for research** ✅
   - Phase 1: codebase-only discovery (RE current capability)
   - Phase 2: Optional web research with explicit RE update

### Revised Implementation Order

#### Phase 1: Research Routing (Immediate - Low Risk)

**Files Changed:**
| File | Lines Added | Change |
|------|-------------|--------|
| project_manager.md | ~25 | Task type classification section |
| orchestrator.md | ~10 | Type check in spawn logic |
| model_selection.json | ~4 | Add requirements_engineer entry |

**Total: ~40 lines** (down from ~250+ in original plan)

**No DB changes. No new status codes. No skill additions.**

#### Phase 2: Security Override (After Phase 1 Success)

**Files Changed:**
| File | Lines Added | Change |
|------|-------------|--------|
| project_manager.md | ~10 | Security sensitive flag |
| orchestrator.md | ~5 | TL review enforcement |

**Total: ~15 lines**

#### Phase 3: Architecture Support (Future)

**Treat as research type - no additional infrastructure needed.**

### Confidence Level

**High** after revisions:
- ✅ No DB schema changes (major risk eliminated)
- ✅ Reuses existing status codes (no parsing changes)
- ✅ Minimal orchestrator changes (~10 lines)
- ✅ Single source of phase truth (PM.state)
- ✅ TL/Investigator roles preserved
- ✅ Offline-compatible (codebase-only discovery)

### Updated Summary

| Category | Phase | Approach | DB Change |
|----------|-------|----------|-----------|
| Research | 1 | PM state type + RE spawn override | NO |
| Security | 2 | PM state flag + TL enforcement | NO |
| Architecture | 3 | Research type + TL validation | NO |
| Infrastructure | Future | Security-like flag | NO |
| Investigation | Future | Keep for BLOCKED only | NO |
| Implementation | Current | Unchanged | NO |

**Key Insight from GPT-5 Review:** The original plan was over-scoped. Most of the value (fixing research task routing) can be achieved with minimal changes by storing task_type in PM state and overriding spawn logic, without touching the database schema or adding new status codes.
