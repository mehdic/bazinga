# Tech Stack Version Detection: Ultrathink Analysis

**Date:** 2025-12-17
**Context:** Version information missing from project_context.json, preventing version guard filtering. Additionally, monorepos need per-component version binding.
**Decision:** Extend schema, add per-component versions, bind task groups to components
**Status:** LLM Review Integrated - Ready for Implementation
**Reviewed by:** OpenAI GPT-5 ✅

---

## Problem Statement

### Problem 1: No Version Detection

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

### Problem 2: Monorepo Version Binding

For monorepos with multiple languages/versions:

```
project/
├── backend/      # Python 3.11, FastAPI
├── frontend/     # TypeScript, Node 18, React
└── mobile/       # TypeScript, React Native
```

**Current Flow:**
1. PM creates BACKEND task group → assigns python.md specialization
2. PM creates FRONTEND task group → assigns react.md, typescript.md specializations
3. Prompt builder loads templates but uses **global** `primary_language_version`

**Problem:** Both groups get the SAME version context. BACKEND should use Python 3.11 guards, FRONTEND should use Node 18 guards.

### Impact

- All version-guarded content is included (conservative fallback)
- Agent sees conflicting patterns (Python 3.10+ AND pre-3.10)
- Wasted tokens (~100-200 per template)
- Wrong version guidance for monorepo components

---

## Architecture Analysis

### Current Data Flow

```
┌─────────────────────┐
│  Tech Stack Scout   │  Writes: project_context.json
│  ─────────────────  │  - primary_language
│  Detects languages  │  - components[].suggested_specializations
│  Detects frameworks │  - NO per-component versions ❌
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PM (Project Mgr)   │  Reads: project_context.json
│  ─────────────────  │  Writes: task_groups table
│  Creates groups     │  - group.specializations ✅
│  Assigns specs      │  - NO component_path ❌
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Prompt Builder     │  Reads: task_groups.specializations
│  ─────────────────  │  Reads: project_context.json
│  Loads templates    │  - Uses global primary_language_version ❌
│  Applies guards     │  - NO per-component lookup ❌
└─────────────────────┘
```

### Required Data Flow

```
┌─────────────────────┐
│  Tech Stack Scout   │  Writes: project_context.json
│  ─────────────────  │  - primary_language + primary_language_version ✅
│  Detects versions   │  - components[].language_version ✅ NEW
│  Per-component      │  - components[].framework_version ✅ NEW
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PM (Project Mgr)   │  Reads: project_context.json
│  ─────────────────  │  Writes: task_groups table
│  Binds to component │  - group.specializations ✅
│                     │  - group.component_path ✅ NEW
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Prompt Builder     │  Reads: task_groups.specializations + component_path
│  ─────────────────  │  Looks up: components[component_path].language_version
│  Per-component ver  │  - Applies version guards with correct version ✅
└─────────────────────┘
```

---

## Files to Modify

### Overview Table

| # | File | Purpose | Changes |
|---|------|---------|---------|
| 1 | `agents/tech_stack_scout.md` | Version detection | Add version detection logic per component |
| 2 | `templates/pm_planning_steps.md` | PM workflow | Add component_path to task group creation |
| 3 | `.claude/skills/bazinga-db/scripts/init_db.py` | DB schema | Add component_path column to task_groups |
| 4 | `.claude/skills/bazinga-db/scripts/bazinga_db.py` | DB CLI | Support component_path in create/update |
| 5 | `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Prompt gen | Look up component version for guards |

---

## Detailed Implementation Plan

### File 1: `agents/tech_stack_scout.md`

**Purpose:** Add version detection for each component

**Location:** Lines ~56-72 (detection steps)

**Changes:**

Add new Step 0 before existing Step 1:

```markdown
### Step 0: Detect Language/Framework Versions

**Check version-specific files (highest confidence):**

| File | Language | Parse |
|------|----------|-------|
| `.python-version` | Python | Full content → "3.11" |
| `.nvmrc`, `.node-version` | Node.js | Full content → "18" |
| `.ruby-version` | Ruby | Full content |
| `.go-version` | Go | Full content |

