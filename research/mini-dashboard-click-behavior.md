# Mini Dashboard Click Behavior Analysis

**Date:** 2025-12-29
**Context:** User reported two issues: (1) task groups not clickable, (2) agent selection groups all same-type agents together
**Decision:** Define correct behavior for task group clicks and individual agent selection
**Status:** Implemented
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The mini dashboard (`mini-dashboard/`) has two UI interaction issues:

1. **Task Groups Click Does Nothing** - Groups display with `cursor: pointer` but clicking has no effect
2. **Agent Selection Groups All Same-Type** - Clicking `developer_1` selects ALL developers, showing combined logs

Both issues stem from incomplete implementation - the UI suggests interactivity that doesn't exist.

---

## Current State Analysis

### Data Model (from schema.md and seed_test_db.py)

**Task Groups Table:**
```sql
task_groups (
    id TEXT,                  -- e.g., "AUTH", "API_CRUD"
    session_id TEXT,
    name TEXT,               -- "JWT Authentication"
    status TEXT,             -- pending/in_progress/completed/failed
    assigned_to TEXT,        -- "developer_1"
    complexity INTEGER,      -- 1-10
    initial_tier TEXT,       -- "Developer" or "Senior Software Engineer"
    revision_count INTEGER,
    last_review_status TEXT, -- APPROVED/CHANGES_REQUESTED
    feature_branch TEXT,
    merge_status TEXT
)
```

**Orchestration Logs Table:**
```sql
orchestration_logs (
    agent_type TEXT,    -- "developer", "qa_expert", "tech_lead"
    agent_id TEXT,      -- "developer_1", "developer_2", "qa_1"
    group_id TEXT,      -- "AUTH", "API_CRUD" (links logs to task groups)
    log_type TEXT,      -- "interaction" or "reasoning"
    ...
)
```

### Key Insight: `agent_type` vs `agent_id`

The data model clearly distinguishes:
- `agent_type` = role category (developer, qa_expert, tech_lead)
- `agent_id` = specific instance (developer_1, developer_2, tech_lead_1)

**Test data confirms multiple instances:**
```python
# From seed_test_db.py line 642-643
(completed_session, 'developer', 'developer_1', 18000),
(completed_session, 'developer', 'developer_2', 16000),
```

### Current Code Issues

**Issue 1: Task Groups (index.html:513-525)**
```javascript
// Groups render WITHOUT data attributes or click handlers
el.innerHTML = data.map(g => `
  <div class="clickable-item">  <!-- No data-group-id! -->
    <div class="item-title">
      ${escapeHtml(g.id)}
      ...
```

**Issue 2: Agent Selection (index.html:546-598)**
```javascript
// Selection uses agent_type, ignoring agent_id
<div class="clickable-item ${selectedAgent === a.agent_type ? 'selected' : ''}"
     data-agent-type="${escapeHtml(a.agent_type)}">

