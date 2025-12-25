#!/usr/bin/env python3
"""
Seeds JSON configuration files into the database.
Called by orchestrator at session initialization.

Usage:
    python3 .claude/skills/config-seeder/scripts/seed_configs.py [--transitions] [--markers] [--rules] [--all]
"""

import argparse
import json
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

# Config directory - relative to project root
CONFIG_DIR = PROJECT_ROOT / "bazinga" / "config"


def _ensure_cwd_at_project_root():
    """Change to project root so all relative paths work correctly.

    This is critical when the script is invoked from a different CWD.
    See: research/absolute-path-resolution-ultrathink.md

    Must be called at entry point (main), NOT at module import time,
    to avoid side effects when this module is imported by tests.
    """
    import os
    try:
        os.chdir(PROJECT_ROOT)
        # Only log if BAZINGA_VERBOSE is set to reduce noise
        if os.environ.get("BAZINGA_VERBOSE"):
            print(f"[INFO] project_root={PROJECT_ROOT}", file=sys.stderr)
    except OSError as e:
        print(f"[WARNING] Failed to chdir to project root {PROJECT_ROOT}: {e}", file=sys.stderr)


def seed_transitions(conn):
    """Seed workflow transitions from JSON."""
    config_path = CONFIG_DIR / "transitions.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()

    # Clear existing transitions
    cursor.execute("DELETE FROM workflow_transitions")

    count = 0
    for agent, statuses in data.items():
        if agent.startswith("_"):  # Skip metadata keys like _version, _description, _special_rules
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

    # Note: commit handled by caller in transaction wrapper
    print(f"Seeded {count} transitions")
    return True


def seed_markers(conn):
    """Seed agent markers from JSON."""
    config_path = CONFIG_DIR / "agent-markers.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()

    # Clear existing markers
    cursor.execute("DELETE FROM agent_markers")

    count = 0
    for agent, config in data.items():
        if agent.startswith("_"):  # Skip metadata keys
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

    # Note: commit handled by caller in transaction wrapper
    print(f"Seeded {count} agent marker sets")
    return True


def seed_special_rules(conn):
    """Seed special rules from transitions.json _special_rules."""
    config_path = CONFIG_DIR / "transitions.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    rules = data.get("_special_rules", {})
    if not rules:
        print("No special rules found")
        return True

    cursor = conn.cursor()

    # Clear existing rules
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

    # Note: commit handled by caller in transaction wrapper
    print(f"Seeded {count} special rules")
    return True


def main():
    global PROJECT_ROOT, CONFIG_DIR

    # Ensure we're in project root for relative path resolution
    _ensure_cwd_at_project_root()

    parser = argparse.ArgumentParser(description="Seed config files to database")
    parser.add_argument("--transitions", action="store_true", help="Seed transitions only")
    parser.add_argument("--markers", action="store_true", help="Seed markers only")
    parser.add_argument("--rules", action="store_true", help="Seed special rules only")
    parser.add_argument("--all", action="store_true", help="Seed all configs")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Database path")
    parser.add_argument("--project-root", type=str, default=None,
                        help="Override detected project root")
    parser.add_argument("--auto-init-db", action="store_true",
                        help="Auto-initialize database if missing")
    args = parser.parse_args()

    # Allow project root override
    if args.project_root:
        PROJECT_ROOT = Path(args.project_root)
        CONFIG_DIR = PROJECT_ROOT / "bazinga" / "config"
        if args.db == DB_PATH:  # Only override if not explicitly set
            args.db = str(PROJECT_ROOT / "bazinga" / "bazinga.db")
        print(f"[INFO] Using override project root: {PROJECT_ROOT}", file=sys.stderr)

    # Default to --all if no specific flag
    if not (args.transitions or args.markers or args.rules):
        args.all = True

    # Check database exists - optionally auto-initialize
    if not Path(args.db).exists():
        if args.auto_init_db:
            print(f"[INFO] Database not found at {args.db}, auto-initializing...", file=sys.stderr)
            init_script = PROJECT_ROOT / ".claude" / "skills" / "bazinga-db" / "scripts" / "init_db.py"
            if init_script.exists():
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(init_script), args.db],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"ERROR: Database initialization failed: {result.stderr}", file=sys.stderr)
                    sys.exit(1)
                print(f"[INFO] Database initialized at {args.db}", file=sys.stderr)
            else:
                print(f"ERROR: init_db.py not found at {init_script}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ERROR: Database not found at {args.db}", file=sys.stderr)
            print("Run init_db.py first to create the database, or use --auto-init-db.", file=sys.stderr)
            sys.exit(1)

    # CONCURRENCY NOTE: Using timeout=5.0 (5 second busy timeout) ensures that if
    # multiple processes try to seed simultaneously, they will wait rather than
    # fail immediately with "database is locked" errors.
    conn = sqlite3.connect(args.db, timeout=5.0)

    # Wrap all seeding in a single transaction for atomicity
    # If any seeding fails, rollback all changes
    #
    # Using BEGIN IMMEDIATE to acquire write lock immediately.
    # This ensures that if multiple processes try to seed simultaneously:
    # - One process acquires the lock and completes
    # - Other processes wait (up to 5s from timeout above)
    # - After lock release, subsequent processes will see the seeded data and
    #   their DELETE + INSERT will be a no-op (same data rewritten)
    # This is safe because config data is idempotent.
    try:
        conn.execute("BEGIN IMMEDIATE")

        success = True
        if args.all or args.transitions:
            success = seed_transitions(conn) and success
        if args.all or args.markers:
            success = seed_markers(conn) and success
        if args.all or args.rules:
            success = seed_special_rules(conn) and success

        if success:
            conn.commit()
            print("✅ Config seeding complete")
        else:
            conn.rollback()
            print("❌ Config seeding had errors - rolled back", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        conn.rollback()
        print(f"❌ Config seeding failed: {e} - rolled back", file=sys.stderr)
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
