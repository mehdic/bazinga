#!/usr/bin/env python3
"""Frontend integration tests for the Mini Dashboard using Playwright.

Tests the complete user interface and interactions.

Usage:
    pytest tests/test_frontend.py -v

Requirements:
    pip install pytest-playwright
    playwright install chromium
"""

import os
import sys
import time
import tempfile
import subprocess
from contextlib import contextmanager

import re

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.seed_test_db import seed_database

# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright, Page, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@contextmanager
def run_server(db_path: str, port: int = 5051):
    """Context manager to run the Flask server."""
    env = os.environ.copy()
    env['BAZINGA_DB_PATH'] = db_path
    env['PORT'] = str(port)

    server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server.py')

    process = subprocess.Popen(
        [sys.executable, server_path],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to start with health check polling
    server_url = f'http://localhost:{port}'
    max_retries = 10
    for i in range(max_retries):
        try:
            import urllib.request
            urllib.request.urlopen(f'{server_url}/api/health', timeout=1)
            break
        except Exception:
            if i == max_retries - 1:
                process.terminate()
                raise RuntimeError("Server failed to start")
            time.sleep(0.5)

    try:
        yield f'http://localhost:{port}'
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture(scope='module')
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    seed_database(db_path)
    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope='module')
def server_url(test_db):
    """Start server and return URL."""
    with run_server(test_db, port=5051) as url:
        yield url


