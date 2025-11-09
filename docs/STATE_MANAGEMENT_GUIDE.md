# State Management Guide for Agents

## Overview

Agents use the `state_helper.py` script to safely read and write state files with file locking. This prevents race conditions when multiple agents run in parallel.

**Why use state_helper.py?**
- ✅ Automatic file locking (prevents race conditions)
- ✅ Atomic read-modify-write operations
- ✅ Cross-platform support (Unix/Windows)
- ✅ Automatic corruption recovery

**Don't manually read/write JSON files!** Use the helper script instead.

---

## Basic Usage

### Read State

```bash
# Read entire state file
python scripts/state_helper.py read pm_state.json

# Example output:
# {
#   "iteration": 1,
#   "mode": "parallel",
#   "completed_groups": []
# }
```

### Update State (Merge)

```bash
# Merge updates into existing state
python scripts/state_helper.py update pm_state.json '{"iteration": 2, "mode": "simple"}'
```

This **merges** the updates with existing state:
- Before: `{"iteration": 1, "mode": "parallel", "completed_groups": []}`
- After: `{"iteration": 2, "mode": "simple", "completed_groups": []}`

### Write State (Replace)

```bash
# Replace entire state file
python scripts/state_helper.py write pm_state.json '{"iteration": 1, "mode": "simple"}'
```

This **replaces** the entire state file.

---

## Common Agent Patterns

### Pattern 1: Update PM State

```bash
# PM updates iteration count
python scripts/state_helper.py update pm_state.json '{
  "iteration": 2,
  "last_update": "2024-11-09T10:30:00Z"
}'
```

### Pattern 2: Update Group Status

```bash
# Developer marks group as in_progress
python scripts/state_helper.py update-group group_A '{
  "status": "in_progress",
  "developer": "Developer-1",
  "started_at": "2024-11-09T10:30:00Z"
}'

# Tech Lead marks group as completed
python scripts/state_helper.py update-group group_A '{
  "status": "completed",
  "approved_by": "Tech Lead"
}'
```

### Pattern 3: Increment Revision Count

```bash
# Increment revision count atomically
new_count=$(python scripts/state_helper.py increment-revision group_A)
echo "Revision count: $new_count"

# Use revision count to determine mode (Sonnet vs Opus)
if [ "$new_count" -ge 3 ]; then
  echo "Using Opus (revision $new_count)"
else
  echo "Using Sonnet (revision $new_count)"
fi
```

### Pattern 4: Read and Check State

```bash
# Read state and extract value using jq
mode=$(python scripts/state_helper.py read pm_state.json | jq -r '.mode')

if [ "$mode" = "parallel" ]; then
  echo "Running in parallel mode"
else
  echo "Running in simple mode"
fi
```

---

## Agent-Specific Examples

### Orchestrator Agent

```bash
# Initialize orchestrator state
python scripts/state_helper.py write orchestrator_state.json '{
  "phase": "initialization",
  "active_agents": [],
  "last_update": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

# Update phase
python scripts/state_helper.py update orchestrator_state.json '{
  "phase": "pm_planning",
  "active_agents": ["pm"]
}'
```

### Project Manager Agent

```bash
# Update PM state after creating task groups
python scripts/state_helper.py update pm_state.json '{
  "mode": "parallel",
  "task_groups": {
    "A": {"status": "pending", "files": ["auth.py"]},
    "B": {"status": "pending", "files": ["users.py"]}
  },
  "iteration": 1
}'

# Track completed groups
python scripts/state_helper.py update pm_state.json '{
  "completed_groups": ["A", "B"]
}'
```

### Developer Agent

```bash
# Mark group as in progress
python scripts/state_helper.py update-group group_A '{
  "status": "in_progress",
  "developer": "Developer-1"
}'

# After completion
python scripts/state_helper.py update-group group_A '{
  "status": "ready_for_qa",
  "completed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'
```

### Tech Lead Agent

```bash
# Get current revision count
revision=$(python scripts/state_helper.py get-revision group_A)

# Increment revision count (changes requested)
new_revision=$(python scripts/state_helper.py increment-revision group_A)

# Determine which model to use
if [ "$new_revision" -ge 3 ]; then
  model="opus"
else
  model="sonnet"
fi

echo "Using model: $model (revision $new_revision)"
```

