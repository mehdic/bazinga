# Orchestrix Migration Refactor Plan

**Date:** 2025-12-14
**Target:** BAZINGA → Orchestrix (full migration)
**Status:** Planning
**Total References:** 6,881 across 332 files

---

## Executive Summary

This document indexes ALL instances of "bazinga" (any format) and categorizes them for migration. Each entry includes:
- **Category** - What type of reference
- **Migration Priority** - P0 (critical), P1 (high), P2 (medium), P3 (low)
- **Insurance Level** - 3 levels of verification

---

## Three Levels of Insurance

### Level 1: Pre-Migration Validation (Automated)
```bash
# Run before any changes
./scripts/pre-migration-check.sh
```
- [ ] All tests pass (`pytest tests/`)
- [ ] CLI installs correctly (`pip install -e .`)
- [ ] Skills invoke successfully (test each skill)
- [ ] Slash commands work (`/bazinga.orchestrate` test run)
- [ ] Database operations work (CRUD test)

### Level 2: Migration Verification (Per-Category)
After each category of changes:
- [ ] Grep check: `grep -rn "bazinga" <changed_files> | wc -l` should be 0
- [ ] Import check: Python files import from new paths
- [ ] Reference check: All cross-file references updated
- [ ] Test suite passes for affected components

### Level 3: Post-Migration Validation (Full)
```bash
# Run after all changes
./scripts/post-migration-check.sh
```
- [ ] Full test suite passes
- [ ] Integration test completes successfully
- [ ] Clean install works (`pip install orchestrix-cli`)
- [ ] Skills invoke with new names (`orchestrix-db`)
- [ ] Slash commands work (`/orchestrix.orchestrate`)
- [ ] Documentation examples work
- [ ] No "bazinga" references remain (except historical research docs)

---

## File Index by Priority

### P0: Critical Path (Breaks Functionality)

| # | File | Refs | Category | Change Required |
|---|------|------|----------|-----------------|
| 1 | `pyproject.toml` | 15+ | CLI/Package | `name="bazinga-cli"` → `name="orchestrix-cli"` |
| 2 | `pyproject.toml` | - | CLI/Package | `bazinga` script entry → `orchestrix` |
| 3 | `src/bazinga_cli/__init__.py` | 208 | Python Package | Rename entire directory + all internal refs |
| 4 | `.claude/skills/bazinga-db/` | 123+ | Skill Directory | Rename to `orchestrix-db/` |
| 5 | `.claude/skills/bazinga-db/scripts/bazinga_db.py` | 49 | Python Script | Rename file + class `BazingaDB` → `OrchestrixDB` |
| 6 | `.claude/skills/bazinga-validator/` | ~20 | Skill Directory | Rename to `orchestrix-validator/` |
| 7 | `.claude/commands/bazinga.orchestrate.md` | 207 | Slash Command | Rename to `orchestrix.orchestrate.md` |
| 8 | `.claude/commands/bazinga.configure-*.md` | ~50 | Slash Commands | Rename all 4 files |
| 9 | `agents/orchestrator.md` | 207 | Agent Definition | Update all skill invocations |
| 10 | `agents/project_manager.md` | 200 | Agent Definition | Update all skill/path refs |

**Verification (Level 2):**
```bash
# After P0 changes
python -c "from orchestrix_cli import OrchestrixSetup; print('OK')"
python -c "from orchestrix_db import OrchestrixDB; print('OK')"
pytest tests/ -v
```

---

### P1: High Priority (User-Facing)

| # | File | Refs | Category | Change Required |
|---|------|------|----------|-----------------|
| 11 | `README.md` | 66 | Documentation | All CLI examples, installation |
| 12 | `.claude/claude.md` | 129 | Project Context | All path refs, skill names |
| 13 | `config/claude.md` | ~100 | Config Template | Mirror of .claude/claude.md |
| 14 | `docs/QUICK_REFERENCE.md` | ~30 | Documentation | CLI examples |
| 15 | `docs/ADVANCED.md` | ~25 | Documentation | Skill names, configs |
| 16 | `docs/ARCHITECTURE.md` | ~20 | Documentation | System description |
| 17 | `docs/SKILLS.md` | ~15 | Documentation | Skill names |
| 18 | `examples/EXAMPLES.md` | ~20 | Documentation | All example commands |
| 19 | `CONTRIBUTING.md` | ~15 | Documentation | Development workflow |
| 20 | `scripts/init-orchestration.sh` | 63 | Script | Path refs |
| 21 | `scripts/init-orchestration.ps1` | ~50 | Script | Path refs (Windows) |

**Verification (Level 2):**
```bash
# After P1 changes
grep -rn "bazinga" docs/ README.md CONTRIBUTING.md | wc -l  # Should be 0
```

