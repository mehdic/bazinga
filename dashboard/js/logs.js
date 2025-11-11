// Real-Time Log Streaming
class LogStreamer {
    constructor() {
        this.container = document.getElementById('logs-content');
        this.autoScroll = true;
        this.refreshInterval = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('logs-refresh');
        const scrollBtn = document.getElementById('logs-scroll-bottom');
        const autoScrollCheck = document.getElementById('logs-autoscroll');

        refreshBtn?.addEventListener('click', () => {
            this.loadLogs();
        });

        scrollBtn?.addEventListener('click', () => {
            this.scrollToBottom();
        });

        autoScrollCheck?.addEventListener('change', (e) => {
            this.autoScroll = e.target.checked;
        });
    }

    async loadLogs(limit = 100) {
        try {
            const response = await fetch(`/api/logs/stream?limit=${limit}`);
            const result = await response.json();

            if (result.logs && result.logs.length > 0) {
                this.container.textContent = result.logs.join('\n');

                if (this.autoScroll) {
                    this.scrollToBottom();
                }
            } else {
                this.container.textContent = 'No logs available yet...';
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.container.textContent = 'Error loading logs: ' + error.message;
        }
    }

    scrollToBottom() {
        const logsContainer = document.getElementById('logs-container');
        if (logsContainer) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }

    startAutoRefresh(interval = 2000) {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            this.loadLogs();
        }, interval);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize
window.logStreamer = new LogStreamer();
