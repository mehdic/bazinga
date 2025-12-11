# UI Message Templates

These are the standard message formats for displaying orchestration progress to users.

## 📍 Compact Progress Capsule Format (MANDATORY)

**All user-visible updates MUST use the capsule format:**

```
[Emoji] [Action/Phase] | [Key Observation] | [Decision/Outcome] → [Next Step]
```

**Rules:**
1. ✅ One capsule per major state transition
2. ✅ Include intent when spawning agents
3. ✅ Surface problems and solutions (not just status)
4. ✅ Link to artifacts for detail > 3 lines
5. ❌ Never output database operations
6. ❌ Never output role checks
7. ❌ Never output routing mechanics ("forwarding to...", "received from...")

---

## Initialization Messages

### Session Start (Basic - for simple requests)
```
🚀 Starting orchestration | Session: {session_id}
```

### Session Start (Enhanced - for complex requests)

**Use this format when the task involves multiple phases, spec files, or complex requirements:**

```markdown
🚀 **BAZINGA Orchestration Starting**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Session:** {session_id}
**Input:** {source_file_or_description}

**Workflow Overview:**
1. 📋 PM analyzes requirements → execution plan
2. 🔨 Developers implement in parallel
3. ✅ QA validates tests + coverage
4. 👔 Tech Lead reviews security + architecture
5. 📋 PM validates criteria → BAZINGA

Spawning Project Manager for analysis...
```

**Note:** Task count is determined by PM during analysis, not shown at init.

**Example:**
```markdown
🚀 **BAZINGA Orchestration Starting**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Session:** bazinga_20251125_114715
**Input:** tasks2.md

**Workflow Overview:**
1. 📋 PM analyzes requirements → execution plan
2. 🔨 Developers implement in parallel
3. ✅ QA validates tests + coverage
4. 👔 Tech Lead reviews security + architecture
5. 📋 PM validates criteria → BAZINGA

Spawning Project Manager for analysis...
```

---

## Planning Phase Messages

### Execution Plan Ready (After PM Planning)

**Use this format after PM completes planning to show the full execution plan:**

```markdown
📋 **Execution Plan Ready**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mode:** {mode} ({N} concurrent developers)
**Tasks:** {task_count} across {phase_count} phases

**Phases:**
> Phase 1: {phase_name} - Groups {group_ids}
> Phase 2: {phase_name} - Groups {group_ids}

**Success Criteria:**
• {criterion_1}
• {criterion_2}

**Starting:** Phase 1 with Groups {ids}
```

**Note:** Use markdown blockquotes (>) instead of box-drawing characters for terminal compatibility.

**Example:**
```markdown
📋 **Execution Plan Ready**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mode:** Parallel (3 concurrent developers)
**Tasks:** 12 across 2 phases

**Phases:**
> Phase 1: Foundation Setup - Groups A, B, C
>   • Group A: Database schema + models
>   • Group B: Authentication infrastructure
>   • Group C: Core API structure
>
> Phase 2: Feature Implementation - Groups D, E, F
>   • Group D: User management endpoints
>   • Group E: Product catalog service
>   • Group F: Order processing logic

**Success Criteria:**
• All tests passing (zero tolerance for failures)
• Coverage >70% on new code
• No high/critical security vulnerabilities

**Starting:** Phase 1 with Groups A, B, C
```

### Planning in Progress
```
📋 Analyzing requirements | {brief_context} | Planning execution strategy
```

**Example:**
```
📋 Analyzing requirements | JWT auth + user registration + password reset | Planning execution strategy
```

### Planning Complete - Simple Mode
```
📋 Planning complete | Single-group execution: {task_summary} | Starting development
```

**Example:**
```
📋 Planning complete | Single-group execution: JWT authentication (5 files, 12 tasks) | Starting development
```

### Planning Complete - Parallel Mode
```
📋 Planning complete | {N} parallel groups: {group_summaries} | Starting development → Groups {list}
```

**Example:**
```
📋 Planning complete | 3 parallel groups: JWT auth (5 files), User reg (3 files), Password reset (4 files) | Starting development → Groups A, B, C
```

### PM Needs Clarification
```
⚠️ PM needs clarification | {blocker_type}: {question_summary} | Awaiting response (auto-proceed with fallback in 5 min)
```

**Example:**
```
⚠️ PM needs clarification | Missing external data: Should we use Stripe test mode or production mode? | Awaiting response (auto-proceed with fallback in 5 min)
```

