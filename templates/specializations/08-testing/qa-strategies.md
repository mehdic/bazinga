---
name: qa-strategies
type: testing
priority: 2
token_estimate: 550
compatible_with: [qa_expert, tech_lead]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# QA Strategies & Test Planning Expertise

## Specialist Profile
QA specialist designing comprehensive test strategies. Expert in test planning, risk-based testing, and quality metrics.

---

## Patterns to Follow

### Test Planning
- **Risk-based prioritization**: High impact first
- **Entry/exit criteria**: Clear gates
- **Test levels defined**: Unit → Integration → E2E
- **Coverage targets**: Realistic, not 100%
- **Traceability matrix**: Requirements → tests

### Test Design Techniques
- **Boundary Value Analysis**: Min, max, and edges
- **Equivalence Partitioning**: Group similar inputs
- **Decision Tables**: Complex logic coverage
- **State Transition**: Workflow testing
- **Pairwise Testing**: Combinatorial efficiency

### Quality Metrics
- **Defect density**: Defects per KLOC
- **Test coverage**: Lines, branches, paths
- **Escaped defects**: Bugs found in production
- **Mean time to detect (MTTD)**: How fast bugs found
- **Defect removal efficiency**: Testing vs. production

### Test Pyramid
- **Unit tests (70%)**: Fast, many, isolated
- **Integration tests (20%)**: API, database contracts
- **E2E tests (10%)**: Critical user journeys
- **Shift left**: More testing earlier

### Defect Management
- **Severity levels**: Critical, High, Medium, Low
- **SLAs per severity**: Time to fix
- **Root cause analysis**: Prevent recurrence
- **Regression suite**: Prevent regressions

---

## Patterns to Avoid

### Planning Anti-Patterns
- ❌ **No test plan**: Ad-hoc testing
- ❌ **Testing everything equally**: Waste of resources
- ❌ **Skipping risk assessment**: Surprises in prod
- ❌ **No exit criteria**: Never-ending testing

### Execution Anti-Patterns
- ❌ **Manual-only regression**: Slow, error-prone
- ❌ **No environment parity**: "Works on my machine"
- ❌ **Skipping negative tests**: Only happy paths
- ❌ **Ignoring non-functional**: Performance, security

### Metrics Anti-Patterns
- ❌ **Test count as quality**: Quantity ≠ quality
- ❌ **100% coverage goal**: False confidence
- ❌ **Hiding defects**: Gaming metrics
- ❌ **No tracking over time**: No trends

### Process Anti-Patterns
- ❌ **QA at the end**: Shift left instead
- ❌ **No automation strategy**: Manual bottleneck
- ❌ **Siloed QA**: Should be team responsibility
- ❌ **No exploratory testing**: Scripted misses edge cases

---

## Verification Checklist

### Planning
- [ ] Test plan documented
- [ ] Risk assessment completed
- [ ] Entry/exit criteria defined
- [ ] Coverage targets set

### Design
- [ ] Boundary values covered
- [ ] Equivalence classes identified
- [ ] Negative scenarios included
- [ ] Non-functional requirements addressed

### Execution
- [ ] Automated regression suite
- [ ] Environment parity ensured
- [ ] Exploratory testing scheduled
- [ ] Cross-browser/device testing

### Metrics
- [ ] Defect metrics tracked
- [ ] Coverage measured
- [ ] Trends analyzed
- [ ] Escaped defects monitored

---

## Code Patterns (Reference)

### Test Plan Structure
- **Scope**: In-scope features, out-of-scope items
- **Approach**: Test levels, types, tools
- **Criteria**: Entry (code complete), Exit (no P1/P2 open)
- **Risks**: Probability, impact, mitigation

### Boundary Testing
<!-- version: pytest >= 7.0 -->
- **Pattern**: `@pytest.mark.parametrize("length,valid", [(1, False), (2, True), (100, True), (101, False)])`
- **Parallel**: `pytest-xdist` with `--dist worksteal` for optimal load balancing
<!-- version: pytest >= 8.0 -->
- **Improved markers**: Better marker inheritance and collection
- **Type hints**: Full type annotation support

### Equivalence Partitioning
- **Classes**: Valid standard, valid edge, invalid format, invalid empty

### Test Case Format
- **ID**: TC-FEAT-001
- **Preconditions**: User logged in as admin
- **Steps**: 1. Navigate, 2. Click, 3. Enter, 4. Submit
- **Expected**: Success message, record created

### Quality Dashboard
- **Metrics**: Coverage %, defect density, MTTD, escaped defects
- **Trends**: Week-over-week comparison
- **Alerts**: Thresholds for action

