# Resume Workflow and Session Initialization

**This file contains the resume workflow (scope preservation) and new session initialization steps.**
**Read by orchestrator during Initialization phase.**

---

## 🔴 SCOPE PRESERVATION (MANDATORY FOR RESUME)

**Original Scope (from session creation):**
- Raw Request: {Original_Scope.raw_request}
- Scope Type: {Original_Scope.scope_type}
- Scope Reference: {Original_Scope.scope_reference}
- Estimated Items: {Original_Scope.estimated_items}

**User's Current Request:** {user_current_message}

**YOUR TASK - SCOPE COMPARISON:**
1. Compare user's current request with Original_Scope.raw_request
2. IF current request implies SAME OR NARROWER scope:
   - Normal resume - continue from where we left off
3. IF current request implies BROADER scope (more items, more phases, additional work):
   - DO NOT narrow to current PM state
   - Create additional task groups for the expanded scope
   - Status: PLANNING_COMPLETE (not CONTINUE) to signal new groups created
4. IF user explicitly requests "everything" or "all of [file/feature]":
   - This means FULL Original_Scope, not just current progress
   - Ensure task groups cover 100% of Original_Scope

**NEVER reduce scope below Original_Scope without explicit user approval.**

---

**After PM responds:** Route using Step 1.3a. In resume scenarios, PM typically returns:
- `CONTINUE` → Immediately spawn agents for in_progress/pending groups (Step 2A.1 or 2B.1)
- `BAZINGA` → Session already complete, proceed to Completion phase
- `NEEDS_CLARIFICATION` → Follow clarification workflow

**🔴 CRITICAL - COMPLETE ALL STEPS IN SAME TURN (NO USER WAIT):**
1. Log PM interaction to database
2. Parse PM status (CONTINUE/BAZINGA/etc)
3. Start spawn sequence or proceed to completion - **all within this turn**
4. Saying "I will spawn" or "Let me spawn" is NOT spawning - call Skill() or Task() tool NOW
   - Call `Skill(command: "prompt-builder")` to build the prompt
   - Then call `Task()` with the built prompt
5. Multi-step sequences (DB query → prompt-builder → spawn) are expected within the same turn

---

**Step 6: Handle PM Response in Resume (CRITICAL)**

**After PM responds, route based on PM's status code:**

| PM Status | Action |
|-----------|--------|
| `CONTINUE` | **IMMEDIATELY start spawn sequence** for pending groups. Call prompt-builder, then Task(). |
| `BAZINGA` | Session is complete → Jump to Completion phase, invoke validator |
| `PLANNING_COMPLETE` | New work added → Jump to Step 1.4, then Phase 2 |
| `NEEDS_CLARIFICATION` | Surface question to user |

**🔴 INTENT WITHOUT ACTION:** If PM says CONTINUE, call `Skill(command: "prompt-builder")` + `Task()` NOW. Don't just describe it.

---

**REMEMBER:** After receiving the session list in Step 0, you MUST execute Steps 1-6 in sequence without stopping. After PM responds, route according to Step 1.3a and continue spawning agents without waiting for user input. These are not optional - they are the MANDATORY resume workflow.

---

## Path B: CREATE NEW SESSION

**IF no active sessions found OR user explicitly requested new session:**

### Step 1: Generate session ID
```bash
SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
```

### Step 2: Create artifacts directory structure
```bash
# Create artifacts directories for this session (required for build baseline logs and skill outputs)
mkdir -p "bazinga/artifacts/${SESSION_ID}"
mkdir -p "bazinga/artifacts/${SESSION_ID}/skills"
```

### Step 3: Create session in database

**🔴 MANDATORY SESSION CREATION - CANNOT BE SKIPPED**

**YOU MUST invoke the bazinga-db skill to create a new session.**
**Database will auto-initialize if it doesn't exist (< 2 seconds).**

Request to bazinga-db-core skill:
```
bazinga-db-core, please create a new orchestration session:

Session ID: $SESSION_ID
Mode: simple
Requirements: [User's requirements from input]
Initial_Branch: [result of git branch --show-current]
Original_Scope: {
  "raw_request": "[exact user request text verbatim]",
  "scope_type": "[file|feature|task_list|description]",
  "scope_reference": "[file path if scope_type=file, otherwise null]",
  "estimated_items": [count if determinable from file/list, null otherwise]
}
```

**Scope Type Detection:**
- `file` - User references a file (e.g., "implement tasks8.md")
- `task_list` - User provides numbered/bulleted list
- `feature` - User requests a feature (e.g., "add authentication")
- `description` - General description