---

## Development Phase Messages

### Work in Progress
```
🔨 Group {id} [{tier}/{model}] implementing | {files_created/modified}, {tests_added} ({coverage}% coverage) | {current_status}
```

**Tier/Model notation:** `[SSE/Sonnet]` for Senior Software Engineer, `[Dev/Haiku]` for Developer. For backward compatibility, brackets are optional and may be omitted if tier/model information is unavailable.

**Examples:**
```
🔨 Group A [SSE/Sonnet] implementing | auth_middleware.py + jwt_utils.py created, 12 tests added (92% coverage) | Tests passing → QA review

🔨 Group B [Dev/Haiku] implementing | user_service.py in progress (8/12 tests passing) | Fixing validation edge cases

🔨 Group C [SSE/Sonnet] implementing | password_reset.py complete, coverage at 78% | Adding missing tests
```

### Developer Work Complete
```
🔨 Group {id} [{tier}/{model}] complete | {summary_of_work} | {status} → {next_phase}
```

**Examples:**
```
🔨 Group A [SSE/Sonnet] complete | JWT auth implemented in 3 files, 12 tests added (92% coverage) | No blockers → QA review

🔨 Group B [Dev/Haiku] complete | User registration with validation, 15 tests (88% coverage) | Ready → QA testing
```

---

## QA Phase Messages

### QA Testing
```
✅ Group {id} testing | Running {test_count} tests + coverage analysis | Validating implementation
```

**Example:**
```
✅ Group A testing | Running 12 tests + coverage analysis | Validating implementation
```

### QA Pass
```
✅ Group {id} tests passing | {test_results}, {coverage}% coverage, {quality_signals} | Approved → Tech Lead review
```

**Examples:**
```
✅ Group A tests passing | 12/12 tests passed, 92% coverage, security clear | Approved → Tech Lead review

✅ Group B tests passing | 15/15 tests passed, 88% coverage, no vulnerabilities | Approved → Code review
```

### QA Fail
```
⚠️ Group {id} QA failed | {failure_summary} → See {artifact_path} | Developer fixing
```

**Examples:**
```
⚠️ Group B QA failed | 3/15 tests failing (auth edge cases) → See bazinga/artifacts/{SESSION_ID}/qa_failures.md | Developer fixing

⚠️ Group C QA failed | 5 tests timeout (performance regression) → See bazinga/artifacts/{SESSION_ID}/qa_failures.md | Investigating
```

---

## Tech Lead Review Messages

### Review in Progress
```
👔 Group {id} reviewing | Security scan + lint check + architecture analysis | Evaluating quality
```

**Example:**
```
👔 Group A reviewing | Security scan + lint check + architecture analysis | Evaluating quality
```

### Review Approved
```
✅ Group {id} approved | {quality_summary} | Complete ({completed}/{total} groups)
```

**Examples:**
```
✅ Group A approved | Security clear, 0 lint issues, architecture solid | Complete (1/3 groups)

✅ Group B approved | 2 medium security issues fixed, all tests passing, code quality excellent | Complete (2/3 groups)
```

### Review - Changes Requested
```
⚠️ Group {id} needs revision | {issue_summary} | Fixes required → Developer
```

**Examples:**
```
⚠️ Group C needs revision | 1 high security issue (SQL injection) + 3 lint errors | Fixes required → Developer

⚠️ Group A needs revision | Test coverage below 80% (currently 72%) | Add missing tests → Developer
```

### Review - Escalation to Opus
```
🔬 Group {id} complexity detected | {reason_for_escalation} | Escalating to Opus → Tech Lead (Rev {N})
```

**Example:**
```
🔬 Group C complexity detected | Persistent architecture issues after 2 revisions | Escalating to Opus → Tech Lead (Rev 3)
```

### Review - Spawn Investigator
```
🔬 Group {id} investigation needed | {complex_issue_summary} | Spawning Investigator for deep analysis
```

**Example:**
```
🔬 Group C investigation needed | Intermittent test failures with unclear root cause | Spawning Investigator for deep analysis
```

### Technical Review Summary (NEW - Multi-group overview)

**Use this format when summarizing Tech Lead reviews for multiple groups:**

