#!/usr/bin/env python3
"""
Dangerous Operation Detectors

Detects dangerous database operations for different databases.
"""

import re
from typing import Dict, Any


def detect_dangerous_operations(operation: Dict[str, Any], db_type: str) -> Dict[str, Any]:
    """
    Detect if operation is dangerous for the given database.

    Args:
        operation: Operation dictionary from parser
        db_type: Database type (postgresql, mysql, sqlserver, mongodb, sqlite, oracle)

    Returns:
        Dictionary with severity, issue, impact, and safe_alternative
    """
    if db_type == "postgresql":
        return check_postgresql(operation)
    elif db_type == "mysql":
        return check_mysql(operation)
    elif db_type == "sqlserver":
        return check_sqlserver(operation)
    elif db_type == "mongodb":
        return check_mongodb(operation)
    elif db_type == "sqlite":
        return check_sqlite(operation)
    elif db_type == "oracle":
        return check_oracle(operation)

    return {"severity": "safe", "reason": "Unknown database type"}


def check_postgresql(operation: Dict) -> Dict:
    """Check PostgreSQL operations."""
    op_str = (operation.get('sql') or operation.get('operation', '')).upper()
    op_type = operation.get('type', '')

    # ADD COLUMN with DEFAULT (without NOT VALID)
    # Check both SQL and Alembic patterns
    is_add_column_with_default = (
        (re.search(r'ADD\s+COLUMN.*DEFAULT', op_str) or
         (op_type == 'add_column' and 'SERVER_DEFAULT' in op_str)) and
        'NOT VALID' not in op_str
    )

    if is_add_column_with_default:
        return {
            "severity": "critical",
            "issue": "Adding column with DEFAULT locks table during rewrite",
            "impact": {
                "locks_table": True,
                "lock_type": "AccessExclusiveLock",
                "blocks_reads": True,
                "blocks_writes": True,
                "estimated_duration": "5-60 seconds per million rows"
            },
            "safe_alternative": {
                "approach": "Three-step migration",
                "steps": [
                    "1. ADD COLUMN ... NULL (no default)",
                    "2. UPDATE in batches: SET column = value WHERE column IS NULL",
                    "3. ALTER COLUMN SET DEFAULT value"
                ],
                "downtime": "none"
            }
        }

    # CREATE INDEX without CONCURRENTLY
    # Check both SQL and Alembic patterns
    is_create_index_without_concurrent = (
        ('CREATE INDEX' in op_str and 'CONCURRENTLY' not in op_str) or
        (op_type == 'create_index' and 'CONCURRENTLY' not in op_str)
    )

    if is_create_index_without_concurrent:
        return {
            "severity": "high",
            "issue": "Index creation without CONCURRENTLY locks table",
            "impact": {
                "locks_table": True,
                "lock_type": "ShareLock",
                "blocks_reads": False,
                "blocks_writes": True,
                "estimated_duration": "20-180 seconds on large table"
            },
            "safe_alternative": {
                "approach": "Concurrent index creation",
                "steps": ["CREATE INDEX CONCURRENTLY idx_name ON table(column)"],
                "downtime": "none",
                "note": "Takes longer but doesn't block writes"
            }
        }

    # DROP COLUMN
    # Check both SQL and Alembic patterns
    is_drop_column = 'DROP COLUMN' in op_str or op_type == 'drop_column'

    if is_drop_column:
        return {
            "severity": "high",
            "issue": "Dropping column can break running application and rewrites table",
            "impact": {
                "locks_table": True,
                "blocks_reads": True,
                "blocks_writes": True,
                "breaks_app": True
            },
            "safe_alternative": {
                "approach": "Multi-step removal",
                "steps": [
                    "1. Deploy code that ignores column",
                    "2. Wait for deployment to complete",
                    "3. Drop column in maintenance window"
                ],
                "downtime": "minimal"
            }
        }

    # ALTER COLUMN TYPE
    # Check both SQL and Alembic patterns
    is_alter_column_type = (
        re.search(r'ALTER\s+COLUMN.*TYPE', op_str) or
        (op_type == 'alter_column' and 'TYPE_=' in op_str)
    )

    if is_alter_column_type:
        return {
            "severity": "critical",
            "issue": "Changing column type rewrites entire table",
            "impact": {
                "locks_table": True,
                "blocks_reads": True,
                "blocks_writes": True,
                "estimated_duration": "Minutes to hours on large tables"
            },
            "safe_alternative": {
                "approach": "Create new column and migrate",
                "steps": [
                    "1. ADD COLUMN new_col TYPE",
                    "2. Backfill in batches",
                    "3. Deploy code using new column",
                    "4. Drop old column"
                ],
                "downtime": "none"
            }
        }

    # ADD CHECK CONSTRAINT without NOT VALID
    if re.search(r'ADD\s+(CONSTRAINT|CHECK)', op_str) and 'NOT VALID' not in op_str:
        return {
            "severity": "high",
            "issue": "Adding check constraint locks table while validating",
            "impact": {
                "locks_table": True,
                "blocks_writes": True
            },
            "safe_alternative": {
                "approach": "Add with NOT VALID then validate",
                "steps": [
                    "1. ADD CONSTRAINT ... NOT VALID",
                    "2. VALIDATE CONSTRAINT (doesn't block writes)"
                ],
                "downtime": "none"
            }
        }

    return {"severity": "safe", "reason": "Operation appears safe"}


