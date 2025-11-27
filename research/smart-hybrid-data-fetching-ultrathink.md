# Smart Hybrid Data Fetching & Production DB Validation: Deep Analysis

**Date:** 2025-11-27
**Context:** PR #134 review identified polling + socket.io redundancy and DB path fragility
**Decision:** Implement Option D (Smart Hybrid) + Option A (Require in prod with CLI automation)
**Status:** Implementing

---

## Problem Statement

### Issue 1: Polling + Socket.io Redundancy

**Current State:**
- Global polling: `refetchInterval: 10000` in providers.tsx
- Per-component polling: 3000ms (active-session), 5000ms (header, session detail)
- Socket.io infrastructure: Full client/server with Zustand store
- **Result:** Both running simultaneously = wasteful DB queries, unnecessary network traffic

**Impact:**
- Unnecessary database load (SQLite queries every 3-5 seconds per component)
- Network overhead (HTTP requests + WebSocket connections)
- Battery drain on mobile devices
- Potential race conditions between polling and socket updates

### Issue 2: Database Path Fragility

**Current State:**
```typescript
const DB_PATH = process.env.DATABASE_URL ||
  path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");
```

**Problem:**
- Relative path assumes specific directory structure
- Works in development but breaks in:
  - Docker containers (different working directory)
  - Production builds (bundled differently)
  - CI/CD pipelines (arbitrary paths)

---

## Solution

### Part 1: Smart Hybrid Data Fetching

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    React Components                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Header    │  │  Sessions   │  │  Analytics  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         └────────────────┼────────────────┘             │
│                          ▼                               │
│              ┌───────────────────┐                       │
│              │ useSmartRefetch() │                       │
│              │   Custom Hook     │                       │
│              └─────────┬─────────┘                       │
│                        │                                 │
│         ┌──────────────┴──────────────┐                 │
│         ▼                              ▼                 │
│  ┌─────────────┐              ┌─────────────┐           │
│  │  Socket.io  │              │   Polling   │           │
│  │  (Primary)  │              │ (Fallback)  │           │
│  └──────┬──────┘              └──────┬──────┘           │
│         │                            │                   │
│         │  isConnected=true          │  isConnected=false│
│         │  → polling disabled        │  → polling enabled│
│         │  → socket events           │  → refetchInterval│
│         │    invalidate cache        │    = 10000ms      │
│         │                            │                   │
└─────────┴────────────────────────────┴───────────────────┘
```

**Implementation Strategy:**

1. **Create `useSmartRefetch` hook** in `lib/hooks/use-smart-refetch.ts`
   - Reads `isConnected` from socket store
   - Returns `refetchInterval` value: `false` when connected, `10000` when disconnected
   - Provides `triggerRefetch` function for socket event handlers

2. **Wire socket events to cache invalidation**
   - When socket receives events (`session:started`, `log:added`, etc.)
   - Call `trpc.useUtils().invalidate()` to refresh relevant queries
   - This gives us real-time updates without polling

3. **Update components to use smart refetch**
   - Replace hardcoded `refetchInterval` with hook value
   - Components automatically switch between modes

**Benefits:**
- When socket connected: Zero polling, instant updates via WebSocket
- When socket disconnected: Graceful fallback to 10s polling
- Seamless transition between modes
- No user intervention required

### Part 2: Production Database Path Validation

**Implementation:**

1. **Fail-fast in production** (`lib/db/client.ts`):
```typescript
const DB_PATH = process.env.DATABASE_URL || (() => {
  if (process.env.NODE_ENV === 'production') {
    throw new Error(
      'DATABASE_URL environment variable is required in production.\n' +
      'Set it in your deployment configuration or .env file.\n' +
      'Example: DATABASE_URL=/path/to/bazinga/bazinga.db'
    );
  }
  // Development fallback
  return path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");
})();
```

2. **Auto-set DATABASE_URL in start script** (`scripts/start-dashboard.sh`):
```bash
# Auto-detect database path
if [ -z "$DATABASE_URL" ]; then
  # Look for database in common locations
  if [ -f "bazinga/bazinga.db" ]; then
    export DATABASE_URL="$(pwd)/bazinga/bazinga.db"
  elif [ -f "../bazinga/bazinga.db" ]; then
    export DATABASE_URL="$(cd .. && pwd)/bazinga/bazinga.db"
  fi

  if [ -n "$DATABASE_URL" ]; then
    echo "$(date): Auto-detected DATABASE_URL=$DATABASE_URL" >> "$DASHBOARD_LOG"
  fi
