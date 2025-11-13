/**
 * Handler for the "Copy Click Command" quick action
 * Copies the "inspekt click" command with the current element's selector
 * @param {Object} context - Manager context with dependencies
 */
export function handleCopyClickCommand(context) {
    const currentElement = context.elementDisplay.getCurrentElement();

    if (!currentElement) {
        console.warn('[Copy Click Command] No element selected');
        return;
    }

    if (!currentElement.selector) {
        console.error('[Copy Click Command] Element has no selector');
        return;
    }

    context.copyToClipboard(
        event,
        `inspekt click "${currentElement.selector}"`,
        'Click command',
        context.settingsManager.getSettings()
    );
}
