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
1. All expected files exist in `tmp/simple-calculator-app/`
2. DB tables populated:
   - `sessions` - New session created
   - `orchestration_logs` - Entries for each agent spawn
   - `task_groups` - Task group for calculator implementation
   - `token_usage` - Token tracking per agent
   - `decisions` - PM and Tech Lead decisions logged
3. Tests pass when run: `pytest tmp/simple-calculator-app/test_calculator.py`
