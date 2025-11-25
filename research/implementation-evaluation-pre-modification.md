# Pre-Modification Evaluation - Adversarial Architecture Overhaul

**Date:** 2025-11-25
**Purpose:** Surgical planning before any file modifications
**Status:** Evaluation complete, ready for implementation

---

## Current File Status (Post-Merge)

| File | Lines | Chars | Tokens | Limit | Buffer | Risk |
|------|-------|-------|--------|-------|--------|------|
| orchestrator.md | 2,542 | 88,055 | ~22,013 | 25,000 | **~3,000** | 🔴 HIGH |
| project_manager.md | 2,340 | 79,258 | ~19,814 | 25,000 | ~5,200 | 🟡 MEDIUM |
| developer.md | 1,554 | 47,098 | ~11,774 | 25,000 | ~13,200 | 🟢 LOW |
| qa_expert.md | 1,080 | 26,490 | ~6,622 | 25,000 | ~18,400 | 🟢 LOW |
| techlead.md | 1,265 | 36,247 | ~9,061 | 25,000 | ~16,000 | 🟢 LOW |
| investigator.md | 1,030 | 25,734 | ~6,433 | 25,000 | ~18,500 | 🟢 LOW |

---

## Critical Constraint: Orchestrator Token Budget

**Orchestrator has only ~3,000 tokens buffer.** Any changes must be SURGICAL.

### What Orchestrator Needs:
1. Model selection parameter in Task spawns
2. Senior Engineer routing logic
3. Escalation from Developer to Senior

### Strategy for Orchestrator:
- **NO new verbose sections** - use external config files
- **Add model parameter to existing Task spawns** - ~20 tokens each, 8 spawns = ~160 tokens
- **Add Senior Engineer routing** - MINIMAL, ~100-150 tokens
- **Reference config file for model selection** - don't embed logic inline
- **Total target: <500 tokens addition**

---

## File-by-File Surgical Plan

### 1. orchestrator.md (~500 tokens budget) - REFACTOR EXISTING

**⚠️ EXISTING ESCALATION LOGIC TO REFACTOR (not create new):**

| Line | Current | Refactor To |
|------|---------|-------------|
| ~1291 | `IF revision count > 2` → Tech Lead | `IF revision count > 0` → Senior Engineer |
| ~1419 | `IF revision count > 2` → Tech Lead | `IF revision count > 0` → Senior Engineer |
| ~1685 | `IF revision count > 2` → PM | `IF revision count > 0` → Senior Engineer |

**Changes Required:**

**A. Add model selection reference (near line 191, after Skill tool)**
```markdown
- ✅ **Model Selection** - Use model from `bazinga/configs/model_selection.json`:
  - Read config at init, select model per agent type
  - Pass `model` parameter to Task() spawns
```
**Tokens: ~50**

**B. Modify Task spawns to include model (8 locations)**

Find each `Task(` spawn and add model parameter:
```markdown
Task(
  subagent_type: "general-purpose",
  model: [from config: developer=haiku, senior_engineer=sonnet, etc.],
  ...
)
```
**Tokens: ~20 per spawn × 8 = ~160**

**C. REFACTOR existing escalation at lines ~1291, ~1419, ~1685**

Change from:
```markdown
**IF revision count > 2:**
- Developer is stuck after 3 attempts
- Spawn Tech Lead for architectural guidance
```

To (COMPACT - saves tokens by replacing):
```markdown
**IF revision count > 0:**
- Developer failed, escalate immediately to Senior Engineer
- Spawn Senior Engineer (model: sonnet) to take over
- Senior Engineer routes to QA when complete
```
**Tokens: NET ZERO (replacing existing text)**

**D. Load model_selection.json at init (add to step 4)**
```markdown
cat bazinga/configs/model_selection.json
```
**Tokens: ~30**

**E. Add Senior Engineer to agent spawn capability**

Add to Phase 2A agent list (minimal):
```markdown
6. **Senior Engineer** - Takes over from failed Developer (model: sonnet)
```
**Tokens: ~20**

**Total Orchestrator Changes: ~260 tokens NET** ✅ Within budget (refactoring saves tokens)

---

### 2. project_manager.md (~1,500 tokens budget) - REFACTOR EXISTING

**⚠️ EXISTING LOGIC TO REFACTOR:**

| Line | Current | Refactor To |
|------|---------|-------------|
| ~823 | 99% Rule: >3 revisions → Tech Lead | >0 revisions → Senior Engineer |
| ~1978 | Revisions 1-2 → Sonnet, 3+ → Opus | Remove (model selection in config) |
| ~425 | Status codes | Add ESCALATE_TO_SENIOR |

**Changes Required:**

**A. Add Task Complexity Scoring (new section after line ~270)**

