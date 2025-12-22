---
name: technical-writing
type: domain
priority: 3
token_estimate: 500
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Technical Writing Expertise

## Specialist Profile
Technical writing specialist creating clear documentation. Expert in API docs, architecture decision records, and developer-focused content.

---

## Patterns to Follow

### README Structure (2025)
- **One-paragraph pitch**: What it does, why it exists
- **Quick start (copy-paste)**: Working in < 5 commands
- **Badges**: Build status, coverage, version
- **Features list**: ✅ for done, 🚧 for in-progress
- **Architecture overview**: Folder structure diagram
- **Prerequisites clearly stated**: Versions, dependencies
- **Link to detailed docs**: Don't overload README
- **Keep updated per release**: Part of definition of done

### API Documentation
- **Request/response examples**: For every endpoint
- **Error scenarios documented**: All 4xx, 5xx responses
- **Authentication explained**: How to get and use tokens
- **Rate limit documentation**: Limits and headers
- **Versioning visible**: Which version docs apply to
- **Try-it-now capability**: Interactive examples
- **README-style workflows**: Show how operations chain together
<!-- version: openapi >= 3.0 -->
- **OpenAPI 3.0**: Callbacks, links, improved security
<!-- version: openapi >= 3.1 -->
- **OpenAPI 3.1**: Full JSON Schema compatibility, webhooks
<!-- version: openapi >= 3.2 -->
- **OpenAPI 3.2**: Overlay specs, enhanced examples

### Architecture Decision Records (ADR)
- **One decision per ADR**: Keep focused
- **Context section**: Why we faced this decision
- **Decision section**: What we chose
- **Consequences section**: Pros, cons, risks
- **Alternatives considered**: What we rejected and why
- **Status field**: Proposed, Accepted, Deprecated, Superseded
- **Store in version control**: `docs/adrs/` folder
- **Numbered sequentially**: `ADR-001`, `ADR-002`

### Docs-as-Code (2025)
- **Markdown in repo**: Same versioning as code
- **CI/CD for docs**: Auto-build, auto-deploy
- **Treat docs as first-class**: Part of PR requirements
- **Review docs in PRs**: Not separate from code review
- **30-45% faster onboarding**: When docs are maintained
<!-- version: typedoc >= 0.25 -->
- **TypeDoc**: Auto-generate from TypeScript
- **Plugin ecosystem**: Extended rendering options
<!-- version: swagger-ui >= 5.0 -->
- **Swagger UI**: Interactive API documentation
- **Deep linking**: Direct links to operations

### Code Comments
- **Explain why, not what**: Code shows what, comments show why
- **Document non-obvious**: Edge cases, workarounds, gotchas
- **Link to tickets/ADRs**: Reference decisions
- **Keep updated**: Stale comments worse than none
- **JSDoc/TSDoc for public APIs**: Type and description

### Changelog Best Practices
- **Keep a CHANGELOG**: Separate from git log
- **Semantic sections**: Added, Changed, Deprecated, Removed, Fixed, Security
- **User-facing language**: Not commit messages
- **Link to PRs/issues**: Traceability
- **Unreleased section**: Upcoming changes visible

---

## Patterns to Avoid

### README Anti-Patterns
- ❌ **Wall of text**: No one reads it
- ❌ **Outdated setup instructions**: Frustrates developers
- ❌ **No quick start**: Barrier to entry
- ❌ **Missing prerequisites**: Works on my machine

### Documentation Anti-Patterns
- ❌ **Docs separate from code**: Gets out of sync
- ❌ **No examples**: Abstract descriptions only
- ❌ **Jargon without explanation**: Assumes reader knowledge
- ❌ **No update process**: Docs decay rapidly

### API Docs Anti-Patterns
- ❌ **Missing error responses**: Only happy path documented
- ❌ **No authentication examples**: Can't get started
- ❌ **Outdated examples**: Wrong syntax, missing fields
- ❌ **No versioning in docs**: Which version is this?

### ADR Anti-Patterns
- ❌ **Decisions not documented**: Lost tribal knowledge
- ❌ **No alternatives listed**: Looks like no thought given
- ❌ **Never updated**: Status stays "proposed" forever
- ❌ **Too detailed**: ADR becomes implementation spec

---

## Verification Checklist

### README
- [ ] Clear one-paragraph description
- [ ] Copy-paste quick start works
- [ ] Prerequisites listed with versions
- [ ] Build/coverage badges present
- [ ] Links to detailed documentation

### API Documentation
- [ ] All endpoints documented
- [ ] Request/response examples provided
- [ ] Error scenarios included
- [ ] Authentication explained
- [ ] Rate limits documented

### ADRs
- [ ] Major decisions have ADRs
- [ ] Context clearly explains the problem
- [ ] Alternatives are listed
- [ ] Consequences include pros and cons
- [ ] Status is current

### Maintenance
- [ ] Docs reviewed in PRs
- [ ] CHANGELOG maintained
- [ ] Auto-generation configured where applicable
- [ ] Deprecation warnings included

---

## Code Patterns (Reference)

### ADR Structure
- **Header**: `# ADR-001: Use PostgreSQL for Primary Database`
- **Status**: `Accepted | Deprecated | Superseded by ADR-005`
- **Context**: Problem statement, requirements, constraints
- **Decision**: What we will do
- **Consequences**: Positive, Negative, Risks

### OpenAPI Example
- **Path**: `/users/{id}` with `summary`, `description`, `parameters`
- **Responses**: `200`, `400`, `401`, `404`, `500` with schemas
- **Examples**: Named examples under `content.application/json.examples`

### README Structure
```
# Project Name
Brief description.

## Quick Start
\`\`\`bash
commands here
\`\`\`

## Features
- ✅ Feature one
- 🚧 Feature two (in progress)

## Documentation
- [API Reference](./docs/api.md)
- [Architecture](./docs/architecture.md)
```

### CHANGELOG Format
- **Sections**: `## [1.2.0] - 2025-01-15` with `### Added`, `### Fixed`, etc.
- **Entry**: `- Add user authentication endpoint (#123)`

