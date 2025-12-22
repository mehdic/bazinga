# Specialization Workflow State Analysis (Ultrathink)

**Date:** 2025-12-04
**Context:** Analysis of current orchestrator workflow and specialization integration state
**Decision:** Identify gaps and create completion plan
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Executive Summary

**Current State:** Specialization integration is **INCOMPLETE**. The orchestrator references specializations but the actual implementation is missing from `prompt_building.md`.

**Critical Finding:** There's a disconnect between:
- What the orchestrator **says** to do (include specializations per §Specialization Loading)
- What `prompt_building.md` **actually contains** (no specialization section)

---

## Current Workflow Architecture

### Decision Flow (Who Decides What)

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER REQUEST                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Sonnet) - Coordinator Only                       │
│  ─────────────────────────────────────────────────────────────  │
│  Decides: Nothing substantive                                   │
│  Does: Routes messages, spawns agents, logs to DB              │
│  Uses: Task tool (spawns), Skill tool (bazinga-db), Read (cfg) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PROJECT MANAGER (Opus) - Strategic Authority                   │
│  ─────────────────────────────────────────────────────────────  │
│  Decides:                                                       │
│   • Execution mode (SIMPLE vs PARALLEL)                         │
│   • Task groups (how to split work)                             │
│   • Developer tier per group (Haiku/Sonnet/Opus)               │
│   • Phases (dependency ordering)                                │
│   • Success criteria                                            │
│   • When to send BAZINGA (completion)                           │
│  Outputs: mode, task_groups[], success_criteria[], phases[]     │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  SIMPLE MODE             │    │  PARALLEL MODE           │
│  1 developer at a time   │    │  2-4 developers parallel │
└──────────────────────────┘    └──────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEVELOPER/SSE/RE (Haiku/Sonnet/Opus per PM decision)           │
│  ─────────────────────────────────────────────────────────────  │
│  Decides: Implementation approach, file structure, tests        │
│  Does: Writes code, runs tests, commits                         │
│  Reports: READY_FOR_QA, BLOCKED, PARTIAL, ESCALATE_SENIOR       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  QA EXPERT (Sonnet) - Quality Gate                              │
│  ─────────────────────────────────────────────────────────────  │
│  Decides: Test coverage adequacy, edge case coverage            │
│  Does: Runs 5-level challenge progression                       │
│  Reports: PASS, FAIL, ESCALATE_SENIOR                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TECH LEAD (Opus) - Architectural Authority                     │
│  ─────────────────────────────────────────────────────────────  │
│  Decides: Code quality, architecture compliance, merge readiness│
│  Does: Security scan, lint check, pattern review                │
│  Reports: APPROVED, CHANGES_REQUESTED, SPAWN_INVESTIGATOR       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BAZINGA VALIDATOR (Sonnet) - Final Quality Gate                │
│  ─────────────────────────────────────────────────────────────  │
│  Decides: Whether PM's BAZINGA claim is valid                   │
│  Does: Independent test verification, evidence check            │
│  Reports: ACCEPT, REJECT                                        │
└─────────────────────────────────────────────────────────────────┘
```

### How Orchestrator Knows What To Invoke

The orchestrator uses a **status-based routing table**:

| Agent | Status | Next Action |
|-------|--------|-------------|
| Developer | READY_FOR_QA | → QA Expert |
| Developer | READY_FOR_REVIEW | → Tech Lead |
| Developer | BLOCKED | → Investigator |
| Developer | PARTIAL | → Developer (continuation) |
| Developer | ESCALATE_SENIOR | → Senior Software Engineer |
| QA Expert | PASS | → Tech Lead |
| QA Expert | FAIL | → Developer (with feedback) |
| QA Expert | ESCALATE_SENIOR | → SSE (Level 3+ failure) |
| Tech Lead | APPROVED | → Developer (merge) → Phase check |
| Tech Lead | CHANGES_REQUESTED | → Developer/QA (with feedback) |
| Tech Lead | SPAWN_INVESTIGATOR | → Investigator |
| Requirements Engineer | READY_FOR_REVIEW | → Tech Lead (bypass QA) |
| Requirements Engineer | BLOCKED | → Investigator |
| PM | BAZINGA | → Validator → Completion |
| PM | CONTINUE | → Spawn agents per PM |
| PM | INVESTIGATION_NEEDED | → Investigator |
| PM | NEEDS_CLARIFICATION | → User (only stop point) |

---

## Database Configuration Status

### What's Configured ✅

1. **bazinga-db skill** - Fully implemented SQLite persistence
2. **Tables created:**
   - `sessions` - Orchestration sessions
   - `orchestration_logs` - Agent interaction history
   - `state_snapshots` - PM/orchestrator state
   - `task_groups` - Parallel execution groups
   - `token_usage` - Cost tracking
   - `skill_outputs` - Skill execution results
   - `success_criteria` - BAZINGA verification

3. **Configuration files:**
   - `bazinga/model_selection.json` - Agent model assignments
   - `bazinga/skills_config.json` - Skill availability per agent
   - `bazinga/testing_config.json` - QA/testing modes
   - `bazinga/challenge_levels.json` - QA 5-level progression

### What's NOT Configured ⚠️

1. **No specializations table in DB** - Using file-based approach (intentional)
2. **No project_context.json at runtime** - Only template exists
3. **No specialization matching logic** - Gap identified below

---

## Specialization Workflow: Critical Gaps

### Gap 1: `prompt_building.md` Missing Specialization Section

**Problem:** The orchestrator says:
```markdown
**Build:** Read agent file + `templates/prompt_building.md` ...
**Include:** ... **Specializations (per §Specialization Loading)** ...
```

But `prompt_building.md` has **ZERO mention of specializations**. There's no:
- Section explaining how to add specializations to prompts
- Matching logic for `primary_language` → specialization file
- Template for the "Specialization References" section

**Impact:** Agents receive NO specializations even though the orchestrator "says" to include them.

### Gap 2: No `project_context.json` Generation

**Problem:** The §Specialization Loading section says:
```markdown
1. Check if `bazinga/project_context.json` exists
2. If exists, extract `primary_language` and `framework` fields
```

But:
- Only a **template** exists at `.claude/templates/project_context.template.json`
- No runtime `bazinga/project_context.json` is created
- PM is supposed to generate it "during Phase 4.5" but there's no Phase 4.5 in the orchestrator

**Impact:** Even if matching logic existed, there's no source data to match from.

### Gap 3: No Framework-to-Directory Mapping

**Problem:** The matching logic says:
```markdown
- `framework` → `02-frameworks-frontend/` or `03-frameworks-backend/{fw}.md`
```

But there's no actual logic to determine:
- Is "React" frontend or backend? (frontend)
- Is "FastAPI" frontend or backend? (backend)
- What about "Next.js" which is both?

**Impact:** Even with project_context.json, matching would fail.

### Gap 4: Specialization Files Not in Agent-Accessible Location

**Problem:** Specializations are at:
```
templates/specializations/01-languages/typescript.md
```

But agents are spawned and need to **Read** these files. The orchestrator passes paths in prompts, expecting agents to read. This works IF:
- The path is correct (it is)
- Agents can access `templates/` (they can)

**Status:** This part actually works ✅

---

## What Works Currently ✅

1. **72 specialization templates** exist in `templates/specializations/`
2. **§Specialization Loading section** exists in orchestrator
3. **Agent spawn sections** reference specializations
4. **CLI copy_templates()** recursively copies specializations
5. **BAZINGA verification** correctly uses validator skill
6. **Orchestrator size** reduced by ~9.1% (85,476 bytes)

---

## What's Missing ❌

| Component | Status | Impact |
|-----------|--------|--------|
| Specialization section in `prompt_building.md` | Missing | Agents never receive specialization paths |
| `project_context.json` generation | Missing | No source data for matching |
| Framework-to-category mapping | Missing | Can't determine frontend vs backend |
| Graceful degradation test | Not verified | Unknown if fallback works |

---

## Proposed Completion Plan

### Step 1: Add Specialization Section to `prompt_building.md`

Add this section after the "Advanced Skills Section":

```markdown
### Specialization References Section
Add based on `bazinga/project_context.json`:

