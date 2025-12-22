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

## How to Run This Test

### 🔴 CRITICAL: Execution Requirements

**1. Run orchestration INLINE (not as spawned sub-agent)**

The orchestration must be run by the main Claude instance directly. Spawning an "orchestrator agent" via `Task()` will fail due to nested agent limitations.

```
# ✅ CORRECT: Run inline via slash command
/bazinga.orchestrate Implement the Simple Calculator App as specified in tests/integration/simple-calculator-spec.md

# ❌ WRONG: Do NOT spawn orchestrator as sub-agent
Task(description="run orchestrator", prompt="...")  # Will fail - nested spawning limits
```

**2. Follow MANDATORY prompt building workflow**

When spawning agents (Developer, QA, Tech Lead), the orchestrator MUST:

```
For each agent spawn:
1. Read FULL agent definition: agents/{agent_type}.md
2. Add specialization block from specialization-loader skill
3. Add configuration from templates/prompt_building.md
4. Include task-specific context
5. Pass complete prompt to Task()
```

**❌ DO NOT use simplified prompts** - Agents need full definitions to execute mandatory workflows (reasoning documentation, DB logging, etc.)

**3. Agents MUST log reasoning to DB**

The full agent definitions contain:
```markdown
## 🧠 Reasoning Documentation (MANDATORY)
**CRITICAL**: You MUST document your reasoning via the bazinga-db skill.
```

If agents don't log reasoning, the prompt was incomplete.

### Pre-Test Cleanup

```bash
rm -rf tmp/simple-calculator-app bazinga/bazinga.db bazinga/project_context.json
```

### Expected DB Population

After correct execution, ALL these tables should have data:

| Table | Expected Rows | Source |
|-------|---------------|--------|
| `sessions` | 1 | Orchestrator init |
| `task_groups` | 1 | PM planning |
| `success_criteria` | 7 | PM planning |
| `skill_outputs` | 1+ | Specialization-loader |
| `orchestration_logs` | 5+ | Each agent spawn |
| `reasoning_log` | 6+ | Developer, QA, TL (understanding + completion phases) |

**If `orchestration_logs` or `reasoning_log` are empty, the test was run incorrectly.**

## Post-Orchestration Verification
After BAZINGA completion, verify:

### 1. File Verification
All expected files exist in `tmp/simple-calculator-app/`:
- [ ] `calculator.py` - Main calculator module
- [ ] `test_calculator.py` - Pytest tests with comprehensive coverage
- [ ] `README.md` - Documentation

### 2. Core DB Tables
- [ ] `sessions` - New session with status "completed"
- [ ] `orchestration_logs` - Entries for PM, Developer, QA, Tech Lead, BAZINGA
- [ ] `task_groups` - Task group CALC with status "completed"

### 3. Context Engineering Verification (NEW)

**First, get the session ID:**
```bash
# Get most recent session ID
SESSION_ID=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1 | grep -o 'bazinga_[0-9_]*')
echo "Session: $SESSION_ID"
```

**QA Specialization Templates:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "$SESSION_ID" "specialization-loader"
```
- [ ] QA Expert should receive > 0 templates (not 0)
- [ ] If testing_mode=full, expect: `08-testing/qa-strategies.md` or `08-testing/testing-patterns.md`
- [ ] `augmented_templates` field should be populated for qa_expert spawn

**Success Criteria:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "$SESSION_ID"
```
- [ ] Should return 7-11 criteria (matching acceptance criteria above)
- [ ] All criteria should have status "met" at BAZINGA time

**Skill Outputs:**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "$SESSION_ID" "specialization-loader"
```
- [ ] At least 1 entry for specialization-loader
- [ ] Contains fields: `templates_after`, `augmented_templates`, `skipped_missing`, `testing_mode_used`

**Reasoning Logs (MANDATORY when run correctly):**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet stream-logs "$SESSION_ID" 20
```
- [ ] Developer: `understanding`, `completion` phases logged
- [ ] QA Expert: `understanding`, `completion` phases logged
- [ ] Tech Lead: `understanding`, `completion` phases logged

**If reasoning logs are empty:** The orchestrator used simplified prompts instead of full agent definitions. Re-run using `/bazinga.orchestrate` which follows `templates/orchestrator/phase_simple.md` to read full agent files.

### 4. Test Execution
```bash
# Use subshell to prevent CWD change from affecting subsequent commands
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v)
```
- [ ] All tests pass (0 failures)
- [ ] Comprehensive coverage of all requirements (operations, memory, history, error handling)

### 5. Known Issues and Diagnostics

| Issue | Cause | Fix |
|-------|-------|-----|
| QA Expert 0 templates | Compatibility filtering removed all templates | Fixed in specialization-loader Step 3.6 (auto-augment) |
| Empty `skill_outputs` | Specialization-loader didn't save output | Check skill invocation in orchestrator |
| Empty `orchestration_logs` | Orchestrator didn't log agent interactions | Run via `/bazinga.orchestrate` (follows full workflow) |
| Empty `reasoning_log` | Agent prompts missing full definition | **Re-run test** - orchestrator must read `agents/*.md` files |
| Empty `success_criteria` | PM didn't save criteria | Check PM spawn included full `agents/project_manager.md` |

**🔴 If logs are empty, the test was executed incorrectly.**

The `/bazinga.orchestrate` slash command follows `templates/orchestrator/phase_simple.md` which mandates:
- Reading full agent definitions from `agents/*.md`
- Including specialization blocks
- Building complete prompts per `templates/prompt_building.md`

Simplified prompts (without full agent definitions) will skip mandatory workflows like reasoning documentation.

## Verification Commands (Quick Reference)

```bash
# Get session ID first
SESSION_ID=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1 | grep -o 'bazinga_[0-9_]*')

# Check session status
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1

# Full dashboard snapshot
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet dashboard-snapshot "$SESSION_ID"

# QA template verification
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output "$SESSION_ID" "specialization-loader"

# Success criteria
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "$SESSION_ID"

# Run tests (use subshell to preserve CWD)
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v)
```
