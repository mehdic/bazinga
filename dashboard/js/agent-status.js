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
     * Render agent status cards
     */
    function render(data) {
        const container = document.getElementById('agent-status-container');
        if (!container) return;

        if (!data.orchestrator_state) {
            container.innerHTML = '<div class="placeholder"><p>Waiting for orchestration to start...</p></div>';
            return;
        }

        const orchestratorState = data.orchestrator_state;
        const activeAgents = orchestratorState.active_agents || [];
        const currentPhase = orchestratorState.current_phase || '';

        // Create agent cards
        const agentCards = AGENT_TYPES.map(agentType => {
            const active = activeAgents.find(a => a.agent_type === agentType);

            if (active) {
                // Active agent
                const elapsed = calculateElapsed(active.spawned_at);
                return `
                    <div class="agent-card active">
                        <div class="agent-header">
                            <span class="agent-name">
                                ${AGENT_ICONS[agentType]} ${AGENT_NAMES[agentType]}
                            </span>
                            <span class="agent-state active">ACTIVE</span>
                        </div>
                        <div class="agent-details">
                            ${active.group_id ? `
                                <div class="agent-detail-line">
                                    <strong>Working on:</strong> Group ${active.group_id}
                                </div>
                            ` : ''}
                            <div class="agent-detail-line">
                                <strong>Elapsed:</strong> ${elapsed}
                            </div>
                            ${active.spawned_at ? `
                                <div class="agent-detail-line">
                                    <strong>Started:</strong> ${formatTime(active.spawned_at)}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            } else {
                // Idle agent
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
