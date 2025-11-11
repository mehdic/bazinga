/**
 * WebSocket Client Module
 * Handles real-time communication with the server
 */

const WebSocketClient = (function() {
    let ws = null;
    let reconnectAttempts = 0;
    let maxReconnectAttempts = 10;
    let reconnectDelay = 2000;
    let listeners = [];
    let connectionStatusCallback = null;

    /**
     * Connect to WebSocket server
     */
    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('Connecting to WebSocket:', wsUrl);

        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('✅ WebSocket connected');
            reconnectAttempts = 0;
            updateConnectionStatus('connected');
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);

                // Handle heartbeat
                if (data.type === 'pong') {
                    return;
                }

                // Notify all listeners
                listeners.forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error('Error in WebSocket listener:', error);
                    }
                });
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };

        ws.onclose = function() {
            console.log('❌ WebSocket closed');
            updateConnectionStatus('disconnected');
            attemptReconnect();
        };
    }

    /**
     * Attempt to reconnect
     */
    function attemptReconnect() {
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const delay = reconnectDelay * reconnectAttempts;
            console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);

            setTimeout(() => {
                connect();
            }, delay);
        } else {
            console.error('Max reconnect attempts reached');
            updateConnectionStatus('failed');
        }
    }

    /**
     * Send message to server
     */
    function send(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    /**
     * Add listener for incoming messages
     */
    function addListener(callback) {
        listeners.push(callback);
    }

    /**
     * Remove listener
     */
    function removeListener(callback) {
        listeners = listeners.filter(cb => cb !== callback);
    }

    /**
     * Set connection status callback
     */
    function onConnectionStatus(callback) {
        connectionStatusCallback = callback;
    }

    /**
     * Update connection status
     */
    function updateConnectionStatus(status) {
        if (connectionStatusCallback) {
            connectionStatusCallback(status);
        }
    }

    /**
     * Disconnect
     */
    function disconnect() {
        if (ws) {
            ws.close();
            ws = null;
        }
    }

    /**
     * Get connection state
     */
    function getState() {
        return ws ? ws.readyState : WebSocket.CLOSED;
    }

    /**
     * Start heartbeat to keep connection alive
     */
    function startHeartbeat() {
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                send({ type: 'ping' });
            }
        }, 30000); // Every 30 seconds
    }

    return {
        connect,
        send,
        addListener,
        removeListener,
        onConnectionStatus,
        disconnect,
        getState,
        startHeartbeat
    };
})();
