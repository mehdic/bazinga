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

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Add _shared directory to path for bazinga_paths import
_script_dir = Path(__file__).resolve().parent
_shared_dir = _script_dir.parent.parent / '_shared'
if _shared_dir.exists() and str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

try:
    from bazinga_paths import get_project_root
    _HAS_BAZINGA_PATHS = True
except ImportError:
    _HAS_BAZINGA_PATHS = False


def _ensure_cwd_at_project_root():
    """Change to project root so all relative paths work correctly.

    This is critical when the script is invoked from a different CWD.
    See: research/absolute-path-resolution-ultrathink.md

    Must be called at entry point (main), NOT at module import time,
    to avoid side effects when this module is imported by tests.
    """
    if not _HAS_BAZINGA_PATHS:
        return  # Cannot detect project root without bazinga_paths

    try:
        project_root = get_project_root()
        os.chdir(project_root)
        # Only log if BAZINGA_VERBOSE is set to reduce noise
        if os.environ.get("BAZINGA_VERBOSE"):
            print(f"[INFO] project_root={project_root}", file=sys.stderr)
    except RuntimeError:
        # Project root detection failed - no valid markers found
        # Don't chdir to avoid changing to wrong directory
        pass
    except OSError as e:
        print(f"[WARNING] Failed to chdir to project root: {e}", file=sys.stderr)


# Database path - relative to project root
DB_PATH = "bazinga/bazinga.db"

# Config file path - relative to project root
MODEL_CONFIG_PATH = "bazinga/model_selection.json"

# Expected transitions version (from workflow/transitions.json)
EXPECTED_TRANSITIONS_VERSION = "1.2.0"

# Version file path (relative to DB directory)
VERSION_FILE_NAME = ".transitions_version"

# Seed script path (centralized to avoid duplication)
SEED_SCRIPT_PATH = _script_dir.parent.parent / "config-seeder" / "scripts" / "seed_configs.py"

# Subprocess timeout for seeding (seconds)
SEED_TIMEOUT_SECONDS = 30