def check_mysql(operation: Dict) -> Dict:
    """Check MySQL operations."""
    op_str = (operation.get('sql') or operation.get('operation', '')).upper()
    op_type = operation.get('type', '')

    # ADD COLUMN with DEFAULT
    # Check both SQL and Django/Alembic patterns
    is_add_column_with_default = (
        re.search(r'ADD\s+COLUMN.*DEFAULT', op_str) or
        (op_type in ['add_column', 'add_field'] and 'DEFAULT' in op_str)
    )

    if is_add_column_with_default:
        return {
            "severity": "critical",
            "issue": "Adding column with DEFAULT locks table during rewrite",
            "impact": {
                "locks_table": True,
                "blocks_writes": True,
                "estimated_duration": "10-120 seconds per million rows"
            },
            "safe_alternative": {
                "approach": "Use pt-online-schema-change or three-step migration",
                "steps": [
                    "Option 1: pt-online-schema-change tool",
                    "Option 2: ADD COLUMN NULL, backfill, SET DEFAULT"
                ],
                "downtime": "none with pt-osc"
            }
        }

    # ALTER TABLE MODIFY COLUMN (type change)
    if re.search(r'MODIFY\s+COLUMN', op_str):
        return {
            "severity": "critical",
            "issue": "Modifying column type rewrites table",
            "impact": {
                "locks_table": True,
                "blocks_writes": True
            },
            "safe_alternative": {
                "approach": "Use pt-online-schema-change or new column migration",
                "steps": [
                    "Recommended: pt-online-schema-change for zero downtime"
                ],
                "downtime": "none with pt-osc"
            }
        }

    # CREATE INDEX without ALGORITHM=INPLACE
    if 'CREATE INDEX' in op_str or 'ADD INDEX' in op_str:
        if 'ALGORITHM=INPLACE' not in op_str:
            return {
                "severity": "medium",
                "issue": "Index creation may lock table (depends on MySQL version)",
                "impact": {
                    "locks_table": True,
                    "blocks_writes": True
                },
                "safe_alternative": {
                    "approach": "Use ALGORITHM=INPLACE (MySQL 5.6+)",
                    "steps": ["ALTER TABLE table ADD INDEX idx ALGORITHM=INPLACE LOCK=NONE"],
                    "downtime": "none on MySQL 5.6+"
                }
            }

    # DROP COLUMN
    if 'DROP COLUMN' in op_str:
        return {
            "severity": "high",
            "issue": "Dropping column can break running application",
            "impact": {
                "breaks_app": True,
                "locks_table": True
            },
            "safe_alternative": {
                "approach": "Deploy code changes first",
                "steps": [
                    "1. Deploy code that doesn't use column",
                    "2. Drop column in next deployment"
                ],
                "downtime": "minimal"
            }
        }

    return {"severity": "safe", "reason": "Operation appears safe"}


