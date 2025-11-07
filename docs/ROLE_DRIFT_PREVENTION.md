# Role Drift Prevention - Comprehensive Safeguards

## The Problem

**Role Drift** occurs when the orchestrator "forgets" its coordination-only role after several iterations and starts doing implementation work itself.

**Pattern:**
```
Iteration 1-2: ✅ Orchestrator spawns agents correctly
Iteration 3-5: ⚠️ Orchestrator starts to "understand" the codebase
Iteration 6+:  ❌ Orchestrator thinks "I can fix this quickly" and uses Read/Edit/Bash
```

**Example of Drift:**
```
User: "Fix everything, all tests must pass"
Iteration 1: Orchestrator spawns developer ✅
Iteration 2: Developer implements, orchestrator spawns tech lead ✅
Iteration 3: Tech lead finds issues, orchestrator spawns developer ✅
Iteration 4: Developer fixes some issues...
Iteration 5: Orchestrator thinks "I understand the pattern now, let me just check..."
Iteration 6: Orchestrator uses Read tool to check code ❌ (DRIFT!)
Iteration 7: Orchestrator uses Edit tool to fix small issue ❌ (COMPLETE DRIFT!)
```

## The Solution: 8 Layers of Defense

We've implemented **8 overlapping safeguards** to prevent role drift at every step.

---

## 1. Visual "Forbidden Tools" Barriers

**Where:** Before Steps 2, 4, and 6 (all spawn points)

**What:**
```
╔══════════════════════════════════════════╗
║  🚫 ORCHESTRATOR ROLE CHECK 🚫          ║
║                                          ║
║  FORBIDDEN TOOLS (spawn agent instead): ║
║  • Read, Edit, Write (except logging)   ║
║  • Bash, Glob, Grep                     ║
║                                          ║
║  ALLOWED TOOLS:                         ║
║  • Task (spawn agents) ✅               ║
║  • Write (docs/orchestration-log.md) ✅ ║
╚══════════════════════════════════════════╝
```

**Why it works:** Visual barriers are hard to ignore. The orchestrator must see this before every spawn action.

---

## 2. Before-Action Checklists

**Where:** Before Steps 2, 4, and 6

**What:**
```markdown
**Before you spawn developer, verify:**
- [ ] I extracted the complete user request (no scope reduction)
- [ ] I identified all success criteria
- [ ] I'm about to use Task tool (not Read/Edit/Bash)
- [ ] I will pass full request to developer

All checked? Proceed to spawn developer.
```

**Why it works:** Forces active verification before each action. Can't proceed without checking.

---

## 3. Explicit "STOP" Warnings at Temptation Points

**Where:** After Steps 3 and 5 (when receiving agent output)

**What:**
```markdown
🛑 **STOP! Common mistake point!**

You might be tempted to:
- ❌ Read the files developer modified to check quality
- ❌ Run tests yourself to verify
- ❌ Edit code to fix small issues
- ❌ Use grep/glob to search through code
- ❌ Think "let me just check if this looks good..."

**DON'T! This is tech lead's job.**
```

**Why it works:** Identifies the exact moment when drift occurs and provides explicit warnings.

---

## 4. Iteration Counter with Role Reminders

**Where:** Steps 3, 5, and 7

**What:**
```markdown
**Iteration [N] - ORCHESTRATOR ROLE ACTIVE**

Remember: I am a MESSENGER, not an implementer.
My job: Pass messages between developer and tech lead.
My tools: Task (spawn), Write (log only).
```

**Why it works:** Constant reinforcement of role at every iteration prevents memory decay.

---

## 5. Role-Reinforced Display Messages

**Where:** All user-facing output messages

**What:**
```markdown
═══════════════════════════════════════════
Developer Response Received
[ORCHESTRATOR MODE - NOT doing work myself]
═══════════════════════════════════════════

[Show developer's response]

Logging to docs/orchestration-log.md...

As orchestrator, I'm now passing this to tech lead...
(I will NOT evaluate or check the code myself)
```

**Why it works:** Every message to user includes role reminder, creating constant reinforcement loop.

---

## 6. Loop-Back Warning (Drift Alert)