---

### P2: Medium Priority (Internal)

| # | File | Refs | Category | Change Required |
|---|------|------|----------|-----------------|
| 22 | `bazinga/` directory | - | Directory | Rename to `orchestrix/` |
| 23 | `bazinga/templates/*.md` | ~300 | Templates | Path refs inside templates |
| 24 | `bazinga/templates/orchestrator/*.md` | ~100 | Templates | Skill invocations |
| 25 | `.claude/skills/_shared/bazinga_paths.py` | 57 | Shared Module | Rename to `orchestrix_paths.py` |
| 26 | `.claude/skills/*/scripts/*.sh` | ~200 | Skill Scripts | Path refs (`bazinga/`) |
| 27 | `.claude/skills/*/scripts/*.ps1` | ~150 | Skill Scripts | Path refs (Windows) |
| 28 | `.gitignore` | ~15 | Config | `bazinga/` patterns |
| 29 | `tests/test_bazinga_paths.py` | 60 | Test File | Rename + update refs |
| 30 | `tests/test_*.py` | ~30 | Test Files | Import updates |
| 31 | `dashboard/server.py` | ~20 | Dashboard | `BazingaDB` imports |
| 32 | `dashboard-v2/` | ~30 | Dashboard V2 | Path refs |

**Verification (Level 2):**
```bash
# After P2 changes
python -m pytest tests/ -v
ls orchestrix/  # Directory exists
```

---

### P3: Low Priority (Research/Historical)

| # | File Pattern | Refs | Category | Change Required |
|---|--------------|------|----------|-----------------|
| 33 | `research/*.md` | 3000+ | Research Docs | Optional - historical context |
| 34 | `research/project_manager_full_backup.md` | 130 | Backup | Optional |
| 35 | `research/*-ultrathink*.md` | ~500 | Analysis Docs | Optional |
| 36 | `research/*implementation*.md` | ~400 | Implementation Docs | Optional |

**Decision:** Research docs can keep "bazinga" references as historical context. Add header note:
```markdown
> **Note:** This document references the project by its original name "BAZINGA".
> The project was renamed to "Orchestrix" in v3.0.
```

---

## Detailed Change Index

### Category A: Python Package (`src/bazinga_cli/`)

**Files to rename:**
```
src/bazinga_cli/           → src/orchestrix_cli/
src/bazinga_cli/__init__.py → src/orchestrix_cli/__init__.py
src/bazinga_cli/telemetry.py → src/orchestrix_cli/telemetry.py
src/bazinga_cli/security.py → src/orchestrix_cli/security.py
```

**Internal changes in `__init__.py` (208 refs):**

| Line Range | Pattern | Change To |
|------------|---------|-----------|
| 43 | `class BazingaSetup` | `class OrchestrixSetup` |
| 32 | `GITHUB_REPO = "mehdic/bazinga"` | `GITHUB_REPO = "mehdic/orchestrix"` |
| Various | `bazinga/` paths | `orchestrix/` paths |
| Various | `bazinga-cli` | `orchestrix-cli` |
| Various | `"bazinga"` strings | `"orchestrix"` strings |

**Insurance:**
```bash
# Level 1: Before
python -c "from bazinga_cli import BazingaSetup"

# Level 2: After rename
python -c "from orchestrix_cli import OrchestrixSetup"

# Level 3: Full test
pip install -e . && orchestrix --help
```

---

### Category B: Skills (`bazinga-db`, `bazinga-validator`)

**Directory renames:**
```
.claude/skills/bazinga-db/           → .claude/skills/orchestrix-db/
.claude/skills/bazinga-validator/    → .claude/skills/orchestrix-validator/
```

**File renames:**
```
scripts/bazinga_db.py                → scripts/orchestrix_db.py
```

**Class renames:**
```python
# bazinga_db.py:136
class BazingaDB:     → class OrchestrixDB:
```

**SKILL.md updates (123 refs in bazinga-db):**
- `name: bazinga-db` → `name: orchestrix-db`
- All `Skill(command: "bazinga-db")` → `Skill(command: "orchestrix-db")`
- Path references `bazinga/bazinga.db` → `orchestrix/orchestrix.db`

**Files that invoke skills (must update):**
| File | Invocations |
|------|-------------|
| `agents/orchestrator.md` | 50+ |
| `agents/project_manager.md` | 30+ |
| `agents/tech_lead.md` | 10+ |
| `agents/qa_expert.md` | 5+ |
| `agents/investigator.md` | 5+ |
| `bazinga/templates/orchestrator/*.md` | 20+ |

**Insurance:**
```bash
# Level 2: After skill rename
python .claude/skills/orchestrix-db/scripts/orchestrix_db.py --help

# Level 3: Integration
Skill(command: "orchestrix-db")  # Test in Claude Code
```

