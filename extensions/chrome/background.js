/**
 * Zen Browser Bridge - Background Service Worker (Chrome)
 *
 * This script runs in the extension background and handles:
 * - CSP bypass using scripting.executeScript API
 * - Message routing between content scripts and tabs
 * - Extension lifecycle management
 */

console.log('[Zen Bridge Extension] Background service worker loaded');

// Track which tabs have Zen Bridge active
const activeTabs = new Set();

// Listen for tab updates to inject into new pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active) {
        console.log('[Zen Bridge] Tab updated:', tab.url);
        activeTabs.add(tabId);
    }
});

// Listen for tab removal to clean up
chrome.tabs.onRemoved.addListener((tabId) => {
    activeTabs.delete(tabId);
});

// Listen for tab activation
chrome.tabs.onActivated.addListener((activeInfo) => {
    activeTabs.add(activeInfo.tabId);
});

// Track WebSocket connection status per tab
const tabConnectionStatus = new Map();

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Zen Bridge] Message from content script:', message.type);

    if (message.type === 'INJECT_MAIN_WORLD_VARS') {
        // Inject version variables into MAIN world
        injectMainWorldVars(sender.tab.id)
            .then(() => sendResponse({ ok: true }))
            .catch(error => sendResponse({ ok: false, error: String(error) }));
        return true; // Keep channel open for async response
    }

    if (message.type === 'WS_STATUS_UPDATE') {
        // Update connection status and inject into main world
        // status can be: 'connecting', true (connected), or false (disconnected)
        const tabId = sender.tab.id;
        const status = message.connected;
        tabConnectionStatus.set(tabId, status);

        updateConnectionStatusInMainWorld(tabId, status)
            .then(() => sendResponse({ ok: true }))
            .catch(error => sendResponse({ ok: false, error: String(error) }));
        return true;
    }

    if (message.type === 'EXECUTE_CODE') {
        // Execute code with CSP bypass
        executeWithCSPBypass(sender.tab.id, message.code, message.requestId)
            .then(sendResponse)
            .catch(error => {
                sendResponse({
                    ok: false,
                    result: null,
                    error: String(error),
                    requestId: message.requestId
                });
            });
        return true; // Keep channel open for async response
    }

    if (message.type === 'GET_STATUS') {
        sendResponse({
            version: chrome.runtime.getManifest().version,
            active: true,
            tabCount: activeTabs.size
        });
        return false;
    }
});

/**
 * Update WebSocket connection status in main world
 */
async function updateConnectionStatusInMainWorld(tabId, status) {
    try {
        await chrome.scripting.executeScript({
            target: { tabId: tabId },
            world: 'MAIN',
            func: (connectionStatus) => {
                // Status can be: 'connecting', true (connected), or false (disconnected)
                window.__INSPEKT_WS_CONNECTED__ = connectionStatus;
            },
            args: [status]
        });
    } catch (error) {
        console.error('[Inspekt] Failed to update connection status:', error);
    }
}

/**
 * Inject version variables into MAIN world
 * This must be done via background script because content scripts run in isolated world
 */
async function injectMainWorldVars(tabId) {
    try {
        await chrome.scripting.executeScript({
            target: { tabId: tabId },
            world: 'MAIN',
            func: () => {
                // Version and status variables
                window.__ZEN_BRIDGE_VERSION__ = '4.2.1';
                window.__ZEN_BRIDGE_EXTENSION__ = true;
                window.__ZEN_BRIDGE_CSP_BLOCKED__ = false;
                window.__INSPEKT_BRIDGE_VERSION__ = '4.2.1';
                window.__INSPEKT_BRIDGE_EXTENSION__ = true;
                window.__INSPEKT_WS_CONNECTED__ = false; // Will be updated by content script

                // DevTools integration
                if (typeof window.__ZEN_DEVTOOLS_MONITOR__ === 'undefined') {
                    window.__ZEN_DEVTOOLS_MONITOR__ = true;

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
                        console.error('[Zen Bridge] ✗ Invalid element. Usage: zenStore($0)');
                        return 'ERROR: Please provide a valid element';
                    };

                    console.log('%c[Zen Bridge]%c DevTools integration ready',
                        'color: #0066ff; font-weight: bold', 'color: inherit');
                    console.log('[Zen Bridge] To capture inspected element:');
                    console.log('  1. Right-click element → Inspect');
                    console.log('  2. In DevTools Console: zenStore($0)');
                    console.log('  3. In terminal: zen inspected');
                    console.log('');
                    console.log('%c[Zen Bridge]%c Extension mode: CSP restrictions bypassed! ✓',
                        'color: #0066ff; font-weight: bold', 'color: #00aa00; font-weight: bold');
                }
            }
        });
        console.log('[Zen Bridge] Version variables and DevTools injected into MAIN world');
    } catch (error) {
        console.error('[Zen Bridge] Failed to inject variables:', error);
        throw error;
    }
}

