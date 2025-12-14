#!/usr/bin/env python3
"""
Migration script: Fix task_groups table schema

Root Cause:
-----------
The task_groups table has `id TEXT PRIMARY KEY`, making group IDs globally unique.
When multiple sessions use the same group ID (e.g., "A", "B"), only the first succeeds.
Subsequent sessions fail with "Task group already exists" error.

Solution:
---------
Change PRIMARY KEY to composite: (id, session_id)
This allows the same group ID to be reused across different sessions.

Usage:
------
python3 migrate_task_groups_schema.py --db /path/to/bazinga.db [--dry-run]

Author: Claude Code
Date: 2025-11-21
"""

import sqlite3
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path


def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    return backup_path


def migrate_task_groups_schema(db_path: str, dry_run: bool = False):
    """Migrate task_groups table to use composite primary key."""

    print(f"{'[DRY RUN] ' if dry_run else ''}Starting task_groups schema migration...")
    print(f"Database: {db_path}")

    if not Path(db_path).exists():
        print(f"❌ Error: Database not found at {db_path}")
        sys.exit(1)

    # Create backup
    if not dry_run:
        backup_path = backup_database(db_path)
        print(f"✓ Created backup: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if task_groups table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='task_groups'
    """)
    if not cursor.fetchone():
        print("⚠️  task_groups table doesn't exist yet. Nothing to migrate.")
        conn.close()
        return

    # Get current data
    cursor.execute("SELECT * FROM task_groups ORDER BY created_at")
    existing_groups = [dict(row) for row in cursor.fetchall()]

    print(f"\n📊 Current state:")
    print(f"   Total task groups: {len(existing_groups)}")

    # Group by session to show conflicts
    by_session = {}
    conflicts = []
    for group in existing_groups:
        sid = group['session_id']
        gid = group['id']
        if sid not in by_session:
            by_session[sid] = []
        by_session[sid].append(gid)

        # Check for potential conflicts (same ID, different session)
        for other in existing_groups:
            if other['id'] == gid and other['session_id'] != sid:
                conflicts.append((gid, sid, other['session_id']))

    print(f"   Unique sessions: {len(by_session)}")
    if conflicts:
        print(f"   ⚠️  Potential conflicts detected: {len(set(conflicts))} group IDs used across multiple sessions")
        for gid, s1, s2 in set(conflicts)[:5]:
            print(f"      - Group '{gid}' exists in sessions: {s1[:20]}..., {s2[:20]}...")

    if dry_run:
        print("\n[DRY RUN] Would perform the following migration:")
        print("   1. Rename task_groups to task_groups_old")
        print("   2. Create new task_groups with composite PRIMARY KEY (id, session_id)")
        print("   3. Copy all data to new table")
        print("   4. Drop old table")
        print("   5. Recreate indexes")
        print(f"\n[DRY RUN] {len(existing_groups)} task groups would be migrated")
        conn.close()
        return

    print("\n🔄 Performing migration...")

    try:
        # Step 1: Rename existing table
        cursor.execute("ALTER TABLE task_groups RENAME TO task_groups_old")
        print("   ✓ Step 1: Renamed task_groups to task_groups_old")

        # Step 2: Create new table with composite primary key
        cursor.execute("""
            CREATE TABLE task_groups (
                id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
                assigned_to TEXT,
                revision_count INTEGER DEFAULT 0,
                last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, session_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        print("   ✓ Step 2: Created new task_groups table with composite PRIMARY KEY")

        # Step 3: Copy data
        cursor.execute("""
            INSERT INTO task_groups
                (id, session_id, name, status, assigned_to, revision_count,
                 last_review_status, created_at, updated_at)
            SELECT
                id, session_id, name, status, assigned_to, revision_count,
                last_review_status, created_at, updated_at
            FROM task_groups_old
        """)
        migrated_count = cursor.rowcount
        print(f"   ✓ Step 3: Copied {migrated_count} task groups to new table")

        # Step 4: Drop old table
        cursor.execute("DROP TABLE task_groups_old")
        print("   ✓ Step 4: Dropped task_groups_old table")

        # Step 5: Recreate indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_taskgroups_session
            ON task_groups(session_id, status)
        """)
        print("   ✓ Step 5: Recreated indexes")

        # Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"   Migrated {migrated_count} task groups")
        print(f"   Schema updated: id TEXT PRIMARY KEY → PRIMARY KEY (id, session_id)")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print("   Database rolled back to previous state")
        print(f"   Backup available at: {backup_path}")
        sys.exit(1)
    finally:
        conn.close()

    print("\n📝 Next steps:")
    print("   1. Test task group creation in new sessions")
    print("   2. Verify existing task groups still accessible")
    print("   3. Run orchestration to confirm fix works")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate task_groups table to use composite primary key',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--db', required=True, help='Path to bazinga.db database')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without making changes')

    args = parser.parse_args()

    migrate_task_groups_schema(args.db, args.dry_run)


if __name__ == '__main__':
    main()
