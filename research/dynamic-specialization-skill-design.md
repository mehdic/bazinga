# Dynamic Agent Specialization via Skill: Architecture Design

**Date:** 2025-12-04
**Context:** Extending BAZINGA with technology-aware agent specialization
**Decision:** Skill-based approach for dynamic agent identity and pattern injection
**Status:** Reviewed and Refined
**Reviewed by:** OpenAI GPT-5 (2025-12-04)

---

## Problem Statement

### Current Limitations

1. **Static Agent Identity**: Developer agent always starts with "You are a DEVELOPER AGENT" regardless of the project being Java/Spring Boot, Python/FastAPI, or React/TypeScript.

2. **Embedded Guidance Approach (Previous Proposal)**: The earlier research doc suggested PM embeds specialization in task descriptions. Issues:
   - PM code becomes bloated with template reading/condensing logic
   - Guidance appears in task description, not agent identity
   - Doesn't modify the "You are..." section that shapes agent behavior

3. **No Technology Awareness**: Agents operate generically without leveraging language/framework-specific patterns, anti-patterns, and verification checklists.

### User's Key Questions

1. **Who constructs the prompt?** Should be orchestrator or a skill, not PM.
2. **How does text flow to developers?** Via enhanced spawn prompt.
3. **Can identity be dynamic?** "You are a Java backend API developer specialized in Spring Boot"
4. **Should this be a skill?** Yes - avoids bloating PM, separation of concerns.
5. **Version awareness?** Adapt patterns to actual project versions (Java 8 vs 21, React 16 vs 18).

---

## Proposed Solution: `specialization-loader` Skill

### Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ 0. ORCHESTRATOR RUNS CODEBASE ANALYSIS (ONCE at session start)  │
├─────────────────────────────────────────────────────────────────┤
│ Skill(command: "codebase-analysis")                             │
│                                                                  │
│ Detects technologies via file patterns:                         │
│   - pom.xml + spring-boot-starter → Java + Spring Boot          │
│   - package.json + react → TypeScript + React                   │
│   - pyproject.toml + fastapi → Python + FastAPI                 │
│                                                                  │
│ Results CACHED to bazinga-db (project_stack table):             │
│ {                                                                │
│   "session_id": "bazinga_20251204_100000",                       │
│   "detected_technologies": {                                     │
│     "language": "java",                                          │
│     "language_version": "8",                                     │
│     "framework": "spring-boot",                                  │
│     "framework_version": "2.7",                                  │
│     "domain": "backend-api"                                      │
│   },                                                             │
│   "style_signals": { ... },                                      │
│   "cached_at": "2025-12-04T10:00:00Z"                            │
│ }                                                                │
│                                                                  │
│ ⚡ KEY OPTIMIZATION: Analysis runs ONCE, not per PM spawn        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. PM READS CACHED STACK DATA (no re-analysis needed)           │
├─────────────────────────────────────────────────────────────────┤
│ PM queries bazinga-db for cached technologies:                  │
│   SELECT * FROM project_stack WHERE session_id = ?              │
│                                                                  │
│ PM uses cached data for:                                         │
│   - Task planning (knows project stack)                          │
│   - Group assignment (per-group stack for monorepos)             │
│   - Developer specialization hints                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR INVOKES SKILL (before spawning developer)       │
├─────────────────────────────────────────────────────────────────┤
│ Skill(command: "specialization-loader")                         │
│                                                                  │
│ Skill reads from bazinga-db (NOT re-analyzing):                 │
│   - Cached technologies from project_stack table                │
│   - Templates from resources/templates/*.md                     │
│                                                                  │
│ Skill returns:                                                   │
│   - Enhanced identity string                                     │
│   - Condensed pattern guidance                                   │
│   - Verification checklist                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ORCHESTRATOR CONSTRUCTS ENHANCED SPAWN PROMPT                │
├─────────────────────────────────────────────────────────────────┤
│ Task(                                                            │
│   subagent_type: "developer",                                    │
│   prompt: """                                                    │
│     {SPECIALIZATION_BLOCK from skill}                           │
│                                                                  │
│     ## Your Task                                                 │
│     {Original task from PM}                                      │
│   """                                                            │
│ )                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Codebase Analysis Caching Strategy

**Problem:** PM may be spawned multiple times during an orchestration session (initial planning, after dev cycles, rework). Running codebase-analysis each time is wasteful.

**Solution:** Run analysis ONCE at orchestration start, cache in bazinga-db.

```
Session Timeline:
─────────────────────────────────────────────────────────────────────
│ Session Start                                                      │
│   └── Orchestrator runs codebase-analysis skill (ONCE)            │
│         └── Results cached to bazinga-db.project_stack            │
│                                                                    │
│ PM Spawn #1 (initial planning)                                    │
│   └── Reads cached data from DB (no analysis)                     │
│                                                                    │
│ Developer work...                                                  │
│                                                                    │
│ PM Spawn #2 (after QA feedback)                                   │
│   └── Reads cached data from DB (no analysis)                     │
│                                                                    │
│ PM Spawn #3 (rework assignment)                                   │
│   └── Reads cached data from DB (no analysis)                     │
│                                                                    │
│ Session End                                                        │
─────────────────────────────────────────────────────────────────────
```

**Database Schema Addition:**

```sql
CREATE TABLE project_stack (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    language TEXT,
    language_version TEXT,
    framework TEXT,
    framework_version TEXT,
    domain TEXT,
    style_signals TEXT,  -- JSON blob
    detected_files TEXT, -- JSON array of key files found
    cached_at TEXT NOT NULL,
    UNIQUE(session_id)
);
```

**Benefits:**
- Analysis cost: O(1) per session instead of O(n) per PM spawn
- Consistency: All agents see the same stack data
- Auditability: Stack detection logged with timestamp
- Speed: PM starts faster (no filesystem scanning)

### Specialization Block Structure

The skill produces a block that PREPENDS to the developer's task prompt:

```markdown
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a Java Backend API Developer specialized in Spring Boot.**

Your expertise includes:
- JDK 21+ features: records, virtual threads, pattern matching
- Spring Boot 3+: constructor injection, Data JPA, transactions
- RESTful API design: proper status codes, structured errors, pagination

### Patterns to Apply

**Immutable Record Types**
```java
public record OrderLine(String productId, int quantity, BigDecimal unitPrice) {
    public OrderLine {
        if (quantity <= 0) throw new IllegalArgumentException("Quantity must be positive");
    }
}
```

**Null-Safe Operations**
```java
public Optional<Customer> findActiveCustomer(String email) {
    return repository.findByEmail(email).filter(Customer::isActive);
}
```

**Structured Error Responses**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [{"field": "email", "message": "Invalid format"}],
    "request_id": "req_abc123"
  }
}
```

### Patterns to Avoid
- Returning null (use Optional)
- Field injection (use constructor)
- Business logic in controllers
- Raw generic types
- Missing @Transactional on writes

### Verification Checklist
- [ ] JUnit 5 tests with @SpringBootTest
- [ ] OpenAPI documentation generated
- [ ] Proper HTTP status codes
- [ ] Actuator health endpoints enabled

---
```

### Why This Works

1. **Prompt Position**: The specialization block appears at the TOP of the prompt, before the task. This positions it as identity context, not just task guidance.

2. **Identity Override**: "You are a Java Backend API Developer" becomes part of how the agent self-identifies, influencing all decisions.

3. **Skill Separation**: All template reading, selection, and condensing happens in the skill - PM and orchestrator stay lean.

4. **Token Efficient**: Skill condenses multiple templates into ~600-800 tokens.

---

## Version-Aware Adaptation

### The Problem

Templates contain modern patterns that may not work with older project versions:

| Pattern | Requires | Project Has | Problem |
|---------|----------|-------------|---------|
| Java records | Java 14+ | Java 8 | Compilation error |
| Virtual threads | Java 21+ | Java 11 | Feature unavailable |
| React hooks | React 16.8+ | React 16.0 | Runtime error |
| Python match/case | Python 3.10+ | Python 3.8 | Syntax error |
| async/await | Node 8+ | Node 6 | Syntax error |

### Solution: AI-Driven Version Adaptation

Rather than maintaining separate templates per version (maintenance nightmare), the skill uses Claude to **adapt patterns at runtime**.

### Version Detection

PM extracts versions from project files:

```python
# Version extraction patterns
VERSION_SOURCES = {
    "java": [
        ("pom.xml", r"<java.version>(\d+)</java.version>"),
        ("pom.xml", r"<maven.compiler.source>(\d+)</maven.compiler.source>"),
        ("build.gradle", r"sourceCompatibility\s*=\s*['\"]?(\d+)"),
    ],
    "python": [
        ("pyproject.toml", r'requires-python\s*=\s*["\']>=(\d+\.\d+)'),
        ("setup.py", r'python_requires\s*=\s*["\']>=(\d+\.\d+)'),
    ],
    "node": [
        ("package.json", r'"node":\s*"[>=^~]*(\d+)'),
        (".nvmrc", r"^v?(\d+)"),
    ],
    "react": [
        ("package.json", r'"react":\s*"[\^~]?(\d+\.\d+)'),
    ],
    "spring-boot": [
        ("pom.xml", r"<spring-boot.version>(\d+\.\d+)"),
        ("build.gradle", r"springBootVersion\s*=\s*['\"](\d+\.\d+)"),
    ],
}
```

### Adaptation Logic in Skill

The skill includes version constraints in template format and adapts:

**Template Format with Version Constraints:**
```markdown
### Implementation Guidelines

**Immutable Data Types**
<!-- version: java >= 14 -->
```java
public record OrderLine(String productId, int quantity) {}
```

<!-- version: java < 14 -->
```java
public final class OrderLine {
    private final String productId;
    private final int quantity;

    public OrderLine(String productId, int quantity) {
        this.productId = productId;
        this.quantity = quantity;
    }

    // Getters, equals, hashCode, toString...
}
```

**Concurrency Patterns**
<!-- version: java >= 21 -->
```java
// Virtual threads for blocking I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> processOrder(order));
}
```

<!-- version: java >= 8, java < 21 -->
```java
// Thread pool for blocking I/O
ExecutorService executor = Executors.newFixedThreadPool(10);
executor.submit(() -> processOrder(order));
```
```

**Skill Adaptation Process:**

```
Step 3.5: Adapt for Project Version

1. Read detected versions from project_context.json:
   - language_version: "8"
   - framework_version: "2.7"

2. For each code example in template:
   - Check version constraint comment
   - Include only examples matching project version
   - Skip examples requiring newer features

3. If no version-appropriate example exists:
   - Generate adapted version using Claude
   - Prompt: "Adapt this Java 21 pattern for Java 8: [pattern]"
```

### Example: Java 8 Project

**Detected:**
```json
{
  "language": "java",
  "language_version": "8",
  "framework": "spring-boot",
  "framework_version": "2.7"
}
```

**Adapted Output:**
```markdown
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a Java 8 Backend API Developer specialized in Spring Boot 2.7.**

Your expertise includes:
- Java 8 features: lambdas, streams, Optional
- Spring Boot 2.7: constructor injection, Spring Data JPA
- RESTful API design: proper status codes, structured errors

### Patterns to Apply

**Immutable DTOs (Java 8 style)**
```java
public final class CreateUserRequest {
    private final String email;
    private final String displayName;

    public CreateUserRequest(String email, String displayName) {
        this.email = Objects.requireNonNull(email);
        this.displayName = Objects.requireNonNull(displayName);
    }

    public String getEmail() { return email; }
    public String getDisplayName() { return displayName; }
}
```

**Service with Optional (Java 8)**
```java
@Service
public class UserService {
    private final UserRepository userRepository;

    @Autowired  // Constructor injection still works in Spring Boot 2.7
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }
}
```

### Patterns to Avoid (Java 8 context)
- Returning null from methods (use Optional)
- Field injection (use constructor)
- var keyword (Java 10+ only)
- Records (Java 14+ only)
- Pattern matching (Java 16+ only)

### Verification Checklist
- [ ] JUnit 4/5 tests
- [ ] Java 8 compatible bytecode
- [ ] No Java 9+ APIs used
```

### Benefits of AI Adaptation

1. **No Template Explosion**: One template per technology, not per version
2. **Always Current**: New patterns added to template, adaptation handles legacy
3. **Context-Aware**: Claude understands why a pattern exists and can translate intent
4. **Graceful Degradation**: If modern pattern has no equivalent, suggests alternative approach

---

## Skill Implementation

### Directory Structure

```
.claude/skills/specialization-loader/
├── SKILL.md                          # Skill definition
├── scripts/
│   └── load_specializations.py       # Main logic
└── resources/
    └── templates/                    # Specialization templates
        ├── 01-languages/
        │   ├── java.md
        │   ├── python.md
        │   ├── typescript.md
        │   └── ...
        ├── 02-frameworks-frontend/
        │   ├── react.md
        │   ├── nextjs.md
        │   └── ...
        ├── 03-frameworks-backend/
        │   ├── spring-boot.md
        │   ├── fastapi.md
        │   └── ...
        └── ...
```

### SKILL.md

```markdown
---
version: 1.0.0
name: specialization-loader
description: Load technology-specific patterns for agents. Use before spawning developers to enhance their expertise based on project stack.
author: BAZINGA Team
tags: [orchestration, specialization, context]
allowed-tools: [Read, Bash]
---

# Specialization Loader Skill

You are the specialization-loader skill. You generate technology-specific identity and pattern guidance for agents based on detected project technologies.

## When to Invoke This Skill

- Before spawning Developer agents (orchestrator invokes you)
- When project technologies are detected in project_context.json
- Never invoke multiple times for the same spawn

## Your Task

### Step 1: Read Project Context

```bash
cat bazinga/project_context.json | jq '.detected_technologies'
```

Expected format:
```json
{
  "language": "java",
  "framework": "spring-boot",
  "domain": "backend-api"
}
```

### Step 2: Select Templates

Based on detected technologies, select up to 3 templates:
1. **Language** (priority 1) - Always include
2. **Framework** (priority 2) - Include if detected
3. **Domain** (priority 3) - Include if detected

Template paths:
- `.claude/skills/specialization-loader/resources/templates/01-languages/{language}.md`
- `.claude/skills/specialization-loader/resources/templates/0X-*/{framework}.md`
- `.claude/skills/specialization-loader/resources/templates/11-domains/{domain}.md`

### Step 3: Read and Condense Templates

Read each template file. Extract:
- Specialist Profile (first paragraph)
- Implementation Guidelines (code examples - pick top 2)
- Patterns to Avoid (bullet list)
- Verification Checklist

### Step 4: Generate Specialization Block

Combine into a single markdown block (<800 tokens):

```markdown
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a {Language} {Domain} Developer specialized in {Framework}.**

