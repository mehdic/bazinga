#!/usr/bin/env python3
"""
Comprehensive test suite for bazinga_paths module.

Tests path auto-detection across various scenarios:
- Basic detection from script location and CWD
- Explicit overrides (--db, --project-root, env vars)
- Edge cases (monorepos, symlinks, moved directories, nested projects)
- Error handling and caching behavior
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pytest

# Add the _shared directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'skills' / '_shared'))

from bazinga_paths import (
    get_project_root,
    get_db_path,
    get_skills_dir,
    get_artifacts_dir,
    get_agents_dir,
    get_detection_info,
    clear_cache,
    _is_bazinga_project_root,
    _detect_from_cwd,
    _detect_from_script_location,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clear_path_cache():
    """Clear the path cache before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """Create a temporary BAZINGA project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "test_project"
        project_root.mkdir()

        # Create required directories
        (project_root / ".claude").mkdir()
        (project_root / ".claude" / "skills").mkdir()
        (project_root / "bazinga").mkdir()

        yield project_root


@pytest.fixture
def temp_project_with_db(temp_project: Path) -> Generator[Path, None, None]:
    """Create a temp project with an actual database file."""
    db_path = temp_project / "bazinga" / "bazinga.db"
    db_path.touch()
    yield temp_project


@pytest.fixture
def nested_projects() -> Generator[dict, None, None]:
    """Create nested project structure (monorepo scenario)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Outer project (monorepo root)
        outer = Path(tmpdir) / "monorepo"
        outer.mkdir()
        (outer / ".claude").mkdir()
        (outer / "bazinga").mkdir()

        # Inner project
        inner = outer / "packages" / "my_app"
        inner.mkdir(parents=True)
        (inner / ".claude").mkdir()
        (inner / "bazinga").mkdir()

        yield {"outer": outer, "inner": inner}


@pytest.fixture
def env_cleanup():
    """Clean up environment variables after test."""
    old_root = os.environ.get("BAZINGA_ROOT")
    yield
    if old_root is None:
        os.environ.pop("BAZINGA_ROOT", None)
    else:
        os.environ["BAZINGA_ROOT"] = old_root


# ============================================================================
# Basic Detection Tests
# ============================================================================

class TestProjectRootValidation:
    """Test _is_bazinga_project_root function."""

    def test_valid_project_root(self, temp_project: Path):
        """Valid project root has both .claude and bazinga directories."""
        is_valid, reason = _is_bazinga_project_root(temp_project)
        assert is_valid is True
        assert "found .claude/ and bazinga/" in reason

    def test_missing_claude_dir(self, temp_project: Path):
        """Missing .claude directory is not valid."""
        shutil.rmtree(temp_project / ".claude")
        is_valid, reason = _is_bazinga_project_root(temp_project)
        assert is_valid is False
        assert "missing .claude/" in reason

    def test_missing_bazinga_dir(self, temp_project: Path):
        """Missing bazinga directory is not valid."""
        shutil.rmtree(temp_project / "bazinga")
        is_valid, reason = _is_bazinga_project_root(temp_project)
        assert is_valid is False
        assert "missing" in reason and "bazinga/" in reason

    def test_both_missing(self):
        """Non-project directory is not valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            is_valid, reason = _is_bazinga_project_root(Path(tmpdir))
            assert is_valid is False
            assert "missing both" in reason


class TestCWDDetection:
    """Test detection from current working directory."""

    def test_detect_from_project_root(self, temp_project: Path):
        """Detect project when CWD is project root."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            root = _detect_from_cwd()
            assert root == temp_project
        finally:
            os.chdir(original_cwd)

    def test_detect_from_subdirectory(self, temp_project: Path):
        """Detect project when CWD is a subdirectory."""
        subdir = temp_project / "src" / "lib"
        subdir.mkdir(parents=True)

        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = _detect_from_cwd()
            assert root == temp_project
        finally:
            os.chdir(original_cwd)

    def test_no_project_found(self):
        """Return None when no project root found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                root = _detect_from_cwd()
                assert root is None
            finally:
                os.chdir(original_cwd)


class TestScriptLocationDetection:
    """Test detection from script location."""

    def test_detect_from_script_in_project(self, temp_project: Path):
        """Detect project from script within project tree."""
        script_path = temp_project / ".claude" / "skills" / "test" / "scripts" / "test.py"
        script_path.parent.mkdir(parents=True)
        script_path.touch()

        root = _detect_from_script_location(script_path)
        assert root == temp_project


# ============================================================================
# Override Tests
# ============================================================================

class TestExplicitOverrides:
    """Test explicit path overrides."""

    def test_override_with_valid_path(self, temp_project: Path):
        """Override with valid project path works."""
        root = get_project_root(override=str(temp_project))
        assert root == temp_project

    def test_override_with_invalid_path(self):
        """Override with invalid path raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError, match="not a valid BAZINGA project root"):
                get_project_root(override=tmpdir)

    def test_override_with_nonexistent_path(self):
        """Override with nonexistent path raises error."""
        with pytest.raises(RuntimeError):
            get_project_root(override="/nonexistent/path/that/doesnt/exist")


