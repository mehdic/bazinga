# Investigation System Critical Fixes

## Changes Being Made

### 1. Skills Configuration
✅ DONE:
- Added "optional" status (can be used if needed, but not automatic)
- Changed all previously disabled skills to "optional" by default (lite profile)
- All agents now have optional skills available when needed
- Updated init script to match

### 2. Orchestrator Architecture Fixes

#### Problem: WHILE Loop Impossible
The orchestrator cannot maintain a WHILE loop because agents terminate after each response.

#### Solution: Turn-Based Investigation Detection

**Add Step 0 (BEFORE Step 1):**
- Check database for active investigations
- If found, resume investigation
- If not, proceed to normal workflow

**Remove WHILE Loop:**
- Investigation continues across multiple orchestrator invocations
- Each turn processes ONE iteration
- Orchestrator terminates after spawning Investigator
- Next orchestrator turn detects active investigation and continues

#### Implementation Steps:

1. **Add Step 0: Active Investigation Check**
   - Query database for investigations with status = "in_progress"
   - If found: Load state, jump to investigation iteration
   - If not: Proceed to Step 1

2. **Remove WHILE loop from Step 2A.6b**
   - Change to: "Process ONE investigation iteration this turn"
   - Add: "Investigation will continue on next orchestrator invocation"

3. **Add Investigation Deduplication**
   - Before creating new investigation, check if one exists for this group
   - If exists and in_progress: Resume it
   - If exists and completed: Don't reinvestigate

4. **Add Solution Handoff Workflow**
   - After ROOT_CAUSE_FOUND + Tech Lead validation
   - Spawn Developer with investigation findings
   - Developer implements solution

5. **Add BLOCKED Resolution Path**
   - PM receives blocker description
   - PM decides: PROVIDE_RESOURCES | REPRIORITIZE | ESCALATE_EXTERNALLY
   - If PROVIDE_RESOURCES: Resume investigation with new context

6. **Add Empty Hypothesis Matrix Validation**
   - Investigator checks if matrix is empty or malformed
   - Returns BLOCKED if cannot proceed

### 3. Tech Lead Language Fixes

Change "spawn" to "request" throughout Tech Lead agent:
- "Spawning Investigator" → "Requesting Investigator"
- "Spawn Command" → "Investigation Request"

### 4. Documentation Updates

Update README to reflect:
- Optional skill status
- Turn-based investigation model
- Investigation workflow examples

## Files to Modify

1. ✅ bazinga/skills_config.json - Add optional status
2. ✅ scripts/init-orchestration.sh - Match skills config
3. ⏳ agents/orchestrator.md - Add Step 0, remove WHILE loop, add workflows
4. ⏳ agents/investigator.md - Add validation
5. ⏳ agents/techlead.md - Change spawn to request
6. ⏳ README.md - Update documentation

## Testing Plan

After fixes:
1. Verify skills_config.json is valid JSON
2. Test init script creates correct config
3. Review orchestrator logic flow
4. Check investigation state machine
