---
name: sqlserver
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [sql]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# SQL Server Engineering Expertise

## Specialist Profile
SQL Server specialist building enterprise database solutions. Expert in T-SQL, query optimization, and SQL Server features.

## Implementation Guidelines

### Stored Procedures

```sql
-- Stored procedure with error handling
CREATE OR ALTER PROCEDURE dbo.CreateUser
    @Email NVARCHAR(255),
    @DisplayName NVARCHAR(100),
    @UserId UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Check for duplicate
        IF EXISTS (SELECT 1 FROM dbo.Users WHERE Email = LOWER(@Email))
        BEGIN
            RAISERROR('Email already exists', 16, 1);
            RETURN;
        END

        SET @UserId = NEWID();

        INSERT INTO dbo.Users (Id, Email, DisplayName, Status, CreatedAt)
        VALUES (@UserId, LOWER(@Email), @DisplayName, 'pending', SYSUTCDATETIME());

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO
```

### Pagination

```sql
-- SQL Server 2012+ (OFFSET/FETCH)
SELECT Id, Email, DisplayName, CreatedAt
FROM dbo.Users
WHERE Status = 'active'
ORDER BY CreatedAt DESC
OFFSET @Offset ROWS FETCH NEXT @Limit ROWS ONLY;

-- With total count (efficient)
WITH FilteredUsers AS (
    SELECT Id, Email, DisplayName, CreatedAt,
           COUNT(*) OVER() AS TotalCount
    FROM dbo.Users
    WHERE Status = 'active'
)
SELECT Id, Email, DisplayName, CreatedAt, TotalCount
FROM FilteredUsers
ORDER BY CreatedAt DESC
OFFSET @Offset ROWS FETCH NEXT @Limit ROWS ONLY;
```

### Window Functions

```sql
-- Rankings and running totals
SELECT
    Id,
    Email,
    OrderCount,
    RANK() OVER (ORDER BY OrderCount DESC) AS Rank,
    DENSE_RANK() OVER (ORDER BY OrderCount DESC) AS DenseRank,
    SUM(OrderCount) OVER (ORDER BY CreatedAt ROWS UNBOUNDED PRECEDING) AS RunningTotal,
    LAG(OrderCount) OVER (ORDER BY CreatedAt) AS PrevOrderCount,
    LEAD(OrderCount) OVER (ORDER BY CreatedAt) AS NextOrderCount
FROM dbo.UserStats;

-- Partitioned calculations
SELECT
    Region,
    UserId,
    TotalSpent,
    TotalSpent * 100.0 / SUM(TotalSpent) OVER (PARTITION BY Region) AS RegionPercent
FROM dbo.UserSpending;
```

### MERGE for Upsert

```sql
MERGE dbo.Users AS target
USING (SELECT @Email AS Email, @DisplayName AS DisplayName) AS source
ON target.Email = source.Email
WHEN MATCHED THEN
    UPDATE SET
        DisplayName = source.DisplayName,
        UpdatedAt = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
    INSERT (Id, Email, DisplayName, Status, CreatedAt)
    VALUES (NEWID(), source.Email, source.DisplayName, 'pending', SYSUTCDATETIME());
```

### JSON Support

```sql
-- SQL Server 2016+
-- Store and query JSON
ALTER TABLE dbo.Users ADD Preferences NVARCHAR(MAX);

-- Query JSON
SELECT Id, Email,
    JSON_VALUE(Preferences, '$.theme') AS Theme,
    JSON_VALUE(Preferences, '$.notifications.email') AS EmailNotifications
FROM dbo.Users
WHERE ISJSON(Preferences) = 1
  AND JSON_VALUE(Preferences, '$.theme') = 'dark';

-- Update JSON
UPDATE dbo.Users
SET Preferences = JSON_MODIFY(Preferences, '$.theme', 'light')
WHERE Id = @UserId;
```

### Table-Valued Parameters

```sql
-- Create type
CREATE TYPE dbo.UserIdList AS TABLE (Id UNIQUEIDENTIFIER);
GO

-- Use in procedure
CREATE PROCEDURE dbo.GetUsersByIds
    @UserIds dbo.UserIdList READONLY
AS
BEGIN
    SELECT u.*
    FROM dbo.Users u
    INNER JOIN @UserIds ids ON u.Id = ids.Id;
END;
GO
```

## Patterns to Avoid
- ❌ NOLOCK hints without understanding
- ❌ Cursors for set-based operations
- ❌ SELECT * in production
- ❌ Missing SET NOCOUNT ON

## Verification Checklist
- [ ] SET NOCOUNT ON in procedures
- [ ] Proper error handling (TRY/CATCH)
- [ ] Parameterized queries
- [ ] Execution plan reviewed
- [ ] Appropriate indexes
