# Batch Processing Rules (Parallel Mode)

**🔴 CRITICAL: This is the PRIMARY FIX for the orchestrator-stopping bug.**

This template defines the MANDATORY batch processing workflow for parallel mode.

**Used by:** Orchestrator Step 2B.2a

---

## The Problem

In parallel mode, the orchestrator receives multiple responses simultaneously. Without proper batch processing, the orchestrator may:
- Process only one response and stop
- Serialize responses ("let me handle A first, then B")
- Leave groups unrouted

This causes the orchestrator-stopping bug.

---

## The Solution: Three-Step Batch Process

When you receive multiple developer/QA/Tech Lead responses in parallel mode, you MUST follow this three-step batch process:

### STEP 1: PARSE ALL RESPONSES FIRST

Before spawning ANY Task, parse ALL responses received in this orchestrator iteration:

```
Parse iteration:
- Developer A response → status = READY_FOR_QA
- Developer B response → status = PARTIAL (69 test failures)
- QA C response → status = READY_FOR_REVIEW
- Tech Lead D response → status = APPROVED
```

**DO NOT spawn Tasks yet.** Complete parsing first.

### STEP 2: BUILD SPAWN QUEUE FOR ALL GROUPS

After parsing ALL responses, build a complete spawn queue:

```
Spawn queue:
1. Group A: status=READY_FOR_QA → Spawn QA Expert A
2. Group B: status=PARTIAL → Spawn Developer B (continuation)
3. Group C: status=READY_FOR_REVIEW → Spawn Tech Lead C
4. Group D: status=APPROVED → Spawn Developer (merge) (Step 2B.7a), then Phase Continuation Check (Step 2B.7b)
```

**Status → Action Mapping:**
- READY_FOR_QA → QA Expert
- READY_FOR_REVIEW → Tech Lead
- APPROVED → Phase Continuation Check
- INCOMPLETE → Developer continuation
- PARTIAL → Developer continuation
- FAILED → Investigator
- BLOCKED → Investigator

### STEP 3: SPAWN ALL TASKS IN ONE MESSAGE BLOCK

**🔴 CRITICAL REQUIREMENT:** Spawn ALL Task calls in a SINGLE message response.

**DO NOT serialize** with "first... then..." language.

**CORRECT PATTERN:**

```
Received responses from Groups A, B, C.
Building spawn queue: QA A + Developer B + Tech Lead C
Spawning all agents in parallel:

[Task call for QA Expert A]
[Task call for Developer B continuation]
[Task call for Tech Lead C]
```

**All three Task calls MUST appear in ONE orchestrator message.**

---

## Forbidden Patterns

❌ **Serialization:** "Let me route Group C first, then I'll respawn Developer B"
- This creates stopping points and causes the bug
- You MUST route ALL groups in ONE message

❌ **Partial spawning:** Spawning only the first group and stopping
- Parse ALL → Build queue for ALL → Spawn ALL
- No exceptions

❌ **Deferred spawning:** "I'll handle the other groups next"
- There is no "next" - handle ALL groups NOW
- Build and spawn complete queue in this message

---

## Required Patterns

✅ **Batch processing:** Parse all → Build queue → Spawn all in ONE message

✅ **Parallel Task calls:** All Task invocations in same orchestrator response

✅ **Complete handling:** Every group gets routed, no groups left pending

---

## Enforcement Checklist

For each response received, verify the required action was taken:
- INCOMPLETE → Developer Task spawned
- PARTIAL → Developer Task spawned
- READY_FOR_QA → QA Expert Task spawned
- READY_FOR_REVIEW → Tech Lead Task spawned
- APPROVED → Developer (merge) spawned (Step 2B.7a), then Phase Continuation Check (Step 2B.7b) OR PM spawned
- BLOCKED → Investigator Task spawned
- FAILED → Investigator Task spawned

IF any response lacks its required action → VIOLATION (group not properly routed)

Step 2B.7b (Pre-Stop Verification) provides final safety net to catch any violations.

---

**This batch processing workflow is MANDATORY and prevents the root cause of the orchestrator-stopping bug.**
