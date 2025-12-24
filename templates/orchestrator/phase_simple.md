## Phase 2A: Simple Mode Execution

**Before any Bash command:** See §Policy-Gate and §Bash Command Allowlist in orchestrator.md

### 🔴 FOREGROUND EXECUTION ONLY

**All Task() calls MUST include `run_in_background: false`.** See orchestrator.md §FOREGROUND EXECUTION ONLY and §PRE-TASK VALIDATION.

### 🔴 POST-SPAWN TOKEN TRACKING (MANDATORY)

**After EVERY Task() call, you MUST:**

1. **Increment spawn counter:**
   ```
   bazinga-db, please update orchestrator state:

   Session ID: {session_id}
   State Type: orchestrator
   State Data: {"total_spawns": {current_total_spawns + 1}}
   ```
   Then invoke: `Skill(command: "bazinga-db")`

2. **Compute token estimate:** `estimated_token_usage = total_spawns * 15000`

**Note:** The prompt-builder script applies token budgets automatically based on model tier (haiku=900, sonnet=1800, opus=2400). The spawn counter is tracked for metrics and debugging purposes.

---

### Step 2A.1: Spawn Single Developer

**User output:** `🔨 Implementing | {tier_name} ({model}) [C:{complexity}] - {brief_task_description}`

Example: `🔨 Implementing | Senior Software Engineer (Sonnet) [C:7] - JWT authentication implementation`

### 🔴 MANDATORY DEVELOPER/SSE PROMPT BUILDING (PM Tier Decision)

