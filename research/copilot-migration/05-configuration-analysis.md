# BAZINGA Configuration System Migration Analysis: Claude Code to GitHub Copilot

**Date:** 2026-01-23
**Status:** Draft
**Author:** Backend System Architect
**Scope:** Configuration System (`bazinga/*.json`) Migration Strategy

---

## Executive Summary

This document analyzes the BAZINGA configuration system for migration to GitHub Copilot. BAZINGA uses three JSON configuration files (`model_selection.json`, `skills_config.json`, `challenge_levels.json`) that control agent behavior, skill availability, and QA progression. Copilot lacks an equivalent native configuration system, requiring careful mapping to agent frontmatter, VS Code settings, and potentially MCP server configuration.

**Key Finding:** A hybrid approach (Option B) is recommended, maintaining shared JSON configuration files for both platforms with a thin abstraction layer to handle platform-specific loading semantics. This preserves BAZINGA's sophisticated configuration capabilities while enabling dual-platform support.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Copilot Mapping](#2-copilot-mapping)
3. [Migration Strategy](#3-migration-strategy)
4. [Dual-Platform Support](#4-dual-platform-support)
5. [Implementation Plan](#5-implementation-plan)
6. [Open Questions](#6-open-questions)

---

## 1. Current State Analysis

### 1.1 Configuration File Inventory

BAZINGA maintains three JSON configuration files in the `bazinga/` directory:

| File | Version | Purpose | Size |
|------|---------|---------|------|
| `model_selection.json` | v1.3.0 | Agent model assignments, escalation rules, task routing | ~100 lines |
| `skills_config.json` | - | Skill availability per agent, specialization settings, token budgets | ~85 lines |
| `challenge_levels.json` | v1.0.0 | QA 5-level test progression, escalation triggers | ~65 lines |

### 1.2 model_selection.json - Agent Model Assignment

**Schema Structure:**

```json
{
  "agents": {
    "<agent_name>": {
      "model": "haiku|sonnet|opus",
      "rationale": "Human-readable explanation"
    }
  },
  "escalation_rules": {
    "<rule_name>": {
      "triggers": ["condition1", "condition2"],
      "description": "When to escalate"
    }
  },
  "task_type_routing": {
    "<task_type>": {
      "agent": "<agent_name>",
      "model": "from_complexity_score|explicit_model",
      "markers": ["keyword1", "keyword2"],
      "matching": "case-insensitive",
      "flags": { "security_sensitive": true },
      "description": "What this routes"
    }
  },
  "_metadata": {
    "version": "1.3.0",
    "description": "...",
    "last_updated": "YYYY-MM-DD",
    "notes": ["note1", "note2"]
  }
}
```

**Current Agent Assignments:**

| Agent | Model | Rationale |
|-------|-------|-----------|
| developer | sonnet | Balanced capability for implementation tasks |
| senior_software_engineer | opus | Escalation - handles complex failures |
| qa_expert | sonnet | Balanced for test generation/validation |
| tech_lead | opus | Critical architectural decisions |
| project_manager | opus | Strategic planning, final quality gate |
| investigator | opus | Complex debugging, root cause analysis |
| requirements_engineer | opus | Requirements analysis, codebase discovery |
| validator | sonnet | Independent BAZINGA verification |
| orchestrator | sonnet | Coordination and routing |
| tech_stack_scout | sonnet | Project context detection |

**Escalation Rules:**

| Rule | Triggers | Effect |
|------|----------|--------|
| developer_to_sse | `revision_count >= 1`, `challenge_level_3_fail`, `challenge_level_4_fail` | Escalate to Senior Software Engineer |
| sse_to_tech_lead | `sse_revision >= 2`, `architectural_concern` | Escalate to Tech Lead |

**Task Type Routing:**

| Task Type | Agent | Markers | Description |
|-----------|-------|---------|-------------|
| research | requirements_engineer | `[R]`, `research`, `evaluate`, `select`, `compare`, `design`, `architecture` | Research and architecture tasks |
| implementation | developer | (default) | Code implementation |
| security | senior_software_engineer | `auth`, `authentication`, `authorization`, `security`, `crypto`, etc. | Security-sensitive tasks |

### 1.3 skills_config.json - Skill Availability

**Schema Structure:**

```json
{
  "specializations": {
    "enabled": true,
    "mode": "advisory",
    "token_budgets": {
      "haiku": { "soft": 600, "hard": 900 },
      "sonnet": { "soft": 1200, "hard": 1800 },
      "opus": { "soft": 1600, "hard": 2400 }
    },
    "include_code_examples": true,
    "include_checklist": true,
    "enabled_agents": ["developer", "senior_software_engineer", "qa_expert", "tech_lead", "requirements_engineer", "investigator"]
  },
  "<agent_name>": {
    "<skill_name>": "mandatory|optional|disabled"
  },
  "context_engineering": {
    "enable_context_assembler": true,
    "enable_fts5": false,
    "retrieval_limits": {
      "<agent_name>": <max_packages>
    },
    "redaction_mode": "pattern_only",
    "token_safety_margin": 0.15
  },
  "_metadata": { ... }
}
```

**Current Skill Assignments:**

| Agent | Mandatory Skills | Optional Skills |
|-------|-----------------|-----------------|
| developer | lint-check | codebase-analysis, test-pattern-analysis, api-contract-validation, db-migration-check |
| senior_software_engineer | lint-check, codebase-analysis, test-pattern-analysis | api-contract-validation, db-migration-check, security-scan |
| tech_lead | security-scan, lint-check, test-coverage | codebase-analysis, pattern-miner, test-pattern-analysis |
| qa_expert | - | pattern-miner, quality-dashboard |
| pm | - | velocity-tracker |
| investigator | codebase-analysis, pattern-miner | test-pattern-analysis, security-scan |

**Token Budgets per Model:**

| Model | Soft Limit | Hard Limit |
|-------|------------|------------|
| haiku | 600 | 900 |
| sonnet | 1200 | 1800 |
| opus | 1600 | 2400 |

### 1.4 challenge_levels.json - QA Test Progression

**Schema Structure:**

```json
{
  "levels": {
    "<level_number>": {
      "name": "Level Name",
      "description": "What this level tests",
      "qa_focus": ["focus1", "focus2"],
      "developer_scope": "haiku|senior_software_engineer",
      "escalation_on_fail": true|false
    }
  },
  "progression": {
    "default_start": 1,
    "max_level": 5,
    "pass_to_advance": true,
    "fail_behavior": {
      "levels_1_2": "retry_with_feedback",
      "levels_3_4_5": "escalate_if_fail"
    }
  },
  "routing": {
    "level_1_2_pass": "advance_level",
    "level_1_2_fail": "developer_retry",
    "level_3_4_5_pass": "advance_level",
    "level_3_4_5_fail": "escalate_to_senior_software_engineer"
  },
  "_metadata": { ... }
}
```

**Challenge Level Definitions:**

| Level | Name | QA Focus | Escalation |
|-------|------|----------|------------|
| 1 | Boundary Probing | null_values, empty_collections, max_min_values, type_boundaries | No |
| 2 | Mutation Analysis | operator_mutations, condition_inversions, return_value_changes | No |
| 3 | Behavioral Contracts | precondition_violations, postcondition_checks, invariant_preservation | Yes |
| 4 | Security Adversary | injection_attacks, auth_bypass, privilege_escalation, data_exposure | Yes |
| 5 | Production Chaos | network_failures, resource_exhaustion, race_conditions, cascading_failures | Yes |

### 1.5 How Configurations Are Loaded

**Loading Mechanism:**

```
+-------------------+     +-------------------+     +-------------------+
| Session Start     | --> | workflow_router.py| --> | Cached in memory  |
| (Orchestrator)    |     | load_model_config |     | MODEL_CONFIG dict |
+-------------------+     +-------------------+     +-------------------+
         |
         v
+-------------------+
| Read JSON files   |
| from bazinga/     |
+-------------------+
```

**workflow_router.py Implementation:**

```python
MODEL_CONFIG_PATH = "bazinga/model_selection.json"
MODEL_CONFIG = None  # Global cache

def load_model_config():
    """Load model config from JSON file. Returns (config, error) tuple."""
    if not Path(MODEL_CONFIG_PATH).exists():
        return None, f"Model config not found: {MODEL_CONFIG_PATH}"

    try:
        with open(MODEL_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {MODEL_CONFIG_PATH}: {e}"

    # Extract agent -> model mapping
    config = {}
    for agent_name, agent_data in data.get("agents", {}).items():
        if isinstance(agent_data, dict) and "model" in agent_data:
            config[agent_name] = agent_data["model"]

    return config, None
```

**Key Loading Characteristics:**

| Characteristic | Current Behavior |
|----------------|------------------|
| Load timing | Once at session start |
| Caching | Global variable (not DB) |
| Hot reload | Not supported (requires new session) |
| Validation | Basic JSON parsing only |
| Error handling | Graceful fallback with error messages |

### 1.6 Configuration Consumers

| Consumer | Config Files Used | Usage Pattern |
|----------|-------------------|---------------|
| Orchestrator | model_selection.json | Read at spawn time for model selection |
| workflow-router skill | model_selection.json | Routing decisions, escalation checks |
| prompt-builder skill | skills_config.json | Token budgets, specialization settings |
| specialization-loader skill | skills_config.json | Agent-specific template loading |
| QA Expert agent | challenge_levels.json | Test level progression |
| Tech Lead agent | skills_config.json | Mandatory skill execution |

### 1.7 Runtime Configuration Changes

**Current Capabilities:**

| Change Type | Supported? | Mechanism |
|-------------|------------|-----------|
| Change agent model | Yes | Edit JSON, new session |
| Enable/disable skill | Yes | Edit JSON, new session |
| Adjust token budgets | Yes | Edit JSON, new session |
| Hot reload mid-session | No | Requires restart |
| Per-request overrides | No | Not implemented |

---

## 2. Copilot Mapping

### 2.1 Copilot Configuration Mechanisms

GitHub Copilot provides several configuration mechanisms, none directly equivalent to BAZINGA's JSON configs:

| Mechanism | Location | Scope | Limitations |
|-----------|----------|-------|-------------|
| Agent frontmatter (`.agent.md`) | `.github/agents/*.agent.md` | Per-agent | No `model` field, limited schema |
| VS Code settings | `.vscode/settings.json` | Workspace | Chat settings only |
| MCP server config | `mcp.json` | Extension | Tool definitions only |
| Skillset definitions | External API | Organization | Max 5 skills per skillset |

### 2.2 Agent Frontmatter Mapping

**What CAN be in .agent.md files:**

```yaml
---
name: developer
description: Implementation specialist that writes code...
tools:
  - read
  - edit
  - terminal
  - github/*
handoffs:
  - label: "Send to QA"
    agent: "qa_expert"
    prompt: "Test this implementation"
    send: false
---
```

**Available Fields:**

| Field | Purpose | BAZINGA Equivalent |
|-------|---------|-------------------|
| `name` | Agent identifier | `name` in frontmatter |
| `description` | When to invoke (auto-routing) | `description` in frontmatter |
| `tools` | Allowed tool access | Implicit in agent body |
| `handoffs` | Transition buttons | workflow-router routing |

**What CANNOT be in .agent.md:**

| Missing Feature | BAZINGA Equivalent | Impact |
|-----------------|-------------------|--------|
| `model` field | `model_selection.json` | Cannot control model per agent |
| Skill availability | `skills_config.json` | No mandatory/optional/disabled |
| Token budgets | `skills_config.json` | No per-model limits |
| Escalation rules | `model_selection.json` | Must encode in agent body |
| Challenge levels | `challenge_levels.json` | Must encode in agent body |

### 2.3 VS Code Settings Mapping

**Relevant settings.json options:**

```json
{
  // Chat-level settings (not agent-specific)
  "chat.tools.terminal.autoApprove": {
    "allowed": ["npm test", "git status"],
    "denied": ["rm -rf", "sudo *"]
  },
  "chat.tools.editFiles.autoApprove": {
    "src/**/*.ts": true,
    "node_modules/**": false
  },

  // Copilot general settings
  "github.copilot.advanced": {
    "inlineSuggestCount": 3
  }
}
```

**Mapping Potential:**

| BAZINGA Config | VS Code Setting Candidate | Feasibility |
|----------------|---------------------------|-------------|
| Model selection | None (Copilot controls model) | Not possible |
| Skill availability | Custom settings extension | Requires extension |
| Token budgets | None | Not possible |
| Tool permissions | `chat.tools.*.autoApprove` | Partial match |
| Challenge levels | Custom settings | Requires extension |

### 2.4 MCP Server Configuration

**mcp.json structure:**

```json
{
  "servers": {
    "bazinga-config": {
      "type": "stdio",
      "command": "python",
      "args": ["bazinga/mcp/config_server.py"]
    }
  }
}
```

**MCP Potential for Configuration:**

| Use Case | MCP Approach | Complexity |
|----------|--------------|------------|
| Expose model_selection.json | Tool: `get_agent_model(agent_name)` | Low |
| Expose skills_config.json | Tool: `get_agent_skills(agent_name)` | Low |
| Expose challenge_levels.json | Tool: `get_challenge_level(level)` | Low |
| Runtime updates | Tool: `update_config(key, value)` | Medium |

### 2.5 Configuration Mapping Matrix

| BAZINGA Config | Copilot Option | Recommended Approach |
|----------------|----------------|---------------------|
| Agent model assignment | None native | Keep JSON, ignore in Copilot |
| Escalation rules | Encode in agent body | Embed in agent instructions |
| Task type routing | Disambiguation in frontmatter | Use `description` for auto-routing |
| Skill availability | Custom extension or MCP | Keep JSON, access via MCP tool |
| Token budgets | Skill instructions | Embed in skill SKILL.md |
| Challenge levels | Agent instructions | Embed in QA Expert agent |

---

## 3. Migration Strategy

### 3.1 Option A: Embed in Agent Files

**Description:** Move all configuration into agent `.agent.md` files and SKILL.md files.

**Implementation:**

```yaml
# .github/agents/developer.agent.md
---
name: developer
description: |
  Implementation specialist for coding tasks.
  MANDATORY SKILLS: lint-check
  OPTIONAL SKILLS: codebase-analysis, test-pattern-analysis
  ESCALATION: After 1 failure, route to Senior Software Engineer
---

# Developer Agent

## Skill Configuration
- **MANDATORY**: lint-check (always run before completion)
- **OPTIONAL**: codebase-analysis, test-pattern-analysis

## Escalation Rules
If your implementation fails QA or review:
- First failure: You can retry
- Second failure: Request escalation to Senior Software Engineer
```

**Pros:**
- Self-contained agents
- No external dependencies
- Works offline

**Cons:**
- Duplicate configuration across agents
- No centralized management
- Changes require editing multiple files
- No programmatic access
- Model selection impossible (Copilot controls)

**Verdict:** Not recommended for BAZINGA's complexity.

### 3.2 Option B: Keep JSON Files (Shared) - RECOMMENDED

**Description:** Maintain `bazinga/*.json` files as configuration source, access via abstraction layer.

**Implementation Architecture:**

```
+---------------------------+
| Configuration Files       |
| bazinga/                  |
| ├── model_selection.json  |  <-- Shared source of truth
| ├── skills_config.json    |
| └── challenge_levels.json |
+---------------------------+
            |
            v
+---------------------------+
| Configuration Provider    |
| (Platform-Agnostic)       |
+---------------------------+
            |
    +-------+-------+
    |               |
    v               v
+----------+   +----------+
| Claude   |   | Copilot  |
| Adapter  |   | Adapter  |
+----------+   +----------+
```

**Claude Code Implementation:**

```python
# bazinga/config/claude_provider.py
class ClaudeConfigProvider:
    def __init__(self, config_dir: str = "bazinga"):
        self.config_dir = config_dir
        self._cache = {}

    def get_agent_model(self, agent_name: str) -> str:
        """Get model assignment for agent."""
        config = self._load("model_selection.json")
        return config.get("agents", {}).get(agent_name, {}).get("model", "sonnet")

    def get_agent_skills(self, agent_name: str) -> dict:
        """Get skill configuration for agent."""
        config = self._load("skills_config.json")
        return config.get(agent_name, {})

    def get_challenge_level(self, level: int) -> dict:
        """Get QA challenge level definition."""
        config = self._load("challenge_levels.json")
        return config.get("levels", {}).get(str(level), {})
```

**Copilot Implementation:**

```python
# bazinga/config/copilot_provider.py
class CopilotConfigProvider:
    def __init__(self, config_dir: str = "bazinga"):
        self.config_dir = config_dir
        self._cache = {}

    def get_agent_model(self, agent_name: str) -> str:
        """Get model - Copilot ignores this, returns for compatibility."""
        # Copilot controls model selection, but we return for logging
        config = self._load("model_selection.json")
        return config.get("agents", {}).get(agent_name, {}).get("model", "default")

    def get_agent_skills(self, agent_name: str) -> dict:
        """Get skill configuration - same as Claude."""
        config = self._load("skills_config.json")
        return config.get(agent_name, {})

    def get_challenge_level(self, level: int) -> dict:
        """Get QA challenge level - same as Claude."""
        config = self._load("challenge_levels.json")
        return config.get("levels", {}).get(str(level), {})
```

**Pros:**
- Single source of truth for configuration
- Works on both platforms
- Easy to modify (edit JSON)
- Supports programmatic access
- Preserves all BAZINGA features

**Cons:**
- Model selection ignored by Copilot
- Requires config access in agent context
- Slight complexity increase

**Verdict:** RECOMMENDED - Best balance of capability and maintainability.

### 3.3 Option C: VS Code Settings Integration

**Description:** Move configuration to `.vscode/settings.json` with custom schema.

**Implementation:**

```json
// .vscode/settings.json
{
  "bazinga.agentModels": {
    "developer": "sonnet",
    "senior_software_engineer": "opus",
    "qa_expert": "sonnet"
  },
  "bazinga.skillConfig": {
    "developer": {
      "lint-check": "mandatory",
      "codebase-analysis": "optional"
    }
  },
  "bazinga.challengeLevels": {
    "1": { "name": "Boundary Probing", "escalation": false },
    "2": { "name": "Mutation Analysis", "escalation": false }
  }
}
```

**Pros:**
- Native VS Code integration
- IDE-aware (autocomplete, validation)
- User-level overrides possible

**Cons:**
- Claude Code doesn't read VS Code settings
- Requires extension for validation
- Different file locations per platform
- No schema enforcement without extension

**Verdict:** Not recommended due to platform incompatibility.

### 3.4 Strategy Comparison Matrix

| Criteria | Option A: Embed | Option B: Shared JSON | Option C: VS Code |
|----------|-----------------|----------------------|-------------------|
| Single source of truth | No | **Yes** | No |
| Works on Claude Code | Yes | **Yes** | No |
| Works on Copilot | Yes | **Yes** | Partial |
| Centralized management | No | **Yes** | Partial |
| Model selection support | No | **Yes** (Claude only) | No |
| Maintenance effort | High | **Low** | Medium |
| Programmatic access | No | **Yes** | Requires extension |

---

## 4. Dual-Platform Support

### 4.1 Unified Configuration Format

**Proposed shared schema:**

```json
{
  "$schema": "bazinga/schemas/config.schema.json",
  "version": "2.0.0",
  "platform_overrides": {
    "claude_code": {
      "model_selection_enabled": true
    },
    "github_copilot": {
      "model_selection_enabled": false,
      "use_handoffs_for_routing": true
    }
  },
  "agents": {
    "developer": {
      "model": "sonnet",
      "skills": {
        "lint-check": "mandatory"
      },
      "escalation": {
        "after_failures": 1,
        "target": "senior_software_engineer"
      }
    }
  }
}
```

### 4.2 Platform-Specific Overrides

**Override mechanism:**

```python
# bazinga/config/provider.py
class ConfigProvider:
    def __init__(self, platform: str):
        self.platform = platform  # "claude_code" or "github_copilot"
        self.base_config = self._load_base()
        self.overrides = self.base_config.get("platform_overrides", {}).get(platform, {})

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled for this platform."""
        # Check override first, then base
        if feature in self.overrides:
            return self.overrides[feature]
        return self.base_config.get("features", {}).get(feature, True)

    def get_agent_model(self, agent_name: str) -> str:
        """Get model - respects platform capabilities."""
        if not self.overrides.get("model_selection_enabled", True):
            return "platform_controlled"
        return self.base_config["agents"][agent_name]["model"]
```

### 4.3 Runtime Detection

**Platform detection:**

```python
# bazinga/config/detection.py
import os

def detect_platform() -> str:
    """Detect which AI platform we're running on."""

    # Check for Claude Code indicators
    if os.environ.get("CLAUDE_CODE_SESSION"):
        return "claude_code"

    # Check for VS Code/Copilot indicators
    if os.environ.get("VSCODE_PID"):
        return "github_copilot"

    # Check for directory structure
    if os.path.exists(".github/agents"):
        return "github_copilot"
    if os.path.exists(".claude/agents"):
        return "claude_code"

    # Default to Claude Code (BAZINGA's primary platform)
    return "claude_code"
```

### 4.4 Configuration Loading by Platform

**Claude Code Loading:**

```python
# In orchestrator/workflow-router
from bazinga.config import ConfigProvider

provider = ConfigProvider(platform="claude_code")
model = provider.get_agent_model("developer")  # Returns "sonnet"
skills = provider.get_agent_skills("developer")  # Returns skill dict
```

**Copilot Loading (via MCP or Agent Body):**

```python
# In MCP server or skill script
from bazinga.config import ConfigProvider

provider = ConfigProvider(platform="github_copilot")
model = provider.get_agent_model("developer")  # Returns "platform_controlled"
skills = provider.get_agent_skills("developer")  # Same as Claude
```

### 4.5 Feature Parity Matrix

| Feature | Claude Code | Copilot | Parity Strategy |
|---------|-------------|---------|-----------------|
| Model selection | Full control | Platform controls | Ignore on Copilot |
| Skill mandatory/optional | Via orchestrator | Via agent instructions | Embed in agent body |
| Token budgets | Enforced | Advisory only | Log but don't enforce |
| Escalation rules | workflow-router | Handoffs | Map to handoff buttons |
| Challenge levels | QA agent reads | QA agent reads | Same implementation |
| Task routing | workflow-router | Disambiguation | Use frontmatter description |

---

## 5. Implementation Plan

### 5.1 Phase 1: Abstraction Layer (Week 1)

**Tasks:**

| Task | Priority | Effort | Output |
|------|----------|--------|--------|
| Create `ConfigProvider` interface | High | 2h | `bazinga/config/provider.py` |
| Implement Claude adapter | High | 2h | `bazinga/config/claude_provider.py` |
| Implement Copilot adapter | High | 3h | `bazinga/config/copilot_provider.py` |
| Add platform detection | Medium | 1h | `bazinga/config/detection.py` |
| Update workflow-router | High | 2h | Use ConfigProvider |
| Add unit tests | Medium | 3h | `tests/test_config_provider.py` |

**Deliverables:**
- Platform-agnostic configuration access
- Backward-compatible with existing JSON files
- Tests covering both platforms

### 5.2 Phase 2: Copilot Agent Generation (Week 2)

**Tasks:**

| Task | Priority | Effort | Output |
|------|----------|--------|--------|
| Create agent generator script | High | 4h | `scripts/generate_copilot_agents.py` |
| Map escalation to handoffs | High | 3h | Handoff configs in frontmatter |
| Embed skill config in agents | Medium | 2h | Skill sections in agent body |
| Generate `.github/agents/*.agent.md` | High | 2h | Generated files |
| Add generation to build pipeline | Medium | 1h | CI/CD integration |

**Agent Generation Logic:**

```python
# scripts/generate_copilot_agents.py
def generate_copilot_agent(agent_name: str, base_agent_path: str, config: dict) -> str:
    """Generate Copilot-compatible agent from BAZINGA agent."""
    base_content = read_file(base_agent_path)

    # Extract and transform frontmatter
    frontmatter = {
        "name": agent_name,
        "description": extract_description(base_content),
        "tools": ["read", "edit", "terminal"],
        "handoffs": generate_handoffs(agent_name, config)
    }

    # Embed configuration in body
    body = base_content
    body = inject_skill_config(body, config["skills"].get(agent_name, {}))
    body = inject_escalation_rules(body, config["escalation_rules"])

    return format_agent_md(frontmatter, body)
```

### 5.3 Phase 3: MCP Configuration Server (Week 3)

**Tasks:**

| Task | Priority | Effort | Output |
|------|----------|--------|--------|
| Create MCP server skeleton | High | 2h | `bazinga/mcp/config_server.py` |
| Implement `get_config` tool | High | 2h | Read config tool |
| Implement `get_agent_model` tool | Medium | 1h | Model lookup tool |
| Implement `get_skill_status` tool | Medium | 1h | Skill status tool |
| Add to mcp.json | High | 1h | Server registration |
| Test with Copilot | High | 3h | End-to-end validation |

**MCP Server Tools:**

```python
# bazinga/mcp/config_server.py
TOOLS = [
    {
        "name": "bazinga_get_config",
        "description": "Get BAZINGA configuration value",
        "parameters": {
            "config_file": {"type": "string", "enum": ["model_selection", "skills_config", "challenge_levels"]},
            "key_path": {"type": "string", "description": "Dot-notation path, e.g., 'agents.developer.model'"}
        }
    },
    {
        "name": "bazinga_get_agent_skills",
        "description": "Get skill configuration for an agent",
        "parameters": {
            "agent_name": {"type": "string", "description": "Agent identifier"}
        }
    }
]
```

### 5.4 Phase 4: Validation and Documentation (Week 4)

**Tasks:**

| Task | Priority | Effort | Output |
|------|----------|--------|--------|
| Integration testing | High | 4h | Test suite |
| Document configuration system | High | 3h | `docs/configuration.md` |
| Update CLAUDE.md | Medium | 1h | Configuration section |
| Create migration guide | Medium | 2h | `docs/copilot-migration.md` |
| Performance testing | Low | 2h | Benchmark results |

---

## 6. Open Questions

### 6.1 Model Selection on Copilot

**Question:** How do we handle model selection when Copilot doesn't support it?

**Options:**
1. **Ignore** - Accept that Copilot uses one model for everything
2. **Log only** - Record intended model for debugging
3. **Handoffs** - Use different agents for different "tiers" (but same underlying model)

**Recommendation:** Option 2 (Log only) - Maintain configuration for Claude Code, log discrepancy on Copilot.

### 6.2 Mandatory Skill Enforcement

**Question:** How do we enforce mandatory skills on Copilot without orchestrator control?

**Options:**
1. **Agent instructions** - Tell agent "you MUST run lint-check before completion"
2. **Handoff workflow** - Create skill-running agents in the handoff chain
3. **Trust agent** - Rely on agent compliance (current BAZINGA approach)

**Recommendation:** Option 1 - Embed mandatory skill requirements in agent instructions.

### 6.3 Challenge Level Progression

**Question:** How does QA Expert track challenge level state without database?

**Options:**
1. **Conversation context** - Track level in ongoing conversation
2. **File-based state** - Write to `bazinga/state/qa_progress.json`
3. **Handoff metadata** - Pass level in handoff prompt

**Recommendation:** Option 3 - Pass challenge level in handoff prompts between agents.

### 6.4 Configuration Hot Reload

**Question:** Should we support mid-session configuration changes?

**Current:** No - requires new session
**Options:**
1. **Keep current** - New session for config changes
2. **Add reload command** - Slash command to reload configs
3. **Watch for changes** - Auto-reload on file change

**Recommendation:** Option 1 for initial migration, Option 2 as future enhancement.

---

## 7. Critical Analysis

### 7.1 Pros of Recommended Approach (Option B)

**Technical:**
- Single source of truth for both platforms
- Minimal code duplication
- Preserves all BAZINGA functionality on Claude Code
- Graceful degradation on Copilot

**Operational:**
- Familiar JSON-based configuration
- No schema migration required
- Easy rollback if issues arise

### 7.2 Cons and Mitigations

| Con | Severity | Mitigation |
|-----|----------|------------|
| Model selection ignored on Copilot | Medium | Accept limitation, log discrepancy |
| Abstraction layer complexity | Low | Keep interface minimal |
| Two code paths to maintain | Medium | Comprehensive test coverage |
| Configuration access in Copilot | Medium | MCP server provides access |

### 7.3 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Config loading fails on Copilot | Low | High | Fallback to defaults |
| Platform detection incorrect | Low | Medium | Multiple detection methods |
| MCP server unavailable | Medium | Medium | Embed critical configs in agents |
| Configuration drift between platforms | Medium | Medium | CI/CD validation |

### 7.4 Verdict

**Option B (Shared JSON Files)** is the recommended approach because:

1. **Preserves BAZINGA's full capability** on Claude Code
2. **Minimal changes** to existing configuration files
3. **Clean abstraction** with platform-specific adapters
4. **Future-proof** - Can add more platforms with new adapters
5. **Graceful degradation** - Works even if MCP unavailable

The main tradeoff is accepting that **model selection cannot work on Copilot** - this is a fundamental platform limitation that no migration strategy can overcome.

---

## References

- [Copilot Deep Dive](./copilot-agents-skills-implementation-deep-dive.md)
- [Agent System Analysis](./01-agent-system-analysis.md)
- [Abstraction Layer Analysis](./10-abstraction-layer-analysis.md)
- [model_selection.json](../../bazinga/model_selection.json)
- [skills_config.json](../../bazinga/skills_config.json)
- [challenge_levels.json](../../bazinga/challenge_levels.json)
- [workflow_router.py](../../.claude/skills/workflow-router/scripts/workflow_router.py)
