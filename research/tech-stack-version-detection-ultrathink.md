# Tech Stack Version Detection: Ultrathink Analysis

**Date:** 2025-12-17
**Context:** Version information missing from project_context.json, preventing version guard filtering
**Decision:** Extend Tech Stack Scout schema and detection logic to capture language/framework versions
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

The prompt builder has version guard filtering implemented:

```markdown
<!-- version: python >= 3.10 -->
- **Use `|` union syntax**: `def foo(x: str | None) -> int | str`
<!-- version: python < 3.10 -->
- **Use `Optional`/`Union`**: `def foo(x: Optional[str]) -> Union[int, str]`
```

But it can't filter because **Tech Stack Scout doesn't detect versions**:

```json
// Current project_context.json - NO VERSION
{
  "primary_language": "python",
  "primary_language_version": null  // MISSING!
}
```

**Impact:**
- All version-guarded content is included (conservative fallback)
- Agent sees both Python 3.10+ AND pre-3.10 patterns
- Wasted tokens (~100-200 per template)
- Potentially confusing guidance

---

## Root Cause Analysis

### 1. Schema Gap

The `project_context.json` schema has no version fields:

| Field | Current | Needed |
|-------|---------|--------|
| `primary_language` | ✅ "python" | ✅ |
| `primary_language_version` | ❌ Missing | "3.11" |
| `secondary_languages` | ✅ ["sql"] | Need versions |
| `components[].framework_version` | ❌ Missing | "14.0.0" |

### 2. Detection Logic Gap

Tech Stack Scout doesn't extract versions from:

| Source File | Version Info |
|-------------|--------------|
| `pyproject.toml` | `tool.poetry.dependencies.python = "^3.11"` |
| `pyproject.toml` | `project.requires-python = ">=3.10"` |
| `.python-version` | `3.11.4` |
| `setup.py` | `python_requires=">=3.10"` |
| `runtime.txt` | `python-3.11.4` |
| `package.json` | `engines.node: ">=18"` |
| `.nvmrc` | `18.17.0` |
| `go.mod` | `go 1.21` |
| `Cargo.toml` | `rust-version = "1.70"` |

### 3. Evidence Array Has Versions (Partial)

Tech Stack Scout DOES capture framework versions in evidence:

```json
"evidence": [
  {"file": "package.json", "key": "next", "version": "14.0.0"}
]
```

But this isn't exposed at the top level for easy access.

---

## Proposed Solution

### Option A: Extend Schema (Recommended)

**Add explicit version fields to project_context.json:**

```json
{
  "schema_version": "2.1",  // Bump version

  "primary_language": "python",
  "primary_language_version": "3.11",  // NEW

  "secondary_languages": [
    {"name": "sql", "version": null},  // ENHANCED
    {"name": "bash", "version": null}
  ],

  "components": [
    {
      "path": "backend/",
      "language": "python",
      "language_version": "3.11",  // NEW
      "framework": "fastapi",
      "framework_version": "0.104.0",  // NEW (from evidence)
      ...
    }
  ],

  "infrastructure": {
    "node_version": "18.17.0",  // NEW (if Node.js detected)
    "python_version": "3.11",   // NEW (if Python detected)
    ...
  }
}
```

**Pros:**
- Clean, explicit schema
- Easy for prompt builder to consume
- Backward compatible (new fields are additive)

**Cons:**
- Requires Tech Stack Scout changes
- More fields to maintain

### Option B: Extract from Evidence Array

**Prompt builder reads version from existing evidence:**

```python
def get_language_version(project_context, language):
    for component in project_context.get('components', []):
        if component.get('language') == language:
            for ev in component.get('evidence', []):
                if ev.get('key') == language:
                    return ev.get('version')
    return None
```

**Pros:**
- No schema changes
- Works with existing data

**Cons:**
- Fragile (evidence format varies)
- Language versions != framework versions in evidence
- Doesn't capture from dedicated version files (.python-version, .nvmrc)

### Option C: Hybrid Approach (Best)

1. **Schema extension** (Option A) for explicit version fields
2. **Tech Stack Scout enhancement** to detect from version files
3. **Prompt builder fallback** to evidence if explicit field missing

---

## Implementation Plan

### Phase 1: Schema Extension (Low Effort)

**File:** `agents/tech_stack_scout.md`

Add to detection steps:

```markdown
### Step 0: Detect Language Versions

**Check version files first (highest confidence):**

| File | Language | Parse Pattern |
|------|----------|---------------|
| `.python-version` | Python | Full content (e.g., "3.11.4") |
| `.nvmrc` | Node.js | Full content (e.g., "18.17.0") |
| `.node-version` | Node.js | Full content |
| `.ruby-version` | Ruby | Full content |
| `.go-version` | Go | Full content |

**Then check config files:**

| File | Language | Parse Pattern |
|------|----------|---------------|
| `pyproject.toml` | Python | `tool.poetry.dependencies.python` or `project.requires-python` |
| `setup.py` | Python | `python_requires` argument |
| `setup.cfg` | Python | `[options] python_requires` |
| `runtime.txt` | Python | "python-X.Y.Z" |
| `package.json` | Node.js | `engines.node` |
| `go.mod` | Go | `go X.Y` directive |
| `Cargo.toml` | Rust | `rust-version` key |

**Version normalization:**
- Remove operators: ">=3.10" → "3.10", "^3.11" → "3.11"
- Keep major.minor: "3.11.4" → "3.11" (for comparison)
- Store full version in `_full` field if needed
```

