import { evalInPage } from '../utils/devtools.js';

/**
 * Handler for the "Show in Elements" quick action
 * Opens the selected element in the Chrome DevTools Elements panel
 * @param {Object} context - Manager context with dependencies
 */
export function handleShowInElements(context) {
    const currentElement = context.elementDisplay.getCurrentElement();

    if (!currentElement) {
        console.warn('[Show in Elements] No element selected');
        return;
    }

    evalInPage(
        `(function() {
            const el = window.__INSPEKT_INSPECTED_ELEMENT__;
            if (el) {
                inspect(el);
                return true;
            }
            return false;
        })()`,
        (result, error) => {
            if (error) {
                console.error('[Show in Elements] Error showing in Elements:', error);
                return;
            }

            if (result) {
                console.log('[Show in Elements] Element shown in Elements panel');
            } else {
                console.error('[Show in Elements] Could not find element');
            }
        }
    );
}
