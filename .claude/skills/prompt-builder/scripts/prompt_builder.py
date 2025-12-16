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
- Specialization templates (bazinga/templates/specializations/*.md)

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
import sqlite3
import sys
from pathlib import Path

# Database path - relative to project root
DB_PATH = "bazinga/bazinga.db"

# Agent file mapping
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
    "developer": 1000,
    "senior_software_engineer": 1200,
    "qa_expert": 800,
    "tech_lead": 600,
    "project_manager": 1800,
    "investigator": 400,
    "requirements_engineer": 500,
}

# Token budgets per model
TOKEN_BUDGETS = {
    "haiku": {"soft": 900, "hard": 1350},
    "sonnet": {"soft": 1800, "hard": 2700},
    "opus": {"soft": 2400, "hard": 3600},
}

# Context budget allocation by agent type
# Increased developer from 0.20 to 0.35 (haiku 900 * 0.35 = 315 tokens for context)
CONTEXT_ALLOCATION = {
    "developer": 0.35,
    "senior_software_engineer": 0.30,
    "qa_expert": 0.30,
    "tech_lead": 0.40,
    "investigator": 0.35,
    "project_manager": 0.10,
    "requirements_engineer": 0.30,
}


def estimate_tokens(text):
    """Rough token estimate (characters / 4)."""
    return len(text) // 4


def get_required_markers(conn, agent_type):
    """Read required markers from database."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT required_markers FROM agent_markers WHERE agent_type = ?",
            (agent_type,)
        )
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return []
        return []
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (agent_markers): {e}", file=sys.stderr)
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

    min_lines = MIN_AGENT_LINES.get(agent_type, 400)
    if lines < min_lines:
        print(f"WARNING: Agent file {file_path} has only {lines} lines (expected {min_lines}+)", file=sys.stderr)

    return content


# =============================================================================
# SPECIALIZATION BUILDING (Replaces specialization-loader skill)
# =============================================================================

def get_task_group_specializations(conn, session_id, group_id):
    """Get specialization paths from task_groups table."""
    try:
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
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (task_groups): {e}", file=sys.stderr)
        return []


def get_project_context():
    """Read project_context.json for version guards."""
    try:
        with open("bazinga/project_context.json") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def validate_template_path(template_path):
    """Validate that template path is safe (no path traversal)."""
    ALLOWED_BASE = Path("bazinga/templates/specializations").resolve()

    # Reject absolute paths
    if Path(template_path).is_absolute():
        print(f"WARNING: Rejecting absolute template path: {template_path}", file=sys.stderr)
        return None

    # Reject paths with parent traversal
    if ".." in str(template_path):
        print(f"WARNING: Rejecting path with traversal: {template_path}", file=sys.stderr)
        return None

    # Resolve and check it's under allowed base
    resolved = Path(template_path).resolve()
    try:
        resolved.relative_to(ALLOWED_BASE)
        return resolved
    except ValueError:
        print(f"WARNING: Template path outside allowed directory: {template_path}", file=sys.stderr)
        return None


def read_template_with_version_guards(template_path, project_context):
    """Read template file and apply version guards (with path validation)."""
    # Validate path for security
    validated_path = validate_template_path(template_path)
    if validated_path is None:
        return ""

    if not validated_path.exists():
        return ""

    try:
        content = validated_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IOError) as e:
        print(f"WARNING: Failed to read template {template_path}: {e}", file=sys.stderr)
        return ""

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
    try:
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
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (context_packages): {e}", file=sys.stderr)
        return []


def get_error_patterns(conn, session_id, limit=3):
    """Get relevant error patterns."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT signature_json, solution, confidence, occurrences
            FROM error_patterns
            WHERE confidence > 0.7
            ORDER BY confidence DESC, occurrences DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (error_patterns): {e}", file=sys.stderr)
        return []


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

    try:
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(agents_to_query))
        cursor.execute(f"""
            SELECT agent_type, reasoning_phase, content, confidence_level, timestamp
            FROM orchestration_logs
            WHERE session_id = ?
            AND (group_id = ? OR group_id = 'global')
            AND agent_type IN ({placeholders})
            AND log_type = 'reasoning'
            ORDER BY timestamp DESC
            LIMIT 5
        """, (session_id, group_id, *agents_to_query))
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (orchestration_logs): {e}", file=sys.stderr)
        return []


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
            sig_str = sig_json[:100] if sig_json else ""
            sol_str = solution[:200] if solution else ""
            line = f"**Known Issue**: {sig_str}\n> **Solution**: {sol_str}\n\n"
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
**GROUP:** {args.group_id or 'N/A'}
**MODE:** {args.mode.capitalize()}
**BRANCH:** {args.branch}

**TASK:** {args.task_title or 'See requirements below'}

**REQUIREMENTS:**
{args.task_requirements or 'See original request'}

**TESTING MODE:** {args.testing_mode}
**COMMIT TO:** {args.branch}
"""

    # Add status guidance based on agent type
    if args.agent_type in ["developer", "senior_software_engineer"]:
        context += "\n**REPORT STATUS:** READY_FOR_QA (if integration tests) or READY_FOR_REVIEW (if unit tests only) or BLOCKED\n"
    elif args.agent_type == "qa_expert":
        context += "\n**REPORT STATUS:** PASS, FAIL, or BLOCKED\n"
    elif args.agent_type == "tech_lead":
        context += "\n**REPORT STATUS:** APPROVED or CHANGES_REQUESTED\n"
    elif args.agent_type == "project_manager":
        context += "\n**REPORT STATUS:** PLANNING_COMPLETE, CONTINUE, BAZINGA, or NEEDS_CLARIFICATION\n"

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

## SCOPE PRESERVATION (MANDATORY)

You are resuming an existing session. The original scope MUST be preserved.
Do NOT reduce scope without explicit user approval.
"""
    return ""


# =============================================================================
# MAIN PROMPT COMPOSITION
# =============================================================================

def build_prompt(args):
    """Build the complete agent prompt."""
    # Check database exists
    if not Path(args.db).exists():
        print(f"WARNING: Database not found at {args.db}, proceeding without DB data", file=sys.stderr)
        conn = None
    else:
        conn = sqlite3.connect(args.db)

    model = args.model or "sonnet"
    components = []

    # 1. Build CONTEXT block (from DB - prior reasoning, packages, errors)
    if conn and args.agent_type != "project_manager":  # PM doesn't need prior context
        context_block = build_context_block(
            conn, args.session_id, args.group_id or "", args.agent_type, model
        )
        if context_block:
            components.append(context_block)

    # 2. Build SPECIALIZATION block (from DB task_groups + template files)
    if conn and args.group_id and args.agent_type not in ["project_manager"]:
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

    # 7. Validate required markers (only if DB available)
    if conn:
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
    if conn:
        print(f"markers_validated=true", file=sys.stderr)


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
    parser.add_argument("--db", default=DB_PATH,
                        help="Database path")

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
