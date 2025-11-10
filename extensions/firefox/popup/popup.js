/**
 * Zen Browser Bridge - Popup Script
 *
 * Handles the settings panel UI and displays connection status
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Display version
    const manifest = browser.runtime.getManifest();
    document.getElementById('version').textContent = `v${manifest.version}`;

    // Check connection status
    await checkConnectionStatus();

    // Refresh status every 5 seconds
    setInterval(checkConnectionStatus, 5000);
});

async function checkConnectionStatus() {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    try {
        // Get active tab
        const tabs = await browser.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) {
            setStatus(statusDot, statusText, 'disconnected', 'No active tab');
            return;
        }

        const tab = tabs[0];

        // Try to check if content script is loaded and WebSocket is connected
        const result = await browser.tabs.executeScript(tab.id, {
            code: `(window.__zen_ws__ && window.__zen_ws__.readyState === 1) ? 'connected' :
                   (window.__ZEN_BRIDGE_EXTENSION__ ? 'loaded' : 'not-loaded')`
        });

        if (result && result[0]) {
            const status = result[0];

            if (status === 'connected') {
                setStatus(statusDot, statusText, 'connected',
                    '✓ Connected to localhost:8766');
            } else if (status === 'loaded') {
                setStatus(statusDot, statusText, 'checking',
                    'Extension loaded, connecting to server...');
            } else {
                setStatus(statusDot, statusText, 'checking',
                    'Extension loading...');
            }
        } else {
            setStatus(statusDot, statusText, 'checking',
                'Initializing...');
        }

    } catch (error) {
        console.error('[Zen Bridge Popup] Error checking status:', error);
        setStatus(statusDot, statusText, 'disconnected',
            'Server not running. Run: zen server start');
    }
}

function setStatus(dot, text, status, message) {
    // Remove all status classes
    dot.classList.remove('connected', 'disconnected');
    text.classList.remove('connected', 'disconnected');

    // Add appropriate class
    if (status === 'connected') {
        dot.classList.add('connected');
        text.classList.add('connected');
    } else if (status === 'disconnected') {
        dot.classList.add('disconnected');
        text.classList.add('disconnected');
    }
    // 'checking' uses default animation

    text.textContent = message;
}
