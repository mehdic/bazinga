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

    def copy_config(self, target_dir: Path) -> bool:
        """Copy global configuration to target directory."""
        source_config = self.source_dir / "config" / "claude.md"
        if not source_config.exists():
            return False

        dest_config = target_dir / ".claude.md"
        shutil.copy2(source_config, dest_config)
        console.print(f"  ✓ Copied .claude.md")
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

        console.print("\n[bold cyan]4. Copying configuration[/bold cyan]")
        if not setup.copy_config(target_dir):
            console.print("[red]✗ Failed to copy configuration[/red]")
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
            "  [cyan]check[/cyan]   - Check system requirements and setup\n"
            "  [cyan]version[/cyan] - Show version information\n\n"
            "[dim]Use 'bazinga --help' for more information[/dim]"
        )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
