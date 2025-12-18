# BAZINGA 2.0 - "Lite by Default" Implementation Plan

## Executive Summary

Transform BAZINGA from "everything enabled" to "lite by default, advanced opt-in" while keeping all existing functionality intact.

**Core Principle:** Simple defaults + progressive disclosure = better UX

---

## ✅ Phase 1: README & Documentation (COMPLETED)

### Files Changed
- ✅ `README.md` - Rewritten to lead with parallel developers killer feature

### Next Steps
- Create `docs/ADVANCED.md` - Move complex features here
- Create `docs/QUICK_REFERENCE.md` - Simple user guide
- Update `docs/DOCS_INDEX.md` - Reorganize doc structure

---

## 🔧 Phase 2: Default Configuration Changes

### 2.1 CLI Changes (`src/bazinga_cli/__init__.py`)

**Current behavior:**
```python
testing_mode: str = typer.Option("minimal", ...)  # Already good!
```

**Changes needed:**
```python
# Add new parameter
profile: str = typer.Option(
    "lite",
    "--profile",
    "-p",
    help="Configuration profile: lite (default), advanced, or custom"
)

# Add skills selection
skills: Optional[str] = typer.Option(
    None,
    "--skills",
    help="Skills to enable: 'core', 'all', or comma-separated list"
)
```

**New flag logic:**
```python
if profile == "lite":
    # Enable only core skills (security-scan, lint-check, test-coverage)
    # Testing mode: minimal
    # Parallelism: enabled (automatic)
    # Advanced skills: disabled

elif profile == "advanced":
    # Enable all skills
    # Testing mode: full
    # Parallelism: enabled (automatic)
    # QA Expert: enabled

elif profile == "custom":
    # Use individual flags (--testing, --skills, etc.)
    pass
```

**Lines to modify:** 748-890 (init function)

**Impact:** LOW - Just adding new options, existing flags still work

---

### 2.2 Init Script Changes (`scripts/init-orchestration.sh`)

**Current:** Creates default configs with all skills enabled

**Changes needed:**

**Around line 50-100 (where skills_config.json is created):**

```bash
# NEW: Create lite profile by default
cat > bazinga/skills_config.json << 'EOF'
{
  "_metadata": {
    "profile": "lite",
    "version": "2.0",
    "description": "Lite profile - core skills only for fast development",
    "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "disabled",
    "test-pattern-analysis": "disabled",
    "api-contract-validation": "disabled",
    "db-migration-check": "disabled"
  },
  "qa_expert": {
    "pattern-miner": "disabled",
    "quality-dashboard": "disabled"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "lint-check": "mandatory",
    "test-coverage": "mandatory"
  },
  "pm": {
    "velocity-tracker": "disabled"
  }
}
EOF
```

**Impact:** MEDIUM - Changes default experience for new users

---

### 2.3 Testing Config (`bazinga/testing_config.json`)

**Current:** Created by init script

**Changes:** Already defaults to "minimal" - NO CHANGES NEEDED ✅

---

## 🛡️ Phase 3: Graceful Degradation (Skills)

### Critical Change: All 10 skills need graceful degradation

**Current behavior:** Skills fail if tools missing

**New behavior:** Skills skip gracefully in lite mode, fail in advanced mode

### 3.1 Template Pattern (Apply to ALL skills)

**File:** `.claude/skills/*/[script].sh` or `*.py`

**Add at the top of each script:**

```bash
#!/bin/bash
# Skill: [name]

# Check if required tool is installed
if ! command -v [tool] &> /dev/null; then
    # Load profile
    PROFILE=$(jq -r '._metadata.profile // "lite"' bazinga/skills_config.json 2>/dev/null || echo "lite")

    if [ "$PROFILE" = "lite" ]; then
        # Lite mode: Warn but don't fail
        cat > bazinga/[output].json << EOF
{
  "status": "skipped",
  "reason": "[tool] not installed",
  "recommendation": "Install with: [install command]",
  "impact": "This check was skipped. Install [tool] for [benefit]."
}
EOF
        echo "⚠️  [Skill name] skipped: [tool] not installed" >&2
        exit 0
    else
        # Advanced mode: User explicitly enabled, so fail
        cat > bazinga/[output].json << EOF
{
  "status": "error",
  "reason": "[tool] required but not installed",
  "recommendation": "Install with: [install command]"
}
EOF
        echo "❌ [Skill name] failed: [tool] not installed" >&2
        exit 1
    fi
fi

# Tool is installed, proceed normally...
```

