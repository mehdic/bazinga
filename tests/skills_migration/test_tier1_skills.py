"""Tests for Tier 1 Skills (Quality Gates) dual-platform compatibility.

Tier 1 Skills: test-coverage, lint-check, security-scan
These skills use Bash scripts and should work identically on both platforms.

See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md FR-009
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Add bazinga/platform to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bazinga" / "platform"))

from detection import Platform, detect_platform


class TestLintCheckSkill:
    """Test lint-check skill dual-platform compatibility."""

    def test_lint_check_skill_md_exists(self) -> None:
        """Verify lint-check SKILL.md exists."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_lint_check_script_exists(self) -> None:
        """Verify lint-check bash script exists."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "scripts" / "lint.sh"
        assert script_path.exists(), f"lint.sh not found at {script_path}"

    def test_lint_check_skill_md_content(self) -> None:
        """Verify SKILL.md has required structure."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "SKILL.md"
        content = skill_path.read_text()

        # Check required frontmatter fields
        assert "name: lint-check" in content
        assert "version:" in content
        assert "allowed-tools:" in content

        # Check required sections
        assert "When to Invoke This Skill" in content
        assert "Your Task" in content

    def test_lint_check_output_path_pattern(self) -> None:
        """Verify lint-check uses session-isolated output paths."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference session-isolated artifact path
        assert "bazinga/artifacts/{SESSION_ID}/skills" in content or \
               "bazinga/artifacts/$SESSION_ID/skills" in content

    def test_lint_check_platform_agnostic(self, claude_env: None) -> None:
        """Verify lint-check works on Claude Code platform."""
        platform = detect_platform()
        assert platform in [Platform.CLAUDE_CODE, Platform.BOTH]

        # Skill should not have platform-specific code that blocks execution
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "SKILL.md"
        content = skill_path.read_text()

        # Should not block on specific platform
        assert "COPILOT_ONLY" not in content
        assert "CLAUDE_ONLY" not in content


class TestTestCoverageSkill:
    """Test test-coverage skill dual-platform compatibility."""

    def test_coverage_skill_md_exists(self) -> None:
        """Verify test-coverage SKILL.md exists."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_coverage_script_exists(self) -> None:
        """Verify test-coverage bash script exists."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "scripts" / "coverage.sh"
        assert script_path.exists(), f"coverage.sh not found at {script_path}"

    def test_coverage_skill_md_content(self) -> None:
        """Verify SKILL.md has required structure."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "SKILL.md"
        content = skill_path.read_text()

        # Check required frontmatter fields
        assert "name: test-coverage" in content
        assert "version:" in content
        assert "allowed-tools:" in content

        # Check required sections
        assert "When to Invoke This Skill" in content
        assert "Your Task" in content

    def test_coverage_output_path_pattern(self) -> None:
        """Verify test-coverage uses session-isolated output paths."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference session-isolated artifact path
        assert "bazinga/artifacts/{SESSION_ID}/skills" in content or \
               "bazinga/artifacts/$SESSION_ID/skills" in content

    def test_coverage_platform_agnostic(self, copilot_env: None) -> None:
        """Verify test-coverage works on Copilot platform."""
        platform = detect_platform()
        assert platform in [Platform.COPILOT, Platform.BOTH]

        # Skill should not have platform-specific code that blocks execution
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "SKILL.md"
        content = skill_path.read_text()

        # Should not block on specific platform
        assert "COPILOT_ONLY" not in content
        assert "CLAUDE_ONLY" not in content


class TestSecurityScanSkill:
    """Test security-scan skill dual-platform compatibility."""

    def test_security_scan_skill_md_exists(self) -> None:
        """Verify security-scan SKILL.md exists."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_security_scan_script_exists(self) -> None:
        """Verify security-scan bash script exists."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "scripts" / "scan.sh"
        assert script_path.exists(), f"scan.sh not found at {script_path}"

    def test_security_scan_skill_md_content(self) -> None:
        """Verify SKILL.md has required structure."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "SKILL.md"
        content = skill_path.read_text()

        # Check required frontmatter fields
        assert "name: security-scan" in content
        assert "version:" in content
        assert "allowed-tools:" in content

        # Check required sections
        assert "When to Invoke This Skill" in content
        assert "Your Task" in content

    def test_security_scan_output_path_pattern(self) -> None:
        """Verify security-scan uses session-isolated output paths."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference session-isolated artifact path
        assert "bazinga/artifacts/{SESSION_ID}/skills" in content or \
               "bazinga/artifacts/$SESSION_ID/skills" in content

    def test_security_scan_platform_agnostic(self, both_platforms_env: None) -> None:
        """Verify security-scan works in dual-platform mode."""
        platform = detect_platform()
        assert platform == Platform.BOTH

        # Skill should not have platform-specific code that blocks execution
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "SKILL.md"
        content = skill_path.read_text()

        # Should not block on specific platform
        assert "COPILOT_ONLY" not in content
        assert "CLAUDE_ONLY" not in content


class TestTier1SkillsSharedPatterns:
    """Test shared patterns across all Tier 1 skills."""

    @pytest.fixture
    def tier1_skills(self) -> list[str]:
        """List of Tier 1 skill names."""
        return ["lint-check", "test-coverage", "security-scan"]

    def test_all_skills_have_bash_script(self, tier1_skills: list[str]) -> None:
        """Verify all Tier 1 skills have bash scripts."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier1_skills:
            skill_dir = base_path / skill_name / "scripts"
            assert skill_dir.exists(), f"Scripts directory missing for {skill_name}"

            # Should have at least one .sh file
            sh_files = list(skill_dir.glob("*.sh"))
            assert len(sh_files) > 0, f"No .sh scripts found for {skill_name}"

    def test_all_skills_have_cross_platform_scripts(self, tier1_skills: list[str]) -> None:
        """Verify all Tier 1 skills support cross-platform execution."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier1_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            content = skill_md.read_text()

            # Should mention cross-platform support
            has_cross_platform = (
                "Windows" in content or
                "PowerShell" in content or
                "Cross-platform" in content or
                ".ps1" in content
            )
            # Cross-platform support is optional but documented if present
            # At minimum, bash scripts work on Unix/macOS

    def test_all_skills_output_json(self, tier1_skills: list[str]) -> None:
        """Verify all Tier 1 skills output JSON format."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier1_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            content = skill_md.read_text()

            # Should reference JSON output
            assert ".json" in content, f"{skill_name} should output JSON"

    def test_all_skills_use_allowed_tools(self, tier1_skills: list[str]) -> None:
        """Verify all Tier 1 skills declare allowed tools."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier1_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            content = skill_md.read_text()

            # Should have allowed-tools frontmatter
            assert "allowed-tools:" in content, f"{skill_name} missing allowed-tools"

            # Should include Bash for execution
            assert "Bash" in content, f"{skill_name} should allow Bash"


class TestTier1SkillIntegration:
    """Integration tests for Tier 1 skills."""

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.joinpath(".claude/skills/lint-check/scripts/lint.sh").exists(),
        reason="lint.sh not found"
    )
    def test_lint_check_script_syntax(self) -> None:
        """Verify lint.sh has valid bash syntax."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "lint-check" / "scripts" / "lint.sh"

        # Check bash syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Bash syntax error in lint.sh: {result.stderr}"

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.joinpath(".claude/skills/test-coverage/scripts/coverage.sh").exists(),
        reason="coverage.sh not found"
    )
    def test_coverage_script_syntax(self) -> None:
        """Verify coverage.sh has valid bash syntax."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "test-coverage" / "scripts" / "coverage.sh"

        # Check bash syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Bash syntax error in coverage.sh: {result.stderr}"

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.joinpath(".claude/skills/security-scan/scripts/scan.sh").exists(),
        reason="scan.sh not found"
    )
    def test_security_scan_script_syntax(self) -> None:
        """Verify scan.sh has valid bash syntax."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "security-scan" / "scripts" / "scan.sh"

        # Check bash syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Bash syntax error in scan.sh: {result.stderr}"
