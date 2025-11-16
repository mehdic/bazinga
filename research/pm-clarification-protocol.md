# PM Clarification Protocol - Design Document

**Status:** Implemented (2025-01-16)
**Authors:** Claude (based on codex's analysis)
**Related Files:** `agents/project_manager.md`, `agents/orchestrator.md`

---

## Problem Statement

### Original Issue

The PM agent had an **absolute prohibition** against asking users for clarification:

```markdown
## ⚠️ CRITICAL: Full Autonomy - Never Ask User
**YOU ARE FULLY AUTONOMOUS. DO NOT ASK THE USER ANYTHING.**
```

### Why This Was Problematic

**Codex's observation:**
> Workflow rigidity can block legitimate clarifications. The PM spec flatly forbids ever asking the human for follow-up. That might work for tiny, unambiguous tickets, but many real-world tasks require confirming assumptions or negotiating trade-offs. Enforcing silence could drive agents to fabricate requirements instead of clarifying them, lowering quality for complex changes.

**Real-world examples of problematic scenarios:**

1. **Mutually Exclusive Requirements**
   - User: "Add passwordless authentication"
   - Also user: "Users should be able to set passwords"
   - PM forced to guess which one to implement

2. **Missing External Data**
   - User: "Integrate with Stripe payment processing"
   - No Stripe API keys in repository
   - No indication of test vs production mode
   - PM forced to fabricate assumptions

3. **Security/Legal Ambiguity**
   - User: "Handle user PII properly"
   - Unclear if GDPR, CCPA, HIPAA, or other compliance needed
   - PM forced to guess compliance requirements

**Consequences of absolute silence:**
- ❌ Wasted developer hours on wrong implementations
- ❌ Multiple revision cycles when assumptions are wrong
- ❌ Lower quality for complex, ambiguous tasks
- ❌ User frustration when delivered solution doesn't match intent

---

## Solution Design

### Design Principles (from codex)

1. **Trigger Heuristics** - Specific, auditable blockers only
2. **Quota and Cooldown** - ONE clarification per session, exhaust resources first
3. **Structured Messaging** - Required template prevents open-ended chats
4. **State + Telemetry** - All logged in bazinga-db with pause/resume support
5. **Fallback Mechanism** - Never permanently blocked, proceeds with safe assumption
6. **Surgical Implementation** - Minimal changes, no bloat

### The Three-Tier System

#### Tier 1: Requirements Engineer (Proactive, First Line)
- **Already implemented** in `/bazinga.orchestrate-advanced` mode
- Asks clarifying questions BEFORE orchestration starts
- Resolves most ambiguities upfront
- Only runs when user explicitly uses advanced mode

#### Tier 2: PM Smart Blocking (Reactive, Rare) - **NEW**
- PM CAN ask, but ONLY for critical blockers
- Strict conditions prevent overuse
- Batched questions (no back-and-forth)
- Automatic fallback after timeout

#### Tier 3: Assumption Documentation (Always) - **NEW**
- PM documents ALL assumptions made
- Transparent about decisions
- User can validate at review/completion
- No blocking, just transparency

---

## Implementation Details

### Four Strict Conditions (ALL Must Be Met)

The PM may signal `NEEDS_CLARIFICATION` **ONLY** when:

#### 1. Specific Blocker Type (must be ONE of these)

**A) Mutually Exclusive Requirements**
- User said X and also said NOT-X in the same request
- Examples:
  - "Add passwordless auth" + "Users should set passwords"
  - "Make it stateless" + "Store session data"
  - "Use REST API" + "Implement GraphQL"

**B) Missing External Data**
- Required data not in repository (API keys, dataset URLs, credentials, endpoints)
- Cannot proceed without this information
- Examples:
  - "Integrate with Stripe" but no Stripe API key or test mode indicator
  - "Connect to production database" but no connection string
  - "Use external API" but no endpoint or authentication details

