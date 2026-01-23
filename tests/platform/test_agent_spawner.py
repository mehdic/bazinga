"""Tests for agent spawner implementations."""

from typing import Dict


from bazinga.platform.interfaces import AgentConfig, AgentResult
from bazinga.platform.agent_spawner.base import BaseAgentSpawner
from bazinga.platform.agent_spawner.claude_code import ClaudeCodeSpawner
from bazinga.platform.agent_spawner.copilot import CopilotSpawner


class TestBaseAgentSpawner:
    """Tests for BaseAgentSpawner."""

    def test_active_agents_tracking(self):
        """Should track active agents during spawn."""

        class TestSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                # Check that agent is tracked during spawn
                assert agent_id in self.get_active_agents()
                return AgentResult(
                    agent_type=config.agent_type,
                    success=True,
                )

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {"tool": "Test"}

        spawner = TestSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        # Initially no active agents
        assert spawner.get_active_agents() == []

        # Spawn executes and cleans up
        result = spawner.spawn_agent(config)
        assert result.success is True

        # After spawn completes, agent is no longer active (synchronous model)
        assert spawner.get_active_agents() == []

    def test_generate_agent_id_format(self):
        """Generated IDs should follow agent_type_N format."""

        class TestSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                return AgentResult(agent_type=config.agent_type, success=True)

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {}

        spawner = TestSpawner()

        agent_id = spawner._generate_agent_id("developer")
        assert agent_id == "developer_1"

        agent_id2 = spawner._generate_agent_id("developer")
        assert agent_id2 == "developer_2"

        agent_id3 = spawner._generate_agent_id("qa_expert")
        assert agent_id3 == "qa_expert_3"

    def test_spawn_parallel_calls_spawn_agent(self):
        """spawn_parallel should call spawn_agent for each config."""

        class TestSpawner(BaseAgentSpawner):
            def __init__(self):
                super().__init__()
                self.spawn_count = 0

            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                self.spawn_count += 1
                return AgentResult(agent_type=config.agent_type, success=True)

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {}

        spawner = TestSpawner()
        configs = [
            AgentConfig(agent_type="developer", prompt="Task 1"),
            AgentConfig(agent_type="developer", prompt="Task 2"),
            AgentConfig(agent_type="developer", prompt="Task 3"),
        ]

        results = spawner.spawn_parallel(configs)
        assert len(results) == 3
        assert spawner.spawn_count == 3

    def test_wait_for_completion_returns_cached_results(self):
        """wait_for_completion should return cached results."""

        class TestSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                return AgentResult(agent_type=config.agent_type, success=True)

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {}

        spawner = TestSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        # Spawn to populate results
        spawner.spawn_agent(config)

        # wait_for_completion returns all results when no IDs specified
        results = spawner.wait_for_completion()
        assert len(results) == 1
        assert results[0].agent_type == "developer"

    def test_spawn_error_handling(self):
        """Should handle errors during spawn."""

        class FailingSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                raise RuntimeError("Spawn failed")

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {}

        spawner = FailingSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        result = spawner.spawn_agent(config)
        assert result.success is False
        assert "Spawn failed" in result.error

    def test_spawn_records_elapsed_time(self):
        """Should record elapsed time for spawns."""

        class TestSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                return AgentResult(agent_type=config.agent_type, success=True)

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {}

        spawner = TestSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        result = spawner.spawn_agent(config)
        assert result.elapsed_ms is not None
        assert result.elapsed_ms >= 0

    def test_spawn_includes_tool_invocation(self):
        """Should include tool invocation in result."""

        class TestSpawner(BaseAgentSpawner):
            def _do_spawn(self, config: AgentConfig, agent_id: str) -> AgentResult:
                return AgentResult(agent_type=config.agent_type, success=True)

            def _build_tool_invocation(self, config: AgentConfig) -> Dict[str, object]:
                return {"tool": "Task", "params": {"prompt": config.prompt}}

        spawner = TestSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        result = spawner.spawn_agent(config)
        assert result.tool_invocation is not None
        assert result.tool_invocation["tool"] == "Task"