class TestEnvironmentVariableOverride:
    """Test BAZINGA_ROOT environment variable override."""

    def test_env_var_override(self, temp_project: Path, env_cleanup):
        """BAZINGA_ROOT environment variable is used."""
        os.environ["BAZINGA_ROOT"] = str(temp_project)
        root = get_project_root()
        assert root == temp_project

    def test_env_var_invalid_path_with_fallback(self, env_cleanup):
        """Invalid BAZINGA_ROOT falls back to CWD detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid project in tmpdir
            valid_project = Path(tmpdir) / "valid"
            valid_project.mkdir()
            (valid_project / ".claude").mkdir()
            (valid_project / "bazinga").mkdir()

            # Set env var to invalid path (not a project)
            invalid_dir = Path(tmpdir) / "invalid"
            invalid_dir.mkdir()
            os.environ["BAZINGA_ROOT"] = str(invalid_dir)

            original_cwd = os.getcwd()
            try:
                # Change to valid project - fallback should find it
                os.chdir(valid_project)
                root = get_project_root()
                assert root == valid_project
            finally:
                os.chdir(original_cwd)

    def test_env_var_invalid_no_fallback_raises(self, env_cleanup):
        """Invalid BAZINGA_ROOT raises when no fallback available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set env var to invalid path
            os.environ["BAZINGA_ROOT"] = tmpdir

            original_cwd = os.getcwd()
            try:
                # Change to a dir that's NOT a valid project
                os.chdir(tmpdir)
                with pytest.raises(RuntimeError):
                    get_project_root()
            finally:
                os.chdir(original_cwd)

    def test_explicit_override_beats_env_var(self, temp_project: Path, env_cleanup):
        """Explicit override takes precedence over env var."""
        # Create second project
        with tempfile.TemporaryDirectory() as tmpdir:
            other_project = Path(tmpdir) / "other"
            other_project.mkdir()
            (other_project / ".claude").mkdir()
            (other_project / "bazinga").mkdir()

            os.environ["BAZINGA_ROOT"] = str(other_project)

            # Explicit override should win
            root = get_project_root(override=str(temp_project))
            assert root == temp_project


# ============================================================================
# Path Derivation Tests
# ============================================================================

