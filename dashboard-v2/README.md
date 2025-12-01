# BAZINGA Dashboard v2.0

> ⚠️ **EXPERIMENTAL**: This dashboard is under initial development and is not yet reliable.
> It provides reporting/monitoring only - skipping it has **no impact** on BAZINGA's core
> multi-agent orchestration functionality.
>
> - **Not installed by default** - opt-in with: `bazinga init my-project --dashboard`
> - **Install later:** `bazinga setup-dashboard`
> - **Update:** `bazinga update --dashboard`

Modern, real-time orchestration monitoring dashboard built with Next.js 14.

## Features

- **Real-time Updates** - Live session monitoring with auto-refresh
- **Session Explorer** - Browse and analyze all orchestration sessions
- **Task Management** - View task groups, progress, and revisions
- **Token Analytics** - Track token usage and costs by agent
- **Quality Metrics** - Monitor success criteria and quality gates
- **AI Insights** - Automated pattern detection and recommendations
- **Dark/Light Theme** - Customizable appearance

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Database**: SQLite with Drizzle ORM
- **API**: tRPC with TanStack Query
- **State**: Zustand (coming soon)

## Getting Started

### Prerequisites

- Node.js 18+
- Existing `bazinga/bazinga.db` database

### Installation

```bash
# Navigate to dashboard directory
cd dashboard-v2

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
dashboard-v2/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── api/trpc/          # tRPC API handler
│   │   ├── sessions/          # Session pages
│   │   ├── analytics/         # Analytics page
│   │   ├── settings/          # Settings page
│   │   └── page.tsx           # Home dashboard
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── dashboard/         # Dashboard-specific components
│   │   └── layout/            # Layout components (sidebar, header)
│   ├── lib/
│   │   ├── db/                # Drizzle ORM schema and client
│   │   ├── trpc/              # tRPC server and routers
│   │   └── utils/             # Utility functions
│   └── types/                 # TypeScript type definitions
├── package.json
├── tailwind.config.ts
├── drizzle.config.ts
└── next.config.js
```

## Database

The dashboard connects to the existing `bazinga/bazinga.db` SQLite database in read-only mode. It visualizes data from:

- `sessions` - Orchestration sessions
- `orchestration_logs` - Agent activity logs
- `task_groups` - Task group status and progress
- `token_usage` - Token consumption tracking
- `success_criteria` - Quality gate criteria
- `state_snapshots` - Historical state data

## Configuration

Environment variables (optional):

```env
DATABASE_URL=../bazinga/bazinga.db
```

## Development

```bash
# Run development server with hot reload
npm run dev

# Type checking
npx tsc --noEmit

# Lint
npm run lint
```

## License

MIT
