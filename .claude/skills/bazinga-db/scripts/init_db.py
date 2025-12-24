#!/usr/bin/env python3
"""
Initialize BAZINGA database schema.
Creates all necessary tables for managing orchestration state.

Path Resolution:
    If no database path is provided, auto-detects project root and uses:
    PROJECT_ROOT/bazinga/bazinga.db
"""

import sqlite3
import sys
import time
from pathlib import Path
import tempfile
import shutil
import subprocess

# Add _shared directory to path for bazinga_paths import
_script_dir = Path(__file__).parent.resolve()
_shared_dir = _script_dir.parent.parent / '_shared'
if _shared_dir.exists() and str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

try:
    from bazinga_paths import get_db_path
    _HAS_BAZINGA_PATHS = True
except ImportError:
    _HAS_BAZINGA_PATHS = False

# Current schema version
SCHEMA_VERSION = 15

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
            current_version = 2  # Advance version to enable subsequent migrations

        # Handle v2→v3 migration (add development_plans table)
        if current_version == 2:
            print("🔄 Migrating schema from v2 to v3...")
            # No data migration needed - just add new table
            # Table will be created below with CREATE TABLE IF NOT EXISTS
            print("✓ Migration to v3 complete (development_plans table added)")
            current_version = 3  # Advance version to enable subsequent migrations

        # Handle v3→v4 migration (add success_criteria table)
        if current_version == 3:
            print("🔄 Migrating schema from v3 to v4...")
            # No data migration needed - just add new table
            # Table will be created below with CREATE TABLE IF NOT EXISTS
            print("✓ Migration to v4 complete (success_criteria table added)")
            current_version = 4  # Advance version to enable subsequent migrations

        # Handle v4→v5 migration (merge-on-approval architecture)
        if current_version == 4:
            print("🔄 Migrating schema from v4 to v5...")

            # Check if sessions table exists (for fresh databases, skip all ALTER and let CREATE TABLE handle it)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            sessions_exists = cursor.fetchone() is not None

            if not sessions_exists:
                print("   ⊘ Base tables don't exist yet - will be created with full schema below")
                print("✓ Migration to v5 complete (fresh database, skipped)")
                current_version = 5  # Skip to next migration, CREATE TABLE will handle it
            else:
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

                    # CRITICAL: Table recreation must be atomic to prevent orphan indexes
                    # Use explicit transaction with exclusive locking
                    # See research/sqlite-orphan-index-corruption-ultrathink.md for full root cause analysis
                    # Close any implicit transaction before starting explicit one
                    conn.commit()
                    try:
                        cursor.execute("BEGIN IMMEDIATE")

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
                                last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED') OR last_review_status IS NULL),
                                feature_branch TEXT,
                                merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure') OR merge_status IS NULL),
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

                        # Swap tables atomically
                        cursor.execute("DROP TABLE task_groups")
                        cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")
                        cursor.execute("CREATE INDEX IF NOT EXISTS idx_taskgroups_session ON task_groups(session_id, status)")

                        # Verify integrity before committing
                        integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                        if integrity != "ok":
                            raise sqlite3.IntegrityError(f"Migration task_groups v4→v5: Database integrity check failed after table recreation: {integrity}")

                        # Use connection methods for commit/rollback (clearer than SQL strings)
                        conn.commit()

                        # Force WAL checkpoint to ensure clean state
                        # Returns (busy, log_frames, checkpointed_frames)
                        checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                        if checkpoint_result:
                            busy, log_frames, checkpointed = checkpoint_result
                            if busy:
                                # Checkpoint couldn't fully complete - retry with backoff
                                for retry in range(3):
                                    time.sleep(0.5 * (retry + 1))
                                    checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                                    if checkpoint_result and not checkpoint_result[0]:
                                        print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                                        break
                                else:
                                    print(f"   ⚠️ WAL checkpoint incomplete: busy={busy}, log={log_frames}, checkpointed={checkpointed}")
                            elif log_frames != checkpointed:
                                print(f"   ⚠️ WAL checkpoint partial: {checkpointed}/{log_frames} frames checkpointed")

                        # Post-commit integrity verification (validates final on-disk state)
                        # This is ADDITIONAL to pre-commit check - both are needed:
                        # - Pre-commit: Enables atomic rollback if corrupt
                        # - Post-commit: Validates finalized disk state after WAL flush
                        post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                        if post_integrity != "ok":
                            print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")
                            print(f"   ⚠️ Database may be corrupted. Consider: rm {db_path}*")

                        # Refresh query planner statistics after major schema change
                        cursor.execute("ANALYZE task_groups;")

                        print("   ✓ Recreated task_groups with expanded status enum")
                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception as rollback_exc:
                            print(f"   ! ROLLBACK failed: {rollback_exc}")
                        print(f"   ✗ v4→v5 migration failed during task_groups recreation, rolled back: {e}")
                        raise
                else:
                    print("   ⊘ task_groups status enum already expanded")

                print("✓ Migration to v5 complete (merge-on-approval architecture)")
                current_version = 5  # Advance version to enable subsequent migrations

        # Handle v5→v6 migration (context packages for inter-agent communication)
        if current_version == 5:
            print("🔄 Migrating schema from v5 to v6...")

            # Check if task_groups table exists (for fresh databases, skip ALTER)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_groups'")
            task_groups_exists = cursor.fetchone() is not None

            if not task_groups_exists:
                print("   ⊘ Base tables don't exist yet - will be created with full schema below")
                print("✓ Migration to v6 complete (fresh database, skipped)")
                current_version = 6
            else:
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
                current_version = 6

        # Migration from v6 to v7: Add specializations to task_groups
        if current_version == 6:
            print("🔄 Migrating schema from v6 to v7...")

            # Check if task_groups table exists (for fresh databases, skip ALTER)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_groups'")
            task_groups_exists = cursor.fetchone() is not None

            if not task_groups_exists:
                print("   ⊘ Base tables don't exist yet - will be created with full schema below")
                print("✓ Migration to v7 complete (fresh database, skipped)")
                current_version = 7
            else:
                # Add specializations column to task_groups
                try:
                    cursor.execute("ALTER TABLE task_groups ADD COLUMN specializations TEXT")
                    print("   ✓ Added task_groups.specializations")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ task_groups.specializations already exists")
                    else:
                        raise

                # CRITICAL: Force WAL checkpoint after schema change
                # Without this, subsequent writes can corrupt the schema catalog
                # causing "orphan index" errors on sqlite_autoindex_task_groups_1
                conn.commit()
                # Returns (busy, log_frames, checkpointed_frames)
                checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                if checkpoint_result:
                    busy, log_frames, checkpointed = checkpoint_result
                    if busy:
                        # Checkpoint couldn't fully complete - retry with backoff
                        for retry in range(3):
                            time.sleep(0.5 * (retry + 1))
                            checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                            if checkpoint_result and not checkpoint_result[0]:
                                print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                                break
                        else:
                            print(f"   ⚠️ WAL checkpoint incomplete: busy={busy}, log={log_frames}, checkpointed={checkpointed}")
                    elif log_frames != checkpointed:
                        print(f"   ⚠️ WAL checkpoint partial: {checkpointed}/{log_frames} frames checkpointed")

                # Post-commit integrity verification (validates final on-disk state)
                post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                if post_integrity != "ok":
                    print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")
                    print(f"   ⚠️ Database may be corrupted. Consider deleting and reinitializing.")

                current_version = 7  # Advance version

                # Refresh query planner statistics after schema change
                cursor.execute("ANALYZE task_groups;")
                print("   ✓ WAL checkpoint completed")

                print("✓ Migration to v7 complete (specializations for tech stack loading)")

        # Migration from v7 to v8: Add reasoning capture columns to orchestration_logs
        if current_version == 7:
            print("🔄 Migrating schema from v7 to v8...")

            # Check if orchestration_logs table exists (for fresh databases, skip ALTER)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orchestration_logs'")
            logs_exists = cursor.fetchone() is not None

            if not logs_exists:
                print("   ⊘ Base tables don't exist yet - will be created with full schema below")
                print("✓ Migration to v8 complete (fresh database, skipped)")
                current_version = 8
            else:
                # Add log_type column (defaults to 'interaction' for existing rows)
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN log_type TEXT DEFAULT 'interaction'
                    """)
                    print("   ✓ Added orchestration_logs.log_type")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.log_type already exists")
                    else:
                        raise

                # Add reasoning_phase column
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN reasoning_phase TEXT
                    """)
                    print("   ✓ Added orchestration_logs.reasoning_phase")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.reasoning_phase already exists")
                    else:
                        raise

                # Add confidence_level column
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN confidence_level TEXT
                    """)
                    print("   ✓ Added orchestration_logs.confidence_level")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.confidence_level already exists")
                    else:
                        raise

                # Add references_json column (JSON array of file paths consulted)
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN references_json TEXT
                    """)
                    print("   ✓ Added orchestration_logs.references_json")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.references_json already exists")
                    else:
                        raise

                # Add redacted column (1 if secrets were redacted)
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN redacted INTEGER DEFAULT 0
                    """)
                    print("   ✓ Added orchestration_logs.redacted")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.redacted already exists")
                    else:
                        raise

                # Add group_id column for reasoning context
                try:
                    cursor.execute("""
                        ALTER TABLE orchestration_logs
                        ADD COLUMN group_id TEXT
                    """)
                    print("   ✓ Added orchestration_logs.group_id")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print("   ⊘ orchestration_logs.group_id already exists")
                    else:
                        raise

                # Create index for reasoning queries
                try:
                    cursor.execute("""
                        CREATE INDEX idx_logs_reasoning
                        ON orchestration_logs(session_id, log_type, reasoning_phase)
                        WHERE log_type = 'reasoning'
                    """)
                    print("   ✓ Created idx_logs_reasoning index")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("   ⊘ idx_logs_reasoning index already exists")
                    else:
                        raise

                # Create index for group-based reasoning queries
                try:
                    cursor.execute("""
                        CREATE INDEX idx_logs_group_reasoning
                        ON orchestration_logs(session_id, group_id, log_type)
                        WHERE log_type = 'reasoning'
                    """)
                    print("   ✓ Created idx_logs_group_reasoning index")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("   ⊘ idx_logs_group_reasoning index already exists")
                    else:
                        raise

                # Commit and checkpoint
                conn.commit()
                checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                if checkpoint_result:
                    busy, log_frames, checkpointed = checkpoint_result
                    if busy:
                        for retry in range(3):
                            time.sleep(0.5 * (retry + 1))
                            checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                            if checkpoint_result and not checkpoint_result[0]:
                                print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                                break
                        else:
                            print(f"   ⚠️ WAL checkpoint incomplete: busy={busy}")

                # Post-commit integrity verification
                post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                if post_integrity != "ok":
                    print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")

                # Refresh query planner statistics
                cursor.execute("ANALYZE orchestration_logs;")
                print("   ✓ WAL checkpoint completed")

                current_version = 8
                print("✓ Migration to v8 complete (agent reasoning capture)")

        # Migration from v8 to v9: Add event logging and scope tracking
        if current_version == 8:
            print("🔄 Migrating schema from v8 to v9...")

            # Check if tables exist (for fresh databases, skip ALTER)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orchestration_logs'")
            logs_exists = cursor.fetchone() is not None
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            sessions_exists = cursor.fetchone() is not None
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_groups'")
            task_groups_exists = cursor.fetchone() is not None

            if not logs_exists and not sessions_exists:
                print("   ⊘ Base tables don't exist yet - will be created with full schema below")
                print("✓ Migration to v9 complete (fresh database, skipped)")
                current_version = 9
            else:
                # CRITICAL: Recreate orchestration_logs to update CHECK constraint
                # Old schema has CHECK(log_type IN ('interaction', 'reasoning'))
                # New schema needs CHECK(log_type IN ('interaction', 'reasoning', 'event'))
                # SQLite doesn't support ALTER TABLE to modify CHECK constraints
                #
                # SAFETY: Wrap in transaction to prevent data loss on error
                try:
                    cursor.execute("BEGIN IMMEDIATE")

                    if logs_exists:
                        print("   - Recreating orchestration_logs to update CHECK constraint...")

                        # Get column info to handle variable schemas
                        # IMPORTANT: Use ordered list (by cid) to ensure SELECT/INSERT column alignment
                        cursor.execute("PRAGMA table_info(orchestration_logs)")
                        col_info = cursor.fetchall()
                        # Sort by cid (column 0) to ensure deterministic order
                        col_info_sorted = sorted(col_info, key=lambda x: x[0])
                        col_names = [row[1] for row in col_info_sorted]  # Ordered list, not set

                        # Backup existing data with columns in consistent order
                        col_list = ', '.join(col_names)
                        cursor.execute(f"SELECT {col_list} FROM orchestration_logs")
                        logs_data = cursor.fetchall()
                        print(f"   - Backed up {len(logs_data)} orchestration log entries")

                        # Drop indexes first (they reference the table)
                        cursor.execute("DROP INDEX IF EXISTS idx_logs_session")
                        cursor.execute("DROP INDEX IF EXISTS idx_logs_agent_type")
                        cursor.execute("DROP INDEX IF EXISTS idx_logs_reasoning")
                        cursor.execute("DROP INDEX IF EXISTS idx_logs_events")

                        # Drop old table
                        cursor.execute("DROP TABLE orchestration_logs")

                        # Create new table with updated CHECK constraint (includes 'event')
                        cursor.execute("""
                            CREATE TABLE orchestration_logs (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                session_id TEXT NOT NULL,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                iteration INTEGER,
                                agent_type TEXT NOT NULL,
                                agent_id TEXT,
                                content TEXT NOT NULL,
                                log_type TEXT DEFAULT 'interaction'
                                    CHECK(log_type IN ('interaction', 'reasoning', 'event')),
                                reasoning_phase TEXT
                                    CHECK(reasoning_phase IS NULL OR reasoning_phase IN (
                                        'understanding', 'approach', 'decisions', 'risks',
                                        'blockers', 'pivot', 'completion'
                                    )),
                                confidence_level TEXT
                                    CHECK(confidence_level IS NULL OR confidence_level IN ('high', 'medium', 'low')),
                                references_json TEXT,
                                redacted INTEGER DEFAULT 0 CHECK(redacted IN (0, 1)),
                                group_id TEXT,
                                event_subtype TEXT,
                                event_payload TEXT,
                                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                            )
                        """)
                        print("   ✓ Created orchestration_logs with updated CHECK constraint")

                        # Restore data - map old columns to new schema
                        if logs_data:
                            # Build insert for columns that exist in both old and new
                            new_cols = {'id', 'session_id', 'timestamp', 'iteration', 'agent_type',
                                       'agent_id', 'content', 'log_type', 'reasoning_phase',
                                       'confidence_level', 'references_json', 'redacted', 'group_id',
                                       'event_subtype', 'event_payload'}
                            common_cols = [c for c in col_names if c in new_cols]
                            col_indices = {name: idx for idx, name in enumerate(col_names)}

                            placeholders = ', '.join(['?' for _ in common_cols])
                            insert_cols = ', '.join(common_cols)

                            for row in logs_data:
                                values = []
                                for c in common_cols:
                                    val = row[col_indices[c]]
                                    # Coalesce NULL log_type to 'interaction' (v8 ALTER TABLE didn't backfill existing rows)
                                    if c == 'log_type' and val is None:
                                        val = 'interaction'
                                    values.append(val)
                                cursor.execute(f"""
                                    INSERT INTO orchestration_logs ({insert_cols})
                                    VALUES ({placeholders})
                                """, values)
                            print(f"   ✓ Restored {len(logs_data)} orchestration log entries")

                        # Recreate indexes
                        cursor.execute("""
                            CREATE INDEX idx_logs_session
                            ON orchestration_logs(session_id, timestamp DESC)
                        """)
                        cursor.execute("""
                            CREATE INDEX idx_logs_agent_type
                            ON orchestration_logs(session_id, agent_type)
                        """)
                        cursor.execute("""
                            CREATE INDEX idx_logs_reasoning
                            ON orchestration_logs(session_id, log_type, reasoning_phase)
                            WHERE log_type = 'reasoning'
                        """)
                        print("   ✓ Recreated indexes")

                    # Commit the transaction for table recreation
                    cursor.execute("COMMIT")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    print(f"   ❌ Migration failed, rolled back: {e}")
                    raise

                # Add metadata column to sessions (for original_scope)
                if sessions_exists:
                    try:
                        cursor.execute("""
                            ALTER TABLE sessions
                            ADD COLUMN metadata TEXT
                        """)
                        print("   ✓ Added sessions.metadata")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ sessions.metadata already exists")
                        else:
                            raise

                # Add item_count column to task_groups
                if task_groups_exists:
                    try:
                        cursor.execute("""
                            ALTER TABLE task_groups
                            ADD COLUMN item_count INTEGER DEFAULT 1
                        """)
                        print("   ✓ Added task_groups.item_count")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ task_groups.item_count already exists")
                        else:
                            raise

                # Create index for event queries
                try:
                    cursor.execute("""
                        CREATE INDEX idx_logs_events
                        ON orchestration_logs(session_id, log_type, event_subtype)
                        WHERE log_type = 'event'
                    """)
                    print("   ✓ Created idx_logs_events index")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("   ⊘ idx_logs_events index already exists")
                    else:
                        raise

                # Commit and checkpoint
                conn.commit()
                checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                if checkpoint_result:
                    busy, log_frames, checkpointed = checkpoint_result
                    if busy:
                        for retry in range(3):
                            time.sleep(0.5 * (retry + 1))
                            checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                            if checkpoint_result and not checkpoint_result[0]:
                                print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                                break
                        else:
                            print(f"   ⚠️ WAL checkpoint incomplete: busy={busy}")

                # Post-commit integrity verification
                post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                if post_integrity != "ok":
                    print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")

                # Refresh query planner statistics
                cursor.execute("ANALYZE orchestration_logs;")
                cursor.execute("ANALYZE sessions;")
                cursor.execute("ANALYZE task_groups;")
                print("   ✓ WAL checkpoint completed")

                current_version = 9
                print("✓ Migration to v9 complete (event logging and scope tracking)")

        # Migration from v9 to v10: Context Engineering System tables
        if current_version == 9:
            print("🔄 Migrating schema from v9 to v10...")

            # Wrap entire migration in transaction for atomicity
            conn.commit()  # Close any implicit transaction
            try:
                cursor.execute("BEGIN IMMEDIATE")

                # T004: Extend context_packages with priority and summary columns
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='context_packages'")
                if cursor.fetchone():
                    # Add priority column if it doesn't exist
                    cursor.execute("PRAGMA table_info(context_packages)")
                    existing_cols = {row[1] for row in cursor.fetchall()}

                    if 'priority' not in existing_cols:
                        cursor.execute("""
                            ALTER TABLE context_packages
                            ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'
                            CHECK(priority IN ('low', 'medium', 'high', 'critical'))
                        """)
                        # Backfill any NULLs (safety for older SQLite versions)
                        cursor.execute("UPDATE context_packages SET priority = 'medium' WHERE priority IS NULL")
                        print("   ✓ Added context_packages.priority")
                    else:
                        print("   ⊘ context_packages.priority already exists")

                    if 'summary' not in existing_cols:
                        cursor.execute("""
                            ALTER TABLE context_packages
                            ADD COLUMN summary TEXT
                        """)
                        print("   ✓ Added context_packages.summary")
                    else:
                        print("   ⊘ context_packages.summary already exists")

                    # Create composite index for relevance ranking (per data-model.md)
                    # IF NOT EXISTS handles the case where index already exists
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_packages_priority_ranking
                        ON context_packages(session_id, priority, created_at DESC)
                    """)
                    print("   ✓ Created idx_packages_priority_ranking composite index")

                # Create error_patterns table for learning from failed-then-succeeded agents
                # Uses composite primary key (pattern_hash, project_id) to allow same pattern across projects
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS error_patterns (
                        pattern_hash TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        signature_json TEXT NOT NULL,
                        solution TEXT NOT NULL,
                        confidence REAL DEFAULT 0.5 CHECK(confidence >= 0.0 AND confidence <= 1.0),
                        occurrences INTEGER DEFAULT 1 CHECK(occurrences >= 1),
                        lang TEXT,
                        last_seen TEXT DEFAULT (datetime('now')),
                        created_at TEXT DEFAULT (datetime('now')),
                        ttl_days INTEGER DEFAULT 90 CHECK(ttl_days > 0),
                        PRIMARY KEY (pattern_hash, project_id)
                    )
                """)
                print("   ✓ Created error_patterns table")

                # Create indexes for error_patterns
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_patterns_project
                    ON error_patterns(project_id, lang)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_patterns_ttl
                    ON error_patterns(last_seen, ttl_days)
                """)
                print("   ✓ Created error_patterns indexes")

                # Create strategies table for successful approaches
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strategies (
                        strategy_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        insight TEXT NOT NULL,
                        helpfulness INTEGER DEFAULT 0 CHECK(helpfulness >= 0),
                        lang TEXT,
                        framework TEXT,
                        last_seen TEXT DEFAULT (datetime('now')),
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                print("   ✓ Created strategies table")

                # Create indexes for strategies
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_strategies_project
                    ON strategies(project_id, framework)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_strategies_topic
                    ON strategies(topic)
                """)
                print("   ✓ Created strategies indexes")

                # Create consumption_scope table for iteration-aware package tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS consumption_scope (
                        scope_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        group_id TEXT NOT NULL,
                        agent_type TEXT NOT NULL CHECK(agent_type IN ('developer', 'qa_expert', 'tech_lead', 'senior_software_engineer', 'investigator')),
                        iteration INTEGER NOT NULL CHECK(iteration >= 0),
                        package_id INTEGER NOT NULL,
                        consumed_at TEXT DEFAULT (datetime('now')),
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                        FOREIGN KEY (package_id) REFERENCES context_packages(id) ON DELETE CASCADE
                    )
                """)
                print("   ✓ Created consumption_scope table")

                # Create indexes for consumption_scope
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_consumption_session
                    ON consumption_scope(session_id, group_id, agent_type)
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_consumption_unique
                    ON consumption_scope(session_id, group_id, agent_type, iteration, package_id)
                """)
                print("   ✓ Created consumption_scope indexes")

                # Verify integrity before committing
                integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                if integrity != "ok":
                    raise sqlite3.IntegrityError(f"Migration v9→v10: Database integrity check failed: {integrity}")

                conn.commit()
                print("   ✓ Migration transaction committed")

            except Exception as e:
                try:
                    conn.rollback()
                except Exception as rollback_exc:
                    print(f"   ! ROLLBACK failed: {rollback_exc}")
                print(f"   ✗ v9→v10 migration failed, rolled back: {e}")
                raise

            # WAL checkpoint after successful commit
            checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
            if checkpoint_result:
                busy, log_frames, checkpointed = checkpoint_result
                if busy:
                    for retry in range(3):
                        time.sleep(0.5 * (retry + 1))
                        checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                        if checkpoint_result and not checkpoint_result[0]:
                            print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                            break
                    else:
                        # Log the latest checkpoint result, not the stale one
                        final_busy = checkpoint_result[0] if checkpoint_result else busy
                        print(f"   ⚠️ WAL checkpoint incomplete: busy={final_busy}")

            # Post-commit integrity verification
            post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
            if post_integrity != "ok":
                print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")

            # Refresh query planner statistics for newly created tables
            cursor.execute("ANALYZE error_patterns;")
            cursor.execute("ANALYZE strategies;")
            cursor.execute("ANALYZE consumption_scope;")
            # context_packages is analyzed later after CREATE TABLE IF NOT EXISTS
            print("   ✓ WAL checkpoint completed")

            current_version = 10
            print("✓ Migration to v10 complete (context engineering system tables)")

        # v10 → v11: Skill outputs multi-invocation support
        if current_version == 10:
            print("\n--- Migrating v10 → v11 (skill outputs multi-invocation) ---")

            # Check if skill_outputs table exists (may not exist in fresh DBs during sequential migration)
            table_exists = cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='skill_outputs'
            """).fetchone()

            if not table_exists:
                # Table will be created later with new columns - skip migration
                print("   ⊘ skill_outputs table will be created with new columns")
            else:
                try:
                    # Use BEGIN IMMEDIATE to acquire exclusive lock for DDL safety
                    cursor.execute("BEGIN IMMEDIATE")

                    # Check existing columns in skill_outputs
                    columns = {row[1] for row in cursor.execute("PRAGMA table_info(skill_outputs)").fetchall()}

                    # Add agent_type column
                    if 'agent_type' not in columns:
                        cursor.execute("""
                            ALTER TABLE skill_outputs
                            ADD COLUMN agent_type TEXT
                        """)
                        print("   ✓ Added skill_outputs.agent_type")
                    else:
                        print("   ⊘ skill_outputs.agent_type already exists")

                    # Add group_id column
                    if 'group_id' not in columns:
                        cursor.execute("""
                            ALTER TABLE skill_outputs
                            ADD COLUMN group_id TEXT
                        """)
                        print("   ✓ Added skill_outputs.group_id")
                    else:
                        print("   ⊘ skill_outputs.group_id already exists")

                    # Add iteration column (default 1 for existing rows)
                    if 'iteration' not in columns:
                        cursor.execute("""
                            ALTER TABLE skill_outputs
                            ADD COLUMN iteration INTEGER DEFAULT 1
                        """)
                        print("   ✓ Added skill_outputs.iteration")
                    else:
                        print("   ⊘ skill_outputs.iteration already exists")

                    # Create composite index for efficient lookups
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_skill_agent_group
                        ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)
                    """)
                    print("   ✓ Created idx_skill_agent_group composite index")

                    # Verify integrity
                    integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                    if integrity != "ok":
                        raise sqlite3.IntegrityError(f"Migration v10→v11: Integrity check failed: {integrity}")

                    conn.commit()
                    print("   ✓ Migration transaction committed")

                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"   ✗ v10→v11 migration failed, rolled back: {e}")
                    raise

            current_version = 11
            print("✓ Migration to v11 complete (skill outputs multi-invocation)")

        # v11 → v12: Add UNIQUE constraint to skill_outputs for race condition prevention
        if current_version == 11:
            print("\n--- Migrating v11 → v12 (skill_outputs UNIQUE constraint) ---")

            # Check if skill_outputs table exists
            table_exists = cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='skill_outputs'
            """).fetchone()

            if not table_exists:
                # Table will be created later with UNIQUE constraint - skip migration
                print("   ⊘ skill_outputs table will be created with UNIQUE constraint")
            else:
                try:
                    # Use BEGIN IMMEDIATE for exclusive lock during DDL
                    cursor.execute("BEGIN IMMEDIATE")

                    # Check if UNIQUE index already exists
                    existing_index = cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='index' AND name='idx_skill_unique_iteration'
                    """).fetchone()

                    if not existing_index:
                        # SQLite doesn't support ADD CONSTRAINT for UNIQUE on existing table
                        # Create a UNIQUE INDEX instead (functionally equivalent)
                        cursor.execute("""
                            CREATE UNIQUE INDEX idx_skill_unique_iteration
                            ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)
                        """)
                        print("   ✓ Created UNIQUE index idx_skill_unique_iteration")
                    else:
                        print("   ⊘ UNIQUE index idx_skill_unique_iteration already exists")

                    # Create DESC index for "latest" queries optimization
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_skill_latest
                        ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration DESC)
                    """)
                    print("   ✓ Created idx_skill_latest (DESC) for latest queries")

                    # Verify integrity
                    integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                    if integrity != "ok":
                        raise sqlite3.IntegrityError(f"Migration v11→v12: Integrity check failed: {integrity}")

                    conn.commit()
                    print("   ✓ Migration transaction committed")

                except sqlite3.IntegrityError as e:
                    conn.rollback()
                    if "UNIQUE constraint failed" in str(e):
                        print(f"   ⚠️ UNIQUE constraint violation found - handling duplicates...")
                        # Handle duplicate iterations by renumbering
                        cursor.execute("BEGIN IMMEDIATE")
                        cursor.execute("""
                            UPDATE skill_outputs SET iteration = (
                                SELECT COUNT(*)
                                FROM skill_outputs s2
                                WHERE s2.session_id = skill_outputs.session_id
                                  AND s2.skill_name = skill_outputs.skill_name
                                  AND COALESCE(s2.agent_type, '') = COALESCE(skill_outputs.agent_type, '')
                                  AND COALESCE(s2.group_id, '') = COALESCE(skill_outputs.group_id, '')
                                  AND s2.timestamp <= skill_outputs.timestamp
                            )
                        """)
                        cursor.execute("""
                            CREATE UNIQUE INDEX idx_skill_unique_iteration
                            ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)
                        """)
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS idx_skill_latest
                            ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration DESC)
                        """)
                        conn.commit()
                        print("   ✓ Fixed duplicate iterations and created UNIQUE index")
                    else:
                        print(f"   ✗ v11→v12 migration failed: {e}")
                        raise

                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"   ✗ v11→v12 migration failed, rolled back: {e}")
                    raise

            current_version = 12
            print("✓ Migration to v12 complete (skill_outputs UNIQUE constraint)")

        # v12 → v13: Deterministic orchestration tables
        if current_version == 12:
            print("\n--- Migrating v12 → v13 (deterministic orchestration) ---")

            try:
                cursor.execute("BEGIN IMMEDIATE")

                # Create workflow_transitions table (seeded from workflow/transitions.json)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_transitions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        current_agent TEXT NOT NULL,
                        response_status TEXT NOT NULL,
                        next_agent TEXT,
                        action TEXT NOT NULL,
                        include_context TEXT,
                        escalation_check INTEGER DEFAULT 0,
                        model_override TEXT,
                        fallback_agent TEXT,
                        bypass_qa INTEGER DEFAULT 0,
                        max_parallel INTEGER,
                        then_action TEXT,
                        UNIQUE(current_agent, response_status)
                    )
                """)
                # Add index for performance (matches fresh DB path)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_wt_agent
                    ON workflow_transitions(current_agent)
                """)
                print("   ✓ Created workflow_transitions table with index")

                # Create agent_markers table (seeded from workflow/agent-markers.json)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_markers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_type TEXT NOT NULL UNIQUE,
                        required_markers TEXT NOT NULL,
                        workflow_markers TEXT
                    )
                """)
                print("   ✓ Created agent_markers table")

                # Create workflow_special_rules table (seeded from workflow/transitions.json _special_rules)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_special_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL UNIQUE,
                        description TEXT,
                        config TEXT NOT NULL
                    )
                """)
                print("   ✓ Created workflow_special_rules table")

                # Verify integrity
                integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                if integrity != "ok":
                    raise sqlite3.IntegrityError(f"Migration v12→v13: Integrity check failed: {integrity}")

                conn.commit()
                print("   ✓ Migration transaction committed")

            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                print(f"   ✗ v12→v13 migration failed, rolled back: {e}")
                raise

            current_version = 13
            print("✓ Migration to v13 complete (deterministic orchestration tables)")

        # v13 → v14: Add escalation tracking columns to task_groups
        if current_version == 13:
            print("\n--- Migrating v13 → v14 (escalation tracking columns) ---")

            # Check if task_groups table exists (may not exist in fresh DBs during sequential migration)
            table_exists = cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='task_groups'
            """).fetchone()

            if not table_exists:
                # Table will be created later with new columns - skip migration
                print("   ⊘ task_groups table will be created with new columns")
            else:
                try:
                    # Add security_sensitive column
                    try:
                        cursor.execute("ALTER TABLE task_groups ADD COLUMN security_sensitive INTEGER DEFAULT 0")
                        print("   ✓ Added task_groups.security_sensitive")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ task_groups.security_sensitive already exists")
                        else:
                            raise

                    # Add qa_attempts column for QA failure escalation
                    try:
                        cursor.execute("ALTER TABLE task_groups ADD COLUMN qa_attempts INTEGER DEFAULT 0")
                        print("   ✓ Added task_groups.qa_attempts")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ task_groups.qa_attempts already exists")
                        else:
                            raise

                    # Add tl_review_attempts column for TL review loop tracking
                    try:
                        cursor.execute("ALTER TABLE task_groups ADD COLUMN tl_review_attempts INTEGER DEFAULT 0")
                        print("   ✓ Added task_groups.tl_review_attempts")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ task_groups.tl_review_attempts already exists")
                        else:
                            raise

                    conn.commit()

                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"   ✗ v13→v14 migration failed, rolled back: {e}")
                    raise

            current_version = 14
            print("✓ Migration to v14 complete (escalation tracking columns)")

        # v14 → v15: Add component_path for version-specific prompt building
        if current_version == 14:
            print("\n--- Migrating v14 → v15 (component_path for version context) ---")

            # Check if task_groups table exists
            table_exists = cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='task_groups'
            """).fetchone()

            if not table_exists:
                # Table will be created later with new columns - skip migration
                print("   ⊘ task_groups table will be created with component_path column")
            else:
                try:
                    cursor.execute("BEGIN IMMEDIATE")

                    # Add component_path column for monorepo component binding
                    try:
                        cursor.execute("ALTER TABLE task_groups ADD COLUMN component_path TEXT")
                        print("   ✓ Added task_groups.component_path")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            print("   ⊘ task_groups.component_path already exists")
                        else:
                            raise

                    # Verify integrity before commit
                    integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                    if integrity != "ok":
                        raise sqlite3.IntegrityError(f"Migration v14→v15: Integrity check failed: {integrity}")

                    conn.commit()
                    print("   ✓ Migration transaction committed")

                    # WAL checkpoint for clean state
                    checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                    if checkpoint_result:
                        busy, log_frames, checkpointed = checkpoint_result
                        if busy:
                            for retry in range(3):
                                time.sleep(0.5 * (retry + 1))
                                checkpoint_result = cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                                if checkpoint_result and not checkpoint_result[0]:
                                    print(f"   ✓ WAL checkpoint succeeded after retry {retry + 1}")
                                    break
                            else:
                                print(f"   ⚠️ WAL checkpoint incomplete: busy={busy}")

                    # Post-commit integrity verification
                    post_integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                    if post_integrity != "ok":
                        print(f"   ⚠️ Post-commit integrity check failed: {post_integrity}")

                    # Refresh query planner statistics
                    cursor.execute("ANALYZE task_groups;")
                    print("   ✓ WAL checkpoint completed")

                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    print(f"   ✗ v14→v15 migration failed, rolled back: {e}")
                    raise

            current_version = 15
            print("✓ Migration to v15 complete (component_path for version context)")

        # Record version upgrade
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES (?, ?)
        """, (SCHEMA_VERSION, f"Schema v{SCHEMA_VERSION}: Context engineering system tables"))
        conn.commit()
        print(f"✓ Schema upgraded to v{SCHEMA_VERSION}")
    elif current_version == SCHEMA_VERSION:
        print(f"✓ Schema is up-to-date (v{SCHEMA_VERSION})")

    print("\nCreating/verifying BAZINGA database schema...")

    # Sessions table
    # Extended in v9 to support metadata (JSON) for original_scope tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            mode TEXT CHECK(mode IN ('simple', 'parallel')),
            original_requirements TEXT,
            status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
            initial_branch TEXT DEFAULT 'main',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created sessions table")

    # Orchestration logs table (replaces orchestration-log.md)
    # Extended in v8 to support agent reasoning capture
    # Extended in v9 to support event logging (pm_bazinga, scope_change, validator_verdict)
    # CHECK constraints enforce valid enumeration values at database layer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orchestration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            iteration INTEGER,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            content TEXT NOT NULL,
            log_type TEXT DEFAULT 'interaction'
                CHECK(log_type IN ('interaction', 'reasoning', 'event')),
            reasoning_phase TEXT
                CHECK(reasoning_phase IS NULL OR reasoning_phase IN (
                    'understanding', 'approach', 'decisions', 'risks',
                    'blockers', 'pivot', 'completion'
                )),
            confidence_level TEXT
                CHECK(confidence_level IS NULL OR confidence_level IN ('high', 'medium', 'low')),
            references_json TEXT,
            redacted INTEGER DEFAULT 0 CHECK(redacted IN (0, 1)),
            group_id TEXT,
            event_subtype TEXT,
            event_payload TEXT,
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
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_reasoning
        ON orchestration_logs(session_id, log_type, reasoning_phase)
        WHERE log_type = 'reasoning'
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_group_reasoning
        ON orchestration_logs(session_id, group_id, log_type)
        WHERE log_type = 'reasoning'
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_events
        ON orchestration_logs(session_id, log_type, event_subtype)
        WHERE log_type = 'event'
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
    # Extended in v9 to support item_count for progress tracking
    # Extended in v14 to support security_sensitive, qa_attempts, tl_review_attempts
    # Extended in v15 to support component_path for version-specific prompt building
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
            specializations TEXT,
            item_count INTEGER DEFAULT 1,
            security_sensitive INTEGER DEFAULT 0,
            qa_attempts INTEGER DEFAULT 0,
            tl_review_attempts INTEGER DEFAULT 0,
            component_path TEXT,
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
    # v11: Added agent_type, group_id, iteration for multi-invocation support
    # v12: Added UNIQUE constraint on iteration for race condition prevention
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            skill_name TEXT NOT NULL,
            output_data TEXT NOT NULL,
            agent_type TEXT,
            group_id TEXT,
            iteration INTEGER DEFAULT 1,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_skill_session
        ON skill_outputs(session_id, skill_name, timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_skill_agent_group
        ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)
    """)
    # v12: UNIQUE index for race condition prevention
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_skill_unique_iteration
        ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)
    """)
    # v12: DESC index for "latest" query optimization
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_skill_latest
        ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration DESC)
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
            priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cp_created ON context_packages(created_at)")
    # Composite index for relevance ranking queries (per data-model.md)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_packages_priority_ranking ON context_packages(session_id, priority, created_at DESC)")
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

    # Error patterns table (for context engineering - learning from failed-then-succeeded agents)
    # Uses composite primary key (pattern_hash, project_id) to allow same pattern across projects
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_patterns (
            pattern_hash TEXT NOT NULL,
            project_id TEXT NOT NULL,
            signature_json TEXT NOT NULL,
            solution TEXT NOT NULL,
            confidence REAL DEFAULT 0.5 CHECK(confidence >= 0.0 AND confidence <= 1.0),
            occurrences INTEGER DEFAULT 1 CHECK(occurrences >= 1),
            lang TEXT,
            last_seen TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now')),
            ttl_days INTEGER DEFAULT 90 CHECK(ttl_days > 0),
            PRIMARY KEY (pattern_hash, project_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_project ON error_patterns(project_id, lang)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_ttl ON error_patterns(last_seen, ttl_days)")
    print("✓ Created error_patterns table with indexes")

    # Strategies table (for context engineering - successful approaches from completions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            insight TEXT NOT NULL,
            helpfulness INTEGER DEFAULT 0 CHECK(helpfulness >= 0),
            lang TEXT,
            framework TEXT,
            last_seen TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategies_project ON strategies(project_id, framework)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategies_topic ON strategies(topic)")
    print("✓ Created strategies table with indexes")

    # Consumption scope table (for context engineering - iteration-aware package tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumption_scope (
            scope_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            agent_type TEXT NOT NULL CHECK(agent_type IN ('developer', 'qa_expert', 'tech_lead', 'senior_software_engineer', 'investigator')),
            iteration INTEGER NOT NULL CHECK(iteration >= 0),
            package_id INTEGER NOT NULL,
            consumed_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES context_packages(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_consumption_session ON consumption_scope(session_id, group_id, agent_type)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_consumption_unique ON consumption_scope(session_id, group_id, agent_type, iteration, package_id)")
    print("✓ Created consumption_scope table with indexes")

    # Workflow transitions table (seeded from workflow/transitions.json via bazinga/config symlink)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_agent TEXT NOT NULL,
            response_status TEXT NOT NULL,
            next_agent TEXT,
            action TEXT NOT NULL,
            include_context TEXT,
            escalation_check INTEGER DEFAULT 0,
            model_override TEXT,
            fallback_agent TEXT,
            bypass_qa INTEGER DEFAULT 0,
            max_parallel INTEGER,
            then_action TEXT,
            UNIQUE(current_agent, response_status)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wt_agent ON workflow_transitions(current_agent)")
    print("✓ Created workflow_transitions table with indexes")

    # Agent markers table (seeded from workflow/agent-markers.json via bazinga/config symlink)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_type TEXT NOT NULL UNIQUE,
            required_markers TEXT NOT NULL,
            workflow_markers TEXT
        )
    """)
    print("✓ Created agent_markers table")

    # Workflow special rules table (seeded from workflow/transitions.json _special_rules)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_special_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT NOT NULL UNIQUE,
            description TEXT,
            config TEXT NOT NULL
        )
    """)
    print("✓ Created workflow_special_rules table")

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
    # Determine database path
    if len(sys.argv) >= 2:
        # Explicit path provided
        db_path = sys.argv[1]
    elif _HAS_BAZINGA_PATHS:
        # Auto-detect using bazinga_paths
        try:
            db_path = str(get_db_path())
            print(f"Auto-detected database path: {db_path}")
        except RuntimeError as e:
            print(f"Error: Could not auto-detect database path: {e}", file=sys.stderr)
            print("Usage: python init_db.py [database_path]", file=sys.stderr)
            print("Example: python init_db.py bazinga/bazinga.db", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python init_db.py <database_path>", file=sys.stderr)
        print("Example: python init_db.py bazinga/bazinga.db", file=sys.stderr)
        sys.exit(1)

    # Create parent directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    init_database(db_path)

    # Auto-seed workflow configs from JSON files
    # This ensures workflow_transitions table is populated after DB creation
    seed_script = _script_dir.parent.parent / "config-seeder" / "scripts" / "seed_configs.py"
    if seed_script.exists():
        print("\n📦 Seeding workflow configurations...")
        result = subprocess.run(
            [sys.executable, str(seed_script), "--db", db_path, "--all"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Print seed_configs output (already has ✅ prefix)
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            print(f"⚠️  Config seeding failed: {result.stderr.strip()}", file=sys.stderr)
            # Don't exit - database is still usable, just without seeded configs
    else:
        print(f"⚠️  Config seeder not found at {seed_script}", file=sys.stderr)


if __name__ == "__main__":
    main()
