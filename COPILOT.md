# BAZINGA on GitHub Copilot

> Multi-Agent Dev Team orchestration system for GitHub Copilot

**Platform**: GitHub Copilot (VS Code)
**Repository**: https://github.com/mehdic/bazinga
**Documentation**: [docs/COPILOT_SETUP.md](docs/COPILOT_SETUP.md)

---

## Quick Start

### Installation

```bash
# Install BAZINGA CLI
pip install bazinga-cli

# Initialize in your project (Copilot mode)
cd /path/to/your/project
bazinga init --platform copilot

# Verify setup
bazinga health-check
```

### First Orchestration

In VS Code with Copilot Chat:

```
@workspace /bazinga Implement user authentication with JWT tokens
```

Watch as BAZINGA:
1. Spawns Project Manager to analyze requirements
2. Creates task groups and assigns complexity tiers
3. Spawns Developer agents (1-4 in parallel)
4. Routes to QA Expert for testing
5. Routes to Tech Lead for code review
6. PM validates completion and sends BAZINGA

Monitor progress at: http://localhost:5050 (mini-dashboard)

---

## Key Copilot-Specific Features

### Agent Spawning via #runSubagent

BAZINGA uses Copilot's `#runSubagent` tool for programmatic agent spawning:

```typescript
// Example: Spawn Developer for authentication task
#runSubagent({
  name: "developer",
  instructions: "Implement JWT authentication following best practices",
  context: {
    taskGroup: "AUTH",
    complexity: 4,
    specializations: ["python", "fastapi", "jwt"]
  }
});
```

### Parallel Execution Support

Since PR #2839 (merged Jan 15, 2026), Copilot supports parallel agent execution:

```typescript
// Spawn multiple developers concurrently
#runSubagent({ name: "developer-1", task: "Group A" });
#runSubagent({ name: "developer-2", task: "Group B" });
#runSubagent({ name: "developer-3", task: "Group C" });
// All execute simultaneously
```

### Progressive Skill Loading

Skills load in 3 stages for optimal performance:

1. **Frontmatter** (metadata) - ~50ms
2. **When to Invoke** (triggers) - ~100ms
3. **Full Content** (on demand) - ~200ms

**Example**: First invocation may take 350ms, subsequent calls are instant.

### File Structure

```
your-project/
├── .github/
│   ├── templates/              # Agent workflows
│   │   ├── pm_*.md            # Project Manager templates
│   │   ├── developer_*.md     # Developer workflow
│   │   ├── qa_*.md            # QA Expert workflow
│   │   ├── tech_lead_*.md     # Tech Lead workflow
│   │   └── specializations/   # Technology-specific guidance
│   │       ├── 01-languages/  # Python, TypeScript, Go, etc.
│   │       ├── 02-frameworks/ # React, FastAPI, Django, etc.
│   │       └── ...            # 13 categories, 72 templates
│   └── skills/                # Copilot Skills (SKILL.md format)
│       ├── lint-check/
│       ├── codebase-analysis/
│       ├── test-coverage/
│       └── ...                # 15+ skills
├── bazinga/
│   ├── bazinga.db             # SQLite database
│   ├── model_selection.json   # Agent model config
│   ├── skills_config.json     # Skill availability
│   ├── challenge_levels.json  # QA test progression
│   └── testing_config.json    # Test framework config
└── .gitignore                 # Updated with bazinga/* exclusions
```

---

## Workflow Integration

### Start Dashboard

```bash
# Terminal 1: Start mini-dashboard for monitoring
cd bazinga
python mini-dashboard/server.py
# Open http://localhost:5050
```

### Invoke Orchestration

```
# In VS Code Copilot Chat
@workspace /bazinga {your task description}
```

### Monitor Progress

The dashboard shows:
- **Sessions**: Active, completed, failed
- **Agents**: PM, Developer, QA, Tech Lead, SSE
- **Task Groups**: Status, complexity, assigned agents
- **Reasoning**: Agent decision-making process
- **Token Usage**: By agent and model

### Review Results

After BAZINGA completion:
1. Check `bazinga/artifacts/{session_id}/` for artifacts
2. Review reasoning in dashboard for decision trail
3. Validate test results and coverage reports
4. Merge approved branches

---

## Platform-Specific Considerations

### ✅ Supported Features

- Multi-agent orchestration (PM → Dev → QA → TL)
- Parallel task groups (1-4 developers simultaneously)
- 5-level QA challenge system
- Tech Lead code review with issue tracking
- Skills system (lint-check, codebase-analysis, etc.)
- Specialization system (72 templates, version guards)
- SQLite database (local mode)
- Dashboard monitoring (dashboard-v2 + mini-dashboard)

### ⚠️ Limitations

1. **No Per-Agent Model Selection**
   - All agents use the same model (set by Copilot platform)
   - Cannot configure "PM uses opus, Developer uses haiku"
   - Workaround: Use complexity routing in `model_selection.json`

