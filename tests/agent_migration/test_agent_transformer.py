"""
Tests for the agent transformer module.

Tests cover:
- FR-007: Agent File Transformer
- FR-008: Agent Inventory Migration

Run with: pytest tests/agent_migration/test_agent_transformer.py -v
"""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bazinga.scripts.agent_transformer import (
    AGENT_NAME_MAPPINGS,
    AGENT_TOOLS,
    TOOL_MAPPINGS,
    AgentFrontmatter,
    TransformResult,
    generate_copilot_frontmatter,
    get_agent_tools,
    parse_frontmatter,
    transform_agent_file,
    transform_agent_name,
    transform_all_agents,
    transform_tool_references,
    validate_transformation,
)


class TestParseYamlFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self, sample_agent_content):
        """Test parsing valid YAML frontmatter."""
        frontmatter, body = parse_frontmatter(sample_agent_content)

        assert frontmatter is not None
        assert frontmatter.name == "test_agent"
        assert frontmatter.description == "A test agent for validation"
        assert frontmatter.model == "sonnet"
        assert "# Test Agent" in body

    def test_parse_no_frontmatter(self, sample_agent_without_frontmatter):
        """Test parsing content without frontmatter."""
        frontmatter, body = parse_frontmatter(sample_agent_without_frontmatter)

        assert frontmatter is None
        assert body == sample_agent_without_frontmatter

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        frontmatter, body = parse_frontmatter("")

        assert frontmatter is None
        assert body == ""

    def test_parse_partial_frontmatter(self):
        """Test parsing incomplete frontmatter."""
        content = "---\nname: incomplete"  # Missing closing ---
        frontmatter, body = parse_frontmatter(content)

        # Should return None frontmatter as it's malformed
        assert frontmatter is None

    def test_parse_preserves_body(self, sample_agent_content):
        """Test that body content is preserved correctly."""
        _, body = parse_frontmatter(sample_agent_content)

        assert "## Your Role" in body
        assert "Task()" in body
        assert "```python" in body


class TestTransformAgentName:
    """Tests for agent name transformation."""

    def test_transform_snake_case_to_kebab(self):
        """Test snake_case to kebab-case conversion."""
        assert transform_agent_name("project_manager") == "project-manager"
        assert transform_agent_name("senior_software_engineer") == "senior-software-engineer"
        assert transform_agent_name("qa_expert") == "qa-expert"

    def test_transform_single_word(self):
        """Test single-word names remain unchanged."""
        assert transform_agent_name("orchestrator") == "orchestrator"
        assert transform_agent_name("developer") == "developer"
        assert transform_agent_name("investigator") == "investigator"

    def test_transform_unknown_name(self):
        """Test fallback for unknown agent names."""
        assert transform_agent_name("custom_agent_name") == "custom-agent-name"
        assert transform_agent_name("my_special_agent") == "my-special-agent"

    def test_all_known_agents_have_mappings(self):
        """Test that all known agents have mappings."""
        known_agents = [
            "orchestrator",
            "project_manager",
            "developer",
            "senior_software_engineer",
            "qa_expert",
            "tech_lead",
            "investigator",
            "requirements_engineer",
            "tech_stack_scout",
            "validator",
        ]
        for agent in known_agents:
            assert agent in AGENT_NAME_MAPPINGS


class TestGetAgentTools:
    """Tests for agent tools retrieval."""

    def test_get_orchestrator_tools(self):
        """Test orchestrator has required tools including #runSubagent."""
        tools = get_agent_tools("orchestrator")

        assert "read" in tools
        assert "#runSubagent" in tools
        assert "execute" in tools

    def test_get_developer_tools(self):
        """Test developer has implementation tools."""
        tools = get_agent_tools("developer")

        assert "read" in tools
        assert "edit" in tools
        assert "execute" in tools
        assert "search" in tools
        # Developer should NOT have #runSubagent
        assert "#runSubagent" not in tools

    def test_get_project_manager_tools(self):
        """Test PM has #runSubagent for spawning."""
        tools = get_agent_tools("project_manager")

        assert "#runSubagent" in tools
        assert "read" in tools

    def test_get_unknown_agent_tools(self):
        """Test unknown agent gets default tools."""
        tools = get_agent_tools("unknown_agent")

        assert len(tools) == 4
        assert "read" in tools


