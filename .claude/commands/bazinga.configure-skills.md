# Bazinga Configure Skills

You are helping the user configure which Skills should be invoked during BAZINGA orchestration.

**Command:** /bazinga.configure-skills

**Note:** This command configures individual Skills. To configure the overall testing framework (enable/disable QA Expert, set testing rigor), use `/bazinga.configure-testing` instead.

## Step 1: Read Current Configuration

First, read the current configuration:

```bash
cat coordination/skills_config.json 2>/dev/null
```

Parse the current status (mandatory/disabled) for each Skill.

## Step 2: Display Numbered Menu

Present this numbered menu to the user:

```
🎯 BAZINGA Skills Configuration

┌─────────────────────────────────────────────────────────────┐
│ 🔧 Developer Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  1  │ lint-check                    │ 5-10s    │ [STATUS]   │
│  2  │ codebase-analysis             │ 15-30s   │ [STATUS]   │
│  3  │ test-pattern-analysis         │ 20-40s   │ [STATUS]   │
│  4  │ api-contract-validation       │ 10-20s   │ [STATUS]   │
│  5  │ db-migration-check            │ 10-15s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Tech Lead Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  6  │ security-scan                 │ 5-60s    │ [STATUS]   │
│  7  │ lint-check                    │ 5-10s    │ [STATUS]   │
│  8  │ test-coverage                 │ 10-20s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🧪 QA Expert Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  9  │ pattern-miner                 │ 30-60s   │ [STATUS]   │
│ 10  │ quality-dashboard             │ 15-30s   │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📊 Project Manager Agent                                    │
├─────┬───────────────────────────────┬──────────┬────────────┤
│ 11  │ velocity-tracker              │ 5-10s    │ [STATUS]   │
└─────┴───────────────────────────────┴──────────┴────────────┘

[STATUS] = ✅ ON or ⚪ OFF
```

Replace [STATUS] with actual current state:
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
  defaults            → Reset to defaults (1,6,7,8,11 ON, rest OFF)
  all                 → Enable all Skills
  none                → Disable all Skills
  fast                → Only fast Skills <20s (1,6,7,8,11)
  advanced            → Only advanced Skills (2,3,4,5,9,10)

Examples:
  "2 3 9"                    → Enable codebase-analysis, test-pattern-analysis, pattern-miner
  "enable 2, disable 7"      → Enable #2, disable #7
  "advanced"                 → Enable all advanced Skills (2,3,4,5,9,10)
  "defaults"                 → Reset to recommended defaults

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
- `"defaults"` or `"default"` or `"reset"` → Skills 1,6,7,8,11 ON, rest OFF
- `"all"` or `"everything"` → all Skills ON
- `"none"` or `"nothing"` → all Skills OFF
- `"fast"` or `"fast-only"` → Skills 1,6,7,8,11 ON (execution time <20s)
- `"advanced"` → Skills 2,3,4,5,9,10 ON (advanced analysis)

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
cat > coordination/skills_config.json << 'EOF'
{
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
  },
  "_metadata": {
    "description": "Skills configuration for BAZINGA agents",
    "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent",
      "DISABLED: Skill will not be invoked",
      "Use /configure-skills to modify this configuration interactively"
    ]
  }
}
EOF
```

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

Configuration saved to coordination/skills_config.json
Run /configure-skills anytime to adjust.
```

## Important Notes

**Default Configuration:**
- Skills 1, 6, 7, 8, 11 are ON (fast, essential quality checks)
- Skills 2, 3, 4, 5, 9, 10 are OFF (advanced, slower analysis)

**Persistence:**
- Configuration persists across all BAZINGA sessions
- Tracked in git (unlike other coordination/*.json files)

**Performance Guidance:**
- Fast Skills (<20s): 1, 6, 7, 8, 11
- Advanced Skills (15-60s): 2, 3, 4, 5, 9, 10
- Consider your workflow: enable advanced Skills for critical work, disable for rapid iteration
