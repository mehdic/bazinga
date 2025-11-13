#!/usr/bin/env python3
"""
Database and Framework Detection

Detects database type and migration framework from config files.
"""

import os
import re
from typing import Optional, Dict


def detect_database_and_framework() -> Optional[Dict]:
    """
    Detect database type and migration framework.

    Returns:
        Dict with 'database' and 'framework' keys, or None
    """
    # Try Alembic (Python/SQLAlchemy)
    if os.path.exists("alembic.ini"):
        db_type = detect_from_alembic()
        if db_type:
            return {"database": db_type, "framework": "alembic"}

    # Try Django
    if os.path.exists("manage.py"):
        db_type = detect_from_django()
        if db_type:
            return {"database": db_type, "framework": "django"}

    # Try Flyway (Java/Kotlin)
    if os.path.exists("flyway.conf") or os.path.exists("flyway.toml"):
        db_type = detect_from_flyway()
        if db_type:
            return {"database": db_type, "framework": "flyway"}

    # Try Liquibase (Java/Kotlin)
    if os.path.exists("liquibase.properties") or os.path.exists("changelog.xml"):
        db_type = detect_from_liquibase()
        if db_type:
            return {"database": db_type, "framework": "liquibase"}

    # Try Mongoose (MongoDB + Node.js)
    if os.path.exists("package.json"):
        if detect_mongoose():
            return {"database": "mongodb", "framework": "mongoose"}

    # Try ActiveRecord (Ruby on Rails)
    if os.path.exists("config/database.yml"):
        db_type = detect_from_rails()
        if db_type:
            return {"database": db_type, "framework": "activerecord"}

    return None


def detect_from_alembic() -> Optional[str]:
    """Detect database from alembic.ini."""
    try:
        with open("alembic.ini", 'r') as f:
            content = f.read()

        # Look for sqlalchemy.url
        url_match = re.search(r'sqlalchemy\.url\s*=\s*(.+)', content)
        if url_match:
            url = url_match.group(1).strip()
            return parse_sqlalchemy_url(url)

    except Exception:
        pass

    return None


def parse_sqlalchemy_url(url: str) -> Optional[str]:
    """Parse database type from SQLAlchemy URL."""
    url = url.lower()

    if url.startswith('postgresql'):
        return "postgresql"
    elif url.startswith('mysql'):
        return "mysql"
    elif url.startswith(('mssql', 'sqlserver')):
        return "sqlserver"
    elif url.startswith('sqlite'):
        return "sqlite"
    elif url.startswith('oracle'):
        return "oracle"

    return None


def detect_from_django() -> Optional[str]:
    """Detect database from Django settings."""
    settings_files = [
        "settings.py",
        "*/settings.py",
        "settings/base.py",
        "config/settings.py"
    ]

    for pattern in settings_files:
        matches = find_files(pattern)
        for settings_file in matches:
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()

                # Look for DATABASE ENGINE
                engine_match = re.search(r"'ENGINE':\s*'django\.db\.backends\.(\w+)'", content)
                if engine_match:
                    engine = engine_match.group(1)

                    if engine == 'postgresql':
                        return "postgresql"
                    elif engine == 'mysql':
                        return "mysql"
                    elif engine == 'sqlite3':
                        return "sqlite"
                    elif engine in ['mssql', 'sqlserver']:
                        return "sqlserver"
                    elif engine == 'oracle':
                        return "oracle"

            except Exception:
                continue

    return None


def detect_from_flyway() -> Optional[str]:
    """Detect database from Flyway config."""
    config_files = ["flyway.conf", "flyway.toml"]

    for config_file in config_files:
        if not os.path.exists(config_file):
            continue

        try:
            with open(config_file, 'r') as f:
                content = f.read()

            # Look for flyway.url
            url_match = re.search(r'flyway\.url\s*=\s*(.+)', content)
            if url_match:
                url = url_match.group(1).strip()
                return parse_jdbc_url(url)

        except Exception:
            continue

    return None


def parse_jdbc_url(url: str) -> Optional[str]:
    """Parse database type from JDBC URL."""
    url = url.lower()

    if 'postgresql' in url:
        return "postgresql"
    elif 'mysql' in url:
        return "mysql"
    elif 'sqlserver' in url or 'mssql' in url:
        return "sqlserver"
    elif 'oracle' in url:
        return "oracle"
    elif 'sqlite' in url:
        return "sqlite"

    return None


def detect_from_liquibase() -> Optional[str]:
    """Detect database from Liquibase config."""
    if os.path.exists("liquibase.properties"):
        try:
            with open("liquibase.properties", 'r') as f:
                content = f.read()

            url_match = re.search(r'url\s*[=:]\s*(.+)', content)
            if url_match:
                url = url_match.group(1).strip()
                return parse_jdbc_url(url)

        except Exception:
            pass

    return None


def detect_mongoose() -> bool:
    """Check if project uses Mongoose for MongoDB."""
    try:
        with open("package.json", 'r') as f:
            import json
            package = json.load(f)

        dependencies = {**package.get('dependencies', {}), **package.get('devDependencies', {})}

        return 'mongoose' in dependencies

    except Exception:
        return False


def detect_from_rails() -> Optional[str]:
    """Detect database from Rails database.yml."""
    try:
        with open("config/database.yml", 'r') as f:
            content = f.read()

        # Look for adapter
        adapter_match = re.search(r'adapter:\s*(\w+)', content)
        if adapter_match:
            adapter = adapter_match.group(1)

            if adapter in ['postgresql', 'postgres']:
                return "postgresql"
            elif adapter == 'mysql2':
                return "mysql"
            elif adapter in ['sqlserver', 'mssql', 'tinytds']:
                return "sqlserver"
            elif adapter == 'sqlite3':
                return "sqlite"
            elif adapter == 'oracle_enhanced':
                return "oracle"

    except Exception:
        pass

    return None


def find_files(pattern: str) -> list:
    """Find files matching pattern."""
    import glob
    return glob.glob(pattern, recursive=True)


# Example usage
if __name__ == "__main__":
    result = detect_database_and_framework()
    if result:
        print(f"Database: {result['database']}")
        print(f"Framework: {result['framework']}")
    else:
        print("Could not detect database or framework")
