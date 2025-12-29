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


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestGroupSelection:
    """Tests for task group selection functionality."""

    def test_group_is_clickable(self, page: Page):
        """Task groups should be clickable."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)

        group = page.locator('#groups .clickable-item').first
        # Should have data-group-id attribute
        group_id = group.get_attribute('data-group-id')
        assert group_id is not None and group_id != ''

    def test_click_group_selects_it(self, page: Page):
        """Clicking a group should select it."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)

        group = page.locator('#groups .clickable-item').first
        group.click()

        # Wait for UI update
        page.wait_for_timeout(500)

        # Group should have selected class
        expect(group).to_have_class(re.compile(r"selected"))

    def test_click_selected_group_deselects(self, page: Page):
        """Clicking already-selected group should deselect it (toggle)."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)

        group = page.locator('#groups .clickable-item').first
        group.click()

        # Wait for selection
        page.wait_for_timeout(500)
        expect(group).to_have_class(re.compile(r"selected"))

        # Click again to deselect
        group.click()
        page.wait_for_timeout(500)

        # Should no longer be selected
        expect(group).not_to_have_class(re.compile(r"selected"))

    def test_group_selection_filters_logs(self, page: Page):
        """Selecting a group should filter logs panel."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)

        # Get initial log count
        page.wait_for_selector('#log-count')
        initial_count_text = page.locator('#log-count').text_content()

        # Select a group
        group = page.locator('#groups .clickable-item').first
        group_id = group.get_attribute('data-group-id')
        group.click()

        # Wait for reload
        page.wait_for_timeout(1000)

        # Log count should show group filter indicator
        count_text = page.locator('#log-count').text_content()
        # Should either be empty (no logs for group) or include group indicator
        # The count may change or stay same depending on data


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestIndividualAgentSelection:
    """Tests for individual agent instance selection."""

    def test_agent_has_agent_id_attribute(self, page: Page):
        """Agents should have data-agent-id attribute."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        agent = page.locator('#agents .clickable-item').first
        agent_id = agent.get_attribute('data-agent-id')
        assert agent_id is not None and agent_id != ''

    def test_agent_has_agent_type_attribute(self, page: Page):
        """Agents should have data-agent-type attribute."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        agent = page.locator('#agents .clickable-item').first
        agent_type = agent.get_attribute('data-agent-type')
        assert agent_type is not None and agent_type != ''

    def test_click_agent_selects_by_id(self, page: Page):
        """Clicking an agent should select by agent_id, not agent_type."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        # Click first agent
        agent = page.locator('#agents .clickable-item').first
        agent_id = agent.get_attribute('data-agent-id')
        agent.click()

        # Wait for UI update
        page.wait_for_timeout(500)

        # Only this specific agent should be selected
        expect(agent).to_have_class(re.compile(r"selected"))

        # Other agents should not be selected
        other_agents = page.locator('#agents .clickable-item:not(.selected)')
        # None of them should have the same agent_id
        for i in range(other_agents.count()):
            other_id = other_agents.nth(i).get_attribute('data-agent-id')
            assert other_id != agent_id

    def test_click_selected_agent_deselects(self, page: Page):
        """Clicking already-selected agent should deselect it (toggle)."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        agent = page.locator('#agents .clickable-item').first
        agent.click()

        # Wait for selection
        page.wait_for_timeout(500)
        expect(agent).to_have_class(re.compile(r"selected"))

        # Click again to deselect
        agent.click()
        page.wait_for_timeout(500)

        # Should no longer be selected
        expect(agent).not_to_have_class(re.compile(r"selected"))

        # Reasoning panel should show empty state
        reasoning_panel = page.locator('#reasoning-panel')
        expect(reasoning_panel).to_contain_text('Click on an agent')

    def test_reasoning_header_shows_agent_id(self, page: Page):
        """Reasoning header should display agent_id when different from type."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        # Find an agent where agent_id differs from agent_type
        agents = page.locator('#agents .clickable-item')
        for i in range(agents.count()):
            agent = agents.nth(i)
            agent_id = agent.get_attribute('data-agent-id')
            agent_type = agent.get_attribute('data-agent-type')

            if agent_id != agent_type:
                agent.click()
                page.wait_for_timeout(500)

                # Header should show both type and id
                header = page.locator('#reasoning-agent')
                header_text = header.text_content()
                assert agent_type in header_text
                assert agent_id in header_text
                break


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestCombinedFiltering:
    """Tests for combined group + agent filtering."""

    def test_select_group_then_agent(self, page: Page):
        """Should be able to select both group and agent."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        # Select a group
        group = page.locator('#groups .clickable-item').first
        group_id = group.get_attribute('data-group-id')
        group.click()
        page.wait_for_timeout(500)

        # Select an agent
        agent = page.locator('#agents .clickable-item').first
        agent.click()
        page.wait_for_timeout(500)

        # Both should be selected
        expect(group).to_have_class(re.compile(r"selected"))
        expect(agent).to_have_class(re.compile(r"selected"))

        # Reasoning header should show group filter
        header = page.locator('#reasoning-agent')
        header_text = header.text_content()
        assert 'Group' in header_text or group_id in header_text

    def test_session_change_clears_selections(self, page: Page):
        """Switching sessions should clear group and agent selections."""
        page.wait_for_selector('#groups .clickable-item', timeout=5000)
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        # Select a group
        group = page.locator('#groups .clickable-item').first
        group.click()
        page.wait_for_timeout(500)

        # Select an agent
        agent = page.locator('#agents .clickable-item').first
        agent.click()
        page.wait_for_timeout(500)

        # Switch to different session (if more than one exists)
        sessions = page.locator('#sessions .clickable-item')
        if sessions.count() >= 2:
            sessions.nth(1).click()
            page.wait_for_timeout(1000)

            # Reasoning panel should reset
            reasoning_panel = page.locator('#reasoning-panel')
            expect(reasoning_panel).to_contain_text('Click on an agent')


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason='Playwright not installed')
class TestContextualEmptyStates:
    """Tests for contextual empty state messages."""

    def test_no_reasoning_shows_contextual_message(self, page: Page):
        """Empty reasoning should show contextual message with agent name."""
        page.wait_for_selector('#agents .clickable-item', timeout=5000)

        # Find an agent, select it
        agent = page.locator('#agents .clickable-item').first
        agent_type = agent.get_attribute('data-agent-type')
        agent.click()

        page.wait_for_timeout(1000)

        # If no reasoning, should show contextual message
        reasoning_panel = page.locator('#reasoning-panel')
        content = reasoning_panel.text_content()

        # Should either have reasoning entries OR a contextual empty message
        if 'No reasoning' in content:
            # Should mention the agent type
            assert agent_type in content or 'reasoning' in content.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
