#!/usr/bin/env python3
"""
Comprehensive test suite for prompt_builder.py script.

Tests the deterministic prompt building workflow:
- Database requirement enforcement
- Argument parsing and sanitization
- Path resolution from project root
- Agent file reading and validation
- Output format and error handling
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# Path to the prompt_builder.py script
SCRIPT_PATH = Path(__file__).parent.parent / ".claude" / "skills" / "prompt-builder" / "scripts" / "prompt_builder.py"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """Create a temporary project directory with required structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create minimal project structure
        (project_root / ".claude").mkdir()
        (project_root / "bazinga").mkdir()
        (project_root / "agents").mkdir()
        (project_root / "bazinga" / "templates" / "specializations").mkdir(parents=True)

        # Create a minimal agent file
        agent_content = """# Developer Agent

## Role
You are a Developer in a BAZINGA multi-agent team.

## Your Task
Implement the assigned task.

## Key Rules
- READY_FOR_QA when done
- NO DELEGATION

## Workflow
1. Read requirements
2. Implement solution
3. Run tests
4. Report status

""" + "# Additional content\n" * 200  # Pad to meet minimum line count

        (project_root / "agents" / "developer.md").write_text(agent_content)
        (project_root / "agents" / "project_manager.md").write_text(agent_content)
        (project_root / "agents" / "qa_expert.md").write_text(agent_content)
        (project_root / "agents" / "tech_lead.md").write_text(agent_content)
        (project_root / "agents" / "senior_software_engineer.md").write_text(agent_content)
        (project_root / "agents" / "investigator.md").write_text(agent_content)
        (project_root / "agents" / "requirements_engineer.md").write_text(agent_content)

        yield project_root


@pytest.fixture
def temp_project_with_db(temp_project: Path) -> Generator[Path, None, None]:
    """Create a temporary project with initialized database."""
    db_path = temp_project / "bazinga" / "bazinga.db"

    # Create minimal database schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables needed by prompt_builder
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS task_groups (
            id TEXT,
            session_id TEXT,
            name TEXT,
            status TEXT DEFAULT 'pending',
            specializations TEXT,
            PRIMARY KEY (session_id, id)
        );

        CREATE TABLE IF NOT EXISTS context_packages (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            group_id TEXT,
            file_path TEXT,
            priority TEXT,
            summary TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS error_patterns (
            id INTEGER PRIMARY KEY,
            signature_json TEXT,
            solution TEXT,
            confidence REAL,
            occurrences INTEGER
        );

        CREATE TABLE IF NOT EXISTS orchestration_logs (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            group_id TEXT,
            agent_type TEXT,
            log_type TEXT,
            reasoning_phase TEXT,
            content TEXT,
            confidence_level REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_markers (
            agent_type TEXT PRIMARY KEY,
            required_markers TEXT
        );
    """)

    # Insert test session
    cursor.execute("""
        INSERT INTO sessions (session_id, status)
        VALUES ('test_session_123', 'active')
    """)

    # Insert test task group
    cursor.execute("""
        INSERT INTO task_groups (id, session_id, name, status, specializations)
        VALUES ('TEST_GROUP', 'test_session_123', 'Test Task', 'pending', '[]')
    """)

    conn.commit()
    conn.close()

    yield temp_project


def run_script(args: list, cwd: Path = None, env: dict = None) -> tuple:
    """Run the prompt_builder.py script and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT_PATH)] + args

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=full_env,
    )

    return result.returncode, result.stdout, result.stderr


# ============================================================================
# Test: Database Requirement Enforcement
# ============================================================================

