// ==UserScript==
// @name         Zen Browser Bridge (WebSocket)
// @namespace    zen-bridge
// @version      3.4
// @description  Execute JavaScript in the active tab via Zen CLI (WebSocket version)
// @match        *://*/*
// @run-at       document-idle
// @grant        none
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    // Expose version for CLI to read
    window.__ZEN_BRIDGE_VERSION__ = '3.4';

    const WS_URL = 'ws://127.0.0.1:8766/ws'; // WebSocket URL
    let ws = null;
    let reconnectTimer = null;
    const RECONNECT_DELAY = 3000; // 3 seconds

    // Store WebSocket globally so it persists across page navigations
    window.__zen_ws__ = null;

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
                // Store globally
                window.__zen_ws__ = ws;
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

            ws.onclose = (event) => {
                console.log('[Zen Bridge] Disconnected (code:', event.code, 'reason:', event.reason || 'none', '). Reconnecting...');
                ws = null;
                window.__zen_ws__ = null;
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

    // DevTools integration: Helper to store inspected elements
    if (typeof window.__ZEN_DEVTOOLS_MONITOR__ === 'undefined') {
        window.__ZEN_DEVTOOLS_MONITOR__ = true;

        // Expose zenStore function for manual element capture
        window.zenStore = function(element) {
            if (element && element.nodeType === 1) {
                window.__ZEN_INSPECTED_ELEMENT__ = element;
                const tag = element.tagName.toLowerCase();
                const id = element.id ? '#' + element.id : '';
                const cls = element.className && typeof element.className === 'string' ?
                    '.' + element.className.split(' ').filter(c => c).join('.') : '';
                console.log('%c[Zen Bridge]%c ✓ Element stored: <' + tag + id + cls + '>',
                    'color: #0066ff; font-weight: bold', 'color: #00aa00');
                console.log('[Zen Bridge] Run in terminal: zen inspected');
                return 'Stored: <' + tag + id + cls + '>';
            }
            console.error('[Zen Bridge] ✗ Invalid element. Usage: zenStore($0) or zenStore(document.querySelector(".selector"))');
            return 'ERROR: Please provide a valid element';
        };

        console.log('%c[Zen Bridge]%c DevTools integration ready', 'color: #0066ff; font-weight: bold', 'color: inherit');
        console.log('[Zen Bridge] To capture inspected element:');
        console.log('  1. Right-click element → Inspect');
        console.log('  2. In DevTools Console: zenStore($0)');
        console.log('  3. In terminal: zen inspected');
    }

    // Initial connection
    if (isFrontTab()) {
        connect();
    }

    // Auto-restart control mode if it was active before page reload
    function autoRestartControl() {
        try {
            const wasActive = sessionStorage.getItem('__ZEN_CONTROL_ACTIVE__');
            console.log('[Zen Bridge] Checking control state... wasActive:', wasActive);

            if (wasActive === 'true') {
                const configStr = sessionStorage.getItem('__ZEN_CONTROL_CONFIG__');
                const selectorsStr = sessionStorage.getItem('__ZEN_CONTROL_REFOCUS_SELECTORS__');
                const config = configStr ? JSON.parse(configStr) : {};

                console.log('[Zen Bridge] Control was active, will auto-restart');
                console.log('[Zen Bridge] Config:', config);
                console.log('[Zen Bridge] Has refocus selectors:', !!selectorsStr);

                // Directly re-initialize control mode with minimal setup
                setTimeout(() => {
                    if (window.__ZEN_CONTROL_ACTIVE__) {
                        console.log('[Zen Bridge] Already restarted, skipping');
                        return; // Already restarted
                    }

                    console.log('[Zen Bridge] Restoring control state...');
                    window.__ZEN_CONTROL_ACTIVE__ = true;
                    window.__ZEN_CONTROL_CURRENT_ELEMENT__ = document.activeElement || document.body;

                    // Recreate the visual highlight styles
                    const focusOutlineMode = config['focus-outline'] || 'custom';
                    if (focusOutlineMode !== 'none' && !document.getElementById('zen-control-styles')) {
                        const style = document.createElement('style');
                        style.id = 'zen-control-styles';
                        const focusColor = config['focus-color'] || '#0066ff';
                        const focusSize = config['focus-size'] || 3;
                        const focusGlow = config['focus-glow'] !== false;
                        const focusAnimation = config['focus-animation'] !== false;

                        let glowColor = 'rgba(0, 102, 255, 0.3)';
                        let glowColorBright = 'rgba(0, 102, 255, 0.5)';
                        if (focusColor.startsWith('#')) {
                            const r = parseInt(focusColor.slice(1, 3), 16);
                            const g = parseInt(focusColor.slice(3, 5), 16);
                            const b = parseInt(focusColor.slice(5, 7), 16);
                            glowColor = `rgba(${r}, ${g}, ${b}, 0.3)`;
                            glowColorBright = `rgba(${r}, ${g}, ${b}, 0.5)`;
                        }

                        const boxShadow = focusGlow ? `0 0 0 2px ${glowColor}, 0 0 12px ${glowColorBright}` : 'none';
                        const animation = focusAnimation ? 'zen-pulse 2s infinite' : 'none';

                        style.textContent = `
                            [data-zen-control-focus] { position: relative !important; }
                            [data-zen-control-focus]::after {
                                content: '' !important; position: absolute !important;
                                top: -${focusSize + 1}px !important; left: -${focusSize + 1}px !important;
                                right: -${focusSize + 1}px !important; bottom: -${focusSize + 1}px !important;
                                border: ${focusSize}px solid ${focusColor} !important;
                                border-radius: 4px !important; pointer-events: none !important;
                                z-index: 2147483647 !important;
                                box-shadow: ${boxShadow} !important;
                                animation: ${animation} !important;
                            }
                            @keyframes zen-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
                        `;
                        document.head.appendChild(style);
                    }

                    console.log('%c[Zen Bridge]%c ✓ Control mode automatically restarted after page load',
                        'color: #0066ff; font-weight: bold', 'color: #00aa00');

                    // Check if we need to refocus an element
                    if (selectorsStr) {
                        const selectors = JSON.parse(selectorsStr);
                        console.log('[Zen Bridge] Will attempt refocus with selectors:', selectors);
                        // We'll handle refocus after the CLI reinitializes all the helper functions
                        window.__ZEN_CONTROL_REFOCUS_SELECTORS__ = selectors;
                        const initialUrl = sessionStorage.getItem('__ZEN_CONTROL_INITIAL_URL__');
                        window.__ZEN_CONTROL_INITIAL_URL__ = initialUrl;

                        // Automatically request full reinitialization via WebSocket
                        console.log('[Zen Bridge] Requesting automatic reinitialization via WebSocket...');

                        // Function to send reinit request
                        const sendReinitRequest = () => {
                            if (window.__zen_ws__ && window.__zen_ws__.readyState === WebSocket.OPEN) {
                                window.__zen_ws__.send(JSON.stringify({
                                    type: 'reinit_control',
                                    config: config
                                }));
                                console.log('[Zen Bridge] Auto-reinitialization request sent via WebSocket');
                            } else {
                                console.log('[Zen Bridge] WebSocket not ready, will send when connected');
                                // Set up one-time listener for when WebSocket connects
                                if (window.__zen_ws__) {
                                    const originalOnOpen = window.__zen_ws__.onopen;
                                    window.__zen_ws__.onopen = (event) => {
                                        if (originalOnOpen) originalOnOpen.call(window.__zen_ws__, event);
                                        window.__zen_ws__.send(JSON.stringify({
                                            type: 'reinit_control',
                                            config: config
                                        }));
                                        console.log('[Zen Bridge] Auto-reinitialization request sent (on connect)');
                                    };
                                } else {
                                    // WebSocket not created yet, will be handled by connect() flow
                                    window.__ZEN_PENDING_REINIT__ = config;
                                }
                            }
                        };

                        sendReinitRequest();
                    }
                }, 50);
            } else {
                console.log('[Zen Bridge] Control was not active, no auto-restart needed');
            }
        } catch (e) {
            console.error('[Zen Bridge] Error auto-restarting control:', e);
        }
    }

    // Run auto-restart check when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoRestartControl);
    } else {
        autoRestartControl();
    }

})();
