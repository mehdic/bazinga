# Dashboard Schema Update: Comprehensive Analysis

**Date:** 2025-12-15
**Context:** Dashboard v2 was built against an older database schema and is now missing several critical tables and columns
**Decision:** Full revamp required to support reasoning capture, context packages, success criteria, and new task group features
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA dashboard-v2 was developed against database schema version ~3-4, but the database has since evolved to **version 12** with significant additions:

1. **Agent Reasoning Capture (v8)** - New columns for tracking agent decision-making process
2. **Event Logging (v9)** - Event subtype/payload for PM BAZINGA, scope changes, validator verdicts
3. **Context Engineering (v10)** - Priority ranking, error patterns, strategies, consumption scope
4. **Skill Multi-Invocation (v11-12)** - Per-agent/group skill outputs with iteration tracking
5. **Success Criteria** - Table for BAZINGA completion validation
6. **Context Packages** - Inter-agent context sharing with priority/summary
7. **Task Group Enhancements** - Branch tracking, merge status, specializations, item_count

The dashboard currently cannot display this critical data, limiting visibility into orchestration quality and agent reasoning.

---

## Current Schema Gap Analysis

### A. Tables Completely Missing from Dashboard

| Table | Version | Purpose | Impact |
|-------|---------|---------|--------|
| `success_criteria` | v4 | BAZINGA validation criteria tracking | Cannot view what criteria PM defined or their verification status |
| `context_packages` | v4 | Inter-agent context files | No visibility into context passed between agents |
| `context_package_consumers` | v4 | Who consumed what context | Cannot track context consumption patterns |
| `error_patterns` | v10 | Learning from failed-then-succeeded agents | Missing error pattern analysis |
| `strategies` | v10 | Successful approaches by topic | Missing strategy recommendations |
| `consumption_scope` | v10 | Iteration-aware context tracking | No context budget visibility |
| `development_plans` | v4 | Development planning | Cannot view development plans |

### B. sessions Table - Missing Columns

| Column | Type | Purpose | Dashboard Impact |
|--------|------|---------|-----------------|
| `initial_branch` | TEXT | Base branch for all work | Cannot show what branch session targets |
| `metadata` | TEXT (v9) | JSON metadata for original_scope | Cannot track scope changes |

### C. orchestration_logs Table - Missing Columns (v8-v9 Additions)

| Column | Type | Purpose | Dashboard Impact |
|--------|------|---------|-----------------|
| `log_type` | TEXT | 'interaction', 'reasoning', or 'event' | Cannot distinguish agent reasoning/events from normal logs |
| `reasoning_phase` | TEXT | understanding/approach/decisions/risks/blockers/pivot/completion | Cannot show structured reasoning phases |
| `confidence_level` | TEXT | high/medium/low | No visibility into agent confidence |
| `references_json` | TEXT | JSON array of files consulted | Cannot show what files agent considered |
| `redacted` | INTEGER | 1 if secrets were redacted | No indication of redacted content |
| `group_id` | TEXT | Task group context | Cannot filter reasoning by task group |
| `event_subtype` | TEXT (v9) | pm_bazinga/scope_change/validator_verdict | Cannot display orchestration events |
| `event_payload` | TEXT (v9) | JSON event data | Cannot show event details |

### D. task_groups Table - Missing Columns

| Column | Type | Purpose | Dashboard Impact |
|--------|------|---------|-----------------|
| `feature_branch` | TEXT | Developer's feature branch | Cannot show branch per task group |
| `merge_status` | TEXT | pending/in_progress/merged/conflict/test_failure | No merge workflow visibility |
| `context_references` | TEXT | JSON array of context package IDs | Cannot show context assigned to group |
| `specializations` | TEXT | JSON array of specialization paths | Cannot show tech stack specializations |
| `item_count` | INTEGER (v9) | Number of tasks in group | Cannot show task counts |

### E. skill_outputs Table - Missing Columns (v11-v12)

| Column | Type | Purpose | Dashboard Impact |
|--------|------|---------|-----------------|
| `agent_type` | TEXT (v11) | Which agent invoked skill | Cannot filter skill outputs by agent |
| `group_id` | TEXT (v11) | Task group context | Cannot associate skill outputs with groups |
| `iteration` | INTEGER (v11) | Multi-invocation tracking | Cannot show skill invocation history |

### F. context_packages Table - Missing Columns (v10)

| Column | Type | Purpose | Dashboard Impact |
|--------|------|---------|-----------------|
| `priority` | TEXT | low/medium/high/critical | Cannot show context priority |
| `summary` | TEXT | Brief package description | Cannot display package summaries |