class TestClaudeCodeSpawner:
    """Tests for ClaudeCodeSpawner."""

    def test_spawn_agent_builds_correct_tool_call(self):
        """Should build correct Task() tool call parameters."""
        spawner = ClaudeCodeSpawner()
        config = AgentConfig(
            agent_type="developer",
            prompt="Implement feature X",
            model="sonnet",
        )

        result = spawner.spawn_agent(config)

        # Check tool invocation structure
        assert result.tool_invocation is not None
        assert result.tool_invocation["tool"] == "Task"
        params = result.tool_invocation["params"]
        assert params["subagent_type"] == "developer"
        assert params["model"] == "sonnet"
        assert params["prompt"] == "Implement feature X"
        assert params["run_in_background"] is False  # CRITICAL requirement

    def test_spawn_agent_default_model(self):
        """Should use default model when not specified."""
        spawner = ClaudeCodeSpawner()
        config = AgentConfig(
            agent_type="developer",
            prompt="Test prompt",
        )

        result = spawner.spawn_agent(config)
        params = result.tool_invocation["params"]
        # Default model should be sonnet
        assert params["model"] == "sonnet"

    def test_background_always_false(self):
        """run_in_background must always be False."""
        spawner = ClaudeCodeSpawner()
        config = AgentConfig(
            agent_type="developer",
            prompt="Test",
            run_in_background=True,  # Even if requested via config
        )

        result = spawner.spawn_agent(config)
        params = result.tool_invocation["params"]
        # Must ALWAYS be False per BAZINGA requirements
        assert params["run_in_background"] is False

    def test_get_spawn_tool_name(self):
        """Should return Task as tool name."""
        spawner = ClaudeCodeSpawner()
        assert spawner.get_spawn_tool_name() == "Task"

    def test_get_parallel_invocation_block(self):
        """Should return list of invocations for parallel execution."""
        spawner = ClaudeCodeSpawner()
        configs = [
            AgentConfig(agent_type="developer", prompt="Task 1"),
            AgentConfig(agent_type="qa_expert", prompt="Task 2"),
        ]

        invocations = spawner.get_parallel_invocation_block(configs)
        assert len(invocations) == 2
        assert invocations[0]["params"]["subagent_type"] == "developer"
        assert invocations[1]["params"]["subagent_type"] == "qa_expert"

    def test_spawn_returns_success(self):
        """spawn_agent should return successful result."""
        spawner = ClaudeCodeSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")

        result = spawner.spawn_agent(config)
        assert result.success is True
        assert result.agent_type == "developer"


