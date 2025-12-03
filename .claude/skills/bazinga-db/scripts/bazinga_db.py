#!/usr/bin/env python3
"""
BAZINGA Database Client - Simple command interface for database operations.
Provides high-level commands for agents without requiring SQL knowledge.
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse


class BazingaDB:
    """Database client for BAZINGA orchestration."""

    # SQLite errors that indicate ACTUAL database corruption (file is unrecoverable)
    # NOTE: Transient errors like "database is locked" or "disk I/O error" are NOT
    # included here - they should be retried, not trigger database deletion!
    CORRUPTION_ERRORS = [
        "database disk image is malformed",
        "file is not a database",
        "database or disk is full",
        "attempt to write a readonly database",
    ]

    def __init__(self, db_path: str, quiet: bool = False):
        self.db_path = db_path
        self.quiet = quiet
        self._ensure_db_exists()

    def _print_success(self, message: str):
        """Print success message unless in quiet mode."""
        if not self.quiet:
            print(message)

    def _print_error(self, message: str):
        """Print error message to stderr."""
        print(f"! {message}", file=sys.stderr)

    def _is_corruption_error(self, error: Exception) -> bool:
        """Check if an exception indicates database corruption."""
        error_msg = str(error).lower()
        return any(corruption in error_msg for corruption in self.CORRUPTION_ERRORS)

    def _backup_corrupted_db(self) -> Optional[str]:
        """Backup a corrupted database file before recovery."""
        db_path = Path(self.db_path)
        if not db_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.with_suffix(f".corrupted_{timestamp}.db")
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self._print_error(f"Corrupted database backed up to: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self._print_error(f"Failed to backup corrupted database: {e}")
            return None

    def _extract_salvageable_data(self) -> Dict[str, List[tuple]]:
        """Try to extract data from a corrupted database before recovery.

        Returns:
            Dict mapping table names to list of row tuples. Empty dict if extraction fails.
        """
        salvaged = {}
        tables_to_try = [
            'sessions', 'orchestration_logs', 'state_snapshots', 'task_groups',
            'token_usage', 'skill_outputs', 'development_plans', 'success_criteria',
            'context_packages', 'context_package_consumers'
        ]

        try:
            # Use a short timeout - if DB is badly corrupted, don't hang
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()

            for table in tables_to_try:
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    if rows:
                        # Get column names for this table
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]
                        salvaged[table] = {'columns': columns, 'rows': rows}
                        self._print_error(f"  Salvaged {len(rows)} rows from {table}")
                except sqlite3.Error:
                    # Table doesn't exist or is unreadable - skip
                    pass

            conn.close()
        except Exception as e:
            self._print_error(f"  Could not extract data: {e}")
            return {}

        return salvaged

    def _restore_salvaged_data(self, salvaged: Dict[str, Dict]) -> int:
        """Restore salvaged data to the new database.

        Args:
            salvaged: Dict from _extract_salvageable_data()

        Returns:
            Number of rows restored.
        """
        if not salvaged:
            return 0

        total_restored = 0

        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()

            # Restore in order to respect foreign keys
            restore_order = [
                'sessions', 'orchestration_logs', 'state_snapshots', 'task_groups',
                'token_usage', 'skill_outputs', 'development_plans', 'success_criteria',
                'context_packages', 'context_package_consumers'
            ]

            for table in restore_order:
                if table not in salvaged:
                    continue

                data = salvaged[table]
                columns = data['columns']
                rows = data['rows']

                if not rows:
                    continue

                # Build INSERT statement
                placeholders = ', '.join(['?' for _ in columns])
                cols_str = ', '.join(columns)

                restored_count = 0
                for row in rows:
                    try:
                        cursor.execute(
                            f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})",
                            row
                        )
                        if cursor.rowcount > 0:
                            restored_count += 1
                    except sqlite3.Error:
                        # Skip rows that fail (e.g., constraint violations)
                        pass

                if restored_count > 0:
                    self._print_error(f"  Restored {restored_count}/{len(rows)} rows to {table}")
                    total_restored += restored_count

            conn.commit()
            conn.close()
        except Exception as e:
            self._print_error(f"  Error restoring data: {e}")

        return total_restored

    def _recover_from_corruption(self) -> bool:
        """Attempt to recover from database corruption by reinitializing.

        Tries to salvage data from the old database before replacing it.

        Returns:
            True if recovery succeeded, False otherwise.
        """
        self._print_error("Database corruption detected. Attempting recovery...")

        # Step 1: Try to salvage data before doing anything destructive
        self._print_error("Attempting to salvage data from corrupted database...")
        salvaged_data = self._extract_salvageable_data()

        # Step 2: Backup corrupted file
        self._backup_corrupted_db()

        # Step 3: Delete corrupted file
        db_path = Path(self.db_path)
        try:
            if db_path.exists():
                db_path.unlink()
        except Exception as e:
            self._print_error(f"Failed to remove corrupted database: {e}")
            return False

        # Step 4: Reinitialize with fresh schema
        try:
            script_dir = Path(__file__).parent
            init_script = script_dir / "init_db.py"

            import subprocess
            result = subprocess.run(
                [sys.executable, str(init_script), self.db_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self._print_error(f"Failed to reinitialize database: {result.stderr}")
                return False

        except Exception as e:
            self._print_error(f"Recovery failed: {e}")
            return False

        # Step 5: Restore salvaged data
        if salvaged_data:
            self._print_error("Restoring salvaged data to new database...")
            restored = self._restore_salvaged_data(salvaged_data)
            if restored > 0:
                self._print_error(f"✓ Database recovered with {restored} rows restored")
            else:
                self._print_error(f"✓ Database recovered (no data could be restored)")
        else:
            self._print_error(f"✓ Database recovered and reinitialized (fresh start)")

        return True

    def check_integrity(self) -> Dict[str, Any]:
        """Run SQLite integrity check on the database.

        Returns:
            Dict with 'ok' bool and 'details' string.
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            conn.close()

            if result == "ok":
                return {"ok": True, "details": "Database integrity check passed"}
            else:
                return {"ok": False, "details": f"Integrity issues found: {result}"}
        except Exception as e:
            return {"ok": False, "details": f"Integrity check failed: {e}"}

    def _ensure_db_exists(self):
        """Ensure database exists and has schema, create if not."""
        db_path = Path(self.db_path)
        needs_init = False
        is_corrupted = False

        if not db_path.exists():
            needs_init = True
            print(f"Database not found at {self.db_path}. Auto-initializing...", file=sys.stderr)
        elif db_path.stat().st_size == 0:
            needs_init = True
            print(f"Database file is empty at {self.db_path}. Auto-initializing...", file=sys.stderr)
        else:
            # File exists and has content - check if it has tables and is not corrupted
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    # First check integrity
                    integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                    if integrity != "ok":
                        is_corrupted = True
                        needs_init = True
                        print(f"Database corrupted at {self.db_path}: {integrity}. Auto-recovering...", file=sys.stderr)
                    else:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                        if not cursor.fetchone():
                            needs_init = True
                            print(f"Database missing schema at {self.db_path}. Auto-initializing...", file=sys.stderr)
            except sqlite3.DatabaseError as e:
                is_corrupted = True
                needs_init = True
                print(f"Database corrupted at {self.db_path}: {e}. Auto-recovering...", file=sys.stderr)
            except Exception as e:
                needs_init = True
                print(f"Database check failed at {self.db_path}: {e}. Auto-initializing...", file=sys.stderr)

        if not needs_init:
            return

        # If corrupted, backup and delete before reinitializing
        if is_corrupted and db_path.exists():
            self._backup_corrupted_db()
            try:
                db_path.unlink()
                print(f"Removed corrupted database file", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not remove corrupted file: {e}", file=sys.stderr)

        # Auto-initialize the database
        script_dir = Path(__file__).parent
        init_script = script_dir / "init_db.py"

        import subprocess
        result = subprocess.run(
            [sys.executable, str(init_script), self.db_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Failed to initialize database: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        print(f"✓ Database auto-initialized at {self.db_path}", file=sys.stderr)

    def _get_connection(self, retry_on_corruption: bool = True) -> sqlite3.Connection:
        """Get database connection with proper settings.

        Args:
            retry_on_corruption: If True, attempt recovery on corruption errors.

        Returns:
            sqlite3.Connection with WAL mode and foreign keys enabled.
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            # Enable WAL mode for better concurrency (reduces "database is locked" errors)
            conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Increase busy timeout to handle concurrent access
            conn.execute("PRAGMA busy_timeout = 30000")
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.DatabaseError as e:
            if retry_on_corruption and self._is_corruption_error(e):
                if self._recover_from_corruption():
                    # Retry connection after recovery
                    return self._get_connection(retry_on_corruption=False)
            raise

    # ==================== SESSION OPERATIONS ====================

    def create_session(self, session_id: str, mode: str, requirements: str) -> Dict[str, Any]:
        """Create a new session with validation."""
        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if mode not in ['simple', 'parallel']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'simple' or 'parallel'")
        if not requirements or not requirements.strip():
            raise ValueError("requirements cannot be empty")

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO sessions (session_id, mode, original_requirements, status)
                VALUES (?, ?, ?, 'active')
            """, (session_id, mode, requirements))
            conn.commit()

            # Verify the insert by reading it back
            verify = conn.execute("""
                SELECT session_id, mode, status, start_time, created_at
                FROM sessions WHERE session_id = ?
            """, (session_id,)).fetchone()

            if not verify:
                raise RuntimeError(f"Failed to verify session creation for {session_id}")

            result = {
                'success': True,
                'session_id': verify['session_id'],
                'mode': verify['mode'],
                'status': verify['status'],
                'start_time': verify['start_time'],
                'created_at': verify['created_at']
            }

            self._print_success(f"✓ Session created: {session_id}")
            return result

        except sqlite3.IntegrityError as e:
            error_msg = str(e).lower()
            if "unique constraint" in error_msg or "primary key" in error_msg:
                # Session already exists - return existing session info
                existing = conn.execute("""
                    SELECT session_id, mode, status, start_time, created_at
                    FROM sessions WHERE session_id = ?
                """, (session_id,)).fetchone()

                if existing:
                    self._print_success(f"✓ Session already exists: {session_id}")
                    return dict(existing)
                else:
                    raise RuntimeError(f"Session reported as existing but not found: {session_id}")
            else:
                # Other integrity error (e.g., foreign key, check constraint)
                raise RuntimeError(f"Database constraint violation: {e}")
        finally:
            conn.close()

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status."""
        conn = self._get_connection()
        end_time = datetime.now().isoformat() if status in ['completed', 'failed'] else None
        conn.execute("""
            UPDATE sessions
            SET status = ?, end_time = ?
            WHERE session_id = ?
        """, (status, end_time, session_id))
        conn.commit()
        conn.close()
        self._print_success(f"✓ Session {session_id} status updated to: {status}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details."""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent sessions ordered by created_at (most recent first)."""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== LOG OPERATIONS ====================

    def log_interaction(self, session_id: str, agent_type: str, content: str,
                       iteration: Optional[int] = None, agent_id: Optional[str] = None,
                       _retry_count: int = 0) -> Dict[str, Any]:
        """Log an agent interaction with validation.

        Args:
            _retry_count: Internal parameter to prevent infinite recursion. Do not set manually.
        """
        # Prevent infinite recursion on repeated failures
        if _retry_count > 1:
            self._print_error(f"Max retries exceeded for log_interaction")
            return {"success": False, "error": "Max retries exceeded after recovery attempt"}

        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if not agent_type or not agent_type.strip():
            raise ValueError("agent_type cannot be empty")
        if not content or not content.strip():
            raise ValueError("content cannot be empty")

        # Note: No agent_type validation against a hardcoded list.
        # Per schema v2 migration, BAZINGA is designed to be extensible.
        # New agent types can be added without code changes.
        # Database enforces NOT NULL, which is sufficient.

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, iteration, agent_type, agent_id, content))
            log_id = cursor.lastrowid
            conn.commit()

            # Verify the insert by reading it back
            verify = conn.execute("""
                SELECT id, session_id, agent_type, LENGTH(content) as content_length, timestamp
                FROM orchestration_logs WHERE id = ?
            """, (log_id,)).fetchone()

            if not verify:
                raise RuntimeError(f"Failed to verify log insertion for log_id={log_id}")

            result = {
                'success': True,
                'log_id': log_id,
                'session_id': verify['session_id'],
                'agent_type': verify['agent_type'],
                'content_length': verify['content_length'],
                'timestamp': verify['timestamp'],
                'iteration': iteration,
                'agent_id': agent_id
            }

            self._print_success(f"✓ Logged {agent_type} interaction (log_id={log_id}, {result['content_length']} chars)")
            return result

        except sqlite3.DatabaseError as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            # Check if it's a corruption error
            if self._is_corruption_error(e):
                if self._recover_from_corruption():
                    # Retry once after recovery (with incremented counter to prevent infinite loop)
                    self._print_error(f"Retrying log operation after recovery...")
                    return self.log_interaction(session_id, agent_type, content, iteration, agent_id,
                                               _retry_count=_retry_count + 1)
            self._print_error(f"Failed to log {agent_type} interaction: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            self._print_error(f"Failed to log {agent_type} interaction: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_logs(self, session_id: str, limit: int = 50, offset: int = 0,
                 agent_type: Optional[str] = None, since: Optional[str] = None) -> List[Dict]:
        """Get orchestration logs with optional filtering."""
        conn = self._get_connection()

        query = "SELECT * FROM orchestration_logs WHERE session_id = ?"
        params = [session_id]

        if agent_type:
            query += " AND agent_type = ?"
            params.append(agent_type)

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def stream_logs(self, session_id: str, limit: int = 50, offset: int = 0) -> str:
        """Stream logs in markdown format (for dashboard)."""
        logs = self.get_logs(session_id, limit, offset)

        if not logs:
            return "No logs found."

        output = []
        for log in reversed(logs):  # Show oldest first
            timestamp = log['timestamp']
            agent_type = log['agent_type'].upper()
            iteration = log['iteration'] if log['iteration'] else '?'
            content = log['content']

            output.append(f"## [{timestamp}] Iteration {iteration} - {agent_type}")
            output.append("")
            output.append(content)
            output.append("")
            output.append("---")
            output.append("")

        return "\n".join(output)

    # ==================== STATE OPERATIONS ====================

    def save_state(self, session_id: str, state_type: str, state_data: Dict) -> None:
        """Save state snapshot."""
        conn = self._get_connection()
        conn.execute("""
            INSERT INTO state_snapshots (session_id, state_type, state_data)
            VALUES (?, ?, ?)
        """, (session_id, state_type, json.dumps(state_data)))
        conn.commit()
        conn.close()
        self._print_success(f"✓ Saved {state_type} state")

    def get_latest_state(self, session_id: str, state_type: str) -> Optional[Dict]:
        """Get latest state snapshot."""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT state_data FROM state_snapshots
            WHERE session_id = ? AND state_type = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, state_type)).fetchone()
        conn.close()
        return json.loads(row['state_data']) if row else None

    # ==================== TASK GROUP OPERATIONS ====================

    def create_task_group(self, group_id: str, session_id: str, name: str,
                         status: str = 'pending', assigned_to: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a task group (upsert - idempotent operation).

        Uses INSERT ... ON CONFLICT to handle duplicates gracefully. If the group
        already exists, only name/status/assigned_to are updated - preserving
        revision_count, last_review_status, and created_at.

        Returns:
            Dict with 'success' bool and 'task_group' data, or 'error' on failure.
        """
        conn = None
        try:
            conn = self._get_connection()
            # Use ON CONFLICT for true upsert - preserves existing metadata
            conn.execute("""
                INSERT INTO task_groups (id, session_id, name, status, assigned_to)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id, session_id) DO UPDATE SET
                    name = excluded.name,
                    status = excluded.status,
                    assigned_to = COALESCE(excluded.assigned_to, assigned_to),
                    updated_at = CURRENT_TIMESTAMP
            """, (group_id, session_id, name, status, assigned_to))
            conn.commit()

            # Fetch and return the saved record
            row = conn.execute("""
                SELECT * FROM task_groups WHERE id = ? AND session_id = ?
            """, (group_id, session_id)).fetchone()

            result = dict(row) if row else None
            self._print_success(f"✓ Task group saved: {group_id} (session: {session_id[:20]}...)")
            return {"success": True, "task_group": result}

        except Exception as e:
            print(f"! Failed to save task group {group_id}: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def update_task_group(self, group_id: str, session_id: str, status: Optional[str] = None,
                         assigned_to: Optional[str] = None, revision_count: Optional[int] = None,
                         last_review_status: Optional[str] = None,
                         auto_create: bool = True, name: Optional[str] = None) -> Dict[str, Any]:
        """Update task group fields (requires session_id for composite key).

        Args:
            group_id: Task group identifier
            session_id: Session identifier
            status: New status value
            assigned_to: Agent assignment
            revision_count: Number of revisions
            last_review_status: APPROVED or CHANGES_REQUESTED
            auto_create: If True and group doesn't exist, create it (default: True)
            name: Name for auto-creation (defaults to group_id if not provided)

        Returns:
            Dict with 'success' bool and 'task_group' data, or 'error' on failure.
        """
        conn = None
        try:
            conn = self._get_connection()
            updates = []
            params = []

            if status:
                updates.append("status = ?")
                params.append(status)
            if assigned_to:
                updates.append("assigned_to = ?")
                params.append(assigned_to)
            if revision_count is not None:
                updates.append("revision_count = ?")
                params.append(revision_count)
            if last_review_status:
                updates.append("last_review_status = ?")
                params.append(last_review_status)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE task_groups SET {', '.join(updates)} WHERE id = ? AND session_id = ?"
                params.extend([group_id, session_id])
                cursor = conn.execute(query, params)
                conn.commit()

                # Check if UPDATE modified any rows
                if cursor.rowcount == 0:
                    if auto_create:
                        # Auto-create the task group if it doesn't exist
                        # Close connection before delegating to create_task_group
                        conn.close()
                        conn = None  # Prevent double-close in finally block
                        group_name = name or f"Task Group {group_id}"
                        self._print_success(f"Task group {group_id} not found, auto-creating...")
                        return self.create_task_group(
                            group_id, session_id, group_name,
                            status=status or 'pending',
                            assigned_to=assigned_to
                        )
                    else:
                        print(f"! Task group not found: {group_id} in session {session_id}", file=sys.stderr)
                        return {"success": False, "error": f"Task group not found: {group_id}"}
                else:
                    self._print_success(f"✓ Task group updated: {group_id} (session: {session_id[:20]}...)")

            # Fetch and return the updated record
            row = conn.execute("""
                SELECT * FROM task_groups WHERE id = ? AND session_id = ?
            """, (group_id, session_id)).fetchone()

            return {"success": True, "task_group": dict(row) if row else None}

        except Exception as e:
            print(f"! Failed to update task group {group_id}: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_task_groups(self, session_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get task groups for a session."""
        conn = self._get_connection()
        if status:
            rows = conn.execute("""
                SELECT * FROM task_groups WHERE session_id = ? AND status = ?
                ORDER BY created_at
            """, (session_id, status)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM task_groups WHERE session_id = ?
                ORDER BY created_at
            """, (session_id,)).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== TOKEN USAGE OPERATIONS ====================

    def log_tokens(self, session_id: str, agent_type: str, tokens: int,
                   agent_id: Optional[str] = None) -> None:
        """Log token usage."""
        conn = self._get_connection()
        conn.execute("""
            INSERT INTO token_usage (session_id, agent_type, agent_id, tokens_estimated)
            VALUES (?, ?, ?, ?)
        """, (session_id, agent_type, agent_id, tokens))
        conn.commit()
        conn.close()

    def get_token_summary(self, session_id: str, by: str = 'agent_type') -> Dict:
        """Get token usage summary grouped by agent_type or agent_id."""
        conn = self._get_connection()
        if by == 'agent_type':
            rows = conn.execute("""
                SELECT agent_type, SUM(tokens_estimated) as total
                FROM token_usage
                WHERE session_id = ?
                GROUP BY agent_type
            """, (session_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT agent_id, SUM(tokens_estimated) as total
                FROM token_usage
                WHERE session_id = ?
                GROUP BY agent_id
            """, (session_id,)).fetchall()
        conn.close()

        result = {row[0]: row[1] for row in rows}
        result['total'] = sum(result.values())
        return result

    # ==================== SKILL OUTPUT OPERATIONS ====================

    def save_skill_output(self, session_id: str, skill_name: str, output_data: Dict) -> None:
        """Save skill output."""
        conn = self._get_connection()
        conn.execute("""
            INSERT INTO skill_outputs (session_id, skill_name, output_data)
            VALUES (?, ?, ?)
        """, (session_id, skill_name, json.dumps(output_data)))
        conn.commit()
        conn.close()
        self._print_success(f"✓ Saved {skill_name} output")

    def get_skill_output(self, session_id: str, skill_name: str) -> Optional[Dict]:
        """Get latest skill output."""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT output_data FROM skill_outputs
            WHERE session_id = ? AND skill_name = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, skill_name)).fetchone()
        conn.close()
        return json.loads(row['output_data']) if row else None

    # ==================== CONFIGURATION OPERATIONS ====================
    # REMOVED: Configuration table no longer exists (2025-11-21)
    # See research/empty-tables-analysis.md for details
    #
    # def set_config(self, key: str, value: Any) -> None:
    #     """Set configuration value."""
    #     ...
    #
    # def get_config(self, key: str) -> Optional[Any]:
    #     """Get configuration value."""
    #     ...

    # ==================== DASHBOARD DATA ====================

    def get_dashboard_snapshot(self, session_id: str) -> Dict:
        """Get complete dashboard data snapshot."""
        return {
            'session': self.get_session(session_id),
            'orchestrator_state': self.get_latest_state(session_id, 'orchestrator'),
            'pm_state': self.get_latest_state(session_id, 'pm'),
            'task_groups': self.get_task_groups(session_id),
            'token_summary': self.get_token_summary(session_id),
            'recent_logs': self.get_logs(session_id, limit=10)
        }

    # ==================== DEVELOPMENT PLAN OPERATIONS ====================

    def save_development_plan(self, session_id: str, original_prompt: str,
                             plan_text: str, phases: List[Dict],
                             current_phase: int, total_phases: int,
                             metadata: Optional[Dict] = None) -> None:
        """Save or update development plan for a session."""
        conn = self._get_connection()
        metadata_json = json.dumps(metadata) if metadata else None
        phases_json = json.dumps(phases)

        conn.execute("""
            INSERT OR REPLACE INTO development_plans
            (session_id, original_prompt, plan_text, phases, current_phase, total_phases, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, original_prompt, plan_text, phases_json, current_phase, total_phases, metadata_json))
        conn.commit()
        conn.close()
        self._print_success(f"✓ Saved development plan for session {session_id}")

    def get_development_plan(self, session_id: str) -> Optional[Dict]:
        """Get development plan for a session."""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT * FROM development_plans WHERE session_id = ?
        """, (session_id,)).fetchone()
        conn.close()

        if not row:
            return None

        plan = dict(row)
        plan['phases'] = json.loads(plan['phases'])
        if plan['metadata']:
            plan['metadata'] = json.loads(plan['metadata'])
        return plan

    def update_plan_progress(self, session_id: str, phase_number: int, status: str) -> None:
        """Update a specific phase status in the development plan."""
        plan = self.get_development_plan(session_id)
        if not plan:
            print(f"Error: No plan found for session {session_id}", file=sys.stderr)
            sys.exit(1)

        phases = plan['phases']
        for phase in phases:
            if phase['phase'] == phase_number:
                phase['status'] = status
                if status == 'completed':
                    phase['completed_at'] = datetime.now().isoformat()
                break

        conn = self._get_connection()
        conn.execute("""
            UPDATE development_plans
            SET phases = ?, current_phase = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
        """, (json.dumps(phases), phase_number, session_id))
        conn.commit()
        conn.close()
        self._print_success(f"✓ Updated phase {phase_number} status to: {status}")

    # ==================== SUCCESS CRITERIA OPERATIONS ====================

    def _validate_criterion_status(self, status: str) -> None:
        """Validate criterion status value."""
        valid_statuses = ['pending', 'met', 'blocked', 'failed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")

    def save_success_criteria(self, session_id: str, criteria: List[Dict]) -> None:
        """Save success criteria for a session (full replacement - removes stale criteria)."""
        # Validate inputs before database operations
        if not criteria:
            raise ValueError("criteria cannot be empty")

        for i, criterion_obj in enumerate(criteria):
            criterion_text = criterion_obj.get('criterion', '').strip()
            if not criterion_text:
                raise ValueError(f"Criterion {i}: 'criterion' text cannot be empty")

            status = criterion_obj.get('status', 'pending')
            self._validate_criterion_status(status)

        conn = self._get_connection()
        try:
            # Use transaction for all-or-nothing save (delete + insert)
            # Step 1: Delete all existing criteria for this session
            conn.execute("""
                DELETE FROM success_criteria WHERE session_id = ?
            """, (session_id,))

            # Step 2: Insert new criteria
            for criterion_obj in criteria:
                criterion_text = criterion_obj.get('criterion', '').strip()
                status = criterion_obj.get('status', 'pending')
                actual = criterion_obj.get('actual')
                evidence = criterion_obj.get('evidence')
                required = criterion_obj.get('required_for_completion', True)

                conn.execute("""
                    INSERT INTO success_criteria
                    (session_id, criterion, status, actual, evidence, required_for_completion, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (session_id, criterion_text, status, actual, evidence, required))

            conn.commit()
            self._print_success(f"✓ Saved {len(criteria)} success criteria for session {session_id}")
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save success criteria: {str(e)}")
        finally:
            conn.close()

    def get_success_criteria(self, session_id: str) -> List[Dict]:
        """Get all success criteria for a session."""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT id, session_id, criterion, status, actual, evidence,
                   required_for_completion, created_at, updated_at
            FROM success_criteria
            WHERE session_id = ?
            ORDER BY id
        """, (session_id,)).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_success_criterion(self, session_id: str, criterion: str,
                                 status: Optional[str] = None,
                                 actual: Optional[str] = None,
                                 evidence: Optional[str] = None) -> None:
        """Update a specific success criterion (status, actual, evidence)."""
        # Validate inputs
        if not criterion or not criterion.strip():
            raise ValueError("criterion text cannot be empty")
        if status is not None:
            self._validate_criterion_status(status)

        conn = self._get_connection()
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
        if actual is not None:
            updates.append("actual = ?")
            params.append(actual)
        if evidence is not None:
            updates.append("evidence = ?")
            params.append(evidence)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE success_criteria SET {', '.join(updates)} WHERE session_id = ? AND criterion = ?"
            params.extend([session_id, criterion])
            cursor = conn.execute(query, params)
            conn.commit()

            if cursor.rowcount == 0:
                print(f"! Criterion not found: '{criterion}' in session {session_id}", file=sys.stderr)
            else:
                self._print_success(f"✓ Updated criterion: {criterion[:50]}...")

        conn.close()

    # ==================== CONTEXT PACKAGE OPERATIONS ====================

    # Canonical agent types (lowercase) for normalization
    VALID_AGENT_TYPES = frozenset({
        'project_manager', 'developer', 'senior_software_engineer',
        'qa_expert', 'tech_lead', 'investigator', 'requirements_engineer', 'orchestrator'
    })

    def save_context_package(self, session_id: str, group_id: str, package_type: str,
                            file_path: str, producer_agent: str, consumers: List[str],
                            priority: str, summary: str, size_bytes: int = None) -> Dict:
        """Save a context package and create consumer entries.

        NOTE: Versioning is not yet implemented. All packages have supersedes_id=NULL.
        Future enhancement: add superseded_by_id column and link previous versions.
        """
        valid_types = ('research', 'failures', 'decisions', 'handoff', 'investigation')
        if package_type not in valid_types:
            raise ValueError(f"Invalid package_type: {package_type}. Must be one of {valid_types}")

        valid_priorities = ('low', 'medium', 'high', 'critical')
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")

        # Normalize and validate producer agent type
        producer_agent = producer_agent.strip().lower()
        if producer_agent not in self.VALID_AGENT_TYPES:
            raise ValueError(f"Invalid producer_agent: {producer_agent}. Must be one of {sorted(self.VALID_AGENT_TYPES)}")

        # Normalize and validate consumer agent types
        normalized_consumers = []
        for c in consumers:
            if not c or not c.strip():
                continue  # Skip empty strings
            c_normalized = c.strip().lower()
            if c_normalized not in self.VALID_AGENT_TYPES:
                raise ValueError(f"Invalid consumer agent: {c}. Must be one of {sorted(self.VALID_AGENT_TYPES)}")
            normalized_consumers.append(c_normalized)
        if not normalized_consumers:
            raise ValueError("At least one valid consumer agent is required")
        consumers = normalized_consumers

        # Validate file path to prevent path traversal and symlink escapes
        from pathlib import Path
        import os

        # Convert to Path and resolve (follows symlinks)
        try:
            candidate_path = Path(file_path).resolve()
        except (ValueError, RuntimeError) as e:
            raise ValueError(f"Invalid file_path: {e}")

        # Define artifacts root and resolve it
        artifacts_root = Path("bazinga/artifacts") / session_id
        artifacts_root_resolved = artifacts_root.resolve()

        # Ensure candidate is within artifacts directory using relative_to
        try:
            rel_path = candidate_path.relative_to(artifacts_root_resolved)
        except ValueError:
            raise ValueError(f"Invalid file_path: must be within {artifacts_root}. Got: {file_path}")

        # Store as repo-relative path (not absolute) for portability
        # Use forward slashes for cross-platform consistency
        normalized_path = f"bazinga/artifacts/{session_id}/{str(rel_path).replace(os.sep, '/')}"

        # Auto-compute size_bytes if not provided and file exists
        if size_bytes is None:
            try:
                size_bytes = os.stat(str(candidate_path)).st_size
            except (OSError, FileNotFoundError):
                # File doesn't exist yet or not accessible - leave as None
                pass

        # Enforce summary length constraint (max 200 chars) and sanitize
        summary = summary.replace('\n', ' ').replace('\r', ' ')  # Single-line
        if len(summary) > 200:
            summary = summary[:197] + "..."

        # Deduplicate consumers to prevent UNIQUE constraint violations
        consumers = list(dict.fromkeys(consumers))  # Preserves order, removes duplicates

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Determine scope
            scope = 'global' if group_id == 'global' or group_id is None else 'group'
            actual_group_id = None if group_id == 'global' else group_id

            # Insert the context package
            cursor.execute("""
                INSERT INTO context_packages
                (session_id, group_id, package_type, file_path, producer_agent, priority, summary, size_bytes, scope)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, actual_group_id, package_type, normalized_path, producer_agent, priority, summary, size_bytes, scope))

            package_id = cursor.lastrowid

            # Create consumer entries
            for consumer in consumers:
                cursor.execute("""
                    INSERT INTO context_package_consumers (package_id, agent_type)
                    VALUES (?, ?)
                """, (package_id, consumer))

            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise RuntimeError(f"Failed to save context package: {e}")

        conn.close()

        self._print_success(f"✓ Created context package {package_id} ({package_type}) with {len(consumers)} consumers")
        return {"package_id": package_id, "file_path": normalized_path, "consumers_created": len(consumers)}

    def get_context_packages(self, session_id: str, group_id: str, agent_type: str,
                            limit: int = 3, include_consumed: bool = False) -> List[Dict]:
        """Get context packages for an agent spawn, ordered by priority.

        Args:
            session_id: Session ID to query
            group_id: Group ID to query
            agent_type: Agent type to query packages for (normalized to lowercase)
            limit: Maximum number of packages to return (default 3)
            include_consumed: If False (default), only return unconsumed packages
        """
        # Normalize agent_type for consistent matching
        agent_type = agent_type.strip().lower()

        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query with optional consumption filter
        consumption_filter = "" if include_consumed else "AND cpc.consumed_at IS NULL"

        # Query packages for this agent type, including global packages
        cursor.execute(f"""
            SELECT cp.id, cp.package_type, cp.priority, cp.summary, cp.file_path, cp.size_bytes, cp.group_id
            FROM context_packages cp
            JOIN context_package_consumers cpc ON cp.id = cpc.package_id
            WHERE cp.session_id = ?
              AND (cp.group_id = ? OR cp.scope = 'global')
              AND cpc.agent_type = ?
              AND cp.supersedes_id IS NULL
              {consumption_filter}
            ORDER BY
              CASE cp.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
              END,
              cp.created_at DESC
            LIMIT ?
        """, (session_id, group_id, agent_type, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def mark_context_consumed(self, package_id: int, agent_type: str, iteration: int = 1) -> bool:
        """Mark a context package as consumed by an agent.

        Only marks consumption if the agent_type was designated as a consumer
        when the package was created. Does NOT create consumer rows implicitly.

        Args:
            package_id: ID of the package to mark consumed
            agent_type: Agent type marking consumption (normalized to lowercase)
            iteration: Iteration number (default 1)

        Returns:
            True if marked successfully, False if agent was not a designated consumer
        """
        # Normalize agent_type
        agent_type = agent_type.strip().lower()

        conn = self._get_connection()
        cursor = conn.cursor()

        # Try to update any pending (unconsumed) row for this package and agent
        # SQLite doesn't support LIMIT in UPDATE, use subquery instead
        cursor.execute("""
            UPDATE context_package_consumers
            SET consumed_at = CURRENT_TIMESTAMP, iteration = ?
            WHERE id IN (
                SELECT id FROM context_package_consumers
                WHERE package_id = ? AND agent_type = ? AND consumed_at IS NULL
                LIMIT 1
            )
        """, (iteration, package_id, agent_type))

        if cursor.rowcount == 0:
            # Check if this agent was ever designated as a consumer (consumed or not)
            cursor.execute("""
                SELECT 1 FROM context_package_consumers
                WHERE package_id = ? AND agent_type = ?
                LIMIT 1
            """, (package_id, agent_type))
            if cursor.fetchone() is None:
                # Agent was never designated as consumer - don't create implicit entry
                conn.close()
                print(f"! Agent '{agent_type}' was not designated as consumer for package {package_id}", file=sys.stderr)
                return False
            # Consumer exists but already consumed - that's fine

        conn.commit()
        conn.close()
        self._print_success(f"✓ Marked package {package_id} as consumed by {agent_type} (iteration {iteration})")
        return True

    def update_context_references(self, group_id: str, session_id: str, package_ids: List[int]) -> None:
        """Update the context_references for a task group."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE task_groups
            SET context_references = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND session_id = ?
        """, (json.dumps(package_ids), group_id, session_id))

        if cursor.rowcount == 0:
            conn.close()
            print(f"! Warning: No task group found with id='{group_id}' and session_id='{session_id}'", file=sys.stderr)
            return

        conn.commit()
        conn.close()
        self._print_success(f"✓ Updated context references for {group_id}: {package_ids}")

    # ==================== QUERY OPERATIONS ====================

    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute custom SQL query (read-only)."""
        if not sql.strip().upper().startswith('SELECT'):
            print("Error: Only SELECT queries allowed", file=sys.stderr)
            sys.exit(1)

        conn = self._get_connection()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(row) for row in rows]


def print_help():
    """Print help text with all available commands."""
    help_text = """
BAZINGA Database Client - Available Commands:

SESSION OPERATIONS:
  create-session <id> <mode> <requirements>   Create new session (mode: simple|parallel)
  list-sessions [limit]                       List recent sessions (default: 10)
  update-session-status <id> <status>         Update session status

LOG OPERATIONS:
  log-interaction <session> <agent> <content> [iteration] [agent_id]
                                              Log agent interaction
  stream-logs <session> [limit] [offset]      Stream logs in markdown (default: limit=50, offset=0)

STATE OPERATIONS:
  save-state <session> <type> <json_data>     Save state snapshot
  get-state <session> <type>                  Get latest state snapshot

TASK GROUP OPERATIONS:
  create-task-group <group_id> <session> <name> [status] [assigned_to]
                                              Create task group (default: status=pending)
  update-task-group <group_id> <session> [--status X] [--assigned_to Y]
                                              Update task group
  get-task-groups <session> [status]          Get task groups

TOKEN OPERATIONS:
  log-tokens <session> <agent> <tokens> [agent_id]
                                              Log token usage
  token-summary <session> [by]                Get token summary (default: by=agent_type)

SKILL OUTPUT OPERATIONS:
  save-skill-output <session> <skill> <json>  Save skill output
  get-skill-output <session> <skill>          Get skill output

DEVELOPMENT PLAN OPERATIONS:
  save-development-plan <session> <prompt> <plan> <phases_json> <current> <total> [metadata]
                                              Save development plan
  get-development-plan <session>              Get development plan
  update-plan-progress <session> <phase> <status>
                                              Update plan phase status

SUCCESS CRITERIA OPERATIONS:
  save-success-criteria <session> <criteria_json>
                                              Save success criteria
  get-success-criteria <session>              Get success criteria
  update-success-criterion <session> <criterion> [--status X] [--actual Y] [--evidence Z]
                                              Update criterion

CONTEXT PACKAGE OPERATIONS:
  save-context-package <session> <group_id> <type> <file_path> <producer> <consumers_json> <priority> <summary>
                                              Save context package (type: research|failures|decisions|handoff|investigation)
  get-context-packages <session> <group_id> <agent_type> [limit]
                                              Get context packages for agent spawn (default: limit=3)
  mark-context-consumed <package_id> <agent_type> [iteration]
                                              Mark package as consumed (default: iteration=1)
  update-context-references <group_id> <session> <package_ids_json>
                                              Update task group context references

QUERY OPERATIONS:
  query <sql>                                 Execute custom SELECT query
  dashboard-snapshot <session>                Get complete dashboard data

DATABASE MAINTENANCE:
  integrity-check                             Check database integrity
  recover-db                                  Attempt to recover corrupted database

HELP:
  help                                        Show this help message

Examples:
  bazinga_db.py --db bazinga.db list-sessions 5
  bazinga_db.py --db bazinga.db query "SELECT * FROM sessions LIMIT 3"
  bazinga_db.py --db bazinga.db get-task-groups session123
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        description='BAZINGA Database Client',
        epilog='Run with "help" command to see all available commands'
    )
    parser.add_argument('--db', required=True, help='Database path')
    parser.add_argument('--quiet', action='store_true', help='Suppress success messages, only show errors')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')

    args = parser.parse_args()
    db = BazingaDB(args.db, quiet=args.quiet)

    # Parse command and execute
    cmd = args.command
    cmd_args = args.args

    try:
        if cmd == 'create-session':
            result = db.create_session(cmd_args[0], cmd_args[1], cmd_args[2])
            # Output verification data as JSON
            print(json.dumps(result, indent=2))
        elif cmd == 'list-sessions':
            limit = int(cmd_args[0]) if len(cmd_args) > 0 else 10
            sessions = db.list_sessions(limit)
            print(json.dumps(sessions, indent=2))
        elif cmd == 'log-interaction':
            result = db.log_interaction(cmd_args[0], cmd_args[1], cmd_args[2],
                             int(cmd_args[3]) if len(cmd_args) > 3 else None,
                             cmd_args[4] if len(cmd_args) > 4 else None)
            # Output verification data as JSON
            print(json.dumps(result, indent=2))
        elif cmd == 'save-state':
            state_data = json.loads(cmd_args[2])
            db.save_state(cmd_args[0], cmd_args[1], state_data)
        elif cmd == 'get-state':
            result = db.get_latest_state(cmd_args[0], cmd_args[1])
            print(json.dumps(result, indent=2))
        elif cmd == 'stream-logs':
            limit = int(cmd_args[1]) if len(cmd_args) > 1 else 50
            offset = int(cmd_args[2]) if len(cmd_args) > 2 else 0
            print(db.stream_logs(cmd_args[0], limit, offset))
        elif cmd == 'dashboard-snapshot':
            result = db.get_dashboard_snapshot(cmd_args[0])
            print(json.dumps(result, indent=2))
        elif cmd == 'log-tokens':
            session_id = cmd_args[0]
            agent_type = cmd_args[1]
            tokens = int(cmd_args[2])
            agent_id = cmd_args[3] if len(cmd_args) > 3 else None
            db.log_tokens(session_id, agent_type, tokens, agent_id)
            db._print_success(f"✓ Logged {tokens} tokens for {agent_type}")
        elif cmd == 'token-summary':
            by = cmd_args[1] if len(cmd_args) > 1 else 'agent_type'
            result = db.get_token_summary(cmd_args[0], by)
            print(json.dumps(result, indent=2))
        elif cmd == 'save-skill-output':
            session_id = cmd_args[0]
            skill_name = cmd_args[1]
            output_data = json.loads(cmd_args[2])
            db.save_skill_output(session_id, skill_name, output_data)
        elif cmd == 'get-skill-output':
            session_id = cmd_args[0]
            skill_name = cmd_args[1]
            result = db.get_skill_output(session_id, skill_name)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-task-groups':
            session_id = cmd_args[0]
            status = cmd_args[1] if len(cmd_args) > 1 else None
            result = db.get_task_groups(session_id, status)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-session-status':
            session_id = cmd_args[0]
            status = cmd_args[1]
            db.update_session_status(session_id, status)
        elif cmd == 'create-task-group':
            group_id = cmd_args[0]
            session_id = cmd_args[1]
            name = cmd_args[2]
            status = cmd_args[3] if len(cmd_args) > 3 else 'pending'
            assigned_to = cmd_args[4] if len(cmd_args) > 4 else None
            result = db.create_task_group(group_id, session_id, name, status, assigned_to)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-task-group':
            group_id = cmd_args[0]
            session_id = cmd_args[1]
            kwargs = {}
            for i in range(2, len(cmd_args), 2):
                key = cmd_args[i].lstrip('--')
                value = cmd_args[i + 1]
                # Convert revision_count to int if present
                if key == 'revision_count':
                    value = int(value)
                # Convert auto_create to bool
                elif key == 'auto_create':
                    value = value.lower() in ('true', '1', 'yes')
                kwargs[key] = value
            result = db.update_task_group(group_id, session_id, **kwargs)
            print(json.dumps(result, indent=2))
        elif cmd == 'save-development-plan':
            session_id = cmd_args[0]
            original_prompt = cmd_args[1]
            plan_text = cmd_args[2]
            phases = json.loads(cmd_args[3])
            current_phase = int(cmd_args[4])
            total_phases = int(cmd_args[5])
            metadata = json.loads(cmd_args[6]) if len(cmd_args) > 6 else None
            db.save_development_plan(session_id, original_prompt, plan_text, phases, current_phase, total_phases, metadata)
        elif cmd == 'get-development-plan':
            session_id = cmd_args[0]
            result = db.get_development_plan(session_id)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-plan-progress':
            session_id = cmd_args[0]
            phase_number = int(cmd_args[1])
            status = cmd_args[2]
            db.update_plan_progress(session_id, phase_number, status)
        elif cmd == 'save-success-criteria':
            session_id = cmd_args[0]
            criteria = json.loads(cmd_args[1])
            db.save_success_criteria(session_id, criteria)
        elif cmd == 'get-success-criteria':
            session_id = cmd_args[0]
            result = db.get_success_criteria(session_id)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-success-criterion':
            session_id = cmd_args[0]
            criterion = cmd_args[1]
            kwargs = {}
            for i in range(2, len(cmd_args), 2):
                key = cmd_args[i].lstrip('--')
                value = cmd_args[i + 1]
                kwargs[key] = value
            db.update_success_criterion(session_id, criterion, **kwargs)
        elif cmd == 'save-context-package':
            session_id = cmd_args[0]
            group_id = cmd_args[1]
            package_type = cmd_args[2]
            file_path = cmd_args[3]
            producer = cmd_args[4]
            try:
                consumers = json.loads(cmd_args[5])
                if not isinstance(consumers, list):
                    raise ValueError("consumers_json must be a JSON array of strings")
                if not all(x and isinstance(x, str) for x in consumers):
                    raise ValueError("All consumer elements must be non-empty strings")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"ERROR: Invalid consumers_json argument: {e}", file=sys.stderr)
                print("Expected: JSON array of agent types, e.g., [\"developer\", \"qa_expert\"]", file=sys.stderr)
                sys.exit(1)
            priority = cmd_args[6]
            summary = cmd_args[7]
            result = db.save_context_package(session_id, group_id, package_type, file_path, producer, consumers, priority, summary)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-context-packages':
            session_id = cmd_args[0]
            group_id = cmd_args[1]
            agent_type = cmd_args[2]
            limit = int(cmd_args[3]) if len(cmd_args) > 3 else 3
            # Validate limit is within acceptable range
            if limit < 1 or limit > 50:
                print(f"ERROR: limit must be between 1 and 50 (got {limit})", file=sys.stderr)
                sys.exit(1)
            result = db.get_context_packages(session_id, group_id, agent_type, limit)
            print(json.dumps(result, indent=2))
        elif cmd == 'mark-context-consumed':
            package_id = int(cmd_args[0])
            agent_type = cmd_args[1]
            iteration = int(cmd_args[2]) if len(cmd_args) > 2 else 1
            db.mark_context_consumed(package_id, agent_type, iteration)
        elif cmd == 'update-context-references':
            group_id = cmd_args[0]
            session_id = cmd_args[1]
            try:
                package_ids = json.loads(cmd_args[2])
                if not isinstance(package_ids, list) or not all(isinstance(x, int) for x in package_ids):
                    raise ValueError("package_ids must be a JSON array of integers")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"ERROR: Invalid package_ids argument: {e}", file=sys.stderr)
                print("Expected: JSON array of integers, e.g., [1, 3, 5]", file=sys.stderr)
                sys.exit(1)
            db.update_context_references(group_id, session_id, package_ids)
        elif cmd == 'query':
            if not cmd_args:
                print("Error: query command requires SQL statement", file=sys.stderr)
                sys.exit(1)
            # Join args to allow unquoted SQL: query SELECT * FROM table
            sql = " ".join(cmd_args)
            result = db.query(sql)
            print(json.dumps(result, indent=2))
        elif cmd == 'integrity-check':
            result = db.check_integrity()
            print(json.dumps(result, indent=2))
            if not result['ok']:
                sys.exit(1)
        elif cmd == 'recover-db':
            if db._recover_from_corruption():
                print(json.dumps({"success": True, "message": "Database recovered successfully"}, indent=2))
            else:
                print(json.dumps({"success": False, "error": "Recovery failed"}, indent=2))
                sys.exit(1)
        elif cmd == 'help':
            print_help()
            sys.exit(0)
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print("\nRun with 'help' command to see available commands.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
