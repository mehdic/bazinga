---
name: project-management
type: domain
priority: 3
token_estimate: 450
compatible_with: [project_manager]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Project Management Expertise

## Specialist Profile
Project management specialist coordinating software delivery. Expert in task breakdown, estimation, risk assessment, and delivery planning.

## Implementation Guidelines

### Task Decomposition

```markdown
## Feature: User Authentication System

### Epic Breakdown
1. **User Registration** (13 pts)
   - Email validation endpoint (2 pts)
   - Registration form + API (3 pts)
   - Email verification flow (5 pts)
   - Welcome email integration (3 pts)

2. **Login/Logout** (8 pts)
   - Login endpoint with JWT (3 pts)
   - Session management (3 pts)
   - Logout + token invalidation (2 pts)

3. **Password Management** (8 pts)
   - Forgot password flow (3 pts)
   - Password reset with token (3 pts)
   - Password strength validation (2 pts)

### Dependency Graph
```
Registration ──► Email Verification ──► Login
                                         │
Password Reset ◄─────────────────────────┘
```

### Critical Path
Registration → Email Verification → Login (must complete in sequence)
Password Management can be parallelized after Login.
```

### Estimation Framework

```markdown
## Estimation Guidelines

### Story Point Reference
| Points | Complexity | Example |
|--------|------------|---------|
| 1 | Trivial | Config change, copy update |
| 2 | Simple | Basic CRUD endpoint |
| 3 | Medium | Endpoint with validation + tests |
| 5 | Complex | Feature with external integration |
| 8 | Very Complex | Multi-service coordination |
| 13 | Epic-sized | Should be broken down |

### T-Shirt Sizing → Points Mapping
| Size | Points | Time (1 dev) |
|------|--------|--------------|
| XS | 1-2 | < 1 day |
| S | 3 | 1-2 days |
| M | 5 | 3-4 days |
| L | 8 | ~1 week |
| XL | 13+ | Break down further |

### Confidence Levels
- High (±10%): Well-understood, similar past work
- Medium (±25%): Some unknowns, new patterns
- Low (±50%): Significant unknowns, new tech
```

### Risk Assessment

```markdown
## Risk Register: Authentication Feature

| ID | Risk | Probability | Impact | Score | Mitigation | Owner |
|----|------|-------------|--------|-------|------------|-------|
| R1 | OAuth provider downtime | Low | High | 6 | Fallback to email auth | Dev Lead |
| R2 | Security vulnerabilities | Medium | Critical | 12 | Security review before launch | Security |
| R3 | Performance under load | Medium | High | 9 | Load test with 10x expected | QA |
| R4 | Scope creep | High | Medium | 9 | Strict change control | PM |

### Risk Scoring
- Probability: Low (1), Medium (2), High (3)
- Impact: Low (1), Medium (2), High (3), Critical (4)
- Score = Probability × Impact
- Action threshold: Score ≥ 6

### Contingency Plans
**R2 - Security vulnerabilities:**
- Trigger: Any P1 security finding
- Action: Delay release, hotfix + re-review
- Budget: 2 days contingency allocated
```

### Sprint Planning

```markdown
## Sprint 23 Plan

### Capacity
| Developer | Availability | Capacity (pts) |
|-----------|--------------|----------------|
| Dev A | 100% | 10 |
| Dev B | 80% (PTO Fri) | 8 |
| Dev C | 100% | 10 |
| **Total** | | **28 pts** |

### Committed Work
| Story | Points | Assignee | Dependencies |
|-------|--------|----------|--------------|
| AUTH-101: Registration API | 3 | Dev A | None |
| AUTH-102: Email verification | 5 | Dev A | AUTH-101 |
| AUTH-103: Login endpoint | 3 | Dev B | None |
| AUTH-104: Session management | 3 | Dev B | AUTH-103 |
| AUTH-105: Password reset | 5 | Dev C | AUTH-103 |
| BUG-42: Fix timeout issue | 2 | Dev C | None |
| TECH-15: Update deps | 2 | Dev A | None |
| **Total** | **23 pts** | | |

### Buffer
- Committed: 23 pts (82% of capacity)
- Buffer: 5 pts for unknowns/bugs
- Stretch goal: AUTH-106 (3 pts) if ahead

### Sprint Goals
1. ✅ Complete registration + verification flow
2. ✅ Basic login functionality working
3. ✅ Password reset initiated
```

### Status Reporting

```markdown
## Weekly Status Report - Week 12

### Summary
🟢 On Track | Sprint 23 | Day 7/10

### Progress
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Velocity | 25 pts | 18 pts | 🟡 |
| Stories Done | 5 | 3 | 🟡 |
| Bugs Open | <5 | 3 | 🟢 |
| Blockers | 0 | 1 | 🔴 |

### Completed This Week
- ✅ AUTH-101: Registration API (3 pts)
- ✅ AUTH-103: Login endpoint (3 pts)
- ✅ BUG-42: Timeout fix (2 pts)

### In Progress
- 🔄 AUTH-102: Email verification (60%)
- 🔄 AUTH-104: Session management (40%)

### Blockers
1. **SendGrid API access** - Waiting on vendor approval
   - Impact: Blocks email verification
   - ETA: Expecting credentials by Wed
   - Mitigation: Mock email service for testing

### Risks
- 🟡 May not complete AUTH-105 this sprint
- Action: Deprioritize if blocked, carry to Sprint 24

### Next Week
- Complete email verification
- Start password reset flow
- Begin QA testing
```

## Patterns to Avoid
- ❌ Estimating without team input
- ❌ 100% capacity planning
- ❌ Ignoring dependencies
- ❌ Scope changes without impact analysis

## Verification Checklist
- [ ] Tasks broken to ≤5 points
- [ ] Dependencies identified
- [ ] Risks assessed with mitigations
- [ ] 15-20% buffer in sprint
- [ ] Clear acceptance criteria