2. **No Hooks System**
   - No equivalent to `.claude/hooks/` for lifecycle automation
   - SessionStart/SessionEnd hooks not available
   - Workaround: Manual setup/teardown via scripts

3. **Cloud Mode Degradation**
   - Copilot Cloud uses InMemoryBackend (no persistence)
   - Limited file system access
   - **Solution**: Use local VS Code for full functionality

### Copilot Cloud vs Local

| Feature | Copilot Local (VS Code) | Copilot Cloud (GitHub.com) |
|---------|-------------------------|----------------------------|
| Database | SQLite (persistent) | InMemory (session-only) |
| Skills | Full execution | Timeout risk |
| File Access | Unrestricted | Sandboxed |
| Recommendation | ✅ **Use for BAZINGA** | ⚠️ Limited functionality |

---

## Dual-Platform Setup

If your team uses both Claude Code and Copilot:

```bash
# Install for both platforms
bazinga install --platform copilot --preserve-claude
```

Result:
```
project/
├── .claude/      # For Claude Code users
├── .github/      # For Copilot users
└── bazinga/      # Shared database and config
```

**Benefits**:
- Same sessions visible to both platforms
- Team members use their preferred platform
- Database schema identical (fully compatible)
- Dashboard shows which platform created each session

**See**: `docs/PLATFORM_DIFFERENCES.md` for detailed comparison

---

## Configuration Files

### `bazinga/model_selection.json`

Controls which AI model each agent uses:

```json
{
  "agents": {
    "project_manager": {"model": "opus", "tier": "strategic"},
    "developer": {"model": "sonnet", "tier": "implementation"},
    "senior_software_engineer": {"model": "opus", "tier": "escalation"},
    "qa_expert": {"model": "sonnet", "tier": "quality"},
    "tech_lead": {"model": "opus", "tier": "architectural"}
  },
  "escalation_rules": {
    "developer": {
      "max_failures": 1,
      "escalate_to": "senior_software_engineer"
    }
  }
}
```

**Note**: On Copilot, the `model` field is informational only (platform controls actual model).

### `bazinga/skills_config.json`

Controls which skills are available to each agent:

```json
{
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "optional",
    "test-pattern-analysis": "optional"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "test-coverage": "mandatory",
    "api-contract-validation": "optional"
  }
}
```

### `bazinga/testing_config.json`

Controls testing requirements:

```json
{
  "mode": "full",
  "unit_tests_required": true,
  "integration_tests_required": true,
  "build_check_required": true,
  "lint_check_required": true
}
```

**Modes**:
- `full`: All quality checks enforced (production)
- `minimal`: Basic checks only (faster iteration)
- `disabled`: Prototyping mode (lint only)

---

## Troubleshooting

### "Session not found" Error

**Cause**: Database file missing or wrong path

**Fix**:
```bash
# Verify database exists
ls -la bazinga/bazinga.db

# If missing, reinitialize
bazinga init --platform copilot --force
```

### Skills Not Loading

**Cause**: Progressive loading hasn't completed

**Fix**:
1. Wait 2-3 seconds after session start
2. Check `.github/skills/{skill-name}/SKILL.md` exists
3. Verify frontmatter is correct

### Parallel Agents Not Working

**Cause**: Copilot version doesn't support PR #2839

**Fix**:
```bash
# Update VS Code and extensions
code --update-extensions

# Verify Copilot version (Settings → Extensions → GitHub Copilot)
# Must be ≥ Jan 15, 2026 release
```

### Database Locked Error

**Cause**: Multiple processes accessing database

**Fix**:
```bash
# Check for running processes
ps aux | grep bazinga

# Kill stale processes
pkill -f mini-dashboard

# Restart dashboard
cd bazinga && python mini-dashboard/server.py
```

---

## Resources

- **Setup Guide**: [docs/COPILOT_SETUP.md](docs/COPILOT_SETUP.md)
- **Platform Comparison**: [docs/PLATFORM_DIFFERENCES.md](docs/PLATFORM_DIFFERENCES.md)
- **Skills Documentation**: `.github/skills/*/README.md`
- **Integration Tests**: `tests/integration/README.md`
- **GitHub Issues**: https://github.com/mehdic/bazinga/issues
- **Discussions**: https://github.com/mehdic/bazinga/discussions

---

## Support

Need help? Check these resources:

1. **Documentation**: `docs/` directory
2. **GitHub Issues**: Report bugs or request features
3. **Discussions**: Ask questions, share tips
4. **Platform Differences**: Read `docs/PLATFORM_DIFFERENCES.md`

---

## What's Next?

1. Run the **Integration Test**: `tests/integration/simple-calculator-spec.md`
2. Explore **Skills**: `.github/skills/*/SKILL.md`
3. Customize **Specializations**: `.github/templates/specializations/`
4. Configure **Testing Mode**: `bazinga/testing_config.json`
5. Monitor **Sessions**: http://localhost:5050 (mini-dashboard)

Happy orchestrating! 🚀
