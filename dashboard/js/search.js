// Session Search and Filtering
class SessionSearch {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const searchInput = document.getElementById('search-input');
        const filterToggle = document.getElementById('filter-toggle');
        const filterPanel = document.getElementById('filter-panel');
        const applyFilters = document.getElementById('apply-filters');
        const clearFilters = document.getElementById('clear-filters');

        // Search input with debounce
        let searchTimeout;
        searchInput?.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });

        // Toggle filter panel
        filterToggle?.addEventListener('click', () => {
            filterPanel.style.display =
                filterPanel.style.display === 'none' ? 'flex' : 'none';
        });

        // Apply filters
        applyFilters?.addEventListener('click', () => {
            this.applyFilters();
        });

        // Clear filters
        clearFilters?.addEventListener('click', () => {
            this.clearFilters();
        });
    }

    async performSearch(query) {
        const filters = this.getCurrentFilters();

        try {
            const response = await fetch('/api/sessions/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, filters })
            });

            const result = await response.json();
            this.displaySearchResults(result.sessions);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    getCurrentFilters() {
        const filters = {};

        const status = document.getElementById('filter-status').value;
        if (status) filters.status = status;

        const dateFrom = document.getElementById('filter-date-from').value;
        if (dateFrom) filters.date_from = dateFrom;

        const dateTo = document.getElementById('filter-date-to').value;
        if (dateTo) filters.date_to = dateTo;

        return filters;
    }

    applyFilters() {
        const query = document.getElementById('search-input').value;
        this.performSearch(query);
    }

    clearFilters() {
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-date-from').value = '';
        document.getElementById('filter-date-to').value = '';
        document.getElementById('search-input').value = '';
        this.performSearch('');
    }

    displaySearchResults(sessions) {
        const sessionsList = document.getElementById('sessions-list');

        if (!sessions || sessions.length === 0) {
            sessionsList.innerHTML = '<div class="no-sessions">No sessions found</div>';
            return;
        }

        sessionsList.innerHTML = sessions.map(session => `
            <div class="session-item" data-session-id="${session.session_id}">
                <div class="session-item-header">
                    <span class="session-item-id">${session.session_id}</span>
                    <span class="session-item-status status-${session.status}">${session.status}</span>
                </div>
                <div class="session-item-time">${new Date(session.timestamp).toLocaleString()}</div>
            </div>
        `).join('');

        // Add click handlers
        sessionsList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.dataset.sessionId;
                this.loadSession(sessionId);
            });
        });
    }

    async loadSession(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            const session = await response.json();
            // Update dashboard with session data
            if (window.dataLoader) {
                window.dataLoader.updateWithSession(session);
            }
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    }
}

// Initialize
window.sessionSearch = new SessionSearch();
