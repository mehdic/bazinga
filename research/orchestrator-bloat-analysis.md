# Orchestrator File Size Analysis

## Current State
- **orchestrator.md**: 2,960 lines (25,234 tokens - **EXCEEDS 25K LIMIT!**)
- **bazinga.orchestrate.md**: 2,967 lines (identical content + header)

## Section Breakdown

| Section | Lines | % | Issue |
|---------|-------|---|-------|
| Phase 2A (Simple Mode) | 942 | 32% | VERY VERBOSE - detailed pseudo-code |
| Phase 2B (Parallel Mode) | 655 | 22% | VERY VERBOSE - similar to 2A |
| Completion & Reporting | 381 | 13% | VERBOSE - detailed aggregation logic |
| Initialization | 218 | 7% | VERBOSE - detailed config reading |
| Phase 1 (PM Spawning) | 197 | 7% | VERBOSE - detailed prompt building |
| Logging & State | 133 | 4% | Acceptable |
| Overview & Role | 130 | 4% | Acceptable |
| Error Handling | 102 | 3% | Acceptable |
| Routing Table | 80 | 3% | Acceptable |

## Identified Bloat

### 1. **Excessive Prompt-Building Instructions** (Lines 636-886)
**Problem:** 250+ lines showing EVERY conditional for building developer prompts:
- Shows complete IF/ELSE for each skill configuration
- Repeats skill documentation inline
- Shows exact prompt templating syntax

**Example:**
```
IF `codebase_analysis_mandatory`:
```
1. **Codebase Analysis Skill**: Run BEFORE coding
   Skill(command: "codebase-analysis")
   Returns: Similar features, utilities, architectural patterns
```

IF `test_pattern_analysis_mandatory`:
... (repeated for every skill)
```

**Solution:** Replace with:
```
Build developer prompt by reading:
1. skills_config.json - add mandatory skills section
2. testing_config.json - add testing mode section
3. Append code_context prepared in Step 2A.0
4. Include PM task group and user requirements
```

**Lines saved:** ~200

---

### 2. **Duplicate Prompt Building Logic** (Phase 2B has nearly identical content)
**Problem:** Lines 1585-1755 (parallel mode developer spawning) repeat 80% of simple mode logic

**Solution:** Reference simple mode with "same as Step 2A.1 but for each group in parallel"

**Lines saved:** ~300

---

### 3. **Verbose Skills Aggregation** (Lines 2516-2586)
**Problem:** 70+ lines of pseudo-code showing how to parse each skill's output
```python
if security_scan:
    skills_used.append({
        "name": "security-scan",
        "status": security_scan.get("status", "unknown"),
        "summary": f"{len(security_scan.get('results', []))} findings"
    })
if coverage_report:
    avg_cov = coverage_report.get("summary", {}).get("line_coverage", 0)
    ...
(repeated for 10 skills)
```

**Solution:** Replace with:
```
Query each skill output from database and aggregate into skills_used list.
See templates/dashboard_schema.md for available fields.
```

**Lines saved:** ~70

---

### 4. **Redundant Example Templates** (Throughout)
**Problem:** Shows complete message templates multiple times:
- Developer spawn message (shown 3+ times)
- READY_FOR_QA format (shown 2+ times)
- BAZINGA format (shown 2+ times)
- Logging format (shown 10+ times)

**Solution:** Show template ONCE in appendix, reference by name elsewhere

**Lines saved:** ~100

---

### 5. **Overly Detailed Code Context Preparation** (Lines 586-635)
**Problem:** 50 lines of pseudo-code showing file search logic

**Solution:** "Use codebase-analysis skill or grep for similar files"

**Lines saved:** ~50

---

### 6. **Redundant Logging Instructions** (Throughout)
**Problem:** Every single step has 20-30 lines showing:
1. Natural language request to bazinga-db
2. Skill() invocation
3. Example of what gets saved

This pattern repeats 20+ times!

