"""Tests for skill invoker implementations."""

import tempfile
from pathlib import Path


from bazinga.platform.interfaces import SkillConfig, SkillResult
from bazinga.platform.skill_invoker.base import BaseSkillInvoker
from bazinga.platform.skill_invoker.claude_code import ClaudeCodeInvoker
from bazinga.platform.skill_invoker.copilot import CopilotInvoker


class TestBaseSkillInvoker:
    """Tests for BaseSkillInvoker."""

    def test_list_skills_from_directory(self):
        """Should list skills from directory."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create skill directories with SKILL.md
            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()
            (skills_dir / "test-coverage").mkdir(parents=True)
            (skills_dir / "test-coverage" / "SKILL.md").touch()

            class TestInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    return SkillResult(skill_name=config.skill_name, success=True)

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = TestInvoker(project_root=tmppath)
            skills = invoker.list_skills()

            assert "lint-check" in skills
            assert "test-coverage" in skills
            assert len(skills) == 2

    def test_skill_exists(self):
        """Should check if skill exists."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()

            class TestInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    return SkillResult(skill_name=config.skill_name, success=True)

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = TestInvoker(project_root=tmppath)

            assert invoker.skill_exists("lint-check") is True
            assert invoker.skill_exists("nonexistent") is False

    def test_invoke_skill_not_found(self):
        """Should return error for non-existent skill."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".claude" / "skills").mkdir(parents=True)

            class TestInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    return SkillResult(skill_name=config.skill_name, success=True)

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = TestInvoker(project_root=tmppath)
            result = invoker.invoke_skill(SkillConfig(skill_name="nonexistent"))

            assert result.success is False
            assert "not found" in result.error

    def test_invoke_skill_success(self):
        """Should invoke skill successfully."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()

            class TestInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    return SkillResult(
                        skill_name=config.skill_name,
                        success=True,
                        output="No issues found",
                    )

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = TestInvoker(project_root=tmppath)
            result = invoker.invoke_skill(SkillConfig(skill_name="lint-check"))

            assert result.success is True
            assert result.output == "No issues found"
            assert result.elapsed_ms is not None

    def test_invoke_skill_error_handling(self):
        """Should handle errors during invocation."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "failing-skill").mkdir(parents=True)
            (skills_dir / "failing-skill" / "SKILL.md").touch()

            class FailingInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    raise RuntimeError("Skill execution failed")

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = FailingInvoker(project_root=tmppath)
            result = invoker.invoke_skill(SkillConfig(skill_name="failing-skill"))

            assert result.success is False
            assert "Skill execution failed" in result.error

    def test_skill_cache_invalidation(self):
        """Should invalidate cache when requested."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "skill-1").mkdir(parents=True)
            (skills_dir / "skill-1" / "SKILL.md").touch()

            class TestInvoker(BaseSkillInvoker):
                def _do_invoke(self, config: SkillConfig) -> SkillResult:
                    return SkillResult(skill_name=config.skill_name, success=True)

                def _get_skills_directory(self) -> Path:
                    return self._project_root / ".claude" / "skills"

            invoker = TestInvoker(project_root=tmppath)

            # Populate cache
            skills = invoker.list_skills()
            assert len(skills) == 1

            # Add new skill
            (skills_dir / "skill-2").mkdir()
            (skills_dir / "skill-2" / "SKILL.md").touch()

            # Still cached
            assert len(invoker.list_skills()) == 1

            # Invalidate cache
            invoker.invalidate_cache()
            assert len(invoker.list_skills()) == 2


