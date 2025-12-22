# Deterministic Orchestration System - Final Implementation Plan

**Date:** 2025-12-16
**Context:** Replace LLM-based prompt composition and workflow routing with deterministic scripts
**Decision:** Unified prompt-builder - Python script does everything, called ON-DEMAND before each spawn
**Status:** ✅ IMPLEMENTED
**Reviewed by:** OpenAI GPT-5

### Implementation Summary (2025-12-16)

All phases completed successfully:
- ✅ Phase 0: Created config directory and JSON files (transitions.json, agent-markers.json)
- ✅ Phase 1: Database schema v13 with workflow_transitions, agent_markers, workflow_special_rules tables
- ✅ Phase 2: Created Python scripts (prompt_builder.py, workflow_router.py, seed_configs.py)
- ✅ Phase 3: Created skill wrappers (prompt-builder, workflow-router, config-seeder)
- ✅ Phase 4: Updated orchestrator to use new deterministic system
- ✅ Phase 5: All tests passing

**Verification:**
- prompt_builder.py generates 1557 lines for developer, 2539 lines for PM (full agent files)
- workflow_router.py returns correct routing decisions from DB
- seed_configs.py seeds 37 transitions, 7 markers, 5 special rules

---

## Executive Summary

The BAZINGA orchestrator currently relies on an LLM to compose agent prompts and determine workflow routing. This is inherently non-deterministic and causes bugs (e.g., prompts missing agent file content).

**Solution:** Two deterministic Python scripts, each wrapped by a thin skill:

1. **`prompt-builder` Skill** → `prompt_builder.py` - Builds complete agent prompts
2. **`workflow-router` Skill** → `workflow_router.py` - Determines next action based on state

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Python script does ALL composition | 100% deterministic - no LLM interpretation |
| Script queries DB directly | Specializations + context read from DB at spawn time |
| Called ON-DEMAND | Fresh DB query before EACH spawn gets latest context |
| Skill is thin wrapper | Just calls script, returns output |
| No skill-to-skill invocation | Skills can't reliably invoke other skills |

**Architecture:**
```
Orchestrator
    │
    └─→ Skill(command: "prompt-builder")
              │
              └─→ prompt_builder.py
                    ├── Reads DB: task_groups.specializations
                    ├── Reads DB: context_packages
                    ├── Reads DB: error_patterns
                    ├── Reads DB: agent_reasoning
                    ├── Reads FS: agents/*.md (full file)
                    ├── Reads FS: templates/specializations/*.md
                    ├── Applies token budgets
                    ├── Validates required markers
                    └── Returns: COMPLETE PROMPT
```

---

## Part 0: On-Demand Invocation Timing

### Why On-Demand Matters

Context is **CUMULATIVE** during orchestration. The prompt_builder.py script is called RIGHT BEFORE each spawn to get the latest DB state.

### Context Growth Timeline

```
Session Start:
├── Config seeded to DB
└── Context: Empty

PM Spawn:
├── prompt_builder.py queries DB
├── Context: Only session info
└── PM gets: agent file + task

PM Creates Task Groups:
└── Specializations stored in DB (per task group)

Developer Spawn:
├── prompt_builder.py queries DB
├── Context: Specializations from task_groups
└── Developer gets: specialization + agent file + task

Developer Completes → Saves Reasoning:
└── agent_reasoning table updated

QA Spawn:
├── prompt_builder.py queries DB (FRESH query!)
├── Context NOW includes: Developer's reasoning!
└── QA gets: specialization + context + agent file + task

QA Completes → Saves Reasoning:
└── agent_reasoning table updated

Tech Lead Spawn:
├── prompt_builder.py queries DB (FRESH query!)
├── Context NOW includes: Dev + QA reasoning!
└── TL gets: specialization + full context + agent file + task
```

### What Each Agent Receives

| Agent | Specialization | Context | Agent File |
|-------|---------------|---------|------------|
| PM (initial) | None | None | Full ~2500 lines |
| PM (resume) | None | Session state | Full ~2500 lines |
| Developer (1st) | From task_groups | None | Full ~1200 lines |
| Developer (retry) | From task_groups | Prior reasoning + feedback | Full ~1200 lines |
| QA Expert | From task_groups | Developer reasoning | Full ~1000 lines |
| Tech Lead | From task_groups | Dev + QA reasoning | Full ~800 lines |
| Investigator | From task_groups | All prior reasoning | Full ~500 lines |

---

## Part 1: Complete Agent Status Codes Reference

### Developer
```
READY_FOR_QA        - Implementation complete, has integration/E2E tests → QA Expert
READY_FOR_REVIEW    - Implementation complete, unit tests only or no tests → Tech Lead
BLOCKED             - Cannot proceed without external help → Investigator or Tech Lead
PARTIAL             - Some work done, more needed → Re-spawn Developer
INCOMPLETE          - Same as PARTIAL → Re-spawn Developer
ESCALATE_SENIOR     - Issue too complex → Senior Software Engineer
NEEDS_TECH_LEAD_VALIDATION - Uncertain about approach → Tech Lead for guidance
```

### Senior Software Engineer
```
READY_FOR_QA        - Implementation complete, has tests → QA Expert
READY_FOR_REVIEW    - Implementation complete, unit tests only → Tech Lead
BLOCKED             - Cannot proceed → Tech Lead (SSE blocked goes to TL, not Investigator)
NEEDS_TECH_LEAD_VALIDATION - Needs architectural guidance → Tech Lead
```

### QA Expert
```
PASS                - All tests pass → Tech Lead
FAIL                - Tests fail → Developer (retry)
FAIL_ESCALATE       - Challenge Level 3+ failure → Senior Software Engineer
PARTIAL             - Some tests couldn't run → Tech Lead (to decide)
BLOCKED             - Can't run tests → Tech Lead (to unblock)
FLAKY               - Intermittent failures → Tech Lead (to analyze)
```

### Tech Lead
```
APPROVED                      - Code quality OK → PM (after merge)
CHANGES_REQUESTED             - Issues found → Developer (fix)
SPAWN_INVESTIGATOR            - Complex problem needs deep analysis → Investigator
ESCALATE_TO_OPUS              - Need stronger model → Re-review with Opus
UNBLOCKING_GUIDANCE_PROVIDED  - Provided guidance for blocked agent → Original agent
ARCHITECTURAL_DECISION_MADE   - Made architectural decision → Developer
```

### Project Manager
```
PLANNING_COMPLETE       - Initial planning done → Spawn Developers
CONTINUE                - Resume/more work needed → Spawn Developers
BAZINGA                 - All complete → END (triggers validator)
NEEDS_CLARIFICATION     - User input needed → Pause for user
INVESTIGATION_NEEDED    - Problem needs investigation → Investigator
INVESTIGATION_ONLY      - Just answered questions, no implementation → END
```

### Investigator
```
ROOT_CAUSE_FOUND        - Found issue → Developer (with fix guidance)
INCOMPLETE              - Partial findings → Continue investigation or Tech Lead
BLOCKED                 - Can't proceed → Tech Lead
EXHAUSTED               - All hypotheses eliminated → Tech Lead (escalate)
WAITING_FOR_RESULTS     - Needs developer to run diagnostic → Developer (diagnostic task)
```

### Requirements Engineer
```
READY_FOR_REVIEW    - Research complete → Tech Lead (bypasses QA)
BLOCKED             - Need external access or permissions → Investigator
PARTIAL             - Partial findings, need more time → Continue RE
```

---

## Part 2: Complete State Transitions Configuration

