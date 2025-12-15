## Phase 2A: Simple Mode Execution

**Before any Bash command:** See §Policy-Gate and §Bash Command Allowlist in orchestrator.md

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

**This enables graduated token zones in context-assembler.** Without tracking, zone detection always defaults to "Normal" and graduated budget management won't activate.

**State persistence:** total_spawns is stored in session state via bazinga-db, incremented after each spawn, and passed to context-assembler for zone detection.

---

### Step 2A.1: Spawn Single Developer

**User output:** `🔨 Implementing | Spawning developer for {brief_task_description}`

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

### SPAWN IMPLEMENTATION AGENT (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

This section handles spawning Developer, SSE, or RE based on PM's `initial_tier` decision.

**TURN 1: Invoke Both Skills**

**A. Context Assembly** (check `skills_config.json` → `context_engineering.enable_context_assembler`):

IF context-assembler ENABLED:
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: {agent_type}  // developer, senior_software_engineer, or requirements_engineer
- Model: {MODEL_CONFIG[agent_type]}
- Current Tokens: {estimated_token_usage}
- Iteration: {iteration_count}
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`
→ Verify: Contains `## Context for {agent_type}` or zone/packages metadata

**Reasoning Auto-Inclusion Rules (handled by context-assembler):**
| Agent Type | Iteration | Reasoning Included? | Level |
|------------|-----------|---------------------|-------|
| `developer` | 0 (initial) | **NO** | - |
| `developer` | > 0 (retry) | **YES** | medium (800 tokens) |
| `senior_software_engineer` | any | **YES** | medium (800 tokens) |
| `requirements_engineer` | any | **YES** | medium (800 tokens) |

**Note:** `estimated_token_usage` = `total_spawns * 15000`. If not tracked yet, pass 0.

IF context-assembler DISABLED or returns empty:
→ Output warning: `⚠️ Context assembly empty | Proceeding without prior reasoning`
→ Set `{CONTEXT_BLOCK}` = "" (empty, non-blocking)

**B. Specialization Loading:**

Check `bazinga/skills_config.json` → `specializations.enabled` and `enabled_agents`:

IF specializations ENABLED for this agent type:
```
[SPEC_CTX_START group={group_id} agent={agent_type}]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: {agent_type}
Model: {MODEL_CONFIG[agent_type]}
Specialization Paths: {specializations from task_group or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`
→ Verify: Contains `[SPECIALIZATION_BLOCK_START]`

IF specializations DISABLED:
→ Set `{SPEC_BLOCK}` = "" (empty)

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked (or explicitly disabled in skills_config)?
- [ ] Specialization-loader invoked (or explicitly disabled)?
- [ ] Both skills returned valid output (or empty with warning)?

END TURN 1 (wait for skill responses)

---

**TURN 2: Compose & Spawn**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):

```
task_title = task_group["title"]
task_requirements = task_group["requirements"]
branch = task_group["branch"] or session_branch
group_id = task_group["group_id"]
agent_type = task_group["initial_tier"]  // developer, senior_software_engineer, or requirements_engineer

// 🔴 MANDATORY: Read the FULL agent file
// NOTE: tech_lead maps to techlead.md (no underscore), all others use {agent_type}.md
AGENT_FILE_MAP = {
  "developer": "agents/developer.md",
  "senior_software_engineer": "agents/senior_software_engineer.md",
  "requirements_engineer": "agents/requirements_engineer.md",
  "qa_expert": "agents/qa_expert.md",
  "tech_lead": "agents/techlead.md",  // NOTE: no underscore!
  "investigator": "agents/investigator.md"
}
IF agent_type NOT IN AGENT_FILE_MAP:
    Output: `❌ Unknown agent type: {agent_type} | Cannot spawn without agent file` and STOP
agent_file_path = AGENT_FILE_MAP[agent_type]
agent_definition = Read(agent_file_path)  // Full 1400+ lines of agent instructions
IF Read fails OR agent_definition is empty:
    Output: `⚠️ Agent file read failed | {agent_file_path}` and STOP

// Build task context to append
task_context = """
---

## Current Task Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple
**BRANCH:** {branch}

**TASK:** {task_title}

**REQUIREMENTS:**
{task_requirements}

**COMMIT TO:** {branch}
**REPORT STATUS:** READY_FOR_QA or BLOCKED when complete
"""

// Combine: Full agent definition + Task context
base_prompt = agent_definition + task_context
```

