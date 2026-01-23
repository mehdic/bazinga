"""
Copilot-compatible orchestration entry point.

Provides the main entry point for running BAZINGA orchestration
on GitHub Copilot platform. Adapts the Claude Code orchestrator
concepts for Copilot's tool and agent syntax.

See: research/copilot-migration/PRD-BAZINGA-DUAL-PLATFORM-MIGRATION.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bazinga.platform.detection import Platform
from bazinga.platform.orchestration.adapter import (
    OrchestrationAdapter,
    OrchestrationState,
)
from bazinga.platform.interfaces import AgentResult, TaskGroupData


@dataclass
class CopilotAgentMessage:
    """
    A message to/from a Copilot agent.

    Used to track agent communication in the Copilot format.
    """

    agent: str  # @developer, @qa-expert, etc.
    role: str  # "spawn" or "response"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_copilot_syntax(self) -> str:
        """Convert to Copilot #runSubagent syntax."""
        if self.role == "spawn":
            return f'#runSubagent {self.agent} "{self.content}"'
        return f"[{self.agent}]: {self.content}"


class CopilotOrchestrator:
    """
    Orchestrator implementation for GitHub Copilot.

    Provides the same orchestration capabilities as the Claude Code
    orchestrator but uses Copilot-compatible syntax and tools.

    Key differences from Claude Code:
    - Uses #runSubagent instead of Task()
    - Uses @agent-name instead of snake_case agent types
    - State persistence may use file backend instead of SQLite
    - Skill invocation uses filesystem loading

    Usage:
        orchestrator = CopilotOrchestrator()
        orchestrator.initialize("Build a calculator app")
        orchestrator.run()  # Drives the orchestration loop
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        force_backend: Optional[str] = None,
    ) -> None:
        """
        Initialize the Copilot orchestrator.

        Args:
            project_root: Project root directory. Defaults to cwd.
            force_backend: Force specific state backend (sqlite, file, memory).
        """
        self._project_root = project_root or Path.cwd()
        self._adapter = OrchestrationAdapter(
            platform=Platform.COPILOT,
            project_root=self._project_root,
        )

        # Message history for Copilot conversation tracking
        self._messages: List[CopilotAgentMessage] = []

        # Current workflow state
        self._current_phase: str = "init"
        self._pm_state: Dict[str, Any] = {}

    @property
    def adapter(self) -> OrchestrationAdapter:
        """Get the underlying adapter."""
        return self._adapter

    @property
    def state(self) -> Optional[OrchestrationState]:
        """Get current orchestration state."""
        return self._adapter.state

    @property
    def messages(self) -> List[CopilotAgentMessage]:
        """Get message history."""
        return self._messages

    # =========================================================================
    # Initialization
    # =========================================================================

    def initialize(
        self,
        requirements: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a new orchestration session.

        Args:
            requirements: User requirements text
            session_id: Optional session ID. Auto-generated if not provided.

        Returns:
            Dict with initialization result
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = f"bazinga_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Add message before attempting initialization (so tests see it even if backend fails)
        self._add_message(
            agent="@orchestrator",
            role="spawn",
            content=f"Initializing session: {session_id}",
        )

        # Initialize session
        result = self._adapter.initialize_session(
            session_id=session_id,
            requirements=requirements,
            mode="simple",  # PM will determine actual mode
        )

        if result.get("success"):
            self._current_phase = "pm_planning"
            self._add_message(
                agent="@orchestrator",
                role="spawn",
                content=f"Session initialized successfully: {session_id}",
            )
        else:
            self._add_message(
                agent="@orchestrator",
                role="spawn",
                content=f"Session initialization failed: {result.get('error', 'Unknown error')}",
            )

        return result

    def resume(self, session_id: str) -> Dict[str, Any]:
        """
        Resume an existing session.

        Args:
            session_id: Session ID to resume

        Returns:
            Dict with resume result
        """
        result = self._adapter.resume_session(session_id)

        if result.get("success"):
            self._current_phase = "resumed"
            self._add_message(
                agent="@orchestrator",
                role="spawn",
                content=f"Session resumed: {session_id}",
            )

        return result

    # =========================================================================
    # Agent Spawning (Copilot Syntax)
    # =========================================================================

    def spawn_pm(self, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Spawn the Project Manager agent.

        Returns the Copilot syntax for spawning PM and placeholder result.
        The actual response would come from Copilot's subagent execution.

        Args:
            context: Optional additional context for PM

        Returns:
            Dict with spawn syntax and expected behavior
        """
        prompt = self._build_pm_prompt(context)

        self._add_message(
            agent="@project-manager",
            role="spawn",
            content=prompt[:100] + "...",
        )

        return {
            "copilot_syntax": f'#runSubagent @project-manager "{prompt}"',
            "agent": "@project-manager",
            "expected_outputs": ["mode", "task_groups", "success_criteria"],
            "next_phase": "pm_response",
        }

    def spawn_developer(
        self,
        group_id: str,
        task_description: str,
        branch: str,
        specialization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Spawn a Developer agent for a task group.

        Args:
            group_id: Task group ID
            task_description: What to implement
            branch: Git branch to work on
            specialization: Optional technology specialization

        Returns:
            Dict with spawn syntax and expected behavior
        """
        prompt = self._build_developer_prompt(
            group_id, task_description, branch, specialization
        )

        self._add_message(
            agent="@developer",
            role="spawn",
            content=f"Group {group_id}: {task_description[:50]}...",
            metadata={"group_id": group_id},
        )

        return {
            "copilot_syntax": f'#runSubagent @developer "{prompt}"',
            "agent": "@developer",
            "group_id": group_id,
            "expected_status": ["READY_FOR_QA", "READY_FOR_REVIEW", "BLOCKED"],
            "next_phase": "developer_response",
        }

    def spawn_qa_expert(
        self,
        group_id: str,
        handoff_file: str,
    ) -> Dict[str, Any]:
        """
        Spawn QA Expert to test implementation.

        Args:
            group_id: Task group ID
            handoff_file: Path to developer's handoff file

        Returns:
            Dict with spawn syntax and expected behavior
        """
        prompt = self._build_qa_prompt(group_id, handoff_file)

        self._add_message(
            agent="@qa-expert",
            role="spawn",
            content=f"Testing group {group_id}",
            metadata={"group_id": group_id},
        )

        return {
            "copilot_syntax": f'#runSubagent @qa-expert "{prompt}"',
            "agent": "@qa-expert",
            "group_id": group_id,
            "expected_status": ["PASS", "FAIL", "FAIL_ESCALATE"],
            "next_phase": "qa_response",
        }

    def spawn_tech_lead(
        self,
        group_id: str,
        handoff_file: str,
    ) -> Dict[str, Any]:
        """
        Spawn Tech Lead for code review.

        Args:
            group_id: Task group ID
            handoff_file: Path to prior agent's handoff file

        Returns:
            Dict with spawn syntax and expected behavior
        """
        prompt = self._build_tech_lead_prompt(group_id, handoff_file)

        self._add_message(
            agent="@tech-lead",
            role="spawn",
            content=f"Reviewing group {group_id}",
            metadata={"group_id": group_id},
        )

        return {
            "copilot_syntax": f'#runSubagent @tech-lead "{prompt}"',
            "agent": "@tech-lead",
            "group_id": group_id,
            "expected_status": ["APPROVED", "CHANGES_REQUESTED"],
            "next_phase": "tech_lead_response",
        }

    def spawn_parallel_developers(
        self,
        groups: List[Dict[str, Any]],
        branch: str,
    ) -> Dict[str, Any]:
        """
        Spawn multiple developers in parallel (Copilot style).

        Note: Copilot may handle parallel spawns differently than Claude Code.
        This generates the syntax for all spawns.

        Args:
            groups: List of dicts with group_id, task_description, specialization
            branch: Git branch

        Returns:
            Dict with parallel spawn syntax
        """
        spawns = []
        for group in groups:
            prompt = self._build_developer_prompt(
                group["group_id"],
                group["task_description"],
                branch,
                group.get("specialization"),
            )
            spawns.append({
                "agent": "@developer",
                "group_id": group["group_id"],
                "copilot_syntax": f'#runSubagent @developer "{prompt}"',
            })

            self._add_message(
                agent="@developer",
                role="spawn",
                content=f"Group {group['group_id']}: {group['task_description'][:50]}...",
                metadata={"group_id": group["group_id"], "parallel": True},
            )

        return {
            "parallel_spawns": spawns,
            "count": len(spawns),
            "note": "Execute all #runSubagent calls in same turn for parallel execution",
        }

    # =========================================================================
    # Response Handling
    # =========================================================================

    def handle_agent_response(
        self,
        agent: str,
        response: str,
        group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a response from a spawned agent.

        Parses the response to determine next action in workflow.

        Args:
            agent: Agent name (@developer, @qa-expert, etc.)
            response: Agent's response text
            group_id: Optional group ID

        Returns:
            Dict with parsed status and next action
        """
        self._add_message(
            agent=agent,
            role="response",
            content=response[:200] + "..." if len(response) > 200 else response,
            metadata={"group_id": group_id},
        )

        # Parse status from response
        status = self._extract_status(response)

        # Determine next action based on workflow
        next_action = self._determine_next_action(agent, status, group_id)

        # Log interaction to backend
        if self._adapter.state:
            self._adapter.log_interaction(
                agent_type=agent.replace("@", "").replace("-", "_"),
                content=response[:500],
                group_id=group_id,
            )

        return {
            "agent": agent,
            "status": status,
            "next_action": next_action,
            "group_id": group_id,
        }

    def _extract_status(self, response: str) -> str:
        """Extract status code from agent response."""
        # Try JSON format first
        try:
            data = json.loads(response)
            if "status" in data:
                return data["status"]
        except json.JSONDecodeError:
            pass

        # Fall back to pattern matching
        status_patterns = [
            "READY_FOR_QA",
            "READY_FOR_REVIEW",
            "PASS",
            "FAIL",
            "FAIL_ESCALATE",
            "APPROVED",
            "CHANGES_REQUESTED",
            "BLOCKED",
            "BAZINGA",
            "PLANNING_COMPLETE",
            "CONTINUE",
        ]

        for pattern in status_patterns:
            if pattern in response.upper():
                return pattern

        return "UNKNOWN"

    def _determine_next_action(
        self,
        agent: str,
        status: str,
        group_id: Optional[str],
    ) -> Dict[str, Any]:
        """Determine next workflow action based on agent response."""
        agent_normalized = agent.replace("@", "").replace("-", "_")

        # Developer flow
        if agent_normalized == "developer":
            if status == "READY_FOR_QA":
                return {"action": "spawn_qa", "group_id": group_id}
            elif status == "READY_FOR_REVIEW":
                return {"action": "spawn_tech_lead", "group_id": group_id}
            elif status == "BLOCKED":
                return {"action": "spawn_tech_lead", "group_id": group_id, "blocked": True}
            elif status == "PARTIAL":
                return {"action": "spawn_tech_lead", "group_id": group_id, "partial": True}
            elif status == "ESCALATE_SENIOR":
                return {"action": "spawn_sse", "group_id": group_id, "escalate": True}

        # Senior Software Engineer flow
        elif agent_normalized == "senior_software_engineer":
            if status == "READY_FOR_QA":
                return {"action": "spawn_qa", "group_id": group_id}
            elif status == "READY_FOR_REVIEW":
                return {"action": "spawn_tech_lead", "group_id": group_id}
            elif status == "BLOCKED":
                return {"action": "spawn_tech_lead", "group_id": group_id, "blocked": True}
            elif status == "ROOT_CAUSE_FOUND":
                return {"action": "spawn_tech_lead", "group_id": group_id, "root_cause": True}
            elif status == "SPAWN_INVESTIGATOR":
                return {"action": "spawn_investigator", "group_id": group_id}

        # QA flow
        elif agent_normalized == "qa_expert":
            if status == "PASS":
                return {"action": "spawn_tech_lead", "group_id": group_id}
            elif status == "FAIL":
                return {"action": "spawn_developer", "group_id": group_id, "retry": True}
            elif status == "FAIL_ESCALATE":
                # Level 3+ failures escalate to SSE, not Developer
                return {"action": "spawn_sse", "group_id": group_id, "escalate": True}
            elif status == "FLAKY":
                return {"action": "spawn_tech_lead", "group_id": group_id, "flaky": True}

        # Tech Lead flow
        elif agent_normalized == "tech_lead":
            if status == "APPROVED":
                return {"action": "check_completion", "group_id": group_id}
            elif status == "APPROVED_WITH_NOTES":
                return {"action": "check_completion", "group_id": group_id, "has_notes": True}
            elif status == "CHANGES_REQUESTED":
                return {"action": "spawn_developer", "group_id": group_id, "changes": True}
            elif status == "SPAWN_INVESTIGATOR":
                return {"action": "spawn_investigator", "group_id": group_id}
            elif status == "UNBLOCKING_GUIDANCE":
                return {"action": "spawn_developer", "group_id": group_id, "guidance": True}

        # Investigator flow
        elif agent_normalized == "investigator":
            if status == "ROOT_CAUSE_FOUND":
                return {"action": "spawn_tech_lead", "group_id": group_id, "root_cause": True}
            elif status == "INVESTIGATION_INCOMPLETE":
                return {"action": "spawn_tech_lead", "group_id": group_id, "incomplete": True}
            elif status == "EXHAUSTED":
                return {"action": "spawn_tech_lead", "group_id": group_id, "exhausted": True}
            elif status == "NEED_DEVELOPER_DIAGNOSTIC":
                return {"action": "spawn_developer", "group_id": group_id, "diagnostic": True}

        # PM flow
        elif agent_normalized == "project_manager":
            if status == "PLANNING_COMPLETE":
                return {"action": "spawn_developers", "start_phase": True}
            elif status == "CONTINUE":
                return {"action": "spawn_developers", "continue": True}
            elif status == "BAZINGA":
                return {"action": "complete", "bazinga": True}
            elif status == "NEEDS_CLARIFICATION":
                return {"action": "request_clarification", "clarification": True}
            elif status == "INVESTIGATION_NEEDED":
                return {"action": "spawn_investigator", "investigation": True}

        return {"action": "unknown", "status": status}

    # =========================================================================
    # Prompt Building
    # =========================================================================

    def _build_pm_prompt(self, context: Optional[str] = None) -> str:
        """Build PM spawn prompt."""
        state = self._adapter.state
        requirements = state.requirements if state else "Unknown requirements"

        prompt = f"""Analyze the following requirements and create a development plan.

Requirements:
{requirements}

{"Additional Context: " + context if context else ""}

Determine:
1. Mode: simple (1 task group) or parallel (multiple groups)
2. Task groups with IDs, names, and descriptions
3. Success criteria for completion
4. Estimated complexity

Return JSON with status: PLANNING_COMPLETE and task_groups array."""

        return prompt

    def _build_developer_prompt(
        self,
        group_id: str,
        task_description: str,
        branch: str,
        specialization: Optional[str] = None,
    ) -> str:
        """Build Developer spawn prompt."""
        state = self._adapter.state

        prompt = f"""Implement the following task.

Session: {state.session_id if state else "unknown"}
Group ID: {group_id}
Branch: {branch}

Task: {task_description}

{"Specialization: " + specialization if specialization else ""}

Requirements:
1. Write clean, tested code
2. Follow project conventions
3. Run lint checks before completing
4. Write handoff file to bazinga/artifacts/{{session_id}}/{{group_id}}/handoff_developer.json

Return JSON with status (READY_FOR_QA, READY_FOR_REVIEW, or BLOCKED)."""

        return prompt

    def _build_qa_prompt(self, group_id: str, handoff_file: str) -> str:
        """Build QA Expert spawn prompt."""
        state = self._adapter.state

        prompt = f"""Test the implementation for group {group_id}.

Session: {state.session_id if state else "unknown"}
Handoff file: {handoff_file}

Run the 5-level QA challenge progression:
1. Boundary probing
2. Mutation analysis
3. Behavioral contracts
4. Security adversary
5. Production chaos

Return JSON with status (PASS, FAIL, or FAIL_ESCALATE)."""

        return prompt

    def _build_tech_lead_prompt(self, group_id: str, handoff_file: str) -> str:
        """Build Tech Lead spawn prompt."""
        state = self._adapter.state

        prompt = f"""Review the implementation for group {group_id}.

Session: {state.session_id if state else "unknown"}
Handoff file: {handoff_file}

Review criteria:
1. Code quality and maintainability
2. Architecture and design patterns
3. Security considerations
4. Test coverage
5. Documentation

Return JSON with status (APPROVED or CHANGES_REQUESTED)."""

        return prompt

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _add_message(
        self,
        agent: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to history."""
        self._messages.append(
            CopilotAgentMessage(
                agent=agent,
                role=role,
                content=content,
                metadata=metadata or {},
            )
        )

    def get_workflow_state(self) -> Dict[str, Any]:
        """Get current workflow state for debugging/display."""
        state = self._adapter.state

        return {
            "session_id": state.session_id if state else None,
            "mode": state.mode if state else None,
            "status": state.status if state else None,
            "current_phase": self._current_phase,
            "task_groups": [
                {"id": g.group_id, "name": g.name, "status": g.status}
                for g in (state.task_groups if state else [])
            ],
            "message_count": len(self._messages),
            "pm_state": self._pm_state,
        }

    def export_copilot_instructions(self) -> str:
        """
        Export orchestration instructions in Copilot format.

        Returns instructions.md content for Copilot agent configuration.
        """
        return """# BAZINGA Orchestrator Instructions (Copilot)

## Your Role

You are the orchestrator for the BAZINGA multi-agent development system.
Coordinate specialized agents to complete software development tasks.

## Available Agents

- @project-manager - Analyzes requirements, creates task groups
- @developer - Implements code
- @senior-software-engineer - Escalation for complex failures
- @qa-expert - Tests implementations
- @tech-lead - Reviews code quality
- @investigator - Deep debugging

## Workflow

1. Spawn @project-manager with requirements
2. Based on PM response, spawn @developer(s)
3. After developer completes, spawn @qa-expert
4. After QA passes, spawn @tech-lead
5. If approved, check for more work or complete
6. When all done, PM sends BAZINGA

## Spawn Syntax

```
#runSubagent @developer "Implement feature X on branch feature/xyz"
```

## Critical Rules

- NEVER implement code yourself
- ALWAYS follow the workflow (dev -> QA -> TL)
- PM decides mode and task groups
- Only PM can send BAZINGA
"""


# ============================================================================
# Entry Point Function
# ============================================================================


def copilot_orchestrate(
    requirements: str,
    project_root: Optional[Path] = None,
    session_id: Optional[str] = None,
) -> CopilotOrchestrator:
    """
    Main entry point for Copilot orchestration.

    Creates an orchestrator, initializes a session, and returns
    the orchestrator ready to drive the workflow.

    Args:
        requirements: User requirements text
        project_root: Optional project root
        session_id: Optional session ID

    Returns:
        Initialized CopilotOrchestrator
    """
    orchestrator = CopilotOrchestrator(project_root=project_root)
    orchestrator.initialize(requirements, session_id)
    return orchestrator