### `bazinga/config/transitions.json`

```json
{
  "_version": "1.0.0",
  "_description": "Deterministic workflow state machine for BAZINGA orchestration",

  "developer": {
    "READY_FOR_QA": {
      "next_agent": "qa_expert",
      "action": "spawn",
      "include_context": ["dev_output", "files_changed", "test_results"]
    },
    "READY_FOR_REVIEW": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["dev_output", "files_changed"]
    },
    "BLOCKED": {
      "next_agent": "investigator",
      "action": "spawn",
      "include_context": ["blocker_details"],
      "fallback_agent": "tech_lead"
    },
    "PARTIAL": {
      "next_agent": "developer",
      "action": "respawn",
      "include_context": ["partial_work", "remaining_tasks"]
    },
    "INCOMPLETE": {
      "next_agent": "developer",
      "action": "respawn",
      "include_context": ["partial_work", "remaining_tasks"]
    },
    "ESCALATE_SENIOR": {
      "next_agent": "senior_software_engineer",
      "action": "spawn",
      "include_context": ["dev_output", "escalation_reason"]
    },
    "NEEDS_TECH_LEAD_VALIDATION": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["validation_request", "uncertainty_details"]
    }
  },

  "senior_software_engineer": {
    "READY_FOR_QA": {
      "next_agent": "qa_expert",
      "action": "spawn",
      "include_context": ["dev_output", "files_changed", "test_results"]
    },
    "READY_FOR_REVIEW": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["dev_output", "files_changed"]
    },
    "BLOCKED": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["blocker_details"]
    },
    "NEEDS_TECH_LEAD_VALIDATION": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["validation_request"]
    }
  },

  "qa_expert": {
    "PASS": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["qa_report", "test_results", "coverage"]
    },
    "FAIL": {
      "next_agent": "developer",
      "action": "respawn",
      "include_context": ["qa_failures", "failing_tests"],
      "escalation_check": true
    },
    "FAIL_ESCALATE": {
      "next_agent": "senior_software_engineer",
      "action": "spawn",
      "include_context": ["qa_report", "challenge_level", "escalation_reason"]
    },
    "PARTIAL": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["qa_report", "partial_results"]
    },
    "BLOCKED": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["blocker_details"]
    },
    "FLAKY": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["flaky_test_details", "qa_report"]
    }
  },

  "tech_lead": {
    "APPROVED": {
      "next_agent": "developer",
      "action": "spawn_merge",
      "then": "check_phase",
      "include_context": ["approval_notes"]
    },
    "CHANGES_REQUESTED": {
      "next_agent": "developer",
      "action": "respawn",
      "include_context": ["tl_feedback", "required_changes"],
      "escalation_check": true
    },
    "SPAWN_INVESTIGATOR": {
      "next_agent": "investigator",
      "action": "spawn",
      "include_context": ["investigation_scope"]
    },
    "ESCALATE_TO_OPUS": {
      "next_agent": "tech_lead",
      "action": "respawn",
      "model_override": "opus",
      "include_context": ["escalation_reason", "original_review"]
    },
    "UNBLOCKING_GUIDANCE_PROVIDED": {
      "next_agent": "_return_to_blocked",
      "action": "spawn",
      "include_context": ["guidance", "unblocking_steps"]
    },
    "ARCHITECTURAL_DECISION_MADE": {
      "next_agent": "developer",
      "action": "spawn",
      "include_context": ["decision", "implementation_guidance"]
    }
  },

  "project_manager": {
    "PLANNING_COMPLETE": {
      "next_agent": "developer",
      "action": "spawn_batch",
      "max_parallel": 4,
      "include_context": ["task_groups"]
    },
    "CONTINUE": {
      "next_agent": "developer",
      "action": "spawn_batch",
      "max_parallel": 4,
      "include_context": ["pending_groups"]
    },
    "BAZINGA": {
      "next_agent": null,
      "action": "validate_then_end",
      "include_context": ["completion_summary"]
    },
    "NEEDS_CLARIFICATION": {
      "next_agent": null,
      "action": "pause_for_user",
      "include_context": ["clarification_question"]
    },
    "INVESTIGATION_NEEDED": {
      "next_agent": "investigator",
      "action": "spawn",
      "include_context": ["investigation_request"]
    },
    "INVESTIGATION_ONLY": {
      "next_agent": null,
      "action": "end_session",
      "include_context": ["investigation_answers"]
    }
  },

  "investigator": {
    "ROOT_CAUSE_FOUND": {
      "next_agent": "developer",
      "action": "spawn",
      "include_context": ["root_cause", "fix_guidance"]
    },
    "INCOMPLETE": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["partial_findings", "next_steps"]
    },
    "BLOCKED": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["blocker_details"]
    },
    "EXHAUSTED": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["hypotheses_tested", "recommendations"]
    },
    "WAITING_FOR_RESULTS": {
      "next_agent": "developer",
      "action": "spawn",
      "include_context": ["diagnostic_request"]
    }
  },

  "requirements_engineer": {
    "READY_FOR_REVIEW": {
      "next_agent": "tech_lead",
      "action": "spawn",
      "include_context": ["research_deliverable"],
      "bypass_qa": true
    },
    "BLOCKED": {
      "next_agent": "investigator",
      "action": "spawn",
      "include_context": ["blocker_details"]
    },
    "PARTIAL": {
      "next_agent": "requirements_engineer",
      "action": "respawn",
      "include_context": ["partial_research"]
    }
  },

  "_special_rules": {
    "testing_mode_disabled": {
      "description": "When testing_mode=disabled, skip QA entirely",
      "affected_statuses": ["READY_FOR_QA"],
      "override_next_agent": "tech_lead"
    },
    "testing_mode_minimal": {
      "description": "When testing_mode=minimal, skip QA Expert",
      "affected_statuses": ["READY_FOR_QA"],
      "override_next_agent": "tech_lead"
    },
    "escalation_after_failures": {
      "description": "After 2 failures, escalate to SSE",
      "threshold": 2,
      "escalation_agent": "senior_software_engineer"
    },
    "security_sensitive": {
      "description": "Security tasks always use SSE + mandatory TL review",
      "force_agent": "senior_software_engineer",
      "mandatory_review": true
    },
    "research_tasks": {
      "description": "Research tasks go to RE, max 2 parallel",
      "agent": "requirements_engineer",
      "max_parallel": 2
    }
  }
}
```

---

## Part 3: Complete Agent Markers Configuration

### `bazinga/config/agent-markers.json`

```json
{
  "_version": "1.0.0",
  "_description": "Required markers that MUST be present in agent prompts for validation",

  "developer": {
    "required": [
      "NO DELEGATION",
      "READY_FOR_QA",
      "READY_FOR_REVIEW",
      "BLOCKED",
      "ESCALATE_SENIOR"
    ],
    "workflow_markers": [
      "Developer → QA",
      "Developer → Tech Lead"
    ]
  },

  "senior_software_engineer": {
    "required": [
      "NO DELEGATION",
      "READY_FOR_QA",
      "READY_FOR_REVIEW",
      "BLOCKED"
    ],
    "workflow_markers": [
      "SSE → QA",
      "SSE → Tech Lead"
    ]
  },

  "qa_expert": {
    "required": [
      "PASS",
      "FAIL",
      "BLOCKED",
      "Challenge Level"
    ],
    "workflow_markers": [
      "QA → Tech Lead",
      "QA → Developer"
    ]
  },

  "tech_lead": {
    "required": [
      "APPROVED",
      "CHANGES_REQUESTED",
      "SPAWN_INVESTIGATOR"
    ],
    "workflow_markers": [
      "Tech Lead → PM",
      "Tech Lead → Developer"
    ]
  },

  "project_manager": {
    "required": [
      "BAZINGA",
      "SCOPE IS IMMUTABLE",
      "CONTINUE",
      "NEEDS_CLARIFICATION",
      "PLANNING_COMPLETE"
    ],
    "workflow_markers": [
      "PM → Developer",
      "only YOU decide when the entire project is complete"
    ]
  },

  "investigator": {
    "required": [
      "ROOT_CAUSE_FOUND",
      "BLOCKED"
    ],
    "workflow_markers": [
      "Investigator → Developer",
      "Investigator → Tech Lead"
    ]
  },

  "requirements_engineer": {
    "required": [
      "READY_FOR_REVIEW",
      "BLOCKED"
    ],
    "workflow_markers": [
      "RE → Tech Lead",
      "bypasses QA"
    ]
  }
}
```

