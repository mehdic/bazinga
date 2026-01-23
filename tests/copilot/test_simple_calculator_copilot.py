"""
Simple Calculator integration test for GitHub Copilot platform.

Validates that the BAZINGA orchestration system can run the
Simple Calculator App test case on the Copilot platform.

See:
- tests/integration/simple-calculator-spec.md (test specification)
- research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

from bazinga.platform.detection import Platform
from bazinga.platform.orchestration.adapter import OrchestrationAdapter
from bazinga.platform.orchestration.copilot_entry import (
    CopilotOrchestrator,
    copilot_orchestrate,
)


# ============================================================================
# Test Data - Simple Calculator Requirements
# ============================================================================


SIMPLE_CALCULATOR_REQUIREMENTS = """
# Simple Calculator App Specification

## Overview
Build a command-line calculator application with basic arithmetic operations.

## Requirements

### Functional Requirements
1. **Addition**: Add two numbers (integers or floats)
2. **Subtraction**: Subtract two numbers
3. **Multiplication**: Multiply two numbers
4. **Division**: Divide two numbers with zero-division handling
5. **Clear**: Reset calculator state
6. **Memory**: Store and recall previous result

### Non-Functional Requirements
1. Clean, readable code following PEP 8
2. Comprehensive unit tests (>80% coverage)
3. Error handling for invalid inputs
4. Type hints throughout

## Success Criteria
- [ ] All operations work correctly with positive/negative numbers
- [ ] Division by zero returns appropriate error
- [ ] Memory store/recall functions correctly
- [ ] Unit tests pass with >80% coverage
- [ ] Code passes lint checks
"""


# ============================================================================
# Copilot Workflow Simulation
# ============================================================================


class MockCopilotWorkflow:
    """
    Simulates a Copilot orchestration workflow for testing.

    Tracks all agent interactions and validates the workflow
    follows the expected pattern.
    """

    def __init__(self, orchestrator: CopilotOrchestrator):
        self.orchestrator = orchestrator
        self.interactions: List[Dict[str, Any]] = []
        self.agent_responses: Dict[str, str] = {}

    def simulate_pm_response(self, mode: str = "simple") -> Dict[str, Any]:
        """Simulate PM planning response."""
        response = json.dumps({
            "status": "PLANNING_COMPLETE",
            "summary": ["Planning complete", "Simple mode", "1 task group"],
            "mode": mode,
            "task_groups": [
                {
                    "group_id": "CALC",
                    "name": "Calculator Implementation",
                    "description": "Implement all calculator operations",
                    "complexity": 5,
                }
            ],
            "success_criteria": [
                "All operations work correctly",
                "Tests pass with >80% coverage",
                "Code passes lint checks",
            ],
        })

        result = self.orchestrator.handle_agent_response(
            agent="@project-manager",
            response=response,
        )

        self.interactions.append({
            "agent": "@project-manager",
            "response": response,
            "result": result,
        })

        return result

    def simulate_developer_response(
        self,
        group_id: str,
        status: str = "READY_FOR_QA",
    ) -> Dict[str, Any]:
        """Simulate developer implementation response."""
        response = json.dumps({
            "status": status,
            "summary": [
                "Implemented calculator operations",
                "Created calculator.py with Calculator class",
                "All unit tests passing (15 tests)",
            ],
            "files_created": ["calculator.py", "test_calculator.py"],
            "tests": {
                "total": 15,
                "passing": 15,
                "failing": 0,
            },
        })

        result = self.orchestrator.handle_agent_response(
            agent="@developer",
            response=response,
            group_id=group_id,
        )

        self.interactions.append({
            "agent": "@developer",
            "group_id": group_id,
            "response": response,
            "result": result,
        })

        return result

    def simulate_qa_response(
        self,
        group_id: str,
        status: str = "PASS",
    ) -> Dict[str, Any]:
        """Simulate QA testing response."""
        response = json.dumps({
            "status": status,
            "summary": [
                "All QA challenges passed",
                "Coverage: 92%",
                "No security issues found",
            ],
            "challenges_passed": [
                "Level 1: Boundary probing",
                "Level 2: Mutation analysis",
                "Level 3: Behavioral contracts",
            ],
        })

        result = self.orchestrator.handle_agent_response(
            agent="@qa-expert",
            response=response,
            group_id=group_id,
        )

        self.interactions.append({
            "agent": "@qa-expert",
            "group_id": group_id,
            "response": response,
            "result": result,
        })

        return result

    def simulate_tech_lead_response(
        self,
        group_id: str,
        status: str = "APPROVED",
    ) -> Dict[str, Any]:
        """Simulate Tech Lead review response."""
        response = json.dumps({
            "status": status,
            "summary": [
                "Code quality excellent",
                "Architecture appropriate for scale",
                "No issues found",
            ],
            "code_quality_score": 9,
        })

        result = self.orchestrator.handle_agent_response(
            agent="@tech-lead",
            response=response,
            group_id=group_id,
        )

        self.interactions.append({
            "agent": "@tech-lead",
            "group_id": group_id,
            "response": response,
            "result": result,
        })

        return result

    def simulate_pm_bazinga(self) -> Dict[str, Any]:
        """Simulate PM sending BAZINGA."""
        response = json.dumps({
            "status": "BAZINGA",
            "summary": [
                "All task groups completed successfully",
                "All success criteria met",
                "Project complete!",
            ],
        })

        result = self.orchestrator.handle_agent_response(
            agent="@project-manager",
            response=response,
        )

        self.interactions.append({
            "agent": "@project-manager",
            "response": response,
            "result": result,
        })

        return result

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of all interactions."""
        agents_involved = list(set(i["agent"] for i in self.interactions))
        return {
            "total_interactions": len(self.interactions),
            "agents_involved": agents_involved,
            "final_status": (
                self.interactions[-1]["result"]["status"]
                if self.interactions
                else "unknown"
            ),
            "workflow_complete": any(
                i["result"].get("next_action", {}).get("bazinga")
                for i in self.interactions
            ),
        }