---

## Solution: Dashboard Update Strategy

### Phase 1: Schema Alignment

**1.1 Update Drizzle Schema (`dashboard-v2/src/lib/db/schema.ts`)**

```typescript
// sessions - add initial_branch
export const sessions = sqliteTable("sessions", {
  sessionId: text("session_id").primaryKey(),
  startTime: text("start_time"),
  endTime: text("end_time"),
  mode: text("mode"),
  originalRequirements: text("original_requirements"),
  status: text("status").default("active"),
  initialBranch: text("initial_branch"),  // NEW
  createdAt: text("created_at"),
});

// orchestration_logs - add reasoning columns
export const orchestrationLogs = sqliteTable("orchestration_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  iteration: integer("iteration"),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  content: text("content").notNull(),
  // NEW v8 columns
  logType: text("log_type").default("interaction"),
  reasoningPhase: text("reasoning_phase"),
  confidenceLevel: text("confidence_level"),
  referencesJson: text("references_json"),
  redacted: integer("redacted").default(0),
  groupId: text("group_id"),
});

// task_groups - add branch/merge/specialization columns
export const taskGroups = sqliteTable("task_groups", {
  id: text("id").primaryKey(),
  sessionId: text("session_id").notNull(),
  name: text("name").notNull(),
  status: text("status").default("pending"),
  assignedTo: text("assigned_to"),
  revisionCount: integer("revision_count").default(0),
  lastReviewStatus: text("last_review_status"),
  complexity: integer("complexity"),
  initialTier: text("initial_tier"),
  // NEW columns
  featureBranch: text("feature_branch"),
  mergeStatus: text("merge_status"),
  contextReferences: text("context_references"),
  specializations: text("specializations"),
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
});

// NEW: success_criteria table
export const successCriteria = sqliteTable("success_criteria", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  criterion: text("criterion").notNull(),
  category: text("category"),
  status: text("status").default("pending"),
  verifiedAt: text("verified_at"),
  verifiedBy: text("verified_by"),
  evidence: text("evidence"),
  createdAt: text("created_at"),
});

// NEW: context_packages table
export const contextPackages = sqliteTable("context_packages", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  groupId: text("group_id"),
  packageType: text("package_type").notNull(),
  filePath: text("file_path").notNull(),
  producerAgent: text("producer_agent").notNull(),
  priority: text("priority").default("medium"),
  summary: text("summary").notNull(),
  sizeBytes: integer("size_bytes"),
  version: integer("version").default(1),
  supersedesId: integer("supersedes_id"),
  scope: text("scope").default("group"),
  createdAt: text("created_at"),
});

// NEW: context_package_consumers table
export const contextPackageConsumers = sqliteTable("context_package_consumers", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  packageId: integer("package_id").notNull(),
  agentType: text("agent_type").notNull(),
  consumedAt: text("consumed_at"),
  iteration: integer("iteration").default(1),
});
```

**1.2 Update Types (`dashboard-v2/src/types/index.ts`)**

Add TypeScript interfaces for all new tables and columns.

### Phase 2: TRPC Router Updates

**2.1 New Queries for Reasoning Data**

```typescript
// Get reasoning logs (separate from interaction logs)
getReasoning: publicProcedure
  .input(z.object({
    sessionId: z.string(),
    groupId: z.string().optional(),
    phase: z.string().optional(),
  }))
  .query(async ({ input }) => {
    const conditions = [
      eq(orchestrationLogs.sessionId, input.sessionId),
      eq(orchestrationLogs.logType, 'reasoning'),
    ];
    if (input.groupId) conditions.push(eq(orchestrationLogs.groupId, input.groupId));
    if (input.phase) conditions.push(eq(orchestrationLogs.reasoningPhase, input.phase));

    return db.select().from(orchestrationLogs)
      .where(and(...conditions))
      .orderBy(orchestrationLogs.timestamp);
  }),

// Get reasoning timeline (grouped by agent and phase)
getReasoningTimeline: publicProcedure
  .input(z.object({ sessionId: z.string() }))
  .query(async ({ input }) => {
    return db.select().from(orchestrationLogs)
      .where(and(
        eq(orchestrationLogs.sessionId, input.sessionId),
        eq(orchestrationLogs.logType, 'reasoning')
      ))
      .orderBy(orchestrationLogs.timestamp);
  }),
```

**2.2 Success Criteria Queries**

```typescript
// Get success criteria for session
getSuccessCriteria: publicProcedure
  .input(z.object({ sessionId: z.string() }))
  .query(async ({ input }) => {
    return db.select().from(successCriteria)
      .where(eq(successCriteria.sessionId, input.sessionId))
      .orderBy(successCriteria.id);
  }),
```

