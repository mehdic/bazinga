#!/usr/bin/env python3
"""Seed a test database with simulated BAZINGA orchestration data.

This script creates a realistic test database with:
- Multiple sessions (active, completed, failed)
- Task groups with various statuses
- Orchestration logs (interactions and reasoning)
- Token usage data

Usage:
    python seed_test_db.py [output_path]

Default output: test_bazinga.db
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the BAZINGA database schema."""
    conn.executescript("""
        -- Sessions table
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            mode TEXT CHECK(mode IN ('simple', 'parallel')),
            original_requirements TEXT,
            status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
            initial_branch TEXT DEFAULT 'main',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Orchestration logs table
        CREATE TABLE IF NOT EXISTS orchestration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            iteration INTEGER,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            content TEXT NOT NULL,
            log_type TEXT DEFAULT 'interaction',
            reasoning_phase TEXT,
            confidence_level TEXT,
            references_json TEXT,
            redacted INTEGER DEFAULT 0,
            group_id TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        -- Task groups table
        CREATE TABLE IF NOT EXISTS task_groups (
            id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT CHECK(status IN (
                'pending', 'in_progress', 'completed', 'failed',
                'approved_pending_merge', 'merging'
            )) DEFAULT 'pending',
            assigned_to TEXT,
            revision_count INTEGER DEFAULT 0,
            last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
            feature_branch TEXT,
            merge_status TEXT,
            complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
            initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
            context_references TEXT,
            specializations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, session_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        -- Token usage table
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_type TEXT NOT NULL,
            agent_id TEXT,
            tokens_estimated INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        -- Skill outputs table
        CREATE TABLE IF NOT EXISTS skill_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            skill_name TEXT NOT NULL,
            output_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_logs_session ON orchestration_logs(session_id, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_logs_agent_type ON orchestration_logs(session_id, agent_type);
        CREATE INDEX IF NOT EXISTS idx_logs_reasoning ON orchestration_logs(session_id, log_type, reasoning_phase);
        CREATE INDEX IF NOT EXISTS idx_taskgroups_session ON task_groups(session_id, status);
        CREATE INDEX IF NOT EXISTS idx_tokens_session ON token_usage(session_id, agent_type);
    """)
    conn.commit()


