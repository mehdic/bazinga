"""Tests for platform interfaces module."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest

from bazinga.platform.interfaces import (
    AgentConfig,
    AgentResult,
    SkillConfig,
    SkillResult,
    SessionData,
    TaskGroupData,
    ReasoningData,
    AgentSpawner,
    SkillInvoker,
    StateBackend,
)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_create_minimal(self):
        """Should create with minimal required fields."""
        config = AgentConfig(
            agent_type="developer",
            prompt="Test prompt",
        )
        assert config.agent_type == "developer"
        assert config.prompt == "Test prompt"
        assert config.model is None
        assert config.run_in_background is False
        assert config.timeout_ms is None

    def test_create_full(self):
        """Should create with all fields."""
        config = AgentConfig(
            agent_type="tech_lead",
            prompt="Review code",
            model="opus",
            run_in_background=False,
            timeout_ms=300000,
        )
        assert config.agent_type == "tech_lead"
        assert config.model == "opus"
        assert config.timeout_ms == 300000

    def test_frozen(self):
        """AgentConfig should be immutable."""
        config = AgentConfig(agent_type="developer", prompt="Test")
        with pytest.raises(AttributeError):
            config.agent_type = "qa_expert"

    def test_validation_empty_agent_type(self):
        """Should reject empty agent_type."""
        with pytest.raises(ValueError, match="agent_type cannot be empty"):
            AgentConfig(agent_type="", prompt="Test")

    def test_validation_empty_prompt(self):
        """Should reject empty prompt."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            AgentConfig(agent_type="developer", prompt="")


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_create_success(self):
        """Should create successful result."""
        result = AgentResult(
            agent_type="developer",
            success=True,
            response="Implementation complete",
        )
        assert result.success is True
        assert result.response == "Implementation complete"
        assert result.error is None
        assert result.is_error is False

    def test_create_failure(self):
        """Should create failed result."""
        result = AgentResult(
            agent_type="developer",
            success=False,
            error="Task failed",
        )
        assert result.success is False
        assert result.error == "Task failed"
        assert result.is_error is True

    def test_is_error_property(self):
        """is_error should detect error conditions."""
        # Success but has error
        result = AgentResult(
            agent_type="developer",
            success=True,
            error="Warning: something odd",
        )
        assert result.is_error is True

        # Failure without error message
        result = AgentResult(
            agent_type="developer",
            success=False,
        )
        assert result.is_error is True

    def test_timing_fields(self):
        """Should track timing information."""
        result = AgentResult(
            agent_type="developer",
            success=True,
            elapsed_ms=1500.5,
        )
        assert result.elapsed_ms == 1500.5

    def test_tool_invocation_field(self):
        """Should store tool invocation details."""
        tool_call = {"tool": "Task", "params": {"prompt": "test"}}
        result = AgentResult(
            agent_type="developer",
            success=True,
            tool_invocation=tool_call,
        )
        assert result.tool_invocation == tool_call


class TestSkillConfig:
    """Tests for SkillConfig dataclass."""

    def test_create_minimal(self):
        """Should create with skill name only."""
        config = SkillConfig(skill_name="lint-check")
        assert config.skill_name == "lint-check"
        assert config.args is None
        assert config.timeout_ms is None

    def test_create_with_args(self):
        """Should create with arguments."""
        config = SkillConfig(
            skill_name="codebase-analysis",
            args="--path /src --depth 3",
            timeout_ms=60000,
        )
        assert config.args == "--path /src --depth 3"
        assert config.timeout_ms == 60000

    def test_frozen(self):
        """SkillConfig should be immutable."""
        config = SkillConfig(skill_name="lint-check")
        with pytest.raises(AttributeError):
            config.skill_name = "other"

    def test_validation_empty_skill_name(self):
        """Should reject empty skill_name."""
        with pytest.raises(ValueError, match="skill_name cannot be empty"):
            SkillConfig(skill_name="")


