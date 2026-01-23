"""Pytest configuration and fixtures for platform tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project():
    """Provide a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create common directories
        (tmppath / ".claude" / "skills").mkdir(parents=True)
        (tmppath / "bazinga").mkdir()
        yield tmppath


@pytest.fixture
def clean_env(monkeypatch):
    """Provide clean environment without platform indicators."""
    monkeypatch.delenv("CLAUDE_CODE", raising=False)
    monkeypatch.delenv("GITHUB_COPILOT_AGENT", raising=False)
    monkeypatch.delenv("BAZINGA_PLATFORM", raising=False)
    monkeypatch.delenv("BAZINGA_STATE_BACKEND", raising=False)


@pytest.fixture
def claude_env(monkeypatch):
    """Set environment for Claude Code."""
    monkeypatch.setenv("CLAUDE_CODE", "1")
    monkeypatch.delenv("GITHUB_COPILOT_AGENT", raising=False)


@pytest.fixture
def copilot_env(monkeypatch):
    """Set environment for Copilot."""
    monkeypatch.delenv("CLAUDE_CODE", raising=False)
    monkeypatch.setenv("GITHUB_COPILOT_AGENT", "1")
