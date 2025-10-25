// ==UserScript==
// @name         Zen Browser Bridge (WebSocket)
// @namespace    zen-bridge
// @version      3.0
// @description  Execute JavaScript in the active tab via Zen CLI (WebSocket version)
// @match        *://*/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const WS_URL = 'ws://127.0.0.1:8766'; // WebSocket port
    let ws = null;
    let reconnectTimer = null;
    const RECONNECT_DELAY = 3000; // 3 seconds

    function isFrontTab() {
        // Only execute in the visible top-level frame
        return document.visibilityState === 'visible' && window === window.top;
    }

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            return; // Already connected
        }

        console.log('[Zen Bridge] Connecting to WebSocket server...');

        try {
            ws = new WebSocket(WS_URL);

            ws.onopen = () => {
                console.log('%c[Zen Bridge]%c Connected via WebSocket', 'color: #0066ff; font-weight: bold', 'color: inherit');
                // Clear reconnect timer if it exists
                if (reconnectTimer) {
                    clearTimeout(reconnectTimer);
                    reconnectTimer = null;
                }
            };

            ws.onmessage = async (event) => {
                if (!isFrontTab()) {
                    // Ignore messages if not front tab
                    return;
                }

                try {
                    const message = JSON.parse(event.data);

                    if (message.type === 'execute') {
                        // Execute code
                        const requestId = message.request_id;
                        const code = message.code;

                        let result, error = null;

                        try {
                            // Execute JavaScript in page context
                            result = (0, eval)(code);

                            // Await promises
                            if (result && typeof result.then === 'function') {
                                result = await result;
                            }
                        } catch (e) {
                            error = String(e && e.stack ? e.stack : e);
                        }

                        // Send result back
                        ws.send(JSON.stringify({
                            type: 'result',
                            request_id: requestId,
                            ok: !error,
                            result: error ? null : (typeof result === 'undefined' ? null : result),
                            error,
                            url: location.href,
                            title: document.title || ''
                        }));

                    } else if (message.type === 'pong') {
                        // Keepalive response
                    }

                } catch (err) {
                    console.error('[Zen Bridge] Error handling message:', err);
                }
            };

            ws.onclose = () => {
                console.log('[Zen Bridge] Disconnected. Reconnecting...');
                ws = null;
                scheduleReconnect();
            };

            ws.onerror = (error) => {
                console.error('[Zen Bridge] WebSocket error:', error);
            };

        } catch (err) {
            console.error('[Zen Bridge] Failed to connect:', err);
            scheduleReconnect();
        }
    }

    function scheduleReconnect() {
        if (reconnectTimer) return; // Already scheduled

        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connect();
        }, RECONNECT_DELAY);
    }

    // Keepalive ping every 30 seconds
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000);

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            // Tab became visible, ensure connection
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                connect();
            }
        }
    });

    // Initial connection
    if (isFrontTab()) {
        connect();
    }

})();
