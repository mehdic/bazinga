#!/usr/bin/env python3
"""
Helper script for agents to safely manage state files with file locking.

This script is called by agent markdown files via Bash to ensure thread-safe
state management when multiple agents run in parallel.

Usage:
    # Read state
    python scripts/state_helper.py read pm_state.json

    # Update state (merge)
    python scripts/state_helper.py update pm_state.json '{"iteration": 1}'

    # Lock and modify (for complex updates)
    python scripts/state_helper.py lock pm_state.json 'state["count"] += 1'

    # Increment revision count
    python scripts/state_helper.py increment-revision group_A
"""

import json
import sys
from pathlib import Path

# Add src to path to import StateManager
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bazinga_cli.state_manager import StateManager


def main():
    if len(sys.argv) < 3:
        print("Usage: state_helper.py <command> <filename> [data]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    # Initialize state manager
    manager = StateManager("coordination")

    if command == "read":
        # Read state file
        filename = sys.argv[2]
        state = manager.read_state(filename)
        print(json.dumps(state, indent=2))

    elif command == "update":
        # Update state file (merge updates)
        filename = sys.argv[2]
        updates = json.loads(sys.argv[3])

        with manager.lock_state(filename) as state:
            state.update(updates)

        print(f"Updated {filename}", file=sys.stderr)

    elif command == "write":
        # Write entire state file (replace)
        filename = sys.argv[2]
        data = json.loads(sys.argv[3])
        manager.write_state(filename, data)
        print(f"Wrote {filename}", file=sys.stderr)

    elif command == "increment-revision":
        # Increment revision count for a group
        group_id = sys.argv[2]
        count = manager.increment_revision_count(group_id)
        print(count)  # Output the new count

    elif command == "get-revision":
        # Get current revision count for a group
        group_id = sys.argv[2]
        count = manager.get_revision_count(group_id)
        print(count)

    elif command == "update-group":
        # Update group status
        group_id = sys.argv[2]
        updates = json.loads(sys.argv[3])
        manager.update_group_status(group_id, updates)
        print(f"Updated group {group_id}", file=sys.stderr)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