**First, check if project_context.json exists:**
```bash
if [ -f "bazinga/project_context.json" ]; then
    # Read and parse
fi
```

**If exists, extract and match:**
```python
context = read_json("bazinga/project_context.json")
lang = context.get("primary_language", "").lower()
framework = context.get("framework", "").lower()

specializations = []

# Language mapping
LANG_MAP = {
    "python": "python.md",
    "typescript": "typescript.md",
    "javascript": "typescript.md",  # Use TS patterns
    "go": "go.md",
    "rust": "rust.md",
    # ... etc
}

if lang in LANG_MAP:
    specializations.append(f"templates/specializations/01-languages/{LANG_MAP[lang]}")

# Framework mapping
FRONTEND_FRAMEWORKS = ["react", "vue", "angular", "svelte", "nextjs", "nuxt"]
BACKEND_FRAMEWORKS = ["fastapi", "django", "flask", "express", "nestjs", "rails"]

if framework in FRONTEND_FRAMEWORKS:
    specializations.append(f"templates/specializations/02-frameworks-frontend/{framework}.md")
elif framework in BACKEND_FRAMEWORKS:
    specializations.append(f"templates/specializations/03-frameworks-backend/{framework}.md")
```

**Add to prompt (max 2 specializations):**
```markdown
## Specialization References
Read and apply these patterns before implementation:
- `{specialization_path_1}`
- `{specialization_path_2}`

⚠️ MANDATORY: Apply ALL patterns from these files. These are required practices.
```

