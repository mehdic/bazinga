# Configure Skills

You are helping the user configure which Skills should be invoked during BAZINGA orchestration.

## Current Configuration

First, check if a configuration already exists:

```bash
cat coordination/skills_config.json 2>/dev/null || echo "No configuration found - will use defaults"
```

## Skills Available by Agent

Present this menu to the user and ask them to configure each Skill:

### 🔧 Developer Agent Skills
- **lint-check** (5-10s) - Static code analysis, catches 80% of review issues
- **codebase-analysis** (15-30s) - Deep architectural pattern analysis [ADVANCED]
- **test-pattern-analysis** (20-40s) - Validates test coverage patterns [ADVANCED]
- **api-contract-validation** (10-20s) - API endpoint contract verification [ADVANCED]
- **db-migration-check** (10-15s) - Database schema migration safety [ADVANCED]

### 🛡️ Tech Lead Agent Skills
- **security-scan** (5-10s basic, 30-60s advanced) - Security vulnerability scanning
- **lint-check** (5-10s) - Code quality verification
- **test-coverage** (10-20s) - Test coverage analysis and reporting

### 🧪 QA Expert Agent Skills
- **pattern-miner** (30-60s) - Mines historical data for patterns [ADVANCED]
- **quality-dashboard** (15-30s) - Unified project health metrics [ADVANCED]

### 📊 Project Manager Agent Skills
- **velocity-tracker** (5-10s) - Team velocity and capacity tracking

## Configuration Options

For each Skill, the user can choose:
- **MANDATORY** - Skill will be automatically invoked by the agent
- **DISABLED** - Skill will not be invoked

## Interactive Configuration

Ask the user:

"I'll help you configure which Skills should run automatically. For each Skill below, tell me if you want it **MANDATORY** (auto-run) or **DISABLED** (never run).

**Developer Agent:**
- lint-check: [current: mandatory]
- codebase-analysis: [current: disabled]
- test-pattern-analysis: [current: disabled]
- api-contract-validation: [current: disabled]
- db-migration-check: [current: disabled]

**Tech Lead Agent:**
- security-scan: [current: mandatory]
- lint-check: [current: mandatory]
- test-coverage: [current: mandatory]

**QA Expert Agent:**
- pattern-miner: [current: disabled]
- quality-dashboard: [current: disabled]

**Project Manager Agent:**
- velocity-tracker: [current: mandatory]

You can respond with changes only (e.g., 'enable codebase-analysis and pattern-miner') or 'use defaults' to keep current settings."

## Saving Configuration

After user provides their choices, create/update the configuration file:

```bash
cat > coordination/skills_config.json << 'EOF'
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
EOF
```

Adjust the JSON based on user's selections.

## Confirmation

After saving, confirm:

"✅ Skills configuration saved to `coordination/skills_config.json`

**Active Skills:**
- Developer: [list mandatory Skills]
- Tech Lead: [list mandatory Skills]
- QA Expert: [list mandatory Skills]
- PM: [list mandatory Skills]

These Skills will be automatically invoked during orchestration. Run `/configure-skills` again anytime to change this configuration."

## Important Notes

- Default configuration (if no file exists): Fast Skills (lint-check, security-scan, test-coverage, velocity-tracker) are mandatory
- ADVANCED Skills are disabled by default due to longer execution time (15-60s)
- Configuration persists across all orchestration sessions
- Orchestrator and agents will automatically respect this configuration
