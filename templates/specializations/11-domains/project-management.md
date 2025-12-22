---
name: project-management
type: domain
priority: 3
token_estimate: 500
compatible_with: [project_manager]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Project Management Expertise

## Specialist Profile
Project management specialist coordinating software delivery. Expert in task breakdown, estimation, risk assessment, and stakeholder communication.

---

## Patterns to Follow

### Task Decomposition
- **Epic → Story → Task**: Three-level breakdown
- **5-point maximum**: Stories larger than 5 should split
- **INVEST criteria**: Independent, Negotiable, Valuable, Estimable, Small, Testable
- **Clear acceptance criteria**: Define "done" before starting
- **Identify dependencies**: What blocks what
- **Critical path analysis**: Sequence-dependent work

### Story Point Estimation (2025)
- **Fibonacci scale**: 1, 2, 3, 5, 8, 13 (higher = more uncertainty)
- **Relative sizing**: Compare to reference story
- **Team-specific**: Points mean different things to different teams
- **Planning poker**: Consensus-based estimation
- **T-shirt sizing for epics**: XS, S, M, L, XL → points later
- **Re-estimate when learned**: Update as understanding grows

### Estimation Reference
- **1 point**: Config change, copy update (< half day)
- **2 points**: Simple CRUD endpoint (half day)
- **3 points**: Endpoint with validation + tests (1-2 days)
- **5 points**: Feature with external integration (3-4 days)
- **8 points**: Multi-service coordination (~1 week)
- **13+ points**: Break down further

### Sprint Planning
- **Velocity-based capacity**: Average of last 3-5 sprints
- **15-20% buffer**: For unknowns and bugs
- **Don't plan at 100%**: Teams need slack
- **Stretch goals**: Optional if ahead of schedule
- **No mid-sprint scope changes**: Protect the sprint
- **Clear sprint goal**: One sentence summary

### Risk Management
- **Probability × Impact scoring**: Prioritize high-score risks
- **Mitigation plans**: Actions to reduce probability
- **Contingency plans**: Actions if risk materializes
- **Risk register**: Track and review weekly
- **Early warning signs**: Define triggers for escalation

### Status Reporting
- **Traffic light status**: 🟢 On track, 🟡 At risk, 🔴 Blocked
- **Metrics tracked**: Velocity, burndown, blockers, scope changes
- **Blockers prominently displayed**: Action items attached
- **Weekly cadence**: Consistent reporting rhythm
- **Stakeholder-appropriate detail**: Executive vs. team view

### Dependency Management
- **Dependency graph**: Visual representation
- **External dependencies flagged**: Higher risk
- **Buffer time for dependencies**: Account for delays
- **Regular sync with dependent teams**: Weekly minimum
- **Escalation path defined**: When delays occur

---

## Patterns to Avoid

### Estimation Anti-Patterns
- ❌ **Estimating without team**: PM/lead estimates alone
- ❌ **Hours not points**: Points are about complexity
- ❌ **Comparing team velocities**: Points aren't standardized
- ❌ **Padding estimates secretly**: Be transparent about risk
- ❌ **No estimation at all**: Need some planning basis

### Planning Anti-Patterns
- ❌ **100% capacity planning**: No room for surprises
- ❌ **Ignoring historical velocity**: Optimism bias
- ❌ **No buffer time**: Everything perfectly timed
- ❌ **Mid-sprint scope additions**: Protect the commitment
- ❌ **No sprint goal**: Just a list of tasks

### Tracking Anti-Patterns
- ❌ **Only tracking velocity**: Ignore quality, bugs, tech debt
- ❌ **Velocity as performance metric**: Creates gaming
- ❌ **No burndown visibility**: Can't see progress
- ❌ **Status reports as punishment**: Hide problems

### Communication Anti-Patterns
- ❌ **Infrequent updates**: Stakeholders surprised
- ❌ **Hiding blockers**: Problems fester
- ❌ **Only good news**: Reality distortion
- ❌ **Technical jargon to non-technical**: Audience matters

---

## Verification Checklist

### Planning
- [ ] Stories broken down to ≤5 points
- [ ] Acceptance criteria defined
- [ ] Dependencies mapped
- [ ] Critical path identified
- [ ] Sprint capacity calculated

### Estimation
- [ ] Team involved in estimation
- [ ] Reference stories used
- [ ] Fibonacci scale applied
- [ ] High uncertainty = higher points
- [ ] Buffer included (15-20%)

### Risk Management
- [ ] Risk register maintained
- [ ] Probability × Impact scored
- [ ] Mitigation plans defined
- [ ] Regular review cadence
- [ ] Escalation paths clear

### Tracking & Communication
- [ ] Daily standups happening
- [ ] Burndown updated
- [ ] Blockers tracked and actioned
- [ ] Weekly status reports sent
- [ ] Stakeholders aligned

---

## Code Patterns (Reference)

### Sprint Capacity Calculation
```
Team capacity:
- Dev A: 100% → 10 pts
- Dev B: 80% (PTO) → 8 pts
- Dev C: 100% → 10 pts
Total: 28 pts

Buffer (20%): 5.6 pts
Committable: 22 pts
```

### Risk Register Entry
```
| ID | Risk | Prob | Impact | Score | Mitigation | Owner |
|----|------|------|--------|-------|------------|-------|
| R1 | Vendor delay | Med | High | 6 | Early integration | Dev Lead |
```

### Status Report Structure
```
## Weekly Status - Week 12
🟢 On Track | Sprint 23 | Day 7/10

### Progress
| Metric | Target | Actual |
|--------|--------|--------|
| Velocity | 25 | 18 |
| Blockers | 0 | 1 |

### Blockers
1. [Description] - ETA: Wed - Mitigation: [action]

### Next Week
- [Priority items]
```

### Sprint Goal Template
- **Format**: "By end of sprint, [stakeholder] can [capability] enabling [benefit]"
- **Example**: "By end of sprint, users can reset passwords via email enabling self-service account recovery"