**2.3 Context Packages Queries**

```typescript
// Get context packages for session
getContextPackages: publicProcedure
  .input(z.object({
    sessionId: z.string(),
    groupId: z.string().optional(),
  }))
  .query(async ({ input }) => {
    const conditions = [eq(contextPackages.sessionId, input.sessionId)];
    if (input.groupId) conditions.push(eq(contextPackages.groupId, input.groupId));

    return db.select().from(contextPackages)
      .where(and(...conditions))
      .orderBy(desc(contextPackages.createdAt));
  }),
```

### Phase 3: UI Component Updates

**3.1 New Reasoning Tab**

Create `src/components/reasoning/reasoning-viewer.tsx`:
- Filter by agent type, phase, confidence level
- Show references (files consulted)
- Indicate redacted content
- Timeline view with phase markers
- Confidence indicators (high=green, medium=yellow, low=red)

**3.2 Update Task Groups Display**

Enhance Tasks tab:
- Show feature branch with git icon
- Merge status badge with workflow indicator
- Specializations chips (e.g., "Python 3.11", "FastAPI")
- Context packages linked to group

**3.3 New Success Criteria Tab**

Create `src/components/criteria/success-criteria-viewer.tsx`:
- List all criteria with status badges
- Category grouping
- Verification timeline
- Evidence viewer (for verified criteria)

**3.4 New Context Flow Tab**

Create `src/components/context/context-flow-viewer.tsx`:
- Visual diagram of context flow between agents
- Package details on hover
- Consumption tracking (who read what)
- Priority indicators

**3.5 Update Session Info Card**

Add to session detail:
- Initial branch display
- Total criteria met/pending ratio

### Phase 4: Analytics Enhancements

**4.1 Reasoning Analytics**

- Confidence distribution across sessions
- Which phases take longest
- Files most frequently referenced
- Redaction frequency (security indicator)

**4.2 Context Flow Analytics**

- Context package sizes over time
- Most productive producers
- Consumption patterns by agent type

---

## Critical Analysis

### Pros ✅

1. **Complete Visibility**: Full insight into agent reasoning and decision-making
2. **Debugging Power**: Can trace why agents made specific choices
3. **Quality Gates**: Success criteria tracking ensures completion validation
4. **Context Traceability**: Understand what information flowed where
5. **Merge Workflow**: Git integration visibility for code review process

### Cons ⚠️

1. **Schema Complexity**: More tables and columns to maintain
2. **Performance**: Reasoning logs can be verbose, need pagination
3. **UI Complexity**: More tabs/views may overwhelm users
4. **Migration Risk**: Must handle databases missing new columns gracefully

### Verdict

**Strongly Recommended.** The current dashboard provides minimal insight into the orchestration process. The v8 schema additions (especially reasoning capture) are critical for understanding agent behavior and debugging issues. Without these updates, users cannot:
- Understand WHY agents made decisions
- Track success criteria for completion validation
- See context flow between agents
- Monitor merge workflow status

---

## Implementation Details

### File Changes Required

| File | Changes |
|------|---------|
| `src/lib/db/schema.ts` | Add 3 new tables, update 3 existing tables |
| `src/types/index.ts` | Add interfaces for all new structures |
| `src/lib/trpc/routers/sessions.ts` | Add 6+ new query procedures |
| `src/app/sessions/[sessionId]/page.tsx` | Add new tabs (Reasoning, Criteria, Context) |
| `src/components/reasoning/reasoning-viewer.tsx` | NEW - Reasoning display |
| `src/components/criteria/success-criteria-viewer.tsx` | NEW - Criteria display |
| `src/components/context/context-flow-viewer.tsx` | NEW - Context flow |
| `src/components/logs/log-filters.tsx` | Add log_type filter toggle |
| `src/components/workflow/state-machine.tsx` | Add merge status to task groups |
| `src/app/analytics/page.tsx` | Add reasoning/context analytics |

### Graceful Degradation

All queries must handle missing columns gracefully:
- Use `COALESCE()` for nullable new columns
- Return empty arrays for missing tables
- Add try/catch around new queries with fallback

### Testing Requirements

1. Test with old database (missing new tables/columns)
2. Test with fresh database (all structures present)
3. Test real-time updates via WebSocket
4. Test export functionality with new fields

---

## Comparison to Alternatives

### Alternative 1: Minimal Updates
Only add success_criteria and skip reasoning/context.

**Rejected:** Reasoning capture is the most valuable v8 addition. Skipping it defeats the purpose of the schema evolution.

