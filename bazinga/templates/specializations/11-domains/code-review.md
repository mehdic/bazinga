---
name: code-review
type: domain
priority: 3
token_estimate: 500
compatible_with: [tech_lead, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Code Review Expertise

## Specialist Profile
Code review specialist ensuring quality and maintainability. Expert in providing constructive feedback, identifying issues, and maintaining team standards.

---

## Patterns to Follow

### Review Timing (2025)
- **Start within 2 hours**: Respect author's time
- **Complete within 24 hours**: Google's 70% target
- **Small PRs first**: Quick wins build momentum
- **Block time for reviews**: Part of daily workflow
- **Draft PRs for early feedback**: Catch issues before complete

### PR Size Best Practices
- **200-400 lines ideal**: Larger PRs get worse reviews
- **Single concern per PR**: One feature, one fix
- **Split large changes**: Series of smaller PRs
- **Stacked PRs for dependencies**: Clear review order
- **Smaller = faster merge**: Less back-and-forth

### Feedback Quality
- **Explicit actions**: Say what you want (change, consider, FYI)
- **Explain why**: Link to docs, articles, past incidents
- **Suggest alternatives**: Don't just criticize
- **Distinguish blocking vs. non-blocking**: nit:, optional:, suggestion:
- **Praise good work**: Acknowledge clever solutions
- **Ask questions**: "What happens if...?" invites dialogue

### Feedback Language
- **"We" not "you"**: "We typically do X" not "You should do X"
- **Questions over demands**: "What do you think about...?"
- **Constructive framing**: "This could be improved by..." not "This is wrong"
- **Be specific**: Line numbers, exact suggestions
- **Assume good intent**: Author made reasonable choices

### What to Review
- **Logic correctness**: Does it solve the problem?
- **Edge cases**: Null, empty, max values, concurrent access
- **Security**: Injection, auth, secrets, input validation
- **Performance**: N+1 queries, large payloads, missing indexes
- **Testability**: Can this be tested? Are tests adequate?
- **Maintainability**: Will future developers understand this?

### Approval Guidelines
- **Approve with suggestions**: If non-blocking comments only
- **Request changes**: If blocking issues exist
- **Don't block on style**: Enforce via linters, not reviews
- **LGTM means ready**: Don't approve speculatively
- **Trust but verify**: Check CI passed, tests exist

### AI-Assisted Review (2025)
- **Use AI for first pass**: Catch obvious issues
- **Human review for logic**: AI misses business context
- **AI for consistency**: Style, formatting, patterns
- **Don't fully automate**: Human judgment still needed
- **Review AI suggestions**: AI can be wrong
<!-- version: github >= 2023 -->
- **GitHub Copilot Code Review**: AI-powered PR analysis
- **Suggested changes**: Inline code suggestions
<!-- version: gitlab >= 16.0 -->
- **GitLab Duo Code Review**: AI-assisted review features
- **Vulnerability detection**: Security scanning in MRs

---

## Patterns to Avoid

### Feedback Anti-Patterns
- ❌ **Vague criticism**: "This is bad" without explanation
- ❌ **Style nitpicking**: Block approval for cosmetic issues
- ❌ **Rewriting code**: Suggest changes, don't dictate
- ❌ **Delayed reviews**: >24h response times
- ❌ **Demanding tone**: "Change this" without rationale

### Review Process Anti-Patterns
- ❌ **Rubber stamping**: Approve without reading
- ❌ **Bike-shedding**: Long debates on trivial matters
- ❌ **Scope creep**: Requesting unrelated changes
- ❌ **Personal preferences**: "I would do it differently"
- ❌ **Hero reviewer**: One person reviews everything

### Communication Anti-Patterns
- ❌ **Public shaming**: Criticizing in group channels
- ❌ **Assumptions of malice**: "Why did you do this?"
- ❌ **No acknowledgment**: Author's explanation ignored
- ❌ **Inconsistent standards**: Different rules for different people

---

## Verification Checklist

### Before Reviewing
- [ ] Understand the PR context (ticket, description)
- [ ] Check if tests pass, build succeeds
- [ ] Identify scope and purpose

### During Review
- [ ] Logic is correct and complete
- [ ] Edge cases handled
- [ ] Security issues checked (OWASP top 10)
- [ ] Performance implications considered
- [ ] Tests cover new functionality
- [ ] Code is readable and maintainable

### Feedback Quality
- [ ] Comments are actionable
- [ ] Blocking vs. non-blocking is clear
- [ ] Rationale provided for suggestions
- [ ] Tone is constructive

### After Review
- [ ] Approved or changes requested within 24h
- [ ] Follow up on discussions
- [ ] Acknowledge author's updates

---

## Code Patterns (Reference)

### Comment Prefixes
- **nit:**: Minor style issue, non-blocking
- **suggestion:**: Optional improvement idea
- **question:**: Seeking clarification
- **blocking:**: Must be addressed before merge
- **FYI:**: Information, no action needed

### Approval Template
```markdown
✅ **LGTM**

Nice work on this feature!
- Great test coverage
- Clean separation of concerns

nit: Consider adding a comment on line 45 explaining the edge case.
```

### Changes Requested Template
```markdown
🔄 **Changes Requested**

Good progress! A few items to address:

**Must fix:**
1. [Security] Input validation missing on line 42
2. [Bug] Race condition in concurrent access

**Suggestions (non-blocking):**
- Extract helper function for readability

Let me know if you have questions!
```

### Security Checklist
- **Input**: Schema validation, parameterized queries, XSS prevention
- **Auth**: Password hashing, session security, authorization checks
- **Data**: No secrets in code/logs, encryption at rest/transit
- **Dependencies**: No known vulnerabilities, pinned versions

