# Blog Post: "Why I Built a Project Manager for AI Coding Agents"

*A long-form article for your personal blog, Medium, or Dev.to*

---

# Why I Built a Project Manager for AI Coding Agents (And Why You Might Need One Too)

**TL;DR:** I got tired of manually coordinating AI coding agents, so I built BAZINGA—a system that spawns parallel AI developers and coordinates them automatically. One request, multiple features built simultaneously, 3x faster than sequential work.

---

## The Problem I Didn't Expect

Six months ago, I started using Claude Code heavily. Like many developers, I was amazed at how much it could do—write functions, debug issues, refactor code, even design entire features.

But after a few weeks, I noticed something weird:

**I wasn't coding anymore. I was managing AI agents.**

Here's what my workflow looked like:

```
Me: "@dev implement JWT authentication"
[20 minutes pass...]
Me: [Check files] "Okay, that's done. Now..."
Me: "@dev implement user registration"
[20 minutes pass...]
Me: "Wait, did I run tests on the auth code?"
Me: [Check logs] "Hmm, I should probably run a security scan too..."
Me: "@security-tool scan auth code"
[10 minutes pass...]
Me: "Okay, now back to registration..."
```

I was spending more time tracking what agents were doing than actually building software.

**I had become a project manager for my AI developers.**

---

## The "Aha" Moment

One day I was working on a REST API that needed three main features:
1. JWT authentication
2. User management endpoints
3. Admin dashboard APIs

These were mostly independent—they touched different files, had minimal overlap, and could theoretically be built in parallel.

But because I was using a single AI assistant sequentially, it took:
- 20 minutes for auth
- 20 minutes for user management
- 20 minutes for admin APIs
- **Total: 60 minutes**

And that's not counting the time I spent:
- Checking if each feature was done
- Running tests manually
- Remembering to run security scans
- Coordinating dependencies

**I thought: "What if AI agents could coordinate themselves?"**

What if instead of me manually orchestrating everything, there was a Project Manager agent that:
1. Analyzed my request
2. Broke it into independent tasks
3. Spawned multiple developers to work in parallel
4. Coordinated their work automatically
5. Ensured quality gates were met

That's when I started building BAZINGA.

---

## What is BAZINGA?

BAZINGA is a multi-agent orchestration system for Claude Code that coordinates teams of AI agents working in parallel.

Instead of:
```bash
You → Single AI agent → Features built sequentially
```

You get:
```bash
You → Project Manager → Multiple AI developers working simultaneously
```

Here's what it looks like in practice:

```bash
@orchestrator implement JWT authentication, user registration, and admin dashboard
```

Behind the scenes:
1. **Project Manager** analyzes the request
   - Detects 3 independent features
   - Decides they can be built in parallel
   - Spawns 3 developer agents

2. **3 Developers work simultaneously**
   - Developer 1: JWT authentication + tests + security scan
   - Developer 2: User registration + tests + security scan
   - Developer 3: Admin dashboard + tests + security scan

3. **Tech Lead reviews all work**
   - Code review
   - Architecture validation
   - Security check
   - Provides feedback or approval

4. **PM confirms completion**
   - "BAZINGA! All features complete in 18 minutes"

**Result: 18 minutes instead of 60+**

And I didn't have to coordinate any of it.

---

## The Architecture: 5 Agents Working Together

BAZINGA coordinates 5 specialized agents, each with a clear role:

### 1. Orchestrator (The Router)
- Routes messages between agents
- Maintains workflow state
- Prevents agents from drifting off-task
- Ensures everyone stays in their lane

**Why needed:** Without a router, agents would talk past each other or forget their roles.

---

### 2. Project Manager (The Planner)
- Analyzes your requirements
- Breaks work into task groups
- Decides parallelism (1-4 developers)
- Tracks progress
- Confirms completion

**Key intelligence:** Adaptive parallelism algorithm that considers:
- Task independence (can they be built separately?)
- File overlap (do they modify the same files?)
- Dependencies (does Task B need Task A first?)
- Complexity (is coordination overhead worth it?)

**Example decisions:**

| Request | PM Decision | Reasoning |
|---------|-------------|-----------|
| "Implement JWT auth" | 1 developer | Single feature, no benefit from parallelism |
| "Add auth, user mgmt, admin dashboard" | 3 developers | Independent features, low file overlap |
| "Add login and password reset" | 1 developer | Password reset depends on login being done |
| "Refactor database layer" | 1 developer | High file overlap, risky to parallelize |

