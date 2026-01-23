# BAZINGA Installation & Distribution Strategy Analysis

**Date:** 2026-01-23
**Context:** Multi-platform installation strategy for Claude Code + GitHub Copilot support
**Decision:** Hybrid distribution (pip + GitHub Releases + Docker)
**Status:** APPROVED WITH CHANGES
**Migration Subject:** M11 - Installation & Distribution (NEW)
**Debate Verdict:** APPROVE WITH CHANGES - Corporate security enhancements required

---

## Executive Summary

This document analyzes installation and distribution strategies for BAZINGA to support multiple AI coding platforms (Claude Code, GitHub Copilot, and potentially others) while addressing corporate/air-gapped environment requirements.

**Key Inspiration:** GitHub's [spec-kit](https://github.com/github/spec-kit) project demonstrates a successful multi-platform CLI approach with `--ai` flag targeting different AI agents.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Requirements](#2-target-requirements)
3. [Spec-Kit Analysis](#3-spec-kit-analysis)
4. [Proposed Distribution Strategy](#4-proposed-distribution-strategy)
5. [Implementation Options](#5-implementation-options)
6. [Corporate/Offline Distribution](#6-corporateoffline-distribution)
7. [Implementation Plan](#7-implementation-plan)
8. [Risk Assessment](#8-risk-assessment)

---

## 1. Current State Analysis

### 1.1 Current BAZINGA CLI

```bash
# Installation
pip install bazinga-cli
# or
uvx bazinga-cli

# Usage (Claude Code only)
bazinga install
bazinga update
bazinga init
```

**Current Limitations:**
- Single platform target (Claude Code only)
- Requires Python 3.11+ and pip
- No offline/corporate distribution option
- No pre-built binaries

### 1.2 Current File Structure

```
# What gets installed to client projects:
.claude/
├── agents/          # 10 agent definitions
├── commands/        # 14 slash commands
├── skills/          # 17 skills
├── templates/       # Message templates
└── hooks/           # Session hooks

bazinga/
├── templates/       # Specialization templates
├── config/          # Workflow configs
├── scripts/         # Dashboard scripts
├── model_selection.json
├── skills_config.json
└── challenge_levels.json
```

---

## 2. Target Requirements

### 2.1 Multi-Platform Support

| Platform | Directory Structure | Priority |
|----------|---------------------|----------|
| Claude Code | `.claude/agents/`, `.claude/skills/` | MVP |
| GitHub Copilot | `.github/agents/`, `.github/skills/` | MVP |
| Cursor | `.cursor/agents/` (TBD) | Post-MVP |
| Windsurf | `.windsurf/` (TBD) | Post-MVP |
| Others | Configurable | Future |

### 2.2 Installation Modes

| Mode | Use Case | Requirements |
|------|----------|--------------|
| **Interactive CLI** | Developer workstation | Python 3.11+, internet |
| **Offline Package** | Corporate/air-gapped | Pre-downloaded archive |
| **GitHub Release** | Direct download | None (self-contained) |
| **Docker** | CI/CD pipelines | Docker only |

### 2.3 Corporate Environment Needs

- Air-gapped networks (no internet)
- Restricted package managers (no pip/npm)
- Audit requirements (known artifact checksums)
- Manual approval workflows
- Windows-heavy environments

---

## 3. Spec-Kit Analysis

### 3.1 How Spec-Kit Does It

[GitHub Spec-Kit](https://github.com/github/spec-kit) uses:

```bash
# Platform selection via --ai flag
specify init my-project --ai claude
specify init my-project --ai copilot
specify init my-project --ai cursor-agent
specify init my-project --ai gemini

# Script type for Windows/Unix
specify init my-project --ai copilot --script ps   # PowerShell
specify init my-project --ai copilot --script sh   # Bash
```

**Supported Platforms:**
- claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, roo, codebuddy, amp, shai, q, bob, qoder

### 3.2 Spec-Kit Installation Structure

```
# Creates platform-specific directories:
.claude/commands/           # For Claude Code
.github/prompts/            # For Copilot
.cursor/                    # For Cursor
```

### 3.3 What We Can Learn

| Spec-Kit Feature | BAZINGA Adoption |
|------------------|------------------|
| `--ai` flag for platform selection | `--platform` flag |
| `--script sh/ps` for shell type | Same approach |
| `uvx` one-time execution | Support both pip and uvx |
| Git-based distribution | Add GitHub Releases |

---

## 4. Proposed Distribution Strategy

### 4.1 CLI with Platform Flag

```bash
# New CLI interface
bazinga install --platform claude          # Claude Code only (current behavior)
bazinga install --platform copilot         # GitHub Copilot only
bazinga install --platform both            # Both platforms
bazinga install --platform auto            # Auto-detect (default)

# Additional flags
bazinga install --script ps                # PowerShell scripts (Windows)
bazinga install --script sh                # Bash scripts (default)
bazinga install --offline /path/to/archive # Install from offline package
```

### 4.2 Auto-Detection Logic

```python
def detect_platform() -> list[Platform]:
    """Auto-detect which platforms are available."""
    platforms = []

    # Check for Claude Code
    if shutil.which("claude") or Path(".claude").exists():
        platforms.append(Platform.CLAUDE)

    # Check for GitHub Copilot
    if os.environ.get("GITHUB_COPILOT_VERSION") or Path(".github/copilot").exists():
        platforms.append(Platform.COPILOT)

    # Check VS Code with Copilot extension
    if Path.home().joinpath(".vscode/extensions").glob("github.copilot-*"):
        platforms.append(Platform.COPILOT)

    return platforms or [Platform.CLAUDE]  # Default to Claude
```

### 4.3 Platform-Specific Installation

```
bazinga install --platform both
│
├── .claude/                    # Claude Code
│   ├── agents/                 # Agent .md files
│   ├── commands/               # Slash commands
│   ├── skills/                 # Skills (shared)
│   └── CLAUDE.md               # Instructions
│
├── .github/                    # GitHub Copilot
│   ├── agents/                 # Agent .agent.md files
│   ├── skills -> ../.claude/skills  # Symlink to shared
│   └── copilot-instructions.md # Copilot instructions
│
└── bazinga/                    # Shared runtime
    ├── templates/
    ├── config/
    ├── scripts/
    └── *.json configs
```

---

## 5. Implementation Options

### 5.1 Option A: Enhanced pip Package (Recommended)

**Approach:** Extend current pip package with platform flags.

```bash
pip install bazinga-cli
bazinga install --platform both
```

**Pros:**
- Minimal changes to existing infrastructure
- Works with existing Python ecosystem
- Easy to maintain single codebase

**Cons:**
- Requires Python 3.11+
- Not truly offline without extra steps

**Implementation:**
1. Add `--platform` flag to CLI
2. Add agent transformation logic (`.md` → `.agent.md`)
3. Add copilot-instructions.md generator
4. Update `copy_*` functions for dual-platform

### 5.2 Option B: GitHub Releases with Pre-built Archives

**Approach:** Publish platform-specific archives to GitHub Releases.

```
Releases:
├── bazinga-v1.3.0-claude-linux.tar.gz
├── bazinga-v1.3.0-claude-macos.tar.gz
├── bazinga-v1.3.0-claude-windows.zip
├── bazinga-v1.3.0-copilot-linux.tar.gz
├── bazinga-v1.3.0-copilot-macos.tar.gz
├── bazinga-v1.3.0-copilot-windows.zip
├── bazinga-v1.3.0-both-linux.tar.gz
├── bazinga-v1.3.0-both-macos.tar.gz
└── bazinga-v1.3.0-both-windows.zip
```

**Pros:**
- No Python required for end users
- Works in air-gapped environments
- Simple: download, extract, done

**Cons:**
- More releases to maintain (3 platforms × 3 OS = 9 archives)
- No automatic updates
- Larger download size

**Implementation:**
1. GitHub Actions workflow to build archives
2. Platform-specific install scripts included
3. Checksum files for verification

### 5.3 Option C: Shiv/PEX Self-Contained Executables

**Approach:** Build single-file Python executables.

```bash
# Download and run directly
./bazinga-linux install --platform both
bazinga-windows.exe install --platform copilot
```

**Pros:**
- Single file, no installation
- Python bundled inside
- Cross-platform from single build

**Cons:**
- Larger file size (~50MB with Python)
- Build complexity
- May have OS compatibility issues

### 5.4 Option D: Hybrid (Recommended)

**Approach:** Combine Options A + B.

| Channel | Target Audience | Method |
|---------|-----------------|--------|
| **pip/uvx** | Developers | `pip install bazinga-cli` |
| **GitHub Releases** | Corporate/offline | Download archives |
| **Docker** | CI/CD | `docker run bazinga` |

---

## 6. Corporate/Offline Distribution

### 6.1 Offline Package Structure

```
bazinga-v1.3.0-offline-both.zip
├── INSTALL.md                  # Instructions
├── checksums.sha256            # Verification
├── install.sh                  # Unix installer
├── install.ps1                 # Windows installer
│
├── claude/                     # Claude Code files
│   ├── agents/
│   ├── commands/
│   ├── skills/
│   └── CLAUDE.md
│
├── copilot/                    # GitHub Copilot files
│   ├── agents/
│   ├── skills/
│   └── copilot-instructions.md
│
└── shared/                     # Shared files
    ├── bazinga/
    │   ├── templates/
    │   ├── config/
    │   └── *.json
    └── scripts/
```

### 6.2 Offline Install Script (Unix)

```bash
#!/bin/bash
# install.sh - Offline BAZINGA installer

set -e

PLATFORM="${1:-both}"  # claude, copilot, both
TARGET="${2:-.}"       # Installation directory

echo "Installing BAZINGA for platform: $PLATFORM"

# Verify checksums
sha256sum -c checksums.sha256

# Install based on platform
case "$PLATFORM" in
    claude)
        cp -r claude/.claude "$TARGET/"
        ;;
    copilot)
        mkdir -p "$TARGET/.github"
        cp -r copilot/agents "$TARGET/.github/"
        cp -r copilot/skills "$TARGET/.github/"
        cp copilot/copilot-instructions.md "$TARGET/.github/"
        ;;
    both)
        cp -r claude/.claude "$TARGET/"
        mkdir -p "$TARGET/.github"
        cp -r copilot/agents "$TARGET/.github/"
        ln -sf "../.claude/skills" "$TARGET/.github/skills"
        cp copilot/copilot-instructions.md "$TARGET/.github/"
        ;;
esac

# Install shared files
cp -r shared/bazinga "$TARGET/"
cp -r shared/scripts "$TARGET/bazinga/"

echo "BAZINGA installed successfully!"
```

### 6.3 Offline Install Script (Windows PowerShell)

```powershell
# install.ps1 - Offline BAZINGA installer for Windows

param(
    [string]$Platform = "both",
    [string]$Target = "."
)

Write-Host "Installing BAZINGA for platform: $Platform"

# Verify checksums
Get-Content checksums.sha256 | ForEach-Object {
    $parts = $_ -split "  "
    $hash = (Get-FileHash $parts[1] -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $parts[0]) {
        throw "Checksum mismatch for $($parts[1])"
    }
}

# Install based on platform
switch ($Platform) {
    "claude" {
        Copy-Item -Recurse "claude\.claude" "$Target\"
    }
    "copilot" {
        New-Item -ItemType Directory -Force "$Target\.github" | Out-Null
        Copy-Item -Recurse "copilot\agents" "$Target\.github\"
        Copy-Item -Recurse "copilot\skills" "$Target\.github\"
        Copy-Item "copilot\copilot-instructions.md" "$Target\.github\"
    }
    "both" {
        Copy-Item -Recurse "claude\.claude" "$Target\"
        New-Item -ItemType Directory -Force "$Target\.github" | Out-Null
        Copy-Item -Recurse "copilot\agents" "$Target\.github\"
        # Windows: Copy instead of symlink (symlinks require admin)
        Copy-Item -Recurse "copilot\skills" "$Target\.github\"
        Copy-Item "copilot\copilot-instructions.md" "$Target\.github\"
    }
}

# Install shared files
Copy-Item -Recurse "shared\bazinga" "$Target\"

Write-Host "BAZINGA installed successfully!"
```

### 6.4 GitHub Actions Release Workflow

```yaml
# .github/workflows/release.yml
name: Build Release Packages

on:
  push:
    tags:
      - 'v*'

jobs:
  build-archives:
    strategy:
      matrix:
        platform: [claude, copilot, both]
        os: [ubuntu-latest, macos-latest, windows-latest]
        include:
          - os: ubuntu-latest
            archive_ext: tar.gz
            os_name: linux
          - os: macos-latest
            archive_ext: tar.gz
            os_name: macos
          - os: windows-latest
            archive_ext: zip
            os_name: windows

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Build archive
        run: |
          python scripts/build_release.py \
            --platform ${{ matrix.platform }} \
            --os ${{ matrix.os_name }} \
            --output bazinga-${{ github.ref_name }}-${{ matrix.platform }}-${{ matrix.os_name }}.${{ matrix.archive_ext }}

      - name: Generate checksums
        run: |
          sha256sum bazinga-*.* > checksums.sha256

      - name: Upload to release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            bazinga-*.*
            checksums.sha256
```

---

## 7. Implementation Plan

### Phase 1: CLI Enhancement (Week 1-2)

| Task | Effort | Deliverable |
|------|--------|-------------|
| Add `--platform` flag | 2 days | CLI accepts claude/copilot/both/auto |
| Add `--script` flag | 1 day | sh/ps script generation |
| Agent transformation | 2 days | `.md` → `.agent.md` converter |
| Copilot instructions generator | 1 day | Generate from CLAUDE.md |
| Update `copy_*` functions | 2 days | Dual-platform file copying |

### Phase 2: Offline Distribution (Week 3-4)

| Task | Effort | Deliverable |
|------|--------|-------------|
| Build script for archives | 2 days | `scripts/build_release.py` |
| Install scripts (sh + ps1) | 2 days | Platform-specific installers |
| GitHub Actions workflow | 2 days | Automated release builds |
| Checksum generation | 1 day | SHA256 verification |
| Documentation | 1 day | Corporate installation guide |

### Phase 3: Testing & Documentation (Week 5)

| Task | Effort | Deliverable |
|------|--------|-------------|
| Test all platform combinations | 2 days | 3 platforms × 3 OS matrix |
| Test offline installation | 1 day | Air-gapped environment sim |
| Update README | 1 day | Multi-platform quick start |
| Corporate deployment guide | 1 day | Enterprise installation docs |

---

## 8. Risk Assessment

### 8.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Windows symlink issues | High | Medium | Copy fallback (already planned) |
| Large archive sizes | Medium | Low | Separate platform archives |
| Agent transformation bugs | Medium | High | Comprehensive test suite |
| Copilot API changes | Medium | High | Version detection + graceful degradation |
| Corporate firewall blocks GitHub | Low | High | Document alternative hosting |

### 8.2 Open Questions

1. Should we support more platforms beyond Claude/Copilot in MVP?
2. Should offline archives include Python runtime (larger but self-contained)?
3. Should we provide Docker images for CI/CD pipelines?
4. Should we support partial updates (agents only, skills only)?

---

## 9. Recommendation

**Recommended Approach: Hybrid (Option D)**

1. **Primary:** Enhanced pip package with `--platform` flag
2. **Secondary:** GitHub Releases with pre-built archives for corporate/offline
3. **Future:** Consider Shiv/PEX for truly self-contained distribution

**CLI Interface:**
```bash
# Standard installation
pip install bazinga-cli
bazinga install --platform both

# Offline installation
# Download: bazinga-v1.3.0-both-linux.tar.gz
tar -xzf bazinga-v1.3.0-both-linux.tar.gz
cd bazinga-v1.3.0-both-linux
./install.sh both .

# Windows offline
# Download: bazinga-v1.3.0-both-windows.zip
Expand-Archive bazinga-v1.3.0-both-windows.zip
cd bazinga-v1.3.0-both-windows
.\install.ps1 -Platform both -Target .
```

---

## 10. Debate Feedback Integration

### Verdict: APPROVE WITH CHANGES

### Required Changes (Incorporated)

#### 1. Corporate Security Enhancements
- **GPG Signing:** All release artifacts must be GPG signed
- **SBOM Generation:** Include Software Bill of Materials for compliance
- **Internal Repository:** Document Artifactory/Nexus hosting procedures

#### 2. Offline Installation Completeness
- **Dashboard:** Include pre-built dashboard OR document Node.js air-gap strategy
- **Verification:** Add `bazinga verify` command for post-installation integrity
- **Unix Permissions:** Handle SELinux contexts, umask, executable permissions

#### 3. Timeline Adjustment
| Phase | Original | Revised |
|-------|----------|---------|
| Phase 1: CLI | 2 weeks | **3 weeks** |
| Phase 2: Offline | 2 weeks | **3 weeks** |
| Phase 3: Testing | 1 week | **2 weeks** |
| **Total** | 5 weeks | **8 weeks** |

#### 4. Auto-Detection Refinement
- Default to `--platform claude` (current behavior), not auto-detect
- Require explicit `--platform auto` to enable detection
- Add confirmation prompt when auto-detect is ambiguous

### Recommended Changes (Incorporated)

#### 1. Simplified Release Artifacts
Reduce from 9 to 4 artifacts:
```
bazinga-vX.Y.Z-all-unix.tar.gz      # Both platforms, sh installer
bazinga-vX.Y.Z-all-windows.zip      # Both platforms, ps1 installer
bazinga-vX.Y.Z-py3-none-any.whl     # Python wheel
ghcr.io/mehdic/bazinga:vX.Y.Z       # Docker image
```

#### 2. Docker in MVP (Elevated from Future)
```dockerfile
FROM python:3.11-slim
COPY . /bazinga
RUN pip install /bazinga
ENTRYPOINT ["bazinga"]
```

#### 3. Windows-Specific Enhancements
- Use NTFS junction points instead of symlinks (no admin required)
- Document PowerShell execution policy: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- Handle MAX_PATH (260 char) limitation with `\\?\` prefix

#### 4. Enterprise Documentation
Create dedicated `docs/enterprise-installation.md`:
- Proxy configuration (`HTTP_PROXY`, `HTTPS_PROXY`)
- Custom CA bundle configuration
- Rollback procedures
- Version pinning

### Additional Considerations from Debate

| Concern | Resolution |
|---------|------------|
| Auto-detect may surprise users | Default to explicit platform |
| Dashboard needs Node.js | Pre-build or document |
| No package signing | Add GPG signing to workflow |
| Windows symlinks need admin | Use junction points |
| 9 release artifacts is too many | Reduce to 4 |
| Docker marked as "future" | Elevate to MVP |

---

## 11. Updated Recommendation

**Final Approach: Enhanced Hybrid (Option D+)**

1. **Primary:** pip/uvx with explicit `--platform` flag (default: claude)
2. **Secondary:** GitHub Releases with 4 artifacts (unix, windows, wheel, docker)
3. **Enterprise:** Docker image + enterprise documentation
4. **Security:** GPG signing + SBOM + checksums

**Revised Timeline: 8 weeks** (vs original 5 weeks)

---

## References

- [GitHub Spec-Kit](https://github.com/github/spec-kit) - Multi-platform CLI reference
- [Spec-Kit Installation Guide](https://github.github.com/spec-kit/installation.html)
- [Python Packaging Guide](https://packaging.python.org/guides/tool-recommendations/)
- [Shiv Documentation](https://github.com/linkedin/shiv)
- [GitHub Actions Release Workflow](https://docs.github.com/en/actions/using-workflows/releasing-and-maintaining-actions)
- [GPG Signing Releases](https://docs.github.com/en/authentication/managing-commit-signature-verification)
- [SBOM Generation](https://cyclonedx.org/)