**C) Security/Legal Decision**
- Security-critical choice with no safe default
- Legal/compliance requirement unclear
- Examples:
  - "Handle PII" but unclear if GDPR/CCPA/HIPAA applies
  - "Encrypt data" but no key management strategy specified
  - "Implement audit logging" but retention policies unclear

#### 2. Evidence of Exhaustion (must complete ALL)

**Before asking, PM MUST:**
- ✅ Search codebase for similar features, patterns, configurations
- ✅ Check existing infrastructure for hints (auth methods, data stores, integrations)
- ✅ Attempt to infer from project context (tech stack, existing choices)
- ✅ If complex: Spawn Investigator to deep-dive (still blocked after investigation)

**This ensures PM tries autonomously first.**

#### 3. Quota Check

- ✅ No other active clarification thread (ONE at a time per project)
- ✅ This is PM's first clarification request for this session

**This prevents back-and-forth conversations.**

#### 4. Planning Phase Only

- ✅ Must be during initial planning (NOT during development/QA/fixes)
- ✅ Cannot ask mid-execution (make best decision and document assumption)

**This keeps execution autonomous once started.**

---

### Clarification Request Format

**If all four conditions are met, PM uses this exact format:**

```markdown
## PM Status: NEEDS_CLARIFICATION

**Blocker Type:** [Mutually Exclusive Requirements / Missing External Data / Security Decision]

**Evidence of Exhaustion:**
- Codebase search: [files/patterns searched, what was found/not found]
- Similar features: [existing features examined]
- Attempted inference: [what reasoning was applied]
- Investigator findings: [if spawned, summary of investigation]

**Question:** [Single specific question]

**Options:**
a) [Option 1 - specific, actionable]
b) [Option 2 - specific, actionable]
c) [Option 3 - if applicable]

**Safe Fallback:** If no response within 5 minutes, I will proceed with option [X] because [clear reasoning based on evidence]. This assumption will be logged with risk assessment.

**Status:** AWAITING_CLARIFICATION (auto-proceed with fallback after 5 minutes)
```

**Key elements:**
- **Blocker Type** - One of three specific categories
- **Evidence** - Proof PM tried to resolve autonomously
- **Options** - Specific, actionable choices (not open-ended)
- **Safe Fallback** - What PM will do if no response (never blocked)
- **Timeout** - 5 minutes, then auto-proceed

---

### Orchestrator Handling (Step 1.3a)

**When PM returns `NEEDS_CLARIFICATION`:**

1. **Log to Database**
   ```
   bazinga-db: Log clarification request
   - Session ID, request type, status: pending
   ```

2. **Update Orchestrator State**
   ```
   bazinga-db: Update orchestrator state
   - clarification_pending: true
   - phase: awaiting_clarification
   ```

3. **Surface to User**
   ```
   ⚠️ **ORCHESTRATOR**: PM needs clarification to proceed

   [Display PM's full NEEDS_CLARIFICATION section]

   ⏱️ **ORCHESTRATOR**: Waiting for response (auto-proceed with fallback in 5 min)
   ```

4. **Wait for Response (5 min timeout)**
   - User responds → Log answer, re-spawn PM
   - Timeout → Log timeout, re-spawn PM with fallback signal

5. **Re-spawn PM with Answer**
   - PM documents answer in `assumptions_made` array
   - PM proceeds with planning
   - Returns normal PM Decision (SIMPLE or PARALLEL mode)

6. **Clear State and Continue**
   ```
   bazinga-db: Update orchestrator state
   - clarification_pending: false
   - phase: planning_complete
   ```

---

### Assumption Documentation

**For ANY decision where PM inferred or assumed, document in pm_state:**

