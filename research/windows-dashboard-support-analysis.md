# Windows Dashboard Support: Deep Analysis

**Date:** 2025-11-28
**Context:** BAZINGA Dashboard v2 lacks Windows pre-built packages and startup scripts
**Decision:** Implement tiered Windows support with clear user guidance
**Status:** Proposed

---

## Problem Statement

Windows users currently cannot use the BAZINGA Dashboard v2 in standalone/pre-built mode. The current situation:

1. **No Windows pre-built package** - GitHub releases only include Linux/macOS tarballs
2. **PowerShell startup script only supports v1** - `start-dashboard.ps1` runs Python dashboard
3. **No Windows standalone script** - `start-standalone.sh` has no `.ps1` equivalent
4. **Native module challenges** - `better-sqlite3` requires C++ build tools on Windows

---

## Current State Analysis

### What Works on Windows

| Component | Status | Notes |
|-----------|--------|-------|
| CLI installation | ✅ Works | `bazinga install` detects Windows |
| Platform detection | ✅ Works | Correctly identifies `windows` platform |
| Script type selection | ✅ Works | Auto-selects PowerShell |
| Dashboard v1 (Python) | ✅ Works | Cross-platform Python server |
| npm install fallback | ⚠️ Works* | Requires npm, C++ build tools |

### What's Missing

| Component | Status | Impact |
|-----------|--------|--------|
| Windows pre-built tarball | ❌ Missing | Forces npm install path |
| `start-dashboard.ps1` v2 support | ❌ Missing | Can't start v2 dashboard |
| `start-standalone.ps1` | ❌ Missing | No standalone startup option |
| GitHub Actions Windows build | ❌ Missing | No automated package creation |
| Windows documentation | ❌ Missing | Users have no guidance |

---

## Solution Options

### Option A: Full Parity (Build Windows Packages)

**Approach:** Add Windows to GitHub Actions build matrix, create pre-built packages.

**Pros:**
- Full feature parity with Linux/macOS
- Zero npm/node-gyp requirements for users
- Consistent experience across platforms

**Cons:**
- `better-sqlite3` native module must be compiled for Windows
- Tarball format unusual on Windows (though supported since Win10 1803)
- Significant CI complexity
- Native module version locking issues

**Effort:** High (8-12 hours)

### Option B: npm-Based Solution (Recommended)

**Approach:** Windows users build from source via npm, but with clear automation and documentation.

**Pros:**
- Simpler implementation
- Node.js/npm common in Windows dev environments
- Can ship pre-compiled `better-sqlite3` binaries via npm
- Lower maintenance burden

**Cons:**
- Longer first-time setup (npm install takes 2-3 minutes)
- Requires Node.js + npm
- May need Visual Studio Build Tools for native modules

**Effort:** Medium (4-6 hours)

### Option C: Docker-Based Solution

**Approach:** Provide Docker Compose for Windows users with Docker Desktop.

**Pros:**
- Zero native dependencies
- Identical experience to Linux/macOS
- WSL2 makes Docker fast on Windows

**Cons:**
- Docker Desktop license requirements for enterprise
- Additional resource usage
- Not all Windows devs have Docker

**Effort:** Low (2-3 hours)

---

## Recommended Solution: Option B + C Hybrid

**Primary:** npm-based with enhanced PowerShell scripts
**Alternative:** Docker Compose for users who prefer containerization

### Why This Approach

1. **Pragmatic:** Most Windows developers have Node.js installed
2. **Low maintenance:** No Windows-specific builds to maintain
3. **Fallback option:** Docker provides escape hatch
4. **Clear upgrade path:** Can add pre-built packages later if demand warrants

---

## Implementation Plan

### Phase 1: PowerShell Scripts (Required)

**Files to create/modify:**

1. **`scripts/start-dashboard.ps1`** - Update for v2 support
   - Add standalone mode detection
   - Add Next.js server startup
   - Add Socket.io server startup
   - Maintain v1 fallback

2. **`dashboard-v2/scripts/start-standalone.ps1`** - New file
   - Mirror bash version functionality
   - Use PowerShell-native commands

### Phase 2: CLI Improvements (Required)

**Files to modify:**

1. **`src/bazinga_cli/__init__.py`**
   - Lines 849-852: Improve Windows message
   - Add clear guidance on npm install path
   - Add prerequisite check for Visual Studio Build Tools

### Phase 3: Documentation (Required)

**Files to create:**

1. **`docs/WINDOWS_SETUP.md`** - Comprehensive Windows guide
   - Prerequisites (Node.js, npm, optional VS Build Tools)
   - Step-by-step installation
   - Troubleshooting native module builds
   - Docker alternative

### Phase 4: GitHub Actions (Optional)

**Files to modify:**

1. **`.github/workflows/dashboard-release.yml`**
   - Add `windows-latest` to matrix
   - Handle Windows-specific paths
   - Use PowerShell commands in "Prepare release package" step

### Phase 5: Release Notes (Required)

**Files to modify:**

1. **`.github/workflows/dashboard-release.yml`**
   - Update release body to include Windows guidance
   - Add Windows section to packages table

---

## Detailed File Changes

### 1. `scripts/start-dashboard.ps1` (Lines 110-195)

**Current behavior:** Only starts Python dashboard (v1)