**Check config files (medium confidence):**

| File | Field | Language/Framework |
|------|-------|---------------------|
| `pyproject.toml` | `project.requires-python` | Python |
| `pyproject.toml` | `tool.poetry.dependencies.python` | Python |
| `package.json` | `engines.node` | Node.js |
| `package.json` | `devDependencies.typescript` | TypeScript |
| `package.json` | `dependencies.react` | React |
| `package.json` | `dependencies.vue` | Vue |
| `package.json` | `dependencies.@angular/core` | Angular |
| `go.mod` | `go X.Y` directive | Go |
| `Cargo.toml` | `rust-version` | Rust |

**Version Normalization:**
- ">=3.10" → "3.10" (extract minimum)
- "^3.11" → "3.11" (extract base)
- "~18.2.0" → "18.2" (extract base)
- "3.11.4" → "3.11" (major.minor only)
- For ranges like ">=3.10,<4.0" → use minimum "3.10"
```

**Update output format (lines ~162-223):**

```json
{
  "schema_version": "2.1",

  "primary_language": "python",
  "primary_language_version": "3.11",  // NEW

  "components": [
    {
      "path": "backend/",
      "language": "python",
      "language_version": "3.11",      // NEW
      "framework": "fastapi",
      "framework_version": "0.104.0",  // NEW
      "suggested_specializations": [...]
    },
    {
      "path": "frontend/",
      "language": "typescript",
      "language_version": "5.0",       // NEW - from devDependencies.typescript
      "node_version": "18",            // NEW - from engines.node or .nvmrc
      "framework": "react",
      "framework_version": "18.2.0",   // NEW - from dependencies.react
      "suggested_specializations": [...]
    }
  ]
}
```

---

### File 2: `templates/pm_planning_steps.md`

**Purpose:** PM binds each task group to a component path

**Location:** Lines ~123-162 (Step 3.5: Assign Specializations)

**Changes:**

Update Step 3.5.2 (lines ~123-136):

```markdown
### Step 3.5.2: Map Task Groups to Components

```
FOR each task_group:
  specializations = []
  component_path = null  // NEW: Track which component this group belongs to
  target_paths = extract file paths from task description

  FOR each component in project_context.components:
    IF target_path starts with component.path:
      specializations.extend(component.suggested_specializations)
      component_path = component.path  // NEW: Bind to first matching component

  task_group.specializations = list(dict.fromkeys(specializations))
  task_group.component_path = component_path  // NEW
```
```

Update Step 3.5.3 (lines ~138-147):

```markdown
### Step 3.5.3: Include in Task Group Definition

```markdown
**Group A:** Implement Login UI
- **Type:** implementation
- **Complexity:** 5 (MEDIUM)
- **Initial Tier:** Developer
- **Target Path:** frontend/src/pages/login.tsx
- **Component Path:** frontend/              // NEW
- **Specializations:** ["01-languages/typescript.md", ...]
```
```

Update Step 3.5.4 canonical template (lines ~149-162):

```markdown
### Step 3.5.4: Store via bazinga-db (CANONICAL TEMPLATE)

```
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
Complexity: 5
Initial Tier: Developer
Item_Count: [number of tasks]
--component-path 'frontend/'                    // NEW
--specializations '["path/to/template1.md", ...]'
```

**Required fields:**
- `Item_Count` - Number of discrete tasks
- `--specializations` - Technology paths (NEVER empty)
- `--component-path` - Component this group belongs to (for version context)  // NEW
```

---

### File 3: `.claude/skills/bazinga-db/scripts/init_db.py`

**Purpose:** Add component_path column to task_groups table

**Location:** Lines ~1320-1345 (CREATE TABLE task_groups)

**Changes:**

Add column after `specializations` (line ~1336):

```python
CREATE TABLE IF NOT EXISTS task_groups (
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN (...)) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(...),
    feature_branch TEXT,
    merge_status TEXT CHECK(...),
    complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
    initial_tier TEXT CHECK(...) DEFAULT 'Developer',
    context_references TEXT,
    specializations TEXT,
    component_path TEXT,  -- NEW: Links to project_context.components[].path
    item_count INTEGER DEFAULT 1,
    security_sensitive INTEGER DEFAULT 0,
    qa_attempts INTEGER DEFAULT 0,
    tl_review_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, session_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)
