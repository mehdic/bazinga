# Dashboard Optional Installation: Analysis and Implementation Plan

**Date:** 2025-12-01
**Context:** Dashboard v2 is under active development and not yet stable. Need to clarify this in docs and add CLI option to skip installation.
**Decision:** Make dashboard opt-in with `--dashboard` flag (not installed by default), harden startup scripts, and update documentation with experimental status warnings
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (2025-12-01)

---

## Problem Statement

### Current State
1. **Dashboard is auto-installed** - The `bazinga init` command automatically downloads/copies the dashboard-v2 and installs its npm dependencies
2. **No user choice** - Users cannot opt-out of dashboard installation
3. **No clear status communication** - No warnings that the dashboard is experimental/unstable
4. **User confusion potential** - Users might expect a production-ready monitoring tool

### Issues Identified
1. Dashboard installation adds 30-60 seconds to `bazinga init`
2. Downloads ~50MB of pre-built artifacts or requires npm install
3. Users without node.js get confusing warnings
4. No indication in docs that dashboard is early-stage

---

## Solution

### Part 1: Add `--dashboard` CLI Flag (Opt-In)

> **Note:** This section was updated after user feedback to change from opt-out (`--no-dashboard`) to opt-in (`--dashboard`).

**File:** `src/bazinga_cli/__init__.py`

**Changes:**
1. Add new option to `init` command:
   ```python
   dashboard: bool = typer.Option(
       False, "--dashboard", help="Install experimental dashboard (not included by default)"
   )
   ```

2. Conditionally run dashboard installation steps only if `dashboard` is True:
   - Step 6: Run `download_prebuilt_dashboard()` and source copy if `dashboard`
   - Step 9: Run `install_dashboard_dependencies()` if `dashboard`

3. Add same option to `update` command (with auto-detection of existing installation)

**User Experience:**
```bash
# Default: dashboard NOT installed
bazinga init my-project

# Install dashboard (experimental)
bazinga init my-project --dashboard
```

### Part 2: Update Documentation

**Files to modify:**

1. **`README.md`** - Add Development Status section mentioning dashboard is experimental
2. **`dashboard-v2/README.md`** - Add prominent experimental warning at top
3. **`docs/DOCS_INDEX.md`** - If dashboard is mentioned, clarify status

**Messaging strategy:**
- Clear "EXPERIMENTAL" badge/warning
- Explain no impact on core BAZINGA functionality
- Reporting-only feature (no functional dependency)

---

## Critical Analysis

### Pros ✅

1. **User autonomy** - Users choose what gets installed
2. **Faster installs** - Default skips dashboard, saving 30-60 seconds
3. **Clear expectations** - Experimental status is explicit
4. **Reduced confusion** - Users without node.js get cleaner experience
5. **Lower bandwidth** - Default skips ~50MB download
6. **Production safety** - CI/CD pipelines unaffected by default

### Cons ⚠️

1. **Additional flag** - Slight increase in CLI complexity
2. **Documentation maintenance** - Must update when dashboard becomes stable
3. **Feature discovery** - Users must know to use `--dashboard` flag

### Verdict
**PROCEED** - Benefits clearly outweigh costs. User autonomy and clear communication are essential for experimental features.

---

## Implementation Details

> **Note:** These examples reflect the final opt-in implementation using `--dashboard`.

### Code Changes in `__init__.py`

**Location 1: `init` command signature**
```python
@app.command()
def init(
    project_name: Optional[str] = typer.Argument(...),
    here: bool = typer.Option(...),
    force: bool = typer.Option(...),
    no_git: bool = typer.Option(...),
    dashboard: bool = typer.Option(
        False,
        "--dashboard",
        help="Install experimental dashboard (not included by default)"
    ),
    testing_mode: str = typer.Option(...),
    profile: str = typer.Option(...),
):
```

**Location 2: Step 6 - Dashboard copy**
```python
if dashboard:
    console.print("  [yellow]⚠️  Dashboard is an early experimental feature[/yellow]")
    # ... dashboard installation code ...
else:
    console.print("  [dim]Skipped (use --dashboard to install)[/dim]")
```

**Location 3: Step 9 - Dashboard dependencies**
```python
if dashboard:
    install_dashboard_dependencies(target_dir, force)
else:
    console.print("  [dim]Skipped (use --dashboard to install)[/dim]")
```

### Documentation Updates

**README.md - Add under "Development Status" section:**
```markdown
**Experimental (early development):**
- ⚠️ Real-time Dashboard - Visual monitoring interface for orchestration sessions
  - Under active development, not yet stable
  - No impact on BAZINGA core functionality if not installed
  - Not installed by default; opt-in with: `bazinga init --dashboard`
```

**dashboard-v2/README.md - Add at top after title:**
```markdown
> ⚠️ **EXPERIMENTAL**: This dashboard is under initial development and not yet reliable.
> It provides reporting/monitoring only - skipping it has no impact on BAZINGA's core
> multi-agent orchestration functionality.
>
> - **Not installed by default** - opt-in with: `bazinga init my-project --dashboard`
> - **Install later:** `bazinga setup-dashboard`
> - **Update:** `bazinga update --dashboard`
```

