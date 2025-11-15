# Claude Development Guide for Inspekt

This document contains architectural patterns, technical decisions, and development guidelines specifically for AI-assisted development on the Inspekt project.

**Last Updated**: 2025-11-15
**Maintained for**: Claude Code and future AI development assistance

---

## Table of Contents

1. [Window Message Bridge Pattern](#window-message-bridge-pattern)
2. [Extension Architecture](#extension-architecture)
3. [Common Patterns](#common-patterns)
4. [Development Guidelines](#development-guidelines)

---

## Window Message Bridge Pattern

### Overview

The **Window Message Bridge** is a critical architectural pattern that enables communication between JavaScript code executing in the browser's **MAIN world** (page context) and the Chrome extension's privileged APIs.

### The Problem

When the Inspekt Chrome extension executes JavaScript code via `chrome.scripting.executeScript()`, it runs in the **MAIN world** to:
- Access the actual page's JavaScript environment
- Bypass Content Security Policy (CSP) restrictions
- Interact with page variables and DOM directly

However, extension APIs like `chrome.runtime.sendMessage()`, `chrome.cookies`, `chrome.storage`, etc., are **NOT accessible from the MAIN world**. They only work in:
- Content scripts (isolated world)
- Background/service worker scripts
- Extension pages (popup, devtools, options)

### The Solution

The bridge uses `window.postMessage()` to communicate between execution contexts:

```
MAIN World Script          Content Script           Background Script
    (page context)      (extension isolated)      (extension privileged)
         │                       │                        │
         │  postMessage          │                        │
         ├──────────────────────>│                        │
         │                       │  chrome.runtime.       │
         │                       │  sendMessage           │
         │                       ├───────────────────────>│
         │                       │                        │
         │                       │              chrome.cookies.getAll()
         │                       │                        ├──┐
         │                       │                        │<─┘
         │                       │  response              │
         │                       │<───────────────────────┤
         │  postMessage          │                        │
         │<──────────────────────┤                        │
         │                       │                        │
```

### Implementation

#### 1. Content Script Bridge (Content Script → Background Script)

**File**: `/Users/roelvangils/Repos/inspekt/extensions/chrome/content.js` (lines 28-65)

```javascript
// Window Message Bridge
// Allows MAIN world scripts to communicate with extension APIs
window.addEventListener('message', async (event) => {
    // Only accept messages from same origin (security)
    if (event.source !== window) return;

    const message = event.data;

    // Handle GET_COOKIES_ENHANCED requests from MAIN world
    if (message && message.type === 'INSPEKT_GET_COOKIES_ENHANCED' && message.source === 'inspekt-page') {
        try {
            // Forward to background script
            const response = await chrome.runtime.sendMessage({
                type: 'GET_COOKIES_ENHANCED'
            });

            // Send response back to MAIN world
            window.postMessage({
                type: 'INSPEKT_COOKIES_RESPONSE',
                source: 'inspekt-extension',
                requestId: message.requestId,
                response: response
            }, '*');
        } catch (error) {
            // Send error back to MAIN world
            window.postMessage({
                type: 'INSPEKT_COOKIES_RESPONSE',
                source: 'inspekt-extension',
                requestId: message.requestId,
                response: {
                    ok: false,
                    error: String(error)
                }
            }, '*');
        }
    }
});
```

#### 2. MAIN World Request (MAIN World → Content Script)

**File**: `/Users/roelvangils/Repos/inspekt/inspekt/scripts/cookies.js` (lines 8-64)

```javascript
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
```

#### 3. Background Script Handler (Background Script → Chrome APIs)

**File**: `/Users/roelvangils/Repos/inspekt/extensions/chrome/background.js` (lines 93-99, 462-513)

```javascript
// Message handler in background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_COOKIES_ENHANCED') {
        // Retrieve detailed cookie information using chrome.cookies API
        getCookiesEnhanced(sender.tab.url)
            .then(sendResponse)
            .catch(error => sendResponse({ ok: false, error: String(error) }));
        return true; // Keep channel open for async response
    }
});

async function getCookiesEnhanced(url) {
    try {
        // Get all cookies for the current URL using privileged API
        const cookies = await chrome.cookies.getAll({ url: url });

        // Extract current domain from URL for party detection
        const currentDomain = new URL(url).hostname;

        // Enhance each cookie with calculated fields
        const enhancedCookies = cookies.map(cookie => {
            const size = cookie.name.length + cookie.value.length;
            const type = cookie.session ? 'session' : 'persistent';
            const expires = cookie.expirationDate
                ? new Date(cookie.expirationDate * 1000).toISOString()
                : null;

            const cookieDomain = cookie.domain.startsWith('.')
                ? cookie.domain.substring(1)
                : cookie.domain;
            const isFirstParty = currentDomain.includes(cookieDomain) ||
                                 cookieDomain.includes(currentDomain);
            const party = isFirstParty ? 'first-party' : 'third-party';

            return {
                ...cookie,
                size: size,
                type: type,
                expires: expires,
                party: party
            };
        });

        return {
            ok: true,
            action: 'list',
            cookies: enhancedCookies,
            count: enhancedCookies.length,
            apiUsed: 'chrome.cookies',
            origin: url,
            hostname: new URL(url).hostname
        };
    } catch (error) {
        console.error('[Inspekt] Cookie retrieval error:', error);
        throw new Error(`Failed to retrieve cookies: ${error.message}`);
    }
}
```

### Message Format Convention

All window messages follow this naming convention:

**Request Messages** (MAIN world → Content script):
- Type: `INSPEKT_<ACTION>_<RESOURCE>`
- Source: `inspekt-page`
- Include: `requestId` (unique identifier)

**Response Messages** (Content script → MAIN world):
- Type: `INSPEKT_<RESOURCE>_RESPONSE`
- Source: `inspekt-extension`
- Include: `requestId` (matching the request), `response` (data object)

Example:
```javascript
// Request
{
    type: 'INSPEKT_GET_COOKIES_ENHANCED',
    source: 'inspekt-page',
    requestId: 'cookie-1234567890-abc123'
}

// Response
{
    type: 'INSPEKT_COOKIES_RESPONSE',
    source: 'inspekt-extension',
    requestId: 'cookie-1234567890-abc123',
    response: {
        ok: true,
        cookies: [...],
        count: 5
    }
}
```

### Security Considerations

1. **Origin Verification**: Always check `event.source === window` to ensure messages come from the same window
2. **Message Source Tags**: Use `source` field (`inspekt-page` / `inspekt-extension`) to distinguish message origins
3. **Request ID Matching**: Use unique request IDs to match responses to requests
4. **Timeout Handling**: Always implement timeouts to prevent indefinite waiting
5. **Error Handling**: Gracefully handle errors and provide fallback mechanisms

### When to Use This Pattern

Use the window message bridge when you need to:

✅ Access Chrome extension APIs from MAIN world scripts
✅ Retrieve data that's not available via standard DOM APIs
✅ Bypass CSP restrictions while maintaining access to extension features
✅ Implement enhanced functionality with graceful fallback

Examples of good use cases:
- `chrome.cookies` API for comprehensive cookie metadata
- `chrome.storage` API for extension storage
- `chrome.tabs` API for tab information
- `chrome.history` API for browsing history

### Extending the Bridge

To add support for a new extension API:

**Step 1**: Add handler in content script:

```javascript
// content.js
window.addEventListener('message', async (event) => {
    if (event.source !== window) return;
    const message = event.data;

    // Add new handler
    if (message && message.type === 'INSPEKT_GET_STORAGE' && message.source === 'inspekt-page') {
        try {
            const response = await chrome.runtime.sendMessage({
                type: 'GET_STORAGE',
                keys: message.keys
            });

            window.postMessage({
                type: 'INSPEKT_STORAGE_RESPONSE',
                source: 'inspekt-extension',
                requestId: message.requestId,
                response: response
            }, '*');
        } catch (error) {
            window.postMessage({
                type: 'INSPEKT_STORAGE_RESPONSE',
                source: 'inspekt-extension',
                requestId: message.requestId,
                response: { ok: false, error: String(error) }
            }, '*');
        }
    }
});
```

**Step 2**: Add handler in background script:

```javascript
// background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'GET_STORAGE') {
        chrome.storage.local.get(message.keys)
            .then(items => sendResponse({ ok: true, items: items }))
            .catch(error => sendResponse({ ok: false, error: String(error) }));
        return true;
    }
});
```

**Step 3**: Create MAIN world function:

```javascript
// scripts/storage.js
async function getEnhancedStorage(keys) {
    if (typeof window === 'undefined') return null;

    try {
        const requestId = 'storage-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        const response = await new Promise((resolve) => {
            const timeout = setTimeout(() => {
                window.removeEventListener('message', handler);
                resolve(null);
            }, 1000);

            const handler = (event) => {
                if (event.source !== window) return;
                const msg = event.data;
                if (msg && msg.type === 'INSPEKT_STORAGE_RESPONSE' &&
                    msg.source === 'inspekt-extension' &&
                    msg.requestId === requestId) {
                    clearTimeout(timeout);
                    window.removeEventListener('message', handler);
                    resolve(msg.response);
                }
            };

            window.addEventListener('message', handler);
            window.postMessage({
                type: 'INSPEKT_GET_STORAGE',
                source: 'inspekt-page',
                requestId: requestId,
                keys: keys
            }, '*');
        });

        return response;
    } catch (e) {
        console.log('[Inspekt] Enhanced storage not available');
        return null;
    }
}
```

---

## Extension Architecture

### Execution Contexts

The Inspekt Chrome extension operates across multiple JavaScript execution contexts:

#### 1. MAIN World (Page Context)
- **Where**: Injected via `chrome.scripting.executeScript()` with `world: 'MAIN'`
- **Purpose**: Execute code in page's JavaScript environment, bypass CSP
- **Available APIs**: DOM, page globals, page JavaScript
- **NOT Available**: Extension APIs (`chrome.*`)
- **Files**: All scripts in `/inspekt/scripts/*.js`

#### 2. Content Script (Isolated World)
- **Where**: Injected via manifest `content_scripts`
- **Purpose**: Bridge between page and extension, DOM access
- **Available APIs**: Limited extension APIs, DOM
- **NOT Available**: Page JavaScript variables, full extension APIs
- **Files**: `/extensions/chrome/content.js`

#### 3. Background Script (Service Worker)
- **Where**: Runs as service worker defined in manifest
- **Purpose**: Handle extension logic, access privileged APIs
- **Available APIs**: Full extension APIs, no DOM access
- **NOT Available**: DOM, page context
- **Files**: `/extensions/chrome/background.js`

### Communication Flow

```
CLI Command
    ↓
WebSocket Server (Python)
    ↓
WebSocket Client (content.js)
    ↓
chrome.runtime.sendMessage (content → background)
    ↓
chrome.scripting.executeScript (background → MAIN world)
    ↓
Execute JavaScript in MAIN world
    ↓ (if extension API needed)
window.postMessage (MAIN → content)
    ↓
chrome.runtime.sendMessage (content → background)
    ↓
Chrome API (background)
    ↓
chrome.runtime.sendMessage (background → content)
    ↓
window.postMessage (content → MAIN)
    ↓
Return result
```

### CSP Bypass Mechanism

The extension uses a two-tier approach for CSP bypass:

**Tier 1: Direct Execution (Fast Path)**
- Uses `AsyncFunction` constructor
- Works on most sites
- Fails on strict CSP sites

**Tier 2: Script Tag Injection (CSP Bypass)**
- Creates `<script>` tag with embedded code
- Extension privilege allows injection despite CSP
- Works on all sites including strict CSP

Implementation in `/extensions/chrome/background.js:253-456`.

---

## Common Patterns

### Pattern 1: Dual-Mode Retrieval with Fallback

When accessing data that may have both a standard API and an enhanced extension API:

```javascript
async function getData() {
    // Try enhanced API first (via extension)
    const enhanced = await getEnhancedData();
    if (enhanced && enhanced.ok) {
        return enhanced;
    }

    // Fallback to standard API
    const standard = getStandardData();
    return {
        ok: true,
        data: standard,
        apiUsed: 'standard'
    };
}
```

Example: `cookies.js` uses `chrome.cookies` API with fallback to `document.cookie`.

### Pattern 2: Promise-Based Window Messaging

For request-response patterns using window messages:

```javascript
async function requestFromExtension(type, data) {
    const requestId = `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return new Promise((resolve) => {
        const timeout = setTimeout(() => {
            window.removeEventListener('message', handler);
            resolve(null); // Timeout fallback
        }, 1000);

        const handler = (event) => {
            if (event.source !== window) return;
            const msg = event.data;

            if (msg &&
                msg.type === `INSPEKT_${type}_RESPONSE` &&
                msg.source === 'inspekt-extension' &&
                msg.requestId === requestId) {

                clearTimeout(timeout);
                window.removeEventListener('message', handler);
                resolve(msg.response);
            }
        };

        window.addEventListener('message', handler);
        window.postMessage({
            type: `INSPEKT_${type}`,
            source: 'inspekt-page',
            requestId: requestId,
            ...data
        }, '*');
    });
}
```

### Pattern 3: Recursive Value Transformation

For transforming nested data structures (used in storage):

```javascript
function transformValueRecursive(obj) {
    if (obj === null || obj === undefined) {
        return obj;
    }

    // If it's an array, transform each element
    if (Array.isArray(obj)) {
        return obj.map(item => transformValueRecursive(item));
    }

    // If it's an object, transform each property
    if (typeof obj === 'object') {
        const result = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                result[key] = transformValueRecursive(obj[key]);
            }
        }
        return result;
    }

    // If it's a string, apply transformations
    if (typeof obj === 'string') {
        return applyStringTransformation(obj);
    }

    // Return as-is for other types
    return obj;
}
```

---

## Development Guidelines

### Adding New Extension Features

When adding functionality that requires Chrome extension APIs:

1. **Check API Availability**: Ensure the Chrome API is available and has appropriate permissions in manifest.json
2. **Add Permission**: Update `/extensions/chrome/manifest.json` if needed
3. **Implement Background Handler**: Add handler in `background.js`
4. **Add Content Script Bridge**: Extend window message listener in `content.js`
5. **Create MAIN World Function**: Implement request function in appropriate script file
6. **Implement Fallback**: Always provide graceful fallback for non-extension environments
7. **Test Both Modes**: Test with extension active and with fallback mode

### Testing Extension Features

1. **Reload Extension**: After code changes, reload via `chrome://extensions/`
2. **Check Console**: Monitor both page console and extension background console
3. **Test Fallback**: Disable extension to verify fallback mode works
4. **Verify Message Flow**: Use console.log to trace message flow through the bridge

### Common Pitfalls to Avoid

❌ **Don't**: Try to use `chrome.runtime` directly in MAIN world scripts
✅ **Do**: Use window message bridge pattern

❌ **Don't**: Forget timeout handling in promise-based messaging
✅ **Do**: Always implement timeouts with fallback

❌ **Don't**: Assume extension APIs are always available
✅ **Do**: Implement dual-mode with fallback

❌ **Don't**: Use synchronous operations in background script
✅ **Do**: Use async/await for all extension API calls

❌ **Don't**: Send sensitive data via window.postMessage without validation
✅ **Do**: Validate event.source and use message type/source tags

### File Organization

- **Extension Files**: `/extensions/chrome/`
  - `manifest.json` - Extension configuration
  - `background.js` - Background service worker
  - `content.js` - Content script (bridge + WebSocket)
  - `permissions.js` - Permission management
  - `devtools.html`, `panel.html` - DevTools integration
  - `popup/` - Extension popup UI

- **Script Files**: `/inspekt/scripts/`
  - All scripts execute in MAIN world
  - Should not directly access extension APIs
  - Use window message bridge when extension features needed

- **Python Backend**: `/inspekt/`
  - CLI commands, services, WebSocket server
  - Loads scripts and sends to browser for execution

---

## Future Patterns to Consider

### 1. Batch Message Handling

For multiple related requests, consider batching:

```javascript
// Instead of multiple individual requests
const cookies = await getCookies();
const storage = await getStorage();
const history = await getHistory();

// Use single batch request
const data = await getBatchData(['cookies', 'storage', 'history']);
```

### 2. Persistent Message Channel

For long-lived connections, consider using `chrome.runtime.connect()` instead of `sendMessage()`:

```javascript
// In content script
const port = chrome.runtime.connect({ name: 'inspekt-channel' });
port.postMessage({ type: 'GET_DATA' });
port.onMessage.addListener((msg) => {
    // Handle response
});
```

### 3. Event-Based Updates

For real-time updates (e.g., cookie changes), use Chrome extension events:

```javascript
// In background script
chrome.cookies.onChanged.addListener((changeInfo) => {
    // Notify MAIN world of cookie change
    sendToMainWorld('COOKIE_CHANGED', changeInfo);
});
```

---

## Changelog

**2025-11-15**: Initial creation with Window Message Bridge pattern documentation
- Documented window message bridge architecture
- Added extension context explanations
- Included implementation examples
- Added development guidelines

---

**End of Document**
