/**
 * Session Navigation Module
 * Handles session list and navigation in sidebar
 */

const SessionNav = (function() {
    let sessions = [];
    let currentSessionId = null;

    /**
     * Initialize session navigation
     */
    async function init() {
        await loadSessions();
        setupSidebarToggle();
    }

    /**
     * Load available sessions
     */
    async function loadSessions() {
        try {
            sessions = await DataLoader.fetchSessions();
            render();
        } catch (error) {
            console.error('Error loading sessions:', error);
            const container = document.getElementById('sessions-list');
            if (container) {
                container.innerHTML = '<div class="loading" style="color: #f85149;">Error loading sessions</div>';
            }
        }
    }

    /**
     * Render session list
     */
    function render() {
        const container = document.getElementById('sessions-list');
        if (!container) return;

        if (sessions.length === 0) {
            container.innerHTML = '<div class="loading">No sessions found</div>';
            return;
        }

        // Sort sessions: current first, then by start_time descending (latest to oldest)
        const sortedSessions = [...sessions].sort((a, b) => {
            // Current session always first
            if (a.is_current && !b.is_current) return -1;
            if (!a.is_current && b.is_current) return 1;

            // Then sort by start_time (latest first)
            const timeA = a.start_time || '';
            const timeB = b.start_time || '';

            // If both have timestamps, compare them
            if (timeA && timeB) {
                return timeB.localeCompare(timeA); // Descending (latest first)
            }

            // If only one has timestamp, prioritize it
            if (timeA && !timeB) return -1;
            if (!timeA && timeB) return 1;

            // Fallback to session_id comparison
            return b.session_id.localeCompare(a.session_id);
        });

        container.innerHTML = sortedSessions.map(session => {
            const isActive = session.session_id === currentSessionId || (currentSessionId === null && session.is_current);

            return `
                <div class="session-item ${isActive ? 'active' : ''}" data-session-id="${session.session_id}">
                    <div class="session-item-id">
                        ${session.is_current ? '🔴 ' : ''}${formatSessionId(session.session_id)}
                    </div>
                    <div class="session-item-time">
                        ${formatSessionTime(session.start_time)}
                    </div>
                    <div class="session-item-status ${session.status}">
                        ${session.status.toUpperCase()}
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers
        container.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.getAttribute('data-session-id');
                selectSession(sessionId);
            });
        });

        // Set current session if not set
        if (!currentSessionId && sortedSessions.length > 0) {
            const currentSession = sortedSessions.find(s => s.is_current) || sortedSessions[0];
            currentSessionId = currentSession.session_id;
        }
    }

    /**
     * Format session ID for display
     */
    function formatSessionId(sessionId) {
        // Remove 'bazinga_' prefix if present
        const cleaned = sessionId.replace('bazinga_', '');

        // If it's a timestamp format (YYYYMMDD_HHMMSS), format it nicely
        const timestampMatch = cleaned.match(/^(\d{8})_(\d{6})$/);
        if (timestampMatch) {
            const [, date, time] = timestampMatch;
            const year = date.substring(0, 4);
            const month = date.substring(4, 6);
            const day = date.substring(6, 8);
            const hour = time.substring(0, 2);
            const minute = time.substring(2, 4);

            return `${year}-${month}-${day} ${hour}:${minute}`;
        }

        // Otherwise return as-is (truncated if too long)
        return cleaned.length > 20 ? cleaned.substring(0, 20) + '...' : cleaned;
    }

    /**
     * Format session time
     */
    function formatSessionTime(timestamp) {
        if (!timestamp) return 'Unknown time';

        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (e) {
            return timestamp;
        }
    }

    /**
     * Select a session
     */
    async function selectSession(sessionId) {
        console.log('📂 Selecting session:', sessionId);
        currentSessionId = sessionId;

        // Update active state in UI
        document.querySelectorAll('.session-item').forEach(item => {
            if (item.getAttribute('data-session-id') === sessionId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Show loading indicator
        const mainContent = document.querySelector('.dashboard-container');
        if (mainContent) {
            mainContent.style.opacity = '0.5';
            mainContent.style.pointerEvents = 'none';
        }

        try {
            // TODO: Load session-specific data from API
            // For now, we only support current session (live data)
            // Historical session support could be added later
            console.log('🔄 Refreshing dashboard data...');

            // Reload current data
            if (window.Dashboard && window.Dashboard.refresh) {
                await window.Dashboard.refresh();
                console.log('✅ Dashboard refreshed successfully');
            } else {
                console.error('❌ Dashboard.refresh() not available');
            }
        } catch (error) {
            console.error('❌ Error refreshing dashboard:', error);
        } finally {
            // Remove loading indicator
            if (mainContent) {
                mainContent.style.opacity = '1';
                mainContent.style.pointerEvents = 'auto';
            }
        }
    }

    /**
     * Setup sidebar toggle
     */
    function setupSidebarToggle() {
        const sidebar = document.getElementById('sidebar');
        const toggleBtn = document.getElementById('sidebar-toggle');

        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');

                // Update toggle button
                if (sidebar.classList.contains('collapsed')) {
                    toggleBtn.textContent = '▶';
                } else {
                    toggleBtn.textContent = '◀';
                }
            });
        }
    }

    /**
     * Get current session ID
     */
    function getCurrentSessionId() {
        return currentSessionId;
    }

    return {
        init,
        loadSessions,
        render,
        selectSession,
        getCurrentSessionId
    };
})();
