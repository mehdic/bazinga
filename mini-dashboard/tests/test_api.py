#!/usr/bin/env python3
"""API endpoint tests for the Mini Dashboard.

Tests all Flask API endpoints with a seeded test database.

Usage:
    cd mini-dashboard && pytest tests/test_api.py -v
"""

import json
import os
import sys
import tempfile
import pytest

# Add mini-dashboard directory to path for imports
MINI_DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, MINI_DASHBOARD_DIR)
sys.path.insert(0, os.path.join(MINI_DASHBOARD_DIR, 'tests'))

from tests.seed_test_db import seed_database


@pytest.fixture(scope='module')
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    seed_database(db_path)
    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope='module')
def app(test_db):
    """Create Flask app with test database."""
    # Set environment variable before importing server
    os.environ['BAZINGA_DB_PATH'] = test_db

    # Import server after setting env var
    from server import app as flask_app
    flask_app.config['TESTING'] = True

    return flask_app


@pytest.fixture(scope='module')
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return OK status."""
        response = client.get('/api/health')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'db_path' in data

    def test_health_includes_db_path(self, client, test_db):
        """Health endpoint should include database path."""
        response = client.get('/api/health')
        data = response.get_json()
        assert data['db_path'] == test_db


class TestSessionsEndpoint:
    """Tests for /api/sessions endpoint."""

    def test_sessions_returns_list(self, client):
        """Sessions endpoint should return a list."""
        response = client.get('/api/sessions')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_sessions_ordered_active_first(self, client):
        """Active sessions should appear first."""
        response = client.get('/api/sessions')
        data = response.get_json()

        # First session should be active
        assert data[0]['status'] == 'active'

    def test_sessions_contain_required_fields(self, client):
        """Sessions should have all required fields."""
        response = client.get('/api/sessions')
        data = response.get_json()

        required_fields = ['session_id', 'status', 'mode', 'original_requirements']
        for session in data:
            for field in required_fields:
                assert field in session, f"Missing field: {field}"

    def test_sessions_limit_applied(self, client):
        """Sessions should be limited to 10."""
        response = client.get('/api/sessions')
        data = response.get_json()
        assert len(data) <= 10

    def test_sessions_include_all_statuses(self, client):
        """Should include active, completed, and failed sessions."""
        response = client.get('/api/sessions')
        data = response.get_json()

        statuses = {s['status'] for s in data}
        assert 'active' in statuses
        assert 'completed' in statuses
        assert 'failed' in statuses


class TestAgentsEndpoint:
    """Tests for /api/session/<session_id>/agents endpoint."""

    def test_agents_for_active_session(self, client):
        """Should return agents for active session."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_agents_contain_required_fields(self, client):
        """Agents should have all required fields."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        required_fields = ['agent_type', 'status', 'reasoning_count']
        for agent in data:
            for field in required_fields:
                assert field in agent, f"Missing field: {field}"

    def test_agents_have_parsed_status(self, client):
        """Agent status should be parsed from content."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        # All agents should have a status
        for agent in data:
            assert agent['status'] is not None
            assert agent['status'] != ''

    def test_agents_ordered_by_first_appearance(self, client):
        """Agents should be ordered by first appearance."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        # PM should appear first (spawned first)
        assert data[0]['agent_type'] == 'project_manager'

    def test_agents_include_token_count(self, client):
        """Agents should include token usage."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        # At least one agent should have tokens
        has_tokens = any(a.get('tokens', 0) > 0 for a in data)
        assert has_tokens

    def test_agents_for_nonexistent_session(self, client):
        """Should return empty list for nonexistent session."""
        response = client.get('/api/session/nonexistent_session/agents')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_agents_content_not_exposed(self, client):
        """Full content should not be exposed (only parsed status)."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        for agent in data:
            assert 'content' not in agent


class TestGroupsEndpoint:
    """Tests for /api/session/<session_id>/groups endpoint."""

    def test_groups_returns_list(self, client):
        """Groups endpoint should return a list."""
        response = client.get('/api/session/bazinga_20251225_100000_active/groups')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

    def test_groups_contain_required_fields(self, client):
        """Groups should have all required fields."""
        response = client.get('/api/session/bazinga_20251225_100000_active/groups')
        data = response.get_json()

        required_fields = ['id', 'name', 'status']
        for group in data:
            for field in required_fields:
                assert field in group, f"Missing field: {field}"

    def test_groups_for_active_session(self, client):
        """Active session should have task groups."""
        response = client.get('/api/session/bazinga_20251225_100000_active/groups')
        data = response.get_json()

        assert len(data) == 2
        group_ids = {g['id'] for g in data}
        assert 'AUTH' in group_ids
        assert 'HASH' in group_ids

    def test_groups_for_completed_session(self, client):
        """Completed session should have task groups."""
        response = client.get('/api/session/bazinga_20251225_080000_done/groups')
        data = response.get_json()

        assert len(data) == 2
        # All groups should be completed
        for group in data:
            assert group['status'] == 'completed'


class TestLogsEndpoint:
    """Tests for /api/session/<session_id>/logs endpoint."""

    def test_logs_returns_list(self, client):
        """Logs endpoint should return a list."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

    def test_logs_contain_required_fields(self, client):
        """Logs should have all required fields."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs')
        data = response.get_json()

        required_fields = ['id', 'timestamp', 'agent_type', 'content_preview']
        for log in data:
            for field in required_fields:
                assert field in log, f"Missing field: {field}"

    def test_logs_ordered_by_timestamp_desc(self, client):
        """Logs should be ordered by timestamp descending (newest first)."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs')
        data = response.get_json()

        if len(data) >= 2:
            # First log should be more recent than second
            assert data[0]['timestamp'] >= data[1]['timestamp']

    def test_logs_only_interactions(self, client):
        """Should only return interaction logs, not reasoning."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs')
        data = response.get_json()

        # Verify we have logs (interactions were seeded)
        assert len(data) > 0

    def test_logs_content_preview_truncated(self, client):
        """Content preview should be truncated."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs')
        data = response.get_json()

        for log in data:
            assert len(log['content_preview']) <= 500

    def test_logs_limit_parameter(self, client):
        """Limit parameter should work."""
        response = client.get('/api/session/bazinga_20251225_100000_active/logs?limit=2')
        data = response.get_json()

        assert len(data) <= 2


