#!/usr/bin/env python3
"""
Initialize a BAZINGA session with all required setup.

This script ensures the deterministic orchestration infrastructure is ready:
1. Database exists and has correct schema
2. Workflow configs are seeded (transitions, markers, special rules)
3. Session artifacts directory exists

Usage:
    python3 .claude/skills/bazinga-db/scripts/init_session.py [--session-id ID]

This should be called at the START of every BAZINGA orchestration session,
BEFORE spawning PM. It's idempotent - safe to run multiple times.
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_project_root():
    """Detect project root by looking for .claude directory or bazinga directory."""
    script_dir = Path(__file__).resolve().parent

    current = script_dir
    for _ in range(10):
        if (current / ".claude").is_dir() or (current / "bazinga").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    cwd = Path.cwd()
    if (cwd / ".claude").is_dir() or (cwd / "bazinga").is_dir():
        return cwd

    return cwd


PROJECT_ROOT = get_project_root()


def ensure_database(db_path: Path) -> bool:
    """Ensure database exists and has correct schema."""
    init_script = PROJECT_ROOT / ".claude" / "skills" / "bazinga-db" / "scripts" / "init_db.py"

    if not init_script.exists():
        print(f"ERROR: init_db.py not found at {init_script}", file=sys.stderr)
        return False

    # Run init_db.py - it's idempotent (handles migrations, won't re-create tables)
    result = subprocess.run(
        [sys.executable, str(init_script), str(db_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"ERROR: Database initialization failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False

    # Check if any output indicates success
    if "already initialized" in result.stdout.lower() or "initialized" in result.stdout.lower():
        print("✓ Database ready", file=sys.stderr)
    else:
        print("✓ Database initialized", file=sys.stderr)

    return True


def ensure_config_seeded(db_path: Path) -> bool:
    """Ensure workflow configs are seeded into database."""
    seed_script = PROJECT_ROOT / ".claude" / "skills" / "config-seeder" / "scripts" / "seed_configs.py"

    if not seed_script.exists():
        print(f"ERROR: seed_configs.py not found at {seed_script}", file=sys.stderr)
        return False

    # Check if config is already seeded by checking BOTH workflow_transitions AND agent_markers
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)  # 5s busy timeout for concurrency
        cursor = conn.cursor()

        # Check transitions count
        cursor.execute("SELECT COUNT(*) FROM workflow_transitions")
        transitions_count = cursor.fetchone()[0]

        # Check markers count - both are required for prompt-builder/marker validation
        cursor.execute("SELECT COUNT(*) FROM agent_markers")
        markers_count = cursor.fetchone()[0]

        conn.close()

        if transitions_count > 0 and markers_count > 0:
            print(f"✓ Config already seeded ({transitions_count} transitions, {markers_count} markers)", file=sys.stderr)
            return True
        elif transitions_count > 0 or markers_count > 0:
            print(f"⚠ Partial config detected ({transitions_count} transitions, {markers_count} markers) - reseeding", file=sys.stderr)
            # Fall through to reseed
    except sqlite3.OperationalError:
        # Table doesn't exist - need to seed
        pass

    # Run seed_configs.py
    result = subprocess.run(
        [sys.executable, str(seed_script), "--all", "--db", str(db_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"ERROR: Config seeding failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False

    # Print seed output
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}", file=sys.stderr)

    print("✓ Config seeded", file=sys.stderr)
    return True


def ensure_artifacts_dir(session_id: str) -> Path:
    """Ensure session artifacts directory exists."""
    artifacts_dir = PROJECT_ROOT / "bazinga" / "artifacts" / session_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    skills_dir = artifacts_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    print(f"✓ Artifacts directory ready: {artifacts_dir}", file=sys.stderr)
    return artifacts_dir


def verify_ready(db_path: Path) -> dict:
    """Verify all components are ready and return status."""
    status = {
        "db_exists": db_path.exists(),
        "transitions_count": 0,
        "markers_count": 0,
        "rules_count": 0,
        "ready": False
    }

    if not status["db_exists"]:
        return status

    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)  # 5s busy timeout for concurrency
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM workflow_transitions")
        status["transitions_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agent_markers")
        status["markers_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM workflow_special_rules")
        status["rules_count"] = cursor.fetchone()[0]

        conn.close()

        # Ready if we have all required config
        # Note: rules_count > 0 is required because special rules control
        # testing_mode behavior, escalation triggers, and security enforcement
        status["ready"] = (
            status["transitions_count"] > 0 and
            status["markers_count"] > 0 and
            status["rules_count"] > 0
        )
    except sqlite3.OperationalError as e:
        status["error"] = str(e)

    return status


def main():
    parser = argparse.ArgumentParser(
        description="Initialize BAZINGA session infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script ensures deterministic orchestration is ready:
1. Database exists with correct schema
2. Workflow configs are seeded
3. Session artifacts directory exists

Run this BEFORE spawning PM in any orchestration session.
"""
    )
    parser.add_argument("--session-id", type=str, default=None,
                        help="Session ID (auto-generated if not provided)")
    parser.add_argument("--db", type=str, default=None,
                        help="Database path (default: bazinga/bazinga.db)")
    parser.add_argument("--project-root", type=str, default=None,
                        help="Override detected project root")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check readiness, don't initialize")
    parser.add_argument("--json", action="store_true",
                        help="Output status as JSON")
    args = parser.parse_args()

    global PROJECT_ROOT
    if args.project_root:
        PROJECT_ROOT = Path(args.project_root)

    db_path = Path(args.db) if args.db else PROJECT_ROOT / "bazinga" / "bazinga.db"
    session_id = args.session_id or f"bazinga_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if args.check_only:
        status = verify_ready(db_path)
        if args.json:
            print(json.dumps(status))
        else:
            if status["ready"]:
                print(f"✓ Session infrastructure ready", file=sys.stderr)
                print(f"  Transitions: {status['transitions_count']}", file=sys.stderr)
                print(f"  Markers: {status['markers_count']}", file=sys.stderr)
                print(f"  Rules: {status['rules_count']}", file=sys.stderr)
            else:
                print(f"✗ Session infrastructure NOT ready", file=sys.stderr)
                if not status["db_exists"]:
                    print(f"  Database missing: {db_path}", file=sys.stderr)
                elif "error" in status:
                    print(f"  Error: {status['error']}", file=sys.stderr)
                else:
                    print(f"  Missing config - run without --check-only to initialize", file=sys.stderr)
        sys.exit(0 if status["ready"] else 1)

    print(f"🚀 Initializing BAZINGA session: {session_id}", file=sys.stderr)
    print(f"   Project root: {PROJECT_ROOT}", file=sys.stderr)
    print(f"   Database: {db_path}", file=sys.stderr)

    # Step 1: Ensure database
    if not ensure_database(db_path):
        print("❌ Session initialization FAILED: database setup failed", file=sys.stderr)
        sys.exit(1)

    # Step 2: Ensure config seeded
    if not ensure_config_seeded(db_path):
        print("❌ Session initialization FAILED: config seeding failed", file=sys.stderr)
        sys.exit(1)

    # Step 3: Ensure artifacts directory
    ensure_artifacts_dir(session_id)

    # Step 4: Verify everything is ready
    status = verify_ready(db_path)
    if not status["ready"]:
        print("❌ Session initialization FAILED: verification failed", file=sys.stderr)
        print(f"   Status: {status}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Session initialization COMPLETE", file=sys.stderr)
    print(f"   Session ID: {session_id}", file=sys.stderr)
    print(f"   Transitions: {status['transitions_count']}", file=sys.stderr)
    print(f"   Markers: {status['markers_count']}", file=sys.stderr)
    print(f"   Rules: {status['rules_count']}", file=sys.stderr)

    # Output session ID to stdout for capture
    print(session_id)


if __name__ == "__main__":
    main()