def check_sqlserver(operation: Dict) -> Dict:
    """Check Microsoft SQL Server operations."""
    op_str = (operation.get('sql') or operation.get('operation', '')).upper()
    op_type = operation.get('type', '')

    # ALTER TABLE ADD COLUMN with DEFAULT
    # Check both SQL and framework patterns
    is_add_with_default = (
        re.search(r'ALTER\s+TABLE.*ADD.*DEFAULT', op_str) or
        (op_type in ['add_column', 'add_field'] and 'DEFAULT' in op_str)
    )

    if is_add_with_default:
        return {
            "severity": "critical",
            "issue": "Adding column with DEFAULT in SQL Server locks table and can be slow",
            "impact": {
                "locks_table": True,
                "blocks_reads": False,
                "blocks_writes": True,
                "estimated_duration": "Dependent on table size and SQL Server version"
            },
            "safe_alternative": {
                "approach": "Two-step migration (SQL Server 2012+)",
                "steps": [
                    "1. ALTER TABLE ADD column NULL",
                    "2. ALTER TABLE ADD CONSTRAINT DF_col DEFAULT value FOR column",
                    "Note: SQL Server 2012+ adds DEFAULT constraints instantly"
                ],
                "downtime": "Minimal on SQL Server 2012+"
            }
        }

    # CREATE INDEX without ONLINE=ON
    if 'CREATE INDEX' in op_str or 'CREATE NONCLUSTERED INDEX' in op_str:
        if 'ONLINE' not in op_str and 'ON' not in op_str:
            return {
                "severity": "high",
                "issue": "Index creation without ONLINE=ON blocks table modifications",
                "impact": {
                    "locks_table": True,
                    "blocks_writes": True,
                    "blocks_reads": False
                },
                "safe_alternative": {
                    "approach": "Online index creation (Enterprise Edition)",
                    "steps": [
                        "CREATE NONCLUSTERED INDEX idx_name ON table(column) WITH (ONLINE=ON)",
                        "Note: Requires SQL Server Enterprise Edition"
                    ],
                    "downtime": "none with ONLINE=ON"
                }
            }

    # DROP COLUMN
    if 'DROP COLUMN' in op_str:
        return {
            "severity": "high",
            "issue": "Dropping column can break running application",
            "impact": {
                "breaks_app": True,
                "locks_table": True,
                "instant_metadata_change": True
            },
            "safe_alternative": {
                "approach": "Multi-step removal",
                "steps": [
                    "1. Deploy code that doesn't use column",
                    "2. Wait for deployment completion",
                    "3. DROP COLUMN (metadata change is instant in SQL Server)"
                ],
                "downtime": "minimal"
            }
        }

    # ALTER COLUMN (type change)
    if re.search(r'ALTER\s+COLUMN.*(?:INT|VARCHAR|NVARCHAR|DECIMAL)', op_str):
        return {
            "severity": "critical",
            "issue": "Changing column type requires table lock and data conversion",
            "impact": {
                "locks_table": True,
                "blocks_all": True,
                "data_conversion_required": True,
                "estimated_duration": "Depends on table size and conversion complexity"
            },
            "safe_alternative": {
                "approach": "Create new column and migrate",
                "steps": [
                    "1. ADD new_column with new type",
                    "2. UPDATE in batches to populate new_column",
                    "3. Deploy code using new_column",
                    "4. DROP old_column"
                ],
                "downtime": "none"
            }
        }

    # Large UPDATE/DELETE without batching
    if ('UPDATE' in op_str or 'DELETE' in op_str) and 'TOP' not in op_str:
        return {
            "severity": "medium",
            "issue": "Large UPDATE/DELETE without batching can cause lock escalation",
            "impact": {
                "lock_escalation_risk": True,
                "transaction_log_growth": True,
                "blocking_risk": True
            },
            "safe_alternative": {
                "approach": "Batch operations with TOP",
                "steps": [
                    "WHILE 1=1 BEGIN",
                    "  UPDATE TOP (1000) table SET column = value WHERE condition",
                    "  IF @@ROWCOUNT = 0 BREAK",
                    "END"
                ],
                "downtime": "none"
            }
        }

    # CREATE CLUSTERED INDEX (table rebuild)
    if 'CREATE CLUSTERED INDEX' in op_str:
        return {
            "severity": "critical",
            "issue": "Creating clustered index rebuilds entire table",
            "impact": {
                "locks_table": True,
                "rebuilds_table": True,
                "blocks_all": True,
                "estimated_duration": "Can take hours on large tables"
            },
            "safe_alternative": {
                "approach": "Use ONLINE=ON if available",
                "steps": [
                    "CREATE CLUSTERED INDEX idx WITH (ONLINE=ON) -- Enterprise only",
                    "Consider maintenance window for Standard Edition"
                ],
                "downtime": "none with Enterprise Edition"
            }
        }

    return {"severity": "safe", "reason": "Operation appears safe"}


