---
description: Configure which Skills are invoked during BAZINGA orchestration (lite/advanced/custom profiles)
---

# Bazinga Configure Skills

You are helping the user configure which Skills should be invoked during BAZINGA orchestration.

**Command:** /bazinga.configure-skills

**Note:** This command configures individual Skills. To configure the overall testing framework (enable/disable QA Expert, set testing rigor), use `/bazinga.configure-testing` instead.

## Step 1: Read Current Configuration

First, read the current configuration:

```bash
cat bazinga/skills_config.json 2>/dev/null
```

Parse the current status (mandatory/disabled) for each Skill.

## Step 2: Display Profile and Numbered Menu

First, show the current profile:

```
🎯 BAZINGA Skills Configuration

Current Profile: [PROFILE]
  • lite: Fast development (3 core skills)
  • advanced: Comprehensive analysis (10 skills)
  • custom: User-configured
```

Then present this numbered menu organized by profile:

```
📦 CORE SKILLS (Lite Profile - Always Active)

┌─────────────────────────────────────────────────────────────┐
│ 🔧 Developer                                                │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  1  │ lint-check                    │ 5-10s    │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Tech Lead                                                │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  6  │ security-scan                 │ 5-60s    │ [STATUS]   │
│  7  │ lint-check                    │ 5-10s    │ [STATUS]   │
│  8  │ test-coverage                 │ 10-20s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

⚡ ADVANCED SKILLS (Opt-in for Comprehensive Analysis)

┌─────────────────────────────────────────────────────────────┐
│ 🔧 Developer                                                │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  2  │ codebase-analysis             │ 15-30s   │ [STATUS]   │
│  3  │ test-pattern-analysis         │ 20-40s   │ [STATUS]   │
│  4  │ api-contract-validation       │ 10-20s   │ [STATUS]   │
│  5  │ db-migration-check            │ 10-15s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🧪 QA Expert                                                │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  9  │ pattern-miner                 │ 30-60s   │ [STATUS]   │
│ 10  │ quality-dashboard             │ 15-30s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📊 Project Manager                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│ 11  │ velocity-tracker              │ 5-10s    │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

[STATUS] = ✅ ON or ⚪ OFF
```

Replace [STATUS] with actual current state and [PROFILE] with the profile from _metadata.profile:
- ✅ ON = mandatory
- ⚪ OFF = disabled

## Step 3: Show Smart Input Options

After the menu, show these shortcuts:

```
💡 Smart Input Options:

Numbers:
  enable 2 3 9        → Turn on Skills #2, #3, #9
  disable 1 7         → Turn off Skills #1, #7
  2 3 9               → Same as "enable 2 3 9" (enable is default)

Presets:
  lite                → Lite profile: Core skills only (1,6,7,8 ON)
  advanced            → Advanced profile: All 10 skills enabled
  defaults            → Same as lite (recommended)
  none                → Disable all Skills

Examples:
  "2 3 9"                    → Enable codebase-analysis, test-pattern-analysis, pattern-miner
  "enable 2, disable 7"      → Enable #2, disable #7
  "lite"                     → Switch to lite profile (fast development)
  "advanced"                 → Switch to advanced profile (all skills)
  "defaults"                 → Reset to lite profile defaults

What would you like to change?
```

## Step 4: Parse User Input

Support these input patterns:

**Number-based:**
- `"2 3 9"` or `"2,3,9"` or `"2, 3, 9"` → enable Skills 2, 3, 9
- `"enable 2 3 9"` → enable Skills 2, 3, 9
- `"disable 1 7"` → disable Skills 1, 7
- `"enable 2, disable 7"` → mixed operations

**Presets:**
- `"lite"` or `"defaults"` or `"default"` or `"reset"` → Lite profile: Skills 1,6,7,8 ON, rest OFF (profile=lite)
- `"advanced"` → Advanced profile: all 10 Skills ON (profile=advanced)
- `"none"` or `"nothing"` → all Skills OFF (profile=custom)

