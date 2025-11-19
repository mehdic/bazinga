# Project Context Storage: DB-First Architecture

**Date**: 2025-11-19
**Status**: Approved for Implementation
**Principle**: Clear rules, no vague decisions

---

## Problem with Current Implementation

**Architectural Inconsistency:**
- Sessions → bazinga-db ✅
- Logs → bazinga-db ✅
- Task groups → bazinga-db ✅
- State → bazinga-db ✅
- **Project context → Files only** ❌

**File Location Error:**
- Template at `.claude/templates/project_context.template.json` (gitignored, won't commit)
- No version control for template
- No history tracking for context evolution

---

## Solution: DB-First with File Cache

### Architecture

```
PM generates context
    ↓
1. Save to DB (primary, with history)
    ↓
2. Write to file (cache for fast reads)
    ↓
Developer reads from file (always exists, always current)
OR
PM/Tech Lead/Investigator query DB (historical analysis)
```

### Clear Rules (No Ambiguity)

**RULE 1: Developers ALWAYS read file, NEVER query DB**
```python
# Developer agent: agents/developer.md
context = read("bazinga/project_context.json")
# NEVER: bazinga-db query (they work on current session only)
```

**RULE 2: PM/Tech Lead/Investigator query DB for historical analysis**
```python
# PM analyzing evolution
bazinga-db, get project_context for last 5 sessions

# Tech Lead comparing patterns
bazinga-db, get project_context where task_type = "auth"

# Investigator debugging regression
bazinga-db, get project_context for session X vs Y
```

**RULE 3: PM writes BOTH at generation time**
```markdown
PM Phase 4.5:
1. Generate context
2. Save to DB (primary): state_type=project_context
3. Write to file (cache): bazinga/project_context.json
```

**RULE 4: Template is version-controlled**
```
.claude/templates/project_context.template.json (committed)
↓
Orchestrator copies to bazinga/ at session start (if missing)
↓
PM overwrites with real context
```

### Decision Matrix

| Agent | Current Context | Historical Context |
|-------|----------------|-------------------|
| Developer | File ✅ | Never ❌ |
| PM | File ✅ | DB ✅ |
| Tech Lead | File ✅ | DB ✅ |
| QA | File ✅ | Never ❌ |
| Investigator | File ✅ | DB ✅ |

### File Locations

| File | Location | Purpose | Committed? |
|------|----------|---------|------------|
| Template | `.claude/templates/project_context.template.json` | Default | ✅ Yes |
| Current | `bazinga/project_context.json` | Cache | ❌ No |
| History | `bazinga.db` (state table) | Primary | ❌ No |

---

## Implementation Changes

### 1. Template Location (5 min)

**Move:**
```bash
mkdir -p .claude/templates
git mv -f .claude/templates/project_context.template.json .claude/templates/
```

**Update references:**
- agents/developer.md: Change path reference

---

### 2. Orchestrator Initialization (agents/orchestrator.md)

**Add to Phase 1 (after session creation):**

```markdown
### Step 1.2: Ensure Project Context Template

Before spawning PM, ensure fallback context exists:

```bash
if [ ! -f "bazinga/project_context.json" ]; then
    cp .claude/templates/project_context.template.json bazinga/project_context.json
fi
```

PM will overwrite with real context. If PM fails, template provides fallback.
```

**Location:** After Step 1.1 (Create session), before Step 1.3 (Spawn PM)
**Lines added:** ~6 (compact)

---

### 3. PM Context Generation (agents/project_manager.md)

**Update Phase 4.5 "Save Context" section:**

```markdown
**Save Context (DB + File):**

1. **Primary: Save to Database**
```
bazinga-db, save state
  session_id: {current_session_id}
  state_type: project_context
  state_data: {context_json}
```

2. **Cache: Write to File**
Write to `bazinga/project_context.json` (overwrites template if present)

**Purpose:**
- DB: Historical analysis (PM/Tech Lead/Investigator)
- File: Fast reads (current session developers)
```

**Location:** Replace existing "Save Context" section
**Lines added:** ~8 (compact, clear)

---

### 4. Developer Documentation (agents/developer.md)

**Update Step 1:**

```markdown
**Step 1: Read Project Context**

```bash
context = read("bazinga/project_context.json")
```

**Rules:**
- ALWAYS read from file (current session)
- NEVER query bazinga-db (historical analysis is for PM/Tech Lead/Investigator)
- If "template": true → PM hasn't generated yet, may invoke codebase-analysis for task-specific context
```

**Location:** Replace existing Step 1 context reading
**Lines added:** ~5 (compact, clear rules)

---

### 5. Fix Test 3 (research/tests/test-analyzer-performance.sh)

**Change Test 3 task:**

```bash
# OLD (no matches in codebase)
--task "implement OAuth2 authentication with Google and GitHub providers"

# NEW (should find agent patterns)
--task "add new agent for code review and quality assurance"
```

**Expected results:** Should find similar agent structures + quality skills

---

### 6. Update claude.md

**Add to "Key Principles" section:**

```markdown
### Agent File Size Constraints

Agent files are approaching maximum context limits. When modifying agent files:

**Requirements:**
- ✅ Surgical: Precise, targeted changes only
- ✅ Compact: Minimal lines without ambiguity
- ✅ Clear: No vague paths or "when needed" logic
- ❌ Avoid: Verbose examples, redundant explanations
- ❌ Avoid: Multiple ways to do the same thing

**Decision rules must be explicit:**
- Good: "Developer reads file, PM queries DB"
- Bad: "Read file or query DB when needed"

**Each addition must justify its lines:**
- Can this be clearer in fewer words?
- Does this remove ambiguity or add it?
- Is this the ONLY way to interpret this?
```

---

## Validation Checklist

After implementation:

**Files:**
- [ ] Template at `.claude/templates/project_context.template.json` (committed)
- [ ] Template NOT in `bazinga/` directory
- [ ] Orchestrator copies template at session start
- [ ] PM saves to DB then file
- [ ] Developer reads file only

**Tests:**
- [ ] Test 3 uses task with actual matches
- [ ] Test 3 passes (finds similar features)

**Documentation:**
- [ ] Agent files updated with clear rules
- [ ] No "when needed" or vague conditions
- [ ] Decision matrix clear (who reads what, when)

**Agent Size:**
- [ ] Orchestrator addition <10 lines
- [ ] PM addition <10 lines
- [ ] Developer addition <8 lines
- [ ] Total addition <30 lines across all agents

---

## Benefits

1. **Consistency:** All state in DB (like everything else)
2. **History:** Track context evolution across sessions
3. **Performance:** File cache for fast developer reads
4. **Clear rules:** No ambiguity about who reads what
5. **Version control:** Template committed, evolvable
6. **Compact:** Minimal line additions to agents

---

**Status:** Ready for surgical implementation
