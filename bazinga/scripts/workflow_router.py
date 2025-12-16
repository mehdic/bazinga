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

# Default model assignments per agent
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
        SELECT name FROM task_groups
        WHERE session_id = ? AND id = ?
    """, (session_id, group_id))
    row = cursor.fetchone()
    if row and row[0]:
        name = row[0].lower()
        return "security" in name or "auth" in name
    return False


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
    parser.add_argument("--db", default=DB_PATH,
                        help="Database path")

    args = parser.parse_args()
    route(args)


if __name__ == "__main__":
    main()
