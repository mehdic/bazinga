# Token-Aware Orchestration

**Status**: Research / Future Feature
**Created**: 2025-11-07
**Priority**: Medium

## Overview

Intelligent token usage monitoring system that recommends (not forces) session breaks at specific thresholds, allowing users to maintain control while benefiting from guided orchestration.

## Problem Statement

Current orchestration can consume significant token budgets in long-running sessions. An initial proposal suggested automatic session breaks at 70% token usage, but this approach has significant drawbacks.

## Initial Proposal (Rejected)

**Option B at 70% Token Usage**: Automatically commit current work and start a new session when reaching 70% of token budget.

### Why This Was Rejected

❌ **Arbitrary threshold** - 70% might be too early (wastes context) or too late (risks running out mid-task)
❌ **Interruption risk** - Could break during critical multi-step operations
❌ **Loss of user control** - Forces behavior without user consent
❌ **Fragmented sessions** - Creates artificial breakpoints in logical work units

## Recommended Alternative: Token-Aware Orchestration

✅ **Progressive conservatism** with user control

### Implementation Design

#### Three Progressive Modes

| Token Usage | Mode | Behavior | Rationale |
|-------------|------|----------|-----------|
| **< 70%** | Normal | Full operation, no restrictions | Plenty of budget available |
| **70-84%** | Conservative | Finish current work, don't start new groups | Prepare for potential wrap-up |
| **85-94%** | Wrap-up | Finish in-progress tasks only, prepare handoff | Ensure clean exit point |
| **95%+** | Emergency | Save state immediately, create handoff document | Prevent mid-task interruption |

#### Conservative Mode (70-84%)

**Behavior**:
- Complete current group(s) that are in progress
- Do NOT spawn new developer groups
- PM can still check completion and send BAZINGA if all work is done
- If more work exists, recommend session break to user

**Example Output**:
```
⚠️ **ORCHESTRATOR**: Token usage at 72% - entering conservative mode
   Current groups will complete, but new groups will be deferred.

   ℹ️  Recommendation: After current work completes, consider starting
       a new session to continue with remaining groups.
```

#### Wrap-up Mode (85-94%)

**Behavior**:
- Finish ONLY tasks already in progress (Developer → QA → Tech Lead flow)
- Do NOT accept changes requested from Tech Lead (too risky)
- If Tech Lead requests changes, save state and prepare handoff instead
- Create detailed handoff document with current state

**Example Output**:
```
⚠️ **ORCHESTRATOR**: Token usage at 87% - entering wrap-up mode
   Completing in-progress tasks only. Changes requested by Tech Lead
   will be deferred to next session.

   📝 Creating handoff document...
```

#### Emergency Mode (95%+)

**Behavior**:
- Immediately save all state files
- Create comprehensive handoff document
- Do NOT spawn any new agents
- Provide clear resume instructions

**Example Output**:
```
🚨 **ORCHESTRATOR**: Token usage at 96% - emergency mode activated
   Saving state and creating handoff document for next session...

   ✅ State saved to bazinga/
   📄 Handoff: docs/session-handoff.md

   To resume: @orchestrator Resume from previous session
```

### Handoff Document Format

```markdown
# Session Handoff

**Created**: 2025-11-07 15:30:00 UTC
**Reason**: Token usage reached 87% (wrap-up mode)
**Token Budget Remaining**: ~13%

## Current State

**Mode**: Parallel
**Active Groups**: A, B, C

### Groups Status

| Group | Status | Current Stage | Next Action |
|-------|--------|---------------|-------------|
| A | ✅ Complete | Approved by Tech Lead | Ready for PM check |
| B | ⏳ In Progress | QA Testing | Wait for QA results |
| C | 🔄 Revising | Developer fixing issues | Needs re-review after fixes |

### Completed Work

- Group A: JWT authentication (APPROVED ✅)
  - Branch: feature/group-A-jwt-auth
  - Commits: abc123, def456
  - All tests passing

### Pending Work

**Group B** (User Registration):
- Developer completed implementation
- QA testing in progress
- Branch: feature/group-B-user-reg

**Group C** (Password Reset):
- Developer addressed first round of Tech Lead feedback
- Needs re-testing by QA
- Branch: feature/group-C-pwd-reset

**Remaining Groups Not Yet Started**: D, E

## Resume Instructions

**Option 1: Continue from where we left off**
```bash
@orchestrator Resume session - Group A approved, Groups B and C in progress
```

**Option 2: Review and restart**
```bash
# Review state files
cat bazinga/pm_state.json
cat bazinga/group_status.json