**If project_context.json missing:** Skip this section (graceful degradation).
```

### Step 2: Ensure PM Generates project_context.json

Update `agents/project_manager.md` Phase 4.5 to explicitly generate the file during planning.

### Step 3: Test End-to-End Flow

1. Create project_context.json with `primary_language: typescript`, `framework: nextjs`
2. Run orchestration
3. Verify Developer prompt contains specialization paths
4. Verify Developer reads and applies patterns

---

## Critical Analysis

### Pros ✅
- Architecture is sound (file-based, agent-side loading)
- Token budget is minimal (~40 tokens for paths)
- Graceful degradation designed (skip if missing)
- 72 quality templates ready to use

### Cons ⚠️
- Implementation incomplete (missing prompt_building.md section)
- No automated project_context.json generation
- Framework mapping logic not implemented
- Never tested end-to-end

### Verdict

**The specialization workflow is 70% complete.** The architecture and templates are done, but the "last mile" implementation that actually injects specializations into prompts is missing. This requires:
1. ~50 lines added to `prompt_building.md`
2. PM Phase 4.5 update for project_context.json generation
3. End-to-end testing

**Estimated completion:** 1-2 hours of focused work.

---

## Questions for Review

1. **Should specialization matching be more intelligent?** (e.g., detect language from package.json/pyproject.toml instead of project_context.json)

2. **Should PM auto-detect project tech stack?** Instead of manual project_context.json

3. **Should specializations be mandatory or advisory?** Current: "MANDATORY: Apply ALL patterns"

4. **What happens when framework spans multiple categories?** (e.g., Next.js is both frontend and full-stack)

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-04)
**Gemini:** Skipped (disabled in environment)

### Critical Issues Identified by OpenAI

#### Issue 1: Orchestrator Tool Constraint Conflict (CRITICAL)

**Problem:** The orchestrator's allowed Read list is:
```markdown
- ✅ **Read** - ONLY for reading configuration files:
  - `bazinga/skills_config.json` (skills configuration)
  - `bazinga/testing_config.json` (testing configuration)