**Add to output format:**

```json
{
  "primary_language": "python",
  "primary_language_version": "3.11",

  "versions_detected": {
    "python": {"version": "3.11", "source": ".python-version", "confidence": "high"},
    "node": {"version": "18", "source": "package.json", "confidence": "medium"}
  }
}
```

### Phase 2: Prompt Builder Integration (Already Done)

The prompt builder already checks:
- `project_context.get('primary_language_version')`
- `secondary_languages[].version`
- `infrastructure.{lang}_version`

Just needs Tech Stack Scout to populate these fields.

### Phase 3: Testing

1. Run Tech Stack Scout on test project with `.python-version` file
2. Verify `primary_language_version` is populated
3. Rebuild developer prompt
4. Verify version guards correctly filter content

---

## Version Detection Logic

### Python Version Detection

**Priority order (highest to lowest confidence):**

1. `.python-version` - Explicit, pyenv standard
2. `pyproject.toml` - Modern Python projects
3. `setup.cfg` - Legacy Python projects
4. `setup.py` - Legacy Python projects
5. `runtime.txt` - Heroku deployments
6. `Pipfile` - Pipenv projects

**Parsing examples:**

```python
# .python-version
"3.11.4"  # → "3.11"

# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"  # → "3.11"

[project]
requires-python = ">=3.10"  # → "3.10"

# setup.py
setup(
    python_requires=">=3.10",  # → "3.10"
)

# runtime.txt
python-3.11.4  # → "3.11"
```

### Node.js Version Detection

**Priority order:**

1. `.nvmrc` or `.node-version` - Explicit
2. `package.json` engines.node - Project requirement
3. `.tool-versions` (asdf) - Multi-language version manager

**Parsing examples:**

```json
// package.json
{
  "engines": {
    "node": ">=18.0.0"  // → "18"
  }
}

// .nvmrc
18.17.0  // → "18"
lts/iron  // → "20" (resolve LTS name)
```

### Go Version Detection

**Priority order:**

1. `.go-version` - Explicit
2. `go.mod` - Module file

**Parsing examples:**

```go
// go.mod
go 1.21  // → "1.21"
```

---

## Edge Cases

### No Version Detected

If no version file found:
- Set `primary_language_version: null`
- Prompt builder uses conservative fallback (include all content)
- Log detection note: "No Python version detected, version guards inactive"

### Version Range

If version is a range like ">=3.10,<4.0":
- Extract minimum: "3.10"
- This is the minimum required, safe for version guards

### Multiple Python Versions (Monorepo)

If different components have different versions:
- Set `primary_language_version` to the lowest common version
- Store per-component versions in `components[].language_version`
- Log: "Multiple Python versions detected: 3.10 (backend), 3.11 (scripts)"

---

## Effort Estimate

| Task | Effort | Files |
|------|--------|-------|
| Update schema documentation | Low | tech_stack_scout.md |
| Add version detection logic | Medium | tech_stack_scout.md |
| Test with various projects | Low | Manual testing |
| Update project_context.json examples | Low | tech_stack_scout.md |

**Total: ~2-4 hours**

---

## Decision Rationale

### Why Option A (Schema Extension)?

1. **Explicit > Implicit**: Clear version fields are easier to consume than parsing evidence arrays
2. **Future-proof**: Schema versions can evolve independently
3. **Single responsibility**: Tech Stack Scout handles all detection, prompt builder just reads
4. **Debuggability**: Easy to see what version was detected in project_context.json

### Why Not Option B (Evidence Parsing)?

1. Evidence format is inconsistent (framework versions, not language versions)
2. Doesn't capture from dedicated version files (.python-version, .nvmrc)
3. Complex parsing logic duplicated in multiple places

---

## Success Criteria

1. ✅ Tech Stack Scout outputs `primary_language_version` when detected
2. ✅ Prompt builder correctly filters Python 3.10+ vs pre-3.10 content
3. ✅ Version guards remove conflicting guidance from prompts
4. ✅ Conservative fallback works when version unknown
5. ✅ Schema is backward compatible (old project_context.json still works)

---

## References

- [PEP 508](https://peps.python.org/pep-0508/) - Python dependency specifiers
- [pyenv](https://github.com/pyenv/pyenv) - .python-version standard
- [nvm](https://github.com/nvm-sh/nvm) - .nvmrc standard
- [asdf](https://asdf-vm.com/) - .tool-versions format
