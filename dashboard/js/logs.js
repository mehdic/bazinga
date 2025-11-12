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
            console.log('📋 Fetching logs from /api/logs/stream...');
            const response = await fetch(`/api/logs/stream?limit=${limit}`);

            console.log('Response status:', response.status, response.statusText);

            if (!response.ok) {
                const text = await response.text();
                console.error('Non-OK response:', text.substring(0, 200));
                this.container.textContent = `Error loading logs (${response.status}): ${response.statusText}\nTrying alternative endpoint...`;

                // Fallback: try to get logs from /api/log endpoint instead
                const logResponse = await fetch('/api/log');
                if (logResponse.ok) {
                    const logData = await logResponse.json();
                    if (logData.content) {
                        const lines = logData.content.split('\n');
                        const recentLines = lines.slice(-limit);
                        this.container.textContent = recentLines.join('\n');
                        console.log('✅ Logs loaded from fallback endpoint');
                        return;
                    }
                }
                throw new Error(`Server returned ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            console.log('Content-Type:', contentType);

            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error('Server returned HTML instead of JSON');
            }

            const result = await response.json();
            console.log('Logs result:', result);

            if (result.logs && result.logs.length > 0) {
                this.container.textContent = result.logs.join('\n');
                console.log(`✅ Loaded ${result.logs.length} log lines`);

                if (this.autoScroll) {
                    this.scrollToBottom();
                }
            } else {
                this.container.textContent = 'No logs available yet...\n\nLogs will appear here when orchestration starts.';
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.container.textContent = `Error loading logs: ${error.message}\n\nPlease check that the dashboard server is running and the orchestration log file exists.`;
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