```markdown
👔 **Technical Review Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Group {id} ({name}):** {status_emoji} {status}
  • Security: {security_summary}
  • Architecture: {architecture_assessment}
  • Tests: {test_summary}

**Group {id} ({name}):** {status_emoji} {status}
  • Security: {security_summary}
  • Issue: {issue_if_any}

**Overall:** {completed}/{total} groups approved, {pending} pending
```

**Example:**
```markdown
👔 **Technical Review Summary**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Group A (Database Schema):** ✅ Approved
  • Security: 0 issues
  • Architecture: Clean migration pattern
  • Tests: 15/15 passing (89% coverage)

**Group B (Authentication):** ⚠️ Minor changes needed
  • Security: 1 medium (add rate limiting)
  • Will be addressed in next iteration

**Group C (Core API):** ✅ Approved
  • Security: 0 issues
  • Architecture: RESTful design, proper error handling
  • Tests: 22/22 passing (91% coverage)

**Overall:** 2/3 groups approved, 1 pending minor fixes
```

---

## Problem/Error Messages (Context Required)

All error messages must include: WHAT failed, WHY (if known), WHAT'S NEXT

### Security Issues Found
```
⚠️ Group {id} security scan | {severity_count} ({issue_types}) | {action} → See {artifact_path}
```

**Examples:**
```
⚠️ Group C security scan | 1 high (SQL injection), 2 medium (XSS) | Developer addressing → See bazinga/artifacts/{SESSION_ID}/skills/security_scan.json

⚠️ Group A security scan | 3 low severity issues (hardcoded strings) | Quick fixes applied → Re-scanning
```

### Coverage Gaps
```
⚠️ Group {id} coverage gaps | {files_below_threshold} → See {artifact_path} | {action}
```

**Example:**
```
⚠️ Group C coverage gaps | 2 files below 80% (password_reset: 72%, validators: 75%) → See bazinga/artifacts/{SESSION_ID}/skills/coverage_report.json | Adding tests
```

### Lint Issues
```
⚠️ Group {id} linting issues | {count} issues ({severity_breakdown}) → See {artifact_path} | {action}
```

**Example:**
```
⚠️ Group B linting issues | 12 issues (5 errors, 7 warnings) → See bazinga/artifacts/{SESSION_ID}/skills/lint_results.json | Auto-fixing
```

### Build Failure
```
❌ Build failed | {error_type} in {location} | Cannot proceed - fix required → {action}
```

**Example:**
```
❌ Build failed | Import error in auth_middleware.py:12 | Cannot proceed - fix required → Developer respawning
```

### Test Failure
```
⚠️ Tests failed in Group {id} | {failure_summary} | {action} → See {artifact_path}
```

**Example:**
```
⚠️ Tests failed in Group B | 3/15 auth edge cases failing | Developer fixing → See bazinga/artifacts/{SESSION_ID}/test_failures.md
```

### Iteration Loop Detected
```
⚠️ Group {id} iteration loop detected | {description} | {escalation_action}
```

**Example:**
```
⚠️ Group C iteration loop detected | Same review failures 3 times | Escalating to Opus + spawning Investigator
```

---

## Investigation Messages

### Investigator Spawned
```
🔬 Spawning Investigator | {problem_summary} | Expected: Root cause analysis + recommendations
```

**Example:**
```
🔬 Spawning Investigator | Group C intermittent test failures across 3 revisions | Expected: Root cause analysis + recommendations
```

### Investigation Complete - Root Cause Found
```
🔬 Investigation complete | Root cause: {diagnosis} | Solution: {fix_summary} → {next_action}
```

**Example:**
```
🔬 Investigation complete | Root cause: Race condition in async auth flow | Solution: Add proper locking mechanism → Developer implementing fix
```

### Investigation Complete - Need More Data
```
🔬 Investigation findings | {hypothesis_count} hypotheses identified | Next: {diagnostic_action} → Developer
```

**Example:**
```
🔬 Investigation findings | 2 hypotheses (race condition vs memory leak) | Next: Add diagnostic logging → Developer
```

---

## Completion Messages

### Group Complete (with Progress Tracking)
```
✅ Group {id} complete | {summary} | Progress: {completed}/{total} ({percentage}%) | → {next_step}
```

**Examples:**
```
✅ Group A complete | JWT auth | Progress: 5/69 (7%) | → QA review
✅ Group B complete | Database schema | Progress: 12/69 (17%) | → QA review
✅ Group Z complete | Final cleanup | Progress: 69/69 (100%) | → PM check
```