def check_mongodb(operation: Dict) -> Dict:
    """Check MongoDB operations."""
    op_str = operation.get('operation', '')

    # createIndex without background:true
    if 'createIndex' in op_str:
        if 'background' not in op_str.lower():
            return {
                "severity": "high",
                "issue": "Foreground index creation blocks all operations on collection",
                "impact": {
                    "locks_collection": True,
                    "blocks_all": True,
                    "estimated_duration": "Seconds to minutes depending on data size"
                },
                "safe_alternative": {
                    "approach": "Use background index creation",
                    "steps": ["db.collection.createIndex({field: 1}, {background: true})"],
                    "downtime": "none",
                    "note": "Background indexing is slower but non-blocking"
                }
            }

    # $rename operation
    if '$rename' in op_str:
        return {
            "severity": "medium",
            "issue": "Field rename scans entire collection",
            "impact": {
                "scans_collection": True,
                "slow_on_large_collections": True
            },
            "safe_alternative": {
                "approach": "Gradual migration",
                "steps": [
                    "1. Add new field alongside old one",
                    "2. Deploy code to write both fields",
                    "3. Backfill in batches",
                    "4. Deploy code using new field",
                    "5. Remove old field"
                ],
                "downtime": "none"
            }
        }

    # Schema validation on large collection
    if 'validationLevel' in op_str or 'validationAction' in op_str:
        return {
            "severity": "medium",
            "issue": "Adding schema validation scans collection",
            "impact": {
                "scans_collection": True
            },
            "safe_alternative": {
                "approach": "Use moderate validation level",
                "steps": ["Use validationLevel: 'moderate' to skip existing documents"],
                "downtime": "none"
            }
        }

    return {"severity": "safe", "reason": "Operation appears safe"}


def check_sqlite(operation: Dict) -> Dict:
    """Check SQLite operations."""
    op_str = (operation.get('sql') or operation.get('operation', '')).upper()

    # DROP COLUMN
    if 'DROP COLUMN' in op_str:
        return {
            "severity": "high",
            "issue": "SQLite requires full table recreation to drop columns",
            "impact": {
                "rewrites_table": True,
                "locks_database": True,
                "requires_downtime": True
            },
            "safe_alternative": {
                "approach": "Table recreation pattern",
                "steps": [
                    "1. CREATE TABLE new_table (...)",
                    "2. INSERT INTO new_table SELECT ... FROM old_table",
                    "3. DROP TABLE old_table",
                    "4. ALTER TABLE new_table RENAME TO old_table"
                ],
                "downtime": "Required for SQLite",
                "note": "Wrap in transaction for atomicity"
            }
        }

    # ALTER COLUMN TYPE
    if re.search(r'ALTER\s+COLUMN.*TYPE', op_str):
        return {
            "severity": "high",
            "issue": "SQLite doesn't support ALTER COLUMN, requires table recreation",
            "impact": {
                "rewrites_table": True,
                "requires_downtime": True
            },
            "safe_alternative": {
                "approach": "Table recreation in transaction",
                "steps": [
                    "Use table recreation pattern (see DROP COLUMN)"
                ],
                "downtime": "Required"
            }
        }

    # ADD CONSTRAINT
    if 'ADD CONSTRAINT' in op_str:
        return {
            "severity": "medium",
            "issue": "SQLite has limited ALTER TABLE support",
            "impact": {
                "may_require_recreation": True
            },
            "safe_alternative": {
                "approach": "Consider application-level validation",
                "steps": [
                    "SQLite constraints often require table recreation",
                    "Consider enforcing constraints in application code"
                ],
                "downtime": "May be required"
            }
        }

    return {"severity": "safe", "reason": "Operation appears safe"}


