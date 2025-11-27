---
description: Configure BAZINGA testing framework (full/minimal/skip modes, QA Expert settings)
---

# Bazinga Configure Testing

You are helping the user configure the BAZINGA testing framework. This controls how much testing and quality assurance is applied during development.

**Command:** /bazinga.configure-testing

## Step 1: Read Current Configuration

First, read the current configuration:

```bash
cat bazinga/testing_config.json 2>/dev/null
```

Parse the current testing mode and individual settings.

## Step 2: Display Current Configuration

Present the current state in a clear, visual format:

```
🧪 BAZINGA Testing Framework Configuration

Current Mode: [CURRENT_MODE]

┌─────────────────────────────────────────────────────────────┐
│ Testing Modes                                                │
├─────────────────────────────────────────────────────────────┤
│  1. FULL       ✅ Complete QA workflow (recommended)        │
│                • All test types (unit, integration, e2e)     │
│                • QA Expert agent reviews                     │
│                • 80% coverage threshold                      │
│                • Full pre-commit validation                  │
│                                                              │
│  2. MINIMAL    ⚡ Fast development                          │
│                • Lint + unit tests only                      │
│                • Skip QA Expert (faster)                     │
│                • Direct Developer → Tech Lead                │
│                                                              │
│  3. DISABLED   🚀 Rapid prototyping                         │
│                • Lint checks only                            │
│                • No test requirements                        │
│                • Fastest iteration                           │
│                • ⚠️  NOT for production                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Current Settings                                             │
├─────────────────────────────────────────────────────────────┤
│ Pre-Commit Validation:                                       │
│   • Lint Check:    [ON/OFF]                                 │
│   • Unit Tests:    [ON/OFF]                                 │
│   • Build Check:   [ON/OFF]                                 │
│                                                              │
│ QA Workflow:                                                 │
│   • QA Expert:     [ENABLED/DISABLED]                       │
│   • Auto-route:    [YES/NO]                                 │
│                                                              │
│ Test Requirements:                                           │
│   • Integration:   [REQUIRED/OPTIONAL]                      │
│   • Contract:      [REQUIRED/OPTIONAL]                      │
│   • E2E:           [REQUIRED/OPTIONAL]                      │
│   • Coverage:      [THRESHOLD]%                             │
└─────────────────────────────────────────────────────────────┘
```

Replace placeholders with actual values from the config.

## Step 3: Show Input Options

After displaying the current config, show these options:

```
💡 Configuration Options:

Quick Mode Selection:
  1 or full              → Switch to FULL mode (complete QA workflow)
  2 or minimal           → Switch to MINIMAL mode (fast development)
  3 or disabled          → Switch to DISABLED mode (rapid prototyping)

Granular Control:
  custom                 → Configure individual settings

Other:
  show                   → Display current config again
  reset                  → Reset to defaults (FULL mode)
  exit or done           → Save and exit

What would you like to change?
```

## Step 4: Parse User Input

Support these input patterns:

**Mode Selection:**
- `"1"` or `"full"` → Set mode to "full"
- `"2"` or `"minimal"` → Set mode to "minimal"
- `"3"` or `"disabled"` → Set mode to "disabled"
- `"reset"` or `"default"` or `"defaults"` → Set mode to "full"

**Custom Configuration:**
- `"custom"` → Enter interactive mode for granular settings

**When user selects "custom", ask them:**
```
🔧 Custom Configuration

You can enable/disable individual components:

Pre-Commit Validation:
  Type: lint on/off, unit on/off, build on/off

QA Workflow:
  Type: qa on/off, autoroute on/off

Test Requirements:
  Type: integration on/off, contract on/off, e2e on/off
  Type: coverage [0-100]

Type 'done' when finished, or 'cancel' to discard changes.
```

## Step 5: Apply Preset Configurations

When user selects a mode, apply the full preset:

**FULL Mode:**
```json
{
  "_testing_framework": {
    "enabled": true,
    "mode": "full",
    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": true,
      "build_check": true
    },
    "test_requirements": {
      "require_integration_tests": true,
      "require_contract_tests": true,
      "require_e2e_tests": true,
      "coverage_threshold": 80
    },
    "qa_workflow": {
      "enable_qa_expert": true,
      "auto_route_to_qa": true,
      "qa_skills_enabled": true
    }
  }
}
```

