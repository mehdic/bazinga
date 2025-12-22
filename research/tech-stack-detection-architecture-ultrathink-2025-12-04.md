# Tech Stack Detection Architecture: Ultrathink Analysis

**Date:** 2025-12-04
**Context:** Designing who should detect project tech stack for specialization loading
**Decision:** Split mechanical detection (Sonnet agent) from intelligent assignment (PM)
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

We need to detect a project's tech stack to load appropriate specializations. This involves:

1. **Detection** (mechanical): What languages/frameworks/tools exist in this project?
2. **Assignment** (intelligent): Which specializations should each task group use?

### Complexity of Detection

| Category | Count | Detection Source |
|----------|-------|------------------|
| Languages | 15 | File extensions, package files |
| Frontend Frameworks | 8 | package.json dependencies |
| Backend Frameworks | 10 | package.json, pyproject.toml, go.mod |
| Databases | 7 | Dependencies, config files, docker-compose |
| Mobile/Desktop | 4 | Package files, project structure |
| Infrastructure | 5 | Config files (Dockerfile, k8s, terraform) |
| Testing | 4 | Dev dependencies |
| Messaging/APIs | 4 | Dependencies, schema files |

### Hard Cases

1. **Monorepos**: `/frontend` (React+TS), `/backend` (FastAPI+Python), `/mobile` (React Native)
2. **Full-stack frameworks**: Next.js has both frontend and API routes
3. **Multiple languages**: Go microservices + Python ML + TS gateway
4. **Legacy + Modern**: JS being migrated to TS
5. **Implicit frameworks**: No explicit dep but using patterns (e.g., REST without OpenAPI)

---

## Proposed Architecture

