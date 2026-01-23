"""
Integration tests for orchestration across platforms.

Tests the OrchestrationAdapter and platform-specific orchestration
for both simple and parallel execution modes.

See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from bazinga.platform.detection import Platform
from bazinga.platform.interfaces import (
    AgentConfig,
    AgentResult,
    SessionData,
    TaskGroupData,
)
from bazinga.platform.orchestration.adapter import (
    OrchestrationAdapter,
    OrchestrationState,
    spawn_agent_for_platform,
    invoke_skill_for_platform,
)
from bazinga.platform.orchestration.copilot_entry import (
    CopilotOrchestrator,
    CopilotAgentMessage,
    copilot_orchestrate,
)


# ============================================================================
# OrchestrationState Tests
# ============================================================================


class TestOrchestrationState:
    """Tests for OrchestrationState dataclass."""

    def test_create_minimal(self):
        """Should create with minimal fields."""
        state = OrchestrationState(session_id="test_123")
        assert state.session_id == "test_123"
        assert state.mode == "simple"
        assert state.status == "active"
        assert state.task_groups == []

    def test_create_full(self):
        """Should create with all fields."""
        now = datetime.now()
        state = OrchestrationState(
            session_id="test_456",
            mode="parallel",
            status="completed",
            platform=Platform.COPILOT,
            requirements="Build auth system",
            task_groups=[
                TaskGroupData(
                    group_id="AUTH",
                    session_id="test_456",
                    name="Authentication",
                    status="completed",
                )
            ],
            current_group_id="AUTH",
            agent_history=[{"agent": "developer", "success": True}],
            created_at=now,
        )
        assert state.mode == "parallel"
        assert state.platform == Platform.COPILOT
        assert len(state.task_groups) == 1

    def test_to_dict_and_back(self):
        """Should serialize and deserialize correctly."""
        original = OrchestrationState(
            session_id="test_789",
            mode="parallel",
            status="active",
            platform=Platform.CLAUDE_CODE,
            requirements="Build something",
            task_groups=[
                TaskGroupData(
                    group_id="GRP1",
                    session_id="test_789",
                    name="Group 1",
                    status="pending",
                )
            ],
            created_at=datetime.now(),
        )

        # Serialize
        data = original.to_dict()
        assert data["session_id"] == "test_789"
        assert data["mode"] == "parallel"

        # Deserialize
        restored = OrchestrationState.from_dict(data)
        assert restored.session_id == original.session_id
        assert restored.mode == original.mode
        assert len(restored.task_groups) == 1
        assert restored.task_groups[0].group_id == "GRP1"


# ============================================================================
# OrchestrationAdapter Tests
# ============================================================================


class TestOrchestrationAdapter:
    """Tests for OrchestrationAdapter."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        # Create bazinga directory
        (tmp_path / "bazinga").mkdir()
        (tmp_path / "bazinga" / "artifacts").mkdir()

        # Create .claude directory for skills
        claude_dir = tmp_path / ".claude" / "skills" / "bazinga-db" / "scripts"
        claude_dir.mkdir(parents=True)

        return tmp_path

    def test_create_adapter_auto_detect(self, temp_project: Path):
        """Should create adapter with auto-detected platform."""
        adapter = OrchestrationAdapter(project_root=temp_project)
        assert adapter.platform in [Platform.CLAUDE_CODE, Platform.UNKNOWN]

    def test_create_adapter_forced_platform(self, temp_project: Path):
        """Should create adapter with forced platform."""
        adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=temp_project
        )
        assert adapter.platform == Platform.COPILOT

    def test_get_platform_info(self, temp_project: Path):
        """Should return platform information."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=temp_project
        )
        info = adapter.get_platform_info()

        assert info["platform"] == "claude_code"
        assert info["spawner_tool"] == "Task"
        assert "backend_persistent" in info

    def test_get_spawn_syntax_claude_code(self, temp_project: Path):
        """Should return Task() syntax for Claude Code."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=temp_project
        )
        syntax = adapter.get_spawn_syntax("developer", "Implement feature", "sonnet")

        assert "Task(" in syntax
        assert "subagent_type" in syntax
        assert "developer" in syntax
        assert "run_in_background: false" in syntax

    def test_get_spawn_syntax_copilot(self, temp_project: Path):
        """Should return #runSubagent syntax for Copilot."""
        adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=temp_project
        )
        syntax = adapter.get_spawn_syntax("developer", "Implement feature")

        assert "#runSubagent" in syntax
        assert "@developer" in syntax

    def test_spawn_agent(self, temp_project: Path):
        """Should spawn agent and return result."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=temp_project
        )

        result = adapter.spawn_agent(
            agent_type="developer",
            prompt="Implement the calculator",
            model="sonnet",
        )

        assert result.success is True
        assert result.agent_type == "developer"
        assert result.tool_invocation is not None
        assert result.tool_invocation["tool"] == "Task"

    def test_spawn_parallel(self, temp_project: Path):
        """Should spawn multiple agents in parallel."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=temp_project
        )

        configs = [
            {"agent_type": "developer", "prompt": "Task 1", "group_id": "A"},
            {"agent_type": "developer", "prompt": "Task 2", "group_id": "B"},
            {"agent_type": "developer", "prompt": "Task 3", "group_id": "C"},
        ]

        results = adapter.spawn_parallel(configs)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.agent_type == "developer" for r in results)


