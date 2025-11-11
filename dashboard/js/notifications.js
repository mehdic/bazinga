// Browser Notifications and Sound Alerts
class NotificationManager {
    constructor() {
        this.notificationPermission = 'default';
        this.lastSessionStatus = null;
        this.init();
    }

    async init() {
        await this.requestPermission();
    }

    async requestPermission() {
        if ('Notification' in window) {
            this.notificationPermission = await Notification.requestPermission();
        }
    }

    notify(title, body, options = {}) {
        const config = window.dashboardConfig?.get('browser_notifications');
        if (!config) return;

        if (this.notificationPermission === 'granted') {
            const notification = new Notification(title, {
                body,
                icon: '/assets/bazinga-icon.png',
                badge: '/assets/bazinga-badge.png',
                ...options
            });

            notification.onclick = () => {
                window.focus();
                notification.close();
            };
        }

        // Also play sound if enabled
        if (window.dashboardConfig?.get('notification_sound')) {
            this.playSound();
        }
    }

    playSound() {
        const audio = document.getElementById('notification-sound');
        if (audio) {
            audio.play().catch(err => console.log('Audio play failed:', err));
        }
    }

    onSessionComplete(sessionId) {
        this.notify(
            '✅ Session Complete',
            `Orchestration session ${sessionId} has completed successfully!`,
            { tag: 'session-complete' }
        );
    }

    onSessionFailed(sessionId, error) {
        this.notify(
            '❌ Session Failed',
            `Orchestration session ${sessionId} failed: ${error}`,
            { tag: 'session-failed' }
        );
    }

    onLongRunningSession(sessionId, duration) {
        this.notify(
            '⏱️ Long Running Session',
            `Session ${sessionId} has been running for ${duration} minutes`,
            { tag: 'long-running' }
        );
    }

    checkSessionStatus(data) {
        const status = data?.orchestrator_state?.status;

        if (!status || status === this.lastSessionStatus) {
            return;
        }

        const sessionId = data?.orchestrator_state?.session_id || 'current';

        switch (status) {
            case 'completed':
                this.onSessionComplete(sessionId);
                break;
            case 'failed':
                this.onSessionFailed(sessionId, 'Unknown error');
                break;
        }

        this.lastSessionStatus = status;
    }

    // Check for custom triggers
    checkCustomTriggers(data) {
        const triggers = window.dashboardConfig?.get('custom_triggers') || [];

        triggers.forEach(trigger => {
            if (this.evaluateTrigger(trigger, data)) {
                this.notify(
                    `🔔 ${trigger.name}`,
                    trigger.message,
                    { tag: `custom-${trigger.id}` }
                );
            }
        });
    }

    evaluateTrigger(trigger, data) {
        // Simple trigger evaluation logic
        // Can be extended based on requirements
        try {
            // Example: trigger when duration exceeds threshold
            if (trigger.type === 'duration') {
                const duration = data?.orchestrator_state?.duration || 0;
                return duration > trigger.threshold;
            }
            return false;
        } catch (error) {
            console.error('Trigger evaluation failed:', error);
            return false;
        }
    }
}

// Initialize
window.notificationManager = new NotificationManager();
