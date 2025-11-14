/**
 * Action Tile Component
 * Renders individual Quick Action tiles with close button and keyboard shortcut
 */

export class ActionTile {
    constructor(action, options = {}) {
        this.action = action;
        this.shortcut = options.shortcut || action.shortcut;
        this.onRemove = options.onRemove || null;
        this.onClick = options.onClick || null;
        this.isDisabled = options.isDisabled || false;
    }

    /**
     * Render the action tile element
     * @returns {HTMLElement} Tile element
     */
    render() {
        const tile = document.createElement('button');
        tile.className = 'action-btn';
        tile.dataset.actionId = this.action.id;
        tile.draggable = true;

        // Disable if element required and not available
        if (this.isDisabled) {
            tile.disabled = true;
        }

        // Icon
        const icon = document.createElement('span');
        icon.className = 'material-icons btn-icon';
        icon.textContent = this.action.icon;
        tile.appendChild(icon);

        // Label
        const label = document.createElement('span');
        label.className = 'btn-label';
        label.textContent = this.action.label;
        tile.appendChild(label);

        // Hint
        const hint = document.createElement('span');
        hint.className = 'btn-hint';
        hint.textContent = this.action.hint;
        tile.appendChild(hint);

        // Keyboard shortcut badge
        if (this.shortcut) {
            const shortcutBadge = document.createElement('span');
            shortcutBadge.className = 'keyboard-shortcut';
            shortcutBadge.textContent = this.shortcut;
            shortcutBadge.title = `Keyboard shortcut: ${this.shortcut}`;
            tile.appendChild(shortcutBadge);
        }

        // Close button (appears on hover)
        const closeBtn = document.createElement('button');
        closeBtn.className = 'close-btn';
        closeBtn.innerHTML = '×';
        closeBtn.title = 'Remove action';
        closeBtn.setAttribute('aria-label', `Remove ${this.action.label}`);

        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();  // Prevent tile click
            if (this.onRemove) {
                this.onRemove(this.action.id, tile);
            }
        });

        tile.appendChild(closeBtn);

        // Tile click handler - always add, check disabled state on click
        if (this.onClick) {
            tile.addEventListener('click', () => {
                // Don't execute if tile is currently disabled
                if (tile.disabled) {
                    console.log('[ActionTile] Tile clicked but disabled:', this.action.id);
                    return;
                }
                console.log('[ActionTile] Tile clicked:', this.action.id);
                this.onClick(this.action.id);
            });
        }

        return tile;
    }

    /**
     * Create a removed/disabled action tile for manage panel
     * @param {Object} action - Action definition
     * @param {Function} onRestore - Restore callback
     * @returns {HTMLElement} Removed tile element
     */
    static createRemovedTile(action, onRestore) {
        const tile = document.createElement('div');
        tile.className = 'removed-action';
        tile.dataset.actionId = action.id;

        // Icon
        const icon = document.createElement('span');
        icon.className = 'material-icons';
        icon.textContent = action.icon;
        tile.appendChild(icon);

        // Label
        const label = document.createElement('span');
        label.className = 'removed-action-label';
        label.textContent = action.label;
        tile.appendChild(label);

        // Restore icon
        const restoreIcon = document.createElement('span');
        restoreIcon.className = 'material-icons restore-icon';
        restoreIcon.textContent = 'add_circle';
        restoreIcon.title = `Restore ${action.label}`;
        tile.appendChild(restoreIcon);

        // Click handler
        tile.addEventListener('click', () => {
            if (onRestore) {
                onRestore(action.id, tile);
            }
        });

        return tile;
    }
}
