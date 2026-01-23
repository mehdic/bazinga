# Platform Differences: Claude Code vs GitHub Copilot

This document outlines the key differences between running BAZINGA on Claude Code versus GitHub Copilot.

## Quick Comparison Table

| Feature | Claude Code | GitHub Copilot | Notes |
|---------|-------------|----------------|-------|
| **Core Orchestration** | ✅ Full | ✅ Full | Same workflow on both |
| **Agent Spawning** | `Task()` tool | `#runSubagent` tool | Different APIs, same behavior |
| **Parallel Execution** | ✅ Yes | ✅ Yes (PR #2839+) | Multiple agents simultaneously |
| **Skill System** | ✅ Immediate load | ✅ Progressive load | 3-level loading on Copilot |
| **Database (Local)** | ✅ SQLite | ✅ SQLite | Same schema, compatible |
| **Database (Cloud)** | ✅ SQLite | ⚠️ InMemory | Cloud mode degraded |
| **File Structure** | `.claude/` | `.github/` | Parallel install supported |
| **Hooks System** | ✅ Supported | ❌ Not available | Pre/post session hooks |
| **Model Selection** | ✅ Per-agent | ❌ Global only | Can't set PM=opus, Dev=haiku |
| **Session Dashboard** | ✅ Same | ✅ Same | Shared dashboard-v2 |
| **Templates** | `bazinga/templates/` | `.github/templates/` | Same content, different paths |
| **Specializations** | ✅ Full | ✅ Full | Version guards work identically |

## Architecture Differences

### Agent Spawning

**Claude Code:**
```typescript
// Spawn Developer agent
Task({
  subagent_type: "developer",
  message: "Implement JWT authentication",
  run_in_background: false
});
```

**GitHub Copilot:**
```typescript
// Spawn Developer agent
#runSubagent({
  name: "developer",
  instructions: "Implement JWT authentication"
});
```

**Key Difference**: Different tool names, but functionally equivalent. BAZINGA abstracts this via `StateBackend`.

### Skill Loading

**Claude Code:**
- Skills loaded immediately when referenced
- `Skill(command: "lint-check")` → executes synchronously
- All skills available from session start

**GitHub Copilot:**
- Progressive 3-level loading:
  1. SKILL.md frontmatter (metadata)
  2. "When to Invoke" section (triggers)
  3. Full skill content (on demand)
- May have 1-2 second delay for first invocation
- Same `Skill(command: "lint-check")` syntax

**Impact**: Minimal. BAZINGA waits for skill loading to complete before proceeding.

### File Structure

**Claude Code Installation:**
```
project/
├── .claude/
│   ├── agents/          # Agent workflows
│   ├── commands/        # Slash commands
│   ├── hooks/           # Session lifecycle hooks
│   └── skills/          # Skills implementation
└── bazinga/
    ├── templates/       # Symlink to ../templates/ (dev mode)
    └── bazinga.db       # Session database
```

**Copilot Installation:**
```
project/
├── .github/
│   ├── templates/       # Agent workflows + specializations
│   └── skills/          # Skills (SKILL.md format)
└── bazinga/
    ├── templates/       # Physical copy of templates
    └── bazinga.db       # Session database (compatible with Claude)
```

**Dual-Platform Setup:**
Both directories can coexist:
```
project/
├── .claude/            # For Claude Code users
├── .github/            # For Copilot users
└── bazinga/            # Shared database and config
```

## Functional Parity

### ✅ Identical Features

These features work exactly the same on both platforms:

1. **Multi-Agent Orchestration**
   - PM → Developer → QA → Tech Lead workflow
   - Parallel task groups
   - Revision cycles

2. **Quality Gates**
   - 5-level QA challenge system
   - Tech Lead code review
   - BAZINGA validation

3. **Skills System**
   - lint-check, codebase-analysis, test-coverage
   - Same JSON output format
   - Identical invocation syntax

4. **Database Schema**
   - SQLite schema v19 (same on both)
   - Session data fully portable
   - Dashboard reads both platforms' sessions

5. **Specialization System**
   - 72 templates (languages, frameworks, tools)
   - Version guards (`#require python>=3.9`)
   - Token budgeting per model tier

### ⚠️ Platform-Specific Limitations

#### Claude Code Only

1. **Hooks System**
   - `.claude/hooks/SessionStart.sh` - pre-session setup
   - `.claude/hooks/SessionEnd.sh` - cleanup
   - **Copilot**: Must manually invoke setup/teardown

2. **Per-Agent Model Selection**
   - `model_selection.json`: `{"project_manager": "opus", "developer": "haiku"}`
   - **Copilot**: All agents use same model (set by platform)

#### Copilot Only

1. **Progressive Skill Loading**
   - Skills load in 3 stages for performance
   - **Claude Code**: Immediate full load

2. **Cloud Mode InMemory Database**
   - Copilot Cloud → no persistent database
   - **Claude Code**: Always persistent SQLite

## State Backend Abstraction

BAZINGA uses `StateBackend` factory to abstract platform differences:

```python
# Auto-detects platform and selects backend
backend = StateBackendFactory.create(
    platform="auto",  # Detects from environment
    mode="auto"       # Local vs Cloud detection
)

# Works identically on both platforms
backend.create_session(session_id, mode, requirements)
backend.spawn_agent("developer", task_data)
backend.get_session_status(session_id)
```

**Platform Detection:**
- Checks for `.claude/` directory → Claude Code
- Checks for `.github/skills/` → Copilot
- Checks environment variables (`COPILOT_CLOUD`, `CLAUDE_CODE_SESSION`)

**Backend Selection:**
- **Claude Code (Local)**: SQLiteBackend
- **Copilot (Local)**: SQLiteBackend (with FileBackend fallback)
- **Copilot (Cloud)**: InMemoryBackend (degraded mode)

## Template System

### Path Resolution

**Claude Code:**
```
Read: bazinga/templates/specializations/01-languages/python.md
```

**Copilot:**
```
Read: .github/templates/specializations/01-languages/python.md
```

**BAZINGA Abstraction:**
```python
# TemplateLoader resolves platform-specific paths
loader = TemplateLoader(platform="auto")
content = loader.load("specializations/01-languages/python.md")
# Returns same content regardless of platform
```

### Version Guards

Same syntax on both platforms:

```markdown
#require python>=3.9
#require django>=4.0,<5.0
#require pytest

Content here only included if requirements met...
```

**Implementation**: `prompt-builder` skill applies guards identically on both platforms.

## Migration Path

### Claude Code → Copilot

1. **Export Sessions** (optional):
   ```bash
   bazinga export-sessions --output sessions.json
   ```

2. **Install for Copilot**:
   ```bash
   bazinga install --platform copilot
   ```

3. **Import Sessions** (optional):
   ```bash
   bazinga import-sessions --input sessions.json
   ```

### Copilot → Claude Code

Same process, reverse direction:

```bash
bazinga export-sessions --output sessions.json
bazinga install --platform claude-code
bazinga import-sessions --input sessions.json
```

### Dual-Platform (Keep Both)

```bash
# Already have .claude/ from Claude Code usage
bazinga install --platform copilot --preserve-claude
```

Result:
- `.claude/` for Claude Code users
- `.github/` for Copilot users
- `bazinga/` shared by both
- Same database, same sessions

## Performance Comparison

| Metric | Claude Code | Copilot | Winner |
|--------|-------------|---------|--------|
| **Agent Spawn Time** | ~1.5s | ~1.8s | Claude (slight) |
| **Skill Invocation** | ~0.5s | ~0.7s | Claude (progressive load) |
| **Database Queries** | ~10ms | ~10ms | Tie (same SQLite) |
| **Parallel Agents** | 4 concurrent | 4 concurrent | Tie (same capacity) |
| **Session Init** | ~2s | ~3s | Claude (no progressive load) |

**Conclusion**: Claude Code is slightly faster due to immediate loading, but difference is negligible in practice (<1s).

## Choosing a Platform

### Use Claude Code If:

- ✅ You want **per-agent model selection** (PM=opus, Dev=haiku)
- ✅ You need **hooks** for session lifecycle automation
- ✅ You prefer **immediate skill loading** (no delay)
- ✅ You're already using Claude Code for development

### Use Copilot If:

- ✅ You have a **GitHub Copilot subscription**
- ✅ You prefer **VS Code integration**
- ✅ You want **GitHub ecosystem integration** (Actions, Codespaces)
- ✅ Your team already uses Copilot for coding

### Use Both If:

- ✅ You have **mixed team** (some use Claude, some Copilot)
- ✅ You want **maximum flexibility**
- ✅ You need **platform redundancy** (if one is down, use the other)

## FAQs

### Q: Can I move sessions between platforms?

**A:** Yes! The database schema is identical. Just copy `bazinga/bazinga.db` to the new platform.

### Q: Will my existing Claude Code sessions work on Copilot?

**A:** Yes. All sessions are platform-agnostic. The dashboard will show which platform created each session.

### Q: Can I use both platforms on the same project simultaneously?

**A:** Yes, with dual-platform setup. The database is shared, so both platforms see the same sessions.

### Q: Which platform is more stable?

**A:** Both are production-ready. Claude Code has been live longer (more mature). Copilot support is GA as of December 18, 2025.

### Q: Can I switch platforms mid-session?

**A:** No. A session is tied to the platform it was started on. Finish the session on the original platform, then start a new one on the other platform.

## Further Reading

- **Copilot Setup**: `docs/COPILOT_SETUP.md`
- **Claude Code Setup**: `CLAUDE.md`
- **PRD Section 6.1-6.8**: Detailed dual-platform architecture
- **Integration Tests**: `tests/integration/platform-compatibility.md`
