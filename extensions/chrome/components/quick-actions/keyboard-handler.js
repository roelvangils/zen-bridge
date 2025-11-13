/**
 * Keyboard Handler Component
 * Handles single-key shortcuts for Quick Actions
 * DevTools panels are isolated from page events, so no conflicts
 */

export class KeyboardHandler {
    constructor(shortcuts, executeCallback) {
        this.shortcuts = shortcuts;  // Map of action IDs to shortcut keys
        this.executeCallback = executeCallback;
        this.enabled = true;
    }

    /**
     * Initialize keyboard handler
     */
    init() {
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }

    /**
     * Handle keydown events
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyDown(e) {
        if (!this.enabled) return;

        // Ignore if user is typing in input/textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Ignore modifier keys (Ctrl, Cmd, Alt, Shift alone)
        if (e.ctrlKey || e.metaKey || e.altKey) {
            return;
        }

        // Get pressed key (uppercase for consistency)
        const key = e.key.toUpperCase();

        // Find action by shortcut key
        const action = this.findActionByKey(key);

        if (action) {
            // Prevent default behavior
            e.preventDefault();

            // Execute action
            this.executeCallback(action.id);

            // Show visual feedback
            this.showFeedback(action.id);
        }
    }

    /**
     * Find action by shortcut key
     * @param {string} key - Key pressed
     * @returns {Object|null} Action with id and shortcut, or null
     */
    findActionByKey(key) {
        for (const [actionId, shortcut] of Object.entries(this.shortcuts)) {
            if (shortcut === key) {
                return { id: actionId, shortcut };
            }
        }
        return null;
    }

    /**
     * Show visual feedback on tile
     * @param {string} actionId - Action ID
     */
    showFeedback(actionId) {
        const tile = document.querySelector(`[data-action-id="${actionId}"]`);
        if (tile) {
            // Add flash animation
            tile.classList.add('shortcut-flash');

            // Remove after animation completes
            setTimeout(() => {
                tile.classList.remove('shortcut-flash');
            }, 300);
        }
    }

    /**
     * Update shortcuts mapping
     * @param {Object} shortcuts - New shortcuts map
     */
    updateShortcuts(shortcuts) {
        this.shortcuts = shortcuts;
    }

    /**
     * Enable keyboard shortcuts
     */
    enable() {
        this.enabled = true;
    }

    /**
     * Disable keyboard shortcuts
     */
    disable() {
        this.enabled = false;
    }

    /**
     * Check if a key is already assigned
     * @param {string} key - Key to check
     * @returns {boolean} True if key is assigned
     */
    isKeyAssigned(key) {
        return Object.values(this.shortcuts).includes(key.toUpperCase());
    }

    /**
     * Get shortcut for action
     * @param {string} actionId - Action ID
     * @returns {string|null} Shortcut key or null
     */
    getShortcut(actionId) {
        return this.shortcuts[actionId] || null;
    }
}