/**
 * Execute JavaScript code with CSP bypass
 * Uses script injection which completely bypasses CSP restrictions
 */
async function executeWithCSPBypass(tabId, code, requestId) {
    try {
        console.log('[Zen Bridge] Executing code in tab', tabId, 'with CSP bypass (script injection)');

        // Use script injection to completely bypass CSP
        // Extensions can inject script tags which are not subject to page CSP
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            world: 'MAIN',  // Execute in main world for full page access
            func: (codeToExecute, resultVarName) => {
                return new Promise((resolve) => {
                    try {
                        // Store code in a data attribute to avoid string interpolation issues
                        const codeVar = `__zenCode_${resultVarName}`;
                        window[codeVar] = codeToExecute;

                        // Inject a script tag - this bypasses CSP because it's done by extension
                        const script = document.createElement('script');
                        // Use JSON.stringify to safely embed the variable name
                        script.textContent = `
                            (async function() {
                                const resultVar = ${JSON.stringify(resultVarName)};
                                const codeVar = ${JSON.stringify(codeVar)};
                                try {
                                    // Get the code from the window variable
                                    const code = window[codeVar];
                                    delete window[codeVar];

                                    // Execute the code - use indirect eval for global scope
                                    // Since this script is injected by extension, eval works here
                                    let result = (0, eval)(code);

                                    // Await if it's a promise
                                    if (result && typeof result.then === 'function') {
                                        result = await result;
                                    }

                                    window[resultVar] = {
                                        ok: true,
                                        result: result,
                                        error: null
                                    };
                                } catch (e) {
                                    window[resultVar] = {
                                        ok: false,
                                        result: null,
                                        error: e.stack || String(e)
                                    };
                                }
                            })();
                        `;

                        // Append to page (extension can do this despite CSP)
                        (document.head || document.documentElement).appendChild(script);

                        // Wait for execution to complete
                        const checkInterval = setInterval(() => {
                            if (window[resultVarName] !== undefined) {
                                clearInterval(checkInterval);
                                const result = window[resultVarName];
                                delete window[resultVarName];
                                script.remove();
                                resolve(result);
                            }
                        }, 10);

                        // Timeout after 30 seconds
                        setTimeout(() => {
                            clearInterval(checkInterval);
                            script.remove();
                            delete window[codeVar];
                            delete window[resultVarName];
                            resolve({ ok: false, result: null, error: 'Execution timeout' });
                        }, 30000);

                    } catch (e) {
                        resolve({ ok: false, result: null, error: String(e) });
                    }
                });
            },
            args: [code, `__zenResult_${requestId}`]
        });

        if (results && results[0]) {
            const executionResult = await results[0].result;
            console.log('[Zen Bridge] Execution successful');

            return {
                ok: executionResult.ok,
                result: executionResult.result,
                error: executionResult.error,
                requestId: requestId
            };
        }

        return {
            ok: false,
            result: null,
            error: 'No result returned from tab',
            requestId: requestId
        };

    } catch (error) {
        console.error('[Zen Bridge] Execution error:', error);
        return {
            ok: false,
            result: null,
            error: String(error),
            requestId: requestId
        };
    }
}

// Log extension initialization
console.log('[Zen Bridge Extension] Version:', chrome.runtime.getManifest().version);
console.log('[Zen Bridge Extension] CSP bypass active - works on all websites!');