**Solution:** Create "Logging Pattern" section once, reference it: "Log this interaction (see Logging Pattern)"

**Lines saved:** ~150

---

### 7. **Completion Report Generation** (Lines 2693-2858)
**Problem:** 165 lines of detailed markdown template generation

**Solution:** Move template to templates/completion_report.md, reference it

**Lines saved:** ~165

---

## Recommendations for Trimming

### HIGH IMPACT (Save ~800 lines)

1. **Consolidate Prompt Building** (~200 lines saved)
   - Replace detailed IF/ELSE with "read configs and append sections"
   - Remove inline skill documentation
   - Reference skill files instead

2. **Remove Phase 2B Duplication** (~300 lines saved)
   - Phase 2B.1 → "Same as 2A.1 but spawn N developers in parallel"
   - Phase 2B.4-7 → "Same as 2A.4-7 but for each group independently"

3. **Simplify Logging Instructions** (~150 lines saved)
   - Create ONE "Logging Pattern" section
   - Replace all detailed logging blocks with: "Log to DB (see Logging Pattern)"

4. **Extract Report Templates** (~100 lines saved)
   - Move completion report template to templates/
   - Replace with: "Generate report using template"

5. **Simplify Aggregation Logic** (~50 lines saved)
   - Remove pseudo-code for skill aggregation
   - Replace with: "Query dashboard snapshot from DB"

### MEDIUM IMPACT (Save ~300 lines)

6. **Consolidate Message Templates** (~80 lines saved)
   - Create "Message Templates" appendix
   - Reference templates by name: "Display spawning message (Template: DEV_SPAWN)"

7. **Simplify Initialization** (~100 lines saved)
   - Remove detailed config file structure examples
   - Replace with: "Read skills_config.json and testing_config.json"

8. **Reduce Routing Table Verbosity** (~50 lines saved)
   - Simplify decision table to just the logic
   - Remove redundant examples

9. **Trim Role Reminders** (~70 lines saved)
   - Consolidate repeated warnings
   - Keep critical ones only

### LOW IMPACT (Save ~150 lines)

10. **Remove Build Check Details** (~40 lines saved)
    - The detailed language detection pseudo-code can be simplified

11. **Simplify Error Handling** (~30 lines saved)
    - Keep critical error patterns only

12. **Trim Code Context Logic** (~80 lines saved)
    - Replace with "Use codebase-analysis skill or grep"

---

## Proposed Target
**Current:** 2,960 lines (~25,000 tokens)
**Target:** ~1,700 lines (~14,000 tokens)
**Reduction:** ~43% smaller (1,260 lines removed)

---

## Benefits
1. ✅ Under Claude's 25K token limit
2. ✅ Faster to read/process for orchestrator
3. ✅ Easier to maintain
4. ✅ Less repetition = fewer errors
5. ✅ Cleaner separation of concerns
6. ✅ Can add future features without hitting limit

---

## Implementation Strategy

### Phase 1: Create Support Files
1. Create `templates/` directory
2. Extract templates:
   - `prompt_templates.md` - All agent prompt templates
   - `message_templates.md` - UI messages
   - `completion_report.md` - Final report template
   - `dashboard_schema.md` - Database schema reference

### Phase 2: Refactor High-Impact Sections
1. Simplify prompt building (Phase 1, 2A.1, 2B.1)
2. Remove Phase 2B duplication
3. Extract logging pattern
4. Simplify completion reporting

### Phase 3: Refactor Medium-Impact Sections
1. Consolidate message templates
2. Simplify initialization
3. Trim routing table
4. Consolidate role reminders

### Phase 4: Polish
1. Remove low-impact verbosity
2. Test with actual orchestration
3. Verify no functionality lost
4. Sync command file

---

## Risk Mitigation
- Keep old version as `orchestrator.md.backup`
- Test each phase separately
- Verify with orchestration run before committing
- Easy rollback if issues found
