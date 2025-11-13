---
name: codebase-analysis
description: Analyze codebase to find similar features, reusable utilities, and architectural patterns
version: 1.0.0
allowed-tools: [Bash, Read]
---

# Codebase Analysis Skill

You are the codebase-analysis skill. When invoked with a task description, you analyze the existing codebase to find similar features, reusable utilities, and architectural patterns.

## When to Invoke This Skill

**Invoke this skill when:**
- Before starting new feature development
- Developer needs to find similar existing code
- Looking for reusable utilities or patterns
- Understanding codebase architecture
- Avoiding duplicate implementations

**Do NOT invoke when:**
- Implementing completely novel features with no precedent
- Working in greenfield projects with no existing code
- Fixing typos or documentation
- Emergency bug fixes (skip analysis to save time)

---

## Your Task

When invoked:
1. Execute the codebase analysis script with task description
2. Read the generated analysis report
3. Return a summary to the calling agent

---

## Step 1: Execute Codebase Analysis Script

Use the **Bash** tool to run the pre-built analysis script with the task description:

```bash
python3 .claude/skills/codebase-analysis/analyze.py --task "{task_description}"
```

This script will:
- Extract keywords from task description
- Find similar existing features
- Discover reusable utilities
- Identify architectural patterns
- Extract project conventions
- Generate `bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json`

---

## Step 2: Read Generated Report

Use the **Read** tool to read:

```bash
bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json
```

Extract key information:
- `similar_features` - Existing code to reference
- `reusable_utilities` - Functions/classes to reuse
- `architectural_patterns` - Project patterns to follow
- `suggested_approach` - Implementation guidance
- `conventions` - Code style and standards

---

## Step 3: Return Summary

Return a concise summary to the calling agent:

```
Codebase Analysis:
- Similar features found: {count}
- Reusable utilities: {count}

Most similar: {file} (similarity: {score})

Reusable utilities:
- {utility1}: {description}
- {utility2}: {description}

Architectural patterns:
- {pattern1}
- {pattern2}

Suggested approach:
{approach}

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json
```

---

## Example Invocation

**Scenario: Implementing Password Reset**

Input: Developer needs to implement password reset endpoint

Expected output:
```
Codebase Analysis:
- Similar features found: 3
- Reusable utilities: 5

Most similar: auth/login.py (similarity: 0.82)

Reusable utilities:
- EmailService (utils/email.py): Send templated emails
- TokenGenerator (utils/crypto.py): Generate secure tokens
- UserValidator (utils/validators.py): Validate email addresses

Architectural patterns:
- Service layer pattern (services/ directory)
- Repository pattern for database access
- JWT authentication

Suggested approach:
1. Create PasswordResetService in services/ (following service layer pattern)
2. Reuse EmailService from utils/email.py
3. Reuse TokenGenerator from utils/crypto.py
4. Follow existing auth patterns in auth/login.py
5. Add tests with 80% coverage target

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json
```

**Scenario: No Similar Features Found**

Input: Implementing completely new payment integration

Expected output:
```
Codebase Analysis:
- Similar features found: 0
- Reusable utilities: 2

No similar payment features found in codebase.

Reusable utilities:
- ApiClient (utils/http.py): HTTP client wrapper
- ConfigLoader (utils/config.py): Load environment config

Architectural patterns:
- Service layer pattern
- Dependency injection

Suggested approach:
1. Implement from scratch following project patterns
2. Create PaymentService in services/
3. Reuse ApiClient for external API calls
4. Add comprehensive tests (no existing payment tests to reference)

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/codebase_analysis.json
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

- The script handles all similarity matching and pattern detection
- Focuses on high similarity matches (>0.7)
- Prioritizes reusable code to avoid duplication
- Respects existing patterns for consistency
- Includes test patterns in analysis
