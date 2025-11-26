# Senior Agent Inheritance Strategy: ULTRATHINK Analysis

**Date:** 2025-11-26
**Context:** Senior Software Engineer agent must handle everything Developer does, plus escalation-specific capabilities
**Decision:** Build script approach with shared base + tier deltas
**Status:** Proposed

---

## Problem Statement

**Current State:**
- Developer agent: 1,618 lines (comprehensive)
- Senior agent: 367 lines (escalation-focused only)

**Gap:** When a task escalates to Senior, the Senior agent is MISSING:
- Spec-Kit integration (~390 lines)
- Project context awareness (~170 lines)
- Tech debt logging (~80 lines)
- Testing mode awareness (disabled/minimal/full)
- Validation gate rules (no estimates allowed)
- Conditional routing logic
- Branch setup instructions
- Detailed coding standards
- Test-passing integrity rules

**Impact:** Senior can't properly continue escalated tasks that involve spec-kit, tech debt, or testing mode awareness.

---

## Requirements

### Must Have
1. Senior MUST have ALL capabilities of Developer
2. Senior MUST have ADDITIONAL escalation-specific sections
3. Senior MUST have MODIFIED sections (mandatory skills, higher standards)
4. Changes to shared content MUST propagate to both agents automatically

### Nice to Have
1. Minimal duplication (DRY principle)
2. Clear separation of concerns
3. Easy to understand structure
4. Follows existing project patterns

---

## Options Analysis

### Option 1: Manual Copy + Extend

**Approach:** Copy all Developer content to Senior, add Senior-specific sections.

```
agents/
├── developer.md                    # 1,618 lines (unchanged)
└── senior_software_engineer.md     # ~2,000 lines (Developer + Senior)
```

| Aspect | Rating | Notes |
|--------|--------|-------|
| Implementation effort | ⭐⭐⭐⭐⭐ | Trivial - just copy/paste |
| Maintenance burden | ⭐ | 2x work for every shared change |
| Risk of drift | ⭐ | Files WILL diverge over time |
| DRY compliance | ⭐ | Massive duplication |
| Follows project patterns | ⭐⭐⭐ | No build step needed |

**Verdict:** ❌ Quick fix, long-term nightmare. Files will drift.

---

### Option 2: Prompt Engineering ("Follow Developer Rules")

**Approach:** Add instruction to Senior: "First, follow all rules in Developer agent, then apply these additional rules..."

```markdown
# Senior Software Engineer Agent

## Base Rules
**CRITICAL:** Follow ALL rules from the Developer agent (agents/developer.md), including:
- Spec-Kit integration
- Project context awareness
- Tech debt logging
- Testing mode awareness
- All workflow and reporting rules

## Additional Senior-Specific Rules
[Senior-specific content here]
```

| Aspect | Rating | Notes |
|--------|--------|-------|
| Implementation effort | ⭐⭐⭐⭐⭐ | Just add instruction |
| Maintenance burden | ⭐⭐⭐⭐ | Single source for base |
| Risk of drift | ⭐⭐⭐ | Depends on model following instructions |
| DRY compliance | ⭐⭐⭐⭐ | No duplication |
| Follows project patterns | ⭐⭐ | Relies on model inference |

**Verdict:** ⚠️ Risky. Model might not reliably follow cross-file references.

---

### Option 3: Build Script (Like Orchestrator)

**Approach:** Use build script pattern already established for orchestrator. Create shared base + tier-specific deltas.

