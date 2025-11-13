/**
 * Drag Handler Component
 * Implements HTML5 Drag and Drop API for tile reordering
 */

export class DragHandler {
    constructor(gridElement, onReorder) {
        this.grid = gridElement;
        this.onReorder = onReorder;  // Callback to notify manager of new order
        this.draggedElement = null;
        this.placeholder = null;
    }

    /**
     * Initialize drag handler
     */
    init() {
        this.createPlaceholder();
        this.setupDragListeners();
    }

    /**
     * Create placeholder element for drag preview
     */
    createPlaceholder() {
        this.placeholder = document.createElement('div');
        this.placeholder.className = 'actions-grid-placeholder';
        this.placeholder.style.display = 'none';
    }

    /**
     * Setup drag event listeners on grid (event delegation)
     */
    setupDragListeners() {
        this.grid.addEventListener('dragstart', this.handleDragStart.bind(this));
        this.grid.addEventListener('dragover', this.handleDragOver.bind(this));
        this.grid.addEventListener('dragenter', this.handleDragEnter.bind(this));
        this.grid.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.grid.addEventListener('drop', this.handleDrop.bind(this));
        this.grid.addEventListener('dragend', this.handleDragEnd.bind(this));
    }

    /**
     * Handle drag start
     * @param {DragEvent} e - Drag event
     */
    handleDragStart(e) {
        if (!e.target.classList.contains('action-btn')) return;

        this.draggedElement = e.target;

        // Add dragging class for visual feedback
        e.target.classList.add('dragging');

        // Set drag effect
        e.dataTransfer.effectAllowed = 'move';

        // Set drag data (for accessibility)
        e.dataTransfer.setData('text/html', e.target.innerHTML);

        // Show placeholder
        this.placeholder.style.display = 'block';
    }

    /**
     * Handle drag over (allow drop)
     * @param {DragEvent} e - Drag event
     */
    handleDragOver(e) {
        if (!this.draggedElement) return;

        e.preventDefault();  // Required to allow drop
        e.dataTransfer.dropEffect = 'move';

        // Get element being dragged over
        const afterElement = this.getDragAfterElement(this.grid, e.clientY);

        if (afterElement == null) {
            this.grid.appendChild(this.placeholder);
        } else {
            this.grid.insertBefore(this.placeholder, afterElement);
        }
    }

    /**
     * Handle drag enter
     * @param {DragEvent} e - Drag event
     */
    handleDragEnter(e) {
        e.preventDefault();
    }

    /**
     * Handle drag leave
     * @param {DragEvent} e - Drag event
     */
    handleDragLeave(e) {
        // Optional: Add visual feedback
    }

    /**
     * Handle drop
     * @param {DragEvent} e - Drag event
     */
    handleDrop(e) {
        if (!this.draggedElement) return;

        e.preventDefault();

        // Insert dragged element at placeholder position
        this.grid.insertBefore(this.draggedElement, this.placeholder);

        // Get new order of action IDs
        const newOrder = this.getNewOrder();

        // Notify manager
        if (this.onReorder) {
            this.onReorder(newOrder);
        }
    }

    /**
     * Handle drag end (cleanup)
     * @param {DragEvent} e - Drag event
     */
    handleDragEnd(e) {
        if (!this.draggedElement) return;

        // Remove dragging class
        this.draggedElement.classList.remove('dragging');

        // Hide placeholder
        this.placeholder.style.display = 'none';

        // Remove placeholder from DOM if present
        if (this.placeholder.parentNode) {
            this.placeholder.parentNode.removeChild(this.placeholder);
        }

        // Reset
        this.draggedElement = null;
    }

    /**
     * Get element that should come after the dragged element
     * @param {HTMLElement} container - Container element
     * @param {number} y - Mouse Y position
     * @returns {HTMLElement|null} Element after drop position
     */
    getDragAfterElement(container, y) {
        // Get all action buttons except the one being dragged
        const draggableElements = [
            ...container.querySelectorAll('.action-btn:not(.dragging)')
        ];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    /**
     * Get current order of action IDs from DOM
     * @returns {Array<string>} Array of action IDs in current order
     */
    getNewOrder() {
        const tiles = this.grid.querySelectorAll('.action-btn');
        return Array.from(tiles).map(tile => tile.dataset.actionId);
    }

    /**
     * Cleanup (remove event listeners)
     */
    destroy() {
        this.grid.removeEventListener('dragstart', this.handleDragStart);
        this.grid.removeEventListener('dragover', this.handleDragOver);
        this.grid.removeEventListener('dragenter', this.handleDragEnter);
        this.grid.removeEventListener('dragleave', this.handleDragLeave);
        this.grid.removeEventListener('drop', this.handleDrop);
        this.grid.removeEventListener('dragend', this.handleDragEnd);
    }
}
