# Inter-Agent Communication Design: Context Package System

**Date:** 2025-12-03
**Context:** BAZINGA orchestration system lacks a formal mechanism to pass information (research, failures, decisions) between agents
**Decision:** Implement a Context Package System using artifacts folder + database tracking with proper join tables
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (2025-12-03)

---

## Problem Statement

### The Core Issue

The BAZINGA multi-agent orchestration system has a critical gap: **agents operate in isolation without receiving context from previous agents in the workflow.**

**Evidence from actual orchestration session:**

1. Requirements Engineers (Phase 1) wrote detailed research (21KB HIN OAuth2 analysis with endpoints, code samples, security requirements)
2. Research was saved to `bazinga/artifacts/bazinga_20251202_234053/research_group_P1_R1_HIN.md`
3. PM received only status code `READY_FOR_REVIEW`, not the research content
4. Phase 2 Developers received task specs from original `tasks5.md`, NOT the research findings
5. **Result:** Research was never consumed by implementing developers

### Impact

- Developers re-research problems already solved
- Architectural decisions made without research context
- Wasted tokens on redundant exploration
- Inconsistent implementations (ignoring research recommendations)
- QA failures from missing integration details (e.g., OAuth endpoints)

### Current Communication Flow (Broken)

```
Research Agent → saves file → PM gets status only → Developer gets nothing
                    ↓
              File exists but isn't consumed
```

### Desired Communication Flow

```
Research Agent → saves context package → PM reads & integrates → Developer receives context
                    ↓                          ↓
              Database tracks package    Package included in spawn prompt
```

---

## Solution: Context Package System

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT PACKAGE SYSTEM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Producer   │───▶│   Package    │───▶│   Consumer   │          │
│  │    Agent     │    │    File      │    │    Agent     │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                   ▲                   │
│         ▼                   ▼                   │                   │
│  ┌──────────────────────────────────────────────┴──────────┐       │
│  │                  SQLite Database                         │       │
│  │  ┌───────────────────────────────────────────────────┐  │       │
│  │  │ context_packages (main table)                     │  │       │
│  │  │ - id, session_id, group_id FK, type, file_path    │  │       │
│  │  │ - producer_agent, priority, summary, size_bytes   │  │       │
│  │  │ - supersedes_id, created_at                       │  │       │
│  │  └───────────────────────────────────────────────────┘  │       │
│  │  ┌───────────────────────────────────────────────────┐  │       │
│  │  │ context_package_consumers (join table)            │  │       │
│  │  │ - package_id FK, agent_type, consumed_at          │  │       │
│  │  └───────────────────────────────────────────────────┘  │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  bazinga/artifacts/{SESSION_ID}/context/                 │      │
│  │  ├── research-{group_id}-{topic}.md                      │      │
│  │  ├── failures-{group_id}-{iteration}.md                  │      │
│  │  ├── decisions-{group_id}-{topic}.md                     │      │
│  │  └── handoff-{from_agent}-{to_agent}-{group_id}.md       │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  task_groups.context_references                          │      │
│  │  (JSON array of package file paths for each group)       │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Files for Content** - Large information (research, failure details) stored in markdown files
2. **Database for Metadata** - Tracking, routing, and status management via SQLite with proper join tables
3. **Artifacts Path Alignment** - Context packages stored in `bazinga/artifacts/{SESSION_ID}/context/` (not separate folder)
4. **YAML Front Matter** - Consistent, parseable header format (not HTML comments)
5. **Summary-First Prompts** - Include only summary + path in spawns, agents Read files themselves
6. **Per-Consumer Tracking** - Join table tracks consumption per agent type, allows multiple consumptions
7. **Versioning Support** - `supersedes_id` allows package updates without losing history
8. **Optional Git** - Git commits optional, DB + local artifacts is source of truth

---

## Package Types

### 1. Research Package (`research-*.md`)

**When Created:** Requirements Engineer completes research phase
**Consumer:** Developer implementing the researched feature
**Location:** `bazinga/artifacts/{SESSION_ID}/context/research-{group_id}-{topic}.md`

