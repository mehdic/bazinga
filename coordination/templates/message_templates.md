# UI Message Templates

These are the standard messages displayed to users during orchestration.

## Agent Spawning Messages

### PM Spawn
```
🧠 **ORCHESTRATOR**: Spawning Project Manager to analyze requirements...
```

### Developer Spawn (Simple Mode)
```
👨‍💻 **ORCHESTRATOR**: Spawning Developer for implementation...
```

### Developer Spawn (Parallel Mode)
```
👨‍💻 **ORCHESTRATOR**: Spawning {N} Developers in parallel for {N} task groups...
```

### QA Spawn
```
🔍 **ORCHESTRATOR**: Spawning QA Expert to validate implementation...
```

### Tech Lead Spawn
```
👔 **ORCHESTRATOR**: Spawning Tech Lead for code review...
```

### Tech Lead Spawn (Revision N)
```
👔 **ORCHESTRATOR**: Spawning Tech Lead for code review (Revision {N})...
```

### Final PM Spawn
```
🧠 **ORCHESTRATOR**: Spawning Project Manager for final check...
```

## Agent Report Formats

### Developer Report: Implementation Complete
```
## Implementation Complete

**Summary:** [One sentence]

**Files Modified:**
- file1.py: [changes]
- file2.js: [changes]

**Tests:** [status]
**Build:** [status]
**Ready for:** QA Review
```

### QA Report: Test Results
```
## QA Expert: Test Results - [PASS/FAIL]

### Quality Analysis
[Analysis of code quality]

### Test Summary
- Unit Tests: [X/Y passed]
- Integration Tests: [X/Y passed]
- Coverage: [N%]

**Recommendation:** [APPROVE_FOR_REVIEW / REQUEST_CHANGES]
```

### Tech Lead Report: Code Review
```
## Tech Lead: Code Review - [APPROVED/REQUEST_CHANGES]

**Architecture:** [assessment]
**Code Quality:** [assessment]
**Security:** [assessment]
**Performance:** [assessment]

**Decision:** [APPROVED / REQUEST_CHANGES]
**Reason:** [explanation]
```

### PM Report: Final Check
```
## Project Manager: Final Check - [BAZINGA/CONTINUE]

**Assessment:** [evaluation of completion]

**Decision:** [BAZINGA / CONTINUE with specific feedback]
```

## Progress Messages

### Iteration Progress
```
📊 **ORCHESTRATOR**: Iteration {N} - Routing to {AGENT}...
```

### Group Completion (Parallel Mode)
```
✅ **ORCHESTRATOR**: Group {group_id} complete ({X}/{N} groups done)
```

### All Groups Complete
```
🎯 **ORCHESTRATOR**: All task groups complete! Spawning PM for final check...
```

## Error Messages

### Stuck Detection
```
⚠️  **ORCHESTRATOR**: Iteration {N} - Same agent spawned {count} times. Reviewing...
```

### Build Failure
```
❌ **ORCHESTRATOR**: Build check failed. Cannot proceed.
```

### Test Failure
```
❌ **ORCHESTRATOR**: Tests failed. Routing back to developer...
```