```
agents/
├── _sources/
│   ├── _shared/
│   │   ├── 00-frontmatter.md      # Template with {{MODEL}} placeholder
│   │   ├── 10-role.md             # Role definition
│   │   ├── 20-workflow-position.md
│   │   ├── 30-spec-kit.md
│   │   ├── 40-context-awareness.md
│   │   ├── 50-quality-tools.md
│   │   ├── 60-workflow-steps.md
│   │   ├── 70-validation-rules.md
│   │   ├── 80-tech-debt.md
│   │   ├── 90-reporting.md
│   │   ├── 91-routing.md
│   │   └── 99-standards.md
│   ├── developer/
│   │   ├── tier-scope.md          # Haiku tier scope
│   │   └── escalation-awareness.md # How to escalate
│   └── senior/
│       ├── tier-identity.md       # Senior identity
│       ├── when-spawned.md        # Spawn conditions
│       ├── failure-analysis.md    # Root cause analysis
│       ├── challenge-levels.md    # Level 3-5 patterns
│       └── escalation-report.md   # Senior report format
├── developer.md                   # GENERATED
└── senior_software_engineer.md    # GENERATED
```

| Aspect | Rating | Notes |
|--------|--------|-------|
| Implementation effort | ⭐⭐ | Significant restructuring |
| Maintenance burden | ⭐⭐⭐⭐⭐ | Single source of truth |
| Risk of drift | ⭐⭐⭐⭐⭐ | Impossible to drift |
| DRY compliance | ⭐⭐⭐⭐⭐ | Zero duplication |
| Follows project patterns | ⭐⭐⭐⭐⭐ | Matches orchestrator pattern |

**Verdict:** ✅ Best long-term solution. Matches existing patterns.

---

### Option 4: Single Unified Agent with Tier Awareness

**Approach:** One agent file that handles both tiers with conditional logic.

```markdown
# Implementation Specialist Agent

## Your Tier
{IF model == "haiku"}
You are a DEVELOPER on Haiku tier...
{ELSE IF model == "sonnet"}
You are a SENIOR SOFTWARE ENGINEER on Sonnet tier...
{ENDIF}

## Shared Workflow
[All shared content]

{IF model == "sonnet"}
## Senior-Specific: Failure Analysis
[Senior-only content]
{ENDIF}
```

| Aspect | Rating | Notes |
|--------|--------|-------|
| Implementation effort | ⭐⭐⭐ | Moderate restructuring |
| Maintenance burden | ⭐⭐⭐⭐ | Single file |
| Risk of drift | ⭐⭐⭐⭐⭐ | Single file can't drift |
| DRY compliance | ⭐⭐⭐⭐⭐ | Zero duplication |
| Follows project patterns | ⭐⭐ | New pattern, conditional logic complex |

**Verdict:** ⚠️ Possible but conditional logic makes file hard to read.

---

### Option 5: Simpler Build Script (Two Source Files)

**Approach:** Simpler than Option 3. Just two source files + merge script.

```
agents/
├── _sources/
│   ├── developer.base.md          # Complete developer (source of truth)
│   └── senior.delta.md            # ONLY what's different for senior
├── developer.md                   # Copy of developer.base.md
└── senior_software_engineer.md    # Merged: base + delta
```

**Build Logic:**
```bash
# developer.md = developer.base.md (direct copy)
# senior.md = developer.base.md + senior.delta.md (merged)
```

**Delta contains:**
1. **REPLACE** sections (frontmatter, role, scope → senior equivalents)
2. **ADD** sections (failure analysis, challenge levels)
3. **MODIFY** sections (skills: optional → mandatory)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Implementation effort | ⭐⭐⭐ | Moderate |
| Maintenance burden | ⭐⭐⭐⭐⭐ | Edit base → both update |
| Risk of drift | ⭐⭐⭐⭐⭐ | Build script ensures sync |
| DRY compliance | ⭐⭐⭐⭐⭐ | Delta only has differences |
| Follows project patterns | ⭐⭐⭐⭐⭐ | Matches orchestrator pattern |
| Complexity | ⭐⭐⭐⭐ | Simpler than Option 3 |

**Verdict:** ✅ RECOMMENDED. Best balance of simplicity and maintainability.

---

## Recommendation: Option 5 (Simpler Build Script)

### Why This Approach

