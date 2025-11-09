# Database Migration Check Skill

**Type:** Model-invoked migration safety validator
**Purpose:** Detect dangerous operations in database migrations before deployment
**Complexity:** Medium (5-20 seconds runtime)

## What This Skill Does

Before applying database migrations, this Skill analyzes migration files to detect dangerous operations that could cause downtime, data loss, or performance issues.

**Key Capabilities:**
1. **Dangerous Operation Detection**: Identifies table locks, rewrites, data loss risks
2. **Multi-Database Support**: PostgreSQL, MySQL, SQL Server, MongoDB (+ SQLite, Oracle)
3. **Safe Alternative Suggestions**: Recommends zero-downtime approaches
4. **Migration Framework Detection**: Alembic, Django, Flyway, Liquibase, Mongoose, ActiveRecord
5. **Performance Impact Analysis**: Estimates lock duration and affected rows

## Supported Databases

**Top 4 Most Common (Primary Focus):**

| Database | Dangerous Operations Detected | Safe Patterns |
|----------|------------------------------|---------------|
| **PostgreSQL** | ADD COLUMN DEFAULT, DROP COLUMN, ADD INDEX, ALTER TYPE | NOT VALID, CONCURRENTLY |
| **MySQL** | ADD COLUMN DEFAULT, ALTER TYPE, ADD INDEX | Online DDL, pt-online-schema-change |
| **SQL Server** | ADD COLUMN DEFAULT, CREATE INDEX, ALTER COLUMN, clustered indexes | ONLINE=ON, batched updates |
| **MongoDB** | Schema changes, index creation on large collections | Background index creation |

**Also Supported:**

| Database | Dangerous Operations Detected | Safe Patterns |
|----------|------------------------------|---------------|
| **SQLite** | Table rewrites, column drops | Recreate table pattern |
| **Oracle** | DDL locks, partition operations, large batch DML | Online operations, parallel DML |

## Usage

```bash
/db-migration-check
```

The Skill automatically finds migration files in common locations:
- `migrations/`, `alembic/versions/`, `db/migrate/`
- Django, Alembic, Flyway, Liquibase, Mongoose formats
- Detects database type from config files

## Output

**File:** `coordination/db_migration_check.json`

```json
{
  "status": "dangerous_operations_detected",
  "database": "postgresql",
  "migration_framework": "alembic",
  "migrations_analyzed": 3,
  "dangerous_operations": [
    {
      "severity": "critical",
      "migration_file": "migrations/0042_add_user_email.py",
      "line": 15,
      "operation": "ADD COLUMN email VARCHAR(255) DEFAULT ''",
      "issue": "Adding column with DEFAULT locks table during rewrite",
      "impact": {
        "locks_table": true,
        "lock_type": "AccessExclusiveLock",
        "blocks_reads": true,
        "blocks_writes": true,
        "estimated_duration": "5-60 seconds per million rows"
      },
      "safe_alternative": {
        "approach": "Three-step migration",
        "steps": [
          "1. ADD COLUMN email VARCHAR(255) NULL (no default)",
          "2. UPDATE users SET email = '' WHERE email IS NULL (in batches)",
          "3. ALTER COLUMN email SET DEFAULT ''"
        ],
        "downtime": "none"
      }
    },
    {
      "severity": "high",
      "migration_file": "migrations/0043_add_email_index.py",
      "line": 8,
      "operation": "CREATE INDEX idx_user_email ON users(email)",
      "issue": "Index creation without CONCURRENTLY locks table",
      "impact": {
        "locks_table": true,
        "lock_type": "ShareLock",
        "blocks_reads": false,
        "blocks_writes": true,
        "estimated_duration": "20-180 seconds on large table"
      },
      "safe_alternative": {
        "approach": "Concurrent index creation",
        "steps": [
          "CREATE INDEX CONCURRENTLY idx_user_email ON users(email)"
        ],
        "downtime": "none",
        "note": "Takes longer but doesn't block writes"
      }
    }
  ],
  "warnings": [
    {
      "severity": "medium",
      "migration_file": "migrations/0044_rename_column.py",
      "operation": "RENAME COLUMN name TO full_name",
      "issue": "Column rename can break running application code",
      "recommendation": "Deploy code changes before migration, or use view alias"
    }
  ],
  "safe_migrations": [
    {
      "migration_file": "migrations/0045_add_optional_field.py",
      "operation": "ADD COLUMN phone VARCHAR(20) NULL",
      "reason": "Adding nullable column is safe (no default, no constraint)"
    }
  ],
  "recommendations": [
    "Run dangerous migrations during maintenance window",
    "Consider pt-online-schema-change for large MySQL tables",
    "Test migrations on production-sized dataset first",
    "Monitor lock waits: SELECT * FROM pg_locks WHERE NOT granted"
  ]
}
```