# ============================================================================
# Test Cases
# ============================================================================


class TestSimpleCalculatorCopilotWorkflow:
    """Tests for Simple Calculator on Copilot platform."""

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        """Create temporary project directory."""
        (tmp_path / "bazinga").mkdir()
        (tmp_path / "bazinga" / "artifacts").mkdir()
        return tmp_path

    @pytest.fixture
    def orchestrator(self, project_dir: Path) -> CopilotOrchestrator:
        """Create Copilot orchestrator."""
        return copilot_orchestrate(
            requirements=SIMPLE_CALCULATOR_REQUIREMENTS,
            project_root=project_dir,
            session_id="bazinga_copilot_calc_test_001",
        )

    @pytest.fixture
    def workflow(self, orchestrator: CopilotOrchestrator) -> MockCopilotWorkflow:
        """Create mock workflow."""
        return MockCopilotWorkflow(orchestrator)

    def test_initialization(self, orchestrator: CopilotOrchestrator):
        """Test session initializes correctly on Copilot."""
        assert orchestrator.adapter.platform == Platform.COPILOT
        assert len(orchestrator.messages) >= 1
        assert orchestrator.messages[0].agent == "@orchestrator"

    def test_pm_spawn_syntax(self, orchestrator: CopilotOrchestrator):
        """Test PM spawn generates correct Copilot syntax."""
        result = orchestrator.spawn_pm()

        assert result["agent"] == "@project-manager"
        assert "#runSubagent @project-manager" in result["copilot_syntax"]
        # expected_outputs contains the data fields PM should return
        assert "mode" in result["expected_outputs"]
        assert "task_groups" in result["expected_outputs"]

    def test_complete_workflow_simple_mode(
        self,
        orchestrator: CopilotOrchestrator,
        workflow: MockCopilotWorkflow,
    ):
        """Test complete workflow in simple mode."""
        # Step 1: PM planning
        pm_result = workflow.simulate_pm_response(mode="simple")
        assert pm_result["status"] == "PLANNING_COMPLETE"
        assert pm_result["next_action"]["action"] == "spawn_developers"

        # Step 2: Developer implementation
        dev_result = workflow.simulate_developer_response(
            group_id="CALC", status="READY_FOR_QA"
        )
        assert dev_result["status"] == "READY_FOR_QA"
        assert dev_result["next_action"]["action"] == "spawn_qa"

        # Step 3: QA testing
        qa_result = workflow.simulate_qa_response(group_id="CALC", status="PASS")
        assert qa_result["status"] == "PASS"
        assert qa_result["next_action"]["action"] == "spawn_tech_lead"

        # Step 4: Tech Lead review
        tl_result = workflow.simulate_tech_lead_response(
            group_id="CALC", status="APPROVED"
        )
        assert tl_result["status"] == "APPROVED"
        assert tl_result["next_action"]["action"] == "check_completion"

        # Step 5: PM BAZINGA
        bazinga_result = workflow.simulate_pm_bazinga()
        assert bazinga_result["status"] == "BAZINGA"
        assert bazinga_result["next_action"]["action"] == "complete"
        assert bazinga_result["next_action"]["bazinga"] is True

        # Verify workflow summary
        summary = workflow.get_workflow_summary()
        assert summary["workflow_complete"] is True
        assert "@project-manager" in summary["agents_involved"]
        assert "@developer" in summary["agents_involved"]
        assert "@qa-expert" in summary["agents_involved"]
        assert "@tech-lead" in summary["agents_involved"]

    def test_developer_spawn_syntax(self, orchestrator: CopilotOrchestrator):
        """Test developer spawn generates correct syntax."""
        result = orchestrator.spawn_developer(
            group_id="CALC",
            task_description="Implement calculator operations",
            branch="feature/calculator",
            specialization="01-languages/python",
        )

        assert result["agent"] == "@developer"
        assert result["group_id"] == "CALC"
        assert "#runSubagent @developer" in result["copilot_syntax"]
        assert "CALC" in result["copilot_syntax"]

    def test_qa_spawn_syntax(self, orchestrator: CopilotOrchestrator):
        """Test QA spawn generates correct syntax."""
        result = orchestrator.spawn_qa_expert(
            group_id="CALC",
            handoff_file="bazinga/artifacts/test/CALC/handoff_developer.json",
        )

        assert result["agent"] == "@qa-expert"
        assert "#runSubagent @qa-expert" in result["copilot_syntax"]
        assert "PASS" in result["expected_status"]
        assert "FAIL" in result["expected_status"]

    def test_tech_lead_spawn_syntax(self, orchestrator: CopilotOrchestrator):
        """Test Tech Lead spawn generates correct syntax."""
        result = orchestrator.spawn_tech_lead(
            group_id="CALC",
            handoff_file="bazinga/artifacts/test/CALC/handoff_qa_expert.json",
        )

        assert result["agent"] == "@tech-lead"
        assert "#runSubagent @tech-lead" in result["copilot_syntax"]
        assert "APPROVED" in result["expected_status"]

    def test_workflow_with_qa_failure(
        self,
        orchestrator: CopilotOrchestrator,
        workflow: MockCopilotWorkflow,
    ):
        """Test workflow handles QA failure correctly."""
        # PM planning
        workflow.simulate_pm_response()

        # Developer implementation
        workflow.simulate_developer_response(group_id="CALC")

        # QA fails
        qa_result = workflow.simulate_qa_response(group_id="CALC", status="FAIL")
        assert qa_result["status"] == "FAIL"
        assert qa_result["next_action"]["action"] == "spawn_developer"
        assert qa_result["next_action"]["retry"] is True

    def test_workflow_with_tl_changes_requested(
        self,
        orchestrator: CopilotOrchestrator,
        workflow: MockCopilotWorkflow,
    ):
        """Test workflow handles Tech Lead changes requested."""
        # PM planning
        workflow.simulate_pm_response()

        # Developer implementation
        workflow.simulate_developer_response(group_id="CALC")

        # QA passes
        workflow.simulate_qa_response(group_id="CALC")

        # Tech Lead requests changes
        tl_result = workflow.simulate_tech_lead_response(
            group_id="CALC", status="CHANGES_REQUESTED"
        )
        assert tl_result["status"] == "CHANGES_REQUESTED"
        assert tl_result["next_action"]["action"] == "spawn_developer"
        assert tl_result["next_action"]["changes"] is True

    def test_message_history(
        self,
        orchestrator: CopilotOrchestrator,
        workflow: MockCopilotWorkflow,
    ):
        """Test message history is properly tracked."""
        # Run through workflow
        workflow.simulate_pm_response()
        workflow.simulate_developer_response(group_id="CALC")

        # Check messages
        messages = orchestrator.messages
        assert len(messages) >= 3  # Init + PM + Developer

        # Verify message structure
        for msg in messages:
            assert msg.agent.startswith("@")
            assert msg.role in ["spawn", "response"]
            assert msg.timestamp is not None

    def test_copilot_instructions_export(self, orchestrator: CopilotOrchestrator):
        """Test Copilot instructions can be exported."""
        instructions = orchestrator.export_copilot_instructions()

        # Verify instructions content
        assert "BAZINGA" in instructions
        assert "@project-manager" in instructions
        assert "@developer" in instructions
        assert "@qa-expert" in instructions
        assert "@tech-lead" in instructions
        assert "#runSubagent" in instructions


