#!/usr/bin/env python3
"""
Security utilities for BAZINGA CLI.

Provides safe subprocess execution, path validation, and input sanitization.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional, List


class SecurityError(Exception):
    """Raised when a security validation fails."""
    pass


class PathValidator:
    """Validates and sanitizes file paths to prevent path traversal attacks."""

    # Reserved names on Windows
    RESERVED_NAMES = {
        'aux', 'con', 'nul', 'prn',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }

    @staticmethod
    def validate_project_name(name: str) -> str:
        """
        Validate project name is safe and follows conventions.

        Args:
            name: Project name to validate

        Returns:
            The validated name

        Raises:
            SecurityError: If name is invalid or unsafe
        """
        # Check length
        if not name or len(name) < 1:
            raise SecurityError("Project name cannot be empty")

        if len(name) > 255:
            raise SecurityError("Project name too long (max 255 characters)")

        # Check for path traversal attempts
        if ".." in name:
            raise SecurityError("Project name cannot contain '..'")

        if name.startswith("/") or name.startswith("\\"):
            raise SecurityError("Project name cannot start with / or \\")

        # Check for null bytes
        if "\x00" in name:
            raise SecurityError("Project name cannot contain null bytes")

        # Allow letters, numbers, hyphens, underscores, and dots
        if not re.match(r'^[a-zA-Z0-9._-]+$', name):
            raise SecurityError(
                "Project name can only contain letters, numbers, hyphens, underscores, and dots"
            )

        # Check for reserved names (Windows)
        if name.lower() in PathValidator.RESERVED_NAMES:
            raise SecurityError(f"'{name}' is a reserved system name")

        return name

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate filename doesn't contain path traversal or dangerous characters.

        Args:
            filename: Filename to validate

        Returns:
            The validated filename

        Raises:
            SecurityError: If filename is unsafe
        """
        # Check for path separators (should be just a name, not a path)
        if "/" in filename or "\\" in filename:
            raise SecurityError(f"Filename cannot contain path separators: {filename}")

        # Check for path traversal
        if ".." in filename:
            raise SecurityError(f"Filename cannot contain '..': {filename}")

        # Check for null bytes
        if "\x00" in filename:
            raise SecurityError(f"Filename cannot contain null bytes: {filename}")

        # Check it's not empty
        if not filename or filename.strip() == "":
            raise SecurityError("Filename cannot be empty")

        return filename

    @staticmethod
    def ensure_within_directory(path: Path, base_dir: Path) -> Path:
        """
        Ensure a path resolves to within a base directory (prevent directory traversal).

        Args:
            path: Path to validate
            base_dir: Base directory that path must be within

        Returns:
            The resolved path

        Raises:
            SecurityError: If path is outside base_dir
        """
        try:
            # Resolve both paths to absolute paths
            resolved_path = path.resolve()
            resolved_base = base_dir.resolve()

            # Check if resolved_path is within resolved_base
            resolved_path.relative_to(resolved_base)

            return resolved_path
        except ValueError:
            raise SecurityError(
                f"Path {path} is outside allowed directory {base_dir}"
            )


class SafeSubprocess:
    """Safe subprocess execution with command whitelisting and validation."""

    # Whitelist of allowed commands
    ALLOWED_COMMANDS = {
        'bash', 'sh',
        'pwsh', 'powershell',
        'python', 'python3',
        'git',
        'npm', 'node',
        'pytest',
        'go',
        'java', 'mvn', 'gradle',
        'ruby', 'gem', 'bundle',
    }

    @staticmethod
    def run(
        command: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 120,
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Run a subprocess with security validations.

        Args:
            command: Command and arguments as a list
            cwd: Working directory (validated to exist)
            timeout: Timeout in seconds (max 600)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit

        Returns:
            CompletedProcess object

        Raises:
            SecurityError: If command is not allowed or validation fails
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If check=True and command fails
        """
        if not command or len(command) == 0:
            raise SecurityError("Command cannot be empty")

        # Validate command is in whitelist
        cmd_name = Path(command[0]).name.lower()
        if cmd_name not in SafeSubprocess.ALLOWED_COMMANDS:
            raise SecurityError(
                f"Command '{cmd_name}' not in whitelist. "
                f"Allowed: {', '.join(sorted(SafeSubprocess.ALLOWED_COMMANDS))}"
            )

        # Validate timeout
        if timeout > 600:
            raise SecurityError("Timeout cannot exceed 600 seconds (10 minutes)")

        # Validate cwd exists and is a directory
        if cwd is not None:
            if not cwd.exists():
                raise SecurityError(f"Working directory does not exist: {cwd}")

            if not cwd.is_dir():
                raise SecurityError(f"Working directory is not a directory: {cwd}")

        # Run subprocess with security settings
        try:
            return subprocess.run(
                command,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
                shell=False,  # SECURITY: Never use shell=True
            )
        except subprocess.TimeoutExpired as e:
            raise subprocess.TimeoutExpired(
                cmd=e.cmd,
                timeout=e.timeout,
                output=getattr(e, 'output', None),
                stderr=getattr(e, 'stderr', None)
            )
        except subprocess.CalledProcessError as e:
            raise e


def validate_script_path(script_path: Path, allowed_dir: Path) -> Path:
    """
    Validate a script path is safe to execute.

    Args:
        script_path: Path to the script
        allowed_dir: Directory that script must be within

    Returns:
        The validated path

    Raises:
        SecurityError: If script path is unsafe
    """
    # Ensure path is within allowed directory
    validated = PathValidator.ensure_within_directory(script_path, allowed_dir)

    # Ensure it's a file
    if not validated.exists():
        raise SecurityError(f"Script does not exist: {script_path}")

    if not validated.is_file():
        raise SecurityError(f"Script path is not a file: {script_path}")

    return validated