Your expertise includes:
- {Key expertise point 1}
- {Key expertise point 2}
- {Key expertise point 3}

### Patterns to Apply
{Top 2 code examples from templates}

### Patterns to Avoid
{Combined bullet list}

### Verification Checklist
{Combined checklist}

---
```

### Step 5: Return Result

Return the specialization block as your response. The orchestrator will prepend this to the developer spawn prompt.

## Example Output

For `{"language": "java", "framework": "spring-boot", "domain": "backend-api"}`:

```markdown
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a Java Backend API Developer specialized in Spring Boot.**

Your expertise includes:
- JDK 21+ features: records, virtual threads, pattern matching
- Spring Boot 3+: constructor injection, Data JPA, transactions
- RESTful API design: proper status codes, structured errors

### Patterns to Apply
[Code examples here]

### Patterns to Avoid
- Returning null (use Optional)
- Field injection (use constructor)
- Business logic in controllers

### Verification Checklist
- [ ] JUnit 5 tests with @SpringBootTest
- [ ] OpenAPI documentation generated
---
```
```

---

## Workflow Integration

### Updated Orchestrator Flow

```
Step 2B.0: Spawn Developers (Parallel Mode)

BEFORE spawning, invoke specialization-loader skill:

1. Skill(command: "specialization-loader")
2. Receive specialization_block from skill
3. For each developer spawn:
   Task(
     subagent_type: "developer",
     model: "haiku",
     prompt: """
       {specialization_block}

       ## Your Task
       {task_description from PM}

       ## Context Packages Available
       {context packages if any}
     """
   )
```

