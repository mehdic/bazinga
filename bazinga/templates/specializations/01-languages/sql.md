---
name: sql
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# SQL Engineering Expertise

## Specialist Profile
SQL specialist writing performant, maintainable queries. Expert in query optimization, indexing strategy, and database design.

---

## Patterns to Follow

### Query Structure
- **Explicit column list**: Never `SELECT *` in production
- **Table aliases**: Short, meaningful (`u` for users, `o` for orders)
- **CTEs for readability**: `WITH` clauses for complex logic
- **Consistent formatting**: Keywords uppercase, indent joins/conditions
- **COALESCE for nulls**: Handle null values explicitly

### Index-Aware Queries
- **Leftmost prefix rule**: Match index column order
- **Sargable conditions**: No functions on indexed columns
- **Range at end**: Equality conditions before range in composite indexes
- **Covering indexes**: Include all needed columns to avoid table lookup
- **EXPLAIN first**: Check execution plan before optimizing

### Joins & Subqueries
- **JOINs over subqueries**: Generally more efficient
- **EXISTS over IN**: For large subquery results
- **Correlated subqueries sparingly**: Can be slow; consider CTEs
- **Appropriate join type**: INNER, LEFT, RIGHT based on requirements

### Aggregation
- **GROUP BY all non-aggregated columns**: SQL standard compliance
- **HAVING for aggregate filters**: Not WHERE
- **Window functions for running totals**: `SUM() OVER (ORDER BY ...)`
- **DISTINCT sparingly**: Often indicates design issue

### Write Operations
- **Transactions for related writes**: BEGIN/COMMIT/ROLLBACK
- **Always have WHERE on UPDATE/DELETE**: Prevent full table modification
- **Batch large operations**: Avoid locking issues
- **RETURNING for inserted data**: Get generated values (PostgreSQL)

### Performance Patterns
- **Keyset pagination**: `WHERE id > last_id LIMIT n` over `OFFSET`
- **Materialized views**: Pre-compute expensive aggregations
- **Partial indexes**: Index only relevant rows
- **Connection pooling**: Reuse connections

### Database-Specific Features
<!-- version: postgresql >= 12 -->
- **Generated columns**: `ALTER TABLE ADD COLUMN full_name TEXT GENERATED ALWAYS AS (first || ' ' || last) STORED`
- **JSON path queries**: `jsonb_path_query(data, '$.items[*].price')`
<!-- version: postgresql >= 13 -->
- **Incremental sort**: Optimizer uses partially sorted data
<!-- version: postgresql >= 14 -->
- **Multirange types**: `INT4MULTIRANGE` for discontinuous ranges
<!-- version: postgresql >= 15 -->
- **MERGE statement**: Standard SQL MERGE for upsert operations
<!-- version: mysql >= 8.0 -->
- **Window functions**: `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`
- **CTEs with recursion**: `WITH RECURSIVE` for hierarchical queries
<!-- version: mysql >= 8.0.19 -->
- **TABLE statement**: `TABLE users` as shorthand for `SELECT * FROM users`

---

## Patterns to Avoid

### Query Anti-Patterns
- ❌ **`SELECT *`**: Fetches unnecessary data; breaks on schema changes
- ❌ **Functions on indexed columns**: `WHERE YEAR(date) = 2024` can't use index
- ❌ **Implicit type conversion**: `WHERE id = '123'` when id is integer
- ❌ **N+1 queries**: Use JOINs or batch fetching
- ❌ **Overusing DISTINCT**: Usually hides join/data issues

### Index Anti-Patterns
- ❌ **Too many indexes**: Slows writes; index what you query
- ❌ **Blunderbus indexing**: Random indexes without EXPLAIN analysis
- ❌ **Missing covering columns**: Forces table lookups
- ❌ **Wrong column order**: Index (a, b) doesn't help `WHERE b = ?`

### Write Anti-Patterns
- ❌ **UPDATE/DELETE without WHERE**: Modifies all rows
- ❌ **Long-running transactions**: Lock contention
- ❌ **No transaction for related writes**: Partial failures corrupt data
- ❌ **Dynamic SQL with concatenation**: SQL injection risk; use parameters

### Design Anti-Patterns
- ❌ **EAV (Entity-Attribute-Value)**: Hard to query; use proper columns
- ❌ **Storing comma-separated values**: Violates 1NF; use junction tables
- ❌ **No foreign keys**: Data integrity issues
- ❌ **Premature denormalization**: Normalize first, denormalize with data

---

## Verification Checklist

### Query Quality
- [ ] No `SELECT *` in production code
- [ ] EXPLAIN plan reviewed
- [ ] Indexes exist for WHERE/JOIN columns
- [ ] No functions on indexed columns in WHERE

### Performance
- [ ] N+1 patterns eliminated
- [ ] Large result sets paginated (keyset preferred)
- [ ] Long-running queries optimized
- [ ] Appropriate indexes without over-indexing

### Safety
- [ ] All writes in transactions
- [ ] UPDATE/DELETE always have WHERE
- [ ] Parameterized queries (no string concatenation)
- [ ] Backups before destructive operations

### Design
- [ ] Foreign keys for relationships
- [ ] Appropriate normalization level
- [ ] Consistent naming conventions
- [ ] NULL handling explicit (NOT NULL where appropriate)

---

## Code Patterns (Reference)

### Recommended Constructs
- **CTE**: `WITH active AS (SELECT * FROM users WHERE status = 'active') SELECT * FROM active`
- **Sargable**: `WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'`
- **Window function**: `SUM(amount) OVER (PARTITION BY user_id ORDER BY date)`
- **EXISTS**: `WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)`
- **Keyset pagination**: `WHERE id > :last_id ORDER BY id LIMIT 20`
- **Safe update**: `BEGIN; UPDATE users SET status = 'inactive' WHERE last_login < '2023-01-01'; COMMIT;`
- **COALESCE**: `COALESCE(display_name, email, 'Unknown') AS name`
<!-- version: postgresql >= 11 -->
- **Covering index**: `CREATE INDEX idx_users_status_email ON users(status) INCLUDE (email)`
<!-- version: postgresql >= 12 -->
- **Generated column**: `total NUMERIC GENERATED ALWAYS AS (quantity * price) STORED`
<!-- version: postgresql >= 15 -->
- **MERGE**: `MERGE INTO target USING source ON condition WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT`
<!-- version: mysql >= 8.0 -->
- **Window rank**: `ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) as rank`