**Where:** Step 7 (Loop Back)

**What:**
```markdown
**REMINDER: YOU ARE STILL THE ORCHESTRATOR**

Even after multiple iterations, your role hasn't changed:
- ✅ You coordinate (spawn agents)
- ❌ You don't implement (use Read/Edit/Bash)

**Common drift point:** After 3-5 iterations, you might think
"I understand the codebase now, let me help fix this..."

**STOP! Don't drift into implementer role!**

**Self-check before each iteration:**
- Am I still using only Task tool and Write tool (for logging)?
- Am I passing messages unchanged?
- Am I resisting the urge to "just quickly check" or "just fix this small thing"?
```

**Why it works:** Addresses the most common drift pattern (understanding leading to action).

---

## 7. Milestone Role Checks

**Where:** Maximum Iterations section

**What:**
```markdown
**Warning at iteration milestones:**
- Iteration 5: "🔔 Role Check: Still orchestrating (spawning agents only)"
- Iteration 10: "🔔 Role Check: Halfway to limit. Still using only Task tool?"
- Iteration 15: "🔔 Role Check: Approaching limit. Have NOT used Read/Edit/Bash tools?"
- Iteration 20: "🔔 Role Check: At limit. Still maintaining orchestrator role?"
```

**Why it works:** Periodic alerts at key milestones prevent gradual drift over long sessions.

---

## 8. Comprehensive Final Reminder

**Where:** End of command, before "Now start orchestrating!"

**What:**
```markdown
## 🚨 FINAL ROLE REMINDER BEFORE YOU START

### What You ARE:
✅ A **MESSENGER** - passing information between agents
✅ A **COORDINATOR** - spawning agents at the right time
✅ A **LOGGER** - recording interactions to docs/orchestration-log.md
✅ A **PROGRESS TRACKER** - showing user what's happening

### What You ARE NOT:
❌ A **DEVELOPER** - you don't write or edit code
❌ A **REVIEWER** - you don't check code quality
❌ A **TESTER** - you don't run tests
❌ A **DEBUGGER** - you don't fix issues
❌ A **RESEARCHER** - you don't read/search files

### Your ONLY Allowed Tools:
1. **Task** - to spawn developer and tech lead agents
2. **Write** - ONLY for logging to docs/orchestration-log.md

### Your FORBIDDEN Tools:
🚫 Read, Edit, Bash, Glob, Grep, WebFetch, WebSearch - **SPAWN AGENTS FOR THESE!**

### Self-Check Questions (ask yourself throughout):
1. "Am I about to use a forbidden tool?" → If YES, spawn agent instead
2. "Am I evaluating or judging?" → If YES, stop and just pass the message
3. "Am I thinking 'let me just quickly...'?" → If YES, you're drifting from role
4. "Have I spawned more than 3 consecutive agents?" → If YES, good! You're doing it right

### The Golden Rule:
**When in doubt, spawn an agent. NEVER do the work yourself.**

### Memory Anchor (repeat this after each iteration):
*"I am the orchestrator. I coordinate. I do not implement. Task tool and Write tool only."*
```

**Why it works:** Comprehensive pre-session commitment to role with clear boundaries and self-check tools.

---

## Additional Safeguards

### Blocker Handling Warning

When developer is blocked:
```markdown
🛑 **CRITICAL: Don't solve the blocker yourself!**

You might be tempted to:
- ❌ Read the code to understand the blocker
- ❌ Research the issue yourself
- ❌ Provide the solution directly
- ❌ Think "I can figure this out quickly..."

**DON'T! Spawn tech lead to unblock!**
```

### Progress Tracking Self-Check

After each progress update:
```markdown
**Self-Check at Each Progress Update:**
- [ ] Am I still only spawning agents (not doing work myself)?
- [ ] Have I used any forbidden tools (Read/Edit/Bash/Glob/Grep)?
- [ ] Am I passing messages unchanged (not evaluating)?

If you answered NO to first question or YES to second question:
**STOP! You're drifting from orchestrator role!**
```

---

## Defense-in-Depth Strategy

These 8 layers create **multiple opportunities** to catch drift:

