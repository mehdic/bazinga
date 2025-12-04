---
name: agile-scrum
type: domain
priority: 3
token_estimate: 500
compatible_with: [project_manager, tech_lead]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Agile/Scrum Methodology Expertise

## Specialist Profile
Agile specialist facilitating iterative delivery. Expert in Scrum ceremonies, backlog management, velocity tracking, and continuous improvement.

---

## Patterns to Follow

### User Story Best Practices
- **Standard format**: As a [role], I want [capability], so that [benefit]
- **INVEST criteria**: Independent, Negotiable, Valuable, Estimable, Small, Testable
- **Acceptance criteria in Gherkin**: Given-When-Then format
- **Definition of Done**: Checklist that applies to all stories
- **Story ≤ 5 points**: Larger stories need splitting
- **Vertical slicing**: End-to-end functionality, not horizontal layers

### Story Splitting Patterns
- **By workflow step**: Registration → Verification → Login
- **By data variation**: Personal info, Preferences, Privacy settings
- **By CRUD operation**: Create, Read, Update, Delete
- **By business rule**: Basic case, Edge case, Error handling
- **By platform**: Web, Mobile, API
- **Spike first**: Research before implementation

### Backlog Refinement
- **Regular cadence**: Weekly, 1-2 hours
- **2 sprints ahead**: Keep backlog ready
- **Team estimates together**: Planning poker
- **Clarify acceptance criteria**: Remove ambiguity
- **Split large stories**: Before sprint planning
- **Prioritize ruthlessly**: Top items are detailed, bottom items rough

### Sprint Ceremonies
- **Planning (2-4 hours)**: What (select stories) + How (break into tasks)
- **Daily standup (15 min)**: Yesterday, Today, Blockers (peer-to-peer, not status report)
- **Review (1-2 hours)**: Demo to stakeholders, get feedback
- **Retrospective (1-1.5 hours)**: What worked, what didn't, actions

### Velocity Management (2025)
- **3-5 sprints to baseline**: New teams need time
- **Only count done work**: 90% complete = 0 points
- **Don't compare across teams**: Points aren't standardized
- **Track trends, not absolutes**: Consistency matters more
- **Use for planning, not performance**: Velocity ≠ productivity
- **WIP limits**: Finish before starting new work

### Retrospective Formats
- **Start-Stop-Continue**: Three columns for actions
- **4Ls**: Liked, Learned, Lacked, Longed for
- **Sailboat**: Wind (helps), Anchor (hinders), Rocks (risks)
- **Mad-Sad-Glad**: Emotional temperature check
- **Action items**: Max 2-3 per retro, assign owners

### Definition of Done
- **Code complete with tests**: Coverage threshold met
- **Code reviewed and approved**: At least one reviewer
- **CI/CD passed**: Build, lint, tests green
- **Documentation updated**: API docs, README if needed
- **Deployed to staging**: Verified in environment
- **No P1/P2 bugs**: Quality gate
<!-- version: jira >= 9.0 -->
- **Jira Automation**: Auto-transition on PR merge
- **DevOps insights**: Deployment frequency tracking
<!-- version: linear >= 2023 -->
- **Linear Cycles**: Built-in sprint-like iterations
- **Triage queue**: Automated issue prioritization

---

## Patterns to Avoid

### Story Anti-Patterns
- ❌ **Technical tasks as stories**: Stories deliver user value
- ❌ **Horizontal slicing**: "Build database layer" as a story
- ❌ **Missing "so that"**: Benefit explains why it matters
- ❌ **Implementation in story**: Describe need, not solution
- ❌ **Stories without criteria**: Can't verify done

### Ceremony Anti-Patterns
- ❌ **Skipping retrospectives**: No improvement
- ❌ **Status reports at standup**: Should be peer coordination
- ❌ **Demo with bugs**: Review working software only
- ❌ **Planning without team**: Estimates need doers

### Sprint Anti-Patterns
- ❌ **Mid-sprint scope changes**: Protect commitment
- ❌ **Carrying over constantly**: Stories too big
- ❌ **No sprint goal**: Just a task list
- ❌ **Velocity as KPI**: Creates gaming behavior

### Estimation Anti-Patterns
- ❌ **Treating estimates as deadlines**: They're approximations
- ❌ **PM assigns points**: Team estimates together
- ❌ **Normalizing points across teams**: Meaningless comparison
- ❌ **No re-estimation**: Update when you learn more

---

## Verification Checklist

### Stories
- [ ] User story format followed
- [ ] INVEST criteria met
- [ ] Acceptance criteria in Gherkin format
- [ ] Story ≤ 5 points
- [ ] Definition of Done defined

### Backlog
- [ ] Regular refinement sessions
- [ ] 2 sprints worth of ready stories
- [ ] Stories prioritized
- [ ] Large stories split

### Ceremonies
- [ ] Sprint planning sets goal and commitment
- [ ] Daily standups < 15 minutes
- [ ] Sprint review demos working software
- [ ] Retrospectives produce action items

### Velocity
- [ ] Velocity tracked per sprint
- [ ] Only done work counted
- [ ] Used for planning, not performance
- [ ] WIP limits enforced

---

## Code Patterns (Reference)

### User Story Template
```
## Story: USER-123
**As a** registered user
**I want to** reset my password via email
**So that** I can regain access if I forget credentials

### Acceptance Criteria
Given I am on the login page
When I click "Forgot Password"
And I enter my registered email
Then I should see "Reset link sent"
And I should receive an email within 5 minutes

### Definition of Done
- [ ] Tests pass (>80% coverage)
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] No P1/P2 bugs
```

### Velocity Tracking
```
| Sprint | Committed | Completed | Carry-over |
|--------|-----------|-----------|------------|
| S21 | 24 | 24 | 0 |
| S22 | 26 | 20 | 6 |
| S23 | 23 | 21 | 2 |
| Avg | 24.3 | 21.7 | - |
```

### Retro Action Items
```
| Action | Owner | Due |
|--------|-------|-----|
| Set up pair programming rotation | Dev Lead | Next sprint |
| Timebox meetings to 1h | PM | Immediately |
```

### Sprint Planning Output
```
Sprint Goal: Users can reset passwords enabling self-service recovery

Committed: 22 pts (78% capacity)
Buffer: 6 pts for unknowns
Stretch: USER-125 (3 pts) if ahead
```