1. **Proven Pattern:** We already use build scripts for orchestrator
2. **Single Source of Truth:** Developer base is THE source
3. **Clear Delta:** Senior differences are explicit and auditable
4. **Pre-commit Hook:** Already have infrastructure for auto-rebuild
5. **Minimal Restructuring:** Just reorganize, don't rewrite

### Implementation Plan

#### Phase 1: Restructure Files

```bash
# Create source directory
mkdir -p agents/_sources

# Move developer to base (it's already comprehensive)
mv agents/developer.md agents/_sources/developer.base.md

# Create senior delta from current senior
# (Extract ONLY the senior-specific parts)
# agents/_sources/senior.delta.md
```

#### Phase 2: Create Delta File Format

```markdown
# Senior Software Engineer Delta
# This file contains ONLY what differs from developer.base.md

## REPLACE: Frontmatter
---
name: senior_software_engineer
description: Senior implementation specialist handling escalated complexity
model: sonnet
---

## REPLACE: Role Section
[Senior role description]

## REMOVE: Scope Definition
# Remove "Your Scope (Haiku Tier)" section

## REMOVE: Escalation Awareness
# Remove "When You Should Report ESCALATE_SENIOR" (IS the senior)

## ADD_AFTER: Role Section
[When You're Spawned section]
[Context You Receive section]

## ADD_AFTER: Workflow Position
[Failure Analysis section]
[Root Cause Categories section]

## ADD_BEFORE: Remember Section
[Challenge Level Response section]

## MODIFY: Skills Section
# Change codebase-analysis: optional → MANDATORY
# Change test-pattern-analysis: optional → MANDATORY

## MODIFY: Report Format
# Add Escalation Context fields
```

#### Phase 3: Build Script

```bash
#!/bin/bash
# scripts/build-agent-files.sh

set -e

SOURCES="agents/_sources"
OUTPUT="agents"

# Developer = direct copy of base
cp "$SOURCES/developer.base.md" "$OUTPUT/developer.md"
echo "✓ Generated developer.md"

# Senior = base + delta merge
python3 scripts/merge_agent_delta.py \
    "$SOURCES/developer.base.md" \
    "$SOURCES/senior.delta.md" \
    "$OUTPUT/senior_software_engineer.md"
echo "✓ Generated senior_software_engineer.md"
```

#### Phase 4: Python Merge Script

```python
# scripts/merge_agent_delta.py
"""
Merge developer base with senior delta to produce senior agent.

Delta commands:
- ## REPLACE: <section>  - Replace entire section
- ## REMOVE: <section>   - Remove section
- ## ADD_AFTER: <section> - Insert after section
- ## ADD_BEFORE: <section> - Insert before section
- ## MODIFY: <section>   - Apply modifications
"""
```

#### Phase 5: Update Pre-commit Hook

```bash
# Add to .git/hooks/pre-commit
if git diff --cached --name-only | grep -q "agents/_sources/"; then
    echo "🔄 Agent sources changed, rebuilding..."
    ./scripts/build-agent-files.sh
    git add agents/developer.md agents/senior_software_engineer.md
fi
```

---

## Delta Content Specification

### Sections to REPLACE in Senior

| Section | Developer | Senior |
|---------|-----------|--------|
| Frontmatter | model: haiku | model: sonnet |
| Role | "DEVELOPER AGENT" | "SENIOR SOFTWARE ENGINEER AGENT" |
| Description | "implementation specialist" | "escalation specialist handling complex..." |

### Sections to REMOVE in Senior

| Section | Reason |
|---------|--------|
| "Your Scope (Haiku Tier)" | Senior has no tier scope limits |
| "Escalation Awareness" | Senior IS the escalation |
| "When You Should Report ESCALATE_SENIOR" | Can't escalate to self |
| "When You Should Report INCOMPLETE" | Senior completes or BLOCKS |

### Sections to ADD in Senior

| Section | Content |
|---------|---------|
| "When You're Spawned" | 3 spawn conditions |
| "Context You Receive" | What's passed from developer |
| "Analyze the Failure First" | Failure analysis approach |
| "Root Cause Categories" | 5 common patterns table |
| "Challenge Level Response" | Level 3-5 fix patterns |
| "Pre-Implementation Checklist" | Senior-specific checklist |

