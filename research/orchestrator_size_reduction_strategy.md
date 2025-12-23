# Orchestrator Size Reduction Strategy

**Date:** 2025-11-17
**Current Status:** orchestrator.md is 3,765 lines (111KB) - approaching size limits
**Goal:** Reduce file size by 30-40% while preserving all functionality

---

## 📊 Current Size Analysis

### Overall Metrics
- **Total Lines:** 3,765
- **Total Characters:** 111,410 (111KB)
- **Total Words:** 14,508
- **Code Blocks:** 375 (lots of examples)

### Largest Sections (Top 10)
| Lines | Section |
|-------|---------|
| 1,239 | Phase 2A: Simple Mode Execution |
| 464 | Phase 2B: Parallel Mode Execution |
| 406 | Agent Response Parsing |
| 329 | Initialization |
| 313 | Phase 1: Spawn Project Manager |
| 182 | Shutdown Protocol |
| 125 | State Management Reference |
| 65 | Role Drift Prevention |
| 63 | Overview |
| 53 | Database Operations |

### Repetitive Patterns
- **Database logging patterns:** 153 occurrences
- **Capsule format examples:** 465 code blocks
- **Skill() invocations:** 61 examples
- **MANDATORY/CRITICAL warnings:** 71 instances
- **Parse/Output/Log blocks:** ~56 similar instruction sequences

---

## 🎯 Extraction Opportunities (High Impact)

### 1. Developer Prompt Building - 1,155 lines ⭐⭐⭐
**Current Location:** Phase 2A, lines 1478-2633
**What It Contains:**
- Step-by-step prompt construction instructions
- Skills configuration integration
- Mandatory/optional skill sections
- Testing framework integration
- Workflow templates
- Report format specifications

**Extraction Strategy:**
```
Create: templates/developer_prompt_template.md

Content:
- Base developer prompt structure
- Skills configuration parser instructions
- Dynamic section builders (mandatory/optional skills)
- Testing framework integration pattern
- Workflow steps template
- Report format

Orchestrator Reference:
"Build developer prompt following templates/developer_prompt_template.md"
```

**Reduction:** ~1,100 lines (29% of total file)

---

### 2. Agent Response Parsing - 406 lines ⭐⭐
**Current Location:** Lines 80-486
**What It Contains:**
- Developer response parsing (82 lines)
- QA response parsing (83 lines)
- Tech Lead response parsing (101 lines)
- PM response parsing (106 lines)
- Investigator response parsing (31 lines)
- Best practices (53 lines)

**Extraction Strategy:**
```
Create: templates/agent_response_parsing.md

Content:
- All 5 agent parsing sections
- Pattern matching strategies
- Fallback logic
- Best practices
- Capsule construction templates

Orchestrator Reference:
"Parse agent responses using templates/agent_response_parsing.md strategies"
```

**Reduction:** ~400 lines (11% of total file)

---

### 3. Tech Lead Prompt Building - 176 lines ⭐
**Current Location:** Phase 2A/2B Tech Lead spawn sections
**What It Contains:**
- Tech Lead role definition
- Security/lint/coverage skill integration
- Review criteria
- Decision tree logic
- Report format

**Extraction Strategy:**
```
Create: templates/techlead_prompt_template.md

Content:
- Base tech lead prompt
- Skill integration patterns
- Review criteria checklist
- Decision tree (approve/changes/escalate/investigate)
- Report format

Orchestrator Reference:
"Build Tech Lead prompt following templates/techlead_prompt_template.md"
```

**Reduction:** ~170 lines (5% of total file)

---

### 4. QA Expert Prompt Building - ~150 lines ⭐
**Current Location:** Phase 2A/2B QA spawn sections
**What It Contains:**
- QA role definition
- Testing types (unit/integration/contract/E2E)
- Coverage requirements
- Failure analysis patterns
- Report format

**Extraction Strategy:**
```
Create: templates/qa_prompt_template.md

Content:
- Base QA prompt structure
- Testing requirements per mode
- Coverage thresholds
- Failure categorization
- Report format with artifact instructions

Orchestrator Reference:
"Build QA prompt following templates/qa_prompt_template.md"
```

**Reduction:** ~150 lines (4% of total file)

---

## 🔧 Compaction Opportunities (Medium Impact)