**D. Compose Full Prompt**:
```
prompt =
  {CONTEXT_BLOCK}  // Prior reasoning + packages (from context-assembler)
  +
  {SPEC_BLOCK}     // Tech identity (from specialization-loader)
  +
  base_prompt      // Full agent file + task context
```

**E. Spawn Agent:**

Output summary:
```
📝 **{agent_type} Prompt** | Group: {group_id} | Model: {model}
   **Task:** {task_title}
   **Branch:** {branch}
   **Specializations:** {status}
   **Context:** {status}
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent_type], description="{agent_type}: {task_title[:90]}", prompt={CONTEXT_BLOCK + SPEC_BLOCK + base_prompt})`

**🔴 SELF-CHECK (Turn 2):**
- ✅ Did I extract CONTEXT_BLOCK from context-assembler output?
- ✅ Did I extract SPEC_BLOCK from specialization-loader output?
- ✅ Does this message contain `Task()`?
- ✅ Is Task() called with combined prompt (context + spec + base)?

---

**🔴🔴🔴 SILENT PROCESSING - DO NOT PRINT BLOCKS 🔴🔴🔴**

Process skill outputs SILENTLY:
1. **INTERNALLY** extract CONTEXT_BLOCK and SPEC_BLOCK
2. **INTERNALLY** build full prompt
3. **OUTPUT** only brief capsule (shown above)
4. **CALL** `Task()` with full prompt

**🔴 FORBIDDEN - DO NOT OUTPUT:**
- ❌ The context block content
- ❌ The specialization block content
- ❌ The full prompt content
- ❌ Any "here's what I'm sending..." preview

**✅ CORRECT (capsule only, Task called):**
```
📝 **Developer Prompt** | Group: main | Model: haiku
   **Task:** Implement OAuth login
   **Specializations:** ✓ (3 templates)
   **Context:** ✓ (2 packages)

Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], description="Developer: Implement OAuth login", prompt=FULL_PROMPT)
```

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
- **READY_FOR_QA/REVIEW:** `🔨 Group {id} [{tier}] complete | {summary}, {files}, {tests} ({coverage}%) | → {next}`
- **PARTIAL:** `🔨 Group {id} [{tier}] implementing | {done} | {status}`
- **BLOCKED:** `⚠️ Group {id} [{tier}] blocked | {blocker} | Investigating`
- **ESCALATE_SENIOR:** `🔺 Group {id} [{tier}] escalating | {reason} | → SSE`

**Tier notation:** `[SSE/Sonnet]`, `[Dev/Haiku]`

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

#### SPAWN INVESTIGATOR (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

**TURN 1: Invoke Both Skills**

**A. Context Assembly:**
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: investigator
- Model: {MODEL_CONFIG["investigator"]}
- Current Tokens: {estimated_token_usage}
- Iteration: 0
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`

**Note:** Reasoning is **automatically included** for Investigator at medium level (800 tokens). Investigator receives Developer's reasoning for debugging context.

**B. Specialization Loading:**
```
[SPEC_CTX_START group={group_id} agent=investigator]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: investigator
Model: {MODEL_CONFIG["investigator"]}
Specialization Paths: {specializations from task_group or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked?
- [ ] Specialization-loader invoked?

END TURN 1

---

**TURN 2: Compose & Spawn Investigator**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):
```
// 🔴 MANDATORY: Read the FULL Investigator agent file
investigator_definition = Read("agents/investigator.md")  // Full agent instructions
IF Read fails OR investigator_definition is empty:
    Output: `⚠️ Agent file read failed | agents/investigator.md` and STOP

// Build task context to append
task_context = """
---

## Current Investigation Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}

**BLOCKER:** {blocker_description}
**Evidence from Developer:** {developer_evidence}

**INVESTIGATE AND REPORT:** ROOT_CAUSE_FOUND or BLOCKED when complete
"""

// Combine: Full agent definition + Task context
base_prompt = investigator_definition + task_context
```

