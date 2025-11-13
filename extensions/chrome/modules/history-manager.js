/**
 * History Manager Module
 * Manages element history tracking and UI
 */

import { getTimeAgo } from '../utils/time.js';
import { evalInPage } from '../utils/devtools.js';

export class HistoryManager {
    constructor() {
        this.elementHistory = [];
        this.elementHistoryContainer = document.getElementById('elementHistory');
        this.maxHistoryItems = 10;
    }

    /**
     * Add element to history
     * @param {Object} element - Element data
     */
    add(element) {
        // Don't add duplicates
        const existing = this.elementHistory.find(e => e.selector === element.selector);
        if (existing) {
            return;
        }

        // Add to beginning of array
        this.elementHistory.unshift(element);

        // Keep only last N items
        if (this.elementHistory.length > this.maxHistoryItems) {
            this.elementHistory = this.elementHistory.slice(0, this.maxHistoryItems);
        }

        // Update UI
        this.updateUI();
    }

    /**
     * Update history UI
     */
    updateUI() {
        if (this.elementHistory.length === 0) {
            this.elementHistoryContainer.innerHTML = '<p class="placeholder">No recent elements.</p>';
            return;
        }

        this.elementHistoryContainer.innerHTML = '';

        this.elementHistory.forEach((element) => {
            const item = this.createHistoryItem(element);
            this.elementHistoryContainer.appendChild(item);
        });
    }

    /**
     * Create history item element
     * @param {Object} element - Element data
     * @returns {HTMLElement} History item element
     */
    createHistoryItem(element) {
        const item = document.createElement('div');
        item.className = 'history-item';

        // Highlight button
        const highlightBtn = document.createElement('button');
        highlightBtn.className = 'history-highlight-btn';
        highlightBtn.innerHTML = '<span class="material-icons">auto_awesome</span>';
        highlightBtn.title = 'Highlight element';
        highlightBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.highlightElement(element.selector);
        });

        // Show in Elements button
        const elementsBtn = document.createElement('button');
        elementsBtn.className = 'history-elements-btn';
        elementsBtn.innerHTML = '<span class="material-icons">push_pin</span>';
        elementsBtn.title = 'Show in Elements panel';
        elementsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showInElementsPanel(element.selector);
        });

        // Info container
        const infoContainer = document.createElement('div');
        infoContainer.className = 'history-info';

        const tagSpan = document.createElement('div');
        tagSpan.className = 'history-tag';
        tagSpan.textContent = `<${element.tag}>`;
        if (element.id) {
            tagSpan.textContent += `#${element.id}`;
        }
        if (element.classes.length > 0) {
            tagSpan.textContent += `.${element.classes[0]}`;
        }

        const timeSpan = document.createElement('div');
        timeSpan.className = 'history-time';
        timeSpan.textContent = getTimeAgo(element.timestamp);

        infoContainer.appendChild(tagSpan);
        infoContainer.appendChild(timeSpan);

        item.appendChild(highlightBtn);
        item.appendChild(elementsBtn);
        item.appendChild(infoContainer);

        // Click info container to restore
        infoContainer.addEventListener('click', () => {
            this.restoreElement(element.selector);
        });

        return item;
    }

    /**
     * Restore element from history
     * @param {string} selector - CSS selector
     */
    restoreElement(selector) {
        evalInPage(
            `(function() {
                const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
                if (el) {
                    window.__INSPEKT_INSPECTED_ELEMENT__ = el;

                    // Highlight briefly
                    const originalOutline = el.style.outline;
                    el.style.outline = '3px solid #0066ff';
                    setTimeout(() => {
                        el.style.outline = originalOutline;
                    }, 1000);

                    return true;
                }
                return false;
            })()`,
            (result, error) => {
                if (result) {
                    console.log('[Inspekt Panel] Element restored from history');
                } else {
                    console.error('[Inspekt Panel] Could not restore element');
                }
            }
        );
    }

    /**
     * Show element in Elements panel
     * @param {string} selector - CSS selector
     */
    showInElementsPanel(selector) {
        evalInPage(
            `(function() {
                const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
                if (el) {
                    window.__INSPEKT_INSPECTED_ELEMENT__ = el;
                    inspect(el);
                    return true;
                }
                return false;
            })()`,
            (result, error) => {
                if (result) {
                    console.log('[Inspekt Panel] Element shown in Elements panel');
                } else {
                    console.error('[Inspekt Panel] Could not find element');
                }
            }
        );
    }

    /**
     * Highlight element from history
     * @param {string} selector - CSS selector
     */
    highlightElement(selector) {
        evalInPage(
            `(function() {
                const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
                if (el) {
                    window.__INSPEKT_INSPECTED_ELEMENT__ = el;
                    return true;
                }
                return false;
            })()`,
            (result, error) => {
                if (result) {
                    // Trigger highlight through event or callback
                    // This will be handled by element-highlighter component
                    window.dispatchEvent(new CustomEvent('inspekt:highlight-element', {
                        detail: { forceNew: true }
                    }));
                } else {
                    console.error('[Inspekt Panel] Could not find element to highlight');
                }
            }
        );
    }

    /**
     * Clear history
     */
    clear() {
        this.elementHistory = [];
        this.updateUI();
    }

    /**
     * Get history
     * @returns {Array} Element history array
     */
    getHistory() {
        return this.elementHistory;
    }
}