### 5. Consolidate Repeated Agent Spawn Pattern - ~200 lines ⭐⭐
**Current Duplication:**
Every agent spawn follows same pattern:
1. Output capsule to user
2. Build prompt from template
3. Spawn with Task tool
4. Parse response
5. Construct output capsule
6. Log to database
7. Route to next phase

**Compaction Strategy:**
```markdown
## Generic Agent Spawn Pattern

### For ANY agent spawn, follow this sequence:

1. **Output capsule:** Use template from templates/message_templates.md
2. **Build prompt:** Use templates/{agent}_prompt_template.md
3. **Spawn agent:** Task(subagent_type: "{agent}", prompt: "{built_prompt}")
4. **Parse response:** Use templates/agent_response_parsing.md
5. **Construct capsule:** Based on parsed data + templates
6. **Log interaction:** bazinga-db log-agent-interaction (status, summary, artifacts)
7. **Route:** Continue to next workflow phase

Then for each agent, just specify:
- Agent type (developer/qa/techlead/pm/investigator)
- Prompt template variables
- Next phase routing logic
```

**Reduction:** ~200 lines by eliminating 6-7 copies of same pattern

---

### 6. Consolidate Database Logging - ~100 lines ⭐
**Current Duplication:**
26 database logging blocks with similar structure:
```bash
Skill(command: "bazinga-db", args: "log-{operation} session_id={SESSION_ID} ...")
```

**Compaction Strategy:**
Create a "Database Operations Reference" section once, then reference it:

```markdown
## Database Operations (See Reference Below)

Whenever you need to log an operation:
- See §Database Operations Reference for exact syntax
- All operations: log-session-init, log-agent-spawn, log-agent-complete, etc.

[Single comprehensive reference section with all logging patterns]
```

**Reduction:** ~80-100 lines by removing repeated examples

---

### 7. Reduce Code Examples - ~300 lines ⭐⭐
**Current:** 375 code blocks with many duplicated patterns

**Compaction Strategy:**
- Keep 1 representative example per concept
- Move comprehensive examples to template files
- Use "See template file for full structure" references

**Areas to reduce:**
- Capsule format examples (use templates reference)
- Skill() invocation examples (show once, reference)
- YAML/Markdown report formats (move to templates)
- Database logging examples (single reference section)

**Reduction:** ~250-300 lines by eliminating redundant examples

---

### 8. Shorten MANDATORY/CRITICAL Warnings - ~50 lines
**Current:** 71 instances of multi-line warnings

**Compaction Strategy:**
```markdown
Instead of:
🔴 MANDATORY DEVELOPER PROMPT BUILDING - NO SHORTCUTS ALLOWED

YOU MUST follow `templates/prompt_building.md` EXACTLY.
DO NOT write custom prompts. DO NOT improvise. DO NOT skip this process.

Use:
🔴 MANDATORY: Follow templates/developer_prompt_template.md (no shortcuts)
```

**Reduction:** ~40-50 lines by compacting warnings to single lines

---

## 📋 Proposed Strategy Options

### Option A: Maximum Extraction (Recommended) ⭐
**Approach:** Extract all prompt templates and parsing logic to separate files

**Files to Create:**
1. `templates/developer_prompt_template.md` (1,100 lines)
2. `templates/qa_prompt_template.md` (150 lines)
3. `templates/techlead_prompt_template.md` (170 lines)
4. `templates/agent_response_parsing.md` (400 lines)
5. `templates/workflow_patterns.md` (200 lines - generic spawn pattern)

**Orchestrator Changes:**
- Replace detailed sections with "Follow [template file]" references
- Keep workflow structure and routing logic
- Keep critical checks and validation

**Total Reduction:** ~2,020 lines (54% reduction)
**New Size:** ~1,745 lines (excellent!)

**Pros:**
- ✅ Massive size reduction
- ✅ Better separation of concerns
- ✅ Templates reusable by other components
- ✅ Easier to update prompt structures

**Cons:**
- ⚠️ Requires careful extraction to maintain all logic
- ⚠️ More files to manage
- ⚠️ Need to ensure references are clear

---

### Option B: Conservative Compaction (Safe)
**Approach:** Only compact repetitive patterns, no major extractions