```json
"assumptions_made": [
  {
    "decision": "Using JWT for authentication",
    "blocker_type": "none",
    "user_response": "inferred_from_codebase",
    "reasoning": "Codebase already has JWT utils in /api/auth.py, no session management found",
    "confidence": "high",
    "risk_if_wrong": "medium - would need to refactor auth approach"
  },
  {
    "decision": "Passwordless authentication only",
    "blocker_type": "mutually_exclusive_requirements",
    "user_response": "User confirmed option (a): passwordless only",
    "reasoning": "User initially said both passwordless and passwords; clarified to passwordless",
    "confidence": "high",
    "risk_if_wrong": "low - explicit user confirmation"
  },
  {
    "decision": "Using Stripe test mode",
    "blocker_type": "missing_external_data",
    "user_response": "timeout_assumed",
    "reasoning": "No Stripe keys in repo; assumed test mode as safest fallback",
    "confidence": "medium",
    "risk_if_wrong": "low - test mode won't affect production"
  }
]
```

**Fields:**
- `decision` - What was decided
- `blocker_type` - Type of blocker (or "none" if inferred)
- `user_response` - Source of answer (inferred/confirmed/timeout)
- `reasoning` - Why this decision was made
- `confidence` - High/medium/low confidence level
- `risk_if_wrong` - Impact if assumption is incorrect

**Benefits:**
- ✅ Transparency - User sees all assumptions
- ✅ Auditability - Tracked in database
- ✅ Validation checkpoint - User can review before execution
- ✅ Learning - System improves from feedback

---

## Examples

### Example 1: Valid Clarification (Mutually Exclusive Requirements)

**User Request:**
```
Add authentication to the app. It should be passwordless for better UX,
and users should be able to set strong passwords for security.
```

**PM Analysis:**
- Blocker: Mutually exclusive requirements (passwordless vs passwords)
- Evidence: Searched codebase, found existing JWT utils but no auth flow
- Cannot infer which approach user wants
- High impact (4+ hours difference between implementations)

**PM Response:**
```markdown
## PM Status: NEEDS_CLARIFICATION

**Blocker Type:** Mutually Exclusive Requirements

**Evidence of Exhaustion:**
- Codebase search: Found JWT utilities in /api/auth.py, no existing auth flow
- Similar features: No authentication currently implemented
- Attempted inference: Request contains both "passwordless" and "set passwords"
- Cannot determine which approach user intends

**Question:** Which authentication method should I implement?

**Options:**
a) Passwordless only (magic links, biometric, no passwords)
b) Password-based only (traditional username/password)
c) Both methods (passwordless as primary + password fallback)

**Safe Fallback:** If no response within 5 minutes, I will proceed with option (b)
password-based because it's more widely understood and has lower implementation risk.
This assumption will be logged with medium risk.

**Status:** AWAITING_CLARIFICATION (auto-proceed with fallback after 5 minutes)
```

**User Response:** "Option c - both methods, passwordless as primary"

**PM Documents:**
```json
{
  "decision": "Implement both passwordless and password authentication",
  "blocker_type": "mutually_exclusive_requirements",
  "user_response": "User confirmed option (c): both methods",
  "reasoning": "Initially ambiguous request clarified to support both auth methods",
  "confidence": "high",
  "risk_if_wrong": "low - explicit user confirmation"
}
```

### Example 2: Invalid Clarification (PM Should Decide)

**User Request:**
```
The tests are failing. Fix them.
```

**PM Should NOT Ask:**
❌ "Do you want me to continue fixing the tests?"
❌ "Which test framework should I use?"
❌ "Should I run tests in parallel?"

**PM Should Autonomously:**
- ✅ Analyze test failures
- ✅ Use existing test framework (from codebase)
- ✅ Assign developers to fix failures
- ✅ Continue until all tests pass
- ✅ Send BAZINGA when complete

**Why:** This is routine execution, not a critical blocker. PM has full authority to continue work.

### Example 3: Valid Clarification (Missing External Data)

**User Request:**
```
Integrate Stripe payment processing for our checkout flow.
```

