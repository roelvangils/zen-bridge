/**
 * Handler for the "Copy Selector" quick action
 * Copies the current element's selector to clipboard
 * @param {Object} context - Manager context with dependencies
 */
export function handleCopySelector(context) {
    const currentElement = context.elementDisplay.getCurrentElement();

    if (!currentElement) {
        console.warn('[Copy Selector] No element selected');
        return;
    }

    if (!currentElement.selector) {
        console.error('[Copy Selector] Element has no selector');
        return;
    }

    context.copyToClipboard(
        event,
        currentElement.selector,
        'Selector',
        context.settingsManager.getSettings()
    );
}
