# Database Logging Pattern

Use this pattern whenever you need to log an agent interaction to the database.

## Pattern

**Step 1: Prepare natural language request**
```
bazinga-db, please log this [AGENT_TYPE] interaction:

Session ID: [current session_id from initialization]
Agent Type: [pm|developer|qa_expert|tech_lead]
Content: [Full agent response text - preserve formatting]
Iteration: [current iteration number]
Agent ID: [agent_identifier]
```

**Step 2: Invoke the skill**
```
Skill(command: "bazinga-db")
```

## Examples

### Logging PM Interaction
```
bazinga-db, please log this PM interaction:

Session ID: bazinga_20250113_143022
Agent Type: pm
Content: I recommend SIMPLE mode for this task...
Iteration: 1
Agent ID: pm_main
```

Then invoke:
```
Skill(command: "bazinga-db")
```

### Logging Developer Interaction
```
bazinga-db, please log this developer interaction:

Session ID: bazinga_20250113_143022
Agent Type: developer
Content: ## Implementation Complete...
Iteration: 1
Agent ID: dev_group_1
```

Then invoke:
```
Skill(command: "bazinga-db")
```

### Logging QA Interaction
```
bazinga-db, please log this QA interaction:

Session ID: bazinga_20250113_143022
Agent Type: qa_expert
Content: ## QA Expert: Test Results - PASS...
Iteration: 1
Agent ID: qa_group_1
```

Then invoke:
```
Skill(command: "bazinga-db")
```

### Logging Tech Lead Interaction
```
bazinga-db, please log this tech_lead interaction:

Session ID: bazinga_20250113_143022
Agent Type: tech_lead
Content: ## Tech Lead: Code Review - APPROVED...
Iteration: 2
Agent ID: techlead_group_1
```

Then invoke:
```
Skill(command: "bazinga-db")
```

## Important Notes
- Always use the session_id from initialization
- Preserve full agent response text including formatting
- Track iteration numbers correctly
- Use consistent agent_id format: `{role}_{group_id}`