**Required changes:**
- Add detection for `dashboard-v2/.next/standalone/server.js`
- Add Node.js server startup for v2 standalone
- Add development mode fallback (npm run dev)
- Add Socket.io server startup
- Maintain backward compatibility with v1

### 2. New: `dashboard-v2/scripts/start-standalone.ps1`

```powershell
# Key sections needed:
- Standalone build detection
- Static file copying (Copy-Item instead of cp -r)
- Environment variable handling
- Node.js server startup with exec-equivalent
```

### 3. `src/bazinga_cli/__init__.py` (Lines 849-852)

**Current:**
```python
if platform == "windows":
    console.print("  [dim]Pre-built packages not available for Windows, will use npm[/dim]")
    return False
```

**Proposed:**
```python
if platform == "windows":
    console.print("  [dim]Pre-built packages not available for Windows[/dim]")
    console.print("  [dim]Windows users: Dashboard will be built from source (npm install)[/dim]")
    console.print("  [dim]This requires Node.js 18+ and npm[/dim]")
    return False
```

### 4. `.github/workflows/dashboard-release.yml` (Lines 155-159)

**Current release body table:**
```markdown
| Platform | Architecture | File |
|----------|--------------|------|
| Linux    | x64          | bazinga-dashboard-linux-x64.tar.gz |
| macOS    | x64          | bazinga-dashboard-darwin-x64.tar.gz |
| macOS    | arm64        | bazinga-dashboard-darwin-arm64.tar.gz |
```

**Proposed addition:**
```markdown
| Platform | Architecture | File |
|----------|--------------|------|
| Linux    | x64          | bazinga-dashboard-linux-x64.tar.gz |
| macOS    | x64          | bazinga-dashboard-darwin-x64.tar.gz |
| macOS    | arm64        | bazinga-dashboard-darwin-arm64.tar.gz |
| Windows  | x64          | Build from source (see docs/WINDOWS_SETUP.md) |
```

---

## Technical Considerations

### better-sqlite3 on Windows

The `better-sqlite3` npm package requires native compilation. Options:

1. **Pre-built binaries:** npm already ships pre-built binaries for common platforms
2. **Build from source:** Requires Visual Studio Build Tools + Python 3
3. **Alternative:** Could use `sql.js` (pure JS) but with performance tradeoff

**Recommendation:** Most Windows users with Node.js already have build tools. Document the requirement clearly.

### Path Handling

Windows uses backslashes. Key areas to check:
- Tarball extraction (use `os.path.normpath`)
- Database path resolution
- Script path detection

**Current code already handles this:** `__init__.py:945` uses `os.path.normpath`

### Port Conflicts

Windows may have services on port 3000 (common dev port).
**Recommendation:** Keep configurable `DASHBOARD_PORT` (already supported)

---

## Testing Matrix

| Test Case | Linux | macOS | Windows |
|-----------|-------|-------|---------|
| CLI detects platform | ✅ | ✅ | ✅ |
| Pre-built download | ✅ | ✅ | N/A (by design) |
| npm install fallback | ✅ | ✅ | ⚠️ Test |
| Dashboard v1 startup | ✅ | ✅ | ✅ |
| Dashboard v2 standalone | ✅ | ✅ | ⚠️ Add |
| Dashboard v2 dev mode | ✅ | ✅ | ⚠️ Test |
| Database connectivity | ✅ | ✅ | ⚠️ Test |

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| better-sqlite3 build fails | Medium | High | Document prerequisites, offer sql.js fallback |
| Users don't have Node.js | Low | Medium | Clear docs, Docker alternative |
| PowerShell version issues | Low | Low | Use PS 5.1+ compatible syntax |
| Path separator issues | Low | Medium | Use Path.join, os.path throughout |

---

## Decision Rationale

**Choosing npm-based over pre-built Windows packages because:**

1. **80/20 rule:** Most Windows developers in target audience already have Node.js
2. **Maintenance burden:** One less platform to build/test/maintain
3. **Native modules:** Windows builds of better-sqlite3 can be fragile
4. **Clear upgrade path:** Can add pre-built later if demand warrants
5. **Docker fallback:** Provides escape hatch for edge cases

---

## Files to Change Summary

| File | Action | Priority |
|------|--------|----------|
| `scripts/start-dashboard.ps1` | Modify - add v2 support | P0 |
| `dashboard-v2/scripts/start-standalone.ps1` | Create new | P0 |
| `src/bazinga_cli/__init__.py` | Modify - improve Windows message | P1 |
| `docs/WINDOWS_SETUP.md` | Create new | P1 |
| `.github/workflows/dashboard-release.yml` | Modify - update release notes | P1 |
| `README.md` | Modify - add Windows note | P2 |

---

## Success Criteria

1. Windows user can run `bazinga install` and get dashboard working
2. Clear error messages guide users through prerequisites
3. `start-dashboard.ps1` can start both v1 and v2 dashboards
4. Documentation covers common Windows issues
5. No changes break existing Linux/macOS functionality

---

## References

- Current CLI code: `src/bazinga_cli/__init__.py:788-1057`
- Bash startup script: `scripts/start-dashboard.sh`
- PowerShell v1 script: `scripts/start-dashboard.ps1`
- GitHub Actions workflow: `.github/workflows/dashboard-release.yml`
- better-sqlite3 docs: https://github.com/WiseLibs/better-sqlite3
