#!/usr/bin/env python3
"""
Initialize BAZINGA database schema.
Creates all necessary tables for managing orchestration state.
"""

import sqlite3
import sys
from pathlib import Path
import tempfile
import shutil

# Current schema version
SCHEMA_VERSION = 3

def get_schema_version(cursor) -> int:
    """Get current schema version from database."""
    try:
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.OperationalError:
        # Table doesn't exist, this is version 0 (pre-versioning)
        return 0

def migrate_v1_to_v2(conn, cursor) -> None:
    """Migrate from v1 (CHECK constraint) to v2 (no constraint)."""
    print("🔄 Migrating schema from v1 to v2...")

    # Export existing data
    cursor.execute("SELECT * FROM orchestration_logs")
    logs_data = cursor.fetchall()
    print(f"   - Backing up {len(logs_data)} orchestration log entries")

    # Drop old table
    cursor.execute("DROP TABLE IF EXISTS orchestration_logs")

    # Recreate with new schema (no CHECK constraint)
    cursor.execute("""
        CREATE TABLE orchestration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            iteration INTEGER,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            content TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)

    # Recreate indexes
    cursor.execute("""
        CREATE INDEX idx_logs_session
        ON orchestration_logs(session_id, timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX idx_logs_agent_type
        ON orchestration_logs(session_id, agent_type)
    """)

    # Restore data
    if logs_data:
        cursor.executemany("""
            INSERT INTO orchestration_logs
            (id, session_id, timestamp, iteration, agent_type, agent_id, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, logs_data)
        print(f"   - Restored {len(logs_data)} orchestration log entries")

    print("✓ Migration to v2 complete")

def init_database(db_path: str) -> None:
    """Initialize the BAZINGA database with complete schema."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode = WAL")

    # Create schema_version table first (if doesn't exist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)

    # Get current schema version
    current_version = get_schema_version(cursor)
    print(f"Current schema version: {current_version}")

    # Run migrations if needed
    if current_version < SCHEMA_VERSION:
        print(f"Schema upgrade required: v{current_version} -> v{SCHEMA_VERSION}")

        if current_version == 0 or current_version == 1:
            # Check if orchestration_logs exists with old schema
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='orchestration_logs'
            """)
            result = cursor.fetchone()
            if result and 'CHECK' in result[0]:
                # Has old CHECK constraint, migrate
                migrate_v1_to_v2(conn, cursor)

        # Handle v2→v3 migration (add development_plans table)
        if current_version == 2:
            print("🔄 Migrating schema from v2 to v3...")
            # No data migration needed - just add new table
            # Table will be created below with CREATE TABLE IF NOT EXISTS
            print("✓ Migration to v3 complete (development_plans table added)")

        # Record version upgrade
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES (?, ?)
        """, (SCHEMA_VERSION, f"Schema v{SCHEMA_VERSION}: Add development_plans table for multi-phase orchestrations"))
        conn.commit()
        print(f"✓ Schema upgraded to v{SCHEMA_VERSION}")
    elif current_version == SCHEMA_VERSION:
        print(f"✓ Schema is up-to-date (v{SCHEMA_VERSION})")

    print("\nCreating/verifying BAZINGA database schema...")

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            mode TEXT CHECK(mode IN ('simple', 'parallel')),
            original_requirements TEXT,
            status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created sessions table")

    # Orchestration logs table (replaces orchestration-log.md)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orchestration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            iteration INTEGER,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            content TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_session
        ON orchestration_logs(session_id, timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_agent_type
        ON orchestration_logs(session_id, agent_type)
    """)
    print("✓ Created orchestration_logs table with indexes")

    # State snapshots table (replaces JSON state files)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            state_type TEXT CHECK(state_type IN ('pm', 'orchestrator', 'group_status')),
            state_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_state_session_type
        ON state_snapshots(session_id, state_type, timestamp DESC)
    """)
    print("✓ Created state_snapshots table with indexes")

    # Task groups table (normalized from pm_state.json)
    # PRIMARY KEY: Composite (id, session_id) allows same group ID across sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_groups (
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
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_taskgroups_session
        ON task_groups(session_id, status)
    """)
    print("✓ Created task_groups table with indexes")

    # Token usage tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            tokens_estimated INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tokens_session
        ON token_usage(session_id, agent_type)
    """)
    print("✓ Created token_usage table with indexes")

    # Skill outputs table (replaces individual JSON files)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            skill_name TEXT NOT NULL,
            output_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_skill_session
        ON skill_outputs(session_id, skill_name, timestamp DESC)
    """)
    print("✓ Created skill_outputs table with indexes")

    # REMOVED: Configuration table - No use case defined
    # See research/empty-tables-analysis.md for details
    # Table creation commented out as of 2025-11-21

    # REMOVED: Decisions table - Redundant with orchestration_logs
    # See research/empty-tables-analysis.md for details
    # Table creation commented out as of 2025-11-21

    # Development plans table (for multi-phase orchestrations)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS development_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            original_prompt TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            phases TEXT NOT NULL,
            current_phase INTEGER,
            total_phases INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_devplans_session
        ON development_plans(session_id)
    """)
    print("✓ Created development_plans table with indexes")

    # Record schema version for new databases
    current_version = get_schema_version(cursor)
    if current_version == 0:
        cursor.execute("""
            INSERT INTO schema_version (version, description)
            VALUES (?, ?)
        """, (SCHEMA_VERSION, f"Initial schema v{SCHEMA_VERSION}"))
        print(f"✓ Recorded schema version: v{SCHEMA_VERSION}")

    conn.commit()
    conn.close()

    print(f"\n✅ Database initialized successfully at: {db_path}")
    print(f"   - Schema version: v{SCHEMA_VERSION}")
    print(f"   - WAL mode enabled for better concurrency")
    print(f"   - Foreign keys enabled for referential integrity")
    print(f"   - All indexes created for optimal query performance")


def main():
    if len(sys.argv) < 2:
        print("Usage: python init_db.py <database_path>")
        print("Example: python init_db.py /home/user/bazinga/bazinga/bazinga.db")
        sys.exit(1)

    db_path = sys.argv[1]

    # Create parent directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    init_database(db_path)


if __name__ == "__main__":
    main()
