# PM Examples & Templates Reference

**Purpose:** Contains detailed examples referenced by `agents/project_manager.md` to keep the main file under token limits.

---

## Investigation Status Examples

### Example 1 - Build Failure

```markdown
## PM Status Update

### Critical Issue Detected
Build failing on production target with linker errors.

### Analysis
- Local dev builds succeed
- CI/CD pipeline fails at link stage
- Root cause: Unknown

**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator with:
- Problem: Production build linker errors (undefined references)
- Context: Works locally, fails in CI
- Hypothesis: Missing library dependencies or compiler flag differences
```

### Example 2 - Deployment Blocker

```markdown
## PM Status Update

### Critical Issue Detected
Deployment to staging environment blocked - pods failing health checks.

### Analysis
- Docker images build successfully
- Kubernetes pods start but fail readiness probe
- Logs show connection timeouts
- Root cause: Unknown

**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator with:
- Problem: Staging deployment health check failures
- Context: Images build, pods start, but fail readiness
- Hypothesis: Network config, missing env vars, or service dependencies
```

### Example 3 - Performance Regression

```markdown
## PM Status Update

### Critical Issue Detected
API response times increased 5x after recent deployment.

### Analysis
- No code changes to query logic
- Database queries show normal execution time
- Load hasn't increased
- Root cause: Unknown

**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator with:
- Problem: 5x performance degradation on API endpoints
- Context: No query changes, normal DB performance, consistent load
- Hypothesis: Connection pooling, cache invalidation, or middleware overhead
```

---

## Reasoning Documentation Examples

### At Task START (Understanding Phase)

```bash
cat > /tmp/reasoning_understanding.md << 'REASONING_EOF'
## Project Understanding

### User Request Summary
[What the user wants]

### Scope Assessment
[Size and complexity]

### Key Requirements
1. [Requirement 1]
2. [Requirement 2]

### Success Criteria
- [Criterion 1]
- [Criterion 2]
REASONING_EOF

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "project_manager" "understanding" \
  --content-file /tmp/reasoning_understanding.md \
  --confidence high
```

### Execution Mode Decision (Approach Phase)

```bash
cat > /tmp/reasoning_approach.md << 'REASONING_EOF'
## Execution Strategy

### Mode
[SIMPLE / PARALLEL]

### Why This Mode
[Rationale]

### Task Groups
1. [Group A]: [Description]
2. [Group B]: [Description]

### Developer Allocation
[How many developers and why]
REASONING_EOF

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "project_manager" "approach" \
  --content-file /tmp/reasoning_approach.md \
  --confidence high
```

### At BAZINGA (Completion Phase)

```bash
cat > /tmp/reasoning_completion.md << 'REASONING_EOF'
## Project Completion Summary

### What Was Delivered
- [Deliverable 1]
- [Deliverable 2]

### Success Criteria Met
- [x] [Criterion 1]
- [x] [Criterion 2]

### Key Decisions Made
- [Decision 1]
- [Decision 2]

### Lessons Learned
[For future projects]
REASONING_EOF

python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{SESSION_ID}" "{GROUP_ID}" "project_manager" "completion" \
  --content-file /tmp/reasoning_completion.md \
  --confidence high
```

---

## Path B Blocker Examples

**Examples that are NOT Path B (must use Path C):**
- ❌ "Coverage only 44%, mocking too complex" → Use Path C (spawn developers to add mocks)
- ❌ "Tests failing due to edge cases" → Use Path C (spawn developers to fix)
- ❌ "Performance target not met" → Use Path C (spawn developers to optimize)
- ❌ "Integration tests need backend" → Use Path C (spawn developers to add mocks)
- ❌ "Pre-existing test failures unrelated to my task" → Use Path C (all failures are fixable)
- ❌ "Some tests fail but my feature works" → Use Path C (project completion requires ALL tests passing)

