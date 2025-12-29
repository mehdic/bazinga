#!/usr/bin/env python3
"""
BAZINGA CLI - Multi-Agent Orchestration System for Claude Code

A sophisticated multi-agent orchestration system that coordinates autonomous
development teams including Project Manager, Developers, QA Expert, Tech Lead,
Investigator, and Requirements Engineer.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .security import PathValidator, SafeSubprocess, SecurityError, validate_script_path
from .telemetry import track_command

__version__ = "1.1.0"

# GitHub repository for release downloads
GITHUB_REPO = "mehdic/bazinga"

console = Console()
app = typer.Typer(
    name="bazinga",
    help="BAZINGA - Multi-Agent Orchestration System for Claude Code",
    add_completion=False,
    rich_markup_mode="rich",
)


class BazingaSetup:
    """Handles BAZINGA installation and setup."""

    # Explicit allowlist of config files to copy/distribute
    # Must match force-include entries in pyproject.toml
    # This prevents copying runtime state files (pm_state.json, etc.) in dev mode
    ALLOWED_CONFIG_FILES = [
        "model_selection.json",
        "challenge_levels.json",
        "skills_config.json",
    ]

    def __init__(self, source_dir: Optional[Path] = None):
        """
        Initialize setup handler.

        Args:
            source_dir: Source directory containing bazinga files.
                       If None, uses the package installation directory.
        """
        if source_dir is None:
            # Try multiple locations to find the bazinga files

            # Option 1: Development mode (running from git clone)
            dev_dir = Path(__file__).parent.parent.parent
            if (dev_dir / "agents").exists():
                self.source_dir = dev_dir
            else:
                # Option 2: Installed mode (via pip/uvx)
                # Files are in share/bazinga_cli relative to sys.prefix
                import sys
                installed_dir = Path(sys.prefix) / "share" / "bazinga_cli"
                if installed_dir.exists():
                    self.source_dir = installed_dir
                else:
                    # Fallback: try relative to the package
                    self.source_dir = dev_dir
        else:
            self.source_dir = source_dir

    def _get_config_source(self, relative_path: str) -> Optional[Path]:
        """
        Resolve config path with priority:
        1. Package directory (bundled with code - always version-matched)
        2. Shared data directory (legacy/system installs)
        3. Project root (editable/dev install)

        Priority order matters: Package dir is checked first to avoid
        stale configs from previous installs in shared-data location.

        Args:
            relative_path: Path relative to source (e.g., "templates")

        Returns:
            Resolved Path if found, None otherwise
        """
        # 1. Check package directory first (force-included in wheels)
        # This ensures version-matched configs, avoiding stale shared-data
        pkg_path = Path(__file__).parent / relative_path
        if pkg_path.exists():
            return pkg_path

        # 2. Check shared data directory (legacy installs, agents, etc.)
        path = self.source_dir / relative_path
        if path.exists():
            return path

        # 3. Check project root (development/editable mode fallback)
        # Iterate upward to find pyproject.toml marker (robust to refactoring)
        current = Path(__file__).resolve().parent
        for _ in range(5):  # Search up to 5 levels
            if (current / "pyproject.toml").exists():
                dev_path = current / relative_path
                if dev_path.exists():
                    return dev_path
                break  # Found project root but path doesn't exist
            current = current.parent

        return None

    def get_agent_files(self) -> list[Path]:
        """Get list of agent markdown files."""
        agents_dir = self.source_dir / "agents"
        if agents_dir.exists():
            return list(agents_dir.glob("*.md"))
        return []

    def copy_agents(self, target_dir: Path) -> bool:
        """Copy agent files to target .claude/agents directory."""
        agents_dir = target_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        agent_files = self.get_agent_files()
        if not agent_files:
            console.print("[yellow]⚠️  No agent files found in source[/yellow]")
            return False

        for agent_file in agent_files:
            try:
                # SECURITY: Validate filename doesn't contain path traversal
                safe_filename = PathValidator.validate_filename(agent_file.name)
                dest = agents_dir / safe_filename

                # SECURITY: Ensure destination is within agents_dir
                PathValidator.ensure_within_directory(dest, agents_dir)

                shutil.copy2(agent_file, dest)
                console.print(f"  ✓ Copied {safe_filename}")
            except SecurityError as e:
                console.print(f"[red]✗ Skipping unsafe file {agent_file.name}: {e}[/red]")
                continue

        return True

    def copy_scripts(self, target_dir: Path, script_type: str = "sh") -> bool:
        """
        Copy scripts to target bazinga/scripts directory.

        Args:
            target_dir: Target directory for installation
            script_type: "sh" for POSIX shell or "ps" for PowerShell
        """
        scripts_dir = target_dir / "bazinga" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Determine which extension to copy based on script type
        script_extension = ".sh" if script_type == "sh" else ".ps1"

        copied_count = 0

        # Copy from both source locations:
        # 1. source_dir/scripts (main scripts folder)
        # 2. source_dir/bazinga/scripts (bazinga-specific scripts like build-baseline.sh)
        source_locations = [
            self.source_dir / "scripts",
            self.source_dir / "bazinga" / "scripts",
        ]

        for source_scripts in source_locations:
            if not source_scripts.exists():
                continue

            for script_file in source_scripts.glob("*"):
                if script_file.is_file():
                    # Skip non-script files (README, etc.) or wrong script type
                    if script_file.suffix in [".sh", ".ps1"]:
                        if script_file.suffix != script_extension:
                            continue  # Skip scripts of the other type

                    try:
                        # SECURITY: Validate filename doesn't contain path traversal
                        safe_filename = PathValidator.validate_filename(script_file.name)
                        dest = scripts_dir / safe_filename

                        # SECURITY: Ensure destination is within scripts_dir
                        PathValidator.ensure_within_directory(dest, scripts_dir)

                        shutil.copy2(script_file, dest)

                        # Make shell scripts executable on Unix-like systems
                        if script_file.suffix == ".sh" and os.name != 'nt':
                            dest.chmod(0o755)

                        console.print(f"  ✓ Copied {safe_filename}")
                        copied_count += 1
                    except SecurityError as e:
                        console.print(f"[red]✗ Skipping unsafe script {script_file.name}: {e}[/red]")
                        continue

            # Also copy README if it exists
            readme_file = source_scripts / "README.md"
            if readme_file.exists():
                try:
                    safe_filename = PathValidator.validate_filename("README.md")
                    dest = scripts_dir / safe_filename
                    PathValidator.ensure_within_directory(dest, scripts_dir)
                    shutil.copy2(readme_file, dest)
                    console.print(f"  ✓ Copied README.md")
                except SecurityError as e:
                    console.print(f"[red]✗ Skipping unsafe README: {e}[/red]")

        return copied_count > 0

    # Command prefixes to exclude from CLI install/update (development-only commands)
    EXCLUDED_COMMAND_PREFIXES = {"speckit."}

    def copy_commands(self, target_dir: Path) -> bool:
        """Copy commands to target .claude/commands directory."""
        commands_dir = target_dir / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)

        source_commands = self.source_dir / ".claude" / "commands"
        if not source_commands.exists():
            return False

        for cmd_file in source_commands.glob("*.md"):
            # Skip excluded command prefixes (development-only)
            if any(cmd_file.name.startswith(prefix) for prefix in self.EXCLUDED_COMMAND_PREFIXES):
                console.print(f"  [dim]⏭️  Skipping {cmd_file.name} (development-only)[/dim]")
                continue
            shutil.copy2(cmd_file, commands_dir / cmd_file.name)
            console.print(f"  ✓ Copied {cmd_file.name}")

        return True

    # Skills to exclude from CLI install/update (development-only skills)
    EXCLUDED_SKILLS = {"skill-creator"}

    def copy_skills(self, target_dir: Path, script_type: str = "sh") -> bool:
        """
        Copy Skills to target .claude/skills directory.

        Args:
            target_dir: Target directory for installation
            script_type: "sh" for bash scripts or "ps" for PowerShell scripts
        """
        skills_dir = target_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        source_skills = self.source_dir / ".claude" / "skills"
        if not source_skills.exists():
            return False

        script_extension = ".sh" if script_type == "sh" else ".ps1"
        copied_count = 0

        # Copy each skill directory
        for skill_dir in source_skills.iterdir():
            if skill_dir.is_dir():
                # Skip excluded skills (development-only)
                if skill_dir.name in self.EXCLUDED_SKILLS:
                    console.print(f"  [dim]⏭️  Skipping {skill_dir.name} (development-only)[/dim]")
                    continue
                dest_skill_dir = skills_dir / skill_dir.name
                dest_skill_dir.mkdir(exist_ok=True)

                # Copy SKILL.md
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    shutil.copy2(skill_md, dest_skill_dir / "SKILL.md")
                    console.print(f"  ✓ Copied {skill_dir.name}/SKILL.md")
                    copied_count += 1

                # Copy all subdirectories and their contents (scripts/, references/, etc.)
                for item in skill_dir.iterdir():
                    if item.is_dir():
                        # Recursively copy entire subdirectory
                        dest_subdir = dest_skill_dir / item.name
                        if dest_subdir.exists():
                            shutil.rmtree(dest_subdir)
                        shutil.copytree(item, dest_subdir)

                        # Make Python and shell scripts executable
                        for script_file in dest_subdir.rglob("*"):
                            if script_file.is_file():
                                if script_file.suffix in [".py", ".sh"] and os.name != 'nt':
                                    script_file.chmod(0o755)

                        console.print(f"  ✓ Copied {skill_dir.name}/{item.name}/")
                        copied_count += 1

                # Copy other files in skill root (Python, shell scripts, LICENSE, etc.)
                for script_file in skill_dir.glob("*"):
                    if script_file.is_file() and script_file.name != "SKILL.md":
                        # Copy Python files (for Python-based Skills)
                        if script_file.suffix == ".py":
                            dest = dest_skill_dir / script_file.name
                            shutil.copy2(script_file, dest)

                            # Make Python scripts executable on Unix-like systems
                            if os.name != 'nt':
                                dest.chmod(0o755)

                            console.print(f"  ✓ Copied {skill_dir.name}/{script_file.name}")
                            copied_count += 1

                        # Copy shell/PowerShell scripts (for shell-based Skills)
                        elif script_file.suffix in [".sh", ".ps1"]:
                            if script_file.suffix == script_extension:
                                dest = dest_skill_dir / script_file.name
                                shutil.copy2(script_file, dest)

                                # Make shell scripts executable on Unix-like systems
                                if script_file.suffix == ".sh" and os.name != 'nt':
                                    dest.chmod(0o755)

                                console.print(f"  ✓ Copied {skill_dir.name}/{script_file.name}")
                                copied_count += 1

                        # Copy other files (LICENSE.txt, README.md, etc.)
                        elif script_file.suffix in [".txt", ".md"] and script_file.name not in ["SKILL.md", "README.md"]:
                            dest = dest_skill_dir / script_file.name
                            shutil.copy2(script_file, dest)
                            console.print(f"  ✓ Copied {skill_dir.name}/{script_file.name}")
                            copied_count += 1

        return copied_count > 0

    def copy_templates(self, target_dir: Path) -> bool:
        """
        Copy templates to target bazinga/templates/ directory.

        Templates are installed to bazinga/templates/ so that agent files
        can reference them with consistent paths in both dev and installed modes.

        Args:
            target_dir: Target directory for installation

        Returns:
            True if templates were copied successfully, False otherwise
        """
        templates_dir = target_dir / "bazinga" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Use helper for path resolution with legacy fallback
        source_templates = self._get_config_source("templates")
        if not source_templates:
            # Legacy fallback: bazinga/templates
            source_templates = self._get_config_source("bazinga/templates")
            if not source_templates:
                console.print("[yellow]⚠️  No templates found in source[/yellow]")
                console.print("[dim]   Checked: package dir, shared-data, project root[/dim]")
                console.print("[dim]   Hint: Update CLI with 'uv tool upgrade bazinga-cli' or reinstall[/dim]")
                return False

        copied_count = 0

        # Copy top-level .md files
        for template_file in source_templates.glob("*.md"):
            try:
                # SECURITY: Validate filename doesn't contain path traversal
                safe_filename = PathValidator.validate_filename(template_file.name)
                dest = templates_dir / safe_filename

                # SECURITY: Ensure destination is within templates_dir
                PathValidator.ensure_within_directory(dest, templates_dir)

                shutil.copy2(template_file, dest)
                console.print(f"  ✓ Copied {safe_filename}")
                copied_count += 1
            except SecurityError as e:
                console.print(f"[red]✗ Skipping unsafe file {template_file.name}: {e}[/red]")
                continue

        # Copy subdirectories (e.g., specializations/)
        for subdir in source_templates.iterdir():
            if subdir.is_dir():
                try:
                    # SECURITY: Validate directory name
                    safe_dirname = PathValidator.validate_filename(subdir.name)
                    dest_subdir = templates_dir / safe_dirname

                    # SECURITY: Ensure destination is within templates_dir
                    PathValidator.ensure_within_directory(dest_subdir, templates_dir)

                    # Remove existing and copy fresh
                    if dest_subdir.exists():
                        shutil.rmtree(dest_subdir)
                    shutil.copytree(subdir, dest_subdir)

                    # Count files in subdirectory
                    subdir_files = list(dest_subdir.rglob("*.md"))
                    console.print(f"  ✓ Copied {safe_dirname}/ ({len(subdir_files)} files)")
                    copied_count += len(subdir_files)
                except SecurityError as e:
                    console.print(f"[red]✗ Skipping unsafe directory {subdir.name}: {e}[/red]")
                    continue

        return copied_count > 0

    def copy_claude_templates(self, target_dir: Path) -> bool:
        """
        Copy .claude/templates/ to target .claude/templates directory.

        This includes project_context.template.json which is used as a fallback
        when the Tech Stack Scout doesn't create project_context.json.

        Args:
            target_dir: Target directory for installation

        Returns:
            True if templates were copied successfully, False otherwise
        """
        templates_dir = target_dir / ".claude" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        source_templates = self.source_dir / ".claude" / "templates"
        if not source_templates.exists():
            console.print("[yellow]⚠️  No .claude/templates found in source[/yellow]")
            return False

        copied_count = 0

        # Copy all files (*.md, *.json, etc.)
        for template_file in source_templates.iterdir():
            if template_file.is_file():
                try:
                    safe_filename = PathValidator.validate_filename(template_file.name)
                    dest = templates_dir / safe_filename
                    PathValidator.ensure_within_directory(dest, templates_dir)
                    shutil.copy2(template_file, dest)
                    console.print(f"  ✓ Copied {safe_filename}")
                    copied_count += 1
                except SecurityError as e:
                    console.print(f"[red]✗ Skipping unsafe file {template_file.name}: {e}[/red]")
                    continue

        return copied_count > 0

    def copy_mini_dashboard(self, target_dir: Path) -> bool:
        """
        Copy mini-dashboard to target bazinga/mini-dashboard/ directory.

        The mini-dashboard is a lightweight Flask + HTML dashboard for
        monitoring BAZINGA orchestration sessions without npm dependencies.

        Args:
            target_dir: Target directory for installation

        Returns:
            True if mini-dashboard was copied successfully, False otherwise
        """
        mini_dashboard_dir = target_dir / "bazinga" / "mini-dashboard"

        # Find source mini-dashboard
        source_mini_dashboard = self._get_config_source("mini-dashboard")
        if not source_mini_dashboard or not source_mini_dashboard.exists():
            # Fallback: check project root (dev mode)
            source_mini_dashboard = self.source_dir / "mini-dashboard"
            if not source_mini_dashboard.exists():
                console.print("  [dim]Mini-dashboard not found in source[/dim]")
                return False

        try:
            # Copy mini-dashboard (exclude tests and __pycache__)
            if mini_dashboard_dir.exists():
                shutil.rmtree(mini_dashboard_dir)

            shutil.copytree(
                source_mini_dashboard,
                mini_dashboard_dir,
                ignore=shutil.ignore_patterns('tests', '__pycache__', '*.pyc', '.pytest_cache')
            )
            console.print("  [green]✓[/green] Mini-dashboard copied (run with: python bazinga/mini-dashboard/server.py)")
            return True
        except Exception as e:
            console.print(f"  [yellow]⚠️  Failed to copy mini-dashboard: {e}[/yellow]")
            return False

    def copy_bazinga_configs(self, target_dir: Path) -> bool:
        """
        Copy bazinga config files (JSON) to target bazinga/ directory.

        Args:
            target_dir: Target directory for installation

        Returns:
            True if configs were copied successfully, False otherwise
        """
        bazinga_dir = target_dir / "bazinga"
        bazinga_dir.mkdir(parents=True, exist_ok=True)

        # Use helper for path resolution (handles shared-data, package, and dev installs)
        source_bazinga = self._get_config_source("bazinga")
        if not source_bazinga:
            console.print("[yellow]⚠️  No bazinga config directory found in source[/yellow]")
            console.print("[dim]   Checked: package dir, shared-data, project root[/dim]")
            console.print("[dim]   Hint: Update CLI with 'uv tool upgrade bazinga-cli' or reinstall[/dim]")
            return False

        copied_count = 0
        for filename in self.ALLOWED_CONFIG_FILES:
            config_file = source_bazinga / filename
            if not config_file.exists():
                console.print(f"[yellow]⚠️  Warning: Expected config file not found: {filename}[/yellow]")
                continue

            try:
                # SECURITY: Validate filename doesn't contain path traversal
                safe_filename = PathValidator.validate_filename(filename)
                dest = bazinga_dir / safe_filename

                # SECURITY: Ensure destination is within bazinga_dir
                PathValidator.ensure_within_directory(dest, bazinga_dir)

                shutil.copy2(config_file, dest)
                console.print(f"  ✓ Copied {safe_filename}")
                copied_count += 1
            except SecurityError as e:
                console.print(f"[red]✗ Skipping unsafe file {filename}: {e}[/red]")
                continue

        # Copy config subdirectory (transitions.json, agent-markers.json)
        # Source: workflow/ (packaged as bazinga_cli/bazinga/config/ in wheel)
        # Dev: bazinga/config is symlink -> ../workflow
        source_config_dir = source_bazinga / "config"
        if source_config_dir.exists() and source_config_dir.is_dir():
            target_config_dir = bazinga_dir / "config"
            target_config_dir.mkdir(parents=True, exist_ok=True)

            for config_file in source_config_dir.glob("*.json"):
                try:
                    safe_filename = PathValidator.validate_filename(config_file.name)
                    dest = target_config_dir / safe_filename
                    PathValidator.ensure_within_directory(dest, target_config_dir)
                    shutil.copy2(config_file, dest)
                    console.print(f"  ✓ Copied config/{safe_filename}")
                    copied_count += 1
                except SecurityError as e:
                    console.print(f"[red]✗ Skipping unsafe file config/{config_file.name}: {e}[/red]")
                    continue

        return copied_count > 0

    def setup_config(self, target_dir: Path, is_update: bool = False) -> bool:
        """
        Setup global configuration, merging with existing config if present.

        DISABLED (2025-11-21): User requested to stop copying claude.md config files
        to client projects. Users should manage their own .claude/claude.md files.

        The session-start hook still loads .claude/claude.md if it exists, but the
        CLI no longer copies/creates this file automatically.

        Args:
            target_dir: Target directory for installation
            is_update: If True, replaces existing BAZINGA config with new version
        """
        console.print(f"  [dim]Skipping config setup (users manage their own .claude/claude.md)[/dim]")
        return True

    def install_compact_recovery_hook(self, target_dir: Path, script_type: str = None) -> bool:
        """
        Install the post-compaction recovery hook for BAZINGA orchestrator.

        This hook fires after context compaction and re-injects the orchestrator
        identity axioms to prevent role drift and background execution issues.

        The hook only outputs if it detects orchestration was in progress
        (checks transcript for /bazinga.orchestrate evidence).

        Args:
            target_dir: Target project directory
            script_type: "sh" or "ps" - if None, auto-detect from platform

        Returns:
            True if hook was installed/updated, False on failure
        """
        import json
        import platform

        # Auto-detect script type if not provided
        if script_type is None:
            script_type = "ps" if platform.system() == "Windows" else "sh"

        # Determine file extension and command format
        # Use safety flags for PowerShell: -NoProfile -NonInteractive
        # Quote the path to handle spaces
        if script_type == "ps":
            hook_filename = "bazinga-compact-recovery.ps1"
            # Prefer pwsh (PowerShell 7) if available, fall back to powershell (5.1)
            ps_exe = "pwsh" if shutil.which("pwsh") else "powershell"
            hook_command = f'{ps_exe} -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ".claude/hooks/bazinga-compact-recovery.ps1"'
        else:
            hook_filename = "bazinga-compact-recovery.sh"
            hook_command = ".claude/hooks/bazinga-compact-recovery.sh"

        # 1. Create hooks directory
        hooks_dir = target_dir / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # 2. Copy hook script from package
        source_hook = self._get_config_source("hooks")
        if source_hook:
            source_hook = source_hook / hook_filename
        else:
            # Try alternative locations
            for try_path in [
                self.source_dir / "hooks" / hook_filename,
                Path(__file__).parent / "hooks" / hook_filename,
            ]:
                if try_path.exists():
                    source_hook = try_path
                    break

        if not source_hook or not source_hook.exists():
            console.print(f"  [yellow]⚠️  Hook script not found: {hook_filename}[/yellow]")
            return False

        hook_dst = hooks_dir / hook_filename
        try:
            shutil.copy2(source_hook, hook_dst)
            # Make executable on Unix-like systems
            if script_type == "sh" and platform.system() != "Windows":
                hook_dst.chmod(0o755)
        except Exception as e:
            console.print(f"  [yellow]⚠️  Failed to copy hook script: {e}[/yellow]")
            return False

        # 3. Update settings.json to include the hook
        settings_path = target_dir / ".claude" / "settings.json"
        settings = {}
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text())
            except json.JSONDecodeError:
                console.print("  [yellow]⚠️  Existing settings.json is malformed, creating new[/yellow]")
                settings = {}

        # Ensure structure exists
        if "hooks" not in settings:
            settings["hooks"] = {}
        if "SessionStart" not in settings["hooks"]:
            settings["hooks"]["SessionStart"] = []

        # Define our hook configs - separate entries for compact and resume
        # Claude Code matchers are exact strings, not regex patterns
        # Use separate dict objects to avoid shared mutation issues
        bazinga_hooks = [
            {"matcher": "compact", "hooks": [{"type": "command", "command": hook_command}]},
            {"matcher": "resume", "hooks": [{"type": "command", "command": hook_command}]}
        ]

        def is_bazinga_hook(hook: dict) -> bool:
            """Check if a hook entry is a bazinga-compact-recovery hook (structural check)."""
            if not isinstance(hook, dict):
                return False
            hooks_list = hook.get("hooks", [])
            for h in hooks_list:
                if isinstance(h, dict):
                    cmd = h.get("command", "")
                    if "bazinga-compact-recovery" in cmd:
                        return True
            return False

        def hooks_match(existing: list, desired: list) -> bool:
            """Compare hooks by matcher and command, ignoring order."""
            def normalize(h):
                matcher = h.get("matcher", "")
                cmds = tuple(sorted(sub.get("command", "") for sub in h.get("hooks", []) if isinstance(sub, dict)))
                return (matcher, cmds)
            existing_set = set(normalize(h) for h in existing if is_bazinga_hook(h))
            desired_set = set(normalize(h) for h in desired)
            return existing_set == desired_set

        # Filter out existing bazinga hooks (structural check, not string-based)
        existing_hooks = settings["hooks"]["SessionStart"]
        other_hooks = [h for h in existing_hooks if not is_bazinga_hook(h)]

        # Check if hooks are already current (order-insensitive comparison)
        settings_changed = False
        if hooks_match(existing_hooks, bazinga_hooks):
            console.print(f"  ✓ Post-compaction recovery hook already current ({hook_filename})")
        else:
            # Update: keep other hooks, add our hooks
            settings["hooks"]["SessionStart"] = other_hooks + bazinga_hooks
            settings_changed = True
            console.print(f"  ✓ {'Updated' if any(is_bazinga_hook(h) for h in existing_hooks) else 'Installed'} post-compaction recovery hook ({hook_filename})")

        # Write settings if changed
        if settings_changed:
            try:
                settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False))
            except Exception as e:
                console.print(f"  [yellow]⚠️  Failed to update settings.json: {e}[/yellow]")
                return False

        return True

    def _replace_bazinga_section(self, content: str, new_bazinga_section: str) -> Optional[str]:
        """
        Replace the BAZINGA section in the content with a new version.

        Returns:
            Updated content with new BAZINGA section, or None if couldn't safely replace
        """
        # Try to find BAZINGA section boundaries
        # Look for the start marker
        start_patterns = [
            r'^---\s*$\s*^## ⚠️ CRITICAL: Orchestrator Role Enforcement',
            r'^## ⚠️ CRITICAL: Orchestrator Role Enforcement',
        ]

        content_before_bazinga = None

        for pattern in start_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                # Found the start of BAZINGA section
                content_before_bazinga = content[:match.start()].rstrip()
                break

        if content_before_bazinga is None:
            # Couldn't find BAZINGA section start
            return None

        # BAZINGA section goes to the end of file (it's the last section)
        # So we just take everything before it and append the new section
        updated_content = content_before_bazinga + '\n\n' + new_bazinga_section

        return updated_content

    def detect_script_type(self, target_dir: Path) -> str:
        """
        Detect which script type is currently installed.

        Returns:
            "sh" or "ps" based on what's found
        """
        scripts_dir = target_dir / ".claude" / "scripts"
        if not scripts_dir.exists():
            # Default to platform-appropriate type
            import platform
            return "ps" if platform.system() == "Windows" else "sh"

        # Check which init script exists
        if (scripts_dir / "init-orchestration.ps1").exists():
            return "ps"
        elif (scripts_dir / "init-orchestration.sh").exists():
            return "sh"
        else:
            # Default to platform-appropriate type
            import platform
            return "ps" if platform.system() == "Windows" else "sh"

    def run_init_script(self, target_dir: Path, script_type: str = "sh") -> bool:
        """
        Run the initialization script to set up coordination files.

        Args:
            target_dir: Target directory
            script_type: "sh" for bash or "ps" for PowerShell
        """
        if script_type == "sh":
            init_script = target_dir / ".claude" / "scripts" / "init-orchestration.sh"
            if not init_script.exists():
                console.print("[yellow]⚠️  Init script not found[/yellow]")
                return False

            try:
                # SECURITY: Validate script path is safe
                scripts_dir = target_dir / ".claude" / "scripts"
                safe_script = validate_script_path(init_script, scripts_dir)

                # SECURITY: Use SafeSubprocess with validated command
                result = SafeSubprocess.run(
                    ["bash", str(safe_script)],
                    cwd=target_dir,
                    timeout=60,  # 1 minute should be enough
                    check=True,
                )
                console.print(f"  ✓ Initialized coordination files")
                return True
            except SecurityError as e:
                console.print(f"[red]✗ Security validation failed: {e}[/red]")
                return False
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗ Failed to run init script: {e}[/red]")
                if e.stdout:
                    console.print(e.stdout)
                if e.stderr:
                    console.print(e.stderr)
                return False
        else:  # PowerShell
            init_script = target_dir / ".claude" / "scripts" / "init-orchestration.ps1"
            if not init_script.exists():
                console.print("[yellow]⚠️  Init script not found[/yellow]")
                return False

            # Check if PowerShell is available
            pwsh_cmd = None
            if shutil.which("pwsh"):
                pwsh_cmd = "pwsh"
            elif shutil.which("powershell"):
                pwsh_cmd = "powershell"

            if not pwsh_cmd:
                console.print(
                    "[yellow]⚠️  PowerShell not found on this system[/yellow]\n"
                    f"      Run manually: pwsh -ExecutionPolicy Bypass -File .claude/scripts/init-orchestration.ps1"
                )
                return True  # Still return success, user can run manually

            try:
                # SECURITY: Validate script path is safe
                scripts_dir = target_dir / ".claude" / "scripts"
                safe_script = validate_script_path(init_script, scripts_dir)

                # SECURITY: Use SafeSubprocess with validated command
                result = SafeSubprocess.run(
                    [pwsh_cmd, "-ExecutionPolicy", "Bypass", "-File", str(safe_script)],
                    cwd=target_dir,
                    timeout=60,
                    check=True,
                )
                console.print(f"  ✓ Initialized coordination files")
                return True
            except SecurityError as e:
                console.print(f"[red]✗ Security validation failed: {e}[/red]")
                return False
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗ Failed to run init script: {e}[/red]")
                if e.stdout:
                    console.print(e.stdout)
                if e.stderr:
                    console.print(e.stderr)
                return False


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def update_gitignore(target_dir: Path) -> bool:
    """
    Add BAZINGA-specific entries to the project's .gitignore file.

    This ensures database files and artifacts are never tracked, preventing
    merge conflicts when sub-agents work on separate branches.

    Args:
        target_dir: The project root directory

    Returns:
        True if gitignore was updated or already configured, False on error
    """
    # Skip if not a git repository
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        console.print("  [dim]Not a git repository, skipping[/dim]")
        return True

    gitignore_path = target_dir / ".gitignore"

    # The marker and entries we'll add
    marker = "# BAZINGA - Auto-generated (do not edit this section)"
    bazinga_entries = f"""{marker}
