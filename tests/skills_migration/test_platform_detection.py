"""Tests for platform detection module.

Validates FR-001: Platform detection with <10ms latency.
See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Add bazinga/platform to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bazinga" / "platform"))

from detection import (
    Platform,
    detect_platform,
    get_platform_name,
    is_claude_code,
    is_copilot,
)


class TestPlatformEnum:
    """Test Platform enum values and string conversion."""

    def test_platform_values(self) -> None:
        """Test that Platform enum has expected values."""
        assert Platform.CLAUDE_CODE.value == "claude_code"
        assert Platform.COPILOT.value == "github_copilot"
        assert Platform.BOTH.value == "both"
        assert Platform.UNKNOWN.value == "unknown"

    def test_platform_str(self) -> None:
        """Test Platform enum string conversion."""
        assert str(Platform.CLAUDE_CODE) == "claude_code"
        assert str(Platform.COPILOT) == "github_copilot"
        assert str(Platform.BOTH) == "both"
        assert str(Platform.UNKNOWN) == "unknown"


class TestEnvironmentDetection:
    """Test environment variable-based platform detection."""

    def test_detect_claude_code_env(self, claude_env: None) -> None:
        """Test detection via CLAUDE_CODE environment variable."""
        platform = detect_platform()
        assert platform == Platform.CLAUDE_CODE

    def test_detect_copilot_env(self, copilot_env: None) -> None:
        """Test detection via GITHUB_COPILOT_AGENT environment variable."""
        platform = detect_platform()
        assert platform == Platform.COPILOT

    def test_manual_override_claude(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test BAZINGA_PLATFORM=claude override."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "claude")
        assert detect_platform() == Platform.CLAUDE_CODE

    def test_manual_override_claude_code(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test BAZINGA_PLATFORM=claude_code override."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "claude_code")
        assert detect_platform() == Platform.CLAUDE_CODE

    def test_manual_override_copilot(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test BAZINGA_PLATFORM=copilot override."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "copilot")
        assert detect_platform() == Platform.COPILOT

    def test_manual_override_github_copilot(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test BAZINGA_PLATFORM=github_copilot override."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "github_copilot")
        assert detect_platform() == Platform.COPILOT

    def test_manual_override_both(self, clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test BAZINGA_PLATFORM=both override."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "both")
        assert detect_platform() == Platform.BOTH


class TestFileBasedDetection:
    """Test file-based platform detection (fallback)."""

    def test_detect_claude_from_agents_dir(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection via .claude/agents/ directory."""
        (tmp_project / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        assert detect_platform(tmp_project) == Platform.CLAUDE_CODE

    def test_detect_claude_from_claude_md(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection via .claude/CLAUDE.md file."""
        (tmp_project / ".claude").mkdir(parents=True, exist_ok=True)
        (tmp_project / ".claude" / "CLAUDE.md").write_text("# Claude Code\n")
        # Remove agents dir to test CLAUDE.md detection
        agents_dir = tmp_project / ".claude" / "agents"
        if agents_dir.exists():
            agents_dir.rmdir()
        assert detect_platform(tmp_project) == Platform.CLAUDE_CODE

    def test_detect_claude_from_settings_json(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection via .claude/settings.json file."""
        (tmp_project / ".claude").mkdir(parents=True, exist_ok=True)
        (tmp_project / ".claude" / "settings.json").write_text("{}")
        # Remove other markers
        for marker in ["agents", "CLAUDE.md"]:
            path = tmp_project / ".claude" / marker
            if path.exists():
                if path.is_dir():
                    path.rmdir()
                else:
                    path.unlink()
        assert detect_platform(tmp_project) == Platform.CLAUDE_CODE

    def test_detect_copilot_from_agents_dir(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection via .github/agents/ directory."""
        # Remove Claude markers first
        claude_dir = tmp_project / ".claude"
        if claude_dir.exists():
            import shutil
            shutil.rmtree(claude_dir)
        (tmp_project / ".github" / "agents").mkdir(parents=True, exist_ok=True)
        assert detect_platform(tmp_project) == Platform.COPILOT

    def test_detect_copilot_from_instructions(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection via .github/copilot-instructions.md file."""
        # Create .github directory and copilot-instructions.md file
        (tmp_project / ".github").mkdir(parents=True, exist_ok=True)
        (tmp_project / ".github" / "copilot-instructions.md").write_text("# Copilot\n")
        assert detect_platform(tmp_project) == Platform.COPILOT

    def test_detect_both_platforms(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection when both platforms' markers exist."""
        (tmp_project / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        (tmp_project / ".github" / "agents").mkdir(parents=True, exist_ok=True)
        assert detect_platform(tmp_project) == Platform.BOTH

    def test_detect_unknown(self, clean_env: None, tmp_project: Path) -> None:
        """Test detection returns UNKNOWN when no markers found."""
        # Remove all platform markers
        import shutil
        for marker_dir in [".claude", ".github"]:
            path = tmp_project / marker_dir
            if path.exists():
                shutil.rmtree(path)
        assert detect_platform(tmp_project) == Platform.UNKNOWN


class TestHelperFunctions:
    """Test helper functions for platform detection."""

    def test_is_claude_code_true(self, claude_env: None) -> None:
        """Test is_claude_code returns True for Claude Code."""
        assert is_claude_code() is True

    def test_is_claude_code_false(self, copilot_env: None) -> None:
        """Test is_claude_code returns False for Copilot."""
        assert is_claude_code() is False

    def test_is_claude_code_both(self, both_platforms_env: None) -> None:
        """Test is_claude_code returns True for BOTH platform."""
        assert is_claude_code() is True

    def test_is_copilot_true(self, copilot_env: None) -> None:
        """Test is_copilot returns True for Copilot."""
        assert is_copilot() is True

    def test_is_copilot_false(self, claude_env: None) -> None:
        """Test is_copilot returns False for Claude Code."""
        assert is_copilot() is False

    def test_is_copilot_both(self, both_platforms_env: None) -> None:
        """Test is_copilot returns True for BOTH platform."""
        assert is_copilot() is True

    def test_get_platform_name_claude(self) -> None:
        """Test get_platform_name for Claude Code."""
        assert get_platform_name(Platform.CLAUDE_CODE) == "Claude Code"

    def test_get_platform_name_copilot(self) -> None:
        """Test get_platform_name for Copilot."""
        assert get_platform_name(Platform.COPILOT) == "GitHub Copilot"

    def test_get_platform_name_both(self) -> None:
        """Test get_platform_name for BOTH."""
        assert get_platform_name(Platform.BOTH) == "Claude Code + GitHub Copilot"

    def test_get_platform_name_unknown(self) -> None:
        """Test get_platform_name for UNKNOWN."""
        assert get_platform_name(Platform.UNKNOWN) == "Unknown Platform"


class TestPerformance:
    """Test platform detection performance requirements."""

    def test_detection_latency(self, claude_env: None) -> None:
        """Test that platform detection completes in <10ms (FR-001)."""
        start = time.perf_counter()
        for _ in range(100):
            detect_platform()
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000

        # FR-001 requires <10ms detection time
        assert avg_ms < 10, f"Detection took {avg_ms:.2f}ms on average (must be <10ms)"

    def test_file_detection_latency(self, clean_env: None, tmp_project: Path) -> None:
        """Test file-based detection is still fast."""
        (tmp_project / ".claude" / "agents").mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        for _ in range(100):
            detect_platform(tmp_project)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000

        # File-based detection should be <10ms (target 5-10ms per PRD)
        assert avg_ms < 10, f"File detection took {avg_ms:.2f}ms on average (must be <10ms)"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_project_root(self, clean_env: None) -> None:
        """Test detection with non-existent project root."""
        result = detect_platform(Path("/nonexistent/path/12345"))
        assert result == Platform.UNKNOWN

    def test_empty_bazinga_platform(self, clean_env: None, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test empty BAZINGA_PLATFORM doesn't crash."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "")
        # Should fall through to file-based detection or UNKNOWN (using clean tmp_project)
        result = detect_platform(tmp_project)
        assert result == Platform.UNKNOWN  # No platform markers in clean tmp_project

    def test_invalid_bazinga_platform(self, clean_env: None, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test invalid BAZINGA_PLATFORM is ignored."""
        monkeypatch.setenv("BAZINGA_PLATFORM", "invalid_platform")
        # Should fall through to file-based detection (using clean tmp_project)
        result = detect_platform(tmp_project)
        assert result == Platform.UNKNOWN  # No platform markers in clean tmp_project

    def test_env_takes_precedence_over_files(
        self, claude_env: None, tmp_project: Path
    ) -> None:
        """Test that env var takes precedence over file markers."""
        # Set up Copilot file markers
        (tmp_project / ".github" / "agents").mkdir(parents=True, exist_ok=True)
        # But env says Claude Code
        assert detect_platform(tmp_project) == Platform.CLAUDE_CODE