**Examples that ARE Path B (legitimate):**
- ✅ "Cannot integrate with Stripe: API keys not provided, cannot proceed without user's account"
- ✅ "Cannot deploy to AWS: project has no AWS credentials, infrastructure setup out of scope"
- ✅ "Cannot test email flow: SendGrid service is down (checked status page), beyond our control"

---

## Development Plan JSON Format

### Save Plan Request Format

```
bazinga-db, please save this development plan:

Session ID: {session_id}
Original Prompt: {user's exact message, escape quotes}
Plan Text: Phase 1: JWT auth
Phase 2: User registration
Phase 3: Email verification
Phases: [{"phase":1,"name":"JWT auth","status":"pending","description":"Implement JWT tokens","requested_now":true},{"phase":2,"name":"User registration","status":"not_started","description":"Signup flow","requested_now":false},{"phase":3,"name":"Email verification","status":"not_started","description":"Email confirmation","requested_now":false}]
Current Phase: 1
Total Phases: 3
Metadata: {"plan_type":"user_provided_partial","scope_requested":"Phase 1 only"}
```

**JSON Construction Rules:**
- Use compact JSON (no newlines inside array)
- Escape quotes in descriptions: `"JWT \"bearer\" tokens"` → `"JWT \\"bearer\\" tokens"`
- Required fields: phase (int), name, status, description, requested_now (bool)
- Keep descriptions short (<50 chars) to avoid command-line limits

---

## PM State JSON Format

```json
{
  "session_id": "[session_id]",
  "initial_branch": "[from session data]",
  "mode": "simple|parallel",
  "mode_reasoning": "Explanation of mode choice",
  "original_requirements": "Full user requirements",
  "success_criteria": [
    {"criterion": "Coverage >70%", "status": "pending", "actual": null, "evidence": null}
  ],
  "investigation_findings": "[Summary or null]",
  "parallel_count": 2,
  "all_tasks": [],
  "task_groups": [],
  "execution_phases": [
    {"phase": 1, "group_ids": ["group_1"], "description": "Setup"}
  ],
  "completed_groups": [],
  "in_progress_groups": [],
  "pending_groups": [],
  "iteration": 1,
  "last_update": "[ISO timestamp]",
  "completion_percentage": 0,
  "estimated_time_remaining_minutes": 30,
  "assumptions_made": [
    {
      "decision": "Description",
      "blocker_type": "none|mutually_exclusive_requirements|missing_external_data|security_decision",
      "user_response": "inferred_from_codebase|User confirmed...|timeout_assumed",
      "reasoning": "Why",
      "confidence": "high|medium|low",
      "risk_if_wrong": "Risk description"
    }
  ]
}
```

---

## Specialization Mapping Table

| Technology | Template Path |
|------------|---------------|
| typescript, ts | `bazinga/templates/specializations/01-languages/typescript.md` |
| javascript, js | `bazinga/templates/specializations/01-languages/javascript.md` |
| python, py | `bazinga/templates/specializations/01-languages/python.md` |
| java | `bazinga/templates/specializations/01-languages/java.md` |
| go, golang | `bazinga/templates/specializations/01-languages/go.md` |
| rust | `bazinga/templates/specializations/01-languages/rust.md` |
| react | `bazinga/templates/specializations/02-frameworks-frontend/react.md` |
| nextjs, next.js | `bazinga/templates/specializations/02-frameworks-frontend/nextjs.md` |
| vue | `bazinga/templates/specializations/02-frameworks-frontend/vue.md` |
| angular | `bazinga/templates/specializations/02-frameworks-frontend/angular.md` |
| express | `bazinga/templates/specializations/03-frameworks-backend/express.md` |
| fastapi | `bazinga/templates/specializations/03-frameworks-backend/fastapi.md` |
| django | `bazinga/templates/specializations/03-frameworks-backend/django.md` |
| spring | `bazinga/templates/specializations/03-frameworks-backend/spring.md` |
