---
name: agile-scrum
type: domain
priority: 3
token_estimate: 400
compatible_with: [project_manager, tech_lead]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Agile/Scrum Methodology Expertise

## Specialist Profile
Agile specialist facilitating iterative delivery. Expert in Scrum ceremonies, backlog management, and continuous improvement.

## Implementation Guidelines

### User Story Format

```markdown
## Story: USER-123

### Title
As a [user], I want [capability] so that [benefit]

### Example
As a **registered user**, I want to **reset my password via email**
so that I can **regain access to my account if I forget my credentials**.

### Acceptance Criteria (Given-When-Then)
```gherkin
Scenario: Request password reset
  Given I am on the login page
  When I click "Forgot Password"
  And I enter my registered email
  Then I should see "Reset link sent"
  And I should receive an email within 5 minutes

Scenario: Reset with valid token
  Given I have a valid reset token
  When I click the reset link
  And I enter a new password meeting requirements
  Then my password should be updated
  And I should be redirected to login

Scenario: Reset with expired token
  Given I have an expired reset token (>24h old)
  When I click the reset link
  Then I should see "Link expired"
  And I should be prompted to request a new link
```

### Definition of Done
- [ ] Code complete with unit tests (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] QA sign-off
- [ ] No P1/P2 bugs
```

### Backlog Refinement

```markdown
## Refinement Session Agenda

### 1. Review Upcoming Stories (30 min)
| Story | Status | Action |
|-------|--------|--------|
| USER-124 | Ready | Estimate |
| USER-125 | Needs AC | Add criteria |
| USER-126 | Too large | Split |

### 2. Story Splitting Patterns

**Original (too large):**
> As a user, I want to manage my profile

**Split by workflow:**
1. View profile information
2. Edit basic info (name, avatar)
3. Change email (with verification)
4. Delete account

**Split by data:**
1. Manage personal info
2. Manage notification preferences
3. Manage privacy settings

**Split by operation (CRUD):**
1. Create profile (during registration)
2. Read profile (view page)
3. Update profile (edit page)
4. Delete profile (account deletion)

### 3. Estimation (Planning Poker)
| Story | Dev A | Dev B | Dev C | Final |
|-------|-------|-------|-------|-------|
| USER-124 | 3 | 5 | 3 | 3 |
| USER-125 | 5 | 5 | 8 | 5 |
| USER-126a | 2 | 3 | 2 | 2 |
```

### Sprint Ceremonies

```markdown
## Ceremony Guide

### Daily Standup (15 min)
**Format:** Each person answers:
1. What did I complete yesterday?
2. What will I work on today?
3. Any blockers?

**Anti-patterns to avoid:**
- Status report to PM (should be peer-to-peer)
- Problem-solving (take offline)
- Going over 15 minutes

### Sprint Planning (2-4 hours)
**Part 1: What (1-2h)**
- Review sprint goal
- Select stories from backlog
- Clarify acceptance criteria

**Part 2: How (1-2h)**
- Break stories into tasks
- Identify dependencies
- Assign initial owners

**Output:** Sprint backlog with committed stories

### Sprint Review (1-2 hours)
**Agenda:**
1. Demo completed features (team)
2. Stakeholder feedback
3. Backlog updates based on feedback
4. Release discussion

### Sprint Retrospective (1-1.5 hours)
**Format Options:**

**Start-Stop-Continue:**
| Start | Stop | Continue |
|-------|------|----------|
| Pair programming | Long meetings | Daily standups |
| Earlier testing | Scope creep | Code reviews |

**4Ls (Liked, Learned, Lacked, Longed for):**
- Liked: Team collaboration
- Learned: New testing approach
- Lacked: Clear requirements
- Longed for: More automation

**Action Items:**
| Action | Owner | Due |
|--------|-------|-----|
| Set up pair programming rotation | Dev Lead | Next sprint |
| Timebox meetings to 1h | PM | Immediately |
```

### Velocity Tracking

```markdown
## Velocity Chart

| Sprint | Committed | Completed | Carry-over |
|--------|-----------|-----------|------------|
| S20 | 25 | 22 | 3 |
| S21 | 24 | 24 | 0 |
| S22 | 26 | 20 | 6 |
| S23 | 23 | 21 | 2 |
| **Avg** | **24.5** | **21.75** | |

### Observations
- Velocity trending: Stable (~22 pts)
- S22 drop: 2 devs sick, 1 blocker
- Recommendation: Plan for 20-22 pts

### Burndown Analysis
Sprint 23:
- Day 1: 23 pts remaining
- Day 5: 15 pts (on track)
- Day 8: 8 pts (slightly behind)
- Day 10: 2 pts (carry-over)

Issue: Late-sprint scope addition (+3 pts)
Action: Enforce change control
```

## Patterns to Avoid
- ❌ Skipping retrospectives
- ❌ Changing scope mid-sprint
- ❌ Treating estimates as commitments
- ❌ PM assigning tasks (team self-organizes)

## Verification Checklist
- [ ] Stories have clear acceptance criteria
- [ ] Sprint goal defined
- [ ] Velocity-based planning
- [ ] Regular retrospectives
- [ ] Definition of Done enforced
