/**
 * Handler for the "Pick Element" quick action
 * Activates the element picker to select an element on the page
 * @param {Object} context - Manager context with dependencies
 */
export function handlePickElement(context) {
    console.log('[Quick Actions] activatePicker handler called');
    console.log('[Quick Actions] elementPicker:', context.elementPicker);
    context.elementPicker.activate();
}