```markdown
---
type: research
group_id: P1_R1_HIN
producer: requirements_engineer
consumers:
  - developer
  - senior_software_engineer
priority: high
version: 1
---

# HIN OAuth2 Integration Research

## Summary
HIN OAuth2 integration research for Swiss healthcare professional authentication.

## Key Findings

### Authentication Endpoint
- **Authorization URL:** https://oauth2.hin.ch/authorize
- **Token URL:** https://oauth2.hin.ch/REST/v1/getoAuthToken
- **Grant Type:** Authorization Code with PKCE

### Required Scopes
- `openid` - Basic authentication
- `profile` - User profile information
- `hin_id` - HIN-specific identifiers
- `gln` - Global Location Number (healthcare)

### Security Requirements
- MFA required for healthcare professionals
- Token refresh: 1 hour expiry
- Secure storage: HttpOnly cookies recommended

## Code Samples

```typescript
// Recommended OAuth2 configuration
const hinOAuthConfig = {
  clientId: process.env.HIN_CLIENT_ID,
  authorizationEndpoint: 'https://oauth2.hin.ch/authorize',
  tokenEndpoint: 'https://oauth2.hin.ch/REST/v1/getoAuthToken',
  scopes: ['openid', 'profile', 'hin_id', 'gln'],
  pkce: true
};
```

## Integration Recommendations
1. Use existing `@company/oauth2-client` library (already in project)
2. Extend `BaseAuthProvider` class in auth-service
3. Store HIN-specific claims in `user_metadata.hin` field

## References
- [HIN OAuth2 Documentation](https://docs.hin.ch/oauth2)
- [Swiss EPD Integration Guide](https://www.e-health-suisse.ch)
```

### 2. Failure Package (`failures-*.md`)

**When Created:** Developer or QA encounters test/build failures
**Consumer:** Developer on next iteration
**Location:** `bazinga/artifacts/{SESSION_ID}/context/failures-{group_id}-iter{N}.md`

**Note:** This replaces `qa_failures_group_{id}.md` with a consistent format - existing QA failure artifacts should be registered in the same registry.

```markdown
---
type: failures
group_id: group_a
iteration: 2
producer: qa_expert
consumers:
  - developer
priority: critical
version: 1
---

# Test Failures: HIN Authentication (Iteration 2)

## Summary
3 integration tests failing in HIN authentication flow.

## Failure Analysis

### Failure 1: Token Exchange Timeout
- **Test:** `hin-auth.integration.test.ts:45`
- **Error:** `ETIMEDOUT: Connection to oauth2.hin.ch timed out after 5000ms`
- **Root Cause:** Test environment lacks HIN sandbox access
- **Fix:** Mock HIN endpoints in test environment OR configure CI with HIN sandbox credentials

### Failure 2: Invalid Scope Error
- **Test:** `hin-auth.integration.test.ts:78`
- **Error:** `OAuthError: invalid_scope - 'gln' scope requires EPD contract`
- **Root Cause:** GLN scope only available with EPD integration contract
- **Fix:** Make GLN scope conditional, request only when EPD integration is enabled

### Failure 3: PKCE Verifier Mismatch
- **Test:** `hin-auth.unit.test.ts:23`
- **Error:** `PKCEError: code_verifier does not match code_challenge`
- **Root Cause:** Challenge generated with SHA256 but verifier sent as plain
- **Fix:** Ensure `code_challenge_method=S256` is sent with authorization request

## Recommended Fix Order
1. Fix PKCE (unit test, quick win)
2. Fix scope handling (business logic)
3. Fix timeout (environment config, may need DevOps)

## Files to Modify
- `src/providers/hin-provider.ts:89-95` (PKCE fix)
- `src/providers/hin-provider.ts:45-50` (scope handling)
- `tests/integration/setup.ts` (mock configuration)
```

### 3. Decision Package (`decisions-*.md`)

**When Created:** Tech Lead makes architectural decision or PM makes process decision
**Consumer:** Developers, future agents working on related features
**Location:** `bazinga/artifacts/{SESSION_ID}/context/decisions-{group_id}-{topic}.md`

