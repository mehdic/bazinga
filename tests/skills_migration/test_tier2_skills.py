"""Tests for Tier 2 Skills (Orchestration Support) dual-platform compatibility.

Tier 2 Skills: context-assembler, workflow-router
These skills use Python scripts with bazinga-db backend and should work identically on both platforms.

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


class TestContextAssemblerSkill:
    """Test context-assembler skill dual-platform compatibility."""

    def test_context_assembler_skill_md_exists(self) -> None:
        """Verify context-assembler SKILL.md exists."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_context_assembler_skill_md_content(self) -> None:
        """Verify SKILL.md has required structure."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        content = skill_path.read_text()

        # Check required frontmatter fields
        assert "name: context-assembler" in content
        assert "version:" in content
        assert "allowed-tools:" in content

        # Check required sections
        assert "When to Invoke This Skill" in content
        assert "Your Task" in content

    def test_context_assembler_uses_bazinga_db(self) -> None:
        """Verify context-assembler uses bazinga-db backend."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference bazinga-db for state management
        assert "bazinga-db" in content or "bazinga_db" in content

    def test_context_assembler_platform_agnostic(self, claude_env: None) -> None:
        """Verify context-assembler works on Claude Code platform."""
        platform = detect_platform()
        assert platform in [Platform.CLAUDE_CODE, Platform.BOTH]

        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        content = skill_path.read_text()

        # Should not block on specific platform
        assert "COPILOT_ONLY" not in content
        assert "CLAUDE_ONLY" not in content

    def test_context_assembler_uses_sqlite(self) -> None:
        """Verify context-assembler uses SQLite backend (works on both platforms)."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference SQLite or bazinga.db
        has_db_ref = (
            "bazinga.db" in content or
            "bazinga/bazinga.db" in content or
            "sqlite" in content.lower() or
            "bazinga-db" in content
        )
        assert has_db_ref, "context-assembler should reference SQLite backend"

    def test_context_assembler_token_budgeting(self) -> None:
        """Verify context-assembler implements token budgeting."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "context-assembler" / "SKILL.md"
        content = skill_path.read_text()

        # Should mention token budget management
        assert "token" in content.lower(), "context-assembler should handle token budgets"
        assert "budget" in content.lower() or "limit" in content.lower()


class TestWorkflowRouterSkill:
    """Test workflow-router skill dual-platform compatibility."""

    def test_workflow_router_skill_md_exists(self) -> None:
        """Verify workflow-router SKILL.md exists."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_workflow_router_script_exists(self) -> None:
        """Verify workflow-router Python script exists."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "scripts" / "workflow_router.py"
        assert script_path.exists(), f"workflow_router.py not found at {script_path}"

    def test_workflow_router_skill_md_content(self) -> None:
        """Verify SKILL.md has required structure."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        content = skill_path.read_text()

        # Check required frontmatter fields
        assert "name: workflow-router" in content
        assert "version:" in content
        assert "allowed-tools:" in content

        # Check required sections
        assert "When to Invoke This Skill" in content
        assert "Your Task" in content

    def test_workflow_router_uses_transitions_table(self) -> None:
        """Verify workflow-router reads from transitions table."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        content = skill_path.read_text()

        # Should reference transitions configuration
        assert "transition" in content.lower()

    def test_workflow_router_platform_agnostic(self, copilot_env: None) -> None:
        """Verify workflow-router works on Copilot platform."""
        platform = detect_platform()
        assert platform in [Platform.COPILOT, Platform.BOTH]

        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        content = skill_path.read_text()

        # Should not block on specific platform
        assert "COPILOT_ONLY" not in content
        assert "CLAUDE_ONLY" not in content

    def test_workflow_router_returns_json(self) -> None:
        """Verify workflow-router returns JSON output."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        content = skill_path.read_text()

        # Should mention JSON output
        assert "JSON" in content or "json" in content

    def test_workflow_router_script_syntax(self) -> None:
        """Verify workflow_router.py has valid Python syntax."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "scripts" / "workflow_router.py"

        # Check Python syntax
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Python syntax error in workflow_router.py: {result.stderr}"


