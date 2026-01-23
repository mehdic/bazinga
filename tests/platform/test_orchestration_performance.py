"""
Performance comparison tests for orchestration across platforms.

Benchmarks the performance of BAZINGA orchestration on Claude Code
vs GitHub Copilot to establish baselines and identify bottlenecks.

See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

import json
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

from bazinga.platform.detection import Platform
from bazinga.platform.factory import (
    get_agent_spawner,
    get_skill_invoker,
    get_state_backend,
)
from bazinga.platform.interfaces import (
    AgentConfig,
    AgentSpawner,
    SessionData,
    SkillConfig,
    SkillInvoker,
    StateBackend,
    TaskGroupData,
)
from bazinga.platform.orchestration.adapter import OrchestrationAdapter


# ============================================================================
# Performance Data Classes
# ============================================================================


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    platform: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for reporting."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 3),
            "avg_time_ms": round(self.avg_time_ms, 3),
            "min_time_ms": round(self.min_time_ms, 3),
            "max_time_ms": round(self.max_time_ms, 3),
            "std_dev_ms": round(self.std_dev_ms, 3),
            "platform": self.platform,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ComparisonReport:
    """Comparison report between platforms."""

    claude_code_results: List[BenchmarkResult]
    copilot_results: List[BenchmarkResult]
    summary: Dict[str, Any] = field(default_factory=dict)

    def compute_summary(self) -> None:
        """Compute comparison summary."""
        self.summary = {}

        for cc_result in self.claude_code_results:
            # Find matching Copilot result
            cp_result = next(
                (r for r in self.copilot_results if r.name == cc_result.name),
                None,
            )
            if cp_result:
                diff_ms = cp_result.avg_time_ms - cc_result.avg_time_ms
                diff_pct = (
                    (diff_ms / cc_result.avg_time_ms * 100)
                    if cc_result.avg_time_ms > 0
                    else 0
                )
                self.summary[cc_result.name] = {
                    "claude_code_ms": cc_result.avg_time_ms,
                    "copilot_ms": cp_result.avg_time_ms,
                    "difference_ms": round(diff_ms, 3),
                    "difference_pct": round(diff_pct, 1),
                    "faster": "claude_code" if diff_ms > 0 else "copilot",
                }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        self.compute_summary()

        lines = [
            "# BAZINGA Platform Performance Comparison",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            "| Benchmark | Claude Code (ms) | Copilot (ms) | Diff (ms) | Diff (%) | Faster |",
            "|-----------|------------------|--------------|-----------|----------|--------|",
        ]

        for name, data in self.summary.items():
            lines.append(
                f"| {name} | {data['claude_code_ms']:.3f} | {data['copilot_ms']:.3f} | "
                f"{data['difference_ms']:+.3f} | {data['difference_pct']:+.1f}% | {data['faster']} |"
            )

        lines.extend([
            "",
            "## Detailed Results",
            "",
            "### Claude Code",
            "",
        ])

        for result in self.claude_code_results:
            lines.extend([
                f"#### {result.name}",
                f"- Iterations: {result.iterations}",
                f"- Average: {result.avg_time_ms:.3f} ms",
                f"- Min/Max: {result.min_time_ms:.3f} / {result.max_time_ms:.3f} ms",
                f"- Std Dev: {result.std_dev_ms:.3f} ms",
                "",
            ])

        lines.append("### Copilot")
        lines.append("")

        for result in self.copilot_results:
            lines.extend([
                f"#### {result.name}",
                f"- Iterations: {result.iterations}",
                f"- Average: {result.avg_time_ms:.3f} ms",
                f"- Min/Max: {result.min_time_ms:.3f} / {result.max_time_ms:.3f} ms",
                f"- Std Dev: {result.std_dev_ms:.3f} ms",
                "",
            ])

        return "\n".join(lines)


# ============================================================================
# Benchmark Utilities
# ============================================================================


def run_benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 100,
    warmup: int = 10,
    platform: str = "unknown",
) -> BenchmarkResult:
    """
    Run a benchmark and collect timing statistics.

    Args:
        name: Benchmark name
        func: Function to benchmark
        iterations: Number of iterations
        warmup: Warmup iterations (not counted)
        platform: Platform name for reporting

    Returns:
        BenchmarkResult with timing statistics
    """
    # Warmup
    for _ in range(warmup):
        func()

    # Benchmark
    times_ms: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times_ms.append(elapsed * 1000)

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=sum(times_ms),
        avg_time_ms=statistics.mean(times_ms),
        min_time_ms=min(times_ms),
        max_time_ms=max(times_ms),
        std_dev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        platform=platform,
    )


# ============================================================================
# Agent Spawner Benchmarks
# ============================================================================


class TestAgentSpawnerPerformance:
    """Benchmark tests for AgentSpawner implementations."""

    @pytest.fixture
    def claude_code_spawner(self, tmp_path: Path) -> AgentSpawner:
        """Get Claude Code spawner."""
        return get_agent_spawner(Platform.CLAUDE_CODE, tmp_path)

    @pytest.fixture
    def copilot_spawner(self, tmp_path: Path) -> AgentSpawner:
        """Get Copilot spawner."""
        return get_agent_spawner(Platform.COPILOT, tmp_path)

    def test_single_spawn_performance(
        self,
        claude_code_spawner: AgentSpawner,
        copilot_spawner: AgentSpawner,
    ):
        """Benchmark single agent spawn operation."""
        config = AgentConfig(
            agent_type="developer",
            prompt="Implement feature",
            model="sonnet",
        )

        # Claude Code
        cc_result = run_benchmark(
            name="single_spawn",
            func=lambda: claude_code_spawner.spawn_agent(config),
            iterations=100,
            platform="claude_code",
        )

        # Copilot
        cp_result = run_benchmark(
            name="single_spawn",
            func=lambda: copilot_spawner.spawn_agent(config),
            iterations=100,
            platform="copilot",
        )

        # Both should be sub-millisecond
        assert cc_result.avg_time_ms < 1.0
        assert cp_result.avg_time_ms < 1.0

        # Performance should be comparable (within 3x - allows for system variance)
        ratio = cp_result.avg_time_ms / max(cc_result.avg_time_ms, 0.001)
        assert 0.3 < ratio < 3.0, f"Performance ratio out of range: {ratio}"

    def test_parallel_spawn_performance(
        self,
        claude_code_spawner: AgentSpawner,
        copilot_spawner: AgentSpawner,
    ):
        """Benchmark parallel spawn (4 developers)."""
        configs = [
            AgentConfig(
                agent_type="developer",
                prompt=f"Task {i}",
                model="sonnet",
            )
            for i in range(4)
        ]

        # Claude Code
        cc_result = run_benchmark(
            name="parallel_spawn_4",
            func=lambda: claude_code_spawner.spawn_parallel(configs),
            iterations=50,
            platform="claude_code",
        )

        # Copilot
        cp_result = run_benchmark(
            name="parallel_spawn_4",
            func=lambda: copilot_spawner.spawn_parallel(configs),
            iterations=50,
            platform="copilot",
        )

        # Should scale roughly linearly (4x single spawn)
        assert cc_result.avg_time_ms < 5.0
        assert cp_result.avg_time_ms < 5.0

    def test_all_agent_types(
        self,
        claude_code_spawner: AgentSpawner,
        copilot_spawner: AgentSpawner,
    ):
        """Benchmark spawning each agent type."""
        agent_types = [
            "developer",
            "senior_software_engineer",
            "qa_expert",
            "tech_lead",
            "project_manager",
            "investigator",
        ]

        for agent_type in agent_types:
            config = AgentConfig(
                agent_type=agent_type,
                prompt="Test task",
                model="sonnet",
            )

            # Quick sanity check - should work for all types
            cc_result = claude_code_spawner.spawn_agent(config)
            cp_result = copilot_spawner.spawn_agent(config)

            assert cc_result.success is True
            assert cp_result.success is True


# ============================================================================
# State Backend Benchmarks
# ============================================================================


class TestStateBackendPerformance:
    """Benchmark tests for StateBackend implementations."""

    @pytest.fixture
    def memory_backend(self, tmp_path: Path) -> StateBackend:
        """Get in-memory backend for baseline."""
        return get_state_backend(
            Platform.CLAUDE_CODE, tmp_path, force_backend="memory"
        )

    @pytest.fixture
    def file_backend(self, tmp_path: Path) -> StateBackend:
        """Get file backend."""
        return get_state_backend(
            Platform.COPILOT, tmp_path, force_backend="file"
        )

    def test_session_create_performance(
        self,
        memory_backend: StateBackend,
        file_backend: StateBackend,
    ):
        """Benchmark session creation."""
        counter = [0]

        def create_session_memory():
            counter[0] += 1
            data = SessionData(
                session_id=f"bazinga_perf_test_mem_{counter[0]}",
                mode="simple",
                requirements="Test",
            )
            return memory_backend.create_session(data)

        def create_session_file():
            counter[0] += 1
            data = SessionData(
                session_id=f"bazinga_perf_test_file_{counter[0]}",
                mode="simple",
                requirements="Test",
            )
            return file_backend.create_session(data)

        # Memory backend
        mem_result = run_benchmark(
            name="session_create",
            func=create_session_memory,
            iterations=50,
            platform="memory",
        )

        # File backend
        file_result = run_benchmark(
            name="session_create",
            func=create_session_file,
            iterations=50,
            platform="file",
        )

        # Memory should be faster
        assert mem_result.avg_time_ms < file_result.avg_time_ms

        # File should still be reasonable (< 100ms)
        assert file_result.avg_time_ms < 100

    def test_task_group_operations(
        self,
        memory_backend: StateBackend,
    ):
        """Benchmark task group CRUD operations."""
        # Create a session first
        session_id = f"bazinga_perf_test_{int(time.time())}"
        memory_backend.create_session(
            SessionData(session_id=session_id, mode="parallel", requirements="Test")
        )

        counter = [0]

        def create_task_group():
            counter[0] += 1
            data = TaskGroupData(
                group_id=f"GROUP_{counter[0]}",
                session_id=session_id,
                name=f"Test Group {counter[0]}",
            )
            return memory_backend.create_task_group(data)

        result = run_benchmark(
            name="task_group_create",
            func=create_task_group,
            iterations=100,
            platform="memory",
        )

        # Should be very fast (in-memory)
        assert result.avg_time_ms < 1.0


# ============================================================================
# Full Orchestration Workflow Benchmarks
# ============================================================================


class TestOrchestrationWorkflowPerformance:
    """Benchmark complete orchestration workflows."""

    @pytest.fixture
    def claude_code_adapter(self, tmp_path: Path) -> OrchestrationAdapter:
        """Get Claude Code adapter."""
        import os
        os.environ["BAZINGA_STATE_BACKEND"] = "memory"
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )
        del os.environ["BAZINGA_STATE_BACKEND"]
        return adapter

    @pytest.fixture
    def copilot_adapter(self, tmp_path: Path) -> OrchestrationAdapter:
        """Get Copilot adapter."""
        import os
        os.environ["BAZINGA_STATE_BACKEND"] = "memory"
        adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )
        del os.environ["BAZINGA_STATE_BACKEND"]
        return adapter

    def test_simple_workflow_latency(
        self,
        claude_code_adapter: OrchestrationAdapter,
        copilot_adapter: OrchestrationAdapter,
    ):
        """
        Benchmark complete simple mode workflow latency.

        Measures orchestration overhead only (not actual agent execution).
        """
        counter = [0]

        def run_simple_workflow_cc():
            counter[0] += 1
            session_id = f"bazinga_perf_cc_{counter[0]}"
            claude_code_adapter.initialize_session(
                session_id=session_id,
                requirements="Test",
                mode="simple",
            )
            claude_code_adapter.spawn_agent("project_manager", "Plan", "opus")
            claude_code_adapter.spawn_agent("developer", "Implement", "sonnet")
            claude_code_adapter.spawn_agent("qa_expert", "Test", "sonnet")
            claude_code_adapter.spawn_agent("tech_lead", "Review", "opus")

        def run_simple_workflow_cp():
            counter[0] += 1
            session_id = f"bazinga_perf_cp_{counter[0]}"
            copilot_adapter.initialize_session(
                session_id=session_id,
                requirements="Test",
                mode="simple",
            )
            copilot_adapter.spawn_agent("project_manager", "Plan")
            copilot_adapter.spawn_agent("developer", "Implement")
            copilot_adapter.spawn_agent("qa_expert", "Test")
            copilot_adapter.spawn_agent("tech_lead", "Review")

        # Claude Code
        cc_result = run_benchmark(
            name="simple_workflow",
            func=run_simple_workflow_cc,
            iterations=20,
            warmup=5,
            platform="claude_code",
        )

        # Copilot
        cp_result = run_benchmark(
            name="simple_workflow",
            func=run_simple_workflow_cp,
            iterations=20,
            warmup=5,
            platform="copilot",
        )

        # Both should complete in < 50ms
        assert cc_result.avg_time_ms < 50
        assert cp_result.avg_time_ms < 50

    def test_parallel_workflow_latency(
        self,
        claude_code_adapter: OrchestrationAdapter,
        copilot_adapter: OrchestrationAdapter,
    ):
        """Benchmark parallel mode workflow with 4 task groups."""
        counter = [0]

        def run_parallel_workflow_cc():
            counter[0] += 1
            session_id = f"bazinga_perf_parallel_cc_{counter[0]}"
            claude_code_adapter.initialize_session(
                session_id=session_id,
                requirements="Test",
                mode="parallel",
            )
            configs = [
                {"agent_type": "developer", "prompt": f"Task {i}", "group_id": f"G{i}"}
                for i in range(4)
            ]
            claude_code_adapter.spawn_parallel(configs)

        def run_parallel_workflow_cp():
            counter[0] += 1
            session_id = f"bazinga_perf_parallel_cp_{counter[0]}"
            copilot_adapter.initialize_session(
                session_id=session_id,
                requirements="Test",
                mode="parallel",
            )
            configs = [
                {"agent_type": "developer", "prompt": f"Task {i}", "group_id": f"G{i}"}
                for i in range(4)
            ]
            copilot_adapter.spawn_parallel(configs)

        # Claude Code
        cc_result = run_benchmark(
            name="parallel_workflow_4",
            func=run_parallel_workflow_cc,
            iterations=20,
            warmup=5,
            platform="claude_code",
        )

        # Copilot
        cp_result = run_benchmark(
            name="parallel_workflow_4",
            func=run_parallel_workflow_cp,
            iterations=20,
            warmup=5,
            platform="copilot",
        )

        # Both should be reasonable
        assert cc_result.avg_time_ms < 50
        assert cp_result.avg_time_ms < 50


# ============================================================================
# Performance Report Generation
# ============================================================================


class TestPerformanceReportGeneration:
    """Test performance report generation."""

    def test_generate_comparison_report(self, tmp_path: Path):
        """Generate a comparison report."""
        import os
        os.environ["BAZINGA_STATE_BACKEND"] = "memory"

        # Claude Code adapter
        cc_adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )

        # Copilot adapter
        cp_adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )

        del os.environ["BAZINGA_STATE_BACKEND"]

        cc_results = []
        cp_results = []

        # Benchmark 1: Single spawn
        config = AgentConfig(
            agent_type="developer",
            prompt="Test",
            model="sonnet",
        )

        cc_results.append(
            run_benchmark(
                "single_spawn",
                lambda: cc_adapter.spawn_agent("developer", "Test", "sonnet"),
                iterations=50,
                platform="claude_code",
            )
        )
        cp_results.append(
            run_benchmark(
                "single_spawn",
                lambda: cp_adapter.spawn_agent("developer", "Test"),
                iterations=50,
                platform="copilot",
            )
        )

        # Benchmark 2: Parallel spawn
        configs = [
            {"agent_type": "developer", "prompt": f"Task {i}"}
            for i in range(4)
        ]

        cc_results.append(
            run_benchmark(
                "parallel_spawn_4",
                lambda: cc_adapter.spawn_parallel(configs),
                iterations=50,
                platform="claude_code",
            )
        )
        cp_results.append(
            run_benchmark(
                "parallel_spawn_4",
                lambda: cp_adapter.spawn_parallel(configs),
                iterations=50,
                platform="copilot",
            )
        )

        # Generate report
        report = ComparisonReport(
            claude_code_results=cc_results,
            copilot_results=cp_results,
        )

        markdown = report.to_markdown()

        # Verify report content
        assert "BAZINGA Platform Performance Comparison" in markdown
        assert "Claude Code" in markdown
        assert "Copilot" in markdown
        assert "single_spawn" in markdown
        assert "parallel_spawn_4" in markdown

        # Optionally save report
        report_path = tmp_path / "performance_report.md"
        report_path.write_text(markdown)
        assert report_path.exists()


# ============================================================================
# Performance Assertions (Acceptance Criteria)
# ============================================================================


class TestPerformanceAcceptanceCriteria:
    """
    Tests that verify performance meets acceptance criteria from PRD.

    From PRD Section 10: Performance Requirements
    - Single spawn overhead: <5ms
    - Parallel spawn (4 agents): <20ms
    - State operation: <50ms
    """

    def test_spawn_overhead_under_5ms(self, tmp_path: Path):
        """AC: Single spawn overhead must be < 5ms."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )

        result = run_benchmark(
            name="spawn_overhead",
            func=lambda: adapter.spawn_agent("developer", "Test", "sonnet"),
            iterations=100,
            platform="claude_code",
        )

        assert result.avg_time_ms < 5.0, (
            f"Spawn overhead {result.avg_time_ms:.2f}ms exceeds 5ms limit"
        )

    def test_parallel_spawn_under_20ms(self, tmp_path: Path):
        """AC: Parallel spawn (4 agents) must be < 20ms."""
        adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )

        configs = [
            {"agent_type": "developer", "prompt": f"Task {i}"}
            for i in range(4)
        ]

        result = run_benchmark(
            name="parallel_spawn_4",
            func=lambda: adapter.spawn_parallel(configs),
            iterations=50,
            platform="claude_code",
        )

        assert result.avg_time_ms < 20.0, (
            f"Parallel spawn {result.avg_time_ms:.2f}ms exceeds 20ms limit"
        )

    def test_copilot_parity(self, tmp_path: Path):
        """AC: Copilot performance within 2x of Claude Code."""
        cc_adapter = OrchestrationAdapter(
            platform=Platform.CLAUDE_CODE, project_root=tmp_path
        )
        cp_adapter = OrchestrationAdapter(
            platform=Platform.COPILOT, project_root=tmp_path
        )

        # Benchmark both
        cc_result = run_benchmark(
            name="spawn",
            func=lambda: cc_adapter.spawn_agent("developer", "Test", "sonnet"),
            iterations=50,
            platform="claude_code",
        )
        cp_result = run_benchmark(
            name="spawn",
            func=lambda: cp_adapter.spawn_agent("developer", "Test"),
            iterations=50,
            platform="copilot",
        )

        # Copilot should be within 2x of Claude Code
        ratio = cp_result.avg_time_ms / max(cc_result.avg_time_ms, 0.001)
        assert ratio < 2.0, (
            f"Copilot performance ratio {ratio:.2f}x exceeds 2x limit"
        )
