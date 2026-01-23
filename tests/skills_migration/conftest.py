"""Pytest configuration and fixtures for skills migration tests.

See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def tmp_project() -> Generator[Path, None, None]:
    """Provide a temporary project directory with minimal structure.

    Note: Does NOT create platform marker directories (.claude/agents/, .github/agents/)
    to allow tests to control which platform markers exist.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create only bazinga directory - let tests create platform-specific markers
        (tmppath / "bazinga").mkdir()
        yield tmppath


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide clean environment without platform indicators."""
    monkeypatch.delenv("CLAUDE_CODE", raising=False)
    monkeypatch.delenv("GITHUB_COPILOT_AGENT", raising=False)
    monkeypatch.delenv("BAZINGA_PLATFORM", raising=False)
    monkeypatch.delenv("BAZINGA_STATE_BACKEND", raising=False)


@pytest.fixture
def claude_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment for Claude Code platform."""
    monkeypatch.setenv("CLAUDE_CODE", "1")
    monkeypatch.delenv("GITHUB_COPILOT_AGENT", raising=False)
    monkeypatch.delenv("BAZINGA_PLATFORM", raising=False)


@pytest.fixture
def copilot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment for GitHub Copilot platform."""
    monkeypatch.delenv("CLAUDE_CODE", raising=False)
    monkeypatch.setenv("GITHUB_COPILOT_AGENT", "1")
    monkeypatch.delenv("BAZINGA_PLATFORM", raising=False)


@pytest.fixture
def both_platforms_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment for dual-platform mode."""
    monkeypatch.delenv("CLAUDE_CODE", raising=False)
    monkeypatch.delenv("GITHUB_COPILOT_AGENT", raising=False)
    monkeypatch.setenv("BAZINGA_PLATFORM", "both")


@pytest.fixture
def tmp_db(tmp_project: Path) -> Generator[Path, None, None]:
    """Create a temporary SQLite database with basic schema."""
    db_path = tmp_project / "bazinga" / "bazinga.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create minimal schema for skills tests
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'active',
            mode TEXT DEFAULT 'simple',
            platform TEXT DEFAULT 'claude',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workflow_transitions (
            id INTEGER PRIMARY KEY,
            from_agent TEXT NOT NULL,
            response_status TEXT NOT NULL,
            to_agent TEXT,
            action TEXT NOT NULL,
            testing_mode TEXT DEFAULT 'full'
        );

        CREATE TABLE IF NOT EXISTS skill_outputs (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            group_id TEXT DEFAULT 'global',
            skill_name TEXT NOT NULL,
            output_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Insert a test session
    cursor.execute("""
        INSERT INTO sessions (session_id, status, mode, platform)
        VALUES ('test_session_001', 'active', 'simple', 'claude')
    """)

    # Insert basic workflow transitions
    transitions = [
        ('developer', 'READY_FOR_QA', 'qa_expert', 'spawn', 'full'),
        ('developer', 'READY_FOR_REVIEW', 'tech_lead', 'spawn', 'minimal'),
        ('qa_expert', 'PASS', 'tech_lead', 'spawn', 'full'),
        ('qa_expert', 'FAIL', 'developer', 'respawn', 'full'),
        ('tech_lead', 'APPROVED', 'project_manager', 'spawn', 'full'),
    ]
    cursor.executemany("""
        INSERT INTO workflow_transitions (from_agent, response_status, to_agent, action, testing_mode)
        VALUES (?, ?, ?, ?, ?)
    """, transitions)

    conn.commit()
    conn.close()

    yield db_path


@pytest.fixture
def skills_config(tmp_project: Path) -> Path:
    """Create a temporary skills_config.json file."""
    import json

    config_path = tmp_project / "bazinga" / "skills_config.json"
    config = {
        "_metadata": {
            "profile": "full",
            "version": "1.0.0"
        },
        "context_engineering": {
            "enable_context_assembler": True,
            "enable_fts5": False,
            "retrieval_limits": {
                "developer": 3,
                "senior_software_engineer": 5,
                "qa_expert": 5,
                "tech_lead": 5,
                "investigator": 5
            },
            "token_safety_margin": 0.15
        },
        "developer": {
            "lint-check": "mandatory",
            "codebase-analysis": "optional"
        },
        "tech_lead": {
            "security-scan": "mandatory",
            "test-coverage": "mandatory"
        }
    }

    config_path.write_text(json.dumps(config, indent=2))
    return config_path
