---
name: postgresql
type: database
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# PostgreSQL Engineering Expertise

## Specialist Profile
PostgreSQL specialist optimizing relational databases. Expert in query optimization, indexing strategies, and advanced features.

---

## Patterns to Follow

### Index Strategy
- **B-tree (default)**: Equality, range, ORDER BY, GROUP BY
- **Hash**: Equality-only comparisons (fast)
- **GIN**: Arrays, JSONB, full-text search
- **GiST**: Geometric, ranges, full-text
- **BRIN**: Large sequential tables (time-series)
- **Partial indexes**: `WHERE status = 'active'` for subset

### Query Optimization
- **EXPLAIN ANALYZE**: Always check query plans
- **pg_stat_statements**: Find slowest queries
- **CTEs for readability**: But know they can be optimization barriers
- **JOINs over subqueries**: Usually more efficient
- **LIMIT with ORDER BY**: Always together for pagination
- **Cursor-based pagination**: For large datasets

### Memory Configuration
- **shared_buffers**: 25% of RAM (starting point)
- **work_mem**: 64-256MB for OLAP, lower for OLTP
- **effective_cache_size**: 50-75% of RAM
- **maintenance_work_mem**: Higher for VACUUM, CREATE INDEX
- **random_page_cost**: 1.1 for SSD, 2.0 for spinning

### Connection Management
- **Connection pooling**: PgBouncer or Pgpool-II
- **Don't increase max_connections**: Use pooler instead
- **Appropriate pool size**: `(cores * 2) + disk_spindles`
- **Statement timeout**: Prevent runaway queries

### Maintenance
- **Autovacuum tuning**: Adjust for write-heavy tables
- **ANALYZE regularly**: Update statistics
- **Monitor bloat**: pg_stat_user_tables for dead tuples
- **Reindex periodically**: Especially after bulk updates

### Advanced Features
- **JSONB with GIN**: Flexible schema + fast queries
- **Full-text search**: tsvector, GIN index, plainto_tsquery
- **Window functions**: RANK, ROW_NUMBER, LAG, LEAD
- **UPSERT**: `ON CONFLICT DO UPDATE`
<!-- version: postgresql >= 12 -->
- **Generated columns**: Computed at write time (STORED)
- **JSON path queries**: `jsonb_path_query()` for complex extraction
<!-- version: postgresql >= 13 -->
- **Incremental sorting**: Optimizer uses partial index order
- **Parallel VACUUM**: Faster table maintenance
<!-- version: postgresql >= 14 -->
- **Multirange types**: `INT4MULTIRANGE` for discontinuous ranges
- **OUT params in procedures**: Return multiple values
<!-- version: postgresql >= 15 -->
- **MERGE statement**: Standard SQL upsert alternative
- **JSON logging**: `log_destination = 'jsonlog'`
<!-- version: postgresql >= 16 -->
- **pg_stat_io**: I/O statistics view
- **Logical replication from standby**: Reduced primary load

---

## Patterns to Avoid

### Query Anti-Patterns
- ❌ **SELECT * in production**: Select only needed columns
- ❌ **Unbounded queries**: Always use LIMIT
- ❌ **OFFSET for deep pagination**: Use cursor/keyset pagination
- ❌ **Correlated subqueries**: Rewrite as JOINs
- ❌ **Functions on indexed columns**: `WHERE LOWER(email) = ...`

### Index Anti-Patterns
- ❌ **Missing FK indexes**: Always index foreign keys
- ❌ **Over-indexing**: Slows writes, wastes space
- ❌ **Low-selectivity indexes**: Status with 3 values
- ❌ **Unused indexes**: Check pg_stat_user_indexes

### Configuration Anti-Patterns
- ❌ **Default shared_buffers (128MB)**: Way too low
- ❌ **High max_connections without pooling**: Memory exhaustion
- ❌ **Disabled autovacuum**: Table bloat, transaction wraparound
- ❌ **Missing statement_timeout**: Runaway queries

### Schema Anti-Patterns
- ❌ **VARCHAR without limit** on user input: Use TEXT or set limit
- ❌ **Serial for new tables**: Use IDENTITY or UUID
- ❌ **Storing money as float**: Use NUMERIC or bigint cents
- ❌ **Timezone-naive timestamps**: Use TIMESTAMPTZ

---

## Verification Checklist

### Indexes
- [ ] Indexes on all foreign keys
- [ ] Indexes match WHERE clauses
- [ ] Partial indexes for common filters
- [ ] GIN for JSONB/array columns
- [ ] No unused indexes (check pg_stat_user_indexes)

### Queries
- [ ] EXPLAIN ANALYZE on slow queries
- [ ] Parameterized queries (prevent injection)
- [ ] Cursor pagination for large sets
- [ ] Appropriate LIMIT on all queries

### Configuration
- [ ] shared_buffers tuned
- [ ] Connection pooling configured
- [ ] Autovacuum parameters reviewed
- [ ] statement_timeout set

### Maintenance
- [ ] Regular ANALYZE runs
- [ ] Bloat monitoring in place
- [ ] Backup strategy tested
- [ ] pg_stat_statements enabled

---

## Code Patterns (Reference)

### Index Types
- **B-tree**: `CREATE INDEX idx_users_email ON users (email);`
- **Partial**: `CREATE INDEX idx_active_users ON users (created_at) WHERE status = 'active';`
- **GIN (JSONB)**: `CREATE INDEX idx_prefs ON users USING GIN (preferences);`
- **Full-text**: `CREATE INDEX idx_search ON users USING GIN (search_vector);`

### Query Patterns
- **Cursor pagination**: `SELECT * FROM users WHERE id > $cursor ORDER BY id LIMIT 20;`
- **UPSERT**: `INSERT INTO t (k, v) VALUES (...) ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v;`
- **Window**: `SELECT *, RANK() OVER (ORDER BY score DESC) FROM users;`
- **JSONB query**: `SELECT * FROM users WHERE prefs @> '{"theme": "dark"}';`

### Maintenance
- **Statistics**: `ANALYZE users;`
- **Vacuum**: `VACUUM (VERBOSE, ANALYZE) users;`
- **Reindex**: `REINDEX INDEX CONCURRENTLY idx_users_email;`

