"""Tests for platform detection module."""

import os
from pathlib import Path
from unittest.mock import patch
import tempfile


from bazinga.platform.detection import Platform, detect_platform


class TestPlatformEnum:
    """Tests for Platform enum."""

    def test_platform_values(self):
        """Platform enum should have expected values."""
        assert Platform.CLAUDE_CODE.value == "claude_code"
        assert Platform.COPILOT.value == "github_copilot"
        assert Platform.BOTH.value == "both"
        assert Platform.UNKNOWN.value == "unknown"

    def test_platform_str(self):
        """Platform enum string representation returns value."""
        assert str(Platform.CLAUDE_CODE) == "claude_code"
        assert str(Platform.COPILOT) == "github_copilot"

    def test_platform_comparison(self):
        """Platform enum comparison."""
        assert Platform.CLAUDE_CODE == Platform.CLAUDE_CODE
        assert Platform.CLAUDE_CODE != Platform.COPILOT


class TestDetectPlatformEnvVars:
    """Tests for environment variable-based detection."""

    def test_detect_claude_code_env(self):
        """Should detect Claude Code from CLAUDE_CODE env var."""
        with patch.dict(os.environ, {"CLAUDE_CODE": "1"}, clear=False):
            # Clear other platform indicators
            env = {k: v for k, v in os.environ.items() if k != "GITHUB_COPILOT_AGENT"}
            with patch.dict(os.environ, env, clear=True):
                os.environ["CLAUDE_CODE"] = "1"
                result = detect_platform()
                assert result == Platform.CLAUDE_CODE

    def test_detect_copilot_env(self):
        """Should detect Copilot from GITHUB_COPILOT_AGENT env var."""
        with patch.dict(os.environ, {"GITHUB_COPILOT_AGENT": "1"}, clear=True):
            result = detect_platform()
            assert result == Platform.COPILOT

    def test_detect_both_env(self):
        """CLAUDE_CODE takes priority when both env vars set."""
        with patch.dict(
            os.environ,
            {"CLAUDE_CODE": "1", "GITHUB_COPILOT_AGENT": "1"},
            clear=True,
        ):
            result = detect_platform()
            # CLAUDE_CODE is checked first, so it wins
            assert result == Platform.CLAUDE_CODE

    def test_bazinga_platform_override_claude(self):
        """BAZINGA_PLATFORM env var should override detection."""
        with patch.dict(
            os.environ, {"BAZINGA_PLATFORM": "claude_code"}, clear=True
        ):
            result = detect_platform()
            assert result == Platform.CLAUDE_CODE

    def test_bazinga_platform_override_copilot(self):
        """BAZINGA_PLATFORM env var should override detection."""
        with patch.dict(
            os.environ, {"BAZINGA_PLATFORM": "github_copilot"}, clear=True
        ):
            result = detect_platform()
            assert result == Platform.COPILOT

    def test_bazinga_platform_invalid_value(self):
        """Invalid BAZINGA_PLATFORM should fall through to file detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            with patch.dict(os.environ, {"BAZINGA_PLATFORM": "invalid"}, clear=True):
                result = detect_platform(tmppath)
                # Falls through to file-based detection, returns UNKNOWN if no markers
                assert result == Platform.UNKNOWN


class TestDetectPlatformFileBased:
    """Tests for file-based detection."""

    def test_detect_claude_dir_only(self):
        """Should detect Claude Code from .claude directory with markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".claude" / "agents").mkdir(parents=True)

            with patch.dict(os.environ, {}, clear=True):
                result = detect_platform(tmppath)
                assert result == Platform.CLAUDE_CODE

    def test_detect_github_copilot_dir(self):
        """Should detect Copilot from .github with proper markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".github" / "agents").mkdir(parents=True)

            with patch.dict(os.environ, {}, clear=True):
                result = detect_platform(tmppath)
                assert result == Platform.COPILOT

    def test_detect_both_dirs(self):
        """Should detect BOTH when both platform markers exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".claude" / "agents").mkdir(parents=True)
            (tmppath / ".github" / "agents").mkdir(parents=True)

            with patch.dict(os.environ, {}, clear=True):
                result = detect_platform(tmppath)
                assert result == Platform.BOTH

    def test_detect_unknown_no_indicators(self):
        """Should return UNKNOWN when no indicators found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            with patch.dict(os.environ, {}, clear=True):
                result = detect_platform(tmppath)
                assert result == Platform.UNKNOWN

    def test_detect_github_dir_without_copilot(self):
        """Should not detect Copilot from just .github directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".github").mkdir()  # No copilot subdirectory

            with patch.dict(os.environ, {}, clear=True):
                result = detect_platform(tmppath)
                # Should be UNKNOWN since no copilot subdir
                assert result == Platform.UNKNOWN


class TestDetectPlatformEdgeCases:
    """Edge case tests for platform detection."""

    def test_none_project_root_uses_cwd(self):
        """Should use cwd when project_root is None."""
        # This should not raise
        result = detect_platform(None)
        assert isinstance(result, Platform)

    def test_nonexistent_path(self):
        """Should handle nonexistent path gracefully."""
        result = detect_platform(Path("/nonexistent/path/12345"))
        # Should fall back to env-based detection
        assert isinstance(result, Platform)

    def test_detection_is_fast(self):
        """Detection should complete quickly (<100ms)."""
        import time

        start = time.time()
        for _ in range(10):
            detect_platform()
        elapsed = time.time() - start

        # 10 detections should take less than 1 second
        assert elapsed < 1.0, f"Detection too slow: {elapsed}s for 10 calls"