---

## Part 4: Database Schema Changes

### New Tables to Add

```sql
-- Add to bazinga-db init_db.py

-- Table: workflow_transitions
-- Seeded from bazinga/config/transitions.json at session start
CREATE TABLE IF NOT EXISTS workflow_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_agent TEXT NOT NULL,
    response_status TEXT NOT NULL,
    next_agent TEXT,
    action TEXT NOT NULL,
    include_context TEXT,  -- JSON array
    escalation_check INTEGER DEFAULT 0,
    model_override TEXT,
    fallback_agent TEXT,
    bypass_qa INTEGER DEFAULT 0,
    max_parallel INTEGER,
    then_action TEXT,
    UNIQUE(current_agent, response_status)
);

-- Table: agent_markers
-- Seeded from bazinga/config/agent-markers.json at session start
CREATE TABLE IF NOT EXISTS agent_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL UNIQUE,
    required_markers TEXT NOT NULL,  -- JSON array
    workflow_markers TEXT  -- JSON array
);

-- Table: special_rules
-- Seeded from transitions.json _special_rules at session start
CREATE TABLE IF NOT EXISTS workflow_special_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    description TEXT,
    config TEXT NOT NULL  -- JSON object
);
```

### Commands to Add to bazinga-db

```
# New commands for config seeding
seed-transitions       - Seed transitions from JSON to DB
seed-markers          - Seed markers from JSON to DB
seed-special-rules    - Seed special rules from JSON to DB
seed-all-configs      - Seed all configs (runs all three above)

# New commands for reading
get-transition {current_agent} {status}  - Get single transition
get-markers {agent_type}                 - Get markers for agent
get-special-rule {rule_name}             - Get special rule

# New commands for prompt building support
get-agent-file-path {agent_type}         - Returns path to agent .md file
validate-prompt-markers {agent_type} {prompt_hash}  - Validate markers present
```

---

## Part 5: Python Scripts

### 5.1 `bazinga/scripts/seed_configs.py`

```python
#!/usr/bin/env python3
"""
Seeds JSON configuration files into the database.
Called by orchestrator at session initialization.

Usage:
    python3 bazinga/scripts/seed_configs.py [--transitions] [--markers] [--rules] [--all]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = "bazinga/bazinga.db"
CONFIG_DIR = Path("bazinga/config")


def seed_transitions(conn):
    """Seed workflow transitions from JSON."""
    config_path = CONFIG_DIR / "transitions.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path) as f:
        data = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM workflow_transitions")

    count = 0
    for agent, statuses in data.items():
        if agent.startswith("_"):  # Skip metadata keys
            continue
        for status, config in statuses.items():
            cursor.execute("""
                INSERT INTO workflow_transitions
                (current_agent, response_status, next_agent, action, include_context,
                 escalation_check, model_override, fallback_agent, bypass_qa, max_parallel, then_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent,
                status,
                config.get("next_agent"),
                config.get("action"),
                json.dumps(config.get("include_context", [])),
                1 if config.get("escalation_check") else 0,
                config.get("model_override"),
                config.get("fallback_agent"),
                1 if config.get("bypass_qa") else 0,
                config.get("max_parallel"),
                config.get("then")
            ))
            count += 1

    conn.commit()
    print(f"Seeded {count} transitions")
    return True


def seed_markers(conn):
    """Seed agent markers from JSON."""
    config_path = CONFIG_DIR / "agent-markers.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path) as f:
        data = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM agent_markers")

    count = 0
    for agent, config in data.items():
        if agent.startswith("_"):
            continue
        cursor.execute("""
            INSERT INTO agent_markers (agent_type, required_markers, workflow_markers)
            VALUES (?, ?, ?)
        """, (
            agent,
            json.dumps(config.get("required", [])),
            json.dumps(config.get("workflow_markers", []))
        ))
        count += 1

    conn.commit()
    print(f"Seeded {count} agent marker sets")
    return True


def seed_special_rules(conn):
    """Seed special rules from transitions.json _special_rules."""
    config_path = CONFIG_DIR / "transitions.json"
    if not config_path.exists():
        return False

    with open(config_path) as f:
        data = json.load(f)

    rules = data.get("_special_rules", {})
    if not rules:
        print("No special rules found")
        return True

    cursor = conn.cursor()
    cursor.execute("DELETE FROM workflow_special_rules")

    count = 0
    for rule_name, config in rules.items():
        cursor.execute("""
            INSERT INTO workflow_special_rules (rule_name, description, config)
            VALUES (?, ?, ?)
        """, (
            rule_name,
            config.get("description", ""),
            json.dumps(config)
        ))
        count += 1

    conn.commit()
    print(f"Seeded {count} special rules")
    return True


def main():
    parser = argparse.ArgumentParser(description="Seed config files to database")
    parser.add_argument("--transitions", action="store_true", help="Seed transitions only")
    parser.add_argument("--markers", action="store_true", help="Seed markers only")
    parser.add_argument("--rules", action="store_true", help="Seed special rules only")
    parser.add_argument("--all", action="store_true", help="Seed all configs")
    args = parser.parse_args()

    # Default to --all if no specific flag
    if not (args.transitions or args.markers or args.rules):
        args.all = True

    conn = sqlite3.connect(DB_PATH)

    success = True
    if args.all or args.transitions:
        success = seed_transitions(conn) and success
    if args.all or args.markers:
        success = seed_markers(conn) and success
    if args.all or args.rules:
        success = seed_special_rules(conn) and success

    conn.close()

    if success:
        print("✅ Config seeding complete")
    else:
        print("❌ Config seeding had errors", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 5.2 `bazinga/scripts/prompt_builder.py` (UNIFIED - Does Everything)

```python
#!/usr/bin/env python3
"""
Deterministically builds agent prompts.
This script does ALL prompt composition - no LLM interpretation.

It queries the database for:
- Specializations (from task_groups.specializations)
- Context packages
- Error patterns
- Prior agent reasoning

Then reads from filesystem:
- Agent definition files (agents/*.md)
- Specialization templates (templates/specializations/*.md)

Usage:
    python3 bazinga/scripts/prompt_builder.py \
        --agent-type developer \
        --session-id "bazinga_xxx" \
        --group-id "AUTH" \
        --task-title "Implement auth" \
        --task-requirements "Create login endpoint" \
        --branch "main" \
        --mode "parallel" \
        --testing-mode "full"

Output:
    Complete prompt to stdout
    Metadata to stderr
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = "bazinga/bazinga.db"

AGENT_FILE_MAP = {
    "developer": "agents/developer.md",
    "senior_software_engineer": "agents/senior_software_engineer.md",
    "qa_expert": "agents/qa_expert.md",
    "tech_lead": "agents/techlead.md",
    "project_manager": "agents/project_manager.md",
    "investigator": "agents/investigator.md",
    "requirements_engineer": "agents/requirements_engineer.md",
}

# Minimum lines expected in each agent file (sanity check)
MIN_AGENT_LINES = {
    "developer": 1200,
    "senior_software_engineer": 1400,
    "qa_expert": 1000,
    "tech_lead": 800,
    "project_manager": 2000,
    "investigator": 500,
    "requirements_engineer": 600,
}

# Token budgets per model
TOKEN_BUDGETS = {
    "haiku": {"soft": 900, "hard": 1350},
    "sonnet": {"soft": 1800, "hard": 2700},
    "opus": {"soft": 2400, "hard": 3600},
}

# Context budget allocation by agent type
CONTEXT_ALLOCATION = {
    "developer": 0.20,
    "senior_software_engineer": 0.25,
    "qa_expert": 0.30,
    "tech_lead": 0.40,
    "investigator": 0.35,
    "project_manager": 0.10,
    "requirements_engineer": 0.25,
}


def estimate_tokens(text):
    """Rough token estimate (characters / 4)."""
    return len(text) // 4


def get_required_markers(conn, agent_type):
    """Read required markers from database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT required_markers FROM agent_markers WHERE agent_type = ?",
        (agent_type,)
    )
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return []


