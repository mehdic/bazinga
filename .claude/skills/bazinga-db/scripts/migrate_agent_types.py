#!/usr/bin/env python3
"""
Migration script to fix agent_type CHECK constraint inconsistency.

This script updates databases that have the old CHECK constraint:
  ('pm', 'developer', 'qa', 'tech_lead', 'orchestrator')

To the correct constraint that matches the codebase:
  ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')

It also migrates existing data:
  - 'qa' → 'qa_expert'
  - 'tech_lead' → 'techlead'
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str) -> None:
    """Migrate agent_type values and CHECK constraint."""

    print(f"Migrating database: {db_path}")

    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Count records that need migration
        print("\nStep 1: Analyzing existing data...")

        qa_count = cursor.execute("""
            SELECT COUNT(*) FROM orchestration_logs WHERE agent_type = 'qa'
        """).fetchone()[0]

        tech_lead_count = cursor.execute("""
            SELECT COUNT(*) FROM orchestration_logs WHERE agent_type = 'tech_lead'
        """).fetchone()[0]

        total_records = cursor.execute("""
            SELECT COUNT(*) FROM orchestration_logs
        """).fetchone()[0]

        print(f"  - Total records: {total_records}")
        print(f"  - Records with 'qa': {qa_count}")
        print(f"  - Records with 'tech_lead': {tech_lead_count}")

        # Step 2: Recreate table with correct CHECK constraint
        print("\nStep 2: Recreating table with correct CHECK constraint...")

        # Create new table with correct constraint
        cursor.execute("""
            CREATE TABLE orchestration_logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                iteration INTEGER,
                agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')),
                agent_id TEXT,
                content TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        print("  - Created new table with correct CHECK constraint")

        # Copy data while transforming agent_type values
        cursor.execute("""
            INSERT INTO orchestration_logs_new (id, session_id, timestamp, iteration, agent_type, agent_id, content)
            SELECT
                id,
                session_id,
                timestamp,
                iteration,
                CASE
                    WHEN agent_type = 'qa' THEN 'qa_expert'
                    WHEN agent_type = 'tech_lead' THEN 'techlead'
                    ELSE agent_type
                END,
                agent_id,
                content
            FROM orchestration_logs
        """)
        copy_count = cursor.rowcount
        print(f"  - Copied and migrated {copy_count} records to new table")

        # Drop old table
        cursor.execute("DROP TABLE orchestration_logs")
        print("  - Dropped old table")

        # Rename new table
        cursor.execute("ALTER TABLE orchestration_logs_new RENAME TO orchestration_logs")
        print("  - Renamed new table to orchestration_logs")

        # Recreate indexes
        print("\nStep 3: Recreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_session
            ON orchestration_logs(session_id, timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_agent_type
            ON orchestration_logs(session_id, agent_type)
        """)
        print("  - Recreated indexes")

        # Step 4: Update token_usage table data (if it has similar issue)
        print("\nStep 4: Checking token_usage table...")

        # Check if token_usage has old values
        token_qa_count = cursor.execute("""
            SELECT COUNT(*) FROM token_usage WHERE agent_type = 'qa'
        """).fetchone()[0]

        token_tl_count = cursor.execute("""
            SELECT COUNT(*) FROM token_usage WHERE agent_type = 'tech_lead'
        """).fetchone()[0]

        if token_qa_count > 0 or token_tl_count > 0:
            print(f"  - Found {token_qa_count} 'qa' and {token_tl_count} 'tech_lead' records")
            print(f"  - Migrating token_usage table...")

            # Create new token_usage table
            cursor.execute("""
                CREATE TABLE token_usage_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    agent_type TEXT NOT NULL,
                    agent_id TEXT,
                    tokens_estimated INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Copy with transformation
            cursor.execute("""
                INSERT INTO token_usage_new
                SELECT
                    id,
                    session_id,
                    timestamp,
                    CASE
                        WHEN agent_type = 'qa' THEN 'qa_expert'
                        WHEN agent_type = 'tech_lead' THEN 'techlead'
                        ELSE agent_type
                    END,
                    agent_id,
                    tokens_estimated
                FROM token_usage
            """)

            # Drop old and rename
            cursor.execute("DROP TABLE token_usage")
            cursor.execute("ALTER TABLE token_usage_new RENAME TO token_usage")

            # Recreate index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tokens_session
                ON token_usage(session_id, agent_type)
            """)

            print(f"  - Migrated {token_qa_count + token_tl_count} records in token_usage")
        else:
            print(f"  - No old agent types in token_usage (already correct)")

        # Commit all changes
        conn.commit()

        print("\n✅ Migration completed successfully!")
        print(f"\nSummary:")
        print(f"  - orchestration_logs: {qa_count + tech_lead_count} records migrated")
        print(f"    - 'qa' → 'qa_expert': {qa_count} records")
        print(f"    - 'tech_lead' → 'techlead': {tech_lead_count} records")
        if token_qa_count > 0 or token_tl_count > 0:
            print(f"  - token_usage: {token_qa_count + token_tl_count} records migrated")
            print(f"    - 'qa' → 'qa_expert': {token_qa_count} records")
            print(f"    - 'tech_lead' → 'techlead': {token_tl_count} records")
        else:
            print(f"  - token_usage: no migration needed")
        print(f"  - CHECK constraint updated to: ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


def verify_migration(db_path: str) -> None:
    """Verify the migration was successful."""
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check schema
        schema = cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='orchestration_logs'
        """).fetchone()[0]

        if "('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')" in schema:
            print("✅ CHECK constraint is correct")
        else:
            print("❌ CHECK constraint may not be correct")
            print(f"Schema: {schema}")

        # Check for any old values
        old_values = cursor.execute("""
            SELECT COUNT(*) FROM orchestration_logs
            WHERE agent_type IN ('qa', 'tech_lead')
        """).fetchone()[0]

        if old_values == 0:
            print("✅ No old agent_type values found")
        else:
            print(f"⚠️  Found {old_values} records with old agent_type values")

        # Show current agent_type distribution
        distribution = cursor.execute("""
            SELECT agent_type, COUNT(*) as count
            FROM orchestration_logs
            GROUP BY agent_type
        """).fetchall()

        if distribution:
            print("\nCurrent agent_type distribution:")
            for agent_type, count in distribution:
                print(f"  - {agent_type}: {count} records")
        else:
            print("\nNo records in orchestration_logs table")

    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_agent_types.py <database_path>")
        print("\nExample:")
        print("  python migrate_agent_types.py /home/user/bazinga/bazinga/bazinga.db")
        print("\nThis script will:")
        print("  1. Update 'qa' → 'qa_expert' in all tables")
        print("  2. Update 'tech_lead' → 'techlead' in all tables")
        print("  3. Recreate orchestration_logs table with correct CHECK constraint")
        sys.exit(1)

    db_path = sys.argv[1]

    # Run migration
    migrate_database(db_path)

    # Verify migration
    verify_migration(db_path)

    print("\n" + "=" * 60)
    print("Migration complete! Database is now consistent with codebase.")
    print("=" * 60)


if __name__ == "__main__":
    main()