**PM Analysis:**
- Blocker: Missing external data (no Stripe API keys in repo)
- Evidence: Searched for config files, env vars, no Stripe credentials found
- Cannot proceed without knowing test vs production mode
- Medium impact (affects integration testing)

**PM Response:**
```markdown
## PM Status: NEEDS_CLARIFICATION

**Blocker Type:** Missing External Data

**Evidence of Exhaustion:**
- Codebase search: No Stripe API keys in config/, .env files, or secrets/
- Similar features: No existing payment integrations found
- Attempted inference: Cannot determine if test mode or production credentials needed

**Question:** Which Stripe environment should I configure?

**Options:**
a) Test mode (use Stripe test API keys for development/staging)
b) Production mode (use production API keys)
c) Both (configurable via environment variable)

**Safe Fallback:** If no response within 5 minutes, I will proceed with option (a)
test mode because it's safer for development and won't process real payments.
This assumption will be logged with low risk.

**Status:** AWAITING_CLARIFICATION (auto-proceed with fallback after 5 minutes)
```

**Timeout:** No user response after 5 minutes

**PM Proceeds with Fallback:**
```json
{
  "decision": "Configure Stripe in test mode",
  "blocker_type": "missing_external_data",
  "user_response": "timeout_assumed",
  "reasoning": "No Stripe credentials in repo; test mode is safest default for development",
  "confidence": "medium",
  "risk_if_wrong": "low - test mode won't affect production, easy to switch later"
}
```

---

## Trade-offs and Rationale

### Why This Design?

**Compared to Other Options:**

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Status Quo** (absolute silence) | Simple rule, forces specific requests | Wasted effort on wrong assumptions | ❌ Too rigid |
| **Always ask when uncertain** | Never guesses wrong | Slow, annoying, too many questions | ❌ Too chatty |
| **Smart clarification** (chosen) | Balances autonomy with quality | More complex rules | ✅ **Best balance** |
| **Documentation only** | Zero blocking | Still risks wrong implementation | ⚠️ Good fallback |

**Why the 4 conditions are strict:**

1. **Specific blocker types** - Prevents PM from asking vague questions
2. **Evidence of exhaustion** - Ensures PM tried autonomously first
3. **Quota limit** - Prevents back-and-forth conversations
4. **Planning phase only** - Keeps execution fast and autonomous

**Why 5-minute timeout:**

- Long enough for user to read and respond
- Short enough to not significantly delay workflow
- Automatic fallback prevents permanent blocking
- User can still provide answer even after timeout (PM documents it)

**Why safe fallback is required:**

- Guarantees forward progress (never stuck)
- Forces PM to think through least-risky option
- Documents reasoning for future reference
- User can correct if wrong, but work continues

---

## Impact Analysis

### Before Implementation

**Scenario:** User says "Add authentication"