def validate_markers(prompt, markers, agent_type):
    """Ensure all required markers are present in prompt."""
    missing = [m for m in markers if m not in prompt]
    if missing:
        print(f"ERROR: Prompt for {agent_type} missing required markers: {missing}", file=sys.stderr)
        print(f"This means the agent file may be corrupted or incomplete.", file=sys.stderr)
        sys.exit(1)


def read_agent_file(agent_type):
    """Read the agent definition file."""
    file_path = AGENT_FILE_MAP.get(agent_type)
    if not file_path:
        print(f"ERROR: Unknown agent type: {agent_type}", file=sys.stderr)
        print(f"Valid types: {list(AGENT_FILE_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: Agent file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    lines = len(content.splitlines())

    min_lines = MIN_AGENT_LINES.get(agent_type, 500)
    if lines < min_lines:
        print(f"WARNING: Agent file {file_path} has only {lines} lines (expected {min_lines}+)", file=sys.stderr)

    return content


# =============================================================================
# SPECIALIZATION BUILDING (Replaces specialization-loader skill)
# =============================================================================

def get_task_group_specializations(conn, session_id, group_id):
    """Get specialization paths from task_groups table."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT specializations FROM task_groups WHERE session_id = ? AND id = ?",
        (session_id, group_id)
    )
    row = cursor.fetchone()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return []
    return []


def get_project_context():
    """Read project_context.json for version guards."""
    try:
        with open("bazinga/project_context.json") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def read_template_with_version_guards(template_path, project_context):
    """Read template file and apply version guards."""
    path = Path(template_path)
    if not path.exists():
        return ""

    content = path.read_text()

    # Simple version guard processing
    # Format: <!-- version: LANG OPERATOR VERSION -->
    # For now, include all content (version guards are a future enhancement)

    return content


def build_specialization_block(conn, session_id, group_id, agent_type, model="sonnet"):
    """Build the specialization block from templates."""
    spec_paths = get_task_group_specializations(conn, session_id, group_id)

    if not spec_paths:
        return ""  # No specializations for this task

    project_context = get_project_context()
    budget = TOKEN_BUDGETS.get(model, TOKEN_BUDGETS["sonnet"])

    # Collect template content
    templates_content = []
    total_tokens = 0

    for path in spec_paths:
        content = read_template_with_version_guards(path, project_context)
        if content:
            tokens = estimate_tokens(content)
            if total_tokens + tokens <= budget["soft"]:
                templates_content.append(content)
                total_tokens += tokens
            else:
                # Over budget - stop adding
                break

    if not templates_content:
        return ""

    # Compose the block
    block = """## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

"""
    block += "\n\n".join(templates_content)

    return block


# =============================================================================
# CONTEXT BUILDING (Replaces context-assembler skill)
# =============================================================================

def get_context_packages(conn, session_id, group_id, agent_type, limit=5):
    """Get context packages from database."""
    cursor = conn.cursor()

    # Query with priority ordering
    query = """
        SELECT id, file_path, priority, summary, group_id, created_at
        FROM context_packages
        WHERE session_id = ?
        AND (group_id = ? OR group_id IS NULL OR group_id = '')
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            created_at DESC
        LIMIT ?
    """
    cursor.execute(query, (session_id, group_id, limit))
    return cursor.fetchall()


def get_error_patterns(conn, session_id, limit=3):
    """Get relevant error patterns."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT signature_json, solution, confidence, occurrences
        FROM error_patterns
        WHERE session_id = ? AND confidence > 0.7
        ORDER BY confidence DESC, occurrences DESC
        LIMIT ?
    """, (session_id, limit))
    return cursor.fetchall()


def get_prior_reasoning(conn, session_id, group_id, agent_type):
    """Get prior agent reasoning for handoffs."""
    # Define which agents' reasoning is relevant for each target
    relevant_agents = {
        'qa_expert': ['developer', 'senior_software_engineer'],
        'tech_lead': ['developer', 'senior_software_engineer', 'qa_expert'],
        'senior_software_engineer': ['developer'],
        'investigator': ['developer', 'senior_software_engineer', 'qa_expert'],
        'developer': ['developer', 'qa_expert', 'tech_lead'],
    }

    agents_to_query = relevant_agents.get(agent_type, [])
    if not agents_to_query:
        return []

    cursor = conn.cursor()
    placeholders = ','.join('?' * len(agents_to_query))
    cursor.execute(f"""
        SELECT agent_type, phase, content, confidence_level, timestamp
        FROM agent_reasoning
        WHERE session_id = ?
        AND (group_id = ? OR group_id = 'global')
        AND agent_type IN ({placeholders})
        ORDER BY timestamp DESC
        LIMIT 5
    """, (session_id, group_id, *agents_to_query))
    return cursor.fetchall()


def build_context_block(conn, session_id, group_id, agent_type, model="sonnet"):
    """Build the context block from database."""
    budget = TOKEN_BUDGETS.get(model, TOKEN_BUDGETS["sonnet"])
    allocation = CONTEXT_ALLOCATION.get(agent_type, 0.20)
    context_budget = int(budget["soft"] * allocation)

    sections = []
    used_tokens = 0

    # 1. Context packages
    packages = get_context_packages(conn, session_id, group_id, agent_type)
    if packages:
        pkg_section = "### Relevant Context\n\n"
        for pkg_id, file_path, priority, summary, pkg_group, created in packages:
            if summary:
                # Truncate long summaries
                truncated = summary[:200] + "..." if len(summary) > 200 else summary
                line = f"**[{priority.upper()}]** {file_path}\n> {truncated}\n\n"
                line_tokens = estimate_tokens(line)
                if used_tokens + line_tokens <= context_budget:
                    pkg_section += line
                    used_tokens += line_tokens
        if pkg_section != "### Relevant Context\n\n":
            sections.append(pkg_section)

    # 2. Prior reasoning (for handoffs)
    if agent_type in ['qa_expert', 'tech_lead', 'senior_software_engineer', 'investigator']:
        reasoning = get_prior_reasoning(conn, session_id, group_id, agent_type)
        if reasoning:
            reason_section = "### Prior Agent Reasoning\n\n"
            for r_agent, r_phase, r_content, r_conf, r_time in reasoning:
                content_truncated = r_content[:300] if r_content else ""
                line = f"**[{r_agent}] {r_phase}:** {content_truncated}\n\n"
                line_tokens = estimate_tokens(line)
                if used_tokens + line_tokens <= context_budget:
                    reason_section += line
                    used_tokens += line_tokens
            if reason_section != "### Prior Agent Reasoning\n\n":
                sections.append(reason_section)

    # 3. Error patterns
    errors = get_error_patterns(conn, session_id)
    if errors:
        err_section = "### Known Error Patterns\n\n"
        for sig_json, solution, confidence, occurrences in errors:
            line = f"⚠️ **Known Issue**: {sig_json[:100]}\n> **Solution**: {solution[:200]}\n\n"
            line_tokens = estimate_tokens(line)
            if used_tokens + line_tokens <= context_budget:
                err_section += line
                used_tokens += line_tokens
        if err_section != "### Known Error Patterns\n\n":
            sections.append(err_section)

    if not sections:
        return ""

    return "## Context from Prior Work\n\n" + "\n".join(sections)


# =============================================================================
# TASK CONTEXT BUILDING
# =============================================================================

def build_task_context(args):
    """Build the task context section."""
    context = f"""
---

## Current Task Assignment

**SESSION:** {args.session_id}
**GROUP:** {args.group_id}
**MODE:** {args.mode.capitalize()}
**BRANCH:** {args.branch}

**TASK:** {args.task_title}

**REQUIREMENTS:**
{args.task_requirements}

**TESTING MODE:** {args.testing_mode}
**COMMIT TO:** {args.branch}
"""

    # Add status guidance based on agent type
    if args.agent_type in ["developer", "senior_software_engineer"]:
        context += "**REPORT STATUS:** READY_FOR_QA (if integration tests) or READY_FOR_REVIEW (if unit tests only) or BLOCKED\n"
    elif args.agent_type == "qa_expert":
        context += "**REPORT STATUS:** PASS, FAIL, or BLOCKED\n"
    elif args.agent_type == "tech_lead":
        context += "**REPORT STATUS:** APPROVED or CHANGES_REQUESTED\n"
    elif args.agent_type == "project_manager":
        context += "**REPORT STATUS:** PLANNING_COMPLETE, CONTINUE, BAZINGA, or NEEDS_CLARIFICATION\n"

    return context


def build_feedback_context(args):
    """Build feedback context for retries."""
    feedback = ""

    if args.qa_feedback:
        feedback += f"""
## Previous QA Feedback (FIX THESE ISSUES)

{args.qa_feedback}
"""

    if args.tl_feedback:
        feedback += f"""
## Tech Lead Feedback (ADDRESS THESE CONCERNS)

{args.tl_feedback}
"""

    if args.investigation_findings:
        feedback += f"""
## Investigation Findings

{args.investigation_findings}
"""

    return feedback


def build_pm_context(args):
    """Build special context for PM spawns."""
    if args.pm_state:
        try:
            pm_state = json.loads(args.pm_state)
            return f"""
## PM STATE (from database)

```json
{json.dumps(pm_state, indent=2)}
```
"""
        except json.JSONDecodeError:
            return f"""
## PM STATE

{args.pm_state}
"""
    return ""


def build_resume_context(args):
    """Build resume context for PM resume spawns."""
    if args.resume_context:
        return f"""
## RESUME CONTEXT

{args.resume_context}

## 🔴 SCOPE PRESERVATION (MANDATORY)

You are resuming an existing session. The original scope MUST be preserved.
Do NOT reduce scope without explicit user approval.
"""
    return ""


# =============================================================================
# MAIN PROMPT COMPOSITION
# =============================================================================

def build_prompt(args):
    """Build the complete agent prompt."""
    conn = sqlite3.connect(DB_PATH)

    model = args.model or "sonnet"
    components = []

    # 1. Build CONTEXT block (from DB - prior reasoning, packages, errors)
    if args.agent_type != "project_manager":  # PM doesn't need prior context
        context_block = build_context_block(
            conn, args.session_id, args.group_id, args.agent_type, model
        )
        if context_block:
            components.append(context_block)

    # 2. Build SPECIALIZATION block (from DB task_groups + template files)
    if args.group_id and args.agent_type not in ["project_manager"]:
        spec_block = build_specialization_block(
            conn, args.session_id, args.group_id, args.agent_type, model
        )
        if spec_block:
            components.append(spec_block)

    # 3. Read AGENT DEFINITION (MANDATORY - this is the core)
    agent_definition = read_agent_file(args.agent_type)
    components.append(agent_definition)

    # 4. Build TASK CONTEXT
    task_context = build_task_context(args)
    components.append(task_context)

    # 5. Build PM-specific context
    if args.agent_type == "project_manager":
        pm_context = build_pm_context(args)
        if pm_context:
            components.append(pm_context)
        resume_context = build_resume_context(args)
        if resume_context:
            components.append(resume_context)

    # 6. Build FEEDBACK context (for retries)
    feedback_context = build_feedback_context(args)
    if feedback_context:
        components.append(feedback_context)

    # Compose final prompt
    full_prompt = "\n\n".join(components)

    # 7. Validate required markers
    markers = get_required_markers(conn, args.agent_type)
    if markers:
        validate_markers(full_prompt, markers, args.agent_type)

    conn.close()

    # 8. Output prompt to stdout
    print(full_prompt)

    # 9. Output metadata to stderr
    lines = len(full_prompt.splitlines())
    tokens = estimate_tokens(full_prompt)
    print(f"[PROMPT_METADATA]", file=sys.stderr)
    print(f"agent_type={args.agent_type}", file=sys.stderr)
    print(f"lines={lines}", file=sys.stderr)
    print(f"tokens_estimate={tokens}", file=sys.stderr)
    print(f"markers_validated={len(markers)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Build deterministic agent prompts")

    # Required arguments
    parser.add_argument("--agent-type", required=True,
                        choices=list(AGENT_FILE_MAP.keys()),
                        help="Type of agent to build prompt for")
    parser.add_argument("--session-id", required=True,
                        help="Session identifier")
    parser.add_argument("--branch", required=True,
                        help="Git branch name")
    parser.add_argument("--mode", required=True,
                        choices=["simple", "parallel"],
                        help="Execution mode")
    parser.add_argument("--testing-mode", required=True,
                        choices=["full", "minimal", "disabled"],
                        help="Testing mode")

    # Conditional arguments
    parser.add_argument("--group-id", default="",
                        help="Task group identifier")
    parser.add_argument("--task-title", default="",
                        help="Task title")
    parser.add_argument("--task-requirements", default="",
                        help="Task requirements")
    parser.add_argument("--model", default="sonnet",
                        choices=["haiku", "sonnet", "opus"],
                        help="Model for token budgeting")

    # Feedback for retries
    parser.add_argument("--qa-feedback", default="",
                        help="QA failure details for developer retry")
    parser.add_argument("--tl-feedback", default="",
                        help="Tech Lead feedback for developer changes")
    parser.add_argument("--investigation-findings", default="",
                        help="Investigation findings")

    # PM-specific
    parser.add_argument("--pm-state", default="",
                        help="PM state JSON from database")
    parser.add_argument("--resume-context", default="",
                        help="Resume context for PM resume spawns")

    args = parser.parse_args()
    build_prompt(args)


if __name__ == "__main__":
    main()
```

### 5.3 `bazinga/scripts/workflow_router.py`

```python
#!/usr/bin/env python3
"""
Deterministically routes to next agent based on current state.

Usage:
    python3 bazinga/scripts/workflow_router.py \
        --current-agent developer \
        --status READY_FOR_QA \
        --session-id "bazinga_xxx" \
        --group-id "AUTH" \
        --testing-mode full

Output:
    JSON with next action to stdout
"""

import argparse
import json
import sqlite3
import sys

DB_PATH = "bazinga/bazinga.db"

MODEL_CONFIG = {
    "developer": "haiku",
    "senior_software_engineer": "sonnet",
    "qa_expert": "sonnet",
    "tech_lead": "opus",
    "project_manager": "opus",
    "investigator": "opus",
    "requirements_engineer": "opus",
}


def get_transition(conn, current_agent, status):
    """Get transition from database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT next_agent, action, include_context, escalation_check,
               model_override, fallback_agent, bypass_qa, max_parallel, then_action
        FROM workflow_transitions
        WHERE current_agent = ? AND response_status = ?
    """, (current_agent, status))
    row = cursor.fetchone()

    if row:
        return {
            "next_agent": row[0],
            "action": row[1],
            "include_context": json.loads(row[2]) if row[2] else [],
            "escalation_check": bool(row[3]),
            "model_override": row[4],
            "fallback_agent": row[5],
            "bypass_qa": bool(row[6]),
            "max_parallel": row[7],
            "then_action": row[8],
        }
    return None


def get_special_rule(conn, rule_name):
    """Get special rule from database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT config FROM workflow_special_rules WHERE rule_name = ?",
        (rule_name,)
    )
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return None


