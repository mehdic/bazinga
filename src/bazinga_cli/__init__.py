#!/usr/bin/env python3
"""
BAZINGA CLI - Multi-Agent Orchestration System for Claude Code

A sophisticated multi-agent orchestration system that coordinates autonomous
development teams including Project Manager, Developers, QA Expert, and Tech Lead.
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

__version__ = "0.1.3"

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
            shutil.copy2(agent_file, agents_dir / agent_file.name)
            console.print(f"  ✓ Copied {agent_file.name}")

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

        source_commands = self.source_dir / "commands"
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

                # Copy appropriate script file
                for script_file in skill_dir.glob("*"):
                    if script_file.suffix in [".sh", ".ps1"]:
                        if script_file.suffix == script_extension:
                            dest = dest_skill_dir / script_file.name
                            shutil.copy2(script_file, dest)

                            # Make shell scripts executable on Unix-like systems
                            if script_file.suffix == ".sh" and os.name != 'nt':
                                dest.chmod(0o755)

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
                result = subprocess.run(
                    ["bash", str(init_script)],
                    cwd=target_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                console.print(f"  ✓ Initialized coordination files")
                return True
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
                result = subprocess.run(
                    [pwsh_cmd, "-ExecutionPolicy", "Bypass", "-File", str(init_script)],
                    cwd=target_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                console.print(f"  ✓ Initialized coordination files")
                return True
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
    tool_commands = {
        "python": {
            "tools": ["bandit", "semgrep", "pytest", "pytest-cov", "ruff"],
            "command": ["pip", "install", "bandit", "semgrep", "pytest", "pytest-cov", "ruff"],
            "description": "Python analysis tools (bandit, semgrep, pytest, pytest-cov, ruff)",
        },
        "javascript": {
            "tools": ["jest", "eslint", "eslint-plugin-security"],
            "command": ["npm", "install", "--save-dev", "jest", "eslint", "eslint-plugin-security", "@jest/globals"],
            "description": "JavaScript analysis tools (jest, eslint, eslint-plugin-security)",
        },
        "go": {
            "tools": ["gosec", "golangci-lint"],
            "command": None,  # Special handling for Go
            "description": "Go analysis tools (gosec, golangci-lint)",
        },
        "java": {
            "tools": ["maven/gradle plugins"],
            "command": None,  # Requires pom.xml/build.gradle configuration
            "description": "Java analysis tools (via Maven/Gradle plugins)",
        },
        "ruby": {
            "tools": ["brakeman", "rubocop"],
            "command": ["gem", "install", "brakeman", "rubocop"],
            "description": "Ruby analysis tools (brakeman, rubocop)",
        },
    }

    if language not in tool_commands:
        return True  # Unknown language, skip

    config = tool_commands[language]

    if not force:
        console.print(f"\n[bold yellow]Install analysis tools for {language.capitalize()}?[/bold yellow]")
        console.print(f"[dim]Tools: {config['description']}[/dim]")
        console.print("[dim]These tools enable automated security scanning, test coverage, and linting.[/dim]\n")

        if not typer.confirm("Install now?", default=True):
            console.print("[yellow]⏭️  Skipped tool installation[/yellow]")
            console.print(f"[dim]You can install manually later using the commands in Skills documentation[/dim]")
            return True

    # Special handling for Go
    if language == "go":
        console.print(f"\n[bold cyan]Installing Go tools...[/bold cyan]")

        # Install gosec
        if not check_command_exists("gosec"):
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
        else:
            console.print("    [dim]✓ gosec already installed[/dim]")

        # Install golangci-lint
        if not check_command_exists("golangci-lint"):
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
        else:
            console.print("    [dim]✓ golangci-lint already installed[/dim]")

        return True

    # Special handling for Java
    if language == "java":
        console.print(f"\n[bold yellow]ℹ️  Java tools require Maven/Gradle configuration[/bold yellow]")
        console.print("[dim]Analysis tools for Java are configured via build plugins:[/dim]")
        console.print("[dim]  • SpotBugs + Find Security Bugs (security scanning)[/dim]")
        console.print("[dim]  • JaCoCo (test coverage)[/dim]")
        console.print("[dim]  • Checkstyle + PMD (linting)[/dim]")
        console.print(f"[dim]\nSee .claude/skills/*/SKILL.md for configuration examples.[/dim]")
        return True

    # Python, JavaScript, Ruby
    if config["command"]:
        console.print(f"\n[bold cyan]Installing {language.capitalize()} tools...[/bold cyan]")

        try:
            # Check if package manager exists
            package_manager = config["command"][0]
            if not check_command_exists(package_manager):
                console.print(f"[red]✗ {package_manager} not found[/red]")
                console.print(f"[yellow]Please install {package_manager} first, then run tools installation manually[/yellow]")
                return False

            # Run installation command
            result = subprocess.run(
                config["command"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
            )

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
):
    """
    Initialize a new BAZINGA project with multi-agent orchestration.

    This will set up the complete multi-agent system including:
    - Agent definitions (orchestrator, PM, developer, QA, tech lead)
    - Initialization scripts
    - Configuration files
    - Coordination state files
    """
    print_banner()

    # Ask for script type preference
    script_type = select_script_type()

    # Determine target directory
    if here:
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
        target_dir = Path.cwd() / project_name
        if target_dir.exists():
            console.print(f"[red]✗ Directory '{project_name}' already exists[/red]")
            raise typer.Exit(1)
        target_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"\n[green]✓[/green] Created directory: [bold]{target_dir}[/bold]")
    else:
        console.print(
            "[red]Error:[/red] Please provide a project name or use --here flag"
        )
        console.print("\nExamples:")
        console.print("  bazinga init my-project")
        console.print("  bazinga init --here")
        raise typer.Exit(1)

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

        console.print("\n[bold cyan]6. Initializing coordination files[/bold cyan]")
        setup.run_init_script(target_dir, script_type)

    # Offer to install analysis tools
    detected_language = detect_project_language(target_dir)
    if detected_language:
        install_analysis_tools(target_dir, detected_language, force)

    # Initialize git if requested
    if not no_git and check_command_exists("git"):
        console.print("\n[bold cyan]7. Initializing git repository[/bold cyan]")
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
    console.print(
        Panel.fit(
            "[bold green]✓ BAZINGA installed successfully![/bold green]\n\n"
            "Your multi-agent orchestration system is ready.\n\n"
            "[bold]Next steps:[/bold]\n"
            f"  1. cd {target_dir.name if project_name else '.'}\n"
            "  2. Open with Claude Code\n"
            "  3. Use: @orchestrator <your request>\n\n"
            "[bold]Example:[/bold]\n"
            "  @orchestrator implement user authentication with JWT",
            title="🎉 Installation Complete",
            border_style="green",
        )
    )

    # Show structure
    console.print("\n[bold]Installed structure:[/bold]")
    tree = Table.grid(padding=(0, 2))
    tree.add_row("📁", ".claude/")
    tree.add_row("  ", "├── agents/      [dim](orchestrator, PM, dev, QA, tech lead)[/dim]")
    tree.add_row("  ", "├── commands/    [dim](slash commands)[/dim]")
    tree.add_row("  ", "├── scripts/     [dim](initialization scripts)[/dim]")
    tree.add_row("  ", "└── skills/      [dim](security-scan, test-coverage, lint-check)[/dim]")
    tree.add_row("📁", "coordination/    [dim](state files for agent coordination)[/dim]")
    tree.add_row("📄", ".claude.md       [dim](global configuration)[/dim]")
    console.print(tree)


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
    coordination_dir = cwd / "coordination"

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
        ]
        missing_agents = [
            agent for agent in required_agents if not (agents_dir / agent).exists()
        ]

        if missing_agents:
            checks.append(
                ("Agent Files", False, f"Missing: {', '.join(missing_agents)}")
            )
        else:
            checks.append(("Agent Files", True, "All 5 agents present"))

        if coordination_dir.exists():
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


@app.command()
def update(
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompts"
    ),
):
    """
    Update BAZINGA components in the current project.

    Updates agent definitions, scripts, and commands to the latest versions
    while preserving coordination state files and existing configuration.
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
        console.print(
            "\n[yellow]This will update BAZINGA components:[/yellow]\n"
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

    setup = BazingaSetup()

    # Detect which script type is currently installed
    script_type = setup.detect_script_type(target_dir)

    console.print("\n[bold]Updating BAZINGA components...[/bold]\n")

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

    # Update skills (preserve script type)
    console.print(f"\n[bold cyan]4. Updating skills ({script_type.upper()})[/bold cyan]")
    if setup.copy_skills(target_dir, script_type):
        console.print("  [green]✓ Skills updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update skills[/yellow]")

    # Update configuration (replace old BAZINGA section with new)
    console.print("\n[bold cyan]5. Updating configuration[/bold cyan]")
    setup.setup_config(target_dir, is_update=True)

    # Success message
    console.print(
        Panel.fit(
            "[bold green]✓ BAZINGA updated successfully![/bold green]\n\n"
            "[dim]Your coordination state files were preserved.[/dim]\n\n"
            "[bold]Next steps:[/bold]\n"
            "  • Review updated agent definitions if needed\n"
            "  • Continue using: @orchestrator <your request>",
            title="🎉 Update Complete",
            border_style="green",
        )
    )


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
    including Project Manager, Developers, QA Expert, and Tech Lead agents.
    """
    if version_flag:
        console.print(f"[bold]BAZINGA CLI[/bold] version [cyan]{__version__}[/cyan]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(
            "[bold]Available commands:[/bold]\n"
            "  [cyan]init[/cyan]    - Initialize a new BAZINGA project\n"
            "  [cyan]update[/cyan]  - Update BAZINGA components to latest version\n"
            "  [cyan]check[/cyan]   - Check system requirements and setup\n"
            "  [cyan]version[/cyan] - Show version information\n\n"
            "[dim]Use 'bazinga --help' for more information[/dim]"
        )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
