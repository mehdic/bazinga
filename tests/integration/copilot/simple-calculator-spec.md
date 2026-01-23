# BAZINGA Integration Test: Simple Calculator App (Copilot Version)

## Purpose

This spec tests the complete BAZINGA orchestration workflow on **GitHub Copilot**. It validates:
- PM task breakdown and mode selection
- Developer implementation via Copilot subagents
- QA Expert testing (all 5 challenge levels if applicable)
- Tech Lead review
- File-based state persistence (Copilot doesn't use SQLite)
- Complete workflow from start to BAZINGA completion

## Platform Differences from Claude Code

| Aspect | Claude Code | GitHub Copilot |
|--------|-------------|----------------|
| Agent Spawning | `Task()` tool | `#runSubagent @agent-name` |
| State Backend | SQLite database | JSON files in bazinga/state/ |
| Skill Invocation | Skill() tool | Filesystem loading |
| Session Files | bazinga/bazinga.db | bazinga/state/session.json |
| Handoff Files | bazinga/artifacts/{session}/{group}/ | bazinga/state/{group}/ |

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

## How to Run This Test on Copilot

### 1. Pre-Test Setup

```bash
# Create state directory
mkdir -p bazinga/state

# Clean previous test artifacts
rm -rf tmp/simple-calculator-app bazinga/state/*
```

### 2. Initialize Session

Create the initial session state:

```bash
cat > bazinga/state/session.json << 'EOF'
{
  "session_id": "bazinga_copilot_test_001",
  "mode": "simple",
  "status": "active",
  "platform": "copilot",
  "requirements": "Build a calculator with add, subtract, multiply, divide, memory, and history",
  "created_at": "2026-01-23T12:00:00Z"
}
EOF
```

### 3. Invoke Orchestrator

Use the Copilot orchestrator agent:

```
@orchestrator Implement the Simple Calculator App as specified in tests/integration/copilot/simple-calculator-spec.md
```

### 4. Expected Workflow

```
1. Orchestrator spawns @project-manager
   → PM analyzes requirements
   → PM returns PLANNING_COMPLETE with task groups

2. Orchestrator spawns @developer
   → Developer implements calculator.py
   → Developer writes tests
   → Developer returns READY_FOR_QA

3. Orchestrator spawns @qa-expert
   → QA runs 5-level challenge
   → QA returns PASS (or FAIL with feedback)

4. Orchestrator spawns @tech-lead
   → TL reviews code quality
   → TL returns APPROVED (or CHANGES_REQUESTED)

5. Orchestrator spawns @project-manager
   → PM checks all criteria met
   → PM returns BAZINGA
```

## Post-Orchestration Verification

### 1. State File Verification

```bash
# Session state
cat bazinga/state/session.json
# Should show status: "completed"

# Task groups
cat bazinga/state/task_groups.json
# Should show group CALC with status: "completed"

# Orchestration log
cat bazinga/state/orchestration_log.json
# Should have entries for PM, Developer, QA, Tech Lead, BAZINGA
```

### 2. File Verification

All expected files exist in `tmp/simple-calculator-app/`:
- [ ] `calculator.py` - Main calculator module
- [ ] `test_calculator.py` - Pytest tests with comprehensive coverage
- [ ] `README.md` - Documentation

### 3. Handoff Files

```bash
# Developer handoff
cat bazinga/state/CALC/handoff_developer.json

# QA handoff
cat bazinga/state/CALC/handoff_qa_expert.json

# Tech Lead handoff
cat bazinga/state/CALC/handoff_tech_lead.json
```

### 4. Test Execution

```bash
# Use subshell to prevent CWD change
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v)
```

- [ ] All tests pass (0 failures)
- [ ] Comprehensive coverage of all requirements

## Expected State Files

### session.json (After Completion)

```json
{
  "session_id": "bazinga_copilot_test_001",
  "mode": "simple",
  "status": "completed",
  "platform": "copilot",
  "requirements": "Build a calculator with add, subtract, multiply, divide, memory, and history",
  "created_at": "2026-01-23T12:00:00Z",
  "completed_at": "2026-01-23T12:30:00Z"
}
```

### task_groups.json (After Completion)

```json
{
  "groups": [
    {
      "group_id": "CALC",
      "name": "Calculator Implementation",
      "status": "completed",
      "assigned_to": "developer_1",
      "branch": "feature/calculator"
    }
  ]
}
```

### orchestration_log.json

```json
{
  "entries": [
    {"timestamp": "...", "agent": "@project-manager", "action": "spawn", "status": "PLANNING_COMPLETE"},
    {"timestamp": "...", "agent": "@developer", "action": "spawn", "status": "READY_FOR_QA"},
    {"timestamp": "...", "agent": "@qa-expert", "action": "spawn", "status": "PASS"},
    {"timestamp": "...", "agent": "@tech-lead", "action": "spawn", "status": "APPROVED"},
    {"timestamp": "...", "agent": "@project-manager", "action": "spawn", "status": "BAZINGA"}
  ]
}
```

## Behavior Differences from Claude Code

### 1. No SQLite Database

Copilot uses JSON files instead of SQLite. The bazinga-db skill is NOT available.
State persistence is handled via `bazinga/platform/state_backend/file.py`.

### 2. Handoff File Location

| Platform | Location |
|----------|----------|
| Claude Code | `bazinga/artifacts/{session_id}/{group_id}/handoff_{agent}.json` |
| Copilot | `bazinga/state/{group_id}/handoff_{agent}.json` |

### 3. Session Resumption

On Copilot, sessions can be resumed by reading `bazinga/state/session.json` and checking status.

### 4. Skill Invocation

Skills are invoked by reading markdown files directly, not via SQLite.

## Performance Expectations

Based on performance benchmarks (see research/copilot-migration/PERFORMANCE_COMPARISON.md):

| Metric | Expected |
|--------|----------|
| Single spawn latency | < 5ms |
| Parallel spawn (4) latency | < 20ms |
| State operation latency | < 50ms |
| Copilot parity | Within 2x of Claude Code |

## Known Limitations

1. **No real-time database queries** - State is file-based
2. **No reasoning log persistence** - JSON doesn't support complex queries
3. **Manual session cleanup** - Must delete state files between tests

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Missing state files | State directory not created | Run `mkdir -p bazinga/state` |
| Agent not found | Missing agent definition | Check `.github/agents/` directory |
| Handoff parsing error | Invalid JSON in handoff | Validate JSON syntax |
| Test failures | Implementation issues | Check developer handoff for details |

## Verification Commands (Quick Reference)

```bash
# Check session status
cat bazinga/state/session.json | jq .status

# Check task groups
cat bazinga/state/task_groups.json | jq '.groups[0].status'

# Check orchestration log
cat bazinga/state/orchestration_log.json | jq '.entries[-1]'

# Run tests
(cd tmp/simple-calculator-app && python -m pytest test_calculator.py -v)
```

## Related Files

- Orchestrator Agent: `.github/agents/orchestrator.agent.md`
- Platform Abstraction: `bazinga/platform/`
- Integration Tests: `tests/platform/test_orchestration_integration.py`
- Performance Tests: `tests/platform/test_orchestration_performance.py`
- PRD: `research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md`
