# Package Distribution Review - TODO

## Issue: config/claude.md Contains BAZINGA-Specific Content

**Date:** 2025-11-19
**Status:** TODO - Needs Review

### Problem

The `config/claude.md` file that gets copied to client projects contains BAZINGA-specific content:
- Line 3: `> **Repository:** https://github.com/mehdic/bazinga`
- Line 5: "This project uses BAZINGA..." (referring to BAZINGA itself, not client project)

**Current behavior:**
When users run `bazinga init`, the CLI copies `config/claude.md` to their project's `.claude/CLAUDE.md`. This file should be generic, not contain BAZINGA's own repository information.

### What Needs Review

**TODO:** Check if `config/claude.md` should be:
1. A generic template (no BAZINGA repo URL, generic project description)
2. Something that was replaced/deleted and needs to be restored from git history
3. Different from what currently exists

### Current Package Distribution (pyproject.toml)

```toml
[tool.hatch.build.targets.wheel.shared-data]
"config" = "share/bazinga_cli/config"
```

This distributes:
- `config/claude.md` - Contains BAZINGA-specific content (PROBLEM)
- `config/coordination.gitignore` - Generic gitignore rules (OK)

### Files in Package

**Included (correct):**
- ✅ `.claude/templates/project_context.template.json` - PM fallback template
- ✅ `config/coordination.gitignore` - Generic gitignore

**Included (needs review):**
- ⚠️ `config/claude.md` - Contains BAZINGA repo URL and BAZINGA-specific context

**Not included (correct):**
- ❌ `.claude/claude.md` - BAZINGA's own project context (internal use only)

### Action Items

- [ ] Review `config/claude.md` content and decide if it should be genericized
- [ ] Check git history for a deleted generic template that should be restored
- [ ] Verify what content clients should actually receive
- [ ] Update `config/claude.md` to be a proper client template if needed
- [ ] Test `bazinga init` after any changes to ensure clients get correct content

### Git History Search Performed

Searched for:
- `.claude.md` at root level - Not found in git history
- `config/.claude.md` - Not found
- Deleted files with "claude" - Only found `.claude/FILE_SYNC.md` and `.claude/claude.md` (both internal)

**Conclusion:** Either:
1. `config/claude.md` needs to be made generic, OR
2. There was a different file (different name) that should be used

### Reference

- CLI setup code: `src/bazinga_cli/__init__.py` lines 291-422 (`setup_config` method)
- Package config: `pyproject.toml` lines 59-68
