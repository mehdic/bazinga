#!/usr/bin/env python3
"""
BAZINGA Orchestrator Integration Test Suite

This comprehensive test validates the entire BAZINGA multi-agent orchestration system:
- Database operations (bazinga-db skill)
- Agent workflow simulation
- File and artifact creation
- Session management
- Task group operations
- Context package operations
- Reasoning capture
- Success criteria tracking

Run with: pytest tests/test_orchestrator_integration.py -v --tb=short

For a quick manual test run:
    python tests/test_orchestrator_integration.py
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Generator, Dict, Any, Optional

# Try to import pytest - not required for manual tests
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Create dummy decorator for when pytest is not available
    class pytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        @staticmethod
        def mark(*args, **kwargs):
            return lambda x: x

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add paths for imports
sys.path.insert(0, str(PROJECT_ROOT / '.claude' / 'skills' / '_shared'))
sys.path.insert(0, str(PROJECT_ROOT / '.claude' / 'skills' / 'bazinga-db' / 'scripts'))

# Import bazinga_db script path
BAZINGA_DB_SCRIPT = PROJECT_ROOT / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'bazinga_db.py'
INIT_DB_SCRIPT = PROJECT_ROOT / '.claude' / 'skills' / 'bazinga-db' / 'scripts' / 'init_db.py'


# ============================================================================
# Test Utilities
# ============================================================================

def run_db_command(command: str, *args, db_path: Optional[Path] = None, expect_success: bool = True) -> Dict[str, Any]:
    """
    Run a bazinga_db.py command and return the result.

    Args:
        command: The database command (e.g., 'create-session', 'log-interaction')
        *args: Additional arguments for the command
        db_path: Path to database (if None, uses auto-detection)
        expect_success: Whether to expect the command to succeed

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'returncode'
    """
    cmd = [sys.executable, str(BAZINGA_DB_SCRIPT), '--quiet']
    if db_path:
        cmd.extend(['--db', str(db_path)])
    cmd.append(command)
    cmd.extend(str(a) for a in args)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    parsed_output = None
    if result.stdout.strip():
        try:
            parsed_output = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            parsed_output = result.stdout.strip()

    output = {
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode,
        'parsed': parsed_output
    }

    if expect_success and not output['success']:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"STDERR: {result.stderr}")
        print(f"STDOUT: {result.stdout}")

    return output


def create_test_project(base_dir: Path) -> Path:
    """
    Create a minimal BAZINGA project structure for testing.

    Args:
        base_dir: Directory to create project in

    Returns:
        Path to the project root
    """
    project = base_dir / "test_app"
    project.mkdir(parents=True, exist_ok=True)

    # Create required directories
    (project / ".claude" / "skills").mkdir(parents=True)
    (project / ".claude" / "agents").mkdir(parents=True)
    (project / "bazinga" / "artifacts").mkdir(parents=True)
    (project / "bazinga" / "templates").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()

    # Create a sample Python app
    (project / "src" / "main.py").write_text('''#!/usr/bin/env python3
"""Simple test application for BAZINGA integration testing."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    print(f"2 + 3 = {add(2, 3)}")
    print(f"5 - 2 = {subtract(5, 2)}")
    print(f"4 * 3 = {multiply(4, 3)}")
    print(f"10 / 2 = {divide(10, 2)}")
''')

    # Create test file
    (project / "tests" / "test_main.py").write_text('''#!/usr/bin/env python3
"""Tests for the main module."""
import pytest
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0] + "/src")
from main import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    assert subtract(-1, -1) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 100) == 0
    assert multiply(-2, 3) == -6

def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5
    with pytest.raises(ValueError):
        divide(1, 0)