### What Changes in Existing Files

| File | Change |
|------|--------|
| `agents/orchestrator.md` | Add skill invocation before developer spawns |
| `agents/developer.md` | No changes (identity comes from prompt) |
| `agents/project_manager.md` | Ensure detected_technologies in project_context.json |
| `.claude/skills/` | Add new specialization-loader skill |
| `templates/` | Move specialization templates here |

### What Stays the Same

- PM still analyzes project and detects technologies
- Orchestrator still spawns developers via Task tool
- Developer agent file remains unchanged
- QA/Tech Lead workflow unchanged

---

## Critical Analysis

### Pros ✅

1. **Clean Separation**: Skill handles all template logic, PM/orchestrator stay lean
2. **Dynamic Identity**: "You are a Java developer" feels more natural than embedded guidance
3. **Token Efficient**: One skill call, one condensed block
4. **Maintainable**: Add new templates without changing orchestrator
5. **Testable**: Skill can be tested independently
6. **Reusable**: Same skill works for all agent types
7. **Precedence Clear**: Block explicitly states it's supplementary

### Cons ⚠️

1. **Extra Skill Call**: Adds one skill invocation per spawn cycle
2. **Template Maintenance**: Need to keep 36+ templates updated
3. **Condensation Quality**: Automated condensation may miss context
4. **Complexity**: New moving part in already complex system

### Verdict

The benefits significantly outweigh the costs. The skill-based approach is the right architecture because:
- It keeps PM and orchestrator focused on their core roles
- It makes specialization a first-class feature
- It's extensible (add templates, not code changes)

---

## Implementation Plan

### Phase 1: Create Skill Structure
1. Create `.claude/skills/specialization-loader/` directory
2. Write SKILL.md following skill implementation guide
3. Create `scripts/load_specializations.py`
4. Move templates from `tmp/agent-specializations/` to skill resources

### Phase 2: Integrate with Orchestrator
1. Add skill invocation before developer spawns
2. Modify prompt construction to prepend specialization block
3. Test with Java/Spring Boot project

### Phase 3: Enhance PM Detection
1. Ensure PM writes detected_technologies to project_context.json
2. Add fallback detection patterns if codebase-analysis unavailable

### Phase 4: Validation
1. Run orchestration on test projects (Java, Python, TypeScript)
2. Verify developer output follows specialized patterns
3. Measure token usage impact

---

## Alternative Approaches Considered

### Alternative A: PM Embeds in Task Description

**Rejected because:**
- Bloats PM agent code
- Guidance appears as task instruction, not identity
- PM already has many responsibilities

### Alternative B: Dynamic Agent Files

Create `developer-java-springboot.md` variants.

**Rejected because:**
- Explosion of files (36+ specializations × agent types)
- Maintenance nightmare
- Doesn't compose (can't combine Java + Security)

### Alternative C: Orchestrator Reads Templates Directly

**Rejected because:**
- Orchestrator has tool restrictions (only bazinga/ folder)
- Violates separation of concerns
- Adds template logic to coordinator

