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
        console.log('📋 Parsing log for communications...', log);

        if (!log) {
            console.warn('No log provided');
            return [];
        }

        if (!log.entries || !Array.isArray(log.entries)) {
            console.warn('Log has no entries array:', log);
            return [];
        }

        console.log(`Found ${log.entries.length} log entries`);
        const communications = [];

        log.entries.forEach((entry, index) => {
            if (!entry.header) {
                console.warn(`Entry ${index} has no header`);
                return;
            }

            // Parse header: ## [TIMESTAMP] Iteration N - Agent Type (Group X)
            const headerMatch = entry.header.match(/##\s*\[([^\]]+)\]\s*Iteration\s*(\d+)\s*-\s*([^(]+)(?:\(Group\s*([^\)]+)\))?/);

            if (!headerMatch) {
                console.warn(`Entry ${index} header didn't match pattern:`, entry.header);
                return;
            }

            const [, timestamp, iteration, agentType, groupId] = headerMatch;

            // Ensure content is an array
            const contentArray = Array.isArray(entry.content) ? entry.content : [String(entry.content || '')];
            const contentText = contentArray.join('\n');

            // Extract summary with multiple fallback strategies
            let summary = '';

            // Strategy 1: Look for "Response:" or "Decision:" sections
            const responseMatch = contentText.match(/###\s*(?:Response|Decision):\s*([^\n]+(?:\n(?!###)[^\n]+)*)/i);
            if (responseMatch) {
                summary = responseMatch[1].trim().split('\n').slice(0, 3).join(' ').substring(0, 200);
            }

            // Strategy 2: Look for any section headers and take content after them
            if (!summary) {
                const sectionMatch = contentText.match(/###\s*[^:]+:\s*([^\n]+(?:\n(?!###)[^\n]+)*)/i);
                if (sectionMatch) {
                    summary = sectionMatch[1].trim().split('\n').slice(0, 3).join(' ').substring(0, 200);
                }
            }

            // Strategy 3: Take first non-empty lines
            if (!summary) {
                const nonEmptyLines = contentArray.filter(line => line.trim().length > 0);
                if (nonEmptyLines.length > 0) {
                    summary = nonEmptyLines.slice(0, 3).join(' ').substring(0, 200);
                }
            }

            // Strategy 4: Fallback to truncated full content
            if (!summary && contentText.trim()) {
                summary = contentText.trim().substring(0, 200);
            }

            communications.push({
                timestamp,
                iteration: parseInt(iteration),
                agentType: agentType.trim(),
                groupId: groupId ? groupId.trim() : null,
                summary: summary || 'View details...',
                fullContent: contentText || 'No content available',
                header: entry.header
            });
        });

        console.log(`✅ Parsed ${communications.length} communications`);
        return communications.reverse(); // Most recent first
    }

    /**
     * Render communications list
     */
    function render(log) {
        console.log('🖼️  Rendering communications...', log);
        currentLog = log;
        const container = document.getElementById('communication-container');

        if (!container) {
            console.error('❌ Communication container not found');
            return;
        }

        const communications = parseLog(log);

        if (communications.length === 0) {
            console.warn('No communications to display');
            container.innerHTML = `
                <div class="placeholder">
                    <p>No communications yet...</p>
                    <p style="font-size: 0.85rem; color: var(--text-tertiary); margin-top: 0.5rem;">
                        Communications will appear here when agents start working
                    </p>
                </div>
            `;
            return;
        }

        // Show last 10 communications
        const recentComms = communications.slice(0, 10);
        console.log(`📊 Displaying ${recentComms.length} communications`);

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
                    ${escapeHtml(comm.summary)}
                </div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.communication-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                showCommunicationDetail(recentComms[index]);
            });
        });

        console.log('✅ Communications rendered successfully');
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
