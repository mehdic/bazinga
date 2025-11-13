# Skills Enforcement Test

## Test Objective
Validate that Skills are now being invoked during orchestration after the fix.

## Expected Behavior

### Before Fix (Broken)
- 0 skills executed in 277 tasks
- No bazinga/*.json result files created
- Agents received {IF} pseudocode blocks literally
- README promised "mandatory quality gates" but none ran

### After Fix (Expected)
- ✅ Developer invokes: lint-check
- ✅ Tech Lead invokes: security-scan, lint-check, test-coverage
- ✅ PM invokes: velocity-tracker
- ✅ Result files created: bazinga/lint_results.json, security_scan.json, etc.
- ✅ Skills appear in final BAZINGA report

## Test Task

Simple implementation that will trigger all mandatory Skills:

**Task:** "Add a simple hello world function to test Skills enforcement"

This should:
1. Spawn Developer → invokes lint-check before commit
2. Spawn Tech Lead → invokes security-scan, lint-check, test-coverage before review
3. Spawn PM → invokes velocity-tracker before BAZINGA

## Test Execution

Run minimal orchestration:
```
@orchestrator Add a simple hello world function to utils/hello.py that returns "Hello, BAZINGA!"
```

## Success Criteria

1. **Skills Execution Count**: > 0 (not 0/277 like before)
2. **Result Files Created**:
   - [ ] bazinga/lint_results.json
   - [ ] bazinga/security_scan.json
   - [ ] bazinga/coverage_report.json
   - [ ] bazinga/project_metrics.json

3. **Skills Appear in Agent Reports**:
   - [ ] Developer report mentions "lint-check executed"
   - [ ] Tech Lead report mentions "security-scan executed"
   - [ ] PM report mentions "velocity-tracker executed"

4. **Final BAZINGA Report Shows Skills**:
   - [ ] Skills Used section lists 4+ skills
   - [ ] Each skill shows status (✅ success, ⚠️ partial, ❌ error)

## Validation Commands

After orchestration completes:

```bash
# Check if result files exist
ls -lh bazinga/*.json

# Count how many Skills result files were created
ls bazinga/*_results.json bazinga/*_scan.json bazinga/*_report.json bazinga/*_metrics.json 2>/dev/null | wc -l

# Read lint results
cat bazinga/lint_results.json

# Read security scan results
cat bazinga/security_scan.json

# Read coverage report
cat bazinga/coverage_report.json

# Read velocity metrics
cat bazinga/project_metrics.json
```

## Expected Output

```
Skills Executed This Session: 4 of 11 available
- lint-check: ✅ Success - 0 issues found
- security-scan: ✅ Success - 0 vulnerabilities
- test-coverage: ✅ Success - 85% coverage
- velocity-tracker: ✅ Success - 1 point completed
```

## Rollback Plan

If test fails (0 skills executed again):
1. Review orchestrator logs for prompt content sent to Task tool
2. Check if {IF} blocks are still being passed literally
3. Verify skills_config.json is being read
4. Check if prompt-building logic is being executed