---

## Example: Complete Java + Spring Boot + Backend API Flow

### 1. PM Detection Output

```json
// bazinga/project_context.json
{
  "session_id": "bazinga_20251204_100000",
  "detected_technologies": {
    "language": "java",
    "framework": "spring-boot",
    "domain": "backend-api"
  }
}
```

### 2. Orchestrator Invokes Skill

```
Skill(command: "specialization-loader")
```

### 3. Skill Returns Specialization Block

```markdown
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a Java Backend API Developer specialized in Spring Boot.**

Your expertise includes:
- JDK 21+ features: records, virtual threads, pattern matching, sealed classes
- Spring Boot 3+: constructor injection, Data JPA, @Transactional
- RESTful API design: proper HTTP status codes, structured error responses, pagination

### Patterns to Apply

**Immutable Record Types**
```java
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank String displayName
) {}
```

**Service with Optional**
```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {
    private final UserRepository userRepository;

    public Optional<UserDto> findById(UUID id) {
        return userRepository.findById(id).map(this::toDto);
    }

    @Transactional
    public UserDto create(CreateUserRequest request) {
        var user = User.builder()
            .email(request.email())
            .displayName(request.displayName())
            .build();
        return toDto(userRepository.save(user));
    }
}
```

### Patterns to Avoid
- Returning null from methods (use Optional)
- Field injection (use constructor @RequiredArgsConstructor)
- Business logic in controllers (use service layer)
- Missing @Transactional on write operations
- Raw generic types (always parameterize)

### Verification Checklist
- [ ] JUnit 5 tests with @SpringBootTest
- [ ] OpenAPI/Swagger documentation generated
- [ ] Proper HTTP status codes (201 for create, 404 for not found)
- [ ] Actuator health endpoints enabled
- [ ] Database migrations version controlled

---
```

### 4. Orchestrator Spawns Developer

```python
Task(
    subagent_type="developer",
    model="haiku",
    prompt="""
## SPECIALIZATION OVERRIDE

For this session, your identity is enhanced:

**You are a Java Backend API Developer specialized in Spring Boot.**

[... specialization block from skill ...]

---

## Your Task

**Group:** AUTH
**Task:** Implement JWT authentication endpoint

**Requirements:**
- POST /api/v1/auth/login accepts email/password
- Returns JWT access token and refresh token
- Token expiry: 15 minutes for access, 7 days for refresh

**Files to modify:**
- src/main/java/com/example/auth/AuthController.java
- src/main/java/com/example/auth/AuthService.java
- src/main/java/com/example/auth/JwtTokenProvider.java

**Branch:** feature/group-AUTH-jwt-auth
"""
)
```

### 5. Developer Response (Influenced by Specialization)

```markdown
## Implementation Complete

**Summary:** Implemented JWT authentication with Spring Security best practices

**Files Modified:**
- src/main/java/com/example/auth/AuthController.java (created)
- src/main/java/com/example/auth/AuthService.java (created)
- src/main/java/com/example/auth/JwtTokenProvider.java (created)
- src/main/java/com/example/auth/dto/LoginRequest.java (created)
- src/main/java/com/example/auth/dto/AuthResponse.java (created)

**Key Changes:**
- Used record types for DTOs (LoginRequest, AuthResponse) per specialization
- Service uses Optional for null-safety
- Constructor injection via @RequiredArgsConstructor
- @Transactional on write operations
- Structured error responses with proper HTTP status codes

**Code Snippet (following specialization patterns):**
```java
public record LoginRequest(
    @NotBlank @Email String email,
    @NotBlank String password
) {}

public record AuthResponse(
    String accessToken,
    String refreshToken,
    Instant expiresAt
) {}

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {
    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        return ResponseEntity.ok(authService.authenticate(request));
    }
}
```

**Verification Checklist Applied:**
- [x] JUnit 5 tests with @SpringBootTest (12 tests)
- [x] OpenAPI documentation via springdoc-openapi
- [x] Proper HTTP status codes (200 OK, 401 Unauthorized)
- [ ] Actuator endpoints (not in scope for this task)

**Tests:**
- Total: 12
- Passing: 12
- Failing: 0

**Status:** READY_FOR_QA
**Next Step:** Orchestrator, please forward to QA Expert for testing
```

---

## Comparison: Before vs After

### Before (Static Identity)
```
Developer prompt:
"You are a DEVELOPER AGENT - an implementation specialist..."

Task: Implement JWT authentication
```

Developer might use any patterns, may not follow Java/Spring conventions.

### After (Dynamic Identity)
```
Developer prompt:
"## SPECIALIZATION OVERRIDE
You are a Java Backend API Developer specialized in Spring Boot.
[patterns, anti-patterns, checklist]

Task: Implement JWT authentication"
```

Developer follows Java/Spring patterns, uses records, Optional, proper annotations.

---

## References