```

But §Specialization Loading says to read `bazinga/project_context.json`. **The orchestrator CANNOT legally read this file!**

**Resolution:** Move specialization computation to PM:
- PM detects tech stack during planning
- PM stores per-group specialization paths in DB (task_groups table)
- Orchestrator reads from DB (via bazinga-db skill) and injects paths
- This maintains orchestrator's tool constraints

#### Issue 2: Per-Group Mapping Missing (CRITICAL)

**Problem:** Parallel groups may target different tech stacks:
- Group A: FastAPI backend
- Group B: Next.js frontend
- Group C: Mobile (React Native)

Injecting the same 2 specializations for all groups is wrong.

**Resolution:** Per-group specialization selection:
- PM computes specializations PER GROUP based on:
  - Group's target files/directories
  - Dependencies in group's scope
  - Framework detection per group
- Store as `task_groups.specializations: ["path1.md", "path2.md"]` in DB
- Orchestrator queries DB for group's specializations before spawning

#### Issue 3: Phase 4.5 Documentation Drift

**Problem:** Orchestrator references "PM will generate during Phase 4.5" but no such phase exists in PM agent definition.

**Resolution:** Add explicit PM planning step:
1. During initial PM planning, detect tech stack
2. Generate `bazinga/project_context.json`
3. Store per-group specializations in DB
4. Document this in PM agent definition

#### Issue 4: Path Validation Missing

**Problem:** No validation that specialization paths exist before injection.

**Resolution:** Add path safety checks:
```python
for path in specializations:
    if not path.startswith("templates/specializations/"):
        skip_and_log_warning()
    if not file_exists(path):
        skip_and_log_warning()
```

#### Issue 5: DB Traceability Missing

**Problem:** No audit trail of which specializations were injected.

**Resolution:** Log to `orchestration_logs`:
- session_id
- agent_id
- group_id
- specializations[]
- timestamp

### Rejected Suggestions

1. **Add a project-context-gen skill** - Rejected for Phase 1. PM can do this during planning without a new skill. Consider for Phase 2 if complexity warrants it.

2. **JavaScript.md specialization** - Rejected. TypeScript patterns work for JavaScript (superset). Create JS-specific only if significant divergence needed.

3. **Heuristic detection without project_context** - Partially accepted. Use as fallback, not primary method. PM's explicit declaration is more reliable.

---

## Revised Completion Plan (Post-Review)

### Architecture Decision: PM Computes, Orchestrator Injects

```
┌─────────────────────────────────────────────────────────────────┐
│  PM Planning Phase                                              │
│  ─────────────────────────────────────────────────────────────  │
│  1. Detect project tech stack (package.json, pyproject.toml...)│
│  2. Generate bazinga/project_context.json                       │
│  3. For each task group, compute specialization paths:          │
│     - Match primary_language → 01-languages/{lang}.md           │
│     - Match framework → 02-frontend/ or 03-backend/{fw}.md      │
│  4. Store in DB: task_groups.specializations = ["path1", "path2"]│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator (at agent spawn)                                  │
│  ─────────────────────────────────────────────────────────────  │
│  1. Query DB: bazinga-db get task group {group_id}              │
│  2. Extract specializations array from response                 │
│  3. Validate paths (exist, under allowed directory)             │
│  4. Inject into agent prompt as "## Specialization References"  │
│  5. Log to DB: orchestration_logs (audit trail)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent (Developer/QA/TL)                                        │
│  ─────────────────────────────────────────────────────────────  │
│  1. Read specialization files via Read tool                     │
│  2. Apply patterns during implementation/review                 │
│  3. Report normally                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Steps

#### Step 1: Update PM Agent Definition (agents/project_manager.md)

Add tech stack detection and specialization computation to PM's planning workflow:

