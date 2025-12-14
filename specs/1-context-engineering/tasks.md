# Tasks: Context Engineering System

**Input**: Design documents from `/specs/1-context-engineering/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Integration tests included where appropriate for skill validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Skill files**: `.claude/skills/context-assembler/`
- **Database schema**: `orchestrix/orchestrix.db` (via orchestrix-db skill)
- **Config**: `orchestrix/skills_config.json`
- **Tests**: `tests/skills/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database schema setup

- [x] T001 Create skill directory structure at `.claude/skills/context-assembler/`
- [x] T002 [P] Add `context_engineering` section to `orchestrix/skills_config.json`
- [x] T003 [P] Create skill reference docs at `.claude/skills/context-assembler/references/usage.md`

---

## Phase 2: Foundational (Database Schema)

**Purpose**: Database tables that MUST exist before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend `context_packages` table with `priority` and `summary` columns via orchestrix-db skill
- [x] T005 [P] Create `error_patterns` table with schema from data-model.md
- [x] T006 [P] Create `strategies` table with schema from data-model.md
- [x] T007 [P] Create `consumption_scope` table with schema from data-model.md
- [x] T008 Enable WAL mode on orchestrix.db (`PRAGMA journal_mode=WAL`)
- [x] T009 Create indexes per data-model.md specifications

**Checkpoint**: Database schema ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Context-Assembler Skill (Priority: P1) 🎯 MVP

**Goal**: A skill that assembles relevant context for agent spawns with prioritized ranking

**Independent Test**: Invoke context-assembler with session_id/group_id/agent_type and verify it returns structured block with prioritized items and overflow indicator

**Functional Requirements**: FR-001, FR-002, FR-008, FR-009, FR-010

### Implementation for User Story 1

- [x] T010 [US1] Create `SKILL.md` with skill definition at `.claude/skills/context-assembler/SKILL.md`
- [x] T011 [US1] Implement heuristic relevance ranking logic in SKILL.md instructions:
  - Priority weight (critical > high > medium > low)
  - Same-group boost
  - Agent-type relevance
  - Recency
- [x] T012 [US1] Implement package retrieval via orchestrix-db skill queries
- [x] T013 [US1] Add output formatting per quickstart.md specification:
  - `## Context for {agent_type}` header
  - `### Relevant Packages ({count}/{available})` section
  - Priority indicators `[HIGH]`, `[MEDIUM]`, `[LOW]`
  - Overflow indicator `📦 +{N} more packages available`
- [x] T014 [US1] Handle empty packages case ("No context packages found" message)
- [x] T015 [US1] Implement FTS5 availability check and heuristic fallback (FR-009)
- [x] T016 [US1] Add graceful degradation on skill failure - return minimal context, log warning (FR-010)

**Checkpoint**: Context-assembler skill functional with basic ranking and output formatting

---

## Phase 4: User Story 2 - Graduated Token Management (Priority: P2)

**Goal**: Token budget enforcement with graduated zones for graceful degradation

**Independent Test**: Simulate different token usage levels (60%, 75%, 85%, 95%) and verify appropriate behavior at each zone

**Functional Requirements**: FR-003, FR-004

### Implementation for User Story 2

- [x] T017 [US2] Add tiktoken dependency documentation to skill usage.md
- [x] T018 [US2] Implement model-aware token estimation in SKILL.md:
  - Model ID to tiktoken encoding mapping
  - 15% safety margin calculation
- [x] T019 [US2] Implement graduated zone detection logic:
  - Normal (0-60%): Full context
  - Soft Warning (60-75%): Prefer summaries
  - Conservative (75-85%): Minimal context
  - Wrap-up (85-95%): Complete current only
  - Emergency (95%+): Checkpoint and break
- [x] T020 [US2] Add zone indicator to output (`🔶 Token budget: {Zone} ({percent}%)`)
- [x] T021 [US2] Implement summary-preference logic for Soft Warning zone
- [x] T022 [US2] Implement truncation behavior for Conservative/Wrap-up zones
- [x] T023 [US2] Add token budget allocation per agent type (from plan.md):
  - Developer: Task 50%, Specialization 20%, Context 20%, Errors 10%
  - Senior Software Engineer: Task 40%, Specialization 20%, Context 25%, Errors 15%
  - QA Expert: Task 40%, Specialization 15%, Context 30%, Errors 15%
  - Tech Lead: Task 30%, Specialization 15%, Context 40%, Errors 15%

