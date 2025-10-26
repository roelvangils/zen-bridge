// Get, set, or delete cookies
(function() {
    const action = 'ACTION_PLACEHOLDER'; // 'list', 'get', 'set', 'delete', 'clear'
    const cookieName = 'NAME_PLACEHOLDER';
    const cookieValue = 'VALUE_PLACEHOLDER';
    const options = OPTIONS_PLACEHOLDER;

    // Parse all cookies into an object
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
            const allCookies = getAllCookies();
            return {
                ok: true,
                action: 'list',
                count: Object.keys(allCookies).length,
                cookies: allCookies
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