def seed_sessions(conn: sqlite3.Connection) -> list:
    """Create test sessions."""
    now = datetime.now()

    sessions = [
        # Active session - currently running
        {
            'session_id': 'bazinga_20251225_100000_active',
            'start_time': (now - timedelta(minutes=30)).isoformat(),
            'end_time': None,
            'mode': 'simple',
            'original_requirements': 'Implement user authentication with JWT tokens and password hashing',
            'status': 'active',
            'initial_branch': 'main',
            'created_at': (now - timedelta(minutes=30)).isoformat()
        },
        # Completed session
        {
            'session_id': 'bazinga_20251225_080000_done',
            'start_time': (now - timedelta(hours=2)).isoformat(),
            'end_time': (now - timedelta(hours=1)).isoformat(),
            'mode': 'parallel',
            'original_requirements': 'Add REST API endpoints for user management with CRUD operations',
            'status': 'completed',
            'initial_branch': 'main',
            'created_at': (now - timedelta(hours=2)).isoformat()
        },
        # Failed session
        {
            'session_id': 'bazinga_20251224_150000_fail',
            'start_time': (now - timedelta(days=1)).isoformat(),
            'end_time': (now - timedelta(days=1, hours=-1)).isoformat(),
            'mode': 'simple',
            'original_requirements': 'Integrate with external payment API',
            'status': 'failed',
            'initial_branch': 'feature/payments',
            'created_at': (now - timedelta(days=1)).isoformat()
        },
        # Another completed session
        {
            'session_id': 'bazinga_20251223_120000_done',
            'start_time': (now - timedelta(days=2)).isoformat(),
            'end_time': (now - timedelta(days=2, hours=-2)).isoformat(),
            'mode': 'simple',
            'original_requirements': 'Refactor database models and add migrations',
            'status': 'completed',
            'initial_branch': 'main',
            'created_at': (now - timedelta(days=2)).isoformat()
        },
    ]

    for s in sessions:
        conn.execute("""
            INSERT INTO sessions (session_id, start_time, end_time, mode,
                                  original_requirements, status, initial_branch, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (s['session_id'], s['start_time'], s['end_time'], s['mode'],
              s['original_requirements'], s['status'], s['initial_branch'], s['created_at']))

    conn.commit()
    return sessions


def seed_task_groups(conn: sqlite3.Connection, sessions: list) -> None:
    """Create test task groups."""
    now = datetime.now()

    # Task groups for active session
    active_session = sessions[0]['session_id']
    task_groups = [
        {
            'id': 'AUTH',
            'session_id': active_session,
            'name': 'JWT Authentication',
            'status': 'in_progress',
            'assigned_to': 'developer_1',
            'revision_count': 0,
            'complexity': 6,
            'initial_tier': 'Developer',
            'created_at': (now - timedelta(minutes=25)).isoformat()
        },
        {
            'id': 'HASH',
            'session_id': active_session,
            'name': 'Password Hashing',
            'status': 'pending',
            'assigned_to': None,
            'revision_count': 0,
            'complexity': 4,
            'initial_tier': 'Developer',
            'created_at': (now - timedelta(minutes=25)).isoformat()
        },
    ]

    # Task groups for completed session
    completed_session = sessions[1]['session_id']
    task_groups.extend([
        {
            'id': 'API_CRUD',
            'session_id': completed_session,
            'name': 'User CRUD Endpoints',
            'status': 'completed',
            'assigned_to': 'developer_1',
            'revision_count': 1,
            'last_review_status': 'APPROVED',
            'complexity': 5,
            'initial_tier': 'Developer',
            'created_at': (now - timedelta(hours=2)).isoformat()
        },
        {
            'id': 'API_AUTH',
            'session_id': completed_session,
            'name': 'Auth Middleware',
            'status': 'completed',
            'assigned_to': 'developer_2',
            'revision_count': 0,
            'last_review_status': 'APPROVED',
            'complexity': 7,
            'initial_tier': 'Senior Software Engineer',
            'created_at': (now - timedelta(hours=2)).isoformat()
        },
    ])

    for tg in task_groups:
        conn.execute("""
            INSERT INTO task_groups (id, session_id, name, status, assigned_to,
                                     revision_count, last_review_status, complexity,
                                     initial_tier, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tg['id'], tg['session_id'], tg['name'], tg['status'],
              tg.get('assigned_to'), tg.get('revision_count', 0),
              tg.get('last_review_status'), tg.get('complexity'),
              tg.get('initial_tier'), tg['created_at']))

    conn.commit()


