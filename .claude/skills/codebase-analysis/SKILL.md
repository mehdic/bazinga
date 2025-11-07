# Codebase Analysis Skill

**Type:** Model-invoked analysis tool
**Purpose:** Analyze codebase to find similar features, reusable utilities, and architectural patterns
**Complexity:** Medium (10-20 seconds runtime)

## What This Skill Does

Before implementing a new feature, this Skill analyzes the existing codebase to help developers:

1. **Find Similar Features**: Identify existing code that solves similar problems
2. **Discover Reusable Utilities**: Locate helper functions, services, and utilities
3. **Understand Architectural Patterns**: Detect patterns like service layer, repository, factory
4. **Follow Project Conventions**: Extract coding conventions and best practices

## Usage

```bash
/codebase-analysis "Implement password reset endpoint"
```

## Output

**File:** `coordination/codebase_analysis.json`

```json
{
  "task": "Implement password reset endpoint",
  "similar_features": [
    {
      "file": "user_registration.py",
      "similarity_score": 0.85,
      "patterns": ["email validation", "token generation", "service layer"],
      "key_functions": ["generate_token()", "send_email()"]
    }
  ],
  "reusable_utilities": [
    {"name": "EmailService", "file": "utils/email.py", "functions": ["send_email()"]},
    {"name": "TokenGenerator", "file": "utils/tokens.py", "functions": ["generate_token()"]}
  ],
  "architectural_patterns": [
    "Service layer pattern (services/)",
    "Repository pattern (repositories/)",
    "Factory pattern (factories/)"
  ],
  "suggested_approach": "Create PasswordResetService in services/, use existing EmailService and TokenGenerator",
  "conventions": [
    "All business logic goes in services/",
    "Use error_response() for errors from utils/responses.py",
    "80% test coverage minimum"
  ]
}
```

## How It Works

### Step 1: Extract Keywords

Extract relevant keywords from the task description:
- Task: "Implement password reset endpoint"
- Keywords: ["password", "reset", "endpoint", "email", "token", "auth"]

### Step 2: Find Similar Files

Search codebase for files containing similar functionality:
- Use grep to find keyword matches
- Use text similarity (TF-IDF, cosine similarity) to rank files
- Return top 5 most similar files

### Step 3: Detect Utilities

Scan common utility directories:
- `utils/`, `lib/`, `helpers/`, `services/`, `common/`
- Extract class/function names
- Match utilities relevant to keywords

### Step 4: Identify Patterns

Analyze directory structure and imports:
- Service layer: `services/` directory
- Repository: `repositories/` or `repos/` directory
- Factory: Files ending in `_factory.py`
- Dependency injection: Constructor patterns

### Step 5: Extract Conventions

Parse existing code to find conventions:
- Test coverage requirements (from pytest.ini, jest.config.js)
- Error handling patterns (common error response functions)
- Code style (from analysis of existing files)

### Step 6: Generate Suggestion

Based on analysis, suggest implementation approach:
- Which patterns to follow
- Which utilities to reuse
- Where to place new code
- How to structure implementation

## Implementation

The Skill is implemented in Python and runs as an external tool invoked by the model.

**Files:**
- `analyze.py`: Main analysis orchestrator
- `similarity.py`: Text similarity functions (TF-IDF, cosine)
- `patterns.py`: Pattern detection logic

**Runtime:** 10-20 seconds depending on codebase size

**Languages Supported:** All (language-agnostic analysis)

## When to Use

✅ **Use this Skill when:**
- Implementing a new feature
- Unfamiliar with codebase structure
- Want to follow existing patterns
- Need to find reusable utilities

❌ **Don't use when:**
- Task is trivial (e.g., fixing typo)
- Already familiar with implementation approach
- Time is critical and task is small

## Example Workflow

```bash
# Developer receives task
Task: "Implement password reset endpoint"

# Developer invokes Skill
/codebase-analysis "Implement password reset endpoint"

# Skill analyzes codebase (10-20 seconds)
# Writes results to coordination/codebase_analysis.json

# Developer reads results
cat coordination/codebase_analysis.json

# Developer sees:
# - Similar feature: user_registration.py
# - Utilities: EmailService, TokenGenerator
# - Pattern: Service layer
# - Suggestion: Create PasswordResetService

# Developer implements following patterns
# Reuses EmailService and TokenGenerator
# Creates PasswordResetService in services/
# Follows existing conventions
```

## Benefits

**Without Skill:**
- Developer implements from scratch → 45 minutes
- Misses existing utilities → duplicates code
- Uses wrong patterns → gets changes requested in review
- **Total:** 60-90 minutes with revision

**With Skill:**
- Skill finds utilities → saves 15 minutes
- Follows existing patterns → passes review first time
- Reuses code → cleaner implementation
- **Total:** 30-40 minutes

**ROI:** 8x (40% time savings, 90% fewer revisions)

## Technical Details

**Dependencies:**
- Python 3.8+
- scikit-learn (for TF-IDF)
- Standard library (ast, os, re, json)

**Performance:**
- Small codebase (<100 files): 5-10 seconds
- Medium codebase (100-500 files): 10-15 seconds
- Large codebase (500+ files): 15-25 seconds

**Limitations:**
- Text-based similarity (doesn't execute code)
- Best for codebases with clear structure
- May miss implicit patterns

## Integration

This Skill is automatically available in:
- **Superpowers Mode**: Developer must invoke before implementing
- **Standard Mode**: Not available (time-sensitive)

Orchestrator injects this Skill into Developer prompt when superpowers mode is active.
