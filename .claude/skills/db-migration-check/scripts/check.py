#!/usr/bin/env python3
"""
Database Migration Check Skill - Main Script

Detects dangerous operations in database migrations.

Usage:
    python check.py

Output:
    bazinga/artifacts/{SESSION_ID}/skills/db_migration_check.json
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add _shared directory to path for bazinga_paths import
# Assumes structure: .claude/skills/<skill_name>/scripts/<script>.py
# _shared is at: .claude/skills/_shared/
_script_dir = Path(__file__).parent.resolve()
_shared_dir = _script_dir.parent.parent / '_shared'
if _shared_dir.exists() and str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

try:
    from bazinga_paths import get_db_path, get_artifacts_dir
    _HAS_BAZINGA_PATHS = True
except ImportError:
    _HAS_BAZINGA_PATHS = False

def _get_db_path_safe() -> str:
    """Get database path with fallback for backward compatibility."""
    if _HAS_BAZINGA_PATHS:
        try:
            return str(get_db_path())
        except RuntimeError:
            pass
    return "bazinga/bazinga.db"

# Get current session ID from database
def get_current_session_id():
    """Get the most recent session ID from the database."""
    db_path = _get_db_path_safe()
    if not os.path.exists(db_path):
        return "bazinga_default"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return "bazinga_default"
    except:
        return "bazinga_default"

SESSION_ID = get_current_session_id()

# Use bazinga_paths for output directory if available
if _HAS_BAZINGA_PATHS:
    try:
        OUTPUT_DIR = get_artifacts_dir(session_id=SESSION_ID) / "skills"
    except RuntimeError:
        OUTPUT_DIR = Path(f"bazinga/artifacts/{SESSION_ID}/skills")
else:
    OUTPUT_DIR = Path(f"bazinga/artifacts/{SESSION_ID}/skills")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "db_migration_check.json"

print(f"📁 Output directory: {OUTPUT_DIR}")

# Load profile for graceful degradation
def load_profile():
    """Load profile from skills_config.json"""
    try:
        with open("bazinga/skills_config.json", "r") as f:
            config = json.load(f)
            return config.get("_metadata", {}).get("profile", "lite")
    except:
        return "lite"

PROFILE = load_profile()

try:
    from parsers import find_migrations, parse_migration_file
    from detectors import detect_dangerous_operations
    from frameworks import detect_database_and_framework
except ImportError as e:
    # Graceful degradation if modules can't be imported
    if PROFILE == "lite":
        # Lite mode: Skip gracefully
        print(f"⚠️  Module import failed - database migration check skipped in lite mode")
        print(f"   Error: {e}")
        output = {
            "status": "skipped",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "impact": "Database migration safety check was skipped. Review migrations manually before deploying.",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)
        sys.exit(0)
    else:
        # Advanced mode: Fail
        print(f"❌ Required modules not found: {e}")
        output = {
            "status": "error",
            "reason": f"Module import failed: {e}",
            "recommendation": "Check that all skill modules are present",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)
        sys.exit(1)


def check_migrations() -> Dict[str, Any]:
    """
    Main migration check function.

    Returns:
        Check results as dictionary
    """
    print("🔍 Database Migration Safety Check")
    print("=" * 50)

    # Step 1: Detect database and framework
    print("\n📊 Detecting database and migration framework...")
    db_info = detect_database_and_framework()

    if not db_info:
        return {
            "status": "no_database_detected",
            "message": "Could not detect database or migration framework",
            "recommendation": "Ensure database config files exist (alembic.ini, manage.py, etc.)"
        }

    db_type = db_info['database']
    framework = db_info['framework']

    print(f"   Database: {db_type}")
    print(f"   Framework: {framework}")

    # Step 2: Find migration files
    print("\n📁 Finding migration files...")
    migration_files = find_migrations(framework)

    if not migration_files:
        return {
            "status": "no_migrations_found",
            "database": db_type,
            "framework": framework,
            "message": "No pending migrations found",
            "recommendation": "This is normal if no schema changes are in the current changeset"
        }

    print(f"   Found {len(migration_files)} migration file(s):")
    for mf in migration_files[:5]:  # Show first 5
        print(f"     - {mf}")
    if len(migration_files) > 5:
        print(f"     ... and {len(migration_files) - 5} more")

    # Step 3: Parse and analyze migrations
    print("\n🔎 Analyzing migrations for dangerous operations...")

    all_dangerous_ops = []
    all_warnings = []
    all_safe_ops = []

    for migration_file in migration_files:
        # Parse migration file
        operations = parse_migration_file(migration_file, framework, db_type)

        if not operations:
            continue

        # Detect dangerous operations
        for operation in operations:
            result = detect_dangerous_operations(operation, db_type)

            operation_info = {
                "migration_file": migration_file,
                "line": operation.get('line', 0),
                "operation": operation.get('sql') or operation.get('operation'),
                **result
            }

            if result['severity'] in ['critical', 'high']:
                all_dangerous_ops.append(operation_info)
            elif result['severity'] == 'medium':
                all_warnings.append(operation_info)
            else:
                all_safe_ops.append(operation_info)

    print(f"   Dangerous operations: {len(all_dangerous_ops)}")
    print(f"   Warnings: {len(all_warnings)}")
    print(f"   Safe operations: {len(all_safe_ops)}")

    # Step 4: Generate recommendations
    print("\n💡 Generating recommendations...")
    recommendations = generate_recommendations(all_dangerous_ops, db_type)

    # Build result
    result = {
        "status": "dangerous_operations_detected" if all_dangerous_ops else "safe_migrations",
        "database": db_type,
        "migration_framework": framework,
        "migrations_analyzed": len(migration_files),
        "dangerous_operations": all_dangerous_ops,
        "warnings": all_warnings,
        "safe_migrations": [
            {
                "migration_file": op['migration_file'],
                "operation": op['operation'],
                "reason": op.get('reason', 'Operation is safe')
            }
            for op in all_safe_ops
        ],
        "recommendations": recommendations
    }

    return result


def generate_recommendations(dangerous_ops: List[Dict], db_type: str) -> List[str]:
    """Generate recommendations based on dangerous operations."""
    recommendations = []

    if not dangerous_ops:
        return ["All migrations appear safe for deployment"]

    # General recommendations
    recommendations.append(
        "CRITICAL: Review dangerous operations before deploying to production"
    )

    if db_type == "postgresql":
        if any('ADD COLUMN' in op.get('operation', '').upper() and 'DEFAULT' in op.get('operation', '').upper() for op in dangerous_ops):
            recommendations.append(
                "PostgreSQL: Use three-step migration for adding columns with defaults (add NULL, backfill, set default)"
            )

        if any('CREATE INDEX' in op.get('operation', '').upper() and 'CONCURRENTLY' not in op.get('operation', '').upper() for op in dangerous_ops):
            recommendations.append(
                "PostgreSQL: Create indexes with CONCURRENTLY to avoid blocking writes"
            )

    elif db_type == "mysql":
        if any('ALTER TABLE' in op.get('operation', '').upper() for op in dangerous_ops):
            recommendations.append(
                "MySQL: Consider using pt-online-schema-change for large tables to avoid downtime"
            )

    elif db_type == "mongodb":
        if any('createIndex' in op.get('operation', '') for op in dangerous_ops):
            recommendations.append(
                "MongoDB: Use background:true option for index creation on large collections"
            )

    elif db_type == "oracle":
        recommendations.append(
            "Oracle: Schedule DDL operations during maintenance windows to minimize lock contention"
        )

    # Add specific recommendations
    recommendations.append(
        "Test migrations on production-sized dataset in staging environment"
    )

    recommendations.append(
        "Monitor database locks during migration deployment"
    )

    return recommendations


def main():
    """Main entry point."""
    # Run check
    result = check_migrations()

    # Write output to session artifacts directory
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ Check complete!")
    print(f"📄 Results: {OUTPUT_FILE}")

    # Print summary
    status = result.get('status')
    if status == 'no_database_detected':
        print(f"\n❌ Status: No database detected")
    elif status == 'no_migrations_found':
        print(f"\n✅ Status: No migrations to check")
    elif status == 'dangerous_operations_detected':
        print(f"\n⚠️  Status: DANGEROUS OPERATIONS DETECTED")
        print(f"   - Critical/High: {len(result.get('dangerous_operations', []))}")
        print(f"   - Warnings: {len(result.get('warnings', []))}")
        print(f"\n💡 Top recommendation:")
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"   {recommendations[0]}")
    elif status == 'safe_migrations':
        print(f"\n✅ Status: All migrations appear safe")
        print(f"   - Safe operations: {len(result.get('safe_migrations', []))}")

    # Exit with error code if dangerous operations
    if status == 'dangerous_operations_detected':
        sys.exit(1)


if __name__ == "__main__":
    main()