## Dangerous Operations by Database

### PostgreSQL

**Critical Operations:**
- `ADD COLUMN ... DEFAULT value` - Rewrites entire table
- `ALTER COLUMN TYPE` - Rewrites entire table
- `DROP COLUMN` - Can break running app, rewrites table
- `ADD CHECK CONSTRAINT` - Locks table while validating
- `CREATE INDEX` (without CONCURRENTLY) - Blocks writes

**Safe Patterns:**
- `ADD COLUMN ... DEFAULT value NOT VALID` then validate separately
- `CREATE INDEX CONCURRENTLY`
- Gradual type migrations

### MySQL

**Critical Operations:**
- `ADD COLUMN ... DEFAULT value` - Locks table during rewrite
- `ALTER COLUMN TYPE` - Rewrites table, blocks writes
- `ADD INDEX` - Blocks writes (unless ALGORITHM=INPLACE)
- `CHANGE COLUMN` - Can rewrite table

**Safe Patterns:**
- `ALGORITHM=INPLACE` for supported operations
- `pt-online-schema-change` for large tables
- Add column as NULL first, backfill, then add default

### SQL Server

**Critical Operations:**
- `ALTER TABLE ADD ... DEFAULT value` - Locks table (version dependent)
- `ALTER COLUMN` type change - Requires table lock and data conversion
- `CREATE CLUSTERED INDEX` - Rebuilds entire table
- `CREATE INDEX` (without ONLINE=ON) - Blocks modifications
- Large `UPDATE`/`DELETE` without batching - Lock escalation risk

**Safe Patterns:**
- `CREATE INDEX ... WITH (ONLINE=ON)` (Enterprise Edition)
- SQL Server 2012+ adds DEFAULT constraints instantly (add column NULL first)
- Batch large DML with `TOP` clause to prevent lock escalation
- Use `ONLINE=ON` for index operations when available

### MongoDB

**Critical Operations:**
- Schema validation rules added to large collections
- Index creation on large collections (foreground)
- `$rename` field on documents (scans entire collection)
- Dropping fields without setting to NULL first

**Safe Patterns:**
- `createIndex({ background: true })` for indexes
- Gradual field migrations with batching
- Schema validation with `validationLevel: "moderate"`

### SQLite

**Critical Operations:**
- `DROP COLUMN` - Requires table recreation
- `ALTER COLUMN TYPE` - Requires table recreation
- `ADD CONSTRAINT` - May require table recreation
- Any operation requiring table copy

**Safe Patterns:**
- Create new table, copy data, rename (in transaction)
- Use application-level validation instead of constraints
- Accept that SQLite requires downtime for schema changes

### Oracle

**Critical Operations:**
- DDL operations (acquire exclusive locks)
- `DROP COLUMN` - Locks table
- `ALTER TABLE` modifications on large tables
- Large batch DML in single transaction
- Partition operations

**Safe Patterns:**
- Use online DDL options when available
- Schedule DDL during maintenance windows
- Break large DML into smaller batches
- Use parallel DML for large operations

## How It Works

### Step 1: Detect Database & Framework

```python
# Detect database from config files
if exists("alembic.ini"):
    framework = "alembic"
    db_type = parse_sqlalchemy_url("alembic.ini")
elif exists("flyway.conf"):
    framework = "flyway"
    db_type = parse_jdbc_url("flyway.conf")
elif exists("manage.py") and has_django:
    framework = "django"
    db_type = parse_django_settings()
elif exists("package.json") and has_mongoose:
    framework = "mongoose"
    db_type = "mongodb"
```

