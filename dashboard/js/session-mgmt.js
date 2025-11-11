// Session Management (Delete, Archive, Export, Compare)
class SessionManagement {
    constructor() {
        this.currentSessionId = null;
        this.setupEventListeners();
    }

    setCurrentSession(sessionId) {
        this.currentSessionId = sessionId;
    }

    setupEventListeners() {
        // Export button
        document.getElementById('export-session')?.addEventListener('click', () => {
            this.exportSession();
        });

        // Archive button
        document.getElementById('archive-session')?.addEventListener('click', () => {
            this.archiveSession();
        });

        // Delete button
        document.getElementById('delete-session')?.addEventListener('click', () => {
            this.deleteSession();
        });

        // Compare button
        document.getElementById('compare-sessions')?.addEventListener('click', () => {
            this.showComparisonModal();
        });

        // Comparison modal
        document.getElementById('run-comparison')?.addEventListener('click', () => {
            this.runComparison();
        });

        document.getElementById('close-comparison-modal')?.addEventListener('click', () => {
            document.getElementById('comparison-modal').style.display = 'none';
        });
    }

    async exportSession() {
        if (!this.currentSessionId) {
            alert('No session selected');
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}/export?format=json`);
            const session = await response.json();

            // Download as JSON
            const blob = new Blob([JSON.stringify(session, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `session_${this.currentSessionId}.json`;
            a.click();
            URL.revokeObjectURL(url);

            alert('Session exported successfully!');
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export session');
        }
    }

    async archiveSession() {
        if (!this.currentSessionId) {
            alert('No session selected');
            return;
        }

        if (!confirm(`Archive session ${this.currentSessionId}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}/archive`, {
                method: 'POST'
            });
            const result = await response.json();

            if (result.success) {
                alert('Session archived successfully!');
                // Refresh sessions list
                if (window.sessionSearch) {
                    window.sessionSearch.performSearch('');
                }
            } else {
                alert('Failed to archive session');
            }
        } catch (error) {
            console.error('Archive failed:', error);
            alert('Failed to archive session');
        }
    }

    async deleteSession() {
        if (!this.currentSessionId) {
            alert('No session selected');
            return;
        }

        if (!confirm(`Delete session ${this.currentSessionId}? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'DELETE'
            });
            const result = await response.json();

            if (result.success) {
                alert('Session deleted successfully!');
                // Refresh sessions list
                if (window.sessionSearch) {
                    window.sessionSearch.performSearch('');
                }
            } else {
                alert('Failed to delete session');
            }
        } catch (error) {
            console.error('Delete failed:', error);
            alert('Failed to delete session');
        }
    }

    async showComparisonModal() {
        const modal = document.getElementById('comparison-modal');
        const select1 = document.getElementById('compare-session1');
        const select2 = document.getElementById('compare-session2');

        // Load sessions list
        try {
            const response = await fetch('/api/sessions/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: '', filters: {} })
            });
            const result = await response.json();

            const options = result.sessions.map(s =>
                `<option value="${s.session_id}">${s.session_id} - ${new Date(s.timestamp).toLocaleString()}</option>`
            ).join('');

            select1.innerHTML = options;
            select2.innerHTML = options;

            modal.style.display = 'flex';
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    async runComparison() {
        const session1 = document.getElementById('compare-session1').value;
        const session2 = document.getElementById('compare-session2').value;

        if (!session1 || !session2) {
            alert('Please select two sessions to compare');
            return;
        }

        try {
            const response = await fetch('/api/sessions/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session1, session2 })
            });
            const comparison = await response.json();

            this.displayComparison(comparison);
        } catch (error) {
            console.error('Comparison failed:', error);
            alert('Failed to compare sessions');
        }
    }

    displayComparison(comparison) {
        const resultsDiv = document.getElementById('comparison-results');

        const html = `
            <h4>Comparison Results</h4>
            <div class="comparison-grid">
                <div class="comparison-col">
                    <h5>Session 1: ${comparison.session1.session_id}</h5>
                    <pre>${JSON.stringify(comparison.session1.data, null, 2)}</pre>
                </div>
                <div class="comparison-col">
                    <h5>Differences</h5>
                    <ul>
                        ${comparison.differences.map(diff => `
                            <li>
                                <strong>${diff.field}:</strong><br>
                                Session 1: ${JSON.stringify(diff.session1)}<br>
                                Session 2: ${JSON.stringify(diff.session2)}
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="comparison-col">
                    <h5>Session 2: ${comparison.session2.session_id}</h5>
                    <pre>${JSON.stringify(comparison.session2.data, null, 2)}</pre>
                </div>
            </div>
        `;

        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    }
}

// Initialize
window.sessionMgmt = new SessionManagement();
