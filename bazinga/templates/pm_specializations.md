# PM Specialization Assignment Details

**Purpose:** Provide technology-specific patterns to agents based on which component(s) each task group targets.

## Step 3.5.1: Read Project Context (from Tech Stack Scout)

```
Read(file_path: "bazinga/project_context.json")
```

**If file missing or empty:** Skip specializations (graceful degradation). Continue to Step 3.6.

## Step 3.5.1b: Fallback Mapping Table

If `project_context.json` exists but lacks `components[].suggested_specializations`, use this mapping table:

**Canonical Key → Template Path Mapping:**

| Canonical Key | Aliases | Template Path |
|---------------|---------|---------------|
| typescript | TypeScript, ts | `bazinga/templates/specializations/01-languages/typescript.md` |
| javascript | JavaScript, js | `bazinga/templates/specializations/01-languages/javascript.md` |
| python | Python, py | `bazinga/templates/specializations/01-languages/python.md` |
| java | Java | `bazinga/templates/specializations/01-languages/java.md` |
| go | Go, Golang, golang | `bazinga/templates/specializations/01-languages/go.md` |
| rust | Rust | `bazinga/templates/specializations/01-languages/rust.md` |
| react | React, reactjs | `bazinga/templates/specializations/02-frameworks-frontend/react.md` |
| nextjs | Next.js, next, next.js | `bazinga/templates/specializations/02-frameworks-frontend/nextjs.md` |
| vue | Vue, vuejs, vue.js | `bazinga/templates/specializations/02-frameworks-frontend/vue.md` |
| angular | Angular | `bazinga/templates/specializations/02-frameworks-frontend/angular.md` |
| express | Express, expressjs | `bazinga/templates/specializations/03-frameworks-backend/express.md` |
| fastapi | FastAPI, fast-api | `bazinga/templates/specializations/03-frameworks-backend/fastapi.md` |
| django | Django | `bazinga/templates/specializations/03-frameworks-backend/django.md` |
| springboot | Spring Boot, spring-boot, spring | `bazinga/templates/specializations/03-frameworks-backend/spring-boot.md` |
| kubernetes | Kubernetes, k8s, K8s | `bazinga/templates/specializations/06-infrastructure/kubernetes.md` |
| docker | Docker | `bazinga/templates/specializations/06-infrastructure/docker.md` |
| postgresql | PostgreSQL, postgres, pg | `bazinga/templates/specializations/05-databases/postgresql.md` |
| mongodb | MongoDB, mongo | `bazinga/templates/specializations/05-databases/mongodb.md` |
| playwright | Playwright, Cypress, cypress | `bazinga/templates/specializations/08-testing/playwright-cypress.md` |
| jest | Jest, Vitest, vitest | `bazinga/templates/specializations/08-testing/jest-vitest.md` |

## Helper Functions

```
# Build MAPPING_TABLE from the canonical key table above (canonical keys only)
MAPPING_TABLE = {
  "typescript": "bazinga/templates/specializations/01-languages/typescript.md",
  "javascript": "bazinga/templates/specializations/01-languages/javascript.md",
  "python": "bazinga/templates/specializations/01-languages/python.md",
  "java": "bazinga/templates/specializations/01-languages/java.md",
  "go": "bazinga/templates/specializations/01-languages/go.md",
  "rust": "bazinga/templates/specializations/01-languages/rust.md",
  "react": "bazinga/templates/specializations/02-frameworks-frontend/react.md",
  "nextjs": "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md",
  "vue": "bazinga/templates/specializations/02-frameworks-frontend/vue.md",
  "angular": "bazinga/templates/specializations/02-frameworks-frontend/angular.md",
  "express": "bazinga/templates/specializations/03-frameworks-backend/express.md",
  "fastapi": "bazinga/templates/specializations/03-frameworks-backend/fastapi.md",
  "django": "bazinga/templates/specializations/03-frameworks-backend/django.md",
  "springboot": "bazinga/templates/specializations/03-frameworks-backend/spring-boot.md",
  "kubernetes": "bazinga/templates/specializations/06-infrastructure/kubernetes.md",
  "docker": "bazinga/templates/specializations/06-infrastructure/docker.md",
  "postgresql": "bazinga/templates/specializations/05-databases/postgresql.md",
  "mongodb": "bazinga/templates/specializations/05-databases/mongodb.md",
  "playwright": "bazinga/templates/specializations/08-testing/playwright-cypress.md",
  "cypress": "bazinga/templates/specializations/08-testing/playwright-cypress.md",
  "jest": "bazinga/templates/specializations/08-testing/jest-vitest.md",
  "vitest": "bazinga/templates/specializations/08-testing/jest-vitest.md"
}

# Utility: Remove punctuation characters from string (preserves + and # for C++/C#)
FUNCTION remove_punctuation(text):
  # Remove only: . - _ / \ (common separators)
  # Keep: + # (for C++, C#, F# language names)
  result = ""
  FOR each char in text:
    IF char is alphanumeric OR char is space OR char in ['+', '#']:
      result += char
  RETURN result

# Utility: Remove all whitespace from string
FUNCTION remove_whitespace(text):
  RETURN text with all whitespace removed

# Utility: Check if file exists
FUNCTION file_exists(path):
  RETURN os.path.isfile(path)

# Normalize input to canonical key
FUNCTION normalize_key(input):
  key = input.lower().strip()
  key = remove_punctuation(key)
  key = remove_whitespace(key)

  ALIAS_MAP = {
    "k8s": "kubernetes",
    "ts": "typescript",
    "js": "javascript",
    "py": "python",
    "pg": "postgresql",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "next": "nextjs",
    "spring": "springboot",
    "golang": "go",
    "reactjs": "react",
    "vuejs": "vue",
    "expressjs": "express"
  }
  IF key IN ALIAS_MAP: key = ALIAS_MAP[key]
  RETURN key

# Parse framework string like "React (Frontend), Express (Backend)"
FUNCTION parse_frameworks(framework_string):
  parts = framework_string.split(",")
  frameworks = []
  FOR each part in parts:
    clean = part
    IF "(" in clean:
      start = clean.find("(")
      end = clean.find(")", start)
      IF end > start:
        clean = clean[:start] + clean[end+1:]
    clean = clean.strip()
    IF clean: frameworks.append(clean)
  RETURN frameworks

# Stable deduplication preserving insertion order
FUNCTION dedupe_stable(items):
  seen = set()
  result = []
  FOR item in items:
    IF item NOT IN seen:
      seen.add(item)
      result.append(item)
  RETURN result

# Lookup with normalization and file existence check
FUNCTION lookup_and_validate(input):
  key = normalize_key(input)
  path = MAPPING_TABLE.get(key)
  IF path is None:
    LOG_WARNING("Unmapped technology: {} (normalized: {})", input, key)
    RETURN None
  IF NOT file_exists(path):
    LOG_WARNING("Template file does not exist: {}", path)
    RETURN None
  RETURN path
```

