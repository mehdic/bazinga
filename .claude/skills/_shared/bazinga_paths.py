#!/usr/bin/env python3
"""
Centralized path management for BAZINGA skills.

This module provides robust path resolution that works across:
- Development environment (bazinga repo)
- Installed environments (client projects after `bazinga install`)
- Different operating systems (Windows, macOS, Linux)
- Edge cases (monorepos, symlinks, moved directories)

Usage:
    from bazinga_paths import get_project_root, get_db_path, get_skills_dir

    # Auto-detect paths
    root = get_project_root()
    db = get_db_path()

    # Or use explicit override
    root = get_project_root(override="/path/to/project")
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Cache for detected paths (avoid repeated filesystem walks)
_cached_project_root: Optional[Path] = None
_cached_detection_source: Optional[str] = None


def _is_bazinga_project_root(path: Path) -> Tuple[bool, str]:
    """
    Check if a directory is a valid BAZINGA project root.

    A valid root has BOTH:
    - .claude/ directory (Claude Code configuration)
    - bazinga/ directory (BAZINGA state/config)

    Returns:
        Tuple of (is_valid, reason_string)
    """
    claude_dir = path / '.claude'
    bazinga_dir = path / 'bazinga'

    has_claude = claude_dir.exists() and claude_dir.is_dir()
    has_bazinga = bazinga_dir.exists() and bazinga_dir.is_dir()

    if has_claude and has_bazinga:
        return True, "found .claude/ and bazinga/"
    elif has_claude:
        return False, "found .claude/ but missing bazinga/"
    elif has_bazinga:
        return False, "found bazinga/ but missing .claude/"
    else:
        return False, "missing both .claude/ and bazinga/"


def _detect_from_script_location(script_path: Optional[Path] = None) -> Optional[Path]:
    """
    Detect project root by walking up from a script's location.

    This is the PREFERRED method as it doesn't depend on CWD.

    Args:
        script_path: Path to the calling script. If None, uses the caller's __file__.

    Returns:
        Project root Path or None if not found.
    """
    if script_path is None:
        # Try to get the caller's __file__ from the call stack
        # This handles cases where bazinga_paths is imported
        import inspect
        for frame_info in inspect.stack():
            frame_file = frame_info.filename
            # Skip this module and standard library
            if 'bazinga_paths' not in frame_file and 'importlib' not in frame_file:
                script_path = Path(frame_file).resolve()
                break

    if script_path is None:
        return None

    # Resolve symlinks to get real path
    try:
        script_path = script_path.resolve()
    except (OSError, RuntimeError):
        return None

    # Walk up from script location
    current = script_path.parent
    visited = set()

    while current != current.parent:
        # Prevent infinite loops (symlink cycles)
        real_current = current.resolve()
        if real_current in visited:
            break
        visited.add(real_current)

        is_root, _ = _is_bazinga_project_root(current)
        if is_root:
            return current

        current = current.parent

    return None


def _detect_from_cwd() -> Optional[Path]:
    """
    Detect project root by walking up from current working directory.

    This is the FALLBACK method when script location detection fails.

    Returns:
        Project root Path or None if not found.
    """
    try:
        current = Path.cwd().resolve()
    except (OSError, RuntimeError):
        return None

    visited = set()

    while current != current.parent:
        real_current = current.resolve()
        if real_current in visited:
            break
        visited.add(real_current)

        is_root, _ = _is_bazinga_project_root(current)
        if is_root:
            return current

        current = current.parent

    return None


def _detect_from_env_file() -> Optional[Path]:
    """
    Read project root from .bazinga/paths.env if it exists.

    This is an OPTIONAL optimization - scripts work without it.

    Returns:
        Project root Path or None if env file doesn't exist or is invalid.
    """
    # First need to find the env file, which requires knowing the root...
    # This creates a chicken-and-egg problem. We solve it by:
    # 1. Check if BAZINGA_ROOT env var is set
    # 2. Try to find .bazinga/paths.env relative to CWD

    env_root = os.environ.get('BAZINGA_ROOT')
    if env_root:
        env_path = Path(env_root)
        if env_path.exists():
            is_root, _ = _is_bazinga_project_root(env_path)
            if is_root:
                return env_path

    # Try CWD-relative
    try:
        cwd = Path.cwd()
        env_file = cwd / '.bazinga' / 'paths.env'
        if env_file.exists():
            # Parse the env file for BAZINGA_ROOT
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('BAZINGA_ROOT='):
                        value = line.split('=', 1)[1].strip('"\'')
                        candidate = Path(value)
                        if candidate.exists():
                            is_root, _ = _is_bazinga_project_root(candidate)
                            if is_root:
                                return candidate
    except (OSError, IOError):
        pass

    return None


def get_project_root(
    override: Optional[str] = None,
    script_path: Optional[str] = None,
    _use_cache: bool = True
) -> Path:
    """
    Get the BAZINGA project root directory.

    Detection order:
    1. Explicit override (--project-root flag)
    2. BAZINGA_ROOT environment variable
    3. .bazinga/paths.env file (if exists)
    4. Script location (walk up from __file__)
    5. Current working directory (walk up from CWD)

    Args:
        override: Explicit path override (highest priority)
        script_path: Path to the calling script (for detection)
        _use_cache: Whether to use cached result (default True)

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root cannot be determined
    """
    global _cached_project_root, _cached_detection_source

    # 1. Explicit override (highest priority)
    if override:
        path = Path(override).resolve()
        is_root, reason = _is_bazinga_project_root(path)
        if not is_root:
            raise RuntimeError(
                f"Override path '{override}' is not a valid BAZINGA project root: {reason}"
            )
        # Cache the override for subsequent calls without override
        _cached_project_root = path
        _cached_detection_source = "explicit override"
        return path

    # 2. Check cache
    if _use_cache and _cached_project_root is not None:
        # Validate cache is still valid
        if _cached_project_root.exists():
            is_root, _ = _is_bazinga_project_root(_cached_project_root)
            if is_root:
                return _cached_project_root
        # Cache invalid, clear it
        _cached_project_root = None
        _cached_detection_source = None

    # 3. Environment variable
    env_root = os.environ.get('BAZINGA_ROOT')
    if env_root:
        path = Path(env_root).resolve()
        if path.exists():
            is_root, _ = _is_bazinga_project_root(path)
            if is_root:
                _cached_project_root = path
                _cached_detection_source = "BAZINGA_ROOT environment variable"
                return path

    # 4. Env file
    env_file_root = _detect_from_env_file()
    if env_file_root:
        _cached_project_root = env_file_root
        _cached_detection_source = ".bazinga/paths.env file"
        return env_file_root

    # 5. Script location (preferred auto-detection)
    script_loc = Path(script_path).resolve() if script_path else None
    script_root = _detect_from_script_location(script_loc)
    if script_root:
        _cached_project_root = script_root
        _cached_detection_source = "script location"
        return script_root

    # 6. CWD (fallback)
    cwd_root = _detect_from_cwd()
    if cwd_root:
        _cached_project_root = cwd_root
        _cached_detection_source = "current working directory"
        return cwd_root

    # Failed to detect
    raise RuntimeError(
        "Could not detect BAZINGA project root. "
        "Ensure you are in a directory with both .claude/ and bazinga/ folders, "
        "or set BAZINGA_ROOT environment variable, "
        "or pass --project-root flag."
    )


def get_db_path(override: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Get the path to the BAZINGA SQLite database.

    Args:
        override: Explicit database path override (--db flag)
        project_root: Pre-computed project root (avoids re-detection)

    Returns:
        Path to bazinga.db
    """
    if override:
        return Path(override).resolve()

    root = project_root or get_project_root()
    return root / 'bazinga' / 'bazinga.db'