bazinga/*.db*
bazinga/artifacts/
"""

    try:
        # Check if .gitignore exists and already has our section
        if gitignore_path.exists():
            # Security: Ensure .gitignore is a regular file, not a symlink or directory
            if not gitignore_path.is_file() or gitignore_path.is_symlink():
                console.print("  [yellow]⚠️  .gitignore is not a regular file, skipping[/yellow]")
                return False

            existing_content = gitignore_path.read_text(encoding='utf-8')

            # Already configured - nothing to do
            if marker in existing_content:
                console.print("  [dim]Already configured[/dim]")
                return True

            # Detect newline style to preserve it
            newline_style = '\r\n' if '\r\n' in existing_content else '\n'

            # Append our section (with blank line separator if needed)
            separator = newline_style if existing_content and not existing_content.endswith(('\n', '\r\n')) else ""
            separator += newline_style if existing_content else ""

            # Normalize bazinga_entries to match the file's newline style
            normalized_entries = bazinga_entries.replace('\n', newline_style)

            gitignore_path.write_text(existing_content + separator + normalized_entries, encoding='utf-8')
            console.print("  [green]✓ Added BAZINGA entries to .gitignore[/green]")
        else:
            # Create new .gitignore with our entries
            gitignore_path.write_text(bazinga_entries, encoding='utf-8')
            console.print("  [green]✓ Created .gitignore with BAZINGA entries[/green]")

        return True

    except Exception as e:
        console.print(f"  [yellow]⚠️  Failed to update .gitignore: {e}[/yellow]")
        return False


def detect_project_language(target_dir: Path) -> Optional[str]:
    """
    Detect the project language based on files present.

    Returns:
        "python", "javascript", "go", "java", "ruby", or None if unknown
    """
    # Python
    if (target_dir / "pyproject.toml").exists() or (target_dir / "setup.py").exists() or (target_dir / "requirements.txt").exists():
        return "python"

    # JavaScript/TypeScript
    if (target_dir / "package.json").exists():
        return "javascript"

    # Go
    if (target_dir / "go.mod").exists():
        return "go"

    # Java
    if (target_dir / "pom.xml").exists() or (target_dir / "build.gradle").exists() or (target_dir / "build.gradle.kts").exists():
        return "java"

    # Ruby
    if (target_dir / "Gemfile").exists() or any(target_dir.glob("*.gemspec")):
        return "ruby"

    return None


def install_analysis_tools(target_dir: Path, language: str, force: bool = False) -> bool:
    """
    Install analysis tools for Skills based on detected language.

    Args:
        target_dir: Project directory
        language: Detected language (python, javascript, go, java, ruby)
        force: Skip confirmation prompt

    Returns:
        True if tools were installed successfully or skipped, False if failed
    """
    tool_configs = {
        "python": {
            "core": ["bandit", "ruff", "pytest-cov"],
            "advanced": ["semgrep"],
            "package_manager": "pip",
            "check_command": lambda t: check_command_exists(t),
            "install_cmd": lambda tools: [sys.executable, "-m", "pip", "install"] + tools,
        },
        "javascript": {
            "core": ["jest", "eslint"],
            "advanced": [],
            "package_manager": "npm",
            "check_command": lambda t: (target_dir / "node_modules" / ".bin" / t).exists() or check_command_exists(t),
            "install_cmd": lambda tools: ["npm", "install", "--save-dev"] + tools + (["@jest/globals"] if "jest" in tools else []),
        },
        "go": {
            "core": ["gosec", "golangci-lint"],
            "advanced": [],
            "package_manager": "go",
            "check_command": lambda t: check_command_exists(t),
            "install_cmd": None,  # Special handling
        },
        "java": {
            "core": [],
            "advanced": [],
            "package_manager": "maven/gradle",
            "check_command": None,
            "install_cmd": None,  # Requires build.gradle/pom.xml configuration
        },
        "ruby": {
            "core": ["brakeman", "rubocop"],
            "advanced": [],
            "package_manager": "gem",
            "check_command": lambda t: check_command_exists(t),
            "install_cmd": lambda tools: ["gem", "install"] + tools,
        },
    }

    if language not in tool_configs:
        return True  # Unknown language, skip

    config = tool_configs[language]

    # Check which tools are already installed
    all_tools = config["core"] + config["advanced"]
    if config["check_command"] and all_tools:
        installed_tools = [tool for tool in all_tools if config["check_command"](tool)]
        missing_core = [tool for tool in config["core"] if tool not in installed_tools]
        missing_advanced = [tool for tool in config["advanced"] if tool not in installed_tools]
    else:
        installed_tools = []
        missing_core = config["core"]
        missing_advanced = config["advanced"]

    # Show tool status
    console.print(f"\n[bold]{language.capitalize()} project detected[/bold]")

    if installed_tools:
        console.print(f"[dim]✓ Already installed: {', '.join(installed_tools)}[/dim]")

    missing_tools = missing_core + missing_advanced

    if not missing_tools and all_tools:
        console.print(f"[green]✓ All analysis tools are installed[/green]")
        return True

    if not all_tools:
        # Special handling for Java
        if language == "java":
            console.print(f"\n[bold yellow]ℹ️  Java tools require Maven/Gradle configuration[/bold yellow]")
            console.print("[dim]Analysis tools for Java are configured via build plugins:[/dim]")
            console.print("[dim]  • SpotBugs + Find Security Bugs (security scanning)[/dim]")
            console.print("[dim]  • JaCoCo (test coverage)[/dim]")
            console.print("[dim]  • Checkstyle + PMD (linting)[/dim]")
            console.print(f"[dim]\nSee .claude/skills/*/README.md for configuration examples.[/dim]")
            return True
        return True

    # Show what's missing
    if missing_core:
        console.print(f"\n[bold yellow]Missing core tools:[/bold yellow] {', '.join(missing_core)}")
        console.print("[dim]Core tools enable: security scanning, linting, test coverage[/dim]")

    if missing_advanced:
        console.print(f"[dim]Missing advanced tools: {', '.join(missing_advanced)}[/dim]")

    # Explain graceful degradation
    console.print(f"\n[dim]💡 In lite mode, skills skip gracefully if tools are missing.[/dim]")
    console.print(f"[dim]   You can still use BAZINGA - just with reduced analysis.[/dim]")

    if not force:
        if not typer.confirm(f"\nInstall missing tools now?", default=True):
            console.print("[yellow]⏭️  Skipped tool installation[/yellow]")
            console.print(f"[dim]\nYou can install manually later:[/dim]")
            if language == "python":
                console.print(f"[dim]  pip install {' '.join(missing_tools)}[/dim]")
            elif language == "javascript":
                console.print(f"[dim]  npm install --save-dev {' '.join(missing_tools)}[/dim]")
            elif language == "go":
                for tool in missing_tools:
                    if tool == "gosec":
                        console.print(f"[dim]  go install github.com/securego/gosec/v2/cmd/gosec@latest[/dim]")
                    elif tool == "golangci-lint":
                        console.print(f"[dim]  go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest[/dim]")
            elif language == "ruby":
                console.print(f"[dim]  gem install {' '.join(missing_tools)}[/dim]")
            return True

    # Special handling for Go - install only missing tools
    if language == "go":
        console.print(f"\n[bold cyan]Installing Go tools...[/bold cyan]")

        for tool in missing_tools:
            if tool == "gosec":
                console.print("  • Installing gosec...")
                try:
                    subprocess.run(
                        ["go", "install", "github.com/securego/gosec/v2/cmd/gosec@latest"],
                        check=True,
                        capture_output=True,
                    )
                    console.print("    [green]✓[/green] gosec installed")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    console.print("    [yellow]⚠️  Failed to install gosec[/yellow]")
            elif tool == "golangci-lint":
                console.print("  • Installing golangci-lint...")
                try:
                    subprocess.run(
                        ["go", "install", "github.com/golangci/golangci-lint/cmd/golangci-lint@latest"],
                        check=True,
                        capture_output=True,
                    )
                    console.print("    [green]✓[/green] golangci-lint installed")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    console.print("    [yellow]⚠️  Failed to install golangci-lint[/yellow]")

        return True

    # Python, JavaScript, Ruby - install only missing tools
    if config["install_cmd"] and missing_tools:
        console.print(f"\n[bold cyan]Installing {language.capitalize()} tools...[/bold cyan]")

        try:
            # Check if package manager exists
            package_manager = config["package_manager"]
            if not check_command_exists(package_manager):
                console.print(f"[red]✗ {package_manager} not found[/red]")
                console.print(f"[yellow]Please install {package_manager} first, then run tool installation manually[/yellow]")
                return False

            # Build installation command for missing tools only
            install_command = config["install_cmd"](missing_tools)

            # Run installation command (SECURITY: Use SafeSubprocess)
            try:
                result = SafeSubprocess.run(
                    install_command,
                    cwd=target_dir,
                    timeout=120,  # 2 minute timeout
                    check=False,  # Don't raise on error, handle below
                )
            except SecurityError as e:
                console.print(f"  [red]✗ Security validation failed: {e}[/red]")
                return False

            if result.returncode == 0:
                console.print(f"  [green]✓[/green] Analysis tools installed successfully")
                return True
            else:
                console.print(f"  [yellow]⚠️  Installation completed with warnings[/yellow]")
                if result.stderr:
                    console.print(f"[dim]{result.stderr[:500]}[/dim]")
                return True  # Still return success, tools might work

        except subprocess.TimeoutExpired:
            console.print(f"  [yellow]⚠️  Installation timed out[/yellow]")
            return False
        except Exception as e:
            console.print(f"  [red]✗ Installation failed: {e}[/red]")
            return False

    return True


