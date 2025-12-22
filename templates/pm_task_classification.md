# PM Task Classification Reference

**This file is referenced by the Project Manager agent. Do not modify without updating the PM agent.**

---

## Task Type Classification (BEFORE Complexity Scoring)

**Classify task TYPE before scoring complexity.**

### Step 0: Detect Task Type

For each task group, classify the type FIRST:

**Research Tasks** (`type: research`):
- Explicit `[R]` marker in task name (preferred)
- Task name contains: "research", "evaluate", "select", "compare"
- Task produces: decision document, comparison matrix, recommendation
- **DB Initial Tier:** `"Developer"` (DB constraint - Orchestrator reads `Type: research` and spawns RE instead)
- **Agent Spawned:** Requirements Engineer (RE tier)
- **Execution Phase:** 1 (before implementation)
- **NOTE:** "investigation" and "analyze" are NOT research keywords - too generic, causes misrouting

**Architecture Tasks** (treated as research):
- Task name contains: "design", "architecture", "API design", "schema design", "data model"
- Task produces: design document, architecture decision record (ADR)
- **Type:** `research` (use same flow as research tasks)
- **DB Initial Tier:** `"Developer"` (DB constraint - Orchestrator spawns RE based on Type)
- **Agent Spawned:** Requirements Engineer (RE tier)
- **Execution Phase:** 1 (before implementation)
- **Tech Lead Validation:** MANDATORY (architecture decisions require TL approval)
- **Example:** "API Design [R]" → RE produces design doc → TL validates → Implementation begins

**Implementation Tasks** (`type: implementation`):
- Default for all other tasks
- Task requires: code writing, test creation, file modifications
- **Initial Tier:** `"Developer"` OR `"Senior Software Engineer"` (use complexity scoring)
- **Execution Phase:** 2+ (after research completes)

**Detection Priority:**
1. Explicit `[R]` marker → `research`
2. Contains research keywords (NOT "investigation") → `research`
3. Default → `implementation`

### Task Group Format with Type

```markdown
**Group R1:** OAuth Provider Research [R]
- **Type:** research
- **Initial Tier:** "Developer"  ← DB value (Orchestrator overrides to spawn RE)
- **Execution Phase:** 1
- **Deliverable:** Provider comparison matrix with recommendation
- **Success Criteria:** Decision on OAuth provider with pros/cons

**Group A:** Implement OAuth Integration
- **Type:** implementation
- **Complexity:** 7 (HIGH)
- **Initial Tier:** "Senior Software Engineer"
- **Execution Phase:** 2
- **Depends On:** R1 (research must complete first)
- **Research Reference:** bazinga/artifacts/{SESSION_ID}/research_group_R1.md
```

**Workflow Ordering:**
- Research groups in Phase 1, implementation in Phase 2+
- Research groups can run in parallel (MAX 2) - PM enforces this limit
- Implementation groups can run in parallel (MAX 4, existing limit)
- **Status remains PLANNING_COMPLETE** (no new status code)

**Important Clarifications:**
1. **Execution Phase ≠ Orchestrator Workflow Phase**: "Phase 1" here means task execution order, NOT orchestrator's internal workflow phases
2. **Metadata is markdown-only**: `Type`, `Security Sensitive`, `Execution Phase` fields are for task description markdown ONLY - do NOT pass these as database columns
3. **DB initial_tier constraint**: Database accepts `"Developer"` or `"Senior Software Engineer"` (title case). For research tasks, use `"Developer"` as DB value - Orchestrator reads `Type: research` and spawns RE instead

**Artifact Path Handoff:**
When creating Phase 2+ implementation groups that depend on Phase 1 research:
- Include `**Research Reference:** bazinga/artifacts/{SESSION_ID}/research_group_{id}.md` in the group description
- Developers MUST read the research deliverable before starting implementation

**ID Sanitization:**
- SESSION_ID/GROUP_ID must match: [A-Za-z0-9_] only
- Replace any character NOT in [A-Za-z0-9_] with underscore ("_")
- NEVER allow "../" (path traversal)

---

## Security Classification (AFTER Type, BEFORE Complexity)

**Flag security-sensitive tasks for mandatory SSE + Tech Lead review.**

**Security Tasks** (`security_sensitive: true`):
- Task name contains: "auth", "authentication", "authorization", "security", "crypto", "encryption", "password", "jwt", "oauth", "saml", "sso", "bearer", "credential"
- Task involves: user data, credentials, access control, session management
- **Initial Tier:** `"Senior Software Engineer"` (ALWAYS - overrides complexity scoring)
- **Tech Lead Review:** MANDATORY (even after QA passes)
- **Note:** "token" removed (too generic - matches CSRF token, string token). Use "bearer", "credential" instead.

**Detection:**
```
IF task_name contains security keywords OR task touches auth/security files:
  → security_sensitive: true
  → initial_tier: "Senior Software Engineer" (force SSE, ignore complexity score)
```

**Task Group Format with Security Flag:**
```markdown
**Group AUTH:** Implement JWT Authentication
- **Type:** implementation
- **Security Sensitive:** true  ← Forces SSE + mandatory TL review
- **Initial Tier:** "Senior Software Engineer" (forced by security flag)
- **Execution Phase:** 2
```

**Security Override Rules:**
1. Security flag OVERRIDES complexity scoring (always SSE, never Dev tier)
2. Tech Lead MUST approve security tasks (cannot skip to PM)
3. Failed security reviews return to SSE (not regular Developer)

---

## Task Complexity Scoring (Developer Assignment)

**Score each task group to determine initial developer tier:**

| Complexity Score | Tier | Agent |
|-----------------|------|-------|
| 1-3 | Low | Developer (Dev tier) |
| 4-6 | Medium | Senior Software Engineer (SSE tier) |
| 7+ | High | Senior Software Engineer (SSE tier) |

**Scoring Factors:**

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

**Example Scoring:**
```
Task: "Add password reset endpoint"
- Touches 3 files (+2)
- Feature following patterns (+2)
- Security-sensitive code (+3)
Total: 7 → HIGH → Assign to Senior Software Engineer

Task: "Fix typo in error message"
- Touches 1 file (+1)
- Bug fix with clear symptoms (+1)
Total: 2 → LOW → Assign to Developer (Dev tier)
```

**Include in task group assignment:**
```markdown
**Group A:** Password Reset
- **Complexity:** 7 (HIGH)
- **Initial Agent:** Senior Software Engineer (SSE tier)
- **Tasks:** T001, T002, T003
```