def get_skills_dir(project_root: Optional[Path] = None) -> Path:
    """
    Get the path to the skills directory.

    Args:
        project_root: Pre-computed project root (avoids re-detection)

    Returns:
        Path to .claude/skills/
    """
    root = project_root or get_project_root()
    return root / '.claude' / 'skills'


def get_artifacts_dir(session_id: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """
    Get the path to the artifacts directory.

    Args:
        session_id: If provided, returns session-specific artifacts dir
        project_root: Pre-computed project root (avoids re-detection)

    Returns:
        Path to bazinga/artifacts/ or bazinga/artifacts/{session_id}/
    """
    root = project_root or get_project_root()
    artifacts = root / 'bazinga' / 'artifacts'
    if session_id:
        return artifacts / session_id
    return artifacts


def get_agents_dir(project_root: Optional[Path] = None) -> Path:
    """
    Get the path to the agents directory.

    Args:
        project_root: Pre-computed project root (avoids re-detection)

    Returns:
        Path to agents/
    """
    root = project_root or get_project_root()
    return root / 'agents'


def get_detection_info() -> dict:
    """
    Get information about how the project root was detected.

    Useful for debugging path issues.

    Returns:
        Dict with detection details
    """
    global _cached_project_root, _cached_detection_source

    try:
        root = get_project_root()
        return {
            "project_root": str(root),
            "detection_source": _cached_detection_source or "unknown",
            "db_path": str(get_db_path(project_root=root)),
            "skills_dir": str(get_skills_dir(project_root=root)),
            "artifacts_dir": str(get_artifacts_dir(project_root=root)),
            "agents_dir": str(get_agents_dir(project_root=root)),
            "cwd": str(Path.cwd()),
            "env_var_set": bool(os.environ.get('BAZINGA_ROOT')),
        }
    except RuntimeError as e:
        return {
            "error": str(e),
            "cwd": str(Path.cwd()),
            "env_var_set": bool(os.environ.get('BAZINGA_ROOT')),
        }


def clear_cache():
    """Clear the cached project root. Useful for testing."""
    global _cached_project_root, _cached_detection_source
    _cached_project_root = None
    _cached_detection_source = None


def add_shared_to_path():
    """
    Add the _shared directory to sys.path for imports.

    Call this at the top of scripts that need bazinga_paths:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / '_shared'))
        from bazinga_paths import get_project_root

    Or use this helper after initial import:
        from bazinga_paths import add_shared_to_path
        add_shared_to_path()
    """
    shared_dir = Path(__file__).parent.resolve()
    shared_str = str(shared_dir)
    if shared_str not in sys.path:
        sys.path.insert(0, shared_str)


# Command-line interface for debugging
if __name__ == '__main__':
    import json
    info = get_detection_info()
    print(json.dumps(info, indent=2))