### 3.2 Skills to Update (10 total)

#### Core Skills (3) - MUST work or skip gracefully

**1. `security-scan` (.claude/skills/security-scan/scan.sh)**
- Tools: bandit, semgrep, gosec, npm audit, brakeman, spotbugs
- Lines to modify: ~50-100 (add graceful degradation at start)
- **Priority:** HIGH

**2. `lint-check` (.claude/skills/lint-check/lint.sh)**
- Tools: ruff, pylint, eslint, golangci-lint, rubocop, checkstyle
- Lines to modify: ~40-80
- **Priority:** HIGH

**3. `test-coverage` (.claude/skills/test-coverage/coverage.sh)**
- Tools: pytest-cov, jest, go test, simplecov, jacoco
- Lines to modify: ~40-80
- **Priority:** HIGH

#### Advanced Skills (7) - Default disabled, skip if not installed

**4. `velocity-tracker` (.claude/skills/velocity-tracker/track.sh)**
- No external dependencies (bash/jq only)
- Lines to modify: ~30-50
- **Priority:** LOW (already mostly safe)

**5. `codebase-analysis` (.claude/skills/codebase-analysis/analyze.py)**
- Dependencies: Python built-ins only
- Lines to modify: ~20-40
- **Priority:** LOW (safe, but add graceful message)

**6. `test-pattern-analysis` (.claude/skills/test-pattern-analysis/analyze_tests.py)**
- Dependencies: Python built-ins only
- Lines to modify: ~20-40
- **Priority:** LOW

**7. `api-contract-validation` (.claude/skills/api-contract-validation/validate.py)**
- Dependencies: pyyaml (already in deps)
- Lines to modify: ~30-50
- **Priority:** LOW

**8. `db-migration-check` (.claude/skills/db-migration-check/check.py)**
- Dependencies: Python built-ins only
- Lines to modify: ~30-50
- **Priority:** LOW

**9. `pattern-miner` (.claude/skills/pattern-miner/mine.sh)**
- Dependencies: jq, git
- Lines to modify: ~40-80
- **Priority:** LOW

**10. `quality-dashboard` (.claude/skills/quality-dashboard/dashboard.sh)**
- Dependencies: jq
- Lines to modify: ~40-80
- **Priority:** LOW

### Impact Summary
- **Files to modify:** 10 skill scripts
- **Code pattern:** Same template for all
- **Risk:** LOW - Adding graceful handling, not changing core logic
- **Testing:** Each skill should be tested with tool missing

---

## 📝 Phase 4: Agent File Cleanup

### 4.1 Orchestrator (`agents/orchestrator.md`)

**Current:** 2,560 lines with extensive instructions

**Changes needed:**

**Section: Initialization (Lines 130-302)**
- ✅ Keep skills config loading (already there)
- ✅ Keep testing config loading (already there)
- Update language to emphasize defaults

**No functional changes needed!** Already reads configs properly.

**Minor doc updates:**
- Lines 160-200: Add note about lite vs advanced profiles
- Example: "Default (lite): 3 skills active, Advanced: 10 skills active"

**Impact:** MINIMAL - Documentation clarification only

---

### 4.2 Developer (`agents/developer.md`)

**Changes needed:**