class TestClaudeCodeInvoker:
    """Tests for ClaudeCodeInvoker."""

    def test_get_skills_directory(self):
        """Should return .claude/skills directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            invoker = ClaudeCodeInvoker(project_root=tmppath)

            skills_dir = invoker._get_skills_directory()
            assert skills_dir == tmppath / ".claude" / "skills"

    def test_get_invocation_syntax_without_args(self):
        """Should return correct Skill() syntax without args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = ClaudeCodeInvoker(project_root=Path(tmpdir))

            syntax = invoker.get_invocation_syntax("lint-check")
            assert syntax == 'Skill(command: "lint-check")'

    def test_get_invocation_syntax_with_args(self):
        """Should return correct Skill() syntax with args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = ClaudeCodeInvoker(project_root=Path(tmpdir))

            syntax = invoker.get_invocation_syntax("lint-check", "--verbose")
            assert syntax == 'Skill(command: "lint-check", args: "--verbose")'

    def test_invoke_skill_returns_syntax(self):
        """Should return invocation syntax in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()

            invoker = ClaudeCodeInvoker(project_root=tmppath)
            result = invoker.invoke_skill(SkillConfig(skill_name="lint-check"))

            assert result.success is True
            assert 'Skill(command: "lint-check")' in result.output

    def test_invoke_skill_with_args(self):
        """Should include args in invocation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "codebase-analysis").mkdir(parents=True)
            (skills_dir / "codebase-analysis" / "SKILL.md").touch()

            invoker = ClaudeCodeInvoker(project_root=tmppath)
            result = invoker.invoke_skill(
                SkillConfig(skill_name="codebase-analysis", args="--depth 3")
            )

            assert result.success is True
            assert "--depth 3" in result.output

    def test_get_skill_path(self):
        """Should return path to skill directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            invoker = ClaudeCodeInvoker(project_root=tmppath)

            skill_path = invoker.get_skill_path("lint-check")
            assert skill_path == tmppath / ".claude" / "skills" / "lint-check"

    def test_get_skill_md_path(self):
        """Should return path to SKILL.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            invoker = ClaudeCodeInvoker(project_root=tmppath)

            md_path = invoker.get_skill_md_path("lint-check")
            assert md_path == tmppath / ".claude" / "skills" / "lint-check" / "SKILL.md"


class TestCopilotInvoker:
    """Tests for CopilotInvoker."""

    def test_get_skills_directory_github(self):
        """Should prefer .github/skills if exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".github" / "skills").mkdir(parents=True)

            invoker = CopilotInvoker(project_root=tmppath)
            skills_dir = invoker._get_skills_directory()
            assert skills_dir == tmppath / ".github" / "skills"

    def test_get_skills_directory_fallback(self):
        """Should fallback to .claude/skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # No .github/skills
            invoker = CopilotInvoker(project_root=tmppath)
            skills_dir = invoker._get_skills_directory()
            assert skills_dir == tmppath / ".claude" / "skills"

    def test_get_invocation_syntax_without_args(self):
        """Should return correct @skill syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = CopilotInvoker(project_root=Path(tmpdir))

            syntax = invoker.get_invocation_syntax("lint-check")
            assert syntax == "Use skill @lint-check"

    def test_get_invocation_syntax_with_args(self):
        """Should include args in syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = CopilotInvoker(project_root=Path(tmpdir))

            syntax = invoker.get_invocation_syntax("lint-check", "--verbose")
            assert syntax == "Use skill @lint-check with: --verbose"

    def test_to_kebab_case(self):
        """Should convert underscores to hyphens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = CopilotInvoker(project_root=Path(tmpdir))

            assert invoker._to_kebab_case("test_coverage") == "test-coverage"
            assert invoker._to_kebab_case("codebase_analysis") == "codebase-analysis"
            assert invoker._to_kebab_case("lint-check") == "lint-check"

    def test_invoke_skill_returns_syntax(self):
        """Should return invocation syntax in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()

            invoker = CopilotInvoker(project_root=tmppath)
            result = invoker.invoke_skill(SkillConfig(skill_name="lint-check"))

            assert result.success is True
            assert "@lint-check" in result.output

    def test_get_skill_description(self):
        """Should extract description from SKILL.md frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            skill_dir = skills_dir / "lint-check"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                """---
description: "Run linting checks"
version: 1.0
---

# Lint Check Skill
"""
            )

            invoker = CopilotInvoker(project_root=tmppath)
            description = invoker.get_skill_description("lint-check")
            assert description == "Run linting checks"

    def test_get_skill_description_not_found(self):
        """Should return None for missing skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invoker = CopilotInvoker(project_root=Path(tmpdir))
            description = invoker.get_skill_description("nonexistent")
            assert description is None


class TestSkillInvokerIntegration:
    """Integration tests for skill invokers."""

    def test_both_invokers_find_same_skills(self):
        """Both invokers should find skills from .claude/skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create shared skills directory
            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "lint-check").mkdir(parents=True)
            (skills_dir / "lint-check" / "SKILL.md").touch()
            (skills_dir / "test-coverage").mkdir(parents=True)
            (skills_dir / "test-coverage" / "SKILL.md").touch()

            claude_invoker = ClaudeCodeInvoker(project_root=tmppath)
            copilot_invoker = CopilotInvoker(project_root=tmppath)

            claude_skills = set(claude_invoker.list_skills())
            copilot_skills = set(copilot_invoker.list_skills())

            assert claude_skills == copilot_skills
            assert "lint-check" in claude_skills
            assert "test-coverage" in claude_skills

    def test_both_invokers_use_different_syntax(self):
        """Invokers should use platform-specific syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_invoker = ClaudeCodeInvoker(project_root=Path(tmpdir))
            copilot_invoker = CopilotInvoker(project_root=Path(tmpdir))

            claude_syntax = claude_invoker.get_invocation_syntax("lint-check")
            copilot_syntax = copilot_invoker.get_invocation_syntax("lint-check")

            assert 'Skill(command: "lint-check")' == claude_syntax
            assert "Use skill @lint-check" == copilot_syntax

    def test_invokers_handle_skills_with_args(self):
        """Both invokers should handle args correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            skills_dir = tmppath / ".claude" / "skills"
            (skills_dir / "codebase-analysis").mkdir(parents=True)
            (skills_dir / "codebase-analysis" / "SKILL.md").touch()

            claude_invoker = ClaudeCodeInvoker(project_root=tmppath)
            copilot_invoker = CopilotInvoker(project_root=tmppath)

            config = SkillConfig(skill_name="codebase-analysis", args="--depth 3")

            claude_result = claude_invoker.invoke_skill(config)
            copilot_result = copilot_invoker.invoke_skill(config)

            assert claude_result.success is True
            assert copilot_result.success is True
            assert "--depth 3" in claude_result.output
            assert "--depth 3" in copilot_result.output