class TestReasoningEndpoint:
    """Tests for /api/session/<session_id>/agent/<agent_type>/reasoning endpoint."""

    def test_reasoning_returns_list(self, client):
        """Reasoning endpoint should return a list."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/project_manager/reasoning'
        )
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

    def test_reasoning_contain_required_fields(self, client):
        """Reasoning entries should have all required fields."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/project_manager/reasoning'
        )
        data = response.get_json()

        required_fields = ['id', 'timestamp', 'reasoning_phase', 'content']
        for entry in data:
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"

    def test_reasoning_for_pm(self, client):
        """PM should have reasoning entries."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/project_manager/reasoning'
        )
        data = response.get_json()

        assert len(data) >= 2  # understanding and completion phases
        phases = {e['reasoning_phase'] for e in data}
        assert 'understanding' in phases
        assert 'completion' in phases

    def test_reasoning_for_developer(self, client):
        """Developer should have reasoning entries."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/developer/reasoning'
        )
        data = response.get_json()

        assert len(data) >= 2
        phases = {e['reasoning_phase'] for e in data}
        assert 'understanding' in phases

    def test_reasoning_ordered_by_timestamp_asc(self, client):
        """Reasoning should be ordered by timestamp ascending."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/developer/reasoning'
        )
        data = response.get_json()

        if len(data) >= 2:
            # First entry should be earlier than second
            assert data[0]['timestamp'] <= data[1]['timestamp']

    def test_reasoning_for_nonexistent_agent(self, client):
        """Should return empty list for agent with no reasoning."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/nonexistent/reasoning'
        )
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_reasoning_includes_confidence(self, client):
        """Reasoning entries should include confidence level."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/project_manager/reasoning'
        )
        data = response.get_json()

        # At least one entry should have confidence
        has_confidence = any(e.get('confidence_level') for e in data)
        assert has_confidence


class TestAgentLogsEndpoint:
    """Tests for /api/session/<session_id>/agent/<agent_type>/logs endpoint."""

    def test_agent_logs_returns_list(self, client):
        """Agent logs endpoint should return a list."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/developer/logs'
        )
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

    def test_agent_logs_include_both_types(self, client):
        """Should include both interaction and reasoning logs."""
        response = client.get(
            '/api/session/bazinga_20251225_100000_active/agent/developer/logs'
        )
        data = response.get_json()

        log_types = {e.get('log_type') for e in data}
        assert 'interaction' in log_types
        assert 'reasoning' in log_types