class TestTransformToolReferences:
    """Tests for tool reference transformation in body content."""

    def test_transform_task_tool_mention(self):
        """Test Task tool documentation is transformed."""
        body = "Use the Task tool to spawn agents."
        transformed, count = transform_tool_references(body)

        assert "#runSubagent tool" in transformed
        assert count >= 1

    def test_transform_task_function_call(self):
        """Test Task() function calls are counted."""
        body = "Use Task() to spawn. Then Task() again."
        transformed, count = transform_tool_references(body)

        assert count >= 1

    def test_preserve_code_blocks(self, sample_agent_with_tools):
        """Test code blocks are preserved but tool mentions are transformed."""
        transformed, count = transform_tool_references(sample_agent_with_tools)

        # Tool mentions should be transformed
        assert count > 0
        # But the content structure should be preserved
        assert "## Using Tools" in transformed


class TestGenerateCopilotFrontmatter:
    """Tests for Copilot frontmatter generation."""

    def test_generate_basic_frontmatter(self):
        """Test basic frontmatter generation."""
        original = AgentFrontmatter(
            name="test_agent",
            description="Test description",
            model="sonnet",
        )
        result = generate_copilot_frontmatter(original, "test_agent")

        assert "---" in result
        assert "name:" in result
        assert "description:" in result
        assert "tools:" in result
        # Model should NOT be in output
        assert "model:" not in result

    def test_generate_orchestrator_frontmatter(self):
        """Test orchestrator gets #runSubagent tool."""
        original = AgentFrontmatter(
            name="orchestrator",
            description="Orchestrator agent",
            model="sonnet",
        )
        result = generate_copilot_frontmatter(original, "orchestrator")

        assert "#runSubagent" in result

    def test_generate_without_original(self):
        """Test frontmatter generation without original."""
        result = generate_copilot_frontmatter(None, "developer")

        assert "---" in result
        assert "name:" in result
        assert "developer" in result

    def test_frontmatter_removes_model(self):
        """Test that model field is NOT included."""
        original = AgentFrontmatter(
            name="test",
            description="Test",
            model="opus",
        )
        result = generate_copilot_frontmatter(original, "test")

        # Count occurrences of 'model' - should be 0
        assert result.count("model:") == 0


class TestTransformAgentFile:
    """Tests for full agent file transformation."""

    def test_transform_creates_output_file(self, tmp_project, sample_agent_content):
        """Test that transformation creates output file."""
        source = tmp_project / "agents" / "test.md"
        source.write_text(sample_agent_content)
        target_dir = tmp_project / "agents" / "copilot"

        result = transform_agent_file(source, target_dir)

        assert result.success
        assert result.target_path.exists()
        assert result.target_path.name == "test.agent.md"

    def test_transform_preserves_body(self, tmp_project, sample_agent_content):
        """Test that body content is preserved."""
        source = tmp_project / "agents" / "test.md"
        source.write_text(sample_agent_content)
        target_dir = tmp_project / "agents" / "copilot"

        result = transform_agent_file(source, target_dir)
        output_content = result.target_path.read_text()

        # Body content should be in output
        assert "## Your Role" in output_content
        assert "Test functionality" in output_content

    def test_transform_records_warnings(self, tmp_project, sample_agent_content):
        """Test that model removal is recorded as warning."""
        source = tmp_project / "agents" / "test.md"
        source.write_text(sample_agent_content)
        target_dir = tmp_project / "agents" / "copilot"

        result = transform_agent_file(source, target_dir)

        # Should have warning about removed model
        assert any("model" in w.lower() for w in result.warnings)

    def test_transform_handles_missing_file(self, tmp_project):
        """Test handling of non-existent source file."""
        source = tmp_project / "agents" / "nonexistent.md"
        target_dir = tmp_project / "agents" / "copilot"

        result = transform_agent_file(source, target_dir)

        assert not result.success
        assert result.error is not None


class TestTransformAllAgents:
    """Tests for batch agent transformation."""

    def test_transform_all_agents_in_directory(self, agents_dir, tmp_project):
        """Test transforming all agents in a directory."""
        target_dir = tmp_project / "agents" / "copilot"

        results = transform_all_agents(agents_dir, target_dir)

        # Should have 4 agents (from fixture)
        assert len(results) == 4
        assert all(r.success for r in results)

    def test_transform_creates_target_directory(self, agents_dir, tmp_project):
        """Test that target directory is created if needed."""
        target_dir = tmp_project / "new" / "copilot"
        assert not target_dir.exists()

        results = transform_all_agents(agents_dir, target_dir)

        assert target_dir.exists()
        assert len(list(target_dir.glob("*.agent.md"))) == 4

    def test_transform_skips_speckit_files(self, agents_dir, tmp_project):
        """Test that _speckit.md files are skipped."""
        # Create a speckit file
        (agents_dir / "orchestrator_speckit.md").write_text("# Speckit")

        target_dir = tmp_project / "agents" / "copilot"
        results = transform_all_agents(agents_dir, target_dir)

        # Should NOT include speckit file
        assert not any("speckit" in r.agent_name for r in results)


