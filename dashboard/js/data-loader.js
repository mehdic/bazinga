/**
 * Data Loader Module
 * Handles fetching and caching coordination data from the server
 */

const DataLoader = (function() {
    const API_BASE = window.location.origin;
    let cache = {
        data: null,
        log: null,
        sessions: null,
        lastUpdate: null
    };

    /**
     * Fetch all coordination data
     */
    async function fetchData() {
        try {
            const response = await fetch(`${API_BASE}/api/data`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            cache.data = data;
            cache.lastUpdate = Date.now();
            return data;
        } catch (error) {
            console.error('Error fetching coordination data:', error);
            throw error;
        }
    }

    /**
     * Fetch orchestration log
     */
    async function fetchLog() {
        try {
            const response = await fetch(`${API_BASE}/api/log`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const log = await response.json();
            cache.log = log;
            return log;
        } catch (error) {
            console.error('Error fetching orchestration log:', error);
            throw error;
        }
    }

    /**
     * Fetch available sessions
     */
    async function fetchSessions() {
        try {
            const response = await fetch(`${API_BASE}/api/sessions`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const sessions = await response.json();
            cache.sessions = sessions;
            return sessions;
        } catch (error) {
            console.error('Error fetching sessions:', error);
            throw error;
        }
    }

    /**
     * Request AI-generated workflow diagram
     */
    async function generateAIDiagram() {
        try {
            const response = await fetch(`${API_BASE}/api/ai-diagram`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error generating AI diagram:', error);
            throw error;
        }
    }

    /**
     * Get cached data
     */
    function getCached() {
        return cache;
    }

    /**
     * Clear cache
     */
    function clearCache() {
        cache = {
            data: null,
            log: null,
            sessions: null,
            lastUpdate: null
        };
    }

    return {
        fetchData,
        fetchLog,
        fetchSessions,
        generateAIDiagram,
        getCached,
        clearCache
    };
})();