**Skill number mappings:**
```
1  = developer.lint-check
2  = developer.codebase-analysis
3  = developer.test-pattern-analysis
4  = developer.api-contract-validation
5  = developer.db-migration-check
6  = tech_lead.security-scan
7  = tech_lead.lint-check
8  = tech_lead.test-coverage
9  = qa_expert.pattern-miner
10 = qa_expert.quality-dashboard
11 = pm.velocity-tracker
```

## Step 5: Apply Changes

After parsing user input, update the configuration:

```bash
cat > bazinga/skills_config.json << 'EOF'
{
  "_metadata": {
    "profile": "lite|advanced|custom",
    "version": "2.0",
    "description": "Description based on profile",
    "created": "existing_timestamp",
    "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent",
      "DISABLED: Skill will not be invoked",
      "Use /bazinga.configure-skills to modify this configuration interactively",
      "LITE PROFILE: 3 core skills (security-scan, lint-check, test-coverage)",
      "ADVANCED PROFILE: All 10 skills enabled"
    ]
  },
  "developer": {
    "lint-check": "mandatory|disabled",
    "codebase-analysis": "mandatory|disabled",
    "test-pattern-analysis": "mandatory|disabled",
    "api-contract-validation": "mandatory|disabled",
    "db-migration-check": "mandatory|disabled"
  },
  "tech_lead": {
    "security-scan": "mandatory|disabled",
    "lint-check": "mandatory|disabled",
    "test-coverage": "mandatory|disabled"
  },
  "qa_expert": {
    "pattern-miner": "mandatory|disabled",
    "quality-dashboard": "mandatory|disabled"
  },
  "pm": {
    "velocity-tracker": "mandatory|disabled"
  }
}
EOF
```

**Profile metadata rules:**
- If using "lite" preset: Set profile="lite", description="Lite profile - core skills only for fast development"
- If using "advanced" preset: Set profile="advanced", description="Advanced profile - all skills enabled for comprehensive analysis"
- If manual skill selection: Set profile="custom", description="Custom profile - user-configured skills"

## Step 6: Confirm Changes

Show a clear confirmation with before/after:

```
✅ Skills Configuration Updated

Changes Applied:
  #2 codebase-analysis: ⚪ OFF → ✅ ON
  #7 lint-check (tech_lead): ✅ ON → ⚪ OFF
  #9 pattern-miner: ⚪ OFF → ✅ ON

Current Active Skills (✅ ON):
  🔧 Developer:
     #1 lint-check
     #2 codebase-analysis

  🛡️ Tech Lead:
     #6 security-scan
     #8 test-coverage

  🧪 QA Expert:
     #9 pattern-miner

  📊 PM:
     #11 velocity-tracker

Total: 6 of 11 Skills active

Configuration saved to bazinga/skills_config.json
Run /configure-skills anytime to adjust.
```

## Important Notes

**Profiles:**
- **Lite** (default): Fast development with 3 core skills (1, 6, 7, 8)
  - Security scan, lint check, test coverage
  - Recommended for most projects
- **Advanced**: Comprehensive analysis with all 10 skills
  - Includes pattern mining, velocity tracking, API validation, etc.
  - Use for production-critical features or complex projects
- **Custom**: Individually selected skills

**Default Configuration (Lite Profile):**
- Skills 1, 6, 7, 8 are ON (core quality gates)
- Skills 2, 3, 4, 5, 9, 10, 11 are OFF (advanced analysis)

**Graceful Degradation:**
- Lite mode: Skills skip gracefully if tools missing (warns but continues)
- Advanced mode: Skills fail if required tools missing (user explicitly opted in)
- Tools not installed? You'll see warnings with installation instructions

**Persistence:**
- Configuration persists across all BAZINGA sessions
- Tracked in git (configuration file, not ephemeral state)

**Performance Guidance:**
- Core Skills (<20s): 1, 6, 7, 8
- Advanced Skills (15-60s): 2, 3, 4, 5, 9, 10, 11
- Consider your workflow: use lite for iteration, advanced for production
