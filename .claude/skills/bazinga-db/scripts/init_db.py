#!/usr/bin/env python3
"""
Initialize BAZINGA database schema.
Creates all necessary tables for managing orchestration state.
"""

import sqlite3
import sys
from pathlib import Path


def init_database(db_path: str) -> None:
    """Initialize the BAZINGA database with complete schema."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode = WAL")

    print("Creating BAZINGA database schema...")

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
            agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')),
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_groups (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
            assigned_to TEXT,
            revision_count INTEGER DEFAULT 0,
            last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    # Configuration table (replaces config JSON files)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuration (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created configuration table")

    # Decisions log table (for orchestrator decisions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            iteration INTEGER,
            decision_type TEXT NOT NULL,
            decision_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_decisions_session
        ON decisions(session_id, timestamp DESC)
    """)
    print("✓ Created decisions table with indexes")

    conn.commit()
    conn.close()

    print(f"\n✅ Database initialized successfully at: {db_path}")
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
