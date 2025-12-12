# Data Model: Context Engineering System

**Feature**: Context Engineering System
**Date**: 2025-12-12
**Status**: Design

## Overview

This document defines the data model for the context engineering system. All tables are stored in `bazinga/bazinga.db` and accessed via the `bazinga-db` skill.

## Entity Relationship Diagram

```
┌─────────────────────┐     ┌─────────────────────┐
│  context_packages   │     │   error_patterns    │
├─────────────────────┤     ├─────────────────────┤
│ package_id (PK)     │     │ pattern_hash (PK)   │
│ session_id (FK)     │     │ project_id          │
│ group_id            │     │ signature_json      │
│ priority            │     │ solution            │
│ summary             │     │ confidence          │
│ content_path        │     │ occurrences         │
│ created_at          │     │ lang                │
└─────────────────────┘     │ last_seen           │
          │                 │ ttl_days            │
          │                 └─────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│  consumption_scope  │     │     strategies      │
├─────────────────────┤     ├─────────────────────┤
│ scope_id (PK)       │     │ strategy_id (PK)    │
│ session_id (FK)     │     │ project_id          │
│ group_id            │     │ topic               │
│ agent_type          │     │ insight             │
│ iteration           │     │ helpfulness         │
│ package_id (FK)     │     │ lang                │
│ consumed_at         │     │ framework           │
└─────────────────────┘     │ last_seen           │
                            └─────────────────────┘
```

## Tables

### 1. context_packages (Extended)

Stores research files, investigation findings, and artifacts passed to agents.

**Schema Extension** (add to existing table):

```sql
-- Add columns to existing context_packages table
ALTER TABLE context_packages ADD COLUMN priority TEXT DEFAULT 'medium';
ALTER TABLE context_packages ADD COLUMN summary TEXT;

-- Create index for relevance ranking
CREATE INDEX idx_packages_priority ON context_packages(session_id, priority, created_at DESC);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| package_id | TEXT | PRIMARY KEY | UUID for the package |
| session_id | TEXT | NOT NULL | Orchestration session reference |
| group_id | TEXT | | Task group (null = session-wide) |
| priority | TEXT | DEFAULT 'medium' | critical/high/medium/low |
| summary | TEXT | | Brief description for ranking display |
| content_path | TEXT | NOT NULL | Path to artifact file |
| created_at | TEXT | NOT NULL | ISO timestamp |

**Priority Values:**
- `critical` - Must always be included (errors, blockers)
- `high` - Include if budget allows (research findings)
- `medium` - Default for most packages
- `low` - Include only if ample budget

### 2. error_patterns (New)

Captures error signatures and solutions for learning.

```sql
CREATE TABLE error_patterns (
    pattern_hash TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    signature_json TEXT NOT NULL,
    solution TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    occurrences INTEGER DEFAULT 1,
    lang TEXT,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ttl_days INTEGER DEFAULT 90
);

CREATE INDEX idx_patterns_project ON error_patterns(project_id, lang);
CREATE INDEX idx_patterns_ttl ON error_patterns(last_seen, ttl_days);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| pattern_hash | TEXT | PRIMARY KEY | SHA256 of normalized signature |
| project_id | TEXT | NOT NULL | Project identifier for isolation |
| signature_json | TEXT | NOT NULL | Structured error signature |
| solution | TEXT | NOT NULL | How the error was resolved |
| confidence | REAL | DEFAULT 0.5 | 0.0-1.0, increases with successful matches |
| occurrences | INTEGER | DEFAULT 1 | Times this pattern was seen |
| lang | TEXT | | Programming language (optional) |
| last_seen | TEXT | NOT NULL | Last occurrence timestamp |
| created_at | TEXT | NOT NULL | First occurrence timestamp |
| ttl_days | INTEGER | DEFAULT 90 | Days before automatic cleanup |

**Signature JSON Structure:**
```json
{
  "error_type": "ModuleNotFoundError",
  "message_pattern": "No module named '...'",
  "context_hints": ["import statement", "tsconfig"],
  "stack_pattern": ["file.py:123", "module.py:456"]
}
```

**Confidence Rules:**
- Initial: 0.5
- Each successful match: +0.1 (max 1.0)
- Each false positive report: -0.2 (min 0.1)
- Below 0.3: Don't inject, keep for observation

### 3. strategies (New)

Stores successful approaches extracted from completed tasks.