class TestPathDerivation:
    """Test derived path functions."""

    def test_get_db_path(self, temp_project: Path):
        """get_db_path returns correct path."""
        db_path = get_db_path(project_root=temp_project)
        assert db_path == temp_project / "bazinga" / "bazinga.db"

    def test_get_db_path_with_override(self, temp_project: Path):
        """get_db_path with explicit override."""
        custom_db = temp_project / "custom.db"
        db_path = get_db_path(override=str(custom_db))
        assert db_path == custom_db

    def test_get_skills_dir(self, temp_project: Path):
        """get_skills_dir returns correct path."""
        skills = get_skills_dir(project_root=temp_project)
        assert skills == temp_project / ".claude" / "skills"

    def test_get_artifacts_dir(self, temp_project: Path):
        """get_artifacts_dir returns correct path."""
        artifacts = get_artifacts_dir(project_root=temp_project)
        assert artifacts == temp_project / "bazinga" / "artifacts"

    def test_get_artifacts_dir_with_session(self, temp_project: Path):
        """get_artifacts_dir with session_id."""
        artifacts = get_artifacts_dir(session_id="test123", project_root=temp_project)
        assert artifacts == temp_project / "bazinga" / "artifacts" / "test123"

    def test_get_agents_dir(self, temp_project: Path):
        """get_agents_dir returns correct path."""
        agents = get_agents_dir(project_root=temp_project)
        assert agents == temp_project / "agents"


# ============================================================================
# Caching Tests
# ============================================================================