1. PM guesses JWT (because it's common)
2. Developer implements JWT auth (2 hours)
3. User reviews: "I wanted OAuth with Google login"
4. Developer re-implements OAuth (3 hours)
5. **Total wasted:** 2 hours + context switching

### After Implementation

**Scenario:** User says "Add authentication"

1. PM searches codebase, finds no auth (exhaustion)
2. PM detects ambiguity (multiple valid methods)
3. PM asks: "JWT, OAuth, or session-based?"
4. User responds: "OAuth with Google" (30 seconds)
5. Developer implements OAuth correctly (3 hours)
6. **Total wasted:** 0 hours

**Net savings:** 2+ hours per ambiguous task

### Autonomy Preserved

**PM still decides autonomously:**
- ✅ 95%+ of tasks (clear or inferable requirements)
- ✅ Technical implementation details
- ✅ Test frameworks (use codebase patterns)
- ✅ Parallelization strategy
- ✅ Bug fixing approach
- ✅ Code organization

**PM only asks:**
- ⚠️ <5% of tasks (critical blockers only)
- ⚠️ Business requirement ambiguities
- ⚠️ Missing external data
- ⚠️ Security/legal decisions

---

## Database Schema Impact

### New Fields in `orchestrator_state`

```json
{
  "clarification_pending": false,
  "clarification_requested_at": "2025-01-16T10:30:00Z",
  "phase": "planning_complete"
}
```

### New Fields in `pm_state`

```json
{
  "assumptions_made": [
    {
      "decision": "string",
      "blocker_type": "none|mutually_exclusive_requirements|missing_external_data|security_decision",
      "user_response": "string",
      "reasoning": "string",
      "confidence": "high|medium|low",
      "risk_if_wrong": "string"
    }
  ]
}
```

### New Log Type in `agent_interactions`

```json
{
  "request_type": "pm_clarification",
  "status": "pending|resolved|timeout",
  "content": "...",
  "user_response": "...",
  "resolved_at": "ISO timestamp"
}
```

---

## Testing Strategy

### Test Cases

**1. Normal Flow (No Clarification Needed)**
- Clear requirements → PM decides autonomously
- Verify: No clarification request, workflow proceeds normally

**2. Clarification with User Response**
- Ambiguous requirements → PM asks → User responds
- Verify: PM documents answer, proceeds with clarified requirements

**3. Clarification with Timeout**
- Ambiguous requirements → PM asks → No response (5 min)
- Verify: PM proceeds with safe fallback, logs timeout assumption

**4. Invalid Clarification Attempt**
- PM tries to ask about technical detail (not blocker)
- Verify: PM decides autonomously instead (conditions not met)

**5. Multiple Clarifications (Quota Test)**
- PM already asked once → Tries to ask again
- Verify: Quota check fails, PM decides autonomously

### Manual Testing Scenarios

**Scenario 1: Mutually Exclusive Requirements**
```
User: "Make the API stateless and maintain user sessions"
Expected: PM asks which approach (stateless or sessions)
```

**Scenario 2: Missing External Data**
```
User: "Connect to the production database"
Expected: PM asks for connection string or proceeds with test DB fallback
```

**Scenario 3: Should NOT Ask**
```
User: "Fix the failing tests"
Expected: PM analyzes failures, assigns developers, no clarification
```

---

## Future Enhancements

### Potential Improvements

1. **Learning from History**
   - Track which assumptions were wrong
   - Adjust confidence levels over time
   - Improve inference from codebase patterns

2. **User Preferences**
   - Allow users to set "always ask" or "never ask" mode
   - Per-project clarification settings
   - Trusted codebase = fewer questions

3. **Proactive Suggestions**
   - PM suggests likely options before asking
   - "Based on your previous project X, should I use Y?"

4. **Clarification Templates**
   - Pre-defined question patterns for common ambiguities
   - Faster question generation
   - More consistent format

### Non-Goals (Out of Scope)

- ❌ **Multi-turn conversations** - ONE question, ONE answer
- ❌ **Open-ended questions** - Always provide specific options
- ❌ **Mid-execution clarifications** - Only during planning
- ❌ **Approval workflows** - PM has authority to execute

---

## References

### Related Documents

- `agents/project_manager.md` - PM agent specification with clarification protocol
- `agents/orchestrator.md` - Orchestrator clarification handling (Step 1.3a)
- `agents/requirements_engineer.md` - Proactive clarification in advanced mode

### Related Issues/PRs

- Initial implementation: PR #[TBD] - Enable PM clarification questions for critical blockers
- Original problem identified by: codex (code review feedback)

### Commit

- Hash: `0b74836`
- Branch: `claude/enable-clarification-questions-01Xt6JxFmj9uSJTq4fL5yYFn`
- Date: 2025-01-16

---

## Appendix: Complete Example Workflow

### End-to-End Example: Stripe Integration

**Step 1: User Request**
```
Integrate Stripe for payment processing in the checkout flow.
```

**Step 2: Orchestrator Spawns PM**
```
🔄 **ORCHESTRATOR**: Phase 1 - Spawning Project Manager to analyze requirements...
```

**Step 3: PM Analysis**
```
PM searches codebase:
- No Stripe SDK found
- No API keys in config files
- No existing payment integrations
- Requirements unclear: test vs production mode

PM determines:
- Blocker Type: Missing External Data ✅
- Evidence of Exhaustion: Searched codebase thoroughly ✅
- Quota Check: First clarification request ✅
- Planning Phase: Yes ✅

All conditions met → Request clarification
```

**Step 4: PM Returns NEEDS_CLARIFICATION**
```markdown
## PM Status: NEEDS_CLARIFICATION

**Blocker Type:** Missing External Data

**Evidence of Exhaustion:**
- Codebase search: No Stripe SDK, no API keys in config/, .env, secrets/
- Similar features: No payment integrations found
- Attempted inference: Cannot determine environment (test vs prod)

**Question:** Which Stripe environment should I configure?

**Options:**
a) Test mode (Stripe test API, safe for development)
b) Production mode (live API keys, real payments)
c) Both (environment-variable based switching)

**Safe Fallback:** If no response in 5 minutes, proceed with (a) test mode
because it's safer for development. This will be logged as medium-confidence assumption.

**Status:** AWAITING_CLARIFICATION
```

**Step 5: Orchestrator Detects NEEDS_CLARIFICATION**
```
📨 **ORCHESTRATOR**: Received PM response - clarification needed
```

**Step 6: Orchestrator Logs to Database**
```
bazinga-db: Log clarification request
- Session: bazinga_20250116_103000
- Type: pm_clarification
- Status: pending
```

**Step 7: Orchestrator Updates State**
```
bazinga-db: Update orchestrator state
- clarification_pending: true
- phase: awaiting_clarification
```

**Step 8: Orchestrator Surfaces to User**
```
⚠️ **ORCHESTRATOR**: PM needs clarification to proceed

**Blocker Type:** Missing External Data

[Full clarification request displayed]

⏱️ **ORCHESTRATOR**: Waiting for your response (auto-proceed with fallback in 5 minutes)

Please provide your answer, or I will proceed with the fallback option.
```

**Step 9: User Responds**
```
User: "Use option c - both modes with environment variable"
```

**Step 10: Orchestrator Logs Response**
```
bazinga-db: Update clarification request
- Status: resolved
- User response: "Use option c - both modes with environment variable"
- Resolved at: 2025-01-16T10:31:15Z
```

**Step 11: Orchestrator Re-spawns PM**
```
🔄 **ORCHESTRATOR**: Re-spawning PM to proceed with clarified requirements...

[Spawns PM with clarification answer included]
```

**Step 12: PM Documents and Plans**
```json
assumptions_made: [
  {
    "decision": "Implement Stripe with environment-based switching (test/prod)",
    "blocker_type": "missing_external_data",
    "user_response": "User confirmed option (c): both modes",
    "reasoning": "No API keys in repo; user wants flexibility for test and prod",
    "confidence": "high",
    "risk_if_wrong": "low - explicit user confirmation"
  }
]
```

**Step 13: PM Returns Normal Decision**
```markdown
## PM Decision: SIMPLE MODE

### Task Groups Created

**Group A: Stripe Integration**
- Install Stripe SDK
- Create payment service with test/prod mode switching
- Implement checkout flow with Stripe
- Add environment variable configuration
- Write tests for both modes

### Next Action
Orchestrator should spawn 1 developer for Group A
```

**Step 14: Orchestrator Clears Clarification State**
```
bazinga-db: Update orchestrator state
- clarification_pending: false
- phase: planning_complete
```

**Step 15: Workflow Continues Normally**
```
👉 **ORCHESTRATOR**: Routing to Phase 2A (Simple Mode)
🔄 **ORCHESTRATOR**: Spawning Developer for Group A...

[Normal workflow proceeds]
```

---

**End of Document**
