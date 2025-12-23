# Coordination → Bazinga Folder Migration Research

**Date:** 2025-11-17
**Issue:** coordination/ folder should be bazinga/ in client projects
**Root Cause:** Templates are referenced in coordination/ but should be in bazinga/

---

## 🔍 Research Findings

### Current State

**coordination/ folder contains:**
```
coordination/
├── skills_config.json
└── templates/
    ├── completion_report.md
    ├── logging_pattern.md
    ├── message_templates.md
    └── prompt_building.md
```

**bazinga/ folder contains:**
```
bazinga/
└── skills_config.json
```

**Problem:** Templates are missing from bazinga/ but referenced by orchestrator and agents!

---

## 📋 All Files Referencing coordination/

### Critical Files (Need Updates)

#### 1. agents/orchestrator.md
- Line 37: `coordination/templates/message_templates.md`
- Line 62: `coordination/templates/message_templates.md`

#### 2. .claude/commands/bazinga.orchestrate.md (Auto-generated)
- Line 38: `coordination/templates/message_templates.md`
- Line 63: `coordination/templates/message_templates.md`

#### 3. .gitignore
- Line 78: `!coordination/templates/` (whitelist)

**→ These 3 files need coordination/ → bazinga/ changes**

---

### Documentation Files (Reference Only - Update for Consistency)

#### 4. orchestrator_size_reduction_strategy.md
- Multiple references to `coordination/templates/` in proposed extraction plans
- Should reference `templates/` for future consistency

#### 5. coordination_vs_bazinga_analysis.md
- Analysis document explaining the difference
- Should be updated to reflect new reality

#### 6. copilot_review_analysis.md
- References to coordination/templates/ in review notes
- Historical document - can be updated or left as-is

#### 7. critical_gap_analysis.md
- Line 302: Reference to coordination/templates/
- Historical document - can be updated or left as-is

#### 8. validation_report_output_improvements.md
- Line 26: Reference to coordination/templates/
- Historical document - can be updated or left as-is

#### 9. dashboard/js/workflow-viz.js
- Need to check what this references

---

## 🔧 Required Changes

### Phase 1: CLI Installation Logic

**File:** `src/bazinga_cli/__init__.py`

**Current:** Does NOT copy coordination/ folder

**Required:** Add method to copy templates to templates/

```python
def copy_templates(self, target_dir: Path) -> bool:
    """Copy coordination templates to bazinga/templates directory."""
    templates_dir = target_dir / "bazinga" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    source_templates = self.source_dir / "coordination" / "templates"
    if not source_templates.exists():
        return False

    for template_file in source_templates.glob("*.md"):
        shutil.copy2(template_file, templates_dir / template_file.name)
        console.print(f"  ✓ Copied {template_file.name}")

    return True
```

**Call from init() and update():**
- Add to init() after step 6 (dashboard)
- Add to update() after step 6 (dashboard)

---

### Phase 2: Update pyproject.toml

**Current:**
```toml
[tool.hatch.build.targets.wheel.shared-data]
"agents" = "share/bazinga_cli/agents"
"scripts" = "share/bazinga_cli/scripts"
# ... (no coordination/)
```

**Option A: Copy coordination/ folder as-is**
```toml
"coordination" = "share/bazinga_cli/coordination"
```

**Option B: Copy templates directly to bazinga/**
```toml
"coordination/templates" = "share/bazinga_cli/bazinga/templates"
```

**Recommendation:** Option B - Avoids having both coordination/ and bazinga/ in distribution

---

### Phase 3: Update Agent References

**Files to update:**
1. `agents/orchestrator.md` (lines 37, 62)
2. Rebuild `.claude/commands/bazinga.orchestrate.md` (auto-generated)

**Change:**
```markdown
# Before
coordination/templates/message_templates.md

# After
templates/message_templates.md
```

---

### Phase 4: Update .gitignore

**Current:**
```gitignore
coordination/
!coordination/templates/
```

**After:**
```gitignore
coordination/
templates/  # Ignore templates (copied from coordination/)
!coordination/templates/  # Keep coordination/templates in repo
```

**Rationale:**
- Keep coordination/templates/ in repo (source of truth)
- Ignore templates/ (copied during init)
- Both bazinga/skills_config.json and templates/ will exist

---

### Phase 5: Init Script Updates

**File:** `scripts/init-orchestration.sh`

**Add after database initialization:**
```bash
# Copy templates to bazinga folder if not present
if [ ! -d "bazinga/templates" ]; then
    if [ -d "coordination/templates" ]; then
        echo "📝 Copying templates to bazinga/templates..."
        cp -r coordination/templates bazinga/templates
        echo "✅ Templates copied"
    fi
fi
```

---

### Phase 6: Update Documentation

**Files:**
1. orchestrator_size_reduction_strategy.md - Update all `coordination/templates/` → `templates/`
2. coordination_vs_bazinga_analysis.md - Update to reflect new structure
3. copilot_review_analysis.md - Optional (historical)
4. critical_gap_analysis.md - Optional (historical)
5. validation_report_output_improvements.md - Optional (historical)

---

## 🎯 Implementation Order

### Step 1: Move templates physically (in repo)
```bash
# Create bazinga/templates in repo
mkdir -p bazinga/templates
cp coordination/templates/*.md templates/
```

### Step 2: Update references
- agents/orchestrator.md
- .gitignore

### Step 3: Rebuild slash command
```bash
./scripts/build-slash-commands.sh
```

### Step 4: Update CLI
- Add copy_templates() method
- Call in init() and update()
- Update pyproject.toml

### Step 5: Update init script
- Add template copy logic

### Step 6: Update documentation
- orchestrator_size_reduction_strategy.md
- coordination_vs_bazinga_analysis.md

### Step 7: Test
- Run init in test directory
- Verify templates/ exists
- Verify orchestrator references work

---

## 📊 Impact Analysis

**Files Modified:** ~12 files
**Risk:** Low-Medium
**Breaking Change:** Yes (for existing installations)

**Migration Path for Existing Users:**
```bash
# After updating bazinga CLI
cd your-project
bazinga update  # Will copy templates to templates/
```

---

## ✅ Validation Checklist

After changes:
- [ ] templates/ folder exists in repo
- [ ] coordination/templates/ still exists (source of truth)
- [ ] agents/orchestrator.md references templates/
- [ ] .claude/commands/bazinga.orchestrate.md references templates/
- [ ] CLI copies templates during init
- [ ] CLI copies templates during update
- [ ] Init script copies templates
- [ ] .gitignore updated
- [ ] Documentation updated
- [ ] Test installation works

---

**Status:** Ready for implementation