### Alternative 2: Separate Reasoning Dashboard
Create a new page just for reasoning analysis.

**Considered:** Might reduce main dashboard complexity, but creates fragmented experience. Better to integrate into session detail tabs.

### Alternative 3: Backend Aggregation
Pre-aggregate reasoning/context data server-side.

**Partially Adopted:** For analytics views, aggregation makes sense. For detail views, raw data needed.

---

## Process Notes

### claude.md Update Requirement

**CRITICAL**: After this implementation, add to `.claude/claude.md`:

```markdown
## 🔴 CRITICAL: Dashboard-Schema Synchronization

**When modifying the database schema (bazinga-db skill):**

1. **Update dashboard schema** in `dashboard-v2/src/lib/db/schema.ts`
2. **Update TypeScript types** in `dashboard-v2/src/types/index.ts`
3. **Add TRPC queries** if new tables/columns need display
4. **Update UI components** to show new data
5. **Test both old and new database versions**

**Checklist for schema changes:**
- [ ] `schema.md` updated in bazinga-db skill
- [ ] Dashboard Drizzle schema updated
- [ ] TypeScript interfaces updated
- [ ] TRPC router has queries for new data
- [ ] UI components display new fields
- [ ] Graceful degradation for missing columns
```

---

## Decision Rationale

1. **Why full revamp vs incremental?**
   - Multiple schema versions have accumulated
   - Incremental would require testing each partial state
   - Clean alignment is safer and more maintainable

2. **Why add all new tables?**
   - Success criteria is essential for BAZINGA validation visibility
   - Context packages explain agent collaboration
   - Reasoning capture is the v8 highlight feature

3. **Why new tabs vs embedding in existing?**
   - Reasoning data is substantial - deserves dedicated space
   - Keeps existing views clean
   - Users can focus on specific aspects

---

## Lessons Learned

1. **Schema versioning matters** - Should have established dashboard update process from v4
2. **Document dependencies** - Dashboard depends on DB schema but this wasn't explicit
3. **Test with production data** - Dashboard worked with test data but real sessions showed gaps

---

## References

- `.claude/skills/bazinga-db/references/schema.md` - Authoritative schema documentation
- `research/reasoning-consumption-and-skill-output-schema.md` - v8 schema design
- `research/agent-reasoning-capture-ultrathink.md` - Reasoning capture rationale
- `dashboard-v2/README.md` - Dashboard architecture

---

## Implementation Priority

1. **P0 (Critical)**: Schema alignment, composite PK fix, success criteria display
2. **P1 (High)**: Reasoning viewer, log type filtering, capability detection
3. **P2 (Medium)**: Task group enhancements (branch, merge, specializations)
4. **P3 (Low)**: Context flow visualization, analytics enhancements

---

## Multi-LLM Review Integration

### Consensus Points (OpenAI GPT-5)

The external review identified several critical issues that align with and enhance the original analysis:

1. **Composite Primary Key Bug (CRITICAL)**
   - **Issue**: Dashboard's `task_groups` Drizzle schema uses `id` as sole primary key
   - **Reality**: Database uses composite PK `(id, session_id)`
   - **Impact**: Can cause cross-session collisions, incorrect updates, broken relations
   - **Fix Required**: Update to use Drizzle's `primaryKey` utility for composite key

2. **Performance/Pagination Missing (HIGH)**
   - **Issue**: Proposed reasoning queries lack limits/offsets
   - **Impact**: Large reasoning logs can hang UI and overwhelm server
   - **Fix Required**: All list endpoints need limit (default 50, max 500), offset, date filters

3. **Capability Detection Missing (HIGH)**
   - **Issue**: Queries don't check if columns/tables exist before querying
   - **Impact**: Runtime SQL errors on older databases
   - **Fix Required**: Add schema capability detection at startup, gate UI features

4. **Privacy/Redaction Enforcement (MEDIUM)**
   - **Issue**: Plan only "indicates" redaction, doesn't enforce it
   - **Impact**: Could expose secrets even with redacted flag
   - **Fix Required**: Default to hiding redacted content, add "show" toggle

### Incorporated Feedback

#### 1. Task Groups Composite PK Fix

```typescript
// CORRECTED: Use composite primary key
import { primaryKey } from "drizzle-orm/sqlite-core";

export const taskGroups = sqliteTable("task_groups", {
  id: text("id").notNull(),
  sessionId: text("session_id").notNull(),
  name: text("name").notNull(),
  status: text("status").default("pending"),
  // ... other columns
}, (table) => ({
  pk: primaryKey({ columns: [table.id, table.sessionId] }),
  sessionIdIdx: index("idx_groups_session_id").on(table.sessionId),
}));
```

