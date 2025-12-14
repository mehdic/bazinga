# BAZINGA Integration Test: Simple Calculator App

## Purpose
This spec is used to test the complete BAZINGA orchestration workflow. Running this spec through the orchestrator validates:
- PM task breakdown and mode selection
- Developer implementation
- QA Expert testing (all 5 challenge levels if applicable)
- Tech Lead review
- DB field population via bazinga-db skill
- Complete workflow from start to BAZINGA completion

## Target Directory
`tmp/simple-calculator-app/`

## Requirements

### Feature: Basic Calculator Module
Create a Python calculator module with the following functionality:

#### Core Operations
1. **Addition** - `add(a, b)` returns the sum of two numbers
2. **Subtraction** - `subtract(a, b)` returns the difference
3. **Multiplication** - `multiply(a, b)` returns the product
4. **Division** - `divide(a, b)` returns the quotient (handle division by zero)

#### Additional Requirements
5. **Memory function** - `memory_store(value)`, `memory_recall()`, `memory_clear()`
6. **History** - Track last 10 operations performed

#### Error Handling
- Division by zero should raise `ValueError` with clear message
- Invalid inputs (non-numeric) should raise `TypeError`

### Files to Create
```
tmp/simple-calculator-app/
├── calculator.py      # Main calculator module
├── test_calculator.py # Unit tests (pytest)
└── README.md          # Brief documentation
```

### Acceptance Criteria
- [ ] All 4 basic operations work correctly
- [ ] Division by zero handled properly
- [ ] Memory functions work as expected
- [ ] History tracks last 10 operations
- [ ] All unit tests pass
- [ ] Code follows Python best practices
- [ ] No security vulnerabilities

## Test Mode
This is a **simple mode** task - single developer should handle implementation.

## Post-Orchestration Verification
After BAZINGA completion, verify:

### 1. File Verification
All expected files exist in `tmp/simple-calculator-app/`:
- [ ] `calculator.py` - Main calculator module
- [ ] `test_calculator.py` - Pytest tests (50+ tests expected)
- [ ] `README.md` - Documentation

### 2. Core DB Tables
- [ ] `sessions` - New session with status "completed"
- [ ] `orchestration_logs` - Entries for PM, Developer, QA, Tech Lead, BAZINGA
- [ ] `task_groups` - Task group CALC with status "completed"

### 3. Context Engineering Verification (NEW)

**QA Specialization Templates:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "{session_id}" "specialization-loader"
```
- [ ] QA Expert should receive > 0 templates (not 0)
- [ ] If testing_mode=full, expect: `08-testing/qa-strategies.md` or `08-testing/testing-patterns.md`
- [ ] `augmented_templates` field should be populated for qa_expert spawn

**Success Criteria:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "{session_id}"
```
- [ ] Should return 7-11 criteria (matching acceptance criteria above)
- [ ] All criteria should have status "met" at BAZINGA time

**Skill Outputs:**
```bash
sqlite3 bazinga/bazinga.db "SELECT * FROM skill_outputs WHERE session_id='{session_id}';"
```
- [ ] At least 1 entry for specialization-loader
- [ ] Contains templates_used, token_count fields

**Reasoning Logs (Optional - agents may not always log):**
```bash
sqlite3 bazinga/bazinga.db "SELECT agent_type, reasoning_phase FROM orchestration_logs WHERE session_id='{session_id}' AND reasoning_phase IS NOT NULL;"
```
- [ ] Developer: `understanding`, `completion` phases
- [ ] QA Expert: `understanding`, `completion` phases
- [ ] Tech Lead: `understanding`, `completion` phases

### 4. Test Execution
```bash
cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v
```
- [ ] All tests pass (50+ tests expected)
- [ ] 100% pass rate

### 5. Known Issues to Watch

| Issue | Expected | Workaround |
|-------|----------|------------|
| QA Expert 0 templates | Should get qa-strategies.md via auto-augment | Fixed in specialization-loader Step 3.6 |
| Empty skill_outputs | Should have specialization-loader entry | Non-blocking, logged for debugging |
| Empty reasoning_log | Should have understanding+completion | Non-blocking, agents may skip |
| Empty success_criteria | PM should persist criteria | Check PM state JSON instead |

## Verification Commands (Quick Reference)

```bash
# Check session status
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1

# Full dashboard snapshot
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet dashboard-snapshot "{session_id}"

# QA template verification
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "{session_id}" "specialization-loader"

# Success criteria
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "{session_id}"

# Run tests
cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v
```
