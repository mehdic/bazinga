---
name: sqlserver
type: database
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# SQL Server Engineering Expertise

## Specialist Profile
SQL Server specialist building enterprise database solutions. Expert in T-SQL, query optimization, and SQL Server features.

---

## Patterns to Follow

### T-SQL Best Practices
- **SET NOCOUNT ON**: In all procedures
- **SET XACT_ABORT ON**: Auto-rollback on error
- **TRY/CATCH for errors**: Structured error handling
- **Table-valued parameters**: For batch operations
- **OUTPUT clause**: Return affected rows

### Performance Optimization
- **Parameterized queries**: Avoid plan cache bloat
- **Execution plan analysis**: SET STATISTICS IO/TIME ON
- **Index tuning advisor**: DMV-based recommendations
- **Query Store**: Performance regression detection
- **Columnstore for analytics**: Massive compression, fast aggregations

### Modern Features (2019+)
<!-- version: sqlserver >= 2019 -->
- **Intelligent Query Processing**: Auto-tuning
- **Accelerated Database Recovery**: Fast recovery
- **Memory-optimized TempDB**: Reduced contention
- **APPROX_COUNT_DISTINCT**: Fast approximate counts
- **Scalar UDF inlining**: Better performance

### Window Functions
- **RANK, DENSE_RANK, ROW_NUMBER**: Ordering
- **LAG, LEAD**: Access previous/next rows
- **FIRST_VALUE, LAST_VALUE**: Boundary values
- **SUM/COUNT OVER**: Running totals
- **PERCENT_RANK, CUME_DIST**: Statistical

### JSON Support
- **JSON_VALUE**: Extract scalar value
- **JSON_QUERY**: Extract object/array
- **JSON_MODIFY**: Update JSON
- **OPENJSON**: Parse to rowset
- **FOR JSON**: Generate JSON output

---

## Patterns to Avoid

### T-SQL Anti-Patterns
- ❌ **Missing SET NOCOUNT ON**: Extra network chatter
- ❌ **NOLOCK hints everywhere**: Dirty reads, not faster
- ❌ **Cursors for set operations**: Use set-based SQL
- ❌ **SELECT ***: Specify needed columns
- ❌ **Scalar UDFs in WHERE**: Performance killer (pre-2019)

### Performance Anti-Patterns
- ❌ **Non-parameterized queries**: Plan bloat
- ❌ **Functions on indexed columns**: Kills index usage
- ❌ **Missing clustered index**: Heap tables
- ❌ **Too many indexes**: Write overhead
- ❌ **Ignoring statistics**: Stale = bad plans

### Design Anti-Patterns
- ❌ **Identity gaps as bug**: By design, not guaranteed
- ❌ **Storing dates as strings**: Use DATE/DATETIME2
- ❌ **VARCHAR for Unicode**: Use NVARCHAR
- ❌ **FLOAT for money**: Use DECIMAL/MONEY

### Error Handling Anti-Patterns
- ❌ **No TRY/CATCH**: Unhandled errors
- ❌ **RAISERROR without proper severity**: Use THROW
- ❌ **Missing XACT_ABORT**: Partial transactions
- ❌ **Ignoring @@TRANCOUNT**: Transaction leaks

---

## Verification Checklist

### Procedures
- [ ] SET NOCOUNT ON
- [ ] SET XACT_ABORT ON
- [ ] TRY/CATCH blocks
- [ ] Parameterized queries

### Performance
- [ ] Execution plans reviewed
- [ ] Indexes on query predicates
- [ ] Statistics up to date
- [ ] Query Store enabled

### Schema
- [ ] Clustered index on all tables
- [ ] Non-clustered for common queries
- [ ] Appropriate data types
- [ ] Constraints for integrity

### Operational
- [ ] Maintenance plans configured
- [ ] Backup/restore tested
- [ ] Monitoring alerts set
- [ ] Index fragmentation managed

---

## Code Patterns (Reference)

### Stored Procedure
- **Template**: `CREATE OR ALTER PROCEDURE dbo.CreateUser ... AS BEGIN SET NOCOUNT ON; SET XACT_ABORT ON; BEGIN TRY BEGIN TRAN; ... COMMIT; END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK; THROW; END CATCH END;`
- **OUTPUT**: `INSERT INTO users (...) OUTPUT INSERTED.Id VALUES (...);`

### Queries
- **Pagination**: `SELECT * FROM users ORDER BY CreatedAt DESC OFFSET @Offset ROWS FETCH NEXT @Limit ROWS ONLY;`
- **Count with results**: `SELECT *, COUNT(*) OVER() AS TotalCount FROM users ORDER BY ... OFFSET ... FETCH ...;`
- **MERGE**: `MERGE INTO t AS target USING (...) AS source ON ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...;`

### Window Functions
- **Ranking**: `SELECT *, RANK() OVER (ORDER BY Score DESC) FROM users;`
- **Running total**: `SELECT *, SUM(Amount) OVER (ORDER BY Date ROWS UNBOUNDED PRECEDING) FROM orders;`
- **Partition**: `SELECT *, SUM(Amount) OVER (PARTITION BY UserId) AS UserTotal FROM orders;`

### JSON
- **Query**: `SELECT Id, JSON_VALUE(Preferences, '$.theme') AS Theme FROM users WHERE ISJSON(Preferences) = 1;`
- **Modify**: `UPDATE users SET Preferences = JSON_MODIFY(Preferences, '$.theme', 'dark') WHERE Id = @Id;`

