"""
Tests for BAZINGA CLI offline mode functionality.

Tests the --offline/-O flag behavior for air-gapped environments.
"""

import os
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from bazinga_cli import (
    app,
    is_offline_mode,
    set_offline_mode,
)


runner = CliRunner()


class TestOfflineModeFlag:
    """Test offline mode flag detection and setting."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)
        # Clear environment variable
        if "BAZINGA_OFFLINE" in os.environ:
            del os.environ["BAZINGA_OFFLINE"]

    def teardown_method(self):
        """Clean up after each test."""
        set_offline_mode(False)
        if "BAZINGA_OFFLINE" in os.environ:
            del os.environ["BAZINGA_OFFLINE"]

    def test_offline_mode_default_false(self):
        """Test that offline mode is disabled by default."""
        assert is_offline_mode() is False

    def test_set_offline_mode_true(self):
        """Test setting offline mode to true."""
        set_offline_mode(True)
        assert is_offline_mode() is True

    def test_set_offline_mode_false(self):
        """Test setting offline mode back to false."""
        set_offline_mode(True)
        set_offline_mode(False)
        assert is_offline_mode() is False

    def test_offline_mode_env_var_true(self):
        """Test BAZINGA_OFFLINE=1 enables offline mode."""
        os.environ["BAZINGA_OFFLINE"] = "1"
        assert is_offline_mode() is True

    def test_offline_mode_env_var_true_string(self):
        """Test BAZINGA_OFFLINE=true enables offline mode."""
        os.environ["BAZINGA_OFFLINE"] = "true"
        assert is_offline_mode() is True

    def test_offline_mode_env_var_yes(self):
        """Test BAZINGA_OFFLINE=yes enables offline mode."""
        os.environ["BAZINGA_OFFLINE"] = "yes"
        assert is_offline_mode() is True

    def test_offline_mode_env_var_case_insensitive(self):
        """Test BAZINGA_OFFLINE is case-insensitive."""
        os.environ["BAZINGA_OFFLINE"] = "TRUE"
        assert is_offline_mode() is True

        os.environ["BAZINGA_OFFLINE"] = "Yes"
        assert is_offline_mode() is True

    def test_offline_mode_env_var_false(self):
        """Test BAZINGA_OFFLINE=0 keeps offline mode disabled."""
        os.environ["BAZINGA_OFFLINE"] = "0"
        assert is_offline_mode() is False

    def test_offline_mode_env_var_empty(self):
        """Test empty BAZINGA_OFFLINE keeps offline mode disabled."""
        os.environ["BAZINGA_OFFLINE"] = ""
        assert is_offline_mode() is False

    def test_offline_mode_flag_takes_precedence(self):
        """Test that explicit flag takes precedence over env var."""
        os.environ["BAZINGA_OFFLINE"] = "0"
        set_offline_mode(True)
        assert is_offline_mode() is True


class TestInitCommandOffline:
    """Test init command with --offline flag."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)

    def test_init_help_shows_offline_option(self):
        """Test that init command shows --offline option in help."""
        result = runner.invoke(app, ["init", "--help"])

        assert result.exit_code == 0
        assert "--offline" in result.output
        assert "-O" in result.output
        assert "offline mode" in result.output.lower()

    def test_init_offline_flag_short(self):
        """Test init with -O short flag."""
        with runner.isolated_filesystem():
            # Mock to prevent actual file operations
            with patch('bazinga_cli.BazingaSetup') as mock_setup:
                mock_instance = MagicMock()
                mock_setup.return_value = mock_instance
                mock_instance.copy_agents.return_value = True
                mock_instance.copy_scripts.return_value = True
                mock_instance.copy_commands.return_value = True
                mock_instance.copy_skills.return_value = True
                mock_instance.setup_config.return_value = True
                mock_instance.copy_templates.return_value = True
                mock_instance.copy_bazinga_configs.return_value = True
                mock_instance.copy_claude_templates.return_value = True
                mock_instance.copy_mini_dashboard.return_value = True
                mock_instance.run_init_script.return_value = True
                mock_instance.install_compact_recovery_hook.return_value = True

                result = runner.invoke(
                    app,
                    ["init", "--here", "-O", "--force"],
                    input="1\n"  # Select bash scripts
                )

                # Should show offline mode message
                assert "Offline mode" in result.output or "offline" in result.output.lower()


class TestUpdateCommandOffline:
    """Test update command with --offline flag."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)

    def test_update_help_shows_offline_option(self):
        """Test that update command shows --offline option in help."""
        result = runner.invoke(app, ["update", "--help"])

        assert result.exit_code == 0
        assert "--offline" in result.output
        assert "-O" in result.output
        assert "offline mode" in result.output.lower()


class TestDownloadPrebuiltDashboardOffline:
    """Test download_prebuilt_dashboard respects offline mode."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)

    def test_download_skipped_in_offline_mode(self, tmp_path):
        """Test that download_prebuilt_dashboard skips in offline mode."""
        from bazinga_cli import download_prebuilt_dashboard

        set_offline_mode(True)

        # Should return False immediately without making network calls
        result = download_prebuilt_dashboard(tmp_path)

        assert result is False

    @patch('urllib.request.urlopen')
    def test_download_attempts_network_when_online(self, mock_urlopen, tmp_path):
        """Test that download_prebuilt_dashboard attempts network when online."""
        from bazinga_cli import download_prebuilt_dashboard

        set_offline_mode(False)

        # Mock network response
        mock_response = MagicMock()
        mock_response.read.return_value = b'[]'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Should attempt network call
        download_prebuilt_dashboard(tmp_path)

        # Network was attempted (urlopen was called)
        assert mock_urlopen.called


class TestUpdateCLIOffline:
    """Test update_cli respects offline mode."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)

    def test_update_cli_skipped_in_offline_mode(self):
        """Test that update_cli skips in offline mode."""
        from bazinga_cli import update_cli

        set_offline_mode(True)

        # Should return False immediately without making network calls
        result = update_cli()

        assert result is False
        # In offline mode, update_cli returns False without network calls


class TestVersionDisplay:
    """Test version information includes offline mode status."""

    def test_version_command_works(self):
        """Test version command displays version."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "1.3.0" in result.output


class TestOfflineModeEdgeCases:
    """Test edge cases for offline mode."""

    def setup_method(self):
        """Reset offline mode before each test."""
        set_offline_mode(False)
        if "BAZINGA_OFFLINE" in os.environ:
            del os.environ["BAZINGA_OFFLINE"]

    def teardown_method(self):
        """Clean up after each test."""
        set_offline_mode(False)
        if "BAZINGA_OFFLINE" in os.environ:
            del os.environ["BAZINGA_OFFLINE"]

    def test_offline_mode_persists_across_calls(self):
        """Test that offline mode persists after being set."""
        set_offline_mode(True)

        # Multiple calls should return same value
        assert is_offline_mode() is True
        assert is_offline_mode() is True
        assert is_offline_mode() is True

    def test_offline_mode_env_var_invalid_values(self):
        """Test that invalid env var values are treated as false."""
        invalid_values = ["false", "no", "0", "nope", "invalid", "123"]

        for value in invalid_values:
            os.environ["BAZINGA_OFFLINE"] = value
            # Reset flag to ensure only env var is checked
            set_offline_mode(False)
            assert is_offline_mode() is False, f"Should be False for value: {value}"
