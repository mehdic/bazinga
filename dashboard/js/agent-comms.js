/**
 * Agent Communications Module
 * Parses and displays agent communications from orchestration log
 */

const AgentComms = (function() {
    let currentLog = null;

    /**
     * Parse orchestration log entries
     */
    function parseLog(log) {
        if (!log || !log.entries) {
            return [];
        }

        const communications = [];

        log.entries.forEach(entry => {
            if (!entry.header) return;

            // Parse header: ## [TIMESTAMP] Iteration N - Agent Type (Group X)
            const headerMatch = entry.header.match(/##\s*\[([^\]]+)\]\s*Iteration\s*(\d+)\s*-\s*([^(]+)(?:\(Group\s*([^\)]+)\))?/);

            if (!headerMatch) return;

            const [, timestamp, iteration, agentType, groupId] = headerMatch;

            // Extract summary from content (first few lines after "Response:" or "Decision:")
            let summary = '';
            const contentText = entry.content.join('\n');

            // Look for response or decision sections
            const responseMatch = contentText.match(/###\s*(?:Response|Decision):\s*([^\n]+(?:\n(?!###)[^\n]+)*)/i);
            if (responseMatch) {
                summary = responseMatch[1].trim().split('\n').slice(0, 3).join(' ').substring(0, 200);
            }

            communications.push({
                timestamp,
                iteration: parseInt(iteration),
                agentType: agentType.trim(),
                groupId: groupId ? groupId.trim() : null,
                summary,
                fullContent: contentText,
                header: entry.header
            });
        });

        return communications.reverse(); // Most recent first
    }

    /**
     * Render communications list
     */
    function render(log) {
        currentLog = log;
        const container = document.getElementById('communication-container');
        if (!container) return;

        const communications = parseLog(log);

        if (communications.length === 0) {
            container.innerHTML = '<div class="placeholder"><p>No communications yet...</p></div>';
            return;
        }

        // Show last 10 communications
        const recentComms = communications.slice(0, 10);

        container.innerHTML = recentComms.map(comm => `
            <div class="communication-item" data-iteration="${comm.iteration}">
                <div class="comm-header">
                    <span class="comm-title">
                        Iteration ${comm.iteration} - ${comm.agentType}
                        ${comm.groupId ? `(Group ${comm.groupId})` : ''}
                    </span>
                    <span class="comm-time">${formatTimestamp(comm.timestamp)}</span>
                </div>
                <div class="comm-summary">
                    ${comm.summary || 'Click to view details...'}
                </div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.communication-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                showCommunicationDetail(recentComms[index]);
            });
        });
    }

    /**
     * Show communication detail in modal
     */
    function showCommunicationDetail(comm) {
        const modal = document.getElementById('communication-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = `${comm.header}`;

        // Render markdown content
        modalBody.innerHTML = `
            <div style="font-family: 'Monaco', 'Courier New', monospace; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; max-height: 60vh; overflow-y: auto;">
                ${escapeHtml(comm.fullContent)}
            </div>
        `;

        modal.classList.add('active');
    }

    /**
     * Format timestamp
     */
    function formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        } catch (e) {
            return timestamp;
        }
    }

    /**
     * Escape HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Update communications (called when log changes)
     */
    async function update() {
        try {
            const log = await DataLoader.fetchLog();
            render(log);
        } catch (error) {
            console.error('Error updating communications:', error);
        }
    }

    return {
        render,
        update,
        showCommunicationDetail
    };
})();
