# Mini Session Dashboard: Design Analysis

**Date:** 2025-12-25
**Context:** Need a minimal but effective dashboard to monitor BAZINGA orchestration sessions in real-time
**Decision:** Pending user approval
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The full dashboard (dashboard-v2) is complex and may have issues. We need a **minimal, effective** alternative that:

1. Finds and displays the current active session
2. Shows orchestrator logs in chronological order
3. Lists subagents (spawned agents) in a table by spawn order
4. Allows clicking on any subagent to see its reasoning/logs
5. Auto-refreshes every 5 seconds
6. Shows subagent statuses clearly

**Key Constraint:** Must be simple enough that it "just works" without complex setup.

---

## Available Data Sources

From `bazinga/bazinga.db` (SQLite), we can query:

| Table | What It Provides | Key Fields |
|-------|------------------|------------|
| `sessions` | Active/recent sessions | `session_id`, `status`, `mode`, `start_time` |
| `orchestration_logs` | All agent interactions + reasoning | `agent_type`, `agent_id`, `content`, `timestamp`, `log_type`, `reasoning_phase` |
| `task_groups` | Task assignments | `id`, `status`, `assigned_to`, `name` |
| `token_usage` | Token consumption per agent | `agent_type`, `tokens_estimated` |

**Critical Insight:** The `orchestration_logs` table has both:
- `log_type='interaction'` - Normal agent responses
- `log_type='reasoning'` - Agent reasoning (what we want to drill into)

---

## Solution Options

### Option A: Textual TUI (Terminal UI)

**Technology:** Python + Textual library (single file)

**Architecture:**
```
mini_dashboard.py (single file, ~300 lines)
    ├── SQLite queries (direct to bazinga.db)
    ├── Textual app with:
    │   ├── Header: Current session info
    │   ├── DataTable: Subagents (clickable rows)
    │   ├── Log panel: Scrolling orchestrator logs
    │   └── Detail panel: Selected agent's reasoning
    └── Auto-refresh every 5s via set_interval
```

**Pros:**
- Terminal-based (runs alongside orchestration in same terminal context)
- Mouse click support for selecting agents
- Rich table rendering with colors/status badges
- Live refresh built-in
- Single file, no build step
- Works offline
- No port conflicts

**Cons:**
- Requires `textual` dependency (~pip install textual)
- Terminal only (some users prefer browser)
- Limited screen real estate

**Example Flow:**
```
┌─ Mini Session Dashboard ──────────────────────────────┐
│ Session: bazinga_20251225_143022 | Status: ACTIVE    │
├──────────────────────────────────────────────────────┤
│ Subagents (click to select)                          │
│ ┌──────┬───────────┬──────────┬─────────────────────┐│
│ │ # │ Agent     │ Status   │ Task Group         ││
│ ├──────┼───────────┼──────────┼─────────────────────┤│
│ │ 1 │ PM        │ ✅ Done  │ planning           ││
│ │ 2 │ Developer │ 🔄 Active│ CALC               ││
│ │ 3 │ QA Expert │ ⏳ Pending│ -                  ││
│ └──────┴───────────┴──────────┴─────────────────────┘│
├──────────────────────────────────────────────────────┤
│ Orchestrator Logs (recent)                           │
│ [14:30:22] PM → Analyzed requirements, mode=simple   │
│ [14:30:45] Developer → Implementing calculator...    │
│ [14:31:02] Developer → Phase 1 complete             │
├──────────────────────────────────────────────────────┤
│ Selected: Developer | Reasoning (2 entries)          │
│ ────────────────────────────────────────────────────│
│ [understanding] Analyzing Simple Calculator spec...  │
│ Confidence: high | Files: tests/integration/...      │
│ ────────────────────────────────────────────────────│
│ [completion] Implemented all operations...           │
│ Confidence: high | Tests: 51 passing                 │
└──────────────────────────────────────────────────────┘
```

---

### Option B: Flask + Vanilla HTML (Web-based)

**Technology:** Python Flask + single HTML file (2 files total)

**Architecture:**
```
mini_dashboard/
├── server.py (~150 lines)
│   ├── Flask app
│   ├── SQLite queries
│   └── JSON API endpoints
└── static/index.html (~200 lines)
    ├── Vanilla JS (no frameworks)
    ├── setInterval polling (5s)
    └── Simple CSS for styling
```