def get_platform_info() -> tuple[str, str]:
    """
    Get current platform information for downloading pre-built releases.

    Returns:
        Tuple of (platform, arch) e.g., ("darwin", "arm64")
    """
    import platform as plat
    import struct

    # Determine platform
    system = plat.system().lower()
    if system == "windows":
        platform = "windows"
    elif system == "darwin":
        platform = "darwin"
    else:
        platform = "linux"

    # Determine architecture
    machine = plat.machine().lower()
    if machine in ("arm64", "aarch64"):
        arch = "arm64"
    elif machine in ("x86_64", "amd64"):
        arch = "x64"
    else:
        # Fallback based on pointer size
        arch = "x64" if struct.calcsize("P") == 8 else "x86"

    return (platform, arch)


def download_prebuilt_dashboard(target_dir: Path, force: bool = False) -> bool:
    """
    Download pre-built dashboard package from GitHub releases.

    Args:
        target_dir: Target directory for installation
        force: Force download even if already installed

    Returns:
        True if download successful, False otherwise (should fall back to npm)
    """
    import json
    import tarfile
    import tempfile
    import urllib.request
    import urllib.error

    dashboard_dir = target_dir / "bazinga" / "dashboard-v2"
    standalone_marker = dashboard_dir / ".next" / "standalone" / "server.js"

    # Check if already have standalone build
    if standalone_marker.exists() and not force:
        console.print("  [green]✓[/green] Pre-built dashboard already installed")
        return True

    platform, arch = get_platform_info()

    console.print(f"  [dim]Checking for pre-built dashboard ({platform}-{arch})...[/dim]")

    # Query GitHub API for latest release
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "bazinga-cli"}
        # Use GITHUB_TOKEN if available for higher rate limits (5000/hr vs 60/hr)
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            releases = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # Check X-RateLimit-Remaining header to confirm rate limit
            rate_remaining = e.headers.get("X-RateLimit-Remaining", "")
            if rate_remaining == "0":
                console.print("  [dim]GitHub API rate limit exceeded[/dim]")
                console.print("  [dim]Tip: Set GITHUB_TOKEN env var for higher rate limits[/dim]")
            else:
                console.print(f"  [dim]Could not check for releases: HTTP 403 Forbidden[/dim]")
        else:
            console.print(f"  [dim]Could not check for releases: HTTP {e.code} {e.reason}[/dim]")
        return False
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        console.print(f"  [dim]Could not check for releases: {e}[/dim]")
        return False

    # Find latest dashboard release
    dashboard_release = None
    for release in releases:
        if release.get("tag_name", "").startswith("dashboard-v"):
            dashboard_release = release
            break

    if not dashboard_release:
        console.print("  [dim]No pre-built dashboard releases found[/dim]")
        return False

    version = dashboard_release["tag_name"].replace("dashboard-v", "")
    console.print(f"  [dim]Found dashboard release v{version}[/dim]")

    # Find the right asset for this platform
    asset_name = f"bazinga-dashboard-{platform}-{arch}.tar.gz"
    asset_url = None

    for asset in dashboard_release.get("assets", []):
        if asset.get("name") == asset_name:
            asset_url = asset.get("browser_download_url")
            break

    if not asset_url:
        console.print(f"  [dim]No pre-built package for {platform}-{arch}[/dim]")
        return False

    # Download the tarball
    console.print(f"  Downloading pre-built dashboard v{version}...")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name

        req = urllib.request.Request(asset_url, headers={"User-Agent": "bazinga-cli"})
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(tmp_path, "wb") as f:
                # Download with progress indication (throttled to reduce I/O)
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 8192
                last_percent = -5  # Ensure first update shows

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        # Throttle: only update every 5%
                        if percent >= last_percent + 5:
                            last_percent = percent
                            console.print(f"\r  [dim]Downloaded: {downloaded // 1024}KB / {total_size // 1024}KB ({percent}%)[/dim]", end="")

        console.print()  # Newline after progress

        # Extract the tarball
        console.print("  Extracting pre-built dashboard...")

        # Remove existing dashboard-v2 if present (but preserve config)
        if dashboard_dir.exists():
            # Only remove .next folder to preserve any local config
            next_dir = dashboard_dir / ".next"
            if next_dir.exists():
                shutil.rmtree(next_dir)

        # Ensure bazinga directory exists
        bazinga_dir = target_dir / "bazinga"
        bazinga_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(tmp_path, "r:gz") as tar:
            # Extract to bazinga directory (tarball contains dashboard-v2/)
            # Security: Validate paths to prevent tar slip attacks
            for member in tar.getmembers():
                member_path = os.path.normpath(os.path.join(bazinga_dir, member.name))
                if not member_path.startswith(str(bazinga_dir)):
                    raise tarfile.TarError(f"Unsafe path in tarball: {member.name}")
            tar.extractall(path=bazinga_dir)

        # Cleanup temp file
        os.unlink(tmp_path)

        # Verify extraction - check both server.js AND BUILD_ID exist
        build_id_marker = dashboard_dir / ".next" / "BUILD_ID"
        standalone_build_id = dashboard_dir / ".next" / "standalone" / ".next" / "BUILD_ID"

        if standalone_marker.exists() and (build_id_marker.exists() or standalone_build_id.exists()):
            console.print(f"  [green]✓[/green] Pre-built dashboard v{version} installed (standalone mode)")
            console.print("  [dim]No npm install required - ready to run![/dim]")
            return True
        elif standalone_marker.exists():
            # server.js exists but BUILD_ID missing - incomplete artifact
            console.print("  [yellow]⚠️  Release artifact incomplete (missing BUILD_ID)[/yellow]")
            console.print("  [dim]Falling back to source/dev mode...[/dim]")
            return False
        else:
            console.print("  [yellow]⚠️  Extraction may have failed, falling back to source/dev mode[/yellow]")
            return False

    except (urllib.error.URLError, tarfile.TarError, OSError) as e:
        console.print(f"  [yellow]⚠️  Download failed: {e}[/yellow]")
        # Cleanup temp file if exists
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False


