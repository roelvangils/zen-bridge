/**
 * Handler for the "inspekt inspected" quick action
 * Copies the "inspekt inspected" command to clipboard
 * @param {Object} context - Manager context with dependencies
 */
export function handleCopyInspectedCommand(context) {
    context.copyToClipboard(
        event,
        'inspekt inspected',
        'Command',
        context.settingsManager.getSettings()
    );
}