```markdown
---
type: decisions
group_id: group_a
producer: tech_lead
consumers:
  - developer
  - senior_software_engineer
  - qa_expert
priority: medium
version: 1
---

# Architecture Decision: Cantonal e-Santé Adapter Pattern

## Summary
Architectural decision: Use adapter pattern for cantonal e-santé integrations.

## Decision
Implement cantonal e-santé integrations using the Adapter Pattern with a base class.

## Context
Switzerland has 26 cantons, each with potentially different e-santé implementations. We need a scalable approach that allows adding new cantons without modifying core logic.

## Options Considered

### Option A: Direct Integration (Rejected)
- Pros: Simple initial implementation
- Cons: Duplicated code, hard to maintain, N×M complexity

### Option B: Strategy Pattern (Rejected)
- Pros: Runtime switching
- Cons: Overkill for canton selection (known at config time)

### Option C: Adapter Pattern (Selected)
- Pros: Clean separation, testable, extensible
- Cons: Slightly more initial setup

## Implementation Guide

```typescript
// Base adapter (create this first)
abstract class BaseCantonalAdapter {
  abstract getPatientDocuments(patientId: string): Promise<Document[]>;
  abstract uploadDocument(doc: Document): Promise<void>;
  // ... other common methods
}

// Canton-specific adapter (create per canton)
class ZurichAdapter extends BaseCantonalAdapter {
  // Zurich-specific implementation
}

// Factory for instantiation
class CantonAdapterFactory {
  static create(cantonCode: string): BaseCantonalAdapter {
    switch(cantonCode) {
      case 'ZH': return new ZurichAdapter();
      case 'BE': return new BernAdapter();
      default: throw new Error(`Unknown canton: ${cantonCode}`);
    }
  }
}
```

## Constraints
- All adapters must implement full `BaseCantonalAdapter` interface
- Unit tests required for each adapter
- Integration tests against canton sandbox environments
```

### 4. Handoff Package (`handoff-*.md`)

**When Created:** Any agent completing work that needs continuation
**Consumer:** Next agent in workflow
**Location:** `bazinga/artifacts/{SESSION_ID}/context/handoff-{from}-{to}-{group_id}.md`

```markdown
---
type: handoff
group_id: group_a
producer: developer
consumers:
  - qa_expert
priority: high
version: 1
---

# Handoff: Developer → QA Expert (Group A)

## Summary
HIN OAuth2 provider implementation complete, ready for QA testing.

## Completed Work
- [x] Created `src/providers/hin-provider.ts` (OAuth2 provider)
- [x] Created `src/types/hin.types.ts` (TypeScript interfaces)
- [x] Updated `src/auth/index.ts` (registered new provider)
- [x] Created unit tests (12 tests, all passing)
- [x] Created integration test stubs (need HIN sandbox)

## Branch Information
- **Feature Branch:** `feature/hin-oauth2-auth`
- **Base Branch:** `main`
- **Commits:** 3 (see below)

## Test Instructions

```bash
# Unit tests
npm run test:unit -- --grep "HIN"

# Integration tests (requires HIN_SANDBOX_* env vars)
HIN_SANDBOX_CLIENT_ID=xxx npm run test:integration -- --grep "HIN"
```

## Known Limitations
1. GLN scope disabled by default (requires EPD contract)
2. MFA flow not tested with real HIN account
3. Token refresh only tested with mock tokens

## Environment Requirements
- `HIN_CLIENT_ID` - OAuth2 client ID
- `HIN_CLIENT_SECRET` - OAuth2 client secret
- `HIN_SANDBOX_URL` - Sandbox base URL (for testing)

## Questions for QA
1. Do we have HIN sandbox credentials for CI?
2. Should MFA flow be tested manually or mocked?
```

---

## Database Schema Addition

### New Tables: `context_packages` + `context_package_consumers`

**Design rationale:** Use a join table for consumer tracking instead of JSON LIKE queries. This enables:
- Proper indexing for efficient lookups
- Per-consumer consumption tracking (multiple agents can consume same package)
- Clean queries without string pattern matching

