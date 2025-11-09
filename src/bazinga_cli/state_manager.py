#!/usr/bin/env python3
"""
Thread-safe state management for BAZINGA orchestration.

Provides atomic file locking to prevent race conditions when multiple agents
access coordination state files concurrently.
"""

import fcntl
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator


class StateManager:
    """
    Thread-safe state file manager with file locking.

    Uses fcntl.flock on Unix and msvcrt.locking on Windows to ensure
    atomic read-modify-write operations on state files.
    """

    def __init__(self, coordination_dir: Path):
        """
        Initialize state manager.

        Args:
            coordination_dir: Directory containing coordination files
        """
        self.coordination_dir = Path(coordination_dir)
        self.coordination_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock_state(
        self, filename: str, default_data: Dict[str, Any] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Acquire exclusive lock on a state file for atomic read-modify-write.

        Usage:
            with state_manager.lock_state("pm_state.json") as state:
                state["completed_groups"].append(group_id)
                # Changes automatically written back on context exit

        Args:
            filename: Name of the state file (e.g., "pm_state.json")
            default_data: Default data if file doesn't exist

        Yields:
            Dictionary containing the state data (can be modified in place)

        Raises:
            OSError: If file operations fail
            json.JSONDecodeError: If file contains invalid JSON
        """
        filepath = self.coordination_dir / filename

        # Create file with default data if it doesn't exist
        if not filepath.exists():
            initial_data = default_data if default_data is not None else {}
            with open(filepath, 'w') as f:
                json.dump(initial_data, f, indent=2)

        # Open file for reading and writing
        with open(filepath, 'r+') as f:
            # Acquire exclusive lock
            self._lock_file(f)

            try:
                # Read current state
                f.seek(0)
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    # File is corrupted, use default
                    data = default_data if default_data is not None else {}

                # Yield data for modification
                yield data

                # Write modified data back atomically
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

            finally:
                # Release lock
                self._unlock_file(f)

    def _lock_file(self, file_obj):
        """
        Acquire exclusive lock on file (platform-specific).

        Args:
            file_obj: Open file object
        """
        if sys.platform == 'win32':
            # Windows: Use msvcrt
            import msvcrt
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Unix/Linux/Mac: Use fcntl
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)

    def _unlock_file(self, file_obj):
        """
        Release lock on file (platform-specific).

        Args:
            file_obj: Open file object
        """
        if sys.platform == 'win32':
            # Windows: Use msvcrt
            import msvcrt
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            # Unix/Linux/Mac: Use fcntl
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

    def read_state(self, filename: str, default_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Read state file without locking (for read-only access).

        Args:
            filename: Name of the state file
            default_data: Default data if file doesn't exist

        Returns:
            Dictionary containing the state data
        """
        filepath = self.coordination_dir / filename

        if not filepath.exists():
            return default_data if default_data is not None else {}

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default_data if default_data is not None else {}

    def write_state(self, filename: str, data: Dict[str, Any]):
        """
        Write state file with locking (atomic write).

        Args:
            filename: Name of the state file
            data: Data to write
        """
        with self.lock_state(filename) as state:
            state.clear()
            state.update(data)

    def update_pm_state(self, updates: Dict[str, Any]):
        """
        Update PM state atomically.

        Args:
            updates: Dictionary of updates to apply
        """
        with self.lock_state("pm_state.json") as state:
            state.update(updates)

    def update_orchestrator_state(self, updates: Dict[str, Any]):
        """
        Update orchestrator state atomically.

        Args:
            updates: Dictionary of updates to apply
        """
        with self.lock_state("orchestrator_state.json") as state:
            state.update(updates)

    def update_group_status(self, group_id: str, updates: Dict[str, Any]):
        """
        Update status for a specific task group atomically.

        Args:
            group_id: Group identifier (e.g., "A", "B", "main")
            updates: Dictionary of updates to apply to this group
        """
        with self.lock_state("group_status.json", default_data={}) as status:
            if group_id not in status:
                status[group_id] = {}
            status[group_id].update(updates)

    def increment_revision_count(self, group_id: str) -> int:
        """
        Atomically increment and return revision count for a group.

        Args:
            group_id: Group identifier

        Returns:
            The new revision count
        """
        with self.lock_state("group_status.json", default_data={}) as status:
            if group_id not in status:
                status[group_id] = {"revision_count": 0}

            if "revision_count" not in status[group_id]:
                status[group_id]["revision_count"] = 0

            status[group_id]["revision_count"] += 1
            return status[group_id]["revision_count"]

    def get_revision_count(self, group_id: str) -> int:
        """
        Get current revision count for a group.

        Args:
            group_id: Group identifier

        Returns:
            Current revision count (0 if not set)
        """
        status = self.read_state("group_status.json", default_data={})
        return status.get(group_id, {}).get("revision_count", 0)