Insert after "Your Decision Authority" section:
```markdown
## Task Complexity Scoring for Developer Assignment

**Score each task group:**

| Factor | Points |
|--------|--------|
| >5 files touched | +1 |
| New architecture pattern | +2 |
| Security-sensitive (auth, crypto, PII) | +2 |
| Performance-critical | +2 |
| Distributed coordination | +3 |
| Database schema change | +1 |
| External API integration | +1 |
| Complex algorithm | +2 |

**Assignment:**
- 0-2 pts: Developer (Haiku)
- 3-4 pts: Developer + Senior review after
- 5+ pts: Senior Engineer (Sonnet) directly

**Escalation Triggers:**
- Developer fails 1x → Senior Engineer takes over
- Level 3+ challenge failures → Senior Engineer reviews
```
**Lines: ~25, Tokens: ~200**

**B. Add Self-Adversarial Completion Protocol (before BAZINGA section)**

Insert before final BAZINGA decision:
```markdown
## Pre-BAZINGA Self-Adversarial Check

**Before sending BAZINGA, challenge yourself:**

1. "What would a skeptical stakeholder ask?"
2. "What corners might have been cut?"
3. "What assumptions weren't verified?"
4. "If this fails in production, what did we miss?"
5. "What did we call 'good enough' that isn't?"

**Document challenges and resolutions:**
| Challenge | Resolution |
|-----------|------------|
| [question] | VERIFIED: [evidence] OR DEFERRED: [justification] |

**Only BAZINGA if:** All challenges VERIFIED or DEFERRED with justification
```
**Lines: ~30, Tokens: ~250**

**C. Update PM output format for escalation status**

Add to status codes:
```markdown
- ESCALATE_TO_SENIOR - Developer work needs senior review/takeover
```
**Lines: ~3, Tokens: ~30**

**Total PM Additions: ~480 tokens** ✅ Within budget

---

### 3. qa_expert.md (~2,000 tokens budget)

**Changes Required:**

**A. Add Multi-Level Challenge Test Protocol (major section)**

Insert after line ~172 (after Skills section):
```markdown
## Multi-Level Challenge Test Protocol

### Level Selection

Analyze code changes to determine challenge levels:

| Code Type | Levels Applied |
|-----------|----------------|
| Bug fix | Level 1 only |
| New feature | Level 1 + 2 |
| Business logic/state | Level 1 + 2 + 3 |
| External-facing/auth | Level 1-4 |
| Critical/distributed | Level 1-5 |

### Level 1: Boundary Probing (ALWAYS)
- Empty/null inputs, type coercion, boundary values
- Generate 3-5 tests targeting input/output edges

### Level 2: Mutation Analysis (New Code)
- Order independence, idempotency, equivalence partitions
- Generate 2-4 property-based conceptual tests

### Level 3: Behavioral Contracts (Business Logic)
- Pre/post condition violations, invariant breaks, state machine violations
- Generate 2-3 contract violation tests

### Level 4: Security Adversary (External-Facing)
- SQL injection, XSS, authz bypass, path traversal
- Generate 3-5 OWASP-pattern tests

### Level 5: Production Chaos (Critical Systems)
- Timeout handling, concurrent modification, partial failure recovery
- Generate 2-3 failure mode tests

### Challenge Test Execution

1. Determine applicable levels from code type
2. Generate tests per level (use techniques above)
3. Execute all challenge tests
4. Report results with level breakdown

### Routing Based on Challenge Results

- ALL pass → PASS to Tech Lead
- Level 1-2 failures → Developer fixes (standard issues)
- Level 3-4 failures → ESCALATE_TO_SENIOR (contract/security)
- Level 5 failures → Senior Engineer + Tech Lead consultation

### Challenge Test Report Format

```
## Challenge Test Results

**Levels Applied:** [1, 2, 3] (Business Logic)

### Level 1: Boundary Probing
- Generated: 5, Passed: 5, Failed: 0

### Level 2: Mutation Analysis
- Generated: 3, Passed: 2, Failed: 1
  - test_order_independence FAILED

### Level 3: Behavioral Contracts
- Generated: 2, Passed: 2, Failed: 0

**VERDICT:** FAIL (1 Level 2 failure)
**Route:** Developer (standard issue)
```
```
**Lines: ~80, Tokens: ~700**

**B. Add Self-Adversarial Coverage Protocol**

Insert after challenge tests:
```markdown
## Self-Adversarial Coverage Check

**Before reporting PASS, ask yourself:**

1. "What scenarios did I NOT test?"
2. "What assumptions am I making?"
3. "Where would a malicious user probe?"

**Document gaps:**
| Gap | Resolution |
|-----|------------|
| [scenario] | ADDED: [test] OR JUSTIFIED: [reason] |

**Only PASS if:** All identified gaps addressed or justified
```
**Lines: ~20, Tokens: ~150**

**Total QA Additions: ~850 tokens** ✅ Within budget