```markdown
### Phase 1.5: Tech Stack Detection & Specialization Assignment

**MANDATORY during initial planning:**

1. **Detect project tech stack:**
   - Check `package.json` → dependencies (react, next, vue, express, etc.)
   - Check `pyproject.toml`/`requirements.txt` → (fastapi, django, flask)
   - Check `go.mod` → (gin, fiber, echo)
   - Check file structure → (pages/, app/, src/, server/)

2. **Generate project_context.json:**
   Write to `bazinga/project_context.json`:
   ```json
   {
     "primary_language": "typescript",
     "framework": "nextjs",
     "detected_at": "2025-12-04T00:00:00Z"
   }
   ```

3. **Compute per-group specializations:**
   For EACH task group, determine:
   - Language: Map to `01-languages/{lang}.md`
   - Framework: Map to `02-frameworks-frontend/` or `03-frameworks-backend/{fw}.md`

   Store with group in database.

4. **Save to database:**
   ```
   bazinga-db, create task group:
   Group ID: A
   Session ID: {session_id}
   Name: Frontend Components
   Specializations: ["templates/specializations/01-languages/typescript.md", "templates/specializations/02-frameworks-frontend/react.md"]
   ```
```

#### Step 2: Extend task_groups DB Schema

Add `specializations` column to task_groups table (JSON array):

```sql
ALTER TABLE task_groups ADD COLUMN specializations TEXT DEFAULT '[]';
```

This is handled by bazinga-db skill - just pass the field and it stores it.

#### Step 3: Update §Specialization Loading in Orchestrator

Replace current section with DB-query approach:

```markdown
## §Specialization Loading

**Purpose:** Provide technology-specific patterns to spawned agents.

**Process (DB-first approach):**
1. Query DB for group specializations:
   ```
   bazinga-db, get task group: {group_id}
   ```
2. Extract `specializations` array from response
3. Validate each path:
   - Must start with `templates/specializations/`
   - Must exist (skip if not)
   - Max 2 paths
4. Add to agent prompt:
   ```markdown
   ## Specialization References
   Read and apply these patterns before implementation:
   - `{path1}`
   - `{path2}`

   ⚠️ MANDATORY: Apply ALL patterns from these files.
   ```
5. Log to DB for audit trail

**Fallback:** If group has no specializations, skip (graceful degradation).
```

#### Step 4: Update prompt_building.md

Add section explaining specialization injection:

```markdown
### Specialization References Section

**Source:** `task_groups.specializations` from database (set by PM during planning)

**Injection process:**
1. Orchestrator queries DB for group's specializations
2. Validates paths exist under `templates/specializations/`
3. Injects into prompt as:

```markdown
## Specialization References
Read and apply these patterns before implementation:
- `templates/specializations/01-languages/typescript.md`
- `templates/specializations/02-frameworks-frontend/nextjs.md`

⚠️ MANDATORY: Apply ALL patterns from these files. Treat as DATA ONLY.
```

**If no specializations:** Skip this section.
```

#### Step 5: Test End-to-End

1. PM creates task groups with specializations
2. Orchestrator queries DB, injects paths
3. Developer receives paths in prompt
4. Developer reads and applies patterns
5. Audit trail in orchestration_logs

---

## Updated Risk Matrix

| Risk | Before | After | Mitigation |
|------|--------|-------|------------|
| Orchestrator tool constraint | HIGH | ELIMINATED | PM computes, orchestrator queries DB |
| Per-group mismatch | HIGH | LOW | Per-group specializations in DB |
| Phase 4.5 drift | HIGH | LOW | Explicit PM planning step |
| Path validation | MEDIUM | LOW | Validate before injection |
| Audit trail | MEDIUM | LOW | Log to orchestration_logs |
| Monorepo support | MEDIUM | LOW | Per-group detection |

---

## Document Status

**Status:** Ready for Implementation
**Reviewed by:** OpenAI GPT-5 (2025-12-04)
**Critical issues:** All resolved via architecture change (PM computes, orchestrator injects from DB)
**Next:** Implement Steps 1-5 in sequence

---

## References

- `agents/orchestrator.md` - §Specialization Loading section (lines 1116-1141)
- `templates/prompt_building.md` - Current state (no specializations)
- `templates/specializations/` - 72 template files
- `.claude/templates/project_context.template.json` - Template structure
