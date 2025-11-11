/**
 * Main Dashboard Controller
 * Initializes and coordinates all dashboard modules
 */

const Dashboard = (function() {
    let isInitialized = false;
    let updateInterval = null;

    /**
     * Initialize dashboard
     */
    async function init() {
        if (isInitialized) return;

        console.log('🚀 Initializing BAZINGA Dashboard...');

        try {
            // Initialize Mermaid
            WorkflowViz.init();

            // Initialize session navigation
            await SessionNav.init();

            // Setup event listeners
            setupEventListeners();

            // Load initial data
            await loadData();

            // Setup WebSocket for real-time updates
            setupWebSocket();

            // Setup fallback polling (in case WebSocket fails)
            setupPolling();

            isInitialized = true;
            console.log('✅ Dashboard initialized');

        } catch (error) {
            console.error('❌ Error initializing dashboard:', error);
            showError('Failed to initialize dashboard. Check console for details.');
        }
    }

    /**
     * Load data from server
     */
    async function loadData() {
        try {
            // Load coordination data
            const data = await DataLoader.fetchData();
            updateDashboard(data);

            // Load orchestration log
            const log = await DataLoader.fetchLog();
            AgentComms.render(log);

        } catch (error) {
            console.error('Error loading data:', error);
            showError('Failed to load coordination data.');
        }
    }

    /**
     * Update dashboard with new data
     */
    function updateDashboard(data) {
        try {
            // Update header/session info
            updateSessionInfo(data);

            // Update progress
            updateProgress(data);

            // Update task groups
            updateTaskGroups(data);

            // Update workflow visualization
            WorkflowViz.update(data);

            // Update agent status
            AgentStatus.update(data);

            // Update quality metrics
            QualityMetrics.update(data);

            console.log('📊 Dashboard updated');

        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }

    /**
     * Update session info in header
     */
    function updateSessionInfo(data) {
        if (!data.orchestrator_state) return;

        const state = data.orchestrator_state;

        // Session ID
        const sessionIdEl = document.getElementById('session-id-text');
        if (sessionIdEl) {
            sessionIdEl.textContent = state.session_id || 'Unknown';
        }

        // Status
        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            const status = state.status || 'initializing';
            statusBadge.textContent = status.toUpperCase();
            statusBadge.className = 'status-badge ' + status;
        }

        // Start time
        const startTimeEl = document.getElementById('start-time');
        if (startTimeEl && state.start_time) {
            const date = new Date(state.start_time);
            startTimeEl.textContent = date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        }

        // Elapsed time
        const elapsedEl = document.getElementById('elapsed-time');
        if (elapsedEl && state.start_time) {
            const elapsed = calculateElapsedTime(state.start_time);
            elapsedEl.textContent = elapsed;
        }

        // Stats
        const iterationsEl = document.getElementById('total-iterations');
        if (iterationsEl) {
            iterationsEl.textContent = `${state.iteration || 0} iterations`;
        }

        const spawnsEl = document.getElementById('total-spawns');
        if (spawnsEl) {
            spawnsEl.textContent = `${state.total_spawns || 0} spawns`;
        }
    }

    /**
     * Update progress section
     */
    function updateProgress(data) {
        if (!data.pm_state) return;

        const pmState = data.pm_state;

        // Progress bar
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        if (progressFill && progressText) {
            const percentage = pmState.completion_percentage || 0;
            progressFill.style.width = `${percentage}%`;
            progressText.textContent = `${Math.round(percentage)}%`;
        }

        // Group counts
        const totalGroupsEl = document.getElementById('total-groups');
        if (totalGroupsEl && pmState.task_groups) {
            totalGroupsEl.textContent = Object.keys(pmState.task_groups).length;
        }

        const completedEl = document.getElementById('completed-groups');
        if (completedEl) {
            completedEl.textContent = pmState.completed_groups?.length || 0;
        }

        const inProgressEl = document.getElementById('inprogress-groups');
        if (inProgressEl) {
            inProgressEl.textContent = pmState.in_progress_groups?.length || 0;
        }

        const pendingEl = document.getElementById('pending-groups');
        if (pendingEl) {
            pendingEl.textContent = pmState.pending_groups?.length || 0;
        }

        // Current phase
        const phaseEl = document.getElementById('current-phase');
        if (phaseEl && data.orchestrator_state) {
            const phase = data.orchestrator_state.current_phase || 'initializing';
            phaseEl.textContent = phase.replace(/_/g, ' ').toUpperCase();
        }
    }

    /**
     * Update task groups
     */
    function updateTaskGroups(data) {
        const container = document.getElementById('groups-container');
        if (!container) return;

        if (!data.pm_state || !data.pm_state.task_groups) {
            container.innerHTML = '<div class="placeholder"><p>Waiting for task groups to be created...</p></div>';
            return;
        }

        const taskGroups = data.pm_state.task_groups;
        const groupStatus = data.group_status || {};

        const groupCards = Object.entries(taskGroups).map(([groupId, group]) => {
            const status = group.status || 'pending';
            const statusInfo = groupStatus[groupId] || {};

            // Build agent pipeline progress
            const iterations = statusInfo.iterations || {};
            const pipelineSteps = [
                { name: 'Dev', key: 'developer', completed: iterations.developer > 0 },
                { name: 'QA', key: 'qa', completed: iterations.qa > 0 },
                { name: 'TL', key: 'tech_lead', completed: iterations.tech_lead > 0 }
            ];

            const pipelineHtml = pipelineSteps.map(step => {
                let className = 'agent-step';
                if (step.completed) {
                    className += ' completed';
                } else if (status === 'in_progress' && !step.completed) {
                    // First incomplete step is active
                    const prevSteps = pipelineSteps.slice(0, pipelineSteps.indexOf(step));
                    if (prevSteps.every(s => s.completed)) {
                        className += ' active';
                    }
                }
                return `<span class="${className}">${step.name}</span>`;
            }).join('<span style="margin: 0 4px;">→</span>');

            return `
                <div class="group-card ${status}">
                    <div class="group-header">
                        <div>
                            <div class="group-title">
                                <span class="group-id">Group ${groupId}</span>: ${group.name}
                            </div>
                        </div>
                        <span class="group-status-badge ${status}">${status.replace('_', ' ')}</span>
                    </div>
                    <div class="group-detail">
                        <strong>Tasks:</strong> ${group.tasks?.join(', ') || 'N/A'}
                    </div>
                    <div class="group-detail">
                        <strong>Files:</strong> ${group.files?.join(', ') || 'N/A'}
                    </div>
                    <div class="group-detail">
                        <strong>Branch:</strong> ${group.branch_name || 'N/A'}
                    </div>
                    ${statusInfo.revision_count !== undefined ? `
                        <div class="group-detail">
                            <strong>Revisions:</strong> ${statusInfo.revision_count}
                            ${statusInfo.revision_count >= 3 ? '<span style="color: #d29922;"> (⚠️ Opus escalation)</span>' : ''}
                        </div>
                    ` : ''}
                    ${statusInfo.duration_minutes ? `
                        <div class="group-detail">
                            <strong>Duration:</strong> ${statusInfo.duration_minutes}m
                        </div>
                    ` : ''}
                    <div class="group-progress">
                        <div class="agent-pipeline">
                            ${pipelineHtml}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = groupCards;
    }

    /**
     * Setup WebSocket connection
     */
    function setupWebSocket() {
        // Set connection status callback
        WebSocketClient.onConnectionStatus((status) => {
            updateConnectionStatus(status);
        });

        // Add listener for data updates
        WebSocketClient.addListener((data) => {
            console.log('📡 Received WebSocket update');
            updateDashboard(data);

            // Also refresh communications log periodically
            if (Math.random() < 0.3) { // 30% chance to reduce load
                AgentComms.update();
            }
        });

        // Connect
        WebSocketClient.connect();

        // Start heartbeat
        WebSocketClient.startHeartbeat();
    }

    /**
     * Setup fallback polling
     */
    function setupPolling() {
        // Poll every 10 seconds as fallback
        updateInterval = setInterval(async () => {
            // Only poll if WebSocket is not connected
            if (WebSocketClient.getState() !== WebSocket.OPEN) {
                console.log('🔄 Polling for updates (WebSocket not connected)...');
                await loadData();
            }
        }, 10000);
    }

    /**
     * Update connection status indicator
     */
    function updateConnectionStatus(status) {
        const statusEl = document.getElementById('connection-status');
        const dotEl = statusEl?.querySelector('.status-dot');
        const textEl = statusEl?.querySelector('.status-text');

        if (!dotEl || !textEl) return;

        switch (status) {
            case 'connected':
                dotEl.className = 'status-dot connected';
                textEl.textContent = 'Connected';
                break;
            case 'disconnected':
                dotEl.className = 'status-dot disconnected';
                textEl.textContent = 'Disconnected';
                break;
            case 'error':
                dotEl.className = 'status-dot disconnected';
                textEl.textContent = 'Error';
                break;
            case 'failed':
                dotEl.className = 'status-dot disconnected';
                textEl.textContent = 'Connection Failed';
                break;
            default:
                dotEl.className = 'status-dot';
                textEl.textContent = 'Connecting...';
        }
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Refresh workflow button
        const refreshBtn = document.getElementById('refresh-workflow');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async () => {
                await WorkflowViz.refresh();
            });
        }

        // Generate AI diagram button
        const aiDiagramBtn = document.getElementById('generate-ai-diagram');
        if (aiDiagramBtn) {
            aiDiagramBtn.addEventListener('click', async () => {
                await WorkflowViz.generateAIDiagram();
            });
        }

        // Close AI diagram modal
        const closeAiModal = document.getElementById('close-ai-modal');
        if (closeAiModal) {
            closeAiModal.addEventListener('click', () => {
                document.getElementById('ai-diagram-modal').classList.remove('active');
            });
        }

        // Close communication modal
        const closeModal = document.getElementById('close-modal');
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                document.getElementById('communication-modal').classList.remove('active');
            });
        }

        // Close modals on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Update elapsed time every second
        setInterval(() => {
            const data = DataLoader.getCached().data;
            if (data?.orchestrator_state?.start_time) {
                const elapsedEl = document.getElementById('elapsed-time');
                if (elapsedEl) {
                    elapsedEl.textContent = calculateElapsedTime(data.orchestrator_state.start_time);
                }
            }
        }, 1000);
    }

    /**
     * Calculate elapsed time
     */
    function calculateElapsedTime(startTime) {
        const start = new Date(startTime);
        const now = new Date();
        const diffMs = now - start;

        const hours = Math.floor(diffMs / 3600000);
        const minutes = Math.floor((diffMs % 3600000) / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        console.error(message);
        // TODO: Add error notification UI
    }

    /**
     * Refresh dashboard
     */
    async function refresh() {
        await loadData();
    }

    /**
     * Cleanup
     */
    function destroy() {
        if (updateInterval) {
            clearInterval(updateInterval);
        }
        WebSocketClient.disconnect();
        isInitialized = false;
    }

    return {
        init,
        refresh,
        destroy
    };
})();

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        Dashboard.init();
    });
} else {
    Dashboard.init();
}

// Make Dashboard available globally
window.Dashboard = Dashboard;
