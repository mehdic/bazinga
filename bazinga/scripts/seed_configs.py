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

# Database path - relative to project root
DB_PATH = "bazinga/bazinga.db"

# Config directory - relative to project root
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

    conn.commit()
    print(f"Seeded {count} agent marker sets")
    return True


def seed_special_rules(conn):
    """Seed special rules from transitions.json _special_rules."""
    config_path = CONFIG_DIR / "transitions.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return False

    with open(config_path) as f:
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

    conn.commit()
    print(f"Seeded {count} special rules")
    return True


def main():
    parser = argparse.ArgumentParser(description="Seed config files to database")
    parser.add_argument("--transitions", action="store_true", help="Seed transitions only")
    parser.add_argument("--markers", action="store_true", help="Seed markers only")
    parser.add_argument("--rules", action="store_true", help="Seed special rules only")
    parser.add_argument("--all", action="store_true", help="Seed all configs")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Database path")
    args = parser.parse_args()

    # Default to --all if no specific flag
    if not (args.transitions or args.markers or args.rules):
        args.all = True

    # Check database exists
    if not Path(args.db).exists():
        print(f"ERROR: Database not found at {args.db}", file=sys.stderr)
        print("Run init_db.py first to create the database.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)

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
