# Orchestrator Database Operations Reference

This file contains reference examples for database operations. The orchestrator should consult this when needed, but doesn't need to keep it all in memory.

---

## §DB: Database Logging Reference

**Pattern for ALL agent interactions:**

After **EVERY agent response** (PM, Developer, QA, Tech Lead):

```
bazinga-db-agents, please log this [agent_type] interaction:

Session ID: [current session_id from init]
Agent Type: [any agent type - common: pm, developer, qa_expert, tech_lead, orchestrator, investigator]
Content: [Full agent response text - preserve all formatting]
Iteration: [current iteration number]
Agent ID: [agent identifier - pm_main, developer_1, qa_expert, tech_lead, investigator_1, etc.]
```

**Note:** System is extensible - any agent type is accepted (no validation against hardcoded list).

Then invoke: `Skill(command: "bazinga-db-agents")`

**Examples:**

**After PM response:**
```
bazinga-db-agents, please log this pm interaction:

Session ID: [session_id]
Agent Type: pm
Content: [PM's full response]
Iteration: 1
Agent ID: pm_main
```

**After Developer response:**
```
bazinga-db-agents, please log this developer interaction:

Session ID: [session_id]
Agent Type: developer
Content: [Full Developer response from Task tool]
Iteration: [iteration]
Agent ID: developer_main
```

**Fully Expanded Example (use this pattern when needed):**
```
bazinga-db-agents, please log this developer interaction:

Session ID: [session_id]
Agent Type: developer
Content: [Full Developer response from Task tool]
Iteration: [iteration]
Agent ID: developer_main
```

Then invoke: `Skill(command: "bazinga-db-agents")`

**Process internally** (logging is system operation - no user output needed for database sync).

---

## State Management from Database - REFERENCE

**⚠️ IMPORTANT:** These are **separate operations** you perform at different times. Do NOT execute them all in sequence! Only use the operation you need at that moment.

### Reading State

**When you need PM state** (before spawning PM):

Request to bazinga-db-core skill:
```
bazinga-db-core, please get the latest PM state for session [current session_id]
```

Then invoke: `Skill(command: "bazinga-db-core")`


**IMPORTANT:** You MUST invoke bazinga-db skill here. Use the returned data. Simply do not echo the skill response text in your message to user.

 Returns PM state or null if first iteration.

---

**When you need orchestrator state** (to check current phase):

Request to bazinga-db-core skill:
```
bazinga-db-core, please get the latest orchestrator state for session [current session_id]
```

Then invoke: `Skill(command: "bazinga-db-core")`


**IMPORTANT:** You MUST invoke bazinga-db skill here. Use the returned data. Simply do not echo the skill response text in your message to user.

 Returns orchestrator state or null if first time.

---

**When you need task groups** (to check statuses):

Request to bazinga-db-workflow skill:
```
bazinga-db-workflow, please get all task groups for session [current session_id]
```

Then invoke: `Skill(command: "bazinga-db-workflow")`

Returns array of groups with their statuses.

---

### Writing State

**Saving PM state** (after PM responds):

Request to bazinga-db-core skill:
```
bazinga-db-core, please save the PM state:

Session ID: [session_id]
State Type: pm
State Data: {JSON data from PM}
```

Then invoke: `Skill(command: "bazinga-db-core")`

---

**Saving orchestrator state** (after phase transitions):

Request to bazinga-db-core skill:
```
bazinga-db-core, please save the orchestrator state:

Session ID: [current session_id]
State Type: orchestrator
State Data: {
  "session_id": "[session_id]",
  "current_phase": "developer_working | qa_testing | tech_review | pm_checking",
  "active_agents": [
    {"type": "developer", "id": "dev_main", "status": "in_progress"}
  ],
  "mode": "simple | parallel"
}
```

Then invoke: `Skill(command: "bazinga-db-core")`

---

**Creating task groups** (from PM response):

For EACH group in PM's task_groups:

Request to bazinga-db-workflow skill:
```
bazinga-db-workflow, please create task group:

Group ID: [extracted group_id]
Session ID: [current session_id]
Name: [extracted group name]
Status: pending
```

Then invoke: `Skill(command: "bazinga-db-workflow")`

Repeat for each group.

---

**Updating task group status** (after Tech Lead approval):

Request to bazinga-db-workflow skill:
```
bazinga-db-workflow, please update task group:

Group ID: [group_id]
Status: completed | failed | in_progress
Last Review Status: APPROVED | CHANGES_REQUESTED
```

Then invoke: `Skill(command: "bazinga-db-workflow")`

---

### Dashboard Queries

**Getting dashboard snapshot** (for completion):

Request to bazinga-db-core skill:
```
bazinga-db-core, please provide dashboard snapshot:

Session ID: [current session_id]
```

Then invoke: `Skill(command: "bazinga-db-core")`

Returns comprehensive session summary.

---

### Session Management

**Creating new session** (Path B):

Request to bazinga-db-core skill:
```
bazinga-db-core, please create a new orchestration session:

Session ID: $SESSION_ID
Mode: simple
Requirements: [User's requirements from input]
```

Then invoke: `Skill(command: "bazinga-db-core")`

---

**Updating session status** (at completion):

Request to bazinga-db-core skill:
```
bazinga-db-core, please update session status:

Session ID: [current session_id]
Status: completed
End Time: [timestamp]
```

Then invoke: `Skill(command: "bazinga-db-core")`

---

**Checking for active sessions** (Path A):

Request to bazinga-db-core skill:
```
bazinga-db-core, please check for active orchestration sessions
```

Then invoke: `Skill(command: "bazinga-db-core")`

Returns most recent session_id or null.

---

## Quick Reference Table

| Operation | When | Skill Request Pattern |
|-----------|------|----------------------|
| Read PM state | Before spawning PM | `get the latest PM state for session [id]` |
| Save PM state | After PM responds | `save the PM state: Session ID... State Type: pm...` |
| Read orchestrator state | Phase checks | `get the latest orchestrator state for session [id]` |
| Save orchestrator state | Phase transitions | `save the orchestrator state: Session ID...` |
| Get task groups | Status checks | `get all task groups for session [id]` |
| Create task group | From PM response | `create task group: Group ID... Session ID...` |
| Update task group | After review | `update task group: Group ID... Status...` |
| Dashboard snapshot | Completion | `provide dashboard snapshot: Session ID...` |
| Log interaction | After every agent | `log this [agent_type] interaction: Session ID...` |
