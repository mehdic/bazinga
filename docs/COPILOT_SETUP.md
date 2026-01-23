# GitHub Copilot Setup Guide

This guide explains how to install and use BAZINGA with GitHub Copilot.

## Prerequisites

- **GitHub Copilot** subscription (Individual, Business, or Enterprise)
- **VS Code** with GitHub Copilot extension installed
- **Python 3.9+** for the bazinga CLI
- **Git** for version control

## Installation

### Option 1: Using the Copilot Install Script (Recommended)

```bash
# Download and run the Copilot-specific installer
curl -sSL https://raw.githubusercontent.com/mehdic/bazinga/main/install-copilot.sh | bash
```

This script will:
1. Install the bazinga CLI via pip
2. Initialize BAZINGA in your project with `--platform copilot` flag
3. Copy templates to `.github/templates/` directory
4. Set up Skills in `.github/skills/`
5. Create Copilot-specific configuration

### Option 2: Manual Installation

```bash
# 1. Install the bazinga CLI
pip install bazinga-cli

# 2. Navigate to your project
cd /path/to/your/project

# 3. Initialize BAZINGA for Copilot
bazinga init --platform copilot

# 4. Verify installation
bazinga health-check
```

## Configuration

After installation, you'll find:

```
your-project/
├── .github/
│   ├── skills/           # Copilot Skills (loaded via SKILL.md)
│   └── templates/        # Agent workflows and specializations
├── bazinga/
│   ├── bazinga.db        # SQLite database (local dev mode)
│   ├── model_selection.json
│   ├── skills_config.json
│   ├── challenge_levels.json
│   └── testing_config.json
└── .gitignore            # Updated with bazinga exclusions
```

## Key Differences from Claude Code

| Feature | Claude Code | GitHub Copilot |
|---------|-------------|----------------|
| **Agent Spawning** | `Task()` tool | `#runSubagent` tool |
| **Parallel Execution** | Multiple `Task()` calls | Multiple `#runSubagent` calls (PR #2839+) |
| **Skill Loading** | Immediate | Progressive (3-level) |
| **File Structure** | `.claude/` directory | `.github/` directory |
| **Hooks System** | Supported | Not supported |
| **Model Selection** | Per-agent configuration | Not natively supported |
| **Database** | SQLite (default) | SQLite (local) or FileBackend (fallback) |

## Basic Usage

### Starting an Orchestration Session

In VS Code with Copilot Chat, invoke BAZINGA:

```
@workspace /bazinga Implement user authentication with JWT tokens
```

This will:
1. Create a new session in `bazinga/bazinga.db`
2. Spawn the Project Manager (PM) agent
3. PM analyzes requirements and creates task groups
4. PM orchestrates Developer, QA, and Tech Lead agents
5. All progress tracked in the dashboard

### Monitoring Progress

Start the mini-dashboard to monitor your orchestration session:

```bash
cd bazinga
python mini-dashboard/server.py
```

Open http://localhost:5050 to view:
- Active sessions
- Agent activity and reasoning
- Task group progress
- Token usage

## Limitations

### Not Supported in Copilot Mode

1. **Per-Agent Model Selection**
   - Copilot uses a single model for all agents
   - Cannot specify "use opus for PM, sonnet for Developer"
   - Workaround: Configure complexity routing in `bazinga/model_selection.json`

2. **Hooks System**
   - No equivalent to `.claude/hooks/` for lifecycle events
   - Cannot auto-run scripts on session start/end
   - Workaround: Manual workflow integration

3. **Slash Commands as First-Class Tools**
   - Copilot slash commands (like `/bazinga.orchestrate`) work differently
   - May need to convert to handoff patterns
   - Documented in `docs/PLATFORM_DIFFERENCES.md`

### Degraded Features in Copilot Cloud

When running Copilot in cloud mode (not local VS Code):

- **Database**: Switches to InMemoryBackend (no persistence across sessions)
- **Skills**: May timeout if execution exceeds cloud limits
- **File System**: Limited access for state management

**Solution**: Use Copilot in local mode (VS Code desktop) for full BAZINGA functionality.

## Troubleshooting

### "Session not found" after orchestration

**Cause**: Database file not created or in wrong location

**Fix**:
```bash
# Check database path
echo $BAZINGA_DB_PATH

# If empty, set to default
export BAZINGA_DB_PATH="$(pwd)/bazinga/bazinga.db"

# Verify database exists
ls -la bazinga/bazinga.db
```

### Skills not loading in Copilot

**Cause**: Progressive loading hasn't completed

**Fix**:
1. Wait 2-3 seconds after session start
2. Check `.github/skills/{skill-name}/SKILL.md` exists
3. Verify SKILL.md has proper frontmatter

### Parallel agent spawning not working

**Cause**: Running older Copilot version without PR #2839 support

**Fix**:
```bash
# Update VS Code and Copilot extension
code --update-extensions

# Verify Copilot version (must be ≥ Jan 15, 2026 release)
```

## Migration from Claude Code

If you have an existing BAZINGA project on Claude Code and want to use it with Copilot:

### Option 1: Dual-Platform Setup (Recommended)

Keep both `.claude/` and `.github/` directories:

```bash
# From existing Claude Code project
bazinga install --platform copilot --preserve-claude
```

This allows you to run the same project on both platforms.

### Option 2: Copilot-Only Setup

Migrate fully to Copilot:

```bash
# Backup Claude Code setup
mv .claude .claude.backup

# Install for Copilot
bazinga install --platform copilot

# Migrate sessions database (optional)
cp bazinga/bazinga.db bazinga/bazinga.db.claude_backup
```

## Next Steps

- Read **Platform Differences** guide: `docs/PLATFORM_DIFFERENCES.md`
- Explore **Skills Documentation**: `.github/skills/*/README.md`
- Run the **Integration Test**: See `tests/integration/README.md`
- Join the **Community**: https://github.com/mehdic/bazinga/discussions

## Support

- **Issues**: https://github.com/mehdic/bazinga/issues
- **Discussions**: https://github.com/mehdic/bazinga/discussions
- **Documentation**: https://github.com/mehdic/bazinga/tree/main/docs
