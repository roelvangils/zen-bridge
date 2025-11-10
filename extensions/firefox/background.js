/**
 * Zen Browser Bridge - Background Script
 *
 * This script runs in the extension background and handles:
 * - CSP bypass using tabs.executeScript API
 * - Message routing between content scripts and tabs
 * - Extension lifecycle management
 */

console.log('[Zen Bridge Extension] Background script loaded');

// Track which tabs have Zen Bridge active
const activeTabs = new Set();

// Listen for tab updates to inject into new pages
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active) {
        console.log('[Zen Bridge] Tab updated:', tab.url);
        activeTabs.add(tabId);
    }
});

// Listen for tab removal to clean up
browser.tabs.onRemoved.addListener((tabId) => {
    activeTabs.delete(tabId);
});

// Listen for tab activation
browser.tabs.onActivated.addListener((activeInfo) => {
    activeTabs.add(activeInfo.tabId);
});

// Listen for messages from content script
browser.runtime.onMessage.addListener((message, sender) => {
    console.log('[Zen Bridge] Message from content script:', message.type);

    if (message.type === 'EXECUTE_CODE') {
        // Execute code with CSP bypass
        return executeWithCSPBypass(sender.tab.id, message.code, message.requestId);
    }

    if (message.type === 'GET_STATUS') {
        return Promise.resolve({
            version: browser.runtime.getManifest().version,
            active: true,
            tabCount: activeTabs.size
        });
    }
});

/**
 * Execute JavaScript code with CSP bypass
 * Uses tabs.executeScript which bypasses CSP restrictions
 */
async function executeWithCSPBypass(tabId, code, requestId) {
    try {
        console.log('[Zen Bridge] Executing code in tab', tabId, 'with CSP bypass');

        // Wrap user code in a function that returns the result
        // Handle both expressions and complete statements/IIFEs
        // Check if code contains IIFE pattern (might have comments before it)
        const isIIFE = /^\s*(\/\/.*\n|\s)*\(function/.test(code) ||
                       /^\s*(\/\/.*\n|\s)*\(async function/.test(code);

        const wrappedCode = isIIFE
            ? `
            (async function() {
                try {
                    let result = ${code};
                    if (result && typeof result.then === 'function') {
                        result = await result;
                    }
                    return { ok: true, result, error: null };
                } catch (e) {
                    return { ok: false, result: null, error: String(e.stack || e) };
                }
            })();
            `
            : `
            (async function() {
                try {
                    const result = await (async () => { return (${code}); })();
                    return { ok: true, result, error: null };
                } catch (e) {
                    return { ok: false, result: null, error: String(e.stack || e) };
                }
            })();
            `;

        // Execute with CSP bypass
        const results = await browser.tabs.executeScript(tabId, {
            code: wrappedCode,
            runAt: 'document_idle'
        });

        if (results && results[0]) {
            const executionResult = results[0];
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
console.log('[Zen Bridge Extension] Version:', browser.runtime.getManifest().version);
console.log('[Zen Bridge Extension] CSP bypass active - works on all websites!');
