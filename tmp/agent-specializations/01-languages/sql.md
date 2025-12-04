---
name: sql
type: language
priority: 1
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# SQL Engineering Expertise

## Specialist Profile
SQL specialist writing performant, maintainable queries. Expert in query optimization, indexing, and database design.

## Implementation Guidelines

### Query Structure

```sql
-- Clear, formatted queries
SELECT
    u.id,
    u.email,
    u.display_name,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
    AND u.created_at >= '2024-01-01'
GROUP BY u.id, u.email, u.display_name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC
LIMIT 100;
```

### CTEs for Readability

```sql
WITH active_users AS (
    SELECT id, email, display_name
    FROM users
    WHERE status = 'active'
),
user_orders AS (
    SELECT
        user_id,
        COUNT(*) AS order_count,
        SUM(total) AS total_spent
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT
    au.email,
    au.display_name,
    COALESCE(uo.order_count, 0) AS order_count,
    COALESCE(uo.total_spent, 0) AS total_spent
FROM active_users au
LEFT JOIN user_orders uo ON uo.user_id = au.id;
```

### Index-Friendly Queries

```sql
-- Good: uses index on (user_id, created_at)
SELECT * FROM orders
WHERE user_id = 123
    AND created_at >= '2024-01-01';

-- Bad: function on indexed column
SELECT * FROM orders
WHERE YEAR(created_at) = 2024;  -- Can't use index

-- Better:
SELECT * FROM orders
WHERE created_at >= '2024-01-01'
    AND created_at < '2025-01-01';
```

### Window Functions

```sql
SELECT
    id,
    email,
    created_at,
    ROW_NUMBER() OVER (ORDER BY created_at) AS row_num,
    RANK() OVER (PARTITION BY status ORDER BY created_at) AS status_rank,
    LAG(created_at) OVER (ORDER BY created_at) AS prev_created,
    SUM(amount) OVER (ORDER BY created_at ROWS UNBOUNDED PRECEDING) AS running_total
FROM users;
```

### Safe Updates

```sql
-- Always use transactions for updates
BEGIN;

UPDATE users
SET status = 'inactive'
WHERE last_login < CURRENT_DATE - INTERVAL '1 year'
    AND status = 'active';

-- Verify before commit
SELECT COUNT(*) FROM users WHERE status = 'inactive';

COMMIT;  -- or ROLLBACK;
```

## Patterns to Avoid
- ❌ SELECT * in production
- ❌ Functions on indexed columns in WHERE
- ❌ N+1 queries (use JOINs)
- ❌ Updates without WHERE
- ❌ Implicit type conversions

## Verification Checklist
- [ ] EXPLAIN plan reviewed
- [ ] Appropriate indexes exist
- [ ] CTEs for complex queries
- [ ] Transactions for writes
- [ ] No N+1 patterns
