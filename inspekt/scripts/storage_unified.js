// Unified storage retrieval - cookies, localStorage, sessionStorage
(async function() {
    const action = 'ACTION_PLACEHOLDER'; // 'list', 'get', 'set', 'delete', 'clear'
    const types = TYPES_PLACEHOLDER; // Array: ['cookies', 'local', 'session']
    const keyName = 'KEY_PLACEHOLDER';
    const value = 'VALUE_PLACEHOLDER';
    const options = OPTIONS_PLACEHOLDER;

    // ============================================================================
    // Helper Functions (shared across all storage types)
    // ============================================================================

    /**
     * Check if a string should be split into an array
     */
    function splitDelimitedString(value) {
        if (value.includes('|')) {
            return value.split('|').map(s => s.trim());
        }
        if (value.includes(',')) {
            const parts = value.split(',').map(s => s.trim());
            if (parts.length > 1 && parts.every(p => p.length > 0)) {
                return parts;
            }
        }
        return null;
    }

    /**
     * Recursively transform values (including nested objects)
     */
    function transformValueRecursive(obj) {
        if (obj === null || obj === undefined) {
            return obj;
        }

        if (Array.isArray(obj)) {
            return obj.map(item => transformValueRecursive(item));
        }

        if (typeof obj === 'object') {
            const result = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    result[key] = transformValueRecursive(obj[key]);
                }
            }
            return result;
        }

        if (typeof obj === 'string') {
            const delimited = splitDelimitedString(obj);
            if (delimited) {
                return delimited;
            }
        }

        return obj;
    }

    /**
     * Transform storage value (parse JSON, split delimited strings)
     */
    function transformValue(value) {
        try {
            const parsed = JSON.parse(value);
            return transformValueRecursive(parsed);
        } catch (e) {
            const delimited = splitDelimitedString(value);
            if (delimited) {
                return delimited;
            }
            return value;
        }
    }

    // ============================================================================
    // Cookies Functions
    // ============================================================================

    /**
     * Try to get enhanced cookie data via chrome.cookies API
     * Uses window message bridge to communicate with extension
     */
    async function getCookiesEnhanced() {
        if (typeof window === 'undefined' || typeof window.postMessage !== 'function') {
            return null;
        }

        try {
            const requestId = 'cookie-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

            const response = await new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    window.removeEventListener('message', messageHandler);
                    resolve(null);
                }, 1000);

                const messageHandler = (event) => {
                    if (event.source !== window) return;

                    const message = event.data;
                    if (message &&
                        message.type === 'INSPEKT_COOKIES_RESPONSE' &&
                        message.source === 'inspekt-extension' &&
                        message.requestId === requestId) {

                        clearTimeout(timeout);
                        window.removeEventListener('message', messageHandler);
                        resolve(message.response);
                    }
                };

                window.addEventListener('message', messageHandler);

                window.postMessage({
                    type: 'INSPEKT_GET_COOKIES_ENHANCED',
                    source: 'inspekt-page',
                    requestId: requestId
                }, '*');
            });

            if (response && response.ok) {
                return response;
            }
        } catch (e) {
            console.log('[Inspekt] Enhanced cookie API not available, falling back to document.cookie');
        }

        return null;
    }

    /**
     * Parse all cookies into an object (fallback method)
     */
    function getAllCookies() {
        const cookies = {};
        if (!document.cookie) return cookies;

        document.cookie.split(';').forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            if (name) {
                cookies[name] = decodeURIComponent(value || '');
            }
        });
        return cookies;
    }

    /**
     * Get a specific cookie
     */
    function getCookie(name) {
        const cookies = getAllCookies();
        return cookies[name] || null;
    }

    /**
     * Set a cookie
     */
    function setCookie(name, value, opts = {}) {
        let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

        if (opts.maxAge) {
            cookie += `; max-age=${opts.maxAge}`;
        } else if (opts.expires) {
            cookie += `; expires=${opts.expires}`;
        }

        if (opts.path) {
            cookie += `; path=${opts.path}`;
        } else {
            cookie += '; path=/';
        }

        if (opts.domain) {
            cookie += `; domain=${opts.domain}`;
        }

        if (opts.secure) {
            cookie += '; secure';
        }

        if (opts.sameSite) {
            cookie += `; samesite=${opts.sameSite}`;
        }

        document.cookie = cookie;
        return true;
    }

    /**
     * Delete a cookie
     */
    function deleteCookie(name) {
        document.cookie = `${encodeURIComponent(name)}=; max-age=0; path=/`;
        const domain = window.location.hostname;
        document.cookie = `${encodeURIComponent(name)}=; max-age=0; path=/; domain=${domain}`;
        return true;
    }

    /**
     * Clear all cookies
     */
    function clearAllCookies() {
        const cookies = getAllCookies();
        const names = Object.keys(cookies);
        names.forEach(name => deleteCookie(name));
        return names.length;
    }

    /**
     * Execute cookie action
     */
    async function executeCookieAction() {
        switch (action) {
            case 'list':
                const enhanced = await getCookiesEnhanced();
                if (enhanced) {
                    return enhanced;
                }

                const allCookies = getAllCookies();
                return {
                    ok: true,
                    count: Object.keys(allCookies).length,
                    items: allCookies,
                    apiUsed: 'document.cookie'
                };

            case 'get':
                const cookieValue = getCookie(keyName);
                return {
                    ok: true,
                    key: keyName,
                    value: cookieValue,
                    exists: cookieValue !== null
                };

            case 'set':
                setCookie(keyName, value, options);
                return {
                    ok: true,
                    key: keyName,
                    value: value
                };

            case 'delete':
                deleteCookie(keyName);
                return {
                    ok: true,
                    key: keyName
                };

            case 'clear':
                const deletedCount = clearAllCookies();
                return {
                    ok: true,
                    deleted: deletedCount
                };

            default:
                return {
                    ok: false,
                    error: 'Invalid action: ' + action
                };
        }
    }

    // ============================================================================
    // localStorage Functions
    // ============================================================================

    /**
     * Check if localStorage is available
     */
    function isLocalStorageAvailable() {
        try {
            const test = '__storage_test__';
            window.localStorage.setItem(test, test);
            window.localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Get all localStorage items
     */
    function getAllLocalStorageItems() {
        const items = {};
        const length = window.localStorage.length;

        for (let i = 0; i < length; i++) {
            const itemKey = window.localStorage.key(i);
            if (itemKey !== null) {
                const rawValue = window.localStorage.getItem(itemKey);
                items[itemKey] = transformValue(rawValue);
            }
        }

        return items;
    }

    /**
     * Execute localStorage action
     */
    function executeLocalStorageAction() {
        if (!isLocalStorageAvailable()) {
            return {
                ok: false,
                error: 'localStorage is not available'
            };
        }

        try {
            switch (action) {
                case 'list':
                    const allItems = getAllLocalStorageItems();
                    return {
                        ok: true,
                        count: Object.keys(allItems).length,
                        items: allItems
                    };

                case 'get':
                    const itemValue = window.localStorage.getItem(keyName);
                    return {
                        ok: true,
                        key: keyName,
                        value: itemValue,
                        exists: itemValue !== null
                    };

                case 'set':
                    window.localStorage.setItem(keyName, value);
                    return {
                        ok: true,
                        key: keyName,
                        value: value
                    };

                case 'delete':
                    window.localStorage.removeItem(keyName);
                    return {
                        ok: true,
                        key: keyName
                    };

                case 'clear':
                    const count = window.localStorage.length;
                    window.localStorage.clear();
                    return {
                        ok: true,
                        deleted: count
                    };

                default:
                    return {
                        ok: false,
                        error: 'Invalid action: ' + action
                    };
            }
        } catch (error) {
            return {
                ok: false,
                error: error.message
            };
        }
    }

    // ============================================================================
    // sessionStorage Functions
    // ============================================================================

    /**
     * Check if sessionStorage is available
     */
    function isSessionStorageAvailable() {
        try {
            const test = '__storage_test__';
            window.sessionStorage.setItem(test, test);
            window.sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Get all sessionStorage items
     */
    function getAllSessionStorageItems() {
        const items = {};
        const length = window.sessionStorage.length;

        for (let i = 0; i < length; i++) {
            const itemKey = window.sessionStorage.key(i);
            if (itemKey !== null) {
                const rawValue = window.sessionStorage.getItem(itemKey);
                items[itemKey] = transformValue(rawValue);
            }
        }

        return items;
    }

    /**
     * Execute sessionStorage action
     */
    function executeSessionStorageAction() {
        if (!isSessionStorageAvailable()) {
            return {
                ok: false,
                error: 'sessionStorage is not available'
            };
        }

        try {
            switch (action) {
                case 'list':
                    const allItems = getAllSessionStorageItems();
                    return {
                        ok: true,
                        count: Object.keys(allItems).length,
                        items: allItems
                    };

                case 'get':
                    const itemValue = window.sessionStorage.getItem(keyName);
                    return {
                        ok: true,
                        key: keyName,
                        value: itemValue,
                        exists: itemValue !== null
                    };

                case 'set':
                    window.sessionStorage.setItem(keyName, value);
                    return {
                        ok: true,
                        key: keyName,
                        value: value
                    };

                case 'delete':
                    window.sessionStorage.removeItem(keyName);
                    return {
                        ok: true,
                        key: keyName
                    };

                case 'clear':
                    const count = window.sessionStorage.length;
                    window.sessionStorage.clear();
                    return {
                        ok: true,
                        deleted: count
                    };

                default:
                    return {
                        ok: false,
                        error: 'Invalid action: ' + action
                    };
            }
        } catch (error) {
            return {
                ok: false,
                error: error.message
            };
        }
    }

    // ============================================================================
    // Main Execution
    // ============================================================================

    try {
        // Build result object based on requested types
        const results = {
            ok: true,
            origin: window.location.origin,
            hostname: window.location.hostname,
            timestamp: new Date().toISOString(),
            storage: {},
            totals: {
                totalItems: 0,
                totalSize: 0,
                byType: {}
            }
        };

        // Execute actions for each requested storage type
        const promises = [];

        if (types.includes('cookies')) {
            promises.push(
                executeCookieAction().then(result => ({type: 'cookies', result}))
            );
        }

        if (types.includes('local')) {
            promises.push(
                Promise.resolve(executeLocalStorageAction()).then(result => ({type: 'local', result}))
            );
        }

        if (types.includes('session')) {
            promises.push(
                Promise.resolve(executeSessionStorageAction()).then(result => ({type: 'session', result}))
            );
        }

        // Wait for all storage types to complete
        const storageResults = await Promise.all(promises);

        // Aggregate results
        for (const {type, result} of storageResults) {
            if (result.ok) {
                // Map type name to output key
                const outputKey = type === 'cookies' ? 'cookies' :
                                  type === 'local' ? 'localStorage' :
                                  'sessionStorage';

                results.storage[outputKey] = result;

                // Calculate totals
                const count = result.count || 0;
                results.totals.byType[outputKey] = count;
                results.totals.totalItems += count;

                // Calculate size (approximate)
                if (result.items) {
                    const itemsStr = JSON.stringify(result.items);
                    results.totals.totalSize += itemsStr.length;
                }
            } else {
                // Include errors
                results.storage[type] = {
                    ok: false,
                    error: result.error
                };
            }
        }

        return results;

    } catch (error) {
        return {
            ok: false,
            error: error.message,
            stack: error.stack
        };
    }
})()