# ============================================================================
# Cross-Platform Comparison Tests
# ============================================================================


class TestCrossplatformComparison:
    """Compare Simple Calculator execution across platforms."""

    @pytest.fixture
    def claude_code_adapter(self, tmp_path: Path) -> OrchestrationAdapter:
        """Create Claude Code adapter."""
        return OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )

    @pytest.fixture
    def copilot_adapter(self, tmp_path: Path) -> OrchestrationAdapter:
        """Create Copilot adapter."""
        return OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )

    def test_spawn_syntax_differs(
        self,
        claude_code_adapter: OrchestrationAdapter,
        copilot_adapter: OrchestrationAdapter,
    ):
        """Test that spawn syntax differs between platforms."""
        claude_syntax = claude_code_adapter.get_spawn_syntax(
            "developer", "Implement calculator", "sonnet"
        )
        copilot_syntax = copilot_adapter.get_spawn_syntax(
            "developer", "Implement calculator"
        )

        # Claude Code uses Task()
        assert "Task(" in claude_syntax
        assert "subagent_type" in claude_syntax
        assert "run_in_background: false" in claude_syntax

        # Copilot uses #runSubagent
        assert "#runSubagent" in copilot_syntax
        assert "@developer" in copilot_syntax

    def test_agent_name_conversion(self, copilot_adapter: OrchestrationAdapter):
        """Test agent names are converted to kebab-case for Copilot."""
        # senior_software_engineer -> senior-software-engineer
        sse_syntax = copilot_adapter.get_spawn_syntax(
            "senior_software_engineer", "Fix issue"
        )
        assert "@senior-software-engineer" in sse_syntax

        # qa_expert -> qa-expert
        qa_syntax = copilot_adapter.get_spawn_syntax("qa_expert", "Test code")
        assert "@qa-expert" in qa_syntax

        # project_manager -> project-manager
        pm_syntax = copilot_adapter.get_spawn_syntax("project_manager", "Plan")
        assert "@project-manager" in pm_syntax

    def test_both_platforms_spawn_successfully(
        self,
        claude_code_adapter: OrchestrationAdapter,
        copilot_adapter: OrchestrationAdapter,
    ):
        """Test both platforms can spawn agents successfully."""
        claude_result = claude_code_adapter.spawn_agent(
            agent_type="developer",
            prompt="Implement calculator",
            model="sonnet",
        )
        copilot_result = copilot_adapter.spawn_agent(
            agent_type="developer",
            prompt="Implement calculator",
        )

        # Both should succeed
        assert claude_result.success is True
        assert copilot_result.success is True

        # Both should have tool invocations
        assert claude_result.tool_invocation is not None
        assert copilot_result.tool_invocation is not None

        # Tools should differ
        assert claude_result.tool_invocation["tool"] == "Task"
        assert copilot_result.tool_invocation["tool"] == "#runSubagent"