**Tier selection (from PM's Initial Tier):**
| PM Decision | Agent File | Model | Description |
|-------------|------------|-------|-------------|
| Developer (default) | `agents/developer.md` | `MODEL_CONFIG["developer"]` | `Dev: {task[:90]}` |
| Senior Software Engineer | `agents/senior_software_engineer.md` | `MODEL_CONFIG["senior_software_engineer"]` | `SSE: {task[:90]}` |
| Requirements Engineer | `agents/requirements_engineer.md` | `MODEL_CONFIG["requirements_engineer"]` | `Research: {task[:90]}` |

**🔴 Research Task Override:** If PM sets `type: research` for a task group, spawn Requirements Engineer regardless of initial_tier. RE produces research deliverables (not code) and returns `READY_FOR_REVIEW` status which routes to Tech Lead for validation.

**🔴 Type Precedence:** If a task is both research AND security-sensitive (e.g., "Research OAuth vulnerabilities"), `type: research` takes precedence for agent selection (spawn RE, not SSE). The security_sensitive flag still ensures mandatory TL review, but the research nature determines the agent type.

**🔴 Research Rejection Routing:** If Tech Lead requests changes on a research task, route back to Requirements Engineer (not Developer). Research deliverables need RE's context and tools, not code-focused Developer.

### SPAWN IMPLEMENTATION AGENT (DETERMINISTIC PROMPT)

**🔴 SINGLE-STEP PROMPT BUILDING**

This section handles spawning Developer, SSE, or RE based on PM's `initial_tier` decision.

**🔴🔴🔴 MANDATORY Step 0: Query Task Group and Map Tier to Agent Type 🔴🔴🔴**

**BEFORE creating the params file, you MUST:**

1. **Query task groups from database:**
   ```bash
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-task-groups "{session_id}"
   ```

   **Response format:** JSON array of task groups, each with `id`, `name`, `initial_tier`, `complexity`, etc.

   **If query fails:** Output `❌ Failed to query task groups | {error}` → STOP

2. **Find the target group and extract initial_tier:**
   ```python
   # Find group by group_id
   target_group = next((g for g in task_groups if g["id"] == group_id), None)
   if not target_group:
       print(f"❌ Group {group_id} not found in task_groups")
       # STOP
   ```

3. **Map initial_tier to agent_type:**

   | DB `initial_tier` Value | Maps To `agent_type` | Model Key |
   |-------------------------|---------------------|-----------|
   | `"Developer"` | `"developer"` | `MODEL_CONFIG["developer"]` |
   | `"Senior Software Engineer"` | `"senior_software_engineer"` | `MODEL_CONFIG["senior_software_engineer"]` |
   | `"Requirements Engineer"` | `"requirements_engineer"` | `MODEL_CONFIG["requirements_engineer"]` |
   | `null` or missing | `"developer"` (default) | `MODEL_CONFIG["developer"]` |

   **Also check task type:** If PM's description contains `**Type:** research`, use `requirements_engineer` regardless of initial_tier.

4. **Determine final agent_type:**
   ```python
   TIER_TO_AGENT = {
       "Developer": "developer",
       "Senior Software Engineer": "senior_software_engineer",
       "Requirements Engineer": "requirements_engineer"
   }

   # Normalize tier value
   tier = (target_group.get("initial_tier") or "").strip()

   # Research type override
   if "**type:** research" in target_group.get("description", "").lower():
       agent_type = "requirements_engineer"
   elif tier in TIER_TO_AGENT:
       agent_type = TIER_TO_AGENT[tier]
   else:
       print(f"⚠️ Unknown tier '{tier}', defaulting to developer")
       agent_type = "developer"
   ```

**🔴 CRITICAL: If you skip this step, SSE/RE tasks will wrongly spawn as Developer!**

**🔴 SELF-CHECK before proceeding:**
- ✅ Did I query task_groups from database successfully?
- ✅ Did I find the target group by group_id?
- ✅ Did I check for research type override?
- ✅ Did I map the tier value to agent_type correctly?
- ✅ For security tasks, is agent_type = "senior_software_engineer"?
- ✅ For research tasks, is agent_type = "requirements_engineer"?

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json` using the agent_type from Step 0:

**⚠️ Path safety:** Ensure session_id and group_id contain only alphanumeric chars and underscores. Reject if they contain `../` or special characters.

```json
{
  "agent_type": "{agent_type}",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "{task_title}",
  "task_requirements": "{task_requirements}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[agent_type]}",
  "output_file": "bazinga/prompts/{session_id}/{agent_type}_{group_id}.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result**

Skill returns JSON. Check:
- `success` is `true`
- `prompt_file` is non-empty
- `markers_ok` is `true`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 2: Spawn Agent with file-based instructions**

Output summary:
```
📝 **{agent_type} Prompt** | Group: {group_id} | Model: {model}
   **Task:** {task_title}
   **Branch:** {branch}
   **Prompt file:** bazinga/prompts/{session_id}/{agent_type}_{group_id}.md
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent_type], description="{agent_type}: {task_title[:90]}", prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file. The file contains your full agent definition, context, and task requirements.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

**🔴 SELF-CHECK:**
- ✅ Did prompt-builder create the file successfully?
- ✅ Does Task() prompt instruct agent to read the file FIRST?
- ✅ Is the prompt file path correct?

**🔴 Follow PM's tier decision. DO NOT override for initial spawn.**


### Step 2A.2: Receive Developer Response

**AFTER receiving the Developer's complete response:**

**Step 1: Parse response and output capsule to user**

Use the Developer Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract:
- **Status** (READY_FOR_QA, READY_FOR_REVIEW, BLOCKED, PARTIAL)
- **Files** created/modified
- **Tests** added (count)
- **Coverage** percentage
- **Summary** of work

**Step 2: Construct capsule** per `response_parsing.md` §Developer Response templates:
- **READY_FOR_QA/REVIEW:** `🔨 Group {id} [{tier}] [C:{complexity}] complete | {summary}, {files}, {tests} ({coverage}%) | → {next}`
- **PARTIAL:** `🔨 Group {id} [{tier}] [C:{complexity}] implementing | {done} | {status}`
- **BLOCKED:** `⚠️ Group {id} [{tier}] [C:{complexity}] blocked | {blocker} | Investigating`
- **ESCALATE_SENIOR:** `🔺 Group {id} [{tier}] [C:{complexity}] escalating | {reason} | → SSE`

**Tier notation:** `[SSE/{model}]`, `[Dev/{model}]` - Model from `MODEL_CONFIG[agent_type]`
**Complexity notation:** `[C:N]` where N is 1-10. Levels: 1-3=Low (Developer), 4-6=Medium (SSE), 7-10=High (SSE)

**Step 3: Output capsule to user**

**Step 4: Log developer interaction** — Use §Logging Reference pattern. Agent ID: `developer_main`.

**AFTER logging: IMMEDIATELY continue to Step 2A.3. Do NOT stop.**

### Step 2A.3: Route Developer Response

**IF Developer reports READY_FOR_QA:**

**🔴 MANDATORY REASONING CHECK (Before QA routing):**

Check that the current agent (developer OR senior_software_engineer) documented required reasoning phases:
```bash
# Use the agent_type that just completed (from Step 2A.1 tier decision)
# Could be "developer" or "senior_software_engineer" depending on escalation
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet check-mandatory-phases \
  "{session_id}" "{group_id}" "{agent_type}"
```

**Routing based on check result:**
| Result | Action |
|--------|--------|
| `"complete": true` | Proceed to QA routing below |
| `"complete": false` | Respawn same agent with reminder to document missing phases |

**IF reasoning check fails (missing understanding OR completion):**
- Build prompt for the SAME agent type (developer/SSE) with missing phase reminder:
  ```
  ⚠️ REASONING DOCUMENTATION INCOMPLETE

  Missing phases: {missing_phases}

  Before reporting READY_FOR_QA, you MUST:
  1. Document `understanding` phase (your interpretation of the task)
  2. Document `completion` phase (summary of what was done)

  Use --content-file pattern shown in your agent instructions.
  ```
- Spawn the SAME agent type (developer or senior_software_engineer) with reminder → Return to Step 2A.2
- **Do NOT proceed to QA with incomplete reasoning**

**IF reasoning check passes:**
- Check testing_config.json for qa_expert_enabled
- IF QA enabled → **IMMEDIATELY continue to Step 2A.4 (Spawn QA). Do NOT stop.**
- IF QA disabled → **IMMEDIATELY skip to Step 2A.6 (Spawn Tech Lead). Do NOT stop.**

**IF Developer reports BLOCKED:**
- **Do NOT stop for user input**
- **IMMEDIATELY spawn Investigator using unified two-turn sequence:**

#### SPAWN INVESTIGATOR (SKILL-BASED PROMPT)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_investigator_{group_id}.json`:
```json
{
  "agent_type": "investigator",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Investigate: {blocker_description[:60]}",
  "task_requirements": "BLOCKER: {blocker_description}\nEvidence from Developer: {developer_evidence}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"investigator\"]}",
  "output_file": "bazinga/prompts/{session_id}/investigator_{group_id}.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn Investigator with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["investigator"], description="Investigator: {blocker[:60]}", prompt="FIRST: Read bazinga/prompts/{session_id}/investigator_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

After Investigator provides solution, spawn Developer again with resolution using the prompt-builder sequence above.

---

**IF Developer reports ESCALATE_SENIOR:**

#### SPAWN SSE ON ESCALATION (SKILL-BASED PROMPT)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_senior_software_engineer_{group_id}.json`:
```json
{
  "agent_type": "senior_software_engineer",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Escalation: {original_task[:60]}",
  "task_requirements": "ORIGINAL TASK: {original_task}\nDEVELOPER'S ATTEMPT: {developer_attempt}\nESCALATION REASON: {escalation_reason}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"senior_software_engineer\"]}",
  "output_file": "bazinga/prompts/{session_id}/senior_software_engineer_{group_id}.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn SSE with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], description="SSE {group_id}: escalation", prompt="FIRST: Read bazinga/prompts/{session_id}/senior_software_engineer_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

---

**IF Developer reports INCOMPLETE (partial work done):**
- **IMMEDIATELY spawn new developer Task using unified two-turn sequence**
- Track revision count in database FIRST:
  ```
  bazinga-db, update task group:
  Group ID: {group_id}
  Revision Count: {revision_count + 1}
  ```
  Invoke: `Skill(command: "bazinga-db")`

#### SPAWN DEVELOPER RETRY (SKILL-BASED PROMPT)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_developer_{group_id}_retry.json`:
```json
{
  "agent_type": "developer",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Continuation: {task_title}",
  "task_requirements": "WORK COMPLETED SO FAR: {summary_of_completed_work}\n\nREMAINING GAPS/ISSUES: {specific_gaps_and_issues}\n\nCONCRETE NEXT STEPS: {next_steps}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"developer\"]}",
  "output_file": "bazinga/prompts/{session_id}/developer_{group_id}_retry.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn Developer with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], description="Dev {group_id}: continuation", prompt="FIRST: Read bazinga/prompts/{session_id}/developer_{group_id}_retry.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

---

**IF revision count >= 1 (Developer failed once):**
- Escalate to SSE using the "SPAWN SSE ON ESCALATION" unified sequence above

**IF Senior Software Engineer also fails (revision count >= 2 after Senior Eng):**
- Spawn Tech Lead for architectural guidance using Tech Lead unified sequence

**🔴 CRITICAL:** Previous developer Task is DONE. You MUST spawn a NEW Task. Writing "Continue fixing NOW" does NOTHING - SPAWN the Task.

**🔴 CRITICAL: Do NOT wait for user input. Automatically proceed based on developer status.**

### Step 2A.4: Spawn QA Expert

**User output (capsule format):**
```
✅ Testing | Running tests + coverage analysis
```

### SPAWN QA EXPERT (SKILL-BASED PROMPT)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_qa_expert_{group_id}.json`:
```json
{
  "agent_type": "qa_expert",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Validate: {dev_task_title}",
  "task_requirements": "Developer Changes: {files_changed}\nChallenge Level: {level}/5",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"qa_expert\"]}",
  "output_file": "bazinga/prompts/{session_id}/qa_expert_{group_id}.md",
  "prior_handoff_file": "bazinga/artifacts/{session_id}/{group_id}/handoff_implementation.json"
}
```
**CRP:** `prior_handoff_file` points to implementation alias (works for both Developer and SSE).

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn QA Expert with file-based instructions**

Output summary:
```
📝 **QA Expert Prompt** | Group: {group_id} | Model: {model}
   **Task:** Validate {dev_task_title} | **Challenge Level:** {level}/5
   **Prompt file:** bazinga/prompts/{session_id}/qa_expert_{group_id}.md
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["qa_expert"], description="QA {group}: tests", prompt="FIRST: Read bazinga/prompts/{session_id}/qa_expert_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`


**AFTER receiving the QA Expert's response:**

**Step 1: Parse response and output capsule to user**

Use the QA Expert Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract:
- **Status** (PASS, FAIL, FAIL_ESCALATE, BLOCKED, FLAKY)
- **Tests** passed/total
- **Coverage** percentage
- **Failed tests** (if any)
- **Quality signals** (security, performance)

**Step 2: Construct capsule** per `response_parsing.md` §QA Response templates:
- **PASS:** `✅ Group {id} tests passing | {tests}, {coverage}% | → Tech Lead`
- **FAIL:** `⚠️ Group {id} QA failed | {failures} | Developer fixing`
- **BLOCKED:** `⚠️ Group {id} blocked | {blocker} | Investigating`
- **FAIL_ESCALATE:** `🔺 Group {id} challenge failed | Level {N}: {reason} | → SSE`
- **FLAKY:** `⚠️ Group {id} flaky tests | {details} | → Tech Lead`

**Step 3: Output capsule to user**

**Step 4: Log QA interaction** — Use §Logging Reference pattern. Agent ID: `qa_main`.

**AFTER logging: IMMEDIATELY continue to Step 2A.5. Do NOT stop.**

---

### Step 2A.5: Route QA Response

**IF QA approves:**
- **Immediately proceed to Step 2A.6** (Spawn Tech Lead)
- Do NOT stop for user input

**IF QA requests changes:**
- **IMMEDIATELY spawn new developer Task using prompt-builder**
- Track revision count in database (increment by 1)
- Use "SPAWN DEVELOPER RETRY (DETERMINISTIC PROMPT)" from Step 2A.3 above
- Include QA feedback and failed tests via --qa-feedback parameter

**IF revision count >= 1 OR QA reports challenge level 3+ failure:**
- Escalate to SSE with QA's challenge level findings
- Use "SPAWN SSE ON ESCALATION (DETERMINISTIC PROMPT)" from Step 2A.3 above

**IF QA reports ESCALATE_SENIOR explicitly:**
- Use "SPAWN SSE ON ESCALATION (DETERMINISTIC PROMPT)" from Step 2A.3 above

**🔴 SECURITY OVERRIDE:** If PM marked task as `security_sensitive: true`:
- ALWAYS spawn Senior Software Engineer for fixes (never regular Developer)
- Security tasks bypass normal revision count escalation - SSE from the start
- Use "SPAWN SSE ON ESCALATION (DETERMINISTIC PROMPT)" from Step 2A.3 above

**IF Senior Software Engineer also fails (revision >= 2 after Senior Eng):**
- Spawn Tech Lead for guidance using Tech Lead sequence below

**🔴 CRITICAL:** SPAWN the Task using prompt-builder - don't write "Fix the QA issues" and stop

### Step 2A.6: Spawn Tech Lead for Review

**User output (capsule format):**
```
👔 Reviewing | Security scan + lint check + architecture analysis
```

### SPAWN TECH LEAD (SKILL-BASED PROMPT)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_tech_lead_{group_id}.json`:
```json
{
  "agent_type": "tech_lead",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Review: {task_title}",
  "task_requirements": "QA Result: {qa_result}\nCoverage: {coverage_pct}%\nFiles Changed: {files_list}",
  "branch": "{branch}",
  "mode": "simple",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"tech_lead\"]}",
  "output_file": "bazinga/prompts/{session_id}/tech_lead_{group_id}.md",
  "prior_handoff_file": "bazinga/artifacts/{session_id}/{group_id}/handoff_qa_expert.json"
}
```
**CRP:** `prior_handoff_file` points to QA's handoff with test results.

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn Tech Lead with file-based instructions**

Output summary:
```
📝 **Tech Lead Prompt** | Group: {group_id} | Model: {model}
   **Task:** Review {task_title} | **QA:** {result} | **Coverage:** {pct}%
   **Prompt file:** bazinga/prompts/{session_id}/tech_lead_{group_id}.md
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["tech_lead"], description="TL {group}: review", prompt="FIRST: Read bazinga/prompts/{session_id}/tech_lead_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`


**AFTER receiving the Tech Lead's response:**

**Step 1: Parse response and output capsule to user**

Use the Tech Lead Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract:
- **Decision** (APPROVED, CHANGES_REQUESTED, SPAWN_INVESTIGATOR, ESCALATE_TO_OPUS)
- **Security issues** count
- **Lint issues** count
- **Architecture concerns**
- **Quality assessment**

**Step 2: Construct capsule** per `response_parsing.md` §Tech Lead Response templates:
- **APPROVED:** `👔 Group {id} ✅ | Security: {N}, Lint: {N}, Coverage: {N}% | Complete ({N}/{total})`
- **CHANGES_REQUESTED:** `⚠️ Group {id} needs changes | {issues} | Developer fixing`
- **SPAWN_INVESTIGATOR:** `🔬 Group {id} investigation | {problem} | Spawning investigator`
- **ESCALATE_TO_OPUS:** `⚠️ Group {id} escalated | {reason} | → Opus`

**Step 3: Output capsule to user**

**Step 4: Log Tech Lead interaction** — Use §Logging Reference pattern. Agent ID: `techlead_main`.

**AFTER logging: IMMEDIATELY continue to Step 2A.7. Do NOT stop.**

---

### Step 2A.6b: Investigation Loop Management (NEW - CRITICAL)

**IF Tech Lead reports: INVESTIGATION_IN_PROGRESS**

**📋 Full investigation loop procedure:** `bazinga/templates/investigation_loop.md` (v1.0)

**Entry Condition:** Tech Lead status = `INVESTIGATION_IN_PROGRESS`

**Required Context (must be available):**
- `session_id` - Current session (from Step 0)
- `group_id` - Current group ("main", "A", "B", etc.)
- `branch` - Developer's feature branch (from developer spawn context - verify available)
- `investigation_state` - Initialized with: problem_summary, hypothesis_matrix, suggested_skills (from Tech Lead)
- `skills_config` - For investigator skills (from Step 0)

**Loop Execution:**

1. **Read the full investigation procedure**

Use the Read tool to read the complete investigation loop:
```
Read(file_path: "bazinga/templates/investigation_loop.md")
```

2. **Execute all steps** in the template (up to 5 iterations)
3. **Return to orchestrator** at the exit code destination below

**Exit Codes (explicit routing):**

| Status | Condition | Next Action |
|--------|-----------|-------------|
| `ROOT_CAUSE_FOUND` | Investigator identified root cause | → Step 2A.6c (Tech Lead validates solution) |
| `BLOCKED` | Missing resources/access | → Escalate to PM for unblock decision |
| `incomplete` | Max 5 iterations reached | → Step 2A.6c (Tech Lead reviews partial findings) |

**Routing Actions Within Loop:**
- `NEED_DEVELOPER_DIAGNOSTIC` → Spawn Developer for instrumentation, continue loop
- `HYPOTHESIS_ELIMINATED` → Continue loop with next hypothesis
- `NEED_MORE_ANALYSIS` → Continue loop for deeper analysis

**Note:** Investigator cannot loop internally. Orchestrator manages iterations (max 5) as separate agent spawns.

---

### Step 2A.6c: Tech Lead Validation of Investigation (NEW)

**After investigation loop completes (root cause found OR incomplete):**

**User output (capsule format):**
```
👔 Validating investigation | Tech Lead reviewing {root_cause OR partial_findings} | Assessing solution quality
```

**Build Tech Lead Validation Prompt:**

Read `agents/techlead.md` and prepend:

```
---
🔬 INVESTIGATION RESULTS FOR VALIDATION
---
Session ID: [session_id]
Group ID: [group_id]
Investigation Status: [completed|incomplete]
Total Iterations: [N]

[IF status == "completed"]
Root Cause Found:
[investigation_state.root_cause]

Confidence: [investigation_state.confidence]

Evidence:
[investigation_state.evidence]

Recommended Solution:
[investigation_state.solution]

Iteration History:
[investigation_state.iterations_log]

Your Task:
1. Validate the Investigator's logic and evidence
2. Verify the root cause makes sense
3. Review the recommended solution
4. Make decision: APPROVED (accept solution) or CHANGES_REQUESTED (needs refinement)
[ENDIF]

[IF status == "incomplete"]
Investigation Status: Incomplete after 5 iterations

Progress Made:
[investigation_state.iterations_log]

Partial Findings:
[investigation_state.partial_findings]

Hypotheses Tested:
[list of tested hypotheses and results]

Your Task:
1. Review progress and partial findings
2. Decide:
   - Accept partial solution (implement what we know)
   - Continue investigation (spawn Investigator again with new approach)
   - Escalate to PM for reprioritization
[ENDIF]
---

[REST OF agents/techlead.md content]
```

**Spawn Tech Lead:**
```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["tech_lead"],
  description: "Tech Lead validation of investigation",
  prompt: [Tech Lead prompt built above],
  run_in_background: false
)
```

**After Tech Lead responds:**

**Log Tech Lead validation** — Use §Logging Reference pattern. Agent ID: `techlead_validation`.

**Tech Lead Decision:**
- Reviews Investigator's logic
- Checks evidence quality
- Validates recommended solution
- Makes decision: APPROVED (solution good) or CHANGES_REQUESTED (needs refinement)

**Route based on Tech Lead decision** (continue to Step 2A.7)

---

### Step 2A.7: Route Tech Lead Response

**IF Tech Lead approves:**
- **Trigger strategy extraction** (capture successful patterns for future context):
  ```
  bazinga-db, please extract strategies:

  Session ID: {session_id}
  Group ID: {group_id}
  Project ID: {project_id}
  Lang: {detected_lang}
  Framework: {detected_framework}
  ```
  Then invoke: `Skill(command: "bazinga-db")`
  *Note: This is non-blocking - proceed even if extraction fails*
- **Immediately proceed to Step 2A.7a** (Spawn Developer for immediate merge)
- Do NOT stop for user input
- Do NOT skip merge step - branches must be merged immediately after approval

**IF Tech Lead requests changes:**
- **IMMEDIATELY spawn appropriate agent Task** with Tech Lead feedback (do NOT just write a message)

**Determine which agent to spawn:**
- If code issues → Spawn Developer (or SSE based on revision count) with Tech Lead's code feedback
- If test issues → Spawn QA Expert with Tech Lead's test feedback

**🔴 MANDATORY: Use prompt-builder to build complete prompts:**

For code issues (Developer/SSE):
- Use prompt-builder with agent_type based on revision count
- Include Tech Lead's feedback via --tl-feedback parameter
- prompt-builder will read agent file and validate markers automatically

For test issues (QA Expert):
- Use prompt-builder with agent_type=qa_expert
- Include Tech Lead's test feedback via --tl-feedback parameter

**Track revision count in database (increment by 1)**

**Escalation path:**
- IF revision count == 1: Escalate to Senior Software Engineer (uses MODEL_CONFIG["senior_software_engineer"])
- IF revision count == 2 AND previous was Senior Eng: Spawn Tech Lead for guidance
- IF revision count > 2: Spawn PM to evaluate if task should be simplified

**🔴 SECURITY OVERRIDE:** If PM marked task as `security_sensitive: true`:
- ALWAYS spawn Senior Software Engineer (never regular Developer)
- On failure, escalate directly to Tech Lead (skip revision count check)
- Security tasks CANNOT be simplified by PM - must be completed by SSE

**🔴 CRITICAL:** Use prompt-builder skill - DO NOT create custom prompts

**IF Tech Lead requests investigation:**
- Already handled in Step 2A.6b
- Should not reach here (investigation spawned earlier)

### Step 2A.7a: Spawn Developer for Merge (Immediate Merge-on-Approval)

**🔴 CRITICAL: Merge happens immediately after Tech Lead approval - NOT batched at end**

**User output (capsule format):**
```
🔀 Merging | Group {id} approved → Merging {feature_branch} to {initial_branch}
```

### 🔴 MANDATORY: Load Merge Workflow Template

**⚠️ YOU MUST READ AND FOLLOW the merge workflow template. This is NOT optional.**

```
Read(file_path: "bazinga/templates/merge_workflow.md")
```

**If Read fails:** Output `❌ Template load failed | merge_workflow.md` and STOP.

**After reading the template, you MUST:**
1. Build the merge prompt using the template's prompt structure
2. Spawn Developer with the merge task
3. Handle the response according to the routing rules below
4. Apply escalation rules for repeated failures

**Status Routing (inline safety net):**

| Status | Action |
|--------|--------|
| `MERGE_SUCCESS` | Update group + progress (see below) → Step 2A.8 (PM check) |
| `MERGE_CONFLICT` | Spawn Developer with conflict context → Retry: Dev→QA→TL→Dev(merge) |
| `MERGE_TEST_FAILURE` | Spawn Developer with test failures → Retry: Dev→QA→TL→Dev(merge) |
| `MERGE_BLOCKED` | Spawn Tech Lead to assess blockage |
| *(Unknown status)* | Route to Tech Lead with "UNKNOWN_STATUS" reason → Tech Lead assesses |

**MERGE_SUCCESS Progress Tracking:**
1. Update task_group: status="completed", merge_status="merged"
2. Query completed progress from task_groups using bazinga-db skill:
   ```
   bazinga-db, please get task groups:

   Session ID: [session_id]
   Status: completed
   ```
   Then invoke: `Skill(command: "bazinga-db")`
   Sum item_count from the returned JSON to get completed items.
3. Output capsule with progress: `✅ Group {id} merged | Progress: {completed_sum}/{total_sum}`

**Escalation (from template):** 2nd fail → SSE, 3rd fail → TL, 4th+ → PM

**DO NOT proceed without reading and applying `bazinga/templates/merge_workflow.md`.**

### Step 2A.8: Spawn PM for Final Check

**FIRST:** Output §Technical Review Summary from `message_templates.md` (aggregate all Tech Lead responses).
**Skip if:** Only one group (already shown in individual review).

**THEN:** Build PM prompt using prompt-builder skill:

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_project_manager_final.json`:
```json
{
  "agent_type": "project_manager",
  "session_id": "{session_id}",
  "group_id": "global",
  "task_title": "Final Assessment",
  "task_requirements": "Implementation Summary: {implementation_summary}\n\nQuality Metrics: {quality_metrics}\n\nAssess if all success criteria are met and decide: BAZINGA or CONTINUE",
  "branch": "{branch}",
  "mode": "{mode}",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"project_manager\"]}",
  "output_file": "bazinga/prompts/{session_id}/project_manager_final.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn PM with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["project_manager"], description="PM final assessment", prompt="FIRST: Read bazinga/prompts/{session_id}/project_manager_final.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

**AFTER PM response:** Parse using `response_parsing.md` §PM Response Parsing. Construct output capsule:
- **BAZINGA:** §Completion template (groups, tests, criteria)
- **CONTINUE:** §PM Assessment template (status, issues, next)
- **NEEDS_CLARIFICATION:** `⚠️ PM needs clarification | {question} | Awaiting response`
- **INVESTIGATION_NEEDED:** `🔬 Investigation needed | {problem} | Spawning Investigator` → §Step 2A.6b

**Apply fallbacks:** If data missing, use generic descriptions per `response_parsing.md`.

**IF PM response lacks explicit status code:**

**🔴 AUTO-ROUTE WHEN PM ASKS FOR PERMISSION (not product questions)**

**PRECEDENCE:** If PM includes explicit status code (CONTINUE, BAZINGA, NEEDS_CLARIFICATION), use that status. Only apply inference when status is missing.

**Detect PERMISSION-SEEKING patterns (auto-route these):**
- "Would you like me to continue/proceed/start/resume..."
- "Should I spawn/assign/begin..."
- "Do you want me to keep going..."

**DO NOT auto-route PRODUCT/TECHNICAL questions:**
- "Would you like Postgres or MySQL?" → NEEDS_CLARIFICATION (legitimate)
- "Should the API use REST or GraphQL?" → NEEDS_CLARIFICATION (legitimate)

**Inference rules (only when no explicit status):**
- Mentions failures, errors, blockers → INVESTIGATION_NEEDED
- Requests changes, fixes, updates → CONTINUE
- Indicates completion or approval → BAZINGA
- Asks about requirements/scope/technical choices → NEEDS_CLARIFICATION
- **Permission-seeking pattern detected** → CONTINUE (PM shouldn't ask permission)

**ENFORCEMENT:** After inferring, immediately spawn the appropriate agent.

**Step 3: Output capsule to user**

**Step 4: Track velocity:**
```
velocity-tracker, please analyze completion metrics
```
**Then invoke:**
```
Skill(command: "velocity-tracker")
```



**Log PM interaction** — Use §Logging Reference pattern. Agent ID: `pm_final`.

### Step 2A.9: Route PM Response (Simple Mode)

**IF PM sends BAZINGA:**
- **Immediately proceed to Completion phase** (no user input needed)

**IF PM sends CONTINUE:**
- Query task groups (§Step 1.4) → Parse PM feedback → Identify what needs fixing
- Build revision prompt per §Step 2A.1 → Spawn agent → Log to database
- Update iteration count in database → Continue workflow (Dev→QA→Tech Lead→PM)

**❌ DO NOT ask "Would you like me to continue?" - just spawn immediately**

**IF PM sends INVESTIGATION_NEEDED:**
- **Immediately spawn Investigator** (no user permission required)
- Extract problem description from PM response

**🔴 Reasoning Timeline Query (BEFORE building Investigator prompt):**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet reasoning-timeline \
  "{session_id}" --group_id "{group_id}"
```

**Reasoning Timeline Prompt Section** (include when timeline found):

**⚠️ Size limits:** Truncate each entry to 300 chars max. Include max 10 entries total. Prioritize `blockers` and `pivot` phases.

```markdown
## Agent Reasoning Timeline (Investigation Context)

Prior agents' documented decision progression:

| Time | Agent | Phase | Confidence | Summary (max 300 chars) |
|------|-------|-------|------------|-------------------------|
| {timestamp} | {agent_type} | {phase} | {confidence} | {summary_truncated_300_chars}... |

**Investigation Focus:**
- Review `blockers` and `pivot` entries for failed approaches
- Check confidence drops that may indicate problem areas
- Use timeline to avoid repeating prior failed hypotheses
```

- **🔴 Use Step 2A.6b (SPAWN INVESTIGATOR sequence)** which includes:
  * Invoke prompt-builder skill with agent_type=investigator
  * prompt-builder reads agent file, builds context, and validates markers
  * Context includes: Session ID, Group ID, Branch, Problem description, Evidence, Reasoning Timeline
- After Investigator response: Route to Tech Lead for validation (Step 2A.6c)
- Continue workflow automatically (Investigator→Tech Lead→Developer→QA→Tech Lead→PM)

**❌ DO NOT ask "Should I spawn Investigator?" - spawn immediately**

**IF PM sends NEEDS_CLARIFICATION:**
- Follow clarification workflow from Step 1.3a (only case where you stop for user input)

**IMPORTANT:** All agent prompts follow `bazinga/templates/prompt_building.md` (loaded at initialization).

---

## 🔴 PHASE COMPLETION - MANDATORY PM RE-SPAWN

**When ALL groups in this phase are APPROVED and MERGED:**

### What You MUST Do:

1. **DO NOT** summarize to user and stop
2. **DO NOT** ask user what to do next
3. **DO NOT** ask "Would you like me to continue?"
4. **MUST** spawn PM immediately

### Mandatory PM Spawn (SKILL-BASED PROMPT):

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_project_manager_phase_{N}.json`:
```json
{
  "agent_type": "project_manager",
  "session_id": "{session_id}",
  "group_id": "global",
  "task_title": "Phase {N} Assessment",
  "task_requirements": "Phase {N} complete. All groups approved and merged: {group_list}.\n\nQuery database for Original_Scope and compare to completed work:\n- Original estimated items: {Original_Scope.estimated_items}\n- Completed items: {sum of completed group item_counts}\n\nBased on this comparison, you MUST either:\n- Assign next phase groups (if work remains from Original_Scope), OR\n- Send BAZINGA (if ALL original tasks from scope are complete)\n\nDO NOT ask for permission. Make the decision based on scope comparison.",
  "branch": "{branch}",
  "mode": "{mode}",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"project_manager\"]}",
  "output_file": "bazinga/prompts/{session_id}/project_manager_phase_{N}.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn PM with file-based instructions**

```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["project_manager"],
  description: "PM: Phase {N} complete - assess scope",
  prompt: "FIRST: Read bazinga/prompts/{session_id}/project_manager_phase_{N}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.",
  run_in_background: false
)
```

### Why This Rule Exists:

Without this mandatory re-spawn:
- Orchestrator may stop after phase completion
- User has to manually restart
- Original scope tracking is lost
- Multi-phase tasks don't complete

**NEVER stop between phases. ALWAYS spawn PM to decide next steps or send BAZINGA.**

---