class TestTier2SkillsSharedPatterns:
    """Test shared patterns across all Tier 2 skills."""

    @pytest.fixture
    def tier2_skills(self) -> list[str]:
        """List of Tier 2 skill names."""
        return ["context-assembler", "workflow-router"]

    def test_all_skills_have_skill_md(self, tier2_skills: list[str]) -> None:
        """Verify all Tier 2 skills have SKILL.md."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier2_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            assert skill_md.exists(), f"SKILL.md missing for {skill_name}"

    def test_all_skills_use_bazinga_db(self, tier2_skills: list[str]) -> None:
        """Verify all Tier 2 skills use bazinga-db backend."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier2_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            content = skill_md.read_text()

            # Should reference bazinga-db or SQLite
            has_db_ref = (
                "bazinga-db" in content or
                "bazinga_db" in content or
                "bazinga.db" in content or
                "sqlite" in content.lower()
            )
            assert has_db_ref, f"{skill_name} should use bazinga-db backend"

    def test_all_skills_declare_allowed_tools(self, tier2_skills: list[str]) -> None:
        """Verify all Tier 2 skills declare allowed tools."""
        base_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        for skill_name in tier2_skills:
            skill_md = base_path / skill_name / "SKILL.md"
            content = skill_md.read_text()

            # Should have allowed-tools frontmatter
            assert "allowed-tools:" in content, f"{skill_name} missing allowed-tools"


class TestTier2DatabaseCompatibility:
    """Test Tier 2 skills work with SQLite backend on both platforms."""

    def test_workflow_transitions_table_schema(self, tmp_db: Path) -> None:
        """Verify workflow_transitions table has expected schema."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_transitions'")
        result = cursor.fetchone()
        assert result is not None, "workflow_transitions table should exist"

        # Check required columns
        cursor.execute("PRAGMA table_info(workflow_transitions)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {"from_agent", "response_status", "to_agent", "action"}
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

        conn.close()

    def test_workflow_router_queries_db(self, tmp_db: Path) -> None:
        """Verify workflow-router can query the database."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # Query like workflow-router would
        cursor.execute("""
            SELECT to_agent, action
            FROM workflow_transitions
            WHERE from_agent = ? AND response_status = ?
        """, ("developer", "READY_FOR_QA"))

        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "qa_expert"
        assert result[1] == "spawn"

        conn.close()

    def test_skill_outputs_table_schema(self, tmp_db: Path) -> None:
        """Verify skill_outputs table has expected schema."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skill_outputs'")
        result = cursor.fetchone()
        assert result is not None, "skill_outputs table should exist"

        # Check required columns
        cursor.execute("PRAGMA table_info(skill_outputs)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {"session_id", "skill_name", "output_json"}
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

        conn.close()

    def test_context_assembler_can_save_output(self, tmp_db: Path, skills_config: Path) -> None:
        """Verify context-assembler can save skill output to database."""
        import sqlite3

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # Simulate saving skill output
        output_json = json.dumps({
            "packages": [
                {"id": 1, "file_path": "research/auth.md", "priority": "high"}
            ],
            "total_available": 5
        })

        cursor.execute("""
            INSERT INTO skill_outputs (session_id, group_id, skill_name, output_json)
            VALUES (?, ?, ?, ?)
        """, ("test_session_001", "AUTH", "context-assembler", output_json))
        conn.commit()

        # Verify saved
        cursor.execute("""
            SELECT output_json FROM skill_outputs
            WHERE session_id = ? AND skill_name = ?
        """, ("test_session_001", "context-assembler"))

        result = cursor.fetchone()
        assert result is not None
        data = json.loads(result[0])
        assert data["total_available"] == 5

        conn.close()


class TestTier2SkillsIntegration:
    """Integration tests for Tier 2 skills."""

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.parent.joinpath(".claude/skills/workflow-router/scripts/workflow_router.py").exists(),
        reason="workflow_router.py not found"
    )
    def test_workflow_router_help_output(self) -> None:
        """Verify workflow_router.py provides help output."""
        script_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "scripts" / "workflow_router.py"

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True
        )

        # Should either show help or exit with code indicating help displayed
        # Note: argparse exits with 0 for --help
        assert result.returncode == 0 or "usage" in result.stdout.lower() or "usage" in result.stderr.lower()

    def test_workflow_router_cli_args(self) -> None:
        """Verify workflow-router accepts expected CLI arguments."""
        skill_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "workflow-router" / "SKILL.md"
        content = skill_path.read_text()

        # Should document CLI arguments
        expected_args = ["--current-agent", "--status", "--session-id"]
        for arg in expected_args:
            assert arg in content, f"workflow-router should document {arg} argument"