# Then invoke orchestrator with context
@orchestrator Continue orchestration - check coordination files for state
```

## Files Modified

- bazinga/pm_state.json (updated)
- bazinga/group_status.json (updated)
- bazinga/orchestrator_state.json (updated)
- docs/orchestration-log.md (complete log available)

## State Files Preserved

All state files have been saved and are ready for next session:
- ✅ bazinga/pm_state.json
- ✅ bazinga/group_status.json
- ✅ bazinga/orchestrator_state.json
- ✅ docs/orchestration-log.md

## Next Session Strategy

**Recommendation**:
1. Spawn PM to review Group A approval
2. Wait for Groups B and C to complete their current cycles
3. Then proceed with Groups D and E in next batch

**Estimated Completion**: 2-3 more groups remaining
```

## Implementation Location

### Primary: Orchestrator Agent

**File**: `agents/orchestrator.md`

**Where to Add**:
- Add token monitoring function that checks usage before each spawn
- Modify routing logic to respect mode (conservative/wrap-up/emergency)
- Add handoff document generation function
- Update state files to include token usage tracking

**Pseudocode**:
```python
def check_token_usage():
    usage = get_current_token_usage()

    if usage >= 0.95:
        return "emergency", "Token budget critically low"
    elif usage >= 0.85:
        return "wrap-up", "Preparing for session end"
    elif usage >= 0.70:
        return "conservative", "Limiting new work"
    else:
        return "normal", None

def should_spawn_new_group(mode):
    if mode == "emergency":
        return False, "Emergency mode - saving state"
    elif mode == "wrap-up":
        return False, "Wrap-up mode - completing in-progress only"
    elif mode == "conservative":
        return False, "Conservative mode - not starting new groups"
    else:
        return True, None

# Before spawning developers:
mode, reason = check_token_usage()
can_spawn, block_reason = should_spawn_new_group(mode)

if not can_spawn:
    create_handoff_document()
    notify_user(reason)
    if mode == "emergency":
        exit_workflow()
```

### Secondary: Project Manager

**File**: `agents/pm.md`

**Enhancement**: PM should be aware of token mode and adjust planning accordingly

**Pseudocode**:
```python
# PM receives token mode in context
if token_mode == "conservative":
    # Be more selective about assigning new batches
    # Recommend smaller group counts
    assign_batch(max_groups=1)
elif token_mode == "wrap-up":
    # Don't assign new work
    check_completion_only()
```

## Benefits

✅ **User Control**: User retains final decision on when to break session
✅ **Smart Guidance**: System provides intelligent recommendations
✅ **Clean Exits**: No mid-task interruptions
✅ **Context Preservation**: Handoff documents ensure continuity
✅ **Budget Awareness**: Better token budget management
✅ **Graceful Degradation**: Progressive conservatism prevents abrupt stops

## Drawbacks & Considerations

⚠️ **Complexity**: Adds another layer of orchestration logic
⚠️ **Token Tracking**: Requires accurate token usage monitoring
⚠️ **Edge Cases**: What if emergency mode triggers during critical operation?
⚠️ **User Experience**: Users need to understand the modes

## Open Questions

1. **Token Tracking Accuracy**: How do we accurately track token usage in real-time?
2. **Mode Transitions**: Should we notify user when transitioning between modes?
3. **Override Capability**: Should users be able to override and force continuation?
4. **Resume Logic**: Should orchestrator have special "resume from handoff" mode?

## Next Steps (If/When Implementing)

1. ✅ Document the research (this file)
2. ⏳ Design token tracking mechanism
3. ⏳ Implement mode detection in orchestrator
4. ⏳ Add handoff document generation
5. ⏳ Update PM to be token-aware
6. ⏳ Test with various token usage scenarios
7. ⏳ Add user documentation

## Related Files

- `agents/orchestrator.md` - Main orchestration logic
- `agents/pm.md` - Project manager decision logic
- `bazinga/orchestrator_state.json` - Would need token_usage field
- `docs/session-handoff.md` - Template for handoff documents

## References

- Original discussion: Session continuation after context limit
- Critical analysis: Documented in README updates (2025-11-07)
- Alternative rejected: Automatic 70% cutoff

---

**Status**: Research complete, implementation deferred
**Decision**: Implement if token management becomes a recurring issue
**Priority**: Medium (nice-to-have, not critical)