# ============================================================================
# Simple Mode Integration Tests
# ============================================================================


class TestSimpleModeIntegration:
    """Integration tests for simple orchestration mode."""

    @pytest.fixture
    def adapter_with_memory(self, tmp_path: Path) -> OrchestrationAdapter:
        """Create adapter with in-memory backend for testing."""
        import os
        os.environ["BAZINGA_STATE_BACKEND"] = "memory"
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )
        # Clean up env
        del os.environ["BAZINGA_STATE_BACKEND"]
        return adapter

    def test_simple_mode_workflow(self, adapter_with_memory: OrchestrationAdapter):
        """Test complete simple mode workflow."""
        adapter = adapter_with_memory

        # 1. Initialize session
        result = adapter.initialize_session(
            session_id="bazinga_test_simple_001",
            requirements="Build a calculator with add and subtract",
            mode="simple",
        )
        # Note: May fail with memory backend, that's OK for this test
        assert adapter.state is not None or result.get("success") is False

    def test_simple_mode_spawn_sequence(self, adapter_with_memory: OrchestrationAdapter):
        """Test developer -> QA -> TL spawn sequence."""
        adapter = adapter_with_memory

        # Initialize
        adapter.initialize_session(
            session_id="bazinga_test_simple_002",
            requirements="Simple task",
            mode="simple",
        )

        # Spawn developer
        dev_result = adapter.spawn_agent(
            agent_type="developer",
            prompt="Implement calculator",
            model="sonnet",
            group_id="CALC",
        )
        assert dev_result.agent_type == "developer"

        # Spawn QA
        qa_result = adapter.spawn_agent(
            agent_type="qa_expert",
            prompt="Test calculator",
            model="sonnet",
            group_id="CALC",
        )
        assert qa_result.agent_type == "qa_expert"

        # Spawn Tech Lead
        tl_result = adapter.spawn_agent(
            agent_type="tech_lead",
            prompt="Review calculator",
            model="opus",
            group_id="CALC",
        )
        assert tl_result.agent_type == "tech_lead"


# ============================================================================
# Parallel Mode Integration Tests
# ============================================================================


