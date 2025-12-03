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
SCHEMA_VERSION = 6

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

        # Handle v3→v4 migration (add success_criteria table)
        if current_version == 3:
            print("🔄 Migrating schema from v3 to v4...")
            # No data migration needed - just add new table
            # Table will be created below with CREATE TABLE IF NOT EXISTS
            print("✓ Migration to v4 complete (success_criteria table added)")

        # Handle v4→v5 migration (merge-on-approval architecture)
        if current_version == 4:
            print("🔄 Migrating schema from v4 to v5...")

            # 1. Add initial_branch to sessions
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN initial_branch TEXT DEFAULT 'main'")
                print("   ✓ Added sessions.initial_branch")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("   ⊘ sessions.initial_branch already exists")
                else:
                    raise

            # 2. Add feature_branch to task_groups
            try:
                cursor.execute("ALTER TABLE task_groups ADD COLUMN feature_branch TEXT")
                print("   ✓ Added task_groups.feature_branch")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("   ⊘ task_groups.feature_branch already exists")
                else:
                    raise

            # 3. Add merge_status to task_groups (without CHECK - SQLite limitation)
            # NOTE: ALTER TABLE cannot add CHECK constraints in SQLite
            # The CHECK constraint is applied in step 4 when we recreate the table
            try:
                cursor.execute("ALTER TABLE task_groups ADD COLUMN merge_status TEXT")
                print("   ✓ Added task_groups.merge_status (CHECK constraint applied in step 4)")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("   ⊘ task_groups.merge_status already exists")
                else:
                    raise

            # 4. Recreate task_groups with expanded status enum AND proper CHECK constraints
            # This step applies CHECK constraints that couldn't be added via ALTER TABLE
            cursor.execute("SELECT sql FROM sqlite_master WHERE name='task_groups'")
            schema = cursor.fetchone()[0]

            if 'approved_pending_merge' not in schema:
                print("   Recreating task_groups with expanded status enum...")

                # Create new table with expanded status enum
                cursor.execute("""
                    CREATE TABLE task_groups_new (
                        id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        status TEXT CHECK(status IN (
                            'pending', 'in_progress', 'completed', 'failed',
                            'approved_pending_merge', 'merging'
                        )) DEFAULT 'pending',
                        assigned_to TEXT,
                        revision_count INTEGER DEFAULT 0,
                        last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
                        feature_branch TEXT,
                        merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
                        complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
                        initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id, session_id),
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                    )
                """)

                # Get existing columns in task_groups
                cursor.execute("PRAGMA table_info(task_groups)")
                existing_cols = [row[1] for row in cursor.fetchall()]

                # Build column list for migration (only columns that exist)
                all_cols = ['id', 'session_id', 'name', 'status', 'assigned_to', 'revision_count',
                           'last_review_status', 'feature_branch', 'merge_status', 'complexity',
                           'initial_tier', 'created_at', 'updated_at']
                cols_to_copy = [c for c in all_cols if c in existing_cols]
                cols_str = ', '.join(cols_to_copy)

                # Copy data
                cursor.execute(f"""
                    INSERT INTO task_groups_new ({cols_str})
                    SELECT {cols_str} FROM task_groups
                """)

                # Swap tables
                cursor.execute("DROP TABLE task_groups")
                cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")
                cursor.execute("CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status)")

                print("   ✓ Recreated task_groups with expanded status enum")
            else:
                print("   ⊘ task_groups status enum already expanded")

            print("✓ Migration to v5 complete (merge-on-approval architecture)")

        # Handle v5→v6 migration (context packages for inter-agent communication)
        if current_version == 5:
            print("🔄 Migrating schema from v5 to v6...")

            # 1. Add context_references to task_groups
            try:
                cursor.execute("ALTER TABLE task_groups ADD COLUMN context_references TEXT")
                print("   ✓ Added task_groups.context_references")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("   ⊘ task_groups.context_references already exists")
                else:
                    raise

            # 2. Create context_packages table (will be created below with IF NOT EXISTS)
            # 3. Create context_package_consumers table (will be created below with IF NOT EXISTS)

            print("✓ Migration to v6 complete (context packages for inter-agent communication)")

        # Record version upgrade
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES (?, ?)
        """, (SCHEMA_VERSION, f"Schema v{SCHEMA_VERSION}: Context packages for inter-agent communication"))
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
            initial_branch TEXT DEFAULT 'main',
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
            status TEXT CHECK(status IN (
                'pending', 'in_progress', 'completed', 'failed',
                'approved_pending_merge', 'merging'
            )) DEFAULT 'pending',
            assigned_to TEXT,
            revision_count INTEGER DEFAULT 0,
            last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
            feature_branch TEXT,
            merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
            complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
            initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
            context_references TEXT,
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

    # Success criteria table (for BAZINGA validation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS success_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            criterion TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'met', 'blocked', 'failed')) DEFAULT 'pending',
            actual TEXT,
            evidence TEXT,
            required_for_completion BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_criterion
        ON success_criteria(session_id, criterion)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_criteria_session_status
        ON success_criteria(session_id, status)
    """)
    print("✓ Created success_criteria table with indexes")

    # Context packages table (for inter-agent communication)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            group_id TEXT,
            package_type TEXT NOT NULL CHECK(package_type IN ('research', 'failures', 'decisions', 'handoff', 'investigation')),
            file_path TEXT NOT NULL,
            producer_agent TEXT NOT NULL,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
            summary TEXT NOT NULL,
            size_bytes INTEGER,
            version INTEGER DEFAULT 1,
            supersedes_id INTEGER,
            scope TEXT DEFAULT 'group' CHECK(scope IN ('group', 'global')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (supersedes_id) REFERENCES context_packages(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_session ON context_packages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_group ON context_packages(group_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_type ON context_packages(package_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_priority ON context_packages(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_scope ON context_packages(scope)")
    print("✓ Created context_packages table with indexes")

    # Context package consumers join table (for per-agent consumption tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context_package_consumers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL,
            agent_type TEXT NOT NULL,
            consumed_at TIMESTAMP,
            iteration INTEGER DEFAULT 1,
            FOREIGN KEY (package_id) REFERENCES context_packages(id) ON DELETE CASCADE,
            UNIQUE(package_id, agent_type, iteration)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpc_package ON context_package_consumers(package_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpc_agent ON context_package_consumers(agent_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpc_pending ON context_package_consumers(consumed_at) WHERE consumed_at IS NULL")
    print("✓ Created context_package_consumers table with indexes")

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
