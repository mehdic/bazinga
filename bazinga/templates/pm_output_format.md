# PM Mandatory Output Format

**Purpose:** Defines required status codes PM must output for orchestrator to parse responses.

---

## 🚨 CRITICAL RULE

**Every PM response MUST include a status header.**

The orchestrator depends on these status codes to route your decisions. Without a status code, orchestrator will log "PM spawn completed without output" and the workflow will stop.

---

## Status Codes by Situation

### Initial Planning (First PM Spawn)

#### When Deciding Execution Mode

```markdown
## PM Status: PLANNING_COMPLETE

**Mode:** PARALLEL (or SIMPLE)
**Developers:** {N} concurrent
**Total Tasks:** {count} across {phase_count} phases

**Phases:**
- Phase 1: {phase_name}
  - Group {id}: {description}
  - Group {id}: {description}
- Phase 2: {phase_name}
  - Group {id}: {description}

**Success Criteria:**
- {criterion_1}
- {criterion_2}

**Next Action:** Orchestrator should spawn {N} developer(s) for Phase 1 groups: {ids}
```

**Required fields for orchestrator parsing:**
- Mode (SIMPLE or PARALLEL)
- Developer count
- Task/phase counts
- Phase breakdown with group IDs
- Success criteria list
- Next action with specific group IDs

**Use when:**
- You've analyzed requirements
- Decided on SIMPLE or PARALLEL mode
- Created task groups
- Ready for orchestrator to spawn developers

#### When Need User Input

```markdown
## PM Status: NEEDS_CLARIFICATION
```

**Use when:** Rare blocker requires user input (see Constrained Clarification Protocol in main PM file)

#### When Only Questions Asked

```markdown
## PM Status: INVESTIGATION_ONLY
```

**Use when:** User only asked questions (no "implement", "fix", "add", etc.)

---

### Progress Assessment (Iteration Check)

**When orchestrator asks you to assess progress after Dev/QA/Tech Lead complete:**

#### Work Incomplete - Continue

```markdown
## PM Status: CONTINUE

**Assessment:** [Current progress summary]
**Remaining Work:** [What still needs to be done]
**Next Action:** Orchestrator should spawn [agent] for [task]
```

**Use when:**
- Test failures remain but root cause is clear
- More iterations needed to complete work
- Simple bugs/fixes remaining

**Example:**
```markdown
## PM Status: CONTINUE

**Assessment:** Group B progress is good (652/711 tests passing, 91.7%).
54 tests fixed across 3 iterations (610→652). Significant progress made.

**Remaining Work:** 59 test failures remain:
- API Gateway: 5 failures (routing, middleware)
- Shared Middleware: 4 failures (mock adjustments)
- JWT: 1 failure (validation edge case)
- Prescription Upload: 1 failure (timeout)
- Others: 21 failures (various)

**Next Action:** Orchestrator should spawn Developer B for iteration 4,
focusing on the 32 fixable tests (API Gateway, Shared Middleware, JWT,
Prescription Upload). Save complex failures for later investigation.
```

---

#### Work Blocked - Investigation Needed

```markdown
## PM Status: INVESTIGATION_NEEDED

**Critical Issue Detected:** [Describe blocker: test failures, build errors, deployment issues, bugs, performance problems]
**Analysis:** [What was tried, current state, symptoms]
**Root Cause:** Unknown (requires investigation)
**Next Action:** Orchestrator should spawn Investigator to diagnose [problem description]
```

**Use when:**
- Test failures with unclear root cause (not simple bugs)
- Build/compilation errors that aren't obvious
- Deployment/infrastructure issues
- Performance regressions without clear cause
- Integration failures between systems
- Any blocker where root cause analysis is needed

**Example:**
```markdown
## PM Status: INVESTIGATION_NEEDED

**Critical Issue Detected:** Auth Service has 17 test failures with AggregateError.
All failures show an identical error pattern but the root cause unclear.

**Analysis:**
- Developer attempted fixes in iterations 1-3
- Test infrastructure examined
- Mock configurations reviewed
- Failures persist across all attempts

**Root Cause:** Unknown - appears to be an architectural/infrastructure issue
rather than simple code bug.

**Next Action:** Orchestrator should spawn Investigator to diagnose Auth Service
test failures. Focus on: test infrastructure, mock timing, async patterns.
```

---

#### All Work Complete

```markdown
## PM Status: BAZINGA

**Final Assessment:** [Completion summary]
**Success Criteria:** [All criteria met with evidence]
```

**Use when:**
- ALL tests passing (100%)
- ALL success criteria met
- No blockers remain
- Work is truly complete

**Example:**
```markdown
## PM Status: BAZINGA

**Final Assessment:** All task groups completed successfully.
- Group A: 100% tests passing (265/265)
- Group B: 100% tests passing (711/711)
- Group C: 100% tests passing (183/183)

**Success Criteria:** ALL MET
✅ All tests passing (1159/1159)
✅ Coverage >80% (achieved 87.3%)
✅ Security scan: 0 high/critical issues
✅ Lint: 0 errors
```

---

## Complete Status Code Reference

| Status Code | When to Use | Orchestrator Action |
|-------------|-------------|---------------------|
| **PLANNING_COMPLETE** | Initial planning done, task groups created | Spawn developers for task groups |
| **CONTINUE** | Work incomplete, more iterations needed | Spawn developer for next iteration |
| **INVESTIGATION_NEEDED** | Blocker with unclear root cause | Spawn Investigator to diagnose |
| **BAZINGA** | All work complete, all criteria met | Proceed to completion phase |
| **NEEDS_CLARIFICATION** | User input required (rare) | Wait for user response |
| **INVESTIGATION_ONLY** | Questions only, no implementation | Display results and exit |

---

## Decision Tree

```
Progress Assessment Decision Tree:

Is ALL work complete? (100% tests passing, all criteria met)
├─ YES → ## PM Status: BAZINGA
│
└─ NO → Is root cause clear?
    ├─ YES (simple bugs/fixes) → ## PM Status: CONTINUE
    │
    └─ NO (unclear root cause, complex blocker) → ## PM Status: INVESTIGATION_NEEDED

Need user input during planning?
└─ YES → ## PM Status: NEEDS_CLARIFICATION

User only asked questions?
└─ YES → ## PM Status: INVESTIGATION_ONLY
```

---

## Enforcement Rules

1. **ALWAYS include status header** - `## PM Status: [CODE]`
2. **Use exact status codes** - Match codes exactly as shown above
3. **Include assessment details** - After status code, explain your decision
4. **Provide next action** - Tell orchestrator what to spawn next (except BAZINGA)
5. **No ambiguity** - Choose ONE status code that best fits the situation

---

## Common Mistakes to Avoid

❌ **Don't output without status:**
```
We should continue with more iterations...
[Missing ## PM Status: CONTINUE]
```

❌ **Don't use wrong status for unclear failures:**
```
## PM Status: CONTINUE
[Should be INVESTIGATION_NEEDED if root cause unclear]
```

❌ **Don't declare BAZINGA prematurely:**
```
## PM Status: BAZINGA
[When tests still failing or criteria unmet]
```

✅ **Correct approach:**
```markdown
## PM Status: CONTINUE

**Assessment:** ...clear progress description...
**Remaining Work:** ...specific items...
**Next Action:** Orchestrator should spawn Developer for iteration X
```

---

**Reference:** This template is referenced by `agents/project_manager.md` line ~102
