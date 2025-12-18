# BAZINGA - Claude Code Multi-Agent Dev Team - Architecture

> **Repository:** https://github.com/mehdic/bazinga

## Table of Contents

1. [System Overview](#system-overview)
2. [Agent Definitions](#agent-definitions)
3. [Workflow Patterns](#workflow-patterns)
4. [Role Drift Prevention](#role-drift-prevention)
5. [State Management](#state-management)
6. [Routing Mechanism](#routing-mechanism)
7. [Tool Restrictions](#tool-restrictions)
8. [Decision Logic](#decision-logic)

## System Overview

BAZINGA (Claude Code Multi-Agent Dev Team) is a hierarchical, stateless agent coordination framework designed for Claude Code. It implements adaptive parallelism, conditional workflow routing, and comprehensive role drift prevention.

### Core Principles

1. **Stateless Agents**: Each agent spawn is independent; state persists via JSON files
2. **Explicit Routing**: Agents tell orchestrator where to route (no implicit decisions)
3. **Conditional Workflows**: Routing adapts based on context (tests vs no tests)
4. **Role Enforcement**: Multiple layers prevent agents from drifting from their roles
5. **Single Source of Truth**: Only PM decides project completion (BAZINGA)

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER REQUEST                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│  • Routes messages between agents                            │
│  • Spawns agents via Task tool                              │
│  • Never implements code                                     │
│  • 6-layer role drift prevention                            │
└────────────────────────┬────────────────────────────────────┘
                         ↓ (spawns PM)
┌─────────────────────────────────────────────────────────────┐
│                   PROJECT MANAGER                            │
│  • Analyzes requirements                                     │
│  • Creates task groups                                       │
│  • Decides simple vs parallel mode (1-4 developers)         │
│  • Tracks progress                                           │
│  • Sends BAZINGA when 100% complete                         │
│  • Tool restrictions: Read state files only, no Edit        │
└────────────────────────┬────────────────────────────────────┘
                         ↓ (spawns Developer(s))
┌─────────────────────────────────────────────────────────────┐
│                      DEVELOPER(S)                            │
│  • Implements code                                           │
│  • Creates/fixes tests                                       │
│  • Runs unit tests                                           │
│  • Decides routing: QA (with tests) or Tech Lead (no tests) │
│  • Full tool access for implementation                      │
└──────────────┬───────────────────┬──────────────────────────┘
               │                    │
    (with tests)│                   │(no tests)
               ↓                    ↓
┌─────────────────────┐   ┌─────────────────────────────────┐
│    QA EXPERT        │   │       TECH LEAD                 │
│  • Integration tests│   │  • Reviews code quality         │
│  • Contract tests   │   │  • Architecture review          │
│  • E2E tests        │   │  • Security review              │
│  • PASS → TechLead  │   │  • Unblocks developers          │
│  • FAIL → Developer │   │  • APPROVED → PM                │
│  • Conditional spawn│   │  • CHANGES_REQUESTED → Dev      │
└──────────┬──────────┘   │  • Receives from QA OR Dev      │
           │              └──────────────┬──────────────────┘
           │ (if PASS)                   │
           └──────────────┬──────────────┘
                          ↓
           ┌──────────────────────────────┐
           │       TECH LEAD              │
           │  (from QA or Dev directly)   │
           └──────────────┬───────────────┘
                          ↓ (if APPROVED)
           ┌──────────────────────────────┐
           │     PROJECT MANAGER          │
           │  • Tracks completion         │
           │  • Spawns more devs OR       │
           │  • Sends BAZINGA             │
           └──────────────────────────────┘
```

## Agent Definitions

### Orchestrator

**File**: `agents/orchestrator.md`

**Role**: Message router and agent spawner

**Responsibilities**:
- Route messages between agents
- Spawn agents using Task tool
- Maintain workflow integrity
- Never implement code

**Tool Usage**:
- Task tool to spawn agents
- Read to check state files
- NO Edit, Write, or Bash for implementation

**Role Drift Prevention**:
1. Pre-response role check: `🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator`
2. Routing decision table (mandatory lookup)
3. Anti-pattern examples (WRONG vs CORRECT)
4. Strategic checkpoints before routing decisions
5. Workflow enforcement in .claude.md
6. Mandatory workflow chain diagram

**Routing Logic**:
```
PM status: PLANNING_COMPLETE
  → Spawn Developer(s) per PM instructions

Developer status: READY_FOR_QA
  → Forward to QA Expert

Developer status: READY_FOR_REVIEW
  → Forward to Tech Lead

QA status: PASS
  → Forward to Tech Lead

QA status: FAIL
  → Forward back to Developer

Tech Lead status: APPROVED
  → Forward to PM

Tech Lead status: CHANGES_REQUESTED
  → Forward back to Developer
```

### Project Manager

**File**: `agents/project_manager.md`

**Role**: Project coordinator and completion authority

**Responsibilities**:
- Analyze requirements
- Create task groups
- Decide execution mode (simple vs parallel)
- Decide parallelism (1-4 developers)
- Track progress across all groups
- Send BAZINGA when 100% complete
- Never ask user questions (full autonomy)

**Tool Usage**:
- Read: ONLY bazinga/*.json state files
- Write: ONLY bazinga/*.json state files
- Glob/Grep: Understanding codebase structure only
- Bash: Analysis only, never run tests
- FORBIDDEN: Edit, NotebookEdit

**Decision Logic**:

```python
def decide_execution_mode(features, file_overlap, dependencies):
    if features == 1 or file_overlap == HIGH:
        return SIMPLE_MODE  # 1 developer sequential

    if 2 <= features <= 4 and independent:
        parallel_count = features
        return PARALLEL_MODE, parallel_count

    if features > 4:
        return PARALLEL_MODE, 4  # Max 4 parallel

    if critical_dependencies:
        return SIMPLE_MODE  # Sequential safer

    return SIMPLE_MODE  # Default safe choice
```

**State File Schema**:
```json
{
  "session_id": "session_YYYYMMDD_HHMMSS",
  "mode": "simple" | "parallel",
  "mode_reasoning": "string",
  "original_requirements": "string",
  "task_groups": [
    {
      "id": "A",
      "name": "JWT Authentication",
      "tasks": ["T1", "T2"],
      "files_affected": ["auth.py"],
      "branch_name": "feature/group-A-jwt-auth",
      "can_parallel": true,
      "depends_on": [],
      "complexity": "medium",
      "estimated_effort_minutes": 15
    }
  ],
  "completed_groups": [],
  "in_progress_groups": [],
  "pending_groups": [],
  "iteration": 1,
  "last_update": "2025-01-07T10:00:00Z"
}
```

**Completion Logic**:
```
IF all_task_groups_approved:
    UPDATE state → completed
    OUTPUT: BAZINGA
    WORKFLOW ENDS

ELSE IF some_complete AND more_pending:
    SPAWN next batch of developers

ELSE IF tests_failing OR changes_requested:
    REASSIGN to developers with feedback
    NEVER ask user "should I continue?"
```

### Developer

**File**: `agents/developer.md`

**Role**: Implementation specialist

**Responsibilities**:
- Write clean, working code
- Create/fix unit tests
- Create/fix integration/contract/E2E tests
- Run unit tests locally
- Decide routing based on test presence
- Fix bugs based on QA/Tech Lead feedback

**Tool Usage**:
- Full access: Read, Write, Edit, Bash, Glob, Grep
- All implementation tools available

**Routing Decision Tree**:
```
Does implementation include tests (integration/contract/E2E)?
├─ YES, tests created/fixed
│  Status: READY_FOR_QA
│  Next Step: Orchestrator, please forward to QA Expert for testing
│  Workflow: Developer → QA Expert → Tech Lead → PM
│
└─ NO, no tests (or only unit tests)
   Status: READY_FOR_REVIEW
   Next Step: Orchestrator, please forward to Tech Lead for code review
   Workflow: Developer → Tech Lead → PM
```

**Report Template**:
```markdown
## Implementation Complete

**Summary:** [One sentence]

**Files Modified:**
- file1.py (created/modified)
- file2.py (created/modified)

**Key Changes:**
- Change 1
- Change 2

**Code Snippet:**
```language
[5-10 lines of key code]
```

**Tests:**
- Total: X
- Passing: Y
- Failing: Z

**Tests Created/Fixed:** YES / NO

**Status:** READY_FOR_QA / READY_FOR_REVIEW
**Next Step:** Orchestrator, please forward to [QA Expert / Tech Lead]
```

**Test-Passing Integrity**:
- NEVER remove @async to avoid test complexity
- NEVER remove decorators to bypass test setup
- NEVER disable features to make tests easier
- FIX tests to match correct implementation
- If major architectural change needed → Request Tech Lead validation

### QA Expert

**File**: `agents/qa_expert.md`

**Role**: Testing specialist (conditionally spawned)

**Responsibilities**:
- Run integration tests
- Run contract tests
- Run end-to-end tests
- Validate API contracts
- Report detailed test results
- Route to Tech Lead (PASS) or Developer (FAIL)

**Important**: Only spawned when Developer has created/fixed integration/contract/E2E tests. If Developer only has unit tests or no tests, QA is skipped.

**Tool Usage**:
- Bash: Run test commands
- Read: Read test files and code
- Write: Create/update test files if needed
- Glob/Grep: Find test patterns

**Test Types**:

1. **Integration Tests**:
   - API endpoints with database
   - Service-to-service communication
   - Middleware integration
   - External service mocking

2. **Contract Tests**:
   - Request/response schema validation
   - API contract compliance
   - Backward compatibility
   - HTTP status codes

3. **E2E Tests**:
   - Full user journeys
   - Cross-component flows
   - Real-world scenarios
   - Multi-step processes

**Routing Logic**:
```
IF all_tests_pass:
    Status: PASS
    Next Step: Orchestrator, please forward to Tech Lead for code review

ELSE IF any_test_fails:
    Status: FAIL
    Next Step: Orchestrator, please send back to Developer to fix failures

ELSE IF environment_blocked:
    Status: BLOCKED
    Next Step: Orchestrator, please forward to Tech Lead to resolve blocker

ELSE IF tests_flaky:
    Status: FLAKY
    Next Step: Orchestrator, please forward to Tech Lead to investigate
```

### Tech Lead

**File**: `agents/tech_lead.md`

**Role**: Quality reviewer and technical authority

**Responsibilities**:
- Review code quality
- Check architecture
- Validate security
- Ensure maintainability
- Unblock developers
- Validate architectural decisions
- Approve individual task groups (NOT entire project)

**Important**: Receives work from TWO sources:
1. QA Expert (when tests passed)
2. Developer directly (when no tests)

**Tool Usage**:
- Read: Review code
- Glob/Grep: Search patterns
- NO Edit, Write (review only, don't implement)

**Review Checklist**:

**CRITICAL (Must Fix)**:
- Security vulnerabilities
- Data corruption risks
- Critical functionality broken
- Authentication/authorization bypasses
- Resource leaks

**HIGH (Should Fix)**:
- Incorrect logic
- Missing error handling
- Poor performance
- Breaking changes without migration
- Tests failing

**MEDIUM (Good to Fix)**:
- Code readability
- Missing edge cases
- Inconsistent conventions
- Insufficient test coverage

**LOW (Optional)**:
- Variable naming
- Code structure optimization
- Minor style issues

**Routing Logic**:
```
IF no_critical_or_high_issues AND core_functionality_works:
    Status: APPROVED
    Next Step: Orchestrator, please forward to PM for completion tracking

ELSE IF critical_or_high_issues:
    Status: CHANGES_REQUESTED
    Next Step: Orchestrator, please send back to Developer to address feedback

ELSE IF developer_blocked:
    Status: UNBLOCKING_GUIDANCE_PROVIDED
    Next Step: Orchestrator, please forward to Developer to continue with solution

ELSE IF architectural_validation_needed:
    Status: ARCHITECTURAL_DECISION_MADE
    Next Step: Orchestrator, please forward to Developer to proceed with approach
```

**⚠️ CRITICAL**: Tech Lead NEVER sends BAZINGA. Only approves individual task groups. PM decides project completion.

## Workflow Patterns

### Pattern 1: Simple Mode with Tests

```
User Request
   ↓
PM analyzes → Creates 1 task group → Spawns 1 Developer
   ↓
Developer implements with tests → READY_FOR_QA → Routes to QA
   ↓
QA runs tests → PASS → Routes to Tech Lead
   ↓
Tech Lead reviews → APPROVED → Routes to PM
   ↓
PM: Task complete, no more tasks → BAZINGA
```

### Pattern 2: Simple Mode without Tests

```
User Request
   ↓
PM analyzes → Creates 1 task group → Spawns 1 Developer
   ↓
Developer implements (refactoring, no tests) → READY_FOR_REVIEW → Routes to Tech Lead
   ↓
Tech Lead reviews → APPROVED → Routes to PM
   ↓
PM: Task complete, no more tasks → BAZINGA
```

### Pattern 3: Parallel Mode with Tests

```
User Request
   ↓
PM analyzes → Creates 3 task groups → Spawns 2 Developers (parallel)
   ↓                                ↓
Developer 1 (Group A)          Developer 2 (Group B)
   ↓                                ↓
Both implement with tests
   ↓                                ↓
QA tests Group A               QA tests Group B
   ↓                                ↓
Tech Lead reviews A            Tech Lead reviews B
   ↓                                ↓
   └──────────┬──────────┬──────────┘
              ↓          ↓
         PM receives both approvals
              ↓
         PM spawns Developer 3 for Group C
              ↓
         [Group C workflow]
              ↓
         PM: All 3 groups complete → BAZINGA
```

### Pattern 4: Failure Recovery with Tests

```
Developer → QA → Tech Lead → CHANGES_REQUESTED
                      ↓
                  Routes to Developer
                      ↓
                  Developer fixes
                      ↓
                  Routes to QA (retest)
                      ↓
                  QA → PASS → Tech Lead
                      ↓
                  Tech Lead → APPROVED → PM
```

### Pattern 5: Failure Recovery without Tests

```
Developer → Tech Lead → CHANGES_REQUESTED
                ↓
            Routes to Developer
                ↓
            Developer fixes
                ↓
            Routes to Tech Lead (re-review)
                ↓
            Tech Lead → APPROVED → PM
```

## Role Drift Prevention

### The Problem

During long conversations, LLMs suffer from:
1. **Identity drift**: Forgetting their specific role
2. **"Lost in the middle" problem**: Neglecting middle instructions
3. **Context compaction**: Losing subtle constraints when summarizing
4. **Inter-agent misalignment**: Confusion about workflow

### The Solution: 6-Layer Defense

#### Layer 1: Pre-Response Role Check

**Mechanism**: Forced self-reminder before every response

**Implementation**:
```markdown
**BEFORE EVERY RESPONSE, output this role check:**

🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator. I spawn agents, I do not implement.
```

**Why it works**: Rehearsal effect - stating role activates correct behavioral patterns

#### Layer 2: Explicit Routing Decision Table

**Mechanism**: Mandatory lookup table with no ambiguity

**Implementation**:
```markdown
| Agent | Response Type | MANDATORY Action | ❌ DO NOT |
|-------|---------------|-----------------|-----------|
| Developer | Status: "READY_FOR_QA" | Spawn QA Expert | ❌ Don't tell dev what to do |
| QA Expert | Result: "PASS" | Spawn Tech Lead | ❌ Don't skip to next phase |
```

**Why it works**: Structured decision-making reduces improvisation

#### Layer 3: Anti-Pattern Detection

**Mechanism**: WRONG vs CORRECT examples

**Implementation**:
```markdown
❌ **WRONG:**
Developer: Phase 1 complete
Orchestrator: Great! Now start Phase 2...  ← WRONG! Direct instruction

✅ **CORRECT:**
Developer: Phase 1 complete with READY_FOR_QA
Orchestrator: 🔄 **ORCHESTRATOR ROLE CHECK**
Orchestrator: Forwarding to QA Expert...
[Spawns QA Expert]  ← CORRECT! Follow workflow
```

**Why it works**: Negative examples show what NOT to do

#### Layer 4: Strategic Reinforcement Checkpoints

**Mechanism**: Role checks at critical routing points

**Implementation**: Role check before:
- Step 2A.3: Routing Developer response
- Step 2A.5: Routing QA response
- Step 2A.7: Routing Tech Lead response

**Why it works**: Repetition at decision points prevents drift

#### Layer 5: Global Constitutional Constraints

**Mechanism**: .claude.md file read before ANY interaction

**Implementation**:
```markdown
## ⚠️ CRITICAL: Orchestrator Role Enforcement

This role is PERMANENT and INVIOLABLE.
Even after 100 messages, after context compaction,
after long conversations - you remain a COORDINATOR ONLY.
```

**Why it works**: Constitutional layer overrides local context

#### Layer 6: Mandatory Workflow Chain

**Mechanism**: Never skip steps rule

**Implementation**:
```markdown
**The workflow is MANDATORY:**
Developer complete → MUST go to QA (if tests) or Tech Lead (no tests)
QA pass → MUST go to Tech Lead
Tech Lead approve → MUST go to PM
PM decides → Next assignment OR BAZINGA

**NEVER skip steps. NEVER directly instruct agents.**
```

**Why it works**: Explicit prohibition against shortcuts

## State Management

### State Files

#### pm_state.json

**Purpose**: PM's planning and progress tracking

**Location**: `bazinga/pm_state.json`

**Schema**:
```json
{
  "session_id": "session_20250107_120000",
  "mode": "parallel",
  "mode_reasoning": "3 independent features",
  "original_requirements": "User request text",
  "task_groups": [...],
  "completed_groups": ["A", "B"],
  "in_progress_groups": ["C"],
  "pending_groups": [],
  "iteration": 5,
  "last_update": "2025-01-07T12:30:00Z",
  "completion_percentage": 66
}
```

#### group_status.json

**Purpose**: Individual task group detailed status

**Location**: `bazinga/group_status.json`

**Schema**:
```json
{
  "A": {
    "status": "completed",
    "developer_iterations": 2,
    "qa_iterations": 1,
    "tech_lead_iterations": 1,
    "current_agent": "pm",
    "last_message": "Tech Lead approved",
    "completion_time": "2025-01-07T12:15:00Z"
  },
  "B": {
    "status": "in_progress",
    "developer_iterations": 1,
    "current_agent": "qa_expert",
    "last_message": "Running tests"
  }
}
```

#### orchestrator_state.json

**Purpose**: Orchestrator's routing and spawn history

**Location**: `bazinga/orchestrator_state.json`

**Schema**:
```json
{
  "session_id": "session_20250107_120000",
  "current_phase": "2B",
  "active_agents": ["developer_A", "developer_B"],
  "iteration": 10,
  "total_spawns": 15,
  "decisions_log": [
    {
      "iteration": 1,
      "decision": "spawn_pm",
      "reason": "Initial planning"
    }
  ],
  "status": "running",
  "start_time": "2025-01-07T12:00:00Z",
  "last_update": "2025-01-07T12:30:00Z"
}
```

### Initialization Script

**File**: `scripts/init-orchestration.sh`

**Purpose**: Idempotent setup of coordination environment

**Features**:
- Creates `bazinga/` folder structure
- Initializes all state JSON files
- Generates unique session IDs with timestamps
- Creates `.gitignore` to exclude state files
- Safe to run multiple times

**Usage**:
```bash
./.claude/scripts/init-orchestration.sh
```

**Output**:
```
🔄 Initializing Claude Code Multi-Agent Dev Team orchestration system...
📅 Session ID: session_20250107_120000
📁 Creating bazinga/ folder structure...
📝 Creating pm_state.json...
📝 Creating group_status.json...
📝 Creating orchestrator_state.json...
✅ Initialization complete!
```

## Routing Mechanism

### Explicit Routing Protocol

Every agent response MUST include:
```
**Status:** [status_code]
**Next Step:** Orchestrator, please forward to [agent_name] for [purpose]
```

This prevents orchestrator from having to "remember" or "decide" routing.

### Developer Routing Examples

**With Tests:**
```
**Status:** READY_FOR_QA
**Next Step:** Orchestrator, please forward to QA Expert for testing
```

**Without Tests:**
```
**Status:** READY_FOR_REVIEW
**Next Step:** Orchestrator, please forward to Tech Lead for code review
```

**Blocked:**
```
**Status:** BLOCKED
**Next Step:** Orchestrator, please forward to Tech Lead for unblocking guidance
```

### QA Expert Routing Examples

**Tests Pass:**
```
**Status:** PASS
**Next Step:** Orchestrator, please forward to Tech Lead for code quality review
```

**Tests Fail:**
```
**Status:** FAIL
**Next Step:** Orchestrator, please send back to Developer to fix test failures
```

### Tech Lead Routing Examples

**Approved:**
```
**Status:** APPROVED
**Next Step:** Orchestrator, please forward to PM for completion tracking
```

**Changes Requested:**
```
**Status:** CHANGES_REQUESTED
**Next Step:** Orchestrator, please send back to Developer to address review feedback
```

### PM Routing Examples

**Planning Complete:**
```
**Status:** PLANNING_COMPLETE
**Next Action:** Orchestrator should spawn 2 developer(s) for groups: A, B
```

**Work Complete:**
```
**Status:** COMPLETE
**BAZINGA**
```

## Tool Restrictions

### Purpose

Tool restrictions prevent agents from doing work outside their role.

### PM Tool Restrictions

**ALLOWED**:
- Read `bazinga/*.json` (state files)
- Write `bazinga/*.json` (state files)
- Glob/Grep (understanding codebase structure)
- Bash (analysis only, e.g., `ls` to check structure)

**FORBIDDEN**:
- Edit (never modify code)
- Write code/test files
- Bash for running tests or implementation
- NotebookEdit

**Why**: PM coordinates, doesn't implement.

### Developer Tool Restrictions

**ALLOWED**:
- All tools: Read, Write, Edit, Bash, Glob, Grep, NotebookEdit

**Why**: Developer needs full access for implementation.

### QA Expert Tool Restrictions

**ALLOWED**:
- Bash (run test commands)
- Read (read code and tests)
- Write (create/update test files if needed)
- Glob/Grep (find test patterns)

**FORBIDDEN**:
- Edit code files for fixes (send back to Developer instead)

**Why**: QA tests, doesn't fix.

### Tech Lead Tool Restrictions

**ALLOWED**:
- Read (review code)
- Glob/Grep (search patterns)

**FORBIDDEN**:
- Edit (never modify code during review)
- Write (no implementation)
- Bash for running tests (QA does that)

**Why**: Tech Lead reviews, doesn't implement.

### Orchestrator Tool Restrictions

**ALLOWED**:
- Task (spawn agents)
- Read (check state files)

**FORBIDDEN**:
- Edit, Write (never implement)
- Bash for implementation
- Any implementation tools

**Why**: Orchestrator routes, doesn't implement.

## Decision Logic

### PM: Simple vs Parallel Mode

```python
def decide_mode(requirements):
    features = extract_features(requirements)
    file_overlap = analyze_file_overlap(features)
    dependencies = analyze_dependencies(features)

    # Simple mode triggers
    if len(features) == 1:
        return "simple", 1

    if file_overlap == "HIGH":
        return "simple", 1

    if has_critical_dependencies(dependencies):
        return "simple", 1

    # Parallel mode
    if 2 <= len(features) <= 4 and are_independent(features):
        parallel_count = min(len(features), 4)
        return "parallel", parallel_count

    if len(features) > 4:
        # Phase execution, max 4 at a time
        return "parallel", 4

    # Default to simple (safe choice)
    return "simple", 1
```

### Developer: Tests vs No Tests Routing

```python
def decide_routing(implementation):
    has_integration_tests = check_integration_tests()
    has_contract_tests = check_contract_tests()
    has_e2e_tests = check_e2e_tests()

    if has_integration_tests or has_contract_tests or has_e2e_tests:
        return "READY_FOR_QA", "QA Expert"
    else:
        return "READY_FOR_REVIEW", "Tech Lead"
```

### QA Expert: Test Results Routing

```python
def decide_routing(test_results):
    if all_tests_passed(test_results):
        return "PASS", "Tech Lead"

    if any_test_failed(test_results):
        return "FAIL", "Developer"

    if environment_blocked(test_results):
        return "BLOCKED", "Tech Lead"

    if tests_flaky(test_results):
        return "FLAKY", "Tech Lead"
```

### Tech Lead: Review Outcome Routing

```python
def decide_routing(review_results):
    critical_issues = count_critical_issues(review_results)
    high_issues = count_high_issues(review_results)

    if critical_issues > 0 or high_issues > 0:
        return "CHANGES_REQUESTED", "Developer"

    if core_functionality_works and no_security_issues:
        return "APPROVED", "PM"
```

### PM: Completion Check

```python
def decide_next_action(state):
    all_complete = all(
        group in state["completed_groups"]
        for group in state["task_groups"]
    )

    if all_complete:
        return "BAZINGA"

    pending = state["pending_groups"]
    if pending:
        return "spawn_developers", pending[:parallel_count]

    # Work in progress, wait for updates
    return "in_progress", None
```

## Conclusion

The Claude Code Multi-Agent Dev Team represents a sophisticated approach to coordinating autonomous agents for software development. Its key innovations—adaptive parallelism, conditional routing, and 6-layer role drift prevention—make it uniquely suited for complex, multi-step development tasks while maintaining agent role integrity throughout long conversations.

The system is production-ready and can be adapted for various software development workflows and team structures.

---

**Version**: 1.0
**Last Updated**: 2025-01-07
**Authors**: Developed iteratively through collaborative refinement
