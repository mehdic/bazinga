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
    python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
        --agent-type developer \
        --session-id "bazinga_xxx" \
        --group-id "AUTH" \
        --task-title "Implement auth" \
        --task-requirements "Create login endpoint" \
        --branch "main" \
        --mode "parallel" \
        --testing-mode "full"

Output:
    Complete prompt to stdout (only on success)
    Metadata to stderr
    Exit code 0 on success, 1 on validation failure
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


def get_project_root():
    """Detect project root by looking for .claude directory or bazinga directory.

    Returns:
        Path to project root, or current working directory if not found.
    """
    # Start from script location and traverse up
    script_dir = Path(__file__).resolve().parent

    # Look for project markers going up from script location
    current = script_dir
    for _ in range(10):  # Max 10 levels up
        if (current / ".claude").is_dir() or (current / "bazinga").is_dir():
            return current
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    # Fallback: check CWD
    cwd = Path.cwd()
    if (cwd / ".claude").is_dir() or (cwd / "bazinga").is_dir():
        return cwd

    # Last resort: use CWD and hope for the best
    return cwd


# Detect project root once at module load
PROJECT_ROOT = get_project_root()

# Database path - relative to project root
DB_PATH = str(PROJECT_ROOT / "bazinga" / "bazinga.db")

# Agent file mapping (relative to PROJECT_ROOT)
AGENT_FILE_MAP = {
    "developer": "agents/developer.md",
    "senior_software_engineer": "agents/senior_software_engineer.md",
    "qa_expert": "agents/qa_expert.md",
    "tech_lead": "agents/techlead.md",
    "project_manager": "agents/project_manager.md",
    "investigator": "agents/investigator.md",
    "requirements_engineer": "agents/requirements_engineer.md",
}

# Specialization templates base directory
SPECIALIZATIONS_BASE = PROJECT_ROOT / "bazinga" / "templates" / "specializations"

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
    """Ensure all required markers are present in prompt.

    Returns:
        True if all markers present, False if missing (caller should handle exit)
    """
    missing = [m for m in markers if m not in prompt]
    if missing:
        print(f"ERROR: Prompt for {agent_type} missing required markers: {missing}", file=sys.stderr)
        print(f"This means the agent file may be corrupted or incomplete.", file=sys.stderr)
        return False
    return True