**D. Compose Full Prompt & Spawn**:
```
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["investigator"], description="Investigator: {blocker[:60]}", prompt={prompt})`

After Investigator provides solution, spawn Developer again with resolution using the unified sequence above.

---

**IF Developer reports ESCALATE_SENIOR:**

#### SPAWN SSE ON ESCALATION (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

**TURN 1: Invoke Both Skills**

**A. Context Assembly:**
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: senior_software_engineer
- Model: {MODEL_CONFIG["senior_software_engineer"]}
- Current Tokens: {estimated_token_usage}
- Iteration: 0
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`

**Note:** Reasoning is **automatically included** for SSE at medium level (800 tokens). SSE receives Developer's reasoning to understand what was tried.

**B. Specialization Loading:**
```
[SPEC_CTX_START group={group_id} agent=senior_software_engineer]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: senior_software_engineer
Model: {MODEL_CONFIG["senior_software_engineer"]}
Specialization Paths: {specializations from task_group or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked?
- [ ] Specialization-loader invoked?

END TURN 1

---

**TURN 2: Compose & Spawn SSE**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):
```
// 🔴 MANDATORY: Read the FULL SSE agent file
sse_definition = Read("agents/senior_software_engineer.md")  // Full agent instructions
IF Read fails OR sse_definition is empty:
    Output: `⚠️ Agent file read failed | agents/senior_software_engineer.md` and STOP

// Build task context to append
task_context = """
---

## Escalation Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple
**BRANCH:** {branch}

**ORIGINAL TASK:** {original_task}
**DEVELOPER'S ATTEMPT:** {developer_attempt}
**ESCALATION REASON:** {escalation_reason}

**COMMIT TO:** {branch}
**REPORT STATUS:** READY_FOR_QA or BLOCKED when complete
"""

// Combine: Full agent definition + Task context
base_prompt = sse_definition + task_context
```

**D. Compose Full Prompt & Spawn**:
```
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], description="SSE {group_id}: escalation", prompt={prompt})`

---

**🔴 LAYER 2 SELF-CHECK (STEP-LEVEL FAIL-SAFE):**

Before moving to the next group or ending your message, verify:
1. ✅ Did I invoke BOTH context-assembler AND specialization-loader in Turn 1?
2. ✅ Did I spawn Task() in Turn 2?

**IF NO:** You violated the workflow. Complete the spawn sequence NOW.

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

#### SPAWN DEVELOPER RETRY (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

**TURN 1: Invoke Both Skills**

**A. Context Assembly:**
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: developer
- Model: {MODEL_CONFIG["developer"]}
- Current Tokens: {estimated_token_usage}
- Iteration: {revision_count + 1}  // > 0 triggers reasoning inclusion
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`

**Note:** Reasoning is **automatically included** for developer retries (iteration > 0) at medium level (800 tokens).

**B. Specialization Loading:**
```
[SPEC_CTX_START group={group_id} agent=developer]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: developer
Model: {MODEL_CONFIG["developer"]}
Specialization Paths: {specializations from task_group or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked with Iteration > 0?
- [ ] Specialization-loader invoked?

END TURN 1

---

**TURN 2: Compose & Spawn Developer**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):
```
// 🔴 MANDATORY: Read the FULL Developer agent file
dev_definition = Read("agents/developer.md")  // Full agent instructions
IF Read fails OR dev_definition is empty:
    Output: `⚠️ Agent file read failed | agents/developer.md` and STOP

// Build task context to append
task_context = """
---

## Continuation Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple
**BRANCH:** {branch}
**ITERATION:** {revision_count + 1}

**WORK COMPLETED SO FAR:**
{summary_of_completed_work}

**REMAINING GAPS/ISSUES:**
{specific_gaps_and_issues}

**REQUIREMENTS:**
{user_completion_requirements}

**CONCRETE NEXT STEPS:**
{next_steps}

**COMMIT TO:** {branch}
**REPORT STATUS:** READY_FOR_QA or BLOCKED when complete
"""

// Combine: Full agent definition + Task context
base_prompt = dev_definition + task_context
```

