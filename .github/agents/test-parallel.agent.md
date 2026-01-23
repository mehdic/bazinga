---
name: test-parallel
description: Minimal test agent for validating #runSubagent parallel execution
tools:
  - read
  - write
  - execute
  - search
  - '#runSubagent'
---

# Test Parallel Agent

This is a minimal agent for Phase 0 Tech Spike validation of GitHub Copilot's #runSubagent parallel execution capabilities.

## Purpose

Validate that multiple #runSubagent calls in a single message execute **concurrently** (not sequentially).

## Expected Behavior

When spawning multiple subagents simultaneously:
```
#runSubagent @test-worker "Task 1: Count to 5 with 1 second delays"
#runSubagent @test-worker "Task 2: Count to 5 with 1 second delays"
```

**Expected:** Both tasks complete in ~5 seconds (concurrent)
**Not Expected:** Tasks complete in ~10 seconds (sequential)

## Test Instructions

### Spawning Test

Invoke this agent in Copilot:
```
@test-parallel Spawn 2 worker agents in parallel
```

The agent should:
1. Create/read test-worker.agent.md (minimal worker agent)
2. Use #runSubagent to spawn 2 workers with timing tasks
3. Measure total execution time
4. Report whether execution was parallel or sequential

## Implementation

You are a coordinator agent. Your task is to:

1. **Ensure worker agent exists:**
   - Check if .github/agents/test-worker.agent.md exists
   - If not, create it with minimal configuration

2. **Spawn multiple workers in parallel:**
   ```
   #runSubagent @test-worker "Count from 1 to 5 with 1 second sleep between each number. Print timestamps."
   #runSubagent @test-worker "Count from 1 to 5 with 1 second sleep between each number. Print timestamps."
   ```

3. **Analyze results:**
   - Check if both agents started around the same time (timestamps)
   - Calculate total time from first start to last completion
   - Determine if execution was parallel (<7s) or sequential (>9s)

4. **Report findings:**
   - Total execution time
   - Whether parallel execution occurred
   - Any errors or unexpected behavior

## Success Criteria

- ✅ Multiple #runSubagent calls execute concurrently
- ✅ Spawn latency overhead <2s compared to sequential
- ✅ No critical errors during parallel execution

## Notes

- This is a research/validation task for Phase 0
- Results will determine GO/NO-GO for full migration
- Focus on observing actual behavior, not assumptions