def check_oracle(operation: Dict) -> Dict:
    """Check Oracle operations."""
    op_str = (operation.get('sql') or operation.get('operation', '')).upper()

    # ALTER TABLE (general DDL)
    if 'ALTER TABLE' in op_str:
        return {
            "severity": "high",
            "issue": "Oracle DDL operations acquire exclusive locks",
            "impact": {
                "locks_table": True,
                "lock_type": "Exclusive DDL lock",
                "blocks_all": True
            },
            "safe_alternative": {
                "approach": "Use online DDL when available",
                "steps": [
                    "Oracle 11g+: Use ONLINE keyword where supported",
                    "Schedule DDL during maintenance window",
                    "Consider Oracle Online Redefinition (DBMS_REDEFINITION)"
                ],
                "downtime": "Depends on Oracle version and operation"
            }
        }

    # DROP COLUMN
    if 'DROP COLUMN' in op_str:
        return {
            "severity": "critical",
            "issue": "Dropping column locks table and may take long time",
            "impact": {
                "locks_table": True,
                "blocks_all": True,
                "estimated_duration": "Can be very slow on large tables"
            },
            "safe_alternative": {
                "approach": "Mark column unused first",
                "steps": [
                    "1. ALTER TABLE table SET UNUSED COLUMN col",
                    "2. Later: DROP UNUSED COLUMNS during maintenance"
                ],
                "downtime": "Reduced with SET UNUSED"
            }
        }

    # Large UPDATE/DELETE operations
    if operation.get('type') == 'update' or ('UPDATE' in op_str or 'DELETE' in op_str):
        return {
            "severity": "medium",
            "issue": "Large DML operations can slow replication and cause lock contention",
            "impact": {
                "slow_replication": True,
                "lock_contention": True
            },
            "safe_alternative": {
                "approach": "Break into smaller batches",
                "steps": [
                    "Use ROWNUM to batch operations",
                    "COMMIT after each batch",
                    "Use PARALLEL hint for large tables"
                ],
                "downtime": "none"
            }
        }

    # CREATE INDEX
    if 'CREATE INDEX' in op_str:
        if 'ONLINE' not in op_str:
            return {
                "severity": "high",
                "issue": "Index creation without ONLINE blocks DML",
                "impact": {
                    "blocks_writes": True
                },
                "safe_alternative": {
                    "approach": "Use ONLINE keyword",
                    "steps": ["CREATE INDEX idx_name ON table(col) ONLINE"],
                    "downtime": "none"
                }
            }

    return {"severity": "safe", "reason": "Operation appears safe"}


# Example usage
if __name__ == "__main__":
    # Test PostgreSQL
    test_ops = [
        {"sql": "ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT ''"},
        {"sql": "CREATE INDEX idx_email ON users(email)"},
        {"sql": "CREATE INDEX CONCURRENTLY idx_email ON users(email)"},
        {"sql": "DROP COLUMN name"},
    ]

    for op in test_ops:
        result = detect_dangerous_operations(op, "postgresql")
        print(f"\nOperation: {op['sql']}")
        print(f"Severity: {result['severity']}")
        if result['severity'] != 'safe':
            print(f"Issue: {result['issue']}")