**Pros:**
- Browser-based (familiar UI paradigm)
- Works on any device with a browser
- More screen space available
- Easy to share (just open URL)
- Standard HTML/CSS/JS (no learning curve)

**Cons:**
- Needs to run a server (port 5000 or similar)
- Potential port conflicts
- Two files instead of one
- Polling-based (not true real-time)
- May have CORS issues if accessed remotely

**Example HTML structure:**
```html
<div id="app">
  <header>Session: <span id="session-id"></span></header>

  <table id="agents-table">
    <tr onclick="selectAgent('developer_1')">...</tr>
  </table>

  <div id="logs-panel"><!-- Scrolling logs --></div>

  <div id="reasoning-panel"><!-- Selected agent's reasoning --></div>
</div>

<script>
  setInterval(fetchData, 5000);
  function selectAgent(agentId) { ... }
</script>
```

---

### Option C: Single Python Script with HTTP Server (Hybrid)

**Technology:** Python only - http.server + embedded HTML

**Architecture:**
```
mini_dashboard.py (single file, ~400 lines)
    ├── Embedded HTML template (as string)
    ├── SQLite queries
    ├── http.server for serving
    └── JSON endpoints
```

**Pros:**
- Single file (like Option A)
- Browser-based (like Option B)
- No external dependencies (uses stdlib)
- Simple to run: `python mini_dashboard.py`

**Cons:**
- HTML embedded in Python (harder to edit)
- `http.server` is basic (no routing helpers)
- Mixing concerns (backend + frontend in one file)

---

## Critical Analysis

### Recommendation: **Option B (Flask + Vanilla HTML)**

**Rationale:**

1. **True clickable interface**
   - Browser-based = familiar UX for clicking and exploring
   - Click on any agent row to expand details
   - Click on groups, logs, reasoning entries
   - No terminal mouse support quirks

2. **Better visual space**
   - Full browser window for data display
   - Scrollable panels that feel natural
   - Easy to resize and arrange windows

3. **Simple polling works fine**
   - 5-second setInterval is reliable and predictable
   - No WebSocket complexity needed for this use case
   - Browser handles rendering efficiently

4. **Minimal but effective**
   - Two small files: server.py (~200 lines) + index.html (~250 lines)
   - No npm/node_modules, no build step
   - Flask is likely already installed (common Python dep)

5. **Easy to extend later**
   - Add more panels/tabs as needed
   - CSS is easy to customize
   - Could add dark mode with a few lines

### Why Not Option A (Textual TUI)?

- Terminal mouse support is inconsistent across terminals
- Users prefer browser for "click around and explore" workflows
- Less visual real estate than a browser window

### Why Not Option C (Hybrid)?

- HTML embedded in Python is hard to maintain
- No advantage over two clean, separate files

---

## Implementation Details

### Architecture

```
mini-dashboard/
├── server.py       (~200 lines) - Flask API + static serving
└── index.html      (~300 lines) - Vanilla JS + CSS, no build step
```

### Flask Server (server.py)

