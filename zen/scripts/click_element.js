// Click on an element specified by selector or using stored element
(function() {
    const selector = 'SELECTOR_PLACEHOLDER';
    const clickType = 'CLICK_TYPE_PLACEHOLDER'; // 'click', 'dblclick', 'contextmenu'

    let element = null;

    // If selector is $0, use stored inspected element
    if (selector === '$0') {
        element = window.__ZEN_INSPECTED_ELEMENT__;
        if (!element || !document.body.contains(element)) {
            return {
                error: 'No element stored. Use: zen inspect "<selector>" first, or provide a selector'
            };
        }
    } else {
        // Find element by selector
        try {
            element = document.querySelector(selector);
        } catch (e) {
            return {
                error: 'Invalid selector: ' + e.message
            };
        }

        if (!element) {
            return {
                error: 'Element not found: ' + selector
            };
        }
    }

    // Get element info for confirmation
    const tag = element.tagName.toLowerCase();
    const id = element.id ? '#' + element.id : '';
    const cls = element.className && typeof element.className === 'string'
        ? '.' + element.className.split(' ').filter(c => c).slice(0, 2).join('.')
        : '';
    const elementDesc = '<' + tag + id + cls + '>';

    // Scroll element into view if needed
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Create and dispatch the appropriate event
    const rect = element.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;

    const eventInit = {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: x,
        clientY: y,
        screenX: x,
        screenY: y,
        button: clickType === 'contextmenu' ? 2 : 0,
        buttons: clickType === 'contextmenu' ? 2 : 1
    };

    // Dispatch mousedown, mouseup, and click/dblclick/contextmenu
    element.dispatchEvent(new MouseEvent('mousedown', eventInit));
    element.dispatchEvent(new MouseEvent('mouseup', eventInit));
    element.dispatchEvent(new MouseEvent(clickType, eventInit));

    // For regular clicks, also trigger the click event
    if (clickType === 'click') {
        element.click();
    }

    return {
        ok: true,
        action: clickType,
        element: elementDesc,
        selector: selector,
        position: {
            x: Math.round(x),
            y: Math.round(y)
        }
    };
})()