**Note:** Mode is initially set to "simple" as a default. The PM will analyze requirements and may update this to "parallel" if multiple independent tasks are detected.
**Note:** Original_Scope is MANDATORY for validator scope checking. The validator uses this to verify PM's completion claims.

Then invoke:
```
Skill(command: "bazinga-db-core")
```

**IMPORTANT:** You MUST invoke bazinga-db-core skill here. Use the returned data.

**What "process silently" means:**
- ✅ DO: Verify the skill succeeded
- ✅ DO: Extract the session_id from response
- ❌ DON'T: Show raw skill output to user
- ❌ DON'T: Show "Session created in database ✓" confirmations

**Display to user (capsule format on success):**
```
🚀 Starting orchestration | Session: [session_id]
```

**IF bazinga-db skill fails or returns error:** Output `❌ Session creation failed | Database error | Cannot proceed - check bazinga-db skill` and STOP.

**AFTER successful session creation: IMMEDIATELY continue to step 3.5 (Seed workflow configs). Do NOT stop.**

### Step 3.5: Seed workflow configurations (MANDATORY)

**🔴 MANDATORY: Seed Workflow Configs to Database**

**YOU MUST invoke the config-seeder skill to seed routing and marker configs to database.**
**This enables deterministic prompt building and workflow routing.**

```
Skill(command: "config-seeder")
```

**Expected output:**
```
Seeded 45 transitions
Seeded 7 agent marker sets
Seeded 5 special rules
✅ Config seeding complete
```

**IF config-seeder skill fails:** Output `❌ Config seeding failed | Workflow routing unavailable | Cannot proceed` and STOP.
**Config seeding is MANDATORY** - without it, prompt-builder and workflow-router cannot function.

**AFTER successful config seeding: IMMEDIATELY continue to step 4 (Load configurations). Do NOT stop.**

### Step 4: Load configurations

```bash
# Read active skills configuration
cat bazinga/skills_config.json

# Read testing framework configuration
cat bazinga/testing_config.json
```

**Note:** Read configurations using Read tool, but don't show Read tool output to user - it's internal setup.

**AFTER reading configs: IMMEDIATELY continue to step 4.5 (Capability discovery). Do NOT stop.**

See `bazinga/templates/prompt_building.md` (loaded at initialization) for how these configs are used to build agent prompts.

### Step 4.5: Capability discovery (MANDATORY)

After loading skills_config.json, determine which skills are available:

```python
# skills_config.json structure: {"developer": {"lint-check": "mandatory", ...}, "tech_lead": {...}}
# May also have metadata fields like "_version", "_updated" - skip those
AVAILABLE_SKILLS = {}  # {agent_name: {skill_name: mode}}
CRITICAL_DISABLED = []

for agent_name, agent_skills in skills_config.items():
    # Skip metadata fields (start with underscore) and non-dict values
    if agent_name.startswith("_") or not isinstance(agent_skills, dict):
        continue
    AVAILABLE_SKILLS[agent_name] = {}
    for skill_name, mode in agent_skills.items():
        if mode != "disabled":
            AVAILABLE_SKILLS[agent_name][skill_name] = mode  # Track per-agent
        elif skill_name in ["lint-check", "security-scan", "test-coverage"]:
            if skill_name not in CRITICAL_DISABLED:  # Avoid duplicates
                CRITICAL_DISABLED.append(skill_name)

# Helper: Check if skill is available for a specific agent
# Usage: skill_available("developer", "lint-check") → True if enabled
# Note: Use before spawning to validate mandatory skills, or when conditionally invoking optional skills
def skill_available(agent: str, skill: str) -> bool:
    return skill in AVAILABLE_SKILLS.get(agent, {})
```

**Critical skill fallbacks:**
| Disabled Skill | Fallback Behavior |
|----------------|-------------------|
| `lint-check` | Skip lint validation (log warning) |
| `security-scan` | Skip security checks (⚠️ WARN USER) |
| `test-coverage` | Skip coverage checks (log warning) |

**IF any CRITICAL_DISABLED skills:**
```
⚠️ WARNING: Critical skills disabled: {CRITICAL_DISABLED}
- security-scan: Security vulnerabilities may not be detected
- lint-check: Code style issues may be missed
- test-coverage: Coverage gaps may not be identified
```

Store in session state: `disabled_skills: [list]`, `capability_warnings: [list]`

### Step 5: Load model configuration from database

