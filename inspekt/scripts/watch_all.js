// Watch all user interactions - keyboard, focus, and accessible names
(function() {
    const action = 'ACTION_PLACEHOLDER'; // 'start' or 'poll'

    // Initialize or get event store
    if (typeof window.__ZEN_ALL_EVENTS__ === 'undefined') {
        window.__ZEN_ALL_EVENTS__ = [];
        window.__ZEN_ALL_EVENTS_INDEX__ = 0;
    }

    // Compute accessible name for focused element
    function computeAccessibleName(el) {
        if (!el || el.nodeType !== 1) return '';

        let name = '';
        let source = '';

        // aria-labelledby (highest priority)
        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const ids = labelledBy.trim().split(/\s+/);
            const labels = ids.map(id => {
                const labelEl = document.getElementById(id);
                return labelEl ? labelEl.textContent.trim() : '';
            }).filter(text => text);
            if (labels.length > 0) {
                return labels.join(' ');
            }
        }

        // aria-label
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) {
            return ariaLabel.trim();
        }

        // For form controls: associated <label> element
        const tagName = el.tagName.toLowerCase();
        if (['input', 'select', 'textarea'].includes(tagName) && el.id) {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label) {
                return label.textContent.trim();
            }
        }

        // For input type="button/submit/reset": value attribute
        if (tagName === 'input' && ['button', 'submit', 'reset'].includes(el.type)) {
            const value = el.getAttribute('value');
            if (value) return value;
        }

        // For buttons/links: content
        if (['button', 'a'].includes(tagName)) {
            const text = el.textContent.trim();
            if (text && text.length < 100) return text;
        }

        // title attribute
        const title = el.getAttribute('title');
        if (title && title.trim()) {
            return title.trim();
        }

        // placeholder (for inputs)
        if (['input', 'textarea'].includes(tagName)) {
            const placeholder = el.getAttribute('placeholder');
            if (placeholder && placeholder.trim()) {
                return placeholder.trim();
            }
        }

        // Default: tag name + role
        const role = el.getAttribute('role') || tagName;
        return `<${role}>`;
    }

    if (action === 'start') {
        // Set up event listeners
        if (typeof window.__ZEN_ALL_WATCHER_ACTIVE__ !== 'undefined') {
            return { ok: true, message: 'Watcher already active' };
        }

        window.__ZEN_ALL_WATCHER_ACTIVE__ = true;
        window.__ZEN_ALL_EVENTS__ = [];
        window.__ZEN_ALL_EVENTS_INDEX__ = 0;

        // Track current text buffer
        let textBuffer = '';
        let lastEventTime = Date.now();

        function flushTextBuffer() {
            if (textBuffer) {
                window.__ZEN_ALL_EVENTS__.push({
                    type: 'text',
                    content: textBuffer,
                    timestamp: Date.now()
                });
                textBuffer = '';
            }
        }

        // Keyboard event handler
        const keyHandler = (e) => {
            const now = Date.now();

            // Check if this is a special key or has modifiers
            const isSpecialKey = e.key === 'Enter' || e.key === 'Tab' ||
                                e.key === 'Escape' || e.key.startsWith('Arrow') ||
                                e.key === 'Backspace' || e.key === 'Delete' ||
                                e.ctrlKey || e.metaKey || e.altKey;

            if (isSpecialKey) {
                // Flush text buffer first
                flushTextBuffer();

                // Format special key
                let keyStr = '';
                if (e.ctrlKey) keyStr += 'Ctrl+';
                if (e.metaKey) keyStr += 'Cmd+';
                if (e.altKey) keyStr += 'Alt+';
                if (e.shiftKey && e.key.length > 1) keyStr += 'Shift+';

                if (e.key === 'Enter') keyStr += 'Enter';
                else if (e.key === 'Tab') keyStr += 'Tab';
                else if (e.key === 'Escape') keyStr += 'Esc';
                else if (e.key === 'Backspace') keyStr += 'Backspace';
                else if (e.key === 'Delete') keyStr += 'Delete';
                else if (e.key === 'ArrowUp') keyStr += '↑';
                else if (e.key === 'ArrowDown') keyStr += '↓';
                else if (e.key === 'ArrowLeft') keyStr += '←';
                else if (e.key === 'ArrowRight') keyStr += '→';
                else keyStr += e.key;

                window.__ZEN_ALL_EVENTS__.push({
                    type: 'key',
                    content: keyStr,
                    timestamp: now
                });
            } else if (e.key.length === 1) {
                // Regular character - add to buffer
                // If more than 500ms since last event, flush first
                if (now - lastEventTime > 500) {
                    flushTextBuffer();
                }
                textBuffer += e.key;
            }

            lastEventTime = now;
        };

        // Focus event handler
        const focusHandler = (e) => {
            // Flush text buffer when focus changes
            flushTextBuffer();

            const element = e.target;
            if (!element || element === document.body || element === document.documentElement) {
                return;
            }

            // Get accessible name
            const accessibleName = computeAccessibleName(element);

            // Get element info
            const tag = element.tagName.toLowerCase();
            const id = element.id ? '#' + element.id : '';
            const role = element.getAttribute('role') || tag;

            window.__ZEN_ALL_EVENTS__.push({
                type: 'focus',
                element: `<${tag}${id}>`,
                role: role,
                accessibleName: accessibleName,
                timestamp: Date.now()
            });
        };

        // Attach listeners
        document.addEventListener('keydown', keyHandler, true);
        document.addEventListener('focusin', focusHandler, true);

        // Store references for cleanup
        window.__ZEN_ALL_KEY_HANDLER__ = keyHandler;
        window.__ZEN_ALL_FOCUS_HANDLER__ = focusHandler;
        window.__ZEN_ALL_TEXT_BUFFER_FLUSHER__ = flushTextBuffer;

        // Flush buffer every 1 second
        window.__ZEN_ALL_FLUSH_INTERVAL__ = setInterval(flushTextBuffer, 1000);

        return {
            ok: true,
            message: 'Watcher started'
        };

    } else if (action === 'poll') {
        // Flush any pending text
        if (typeof window.__ZEN_ALL_TEXT_BUFFER_FLUSHER__ === 'function') {
            window.__ZEN_ALL_TEXT_BUFFER_FLUSHER__();
        }

        // Get new events since last poll
        const allEvents = window.__ZEN_ALL_EVENTS__ || [];
        const lastIndex = window.__ZEN_ALL_EVENTS_INDEX__ || 0;
        const newEvents = allEvents.slice(lastIndex);

        // Update index
        window.__ZEN_ALL_EVENTS_INDEX__ = allEvents.length;

        return {
            ok: true,
            events: newEvents,
            hasEvents: newEvents.length > 0
        };

    } else if (action === 'stop') {
        // Clean up
        if (window.__ZEN_ALL_KEY_HANDLER__) {
            document.removeEventListener('keydown', window.__ZEN_ALL_KEY_HANDLER__, true);
            delete window.__ZEN_ALL_KEY_HANDLER__;
        }
        if (window.__ZEN_ALL_FOCUS_HANDLER__) {
            document.removeEventListener('focusin', window.__ZEN_ALL_FOCUS_HANDLER__, true);
            delete window.__ZEN_ALL_FOCUS_HANDLER__;
        }
        if (window.__ZEN_ALL_FLUSH_INTERVAL__) {
            clearInterval(window.__ZEN_ALL_FLUSH_INTERVAL__);
            delete window.__ZEN_ALL_FLUSH_INTERVAL__;
        }

        delete window.__ZEN_ALL_WATCHER_ACTIVE__;
        delete window.__ZEN_ALL_TEXT_BUFFER_FLUSHER__;

        return {
            ok: true,
            message: 'Watcher stopped'
        };
    }

    return { ok: false, error: 'Invalid action' };
})()