def get_revision_count(conn, session_id, group_id):
    """Get revision count for a group."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT revision_count FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    return row[0] if row else 0


def get_pending_groups(conn, session_id):
    """Get list of pending groups."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM task_groups
        WHERE session_id = ? AND status = 'pending'
    """, (session_id,))
    return [row[0] for row in cursor.fetchall()]


def get_in_progress_groups(conn, session_id):
    """Get list of in-progress groups."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM task_groups
        WHERE session_id = ? AND status = 'in_progress'
    """, (session_id,))
    return [row[0] for row in cursor.fetchall()]


def check_security_sensitive(conn, session_id, group_id):
    """Check if task is security sensitive."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT description FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    if row and row[0]:
        desc = row[0].lower()
        return "security" in desc or "security_sensitive" in desc
    return False


def route(args):
    """Determine next action based on state."""
    conn = sqlite3.connect(DB_PATH)

    # Get base transition
    transition = get_transition(conn, args.current_agent, args.status)

    if not transition:
        result = {
            "success": False,
            "error": f"Unknown transition: {args.current_agent} + {args.status}",
            "suggestion": "Route to tech_lead for manual handling",
            "fallback_action": {
                "next_agent": "tech_lead",
                "action": "spawn",
                "reason": "Unknown status - escalating for guidance"
            }
        }
        print(json.dumps(result, indent=2))
        conn.close()
        sys.exit(1)

    next_agent = transition["next_agent"]
    action = transition["action"]

    # Apply testing mode rules
    if args.testing_mode in ["disabled", "minimal"]:
        if next_agent == "qa_expert":
            next_agent = "tech_lead"
            action = "spawn"
            transition["skip_reason"] = f"QA skipped (testing_mode={args.testing_mode})"

    # Apply escalation rules
    if transition.get("escalation_check"):
        revision_count = get_revision_count(conn, args.session_id, args.group_id)
        escalation_rule = get_special_rule(conn, "escalation_after_failures")
        threshold = escalation_rule.get("threshold", 2) if escalation_rule else 2

        if revision_count >= threshold:
            next_agent = "senior_software_engineer"
            action = "spawn"
            transition["escalation_applied"] = True
            transition["escalation_reason"] = f"Escalated after {revision_count} failures"

    # Apply security sensitive rules
    if check_security_sensitive(conn, args.session_id, args.group_id):
        security_rule = get_special_rule(conn, "security_sensitive")
        if security_rule and args.current_agent == "developer":
            # Force SSE for security tasks
            if next_agent == "developer":
                next_agent = "senior_software_engineer"
            transition["security_override"] = True

    # Handle batch spawns
    groups_to_spawn = []
    if action == "spawn_batch":
        pending = get_pending_groups(conn, args.session_id)
        max_parallel = transition.get("max_parallel", 4)
        groups_to_spawn = pending[:max_parallel]

    # Handle phase check (after merge)
    if transition.get("then_action") == "check_phase":
        pending = get_pending_groups(conn, args.session_id)
        in_progress = get_in_progress_groups(conn, args.session_id)

        if pending or in_progress:
            # More work to do
            transition["phase_check"] = "continue"
            if pending:
                groups_to_spawn = pending[:4]
        else:
            # All complete - route to PM
            next_agent = "project_manager"
            action = "spawn"
            transition["phase_check"] = "complete"

    # Determine model
    model = transition.get("model_override") or MODEL_CONFIG.get(next_agent, "sonnet")

    # Build result
    result = {
        "success": True,
        "current_agent": args.current_agent,
        "response_status": args.status,
        "next_agent": next_agent,
        "action": action,
        "model": model,
        "group_id": args.group_id,
        "session_id": args.session_id,
        "include_context": transition.get("include_context", []),
    }

    # Add batch spawn info if applicable
    if groups_to_spawn:
        result["groups_to_spawn"] = groups_to_spawn

    # Add any special flags
    if transition.get("bypass_qa"):
        result["bypass_qa"] = True
    if transition.get("escalation_applied"):
        result["escalation_applied"] = True
        result["escalation_reason"] = transition.get("escalation_reason")
    if transition.get("skip_reason"):
        result["skip_reason"] = transition.get("skip_reason")
    if transition.get("phase_check"):
        result["phase_check"] = transition.get("phase_check")
    if transition.get("security_override"):
        result["security_override"] = True

    print(json.dumps(result, indent=2))
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Deterministic workflow routing")

    parser.add_argument("--current-agent", required=True,
                        help="Agent that just responded")
    parser.add_argument("--status", required=True,
                        help="Status code from agent response")
    parser.add_argument("--session-id", required=True,
                        help="Session identifier")
    parser.add_argument("--group-id", required=True,
                        help="Current group ID")
    parser.add_argument("--testing-mode", default="full",
                        choices=["full", "minimal", "disabled"],
                        help="Testing mode")

    args = parser.parse_args()
    route(args)


