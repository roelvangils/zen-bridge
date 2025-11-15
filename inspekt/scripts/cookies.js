// Get, set, or delete cookies
(async function() {
    const action = 'ACTION_PLACEHOLDER'; // 'list', 'get', 'set', 'delete', 'clear'
    const cookieName = 'NAME_PLACEHOLDER';
    const cookieValue = 'VALUE_PLACEHOLDER';
    const options = OPTIONS_PLACEHOLDER;

    // Try to get enhanced cookie data via chrome.cookies API
    // Uses window message bridge to communicate with extension
    async function getCookiesEnhanced() {
        // Check if we're in a browser context with window.postMessage
        if (typeof window === 'undefined' || typeof window.postMessage !== 'function') {
            return null;
        }

        try {
            // Generate unique request ID
            const requestId = 'cookie-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

            // Create promise that waits for response via window message
            const response = await new Promise((resolve, reject) => {
                // Timeout after 1 second
                const timeout = setTimeout(() => {
                    window.removeEventListener('message', messageHandler);
                    resolve(null); // Fallback to document.cookie
                }, 1000);

                // Listen for response from extension
                const messageHandler = (event) => {
                    // Only accept messages from same origin
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

                // Send request to extension via window.postMessage
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

        // Fallback: use document.cookie (limited data)
        return null;
    }

    // Parse all cookies into an object (fallback method)
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

    // Get a specific cookie
    function getCookie(name) {
        const cookies = getAllCookies();
        return cookies[name] || null;
    }

    // Set a cookie
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

    // Delete a cookie
    function deleteCookie(name) {
        document.cookie = `${encodeURIComponent(name)}=; max-age=0; path=/`;
        // Also try to delete for the current domain
        const domain = window.location.hostname;
        document.cookie = `${encodeURIComponent(name)}=; max-age=0; path=/; domain=${domain}`;
        return true;
    }

    // Clear all cookies
    function clearAllCookies() {
        const cookies = getAllCookies();
        const names = Object.keys(cookies);
        names.forEach(name => deleteCookie(name));
        return names.length;
    }

    // Execute action
    switch (action) {
        case 'list':
            // Try enhanced API first
            const enhanced = await getCookiesEnhanced();
            if (enhanced) {
                return enhanced;
            }

            // Fallback to document.cookie
            const allCookies = getAllCookies();
            return {
                ok: true,
                action: 'list',
                count: Object.keys(allCookies).length,
                cookies: allCookies,
                apiUsed: 'document.cookie',
                origin: window.location.origin,
                hostname: window.location.hostname
            };

        case 'get':
            const value = getCookie(cookieName);
            return {
                ok: true,
                action: 'get',
                name: cookieName,
                value: value,
                exists: value !== null
            };

        case 'set':
            setCookie(cookieName, cookieValue, options);
            return {
                ok: true,
                action: 'set',
                name: cookieName,
                value: cookieValue
            };

        case 'delete':
            deleteCookie(cookieName);
            return {
                ok: true,
                action: 'delete',
                name: cookieName
            };

        case 'clear':
            const deletedCount = clearAllCookies();
            return {
                ok: true,
                action: 'clear',
                deleted: deletedCount
            };

        default:
            return {
                ok: false,
                error: 'Invalid action: ' + action
            };
    }
})()