async function selectAgent(agentType) {
    selectedAgent = agentType;  // Stores TYPE not ID
    document.querySelectorAll('#agents .clickable-item').forEach(el => {
        el.classList.toggle('selected', el.dataset.agentType === agentType);
        // ^^^ Compares by TYPE - selects ALL same-type agents
    });
}
```

---

## Proposed Behavior

### Feature 1: Task Group Selection

**When user clicks a task group:**

1. **Visual Feedback**
   - Highlight the selected group with `selected` class
   - Clear any previously selected group

2. **Filter Logs Panel**
   - Show only logs where `group_id` matches selected group
   - API: `/api/session/{id}/logs?group_id={group_id}`

3. **Filter Agents Panel**
   - Show only agents that have logged activity for this group
   - Or highlight agents assigned to this group (`assigned_to` field)

4. **Update Reasoning Panel**
   - If an agent is also selected, filter reasoning by both agent AND group
   - API already supports: `/api/session/{id}/agent/{type}/reasoning?group_id={group_id}`

5. **Display Group Details (Optional Enhancement)**
   - Could show a detail panel with: status, complexity, branch, revision count
   - For v1, just filtering is sufficient

**Required Changes:**

| Location | Change |
|----------|--------|
| `index.html:513` | Add `data-group-id="${escapeHtml(g.id)}"` attribute |
| `index.html:593` | Add `selectGroup(groupId)` function |
| `index.html:680` | Add click event listener for groups |
| `index.html:563` | Update `loadLogs()` to pass `group_id` if selected |
| `server.py:222` | Update `/api/session/{id}/logs` to accept `group_id` query param |

### Feature 2: Individual Agent Selection

**When user clicks an agent:**

1. **Select Individual Instance**
   - Click on `developer_1` selects ONLY `developer_1`
   - Click on `developer_2` selects ONLY `developer_2`

2. **Visual Feedback**
   - Only the clicked agent row highlights
   - Other agents of same type remain unselected

3. **Filter Reasoning**
   - Show reasoning only for the specific `agent_id`
   - API needs to accept `agent_id` parameter

**Required Changes:**

| Location | Change |
|----------|--------|
| `index.html:546` | Add `data-agent-id="${escapeHtml(a.agent_id || a.agent_type)}"` |
| `index.html:546` | Change selection compare to use `agent_id` |
| `index.html:593` | Update `selectAgent()` to accept and track `agentId` |
| `index.html:607` | Pass `agent_id` to reasoning API |
| `server.py:247` | Add `agent_id` query param to reasoning endpoint |

---

## Implementation Details

### 1. Task Group Selection Implementation

**HTML (add data attribute):**
```javascript
// index.html:513 - Add data-group-id
el.innerHTML = data.map(g => `
  <div class="clickable-item ${selectedGroup === g.id ? 'selected' : ''}"
       data-group-id="${escapeHtml(g.id)}">
```

**State variable:**
```javascript
// index.html:396 - Add state
let selectedGroup = null;
```

**Selection function:**
```javascript
// New function around line 592
async function selectGroup(groupId) {
    selectedGroup = groupId;

    // Update UI - highlight selected group
    document.querySelectorAll('#groups .clickable-item').forEach(el => {
        el.classList.toggle('selected', el.dataset.groupId === groupId);
    });

    // Reload logs filtered by group
    await loadLogs();

    // If agent selected, reload reasoning filtered by group
    if (selectedAgent) {
        await loadReasoning();
    }
}
```

**Event listener:**
```javascript
// index.html after line 679 - Add event delegation
document.getElementById('groups').addEventListener('click', (e) => {
    const item = e.target.closest('.clickable-item[data-group-id]');
    if (item) {
        selectGroup(item.dataset.groupId);
    }
});
```

**Update loadLogs to use selectedGroup:**
```javascript
async function loadLogs() {
    if (!currentSession) return;

    let url = `/api/session/${currentSession}/logs`;
    if (selectedGroup) {
        url += `?group_id=${encodeURIComponent(selectedGroup)}`;
    }
    const data = await fetchJSON(url);
    // ... rest unchanged
}
```

**Backend change (server.py:222):**
```python
@app.route('/api/session/<session_id>/logs')
def get_logs(session_id):
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    group_id = request.args.get('group_id')  # NEW

    query = """
        SELECT id, timestamp, agent_type, agent_id, iteration,
               SUBSTR(content, 1, 500) as content_preview
        FROM orchestration_logs
        WHERE session_id = ? AND log_type = 'interaction'
    """
    params = [session_id]

    if group_id:  # NEW
        query += " AND group_id = ?"
        params.append(group_id)

    query += " ORDER BY datetime(timestamp) DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    # ... rest unchanged
```

### 2. Individual Agent Selection Implementation

**HTML (add data-agent-id):**
```javascript
// index.html:545-559 - Add agent_id to data attribute
el.innerHTML = data.map(a => `
  <div class="clickable-item ${selectedAgentId === a.agent_id ? 'selected' : ''}"
       data-agent-type="${escapeHtml(a.agent_type)}"
       data-agent-id="${escapeHtml(a.agent_id || a.agent_type)}">
    <div class="item-title">
      ${escapeHtml(a.agent_type)}
      ${a.agent_id && a.agent_id !== a.agent_type ?
        `<span class="item-meta">(${escapeHtml(a.agent_id)})</span>` : ''}
```

**State variables:**
```javascript
// index.html:396 - Replace selectedAgent with:
let selectedAgentId = null;
let selectedAgentType = null;
```

**Updated selectAgent function:**
```javascript
async function selectAgent(agentId, agentType) {
    selectedAgentId = agentId;
    selectedAgentType = agentType;

    // Update UI - only highlight the specific agent instance
    document.querySelectorAll('#agents .clickable-item').forEach(el => {
        el.classList.toggle('selected', el.dataset.agentId === agentId);
    });

    // Display which specific agent is selected
    const displayName = agentId !== agentType ?
        `${agentType} (${agentId})` : agentType;
    document.getElementById('reasoning-agent').textContent = displayName;

    await loadReasoning();
}
```

**Updated event listener:**
```javascript
document.getElementById('agents').addEventListener('click', (e) => {
    const item = e.target.closest('.clickable-item[data-agent-id]');
    if (item) {
        selectAgent(item.dataset.agentId, item.dataset.agentType);
    }
});
```

**Updated loadReasoning:**
```javascript
async function loadReasoning() {
    if (!currentSession || !selectedAgentId) return;

    let url = `/api/session/${currentSession}/agent/${selectedAgentType}/reasoning`;
    const params = new URLSearchParams();

    if (selectedAgentId !== selectedAgentType) {
        params.append('agent_id', selectedAgentId);
    }
    if (selectedGroup) {
        params.append('group_id', selectedGroup);
    }
    if (params.toString()) {
        url += '?' + params.toString();
    }

    const data = await fetchJSON(url);
    // ... rest unchanged
}
```

**Backend change (server.py:247):**
```python
@app.route('/api/session/<session_id>/agent/<path:agent_type>/reasoning')
def get_reasoning(session_id, agent_type):
    group_id = request.args.get('group_id')
    agent_id = request.args.get('agent_id')  # NEW

    query = """
        SELECT id, timestamp, reasoning_phase, confidence_level,
               content, group_id, references_json, agent_id
        FROM orchestration_logs
        WHERE session_id = ? AND agent_type = ? AND log_type = 'reasoning'
    """
    params = [session_id, agent_type]

    if agent_id:  # NEW - filter by specific agent instance
        query += " AND agent_id = ?"
        params.append(agent_id)

    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)

    query += " ORDER BY datetime(timestamp) ASC LIMIT 50"
    # ... rest unchanged