**D. Compose Full Prompt & Spawn**:
```
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], description="Dev {group_id}: continuation", prompt={prompt})`

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

### SPAWN QA EXPERT (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

**TURN 1: Invoke Both Skills**

**A. Context Assembly** (check `skills_config.json` → `context_engineering.enable_context_assembler`):

IF context-assembler ENABLED:
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: qa_expert
- Model: {MODEL_CONFIG["qa_expert"]}
- Current Tokens: {estimated_token_usage}
- Iteration: {iteration_count}
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`
→ Verify: Contains `## Context for qa_expert` or zone/packages metadata

**Note:** Reasoning is **automatically included** for `qa_expert` at medium level (800 tokens). Prior Developer reasoning provides handoff continuity.

IF context-assembler DISABLED or returns empty:
→ Set `{CONTEXT_BLOCK}` = "" (empty, non-blocking)

**B. Specialization Loading:**
```
[SPEC_CTX_START group={group_id} agent=qa_expert]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: qa_expert
Model: {MODEL_CONFIG["qa_expert"]}
Specialization Paths: {specializations from PM or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`
→ Verify: Contains `[SPECIALIZATION_BLOCK_START]`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked (or explicitly disabled in skills_config)?
- [ ] Specialization-loader invoked?
- [ ] Both skills returned valid output?

END TURN 1 (wait for skill responses)

---

**TURN 2: Compose & Spawn**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):
```
// 🔴 MANDATORY: Read the FULL QA Expert agent file
qa_definition = Read("agents/qa_expert.md")  // Full agent instructions
IF Read fails OR qa_definition is empty:
    Output: `⚠️ Agent file read failed | agents/qa_expert.md` and STOP

// Build task context to append
task_context = """
---

## Current Task Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple

**TASK:** Validate {dev_task_title}
**Developer Changes:** {files_changed}
**Challenge Level:** {level}/5

**REPORT STATUS:** PASS, FAIL, or BLOCKED when complete
"""

// Combine: Full agent definition + Task context
base_prompt = qa_definition + task_context
```

**D. Compose Full Prompt**:
```
prompt =
  {CONTEXT_BLOCK}  // Prior reasoning + packages
  +
  {SPEC_BLOCK}     // Tech identity
  +
  base_prompt      // Full agent file + task context
```

**E. Spawn QA:**

Output summary:
```
📝 **QA Expert Prompt** | Group: {group_id} | Model: {model}
   **Task:** Validate {dev_task_title} | **Challenge Level:** {level}/5
   **Specializations:** {status}
   **Context Packages:** {count if any}
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["qa_expert"], description="QA {group}: tests", prompt={CONTEXT_BLOCK + SPEC_BLOCK + base_prompt})`

**🔴 SELF-CHECK (QA Spawn):**
- ✅ Did I query context packages for qa_expert?
- ✅ Does base_prompt include context packages (if any)?
- ✅ Is Task() called with spec_block + base_prompt?


**AFTER receiving the QA Expert's response:**

**Step 1: Parse response and output capsule to user**

Use the QA Expert Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract:
- **Status** (PASS, FAIL, PARTIAL, BLOCKED, FLAKY)
- **Tests** passed/total
- **Coverage** percentage
- **Failed tests** (if any)
- **Quality signals** (security, performance)

**Step 2: Construct capsule** per `response_parsing.md` §QA Response templates:
- **PASS:** `✅ Group {id} tests passing | {tests}, {coverage}% | → Tech Lead`
- **FAIL:** `⚠️ Group {id} QA failed | {failures} | Developer fixing`
- **BLOCKED:** `⚠️ Group {id} blocked | {blocker} | Investigating`
- **ESCALATE_SENIOR:** `🔺 Group {id} challenge failed | Level {N}: {reason} | → SSE`

**Step 3: Output capsule to user**

**Step 4: Log QA interaction** — Use §Logging Reference pattern. Agent ID: `qa_main`.