---

### 3. Developers (The Builders)
- Implement features
- Write unit tests
- Run security scans
- Check code quality
- Fix issues from Tech Lead reviews

**Parallel execution:** 1-4 developers can work simultaneously on independent tasks.

**Built-in quality gates:**
- Security scanning (bandit, gosec, npm audit)
- Lint checking (ruff, eslint, golangci-lint)
- Test coverage (pytest-cov, jest, go test)

Each developer is responsible for their own testing and scanning—no manual coordination needed.

---

### 4. Tech Lead (The Reviewer)
- Reviews all code from developers
- Validates security
- Checks architecture
- Provides feedback or approval

**Intelligent escalation:**
- Revisions 1-2: Claude Sonnet (fast, handles 90% of reviews)
- Revision 3+: Claude Opus (deep analysis for persistent issues)

Cost-effective and automatic—no manual model switching.

---

### 5. QA Expert (The Tester, optional)
- Integration tests
- Contract tests
- E2E scenarios
- Pattern mining from historical data

**When used:** Full testing mode (opt-in for production-critical code).

---

## How Adaptive Parallelism Works

The most interesting part of BAZINGA is the PM's decision-making about parallelism.

### The Naive Approach (Doesn't Work)

You might think: "Just always spawn N developers for N tasks!"

But that breaks down quickly:

**Problem 1: Dependencies**
```
Task 1: Implement login
Task 2: Implement password reset (needs login to exist)
```
If these run in parallel, Task 2 will fail because Task 1 isn't done yet.

**Problem 2: File Overlap**
```
Task 1: Refactor database connection
Task 2: Optimize database queries
```
Both modify the same database layer—parallel work would create merge conflicts.

**Problem 3: Coordination Overhead**
```
Task 1: Fix a typo in README
Task 2: Update a comment in one function
```
Spawning 2 devs for trivial tasks adds overhead without benefit.

---

### The Smart Approach (BAZINGA)

The PM analyzes multiple factors:

**1. Task Independence**
- Can Task B start without Task A being done?
- Are there logical dependencies?

**2. File Overlap**
- Do tasks modify the same files?
- High overlap = higher merge conflict risk

**3. Complexity**
- Are tasks non-trivial enough to benefit from parallelism?
- Is coordination overhead worth the speedup?

**4. Risk Assessment**
- Is this a refactoring (high risk in parallel)?
- Or net-new features (low risk in parallel)?

Based on this analysis, the PM decides:
- **1 developer:** Sequential execution (dependencies, high overlap, or low complexity)
- **2-4 developers:** Parallel execution (independent, low overlap, non-trivial tasks)

---

## Real Example: Building an Authentication System

Let me show you a real workflow comparison.

### Before BAZINGA (Sequential)

```bash
$ @dev implement JWT authentication with access and refresh tokens

[Developer works for 20 minutes]

Developer: "Done. JWT auth implemented with tests."

$ [Me checking files...]
$ [Running tests manually...]
$ [Running security scan...]

$ @dev now implement user registration with email verification

[Developer works for 20 minutes]

Developer: "Done. User registration with email verification."

$ [Me checking again...]
$ [Running tests again...]
$ [Running security scan again...]

$ @dev now implement password reset flow

[Developer works for 20 minutes]

Developer: "Done. Password reset flow implemented."

$ [Me checking a third time...]
$ @review-agent review all the auth code

[Review agent works for 15 minutes]

Total time: ~85 minutes + my manual coordination
```

---

### After BAZINGA (Parallel)

```bash
$ @orchestrator implement authentication system with JWT (access and refresh tokens), user registration with email verification, and password reset flow

PM: "Analyzing request... Detected 3 independent features."
PM: "Spawning 3 developers in parallel."

[3 developers work simultaneously for 18 minutes]

Developer 1 (JWT):
✓ Implementation complete
✓ Unit tests written
✓ Security scan passed (no issues)
✓ Lint check passed
✓ Coverage: 87%

Developer 2 (Registration):
✓ Implementation complete
✓ Unit tests written
✓ Security scan passed (no issues)
✓ Lint check passed
✓ Coverage: 82%

Developer 3 (Password Reset):
✓ Implementation complete
✓ Unit tests written
✓ Security scan passed (no issues)
✓ Lint check passed
✓ Coverage: 85%

Tech Lead: "Reviewing all implementations..."
Tech Lead: "All features approved. Code quality excellent, security validated."

PM: "BAZINGA! All features complete."

Total time: 18 minutes, zero manual coordination
```

