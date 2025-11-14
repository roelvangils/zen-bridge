/**
 * Element validation and helper utilities for handlers
 */

/**
 * Validate that an element is currently selected
 * @param {Object} elementDisplay - Element display instance
 * @returns {Object|null} Current element or null if not selected
 */
export function validateElementSelected(elementDisplay) {
    const currentElement = elementDisplay.getCurrentElement();

    if (!currentElement) {
        console.warn('[Element Helpers] No element selected');
        return null;
    }

    return currentElement;
}

/**
 * Validate that an element has a selector
 * @param {Object} element - Element object
 * @returns {boolean} True if element has valid selector
 */
export function validateElementSelector(element) {
    if (!element || !element.selector) {
        console.error('[Element Helpers] Element has no selector');
        return false;
    }

    return true;
}

/**
 * Get current element with validation
 * @param {Object} elementDisplay - Element display instance
 * @param {boolean} requireSelector - Whether to validate selector exists
 * @returns {Object|null} Current element or null if validation fails
 */
export function getCurrentElementWithValidation(elementDisplay, requireSelector = true) {
    const element = validateElementSelected(elementDisplay);

    if (!element) {
        return null;
    }

    if (requireSelector && !validateElementSelector(element)) {
        return null;
    }

    return element;
}