**AFTER logging: IMMEDIATELY continue to Step 2A.5. Do NOT stop.**

---

### Step 2A.5: Route QA Response

**IF QA approves:**
- **Immediately proceed to Step 2A.6** (Spawn Tech Lead)
- Do NOT stop for user input

**IF QA requests changes:**
- **IMMEDIATELY spawn new developer Task using unified two-turn sequence**
- Track revision count in database (increment by 1)
- Use "SPAWN DEVELOPER RETRY (TWO-TURN SEQUENCE)" from Step 2A.3 above
- Include QA feedback and failed tests in base prompt

**IF revision count >= 1 OR QA reports challenge level 3+ failure:**
- Escalate to SSE with QA's challenge level findings
- Use "SPAWN SSE ON ESCALATION (TWO-TURN SEQUENCE)" from Step 2A.3 above

**IF QA reports ESCALATE_SENIOR explicitly:**
- Use "SPAWN SSE ON ESCALATION (TWO-TURN SEQUENCE)" from Step 2A.3 above

**🔴 SECURITY OVERRIDE:** If PM marked task as `security_sensitive: true`:
- ALWAYS spawn Senior Software Engineer for fixes (never regular Developer)
- Security tasks bypass normal revision count escalation - SSE from the start
- Use "SPAWN SSE ON ESCALATION (TWO-TURN SEQUENCE)" from Step 2A.3 above

**IF Senior Software Engineer also fails (revision >= 2 after Senior Eng):**
- Spawn Tech Lead for guidance using Tech Lead unified sequence below

**🔴 CRITICAL:** SPAWN the Task using unified sequence - don't write "Fix the QA issues" and stop

### Step 2A.6: Spawn Tech Lead for Review

**User output (capsule format):**
```
👔 Reviewing | Security scan + lint check + architecture analysis
```

### SPAWN TECH LEAD (TWO-TURN SEQUENCE)

**🔴 PRE-SPAWN CHECKLIST - BOTH SKILLS REQUIRED**

**TURN 1: Invoke Both Skills**

**A. Context Assembly** (check `skills_config.json` → `context_engineering.enable_context_assembler`):

IF context-assembler ENABLED:
```
Assemble context for agent spawn:
- Session: {session_id}
- Group: {group_id}
- Agent: tech_lead
- Model: {MODEL_CONFIG["tech_lead"]}
- Current Tokens: {estimated_token_usage}
- Iteration: {iteration_count}
```
Then invoke: `Skill(command: "context-assembler")`
→ Capture output as `{CONTEXT_BLOCK}`
→ Verify: Contains `## Context for tech_lead` or zone/packages metadata

**Note:** Reasoning is **automatically included** for `tech_lead` at medium level (800 tokens). Prior Developer and QA reasoning provides review continuity.

IF context-assembler DISABLED or returns empty:
→ Set `{CONTEXT_BLOCK}` = "" (empty, non-blocking)

**B. Specialization Loading:**
```
[SPEC_CTX_START group={group_id} agent=tech_lead]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: tech_lead
Model: {MODEL_CONFIG["tech_lead"]}
Specialization Paths: {specializations from PM or project_context.json}
Testing Mode: {testing_mode}
[SPEC_CTX_END]
```
Then invoke: `Skill(command: "specialization-loader")`
→ Capture output as `{SPEC_BLOCK}`
→ Verify: Contains `[SPECIALIZATION_BLOCK_START]`

**✅ TURN 1 SELF-CHECK:**
- [ ] Context-assembler invoked (or explicitly disabled in skills_config)?
- [ ] Specialization-loader invoked?
- [ ] Both skills returned valid output?

END TURN 1 (wait for skill responses)

---

**TURN 2: Compose & Spawn**

