# Dual-Platform Abstraction Layer Analysis

**Date:** 2026-01-23
**Context:** Design abstraction layer for BAZINGA to support both Claude Code and GitHub Copilot
**Decision:** Pending review
**Status:** Proposed
**Author:** Backend System Architect

---

## Executive Summary

This document defines the abstraction layer architecture required to run BAZINGA on both Claude Code and GitHub Copilot platforms. The design follows the adapter pattern, where platform-specific implementations conform to shared interfaces, allowing the core orchestration logic to remain platform-agnostic.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Platform Difference Matrix](#2-platform-difference-matrix)
3. [Abstraction Requirements](#3-abstraction-requirements)
4. [Architecture Design](#4-architecture-design)
5. [Interface Definitions](#5-interface-definitions)
6. [Implementation Patterns](#6-implementation-patterns)
7. [File Structure Proposal](#7-file-structure-proposal)
8. [Migration Path](#8-migration-path)
9. [Testing Strategy](#9-testing-strategy)
10. [Risk Assessment](#10-risk-assessment)
11. [Critical Analysis](#11-critical-analysis)
12. [Open Questions](#12-open-questions)

---

## 1. Problem Statement

BAZINGA currently runs exclusively on Claude Code, using platform-specific constructs:

- `Task()` tool for agent spawning
- `Skill(command: "x")` for skill invocation
- `.claude/` directory structure for skills and commands
- Claude-specific markdown frontmatter in agent files

To support GitHub Copilot without maintaining two separate codebases, we need an abstraction layer that:

1. **Isolates platform-specific code** behind stable interfaces
2. **Preserves 100% of BAZINGA functionality** on both platforms
3. **Enables incremental migration** without breaking existing Claude Code support
4. **Minimizes code duplication** between platforms

---

## 2. Platform Difference Matrix

### 2.1 Core Feature Comparison

| Feature | Claude Code | Copilot | Abstraction Needed |
|---------|-------------|---------|-------------------|
| **Agent Spawning** | `Task()` tool with explicit model selection | `#runSubagent`, handoffs, `@agent` | `AgentSpawner` interface |
| **Skill Invocation** | `Skill(command: "name")` explicit invocation | Automatic by description match | `SkillInvoker` interface |
| **Context Management** | Inherited context, manual compaction | Isolated subagent contexts, auto-compaction | `ContextManager` interface |
| **State Persistence** | SQLite via bazinga-db skill | Unknown (likely in-memory) | `StateManager` interface |
| **Agent Definitions** | `agents/*.md` with frontmatter | `.github/agents/*.agent.md` with YAML | `AgentDefinitionParser` |
| **Skill Definitions** | `.claude/skills/*/SKILL.md` | `.github/skills/*/SKILL.md` | Shared with path mapping |
| **Commands/Slash** | `.claude/commands/*.md` | Not directly supported | Partial (adapt to handoffs) |
| **Configuration** | `bazinga/*.json` files | Unknown (VS Code settings?) | `ConfigurationProvider` |
| **Tool Confirmation** | Per-model tool permissions | Per-invocation/session confirmation | `ToolPermissionManager` |
| **Parallelism** | Multiple `Task()` in one message | No built-in parallelism | `ParallelExecutor` interface |

### 2.2 Directory Structure Mapping

| Claude Code | Copilot | Notes |
|-------------|---------|-------|
| `.claude/agents/` | `.github/agents/` | Agent definitions |
| `.claude/skills/` | `.github/skills/` (or `.claude/skills/`) | Copilot supports both |
| `.claude/commands/` | No equivalent | Convert to handoffs |
| `.claude/templates/` | `.github/templates/` or inline | Context injection |
| `bazinga/` | `bazinga/` | Shared runtime directory |
| `agents/*.md` | `.github/agents/*.agent.md` | Different file extension |

### 2.3 Agent Definition Format Comparison

**Claude Code (`agents/developer.md`):**
```yaml
---
name: developer
description: Implementation specialist that writes code...
model: sonnet
---

# Developer Agent

You are a **DEVELOPER AGENT**...
```

**Copilot (`.github/agents/developer.agent.md`):**
```yaml
---
name: developer
description: Implementation specialist that writes code...
tools:
  - read
  - edit
  - terminal
handoffs:
  - label: "Send to QA"
    agent: "qa_expert"
    prompt: "Test this implementation"
    send: false
---

# Developer Agent

You are a **DEVELOPER AGENT**...
```

**Key differences:**
- Copilot requires `.agent.md` extension
- Copilot uses `tools:` instead of `allowed-tools:`
- Copilot has `handoffs:` for agent transitions (we use workflow-router)
- Copilot does not have `model:` field (model selection is different)

### 2.4 Skill Format Comparison

Both platforms use similar SKILL.md format, but with different paths and loading semantics:

| Aspect | Claude Code | Copilot |
|--------|-------------|---------|
| Discovery | Explicit invocation | Automatic by description |
| Loading | Full load on invocation | Progressive 3-level |
| Path | `.claude/skills/*/SKILL.md` | `.github/skills/*/SKILL.md` |
| Tools | `allowed-tools:` frontmatter | Implicit based on content |

---

## 3. Abstraction Requirements

### 3.1 What MUST Be Abstracted

These features differ fundamentally between platforms and require platform-specific implementations:

| Component | Why Abstraction Required |
|-----------|-------------------------|
| **Agent Spawning** | `Task()` vs `#runSubagent`/handoffs - completely different APIs |
| **Skill Invocation** | Explicit vs automatic - different invocation paradigms |
| **Agent Definition Parsing** | Different frontmatter schema, different file extensions |
| **Model Selection** | Claude has explicit model per agent, Copilot is model-agnostic |
| **Context Passing** | Inherited vs isolated - affects how we pass state between agents |
| **Parallel Execution** | Multiple `Task()` vs sequential handoffs |
| **Status Extraction** | CRP JSON parsing vs Copilot response parsing |
| **Tool Permissions** | Claude's per-model vs Copilot's per-session approval |

### 3.2 What CAN Be Shared Directly

These components work identically or near-identically on both platforms:

| Component | Sharing Strategy |
|-----------|------------------|
| **Workflow State Machine** | `workflow/transitions.json` - platform-agnostic |
| **Agent Markers** | `workflow/agent-markers.json` - status codes work on both |
| **Templates** | `templates/specializations/` - markdown content works everywhere |
| **Database Schema** | `bazinga/bazinga.db` - SQLite is platform-agnostic |
| **Configuration Files** | `bazinga/*.json` - JSON parsing works everywhere |
| **SKILL.md Content** | Body content is platform-agnostic |
| **Message Templates** | `bazinga/templates/message_templates.md` |

### 3.3 What Must Be Platform-Specific

| Component | Claude Code Implementation | Copilot Implementation |
|-----------|---------------------------|------------------------|
| **Agent Definitions** | `agents/*.md` with model field | `.github/agents/*.agent.md` with handoffs |
| **Skill Discovery** | Registry of available skills | SKILL.md descriptions for auto-match |
| **Orchestrator Entry** | `/bazinga.orchestrate` command | `@orchestrator` agent mention |
| **Slash Commands** | `.claude/commands/` directory | Convert to agent handoffs |
| **Model Routing** | `bazinga/model_selection.json` | N/A (single model per context) |
| **Background Execution** | `run_in_background: false` enforcement | N/A (no background mode) |

---

## 4. Architecture Design

### 4.1 High-Level Architecture

```
+-----------------------------------------------------------------------+
|                           BAZINGA CORE                                 |
|                                                                        |
|  +------------------+  +------------------+  +------------------+      |
|  | Workflow Engine  |  | State Machine    |  | Template Engine  |      |
|  | (transitions.json)  | (workflow-router)|  | (specializations)|      |
|  +------------------+  +------------------+  +------------------+      |
|                                                                        |
|  +------------------+  +------------------+  +------------------+      |
|  | Database Layer   |  | Configuration    |  | Message Format   |      |
|  | (bazinga-db)     |  | Provider         |  | (CRP JSON)       |      |
|  +------------------+  +------------------+  +------------------+      |
+-----------------------------------------------------------------------+
                                    |
                          Platform Interfaces
                                    |
          +-------------------------+-------------------------+
          |                                                   |
+---------+---------+                             +-----------+---------+
|  CLAUDE ADAPTER   |                             |   COPILOT ADAPTER   |
|                   |                             |                     |
| +---------------+ |                             | +---------------+   |
| | AgentSpawner  | |                             | | AgentSpawner  |   |
| | (Task())      | |                             | | (#runSubagent)|   |
| +---------------+ |                             | +---------------+   |
|                   |                             |                     |
| +---------------+ |                             | +---------------+   |
| | SkillInvoker  | |                             | | SkillInvoker  |   |
| | (Skill())     | |                             | | (auto-match)  |   |
| +---------------+ |                             | +---------------+   |
|                   |                             |                     |
| +---------------+ |                             | +---------------+   |
| | ContextMgr    | |                             | | ContextMgr    |   |
| | (inherited)   | |                             | | (isolated)    |   |
| +---------------+ |                             | +---------------+   |
|                   |                             |                     |
| +---------------+ |                             | +---------------+   |
| | AgentDefParser| |                             | | AgentDefParser|   |
| | (agents/*.md) | |                             | | (.agent.md)   |   |
| +---------------+ |                             | +---------------+   |
+-------------------+                             +---------------------+
```

### 4.2 Runtime Detection

The abstraction layer must detect which platform it's running on at startup:

```python
# bazinga/core/platform.py

class Platform(Enum):
    CLAUDE_CODE = "claude_code"
    COPILOT = "copilot"
    UNKNOWN = "unknown"

def detect_platform() -> Platform:
    """
    Detect which platform BAZINGA is running on.

    Detection strategy:
    1. Check for Claude-specific environment variable
    2. Check for Copilot-specific markers
    3. Check directory structure
    4. Fall back to UNKNOWN
    """
    # Check Claude Code markers
    if os.path.exists(".claude") and os.getenv("CLAUDE_CODE_VERSION"):
        return Platform.CLAUDE_CODE

    # Check Copilot markers
    if os.path.exists(".github/agents") or os.getenv("GITHUB_COPILOT_VERSION"):
        return Platform.COPILOT

    # Check for .claude directory (legacy Claude Code detection)
    if os.path.exists(".claude/skills"):
        return Platform.CLAUDE_CODE

    # Check for .github skills (Copilot)
    if os.path.exists(".github/skills"):
        return Platform.COPILOT

    return Platform.UNKNOWN
```

### 4.3 Adapter Factory Pattern

```python
# bazinga/core/factory.py

from typing import Protocol
from .platform import detect_platform, Platform

def get_platform_adapter() -> "PlatformAdapter":
    """
    Factory function to get the appropriate platform adapter.
    """
    platform = detect_platform()

    if platform == Platform.CLAUDE_CODE:
        from bazinga.adapters.claude import ClaudeAdapter
        return ClaudeAdapter()

    elif platform == Platform.COPILOT:
        from bazinga.adapters.copilot import CopilotAdapter
        return CopilotAdapter()

    else:
        raise RuntimeError(
            "Unable to detect platform. "
            "Ensure you're running in Claude Code or GitHub Copilot environment."
        )
```

---

## 5. Interface Definitions

### 5.1 Core Interfaces

```python
# bazinga/core/interfaces.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

class AgentType(Enum):
    """Standard agent types across both platforms."""
    ORCHESTRATOR = "orchestrator"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    SENIOR_SOFTWARE_ENGINEER = "senior_software_engineer"
    QA_EXPERT = "qa_expert"
    TECH_LEAD = "tech_lead"
    INVESTIGATOR = "investigator"
    REQUIREMENTS_ENGINEER = "requirements_engineer"
    VALIDATOR = "validator"

@dataclass
class AgentSpawnParams:
    """Parameters for spawning an agent."""
    agent_type: AgentType
    prompt: str
    session_id: str
    group_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    prior_handoff_file: Optional[str] = None
    model_override: Optional[str] = None  # Claude-specific

@dataclass
class AgentResponse:
    """Standardized agent response."""
    status: str  # e.g., "READY_FOR_QA", "APPROVED", "BAZINGA"
    summary: List[str]
    handoff_file: Optional[str] = None
    raw_response: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentSpawner(ABC):
    """
    Interface for spawning agents.

    Claude Code: Uses Task() tool
    Copilot: Uses #runSubagent or handoffs
    """

    @abstractmethod
    async def spawn(self, params: AgentSpawnParams) -> AgentResponse:
        """Spawn an agent and wait for response."""
        pass

    @abstractmethod
    async def spawn_parallel(
        self, params_list: List[AgentSpawnParams]
    ) -> List[AgentResponse]:
        """Spawn multiple agents in parallel (if supported)."""
        pass

    @abstractmethod
    def supports_parallel(self) -> bool:
        """Check if platform supports parallel agent spawning."""
        pass

    @abstractmethod
    def get_max_parallel(self) -> int:
        """Get maximum parallel agents supported (0 if not supported)."""
        pass

@dataclass
class SkillInvocation:
    """Parameters for invoking a skill."""
    skill_name: str
    operation: str
    params: Dict[str, Any]

@dataclass
class SkillResult:
    """Result from skill invocation."""
    success: bool
    output: Any
    error: Optional[str] = None

class SkillInvoker(ABC):
    """
    Interface for invoking skills.

    Claude Code: Explicit Skill(command: "name") invocation
    Copilot: Automatic invocation based on description matching
    """

    @abstractmethod
    async def invoke(self, invocation: SkillInvocation) -> SkillResult:
        """Invoke a skill with given parameters."""
        pass

    @abstractmethod
    def list_available_skills(self) -> List[str]:
        """List all available skills."""
        pass

    @abstractmethod
    def get_skill_path(self, skill_name: str) -> str:
        """Get the path to a skill's SKILL.md file."""
        pass

class ContextManager(ABC):
    """
    Interface for managing context between agents.

    Claude Code: Inherited context with manual compaction
    Copilot: Isolated subagent contexts with auto-compaction
    """

    @abstractmethod
    def prepare_agent_context(
        self,
        agent_type: AgentType,
        session_id: str,
        group_id: Optional[str] = None,
        include_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Prepare context to pass to an agent."""
        pass

    @abstractmethod
    def extract_handoff_context(self, response: AgentResponse) -> Dict[str, Any]:
        """Extract context from agent response for handoff."""
        pass

    @abstractmethod
    def supports_context_isolation(self) -> bool:
        """Check if platform supports isolated agent contexts."""
        pass

class StateManager(ABC):
    """
    Interface for persistent state management.

    Both platforms: SQLite via bazinga-db skill
    """

    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        mode: str,
        requirements: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new orchestration session."""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        pass

    @abstractmethod
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status."""
        pass

    @abstractmethod
    async def log_interaction(
        self,
        session_id: str,
        agent_type: str,
        content: str,
        iteration: int = 1
    ) -> bool:
        """Log agent interaction."""
        pass

    @abstractmethod
    async def save_task_group(
        self,
        session_id: str,
        group_id: str,
        name: str,
        status: str = "pending",
        specializations: Optional[List[str]] = None
    ) -> bool:
        """Save or update a task group."""
        pass

    @abstractmethod
    async def get_task_groups(
        self,
        session_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get task groups for a session."""
        pass

@dataclass
class AgentDefinition:
    """Parsed agent definition."""
    name: str
    description: str
    model: Optional[str]  # Claude-specific
    tools: List[str]
    handoffs: List[Dict[str, Any]]  # Copilot-specific
    body: str  # Markdown content

class AgentDefinitionParser(ABC):
    """
    Interface for parsing agent definition files.

    Claude Code: agents/*.md with model field
    Copilot: .github/agents/*.agent.md with handoffs
    """

    @abstractmethod
    def parse(self, file_path: str) -> AgentDefinition:
        """Parse an agent definition file."""
        pass

    @abstractmethod
    def get_agent_path(self, agent_type: AgentType) -> str:
        """Get the file path for an agent definition."""
        pass

    @abstractmethod
    def list_agents(self) -> List[str]:
        """List all available agent definition files."""
        pass

class ConfigurationProvider(ABC):
    """
    Interface for configuration management.

    Both platforms: bazinga/*.json files
    """

    @abstractmethod
    def get_model_config(self) -> Dict[str, Dict[str, str]]:
        """Get model configuration (agent -> model mapping)."""
        pass

    @abstractmethod
    def get_skills_config(self) -> Dict[str, Dict[str, str]]:
        """Get skills configuration (agent -> skills -> mode)."""
        pass

    @abstractmethod
    def get_testing_config(self) -> Dict[str, Any]:
        """Get testing configuration."""
        pass

    @abstractmethod
    def get_workflow_transitions(self) -> Dict[str, Any]:
        """Get workflow state machine transitions."""
        pass

class PlatformAdapter(ABC):
    """
    Main platform adapter that provides all interfaces.
    """

    @property
    @abstractmethod
    def spawner(self) -> AgentSpawner:
        """Get the agent spawner for this platform."""
        pass

    @property
    @abstractmethod
    def skill_invoker(self) -> SkillInvoker:
        """Get the skill invoker for this platform."""
        pass

    @property
    @abstractmethod
    def context_manager(self) -> ContextManager:
        """Get the context manager for this platform."""
        pass

    @property
    @abstractmethod
    def state_manager(self) -> StateManager:
        """Get the state manager for this platform."""
        pass

    @property
    @abstractmethod
    def agent_parser(self) -> AgentDefinitionParser:
        """Get the agent definition parser for this platform."""
        pass

    @property
    @abstractmethod
    def config_provider(self) -> ConfigurationProvider:
        """Get the configuration provider for this platform."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get the platform name."""
        pass
```

### 5.2 Response Parsing Interface

```python
# bazinga/core/response_parser.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re
import json

@dataclass
class ParsedResponse:
    """Standardized parsed response from any agent."""
    status: str
    summary: List[str]
    raw_output: str
    confidence: float  # 0.0 to 1.0 based on extraction confidence
    fallback_used: bool
    metadata: Dict[str, Any]

class ResponseParser(ABC):
    """
    Interface for parsing agent responses.

    Both platforms use CRP JSON format, but fallback strategies differ.
    """

    @abstractmethod
    def parse(self, raw_response: str, agent_type: str) -> ParsedResponse:
        """Parse a raw agent response into structured format."""
        pass

    @abstractmethod
    def extract_status(self, raw_response: str, agent_type: str) -> str:
        """Extract status code from response."""
        pass

    @abstractmethod
    def extract_handoff_file(self, raw_response: str) -> Optional[str]:
        """Extract handoff file path if present."""
        pass

class CRPResponseParser(ResponseParser):
    """
    Shared implementation for CRP JSON format parsing.

    This is platform-agnostic and can be used by both adapters.
    """

    # Status patterns per agent type
    STATUS_PATTERNS = {
        "developer": [
            "READY_FOR_QA", "READY_FOR_REVIEW", "BLOCKED",
            "PARTIAL", "ESCALATE_SENIOR", "NEEDS_TECH_LEAD_VALIDATION",
            "MERGE_SUCCESS", "MERGE_CONFLICT", "MERGE_TEST_FAILURE", "MERGE_BLOCKED"
        ],
        "qa_expert": ["PASS", "FAIL", "FAIL_ESCALATE", "BLOCKED", "FLAKY", "PARTIAL"],
        "tech_lead": [
            "APPROVED", "CHANGES_REQUESTED", "SPAWN_INVESTIGATOR",
            "ESCALATE_TO_OPUS", "UNBLOCKING_GUIDANCE", "ARCHITECTURAL_DECISION_MADE"
        ],
        "project_manager": [
            "PLANNING_COMPLETE", "CONTINUE", "BAZINGA",
            "NEEDS_CLARIFICATION", "INVESTIGATION_NEEDED", "INVESTIGATION_ONLY"
        ],
        "investigator": [
            "ROOT_CAUSE_FOUND", "INVESTIGATION_INCOMPLETE", "BLOCKED",
            "EXHAUSTED", "NEED_DEVELOPER_DIAGNOSTIC",
            "HYPOTHESIS_ELIMINATED", "NEED_MORE_ANALYSIS"
        ],
        # ... other agent types
    }

    def parse(self, raw_response: str, agent_type: str) -> ParsedResponse:
        """
        Parse CRP JSON format with fallbacks.

        Expected format:
        {"status": "READY_FOR_QA", "summary": ["Line 1", "Line 2"]}
        """
        # Try JSON extraction first
        json_match = re.search(r'\{[^{}]*"status"[^{}]*\}', raw_response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return ParsedResponse(
                    status=parsed.get("status", "UNKNOWN"),
                    summary=parsed.get("summary", []),
                    raw_output=raw_response,
                    confidence=1.0,
                    fallback_used=False,
                    metadata=parsed
                )
            except json.JSONDecodeError:
                pass

        # Fallback: Extract status from markdown
        status = self.extract_status(raw_response, agent_type)
        return ParsedResponse(
            status=status,
            summary=[raw_response[:200]],  # First 200 chars as summary
            raw_output=raw_response,
            confidence=0.5,
            fallback_used=True,
            metadata={}
        )

    def extract_status(self, raw_response: str, agent_type: str) -> str:
        """Extract status using pattern matching."""
        patterns = self.STATUS_PATTERNS.get(agent_type, [])
        for pattern in patterns:
            if pattern in raw_response.upper():
                return pattern
        return "UNKNOWN"

    def extract_handoff_file(self, raw_response: str) -> Optional[str]:
        """Extract handoff file path."""
        match = re.search(r'handoff[_-]?\w*\.json', raw_response)
        return match.group() if match else None
```

---

## 6. Implementation Patterns

### 6.1 Claude Code Adapter

```python
# bazinga/adapters/claude/spawner.py

from bazinga.core.interfaces import (
    AgentSpawner, AgentSpawnParams, AgentResponse, AgentType
)
from typing import List

class ClaudeAgentSpawner(AgentSpawner):
    """
    Claude Code implementation using Task() tool.
    """

    MAX_PARALLEL = 4  # BAZINGA hard limit

    async def spawn(self, params: AgentSpawnParams) -> AgentResponse:
        """
        Spawn agent using Task() tool.

        This generates the Task() call that Claude Code will execute.
        """
        task_params = {
            "subagent_type": "general-purpose",
            "model": self._get_model(params.agent_type, params.model_override),
            "description": f"Spawn {params.agent_type.value} for {params.session_id}",
            "prompt": params.prompt,
            "run_in_background": False  # CRITICAL: Always foreground
        }

        # Generate Task() invocation
        # Note: Actual execution happens in the orchestrator context
        return AgentResponse(
            status="SPAWNED",
            summary=[f"Task() called for {params.agent_type.value}"],
            metadata={"task_params": task_params}
        )

    async def spawn_parallel(
        self, params_list: List[AgentSpawnParams]
    ) -> List[AgentResponse]:
        """
        Spawn multiple agents in parallel.

        Claude Code supports this via multiple Task() calls in one message.
        """
        if len(params_list) > self.MAX_PARALLEL:
            raise ValueError(
                f"Cannot spawn more than {self.MAX_PARALLEL} agents in parallel"
            )

        responses = []
        for params in params_list:
            response = await self.spawn(params)
            responses.append(response)

        return responses

    def supports_parallel(self) -> bool:
        return True

    def get_max_parallel(self) -> int:
        return self.MAX_PARALLEL

    def _get_model(
        self, agent_type: AgentType, override: Optional[str] = None
    ) -> str:
        """Get model from config or use override."""
        if override:
            return override

        # Read from bazinga/model_selection.json
        config = self._load_model_config()
        return config.get("agents", {}).get(agent_type.value, {}).get("model", "sonnet")

    def _load_model_config(self) -> dict:
        """Load model configuration from JSON file."""
        import json
        try:
            with open("bazinga/model_selection.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"agents": {}}
```

### 6.2 Copilot Adapter

```python
# bazinga/adapters/copilot/spawner.py

from bazinga.core.interfaces import (
    AgentSpawner, AgentSpawnParams, AgentResponse, AgentType
)
from typing import List

class CopilotAgentSpawner(AgentSpawner):
    """
    GitHub Copilot implementation using #runSubagent or handoffs.
    """

    async def spawn(self, params: AgentSpawnParams) -> AgentResponse:
        """
        Spawn agent using Copilot mechanisms.

        Strategy:
        1. For subagent spawning: Use #runSubagent directive
        2. For agent transitions: Use handoff buttons
        """
        # Generate #runSubagent directive
        # Copilot will process this in the chat context
        directive = f"""
#runSubagent

@{params.agent_type.value}

{params.prompt}
"""

        return AgentResponse(
            status="SPAWNED",
            summary=[f"#runSubagent called for @{params.agent_type.value}"],
            metadata={"directive": directive}
        )

    async def spawn_parallel(
        self, params_list: List[AgentSpawnParams]
    ) -> List[AgentResponse]:
        """
        Copilot does not support parallel agent spawning.

        Fallback: Sequential spawning with handoffs.
        """
        responses = []
        for params in params_list:
            response = await self.spawn(params)
            responses.append(response)
            # Note: In Copilot, these will execute sequentially

        return responses

    def supports_parallel(self) -> bool:
        return False  # Copilot executes agents sequentially

    def get_max_parallel(self) -> int:
        return 0  # No parallel support
```

### 6.3 Skill Invoker Implementations

**Claude Code:**
```python
# bazinga/adapters/claude/skill_invoker.py

class ClaudeSkillInvoker(SkillInvoker):
    """Claude Code uses explicit Skill(command: "name") invocation."""

    SKILL_BASE_PATH = ".claude/skills"

    async def invoke(self, invocation: SkillInvocation) -> SkillResult:
        """
        Invoke skill using Skill() tool.

        Format: Skill(command: "skill-name")
        """
        # Generate Skill() invocation
        return SkillResult(
            success=True,
            output=f'Skill(command: "{invocation.skill_name}")',
            error=None
        )

    def list_available_skills(self) -> List[str]:
        """List skills from .claude/skills/ directory."""
        import os
        skills = []
        for item in os.listdir(self.SKILL_BASE_PATH):
            skill_path = os.path.join(self.SKILL_BASE_PATH, item, "SKILL.md")
            if os.path.exists(skill_path):
                skills.append(item)
        return skills

    def get_skill_path(self, skill_name: str) -> str:
        return f"{self.SKILL_BASE_PATH}/{skill_name}/SKILL.md"
```

**Copilot:**
```python
# bazinga/adapters/copilot/skill_invoker.py

class CopilotSkillInvoker(SkillInvoker):
    """
    Copilot uses automatic skill activation based on description matching.

    Skills are discovered from .github/skills/ or .claude/skills/ (backward compat).
    """

    SKILL_PATHS = [".github/skills", ".claude/skills"]

    async def invoke(self, invocation: SkillInvocation) -> SkillResult:
        """
        In Copilot, skills are invoked automatically based on prompt content.

        We generate a prompt that will trigger the skill.
        """
        # Generate prompt that will trigger skill auto-activation
        prompt = self._generate_skill_trigger_prompt(invocation)

        return SkillResult(
            success=True,
            output=prompt,
            error=None
        )

    def _generate_skill_trigger_prompt(
        self, invocation: SkillInvocation
    ) -> str:
        """Generate prompt that triggers skill based on description."""
        skill_info = self._get_skill_info(invocation.skill_name)

        # Use skill description to craft triggering prompt
        return f"""
Please {skill_info['description']}

Parameters:
- Operation: {invocation.operation}
{self._format_params(invocation.params)}
"""

    def list_available_skills(self) -> List[str]:
        """List skills from all supported paths."""
        import os
        skills = []
        for base_path in self.SKILL_PATHS:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    skill_path = os.path.join(base_path, item, "SKILL.md")
                    if os.path.exists(skill_path):
                        skills.append(item)
        return skills
```

---

## 7. File Structure Proposal

### 7.1 Core Package Structure

```
bazinga/
├── core/                          # Platform-agnostic core
│   ├── __init__.py
│   ├── interfaces.py              # All abstract interfaces
│   ├── platform.py                # Platform detection
│   ├── factory.py                 # Adapter factory
│   ├── workflow_engine.py         # Workflow state machine
│   ├── response_parser.py         # CRP JSON parsing
│   └── message_formatter.py       # Output capsule formatting
│
├── adapters/                      # Platform-specific implementations
│   ├── __init__.py
│   ├── claude/                    # Claude Code adapter
│   │   ├── __init__.py
│   │   ├── adapter.py             # Main ClaudeAdapter class
│   │   ├── spawner.py             # ClaudeAgentSpawner
│   │   ├── skill_invoker.py       # ClaudeSkillInvoker
│   │   ├── context_manager.py     # ClaudeContextManager
│   │   ├── agent_parser.py        # ClaudeAgentDefinitionParser
│   │   └── state_manager.py       # ClaudeStateManager (uses bazinga-db)
│   │
│   └── copilot/                   # Copilot adapter
│       ├── __init__.py
│       ├── adapter.py             # Main CopilotAdapter class
│       ├── spawner.py             # CopilotAgentSpawner
│       ├── skill_invoker.py       # CopilotSkillInvoker
│       ├── context_manager.py     # CopilotContextManager
│       ├── agent_parser.py        # CopilotAgentDefinitionParser
│       └── state_manager.py       # CopilotStateManager (uses bazinga-db)
│
└── shared/                        # Shared utilities
    ├── __init__.py
    ├── config_loader.py           # JSON configuration loading
    ├── template_engine.py         # Template processing
    └── validation.py              # Input validation
```

### 7.2 Agent and Skill Dual-Location

```
project_root/
│
├── agents/                        # Claude Code agent definitions (source)
│   ├── developer.md
│   ├── orchestrator.md
│   ├── project_manager.md
│   └── ...
│
├── .github/agents/                # Copilot agent definitions (generated)
│   ├── developer.agent.md
│   ├── orchestrator.agent.md
│   ├── project_manager.agent.md
│   └── ...
│
├── .claude/skills/                # Skills (works for both)
│   ├── bazinga-db/
│   ├── prompt-builder/
│   └── ...
│
├── .github/skills/                # Copilot skill symlinks (optional)
│   └── -> ../.claude/skills/      # Symlink to .claude/skills
│
├── workflow/                      # Shared workflow configuration
│   ├── transitions.json
│   └── agent-markers.json
│
└── bazinga/                       # Runtime state (shared)
    ├── bazinga.db
    ├── model_selection.json
    ├── skills_config.json
    └── templates/
```

### 7.3 Installation Modification

The CLI installer needs to be updated to support both platforms:

```python
# src/bazinga_cli/__init__.py (modified)

def install(platform: str = "auto"):
    """
    Install BAZINGA files for the specified platform.

    Args:
        platform: "claude", "copilot", or "auto" (detect from environment)
    """
    if platform == "auto":
        platform = detect_target_platform()

    if platform == "claude":
        copy_claude_files()
    elif platform == "copilot":
        copy_copilot_files()
    elif platform == "both":
        copy_claude_files()
        copy_copilot_files()

    # Always copy shared files
    copy_shared_files()

def copy_claude_files():
    """Copy Claude Code specific files."""
    copy_agents(target_dir / ".claude" / "agents")
    copy_commands(target_dir / ".claude" / "commands")
    copy_skills(target_dir / ".claude" / "skills")

def copy_copilot_files():
    """Copy Copilot specific files."""
    generate_copilot_agents(target_dir / ".github" / "agents")
    # Symlink skills to .claude/skills for compatibility
    create_skill_symlink(target_dir)

def generate_copilot_agents(target_dir):
    """
    Generate Copilot-format agent files from Claude agent files.

    Transformation:
    - Add .agent.md extension
    - Convert model: field to tools: field
    - Generate handoffs from workflow/transitions.json
    """
    for agent_file in source_agents:
        definition = parse_claude_agent(agent_file)
        copilot_definition = transform_to_copilot(definition)
        write_copilot_agent(target_dir / f"{definition.name}.agent.md", copilot_definition)
```

---

## 8. Migration Path

### 8.1 Phase 1: Foundation (Week 1-2)

**Goal:** Create abstraction layer without breaking existing functionality

1. **Create interfaces module** (`bazinga/core/interfaces.py`)
   - Define all interfaces as Python ABCs
   - No implementation changes to existing code

2. **Implement Claude adapter** (`bazinga/adapters/claude/`)
   - Wrap existing functionality in adapter pattern
   - All existing code continues to work unchanged

3. **Add platform detection** (`bazinga/core/platform.py`)
   - Detect Claude Code environment
   - Default to Claude Code for unknown environments

4. **Testing:** Run full integration test suite
   - Ensure 100% compatibility with existing Claude Code behavior

### 8.2 Phase 2: Copilot Scaffolding (Week 3-4)

**Goal:** Create Copilot adapter skeleton

1. **Implement Copilot adapter** (`bazinga/adapters/copilot/`)
   - Stub implementations that raise NotImplementedError
   - Identify which features need most work

2. **Generate Copilot agent files**
   - Script to transform `agents/*.md` to `.github/agents/*.agent.md`
   - Validate generated files in Copilot environment

3. **Skill path mapping**
   - Create symlink strategy for `.github/skills/`
   - Test skill discovery in Copilot

4. **Testing:** Manual Copilot environment testing
   - Verify agent files load correctly
   - Verify skills are discovered

### 8.3 Phase 3: Copilot Implementation (Week 5-8)

**Goal:** Full Copilot support

1. **Implement CopilotAgentSpawner**
   - `#runSubagent` directive generation
   - Handoff button configuration
   - Response parsing for Copilot format

2. **Implement CopilotSkillInvoker**
   - Auto-activation prompt generation
   - Skill description matching

3. **Implement CopilotContextManager**
   - Isolated context handling
   - Context sanitization for subagents

4. **Implement CopilotStateManager**
   - Reuse bazinga-db skill (shared)
   - Handle Copilot-specific session metadata

5. **Testing:** Full integration test on Copilot
   - Run Simple Calculator test
   - Verify all agent transitions

### 8.4 Phase 4: Parallel Strategy (Week 9-10)

**Goal:** Handle Copilot's lack of parallel execution

1. **Implement sequential fallback**
   - When `spawn_parallel` called on Copilot
   - Execute agents sequentially with proper handoffs

2. **Optimize for Copilot's strengths**
   - Leverage worktree isolation for concurrent file changes
   - Use handoff context to maintain state

3. **Update orchestrator logic**
   - Detect platform and adjust parallelism strategy
   - PM outputs parallel groups that execute sequentially on Copilot

4. **Testing:** Compare execution on both platforms
   - Same input, verify same output
   - Document performance differences

### 8.5 Phase 5: Polish and Documentation (Week 11-12)

**Goal:** Production-ready dual-platform support

1. **CLI updates**
   - `bazinga install --platform=copilot`
   - `bazinga install --platform=both`

2. **Documentation**
   - Platform-specific setup guides
   - Limitation documentation for Copilot

3. **Test coverage**
   - Unit tests for all interfaces
   - Integration tests on both platforms
   - CI/CD for both platforms

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_interfaces.py

import pytest
from bazinga.core.interfaces import AgentSpawner, AgentSpawnParams

class TestAgentSpawnerInterface:
    """Test that all adapters implement AgentSpawner correctly."""

    @pytest.fixture(params=["claude", "copilot"])
    def spawner(self, request):
        """Get spawner for each platform."""
        if request.param == "claude":
            from bazinga.adapters.claude import ClaudeAgentSpawner
            return ClaudeAgentSpawner()
        else:
            from bazinga.adapters.copilot import CopilotAgentSpawner
            return CopilotAgentSpawner()

    def test_spawn_returns_response(self, spawner):
        """Test that spawn returns an AgentResponse."""
        params = AgentSpawnParams(
            agent_type="developer",
            prompt="Test prompt",
            session_id="test_session"
        )
        response = spawner.spawn(params)
        assert response.status is not None

    def test_supports_parallel_returns_bool(self, spawner):
        """Test that supports_parallel returns a boolean."""
        result = spawner.supports_parallel()
        assert isinstance(result, bool)
```

### 9.2 Integration Tests

```python
# tests/integration/test_dual_platform.py

import pytest
from bazinga.core.factory import get_platform_adapter

@pytest.fixture
def adapter():
    """Get the appropriate adapter for current platform."""
    return get_platform_adapter()

class TestOrchestratorWorkflow:
    """Test that full orchestrator workflow works on both platforms."""

    def test_session_creation(self, adapter):
        """Test session can be created."""
        result = adapter.state_manager.create_session(
            session_id="test_" + str(time.time()),
            mode="simple",
            requirements="Test requirements"
        )
        assert result is True

    def test_agent_spawn_and_response(self, adapter):
        """Test agent can be spawned and returns response."""
        # This test validates the full spawn -> response cycle
        pass

    def test_skill_invocation(self, adapter):
        """Test skill can be invoked."""
        result = adapter.skill_invoker.invoke(
            SkillInvocation(
                skill_name="bazinga-db",
                operation="list-sessions",
                params={"limit": 1}
            )
        )
        assert result.success
```

### 9.3 Cross-Platform Verification

```bash
# scripts/test-dual-platform.sh

#!/bin/bash
# Run same test on both platforms and compare results

echo "=== Testing on Claude Code ==="
BAZINGA_PLATFORM=claude python -m pytest tests/integration/ -v

echo "=== Testing on Copilot ==="
BAZINGA_PLATFORM=copilot python -m pytest tests/integration/ -v

echo "=== Comparing results ==="
diff results_claude.json results_copilot.json
```

---

## 10. Risk Assessment

### 10.1 High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Copilot API changes** | Adapter becomes invalid | Monitor Copilot changelog, version-pin behavior |
| **Parallel execution gap** | Performance degradation on Copilot | Document clearly, provide optimization guide |
| **State management differences** | Data inconsistency | Use SQLite as single source of truth |
| **Context size limits** | Prompts too large for Copilot | Implement progressive loading like Copilot skills |

### 10.2 Medium Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Handoff configuration complexity** | Hard to maintain | Auto-generate from transitions.json |
| **Skill auto-activation reliability** | Wrong skill invoked | Improve descriptions, add explicit triggers |
| **Model selection on Copilot** | Can't control model tier | Accept limitation, document behavior |

### 10.3 Low Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Directory structure differences** | Minor confusion | Clear documentation, symlinks |
| **File extension differences** | Build script complexity | Automated generation |
| **Configuration file locations** | Minor maintenance | Shared location (bazinga/) |

---

## 11. Critical Analysis

### 11.1 Pros

1. **Clean separation of concerns** - Platform-specific code isolated
2. **Incremental migration** - Can add Copilot support without breaking Claude
3. **Shared state** - SQLite database works on both platforms
4. **Minimal code duplication** - Core logic shared, only adapters differ
5. **Future-proof** - Easy to add more platforms (e.g., Cursor)

### 11.2 Cons

1. **Increased complexity** - More abstraction layers to maintain
2. **Performance overhead** - Additional function calls through interfaces
3. **Parallel execution gap** - Copilot cannot match Claude's parallel spawning
4. **Testing burden** - Must test on both platforms
5. **Model selection loss** - Copilot doesn't support per-agent model selection

### 11.3 Verdict

**Recommendation: PROCEED with abstraction layer implementation.**

The benefits of dual-platform support outweigh the costs. The key success factors are:

1. **Keep interfaces minimal** - Only abstract what's necessary
2. **Document limitations clearly** - Users must understand Copilot's constraints
3. **Automate testing** - CI/CD on both platforms from day one
4. **Start with Claude adapter** - Prove abstraction doesn't break existing functionality

---

## 12. Open Questions

### 12.1 Unknowns Requiring Clarification

| Question | Impact | Resolution Path |
|----------|--------|-----------------|
| Does Copilot support skill scripts? | May need to convert Python skills to different format | Test in Copilot environment |
| How does Copilot handle large context? | May affect specialization loading | Benchmark context limits |
| Can Copilot handoffs preserve state? | May need additional state serialization | Test state transfer |
| What's Copilot's equivalent of MCP? | May need different tool integration | Research Copilot tool API |

### 12.2 Blockers Requiring Resolution

| Blocker | Required Action | Owner |
|---------|-----------------|-------|
| Copilot skill path validation | Test skill discovery in real Copilot env | Developer |
| `#runSubagent` behavior | Verify subagent context isolation | Developer |
| Handoff button integration | Test orchestrator-to-agent handoffs | Developer |
| Response parsing | Validate CRP JSON works in Copilot | Developer |

### 12.3 Future Considerations

1. **Cursor Support** - Same abstraction could support Cursor IDE
2. **Windsurf Support** - Codeium's agent platform
3. **Local LLM Support** - Ollama/LMStudio integration
4. **API-First Mode** - BAZINGA as a service

---

## References

- [Copilot Deep Dive](./copilot-agents-skills-implementation-deep-dive.md)
- [BAZINGA Architecture](.claude/CLAUDE.md)
- [Workflow Transitions](../workflow/transitions.json)
- [Agent Markers](../workflow/agent-markers.json)
- [Model Selection](../bazinga/model_selection.json)
