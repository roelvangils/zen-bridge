/**
 * Screenshot utilities for capturing element screenshots
 */

/**
 * Capture a screenshot of a specific element
 * @param {Object} element - Element object with bounds information
 * @returns {Promise<Blob>} Screenshot image as blob
 */
export async function captureElementScreenshot(element) {
    console.log('[Screenshot Helpers] Starting capture for element:', element.selector);

    // Get the element's position and size
    const rect = await getElementBounds(element);
    console.log('[Screenshot Helpers] Got element bounds:', rect);

    if (!rect) {
        throw new Error('Could not get element bounds');
    }

    // Capture the visible tab
    console.log('[Screenshot Helpers] Capturing visible tab...');
    const dataUrl = await captureVisibleTab();
    console.log('[Screenshot Helpers] Tab captured, data URL length:', dataUrl.length);

    // Crop to element bounds
    console.log('[Screenshot Helpers] Cropping image to bounds...');
    const blob = await cropImage(dataUrl, rect);
    console.log('[Screenshot Helpers] Blob created, size:', blob.size);

    return blob;
}

/**
 * Get element bounds from the page
 * @param {Object} element - Element object
 * @returns {Promise<DOMRect>} Element bounds
 */
async function getElementBounds(element) {
    return new Promise((resolve, reject) => {
        // Use chrome.devtools.inspectedWindow.tabId for DevTools context
        const tabId = chrome.devtools.inspectedWindow.tabId;

        chrome.tabs.sendMessage(
            tabId,
            {
                action: 'getElementBounds',
                selector: element.selector
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                    return;
                }

                if (response && response.success && response.bounds) {
                    resolve(response.bounds);
                } else {
                    reject(new Error(response?.error || 'Could not get element bounds'));
                }
            }
        );
    });
}

/**
 * Capture the visible tab as a data URL
 * @returns {Promise<string>} Data URL of screenshot
 */
async function captureVisibleTab() {
    return new Promise((resolve, reject) => {
        chrome.tabs.captureVisibleTab(
            null,
            { format: 'png' },
            (dataUrl) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                    return;
                }

                resolve(dataUrl);
            }
        );
    });
}

/**
 * Crop an image to specific bounds
 * @param {string} dataUrl - Source image data URL
 * @param {DOMRect} rect - Bounds to crop to
 * @returns {Promise<Blob>} Cropped image as blob
 */
async function cropImage(dataUrl, rect) {
    return new Promise((resolve, reject) => {
        const img = new Image();

        img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Set canvas size to element size
            canvas.width = rect.width;
            canvas.height = rect.height;

            // Draw the cropped portion
            ctx.drawImage(
                img,
                rect.x, rect.y, rect.width, rect.height, // Source rectangle
                0, 0, rect.width, rect.height            // Destination rectangle
            );

            // Convert to blob
            canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Failed to create blob from canvas'));
                }
            }, 'image/png');
        };

        img.onerror = () => {
            reject(new Error('Failed to load image'));
        };

        img.src = dataUrl;
    });
}

/**
 * Show screenshot in a modal overlay
 * Users can right-click to copy or download the image
 * @param {string} dataUrl - Screenshot data URL
 * @param {string} selector - Element selector for context
 */
export function showScreenshotModal(dataUrl, selector) {
    console.log('[Screenshot] Showing screenshot modal');

    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'screenshot-modal-overlay';
    overlay.innerHTML = `
        <div class="screenshot-modal">
            <div class="screenshot-modal-header">
                <h3>Element Screenshot</h3>
                <button class="screenshot-modal-close" title="Close (Esc)">
                    <span class="material-icons">close</span>
                </button>
            </div>
            <div class="screenshot-modal-body">
                <div class="screenshot-selector">${escapeHtml(selector)}</div>
                <div class="screenshot-container">
                    <img src="${dataUrl}" alt="Element screenshot" class="screenshot-image">
                </div>
                <div class="screenshot-instructions">
                    Right-click the image to copy or save
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // Close handlers
    const closeModal = () => {
        overlay.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 200);
    };

    const closeButton = overlay.querySelector('.screenshot-modal-close');
    closeButton.addEventListener('click', closeModal);

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escHandler);
        }
    });

    // Fade in animation
    requestAnimationFrame(() => {
        overlay.classList.add('show');
    });
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Scroll element into view if needed
 * @param {string} selector - Element selector
 * @returns {Promise<void>}
 */
export async function scrollElementIntoView(selector) {
    return new Promise((resolve, reject) => {
        // Use chrome.devtools.inspectedWindow.tabId for DevTools context
        const tabId = chrome.devtools.inspectedWindow.tabId;

        chrome.tabs.sendMessage(
            tabId,
            {
                action: 'scrollIntoView',
                selector: selector
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                    return;
                }

                if (response && response.success) {
                    resolve();
                } else {
                    reject(new Error(response?.error || 'Could not scroll element into view'));
                }
            }
        );
    });
}