def install_dashboard_dependencies(target_dir: Path, force: bool = False) -> bool:
    """
    Install dashboard v2 - tries pre-built first, falls back to npm install.

    Args:
        target_dir: Project directory
        force: Skip confirmation prompt

    Returns:
        True if dependencies were installed successfully or skipped, False if failed
    """
    dashboard_dir = target_dir / "bazinga" / "dashboard-v2"

    # Check if dashboard folder exists
    if not dashboard_dir.exists():
        console.print("  [dim]Dashboard v2 folder not found, skipping dependency installation[/dim]")
        return True

    # Check for standalone build (pre-built release)
    standalone_marker = dashboard_dir / ".next" / "standalone" / "server.js"
    if standalone_marker.exists() and not force:
        console.print("  [green]✓[/green] Pre-built dashboard already installed (standalone mode)")
        return True

    # Try downloading pre-built dashboard first (faster, no npm required)
    console.print("\n[bold]Option 1: Pre-built dashboard (faster, no npm required)[/bold]")
    try:
        if download_prebuilt_dashboard(target_dir, force):
            return True
    except Exception as e:
        console.print(f"  [yellow]⚠️  Pre-built download failed: {e}. Falling back to npm.[/yellow]")

    # Fall back to npm install
    console.print("\n[bold]Option 2: Build from source (requires npm)[/bold]")

    package_json = dashboard_dir / "package.json"
    if not package_json.exists():
        console.print("  [yellow]⚠️  package.json not found in dashboard-v2 folder[/yellow]")
        return True

    # Check for node_modules indicating dependencies were already installed
    node_modules = dashboard_dir / "node_modules"
    if node_modules.exists() and not force:
        console.print("  [green]✓[/green] Dashboard v2 dependencies already installed")
        return True

    # Check if npm is available
    if not check_command_exists("npm"):
        console.print("  [yellow]⚠️  npm not found, skipping dashboard dependencies[/yellow]")
        console.print(f"  [dim]Install Node.js, then run: cd bazinga/dashboard-v2 && npm install[/dim]")
        return True

    console.print("  [dim]Dashboard v2 uses Next.js with TypeScript[/dim]")
    console.print("  [dim]This enables: real-time monitoring, session analytics, AI insights[/dim]")

    if not force:
        if not typer.confirm("  Install dashboard dependencies (npm install)?", default=True):
            console.print("  [yellow]⏭️  Skipped dashboard dependency installation[/yellow]")
            console.print(f"  [dim]You can install later with: cd bazinga/dashboard-v2 && npm install[/dim]")
            return True

    # Install dependencies using npm
    try:
        console.print("  Installing npm packages (this may take a minute)...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=dashboard_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout for npm
        )

        if result.returncode == 0:
            console.print("  [green]✓[/green] Dashboard v2 dependencies installed")
            return True
        else:
            console.print("  [yellow]⚠️  npm install completed with warnings[/yellow]")
            if result.stderr:
                # Only show first 200 chars of error
                console.print(f"  [dim]{result.stderr[:200]}[/dim]")
            return True  # Still return success, npm often has warnings

    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠️  npm install timed out[/yellow]")
        console.print(f"  [dim]Install manually: cd bazinga/dashboard-v2 && npm install[/dim]")
        return True

    except Exception as e:
        console.print(f"  [yellow]⚠️  Dashboard dependency installation failed: {e}[/yellow]")
        console.print(f"  [dim]Install manually: cd bazinga/dashboard-v2 && npm install[/dim]")
        return True


