/**
 * Element Display Module
 * Renders current element information in the UI
 */

export class ElementDisplay {
    constructor() {
        this.currentElement = null;
        this.inspectedElement = document.getElementById('inspectedElement');

        // Note: Action buttons are now managed by QuickActionsManager
        // No longer need to reference them here
    }

    /**
     * Update display with new element
     * @param {Object} element - Element data
     */
    update(element) {
        this.currentElement = element;
        // Note: Button states are now handled by QuickActionsManager.updateElementStates()
        this.renderElementCard(element);
    }

    /**
     * Get current element
     * @returns {Object|null} Current element data
     */
    getCurrentElement() {
        return this.currentElement;
    }

    /**
     * Render element card
     * @param {Object} element - Element data
     */
    renderElementCard(element) {
        const card = document.createElement('div');
        card.className = 'element-card';

        // Tag line
        const tagLine = document.createElement('div');
        tagLine.className = 'element-tag';
        tagLine.textContent = `<${element.tag}>`;
        if (element.id) {
            tagLine.textContent += `#${element.id}`;
        }
        if (element.classes.length > 0) {
            tagLine.textContent += `.${element.classes.slice(0, 2).join('.')}`;
        }
        card.appendChild(tagLine);

        // Info container
        const infoContainer = document.createElement('div');
        infoContainer.className = 'element-info';

        if (element.selector) {
            infoContainer.appendChild(this.createInfoRow('Selector', element.selector));
        }

        if (element.role) {
            infoContainer.appendChild(this.createInfoRow('Role', element.role));
        }

        if (element.accessibleName) {
            infoContainer.appendChild(this.createInfoRow('Accessible Name', element.accessibleName));
        }

        if (element.textContent) {
            const shortText = element.textContent.length > 60
                ? element.textContent.substring(0, 60) + '...'
                : element.textContent;
            infoContainer.appendChild(this.createInfoRow('Text', shortText));
        }

        card.appendChild(infoContainer);

        // Update DOM
        this.inspectedElement.innerHTML = '';
        this.inspectedElement.appendChild(card);
    }

    /**
     * Create info row element
     * @param {string} label - Label text
     * @param {string} value - Value text
     * @returns {HTMLElement} Info row element
     */
    createInfoRow(label, value) {
        const row = document.createElement('div');
        row.className = 'info-row';

        const labelSpan = document.createElement('span');
        labelSpan.className = 'info-label';
        labelSpan.textContent = label + ':';

        const valueSpan = document.createElement('span');
        valueSpan.className = 'info-value';
        valueSpan.textContent = value;

        row.appendChild(labelSpan);
        row.appendChild(valueSpan);

        return row;
    }

    /**
     * Clear display
     */
    clear() {
        this.currentElement = null;
        this.inspectedElement.innerHTML = '<p class="placeholder">No element selected. Right-click an element and select "Inspect".</p>';

        // Note: Button states are now handled by QuickActionsManager.updateElementStates()
    }
}
