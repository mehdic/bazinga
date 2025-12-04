---
name: postgresql
type: database
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# PostgreSQL Engineering Expertise

## Specialist Profile
PostgreSQL specialist optimizing relational databases. Expert in query optimization, indexing strategies, and advanced features.

## Implementation Guidelines

### Migrations

```sql
-- migrations/001_create_users.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_status_check CHECK (status IN ('active', 'inactive', 'pending'))
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_status ON users (status) WHERE status = 'active';
CREATE INDEX idx_users_created_at ON users (created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Advanced Queries

```sql
-- Pagination with cursor
SELECT id, email, display_name, created_at
FROM users
WHERE created_at < $1  -- cursor
  AND status = 'active'
ORDER BY created_at DESC
LIMIT 20;

-- Full-text search
ALTER TABLE users ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(display_name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(email, '')), 'B')
    ) STORED;

CREATE INDEX idx_users_search ON users USING GIN (search_vector);

SELECT * FROM users
WHERE search_vector @@ plainto_tsquery('english', $1);

-- UPSERT
INSERT INTO users (email, display_name, status)
VALUES ($1, $2, $3)
ON CONFLICT (email)
DO UPDATE SET
    display_name = EXCLUDED.display_name,
    updated_at = NOW()
RETURNING *;
```

### Window Functions

```sql
-- Rank users by activity
SELECT
    id,
    email,
    order_count,
    RANK() OVER (ORDER BY order_count DESC) as rank,
    PERCENT_RANK() OVER (ORDER BY order_count DESC) as percentile
FROM (
    SELECT u.id, u.email, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id
) sub;

-- Running totals
SELECT
    date_trunc('day', created_at) as day,
    COUNT(*) as daily_signups,
    SUM(COUNT(*)) OVER (ORDER BY date_trunc('day', created_at)) as cumulative
FROM users
GROUP BY 1
ORDER BY 1;
```

### JSON Operations

```sql
-- Store and query JSONB
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';

CREATE INDEX idx_users_preferences ON users USING GIN (preferences);

-- Query nested JSON
SELECT * FROM users
WHERE preferences @> '{"notifications": {"email": true}}';

-- Update nested value
UPDATE users
SET preferences = jsonb_set(preferences, '{theme}', '"dark"')
WHERE id = $1;
```

## Patterns to Avoid
- ❌ SELECT * in production
- ❌ Missing indexes on foreign keys
- ❌ Unbounded queries without LIMIT
- ❌ N+1 in application code

## Verification Checklist
- [ ] Proper indexes for queries
- [ ] Parameterized queries
- [ ] Appropriate data types
- [ ] Constraints for data integrity
- [ ] EXPLAIN ANALYZE for complex queries
