/**
 * Inspekt - Content Script (Firefox)
 *
 * This script runs on every page and handles:
 * - WebSocket connection to localhost:8766
 * - Message routing between WebSocket and background script
 * - DevTools integration
 */

(function() {
    'use strict';

    // Expose version and status in BOTH isolated world (content script) AND main world (page)
    // Content script world (for content script use)
    window.__ZEN_BRIDGE_VERSION__ = '4.0.0';
    window.__ZEN_BRIDGE_EXTENSION__ = true;
    window.__ZEN_BRIDGE_CSP_BLOCKED__ = false; // Extension bypasses CSP!

    // CRITICAL: Also inject into MAIN world so it's accessible when code is executed
    // via browser.tabs.executeScript (which runs in main world, not isolated world)
    const script = document.createElement('script');
    script.textContent = `
        window.__ZEN_BRIDGE_VERSION__ = '4.0.0';
        window.__ZEN_BRIDGE_EXTENSION__ = true;
        window.__ZEN_BRIDGE_CSP_BLOCKED__ = false;
    `;
    (document.head || document.documentElement).appendChild(script);
    script.remove();

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

            ws.onopen = () => {
                console.log('%c[Inspekt]%c Connected via WebSocket',
                    'color: #0066ff; font-weight: bold', 'color: inherit');
                if (reconnectTimer) {
                    clearTimeout(reconnectTimer);
                    reconnectTimer = null;
                }
                window.__zen_ws__ = ws;

                // Send browser info to server
                const browserInfo = {
                    type: 'browser_info',
                    userAgent: navigator.userAgent,
                    browserName: navigator.userAgentData?.brands?.[0]?.brand || 'Firefox',
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
                            const response = await browser.runtime.sendMessage({
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
                window.__zen_ws__ = null;
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
                window.__zen_ws__ = null;
            }
        }
    });

    // DevTools integration - inject into MAIN world so it's accessible in DevTools console
    const devToolsScript = document.createElement('script');
    devToolsScript.textContent = `
        if (typeof window.__ZEN_DEVTOOLS_MONITOR__ === 'undefined') {
            window.__ZEN_DEVTOOLS_MONITOR__ = true;

            window.zenStore = function(element) {
                if (element && element.nodeType === 1) {
                    window.__ZEN_INSPECTED_ELEMENT__ = element;
                    const tag = element.tagName.toLowerCase();
                    const id = element.id ? '#' + element.id : '';
                    const cls = element.className && typeof element.className === 'string' ?
                        '.' + element.className.split(' ').filter(c => c).join('.') : '';
                    console.log('%c[Inspekt]%c ✓ Element stored: <' + tag + id + cls + '>',
                        'color: #0066ff; font-weight: bold', 'color: #00aa00');
                    console.log('[Inspekt] Run in terminal: zen inspected');
                    return 'Stored: <' + tag + id + cls + '>';
                }
                console.error('[Inspekt] ✗ Invalid element. Usage: zenStore($0)');
                return 'ERROR: Please provide a valid element';
            };

            console.log('%c[Inspekt]%c DevTools integration ready',
                'color: #0066ff; font-weight: bold', 'color: inherit');
            console.log('[Inspekt] To capture inspected element:');
            console.log('  1. Right-click element → Inspect');
            console.log('  2. In DevTools Console: zenStore($0)');
            console.log('  3. In terminal: zen inspected');
            console.log('');
            console.log('%c[Inspekt]%c Extension mode: CSP restrictions bypassed! ✓',
                'color: #0066ff; font-weight: bold', 'color: #00aa00; font-weight: bold');
        }
    `;
    (document.head || document.documentElement).appendChild(devToolsScript);
    devToolsScript.remove();

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