def read_agent_file(agent_type):
    """Read the agent definition file."""
    file_path = AGENT_FILE_MAP.get(agent_type)
    if not file_path:
        print(f"ERROR: Unknown agent type: {agent_type}", file=sys.stderr)
        print(f"Valid types: {list(AGENT_FILE_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    path = PROJECT_ROOT / file_path
    if not path.exists():
        print(f"ERROR: Agent file not found: {path}", file=sys.stderr)
        print(f"Project root: {PROJECT_ROOT}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    lines = len(content.splitlines())

    min_lines = MIN_AGENT_LINES.get(agent_type, 400)
    if lines < min_lines:
        print(f"WARNING: Agent file {path} has only {lines} lines (expected {min_lines}+)", file=sys.stderr)

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
    context_path = PROJECT_ROOT / "bazinga" / "project_context.json"
    try:
        with open(context_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def validate_template_path(template_path):
    """Validate that template path is safe (no path traversal)."""
    allowed_base = SPECIALIZATIONS_BASE.resolve()

    # Reject absolute paths
    if Path(template_path).is_absolute():
        print(f"WARNING: Rejecting absolute template path: {template_path}", file=sys.stderr)
        return None

    # Reject paths with parent traversal
    if ".." in str(template_path):
        print(f"WARNING: Rejecting path with traversal: {template_path}", file=sys.stderr)
        return None

    # Resolve relative to project root and check it's under allowed base
    resolved = (PROJECT_ROOT / template_path).resolve()
    try:
        resolved.relative_to(allowed_base)
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


def get_error_patterns(conn, limit=3):
    """Get relevant error patterns.

    Note: Currently fetches global patterns. Per-session filtering can be added
    if error_patterns table gains session_id column.
    """
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

    # 3. Error patterns (global, not per-session)
    errors = get_error_patterns(conn)
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
# GLOBAL BUDGET ENFORCEMENT
# =============================================================================

def enforce_global_budget(components, model="sonnet"):
    """Enforce global token budget by trimming lowest-priority sections.

    Priority order (highest to lowest):
    1. Agent definition (NEVER trim)
    2. Task context (NEVER trim)
    3. PM context (NEVER trim if PM)
    4. Context block (trim if needed)
    5. Specialization block (trim if needed)
    6. Feedback context (trim first)

    Returns:
        tuple: (trimmed_components, trimmed_sections_log)
    """
    budget = TOKEN_BUDGETS.get(model, TOKEN_BUDGETS["sonnet"])
    hard_limit = budget["hard"]

    # Calculate total tokens
    total_tokens = sum(estimate_tokens(c) for c in components)

    if total_tokens <= hard_limit:
        return components, []

    # Need to trim - identify sections by content markers
    trimmed_log = []
    result = []

    # Categorize components by priority
    for i, comp in enumerate(components):
        # High priority - never trim
        if "Current Task Assignment" in comp:
            result.append(comp)
        elif "## RESUME CONTEXT" in comp or "## PM STATE" in comp:
            result.append(comp)
        # Agent definition - never trim (identified by size)
        elif estimate_tokens(comp) > 500 and "SPECIALIZATION GUIDANCE" not in comp and "Context from Prior Work" not in comp:
            result.append(comp)
        # Medium priority - trim if needed
        elif "Context from Prior Work" in comp:
            # Context block - can be trimmed
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Context block ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        elif "SPECIALIZATION GUIDANCE" in comp:
            # Specialization block - can be trimmed
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Specialization block ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        # Low priority - trim first
        elif "Previous QA Feedback" in comp or "Tech Lead Feedback" in comp or "Investigation Findings" in comp:
            # Feedback context - trim first
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Feedback context ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        else:
            # Unknown section - keep by default
            result.append(comp)

    return result, trimmed_log


# =============================================================================
# MAIN PROMPT COMPOSITION
# =============================================================================

def build_prompt(args):
    """Build the complete agent prompt."""
    global PROJECT_ROOT, SPECIALIZATIONS_BASE

    # Allow project root override for testing
    if args.project_root:
        PROJECT_ROOT = Path(args.project_root)
        SPECIALIZATIONS_BASE = PROJECT_ROOT / "bazinga" / "templates" / "specializations"
        print(f"[INFO] Using override project root: {PROJECT_ROOT}", file=sys.stderr)

    # Check database exists - FAIL by default (deterministic orchestration requires DB)
    if not Path(args.db).exists():
        if args.allow_no_db:
            print(f"WARNING: Database not found at {args.db}, proceeding without DB data (--allow-no-db)", file=sys.stderr)
            conn = None
        else:
            print(f"ERROR: Database not found at {args.db}", file=sys.stderr)
            print(f"Deterministic orchestration requires database. Options:", file=sys.stderr)
            print(f"  1. Run config-seeder skill to initialize database", file=sys.stderr)
            print(f"  2. Use --allow-no-db to skip DB validation (NOT RECOMMENDED)", file=sys.stderr)
            sys.exit(1)
    else:
        conn = sqlite3.connect(args.db)

    # Use try/finally to ensure conn.close() is always called
    try:
        model = args.model or "sonnet"
        components = []
        markers_valid = True

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

        # 7. Enforce global budget - trim lowest-priority sections if over hard limit
        components, trimmed_sections = enforce_global_budget(components, model)
        if trimmed_sections:
            for trim_msg in trimmed_sections:
                print(f"WARNING: {trim_msg}", file=sys.stderr)

        # Compose final prompt
        full_prompt = "\n\n".join(components)

        # 8. Validate required markers (only if DB available)
        if conn:
            markers = get_required_markers(conn, args.agent_type)
            if markers:
                markers_valid = validate_markers(full_prompt, markers, args.agent_type)

        # 9. Prepare metadata
        lines = len(full_prompt.splitlines())
        tokens = estimate_tokens(full_prompt)

        # 10. Output metadata to stderr FIRST
        print(f"[PROMPT_METADATA]", file=sys.stderr)
        print(f"agent_type={args.agent_type}", file=sys.stderr)
        print(f"project_root={PROJECT_ROOT}", file=sys.stderr)
        print(f"lines={lines}", file=sys.stderr)
        print(f"tokens_estimate={tokens}", file=sys.stderr)
        print(f"sections_trimmed={len(trimmed_sections)}", file=sys.stderr)
        if conn:
            print(f"markers_validated={str(markers_valid).lower()}", file=sys.stderr)

        # 11. Exit with error if markers were invalid (WITHOUT emitting prompt)
        if not markers_valid:
            print("ERROR: Prompt validation failed - not emitting invalid prompt", file=sys.stderr)
            sys.exit(1)

        # 12. Output prompt to stdout ONLY on success
        print(full_prompt)

    finally:
        # Always close database connection
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build deterministic agent prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 prompt_builder.py --agent-type developer --session-id "bazinga_123" \\
        --branch "main" --mode "simple" --testing-mode "full"

Debug mode:
    python3 prompt_builder.py --debug --agent-type developer ...
    (Prints received arguments to stderr for debugging)
"""
    )

    # Debug flag
    parser.add_argument("--debug", action="store_true",
                        help="Print debug info including received arguments")

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
    parser.add_argument("--allow-no-db", action="store_true",
                        help="Allow building prompts without database (NOT RECOMMENDED)")
    parser.add_argument("--project-root", default=None,
                        help="Override detected project root (for testing)")

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

    # Sanitize sys.argv - remove empty or whitespace-only args that bash might pass
    # This handles issues with multiline commands using backslash continuations
    original_argv = sys.argv.copy()
    sanitized_argv = [arg for arg in sys.argv if arg.strip()]

    # Check if sanitization changed anything
    args_removed = len(original_argv) != len(sanitized_argv)

    # First, check for --debug early to help diagnose parsing issues
    if "--debug" in sanitized_argv:
        print(f"[DEBUG] Original sys.argv ({len(original_argv)} args):", file=sys.stderr)
        for i, arg in enumerate(original_argv):
            # Show repr() to reveal whitespace/invisible chars
            print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        if args_removed:
            print(f"[DEBUG] Sanitized to ({len(sanitized_argv)} args):", file=sys.stderr)
            for i, arg in enumerate(sanitized_argv):
                print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        print(f"[DEBUG] Project root: {PROJECT_ROOT}", file=sys.stderr)

    # Use sanitized argv for parsing
    if args_removed:
        print(f"[INFO] Removed {len(original_argv) - len(sanitized_argv)} empty/whitespace args from command line", file=sys.stderr)

    try:
        args = parser.parse_args(sanitized_argv[1:])  # Skip script name
    except SystemExit as e:
        # argparse calls sys.exit on error - intercept to add diagnostics
        if e.code != 0:
            print(f"\n[ERROR] Argument parsing failed. Raw sys.argv:", file=sys.stderr)
            for i, arg in enumerate(original_argv):
                print(f"  [{i}] {repr(arg)}", file=sys.stderr)
            if args_removed:
                print(f"\nSanitized argv:", file=sys.stderr)
                for i, arg in enumerate(sanitized_argv):
                    print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        raise

    if args.debug:
        print(f"[DEBUG] Parsed args: {args}", file=sys.stderr)

    build_prompt(args)


if __name__ == "__main__":
    main()