**Speedup: 85 minutes → 18 minutes (4.7x faster)**

And I didn't have to:
- Check if each dev was done
- Manually run tests
- Remember to run security scans
- Coordinate the review

The PM handled all of it.

---

## Automatic Quality Gates

One of the biggest benefits of BAZINGA is that quality checks are automatic and built-in.

Every developer automatically runs:

### 1. Security Scanning
- **Tools:** bandit (Python), gosec (Go), npm audit (JS), brakeman (Ruby), SpotBugs (Java)
- **Checks:** SQL injection, XSS, hardcoded secrets, auth bypasses, insecure dependencies
- **Escalation:** Basic scan (5-10s) → Advanced scan (30-60s) after 2 revisions

No more "oops, forgot to run security scan before deploying."

---

### 2. Lint Checking
- **Tools:** ruff (Python), eslint (JS), golangci-lint (Go), rubocop (Ruby), Checkstyle (Java)
- **Checks:** Code style, complexity, best practices, common mistakes
- **Enforcement:** All issues must be fixed before Tech Lead approval

Consistent code quality without manual enforcement.

---

### 3. Test Coverage
- **Tools:** pytest-cov (Python), jest (JS), go test (Go), simplecov (Ruby), JaCoCo (Java)
- **Checks:** Line coverage, branch coverage, untested code paths
- **Target:** 80% coverage by default

Every feature ships with tests—not as an afterthought.

---

### 4. Code Review
- Tech Lead reviews all work
- Checks architecture, security, maintainability
- Uses Opus for deep analysis if needed (revision 3+)

Automated but intelligent review process.

---

## Performance: Is It Really Faster?

I've tested BAZINGA on various projects. Here's what I've found:

### Speedup Data

| Task Type | Sequential | BAZINGA | Speedup |
|-----------|-----------|---------|---------|
| 2 independent features | 40 min | 15 min | 2.7x |
| 3 independent features | 60 min | 20 min | 3x |
| 4 independent modules | 90 min | 30 min | 3x |

**Limitations:**
- Max 4 developers (coordination overhead beyond this)
- Features must be truly independent
- Dependencies force sequential execution
- Refactoring often better done sequentially

**When BAZINGA shines:**
- Net-new features with low file overlap
- Independent modules or services
- REST API endpoints
- Multiple bug fixes in different areas

**When BAZINGA doesn't help:**
- Single complex feature
- Refactoring with high file overlap
- Dependent tasks (Task B needs Task A)
- Trivial changes (overhead > benefit)

---

## Challenges I Faced

Building BAZINGA wasn't straightforward. Here are the main challenges:

### 1. Role Drift
**Problem:** Agents would forget their roles and start doing each other's jobs.

Example: Developer would try to coordinate other developers (PM's job) or Tech Lead would start implementing code (Developer's job).

**Solution:** Clear role definitions in prompts + Orchestrator that enforces role boundaries.

---

### 2. State Management
**Problem:** With 5 agents working concurrently, tracking who's doing what is complex.

**Solution:** JSON state files in `coordination/` directory:
- `pm_state.json` - Task groups, progress, iteration count
- `group_status.json` - Per-task status, revision counts
- `orchestrator_state.json` - Active agents, routing state

All gitignored (except config files) to avoid merge conflicts.

---

### 3. Merge Conflicts
**Problem:** Even with low overlap, parallel devs sometimes modify adjacent code.

**Solution:** PM's overlap analysis + Tech Lead validation. If conflicts arise, Tech Lead provides resolution guidance.

---

### 4. Coordination Overhead
**Problem:** Spawning multiple agents adds overhead (startup, routing, merging).

**Solution:** PM's complexity check—only parallelize if benefit > overhead. For trivial tasks, use 1 developer.

---

### 5. Tool Availability
**Problem:** Not all projects have security/lint/coverage tools installed.

**Solution:** Graceful degradation—BAZINGA warns if tools are missing but continues working. Optional tool auto-installation during setup.

---

## What I Learned

### 1. Parallelism Isn't Always Faster
The naive approach of "always use max parallelism" doesn't work.