**Checkpoint**: Token management with graduated zones working across all agent types ✅

---

## Phase 5: User Story 3 - Error Pattern Capture (Priority: P3)

**Goal**: Capture error patterns when agents fail-then-succeed and inject solutions for similar errors

**Independent Test**: Create an error, solve it, verify pattern captured, trigger similar error, verify solution hint provided

**Functional Requirements**: FR-005, FR-006, FR-011

### Implementation for User Story 3

- [X] T024 [US3] Implement error signature extraction logic:
  - Error type extraction
  - Message pattern normalization
  - Context hints extraction
  - Stack pattern extraction
- [X] T025 [US3] Implement secret redaction before storage (FR-011):
  - Regex patterns for common secrets (API keys, passwords, tokens)
  - Entropy detection for high-entropy strings
  - Configurable via `redaction_mode` setting
- [X] T026 [US3] Implement pattern_hash generation (SHA256 of normalized signature)
- [X] T027 [US3] Add error pattern capture to fail-then-succeed flow:
  - Initial confidence 0.5
  - Store via orchestrix-db skill
- [X] T028 [US3] Implement error pattern matching query:
  - Project isolation (project_id)
  - Language filtering (optional)
  - Confidence threshold (> 0.7 for injection)
- [X] T029 [US3] Add error pattern section to context output:
  - `### Error Patterns ({count} matches)` header
  - Warning icon `⚠️ **Known Issue**: {message}`
  - Solution hint with confidence
- [X] T030 [US3] Implement confidence adjustment rules:
  - Successful match: +0.1 (max 1.0)
  - False positive report: -0.2 (min 0.1)
  - Below 0.3: Don't inject, observe only
- [X] T031 [US3] Implement TTL-based cleanup query (patterns older than `ttl_days`)

**Checkpoint**: Error pattern capture, matching, and injection working end-to-end ✅

---

## Phase 6: User Story 4 - Configurable Retrieval Limits (Priority: P4)

**Goal**: Per-agent-type retrieval limits configurable via skills_config.json

**Independent Test**: Configure different limits for Developer (3) vs QA (5), invoke context-assembler, verify correct counts

**Functional Requirements**: FR-007

### Implementation for User Story 4

- [X] T032 [US4] Add retrieval_limits schema to skills_config.json:
  ```json
  "context_engineering": {
    "retrieval_limits": {
      "developer": 3,
      "senior_software_engineer": 5,
      "qa_expert": 5,
      "tech_lead": 5,
      "investigator": 5
    }
  }
  ```
- [X] T033 [US4] Implement config reading in SKILL.md instructions
- [X] T034 [US4] Apply limit during package retrieval (LIMIT clause)
- [X] T035 [US4] Default fallback when agent type not in config (default: 3)
- [X] T036 [US4] Update overflow indicator calculation to use dynamic limit