**MINIMAL Mode:**
```json
{
  "_testing_framework": {
    "enabled": true,
    "mode": "minimal",
    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": true,
      "build_check": true
    },
    "test_requirements": {
      "require_integration_tests": false,
      "require_contract_tests": false,
      "require_e2e_tests": false,
      "coverage_threshold": 0
    },
    "qa_workflow": {
      "enable_qa_expert": false,
      "auto_route_to_qa": false,
      "qa_skills_enabled": false
    }
  }
}
```

**DISABLED Mode:**
```json
{
  "_testing_framework": {
    "enabled": false,
    "mode": "disabled",
    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": false,
      "build_check": false
    },
    "test_requirements": {
      "require_integration_tests": false,
      "require_contract_tests": false,
      "require_e2e_tests": false,
      "coverage_threshold": 0
    },
    "qa_workflow": {
      "enable_qa_expert": false,
      "auto_route_to_qa": false,
      "qa_skills_enabled": false
    }
  }
}
```

## Step 6: Show Warning for DISABLED Mode

If user selects DISABLED mode, show this warning before applying:

```
⚠️  WARNING: Disabling Testing Framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This will disable most quality checks and is NOT recommended for:
  • Production code
  • Team projects
  • Code that will be merged to main branch

Only use DISABLED mode for:
  ✓ Rapid prototyping
  ✓ Proof-of-concept development
  ✓ Personal experimental projects

Lint checks will still run to maintain minimum code quality.

Are you sure you want to continue? (yes/no)
```

If user confirms with "yes" or "y", proceed. Otherwise, go back to menu.

## Step 7: Update Configuration File

Use the Write tool to update `bazinga/testing_config.json`:

```python
# Read current config
current_config = read_json("bazinga/testing_config.json")

# Update the _testing_framework section with new values
current_config["_testing_framework"]["mode"] = selected_mode
current_config["_testing_framework"]["enabled"] = (selected_mode != "disabled")
# ... update other fields based on mode ...

# Update metadata
current_config["_metadata"]["last_updated"] = current_timestamp()

# Write back to file
write_json("bazinga/testing_config.json", current_config)
```

**IMPORTANT:** Preserve the `_metadata.created` timestamp! Only update `last_updated`.

## Step 8: Display Confirmation

After updating, show confirmation with the new configuration:

```
✅ Testing Framework Configuration Updated

New Mode: [SELECTED_MODE]

Summary of Changes:
  • Testing Mode: [OLD_MODE] → [NEW_MODE]
  • QA Expert: [ENABLED/DISABLED]
  • Pre-commit validation: [SUMMARY]

The new configuration will take effect on the next BAZINGA orchestration.

Use /configure-testing anytime to change these settings.
```

## Step 9: Provide Context-Sensitive Recommendations

Based on the selected mode, provide recommendations:

**If FULL mode:**
```
💡 Recommended for:
  • Production code
  • Team collaboration
  • Critical features
  • Before merging to main branch

Estimated time per task: 15-25 minutes
Quality level: HIGH ✅
```

**If MINIMAL mode:**
```
💡 Recommended for:
  • Feature development
  • Quick iterations
  • Non-critical changes
  • Personal branches

Estimated time per task: 10-15 minutes
Quality level: MEDIUM ⚡
```

**If DISABLED mode:**
```
⚠️  Remember:
  • Lint checks still enforced
  • Tech Lead still reviews
  • NOT suitable for production
  • Use for prototyping only

Estimated time per task: 5-10 minutes
Quality level: LOW 🚀
```

## Error Handling

If `bazinga/testing_config.json` doesn't exist:
1. Show message: "Testing config not found. Running initialization..."
2. Run: `bash bazinga/scripts/init-orchestration.sh`
3. Confirm file created, then continue

If file is corrupted (invalid JSON):
1. Show error message
2. Offer to reset to defaults
3. If user confirms, recreate file with FULL mode preset

## Examples

**Example 1 - Quick mode switch:**
```
User: 2
Assistant: [Switches to MINIMAL mode, shows confirmation]
```

**Example 2 - Full to Disabled:**
```
User: disabled
Assistant: [Shows warning]
User: yes
Assistant: [Applies DISABLED mode, shows confirmation]
```

**Example 3 - Custom configuration:**
```
User: custom
Assistant: [Shows custom options]
User: qa off
Assistant: [Disables QA Expert]
User: coverage 60
Assistant: [Sets threshold to 60%]
User: done
Assistant: [Saves custom config, shows summary]
```

## Final Notes

- Always update `_metadata.last_updated` timestamp
- Never modify `_metadata.created` timestamp
- Validate all changes before writing
- Show clear before/after comparison
- Provide contextual recommendations