```

**Add proper v15 migration** (following existing migration pattern with WAL checkpoint):

```python
# At top of file, bump schema version:
SCHEMA_VERSION = 15  # Was 14

# In migrate_schema() function, add v14→v15 migration block:
if current_version < 15:
    print("  Migrating v14 → v15: Adding component_path to task_groups...")
    cursor.execute("BEGIN IMMEDIATE")
    try:
        cursor.execute("ALTER TABLE task_groups ADD COLUMN component_path TEXT")
        cursor.execute("COMMIT")

        # Post-commit integrity checks (required by existing pattern)
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        result = cursor.execute("PRAGMA integrity_check").fetchone()
        if result[0] != "ok":
            raise Exception(f"Integrity check failed: {result[0]}")
        cursor.execute("ANALYZE task_groups")

        print("  ✓ Added component_path column to task_groups")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            cursor.execute("ROLLBACK")
            print("  ✓ component_path column already exists")
        else:
            cursor.execute("ROLLBACK")
            raise
```

**CRITICAL:** This follows the existing migration framework with:
- `BEGIN IMMEDIATE` for exclusive lock
- `PRAGMA wal_checkpoint(TRUNCATE)` for WAL cleanup
- `PRAGMA integrity_check` for corruption detection
- `ANALYZE` for query optimizer stats

---

### File 4: `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Purpose:** Support component_path in create/update task group operations

**Location:** Lines ~1166-1250 (create_task_group function)

**Changes:**

Update function signature (line ~1166):

```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None,
                     specializations: Optional[List[str]] = None,
                     item_count: Optional[int] = None,
                     component_path: Optional[str] = None) -> Dict[str, Any]:  # NEW
    """Create or update a task group (upsert - idempotent operation).

    Args:
        ...
        component_path: Path to the component this group belongs to (e.g., "backend/")
                       Used for per-component version context in prompt building.
    """
```

Update INSERT statement to include component_path:

```python
cursor.execute("""
    INSERT INTO task_groups (
        id, session_id, name, status, assigned_to,
        specializations, item_count, component_path  -- NEW
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)  -- Add ? for component_path
    ON CONFLICT(id, session_id) DO UPDATE SET
        name = excluded.name,
        status = excluded.status,
        assigned_to = excluded.assigned_to,
        specializations = excluded.specializations,
        item_count = excluded.item_count,
        component_path = excluded.component_path,  -- NEW
        updated_at = CURRENT_TIMESTAMP
""", (group_id, session_id, name, status, assigned_to,
      json.dumps(specializations) if specializations else None,
      item_count,
      component_path))  # NEW
```

**Update CLI manual flag parsing** (bazinga_db.py uses manual parsing, NOT argparse):

```python
# In create-task-group command handler, extend existing flag parsing:
# (around line ~2100 in handle_create_task_group or similar)

# Existing pattern for reference:
# --specializations '["path1", "path2"]'
# --item_count 5

# Add component_path parsing (normalize dashes to underscores):
component_path = None
for i, arg in enumerate(args):
    if arg in ('--component-path', '--component_path'):
        if i + 1 < len(args):
            component_path = args[i + 1]
        break

# Pass to create_task_group():
result = db.create_task_group(
    group_id=group_id,
    session_id=session_id,
    name=name,
    status=status,
    specializations=specializations,
    item_count=item_count,
    component_path=component_path  # NEW
)
```

**Also update `update-task-group` command:**