**C. Read Agent File & Build Prompt** (internal, DO NOT OUTPUT):
```
// 🔴 MANDATORY: Read the FULL Tech Lead agent file
tl_definition = Read("agents/techlead.md")  // Full agent instructions
IF Read fails OR tl_definition is empty:
    Output: `⚠️ Agent file read failed | agents/techlead.md` and STOP

// Build task context to append
task_context = """
---

## Current Task Assignment

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Simple

**TASK:** Review {task_title}
**QA Result:** {qa_result}
**Coverage:** {coverage_pct}%
**Files Changed:** {files_list}

**REPORT STATUS:** APPROVED, CHANGES_REQUESTED, or SPAWN_INVESTIGATOR when complete
"""

// Combine: Full agent definition + Task context
base_prompt = tl_definition + task_context
```

**D. Compose Full Prompt**:
```
prompt =
  {CONTEXT_BLOCK}  // Prior reasoning + packages
  +
  {SPEC_BLOCK}     // Tech identity
  +
  base_prompt      // Full agent file + task context
```

**E. Spawn Tech Lead:**

Output summary:
```
📝 **Tech Lead Prompt** | Group: {group_id} | Model: {model}
   **Task:** Review {task_title} | **QA:** {result} | **Coverage:** {pct}%
   **Specializations:** {status}
   **Context Packages:** {count if any}
   **Reasoning Entries:** {count if any}
```
→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["tech_lead"], description="TL {group}: review", prompt={CONTEXT_BLOCK + SPEC_BLOCK + base_prompt})`

**🔴 SELF-CHECK (TL Spawn):**
- ✅ Did I query context packages for tech_lead?
- ✅ Did I query reasoning from implementation agents?
- ✅ Does base_prompt include context packages (if any)?
- ✅ Does base_prompt include reasoning (if any)?
- ✅ Is Task() called with spec_block + base_prompt?


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
  prompt: [Tech Lead prompt built above]
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
- If code issues → Spawn developer with Tech Lead's code feedback
- If test issues → Spawn QA Expert with Tech Lead's test feedback

**Build prompt and spawn Task:**
```
# Model selection: use MODEL_CONFIG for appropriate agent
Task(subagent_type="general-purpose", model=MODEL_CONFIG["{agent}"], description="{agent} {id}: fix Tech Lead issues", prompt=[prompt with feedback])
```

**Track revision count in database (increment by 1)**

**Escalation path:**
- IF revision count == 1: Escalate to Senior Software Engineer (uses MODEL_CONFIG["senior_software_engineer"])
- IF revision count == 2 AND previous was Senior Eng: Spawn Tech Lead for guidance
- IF revision count > 2: Spawn PM to evaluate if task should be simplified

**🔴 SECURITY OVERRIDE:** If PM marked task as `security_sensitive: true`:
- ALWAYS spawn Senior Software Engineer (never regular Developer)
- On failure, escalate directly to Tech Lead (skip revision count check)
- Security tasks CANNOT be simplified by PM - must be completed by SSE

**🔴 CRITICAL:** SPAWN the Task - don't write "Fix the Tech Lead's feedback" and stop

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

**THEN:** Build PM prompt with implementation summary + quality metrics → Spawn:
`Task(subagent_type="general-purpose", model=MODEL_CONFIG["project_manager"], description="PM final assessment", prompt=[PM prompt])`

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

- Build Investigator prompt with context:
  * Session ID, Group ID, Branch
  * Problem description (any blocker: test failures, build errors, deployment issues, bugs, performance problems, etc.)
  * Available evidence (logs, error messages, diagnostics, stack traces, metrics)
  * **Reasoning Timeline (if any)** - prior agent decisions and pivots
- Spawn: `Task(subagent_type="general-purpose", model=MODEL_CONFIG["investigator"], description="Investigate blocker", prompt=[Investigator prompt])`
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

### Mandatory PM Spawn Prompt:

```
Phase {N} complete. All groups approved and merged: {group_list}.

Query database for Original_Scope and compare to completed work:
- Original estimated items: {Original_Scope.estimated_items}
- Completed items: {sum of completed group item_counts}

Based on this comparison, you MUST either:
- Assign next phase groups (if work remains from Original_Scope), OR
- Send BAZINGA (if ALL original tasks from scope are complete)

DO NOT ask for permission. Make the decision based on scope comparison.
```

### Spawn Command:

```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["project_manager"],
  description: "PM: Phase {N} complete - assess scope",
  prompt: [PM prompt above]
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
