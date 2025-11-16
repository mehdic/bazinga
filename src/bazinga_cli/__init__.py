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

console = Console()
app = typer.Typer(
    name="bazinga",
    help="BAZINGA - Multi-Agent Orchestration System for Claude Code",
    add_completion=False,
    rich_markup_mode="rich",
)


class BazingaSetup:
    """Handles BAZINGA installation and setup."""

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
        Copy scripts to target .claude/scripts directory.

        Args:
            target_dir: Target directory for installation
            script_type: "sh" for POSIX shell or "ps" for PowerShell
        """
        scripts_dir = target_dir / ".claude" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        source_scripts = self.source_dir / "scripts"
        if not source_scripts.exists():
            return False

        # Determine which extension to copy based on script type
        script_extension = ".sh" if script_type == "sh" else ".ps1"

        copied_count = 0
        for script_file in source_scripts.glob("*"):
            if script_file.is_file():
                # Skip non-script files (README, etc.) or wrong script type
                if script_file.suffix in [".sh", ".ps1"]:
                    if script_file.suffix != script_extension:
                        continue  # Skip scripts of the other type

                dest = scripts_dir / script_file.name
                shutil.copy2(script_file, dest)

                # Make shell scripts executable on Unix-like systems
                if script_file.suffix == ".sh" and os.name != 'nt':
                    dest.chmod(0o755)

                console.print(f"  ✓ Copied {script_file.name}")
                copied_count += 1

        # Also copy README if it exists
        readme_file = source_scripts / "README.md"
        if readme_file.exists():
            dest = scripts_dir / "README.md"
            shutil.copy2(readme_file, dest)
            console.print(f"  ✓ Copied README.md")

        return copied_count > 0

    def copy_commands(self, target_dir: Path) -> bool:
        """Copy commands to target .claude/commands directory."""
        commands_dir = target_dir / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)

        source_commands = self.source_dir / ".claude" / "commands"
        if not source_commands.exists():
            return False

        for cmd_file in source_commands.glob("*.md"):
            shutil.copy2(cmd_file, commands_dir / cmd_file.name)
            console.print(f"  ✓ Copied {cmd_file.name}")

        return True

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

    def setup_config(self, target_dir: Path, is_update: bool = False) -> bool:
        """
        Setup global configuration, merging with existing .claude.md if present.

        Strategy:
        1. Check if .claude.md or .claude/.claude.md exists in target
        2. If exists and is_update=True, replace old BAZINGA section with new one
        3. If exists and is_update=False, append if not present
        4. If doesn't exist, create new .claude.md with our content

        Args:
            target_dir: Target directory for installation
            is_update: If True, replaces existing BAZINGA config with new version
        """
        source_config = self.source_dir / "config" / "claude.md"
        if not source_config.exists():
            return False

        # Read BAZINGA configuration
        with open(source_config, 'r') as f:
            bazinga_config = f.read()

        # Extract BAZINGA-specific content
        bazinga_lines = bazinga_config.split('\n')
        bazinga_config_section = None
        for i, line in enumerate(bazinga_lines):
            if "⚠️ CRITICAL" in line or "Orchestrator Role Enforcement" in line:
                # Include separator line before this section
                start_idx = max(0, i - 2)  # Include the --- separator
                bazinga_config_section = '\n'.join(bazinga_lines[start_idx:])
                break

        if not bazinga_config_section:
            # Fallback: use everything after line 7
            bazinga_config_section = '\n'.join(bazinga_lines[7:])

        # Check for existing .claude.md in project root or .claude/ directory
        # Check multiple variations (case-insensitive)
        possible_filenames = [
            ".claude.md",    # Recommended format
            "claude.md",     # Without dot
            "CLAUDE.md",     # Uppercase without dot
            ".CLAUDE.md",    # Uppercase with dot
        ]

        possible_locations = []
        # Check in project root
        for filename in possible_filenames:
            possible_locations.append(target_dir / filename)
        # Check in .claude/ directory
        for filename in possible_filenames:
            possible_locations.append(target_dir / ".claude" / filename)

        existing_config_path = None
        for path in possible_locations:
            if path.exists():
                existing_config_path = path
                console.print(f"  [dim]Found existing config: {path.name}[/dim]")
                break

        if existing_config_path:
            # Read existing configuration
            with open(existing_config_path, 'r') as f:
                existing_content = f.read()

            # Check if BAZINGA configuration is already present
            has_bazinga = "BAZINGA" in existing_content or "Orchestrator Role Enforcement" in existing_content

            if has_bazinga and is_update:
                # Update mode: Replace old BAZINGA section with new one
                try:
                    # Try to intelligently replace the BAZINGA section
                    updated_content = self._replace_bazinga_section(
                        existing_content,
                        bazinga_config_section
                    )

                    if updated_content is None:
                        # Couldn't automatically update - save to separate file
                        update_file = existing_config_path.parent / f"{existing_config_path.name}.bazinga-update"
                        with open(update_file, 'w') as f:
                            f.write(bazinga_config_section)

                        console.print(
                            f"  ⚠️  Could not automatically update {existing_config_path.name}\n"
                            f"      New BAZINGA config saved to: {update_file.name}\n"
                            f"      Please manually merge the changes."
                        )
                        return True

                    # Successfully created updated content
                    with open(existing_config_path, 'w') as f:
                        f.write(updated_content)

                    console.print(f"  ✓ Updated BAZINGA config in {existing_config_path.name}")
                    return True

                except Exception as e:
                    # Error during update - save to separate file
                    update_file = existing_config_path.parent / f"{existing_config_path.name}.bazinga-update"
                    with open(update_file, 'w') as f:
                        f.write(bazinga_config_section)

                    console.print(
                        f"  ⚠️  Error updating {existing_config_path.name}: {e}\n"
                        f"      New BAZINGA config saved to: {update_file.name}\n"
                        f"      Please manually merge the changes."
                    )
                    return True

            elif has_bazinga and not is_update:
                # Init mode: Already has BAZINGA, skip
                console.print(f"  ℹ️  BAZINGA config already present in {existing_config_path.name}")
                return True

            else:
                # No BAZINGA section - append it
                merged_content = existing_content.rstrip() + '\n\n' + bazinga_config_section

                with open(existing_config_path, 'w') as f:
                    f.write(merged_content)

                console.print(f"  ✓ Merged BAZINGA config into existing {existing_config_path.name}")
                return True
        else:
            # No existing config, create new one
            dest_config = target_dir / ".claude.md"
            shutil.copy2(source_config, dest_config)
            console.print(f"  ✓ Created .claude.md with BAZINGA config")
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
            "install_cmd": lambda tools: ["pip", "install"] + tools,
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


def install_dashboard_dependencies(target_dir: Path, force: bool = False) -> bool:
    """
    Install dashboard dependencies for real-time orchestration monitoring.

    Args:
        target_dir: Project directory
        force: Skip confirmation prompt

    Returns:
        True if dependencies were installed successfully or skipped, False if failed
    """
    dashboard_dir = target_dir / "dashboard"

    # Check if dashboard folder exists
    if not dashboard_dir.exists():
        console.print("  [dim]Dashboard folder not found, skipping dependency installation[/dim]")
        return True

    requirements_file = dashboard_dir / "requirements.txt"
    if not requirements_file.exists():
        console.print("  [yellow]⚠️  requirements.txt not found in dashboard folder[/yellow]")
        return True

    # Check for marker file indicating dependencies were already installed
    marker_file = dashboard_dir / ".deps-installed"
    if marker_file.exists() and not force:
        console.print("  [green]✓[/green] Dashboard dependencies already installed")
        return True

    # Define required packages
    required_packages = [
        ("flask", "flask"),
        ("flask-sock", "flask_sock"),
        ("watchdog", "watchdog"),
        ("anthropic", "anthropic"),
    ]

    # Check which packages are already installed
    missing = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if not missing:
        console.print("  [green]✓[/green] Dashboard dependencies already installed")
        # Create marker file so we don't check again
        marker_file.touch()
        return True

    # Show what needs to be installed
    console.print(f"  [dim]Missing packages: {', '.join(missing)}[/dim]")
    console.print("  [dim]These enable: real-time monitoring, workflow visualization, WebSocket updates[/dim]")

    if not force:
        if not typer.confirm("  Install dashboard dependencies?", default=True):
            console.print("  [yellow]⏭️  Skipped dashboard dependency installation[/yellow]")
            console.print(f"  [dim]You can install later with: bazinga setup-dashboard[/dim]")
            return True

    # Install dependencies
    try:
        # Check if pip is available
        if not check_command_exists("pip3") and not check_command_exists("pip"):
            console.print("  [yellow]⚠️  pip not found, skipping dashboard dependencies[/yellow]")
            console.print(f"  [dim]Install manually: cd dashboard && pip3 install -r requirements.txt[/dim]")
            return True

        pip_cmd = "pip3" if check_command_exists("pip3") else "pip"

        # Install using requirements.txt
        result = subprocess.run(
            [pip_cmd, "install", "-q", "-r", str(requirements_file)],
            cwd=dashboard_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            console.print("  [green]✓[/green] Dashboard dependencies installed")
            # Create marker file to skip prompt next time
            marker_file.touch()
            return True
        else:
            console.print("  [yellow]⚠️  Dashboard dependency installation completed with warnings[/yellow]")
            if result.stderr and "error" in result.stderr.lower():
                console.print(f"  [dim]{result.stderr[:200]}[/dim]")
            # Still create marker file to avoid repeated prompts
            marker_file.touch()
            return True  # Still return success, dependencies might work

    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠️  Dashboard dependency installation timed out[/yellow]")
        console.print(f"  [dim]Install manually: cd dashboard && pip3 install -r requirements.txt[/dim]")
        return True  # Don't fail the whole installation

    except Exception as e:
        console.print(f"  [yellow]⚠️  Dashboard dependency installation failed: {e}[/yellow]")
        console.print(f"  [dim]Install manually: cd dashboard && pip3 install -r requirements.txt[/dim]")
        return True  # Don't fail the whole installation


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

        console.print("\n[bold cyan]6. Copying dashboard files[/bold cyan]")
        source_dashboard = setup.source_dir / "dashboard"
        target_dashboard = target_dir / "dashboard"

        if source_dashboard.exists():
            try:
                shutil.copytree(source_dashboard, target_dashboard)
                console.print("  ✓ Dashboard installed")

                # Copy research folder too (for documentation)
                source_research = setup.source_dir / "research"
                target_research = target_dir / "research"
                if source_research.exists():
                    target_research.mkdir(parents=True, exist_ok=True)
                    dashboard_doc = source_research / "dashboard-feature.md"
                    if dashboard_doc.exists():
                        shutil.copy2(dashboard_doc, target_research / "dashboard-feature.md")
                        console.print("  ✓ Copied dashboard documentation")
            except Exception as e:
                console.print(f"  [yellow]⚠️  Failed to copy dashboard: {e}[/yellow]")
        else:
            console.print("  [yellow]⚠️  Dashboard not found in source[/yellow]")

        console.print("\n[bold cyan]7. Initializing coordination files[/bold cyan]")
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
    console.print("\n[bold cyan]8. Installing dashboard dependencies[/bold cyan]")
    install_dashboard_dependencies(target_dir, force)

    # Initialize git if requested
    if not no_git and check_command_exists("git"):
        console.print("\n[bold cyan]9. Initializing git repository[/bold cyan]")
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
    tree.add_row("  ", "└── skills/      [dim](security-scan, test-coverage, lint-check)[/dim]")
    tree.add_row("📁", "bazinga/    [dim](state files for agent coordination)[/dim]")
    tree.add_row("📄", ".claude.md       [dim](global configuration)[/dim]")
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
    config_file = cwd / ".claude.md"
    bazinga_dir = cwd / "bazinga"

    bazinga_installed = all(
        [
            claude_dir.exists(),
            agents_dir.exists(),
            config_file.exists(),
            (agents_dir / "orchestrator.md").exists(),
        ]
    )

    if bazinga_installed:
        checks.append(("BAZINGA Setup", True, "Found in current directory"))

        # Check for required agents
        required_agents = [
            "orchestrator.md",
            "project_manager.md",
            "developer.md",
            "qa_expert.md",
            "techlead.md",
            "investigator.md",
            "requirements_engineer.md",
        ]
        missing_agents = [
            agent for agent in required_agents if not (agents_dir / agent).exists()
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
        result = subprocess.run(
            ["pip", "show", "bazinga-cli"],
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
                        ["pip", "install", "-e", str(bazinga_repo), "--quiet"],
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
                    ["pip", "install", "--upgrade", git_url],
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
            "  • Skills (.claude/skills/)\n"
            "  • Configuration (.claude.md - merged if needed)\n\n"
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

    # Copy dashboard folder
    console.print("\n[bold cyan]6. Copying dashboard files[/bold cyan]")
    source_dashboard = setup.source_dir / "dashboard"
    target_dashboard = target_dir / "dashboard"

    if source_dashboard.exists():
        import shutil
        try:
            if target_dashboard.exists():
                # Update existing dashboard (preserve any custom modifications to server.py if any)
                for item in source_dashboard.iterdir():
                    if item.is_file():
                        shutil.copy2(item, target_dashboard / item.name)
                        console.print(f"  ✓ Updated {item.name}")
                    elif item.is_dir():
                        target_subdir = target_dashboard / item.name
                        if target_subdir.exists():
                            shutil.rmtree(target_subdir)
                        shutil.copytree(item, target_subdir)
                        console.print(f"  ✓ Updated {item.name}/")
            else:
                # Fresh copy of dashboard
                shutil.copytree(source_dashboard, target_dashboard)
                console.print("  ✓ Dashboard installed")

            # Copy research folder too (for documentation)
            source_research = setup.source_dir / "research"
            target_research = target_dir / "research"
            if source_research.exists():
                if not target_research.exists():
                    target_research.mkdir(parents=True, exist_ok=True)
                dashboard_doc = source_research / "dashboard-feature.md"
                if dashboard_doc.exists():
                    shutil.copy2(dashboard_doc, target_research / "dashboard-feature.md")
                    console.print("  ✓ Updated dashboard documentation")
        except Exception as e:
            console.print(f"  [yellow]⚠️  Failed to copy dashboard: {e}[/yellow]")
    else:
        console.print("  [yellow]⚠️  Dashboard not found in source[/yellow]")

    # Update dashboard dependencies
    console.print("\n[bold cyan]7. Installing dashboard dependencies[/bold cyan]")
    install_dashboard_dependencies(target_dir, force)

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
        False, "--force", "-f", help="Skip confirmation prompts"
    ),
):
    """
    Install dashboard dependencies for real-time orchestration monitoring.

    This command installs the required Python packages for the BAZINGA
    dashboard server:
    - flask (web server)
    - flask-sock (WebSocket support)
    - watchdog (file system monitoring)
    - anthropic (AI diagram generation)

    The dashboard provides real-time monitoring of orchestration sessions
    with workflow visualization, agent status tracking, and more.
    """
    target_dir = Path.cwd()

    # Check if BAZINGA is installed
    if not (target_dir / ".claude" / "agents" / "orchestrator.md").exists():
        console.print(
            "[red]✗ BAZINGA not found in current directory[/red]\n"
            "Run 'bazinga init --here' to install BAZINGA first."
        )
        raise typer.Exit(1)

    # Check if dashboard folder exists
    dashboard_dir = target_dir / "dashboard"
    if not dashboard_dir.exists():
        console.print(
            "[yellow]⚠️  Dashboard folder not found[/yellow]\n"
            "[dim]The dashboard may not be installed in this project.[/dim]\n"
            "[dim]Try running 'bazinga update' first.[/dim]"
        )
        raise typer.Exit(1)

    # Check for marker file indicating dependencies were already installed
    marker_file = dashboard_dir / ".deps-installed"
    if marker_file.exists() and not force:
        console.print("\n[bold green]✓ Dashboard dependencies already installed![/bold green]\n")
        console.print("[dim]You can start the dashboard with:[/dim]")
        console.print("[dim]  cd dashboard && ./dashboard.sh start[/dim]")
        console.print("[dim]  or: cd dashboard && python3 server.py[/dim]")
        console.print("\n[dim]To reinstall, use: bazinga setup-dashboard --force[/dim]")
        return

    console.print("\n[bold]Dashboard Dependency Installation[/bold]\n")

    # Define required packages
    required_packages = [
        ("flask", "3.0.0"),
        ("flask-sock", "0.7.0"),
        ("watchdog", "3.0.0"),
        ("anthropic", "0.39.0"),
    ]

    # Check which packages are already installed
    console.print("[bold cyan]Checking installed packages...[/bold cyan]\n")

    installed = []
    missing = []

    for package, version in required_packages:
        try:
            # Try importing to check if installed
            if package == "flask-sock":
                import flask_sock
                installed.append(f"{package}=={version}")
            elif package == "flask":
                import flask
                installed.append(f"{package}=={version}")
            elif package == "watchdog":
                import watchdog
                installed.append(f"{package}=={version}")
            elif package == "anthropic":
                import anthropic
                installed.append(f"{package}=={version}")
        except ImportError:
            missing.append(f"{package}=={version}")

    # Show status
    if installed:
        console.print("[green]✓ Already installed:[/green]")
        for pkg in installed:
            console.print(f"  [dim]• {pkg}[/dim]")
        console.print()

    if not missing:
        console.print("[bold green]✓ All dashboard dependencies are already installed![/bold green]\n")
        console.print("[dim]You can start the dashboard with:[/dim]")
        console.print("[dim]  cd dashboard && ./dashboard.sh start[/dim]")
        console.print("[dim]  or: cd dashboard && python3 server.py[/dim]")
        return

    # Show what needs to be installed
    console.print("[bold yellow]Missing dependencies:[/bold yellow]")
    for pkg in missing:
        console.print(f"  • {pkg}")
    console.print()

    console.print("[dim]These packages enable:[/dim]")
    console.print("[dim]  • Real-time WebSocket updates[/dim]")
    console.print("[dim]  • Workflow visualization[/dim]")
    console.print("[dim]  • Agent status tracking[/dim]")
    console.print("[dim]  • AI-powered diagrams (optional)[/dim]")
    console.print()

    # Prompt for confirmation
    if not force:
        console.print("[bold]Installation options:[/bold]")
        console.print("  [cyan]y[/cyan] - Install dependencies now")
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
            console.print(f"[dim]  cd dashboard[/dim]")
            console.print(f"[dim]  pip3 install -r requirements.txt[/dim]")
            console.print("\n[dim]Or run this command again:[/dim]")
            console.print(f"[dim]  bazinga setup-dashboard[/dim]")
            return

    # Install dependencies
    console.print("\n[bold cyan]Installing dashboard dependencies...[/bold cyan]\n")

    requirements_file = dashboard_dir / "requirements.txt"

    if not requirements_file.exists():
        console.print("[red]✗ requirements.txt not found in dashboard folder[/red]")
        raise typer.Exit(1)

    try:
        # Check if pip is available
        if not check_command_exists("pip3") and not check_command_exists("pip"):
            console.print("[red]✗ pip not found[/red]")
            console.print("[yellow]Please install pip first[/yellow]")
            raise typer.Exit(1)

        pip_cmd = "pip3" if check_command_exists("pip3") else "pip"

        # Install using requirements.txt
        result = subprocess.run(
            [pip_cmd, "install", "-r", str(requirements_file)],
            cwd=dashboard_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            console.print("[bold green]✓ Dashboard dependencies installed successfully![/bold green]\n")
            # Create marker file to skip prompt next time
            marker_file.touch()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Start the dashboard:")
            console.print("     [cyan]cd dashboard && ./dashboard.sh start[/cyan]")
            console.print("  2. Open in browser:")
            console.print("     [cyan]http://localhost:53124[/cyan]")
            console.print("\n[dim]Or the dashboard will auto-start when you run orchestration:[/dim]")
            console.print("[dim]  ./scripts/init-orchestration.sh[/dim]")
        else:
            console.print("[yellow]⚠️  Installation completed with warnings[/yellow]")
            if result.stderr:
                console.print(f"\n[dim]Error details:[/dim]")
                console.print(f"[dim]{result.stderr[:500]}[/dim]")
            # Still create marker file to avoid repeated prompts
            marker_file.touch()
            console.print("\n[yellow]Some dependencies may still work. Try starting the dashboard:[/yellow]")
            console.print("  [cyan]cd dashboard && python3 server.py[/cyan]")

    except subprocess.TimeoutExpired:
        console.print("[red]✗ Installation timed out[/red]")
        console.print("[yellow]Try installing manually:[/yellow]")
        console.print(f"  [cyan]cd dashboard && pip3 install -r requirements.txt[/cyan]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗ Installation failed: {e}[/red]")
        console.print("\n[yellow]Try installing manually:[/yellow]")
        console.print(f"  [cyan]cd dashboard && pip3 install -r requirements.txt[/cyan]")
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