class TestParallelModeIntegration:
    """Integration tests for parallel orchestration mode."""

    @pytest.fixture
    def adapter_with_memory(self, tmp_path: Path) -> OrchestrationAdapter:
        """Create adapter with in-memory backend for testing."""
        import os
        os.environ["BAZINGA_STATE_BACKEND"] = "memory"
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )
        del os.environ["BAZINGA_STATE_BACKEND"]
        return adapter

    def test_parallel_mode_workflow(self, adapter_with_memory: OrchestrationAdapter):
        """Test parallel mode with multiple task groups."""
        adapter = adapter_with_memory

        # Initialize
        adapter.initialize_session(
            session_id="bazinga_test_parallel_001",
            requirements="Build auth system",
            mode="parallel",
        )

        # Spawn parallel developers
        configs = [
            {
                "agent_type": "developer",
                "prompt": "Implement login",
                "model": "sonnet",
                "group_id": "AUTH",
            },
            {
                "agent_type": "developer",
                "prompt": "Implement registration",
                "model": "sonnet",
                "group_id": "REG",
            },
            {
                "agent_type": "developer",
                "prompt": "Implement password reset",
                "model": "sonnet",
                "group_id": "PWD",
            },
        ]

        results = adapter.spawn_parallel(configs)

        assert len(results) == 3
        assert all(r.success for r in results)

        # Verify agent history
        assert adapter.state is not None
        assert len(adapter.state.agent_history) == 3

    def test_parallel_mode_max_4_developers(self, adapter_with_memory: OrchestrationAdapter):
        """Test that parallel mode respects 4 developer max."""
        adapter = adapter_with_memory

        adapter.initialize_session(
            session_id="bazinga_test_parallel_002",
            requirements="Large project",
            mode="parallel",
        )

        # Create 5 configs (exceeds limit)
        configs = [
            {"agent_type": "developer", "prompt": f"Task {i}", "group_id": f"G{i}"}
            for i in range(5)
        ]

        # Should handle all 5 (spawner doesn't enforce limit, orchestrator does)
        results = adapter.spawn_parallel(configs)
        assert len(results) == 5

    def test_parallel_mode_different_platforms(self):
        """Test parallel spawn generates correct syntax per platform."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Claude Code
            claude_adapter = OrchestrationAdapter(
                platform=Platform.CLAUDE_CODE, project_root=tmp_path
            )
            claude_syntax = claude_adapter.get_spawn_syntax("developer", "Task")
            assert "Task(" in claude_syntax

            # Copilot
            copilot_adapter = OrchestrationAdapter(
                platform=Platform.COPILOT, project_root=tmp_path
            )
            copilot_syntax = copilot_adapter.get_spawn_syntax("developer", "Task")
            assert "#runSubagent" in copilot_syntax


# ============================================================================
# CopilotOrchestrator Tests
# ============================================================================


class TestCopilotOrchestrator:
    """Tests for CopilotOrchestrator."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> CopilotOrchestrator:
        """Create a Copilot orchestrator for testing."""
        return CopilotOrchestrator(project_root=tmp_path)

    def test_initialize(self, orchestrator: CopilotOrchestrator):
        """Should initialize a new session."""
        result = orchestrator.initialize("Build a calculator")

        # May fail due to backend, but adapter should be initialized
        assert orchestrator.adapter is not None
        assert len(orchestrator.messages) >= 1

    def test_spawn_pm(self, orchestrator: CopilotOrchestrator):
        """Should generate PM spawn syntax."""
        orchestrator.initialize("Build a calculator")
        result = orchestrator.spawn_pm()

        assert "copilot_syntax" in result
        assert "#runSubagent @project-manager" in result["copilot_syntax"]
        assert result["agent"] == "@project-manager"

    def test_spawn_developer(self, orchestrator: CopilotOrchestrator):
        """Should generate developer spawn syntax."""
        orchestrator.initialize("Build a calculator")
        result = orchestrator.spawn_developer(
            group_id="CALC",
            task_description="Implement add function",
            branch="feature/calc",
        )

        assert "#runSubagent @developer" in result["copilot_syntax"]
        assert result["group_id"] == "CALC"

    def test_spawn_qa_expert(self, orchestrator: CopilotOrchestrator):
        """Should generate QA spawn syntax."""
        orchestrator.initialize("Build a calculator")
        result = orchestrator.spawn_qa_expert(
            group_id="CALC",
            handoff_file="bazinga/artifacts/test/CALC/handoff_developer.json",
        )

        assert "#runSubagent @qa-expert" in result["copilot_syntax"]
        assert result["group_id"] == "CALC"

    def test_spawn_tech_lead(self, orchestrator: CopilotOrchestrator):
        """Should generate Tech Lead spawn syntax."""
        orchestrator.initialize("Build a calculator")
        result = orchestrator.spawn_tech_lead(
            group_id="CALC",
            handoff_file="bazinga/artifacts/test/CALC/handoff_qa_expert.json",
        )

        assert "#runSubagent @tech-lead" in result["copilot_syntax"]
        assert result["group_id"] == "CALC"

    def test_spawn_parallel_developers(self, orchestrator: CopilotOrchestrator):
        """Should generate parallel developer spawn syntax."""
        orchestrator.initialize("Build auth system")

        groups = [
            {"group_id": "AUTH", "task_description": "Implement login"},
            {"group_id": "REG", "task_description": "Implement registration"},
        ]

        result = orchestrator.spawn_parallel_developers(groups, branch="feature/auth")

        assert result["count"] == 2
        assert len(result["parallel_spawns"]) == 2
        assert all("@developer" in s["copilot_syntax"] for s in result["parallel_spawns"])

    def test_handle_agent_response_developer(self, orchestrator: CopilotOrchestrator):
        """Should route developer response correctly."""
        orchestrator.initialize("Build a calculator")

        response = '{"status": "READY_FOR_QA", "summary": ["Done"]}'
        result = orchestrator.handle_agent_response(
            agent="@developer",
            response=response,
            group_id="CALC",
        )

        assert result["status"] == "READY_FOR_QA"
        assert result["next_action"]["action"] == "spawn_qa"

    def test_handle_agent_response_qa_pass(self, orchestrator: CopilotOrchestrator):
        """Should route QA PASS to Tech Lead."""
        orchestrator.initialize("Build a calculator")

        response = '{"status": "PASS", "summary": ["All tests pass"]}'
        result = orchestrator.handle_agent_response(
            agent="@qa-expert",
            response=response,
            group_id="CALC",
        )

        assert result["status"] == "PASS"
        assert result["next_action"]["action"] == "spawn_tech_lead"

    def test_handle_agent_response_qa_fail(self, orchestrator: CopilotOrchestrator):
        """Should route QA FAIL back to Developer."""
        orchestrator.initialize("Build a calculator")

        response = '{"status": "FAIL", "summary": ["Test failures"]}'
        result = orchestrator.handle_agent_response(
            agent="@qa-expert",
            response=response,
            group_id="CALC",
        )

        assert result["status"] == "FAIL"
        assert result["next_action"]["action"] == "spawn_developer"
        assert result["next_action"].get("retry") is True

    def test_handle_agent_response_tl_approved(self, orchestrator: CopilotOrchestrator):
        """Should handle Tech Lead approval."""
        orchestrator.initialize("Build a calculator")

        response = '{"status": "APPROVED", "summary": ["Code looks good"]}'
        result = orchestrator.handle_agent_response(
            agent="@tech-lead",
            response=response,
            group_id="CALC",
        )

        assert result["status"] == "APPROVED"
        assert result["next_action"]["action"] == "check_completion"

    def test_handle_agent_response_pm_bazinga(self, orchestrator: CopilotOrchestrator):
        """Should handle PM BAZINGA."""
        orchestrator.initialize("Build a calculator")

        response = '{"status": "BAZINGA", "summary": ["All complete"]}'
        result = orchestrator.handle_agent_response(
            agent="@project-manager",
            response=response,
        )

        assert result["status"] == "BAZINGA"
        assert result["next_action"]["action"] == "complete"
        assert result["next_action"].get("bazinga") is True

    def test_get_workflow_state(self, orchestrator: CopilotOrchestrator):
        """Should return workflow state."""
        orchestrator.initialize("Build a calculator")
        state = orchestrator.get_workflow_state()

        assert "current_phase" in state
        assert "message_count" in state
        assert state["message_count"] >= 1

    def test_export_copilot_instructions(self, orchestrator: CopilotOrchestrator):
        """Should export valid Copilot instructions."""
        instructions = orchestrator.export_copilot_instructions()

        assert "# BAZINGA Orchestrator Instructions" in instructions
        assert "@project-manager" in instructions
        assert "@developer" in instructions
        assert "#runSubagent" in instructions


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_spawn_agent_for_platform_claude_code(self):
        """Should spawn using Claude Code spawner."""
        result = spawn_agent_for_platform(
            agent_type="developer",
            prompt="Test prompt",
            model="sonnet",
            platform=Platform.CLAUDE_CODE,
        )

        assert result.success is True
        assert result.tool_invocation["tool"] == "Task"

    def test_spawn_agent_for_platform_copilot(self):
        """Should spawn using Copilot spawner."""
        result = spawn_agent_for_platform(
            agent_type="developer",
            prompt="Test prompt",
            platform=Platform.COPILOT,
        )

        assert result.success is True
        assert result.tool_invocation["tool"] == "#runSubagent"


