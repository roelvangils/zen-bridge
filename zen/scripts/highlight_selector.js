// Highlight elements matching a CSS selector
// Usage: Replace 'SELECTOR' with your actual selector
(function(selector) {
    const elements = document.querySelectorAll(selector);

    if (elements.length === 0) {
        return `No elements found matching: ${selector}`;
    }

    // Remove previous highlights
    document.querySelectorAll('[data-zen-highlight]').forEach(el => {
        el.style.outline = '';
        el.removeAttribute('data-zen-highlight');
    });

    // Add new highlights
    elements.forEach((el, index) => {
        el.style.outline = '3px solid #ff6b6b';
        el.setAttribute('data-zen-highlight', index);
    });

    return `Highlighted ${elements.length} element(s) matching: ${selector}`;
})('SELECTOR')  // Replace SELECTOR with actual selector like 'a', '.class', '#id'
