/**
 * Zen Browser Bridge - Content Script (Chrome)
 *
 * This script runs on every page and handles:
 * - WebSocket connection to localhost:8766
 * - Message routing between WebSocket and background script
 * - DevTools integration
 */

(function() {
    'use strict';

    // Expose version and status in content script world (isolated)
    window.__INSPEKT_BRIDGE_VERSION__ = '4.2.1';
    window.__INSPEKT_BRIDGE_EXTENSION__ = true;
    window.__INSPEKT_BRIDGE_CSP_BLOCKED__ = false; // Extension bypasses CSP!

    // CRITICAL: Inject into MAIN world via background script
    // (inline script injection is blocked by CSP, even from content scripts)
    chrome.runtime.sendMessage({
        type: 'INJECT_MAIN_WORLD_VARS'
    }).then(() => {
        console.log('[Inspekt] Main world variables injected');
    }).catch(() => {
        // Background script might not be ready yet, that's okay
    });

    const WS_URL = 'ws://127.0.0.1:8766/ws';
    let ws = null;
    let reconnectTimer = null;
    const RECONNECT_DELAY = 3000;

    console.log('%c[Inspekt Extension]%c Loaded (CSP bypass enabled)',
        'color: #0066ff; font-weight: bold', 'color: inherit');

    function isFrontTab() {
        // Only consider a tab "front" if it's visible AND the top-level window
        return document.visibilityState === 'visible' && window === window.top;
    }

    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            return;
        }

        console.log('[Inspekt] Connecting to WebSocket server...');

        try {
            ws = new WebSocket(WS_URL);

            // Notify background script that we're connecting
            chrome.runtime.sendMessage({
                type: 'WS_STATUS_UPDATE',
                connected: 'connecting'
            }).catch(() => {
                // Background script might not be ready
            });

            ws.onopen = () => {
                console.log('%c[Inspekt]%c Connected via WebSocket',
                    'color: #0066ff; font-weight: bold', 'color: inherit');
                if (reconnectTimer) {
                    clearTimeout(reconnectTimer);
                    reconnectTimer = null;
                }
                window.__inspekt_ws__ = ws;

                // Notify background script of connection status
                chrome.runtime.sendMessage({
                    type: 'WS_STATUS_UPDATE',
                    connected: true
                }).catch(() => {
                    // Background script might not be ready
                });

                // Send browser info to server
                const browserInfo = {
                    type: 'browser_info',
                    userAgent: navigator.userAgent,
                    browserName: navigator.userAgentData?.brands?.[0]?.brand || 'Chrome',
                    url: window.location.href,
                    title: document.title
                };
                ws.send(JSON.stringify(browserInfo));
            };

            ws.onmessage = async (event) => {
                if (!isFrontTab()) {
                    return;
                }

                try {
                    const message = JSON.parse(event.data);

                    if (message.type === 'execute') {
                        const requestId = message.request_id;
                        const code = message.code;

                        try {
                            // Send to background script for CSP bypass execution
                            const response = await chrome.runtime.sendMessage({
                                type: 'EXECUTE_CODE',
                                code: code,
                                requestId: requestId
                            });

                            // Send result back via WebSocket
                            ws.send(JSON.stringify({
                                type: 'result',
                                request_id: requestId,
                                ok: response.ok,
                                result: response.result,
                                error: response.error,
                                url: location.href,
                                title: document.title || ''
                            }));
                        } catch (err) {
                            // If background script fails, send error back
                            console.error('[Inspekt] Background script error:', err);
                            ws.send(JSON.stringify({
                                type: 'result',
                                request_id: requestId,
                                ok: false,
                                result: null,
                                error: `Extension error: ${err.message}`,
                                url: location.href,
                                title: document.title || ''
                            }));
                        }

                    } else if (message.type === 'pong') {
                        // Keepalive response
                    }

                } catch (err) {
                    console.error('[Inspekt] Error handling message:', err);
                }
            };

            ws.onclose = (event) => {
                console.log('[Inspekt] Disconnected (code:', event.code, '). Reconnecting...');
                ws = null;
                window.__inspekt_ws__ = null;

                // Notify background script of disconnection
                chrome.runtime.sendMessage({
                    type: 'WS_STATUS_UPDATE',
                    connected: false
                }).catch(() => {
                    // Background script might not be ready
                });

                scheduleReconnect();
            };

            ws.onerror = (error) => {
                console.error('[Inspekt] WebSocket error:', error);
            };

        } catch (err) {
            console.error('[Inspekt] Failed to connect:', err);
            scheduleReconnect();
        }
    }

    function scheduleReconnect() {
        if (reconnectTimer) return;

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

    // Handle visibility changes to connect/disconnect appropriately
    document.addEventListener('visibilitychange', async () => {
        if (document.visibilityState === 'visible' && window === window.top) {
            // Tab became visible - connect if needed and domain is allowed
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                const allowed = await ZenPermissions.isAllowed();
                if (allowed) {
                    connect();
                }
            }
        } else if (document.visibilityState === 'hidden') {
            // Tab became hidden - disconnect to save resources
            if (ws && ws.readyState === WebSocket.OPEN) {
                console.log('[Inspekt] Tab hidden, closing connection');
                ws.close();
                ws = null;
                window.__inspekt_ws__ = null;
            }
        }
    });

    // DevTools integration is now injected via background script
    // (inline script injection is blocked by CSP)

    // Initial connection - only connect if this is a visible top-level tab AND domain is allowed
    async function initializeConnection() {
        if (isFrontTab()) {
            // Check if domain is allowed (will show opt-in modal if not)
            const allowed = await ZenPermissions.checkAndRequest();
            if (allowed) {
                console.log('[Inspekt] Domain authorized, connecting...');
                connect();
            } else {
                console.log('[Inspekt] Domain not authorized. Connection blocked.');
            }
        }
    }

    initializeConnection();

})();