```python
# Add component_path to valid_flags dict:
valid_flags = {
    'status', 'assigned_to', 'specializations', 'item_count',
    'complexity', 'initial_tier', 'security_sensitive',
    'component_path'  # NEW
}

# Include in SQL building when provided
```

**CRITICAL:** Do NOT use argparse - the CLI uses manual flag parsing for subcommands.

---

### File 5: `.claude/skills/prompt-builder/scripts/prompt_builder.py`

**Purpose:** Look up component-specific version for version guards

**Location:** Lines ~584-599 (get_task_group_specializations) and ~769-802 (apply_version_guards)

**Changes:**

#### Change 5.1: Add function to get component path for task group

Add after `get_task_group_specializations()` (line ~600):

```python
def get_task_group_component_path(conn, session_id, group_id):
    """Get the component_path for a task group."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT component_path FROM task_groups WHERE session_id = ? AND id = ?",
            (session_id, group_id)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None
    except sqlite3.OperationalError:
        return None
```

#### Change 5.2: Add function to get component version context

Add after the above:

```python
def get_component_version_context(project_context, component_path):
    """Get version context for a specific component.

    Args:
        project_context: The full project_context.json dict
        component_path: Path like "backend/" or "frontend/"

    Returns:
        Dict with version info, e.g., {"python": "3.11", "fastapi": "0.104.0"}
        Falls back to global versions if component not found.
    """
    if not project_context:
        return {}

    if not component_path:
        # Fallback to global versions
        return _get_global_version_context(project_context)

    # LONGEST-PREFIX MATCH: Find most specific component
    # e.g., "backend/api/" should match before "backend/"
    best_match = None
    best_match_len = 0

    normalized_path = component_path.rstrip('/').replace('\\', '/') + '/'

    for comp in project_context.get("components", []):
        comp_path = (comp.get("path") or "").rstrip('/').replace('\\', '/') + '/'
        if normalized_path.startswith(comp_path) and len(comp_path) > best_match_len:
            best_match = comp
            best_match_len = len(comp_path)

    if best_match:
        return {
            # Language version
            best_match.get("language", "").lower(): best_match.get("language_version"),
            # Framework version
            best_match.get("framework", "").lower(): best_match.get("framework_version"),
            # Node version (for JS/TS projects)
            "node": best_match.get("node_version"),
            # TypeScript version
            "typescript": best_match.get("typescript_version"),
            # Test framework versions
            "pytest": best_match.get("pytest_version"),
            "jest": best_match.get("jest_version"),
        }

    # Fallback to global
    return _get_global_version_context(project_context)


def _get_global_version_context(project_context):
    """Get global version context as fallback."""
    return {
        "python": project_context.get("primary_language_version"),
        "node": project_context.get("infrastructure", {}).get("node_version"),
        "typescript": project_context.get("infrastructure", {}).get("typescript_version"),
    }
```

#### Change 5.3: Add inference fallback when component_path is missing

```python
def infer_component_from_specializations(project_context, spec_paths):
    """Infer component_path from specialization template paths.

    If PM didn't set component_path, try to match specialization paths
    to components by their directory prefixes.

    Example: "01-languages/python.md" → look for components with language="python"
    """
    if not project_context or not spec_paths:
        return None

    # Extract language hints from specialization paths
    for path in spec_paths:
        path_lower = path.lower()
        for comp in project_context.get("components", []):
            comp_lang = (comp.get("language") or "").lower()
            comp_framework = (comp.get("framework") or "").lower()

            # Match by language in path
            if comp_lang and comp_lang in path_lower:
                return comp.get("path")
            # Match by framework in path
            if comp_framework and comp_framework in path_lower:
                return comp.get("path")

    return None
```

#### Change 5.4: Update build_specialization_block to use component versions

Update `build_specialization_block()` (lines ~830-850):