class TestCaching:
    """Test caching behavior."""

    def test_cache_is_used(self, temp_project: Path):
        """Subsequent calls use cached value when override used."""
        # Use temp project from a non-project directory
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)  # Not a project root
                root1 = get_project_root(override=str(temp_project))
                root2 = get_project_root()  # Should use cache
                assert root1 == root2 == temp_project
            finally:
                os.chdir(original_cwd)

    def test_clear_cache_triggers_redetection(self, temp_project: Path):
        """clear_cache causes re-detection on next call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)  # Not a project root

                # Prime cache with temp_project
                get_project_root(override=str(temp_project))
                clear_cache()

                # After clearing, should fail since CWD isn't a project
                with pytest.raises(RuntimeError):
                    get_project_root()
            finally:
                os.chdir(original_cwd)

    def test_cache_invalidation_on_deletion(self, temp_project: Path):
        """Cache is invalidated if directory is deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)  # Not a project root

                get_project_root(override=str(temp_project))

                # Delete the project
                shutil.rmtree(temp_project)

                # Should fail since cached path no longer exists
                with pytest.raises(RuntimeError):
                    get_project_root()
            finally:
                os.chdir(original_cwd)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_nested_projects_finds_nearest(self, nested_projects: dict):
        """In nested projects, finds the nearest root."""
        inner = nested_projects["inner"]

        original_cwd = os.getcwd()
        try:
            os.chdir(inner)
            root = _detect_from_cwd()
            # Should find inner, not outer
            assert root == inner
        finally:
            os.chdir(original_cwd)

    def test_deeply_nested_subdirectory(self, temp_project: Path):
        """Detection works from deeply nested directories."""
        deep = temp_project / "a" / "b" / "c" / "d" / "e" / "f"
        deep.mkdir(parents=True)

        original_cwd = os.getcwd()
        try:
            os.chdir(deep)
            root = _detect_from_cwd()
            assert root == temp_project
        finally:
            os.chdir(original_cwd)

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require admin on Windows")
    def test_symlink_resolution(self, temp_project: Path):
        """Symlinks are resolved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            link_path = Path(tmpdir) / "project_link"
            link_path.symlink_to(temp_project)

            # Detection through symlink should resolve to real path
            root = get_project_root(override=str(link_path))
            assert root.resolve() == temp_project.resolve()

    def test_path_with_spaces(self):
        """Handles paths with spaces correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "my project with spaces"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / "bazinga").mkdir()

            root = get_project_root(override=str(project))
            assert root == project

    def test_path_with_unicode(self):
        """Handles paths with unicode characters correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "项目_проект_プロジェクト"
            project.mkdir()
            (project / ".claude").mkdir()
            (project / "bazinga").mkdir()

            root = get_project_root(override=str(project))
            assert root == project


class TestSymlinkCycles:
    """Test behavior with symlink cycles (prevent infinite loops)."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require admin on Windows")
    def test_symlink_cycle_detection(self):
        """Detection doesn't hang on symlink cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            a = Path(tmpdir) / "a"
            b = Path(tmpdir) / "b"

            a.mkdir()
            b.symlink_to(a)
            (a / "link_to_b").symlink_to(b)

            original_cwd = os.getcwd()
            try:
                os.chdir(a)
                # Should complete (possibly returning None) without hanging
                result = _detect_from_cwd()
                # No assertion on result, just that it completes
            finally:
                os.chdir(original_cwd)


# ============================================================================
# Detection Info Tests
# ============================================================================

class TestDetectionInfo:
    """Test get_detection_info function."""

    def test_successful_detection_info(self, temp_project: Path):
        """Detection info includes all expected fields on success."""
        get_project_root(override=str(temp_project))
        info = get_detection_info()

        assert "project_root" in info
        assert "detection_source" in info
        assert "db_path" in info
        assert "skills_dir" in info
        assert "artifacts_dir" in info
        assert "agents_dir" in info
        assert "cwd" in info
        assert "env_var_set" in info
        assert "error" not in info

    def test_failed_detection_info(self):
        """Detection info includes error on failure."""
        clear_cache()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                info = get_detection_info()

                assert "error" in info
                assert "cwd" in info
            finally:
                os.chdir(original_cwd)


# ============================================================================
# Integration Tests
# ============================================================================

class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_bazinga_db_script_scenario(self, temp_project_with_db: Path):
        """Simulate bazinga_db.py script detection."""
        project = temp_project_with_db

        # Create script structure like bazinga_db.py
        scripts_dir = project / ".claude" / "skills" / "bazinga-db" / "scripts"
        scripts_dir.mkdir(parents=True)
        script_path = scripts_dir / "bazinga_db.py"
        script_path.touch()

        # Detection from script location
        root = _detect_from_script_location(script_path)
        assert root == project

        # DB path should be correct
        db_path = get_db_path(project_root=root)
        assert db_path == project / "bazinga" / "bazinga.db"
        assert db_path.exists()

    def test_installed_project_scenario(self):
        """Simulate installed project (bazinga install)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "my_client_project"
            project.mkdir()

            # Installed structure
            (project / ".claude" / "skills" / "bazinga-db" / "scripts").mkdir(parents=True)
            (project / "bazinga").mkdir()
            (project / "bazinga" / "bazinga.db").touch()

            root = get_project_root(override=str(project))
            db = get_db_path(project_root=root)

            assert root == project
            assert db == project / "bazinga" / "bazinga.db"

    def test_dev_environment_scenario(self):
        """Simulate development environment (bazinga repo)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Dev structure (like /home/user/bazinga/)
            repo = Path(tmpdir) / "bazinga"
            repo.mkdir()
            (repo / ".claude" / "skills").mkdir(parents=True)
            (repo / "bazinga").mkdir()
            (repo / "agents").mkdir()

            root = get_project_root(override=str(repo))

            assert get_skills_dir(project_root=root) == repo / ".claude" / "skills"
            assert get_agents_dir(project_root=root) == repo / "agents"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and messages."""

    def test_no_project_root_error_message(self):
        """Error message is helpful when no project found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                clear_cache()

                with pytest.raises(RuntimeError) as exc_info:
                    get_project_root()

                error_msg = str(exc_info.value)
                assert "Could not detect" in error_msg
                assert ".claude/" in error_msg or "BAZINGA_ROOT" in error_msg
            finally:
                os.chdir(original_cwd)

    def test_invalid_override_error_message(self):
        """Error message explains why override is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError) as exc_info:
                get_project_root(override=tmpdir)

            error_msg = str(exc_info.value)
            assert "not a valid BAZINGA project root" in error_msg


# ============================================================================
# Performance Tests (optional, can be skipped)
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    def test_cached_access_is_reasonable(self, temp_project: Path):
        """Cached access should complete in reasonable time."""
        import time

        # Prime the cache
        get_project_root(override=str(temp_project))

        # Time 100 cached accesses
        start = time.perf_counter()
        for _ in range(100):
            get_project_root()
        elapsed = time.perf_counter() - start

        # Should be < 500ms for 100 calls (< 5ms per call)
        # This is a sanity check, not a tight performance bound
        assert elapsed < 0.5, f"Cached access too slow: {elapsed*1000:.2f}ms for 100 calls"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
