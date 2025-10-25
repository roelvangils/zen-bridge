// ==UserScript==
// @name         Zen Browser Bridge
// @namespace    zen-bridge
// @version      2.0
// @description  Execute JavaScript in the active tab via Zen CLI
// @match        *://*/*
// @run-at       document-idle
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// ==/UserScript==

(function () {
    'use strict';

    const POLL_MS = 300; // polling interval
    const BRIDGE = 'http://127.0.0.1:8765';

    function isFrontTab() {
        // Only execute in the visible top-level frame
        return document.visibilityState === 'visible' && window === window.top;
    }

    function get(url) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'GET',
                url,
                timeout: 5000,
                onload: (res) => resolve(res.responseText),
                onerror: reject,
                ontimeout: reject,
            });
        });
    }

    function post(url, data) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'POST',
                url,
                data: typeof data === 'string' ? data : JSON.stringify(data),
                headers: { 'Content-Type': 'application/json' },
                timeout: 5000,
                onload: (res) => resolve(res.responseText),
                onerror: reject,
                ontimeout: reject,
            });
        });
    }

    async function poll() {
        if (!isFrontTab()) return;

        try {
            // Request next code to execute
            const raw = await get(`${BRIDGE}/next`);
            if (!raw) return;

            let payload;
            try {
                payload = JSON.parse(raw);
            } catch {
                return;
            }

            if (!payload || !payload.code || !payload.request_id) return;

            const requestId = payload.request_id;
            let result, error = null;

            try {
                // Execute JavaScript in page context
                // Using indirect eval for global scope
                result = (0, eval)(payload.code);

                // Await promises
                if (result && typeof result.then === 'function') {
                    result = await result;
                }
            } catch (e) {
                error = String(e && e.stack ? e.stack : e);
            }

            // Send result back to bridge
            await post(`${BRIDGE}/submit`, {
                request_id: requestId,
                ok: !error,
                result: error ? null : (typeof result === 'undefined' ? null : result),
                error,
                url: location.href,
                title: document.title || '',
            });
        } catch (_) {
            // Silent fail if bridge is down
        }
    }

    // Start polling
    setInterval(poll, POLL_MS);

    // Visual indicator (optional - comment out if not wanted)
    console.log('%c[Zen Bridge]%c Connected', 'color: #0066ff; font-weight: bold', 'color: inherit');
})();
