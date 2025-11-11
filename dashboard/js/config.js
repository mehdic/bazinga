// Configuration Management
class DashboardConfig {
    constructor() {
        this.config = null;
        this.init();
    }

    async init() {
        await this.loadConfig();
        this.setupEventListeners();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            this.config = await response.json();
            return this.config;
        } catch (error) {
            console.error('Failed to load config:', error);
            return null;
        }
    }

    async saveConfig(newConfig) {
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            const result = await response.json();
            if (result.success) {
                this.config = result.config;
                this.applyConfig();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Failed to save config:', error);
            return false;
        }
    }

    applyConfig() {
        if (!this.config) return;

        // Apply theme
        document.body.setAttribute('data-theme', this.config.theme || 'dark');

        // Show/hide AI diagram button
        const aiBtn = document.getElementById('generate-ai-diagram');
        if (aiBtn) {
            aiBtn.style.display = this.config.ai_diagrams_enabled ? 'inline-block' : 'none';
        }
    }

    setupEventListeners() {
        // Config button
        const configBtn = document.getElementById('config-btn');
        const configModal = document.getElementById('config-modal');
        const closeBtn = document.getElementById('close-config-modal');
        const cancelBtn = document.getElementById('config-cancel');
        const saveBtn = document.getElementById('config-save');

        configBtn?.addEventListener('click', () => {
            this.showConfigModal();
        });

        closeBtn?.addEventListener('click', () => {
            configModal.style.display = 'none';
        });

        cancelBtn?.addEventListener('click', () => {
            configModal.style.display = 'none';
        });

        saveBtn?.addEventListener('click', async () => {
            await this.saveConfigFromModal();
        });
    }

    showConfigModal() {
        if (!this.config) return;

        const modal = document.getElementById('config-modal');

        // Populate form
        document.getElementById('config-ai-diagrams').checked = this.config.ai_diagrams_enabled || false;
        document.getElementById('config-browser-notifs').checked = this.config.browser_notifications || false;
        document.getElementById('config-sound-alerts').checked = this.config.notification_sound || false;
        document.getElementById('config-theme').value = this.config.theme || 'dark';
        document.getElementById('config-update-freq').value = this.config.update_frequency || 1000;
        document.getElementById('config-retention-days').value = this.config.session_retention_days || 30;

        // Email settings
        const emailConfig = this.config.email_notifications || {};
        document.getElementById('config-email-enabled').checked = emailConfig.enabled || false;
        document.getElementById('config-smtp-server').value = emailConfig.smtp_server || '';
        document.getElementById('config-smtp-port').value = emailConfig.smtp_port || 587;
        document.getElementById('config-from-email').value = emailConfig.from_email || '';
        document.getElementById('config-to-emails').value = (emailConfig.to_emails || []).join(', ');

        // Slack settings
        const slackConfig = this.config.slack_notifications || {};
        document.getElementById('config-slack-enabled').checked = slackConfig.enabled || false;
        document.getElementById('config-slack-webhook').value = slackConfig.webhook_url || '';

        modal.style.display = 'flex';
    }

    async saveConfigFromModal() {
        const newConfig = {
            ai_diagrams_enabled: document.getElementById('config-ai-diagrams').checked,
            browser_notifications: document.getElementById('config-browser-notifs').checked,
            notification_sound: document.getElementById('config-sound-alerts').checked,
            theme: document.getElementById('config-theme').value,
            update_frequency: parseInt(document.getElementById('config-update-freq').value),
            session_retention_days: parseInt(document.getElementById('config-retention-days').value),
            email_notifications: {
                enabled: document.getElementById('config-email-enabled').checked,
                smtp_server: document.getElementById('config-smtp-server').value,
                smtp_port: parseInt(document.getElementById('config-smtp-port').value),
                from_email: document.getElementById('config-from-email').value,
                to_emails: document.getElementById('config-to-emails').value
                    .split(',')
                    .map(e => e.trim())
                    .filter(e => e)
            },
            slack_notifications: {
                enabled: document.getElementById('config-slack-enabled').checked,
                webhook_url: document.getElementById('config-slack-webhook').value
            },
            custom_triggers: this.config.custom_triggers || []
        };

        const success = await this.saveConfig(newConfig);
        if (success) {
            document.getElementById('config-modal').style.display = 'none';
            alert('Configuration saved successfully!');
        } else {
            alert('Failed to save configuration. Please try again.');
        }
    }

    get(key) {
        return this.config ? this.config[key] : null;
    }
}

// Global instance
window.dashboardConfig = new DashboardConfig();