```sql
-- Main context packages table
CREATE TABLE IF NOT EXISTS context_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT,  -- FK to task_groups, NULL for global packages
    package_type TEXT NOT NULL CHECK(package_type IN ('research', 'failures', 'decisions', 'handoff', 'investigation')),
    file_path TEXT NOT NULL,
    producer_agent TEXT NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    summary TEXT NOT NULL,  -- Brief description for routing (max 200 chars)
    size_bytes INTEGER,  -- File size for budget decisions
    version INTEGER DEFAULT 1,  -- For package updates
    supersedes_id INTEGER,  -- Previous version if updated
    scope TEXT DEFAULT 'group' CHECK(scope IN ('group', 'global')),  -- Group-specific or session-wide
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (supersedes_id) REFERENCES context_packages(id)
);

-- Consumer tracking join table
CREATE TABLE IF NOT EXISTS context_package_consumers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    agent_type TEXT NOT NULL,  -- developer, qa_expert, tech_lead, etc.
    consumed_at DATETIME,  -- NULL = not yet consumed
    iteration INTEGER DEFAULT 1,  -- Which iteration of the agent consumed it
    FOREIGN KEY (package_id) REFERENCES context_packages(id),
    UNIQUE(package_id, agent_type, iteration)  -- Track per-iteration consumption
);

-- Efficient indexes
CREATE INDEX idx_cp_session ON context_packages(session_id);
CREATE INDEX idx_cp_group ON context_packages(group_id);
CREATE INDEX idx_cp_type ON context_packages(package_type);
CREATE INDEX idx_cp_priority ON context_packages(priority);
CREATE INDEX idx_cp_scope ON context_packages(scope);

CREATE INDEX idx_cpc_package ON context_package_consumers(package_id);
CREATE INDEX idx_cpc_agent ON context_package_consumers(agent_type);
CREATE INDEX idx_cpc_pending ON context_package_consumers(consumed_at) WHERE consumed_at IS NULL;
```

### Task Groups Extension

Add `context_references` column to track which packages are relevant for each group:

```sql
-- Add to existing task_groups table
ALTER TABLE task_groups ADD COLUMN context_references TEXT;  -- JSON array of package IDs
```

This allows PM to explicitly link packages to groups during planning.

---

## Protocol Changes

### 1. Producer Protocol (Agent Creating Context)

When an agent has significant information to pass:

```markdown
## Context Package Created

I have created a context package for the next agent:

**File:** `bazinga/artifacts/{session_id}/context/research-{group_id}-hin-oauth2.md`
**Type:** research
**Priority:** high
**Consumers:** developer, senior_software_engineer
**Summary:** HIN OAuth2 integration research with endpoints, scopes, and code samples

📦 **ORCHESTRATOR:** Please register this context package and ensure it reaches the implementing developer.
```

### 2. Consumer Protocol (Agent Receiving Context)

Orchestrator includes **summary + path only** (not full content) in spawn prompts. Agents read files themselves:

```markdown
## Context Packages Available

The following context packages are relevant to your task. **Read these files before starting.**

| Priority | Type | Summary | File |
|----------|------|---------|------|
| 🔴 HIGH | research | HIN OAuth2 endpoints, scopes, security | `bazinga/artifacts/.../context/research-group_a-hin.md` |
| 🟡 MEDIUM | decision | Use adapter pattern for cantonal integrations | `bazinga/artifacts/.../context/decisions-group_a-adapters.md` |

**Total packages:** 2 (estimated ~600 tokens if fully read)

📋 **Instructions:**
1. Read the context package files listed above using the Read tool
2. Incorporate findings into your implementation
3. If packages conflict, prefer higher priority
```

### 3. Orchestrator Protocol (Routing)

**Prompt inclusion rules** (to avoid token overflow):
- Include at most **K=3** packages per spawn (configurable)
- Prioritize by: `priority DESC, created_at DESC`
- Include only summary + file path (max ~100 tokens per package)
- Agents use Read tool to get full content

Before spawning any agent, orchestrator queries database:

```sql
-- Get packages for agent spawn
SELECT cp.id, cp.package_type, cp.priority, cp.summary, cp.file_path, cp.size_bytes
FROM context_packages cp
JOIN context_package_consumers cpc ON cp.id = cpc.package_id
WHERE cp.session_id = :session_id
  AND (cp.group_id = :group_id OR cp.scope = 'global')
  AND cpc.agent_type = :agent_type
  AND cp.supersedes_id IS NULL  -- Only latest versions
ORDER BY
  CASE cp.priority
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END,
  cp.created_at DESC
LIMIT 3;
```

### 4. Consumption Tracking Protocol

When an agent successfully reads and uses a context package:

```sql
-- Mark package as consumed by agent
UPDATE context_package_consumers
SET consumed_at = CURRENT_TIMESTAMP
WHERE package_id = :package_id
  AND agent_type = :agent_type
  AND iteration = :iteration;
```

**Note:** Consumption is tracked per-agent-type per-iteration, not globally. A package can be consumed multiple times across different agents and iterations.

---

## Implementation Plan