---

### Category C: Slash Commands

**File renames:**
```
.claude/commands/bazinga.orchestrate.md          → orchestrix.orchestrate.md
.claude/commands/bazinga.orchestrate-advanced.md → orchestrix.orchestrate-advanced.md
.claude/commands/bazinga.orchestrate-from-spec.md → orchestrix.orchestrate-from-spec.md
.claude/commands/bazinga.configure-skills.md     → orchestrix.configure-skills.md
.claude/commands/bazinga.configure-testing.md    → orchestrix.configure-testing.md
```

**Content updates (207 refs in orchestrate.md):**
- All skill invocations
- All path references
- All output examples

**Build script updates:**
```
scripts/build-slash-commands.sh  # Update output filenames
scripts/build-slash-commands.ps1 # Update output filenames
```

**Insurance:**
```bash
# Level 2: After rename
ls .claude/commands/orchestrix.*.md

# Level 3: Functional test
/orchestrix.orchestrate "test task"
```

---

### Category D: Directory Structure (`bazinga/`)

**Directory rename:**
```
bazinga/                    → orchestrix/
bazinga/bazinga.db         → orchestrix/orchestrix.db
bazinga/templates/         → orchestrix/templates/
bazinga/artifacts/         → orchestrix/artifacts/
bazinga/scripts/           → orchestrix/scripts/
```

**Config files:**
```
bazinga/model_selection.json   → orchestrix/model_selection.json
bazinga/challenge_levels.json  → orchestrix/challenge_levels.json
bazinga/skills_config.json     → orchestrix/skills_config.json
```

**Files with path references (2017 refs):**
Every file that references `bazinga/` paths:
- Agent definitions (all)
- Skill scripts (all)
- Templates (all)
- Python code (CLI, tests)
- Documentation (all)

**Insurance:**
```bash
# Level 1: Before
ls bazinga/

# Level 2: After
ls orchestrix/
grep -rn "bazinga/" . | grep -v research/ | wc -l  # Should be 0

# Level 3: Full test
python -c "from pathlib import Path; assert Path('orchestrix').exists()"
```

---

### Category E: Database References

**File renames:**
```
bazinga/bazinga.db → orchestrix/orchestrix.db
```

**Pattern replacements (412 refs):**
| Pattern | Replacement |
|---------|-------------|
| `bazinga.db` | `orchestrix.db` |
| `bazinga_db.py` | `orchestrix_db.py` |
| `BazingaDB` | `OrchestrixDB` |
| `bazinga_db` module | `orchestrix_db` module |

**Files affected:**
- `.claude/skills/bazinga-db/scripts/bazinga_db.py`
- `.claude/skills/bazinga-db/scripts/auto_logger.py`
- `tests/test_concurrent_access.py`
- `tests/test_performance_comparison.py`
- `dashboard/server.py`

**Insurance:**
```bash
# Level 2: After
python -c "from orchestrix_db import OrchestrixDB; db = OrchestrixDB('test.db')"

# Level 3: Full CRUD test
python tests/test_concurrent_access.py
```

---

### Category F: GitHub/Repository References

**Pattern replacements (56 refs):**
| Pattern | Replacement |
|---------|-------------|
| `mehdic/bazinga` | `mehdic/orchestrix` |
| `github.com/mehdic/bazinga` | `github.com/mehdic/orchestrix` |
| `bazinga.git` | `orchestrix.git` |

**Files affected:**
- `pyproject.toml` (URLs)
- `README.md` (installation)
- `CONTRIBUTING.md`
- `src/bazinga_cli/__init__.py` (GITHUB_REPO constant)

**Insurance:**
```bash
# Level 2: After
grep -rn "mehdic/bazinga" . | wc -l  # Should be 0 (except research/)
```

---

### Category G: Class/Function Names (Python)

**Renames required:**

| Current | New | Location |
|---------|-----|----------|
| `class BazingaSetup` | `class OrchestrixSetup` | `src/bazinga_cli/__init__.py:43` |
| `class BazingaDB` | `class OrchestrixDB` | `.claude/skills/bazinga-db/scripts/bazinga_db.py:136` |
| `def copy_bazinga_configs` | `def copy_orchestrix_configs` | `src/bazinga_cli/__init__.py` |
| `BAZINGA_DIR` | `ORCHESTRIX_DIR` | Multiple files |

**Import updates:**
```python
# Before
from bazinga_db import BazingaDB
from bazinga_cli import BazingaSetup

# After
from orchestrix_db import OrchestrixDB
from orchestrix_cli import OrchestrixSetup
```