class TestSkillResult:
    """Tests for SkillResult dataclass."""

    def test_create_success(self):
        """Should create successful skill result."""
        result = SkillResult(
            skill_name="lint-check",
            success=True,
            output="No issues found",
        )
        assert result.success is True
        assert result.output == "No issues found"

    def test_create_failure(self):
        """Should create failed skill result."""
        result = SkillResult(
            skill_name="security-scan",
            success=False,
            error="Scan timeout",
        )
        assert result.success is False
        assert result.error == "Scan timeout"


class TestSessionData:
    """Tests for SessionData dataclass."""

    def test_create_required(self):
        """Should create with required fields."""
        session = SessionData(
            session_id="bazinga_123",
            mode="simple",
            requirements="Build feature",
        )
        assert session.session_id == "bazinga_123"
        assert session.mode == "simple"
        assert session.requirements == "Build feature"
        assert session.status == "active"
        assert session.platform == "claude_code"

    def test_create_full(self):
        """Should create with all fields."""
        now = datetime.now()
        session = SessionData(
            session_id="bazinga_456",
            mode="parallel",
            requirements="Build auth system",
            status="completed",
            platform="github_copilot",
            created_at=now,
            updated_at=now,
            metadata={"version": "1.0"},
        )
        assert session.mode == "parallel"
        assert session.requirements == "Build auth system"
        assert session.platform == "github_copilot"
        assert session.metadata == {"version": "1.0"}


class TestTaskGroupData:
    """Tests for TaskGroupData dataclass."""

    def test_create_required(self):
        """Should create with required fields."""
        group = TaskGroupData(
            group_id="AUTH",
            session_id="bazinga_123",
            name="Authentication",
        )
        assert group.group_id == "AUTH"
        assert group.session_id == "bazinga_123"
        assert group.name == "Authentication"
        assert group.status == "pending"

    def test_create_full(self):
        """Should create with all fields."""
        group = TaskGroupData(
            group_id="AUTH",
            session_id="bazinga_123",
            name="Authentication Module",
            status="in_progress",
            assigned_to="developer_1",
            specialization_path="backend/auth",
            component_path="src/auth",
            complexity=8,
            metadata={"priority": 1},
        )
        assert group.name == "Authentication Module"
        assert group.assigned_to == "developer_1"
        assert group.complexity == 8


class TestReasoningData:
    """Tests for ReasoningData dataclass."""

    def test_create_required(self):
        """Should create with required fields."""
        reasoning = ReasoningData(
            session_id="bazinga_123",
            group_id="AUTH",
            agent_type="developer",
            phase="understanding",
            content="Analyzing requirements...",
        )
        assert reasoning.phase == "understanding"
        assert reasoning.confidence == "medium"

    def test_create_full(self):
        """Should create with all fields."""
        reasoning = ReasoningData(
            session_id="bazinga_123",
            group_id="AUTH",
            agent_type="tech_lead",
            phase="completion",
            content="Code review complete",
            confidence="high",
            tokens_used=1500,
            references=["auth.py", "test_auth.py"],
        )
        assert reasoning.confidence == "high"
        assert reasoning.tokens_used == 1500
        assert len(reasoning.references) == 2


class TestAgentSpawnerABC:
    """Tests for AgentSpawner abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Should not be able to instantiate ABC directly."""
        with pytest.raises(TypeError):
            AgentSpawner()

    def test_concrete_implementation(self):
        """Should be able to implement concrete class."""

        class MockSpawner(AgentSpawner):
            def spawn_agent(self, config: AgentConfig) -> AgentResult:
                return AgentResult(
                    agent_type=config.agent_type,
                    success=True,
                )

            def spawn_parallel(
                self, configs: List[AgentConfig]
            ) -> List[AgentResult]:
                return [self.spawn_agent(c) for c in configs]

            def get_active_agents(self) -> List[str]:
                return []

            def wait_for_completion(
                self,
                agent_ids: Optional[List[str]] = None,
                timeout_ms: Optional[int] = None,
            ) -> List[AgentResult]:
                return []

        spawner = MockSpawner()
        config = AgentConfig(agent_type="developer", prompt="Test")
        result = spawner.spawn_agent(config)
        assert result.success is True

    def test_get_spawn_tool_name_default(self):
        """Default spawn tool should be Task."""

        class MockSpawner(AgentSpawner):
            def spawn_agent(self, config: AgentConfig) -> AgentResult:
                return AgentResult(agent_type=config.agent_type, success=True)

            def spawn_parallel(
                self, configs: List[AgentConfig]
            ) -> List[AgentResult]:
                return []

            def get_active_agents(self) -> List[str]:
                return []

            def wait_for_completion(
                self,
                agent_ids: Optional[List[str]] = None,
                timeout_ms: Optional[int] = None,
            ) -> List[AgentResult]:
                return []

        spawner = MockSpawner()
        assert spawner.get_spawn_tool_name() == "Task"