### Phase 1: Database Schema Updates
1. Add `context_packages` table to bazinga-db skill
2. Add `context_package_consumers` join table
3. Add `context_references` column to `task_groups` table
4. Add helper functions:
   - `save_context_package(session_id, group_id, type, file_path, producer, consumers[], priority, summary)`
   - `get_context_packages(session_id, group_id, agent_type, limit=3)`
   - `mark_consumed(package_id, agent_type, iteration)`
   - `update_package(package_id, new_file_path)` - handles versioning/supersedence

### Phase 2: Context Directory Structure
1. Create `bazinga/artifacts/{SESSION_ID}/context/` directory during session init
2. Define file naming conventions (validated by orchestrator):
   - `research-{group_id}-{topic}.md`
   - `failures-{group_id}-iter{N}.md`
   - `decisions-{group_id}-{topic}.md`
   - `handoff-{from}-{to}-{group_id}.md`
3. Implement YAML front matter parser for validation

### Phase 3: Agent Protocol Updates
1. **Requirements Engineer / Investigator:** Add "Context Package Created" output section
2. **Orchestrator:** Query context packages before spawning, include summary table in prompts
3. **Developer / QA / Tech Lead:** Add instructions to read context packages in agent prompts
4. **PM:** Update task_groups.context_references when receiving research deliverables

### Phase 4: Existing Artifact Integration
1. Register existing QA failure artifacts (`qa_failures_group_{id}.md`) in context_packages table
2. Register Investigator reports in context_packages table
3. Migrate without changing existing file locations (add type=qa_failures, type=investigation)

### Phase 5: Testing & Validation
1. Unit tests for database schema and queries
2. Integration test: research→developer handoff flow
3. Integration test: failures→developer iteration flow
4. Test parallel mode with multiple groups
5. Test token budget limits (K=3 packages)

---

## Critical Analysis

### Pros ✅

1. **Solves the core problem** - Research actually reaches developers
2. **Artifacts path alignment** - Uses existing `bazinga/artifacts/` structure, no new directories
3. **Database tracking with proper schema** - Join tables enable efficient queries and per-consumer tracking
4. **Flexible content** - Markdown with YAML front matter, parseable and human-readable
5. **Priority routing** - Critical failures routed before low-priority research
6. **Token-safe prompts** - Summary-first approach avoids context overflow
7. **Versioning support** - Packages can be updated without losing history
8. **Backward compatible** - Existing QA/Investigation artifacts can be registered without changes

### Cons ⚠️

1. **Additional complexity** - Two new tables, protocol changes across agents
2. **Migration effort** - Existing artifacts need to be registered in new schema
3. **Agent prompt changes** - All agents need updated instructions
4. **File size management** - Large research files need size limits

### Mitigations

| Risk | Mitigation |
|------|------------|
| Complexity | Phased rollout: research first, then failures, then decisions |
| Migration | Auto-register existing artifacts during session init |
| Prompt changes | Update agent definitions incrementally, test each |
| File size | Track size_bytes, warn if >50KB, enforce K=3 limit |
| Token overflow | Summary-first prompts (~100 tokens/package), agents Read full files |

### Verdict

**Implement with phased rollout.** The benefits of proper inter-agent communication outweigh the implementation complexity. The improved schema (join tables, versioning, path alignment) addresses the initial design issues identified in review.

---

## Comparison to Alternatives

### Alternative 1: Pass Everything in Prompts
- **Rejected:** Token limits make this infeasible for large research
- **Why ours is better:** Files have no size limit, prompts stay focused

### Alternative 2: Use Only Database (No Files)
- **Rejected:** Large content in database is inefficient, no git history
- **Why ours is better:** Files give git history, database gives routing

### Alternative 3: Shared Memory Store (Redis)
- **Rejected:** Adds infrastructure dependency, ephemeral storage
- **Why ours is better:** Git persistence survives across sessions and environments

### Alternative 4: Message Queue (RabbitMQ/Kafka)
- **Rejected:** Massive over-engineering for file-based agents
- **Why ours is better:** Simpler, uses existing git/sqlite infrastructure

---

## Decision Rationale

This design was chosen because:

1. **Uses existing infrastructure** - Git and SQLite already in BAZINGA
2. **Matches agent model** - Agents already read/write files, this extends that
3. **Solves the actual problem** - Research→Developer handoff explicitly addressed
4. **Minimal changes** - Database addition + protocol update, not architectural rewrite
5. **Testable** - Can verify by checking if developers receive research context

