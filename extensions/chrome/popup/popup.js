/**
 * Inspekt - Popup Script (Chrome)
 *
 * Handles the settings panel UI and displays connection status
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Display version
    const manifest = chrome.runtime.getManifest();
    document.getElementById('version').textContent = `v${manifest.version}`;

    // Load allowed domains
    await loadAllowedDomains();

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
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) {
            setStatus(statusDot, statusText, 'disconnected', 'No active tab');
            return;
        }

        const tab = tabs[0];

        // Try to check if content script is loaded and WebSocket is connected
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
                return (window.__INSPEKT_WS_CONNECTED__ === true) ? 'connected' :
                       (window.__INSPEKT_BRIDGE_EXTENSION__ ? 'loaded' : 'not-loaded');
            }
        });

        if (results && results[0]) {
            const status = results[0].result;

            if (status === 'connected') {
                setStatus(statusDot, statusText, 'connected',
                    '<span class="material-icons md-inline">check</span> Connected to localhost:8766');
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
        console.error('[Inspekt Popup] Error checking status:', error);
        setStatus(statusDot, statusText, 'disconnected',
            'Server not running. Run: inspekt server start');
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

async function loadAllowedDomains() {
    const currentDomainStatus = document.getElementById('current-domain-status');
    const domainsList = document.getElementById('allowed-domains-list');

    try {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        const tab = tabs[0];
        const url = new URL(tab.url);
        const currentDomain = url.hostname;

        // Get allowed domains
        const allowedDomains = await ZenPermissions.getAllowedDomains();
        const isCurrentAllowed = allowedDomains.includes(currentDomain);

        // Show current domain status
        currentDomainStatus.innerHTML = `
            <div>
                <div class="domain-name">Current: ${currentDomain}</div>
                <span class="domain-badge ${isCurrentAllowed ? 'allowed' : 'denied'}">
                    ${isCurrentAllowed ? '<span class="material-icons md-inline">check</span> Allowed' : '<span class="material-icons md-inline">close</span> Not Allowed'}
                </span>
            </div>
            ${!isCurrentAllowed ? `
                <button id="allow-current-btn">Allow This Domain</button>
            ` : `
                <button id="remove-current-btn" class="remove">Remove</button>
            `}
        `;

        // Add event listener for current domain button
        if (!isCurrentAllowed) {
            document.getElementById('allow-current-btn').addEventListener('click', async () => {
                await ZenPermissions.allowDomain(currentDomain);
                await loadAllowedDomains();
                // Reload the tab to trigger connection
                chrome.tabs.reload(tab.id);
            });
        } else {
            document.getElementById('remove-current-btn').addEventListener('click', async () => {
                await ZenPermissions.removeDomain(currentDomain);
                await loadAllowedDomains();
            });
        }

        // Show all allowed domains (except current)
        const otherDomains = allowedDomains.filter(d => d !== currentDomain);

        if (otherDomains.length === 0) {
            domainsList.innerHTML = '<div class="no-domains">No other domains allowed</div>';
        } else {
            domainsList.innerHTML = otherDomains.map(domain => `
                <div class="domain-item">
                    <span class="domain-name">${domain}</span>
                    <button class="remove-domain-btn" data-domain="${domain}">Remove</button>
                </div>
            `).join('');

            // Add remove listeners
            document.querySelectorAll('.remove-domain-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const domain = e.target.getAttribute('data-domain');
                    await ZenPermissions.removeDomain(domain);
                    await loadAllowedDomains();
                });
            });
        }

    } catch (error) {
        console.error('[Inspekt Popup] Error loading domains:', error);
        currentDomainStatus.innerHTML = '<div class="no-domains">Unable to load domain information</div>';
    }
}
