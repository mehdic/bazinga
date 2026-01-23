"""Tests for state backend implementations."""

import tempfile
from pathlib import Path
import json
import threading

import pytest

from bazinga.platform.interfaces import (
    SessionData,
    TaskGroupData,
    ReasoningData,
)
from bazinga.platform.state_backend.memory import InMemoryBackend
from bazinga.platform.state_backend.file import FileBackend
from bazinga.platform.state_backend.sqlite import SQLiteBackend


class TestInMemoryBackend:
    """Tests for InMemoryBackend."""

    def test_is_not_persistent(self):
        """InMemory backend should not be persistent."""
        backend = InMemoryBackend()
        assert backend.is_persistent() is False

    def test_does_not_support_transactions(self):
        """InMemory backend should not support transactions."""
        backend = InMemoryBackend()
        assert backend.supports_transactions() is False

    def test_create_session(self):
        """Should create session."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_test_001",
            mode="simple",
            requirements="Test requirements",
        )

        result = backend.create_session(session)

        assert result["success"] is True
        assert result["session_id"] == "bazinga_test_001"

    def test_create_session_duplicate(self):
        """Should fail on duplicate session."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_dup_001",
            mode="simple",
            requirements="Test requirements",
        )

        backend.create_session(session)
        result = backend.create_session(session)

        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_get_session(self):
        """Should retrieve session."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_get_001",
            mode="parallel",
            requirements="Test requirements",
        )
        backend.create_session(session)

        retrieved = backend.get_session("bazinga_get_001")

        assert retrieved is not None
        assert retrieved.session_id == "bazinga_get_001"
        assert retrieved.mode == "parallel"

    def test_get_session_not_found(self):
        """Should return None for nonexistent session."""
        backend = InMemoryBackend()
        result = backend.get_session("nonexistent")
        assert result is None

    def test_update_session(self):
        """Should update session."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_upd_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        result = backend.update_session("bazinga_upd_001", {"status": "completed"})

        assert result["success"] is True
        updated = backend.get_session("bazinga_upd_001")
        assert updated.status == "completed"

    def test_create_task_group(self):
        """Should create task group."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_tg_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        group = TaskGroupData(
            group_id="AUTH",
            session_id="bazinga_tg_001",
            name="Authentication",
        )
        result = backend.create_task_group(group)

        assert result["success"] is True
        assert result["group_id"] == "AUTH"

    def test_get_task_groups(self):
        """Should retrieve task groups."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_gtg_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        backend.create_task_group(
            TaskGroupData(
                group_id="AUTH",
                session_id="bazinga_gtg_001",
                name="Authentication",
            )
        )
        backend.create_task_group(
            TaskGroupData(
                group_id="API",
                session_id="bazinga_gtg_001",
                name="API Integration",
            )
        )

        groups = backend.get_task_groups("bazinga_gtg_001")

        assert len(groups) == 2
        group_ids = [g.group_id for g in groups]
        assert "AUTH" in group_ids
        assert "API" in group_ids

    def test_log_interaction(self):
        """Should log interaction."""
        backend = InMemoryBackend()

        result = backend.log_interaction(
            session_id="bazinga_log_001",
            agent_type="developer",
            content="Implementation complete",
        )

        assert result["success"] is True
        assert "log_id" in result

    def test_save_reasoning(self):
        """Should save reasoning."""
        backend = InMemoryBackend()

        reasoning = ReasoningData(
            session_id="bazinga_reason_001",
            group_id="AUTH",
            agent_type="developer",
            phase="understanding",
            content="Analyzing requirements...",
        )
        result = backend.save_reasoning(reasoning)

        assert result["success"] is True

    def test_get_reasoning(self):
        """Should retrieve reasoning with filters."""
        backend = InMemoryBackend()

        # Save multiple reasoning entries
        for phase in ["understanding", "completion"]:
            backend.save_reasoning(
                ReasoningData(
                    session_id="bazinga_getr_001",
                    group_id="AUTH",
                    agent_type="developer",
                    phase=phase,
                    content=f"Phase: {phase}",
                )
            )

        # Get all for session
        all_reasoning = backend.get_reasoning("bazinga_getr_001")
        assert len(all_reasoning) == 2

        # Filter by phase
        understanding = backend.get_reasoning(
            "bazinga_getr_001", phase="understanding"
        )
        assert len(understanding) == 1

    def test_clear(self):
        """Should clear all data."""
        backend = InMemoryBackend()
        session = SessionData(
            session_id="bazinga_clear_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        backend.clear()

        assert backend.get_session("bazinga_clear_001") is None

    def test_thread_safety(self):
        """Should be thread-safe."""
        backend = InMemoryBackend()
        errors = []

        def create_sessions(start_idx):
            try:
                for i in range(10):
                    session = SessionData(
                        session_id=f"bazinga_thread_{start_idx}_{i}",
                        mode="simple",
                        requirements="Test requirements",
                    )
                    backend.create_session(session)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=create_sessions, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestFileBackend:
    """Tests for FileBackend."""

    def test_is_persistent(self):
        """File backend should be persistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))
            assert backend.is_persistent() is True

    def test_does_not_support_transactions(self):
        """File backend should not support transactions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))
            assert backend.supports_transactions() is False

    def test_creates_directories(self):
        """Should create necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "state"
            backend = FileBackend(base_dir=base_dir)

            # Verify backend was created with correct base_dir
            assert backend.is_persistent() is True
            assert (base_dir / "sessions").exists()
            assert (base_dir / "interactions").exists()
            assert (base_dir / "reasoning").exists()

    def test_create_and_get_session(self):
        """Should persist session to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))

            session = SessionData(
                session_id="bazinga_file_001",
                mode="parallel",
                requirements="File test",
            )
            backend.create_session(session)

            # Verify file exists
            session_file = Path(tmpdir) / "sessions" / "bazinga_file_001.json"
            assert session_file.exists()

            # Retrieve
            retrieved = backend.get_session("bazinga_file_001")
            assert retrieved.mode == "parallel"

    def test_atomic_write(self):
        """Write should be atomic (using temp file)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))

            session = SessionData(
                session_id="bazinga_atomic_001",
                mode="simple",
                requirements="Test requirements",
            )
            backend.create_session(session)

            # Update should not leave temp files
            backend.update_session("bazinga_atomic_001", {"status": "completed"})

            # No .tmp files should remain
            tmp_files = list(Path(tmpdir).rglob("*.tmp"))
            assert len(tmp_files) == 0

    def test_task_group_in_session_file(self):
        """Task groups should be stored in session file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))

            session = SessionData(
                session_id="bazinga_tgf_001",
                mode="simple",
                requirements="Test requirements",
            )
            backend.create_session(session)

            group = TaskGroupData(
                group_id="AUTH",
                session_id="bazinga_tgf_001",
                name="Authentication",
            )
            backend.create_task_group(group)

            # Read raw file
            session_file = Path(tmpdir) / "sessions" / "bazinga_tgf_001.json"
            data = json.loads(session_file.read_text())

            assert "task_groups" in data
            assert "AUTH" in data["task_groups"]

    def test_reasoning_separate_file(self):
        """Reasoning should be in separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_dir=Path(tmpdir))

            reasoning = ReasoningData(
                session_id="bazinga_rf_001",
                group_id="AUTH",
                agent_type="developer",
                phase="understanding",
                content="Test content",
            )
            backend.save_reasoning(reasoning)

            # Check file
            reasoning_file = Path(tmpdir) / "reasoning" / "bazinga_rf_001.json"
            assert reasoning_file.exists()


class TestSQLiteBackend:
    """Tests for SQLiteBackend."""

    def test_is_persistent(self):
        """SQLite backend should be persistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = SQLiteBackend(
                db_path=Path(tmpdir) / "test.db",
                project_root=Path(tmpdir),
            )
            assert backend.is_persistent() is True

    def test_supports_transactions(self):
        """SQLite backend should support transactions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = SQLiteBackend(
                db_path=Path(tmpdir) / "test.db",
                project_root=Path(tmpdir),
            )
            assert backend.supports_transactions() is True

    # Note: Full SQLite tests require bazinga_db.py to be available
    # These tests verify the interface contract


class TestBackendValidation:
    """Tests for input validation across backends."""

    @pytest.fixture(params=["memory", "file"])
    def backend(self, request, tmp_path):
        """Fixture providing different backends."""
        if request.param == "memory":
            return InMemoryBackend()
        elif request.param == "file":
            return FileBackend(base_dir=tmp_path / "state")

    def test_session_id_validation_empty(self, backend):
        """Should reject empty session_id."""
        session = SessionData(
            session_id="",
            mode="simple",
            requirements="Test requirements",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            backend.create_session(session)

    def test_session_id_validation_prefix(self, backend):
        """Should require bazinga_ prefix."""
        session = SessionData(
            session_id="invalid_id",
            mode="simple",
            requirements="Test requirements",
        )

        with pytest.raises(ValueError, match="must start with"):
            backend.create_session(session)

    def test_group_id_validation_empty(self, backend):
        """Should reject empty group_id."""
        # First create session
        session = SessionData(
            session_id="bazinga_val_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        group = TaskGroupData(
            group_id="",
            session_id="bazinga_val_001",
            name="Test Group",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            backend.create_task_group(group)

    def test_group_id_validation_characters(self, backend):
        """Should reject invalid characters in group_id."""
        session = SessionData(
            session_id="bazinga_val_002",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        group = TaskGroupData(
            group_id="invalid@id!",
            session_id="bazinga_val_002",
            name="Test Group",
        )

        with pytest.raises(ValueError, match="alphanumeric"):
            backend.create_task_group(group)


class TestBackendDashboard:
    """Tests for dashboard snapshot functionality."""

    def test_dashboard_snapshot_memory(self):
        """InMemoryBackend should provide dashboard snapshot."""
        backend = InMemoryBackend()

        # Setup data
        session = SessionData(
            session_id="bazinga_dash_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)
        backend.create_task_group(
            TaskGroupData(
                group_id="AUTH",
                session_id="bazinga_dash_001",
                name="Authentication",
            )
        )
        backend.log_interaction("bazinga_dash_001", "developer", "Test")
        backend.save_reasoning(
            ReasoningData(
                session_id="bazinga_dash_001",
                group_id="AUTH",
                agent_type="developer",
                phase="understanding",
                content="Test",
            )
        )

        snapshot = backend.get_dashboard_snapshot("bazinga_dash_001")

        assert "session" in snapshot
        assert "task_groups" in snapshot
        assert "interactions" in snapshot
        assert "reasoning" in snapshot

    def test_dashboard_snapshot_file(self, tmp_path):
        """FileBackend should provide dashboard snapshot."""
        backend = FileBackend(base_dir=tmp_path / "state")

        session = SessionData(
            session_id="bazinga_dashf_001",
            mode="simple",
            requirements="Test requirements",
        )
        backend.create_session(session)

        snapshot = backend.get_dashboard_snapshot("bazinga_dashf_001")

        assert "session" in snapshot

    def test_dashboard_snapshot_not_found(self):
        """Should return error for nonexistent session."""
        backend = InMemoryBackend()

        snapshot = backend.get_dashboard_snapshot("nonexistent")

        assert "error" in snapshot