**🔴 MANDATORY: Load Model Configuration**

**Query model configuration for all agents:**

Request to bazinga-db-core skill:
```
bazinga-db-core, please retrieve model configuration:
Query: Get all agent model assignments from model_config table
```

Then invoke:
```
Skill(command: "bazinga-db-core")
```

**Load model config from source of truth:**
```
Read(file_path: "bazinga/model_selection.json")
```

**Parse and store model mappings:**
```
MODEL_CONFIG = {}
for agent_name, agent_data in config["agents"].items():
    MODEL_CONFIG[agent_name] = agent_data["model"]
# e.g., MODEL_CONFIG["developer"] = "sonnet", MODEL_CONFIG["tech_lead"] = "opus"
```

**Source of truth:** `bazinga/model_selection.json` - NEVER hardcode model names elsewhere.

**🔄 CONTEXT RECOVERY:** If you lose model config (e.g., after context compaction), re-read:
```
Read(file_path: "bazinga/model_selection.json")
```

**Use MODEL_CONFIG values in ALL Task invocations instead of hardcoded models.**

### Step 6: Store config references in database

**🔴 MANDATORY: Store configuration in database**

**YOU MUST invoke bazinga-db-core skill to save orchestrator initial state.**

Request to bazinga-db-core skill:
```
bazinga-db-core, please save the orchestrator state:

Session ID: [current session_id]
State Type: orchestrator
State Data: {
  "session_id": "[current session_id]",
  "current_phase": "initialization",
  "skills_config_loaded": true,
  "active_skills_count": [count from skills_config.json],
  "testing_config_loaded": true,
  "testing_mode": "[mode from testing_config.json]",
  "qa_expert_enabled": [boolean from testing_config.json],
  "iteration": 0,
  "total_spawns": 0
}
```

Then invoke:
```
Skill(command: "bazinga-db-core")
```

**IMPORTANT:** You MUST invoke bazinga-db-core skill here. Use the returned data.

**What "process silently" means:**
- ✅ DO: Verify the skill succeeded
- ❌ DON'T: Show raw skill output to user
- ❌ DON'T: Show "Config saved ✓" confirmations

**IF skill fails:** Output `❌ Config save failed | Cannot proceed` and STOP.

**AFTER successful config save: IMMEDIATELY continue to step 6 (Build baseline check). Do NOT stop.**

### Step 7: Run build baseline check

**Note:** Run build check silently. No user output needed unless build fails.

```bash
bash bazinga/scripts/build-baseline.sh "$SESSION_ID"
```

The wrapper script:
- Auto-detects project language (package.json, go.mod, etc.)
- Runs appropriate build command
- Saves results to `bazinga/artifacts/{SESSION_ID}/build_baseline.log`
- Returns exit code: 0=success, 1=error

**Check result:**
- If exit code 0: Silent (no output)
- If exit code 1: `⚠️ Build baseline | Existing errors detected | Will track new errors`

**⚠️ DO NOT run inline npm/go/python commands** - use the wrapper script per §Bash Command Allowlist.

**AFTER build baseline check: IMMEDIATELY continue to step 7 (Load template guides). Do NOT stop.**

### Step 8: Load critical template guides

**⚠️ MANDATORY: Read templates that contain runtime instructions**

These templates are NOT documentation - they contain critical operational logic that must be loaded before orchestration begins.

```
Read(file_path: "bazinga/templates/message_templates.md")
Read(file_path: "bazinga/templates/response_parsing.md")
Read(file_path: "bazinga/templates/prompt_building.md")
```

**Verify all 3 templates loaded.** If ANY Read fails → Output `❌ Template load failed | [filename]` and STOP.

**AFTER loading and verifying templates: IMMEDIATELY continue to verification checkpoint below. Do NOT stop.**

---

## Database Storage

All state stored in SQLite database at `bazinga/bazinga.db`:
- **Tables:** sessions, orchestration_logs, state_snapshots, task_groups, token_usage, skill_outputs, configuration
- **Benefits:** Concurrent-safe, ACID transactions, fast indexed queries
- **Details:** See `.claude/skills/bazinga-db/SKILL.md` for complete schema

---

## ⚠️ INITIALIZATION VERIFICATION CHECKPOINT

**CRITICAL:** Verify initialization complete (session ID, database, configs loaded, templates loaded). User sees: `🚀 Starting orchestration | Session: [session_id]`

**Then IMMEDIATELY proceed to Step 0.5 - Tech Stack Detection.**
