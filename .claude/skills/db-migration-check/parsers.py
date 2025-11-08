#!/usr/bin/env python3
"""
Migration File Parsers

Finds and parses migration files from different frameworks.
"""

import os
import re
import glob
from typing import List, Dict, Any


def find_migrations(framework: str) -> List[str]:
    """
    Find migration files for given framework.

    Args:
        framework: Migration framework name

    Returns:
        List of migration file paths
    """
    migration_patterns = {
        "alembic": "alembic/versions/*.py",
        "django": "*/migrations/*.py",
        "flyway": "db/migration/*.sql",
        "liquibase": "db/changelog/*.xml",
        "mongoose": "migrations/*.js",
        "activerecord": "db/migrate/*.rb"
    }

    pattern = migration_patterns.get(framework, "migrations/*")
    migration_files = glob.glob(pattern, recursive=True)

    # Filter out __pycache__ and __init__.py
    migration_files = [
        f for f in migration_files
        if '__pycache__' not in f and not f.endswith('__init__.py')
    ]

    return sorted(migration_files)


def parse_migration_file(filepath: str, framework: str, db_type: str) -> List[Dict[str, Any]]:
    """
    Parse migration file and extract operations.

    Args:
        filepath: Path to migration file
        framework: Migration framework
        db_type: Database type

    Returns:
        List of operation dictionaries
    """
    if framework == "alembic":
        return parse_alembic_migration(filepath)
    elif framework == "django":
        return parse_django_migration(filepath)
    elif framework in ["flyway", "liquibase"]:
        return parse_sql_migration(filepath)
    elif framework == "mongoose":
        return parse_mongoose_migration(filepath)
    elif framework == "activerecord":
        return parse_rails_migration(filepath)

    return []


def parse_alembic_migration(filepath: str) -> List[Dict]:
    """Parse Alembic (Python) migration file."""
    operations = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        # Extract SQL from op.execute() calls
        for i, line in enumerate(lines, 1):
            # op.execute("SQL")
            exec_match = re.search(r'op\.execute\s*\(\s*["\'](.+?)["\']', line)
            if exec_match:
                sql = exec_match.group(1)
                operations.append({
                    "type": "sql",
                    "sql": sql,
                    "line": i
                })

            # op.add_column()
            if 'op.add_column' in line:
                operations.append({
                    "type": "add_column",
                    "operation": line.strip(),
                    "line": i
                })

            # op.drop_column()
            if 'op.drop_column' in line:
                operations.append({
                    "type": "drop_column",
                    "operation": line.strip(),
                    "line": i
                })

            # op.alter_column()
            if 'op.alter_column' in line:
                operations.append({
                    "type": "alter_column",
                    "operation": line.strip(),
                    "line": i
                })

            # op.create_index()
            if 'op.create_index' in line:
                operations.append({
                    "type": "create_index",
                    "operation": line.strip(),
                    "line": i
                })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return operations


def parse_django_migration(filepath: str) -> List[Dict]:
    """Parse Django migration file."""
    operations = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # migrations.AddField()
            if 'migrations.AddField' in line:
                operations.append({
                    "type": "add_field",
                    "operation": line.strip(),
                    "line": i
                })

            # migrations.RemoveField()
            if 'migrations.RemoveField' in line:
                operations.append({
                    "type": "remove_field",
                    "operation": line.strip(),
                    "line": i
                })

            # migrations.AlterField()
            if 'migrations.AlterField' in line:
                operations.append({
                    "type": "alter_field",
                    "operation": line.strip(),
                    "line": i
                })

            # migrations.RunSQL()
            if 'migrations.RunSQL' in line:
                # Try to extract SQL
                sql_match = re.search(r'RunSQL\s*\(\s*["\'](.+?)["\']', line)
                if sql_match:
                    operations.append({
                        "type": "sql",
                        "sql": sql_match.group(1),
                        "line": i
                    })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return operations


def parse_sql_migration(filepath: str) -> List[Dict]:
    """Parse raw SQL migration file."""
    operations = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('--') or line.startswith('/*'):
                continue

            # Extract SQL statements
            if any(keyword in line.upper() for keyword in ['ALTER TABLE', 'CREATE INDEX', 'DROP', 'ADD COLUMN']):
                operations.append({
                    "type": "sql",
                    "sql": line,
                    "line": i
                })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return operations


def parse_mongoose_migration(filepath: str) -> List[Dict]:
    """Parse Mongoose (MongoDB) migration file."""
    operations = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # createIndex()
            if 'createIndex' in line:
                operations.append({
                    "type": "create_index",
                    "operation": line.strip(),
                    "line": i
                })

            # updateMany() or update()
            if re.search(r'\.(updateMany|update)\s*\(', line):
                operations.append({
                    "type": "update",
                    "operation": line.strip(),
                    "line": i
                })

            # Schema validation
            if 'validationLevel' in line or 'validationAction' in line:
                operations.append({
                    "type": "validation",
                    "operation": line.strip(),
                    "line": i
                })

            # $rename
            if '$rename' in line:
                operations.append({
                    "type": "rename",
                    "operation": line.strip(),
                    "line": i
                })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return operations


def parse_rails_migration(filepath: str) -> List[Dict]:
    """Parse ActiveRecord (Rails) migration file."""
    operations = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # add_column
            if 'add_column' in line:
                operations.append({
                    "type": "add_column",
                    "operation": line.strip(),
                    "line": i
                })

            # remove_column
            if 'remove_column' in line:
                operations.append({
                    "type": "remove_column",
                    "operation": line.strip(),
                    "line": i
                })

            # change_column
            if 'change_column' in line:
                operations.append({
                    "type": "change_column",
                    "operation": line.strip(),
                    "line": i
                })

            # add_index
            if 'add_index' in line:
                operations.append({
                    "type": "add_index",
                    "operation": line.strip(),
                    "line": i
                })

            # execute() - raw SQL
            if line.strip().startswith('execute'):
                sql_match = re.search(r'execute\s*\(\s*["\'](.+?)["\']', line)
                if sql_match:
                    operations.append({
                        "type": "sql",
                        "sql": sql_match.group(1),
                        "line": i
                    })

    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return operations


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python parsers.py <framework> <filepath>")
        sys.exit(1)

    framework = sys.argv[1]
    filepath = sys.argv[2]

    operations = parse_migration_file(filepath, framework, "postgresql")
    print(f"Found {len(operations)} operations:")
    for op in operations:
        print(f"  Line {op['line']}: {op.get('sql') or op.get('operation')}")
