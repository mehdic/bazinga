---
name: research-analysis
type: domain
priority: 3
token_estimate: 450
compatible_with: [requirements_engineer, tech_lead, project_manager]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Research & Requirements Analysis Expertise

## Specialist Profile
Requirements analysis specialist conducting systematic research. Expert in stakeholder analysis, requirement elicitation, and technical feasibility assessment.

## Implementation Guidelines

### Codebase Discovery

```markdown
## Codebase Analysis Report

### 1. Project Structure
```
src/
├── api/           # HTTP handlers (Express/Fastify)
├── services/      # Business logic layer
├── repositories/  # Data access layer
├── models/        # Domain entities
├── utils/         # Shared utilities
└── types/         # TypeScript definitions
```

### 2. Technology Stack
| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Runtime | Node.js | 20.x | LTS |
| Framework | Express | 4.18 | REST API |
| Database | PostgreSQL | 16 | Primary store |
| ORM | Prisma | 5.x | Type-safe queries |
| Cache | Redis | 7.x | Sessions, caching |
| Testing | Jest | 29.x | Unit + integration |

### 3. Architectural Patterns
- **Layered Architecture**: Controllers → Services → Repositories
- **Dependency Injection**: Constructor injection pattern
- **Repository Pattern**: Abstract data access
- **DTO Pattern**: Request/Response objects

### 4. Existing Conventions
- File naming: kebab-case (user-service.ts)
- Class naming: PascalCase (UserService)
- Function naming: camelCase (createUser)
- Test files: *.test.ts co-located with source

### 5. Integration Points
- Authentication: JWT with refresh tokens
- External APIs: Payment gateway (Stripe)
- Message Queue: Not currently used
- Monitoring: Prometheus metrics endpoint
```

### Requirements Template

```markdown
## Requirement: REQ-USER-001
**Title:** User Registration with Email Verification

### Description
As a new user, I want to register with my email and verify my account
so that I can securely access the system.

### Acceptance Criteria
1. User can submit registration form with:
   - Email (required, valid format, unique)
   - Password (min 12 chars, complexity requirements)
   - Display name (2-100 characters)

2. System sends verification email within 30 seconds
3. Verification link expires after 24 hours
4. User cannot login until email is verified
5. User can request new verification email (rate limited)

### Technical Constraints
- Must integrate with existing auth service
- Email provider: SendGrid (already configured)
- Token storage: Redis with 24h TTL

### Dependencies
- REQ-AUTH-001: Authentication system (complete)
- REQ-EMAIL-001: Email service integration (complete)

### Non-Functional Requirements
- Response time: < 200ms for registration
- Email delivery: 99% within 30 seconds
- Rate limit: 3 registration attempts per IP per hour

### Priority
P1 - Required for MVP

### Estimation
Story points: 8
```

### Technical Feasibility Assessment

```markdown
## Feasibility Analysis: Real-time Notifications

### 1. Requirement Summary
Implement real-time notifications for user events (messages, orders, alerts).

### 2. Technical Options

#### Option A: WebSockets (Socket.io)
**Pros:**
- Bi-directional communication
- Wide browser support
- Existing team expertise

**Cons:**
- Connection management complexity
- Scaling requires sticky sessions or Redis adapter

**Effort:** Medium (2-3 sprints)

#### Option B: Server-Sent Events (SSE)
**Pros:**
- Simpler implementation
- Native browser support
- Easier to scale (stateless)

**Cons:**
- Uni-directional only
- Limited concurrent connections in some browsers

**Effort:** Low (1-2 sprints)

#### Option C: Polling
**Pros:**
- Simplest implementation
- No infrastructure changes

**Cons:**
- Higher latency
- Increased server load
- Not truly real-time

**Effort:** Low (1 sprint)

### 3. Recommendation
**Option A: WebSockets with Socket.io**

Rationale:
- Bi-directional needed for read receipts
- Team has prior experience
- Redis adapter handles scaling

### 4. Implementation Approach
1. Add Socket.io server alongside Express
2. Implement Redis adapter for multi-node
3. Create event emitter service
4. Add client SDK wrapper
5. Implement reconnection handling

### 5. Risks & Mitigations
| Risk | Probability | Mitigation |
|------|-------------|------------|
| Connection drops | Medium | Auto-reconnect + offline queue |
| Memory leaks | Low | Connection timeout + monitoring |
| Scale issues | Low | Load test before launch |
```

### Stakeholder Analysis

```markdown
## Stakeholder Map: User Management Feature

### Primary Stakeholders
| Stakeholder | Role | Interest | Influence | Needs |
|-------------|------|----------|-----------|-------|
| End Users | Consumer | High | Low | Easy registration, privacy |
| Admin Users | Operator | High | Medium | User management tools |
| Support Team | Internal | High | Medium | User lookup, audit logs |
| Security Team | Internal | Medium | High | Compliance, audit trail |

### Communication Plan
| Stakeholder | Frequency | Method | Content |
|-------------|-----------|--------|---------|
| End Users | Release | Changelog | New features |
| Admin Users | Weekly | Slack | Progress updates |
| Security Team | Milestone | Review meeting | Security assessment |

### Requirement Sources
- User interviews: 10 conducted
- Support tickets: Top 5 pain points analyzed
- Analytics: User drop-off points identified
- Competitor analysis: Feature comparison done
```

## Patterns to Avoid
- ❌ Assumptions without validation
- ❌ Missing non-functional requirements
- ❌ No stakeholder alignment
- ❌ Skipping feasibility analysis

## Verification Checklist
- [ ] Codebase analyzed
- [ ] Stakeholders identified
- [ ] Requirements documented
- [ ] Feasibility assessed
- [ ] Dependencies mapped
