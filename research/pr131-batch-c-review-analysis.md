# PR #131 Batch C Review Analysis

**Date:** 2025-11-26
**Context:** Review feedback after Batch C dashboard features
**Status:** ✅ ALL ISSUES RESOLVED

---

## Critical Issues (P1 - Must Fix)

### 1. Schema Mismatch - Drizzle vs Actual Database ✅ FIXED

**Issue:** Drizzle schema defines columns that don't exist in the actual SQLite database.

**Specific Mismatches:**
- `sessions` table: `id` (autoincrement), `developer_count`, `updated_at` don't exist
- `token_usage` table: `model_tier`, `tokens_used` vs actual `tokens_estimated`

**Risk:** Runtime "no such column" errors when queries execute.

**Resolution:** Commit `c869c94` - Completely rewrote schema to match actual database.

### 2. WAL Pragma with Read-Only Mode ✅ FIXED

**Issue:** Code opens database as read-only but tries to set WAL mode:
```typescript
_sqlite = new Database(DB_PATH, { readonly: true });
_sqlite.pragma("journal_mode = WAL");  // SQLITE_READONLY error
```

**Risk:** Crashes when database file exists.

**Resolution:** Commit `c869c94` - Removed WAL pragma.

### 3. `.gitignore` Missing `.env` Files ✅ FIXED

**Issue:** No exclusion for `.env`, `.env.local`, etc.

**Risk:** Credential leaks if environment files are committed.

**Resolution:** Commit `a18cd81` - Added `.env`, `.env.*`, `!.env.example` patterns.

### 4. ESM `__dirname` Compatibility ✅ FIXED

**Issue:** `drizzle.config.ts` uses `__dirname` which is undefined in ES Modules.

**Resolution:** Commit `a18cd81` - Replaced with `process.cwd()`.

### 5. `package-lock.json` Blocking Diff Review ✅ FIXED

**Issue:** 10,000+ line file truncating PR diff, blocking code review.

**Resolution:** Commit `4fcce3b` - Removed from git, added to .gitignore.

---

## Medium Issues (P2 - Should Fix)

### 4. Unused Imports

**Files with unused imports:**
- `active-session.tsx`: `Clock`, `Zap`
- `sessions/page.tsx`: `ScrollArea`, `cn`, `Bot`, `TrendingUp`
- Various: `Legend`, `DropdownMenuItem`

**Risk:** Code bloat, linter warnings.

**Fix:** Remove unused imports from affected files.

### 5. Root `.gitignore` Regression

**Issue:** Changed from `lib/` to `/lib/` which could un-ignore nested library folders.

**Risk:** Virtual environment libraries could be committed.

**Fix:** Verify the pattern is correct for project structure.

---

## Low Issues (P3 - Can Defer)

### 6. `__dirname` ESM Compatibility

**Issue:** `__dirname` used in drizzle config may not work in ES Modules.

**Context:** Next.js handles this, may not be actual issue.

**Decision:** Defer - verify if actually causing problems.

### 7. Unused `useQuery` with `enabled: false`

**Issue:** Query hook called but result never used.

**Context:** May be intentional for conditional fetching.

**Decision:** Defer - investigate actual usage pattern.

---

## Action Plan

1. **IMMEDIATE:** Fix schema mismatch - align with actual database
2. **IMMEDIATE:** Fix WAL pragma conflict
3. **IMMEDIATE:** Add `.env` to gitignore
4. **SOON:** Clean up unused imports
5. **DEFER:** ESM compatibility (verify if issue first)

---

## Schema Reference

From `.claude/skills/bazinga-db/references/schema.md`:

```sql
-- Actual sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    mode TEXT CHECK(mode IN ('simple', 'parallel')),
    original_requirements TEXT,
    status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Actual token_usage table
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_type TEXT NOT NULL,
    agent_id TEXT,
    tokens_estimated INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)
```

Note: No `model_tier`, `tokens_used`, `estimated_cost` columns in actual schema.
