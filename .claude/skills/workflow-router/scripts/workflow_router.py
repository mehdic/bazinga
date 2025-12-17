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
from pathlib import Path

# Database path - relative to project root
DB_PATH = "bazinga/bazinga.db"

# Config file path - relative to project root
MODEL_CONFIG_PATH = "bazinga/model_selection.json"

# Fallback model assignments (used if config file missing)
DEFAULT_MODEL_CONFIG = {
    "developer": "haiku",
    "senior_software_engineer": "sonnet",
    "qa_expert": "sonnet",
    "tech_lead": "opus",
    "project_manager": "opus",
    "investigator": "opus",
    "requirements_engineer": "opus",
}


def load_model_config():
    """Load model config from JSON file, fallback to defaults."""
    try:
        if Path(MODEL_CONFIG_PATH).exists():
            with open(MODEL_CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            # Extract agent -> model mapping
            config = {}
            for agent_name, agent_data in data.get("agents", {}).items():
                if isinstance(agent_data, dict) and "model" in agent_data:
                    config[agent_name] = agent_data["model"]
            if config:
                return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"WARNING: Failed to load model config: {e}", file=sys.stderr)
    return DEFAULT_MODEL_CONFIG


# Load model config at module init
MODEL_CONFIG = load_model_config()


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
        # Parse include_context safely - handle malformed JSON
        try:
            include_context = json.loads(row[2]) if row[2] else []
        except json.JSONDecodeError:
            include_context = []

        return {
            "next_agent": row[0],
            "action": row[1],
            "include_context": include_context,
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
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return None
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


def get_qa_attempts(conn, session_id, group_id):
    """Get QA failure attempts count for a group (v14+)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT qa_attempts FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    return row[0] if row and row[0] else 0


def get_tl_review_attempts(conn, session_id, group_id):
    """Get TL review attempts count for a group (v14+)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tl_review_attempts FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    return row[0] if row and row[0] else 0


def get_escalation_count(conn, session_id, group_id, current_agent):
    """Get the appropriate escalation counter based on agent type.

    v14: Uses separate counters for different failure loops:
    - qa_expert FAIL → qa_attempts
    - tech_lead CHANGES_REQUESTED → tl_review_attempts
    - Other → revision_count (legacy)
    """
    if current_agent == "qa_expert":
        return get_qa_attempts(conn, session_id, group_id)
    elif current_agent == "tech_lead":
        return get_tl_review_attempts(conn, session_id, group_id)
    else:
        return get_revision_count(conn, session_id, group_id)


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
    """Check if task is security sensitive.

    Checks in order:
    1. security_sensitive column (v14+) - PM's explicit flag
    2. Fallback: name-based detection ("security", "auth" in name)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, security_sensitive FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    if not row:
        return False

    name = row[0] or ""
    # SELECT always returns 2 columns (name, security_sensitive)
    security_flag = row[1]

    # Check explicit flag first (v14+)
    if security_flag is not None and security_flag == 1:
        return True

    # Fallback: name-based detection
    name_lower = name.lower()
    return "security" in name_lower or "auth" in name_lower


def route(args):
    """Determine next action based on state."""
    # Check database exists
    if not Path(args.db).exists():
        result = {
            "success": False,
            "error": f"Database not found at {args.db}",
            "suggestion": "Run init_db.py and seed_configs.py first"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    conn = sqlite3.connect(args.db)

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
    # v14: Use appropriate counter based on agent type (qa_attempts, tl_review_attempts, or revision_count)
    if transition.get("escalation_check"):
        escalation_count = get_escalation_count(conn, args.session_id, args.group_id, args.current_agent)
        escalation_rule = get_special_rule(conn, "escalation_after_failures")
        threshold = escalation_rule.get("threshold", 2) if escalation_rule else 2

        if escalation_count >= threshold:
            next_agent = "senior_software_engineer"
            action = "spawn"
            transition["escalation_applied"] = True
            transition["escalation_counter"] = f"{args.current_agent}_attempts={escalation_count}"
            transition["escalation_reason"] = f"Escalated after {escalation_count} failures"

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
        # Use 'or 4' instead of default to handle NULL from DB (which returns None, not default)
        max_parallel = transition.get("max_parallel") or 4
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
    parser.add_argument("--db", default=DB_PATH,
                        help="Database path")

    args = parser.parse_args()
    route(args)


if __name__ == "__main__":
    main()