# ============================================================================
# Performance Baseline Tests
# ============================================================================


class TestPerformanceBaseline:
    """Establish performance baselines for Copilot orchestration."""

    def test_spawn_latency(self, tmp_path: Path):
        """Measure spawn operation latency."""
        import time

        adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )

        # Warm up
        adapter.spawn_agent("developer", "Test", "sonnet")

        # Measure
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            adapter.spawn_agent("developer", "Test", "sonnet")
        elapsed = time.perf_counter() - start

        avg_latency_ms = (elapsed / iterations) * 1000

        # Should be very fast (just object creation, no network)
        assert avg_latency_ms < 10, f"Spawn latency too high: {avg_latency_ms:.2f}ms"

    def test_parallel_spawn_latency(self, tmp_path: Path):
        """Measure parallel spawn latency."""
        import time

        adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )

        configs = [
            {"agent_type": "developer", "prompt": f"Task {i}"}
            for i in range(4)
        ]

        # Warm up
        adapter.spawn_parallel(configs)

        # Measure
        iterations = 50
        start = time.perf_counter()
        for _ in range(iterations):
            adapter.spawn_parallel(configs)
        elapsed = time.perf_counter() - start

        avg_latency_ms = (elapsed / iterations) * 1000

        # Should be fast even for parallel spawns
        assert avg_latency_ms < 20, f"Parallel spawn latency too high: {avg_latency_ms:.2f}ms"