```python
def build_specialization_block(conn, session_id, group_id, agent_type, model="sonnet"):
    """Build the specialization block from templates."""
    spec_paths = get_task_group_specializations(conn, session_id, group_id)

    if not spec_paths:
        return ""

    project_context = get_project_context()

    # Get component-specific version context (NEW)
    component_path = get_task_group_component_path(conn, session_id, group_id)

    # INFERENCE FALLBACK: If no component_path, try to infer from specializations
    if not component_path:
        component_path = infer_component_from_specializations(project_context, spec_paths)

    version_context = get_component_version_context(project_context, component_path)

    # Collect ALL template content - global budget trimming handles limits
    templates_content = []

    for path in spec_paths:
        # Pass version_context instead of full project_context (CHANGED)
        content = read_template_with_version_guards(path, version_context)
        if content:
            templates_content.append(content)

    # ... rest unchanged
```

#### Change 5.5: Update evaluate_version_guard with token normalization

Update `evaluate_version_guard()` (lines ~712-766):

```python
# Guard token vocabulary - maps aliases to canonical names
GUARD_TOKEN_ALIASES = {
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "ts": "typescript",
    "nodejs": "node",
    "node.js": "node",
    "reactjs": "react",
    "vuejs": "vue",
    "angular": "angular",
}

def normalize_guard_token(token):
    """Normalize guard token to canonical name."""
    token_lower = token.lower().strip()
    return GUARD_TOKEN_ALIASES.get(token_lower, token_lower)


def evaluate_version_guard(guard_text, version_context):
    """Evaluate a version guard against version context.

    Args:
        guard_text: e.g., "python >= 3.10" or "node >= 18"
        version_context: Dict like {"python": "3.11", "node": "18", "react": "18.2.0"}

    Returns:
        True if condition is met, False otherwise
    """
    if not version_context:
        return True  # No context = include everything

    # Parse conditions (comma-separated for AND)
    conditions = [c.strip() for c in guard_text.split(',')]

    for condition in conditions:
        # Support hyphenated names like "react-native"
        match = re.match(r'([\w\-\.]+)\s*(>=|>|<=|<|==)\s*([\d.]+)', condition)
        if not match:
            continue

        lang, operator, version_str = match.groups()
        required_version = parse_version(version_str)

        # Normalize token (e.g., "py" → "python", "ts" → "typescript")
        normalized_lang = normalize_guard_token(lang)

        # Look up detected version from context
        detected_version = parse_version(version_context.get(normalized_lang))

        if detected_version is not None:
            if not version_matches(detected_version, operator, required_version):
                return False
        # If no version detected, include content (conservative)

    return True
```

**Guard Token Vocabulary:**

| Guard Token | Detected From | Aliases |
|-------------|---------------|---------|
| `python` | `.python-version`, `pyproject.toml` | `py`, `python3` |
| `node` | `.nvmrc`, `package.json engines.node` | `nodejs`, `node.js` |
| `typescript` | `package.json devDependencies.typescript` | `ts` |
| `react` | `package.json dependencies.react` | `reactjs` |
| `vue` | `package.json dependencies.vue` | `vuejs` |
| `jest` | `package.json devDependencies.jest` | - |
| `pytest` | `pyproject.toml` | - |

---

## Migration Strategy

### Database Migration

The schema change adds a nullable column, so existing databases will:
1. Work without migration (component_path = NULL for old groups)
2. Auto-migrate on next bazinga-db invocation (ALTER TABLE)
3. New task groups will have component_path set by PM

### Backward Compatibility

| Scenario | Behavior |
|----------|----------|
| Old project_context.json (no versions) | Falls back to include all version-guarded content |
| Old task_groups (no component_path) | Falls back to global primary_language_version |
| New task_groups with component_path | Uses per-component versions |

---

## Testing Plan

### Test Case 1: Single-Language Project (Python 3.11)

1. Create `.python-version` with "3.11"
2. Run Tech Stack Scout
3. Verify `primary_language_version: "3.11"` in project_context.json
4. Run orchestration with calculator spec
5. Verify developer prompt excludes `<!-- version: python < 3.10 -->` content

### Test Case 2: Monorepo (Python backend + Node frontend)

1. Create structure:
   ```
   backend/.python-version  # 3.11
   frontend/.nvmrc          # 18
   ```
