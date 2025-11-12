/**
 * Inspekt DevTools Integration
 *
 * Automatically captures elements selected in Chrome DevTools inspector.
 * When you inspect an element (right-click → Inspect), it's automatically
 * stored and available via `inspekt inspected` command.
 *
 * Also provides a custom DevTools panel with settings and quick actions.
 */

// Create the Inspekt panel in DevTools
chrome.devtools.panels.create(
    'Inspekt',              // Panel title
    'icons/icon-16.png',    // Icon path
    'panel.html',           // Panel HTML page
    (panel) => {
        console.log('[Inspekt DevTools] Panel created successfully');

        // Panel lifecycle events
        panel.onShown.addListener((window) => {
            console.log('[Inspekt DevTools] Panel opened');
        });

        panel.onHidden.addListener(() => {
            console.log('[Inspekt DevTools] Panel hidden');
        });
    }
);

// Monitor element selection in the Elements panel
chrome.devtools.panels.elements.onSelectionChanged.addListener(() => {
    // When user selects an element in DevTools inspector
    // $0 is the currently selected element in DevTools
    chrome.devtools.inspectedWindow.eval(
        `(function() {
            // Check if $0 is available and is a valid element
            if (typeof $0 !== 'undefined' && $0 && $0.nodeType === 1) {
                // Store the element in the global variable
                window.__INSPEKT_INSPECTED_ELEMENT__ = $0;

                // Get element info for console feedback
                const tag = $0.tagName.toLowerCase();
                const id = $0.id ? '#' + $0.id : '';
                const cls = $0.className && typeof $0.className === 'string' ?
                    '.' + $0.className.trim().split(/\\s+/).slice(0, 2).join('.') : '';
                const selector = tag + id + cls;

                // Log confirmation
                console.log(
                    '%c[Inspekt]%c ✓ Element auto-stored: %c<' + selector + '>',
                    'color: #0066ff; font-weight: bold',
                    'color: inherit',
                    'color: #00aa00; font-weight: bold'
                );
                console.log('[Inspekt] Run in terminal: inspekt inspected');

                return { success: true, selector: selector };
            } else {
                return { success: false, reason: 'No valid element selected' };
            }
        })()`,
        (result, error) => {
            if (error) {
                console.error('[Inspekt DevTools] Error storing element:', error);
            } else if (result && result.success) {
                // Successfully stored
                console.log('[Inspekt DevTools] Element stored:', result.selector);
            }
        }
    );
});

// Initialize DevTools integration
console.log('[Inspekt DevTools] Integration loaded');
console.log('[Inspekt DevTools] Elements are now automatically tracked when inspected');