def select_script_type() -> str:
    """
    Interactive selection of script type using arrow keys.

    Returns:
        "sh" for POSIX shell or "ps" for PowerShell
    """
    import sys
    import platform

    # Determine default based on platform
    default_script = "ps" if platform.system() == "Windows" else "sh"

    choices = {
        "sh": "POSIX Shell (bash/zsh) - Linux/macOS",
        "ps": "PowerShell - Windows/Cross-platform",
    }

    console.print("\n[bold]Select script type:[/bold]")
    console.print("  [cyan]1.[/cyan] POSIX Shell (bash/zsh) - Linux/macOS")
    console.print("  [cyan]2.[/cyan] PowerShell - Windows/Cross-platform")

    default_choice = "1" if default_script == "sh" else "2"
    console.print(f"\n[dim]Default for your platform: {choices[default_script]}[/dim]")

    # Simple prompt for choice
    choice = typer.prompt(
        "Enter choice (1 or 2, or press Enter for default)",
        default=default_choice,
        show_default=False,
    )

    if choice == "1":
        return "sh"
    elif choice == "2":
        return "ps"
    else:
        # Invalid choice, use default
        console.print(f"[yellow]Invalid choice, using default: {default_script}[/yellow]")
        return default_script


def print_banner():
    """Print BAZINGA banner."""
    banner = """
[bold cyan]
██████╗  █████╗ ███████╗██╗███╗   ██╗ ██████╗  █████╗
██╔══██╗██╔══██╗╚══███╔╝██║████╗  ██║██╔════╝ ██╔══██╗
██████╔╝███████║  ███╔╝ ██║██╔██╗ ██║██║  ███╗███████║
██╔══██╗██╔══██║ ███╔╝  ██║██║╚██╗██║██║   ██║██╔══██║
██████╔╝██║  ██║███████╗██║██║ ╚████║╚██████╔╝██║  ██║
╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝[/bold cyan]
    """
    console.print(banner)
    console.print(
        "[bold white]Multi-Agent Orchestration System for Claude Code[/bold white]\n",
        justify="center",
    )


@app.command()
def init(
    project_name: Optional[str] = typer.Argument(
        None, help="Name of the project directory to create"
    ),
    here: bool = typer.Option(
        False, "--here", help="Initialize in the current directory"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompts"
    ),
    no_git: bool = typer.Option(
        False, "--no-git", help="Skip git repository initialization"
    ),
    dashboard: bool = typer.Option(
        False,
        "--dashboard",
        help="Install experimental dashboard (early development, no impact on BAZINGA functionality)",
    ),
    testing_mode: str = typer.Option(
        "minimal",
        "--testing",
        "-t",
        help="Testing framework mode: full, minimal (default), or disabled",
    ),
    profile: str = typer.Option(
        "lite",
        "--profile",
        "-p",
        help="Configuration profile: lite (default), advanced, or custom",
    ),
):
    """
    Initialize a new BAZINGA project with multi-agent orchestration.

    This will set up the complete multi-agent system including:
    - Agent definitions (orchestrator, PM, developer, QA, tech lead, investigator, requirements engineer)
    - Initialization scripts
    - Configuration files
    - Coordination state files

    Profiles:
    - lite (default): Fast development with 3 core skills, parallel mode enabled
    - advanced: All 10 skills enabled, full testing mode
    - custom: Use individual flags (--testing) for fine control

    Testing modes (for custom profile):
    - full: All tests + QA Expert (production)
    - minimal: Lint + unit tests only (default)
    - disabled: Lint only (rapid prototyping)
    """
    print_banner()

    # Validate profile
    valid_profiles = ["lite", "advanced", "custom"]
    if profile.lower() not in valid_profiles:
        console.print(
            f"[red]✗ Invalid profile: '{profile}'[/red]\n"
            f"Valid options: {', '.join(valid_profiles)}"
        )
        raise typer.Exit(1)
    profile = profile.lower()

    # Handle profile presets
    if profile == "advanced":
        # Advanced profile: Enable all skills, full testing
        testing_mode = "full"
        console.print(f"[cyan]Using advanced profile: All skills enabled, full testing mode[/cyan]\n")
    elif profile == "lite":
        # Lite profile: Core skills only, minimal testing (already default in init script)
        # If user didn't specify testing mode, keep minimal
        if testing_mode == "minimal":
            pass  # Use default
        console.print(f"[cyan]Using lite profile: 3 core skills, parallel mode enabled[/cyan]\n")
    # custom profile uses individual flags as-is

    # Validate testing mode
    valid_testing_modes = ["full", "minimal", "disabled"]
    if testing_mode.lower() not in valid_testing_modes:
        console.print(
            f"[red]✗ Invalid testing mode: '{testing_mode}'[/red]\n"
            f"Valid options: {', '.join(valid_testing_modes)}"
        )
        raise typer.Exit(1)
    testing_mode = testing_mode.lower()

    # Ask for script type preference
    script_type = select_script_type()

    # Determine target directory
    if here or not project_name:
        # Default to current directory if --here flag or no project name provided
        target_dir = Path.cwd()
        if not force:
            console.print(
                f"\n[yellow]This will initialize BAZINGA in:[/yellow] [bold]{target_dir}[/bold]"
            )
            confirm = typer.confirm("Continue?")
            if not confirm:
                console.print("[red]Cancelled[/red]")
                raise typer.Exit(1)
    elif project_name:
        # SECURITY: Validate project name
        try:
            safe_name = PathValidator.validate_project_name(project_name)
        except SecurityError as e:
            console.print(f"[red]✗ Invalid project name: {e}[/red]")
            console.print("\n[yellow]Project name requirements:[/yellow]")
            console.print("  • Only letters, numbers, hyphens, underscores, and dots")
            console.print("  • Cannot contain '..' or path separators")
            console.print("  • Maximum 255 characters")
            raise typer.Exit(1)

        target_dir = Path.cwd() / safe_name
        if target_dir.exists():
            console.print(f"[red]✗ Directory '{safe_name}' already exists[/red]")
            raise typer.Exit(1)
        target_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"\n[green]✓[/green] Created directory: [bold]{target_dir}[/bold]")

    # Setup instance
    setup = BazingaSetup()

    # Copy files with progress
    console.print("\n[bold]Installing BAZINGA components...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing...", total=None)

        console.print("[bold cyan]1. Copying agent definitions[/bold cyan]")
        if not setup.copy_agents(target_dir):
            console.print("[red]✗ Failed to copy agents[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]2. Copying scripts ({script_type.upper()})[/bold cyan]")
        if not setup.copy_scripts(target_dir, script_type):
            console.print("[yellow]⚠️  No scripts found[/yellow]")

        console.print("\n[bold cyan]3. Copying commands[/bold cyan]")
        if not setup.copy_commands(target_dir):
            console.print("[yellow]⚠️  No commands found[/yellow]")

        console.print(f"\n[bold cyan]4. Copying skills ({script_type.upper()})[/bold cyan]")
        if not setup.copy_skills(target_dir, script_type):
            console.print("[yellow]⚠️  No skills found[/yellow]")

        console.print("\n[bold cyan]5. Setting up configuration[/bold cyan]")
        if not setup.setup_config(target_dir):
            console.print("[red]✗ Failed to setup configuration[/red]")
            raise typer.Exit(1)

        console.print("\n[bold cyan]6. Dashboard v2[/bold cyan]")
        if dashboard:
            console.print("  [dim]Installing (early experimental feature)...[/dim]")
            # Ensure bazinga directory exists
            (target_dir / "bazinga").mkdir(parents=True, exist_ok=True)

            # Try downloading pre-built dashboard first (faster, no npm required)
            prebuilt_ok = False
            try:
                prebuilt_ok = download_prebuilt_dashboard(target_dir, force=True)
            except Exception as e:
                console.print(f"  [yellow]⚠️  Pre-built download failed: {e}. Falling back to source copy.[/yellow]")

            if prebuilt_ok:
                console.print("  [green]✓[/green] Dashboard installed from pre-built release")
            else:
                # Fall back to copying source files
                console.print("  [dim]Pre-built not available, copying source files...[/dim]")
                source_dashboard = setup.source_dir / "dashboard-v2"
                target_dashboard = target_dir / "bazinga" / "dashboard-v2"

                if source_dashboard.exists():
                    try:
                        # Copy dashboard-v2 but exclude node_modules
                        shutil.copytree(
                            source_dashboard,
                            target_dashboard,
                            ignore=shutil.ignore_patterns('node_modules', '.next', '*.log')
                        )
                        console.print("  ✓ Dashboard v2 source copied (requires npm install && npm run build)")
                    except Exception as e:
                        console.print(f"  [yellow]⚠️  Failed to copy dashboard: {e}[/yellow]")
                else:
                    console.print("  [yellow]⚠️  Dashboard v2 not found in source[/yellow]")

            # Copy research folder for documentation
            source_research = setup.source_dir / "research"
            target_research = target_dir / "research"
            if source_research.exists():
                target_research.mkdir(parents=True, exist_ok=True)
                dashboard_doc = source_research / "new-database-dashboard-ultrathink.md"
                if dashboard_doc.exists():
                    shutil.copy2(dashboard_doc, target_research / "dashboard-v2-design.md")
                    console.print("  ✓ Copied dashboard documentation")
        else:
            console.print("  [dim]Skipped (experimental; install later: 'bazinga setup-dashboard')[/dim]")

        console.print("\n[bold cyan]7. Copying templates[/bold cyan]")
        if not setup.copy_templates(target_dir):
            console.print("[yellow]⚠️  No templates found[/yellow]")

        console.print("\n[bold cyan]7.1. Copying config files[/bold cyan]")
        if not setup.copy_bazinga_configs(target_dir):
            console.print("[yellow]⚠️  No config files found[/yellow]")

        console.print("\n[bold cyan]7.2. Copying .claude templates[/bold cyan]")
        if not setup.copy_claude_templates(target_dir):
            console.print("[yellow]⚠️  No .claude templates found[/yellow]")

        console.print("\n[bold cyan]7.3. Installing compaction recovery hook[/bold cyan]")
        setup.install_compact_recovery_hook(target_dir, script_type)

        console.print("\n[bold cyan]7.4. Mini-dashboard[/bold cyan]")
        setup.copy_mini_dashboard(target_dir)

        console.print("\n[bold cyan]8. Initializing coordination files[/bold cyan]")
        setup.run_init_script(target_dir, script_type)

        # Update testing configuration if not default
        if testing_mode != "minimal":
            import json
            testing_config_path = target_dir / "bazinga" / "testing_config.json"
            if testing_config_path.exists():
                try:
                    with open(testing_config_path, "r") as f:
                        testing_config = json.load(f)

                    # Update mode and related settings
                    testing_config["_testing_framework"]["mode"] = testing_mode

                    if testing_mode == "full":
                        testing_config["_testing_framework"]["test_requirements"]["require_integration_tests"] = True
                        testing_config["_testing_framework"]["test_requirements"]["require_contract_tests"] = True
                        testing_config["_testing_framework"]["test_requirements"]["require_e2e_tests"] = True
                        testing_config["_testing_framework"]["test_requirements"]["coverage_threshold"] = 80
                        testing_config["_testing_framework"]["qa_workflow"]["enable_qa_expert"] = True
                        testing_config["_testing_framework"]["qa_workflow"]["auto_route_to_qa"] = True
                    elif testing_mode == "disabled":
                        testing_config["_testing_framework"]["enabled"] = False
                        testing_config["_testing_framework"]["pre_commit_validation"]["unit_tests"] = False
                        testing_config["_testing_framework"]["pre_commit_validation"]["build_check"] = False

                    with open(testing_config_path, "w") as f:
                        json.dump(testing_config, f, indent=2)

                    console.print(f"  ✓ Testing mode set to: [bold]{testing_mode}[/bold]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to update testing mode: {e}[/yellow]")

        # Update skills configuration for advanced profile
        if profile == "advanced":
            import json
            skills_config_path = target_dir / "bazinga" / "skills_config.json"
            if skills_config_path.exists():
                try:
                    with open(skills_config_path, "r") as f:
                        skills_config = json.load(f)

                    # Update profile metadata
                    skills_config["_metadata"]["profile"] = "advanced"
                    skills_config["_metadata"]["description"] = "Advanced profile - all skills enabled for comprehensive analysis"

                    # Enable all advanced skills
                    skills_config["developer"]["codebase-analysis"] = "mandatory"
                    skills_config["developer"]["test-pattern-analysis"] = "mandatory"
                    skills_config["developer"]["api-contract-validation"] = "mandatory"
                    skills_config["developer"]["db-migration-check"] = "mandatory"
                    skills_config["qa_expert"]["pattern-miner"] = "mandatory"
                    skills_config["qa_expert"]["quality-dashboard"] = "mandatory"
                    skills_config["pm"]["velocity-tracker"] = "mandatory"

                    with open(skills_config_path, "w") as f:
                        json.dump(skills_config, f, indent=2)

                    console.print(f"  ✓ Advanced profile: All 10 skills enabled")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to update skills config: {e}[/yellow]")

    # Offer to install analysis tools
    detected_language = detect_project_language(target_dir)
    if detected_language:
        install_analysis_tools(target_dir, detected_language, force)

    # Install dashboard dependencies
    console.print("\n[bold cyan]9. Dashboard dependencies[/bold cyan]")
    if dashboard:
        install_dashboard_dependencies(target_dir, force)
    else:
        console.print("  [dim]Skipped[/dim]")

    # Initialize git if requested
    if not no_git and check_command_exists("git"):
        console.print("\n[bold cyan]10. Initializing git repository[/bold cyan]")
        try:
            subprocess.run(
                ["git", "init"],
                cwd=target_dir,
                capture_output=True,
                check=True,
            )
            console.print("  ✓ Git repository initialized")
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠️  Git initialization failed[/yellow]")

    # Update .gitignore to prevent database merge conflicts
    console.print("\n[bold cyan]11. Configuring .gitignore[/bold cyan]")
    update_gitignore(target_dir)

    # Success message
    profile_desc = {
        "lite": "Lite (3 core skills, fast development)",
        "advanced": "Advanced (10 skills, comprehensive analysis)",
        "custom": "Custom (user-configured)"
    }
    testing_mode_desc = {
        "full": "Full testing with QA Expert",
        "minimal": "Minimal testing (lint + unit tests)",
        "disabled": "Prototyping mode (lint only)"
    }

    bazinga_commands = "[bold]BAZINGA Commands:[/bold]\n"
    bazinga_commands += "[dim]  • /bazinga.orchestrate           (start orchestration)\n"
    bazinga_commands += "  • /bazinga.orchestrate-advanced  (with requirements discovery)\n"
    bazinga_commands += "  • /bazinga.orchestrate-from-spec (orchestrate from spec-kit)[/dim]\n\n"
    bazinga_commands += "[dim]Customize:\n"
    bazinga_commands += "  • /bazinga.configure-skills    (add/remove skills)\n"
    bazinga_commands += "  • /bazinga.configure-testing   (change testing mode)[/dim]"

    # Determine next steps message based on whether project was created
    if project_name:
        next_steps = f"  1. cd {target_dir.name}\n  2. Open with Claude Code\n  3. Use: /bazinga.orchestrate <your request>\n     [dim](or @orchestrator if you prefer)[/dim]"
    else:
        next_steps = "  1. Open with Claude Code\n  2. Use: /bazinga.orchestrate <your request>\n     [dim](or @orchestrator if you prefer)[/dim]"

    console.print(
        Panel.fit(
            f"[bold green]✓ BAZINGA installed successfully![/bold green]\n\n"
            f"Your multi-agent orchestration system is ready.\n"
            f"[dim]Profile: {profile_desc.get(profile, profile)}[/dim]\n"
            f"[dim]Testing: {testing_mode_desc.get(testing_mode, testing_mode)}[/dim]\n\n"
            "[bold]Next steps:[/bold]\n"
            f"{next_steps}\n\n"
            "[bold]Example:[/bold]\n"
            "  /bazinga.orchestrate implement user authentication with JWT\n"
            "  [dim](or: @orchestrator implement user authentication with JWT)[/dim]\n\n"
            f"{bazinga_commands}",
            title="🎉 Installation Complete",
            border_style="green",
        )
    )

    # Show structure
    console.print("\n[bold]Installed structure:[/bold]")
    tree = Table.grid(padding=(0, 2))
    tree.add_row("📁", ".claude/")
    tree.add_row("  ", "├── agents/      [dim](7 agents: orchestrator, PM, dev, QA, tech lead, investigator, req engineer)[/dim]")
    tree.add_row("  ", "├── commands/    [dim](slash commands)[/dim]")
    tree.add_row("  ", "├── scripts/     [dim](initialization scripts)[/dim]")
    tree.add_row("  ", "├── skills/      [dim](security-scan, test-coverage, lint-check)[/dim]")
    tree.add_row("  ", "└── CLAUDE.md    [dim](global configuration)[/dim]")
    tree.add_row("📁", "bazinga/         [dim](state files for agent coordination)[/dim]")
    console.print(tree)

    # Track installation (anonymous telemetry)
    track_command("init", __version__)