---

## Comparison to Alternatives

### Alternative 1: Make Dashboard Opt-In (not opt-out)
**ACCEPTED** - User requested dashboard to be opt-in after initial review. This makes more sense for an experimental feature - users explicitly choose to install it rather than having to know to skip it.

### Alternative 2: Remove Dashboard from CLI Install Entirely
**Rejected** - Dashboard has value for users who want to monitor orchestration. Removal would harm user experience for those who want it.

### Alternative 3: Interactive Prompt During Install
**Rejected** - Would slow down installs and break automated/CI pipelines. Flag-based approach is cleaner.

---

## Decision Rationale

1. **Opt-in for experimental features** - Experimental features should require explicit user action
2. **Default behavior is clean** - Users who don't need dashboard get faster installs
3. **Clear messaging** - Experimental status is communicated in docs and when using `--dashboard`
4. **No functional impact** - Core BAZINGA works identically with or without dashboard
5. **Future-proof** - When dashboard stabilizes, we can change default to opt-in or remove flag

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users confused by flag | Low | Low | Clear help text explaining experimental status |
| Dashboard never used | Low | Low | Clear documentation and messaging encourage adoption |
| Users expect dashboard to work | Medium | Medium | Prominent warnings in docs and install output |
| CI/CD pipelines break | Very Low | Low | Default is no dashboard, so pipelines unaffected |

---

## Implementation Checklist

1. [x] Add `--dashboard` option to `init` command (opt-in)
2. [x] Add `--dashboard` option to `update` command (with auto-detection)
3. [x] Conditionally run dashboard steps in init only if `--dashboard`
4. [x] Conditionally run dashboard steps in update if `--dashboard` OR existing installation
5. [x] Add experimental warning during dashboard install
6. [x] Update README.md Development Status section
7. [x] Update dashboard-v2/README.md with warning banner
8. [x] Harden start-dashboard scripts (exit 0 if dashboard not installed)
9. [x] Fix setup-dashboard to download dashboard if not present

---

## Files to Modify

1. `src/bazinga_cli/__init__.py` - CLI changes
2. `README.md` - Development status update
3. `dashboard-v2/README.md` - Experimental warning
4. `scripts/start-dashboard.sh` - Graceful exit when dashboard not installed
5. `scripts/start-dashboard.ps1` - Same for Windows

---

## Test Plan

1. **Test default install** - Dashboard should NOT install unless `--dashboard` is specified
2. **Test --dashboard** - Dashboard should be installed cleanly when flag is provided
3. **Test update --dashboard** - Should update dashboard when flag is provided
4. **Test update (no flag, existing dashboard)** - Should auto-detect and update
5. **Test update (no flag, no dashboard)** - Should skip dashboard update by default
6. **Test setup-dashboard after init without --dashboard** - Should download and install
7. **Verify messaging** - All warnings are clear and consistent

---

## References

- CLI code: `src/bazinga_cli/__init__.py`
- Dashboard install: `init()` function steps 6 and 9
- Update command: `update()` function dashboard step
- Dashboard README: `dashboard-v2/README.md`
- Startup scripts: `scripts/start-dashboard.sh`, `scripts/start-dashboard.ps1`

---

## Multi-LLM Review Integration

### Consensus Points (OpenAI Review)

1. **Good direction** - Adding opt-out and explicit experimental messaging is warranted
2. **Startup script hardening required** - Must handle missing dashboard gracefully
3. **Documentation updates needed** - Clear experimental warnings and install-later guidance

### Incorporated Feedback

1. **✅ Harden start-dashboard.sh/ps1** - Scripts must exit cleanly (exit 0) if dashboard not installed, not throw errors
2. **✅ Add "how to install later" guidance** - When skipping dashboard, print command to install later
3. **✅ Update documentation** - Add experimental banners to README.md and dashboard-v2/README.md
4. **✅ Function-based references** - Replaced line numbers with function/section names

### Rejected Suggestions (With Reasoning)

1. **⏭️ Settings.json persistence** - Adds complexity; users can remember the flag for now. Can be added in future enhancement.
2. **⏭️ `bazinga dashboard install/remove/status` subcommands** - Scope creep; existing `setup-dashboard` command can be enhanced later.
3. **⏭️ CI auto-detection** - Nice-to-have but adds complexity; users can set flags in CI scripts.

### Accepted (After User Feedback)

1. **✅ Opt-in instead of opt-out** - User requested dashboard to be opt-in (`--dashboard`) rather than opt-out (`--no-dashboard`). Dashboard is experimental, so opt-in makes more sense.

### Revised Implementation Plan

1. Add `--dashboard` flag to `init` and `update` commands (opt-in, not installed by default)
2. Harden `scripts/start-dashboard.sh` - check dashboard exists before starting
3. Harden `scripts/start-dashboard.ps1` - same check for Windows
4. Print "install later" guidance when dashboard is skipped
5. Update README.md with experimental status
6. Update dashboard-v2/README.md with experimental banner