class TestCopilotSpawner:
    """Tests for CopilotSpawner."""

    def test_spawn_agent_builds_correct_tool_call(self):
        """Should build correct #runSubagent tool call."""
        spawner = CopilotSpawner()
        config = AgentConfig(
            agent_type="developer",
            prompt="Implement feature X",
        )

        result = spawner.spawn_agent(config)

        assert result.tool_invocation is not None
        assert result.tool_invocation["tool"] == "#runSubagent"
        params = result.tool_invocation["params"]
        assert params["agent"] == "@developer"
        assert params["prompt"] == "Implement feature X"

    def test_agent_name_conversion(self):
        """Should convert snake_case to kebab-case for Copilot."""
        spawner = CopilotSpawner()

        assert spawner._to_kebab_case("senior_software_engineer") == "senior-software-engineer"
        assert spawner._to_kebab_case("tech_lead") == "tech-lead"
        assert spawner._to_kebab_case("developer") == "developer"
        assert spawner._to_kebab_case("qa_expert") == "qa-expert"
        assert spawner._to_kebab_case("project_manager") == "project-manager"

    def test_no_model_in_params(self):
        """Copilot spawner should not include model (Copilot limitation)."""
        spawner = CopilotSpawner()
        config = AgentConfig(
            agent_type="developer",
            prompt="Test",
            model="opus",  # Even if specified
        )

        result = spawner.spawn_agent(config)
        params = result.tool_invocation["params"]
        # Copilot doesn't support model selection
        assert "model" not in params

    def test_agent_uses_at_prefix(self):
        """Should prefix agent name with @."""
        spawner = CopilotSpawner()
        config = AgentConfig(agent_type="tech_lead", prompt="Review")

        result = spawner.spawn_agent(config)
        params = result.tool_invocation["params"]
        assert params["agent"] == "@tech-lead"

    def test_get_spawn_tool_name(self):
        """Should return #runSubagent as tool name."""
        spawner = CopilotSpawner()
        assert spawner.get_spawn_tool_name() == "#runSubagent"

    def test_get_parallel_invocation_block(self):
        """Should return list of invocations for parallel execution."""
        spawner = CopilotSpawner()
        configs = [
            AgentConfig(agent_type="developer", prompt="Task 1"),
            AgentConfig(agent_type="qa_expert", prompt="Task 2"),
        ]

        invocations = spawner.get_parallel_invocation_block(configs)
        assert len(invocations) == 2
        assert invocations[0]["params"]["agent"] == "@developer"
        assert invocations[1]["params"]["agent"] == "@qa-expert"

    def test_get_inline_invocation_syntax(self):
        """Should return inline #runSubagent syntax."""
        spawner = CopilotSpawner()
        config = AgentConfig(agent_type="tech_lead", prompt="Review the code")

        syntax = spawner.get_inline_invocation_syntax(config)
        assert syntax == '#runSubagent @tech-lead "Review the code"'

    def test_spawn_parallel(self):
        """Should spawn multiple agents."""
        spawner = CopilotSpawner()
        configs = [
            AgentConfig(agent_type="developer", prompt="Task 1"),
            AgentConfig(agent_type="developer", prompt="Task 2"),
        ]

        results = spawner.spawn_parallel(configs)
        assert len(results) == 2
        assert all(r.agent_type == "developer" for r in results)


class TestAgentSpawnerIntegration:
    """Integration tests for agent spawners."""

    def test_both_spawners_produce_consistent_results(self):
        """Both spawners should produce similar result structure."""
        claude_spawner = ClaudeCodeSpawner()
        copilot_spawner = CopilotSpawner()

        config = AgentConfig(
            agent_type="developer",
            prompt="Test task",
        )

        claude_result = claude_spawner.spawn_agent(config)
        copilot_result = copilot_spawner.spawn_agent(config)

        # Both should succeed
        assert claude_result.success is True
        assert copilot_result.success is True

        # Both have same agent_type
        assert claude_result.agent_type == config.agent_type
        assert copilot_result.agent_type == config.agent_type

        # Both have tool_invocation
        assert claude_result.tool_invocation is not None
        assert copilot_result.tool_invocation is not None

    def test_spawners_use_different_tools(self):
        """Spawners should use platform-specific tools."""
        claude_spawner = ClaudeCodeSpawner()
        copilot_spawner = CopilotSpawner()

        config = AgentConfig(agent_type="developer", prompt="Test")

        claude_result = claude_spawner.spawn_agent(config)
        copilot_result = copilot_spawner.spawn_agent(config)

        assert claude_result.tool_invocation["tool"] == "Task"
        assert copilot_result.tool_invocation["tool"] == "#runSubagent"

    def test_spawner_handles_all_agent_types(self):
        """Both spawners should handle all agent types."""
        agent_types = [
            "developer",
            "senior_software_engineer",
            "qa_expert",
            "tech_lead",
            "project_manager",
            "investigator",
        ]

        for SpawnerClass in [ClaudeCodeSpawner, CopilotSpawner]:
            spawner = SpawnerClass()
            for agent_type in agent_types:
                config = AgentConfig(agent_type=agent_type, prompt="Test")
                result = spawner.spawn_agent(config)
                assert result.success is True
                assert result.agent_type == agent_type
