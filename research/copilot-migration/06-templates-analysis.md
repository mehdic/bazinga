# BAZINGA Templates System: Copilot Migration Analysis

**Date:** 2026-01-23
**Context:** Analysis of BAZINGA's template system for dual-platform support (Claude Code + GitHub Copilot)
**Status:** Draft
**Related Documents:**
- `research/copilot-agents-skills-implementation-deep-dive.md` - Copilot architecture reference
- `research/copilot-migration/01-agent-system-analysis.md` - Agent system analysis
- `research/copilot-migration/02-skills-system-analysis.md` - Skills system analysis

---

## Executive Summary

This document analyzes BAZINGA's extensive template system (95 files) for migration to GitHub Copilot while maintaining Claude Code compatibility. The templates serve three critical functions:

1. **Agent Workflow Templates** (23 files) - Define agent behavior, routing, and output formats
2. **Orchestration Templates** (4 files) - Phase execution guides for simple/parallel modes
3. **Specialization Templates** (72 files) - Technology-specific guidance with version guards

Key challenges include:
- Copilot has no native template system (skills reference resources via relative paths)
- Version guards require custom processing logic
- Token budgets differ between platforms
- Template loading must be deterministic for both platforms

**Recommended approach:** Option C (Copilot-native adaptation) with an abstraction layer that handles template loading for both platforms through the same Python scripts.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Copilot Mapping](#2-copilot-mapping)
3. [Migration Strategy Options](#3-migration-strategy-options)
4. [Dual-Platform Support Design](#4-dual-platform-support-design)
5. [Implementation Plan](#5-implementation-plan)
6. [Risk Assessment](#6-risk-assessment)

---

## 1. Current State Analysis

### 1.1 Template Inventory

**Total Templates:** 95 files across three categories

#### Category A: Agent Workflow Templates (23 files)

| File | Purpose | Size (approx) | Agents Using |
|------|---------|---------------|--------------|
| `developer_speckit.md` | Developer task framework | ~400 lines | Developer, SSE |
| `qa_speckit.md` | QA testing framework (spec-kit mode) | ~214 lines | QA Expert |
| `tech_lead_speckit.md` | Review framework (spec-kit mode) | ~254 lines | Tech Lead |
| `pm_speckit.md` | PM spec-kit integration | ~518 lines | Project Manager |
| `pm_planning_steps.md` | Planning methodology | ~300 lines | Project Manager |
| `pm_task_classification.md` | Task categorization | ~200 lines | Project Manager |
| `pm_output_format.md` | PM output structure | ~150 lines | Project Manager |
| `pm_routing.md` | Agent routing decisions | ~250 lines | Project Manager |
| `pm_autonomy.md` | PM decision autonomy | ~200 lines | Project Manager |
| `pm_bazinga_validation.md` | Completion validation | ~150 lines | Project Manager |
| `message_templates.md` | Output capsule formats | ~200 lines | All agents |
| `response_parsing.md` | Response extraction rules | ~300 lines | Orchestrator |
| `prompt_building.md` | Prompt composition rules | ~250 lines | prompt-builder skill |
| `batch_processing.md` | Parallel batch handling | ~150 lines | Orchestrator |
| `completion_report.md` | Session completion format | ~100 lines | PM, Orchestrator |
| `investigation_loop.md` | Investigator workflow | ~200 lines | Investigator |
| `logging_pattern.md` | DB logging patterns | ~100 lines | All agents |
| `merge_workflow.md` | Git merge procedures | ~150 lines | Developer |
| `shutdown_protocol.md` | Graceful shutdown | ~100 lines | Orchestrator |

#### Category B: Orchestration Templates (4 files)

| File | Purpose | Size (approx) |
|------|---------|---------------|
| `orchestrator/phase_simple.md` | Simple mode execution guide | ~995 lines |
| `orchestrator/phase_parallel.md` | Parallel mode execution guide | ~730 lines |
| `orchestrator/clarification_flow.md` | User clarification handling | ~150 lines |
| `orchestrator/scope_validation.md` | Scope validation rules | ~100 lines |

#### Category C: Specialization Templates (72 files)

Organized in 11 categories:

| Category | Files | Examples |
|----------|-------|----------|
| `01-languages/` | 15 | python.md, typescript.md, java.md, go.md, rust.md |
| `02-frameworks-frontend/` | 8 | react.md, vue.md, angular.md, nextjs.md |
| `03-frameworks-backend/` | 10 | fastapi.md, django.md, express.md, spring-boot.md |
| `04-mobile-desktop/` | 4 | flutter.md, react-native.md, ios-swiftui.md |
| `05-databases/` | 7 | postgresql.md, mongodb.md, redis.md, prisma-orm.md |
| `06-infrastructure/` | 5 | docker.md, kubernetes.md, terraform.md |
| `07-messaging-apis/` | 4 | graphql.md, grpc.md, kafka-rabbitmq.md |
| `08-testing/` | 4 | testing-patterns.md, playwright-cypress.md, qa-strategies.md |
| `09-data-ai/` | 3 | machine-learning.md, llm-langchain.md |
| `10-security/` | 3 | jwt-oauth.md, auth-patterns.md, security-auditing.md |
| `11-domains/` | 8 | backend-api.md, microservices.md, code-review.md |
| `00-MASTER-INDEX.md` | 1 | Index and usage guide |

### 1.2 Template Loading Architecture

**Current loading flow:**

```
┌───────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                                │
│                                                                │
│  1. Writes params JSON to bazinga/prompts/{session}/params.json│
│  2. Invokes prompt-builder skill                              │
│  3. Reads generated prompt file                               │
│  4. Spawns agent with Task()                                  │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                 PROMPT-BUILDER (Python Script)                 │
│                                                                │
│  1. Reads params.json                                         │
│  2. Queries DB for specializations, context, error patterns   │
│  3. Reads agent template file (agents/*.md)                   │
│  4. Reads specialization templates (templates/specializations/)│
│  5. Applies version guards (parse project_context.json)       │
│  6. Applies token budgets (haiku=900, sonnet=1800, opus=2400) │
│  7. Composes final prompt                                     │
│  8. Writes to output file                                     │
│  9. Returns JSON with success status                          │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                    GENERATED PROMPT FILE                       │
│                                                                │
│  CONTEXT_BLOCK (from DB: context packages, prior reasoning)   │
│  +                                                            │
│  SPEC_BLOCK (from templates: version-filtered, token-budgeted)│
│  +                                                            │
│  TASK_BLOCK (session, group, requirements)                    │
│  +                                                            │
│  AGENT_TEMPLATE (from agents/*.md)                            │
└───────────────────────────────────────────────────────────────┘
```

### 1.3 Version Guards System

Templates use HTML comment markers for version-conditional content:

```markdown
<!-- version: react >= 18 -->
- **Server Components by default**: Only use `'use client'` when needed

<!-- version: react < 18 -->
- **Client-side rendering**: No Server Components; use data fetching libraries

<!-- version: react >= 19 -->
- **useActionState for forms**: Replaces useFormState with clearer semantics
```

**Supported operators:** `>=`, `>`, `<=`, `<`, `==`

**Version context sources:**
1. `bazinga/project_context.json` (primary)
2. Inline detection from `package.json`, `pyproject.toml`, `go.mod` (fallback)

**Guard token aliases (60+ total):**
- Languages: `python`, `py`, `python3`, `typescript`, `ts`, `java`, etc.
- Frameworks: `react`, `vue`, `angular`, `django`, `fastapi`, etc.
- Databases: `postgres`, `postgresql`, `pg`, `mongodb`, `mongo`, etc.

### 1.4 Specialization Composition

The `specialization-loader` skill composes technology-specific identity blocks:

**Input context:**
```
Session ID: bazinga_20251204_120000
Group ID: AUTH
Agent Type: developer
Model: haiku
Specialization Paths: [
  "01-languages/python.md",
  "03-frameworks-backend/fastapi.md",
  "11-domains/backend-api.md"
]
```

**Composed output:**
```markdown
## SPECIALIZATION GUIDANCE (Advisory)

For this session, your identity is enhanced:

**You are a Python 3.11 Backend API Developer specialized in FastAPI 0.100+.**

Your expertise includes:
- Python 3.11 features: pattern matching, ExceptionGroups, tomllib
- FastAPI patterns: dependency injection, Pydantic v2, async/await
- RESTful API design: proper status codes, pagination, error handling

### Patterns to Follow
- Type hints everywhere with strict mode
- Async handlers for I/O-bound operations
- Pydantic models for request/response validation

### Patterns to Avoid
- Sync database calls in async handlers
- Mutable default arguments
- Catching broad exceptions
```

### 1.5 Token Budget Enforcement

| Model | Soft Limit | Hard Limit | Context Allocation |
|-------|------------|------------|-------------------|
| haiku | 900 tokens | 1350 tokens | 35% (developer), 30% (SSE/QA) |
| sonnet | 1800 tokens | 2700 tokens | 40% (tech_lead) |
| opus | 2400 tokens | 3600 tokens | 35% (investigator) |

**Trimming strategy (when over budget):**
1. Trim "Code Patterns (Reference)" sections first
2. Trim detailed explanations, keep bullet points
3. Trim "Verification Checklist" last (highest value)
4. Stop adding templates if hard limit reached

---

## 2. Copilot Mapping

### 2.1 Copilot Resource Model

From `copilot-agents-skills-implementation-deep-dive.md`, Copilot uses a 3-level loading system:

```
┌────────────────────────────────────────────────────────────┐
│ LEVEL 1: DISCOVERY (Always Active)                         │
│                                                             │
│ Copilot reads YAML frontmatter ONLY:                       │
│   - name: "webapp-testing"                                 │
│   - description: "Tests web applications..."               │
└────────────────────────────────────────────────────────────┘
                           │
                    prompt matches
                           ▼
┌────────────────────────────────────────────────────────────┐
│ LEVEL 2: INSTRUCTIONS (On Demand)                          │
│                                                             │
│ Full SKILL.md body loads into context                      │
│ Supporting files NOT loaded yet                            │
└────────────────────────────────────────────────────────────┘
                           │
                    Copilot references file
                           ▼
┌────────────────────────────────────────────────────────────┐
│ LEVEL 3: RESOURCES (On Reference)                          │
│                                                             │
│ Individual files load when Copilot references them:        │
│   - [script](./helper.sh) → loads helper.sh               │
│   - [template](./main.json) → loads main.json             │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Template-to-Copilot Mapping Options

| BAZINGA Template Type | Copilot Equivalent | Notes |
|----------------------|-------------------|-------|
| Agent workflow | SKILL.md body | Loaded at Level 2 |
| Orchestration | SKILL.md + resources | References load at Level 3 |
| Specializations | Resource files | Must be referenced explicitly |

### 2.3 Key Differences

| Aspect | Claude Code | Copilot |
|--------|-------------|---------|
| Template loading | Deterministic via script | Semantic matching by LLM |
| Version guards | Custom parser (Python) | No native support |
| Token budgets | Explicit per-model limits | No native support |
| Template references | Programmatic file reading | Markdown link references |
| Composition | Python script composes | LLM decides what to include |

### 2.4 Version Guards in Copilot

**Challenge:** Copilot has no version guard system.

**Options:**
1. **Pre-process templates:** Generate version-specific variants at install time
2. **Runtime processing:** Keep Python script, call via MCP or inline
3. **LLM-based filtering:** Include all variants, let LLM choose (unreliable)

**Recommended:** Option 2 - Use same Python script via platform abstraction.

---

## 3. Migration Strategy Options

### 3.1 Option A: Bundle in Skills

**Approach:** Embed templates directly into skill SKILL.md files.

**Structure:**
```
.github/skills/
├── developer/
│   ├── SKILL.md         # Contains developer_speckit.md content
│   └── specializations/ # Contains relevant specialization content
├── qa-expert/
│   └── SKILL.md         # Contains qa_speckit.md content
└── orchestrator/
    ├── SKILL.md
    ├── phase_simple.md   # Referenced as resource
    └── phase_parallel.md
```

**Pros:**
- Self-contained skills
- Works with Copilot's 3-level loading
- No external dependencies

**Cons:**
- Duplicates content across skills
- Hard to maintain synchronization
- Large skill files exceed token limits
- Loses version guard functionality
- No token budget enforcement

**Verdict:** Not recommended due to maintenance burden and loss of functionality.

### 3.2 Option B: Keep as Shared Resources

**Approach:** Maintain templates in central location, reference from skills.

**Structure:**
```
.github/
├── skills/
│   ├── developer/
│   │   └── SKILL.md     # References ../templates/developer_speckit.md
│   └── qa-expert/
│       └── SKILL.md     # References ../templates/qa_speckit.md
└── templates/           # Shared templates (same as current)
    ├── developer_speckit.md
    ├── qa_speckit.md
    └── specializations/
```

**Pros:**
- Single source of truth
- Easier maintenance
- Familiar structure

**Cons:**
- Copilot loads resources on reference, not programmatically
- Cannot apply version guards at load time
- Cannot enforce token budgets
- Path resolution may be fragile

**Verdict:** Partially viable but loses key functionality.

### 3.3 Option C: Copilot-Native Adaptation (Recommended)

**Approach:** Use platform abstraction layer with shared Python processing.

**Structure:**
```
bazinga/
├── templates/              # SOURCE templates (unchanged)
│   ├── specializations/
│   ├── developer_speckit.md
│   └── ...
├── scripts/
│   └── template_loader.py  # Platform-agnostic template processing
└── ...

.github/skills/             # Copilot skills (reference shared logic)
├── prompt-builder/
│   ├── SKILL.md
│   └── scripts/
│       └── prompt_builder.py  # Symlink or wrapper
└── specialization-loader/
    ├── SKILL.md
    └── scripts/
        └── spec_loader.py     # Symlink or wrapper
```

**Key insight:** Both platforms can use the same Python script for:
1. Reading templates
2. Applying version guards
3. Enforcing token budgets
4. Composing prompts

**Execution flow:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PLATFORM DETECTION                        │
│                                                              │
│  IF .github/skills exists AND Copilot detected:             │
│    → Use Copilot paths (.github/skills/, .github/templates/)│
│  ELSE:                                                       │
│    → Use Claude paths (.claude/skills/, bazinga/templates/) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 TEMPLATE LOADER (Python)                     │
│                                                              │
│  Same logic for both platforms:                             │
│  1. Resolve template paths based on platform                │
│  2. Read project_context.json (same location)               │
│  3. Apply version guards                                    │
│  4. Apply token budgets                                     │
│  5. Compose prompt                                          │
│  6. Return/write result                                     │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Same templates work on both platforms
- Full version guard support
- Full token budget support
- Single maintenance point
- Deterministic behavior

**Cons:**
- Requires Python execution on Copilot (via Bash tool)
- More complex setup
- Skill must invoke script (not purely declarative)

**Verdict:** Recommended - preserves all functionality with minimal overhead.

---

## 4. Dual-Platform Support Design

### 4.1 Platform Abstraction Layer

**File:** `bazinga/scripts/template_loader.py`

```python
"""
Platform-agnostic template loading for BAZINGA.
Works with both Claude Code and GitHub Copilot.
"""

import os
from pathlib import Path
from enum import Enum

class Platform(Enum):
    CLAUDE_CODE = "claude"
    COPILOT = "copilot"

def detect_platform() -> Platform:
    """Detect which platform we're running on."""
    # Check for Copilot-specific markers
    if (Path(".github/skills").exists() and
        os.environ.get("GITHUB_COPILOT_AGENT")):
        return Platform.COPILOT
    return Platform.CLAUDE_CODE

def get_template_paths(platform: Platform) -> dict:
    """Return platform-specific paths."""
    if platform == Platform.COPILOT:
        return {
            "templates": Path(".github/templates"),
            "specializations": Path(".github/templates/specializations"),
            "agents": Path(".github/agents"),
            "skills": Path(".github/skills"),
            "context": Path("bazinga/project_context.json"),
        }
    else:  # CLAUDE_CODE
        return {
            "templates": Path("bazinga/templates"),
            "specializations": Path("bazinga/templates/specializations"),
            "agents": Path(".claude/agents"),
            "skills": Path(".claude/skills"),
            "context": Path("bazinga/project_context.json"),
        }
```

### 4.2 Template Path Resolution

**Cross-platform path mapping:**

| Template Type | Claude Code Path | Copilot Path |
|--------------|------------------|--------------|
| Agent workflows | `bazinga/templates/{name}.md` | `.github/templates/{name}.md` |
| Orchestration | `bazinga/templates/orchestrator/` | `.github/templates/orchestrator/` |
| Specializations | `bazinga/templates/specializations/` | `.github/templates/specializations/` |
| Project context | `bazinga/project_context.json` | `bazinga/project_context.json` |

**Note:** Project context stays in `bazinga/` for both platforms since it's session data, not configuration.

### 4.3 Version Guards Compatibility

The existing version guard parser in `prompt_builder.py` works for both platforms:

```python
def parse_version(version_str: str) -> tuple:
    """Parse version string into comparable tuple."""
    # Handles: "3.11", "18", "2.7", "16.8", etc.
    ...

def evaluate_version_guard(guard: str, context: dict) -> bool:
    """Evaluate version guard against project context."""
    # Handles: <!-- version: react >= 18 -->
    ...

def apply_version_guards(content: str, context: dict) -> str:
    """Filter content based on version guards."""
    ...
```

**No changes needed** - just ensure `project_context.json` is available.

### 4.4 Token Budget Compatibility

Token budgets are model-tier based, not platform-specific:

```python
TOKEN_BUDGETS = {
    "haiku": {"soft": 900, "hard": 1350},   # Fast tier
    "sonnet": {"soft": 1800, "hard": 2700}, # Balanced tier
    "opus": {"soft": 2400, "hard": 3600},   # Deep tier
}

# Copilot model mapping (approximate)
COPILOT_MODEL_MAPPING = {
    "gpt-4o-mini": "haiku",   # Fast tier
    "gpt-4o": "sonnet",       # Balanced tier
    "o1": "opus",             # Deep tier (if available)
}
```

### 4.5 Specialization Loader Adaptation

**Current specialization-loader skill** can work on both platforms with minor changes:

**Claude Code invocation:**
```python
Skill(command: "specialization-loader")
```

**Copilot invocation:**
```bash
# Via Bash tool within skill
python3 .github/skills/specialization-loader/scripts/spec_loader.py \
  --session-id "{session_id}" \
  --group-id "{group_id}" \
  --agent-type "developer" \
  --model "gpt-4o-mini" \
  --specializations '["01-languages/python.md", "03-frameworks-backend/fastapi.md"]'
```

### 4.6 Template Installation

**bazinga install** command additions:

```python
def install_for_copilot(project_root: Path):
    """Install templates for Copilot compatibility."""

    # Create Copilot directory structure
    (project_root / ".github/templates").mkdir(parents=True, exist_ok=True)
    (project_root / ".github/skills").mkdir(parents=True, exist_ok=True)
    (project_root / ".github/agents").mkdir(parents=True, exist_ok=True)

    # Copy templates to Copilot location
    shutil.copytree(
        PACKAGE_DATA / "templates",
        project_root / ".github/templates",
        dirs_exist_ok=True
    )

    # Copy Copilot-specific skills
    shutil.copytree(
        PACKAGE_DATA / "copilot-skills",
        project_root / ".github/skills",
        dirs_exist_ok=True
    )

    # Create copilot-instructions.md
    create_copilot_instructions(project_root)
```

---

## 5. Implementation Plan

### 5.1 Phase 1: Abstraction Layer (Week 1)

**Tasks:**

1. **Create platform detection module**
   - File: `bazinga/scripts/platform.py`
   - Detect Claude Code vs Copilot environment
   - Return platform-specific paths

2. **Refactor prompt_builder.py**
   - Import platform detection
   - Use platform-specific paths
   - Add Copilot model mapping

3. **Refactor specialization-loader**
   - Use platform detection
   - Support both invocation patterns

4. **Add tests**
   - Platform detection tests
   - Cross-platform path resolution tests
   - Mock both environments

**Estimated effort:** 3-4 days

### 5.2 Phase 2: Copilot Template Structure (Week 2)

**Tasks:**

1. **Create Copilot skill definitions**
   - `.github/skills/prompt-builder/SKILL.md`
   - `.github/skills/specialization-loader/SKILL.md`
   - `.github/skills/template-loader/SKILL.md`

2. **Create copilot-instructions.md**
   - Document BAZINGA workflow for Copilot
   - Include agent invocation patterns
   - Reference skills and templates

3. **Update bazinga CLI**
   - Add `--with-copilot` flag to install
   - Copy templates to `.github/templates/`
   - Create Copilot skills structure

4. **Add integration tests**
   - Test template loading on Copilot paths
   - Test version guards work correctly
   - Test token budgets applied

**Estimated effort:** 4-5 days

### 5.3 Phase 3: Agent Adaptation (Week 3)

**Tasks:**

1. **Create Copilot agent definitions**
   - `.github/agents/developer.agent.md`
   - `.github/agents/qa-expert.agent.md`
   - `.github/agents/tech-lead.agent.md`
   - `.github/agents/project-manager.agent.md`

2. **Adapt orchestrator for Copilot**
   - Use handoff mechanism for agent transitions
   - Adapt for Copilot's skill activation

3. **Document dual-platform usage**
   - Update CLAUDE.md with Copilot notes
   - Create COPILOT.md for Copilot-specific guidance

**Estimated effort:** 4-5 days

### 5.4 Phase 4: Testing & Documentation (Week 4)

**Tasks:**

1. **End-to-end testing on Copilot**
   - Run simple calculator test
   - Run parallel mode test
   - Verify all agents work

2. **Documentation**
   - Update installation guide
   - Add Copilot setup instructions
   - Document platform differences

3. **Bug fixes and polish**
   - Address issues found in testing
   - Optimize performance if needed

**Estimated effort:** 3-4 days

### 5.5 Implementation Checklist

```markdown
## Phase 1: Abstraction Layer
- [ ] Create `bazinga/scripts/platform.py`
- [ ] Add platform detection logic
- [ ] Add path resolution for both platforms
- [ ] Refactor `prompt_builder.py` to use abstraction
- [ ] Refactor `specialization-loader` to use abstraction
- [ ] Add Copilot model mapping
- [ ] Add unit tests for platform detection
- [ ] Add unit tests for path resolution

## Phase 2: Copilot Template Structure
- [ ] Create `.github/skills/prompt-builder/SKILL.md`
- [ ] Create `.github/skills/specialization-loader/SKILL.md`
- [ ] Create `copilot-instructions.md` template
- [ ] Update `bazinga install` for Copilot
- [ ] Add `--with-copilot` flag
- [ ] Test template copying
- [ ] Add integration tests

## Phase 3: Agent Adaptation
- [ ] Create `.github/agents/developer.agent.md`
- [ ] Create `.github/agents/qa-expert.agent.md`
- [ ] Create `.github/agents/tech-lead.agent.md`
- [ ] Create `.github/agents/project-manager.agent.md`
- [ ] Adapt orchestrator for Copilot
- [ ] Test handoff mechanism

## Phase 4: Testing & Documentation
- [ ] Run simple calculator test on Copilot
- [ ] Run parallel mode test on Copilot
- [ ] Update installation guide
- [ ] Create COPILOT.md
- [ ] Address bugs from testing
```

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Copilot skill execution differs from Claude | Medium | High | Test early, maintain platform-specific fallbacks |
| Version guards fail on Copilot | Low | Medium | Same Python script, just different paths |
| Token budgets not respected | Medium | Medium | Copilot model mapping may need tuning |
| Template paths break | Low | High | Comprehensive path resolution tests |
| Copilot updates break integration | Medium | Medium | Pin to known-working Copilot version |

### 6.2 Maintenance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dual maintenance burden | High | Medium | Single source templates, platform abstraction |
| Template drift between platforms | Medium | High | Automated sync checks in CI |
| Documentation lag | High | Low | Generate platform-specific docs from single source |

### 6.3 Compatibility Matrix

| Component | Claude Code | Copilot | Notes |
|-----------|-------------|---------|-------|
| Version guards | Full | Full | Same Python script |
| Token budgets | Full | Partial | Model mapping approximation |
| Specializations | Full | Full | Same loading logic |
| Template references | Programmatic | Link-based | Different invocation |
| Agent workflows | Full | Adapted | Copilot uses handoffs |
| Orchestration | Full | Adapted | Copilot lacks native orchestrator |

---

## 7. Appendix: Template File Inventory

### 7.1 Root Templates (23 files)

```
templates/
├── batch_processing.md
├── completion_report.md
├── developer_speckit.md
├── investigation_loop.md
├── logging_pattern.md
├── merge_workflow.md
├── message_templates.md
├── pm_autonomy.md
├── pm_bazinga_validation.md
├── pm_output_format.md
├── pm_planning_steps.md
├── pm_routing.md
├── pm_speckit.md
├── pm_task_classification.md
├── prompt_building.md
├── qa_speckit.md
├── response_parsing.md
├── shutdown_protocol.md
└── tech_lead_speckit.md
```

### 7.2 Orchestration Templates (4 files)

```
templates/orchestrator/
├── clarification_flow.md
├── phase_parallel.md
├── phase_simple.md
└── scope_validation.md
```

### 7.3 Specialization Templates (72 files)

```
templates/specializations/
├── 00-MASTER-INDEX.md
├── 01-languages/           # 15 files
├── 02-frameworks-frontend/ # 8 files
├── 03-frameworks-backend/  # 10 files
├── 04-mobile-desktop/      # 4 files
├── 05-databases/           # 7 files
├── 06-infrastructure/      # 5 files
├── 07-messaging-apis/      # 4 files
├── 08-testing/             # 4 files
├── 09-data-ai/             # 3 files
├── 10-security/            # 3 files
└── 11-domains/             # 8 files
```

---

## 8. References

- `research/copilot-agents-skills-implementation-deep-dive.md` - Copilot architecture
- `.claude/skills/prompt-builder/scripts/prompt_builder.py` - Current prompt building logic
- `.claude/skills/specialization-loader/SKILL.md` - Current specialization loading
- `tests/test_version_guards.py` - Version guard test suite (205 tests)
- `templates/specializations/00-MASTER-INDEX.md` - Specialization index
