"""Tests for factory functions."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


from bazinga.platform.detection import Platform
from bazinga.platform.factory import (
    get_agent_spawner,
    get_skill_invoker,
    get_state_backend,
    get_platform_info,
)
from bazinga.platform.agent_spawner.claude_code import ClaudeCodeSpawner
from bazinga.platform.agent_spawner.copilot import CopilotSpawner
from bazinga.platform.skill_invoker.claude_code import ClaudeCodeInvoker
from bazinga.platform.skill_invoker.copilot import CopilotInvoker
from bazinga.platform.state_backend.sqlite import SQLiteBackend
from bazinga.platform.state_backend.file import FileBackend
from bazinga.platform.state_backend.memory import InMemoryBackend


class TestGetAgentSpawner:
    """Tests for get_agent_spawner factory."""

    def test_auto_detect_claude_code(self):
        """Should return ClaudeCodeSpawner for Claude Code platform."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=True):
            spawner = get_agent_spawner()
            assert isinstance(spawner, ClaudeCodeSpawner)

    def test_auto_detect_copilot(self):
        """Should return CopilotSpawner for Copilot platform."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_AGENT": "1"}, clear=True):
            spawner = get_agent_spawner()
            assert isinstance(spawner, CopilotSpawner)

    def test_explicit_platform_claude(self):
        """Should respect explicit platform parameter."""
        spawner = get_agent_spawner(platform=Platform.CLAUDE_CODE)
        assert isinstance(spawner, ClaudeCodeSpawner)

    def test_explicit_platform_copilot(self):
        """Should respect explicit platform parameter."""
        spawner = get_agent_spawner(platform=Platform.COPILOT)
        assert isinstance(spawner, CopilotSpawner)

    def test_unknown_platform_defaults_claude(self):
        """Unknown platform should default to Claude Code."""
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                # No platform indicators
                spawner = get_agent_spawner(project_root=Path(tmpdir))
                assert isinstance(spawner, ClaudeCodeSpawner)

    def test_both_platforms_defaults_claude(self):
        """BOTH platform should default to Claude Code."""
        spawner = get_agent_spawner(platform=Platform.BOTH)
        assert isinstance(spawner, ClaudeCodeSpawner)


class TestGetSkillInvoker:
    """Tests for get_skill_invoker factory."""

    def test_auto_detect_claude_code(self):
        """Should return ClaudeCodeInvoker for Claude Code platform."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=True):
            invoker = get_skill_invoker()
            assert isinstance(invoker, ClaudeCodeInvoker)

    def test_auto_detect_copilot(self):
        """Should return CopilotInvoker for Copilot platform."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_AGENT": "1"}, clear=True):
            invoker = get_skill_invoker()
            assert isinstance(invoker, CopilotInvoker)

    def test_explicit_platform(self):
        """Should respect explicit platform parameter."""
        invoker = get_skill_invoker(platform=Platform.COPILOT)
        assert isinstance(invoker, CopilotInvoker)

    def test_project_root_passed_to_invoker(self):
        """Should pass project_root to invoker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            invoker = get_skill_invoker(
                platform=Platform.CLAUDE_CODE,
                project_root=tmppath,
            )
            assert invoker._project_root == tmppath


class TestGetStateBackend:
    """Tests for get_state_backend factory."""

    def test_auto_detect_claude_code_sqlite(self):
        """Claude Code should use SQLite by default."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                backend = get_state_backend(project_root=Path(tmpdir))
                assert isinstance(backend, SQLiteBackend)

    def test_force_memory_backend(self):
        """force_backend='memory' should return InMemoryBackend."""
        backend = get_state_backend(force_backend="memory")
        assert isinstance(backend, InMemoryBackend)

    def test_force_file_backend(self):
        """force_backend='file' should return FileBackend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = get_state_backend(
                force_backend="file",
                project_root=Path(tmpdir),
            )
            assert isinstance(backend, FileBackend)

    def test_force_sqlite_backend(self):
        """force_backend='sqlite' should return SQLiteBackend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = get_state_backend(
                force_backend="sqlite",
                project_root=Path(tmpdir),
            )
            assert isinstance(backend, SQLiteBackend)

    def test_env_var_override(self):
        """BAZINGA_STATE_BACKEND env var should override auto-detect."""
        with patch.dict(
            os.environ,
            {"BAZINGA_STATE_BACKEND": "memory", "CLAUDE_CODE": "1"},
        ):
            backend = get_state_backend()
            assert isinstance(backend, InMemoryBackend)

    def test_copilot_falls_back_gracefully(self):
        """Copilot should fall back if SQLite not accessible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # This tests the fallback mechanism
            backend = get_state_backend(
                platform=Platform.COPILOT,
                project_root=Path(tmpdir),
            )
            # Should return either SQLite or File backend
            assert isinstance(backend, (SQLiteBackend, FileBackend))


class TestGetPlatformInfo:
    """Tests for get_platform_info function."""

    def test_returns_dict(self):
        """Should return dict with platform info."""
        info = get_platform_info()
        assert isinstance(info, dict)

    def test_contains_required_keys(self):
        """Should contain required information keys."""
        info = get_platform_info()

        assert "platform" in info
        assert "platform_name" in info
        assert "env_vars" in info
        assert "cwd" in info

    def test_env_vars_section(self):
        """Should include environment variable status."""
        info = get_platform_info()

        env_vars = info["env_vars"]
        assert "CLAUDE_CODE" in env_vars
        assert "GITHUB_COPILOT_AGENT" in env_vars
        assert "BAZINGA_PLATFORM" in env_vars
        assert "BAZINGA_STATE_BACKEND" in env_vars

    def test_directory_checks(self):
        """Should include directory existence checks."""
        info = get_platform_info()

        assert "has_claude_dir" in info
        assert "has_github_dir" in info
        assert isinstance(info["has_claude_dir"], bool)
        assert isinstance(info["has_github_dir"], bool)

    def test_platform_value_format(self):
        """Platform value should be from Platform enum."""
        info = get_platform_info()

        # Should be one of the valid platform values
        valid_values = ["claude_code", "github_copilot", "both", "unknown"]
        assert info["platform"] in valid_values


class TestFactoryIntegration:
    """Integration tests for factory functions."""

    def test_all_factories_work_together(self):
        """All factories should work with same platform."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)

                spawner = get_agent_spawner(project_root=tmppath)
                invoker = get_skill_invoker(project_root=tmppath)
                backend = get_state_backend(project_root=tmppath)

                # All should be Claude Code implementations
                assert isinstance(spawner, ClaudeCodeSpawner)
                assert isinstance(invoker, ClaudeCodeInvoker)
                assert isinstance(backend, SQLiteBackend)

    def test_consistent_copilot_setup(self):
        """All factories should return Copilot implementations."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_AGENT": "1"}, clear=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)

                spawner = get_agent_spawner(project_root=tmppath)
                invoker = get_skill_invoker(project_root=tmppath)
                backend = get_state_backend(project_root=tmppath)

                assert isinstance(spawner, CopilotSpawner)
                assert isinstance(invoker, CopilotInvoker)
                # Backend could be SQLite or File (fallback)
                assert isinstance(backend, (SQLiteBackend, FileBackend))

    def test_explicit_override_all(self):
        """Explicit platform should override for all factories."""
        spawner = get_agent_spawner(platform=Platform.COPILOT)
        invoker = get_skill_invoker(platform=Platform.COPILOT)

        assert isinstance(spawner, CopilotSpawner)
        assert isinstance(invoker, CopilotInvoker)
