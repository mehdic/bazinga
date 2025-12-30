# BAZINGA Technology Specializations

BAZINGA includes **72 technology-specific specialization templates** that enhance agent expertise based on your project's tech stack. This document explains how specializations work and what's available.

---

## Overview

### What Are Specializations?

Specializations are markdown templates containing technology-specific:
- Best practices and patterns
- Common pitfalls to avoid
- Version-specific guidance
- Testing strategies
- Security considerations

When an agent is spawned, the `specialization-loader` skill:
1. Reads your project's detected tech stack from `bazinga/project_context.json`
2. Loads relevant specialization templates
3. Applies version guards (e.g., Python 3.11 patterns vs 2.7)
4. Composes an identity block within token budget
5. Injects the composed expertise into the agent prompt

### How Tech Stack Detection Works

Before the Project Manager starts, the **Tech Stack Scout** agent:
1. Analyzes your project files (package.json, pyproject.toml, go.mod, etc.)
2. Detects frameworks, languages, databases, and tools
3. Identifies versions where possible
4. Saves results to `bazinga/project_context.json`

Example output:
```json
{
  "primary_language": "python",
  "primary_language_version": "3.11",
  "frameworks": ["fastapi", "sqlalchemy"],
  "databases": ["postgresql"],
  "testing": ["pytest"],
  "infrastructure": ["docker"]
}
```

---

## Available Specializations

### Categories

| Category | Templates | Examples |
|----------|-----------|----------|
| **01-languages** | 8 | Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP |
| **02-frameworks-frontend** | 8 | React, Vue, Angular, Svelte, Next.js, Nuxt, Astro, HTMX |
| **03-frameworks-backend** | 8 | FastAPI, Express, Django, Rails, Spring Boot, ASP.NET, Phoenix, Gin |
| **04-mobile-desktop** | 6 | React Native, Flutter, Swift, Kotlin, Electron, Tauri |
| **05-databases** | 8 | PostgreSQL, MySQL, MongoDB, Redis, SQLite, DynamoDB, Elasticsearch, Neo4j |
| **06-infrastructure** | 8 | Docker, Kubernetes, Terraform, AWS, GCP, Azure, Nginx, Caddy |
| **07-messaging-apis** | 6 | GraphQL, gRPC, REST, Kafka, RabbitMQ, WebSocket |
| **08-testing** | 6 | pytest, Jest, Vitest, Playwright, Cypress, k6 |
| **09-data-ai** | 6 | Pandas, NumPy, PyTorch, TensorFlow, LangChain, Hugging Face |
| **10-security** | 4 | OWASP, OAuth2/OIDC, Cryptography, Security Headers |
| **11-domains** | 4 | E-commerce, Fintech, Healthcare, Real-time |

**Total:** 72 specialization templates

---

## Template Structure

Each specialization template follows this structure:

```markdown
---
name: Technology Name
version: 1.0.0
applicable_to: [developer, qa_expert, tech_lead]
priority: 100
---

# Technology Name Specialization

## Identity Enhancement
[How this changes the agent's expertise]

## Best Practices
[Technology-specific patterns]

## Common Pitfalls
[What to avoid]

## Version-Specific Guidance
<!-- @version-guard: python >= 3.10 -->
[Content only included for Python 3.10+]
<!-- @end-version-guard -->

## Testing Strategy
[How to test with this technology]

## Security Considerations
[Security-specific guidance]
```

### Version Guards

Templates can include version-specific content using guards:

```markdown
<!-- @version-guard: node >= 18 -->
Use native fetch() instead of node-fetch package.
<!-- @end-version-guard -->

<!-- @version-guard: node < 18 -->
Install node-fetch for HTTP requests.
<!-- @end-version-guard -->
```

The `specialization-loader` skill evaluates these guards against your project's detected versions and only includes matching content.

---

## How Agents Use Specializations

### Developer Agent

Receives specializations for:
- Primary programming language
- Frameworks in use
- Database technologies
- Testing tools

Example composed identity for a FastAPI + PostgreSQL project:
```
You are a Developer specialized in:
- Python 3.11 (async/await patterns, type hints, dataclasses)
- FastAPI (dependency injection, Pydantic models, async routes)
- PostgreSQL (connection pooling, prepared statements, JSONB)
- pytest (fixtures, async testing, parameterization)
```

### QA Expert Agent

Receives specializations for:
- Testing frameworks
- Language-specific testing patterns
- Database testing strategies

Plus auto-augmentation with QA-specific templates.

### Tech Lead Agent

Receives specializations for:
- Security practices for the stack
- Architectural patterns
- Code review focus areas

Plus auto-augmentation with review-specific templates.

---

## Token Budget

Specializations are composed within per-model token budgets:

| Model | Token Budget | Typical Use |
|-------|--------------|-------------|
| Haiku | 900 tokens | Developer (simple tasks) |
| Sonnet | 1,800 tokens | QA Expert, Tech Lead |
| Opus | 2,400 tokens | PM, SSE, Investigator |

If multiple specializations apply, the loader:
1. Prioritizes by relevance score
2. Includes highest-priority templates first
3. Truncates lower-priority content to fit budget

---

## Customization

### Adding Project-Specific Specializations

Create a file in `bazinga/templates/specializations/` with the standard structure:

```markdown
---
name: My Custom Framework
version: 1.0.0
applicable_to: [developer]
priority: 150
---

# My Custom Framework Specialization

[Your custom guidance...]
```

Higher priority values (150 vs 100) ensure your custom templates are included first.

### Disabling Specializations

To run agents without specializations (not recommended):

1. Delete or rename `bazinga/project_context.json`
2. The specialization-loader will have no context to load

---

## Master Index

The complete list of specializations is available at:
`templates/specializations/00-MASTER-INDEX.md`

This file contains:
- All template paths
- Guard token definitions
- Category organization
- Version mapping

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Agent workflow details
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Project structure
- `.claude/skills/specialization-loader/SKILL.md` - Loader skill documentation
- `.claude/skills/prompt-builder/SKILL.md` - Prompt composition details

---

**Version:** 1.1.0
**Last Updated:** 2025-12-30
