---
name: oracle
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Oracle Database Engineering Expertise

## Specialist Profile
Oracle DB specialist building enterprise database solutions. Expert in PL/SQL, performance tuning, and Oracle-specific features.

## Implementation Guidelines

### PL/SQL Procedures

```sql
-- Stored procedure with error handling
CREATE OR REPLACE PROCEDURE create_user(
    p_email       IN  VARCHAR2,
    p_display_name IN VARCHAR2,
    p_user_id     OUT VARCHAR2,
    p_status      OUT VARCHAR2
) AS
    v_count NUMBER;
BEGIN
    -- Check for duplicate
    SELECT COUNT(*) INTO v_count
    FROM users WHERE email = LOWER(p_email);

    IF v_count > 0 THEN
        p_status := 'ERROR: Email already exists';
        RETURN;
    END IF;

    -- Generate UUID
    p_user_id := SYS_GUID();

    INSERT INTO users (id, email, display_name, status, created_at)
    VALUES (p_user_id, LOWER(p_email), p_display_name, 'pending', SYSTIMESTAMP);

    COMMIT;
    p_status := 'SUCCESS';

EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_status := 'ERROR: ' || SQLERRM;
END create_user;
/
```

### Pagination with ROWNUM/FETCH

```sql
-- Oracle 12c+ (FETCH FIRST)
SELECT id, email, display_name, created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC
OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;

-- Pre-12c (ROWNUM)
SELECT * FROM (
    SELECT u.*, ROWNUM rn FROM (
        SELECT id, email, display_name, created_at
        FROM users
        WHERE status = 'active'
        ORDER BY created_at DESC
    ) u
    WHERE ROWNUM <= :offset + :limit
)
WHERE rn > :offset;
```

### Analytic Functions

```sql
-- Running totals and rankings
SELECT
    id,
    email,
    order_count,
    RANK() OVER (ORDER BY order_count DESC) as rank,
    SUM(order_count) OVER (ORDER BY created_at ROWS UNBOUNDED PRECEDING) as cumulative_orders,
    LAG(order_count) OVER (ORDER BY created_at) as prev_order_count
FROM user_stats;

-- Partitioned analytics
SELECT
    region,
    user_id,
    total_spent,
    RATIO_TO_REPORT(total_spent) OVER (PARTITION BY region) as region_share
FROM user_spending;
```

### Bulk Operations

```sql
-- BULK COLLECT for efficient reads
DECLARE
    TYPE user_table IS TABLE OF users%ROWTYPE;
    v_users user_table;
BEGIN
    SELECT * BULK COLLECT INTO v_users
    FROM users
    WHERE status = 'pending'
    AND created_at < SYSTIMESTAMP - INTERVAL '7' DAY;

    FORALL i IN 1..v_users.COUNT
        UPDATE users SET status = 'inactive'
        WHERE id = v_users(i).id;

    COMMIT;
END;
/

-- MERGE for upsert
MERGE INTO users target
USING (SELECT :email AS email, :name AS display_name FROM dual) source
ON (target.email = source.email)
WHEN MATCHED THEN
    UPDATE SET display_name = source.display_name, updated_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN
    INSERT (id, email, display_name, status, created_at)
    VALUES (SYS_GUID(), source.email, source.display_name, 'pending', SYSTIMESTAMP);
```

### Hints and Performance

```sql
-- Index hints
SELECT /*+ INDEX(u idx_users_status_created) */
    id, email, display_name
FROM users u
WHERE status = 'active'
ORDER BY created_at DESC;

-- Parallel execution
SELECT /*+ PARALLEL(u, 4) */
    region, COUNT(*) as user_count
FROM users u
GROUP BY region;
```

## Patterns to Avoid
- ❌ SELECT * in production
- ❌ Not using bind variables
- ❌ Missing exception handling in PL/SQL
- ❌ Cartesian joins without WHERE

## Verification Checklist
- [ ] Bind variables for all parameters
- [ ] BULK COLLECT for large datasets
- [ ] Proper exception handling
- [ ] Execution plan reviewed
- [ ] Indexes match query patterns
