# Optional Testing Framework Design - Complete Analysis

**Date:** 2025-11-09
**Status:** Proposal - Ready for Implementation
**Recommended Approach:** Option A (Granular Control with Preset Modes)
**Request:** Enable/Disable Testing Framework for rapid prototyping vs. production workflows

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Codebase Exploration Results](#codebase-exploration-results)
4. [Design Options (A, B, C)](#design-options-comparison)
5. [Implementation Plan - Option A](#implementation-plan---option-a-recommended)
6. [Usage Examples](#usage-examples)
7. [Critical Considerations](#critical-considerations)
8. [Expected Impact](#expected-impact)
9. [Recommendation](#recommendation)

---

## Executive Summary

This document proposes adding an **Enable/Disable Testing Framework** feature to BAZINGA's skill selection system, allowing users to choose different levels of testing rigor based on their development context (prototyping vs. production).

**Key Benefit:** Users can disable comprehensive testing workflows for rapid prototyping while preserving critical code quality checks (lint).

**Problem Statement:**
Some users want to develop without comprehensive testing for:
- Rapid prototyping
- Proof-of-concept development
- Experimental features
- Fast iteration cycles

**Current Limitation:**
The QA Expert and full testing workflow are tightly integrated and cannot be easily disabled.

**Proposed Solution:**
Add testing configuration with three modes:
- **Full**: All testing (current behavior)
- **Minimal**: Lint + unit tests, skip QA Expert
- **Disabled**: Lint only (fastest)

---

## Current State Analysis

### Testing Integration Points (Critical to Understand)

**Current Default Behavior:**
- Developer writes code + tests
- Pre-commit: lint + unit tests + build check
- Routing decision:
  - If integration/contract/E2E tests exist → READY_FOR_QA → QA Expert
  - If only unit tests → READY_FOR_REVIEW → Tech Lead directly
- Tech Lead reviews and approves
- PM tracks completion

---

## Codebase Exploration Results

### 1. Skill Selection & Configuration System

**Primary Configuration File:** `/bazinga/skills_config.json`

**Current State:**
```json
{
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "disabled",
    "test-pattern-analysis": "disabled",
    "api-contract-validation": "disabled",
    "db-migration-check": "disabled"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "lint-check": "mandatory",
    "test-coverage": "mandatory"
  },
  "qa_expert": {
    "pattern-miner": "disabled",
    "quality-dashboard": "disabled"
  },
  "pm": {
    "velocity-tracker": "mandatory"
  }
}
```

**Configuration Command:** `/.claude/commands/configure-skills.md`
- Interactive numbered menu (10 skills total)
- Supports presets (defaults, all, none, fast, advanced)
- Updates skills_config.json with "mandatory" or "disabled"
- Persists across sessions
- Tracked in git

**Skill Invocation Pattern:**
```bash
Skill(command: "skill-name")
```

Examples in codebase:
- `agents/developer.md:542,607` - `Skill(command: "lint-check")`
- `agents/orchestrator.md:584-814` - Multiple skill invocations

---

### 2. How Testing is Currently Integrated

**Key Decision Point: READY_FOR_QA vs READY_FOR_REVIEW**

Location: `agents/developer.md:825-860`

**Developer routing logic:**
- **WITH Tests** (integration/contract/E2E) → `READY_FOR_QA` → QA Expert
- **WITHOUT Tests** (only unit tests) → `READY_FOR_REVIEW` → Tech Lead directly

**QA Expert Agent Structure:**

Location: `agents/qa_expert.md:1-148`

Key characteristics:
- Line 22-24: "QA Expert is ONLY spawned when tests exist"
- Line 44: "You are ONLY spawned when Developer has created integration/contract/E2E tests"
- Line 98-99: "You run ALL three test types"
- Line 107-147: Available Skills (pattern-miner, quality-dashboard)

**Testing Integration in Developer Workflow:**

Location: `agents/developer.md:589-650`

**Pre-Commit Quality Validation:**
1. INVOKE lint-check Skill (MANDATORY) - Line 604-611
2. Fix ALL lint issues - Line 613-617
3. Run unit tests - Line 619-625
4. Run build check - Line 626-635
5. ONLY THEN commit - Line 637-642

**Test-Passing Integrity:** Lines 652-707
- Forbidden major changes to pass tests
- Requires Tech Lead validation for major changes

---

### 3. QA Tester Agent Invocation

**How QA Expert is Spawned:**

Location: `agents/orchestrator.md:700-850`

**Pattern:**
1. Developer reports status: `READY_FOR_QA` or `READY_FOR_REVIEW`
2. Orchestrator reads developer message
3. If `READY_FOR_QA`: Spawns QA Expert
4. If `READY_FOR_REVIEW`: Routes directly to Tech Lead

**Conditional Spawning Logic:**
```python
skills_config = read_json("bazinga/skills_config.json")
qa_skills = skills_config["qa_expert"]

# Check if pattern-miner or quality-dashboard are mandatory
IF qa_skills["pattern-miner"] == "mandatory" OR
   qa_skills["quality-dashboard"] == "mandatory":
    # Add to QA Expert spawn prompt
```

---

### 4. Configuration & Settings Storage

**State File Locations:**

Created by: `scripts/init-orchestration.sh`

**Permanent Configuration:**
- `/bazinga/skills_config.json` - Skills enable/disable (TRACKED IN GIT)

**Temporary State Files** (not tracked in git):
- `/bazinga/pm_state.json` - PM's persistent state
- `/bazinga/group_status.json` - Per-group progress
- `/bazinga/orchestrator_state.json` - Orchestrator state
- `/bazinga/messages/*.json` - Inter-agent messages

**Skills Results:**
- `bazinga/lint_results.json`
- `bazinga/coverage_report.json`
- `bazinga/security_scan.json`
- `bazinga/codebase_analysis_results.json`
- `bazinga/test_pattern_results.json`
- `bazinga/pattern_insights.json`
- `bazinga/quality_dashboard.json`

---

### 5. Agents Code Structure & Testing Decisions

**Agent Files:** `agents/`

1. **orchestrator.md** (74,654 bytes)
   - Line 140-159: Initialization - reads skills_config.json
   - Line 563-614: Developer spawning with conditional Skills injection
   - Line 800-825: QA Expert spawning with conditional Skills

2. **project_manager.md** (65,259 bytes)
   - Line 37-101: Workflow showing decision points
   - Line 78-101: Different patterns (WITH tests vs WITHOUT tests)
   - Line 110-117: Key principles about testing coordination

3. **developer.md** (33,211 bytes)
   - Line 32-38: Workflow showing READY_FOR_QA vs READY_FOR_REVIEW paths
   - Line 825-860: Explicit routing decision logic
   - Line 598-650: Pre-commit quality validation workflow
   - Line 819-821: Status field - determines routing

4. **qa_expert.md** (22,975 bytes)
   - Line 22-24: When QA is spawned
   - Line 107-147: Conditional Skill invocation
   - Line 127-146: When to invoke pattern-miner and quality-dashboard

5. **techlead.md** (18,724 bytes)
   - Line 128-145: Pre-review automated Skills
   - Line 146-156: Reading Skill results

**Testing Decision Flow:**
```
Developer Implementation
    ↓
Tests Created? (integration/contract/E2E)
    ├─ YES → Status: READY_FOR_QA → QA Expert
    │         ├─ Tests Pass → Tech Lead
    │         └─ Tests Fail → Developer (loop)
    │
    └─ NO → Status: READY_FOR_REVIEW → Tech Lead directly
         (only unit tests were run)
                ↓
            Tech Lead Reviews
                ↓
            APPROVED → PM (completion tracking)
            CHANGES_REQUESTED → Developer (loop)
```

---

### 6. Existing Configuration Patterns to Follow

**Pattern 1: Mandatory vs Disabled Skills**

Location: `/bazinga/skills_config.json`

Current pattern:
```json
{
  "developer": {
    "skill_name": "mandatory" | "disabled"
  }
}
```

**Where it's checked:**
- `agents/orchestrator.md:143-159` - Count active skills
- `agents/orchestrator.md:566` - IF check for each skill
- `agents/orchestrator.md:804` - qa_skills config check

**Pattern 2: Conditional Skill Invocation**

Location: `agents/orchestrator.md:625-680`

Example:
```bash
IF `codebase_analysis_mandatory`, add:
    2. **INVOKE Codebase Analysis Skill (MANDATORY):**
       Skill(command: "codebase-analysis")
ELSE: [skip section]
```

**Pattern 3: Routing Decision Logic**

Location: `agents/developer.md:831-860`

Example:
```markdown
**Status:** [READY_FOR_QA if tests exist] / [READY_FOR_REVIEW if no tests]
**Next Step:** Orchestrator, please forward to [QA Expert / Tech Lead]
```

**Pattern 4: Skills Results Storage**

All Skills write JSON to `bazinga/` with standardized format:
- `bazinga/<skill>_results.json` or `bazinga/<skill>_report.json`
- Includes timestamp, tool used, findings, suggestions
- Agents read and process results before continuing

---

### 7. Current Testing Integration Points Summary

| Component | Location | Line | Purpose |
|-----------|----------|------|---------|
| **Decision Logic** | `developer.md` | 831-860 | Route to QA or Tech Lead |
| **QA Spawning** | `orchestrator.md` | 800-850 | Check skills config for QA |
| **Skills Loading** | `orchestrator.md` | 140-159 | Load skills_config at init |
| **Test Coverage** | `tech_lead.md` | 128-145 | Run test-coverage skill |
| **Lint Check** | `developer.md` | 598-650 | Mandatory pre-commit |
| **Config Command** | `configure-skills.md` | 1-206 | Enable/disable skills |
| **Init Script** | `init-orchestration.sh` | 96-132 | Create skills_config.json |

---

### Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PM → Orchestrator → Developer                              │
│                         │                                    │
│                         ├─ Code Implementation              │
│                         ├─ Pre-Commit Validation:           │
│                         │   ✓ Lint Check (MANDATORY)        │
│                         │   ✓ Unit Tests                    │
│                         │   ✓ Build Check                   │
│                         │                                    │
│                         └─ Routing Decision:                │
│                             │                                │
│              ┌──────────────┴──────────────┐                │
│              ▼                              ▼                │
│     READY_FOR_QA                   READY_FOR_REVIEW         │
│   (integration/contract/E2E)         (unit tests only)      │
│              │                              │                │
│              ▼                              │                │
│         QA Expert ────────────────────────┐ │               │
│              │                             │ │               │
│              ├─ Run all test types        │ │               │
│              ├─ Pattern Mining (optional) │ │               │
│              └─ Quality Dashboard (opt)   │ │               │
│                                            │ │               │
│                                            ▼ ▼               │
│                                         Tech Lead            │
│                                            │                 │
│                              ┌─────────────┴─────────────┐   │
│                              ▼                           ▼   │
│                          APPROVED              CHANGES_REQ   │
│                              │                           │   │
│                              ▼                           │   │
│                             PM ←────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Current Testing Touchpoints

| Component | File | Lines | What Happens |
|-----------|------|-------|--------------|
| **Routing Logic** | `developer.md` | 831-860 | Decides QA vs direct Tech Lead |
| **Pre-Commit** | `developer.md` | 598-650 | Lint + unit tests + build |
| **QA Spawning** | `orchestrator.md` | 800-850 | Conditionally spawns QA Expert |
| **Skills Config** | `skills_config.json` | - | Enable/disable individual skills |
| **Test Coverage** | `tech_lead.md` | 128-145 | Runs test-coverage skill |

---

## Design Options Comparison

### **Option A: Granular Testing Control (RECOMMENDED)**

Add a structured testing configuration with multiple levels of control:

```json
{
  "_testing_framework": {
    "enabled": true,                    // Master toggle
    "mode": "full",                     // "full" | "minimal" | "disabled"

    "pre_commit_validation": {
      "lint_check": true,               // Should ALWAYS be true (critical)
      "unit_tests": true,               // Can disable for prototyping
      "build_check": true                // Can disable for rapid iteration
    },

    "test_requirements": {
      "require_integration_tests": true,
      "require_contract_tests": true,
      "require_e2e_tests": true,
      "coverage_threshold": 80
    },

    "qa_workflow": {
      "enable_qa_expert": true,          // Disable = skip QA entirely
      "auto_route_to_qa": true,          // If false, always go to Tech Lead
      "qa_skills_enabled": true          // Pattern mining, quality dashboard
    }
  },

  // Rest of existing config...
  "developer": { ... },
  "tech_lead": { ... },
  "qa_expert": { ... }
}
```

**Preset Modes:**
- **`full`**: All testing enabled (current behavior)
- **`minimal`**: Lint + unit tests only, skip QA Expert
- **`disabled`**: Only lint checks (fastest iteration)

**Advantages:**
- ✅ Maximum flexibility
- ✅ Progressive disabling (gradual trade-off)
- ✅ Preserves critical checks (lint always on)
- ✅ Clear semantics for each setting

**Disadvantages:**
- ❌ More complex configuration
- ❌ More code changes needed

---

### **Option B: Simple Master Toggle**

Minimal approach - single boolean flag:

```json
{
  "_testing_framework": {
    "enabled": true,                    // true = current behavior
                                         // false = skip QA, keep pre-commit
    "preserve_lint_checks": true        // Safety: always run lint
  }
}
```

**When `enabled: false`:**
- ✅ Skip QA Expert entirely
- ✅ Developer routes directly to READY_FOR_REVIEW
- ✅ Still run lint checks (safety)
- ✅ Still run unit tests + build (basic quality)
- ❌ No integration/contract/E2E tests
- ❌ No test-coverage skill

**Advantages:**
- ✅ Simple to understand
- ✅ Minimal code changes
- ✅ Clear binary choice

**Disadvantages:**
- ❌ Less granular control
- ❌ Can't fine-tune what to keep

---

### **Option C: Three-Tier System**

Balanced approach with three testing levels:

```json
{
  "_testing_framework": {
    "level": "standard",    // "strict" | "standard" | "none"

    "levels_definition": {
      "strict": {
        "description": "Full QA workflow with all test types",
        "qa_expert": true,
        "integration_tests": true,
        "coverage_threshold": 80,
        "lint": true,
        "unit_tests": true
      },
      "standard": {
        "description": "Basic testing without QA workflow",
        "qa_expert": false,
        "integration_tests": false,
        "coverage_threshold": 0,
        "lint": true,
        "unit_tests": true
      },
      "none": {
        "description": "Prototyping mode - lint only",
        "qa_expert": false,
        "integration_tests": false,
        "coverage_threshold": 0,
        "lint": true,
        "unit_tests": false
      }
    }
  }
}
```

**Advantages:**
- ✅ Balanced simplicity and flexibility
- ✅ Clear semantic levels
- ✅ Easy to switch between modes

**Disadvantages:**
- ❌ Limited to predefined combinations
- ❌ Can't customize individual settings

---

## Implementation Plan - Option A (Recommended)

### Phase 1: Configuration Layer (Foundation)

#### **File 1: `/scripts/init-orchestration.sh`**
**Location:** Lines 96-132 (after other config initialization)

**Add new testing framework config:**

```bash
# Create/update testing framework configuration
cat > bazinga/testing_config.json << 'EOF'
{
  "_testing_framework": {
    "enabled": true,
    "mode": "full",
    "_mode_options": ["full", "minimal", "disabled"],

    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": true,
      "build_check": true,
      "_note": "lint_check should always be true for code quality"
    },

    "test_requirements": {
      "require_integration_tests": true,
      "require_contract_tests": true,
      "require_e2e_tests": true,
      "coverage_threshold": 80,
      "_note": "These only apply when mode=full"
    },

    "qa_workflow": {
      "enable_qa_expert": true,
      "auto_route_to_qa": true,
      "qa_skills_enabled": true,
      "_note": "Disable enable_qa_expert to skip QA workflow entirely"
    }
  },

  "_metadata": {
    "description": "Testing framework configuration for BAZINGA",
    "created": "$(date -Iseconds)",
    "version": "1.0",
    "presets": {
      "full": "All testing enabled - complete QA workflow",
      "minimal": "Lint + unit tests only, skip QA Expert",
      "disabled": "Only lint checks - fastest iteration"
    }
  }
}
EOF

echo "✓ Testing framework configuration created"
```

**Impact:** Introduces new configuration file with granular controls

---

#### **File 2: `/.claude/commands/configure-testing.md`**
**New file** - Testing-specific configuration command

```markdown
You are configuring the BAZINGA testing framework. This controls how much testing and quality assurance is applied during development.

## Current Configuration

Read and display:
```bash
cat bazinga/testing_config.json | jq '._testing_framework'
```

## Testing Modes

1. **Full (Recommended for Production)**
   - All test types (unit, integration, contract, E2E)
   - QA Expert workflow
   - 80% coverage threshold
   - Full pre-commit validation

2. **Minimal (Fast Development)**
   - Lint checks + unit tests only
   - Skip QA Expert
   - Direct Developer → Tech Lead routing
   - Faster iteration

3. **Disabled (Rapid Prototyping)**
   - Lint checks only
   - No test requirements
   - Fastest possible iteration
   - ⚠️ NOT recommended for production code

## Quick Presets

Ask the user which preset they want:

**1. Full Testing (current default)**
```json
{
  "enabled": true,
  "mode": "full",
  "pre_commit_validation": {
    "lint_check": true,
    "unit_tests": true,
    "build_check": true
  },
  "qa_workflow": {
    "enable_qa_expert": true,
    "auto_route_to_qa": true
  }
}
```

**2. Minimal Testing**
```json
{
  "enabled": true,
  "mode": "minimal",
  "pre_commit_validation": {
    "lint_check": true,
    "unit_tests": true,
    "build_check": true
  },
  "qa_workflow": {
    "enable_qa_expert": false,
    "auto_route_to_qa": false
  }
}
```

**3. Disabled (Lint Only)**
```json
{
  "enabled": false,
  "mode": "disabled",
  "pre_commit_validation": {
    "lint_check": true,
    "unit_tests": false,
    "build_check": false
  },
  "qa_workflow": {
    "enable_qa_expert": false,
    "auto_route_to_qa": false
  }
}
```

**4. Custom Configuration**
- Allow user to set individual flags

## Update Configuration

Use Write tool to update `bazinga/testing_config.json` with the selected preset.

## ⚠️ Important Warnings

If user selects "Disabled" mode, warn:
```
⚠️  WARNING: Disabling testing framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This will disable most quality checks and is NOT recommended for:
- Production code
- Team projects
- Code that will be merged to main branch

Only use this for:
✓ Rapid prototyping
✓ Proof-of-concept development
✓ Personal experimental projects

Lint checks will still run to maintain minimum code quality.
```

## Verify Changes

After updating, display the new configuration and confirm with the user.
```

**Impact:** Provides user-friendly command to configure testing levels

---

### Phase 2: Orchestrator Integration (Coordination Layer)

#### **File 3: `/agents/orchestrator.md`**

**Change 1: Load Testing Config (Lines ~140-159)**

Add after loading `skills_config.json`:

```markdown
3. **Load Testing Framework Configuration:**

```bash
testing_config=$(cat bazinga/testing_config.json)
testing_enabled=$(echo "$testing_config" | jq -r '._testing_framework.enabled')
testing_mode=$(echo "$testing_config" | jq -r '._testing_framework.mode')
qa_enabled=$(echo "$testing_config" | jq -r '._testing_framework.qa_workflow.enable_qa_expert')
```

Store in orchestrator state:
- `testing_framework_mode`: Current testing level (full/minimal/disabled)
- `qa_expert_enabled`: Whether to spawn QA Expert
- `testing_validation_rules`: What pre-commit checks are required

**Critical:** Pass this configuration to all spawned agents so they know the testing expectations.
```

**Change 2: Developer Spawning (Lines ~563-614)**

Add testing context to Developer spawn prompt:

```markdown
## Testing Framework Configuration

**Testing Mode:** {testing_mode}
**QA Workflow Enabled:** {qa_enabled}

{IF testing_mode == "disabled"}
⚠️ **TESTING FRAMEWORK DISABLED**
- Only lint checks are required
- No test implementation needed
- Route directly to READY_FOR_REVIEW
- Skip all test-related workflow steps
{ENDIF}

{IF testing_mode == "minimal"}
📋 **MINIMAL TESTING MODE**
- Lint checks + unit tests required
- No integration/contract/E2E tests needed
- Skip QA Expert - route to READY_FOR_REVIEW
- Focus on fast iteration
{ENDIF}

{IF testing_mode == "full"}
✅ **FULL TESTING MODE**
- All test types may be required
- QA Expert workflow available
- Route to READY_FOR_QA if integration tests exist
- Standard workflow applies
{ENDIF}

**Pre-Commit Validation Required:**
- Lint Check: {lint_check_enabled}
- Unit Tests: {unit_tests_enabled}
- Build Check: {build_check_enabled}
```

**Change 3: QA Expert Spawning Logic (Lines ~800-850)**

Wrap QA spawning in conditional:

```markdown
## Step 4: Route Based on Testing Configuration

**Read developer status and testing config:**

```bash
dev_status=$(cat bazinga/messages/developer_to_orchestrator.json | jq -r '.status')
qa_enabled=$(cat bazinga/testing_config.json | jq -r '._testing_framework.qa_workflow.enable_qa_expert')
```

**Routing Decision:**

```python
IF dev_status == "READY_FOR_QA" AND qa_enabled == true:
    # Spawn QA Expert (existing logic)
    Task(
        subagent_type="general-purpose",
        prompt=f"""
        You are the QA Expert agent...
        {existing QA prompt}
        """
    )

ELIF dev_status == "READY_FOR_QA" AND qa_enabled == false:
    # Testing disabled - route directly to Tech Lead
    WRITE bazinga/messages/orchestrator_to_developer.json:
    {
        "message": "Testing framework disabled - routing directly to Tech Lead",
        "bypassed_qa": true,
        "reason": "qa_workflow.enable_qa_expert = false"
    }

    # Continue to Tech Lead workflow
    [route to Tech Lead spawn logic]

ELIF dev_status == "READY_FOR_REVIEW":
    # Standard path - route to Tech Lead
    [existing logic]
```

---

### Phase 3: Developer Workflow Changes

#### **File 4: `/agents/developer.md`**

**Change 1: Load Testing Config (Add at top of workflow, ~Lines 100-120)**

```markdown
## Initialize: Read Testing Configuration

**Before starting work, understand the testing requirements:**

```bash
testing_config=$(cat bazinga/testing_config.json | jq '._testing_framework')
testing_mode=$(echo "$testing_config" | jq -r '.mode')
qa_enabled=$(echo "$testing_config" | jq -r '.qa_workflow.enable_qa_expert')
unit_tests_required=$(echo "$testing_config" | jq -r '.pre_commit_validation.unit_tests')
lint_required=$(echo "$testing_config" | jq -r '.pre_commit_validation.lint_check')
build_check_required=$(echo "$testing_config" | jq -r '.pre_commit_validation.build_check')
```

**Store in memory - these affect your entire workflow.**
```

**Change 2: Pre-Commit Validation (Lines ~598-650)**

Make validation steps conditional:

```markdown
## Pre-Commit Quality Validation

**Before committing, validate based on testing configuration:**

**1. Lint Check (ALWAYS REQUIRED):**
```bash
# Lint is ALWAYS mandatory for code quality
Skill(command: "lint-check")
```

Fix ALL lint issues before proceeding. No exceptions.

{IF unit_tests_required == true}
**2. Run Unit Tests:**
```bash
# Run unit test suite
npm test  # or pytest, go test, etc.
```

All unit tests MUST pass before commit.
{ENDIF}

{IF build_check_required == true}
**3. Run Build Check:**
```bash
# Verify project builds successfully
npm run build  # or appropriate build command
```

Build MUST succeed before commit.
{ENDIF}

{IF testing_mode == "disabled"}
⚠️ **Testing framework disabled - minimal validation only**
- Only lint checks were required
- Skipping comprehensive testing
- Proceeding to commit
{ENDIF}
```

**Change 3: Routing Decision (Lines ~831-860)**

Update routing logic:

```markdown
## Determine Next Step - Routing Decision

**Read testing configuration:**
```bash
testing_mode=$(cat bazinga/testing_config.json | jq -r '._testing_framework.mode')
qa_enabled=$(cat bazinga/testing_config.json | jq -r '._testing_framework.qa_workflow.enable_qa_expert')
auto_route_to_qa=$(cat bazinga/testing_config.json | jq -r '._testing_framework.qa_workflow.auto_route_to_qa')
```

**Routing Logic:**

```python
# Case 1: Testing disabled or minimal
IF testing_mode in ["disabled", "minimal"] OR qa_enabled == false:
    status = "READY_FOR_REVIEW"
    next_agent = "Tech Lead"
    reason = "Testing framework disabled or QA workflow skipped"

    WRITE bazinga/messages/developer_to_orchestrator.json:
    {
        "status": "READY_FOR_REVIEW",
        "next_step": "Route to Tech Lead",
        "message": "Implementation complete. Testing framework in {testing_mode} mode.",
        "tests_created": false,
        "qa_skipped": true,
        "testing_mode": testing_mode
    }

# Case 2: Full testing mode WITH integration/contract/E2E tests
ELIF testing_mode == "full" AND created_integration_tests == true AND qa_enabled == true:
    status = "READY_FOR_QA"
    next_agent = "QA Expert"

    WRITE bazinga/messages/developer_to_orchestrator.json:
    {
        "status": "READY_FOR_QA",
        "next_step": "Route to QA Expert",
        "message": "Implementation complete with comprehensive tests",
        "tests_created": true,
        "test_types": ["integration", "contract", "e2e"]
    }

# Case 3: Full testing mode but only unit tests (no integration)
ELIF testing_mode == "full" AND created_integration_tests == false:
    status = "READY_FOR_REVIEW"
    next_agent = "Tech Lead"

    WRITE bazinga/messages/developer_to_orchestrator.json:
    {
        "status": "READY_FOR_REVIEW",
        "next_step": "Route to Tech Lead",
        "message": "Implementation complete with unit tests only",
        "tests_created": true,
        "test_types": ["unit"]
    }
```

**Format final message:**

```
✅ **Implementation Complete**

**Status:** {status}
**Testing Mode:** {testing_mode}
**Tests Created:** {yes/no}
**Next Step:** Orchestrator, please forward to {Tech Lead / QA Expert}

{IF qa_skipped}
ℹ️  QA workflow skipped due to testing configuration
{ENDIF}
```
```

---

### Phase 4: Tech Lead & QA Updates

#### **File 5: `/agents/techlead.md`**

**Change: Pre-Review Skills (Lines ~128-145)**

Make test-coverage skill conditional:

```markdown
## Pre-Review Automated Quality Checks

**Read testing configuration:**
```bash
testing_mode=$(cat bazinga/testing_config.json | jq -r '._testing_framework.mode')
test_coverage_skill=$(cat bazinga/skills_config.json | jq -r '.tech_lead."test-coverage"')
```

**Run applicable skills:**

1. **Security Scan (if enabled):**
   {existing security-scan logic}

2. **Lint Check (if enabled):**
   {existing lint-check logic}

{IF testing_mode == "full" AND test_coverage_skill == "mandatory"}
3. **Test Coverage (CONDITIONAL):**
   ```bash
   Skill(command: "test-coverage")
   ```

   Read and analyze `bazinga/coverage_report.json`
{ENDIF}

{IF testing_mode != "full"}
ℹ️  **Test coverage analysis skipped** - testing mode: {testing_mode}
{ENDIF}
```

---

#### **File 6: `/agents/qa_expert.md`**

**Change: Conditional Spawning Note (Lines ~22-24)**

Update documentation:

```markdown
## When QA Expert is Spawned

You are ONLY spawned when:
1. Developer has created integration/contract/E2E tests, AND
2. Testing framework is enabled (mode = "full"), AND
3. QA workflow is enabled (qa_workflow.enable_qa_expert = true)

**Testing Configuration Awareness:**

```bash
testing_config=$(cat bazinga/testing_config.json | jq '._testing_framework')
```

If testing framework is in "minimal" or "disabled" mode, you will NOT be spawned.
Developer routes directly to Tech Lead in those cases.

**Your role:**
- Run ALL test types (integration, contract, E2E)
- Analyze test results
- Optionally invoke pattern-miner and quality-dashboard skills
- Report to Tech Lead
```

---

### Phase 5: Configuration Command Updates

#### **File 7: `/.claude/commands/configure-skills.md`**

**Change: Add Testing Framework Section (Lines ~20-30)**

Add new section after introduction:

```markdown
## Configuration Options

You can configure:
1. **Individual Skills** - Enable/disable specific skills per role
2. **Testing Framework** - Control testing requirements (NEW!)

---

## Option A: Configure Testing Framework

If user wants to enable/disable testing, use:

```bash
SlashCommand(command: "/configure-testing")
```

This provides:
- Quick presets (full/minimal/disabled)
- Granular control over test types
- QA workflow enable/disable

---

## Option B: Configure Individual Skills

{existing skills configuration logic}
```

---

## Implementation Checklist

### Phase 1: Configuration Layer
- [ ] 1.1 Update init-orchestration.sh with testing_config.json
- [ ] 1.2 Create /configure-testing command
- [ ] 1.3 Add .gitignore entry for testing_config.json (optional)
- [ ] 1.4 Test config initialization

### Phase 2: Orchestrator Changes
- [ ] 2.1 Load testing config at initialization
- [ ] 2.2 Pass testing context to Developer spawn
- [ ] 2.3 Update QA Expert spawn conditional logic
- [ ] 2.4 Add routing bypass when QA disabled
- [ ] 2.5 Test orchestration with different modes

### Phase 3: Developer Changes
- [ ] 3.1 Load testing config at workflow start
- [ ] 3.2 Make pre-commit validation conditional
- [ ] 3.3 Update routing decision logic
- [ ] 3.4 Add testing mode to status messages
- [ ] 3.5 Test developer workflow in each mode

### Phase 4: Tech Lead & QA Updates
- [ ] 4.1 Make test-coverage skill conditional in Tech Lead
- [ ] 4.2 Update QA Expert spawning documentation
- [ ] 4.3 Test tech lead review in each mode

### Phase 5: Configuration UI
- [ ] 5.1 Update configure-skills command
- [ ] 5.2 Add testing framework help docs
- [ ] 5.3 Test configuration changes

### Phase 6: Documentation & Testing
- [ ] 6.1 Update README with testing configuration
- [ ] 6.2 Add migration guide for existing users
- [ ] 6.3 Test full workflow in each mode
- [ ] 6.4 Verify backward compatibility

---

## Usage Examples

### Example 1: Rapid Prototyping (Disabled Mode)

```bash
# User runs
/configure-testing

# Selects: "3. Disabled (Lint Only)"

# Result workflow:
PM → Orchestrator → Developer
                      ├─ Write code
                      ├─ Run lint check ✓
                      └─ Commit → READY_FOR_REVIEW
                                          ↓
                                    Tech Lead (direct)
                                          ↓
                                      APPROVED
                                          ↓
                                         PM
```

**Time savings:** ~40-60% faster (no test writing, no QA agent)

---

### Example 2: Fast Development (Minimal Mode)

```bash
# User runs
/configure-testing

# Selects: "2. Minimal Testing"

# Result workflow:
PM → Orchestrator → Developer
                      ├─ Write code
                      ├─ Write unit tests
                      ├─ Run lint check ✓
                      ├─ Run unit tests ✓
                      └─ Commit → READY_FOR_REVIEW
                                          ↓
                                    Tech Lead (direct)
                                          ↓
                                      APPROVED
                                          ↓
                                         PM
```

**Time savings:** ~30-40% faster (no integration tests, no QA agent)

---

### Example 3: Production Ready (Full Mode - Default)

```bash
# Default configuration (no changes needed)

# Result workflow:
PM → Orchestrator → Developer
                      ├─ Write code
                      ├─ Write all test types
                      ├─ Run lint check ✓
                      ├─ Run unit tests ✓
                      ├─ Run build check ✓
                      └─ Commit → READY_FOR_QA
                                          ↓
                                     QA Expert
                                      ├─ Integration tests ✓
                                      ├─ Contract tests ✓
                                      ├─ E2E tests ✓
                                      └─ Quality analysis
                                                ↓
                                          Tech Lead
                                                ↓
                                            APPROVED
                                                ↓
                                               PM
```

**Quality:** Maximum (all testing stages)

---

## Critical Considerations

### 1. Safety Guardrails

**Always Preserved (Even in Disabled Mode):**
- ✅ Lint checks (code quality minimum)
- ✅ Git commit process
- ✅ Tech Lead review
- ✅ PM tracking

**Never Disable:**
- Lint checks (too critical)
- Git safety (push branch validation)
- Role-based access control

### 2. Backward Compatibility

**Default Behavior:**
- testing_config.json defaults to "full" mode
- If file doesn't exist, assume full testing
- Existing workflows unchanged

**Migration:**
- No breaking changes
- Opt-in feature
- Explicit user action required to disable testing

### 3. Edge Cases

| Scenario | Handling |
|----------|----------|
| testing_config.json missing | Default to full mode, create file |
| Invalid mode value | Error + default to full mode |
| QA enabled but testing disabled | Validation error - QA requires testing |
| Mid-session config change | Warn that change takes effect next task |
| Test failures in disabled mode | N/A - tests not run |

---

## Expected Impact

| Metric | Disabled Mode | Minimal Mode | Full Mode (Current) |
|--------|---------------|--------------|---------------------|
| **Avg Time per Task** | 5-10 min | 10-15 min | 15-25 min |
| **Code Quality** | Low-Medium | Medium | High |
| **Bug Risk** | High | Medium | Low |
| **Best For** | Prototypes, POCs | Fast iteration | Production, Teams |
| **Agents Spawned** | 2 (Dev, Lead) | 2 (Dev, Lead) | 3 (Dev, QA, Lead) |
| **Test Coverage** | None | Unit only | All types |

---

## Recommendation

**Implement Option A (Granular Control)** with the following rationale:

1. **Maximum Flexibility:** Users can choose exactly what level of testing they need
2. **Progressive Degradation:** Can dial down testing incrementally rather than all-or-nothing
3. **Safety First:** Always preserves lint checks regardless of mode
4. **Clear Semantics:** Three preset modes are easy to understand
5. **Future-Proof:** Can add more granular controls later without breaking changes

**Implementation Effort:** Medium (6-8 hours)
**User Value:** High
**Risk:** Low (backward compatible, defaults to current behavior)

---

## Next Steps

1. Get user approval for Option A approach
2. Understand init-orchestration.sh role and calling context
3. Implement Phase 1 (Configuration Layer)
4. Test configuration creation and presets
5. Implement Phase 2-5 sequentially
6. End-to-end testing with all three modes
7. Documentation updates

---

**Status:** Ready for implementation pending clarification on init-orchestration.sh