The PM's adaptive algorithm is critical—it needs to make intelligent decisions about when parallelism helps.

### 2. Coordination is Hard (Even for AI)
Just like human teams, AI teams need clear roles, communication protocols, and state management.

The Orchestrator isn't optional—without it, agents quickly drift off-task.

### 3. Quality Gates Must Be Automatic
Developers (human or AI) will skip optional quality checks.

Making security scans, lint, and coverage checks automatic ensures they always happen.

### 4. Model Escalation Matters
Using Opus for everything is expensive and slow.

Using Sonnet for typical work and auto-escalating to Opus for hard problems is the sweet spot.

---

## Current Status & What's Next

BAZINGA is **early stage and open source (MIT)**.

I'm at a decision point: **Is this worth building further?**

### What I Need
**Feedback from real users:**
- Does this solve a problem you have?
- Would you use this over manual agent coordination?
- What would make this a daily tool?
- Where does it break down?

### What I'm Exploring
1. **Does automated coordination beat manual control?**
   - Or do developers prefer managing agents themselves?

2. **What workflows benefit most?**
   - API development? Bug fixes? Refactoring? New features?

3. **Is 3x speed worth the complexity?**
   - Or is the overhead too high?

4. **Where should I focus next?**
   - Better parallelism algorithm?
   - More language support?
   - Improved quality gates?
   - Different problem entirely?

---

## Try It & Let Me Know

If this resonates with you, I'd love your feedback.

### Installation (1 command)
```bash
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project
cd my-project
@orchestrator implement user authentication with JWT
```

### Share Feedback
- **Quick survey (2 min):** [YOUR FEEDBACK FORM]
- **GitHub issues:** https://github.com/mehdic/bazinga/issues
- **Email me:** [YOUR EMAIL]
- **15-min chat:** [YOUR CALENDLY LINK]

**Honest feedback wanted**—even "this is useless because X" helps me learn.

---

## The Bigger Picture

I built BAZINGA to solve a specific problem I had: too much time managing AI agents, not enough time building.

But I think there's a broader question here:

**As AI coding tools get more powerful, how do we coordinate them?**

Right now, most AI coding assistants are single-agent systems. You talk to one AI, it does one thing at a time.

But real dev teams don't work that way. They work in parallel, specialize in roles, coordinate automatically.

BAZINGA is an experiment in bringing that team dynamic to AI developers.

Maybe it works. Maybe it doesn't. But I think the question is worth exploring.

---

## Final Thoughts

I don't know if BAZINGA is the right solution.

I don't know if automated coordination beats manual control.

I don't even know if parallel AI development is a real problem people have.

**But I know I had this problem. And I'm curious if others do too.**

If you've ever felt like you were babysitting AI agents instead of coding, give BAZINGA a try.

And let me know what you think.

---

**GitHub:** https://github.com/mehdic/bazinga
**Feedback:** [YOUR FEEDBACK FORM]
**Author:** [@mehdic](https://github.com/mehdic)

---

*Thanks for reading! If you found this interesting, share it with someone who might benefit from parallel AI development.*

---

## Appendix: Technical Details

For those interested in the implementation details:

### Tech Stack
- **Language:** Python 3.11+
- **Framework:** Claude Agent SDK
- **State:** JSON files (gitignored)
- **Quality Tools:** bandit, ruff, gosec, eslint, pytest-cov, jest, etc.

### Agent Prompts
Each agent has a detailed system prompt defining:
- Role and responsibilities
- Communication protocol
- Success criteria
- Constraints

View prompts: `.claude/agents/` directory

### Parallelism Algorithm
The PM uses a scoring system:
- Independence score (0-100)
- Overlap score (0-100)
- Complexity score (0-100)
- Risk score (0-100)

Threshold: Parallelize if combined score > 60

View implementation: `.claude/agents/project_manager.md`

### State Management
3 main state files:
- `pm_state.json` - PM planning
- `group_status.json` - Task tracking
- `orchestrator_state.json` - Routing state

All atomic updates, no locking (stateless agents).

### Quality Gate Integration
Skills system hooks:
- `security-scan` - Pre-commit security checks
- `lint-check` - Code quality validation
- `test-coverage` - Coverage analysis

View Skills: `.claude/skills/` directory

---

*Have questions about the implementation? Open an issue on GitHub or email me!*