### Group Approved
```
✅ Group {id} approved | {quality_summary} | Complete ({completed}/{total} groups)
```

**Example:**
```
✅ Group A approved | Security clear, coverage 92%, all tests passing | Complete (1/3 groups done)
```

### All Groups Complete
```
✅ All groups complete | {total_groups}/{total_groups} groups approved, all quality gates passed | Final PM check → BAZINGA
```

**Example:**
```
✅ All groups complete | 3/3 groups approved, all quality gates passed | Final PM check → BAZINGA
```

### Session Complete
```
✅ BAZINGA - Orchestration Complete!
```

---

## Progress Summary Messages (Parallel Mode)

### Periodic Status Update
When multiple groups are working in parallel, show compact status table:

```
📊 Progress: {completed}/{total} groups complete
   ✅ Group A: Approved
   🔨 Group B: QA testing
   ⚠️ Group C: Fixing security issues (Rev 2)
```

**Example:**
```
📊 Progress: 1/3 groups complete
   ✅ Group A: Approved
   🔨 Group B: QA testing
   ⚠️ Group C: Fixing security issues (Rev 2)
```

---

## Summary vs Artifact Separation

**Principle:** Main transcript shows summaries. Details go to artifacts.

### What Goes in Main Transcript (Capsule Format)
- ✅ Phase transitions (planning → development → QA → review)
- ✅ Problems encountered (brief description)
- ✅ Solutions applied (brief description)
- ✅ Quality signals (tests passed, security clear, coverage %)
- ✅ Next actions (what's happening next)

### What Goes to Artifacts (Link Only in Transcript)
- 📄 Full test failure outputs → `artifacts/{SESSION_ID}/qa_failures.md`
- 📄 Security scan details → `artifacts/{SESSION_ID}/skills/security_scan.json`
- 📄 Coverage reports → `artifacts/{SESSION_ID}/skills/coverage_report.json`
- 📄 Lint results → `artifacts/{SESSION_ID}/skills/lint_results.json`
- 📄 Investigation reports → `artifacts/{SESSION_ID}/investigation_*.md`
- 📄 Agent full responses → Database logs (user doesn't see)

### Artifact Linking Pattern

When detail exceeds 3 lines, use summary + link:

```
[Emoji] [Summary] → See [artifact_path]

Examples:
⚠️ 12 linting issues found in Group B (5 errors, 7 warnings) → See bazinga/artifacts/{SESSION_ID}/skills/lint_results.json
⚠️ Coverage gaps in 2 files (password_reset: 72%, validators: 75%) → See bazinga/artifacts/{SESSION_ID}/skills/coverage_report.json
🔬 Investigation findings: 3 hypotheses, 12 diagnostic tests → See bazinga/artifacts/{SESSION_ID}/investigation_group_c.md
```

---

## Agent Report Format (Internal - Orchestrator Parses)

**IMPORTANT:** These structures show the **ideal data points** the orchestrator will attempt to parse from agent responses. Agents output free-form text; the orchestrator uses best-effort pattern matching to extract these fields. These are NOT mandatory output formats - agents can respond naturally and the parsing logic will adapt (see Phase 2 implementation in agents/orchestrator.md for parsing details).

Agents return structured data. Orchestrator extracts key info and transforms to capsule for user.

### Developer Report Structure
```yaml
status: READY_FOR_QA | BLOCKED | PARTIAL
summary: One sentence summary of work completed
problems_found: List of issues encountered and how resolved
files_modified: [file1.py, file2.js, ...]
files_created: [new_file1.py, ...]
tests_added: count
coverage: percentage
blockers: null | Description of any blocking issue
```

**Orchestrator transforms to:**
```
🔨 Group {id} complete | {summary}, {files} modified/created, {tests} tests added ({coverage}% coverage) | {status} → {next_phase}
```

### QA Report Structure
```yaml
status: PASS | FAIL | PARTIAL
tests_run: count
tests_passed: count
tests_failed: count
coverage: percentage
critical_failures: [test_name: reason, ...] | null
recommendation: APPROVE_FOR_REVIEW | REQUEST_CHANGES
```

**Orchestrator transforms to:**

If PASS:
```
✅ Group {id} tests passing | {passed}/{run} tests passed, {coverage}% coverage, {quality_signals} | Approved → Tech Lead review
```

If FAIL:
```
⚠️ Group {id} QA failed | {failed}/{run} tests failing ({failure_summary}) | Developer fixing → See bazinga/artifacts/{session}/qa_failures.md
```

### Tech Lead Report Structure
```yaml
status: APPROVED | CHANGES_REQUESTED | NEEDS_INVESTIGATION | ESCALATE_TO_OPUS | SPAWN_INVESTIGATOR
security_issues: {critical: N, high: N, medium: N, low: N}
lint_issues: {error: N, warning: N, info: N}
coverage: percentage
architecture_concerns: null | Brief description
decision: APPROVED | REQUEST_CHANGES | ESCALATE_TO_OPUS | SPAWN_INVESTIGATOR
reason: One sentence explanation
skill_results_summary: Brief summary of security/coverage/lint findings
escalation_reason: null | Why escalating/investigating
```

**Orchestrator transforms to:**

If APPROVED:
```
✅ Group {id} approved | {quality_summary} | Complete ({completed}/{total})
```

If CHANGES_REQUESTED:
```
⚠️ Group {id} needs revision | {issue_summary} | Fixes required → Developer
```

If ESCALATE_TO_OPUS:
```
🔬 Group {id} complexity detected | {escalation_reason} | Escalating to Opus → Tech Lead (Rev {N})
```

If SPAWN_INVESTIGATOR:
```
🔬 Group {id} investigation needed | {complex_issue} | Spawning Investigator for deep analysis
```

### PM Report Structure
```yaml
status: BAZINGA | CONTINUE | NEEDS_CLARIFICATION
decision: Final decision
assessment: Evaluation of completion
feedback: null | Specific feedback for next iteration
```

**Orchestrator transforms to:**

If BAZINGA:
```
✅ BAZINGA - Orchestration Complete!
[Shows final report]
```

If CONTINUE:
```
📋 PM check | {assessment} | {feedback} → {next_action}
```

If NEEDS_CLARIFICATION:
```
⚠️ PM needs clarification | {blocker_type}: {question} | Awaiting response
```

---

## Emoji Legend

- 🚀 - Session start
- 📋 - Planning / PM activity
- 🔨 - Development work
- ✅ - Success / approval / tests passing
- ⚠️ - Warning / issue detected / needs attention
- ❌ - Critical failure / blocker
- 👔 - Tech Lead review
- 🔬 - Investigation / deep analysis / escalation
- 📊 - Status summary / metrics

---

## Template Usage Examples

### Full Orchestration Flow Example

```
🚀 Starting orchestration | Session: bazinga_20251117_143530

📋 Planning complete | 3 parallel groups: JWT auth (5 files), User reg (3 files), Password reset (4 files) | Starting development → Groups A, B, C

🔨 Group A implementing | auth_middleware.py + jwt_utils.py + token_validator.py created, 12 tests added (92% coverage) | Tests passing → QA review
🔨 Group B implementing | user_service.py + validators.py created, 15 tests added (88% coverage) | Tests passing → QA review
🔨 Group C implementing | password_reset.py + email_service.py created, 9 tests added (78% coverage) | Tests passing → QA review

✅ Group A tests passing | 12/12 tests passed, 92% coverage, security clear | Approved → Tech Lead review
✅ Group B tests passing | 15/15 tests passed, 88% coverage, security clear | Approved → Tech Lead review
⚠️ Group C QA failed | Coverage below threshold (78% vs 80% target) | Adding edge case tests

✅ Group A approved | Security clear, 0 lint issues, architecture solid | Complete (1/3 groups)
✅ Group B approved | 2 medium security issues fixed, all tests passing, code quality excellent | Complete (2/3 groups)

🔨 Group C complete | Added 4 edge case tests, coverage now 85% | Ready → QA re-test

✅ Group C tests passing | 13/13 tests passed, 85% coverage, security clear | Approved → Tech Lead review

⚠️ Group C security scan | 1 high (SQL injection in password_reset.py:45) | Fixing with parameterized queries → See bazinga/artifacts/{SESSION_ID}/skills/security_scan.json

🔨 Group C complete | SQL injection fixed, re-scanned clean | Ready → Tech Lead re-review

✅ Group C approved | Security clear, coverage 85%, all quality gates passed | Complete (3/3 groups)

✅ All groups complete | 3/3 groups approved, all quality gates passed | Final PM check → BAZINGA

✅ BAZINGA - Orchestration Complete!
```

---

**Last Updated:** 2025-11-17
**Version:** 2.0 (Compact Capsule Format)