- `research/skill-implementation-guide.md` - Skill creation standards
- `agents/developer.md` - Current developer agent
- `agents/orchestrator.md` - Current orchestrator workflow
- `tmp/agent-specializations/` - Template library (36 templates)

---

## Multi-LLM Review Integration

**Reviewed:** 2025-12-04 by OpenAI GPT-5

### Consensus Points (Accepted)

1. **Make skill deterministic** - Remove LLM calls from skill. Use rule-based selection with version guards in templates.
2. **Add caching and DB logging** - Cache specialization blocks, include `specialization_id` in spawn prompts for traceability.
3. **Integrate codebase-analysis signals** - Detect existing idioms (Lombok, JUnit version, Swagger) to mirror rather than prescribe patterns.
4. **Enforce placement and token policy** - Core guardrails first, specialization second (≤300-500 tokens), task third.
5. **Add per-group specialization** - Support monorepos where different groups target different stacks.
6. **Provide toggles in skills_config.json** - `enable_specialization_loader`, `mode: advisory|strict`, `allow_new_dependencies`.
7. **Security hardening** - Sanitize template content, wrap with "Advisory Only" disclaimer.
8. **Define failure paths** - Graceful fallback to conservative/no specialization if detection fails.
9. **Keep checklists scoped** - Tag items with "if-present", don't suggest new dependencies.

### Incorporated Changes

#### 1. Deterministic Version Selection (Not AI-Driven)

**Original:** Skill uses Claude to adapt patterns at runtime.

**Revised:** Templates include version-guarded sections. Skill uses regex matching:

```markdown
<!-- version: java >= 14 -->
```java
public record OrderLine(...) {}
```

<!-- version: java < 14 -->
```java
public final class OrderLine { ... }
```
```

Selection is deterministic: parse version guards, emit only matching sections.

#### 2. Codebase Style Detection

Before rendering, skill probes for existing idioms:

```python
STYLE_SIGNALS = {
    "lombok": ("**/*.java", r"import lombok"),
    "junit5": ("**/pom.xml", r"junit-jupiter"),
    "junit4": ("**/pom.xml", r"junit.*4\."),
    "springdoc": ("**/pom.xml", r"springdoc-openapi"),
    "swagger2": ("**/pom.xml", r"springfox-swagger"),
    "field_injection": ("**/*.java", r"@Autowired\s+private"),
    "constructor_injection": ("**/*.java", r"@RequiredArgsConstructor|private final.*@Autowired"),
}
```