if __name__ == "__main__":
    main()
```

---

## Part 6: Skills Definitions

### 6.1 `prompt-builder` Skill (Thin Wrapper)

**Location:** `.claude/skills/prompt-builder/SKILL.md`

```markdown
---
name: prompt-builder
description: Builds complete agent prompts deterministically via Python script. Call this before spawning ANY agent.
version: 2.0.0
allowed-tools: [Bash]
---

# Prompt Builder Skill

You build agent prompts by calling `prompt_builder.py`. This script handles EVERYTHING:
- Reads specializations from DB (task_groups.specializations)
- Reads context from DB (context_packages, error_patterns, reasoning)
- Reads agent definition files from filesystem
- Applies token budgets
- Validates required markers
- Returns complete prompt

## When to Invoke

**RIGHT BEFORE spawning ANY agent** (Developer, SSE, QA, Tech Lead, PM, Investigator, RE).

This is called ON-DEMAND to get the latest context from DB.

## Your Task

### Step 1: Extract Parameters from Orchestrator Context

- agent_type (required): developer, qa_expert, tech_lead, etc.
- session_id (required)
- group_id (required for non-PM)
- task_title
- task_requirements
- branch
- mode (simple/parallel)
- testing_mode (full/minimal/disabled)
- model (haiku/sonnet/opus)
- qa_feedback (if retry after QA failure)
- tl_feedback (if retry after Tech Lead changes)
- pm_state (for PM spawns)
- resume_context (for PM resume)

