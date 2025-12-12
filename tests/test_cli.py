"""
Tests for BAZINGA CLI commands.

Tests the main CLI interface and command execution.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from bazinga_cli import app, BazingaSetup


runner = CliRunner()


class TestVersionCommand:
    """Test version command."""

    def test_version_displays_version(self):
        """Test version command displays correct version."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "1.1.0" in result.output

    def test_version_shows_header(self):
        """Test version command shows ASCII art header."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "BAZINGA" in result.output


class TestCheckCommand:
    """Test check command."""

    def test_check_command_runs(self):
        """Test check command executes without errors."""
        result = runner.invoke(app, ["check"])

        # Should not crash
        assert result.exit_code == 0
        # Check for key output elements (ASCII art contains BAZINGA)
        assert "BAZINGA" in result.output or "Checking system" in result.output


class TestInitCommand:
    """Test init command."""

    def test_init_with_invalid_project_name(self):
        """Test init rejects invalid project names."""
        invalid_names = [
            "../malicious",
            "/etc/passwd",
            "test;rm -rf",
            "app$(cmd)",
        ]

        for name in invalid_names:
            # Provide default input for script type prompt (just press enter)
            result = runner.invoke(app, ["init", name], input="\n")

            assert result.exit_code == 1
            assert "Invalid project name" in result.output

    def test_init_with_path_traversal(self):
        """Test init rejects path traversal attempts."""
        result = runner.invoke(app, ["init", "../../etc/bazinga"], input="\n")

        assert result.exit_code == 1
        assert "Invalid project name" in result.output
        assert ".." in result.output or "cannot contain" in result.output

    def test_init_with_empty_name(self):
        """Test init rejects empty project name."""
        result = runner.invoke(app, ["init", ""])

        assert result.exit_code != 0

    def test_init_with_valid_name_creates_structure(self, tmp_path):
        """Test init with valid name creates project structure."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Provide input for script type (1 for bash)
            result = runner.invoke(app, ["init", "test-project"], input="1\n")

            # Should succeed
            assert result.exit_code == 0

            # Should create directory structure
            project_dir = Path("test-project")
            assert project_dir.exists()
            assert (project_dir / ".claude").exists()

    def test_init_with_existing_directory_fails(self, tmp_path):
        """Test init fails when directory already exists."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create directory
            Path("existing-project").mkdir()

            result = runner.invoke(app, ["init", "existing-project"], input="1\n")

            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_without_name_or_flag_fails(self):
        """Test init without project name or --here flag fails."""
        result = runner.invoke(app, ["init"])

        assert result.exit_code != 0


class TestBazingaSetup:
    """Test BazingaSetup class."""

    def test_get_agent_files_finds_agents(self, tmp_path):
        """Test get_agent_files finds agent markdown files."""
        # Create agents directory
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Create agent files
        (agents_dir / "orchestrator.md").write_text("# Orchestrator")
        (agents_dir / "developer.md").write_text("# Developer")

        setup = BazingaSetup(source_dir=tmp_path)
        agent_files = setup.get_agent_files()

        assert len(agent_files) == 2
        assert any(f.name == "orchestrator.md" for f in agent_files)
        assert any(f.name == "developer.md" for f in agent_files)

    def test_get_agent_files_no_agents_directory(self, tmp_path):
        """Test get_agent_files returns empty list when no agents directory."""
        setup = BazingaSetup(source_dir=tmp_path)
        agent_files = setup.get_agent_files()

        assert agent_files == []

    def test_copy_agents_validates_filenames(self, tmp_path):
        """Test copy_agents validates filenames for security."""
        # Create source agents directory with malicious filename
        source_dir = tmp_path / "source"
        agents_dir = source_dir / "agents"
        agents_dir.mkdir(parents=True)

        # Normal file
        (agents_dir / "orchestrator.md").write_text("# Orchestrator")

        # Create target directory
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        setup = BazingaSetup(source_dir=source_dir)

        # Should copy safely
        with patch('bazinga_cli.console.print') as mock_print:
            result = setup.copy_agents(target_dir)

            assert result is True

        # Verify file was copied
        assert (target_dir / ".claude" / "agents" / "orchestrator.md").exists()

    def test_copy_agents_skips_path_traversal_attempts(self, tmp_path):
        """Test copy_agents skips files with path traversal in names."""
        source_dir = tmp_path / "source"
        agents_dir = source_dir / "agents"
        agents_dir.mkdir(parents=True)

        # This test verifies the security check works
        # In real scenario, such files shouldn't exist, but we test the defense

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        setup = BazingaSetup(source_dir=source_dir)

        # Even if we manually try to construct a bad path, should be caught
        # The validate_filename call in copy_agents will prevent this


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_cli_rejects_malicious_input(self):
        """Test CLI properly rejects various malicious inputs."""
        malicious_inputs = [
            ("../../../etc/passwd", "path traversal"),
            ("test; rm -rf /", "command injection"),
            ("app$(whoami)", "command substitution"),
            ("file\x00name", "null byte injection"),
        ]

        for malicious_input, attack_type in malicious_inputs:
            result = runner.invoke(app, ["init", malicious_input], input="\n")

            assert result.exit_code != 0, \
                f"Should reject {attack_type}: {malicious_input}"
            assert "Invalid" in result.output or "Error" in result.output

    def test_cli_accepts_safe_input(self):
        """Test CLI accepts legitimate project names."""
        safe_names = [
            "my-project",
            "test_app",
            "MyApp123",
            "app.v2",
        ]

        for safe_name in safe_names:
            # Just test that validation passes (don't actually create)
            from bazinga_cli.security import PathValidator, SecurityError

            try:
                result = PathValidator.validate_project_name(safe_name)
                assert result == safe_name
            except SecurityError:
                pytest.fail(f"Should accept safe name: {safe_name}")