### QA Expert Agent

```bash
# Update test results
python scripts/state_helper.py update-group group_A '{
  "tests_passed": 25,
  "tests_failed": 0,
  "test_status": "PASS"
}'
```

---

## Error Handling

The helper script handles errors gracefully:

```bash
# Check if operation succeeded
if python scripts/state_helper.py update pm_state.json '{"key": "value"}'; then
  echo "Update successful"
else
  echo "Update failed"
  exit 1
fi
```

---

## Advanced: Custom Atomic Operations

For complex state updates, you can use a temporary approach:

```bash
# Read current state
current=$(python scripts/state_helper.py read pm_state.json)

# Modify in shell (using jq for JSON manipulation)
updated=$(echo "$current" | jq '.completed_groups += ["C"]')

# Write back atomically
echo "$updated" | python -c "
import json, sys
sys.path.insert(0, 'src')
from bazinga_cli.state_manager import StateManager
manager = StateManager('coordination')
manager.write_state('pm_state.json', json.load(sys.stdin))
"
```

---

## Migration from Old Pattern

### OLD (Unsafe - Race Conditions!)

```bash
# ❌ Don't do this - race conditions!
cat coordination/pm_state.json | jq '.iteration += 1' > coordination/pm_state.json
```

**Problem**: If two agents do this simultaneously, one agent's changes will be lost.

### NEW (Safe - Atomic Updates)

```bash
# ✅ Do this - atomic and safe
python scripts/state_helper.py update pm_state.json '{"iteration": 2}'
```

---

## State Files Reference

| File | Used By | Purpose |
|------|---------|---------|
| `pm_state.json` | Project Manager | Task groups, mode, progress |
| `orchestrator_state.json` | Orchestrator | Active agents, phase |
| `group_status.json` | All agents | Per-group status and revisions |
| `messages/*.json` | All agents | Inter-agent communication |

---

## Tips and Best Practices

1. **Always use state_helper.py** - Don't read/write JSON directly
2. **Use update, not write** - Merging is safer than replacing
3. **Check exit codes** - Verify operations succeeded
4. **Use jq for extraction** - Parse JSON output safely
5. **Timestamps in ISO format** - Use `date -u +%Y-%m-%dT%H:%M:%SZ`

---

## Troubleshooting

### "No such file or directory"

State helper not found. Use full path:
```bash
python "$(pwd)/scripts/state_helper.py" read pm_state.json
```

### "Import error: bazinga_cli"

Run from project root directory:
```bash
cd /path/to/bazinga
python scripts/state_helper.py read pm_state.json
```

### State file corrupted

The helper automatically recovers from corrupted JSON files:
```bash
# This will create fresh state if corrupted
python scripts/state_helper.py read pm_state.json
```

---

## Performance

State operations are fast:
- **Read**: <1ms
- **Update**: 1-5ms (includes locking)
- **Increment**: 1-5ms (atomic counter)

File locking overhead is minimal even with multiple concurrent agents.

---

## Example: Complete Developer Workflow

```bash
#!/bin/bash
# Developer agent workflow with safe state management

GROUP_ID="group_A"

# 1. Mark as in progress
python scripts/state_helper.py update-group "$GROUP_ID" '{
  "status": "in_progress",
  "developer": "Developer-1",
  "started_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

# 2. Implement code
echo "Implementing..."

# 3. Run tests
if pytest; then
  # 4. Mark as ready for QA
  python scripts/state_helper.py update-group "$GROUP_ID" '{
    "status": "ready_for_qa",
    "tests_passed": true
  }'
else
  # Tests failed
  python scripts/state_helper.py update-group "$GROUP_ID" '{
    "status": "tests_failed"
  }'
  exit 1
fi
```

---

## See Also

- `src/bazinga_cli/state_manager.py` - StateManager implementation
- `tests/test_state_manager.py` - State manager tests
- `SECURITY_FIXES.md` - Race condition prevention