**Changes:**
1. Consolidate agent spawn pattern (200 lines saved)
2. Consolidate database logging (100 lines saved)
3. Reduce code examples (300 lines saved)
4. Shorten warnings (50 lines saved)

**Total Reduction:** ~650 lines (17% reduction)
**New Size:** ~3,115 lines (still large)

**Pros:**
- ✅ Lower risk (no structural changes)
- ✅ Quick to implement
- ✅ No new files needed

**Cons:**
- ⚠️ Still near size limit
- ⚠️ Doesn't solve underlying structure issue

---

### Option C: Hybrid Approach (Balanced) ⭐⭐
**Approach:** Extract largest sections + compact repetitive patterns

**Extractions:**
1. Developer prompt building → template (1,100 lines)
2. Agent response parsing → template (400 lines)

**Compactions:**
1. Consolidate agent spawn pattern (200 lines)
2. Reduce code examples (200 lines)

**Total Reduction:** ~1,900 lines (50% reduction)
**New Size:** ~1,865 lines (good!)

**Pros:**
- ✅ Significant size reduction
- ✅ Only 2 new template files
- ✅ Tackles biggest sections
- ✅ Lower complexity than Option A

**Cons:**
- ⚠️ Tech Lead/QA prompts still embedded
- ⚠️ Some duplication remains

---

## 🎯 Recommended Approach: Option C (Hybrid)

**Rationale:**
1. **Immediate impact:** Tackles the two largest sections (1,500 lines)
2. **Manageable scope:** Only 2 new template files
3. **Preserves structure:** Workflow logic stays in orchestrator
4. **Future-proof:** Can extract more later if needed

**Implementation Plan:**

### Phase 1: Extract Developer Prompt Building
1. Create `templates/developer_prompt_template.md`
2. Move lines 1478-2633 from orchestrator.md
3. Replace with: "Build prompt following developer_prompt_template.md"
4. Test: Verify developer spawns still work correctly

### Phase 2: Extract Agent Response Parsing
1. Create `templates/agent_response_parsing.md`
2. Move lines 80-486 from orchestrator.md
3. Replace with: "Parse responses using agent_response_parsing.md"
4. Test: Verify capsule construction still works

### Phase 3: Compact Repetitive Patterns
1. Create generic agent spawn pattern section (lines 1461-1700 area)
2. Reference it from all spawn points instead of repeating
3. Consolidate code examples (keep 1 per concept)

### Phase 4: Validation
1. Read through entire orchestrator.md for coherence
2. Verify all template references are clear
3. Check that no functionality was lost
4. Test with simple orchestration run

**Expected Result:**
- Orchestrator.md: ~1,865 lines (from 3,765)
- 50% reduction achieved
- All functionality preserved
- Cleaner separation of concerns

---

## 🔒 Safety Considerations

**Before any extraction:**
1. ✅ Create backup of current orchestrator.md
2. ✅ Commit current state to git
3. ✅ Extract one section at a time
4. ✅ Test after each extraction
5. ✅ Don't combine with other changes

**Testing checklist after each phase:**
- [ ] File syntax is valid markdown
- [ ] All template references resolve
- [ ] No orphaned sections
- [ ] Workflow logic still makes sense
- [ ] Role checks still present
- [ ] Database operations still specified
- [ ] Error handling still in place

**Rollback strategy:**
- Each phase is a separate git commit
- Can revert individual phases if issues found
- Keep extracted content in commits (for reference)

---

## 🤔 Questions for User

Before proceeding, please confirm:

1. **Which option?** A (Maximum), B (Conservative), or C (Hybrid)?
2. **Risk tolerance?** Comfortable with structural changes or prefer minimal risk?
3. **Timeline?** Extract all at once or phase by phase with validation?
4. **Template location?** `templates/` or different folder?

---

## 📊 Size Comparison Summary

| Approach | Lines Saved | New Size | % Reduction | Risk | Files Created |
|----------|-------------|----------|-------------|------|---------------|
| Option A (Max) | 2,020 | 1,745 | 54% | Medium | 5 |
| Option B (Safe) | 650 | 3,115 | 17% | Low | 0 |
| **Option C (Hybrid)** | **1,900** | **1,865** | **50%** | **Low-Med** | **2** |

**Recommendation:** Option C provides the best balance of impact vs. risk.

---

**Next Step:** Awaiting user approval to proceed with selected option.
