/**
 * Offscreen Document for Clipboard Operations
 *
 * Chrome Manifest V3 service workers don't have access to the Clipboard API with images.
 * This offscreen document runs in a DOM context and can use navigator.clipboard.write()
 */

console.log('[Offscreen] Clipboard handler loaded');

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Offscreen] Received message:', message.type, 'target:', message.target);

    // Only process messages meant for the offscreen document
    if (message.type === 'OFFSCREEN_COPY_IMAGE' && message.target === 'offscreen') {
        console.log('[Offscreen] Processing clipboard copy request...');

        copyImageToClipboard(message.dataUrl)
            .then(() => {
                console.log('[Offscreen] Image successfully copied to clipboard');
                sendResponse({ success: true });
            })
            .catch((error) => {
                console.error('[Offscreen] Failed to copy image:', error);
                sendResponse({ success: false, error: error.message });
            });

        return true; // Keep message channel open for async response
    }

    // Don't respond to messages not meant for us
    return false;
});

/**
 * Copy image to clipboard from data URL
 * @param {string} dataUrl - Image data URL (base64 encoded)
 * @returns {Promise<void>}
 */
async function copyImageToClipboard(dataUrl) {
    try {
        // Convert data URL to blob
        const response = await fetch(dataUrl);
        const blob = await response.blob();

        console.log('[Offscreen] Converted data URL to blob, size:', blob.size);

        // Focus the document before clipboard write (required by Chrome)
        window.focus();

        // Use a textarea workaround for clipboard write
        // This is more reliable than navigator.clipboard in offscreen documents
        await writeImageToClipboardViaDOM(blob);

        console.log('[Offscreen] Successfully wrote image to clipboard');
    } catch (error) {
        console.error('[Offscreen] Clipboard write failed:', error);
        throw error;
    }
}

/**
 * Write image to clipboard using button click workaround
 * Offscreen documents need a user gesture to write to clipboard
 * We simulate this by creating a button and programmatically clicking it
 * @param {Blob} blob - Image blob
 * @returns {Promise<void>}
 */
async function writeImageToClipboardViaDOM(blob) {
    console.log('[Offscreen] Using button-click workaround for clipboard write...');

    return new Promise((resolve, reject) => {
        // Create a button that will trigger the clipboard write
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.style.position = 'fixed';
        button.style.top = '0';
        button.style.left = '0';
        document.body.appendChild(button);

        // Add click handler that does the clipboard write
        button.addEventListener('click', async () => {
            try {
                console.log('[Offscreen] Button clicked, writing to clipboard...');

                // Create ClipboardItem with the image
                const clipboardItem = new ClipboardItem({
                    'image/png': blob
                });

                // Write to clipboard (this works because it's in a click handler)
                await navigator.clipboard.write([clipboardItem]);

                console.log('[Offscreen] Clipboard write successful!');

                // Clean up
                document.body.removeChild(button);
                resolve();
            } catch (error) {
                console.error('[Offscreen] Clipboard write failed:', error);
                document.body.removeChild(button);
                reject(error);
            }
        });

        // Programmatically click the button to trigger the handler
        console.log('[Offscreen] Programmatically clicking button...');
        button.click();
    });
}