```sql
CREATE TABLE strategies (
    strategy_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    insight TEXT NOT NULL,
    helpfulness INTEGER DEFAULT 0,
    lang TEXT,
    framework TEXT,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_strategies_project ON strategies(project_id, framework);
CREATE INDEX idx_strategies_topic ON strategies(topic);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| strategy_id | TEXT | PRIMARY KEY | UUID |
| project_id | TEXT | NOT NULL | Project identifier |
| topic | TEXT | NOT NULL | Category (e.g., "React Native offline") |
| insight | TEXT | NOT NULL | The learned approach |
| helpfulness | INTEGER | DEFAULT 0 | Incremented when strategy helps |
| lang | TEXT | | Programming language |
| framework | TEXT | | Framework/library context |
| last_seen | TEXT | NOT NULL | Last time strategy was referenced |
| created_at | TEXT | NOT NULL | When strategy was captured |

### 4. consumption_scope (New)

Tracks which packages were consumed per session/group/agent/iteration.

```sql
CREATE TABLE consumption_scope (
    scope_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    package_id TEXT NOT NULL,
    consumed_at TEXT NOT NULL,
    FOREIGN KEY (package_id) REFERENCES context_packages(package_id)
);

CREATE INDEX idx_consumption_session ON consumption_scope(session_id, group_id, agent_type);
CREATE UNIQUE INDEX idx_consumption_unique ON consumption_scope(session_id, group_id, agent_type, iteration, package_id);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| scope_id | TEXT | PRIMARY KEY | UUID |
| session_id | TEXT | NOT NULL | Orchestration session |
| group_id | TEXT | NOT NULL | Task group |
| agent_type | TEXT | NOT NULL | developer/qa_expert/tech_lead |
| iteration | INTEGER | NOT NULL | Retry iteration (0 = first attempt) |
| package_id | TEXT | NOT NULL, FK | Package that was consumed |
| consumed_at | TEXT | NOT NULL | When consumption occurred |

**Purpose:** Enables iteration-aware tracking so the same package isn't marked "consumed" across retries, allowing fresh agents to see relevant context.

## Validation Rules

### Error Pattern Validation

1. `signature_json` MUST be valid JSON
2. `confidence` MUST be between 0.0 and 1.0
3. `ttl_days` MUST be > 0
4. `solution` MUST NOT contain secrets (redacted at capture)

### Strategy Validation

1. `insight` SHOULD be < 500 characters
2. `topic` SHOULD use consistent naming (lowercase, hyphenated)
3. `helpfulness` MUST be >= 0

### Consumption Scope Validation

1. Combination of (session_id, group_id, agent_type, iteration, package_id) MUST be unique
2. `iteration` MUST be >= 0

## Migrations

### Migration 001: Add Context Engineering Tables

```sql
-- Enable WAL mode for parallel access
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Extend context_packages
ALTER TABLE context_packages ADD COLUMN priority TEXT DEFAULT 'medium';
ALTER TABLE context_packages ADD COLUMN summary TEXT;
CREATE INDEX IF NOT EXISTS idx_packages_priority ON context_packages(session_id, priority, created_at DESC);

-- Create error_patterns table
CREATE TABLE IF NOT EXISTS error_patterns (
    pattern_hash TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    signature_json TEXT NOT NULL,
    solution TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    occurrences INTEGER DEFAULT 1,
    lang TEXT,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ttl_days INTEGER DEFAULT 90
);
CREATE INDEX IF NOT EXISTS idx_patterns_project ON error_patterns(project_id, lang);

-- Create strategies table
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    insight TEXT NOT NULL,
    helpfulness INTEGER DEFAULT 0,
    lang TEXT,
    framework TEXT,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strategies_project ON strategies(project_id, framework);

-- Create consumption_scope table
CREATE TABLE IF NOT EXISTS consumption_scope (
    scope_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    package_id TEXT NOT NULL,
    consumed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_consumption_session ON consumption_scope(session_id, group_id, agent_type);
```

## State Transitions

### Error Pattern Lifecycle

```
┌─────────────┐    fail→succeed    ┌─────────────┐
│   (none)    │ ─────────────────► │   ACTIVE    │
└─────────────┘                    └──────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │ match + success     │ match + failure     │ TTL expired
                    ▼                     ▼                     ▼
              ┌───────────┐        ┌───────────┐        ┌───────────┐
              │ CONFIRMED │        │  DEMOTED  │        │  EXPIRED  │
              │ conf +0.1 │        │ conf -0.2 │        │ (deleted) │
              └───────────┘        └───────────┘        └───────────┘
```

### Context Package Priority

```
┌─────────┐    error/blocker    ┌──────────┐
│  MEDIUM │ ─────────────────►  │ CRITICAL │
└────┬────┘                     └──────────┘
     │
     │ research finding
     ▼
┌─────────┐    resolved/stale   ┌─────────┐
│  HIGH   │ ─────────────────►  │   LOW   │
└─────────┘                     └─────────┘
```
