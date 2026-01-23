# M8: CLI/Installation System Migration Analysis

**Date:** 2026-01-23
**Context:** BAZINGA CLI migration from Claude Code to dual-platform (Claude Code + GitHub Copilot) support
**Status:** Draft
**Subject:** CLI Installation System Architecture and Migration Strategy

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State - Claude Code](#2-current-state---claude-code)
3. [Copilot Equivalent](#3-copilot-equivalent)
4. [Migration Strategy Options](#4-migration-strategy-options)
5. [Dual-Platform Support](#5-dual-platform-support)
6. [Implementation Plan](#6-implementation-plan)
7. [Open Questions](#7-open-questions)
8. [Critical Analysis](#8-critical-analysis)

---

## 1. Executive Summary

The BAZINGA CLI (`bazinga-cli` PyPI package) provides installation, initialization, and update commands for deploying the multi-agent orchestration system to client projects. This analysis examines how to extend the CLI to support dual-platform installation (Claude Code and GitHub Copilot) while maintaining backward compatibility.

**Key Findings:**
- Current CLI is Claude Code-specific in file placement (`.claude/` directories)
- Copilot uses different conventions (`.github/` directories)
- Both platforms support similar SKILL.md format with minor variations
- A platform flag (`--platform`) approach is recommended for dual-platform support
- VS Code extension installer could provide better UX for Copilot users

**Recommendation:** Implement Option A (Same CLI, Dual Destinations) with a `--platform` flag and automatic platform detection, while preserving existing behavior as default.

---

## 2. Current State - Claude Code

### 2.1 CLI Commands

The BAZINGA CLI (`src/bazinga_cli/__init__.py`) provides three main commands:

| Command | Purpose | Key Actions |
|---------|---------|-------------|
| `bazinga init` | Create new project | Create directory, copy all files, initialize git |
| `bazinga install` | Install into existing project | Copy files to existing directory |
| `bazinga update` | Update existing installation | Refresh files, preserve user configs |

### 2.2 File Distribution Matrix

The CLI distributes files from multiple sources to various destinations:

| Source Location | Destination | Copy Function | Mechanism |
|-----------------|-------------|---------------|-----------|
| `agents/*.md` | `.claude/agents/` | `copy_agents()` | Direct copy |
| `scripts/*.sh` | `bazinga/scripts/` | `copy_scripts()` | Copy + chmod |
| `bazinga/scripts/*.sh` | `bazinga/scripts/` | `copy_scripts()` | Copy + chmod |
| `.claude/commands/*.md` | `.claude/commands/` | `copy_commands()` | Direct copy |
| `.claude/skills/*/` | `.claude/skills/*/` | `copy_skills()` | Recursive copy |
| `.claude/templates/` | `.claude/templates/` | `copy_claude_templates()` | Direct copy |
| `templates/` | `bazinga/templates/` | `copy_templates()` | Recursive copy |
| `bazinga/*.json` | `bazinga/` | `copy_bazinga_configs()` | ALLOWED_CONFIG_FILES |
| `workflow/*.json` | `bazinga/config/` | `copy_bazinga_configs()` | Direct copy |
| `dashboard-v2/` | `bazinga/dashboard-v2/` | `download_prebuilt_dashboard()` | Tarball or copytree |
| `mini-dashboard/` | `bazinga/mini-dashboard/` | `copy_mini_dashboard()` | copytree |
| `hooks/*.sh` | `.claude/hooks/` | `install_compact_recovery_hook()` | Copy + settings.json |

### 2.3 BazingaSetup Class Architecture

```python
class BazingaSetup:
    """Handles BAZINGA installation and setup."""

    ALLOWED_CONFIG_FILES = [
        "model_selection.json",
        "challenge_levels.json",
        "skills_config.json",
    ]

    EXCLUDED_COMMAND_PREFIXES = {"speckit."}  # Dev-only commands
    EXCLUDED_SKILLS = {"skill-creator"}        # Dev-only skills

    def __init__(self, source_dir: Optional[Path] = None):
        # Priority order for source resolution:
        # 1. Development mode (git clone with agents/ dir)
        # 2. Installed mode (sys.prefix/share/bazinga_cli)
        # 3. Fallback to dev directory
```

### 2.4 Source Resolution Logic

The CLI uses a sophisticated source resolution system:

```python
def _get_config_source(self, relative_path: str) -> Optional[Path]:
    """
    Priority order:
    1. Package directory (bundled with code - version-matched)
    2. Shared data directory (legacy/system installs)
    3. Project root (editable/dev install)
    """
```

### 2.5 Dev vs Installed Mode Detection

```python
# Development mode check
dev_dir = Path(__file__).parent.parent.parent
if (dev_dir / "agents").exists():
    self.source_dir = dev_dir
else:
    # Installed mode - files in share/bazinga_cli
    installed_dir = Path(sys.prefix) / "share" / "bazinga_cli"
```

### 2.6 pyproject.toml Configuration

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/bazinga_cli"]
exclude = ["bazinga/templates", "bazinga/config"]

[tool.hatch.build.targets.wheel.force-include]
"bazinga/model_selection.json" = "bazinga_cli/bazinga/model_selection.json"
"bazinga/challenge_levels.json" = "bazinga_cli/bazinga/challenge_levels.json"
"bazinga/skills_config.json" = "bazinga_cli/bazinga/skills_config.json"
"templates" = "bazinga_cli/templates"
"workflow" = "bazinga_cli/bazinga/config"

[tool.hatch.build.targets.wheel.shared-data]
"agents" = "share/bazinga_cli/agents"
"scripts" = "share/bazinga_cli/scripts"
".claude/commands" = "share/bazinga_cli/.claude/commands"
".claude/skills" = "share/bazinga_cli/.claude/skills"
"dashboard-v2" = "share/bazinga_cli/dashboard-v2"
"mini-dashboard" = "share/bazinga_cli/mini-dashboard"
```

### 2.7 CLI Options and Profiles

```python
@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None),
    here: bool = typer.Option(False, "--here"),
    force: bool = typer.Option(False, "--force", "-f"),
    no_git: bool = typer.Option(False, "--no-git"),
    dashboard: bool = typer.Option(False, "--dashboard"),
    testing_mode: str = typer.Option("minimal", "--testing", "-t"),
    profile: str = typer.Option("lite", "--profile", "-p"),
):
```

| Profile | Description | Skills | Testing |
|---------|-------------|--------|---------|
| `lite` | Fast development | 3 core skills | Minimal |
| `advanced` | Comprehensive | 10 skills | Full |
| `custom` | User-configured | Per flags | Per flags |

---

## 3. Copilot Equivalent

### 3.1 Copilot Installation Methods

GitHub Copilot uses different installation approaches:

| Method | Mechanism | Use Case |
|--------|-----------|----------|
| **Manual** | User creates `.github/` directories manually | One-off setup |
| **VS Code Extension** | Extension installs files | Recommended for VS Code users |
| **CLI (gh)** | `gh copilot` commands | GitHub CLI integration |
| **Organization Settings** | GitHub repository settings | Enterprise/org-wide |

### 3.2 Copilot File Structure

```
.github/
├── agents/              # Custom agents (*.agent.md)
│   └── developer.agent.md
├── skills/              # Project skills
│   └── my-skill/
│       └── SKILL.md
├── copilot-instructions.md  # Global instructions (like CLAUDE.md)
└── workflows/           # GitHub Actions (not Copilot-specific)

~/.copilot/             # User-level (cross-project)
├── agents/             # Personal agents
└── skills/             # Personal skills
```

### 3.3 Copilot Settings Configuration

Unlike Claude Code's `settings.json` for hooks, Copilot uses:

| Setting | Location | Purpose |
|---------|----------|---------|
| Agent instructions | `.github/copilot-instructions.md` | Global context |
| Custom agents | `.github/agents/*.agent.md` | Project agents |
| Skills | `.github/skills/*/SKILL.md` | Project skills |
| User settings | VS Code `settings.json` | Tool permissions |

### 3.4 Key Differences from Claude Code

| Aspect | Claude Code | Copilot |
|--------|-------------|---------|
| Directory prefix | `.claude/` | `.github/` |
| Agent filename | `*.md` | `*.agent.md` |
| Global instructions | `.claude/CLAUDE.md` | `.github/copilot-instructions.md` |
| Hooks directory | `.claude/hooks/` | N/A (use VS Code commands) |
| Skills location | `.claude/skills/` | `.github/skills/` (or `.claude/skills/`) |
| Command files | `.claude/commands/*.md` | N/A (use agent handoffs) |
| Settings | `.claude/settings.json` | VS Code `settings.json` |

### 3.5 Copilot Backward Compatibility

Copilot provides backward compatibility with Claude Code locations:

```
# Copilot skill discovery priority:
1. .github/skills/
2. .claude/skills/     # Backward compatibility
3. ~/.copilot/skills/  # User-level
4. ~/.claude/skills/   # Backward compatibility
```

This means existing `.claude/skills/` installations work with Copilot without modification.

---

## 4. Migration Strategy Options

### Option A: Same CLI, Dual Destinations

**Description:** Extend existing CLI with `--platform` flag to install files to appropriate locations.

```bash
# Default (Claude Code)
bazinga install

# Copilot-specific
bazinga install --platform=copilot

# Both platforms
bazinga install --platform=both
```

**Implementation:**

```python
@app.command()
def install(
    platform: str = typer.Option(
        "claude",
        "--platform",
        "-P",
        help="Target platform: claude, copilot, or both"
    ),
):
    """Install BAZINGA to the specified platform(s)."""
    if platform in ("claude", "both"):
        install_for_claude(target_dir)
    if platform in ("copilot", "both"):
        install_for_copilot(target_dir)
```

**Pros:**
- Single CLI for all platforms
- Consistent user experience
- Reuses existing code
- Easy to add new platforms

**Cons:**
- More complex CLI logic
- Need to maintain parallel copy functions
- Platform detection adds complexity

**Effort:** Medium (2-3 days)

---

### Option B: Separate CLI Commands

**Description:** Add separate commands for each platform.

```bash
# Existing commands unchanged
bazinga install          # Claude Code (default)

# New platform-specific commands
bazinga install-copilot  # Copilot only
bazinga install-all      # Both platforms
```

**Implementation:**

```python
@app.command()
def install():
    """Install BAZINGA for Claude Code."""
    install_for_claude(target_dir)

@app.command("install-copilot")
def install_copilot():
    """Install BAZINGA for GitHub Copilot."""
    install_for_copilot(target_dir)

@app.command("install-all")
def install_all():
    """Install BAZINGA for all supported platforms."""
    install_for_claude(target_dir)
    install_for_copilot(target_dir)
```

**Pros:**
- Clear separation of concerns
- Backward compatible (existing commands unchanged)
- Easier to document

**Cons:**
- Code duplication between commands
- More commands to maintain
- Inconsistent with industry patterns (`--platform` is more common)

**Effort:** Medium (2-3 days)

---

### Option C: VS Code Extension Installer

**Description:** Create a VS Code extension that provides installation UI.

```
┌─────────────────────────────────────────────────┐
│  BAZINGA Installer                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  Select platform:                               │
│  [x] Claude Code                                │
│  [x] GitHub Copilot                            │
│                                                 │
│  Profile:                                       │
│  ( ) Lite    (x) Advanced    ( ) Custom        │
│                                                 │
│  [Install BAZINGA]                              │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Implementation:**
- Create VS Code extension (`bazinga-installer`)
- Use VS Code workspace APIs for file operations
- Integrate with both Claude Code and Copilot

**Pros:**
- Best UX for VS Code users (majority)
- Visual configuration
- No CLI required
- Platform auto-detection

**Cons:**
- New codebase to maintain (TypeScript)
- Doesn't help CLI users
- Additional distribution channel (VS Code Marketplace)
- Requires VS Code (not IDE-agnostic)

**Effort:** High (1-2 weeks)

---

### Recommended Approach: Option A + Automatic Detection

Implement Option A with automatic platform detection:

```python
def detect_platform(target_dir: Path) -> str:
    """Auto-detect which platform(s) to target."""
    has_claude = (target_dir / ".claude").exists()
    has_github = (target_dir / ".github").exists()
    has_copilot = (
        has_github and
        ((target_dir / ".github" / "agents").exists() or
         (target_dir / ".github" / "skills").exists())
    )

    if has_claude and has_copilot:
        return "both"
    elif has_copilot:
        return "copilot"
    elif has_claude:
        return "claude"
    else:
        # Default for new projects
        return "claude"
```

**Rationale:**
1. **Backward Compatible** - Existing behavior unchanged (default = claude)
2. **Future-Proof** - Easy to add more platforms
3. **User-Friendly** - Auto-detection reduces user decisions
4. **Single Codebase** - No duplication
5. **Industry Standard** - `--platform` flag is common pattern

---

## 5. Dual-Platform Support

### 5.1 Unified File Structure

For dual-platform installations, use this structure:

```
project/
├── .claude/                    # Claude Code specific
│   ├── agents/                 # Agent definitions
│   ├── commands/               # Slash commands
│   ├── skills/                 # Skills (also read by Copilot)
│   ├── hooks/                  # Hooks (Claude Code only)
│   ├── templates/              # Templates
│   ├── settings.json           # Claude Code settings
│   └── CLAUDE.md               # Claude Code instructions
│
├── .github/                    # Copilot specific
│   ├── agents/                 # Custom agents (*.agent.md)
│   ├── copilot-instructions.md # Copilot global instructions
│   └── skills -> ../.claude/skills  # Symlink (optional)
│
└── bazinga/                    # Shared runtime state
    ├── bazinga.db              # SQLite database
    ├── templates/              # Specialization templates
    ├── config/                 # Workflow configuration
    ├── dashboard-v2/           # Dashboard (platform-agnostic)
    ├── mini-dashboard/         # Mini dashboard
    ├── model_selection.json    # Model assignments
    ├── skills_config.json      # Skills configuration
    └── challenge_levels.json   # QA challenge levels
```

### 5.2 Platform-Specific File Mapping

| Source | Claude Code Destination | Copilot Destination |
|--------|-------------------------|---------------------|
| `agents/*.md` | `.claude/agents/` | `.github/agents/*.agent.md` |
| `.claude/commands/*.md` | `.claude/commands/` | N/A (use handoffs) |
| `.claude/skills/*/` | `.claude/skills/*/` | `.github/skills/*/` or symlink |
| `hooks/*.sh` | `.claude/hooks/` | N/A |
| Global config | `.claude/CLAUDE.md` | `.github/copilot-instructions.md` |
| Settings | `.claude/settings.json` | N/A |

### 5.3 Agent File Translation

Agent files need transformation for Copilot:

**Claude Code format (`developer.md`):**
```markdown
---
name: Developer
model: sonnet
description: Implements code changes
---

# Developer Agent

You are a Developer...
```

**Copilot format (`developer.agent.md`):**
```markdown
---
name: developer
description: Implements code changes
# Note: 'model' field not supported in Copilot
tools:
  - read
  - edit
  - execute
---

# Developer Agent

You are a Developer...
```

### 5.4 Skills Sharing Strategy

Skills are compatible between platforms with minor differences:

| Aspect | Claude Code | Copilot |
|--------|-------------|---------|
| Location | `.claude/skills/` | `.github/skills/` (or `.claude/skills/`) |
| Format | SKILL.md + YAML frontmatter | SKILL.md + YAML frontmatter |
| Discovery | Explicit invocation | Automatic by description |
| Loading | Full on invocation | Progressive (3-level) |

**Recommended approach:** Install skills to `.claude/skills/` (works on both platforms due to Copilot backward compatibility), but optionally symlink to `.github/skills/` for Copilot-first projects.

### 5.5 Implementation: Platform-Specific Copy Functions

```python
def copy_agents_for_claude(self, target_dir: Path) -> bool:
    """Copy agent files to .claude/agents/ directory."""
    agents_dir = target_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for agent_file in self.get_agent_files():
        shutil.copy2(agent_file, agents_dir / agent_file.name)
    return True

def copy_agents_for_copilot(self, target_dir: Path) -> bool:
    """Copy agent files to .github/agents/ with .agent.md extension."""
    agents_dir = target_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for agent_file in self.get_agent_files():
        # Transform filename: developer.md -> developer.agent.md
        copilot_name = agent_file.stem + ".agent.md"
        # Transform content if needed
        content = self.transform_agent_for_copilot(agent_file)
        (agents_dir / copilot_name).write_text(content)
    return True

def transform_agent_for_copilot(self, agent_file: Path) -> str:
    """Transform Claude Code agent to Copilot format."""
    content = agent_file.read_text()
    # Parse YAML frontmatter
    frontmatter, body = self.parse_frontmatter(content)

    # Remove unsupported fields
    frontmatter.pop('model', None)  # Copilot doesn't support model selection

    # Add Copilot-specific fields
    if 'tools' not in frontmatter:
        frontmatter['tools'] = ['read', 'edit', 'execute', 'search']

    # Reconstruct document
    return self.format_frontmatter(frontmatter) + body
```

### 5.6 CLI Flag Implementation

```python
from enum import Enum

class Platform(str, Enum):
    CLAUDE = "claude"
    COPILOT = "copilot"
    BOTH = "both"
    AUTO = "auto"

@app.command()
def install(
    target_dir: Path = typer.Argument(Path.cwd()),
    platform: Platform = typer.Option(
        Platform.AUTO,
        "--platform",
        "-P",
        help="Target platform: claude, copilot, both, or auto (default)"
    ),
    force: bool = typer.Option(False, "--force", "-f"),
):
    """Install BAZINGA to target directory."""
    setup = BazingaSetup()

    # Auto-detect platform if needed
    if platform == Platform.AUTO:
        platform = detect_platform(target_dir)
        console.print(f"[dim]Auto-detected platform: {platform}[/dim]")

    # Install for selected platform(s)
    platforms_to_install = {
        Platform.CLAUDE: [Platform.CLAUDE],
        Platform.COPILOT: [Platform.COPILOT],
        Platform.BOTH: [Platform.CLAUDE, Platform.COPILOT],
    }

    for plat in platforms_to_install[platform]:
        if plat == Platform.CLAUDE:
            console.print("\n[bold cyan]Installing for Claude Code...[/bold cyan]")
            setup.install_for_claude(target_dir)
        elif plat == Platform.COPILOT:
            console.print("\n[bold cyan]Installing for GitHub Copilot...[/bold cyan]")
            setup.install_for_copilot(target_dir)
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Days 1-2)

**Step 1.1: Add Platform Enum and Flag**
```python
# In src/bazinga_cli/__init__.py
from enum import Enum

class Platform(str, Enum):
    CLAUDE = "claude"
    COPILOT = "copilot"
    BOTH = "both"
    AUTO = "auto"
```

**Step 1.2: Implement Platform Detection**
```python
def detect_platform(target_dir: Path) -> Platform:
    """Detect installed platform(s) or recommend default."""
    # Check for existing installations
    has_claude = (target_dir / ".claude" / "agents").exists()
    has_copilot = (target_dir / ".github" / "agents").exists()

    if has_claude and has_copilot:
        return Platform.BOTH
    elif has_copilot:
        return Platform.COPILOT
    elif has_claude:
        return Platform.CLAUDE

    # New project - check for GitHub repo indicators
    if (target_dir / ".github").exists():
        return Platform.BOTH  # Likely GitHub project, install both
    return Platform.CLAUDE  # Default
```

**Step 1.3: Create Agent Transformer**
```python
def transform_agent_for_copilot(self, agent_file: Path) -> str:
    """Transform Claude agent to Copilot format."""
    import yaml
    content = agent_file.read_text()

    # Extract frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
    else:
        frontmatter = {}
        body = content

    # Transform frontmatter
    frontmatter.pop('model', None)  # Remove unsupported field
    if 'tools' not in frontmatter:
        frontmatter['tools'] = ['read', 'edit', 'execute', 'search']

    # Reconstruct
    yaml_str = yaml.dump(frontmatter, default_flow_style=False)
    return f"---\n{yaml_str}---\n\n{body}"
```

### Phase 2: Copy Functions (Days 3-4)

**Step 2.1: Refactor Existing Copy Functions**

Extract platform-agnostic logic into base functions:

```python
def _copy_agent_files(self, source_files: list[Path], dest_dir: Path,
                       transform_fn: Optional[Callable] = None) -> int:
    """Base agent copy with optional transformation."""
    copied = 0
    for src in source_files:
        try:
            safe_name = PathValidator.validate_filename(src.name)
            if transform_fn:
                content = transform_fn(src)
                dest = dest_dir / safe_name
                dest.write_text(content)
            else:
                shutil.copy2(src, dest_dir / safe_name)
            copied += 1
        except SecurityError as e:
            console.print(f"[red]Skipping {src.name}: {e}[/red]")
    return copied
```

**Step 2.2: Implement Copilot-Specific Functions**

```python
def copy_agents_for_copilot(self, target_dir: Path) -> bool:
    """Copy agents to .github/agents/ with Copilot format."""
    agents_dir = target_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    agent_files = self.get_agent_files()
    if not agent_files:
        return False

    for agent_file in agent_files:
        # Rename: developer.md -> developer.agent.md
        copilot_name = agent_file.stem + ".agent.md"
        content = self.transform_agent_for_copilot(agent_file)
        (agents_dir / copilot_name).write_text(content)
        console.print(f"  + Copied {copilot_name}")

    return True

def copy_skills_for_copilot(self, target_dir: Path) -> bool:
    """Copy skills to .github/skills/ for Copilot."""
    # Check if .claude/skills already exists (use symlink for efficiency)
    claude_skills = target_dir / ".claude" / "skills"
    github_skills = target_dir / ".github" / "skills"

    if claude_skills.exists() and not github_skills.exists():
        # Create symlink for efficiency
        github_dir = target_dir / ".github"
        github_dir.mkdir(parents=True, exist_ok=True)
        github_skills.symlink_to("../.claude/skills")
        console.print("  + Created symlink .github/skills -> .claude/skills")
        return True

    # Otherwise copy directly
    return self._copy_skills_to_dir(github_skills)

def create_copilot_instructions(self, target_dir: Path) -> bool:
    """Create .github/copilot-instructions.md from CLAUDE.md."""
    claude_md = target_dir / ".claude" / "CLAUDE.md"
    copilot_instructions = target_dir / ".github" / "copilot-instructions.md"

    if not claude_md.exists():
        return False

    # Transform Claude-specific references to Copilot equivalents
    content = claude_md.read_text()
    content = content.replace("Claude Code", "GitHub Copilot")
    content = content.replace(".claude/", ".github/")
    content = content.replace("Task()", "#runSubagent")

    copilot_instructions.parent.mkdir(parents=True, exist_ok=True)
    copilot_instructions.write_text(content)
    console.print("  + Created copilot-instructions.md")
    return True
```

### Phase 3: Command Integration (Days 5-6)

**Step 3.1: Update init Command**

```python
@app.command()
def init(
    project_name: Optional[str] = typer.Argument(None),
    platform: Platform = typer.Option(
        Platform.AUTO, "--platform", "-P",
        help="Target platform: claude, copilot, both, or auto"
    ),
    # ... existing options ...
):
    """Initialize a new BAZINGA project."""
    # ... existing code ...

    # Platform-specific installation
    if platform == Platform.AUTO:
        platform = detect_platform(target_dir)

    if platform in (Platform.CLAUDE, Platform.BOTH):
        console.print("\n[bold cyan]Installing for Claude Code...[/bold cyan]")
        setup.copy_agents(target_dir)
        setup.copy_commands(target_dir)
        setup.copy_skills(target_dir, script_type)
        # ... etc ...

    if platform in (Platform.COPILOT, Platform.BOTH):
        console.print("\n[bold cyan]Installing for GitHub Copilot...[/bold cyan]")
        setup.copy_agents_for_copilot(target_dir)
        setup.copy_skills_for_copilot(target_dir)
        setup.create_copilot_instructions(target_dir)
```

**Step 3.2: Update install Command**

```python
@app.command()
def install(
    path: Optional[str] = typer.Argument("."),
    platform: Platform = typer.Option(
        Platform.AUTO, "--platform", "-P",
        help="Target platform: claude, copilot, both, or auto"
    ),
    # ... existing options ...
):
    """Install BAZINGA to an existing project."""
    # Similar changes to init
```

**Step 3.3: Update update Command**

```python
@app.command()
def update(
    path: Optional[str] = typer.Argument("."),
    platform: Platform = typer.Option(
        Platform.AUTO, "--platform", "-P",
        help="Target platform to update"
    ),
    # ... existing options ...
):
    """Update an existing BAZINGA installation."""
    # Detect what's currently installed
    actual_platform = detect_installed_platform(target_dir)

    if platform == Platform.AUTO:
        platform = actual_platform

    # Update only installed platforms
    # ... implementation ...
```

### Phase 4: Testing (Days 7-8)

**Step 4.1: Unit Tests**

```python
# tests/test_cli_platform.py

def test_detect_platform_new_project(tmp_path):
    """New projects default to Claude."""
    assert detect_platform(tmp_path) == Platform.CLAUDE

def test_detect_platform_github_project(tmp_path):
    """GitHub projects default to both."""
    (tmp_path / ".github").mkdir()
    assert detect_platform(tmp_path) == Platform.BOTH

def test_detect_platform_claude_installed(tmp_path):
    """Detect existing Claude installation."""
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    assert detect_platform(tmp_path) == Platform.CLAUDE

def test_agent_transform_removes_model():
    """Agent transform removes unsupported 'model' field."""
    setup = BazingaSetup()
    result = setup.transform_agent_for_copilot(
        Path("tests/fixtures/developer.md")
    )
    assert "model:" not in result

def test_agent_transform_adds_tools():
    """Agent transform adds default tools."""
    setup = BazingaSetup()
    result = setup.transform_agent_for_copilot(
        Path("tests/fixtures/developer.md")
    )
    assert "tools:" in result
```

**Step 4.2: Integration Tests**

```python
def test_init_claude_only(tmp_path):
    """Test init for Claude Code only."""
    result = runner.invoke(app, ["init", "--here", "--platform=claude", "-f"],
                          obj={"cwd": tmp_path})
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "agents").exists()
    assert not (tmp_path / ".github" / "agents").exists()

def test_init_copilot_only(tmp_path):
    """Test init for Copilot only."""
    result = runner.invoke(app, ["init", "--here", "--platform=copilot", "-f"],
                          obj={"cwd": tmp_path})
    assert result.exit_code == 0
    assert (tmp_path / ".github" / "agents").exists()

def test_init_both_platforms(tmp_path):
    """Test init for both platforms."""
    result = runner.invoke(app, ["init", "--here", "--platform=both", "-f"],
                          obj={"cwd": tmp_path})
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "agents").exists()
    assert (tmp_path / ".github" / "agents").exists()
```

### Phase 5: Documentation (Day 9)

**Step 5.1: Update README.md**

```markdown
## Installation

### Quick Start

# Install for Claude Code (default)
bazinga init my-project

# Install for GitHub Copilot
bazinga init my-project --platform=copilot

# Install for both platforms
bazinga init my-project --platform=both

### Platform Detection

BAZINGA automatically detects the target platform based on existing
project structure:

- Existing `.claude/` directory → Claude Code
- Existing `.github/agents/` directory → GitHub Copilot
- Both directories → Both platforms
- Neither → Defaults to Claude Code

Override with `--platform` flag.
```

**Step 5.2: Update CLAUDE.md**

Add section on dual-platform support and file locations.

### Effort Estimate

| Phase | Task | Days |
|-------|------|------|
| 1 | Foundation (enum, detection) | 2 |
| 2 | Copy functions | 2 |
| 3 | Command integration | 2 |
| 4 | Testing | 2 |
| 5 | Documentation | 1 |
| **Total** | | **9 days** |

---

## 7. Open Questions

### 7.1 Agent Model Selection

**Question:** Copilot doesn't support per-agent model selection. How do we handle `model_selection.json`?

**Options:**
- A) Ignore model selection for Copilot (platform limitation)
- B) Map to Copilot model hints in instructions
- C) Keep model_selection.json as Claude-only feature

**Recommendation:** Option C - document as Claude-specific feature.

### 7.2 Slash Commands Migration

**Question:** Copilot doesn't have slash commands. What's the equivalent?

**Options:**
- A) Convert to agent handoffs
- B) Convert to skills
- C) Drop for Copilot (document limitation)

**Recommendation:** Option A - convert key commands to handoffs in agent definitions.

### 7.3 Hooks System

**Question:** Copilot doesn't have a hooks system like `.claude/settings.json`. How do we handle compaction recovery?

**Options:**
- A) Skip hooks for Copilot
- B) Use VS Code extension for hooks
- C) Convert to Copilot background agent pattern

**Recommendation:** Option A initially, evaluate Option B for future.

### 7.4 Skills Symlink vs Copy

**Question:** Should Copilot share skills via symlink to `.claude/skills/` or have its own copy?

**Options:**
- A) Symlink (saves space, single source of truth)
- B) Copy (no symlink issues on Windows)
- C) User choice via flag

**Recommendation:** Option A with Option B fallback for Windows.

### 7.5 VS Code Extension

**Question:** Should we build a VS Code extension for better UX?

**Analysis:**
- Pros: Better UX, auto-detection, visual config
- Cons: Separate codebase (TypeScript), maintenance burden

**Recommendation:** Phase 2 consideration - focus on CLI first.

---

## 8. Critical Analysis

### 8.1 Pros of Recommended Approach

1. **Single CLI** - One tool for all platforms
2. **Backward Compatible** - Existing behavior preserved
3. **Auto-Detection** - Reduces user decisions
4. **Shared State** - `bazinga/` directory works for both platforms
5. **Skill Reuse** - Skills work on both platforms via backward compat

### 8.2 Cons and Risks

1. **Agent Transformation** - May lose Claude-specific features
2. **Command Migration** - Slash commands don't map cleanly to Copilot
3. **Hooks Gap** - No equivalent in Copilot
4. **Model Selection** - Platform-specific limitation
5. **Testing Complexity** - Need to test both platforms

### 8.3 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent transformation loses features | Document platform-specific features clearly |
| Command migration incomplete | Convert critical commands to handoffs, document gaps |
| Hooks gap | Document as Claude-specific, evaluate VS Code extension |
| Model selection ignored | Document as Claude-specific feature |
| Testing complexity | Automated tests for both platforms, CI matrix |

### 8.4 Verdict

**The recommended Option A (Same CLI, Dual Destinations) approach provides the best balance of:**
- Minimal code duplication
- Maximum backward compatibility
- Clear path to add more platforms
- Reasonable implementation effort (9 days)

The main trade-off is increased CLI complexity, but this is manageable with good abstraction and testing.

---

## Appendix A: Full CLI Command Reference (Proposed)

```bash
# Initialize new project
bazinga init [PROJECT_NAME]
  --here                    # Initialize in current directory
  --platform={claude,copilot,both,auto}
  --profile={lite,advanced,custom}
  --testing={full,minimal,disabled}
  --dashboard               # Include dashboard
  --force                   # Skip confirmations
  --no-git                  # Skip git init

# Install to existing project
bazinga install [PATH]
  --platform={claude,copilot,both,auto}
  --profile={lite,advanced,custom}
  --force

# Update existing installation
bazinga update [PATH]
  --platform={claude,copilot,both,auto}
  --force

# Check installation
bazinga check [PATH]
  --platform={claude,copilot,both,auto}

# Version info
bazinga --version
bazinga version
```

---

## Appendix B: File Transformation Examples

### Agent File: developer.md → developer.agent.md

**Input (Claude Code):**
```markdown
---
name: Developer
model: sonnet
description: Implements code changes
---

# Developer Agent

You are a Developer agent in the BAZINGA multi-agent system.
```

**Output (Copilot):**
```markdown
---
name: developer
description: Implements code changes
tools:
  - read
  - edit
  - execute
  - search
---

# Developer Agent

You are a Developer agent in the BAZINGA multi-agent system.
```

### Global Instructions: CLAUDE.md → copilot-instructions.md

**Input (Claude Code):**
```markdown
# Project Context

This project uses BAZINGA orchestration with Claude Code.

Use Task() to spawn sub-agents.
Configuration is in .claude/settings.json.
```

**Output (Copilot):**
```markdown
# Project Context

This project uses BAZINGA orchestration with GitHub Copilot.

Use #runSubagent to spawn sub-agents.
Configuration is in VS Code settings.
```
