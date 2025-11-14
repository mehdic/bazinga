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

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure database exists, create if not."""
        if not Path(self.db_path).exists():
            print(f"Database not found at {self.db_path}. Auto-initializing...", file=sys.stderr)
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

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

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

            print(f"✓ Session created: {session_id}")
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
                    print(f"✓ Session already exists: {session_id}")
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
        print(f"✓ Session {session_id} status updated to: {status}")

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
                       iteration: Optional[int] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Log an agent interaction with validation."""
        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if not agent_type or not agent_type.strip():
            raise ValueError("agent_type cannot be empty")
        if not content or not content.strip():
            raise ValueError("content cannot be empty")
        if agent_type not in ['pm', 'developer', 'qa_expert', 'techlead', 'orchestrator']:
            raise ValueError(f"Invalid agent_type: {agent_type}")

        conn = self._get_connection()
        try:
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

            print(f"✓ Logged {agent_type} interaction (log_id={log_id}, {result['content_length']} chars)")
            return result

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to log {agent_type} interaction: {str(e)}")
        finally:
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
        print(f"✓ Saved {state_type} state")

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
                         status: str = 'pending', assigned_to: Optional[str] = None) -> None:
        """Create a new task group."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO task_groups (id, session_id, name, status, assigned_to)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, session_id, name, status, assigned_to))
            conn.commit()
            print(f"✓ Task group created: {group_id}")
        except sqlite3.IntegrityError:
            print(f"! Task group already exists: {group_id}", file=sys.stderr)
        finally:
            conn.close()

    def update_task_group(self, group_id: str, status: Optional[str] = None,
                         assigned_to: Optional[str] = None, revision_count: Optional[int] = None,
                         last_review_status: Optional[str] = None) -> None:
        """Update task group fields."""
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
            query = f"UPDATE task_groups SET {', '.join(updates)} WHERE id = ?"
            params.append(group_id)
            conn.execute(query, params)
            conn.commit()
            print(f"✓ Task group updated: {group_id}")

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
        print(f"✓ Saved {skill_name} output")

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

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        conn = self._get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO configuration (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, json.dumps(value)))
        conn.commit()
        conn.close()
        print(f"✓ Config set: {key}")

    def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value."""
        conn = self._get_connection()
        row = conn.execute("""
            SELECT value FROM configuration WHERE key = ?
        """, (key,)).fetchone()
        conn.close()
        return json.loads(row['value']) if row else None

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


def main():
    parser = argparse.ArgumentParser(description='BAZINGA Database Client')
    parser.add_argument('--db', required=True, help='Database path')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')

    args = parser.parse_args()
    db = BazingaDB(args.db)

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
            print(f"✓ Logged {tokens} tokens for {agent_type}")
        elif cmd == 'token-summary':
            by = cmd_args[1] if len(cmd_args) > 1 else 'agent_type'
            result = db.get_token_summary(cmd_args[0], by)
            print(json.dumps(result, indent=2))
        elif cmd == 'save-skill-output':
            session_id = cmd_args[0]
            skill_name = cmd_args[1]
            output_data = json.loads(cmd_args[2])
            db.save_skill_output(session_id, skill_name, output_data)
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
            db.create_task_group(group_id, session_id, name, status, assigned_to)
        elif cmd == 'update-task-group':
            group_id = cmd_args[0]
            kwargs = {}
            for i in range(1, len(cmd_args), 2):
                key = cmd_args[i].lstrip('--')
                value = cmd_args[i + 1]
                # Convert revision_count to int if present
                if key == 'revision_count':
                    value = int(value)
                kwargs[key] = value
            db.update_task_group(group_id, **kwargs)
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
