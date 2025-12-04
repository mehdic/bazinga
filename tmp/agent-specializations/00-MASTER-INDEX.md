# Agent Specialization Templates - Master Index

**Purpose:** Templates for dynamic agent specialization based on detected project stack.

**Usage:** The `specialization-loader` skill selects templates based on:
1. Detected language (priority 1)
2. Detected framework (priority 2)
3. Detected domain (priority 3)

Templates are combined and version-filtered before injection into agent prompts.

---

## Template Categories

### 01-languages/
| Template | Token Est. | Description |
|----------|------------|-------------|
| java.md | ~600 | Java 8-21 patterns with version guards |
| python.md | ~500 | Python 3.8+ patterns |
| typescript.md | ~500 | TypeScript 4.x/5.x patterns |
| go.md | ~400 | Go 1.18+ patterns |
| rust.md | ~450 | Rust patterns and ownership |
| csharp.md | ~500 | C# 8-12 patterns |
| ruby.md | ~400 | Ruby 3.x patterns |
| php.md | ~400 | PHP 8.x patterns |
| kotlin.md | ~450 | Kotlin patterns |
| swift.md | ~400 | Swift 5.x patterns |

### 02-frameworks-frontend/
| Template | Token Est. | Description |
|----------|------------|-------------|
| react.md | ~500 | React 16-18 patterns with hooks |
| vue.md | ~450 | Vue 2/3 patterns |
| nextjs.md | ~500 | Next.js 12-14 patterns |
| angular.md | ~450 | Angular patterns |
| svelte.md | ~400 | Svelte patterns |

### 03-frameworks-backend/
| Template | Token Est. | Description |
|----------|------------|-------------|
| spring-boot.md | ~600 | Spring Boot 2.x/3.x patterns |
| fastapi.md | ~450 | FastAPI patterns |
| django.md | ~450 | Django patterns |
| express.md | ~400 | Express.js patterns |
| rails.md | ~450 | Rails patterns |
| nestjs.md | ~450 | NestJS patterns |

### 11-domains/
| Template | Token Est. | Description |
|----------|------------|-------------|
| backend-api.md | ~400 | REST/GraphQL API patterns |
| microservices.md | ~450 | Microservices patterns |
| security-focused.md | ~400 | Security-first patterns |

---

## Version Guard Syntax

Templates use HTML comments for version guards:

```markdown
<!-- version: java >= 14 -->
```java
public record User(String name, String email) {}
```

<!-- version: java < 14 -->
```java
public final class User {
    private final String name;
    private final String email;
    // Constructor, getters, equals, hashCode...
}
```
```

The specialization-loader skill parses these guards and includes only version-appropriate sections.

---

## Style Signal Syntax

Templates can be conditionally included based on detected style:

```markdown
<!-- style: uses_lombok -->
@RequiredArgsConstructor
public class UserService {
    private final UserRepository repository;
}

<!-- style: !uses_lombok -->
public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

---

## Template Combination Rules

1. **Max 3 templates** combined per specialization
2. **Token budget**: ≤500 tokens total
3. **Priority order**: Language > Framework > Domain
4. **Deduplication**: Overlapping patterns merged

**Example combinations:**
- Java + Spring Boot + Backend API → Java backend developer
- TypeScript + React + (none) → React frontend developer
- Python + FastAPI + Backend API → FastAPI backend developer
