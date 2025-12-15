# Dashboard Schema Fixes: Critical Bug Analysis

**Date:** 2025-12-15
**Context:** Dashboard-v2 schema misalignment with actual database (init_db.py)
**Decision:** Fix all schema mismatches identified in self-review
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

The dashboard-v2 Drizzle ORM schema has significant misalignments with the actual SQLite database schema defined in `init_db.py`. These bugs cause:
- Runtime failures (calling non-existent methods)
- Silent data issues (wrong column names)
- Misleading code (defining tables that don't exist)

## Issues Identified

### 1. CRITICAL: capabilities.ts uses non-existent Drizzle method

**Current code (BROKEN):**
```typescript
// capabilities.ts lines 27-30, 52-53, 66-68
const result = await db.all(sql`
  SELECT name FROM sqlite_master WHERE type='table' AND name=${tableName}
`);
```

**Problem:** `db.all()` is a better-sqlite3 method, NOT a Drizzle ORM method. Drizzle uses query builder patterns (`db.select().from()`) or `db.execute()` for raw SQL.

**Fix options:**
1. Use raw `sqlite` connection: `sqlite.prepare(...).all()`
2. Use Drizzle's execute: Would need different pattern
3. Use Drizzle select with sql template

**Recommended fix:** Use the raw `sqlite` export which is better-sqlite3 and has `.prepare().all()`.

```typescript
import { sqlite } from "./client";

async function probeTable(tableName: string): Promise<boolean> {
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(tableName)) return false;
  try {
    const stmt = sqlite.prepare(
      `SELECT name FROM sqlite_master WHERE type='table' AND name=?`
    );
    const result = stmt.all(tableName);
    return result.length > 0;
  } catch {
    return false;
  }
}
```

### 2. CRITICAL: development_plans table has completely wrong columns

**Current schema (WRONG):**
```typescript
export const developmentPlans = sqliteTable("development_plans", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  planType: text("plan_type").notNull(),    // DOESN'T EXIST
  planData: text("plan_data").notNull(),    // DOESN'T EXIST
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
});
```

**Actual schema (from init_db.py lines 1283-1295):**
```sql
CREATE TABLE IF NOT EXISTS development_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,        -- NOTE: UNIQUE constraint!
    original_prompt TEXT NOT NULL,
    plan_text TEXT NOT NULL,
    phases TEXT NOT NULL,
    current_phase INTEGER,
    total_phases INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)
```

**Fix:** Complete rewrite of the table definition.

### 3. CRITICAL: Non-existent tables defined in schema

**Tables that DON'T EXIST in init_db.py:**
- `configuration` (lines 115-120 in schema.ts)
- `decisions` (lines 122-130 in schema.ts)
- `model_config` (lines 132-138 in schema.ts)

**Evidence from init_db.py:**
```python
# REMOVED: Configuration table - No use case defined
# See research/empty-tables-analysis.md for details
# Table creation commented out as of 2025-11-21

# REMOVED: Decisions table - Redundant with orchestration_logs
```

**Impact:**
- Queries to these tables will fail (though currently caught by try/catch)
- Relations defined for them are invalid
- Code is misleading

**Fix:** Remove these table definitions and their relations.

### 4. MODERATE: success_criteria index should be UNIQUE

**Current (WRONG):**
```typescript
uniqueCriterionIdx: index("idx_unique_criterion").on(table.sessionId, table.criterion),
```

**Actual (from init_db.py line 1319):**
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_criterion
ON success_criteria(session_id, criterion)
```

**Fix:** Use `uniqueIndex()` instead of `index()`.

### 5. MODERATE: requiredForCompletion null handling

**Current code:**
```typescript
const requiredCriteria = criteria.filter((c) => c.requiredForCompletion);
```

**Problem:** `requiredForCompletion` is INTEGER (0/1/null). JavaScript truthiness:
- `1` → truthy ✅
- `0` → falsy ✅
- `null` → falsy ❌ (should be truthy - DB default is 1)

**Fix:** Explicit comparison: `c.requiredForCompletion !== 0`

### 6. MINOR: CriterionItemProps missing field

The interface doesn't include `requiredForCompletion`, making it incomplete.

### 7. MINOR: Orphaned relations

Relations for non-existent tables (`decisionsRelations`) should be removed.

### 8. MINOR: DevelopmentPlan TypeScript type wrong

The type has `planType` and `planData` which don't exist.

## Proposed Fix Order

1. **capabilities.ts** - Fix first since it's used by other code
2. **schema.ts** - Fix all table definitions
3. **types/index.ts** - Update TypeScript types to match
4. **success-criteria-viewer.tsx** - Fix null handling
5. **Remove orphaned code** - Relations, unused queries
6. **Build test** - Verify compilation

## Risk Assessment

| Fix | Risk Level | Mitigation |
|-----|------------|------------|
| capabilities.ts | Medium | Test with actual DB after fix |
| development_plans | Low | Table rarely used, no breaking changes to existing queries |
| Remove tables | Low | Queries already wrapped in try/catch |
| unique index | Low | Drizzle-level only, doesn't affect DB |
| null handling | Low | Logic fix, no API changes |

## Implementation Checklist

- [ ] Fix capabilities.ts to use sqlite.prepare().all()
- [ ] Rewrite development_plans table definition
- [ ] Remove configuration, decisions, model_config tables
- [ ] Remove orphaned relations
- [ ] Change success_criteria index to uniqueIndex
- [ ] Fix requiredForCompletion null check
- [ ] Update DevelopmentPlan TypeScript type
- [ ] Remove getDecisions from TRPC router (table doesn't exist)
- [ ] Run npm build
- [ ] Verify no TypeScript errors

## Verification Plan

After fixes:
1. `npm run build` - Must succeed
2. Start dashboard against actual bazinga.db
3. Verify capabilities detection works
4. Verify success criteria viewer renders correctly

## Questions for Review

1. Should we keep the `decisions` TRPC endpoint that returns `[]` for backwards compatibility, or remove it entirely?
2. Is there any code depending on `model_config` table that needs migration?
3. Should development_plans queries be added to the dashboard, or is this table unused in UI?

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-15)

### Consensus Points from Review
1. All three capability functions (probeTable, probeColumn, getSchemaVersion) need fixing - not just one
2. skill_outputs needs UNIQUE index to match init_db.py v12
3. Remove all non-existent tables (configuration, decisions, model_config)
4. Use `uniqueIndex()` for UNIQUE constraints in Drizzle

### Incorporated Feedback
1. **Fixed ALL capability functions** - Changed from async Drizzle to sync better-sqlite3
   - `probeTable` → Uses `sqlite.prepare().all()`
   - `probeColumn` → Uses `sqlite.pragma()` for safer PRAGMA execution
   - `getSchemaVersion` → Uses `sqlite.prepare().all()`
2. **Added UNIQUE index to skill_outputs** - Changed from `index()` to `uniqueIndex()`
3. **Fixed development_plans** - Complete rewrite with actual columns + UNIQUE session_id constraint
4. **Explicit null handling** - `requiredForCompletion !== 0` instead of truthy check

### Rejected Suggestions (With Reasoning)
1. **Generate Drizzle types from SQLite introspection** - Good long-term idea but out of scope for this fix
2. **Align all index names with init_db.py** - Not blocking, deferred to future cleanup
3. **Add TypeScript union types for enums** - Good idea but out of scope for this fix

### Implementation Status: COMPLETE
- [x] capabilities.ts - All three functions fixed
- [x] schema.ts - development_plans, success_criteria, skill_outputs fixed
- [x] schema.ts - Removed configuration, decisions, model_config
- [x] types/index.ts - DevelopmentPlan type updated
- [x] sessions.ts - Removed getDecisions query
- [x] success-criteria-viewer.tsx - Fixed null handling
- [x] Build passes successfully