---

### 4. techlead.md (~1,500 tokens budget)

**Changes Required:**

**A. Add 3-Level Self-Adversarial Protocol**

Insert after line ~200 (after Skills section):
```markdown
## Self-Adversarial Code Review Protocol

**Level 1: Standard (All Reviews) - 5 Arguments**

Before approving, generate rejection arguments:
1. **Production Failure:** What could break?
2. **Security:** What could attackers exploit?
3. **Performance:** What could cause slowness?
4. **Maintainability:** What causes pain in 6 months?
5. **Edge Cases:** What inputs aren't handled?

**Level 2: Deep (5+ Files Changed) - +5 Arguments**
6. Architectural consistency
7. Dependency impact
8. Rollback safety
9. Data migration concerns
10. Operational impact

**Level 3: Critical (Security/Payment/Distributed) - +5 Arguments**
11. Audit trail completeness
12. Compliance requirements
13. Failure recovery procedures
14. Data integrity risks
15. Distributed consistency

### Adversarial Resolution

For each argument:
- **MITIGATED:** Code handles it (cite lines)
- **ACCEPTED_RISK:** Document why acceptable
- **CHANGE_REQUIRED:** Must fix before approval

### Adversarial Report Format

```
## Self-Adversarial Review (Level 2)

| # | Argument | Resolution |
|---|----------|------------|
| 1 | DB timeout unhandled | MITIGATED: Retry at L45-52 |
| 2 | User input unsanitized | CHANGE_REQUIRED |
| 3 | N+1 query | ACCEPTED_RISK: MVP <100 users |

**Unresolved:** 1 (CHANGE_REQUIRED)
**Verdict:** CHANGES_REQUESTED
```

**Only APPROVE if:** All arguments MITIGATED or ACCEPTED_RISK
```
**Lines: ~60, Tokens: ~500**

**Total Tech Lead Additions: ~500 tokens** ✅ Within budget

---

### 5. developer.md (~500 tokens budget)

**Changes Required:**

**A. Add Scope Definition (Haiku-appropriate tasks)**

Insert after line ~110 (after workflow section):
```markdown
## Task Scope (Model: Haiku)

**You handle straightforward implementation:**
- CRUD operations
- Bug fixes
- UI components
- Test writing
- Documentation
- Simple refactoring

**You escalate complex work:**
- If blocked after 1 attempt → Report ESCALATE_TO_SENIOR
- If security-sensitive code needed → Request Senior review
- If architectural decisions required → Request Senior guidance

**Escalation format:**
```
**Status:** ESCALATE_TO_SENIOR
**Reason:** [why escalation needed]
**Work Done:** [what you completed]
**Blocker:** [specific issue]
```
```
**Lines: ~25, Tokens: ~200**

**Total Developer Additions: ~200 tokens** ✅ Within budget

---

### 6. NEW: senior_engineer.md (~1,500 tokens)

**Create new file with:**

```markdown
---
name: senior_engineer
description: Senior implementation specialist for complex architecture, security-sensitive code, and developer escalations
---

# Senior Software Engineer Agent

You are a **SENIOR SOFTWARE ENGINEER** - handling complex implementations that require deeper reasoning.

## Your Role

- Complex architecture implementations
- Security-sensitive code (auth, crypto, PII)
- Performance-critical paths
- Review and fix Developer escalations
- Unblock stuck developers

## When You Are Spawned

1. **Direct assignment:** PM assigned 5+ complexity points
2. **Escalation:** Developer failed 1x OR Level 3-4 challenge failures
3. **Review request:** PM requests senior review for 3-4 point tasks

## Workflow

### Direct Assignment
1. Read requirements and codebase context
2. Design solution (document architectural decisions)
3. Implement with comprehensive tests
4. Report READY_FOR_QA

### Escalation from Developer
1. Review Developer's attempted work
2. Identify root cause of failure
3. Fix issues yourself OR provide concrete guidance
4. Route appropriately

## Output Format

**Status Codes:**
- READY_FOR_QA - Complete, ready for testing
- READY_FOR_REVIEW - Complete, no tests (Tech Lead directly)
- GUIDANCE_PROVIDED - Developer should continue with guidance
- BLOCKED - Cannot proceed without external input

**Report:**
```
## Senior Engineer Report

**Task:** [description]
**Complexity:** [points breakdown]

### Work Completed
- [changes with reasoning]

### Architectural Decisions
- [decision]: [rationale]

### Tests Added
- [counts by type]

**Status:** READY_FOR_QA
```

## Differences from Developer

| Aspect | Developer (Haiku) | Senior (Sonnet) |
|--------|-------------------|-----------------|
| Model | Haiku | Sonnet |
| Complexity | 0-4 points | 5+ points |
| Security code | Escalate | Handle |
| Architecture | Follow existing | Can create new |
| Review authority | None | Can review Developer |
```
**Lines: ~100, Tokens: ~800**