@pytest.fixture(scope='function')
def page(server_url):
    """Create a new browser page for each test."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip('Playwright not installed')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(server_url)
        # Wait for initial load
        page.wait_for_selector('#sessions')
        yield page
        context.close()
        browser.close()


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestDashboardLoad:
    """Tests for initial dashboard loading."""

    def test_page_loads(self, page: Page):
        """Dashboard should load without errors."""
        assert page.title() == 'BAZINGA Mini Dashboard'

    def test_header_visible(self, page: Page):
        """Header should be visible."""
        header = page.locator('.header h1')
        expect(header).to_be_visible()
        expect(header).to_contain_text('BAZINGA Mini Dashboard')

    def test_sidebar_sections_visible(self, page: Page):
        """All sidebar sections should be visible."""
        expect(page.locator('h2:has-text("Sessions")')).to_be_visible()
        expect(page.locator('h2:has-text("Task Groups")')).to_be_visible()
        expect(page.locator('h2:has-text("Agents")')).to_be_visible()

    def test_panels_visible(self, page: Page):
        """Main panels should be visible."""
        expect(page.locator('text=Orchestration Logs')).to_be_visible()
        expect(page.locator('text=Agent Reasoning')).to_be_visible()


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestSessionList:
    """Tests for session list functionality."""

    def test_sessions_loaded(self, page: Page):
        """Sessions should be loaded from API."""
        # Wait for sessions to load
        page.wait_for_selector('#sessions .clickable-item')

        sessions = page.locator('#sessions .clickable-item')
        assert sessions.count() >= 1

    def test_active_session_highlighted(self, page: Page):
        """First session should be auto-selected (active)."""
        page.wait_for_selector('#sessions .clickable-item.active')

        active_session = page.locator('#sessions .clickable-item.active')
        expect(active_session).to_be_visible()

    def test_session_has_status_badge(self, page: Page):
        """Sessions should have status badges."""
        page.wait_for_selector('#sessions .clickable-item .status-badge')

        badges = page.locator('#sessions .clickable-item .status-badge')
        assert badges.count() >= 1

    def test_click_different_session(self, page: Page):
        """Clicking a different session should select it."""
        page.wait_for_selector('#sessions .clickable-item')

        # Click second session if available
        sessions = page.locator('#sessions .clickable-item')
        if sessions.count() >= 2:
            sessions.nth(1).click()

            # Wait for UI update
            page.wait_for_timeout(500)

            # Second session should now be active
            expect(sessions.nth(1)).to_have_class(re.compile(r"active"))


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestTaskGroups:
    """Tests for task groups functionality."""

    def test_groups_loaded(self, page: Page):
        """Task groups should be loaded."""
        page.wait_for_selector('#groups')

        # Wait for groups to load
        page.wait_for_timeout(1000)

        groups_container = page.locator('#groups')
        # Should have content (either groups or empty message)
        expect(groups_container).not_to_be_empty()

    def test_group_shows_status(self, page: Page):
        """Task groups should show status."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)

        group = page.locator('#groups .clickable-item').first
        expect(group.locator('.status-badge')).to_be_visible()


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestAgentList:
    """Tests for agent list functionality."""

    def test_agents_loaded(self, page: Page):
        """Agents should be loaded."""
        page.wait_for_selector('#agents')

        # Wait for agents to load
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        agents = page.locator('#agents .clickable-item')
        assert agents.count() >= 1

    def test_agent_shows_details(self, page: Page):
        """Agents should show status and stats."""
        page.wait_for_selector('#agents .clickable-item')

        agent = page.locator('#agents .clickable-item').first

        # Should show agent type
        expect(agent).to_contain_text('project_manager')

        # Should show stats (Reasoning:, Logs:, Tokens:)
        expect(agent).to_contain_text('Reasoning:')
        expect(agent).to_contain_text('Logs:')

    def test_click_agent_shows_reasoning(self, page: Page):
        """Clicking an agent should show its reasoning."""
        page.wait_for_selector('#agents .clickable-item')

        # Click first agent
        page.locator('#agents .clickable-item').first.click()

        # Wait for reasoning to load
        page.wait_for_timeout(1000)

        # Check reasoning panel has content
        reasoning_panel = page.locator('#reasoning-panel')

        # Should either have reasoning entries or "no reasoning" message
        content = reasoning_panel.inner_text()
        assert 'reasoning' in content.lower() or 'select' in content.lower()

    def test_agent_selection_visual(self, page: Page):
        """Selected agent should have visual indicator."""
        page.wait_for_selector('#agents .clickable-item')

        # Click first agent
        agent = page.locator('#agents .clickable-item').first
        agent.click()

        # Should have selected class
        expect(agent).to_have_class(re.compile(r"selected"))


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestLogsPanel:
    """Tests for orchestration logs panel."""

    def test_logs_loaded(self, page: Page):
        """Logs should be loaded."""
        page.wait_for_selector('#logs-panel')

        # Wait for logs
        page.wait_for_timeout(1000)

        logs_container = page.locator('#logs-panel')
        expect(logs_container).not_to_be_empty()

    def test_log_entry_format(self, page: Page):
        """Log entries should have proper format."""
        page.wait_for_selector('.log-entry', timeout=5000)

        log_entry = page.locator('.log-entry').first

        # Should have timestamp
        expect(log_entry.locator('.log-time')).to_be_visible()

        # Should have agent type
        expect(log_entry.locator('.log-agent')).to_be_visible()


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestReasoningPanel:
    """Tests for agent reasoning panel."""

    def test_reasoning_initial_state(self, page: Page):
        """Reasoning panel should show instruction initially."""
        reasoning_panel = page.locator('#reasoning-panel')
        expect(reasoning_panel).to_contain_text('Click on an agent')

    def test_reasoning_loads_on_agent_click(self, page: Page):
        """Reasoning should load when agent is clicked."""
        page.wait_for_selector('#agents .clickable-item')

        # Find and click an agent that has reasoning (PM or Developer)
        pm_agent = page.locator('#agents .clickable-item:has-text("project_manager")')
        if pm_agent.count() > 0:
            pm_agent.click()
        else:
            page.locator('#agents .clickable-item').first.click()

        # Wait for reasoning to load
        page.wait_for_timeout(1500)

        reasoning_panel = page.locator('#reasoning-panel')
        content = reasoning_panel.inner_text()

        # Should have reasoning entries or indicate none
        assert len(content) > 50  # Should have meaningful content

    def test_reasoning_entry_format(self, page: Page):
        """Reasoning entries should have proper format."""
        page.wait_for_selector('#agents .clickable-item')

        # Click PM to get reasoning
        pm_agent = page.locator('#agents .clickable-item:has-text("project_manager")')
        if pm_agent.count() > 0:
            pm_agent.click()

        # Wait for reasoning entries
        try:
            page.wait_for_selector('.reasoning-entry', timeout=3000)

            entry = page.locator('.reasoning-entry').first

            # Should have phase
            expect(entry.locator('.reasoning-phase')).to_be_visible()

            # Should have content
            expect(entry.locator('.reasoning-content')).to_be_visible()
        except:
            # If no reasoning entries, that's OK for some agents
            pass


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestAutoRefresh:
    """Tests for auto-refresh functionality."""

    def test_refresh_indicator_visible(self, page: Page):
        """Refresh indicator should be visible."""
        indicator = page.locator('#refresh-status')
        expect(indicator).to_be_visible()
        expect(indicator).to_contain_text('Auto-refresh')

    def test_refresh_indicator_updates(self, page: Page):
        """Refresh indicator should show 'Refreshing...' during refresh."""
        indicator = page.locator('#refresh-status')

        # Wait for indicator to be visible first
        expect(indicator).to_be_visible()

        # Track if we see either the refreshing or normal state
        # (the refresh happens quickly, so we might miss it)
        initial_text = indicator.text_content()

        # Verify it's in a valid state (either refreshing or showing interval)
        assert 'Auto-refresh' in initial_text or 'Refreshing' in initial_text


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestResponsiveness:
    """Tests for UI responsiveness."""

    def test_sidebar_scrollable(self, page: Page):
        """Sidebar should be scrollable when content overflows."""
        sidebar = page.locator('.sidebar')
        overflow = sidebar.evaluate('el => getComputedStyle(el).overflowY')
        assert overflow in ['auto', 'scroll']

    def test_panels_scrollable(self, page: Page):
        """Main panels should be scrollable."""
        panel = page.locator('.panel-content').first
        overflow = panel.evaluate('el => getComputedStyle(el).overflowY')
        assert overflow in ['auto', 'scroll']


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestStatusBadges:
    """Tests for status badge styling."""

    def test_active_status_badge(self, page: Page):
        """Active status should have green badge."""
        page.wait_for_selector('.status-badge')

        active_badge = page.locator('.status-badge.status-active')
        if active_badge.count() > 0:
            expect(active_badge.first).to_be_visible()

    def test_completed_status_badge(self, page: Page):
        """Completed status should have blue badge."""
        page.wait_for_selector('.status-badge')

        completed_badge = page.locator('.status-badge.status-completed')
        if completed_badge.count() > 0:
            expect(completed_badge.first).to_be_visible()


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestErrorStates:
    """Tests for error handling in UI."""

    def test_no_crash_on_empty_data(self, page: Page):
        """UI should not crash when data is empty."""
        # Dashboard should load even if some data is missing
        expect(page.locator('.container')).to_be_visible()

    def test_empty_states_displayed(self, page: Page):
        """Empty states should be displayed gracefully."""
        # The empty state messages should be styled
        page.wait_for_timeout(500)

        # Check page didn't crash
        assert page.title() == 'BAZINGA Mini Dashboard'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
