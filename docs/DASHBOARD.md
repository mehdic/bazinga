# BAZINGA Dashboard (Experimental)

> **Status:** Experimental - Under active development, not yet reliable for production use.

The BAZINGA Dashboard provides a visual interface for monitoring orchestration sessions, viewing agent interactions, and tracking project health metrics.

---

## Overview

The dashboard is a Next.js application that reads from the BAZINGA SQLite database (`bazinga/bazinga.db`) to display real-time orchestration progress.

**Key Features:**
- Session list with status indicators
- Task group progress tracking
- Agent interaction timeline
- Reasoning log viewer
- Success criteria tracking

---

## Installation

The dashboard is **not installed by default**. To add it to your project:

### During Project Initialization

```bash
# New project with dashboard
bazinga init my-project --dashboard

# Existing directory with dashboard
bazinga init --here --dashboard
```

### Add to Existing Project

```bash
bazinga setup-dashboard
```

---

## Starting the Dashboard

### Option 1: Using the Start Script

```bash
# From your project root
./bazinga/scripts/start-dashboard.sh
```

**Windows:**
```powershell
.\bazinga\scripts\start-dashboard.ps1
```

### Option 2: Manual Start

```bash
cd bazinga/dashboard-v2
npm install  # First time only
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

---

## Features

### Session Overview

View all orchestration sessions with:
- Session ID and creation time
- Status (planning, in_progress, completed, failed)
- Mode (simple or parallel)
- Original request summary

### Task Groups

For each session, see:
- Task group ID and description
- Current status and assigned agent
- Revision count
- Specialization paths applied

### Agent Timeline

Visual timeline showing:
- Which agents ran and when
- Agent status outputs
- Routing decisions

### Reasoning Logs

View agent decision-making:
- Understanding phase (how agents interpreted tasks)
- Strategy phase (how they planned execution)
- Completion phase (what they accomplished)
- Confidence levels

### Success Criteria

Track success criteria:
- Criteria descriptions
- Met/unmet status
- Evidence captured

---

## Architecture

```
dashboard-v2/
├── src/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   ├── lib/
│   │   ├── db/          # Drizzle ORM schema
│   │   └── trpc/        # tRPC routers
│   └── types/           # TypeScript interfaces
├── package.json
└── drizzle.config.ts
```

**Tech Stack:**
- Next.js 14 (App Router)
- tRPC for type-safe API
- Drizzle ORM for database access
- Tailwind CSS for styling
- SQLite (reads from bazinga.db)

---

## Known Limitations

Since the dashboard is experimental:

1. **Not real-time** - Requires page refresh to see updates
2. **Read-only** - Cannot modify sessions or tasks
3. **Single database** - Only reads from `bazinga/bazinga.db`
4. **No authentication** - Runs locally only
5. **Schema coupling** - Must match bazinga-db schema version

---

## Troubleshooting

### "Database not found"

Ensure an orchestration session has run to create `bazinga/bazinga.db`.

### "Table does not exist"

The dashboard schema may be out of sync with the database. Run a fresh orchestration to initialize the database with the current schema.

### "Port 3000 in use"

```bash
# Use a different port
npm run dev -- -p 3001
```

### Dashboard shows no data

1. Check that `bazinga/bazinga.db` exists
2. Verify a session has been created (run an orchestration first)
3. Check browser console for errors

---

## Development

### Adding New Features

1. Update Drizzle schema in `src/lib/db/schema.ts`
2. Add TypeScript types in `src/types/index.ts`
3. Create tRPC queries in `src/lib/trpc/routers/`
4. Build UI components

### Schema Sync

The dashboard schema must stay in sync with `bazinga-db` skill. See `.claude/claude.md` section on Dashboard-Schema Synchronization.

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - State management details
- [SKILLS.md](SKILLS.md) - bazinga-db skill reference
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Project structure

---

**Version:** 1.1.0
**Last Updated:** 2025-12-30
**Status:** Experimental
