---
name: oracle
type: database
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Oracle Database Engineering Expertise

## Specialist Profile
Oracle DB specialist building enterprise database solutions. Expert in PL/SQL, performance tuning, and Oracle-specific features.

---

## Patterns to Follow

### PL/SQL Best Practices
- **BULK COLLECT for reads**: Process sets, not rows
- **FORALL for writes**: Batch DML operations
- **Exception handling**: WHEN OTHERS with RAISE
- **AUTONOMOUS_TRANSACTION**: Independent commits
- **Packages for organization**: Logical grouping of procedures

### Performance Optimization
- **Bind variables always**: Avoid hard parsing
- **EXPLAIN PLAN before execution**: Check access paths
- **Hints sparingly**: `/*+ INDEX */`, `/*+ PARALLEL */`
- **Partitioning for large tables**: Range, list, hash
- **Materialized views**: Pre-computed aggregations

### Modern Features (23c+)
<!-- version: oracle >= 23 -->
- **JSON Relational Duality**: JSON views over relational data
- **JavaScript stored procedures**: JS in the database
- **Annotations**: Metadata on database objects
- **SQL domains**: Semantic data types
- **Boolean data type**: Native boolean (finally)

### Concurrency & Transactions
- **MERGE for upsert**: Atomic insert/update
- **SELECT FOR UPDATE SKIP LOCKED**: Queue processing
- **Autonomous transactions for logging**: Independent commit
- **Read consistency**: Understand SCN
- **Deadlock prevention**: Consistent ordering

### Analytic Functions
- **RANK, DENSE_RANK, ROW_NUMBER**: Ordering within groups
- **LAG, LEAD**: Previous/next row values
- **RATIO_TO_REPORT**: Percentage of total
- **LISTAGG**: String aggregation
- **OVER (PARTITION BY)**: Window calculations

---

## Patterns to Avoid

### PL/SQL Anti-Patterns
- ❌ **Row-by-row processing**: Use BULK COLLECT/FORALL
- ❌ **WHEN OTHERS without RAISE**: Swallows errors
- ❌ **Commit inside loops**: Transaction fragmentation
- ❌ **Implicit cursors in loops**: Use bulk operations
- ❌ **Dynamic SQL without binds**: Injection risk, hard parse

### Performance Anti-Patterns
- ❌ **SELECT * in production**: Specify columns
- ❌ **Not using bind variables**: Library cache bloat
- ❌ **Missing indexes on FK columns**: Slow joins
- ❌ **Full table scans unintentionally**: Check explain plan
- ❌ **Cartesian joins**: Missing WHERE conditions

### Design Anti-Patterns
- ❌ **VARCHAR2 for numbers**: Use NUMBER
- ❌ **Storing dates as strings**: Use DATE/TIMESTAMP
- ❌ **No constraints**: Rely on app validation only
- ❌ **Triggers for business logic**: Hard to debug/maintain

### Concurrency Anti-Patterns
- ❌ **Long transactions**: Hold locks, block others
- ❌ **SELECT FOR UPDATE without NOWAIT/TIMEOUT**: Hangs
- ❌ **Ignoring ORA-00060 deadlocks**: Need investigation
- ❌ **Uncommitted changes in sessions**: Resource lock

---

## Verification Checklist

### PL/SQL
- [ ] BULK COLLECT for multi-row reads
- [ ] FORALL for batch DML
- [ ] Proper exception handling
- [ ] Bind variables used

### Performance
- [ ] Execution plan reviewed
- [ ] Indexes on query predicates
- [ ] Statistics current (DBMS_STATS)
- [ ] AWR/ASH for analysis

### Schema
- [ ] Primary keys on all tables
- [ ] Foreign keys indexed
- [ ] Constraints for integrity
- [ ] Partitioning for large tables

### Operational
- [ ] Regular statistics gathering
- [ ] Index maintenance
- [ ] Backup/recovery tested
- [ ] Alerting configured

---

## Code Patterns (Reference)

### PL/SQL
- **Bulk read**: `SELECT * BULK COLLECT INTO v_users FROM users WHERE status = 'pending';`
- **Bulk write**: `FORALL i IN 1..v_users.COUNT UPDATE users SET status = 'active' WHERE id = v_users(i).id;`
- **Exception**: `EXCEPTION WHEN OTHERS THEN ROLLBACK; RAISE;`

### Queries
- **Pagination (12c+)**: `SELECT * FROM users ORDER BY created_at DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;`
- **MERGE**: `MERGE INTO t USING (...) ON (...) WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...;`
- **Analytics**: `SELECT id, RANK() OVER (ORDER BY score DESC) FROM users;`

### Hints
- **Index**: `SELECT /*+ INDEX(u idx_users_status) */ * FROM users u WHERE status = 'active';`
- **Parallel**: `SELECT /*+ PARALLEL(u, 4) */ region, COUNT(*) FROM users u GROUP BY region;`

### JSON (21c+)
- **JSON column**: `CREATE TABLE t (id NUMBER, data JSON);`
- **Query**: `SELECT JSON_VALUE(data, '$.name') FROM t;`