class TestDatabaseRequirement:
    """Tests for database existence enforcement."""

    def test_fails_without_database(self, temp_project: Path):
        """Script should fail if database doesn't exist (default behavior)."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project / "bazinga" / "nonexistent.db"),
        ], cwd=temp_project)

        assert returncode == 1
        assert "ERROR: Database not found" in stderr
        assert "Deterministic orchestration requires database" in stderr
        assert stdout == ""  # No prompt should be emitted

    def test_allows_no_db_with_flag(self, temp_project: Path):
        """Script should allow missing DB when --allow-no-db is specified."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--allow-no-db",
            "--project-root", str(temp_project),
            "--db", str(temp_project / "bazinga" / "nonexistent.db"),
        ], cwd=temp_project)

        assert returncode == 0
        assert "WARNING: Database not found" in stderr
        assert "--allow-no-db" in stderr
        # Agent content from temp project
        assert "Developer Agent" in stdout or "developer" in stdout.lower()

    def test_works_with_valid_database(self, temp_project_with_db: Path):
        """Script should work normally with valid database."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_session_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--group-id", "TEST_GROUP",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        assert "[PROMPT_METADATA]" in stderr
        assert "agent_type=developer" in stderr
        # Prompt should be emitted
        assert len(stdout) > 100


# ============================================================================
# Test: Argument Parsing
# ============================================================================

class TestArgumentParsing:
    """Tests for argument parsing and sanitization."""

    def test_required_arguments_enforced(self, temp_project_with_db: Path):
        """Script should fail if required arguments are missing."""
        # Missing --agent-type
        returncode, stdout, stderr = run_script([
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
        ], cwd=temp_project_with_db)

        assert returncode != 0
        assert "required" in stderr.lower() or "agent-type" in stderr.lower()

    def test_invalid_agent_type_rejected(self, temp_project_with_db: Path):
        """Script should reject invalid agent types."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "invalid_agent",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode != 0
        assert "invalid" in stderr.lower() or "choice" in stderr.lower()

    def test_debug_flag_outputs_diagnostics(self, temp_project_with_db: Path):
        """Debug flag should print argument diagnostics."""
        returncode, stdout, stderr = run_script([
            "--debug",
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        assert "[DEBUG]" in stderr
        assert "sys.argv" in stderr or "Parsed args" in stderr

    def test_empty_args_sanitized(self, temp_project_with_db: Path):
        """Empty arguments should be sanitized and removed."""
        # This simulates what happens with bash backslash continuations
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "",  # Empty arg that bash might pass
            "--session-id", "test_123",
            "",  # Another empty arg
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        # Check sanitization happened
        assert "Removed" in stderr and "empty" in stderr.lower()

    def test_all_agent_types_valid(self, temp_project_with_db: Path):
        """All defined agent types should be accepted."""
        agent_types = [
            "developer",
            "senior_software_engineer",
            "qa_expert",
            "tech_lead",
            "project_manager",
            "investigator",
            "requirements_engineer",
        ]

        for agent_type in agent_types:
            returncode, stdout, stderr = run_script([
                "--agent-type", agent_type,
                "--session-id", "test_123",
                "--branch", "main",
                "--mode", "simple",
                "--testing-mode", "full",
                "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
            ], cwd=temp_project_with_db)

            assert returncode == 0, f"Agent type '{agent_type}' failed: {stderr}"


# ============================================================================
# Test: Output Format
# ============================================================================

class TestOutputFormat:
    """Tests for correct output format."""

    def test_metadata_output_to_stderr(self, temp_project_with_db: Path):
        """Metadata should go to stderr, prompt to stdout."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0

        # Metadata in stderr
        assert "[PROMPT_METADATA]" in stderr
        assert "agent_type=developer" in stderr
        assert "lines=" in stderr
        assert "tokens_estimate=" in stderr

        # Prompt in stdout (not metadata)
        assert "[PROMPT_METADATA]" not in stdout

    def test_project_root_in_metadata(self, temp_project_with_db: Path):
        """Project root should be included in metadata."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        assert "project_root=" in stderr

    def test_task_context_included(self, temp_project_with_db: Path):
        """Task context should be included in output."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_session_123",
            "--branch", "feature/test",
            "--mode", "parallel",
            "--testing-mode", "minimal",
            "--group-id", "AUTH",
            "--task-title", "Implement authentication",
            "--task-requirements", "Create login endpoint",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0

        # Task context should be in output
        assert "test_session_123" in stdout
        assert "AUTH" in stdout or "N/A" in stdout  # group_id
        assert "feature/test" in stdout  # branch
        assert "Parallel" in stdout  # mode
        assert "minimal" in stdout  # testing_mode


# ============================================================================
# Test: PM-Specific Arguments
# ============================================================================

class TestPMSpecificArgs:
    """Tests for Project Manager specific arguments."""

    def test_pm_state_argument(self, temp_project_with_db: Path):
        """PM state JSON should be included in output."""
        pm_state = json.dumps({"groups_completed": 1, "total_groups": 3})

        returncode, stdout, stderr = run_script([
            "--agent-type", "project_manager",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "parallel",
            "--testing-mode", "full",
            "--pm-state", pm_state,
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        assert "PM STATE" in stdout or "groups_completed" in stdout

    def test_resume_context_argument(self, temp_project_with_db: Path):
        """Resume context should be included for PM resume spawns."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "project_manager",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--resume-context", "Previous session was interrupted at group B",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        assert "RESUME CONTEXT" in stdout
        assert "Previous session" in stdout or "interrupted" in stdout


# ============================================================================
# Test: Feedback Arguments (Retries)
# ============================================================================

class TestFeedbackArgs:
    """Tests for feedback arguments used in retries."""

    def test_qa_feedback_included(self, temp_project_with_db: Path):
        """QA feedback should be included in developer retry prompt."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--project-root", str(temp_project_with_db),
            "--qa-feedback", "Test test_auth_edge_case failed: assertion error on line 42",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        # Feedback content should be in output (header is "Previous QA Feedback (FIX THESE ISSUES)")
        assert "test_auth_edge_case" in stdout, f"QA feedback not found in output. stderr: {stderr}"

    def test_tl_feedback_included(self, temp_project_with_db: Path):
        """Tech Lead feedback should be included in developer retry prompt."""
        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--project-root", str(temp_project_with_db),
            "--tl-feedback", "Security issue: SQL injection vulnerability in user input handling",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        # Feedback content should be in output (header is "Tech Lead Feedback (ADDRESS THESE CONCERNS)")
        assert "SQL injection" in stdout, f"TL feedback not found in output. stderr: {stderr}"


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_missing_agent_file_fails(self, temp_project_with_db: Path):
        """Script should fail if agent file doesn't exist."""
        # Remove the developer.md file
        (temp_project_with_db / "agents" / "developer.md").unlink()

        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--project-root", str(temp_project_with_db),
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=temp_project_with_db)

        assert returncode == 1
        assert "ERROR" in stderr
        assert "not found" in stderr.lower()
        assert stdout == ""  # No prompt emitted on error

    def test_help_flag_works(self):
        """Help flag should display usage information."""
        returncode, stdout, stderr = run_script(["--help"])

        assert returncode == 0
        assert "usage" in stdout.lower() or "usage" in stderr.lower()
        assert "--agent-type" in stdout or "--agent-type" in stderr


# ============================================================================
# Test: Integration with Real Database
# ============================================================================

class TestDatabaseIntegration:
    """Tests for database integration scenarios."""

    def test_specializations_loaded_from_db(self, temp_project_with_db: Path):
        """Specializations should be loaded from task_groups table."""
        # Update task group with specializations
        db_path = temp_project_with_db / "bazinga" / "bazinga.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create a specialization template
        spec_dir = temp_project_with_db / "bazinga" / "templates" / "specializations"
        (spec_dir / "python.md").write_text("""# Python Developer Guidance
- Use type hints
- Follow PEP 8
""")

        # Update task group with specialization
        cursor.execute("""
            UPDATE task_groups
            SET specializations = ?
            WHERE id = 'TEST_GROUP'
        """, (json.dumps(["bazinga/templates/specializations/python.md"]),))
        conn.commit()
        conn.close()

        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_session_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--group-id", "TEST_GROUP",
            "--db", str(db_path),
        ], cwd=temp_project_with_db)

        assert returncode == 0
        # Specialization content should be in output
        assert "Python" in stdout or "type hints" in stdout or "PEP 8" in stdout


# ============================================================================
# Test: Cross-Platform Path Handling
# ============================================================================

class TestPathHandling:
    """Tests for path resolution across platforms."""

    def test_runs_from_different_cwd(self, temp_project_with_db: Path):
        """Script should work when run from different CWD."""
        # Create a subdirectory to run from
        subdir = temp_project_with_db / "some" / "nested" / "dir"
        subdir.mkdir(parents=True)

        returncode, stdout, stderr = run_script([
            "--agent-type", "developer",
            "--session-id", "test_123",
            "--branch", "main",
            "--mode", "simple",
            "--testing-mode", "full",
            "--db", str(temp_project_with_db / "bazinga" / "bazinga.db"),
        ], cwd=subdir)

        # Should still work due to PROJECT_ROOT detection
        assert returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