class TestValidateTransformation:
    """Tests for transformation validation."""

    def test_validate_successful_transformation(self, tmp_project, sample_agent_content):
        """Test validation of successful transformation."""
        source = tmp_project / "agents" / "test.md"
        source.write_text(sample_agent_content)
        target_dir = tmp_project / "agents" / "copilot"

        result = transform_agent_file(source, target_dir)
        errors = validate_transformation(result)

        assert len(errors) == 0

    def test_validate_failed_transformation(self, tmp_project):
        """Test validation catches failed transformation."""
        result = TransformResult(
            source_path=Path("nonexistent"),
            target_path=tmp_project / "nonexistent.agent.md",
            agent_name="test",
            copilot_name="test",
            success=False,
            error="File not found",
        )

        errors = validate_transformation(result)

        assert len(errors) > 0
        assert "failed" in errors[0].lower()


class TestRealAgentTransformation:
    """Integration tests using real agent files."""

    @pytest.fixture
    def real_agents_dir(self):
        """Get the real agents directory."""
        project_root = Path(__file__).parent.parent.parent
        agents_dir = project_root / "agents"
        if not agents_dir.exists():
            pytest.skip("Real agents directory not found")
        return agents_dir

    def test_transform_real_orchestrator(self, real_agents_dir, tmp_project):
        """Test transforming the real orchestrator agent."""
        source = real_agents_dir / "orchestrator.md"
        if not source.exists():
            pytest.skip("orchestrator.md not found")

        target_dir = tmp_project / "copilot"
        result = transform_agent_file(source, target_dir)

        assert result.success
        assert result.copilot_name == "orchestrator"

        # Validate output
        content = result.target_path.read_text()
        assert "#runSubagent" in content
        # Model should be removed
        frontmatter, _ = parse_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.model is None

    def test_transform_all_real_agents(self, real_agents_dir, tmp_project):
        """Test transforming all real agents."""
        target_dir = tmp_project / "copilot"

        results = transform_all_agents(real_agents_dir, target_dir)

        # Should have multiple agents
        assert len(results) >= 9
        # All should succeed
        failures = [r for r in results if not r.success]
        assert len(failures) == 0, f"Failed: {[r.agent_name for r in failures]}"

    def test_round_trip_validation(self, real_agents_dir, tmp_project):
        """Test round-trip: transform and validate."""
        target_dir = tmp_project / "copilot"

        results = transform_all_agents(real_agents_dir, target_dir)

        for result in results:
            if result.success:
                errors = validate_transformation(result)
                assert len(errors) == 0, f"{result.agent_name}: {errors}"


class TestToolMappings:
    """Tests for tool mapping constants."""

    def test_all_claude_tools_have_mappings(self):
        """Test all expected Claude tools have mappings."""
        expected_tools = [
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Task",
            "Grep",
            "Glob",
            "Skill",
        ]
        for tool in expected_tools:
            assert tool in TOOL_MAPPINGS

    def test_copilot_tools_are_lowercase(self):
        """Test Copilot tools follow convention (lowercase or #)."""
        for copilot_tool in TOOL_MAPPINGS.values():
            assert copilot_tool.islower() or copilot_tool.startswith("#")


class TestAgentToolsConfiguration:
    """Tests for agent tools configuration."""

    def test_orchestrating_agents_have_runsubagent(self):
        """Test that orchestrating agents can spawn subagents."""
        orchestrating_agents = ["orchestrator", "project_manager"]
        for agent in orchestrating_agents:
            tools = AGENT_TOOLS.get(agent, [])
            assert "#runSubagent" in tools, f"{agent} should have #runSubagent"

    def test_implementing_agents_lack_runsubagent(self):
        """Test that implementing agents cannot spawn subagents."""
        implementing_agents = ["developer", "senior_software_engineer", "qa_expert"]
        for agent in implementing_agents:
            tools = AGENT_TOOLS.get(agent, [])
            assert "#runSubagent" not in tools, f"{agent} should NOT have #runSubagent"

    def test_all_agents_have_read(self):
        """Test all agents can read files."""
        for agent, tools in AGENT_TOOLS.items():
            assert "read" in tools, f"{agent} should have read capability"