**Section: Skills section (appears in orchestrator's developer prompt building)**

Currently orchestrator builds developer prompt dynamically based on skills_config.json.
No changes to developer.md needed - it's template-driven.

**Impact:** NONE - Already dynamic ✅

---

### 4.3 Tech Lead (`agents/tech_lead.md`)

**Current:** Already receives skills config from orchestrator

**Changes needed:**

**Section: Skills invocation**

Currently orchestrator builds tech lead prompt with skills.
No changes to tech_lead.md needed - it's template-driven.

**Impact:** NONE - Already dynamic ✅

---

### 4.4 PM (`agents/project_manager.md`)

**Changes needed:**

**Section: Velocity tracker invocation**

PM prompt is built by orchestrator with velocity-tracker skill conditionally.
No changes to pm.md needed - it's template-driven.

**Impact:** NONE - Already dynamic ✅

---

### 4.5 QA Expert (`agents/qa_expert.md`)

**Changes needed:**

**Section: Advanced skills (pattern-miner, quality-dashboard)**

QA prompt is built by orchestrator conditionally.
No changes to qa_expert.md needed - it's template-driven.

**Impact:** NONE - Already dynamic ✅

---

**FINDING:** Agent files are well-architected! Orchestrator dynamically builds prompts based on config. No agent file changes needed. 🎉

---

## 🎯 Phase 5: New Slash Commands

### 5.1 Update Existing Commands

**File:** `.claude/commands/bazinga.configure-skills.md`

**Current:** Lists all skills equally

**Changes needed:**

Add section at top:
```markdown
**Current Profile:** [lite/advanced/custom]

You are currently using the [PROFILE] profile.

[LITE]: Fast development with core quality gates (3 skills)
[ADVANCED]: Comprehensive analysis with all features (10 skills)
[CUSTOM]: Individually selected skills
```

Update skills list:
```markdown
[CORE SKILLS - Active in Lite Profile]
✓ 1. security-scan       (Tech Lead) - Vulnerability detection
✓ 2. lint-check          (Developer, Tech Lead) - Code quality
✓ 3. test-coverage       (Tech Lead) - Coverage analysis

[ADVANCED SKILLS - Opt-in]
  4. velocity-tracker    (PM) - Metrics and velocity
  5. codebase-analysis   (Developer) - Pattern extraction
  ...
```

**Lines to modify:** ~20-80

---

### 5.2 Create New Command (Optional)

**File:** `.claude/commands/bazinga.configure-profile.md` (NEW)

```markdown
---
name: bazinga.configure-profile
description: Switch between lite and advanced profiles
---

# Profile Configuration

Change your BAZINGA configuration profile.

## Current Profile

[Read from bazinga/skills_config.json -> _metadata.profile]

## Available Profiles

### 1. Lite (Default)
- **Speed:** Fast iteration
- **Skills:** 3 core skills (security, lint, coverage)
- **Testing:** Minimal (lint + unit tests)
- **Parallelism:** Enabled (automatic)
- **Best for:** Most projects, fast development

### 2. Advanced
- **Speed:** Comprehensive analysis
- **Skills:** All 10 skills enabled
- **Testing:** Full (QA Expert + integration tests)
- **Parallelism:** Enabled (automatic)
- **Best for:** Production-critical features, complex projects

### 3. Custom
- **Speed:** Your choice
- **Skills:** Pick individual skills via /bazinga.configure-skills
- **Testing:** Choose mode via /bazinga.configure-testing
- **Best for:** Specific needs

## Select Profile

[Instructions for updating bazinga/skills_config.json and testing_config.json]

## Apply Profile

After selecting, restart orchestration for changes to take effect.
```

**Impact:** OPTIONAL - Nice-to-have but not critical

---

## 📚 Phase 6: Documentation Restructuring

### 6.1 Create New Files

**1. `docs/ADVANCED.md` (NEW)**

Move from README:
- Spec-kit integration details
- Tech debt tracking
- Role drift prevention deep-dive
- PM metrics and velocity tracking details
- All advanced skills documentation
- Architecture details

**2. `docs/QUICK_REFERENCE.md` (NEW)**

Simple 1-page guide:
- Quick start
- Common commands
- Default configuration
- When to use advanced features
- Troubleshooting quick tips

---

### 6.2 Update Existing Files

**1. `docs/SKILLS.md`**

Reorganize:
```markdown
# Skills Reference

## Core Skills (Lite Profile)

### security-scan
[Current content]

### lint-check
[Current content]

### test-coverage
[Current content]

---

## Advanced Skills (Opt-in)

### velocity-tracker
[Current content]

...
```

**2. `docs/DOCS_INDEX.md`**

Update navigation:
```markdown
# Documentation Index

## For Most Users (Lite Profile)
- README.md - Quick start
- QUICK_REFERENCE.md - Common commands
- EXAMPLES.md - Usage patterns

## For Advanced Users
- ADVANCED.md - Advanced features
- SKILLS.md - Complete skills reference
- ARCHITECTURE.md - How it works

## For Contributors
- ROLE_DRIFT_PREVENTION.md
- MODEL_ESCALATION.md
- ...
```

---

## 🧪 Phase 7: Testing Strategy

### 7.1 Manual Testing Checklist

**Lite Profile (Default):**
- [ ] `bazinga init test-lite`
- [ ] Verify skills_config.json has profile="lite"
- [ ] Verify only 3 skills enabled
- [ ] Run orchestration with missing tools (should warn, not fail)
- [ ] Verify parallel mode works
- [ ] Verify security/lint/coverage run

**Advanced Profile:**
- [ ] `bazinga init test-advanced --profile advanced`
- [ ] Verify all 10 skills enabled
- [ ] Verify full testing mode
- [ ] Verify QA Expert spawns
- [ ] Run with missing tools (should fail in advanced mode)

**Graceful Degradation:**
- [ ] Remove bandit: `pip uninstall bandit`
- [ ] Run orchestration in lite mode → should warn and continue
- [ ] Run orchestration in advanced mode → should fail
- [ ] Repeat for each core skill tool

### 7.2 Automated Tests

**Add to `tests/test_cli.py`:**
```python
def test_init_lite_profile():
    """Test that lite profile creates correct config"""
    # Run init with lite profile
    # Verify skills_config.json has lite profile
    # Verify only 3 skills are mandatory
    pass

def test_init_advanced_profile():
    """Test that advanced profile enables all skills"""
    pass

def test_graceful_degradation():
    """Test that skills skip when tools missing in lite mode"""
    pass
```

---

## 📊 Impact Analysis

### Files Changed Summary

| Category | Files | Impact | Risk |
|----------|-------|--------|------|
| **Documentation** | 5 files | New docs, README rewrite | LOW |
| **CLI** | 1 file | Add profile flag | LOW |
| **Init Scripts** | 1 file | Change default config | MEDIUM |
| **Skills** | 10 files | Add graceful degradation | LOW-MEDIUM |
| **Agents** | 0 files | No changes (already dynamic) | NONE |
| **Commands** | 2 files | Update/create config commands | LOW |

**Total files modified:** ~19 files
**Total new files:** ~3 files
**Risk level:** LOW-MEDIUM (mostly adding features, not changing core logic)

---

## 🚀 Implementation Order (Recommended)

### Week 1: Foundation
1. ✅ README rewrite (DONE)
2. Update init script with lite defaults
3. Add profile flag to CLI

### Week 2: Graceful Degradation
4. Add graceful degradation template
5. Update 3 core skills (security-scan, lint-check, test-coverage)
6. Test core skills with missing tools

### Week 3: Advanced Skills
7. Update 7 advanced skills with graceful degradation
8. Test all skills
9. Update configure-skills command

### Week 4: Documentation & Polish
10. Create ADVANCED.md
11. Create QUICK_REFERENCE.md
12. Update SKILLS.md organization
13. Add automated tests
14. Final testing

---

## ⚠️ Breaking Changes

**NONE!** This is purely additive:
- Existing `bazinga init` commands still work
- Existing flags (--testing, etc.) still work
- Just changes the defaults for new users
- Advanced users can use `--profile advanced` to get old behavior

---

## 🎯 Success Metrics

After implementation:
1. **New user experience:** Can run `bazinga init my-project` with zero config
2. **Missing tools:** Warns but continues (doesn't break)
3. **Advanced users:** Can opt-in to full features easily
4. **Documentation:** Clear path from beginner → advanced
5. **No regressions:** All existing functionality still works

---

## 📝 Open Questions

1. **CLI flag naming:** Should `--profile advanced` be `--advanced`? (More concise)
2. **Skill auto-install:** Should lite mode offer to install missing tools? (Could be annoying)
3. **Migration:** Should we auto-migrate existing projects to lite? (Probably not - leave them as-is)
4. **Profile switching:** Should we create `/bazinga.configure-profile` or keep it in `/bazinga.configure-skills`?

---

## Next Steps

Ready to implement? Start with:

```bash
# 1. Update init script
vim scripts/init-orchestration.sh

# 2. Add CLI profile flag
vim src/bazinga_cli/__init__.py

# 3. Add graceful degradation to core skills
vim .claude/skills/security-scan/scan.sh
vim .claude/skills/lint-check/lint.sh
vim .claude/skills/test-coverage/coverage.sh
```

Then test thoroughly before moving to advanced skills and documentation.