def get_transitions_info(db_path: str) -> tuple[int, str | None]:
    """
    Get transitions count from DB and version from version file.
    Returns (count, version) tuple. Version is None if file doesn't exist.
    """
    count = 0
    version = None

    # Get count from DB (use context manager to ensure closure)
    try:
        with sqlite3.connect(db_path, timeout=2.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM workflow_transitions")
            count = cursor.fetchone()[0]
    except sqlite3.OperationalError as e:
        print(f"[workflow-router] Could not read transitions count: {e}", file=sys.stderr)

    # Get version from file (next to DB)
    version_file = Path(db_path).parent / VERSION_FILE_NAME
    if version_file.exists():
        try:
            version = version_file.read_text().strip()
        except Exception:
            pass

    return count, version


def write_version_file(db_path: str, version: str):
    """Write version to version file next to DB."""
    version_file = Path(db_path).parent / VERSION_FILE_NAME
    try:
        version_file.write_text(version)
    except Exception:
        pass  # Best effort


def auto_seed_configs(db_path: str, verbose: bool = False) -> tuple[bool, str]:
    """
    Auto-seed workflow configs if missing or outdated.
    Returns (success, message) tuple.
    """
    if not SEED_SCRIPT_PATH.exists():
        return False, f"Config seeder not found at {SEED_SCRIPT_PATH}"

    if verbose:
        print(f"[workflow-router] Seeding configs...", file=sys.stderr)

    try:
        result = subprocess.run(
            [sys.executable, str(SEED_SCRIPT_PATH), "--db", db_path, "--all"],
            capture_output=True,
            text=True,
            timeout=SEED_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return False, f"Config seeding timed out after {SEED_TIMEOUT_SECONDS}s"

    if result.returncode != 0:
        # Include stdout if stderr is empty for better diagnostics
        error_output = result.stderr.strip()
        if not error_output and result.stdout.strip():
            error_output = result.stdout.strip()[:200]  # Truncate long output
        return False, f"Config seeding failed: {error_output}"

    return True, "Configs seeded successfully"

# Global config - loaded lazily in main()
MODEL_CONFIG = None


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

    if not config:
        return None, f"No agent configs found in {MODEL_CONFIG_PATH}"

    return config, None


def emit_error(error_msg, suggestion=None):
    """Print JSON error and exit."""
    result = {
        "success": False,
        "error": error_msg,
    }
    if suggestion:
        result["suggestion"] = suggestion
    print(json.dumps(result, indent=2))
    sys.exit(1)


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
        except json.JSONDecodeError as e:
            print(
                f"[workflow-router] malformed include_context for {current_agent}/{status}: {e}",
                file=sys.stderr
            )
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
            "suggestion": "Use Skill(command: 'bazinga-db') to initialize database"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Smart seeding: only seed if missing, empty, or version mismatch
    count, stored_version = get_transitions_info(args.db)
    needs_seeding = (count == 0) or (stored_version != EXPECTED_TRANSITIONS_VERSION)

    if needs_seeding:
        if SEED_SCRIPT_PATH.exists():
            success, message = auto_seed_configs(args.db, verbose=True)
            if success:
                # Write version file after successful seeding
                write_version_file(args.db, EXPECTED_TRANSITIONS_VERSION)
            elif count > 0:
                # Seeding failed, but we have existing transitions - proceed with warning
                print(f"[workflow-router] Warning: {message} (proceeding with existing {count} transitions)", file=sys.stderr)
            else:
                # Seeding failed and no transitions - fatal
                result = {
                    "success": False,
                    "error": f"Config seeding failed and no transitions exist: {message}",
                    "suggestion": "Use Skill(command: 'config-seeder') to seed configs"
                }
                print(json.dumps(result, indent=2))
                sys.exit(1)
        elif count == 0:
            # Seeder not found and no transitions - fatal
            result = {
                "success": False,
                "error": "No transitions in database and config-seeder not found",
                "suggestion": "Use Skill(command: 'config-seeder') to seed workflow configs"
            }
            print(json.dumps(result, indent=2))
            sys.exit(1)
        else:
            # Seeder not found but we have transitions - proceed with warning if version mismatch
            if stored_version != EXPECTED_TRANSITIONS_VERSION:
                print(
                    f"[workflow-router] transitions version mismatch "
                    f"(stored={stored_version}, expected={EXPECTED_TRANSITIONS_VERSION}); "
                    f"proceeding with existing {count} transitions",
                    file=sys.stderr
                )

    # Use try/finally to ensure connection closure on all paths
    conn = sqlite3.connect(args.db, timeout=2.0)
    try:
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

        # Determine model - only needed for spawn/respawn actions with a next_agent
        model = None
        if action in ("spawn", "respawn", "spawn_batch") and next_agent:
            model = transition.get("model_override")
            if not model:
                if next_agent not in MODEL_CONFIG:
                    # Unknown agent - emit error JSON instead of raising
                    emit_error(
                        f"Agent '{next_agent}' not found in {MODEL_CONFIG_PATH}",
                        f"Add '{next_agent}' to agents section in {MODEL_CONFIG_PATH}"
                    )
                model = MODEL_CONFIG[next_agent]

        # Build result
        result = {
            "success": True,
            "current_agent": args.current_agent,
            "response_status": args.status,
            "next_agent": next_agent,
            "action": action,
            "group_id": args.group_id,
            "session_id": args.session_id,
            "include_context": transition.get("include_context", []),
        }

        # Only include model when spawning an agent
        if model:
            result["model"] = model

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
    finally:
        conn.close()


def main():
    global MODEL_CONFIG

    # Ensure we're in project root for relative path resolution
    _ensure_cwd_at_project_root()

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

    # Load model config with error handling
    MODEL_CONFIG, config_error = load_model_config()
    if config_error:
        emit_error(config_error, "Ensure bazinga/model_selection.json exists and is valid JSON")

    route(args)


if __name__ == "__main__":
    main()
