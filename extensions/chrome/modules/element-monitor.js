/**
 * Element Monitor Module
 * Polls for element selection changes and emits events
 */

import { evalInPage } from '../utils/devtools.js';

export class ElementMonitor {
    constructor() {
        this.lastElementCheck = null;
        this.pollInterval = null;
        this.listeners = [];
    }

    /**
     * Initialize and start monitoring
     */
    init() {
        this.start();
    }

    /**
     * Start monitoring element selection
     */
    start() {
        this.pollInterval = setInterval(() => {
            this.checkElement();
        }, 500);
    }

    /**
     * Stop monitoring
     */
    stop() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    /**
     * Check for element changes
     */
    checkElement() {
        evalInPage(
            `(function() {
                const el = window.__INSPEKT_INSPECTED_ELEMENT__;
                if (!el || el.nodeType !== 1) return null;

                function getCSSPath(el) {
                    if (!(el instanceof Element)) return '';
                    const path = [];
                    while (el.nodeType === Node.ELEMENT_NODE) {
                        let selector = el.nodeName.toLowerCase();
                        if (el.id) {
                            selector += '#' + CSS.escape(el.id);
                            path.unshift(selector);
                            break;
                        } else {
                            let sibling = el;
                            let nth = 1;
                            while (sibling.previousElementSibling) {
                                sibling = sibling.previousElementSibling;
                                if (sibling.nodeName.toLowerCase() === selector) nth++;
                            }
                            if (nth !== 1) selector += ':nth-of-type(' + nth + ')';
                        }
                        path.unshift(selector);
                        el = el.parentNode;
                    }
                    return path.join(' > ');
                }

                const tag = el.tagName.toLowerCase();
                const id = el.id || null;
                const classes = Array.from(el.classList);
                const selector = getCSSPath(el);
                const textContent = (el.textContent || '').trim().substring(0, 100);

                function getAccessibleName(el) {
                    const ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel) return ariaLabel;

                    const ariaLabelledBy = el.getAttribute('aria-labelledby');
                    if (ariaLabelledBy) {
                        const labelEl = document.getElementById(ariaLabelledBy);
                        if (labelEl) return labelEl.textContent.trim();
                    }

                    if (el.tagName === 'IMG') return el.alt || '';
                    if (el.tagName === 'BUTTON' || el.tagName === 'A') return el.textContent.trim();

                    return '';
                }

                const accessibleName = getAccessibleName(el);
                const role = el.getAttribute('role') || tag;

                return {
                    tag,
                    id,
                    classes,
                    selector,
                    textContent,
                    accessibleName,
                    role,
                    timestamp: Date.now()
                };
            })()`,
            (result, error) => {
                if (error) {
                    console.error('[Inspekt Panel] Error getting element:', error);
                    return;
                }

                if (result && result.selector !== this.lastElementCheck) {
                    this.lastElementCheck = result.selector;
                    this.notifyListeners(result);
                }
            }
        );
    }

    /**
     * Register a listener for element changes
     * @param {Function} callback - Called with element data
     */
    onElementChange(callback) {
        this.listeners.push(callback);
    }

    /**
     * Notify all listeners of element change
     * @param {Object} element - Element data
     */
    notifyListeners(element) {
        this.listeners.forEach(callback => callback(element));
    }
}