def seed_orchestration_logs(conn: sqlite3.Connection, sessions: list) -> None:
    """Create test orchestration logs (interactions and reasoning)."""
    now = datetime.now()
    active_session = sessions[0]['session_id']
    completed_session = sessions[1]['session_id']

    logs = []

    # === ACTIVE SESSION LOGS ===
    base_time = now - timedelta(minutes=30)

    # PM interaction
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=1)).isoformat(),
        'iteration': 1,
        'agent_type': 'project_manager',
        'agent_id': 'pm_1',
        'content': json.dumps({
            'status': 'PLANNING_COMPLETE',
            'mode': 'simple',
            'task_groups': ['AUTH', 'HASH'],
            'summary': 'Analyzed requirements. Created 2 task groups for authentication implementation.'
        }),
        'log_type': 'interaction',
        'group_id': None
    })

    # PM reasoning - understanding
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=1, seconds=30)).isoformat(),
        'iteration': 1,
        'agent_type': 'project_manager',
        'agent_id': 'pm_1',
        'content': '''Analyzing the requirements for JWT authentication implementation.

Key observations:
1. Need secure token generation and validation
2. Password hashing required for user credentials
3. Token refresh mechanism needed

Breaking down into logical task groups:
- AUTH: JWT token handling (generation, validation, refresh)
- HASH: Password hashing and verification

Complexity assessment:
- AUTH: 6/10 (moderate security considerations)
- HASH: 4/10 (standard bcrypt implementation)''',
        'log_type': 'reasoning',
        'reasoning_phase': 'understanding',
        'confidence_level': 'high',
        'references_json': json.dumps(['src/auth/', 'requirements.md']),
        'group_id': 'global'
    })

    # PM reasoning - completion
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=2)).isoformat(),
        'iteration': 1,
        'agent_type': 'project_manager',
        'agent_id': 'pm_1',
        'content': '''Planning phase complete.

Created task groups:
1. AUTH - JWT Authentication (complexity: 6, tier: Developer)
2. HASH - Password Hashing (complexity: 4, tier: Developer)

Recommended execution order: AUTH first (dependency for HASH tests)
Mode selected: simple (sequential execution appropriate for dependencies)''',
        'log_type': 'reasoning',
        'reasoning_phase': 'completion',
        'confidence_level': 'high',
        'group_id': 'global'
    })

    # Developer interaction
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=5)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_1',
        'content': json.dumps({
            'status': 'READY_FOR_QA',
            'group_id': 'AUTH',
            'files_modified': ['src/auth/jwt.py', 'src/auth/middleware.py'],
            'tests_written': 15,
            'summary': 'Implemented JWT token generation and validation with RS256 signing.'
        }),
        'log_type': 'interaction',
        'group_id': 'AUTH'
    })

    # Developer reasoning - understanding
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=5, seconds=30)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_1',
        'content': '''Understanding JWT authentication requirements.

Reviewed existing codebase:
- No existing auth implementation
- Using FastAPI framework
- Need to integrate with existing user model

Implementation plan:
1. Create JWT utility module with token generation/validation
2. Implement auth middleware for route protection
3. Add refresh token support
4. Write comprehensive tests

Security considerations:
- Use RS256 for asymmetric signing (more secure than HS256)
- Token expiry: 15 min access, 7 day refresh
- Store refresh tokens in httpOnly cookies''',
        'log_type': 'reasoning',
        'reasoning_phase': 'understanding',
        'confidence_level': 'high',
        'references_json': json.dumps(['src/models/user.py', 'src/main.py']),
        'group_id': 'AUTH'
    })

    # Developer reasoning - approach
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=8)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_1',
        'content': '''Selected implementation approach.

Architecture decisions:
- PyJWT library for token handling
- Dependency injection for auth service
- Pydantic models for token payloads

File structure:
src/auth/
├── jwt.py          # Token generation/validation
├── middleware.py   # FastAPI middleware
├── schemas.py      # Pydantic models
└── dependencies.py # FastAPI dependencies

Test coverage target: 90%+''',
        'log_type': 'reasoning',
        'reasoning_phase': 'approach',
        'confidence_level': 'high',
        'group_id': 'AUTH'
    })

    # Developer reasoning - completion
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=15)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_1',
        'content': '''Implementation complete for AUTH task group.

Deliverables:
- src/auth/jwt.py: Token generation with RS256, validation, refresh logic
- src/auth/middleware.py: FastAPI auth middleware with route protection
- tests/test_auth.py: 15 tests covering all scenarios

Key features:
- Access tokens (15 min expiry)
- Refresh tokens (7 day expiry, stored in httpOnly cookie)
- Token blacklisting for logout
- Role-based access control support

All tests passing. Ready for QA review.''',
        'log_type': 'reasoning',
        'reasoning_phase': 'completion',
        'confidence_level': 'high',
        'references_json': json.dumps(['src/auth/jwt.py', 'src/auth/middleware.py', 'tests/test_auth.py']),
        'group_id': 'AUTH'
    })

    # QA Expert interaction (in progress)
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=20)).isoformat(),
        'iteration': 3,
        'agent_type': 'qa_expert',
        'agent_id': 'qa_1',
        'content': json.dumps({
            'status': 'TESTING_IN_PROGRESS',
            'group_id': 'AUTH',
            'tests_run': 15,
            'tests_passed': 15,
            'coverage': 92,
            'summary': 'Running security-focused test challenges...'
        }),
        'log_type': 'interaction',
        'group_id': 'AUTH'
    })

    # QA reasoning - understanding
    logs.append({
        'session_id': active_session,
        'timestamp': (base_time + timedelta(minutes=20, seconds=30)).isoformat(),
        'iteration': 3,
        'agent_type': 'qa_expert',
        'agent_id': 'qa_1',
        'content': '''Reviewing JWT authentication implementation for testing.

Code review findings:
- Well-structured implementation following FastAPI best practices
- Good test coverage at 92%
- Security considerations properly addressed

Test strategy:
1. Boundary testing: Token expiry edge cases
2. Security testing: Invalid signatures, expired tokens, malformed JWTs
3. Integration testing: Full auth flow with middleware
4. Performance testing: Token generation under load''',
        'log_type': 'reasoning',
        'reasoning_phase': 'understanding',
        'confidence_level': 'high',
        'references_json': json.dumps(['src/auth/jwt.py', 'tests/test_auth.py']),
        'group_id': 'AUTH'
    })

    # === COMPLETED SESSION LOGS ===
    base_time_completed = now - timedelta(hours=2)

    # PM for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=2)).isoformat(),
        'iteration': 1,
        'agent_type': 'project_manager',
        'agent_id': 'pm_1',
        'content': json.dumps({
            'status': 'PLANNING_COMPLETE',
            'mode': 'parallel',
            'task_groups': ['API_CRUD', 'API_AUTH'],
            'summary': 'Created parallel task groups for REST API implementation.'
        }),
        'log_type': 'interaction',
        'group_id': None
    })

    # Developer 1 for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=30)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_1',
        'content': json.dumps({
            'status': 'READY_FOR_QA',
            'group_id': 'API_CRUD',
            'files_modified': ['src/api/users.py', 'src/models/user.py'],
            'tests_written': 24,
            'summary': 'Implemented CRUD endpoints for user management.'
        }),
        'log_type': 'interaction',
        'group_id': 'API_CRUD'
    })

    # Developer 2 for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=35)).isoformat(),
        'iteration': 2,
        'agent_type': 'developer',
        'agent_id': 'developer_2',
        'content': json.dumps({
            'status': 'READY_FOR_QA',
            'group_id': 'API_AUTH',
            'files_modified': ['src/middleware/auth.py'],
            'tests_written': 18,
            'summary': 'Implemented authentication middleware with role-based access.'
        }),
        'log_type': 'interaction',
        'group_id': 'API_AUTH'
    })

    # QA for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=50)).isoformat(),
        'iteration': 3,
        'agent_type': 'qa_expert',
        'agent_id': 'qa_1',
        'content': json.dumps({
            'status': 'PASS',
            'group_id': 'API_CRUD',
            'tests_run': 24,
            'tests_passed': 24,
            'coverage': 95,
            'summary': 'All tests passing with excellent coverage.'
        }),
        'log_type': 'interaction',
        'group_id': 'API_CRUD'
    })

    # Tech Lead for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=70)).isoformat(),
        'iteration': 4,
        'agent_type': 'tech_lead',
        'agent_id': 'tech_lead_1',
        'content': json.dumps({
            'status': 'APPROVED',
            'group_id': 'API_CRUD',
            'code_quality': 9,
            'security_score': 8,
            'summary': 'Code review passed. Well-structured implementation.'
        }),
        'log_type': 'interaction',
        'group_id': 'API_CRUD'
    })

    # Tech Lead reasoning
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=70, seconds=30)).isoformat(),
        'iteration': 4,
        'agent_type': 'tech_lead',
        'agent_id': 'tech_lead_1',
        'content': '''Code review for API_CRUD task group.

Evaluation:
- Architecture: Clean separation of concerns, follows REST principles
- Code quality: 9/10 - Well-documented, consistent style
- Security: 8/10 - Proper input validation, no SQL injection risks
- Performance: Good use of async/await, efficient queries

Minor suggestions (non-blocking):
- Consider adding rate limiting for create/update endpoints
- Add OpenAPI documentation comments

APPROVED for merge.''',
        'log_type': 'reasoning',
        'reasoning_phase': 'completion',
        'confidence_level': 'high',
        'group_id': 'API_CRUD'
    })

    # PM BAZINGA for completed session
    logs.append({
        'session_id': completed_session,
        'timestamp': (base_time_completed + timedelta(minutes=90)).isoformat(),
        'iteration': 5,
        'agent_type': 'project_manager',
        'agent_id': 'pm_1',
        'content': json.dumps({
            'status': 'BAZINGA',
            'summary': 'All task groups completed successfully. REST API implementation done.',
            'success_criteria_met': True
        }),
        'log_type': 'interaction',
        'group_id': None
    })

    # Insert all logs
    for log in logs:
        conn.execute("""
            INSERT INTO orchestration_logs
            (session_id, timestamp, iteration, agent_type, agent_id, content,
             log_type, reasoning_phase, confidence_level, references_json, group_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log['session_id'], log['timestamp'], log.get('iteration'),
            log['agent_type'], log.get('agent_id'), log['content'],
            log.get('log_type', 'interaction'), log.get('reasoning_phase'),
            log.get('confidence_level'), log.get('references_json'),
            log.get('group_id')
        ))

    conn.commit()


def seed_token_usage(conn: sqlite3.Connection, sessions: list) -> None:
    """Create test token usage data."""
    now = datetime.now()
    active_session = sessions[0]['session_id']
    completed_session = sessions[1]['session_id']

    token_data = [
        # Active session
        (active_session, 'project_manager', 'pm_1', 5000),
        (active_session, 'developer', 'developer_1', 15000),
        (active_session, 'qa_expert', 'qa_1', 8000),
        # Completed session
        (completed_session, 'project_manager', 'pm_1', 6000),
        (completed_session, 'developer', 'developer_1', 18000),
        (completed_session, 'developer', 'developer_2', 16000),
        (completed_session, 'qa_expert', 'qa_1', 12000),
        (completed_session, 'tech_lead', 'tech_lead_1', 10000),
    ]

    for session_id, agent_type, agent_id, tokens in token_data:
        conn.execute("""
            INSERT INTO token_usage (session_id, agent_type, agent_id, tokens_estimated)
            VALUES (?, ?, ?, ?)
        """, (session_id, agent_type, agent_id, tokens))

    conn.commit()


def seed_database(db_path: str) -> None:
    """Seed the complete test database."""
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create and populate
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print(f"Creating schema...")
    create_schema(conn)

    print(f"Seeding sessions...")
    sessions = seed_sessions(conn)

    print(f"Seeding task groups...")
    seed_task_groups(conn, sessions)

    print(f"Seeding orchestration logs...")
    seed_orchestration_logs(conn, sessions)

    print(f"Seeding token usage...")
    seed_token_usage(conn, sessions)

    # Verify counts
    session_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    log_count = conn.execute("SELECT COUNT(*) FROM orchestration_logs").fetchone()[0]
    group_count = conn.execute("SELECT COUNT(*) FROM task_groups").fetchone()[0]
    token_count = conn.execute("SELECT COUNT(*) FROM token_usage").fetchone()[0]

    reasoning_count = conn.execute(
        "SELECT COUNT(*) FROM orchestration_logs WHERE log_type = 'reasoning'"
    ).fetchone()[0]

    conn.close()

    print(f"\nDatabase seeded successfully: {db_path}")
    print(f"  Sessions: {session_count}")
    print(f"  Task groups: {group_count}")
    print(f"  Orchestration logs: {log_count} ({reasoning_count} reasoning entries)")
    print(f"  Token usage records: {token_count}")


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'test_bazinga.db'
    seed_database(db_path)
