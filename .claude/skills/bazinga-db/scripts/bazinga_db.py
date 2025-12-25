#!/usr/bin/env python3
"""
BAZINGA Database Client - Simple command interface for database operations.
Provides high-level commands for agents without requiring SQL knowledge.

Path Resolution:
    The script auto-detects the project root and database path. You can override:
    - --db PATH          Explicit database path
    - --project-root DIR Explicit project root (db at DIR/bazinga/bazinga.db)
    - BAZINGA_ROOT env   Environment variable override

    If none provided, auto-detects by walking up from script location or CWD.
"""

import sqlite3
import json
import sys
import time
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import argparse

# Secret patterns for redaction (compiled for performance)
# See: research/agent-reasoning-capture-ultrathink.md
# Context-preserving: patterns with capture groups use \1= to keep variable names
# Word boundaries (\b) prevent false positives from partial matches in URLs/identifiers
SECRET_PATTERNS = [
    # Generic patterns (preserve variable name context)
    (re.compile(r'(?i)\b(api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?'), r'\1=REDACTED'),
    (re.compile(r'(?i)\b(secret|password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']+["\']?'), r'\1=REDACTED'),
    (re.compile(r'(?i)\b(token)\s*[=:]\s*["\']?[a-zA-Z0-9_.-]{20,}["\']?'), r'\1=REDACTED'),
    # Anthropic - MUST be before generic OpenAI pattern (more specific prefix)
    (re.compile(r'\bsk-ant-[a-zA-Z0-9-]{20,}\b'), 'ANTHROPIC_KEY_REDACTED'),
    # OpenAI (including sk-proj-* format with hyphens) - word boundary prevents flask-sk-... matches
    (re.compile(r'\bsk-[a-zA-Z0-9-]{20,}\b'), 'OPENAI_KEY_REDACTED'),
    # GitHub
    (re.compile(r'\bghp_[a-zA-Z0-9]{36}\b'), 'GITHUB_TOKEN_REDACTED'),
    (re.compile(r'\bgho_[a-zA-Z0-9]{36}\b'), 'GITHUB_OAUTH_REDACTED'),
    (re.compile(r'\bgithub_pat_[a-zA-Z0-9_]{22,}\b'), 'GITHUB_PAT_REDACTED'),
    # AWS (preserve variable name context)
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'AWS_ACCESS_KEY_REDACTED'),
    (re.compile(r'(?i)\b(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\']?[a-zA-Z0-9/+=]{40}["\']?'), r'\1=REDACTED'),
    # Private keys (match entire block from BEGIN to END)
    (re.compile(r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----[\s\S]*?-----END (RSA |EC |DSA )?PRIVATE KEY-----'), 'PRIVATE_KEY_REDACTED'),
    (re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----'), 'SSH_KEY_REDACTED'),
    # Slack
    (re.compile(r'\bxox[baprs]-[a-zA-Z0-9-]{10,}\b'), 'SLACK_TOKEN_REDACTED'),
    # Stripe
    (re.compile(r'\bpk_(test|live)_[a-zA-Z0-9]{10,}\b'), 'STRIPE_PK_REDACTED'),
    (re.compile(r'\bsk_(test|live)_[a-zA-Z0-9]{10,}\b'), 'STRIPE_SK_REDACTED'),
    # Authorization headers (preserve header name)
    (re.compile(r'(?i)\b(authorization):\s*bearer\s+[a-zA-Z0-9._-]{10,}'), r'\1: Bearer REDACTED'),
]


def scan_and_redact(text: str) -> Tuple[str, bool]:
    """Scan text for secrets and redact them.

    Args:
        text: The text to scan and potentially redact

    Returns:
        Tuple of (redacted_text, was_redacted)
    """
    redacted = False
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        # Use subn for single-pass operation (returns replacement count)
        result, num_subs = pattern.subn(replacement, result)
        if num_subs > 0:
            redacted = True
    return result, redacted


def validate_complexity(complexity: Any) -> Optional[str]:
    """Validate complexity value. Returns error message if invalid, None if valid.

    Args:
        complexity: Value to validate (should be int 1-10)

    Returns:
        Error message string if invalid, None if valid
    """
    if complexity is None:
        return None  # None is valid (optional field)
    if not isinstance(complexity, int):
        return f"complexity must be an integer, got {type(complexity).__name__}"
    if not 1 <= complexity <= 10:
        return f"complexity must be between 1 and 10, got {complexity}"
    return None


# Cross-platform file locking
# fcntl is Unix/Linux/macOS only; msvcrt is Windows only
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Windows file locking via msvcrt
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# Deferred warning flag - only warn once when lock is actually needed
_LOCK_WARNING_SHOWN = False

# Add _shared directory to path for bazinga_paths import
# Path: .claude/skills/bazinga-db/scripts/bazinga_db.py
#   -> .claude/skills/bazinga-db/scripts/  (parent)
#   -> .claude/skills/bazinga-db/          (parent.parent)
#   -> .claude/skills/                      (parent.parent.parent)
#   -> .claude/skills/_shared/              (where bazinga_paths.py lives)
_script_dir = Path(__file__).parent.resolve()
_shared_dir = _script_dir.parent.parent / '_shared'
if _shared_dir.exists() and str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

try:
    from bazinga_paths import get_project_root, get_db_path, get_detection_info
    _HAS_BAZINGA_PATHS = True
except ImportError:
    _HAS_BAZINGA_PATHS = False


def _ensure_cwd_at_project_root():
    """Change to project root so all relative paths work correctly.

    This is critical when the script is invoked from a different CWD.
    See: research/absolute-path-resolution-ultrathink.md

    Must be called at entry point (main), NOT at module import time,
    to avoid side effects when this module is imported by tests.
    """
    if not _HAS_BAZINGA_PATHS:
        return  # Cannot detect project root without bazinga_paths

    try:
        project_root = get_project_root()
        import os
        os.chdir(project_root)
        # Only log if BAZINGA_VERBOSE is set to reduce noise
        if os.environ.get("BAZINGA_VERBOSE"):
            print(f"[INFO] project_root={project_root}", file=sys.stderr)
    except RuntimeError:
        # Project root detection failed - no valid markers found
        # Don't chdir to avoid changing to wrong directory
        pass
    except OSError as e:
        print(f"[WARNING] Failed to chdir to project root: {e}", file=sys.stderr)

# Import SCHEMA_VERSION from init_db.py to avoid duplication
try:
    from init_db import SCHEMA_VERSION as EXPECTED_SCHEMA_VERSION
except ImportError:
    # Fallback if init_db.py is not accessible
    print("Warning: Could not import SCHEMA_VERSION from init_db.py, using fallback value 7. "
          "Check if init_db.py exists in the same directory.", file=sys.stderr)
    EXPECTED_SCHEMA_VERSION = 7


class DatabaseInitError(Exception):
    """Exception raised when database initialization fails.

    This allows callers to handle initialization failures gracefully
    rather than having the process terminated by sys.exit().
    """
    pass


class MigrationLockError(Exception):
    """Exception raised when migration lock cannot be acquired after retries."""
    pass


class BazingaDB:
    """Database client for BAZINGA orchestration."""

    # SQLite errors that indicate ACTUAL database corruption (file is unrecoverable)
    # NOTE: Only true corruption errors that indicate the database file itself is damaged.
    # Transient/operational errors (locked, full disk, readonly) should NOT trigger recovery!
    CORRUPTION_ERRORS = [
        "database disk image is malformed",
        "malformed database schema",  # Orphan indexes from interrupted table recreations, inconsistent schema catalog
        "file is not a database",
        # "database or disk is full" - operational, not corruption
        # "attempt to write a readonly database" - permission issue, not corruption
    ]

    # Tables to salvage during recovery (ordered for FK dependencies)
    # Includes all tables from schema.md - code handles missing tables gracefully
    SALVAGE_TABLE_ORDER = [
        'sessions', 'orchestration_logs', 'state_snapshots', 'task_groups',
        'token_usage', 'skill_outputs', 'development_plans', 'success_criteria',
        'context_packages', 'context_package_consumers',
        'configuration', 'decisions', 'model_config'  # May not exist in all DBs
    ]

    # SQLite errors that indicate BAD QUERIES, NOT corruption
    # These happen when agents write inline SQL with wrong column/table names
    # They should NEVER trigger database recovery/deletion
    QUERY_ERRORS = [
        "no such column",
        "no such table",
        "syntax error",
        "near \"",           # Syntax errors like 'near "SELECT"'
        "unrecognized token",
        "no such function",
        "ambiguous column name",
        "constraint failed",  # Constraint violations are not corruption
        "unique constraint",
        "foreign key constraint",
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

    def _is_query_error(self, error: Exception) -> bool:
        """Check if an exception indicates a bad query (NOT corruption).

        These are errors caused by wrong column/table names, syntax errors, etc.
        They should NEVER trigger database recovery/deletion.
        """
        error_msg = str(error).lower()
        return any(query_err in error_msg for query_err in self.QUERY_ERRORS)

    def _is_corruption_error(self, error: Exception) -> bool:
        """Check if an exception indicates database corruption.

        IMPORTANT: Query errors (wrong column names, etc.) are NOT corruption.
        This prevents data loss when agents write bad SQL.
        """
        error_msg = str(error).lower()

        # First, check if this is a query error - these are NEVER corruption
        if self._is_query_error(error):
            return False

        return any(corruption in error_msg for corruption in self.CORRUPTION_ERRORS)

    def _normalize_specialization_path(self, spec_path: str, project_root: Optional[Path] = None, verify_exists: bool = False) -> Tuple[bool, str]:
        """Normalize and validate specialization path.

        Accepts either:
        - Short path: "01-languages/python.md" -> auto-prefixed
        - Medium path: "specializations/01-languages/python.md" -> normalized
        - Full path: "bazinga/templates/specializations/01-languages/python.md"

        Args:
            spec_path: Path to specialization file (short, medium, or full)
            project_root: Project root directory (auto-detected if not provided)
            verify_exists: If True, verify the file actually exists (optional)

        Returns:
            Tuple of (is_valid, normalized_path_or_error_message)
        """
        try:
            import re

            # Validate path contains only safe characters first
            if not re.match(r'^[a-zA-Z0-9/_.-]+$', spec_path):
                return False, f"Path contains unsafe characters: {spec_path}"

            # Block path traversal attempts
            if '..' in spec_path:
                return False, f"Path traversal not allowed: {spec_path}"

            # Auto-detect project root if not provided
            if project_root is None:
                if _HAS_BAZINGA_PATHS:
                    project_root = get_project_root()
                else:
                    project_root = Path(self.db_path).parent.parent

            # Define the specializations base (canonical path for installed mode)
            spec_base = "bazinga/templates/specializations/"

            # Normalize: auto-prefix if not already a full path
            if spec_path.startswith(spec_base):
                # Already canonical full path
                normalized_path = spec_path
            elif spec_path.startswith("templates/specializations/"):
                # Dev mode path: templates/specializations/... -> normalize to bazinga/templates/...
                normalized_path = "bazinga/" + spec_path
            elif spec_path.startswith("specializations/"):
                # Handle "specializations/01-languages/..." -> strip "specializations/" and prefix
                normalized_path = spec_base + spec_path[len("specializations/"):]
            else:
                # Short path like "01-languages/python.md" -> auto-prefix
                normalized_path = spec_base + spec_path.lstrip('/')

            # Verify the normalized path is within allowed directory
            allowed_base = (project_root / "bazinga" / "templates" / "specializations").resolve()
            full_path = (project_root / normalized_path).resolve()

            try:
                full_path.relative_to(allowed_base)
            except ValueError:
                return False, f"Path escapes allowed directory: {spec_path}"

            # Optional file existence check
            if verify_exists and not full_path.exists():
                return False, f"File not found: {normalized_path}"

            return True, normalized_path

        except Exception as e:
            return False, f"Path validation error: {e}"

    def _backup_corrupted_db(self) -> Optional[str]:
        """Backup a corrupted database file before recovery.

        Also backs up WAL and SHM sidecar files if present for complete recovery.
        """
        db_path = Path(self.db_path)
        if not db_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.with_suffix(f".corrupted_{timestamp}.db")
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self._print_error(f"Corrupted database backed up to: {backup_path}")

            # Also backup WAL and SHM files if they exist (for complete recovery)
            for ext in ['-wal', '-shm']:
                sidecar = Path(str(db_path) + ext)
                if sidecar.exists():
                    sidecar_backup = Path(str(backup_path) + ext)
                    try:
                        shutil.copy2(sidecar, sidecar_backup)
                        self._print_error(f"  Also backed up {sidecar.name}")
                    except Exception:
                        pass  # Non-fatal - main backup succeeded

            return str(backup_path)
        except Exception as e:
            self._print_error(f"Failed to backup corrupted database: {e}")
            return None

    def _extract_salvageable_data(self) -> Dict[str, Dict[str, Any]]:
        """Try to extract data from a corrupted database before recovery.

        Returns:
            Dict mapping table names to {'columns': List[str], 'rows': List[tuple]}.
            Empty dict if extraction fails.
        """
        salvaged: Dict[str, Dict[str, Any]] = {}

        try:
            # Use a short timeout - if DB is badly corrupted, don't hang
            # Open in read-only mode to prevent accidental writes to corrupted DB
            uri = f"file:{self.db_path}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=5.0) as conn:
                cursor = conn.cursor()

                for table in self.SALVAGE_TABLE_ORDER:
                    try:
                        cursor.execute(f"SELECT * FROM \"{table}\"")
                        rows = cursor.fetchall()
                        if rows:
                            # Get column names for this table
                            cursor.execute(f"PRAGMA table_info(\"{table}\")")
                            columns = [col[1] for col in cursor.fetchall()]
                            salvaged[table] = {'columns': columns, 'rows': rows}
                            self._print_error(f"  Salvaged {len(rows)} rows from {table}")
                    except sqlite3.Error:
                        # Table doesn't exist or is unreadable - skip
                        pass
        except Exception as e:
            self._print_error(f"  Could not extract data: {e}")
            return {}

        return salvaged

    def _restore_salvaged_data(self, salvaged: Dict[str, Dict[str, Any]]) -> int:
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
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.cursor()
                # Disable FK constraints during restore to avoid ordering issues
                # Table ordering handles most cases, but this is a safety layer
                cursor.execute("PRAGMA foreign_keys = OFF")

                for table in self.SALVAGE_TABLE_ORDER:
                    if table not in salvaged:
                        continue

                    data = salvaged[table]
                    old_columns = data['columns']
                    rows = data['rows']

                    if not rows:
                        continue

                    # Get current schema columns to handle schema changes
                    cursor.execute(f"PRAGMA table_info(\"{table}\")")
                    new_columns = [col[1] for col in cursor.fetchall()]

                    # Intersect: only restore columns that exist in both old and new schema
                    valid_columns = [c for c in old_columns if c in new_columns]
                    if not valid_columns:
                        self._print_error(f"  Skipping {table}: no matching columns")
                        continue

                    # Get indices of valid columns in original row data
                    col_indices = [old_columns.index(c) for c in valid_columns]

                    # Build INSERT statement once (with quoted identifiers)
                    cols_str = ', '.join(f'"{c}"' for c in valid_columns)
                    placeholders = ', '.join(['?' for _ in valid_columns])
                    insert_sql = f"INSERT OR IGNORE INTO \"{table}\" ({cols_str}) VALUES ({placeholders})"

                    # Filter row data to only valid columns and use executemany
                    filtered_rows = [tuple(row[i] for i in col_indices) for row in rows]

                    try:
                        cursor.executemany(insert_sql, filtered_rows)
                        restored_count = cursor.rowcount if cursor.rowcount > 0 else 0
                    except sqlite3.Error:
                        # Fall back to row-by-row on error
                        restored_count = 0
                        for row in filtered_rows:
                            try:
                                cursor.execute(insert_sql, row)
                                if cursor.rowcount > 0:
                                    restored_count += 1
                            except sqlite3.Error:
                                # Skip rows that fail (e.g., constraint violations, duplicates)
                                # This is intentional - salvage as much data as possible
                                pass

                    if restored_count > 0:
                        self._print_error(f"  Restored {restored_count}/{len(rows)} rows to {table}")
                        total_restored += restored_count
                    elif len(rows) > 0:
                        # Warn when salvaged data couldn't be restored (schema mismatch, constraints)
                        self._print_error(f"  Warning: 0/{len(rows)} rows restored to {table}")

                # Re-enable FK constraints after restore
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
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

        # Step 3: Delete corrupted file (and WAL/SHM sidecars)
        db_path = Path(self.db_path)
        try:
            if db_path.exists():
                db_path.unlink()
            # Also remove WAL and SHM sidecar files to ensure clean reinit
            for ext in ['-wal', '-shm']:
                sidecar = Path(str(db_path) + ext)
                if sidecar.exists():
                    sidecar.unlink()
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
            # Retry loop for transient lock errors during startup
            for attempt in range(4):  # 0, 1, 2, 3 = max 4 attempts
                try:
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
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
                            else:
                                # Check schema version - run migrations if outdated
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
                                if cursor.fetchone():
                                    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                                    version_row = cursor.fetchone()
                                    current_version = version_row[0] if version_row else 0
                                    # Check against expected version from init_db.py
                                    if current_version < EXPECTED_SCHEMA_VERSION:
                                        needs_init = True
                                        print(f"Database schema outdated (v{current_version} < v{EXPECTED_SCHEMA_VERSION}). Running migrations...", file=sys.stderr)
                                else:
                                    # schema_version table missing - treat as outdated and run migrations
                                    needs_init = True
                                    print(f"Database missing schema_version table at {self.db_path}. Running migrations...", file=sys.stderr)
                    break  # Success - exit retry loop
                except sqlite3.OperationalError as e:
                    # Handle transient lock errors with retry/backoff
                    error_msg = str(e).lower()
                    if any(lock_err in error_msg for lock_err in ["database is locked", "database is busy", "schema is locked"]):
                        if attempt < 3:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                            print(f"Database locked during init, retrying in {wait_time}s (attempt {attempt + 1}/4)...", file=sys.stderr)
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"Database locked after 4 attempts at {self.db_path}: {e}", file=sys.stderr)
                            raise
                    raise  # Non-lock operational error
                except sqlite3.DatabaseError as e:
                    # Check if this is a query error (wrong column/table names) vs real corruption
                    if self._is_query_error(e):
                        # Query errors should NOT trigger recovery - just propagate the error
                        print(f"Query error at {self.db_path}: {e}. This is a SQL syntax/schema error (e.g., incorrect table/column name), NOT database corruption. Fix the query.", file=sys.stderr)
                        raise  # Let caller handle it - don't destroy the database
                    elif self._is_corruption_error(e):
                        is_corrupted = True
                        needs_init = True
                        print(f"Database corrupted at {self.db_path}: {e}. Auto-recovering...", file=sys.stderr)
                    else:
                        # Unknown database error - log but don't assume corruption
                        print(f"Database error at {self.db_path}: {e}. May need investigation.", file=sys.stderr)
                        raise  # Let caller handle it
                    break  # Exit retry loop on corruption (will reinit)
                except Exception as e:
                    needs_init = True
                    print(f"Database check failed at {self.db_path}: {e}. Auto-initializing...", file=sys.stderr)
                    break  # Exit retry loop

        if not needs_init:
            return

        # CRITICAL: Use file lock to prevent concurrent schema migrations
        # Multiple parallel agents checking schema simultaneously can all trigger
        # migration, corrupting the database with orphan indexes
        lock_file_path = Path(str(db_path) + '.migrate.lock')
        lock_file = None
        lock_acquired = False
        try:
            # Create lock file and acquire exclusive lock with retry/backoff
            if HAS_FCNTL:
                # Unix/Linux/macOS: Use fcntl.flock with bounded retry
                lock_file = open(lock_file_path, 'a')
                max_retries = 4
                for attempt in range(max_retries):
                    try:
                        # Use LOCK_EX | LOCK_NB for non-blocking to enable retry
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        lock_acquired = True
                        print(f"Acquired migration lock", file=sys.stderr)
                        break
                    except (OSError, IOError) as lock_err:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                            print(f"Migration lock busy, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...", file=sys.stderr)
                            time.sleep(wait_time)
                        else:
                            # Final attempt failed - abort migration
                            if lock_file:
                                lock_file.close()
                            raise MigrationLockError(
                                f"Failed to acquire migration lock after {max_retries} attempts: {lock_err}. "
                                "Another process may be migrating the database."
                            )
            elif HAS_MSVCRT:
                # Windows: Use msvcrt.locking with bounded retry
                # msvcrt.locking locks from current file position, so we must:
                # 1. Ensure file has at least 1 byte (write sentinel if empty)
                # 2. Seek to position 0 before locking
                # 3. Lock the same position we'll unlock (position 0, 1 byte)
                try:
                    # Try to open existing file
                    lock_file = open(lock_file_path, 'r+b')
                except FileNotFoundError:
                    # Create new file
                    lock_file = open(lock_file_path, 'w+b')

                # Ensure file has at least 1 byte for valid lock region
                lock_file.seek(0, 2)  # Seek to end
                if lock_file.tell() == 0:
                    lock_file.write(b'\x00')  # Write sentinel byte
                    lock_file.flush()

                max_retries = 4
                for attempt in range(max_retries):
                    try:
                        # Always seek to 0 before locking to ensure consistent position
                        lock_file.seek(0)
                        # LK_NBLCK = non-blocking exclusive lock
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        lock_acquired = True
                        print(f"Acquired migration lock (Windows)", file=sys.stderr)
                        break
                    except (OSError, IOError) as lock_err:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                            print(f"Migration lock busy, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...", file=sys.stderr)
                            time.sleep(wait_time)
                        else:
                            # Final attempt failed - abort migration
                            if lock_file:
                                lock_file.close()
                            raise MigrationLockError(
                                f"Failed to acquire migration lock after {max_retries} attempts: {lock_err}. "
                                "Another process may be migrating the database."
                            )
            else:
                # No locking available - warn once and abort migration to prevent corruption
                global _LOCK_WARNING_SHOWN
                if not _LOCK_WARNING_SHOWN:
                    print("Warning: No file locking mechanism available (fcntl/msvcrt not found).", file=sys.stderr)
                    _LOCK_WARNING_SHOWN = True
                raise MigrationLockError(
                    "Cannot safely migrate database: no file locking mechanism available. "
                    "This prevents concurrent migration corruption. "
                    "Please ensure fcntl (Unix) or msvcrt (Windows) is available."
                )

            # Re-check schema version while holding lock - another process may have migrated
            if db_path.exists() and db_path.stat().st_size > 0:
                try:
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                        cursor = conn.cursor()

                        # If corruption was detected earlier, verify it still exists
                        if is_corrupted:
                            integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
                            if integrity != "ok":
                                # Corruption confirmed - continue to recovery below
                                print(f"Corruption confirmed under lock: {integrity}", file=sys.stderr)
                            else:
                                # Corruption was fixed by another process
                                is_corrupted = False

                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
                        if cursor.fetchone():
                            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                            version_row = cursor.fetchone()
                            current_version = version_row[0] if version_row else 0
                            if current_version >= EXPECTED_SCHEMA_VERSION and not is_corrupted:
                                print(f"Schema already up-to-date (migrated by another process)", file=sys.stderr)
                                return  # Another process already migrated
                except (sqlite3.Error, OSError) as e:
                    # Log the specific error for debugging, but don't abort migration
                    print(f"Warning: Schema re-check failed ({type(e).__name__}): {e}", file=sys.stderr)
                    # Continue with migration if re-check fails

            # If corrupted, use _recover_from_corruption() to properly salvage data
            # This follows research/sqlite-orphan-index-corruption-ultrathink.md mandate
            # to extract salvageable data before re-initialization
            if is_corrupted and db_path.exists():
                if not self._recover_from_corruption():
                    raise DatabaseInitError(
                        f"Failed to recover corrupted database at {self.db_path}. "
                        "Manual intervention may be required."
                    )
                print(f"✓ Database recovered at {self.db_path}", file=sys.stderr)
                return  # Recovery includes re-initialization, no need to continue

            # Auto-initialize the database (non-corrupted case: new or schema upgrade)
            script_dir = Path(__file__).parent
            init_script = script_dir / "init_db.py"

            import subprocess
            result = subprocess.run(
                [sys.executable, str(init_script), self.db_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise DatabaseInitError(
                    f"Failed to initialize database at {self.db_path}: {result.stderr}"
                )

            print(f"✓ Database auto-initialized at {self.db_path}", file=sys.stderr)

        finally:
            # Release lock and clean up (handles both Unix fcntl and Windows msvcrt)
            if lock_file:
                try:
                    if lock_acquired:
                        if HAS_FCNTL:
                            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                        elif HAS_MSVCRT:
                            # msvcrt.locking requires unlocking same byte range
                            lock_file.seek(0)
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    lock_file.close()
                    # DO NOT delete lock file - leaves it for future processes
                    # Deleting creates race condition: waiting process may hold FD to deleted inode
                    # while new process creates new file and locks it simultaneously
                except Exception:
                    # Ignore errors during lock release - not critical if cleanup fails
                    pass

    def _get_connection(self, retry_on_corruption: bool = True, _lock_retry: int = 0) -> sqlite3.Connection:
        """Get database connection with proper settings.

        Args:
            retry_on_corruption: If True, attempt recovery on corruption errors.
            _lock_retry: Internal counter for lock retry attempts (max 3 retries with backoff).

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
        except sqlite3.OperationalError as e:
            # Handle transient "database is locked" errors with retry/backoff
            if "database is locked" in str(e).lower() and _lock_retry < 3:
                wait_time = 2 ** _lock_retry  # Exponential backoff: 1s, 2s, 4s
                self._print_error(f"Database locked, retrying in {wait_time}s (attempt {_lock_retry + 1}/3)...")
                time.sleep(wait_time)
                return self._get_connection(retry_on_corruption, _lock_retry + 1)
            raise
        except sqlite3.DatabaseError as e:
            if retry_on_corruption and self._is_corruption_error(e):
                if self._recover_from_corruption():
                    # Retry connection after recovery
                    return self._get_connection(retry_on_corruption=False)
            raise

    # ==================== SESSION OPERATIONS ====================

    def create_session(self, session_id: str, mode: str, requirements: str,
                       initial_branch: Optional[str] = None,
                       metadata: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session with validation.

        Args:
            session_id: Unique session identifier
            mode: 'simple' or 'parallel'
            requirements: Original user requirements
            initial_branch: Git branch name (defaults to 'main')
            metadata: JSON string containing original_scope and other extensible data
        """
        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if mode not in ['simple', 'parallel']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'simple' or 'parallel'")
        if not requirements or not requirements.strip():
            raise ValueError("requirements cannot be empty")

        # Default initial_branch to 'main' if not provided
        if initial_branch is None:
            initial_branch = 'main'

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO sessions (session_id, mode, original_requirements, status, initial_branch, metadata)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, (session_id, mode, requirements, initial_branch, metadata))
            conn.commit()

            # Verify the insert by reading it back
            verify = conn.execute("""
                SELECT session_id, mode, status, start_time, created_at, initial_branch, metadata
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
                'created_at': verify['created_at'],
                'initial_branch': verify['initial_branch'],
                'metadata': verify['metadata']
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
                except Exception:
                    pass  # Best-effort cleanup, ignore rollback failures
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
                except Exception:
                    pass  # Best-effort cleanup, ignore rollback failures
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

    # ==================== EVENT OPERATIONS (v9) ====================

    def save_event(self, session_id: str, event_subtype: str, payload: str,
                   _retry_count: int = 0) -> Dict[str, Any]:
        """Save an event to orchestration_logs with log_type='event'.

        Used for: pm_bazinga, scope_change, validator_verdict events.

        Args:
            session_id: The session ID
            event_subtype: Type of event (pm_bazinga, scope_change, validator_verdict)
            payload: JSON string payload
            _retry_count: Internal retry counter

        Returns:
            Dict with success status and event_id
        """
        if _retry_count > 1:
            self._print_error(f"Max retries exceeded for save_event")
            return {"success": False, "error": "Max retries exceeded"}

        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if not event_subtype or not event_subtype.strip():
            raise ValueError("event_subtype cannot be empty")

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                INSERT INTO orchestration_logs
                (session_id, agent_type, content, log_type, event_subtype, event_payload)
                VALUES (?, 'system', ?, 'event', ?, ?)
            """, (session_id, f"Event: {event_subtype}", event_subtype, payload))
            event_id = cursor.lastrowid
            conn.commit()

            result = {
                'success': True,
                'event_id': event_id,
                'session_id': session_id,
                'event_subtype': event_subtype
            }

            self._print_success(f"✓ Saved {event_subtype} event (id={event_id})")
            return result

        except sqlite3.DatabaseError as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            if self._is_corruption_error(e):
                if self._recover_from_corruption():
                    return self.save_event(session_id, event_subtype, payload,
                                          _retry_count=_retry_count + 1)
            self._print_error(f"Failed to save {event_subtype} event: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            self._print_error(f"Failed to save {event_subtype} event: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_events(self, session_id: str, event_subtype: Optional[str] = None,
                   limit: int = 50) -> List[Dict]:
        """Get events from orchestration_logs where log_type='event'.

        Args:
            session_id: The session ID
            event_subtype: Optional filter by event type (pm_bazinga, scope_change, etc.)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries with id, event_subtype, event_payload, timestamp
        """
        conn = self._get_connection()

        query = """
            SELECT id, session_id, timestamp, event_subtype, event_payload
            FROM orchestration_logs
            WHERE session_id = ? AND log_type = 'event'
        """
        params = [session_id]

        if event_subtype:
            query += " AND event_subtype = ?"
            params.append(event_subtype)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(row) for row in rows]

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
                         status: str = 'pending', assigned_to: Optional[str] = None,
                         specializations: Optional[List[str]] = None,
                         item_count: Optional[int] = None,
                         component_path: Optional[str] = None,
                         initial_tier: Optional[str] = None,
                         complexity: Optional[int] = None) -> Dict[str, Any]:
        """Create or update a task group (upsert - idempotent operation).

        Uses INSERT ... ON CONFLICT to handle duplicates gracefully. If the group
        already exists, only name/status/assigned_to/specializations/item_count/component_path/initial_tier/complexity
        are updated - preserving revision_count, last_review_status, and created_at.

        Args:
            specializations: List of specialization file paths for this group
            item_count: Number of discrete tasks/items in this group (for progress tracking)
            component_path: Monorepo component path (e.g., 'frontend/', 'backend/') for version lookup
            initial_tier: Starting agent tier ('Developer' or 'Senior Software Engineer')
            complexity: Task complexity score (1-10). 1-3=Low, 4-6=Medium, 7-10=High

        Returns:
            Dict with 'success' bool and 'task_group' data, or 'error' on failure.
        """
        conn = None
        try:
            # Defensive type validation for specializations
            if specializations is not None:
                if not isinstance(specializations, list):
                    return {
                        "success": False,
                        "error": f"specializations must be a list, got {type(specializations).__name__}"
                    }
                if not all(isinstance(s, str) for s in specializations):
                    return {
                        "success": False,
                        "error": "specializations must contain only strings"
                    }
                # Normalize and validate paths (auto-prefix short paths)
                normalized_specs = []
                for spec_path in specializations:
                    is_valid, result = self._normalize_specialization_path(spec_path)
                    if not is_valid:
                        return {
                            "success": False,
                            "error": f"Invalid specialization path: {result}"
                        }
                    normalized_specs.append(result)
                specializations = normalized_specs

            # Validate item_count if provided
            if item_count is not None and (not isinstance(item_count, int) or item_count < 1):
                return {
                    "success": False,
                    "error": "item_count must be a positive integer"
                }

            # Validate initial_tier if provided
            valid_tiers = ('Developer', 'Senior Software Engineer')
            if initial_tier is not None and initial_tier not in valid_tiers:
                return {
                    "success": False,
                    "error": f"initial_tier must be one of {valid_tiers}, got '{initial_tier}'"
                }

            # Validate complexity if provided (must be 1-10)
            complexity_error = validate_complexity(complexity)
            if complexity_error:
                return {"success": False, "error": complexity_error}

            conn = self._get_connection()
            # Serialize specializations to JSON (preserve [] vs None distinction)
            specs_json = json.dumps(specializations) if specializations is not None else None
            # Use ON CONFLICT for true upsert - preserves existing metadata
            # COALESCE for status: INSERT uses 'pending' default, UPDATE preserves existing if None passed
            conn.execute("""
                INSERT INTO task_groups (id, session_id, name, status, assigned_to, specializations, item_count, component_path, initial_tier, complexity)
                VALUES (?, ?, ?, COALESCE(?, 'pending'), ?, ?, COALESCE(?, 1), ?, COALESCE(?, 'Developer'), ?)
                ON CONFLICT(id, session_id) DO UPDATE SET
                    name = excluded.name,
                    status = COALESCE(excluded.status, task_groups.status),
                    assigned_to = COALESCE(excluded.assigned_to, task_groups.assigned_to),
                    specializations = COALESCE(excluded.specializations, task_groups.specializations),
                    item_count = COALESCE(excluded.item_count, task_groups.item_count),
                    component_path = COALESCE(excluded.component_path, task_groups.component_path),
                    initial_tier = COALESCE(excluded.initial_tier, task_groups.initial_tier),
                    complexity = COALESCE(excluded.complexity, task_groups.complexity),
                    updated_at = CURRENT_TIMESTAMP
            """, (group_id, session_id, name, status, assigned_to, specs_json, item_count, component_path, initial_tier, complexity))
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
                         auto_create: bool = True, name: Optional[str] = None,
                         specializations: Optional[List[str]] = None,
                         item_count: Optional[int] = None,
                         security_sensitive: Optional[int] = None,
                         qa_attempts: Optional[int] = None,
                         tl_review_attempts: Optional[int] = None,
                         component_path: Optional[str] = None,
                         initial_tier: Optional[str] = None,
                         complexity: Optional[int] = None) -> Dict[str, Any]:
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
            specializations: List of specialization file paths for this group
            item_count: Number of discrete tasks/items in this group
            security_sensitive: Whether this group has security-sensitive code (0 or 1)
            qa_attempts: Number of QA test attempts
            tl_review_attempts: Number of Tech Lead review attempts
            component_path: Monorepo component path (e.g., 'frontend/', 'backend/') for version lookup
            initial_tier: Starting agent tier ('Developer' or 'Senior Software Engineer')
            complexity: Task complexity score (1-10). 1-3=Low, 4-6=Medium, 7-10=High

        Returns:
            Dict with 'success' bool and 'task_group' data, or 'error' on failure.
        """
        conn = None
        try:
            # Defensive type validation for specializations
            if specializations is not None:
                if not isinstance(specializations, list):
                    return {
                        "success": False,
                        "error": f"specializations must be a list, got {type(specializations).__name__}"
                    }
                if not all(isinstance(s, str) for s in specializations):
                    return {
                        "success": False,
                        "error": "specializations must contain only strings"
                    }
                # Normalize and validate paths (auto-prefix short paths)
                normalized_specs = []
                for spec_path in specializations:
                    is_valid, result = self._normalize_specialization_path(spec_path)
                    if not is_valid:
                        return {
                            "success": False,
                            "error": f"Invalid specialization path: {result}"
                        }
                    normalized_specs.append(result)
                specializations = normalized_specs

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
            if name:
                updates.append("name = ?")
                params.append(name)
            if specializations is not None:
                updates.append("specializations = ?")
                params.append(json.dumps(specializations))
            if item_count is not None:
                updates.append("item_count = ?")
                params.append(item_count)
            if security_sensitive is not None:
                updates.append("security_sensitive = ?")
                params.append(security_sensitive)
            if qa_attempts is not None:
                updates.append("qa_attempts = ?")
                params.append(qa_attempts)
            if tl_review_attempts is not None:
                updates.append("tl_review_attempts = ?")
                params.append(tl_review_attempts)
            if component_path is not None:
                updates.append("component_path = ?")
                params.append(component_path)
            if initial_tier is not None:
                valid_tiers = ('Developer', 'Senior Software Engineer')
                if initial_tier not in valid_tiers:
                    return {
                        "success": False,
                        "error": f"initial_tier must be one of {valid_tiers}, got '{initial_tier}'"
                    }
                updates.append("initial_tier = ?")
                params.append(initial_tier)
            if complexity is not None:
                complexity_error = validate_complexity(complexity)
                if complexity_error:
                    return {"success": False, "error": complexity_error}
                updates.append("complexity = ?")
                params.append(complexity)

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

    def save_skill_output(self, session_id: str, skill_name: str, output_data: Dict,
                         agent_type: Optional[str] = None, group_id: Optional[str] = None) -> int:
        """Save skill output with auto-computed iteration.

        Iteration is computed atomically using INSERT...SELECT to prevent race conditions.
        Uses UNIQUE constraint with retry on IntegrityError for concurrent safety.
        Returns the iteration number assigned.
        """
        conn = self._get_connection()
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Use BEGIN IMMEDIATE to acquire exclusive lock upfront
                conn.execute("BEGIN IMMEDIATE")

                # Atomic INSERT with computed iteration using INSERT...SELECT
                # Build WHERE clause properly for NULL handling
                if agent_type is None and group_id is None:
                    where_clause = "agent_type IS NULL AND group_id IS NULL"
                    params = (session_id, skill_name, json.dumps(output_data), session_id, skill_name)
                elif agent_type is None:
                    where_clause = "agent_type IS NULL AND group_id = ?"
                    params = (session_id, skill_name, json.dumps(output_data), group_id, session_id, skill_name, group_id)
                elif group_id is None:
                    where_clause = "agent_type = ? AND group_id IS NULL"
                    params = (session_id, skill_name, json.dumps(output_data), agent_type, session_id, skill_name, agent_type)
                else:
                    where_clause = "agent_type = ? AND group_id = ?"
                    params = (session_id, skill_name, json.dumps(output_data), agent_type, group_id, session_id, skill_name, agent_type, group_id)

                cursor = conn.execute(f"""
                    INSERT INTO skill_outputs (session_id, skill_name, output_data, agent_type, group_id, iteration)
                    SELECT ?, ?, ?, {'NULL' if agent_type is None else '?'}, {'NULL' if group_id is None else '?'},
                           COALESCE((SELECT MAX(iteration) FROM skill_outputs
                                     WHERE session_id = ? AND skill_name = ? AND {where_clause}), 0) + 1
                """, params)

                # Get the iteration that was assigned
                next_iteration = conn.execute(f"""
                    SELECT iteration FROM skill_outputs
                    WHERE rowid = ?
                """, (cursor.lastrowid,)).fetchone()['iteration']

                conn.commit()
                conn.close()
                break  # Success, exit retry loop

            except sqlite3.IntegrityError as e:
                conn.rollback()
                if attempt < max_retries - 1:
                    # Retry on UNIQUE constraint violation (concurrent insert)
                    import time
                    time.sleep(0.01 * (attempt + 1))  # Brief backoff
                    continue
                else:
                    conn.close()
                    raise
            except Exception as e:
                conn.rollback()
                conn.close()
                raise

        if agent_type:
            self._print_success(f"✓ Saved {skill_name} output for {agent_type} (iteration {next_iteration})")
        else:
            self._print_success(f"✓ Saved {skill_name} output (iteration {next_iteration})")
        return next_iteration

    def get_skill_output(self, session_id: str, skill_name: str,
                        agent_type: Optional[str] = None) -> Optional[Dict]:
        """Get latest skill output (backward compatible).

        If agent_type is provided, returns latest for that agent.
        Otherwise returns latest across all agents.
        """
        conn = self._get_connection()

        if agent_type:
            row = conn.execute("""
                SELECT output_data FROM skill_outputs
                WHERE session_id = ? AND skill_name = ? AND agent_type = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (session_id, skill_name, agent_type)).fetchone()
        else:
            row = conn.execute("""
                SELECT output_data FROM skill_outputs
                WHERE session_id = ? AND skill_name = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (session_id, skill_name)).fetchone()

        conn.close()
        return json.loads(row['output_data']) if row else None

    def get_skill_output_all(self, session_id: str, skill_name: str,
                            agent_type: Optional[str] = None) -> List[Dict]:
        """Get all skill outputs for a skill (supports multi-invocation).

        Returns array of objects with iteration, agent_type, group_id, timestamp, and output_data.
        Ordered by timestamp DESC (most recent first) for consistent access patterns.
        """
        conn = self._get_connection()

        if agent_type:
            # Filter by agent type, order by timestamp DESC for consistent "latest first"
            rows = conn.execute("""
                SELECT iteration, agent_type, group_id, timestamp, output_data
                FROM skill_outputs
                WHERE session_id = ? AND skill_name = ? AND agent_type = ?
                ORDER BY timestamp DESC
            """, (session_id, skill_name, agent_type)).fetchall()
        else:
            # All outputs for skill, order by timestamp DESC
            rows = conn.execute("""
                SELECT iteration, agent_type, group_id, timestamp, output_data
                FROM skill_outputs
                WHERE session_id = ? AND skill_name = ?
                ORDER BY timestamp DESC
            """, (session_id, skill_name)).fetchall()

        conn.close()

        return [{
            'iteration': row['iteration'],
            'agent_type': row['agent_type'],
            'group_id': row['group_id'],
            'timestamp': row['timestamp'],
            'output_data': json.loads(row['output_data'])
        } for row in rows]

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

    # ==================== REASONING CAPTURE OPERATIONS ====================
    # See: research/agent-reasoning-capture-ultrathink.md

    # Valid reasoning phases
    VALID_REASONING_PHASES = frozenset({
        'understanding',  # Initial problem comprehension
        'approach',       # Strategy selection
        'decisions',      # Key choices made
        'risks',          # Identified risks/concerns
        'blockers',       # Issues preventing progress
        'pivot',          # Strategy changes mid-execution
        'completion',     # Final summary/outcome
    })

    # Valid confidence levels
    VALID_CONFIDENCE_LEVELS = frozenset({'high', 'medium', 'low'})

    def save_reasoning(self, session_id: str, group_id: str, agent_type: str,
                       reasoning_phase: str, content: str,
                       agent_id: Optional[str] = None, iteration: Optional[int] = None,
                       confidence: Optional[str] = None,
                       references: Optional[List[str]] = None,
                       _retry_count: int = 0) -> Dict[str, Any]:
        """Save agent reasoning to the database with secret redaction.

        Args:
            session_id: Session identifier
            group_id: Task group identifier
            agent_type: Type of agent (e.g., 'developer', 'tech_lead')
            reasoning_phase: Phase of reasoning (understanding, approach, decisions, etc.)
            content: The reasoning text to save
            agent_id: Optional specific agent ID
            iteration: Optional iteration number
            confidence: Optional confidence level (high, medium, low)
            references: Optional list of file paths consulted
            _retry_count: Internal retry counter for exponential backoff

        Returns:
            Dict with success status and log details
        """
        # Validate inputs
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty")
        if not group_id or not group_id.strip():
            raise ValueError("group_id cannot be empty")
        if not agent_type or not agent_type.strip():
            raise ValueError("agent_type cannot be empty")
        if not reasoning_phase or not reasoning_phase.strip():
            raise ValueError("reasoning_phase cannot be empty")
        if reasoning_phase not in self.VALID_REASONING_PHASES:
            raise ValueError(f"Invalid reasoning_phase: {reasoning_phase}. Must be one of: {sorted(self.VALID_REASONING_PHASES)}")
        if not content or not content.strip():
            raise ValueError("content cannot be empty")
        if confidence is not None and confidence not in self.VALID_CONFIDENCE_LEVELS:
            raise ValueError(f"Invalid confidence: {confidence}. Must be one of: {sorted(self.VALID_CONFIDENCE_LEVELS)}")

        # Validate and coerce references to list of strings
        if references is not None:
            if not isinstance(references, list):
                raise TypeError(f"references must be a list, got {type(references).__name__}")
            for i, ref in enumerate(references):
                if not isinstance(ref, str):
                    raise TypeError(f"references[{i}] must be a string, got {type(ref).__name__}")

        # Scan and redact secrets
        redacted_content, was_redacted = scan_and_redact(content)
        if was_redacted:
            self._print_error("Warning: Secrets detected and redacted from reasoning content")

        # Serialize references
        references_json = json.dumps(references) if references else None

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                INSERT INTO orchestration_logs
                (session_id, iteration, agent_type, agent_id, content, log_type,
                 reasoning_phase, confidence_level, references_json, redacted, group_id)
                VALUES (?, ?, ?, ?, ?, 'reasoning', ?, ?, ?, ?, ?)
            """, (session_id, iteration, agent_type, agent_id, redacted_content,
                  reasoning_phase, confidence, references_json,
                  1 if was_redacted else 0, group_id))
            log_id = cursor.lastrowid
            conn.commit()

            # Verify the insert
            verify = conn.execute("""
                SELECT id, session_id, agent_type, reasoning_phase, LENGTH(content) as content_length,
                       timestamp, redacted, group_id
                FROM orchestration_logs WHERE id = ?
            """, (log_id,)).fetchone()

            if not verify:
                raise RuntimeError(f"Failed to verify reasoning save for log_id={log_id}")

            result = {
                'success': True,
                'log_id': log_id,
                'session_id': verify['session_id'],
                'group_id': verify['group_id'],
                'agent_type': verify['agent_type'],
                'reasoning_phase': verify['reasoning_phase'],
                'content_length': verify['content_length'],
                'timestamp': verify['timestamp'],
                'redacted': bool(verify['redacted']),
            }

            self._print_success(f"✓ Saved {agent_type} reasoning ({reasoning_phase}, log_id={log_id}, {result['content_length']} chars)")
            return result

        except sqlite3.OperationalError as e:
            # Handle "database is locked" with exponential backoff + jitter
            if "database is locked" in str(e).lower() and _retry_count < 4:
                wait_time = (2 ** _retry_count) + random.uniform(0, 0.5)  # Jitter prevents thundering herd
                self._print_error(f"Database locked, retrying in {wait_time:.1f}s (attempt {_retry_count + 1}/4)...")
                time.sleep(wait_time)
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass  # Best-effort cleanup, ignore close failures
                return self.save_reasoning(
                    session_id, group_id, agent_type, reasoning_phase, content,
                    agent_id, iteration, confidence, references,
                    _retry_count=_retry_count + 1
                )
            # Retries exhausted or non-lock error - return structured error (don't raise)
            self._print_error(f"Database error saving {agent_type} reasoning: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass  # Best-effort cleanup, ignore rollback failures
            self._print_error(f"Failed to save {agent_type} reasoning: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_reasoning(self, session_id: str, group_id: Optional[str] = None,
                      agent_type: Optional[str] = None,
                      phase: Optional[str] = None,
                      limit: int = 50,
                      output_format: str = 'json') -> Any:
        """Get reasoning entries with optional filtering.

        Args:
            session_id: Session identifier
            group_id: Optional task group filter
            agent_type: Optional agent type filter
            phase: Optional reasoning phase filter
            limit: Maximum number of results (default 50)
            output_format: Output format - 'json' (default) or 'prompt-summary'
                           prompt-summary returns pre-truncated markdown ready for prompts

        Returns:
            List of reasoning entries (json) or formatted markdown string (prompt-summary)
        """
        conn = self._get_connection()

        query = """
            SELECT id, session_id, group_id, agent_type, agent_id, iteration,
                   reasoning_phase, confidence_level, content, references_json,
                   redacted, timestamp
            FROM orchestration_logs
            WHERE session_id = ? AND log_type = 'reasoning'
        """
        params: List[Any] = [session_id]

        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)

        if agent_type:
            query += " AND agent_type = ?"
            params.append(agent_type)

        if phase:
            if phase not in self.VALID_REASONING_PHASES:
                raise ValueError(f"Invalid phase: {phase}. Must be one of: {sorted(self.VALID_REASONING_PHASES)}")
            query += " AND reasoning_phase = ?"
            params.append(phase)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()

        results = []
        for row in rows:
            entry = dict(row)
            # Parse references_json back to list
            if entry.get('references_json'):
                try:
                    entry['references'] = json.loads(entry['references_json'])
                except json.JSONDecodeError:
                    entry['references'] = []
            else:
                entry['references'] = []
            del entry['references_json']
            entry['redacted'] = bool(entry.get('redacted', 0))
            results.append(entry)

        # Return based on output format
        if output_format == 'prompt-summary':
            # Return pre-formatted markdown ready for prompt injection
            # Truncates content to 300 chars per entry, max 5 entries (per orchestrator template spec)
            if not results:
                return "No previous reasoning found for this context."

            # Limit to max 5 entries for prompt injection (prevents context bloat)
            max_entries = 5
            limited_results = results[:max_entries]
            total_count = len(results)

            lines = [
                "## Previous Agent Reasoning (Handoff Context)",
                "",
                "Prior agents documented their decision-making for this task:",
                "",
                "| Agent | Phase | Confidence | Key Points (max 300 chars) |",
                "|-------|-------|------------|----------------------------|"
            ]
            for entry in limited_results:
                agent = entry.get('agent_type', 'unknown')
                phase = entry.get('reasoning_phase', 'unknown')
                confidence = entry.get('confidence_level', '-')
                content = entry.get('content', '')
                # Truncate content to 300 chars
                if len(content) > 300:
                    content = content[:297] + "..."
                # Escape pipe characters and newlines for markdown table
                content = content.replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {agent} | {phase} | {confidence} | {content} |")

            # Add truncation notice if entries were limited
            if total_count > max_entries:
                lines.append(f"\n*Showing {max_entries} of {total_count} entries (use --format json for full data)*")

            lines.extend([
                "",
                "**Use this to:**",
                "- Understand WHY prior decisions were made (not just WHAT)",
                "- Avoid repeating failed approaches (check `pivot` and `blockers` phases)",
                "- Build on prior agent's understanding"
            ])
            return '\n'.join(lines)

        return results

    def reasoning_timeline(self, session_id: str, group_id: Optional[str] = None,
                           output_format: str = 'json') -> str:
        """Get a timeline of reasoning across all agents.

        Args:
            session_id: Session identifier
            group_id: Optional task group filter
            output_format: Output format ('json' or 'markdown')

        Returns:
            Formatted timeline string
        """
        conn = self._get_connection()

        query = """
            SELECT id, group_id, agent_type, agent_id, iteration,
                   reasoning_phase, confidence_level, content, redacted, timestamp
            FROM orchestration_logs
            WHERE session_id = ? AND log_type = 'reasoning'
        """
        params: List[Any] = [session_id]

        if group_id:
            query += " AND group_id = ?"
            params.append(group_id)

        query += " ORDER BY timestamp ASC"

        rows = conn.execute(query, params).fetchall()
        conn.close()

        entries = [dict(row) for row in rows]

        if output_format == 'json':
            return json.dumps(entries, indent=2)

        # Markdown format
        if not entries:
            return "# Reasoning Timeline\n\nNo reasoning entries found."

        lines = ["# Reasoning Timeline", ""]
        current_group = None

        for entry in entries:
            # Group header
            if entry['group_id'] != current_group:
                current_group = entry['group_id']
                lines.append(f"## Group: {current_group or 'global'}")
                lines.append("")

            # Entry
            timestamp = entry['timestamp']
            agent = entry['agent_type']
            if entry['agent_id']:
                agent = f"{agent} ({entry['agent_id']})"
            phase = entry['reasoning_phase']
            confidence = entry.get('confidence_level', '')
            confidence_badge = f" [{confidence}]" if confidence else ""
            redacted_badge = " 🔒" if entry.get('redacted') else ""

            lines.append(f"### [{timestamp}] {agent} - {phase}{confidence_badge}{redacted_badge}")
            lines.append("")

            # Truncate long content for timeline view (300 chars per template spec)
            content = entry['content']
            if len(content) > 300:
                content = content[:300] + "..."
            # Escape backtick sequences to prevent code fence breakout (security: prevents prompt injection)
            # Replace ``` with `\u200b`\u200b` (zero-width space breaks the fence sequence)
            content = content.replace('```', '`\u200b`\u200b`')
            # Wrap in code fence to escape markdown special chars (prevents formatting injection)
            lines.append("```text")
            lines.append(content)
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    # Mandatory reasoning phases that must be documented
    MANDATORY_PHASES = frozenset({'understanding', 'completion'})

    def check_mandatory_phases(self, session_id: str, group_id: str,
                               agent_type: str) -> Dict[str, Any]:
        """Check if mandatory reasoning phases have been documented.

        Args:
            session_id: Session identifier
            group_id: Task group identifier
            agent_type: Type of agent to check

        Returns:
            Dict with:
                - complete: bool - True if all mandatory phases documented
                - missing: List[str] - Phases not yet documented
                - documented: List[str] - Phases that have been documented
        """
        conn = self._get_connection()

        # Get all reasoning phases for this agent/group
        rows = conn.execute("""
            SELECT DISTINCT reasoning_phase
            FROM orchestration_logs
            WHERE session_id = ? AND group_id = ? AND agent_type = ?
              AND log_type = 'reasoning' AND reasoning_phase IS NOT NULL
        """, (session_id, group_id, agent_type)).fetchall()
        conn.close()

        documented = {row['reasoning_phase'] for row in rows}
        missing = list(self.MANDATORY_PHASES - documented)
        documented_mandatory = list(self.MANDATORY_PHASES & documented)

        return {
            'complete': len(missing) == 0,
            'missing': sorted(missing),
            'documented': sorted(documented_mandatory),
            'all_documented': sorted(documented),
            'session_id': session_id,
            'group_id': group_id,
            'agent_type': agent_type,
        }

    # ==================== ERROR PATTERN OPERATIONS ====================
    # Phase 5: User Story 3 - Error Pattern Capture (T024-T031)
    # See: specs/1-context-engineering/data-model.md for schema

    def _extract_error_signature(self, error_type: str, error_message: str,
                                  context_hints: List[str] = None,
                                  stack_pattern: List[str] = None) -> Dict[str, Any]:
        """T024: Extract structured error signature from error details.

        Creates a normalized signature that can be used for matching similar errors.

        Args:
            error_type: Error class/type (e.g., "ModuleNotFoundError", "TypeError")
            error_message: Full error message text
            context_hints: List of contextual hints (e.g., ["import statement", "tsconfig"])
            stack_pattern: Simplified stack trace patterns (e.g., ["file.py:123"])

        Returns:
            Dict with structured signature fields
        """
        import re

        # Normalize error message - remove variable parts (paths, line numbers, specific values)
        message_pattern = error_message
        # Remove absolute paths (Unix)
        message_pattern = re.sub(r'/[^\s]+/', '.../', message_pattern)
        # Remove absolute paths (Windows) - use raw string for replacement to avoid escape issues
        message_pattern = re.sub(r'[A-Z]:\\[^\s]+\\', r'...\\', message_pattern)
        # Remove line numbers
        message_pattern = re.sub(r'line \d+', 'line N', message_pattern)
        # Remove specific variable names/values but keep structure
        message_pattern = re.sub(r"'[^']{1,50}'", "'...'", message_pattern)
        message_pattern = re.sub(r'"[^"]{1,50}"', '"..."', message_pattern)

        return {
            "error_type": error_type.strip() if error_type else "Unknown",
            "message_pattern": message_pattern.strip()[:500],  # Limit length
            "context_hints": context_hints or [],
            "stack_pattern": stack_pattern or []
        }

    def _generate_pattern_hash(self, signature: Dict[str, Any]) -> str:
        """T026: Generate SHA256 hash of normalized error signature.

        The hash uniquely identifies an error pattern for deduplication.
        """
        import hashlib

        # Create deterministic string representation
        # Sort keys and normalize for consistent hashing
        hash_input = (
            f"{signature.get('error_type', '')}:"
            f"{signature.get('message_pattern', '')}:"
            f"{','.join(sorted(signature.get('context_hints', [])))}"
        )

        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def save_error_pattern(self, project_id: str, error_type: str, error_message: str,
                          solution: str, lang: str = None,
                          context_hints: List[str] = None,
                          stack_pattern: List[str] = None) -> Dict[str, Any]:
        """T024-T027: Save an error pattern from a fail-then-succeed flow.

        Captures error signature, redacts secrets, generates hash, and stores.
        If pattern already exists, updates occurrences and last_seen.

        Args:
            project_id: Project identifier for isolation
            error_type: Error class/type (e.g., "ModuleNotFoundError")
            error_message: Full error message text
            solution: How the error was resolved
            lang: Programming language (optional)
            context_hints: Contextual hints for matching
            stack_pattern: Simplified stack trace patterns

        Returns:
            Dict with pattern_hash and operation result
        """
        # T024: Extract signature
        signature = self._extract_error_signature(
            error_type, error_message, context_hints, stack_pattern
        )

        # T025: Redact secrets from signature and solution
        signature_json = json.dumps(signature)
        signature_json, sig_redacted = scan_and_redact(signature_json)
        solution, sol_redacted = scan_and_redact(solution)

        # T026: Generate pattern hash
        pattern_hash = self._generate_pattern_hash(json.loads(signature_json))

        conn = self._get_connection()
        try:
            # Check if pattern already exists
            existing = conn.execute("""
                SELECT occurrences, confidence FROM error_patterns
                WHERE pattern_hash = ? AND project_id = ?
            """, (pattern_hash, project_id)).fetchone()

            if existing:
                # Update existing pattern
                new_occurrences = existing['occurrences'] + 1
                conn.execute("""
                    UPDATE error_patterns
                    SET occurrences = ?,
                        last_seen = datetime('now'),
                        solution = CASE WHEN COALESCE(length(?), 0) > COALESCE(length(solution), 0) THEN ? ELSE solution END
                    WHERE pattern_hash = ? AND project_id = ?
                """, (new_occurrences, solution, solution, pattern_hash, project_id))
                conn.commit()

                self._print_success(f"✓ Updated error pattern (occurrences: {new_occurrences})")
                return {
                    "success": True,
                    "pattern_hash": pattern_hash,
                    "operation": "updated",
                    "occurrences": new_occurrences,
                    "redacted": sig_redacted or sol_redacted
                }
            else:
                # Insert new pattern with initial confidence 0.5
                conn.execute("""
                    INSERT INTO error_patterns
                    (pattern_hash, project_id, signature_json, solution, confidence,
                     occurrences, lang, last_seen, created_at, ttl_days)
                    VALUES (?, ?, ?, ?, 0.5, 1, ?, datetime('now'), datetime('now'), 90)
                """, (pattern_hash, project_id, signature_json, solution, lang))
                conn.commit()

                self._print_success(f"✓ Saved new error pattern: {pattern_hash[:16]}...")
                return {
                    "success": True,
                    "pattern_hash": pattern_hash,
                    "operation": "created",
                    "occurrences": 1,
                    "confidence": 0.5,
                    "redacted": sig_redacted or sol_redacted
                }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save error pattern: {str(e)}")
        finally:
            conn.close()

    def get_error_patterns(self, project_id: str, lang: str = None,
                          min_confidence: float = 0.7,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """T028: Query matching error patterns for context injection.

        Returns patterns above confidence threshold for the given project.

        Args:
            project_id: Project identifier for isolation
            lang: Filter by programming language (optional)
            min_confidence: Minimum confidence threshold (default: 0.7)
            limit: Maximum patterns to return (default: 5)

        Returns:
            List of error patterns with signature, solution, confidence
        """
        conn = self._get_connection()

        if lang:
            rows = conn.execute("""
                SELECT pattern_hash, signature_json, solution, confidence,
                       occurrences, lang, last_seen
                FROM error_patterns
                WHERE project_id = ? AND lang = ? AND confidence >= ?
                ORDER BY confidence DESC, occurrences DESC
                LIMIT ?
            """, (project_id, lang, min_confidence, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT pattern_hash, signature_json, solution, confidence,
                       occurrences, lang, last_seen
                FROM error_patterns
                WHERE project_id = ? AND confidence >= ?
                ORDER BY confidence DESC, occurrences DESC
                LIMIT ?
            """, (project_id, min_confidence, limit)).fetchall()

        conn.close()

        result = []
        for row in rows:
            pattern = dict(row)
            # Parse signature JSON
            try:
                pattern['signature'] = json.loads(pattern.pop('signature_json'))
            except json.JSONDecodeError:
                pattern['signature'] = {}
            result.append(pattern)

        return result

    def update_error_pattern_confidence(self, pattern_hash: str, project_id: str,
                                        success: bool) -> Dict[str, Any]:
        """T030: Adjust confidence based on match outcome.

        Rules:
        - Successful match: +0.1 (max 1.0)
        - False positive report: -0.2 (min 0.1)
        - Below 0.3: Pattern still stored but not injected

        Args:
            pattern_hash: Hash of the pattern to update
            project_id: Project identifier
            success: True if solution helped, False if false positive

        Returns:
            Dict with updated confidence value
        """
        conn = self._get_connection()

        try:
            # Get current confidence
            row = conn.execute("""
                SELECT confidence FROM error_patterns
                WHERE pattern_hash = ? AND project_id = ?
            """, (pattern_hash, project_id)).fetchone()

            if not row:
                return {"success": False, "error": "Pattern not found"}

            current = row['confidence']

            # Apply adjustment rules
            if success:
                new_confidence = min(1.0, current + 0.1)
            else:
                new_confidence = max(0.1, current - 0.2)

            conn.execute("""
                UPDATE error_patterns
                SET confidence = ?, last_seen = datetime('now')
                WHERE pattern_hash = ? AND project_id = ?
            """, (new_confidence, pattern_hash, project_id))
            conn.commit()

            self._print_success(f"✓ Updated confidence: {current:.2f} → {new_confidence:.2f}")
            return {
                "success": True,
                "pattern_hash": pattern_hash,
                "previous_confidence": current,
                "new_confidence": new_confidence,
                "injectable": new_confidence >= 0.3  # Below 0.3: observe only
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update confidence: {str(e)}")
        finally:
            conn.close()

    def cleanup_expired_patterns(self, project_id: str = None) -> Dict[str, Any]:
        """T031: Remove patterns that have exceeded their TTL.

        Patterns are deleted when last_seen + ttl_days < current date.

        Args:
            project_id: Limit cleanup to specific project (optional)

        Returns:
            Dict with count of deleted patterns
        """
        conn = self._get_connection()

        try:
            if project_id is not None:
                cursor = conn.execute("""
                    DELETE FROM error_patterns
                    WHERE project_id = ?
                    AND date(last_seen, '+' || ttl_days || ' days') < date('now')
                """, (project_id,))
            else:
                cursor = conn.execute("""
                    DELETE FROM error_patterns
                    WHERE date(last_seen, '+' || ttl_days || ' days') < date('now')
                """)

            deleted_count = cursor.rowcount
            conn.commit()

            self._print_success(f"✓ Cleaned up {deleted_count} expired error patterns")
            return {
                "success": True,
                "deleted_count": deleted_count,
                "project_id": project_id
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to cleanup patterns: {str(e)}")
        finally:
            conn.close()

    # ==================== CONSUMPTION SCOPE OPERATIONS ====================

    def save_consumption(self, session_id: str, group_id: str, agent_type: str,
                         iteration: int, package_id: int) -> Dict[str, Any]:
        """Save consumption record to consumption_scope table (T037).

        Args:
            session_id: Session identifier
            group_id: Task group identifier
            agent_type: Type of agent consuming the package
            iteration: Iteration number (0-based)
            package_id: ID of the consumed context package

        Returns:
            Dict with scope_id and success status
        """
        import hashlib
        # Deterministic scope_id for idempotency (same inputs = same ID)
        composite = f"{session_id}:{group_id}:{agent_type}:{iteration}:{package_id}"
        scope_id = hashlib.sha256(composite.encode()).hexdigest()[:32]

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO consumption_scope
                (scope_id, session_id, group_id, agent_type, iteration, package_id, consumed_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (scope_id, session_id, group_id, agent_type, iteration, package_id))
            conn.commit()

            # Check if row was actually inserted (vs ignored as duplicate)
            inserted = cursor.rowcount > 0

            if inserted:
                self._print_success(f"✓ Saved consumption: {agent_type} consumed package {package_id}")
            else:
                self._print_success(f"✓ Consumption exists: {agent_type} package {package_id} (idempotent)")

            return {
                "success": True,
                "inserted": inserted,
                "scope_id": scope_id,
                "session_id": session_id,
                "group_id": group_id,
                "agent_type": agent_type,
                "iteration": iteration,
                "package_id": package_id
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save consumption: {str(e)}")
        finally:
            conn.close()

    def get_consumption(self, session_id: str, group_id: Optional[str] = None,
                        agent_type: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Query consumption_scope records (T037).

        Args:
            session_id: Session identifier
            group_id: Optional filter by group
            agent_type: Optional filter by agent type
            limit: Maximum records to return (default 50, clamped to 1-1000)

        Returns:
            List of consumption records
        """
        # Clamp limit to safe range (1-1000)
        limit = max(1, min(limit, 1000))

        conn = self._get_connection()
        try:
            sql = "SELECT * FROM consumption_scope WHERE session_id = ?"
            params: List[Any] = [session_id]

            if group_id:
                sql += " AND group_id = ?"
                params.append(group_id)
            if agent_type:
                sql += " AND agent_type = ?"
                params.append(agent_type)

            sql += " ORDER BY consumed_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==================== STRATEGIES OPERATIONS ====================

    VALID_TOPICS = {'implementation', 'architecture', 'methodology', 'general'}

    def save_strategy(self, project_id: str, topic: str, insight: str,
                      lang: Optional[str] = None, framework: Optional[str] = None,
                      strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """Save strategy to strategies table (T038).

        Args:
            project_id: Project identifier
            topic: Category (implementation, architecture, methodology, general)
            insight: The actual insight/approach (max 500 chars)
            lang: Optional language context
            framework: Optional framework context
            strategy_id: Optional custom ID (auto-generated if not provided)

        Returns:
            Dict with strategy_id and success status
        """
        import hashlib

        # Validate topic against allowed values
        if topic not in self.VALID_TOPICS:
            topic = 'general'  # Normalize invalid topics to 'general'

        # Generate strategy_id from content hash if not provided
        if not strategy_id:
            content_hash = hashlib.sha256(insight.encode()).hexdigest()[:16]
            strategy_id = f"{project_id}_{topic}_{content_hash}"

        # Truncate insight to 500 chars
        insight = insight[:500] if len(insight) > 500 else insight

        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO strategies (strategy_id, project_id, topic, insight, helpfulness, lang, framework, last_seen, created_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(strategy_id) DO UPDATE SET
                    helpfulness = helpfulness + 1,
                    last_seen = datetime('now')
            """, (strategy_id, project_id, topic, insight, lang, framework))
            conn.commit()

            self._print_success(f"✓ Saved strategy: {topic} for {project_id}")
            return {
                "success": True,
                "strategy_id": strategy_id,
                "project_id": project_id,
                "topic": topic
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save strategy: {str(e)}")
        finally:
            conn.close()

    def get_strategies(self, project_id: str, lang: Optional[str] = None,
                       framework: Optional[str] = None, topic: Optional[str] = None,
                       limit: int = 5) -> List[Dict]:
        """Query strategies table (T038).

        Args:
            project_id: Project identifier
            lang: Optional filter by language
            framework: Optional filter by framework
            topic: Optional filter by topic
            limit: Maximum strategies to return (default 5, clamped to 1-100)

        Returns:
            List of strategy records sorted by helpfulness
        """
        # Clamp limit to safe range (1-100)
        limit = max(1, min(limit, 100))

        # Validate topic if provided
        if topic and topic not in self.VALID_TOPICS:
            self._print_error(f"Invalid topic '{topic}'. Valid: {', '.join(self.VALID_TOPICS)}")
            return []

        conn = self._get_connection()
        try:
            sql = "SELECT * FROM strategies WHERE project_id = ?"
            params: List[Any] = [project_id]

            if lang:
                sql += " AND (lang IS NULL OR lang = ?)"
                params.append(lang)
            if framework:
                sql += " AND (framework IS NULL OR framework = ?)"
                params.append(framework)
            if topic:
                sql += " AND topic = ?"
                params.append(topic)

            sql += " ORDER BY helpfulness DESC, last_seen DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def update_strategy_helpfulness(self, strategy_id: str, increment: int = 1) -> Dict[str, Any]:
        """Increment strategy helpfulness counter (T038).

        Args:
            strategy_id: Strategy identifier
            increment: Amount to increment (default 1, clamped to 0-100)

        Returns:
            Dict with updated helpfulness value
        """
        # Validate increment (guard against negative/huge values)
        increment = max(0, min(increment, 100))

        conn = self._get_connection()
        try:
            # Atomic update (no read-modify-write race condition)
            cursor = conn.execute("""
                UPDATE strategies
                SET helpfulness = MAX(0, helpfulness + ?), last_seen = datetime('now')
                WHERE strategy_id = ?
            """, (increment, strategy_id))
            conn.commit()

            if cursor.rowcount == 0:
                return {"success": False, "error": "Strategy not found"}

            # Get the new value for reporting
            row = conn.execute(
                "SELECT helpfulness FROM strategies WHERE strategy_id = ?",
                (strategy_id,)
            ).fetchone()
            new_helpfulness = row['helpfulness'] if row else 0
            # Calculate previous from new (since we did atomic update)
            previous_helpfulness = max(0, new_helpfulness - increment)

            self._print_success(f"✓ Updated helpfulness: {previous_helpfulness} → {new_helpfulness}")
            return {
                "success": True,
                "strategy_id": strategy_id,
                "previous_helpfulness": previous_helpfulness,
                "new_helpfulness": new_helpfulness
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update helpfulness: {str(e)}")
        finally:
            conn.close()

    def extract_strategies(self, session_id: str, group_id: str, project_id: str,
                           lang: Optional[str] = None, framework: Optional[str] = None) -> Dict[str, Any]:
        """Extract strategies from agent_reasoning for successful task completion.

        Queries completion/decisions/approach phases and saves as strategies.

        Args:
            session_id: Session identifier
            group_id: Task group identifier
            project_id: Project identifier for strategy scoping
            lang: Optional language context
            framework: Optional framework context

        Returns:
            Dict with count of extracted strategies
        """
        import hashlib

        conn = self._get_connection()
        try:
            # Query reasoning for successful completion insights
            rows = conn.execute("""
                SELECT phase, content, agent_type FROM agent_reasoning
                WHERE session_id = ? AND group_id = ? AND phase IN ('completion', 'decisions', 'approach')
                ORDER BY created_at DESC LIMIT 5
            """, (session_id, group_id)).fetchall()

            extracted = 0
            topic_map = {'completion': 'implementation', 'decisions': 'architecture', 'approach': 'methodology'}

            for row in rows:
                phase, content, agent_type = row['phase'], row['content'], row['agent_type']
                topic = topic_map.get(phase, 'general')

                # Generate strategy_id matching save_strategy format
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                strategy_id = f"{project_id}_{topic}_{content_hash}"

                # Truncate insight to 500 chars
                insight = content[:500] if len(content) > 500 else content

                # Upsert strategy (increment helpfulness if exists)
                conn.execute("""
                    INSERT INTO strategies (strategy_id, project_id, topic, insight, helpfulness, lang, framework, last_seen, created_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'))
                    ON CONFLICT(strategy_id) DO UPDATE SET
                        helpfulness = helpfulness + 1,
                        last_seen = datetime('now')
                """, (strategy_id, project_id, topic, insight, lang, framework))
                extracted += 1

            conn.commit()
            self._print_success(f"✓ Extracted {extracted} strategies from group {group_id}")
            return {
                "success": True,
                "extracted_count": extracted,
                "session_id": session_id,
                "group_id": group_id,
                "project_id": project_id
            }
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to extract strategies: {str(e)}")
        finally:
            conn.close()

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
  get-session <id>                            Get session details by ID
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
                    [--specializations JSON] [--component-path PATH] [--initial_tier TIER]
                    [--item_count N] [--complexity N]
                                              Create task group with specializations, complexity (1-10), initial tier
  update-task-group <group_id> <session> [--status X] [--assigned_to Y] [--complexity N]
                    [--specializations JSON] [--component-path PATH] [--initial_tier TIER]
                    [--item_count N] [--revision_count N] [--security_sensitive 0|1]
                    [--qa_attempts N] [--tl_review_attempts N]
                                              Update task group fields
  get-task-groups <session> [status]          Get task groups (includes specializations, component_path, initial_tier, complexity)

TOKEN OPERATIONS:
  log-tokens <session> <agent> <tokens> [agent_id]
                                              Log token usage
  token-summary <session> [by]                Get token summary (default: by=agent_type)

SKILL OUTPUT OPERATIONS:
  save-skill-output <session> <skill> <json> [--agent X] [--group Y]
                                              Save skill output (iteration auto-computed)
  get-skill-output <session> <skill> [--agent X]
                                              Get latest skill output
  get-skill-output-all <session> <skill> [--agent X]
                                              Get all skill outputs (multi-invocation)

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

REASONING CAPTURE OPERATIONS:
  save-reasoning <session> <group_id> <agent_type> <phase> <content> [options]
                                              Save agent reasoning (auto-redacts secrets)
                                              Options: [--agent_id X] [--iteration N] [--confidence high|medium|low] [--references JSON]
                                              Phases: understanding, approach, decisions, risks, blockers, pivot, completion
  get-reasoning <session> [--group_id X] [--agent_type Y] [--phase Z] [--limit N]
                                              Get reasoning entries with optional filters (default: limit=50)
  reasoning-timeline <session> [--group_id X] [--format json|markdown]
                                              Get chronological reasoning timeline (default: format=json)
  check-mandatory-phases <session> <group_id> <agent_type>
                                              Check if mandatory phases (understanding, completion) are documented
                                              Returns exit code 1 if phases are missing

ERROR PATTERN OPERATIONS:
  save-error-pattern <project_id> <error_type> <error_message> <solution> [options]
                                              Capture error pattern from fail-then-succeed flow
                                              Options: [--lang X] [--context_hints JSON] [--stack_pattern JSON]
  get-error-patterns <project_id> [--lang X] [--min_confidence N] [--limit N]
                                              Query matching error patterns (default: min_confidence=0.7, limit=5)
  update-error-confidence <pattern_hash> <project_id> <success|failure>
                                              Adjust pattern confidence (+0.1 on success, -0.2 on failure)
  cleanup-error-patterns [project_id]         Remove patterns that have exceeded their TTL

CONSUMPTION SCOPE OPERATIONS (Context Engineering):
  save-consumption <session> <group_id> <agent_type> <iteration> <package_id>
                                              Save consumption record (iteration-aware tracking)
  get-consumption <session> [--group_id X] [--agent_type Y] [--limit N]
                                              Get consumption records (default: limit=50)

STRATEGIES OPERATIONS (Context Engineering):
  save-strategy <project_id> <topic> <insight> [options]
                                              Save strategy from successful task completion
                                              Options: [--lang X] [--framework Y] [--strategy_id Z]
                                              Topics: implementation, architecture, methodology, general
  get-strategies <project_id> [--lang X] [--framework Y] [--topic Z] [--limit N]
                                              Get strategies sorted by helpfulness (default: limit=5)
  update-strategy-helpfulness <strategy_id> [increment]
                                              Increment helpfulness counter (default: +1)
  extract-strategies <session> <group_id> <project_id> [--lang X] [--framework Y]
                                              Extract strategies from agent_reasoning after TL approval

QUERY OPERATIONS:
  query <sql>                                 Execute custom SELECT query
  dashboard-snapshot <session>                Get complete dashboard data

DATABASE MAINTENANCE:
  integrity-check                             Check database integrity
  recover-db                                  Attempt to recover corrupted database
  detect-paths                                Show auto-detected paths (debugging)

HELP:
  help                                        Show this help message

PATH RESOLUTION:
  The script auto-detects the database path. Override with:
  --db PATH           Explicit database path
  --project-root DIR  Project root (db at DIR/bazinga/bazinga.db)
  BAZINGA_ROOT env    Environment variable

Examples:
  bazinga_db.py list-sessions 5                                    # Auto-detect path
  bazinga_db.py --db bazinga.db list-sessions 5                    # Explicit path
  bazinga_db.py --project-root /path/to/project list-sessions 5    # Project root
  bazinga_db.py detect-paths                                       # Show detected paths
  bazinga_db.py query "SELECT * FROM sessions LIMIT 3"
  bazinga_db.py get-task-groups session123
"""
    print(help_text)


def _resolve_db_path(args) -> str:
    """Resolve the database path from arguments or auto-detection."""
    # 1. Explicit --db takes highest priority
    if args.db:
        return args.db

    # 2. Try auto-detection via bazinga_paths module
    if _HAS_BAZINGA_PATHS:
        try:
            db_path = get_db_path(
                override=args.db,
                project_root=Path(args.project_root) if args.project_root else None
            )
            return str(db_path)
        except RuntimeError as e:
            print(f"Error: Could not auto-detect database path: {e}", file=sys.stderr)
            print("Hint: Use --db to specify path explicitly, or ensure you're in a BAZINGA project.", file=sys.stderr)
            sys.exit(1)
    else:
        # Fallback: try to find db relative to script location
        script_dir = Path(__file__).parent.resolve()
        # Walk up to find project root
        current = script_dir
        for _ in range(10):  # Max 10 levels up
            candidate = current / 'bazinga' / 'bazinga.db'
            if (current / '.claude').exists() and (current / 'bazinga').exists():
                return str(candidate)
            if current.parent == current:
                break
            current = current.parent

        print("Error: --db is required (auto-detection unavailable)", file=sys.stderr)
        sys.exit(1)


def main():
    # Ensure we're in project root for relative path resolution
    _ensure_cwd_at_project_root()

    parser = argparse.ArgumentParser(
        description='BAZINGA Database Client',
        epilog='Run with "help" command to see all available commands'
    )
    parser.add_argument('--db', required=False, help='Database path (auto-detected if not provided)')
    parser.add_argument('--project-root', required=False, help='Project root directory (for auto-detection)')
    parser.add_argument('--quiet', action='store_true', help='Suppress success messages, only show errors')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Command arguments')

    args = parser.parse_args()

    # Handle detect-paths command before resolving db
    if args.command == 'detect-paths':
        if _HAS_BAZINGA_PATHS:
            info = get_detection_info()
            print(json.dumps(info, indent=2))
        else:
            print(json.dumps({"error": "bazinga_paths module not available"}, indent=2))
        sys.exit(0)

    # Resolve database path
    db_path = _resolve_db_path(args)
    db = BazingaDB(db_path, quiet=args.quiet)

    # Parse command and execute
    cmd = args.command
    cmd_args = args.args

    try:
        if cmd == 'create-session':
            # create-session <session_id> <mode> <requirements> [--initial_branch X] [--metadata JSON]
            if len(cmd_args) < 3:
                print("Error: create-session requires at least 3 args: <session_id> <mode> <requirements>", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            mode = cmd_args[1]
            requirements = cmd_args[2]
            initial_branch = None
            metadata = None
            # Parse optional flags
            i = 3
            while i < len(cmd_args):
                if cmd_args[i] == '--initial_branch' and i + 1 < len(cmd_args):
                    initial_branch = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--metadata' and i + 1 < len(cmd_args):
                    metadata = cmd_args[i + 1]
                    i += 2
                else:
                    print(f"Error: Unknown flag or missing value: {cmd_args[i]}", file=sys.stderr)
                    sys.exit(1)
            result = db.create_session(session_id, mode, requirements, initial_branch, metadata)
            # Output verification data as JSON
            print(json.dumps(result, indent=2))
        elif cmd == 'get-session':
            if len(cmd_args) < 1:
                print(json.dumps({"success": False, "error": "get-session requires <session_id>"}, indent=2), file=sys.stderr)
                sys.exit(1)
            session = db.get_session(cmd_args[0])
            if session:
                print(json.dumps(session, indent=2))
            else:
                print(json.dumps({"success": False, "error": f"Session not found: {cmd_args[0]}"}, indent=2), file=sys.stderr)
                sys.exit(1)
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
            # Parse --agent and --group flags
            agent_type = None
            group_id = None
            positional_args = []
            i = 0
            while i < len(cmd_args):
                if cmd_args[i] == '--agent' and i + 1 < len(cmd_args):
                    agent_type = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--group' and i + 1 < len(cmd_args):
                    group_id = cmd_args[i + 1]
                    i += 2
                else:
                    positional_args.append(cmd_args[i])
                    i += 1
            # Validate required arguments
            if len(positional_args) < 3:
                print(json.dumps({
                    "success": False,
                    "error": "save-skill-output requires <session_id> <skill_name> <output_json> [--agent <type>] [--group <id>]"
                }, indent=2), file=sys.stderr)
                sys.exit(1)
            session_id = positional_args[0]
            skill_name = positional_args[1]
            try:
                output_data = json.loads(positional_args[2])
            except json.JSONDecodeError as e:
                print(json.dumps({"success": False, "error": f"Invalid JSON in output_data: {e}"}, indent=2), file=sys.stderr)
                sys.exit(1)
            iteration = db.save_skill_output(session_id, skill_name, output_data, agent_type, group_id)
            if not args.quiet:
                print(json.dumps({"iteration": iteration}))
        elif cmd == 'get-skill-output':
            # Parse --agent flag
            agent_type = None
            positional_args = []
            i = 0
            while i < len(cmd_args):
                if cmd_args[i] == '--agent' and i + 1 < len(cmd_args):
                    agent_type = cmd_args[i + 1]
                    i += 2
                else:
                    positional_args.append(cmd_args[i])
                    i += 1
            # Validate required arguments
            if len(positional_args) < 2:
                print(json.dumps({
                    "success": False,
                    "error": "get-skill-output requires <session_id> <skill_name> [--agent <type>]"
                }, indent=2), file=sys.stderr)
                sys.exit(1)
            session_id = positional_args[0]
            skill_name = positional_args[1]
            result = db.get_skill_output(session_id, skill_name, agent_type)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-skill-output-all':
            # Parse --agent flag
            agent_type = None
            positional_args = []
            i = 0
            while i < len(cmd_args):
                if cmd_args[i] == '--agent' and i + 1 < len(cmd_args):
                    agent_type = cmd_args[i + 1]
                    i += 2
                else:
                    positional_args.append(cmd_args[i])
                    i += 1
            # Validate required arguments
            if len(positional_args) < 2:
                print(json.dumps({
                    "success": False,
                    "error": "get-skill-output-all requires <session_id> <skill_name> [--agent <type>]"
                }, indent=2), file=sys.stderr)
                sys.exit(1)
            session_id = positional_args[0]
            skill_name = positional_args[1]
            result = db.get_skill_output_all(session_id, skill_name, agent_type)
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
            # Parse --specializations, --item_count, --component-path, --initial_tier, --complexity flags first, then extract positional args
            specializations = None
            item_count = None
            component_path = None
            initial_tier = None
            complexity = None
            positional_args = []
            i = 0
            while i < len(cmd_args):
                arg = cmd_args[i]
                # Normalize dashes to underscores in flag NAME only (preserve leading --)
                # e.g., '--item-count' -> '--item_count', '--component-path' -> '--component_path'
                if arg.startswith('--'):
                    arg_normalized = '--' + arg[2:].replace('-', '_')
                else:
                    arg_normalized = arg
                if arg_normalized == '--specializations' and i + 1 < len(cmd_args):
                    try:
                        specializations = json.loads(cmd_args[i + 1])
                        if not isinstance(specializations, list):
                            print(json.dumps({"success": False, "error": "--specializations must be a JSON array"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                        if not all(isinstance(s, str) for s in specializations):
                            print(json.dumps({"success": False, "error": "--specializations array must contain only strings"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                    except json.JSONDecodeError as e:
                        print(json.dumps({"success": False, "error": f"Invalid JSON for --specializations: {e}"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                    i += 2  # Skip flag and value
                elif arg_normalized == '--item_count' and i + 1 < len(cmd_args):
                    try:
                        item_count = int(cmd_args[i + 1])
                        if item_count < 1:
                            print(json.dumps({"success": False, "error": "--item_count must be a positive integer"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                    except ValueError:
                        print(json.dumps({"success": False, "error": "--item_count must be a valid integer"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                    i += 2  # Skip flag and value
                elif arg_normalized == '--component_path' and i + 1 < len(cmd_args):
                    component_path = cmd_args[i + 1]
                    i += 2  # Skip flag and value
                elif arg_normalized == '--initial_tier' and i + 1 < len(cmd_args):
                    initial_tier = cmd_args[i + 1]
                    valid_tiers = ('Developer', 'Senior Software Engineer')
                    if initial_tier not in valid_tiers:
                        print(json.dumps({"success": False, "error": f"--initial_tier must be one of {valid_tiers}, got '{initial_tier}'"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                    i += 2  # Skip flag and value
                elif arg_normalized == '--complexity' and i + 1 < len(cmd_args):
                    try:
                        complexity = int(cmd_args[i + 1])
                        if not 1 <= complexity <= 10:
                            print(json.dumps({"success": False, "error": "--complexity must be between 1 and 10"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                    except ValueError:
                        print(json.dumps({"success": False, "error": "--complexity must be a valid integer"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                    i += 2  # Skip flag and value
                else:
                    positional_args.append(cmd_args[i])
                    i += 1
            # Validate positional args count (required: group_id, session_id, name)
            if len(positional_args) < 3:
                print(json.dumps({"success": False, "error": "create-task-group requires at least 3 args: <group_id> <session_id> <name>"}, indent=2), file=sys.stderr)
                sys.exit(1)
            if len(positional_args) > 5:
                print(json.dumps({"success": False, "error": "create-task-group accepts at most 5 positional args: <group_id> <session_id> <name> [status] [assigned_to]"}, indent=2), file=sys.stderr)
                sys.exit(1)
            # Now assign positional args correctly
            group_id = positional_args[0]
            session_id = positional_args[1]
            name = positional_args[2]
            # Default to None so upsert preserves existing status; INSERT defaults to 'pending'
            status = positional_args[3] if len(positional_args) > 3 else None
            assigned_to = positional_args[4] if len(positional_args) > 4 else None
            result = db.create_task_group(group_id, session_id, name, status, assigned_to, specializations, item_count, component_path, initial_tier, complexity)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-task-group':
            # Validate minimum args
            if len(cmd_args) < 2:
                print(json.dumps({"success": False, "error": "update-task-group requires at least 2 args: <group_id> <session_id>"}, indent=2), file=sys.stderr)
                sys.exit(1)
            group_id = cmd_args[0]
            session_id = cmd_args[1]
            kwargs = {}
            # Allowlist of valid flags
            # v14: Added security_sensitive, qa_attempts, tl_review_attempts for escalation tracking
            # v15: Added component_path for version-specific prompt building
            # v16: Added initial_tier for PM-assigned starting tier
            # v17: Added complexity for PM-assigned task complexity scoring (1-10)
            valid_flags = {"status", "assigned_to", "revision_count", "last_review_status", "auto_create", "name", "specializations", "item_count", "security_sensitive", "qa_attempts", "tl_review_attempts", "component_path", "initial_tier", "complexity"}
            for i in range(2, len(cmd_args), 2):
                key = cmd_args[i].lstrip('--')
                key = key.replace('-', '_')  # Normalize dashes to underscores (--assigned-to → assigned_to)
                # Validate flag is in allowlist
                if key not in valid_flags:
                    print(json.dumps({"success": False, "error": f"Unknown flag --{key}. Valid flags: {', '.join(sorted(valid_flags))}"}, indent=2), file=sys.stderr)
                    sys.exit(1)
                if i + 1 >= len(cmd_args):
                    print(json.dumps({"success": False, "error": f"Missing value for --{key}"}, indent=2), file=sys.stderr)
                    sys.exit(1)
                value = cmd_args[i + 1]
                # Convert integer flags
                if key in ('revision_count', 'item_count', 'qa_attempts', 'tl_review_attempts', 'complexity'):
                    try:
                        value = int(value)
                        # Validate complexity range
                        if key == 'complexity' and not 1 <= value <= 10:
                            print(json.dumps({"success": False, "error": "--complexity must be between 1 and 10"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                    except ValueError:
                        print(json.dumps({"success": False, "error": f"--{key} must be an integer, got: {value}"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                # Convert security_sensitive to int (0 or 1)
                elif key == 'security_sensitive':
                    value = 1 if value.lower() in ('true', '1', 'yes') else 0
                # Convert auto_create to bool
                elif key == 'auto_create':
                    value = value.lower() in ('true', '1', 'yes')
                # Parse and validate specializations JSON
                elif key == 'specializations':
                    try:
                        value = json.loads(value)
                        # Validate it's a list of strings
                        if not isinstance(value, list):
                            print(json.dumps({"success": False, "error": "--specializations must be a JSON array"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                        if not all(isinstance(s, str) for s in value):
                            print(json.dumps({"success": False, "error": "--specializations array must contain only strings"}, indent=2), file=sys.stderr)
                            sys.exit(1)
                    except json.JSONDecodeError as e:
                        print(json.dumps({"success": False, "error": f"Invalid JSON for --specializations: {e}"}, indent=2), file=sys.stderr)
                        sys.exit(1)
                # Validate initial_tier
                elif key == 'initial_tier':
                    valid_tiers = ('Developer', 'Senior Software Engineer')
                    if value not in valid_tiers:
                        print(json.dumps({"success": False, "error": f"--initial_tier must be one of {valid_tiers}, got '{value}'"}, indent=2), file=sys.stderr)
                        sys.exit(1)
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
        elif cmd == 'save-reasoning':
            # Parse positional and optional args
            # Required: session_id, group_id, agent_type, phase, content (or --content-file)
            # Optional: --agent_id, --iteration, --confidence, --references, --content-file
            valid_flags = {'--agent_id', '--iteration', '--confidence', '--references', '--content-file'}

            if len(cmd_args) < 4:
                print("Error: save-reasoning requires: <session_id> <group_id> <agent_type> <phase> <content>", file=sys.stderr)
                print("       Or use --content-file to read content from a file", file=sys.stderr)
                sys.exit(1)

            session_id = cmd_args[0]
            group_id = cmd_args[1]
            agent_type = cmd_args[2]
            phase = cmd_args[3]

            # Check if content is provided positionally or via --content-file
            content = None
            kwargs = {}
            i = 4

            # If 5th arg exists and doesn't start with --, it's the content
            if len(cmd_args) > 4 and not cmd_args[4].startswith('--'):
                content = cmd_args[4]
                i = 5

            # Parse optional flags
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg.startswith('--'):
                    if arg not in valid_flags:
                        print(f"Error: Unknown flag '{arg}'. Valid flags: {sorted(valid_flags)}", file=sys.stderr)
                        sys.exit(1)
                    if i + 1 >= len(cmd_args):
                        print(f"Error: Flag '{arg}' requires a value", file=sys.stderr)
                        sys.exit(1)
                    key = arg.lstrip('--')
                    value = cmd_args[i + 1]
                    if key == 'iteration':
                        try:
                            value = int(value)
                        except ValueError:
                            print(f"Error: --iteration must be an integer, got '{value}'", file=sys.stderr)
                            sys.exit(1)
                    elif key == 'references':
                        try:
                            value = json.loads(value)
                            if not isinstance(value, list):
                                raise ValueError("references must be a JSON array")
                        except json.JSONDecodeError as e:
                            print(f"Error: Invalid JSON for --references: {e}", file=sys.stderr)
                            sys.exit(1)
                    elif key == 'content-file':
                        # Read content from file (avoids shell escaping and process table exposure)
                        try:
                            content = Path(value).read_text()
                        except Exception as e:
                            print(f"Error: Could not read content file '{value}': {e}", file=sys.stderr)
                            sys.exit(1)
                        i += 2
                        continue  # Don't add to kwargs
                    kwargs[key] = value
                    i += 2
                else:
                    # Unexpected positional argument - fail fast
                    print(f"Error: Unexpected argument '{arg}' after positional args.", file=sys.stderr)
                    print("Usage: save-reasoning <session_id> <group_id> <agent_type> <phase> [<content>] [--content-file FILE] [--agent_id X] [--iteration N] [--confidence X] [--references JSON]", file=sys.stderr)
                    sys.exit(1)

            # Validate content was provided
            if content is None:
                print("Error: Content is required. Provide as 5th argument or use --content-file FILE", file=sys.stderr)
                sys.exit(1)

            try:
                result = db.save_reasoning(session_id, group_id, agent_type, phase, content, **kwargs)
                print(json.dumps(result, indent=2))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif cmd == 'get-reasoning':
            # Required: session_id
            # Optional: --group_id, --agent_type, --phase, --limit, --format
            if len(cmd_args) < 1:
                print("Error: get-reasoning requires at least 1 arg: <session_id>", file=sys.stderr)
                sys.exit(1)

            session_id = cmd_args[0]
            kwargs = {}
            output_format = 'json'
            valid_flags = {'--group_id', '--agent_type', '--phase', '--limit', '--format'}
            i = 1
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg.startswith('--'):
                    if arg not in valid_flags:
                        print(f"Error: Unknown flag '{arg}'. Valid flags: {sorted(valid_flags)}", file=sys.stderr)
                        sys.exit(1)
                    if i + 1 >= len(cmd_args):
                        print(f"Error: Flag '{arg}' requires a value", file=sys.stderr)
                        sys.exit(1)
                    key = arg.lstrip('--')
                    value = cmd_args[i + 1]
                    if key == 'limit':
                        try:
                            value = int(value)
                        except ValueError:
                            print(f"Error: --limit must be an integer, got '{value}'", file=sys.stderr)
                            sys.exit(1)
                    elif key == 'format':
                        if value not in ('json', 'prompt-summary'):
                            print(f"Error: --format must be 'json' or 'prompt-summary', got '{value}'", file=sys.stderr)
                            sys.exit(1)
                        output_format = value
                        i += 2
                        continue  # Don't add to kwargs
                    kwargs[key] = value
                    i += 2
                else:
                    # Unexpected positional argument - fail fast
                    print(f"Error: Unexpected argument '{arg}'. Use --flag syntax for options.", file=sys.stderr)
                    print(f"Usage: get-reasoning <session_id> [--group_id X] [--agent_type X] [--phase X] [--limit N] [--format json|prompt-summary]", file=sys.stderr)
                    sys.exit(1)

            try:
                result = db.get_reasoning(session_id, output_format=output_format, **kwargs)
                if output_format == 'prompt-summary':
                    print(result)  # Already formatted string
                else:
                    print(json.dumps(result, indent=2))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif cmd == 'reasoning-timeline':
            # Required: session_id
            # Optional: --group_id, --format
            if len(cmd_args) < 1:
                print("Error: reasoning-timeline requires at least 1 arg: <session_id>", file=sys.stderr)
                sys.exit(1)

            session_id = cmd_args[0]
            group_id = None
            fmt = 'json'
            valid_flags = {'--group_id', '--format'}

            i = 1
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg == '--group_id':
                    if i + 1 >= len(cmd_args):
                        print("Error: --group_id requires a value", file=sys.stderr)
                        sys.exit(1)
                    group_id = cmd_args[i + 1]
                    i += 2
                elif arg == '--format':
                    if i + 1 >= len(cmd_args):
                        print("Error: --format requires a value", file=sys.stderr)
                        sys.exit(1)
                    fmt = cmd_args[i + 1]
                    if fmt not in ('json', 'markdown'):
                        print(f"Error: --format must be 'json' or 'markdown', got '{fmt}'", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg.startswith('--'):
                    print(f"Error: Unknown flag '{arg}'. Valid flags: {sorted(valid_flags)}", file=sys.stderr)
                    sys.exit(1)
                else:
                    # Unexpected positional argument - fail fast
                    print(f"Error: Unexpected argument '{arg}'. Use --flag syntax for options.", file=sys.stderr)
                    print(f"Usage: reasoning-timeline <session_id> [--group_id X] [--format json|markdown]", file=sys.stderr)
                    sys.exit(1)

            result = db.reasoning_timeline(session_id, group_id=group_id, output_format=fmt)
            print(result)
        elif cmd == 'check-mandatory-phases':
            # Required: session_id, group_id, agent_type
            if len(cmd_args) < 3:
                print("Error: check-mandatory-phases requires 3 args: <session_id> <group_id> <agent_type>", file=sys.stderr)
                sys.exit(1)

            session_id = cmd_args[0]
            group_id = cmd_args[1]
            agent_type = cmd_args[2]

            result = db.check_mandatory_phases(session_id, group_id, agent_type)
            print(json.dumps(result, indent=2))

            # Exit with error code if mandatory phases are missing
            if not result['complete']:
                sys.exit(1)
        # ==================== ERROR PATTERN COMMANDS ====================
        elif cmd == 'save-error-pattern':
            # save-error-pattern <project_id> <error_type> <error_message> <solution> [--lang X] [--context_hints JSON] [--stack_pattern JSON]
            if len(cmd_args) < 4:
                print("Error: save-error-pattern requires 4 args: <project_id> <error_type> <error_message> <solution>", file=sys.stderr)
                sys.exit(1)

            project_id = cmd_args[0]
            error_type = cmd_args[1]
            error_message = cmd_args[2]
            solution = cmd_args[3]

            # Parse optional flags
            lang = None
            context_hints = None
            stack_pattern = None
            valid_flags = {'--lang', '--context_hints', '--stack_pattern'}
            i = 4
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg == '--lang' and i + 1 < len(cmd_args):
                    lang = cmd_args[i + 1]
                    i += 2
                elif arg == '--context_hints' and i + 1 < len(cmd_args):
                    try:
                        context_hints = json.loads(cmd_args[i + 1])
                        if not isinstance(context_hints, list):
                            raise ValueError("context_hints must be a JSON array")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Error: Invalid JSON for --context_hints: {e}", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg == '--stack_pattern' and i + 1 < len(cmd_args):
                    try:
                        stack_pattern = json.loads(cmd_args[i + 1])
                        if not isinstance(stack_pattern, list):
                            raise ValueError("stack_pattern must be a JSON array")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Error: Invalid JSON for --stack_pattern: {e}", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg.startswith('--'):
                    print(f"Error: Unknown flag '{arg}'. Valid flags: {sorted(valid_flags)}", file=sys.stderr)
                    sys.exit(1)
                else:
                    print(f"Error: Unexpected argument '{arg}'", file=sys.stderr)
                    sys.exit(1)

            result = db.save_error_pattern(project_id, error_type, error_message, solution,
                                          lang=lang, context_hints=context_hints,
                                          stack_pattern=stack_pattern)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-error-patterns':
            # get-error-patterns <project_id> [--lang X] [--min_confidence N] [--limit N]
            if len(cmd_args) < 1:
                print("Error: get-error-patterns requires at least 1 arg: <project_id>", file=sys.stderr)
                sys.exit(1)

            project_id = cmd_args[0]
            lang = None
            min_confidence = 0.7
            limit = 5
            valid_flags = {'--lang', '--min_confidence', '--limit'}
            i = 1
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg == '--lang' and i + 1 < len(cmd_args):
                    lang = cmd_args[i + 1]
                    i += 2
                elif arg == '--min_confidence' and i + 1 < len(cmd_args):
                    try:
                        min_confidence = float(cmd_args[i + 1])
                    except ValueError:
                        print(f"Error: --min_confidence must be a number", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg == '--limit' and i + 1 < len(cmd_args):
                    try:
                        limit = int(cmd_args[i + 1])
                    except ValueError:
                        print(f"Error: --limit must be an integer", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg.startswith('--'):
                    print(f"Error: Unknown flag '{arg}'. Valid flags: {sorted(valid_flags)}", file=sys.stderr)
                    sys.exit(1)
                else:
                    print(f"Error: Unexpected argument '{arg}'", file=sys.stderr)
                    sys.exit(1)

            result = db.get_error_patterns(project_id, lang=lang, min_confidence=min_confidence, limit=limit)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-error-confidence':
            # update-error-confidence <pattern_hash> <project_id> <success|failure>
            if len(cmd_args) < 3:
                print("Error: update-error-confidence requires 3 args: <pattern_hash> <project_id> <success|failure>", file=sys.stderr)
                sys.exit(1)

            pattern_hash = cmd_args[0]
            project_id = cmd_args[1]
            outcome = cmd_args[2].lower()
            if outcome not in ('success', 'failure'):
                print(f"Error: Outcome must be 'success' or 'failure', got '{outcome}'", file=sys.stderr)
                sys.exit(1)

            result = db.update_error_pattern_confidence(pattern_hash, project_id, success=(outcome == 'success'))
            print(json.dumps(result, indent=2))
        elif cmd == 'cleanup-error-patterns':
            # cleanup-error-patterns [project_id]
            project_id = cmd_args[0] if len(cmd_args) > 0 else None
            result = db.cleanup_expired_patterns(project_id)
            print(json.dumps(result, indent=2))

        # ==================== CONSUMPTION SCOPE COMMANDS ====================
        elif cmd == 'save-consumption':
            # save-consumption <session> <group_id> <agent_type> <iteration> <package_id>
            if len(cmd_args) < 5:
                print("Error: save-consumption requires: <session> <group_id> <agent_type> <iteration> <package_id>", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            group_id = cmd_args[1]
            agent_type = cmd_args[2]
            iteration = int(cmd_args[3])
            package_id = int(cmd_args[4])
            result = db.save_consumption(session_id, group_id, agent_type, iteration, package_id)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-consumption':
            # get-consumption <session> [--group_id X] [--agent_type Y] [--limit N]
            if len(cmd_args) < 1:
                print("Error: get-consumption requires: <session>", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            group_id = None
            agent_type = None
            limit = 50
            i = 1
            while i < len(cmd_args):
                if cmd_args[i] == '--group_id' and i + 1 < len(cmd_args):
                    group_id = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--agent_type' and i + 1 < len(cmd_args):
                    agent_type = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--limit' and i + 1 < len(cmd_args):
                    limit = int(cmd_args[i + 1])
                    i += 2
                else:
                    i += 1
            result = db.get_consumption(session_id, group_id, agent_type, limit)
            print(json.dumps(result, indent=2))

        # ==================== STRATEGIES COMMANDS ====================
        elif cmd == 'save-strategy':
            # save-strategy <project_id> <topic> <insight> [--lang X] [--framework Y] [--strategy_id Z]
            if len(cmd_args) < 3:
                print("Error: save-strategy requires: <project_id> <topic> <insight>", file=sys.stderr)
                sys.exit(1)
            project_id = cmd_args[0]
            topic = cmd_args[1]
            insight = cmd_args[2]
            lang = None
            framework = None
            strategy_id = None
            i = 3
            while i < len(cmd_args):
                if cmd_args[i] == '--lang' and i + 1 < len(cmd_args):
                    lang = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--framework' and i + 1 < len(cmd_args):
                    framework = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--strategy_id' and i + 1 < len(cmd_args):
                    strategy_id = cmd_args[i + 1]
                    i += 2
                else:
                    i += 1
            result = db.save_strategy(project_id, topic, insight, lang, framework, strategy_id)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-strategies':
            # get-strategies <project_id> [--lang X] [--framework Y] [--topic Z] [--limit N]
            if len(cmd_args) < 1:
                print("Error: get-strategies requires: <project_id>", file=sys.stderr)
                sys.exit(1)
            project_id = cmd_args[0]
            lang = None
            framework = None
            topic = None
            limit = 5
            i = 1
            while i < len(cmd_args):
                if cmd_args[i] == '--lang' and i + 1 < len(cmd_args):
                    lang = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--framework' and i + 1 < len(cmd_args):
                    framework = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--topic' and i + 1 < len(cmd_args):
                    topic = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--limit' and i + 1 < len(cmd_args):
                    limit = int(cmd_args[i + 1])
                    i += 2
                else:
                    i += 1
            result = db.get_strategies(project_id, lang, framework, topic, limit)
            print(json.dumps(result, indent=2))
        elif cmd == 'update-strategy-helpfulness':
            # update-strategy-helpfulness <strategy_id> [increment]
            if len(cmd_args) < 1:
                print("Error: update-strategy-helpfulness requires: <strategy_id>", file=sys.stderr)
                sys.exit(1)
            strategy_id = cmd_args[0]
            increment = int(cmd_args[1]) if len(cmd_args) > 1 else 1
            result = db.update_strategy_helpfulness(strategy_id, increment)
            print(json.dumps(result, indent=2))
        elif cmd == 'extract-strategies':
            # extract-strategies <session> <group_id> <project_id> [--lang X] [--framework Y]
            if len(cmd_args) < 3:
                print("Error: extract-strategies requires: <session> <group_id> <project_id>", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            group_id = cmd_args[1]
            project_id = cmd_args[2]
            lang = None
            framework = None
            i = 3
            while i < len(cmd_args):
                if cmd_args[i] == '--lang' and i + 1 < len(cmd_args):
                    lang = cmd_args[i + 1]
                    i += 2
                elif cmd_args[i] == '--framework' and i + 1 < len(cmd_args):
                    framework = cmd_args[i + 1]
                    i += 2
                else:
                    i += 1
            result = db.extract_strategies(session_id, group_id, project_id, lang, framework)
            print(json.dumps(result, indent=2))

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
        elif cmd == 'save-event':
            # save-event <session_id> <event_subtype> <payload>
            if len(cmd_args) < 3:
                print("Error: save-event requires 3 args: <session_id> <event_subtype> <payload>", file=sys.stderr)
                print("  event_subtype: pm_bazinga, scope_change, validator_verdict", file=sys.stderr)
                print("  payload: JSON string", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            event_subtype = cmd_args[1]
            payload = cmd_args[2]
            result = db.save_event(session_id, event_subtype, payload)
            print(json.dumps(result, indent=2))
        elif cmd == 'get-events':
            # get-events <session_id> [event_subtype] [limit]
            # Also supports: get-events <session_id> [event_subtype] --limit N
            if len(cmd_args) < 1:
                print("Error: get-events requires at least 1 arg: <session_id> [event_subtype] [limit]", file=sys.stderr)
                print("  Examples:", file=sys.stderr)
                print("    get-events sess_123                    # all events, limit 50", file=sys.stderr)
                print("    get-events sess_123 pm_bazinga         # filter by subtype", file=sys.stderr)
                print("    get-events sess_123 pm_bazinga 1       # with limit", file=sys.stderr)
                sys.exit(1)
            session_id = cmd_args[0]
            event_subtype = None
            limit = 50

            # Parse remaining args, handling --limit flag
            i = 1
            while i < len(cmd_args):
                arg = cmd_args[i]
                if arg == '--limit' and i + 1 < len(cmd_args):
                    try:
                        limit = int(cmd_args[i + 1])
                    except ValueError:
                        print(f"Error: --limit requires integer, got '{cmd_args[i + 1]}'", file=sys.stderr)
                        sys.exit(1)
                    i += 2
                elif arg.startswith('--'):
                    print(f"Error: Unknown flag '{arg}'", file=sys.stderr)
                    sys.exit(1)
                elif event_subtype is None:
                    event_subtype = arg
                    i += 1
                else:
                    # Positional limit
                    try:
                        limit = int(arg)
                    except ValueError:
                        print(f"Error: Invalid limit '{arg}' - must be integer", file=sys.stderr)
                        sys.exit(1)
                    i += 1

            result = db.get_events(session_id, event_subtype, limit)
            print(json.dumps(result, indent=2))
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