---

## Open Questions (Resolved)

1. **Context package expiry?** - Should old packages auto-expire after N days?
   - **Answer:** No auto-expiry. Cleanup handled by `bazinga cleanup` command which purges entire sessions. Packages are session-scoped.

2. **Cross-session packages?** - Can session B access session A's research?
   - **Answer:** No. Packages are session-scoped by design. For cross-session knowledge, use the `research/` folder (committed to git).

3. **Package versioning?** - What if research is updated mid-session?
   - **Answer:** ✅ Solved with `supersedes_id` and `version` fields. Updates create new packages pointing to previous version.

4. **Conflict resolution?** - Multiple packages for same group_id?
   - **Answer:** Priority-based routing. Critical > High > Medium > Low. Within same priority, most recent wins.

---

## References

- [BAZINGA Agent Communication Analysis](./agent-communication-analysis.md) (this exploration)
- [bazinga-db Skill Documentation](.claude/skills/bazinga-db/SKILL.md)
- [Orchestrator Agent Definition](.claude/agents/orchestrator.md)
- [Project Manager Agent Definition](.claude/agents/project_manager.md)

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-03)
**Gemini:** Skipped (API blocked in Claude Code Web environment)

### Key Issues Identified by OpenAI

| Issue | Severity | Status |
|-------|----------|--------|
| Path conflict with existing artifacts | Critical | ✅ Fixed |
| JSON LIKE queries non-indexable | Critical | ✅ Fixed |
| Single consumed_by insufficient | Critical | ✅ Fixed |
| Git commit requirement unsafe | High | ✅ Fixed |
| Prompt bloat risk | High | ✅ Fixed |
| Duplication with existing QA artifacts | Medium | ✅ Fixed |

### Incorporated Feedback

1. **Path Alignment** (Critical)
   - **Before:** `bazinga/context/{session_id}/`
   - **After:** `bazinga/artifacts/{SESSION_ID}/context/`
   - **Why:** Aligns with existing orchestrator guardrails for artifacts path

2. **Schema Redesign** (Critical)
   - **Before:** `consumer_agents TEXT` with JSON LIKE queries
   - **After:** Join table `context_package_consumers` with proper indexes
   - **Why:** Enables efficient per-consumer tracking and multiple consumptions

3. **Git Optional** (High)
   - **Before:** Required git commit/push for persistence
   - **After:** DB + local artifacts is source of truth, git optional
   - **Why:** Works in environments without git remotes, avoids repo pollution

4. **Summary-First Prompts** (High)
   - **Before:** Include full context in spawn prompts
   - **After:** Include summary + path only, agents Read files themselves
   - **Why:** Prevents token overflow, K=3 package limit, ~100 tokens/package

5. **YAML Front Matter** (Medium)
   - **Before:** HTML comments for metadata
   - **After:** YAML front matter (`---` delimited)
   - **Why:** Consistent with Spec-Kit, parseable, industry standard

6. **Versioning Support** (Medium)
   - **Before:** No versioning
   - **After:** `supersedes_id` + `version` fields
   - **Why:** Allows package updates without losing history

7. **Task Groups Integration** (Medium)
   - **Before:** Separate context_packages lookup
   - **After:** Add `context_references` to task_groups table
   - **Why:** PM can explicitly link packages to groups during planning

8. **Unify with Existing Artifacts** (Medium)
   - **Before:** New package types only
   - **After:** Register existing QA/Investigation artifacts in same registry
   - **Why:** Single source of truth for all context, no duplication

### Rejected Suggestions (With Reasoning)

1. **Security Scan Gate**
   - **Suggestion:** Run security-scan on context packages before registration
   - **Rejected:** Over-engineering for internal agent communication. Context packages contain research findings, not user input. Security scan skill already runs on code changes.

2. **Artifact Index JSON File**
   - **Suggestion:** Generate `artifact_index.json` as fallback when DB unavailable
   - **Rejected:** DB availability is a prerequisite for orchestration. If DB is down, orchestration cannot proceed anyway. Adds complexity without solving a real problem.

3. **Foreign Key Enforcement for group_id**
   - **Suggestion:** Strict FK to task_groups for group_id
   - **Rejected:** Group IDs vary across modes (simple/parallel/spec-kit). Loose coupling preferred with validation at insertion time rather than schema-level constraints.
