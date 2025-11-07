#!/usr/bin/env python3
"""
BAZINGA CLI - Multi-Agent Orchestration System for Claude Code

A sophisticated multi-agent orchestration system that coordinates autonomous
development teams including Project Manager, Developers, QA Expert, and Tech Lead.
"""

import os
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

__version__ = "0.1.0"

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
            # When installed via pip/uvx, files are in the package directory
            self.source_dir = Path(__file__).parent.parent.parent
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

    def copy_scripts(self, target_dir: Path) -> bool:
        """Copy scripts to target .claude/scripts directory."""
        scripts_dir = target_dir / ".claude" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        source_scripts = self.source_dir / "scripts"
        if not source_scripts.exists():
            return False

        for script_file in source_scripts.glob("*"):
            if script_file.is_file():
                dest = scripts_dir / script_file.name
                shutil.copy2(script_file, dest)
                # Make scripts executable
                if script_file.suffix == ".sh":
                    dest.chmod(0o755)
                console.print(f"  ✓ Copied {script_file.name}")

        return True

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

    def setup_config(self, target_dir: Path) -> bool:
        """
        Setup global configuration, merging with existing .claude.md if present.

        Strategy:
        1. Check if .claude.md or .claude/.claude.md exists in target
        2. If exists, read it and check if BAZINGA config is already present
        3. If not present, append BAZINGA config (intelligently or at bottom)
        4. If doesn't exist, create new .claude.md with our content
        """
        source_config = self.source_dir / "config" / "claude.md"
        if not source_config.exists():
            return False

        # Read BAZINGA configuration
        with open(source_config, 'r') as f:
            bazinga_config = f.read()

        # Check for existing .claude.md in project root or .claude/ directory
        possible_locations = [
            target_dir / ".claude.md",
            target_dir / ".claude" / ".claude.md",
        ]

        existing_config_path = None
        for path in possible_locations:
            if path.exists():
                existing_config_path = path
                break

        if existing_config_path:
            # Read existing configuration
            with open(existing_config_path, 'r') as f:
                existing_content = f.read()

            # Check if BAZINGA configuration is already present
            if "BAZINGA" in existing_content or "Orchestrator Role Enforcement" in existing_content:
                console.print(f"  ℹ️  BAZINGA config already present in {existing_config_path.name}")
                return True

            # Extract BAZINGA-specific content (everything after the first header section)
            # BAZINGA config starts with the critical orchestrator enforcement section
            bazinga_lines = bazinga_config.split('\n')

            # Find where BAZINGA-specific config starts (after initial project context)
            bazinga_start_markers = [
                "## ⚠️ CRITICAL: Orchestrator Role Enforcement",
                "---",
            ]

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

            # Merge: Add BAZINGA config to existing file
            # Try to insert after initial project description (first 4-5 lines)
            existing_lines = existing_content.split('\n')

            # Simple strategy: append to bottom with clear separator
            merged_content = existing_content.rstrip() + '\n\n' + bazinga_config_section

            # Write merged configuration
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

    def run_init_script(self, target_dir: Path) -> bool:
        """Run the initialization script to set up coordination files."""
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


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def print_banner():
    """Print BAZINGA banner."""
    banner = """
██████╗  █████╗ ███████╗██╗███╗   ██╗ ██████╗  █████╗
██╔══██╗██╔══██╗╚══███╔╝██║████╗  ██║██╔════╝ ██╔══██╗
██████╔╝███████║  ███╔╝ ██║██╔██╗ ██║██║  ███╗███████║
██╔══██╗██╔══██║ ███╔╝  ██║██║╚██╗██║██║   ██║██╔══██║
██████╔╝██║  ██║███████╗██║██║ ╚████║╚██████╔╝██║  ██║
╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print(
        "[bold]Multi-Agent Orchestration System for Claude Code[/bold]\n",
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

        console.print("\n[bold cyan]2. Copying scripts[/bold cyan]")
        if not setup.copy_scripts(target_dir):
            console.print("[yellow]⚠️  No scripts found[/yellow]")

        console.print("\n[bold cyan]3. Copying commands[/bold cyan]")
        if not setup.copy_commands(target_dir):
            console.print("[yellow]⚠️  No commands found[/yellow]")

        console.print("\n[bold cyan]4. Setting up configuration[/bold cyan]")
        if not setup.setup_config(target_dir):
            console.print("[red]✗ Failed to setup configuration[/red]")
            raise typer.Exit(1)

        console.print("\n[bold cyan]5. Initializing coordination files[/bold cyan]")
        setup.run_init_script(target_dir)

    # Initialize git if requested
    if not no_git and check_command_exists("git"):
        console.print("\n[bold cyan]6. Initializing git repository[/bold cyan]")
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
    tree.add_row("  ", "└── scripts/     [dim](initialization scripts)[/dim]")
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
            "  • Configuration (.claude.md - merged if needed)\n\n"
            "[dim]Coordination files will NOT be modified[/dim]\n"
        )
        confirm = typer.confirm("Continue with update?")
        if not confirm:
            console.print("[red]Cancelled[/red]")
            raise typer.Exit(1)

    setup = BazingaSetup()

    console.print("\n[bold]Updating BAZINGA components...[/bold]\n")

    # Update agents
    console.print("[bold cyan]1. Updating agent definitions[/bold cyan]")
    if setup.copy_agents(target_dir):
        console.print("  [green]✓ Agents updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update agents[/yellow]")

    # Update scripts
    console.print("\n[bold cyan]2. Updating scripts[/bold cyan]")
    if setup.copy_scripts(target_dir):
        console.print("  [green]✓ Scripts updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update scripts[/yellow]")

    # Update commands
    console.print("\n[bold cyan]3. Updating commands[/bold cyan]")
    if setup.copy_commands(target_dir):
        console.print("  [green]✓ Commands updated[/green]")
    else:
        console.print("  [yellow]⚠️  Failed to update commands[/yellow]")

    # Update configuration (merge if needed)
    console.print("\n[bold cyan]4. Updating configuration[/bold cyan]")
    setup.setup_config(target_dir)

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
