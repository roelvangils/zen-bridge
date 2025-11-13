/**
 * Element Picker Component
 * Activates element picker tool for selecting elements on page
 */

import { evalInPage } from '../utils/devtools.js';

export class ElementPicker {
    constructor() {
        this.btnPickElement = document.getElementById('btnPickElement');
    }

    /**
     * Initialize picker
     */
    init() {
        // Event listener setup is handled by quick-actions or panel.js
    }

    /**
     * Activate element picker on page
     */
    activate() {
        fetch(chrome.runtime.getURL('element_picker.js'))
            .then(response => response.text())
            .then(pickerScript => {
                evalInPage(
                    pickerScript,
                    (result, error) => {
                        if (error) {
                            console.error('[Inspekt Panel] Error activating picker:', error);
                            return;
                        }

                        if (result && result.error) {
                            console.log('[Inspekt Panel]', result.error);
                            return;
                        }

                        // Show feedback
                        this.btnPickElement.textContent = 'Picking...';
                        this.btnPickElement.disabled = true;
                        this.btnPickElement.classList.add('success-flash');

                        // Start polling for picker completion
                        this.pollForCompletion();
                    }
                );
            })
            .catch(error => {
                console.error('[Inspekt Panel] Error loading picker script:', error);
            });
    }

    /**
     * Poll for picker completion
     */
    pollForCompletion() {
        const pollInterval = setInterval(() => {
            evalInPage(
                'window.__ZEN_PICKER_ACTIVE__',
                (isActive, error) => {
                    // If picker is no longer active, it was completed or cancelled
                    if (!isActive) {
                        clearInterval(pollInterval);

                        // Reset button
                        this.btnPickElement.innerHTML = '<span class="material-icons btn-icon">gps_fixed</span><span class="btn-label">Pick Element</span><span class="btn-hint">Select element on page</span>';
                        this.btnPickElement.disabled = false;
                        this.btnPickElement.classList.remove('success-flash');

                        console.log('[Inspekt Panel] Picker completed');
                    }
                }
            );
        }, 500);
    }
}