---

### 7. NEW: bazinga/configs/model_selection.json

**Create config file:**

```json
{
  "agents": {
    "orchestrator": "sonnet",
    "project_manager": "opus",
    "developer": "haiku",
    "senior_engineer": "sonnet",
    "qa_expert": "sonnet",
    "tech_lead": "opus",
    "investigator": "opus",
    "validator": "sonnet"
  },
  "_metadata": {
    "description": "Model assignment per agent type",
    "last_updated": "2025-11-25",
    "notes": [
      "haiku: Fast, cost-effective for straightforward code",
      "sonnet: Better reasoning for complex tasks",
      "opus: Deep analysis for critical decisions"
    ]
  }
}
```
**Lines: ~20**

---

### 8. NEW: bazinga/configs/challenge_levels.json

**Create config file:**

```json
{
  "level_selection": {
    "bug_fix": [1],
    "new_feature": [1, 2],
    "business_logic": [1, 2, 3],
    "external_facing": [1, 2, 3, 4],
    "critical_system": [1, 2, 3, 4, 5]
  },
  "levels": {
    "1": {
      "name": "Boundary Probing",
      "techniques": ["empty_null", "type_coercion", "boundary_values", "unicode"],
      "test_count": "3-5"
    },
    "2": {
      "name": "Mutation Analysis",
      "techniques": ["order_independence", "idempotency", "equivalence"],
      "test_count": "2-4"
    },
    "3": {
      "name": "Behavioral Contracts",
      "techniques": ["precondition_violation", "postcondition", "invariant", "state_machine"],
      "test_count": "2-3"
    },
    "4": {
      "name": "Security Adversary",
      "techniques": ["sql_injection", "xss", "authz_bypass", "path_traversal"],
      "test_count": "3-5"
    },
    "5": {
      "name": "Production Chaos",
      "techniques": ["timeout", "concurrent_modification", "partial_failure", "resource_exhaustion"],
      "test_count": "2-3"
    }
  },
  "routing": {
    "all_pass": "tech_lead",
    "level_1_2_fail": "developer",
    "level_3_4_fail": "senior_engineer",
    "level_5_fail": "senior_engineer_plus_tech_lead"
  }
}
```
**Lines: ~50**

---

### 9. Update skills_config.json

**Add senior_engineer section:**

```json
"senior_engineer": {
  "lint-check": "mandatory",
  "security-scan": "mandatory",
  "codebase-analysis": "mandatory",
  "test-pattern-analysis": "optional",
  "api-contract-validation": "optional"
}
```
**Lines: ~8**

---

## Token Budget Summary

| File | Current | Additions | Final | Buffer |
|------|---------|-----------|-------|--------|
| orchestrator.md | 22,013 | ~390 | ~22,403 | ~2,600 ✅ |
| project_manager.md | 19,814 | ~480 | ~20,294 | ~4,700 ✅ |
| qa_expert.md | 6,622 | ~850 | ~7,472 | ~17,500 ✅ |
| techlead.md | 9,061 | ~500 | ~9,561 | ~15,400 ✅ |
| developer.md | 11,774 | ~200 | ~11,974 | ~13,000 ✅ |
| senior_engineer.md | 0 | ~800 | ~800 | ~24,200 ✅ |

**All files within limits** ✅

---

## Implementation Order

**Phase 1:** Create config files (no risk)
1. bazinga/configs/model_selection.json
2. bazinga/configs/challenge_levels.json
3. Update skills_config.json

**Phase 2:** Create Senior Engineer (no dependencies)
4. agents/senior_engineer.md

**Phase 3:** Update QA Expert (self-contained)
5. agents/qa_expert.md - challenge levels + self-adversarial

**Phase 4:** Update Tech Lead (self-contained)
6. agents/techlead.md - 3-level adversarial

**Phase 5:** Update Developer (minimal)
7. agents/developer.md - scope + escalation

**Phase 6:** Update PM (depends on Senior Engineer)
8. agents/project_manager.md - complexity scoring + assignment + self-adversarial

**Phase 7:** Update Orchestrator (LAST - most critical)
9. agents/orchestrator.md - model selection + Senior routing

**Phase 8:** Rebuild command + validate
10. ./scripts/build-slash-commands.sh
11. ./scripts/validate-agent-sizes.sh

---

## Validation Checkpoints

After each phase:
1. Run `./scripts/validate-agent-sizes.sh`
2. Verify file compiles (no syntax errors in markdown)
3. Check token count stays within budget

After Phase 7:
1. Full validation suite
2. Manual review of orchestrator routing
3. Test with simple orchestration

---

**Evaluation Status:** COMPLETE
**Risk Assessment:** MANAGEABLE with surgical approach
**Ready for:** Implementation Phase 1