Use these to:
- Enable/disable template sections that match existing style
- Suppress suggestions for patterns not present (e.g., don't suggest Lombok if not used)

#### 3. Token Budget and Placement

```markdown
## Prompt Construction Order (MANDATORY)

1. **Core Agent Guardrails** (base developer.md) - FIRST
2. **Specialization Block** (≤500 tokens) - SECOND, prefixed with:
   > **ADVISORY GUIDANCE** - Does not override mandatory workflow/quality gates.
3. **Task Description** (from PM) - THIRD
4. **Context Packages** (if any) - FOURTH
```

#### 4. Per-Group Specialization

```json
// Task group metadata from PM
{
  "group_id": "FRONTEND",
  "target_files": ["src/frontend/**"],
  "detected_stack": {
    "language": "typescript",
    "framework": "react",
    "domain": "frontend-spa"
  }
},
{
  "group_id": "BACKEND",
  "target_files": ["src/api/**"],
  "detected_stack": {
    "language": "java",
    "framework": "spring-boot",
    "domain": "backend-api"
  }
}
```

Orchestrator invokes skill per-group with group-specific stack.

#### 5. Skills Config Integration

```json
// bazinga/skills_config.json
{
  "specialization-loader": {
    "enabled": true,
    "mode": "advisory",
    "allow_new_dependencies": false,
    "max_tokens": 500,
    "cache_ttl_minutes": 60
  }
}
```

#### 6. Advisory Wrapper

All specialization blocks are wrapped:

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates
> - Routing and status requirements
> - Pre-commit quality checks
> - Core agent workflow rules

For this session, your identity is enhanced:
**You are a Java 8 Backend API Developer specialized in Spring Boot 2.7.**
...
```

#### 7. Audit Trail

```python
# Logged to bazinga-db skill_outputs table
{
  "skill": "specialization-loader",
  "specialization_id": "spec_java8_sb27_noLombok_junit4",
  "stack": {"language": "java", "version": "8", "framework": "spring-boot", "framework_version": "2.7"},
  "style_signals": {"lombok": false, "junit5": false, "constructor_injection": true},
  "tokens_used": 487,
  "group_id": "AUTH"
}
```

Referenced in developer spawn and final reports.

### Rejected Suggestions (With Reasoning)

1. **"Extend to QA and Tech Lead"** - Deferred to Phase 2. Developer specialization is the primary use case; QA/TL guidance is shorter and can be added later.

2. **"Validate compatibility proactively with regex"** - Partially accepted. Version guards in templates are sufficient; runtime regex validation adds complexity without proportional benefit.

### Revised Implementation Plan

| Phase | Task | Priority |
|-------|------|----------|
| 1 | Create skill with deterministic selection | High |
| 1 | Add version guards to templates | High |
| 1 | Implement style signal detection | High |
| 2 | Add caching and DB logging | Medium |
| 2 | Per-group specialization support | Medium |
| 3 | Extend to QA/Tech Lead | Low |
| 3 | Add more templates (60+) | Low |

### Confidence Assessment

**Before Review:** Medium (conceptually sound but operational gaps)
**After Integration:** High (deterministic, auditable, graceful fallback, respects existing idioms)

---

## Revised Workflow Example: Java 8 + Spring Boot 2.7

This section demonstrates the complete flow with all integrated feedback applied.

### Scenario

User request: "Add a new /orders endpoint with pagination support"

Project: Java 8, Spring Boot 2.7, uses Lombok, constructor injection, JUnit 5

### Step 1: PM Analyzes and Detects Stack

PM performs codebase analysis and stores detection:

```json
{
  "technologies": {
    "language": "java",
    "framework": "spring-boot",
    "domain": "backend-api"
  },
  "versions": {
    "java": "1.8",
    "spring-boot": "2.7.14",
    "junit": "5"
  },
  "style_signals": {
    "injection_style": "constructor",
    "uses_lombok": true,
    "naming_convention": "camelCase",
    "test_framework": "junit5-mockito",
    "existing_patterns": ["@RestController", "@Service", "ResponseEntity"]
  },
  "task_groups": [
    {
      "id": "G1",
      "description": "Implement OrderController with pagination",
      "stack": ["java", "spring-boot", "backend-api"]
    }
  ]
}
```

### Step 2: PM Returns Task Assignment

```
STATUS: TASK_ASSIGNMENT

MODE: SIMPLE
PARALLELISM: 1

GROUP G1:
  STACK: java@1.8, spring-boot@2.7, backend-api
  STYLE: constructor-injection, lombok, junit5-mockito
  DEVELOPER_COUNT: 1
  TASKS:
    - Create OrderController with GET /orders endpoint
    - Implement pagination using Spring Data Pageable
    - Add OrderService with repository integration
    - Write unit tests for controller and service

READY_FOR_DEVELOPMENT
```

### Step 3: Orchestrator Invokes Skill

```
Skill(command: "specialization-loader")

Context provided:
  agent_type: developer
  stack: [java, spring-boot, backend-api]
  versions:
    java: "1.8"
    spring-boot: "2.7"
  style:
    injection_style: constructor
    uses_lombok: true
    test_framework: junit5-mockito
```

### Step 4: Skill Processes (Deterministically)

The skill:

1. **Loads templates**: `java.md`, `spring-boot.md`, `backend-api.md`

2. **Applies version guards** - For Java 1.8, strips:
   - Records (Java 14+)
   - `var` keyword (Java 10+)
   - Pattern matching (Java 16+)
   - Text blocks (Java 15+)

3. **Applies style signals** - Includes Lombok patterns since `uses_lombok: true`

4. **Constructs identity**: "Java 8 Backend API Developer specialized in Spring Boot 2.7"

### Step 5: Skill Returns Specialization Block (~480 tokens)

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates
> - Routing and status requirements
> - Pre-commit quality checks
> - Core agent workflow rules

For this session, your identity is enhanced:
**You are a Java 8 Backend API Developer specialized in Spring Boot 2.7.**

Your expertise includes:
- Java 8 features: lambdas, streams, Optional, CompletableFuture
- Spring Boot 2.7: constructor injection, Spring Data JPA, Pageable
- RESTful API design: proper status codes, structured error responses
- Testing: JUnit 5, Mockito, @WebMvcTest

### Implementation Patterns (Java 8 + Spring Boot 2.7)

**Controller with Pagination:**
```java
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor  // Lombok - matches project style
public class OrderController {

    private final OrderService orderService;

    @GetMapping
    public ResponseEntity<Page<OrderDto>> getOrders(
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {
        return ResponseEntity.ok(orderService.findAll(pageable));
    }
}
```

**Service Layer:**
```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;

    public Page<OrderDto> findAll(Pageable pageable) {
        return orderRepository.findAll(pageable)
            .map(this::toDto);
    }

    private OrderDto toDto(Order order) {
        return new OrderDto(
            order.getId(),
            order.getCustomerId(),
            order.getTotal(),
            order.getCreatedAt()
        );
    }
}
```

**Unit Test Pattern:**
```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    void getOrders_returnsPagedResults() throws Exception {
        Page<OrderDto> page = new PageImpl<>(List.of(testOrder()));
        when(orderService.findAll(any(Pageable.class))).thenReturn(page);

        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").isArray());
    }
}
```

### Patterns to Avoid
- ❌ `var` keyword (Java 10+ only)
- ❌ Records (Java 14+ only)
- ❌ Text blocks `"""` (Java 15+ only)
- ❌ Pattern matching in instanceof (Java 16+ only)
- ❌ Field injection (@Autowired on fields) - project uses constructor injection
- ❌ Returning null - use Optional<T> for nullable returns

### Codebase Conventions Detected
- ✅ Use Lombok @RequiredArgsConstructor for DI
- ✅ Use ResponseEntity for controller returns
- ✅ Use camelCase for method names
- ✅ Use JUnit 5 + Mockito for tests
```

### Step 6: Orchestrator Spawns Developer

```python
Task(
    subagent_type="developer",
    model="haiku",  # From model_selection.json
    prompt=f"""
{specialization_block}