### Two-Phase Approach

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Tech Stack Scout (Sonnet, Plan Mode)                  │
│  ─────────────────────────────────────────────────────────────  │
│  WHEN: Step 0.5 of orchestration (before PM)                    │
│  WHO: Sonnet agent in plan mode (read-only, no implementation)  │
│  WHAT: Deep analysis of project structure                       │
│  OUTPUT: bazinga/project_context.json (comprehensive)           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: PM Planning (Opus)                                    │
│  ─────────────────────────────────────────────────────────────  │
│  WHEN: Step 1 of orchestration                                  │
│  WHO: Project Manager (Opus)                                    │
│  WHAT: Use pre-analyzed context to assign specializations       │
│  OUTPUT: Per-group specializations in DB                        │
└─────────────────────────────────────────────────────────────────┘
```

### Why Sonnet in Plan Mode?

| Aspect | Haiku | Sonnet | Sonnet (Plan Mode) | Opus |
|--------|-------|--------|-------------------|------|
| Cost | $ | $$ | $$ | $$$$ |
| Accuracy | Low | High | High | Highest |
| Speed | Fast | Medium | Medium | Slow |
| Can read files | Yes | Yes | Yes | Yes |
| Can implement | Yes | Yes | No (plan only) | Yes |
| Deep analysis | Limited | Good | Good | Excellent |

**Sonnet in Plan Mode** is ideal because:
- **Accurate enough** for complex detection (monorepos, edge cases)
- **Cost-effective** compared to Opus
- **Read-only** - can't accidentally modify anything
- **Focused** - plan mode forces analysis without action

### Tech Stack Scout Agent Specification

**Identity:** Tech Stack Scout
**Model:** Sonnet (plan mode)
**Role:** Analyze project structure and output comprehensive tech context

**Capabilities:**
- Read any file in project (package.json, pyproject.toml, go.mod, etc.)
- Analyze directory structure
- Parse dependency files
- Identify patterns and conventions
- Output structured JSON

**Constraints:**
- Plan mode only (no edits, no bash commands)
- Single spawn at orchestration start
- Must complete before PM spawns
- Output to `bazinga/project_context.json`

### Output Format: project_context.json

```json
{
  "detected_at": "2025-12-04T12:00:00Z",
  "confidence": "high",

  "primary_language": "typescript",
  "secondary_languages": ["python", "sql"],

  "structure": "monorepo",
  "components": [
    {
      "path": "frontend/",
      "type": "frontend",
      "language": "typescript",
      "framework": "nextjs",
      "testing": ["jest", "playwright"],
      "suggested_specializations": [
        "01-languages/typescript.md",
        "02-frameworks-frontend/nextjs.md"
      ]
    },
    {
      "path": "backend/",
      "type": "backend",
      "language": "python",
      "framework": "fastapi",
      "database": "postgresql",
      "testing": ["pytest"],
      "suggested_specializations": [
        "01-languages/python.md",
        "03-frameworks-backend/fastapi.md"
      ]
    },
    {
      "path": "mobile/",
      "type": "mobile",
      "language": "typescript",
      "framework": "react-native",
      "suggested_specializations": [
        "01-languages/typescript.md",
        "04-mobile-desktop/react-native.md"
      ]
    }
  ],

  "infrastructure": {
    "containerization": "docker",
    "orchestration": "kubernetes",
    "ci_cd": "github-actions"
  },

  "global_specializations": [
    "06-infrastructure/docker.md",
    "06-infrastructure/github-actions.md"
  ],

  "detection_notes": [
    "Next.js detected via next.config.js and package.json",
    "FastAPI detected via pyproject.toml dependencies",
    "Monorepo structure detected via multiple package.json files"
  ]
}
```

### PM's Role (Simplified)

PM no longer does detection. PM reads `project_context.json` and:

1. **Maps task groups to components:**
   - "Implement login UI" → targets `frontend/` → use frontend specializations
   - "Add auth API" → targets `backend/` → use backend specializations

2. **Stores per-group specializations in DB:**
   ```
   Group A: ["typescript.md", "nextjs.md"]
   Group B: ["python.md", "fastapi.md"]
   ```

3. **Can override suggestions:**
   - Scout suggests `react.md` but PM knows task needs `nextjs.md` specifically

---

## Critical Analysis

### Pros ✅

1. **Separation of concerns** - Detection is mechanical, assignment is intelligent
2. **Cost-effective** - Sonnet ($) vs Opus ($$$$) for detection
3. **Accurate** - Sonnet handles complex cases (monorepos, edge cases)
4. **Safe** - Plan mode prevents accidental modifications
5. **Reusable** - project_context.json useful beyond specializations
6. **PM focus** - PM focuses on planning, not file parsing
7. **One-time cost** - Scout runs once per session

### Cons ⚠️

1. **Extra agent spawn** - Adds one Sonnet call at start
2. **Sequential dependency** - PM must wait for Scout to complete
3. **Potential redundancy** - PM might re-read some files anyway
4. **New agent to maintain** - Another agent definition to keep updated
5. **Failure handling** - What if Scout fails or times out?

### Trade-offs

| Trade-off | Decision | Rationale |
|-----------|----------|-----------|
| Cost vs Accuracy | Sonnet (not Haiku) | Detection complexity requires accuracy |
| Speed vs Completeness | Complete analysis | One-time cost, reused throughout session |
| New agent vs PM extension | New agent | Clean separation, PM already large |

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scout timeout | LOW | MEDIUM | Set reasonable timeout (2 min), fallback to minimal context |
| Scout inaccuracy | LOW | LOW | PM can override suggestions |
| Scout failure | LOW | MEDIUM | Graceful degradation - proceed without specializations |
| Increased latency | MEDIUM | LOW | ~30s added to orchestration start (acceptable) |

---

## Alternatives Considered

### Alternative 1: PM Does Everything

**Approach:** PM detects AND assigns in one phase
**Pros:** Simpler, one agent
**Cons:** PM already complex, expensive (Opus), mixes concerns
**Verdict:** Rejected - PM should focus on planning

### Alternative 2: Extend codebase-analysis Skill

**Approach:** Existing skill outputs project_context.json
**Pros:** Reuses existing code, no new agent
**Cons:** Skill is for codebase patterns, not tech detection; different purpose
**Verdict:** Rejected - purpose mismatch

### Alternative 3: Haiku Detection Agent

**Approach:** Cheap Haiku agent does detection
**Pros:** Very cheap
**Cons:** May miss edge cases (monorepos, full-stack frameworks)
**Verdict:** Rejected - accuracy more important than cost savings

### Alternative 4: Orchestrator Detection (Extended Permissions)

**Approach:** Orchestrator reads files directly
**Pros:** No extra spawn
**Cons:** Violates orchestrator's coordinator role, scope creep
**Verdict:** Rejected - orchestrator shouldn't analyze

---

## Implementation Plan

### Step 1: Create Tech Stack Scout Agent

Create `agents/tech_stack_scout.md`:
- Define role and constraints
- Specify detection algorithm
- Define output format
- Include examples for edge cases

### Step 2: Update Orchestrator Step 0

Add Step 0.5 before PM spawn:
```markdown
### Step 0.5: Tech Stack Detection

