"""
Tests for security utilities.

Tests path validation, filename sanitization, and safe subprocess execution.
"""

import subprocess
from pathlib import Path

import pytest

from bazinga_cli.security import (
    PathValidator,
    SafeSubprocess,
    SecurityError,
    validate_script_path,
)


class TestPathValidator:
    """Test path validation functions."""

    def test_validate_project_name_valid(self):
        """Test valid project names."""
        valid_names = [
            "my-project",
            "MyProject123",
            "test_app",
            "app.v2",
            "a",
            "A" * 255,
        ]
        for name in valid_names:
            result = PathValidator.validate_project_name(name)
            assert result == name

    def test_validate_project_name_path_traversal(self):
        """Test rejection of path traversal attempts."""
        invalid_names = [
            "../etc/passwd",
            "../../secret",
            "foo/../bar",
            "..hidden",
        ]
        for name in invalid_names:
            with pytest.raises(SecurityError, match="cannot contain"):
                PathValidator.validate_project_name(name)

    def test_validate_project_name_absolute_paths(self):
        """Test rejection of absolute paths."""
        invalid_names = [
            "/etc/passwd",
            "/tmp/test",
            "\\Windows\\System32",
        ]
        for name in invalid_names:
            with pytest.raises(SecurityError, match="cannot start with"):
                PathValidator.validate_project_name(name)

    def test_validate_project_name_null_bytes(self):
        """Test rejection of null byte injection."""
        with pytest.raises(SecurityError, match="null bytes"):
            PathValidator.validate_project_name("test\x00file")

    def test_validate_project_name_invalid_characters(self):
        """Test rejection of dangerous characters."""
        invalid_names = [
            "my project",  # space
            "test;rm -rf",  # semicolon
            "app$(cmd)",  # command substitution
            "file|pipe",  # pipe
            "test&background",  # ampersand
        ]
        for name in invalid_names:
            with pytest.raises(SecurityError, match="can only contain"):
                PathValidator.validate_project_name(name)

    def test_validate_project_name_reserved(self):
        """Test rejection of Windows reserved names."""
        reserved = ["aux", "con", "nul", "prn", "com1", "lpt1"]
        for name in reserved:
            with pytest.raises(SecurityError, match="reserved"):
                PathValidator.validate_project_name(name)

    def test_validate_project_name_empty(self):
        """Test rejection of empty names."""
        with pytest.raises(SecurityError, match="cannot be empty"):
            PathValidator.validate_project_name("")

    def test_validate_project_name_too_long(self):
        """Test rejection of overly long names."""
        with pytest.raises(SecurityError, match="too long"):
            PathValidator.validate_project_name("a" * 256)

    def test_validate_filename_valid(self):
        """Test valid filenames."""
        valid_filenames = [
            "test.py",
            "script.sh",
            "config.json",
            "README.md",
        ]
        for filename in valid_filenames:
            result = PathValidator.validate_filename(filename)
            assert result == filename

    def test_validate_filename_path_separators(self):
        """Test rejection of path separators in filenames."""
        invalid_filenames = [
            "../test.py",
            "dir/file.sh",
            "..\\script.ps1",
            "C:\\file.txt",
        ]
        for filename in invalid_filenames:
            with pytest.raises(SecurityError, match="path separators"):
                PathValidator.validate_filename(filename)

    def test_validate_filename_path_traversal(self):
        """Test rejection of path traversal in filenames."""
        with pytest.raises(SecurityError, match="cannot contain"):
            PathValidator.validate_filename("..test")

    def test_ensure_within_directory_valid(self, tmp_path):
        """Test path is correctly validated when within base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        safe_path = base_dir / "subdir" / "file.txt"
        result = PathValidator.ensure_within_directory(safe_path, base_dir)

        assert str(result).startswith(str(base_dir.resolve()))

    def test_ensure_within_directory_traversal(self, tmp_path):
        """Test rejection of path traversal outside base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        unsafe_path = base_dir / ".." / "outside" / "file.txt"

        with pytest.raises(SecurityError, match="outside allowed directory"):
            PathValidator.ensure_within_directory(unsafe_path, base_dir)


class TestSafeSubprocess:
    """Test safe subprocess execution."""

    def test_run_valid_command(self):
        """Test execution of whitelisted command."""
        result = SafeSubprocess.run(
            ["python", "--version"],
            timeout=5,
        )
        assert result.returncode == 0
        assert "Python" in result.stdout or "Python" in result.stderr

    def test_run_command_not_in_whitelist(self):
        """Test rejection of non-whitelisted command."""
        with pytest.raises(SecurityError, match="not in whitelist"):
            SafeSubprocess.run(["curl", "http://evil.com"])

    def test_run_with_timeout(self):
        """Test timeout enforcement."""
        with pytest.raises(subprocess.TimeoutExpired):
            SafeSubprocess.run(
                ["python", "-c", "import time; time.sleep(10)"],
                timeout=1,
            )

    def test_run_timeout_too_long(self):
        """Test rejection of excessive timeout."""
        with pytest.raises(SecurityError, match="cannot exceed 600"):
            SafeSubprocess.run(
                ["python", "--version"],
                timeout=700,
            )

    def test_run_invalid_cwd(self, tmp_path):
        """Test rejection of non-existent working directory."""
        invalid_cwd = tmp_path / "nonexistent"

        with pytest.raises(SecurityError, match="does not exist"):
            SafeSubprocess.run(
                ["python", "--version"],
                cwd=invalid_cwd,
            )

    def test_run_cwd_not_directory(self, tmp_path):
        """Test rejection of non-directory working directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(SecurityError, match="not a directory"):
            SafeSubprocess.run(
                ["python", "--version"],
                cwd=file_path,
            )

    def test_run_empty_command(self):
        """Test rejection of empty command."""
        with pytest.raises(SecurityError, match="cannot be empty"):
            SafeSubprocess.run([])


class TestValidateScriptPath:
    """Test script path validation."""

    def test_validate_script_path_valid(self, tmp_path):
        """Test validation of legitimate script within allowed directory."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        script = scripts_dir / "test.sh"
        script.write_text("#!/bin/bash\necho 'test'")

        result = validate_script_path(script, scripts_dir)
        assert result == script.resolve()

    def test_validate_script_path_outside_directory(self, tmp_path):
        """Test rejection of script outside allowed directory."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        script = outside_dir / "evil.sh"
        script.write_text("#!/bin/bash\nrm -rf /")

        with pytest.raises(SecurityError, match="outside allowed directory"):
            validate_script_path(script, scripts_dir)

    def test_validate_script_path_nonexistent(self, tmp_path):
        """Test rejection of non-existent script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        script = scripts_dir / "nonexistent.sh"

        with pytest.raises(SecurityError, match="does not exist"):
            validate_script_path(script, scripts_dir)

    def test_validate_script_path_not_file(self, tmp_path):
        """Test rejection of directory instead of file."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        subdir = scripts_dir / "subdir"
        subdir.mkdir()

        with pytest.raises(SecurityError, match="not a file"):
            validate_script_path(subdir, scripts_dir)
