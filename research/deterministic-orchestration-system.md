# Deterministic Orchestration System: Prompt Builder + Workflow Router

**Date:** 2025-12-16
**Context:** Current LLM-based orchestration is non-deterministic, causing prompt composition and routing bugs
**Decision:** Replace LLM interpretation with deterministic shell/Python scripts
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Executive Summary

The BAZINGA orchestrator currently relies on an LLM to:
1. Compose agent prompts from multiple files (agent definitions, specializations, context)
2. Determine workflow routing based on agent response status codes

**Problem:** LLMs are non-deterministic. The same instructions can produce different outputs across invocations. This causes:
- Prompts missing critical agent instructions (current bug)
- Inconsistent workflow routing
- Debugging nightmares (can't reproduce issues)

**Solution:** Two deterministic scripts:
1. **`prompt-builder.py`** - Assembles agent prompts from components
2. **`workflow-router.py`** - Determines next action based on current state

The orchestrator becomes a thin coordination layer that calls these scripts and spawns agents.

---

## Phase 1: Deterministic Prompt Builder

### Problem Statement

The orchestrator is supposed to compose prompts as:
```
FULL_PROMPT = CONTEXT_BLOCK + SPEC_BLOCK + AGENT_DEFINITION + TASK_CONTEXT
```

But it constructs custom abbreviated prompts instead, missing ~1400 lines of agent instructions.

### Root Cause

The LLM orchestrator:
1. Reads agent file (1400+ lines) ✅
2. "Remembers" it for later ❌ (forgets or summarizes)
3. Constructs custom prompt ❌ (instead of using file content)

### Solution: prompt-builder.py

A Python script that:
1. Takes parameters (agent_type, session_id, task_context, etc.)
2. Reads all required files
3. Composes the prompt deterministically
4. Returns the complete prompt

**The orchestrator CANNOT construct prompts. It MUST call the script.**

### Interface Design

```bash
# Usage
python3 bazinga/scripts/prompt-builder.py \
  --agent-type developer \
  --session-id "bazinga_20251215_103357" \
  --group-id "AUTH" \
  --task-title "Implement JWT authentication" \
  --task-requirements "Create login endpoint with refresh tokens" \
  --branch "feature/auth" \
  --mode "parallel" \
  --testing-mode "full" \
  --specializations '["01-languages/typescript.md", "03-frameworks-backend/express.md"]' \
  --context-block "$CONTEXT_BLOCK" \
  --spec-block "$SPEC_BLOCK"

# Output: Complete prompt to stdout (orchestrator captures it)
```

### Parameter Specification

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `--agent-type` | Yes | enum | developer, senior_software_engineer, qa_expert, tech_lead, project_manager, investigator, requirements_engineer |
| `--session-id` | Yes | string | Session identifier |
| `--group-id` | Yes* | string | Task group ID (*optional for PM) |
| `--task-title` | Yes* | string | Task title (*optional for PM) |
| `--task-requirements` | Yes* | string | Detailed requirements (*optional for PM) |
| `--branch` | Yes | string | Git branch to work on |
| `--mode` | Yes | enum | simple, parallel |
| `--testing-mode` | Yes | enum | full, minimal, disabled |
| `--specializations` | No | JSON array | Template paths for specialization |
| `--context-block` | No | string | Pre-assembled context from context-assembler |
| `--spec-block` | No | string | Pre-assembled specialization from specialization-loader |
| `--pm-state` | No | JSON | PM state from database (for PM spawns) |
| `--resume-context` | No | string | Resume context (for PM resume) |
| `--qa-feedback` | No | string | QA failure details (for dev retry) |
| `--tl-feedback` | No | string | Tech Lead feedback (for dev changes) |

### Composition Algorithm

```python
def build_prompt(args):
    # 1. Read agent definition file (MANDATORY)
    agent_file = AGENT_FILE_MAP[args.agent_type]
    agent_definition = read_file(f"agents/{agent_file}")

    if len(agent_definition) < MIN_LENGTHS[args.agent_type]:
        raise Error(f"Agent file too short: {len(agent_definition)} < {MIN_LENGTHS[args.agent_type]}")

    # 2. Build task context (SHORT, ~20 lines)
    task_context = f"""
---

## Current Task Assignment

**SESSION:** {args.session_id}
**GROUP:** {args.group_id}
**MODE:** {args.mode}
**BRANCH:** {args.branch}

**TASK:** {args.task_title}

**REQUIREMENTS:**
{args.task_requirements}

**TESTING MODE:** {args.testing_mode}
**COMMIT TO:** {args.branch}
**REPORT STATUS:** {STATUS_BY_AGENT[args.agent_type]}
"""

    # 3. Add feedback context if retry
    if args.qa_feedback:
        task_context += f"\n## Previous QA Feedback\n{args.qa_feedback}\n"
    if args.tl_feedback:
        task_context += f"\n## Tech Lead Feedback\n{args.tl_feedback}\n"

    # 4. Compose in order
    components = []
    if args.context_block:
        components.append(args.context_block)
    if args.spec_block:
        components.append(args.spec_block)
    components.append(agent_definition)
    components.append(task_context)

    full_prompt = "\n\n".join(components)

    # 5. Validate required markers present
    validate_markers(full_prompt, args.agent_type)

    return full_prompt
```

### Required Marker Validation

Each agent type has required markers that MUST be present in the final prompt:

```python
REQUIRED_MARKERS = {
    "developer": [
        "NO DELEGATION",
        "READY_FOR_QA",
        "READY_FOR_REVIEW",
        "BLOCKED",
    ],
    "senior_software_engineer": [
        "NO DELEGATION",
        "READY_FOR_QA",
        "ESCALATE",
    ],
    "qa_expert": [
        "PASS",
        "FAIL",
        "BLOCKED",
        "Challenge Level",
    ],
    "tech_lead": [
        "APPROVED",
        "CHANGES_REQUESTED",
        "SPAWN_INVESTIGATOR",
    ],
    "project_manager": [
        "BAZINGA",
        "SCOPE IS IMMUTABLE",
        "CONTINUE",
        "NEEDS_CLARIFICATION",
    ],
    "investigator": [
        "ROOT_CAUSE_FOUND",
        "NEED_DIAGNOSTIC",
    ],
    "requirements_engineer": [
        "READY_FOR_REVIEW",
        "BLOCKED",
    ],
}

def validate_markers(prompt, agent_type):
    missing = []
    for marker in REQUIRED_MARKERS[agent_type]:
        if marker not in prompt:
            missing.append(marker)

    if missing:
        raise Error(f"Prompt missing required markers for {agent_type}: {missing}")
```

### Agent File Map

```python
AGENT_FILE_MAP = {
    "developer": "developer.md",
    "senior_software_engineer": "senior_software_engineer.md",
    "qa_expert": "qa_expert.md",
    "tech_lead": "techlead.md",  # NOTE: no underscore
    "project_manager": "project_manager.md",
    "investigator": "investigator.md",
    "requirements_engineer": "requirements_engineer.md",
}

MIN_LENGTHS = {
    "developer": 1200,
    "senior_software_engineer": 1400,
    "qa_expert": 1000,
    "tech_lead": 800,
    "project_manager": 2000,
    "investigator": 500,
    "requirements_engineer": 700,
}
```

### PM-Specific Parameters

PM spawns have different context requirements:

```python
def build_pm_prompt(args):
    agent_definition = read_file("agents/project_manager.md")

    if args.resume_context:
        # Resume spawn
        task_context = f"""
---

## SESSION CONTEXT (RESUME)

**Session ID:** {args.session_id}
**Status:** Active (resuming)
**Mode:** {args.mode}

## PM STATE (from database)
```json
{json.dumps(args.pm_state, indent=2)}
```

## User Request
{args.resume_context}

## 🔴 SCOPE PRESERVATION (MANDATORY)
{args.scope_preservation}
"""
    else:
        # Initial spawn
        task_context = f"""
---

## SESSION CONTEXT (NEW)

**Session ID:** {args.session_id}

## User Requirements
{args.task_requirements}

## MANDATORY FIRST ACTION
Before ANY analysis, save your understanding of this request...
"""

    return agent_definition + task_context
```

### Integration with Specialization Loader

The prompt-builder can call specialization-loader internally OR receive pre-built blocks:

**Option A: Orchestrator calls specialization-loader first, passes result:**
```bash
# Orchestrator calls specialization-loader
SPEC_BLOCK=$(Skill specialization-loader output)

# Then calls prompt-builder with result
python3 prompt-builder.py --spec-block "$SPEC_BLOCK" ...
```

**Option B: Prompt-builder calls specialization-loader internally:**
```bash
# Prompt-builder handles everything
python3 prompt-builder.py --build-specialization ...
```

**Recommendation:** Option A (separate calls) for modularity and debugging.

### Output Format

```
[PROMPT_START agent_type={type} session={id} group={group}]
{complete prompt content}
[PROMPT_END]

Metadata:
- Lines: {count}
- Tokens (est): {count}
- Markers verified: {list}
- Components: context_block={yes/no}, spec_block={yes/no}, agent_file={lines}, task_context={lines}
```

### Error Handling

| Error | Action |
|-------|--------|
| Agent file not found | Exit 1 with clear message |
| Agent file too short | Exit 1 - file may be corrupted |
| Required marker missing | Exit 1 - prompt invalid |
| Invalid JSON in parameters | Exit 1 with parse error |
| Missing required parameter | Exit 1 with usage |

---

## Phase 2: Deterministic Workflow Router

### Problem Statement

The orchestrator must decide:
1. After Developer responds → What next? (QA, Tech Lead, or retry?)
2. After QA responds → What next? (Tech Lead, Developer, or escalate?)
3. After Tech Lead responds → What next? (PM, Developer, or Investigator?)
4. After PM responds → What next? (Developers, or BAZINGA?)

Currently, this logic is embedded in LLM prompts and interpreted non-deterministically.

### Solution: workflow-router.py

A Python script that:
1. Takes current state (agent, status, context)
2. Returns the deterministic next action
3. Covers ALL workflow transitions

### State Machine Definition

#### Agent Status Codes

```python
DEVELOPER_STATUSES = [
    "READY_FOR_QA",      # Has integration/E2E tests → QA Expert
    "READY_FOR_REVIEW",  # Unit tests only or no tests → Tech Lead
    "BLOCKED",           # Cannot proceed → Investigator or Tech Lead
    "PARTIAL",           # Some work done → Re-spawn Developer
    "INCOMPLETE",        # Same as PARTIAL
    "ESCALATE_SENIOR",   # Too complex → Senior Software Engineer
]

QA_STATUSES = [
    "PASS",              # All tests pass → Tech Lead
    "FAIL",              # Tests fail → Developer (retry)
    "PARTIAL",           # Some tests couldn't run → Tech Lead (to decide)
    "BLOCKED",           # Can't run tests → Tech Lead (to unblock)
    "ESCALATE_SENIOR",   # Level 3+ failure → Senior Software Engineer
]

TECH_LEAD_STATUSES = [
    "APPROVED",           # Code quality OK → PM (or merge + PM)
    "CHANGES_REQUESTED",  # Issues found → Developer (fix)
    "SPAWN_INVESTIGATOR", # Complex problem → Investigator
    "ESCALATE_TO_OPUS",   # Need stronger model → Re-review with Opus
]

PM_STATUSES = [
    "PLANNING_COMPLETE",     # Initial planning done → Spawn Developers
    "CONTINUE",              # Resume/more work → Spawn Developers
    "BAZINGA",               # All complete → END
    "NEEDS_CLARIFICATION",   # User input needed → Pause
    "INVESTIGATION_NEEDED",  # Problem needs investigation → Investigator
    "INVESTIGATION_ONLY",    # Just answered questions → END (no implementation)
]

INVESTIGATOR_STATUSES = [
    "ROOT_CAUSE_FOUND",  # Found issue → Developer (with fix guidance)
    "NEED_DIAGNOSTIC",   # Need more info → Tech Lead (for guidance)
    "BLOCKED",           # Can't proceed → Tech Lead
]

RE_STATUSES = [
    "READY_FOR_REVIEW",  # Research complete → Tech Lead (bypasses QA)
    "BLOCKED",           # Need access/info → Investigator
    "PARTIAL",           # More work needed → Continue RE
]
```

#### Complete State Transition Table

```python
TRANSITIONS = {
    # Developer transitions
    ("developer", "READY_FOR_QA"): {
        "next_agent": "qa_expert",
        "action": "spawn",
        "include_context": ["dev_output", "files_changed", "test_results"],
    },
    ("developer", "READY_FOR_REVIEW"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["dev_output", "files_changed"],
    },
    ("developer", "BLOCKED"): {
        "next_agent": "investigator",
        "action": "spawn",
        "include_context": ["blocker_details"],
        "fallback": {"next_agent": "tech_lead", "action": "spawn"},  # If no investigator configured
    },
    ("developer", "PARTIAL"): {
        "next_agent": "developer",
        "action": "respawn",
        "include_context": ["partial_work", "remaining_tasks"],
    },
    ("developer", "INCOMPLETE"): {
        "next_agent": "developer",
        "action": "respawn",
        "include_context": ["partial_work", "remaining_tasks"],
    },
    ("developer", "ESCALATE_SENIOR"): {
        "next_agent": "senior_software_engineer",
        "action": "spawn",
        "include_context": ["dev_output", "escalation_reason"],
    },

    # QA Expert transitions
    ("qa_expert", "PASS"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["qa_report", "test_results", "coverage"],
    },
    ("qa_expert", "FAIL"): {
        "next_agent": "developer",
        "action": "respawn",
        "include_context": ["qa_failures", "failing_tests"],
        "escalation_check": True,  # Check revision_count for SSE escalation
    },
    ("qa_expert", "PARTIAL"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["qa_report", "partial_results"],
    },
    ("qa_expert", "BLOCKED"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["blocker_details"],
    },
    ("qa_expert", "ESCALATE_SENIOR"): {
        "next_agent": "senior_software_engineer",
        "action": "spawn",
        "include_context": ["qa_report", "escalation_reason"],
    },

    # Tech Lead transitions
    ("tech_lead", "APPROVED"): {
        "next_agent": "developer",  # For merge task
        "action": "spawn_merge",
        "then": "check_phase",  # After merge, check if more groups or PM
        "include_context": ["approval_notes"],
    },
    ("tech_lead", "CHANGES_REQUESTED"): {
        "next_agent": "developer",
        "action": "respawn",
        "include_context": ["tl_feedback", "required_changes"],
        "escalation_check": True,
    },
    ("tech_lead", "SPAWN_INVESTIGATOR"): {
        "next_agent": "investigator",
        "action": "spawn",
        "include_context": ["investigation_scope"],
    },
    ("tech_lead", "ESCALATE_TO_OPUS"): {
        "next_agent": "tech_lead",
        "action": "respawn",
        "model_override": "opus",
        "include_context": ["escalation_reason", "original_review"],
    },

    # PM transitions
    ("project_manager", "PLANNING_COMPLETE"): {
        "next_agent": "developer",  # Or multiple
        "action": "spawn_batch",
        "max_parallel": 4,
        "include_context": ["task_groups"],
    },
    ("project_manager", "CONTINUE"): {
        "next_agent": "developer",
        "action": "spawn_batch",
        "max_parallel": 4,
        "include_context": ["pending_groups"],
    },
    ("project_manager", "BAZINGA"): {
        "next_agent": None,
        "action": "validate_then_end",
        "include_context": ["completion_summary"],
    },
    ("project_manager", "NEEDS_CLARIFICATION"): {
        "next_agent": None,
        "action": "pause_for_user",
        "include_context": ["clarification_question"],
    },
    ("project_manager", "INVESTIGATION_NEEDED"): {
        "next_agent": "investigator",
        "action": "spawn",
        "include_context": ["investigation_request"],
    },
    ("project_manager", "INVESTIGATION_ONLY"): {
        "next_agent": None,
        "action": "end_session",
        "include_context": ["investigation_answers"],
    },

    # Investigator transitions
    ("investigator", "ROOT_CAUSE_FOUND"): {
        "next_agent": "developer",
        "action": "spawn",
        "include_context": ["root_cause", "fix_guidance"],
    },
    ("investigator", "NEED_DIAGNOSTIC"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["diagnostic_request"],
    },
    ("investigator", "BLOCKED"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["blocker_details"],
    },

    # Requirements Engineer transitions
    ("requirements_engineer", "READY_FOR_REVIEW"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["research_deliverable"],
        "bypass_qa": True,  # RE output goes directly to TL
    },
    ("requirements_engineer", "BLOCKED"): {
        "next_agent": "investigator",
        "action": "spawn",
        "include_context": ["blocker_details"],
    },
    ("requirements_engineer", "PARTIAL"): {
        "next_agent": "requirements_engineer",
        "action": "respawn",
        "include_context": ["partial_research"],
    },

    # Senior Software Engineer transitions (same as Developer)
    ("senior_software_engineer", "READY_FOR_QA"): {
        "next_agent": "qa_expert",
        "action": "spawn",
        "include_context": ["dev_output", "files_changed", "test_results"],
    },
    ("senior_software_engineer", "READY_FOR_REVIEW"): {
        "next_agent": "tech_lead",
        "action": "spawn",
        "include_context": ["dev_output", "files_changed"],
    },
    ("senior_software_engineer", "BLOCKED"): {
        "next_agent": "tech_lead",
        "action": "spawn",  # SSE blocked goes to TL, not Investigator
        "include_context": ["blocker_details"],
    },
}
```

### Interface Design

```bash
# Usage
python3 bazinga/scripts/workflow-router.py \
  --current-agent developer \
  --response-status READY_FOR_QA \
  --session-id "bazinga_20251215_103357" \
  --group-id "AUTH" \
  --revision-count 0 \
  --testing-mode full \
  --groups-status '{"AUTH": "in_progress", "API": "pending"}' \
  --agent-response "$(cat agent_output.txt)"

# Output: JSON with next action
{
  "next_agent": "qa_expert",
  "action": "spawn",
  "parameters": {
    "group_id": "AUTH",
    "include_context": ["dev_output", "files_changed", "test_results"]
  },
  "context_to_extract": ["files_changed", "test_results"],
  "model": "sonnet"
}
```

### Routing Algorithm

```python
def get_next_action(args):
    key = (args.current_agent, args.response_status)

    if key not in TRANSITIONS:
        return {
            "error": f"Unknown transition: {key}",
            "suggestion": "Check agent output for valid status code"
        }

    transition = TRANSITIONS[key]

    # Handle escalation checks
    if transition.get("escalation_check"):
        if args.revision_count >= 2:
            # Escalate to SSE
            return {
                "next_agent": "senior_software_engineer",
                "action": "spawn",
                "parameters": {"escalation_reason": "Multiple failures"},
                "model": MODEL_CONFIG["senior_software_engineer"]
            }

    # Handle model overrides
    model = transition.get("model_override") or MODEL_CONFIG.get(transition["next_agent"])

    # Handle batch spawns (parallel mode)
    if transition["action"] == "spawn_batch":
        pending = [g for g, s in args.groups_status.items() if s == "pending"]
        return {
            "next_agent": transition["next_agent"],
            "action": "spawn_batch",
            "groups": pending[:transition["max_parallel"]],
            "model": model
        }

    # Handle phase checks (after merge)
    if transition.get("then") == "check_phase":
        pending = [g for g, s in args.groups_status.items() if s != "completed"]
        if pending:
            return {
                "next_agent": "developer",
                "action": "spawn_batch",
                "groups": pending[:4],
                "model": MODEL_CONFIG["developer"]
            }
        else:
            return {
                "next_agent": "project_manager",
                "action": "spawn",
                "parameters": {"assessment_type": "final"},
                "model": MODEL_CONFIG["project_manager"]
            }

    return {
        "next_agent": transition["next_agent"],
        "action": transition["action"],
        "parameters": {
            "include_context": transition.get("include_context", []),
            "group_id": args.group_id,
        },
        "model": model
    }
```

### Testing Mode Impact on Routing

```python
def adjust_for_testing_mode(transition, testing_mode):
    """Adjust routing based on testing mode configuration."""

    if testing_mode == "disabled":
        # Skip QA entirely
        if transition["next_agent"] == "qa_expert":
            return {
                "next_agent": "tech_lead",
                "action": "spawn",
                "skip_reason": "testing_mode=disabled"
            }

    elif testing_mode == "minimal":
        # Skip QA, go directly to Tech Lead
        if transition["next_agent"] == "qa_expert":
            return {
                "next_agent": "tech_lead",
                "action": "spawn",
                "skip_reason": "testing_mode=minimal"
            }

    return transition
```

### Status Code Extraction

The router can also help extract status codes from agent responses:

```python
STATUS_PATTERNS = {
    "READY_FOR_QA": [
        r"Status:\s*READY_FOR_QA",
        r"\*\*Status:\*\*\s*READY_FOR_QA",
        r"READY_FOR_QA",
    ],
    "APPROVED": [
        r"Decision:\s*APPROVED",
        r"\*\*Decision:\*\*\s*APPROVED",
        r"Status:\s*APPROVED",
    ],
    # ... etc for all status codes
}

def extract_status(agent_type, response_text):
    """Extract status code from agent response."""
    for status, patterns in STATUS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                # Validate this status is valid for this agent type
                if is_valid_status(agent_type, status):
                    return status

    return "UNKNOWN"
```

---

## Implementation Architecture

### Directory Structure

```
bazinga/
├── scripts/
│   ├── prompt-builder.py      # Phase 1: Deterministic prompt composition
│   ├── workflow-router.py     # Phase 2: Deterministic workflow routing
│   ├── status-extractor.py    # Helper: Extract status from responses
│   └── orchestrator-loop.py   # Optional: Main orchestration loop
├── config/
│   ├── transitions.json       # State machine definition
│   ├── agent-markers.json     # Required markers per agent
│   └── status-patterns.json   # Regex patterns for status extraction
```

### Orchestrator Integration

The orchestrator's role becomes minimal:

```markdown
## Orchestrator Responsibilities (After Refactor)

1. **Initialize** - Create session, load configs
2. **Spawn PM** - Call prompt-builder, spawn PM
3. **Receive Response** - Capture agent output
4. **Route** - Call workflow-router to get next action
5. **Build Prompt** - Call prompt-builder for next agent
6. **Spawn Agent** - Execute Task() with built prompt
7. **Loop** - Until workflow-router returns "end"
```

**The orchestrator no longer needs:**
- Complex prompt composition logic
- Workflow routing logic
- Status code interpretation
- Escalation rules

### Migration Strategy

#### Phase 1: Prompt Builder (Week 1-2)

1. **Day 1-2:** Implement prompt-builder.py with basic agent types
2. **Day 3-4:** Add marker validation
3. **Day 5:** Integrate with orchestrator (optional call first)
4. **Day 6-7:** Test with all agent types
5. **Week 2:** Make mandatory, remove LLM prompt composition

#### Phase 2: Workflow Router (Week 3-4)

1. **Day 1-2:** Implement core state machine
2. **Day 3-4:** Add all transitions
3. **Day 5:** Add testing mode adjustments
4. **Day 6-7:** Add status extraction helper
5. **Week 4:** Integrate, test, make mandatory

### Backward Compatibility

During migration:
1. Scripts are optional - orchestrator can still use LLM logic
2. Add `--use-deterministic` flag to enable new system
3. Log both outputs to compare (A/B testing)
4. Once validated, make deterministic mandatory

---

## Risks and Mitigations

### Risk 1: Parameter Explosion

**Risk:** Too many parameters to pass to scripts
**Mitigation:**
- Use JSON config files for complex data
- Group related parameters
- Allow reading from database directly

### Risk 2: Edge Cases Not Covered

**Risk:** State machine missing transitions
**Mitigation:**
- Comprehensive transition table (defined above)
- Fallback to "unknown" with clear error
- Easy to add new transitions

### Risk 3: Script Failures

**Risk:** Script crashes break orchestration
**Mitigation:**
- Comprehensive error handling
- Exit codes for different failure types
- Orchestrator fallback to manual routing (temporary)

### Risk 4: Loss of Flexibility

**Risk:** Can't handle unexpected scenarios
**Mitigation:**
- "UNKNOWN" status triggers Tech Lead review
- Manual override capability
- Easy to extend transition table

---

## Testing Strategy

### Unit Tests for prompt-builder.py

```python
def test_developer_prompt_includes_agent_file():
    prompt = run_prompt_builder(agent_type="developer", ...)
    assert len(prompt.split('\n')) > 1200
    assert "NO DELEGATION" in prompt
    assert "READY_FOR_QA" in prompt

def test_pm_prompt_includes_bazinga_rules():
    prompt = run_prompt_builder(agent_type="project_manager", ...)
    assert "BAZINGA" in prompt
    assert "SCOPE IS IMMUTABLE" in prompt

def test_marker_validation_fails_on_short_prompt():
    with pytest.raises(MarkerValidationError):
        run_prompt_builder(agent_type="developer", mock_agent_file="short content")
```

### Unit Tests for workflow-router.py

```python
def test_developer_ready_for_qa_routes_to_qa():
    result = run_workflow_router(current_agent="developer", status="READY_FOR_QA")
    assert result["next_agent"] == "qa_expert"

def test_qa_fail_routes_to_developer():
    result = run_workflow_router(current_agent="qa_expert", status="FAIL")
    assert result["next_agent"] == "developer"

def test_escalation_after_2_failures():
    result = run_workflow_router(
        current_agent="qa_expert",
        status="FAIL",
        revision_count=2
    )
    assert result["next_agent"] == "senior_software_engineer"

def test_testing_disabled_skips_qa():
    result = run_workflow_router(
        current_agent="developer",
        status="READY_FOR_QA",
        testing_mode="disabled"
    )
    assert result["next_agent"] == "tech_lead"
```

### Integration Tests

```python
def test_full_simple_workflow():
    """Test: Developer → QA → TL → PM → BAZINGA"""
    session = create_session()

    # PM spawn
    pm_prompt = prompt_builder(agent_type="project_manager", ...)
    pm_response = spawn_and_capture(pm_prompt)

    # Get next action
    action = workflow_router(current_agent="project_manager",
                            status=extract_status(pm_response))
    assert action["next_agent"] == "developer"

    # Developer spawn
    dev_prompt = prompt_builder(agent_type="developer", ...)
    dev_response = spawn_and_capture(dev_prompt)

    # ... continue through workflow ...

    # Verify BAZINGA reached
    assert session.status == "completed"
```

---

## Comparison: Before vs After

### Before (LLM-Based)

```
Orchestrator (LLM):
  1. Receives PM response
  2. Interprets status code (may misread)
  3. Decides next agent (may choose wrong one)
  4. Reads agent file (may forget content)
  5. Composes prompt (may skip sections)
  6. Spawns agent (may have incomplete prompt)

Failure modes:
  - Custom prompt instead of agent file ❌
  - Wrong routing decision ❌
  - Missed status code ❌
  - Forgotten escalation rule ❌
```

### After (Deterministic)

```
Orchestrator (LLM):
  1. Receives PM response
  2. Calls status-extractor.py → status code
  3. Calls workflow-router.py → next action
  4. Calls prompt-builder.py → complete prompt
  5. Spawns agent with built prompt

Failure modes:
  - Script has bug (fixable, testable) ✓
  - Unknown status code (explicit error) ✓
  - Missing transition (explicit error) ✓
```

---

## Decision Summary

| Aspect | Current (LLM) | Proposed (Deterministic) |
|--------|---------------|--------------------------|
| Prompt composition | Non-deterministic | 100% deterministic |
| Workflow routing | Non-deterministic | 100% deterministic |
| Testability | Hard to test | Unit testable |
| Debugging | Reproduce issues? | Same inputs = same outputs |
| Maintenance | Scattered in prompts | Centralized in scripts |
| Flexibility | High (LLM interprets) | Explicit (add to transition table) |
| Reliability | ~80% (bugs happen) | ~99% (script bugs are fixable) |

---

## Appendix A: Complete Transition Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BAZINGA Workflow                             │
└─────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │     PM       │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              PLANNING_COMPLETE   CONTINUE        BAZINGA
                    │                │                │
                    ▼                ▼                ▼
              ┌─────────────────────────┐        ┌────────┐
              │  Spawn Developer(s)     │        │  END   │
              │  (max 4 parallel)       │        └────────┘
              └───────────┬─────────────┘
                          │
         ┌────────────────┼────────────────┬───────────────┐
         ▼                ▼                ▼               ▼
   READY_FOR_QA    READY_FOR_REVIEW    BLOCKED       ESCALATE_SENIOR
         │                │                │               │
         ▼                │                ▼               ▼
   ┌──────────┐           │         ┌────────────┐  ┌─────────┐
   │ QA Expert│           │         │Investigator│  │   SSE   │
   └────┬─────┘           │         └─────┬──────┘  └────┬────┘
        │                 │               │              │
   ┌────┼────┐            │               │              │
   ▼    ▼    ▼            │               ▼              │
 PASS FAIL BLOCKED        │        ROOT_CAUSE_FOUND      │
   │    │    │            │               │              │
   │    │    │            │               ▼              │
   │    │    └────────────┼───────►┌──────────┐◄─────────┘
   │    │                 │        │ Developer│
   │    └────────────────►│        │ (retry)  │
   │                      │        └────┬─────┘
   │                      │             │
   ▼                      ▼             │
   └──────────────►┌──────────────┐◄────┘
                   │  Tech Lead   │
                   └──────┬───────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          APPROVED  CHANGES_REQ  SPAWN_INVESTIGATOR
              │           │           │
              ▼           │           ▼
        ┌──────────┐      │    ┌────────────┐
        │  Merge   │      │    │Investigator│
        └────┬─────┘      │    └────────────┘
             │            │
             ▼            │
      ┌────────────┐      │
      │ Check Phase├──────┘
      └──────┬─────┘
             │
     ┌───────┼───────┐
     ▼               ▼
  More Groups    All Complete
     │               │
     ▼               ▼
  Developer        PM
  (next phase)   (BAZINGA?)
```

---

## Appendix B: Parameter Reference

### prompt-builder.py Parameters

```
Required:
  --agent-type         Agent type (developer, qa_expert, tech_lead, project_manager, etc.)
  --session-id         Session identifier
  --branch             Git branch name
  --mode               Execution mode (simple, parallel)
  --testing-mode       Testing mode (full, minimal, disabled)

Conditional (required for non-PM):
  --group-id           Task group identifier
  --task-title         Task title
  --task-requirements  Task requirements text

Optional:
  --specializations    JSON array of template paths
  --context-block      Pre-built context from context-assembler
  --spec-block         Pre-built specialization block
  --pm-state           JSON PM state (for PM spawns)
  --resume-context     Resume context text (for PM resume)
  --qa-feedback        QA failure details (for developer retry)
  --tl-feedback        Tech Lead feedback (for developer changes)
  --revision-count     Number of previous attempts (for escalation)
```

### workflow-router.py Parameters

```
Required:
  --current-agent      Agent that just responded
  --response-status    Status code from agent response
  --session-id         Session identifier
  --group-id           Current group ID

Optional:
  --testing-mode       Testing mode (affects QA routing)
  --revision-count     Number of previous attempts
  --groups-status      JSON map of group_id → status
  --agent-response     Full agent response text (for extraction)
```

---

## References

- Current orchestrator: `.claude/commands/bazinga.orchestrate.md`
- Phase templates: `templates/orchestrator/phase_simple.md`, `phase_parallel.md`
- Agent definitions: `agents/*.md`
- Response parsing: `templates/response_parsing.md`
- Specialization loader: `.claude/skills/specialization-loader/SKILL.md`