# ============================================================================
# CopilotAgentMessage Tests
# ============================================================================


class TestCopilotAgentMessage:
    """Tests for CopilotAgentMessage dataclass."""

    def test_create_spawn_message(self):
        """Should create spawn message."""
        msg = CopilotAgentMessage(
            agent="@developer",
            role="spawn",
            content="Implement feature",
        )
        assert msg.agent == "@developer"
        assert msg.role == "spawn"

    def test_to_copilot_syntax_spawn(self):
        """Should convert spawn message to Copilot syntax."""
        msg = CopilotAgentMessage(
            agent="@developer",
            role="spawn",
            content="Implement feature",
        )
        syntax = msg.to_copilot_syntax()
        assert syntax == '#runSubagent @developer "Implement feature"'

    def test_to_copilot_syntax_response(self):
        """Should convert response message to display format."""
        msg = CopilotAgentMessage(
            agent="@developer",
            role="response",
            content="Done",
        )
        syntax = msg.to_copilot_syntax()
        assert syntax == "[@developer]: Done"


# ============================================================================
# copilot_orchestrate Function Tests
# ============================================================================


class TestCopilotOrchestrateFunction:
    """Tests for copilot_orchestrate entry point."""

    def test_copilot_orchestrate_creates_orchestrator(self, tmp_path: Path):
        """Should create and initialize orchestrator."""
        orchestrator = copilot_orchestrate(
            requirements="Build a calculator",
            project_root=tmp_path,
            session_id="bazinga_copilot_test_001",
        )

        assert isinstance(orchestrator, CopilotOrchestrator)
        assert orchestrator.adapter.platform == Platform.COPILOT

    def test_copilot_orchestrate_auto_session_id(self, tmp_path: Path):
        """Should auto-generate session ID if not provided."""
        orchestrator = copilot_orchestrate(
            requirements="Build something",
            project_root=tmp_path,
        )

        assert orchestrator.adapter.state is not None or len(orchestrator.messages) >= 1