**Fallback logic:**
```
IF project_context has NO components[].suggested_specializations:
  specializations = []

  # Map primary_language
  IF project_context.primary_language:
    path = lookup_and_validate(project_context.primary_language)
    IF path: specializations.append(path)

  # Map framework(s)
  IF project_context.framework:
    frameworks = parse_frameworks(project_context.framework)
    FOR each fw in frameworks:
      path = lookup_and_validate(fw)
      IF path: specializations.append(path)

  # Map database(s)
  IF project_context.database:
    databases = parse_frameworks(project_context.database)
    FOR each db in databases:
      path = lookup_and_validate(db)
      IF path: specializations.append(path)

  # Map infrastructure
  IF project_context.infrastructure:
    infra_items = parse_frameworks(project_context.infrastructure)
    FOR each item in infra_items:
      path = lookup_and_validate(item)
      IF path: specializations.append(path)

  # Map testing framework(s)
  IF project_context.testing:
    test_frameworks = parse_frameworks(project_context.testing)
    FOR each tf in test_frameworks:
      path = lookup_and_validate(tf)
      IF path: specializations.append(path)

  specializations = dedupe_stable(specializations)
```

## Step 3.5.2: Map Task Groups to Components

For each task group, determine which component(s) it targets:

```
Example project_context.json structure:
{
  "components": [
    {
      "path": "frontend/",
      "type": "frontend",
      "framework": "nextjs",
      "suggested_specializations": [
        "bazinga/templates/specializations/01-languages/typescript.md",
        "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md"
      ]
    },
    {
      "path": "backend/",
      "type": "backend",
      "framework": "fastapi",
      "suggested_specializations": [
        "bazinga/templates/specializations/01-languages/python.md",
        "bazinga/templates/specializations/03-frameworks-backend/fastapi.md"
      ]
    }
  ]
}
```

**Path matching logic:**

```
FUNCTION path_matches(target_path, component_path):
  real_target = os.path.realpath(target_path)
  real_component = os.path.realpath(component_path)
  norm_target = os.path.normpath(real_target)
  norm_component = os.path.normpath(real_component)
  TRY:
    common = os.path.commonpath([norm_target, norm_component])
    RETURN common == norm_component
  CATCH ValueError:
    RETURN False

FOR each task_group:
  specializations = []

  IF project_context.components EXISTS AND has suggested_specializations:
    target_paths = extract file paths from task description
    matched_components = []

    FOR each component in project_context.components:
      FOR each target_path in target_paths:
        IF path_matches(target_path, component.path):
          matched_components.append(component)
          BREAK

    IF len(matched_components) > 0:
      FOR component in matched_components:
        specializations.extend(component.suggested_specializations)
      specializations = dedupe_stable(specializations)

  # FALLBACK: Use mapping table if no suggested_specializations found
  IF len(specializations) == 0:
    [Use fallback logic from Step 3.5.1b]

  task_group.specializations = specializations
```

## Step 3.5.3: Include Specializations in Task Group Definition

```markdown
**Group A:** Implement Login UI
- **Type:** implementation
- **Complexity:** 5 (MEDIUM)
- **Initial Tier:** Developer
- **Execution Phase:** 1
- **Target Path:** frontend/src/pages/login.tsx
- **Specializations:** ["bazinga/templates/specializations/01-languages/typescript.md", "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md"]
```

## Step 3.5.4: Store Specializations via bazinga-db

```
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
Complexity: 5
Initial Tier: Developer
--specializations '["bazinga/templates/specializations/01-languages/typescript.md", "bazinga/templates/specializations/02-frameworks-frontend/nextjs.md"]'
```

Then invoke: `Skill(command: "bazinga-db")`

**No specialization limit:** Assign as many specializations as the task requires. The orchestrator validates paths exist before including in agent prompts.
