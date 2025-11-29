# Dashboard Update Path Bug: Root Cause Analysis

**Date:** 2025-11-29
**Context:** Updating from dashboard v1.0.1 to v1.0.2 doesn't fix BUILD_ID issue
**Decision:** Fix path parameter in update command
**Status:** Identified, fix ready

---

## Problem Statement

When a user has dashboard v1.0.1 installed (missing BUILD_ID) and runs `bazinga update`, the v1.0.2 release is downloaded but the BUILD_ID issue persists. The dashboard still fails to start.

---

## Root Cause

### The Bug

**File:** `src/bazinga_cli/__init__.py`

**Line 1925 (update command):**
```python
bazinga_dir = target_dir / "bazinga"
...
if download_prebuilt_dashboard(bazinga_dir, force=True):  # ← WRONG!
```

**Line 991 (init command):**
```python
if download_prebuilt_dashboard(target_dir, force):  # ← CORRECT!
```

### What Happens

Inside `download_prebuilt_dashboard()`:
```python
dashboard_dir = target_dir / "bazinga" / "dashboard-v2"
```

| Command | Passed `target_dir` | Calculated `dashboard_dir` | Result |
|---------|---------------------|---------------------------|--------|
| `init` | `project_root` | `project_root/bazinga/dashboard-v2` | ✅ Correct |
| `update` | `project_root/bazinga` | `project_root/bazinga/bazinga/dashboard-v2` | ❌ **WRONG** |

### The Effect

During `bazinga update`:
1. Function cleans `bazinga/bazinga/dashboard-v2/.next/` (wrong path)
2. Tarball extracts to `bazinga/bazinga/dashboard-v2/` (wrong path)
3. OLD v1.0.1 files remain at `bazinga/dashboard-v2/` (correct path, untouched!)
4. Startup script looks at `bazinga/dashboard-v2/` → finds OLD broken files
5. BUILD_ID still missing → **ERROR**

---

## Critical Analysis

### Pros of the Fix ✅
1. **One-line fix** - Minimal change, low risk
2. **Matches init behavior** - Consistent with working code path
3. **No breaking changes** - Fix is purely corrective

### Cons / Risks ⚠️
1. **Users with wrong path** - If someone ran `update` before, they have files at wrong path
   - Mitigation: These are orphaned files, won't cause issues
2. **No version check** - Even after fix, old CLI versions have this bug
   - Mitigation: Users need to update CLI first

### Verdict

**Simple, clear bug.** The `update` command passes the wrong directory level to `download_prebuilt_dashboard`. The function expects project root, but update passes the bazinga subdirectory.

---

## The Fix

**Before:**
```python
# Line 1921-1925
bazinga_dir = target_dir / "bazinga"
bazinga_dir.mkdir(parents=True, exist_ok=True)

# Try to download pre-built dashboard from GitHub releases
if download_prebuilt_dashboard(bazinga_dir, force=True):
```

**After:**
```python
# Line 1921-1925
bazinga_dir = target_dir / "bazinga"
bazinga_dir.mkdir(parents=True, exist_ok=True)

# Try to download pre-built dashboard from GitHub releases
if download_prebuilt_dashboard(target_dir, force=True):  # ← Pass target_dir, not bazinga_dir
```

---

## Why This Wasn't Caught

1. **Init works correctly** - Most testing was on fresh installs
2. **Path looks similar** - Easy to confuse `target_dir` and `bazinga_dir`
3. **No update integration test** - No test verifies v1 → v2 upgrade path
4. **Silent failure** - Downloads "succeed" but to wrong location

---

## Test Verification

To verify the fix:

```bash
# 1. Create project with v1.0.1-like state (missing BUILD_ID)
mkdir -p /tmp/test-upgrade/bazinga/dashboard-v2/.next/standalone
touch /tmp/test-upgrade/bazinga/dashboard-v2/.next/standalone/server.js
# Note: NO BUILD_ID file

# 2. Run update (after fix)
cd /tmp/test-upgrade && bazinga update --force

# 3. Verify BUILD_ID now exists at correct path
ls -la /tmp/test-upgrade/bazinga/dashboard-v2/.next/BUILD_ID
ls -la /tmp/test-upgrade/bazinga/dashboard-v2/.next/standalone/.next/BUILD_ID

# 4. Verify NO wrong path was created
ls /tmp/test-upgrade/bazinga/bazinga/  # Should not exist or be empty
```

---

## Lessons Learned

1. **Test upgrade paths** - Fresh install != upgrade behavior
2. **Be explicit about path semantics** - Function docstring should clarify expected path level
3. **Add path validation** - Function could assert expected directory structure
4. **Integration tests for CLI commands** - Unit tests don't catch path mismatches

---

## Related Issues

- Previous analysis: `research/dashboard-build-id-missing-root-cause.md` (incomplete - missed this bug)
- Dashboard startup fix: `scripts/start-dashboard.sh` (graceful fallback, doesn't fix root cause)

---

## References

- Bug location: `src/bazinga_cli/__init__.py:1925`
- Correct pattern: `src/bazinga_cli/__init__.py:991`
- Function definition: `src/bazinga_cli/__init__.py:820`