**Checkpoint**: Configurable retrieval limits working for all agent types ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Add consumption tracking to `consumption_scope` table on each context delivery
- [X] T038 [P] Implement strategies table population (extract insights from successful tasks)
- [X] T039 [P] Add database lock retry logic (exponential backoff: 100ms, 200ms, 400ms)
- [X] T040 [P] Update orchestrix-db skill to expose context engineering table operations
- [X] T041 Validate quickstart.md scenarios against implementation
- [X] T042 Integrate context-assembler into orchestrator spawn workflow:

  **Problem**: Currently orchestrator queries `orchestrix-db` directly for context packages (see `phase_simple.md` lines 24-35, 604-616, 743-755). The context-assembler skill exists but is never invoked. The 2000 token cap in context-assembler (SKILL.md line 149) is a workaround because `current_tokens` is never passed.

  **Solution - Part A: Token Estimation in Orchestrator**
  1. Track `total_spawns` in orchestrator state (already exists at line 832 in orchestrator.md)
  2. After each Task() spawn, increment: `total_spawns += 1`
  3. Estimate tokens: `estimated_tokens = total_spawns * 15000` (avg ~15k tokens per spawn cycle)
  4. Store in session via orchestrix-db: `estimated_token_usage` field

  **Solution - Part B: Replace Direct orchestrix-db Calls**

  Update `orchestrix/templates/orchestrator/phase_simple.md`:
  - Lines 24-35: Replace orchestrix-db context query with context-assembler invocation
  - Lines 604-616: Same for QA Expert spawn
  - Lines 743-755: Same for Tech Lead spawn

  Update `orchestrix/templates/orchestrator/phase_parallel.md`:
  - Lines 163-174: Same pattern for parallel spawns

  **New Context Query Pattern** (replace existing):
  ```
  context-assembler, please assemble context:

  Session ID: {session_id}
  Group ID: {group_id}
  Agent Type: {agent_type}
  Model: {MODEL_CONFIG[agent_type]}
  Current Tokens: {estimated_token_usage}
  Iteration: {iteration}
  ```
  Then invoke: `Skill(command: "context-assembler")`

  **Solution - Part C: Remove 2000 Token Cap**
  After orchestrator passes real `current_tokens`, remove the conservative cap from SKILL.md (lines 147-151) since zone detection will work properly.

  **Files to Modify**:
  - `orchestrix/templates/orchestrator/phase_simple.md` (3 locations)
  - `orchestrix/templates/orchestrator/phase_parallel.md` (1 location)
  - `agents/orchestrator.md` (add token tracking after spawns)
  - `.claude/skills/context-assembler/SKILL.md` (remove 2000 cap after integration)

  **Validation**:
  - Spawn 5+ agents in sequence, verify estimated_token_usage increases
  - At spawn 6+, zone should shift from Normal to Soft_Warning (~90k estimated)
  - Verify context-assembler returns truncated summaries in Soft_Warning zone
- [X] T043 Performance validation: context assembly < 500ms (SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 - MVP, must complete first
- **User Story 2 (Phase 4)**: Depends on Phase 3 (builds on skill)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (uses error_patterns table)
- **User Story 4 (Phase 6)**: Depends on Phase 3 (modifies skill behavior)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 2 (Schema)
    │
    ├──► US1 (P1) Context-Assembler ──► US2 (P2) Token Zones
    │                                        │
    │                                        └──► US4 (P4) Config Limits
    │
    └──► US3 (P3) Error Patterns (can parallel with US1)
```

- **US1 and US3 can run in parallel** after Phase 2 (different concerns)
- **US2 must follow US1** (extends the skill)
- **US4 must follow US1** (modifies skill behavior)

### Within Each User Story

- Schema/models before business logic
- Core implementation before integrations
- Story complete before moving to next priority
- Commit after each task or logical group

### Parallel Opportunities

- T002, T003 can run in parallel (different files)
- T005, T006, T007 can run in parallel (independent tables)
- US1 and US3 can run in parallel after Phase 2
- T037, T038, T039, T040 can run in parallel (different concerns)

---

## Parallel Example: Phase 2 (Database Schema)

```bash
# Launch all table creation tasks together:
Task: "Create error_patterns table with schema from data-model.md"
Task: "Create strategies table with schema from data-model.md"
Task: "Create consumption_scope table with schema from data-model.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test context-assembler skill independently
5. Deploy/demo basic context assembly

### Recommended Order (Sequential)

1. Setup + Foundational → Schema ready
2. User Story 1 (P1) → Test context-assembler MVP
3. User Story 3 (P3) → Test error pattern capture
4. User Story 2 (P2) → Test token zones
5. User Story 4 (P4) → Test configurable limits
6. Polish → Final validation

### Parallel Team Strategy

With multiple developers after Phase 2:
- Developer A: User Story 1 → User Story 2 → User Story 4
- Developer B: User Story 3 (independent error patterns)

---

## Success Criteria Mapping

| Task Range | Success Criteria |
|------------|------------------|
| T010-T016 | SC-006 (FTS5 fallback) |
| T017-T023 | SC-002 (prompt sizes < 80%) |
| T024-T031 | SC-004 (error recurrence < 10%) |
| T037 | SC-003 (consumption tracking > 50%) |
| T043 | SC-005 (assembly < 500ms) |
| All | SC-001 (iterations < 3 per task group) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