1. Spawn Tech Stack Scout (Sonnet, plan mode)
2. Scout analyzes project, outputs bazinga/project_context.json
3. If Scout fails/times out: proceed with empty context (graceful degradation)
4. Continue to Step 1: Spawn PM
```

### Step 3: Update PM to Use Context

PM reads `project_context.json` and uses it for:
- Understanding project structure
- Assigning specializations per task group
- Can override Scout's suggestions based on task requirements

### Step 4: Test Scenarios

- Simple project (single language/framework)
- Monorepo (multiple components)
- Full-stack framework (Next.js)
- Legacy + modern mix
- Scout failure (graceful degradation)

---

## Questions for Review

1. **Should Scout be a dedicated agent or a skill?**
   - Agent: More flexible, can handle complex cases
   - Skill: Lighter weight, but less capable

2. **What's the right timeout for Scout?**
   - 1 minute? 2 minutes? Should be fast but thorough

3. **Should Scout's suggestions be binding or advisory?**
   - Current proposal: Advisory (PM can override)

4. **How detailed should project_context.json be?**
   - Current: Rich (components, infrastructure, notes)
   - Alternative: Minimal (just language/framework)

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-04)
**Gemini:** Skipped (disabled in environment)

### User Decisions on Suggested Changes

| Suggestion | User Decision | Notes |
|------------|---------------|-------|
| Scout sole writer of project_context.json | ✅ APPROVED | PM reads only, doesn't overwrite |
| Register in DB as context package | ✅ APPROVED | For discoverability and resume support |
| Backward-compatible schema | ❌ REJECTED | Create migration script for old data instead |
| Max-2 specialization limit | ❌ REJECTED | As many specializations as needed |
| Performance safeguards (ignore globs) | ✅ APPROVED | Ignore node_modules, .git, venv, etc. |
| Tool whitelist for Scout | ✅ APPROVED | Read, Glob, Grep only |
| Timeout/fallback | ✅ APPROVED | 2 min timeout, proceed with minimal on failure |
| Evidence trail | ✅ APPROVED | Include file paths as proof |

### Incorporated Changes

1. **Scout is sole writer** - PM will NOT generate project_context.json if Scout already created it
2. **DB registration** - Detection output registered as context package in bazinga-db
3. **New schema only** - Rich schema with components[], no backward compatibility needed (migration script handles old data)
4. **No specialization limit** - PM can assign as many specializations as task requires
5. **Performance safeguards** - Scout ignores: node_modules, .git, venv, dist, build, coverage, *.lock
6. **Tool constraints** - Scout allowed: Read, Glob, Grep. Forbidden: Edit, Write, Bash
7. **Timeout handling** - 2 minute timeout, fallback to minimal context on failure
8. **Evidence** - Each detection includes file path + dependency key as proof

### Rejected Suggestions

1. **Backward-compatible schema** - User prefers clean new schema + migration script over dual-format
2. **Max-2 limit** - User wants flexibility for complex projects that need more specializations

---

## Final Architecture (Post-Approval)

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 0.5: Tech Stack Scout (Sonnet, Plan Mode)                 │
│  ─────────────────────────────────────────────────────────────  │
│  Tools: Read, Glob, Grep only                                   │
│  Ignores: node_modules, .git, venv, dist, build, *.lock         │
│  Timeout: 2 minutes (fallback to minimal on failure)            │
│  Output: bazinga/project_context.json (rich schema)             │
│  DB: Register as context package for discoverability            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: PM Planning (Opus)                                     │
│  ─────────────────────────────────────────────────────────────  │
│  Reads: project_context.json (does NOT overwrite)               │
│  Decides: Per-group specializations (no limit on count)         │
│  Stores: task_groups.specializations in DB                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2+: Orchestrator (at agent spawn)                         │
│  ─────────────────────────────────────────────────────────────  │
│  Queries: DB for group's specializations                        │
│  Validates: Paths exist under templates/specializations/│
│  Injects: Into agent prompt                                     │
│  Logs: To orchestration_logs for audit trail                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document Status

**Status:** Ready for Implementation
**Reviewed by:** OpenAI GPT-5 (2025-12-04)
**User Approved:** 2025-12-04
**Next:** Create Tech Stack Scout agent, update orchestrator Step 0.5

---

## References

- `templates/specializations/` - 72 specialization templates
- `research/specialization-workflow-state-ultrathink-2025-12-04.md` - Previous analysis
- `agents/orchestrator.md` - Current orchestrator workflow