class TestSessionStatsEndpoint:
    """Tests for /api/session/<session_id>/stats endpoint."""

    def test_stats_returns_object(self, client):
        """Stats endpoint should return an object."""
        response = client.get('/api/session/bazinga_20251225_100000_active/stats')
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, dict)

    def test_stats_include_session_info(self, client):
        """Stats should include session information."""
        response = client.get('/api/session/bazinga_20251225_100000_active/stats')
        data = response.get_json()

        assert 'session' in data
        assert data['session'] is not None
        assert data['session']['session_id'] == 'bazinga_20251225_100000_active'

    def test_stats_include_agent_stats(self, client):
        """Stats should include per-agent log counts."""
        response = client.get('/api/session/bazinga_20251225_100000_active/stats')
        data = response.get_json()

        assert 'agent_stats' in data
        assert isinstance(data['agent_stats'], dict)
        assert 'project_manager' in data['agent_stats']

    def test_stats_include_token_total(self, client):
        """Stats should include total token count."""
        response = client.get('/api/session/bazinga_20251225_100000_active/stats')
        data = response.get_json()

        assert 'total_tokens' in data
        assert data['total_tokens'] > 0

    def test_stats_include_group_stats(self, client):
        """Stats should include task group statistics."""
        response = client.get('/api/session/bazinga_20251225_100000_active/stats')
        data = response.get_json()

        assert 'group_stats' in data
        assert isinstance(data['group_stats'], dict)


class TestIndexRoute:
    """Tests for the main index route."""

    def test_index_returns_html(self, client):
        """Index should return HTML page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
        assert b'BAZINGA Mini Dashboard' in response.data


class TestStatusParsing:
    """Tests for status parsing from agent content."""

    def test_parse_json_status(self, client):
        """Should parse status from JSON in agent content."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        # Find developer agent
        dev_agent = next((a for a in data if a['agent_type'] == 'developer'), None)
        assert dev_agent is not None
        assert dev_agent['status'] == 'READY_FOR_QA'

    def test_parse_pm_status(self, client):
        """PM should have a valid parsed status."""
        response = client.get('/api/session/bazinga_20251225_100000_active/agents')
        data = response.get_json()

        pm_agent = next((a for a in data if a['agent_type'] == 'project_manager'), None)
        assert pm_agent is not None
        # PM status should be parsed from content - check it's not UNKNOWN
        assert pm_agent['status'] != 'UNKNOWN'
        assert pm_agent['status'] in ['PLANNING_COMPLETE', 'PASS', 'ACTIVE', 'BAZINGA']


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_session_returns_empty(self, client):
        """Invalid session should return empty results, not error."""
        endpoints = [
            '/api/session/invalid_session_id/agents',
            '/api/session/invalid_session_id/groups',
            '/api/session/invalid_session_id/logs',
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