**Files with imports:**
- `tests/test_concurrent_access.py`
- `tests/test_performance_comparison.py`
- `dashboard/server.py`
- `.claude/skills/bazinga-db/scripts/auto_logger.py`

**Insurance:**
```bash
# Level 2: After
python -c "from orchestrix_db import OrchestrixDB"
python -c "from orchestrix_cli import OrchestrixSetup"

# Level 3: All imports work
pytest tests/ --collect-only  # Imports checked during collection
```

---

## Migration Execution Order

### Phase 1: Foundation (P0 Critical)
```
1.1 Create migration branch
1.2 Run Level 1 pre-migration checks
1.3 Rename Python package: src/bazinga_cli/ → src/orchestrix_cli/
1.4 Update pyproject.toml (package name, entry points)
1.5 Verify: pip install -e . && orchestrix --help
```

### Phase 2: Skills (P0 Critical)
```
2.1 Rename skill directories
2.2 Rename Python scripts
2.3 Update class names (BazingaDB → OrchestrixDB)
2.4 Update all SKILL.md files
2.5 Verify: Each skill invokes correctly
```

### Phase 3: Commands (P0 Critical)
```
3.1 Rename slash command files
3.2 Update content (skill invocations, paths)
3.3 Update build scripts
3.4 Verify: /orchestrix.orchestrate works
```

### Phase 4: Agents (P0 Critical)
```
4.1 Update orchestrator.md (all skill invocations)
4.2 Update project_manager.md
4.3 Update other agents (tech_lead, qa_expert, etc.)
4.4 Verify: Integration test passes
```

### Phase 5: Directory Structure (P2 Medium)
```
5.1 Rename bazinga/ → orchestrix/
5.2 Update all path references
5.3 Update .gitignore
5.4 Verify: All paths resolve correctly
```

### Phase 6: Documentation (P1 High)
```
6.1 Update README.md
6.2 Update docs/*.md
6.3 Update examples/
6.4 Update CONTRIBUTING.md
6.5 Verify: All examples work
```

### Phase 7: Tests & Dashboard (P2 Medium)
```
7.1 Rename test files
7.2 Update test imports
7.3 Update dashboard code
7.4 Verify: Full test suite passes
```

### Phase 8: Final Validation (Level 3)
```
8.1 Run post-migration-check.sh
8.2 Clean install test
8.3 Integration test
8.4 Grep audit (no remaining refs except research/)
8.5 Create PR
```

---

## Rollback Plan

If migration fails at any phase:

```bash
# Restore from git
git checkout main -- .

# Or restore specific files
git checkout HEAD~1 -- src/bazinga_cli/
```

**Checkpoints:**
- After Phase 1: Tag `migration-phase1`
- After Phase 4: Tag `migration-phase4-critical-complete`
- After Phase 8: Tag `v3.0.0-orchestrix`

---

## Grep Audit Commands

**Pre-migration baseline:**
```bash
grep -rn -i "bazinga" --include="*.py" --include="*.md" --include="*.sh" . | wc -l
# Expected: 6881
```

**Post-migration (excluding research/):**
```bash
grep -rn -i "bazinga" --include="*.py" --include="*.md" --include="*.sh" . | grep -v "research/" | wc -l
# Expected: 0 (or very low, only historical notes)
```

**Specific checks:**
```bash
# No bazinga in Python
grep -rn "bazinga" --include="*.py" src/ .claude/skills/ tests/ | grep -v research/

# No bazinga in active docs
grep -rn "bazinga" README.md docs/ CONTRIBUTING.md

# No bazinga in agents
grep -rn "bazinga" agents/

# No bazinga paths
grep -rn "bazinga/" --include="*.py" --include="*.md" --include="*.sh" . | grep -v research/
```

---

## Summary Statistics

| Category | Files | References | Priority |
|----------|-------|------------|----------|
| Python Package | 5 | 250+ | P0 |
| Skills | 10+ | 300+ | P0 |
| Slash Commands | 5 | 250+ | P0 |
| Agents | 7 | 500+ | P0 |
| Directory/Paths | 100+ | 2000+ | P2 |
| Documentation | 20+ | 300+ | P1 |
| Tests | 5+ | 100+ | P2 |
| Research (keep) | 150+ | 3000+ | P3 (optional) |
| **TOTAL** | **332** | **6881** | - |

---

## Next Steps

1. **Review this plan** - Validate categorization and priorities
2. **Create migration scripts** - Automate repetitive changes
3. **Set up CI checks** - Automated verification at each phase
4. **Execute Phase 1** - Start with Python package rename
5. **Iterate** - Complete each phase with verification

---

## References

- `research/project-naming-analysis.md` - Naming decision rationale
- OpenAI GPT-5 review (2025-12-14) - Collision analysis
- Integration test spec: `tests/integration/simple-calculator-spec.md`