class TestSkillInvokerABC:
    """Tests for SkillInvoker abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Should not be able to instantiate ABC directly."""
        with pytest.raises(TypeError):
            SkillInvoker()

    def test_concrete_implementation(self):
        """Should be able to implement concrete class."""

        class MockInvoker(SkillInvoker):
            def invoke_skill(self, config: SkillConfig) -> SkillResult:
                return SkillResult(
                    skill_name=config.skill_name,
                    success=True,
                    output="{}",
                )

            def list_skills(self) -> List[str]:
                return ["lint-check", "test-coverage"]

            def skill_exists(self, skill_name: str) -> bool:
                return skill_name in ["lint-check", "test-coverage"]

        invoker = MockInvoker()
        assert "lint-check" in invoker.list_skills()
        assert invoker.skill_exists("lint-check")

    def test_get_invocation_syntax_default(self):
        """Default invocation syntax should follow Skill() pattern."""

        class MockInvoker(SkillInvoker):
            def invoke_skill(self, config: SkillConfig) -> SkillResult:
                return SkillResult(
                    skill_name=config.skill_name,
                    success=True,
                )

            def list_skills(self) -> List[str]:
                return []

            def skill_exists(self, skill_name: str) -> bool:
                return True

        invoker = MockInvoker()
        syntax = invoker.get_invocation_syntax("lint-check")
        assert syntax == 'Skill(command: "lint-check")'

        syntax_with_args = invoker.get_invocation_syntax("lint-check", "--format json")
        assert syntax_with_args == 'Skill(command: "lint-check", args: "--format json")'


class TestStateBackendABC:
    """Tests for StateBackend abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Should not be able to instantiate ABC directly."""
        with pytest.raises(TypeError):
            StateBackend()

    def test_concrete_implementation(self):
        """Should be able to implement concrete class."""

        class MockBackend(StateBackend):
            def create_session(self, data: SessionData) -> Dict[str, Any]:
                return {"success": True}

            def get_session(self, session_id: str) -> Optional[SessionData]:
                return None

            def update_session(
                self, session_id: str, updates: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {"success": True}

            def create_task_group(
                self, data: TaskGroupData
            ) -> Dict[str, Any]:
                return {"success": True}

            def get_task_groups(
                self, session_id: str
            ) -> List[TaskGroupData]:
                return []

            def update_task_group(
                self, session_id: str, group_id: str, updates: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {"success": True}

            def log_interaction(
                self,
                session_id: str,
                agent_type: str,
                content: str,
                **kwargs: Any,
            ) -> Dict[str, Any]:
                return {"success": True}

            def save_reasoning(
                self, data: ReasoningData
            ) -> Dict[str, Any]:
                return {"success": True}

            def get_reasoning(
                self,
                session_id: str,
                group_id: Optional[str] = None,
                agent_type: Optional[str] = None,
                phase: Optional[str] = None,
            ) -> List[ReasoningData]:
                return []

            def get_dashboard_snapshot(
                self, session_id: str
            ) -> Dict[str, Any]:
                return {}

        backend = MockBackend()
        assert backend.is_persistent() is True
        assert backend.supports_transactions() is True