### Step 2: Call the Python Script

```bash
python3 bazinga/scripts/prompt_builder.py \
  --agent-type "{agent_type}" \
  --session-id "{session_id}" \
  --group-id "{group_id}" \
  --task-title "{task_title}" \
  --task-requirements "{task_requirements}" \
  --branch "{branch}" \
  --mode "{mode}" \
  --testing-mode "{testing_mode}" \
  --model "{model}" \
  --qa-feedback "{qa_feedback}" \
  --tl-feedback "{tl_feedback}" \
  --pm-state '{pm_state_json}' \
  --resume-context "{resume_context}"
```

### Step 3: Return the Output

- stdout = Complete prompt (return this to orchestrator)
- stderr = Metadata (for logging)

## What the Script Does Internally

1. Queries DB for `task_groups.specializations` → reads template files
2. Queries DB for `context_packages`, `error_patterns`, `agent_reasoning`
3. Reads full agent definition file (`agents/*.md`)
4. Applies token budgets per model
5. Validates required markers are present
6. Returns composed prompt

## Error Handling

| Error | Meaning |
|-------|---------|
| Exit code 1 + "missing markers" | Agent file corrupted/incomplete |
| Exit code 1 + "file not found" | Agent file missing |
| Exit code 1 + "unknown agent type" | Invalid agent_type parameter |
```

### 6.2 `workflow-router` Skill

**Location:** `.claude/skills/workflow-router/SKILL.md`

```markdown
---
name: workflow-router
description: Determines next agent based on state machine rules. Call after receiving ANY agent response.
version: 1.0.0
allowed-tools: [Bash]
---

# Workflow Router Skill

You determine the next action by calling `workflow_router.py`.

## When to Invoke

**After receiving ANY agent response**, to determine what to do next.

## Your Task

### Step 1: Extract Parameters

- current_agent: Agent that just responded (developer, qa_expert, etc.)
- status: Status code from response (READY_FOR_QA, PASS, APPROVED, etc.)
- session_id
- group_id
- testing_mode

### Step 2: Call the Script

```bash
python3 bazinga/scripts/workflow_router.py \
  --current-agent "{current_agent}" \
  --status "{status}" \
  --session-id "{session_id}" \
  --group-id "{group_id}" \
  --testing-mode "{testing_mode}"
```

### Step 3: Return JSON Result

The script outputs JSON:
```json
{
  "success": true,
  "next_agent": "qa_expert",
  "action": "spawn",
  "model": "sonnet",
  "include_context": ["dev_output", "test_results"],
  "groups_to_spawn": ["AUTH", "API"]
}
```

## Actions Explained

| Action | What to Do |
|--------|------------|
| `spawn` | Spawn single agent (use prompt-builder first) |
| `spawn_batch` | Spawn multiple developers for `groups_to_spawn` |
| `respawn` | Re-spawn same agent type with feedback |
| `validate_then_end` | Run bazinga-validator, then end session |
| `pause_for_user` | Surface clarification question to user |
| `end_session` | Mark session complete |
```

### 6.3 `config-seeder` Skill

**Location:** `.claude/skills/config-seeder/SKILL.md`

```markdown
---
name: config-seeder
description: Seeds JSON configuration files into database. Run once at session initialization.
version: 1.0.0
allowed-tools: [Bash]
---

# Config Seeder Skill

Seeds JSON config files into database tables.

## When to Invoke

**Once at session start**, BEFORE spawning PM.

## Your Task

```bash
python3 bazinga/scripts/seed_configs.py --all
```

## What Gets Seeded

1. `bazinga/config/transitions.json` → `workflow_transitions` table
2. `bazinga/config/agent-markers.json` → `agent_markers` table
3. `_special_rules` → `workflow_special_rules` table

## Success Output

```
Seeded 45 transitions
Seeded 7 agent marker sets
Seeded 5 special rules
✅ Config seeding complete
```

## Error Handling

If JSON files not found, orchestration CANNOT proceed.
```

---

## Part 7: Changes to Orchestrator

### 7.1 Initialization Changes

Add to orchestrator initialization (after session creation, before PM spawn):

```markdown
## Step 0.3: Seed Configuration to Database

**Invoke config-seeder skill:**

```
Skill(command: "config-seeder")
```

This seeds transitions.json and agent-markers.json into database tables.
Must complete before any agent spawns.

**If seeding fails:** STOP - cannot proceed without routing config.
```

### 7.2 Agent Spawning Changes (SIMPLIFIED)

Replace ALL prompt composition logic with:

```markdown
## Spawning ANY Agent

**Step 1: Invoke prompt-builder**

Provide context in your message:
```
Build prompt for:
- Agent Type: {agent_type}
- Session ID: {session_id}
- Group ID: {group_id}
- Task Title: {title}
- Task Requirements: {requirements}
- Branch: {branch}
- Mode: {mode}
- Testing Mode: {testing_mode}
- Model: {model}
- QA Feedback: {if retry after QA fail}
- TL Feedback: {if retry after changes requested}
- PM State: {for PM spawns}
- Resume Context: {for PM resume}
```

Then invoke:
```
Skill(command: "prompt-builder")
```

**Step 2: Spawn Agent**

Use the complete prompt from skill output:
```
Task(
  subagent_type: "general-purpose",
  model: {model},
  description: "{agent_type}: {task_title[:90]}",
  prompt: {COMPLETE_PROMPT from prompt-builder}
)
```

**Note:** The prompt-builder script queries DB for specializations and context
automatically - no need to invoke other skills first.
```

### 7.3 Routing Changes

Replace all routing logic with:

```markdown
## After Receiving Agent Response

**Step 1: Extract Status**

Parse agent response for status code (READY_FOR_QA, PASS, APPROVED, etc.)

**Step 2: Invoke workflow-router**

Provide context:
```
Route from:
- Current Agent: {agent_type}
- Status: {extracted_status}
- Session ID: {session_id}
- Group ID: {group_id}
- Testing Mode: {testing_mode}
```

Then invoke:
```
Skill(command: "workflow-router")
```

**Step 3: Execute Action**

