---
name: research-analysis
type: domain
priority: 3
token_estimate: 500
compatible_with: [requirements_engineer, tech_lead, project_manager]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Research & Requirements Analysis Expertise

## Specialist Profile
Requirements analysis specialist conducting systematic research. Expert in codebase discovery, stakeholder analysis, feasibility assessment, and requirement elicitation.

---

## Patterns to Follow

### Codebase Discovery
- **Project structure mapping**: Understand folder organization
- **Technology stack identification**: Frameworks, languages, versions
- **Architectural pattern recognition**: Layered, DDD, microservices
- **Convention identification**: Naming, file organization, patterns
- **Integration points mapping**: APIs, databases, queues
- **Test strategy understanding**: Unit, integration, E2E patterns

### Requirement Elicitation
- **User story format**: As a [role], I want [capability], so that [benefit]
- **Acceptance criteria**: Given-When-Then (Gherkin) format
- **INVEST criteria**: Independent, Negotiable, Valuable, Estimable, Small, Testable
- **Non-functional requirements**: Performance, security, scalability
- **Constraints documentation**: Technical, business, regulatory
- **Dependency mapping**: What blocks what, external dependencies

### Stakeholder Analysis
- **Identify all stakeholders**: Users, operators, internal teams
- **Interest vs. influence matrix**: High/low quadrants
- **Communication plan**: Who gets what, how often
- **Requirement sources**: Interviews, tickets, analytics
- **Consensus building**: Align conflicting requirements

### Technical Feasibility Assessment
- **Options enumeration**: At least 3 approaches
- **Pros/cons analysis**: For each option
- **Effort estimation**: Rough sizing (T-shirt or sprints)
- **Risk identification**: Technical, schedule, resource
- **Recommendation with rationale**: Why this over others
- **Proof of concept scope**: What to validate early

### Impact Analysis
- **Affected systems**: Which services, databases, APIs
- **Breaking changes**: Backward compatibility concerns
- **Migration requirements**: Data, schema, API versions
- **Rollback strategy**: How to undo if needed
- **Dependency updates**: Downstream consumers affected

### Documentation Standards
- **Requirements template**: Consistent format
- **Traceability matrix**: Requirements → implementation → tests
- **Versioning**: Track requirement changes
- **Approval workflow**: Who signs off
- **Living documentation**: Update as understanding evolves

---

## Patterns to Avoid

### Research Anti-Patterns
- ❌ **Assumptions without validation**: Ask, don't assume
- ❌ **Single source of truth**: Triangulate with multiple sources
- ❌ **Surface-level analysis**: Dig into code, not just docs
- ❌ **Ignoring legacy constraints**: Existing code limits options

### Requirements Anti-Patterns
- ❌ **Missing acceptance criteria**: How do we know it's done?
- ❌ **Vague user stories**: "Improve performance"
- ❌ **No non-functional requirements**: Only happy path
- ❌ **Gold plating**: Adding unrequested features
- ❌ **Solution in requirement**: Describe need, not implementation

### Stakeholder Anti-Patterns
- ❌ **Missing stakeholders**: Discover late, rework later
- ❌ **No prioritization**: Everything is P0
- ❌ **Ignoring dissent**: Minority concerns matter
- ❌ **Scope creep**: Requirements grow without control

### Feasibility Anti-Patterns
- ❌ **Single option considered**: No alternatives
- ❌ **Premature commitment**: Decide before research
- ❌ **Ignoring constraints**: Technical debt, team skills
- ❌ **No risk assessment**: Optimism bias

---

## Verification Checklist

### Codebase Analysis
- [ ] Project structure documented
- [ ] Technology stack identified
- [ ] Conventions catalogued
- [ ] Integration points mapped
- [ ] Existing patterns noted

### Requirements
- [ ] User stories complete (who, what, why)
- [ ] Acceptance criteria defined (Given-When-Then)
- [ ] Non-functional requirements captured
- [ ] Dependencies identified
- [ ] Constraints documented

### Stakeholders
- [ ] All stakeholders identified
- [ ] Interest/influence assessed
- [ ] Communication plan created
- [ ] Conflicts surfaced and resolved

### Feasibility
- [ ] Multiple options analyzed
- [ ] Pros/cons documented
- [ ] Effort estimated
- [ ] Risks identified with mitigations
- [ ] Recommendation justified

---

## Code Patterns (Reference)

### Codebase Report Structure
```
## Project Structure
src/
├── api/        # HTTP handlers
├── services/   # Business logic
├── repositories/ # Data access
└── types/      # Type definitions

## Technology Stack
| Layer | Tech | Version |
|-------|------|---------|
| Runtime | Node.js | 20.x |
| Framework | Express | 4.18 |

## Conventions
- File naming: kebab-case
- Test files: *.test.ts co-located
```

### Requirement Template
```
## REQ-001: [Title]
**User Story**: As a [role], I want [capability], so that [benefit]

**Acceptance Criteria**:
- Given [context], When [action], Then [result]

**Non-Functional**:
- Performance: < 200ms response
- Security: Authenticated users only

**Dependencies**: REQ-002, external-api
**Priority**: P1
**Estimation**: 5 story points
```

### Feasibility Template
```
## Option A: [Name]
**Pros**: Faster, team expertise
**Cons**: More expensive, vendor lock-in
**Effort**: 3 sprints
**Risks**: API deprecation

## Recommendation
Option A because [rationale]
```

### Stakeholder Matrix
```
| Stakeholder | Interest | Influence | Communication |
|-------------|----------|-----------|---------------|
| End Users | High | Low | Release notes |
| Dev Team | High | High | Daily standups |
| Security | Medium | High | Review meetings |
```

