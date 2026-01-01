---
name: bazinga-db-agents
description: Agent logs, reasoning, and token tracking. Use when logging interactions, saving reasoning, tracking tokens, or managing events.
version: 2.0.0
allowed-tools: [Bash, Read]
---

# BAZINGA-DB Agents Skill

You are the bazinga-db-agents skill. You manage agent interaction logs, reasoning capture, token usage, skill outputs, and events.

## When to Invoke This Skill

**Invoke when:**
- Logging agent interactions
- Saving or retrieving agent reasoning
- Tracking token usage
- Recording skill outputs
- Saving or querying events (TL issues, verdicts, etc.)

**Do NOT invoke when:**
- Managing sessions or state → Use `bazinga-db-core`
- Managing task groups or plans → Use `bazinga-db-workflow`
- Managing context packages → Use `bazinga-db-context`

## Script Location

**Path:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

All commands use this script with `--quiet` flag:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command> [args...]
```

## Commands

### log-interaction

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet log-interaction \
  "<session_id>" "<agent_type>" "<message>" <sequence_num>
```

Logs an agent interaction in the orchestration flow.

**Parameters:**
- `agent_type`: `pm`, `developer`, `sse`, `qa_expert`, `tech_lead`, `investigator`, `requirements_engineer`
- `sequence_num`: Integer for ordering

### stream-logs

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet stream-logs \
  "<session_id>" [--format markdown|json] [--since "<timestamp>"]
```

Stream orchestration logs, optionally in markdown format.

### save-reasoning

```bash
# Recommended: Use --content-file to avoid exposing content in process table
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "<session_id>" "<group_id>" "<agent_type>" "<phase>" \
  --content-file /tmp/reasoning.txt [--confidence N] [--tokens N]

# Alternative: Inline content (avoid for sensitive data)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "<session_id>" "<group_id>" "<agent_type>" "<phase>" "<content>" \
  [--confidence N] [--tokens N]
```

Saves agent reasoning with automatic secret redaction.

**⚠️ Security:** Prefer `--content-file` over inline content to avoid exposing reasoning in process listings.

**Phases:** `understanding`, `approach`, `decisions`, `risks`, `blockers`, `pivot`, `completion`

**Example (recommended):**
```bash
# Write content to temp file first
cat > /tmp/reasoning.txt << 'EOF'
Analyzed requirements: need add/subtract/multiply/divide operations
EOF

python3 .../bazinga_db.py --quiet save-reasoning \
  "bazinga_xxx" "CALC" "developer" "understanding" \
  --content-file /tmp/reasoning.txt --confidence 85
```

### get-reasoning

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-reasoning \
  "<session_id>" [group_id] [agent_type] [phase]
```

Retrieve reasoning entries with optional filters.

### reasoning-timeline

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet reasoning-timeline \
  "<session_id>" [--format markdown|json]
```

Get chronological reasoning timeline across all agents.

### check-mandatory-phases

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet check-mandatory-phases \
  "<session_id>" "<group_id>" "<agent_type>"
```

Check if agent documented mandatory phases (understanding, completion).

**Returns:** `{"complete": true/false, "missing": [...]}`

### log-tokens

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet log-tokens \
  "<session_id>" "<agent_type>" <token_count> [model]
```

Log token usage for an agent.

### token-summary

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet token-summary "<session_id>"
```

Get token usage summary by agent and model.

### save-skill-output

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-skill-output \
  "<session_id>" "<group_id>" "<skill_name>" '<json_output>'
```

Save skill execution output for audit trail.

**Example:**
```bash
python3 .../bazinga_db.py --quiet save-skill-output \
  "bazinga_xxx" "AUTH" "specialization-loader" \
  '{"templates_used": ["python.md"], "token_count": 450}'
```

### get-skill-output

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output \
  "<session_id>" "<skill_name>" [group_id]
```

Get latest skill output, optionally filtered by group.

### get-skill-output-all

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-skill-output-all \
  "<session_id>" [skill_name]
```

Get all skill outputs for a session.

### check-skill-evidence

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet check-skill-evidence \
  "<session_id>" "<skill_name>" [--within-minutes N]
```

Check for recent skill invocation evidence.

### save-event

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-event \
  "<session_id>" "<event_subtype>" '<json_payload>'
```

Save a generic event with JSON payload.

**Common event types:**
- `scope_change` - User approved scope reduction
- `role_violation` - Detected role boundary violation
- `tl_issues` - Tech Lead issues after CHANGES_REQUESTED
- `tl_issue_responses` - Developer responses to TL issues
- `tl_verdicts` - TL verdicts on Developer rejections
- `investigation_iteration` - Investigator agent iteration progress
- `pm_bazinga` - PM sends BAZINGA completion signal
- `validator_verdict` - Validator ACCEPT/REJECT decision

**Tech Lead Review Events:**
```bash
# Save TL issues event
python3 .../bazinga_db.py --quiet save-event \
  "sess_123" "tl_issues" \
  '{"group_id": "AUTH", "iteration": 1, "issues": [...], "blocking_count": 3}'

# Save Developer responses
python3 .../bazinga_db.py --quiet save-event \
  "sess_123" "tl_issue_responses" \
  '{"group_id": "AUTH", "iteration": 1, "issue_responses": [...], "blocking_summary": {...}}'

# Save TL verdicts on rejections
python3 .../bazinga_db.py --quiet save-event \
  "sess_123" "tl_verdicts" \
  '{"group_id": "AUTH", "iteration": 2, "verdicts": [...], "summary": {...}}'
```

**Deduplication:** Events are deduplicated by `(session_id, group_id, iteration, event_type)`.

### get-events

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-events \
  "<session_id>" [event_subtype] [limit]
```

Query events by session and optionally by subtype.

### save-investigation-iteration (Atomic)

```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-investigation-iteration \
  "<session_id>" "<group_id>" <iteration> "<status>" \
  --state-file /tmp/state.json --event-file /tmp/event.json
```

Atomically save investigation state AND event together. Ensures consistency between
state (for resumption) and events (for audit trail). Uses single transaction.

**Parameters:**
- `iteration`: Integer iteration number (1-10)
- `status`: under_investigation, root_cause_found, hypothesis_eliminated, etc.
- `--state-file`: Path to JSON file with investigation state data
- `--event-file`: Path to JSON file with event payload

**Returns:**
```json
{
  "success": true,
  "atomic": true,
  "state_saved": true,
  "event_saved": true,
  "event_id": 123,
  "iteration": 1,
  "idempotent": false
}
```

## Output Format

Return ONLY raw JSON output. No formatting, markdown, or commentary.

## Error Handling

- Missing session: Returns `{"error": "Session not found: <id>"}`
- Invalid phase: Returns `{"error": "Invalid phase: <phase>"}`
- JSON parse error: Returns `{"error": "Invalid JSON: <details>"}`

## References

- Full schema: `.claude/skills/bazinga-db/references/schema.md`
- Event schemas: `bazinga/schemas/event_*.schema.json`
- All commands: `.claude/skills/bazinga-db/references/command_examples.md`
- CLI help: `python3 .../bazinga_db.py help`
