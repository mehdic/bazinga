---
name: codebase-analysis
description: Analyze codebase to find similar features, reusable utilities, and architectural patterns
allowed-tools: [Bash, Read, Write, Grep]
---

# Codebase Analysis Skill

You are the codebase-analysis skill. When invoked with a task description, you analyze the existing codebase to find similar features, reusable utilities, and architectural patterns.

## Your Task

When invoked, you will:
1. Extract keywords from the task description
2. Find similar existing features
3. Discover reusable utilities
4. Identify architectural patterns
5. Extract project conventions
6. Generate implementation suggestions

---

## Step 1: Extract Keywords from Task

When invoked, you'll receive a task description (e.g., "Implement password reset endpoint").

Extract relevant keywords:
- Primary feature: "password reset"
- Related concepts: "email", "token", "authentication", "validation"
- Component type: "endpoint", "API"

---

## Step 2: Find Similar Features

Use **Grep** to search for similar functionality:

```bash
# Search for related keywords in source files
grep -r -i "password\|reset\|token" --include="*.py" --include="*.js" --include="*.go" --include="*.java" -l .
```

Use the **Read** tool to read the top 3-5 most relevant files.

Analyze each file for:
- Similar functionality patterns
- Key functions/classes used
- Dependencies and imports
- Error handling approaches
- Test coverage approach

Calculate similarity score (0-1):
```
similarity = (matching_keywords / total_keywords) × (shared_patterns_count / 10)
```

---

## Step 3: Discover Reusable Utilities

Use **Bash** to find common utility directories:

```bash
find . -type d -name "utils" -o -name "helpers" -o -name "lib" -o -name "common" -o -name "services"
```

Use **Grep** to find relevant utility functions:

```bash
# For task "password reset", search for:
grep -r "class.*Service\|def send_email\|def generate_token\|def validate_email" utils/ lib/ services/ --include="*.py"
```

For each utility found:
- Extract name, file path, purpose
- Check if it matches task requirements

---

## Step 4: Identify Architectural Patterns

Use **Bash** to analyze directory structure:

```bash
ls -d */ | head -20
```

Identify common patterns:
- **Service layer**: `services/` directory exists → "Service layer pattern"
- **Repository**: `repositories/` or `repos/` exists → "Repository pattern"
- **Factory**: Files ending in `_factory.py` → "Factory pattern"
- **MVC**: `models/`, `views/`, `controllers/` → "MVC pattern"

Use **Grep** to detect dependency injection:
```bash
grep -r "def __init__.*:.*\)" --include="*.py" | head -5
```

---

## Step 5: Extract Project Conventions

**Test coverage target:**
Use **Read** to check:
- `pytest.ini` for `--cov-fail-under=XX`
- `jest.config.js` for `coverageThreshold`

**Error handling:**
Use **Grep** to find common error response patterns:
```bash
grep -r "def error_response\|class.*Error\|return.*error" utils/ lib/ --include="*.py" -l | head -3
```

**Code style:**
- Check for `.editorconfig`, `.prettierrc`, `pyproject.toml`

---

## Step 6: Generate Implementation Suggestion

Based on analysis, create a suggested approach:

```
Suggested approach:
1. Create {FeatureName}Service in services/ (following service layer pattern)
2. Reuse {UtilityName} from utils/{file}
3. Follow {PatternName} pattern like {SimilarFile}
4. Add tests with {coverage_target}% coverage
5. Use {ErrorHandler} for error responses
```

---

## Step 7: Write Output

Use the **Write** tool to create `coordination/codebase_analysis.json`:

```json
{
  "task": "<original task description>",
  "similar_features": [
    {
      "file": "<file path>",
      "similarity_score": <0-1>,
      "patterns": ["<pattern1>", "<pattern2>"],
      "key_functions": ["<function1>", "<function2>"]
    }
  ],
  "reusable_utilities": [
    {
      "name": "<utility name>",
      "file": "<file path>",
      "functions": ["<function1>", "<function2>"]
    }
  ],
  "architectural_patterns": [
    "<pattern 1>",
    "<pattern 2>"
  ],
  "suggested_approach": "<implementation suggestion>",
  "conventions": [
    "<convention 1>",
    "<convention 2>"
  ]
}
```

---

## Step 8: Return Summary

Return a concise summary:

```
Codebase Analysis:
- Similar features found: X
- Reusable utilities: Y

Most similar: {file} (similarity: {score})

Reusable utilities:
- {utility1}: {description}
- {utility2}: {description}

Architectural patterns:
- {pattern1}
- {pattern2}

Suggested approach:
{approach}

Details saved to: coordination/codebase_analysis.json
```

---

## Error Handling

**If no similar features found:**
- Return: "No similar features found. Suggest implementing from scratch following project patterns."

**If no utilities found:**
- Return: "No reusable utilities found. Developer may need to create new utility functions."

**If codebase structure unclear:**
- Return: "Could not detect clear architectural patterns. Analyze manually."

---

## Notes

- Focus on **high similarity matches** (>0.7)
- Prioritize **reusable code** to avoid duplication
- Respect **existing patterns** for consistency
- Include **test patterns** in analysis