### Sections to MODIFY in Senior

| Section | Change |
|---------|--------|
| Skills | codebase-analysis: optional → MANDATORY |
| Skills | test-pattern-analysis: optional → MANDATORY |
| Report format | Add "Escalation Context" fields |
| Report format | Add "Root Cause Analysis" field |
| Remember | Different 5 items vs Developer's 7 |

---

## Comparison: Before vs After

### Before (Current State)

```
Developer: 1,618 lines (comprehensive)
Senior: 367 lines (missing critical sections)

When escalated:
- Senior doesn't know about Spec-Kit ❌
- Senior doesn't know about Tech Debt ❌
- Senior doesn't know testing modes ❌
```

### After (Proposed State)

```
developer.base.md: ~1,618 lines (source of truth)
senior.delta.md: ~300 lines (differences only)

Generated:
- developer.md: ~1,618 lines (copy of base)
- senior.md: ~1,800 lines (base + delta)

When escalated:
- Senior knows EVERYTHING Developer knows ✅
- Senior has ADDITIONAL escalation expertise ✅
- Single source of truth prevents drift ✅
```

---

## Risk Analysis

### Risks of NOT Implementing

| Risk | Impact | Likelihood |
|------|--------|------------|
| Senior fails spec-kit tasks | High | High (any spec-kit escalation) |
| Senior doesn't log tech debt | Medium | High (root causes reveal debt) |
| Senior uses wrong testing mode | Medium | Medium (mode-specific routing) |
| Files drift over time | High | Certain (manual sync impossible) |

### Risks of Implementation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Build script bugs | Medium | Comprehensive tests |
| Complex merge logic | Medium | Keep delta format simple |
| Learning curve | Low | Document thoroughly |

---

## Implementation Estimate

| Phase | Effort |
|-------|--------|
| Restructure files | 30 mins |
| Create delta file | 1 hour |
| Build script | 1 hour |
| Merge script | 2 hours |
| Update pre-commit | 15 mins |
| Testing | 1 hour |
| Documentation | 30 mins |
| **Total** | **~6 hours** |

---

## Decision

**Recommended Approach:** Option 5 (Simpler Build Script)

**Rationale:**
1. Matches existing orchestrator pattern
2. Single source of truth eliminates drift
3. Delta file makes differences explicit
4. Pre-commit hook automates rebuilds
5. Reasonable implementation effort

**Next Steps:**
1. Create `agents/_sources/` directory structure
2. Move developer.md to developer.base.md
3. Create senior.delta.md with differences
4. Implement build and merge scripts
5. Update pre-commit hook
6. Test generation
7. Update CONTRIBUTING.md

---

## Alternative: Quick Win First

If 6 hours is too much for now, we can do a **quick win** first:

**Quick Win (30 mins):**
1. Manually copy all missing sections from Developer to Senior
2. Accept temporary duplication
3. Add TODO comment for build script implementation

**Then later:**
- Implement proper build script
- Remove duplication

This gives Senior full capabilities NOW while we build the proper solution.

---

## Lessons Learned

1. **Tier escalation requires capability inheritance** - Higher tiers should have superset of lower tier capabilities
2. **Build scripts prevent drift** - Manual sync always fails eventually
3. **Delta approach is cleaner** - Explicit differences are easier to audit than full duplication
4. **Project patterns matter** - Following existing patterns (orchestrator build) reduces cognitive load

---

## References

- `/home/user/bazinga/agents/developer.md` - Current developer agent
- `/home/user/bazinga/agents/senior_software_engineer.md` - Current senior agent
- `/home/user/bazinga/scripts/build-slash-commands.sh` - Existing build pattern
- `/home/user/bazinga/research/developer-vs-senior-engineer-agent-comparison.md` - Detailed comparison