```python
#!/usr/bin/env python3
"""Mini Session Dashboard - Minimal Flask server for BAZINGA monitoring."""

import os
import re
import json
import sqlite3
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')
DB_PATH = os.environ.get('BAZINGA_DB_PATH', 'bazinga/bazinga.db')


def get_db():
    """Get read-only database connection with busy timeout."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=2000")
    return conn


def parse_status(content: str) -> str:
    """Extract status from agent response content."""
    if not content:
        return 'UNKNOWN'
    try:
        # Look for JSON with status field
        matches = re.findall(r'\{[^{}]+\}', content)
        for m in reversed(matches):
            data = json.loads(m)
            if 'status' in data:
                return data['status']
    except:
        pass
    # Fallback regex
    match = re.search(r'status["\s:]+([A-Z_]+)', content, re.I)
    return match.group(1).upper() if match else 'UNKNOWN'


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/sessions')
def get_sessions():
    """Get recent sessions (active first)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM sessions
        ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END,
                 COALESCE(created_at, start_time) DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/session/<session_id>/agents')
def get_agents(session_id):
    """Get spawned agents with parsed status."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            l.agent_type, l.agent_id, l.content, l.timestamp,
            (SELECT COUNT(*) FROM orchestration_logs l2
             WHERE l2.session_id = l.session_id
               AND l2.agent_type = l.agent_type
               AND COALESCE(l2.agent_id,'') = COALESCE(l.agent_id,'')
               AND l2.log_type = 'reasoning') as reasoning_count,
            (SELECT SUM(tokens_estimated) FROM token_usage t
             WHERE t.session_id = l.session_id
               AND t.agent_type = l.agent_type) as tokens
        FROM orchestration_logs l
        WHERE l.session_id = ?
          AND l.id = (
              SELECT MAX(id) FROM orchestration_logs l2
              WHERE l2.session_id = l.session_id
                AND l2.agent_type = l.agent_type
                AND COALESCE(l2.agent_id,'') = COALESCE(l.agent_id,''))
        ORDER BY (SELECT MIN(timestamp) FROM orchestration_logs l3
                  WHERE l3.session_id = l.session_id
                    AND l3.agent_type = l.agent_type) ASC
    """, (session_id,)).fetchall()
    conn.close()

    agents = []
    for r in rows:
        d = dict(r)
        d['status'] = parse_status(d.get('content', ''))
        del d['content']  # Don't send full content
        agents.append(d)
    return jsonify(agents)


@app.route('/api/session/<session_id>/groups')
def get_groups(session_id):
    """Get task groups."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, status, assigned_to, complexity, revision_count
        FROM task_groups WHERE session_id = ? ORDER BY created_at
    """, (session_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/session/<session_id>/logs')
def get_logs(session_id):
    """Get recent orchestration logs."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, timestamp, agent_type, agent_id,
               SUBSTR(content, 1, 500) as content_preview
        FROM orchestration_logs
        WHERE session_id = ? AND log_type = 'interaction'
        ORDER BY timestamp DESC LIMIT 100
    """, (session_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/session/<session_id>/agent/<agent_type>/reasoning')
def get_reasoning(session_id, agent_type):
    """Get reasoning entries for an agent."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, timestamp, reasoning_phase, confidence_level,
               content, group_id, references_json
        FROM orchestration_logs
        WHERE session_id = ? AND agent_type = ? AND log_type = 'reasoning'
        ORDER BY timestamp ASC LIMIT 50
    """, (session_id, agent_type)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"🚀 Mini Dashboard running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
```

