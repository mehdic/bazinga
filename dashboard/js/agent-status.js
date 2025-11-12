/**
 * Agent Status Module
 * Displays current agent status and activity
 */

const AgentStatus = (function() {
    const AGENT_TYPES = ['developer', 'qa', 'tech_lead', 'pm'];
    const AGENT_ICONS = {
        developer: '🧑‍💻',
        qa: '🧪',
        tech_lead: '👔',
        pm: '📋'
    };
    const AGENT_NAMES = {
        developer: 'Developer',
        qa: 'QA Expert',
        tech_lead: 'Tech Lead',
        pm: 'Project Manager'
    };

    /**
     * Parse log to extract agent activities
     */
    function parseAgentActivities(log) {
        const activities = {
            developer: null,
            qa: null,
            tech_lead: null,
            pm: null
        };

        if (!log || !log.entries || log.entries.length === 0) {
            return activities;
        }

        const agentTypeMap = {
            'Project Manager': 'pm',
            'Developer': 'developer',
            'QA Expert': 'qa',
            'Tech Lead': 'tech_lead'
        };

        // Parse log entries in reverse (most recent first)
        for (let i = log.entries.length - 1; i >= 0; i--) {
            const entry = log.entries[i];
            const header = entry.header || '';

            // Parse header: ## [TIMESTAMP] Iteration N - Agent Type (Group X)
            const match = header.match(/##\s*\[([^\]]+)\]\s*Iteration\s*(\d+)\s*-\s*([^(]+)(?:\(Group\s*([^\)]+)\))?/);

            if (match) {
                const [, timestamp, iteration, agentType, groupId] = match;
                const agentKey = agentTypeMap[agentType.trim()];

                // Only record the most recent activity for each agent
                if (agentKey && !activities[agentKey]) {
                    activities[agentKey] = {
                        timestamp: timestamp.trim(),
                        iteration: parseInt(iteration),
                        groupId: groupId ? groupId.trim() : null,
                        agentType: agentType.trim()
                    };
                }
            }
        }

        return activities;
    }

    /**
     * Check if activity is recent (within 5 minutes)
     */
    function isRecentActivity(timestampStr) {
        try {
            const activityTime = new Date(timestampStr);
            const now = new Date();
            const diffMs = now - activityTime;
            const diffMinutes = diffMs / 60000;
            return diffMinutes <= 5; // Active if within last 5 minutes
        } catch (e) {
            return false;
        }
    }

    /**
     * Render agent status cards
     */
    function render(data, log = null) {
        const container = document.getElementById('agent-status-container');
        if (!container) return;

        if (!data.orchestrator_state) {
            container.innerHTML = '<div class="placeholder"><p>Waiting for orchestration to start...</p></div>';
            return;
        }

        const orchestratorState = data.orchestrator_state;
        const activities = log ? parseAgentActivities(log) : {};

        // Create agent cards
        const agentCards = AGENT_TYPES.map(agentType => {
            const activity = activities[agentType];

            if (activity && isRecentActivity(activity.timestamp)) {
                // Recently active agent
                const elapsed = calculateElapsed(activity.timestamp);
                return `
                    <div class="agent-card active">
                        <div class="agent-header">
                            <span class="agent-name">
                                ${AGENT_ICONS[agentType]} ${AGENT_NAMES[agentType]}
                            </span>
                            <span class="agent-state active">ACTIVE</span>
                        </div>
                        <div class="agent-details">
                            ${activity.groupId ? `
                                <div class="agent-detail-line">
                                    <strong>Working on:</strong> Group ${activity.groupId}
                                </div>
                            ` : ''}
                            <div class="agent-detail-line">
                                <strong>Iteration:</strong> ${activity.iteration}
                            </div>
                            <div class="agent-detail-line">
                                <strong>Active for:</strong> ${elapsed}
                            </div>
                        </div>
                    </div>
                `;
            } else if (activity) {
                // Was active, but not recently
                return `
                    <div class="agent-card idle">
                        <div class="agent-header">
                            <span class="agent-name">
                                ${AGENT_ICONS[agentType]} ${AGENT_NAMES[agentType]}
                            </span>
                            <span class="agent-state idle">IDLE</span>
                        </div>
                        <div class="agent-details">
                            <div class="agent-detail-line" style="color: #9ca3af;">
                                Last active: ${formatTime(activity.timestamp)}
                            </div>
                            ${activity.groupId ? `
                                <div class="agent-detail-line" style="color: #6e7681;">
                                    Last worked on: Group ${activity.groupId}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            } else {
                // Never active
                return `
                    <div class="agent-card idle">
                        <div class="agent-header">
                            <span class="agent-name">
                                ${AGENT_ICONS[agentType]} ${AGENT_NAMES[agentType]}
                            </span>
                            <span class="agent-state idle">IDLE</span>
                        </div>
                        <div class="agent-details">
                            <div class="agent-detail-line" style="color: #6e7681;">
                                Waiting for next task...
                            </div>
                        </div>
                    </div>
                `;
            }
        });

        container.innerHTML = agentCards.join('');

        // Also show recent decisions
        if (orchestratorState.decisions_log && orchestratorState.decisions_log.length > 0) {
            const recentDecisions = orchestratorState.decisions_log.slice(-3).reverse();
            const decisionsHtml = `
                <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
                    <h4 style="margin-bottom: 1rem; font-size: 0.95rem; color: var(--text-secondary);">Recent Decisions</h4>
                    ${recentDecisions.map(decision => `
                        <div style="background: var(--bg-tertiary); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 0.5rem; font-size: 0.85rem;">
                            <div style="color: var(--accent-primary); font-weight: 600; margin-bottom: 0.25rem;">
                                ${formatDecision(decision.decision)}
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.8rem;">
                                ${decision.reasoning}
                            </div>
                            <div style="color: var(--text-tertiary); font-size: 0.75rem; margin-top: 0.25rem;">
                                ${formatTime(decision.timestamp)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.innerHTML += decisionsHtml;
        }
    }

    /**
     * Calculate elapsed time
     */
    function calculateElapsed(startTime) {
        if (!startTime) return '0m';

        const start = new Date(startTime);
        const now = new Date();
        const diffMs = now - start;

        const minutes = Math.floor(diffMs / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);

        if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    }

    /**
     * Format time
     */
    function formatTime(timestamp) {
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
     * Format decision name
     */
    function formatDecision(decision) {
        return decision
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Update agent status (called when data changes)
     */
    function update(data) {
        render(data);
    }

    return {
        render,
        update
    };
})();