@app.command()
def check():
    """
    Check that all required tools and configurations are present.

    Verifies:
    - Git installation
    - Claude Code configuration
    - BAZINGA setup (if in a bazinga project)
    """
    print_banner()

    console.print("[bold]Checking system requirements...[/bold]\n")

    checks = []

    # Check git
    if check_command_exists("git"):
        checks.append(("Git", True, "Installed"))
    else:
        checks.append(("Git", False, "Not found"))

    # Check if we're in a BAZINGA project
    cwd = Path.cwd()
    claude_dir = cwd / ".claude"
    agents_dir = claude_dir / "agents"
    # Check for config in new location (.claude/CLAUDE.md) or old location (.claude.md) for backwards compatibility
    config_file_new = claude_dir / "CLAUDE.md"
    config_file_old = cwd / ".claude.md"
    config_exists = config_file_new.exists() or config_file_old.exists()
    bazinga_dir = cwd / "bazinga"

    bazinga_installed = all(
        [
            claude_dir.exists(),
            agents_dir.exists(),
            config_exists,
            (agents_dir / "orchestrator.md").exists(),
        ]
    )

    if bazinga_installed:
        checks.append(("BAZINGA Setup", True, "Found in current directory"))

        # Check for required agents (with legacy alias support)
        # tech_lead.md was renamed from techlead.md - accept either for backward compatibility
        required_agents = [
            "orchestrator.md",
            "project_manager.md",
            "developer.md",
            "qa_expert.md",
            ("tech_lead.md", "techlead.md"),  # Primary, legacy alias
            "investigator.md",
            "requirements_engineer.md",
        ]

        def agent_exists(agent_spec):
            """Check if agent file exists, supporting legacy aliases."""
            if isinstance(agent_spec, tuple):
                return any((agents_dir / name).exists() for name in agent_spec)
            return (agents_dir / agent_spec).exists()

        def agent_name(agent_spec):
            """Get display name for agent (primary name only)."""
            return agent_spec[0] if isinstance(agent_spec, tuple) else agent_spec

        missing_agents = [
            agent_name(agent) for agent in required_agents if not agent_exists(agent)
        ]

        if missing_agents:
            checks.append(
                ("Agent Files", False, f"Missing: {', '.join(missing_agents)}")
            )
        else:
            checks.append(("Agent Files", True, "All 7 agents present"))

        if bazinga_dir.exists():
            checks.append(("Coordination Files", True, "Initialized"))
        else:
            checks.append(("Coordination Files", False, "Not initialized"))
    else:
        checks.append(("BAZINGA Setup", False, "Not found (run 'bazinga init')"))

    # Display results
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for name, status, details in checks:
        status_icon = "[green]✓[/green]" if status else "[red]✗[/red]"
        status_text = "[green]OK[/green]" if status else "[red]MISSING[/red]"
        table.add_row(name, f"{status_icon} {status_text}", details)

    console.print(table)

    # Summary
    all_ok = all(status for _, status, _ in checks)
    if all_ok:
        console.print(
            "\n[bold green]✓ All checks passed! You're ready to use BAZINGA.[/bold green]"
        )
    else:
        console.print(
            "\n[bold yellow]⚠️  Some components are missing. Install with:[/bold yellow]"
        )
        console.print("    bazinga init --here")


def get_bazinga_git_url(branch: Optional[str] = None) -> str:
    """
    Construct the git URL for installing/updating BAZINGA CLI.

    Args:
        branch: Optional git branch to install from (e.g., "develop", "feature/xyz")

    Returns:
        Formatted git URL for pip/uv installation
    """
    base_url = "git+https://github.com/mehdic/bazinga.git"
    return f"{base_url}@{branch}" if branch else base_url