---

## YOUR ASSIGNMENT

GROUP: G1
TASKS:
- Create OrderController with GET /orders endpoint
- Implement pagination using Spring Data Pageable
- Add OrderService with repository integration
- Write unit tests for controller and service

CONTEXT:
{pm_context}

IMPORTANT: Follow all standard developer workflow rules.
The specialization above is advisory guidance for this specific technology stack.
"""
)
```

### Step 7: Audit Trail Logged

```python
bazinga_db.log_specialization(
    session_id=current_session,
    group_id="G1",
    agent_type="developer",
    specialization_id="java@1.8+spring-boot@2.7+backend-api",
    templates_used=["java.md", "spring-boot.md", "backend-api.md"],
    version_guards_applied=["no-var", "no-records", "no-text-blocks"],
    style_adaptations=["lombok", "constructor-injection"],
    token_count=480
)
```

### Comparison: Before vs After

| Aspect | Before (Static) | After (Dynamic Specialization) |
|--------|-----------------|-------------------------------|
| Agent Identity | "You are a developer" | "You are a Java 8 Backend API Developer specialized in Spring Boot 2.7" |
| Code Examples | Generic or none | Version-appropriate Java 8 + Spring Boot 2.7 patterns |
| Style Guidance | None | Matches project (Lombok, constructor injection) |
| Version Awareness | None | Won't suggest `var`, records, or Java 14+ features |
| Traceability | None | Logged to bazinga-db with specialization_id |
| Token Overhead | 0 | ~480 tokens (within budget) |

### Monorepo Support

For monorepos with multiple stacks:

```
GROUP G1 (Backend):
  STACK: java@17, spring-boot@3.2, backend-api
  → Spawns developer with Java 17 + Spring Boot 3.2 specialization

GROUP G2 (Frontend):
  STACK: typescript@5.3, react@18, nextjs@14
  → Spawns developer with TypeScript + React + Next.js specialization
```

Each developer receives the appropriate specialization for their group's stack.

---

## Documentation Requirements (Create at Implementation Time)

**NOTE:** When implementing this feature, create user-facing documentation and reference it from the README.

### Required Documentation

Create `docs/dynamic-specialization.md` with:

1. **Overview**
   - What is Dynamic Agent Specialization
   - How it enhances developer agents with technology-specific expertise
   - Automatic stack detection and version adaptation

2. **How It Works**
   - Codebase analysis runs once at session start
   - Stack data cached in bazinga-db
   - Specialization templates applied based on detected technologies
   - Version-appropriate patterns (Java 8 vs 21, React 16 vs 18)
   - Style signal detection (Lombok, injection style, test framework)

3. **Advantages**
   - **Context-Aware Code**: Developers generate code matching your actual stack versions
   - **Fewer Errors**: Won't suggest Java 14+ records in a Java 8 project
   - **Consistent Style**: Mirrors your existing codebase conventions
   - **Faster Onboarding**: Agents immediately understand project idioms
   - **Reduced Rework**: Follows patterns already in use, not prescribing new ones
   - **Monorepo Support**: Per-group specialization for different stacks

4. **Configuration**
   - `skills_config.json` settings for specialization-loader
   - Template customization
   - Enabling/disabling specific templates

5. **Template Reference**
   - Available templates (languages, frameworks, domains)
   - Template format and version guards
   - How to add custom templates

### README Update

Add to `README.md` features section:

```markdown
### Dynamic Agent Specialization

BAZINGA automatically detects your project's technology stack and adapts agent behavior:

- **Stack Detection**: Identifies languages, frameworks, and versions from project files
- **Version-Aware Patterns**: Suggests Java 8 patterns for Java 8 projects, Java 21 for Java 21
- **Style Matching**: Detects and follows your existing conventions (Lombok, injection style)
- **Monorepo Support**: Different specializations for different parts of your codebase

See [Dynamic Specialization Guide](docs/dynamic-specialization.md) for details.
```

### Implementation Checklist

- [ ] Create `docs/dynamic-specialization.md`
- [ ] Add feature section to `README.md`
- [ ] Include architecture diagram
- [ ] Add configuration examples
- [ ] Document template customization