### HTML Frontend (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BAZINGA Mini Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; }
    .container { display: grid; grid-template-columns: 300px 1fr; height: 100vh; }

    /* Sidebar */
    .sidebar { background: #16213e; padding: 1rem; overflow-y: auto; }
    .sidebar h2 { font-size: 0.9rem; color: #888; margin: 1rem 0 0.5rem; }
    .session-item, .group-item, .agent-row {
      padding: 0.5rem; margin: 0.25rem 0; background: #1a1a2e;
      border-radius: 4px; cursor: pointer; transition: background 0.2s;
    }
    .session-item:hover, .group-item:hover, .agent-row:hover { background: #0f3460; }
    .session-item.active, .agent-row.selected { background: #e94560; }
    .status-badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; }
    .status-active { background: #4ade80; color: #000; }
    .status-completed { background: #60a5fa; color: #000; }
    .status-failed { background: #f87171; color: #000; }

    /* Main content */
    .main { display: flex; flex-direction: column; overflow: hidden; }
    .header { background: #0f3460; padding: 1rem; display: flex; justify-content: space-between; }
    .header h1 { font-size: 1.2rem; }
    .refresh-indicator { color: #4ade80; font-size: 0.8rem; }

    /* Panels */
    .panels { flex: 1; display: grid; grid-template-rows: 1fr 1fr; overflow: hidden; }
    .panel { border-top: 1px solid #333; overflow-y: auto; padding: 1rem; }
    .panel h3 { font-size: 0.9rem; color: #888; margin-bottom: 0.5rem; position: sticky; top: 0; background: #1a1a2e; }

    /* Logs */
    .log-entry { padding: 0.5rem; border-bottom: 1px solid #333; font-family: monospace; font-size: 0.85rem; }
    .log-entry .time { color: #888; }
    .log-entry .agent { color: #4ade80; }

    /* Reasoning */
    .reasoning-entry { background: #16213e; padding: 1rem; margin: 0.5rem 0; border-radius: 4px; }
    .reasoning-entry .phase { color: #e94560; font-weight: bold; }
    .reasoning-entry .confidence { font-size: 0.8rem; color: #888; }
    .reasoning-entry .content { margin-top: 0.5rem; white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="container">
    <div class="sidebar">
      <h2>Sessions</h2>
      <div id="sessions"></div>
      <h2>Task Groups</h2>
      <div id="groups"></div>
      <h2>Agents (click to view)</h2>
      <div id="agents"></div>
    </div>
    <div class="main">
      <div class="header">
        <h1>🎯 BAZINGA Mini Dashboard</h1>
        <span class="refresh-indicator" id="refresh-status">Auto-refresh: 5s</span>
      </div>
      <div class="panels">
        <div class="panel" id="logs-panel">
          <h3>📋 Orchestration Logs (recent)</h3>
          <div id="logs"></div>
        </div>
        <div class="panel" id="reasoning-panel">
          <h3>🧠 Agent Reasoning</h3>
          <div id="reasoning">Select an agent to view reasoning</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentSession = null;
    let selectedAgent = null;

    async function fetchJSON(url) {
      const res = await fetch(url);
      return res.json();
    }

    async function loadSessions() {
      const sessions = await fetchJSON('/api/sessions');
      const el = document.getElementById('sessions');
      el.innerHTML = sessions.map(s => `
        <div class="session-item ${s.session_id === currentSession ? 'active' : ''}"
             onclick="selectSession('${s.session_id}')">
          <div>${s.session_id.slice(-15)}</div>
          <span class="status-badge status-${s.status}">${s.status}</span>
        </div>
      `).join('');

      // Auto-select first active session
      if (!currentSession && sessions.length) {
        selectSession(sessions[0].session_id);
      }
    }

    async function selectSession(sessionId) {
      currentSession = sessionId;
      selectedAgent = null;
      document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
      event?.target?.closest('.session-item')?.classList.add('active');
      await Promise.all([loadGroups(), loadAgents(), loadLogs()]);
      document.getElementById('reasoning').innerHTML = 'Select an agent to view reasoning';
    }

    async function loadGroups() {
      if (!currentSession) return;
      const groups = await fetchJSON(`/api/session/${currentSession}/groups`);
      document.getElementById('groups').innerHTML = groups.map(g => `
        <div class="group-item">
          <strong>${g.id}</strong>: ${g.name || 'Unnamed'}
          <span class="status-badge status-${g.status === 'completed' ? 'completed' : 'active'}">${g.status}</span>
        </div>
      `).join('') || '<div style="color:#888">No task groups</div>';
    }

    async function loadAgents() {
      if (!currentSession) return;
      const agents = await fetchJSON(`/api/session/${currentSession}/agents`);
      document.getElementById('agents').innerHTML = agents.map(a => `
        <div class="agent-row ${selectedAgent === a.agent_type ? 'selected' : ''}"
             onclick="selectAgent('${a.agent_type}')">
          <div><strong>${a.agent_type}</strong> ${a.agent_id ? `(${a.agent_id})` : ''}</div>
          <div style="font-size:0.8rem;color:#888">
            Status: ${a.status} | Reasoning: ${a.reasoning_count || 0} | Tokens: ${a.tokens || 0}
          </div>
        </div>
      `).join('') || '<div style="color:#888">No agents spawned yet</div>';
    }

    async function loadLogs() {
      if (!currentSession) return;
      const logs = await fetchJSON(`/api/session/${currentSession}/logs`);
      document.getElementById('logs').innerHTML = logs.slice(0, 50).map(l => `
        <div class="log-entry">
          <span class="time">[${l.timestamp?.slice(11, 19) || '?'}]</span>
          <span class="agent">${l.agent_type}</span>:
          ${(l.content_preview || '').slice(0, 200)}...
        </div>
      `).join('') || '<div style="color:#888">No logs yet</div>';
    }

    async function selectAgent(agentType) {
      selectedAgent = agentType;
      document.querySelectorAll('.agent-row').forEach(el => el.classList.remove('selected'));
      event?.target?.closest('.agent-row')?.classList.add('selected');
      await loadReasoning();
    }

    async function loadReasoning() {
      if (!currentSession || !selectedAgent) return;
      const reasoning = await fetchJSON(`/api/session/${currentSession}/agent/${selectedAgent}/reasoning`);
      document.getElementById('reasoning').innerHTML = reasoning.length ? reasoning.map(r => `
        <div class="reasoning-entry">
          <span class="phase">[${r.reasoning_phase}]</span>
          <span class="confidence">Confidence: ${r.confidence_level || 'unknown'}</span>
          <div class="content">${r.content?.slice(0, 1000) || 'No content'}${r.content?.length > 1000 ? '...' : ''}</div>
        </div>
      `).join('') : '<div style="color:#888">No reasoning entries for this agent</div>';
    }

    // Auto-refresh every 5 seconds
    async function refresh() {
      const status = document.getElementById('refresh-status');
      status.textContent = '⟳ Refreshing...';
      await loadSessions();
      if (currentSession) {
        await Promise.all([loadGroups(), loadAgents(), loadLogs()]);
        if (selectedAgent) await loadReasoning();
      }
      status.textContent = 'Auto-refresh: 5s';
    }

    // Initial load
    loadSessions();
    setInterval(refresh, 5000);
  </script>
</body>
</html>
```

### File Location

```
mini-dashboard/
├── server.py       # Flask backend
└── index.html      # Frontend (served by Flask)
```

**Run with:**
```bash
cd mini-dashboard && python server.py
# Opens at http://localhost:5050
```

---

## Comparison to dashboard-v2

| Aspect | dashboard-v2 | mini-dashboard |
|--------|--------------|----------------|
| **Lines of code** | ~5000+ | ~300 |
| **Dependencies** | 30+ npm packages | 1 (textual) |
| **Build step** | Yes (Next.js) | No |
| **Startup time** | 5-10s | <1s |
| **Real-time** | WebSocket | SQLite polling |
| **UI complexity** | High (charts, tabs) | Low (table, text) |
| **Primary use** | Analysis, review | Live monitoring |

---

## Alternative Considered: Rich Live Display

**Technology:** Python + rich library (no textual)

```python
from rich.live import Live
from rich.table import Table
from rich.console import Console

def make_table(agents):
    table = Table(title="Subagents")
    table.add_column("#")
    table.add_column("Agent")
    table.add_column("Status")
    for i, a in enumerate(agents):
        table.add_row(str(i+1), a['agent_type'], a['status'])
    return table

with Live(refresh_per_second=0.2) as live:
    while True:
        agents = get_spawned_agents(...)
        live.update(make_table(agents))
```

**Why Rejected:**
- No click support (read-only display)
- Can't drill into agent reasoning interactively
- Would need keyboard input handling (complex)

---

## Success Metrics

The mini dashboard succeeds if:

1. **Single command start:** `python bazinga/mini-dashboard.py`
2. **Immediate usefulness:** Shows current session within 1 second
3. **Agent visibility:** Can see all spawned agents and their status
4. **Reasoning access:** Can click/select agent to see its reasoning
5. **Live updates:** Refreshes every 5 seconds automatically
6. **Minimal footprint:** <500 lines of code, 1 dependency

---

## Implementation Plan

1. **Create `bazinga/mini-dashboard.py`**
   - Import textual, sqlite3
   - Define data fetching functions
   - Build Textual App class
   - Add CSS for layout

2. **Add keybindings**
   - `q` = quit
   - `r` = force refresh
   - `↑/↓` or `j/k` = navigate agents
   - `Enter` = select agent

3. **Handle edge cases**
   - No active session → show message
   - Database locked → retry with backoff
   - No reasoning entries → show "No reasoning logged"

4. **Test with real orchestration**
   - Run integration test
   - Open mini dashboard in parallel
   - Verify agents appear as spawned
   - Verify reasoning shows on click

---

## Questions for User

Before implementing, please confirm:

1. **Terminal vs Browser:** Is a terminal-based TUI acceptable, or do you strongly prefer browser-based?

2. **Textual dependency:** Is `pip install textual` acceptable as the only extra dependency?

3. **Placement:** Should this be `bazinga/mini-dashboard.py` or somewhere else?

4. **Additional features:** Any other data you want to see? (e.g., token usage, task group progress)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Textual API changes | Pin version in requirements |
| SQLite locking | Use WAL mode (already enabled), retry on lock |
| Terminal size too small | Responsive layout with min-height checks |
| User prefers browser | Can add Option B later as alternative |

---

## Multi-LLM Review Integration

### Critical Issues Fixed

| Issue | Resolution |
|-------|------------|
| **Agent status derivation unreliable** | Parse status from latest orchestration_logs.content JSON (look for `"status": "..."` pattern) instead of task_groups.assigned_to |
| **Session timestamp inconsistency** | Use `COALESCE(created_at, start_time)` in queries |
| **Reasoning lacks group context** | Add group_id filter to reasoning queries |
| **Log volume/performance** | Add LIMIT 200 to log queries, pagination on demand |
| **SQLite locking** | Use read-only URI mode + busy_timeout=2000ms |

### Incorporated Improvements

1. **Session picker** - Add top panel with last 5 sessions, `s` key to switch
2. **Bounded queries** - LIMIT 200 on logs, paginate with PgUp/PgDn
3. **Robust status parsing** - Extract JSON status from content with regex fallback
4. **Group awareness** - Add Groups table between Session and Agents
5. **Token usage** - Show tokens per agent in table, total in footer
6. **CLI configurability** - `--db-path`, `--refresh-ms` flags
7. **Read-only DB access** - `file:...?mode=ro&cache=shared` URI
8. **Keyboard shortcuts** - `s`=session, `g`=group, `r`=refresh, `q`=quit, `h`=help

### Rejected Suggestions (With Reasoning)

| Suggestion | Why Rejected |
|------------|--------------|
| **Artifacts visibility** | Out of scope for "minimal" - adds file system scanning complexity |
| **Quality gates/skills display** | Scope creep - focus on core agent visibility first |
| **Relative time formatting** | Nice-to-have, not essential for v1 |
| **PyScript/file:// alternative** | Unnecessary if TUI works well |

### Updated Architecture (Flask + HTML)

```
mini-dashboard/
├── server.py (~150 lines)
│   ├── Flask app with JSON API endpoints
│   ├── SQLite read-only connection with busy_timeout
│   ├── Status parsing from agent content
│   └── Bounded queries (LIMIT on all)
└── index.html (~250 lines)
    ├── Sidebar: Sessions, Groups, Agents (all clickable)
    ├── Main: Logs panel + Reasoning panel
    ├── Auto-refresh every 5s via setInterval
    └── Dark theme CSS (no external deps)
```

### Revised Data Queries

**1. Session Selection (fixed)**
```python
def get_sessions(db_path, limit=5):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=2000")
    rows = conn.execute("""
        SELECT * FROM sessions
        ORDER BY
            CASE status WHEN 'active' THEN 0 ELSE 1 END,
            COALESCE(created_at, start_time) DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

**2. Agent Status Parsing (new)**
```python
import re
import json

def parse_agent_status(content: str) -> str:
    """Extract status from agent response content."""
    # Try JSON parsing for compact responses
    try:
        # Look for last JSON object in content
        json_match = re.findall(r'\{[^{}]+\}', content)
        if json_match:
            data = json.loads(json_match[-1])
            if 'status' in data:
                return data['status']
    except json.JSONDecodeError:
        pass

    # Fallback: regex for status patterns
    status_match = re.search(r'status["\s:]+([A-Z_]+)', content, re.IGNORECASE)
    if status_match:
        return status_match.group(1).upper()

    return 'UNKNOWN'


def get_agents_with_status(db_path, session_id):
    """Get agents with parsed statuses from their latest log."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=2000")

    # Get latest log per agent
    rows = conn.execute("""
        SELECT
            l.agent_type,
            l.agent_id,
            l.content,
            l.timestamp,
            (SELECT SUM(tokens_estimated) FROM token_usage t
             WHERE t.session_id = l.session_id AND t.agent_id = l.agent_id) as tokens
        FROM orchestration_logs l
        WHERE l.session_id = ?
          AND l.id = (
              SELECT MAX(id) FROM orchestration_logs l2
              WHERE l2.session_id = l.session_id
                AND l2.agent_type = l.agent_type
                AND COALESCE(l2.agent_id, '') = COALESCE(l.agent_id, '')
          )
        ORDER BY l.timestamp ASC
    """, (session_id,)).fetchall()
    conn.close()

    agents = []
    for row in rows:
        r = dict(row)
        r['status'] = parse_agent_status(r['content'])
        agents.append(r)
    return agents
```

**3. Group-Filtered Reasoning (fixed)**
```python
def get_agent_reasoning(db_path, session_id, agent_type, group_id=None):
    """Get reasoning entries for agent, optionally filtered by group."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=2000")

    query = """
        SELECT * FROM orchestration_logs
        WHERE session_id = ?
          AND agent_type = ?
          AND log_type = 'reasoning'
    """
    params = [session_id, agent_type]

    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)

    query += " ORDER BY timestamp ASC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

---

## References

- [Textual Documentation](https://textual.textualize.io/)
- Database schema: `.claude/skills/bazinga-db/references/schema.md`
- Existing dashboard: `dashboard-v2/`