#### 2. Paginated Reasoning Queries

```typescript
getReasoning: publicProcedure
  .input(z.object({
    sessionId: z.string(),
    groupId: z.string().optional(),
    phase: z.string().optional(),
    limit: z.number().min(1).max(500).default(50),
    offset: z.number().default(0),
  }))
  .query(async ({ input }) => {
    // ... existing conditions
    return db.select().from(orchestrationLogs)
      .where(and(...conditions))
      .orderBy(orchestrationLogs.timestamp)
      .limit(input.limit)
      .offset(input.offset);
  }),
```

#### 3. Schema Capability Detection

```typescript
// Add to src/lib/db/capabilities.ts
interface SchemaCapabilities {
  hasReasoningColumns: boolean;
  hasSuccessCriteria: boolean;
  hasContextPackages: boolean;
  hasTaskGroupExtensions: boolean;
}

async function detectCapabilities(db: Database): Promise<SchemaCapabilities> {
  // Probe for v8 columns
  const hasReasoningColumns = await probeColumn(db, 'orchestration_logs', 'log_type');
  const hasSuccessCriteria = await probeTable(db, 'success_criteria');
  const hasContextPackages = await probeTable(db, 'context_packages');
  const hasTaskGroupExtensions = await probeColumn(db, 'task_groups', 'specializations');

  return { hasReasoningColumns, hasSuccessCriteria, hasContextPackages, hasTaskGroupExtensions };
}

// Cache capabilities at startup, expose via TRPC
getCapabilities: publicProcedure.query(() => cachedCapabilities),
```

#### 4. Redaction Enforcement in UI

```tsx
// In reasoning-viewer.tsx
function ReasoningEntry({ log }: { log: ReasoningLog }) {
  const [showContent, setShowContent] = useState(false);

  if (log.redacted && !showContent) {
    return (
      <div className="p-3 bg-yellow-500/10 border-yellow-500/50">
        <span className="text-yellow-500">Content redacted for security</span>
        <Button variant="ghost" size="sm" onClick={() => setShowContent(true)}>
          Show anyway
        </Button>
      </div>
    );
  }

  return <div>{log.content}</div>;
}
```

### Rejected Suggestions (With Reasoning)

1. **"Derive success criteria from state_snapshots"**
   - **Rejected**: The `success_criteria` table EXISTS in init_db.py (v4+ migration)
   - **Evidence**: `CREATE TABLE IF NOT EXISTS success_criteria` in init_db.py line 1305
   - **Resolution**: Query the table directly as originally planned

2. **"Skip error_patterns, strategies, consumption_scope tables"**
   - **Rejected**: These tables also exist in init_db.py
   - **However**: Agreed these are P3 priority - focus on core tables first

3. **"Progressive rollout of Reasoning tab"**
   - **Partially Accepted**: Start with summary + paginated list, defer complex visualizations

### Updated Priority Matrix

| Priority | Item | Status |
|----------|------|--------|
| **P0** | Composite PK fix for task_groups | **CRITICAL - Added** |
| **P0** | Schema capability detection | **CRITICAL - Added** |
| **P0** | Core schema alignment (sessions, logs, task_groups) | Original |
| **P1** | Pagination for all list queries | **Added** |
| **P1** | Redaction enforcement | **Added** |
| **P1** | Success criteria display | Original |
| **P2** | Reasoning viewer (summary-first approach) | Modified |
| **P2** | Task group enhancements | Original |
| **P3** | Context flow visualization | Original |
| **P3** | Pattern/strategy tables | Deferred |

### Testing Additions (From Review)

1. **Old DB compatibility** - Test with DB missing v8 columns
2. **Partial upgrade** - Test with some tables present, others missing
3. **Large volume** - Test with 10,000+ reasoning logs
4. **Cross-session** - Verify task_groups don't collide across sessions

---

## Final Implementation Checklist

- [ ] Fix composite PK for task_groups (Drizzle + all queries)
- [ ] Add schema capability detection service
- [ ] Add pagination (limit/offset) to all list queries
- [ ] Update Drizzle schema for v8 columns
- [ ] Add TypeScript types for new structures
- [ ] Add success_criteria TRPC queries
- [ ] Add context_packages TRPC queries
- [ ] Create reasoning-viewer component (with redaction)
- [ ] Create success-criteria-viewer component
- [ ] Update log-filters with log_type toggle
- [ ] Update task groups display (branch, merge, specializations)
- [ ] Gate UI features based on capabilities
- [ ] Test with old/new/partial databases
- [ ] Add claude.md dashboard sync documentation
