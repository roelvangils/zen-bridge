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

    if (message.type === 'COPY_IMAGE_TO_CLIPBOARD') {
        // Handle clipboard write from DevTools panel (which has restricted permissions)
        copyImageToClipboard(message.blob)
            .then(() => sendResponse({ ok: true }))
            .catch(error => sendResponse({ ok: false, error: String(error) }));
        return true; // Keep channel open for async response
    }
});

/**
 * Copy image blob to clipboard via offscreen document
 * DevTools panels have restricted clipboard access, and service workers don't have ClipboardItem
 * So we use an offscreen document which has full DOM APIs
 */
async function copyImageToClipboard(dataUrl) {
    try {
        // Ensure offscreen document exists
        await setupOffscreenDocument();

        console.log('[Zen Bridge] Sending clipboard write request to offscreen document...');

        // Get the offscreen document context
        const offscreenContexts = await chrome.runtime.getContexts({
            contextTypes: ['OFFSCREEN_DOCUMENT'],
            documentUrls: [chrome.runtime.getURL('offscreen.html')]
        });

        if (offscreenContexts.length === 0) {
            throw new Error('Offscreen document not found');
        }

        // Send message directly to the offscreen document
        const response = await chrome.runtime.sendMessage({
            type: 'OFFSCREEN_COPY_IMAGE',
            dataUrl: dataUrl,
            target: 'offscreen'
        });

        console.log('[Zen Bridge] Response from offscreen:', response);

        if (!response || !response.success) {
            throw new Error(response?.error || 'Failed to copy via offscreen document');
        }

        console.log('[Zen Bridge] Image copied to clipboard via offscreen document');
    } catch (error) {
        console.error('[Zen Bridge] Failed to copy image to clipboard:', error);
        throw error;
    }
}

/**
 * Setup offscreen document for clipboard operations
 */
async function setupOffscreenDocument() {
    // Check if offscreen document already exists
    const existingContexts = await chrome.runtime.getContexts({
        contextTypes: ['OFFSCREEN_DOCUMENT'],
        documentUrls: [chrome.runtime.getURL('offscreen.html')]
    });

    if (existingContexts.length > 0) {
        return; // Already exists
    }

    // Create offscreen document
    await chrome.offscreen.createDocument({
        url: 'offscreen.html',
        reasons: ['CLIPBOARD'],
        justification: 'Copy screenshots to clipboard from DevTools panel'
    });

    console.log('[Zen Bridge] Offscreen document created for clipboard operations');

    // Longer delay to ensure offscreen document is fully loaded and ready
    await new Promise(resolve => setTimeout(resolve, 300));
}

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
 * Execute JavaScript code with multi-tier CSP handling
 *
 * Tier 1: Try direct execution (fast, clean, works on most sites)
 * Tier 2: Fall back to script tag injection (works on strict CSP sites)
 */
async function executeWithCSPBypass(tabId, code, requestId) {
    try {
        // TIER 1: Try direct execution first (fast path)
        console.log('[Zen Bridge] Attempting direct execution...');

        const directResult = await executeDirectly(tabId, code, requestId);

        // Check if it failed due to CSP
        if (!directResult.ok && directResult.error &&
            (directResult.error.includes('EvalError') ||
             directResult.error.includes('Content Security Policy') ||
             directResult.error.includes('unsafe-eval'))) {

            console.log('[Zen Bridge] CSP detected, falling back to script tag injection');

            // TIER 2: Fall back to script tag injection
            return await executeViaScriptTag(tabId, code, requestId);
        }

        // Direct execution succeeded or failed for non-CSP reasons
        return directResult;

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

/**
 * TIER 1: Direct execution using AsyncFunction
 * Fast and clean, works on sites without strict CSP
 */
async function executeDirectly(tabId, code, requestId) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            world: 'MAIN',
            func: async (codeToExecute) => {
                try {
                    // Try using AsyncFunction (blocked by strict CSP)
                    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
                    const fn = new AsyncFunction('return (' + codeToExecute + ')');
                    let result = await fn();

                    // Handle nested promises
                    if (result && typeof result.then === 'function') {
                        result = await result;
                    }

                    return {
                        ok: true,
                        result: result,
                        error: null
                    };
                } catch (e) {
                    return {
                        ok: false,
                        result: null,
                        error: e.stack || String(e)
                    };
                }
            },
            args: [code]
        });

        if (results && results[0]) {
            const executionResult = await results[0].result;
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
        return {
            ok: false,
            result: null,
            error: String(error),
            requestId: requestId
        };
    }
}

/**
 * TIER 2: Script tag injection (CSP bypass)
 * Works on all sites including those with strict CSP
 * Uses direct code embedding (no eval/Function constructor)
 */
async function executeViaScriptTag(tabId, code, requestId) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            world: 'MAIN',
            func: (codeToExecute, resultId) => {
                return new Promise((resolve) => {
                    try {
                        // Create a script tag - extensions can inject these even with CSP
                        const script = document.createElement('script');

                        // CRITICAL: Embed the code DIRECTLY into the script tag's source
                        // The code becomes part of the static script content, NOT eval'd
                        // This completely bypasses CSP restrictions
                        script.textContent = `
                            (async function() {
                                try {
                                    // Execute user code directly (no eval, no Function constructor)
                                    // The code below is inserted as raw JavaScript source
                                    const __result__ = await (${codeToExecute});

                                    window['${resultId}'] = {
                                        ok: true,
                                        result: __result__,
                                        error: null
                                    };
                                } catch (e) {
                                    window['${resultId}'] = {
                                        ok: false,
                                        result: null,
                                        error: e.stack || String(e)
                                    };
                                }
                            })();
                        `;

                        // Inject the script (extension privilege allows this despite CSP)
                        (document.head || document.documentElement).appendChild(script);

                        // Poll for result
                        const startTime = Date.now();
                        const checkInterval = setInterval(() => {
                            if (window[resultId] !== undefined) {
                                clearInterval(checkInterval);
                                const result = window[resultId];
                                delete window[resultId];
                                script.remove();
                                resolve(result);
                            } else if (Date.now() - startTime > 30000) {
                                // 30 second timeout
                                clearInterval(checkInterval);
                                script.remove();
                                delete window[resultId];
                                resolve({
                                    ok: false,
                                    result: null,
                                    error: 'Execution timeout (30s)'
                                });
                            }
                        }, 10);

                    } catch (e) {
                        resolve({
                            ok: false,
                            result: null,
                            error: 'Script injection failed: ' + String(e)
                        });
                    }
                });
            },
            args: [code, `__inspektResult_${requestId}`]
        });

        if (results && results[0]) {
            const executionResult = await results[0].result;
            console.log('[Zen Bridge] Script tag execution successful');

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
        console.error('[Zen Bridge] Script tag execution error:', error);
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
