/**
 * Clipboard utility functions
 */

/**
 * Copy text to clipboard with visual feedback
 * Works in DevTools panels using execCommand fallback
 *
 * @param {Event} event - Click event from the button
 * @param {string} text - Text to copy
 * @param {string} label - Label for logging (e.g., "Command", "Selector")
 * @param {Object} settings - Settings object with showNotifications flag
 * @returns {boolean} True if successful, false otherwise
 */
export function copyToClipboard(event, text, label, settings = {}) {
    // Create a temporary textarea element (works in DevTools panels)
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);

    try {
        textarea.select();
        textarea.setSelectionRange(0, 99999); // For mobile devices

        const success = document.execCommand('copy');

        if (success) {
            console.log(`[Inspekt Panel] ${label} copied to clipboard:`, text);

            // Show visual feedback
            const btn = event.target.closest('.action-btn');
            if (btn) {
                btn.classList.add('success-flash');
                setTimeout(() => btn.classList.remove('success-flash'), 500);
            }

            // Show notification in console if enabled
            if (settings.showNotifications) {
                chrome.devtools.inspectedWindow.eval(
                    `console.log('%c[Inspekt]%c ${label} copied to clipboard',
                        'color: #0066ff; font-weight: bold', 'color: #00aa00')`
                );
            }

            return true;
        } else {
            console.error('[Inspekt Panel] Failed to copy:', label);
            return false;
        }
    } catch (err) {
        console.error('[Inspekt Panel] Copy error:', err);
        return false;
    } finally {
        document.body.removeChild(textarea);
    }
}
