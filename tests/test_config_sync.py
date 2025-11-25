"""
Test that ALLOWED_CONFIG_FILES in __init__.py stays in sync with
force-include entries in pyproject.toml.

This prevents the scenario where a developer adds a new config file
to pyproject.toml but forgets to add it to the Python allowlist,
resulting in files being packaged but never installed/copied.
"""

import tomllib
from pathlib import Path

import pytest


def get_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


def test_allowed_config_files_matches_pyproject():
    """
    Verify that BazingaSetup.ALLOWED_CONFIG_FILES matches the config files
    in pyproject.toml's force-include section (excluding templates).

    This test catches the case where someone adds a new config file to
    pyproject.toml but forgets to update ALLOWED_CONFIG_FILES.
    Supports any file type (JSON, YAML, etc.) - not just .json files.
    """
    # Import here to avoid circular imports during test collection
    from bazinga_cli import BazingaSetup

    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    # Get force-include entries
    force_include = (
        pyproject.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
        .get("force-include", {})
    )

    # Extract config files from force-include keys (excluding templates directory)
    # Format: "bazinga/model_selection.json" = "bazinga_cli/bazinga/model_selection.json"
    # Templates are handled separately by copy_templates(), not ALLOWED_CONFIG_FILES
    pyproject_configs = set()
    for src_path in force_include.keys():
        if src_path.startswith("bazinga/") and "templates" not in src_path:
            # Extract just the filename
            filename = Path(src_path).name
            pyproject_configs.add(filename)

    # Get ALLOWED_CONFIG_FILES from BazingaSetup
    allowed_configs = set(BazingaSetup.ALLOWED_CONFIG_FILES)

    # Check for files in pyproject but not in ALLOWED_CONFIG_FILES
    missing_from_allowlist = pyproject_configs - allowed_configs
    if missing_from_allowlist:
        pytest.fail(
            f"Config files in pyproject.toml force-include but missing from "
            f"BazingaSetup.ALLOWED_CONFIG_FILES: {missing_from_allowlist}\n"
            f"Add these to ALLOWED_CONFIG_FILES in src/bazinga_cli/__init__.py"
        )

    # Check for files in ALLOWED_CONFIG_FILES but not in pyproject
    missing_from_pyproject = allowed_configs - pyproject_configs
    if missing_from_pyproject:
        pytest.fail(
            f"Config files in ALLOWED_CONFIG_FILES but missing from "
            f"pyproject.toml force-include: {missing_from_pyproject}\n"
            f"Add these to [tool.hatch.build.targets.wheel.force-include] in pyproject.toml"
        )


def test_config_files_exist_in_source():
    """
    Verify that all ALLOWED_CONFIG_FILES actually exist in the source
    bazinga/ directory.
    """
    from bazinga_cli import BazingaSetup

    project_root = get_project_root()
    bazinga_dir = project_root / "bazinga"

    missing_files = []
    for filename in BazingaSetup.ALLOWED_CONFIG_FILES:
        if not (bazinga_dir / filename).exists():
            missing_files.append(filename)

    if missing_files:
        pytest.fail(
            f"Config files in ALLOWED_CONFIG_FILES but missing from "
            f"bazinga/ directory: {missing_files}"
        )