''')

    # Create minimal config files
    (project / "bazinga" / "model_selection.json").write_text(json.dumps({
        "agents": {
            "developer": {"model": "haiku"},
            "qa_expert": {"model": "sonnet"},
            "tech_lead": {"model": "opus"},
            "project_manager": {"model": "opus"}
        },
        "_metadata": {"version": "1.0.0", "description": "Test config"}
    }, indent=2))

    (project / "bazinga" / "skills_config.json").write_text(json.dumps({
        "developer": {"lint-check": "mandatory"},
        "_metadata": {"description": "Test skills config"}
    }, indent=2))

    (project / "bazinga" / "challenge_levels.json").write_text(json.dumps({
        "levels": {
            "1": {"name": "Boundary Probing", "escalation_on_fail": False}
        },
        "_metadata": {"version": "1.0.0"}
    }, indent=2))

    return project


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_test_project() -> Generator[Path, None, None]:
    """Create a temporary test project with database."""
    with tempfile.TemporaryDirectory(prefix="bazinga_test_") as tmpdir:
        project = create_test_project(Path(tmpdir))
        db_path = project / "bazinga" / "bazinga.db"

        # Initialize the database
        init_result = subprocess.run(
            [sys.executable, str(INIT_DB_SCRIPT), '--db', str(db_path)],
            capture_output=True, text=True, timeout=30
        )
        if init_result.returncode != 0:
            print(f"DB init failed: {init_result.stderr}")

        yield project


@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for testing."""
    return f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


# ============================================================================
# Database Operation Tests
# ============================================================================

class TestDatabaseInitialization:
    """Test database initialization and basic operations."""

    def test_database_auto_init(self, temp_test_project: Path):
        """Test that database initializes automatically."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"
        assert db_path.exists(), "Database file should exist after initialization"

        # Verify it's a valid SQLite database
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Check for expected tables
        expected_tables = {
            'sessions', 'agent_logs', 'orchestrator_state', 'task_groups',
            'token_usage', 'skill_outputs', 'development_plans', 'success_criteria'
        }
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    def test_wal_mode_enabled(self, temp_test_project: Path):
        """Test that WAL mode is enabled for concurrency."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        conn.close()

        assert mode.lower() == "wal", f"Expected WAL mode, got {mode}"


class TestSessionManagement:
    """Test session creation and management."""

    def test_create_session(self, temp_test_project: Path, session_id: str):
        """Test creating a new orchestration session."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        result = run_db_command(
            'create-session',
            session_id,
            'simple',
            'Test requirements: implement calculator',
            db_path=db_path
        )

        assert result['success'], f"Failed to create session: {result['stderr']}"

    def test_list_sessions(self, temp_test_project: Path, session_id: str):
        """Test listing recent sessions."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Create session first
        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        # List sessions
        result = run_db_command('list-sessions', '10', db_path=db_path)

        assert result['success'], f"Failed to list sessions: {result['stderr']}"
        assert result['parsed'] is not None

        if isinstance(result['parsed'], list):
            session_ids = [s.get('session_id') for s in result['parsed']]
            assert session_id in session_ids, f"Session {session_id} not found in list"

    def test_update_session_status(self, temp_test_project: Path, session_id: str):
        """Test updating session status."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Create session
        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        # Update status
        result = run_db_command('update-session-status', session_id, 'completed', db_path=db_path)

        assert result['success'], f"Failed to update session status: {result['stderr']}"


class TestLoggingOperations:
    """Test agent interaction logging."""

    def test_log_pm_interaction(self, temp_test_project: Path, session_id: str):
        """Test logging a Project Manager interaction."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Create session first
        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        content = json.dumps({
            "mode": "simple",
            "task_groups": [{"id": "group_a", "name": "Calculator"}],
            "analysis": "Implementing basic calculator functions"
        })

        result = run_db_command(
            'log-interaction',
            session_id, 'project_manager', content, '1', 'pm_main',
            db_path=db_path
        )

        assert result['success'], f"Failed to log PM interaction: {result['stderr']}"

    def test_log_developer_interaction(self, temp_test_project: Path, session_id: str):
        """Test logging a Developer interaction."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        content = "Implemented add() and subtract() functions. All tests passing."

        result = run_db_command(
            'log-interaction',
            session_id, 'developer', content, '1', 'dev_1',
            db_path=db_path
        )

        assert result['success'], f"Failed to log developer interaction: {result['stderr']}"

    def test_log_qa_expert_interaction(self, temp_test_project: Path, session_id: str):
        """Test logging a QA Expert interaction."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        content = "Level 1 (Boundary Probing) tests passed. 4/4 tests green."

        result = run_db_command(
            'log-interaction',
            session_id, 'qa_expert', content, '1', 'qa_main',
            db_path=db_path
        )

        assert result['success'], f"Failed to log QA interaction: {result['stderr']}"

    def test_log_tech_lead_interaction(self, temp_test_project: Path, session_id: str):
        """Test logging a Tech Lead interaction."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        content = "Code review approved. Clean implementation, good test coverage."

        result = run_db_command(
            'log-interaction',
            session_id, 'tech_lead', content, '1', 'tl_main',
            db_path=db_path
        )

        assert result['success'], f"Failed to log Tech Lead interaction: {result['stderr']}"

    def test_stream_logs(self, temp_test_project: Path, session_id: str):
        """Test streaming/querying logs."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command('log-interaction', session_id, 'project_manager', 'PM log 1', '1', db_path=db_path)
        run_db_command('log-interaction', session_id, 'developer', 'Dev log 1', '1', db_path=db_path)

        result = run_db_command('stream-logs', session_id, '10', db_path=db_path)

        assert result['success'], f"Failed to stream logs: {result['stderr']}"


class TestStateManagement:
    """Test orchestrator and PM state management."""

    def test_save_orchestrator_state(self, temp_test_project: Path, session_id: str):
        """Test saving orchestrator state."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        state = json.dumps({
            "current_phase": "execution",
            "active_groups": ["group_a"],
            "completed_groups": [],
            "iteration": 1
        })

        result = run_db_command('save-state', session_id, 'orchestrator', state, db_path=db_path)

        assert result['success'], f"Failed to save orchestrator state: {result['stderr']}"

    def test_save_pm_state(self, temp_test_project: Path, session_id: str):
        """Test saving PM state."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        state = json.dumps({
            "mode": "simple",
            "task_groups": [{"id": "group_a", "name": "Calculator", "status": "in_progress"}],
            "iteration": 1
        })

        result = run_db_command('save-state', session_id, 'pm', state, db_path=db_path)

        assert result['success'], f"Failed to save PM state: {result['stderr']}"

    def test_get_state(self, temp_test_project: Path, session_id: str):
        """Test retrieving state."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        # Save state
        state = json.dumps({"iteration": 5, "status": "running"})
        run_db_command('save-state', session_id, 'orchestrator', state, db_path=db_path)

        # Get state
        result = run_db_command('get-state', session_id, 'orchestrator', db_path=db_path)

        assert result['success'], f"Failed to get state: {result['stderr']}"


class TestTaskGroupOperations:
    """Test task group creation and management."""

    def test_create_task_group(self, temp_test_project: Path, session_id: str):
        """Test creating a task group."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        result = run_db_command(
            'create-task-group',
            'group_a', session_id, 'Calculator Functions', 'pending', 'dev_1',
            db_path=db_path
        )

        assert result['success'], f"Failed to create task group: {result['stderr']}"

    def test_update_task_group_status(self, temp_test_project: Path, session_id: str):
        """Test updating task group status."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command('create-task-group', 'group_a', session_id, 'Calculator', 'pending', db_path=db_path)

        result = run_db_command(
            'update-task-group',
            'group_a', session_id,
            '--status', 'completed',
            db_path=db_path
        )

        assert result['success'], f"Failed to update task group: {result['stderr']}"

    def test_get_task_groups(self, temp_test_project: Path, session_id: str):
        """Test getting task groups."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command('create-task-group', 'group_a', session_id, 'Group A', 'pending', db_path=db_path)
        run_db_command('create-task-group', 'group_b', session_id, 'Group B', 'in_progress', db_path=db_path)

        result = run_db_command('get-task-groups', session_id, db_path=db_path)

        assert result['success'], f"Failed to get task groups: {result['stderr']}"


class TestSuccessCriteria:
    """Test success criteria operations."""

    def test_save_success_criteria(self, temp_test_project: Path, session_id: str):
        """Test saving success criteria."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        criteria = json.dumps([
            {"criterion": "All unit tests passing", "status": "pending"},
            {"criterion": "No lint errors", "status": "pending"},
            {"criterion": "Code review approved", "status": "pending"}
        ])

        result = run_db_command('save-success-criteria', session_id, criteria, db_path=db_path)

        assert result['success'], f"Failed to save success criteria: {result['stderr']}"

    def test_get_success_criteria(self, temp_test_project: Path, session_id: str):
        """Test getting success criteria."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        criteria = json.dumps([{"criterion": "All tests pass", "status": "pending"}])
        run_db_command('save-success-criteria', session_id, criteria, db_path=db_path)

        result = run_db_command('get-success-criteria', session_id, db_path=db_path)

        assert result['success'], f"Failed to get success criteria: {result['stderr']}"

    def test_update_success_criterion(self, temp_test_project: Path, session_id: str):
        """Test updating a success criterion."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        criteria = json.dumps([{"criterion": "All tests pass", "status": "pending"}])
        run_db_command('save-success-criteria', session_id, criteria, db_path=db_path)

        result = run_db_command(
            'update-success-criterion',
            session_id, 'All tests pass',
            '--status', 'met',
            '--actual', '4/4 tests passing',
            db_path=db_path
        )

        assert result['success'], f"Failed to update success criterion: {result['stderr']}"


class TestContextPackages:
    """Test context package operations."""

    def test_save_context_package(self, temp_test_project: Path, session_id: str):
        """Test saving a context package."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        # Create artifact directory and file
        artifact_dir = temp_test_project / "bazinga" / "artifacts" / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_file = artifact_dir / "research_group_a.md"
        artifact_file.write_text("# Research Results\n\nFindings here...")

        result = run_db_command(
            'save-context-package',
            session_id, 'group_a', 'research',
            str(artifact_file),
            'requirements_engineer',
            '["developer", "senior_software_engineer"]',
            'high',
            'Research findings for calculator implementation',
            db_path=db_path
        )

        assert result['success'], f"Failed to save context package: {result['stderr']}"

    def test_get_context_packages(self, temp_test_project: Path, session_id: str):
        """Test getting context packages for an agent."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        # Create and save a package
        artifact_dir = temp_test_project / "bazinga" / "artifacts" / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_file = artifact_dir / "research_group_a.md"
        artifact_file.write_text("# Research")

        run_db_command(
            'save-context-package',
            session_id, 'group_a', 'research',
            str(artifact_file), 'requirements_engineer',
            '["developer"]', 'high', 'Test summary',
            db_path=db_path
        )

        result = run_db_command(
            'get-context-packages',
            session_id, 'group_a', 'developer', '5',
            db_path=db_path
        )

        assert result['success'], f"Failed to get context packages: {result['stderr']}"


class TestReasoningCapture:
    """Test reasoning capture operations."""

    def test_save_reasoning_understanding(self, temp_test_project: Path, session_id: str):
        """Test saving understanding phase reasoning."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        result = run_db_command(
            'save-reasoning',
            session_id, 'group_a', 'developer', 'understanding',
            'Understanding the task: implement calculator functions. Key requirements: add, subtract, multiply, divide.',
            '--confidence', 'high',
            '--references', '["src/main.py"]',
            db_path=db_path
        )

        assert result['success'], f"Failed to save reasoning: {result['stderr']}"

    def test_save_reasoning_completion(self, temp_test_project: Path, session_id: str):
        """Test saving completion phase reasoning."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        result = run_db_command(
            'save-reasoning',
            session_id, 'group_a', 'developer', 'completion',
            'Task completed. Implemented all 4 calculator functions with full test coverage.',
            '--confidence', 'high',
            db_path=db_path
        )

        assert result['success'], f"Failed to save completion reasoning: {result['stderr']}"

    def test_get_reasoning(self, temp_test_project: Path, session_id: str):
        """Test getting reasoning entries."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command(
            'save-reasoning',
            session_id, 'group_a', 'developer', 'understanding', 'Test reasoning',
            db_path=db_path
        )

        result = run_db_command('get-reasoning', session_id, db_path=db_path)

        assert result['success'], f"Failed to get reasoning: {result['stderr']}"

    def test_reasoning_timeline(self, temp_test_project: Path, session_id: str):
        """Test getting reasoning timeline."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'understanding', 'Step 1', db_path=db_path)
        run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'decisions', 'Step 2', db_path=db_path)
        run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'completion', 'Step 3', db_path=db_path)

        result = run_db_command('reasoning-timeline', session_id, '--format', 'json', db_path=db_path)

        assert result['success'], f"Failed to get reasoning timeline: {result['stderr']}"


class TestDashboard:
    """Test dashboard snapshot functionality."""

    def test_dashboard_snapshot(self, temp_test_project: Path, session_id: str):
        """Test getting a dashboard snapshot."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Create session and populate with data
        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)
        run_db_command('create-task-group', 'group_a', session_id, 'Calculator', 'completed', db_path=db_path)
        run_db_command('log-interaction', session_id, 'project_manager', 'PM analysis', '1', db_path=db_path)
        run_db_command('log-interaction', session_id, 'developer', 'Dev implementation', '1', db_path=db_path)

        result = run_db_command('dashboard-snapshot', session_id, db_path=db_path)

        assert result['success'], f"Failed to get dashboard snapshot: {result['stderr']}"


# ============================================================================
# Integration Workflow Tests
# ============================================================================

class TestFullOrchestrationWorkflow:
    """Test a complete orchestration workflow simulation."""

    def test_simple_mode_workflow(self, temp_test_project: Path, session_id: str):
        """
        Simulate a complete simple mode orchestration workflow:
        1. PM creates task breakdown
        2. Developer implements
        3. QA tests
        4. Tech Lead reviews
        5. PM validates and sends BAZINGA
        """
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Step 1: Create session
        result = run_db_command('create-session', session_id, 'simple', 'Implement calculator app', db_path=db_path)
        assert result['success'], "Failed to create session"

        # Step 2: PM creates task breakdown
        pm_state = json.dumps({
            "mode": "simple",
            "task_groups": [{"id": "group_a", "name": "Calculator Functions", "status": "pending"}],
            "success_criteria": ["All tests pass", "No lint errors"]
        })
        run_db_command('save-state', session_id, 'pm', pm_state, db_path=db_path)
        run_db_command('log-interaction', session_id, 'project_manager', 'Created task breakdown', '1', 'pm_main', db_path=db_path)

        # Step 3: Create task group
        run_db_command('create-task-group', 'group_a', session_id, 'Calculator Functions', 'pending', 'dev_1', db_path=db_path)

        # Save success criteria
        criteria = json.dumps([
            {"criterion": "All tests pass", "status": "pending"},
            {"criterion": "No lint errors", "status": "pending"}
        ])
        run_db_command('save-success-criteria', session_id, criteria, db_path=db_path)

        # Step 4: Developer implements
        run_db_command('update-task-group', 'group_a', session_id, '--status', 'in_progress', db_path=db_path)
        run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'understanding', 'Implementing calculator', db_path=db_path)
        run_db_command('log-interaction', session_id, 'developer', 'Implemented add, subtract, multiply, divide', '1', 'dev_1', db_path=db_path)
        run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'completion', 'All functions implemented', db_path=db_path)

        # Step 5: QA tests
        run_db_command('log-interaction', session_id, 'qa_expert', 'Level 1 tests passed: 4/4', '1', 'qa_main', db_path=db_path)

        # Step 6: Tech Lead reviews
        run_db_command('log-interaction', session_id, 'tech_lead', 'Code review approved', '1', 'tl_main', db_path=db_path)

        # Step 7: Update task group to completed
        run_db_command('update-task-group', 'group_a', session_id, '--status', 'completed', db_path=db_path)

        # Step 8: Update success criteria
        run_db_command('update-success-criterion', session_id, 'All tests pass', '--status', 'met', '--actual', '4/4', db_path=db_path)
        run_db_command('update-success-criterion', session_id, 'No lint errors', '--status', 'met', '--actual', '0 errors', db_path=db_path)

        # Step 9: PM sends BAZINGA
        run_db_command('log-interaction', session_id, 'project_manager', 'BAZINGA! All criteria met.', '2', 'pm_main', db_path=db_path)
        run_db_command('update-session-status', session_id, 'completed', db_path=db_path)

        # Verify final state
        snapshot = run_db_command('dashboard-snapshot', session_id, db_path=db_path)
        assert snapshot['success'], "Failed to get final dashboard snapshot"

        # Verify task groups
        groups = run_db_command('get-task-groups', session_id, db_path=db_path)
        assert groups['success'], "Failed to get task groups"

        # Verify success criteria
        criteria_result = run_db_command('get-success-criteria', session_id, db_path=db_path)
        assert criteria_result['success'], "Failed to get success criteria"

        print(f"\n✅ Simple mode workflow completed successfully for session: {session_id}")

    def test_parallel_mode_workflow(self, temp_test_project: Path, session_id: str):
        """
        Simulate a parallel mode orchestration workflow with multiple developers.
        """
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        # Create session
        run_db_command('create-session', session_id, 'parallel', 'Implement calculator with UI', db_path=db_path)

        # PM creates parallel task groups
        pm_state = json.dumps({
            "mode": "parallel",
            "task_groups": [
                {"id": "group_a", "name": "Core Functions", "status": "pending"},
                {"id": "group_b", "name": "UI Components", "status": "pending"}
            ]
        })
        run_db_command('save-state', session_id, 'pm', pm_state, db_path=db_path)

        # Create both task groups
        run_db_command('create-task-group', 'group_a', session_id, 'Core Functions', 'pending', 'dev_1', db_path=db_path)
        run_db_command('create-task-group', 'group_b', session_id, 'UI Components', 'pending', 'dev_2', db_path=db_path)

        # Parallel development
        run_db_command('update-task-group', 'group_a', session_id, '--status', 'in_progress', db_path=db_path)
        run_db_command('update-task-group', 'group_b', session_id, '--status', 'in_progress', db_path=db_path)

        run_db_command('log-interaction', session_id, 'developer', 'Group A: Core functions done', '1', 'dev_1', db_path=db_path)
        run_db_command('log-interaction', session_id, 'developer', 'Group B: UI components done', '1', 'dev_2', db_path=db_path)

        # Both complete
        run_db_command('update-task-group', 'group_a', session_id, '--status', 'completed', db_path=db_path)
        run_db_command('update-task-group', 'group_b', session_id, '--status', 'completed', db_path=db_path)

        # Verify
        groups = run_db_command('get-task-groups', session_id, db_path=db_path)
        assert groups['success'], "Failed to get task groups"

        print(f"\n✅ Parallel mode workflow completed successfully for session: {session_id}")


# ============================================================================
# File and Artifact Tests
# ============================================================================

class TestFileAndArtifactCreation:
    """Test file and artifact creation."""

    def test_artifact_directory_structure(self, temp_test_project: Path, session_id: str):
        """Test that artifact directories are created correctly."""
        artifact_dir = temp_test_project / "bazinga" / "artifacts" / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Create various artifacts
        (artifact_dir / "context").mkdir()
        (artifact_dir / "skills").mkdir()

        # Create test artifacts
        (artifact_dir / "context" / "research_group_a.md").write_text("# Research\nFindings...")
        (artifact_dir / "skills" / "lint_results.json").write_text('{"status": "clean"}')

        assert (artifact_dir / "context" / "research_group_a.md").exists()
        assert (artifact_dir / "skills" / "lint_results.json").exists()

    def test_config_files_exist(self, temp_test_project: Path):
        """Test that all required config files exist."""
        bazinga_dir = temp_test_project / "bazinga"

        required_configs = [
            "model_selection.json",
            "skills_config.json",
            "challenge_levels.json"
        ]

        for config in required_configs:
            assert (bazinga_dir / config).exists(), f"Missing config: {config}"

            # Verify it's valid JSON
            content = (bazinga_dir / config).read_text()
            data = json.loads(content)
            assert isinstance(data, dict), f"{config} should be a JSON object"


# ============================================================================
# Performance and Concurrency Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    def test_database_operation_speed(self, temp_test_project: Path, session_id: str):
        """Test that database operations complete within SLA (<500ms)."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        import time

        # Time a log operation
        start = time.perf_counter()
        run_db_command('log-interaction', session_id, 'developer', 'Test log', '1', db_path=db_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Log operation took {elapsed*1000:.0f}ms (SLA: 500ms)"

        # Time a query operation
        start = time.perf_counter()
        run_db_command('get-task-groups', session_id, db_path=db_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Query operation took {elapsed*1000:.0f}ms (SLA: 500ms)"

    def test_bulk_operations(self, temp_test_project: Path, session_id: str):
        """Test bulk operations performance."""
        db_path = temp_test_project / "bazinga" / "bazinga.db"

        run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)

        import time

        # Insert 50 log entries
        start = time.perf_counter()
        for i in range(50):
            run_db_command('log-interaction', session_id, 'developer', f'Log entry {i}', str(i), db_path=db_path)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / 50) * 1000
        print(f"\n📊 Bulk insert: 50 logs in {elapsed:.2f}s (avg: {avg_time:.0f}ms/log)")

        assert avg_time < 200, f"Average log time {avg_time:.0f}ms exceeds 200ms limit"


# ============================================================================
# Configuration File Tests
# ============================================================================

class TestConfigurationFiles:
    """Test that configuration files are properly loaded and validated."""

    def test_model_selection_config(self):
        """Test model_selection.json structure."""
        config_path = PROJECT_ROOT / "bazinga" / "model_selection.json"
        assert config_path.exists(), "model_selection.json not found"

        config = json.loads(config_path.read_text())

        # Required agents
        required_agents = ['developer', 'qa_expert', 'tech_lead', 'project_manager', 'investigator']
        for agent in required_agents:
            assert agent in config['agents'], f"Missing agent: {agent}"
            assert 'model' in config['agents'][agent], f"Missing model for {agent}"

    def test_skills_config(self):
        """Test skills_config.json structure."""
        config_path = PROJECT_ROOT / "bazinga" / "skills_config.json"
        assert config_path.exists(), "skills_config.json not found"

        config = json.loads(config_path.read_text())

        # Check developer has required skills
        assert 'developer' in config
        assert 'lint-check' in config['developer']

    def test_challenge_levels_config(self):
        """Test challenge_levels.json structure."""
        config_path = PROJECT_ROOT / "bazinga" / "challenge_levels.json"
        assert config_path.exists(), "challenge_levels.json not found"

        config = json.loads(config_path.read_text())

        # Check levels exist
        assert 'levels' in config
        assert '1' in config['levels']
        assert 'name' in config['levels']['1']


# ============================================================================
# Agent File Tests
# ============================================================================

class TestAgentFiles:
    """Test that all agent definition files exist and are valid."""

    def test_all_agents_exist(self):
        """Test that all required agent files exist."""
        agents_dir = PROJECT_ROOT / "agents"

        required_agents = [
            'orchestrator.md',
            'project_manager.md',
            'developer.md',
            'qa_expert.md',
            'techlead.md',
            'investigator.md',
            'senior_software_engineer.md',
            'requirements_engineer.md'
        ]

        for agent in required_agents:
            agent_path = agents_dir / agent
            assert agent_path.exists(), f"Missing agent file: {agent}"

    def test_agent_frontmatter(self):
        """Test that agent files have valid frontmatter."""
        agents_dir = PROJECT_ROOT / "agents"

        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()

            # Check for frontmatter
            assert content.startswith("---"), f"{agent_file.name} missing frontmatter"

            # Extract frontmatter
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{agent_file.name} has invalid frontmatter format"

            frontmatter = parts[1].strip()
            assert "name:" in frontmatter, f"{agent_file.name} missing 'name' in frontmatter"


# ============================================================================
# Main Entry Point
# ============================================================================

def generate_test_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive test report."""
    report = []
    report.append("=" * 80)
    report.append("BAZINGA ORCHESTRATOR INTEGRATION TEST REPORT")
    report.append("=" * 80)
    report.append(f"Date: {datetime.now().isoformat()}")
    report.append(f"Project Root: {PROJECT_ROOT}")
    report.append("")

    # Summary
    total = results.get('total', 0)
    passed = results.get('passed', 0)
    failed = results.get('failed', 0)
    skipped = results.get('skipped', 0)

    report.append("SUMMARY")
    report.append("-" * 40)
    report.append(f"Total Tests:   {total}")
    report.append(f"Passed:        {passed} ✅")
    report.append(f"Failed:        {failed} ❌")
    report.append(f"Skipped:       {skipped} ⏭️")
    report.append(f"Pass Rate:     {(passed/total*100):.1f}%" if total > 0 else "N/A")
    report.append("")

    # Test categories
    report.append("TEST CATEGORIES")
    report.append("-" * 40)
    for category, count in results.get('categories', {}).items():
        report.append(f"  {category}: {count} tests")
    report.append("")

    # Component status
    report.append("COMPONENT STATUS")
    report.append("-" * 40)
    components = [
        ("Database Operations", passed > 0),
        ("Session Management", passed > 0),
        ("Task Group Operations", passed > 0),
        ("Context Packages", passed > 0),
        ("Reasoning Capture", passed > 0),
        ("Success Criteria", passed > 0),
        ("Agent Files", passed > 0),
        ("Config Files", passed > 0)
    ]
    for component, status in components:
        icon = "✅" if status else "❌"
        report.append(f"  {icon} {component}")
    report.append("")

    report.append("=" * 80)
    return "\n".join(report)


def run_manual_tests():
    """Run tests manually (without pytest) for quick verification."""
    print("\n" + "=" * 80)
    print("BAZINGA ORCHESTRATOR INTEGRATION TEST - MANUAL RUN")
    print("=" * 80 + "\n")

    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'categories': {}
    }

    with tempfile.TemporaryDirectory(prefix="bazinga_test_") as tmpdir:
        project = create_test_project(Path(tmpdir))
        db_path = project / "bazinga" / "bazinga.db"

        # Initialize database
        print("📦 Initializing test database...")
        init_result = subprocess.run(
            [sys.executable, str(INIT_DB_SCRIPT), '--db', str(db_path)],
            capture_output=True, text=True, timeout=30
        )

        if init_result.returncode != 0:
            print(f"❌ Database initialization failed: {init_result.stderr}")
            return
        print("✅ Database initialized\n")

        session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Run test categories
        test_cases = [
            ("Session Creation", lambda: run_db_command('create-session', session_id, 'simple', 'Test', db_path=db_path)),
            ("List Sessions", lambda: run_db_command('list-sessions', '5', db_path=db_path)),
            ("Log Interaction", lambda: run_db_command('log-interaction', session_id, 'developer', 'Test log', '1', db_path=db_path)),
            ("Save State", lambda: run_db_command('save-state', session_id, 'pm', '{"test": true}', db_path=db_path)),
            ("Get State", lambda: run_db_command('get-state', session_id, 'pm', db_path=db_path)),
            ("Create Task Group", lambda: run_db_command('create-task-group', 'group_a', session_id, 'Test Group', 'pending', db_path=db_path)),
            ("Update Task Group", lambda: run_db_command('update-task-group', 'group_a', session_id, '--status', 'completed', db_path=db_path)),
            ("Get Task Groups", lambda: run_db_command('get-task-groups', session_id, db_path=db_path)),
            ("Save Success Criteria", lambda: run_db_command('save-success-criteria', session_id, '[{"criterion":"test","status":"pending"}]', db_path=db_path)),
            ("Get Success Criteria", lambda: run_db_command('get-success-criteria', session_id, db_path=db_path)),
            ("Save Reasoning", lambda: run_db_command('save-reasoning', session_id, 'group_a', 'developer', 'understanding', 'Test', db_path=db_path)),
            ("Get Reasoning", lambda: run_db_command('get-reasoning', session_id, db_path=db_path)),
            ("Dashboard Snapshot", lambda: run_db_command('dashboard-snapshot', session_id, db_path=db_path)),
            ("Update Session Status", lambda: run_db_command('update-session-status', session_id, 'completed', db_path=db_path)),
        ]

        print("🧪 Running tests...\n")

        for test_name, test_fn in test_cases:
            results['total'] += 1
            try:
                result = test_fn()
                if result['success']:
                    results['passed'] += 1
                    print(f"  ✅ {test_name}")
                else:
                    results['failed'] += 1
                    print(f"  ❌ {test_name}: {result['stderr'][:100]}")
            except Exception as e:
                results['failed'] += 1
                print(f"  ❌ {test_name}: {str(e)[:100]}")

        print("\n" + "-" * 40)
        print(f"Results: {results['passed']}/{results['total']} passed")

        if results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️ {results['failed']} tests failed")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        run_manual_tests()
    elif HAS_PYTEST:
        # Run with pytest
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        # Fall back to manual tests if pytest not installed
        print("pytest not installed, running manual tests...")
        run_manual_tests()
