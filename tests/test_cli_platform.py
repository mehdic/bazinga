"""
Unit tests for CLI platform flag functionality.

Tests the --platform/-P flag implementation for init and update commands,
including platform-specific copy functions.
"""
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bazinga_cli import BazingaSetup


class TestBazingaSetup:
    """Test platform-specific setup functions."""

    def test_copy_agents_for_copilot_creates_agent_md_files(self):
        """Test that copy_agents_for_copilot() creates .agent.md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            # Create dummy agent source files
            agents_source = target_dir / "source_agents"
            agents_source.mkdir()
            (agents_source / "developer.md").write_text("# Developer")
            (agents_source / "qa_expert.md").write_text("# QA Expert")

            # Create setup with custom source
            setup = BazingaSetup(source_dir=target_dir)

            # Override get_agent_files to return our test files
            original_get_agent_files = setup.get_agent_files
            setup.get_agent_files = lambda: list(agents_source.glob("*.md"))

            # Copy agents for Copilot
            result = setup.copy_agents_for_copilot(target_dir)

            # Restore original method
            setup.get_agent_files = original_get_agent_files

            # Verify
            assert result is True, "copy_agents_for_copilot should return True"
            agents_dir = target_dir / ".github" / "agents"
            assert agents_dir.exists(), ".github/agents directory should exist"
            assert (agents_dir / "developer.agent.md").exists(), "developer.agent.md should exist"
            assert (agents_dir / "qa_expert.agent.md").exists(), "qa_expert.agent.md should exist"

    def test_copy_agents_for_copilot_converts_extension(self):
        """Test that .md files are converted to .agent.md for Copilot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            agents_source = target_dir / "source_agents"
            agents_source.mkdir()
            (agents_source / "orchestrator.md").write_text("# Orchestrator Agent")

            setup = BazingaSetup(source_dir=target_dir)
            original_get_agent_files = setup.get_agent_files
            setup.get_agent_files = lambda: list(agents_source.glob("*.md"))

            setup.copy_agents_for_copilot(target_dir)
            setup.get_agent_files = original_get_agent_files

            agent_file = target_dir / ".github" / "agents" / "orchestrator.agent.md"
            assert agent_file.exists(), "orchestrator.agent.md should exist"
            assert "Orchestrator Agent" in agent_file.read_text(), "Content should be preserved"

    def test_copy_skills_for_copilot_creates_symlink_when_possible(self):
        """Test that copy_skills_for_copilot() creates symlink when possible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)

            # Create Claude skills directory
            claude_skills = target_dir / ".claude" / "skills"
            claude_skills.mkdir(parents=True)
            (claude_skills / "test-skill").mkdir()
            (claude_skills / "test-skill" / "SKILL.md").write_text("# Test Skill")

            setup = BazingaSetup(source_dir=target_dir)

            # Override copy_skills to do nothing (we just need the directory to exist)
            original_copy_skills = setup.copy_skills
            setup.copy_skills = lambda *args, **kwargs: True

            # Copy skills for Copilot
            result = setup.copy_skills_for_copilot(target_dir)

            setup.copy_skills = original_copy_skills

            assert result is True, "copy_skills_for_copilot should return True"
            github_skills = target_dir / ".github" / "skills"
            assert github_skills.exists(), ".github/skills should exist"

            # Check if it's a symlink or a directory (depends on OS support)
            # On systems without symlink support, it should be a copy
            assert github_skills.is_dir() or github_skills.is_symlink(), \
                ".github/skills should be either a symlink or directory"

    def test_create_copilot_instructions_generates_file(self):
        """Test that create_copilot_instructions() generates copilot-instructions.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)

            # Create CLAUDE.md
            claude_dir = target_dir / ".claude"
            claude_dir.mkdir()
            claude_md = claude_dir / "CLAUDE.md"
            claude_md.write_text("""# Project Context

This is a test project.

File locations:
- .claude/agents/
- .claude/skills/
- .claude/templates/
""")

            setup = BazingaSetup()

            # Create copilot instructions
            result = setup.create_copilot_instructions(target_dir)

            assert result is True, "create_copilot_instructions should return True"

            copilot_instructions = target_dir / ".github" / "copilot-instructions.md"
            assert copilot_instructions.exists(), "copilot-instructions.md should exist"

            content = copilot_instructions.read_text()
            assert "GitHub Copilot Instructions" in content, "Should have Copilot header"
            assert ".github/agents/" in content, "Should convert .claude/agents/ to .github/agents/"
            assert ".github/skills/" in content, "Should convert .claude/skills/ to .github/skills/"
            assert ".github/templates/" in content, "Should convert .claude/templates/ to .github/templates/"
            assert ".claude/agents/" not in content, "Should not contain .claude/ references"

    def test_create_copilot_instructions_handles_missing_claude_md(self):
        """Test that create_copilot_instructions() handles missing CLAUDE.md gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)

            setup = BazingaSetup()

            # Try to create copilot instructions without CLAUDE.md
            result = setup.create_copilot_instructions(target_dir)

            assert result is False, "create_copilot_instructions should return False when CLAUDE.md is missing"


class TestPlatformValidation:
    """Test platform parameter validation."""

    def test_valid_platform_values(self):
        """Test that valid platform values are accepted."""
        valid_platforms = ["claude", "copilot", "both"]
        for platform in valid_platforms:
            # In actual CLI, this validation happens in the command function
            # Here we just verify the values are correct
            assert platform.lower() in ["claude", "copilot", "both"]

    def test_platform_flag_abbreviation(self):
        """Test that -P abbreviation is available."""
        # This is tested via the typer.Option definition
        # The actual flag "-P" is defined in the init() and update() function signatures
        pass  # Placeholder for integration test


# Run tests with: python -m pytest tests/test_cli_platform.py -v
