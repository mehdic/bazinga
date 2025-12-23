# Clarification Flow Protocol

**Purpose:** Handle PM NEEDS_CLARIFICATION responses with hard cap enforcement
**When:** PM returns NEEDS_CLARIFICATION status

---

## Clarification State Machine

### State Fields (stored in orchestrator state)

| Field | Type | Description |
|-------|------|-------------|
| `clarification_used` | boolean | Has PM used their one clarification? |
| `clarification_resolved` | boolean | Has user responded to clarification? |
| `clarification_question` | string | PM's stored question for user |

---

## Step 1: Check Orchestrator State

```
Skill(command: "bazinga-db") → get-state {session_id} orchestrator
```

---

## Step 2: Evaluate State

### Case A: First Clarification Request

**IF `clarification_used = false` (or null/missing):**

1. **Allow the clarification** - PM gets ONE chance
2. **Store the question:**
   ```
   Skill(command: "bazinga-db") → save-state {session_id} orchestrator {
     "clarification_used": true,
     "clarification_resolved": false,
     "clarification_question": "{PM's question}"
   }
   ```
3. **Surface to user:** Display PM's question and wait for response
4. **Scope check is PAUSED** - This is the ONE allowed pause

### Case B: Clarification Pending (Awaiting User)

**IF `clarification_used = true` AND `clarification_resolved = false`:**

1. **Do NOT respawn PM** - Still waiting for user
2. **Surface the stored question** from `clarification_question` field
3. **Wait for user response**

### Case C: User Responded

**When user provides response:**

1. **Update state:**
   ```
   Skill(command: "bazinga-db") → save-state {session_id} orchestrator {
     "clarification_resolved": true,
     "user_clarification_response": "{user's response}"
   }
   ```
2. **Resume scope check** - No longer paused
3. **Respawn PM** with user's clarification included in context

### Case D: Hard Cap Exceeded

**IF `clarification_resolved = true` AND PM returns NEEDS_CLARIFICATION again:**

1. **HARD CAP EXCEEDED** - PM already used their one clarification
2. **DO NOT** surface another question to user
3. **AUTO-FALLBACK:** Respawn PM with fallback message:

```
Previous clarification was already provided. You MUST proceed with available information.
Make reasonable assumptions and document them. Do not request further clarification.
```

---

## Decision Flow Diagram

```
PM returns NEEDS_CLARIFICATION
         │
         ▼
┌─────────────────────────┐
│ clarification_used = ?  │
└─────────────────────────┘
         │
    ┌────┴────┐
    │         │
  false      true
    │         │
    ▼         ▼
 ALLOW    ┌───────────────────────┐
  └──►    │ clarification_resolved│
          └───────────────────────┘
                    │
              ┌─────┴─────┐
              │           │
            false        true
              │           │
              ▼           ▼
           WAIT      HARD CAP
         for user   AUTO-FALLBACK
```

---

## State Transitions

| Current State | Event | Next State | Action |
|---------------|-------|------------|--------|
| `used=false` | PM asks | `used=true, resolved=false` | Surface question |
| `used=true, resolved=false` | User responds | `used=true, resolved=true` | Resume with response |
| `used=true, resolved=true` | PM asks again | (same) | Auto-fallback, force proceed |

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| First NEEDS_CLARIFICATION | Allow, save question, wait for user |
| Awaiting user response | Surface stored question, wait |
| User responded | Update state, respawn PM with response |
| PM asks again after response | HARD CAP - auto-fallback, force proceed |
