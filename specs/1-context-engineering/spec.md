# Feature Specification: Context Engineering System

**Feature Branch**: `1-context-engineering`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Research document at `research/context-engineering-strategy.md`

## Clarifications

### Session 2025-12-12

- Q: Should error patterns be sanitized/redacted before storage? → A: Yes - Apply regex patterns + entropy detection to redact secrets before storage

## User Scenarios & Testing

### User Story 1 - Context-Assembler Skill (Priority: P1)

As an orchestrator, I need a dedicated skill that assembles relevant context for each agent spawn so that agents receive the most useful information within their token budget.

**Why this priority**: Without this, agents either receive too much irrelevant context (token waste) or miss critical information (failures/rework). This is the foundation for all other context improvements.

**Independent Test**: Invoke context-assembler with session_id/group_id/agent_type and verify it returns a structured block with prioritized items, overflow indicator, and stays within budget.

**Acceptance Scenarios**:

1. **Given** an active orchestration session with 5 context packages, **When** context-assembler is invoked for a Developer, **Then** it returns top 3 packages ranked by relevance with "+2 more available" indicator
2. **Given** a model token limit of 100k, **When** assembling context that would exceed 85k, **Then** it truncates least-relevant items and applies 15% safety margin
3. **Given** no context packages exist for a group, **When** context-assembler is invoked, **Then** it returns empty block with "No context packages found" message

---

### User Story 2 - Graduated Token Management (Priority: P2)

As a system operator, I need token budget enforcement with graduated zones so that agents don't get cut off mid-task and context is appropriately sized to remaining budget.

**Why this priority**: Hard cutoffs cause mid-operation failures. Graduated zones allow graceful degradation and prevent costly failures.

**Independent Test**: Simulate different token usage levels (60%, 75%, 85%, 95%) and verify appropriate behavior at each zone.

**Acceptance Scenarios**:

1. **Given** token usage at 55%, **When** context is assembled, **Then** full context with all packages is included (Normal zone)
2. **Given** token usage at 70%, **When** context is assembled, **Then** summarized context is preferred (Soft Warning zone)
3. **Given** token usage at 90%, **When** agent starts operation, **Then** system only allows completion of current operation (Wrap-up zone)

---

### User Story 3 - Error Pattern Capture (Priority: P3)

As a developer agent, I need access to previously-solved error patterns so that I don't waste iterations re-solving known problems.

**Why this priority**: Repeated errors across sessions waste significant time. Capturing solutions enables learning.

**Independent Test**: Create an error, solve it, verify pattern captured, then trigger similar error and verify solution hint is provided.

**Acceptance Scenarios**:

1. **Given** an agent fails with error X then succeeds on retry, **When** the retry completes, **Then** error signature and solution are captured to database
2. **Given** a stored error pattern with confidence > 0.7, **When** a new agent encounters matching error signature, **Then** solution hint is injected into context
3. **Given** an error pattern older than TTL (90 days), **When** cleanup runs, **Then** pattern is removed from database

---

### User Story 4 - Configurable Retrieval Limits (Priority: P4)

As a project maintainer, I need per-agent-type retrieval limits so that different agent roles receive appropriately sized context.

**Why this priority**: QA and Tech Lead need more context than Developers. One-size-fits-all limits are suboptimal.

**Independent Test**: Configure different limits for Developer (3) vs QA (5), invoke context-assembler for each, verify correct counts.

**Acceptance Scenarios**:

1. **Given** config sets Developer retrieval limit to 3, **When** 10 packages exist, **Then** Developer receives 3 packages plus overflow indicator
2. **Given** config sets QA retrieval limit to 5, **When** 10 packages exist, **Then** QA receives 5 packages plus overflow indicator
3. **Given** no config exists for agent type, **When** context-assembler is invoked, **Then** default limit of 3 is used

---

### Edge Cases

- What happens when database is locked during parallel execution?
  - System uses WAL mode and retries with exponential backoff
- How does system handle corrupt or oversized context packages?
  - Skip corrupt packages, log warning, continue with valid ones
- What if token counting differs between estimation and actual?
  - Apply 15% safety margin to account for estimation drift
- How are secrets in error messages handled?
  - Apply regex patterns + entropy detection to redact before storage; configurable allow-lists for false positives

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a `context-assembler` skill that accepts session_id, group_id, agent_type, and model as inputs
- **FR-002**: System MUST rank context packages by priority level, same-group match, agent-type relevance, and recency
- **FR-003**: System MUST enforce per-agent token budgets with model-aware tokenization
- **FR-004**: System MUST apply graduated token zones (Normal/Warning/Conservative/Wrap-up/Emergency)
- **FR-005**: System MUST capture error patterns when agents fail then succeed on retry
- **FR-006**: System MUST inject relevant error pattern solutions into agent context
- **FR-007**: System MUST support configurable retrieval limits per agent type
- **FR-008**: System MUST show overflow indicator when more packages exist than retrieved
- **FR-009**: System MUST handle FTS5 unavailability with heuristic fallback ranking
- **FR-010**: System MUST never block execution on context-assembler failure (graceful degradation)
- **FR-011**: System MUST redact sensitive data (secrets, credentials, PII) from error patterns before storage using regex patterns and entropy detection

### Key Entities

- **ContextPackage**: Research files, investigation findings, or other artifacts to be passed to agents
- **ErrorPattern**: Captured error signature with solution, confidence score, and occurrence count
- **Strategy**: Successful approaches extracted from completed tasks with helpfulness score
- **ConsumptionScope**: Tracking which packages were consumed per session/group/agent/iteration

## Success Criteria

### Measurable Outcomes

- **SC-001**: Average iterations per task group drops below 3 (currently ~4)
- **SC-002**: Prompt sizes stay below 80% of model limit across all agent invocations
- **SC-003**: More than 50% of injected context packages are actually consumed by agents
- **SC-004**: Same error recurrence rate drops below 10% within a session
- **SC-005**: Context assembly completes within 500ms per invocation
- **SC-006**: System operates correctly when FTS5 is unavailable (fallback mode)

## Assumptions

- SQLite WAL mode is available in the deployment environment
- Token estimation accuracy within 15% of actual for target models
- Error patterns are language-agnostic (signature matching, not code-specific)
- Projects have unique identifiers for cross-session isolation
