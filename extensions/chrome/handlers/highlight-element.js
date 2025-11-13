/**
 * Handler for the "Highlight Element" quick action
 * Highlights the currently selected element on the page
 * @param {Object} context - Manager context with dependencies
 */
export function handleHighlightElement(context) {
    context.elementHighlighter.highlight();
}
