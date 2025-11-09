"""
Tests for state manager with file locking.

Tests atomic read-modify-write operations and race condition prevention.
"""

import json
import threading
import time
from pathlib import Path

import pytest

from bazinga_cli.state_manager import StateManager


class TestStateManager:
    """Test state manager functionality."""

    def test_init_creates_directory(self, tmp_path):
        """Test state manager creates coordination directory."""
        coord_dir = tmp_path / "coordination"
        manager = StateManager(coord_dir)

        assert coord_dir.exists()
        assert coord_dir.is_dir()

    def test_lock_state_creates_file_with_defaults(self, tmp_path):
        """Test lock_state creates file with default data if it doesn't exist."""
        manager = StateManager(tmp_path / "coordination")
        default_data = {"initialized": True, "count": 0}

        with manager.lock_state("test.json", default_data=default_data) as state:
            assert state == default_data

        # Verify file was created
        state_file = tmp_path / "coordination" / "test.json"
        assert state_file.exists()

    def test_lock_state_read_modify_write(self, tmp_path):
        """Test atomic read-modify-write operation."""
        manager = StateManager(tmp_path / "coordination")

        # Initialize state
        with manager.lock_state("counter.json", default_data={"count": 0}) as state:
            state["count"] = 1

        # Read and verify
        with manager.lock_state("counter.json") as state:
            assert state["count"] == 1

        # Modify again
        with manager.lock_state("counter.json") as state:
            state["count"] += 1

        # Verify final value
        with manager.lock_state("counter.json") as state:
            assert state["count"] == 2

    def test_lock_state_prevents_race_conditions(self, tmp_path):
        """Test file locking prevents race conditions with concurrent writes."""
        manager = StateManager(tmp_path / "coordination")

        # Initialize counter
        with manager.lock_state("race.json", default_data={"count": 0}) as state:
            pass

        errors = []
        results = []

        def increment_counter(thread_id):
            """Increment counter 10 times."""
            try:
                for _ in range(10):
                    with manager.lock_state("race.json") as state:
                        current = state["count"]
                        # Simulate some processing time
                        time.sleep(0.001)
                        state["count"] = current + 1
                results.append(thread_id)
            except Exception as e:
                errors.append(e)

        # Run 5 threads concurrently, each incrementing 10 times
        threads = []
        for i in range(5):
            t = threading.Thread(target=increment_counter, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

        # Verify all threads completed
        assert len(results) == 5

        # Verify final count is correct (5 threads * 10 increments = 50)
        with manager.lock_state("race.json") as state:
            assert state["count"] == 50, \
                f"Race condition detected: expected 50, got {state['count']}"

    def test_read_state_nonexistent_file(self, tmp_path):
        """Test reading non-existent file returns default."""
        manager = StateManager(tmp_path / "coordination")
        default = {"default": True}

        result = manager.read_state("nonexistent.json", default_data=default)

        assert result == default

    def test_read_state_corrupted_json(self, tmp_path):
        """Test reading corrupted JSON returns default."""
        coord_dir = tmp_path / "coordination"
        coord_dir.mkdir()

        # Create corrupted JSON file
        corrupted_file = coord_dir / "corrupted.json"
        corrupted_file.write_text("{invalid json content")

        manager = StateManager(coord_dir)
        default = {"recovered": True}

        result = manager.read_state("corrupted.json", default_data=default)

        assert result == default

    def test_write_state(self, tmp_path):
        """Test writing state atomically."""
        manager = StateManager(tmp_path / "coordination")

        data = {"key": "value", "number": 42}
        manager.write_state("test.json", data)

        # Verify written correctly
        result = manager.read_state("test.json")
        assert result == data

    def test_update_pm_state(self, tmp_path):
        """Test updating PM state."""
        manager = StateManager(tmp_path / "coordination")

        # Initialize
        with manager.lock_state("pm_state.json", default_data={"iteration": 0}) as state:
            pass

        # Update
        manager.update_pm_state({"iteration": 1, "mode": "parallel"})

        # Verify
        result = manager.read_state("pm_state.json")
        assert result["iteration"] == 1
        assert result["mode"] == "parallel"

    def test_update_orchestrator_state(self, tmp_path):
        """Test updating orchestrator state."""
        manager = StateManager(tmp_path / "coordination")

        manager.update_orchestrator_state({"phase": "initialization", "agents": []})

        result = manager.read_state("orchestrator_state.json")
        assert result["phase"] == "initialization"
        assert result["agents"] == []

    def test_update_group_status(self, tmp_path):
        """Test updating group status."""
        manager = StateManager(tmp_path / "coordination")

        # Update group A
        manager.update_group_status("A", {"status": "in_progress", "developer": "Dev-1"})

        # Update group B
        manager.update_group_status("B", {"status": "pending"})

        # Update group A again (should merge)
        manager.update_group_status("A", {"status": "completed"})

        # Verify
        result = manager.read_state("group_status.json")
        assert result["A"]["status"] == "completed"
        assert result["A"]["developer"] == "Dev-1"
        assert result["B"]["status"] == "pending"

    def test_increment_revision_count(self, tmp_path):
        """Test incrementing revision count atomically."""
        manager = StateManager(tmp_path / "coordination")

        # First increment
        count1 = manager.increment_revision_count("group_A")
        assert count1 == 1

        # Second increment
        count2 = manager.increment_revision_count("group_A")
        assert count2 == 2

        # Different group
        count3 = manager.increment_revision_count("group_B")
        assert count3 == 1

    def test_increment_revision_count_concurrent(self, tmp_path):
        """Test revision count increments are atomic under concurrency."""
        manager = StateManager(tmp_path / "coordination")

        errors = []
        results = []

        def increment_multiple_times(thread_id):
            """Increment revision count 5 times."""
            try:
                for _ in range(5):
                    count = manager.increment_revision_count("concurrent_group")
                    results.append((thread_id, count))
            except Exception as e:
                errors.append(e)

        # Run 3 threads concurrently
        threads = []
        for i in range(3):
            t = threading.Thread(target=increment_multiple_times, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0

        # Verify final count (3 threads * 5 increments = 15)
        final_count = manager.get_revision_count("concurrent_group")
        assert final_count == 15

        # Verify all increments were unique (no duplicate counts)
        counts = [count for _, count in results]
        assert len(counts) == len(set(counts)), \
            f"Duplicate revision counts detected: {counts}"

    def test_get_revision_count_nonexistent(self, tmp_path):
        """Test getting revision count for non-existent group returns 0."""
        manager = StateManager(tmp_path / "coordination")

        count = manager.get_revision_count("nonexistent_group")
        assert count == 0

    def test_state_persists_across_manager_instances(self, tmp_path):
        """Test state persists when creating new manager instances."""
        coord_dir = tmp_path / "coordination"

        # Write with first manager instance
        manager1 = StateManager(coord_dir)
        manager1.write_state("persistent.json", {"value": 42})

        # Read with second manager instance
        manager2 = StateManager(coord_dir)
        result = manager2.read_state("persistent.json")

        assert result["value"] == 42

    def test_nested_lock_same_file_deadlock_prevention(self, tmp_path):
        """
        Test that attempting to lock the same file twice in the same thread
        will block (this is expected behavior - don't nest locks on same file).

        Note: This test documents expected behavior, not a feature.
        """
        manager = StateManager(tmp_path / "coordination")

        with manager.lock_state("test.json", default_data={"count": 0}) as state:
            state["count"] = 1

            # This would block indefinitely in real usage
            # We just document that nested locks on same file should be avoided
            # Not actually testing it to avoid test hangs

        # Just verify the file was written correctly
        result = manager.read_state("test.json")
        assert result["count"] == 1