def update_cli(branch: Optional[str] = None) -> bool:
    """
    Update the BAZINGA CLI itself by pulling latest changes and reinstalling.

    Args:
        branch: Optional git branch to pull from (e.g., "develop", "feature/xyz")

    Returns True if update was successful, False otherwise.
    """
    try:
        # Try pip first (for pip installs and editable installs)
        # Use sys.executable -m pip to ensure we use the correct Python environment
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "bazinga-cli"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            # Parse the output to find installation location
            location = None
            editable_project_location = None
            for line in result.stdout.split('\n'):
                if line.startswith('Location:'):
                    location = line.split(':', 1)[1].strip()
                elif line.startswith('Editable project location:'):
                    editable_project_location = line.split(':', 1)[1].strip()

            # If it's an editable install, update from git
            if editable_project_location:
                bazinga_repo = Path(editable_project_location)
                console.print(f"  [dim]Found editable install at: {bazinga_repo}[/dim]")

                was_updated = False

                # Check if it's a git repo
                if not (bazinga_repo / ".git").exists():
                    console.print("  [dim]Not a git repository, skipping git pull[/dim]")
                else:
                    # Pull latest changes
                    if branch:
                        console.print(f"  [dim]Fetching and checking out branch: {branch}...[/dim]")
                        # Fetch the branch first
                        fetch_result = subprocess.run(
                            ["git", "fetch", "origin", branch],
                            cwd=bazinga_repo,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if fetch_result.returncode != 0:
                            console.print(f"  [yellow]Warning: git fetch failed: {fetch_result.stderr}[/yellow]")

                        # Checkout the branch
                        checkout_result = subprocess.run(
                            ["git", "checkout", branch],
                            cwd=bazinga_repo,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if checkout_result.returncode != 0:
                            console.print(f"  [yellow]Warning: git checkout failed: {checkout_result.stderr}[/yellow]")

                        # Pull the latest changes for this branch
                        pull_result = subprocess.run(
                            ["git", "pull", "origin", branch],
                            cwd=bazinga_repo,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                    else:
                        console.print("  [dim]Pulling latest changes...[/dim]")
                        pull_result = subprocess.run(
                            ["git", "pull"],
                            cwd=bazinga_repo,
                            capture_output=True,
                            text=True,
                            check=False
                        )

                    if pull_result.returncode != 0:
                        console.print(f"  [yellow]Warning: git pull failed: {pull_result.stderr}[/yellow]")
                    elif "Already up to date" in pull_result.stdout or "Already up-to-date" in pull_result.stdout:
                        console.print("  [dim]Already up to date[/dim]")
                    else:
                        console.print("  [dim]Pulled latest changes[/dim]")

                        # Check if CLI code itself was updated (not just content files)
                        # We only want to warn/return True if files in src/ changed
                        diff_result = subprocess.run(
                            ["git", "diff", "--name-only", "HEAD@{1}", "HEAD"],
                            cwd=bazinga_repo,
                            capture_output=True,
                            text=True,
                            check=False
                        )

                        if diff_result.returncode == 0:
                            changed_files = diff_result.stdout.strip().split('\n')
                            # Check if any changed files are in src/ (CLI code)
                            cli_files_changed = any(
                                f.startswith('src/') for f in changed_files if f
                            )

                            if cli_files_changed:
                                console.print("  [dim]CLI code was updated[/dim]")
                                was_updated = True
                            else:
                                console.print("  [dim]Only content files were updated (agents, scripts, etc.)[/dim]")
                                was_updated = False
                        else:
                            # If we can't determine what changed, assume CLI was updated (conservative)
                            was_updated = True

                # Only reinstall if there were updates
                if was_updated:
                    console.print("  [dim]Reinstalling CLI...[/dim]")
                    install_result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-e", str(bazinga_repo), "--quiet"],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if install_result.returncode != 0:
                        console.print(f"  [yellow]Warning: reinstall failed: {install_result.stderr}[/yellow]")
                        return False

                return was_updated
            else:
                # Not an editable install, try upgrading from PyPI or git
                git_url = get_bazinga_git_url(branch)
                if branch:
                    console.print(f"  [dim]Upgrading from git repository (branch: {branch})...[/dim]")
                else:
                    console.print("  [dim]Upgrading from git repository...[/dim]")
                upgrade_result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", git_url],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if upgrade_result.returncode != 0:
                    console.print(f"  [yellow]Warning: upgrade failed: {upgrade_result.stderr}[/yellow]")
                    return False

                # Check if there was an actual update
                output = upgrade_result.stdout + upgrade_result.stderr
                if "Successfully installed" in output or "Successfully upgraded" in output:
                    console.print("  [dim]CLI updated[/dim]")
                    return True
                elif "Requirement already satisfied" in output or "already up-to-date" in output.lower():
                    console.print("  [dim]Already up to date[/dim]")
                    return False
                else:
                    # Uncertain, assume update happened
                    return True

        # pip show failed - try uv tool (for uv tool installs)
        console.print("  [dim]Checking for uv tool installation...[/dim]")
        uv_check = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=False
        )

        if uv_check.returncode == 0 and "bazinga-cli" in uv_check.stdout:
            git_url = get_bazinga_git_url(branch)
            if branch:
                console.print(f"  [dim]Found uv tool installation, updating from branch: {branch}...[/dim]")
            else:
                console.print("  [dim]Found uv tool installation, checking for updates...[/dim]")
            uv_upgrade = subprocess.run(
                ["uv", "tool", "install", "--force", "bazinga-cli", "--from", git_url],
                capture_output=True,
                text=True,
                check=False
            )

            if uv_upgrade.returncode != 0:
                console.print(f"  [yellow]Warning: uv upgrade failed[/yellow]")
                console.print(f"  [dim]stderr: {uv_upgrade.stderr}[/dim]")
                return False

            # Check if there was actually an update (uv shows "Updated" when pulling new commits)
            output = uv_upgrade.stdout + uv_upgrade.stderr
            if "Updated https://github.com" in output or "Installed bazinga-cli" in output:
                console.print("  [dim]CLI updated[/dim]")
                return True
            else:
                # No update detected - already up to date
                console.print("  [dim]Already up to date[/dim]")
                return False

        # Neither pip nor uv found the installation
        console.print("  [dim]Could not detect installation method (pip or uv)[/dim]")
        console.print("  [dim]You may need to manually reinstall:[/dim]")
        console.print("  [dim]  uv tool install --force bazinga-cli --from git+https://github.com/mehdic/bazinga.git[/dim]")
        return False

    except Exception as e:
        console.print(f"  [yellow]Warning: CLI update failed: {e}[/yellow]")
        return False


@app.command()
def update(
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompts"
    ),
    branch: Optional[str] = typer.Option(
        None, "-b", help="Git branch to update from (e.g., 'develop', 'feature/xyz')"
    ),
    dashboard: bool = typer.Option(
        False,
        "--dashboard",
        help="Update experimental dashboard (early development, no impact on BAZINGA functionality)",
    ),
):
    """
    Update BAZINGA components in the current project.

    Updates the BAZINGA CLI itself and project components (agents, scripts,
    commands, skills) to the latest versions while preserving coordination
    state files and existing configuration.

    By default, updates from the main branch. Use -b to test changes
    from a specific branch before they're merged to main.

    Examples:
      bazinga update                    # Update from main branch
      bazinga update -b develop         # Test changes from develop branch
      bazinga update -b feature/new-fix # Test a specific feature branch
    """
    print_banner()

    target_dir = Path.cwd()

    # Check if BAZINGA is installed
    if not (target_dir / ".claude" / "agents" / "orchestrator.md").exists():
        console.print(
            "[red]✗ BAZINGA not found in current directory[/red]\n"
            "Run 'bazinga init --here' to install first."
        )
        raise typer.Exit(1)

    if not force:
        branch_info = f" (from branch: {branch})" if branch else ""
        console.print(
            f"\n[yellow]This will update{branch_info}:[/yellow]\n"
            "  • BAZINGA CLI (pull latest & reinstall)\n"
            "  • Agent definitions (.claude/agents/)\n"
            "  • Scripts (.claude/scripts/)\n"
            "  • Commands (.claude/commands/)\n"
            "  • Skills (.claude/skills/)\n\n"
            "[dim]Coordination files will NOT be modified[/dim]\n"
        )
        confirm = typer.confirm("Continue with update?")
        if not confirm:
            console.print("[red]Cancelled[/red]")
            raise typer.Exit(1)

    console.print("\n[bold]Updating BAZINGA...[/bold]\n")

    # Step 0: Update the CLI itself
    if branch:
        console.print(f"[bold cyan]0. Updating BAZINGA CLI (branch: {branch})[/bold cyan]")
    else:
        console.print("[bold cyan]0. Updating BAZINGA CLI[/bold cyan]")
    cli_was_updated = update_cli(branch)
    if cli_was_updated:
        console.print("  [green]✓ CLI updated[/green]")
    else:
        console.print("  [dim]Already up to date[/dim]")

    setup = BazingaSetup()

    # Detect which script type is currently installed
    script_type = setup.detect_script_type(target_dir)

    console.print()

    # Update agents
    console.print("[bold cyan]1. Updating agent definitions[/bold cyan]")
    if setup.copy_agents(target_dir):
        console.print("  [green]✓ Agents updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update agents[/yellow]")

    # Update scripts (preserve script type)
    console.print(f"\n[bold cyan]2. Updating scripts ({script_type.upper()})[/bold cyan]")
    if setup.copy_scripts(target_dir, script_type):
        console.print("  [green]✓ Scripts updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update scripts[/yellow]")

    # Update commands
    console.print("\n[bold cyan]3. Updating commands[/bold cyan]")
    if setup.copy_commands(target_dir):
        console.print("  [green]✓ Commands updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update commands[/yellow]")

    # Remove deprecated commands (old names without bazinga. prefix)
    console.print("\n[bold cyan]3.1. Removing deprecated commands[/bold cyan]")
    deprecated_commands = [
        "orchestrate.md",
        "orchestrate-from-spec.md",
        "configure-skills.md",
        "configure-testing.md",
    ]
    commands_dir = target_dir / ".claude" / "commands"
    if commands_dir.exists():
        removed_count = 0
        for cmd in deprecated_commands:
            cmd_path = commands_dir / cmd
            if cmd_path.exists():
                cmd_path.unlink()
                removed_count += 1
                console.print(f"  ✓ Removed deprecated /{cmd.replace('.md', '')}")
        if removed_count == 0:
            console.print("  [dim]No deprecated commands found[/dim]")
        else:
            console.print(f"  [green]✓ Removed {removed_count} deprecated command(s)[/green]")
    else:
        console.print("  [yellow]⚠️  Commands directory not found[/yellow]")

    # Remove deprecated state files (migrated to database)
    console.print("\n[bold cyan]3.2. Removing deprecated state files[/bold cyan]")
    deprecated_state_files = [
        ("bazinga/pm_state.json", "PM state (now in database)"),
        ("bazinga/orchestrator_state.json", "Orchestrator state (now in database)"),
        ("bazinga/group_status.json", "Task groups (now in database)"),
        ("bazinga/next_session_task_list.md", "Task list (now in database)"),
        ("docs/orchestration-log.md", "Logs (now in database)"),
    ]
    removed_count = 0
    for file_path, description in deprecated_state_files:
        full_path = target_dir / file_path
        if full_path.exists():
            full_path.unlink()
            removed_count += 1
            console.print(f"  ✓ Removed {description}: {file_path}")
    if removed_count == 0:
        console.print("  [dim]No deprecated state files found[/dim]")
    else:
        console.print(f"  [green]✓ Removed {removed_count} deprecated file(s)[/green]")
        console.print("  [dim]All state is now in bazinga/bazinga.db[/dim]")

    # Update skills (preserve script type)
    console.print(f"\n[bold cyan]4. Updating skills ({script_type.upper()})[/bold cyan]")
    if setup.copy_skills(target_dir, script_type):
        console.print("  [green]✓ Skills updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update skills[/yellow]")

    # Update configuration (replace old BAZINGA section with new)
    console.print("\n[bold cyan]5. Updating configuration[/bold cyan]")
    setup.setup_config(target_dir, is_update=True)

    # Update dashboard from pre-built releases
    console.print("\n[bold cyan]6. Dashboard v2[/bold cyan]")
    # Auto-detect existing dashboard installation
    bazinga_dir = target_dir / "bazinga"
    dashboard_installed = (bazinga_dir / "dashboard-v2").exists()

    if not dashboard and not dashboard_installed:
        console.print("  [dim]Skipped (experimental; install: 'bazinga setup-dashboard')[/dim]")
    else:
        if dashboard_installed and not dashboard:
            console.print("  [dim]Existing dashboard detected, updating...[/dim]")
        bazinga_dir.mkdir(parents=True, exist_ok=True)

        # Check for orphaned dashboard from previous buggy update (extracted to wrong path)
        orphaned_dashboard = bazinga_dir / "bazinga" / "dashboard-v2"
        if orphaned_dashboard.exists():
            # Safety guards: ensure it's a directory, not a symlink, and within expected path
            try:
                is_safe_to_remove = (
                    orphaned_dashboard.is_dir()
                    and not orphaned_dashboard.is_symlink()
                    and os.path.commonpath([str(orphaned_dashboard.resolve()), str(bazinga_dir.resolve())]) == str(bazinga_dir.resolve())
                )
                if is_safe_to_remove:
                    console.print("  [yellow]⚠️  Found orphaned dashboard at bazinga/bazinga/dashboard-v2[/yellow]")
                    console.print("  [dim]This was created by a previous buggy update. Removing...[/dim]")
                    shutil.rmtree(orphaned_dashboard)
                    # Also remove empty parent if it exists
                    orphaned_parent = bazinga_dir / "bazinga"
                    if orphaned_parent.exists() and not any(orphaned_parent.iterdir()):
                        orphaned_parent.rmdir()
                    console.print("  [green]✓ Orphaned dashboard removed[/green]")
                else:
                    console.print("  [yellow]⚠️  Skipping orphan removal (unexpected path or symlink)[/yellow]")
            except Exception as e:
                console.print(f"  [yellow]⚠️  Could not remove orphaned dashboard: {e}[/yellow]")

        # Try to download pre-built dashboard from GitHub releases
        # Note: Pass target_dir (project root), not bazinga_dir - function adds /bazinga/dashboard-v2
        prebuilt_ok = False
        try:
            prebuilt_ok = download_prebuilt_dashboard(target_dir, force=True)
        except Exception as e:
            console.print(f"  [yellow]⚠️  Pre-built download failed: {e}. Falling back to source copy.[/yellow]")

        if prebuilt_ok:
            console.print("  [green]✓ Dashboard updated from release[/green]")
        else:
            # Fall back to copying source files if pre-built not available
            console.print("  [dim]Pre-built not available, copying source files...[/dim]")
            source_dashboard = setup.source_dir / "dashboard-v2"
            target_dashboard = bazinga_dir / "dashboard-v2"

            if source_dashboard.exists():
                try:
                    ignore_patterns = shutil.ignore_patterns('node_modules', '.next', '*.log')
                    if target_dashboard.exists():
                        for item in source_dashboard.iterdir():
                            if item.name in ['node_modules', '.next']:
                                continue
                            if item.is_file():
                                shutil.copy2(item, target_dashboard / item.name)
                            elif item.is_dir():
                                target_subdir = target_dashboard / item.name
                                if target_subdir.exists():
                                    shutil.rmtree(target_subdir)
                                shutil.copytree(item, target_subdir, ignore=ignore_patterns)
                    else:
                        shutil.copytree(source_dashboard, target_dashboard, ignore=ignore_patterns)
                    console.print("  [yellow]⚠️  Source files copied (run npm install && npm run build)[/yellow]")
                except Exception as e:
                    console.print(f"  [yellow]⚠️  Failed to copy dashboard: {e}[/yellow]")
            else:
                console.print("  [yellow]⚠️  Dashboard v2 not found[/yellow]")

    # Update templates
    console.print("\n[bold cyan]7. Updating templates[/bold cyan]")
    if setup.copy_templates(target_dir):
        console.print("  [green]✓ Templates updated[/green]")
    else:
        console.print("  [yellow]⚠️  No templates found[/yellow]")

    # Update config files
    console.print("\n[bold cyan]7.1. Updating config files[/bold cyan]")
    if setup.copy_bazinga_configs(target_dir):
        console.print("  [green]✓ Config files updated[/green]")
    else:
        console.print("  [yellow]⚠️  No config files found[/yellow]")

    # Update .claude templates
    console.print("\n[bold cyan]7.2. Updating .claude templates[/bold cyan]")
    if setup.copy_claude_templates(target_dir):
        console.print("  [green]✓ .claude templates updated[/green]")
    else:
        console.print("  [yellow]⚠️  No .claude templates found[/yellow]")

    # Install/update compaction recovery hook
    console.print("\n[bold cyan]7.3. Updating compaction recovery hook[/bold cyan]")
    setup.install_compact_recovery_hook(target_dir, script_type)

    # Update mini-dashboard
    console.print("\n[bold cyan]7.4. Updating mini-dashboard[/bold cyan]")
    setup.copy_mini_dashboard(target_dir)

    # Update dashboard dependencies
    console.print("\n[bold cyan]8. Dashboard dependencies[/bold cyan]")
    # Use same auto-detection: update if --dashboard OR dashboard was previously installed
    if dashboard or dashboard_installed:
        install_dashboard_dependencies(target_dir, force)
    else:
        console.print("  [dim]Skipped[/dim]")

    # Update .gitignore to prevent database merge conflicts
    console.print("\n[bold cyan]9. Configuring .gitignore[/bold cyan]")
    update_gitignore(target_dir)

    # Success message
    success_message = (
        "[bold green]✓ BAZINGA updated successfully![/bold green]\n\n"
        "[dim]Your coordination state files were preserved.[/dim]\n\n"
    )

    if cli_was_updated:
        success_message += (
            "[bold yellow]⚠️  CLI was updated during this run[/bold yellow]\n"
            "[yellow]Run 'bazinga update' again to use new CLI features.[/yellow]\n\n"
        )

    success_message += (
        "[bold]Next steps:[/bold]\n"
    )

    if cli_was_updated:
        success_message += "  • [cyan]bazinga update[/cyan] (run again to complete update)\n"

    success_message += "  • Review updated agent definitions if needed\n"
    success_message += "  • Continue using: /bazinga.orchestrate <your request>\n"
    success_message += "    [dim](or @orchestrator if you prefer)[/dim]"

    console.print(
        Panel.fit(
            success_message,
            title="🎉 Update Complete",
            border_style="green",
        )
    )

    # Track update (anonymous telemetry)
    track_command("update", __version__)


@app.command()
def setup_dashboard(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reinstall dependencies"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompts (for CI/automation)"
    ),
):
    """
    Install dashboard v2 dependencies for real-time orchestration monitoring.

    This command installs the required npm packages for the BAZINGA
    dashboard v2 (Next.js):
    - next (React framework)
    - react (UI library)
    - tailwindcss (styling)
    - drizzle-orm (database)
    - trpc (type-safe API)

    The dashboard provides real-time monitoring of orchestration sessions
    with workflow visualization, session analytics, and AI insights.
    """
    target_dir = Path.cwd()

    # Check if BAZINGA is installed
    if not (target_dir / ".claude" / "agents" / "orchestrator.md").exists():
        console.print(
            "[red]✗ BAZINGA not found in current directory[/red]\n"
            "Run 'bazinga init --here' to install BAZINGA first."
        )
        raise typer.Exit(1)

    # Check if dashboard-v2 folder exists
    dashboard_dir = target_dir / "bazinga" / "dashboard-v2"
    if not dashboard_dir.exists():
        console.print(
            "[yellow]⚠️  Dashboard v2 folder not found[/yellow]\n"
            "[dim]The dashboard was not installed during init (it's opt-in).[/dim]\n"
        )
        # Offer to download/install the dashboard
        console.print("[bold]Would you like to install the dashboard now?[/bold]")
        if not force and not yes:
            if not typer.confirm("  Install dashboard?", default=True):
                console.print("[yellow]Cancelled[/yellow]")
                console.print("[dim]You can install later with: bazinga setup-dashboard[/dim]")
                raise typer.Exit(0)

        # Download pre-built dashboard
        console.print("\n[bold]Installing dashboard v2...[/bold]")
        prebuilt_ok = False
        try:
            prebuilt_ok = download_prebuilt_dashboard(target_dir, force=True)
        except Exception as e:
            console.print(f"  [yellow]⚠️  Pre-built download failed: {e}[/yellow]")

        if prebuilt_ok:
            console.print("  [green]✓[/green] Dashboard installed from pre-built release")
        else:
            # Fall back to copying source files if we have access to them
            console.print("  [yellow]⚠️  Pre-built not available[/yellow]")
            console.print("  [dim]Try running 'bazinga update --dashboard' instead[/dim]")
            raise typer.Exit(1)

    # Check for node_modules indicating dependencies were already installed
    node_modules = dashboard_dir / "node_modules"
    if node_modules.exists() and not force:
        console.print("\n[bold green]✓ Dashboard v2 dependencies already installed![/bold green]\n")
        console.print("[dim]You can start the dashboard with:[/dim]")
        console.print("[dim]  cd bazinga/dashboard-v2 && npm run dev[/dim]")
        console.print("\n[dim]To reinstall, use: bazinga setup-dashboard --force[/dim]")
        return

    console.print("\n[bold]Dashboard v2 Dependency Installation[/bold]\n")

    # Check if npm is available
    if not check_command_exists("npm"):
        console.print("[red]✗ npm not found[/red]")
        console.print("[yellow]Please install Node.js first (https://nodejs.org)[/yellow]")
        raise typer.Exit(1)

    # Check if package.json exists
    package_json = dashboard_dir / "package.json"
    if not package_json.exists():
        console.print("[red]✗ package.json not found in dashboard-v2 folder[/red]")
        raise typer.Exit(1)

    console.print("[dim]Dashboard v2 uses Next.js with TypeScript[/dim]")
    console.print("[dim]This enables:[/dim]")
    console.print("[dim]  • Real-time session monitoring[/dim]")
    console.print("[dim]  • Session history and analytics[/dim]")
    console.print("[dim]  • Task group visualization[/dim]")
    console.print("[dim]  • Token usage tracking[/dim]")
    console.print("[dim]  • AI-powered insights[/dim]")
    console.print()

    # Prompt for confirmation (skip if --force or --yes)
    if not force and not yes:
        console.print("[bold]Installation options:[/bold]")
        console.print("  [cyan]y[/cyan] - Install dependencies now (npm install)")
        console.print("  [cyan]n[/cyan] - Skip for now")
        console.print()

        choice = typer.prompt(
            "Install dashboard dependencies?",
            type=str,
            default="y",
            show_default=True,
        ).lower()

        if choice not in ["y", "yes"]:
            console.print("\n[yellow]⏭️  Skipped dashboard dependency installation[/yellow]")
            console.print("\n[dim]You can install manually later:[/dim]")
            console.print(f"[dim]  cd bazinga/dashboard-v2 && npm install[/dim]")
            return

    # Install dependencies
    console.print("\n[bold cyan]Installing npm dependencies (this may take a minute)...[/bold cyan]\n")

    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=dashboard_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout for npm
        )

        if result.returncode == 0:
            console.print("[bold green]✓ Dashboard v2 dependencies installed successfully![/bold green]\n")
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Start the dashboard:")
            console.print("     [cyan]cd bazinga/dashboard-v2 && npm run dev[/cyan]")
            console.print("  2. Open in browser:")
            console.print("     [cyan]http://localhost:3000[/cyan]")
            console.print("\n[dim]Or the dashboard will auto-start when you run orchestration:[/dim]")
            console.print("[dim]  ./scripts/init-orchestration.sh[/dim]")
        else:
            console.print("[yellow]⚠️  npm install completed with warnings[/yellow]")
            if result.stderr:
                console.print(f"\n[dim]Details:[/dim]")
                console.print(f"[dim]{result.stderr[:500]}[/dim]")
            console.print("\n[yellow]Try starting the dashboard anyway:[/yellow]")
            console.print("  [cyan]cd bazinga/dashboard-v2 && npm run dev[/cyan]")

    except subprocess.TimeoutExpired:
        console.print("[red]✗ npm install timed out[/red]")
        console.print("[yellow]Try installing manually:[/yellow]")
        console.print(f"  [cyan]cd bazinga/dashboard-v2 && npm install[/cyan]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗ Installation failed: {e}[/red]")
        console.print("\n[yellow]Try installing manually:[/yellow]")
        console.print(f"  [cyan]cd bazinga/dashboard-v2 && npm install[/cyan]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show BAZINGA CLI version."""
    console.print(f"[bold]BAZINGA CLI[/bold] version [cyan]{__version__}[/cyan]")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
):
    """
    BAZINGA - Multi-Agent Orchestration System for Claude Code.

    A sophisticated multi-agent system coordinating autonomous development teams
    including Project Manager, Developers, QA Expert, Tech Lead, Investigator,
    and Requirements Engineer agents.
    """
    if version_flag:
        console.print(f"[bold]BAZINGA CLI[/bold] version [cyan]{__version__}[/cyan]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(
            "[bold]Available commands:[/bold]\n"
            "  [cyan]init[/cyan]           - Initialize a new BAZINGA project\n"
            "  [cyan]update[/cyan]         - Update BAZINGA components to latest version\n"
            "  [cyan]setup-dashboard[/cyan] - Install dashboard dependencies\n"
            "  [cyan]check[/cyan]          - Check system requirements and setup\n"
            "  [cyan]version[/cyan]        - Show version information\n\n"
            "[dim]Use 'bazinga --help' for more information[/dim]"
        )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