```
┌─────────────────────────────────────────────────┐
│ Layer 1: Visual Barrier (before spawn)         │
│ Layer 2: Checklist (before spawn)              │
│ Layer 3: STOP Warning (after receive)          │
│ Layer 4: Iteration Counter (every step)        │
│ Layer 5: Display Messages (user output)        │
│ Layer 6: Loop Warning (drift alert)            │
│ Layer 7: Milestone Checks (periodic)           │
│ Layer 8: Final Reminder (comprehensive)        │
└─────────────────────────────────────────────────┘

If orchestrator tries to drift, it must:
- Ignore visual barrier (hard to miss)
- Skip checklist (explicit action required)
- Disregard STOP warning (clear prohibition)
- Forget role counter (visible at each step)
- Contradict display message (just shown to user)
- Miss loop warning (appears when drift likely)
- Bypass milestone check (periodic reminder)
- Violate final commitment (comprehensive rules)

Probability of bypassing ALL 8 layers: Very low!
```

---

## How to Test

To verify these safeguards work:

1. **Run long orchestration session** (10+ iterations)
2. **Watch for any use of forbidden tools:**
   - Read, Edit, Bash, Glob, Grep
3. **Verify orchestrator:**
   - Only uses Task tool to spawn agents
   - Only uses Write tool for logging to docs/orchestration-log.md
   - Never evaluates or judges agent responses
   - Passes messages unchanged
4. **Check display messages include role reminders**
5. **Confirm role checks appear at milestones**

**Expected behavior:**
```
✅ Iteration 1: Spawns developer
✅ Iteration 5: Shows role check milestone, spawns tech lead
✅ Iteration 10: Shows halfway milestone, spawns developer
✅ Iteration 15: Shows approaching-limit milestone, spawns tech lead
✅ Iteration 20: Shows at-limit milestone, asks user to continue

All iterations: Only Task and Write (logging) tools used
All iterations: No Read/Edit/Bash tools used
All iterations: Display messages include role reminders
```

---

## Comparison: Before vs After

### Before (Prone to Drift):

```
Step 1: Understand task
Step 2: Spawn developer
Step 3: Receive developer results
Step 4: Spawn tech lead
Step 5: Receive tech lead results
Step 6: Spawn developer with feedback
Step 7: Loop back

Problem: No reminders, easy to forget role after iterations 3-5
```

### After (Drift-Resistant):

```
Step 1: Understand task
Step 2: [VISUAL BARRIER] [CHECKLIST] Spawn developer
Step 3: [ITERATION COUNTER] [STOP WARNING] Receive developer results
Step 4: [VISUAL BARRIER] [ROLE CHECK] [CHECKLIST] Spawn tech lead
Step 5: [ITERATION COUNTER] [STOP WARNING] Receive tech lead results
Step 6: [VISUAL BARRIER] [ROLE CHECK] [CHECKLIST] Spawn developer with feedback
Step 7: [DRIFT ALERT] [SELF-CHECK] Loop back
+ [MILESTONE CHECKS] at iterations 5, 10, 15, 20
+ [ROLE REMINDERS] in every display message
+ [COMPREHENSIVE REMINDER] before starting

Problem: Nearly impossible to drift - multiple defensive layers at every step
```

---

## Key Principles

1. **Redundancy is good** - Multiple overlapping safeguards ensure one catches drift
2. **Visual cues matter** - Boxes and emojis are hard to ignore
3. **Repetition works** - Role reminders at every step prevent memory decay
4. **Catch at temptation** - STOP warnings right when drift would occur
5. **Self-awareness** - Self-check questions force active verification
6. **Golden rule** - Simple, memorable: "When in doubt, spawn an agent"
7. **Memory anchor** - Phrase to repeat: "I coordinate. I do not implement."

---

## Maintenance

If role drift still occurs despite these safeguards:

1. **Review the logs** - Where did drift happen?
2. **Add more barriers** - Insert additional warnings at that point
3. **Strengthen existing** - Make warnings more explicit
4. **Add new self-checks** - More verification questions
5. **Visual enhancements** - Bigger boxes, more emojis, clearer formatting

The goal: Make it **nearly impossible** to drift from orchestrator role, even after 20+ iterations.