### Step 2: Find Migration Files

```python
migration_paths = {
    "alembic": "alembic/versions/*.py",
    "django": "*/migrations/*.py",
    "flyway": "db/migration/*.sql",
    "liquibase": "db/changelog/*.xml",
    "mongoose": "migrations/*.js"
}

pending_migrations = find_unapplied_migrations(framework)
```

### Step 3: Parse & Analyze Migrations

```python
for migration_file in pending_migrations:
    if db_type in ["postgresql", "mysql", "oracle"]:
        sql_statements = extract_sql(migration_file)
        for stmt in sql_statements:
            check_sql_operation(stmt, db_type)

    elif db_type == "mongodb":
        operations = extract_mongo_operations(migration_file)
        for op in operations:
            check_mongo_operation(op)
```

### Step 4: Check for Dangerous Patterns

```python
def check_sql_operation(stmt, db_type):
    # PostgreSQL dangerous patterns
    if db_type == "postgresql":
        if re.search(r'ADD COLUMN .* DEFAULT', stmt, re.I):
            if not re.search(r'NOT VALID', stmt, re.I):
                report_issue(
                    severity="critical",
                    operation="ADD COLUMN DEFAULT",
                    alternative="Add column as NULL, backfill, set default"
                )

        if re.search(r'CREATE INDEX(?! CONCURRENTLY)', stmt, re.I):
            report_issue(
                severity="high",
                operation="CREATE INDEX",
                alternative="CREATE INDEX CONCURRENTLY"
            )
```

## Implementation

**Files:**
- `check.py`: Main migration checker
- `parsers.py`: Parse migration files (SQL, Python, JS, XML)
- `detectors.py`: Database-specific dangerous operation detection
- `frameworks.py`: Framework detection (Alembic, Django, Flyway, etc.)

**Dependencies:**
- Python 3.8+
- sqlparse (for SQL parsing)
- Standard library (re, ast, json, xml)

**Runtime:**
- Small migrations (<10 files): 5 seconds
- Medium migrations (10-50 files): 10-15 seconds
- Large migrations (50+ files): 15-25 seconds

**Languages Supported:** SQL, Python, JavaScript, XML (migration files)

## When to Use

✅ **Use this Skill when:**
- Creating or modifying database migrations
- Before deploying schema changes to production
- Adding indexes, columns, constraints
- Modifying existing tables with data

❌ **Don't use when:**
- No migrations in current changeset
- Empty database (no data to affect)
- Non-relational data stores (except MongoDB)

## Example Workflow

```bash
# Developer creates migration
alembic revision -m "add user email"

# Developer writes migration
# op.add_column('users', sa.Column('email', sa.String(255), server_default=''))

# Developer invokes Skill
/db-migration-check

# Skill analyzes migration (10 seconds)
# Detects dangerous operation

# Developer sees:
# - CRITICAL: ADD COLUMN with DEFAULT locks table
# - Estimated impact: 30-90 seconds on users table (5M rows)
# - Safe alternative: 3-step migration

# Developer fixes migration:
# Step 1: op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
# Step 2: (separate migration) Backfill in batches
# Step 3: (separate migration) op.alter_column('users', 'email', server_default='')

# Re-run check
/db-migration-check
# Result: All safe operations ✅
```

## Benefits

**Without Skill:**
- Developer runs migration in production
- Table locks for 2 minutes
- 500 requests/sec fail with timeouts
- Emergency rollback required
- Customer complaints
- **Total:** 4-8 hours incident response + customer impact

**With Skill:**
- Skill detects dangerous operation (10 seconds)
- Developer implements safe 3-step approach
- Zero downtime deployment
- **Total:** 30 minutes to refactor migration

**ROI:** 8-16x (prevents production incidents)

## Integration

This Skill is configurable via `/configure-skills` command.

When marked as 'mandatory' in skills_config.json, the Orchestrator automatically invokes this Skill when database migration changes are detected before Developer commits.