Parse JSON result and execute:
- `spawn` → Go to "Spawning ANY Agent" with next_agent
- `spawn_batch` → Spawn developers for each group in groups_to_spawn
- `respawn` → Re-spawn with feedback
- `validate_then_end` → Invoke bazinga-validator skill
- `pause_for_user` → Surface clarification question
- `end_session` → Mark session complete
```

---

## Part 8: Updated Task List

### Phase 0: Preparation (Do First)

| # | Task | Description | Files |
|---|------|-------------|-------|
| 0.1 | Create config directory | `mkdir -p bazinga/config` | - |
| 0.2 | Create transitions.json | Full state machine config | `bazinga/config/transitions.json` |
| 0.3 | Create agent-markers.json | All agent markers | `bazinga/config/agent-markers.json` |
| 0.4 | Add to pyproject.toml | Include new files in package | `pyproject.toml` |

### Phase 1: Database Schema

| # | Task | Description | Files |
|---|------|-------------|-------|
| 1.1 | Add workflow_transitions table | Schema for transitions | `.claude/skills/bazinga-db/scripts/init_db.py` |
| 1.2 | Add agent_markers table | Schema for markers | `.claude/skills/bazinga-db/scripts/init_db.py` |
| 1.3 | Add workflow_special_rules table | Schema for special rules | `.claude/skills/bazinga-db/scripts/init_db.py` |
| 1.4 | Update schema.md | Document new tables | `.claude/skills/bazinga-db/references/schema.md` |
| 1.5 | Increment SCHEMA_VERSION | Bump to next version | `.claude/skills/bazinga-db/scripts/init_db.py` |

### Phase 2: Python Scripts

| # | Task | Description | Files |
|---|------|-------------|-------|
| 2.1 | Create seed_configs.py | Config seeding script | `bazinga/scripts/seed_configs.py` |
| 2.2 | Create prompt_builder.py | **UNIFIED** prompt building (does everything) | `bazinga/scripts/prompt_builder.py` |
| 2.3 | Create workflow_router.py | Routing script | `bazinga/scripts/workflow_router.py` |
| 2.4 | Test seed_configs.py | Verify seeding works | - |
| 2.5 | Test prompt_builder.py | Verify all agent types, DB queries | - |
| 2.6 | Test workflow_router.py | Verify all transitions | - |

### Phase 3: Skills (Thin Wrappers)

| # | Task | Description | Files |
|---|------|-------------|-------|
| 3.1 | Create prompt-builder skill directory | `mkdir -p .claude/skills/prompt-builder` | - |
| 3.2 | Create prompt-builder SKILL.md | Thin wrapper that calls script | `.claude/skills/prompt-builder/SKILL.md` |
| 3.3 | Create workflow-router skill directory | `mkdir -p .claude/skills/workflow-router` | - |
| 3.4 | Create workflow-router SKILL.md | Thin wrapper that calls script | `.claude/skills/workflow-router/SKILL.md` |
| 3.5 | Create config-seeder skill directory | `mkdir -p .claude/skills/config-seeder` | - |
| 3.6 | Create config-seeder SKILL.md | Calls seed_configs.py | `.claude/skills/config-seeder/SKILL.md` |

### Phase 4: Orchestrator Updates

| # | Task | Description | Files |
|---|------|-------------|-------|
| 4.1 | Add config seeding step | Step 0.3 in initialization | `agents/orchestrator.md` |
| 4.2 | Update PM spawn (new session) | Use prompt-builder skill only | `agents/orchestrator.md` |
| 4.3 | Update PM spawn (resume) | Use prompt-builder skill only | `agents/orchestrator.md` |
| 4.4 | Update Developer spawn (simple) | Use prompt-builder skill only | `templates/orchestrator/phase_simple.md` |
| 4.5 | Update Developer spawn (parallel) | Use prompt-builder skill only | `templates/orchestrator/phase_parallel.md` |
| 4.6 | Update QA spawn | Use prompt-builder skill only | `templates/orchestrator/phase_simple.md`, `phase_parallel.md` |
| 4.7 | Update Tech Lead spawn | Use prompt-builder skill only | `templates/orchestrator/phase_simple.md`, `phase_parallel.md` |
| 4.8 | Add workflow-router calls | Replace all routing logic | `templates/orchestrator/phase_simple.md`, `phase_parallel.md` |
| 4.9 | Remove old prompt composition | Clean up duplicated logic | Various |

### Phase 5: Testing

| # | Task | Description | Files |
|---|------|-------------|-------|
| 5.1 | Create unit tests for seed_configs.py | Test config seeding | `tests/unit/test_seed_configs.py` |
| 5.2 | Create unit tests for prompt_builder.py | Test all agent types + DB queries | `tests/unit/test_prompt_builder.py` |
| 5.3 | Create unit tests for workflow_router.py | Test all transitions | `tests/unit/test_workflow_router.py` |
| 5.4 | Run integration test | Full orchestration test | - |
| 5.5 | Verify Developer prompt contains full file | Check line count ≥1200 | - |
| 5.6 | Verify PM resume includes full file | Original bug fix verified | - |
| 5.7 | Verify context accumulates | QA gets Dev reasoning, TL gets Dev+QA | - |

### Phase 6: Documentation & Cleanup

| # | Task | Description | Files |
|---|------|-------------|-------|
| 6.1 | Update prompt_building.md | Remove old instructions | `templates/prompt_building.md` |
| 6.2 | Update claude.md | Add deterministic system docs | `.claude/claude.md` |
| 6.3 | Remove old prompt composition code | Clean up templates | Various |
| 6.4 | Update specialization-loader SKILL.md | Document that prompt-builder replaces it for spawns | `.claude/skills/specialization-loader/SKILL.md` |
| 6.5 | Update context-assembler SKILL.md | Document that prompt-builder replaces it for spawns | `.claude/skills/context-assembler/SKILL.md` |

---

## Part 9: Verification Checklist

After implementation, verify:

**Configuration:**
- [ ] `bazinga/config/transitions.json` exists with all 45+ transitions
- [ ] `bazinga/config/agent-markers.json` exists with all 7 agents
- [ ] Files included in pyproject.toml for installation

**Database:**
- [ ] `workflow_transitions` table created
- [ ] `agent_markers` table created
- [ ] `workflow_special_rules` table created
- [ ] SCHEMA_VERSION incremented

**Scripts:**
- [ ] `seed_configs.py` runs without errors
- [ ] `prompt_builder.py` outputs complete prompts for all 7 agent types
- [ ] `prompt_builder.py` queries DB for specializations
- [ ] `prompt_builder.py` queries DB for context/reasoning
- [ ] `workflow_router.py` returns correct next actions

**Skills:**
- [ ] `prompt-builder` skill invokes script correctly
- [ ] `workflow-router` skill invokes script correctly
- [ ] `config-seeder` skill invokes script correctly

**Orchestrator:**
- [ ] Config seeding happens at init
- [ ] All agent spawns use prompt-builder skill ONLY
- [ ] All routing uses workflow-router skill
- [ ] No direct calls to specialization-loader or context-assembler for spawns

**Integration:**
- [ ] Integration test passes
- [ ] Developer prompt includes full agent file (1200+ lines)
- [ ] PM resume prompt includes full agent file (2000+ lines)
- [ ] QA prompt includes Developer reasoning (context accumulated)
- [ ] Tech Lead prompt includes Dev + QA reasoning

---

## Part 10: Migration Notes

### What Gets Replaced

| Old Pattern | New Pattern |
|-------------|-------------|
| Orchestrator calls specialization-loader | prompt_builder.py queries DB + reads templates |
| Orchestrator calls context-assembler | prompt_builder.py queries DB |
| Orchestrator composes prompt inline | Orchestrator calls prompt-builder skill |
| LLM interprets routing rules | workflow_router.py reads transitions from DB |

### Backward Compatibility

- `specialization-loader` skill remains available for other uses
- `context-assembler` skill remains available for other uses
- Neither is REMOVED, just not called during agent spawns
- Skills can still be invoked directly if needed

### Rollback Plan

If issues arise:
1. Revert orchestrator to old pattern (call skills directly)
2. The skills still work independently
3. New DB tables don't affect old flow

---

## References

- Original bug analysis: `research/agent-prompt-composition-fix.md`
- Initial deterministic design: `research/deterministic-orchestration-system.md`
- Unified skill analysis: `research/unified-prompt-builder-skill.md`
- Agent files: `agents/*.md`
- Response parsing: `templates/response_parsing.md`