```

---

## Critical Analysis

### Pros

- **Consistent with data model** - Uses `agent_id` and `group_id` as designed
- **Minimal changes** - Backend already has most data, just needs filters
- **Backward compatible** - Old behavior works if no filters passed
- **Intuitive UX** - Click to filter is expected behavior

### Cons

- **State complexity** - Need to track `selectedGroup`, `selectedAgentId`, `selectedAgentType`
- **Combined filters** - User might want to clear group filter independently
- **URL state** - Filters not persisted in URL (refresh loses selection)

### Risks

1. **Empty state handling** - What if no logs/reasoning for filtered selection?
2. **Performance** - Multiple API calls on each selection change
3. **Agent display** - Need clear visual distinction between agents with same type

### Mitigations

1. Show "No logs for this selection" empty state message
2. Debounce rapid clicks, consider caching recent responses
3. Always show `agent_id` in parentheses when multiple instances exist

---

## Alternative Approaches Considered

### Alternative A: Master-Detail Layout
Replace sidebar+panels with master-detail: click group → show group page with tabs for logs/agents/reasoning.

**Rejected:** Too much redesign for mini dashboard philosophy (minimal, quick view).

### Alternative B: Filter Badges
Show active filters as dismissible badges above panels (e.g., "Group: AUTH ✕")

**Consider for v2:** Good UX pattern but adds complexity. For now, clicking same item again could deselect.

### Alternative C: Combine Agent Selection
Keep selecting by `agent_type` but add a sub-menu/dropdown to pick specific instance.

**Rejected:** More complex than direct selection. Data shows agent_id is the right granularity.

---

## Decision Rationale

The proposed implementation is minimal and correct:

1. **Follows existing patterns** - Sessions already use click-to-select with data attributes
2. **Uses existing API capabilities** - Reasoning endpoint already accepts `group_id`
3. **Matches user expectation** - Click filters, click different item changes filter
4. **Aligns with data model** - `agent_id` is designed for this use case

---

## Implementation Checklist

### Frontend (index.html)

- [ ] Add `selectedGroup` and `selectedAgentId` state variables
- [ ] Add `data-group-id` attribute to group items
- [ ] Add `data-agent-id` attribute to agent items
- [ ] Add `selectGroup()` function
- [ ] Update `selectAgent()` to use agent_id
- [ ] Add click event listener for groups
- [ ] Update click event listener for agents
- [ ] Update `loadLogs()` to pass group_id filter
- [ ] Update `loadReasoning()` to pass agent_id and group_id filters
- [ ] Update agent selection comparison in `loadAgents()`

### Backend (server.py)

- [ ] Add `group_id` parameter to `/api/session/{id}/logs` endpoint
- [ ] Add `agent_id` parameter to `/api/session/{id}/agent/{type}/reasoning` endpoint

### Testing

- [ ] Verify group click highlights only that group
- [ ] Verify group click filters logs
- [ ] Verify agent click selects individual instance
- [ ] Verify reasoning shows only selected agent's data
- [ ] Verify combined filters (group + agent) work
- [ ] Verify empty state messages display correctly
- [ ] Test with seed database (has developer_1 and developer_2)

---

## References

- `mini-dashboard/index.html` - Frontend code
- `mini-dashboard/server.py` - Backend API
- `mini-dashboard/tests/seed_test_db.py` - Test data with multiple agent instances
- `.claude/skills/bazinga-db/references/schema.md` - Database schema documentation
