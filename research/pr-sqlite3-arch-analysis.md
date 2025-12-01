# SQLite3 Architecture Mismatch Analysis

**Date:** 2025-12-01
**Context:** User running `bazinga update` on Intel Mac gets arm64 binaries
**Decision:** Fix GitHub Actions runner for darwin-x64
**Status:** Proposed

---

## Problem Statement

User on Intel Mac (x86_64) ran `bazinga update`, downloaded `bazinga-dashboard-darwin-x64.tar.gz` (v1.0.2), but the `better-sqlite3` native binary inside is compiled for arm64.

Error:
```
incompatible architecture (have 'arm64', need 'x86_64h' or 'x86_64')
```

## Root Cause

**The GitHub Actions workflow uses `macos-latest` for darwin-x64 builds:**

```yaml
matrix:
  include:
    - os: macos-latest    # BUG: This is now arm64!
      platform: darwin
      arch: x64
    - os: macos-14        # Also arm64
      platform: darwin
      arch: arm64
```

**GitHub changed `macos-latest` to point to `macos-14` (Apple Silicon) in late 2024.**

Both builds are running on arm64 runners, so the "darwin-x64" package contains arm64 native binaries.

## Solution

Use `macos-13` for darwin-x64 builds (the last Intel macOS runner):

```yaml
matrix:
  include:
    - os: macos-13        # Intel Mac (x86_64)
      platform: darwin
      arch: x64
    - os: macos-14        # Apple Silicon (arm64)
      platform: darwin
      arch: arm64
```

## Why This Wasn't Caught

1. The package downloads correctly (`darwin-x64.tar.gz`)
2. The extraction works
3. Only fails at runtime when Node.js tries to load the native addon
4. No CI test validates the binary architecture

## Additional Fix Applied

Also included better-sqlite3 native module in the release package for the socket server (separate commit).

## Verification

After fix, releases should be tested:
1. Download darwin-x64 package on Intel Mac
2. Run: `file .next/standalone/node_modules/better-sqlite3/build/Release/better_sqlite3.node`
3. Should show: `Mach-O 64-bit bundle x86_64`

## References

- GitHub macos-latest migration: https://github.blog/changelog/2024-04-01-macos-14-sonoma-is-generally-available-on-github-actions/
- Affected release: dashboard-v1.0.2