fi
```

3. **CLI updates** (`bazinga install`/`update`):
   - When copying dashboard files, also create `.env.local` with DATABASE_URL
   - Path is relative to where database will be created

---

## Critical Analysis

### Pros

**Smart Hybrid:**
- Eliminates 90%+ of unnecessary polling when socket works
- Provides resilience when WebSocket fails
- No changes to component logic (just hook values)
- Backwards compatible

**DB Validation:**
- Fails fast with clear error message
- Auto-detection covers most use cases
- CLI automation eliminates manual configuration

### Cons

**Smart Hybrid:**
- Slightly more complex state management
- Socket events must be comprehensive (no missed updates)
- Need to ensure cache invalidation is granular enough

**DB Validation:**
- Additional environment variable to manage
- Auto-detection could pick wrong database in edge cases

### Mitigations

1. **Socket event coverage:** Current implementation covers all critical events
2. **Cache invalidation granularity:** Use targeted invalidation (`sessions.getById`) not global
3. **DB path ambiguity:** Log which path was auto-detected so users can verify

---

## Implementation Details

### File Changes

| File | Change |
|------|--------|
| `lib/hooks/use-smart-refetch.ts` | NEW - Smart refetch hook |
| `lib/socket/client.ts` | Add cache invalidation on events |
| `components/providers.tsx` | Remove global refetchInterval |
| `components/layout/header.tsx` | Use smart refetch |
| `components/dashboard/active-session.tsx` | Use smart refetch |
| `app/sessions/[sessionId]/page.tsx` | Use smart refetch |
| `lib/db/client.ts` | Add production validation |
| `scripts/start-dashboard.sh` | Auto-detect DATABASE_URL |

### Testing Strategy

1. **Socket connected:** Verify no polling (network tab shows no periodic requests)
2. **Socket disconnected:** Verify polling resumes (10s intervals)
3. **Production build:** Verify error thrown without DATABASE_URL
4. **Auto-detection:** Verify start script finds database

---

## Comparison to Alternatives

### Alternative A: Keep Both (rejected)
- Wastes resources for no benefit
- Potential race conditions

### Alternative B: Socket.io Only (rejected)
- No fallback when WebSocket fails
- Poor user experience in unreliable networks

### Alternative C: Polling Only (rejected)
- Loses real-time capability
- Higher latency for updates

### Alternative D: Smart Hybrid (chosen)
- Best of both worlds
- Graceful degradation
- Optimal resource usage

---

## Decision Rationale

1. **Performance:** Reducing unnecessary polling improves battery life, reduces server load
2. **Reliability:** Fallback ensures data freshness even when WebSocket fails
3. **Developer Experience:** No manual configuration required
4. **Production Safety:** Fail-fast prevents silent failures in deployment

---

## Lessons Learned

1. **Don't over-engineer initially:** Having both polling and socket.io was fine for MVP
2. **Optimize when patterns emerge:** Now that we see both running, we can intelligently combine
3. **Environment variables for deployment:** Always require explicit configuration in production
4. **Automation over documentation:** CLI auto-setup beats README instructions

---

## References

- PR #134 review comments
- Socket.io best practices: https://socket.io/docs/v4/
- React Query caching: https://tanstack.com/query/latest/docs/react/guides/caching
- Next.js environment variables: https://nextjs.org/docs/app/building-your-application/configuring/environment-variables