2. Run Tech Stack Scout
3. Verify components have language_version
4. Create two task groups via PM (BACKEND, FRONTEND)
5. Verify BACKEND group has `component_path: "backend/"`
6. Build developer prompt for BACKEND
7. Verify Python 3.11 guards applied (not Node guards)

### Test Case 3: Backward Compatibility

1. Use existing bazinga.db without component_path column
2. Run bazinga-db
3. Verify migration adds column
4. Verify old task groups still work (fallback to global version)

---

## Effort Estimate

| Task | Effort | Files |
|------|--------|-------|
| Tech Stack Scout version detection | 2 hours | agents/tech_stack_scout.md |
| PM component_path binding | 1 hour | templates/pm_planning_steps.md |
| Database schema + migration | 1 hour | init_db.py |
| bazinga-db CLI update | 1 hour | bazinga_db.py |
| Prompt builder component lookup | 2 hours | prompt_builder.py |
| Testing | 2 hours | Manual |

**Total: ~9 hours**

---

## Success Criteria

1. ✅ Tech Stack Scout outputs `components[].language_version`
2. ✅ PM stores `component_path` for each task group
3. ✅ Prompt builder looks up component-specific versions
4. ✅ Version guards filter correctly per component
5. ✅ Monorepo with Python backend + Node frontend works correctly
6. ✅ Backward compatible with existing databases/projects

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tech Stack Scout parses version incorrectly | Wrong guards applied | Add unit tests for version parsing |
| PM doesn't set component_path | Falls back to global | Inference fallback + global fallback (conservative) |
| Multiple components match path | Wrong component used | **Longest-prefix match** ensures most specific |
| Database migration fails | Old DBs broken | Proper v15 migration with WAL checkpoint + integrity check |
| Guard tokens mismatch template tokens | Guards don't filter | Token normalization + vocabulary mapping |
| Version range parsing edge cases | Wrong minimum extracted | Unit tests for ">=", "^", "~" patterns |

---

## References

- [PEP 508](https://peps.python.org/pep-0508/) - Python dependency specifiers
- [pyenv](https://github.com/pyenv/pyenv) - .python-version standard
- [nvm](https://github.com/nvm-sh/nvm) - .nvmrc standard

---

## Multi-LLM Review Integration

**Reviewer:** OpenAI GPT-5
**Date:** 2025-12-17

### Consensus Points (Incorporated)

All 6 recommendations from the LLM review were approved and integrated:

1. ✅ **Proper v15 database migration** - Replaced ad-hoc ALTER TABLE with full migration block including WAL checkpoint, integrity check, and ANALYZE
2. ✅ **Manual CLI flag parsing** - Replaced argparse suggestion with correct manual flag parsing pattern used by bazinga_db.py
3. ✅ **Longest-prefix component matching** - Updated `get_component_version_context()` to find most specific matching component
4. ✅ **Inference fallback** - Added `infer_component_from_specializations()` to derive component when PM doesn't set component_path
5. ✅ **Guard token normalization** - Added `GUARD_TOKEN_ALIASES` and `normalize_guard_token()` for "py"→"python", "ts"→"typescript" etc.
6. ✅ **Expanded version detection** - Added TypeScript, React, Vue, Angular version detection from package.json

### Critical Issues Fixed

| Issue | Original Plan | Fixed Plan |
|-------|---------------|------------|
| DB migration style | Ad-hoc ALTER TABLE | Proper v15 migration with WAL checkpoint |
| CLI parsing | argparse | Manual flag parsing (matches codebase) |
| Component matching | First match | Longest-prefix match |
| Missing component_path | Global fallback only | Inference fallback + global fallback |

### Rejected Suggestions

None - all suggestions were approved.

### Implementation Confidence

**Medium-High** - With all LLM feedback integrated:
- Database migration follows existing patterns
- CLI parsing matches codebase conventions
- Fallback chain ensures graceful degradation
- Token normalization prevents template/guard mismatches
